# Project Sidecar — Master Task Checklist

## Phase 1: Repository & Cloudflare Gateway Setup
- [x] Create comprehensive architectural documentation and ADR (`docs/adr/0001-architecture-selection.md`)
- [x] Create system architecture specification with Mermaid sequence diagrams (`docs/architecture.md`)
- [x] Create hardware shopping and pinout wiring guide (`docs/hardware-guide.md`)
- [x] Create technical research notes and feasibility dossier (`docs/research-notes.md`)
- [x] Scaffold repository directory layout (`cloud-gateway/`, `firmware/`, `docs/`, `tasks/`)
- [ ] Initialize Cloudflare Worker project (`cloud-gateway/wrangler.toml`, `package.json`, `src/index.ts`)
- [ ] Implement `@cf/openai/whisper` speech-to-text handler in Cloudflare Worker
- [ ] Implement Meta MuseAI GraphQL client with session cookie authentication
- [ ] Implement Neural TTS streaming audio generator
- [ ] Test Cloudflare Worker locally and deploy to free Cloudflare edge

## Checkpoint 1: Cloudflare Gateway Operational
- [ ] Gateway accepts audio buffer and returns synthesized voice response via curl/test script
- [ ] Verified zero-cost execution within 10,000 daily free neurons

---

## Phase 2: Hardware Acquisition & Desk Wiring (Tomorrow)
- [ ] Purchase ESP32 DevKit V1 and INMP441 I2S microphone module in local market
- [ ] Wire INMP441 to ESP32 using the pinout guide (GPIO 32, 25, 33, 3V3, GND)
- [ ] Power on ESP32 via 5V USB cable and verify power LED
- [ ] Flash test sketch to verify I2S microphone audio sampling

## Checkpoint 2: Hardware Ready
- [ ] Serial plotter confirms clean, unclipped 16kHz audio waveform from microphone

---

## Phase 3: ESP32 Firmware Development
- [ ] Initialize PlatformIO / Arduino C++ project in `firmware/`
- [ ] Implement non-blocking Wi-Fi manager with exponential backoff reconnect
- [ ] Implement I2S DMA audio capture pipeline
- [ ] Implement WebSocket client streaming binary audio chunks to Cloudflare Gateway
- [ ] Implement Bluetooth A2DP Source library (`ESP32-A2DP`)
- [ ] Pair ESP32 with Amazon Echo Dot 4th Gen and verify continuous audio streaming

## Checkpoint 3: End-to-End Pipeline
- [ ] Spoken voice command on ESP32 mic routes to Cloudflare, returns TTS, and plays on Echo Dot

---

## Phase 4: Proactive Alerts & Production Hardening
- [ ] Implement 5-minute scheduled Cron trigger in Cloudflare Worker to check MuseAI notifications
- [ ] Implement push announcement handler on ESP32 when unread Muse notification arrives
- [ ] Measure and optimize end-to-end latency to achieve < 1.0s turnaround
- [ ] Document final operating manual and maintenance guide in `README.md`
