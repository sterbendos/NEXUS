from __future__ import annotations

import json
from typing import Any


class PromptFormatter:
    """Create structured prompts from telemetry or raw logs."""

    @staticmethod
    def build_prompt(log_payload: dict[str, Any]) -> str:
        telemetry_json = json.dumps(log_payload, ensure_ascii=True, indent=2)
        return (
            "You are a cybersecurity analysis assistant for authorized defensive analysis. "
            "Classify risk and provide practical mitigation steps based only on provided telemetry.\n\n"
            "Return strict JSON with keys: "
            "threat_classification, severity, suggested_mitigation, rationale. "
            "Severity must be one of: low, medium, high, critical.\n\n"
            f"Telemetry:\n{telemetry_json}"
        )
