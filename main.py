"""
AI Agent System - Main Entry Point
Launches the Orchestrator API Server
"""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    """Start the FastAPI server"""
    port = int(os.getenv("SERVICE_PORT", 8000))
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    print(f"🚀 Starting AI Agent Orchestrator on {host}:{port}")
    
    uvicorn.run(
        "api_v1.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()