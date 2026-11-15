# Hardware Shopping & Wiring Guide — Project Sidecar

> **Target Device:** ESP32 DevKit V1 (30-pin / 38-pin) + INMP441 Microphone + Amazon Echo Dot 4th Gen  
> **Location / Market:** Bangladesh (BD)  

---

## 1. Shopping List for Tomorrow (What to Buy in BD)

You can find all these items in local electronics markets (e.g., Stadium Market / Patuatuly in Dhaka) or online via **TechshopBD**, **RobomartBD**, or **Daraz**.

| Item | Model / Spec | Estimated Price (BDT) | Purpose |
| :--- | :--- | :--- | :--- |
| **1. ESP32 DevKit V1** | ESP-WROOM-32 (30-pin or 38-pin version) | ~350 – 450 BDT | Core Wi-Fi & Bluetooth microcontroller |
| **2. Digital Mic Module** | **INMP441** (Omnidirectional I2S Digital Mic) | ~150 – 220 BDT | Room audio capture with direct digital I2S clarity |
| **3. Jumper Wires** | Female-to-Female (F-F) Dupont wires (at least 5–10 pcs) | ~40 – 60 BDT | Connecting INMP441 to ESP32 pins without soldering |
| **4. Micro-USB Cable** | Good quality data/charging cable | ~80 – 120 BDT (or use existing) | Powering & programming ESP32 from any 5V phone charger |
| **5. (Optional) Breadboard** | Mini Breadboard (170-point or 400-point) | ~60 – 100 BDT | Easy testing without loose dangling wires |

> **Total Budget:** ~**650 – 850 BDT** (~$5–$7 USD total). No expensive hardware, no inflated Pi prices.

---

## 2. INMP441 to ESP32 DevKit V1 Pinout & Wiring

The **INMP441** is an I2S digital microphone. It sends clean digital audio directly to the ESP32's hardware I2S registers, completely eliminating analog noise.

### Pinout Mapping Table

| INMP441 Pin | ESP32 GPIO Pin | Wire Function | Notes |
| :--- | :--- | :--- | :--- |
| **VDD** | **3V3** (3.3V) | Power supply | ⚠️ Do NOT connect to 5V (3.3V logic only) |
| **GND** | **GND** | Ground | Common ground |
| **SD** | **GPIO 32** (or GPIO 22) | Serial Data (I2S Data In) | Transmits raw PCM digital audio bits |
| **WS** | **GPIO 25** (or GPIO 15) | Word Select (Left/Right Clock) | Audio frame synchronization clock |
| **SCK** | **GPIO 33** (or GPIO 14) | Serial Clock (Bit Clock) | I2S bit clock signal |
| **L/R** | **GND** | Left / Right Channel Select | Tie to **GND** for Left channel mono output |

```
    INMP441 Module                    ESP32 DevKit V1
   ┌───────────────┐                 ┌───────────────┐
   │          VDD  │ ──────────────► │ 3V3           │
   │          GND  │ ──────────────► │ GND           │
   │          L/R  │ ───┐            │               │
   │               │   (tie to GND)  │               │
   │          SD   │ ──────────────► │ GPIO 32       │
   │          WS   │ ──────────────► │ GPIO 25       │
   │          SCK  │ ──────────────► │ GPIO 33       │
   └───────────────┘                 └───────────────┘
```

---

## 3. Amazon Echo Dot (4th Gen) Wireless Pairing Setup

You do **not** need to open or tamper with your Echo Dot.

1. Power on your **Amazon Echo Dot (4th Gen)** using its original power adapter.
2. Put the Echo Dot into Bluetooth Pairing Mode:
   * Open the **Alexa App** on your phone ➔ **Devices** ➔ **Echo & Alexa** ➔ Select your Echo Dot ➔ **Bluetooth Devices** ➔ **Pair a New Device**.
   * *Or simply say:* *"Alexa, pair Bluetooth."*
3. The Echo Dot will say: *"Searching..."*
4. In our ESP32 firmware configuration, we will scan and bind the Echo Dot's Bluetooth MAC address directly. Once paired once, the ESP32 will auto-connect instantly every time it boots!

---

## 4. Hardware Verification Checklist (When you unpack tomorrow)

- [ ] Inspect the ESP32 board: ensure the micro-USB port is firmly mounted and pins are straight.
- [ ] Connect the ESP32 to your PC via USB: the red power LED should glow solid.
- [ ] Inspect the INMP441 board: ensure the tiny microphone hole in the center is clean and unobstructed.
- [ ] Keep jumper wires firmly seated: loose jumper wires on I2S clock lines (SCK/WS) are the #1 cause of audio buzzing.
