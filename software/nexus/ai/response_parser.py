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
            # Find the first '{' and then scan for the matching closing '}'
            # This handles nested dicts and trailing model commentary correctly.
            start = response_text.find("{")
            if start != -1:
                depth = 0
                end = start
                for i, ch in enumerate(response_text[start:], start):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            end = i
                            break
                parsed = json.loads(response_text[start : end + 1])
            else:
                parsed = json.loads(response_text)

            if not isinstance(parsed, dict):
                parsed = {}
        except (json.JSONDecodeError, Exception):
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
