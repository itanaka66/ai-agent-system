import os
from typing import List, Dict
import asyncio
from services.ollama_client import OllamaClient
from agents.executor_agent import ExecutorAgent

class LoadTest:
    """負荷分散テスト用クラス"""
    
    def __init__(self):
        self.ollama_urls = [os.getenv("OLLAMA_MASTER_URL"), os.getenv("OLLAMA_WORKER_URL")]
        cpu_nodes_str = os.getenv("OLLAMA_CPU_NODES", "")
        self.cpu_nodes = [n.strip() for n in cpu_nodes_str.split(",") if n.strip()]
        
    async def run_load_test(self, query: str, num_requests: int):
        """負荷分散テストを実行
        
        Args:
            query (str): テスト用の質問
            num_requests (int): 実行するリクエスト数
        """
        
        tasks = []
        for i in range(num_requests):
            if i % 10 == 0:  # GPU ノードに振り分ける
                task_url = self.ollama_urls[0] or self.ollama_urls[1]
                model_name = "qwen2.5:32b"
            else:
                task_url = random.choice(self.cpu_nodes) if self.cpu_nodes else None
                model_name = "llama3:8b"  # CPU ノード用モデル
                
            if not task_url:
                raise Exception("No available nodes to distribute the load")
            
            tasks.append(asyncio.create_task(
                self._run_request(query, task_url, model_name)
            ))
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def _run_request(self, query: str, node_url: str, model_name: str):
        """単一のリクエストを実行
        
        Args:
            query (str): リクエスト用の質問
            node_url (str): 対象ノード URL
            model_name (str): 使用するモデル名
            
        Returns:
            dict: API のレスポンス
        """
        
        try:
            client = OllamaClient(node_url)
            
            if "cpu" in node_url.lower():
                agent = ExecutorAgent()
                result = await agent.generate_response(query=query, context=None)
            else:
                result = await client.generate(
                    model=model_name,
                    prompt=query,
                    max_tokens=2048
                )
                
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}