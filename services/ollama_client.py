import os, requests
from typing import Optional

class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    async def generate(self, model: str, prompt: str, max_tokens: int = 4096, temperature: Optional[float] = None) -> str:
        """Generate response from Ollama"""

        options = {"num_ctx": max_tokens}
        if temperature is not None:
            options["temperature"] = temperature

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # CPU nodes may be slower
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                raise Exception(f"Ollama error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama timeout at {self.base_url}")