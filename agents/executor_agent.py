    async def generate_response(self, query: str, context: List[Dict] = None) -> str:
        """
        高速応答を生成
        
        Args:
            query (str): ユーザーの質問
            context (List[Dict]): コンテキスト情報（オプション）
        
        Returns:
            str: 生成された回答
        """
        
        from services.ollama_client import OllamaClient
        
        # ノード選択（CPU クラスターがあれば使用する）
        node_url = self._select_optimal_node()
        
        if not node_url:
            raise Exception("No executor nodes available")
        
        client = OllamaClient(node_url)
        
        prompt = self._build_fast_prompt(query, context)
        
        try:
            response = await client.generate(
                model=self.model_name if "gpu" in node_url.lower() else self.model_cpu_lighter,
                prompt=prompt,
                max_tokens=1024  # 高速応答のため短め
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Fast response generation error: {e}")
            raise
    
    def _select_optimal_node(self) -> Optional[str]:
        """最適な実行ノードを選択（CPU クラスター優先）"""
        
        # CPU ノードがあれば使用（負荷分散のためランダム選択）
        if self.cpu_nodes:
            return random.choice(self.cpu_nodes)
        
        # Fallback to GPU worker
        return self.ollama_url
    
    async def execute_code(self, code_snippet: str, language: str = "python") -> Dict:
        """
        コードを実行（サンドボックス内でのみ動作）
        
        Args:
            code_snippet (str): 実行するコード
            language (str): プログラミング言語
        
        Returns:
            Dict: 実行結果
        """
        
        # ⚠️ 本番環境では必ずサンドボックス化してください！
        # ここでは簡易的な実装例のみ示します
        
        try:
            if language == "python":
                # 安全な実行（制限付き）
                local_vars = {}
                
                # 制限：危険な組み込み関数を無効化
                safe_globals = {
                    "__builtins__": {
                        "len": len,
                        "str": str,
                        "int": int,
                        "float": float,
                        "list": list,
                        "dict": dict,
                        "range": range
                    }
                }
                
                # 実行（制限あり）
                exec(code_snippet, safe_globals, local_vars)
                
                return {
                    "success": True,
                    "output": str(local_vars.get("result", "")),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "error": f"Language '{language}' is not supported",
                    "output": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None
            }
    
    async def trigger_image_generation(self, prompt: str, workflow_id: str = None) -> Dict:
        """
        ComfyUI 経由で画像を生成
        
        Args:
            prompt (str): プロンプトテキスト
            workflow_id (str): ワークフロー ID（オプション）
        
        Returns:
            Dict: 生成結果
        """
        
        import requests
        from urllib.parse import urljoin
        
        comfy_url = f"{self.comfyui_host}:{self.comfyui_port}" if ":" not in self.comfyui_host else self.comfyui_host
        
        try:
            # ComfyUI API 呼び出し（簡易版）
            payload = {
                "prompt": prompt,
                "workflow_id": workflow_id or "default"
            }
            
            response = requests.post(
                f"{comfy_url}/api/v1/prompt",
                json=payload,
                timeout=300  # 画像生成は時間がかかる
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "job_id": response.json().get("id"),
                    "status": "queued"
                }
            else:
                return {
                    "success": False,
                    "error": f"ComfyUI API error: {response.status_code}",
                    "image_url": None
                }
                
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_url": None
            }
    
    async def check_node_health(self) -> Dict:
        """ノードのヘルスチェック"""
        
        import requests
        
        try:
            # GPU ノード
            if self.ollama_url:
                health_resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                
                gpu_status = {
                    "available": health_resp.status_code == 200,
                    "models_count": len(health_resp.json().get("models", [])) if health_resp.status_code == 200 else 0
                }
            else:
                gpu_status = {"available": False}
            
            # CPU ノード
            cpu_nodes_health = []
            for node in self.cpu_nodes:
                try:
                    resp = requests.get(f"{node}/api/tags", timeout=3)
                    cpu_nodes_health.append({
                        "url": node,
                        "status": "up" if resp.status_code == 200 else "down"
                    })
                except Exception as e:
                    cpu_nodes_health.append({
                        "url": node,
                        "status": "error",
                        "message": str(e)
                    })
            
            return {
                "gpu_worker": gpu_status,
                "cpu_cluster": cpu_nodes_health,
                "overall_status": self._calculate_overall_health(gpu_status, cpu_nodes_health)
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"error": str(e)}
    
    def _build_fast_prompt(self, query: str, context: List[Dict] = None) -> str:
        """高速応答用プロンプトを構築"""
        
        system_instruction = "あなたは素早く正確な回答をするアシスタントです。"
        
        if context and len(context) > 0:
            context_info = "\n".join([f"- {doc.get('content', '')[:100]}..." for doc in context[:3]])
            
            return f"""{system_instruction}

参考情報：
{context_info}

質問: {query}

回答:"""
        
        else:
            return f"""{system_instruction}

質問: {query}

簡潔に答えてください。

回答:"""
    
    def _calculate_overall_health(self, gpu_status: Dict, cpu_nodes: List[Dict]) -> str:
        """全体の健全性を計算"""
        
        if not gpu_status.get("available"):
            return "degraded"  # GPU がない
        
        up_count = sum(1 for n in cpu_nodes if n.get("status") == "up")
        
        if len(cpu_nodes) > 0 and up_count == len(cpu_nodes):
            return "healthy"
        elif up_count >= len(cpu_nodes) // 2:
            return "partially_degraded"
        else:
            return "critical"


# テスト用
if __name__ == "__main__":
    import asyncio
    
    async def test_executor():
        agent = ExecutorAgent()
        
        # ノードヘルスチェック
        health = await agent.check_node_health()
        print(f"Node Health: {health}")
        
        # 高速応答テスト
        response = await agent.generate_response(
            query="今の時間は何ですか？",
            context=None
        )
        print(f"Response: {response[:100]}")
    
    asyncio.run(test_executor())