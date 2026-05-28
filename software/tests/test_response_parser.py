from nexus.ai.response_parser import ResponseParser


def test_response_parser_extracts_hardware_jobs():
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
