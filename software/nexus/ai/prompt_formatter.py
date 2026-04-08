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
            "Use keys: threat_classification, severity, suggested_mitigation, rationale.\n\n"
            f"Data: {telemetry_json}"
        )
