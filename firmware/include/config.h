#pragma once

#include <Arduino.h>

// =========================================================================
// Wi-Fi Configuration
// =========================================================================
// Replace with your home Wi-Fi credentials
#ifndef WIFI_SSID
#define WIFI_SSID "YOUR_WIFI_SSID"
#endif

#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#endif

// =========================================================================
// Cloudflare Gateway Endpoint
// =========================================================================
#define CLOUDFLARE_VOICE_URL "https://sidecar-cloud-gateway.ismamhasanovi.workers.dev/api/voice"
#define CLOUDFLARE_HEALTH_URL "https://sidecar-cloud-gateway.ismamhasanovi.workers.dev/health"

// =========================================================================
// Amazon Echo Dot 4th Gen Bluetooth Sink Name
// =========================================================================
// Set Echo Dot into pairing mode: "Alexa, pair Bluetooth"
// By default, Echo Dot 4th Gen advertises as "Echo Dot" or "Echo Dot-XXX"
#define BT_SINK_NAME "Echo Dot"

// =========================================================================
// INMP441 I2S Digital Microphone Pinout
// =========================================================================
#define I2S_MIC_SCK_PIN   33   // Serial Clock (BCLK)
#define I2S_MIC_WS_PIN    25   // Word Select / Left-Right Clock (LRC)
#define I2S_MIC_SD_PIN    32   // Serial Data (DIN)
// INMP441 VDD -> 3V3, GND -> GND, L/R -> GND (Left Channel)

// =========================================================================
// Audio Sampling & VAD Parameters
// =========================================================================
#define SAMPLE_RATE              16000  // 16kHz for Whisper
#define SAMPLE_BITS              16     // 16-bit PCM
#define I2S_PORT_MIC             I2S_NUM_0

// Buffer sizing
#define DMA_BUF_COUNT            8
#define DMA_BUF_LEN              512
#define MAX_RECORDING_SECONDS    7
#define MAX_AUDIO_BUFFER_SIZE    (SAMPLE_RATE * sizeof(int16_t) * MAX_RECORDING_SECONDS) // ~224 KB in PSRAM or heap

// Voice Activity Detection (VAD)
#define VAD_SILENCE_LIMIT_MS     1200   // 1.2s silence terminates utterance
#define VAD_MIN_SPEECH_MS        600    // Minimum utterance length to reject clicks
#define VAD_NOISE_FLOOR_DEFAULT  1500   // Dynamic baseline calibration

// =========================================================================
// Hardware UI / LED Diagnostics (ESP32 DevKit V1)
// =========================================================================
#define STATUS_LED_PIN           2      // Built-in Blue LED on ESP32 DevKit V1
