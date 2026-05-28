"""Tests for nexus.db.database.DatabaseManager (current schema)."""
from __future__ import annotations

import json
import threading

import pytest

from nexus.db.database import DatabaseManager


@pytest.fixture()
def temp_db(tmp_path):
    db_path = tmp_path / "test_nexus.db"
    manager = DatabaseManager(db_path)
    yield manager


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def test_tables_created(temp_db):
    with temp_db._connect() as conn:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert "telemetry_logs" in tables
    assert "anomaly_logs" in tables
    assert "ai_analysis" in tables
    assert "notes" in tables
    assert "evidence_tags" in tables


# ---------------------------------------------------------------------------
# Telemetry CRUD
# ---------------------------------------------------------------------------

def test_store_and_fetch_telemetry(temp_db):
    payload = {"device_id": "dev-1", "source": "tcp", "channel": "tcp", "metrics": {}}
    row_id = temp_db.store_telemetry(payload)
    assert row_id > 0

    rows = temp_db.fetch_telemetry()
    assert len(rows) == 1
    assert rows[0]["device_id"] == "dev-1"


def test_count_telemetry(temp_db):
    assert temp_db.count_telemetry() == 0
    temp_db.store_telemetry({"device_id": "d"})
    assert temp_db.count_telemetry() == 1


def test_fetch_telemetry_device_filter(temp_db):
    temp_db.store_telemetry({"device_id": "alpha"})
    temp_db.store_telemetry({"device_id": "beta"})
    rows = temp_db.fetch_telemetry(device_id="alpha")
    assert len(rows) == 1
    assert rows[0]["device_id"] == "alpha"


# ---------------------------------------------------------------------------
# Anomaly CRUD
# ---------------------------------------------------------------------------

def test_store_and_fetch_anomaly(temp_db):
    row_id = temp_db.store_anomaly("ingest_error", "medium", "bad JSON")
    assert row_id > 0
    anomalies = temp_db.fetch_anomalies()
    assert len(anomalies) == 1
    assert anomalies[0]["event_type"] == "ingest_error"


# ---------------------------------------------------------------------------
# Purge
# ---------------------------------------------------------------------------

def test_purge_old_telemetry(temp_db):
    for i in range(10):
        temp_db.store_telemetry({"device_id": f"d{i}"})
    assert temp_db.count_telemetry() == 10

    deleted = temp_db.purge_old_telemetry(keep_last_n=5)
    assert deleted == 5
    assert temp_db.count_telemetry() == 5


def test_purge_keeps_most_recent(temp_db):
    for i in range(5):
        temp_db.store_telemetry({"device_id": f"old-{i}"})
    last_id = temp_db.store_telemetry({"device_id": "newest"})

    temp_db.purge_old_telemetry(keep_last_n=1)
    rows = temp_db.fetch_telemetry()
    assert len(rows) == 1
    assert rows[0]["device_id"] == "newest"


def test_purge_old_anomalies(temp_db):
    for _ in range(6):
        temp_db.store_anomaly("x", "low", "detail")
    deleted = temp_db.purge_old_anomalies(keep_last_n=3)
    assert deleted == 3
    assert len(temp_db.fetch_anomalies()) == 3


# ---------------------------------------------------------------------------
# Device summary
# ---------------------------------------------------------------------------

def test_fetch_device_summary(temp_db):
    temp_db.store_telemetry({"device_id": "dev-A", "network": {"ip": "10.0.0.1", "mac": "aa:bb"}})
    temp_db.store_telemetry({"device_id": "dev-A"})
    summary = temp_db.fetch_device_summary()
    assert len(summary) == 1
    assert summary[0]["events"] == 2
    assert summary[0]["ip"] == "10.0.0.1"


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_concurrent_writes(temp_db):
    def worker(n):
        for i in range(10):
            temp_db.store_telemetry({"device_id": f"worker-{n}-{i}"})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert temp_db.count_telemetry() == 50
