---
title: "NEXUS and OTOM"
author: "sterbendos"
description: "An ESP32-S3 firmware platform and PyQt6 desktop command center for telemetry ingest, analysis, and incident review."
created_at: "2026-05-28"
---

# NEXUS and OTOM Journal

## Project Overview

NEXUS is the desktop side of the stack and OTOM is the ESP32-S3 firmware that emits telemetry, accepts a narrow remote job protocol, and mirrors state back to the host over Serial or TCP. The goal of this project is to make the embedded device and the desktop app feel like one system: telemetry in, validation and storage in the middle, then analysis, review, and audited job dispatch back to the device.

This journal tracks the hardware and software build for the Hack Club project submission. It records what changed, why it changed, and what I want to finish next.

## 2026-05-28 - Documentation and demo pass

Today I cleaned up the project so it is easier to understand from the outside and easier to show publicly.

- Replaced the custom license text with the MIT License so the project is clearly open source.
- Rewrote the root `README.md` so it explains the full hardware and software architecture instead of only giving a short overview.
- Added a `demo/` folder with a self-contained browser simulation that can be deployed to Vercel as a public URL.
- Updated the software quick-start documentation so it matches the current desktop application behavior.

The demo matters because it gives the project a safe public face. It shows the idea of the product without connecting to real hardware, which makes it much easier to share in a browser or in a submission page.

## 2026-05-28 - What the system does

The build now has a clear data path:

- OTOM emits newline-delimited JSON telemetry over Serial and, when configured, over TCP.
- NEXUS reads the stream, normalizes missing fields, rate limits noisy input, and stores the result in SQLite.
- The desktop UI presents the data in dedicated tabs for ingest, network monitoring, incident review, notes, logs, chat, and AI analysis.
- The AI path asks a local Ollama model for structured JSON, not free-form prose.
- If the model suggests hardware jobs, NEXUS validates them against an allowlist before sending anything back to the device.
- OTOM validates the job schema, enforces audit mode, and emits job status telemetry so the whole workflow can be audited.

That structure is important to me because I want the project to be explainable end to end, not just impressive on the surface.

## 2026-05-28 - Hardware and firmware notes

The firmware is organized into small modules rather than one giant sketch.

- `telemetry.h` handles telemetry emission and transport.
- `job_control.h` handles the remote job queue and the job allowlist.
- `sd_utils.h`, `rf_tools.h`, `wifi_tools.h`, `rfid_tools.h`, `badusb.h`, `ble_spam.h`, and `jam.h` split the device features into separate subsystems.
- `ui_logic.h` and `ui_draw.h` keep the OLED navigation and presentation logic separate from the rest of the sketch.

That layout makes the device easier to reason about and easier to document. It also makes it clearer which parts are responsible for telemetry, which parts are responsible for state, and which parts are just feature modules.

## 2026-05-28 - Desktop software notes

The Python app is built around a few core layers:

- the ingestion manager for Serial and TCP telemetry
- a thread-safe SQLite database layer
- local Ollama integration for structured analysis and chat
- a notes and evidence workflow for incident review
- a tabbed PyQt6 interface that ties the whole thing together

The most useful part of the desktop app is that it keeps the project grounded in actual workflow. It is not just a viewer; it stores data, supports review, and keeps the AI path constrained enough that the output can be validated before anything is dispatched.

## Current Status

The repository now has:

- a clearer open-source license
- a thorough project README
- a browser demo for public sharing
- a Hack Club journal file at the repo root

## Next Steps

- Add screenshots or photos of the hardware build once they are available.
- Add more journal entries as the device build progresses.
- Tighten the demo if I want a more polished public submission page.
- Keep documenting the hardware and firmware changes as the project moves forward.
