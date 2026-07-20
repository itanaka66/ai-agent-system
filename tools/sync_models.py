import os
from typing import List

class ModelSyncer:
    """モデルの同期用クラス"""
    
    def __init__(self):
        cpu_nodes_str = os.getenv("OLLAMA_CPU_NODES", "")
        self.cpu_nodes = [n.strip() for n in cpu_nodes_str.split(",") if n.strip()]
        
        self.models_to_sync = [
            "llama3:8b",
            "phi3:mini"
        ]
    
    def sync_models(self):
        """モデルを同期する"""
        
        if not self.cpu_nodes:
            raise Exception("No CPU nodes specified for model synchronization")
        
        for node in self.cpu_nodes:
            print(f"Synchronizing models to {node}...")
            
            # モデルのダウンロード
            for model_name in self.models_to_sync:
                sync_command = f"ollama pull {model_name}"
                
                import subprocess
                
                result = subprocess.run(sync_command, shell=True, capture_output=True)
                if result.returncode != 0:
                    print(f"Error syncing {model_name} to {node}: {result.stderr.decode()}")
                else:
                    print(f"{model_name} synchronized successfully!")
    
    def check_model_status(self):
        """モデルの状態をチェックする"""
        
        for node in self.cpu_nodes:
            try:
                import requests
                
                model_list_url = f"http://{node}/api/tags"
                
                response = requests.get(model_list_url)
                
                if response.status_code != 200:
                    print(f"Failed to check models on {node}: {response.text}")
                else:
                    installed_models = [model["tag"] for model in response.json().get("models", [])]
                    
                    missing_models = set(self.models_to_sync) - set(installed_models)
                    
                    if missing_models:
                        print(f"On node {node}, the following models are missing: {missing_models}")
                    else:
                        print(f"All required models installed on {node}.")
            
            except Exception as e:
                print(f"Error checking model status on {node}: {str(e)}")