# NEXUS Desktop Quick Start

This folder contains the PyQt6 desktop client that ingests OTOM telemetry, stores it in SQLite, runs local Ollama analysis, and can dispatch allowlisted hardware jobs back to the device when audit mode is armed.

For the full system overview, firmware architecture, telemetry schema, and demo deployment instructions, see the repository root [README](../README.md).

## Run

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

## What The Desktop App Does

- opens Serial or TCP telemetry sessions
- validates and normalizes JSON telemetry
- stores telemetry, anomalies, notes, evidence tags, and AI output in SQLite
- shows a dashboard, network monitor, incident view, notes editor, logs browser, and AI tabs
- sends structured telemetry to Ollama and parses the response back into stable JSON
- validates and serializes `nexus.remote.job.v1` commands before dispatch

## Helpful Modules

- `nexus/app.py`: application composition
- `nexus/controllers/app_controller.py`: signal wiring and orchestration
- `nexus/hardware/telemetry_ingest.py`: serial/TCP ingest and validation
- `nexus/hardware/job_protocol.py`: job schema helpers
- `nexus/db/database.py`: SQLite storage
- `nexus/ai/ai_connector.py`: analysis requests to Ollama
- `nexus/ai/chat_connector.py`: conversational Ollama chat
- `nexus/notes/notes_service.py`: notes storage and export
- `nexus/ui/`: tabbed UI and dashboard widgets
