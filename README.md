# AI Agent System / AI エージェントシステム

<div align="center">

[![CI](https://github.com/itanaka66/ai-agent-system/actions/workflows/ci.yml/badge.svg)](https://github.com/itanaka66/ai-agent-system/actions/workflows/ci.yml)

**A Multi-Agent AI System with RTX 3090 + Intel Arc A770 + CPU Cluster**

**RTX 3090 と Intel Arc A770 および CPU クラスターを備えたマルチエージェント AI システム**

[English](#english) | [日本語](#japanese)

</div>

---

## 🌐 English

### 🚀 Quick Start (Windows / macOS / Linux / Cloud)
New here, or don't have the dedicated GPU hardware below? Try the whole system - backend, web UI, database, vector store, and a local LLM - with only Docker installed. No Python, Node.js, or GPU required.

**⚠️ The Web UI isn't just a nice-to-have here - step 4 below is required.** The agents ship pre-configured for a 32B production model that this Quick Start never downloads (it's ~20GB and needs a GPU to run well), so `standard`/`debate` chat modes **will fail until you open the Web UI and repoint them** at the small models you actually pulled. The flow below shows where that step sits:

```mermaid
flowchart TD
    A["1: Install Docker\n(Desktop on Win/Mac, Engine on Linux/Cloud)"] --> B["2: Clone repo &amp; run\n./install.sh --all  or  .\install.ps1 -All"]
    B --> C["3: Pull small models\nllama3:8b, phi3:mini"]
    C --> D{{"4: Open the Web UI\nhttp://localhost:3000"}}
    D --> E["REQUIRED: Agent Console -&gt;\nrepoint each agent's model\nto llama3:8b / phi3:mini"]
    E --> F(["System operational"])
    F --> G["Chat via curl / REST API"]
    F --> H["Optional: Workflow Builder -\ndesign custom agent pipelines"]

    class D,E required
    classDef required fill:#ffe4b3,stroke:#d97706,stroke-width:2px,color:#000
```

**1. Install Docker**
| Platform | What to install |
|----------|------------------|
| Windows | [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/) (includes WSL2 + Compose) |
| macOS | [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/) |
| Linux | [Docker Engine + Compose plugin](https://docs.docker.com/engine/install/) |
| Cloud (AWS/GCP/Azure/...) | Any Linux VM - follow the Linux instructions above |

**2. Clone and run**
```bash
# macOS / Linux / Windows (via WSL or Git Bash)
git clone https://github.com/itanaka66/ai-agent-system.git
cd ai-agent-system
./install.sh --all
```
```powershell
# Windows (PowerShell)
git clone https://github.com/itanaka66/ai-agent-system.git
cd ai-agent-system
.\install.ps1 -All
```

**3. Pull a couple of small models** (one-time, ~5-8GB total, runs on CPU - no GPU needed)
```bash
docker compose exec ollama ollama pull llama3:8b
docker compose exec ollama ollama pull phi3:mini
```

**4. Open the Web UI and point agents at your models (required)**
1. Open http://localhost:3000 - this is the **Agent Console**, the app's own web UI (`frontend/`), already running as part of `--all`.
2. Go to **エージェント設定 (Agent Settings)**.
3. For every agent still showing `qwen2.5:32b` (the production default), change **モデル (Model)** to `llama3:8b` (or `phi3:mini` for lighter/faster ones) and save. Changes apply immediately - no restart needed.

Skip this and only `mode=simple` chat requests will work; `standard`/`debate` will error with "model not found" until the agents point at models you've actually pulled.

**5. Use it**
- Chat via the API: see [Usage](#usage) below
- Or keep using the Web UI to tweak prompts/temperature or build custom agent pipelines: see [Web UI](#web-ui-graphical-agent-customization) below

Everything - agents, RAG memory, and logging - now runs in containers. Stop it all with `docker compose down`.

For the full RTX 3090 + Intel Arc A770 + CPU cluster production setup described below (which already ships model assignments that match its own defaults), see "Installation" instead.

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
| 🖥️ Agent Console | Built-in web UI (`frontend/`) to graphically edit agent prompts/models and build agent workflows - **required after Quick Start** to match agents to the models you actually pulled, not just an optional extra |

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

### Installation (Dedicated Hardware / Production)
For the RTX 3090 + Intel Arc A770 + CPU cluster setup this project targets in production. New here? Use Quick Start above instead.

```bash
# Clone repository
git clone https://github.com/itanaka66/ai-agent-system.git
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

### Optional: Run the app and/or Qdrant / PostgreSQL / Ollama / Flowise via Docker
If you don't already have these running on dedicated hardware, `docker-compose.yml` can start any combination of them locally - including this app's own backend/web UI (see Quick Start above). Each service is behind a Compose [profile](https://docs.docker.com/compose/how-tos/profiles/) of the same name, selectable from the CLI:

```bash
# Interactive picker (prompts y/N for each service) - Linux/macOS/WSL/Git Bash
./install.sh
# Windows PowerShell
.\install.ps1

# Or select explicitly via flags
./install.sh --qdrant --postgres --ollama --flowise
./install.sh --all

# Equivalent raw docker compose invocation
docker compose --profile qdrant --profile postgres up -d
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
A React SPA under `frontend/` lets you customize agents from the browser instead of editing files by hand. **If you followed Quick Start, this isn't optional** - see step 4 there: the shipped agents default to a 32B model, so you need this UI (or the underlying `/api/v1/agents` REST API) to point them at whatever models you actually pulled.

Already running via `--all`/Docker at http://localhost:3000. To run it separately for frontend development instead:
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
Two templates are provided: `.env.example` for the dedicated-hardware/production setup (defaults above), and `.env.docker.example` for the all-Docker Quick Start (points at container hostnames like `ollama`/`postgres`/`qdrant` and uses small CPU-friendly models). `install.sh`/`install.ps1` pick the right one automatically.

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

## 🚀 クイックスタート（Windows / macOS / Linux / クラウド）
初めての方、または下記の専用GPUハードウェアをお持ちでない方は、Dockerだけでシステム全体（バックエンド・Web UI・データベース・ベクトルストア・ローカルLLM）を試せます。Python・Node.js・GPUは不要です。

**⚠️ Web UI はおまけではなく、下記の手順4は必須です。** エージェントは初期状態で32B（qwen2.5:32b）の本番用モデルを使うよう設定されていますが、このクイックスタートではそのモデルを取得しません（約20GBかつGPU推奨のため）。そのため **Web UI を開いて実際に取得したモデルに設定し直さない限り、`standard`/`debate` モードのチャットは失敗します**。全体の流れは以下の通りです：

```mermaid
flowchart TD
    A["1: Docker をインストール\n（Windows/MacはDesktop、Linux/クラウドはEngine）"] --> B["2: クローンして起動\n./install.sh --all  または  .\install.ps1 -All"]
    B --> C["3: 軽量モデルを取得\nllama3:8b, phi3:mini"]
    C --> D{{"4: Web UI を開く\nhttp://localhost:3000"}}
    D --> E["必須: エージェント設定画面で\n各エージェントのモデルを\nllama3:8b / phi3:mini に変更"]
    E --> F(["運用開始"])
    F --> G["curl / REST API でチャット"]
    F --> H["任意: ワークフロービルダーで\nカスタムパイプラインを設計"]

    class D,E required
    classDef required fill:#ffe4b3,stroke:#d97706,stroke-width:2px,color:#000
```

**1. Docker をインストール**
| プラットフォーム | インストールするもの |
|----------|------------------|
| Windows | [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/)（WSL2・Compose 込み） |
| macOS | [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/) |
| Linux | [Docker Engine + Compose プラグイン](https://docs.docker.com/engine/install/) |
| クラウド（AWS/GCP/Azure等） | 任意の Linux VM（上記 Linux の手順と同じ） |

**2. クローンして起動**
```bash
# macOS / Linux / Windows（WSL または Git Bash）
git clone https://github.com/itanaka66/ai-agent-system.git
cd ai-agent-system
./install.sh --all
```
```powershell
# Windows（PowerShell）
git clone https://github.com/itanaka66/ai-agent-system.git
cd ai-agent-system
.\install.ps1 -All
```

**3. 軽量モデルを取得**（初回のみ、合計約5〜8GB、GPU不要でCPUで動作）
```bash
docker compose exec ollama ollama pull llama3:8b
docker compose exec ollama ollama pull phi3:mini
```

**4. Web UI を開いてエージェントのモデルを設定（必須）**
1. http://localhost:3000 を開く - これが本アプリ自身の Web UI である **Agent Console**（`frontend/`）で、`--all` の時点ですでに起動しています。
2. **エージェント設定** に進む。
3. `qwen2.5:32b`（本番用の既定値）のままになっている各エージェントについて、**モデル** を `llama3:8b`（軽量・高速にしたい場合は `phi3:mini`）に変更して保存する。変更は再起動不要で即座に反映されます。

この手順を省略すると、`mode=simple` のチャットしか動作せず、`standard`/`debate` は「モデルが見つからない」エラーになります。

**5. 使ってみる**
- API 経由でチャット：下記の[使用方法](#使用方法)を参照
- または Web UI でプロンプト・temperature を調整したり、カスタムなエージェントパイプラインを作成：下記の[Web UI](#web-uiエージェントのグラフィカルなカスタマイズ)を参照

エージェント・RAGメモリ・ログ保存まで、すべてコンテナ上で動作しています。停止する場合は `docker compose down` を実行してください。

RTX 3090 + Intel Arc A770 + CPU クラスターによる本番構成（自身の既定値と一致するモデル割り当て済み）は、下記の「インストール手順」を参照してください。

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
| 🖥️ エージェントコンソール | 標準搭載の Web UI（`frontend/`）でエージェントのプロンプト・モデルやワークフローをファイル編集なしにグラフィカルに設定可能 - **クイックスタート後は必須**（取得したモデルにエージェントを合わせるため）で、単なるおまけ機能ではない |

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

## インストール手順（専用ハードウェア／本番構成）
RTX 3090 + Intel Arc A770 + CPU クラスターによる本番構成向けです。初めての方は上記のクイックスタートをご利用ください。

# リポジトリをクローン
``` bash
git clone https://github.com/itanaka66/ai-agent-system.git
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

### オプション：アプリ本体や Qdrant / PostgreSQL / Ollama / Flowise を Docker で起動
専用ハードウェアで稼働させていない場合、`docker-compose.yml` でこれら（本アプリのバックエンド／Web UI を含む。上記クイックスタート参照）をローカルに起動できます。各サービスは同名の Compose [プロファイル](https://docs.docker.com/compose/how-tos/profiles/) に紐づいており、CLI から起動するサービスを選択できます。

```bash
# 対話形式で選択（各サービスに y/N で回答）- Linux/macOS/WSL/Git Bash
./install.sh
# Windows PowerShell
.\install.ps1

# または CLI フラグで明示的に選択
./install.sh --qdrant --postgres --ollama --flowise
./install.sh --all

# 上記と等価な docker compose 直接実行
docker compose --profile qdrant --profile postgres up -d
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
`frontend/` 以下に React 製の SPA があり、ブラウザからエージェントを設定できます。**クイックスタートに従った場合、これは任意ではありません** - 上記の手順4の通り、初期状態のエージェントは32Bモデルを前提としているため、実際に取得したモデルに合わせるにはこの画面（または裏側の `/api/v1/agents` REST API）が必要です。

`--all`／Docker 経由ではすでに http://localhost:3000 で起動済みです。フロントエンド開発用に単独で起動する場合：
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 （/api を :8000 のバックエンドへプロキシ）
```

- **エージェント設定** — 各パイプライン段階（提案／批評／判定／検証／標準応答／高速実行）のモデル・システムプロンプト・temperature・max_tokens を編集できます。保存すると再起動なしで次回のチャットリクエストから反映されます。
- **ワークフロービルダー** — キャンバス上にエージェントノードをドラッグ配置し、入出力変数名でデータフローを設計、テスト実行できます。ワークフローは `configs/workflow_configs/*.json` に保存されます。

これらは新規追加した REST API（`/api/v1/agents`、`/api/v1/agents/models`、`/api/v1/workflows`、`/api/v1/workflows/{name}/run`）に対応しています。既存の Flowise 連携（`FLOWISE_URL`）はそのまま併用可能です。

## 環境変数
テンプレートは2種類あります：`.env.example`（専用ハードウェア／本番構成、上記の既定値）と `.env.docker.example`（全体をDockerで動かすクイックスタート向け。`ollama`/`postgres`/`qdrant` などコンテナのホスト名を指定し、軽量なCPU向けモデルを使用）。`install.sh`/`install.ps1` が自動的に適切な方を選びます。

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