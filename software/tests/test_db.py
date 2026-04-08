import pytest
import sqlite3
import threading
from pathlib import Path
from nexus.db.database_manager import DatabaseManager

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_nexus.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize()
    yield manager
    
def test_db_initialization(temp_db):
    conn = temp_db._get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    assert "events" in tables
    assert "devices" in tables
    assert "evidence_tags" in tables
    assert "ai_insights" in tables

def test_insert_device(temp_db):
    temp_db.insert_device("OTOM-123", "esp32-firmware", "192.168.1.10", "AA:BB:CC:DD:EE:FF")
    
    conn = temp_db._get_connection()
    c = conn.cursor()
    c.execute("SELECT device_id, source, ip_address, mac_address FROM devices")
    row = c.fetchone()
    
    assert row is not None
    assert row[0] == "OTOM-123"
    assert row[1] == "esp32-firmware"
    assert row[2] == "192.168.1.10"
    assert row[3] == "AA:BB:CC:DD:EE:FF"
    
def test_insert_telemetry_event(temp_db):
    event_id = temp_db.insert_telemetry_event(
        timestamp="2024-03-01T12:00:00Z",
        device_id="OTOM-123",
        source="tcp",
        channel="tcp",
        event_type="heartbeat",
        severity="info",
        message="alive",
        anomaly=False,
        raw_json='{"status": "ok"}'
    )
    
    assert event_id > 0
    
    conn = temp_db._get_connection()
    c = conn.cursor()
    c.execute("SELECT event_type, message FROM events WHERE id=?", (event_id,))
    row = c.fetchone()
    
    assert row is not None
    assert row[0] == "heartbeat"
    assert row[1] == "alive"

def test_concurrent_writes(temp_db):
    # Ensure SQLite WAL mode and connection pooling handle concurrent inserts
    def worker(worker_id):
        for i in range(10):
            temp_db.insert_telemetry_event(
                timestamp=f"2024-03-01T12:00:{worker_id}{i}Z",
                device_id=f"device-{worker_id}",
                source="tcp",
                channel="tcp",
                event_type="test",
                severity="info",
                message=f"msg {i}",
                anomaly=False,
                raw_json="{}"
            )
            
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    conn = temp_db._get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM events")
    count = c.fetchone()[0]
    
    assert count == 50
