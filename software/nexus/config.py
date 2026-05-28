import os
from pathlib import Path
from urllib.parse import urlparse

APP_NAME = "NEXUS"
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "nexus.db"
DEFAULT_TCP_HOST = "0.0.0.0"
DEFAULT_TCP_PORT = 9000
DEFAULT_SERIAL_BAUD = 115200

_base_url = os.getenv("NEXUS_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
_parsed = urlparse(_base_url)
if not _parsed.scheme or not _parsed.netloc:
    raise ValueError(
        f"Invalid NEXUS_OLLAMA_BASE_URL: {_base_url}. "
        f"Must include scheme and host (e.g. http://localhost:11434)"
    )
OLLAMA_BASE_URL = _base_url

_model = os.getenv("NEXUS_OLLAMA_MODEL", "gemma3:4b")
if not _model or not _model.strip():
    raise ValueError("NEXUS_OLLAMA_MODEL must not be empty")
OLLAMA_MODEL = _model.strip()
