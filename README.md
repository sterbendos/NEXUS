<div align="center">

# OTOM and NEXUS Ecosystem

**Open-source hardware tooling plus a Python desktop command center for telemetry, analysis, and incident review.**

[![ESP32-S3](https://img.shields.io/badge/Hardware-ESP32--S3-orange.svg)](#)
[![Python Applications](https://img.shields.io/badge/NEXUS-Python%20%7C%20PyQt6-blue.svg)](#)
[![License: CUSTOM](https://img.shields.io/badge/License-MIT-green.svg)](#)
[![Status: Active](https://img.shields.io/badge/Status-Active%20Development-success.svg)](#)

</div>

---

## Overview
OTOM is an ESP32-S3-based embedded device that produces telemetry and device-state data. NEXUS is the companion Python/PyQt6 desktop application that ingests that data over Serial or TCP, stores it in SQLite, and provides local AI-assisted analysis, notes, logs, and incident review.

## Hardware Capabilities
- Wi-Fi scanning and beacon-related telemetry
- Native USB HID support
- BLE and RF tooling
- SD card logging and replay workflows
- OLED-based UI for on-device navigation
- Built-in telemetry output for the desktop client

## Desktop Dashboard
- Real-time telemetry ingest from Serial or TCP
- SQLite-backed log, note, and evidence storage
- Local Ollama integration for analysis and chat
- PCAP inspection via PyShark
- Incident-focused views for timelines, anomalies, and notes

## Requirements
- ESP32-S3 dev board with native USB support
- 128x64 OLED display
- 2x nRF24L01 transceivers
- microSD card breakout module
- Tactile buttons for navigation

## Installation

### Firmware
1. Open `hardware/OTOM/OTOM.ino` in Arduino IDE.
2. Install the required libraries from the Arduino Library Manager.
3. Select the ESP32S3 board profile.
4. Enable USB CDC on boot.
5. Upload the sketch.

### Desktop Client
```powershell
cd software
py -3 -m venv .venv
.venv\Scripts\activate
py -3 -m pip install -r requirements.txt
py -3 main.py
```

## Configuration
- `NEXUS_OLLAMA_BASE_URL` sets the Ollama server URL
- `NEXUS_OLLAMA_MODEL` sets the model name

## Disclaimer
Use this project only for authorized testing, research, and defensive analysis on systems you own or have permission to assess.
