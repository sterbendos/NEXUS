"""Tests for nexus.ai.response_parser.ResponseParser."""
from __future__ import annotations

import pytest

from nexus.ai.response_parser import ResponseParser


def test_extracts_hardware_jobs():
    response = {
        "model": "test-model",
        "response": """
        {
          "threat_classification": "Recon",
          "severity": "high",
          "suggested_mitigation": "Survey environment",
          "rationale": "Passive audit requested",
          "hardware_jobs": [
            {
              "schema": "nexus.remote.job.v1",
              "kind": "job_submit",
              "job_id": "job-1",
              "job_type": "device_inventory",
              "requested_by": "nexus-ai",
              "audit_mode": true,
              "arguments": {}
            }
          ]
        }
        """,
    }

    parsed = ResponseParser.parse(response)
    assert parsed["threat_classification"] == "Recon"
    assert parsed["severity"] == "high"
    assert parsed["hardware_jobs"]
    assert parsed["hardware_jobs"][0]["job_type"] == "device_inventory"


def test_empty_response():
    parsed = ResponseParser.parse({"model": "m", "response": ""})
    assert parsed["threat_classification"] == "Unknown"
    assert parsed["severity"] == "medium"
    assert parsed["hardware_jobs"] == []


def test_malformed_json_with_extra_text():
    response = {
        "model": "m",
        "response": 'Here is my analysis:\n{"threat_classification": "Phishing", "severity": "critical"}\nLet me know if you need more.',
    }
    parsed = ResponseParser.parse(response)
    assert parsed["threat_classification"] == "Phishing"
    assert parsed["severity"] == "critical"


def test_missing_keys():
    response = {"model": "m", "response": '{"extra_field": "value"}'}
    parsed = ResponseParser.parse(response)
    assert parsed["threat_classification"] == "Unknown"
    assert parsed["severity"] == "medium"
    assert parsed["suggested_mitigation"] == "No mitigation provided."


def test_invalid_severity_coerced_to_medium():
    response = {"model": "m", "response": '{"severity": "unknown-level"}'}
    parsed = ResponseParser.parse(response)
    assert parsed["severity"] == "medium"


def test_hardware_jobs_not_a_list():
    response = {"model": "m", "response": '{"hardware_jobs": "not_a_list"}'}
    parsed = ResponseParser.parse(response)
    assert parsed["hardware_jobs"] == []


def test_nested_braces():
    response = {
        "model": "m",
        "response": '{"details": {"inner": "value"}, "hardware_jobs": [{"job_id": "1"}]}',
    }
    parsed = ResponseParser.parse(response)
    assert len(parsed["hardware_jobs"]) == 1
    assert parsed["hardware_jobs"][0]["job_id"] == "1"
