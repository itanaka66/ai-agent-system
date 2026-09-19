import os, requests
from typing import Optional

# Fixed defaults sent with every request. num_ctx is a large, constant
# context-window size independent of any per-agent setting; top_p and
# repeat_penalty aren't (yet) configurable per agent.
DEFAULT_NUM_CTX = 65536
DEFAULT_TOP_P = 0.9
DEFAULT_REPEAT_PENALTY = 1.1
DEFAULT_TEMPERATURE = 0.7

class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    async def generate(self, model: str, prompt: str, max_tokens: int = 4096, temperature: Optional[float] = None) -> str:
        """Generate response from Ollama"""

        options = {
            "num_ctx": DEFAULT_NUM_CTX,
            # max_tokens is per-agent (Agent Console / workflow node settings)
            # and caps generation length - Ollama calls that num_predict.
            "num_predict": max_tokens,
            "temperature": temperature if temperature is not None else DEFAULT_TEMPERATURE,
            "top_p": DEFAULT_TOP_P,
            "repeat_penalty": DEFAULT_REPEAT_PENALTY,
        }

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