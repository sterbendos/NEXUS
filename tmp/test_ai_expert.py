import requests
import json
import time
import re

def test_nexus_ai_pipeline_v3():
    telemetry = {
        "device_id": "OTOM-CORE",
        "timestamp": time.time(),
        "source": "WIFI_ATTACK",
        "channel": "11",
        "events": ["Beacon Flood Detected", "SSID: FakeAP_01"],
        "metrics": {"anomaly_score": 0.95}
    }
    
    prompt = (
        "Analyze this cybersecurity telemetry and return valid JSON.\n"
        "Classification: [Name of the attack]\n"
        "Severity: [low, medium, high, or critical]\n"
        "Mitigation: [What to do about it]\n"
        "Rationale: [Brief explanation]\n\n"
        "Use keys: threat_classification, severity, suggested_mitigation, rationale.\n\n"
        f"Data: {json.dumps(telemetry, indent=2)}"
    )

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma3:4b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    print("Testing pipeline V3 (Robust Parsing) on gemma3:4b...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        raw_result = response.json()
        response_text = raw_result.get("response", "")
        
        print("\n--- RAW AI RESPONSE ---")
        print(response_text)
        print("-----------------------\n")
        
        # Simulating ResponseParser.parse robust logic
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group(0))
            print("\n=== EXTRACTED JSON ANALYSIS ===")
            print(json.dumps(analysis, indent=2))
        else:
            print("No JSON block found in response.")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_nexus_ai_pipeline_v3()
