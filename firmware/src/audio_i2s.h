#pragma once

#include "config.h"
#include <driver/i2s.h>

class AudioInput {
public:
    AudioInput();
    bool begin();
    void calibrateNoiseFloor();
    int readAudioChunk(int16_t* buffer, int samplesToRead);
    int32_t calculateRMS(const int16_t* buffer, int sampleCount);
    int32_t getNoiseFloor() const { return m_noiseFloor; }
    int32_t getVadThreshold() const { return m_vadThreshold; }

private:
    int32_t m_noiseFloor;
    int32_t m_vadThreshold;
};

extern AudioInput g_audioInput;
