"""
Main Orchestration Logic
Manages task routing, agent coordination, and request processing
"""

import os
import asyncio
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.ollama_client import OllamaClient
from services.qdrant_client import QdrantHandler
from services.postgres_logger import PostgresLogger
from core.loop_detector import LoopDetector
from utils.logger import setup_logger
from utils.metrics import MetricsCollector
from services import agent_config_store
from services import node_pool

logger = setup_logger(__name__)


class Orchestrator:
    def __init__(self):
        """Initialize orchestrator with all service connections"""
        
        # Ollama Clients
        self.ollama_master = OllamaClient(os.getenv("OLLAMA_MASTER_URL"))
        self.ollama_worker = OllamaClient(os.getenv("OLLAMA_WORKER_URL"))
        
        # Service Handlers
        self.qdrant = QdrantHandler()
        self.db_logger = PostgresLogger()
        self.loop_detector = LoopDetector(self.db_logger)
        
        # Metrics
        self.metrics = MetricsCollector()
        
        # Model Configuration
        self.model_thinker = os.getenv("MODEL_GPT_THINKER")
        self.model_executor = os.getenv("MODEL_FAST_EXECUTOR")
        
    async def process_request(
        self, 
        user_query: str, 
        session_id: str,
        mode: str = "standard",
        user_id: str = None
    ) -> Dict:
        """
        Main request processing pipeline
        
        Args:
            user_query: User's input question
            session_id: Current conversation session ID
            mode: Processing mode (standard, debate, simple)
            user_id: User identifier for logging
            
        Returns:
            Dictionary with answer and metadata
        """
        
        start_time = datetime.now()
        
        try:
            # 1. Generate Session ID if not provided
            if not session_id:
                session_id = await self._create_session(user_id)
                
            # 2. Loop Detection (Security Check)
            is_loop, loop_pattern = await self.loop_detector.check_history(
                session_id, user_query
            )
            
            if is_loop:
                logger.warning(f"Loop detected for session {session_id}: {loop_pattern}")
                return {
                    "answer": self._generate_loop_response(),
                    "error_type": "loop_detected",
                    "status_code": 429,
                    "tokens_used": 0
                }
            
            # 3. Route Task to Appropriate Agent
            routing_decision = await self._route_task(user_query, mode)
            
            # 4. Execute Based on Routing Decision
            if routing_decision["type"] == "flowise":
                from services.flowise_client import FlowiseClient
                result = await self._execute_flowise(
                    user_query, session_id, routing_decision
                )
            else:
                result = await self._execute_internal_mode(user_query, session_id, mode)
            
            # 5. Log to PostgreSQL
            await self.db_logger.save_message(
                session_id=session_id,
                role="assistant",
                content=result.get("answer", ""),
                tokens_used=result.get("tokens_used", 0),
                model_used=self.model_thinker,
                validation_score=result.get("validation_score")
            )
            
            # 6. Save to Qdrant for Memory (if enabled)
            if routing_decision.get("save_to_memory", True):
                await self.qdrant.save_conversation(
                    session_id=session_id, 
                    query=user_query, 
                    answer=result.get("answer", "")
                )
            
            # 7. Record Metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics.record_request(
                mode=mode,
                success=True,
                duration=duration,
                tokens_used=result.get("tokens_used", 0)
            )
            
            return {
                "answer": result.get("answer"),
                "status_code": 200,
                **result
            }
            
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            self.metrics.record_request(mode=mode, success=False)
            
            return {
                "answer": "Internal system error occurred. Please try again.",
                "error_type": "internal_error",
                "status_code": 500,
                "tokens_used": 0
            }
    
    async def _execute_internal_mode(
        self, 
        query: str, 
        session_id: str, 
        mode: str
    ) -> Dict:
        """Execute task based on internal processing modes"""
        
        if mode == "debate":
            return await self._debate_flow(query, session_id)
        elif mode == "simple":
            return await self._simple_query(query, session_id)
        else:  # standard
            return await self._standard_flow(query, session_id)
    
    # Fallback configs used only if configs/agent_configs.json is missing/deleted an entry
    _DEFAULT_AGENT_CONFIGS = {
        "thinker_proposal": {
            "target": "gpu_master", "model": None, "temperature": 0.8, "max_tokens": 4096,
            "system_prompt": "You are a creative problem solver. Provide 3 potential solutions to the user's query. "
                              "For each solution, include pros and cons. Please format your response as JSON with structure: "
                              '{"proposal": "...", "options": [...], "recommended": "option_number"}'
        },
        "thinker_critique": {
            "target": "gpu_master", "model": None, "temperature": 0.6, "max_tokens": 4096,
            "system_prompt": "You are a critical analyst. Review the following proposal and identify weaknesses, risks, "
                              "and potential improvements. Provide your critique in JSON format with structure: "
                              '{"critique": "...", "issues": [...], "improvements": [...]}'
        },
        "judge_decision": {
            "target": "gpu_master", "model": None, "temperature": 0.5, "max_tokens": 4096,
            "system_prompt": "You are the final decision maker. Combine the proposal and critique into a single answer. "
                              "Generate a final comprehensive answer that addresses all concerns."
        },
        "standard_answer": {
            "target": "gpu_master", "model": None, "temperature": 0.7, "max_tokens": 4096,
            "system_prompt": "You are a helpful AI assistant. Answer the following query based on your knowledge and "
                              "the provided context. Please provide a concise, accurate answer."
        },
        "executor_simple": {
            "target": "gpu_worker", "model": None, "temperature": 0.7, "max_tokens": 1024,
            "system_prompt": "Answer concisely."
        },
        "validator": {
            "target": "gpu_worker", "model": None, "temperature": 0.2, "max_tokens": 500,
            "system_prompt": "Check if the following answer makes sense and contains no obvious falsehoods. "
                              'Respond in JSON format: {"score": <0-10>, "reason": "<explanation>", "need_regen": <true/false>}. '
                              "Scoring: 10 = perfect, 5 = acceptable, 1 = problematic"
        },
    }

    def _agent_settings(self, key: str) -> Dict:
        """Resolve the effective (model/prompt/temperature/target) for a pipeline stage,
        preferring the live agent_configs.json store so web-UI edits apply immediately."""

        default = dict(self._DEFAULT_AGENT_CONFIGS[key])
        default["model"] = default["model"] or (
            self.model_executor if default["target"] == "gpu_worker" else self.model_thinker
        )

        stored = agent_config_store.get_agent_or_default(key, default)
        # stored may come straight from JSON (missing internal-only "model" fallback rules)
        stored.setdefault("model", default["model"])
        stored.setdefault("target", default["target"])
        stored.setdefault("temperature", default["temperature"])
        stored.setdefault("max_tokens", default["max_tokens"])
        stored.setdefault("system_prompt", default["system_prompt"])
        return stored

    def _client_for_target(self, target: str) -> OllamaClient:
        if target == "cpu_cluster":
            node_url = node_pool.next_cpu_node()
            if node_url:
                return OllamaClient(node_url)
            logger.warning("target 'cpu_cluster' requested but OLLAMA_CPU_NODES is not configured; falling back to gpu_worker")
            return self.ollama_worker

        return self.ollama_worker if target == "gpu_worker" else self.ollama_master

    async def _run_stage(self, key: str, dynamic_prompt: str) -> str:
        """Run one pipeline stage using its configurable system prompt + model."""

        settings = self._agent_settings(key)
        full_prompt = f"{settings['system_prompt']}\n\n{dynamic_prompt}"

        return await self._call_model(
            client=self._client_for_target(settings["target"]),
            model=settings["model"],
            prompt=full_prompt,
            max_tokens=settings["max_tokens"],
            temperature=settings["temperature"]
        )

    async def _debate_flow(self, query: str, session_id: str) -> Dict:
        """Multi-agent debate workflow for high-quality answers"""

        # Retrieve knowledge base context
        docs = await self.qdrant.search(query, limit=3, score_threshold=0.75)

        context_text = "\n".join([d.get("content", "")[:500] for d in docs]) if docs else "No relevant context found"

        # Debater A: Generate Proposal (RTX 3090 - Thinker)
        proposal = await self._run_stage(
            "thinker_proposal",
            f"Context from knowledge base: {context_text}\n\nUser Query: {query}"
        )

        # Debater B: Critique Proposal (RTX 3090 - Thinker)
        critique = await self._run_stage(
            "thinker_critique",
            f"Original Query: {query}\nProposal: {proposal[:2000]}"
        )

        # Judge: Final Decision (RTX 3090 - Thinker)
        final_answer = await self._run_stage(
            "judge_decision",
            f"Query: {query}\nProposal: {proposal[:2000]}\nCritique: {critique[:2000]}"
        )

        # Validate with lightweight agent (Arc A770)
        validation = await self._validate_response(final_answer, query)

        return {
            "answer": final_answer,
            "validation_score": validation.get("score"),
            "need_regen": validation.get("need_regen", False),
            "tokens_used": 0,
            "mode": "debate"
        }

    async def _standard_flow(self, query: str, session_id: str) -> Dict:
        """Standard single-pass workflow"""

        docs = await self.qdrant.search(query, limit=2, score_threshold=0.70)
        context = "\n".join([d.get("content", "") for d in docs]) if docs else ""

        answer = await self._run_stage(
            "standard_answer",
            f"Context from knowledge base: {context}\n\nUser Query: {query}"
        )

        # Validate with lightweight agent
        validation = await self._validate_response(answer, query)

        return {
            "answer": answer,
            "validation_score": validation.get("score"),
            "tokens_used": 0,
            "mode": "standard"
        }

    async def _simple_query(self, query: str, session_id: str) -> Dict:
        """Simple quick response without RAG"""

        answer = await self._run_stage("executor_simple", f"Query: {query}")

        return {
            "answer": answer,
            "validation_score": None,
            "tokens_used": 0,
            "mode": "simple"
        }

    async def _call_model(
        self,
        client: OllamaClient,
        model: str,
        prompt: str,
        max_tokens: int = 4096,
        temperature: Optional[float] = None
    ) -> str:
        """Unified model calling with error handling"""

        try:
            response = await client.generate(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if isinstance(response, dict):
                return response.get("response", "") or str(response)
            return response

        except Exception as e:
            logger.error(f"Model call failed: {e}")
            raise

    async def _validate_response(self, answer: str, query: str) -> Dict:
        """Validate AI response for hallucination"""

        result = await self._run_stage(
            "validator",
            f"Original Query: {query}\nAI Answer: {answer}"
        )

        # Try to parse JSON response
        try:
            import json
            return json.loads(result)
        except:
            return {"score": 7.0, "reason": "Parse error", "need_regen": False}
    
    async def _execute_flowise(
        self, 
        query: str, 
        session_id: str, 
        routing_decision: Dict
    ) -> Dict:
        """Execute workflow via Flowise"""
        
        from services.flowise_client import FlowiseClient
        
        flowise = FlowiseClient()
        result = await flowise.run_workflow(query, session_id)
        
        return {
            "answer": result.get("answer", ""),
            "source_docs": result.get("source_docs", []),
            "validation_score": None,  # Flowise handles validation internally
            "tokens_used": 0,
            "mode": "flowise"
        }
    
    async def _route_task(self, query: str, mode: str) -> Dict:
        """Determine which workflow to use based on task complexity"""
        
        if mode == "flowise" or (os.getenv("FLOWISE_URL") and mode in ["debate", "standard"]):
            return {
                "type": "flowise",
                "save_to_memory": True,
                "priority": "high" if mode == "debate" else "normal"
            }
        
        elif mode == "debate":
            return {"type": "internal_debate", "save_to_memory": True}
        elif mode == "simple":
            return {"type": "internal_simple", "save_to_memory": False}
        else:  # standard
            return {"type": "internal_standard", "save_to_memory": True}
    
    async def _create_session(self, user_id: str = None) -> str:
        """Create new session in database"""
        
        import uuid
        from datetime import datetime
        
        session_id = str(uuid.uuid4())
        
        await self.db_logger.create_session(
            user_id=user_id or "anonymous",
            session_id=session_id,
            created_at=datetime.now()
        )
        
        return session_id
    
    def _generate_loop_response(self) -> str:
        """Generate response when loop is detected"""
        
        responses = [
            "I notice we're repeating similar topics. Let's explore a different direction.",
            "This seems to be going in circles. Shall I summarize what we've discussed?",
            "We've covered this topic extensively. Would you like suggestions for new areas?"
        ]
        
        import random
        return random.choice(responses)