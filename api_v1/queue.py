"""
LLM Queue Status API
Lets the web UI show what's currently queued/running against the Ollama
nodes (chat requests and workflow runs), with a progress estimate for each.
"""

from fastapi import APIRouter

from services import llm_queue

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("")
async def list_queue():
    """Current LLM job queue, oldest first."""

    return {"jobs": llm_queue.snapshot()}
