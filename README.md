# AI Agent System / AI エージェントシステム

<div align="center">

**A Multi-Agent AI System with RTX 3090 + Intel Arc A770 + CPU Cluster**

**RTX 3090 と Intel Arc A770 および CPU クラスターを備えたマルチエージェント AI システム**

[English](#english) | [日本語](#japanese)

</div>

---

## 🌐 English

### Overview
This is an enterprise-grade AI agent system designed to leverage heterogeneous hardware resources:
- **RTX 3090 (24GB VRAM):** Complex reasoning, debate generation, decision making
- **Intel Arc A770 (16GB VRAM):** Fast execution, ComfyUI integration, validation
- **CPU Cluster (10 nodes):** Load distribution, embedding tasks, fallback processing

### Key Features
| Feature | Description |
|---------|-------------|
| 🔄 Multi-Agent Debate | A → Proposal, B → Critique, Judge → Final decision |
| 🔒 Hallucination Prevention | Qdrant RAG + Validator Agent validation |
| ⚠️ Loop Detection | History analysis prevents infinite conversation loops |
| 📊 Monitoring | Prometheus + Grafana for system observability |
| 🎨 Workflow Customization | Flowise integration for visual workflow design |

### Architecture

```bash
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ WebUI       │────▶│ Orchestrator│────▶│ RTX 3090    │
│             │     │ (API Server)│     │ (Thinker)   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                   ▲
                            ▼                   │
                    ┌─────────────┐     ┌─────────────┐
                    │ CPU Cluster │◀───▶│ Intel Arc   │
                    │ (10 nodes)  │     │ A770        │
                    └─────────────┘     └─────────────┘
                            ▲                   │
                            ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ PostgreSQL  │     │ Qdrant      │
                    │ (Logs)      │     │ (Vector DB) │
                    └─────────────┘     └─────────────┘

```

### Installation
```bash
# Clone repository
git clone https://github.com/your-org/ai-agent-system.git
cd ai-agent-system

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual credentials

# Initialize database
psql -h 192.168.0.151 -U agent_user -d ai_agent_db < tools/init_db.sql

# Run Ollama models (on each GPU/CPU node)
ollama pull qwen2.5:32b-q4_K_M
ollama pull llama3:8b
ollama pull phi3:mini

# Start the orchestrator
python main.py --host 0.0.0.0 --port 8000

# Optional: Start Flowise for workflow customization
docker run -p 3001:8080 flowiseai/flowise
```

## Usage

# Basic chat request
``` bash
curl http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "session_id": "", "query": "Hello!", "mode": "standard"}'

# Debate mode (higher accuracy)
curl http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "session_id": "", "query": "Your question here", "mode": "debate"}'
```

## Environment Variables
  | Variable | Description | Required |
|----------|-------------|----------|
| `OLLAMA_MASTER_URL` | RTX 3090 Ollama endpoint | ✅ Yes |
| `OLLAMA_WORKER_URL` | Intel Arc A770 Ollama endpoint | ✅ Yes |
| `OLLAMA_CPU_NODES` | CPU cluster nodes (comma-separated) | ⚠️ Optional |
| `POSTGRES_HOST/PORT/USER/PASSWORD` | PostgreSQL connection | ✅ Yes |
| `QDRANT_HOST` | Vector database URL | ✅ Yes |

## Hardware Requirements
| Component | RTX 3090 | Intel Arc A770 | CPU Node (per) |
|-----------|----------|----------------|----------------|
| vCPU | - | - | 4-8 cores |
| RAM | 24GB GPU | 16GB GPU | 16-32 GB |
| Storage | NVMe SSD | NVMe SSD | NVMe SSD (200+ MB/s read) |

# 🇯🇵 日本語
## 概要
これは、多様なハードウェアリソースを活用するために設計されたエンタープライズグレードの AI エージェントシステムです：

RTX 3090（VRAM 24GB）：複雑な推論、ディベート生成、意思決定
Intel Arc A770（VRAM 16GB）：高速実行、ComfyUI 連携、検証
CPU クラスター（10 ノード）：負荷分散、埋め込みタスク、フォールバック処理

## 主要機能
| 機能 | 説明 |
|---------|-------------|
| 🔄 マルチエージェント ディベート | A→提案、B→批判、JUDGE→最終判断 |
| 🔒 ハルシネーション防止 | Qdrant RAG + Validator Agent で検証 |
| ⚠️ ループ検出 | 履歴分析により無限会話を防ぐ |
| 📊 モニタリング | Prometheus + Grafana で可視化 |
| 🎨 ワークフローカスタマイズ | Flowise 統合で視覚的デザイン可能 |

## アーキテクチャ

```bash
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ WebUI       │────▶│ オーケストレーター │     │ RTX 3090    │
│             │     │ (API サーバー)   │     │ (思考者)    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                   ▲
                            ▼                   │
                    ┌─────────────┐     ┌─────────────┐
                    │ CPU クラスター│◀───▶│ Intel Arc   │
                    │ (10 ノード)    │     │ A770        │
                    └─────────────┘     └─────────────┘
                            ▲                   │
                            ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ PostgreSQL  │     │ Qdrant      │
                    │ (ログ保存)    │     │ (ベクトル DB)│
                    └─────────────┘     └─────────────┘
```

## インストール手順
# リポジトリをクローン
``` bash
git clone https://github.com/your-org/ai-agent-system.git
cd ai-agent-system

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境設定ファイル作成
cp .env.example .env
# .env を実際の認証情報で編集

# データベース初期化
psql -h 192.168.0.151 -U agent_user -d ai_agent_db < tools/init_db.sql

# Ollama モデルのダウンロード (各 GPU/CPU ノードで実行)
ollama pull qwen2.5:32b-q4_K_M
ollama pull llama3:8b
ollama pull phi3:mini

# オーケストレーター起動
python main.py --host 0.0.0.0 --port 8000

# オプション：Flowise を起動してワークフローをカスタマイズ可能に
docker run -p 3001:8080 flowiseai/flowise

## 使用方法
# 基本的なチャットリクエスト
curl http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "session_id": "", "query": "こんにちは！", "mode": "standard"}'

# ディベートモード（高精度）
curl http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "session_id": "", "query": "ここに関心のある質問", "mode": "debate"}'
```

## 環境変数
| 変数名 | 説明 | 必須 |
|----------|-------------|----------|
| `OLLAMA_MASTER_URL` | RTX 3090 の Ollama エンドポイント | ✅ 必要 |
| `OLLAMA_WORKER_URL` | Intel Arc A770 の Ollama エンドポイント | ✅ 必要 |
| `OLLAMA_CPU_NODES` | CPU クラスターノード（カンマ区切り） | ⚠️ 任意 |
| `POSTGRES_HOST/PORT/USER/PASSWORD` | PostgreSQL 接続情報 | ✅ 必要 |
| `QDRANT_HOST` | ベクトルデータベースの URL | ✅ 必要 |

## ハードウェア要件
| コンポーネント | RTX 3090 | Intel Arc A770 | CPU ノード（1 台あたり） |
|-----------|----------|----------------|----------------|
| vCPU | - | - | 4-8 コア |
| RAM | VRAM 24GB | VRAM 16GB | 16-32 GB システムメモリ |
| ストレージ | NVMe SSD | NVMe SSD | NVMe SSD (読み込み 200+ MB/s) |

## 📌 セキュリティの注意点 / Security Notes
⚠️ 重要: .env ファイルは絶対 GitHub にアップロードしないでください！

```bash
Critical: Never upload the .env file to GitHub!

# .gitignore 設定例/.gitignore configuration example
echo ".env" >> .gitignore
```

📞 サポート / Support
問題が発生した場合、以下の情報と共にログを提出してください：
If you encounter issues, please submit logs with the following information:

```bash
logs/errors.log エラーログ/Error log
.env ファイル（機密情報はマスキング）.env file (mask sensitive info)
```
問題が発生したチャット ID Chat session ID where issue occurred
📝 ライセンス / License
MIT License - 自由に利用・改変可能/Free to use and modify under MIT terms.

<div align="center">

Made with ❤️ for Enterprise AI Solutions

</div>