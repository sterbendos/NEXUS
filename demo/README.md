# NEXUS Demo

This folder contains a safe, self-contained static simulation of the NEXUS and OTOM workflow.

What it demonstrates:
- live telemetry events
- serial/TCP transport switching
- audit-mode gating for allowlisted jobs
- an AI-style structured analysis panel
- the telemetry-to-SQLite-to-analysis pipeline concept

What it does not do:
- it does not connect to real hardware
- it does not run the embedded firmware
- it does not send radio, BLE, Wi-Fi, or USB actions

## Local preview

Open `index.html` directly in a browser, or serve the folder with any static server.

Examples:

```powershell
cd demo
py -m http.server 8000
```

Then open `http://localhost:8000`.

## Deploy to Vercel

1. Create a new Vercel project from this repository.
2. Set the project root to `demo`.
3. Keep the framework preset as `Other`.
4. Deploy.

If you prefer the CLI:

```powershell
vercel --cwd demo
```

The result is a public URL that can be shared as a live product demo.
