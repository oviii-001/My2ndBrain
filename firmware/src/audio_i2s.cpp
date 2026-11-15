#include "audio_i2s.h"

AudioInput g_audioInput;

AudioInput::AudioInput() 
    : m_noiseFloor(VAD_NOISE_FLOOR_DEFAULT),
      m_vadThreshold(VAD_NOISE_FLOOR_DEFAULT * 2) {
}

bool AudioInput::begin() {
    Serial.println("[I2S] Initializing INMP441 Microphone Driver...");

    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT, // Read 32-bit slot from INMP441
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = DMA_BUF_COUNT,
        .dma_buf_len = DMA_BUF_LEN,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_MIC_SCK_PIN,
        .ws_io_num = I2S_MIC_WS_PIN,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_MIC_SD_PIN
    };

    esp_err_t err = i2s_driver_install(I2S_PORT_MIC, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Driver install failed: %d\n", err);
        return false;
    }

    err = i2s_set_pin(I2S_PORT_MIC, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Set pin failed: %d\n", err);
        return false;
    }

    i2s_zero_dma_buffer(I2S_PORT_MIC);
    Serial.println("[I2S] INMP441 configured successfully (16kHz 16-bit Mono equivalent).");
    return true;
}

void AudioInput::calibrateNoiseFloor() {
    Serial.println("[I2S] Calibrating ambient room noise floor (1 second silence)...");
    const int CHUNK_SIZE = 512;
    int16_t tempBuffer[CHUNK_SIZE];
    int64_t totalRms = 0;
    int iterations = 0;

    unsigned long start = millis();
    while (millis() - start < 1000) {
        int read = readAudioChunk(tempBuffer, CHUNK_SIZE);
        if (read > 0) {
            totalRms += calculateRMS(tempBuffer, read);
            iterations++;
        }
        delay(10);
    }

    if (iterations > 0) {
        m_noiseFloor = (int32_t)(totalRms / iterations);
    } else {
        m_noiseFloor = VAD_NOISE_FLOOR_DEFAULT;
    }

    // Dynamic threshold: 2.2x background ambient noise floor, minimum 1200
    m_vadThreshold = max((int32_t)(m_noiseFloor * 2.2), (int32_t)1200);
    Serial.printf("[I2S] Calibration complete. Ambient Noise: %d | Speech Threshold: %d\n", 
                  m_noiseFloor, m_vadThreshold);
}

int AudioInput::readAudioChunk(int16_t* buffer, int samplesToRead) {
    // We allocate a temporary 32-bit buffer to read the high-resolution slot
    int32_t rawSamples[samplesToRead];
    size_t bytesRead = 0;

    esp_err_t result = i2s_read(I2S_PORT_MIC, rawSamples, samplesToRead * sizeof(int32_t), 
                                &bytesRead, portMAX_DELAY);

    if (result != ESP_OK || bytesRead == 0) {
        return 0;
    }

    int samplesCount = bytesRead / sizeof(int32_t);
    for (int i = 0; i < samplesCount; i++) {
        // Shift 24-bit INMP441 sample down to 16-bit PCM with soft digital gain
        int32_t s = rawSamples[i] >> 14;
        if (s > 32767) s = 32767;
        if (s < -32768) s = -32768;
        buffer[i] = (int16_t)s;
    }

    return samplesCount;
}

int32_t AudioInput::calculateRMS(const int16_t* buffer, int sampleCount) {
    if (sampleCount <= 0) return 0;
    int64_t sumSquares = 0;
    for (int i = 0; i < sampleCount; i++) {
        sumSquares += (int64_t)buffer[i] * buffer[i];
    }
    return (int32_t)sqrt(sumSquares / sampleCount);
}
