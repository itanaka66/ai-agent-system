import os, requests
from utils.logger import setup_logger

logger = setup_logger(__name__)

class FlowiseClient:
    def __init__(self):
        self.base_url = os.getenv("FLOWISE_URL")
        self.flow_id = os.getenv("FLOWISE_FLOW_ID")
        self.api_key = os.getenv("FLOWISE_API_KEY")
        
    async def run_workflow(self, user_query: str, session_id: str = "") -> dict:
        """Flowise に質問を送り、回答を受け取る"""
        
        url = f"{self.base_url}/api/v1/prediction/{self.flow_id}"
        
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        # Flowise への入力データ (質問テキスト)
        payload = {
            "question": user_query,
            "overrideConfig": {
                "sessionId": session_id, # セッション ID を渡す（必要に応じて）
                "memory": True 
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                # Flowise の出力形式は通常 {"text": "..."} または {"output": "..."}
                answer = data.get("text", "") or data.get("output", str(data))
                
                return {
                    "success": True,
                    "answer": answer,
                    "source_docs": data.get("sources", []) # 参考資料があれば取得
                }
            else:
                logger.error(f"Flowise API Error: {response.status_code} - {response.text}")
                raise Exception(f"Flowise API failed: {response.text}")
                
        except Exception as e:
            return {"success": False, "error": str(e)}