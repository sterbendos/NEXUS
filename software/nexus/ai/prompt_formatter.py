from __future__ import annotations

import json
from typing import Any


class PromptFormatter:
    """Create structured prompts from telemetry or raw logs."""

    @staticmethod
    def build_prompt(log_payload: dict[str, Any]) -> str:
        telemetry_json = json.dumps(log_payload, ensure_ascii=True, indent=2)
        return (
            "Analyze this cybersecurity telemetry and return valid JSON.\n"
            "Classification: [Name of the attack]\n"
            "Severity: [low, medium, high, or critical]\n"
            "Mitigation: [What to do about it]\n"
            "Rationale: [Brief explanation]\n\n"
            "Use keys: threat_classification, severity, suggested_mitigation, rationale, hardware_jobs.\n"
            "hardware_jobs must be an array of typed job requests using schema 'nexus.remote.job.v1'.\n"
            "Only propose allowlisted, authorized audit jobs. Prefer passive tests unless the telemetry explicitly warrants a lab-only active test.\n\n"
            "Each hardware job object should include: job_id, job_type, requested_by, audit_mode, arguments.\n\n"
            f"Data: {telemetry_json}"
        )
