from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DatabaseManager:
    """Thread-safe SQLite manager for telemetry, notes, evidence, and AI output."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS anomaly_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telemetry_id INTEGER,
                    event_id TEXT,
                    timestamp TEXT NOT NULL,
                    threat_classification TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    mitigation TEXT NOT NULL,
                    raw_response TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telemetry_id) REFERENCES telemetry_logs(id)
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS evidence_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    tags TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def store_telemetry(self, telemetry: dict[str, Any]) -> int:
        timestamp = str(telemetry.get("timestamp") or self._utc_now())
        device_id = str(telemetry.get("device_id") or "unknown-device")
        source = str(telemetry.get("source") or "unknown")
        channel = str(telemetry.get("channel") or source)
        payload = json.dumps(telemetry, ensure_ascii=True)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO telemetry_logs (timestamp, device_id, source, channel, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, device_id, source, channel, payload),
            )
            return int(cursor.lastrowid)

    def fetch_telemetry(self, device_id: str = "", limit: int = 200) -> list[dict[str, Any]]:
        query = (
            "SELECT id, timestamp, device_id, source, channel, payload "
            "FROM telemetry_logs "
        )
        params: tuple[Any, ...]
        if device_id:
            query += "WHERE device_id = ? "
            params = (device_id, max(1, min(limit, 1000)))
        else:
            params = (max(1, min(limit, 1000)),)
        query += "ORDER BY id DESC LIMIT ?"

        with self._lock, self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            payload_text = row["payload"]
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError:
                payload = {"_raw_payload": payload_text}

            results.append(
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "device_id": row["device_id"],
                    "source": row["source"],
                    "channel": row["channel"],
                    "payload": payload,
                }
            )
        return results

    def count_telemetry(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM telemetry_logs").fetchone()
        return int(row["total"]) if row else 0

    def fetch_device_summary(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    device_id,
                    COUNT(*) AS events,
                    MAX(timestamp) AS last_seen,
                    MAX(
                        CASE
                            WHEN json_valid(payload)
                            THEN json_extract(payload, '$.network.ip')
                            ELSE ''
                        END
                    ) AS ip,
                    MAX(
                        CASE
                            WHEN json_valid(payload)
                            THEN json_extract(payload, '$.network.mac')
                            ELSE ''
                        END
                    ) AS mac
                FROM telemetry_logs
                GROUP BY device_id
                ORDER BY last_seen DESC
                """
            ).fetchall()

        summary: list[dict[str, Any]] = []
        for row in rows:
            summary.append(
                {
                    "device_id": row["device_id"],
                    "events": int(row["events"]),
                    "last_seen": row["last_seen"] or "",
                    "ip": row["ip"] or "",
                    "mac": row["mac"] or "",
                }
            )
        return summary

    def store_anomaly(self, event_type: str, severity: str, details: str, timestamp: str = "") -> int:
        timestamp_value = timestamp or self._utc_now()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO anomaly_logs (timestamp, event_type, severity, details)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp_value, event_type, severity, details),
            )
            return int(cursor.lastrowid)

    def fetch_anomalies(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, event_type, severity, details
                FROM anomaly_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, min(limit, 1000)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def store_ai_analysis(
        self,
        telemetry_id: int | None,
        event_id: str,
        threat_classification: str,
        severity: str,
        mitigation: str,
        raw_response: dict[str, Any] | str,
    ) -> int:
        raw_text = raw_response if isinstance(raw_response, str) else json.dumps(raw_response, ensure_ascii=True)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO ai_analysis (
                    telemetry_id, event_id, timestamp,
                    threat_classification, severity, mitigation, raw_response
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    telemetry_id,
                    event_id,
                    self._utc_now(),
                    threat_classification,
                    severity,
                    mitigation,
                    raw_text,
                ),
            )
            return int(cursor.lastrowid)

    def store_note(self, event_id: str, content: str, timestamp: str = "") -> int:
        timestamp_value = timestamp or self._utc_now()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notes (event_id, timestamp, content)
                VALUES (?, ?, ?)
                """,
                (event_id, timestamp_value, content),
            )
            return int(cursor.lastrowid)

    def fetch_notes(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_id, timestamp, content
                FROM notes
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, min(limit, 1000)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def store_evidence_tag(self, event_id: str, tags: str, description: str) -> int:
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO evidence_tags (event_id, tags, description)
                VALUES (?, ?, ?)
                """,
                (event_id, tags, description),
            )
            return int(cursor.lastrowid)

    def fetch_evidence_tags(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_id, tags, description, created_at
                FROM evidence_tags
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, min(limit, 1000)),),
            ).fetchall()
        return [dict(row) for row in rows]
