from nexus.hardware.job_protocol import (
    ALLOWED_JOB_TYPES,
    JOB_SCHEMA_VERSION,
    build_job_command,
    validate_job_payload,
)


def test_build_job_command_includes_schema_and_kind():
    job = build_job_command("job-1", "device_inventory", requested_by="nexus-ai", audit_mode=True)
    assert job["schema"] == JOB_SCHEMA_VERSION
    assert job["kind"] == "job_submit"
    assert job["job_id"] == "job-1"
    assert job["job_type"] == "device_inventory"


def test_validate_job_payload_accepts_allowlisted_job():
    payload = build_job_command("job-2", "passive_survey")
    ok, reason = validate_job_payload(payload)
    assert ok is True
    assert reason == ""


def test_validate_job_payload_rejects_unknown_type():
    payload = build_job_command("job-3", "not_allowed")
    ok, reason = validate_job_payload(payload)
    assert ok is False
    assert "allowlisted" in reason


def test_allowed_job_types_cover_expected_families():
    assert "device_inventory" in ALLOWED_JOB_TYPES
    assert "spectrum_scan" in ALLOWED_JOB_TYPES
