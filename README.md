# AI Agent System / AI エージェントシステム

<div align="center">

[![CI](https://github.com/itanaka66/ai-agent-system/actions/workflows/ci.yml/badge.svg)](https://github.com/itanaka66/ai-agent-system/actions/workflows/ci.yml)

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
- **CPU Cluster (3 nodes):** Load distribution, embedding tasks, fallback processing

### Key Features
| Feature | Description |
|---------|-------------|
| 🔄 Multi-Agent Debate | A → Proposal, B → Critique, Judge → Final decision |
| 🔒 Hallucination Prevention | Qdrant RAG + Validator Agent validation |
| ⚠️ Loop Detection | History analysis prevents infinite conversation loops |
| 📊 Monitoring | Prometheus + Grafana for system observability |
| 🎨 Workflow Customization | Flowise integration for visual workflow design |
| 🖥️ Agent Console | Built-in web UI (`frontend/`) to graphically edit agent prompts/models and build agent workflows, no file editing required |

### Architecture

```bash
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   WebUI /   │────▶│ Orchestrator│────▶│ RTX 3090    │
│   Console   │     │ (API Server)│     │ (Thinker)   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                   ▲
                            ▼                   │
                    ┌─────────────┐     ┌─────────────┐
                    │ CPU Cluster │◀───▶│ Intel Arc   │
                    │ (3 nodes)   │     │ A770        │
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

# Start the orchestrator (host/port come from SERVICE_HOST / SERVICE_PORT in .env, default 0.0.0.0:8000)
python main.py

# Optional: Start Flowise for workflow customization
docker run -p 3001:8080 flowiseai/flowise
```

## Usage

`POST /api/v1/chat` takes its arguments as query parameters (not a JSON body).

```bash
# Basic chat request
curl -X POST "http://localhost:8000/api/v1/chat?user_id=user123&session_id=&query=Hello!&mode=standard"

# Debate mode (higher accuracy)
curl -X POST "http://localhost:8000/api/v1/chat?user_id=user123&session_id=&query=Your%20question%20here&mode=debate"
```

## Web UI: Graphical Agent Customization
A React SPA under `frontend/` lets you customize agents from the browser instead of editing files by hand.

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 (proxies /api to the backend on :8000)
```

- **エージェント設定 (Agent Settings)** — edit each pipeline stage's model, system prompt, temperature and max tokens. Changes apply to the next `/api/v1/chat` request immediately (no restart).
- **ワークフロービルダー (Workflow Builder)** — drag agent nodes onto a canvas, wire them together via named input/output variables, and test-run the graph. Workflows are stored as `configs/workflow_configs/*.json`.

Backed by new REST endpoints: `GET/POST/PUT/DELETE /api/v1/agents`, `GET /api/v1/agents/models`, and `GET/PUT/DELETE /api/v1/workflows`, `POST /api/v1/workflows/{name}/run`.

The existing Flowise integration (`FLOWISE_URL`) is unaffected and can still be used side-by-side.

## Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `OLLAMA_MASTER_URL` | RTX 3090 Ollama endpoint | ✅ Yes |
| `OLLAMA_WORKER_URL` | Intel Arc A770 Ollama endpoint | ✅ Yes |
| `MODEL_GPT_THINKER` | Default model for thinker/debate stages (RTX 3090) | ✅ Yes |
| `MODEL_FAST_EXECUTOR` | Default model for validator/executor stages (Arc A770) | ✅ Yes |
| `OLLAMA_CPU_NODES` | CPU cluster nodes (comma-separated). Selectable as target `cpu_cluster` (round-robin) in Agent Console / Workflow Builder | ⚠️ Optional |
| `POSTGRES_HOST/PORT/USER/PASSWORD/DB` | PostgreSQL connection | ✅ Yes |
| `QDRANT_HOST` / `QDRANT_API_KEY` | Vector database URL / API key | ✅ Yes |
| `CORS_ORIGINS` | Comma-separated allowed origins for the web UI. `*`/unset allows all (dev default) | ⚠️ Optional |
| `QDRANT_COLLECTION_CORPUS/HISTORY` | Qdrant collection names | ⚠️ Optional |
| `PROMETHEUS_URL` / `GRAFANA_URL` | Monitoring dashboards | ⚠️ Optional |
| `FLOWISE_URL/FLOWISE_FLOW_ID/FLOWISE_API_KEY` | Flowise workflow integration | ⚠️ Optional |
| `SERVICE_HOST` / `SERVICE_PORT` | Orchestrator bind address/port (default `0.0.0.0:8000`) | ⚠️ Optional |
| `SECRET_KEY` / `API_TOKEN` | App secret / API auth token | ✅ Yes |
| `LOG_LEVEL` | Logging verbosity | ⚠️ Optional |

## Hardware Requirements
| Component | RTX 3090 | Intel Arc A770 | CPU Node (per) |
|-----------|----------|----------------|----------------|
| vCPU | - | - | 4-8 cores |
| RAM | 24GB GPU | 16GB GPU | 16-32 GB |
| Storage | NVMe SSD | NVMe SSD | NVMe SSD (200+ MB/s read) |

# 🇯🇵 日本語
## 概要
これは、多様なハードウェアリソースを活用するために設計されたエンタープライズグレードの AI エージェントシステムです：

* RTX 3090（VRAM 24GB）：複雑な推論、ディベート生成、意思決定
* Intel Arc A770（VRAM 16GB）：高速実行、ComfyUI 連携、検証
* CPU クラスター（3 ノード）：負荷分散、埋め込みタスク、フォールバック処理

## 主要機能
| 機能 | 説明 |
|---------|-------------|
| 🔄 マルチエージェント ディベート | A→提案、B→批判、JUDGE→最終判断 |
| 🔒 ハルシネーション防止 | Qdrant RAG + Validator Agent で検証 |
| ⚠️ ループ検出 | 履歴分析により無限会話を防ぐ |
| 📊 モニタリング | Prometheus + Grafana で可視化 |
| 🎨 ワークフローカスタマイズ | Flowise 統合で視覚的デザイン可能 |
| 🖥️ エージェントコンソール | 標準搭載の Web UI（`frontend/`）でエージェントのプロンプト・モデルやワークフローをファイル編集なしにグラフィカルに設定可能 |

## アーキテクチャ

```bash
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  WebUI /    │────▶│ オーケストレーター │     │ RTX 3090    │
│  コンソール   │     │ (API サーバー)   │     │ (思考者)    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                   ▲
                            ▼                   │
                    ┌─────────────┐     ┌─────────────┐
                    │ CPU クラスター│◀───▶│ Intel Arc   │
                    │ (3 ノード)     │     │ A770        │
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

# オーケストレーター起動（ホスト/ポートは .env の SERVICE_HOST / SERVICE_PORT で指定、既定値 0.0.0.0:8000）
python main.py

# オプション：Flowise を起動してワークフローをカスタマイズ可能に
docker run -p 3001:8080 flowiseai/flowise
```

## 使用方法
`POST /api/v1/chat` はクエリパラメータで引数を受け取ります（JSON ボディではありません）。

```bash
# 基本的なチャットリクエスト
curl -X POST "http://localhost:8000/api/v1/chat?user_id=user123&session_id=&query=こんにちは！&mode=standard"

# ディベートモード（高精度）
curl -X POST "http://localhost:8000/api/v1/chat?user_id=user123&session_id=&query=ここに関心のある質問&mode=debate"
```

## Web UI：エージェントのグラフィカルなカスタマイズ
`frontend/` 以下に React 製の SPA があり、ブラウザからエージェントを設定できます。

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 （/api を :8000 のバックエンドへプロキシ）
```

- **エージェント設定** — 各パイプライン段階（提案／批評／判定／検証／標準応答／高速実行）のモデル・システムプロンプト・temperature・max_tokens を編集できます。保存すると再起動なしで次回のチャットリクエストから反映されます。
- **ワークフロービルダー** — キャンバス上にエージェントノードをドラッグ配置し、入出力変数名でデータフローを設計、テスト実行できます。ワークフローは `configs/workflow_configs/*.json` に保存されます。

これらは新規追加した REST API（`/api/v1/agents`、`/api/v1/agents/models`、`/api/v1/workflows`、`/api/v1/workflows/{name}/run`）に対応しています。既存の Flowise 連携（`FLOWISE_URL`）はそのまま併用可能です。

## 環境変数
| 変数名 | 説明 | 必須 |
|----------|-------------|----------|
| `OLLAMA_MASTER_URL` | RTX 3090 の Ollama エンドポイント | ✅ 必要 |
| `OLLAMA_WORKER_URL` | Intel Arc A770 の Ollama エンドポイント | ✅ 必要 |
| `MODEL_GPT_THINKER` | Thinker/ディベート段階の既定モデル（RTX 3090） | ✅ 必要 |
| `MODEL_FAST_EXECUTOR` | Validator/Executor 段階の既定モデル（Arc A770） | ✅ 必要 |
| `OLLAMA_CPU_NODES` | CPU クラスターノード（カンマ区切り）。Agent Console / ワークフロービルダーで実行先「cpu_cluster」としてラウンドロビン選択可能 | ⚠️ 任意 |
| `POSTGRES_HOST/PORT/USER/PASSWORD/DB` | PostgreSQL 接続情報 | ✅ 必要 |
| `QDRANT_HOST` / `QDRANT_API_KEY` | ベクトルデータベースの URL / API キー | ✅ 必要 |
| `CORS_ORIGINS` | Web UI からのアクセスを許可するオリジン（カンマ区切り）。`*` または未設定で全許可（開発用デフォルト） | ⚠️ 任意 |
| `QDRANT_COLLECTION_CORPUS/HISTORY` | Qdrant コレクション名 | ⚠️ 任意 |
| `PROMETHEUS_URL` / `GRAFANA_URL` | モニタリングダッシュボード | ⚠️ 任意 |
| `FLOWISE_URL/FLOWISE_FLOW_ID/FLOWISE_API_KEY` | Flowise ワークフロー連携 | ⚠️ 任意 |
| `SERVICE_HOST` / `SERVICE_PORT` | オーケストレーターの待受アドレス/ポート（既定 `0.0.0.0:8000`） | ⚠️ 任意 |
| `SECRET_KEY` / `API_TOKEN` | アプリシークレット / API 認証トークン | ✅ 必要 |
| `LOG_LEVEL` | ログ出力レベル | ⚠️ 任意 |

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