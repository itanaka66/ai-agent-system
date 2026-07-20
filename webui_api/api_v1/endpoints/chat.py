from fastapi import APIRouter, HTTPException
from typing import Optional

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(
    user_id: str,
    session_id: Optional[str] = None,
    query: str = ...,
    mode: str = "standard"  # standard, debate, simple
):
    """
    メインチャットエンドポイント
    
    Args:
        user_id (str): ユーザー識別子
        session_id (Optional[str]): セッションID（未指定時は新規作成）
        query (str): ユーザーの質問/メッセージ
        mode (str): 処理モード（標準、ディベート、高速）

    Returns:
        dict: 応答データ

    Raises:
        HTTPException: エラー発生時
    """
    
    try:
        from core.orchestrator import Orchestrator
        
        # オーケストレーターから応答を取得
        orchestrator = Orchestrator()
        result = await orchestrator.process_request(
            user_query=query,
            session_id=session_id or "default_session",
            mode=mode
        )
        
        logger.info(f"✅ Response sent - Tokens: {result.get('tokens_used', 0)}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))