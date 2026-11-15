# My2ndBrain — Master Task Checklist

## Phase 1: Core Engine & Protocol Integration (COMPLETED)
- [x] Reverse-engineer Meta Muse AI Hatch Noise_XX encrypted WebSocket protocol
- [x] Implement in-process thread-safe `MuseBridge` in `pc-simulator/simulator.py`
- [x] Optimize conversational latency from 31.7s to ~3.5s via fast ACK breaks & sequence polling
- [x] Add background pre-warming for Noise_XX WebSocket handshake
- [x] Redesign repository documentation and architecture specs in `README.md`

## Phase 2: High-Fidelity Audio & Next-Gen STT (COMPLETED)
- [x] Research Iron Man JARVIS British male voice implementations across GitHub
- [x] Integrate Microsoft Neural `en-GB-RyanNeural` (`rate="+2%"`, `pitch="-1Hz"`) via `edge-tts`
- [x] Implement zero-disk in-memory MP3 playback streaming directly into `pygame.mixer`
- [x] Upgrade Cloudflare edge STT to dual-engine topology (Deepgram Nova-3 + Whisper fallback)
- [x] Conduct Ponytail audit and prune dead GraphQL POST and monolithic pipeline code

## Phase 3: Hardware Acquisition & Room Station Deployment (TOMORROW)
- [ ] Purchase ESP32 DevKit V1 & INMP441 I2S microphone module (~700 BDT)
- [ ] Connect INMP441 to ESP32 pins:
  - `VDD` ➔ `3V3`, `GND` ➔ `GND`, `L/R` ➔ `GND`
  - `SD` ➔ `GPIO 32`, `WS` ➔ `GPIO 25`, `SCK` ➔ `GPIO 33`
- [ ] Plug ESP32 into PC via Micro-USB cable
- [ ] Run `firmware/flash.bat` (automated one-click flash)
- [ ] Pair Echo Dot 4th Gen over Bluetooth (*"Alexa, pair Bluetooth"*)
- [ ] Speak to Jarvis 24/7 in your room with PC off!
