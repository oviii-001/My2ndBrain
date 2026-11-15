# Project Sidecar (Ambient Voice Satellite for Meta MuseAI)

> **A 24/7 standalone, hands-free personal voice assistant station powered by Meta MuseAI, using an ESP32 DevKit V1 and an Amazon Echo Dot (4th Gen) at $0.00/month operating cost.**

[![Architecture](https://img.shields.io/badge/Architecture-Serverless%20%2B%20ESP32-blue.svg)](docs/architecture.md)
[![Hardware](https://img.shields.io/badge/Hardware-ESP32%20%2B%20INMP441%20%2B%20Echo%20Dot-orange.svg)](docs/hardware-guide.md)
[![Cost](https://img.shields.io/badge/Monthly%20Cost-%240.00-brightgreen.svg)](docs/research-notes.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What is Project Sidecar?

Meta's **MuseAI** is an autonomous personal AI agent capable of managing your Gmail, Facebook, Instagram DMs, reminders, and daily life. However, it lacks any physical voice presence or hands-free wake word—requiring you to manually open your phone.

**Project Sidecar** gives Meta MuseAI a physical body in your room:
1. You say your wake word in your room (*"Hey Jarvis..."*).
2. An **ESP32 DevKit V1** with an **INMP441 I2S microphone** captures your speech.
3. A zero-cost **Cloudflare Workers AI** serverless bridge transcribes the audio using **Whisper** and relays the command directly to your Meta MuseAI session.
4. Meta MuseAI processes your query and returns the assistant response.
5. Neural Text-to-Speech converts the reply to voice and streams it directly to your **Amazon Echo Dot (4th Gen)** over wireless Bluetooth!
6. **Proactive announcements:** When MuseAI has a reminder or priority alert, your Echo Dot announces it automatically.

---

## ⚡ Key Features

* **Zero PC / Phone Running:** Your workstation and phone remain completely turned off. The ESP32 is powered by any 5V USB charger (<0.5W power consumption).
* **Zero Alexa Skills:** The Echo Dot 4th Gen is used strictly as a high-fidelity wireless Bluetooth speaker. No clunky *"Alexa, open skill"* commands.
* **100% Free Forever ($0.00/mo):** Built entirely within Cloudflare's permanent free tiers (10,000 free Neurons/day = ~4 hours of speech daily, 100,000 requests/day). **No credit card required.**
* **Sub-Second Latency:** Cloudflare's global edge network provides <900ms end-to-end voice turnaround.
* **Low Budget Hardware:** Built for under **~700 BDT (~$6 USD)** using standard hobbyist parts available in Bangladesh.

---

## 🏗️ Repository Layout

```
.
├── docs/
│   ├── adr/
│   │   └── 0001-architecture-selection.md  # Architectural Decision Record
│   ├── architecture.md                     # System architecture & sequence diagrams
│   ├── hardware-guide.md                   # Shopping list (BD), pinouts & wiring guide
│   └── research-notes.md                   # Technical research on Echo Dot, Cloudflare & Muse
├── tasks/
│   ├── plan.md                             # Phase-by-phase implementation plan
│   └── todo.md                             # Interactive master task checklist
├── cloud-gateway/                          # Cloudflare Workers AI backend (TypeScript)
└── firmware/                               # ESP32 C++ firmware (PlatformIO / Arduino)
```

---

## 🛒 Hardware Required

1. **ESP32 DevKit V1** (ESP-WROOM-32, 30-pin or 38-pin) (~350–450 BDT)
2. **INMP441 I2S Digital Microphone Module** (~150–220 BDT)
3. **Amazon Echo Dot (4th Gen)** (Used as Bluetooth audio speaker)
4. **5x Female-to-Female Jumper Wires**
5. **Standard 5V Micro-USB Phone Charger**

See [docs/hardware-guide.md](docs/hardware-guide.md) for detailed wiring diagrams and local store sourcing in Bangladesh.

---

## 🚀 Quick Reference & Documentation Links

* [Architectural Decision Record (ADR 0001)](docs/adr/0001-architecture-selection.md)
* [System Architecture & Sequence Diagrams](docs/architecture.md)
* [Hardware Pinout & Setup Guide](docs/hardware-guide.md)
* [Research Notes & Feasibility Dossier](docs/research-notes.md)
* [Master Task Checklist](tasks/todo.md)

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
