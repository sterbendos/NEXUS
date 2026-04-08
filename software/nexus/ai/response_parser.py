from __future__ import annotations

import json
from typing import Any


class ResponseParser:
    """Parse Ollama responses into a stable analysis schema."""

    @staticmethod
    def _coerce_severity(value: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        normalized = value.strip().lower()
        return normalized if normalized in allowed else "medium"

    @classmethod
    def parse(cls, response_body: dict[str, Any]) -> dict[str, Any]:
        model = str(response_body.get("model") or "")
        response_text = str(response_body.get("response") or "").strip()

        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                parsed = json.loads(response_text)
            
            if not isinstance(parsed, dict):
                parsed = {}
        except (json.JSONDecodeError, ImportError):
            parsed = {}

        threat = str(parsed.get("threat_classification") or "Unknown")
        severity = cls._coerce_severity(str(parsed.get("severity") or "medium"))
        mitigation = str(parsed.get("suggested_mitigation") or "No mitigation provided.")
        rationale = str(parsed.get("rationale") or "")

        return {
            "model": model,
            "threat_classification": threat,
            "severity": severity,
            "suggested_mitigation": mitigation,
            "rationale": rationale,
            "raw_response": response_body,
        }
