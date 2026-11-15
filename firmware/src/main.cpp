#include <Arduino.h>
#include <WiFi.h>
#include "config.h"
#include "audio_i2s.h"
#include "cloud_gateway.h"
#include "bt_speaker.h"

enum SystemState {
    STATE_WIFI_CONNECTING,
    STATE_BT_CONNECTING,
    STATE_IDLE_LISTENING,
    STATE_RECORDING,
    STATE_PROCESSING,
    STATE_SPEAKING
};

static SystemState g_currentState = STATE_WIFI_CONNECTING;
static unsigned long g_lastLedToggle = 0;
static bool g_ledState = false;

// Audio capture buffer in internal RAM (16kHz 16-bit Mono, 6 seconds = 192KB)
static const size_t MAX_SAMPLES = SAMPLE_RATE * 6;
static int16_t* g_audioRecordBuffer = nullptr;
static size_t g_recordedSamples = 0;

// VAD Tracking
static unsigned long g_speechStartTime = 0;
static unsigned long g_silenceStartTime = 0;
static bool g_isSpeaking = false;

void setStatusLed(bool on) {
    digitalWrite(STATUS_LED_PIN, on ? HIGH : LOW);
}

void updateLed() {
    unsigned long now = millis();
    unsigned long interval = 500;

    switch (g_currentState) {
        case STATE_WIFI_CONNECTING:
        case STATE_BT_CONNECTING:
            interval = 250; // Fast blink while searching for networks
            break;
        case STATE_IDLE_LISTENING:
            setStatusLed(true); // Solid ON when ready for voice
            return;
        case STATE_RECORDING:
            interval = 100; // Rapid flutter while actively recording speech
            break;
        case STATE_PROCESSING:
            interval = 150; // Processing Cloudflare request
            break;
        case STATE_SPEAKING:
            setStatusLed(true);
            return;
    }

    if (now - g_lastLedToggle >= interval) {
        g_lastLedToggle = now;
        g_ledState = !g_ledState;
        setStatusLed(g_ledState);
    }
}

void setupWifi() {
    Serial.println("\n[WiFi] Connecting to home network...");
    Serial.printf("[WiFi] SSID: %s\n", WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 25) {
        delay(400);
        updateLed();
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WiFi] Connected! IP: %s | RSSI: %d dBm\n", 
                      WiFi.localIP().toString().c_str(), WiFi.RSSI());
    } else {
        Serial.println("\n[WiFi] Warning: Wi-Fi credentials not configured or network unreachable.");
        Serial.println("[WiFi] Update WIFI_SSID and WIFI_PASSWORD in include/config.h");
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("====================================================");
    Serial.println("  PROJECT SIDECAR — 24/7 AMBIENT VOICE ASSISTANT   ");
    Serial.println("  Cloudflare Workers AI + Meta Muse + Echo Dot 4th  ");
    Serial.println("====================================================");

    pinMode(STATUS_LED_PIN, OUTPUT);
    setStatusLed(false);

    // 1. Allocate audio buffer
    g_audioRecordBuffer = (int16_t*)ps_malloc(MAX_SAMPLES * sizeof(int16_t));
    if (!g_audioRecordBuffer) {
        g_audioRecordBuffer = (int16_t*)malloc(MAX_SAMPLES * sizeof(int16_t));
    }

    if (!g_audioRecordBuffer) {
        Serial.println("[System] CRITICAL ERROR: Failed to allocate audio buffer!");
    } else {
        Serial.printf("[System] Audio record buffer allocated: %u KB\n", 
                      (unsigned int)((MAX_SAMPLES * sizeof(int16_t)) / 1024));
    }

    // 2. Connect Wi-Fi
    g_currentState = STATE_WIFI_CONNECTING;
    setupWifi();

    // 3. Initialize I2S Microphone Driver
    if (!g_audioInput.begin()) {
        Serial.println("[System] CRITICAL ERROR: I2S INMP441 initialization failed!");
    } else {
        g_audioInput.calibrateNoiseFloor();
    }

    // 4. Initialize Bluetooth A2DP Source to Amazon Echo Dot
    g_currentState = STATE_BT_CONNECTING;
    g_btSpeaker.begin(BT_SINK_NAME);

    // 5. Initialize Cloudflare Gateway
    g_cloudGateway.begin();

    g_currentState = STATE_IDLE_LISTENING;
    Serial.println("[System] Sidecar Assistant is READY. Listening for ambient speech...");
}

