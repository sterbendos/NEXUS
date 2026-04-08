<div align="center">
  
# ☠️ OTOM & NEXUS Ecosystem

**The Ultimate Open-Source Hardware Pentesting Multi-Tool & AI Command Center.**

[![ESP32-S3](https://img.shields.io/badge/Hardware-ESP32--S3-orange.svg)](#)
[![Python Applications](https://img.shields.io/badge/NEXUS-Python%20%7C%20PyQt6-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#)
[![Status: Active](https://img.shields.io/badge/Status-Active%20Development-success.svg)](#)

</div>

---

## 📖 Overview
The **OTOM** is a powerful, portable, ESP32-S3-powered penetration testing device (similar to the Flipper Zero/Hak5 tools) designed for wireless auditing, physical security bypasses, and red-team engagements. 

It acts seamlessly alongside **NEXUS**, a comprehensive Python/PyQt6 desktop command-and-control (C2) dashboard. NEXUS ingests raw packet data from the OTOM via Serial or TCP, stores it in an SQLite database, and runs it through an integrated AI Threat-Analysis engine.

---

## ⚡ Hardware Capabilities (OTOM)
Built modularly in C++ for the ESP32-S3, the OTOM device features a 128x64 OLED display, an SD card module, and dual nRF24L01 radios for complex RF attacks.

* 💥 **Wi-Fi Beacon Spammer:** Hijacks the native 802.11 modem to flood the local spectrum with dozens of randomized fake access points/SSIDs.
* ⌨️ **BadUSB (Native HID):** Uses the ESP32-S3's hardware Native USB to execute lethal Keystroke Injection (DuckyScript) payloads locally on the target machine.
* 📶 **Bluetooth / BLE Spam:** Targets Apple, Windows, and Android devices with spoofed pairing requests to overwhelm targeted local phones and PCs.
* 📡 **RF Jamming:** High-speed channel sweeping and precision carrier-wave jamming using dual nRF24 radios covering the 2.4GHz spectrum.
* 💾 **Signal Capture & Replay:** Captures raw 2.4GHz payload envelopes and saves them to the SD card for later reverse-engineering or replay attacks.
* 🎮 **DOOM Raycaster:** Includes a fully playable, 1-bit retro 3D raycasting engine directly inside the main UI (complete with destructible walls and HUD metrics) because... why not?

---

## 🖥️ Desktop Dashboard (NEXUS)
The NEXUS client ensures you don't just collect data—you understand it. 

* **Real-time Telemetry:** Parses incoming Serial/TCP data from the OTOM and visualizes network endpoints and anomalous device events in real-time.
* **AI Engine:** Pushes captured signals and telemetry directly through a localized AI module to dynamically classify threats, score severity, and spit out recommended mitigations.
* **PCAP Analysis:** Built-in integration with `pyshark` to quickly analyze massive network capture files without dropping into Wireshark.
* **Incident Reports:** Integrated Markdown/PDF note-taking to automatically generate standard Pentest Incident Response Reports based on captured data.

---

## 🛠️ Required Hardware Components
- 1x **ESP32-S3 Dev Board** (Must have Native USB capability for BadUSB to function).
- 1x **128x64 OLED Display** (I2C: SDA/SCL).
- 2x **nRF24L01 Transceivers**.
- 1x **microSD Card Breakout Module**.
- 5x Tactile Push Buttons (Up, Down, Enter, Exit, Confirm).

---

## 🚀 Installation & Flashing

### Firmware (OTOM)
1. Clone this repository to your machine.
2. Open `hardware/OTOM/OTOM.ino` in the Arduino IDE.
3. Install the required libraries via the Arduino Library Manager:
   - `Adafruit GFX Library`
   - `Adafruit SH110X`
   - `RF24` (by TMRh20)
   - `RoboEyes`
4. Select your **ESP32S3 Dev Module** in the Board Manager.
5. Set **Tools -> USB CDC On Boot** to **Enabled**.
6. Click **Upload**.

> **Note:** If the Arduino Boards Manager fails to download the ESP32 core, execute the included `install_esp32_core.bat` script to manually force-clone the required compilers directly from GitHub.

### Client (NEXUS)
It is recommended to run NEXUS inside a Python virtual environment.
```bash
cd software
python -m venv .venv
source .venv/Scripts/activate  # (or .venv\Scripts\activate on Windows)
pip install -r requirements.txt
python main.py
```

---

## 📜 Legal / Disclaimer
This toolset is developed **strictly for educational and professional network auditing purposes**. You must have explicit, mutual, and written consent from the network/device owner before performing any RF interference, network injection, or Keystroke Injection attacks. The creators assume NO responsibility for any illegal use or damages caused by the improper use of this hardware and software ecosystem. Use responsibly.
