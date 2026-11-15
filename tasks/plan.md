# Implementation Plan: Project Sidecar (ESP32 + Cloudflare + Meta MuseAI)

## Overview
Project Sidecar builds a 24/7 ambient personal voice assistant ("Jarvis") using an ESP32 DevKit V1, an INMP441 I2S microphone, an idle Amazon Echo Dot (4th Gen) as a Bluetooth speaker, and a serverless Cloudflare Workers AI bridge communicating with Meta MuseAI at zero monthly cost ($0.00/mo).

## Architecture Decisions
- **ADR 0001:** ESP32 DevKit V1 as hardware satellite + Cloudflare Workers AI (`@cf/openai/whisper`) + Meta MuseAI internal GraphQL bridge + Bluetooth A2DP to Echo Dot 4th Gen.
- **Protocol:** Real-time bi-directional WebSocket connection between ESP32 and Cloudflare Worker.
- **Zero-Cloud-Cost Hard Cap:** Built strictly within Cloudflare's permanent 10,000 Neurons/day free tier (no credit card required).

---

## Phase Breakdown

### Phase 1A: PC Hardware Simulator & Cloud Gateway (Tonight - Zero Hardware Wait)
Build and verify the full voice pipeline tonight on your laptop while simulating the ESP32:
- Set up `pc-simulator/` script using `sounddevice` to capture laptop mic audio at 16kHz PCM (exact INMP441 format).
- Initialize Cloudflare Worker project with Wrangler and TypeScript (`cloud-gateway/`).
- Implement `@cf/openai/whisper` speech-to-text pipeline from audio buffers.
- Implement Meta MuseAI GraphQL reverse client with persistent session cookies.
- Implement Edge Neural TTS audio generator streaming MP3/PCM audio buffers back to PC.
- Test full two-way voice conversations with Meta Muse tonight using laptop mic + Echo Dot (via PC Bluetooth).

### Phase 1B: Meta MuseAI Authentication & Integration
- Extract session cookies (`c_user`, `xs`, `datr`) from `meta.ai`.
- Configure encrypted secrets in Cloudflare Worker (`wrangler secret put`).
- Validate Gmail and Instagram message querying through the gateway.

### Phase 2: Physical ESP32 Hardware Acquisition & Bench Setup (Tomorrow)
- Purchase ESP32 DevKit V1 and INMP441 I2S microphone module.
- Wire INMP441 to ESP32 (GPIO 32, 25, 33, 3V3, GND).
- Install PlatformIO / Arduino IDE with ESP32 board support packages.
- Run hardware sanity tests (LED blink, I2S microphone serial plotter test).

### Phase 3: ESP32 Firmware Development (`/firmware`)
- Replace PC simulator with ESP32 C++ firmware.
- Implement I2S digital audio sampler with DMA buffers (16kHz, 16-bit PCM).
- Implement Wi-Fi manager with auto-reconnect logic.
- Implement secure WebSocket client (`wss://`) streaming audio chunks to Cloudflare.
- Implement Bluetooth Classic A2DP Source (`ESP32-A2DP`) pairing directly with Echo Dot 4th Gen.
- Implement audio playback buffer receiving TTS stream and piping directly to Echo Dot.

### Phase 4: Integration, Latency Tuning & Proactive Jarvis Testing
- End-to-end voice query test: "Hey Jarvis" ➔ Whisper ➔ Meta MuseAI ➔ Echo Dot speaker.
- Latency profiling: Ensure end-to-end voice turnaround is under 1.0 second.
- Proactive event push test: Verify MuseAI reminders trigger automatic Echo Dot announcements.
- Stress testing & 24/7 stability verification.

---

## Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Meta session cookie expiration** | Medium | Gateway returns a clear alert if session expires; script provided to refresh cookies via browser. |
| **I2S clock jitter / audio buzz** | Low | Dedicated hardware DMA buffers on ESP32; short, well-seated jumper wires (<10cm). |
| **Bluetooth audio packet drop** | Low | Pre-allocated ring buffer in ESP32 heap; fixed 44.1kHz SBC audio stream. |
| **Cloudflare daily quota exhaustion** | Low | Hard cap at 10,000 Neurons/day (~4 hours of speech/day); fails gracefully without charging. |
