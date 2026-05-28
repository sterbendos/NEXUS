from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


JOB_SCHEMA_VERSION = "nexus.remote.job.v1"

ALLOWED_JOB_TYPES = {
    "device_inventory",
    "hardware_self_test",
    "passive_survey",
    "config_check",
    "benign_validation",
    "spectrum_scan",
    "link_test",
    "capture_signal",
    "monitor_mode",
    "sd_benchmark",
}

JOB_STATUSES = {"queued", "running", "completed", "blocked", "failed"}


@dataclass(slots=True)
class HardwareJob:
    job_id: str
    job_type: str
    requested_by: str = "nexus-ai"
    audit_mode: bool = True
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": JOB_SCHEMA_VERSION,
            "kind": "job_submit",
            "job_id": self.job_id,
            "job_type": self.job_type,
            "requested_by": self.requested_by,
            "audit_mode": self.audit_mode,
            "arguments": self.arguments,
        }


def validate_job_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    if payload.get("schema") != JOB_SCHEMA_VERSION:
        return False, "Unsupported job schema"
    if payload.get("kind") not in {"job_submit", "job_cancel", "job_status", "job_arm"}:
        return False, "Unsupported job kind"
    if payload.get("kind") == "job_submit":
        job_type = str(payload.get("job_type") or "").strip()
        if not job_type:
            return False, "Missing job_type"
        if job_type not in ALLOWED_JOB_TYPES:
            return False, f"Job type '{job_type}' is not allowlisted"
        job_id = str(payload.get("job_id") or "").strip()
        if not job_id:
            return False, "Missing job_id"
    return True, ""


def build_job_command(
    job_id: str,
    job_type: str,
    requested_by: str = "nexus-ai",
    audit_mode: bool = True,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return HardwareJob(
        job_id=job_id,
        job_type=job_type,
        requested_by=requested_by,
        audit_mode=audit_mode,
        arguments=arguments or {},
    ).to_dict()
