import os
from typing import Dict, Any
import requests

class ComfyUIWrapper:
    """ComfyUI API のラッパークラス"""
    
    def __init__(self):
        self.comfyui_host = os.getenv("COMFYUI_HOST")
        self.comfyui_port = int(os.getenv("COMFYUI_PORT", "8188"))
        
        if not self.comfyui_host:
            raise ValueError("Environment variable COMFYUI_HOST is missing.")
    
    def generate_image(self, prompt: str) -> Dict[str, Any]:
        """プロンプトから画像を生成
        
        Args:
            prompt (str): 画像生成のためのプロンプトテキスト
            
        Returns:
            dict: API のレスポンス
        """
        
        url = f"http://{self.comfyui_host}:{self.comfyui_port}/api/v1/prompt"
        
        response = requests.post(
            url,
            json={"prompt": prompt},
            timeout=300  # 画像生成は時間がかかるため、タイムアウトを長めに設定
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to generate image: {response.text}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """ワークフローのステータスを取得
        
        Args:
            workflow_id (str): 生成されたワークフロー ID
            
        Returns:
            dict: API のレスポンス
        """
        
        url = f"http://{self.comfyui_host}:{self.comfyui_port}/api/v1/workflows/{workflow_id}"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get workflow status: {response.text}")