"""
Node Status API
Lets the web UI show whether the cluster's Ollama nodes (RTX 3090 master,
Intel Arc worker, CPU cluster) are actually reachable.
"""

import asyncio
import os

import httpx
from fastapi import APIRouter

from services import node_pool

router = APIRouter(prefix="/nodes", tags=["nodes"])


async def _check(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{url.rstrip('/')}/api/tags")
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

    targets = {
        "gpu_master": [u for u in [os.getenv("OLLAMA_MASTER_URL")] if u],
        "gpu_worker": [u for u in [os.getenv("OLLAMA_WORKER_URL")] if u],
        "cpu_cluster": node_pool.get_cpu_nodes(),
    }

    results = {}
    for target, urls in targets.items():
        results[target] = await asyncio.gather(*(_check(u) for u in urls))

    return results
