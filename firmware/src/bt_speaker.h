#pragma once

#include "config.h"
#include "BluetoothA2DPSource.h"

enum ChimeType {
    CHIME_WAKE,
    CHIME_THINKING,
    CHIME_SUCCESS,
    CHIME_ERROR
};

class BtSpeaker {
public:
    BtSpeaker();
    bool begin(const char* deviceName = BT_SINK_NAME);
    bool isConnected();
    void playChime(ChimeType chime);
    void playAudioBuffer(const int16_t* pcmData, size_t sampleCount);
    void tick();

    // Sound callback for Bluetooth A2DP library
    static int32_t getSoundData(uint8_t* data, int32_t len);

private:
    BluetoothA2DPSource m_a2dpSource;
    static const int16_t* s_activePlaybackBuffer;
    static size_t s_activePlaybackSamples;
    static size_t s_playbackIndex;
    static bool s_isPlaying;
};

extern BtSpeaker g_btSpeaker;
