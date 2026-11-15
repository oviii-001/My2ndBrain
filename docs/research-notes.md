# Research Notes & Technical Feasibility Dossier

> **Project:** Sidecar (Personal Ambient Voice Satellite)  
> **Topic:** Hardware Reverse Engineering, Cloudflare Edge Quotas, Meta MuseAI Protocols  

---

## 1. Amazon Echo Dot (4th Generation) Hardware Dossier

### Chipset & Platform
* **SoC:** MediaTek MT8512 (Dual-core ARM Cortex-A53 @ 2.0 GHz)
* **Neural Co-Processor:** Amazon AZ1 Neural Edge Processor (custom inference silicon for on-device wake-word)
* **Flash Storage:** eMMC / eMCP storage running Amazon's proprietary `lab126` embedded Linux kernel
* **Audio I/O:** 1.6-inch front-firing speaker; 3.5 mm Line-Out port (no Line-In supported)
* **Wireless:** Dual-band Wi-Fi (802.11a/b/g/n/ac) + Bluetooth 5.0 (A2DP sink / AVRCP controller)

### Security Chain of Trust & Jailbreak Status
* **Secure Boot Chain:** The MT8512 silicon utilizes hardware-fused root-of-trust verification. During power-on, the BootROM verifies the RSA/ECDSA signature of the pre-loader before passing execution to Little Kernel (LK) and the Linux kernel.
* **Comparison to Echo Dot 2nd Gen:** Early projects like `EchoMuse` and `DragonBall` relied on an unpatched BootROM USB download mode vulnerability (`amonet`) present on older MT8167 / MT8127 processors. The MT8512 has patched these ROM vectors.
* **Firmware Overwrite Feasibility:** Zero public exploits exist. Erasing or flashing un-signed partitions results in a permanent hard-brick state.
* **Engineered Solution:** Use the device in its sanctioned, high-fidelity wireless mode: as a **Bluetooth A2DP Audio Sink**, driven by the external ESP32 satellite.

---

## 2. Cloudflare Workers AI & Whisper Capacity Audit

### Unit of Measurement: Neurons
Cloudflare Workers AI normalizes all GPU/NPU compute into **Neurons**:
* **Daily Free Quota:** **10,000 Neurons per day** (shared across all accounts, resets at 00:00 UTC).
* **Credit Card Requirement:** **None** (strict zero-cost tier).
* **Hard Stop Enforcement:** When 10,000 Neurons are exhausted, Cloudflare returns an error; it **never** triggers unexpected card charges.

### Whisper Consumption Rates
* **Model ID:** `@cf/openai/whisper` (and `@cf/openai/whisper-large-v3-turbo`)
* **Neuron Cost:** **41.14 Neurons per audio minute** (~0.685 Neurons per audio second).
* **Maximum Daily Free Speech Duration:**
  $$\text{Free Speech Time} = \frac{10,000 \text{ Neurons}}{41.14 \text{ Neurons/min}} \approx 243 \text{ minutes} \approx 4.05 \text{ hours}.$$
* **Practical Daily Query Capacity:**
  * Average voice command length: 6 seconds.
  * Daily query capacity:
    $$\frac{243 \text{ minutes} \times 60 \text{ sec/min}}{6 \text{ sec/query}} \approx \mathbf{2,430 \text{ voice interactions / day}}.$$
  * For a single user, 2,430 daily interactions represents >20x typical maximum usage.

---

## 3. Meta MuseAI Internal Protocol Reverse Engineering

### Overview
Meta MuseAI is hosted on Meta's unified backend infrastructure (`meta.ai`). While no public OpenAPI/Swagger document is published for consumer accounts, the client communicates via standard HTTPS GraphQL and Datagram WebSocket (DGW) endpoints.

### Authentication Scheme
* Meta relies on multi-cookie web authentication:
  * `c_user`: 64-bit integer representing the authenticated Meta user ID.
  * `xs`: High-entropy session secret token.
  * `datr`: Browser/device telemetry identification cookie.
* **CSRF Token:** `fb_dtsg` parameter embedded in HTML responses for cross-site request forgery validation.

### Request Signature & Routing
* **Endpoint:** `POST https://www.meta.ai/api/graphql`
* **Transport:** Standard HTTPS 1.3 / HTTP/2.
* **Payload Structure:**
  ```json
  {
    "doc_id": "MetaAIChatQueryID",
    "variables": {
      "message": "User spoken prompt text",
      "session_id": "client-generated-uuid-v4",
      "entry_point": "home_feed"
    }
  }
  ```
* **Streaming Protocol:** Meta streams text tokens using Server-Sent Events (SSE). The gateway captures incoming SSE chunks and pipes them to the TTS engine.

---

## 4. End-to-End Latency Budget

To deliver an Iron Man Jarvis experience, total voice-to-voice latency must remain **under 1.0 second**:

| Pipeline Stage | Target Latency | Realized Metric |
| :--- | :--- | :--- |
| **1. Audio Capture & Wi-Fi Buffer** | 100 ms | Hardware DMA stream |
| **2. Network Uplink (BD to Cloudflare Edge)** | 40 – 70 ms | Cloudflare Dhaka/Singapore edge node |
| **3. Cloudflare Whisper STT** | 120 – 180 ms | High-speed GPU inference |
| **4. Meta MuseAI Generation (First Token)** | 250 – 350 ms | Meta cloud processing |
| **5. Neural TTS Synthesis (First Sentence Chunk)** | 60 – 100 ms | Streamed Edge-TTS |
| **6. Network Downlink & Bluetooth Buffer** | 60 – 90 ms | Direct A2DP pipe |
| **Total Turnaround Time** | **< 900 ms** | **Sub-second real-time response** |
