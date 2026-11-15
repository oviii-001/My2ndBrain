# Project Sidecar — 1-Click ESP32 Auto-Flasher for Windows
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Project Sidecar — ESP32 Jarvis Auto-Flasher" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Locate esptool
$usePythonEsptool = $false
$esptool = "esptool"
$esptoolCmd = Get-Command esptool -ErrorAction SilentlyContinue
if ($esptoolCmd) {
    $esptool = $esptoolCmd.Source
} else {
    $testPy = & python -m esptool version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $usePythonEsptool = $true
    } else {
        $fallback = "C:\Users\USERAS\AppData\Roaming\Python\Python314\Scripts\esptool.exe"
        if (Test-Path $fallback) {
            $esptool = $fallback
        } else {
            Write-Host "ERROR: esptool not found." -ForegroundColor Red
            Write-Host "Run: python -m pip install esptool" -ForegroundColor Yellow
            exit 1
        }
    }
}

# 2. Check Wi-Fi configuration
$configPath = "$PSScriptRoot\include\config.h"
if (Test-Path $configPath) {
    $configContent = Get-Content $configPath -Raw
    if ($configContent -match 'WIFI_SSID\s+"YOUR_WIFI_SSID"') {
        Write-Host "`n[!] Wi-Fi credentials not configured yet." -ForegroundColor Yellow
        $wifiSsid = Read-Host "Enter your 2.4GHz Wi-Fi Name (SSID)"
        $wifiPass = Read-Host "Enter your Wi-Fi Password"
        if ($wifiSsid) {
            $configContent = $configContent -replace 'WIFI_SSID "YOUR_WIFI_SSID"', "WIFI_SSID `"$wifiSsid`""
            $configContent = $configContent -replace 'WIFI_PASSWORD "YOUR_WIFI_PASSWORD"', "WIFI_PASSWORD `"$wifiPass`""
            Set-Content -Path $configPath -Value $configContent -Encoding utf8
            Write-Host "[+] Configured Wi-Fi credentials in include/config.h" -ForegroundColor Green
            Write-Host "[*] Compiling firmware with your Wi-Fi..." -ForegroundColor Cyan
            & python -m platformio run -d "$PSScriptRoot"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Compilation failed." -ForegroundColor Red
                exit 1
            }
            Copy-Item "$PSScriptRoot\.pio\build\esp32dev\firmware.bin" "$PSScriptRoot\bin\firmware.bin" -Force
        }
    }
}

# 3. Locate built binaries
$releaseDir = "$PSScriptRoot\bin"
$buildDir = "$PSScriptRoot\.pio\build\esp32dev"

if (Test-Path "$releaseDir\firmware.bin") {
    $bootloader = "$releaseDir\bootloader.bin"
    $partitions = "$releaseDir\partitions.bin"
    $firmware = "$releaseDir\firmware.bin"
    Write-Host "Using pre-compiled release binaries from $releaseDir" -ForegroundColor Green
} elseif (Test-Path "$buildDir\firmware.bin") {
    $bootloader = "$buildDir\bootloader.bin"
    $partitions = "$buildDir\partitions.bin"
    $firmware = "$buildDir\firmware.bin"
    Write-Host "Using built binaries from $buildDir" -ForegroundColor Green
} else {
    Write-Host "Binaries not found. Compiling with PlatformIO..." -ForegroundColor Yellow
    & python -m platformio run -d "$PSScriptRoot"
    $bootloader = "$buildDir\bootloader.bin"
    $partitions = "$buildDir\partitions.bin"
    $firmware = "$buildDir\firmware.bin"
}

# 3. Detect connected COM port
Write-Host "Detecting connected ESP32 on USB ports..." -ForegroundColor Gray
$comPorts = [System.IO.Ports.SerialPort]::GetPortNames()

if ($comPorts.Count -eq 0) {
    Write-Host "`n[!] No ESP32 detected on USB!" -ForegroundColor Red
    Write-Host "1. Connect your ESP32 to your PC using a micro-USB / USB-C DATA cable." -ForegroundColor Yellow
    Write-Host "2. (Note: Ensure the cable has data lines, not charge-only)." -ForegroundColor Yellow
    Write-Host "3. If device manager shows an unknown device, install CP210x or CH340 driver." -ForegroundColor Yellow
    exit 1
}

$targetPort = $comPorts[0]
Write-Host "Detected ESP32 on port: $targetPort" -ForegroundColor Green

# 4. Flash binary with esptool
Write-Host "`nFlashing firmware to ESP32 at 921600 baud..." -ForegroundColor Cyan

$flashArgs = @(
    "--chip", "esp32",
    "--port", $targetPort,
    "--baud", "921600",
    "--before", "default_reset",
    "--after", "hard_reset",
    "write_flash", "-z",
    "--flash_mode", "dio",
    "--flash_freq", "40m",
    "--flash_size", "detect",
    "0x1000", $bootloader,
    "0x8000", $partitions,
    "0x10000", $firmware
)

if ($usePythonEsptool) {
    & python -m esptool @flashArgs
} else {
    & $esptool @flashArgs
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n==========================================================" -ForegroundColor Green
    Write-Host "  [SUCCESS] Firmware Flashed Successfully!" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "1. Put your Echo Dot in Bluetooth pairing mode: 'Alexa, pair Bluetooth'" -ForegroundColor White
    Write-Host "2. The ESP32 will pair automatically as an A2DP Bluetooth transmitter." -ForegroundColor White
    Write-Host "3. Speak your request in your room to activate Jarvis!" -ForegroundColor White
} else {
    Write-Host "`n[!] Flashing failed. Check USB connection and hold the 'BOOT' button on the ESP32 while flashing." -ForegroundColor Red
}
