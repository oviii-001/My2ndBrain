# ⚡ ESP32 Jarvis Firmware Guide

Production-ready, standalone firmware for **ESP32 DevKit V1** paired with the **INMP441 I2S Microphone** and **Amazon Echo Dot (4th Gen)** via Bluetooth A2DP.

---

## 🚀 1-Click Flashing (Windows)

When your ESP32 arrives:

1. Connect the ESP32 to your PC using a **Micro-USB / USB-C data cable** (ensure it has data lines, not charge-only).
2. Double-click `flash.bat` (or run in PowerShell):
   ```powershell
   cd firmware
   .\flash.bat
   ```
3. **Wi-Fi Setup**: If you haven't configured Wi-Fi in `include/config.h`, the flasher will automatically prompt you in the console:
   ```text
   [!] Wi-Fi credentials not configured yet.
   Enter your 2.4GHz Wi-Fi Name (SSID): YourHomeWifi
   Enter your Wi-Fi Password: YourPassword
   ```
4. It will automatically compile and flash the firmware to your ESP32 at **921,600 baud** in ~15 seconds!

---

## 🔌 Hardware Wiring Diagram

Connect the **INMP441 I2S Microphone** to the **ESP32 DevKit V1** using 5 Dupont jumper wires:

| INMP441 Pin | ESP32 Pin | Function / Description |
| :--- | :--- | :--- |
| **VDD** | **3V3** | 3.3V Power Supply |
| **GND** | **GND** | Ground |
| **SD** | **GPIO 32** | Serial Data Out (I2S DIN) |
| **WS** | **GPIO 25** | Word Select / LRCLK |
| **SCK** | **GPIO 33** | Serial Clock / BCLK |
| **L/R** | **GND** | Left/Right Channel (Tied to GND for Mono Left) |

> [!IMPORTANT]
> Always connect **L/R** to **GND**. This forces the INMP441 to output on the left audio channel, which matches the firmware's 16kHz 16-bit mono I2S driver configuration.

---

## 🔊 Amazon Echo Dot (4th Gen) Bluetooth Setup

1. Make sure your Echo Dot is powered on and connected to power.
2. Say to your Echo Dot:
   > *"Alexa, pair Bluetooth"*
3. The Echo Dot will say: *"Searching..."* with a pulsing blue light ring.
4. Power on the ESP32 (or press the **EN / RST** button on the ESP32).
5. The ESP32 scans for Bluetooth audio sinks named `Echo Dot` and pairs automatically as an **A2DP Source**.
6. The Echo Dot will announce: *"Connected to Bluetooth"* or play a connection chime.

---

## 🎙️ Room Operation (PC Completely Off!)

Once flashed and paired:

1. **Unplug ESP32 from PC** and plug it into any standard **5V phone charger** in your room.
2. The ESP32 boots up in under 2 seconds, connects to your 2.4GHz Wi-Fi, and links to your Echo Dot.
3. Speak your request naturally from anywhere in your room.
4. The station captures your voice via INMP441, streams raw audio to the Cloudflare Edge Gateway, communicates with your personal Muse AI, synthesizes the authentic British Jarvis voice, and streams the voice directly through your Echo Dot speaker.
5. Operating cost: **$0.00/month**. PC stays powered off!
