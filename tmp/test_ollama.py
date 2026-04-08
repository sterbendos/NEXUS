import requests
import json

def test_local_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma3:4b",
        "prompt": "Say hello world in 3 words.",
        "stream": False,
        "format": "json"
    }
    
    try:
        print(f"Testing local Ollama at {url} with model gemma3:4b...")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Success!")
        print(f"Response: {response.json().get('response')}")
    except Exception as e:
        print(f"Failed to connect to local Ollama: {e}")

if __name__ == "__main__":
    test_local_ollama()
