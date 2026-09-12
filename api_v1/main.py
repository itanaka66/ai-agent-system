from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import os
from dotenv import load_dotenv 
import logging
from core.orchestrator import Orchestrator
from utils.metrics import MetricsCollector
from services.postgres_logger import PostgresLogger
from api_v1 import agents as agents_router
from api_v1 import workflows as workflows_router
from api_v1 import nodes as nodes_router

# ロギング設定
logger = logging.getLogger(__name__)

# .env の読み込み
load_dotenv()

app = FastAPI(
    title="AI Agent Orchestrator API",
    description="Enterprise Multi-Agent AI System with GPU/CPU Cluster",
    version="1.0.0"
)

# instrumentator = Instrumentator()
instrumentator = Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# CORS 設定
# CORS_ORIGINS: カンマ区切りのオリジンリスト（例: "https://app.example.com,https://admin.example.com"）
# 未設定または "*" の場合は全オリジン許可（開発用デフォルト）。本番では必ず具体的なオリジンを設定してください。
_cors_origins_env = os.getenv("CORS_ORIGINS", "*").strip()
if _cors_origins_env in ("", "*"):
    _cors_origins = ["*"]
else:
    _cors_origins = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# エージェント設定 / ワークフロービルダー用 API（Web UI からのグラフィカルなカスタマイズ用）
app.include_router(agents_router.router, prefix="/api/v1")
app.include_router(workflows_router.router, prefix="/api/v1")
app.include_router(nodes_router.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_db_client():
    """データベース接続初期化"""
    
    logger.info("🚀 AI Agent System starting up...")
    app.state.orchestrator = Orchestrator()
    app.state.db_logger = PostgresLogger()

metrics_collector = MetricsCollector()

# メインチャットエンドポイント
@app.post("/api/v1/chat")
async def chat_endpoint(
    user_id: str = None,
    session_id: str = None,
    query: str = ...,
    mode: str = "standard"  # standard, debate, simple
):
    
    metrics_collector.increment_request_count("POST", "/api/v1/chat")

    try:
        logger.info(f"📨 Request received - User: {user_id}, Mode: {mode}")
        
        # オーケストレーターで処理
        result = await app.state.orchestrator.process_request(
            user_query=query,
            session_id=session_id or "default_session",
            mode=mode
        )
        
        metrics_collector.observe_response_time("POST", "/api/v1/chat", result.get("processing_duration"))
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# メインエントリーポイント
if __name__ == "__main__":
    
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════╗
    ║         AI Agent Orchestrator v1.0          ║
    ╚════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "api_v1.main:app", 
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )