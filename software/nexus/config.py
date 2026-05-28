import os
from pathlib import Path

APP_NAME = "NEXUS"
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "nexus.db"
OLLAMA_BASE_URL = os.getenv("NEXUS_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("NEXUS_OLLAMA_MODEL", "gemma3:4b")
DEFAULT_TCP_HOST = "0.0.0.0"
DEFAULT_TCP_PORT = 9000
DEFAULT_SERIAL_BAUD = 115200
