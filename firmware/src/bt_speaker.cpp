#include "bt_speaker.h"

BtSpeaker g_btSpeaker;

const int16_t* BtSpeaker::s_activePlaybackBuffer = nullptr;
size_t BtSpeaker::s_activePlaybackSamples = 0;
size_t BtSpeaker::s_playbackIndex = 0;
bool BtSpeaker::s_isPlaying = false;

// Pre-generated procedural chimes (sine waves in 44.1kHz standard A2DP format)
static int16_t s_chimeBuffer[4410]; // 100ms at 44.1kHz
static size_t s_chimeLength = 0;

BtSpeaker::BtSpeaker() {}

bool BtSpeaker::begin(const char* deviceName) {
    Serial.printf("[Bluetooth] Initializing A2DP Source searching for '%s'...\n", deviceName);
    
    // Configure Bluetooth A2DP Source
    m_a2dpSource.set_auto_reconnect(true);
    m_a2dpSource.start_raw(deviceName, getSoundData);
    
    Serial.println("[Bluetooth] A2DP transmitter running. Put Echo Dot in pairing mode: 'Alexa, pair Bluetooth'");
    return true;
}

bool BtSpeaker::isConnected() {
    return m_a2dpSource.is_connected();
}

bool BtSpeaker::isPlaying() {
    return s_isPlaying;
}

int32_t BtSpeaker::getSoundData(uint8_t* data, int32_t len) {
    if (!data || len <= 0) return 0;

    int16_t* out = (int16_t*)data;
    int samplesNeeded = len / (2 * sizeof(int16_t)); // Stereo 16-bit

    if (!s_isPlaying || !s_activePlaybackBuffer || s_playbackIndex >= s_activePlaybackSamples) {
        memset(data, 0, len); // Output digital silence when not playing
        s_isPlaying = false;
        return len;
    }

    for (int i = 0; i < samplesNeeded; i++) {
        if (s_playbackIndex < s_activePlaybackSamples) {
            int16_t sample = s_activePlaybackBuffer[s_playbackIndex++];
            out[i * 2]     = sample; // Left
            out[i * 2 + 1] = sample; // Right
        } else {
            out[i * 2]     = 0;
            out[i * 2 + 1] = 0;
            s_isPlaying = false;
        }
    }

    return len;
}

void BtSpeaker::playAudioBuffer(const int16_t* pcmData, size_t sampleCount) {
    s_activePlaybackBuffer = pcmData;
    s_activePlaybackSamples = sampleCount;
    s_playbackIndex = 0;
    s_isPlaying = true;
}

void BtSpeaker::playChime(ChimeType chime) {
    float freq = 880.0f; // Default A5
    int durationMs = 120;

    switch (chime) {
        case CHIME_WAKE:
            freq = 987.77f; // B5
            durationMs = 150;
            break;
        case CHIME_THINKING:
            freq = 659.25f; // E5
            durationMs = 100;
            break;
        case CHIME_SUCCESS:
            freq = 1318.51f; // E6
            durationMs = 180;
            break;
        case CHIME_ERROR:
            freq = 349.23f; // F4
            durationMs = 250;
            break;
    }

    const int SAMPLE_RATE_A2DP = 44100;
    s_chimeLength = (SAMPLE_RATE_A2DP * durationMs) / 1000;
    if (s_chimeLength > sizeof(s_chimeBuffer) / sizeof(int16_t)) {
        s_chimeLength = sizeof(s_chimeBuffer) / sizeof(int16_t);
    }

    for (size_t i = 0; i < s_chimeLength; i++) {
        float angle = (2.0f * PI * freq * i) / SAMPLE_RATE_A2DP;
        // Apply smooth envelope to prevent clicking
        float envelope = 1.0f - ((float)i / (float)s_chimeLength);
        s_chimeBuffer[i] = (int16_t)(sin(angle) * 12000.0f * envelope);
    }

    playAudioBuffer(s_chimeBuffer, s_chimeLength);
}

void BtSpeaker::tick() {
    // Keep internal tasks alive if needed
}
