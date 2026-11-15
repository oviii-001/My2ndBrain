#include "cloud_gateway.h"

CloudGateway g_cloudGateway;

CloudGateway::CloudGateway() {}

bool CloudGateway::begin() {
    return true;
}

void CloudGateway::writeWavHeader(uint8_t* header, uint32_t pcmDataLen) {
    uint32_t totalDataLen = pcmDataLen + 36;
    uint32_t sampleRate = SAMPLE_RATE;
    uint16_t numChannels = 1;
    uint16_t bitsPerSample = SAMPLE_BITS;
    uint32_t byteRate = sampleRate * numChannels * (bitsPerSample / 8);
    uint16_t blockAlign = numChannels * (bitsPerSample / 8);

    header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
    header[4] = (uint8_t)(totalDataLen & 0xff);
    header[5] = (uint8_t)((totalDataLen >> 8) & 0xff);
    header[6] = (uint8_t)((totalDataLen >> 16) & 0xff);
    header[7] = (uint8_t)((totalDataLen >> 24) & 0xff);
    header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
    header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
    header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0; // SubChunk1Size (16 for PCM)
    header[20] = 1; header[21] = 0; // AudioFormat (1 for PCM)
    header[22] = (uint8_t)numChannels; header[23] = 0;
    header[24] = (uint8_t)(sampleRate & 0xff);
    header[25] = (uint8_t)((sampleRate >> 8) & 0xff);
    header[26] = (uint8_t)((sampleRate >> 16) & 0xff);
    header[27] = (uint8_t)((sampleRate >> 24) & 0xff);
    header[28] = (uint8_t)(byteRate & 0xff);
    header[29] = (uint8_t)((byteRate >> 8) & 0xff);
    header[30] = (uint8_t)((byteRate >> 16) & 0xff);
    header[31] = (uint8_t)((byteRate >> 24) & 0xff);
    header[32] = (uint8_t)blockAlign; header[33] = 0;
    header[34] = (uint8_t)bitsPerSample; header[35] = 0;
    header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
    header[40] = (uint8_t)(pcmDataLen & 0xff);
    header[41] = (uint8_t)((pcmDataLen >> 8) & 0xff);
    header[42] = (uint8_t)((pcmDataLen >> 16) & 0xff);
    header[43] = (uint8_t)((pcmDataLen >> 24) & 0xff);
}

CloudResponse CloudGateway::sendVoiceAudio(const uint8_t* pcmData, size_t pcmBytes) {
    CloudResponse resp;
    resp.success = false;
    resp.audioData = nullptr;
    resp.audioLen = 0;

    if (pcmBytes == 0 || pcmData == nullptr) {
        Serial.println("[Cloud] Error: empty audio buffer.");
        return resp;
    }

    WiFiClientSecure client;
    client.setInsecure(); // Cloudflare edge SSL certificate validation

    HTTPClient http;
    http.setTimeout(15000); // 15s timeout for Whisper STT + Muse inference + TTS

    if (!http.begin(client, CLOUDFLARE_VOICE_URL)) {
        Serial.println("[Cloud] Failed to connect to Cloudflare Gateway URL.");
        return resp;
    }

    http.addHeader("Content-Type", "audio/wav");

    // Prepend 44-byte WAV header
    const size_t WAV_HEADER_SIZE = 44;
    size_t totalPayloadSize = WAV_HEADER_SIZE + pcmBytes;
    uint8_t* payload = (uint8_t*)malloc(totalPayloadSize);
    if (!payload) {
        Serial.println("[Cloud] Error: Out of memory allocating WAV payload.");
        http.end();
        return resp;
    }

    writeWavHeader(payload, pcmBytes);
    memcpy(payload + WAV_HEADER_SIZE, pcmData, pcmBytes);

    Serial.printf("[Cloud] Uploading %u bytes of WAV audio to Cloudflare Gateway...\n", (unsigned int)totalPayloadSize);
    unsigned long startTime = millis();
    int httpCode = http.POST(payload, totalPayloadSize);
    free(payload);

    unsigned long elapsed = millis() - startTime;
    Serial.printf("[Cloud] Gateway responded HTTP %d in %lu ms\n", httpCode, elapsed);

    if (httpCode == HTTP_CODE_OK) {
        String jsonPayload = http.getString();
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, jsonPayload);

        if (!error) {
            resp.success = true;
            resp.transcript = doc["transcript"].as<String>();
            resp.reply = doc["reply"].as<String>();
            Serial.printf("[Cloud] STT Transcript: \"%s\"\n", resp.transcript.c_str());
            Serial.printf("[Cloud] Muse Response:  \"%s\"\n", resp.reply.c_str());
        } else {
            Serial.printf("[Cloud] JSON parsing failed: %s\n", error.c_str());
        }
    } else {
        Serial.printf("[Cloud] HTTP Error: %d - %s\n", httpCode, http.errorToString(httpCode).c_str());
    }

    http.end();
    return resp;
}

void CloudGateway::freeResponse(CloudResponse& resp) {
    if (resp.audioData) {
        free(resp.audioData);
        resp.audioData = nullptr;
    }
    resp.audioLen = 0;
}