void processSpeechAudio() {
    g_currentState = STATE_PROCESSING;
    Serial.printf("[System] Finished recording: %u samples (%lu ms). Sending to Cloudflare...\n",
                  (unsigned int)g_recordedSamples, (unsigned long)((g_recordedSamples * 1000) / SAMPLE_RATE));

    g_btSpeaker.playChime(CHIME_THINKING);

    size_t byteCount = g_recordedSamples * sizeof(int16_t);
    CloudResponse resp = g_cloudGateway.sendVoiceAudio((uint8_t*)g_audioRecordBuffer, byteCount);

    if (resp.success) {
        Serial.println("[System] Conversation turn successful!");
        g_currentState = STATE_SPEAKING;

        if (resp.audioData && resp.audioLen > 44) {
            // Skip 44-byte WAV header and stream synthesized voice PCM samples to Echo Dot
            const int16_t* pcmSamples = (const int16_t*)(resp.audioData + 44);
            size_t sampleCount = (resp.audioLen - 44) / sizeof(int16_t);
            Serial.printf("[System] Streaming %u speech samples to Echo Dot speaker...\n", (unsigned int)sampleCount);
            g_btSpeaker.playAudioBuffer(pcmSamples, sampleCount);

            // Wait for audio playback to complete
            while (g_btSpeaker.isPlaying()) {
                delay(20);
                g_btSpeaker.tick();
            }
        } else {
            g_btSpeaker.playChime(CHIME_SUCCESS);
            delay(1200);
        }
    } else {
        Serial.println("[System] Voice query failed or no speech detected.");
        g_btSpeaker.playChime(CHIME_ERROR);
    }

    g_cloudGateway.freeResponse(resp);
    g_recordedSamples = 0;
    g_isSpeaking = false;
    g_currentState = STATE_IDLE_LISTENING;
    Serial.println("[System] Listening resumed...");
}

void loop() {
    updateLed();
    g_btSpeaker.tick();

    if (g_currentState == STATE_IDLE_LISTENING || g_currentState == STATE_RECORDING) {
        const int CHUNK_SAMPLES = 256;
        int16_t chunk[CHUNK_SAMPLES];

        int samplesRead = g_audioInput.readAudioChunk(chunk, CHUNK_SAMPLES);
        if (samplesRead <= 0) {
            delay(5);
            return;
        }

        int32_t rms = g_audioInput.calculateRMS(chunk, samplesRead);
        int32_t threshold = g_audioInput.getVadThreshold();
        unsigned long now = millis();

        if (rms >= threshold) {
            // Voice energy detected
            if (!g_isSpeaking) {
                g_isSpeaking = true;
                g_speechStartTime = now;
                g_recordedSamples = 0;
                g_currentState = STATE_RECORDING;
                Serial.printf("[VAD] Speech trigger! RMS: %d > Threshold: %d\n", rms, threshold);
                g_btSpeaker.playChime(CHIME_WAKE);
            }
            g_silenceStartTime = 0; // Reset silence counter
        } else {
            // Below threshold (silence/ambient)
            if (g_isSpeaking && g_silenceStartTime == 0) {
                g_silenceStartTime = now;
            }
        }

        // If currently recording speech, append chunk to buffer
        if (g_isSpeaking && g_audioRecordBuffer) {
            if (g_recordedSamples + samplesRead < MAX_SAMPLES) {
                memcpy(g_audioRecordBuffer + g_recordedSamples, chunk, samplesRead * sizeof(int16_t));
                g_recordedSamples += samplesRead;
            }

            // Check if silence exceeded timeout (utterance finished)
            if (g_silenceStartTime > 0 && (now - g_silenceStartTime >= VAD_SILENCE_LIMIT_MS)) {
                if (now - g_speechStartTime >= VAD_MIN_SPEECH_MS) {
                    processSpeechAudio();
                } else {
                    // Ignore clicks shorter than minimum speech duration
                    Serial.println("[VAD] Audio transient rejected (too short).");
                    g_isSpeaking = false;
                    g_recordedSamples = 0;
                    g_currentState = STATE_IDLE_LISTENING;
                }
            } else if (g_recordedSamples + CHUNK_SAMPLES >= MAX_SAMPLES) {
                // Max recording buffer reached
                processSpeechAudio();
            }
        }
    }
}
