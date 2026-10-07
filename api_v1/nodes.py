"""
Node Status API
Lets the web UI show whether the cluster's Ollama nodes (RTX 3090 master,
Intel Arc worker, CPU cluster) are actually reachable.
"""

import asyncio
import os
from typing import Optional

import httpx
from fastapi import APIRouter

from services import node_pool

router = APIRouter(prefix="/nodes", tags=["nodes"])


async def _check(url: str, api_key: Optional[str] = None) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{url.rstrip('/')}/api/tags", headers=headers)
        return {
            "url": url,
            "status": "up" if resp.status_code == 200 else "down",
            "models_count": len(resp.json().get("models", [])) if resp.status_code == 200 else 0,
        }
    except Exception as e:
        return {"url": url, "status": "down", "error": str(e)}


@router.get("")
async def list_nodes():
    """Health-check every configured Ollama endpoint, grouped by target."""

    master_key = os.getenv("OLLAMA_MASTER_API_KEY")
    worker_key = os.getenv("OLLAMA_WORKER_API_KEY")
    cpu_key = os.getenv("OLLAMA_CPU_API_KEY")

    targets = {
        "gpu_master": ([u for u in [os.getenv("OLLAMA_MASTER_URL")] if u], master_key),
        "gpu_worker": ([u for u in [os.getenv("OLLAMA_WORKER_URL")] if u], worker_key),
        "cpu_cluster": (node_pool.get_cpu_nodes(), cpu_key),
    }

    results = {}
    for target, (urls, api_key) in targets.items():
        results[target] = await asyncio.gather(*(_check(u, api_key) for u in urls))

    return results
