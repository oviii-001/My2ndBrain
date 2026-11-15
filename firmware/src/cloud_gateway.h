#pragma once

#include "config.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

struct CloudResponse {
    bool success;
    String transcript;
    String reply;
    uint8_t* audioData;
    size_t audioLen;
};

class CloudGateway {
public:
    CloudGateway();
    bool begin();
    CloudResponse sendVoiceAudio(const uint8_t* pcmData, size_t pcmBytes);
    void freeResponse(CloudResponse& resp);

private:
    void writeWavHeader(uint8_t* header, uint32_t pcmDataLen);
};

extern CloudGateway g_cloudGateway;
