"""
Thinker Agent (RTX 3090)
Handles complex reasoning, debate generation, and decision making
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

from .base_agent import BaseAgent


class ThinkerAgent(BaseAgent):
    def __init__(self):
        api_url = os.getenv("OLLAMA_MASTER_URL")
        model = os.getenv("MODEL_GPT_THINKER", "qwen2.5:32b")
        
        super().__init__(name="Thinker Agent", model=model, api_url=api_url)
    
    async def execute(self, task: Dict) -> Dict:
        """Execute reasoning task"""
        
        query = task.get("query", "")
        context = task.get("context", [])
        mode = task.get("mode", "standard")
        
        if mode == "proposal":
            return await self._generate_proposal(query, context)
        elif mode == "critique":
            return await self._generate_critique(query, context)
        elif mode == "judge":
            return await self._make_judgment(task.get("proposal", ""), task.get("critique", ""))
        else:  # standard reasoning
            return await self._standard_reasoning(query, context)
    
    async def _generate_proposal(self, query: str, context: List[str]) -> Dict:
        """Generate solution proposal"""
        
        prompt = f"""You are an expert problem solver. Generate a detailed proposal to address the following user request.

Context Information: {chr(10).join(context[:3]) if context else "No external context available"}

User Query: {query}

Please structure your response as JSON with this format:
{{
    "title": "<Proposal Title>",
    "main_solution": "<Detailed solution>",
    "alternatives": ["<Alternative 1>", "<Alternative 2>"],
    "recommendation": <0-3 index of best option>,
    "reasoning": "<Explanation>"
}}"""
        
        response = await self.generate(
            prompt=prompt,
            max_tokens=4096
        )
        
        return {
            "type": "proposal",
            "content": response,
            "agent": self.name
        }
    
    async def _generate_critique(self, query: str, context: List[str]) -> Dict:
        """Critique an existing proposal"""
        
        # This will be called after getting a proposal
        prompt = f"""You are a critical analyst. Review the following proposal and identify weaknesses, risks, and improvements.

Original Query: {query}

Please respond as JSON with this format:
{{
    "strengths": ["<Strength 1>", "<Strength 2>"],
    "weaknesses": ["<Weakness 1>", "<Weakness 2>"],
    "risks": ["<Risk 1>", "<Risk 2>"],
    "improvements": ["<Improvement suggestion>"]
}}"""
        
        response = await self.generate(
            prompt=prompt,
            max_tokens=4096
        )
        
        return {
            "type": "critique",
            "content": response,
            "agent": self.name
        }
    
    async def _make_judgment(self, proposal: str, critique: str) -> Dict:
        """Make final decision from proposal and critique"""
        
        prompt = f"""You are the final decision maker. Combine the proposal and its critique into a single comprehensive answer.

Proposal:\n{proposal}

Critique:\n{critique}

Generate a final polished answer that addresses all concerns."""
        
        response = await self.generate(
            prompt=prompt,
            max_tokens=4096
        )
        
        return {
            "type": "final_answer",
            "content": response,
            "agent": self.name
        }
    
    async def _standard_reasoning(self, query: str, context: List[str]) -> Dict:
        """Standard reasoning without debate"""
        
        prompt = f"""You are a helpful AI assistant. Answer the following query based on your knowledge and any provided context.

Context: {chr(10).join(context[:5]) if context else "No additional context"}

User Query: {query}

Please provide a clear, accurate answer."""
        
        response = await self.generate(prompt=prompt)
        
        return {
            "type": "answer",
            "content": response,
            "agent": self.name
        }