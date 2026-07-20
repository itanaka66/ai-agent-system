"""
Base Agent Class
Common functionality for all agent types
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseAgent(ABC):
    def __init__(self, name: str, model: str, api_url: str):
        self.name = name
        self.model = model
        self.api_url = api_url
        self.memory_limit = 4096
    
    @abstractmethod
    async def execute(self, task: Dict) -> Dict:
        """Execute agent's primary function"""
        pass
    
    async def generate(
        self, 
        prompt: str, 
        system_message: str = None,
        max_tokens: int = 4096
    ) -> str:
        """Generate response using Ollama API"""
        
        from services.ollama_client import OllamaClient
        
        client = OllamaClient(self.api_url)
        
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        
        try:
            response = await client.generate(
                model=self.model,
                prompt=full_prompt,
                max_tokens=max_tokens
            )
            
            if isinstance(response, dict):
                return response.get("response", "") or str(response)
            return response
            
        except Exception as e:
            logger.error(f"{self.name} generation failed: {e}")
            raise
    
    def validate_response(self, response: str) -> bool:
        """Basic validation of agent's response"""
        
        if not response or len(response.strip()) == 0:
            return False
        
        if len(response) < 10:
            return False
            
        # Check for common error patterns
        error_indicators = [
            "sorry", "cannot", "unable to", "error", 
            "fail", "don't know"
        ]
        
        response_lower = response.lower()
        
        if any(indicator in response_lower for indicator in error_indicators):
            logger.warning(f"{self.name} returned error-indicating response")
            
        return True