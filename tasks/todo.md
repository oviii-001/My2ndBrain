# Project Sidecar — Master Task Checklist

## Phase 1: Complete Production Cloud & Firmware Development (DONE TODAY)
- [x] Create comprehensive architectural documentation and ADR (`docs/adr/0001-architecture-selection.md`)
- [x] Create system architecture specification with Mermaid sequence diagrams (`docs/architecture.md`)
- [x] Create hardware shopping and pinout wiring guide (`docs/hardware-guide.md`)
- [x] Create technical research notes and feasibility dossier (`docs/research-notes.md`)
- [x] Scaffold repository directory layout (`cloud-gateway/`, `firmware/`, `pc-simulator/`, `docs/`, `tasks/`)
- [x] Install Python audio simulation dependencies (`sounddevice`, `websockets`, `numpy`, `pyttsx3`, `requests`)
- [x] Initialize Cloudflare Worker project (`cloud-gateway/wrangler.toml`, `package.json`, `src/index.ts`)
- [x] Implement `@cf/openai/whisper` speech-to-text handler in Cloudflare Worker
- [x] Implement `@cf/myshell-ai/melotts` neural speech generator returning WAV audio
- [x] Implement Meta MuseAI GraphQL client with session cookie authentication
- [x] Deploy Cloudflare Worker to production via Cloudflare MCP (`https://sidecar-cloud-gateway.ismamhasanovi.workers.dev`)
- [x] Build PC Mic Simulator (`pc-simulator/simulator.py`) supporting live speech and neural audio playback
- [x] Develop production ESP32 C++ firmware in `firmware/`:
  - [x] I2S DMA INMP441 audio driver (`firmware/src/audio_i2s.cpp`)
  - [x] Cloudflare Gateway HTTPS client (`firmware/src/cloud_gateway.cpp`)
  - [x] Bluetooth A2DP Source transmitter for Echo Dot 4th Gen (`firmware/src/bt_speaker.cpp`)
  - [x] System state machine & LED diagnostics (`firmware/src/main.cpp`)
- [x] Compile ESP32 firmware with PlatformIO (`SUCCESS` — RAM: 20.9%, Flash: 51.4%)
- [x] Package pre-compiled binary release files in `firmware/bin/` (`bootloader.bin`, `partitions.bin`, `firmware.bin`)
- [x] Create 1-click auto-flasher script for Windows (`firmware/flash.bat` & `firmware/flash.ps1`)

---

## Phase 2: Hardware Acquisition & Flash (Tomorrow)
- [ ] Purchase ESP32 DevKit V1 and INMP441 I2S microphone module (~700 BDT)
- [ ] Connect INMP441 to ESP32 using 5 Dupont jumper wires:
  - `VDD` -> `3V3`, `GND` -> `GND`, `L/R` -> `GND`
  - `SD` -> `GPIO 32`, `WS` -> `GPIO 25`, `SCK` -> `GPIO 33`
- [ ] Plug ESP32 into PC via USB cable
- [ ] Set Wi-Fi credentials in `firmware/include/config.h`
- [ ] Run `firmware/flash.bat` (Flashes firmware in ~15 seconds)
- [ ] Say: *"Alexa, pair Bluetooth"* to pair Echo Dot 4th Gen
- [ ] Speak to Jarvis in your room!

---

## Phase 3: Meta Muse Account Linking (Whenever Ready)
- [ ] Grab `c_user`, `xs`, `datr` from `meta.ai` cookies
- [ ] Bind credentials to Cloudflare Worker secrets (`META_C_USER`, `META_XS`, `META_DATR`)
- [ ] Document final operating manual and maintenance guide in `README.md`
