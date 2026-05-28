import pytest
from datetime import datetime, timezone
from nexus.hardware.telemetry_ingest import TelemetrySchemaValidator

@pytest.fixture
def validator():
    return TelemetrySchemaValidator()

def test_validator_normalizes_empty_timestamp(validator):
    payload = {"device_id": "test-device"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    
    assert valid is True
    assert "timestamp" in result
    assert "T" in result["timestamp"]  # ISO format

def test_validator_normalizes_epoch_timestamp(validator):
    # Test seconds
    payload = {"timestamp": 1709650000, "device_id": "test-device"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert valid is True
    assert "2024" in result["timestamp"]
    
    # Test milliseconds
    payload = {"timestamp": 1709650000123, "device_id": "test-device"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert valid is True
    assert "2024" in result["timestamp"]

def test_validator_handles_missing_device_id(validator):
    payload = {}
    valid, result, err = validator.validate(payload, "serial", "serial")
    
    assert valid is True
    assert result["device_id"] == "unknown-device"

def test_validator_handles_different_device_id_keys(validator):
    payload = {"device": "OTOM-123"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert result["device_id"] == "OTOM-123"
    
    payload = {"id": "OTOM-456"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert result["device_id"] == "OTOM-456"

def test_validator_rejects_non_dict(validator):
    valid, result, err = validator.validate("string payload", "tcp", "tcp")
    assert valid is False
    assert "JSON object" in err

def test_validator_ensures_network_and_metrics_dicts(validator):
    payload = {"network": "bad", "metrics": "bad", "events": "bad"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    
    assert valid is True
    assert isinstance(result["network"], dict)
    assert result["network"]["ip"] == ""
    assert isinstance(result["metrics"], dict)
    assert isinstance(result["events"], list)


def test_validator_normalizes_negative_epoch(validator):
    payload = {"timestamp": -1, "device_id": "test"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert valid is True
    assert "T" in result["timestamp"]


def test_validator_handles_very_long_device_id(validator):
    payload = {"device_id": "x" * 10000}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert valid is True
    assert len(result["device_id"]) == 10000


def test_validator_handles_unicode_device_id(validator):
    payload = {"device_id": "héllo-世界"}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert valid is True
    assert result["device_id"] == "héllo-世界"


def test_validator_handles_nested_malicious_payload(validator):
    payload = {"device_id": "test", "__proto__": {"admin": True}}
    valid, result, err = validator.validate(payload, "tcp", "tcp")
    assert valid is True
    assert result.get("__proto__") == {"admin": True}
