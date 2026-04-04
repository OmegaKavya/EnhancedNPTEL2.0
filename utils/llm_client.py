import requests
import json

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model="llama3.2"):
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{base_url}/api/generate"

    def generate(self, prompt, format_json=True):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if format_json:
            payload["format"] = "json"
        
        try:
            response = requests.post(self.generate_url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '')
            
            if format_json:
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON from Ollama response: {response_text[:200]}")
                    return None
            return response_text
            
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama. Is it running on localhost:11434?")
            return None
        except requests.exceptions.Timeout:
            print("Error: Ollama request timed out")
            return None
        except Exception as e:
            print(f"Ollama client error: {e}")
            return None

    def is_available(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

ollama_client = OllamaClient()
