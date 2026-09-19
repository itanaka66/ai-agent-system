import os, requests
from typing import Optional

# Fixed defaults sent only to the RTX 3090 (OLLAMA_MASTER_URL). Every other
# node (Intel Arc A770 / CPU cluster) gets no "options" override at all -
# Ollama's own built-in defaults apply, since they don't have the VRAM/RAM
# for a 65536-token context window the way the RTX 3090 does.
DEFAULT_NUM_CTX = 65536
DEFAULT_TOP_P = 0.9
DEFAULT_REPEAT_PENALTY = 1.1
DEFAULT_TEMPERATURE = 0.7

class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def _is_rtx3090(self) -> bool:
        """True when this client targets OLLAMA_MASTER_URL (the RTX 3090)."""

        master_url = os.getenv("OLLAMA_MASTER_URL", "").rstrip('/')
        return bool(master_url) and self.base_url == master_url

    async def generate(self, model: str, prompt: str, max_tokens: int = 4096, temperature: Optional[float] = None) -> str:
        """Generate response from Ollama"""

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        if self._is_rtx3090():
            payload["options"] = {
                "num_ctx": DEFAULT_NUM_CTX,
                # max_tokens is per-agent (Agent Console / workflow node settings)
                # and caps generation length - Ollama calls that num_predict.
                "num_predict": max_tokens,
                "temperature": temperature if temperature is not None else DEFAULT_TEMPERATURE,
                "top_p": DEFAULT_TOP_P,
                "repeat_penalty": DEFAULT_REPEAT_PENALTY,
            }
        # else: no "options" key - Ollama's own defaults apply on this node
        
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