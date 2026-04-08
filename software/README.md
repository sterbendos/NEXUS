# NEXUS Desktop Intelligent Analysis Platform

## Overview
NEXUS is a modular PyQt6 desktop application for telemetry ingestion, defensive network analysis, incident response support, evidence handling, and local AI-assisted interpretation.

The embedded firmware (`hardware/OTOM.ino`) is treated as a read-only telemetry source and is not modified.

## Run
```powershell
cd software
python -m pip install -r requirements.txt
python main.py
```

## Default Telemetry JSON Schema
The ingest layer accepts flexible JSON and normalizes into:

```json
{
  "timestamp": "ISO-8601 string (auto-filled if missing)",
  "device_id": "string (defaults to unknown-device)",
  "source": "serial|tcp",
  "channel": "serial|tcp",
  "network": {
    "ip": "string",
    "mac": "string"
  },
  "metrics": {},
  "events": []
}
```

## Key Modules
- `nexus/hardware/telemetry_ingest.py`: serial auto-detect, TCP listener, JSON validation, DB persistence
- `nexus/ai/ai_connector.py`: asynchronous Ollama API integration (`http://localhost:11434`)
- `nexus/db/database.py`: thread-safe SQLite storage and queries
- `nexus/ui/main_window.py`: QMainWindow + sidebar navigation + stacked tabs
- `nexus/controllers/app_controller.py`: signal wiring and app orchestration

## Tabs
1. Dashboard
2. Data Ingest
3. Network Monitor
4. Incident Response
5. Pentesting (Authorized Analysis)
6. AI Analysis
7. Notes Device
8. Logs Database
