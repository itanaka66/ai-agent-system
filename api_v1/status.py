from fastapi import APIRouter

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_status():
    """
    システムステータス取得
    
    Returns:
        dict: ステータス情報
    """

    try:
        from core.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        return {
            "orchestrator": "running",
            "database": await orchestrator.db_logger.check_connection(),
            "nodes": {
                "gpu_master": os.getenv("OLLAMA_MASTER_URL"),
                "gpu_worker": os.getenv("OLLAMA_WORKER_URL"),
                "cpu_nodes": len(os.getenv("OLLAMA_CPU_NODES", "").split(","))
            }
        }

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {"status": "error", "message": str(e)}