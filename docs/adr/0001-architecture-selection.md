# ADR 0001: Standalone ESP32 + Cloudflare Workers AI + Meta MuseAI Voice Assistant

* **Status:** Accepted
* **Date:** 2026-11-15
* **Deciders:** System Architect, Lead Developer
* **Project Codename:** Sidecar (Personal Ambient Voice Satellite)

---

## 1. Context and Problem Statement

The objective is to build an always-on, ambient, hands-free voice assistant station ("Jarvis") in the user's room. The user heavily utilizes **Meta MuseAI** on Android for managing personal life workflows (Gmail, Facebook DMs, Instagram messages, notifications, personal tasks). However, MuseAI lacks any hands-free wake word or voice hardware integration.

The user owns an **Amazon Echo Dot (4th Generation)** sitting idle. The initial desire was to flash custom firmware directly onto the Echo Dot to repurpose it into a standalone voice assistant.

### Constraints & Discovered Realities
1. **Echo Dot 4th Gen Hardware Lockdown:** 
   * The Echo Dot 4th Gen uses the MediaTek MT8512 SoC with hardware-enforced cryptographic Secure Boot.
   * Unlike the legacy Echo Dot 2nd Gen (which had vulnerable bootroms used by `EchoMuse`), the 4th Gen has **no public bootloader exploit, no custom firmware, and no Linux port**. Attempting to flash it over USB/UART bricks the device.
   * The device has no 3.5mm line-in (line-out only) and does not stream its microphone array over Bluetooth.
2. **User Operating Constraints:**
   * **No 24/7 PC/Workstation:** The user's single workstation PC cannot remain powered on 24/7 due to power waste, heat, noise, and work isolation.
   * **No Phone as Server:** The user's phone cannot act as an always-on server due to battery drain and mobile lifecycle management.
   * **Zero Cloud Costs ($0.00/mo):** No paid servers, no AWS/GCP services requiring international credit cards (strict currency quota in Bangladesh), and no hidden bill risk.
   * **No Amazon Alexa Skills:** Rejects the clunky UX of saying *"Alexa, open [skill name]"*. Demands natural, direct interaction.
   * **Component Availability:** Raspberry Pi Zero 2W is cost-prohibitive in Bangladesh due to RAM shortages; **ESP32 DevKit V1** is affordable (~350–450 BDT) and readily available.

---

## 2. Decision

We will build **Project Sidecar**: a three-tier hybrid edge-and-cloud architecture:

1. **Hardware Edge Satellite (Physical Room):**
   * **ESP32 DevKit V1** powered by a standard 5V USB charger (consuming <0.5W, running 24/7).
   * **INMP441 I2S Digital Microphone Module** directly wired to the ESP32 for high-clarity 16 kHz digital voice capture.
   * **Amazon Echo Dot (4th Gen)** paired wirelessly to the ESP32 via **Bluetooth Classic (A2DP Source)** to act as the room's high-fidelity voice speaker.
2. **Serverless Global Edge Bridge (Zero Cost, Zero Sleep):**
   * **Cloudflare Workers AI** deployed on Cloudflare's edge network.
   * **Speech-to-Text (STT):** Cloudflare's hosted `@cf/openai/whisper` (10,000 Neurons/day free tier = ~4 hours of speech transcription daily, hard cap with zero billing risk, no credit card required).
   * **AI Gateway:** Direct HTTPS GraphQL communication with Meta MuseAI using stored persistent session cookies (`datr`, `c_user`, `xs`).
   * **Text-to-Speech (TTS):** Edge Neural TTS streaming MP3 audio back to the ESP32.
3. **Proactive Background Triggers:**
   * Cloudflare Worker **Cron Triggers** run every 5 minutes to query MuseAI for proactive notifications/reminders and push audio alerts to the ESP32.

---

## 3. Considered Alternatives

| Alternative | Pros | Cons | Why Rejected |
| :--- | :--- | :--- | :--- |
| **Direct Echo Dot 4th Gen Firmware Flash** | All-in-one hardware | Bricks device; cryptographically impossible | Zero public exploits; hardware-level secure boot |
| **Amazon Alexa Custom Skill** | Uses Echo Dot mic & speaker natively | Terrible UX (*"Alexa, ask my skill..."*); limited response streaming | User strictly rejected Amazon Skills |
| **Local PC / Mini-PC Server** | 100% offline STT/TTS | Wastes power; noisy; requires PC on 24/7 | User has only one PC for work |
| **Hugging Face Spaces Free Tier** | Free Docker container | Sleeps after inactivity (30–60s cold start) | Unacceptable latency for an interactive Jarvis |
| **Google Cloud Run** | Scalable, fast | Requires international credit card; unexpected billing risk in USD | Prior bad experience; currency limits in BD |

---

## 4. Consequences & Trade-offs

### Positive
* **Zero Monthly Operating Cost:** Uses permanent free tiers with strict zero-cost hard caps (no credit card required).
* **Zero Host Dependency:** PC and phone remain completely turned off.
* **Instant Wake & Response:** Cloudflare edge execution (<15ms cold start) gives sub-second end-to-end voice turnaround.
* **Repurposes Existing Hardware:** Idle Echo Dot 4th Gen becomes a room speaker via Bluetooth.
* **Low Hardware Budget:** Only requires an ESP32 DevKit V1 (~400 BDT) and an INMP441 module (~180 BDT).

### Negative / Limitations
* **Meta Session Cookie Maintenance:** Since Meta MuseAI lacks a public developer API, the session cookie (`datr`, `xs`) must be refreshed manually every few months if Meta invalidates web sessions.
* **Bluetooth Range & Pairing:** ESP32 must remain within 5–8 meters of the Echo Dot for stable A2DP audio streaming.
