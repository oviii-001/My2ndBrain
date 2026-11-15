# Implementation Plan: My2ndBrain (Ambient Voice Satellite for Meta Muse AI)

> **Version:** 2.0.0  
> **Status:** Active Execution  
> **Scope:** High-fidelity British male voice (Iron Man JARVIS), next-gen STT (Deepgram Nova-3 + Whisper), over-engineering cleanup, and ESP32 physical station deployment.

---

## 1. System Overview & Dependency Graph

```
[INMP441 Microphone (ESP32 / PC)]
           │
           ▼
[Edge STT: Deepgram Nova-3 / Whisper]
           │
           ▼
[Hatch Noise_XX WebSocket Client] ──► [Meta Muse AI Brain (Jarvis)]
           │
           ▼
[Neural TTS: en-GB-RyanNeural (British Male)]
           │
           ▼
[Echo Dot 4th Gen (A2DP Bluetooth)]
```

---

## 2. Vertical Implementation Tasks

### Task 1: Authentic British Male Jarvis Voice (Iron Man Style)

**Description:**  
Upgrade audio synthesis from robotic SAPI/pyttsx3 to a studio-grade British male neural voice matching Paul Bettany's performance in Marvel's Iron Man. Leverages Microsoft Neural `en-GB-RyanNeural` with negative pitch shift (`-1Hz`) and slight pace acceleration (`+2%`) via `edge-tts` and in-memory streaming through `pygame.mixer`.

**Acceptance criteria:**
- [x] Given an assistant response text, when synthesized, it plays in under 1.5 seconds without writing temporary audio files to disk.
- [x] Audio renders with an articulate, calm, polite British male accent.
- [x] Graceful fallback to local engine if network connection drops.

**Verification:**
- [x] Automated test: `python -c "import edge_tts, pygame; ..."` successfully streams and loads in memory.
- [x] Manual check: Run `python pc-simulator/simulator.py --manual` and verify auditory response fidelity.

**Dependencies:** None  
**Files touched:**
- `pc-simulator/simulator.py`
- `README.md`

---

### Task 2: Dual-Engine High-Speed STT (Deepgram Nova-3 + Whisper Fallback)

**Description:**  
Upgrade the Cloudflare edge Speech-to-Text pipeline from standard Whisper to a dual-engine topology. Evaluates incoming 16kHz PCM audio against `@cf/deepgram/nova-3` for sub-300ms transcription with superior ambient noise filtering, falling back seamlessly to `@cf/openai/whisper`.

**Acceptance criteria:**
- [x] Given spoken voice audio with background noise, STT transcribes in under 500ms.
- [x] Returns clean text and engine metadata (`engine: "deepgram-nova-3" | "openai-whisper"`).
- [x] Handles empty payloads and audio decoding edge-cases gracefully.

**Verification:**
- [x] Manual check: `POST /api/stt` with WAV payload returns `200 OK` with valid transcript.

**Dependencies:** Task 1  
**Files touched:**
- `cloud-gateway/src/index.ts`
- `pc-simulator/simulator.py`

---

### Task 3: Over-Engineering & Bloat Reduction (Ponytail Cleanup)

**Description:**  
Audit and prune unused abstractions across the repository: eliminate dead GraphQL POST attempts to `meta.ai` in `cloud-gateway/src/index.ts`, remove redundant cookie header formatting, replace PowerShell subprocess speech synthesis calls with native in-memory playback, and consolidate duplicate audio decoding pipelines.

**Acceptance criteria:**
- [x] Dead code in `cloud-gateway/src/index.ts` removed (-40+ lines).
- [x] Monolithic redundant `/api/voice` calls bypassed in favor of dedicated `/api/stt`.
- [x] Working tree clean and free of leftover debug dumps.

**Verification:**
- [x] Git diff audit confirming net reduction in lines of code without regression.
- [x] `simulator.py` runs with zero warnings.

**Dependencies:** Task 1, Task 2  
**Files touched:**
- `cloud-gateway/src/index.ts`
- `pc-simulator/simulator.py`

---

### Task 4: ESP32 Hardware Flashing & Room Deployment

**Description:**  
Connect physical ESP32 DevKit V1 and INMP441 I2S microphone module via Dupont wires, flash production firmware with `firmware/flash.bat`, pair with Amazon Echo Dot (4th Gen) over Bluetooth A2DP, and verify standalone room operation without a PC.

**Acceptance criteria:**
- [ ] ESP32 boots and connects to local 2.4GHz Wi-Fi in under 5 seconds.
- [ ] INMP441 captures clean 16kHz audio over I2S DMA.
- [ ] Echo Dot announces connection and plays assistant responses cleanly.

**Verification:**
- [ ] PlatformIO build test: RAM < 25%, Flash < 55%.
- [ ] One-click Windows flasher connects to serial COM port and uploads partitions + firmware.

**Dependencies:** Task 1, Task 2, Task 3  
**Files touched:**
- `firmware/src/main.cpp`
- `firmware/include/config.h`
- `firmware/flash.bat`
