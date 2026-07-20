"""
Task Router Agent
Routes incoming queries to appropriate processing pipelines based on complexity
"""

import os
from typing import Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RouterAgent:
    def __init__(self):
        self.ollama_master_url = os.getenv("OLLAMA_MASTER_URL")
        self.model_router = os.getenv("MODEL_GPT_THINKER", "llama3:8b")  # Fallback
        
        # Complexity thresholds
        self.complexity_thresholds = {
            "simple": 0,
            "standard": 0.4,
            "complex": 0.7,
            "debate": 0.9
        }
    
    async def route_query(self, query: str) -> Dict:
        """
        Determine processing path based on query complexity
        
        Returns:
            Dictionary with routing decision and metadata
        """
        
        # Quick heuristic analysis first
        heuristics = self._analyze_heuristics(query)
        
        # Use LLM for final classification if needed
        if heuristics["confidence"] < 0.8:
            classification = await self._llm_classify(query)
        else:
            classification = heuristics
        
        routing_decision = {
            "mode": classification["mode"],
            "complexity_score": classification["score"],
            "use_gpu_master": classification["need_high_quality"],
            "should_use_rag": classification.get("use_rag", True),
            "estimated_tokens": self._estimate_token_count(query)
        }
        
        return routing_decision
    
    def _analyze_heuristics(self, query: str) -> Dict:
        """Fast heuristic-based complexity analysis"""
        
        import re
        
        # Query length
        word_count = len(query.split())
        char_count = len(query)
        
        # Check for complex indicators
        has_complex_words = bool(re.search(r'\b(analyze|evaluate|compare|critique|optimize|architecture)\b', query.lower()))
        has_multiple_questions = query.count('?') > 1
        has_code_syntax = bool(re.search(r'[\{\}\(\)\[\]]', query)) or ('function' in query.lower() and 'code' in query.lower())
        
        # Calculate base complexity score
        length_score = min(word_count / 30, 1.0) * 0.3  # Max 30% from length
        indicator_score = (has_complex_words + has_multiple_questions + has_code_syntax) * 0.25
        
        base_score = length_score + indicator_score
        
        # Assign mode based on score
        if base_score < 0.4:
            mode = "simple"
        elif base_score < 0.7:
            mode = "standard"
        else:
            mode = "debate"
        
        return {
            "mode": mode,
            "score": round(base_score, 2),
            "confidence": min(0.8 + (base_score * 0.1), 0.95),
            "need_high_quality": base_score >= 0.4,
            "use_rag": has_complex_words or word_count > 10
        }
    
    async def _llm_classify(self, query: str) -> Dict:
        """Use LLM for more accurate classification"""
        
        from services.ollama_client import OllamaClient
        
        prompt = f"""Classify this user query into one of three modes: simple, standard, or debate.

User Query: {query}

Output only the mode name and a 0-1 confidence score in JSON format:
{{"mode": "<simple|standard|debate>", "score": <0-1>, "use_rag": true/false}}"""
        
        client = OllamaClient(self.ollama_master_url)
        
        try:
            response = await client.generate(
                model=self.model_router,
                prompt=prompt,
                max_tokens=50
            )
            
            import json
            
            # Extract JSON from response
            if isinstance(response, dict):
                return response
                
            # Try to parse text response as JSON
            try:
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            except:
                pass
                
        except Exception as e:
            logger.error(f"LLM classification failed, using heuristics: {e}")
        
        # Fallback to heuristics
        return self._analyze_heuristics(query)
    
    def _estimate_token_count(self, text: str) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)"""
        
        import re
        
        # Remove special formatting
        clean_text = re.sub(r'[^\w\s]', '', text)
        
        word_count = len(clean_text.split())
        
        return word_count * 1.3  # Average tokens per word for English