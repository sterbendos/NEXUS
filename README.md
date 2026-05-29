<div align="center">

# NEXUS and OTOM Ecosystem

**An ESP32-S3 firmware platform plus a PyQt6 desktop command center for telemetry ingest, local analysis, and incident review.**

[![ESP32-S3](https://img.shields.io/badge/Hardware-ESP32--S3-orange.svg)](#)
[![Python Applications](https://img.shields.io/badge/NEXUS-Python%20%7C%20PyQt6-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-success.svg)](#)

</div>

---

## Overview

NEXUS is the desktop side of the system. OTOM is the ESP32-S3 firmware that emits telemetry and accepts a narrow, allowlisted remote job protocol. NEXUS ingests those streams over Serial or TCP, normalizes them, stores them in SQLite, and exposes a workflow for analysis, notes, evidence, and incident review.

This repository also includes `demo/`, a safe static simulation that can be deployed to Vercel or any other static host to show the product in a browser without connecting to real hardware.

If you only want the software quick start, `software/README.md` still contains the short run guide. This top-level README is the canonical architecture document.

## What Lives Where

- `hardware/OTOM/`: the ESP32-S3 firmware sketch and module headers.
- `hardware/PCB/`: the KiCad hardware project.
- `software/`: the PyQt6 desktop application and tests.
- `demo/`: the Vercel-friendly public simulation.

## How The System Works

The live system is a pipeline:

1. OTOM boots, initializes the display, buttons, radios, SD card, telemetry output, and optional Wi-Fi TCP telemetry server.
2. The firmware prints newline-delimited JSON telemetry to Serial and, when Wi-Fi is available, mirrors the same stream over TCP.
3. NEXUS opens either transport, validates the JSON, fills in missing fields, and stores the result in SQLite.
4. The desktop UI shows the data in dedicated tabs for ingest, network summary, incidents, AI analysis, notes, logs, and chat.
5. The AI layer sends the telemetry to a local Ollama model and asks for structured JSON output.
6. If the model suggests hardware jobs, NEXUS validates those jobs against the allowlist, serializes them as `nexus.remote.job.v1`, and sends them back to the device.
7. OTOM validates the job schema, enforces audit mode, queues or blocks the job, and emits job status telemetry back into the same stream.

## OTOM Firmware

The firmware entry point is `hardware/OTOM/OTOM.ino`. It wires together a modular set of headers that each own one subsystem:

- `telemetry.h`: JSON telemetry emission, heartbeat scheduling, Serial/TCP delivery, and TCP client handling.
- `job_control.h`: the remote job queue, schema validation, allowlist enforcement, audit-mode gating, and job status telemetry.
- `ui_logic.h` and `ui_draw.h`: menu navigation and the OLED presentation flow.
- `sd_utils.h`: SD card mounting, storage, and replay helpers.
- `rf_tools.h`, `wifi_tools.h`, `ble_spam.h`, `rfid_tools.h`, `badusb.h`, and `jam.h`: lab-focused tooling modules that are part of the firmware tree.
- `buttons.h`, `eyes.h`, `types.h`, `globals.h`, `config.h`, and related headers: shared state, enums, pin mapping, and display state.

The main loop is state-driven. It updates buttons, telemetry, and job control every cycle, then dispatches to the current UI or run mode. Long-running actions are broken out into their own run states so the firmware can keep responding to input.

### Telemetry Format

OTOM emits JSON objects as single lines. NEXUS accepts flexible payloads, but the firmware format includes the fields below:

```json
{
  "timestamp": "millis-derived value",
  "device_id": "OTOM-XXXXXX",
  "source": "esp32-firmware",
  "channel": "serial",
  "event_id": "42",
  "event_type": "heartbeat",
  "severity": "info",
  "message": "Periodic status",
  "anomaly": false,
  "network": {
    "ip": "192.168.4.20",
    "mac": "24:6F:XX:XX:XX:XX"
  },
  "metrics": {
    "sd_ready": 1,
    "nrf1_ready": 1,
    "nrf2_ready": 1,
    "session_on": 0,
    "captured_count": 0,
    "wifi_count": 0,
    "file_count": 0,
    "menu_index": 0
  },
  "events": [
    {
      "name": "heartbeat",
      "message": "Periodic status"
    }
  ],
  "state": {
    "ui_mode": "menu",
    "page": "status",
    "run_mode": "none"
  }
}
```

OTOM also emits `job_status` records for queued, running, completed, blocked, and failed jobs so the desktop app can audit the whole lifecycle.

### Job Protocol

The remote job channel uses the schema `nexus.remote.job.v1`. The desktop app only sends allowlisted jobs and the firmware only accepts the same allowlist. The accepted job types are:

- `device_inventory`
- `hardware_self_test`
- `passive_survey`
- `config_check`
- `benign_validation`
- `spectrum_scan`
- `link_test`
- `capture_signal`
- `monitor_mode`
- `sd_benchmark`

The firmware enforces two extra gates:

- the job kind must be one of the supported job message types
- audit mode must be armed, or the submitted payload must explicitly set `audit_mode: true`

This keeps the command path narrow and auditable.

## NEXUS Desktop Software

`software/main.py` starts the PyQt6 application and hands control to `nexus/app.py`. The application is composed from a small number of focused modules:

- `nexus/app.py`: builds the database, ingest manager, AI connectors, notes service, and main window.
- `nexus/controllers/app_controller.py`: connects UI signals to the ingest, database, AI, notes, and job-dispatch flows.
- `nexus/hardware/telemetry_ingest.py`: opens Serial or TCP, validates inbound JSON, rate-limits noisy sources, and forwards normalized telemetry to the database writer thread.
- `nexus/hardware/job_protocol.py`: serializes and validates job payloads before dispatch.
- `nexus/db/database.py`: owns the SQLite schema and all read/write operations.
- `nexus/ai/ai_connector.py`: sends telemetry to Ollama for structured analysis.
- `nexus/ai/chat_connector.py`: maintains the conversational chat interface.
- `nexus/ai/prompt_formatter.py`: tells the model what JSON structure to return and which job types are allowed.
- `nexus/ai/response_parser.py`: extracts and normalizes the model response back into a stable schema.
- `nexus/notes/notes_service.py`: stores notes and exports Markdown or PDF.
- `nexus/ui/*`: the tabbed interface and dashboard presentation layer.

### Desktop Tabs

The main window exposes the following workflows:

- Dashboard: live status, telemetry preview, and environment summary.
- Data Ingest: Serial and TCP listener controls plus parsed/raw telemetry views.
- Network Monitor: discovered devices and last-seen summaries.
- Incident Response: anomaly timeline and review workflow.
- Pentesting: PCAP inspection and evidence tagging for authorized analysis.
- AI Analysis: structured model output plus dispatchable hardware jobs.
- AI Chat: a conversational Ollama-backed assistant.
- Notes Device: Markdown notes and PDF export.
- Logs Database: SQLite telemetry queries and CSV export.

### Storage Model

The SQLite database stores four core records plus evidence tags:

- `telemetry_logs`
- `anomaly_logs`
- `ai_analysis`
- `notes`
- `evidence_tags`

The ingest layer stores normalized telemetry rows, the controller adds anomalies and AI output, and the notes service records operator commentary that can be exported later.

## AI Flow

NEXUS does not ask the model for free-form prose. It asks for a structured JSON object with these keys:

- `threat_classification`
- `severity`
- `suggested_mitigation`
- `rationale`
- `hardware_jobs`

That design matters because the app can parse the model response deterministically, store it, and only dispatch jobs that still pass validation.

The chat path is separate from the telemetry-analysis path. Chat keeps a conversational history with a system prompt, while analysis is a single structured request derived from the current telemetry payload.

## Hardware and Software Requirements

### Hardware

- ESP32-S3 dev board with native USB support
- 128x64 OLED display
- 2x nRF24L01 transceivers
- microSD card breakout module
- Tactile buttons for navigation

### Software

- Python 3.10 or newer
- PyQt6
- PyQt6-Charts, optional, for the Dashboard events/sec chart
- pyserial
- requests
- pyshark, optional, for PCAP summaries
- Ollama running locally if you want AI analysis and chat

If you want PCAP summaries, the Python dependency is only part of the stack. PyShark also works best when `tshark` or Wireshark is available on the machine.

## Installation

### Desktop Client

```powershell
cd software
py -3.10 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

Optional environment variables:

- `NEXUS_OLLAMA_BASE_URL`: Ollama server URL, defaults to `http://localhost:11434`
- `NEXUS_OLLAMA_MODEL`: model name, defaults to `gemma3:4b`

### Firmware

1. Open `hardware/OTOM/OTOM.ino` in Arduino IDE or PlatformIO.
2. Install the required board support and libraries.
3. Select the ESP32-S3 board profile.
4. Enable USB CDC on boot if your board requires it.
5. Upload the sketch and open the serial monitor if you want to watch the raw telemetry.

The firmware automatically emits telemetry on boot and will also accept TCP telemetry when Wi-Fi is configured in `hardware/OTOM/config.h`.

## Public Demo and Vercel

The `demo/` folder is a safe interactive simulation of the system. It shows:

- live telemetry events
- transport switching between serial and TCP
- audit-mode job gating
- a structured AI analysis panel
- the telemetry-to-SQLite-to-review pipeline concept

It does not connect to the actual firmware and it does not send radio, BLE, Wi-Fi, or USB actions.

### Deploy On Vercel

1. Create a new Vercel project from this repository.
2. Set the project root directory to `demo`.
3. Keep the framework preset as `Other`.
4. Deploy.

You can also run the static demo locally:

```powershell
cd demo
py -m http.server 8000
```

Then open `http://localhost:8000`.

## Repository Layout

- `hardware/OTOM/`: firmware modules and telemetry output
- `hardware/PCB/`: KiCad project files and backups
- `software/nexus/`: desktop application code
- `software/tests/`: unit tests for the desktop side
- `software/data/`: local SQLite database file
- `demo/`: browser-based simulation for public sharing

## Safety

This repository is intended for authorized research, development, and lab use. Some firmware modules are experimental or lab-only. The public demo intentionally excludes those actions and only simulates the product workflow.

## this project was built assisted with AI. 
## License

The project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.
