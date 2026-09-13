#!/usr/bin/env bash
# Select which Docker services to start for this project - this project's own
# backend and/or web UI (independently selectable), and/or its optional
# backing services (Qdrant, PostgreSQL, Ollama, Flowise) - via CLI flags or
# an interactive prompt, then start them with `docker compose` using
# matching Compose profiles.
#
# Works on Linux, macOS, and Windows (inside WSL or Git Bash). Native
# Windows PowerShell users: see install.ps1 instead.
#
# Usage:
#   ./install.sh [--orchestrator] [--webui] [--qdrant] [--postgres] [--ollama] [--flowise] [--all]
#   ./install.sh              # no flags: interactive picker
#   ./install.sh --all        # everything: full beginner quick start
#   ./install.sh --webui      # just the web UI (see README "Installing just the Web UI")
#
set -euo pipefail
cd "$(dirname "$0")"

ALL_SERVICES=(orchestrator webui qdrant postgres ollama flowise)
SERVICES=()

usage() {
  cat <<EOF
Usage: $0 [--orchestrator] [--webui] [--app] [--qdrant] [--postgres] [--ollama] [--flowise] [--all]

Selects which services to start via docker compose profiles. Run with no
flags for an interactive yes/no prompt per service.

  --orchestrator  This project's own backend API (built locally)
  --webui         This project's own web UI / Agent Console (built locally)
  --app           Shorthand for --orchestrator --webui together
  --qdrant        Vector database (RAG / conversation memory)
  --postgres      PostgreSQL (chat/session logs)
  --ollama        Local Ollama server (LLM inference)
  --flowise       Flowise (visual workflow designer)
  --all           Start every service above (recommended for a first try)
  -h, --help      Show this help

First time on Windows/macOS/Linux/cloud? Run: $0 --all
Only want the web UI (e.g. backend runs elsewhere)? Run: $0 --webui
EOF
}

if [ "$#" -gt 0 ]; then
  for arg in "$@"; do
    case "$arg" in
      --orchestrator|--webui|--qdrant|--postgres|--ollama|--flowise) SERVICES+=("${arg#--}") ;;
      --app) SERVICES+=("orchestrator" "webui") ;;
      --all) SERVICES=("${ALL_SERVICES[@]}") ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown option: $arg" >&2; usage; exit 1 ;;
    esac
  done
else
  echo "起動するサービスを選択してください / Select services to start:"
  for svc in "${ALL_SERVICES[@]}"; do
    read -r -p "  $svc を起動しますか？ [y/N]: " answer
    case "$answer" in
      [yY]*) SERVICES+=("$svc") ;;
    esac
  done
fi

if [ "${#SERVICES[@]}" -eq 0 ]; then
  echo "サービスが選択されませんでした。終了します。 / No services selected, exiting."
  exit 0
fi

is_selected() {
  local target="$1"
  for svc in "${SERVICES[@]}"; do
    [ "$svc" = "$target" ] && return 0
  done
  return 1
}

# De-duplicate (e.g. `--app --webui` would otherwise list "webui" twice)
DEDUPED=()
for svc in "${SERVICES[@]}"; do
  is_in_deduped=0
  for d in "${DEDUPED[@]:-}"; do
    [ "$d" = "$svc" ] && is_in_deduped=1 && break
  done
  [ "$is_in_deduped" -eq 0 ] && DEDUPED+=("$svc")
done
SERVICES=("${DEDUPED[@]}")

if [ ! -f .env ]; then
  if { is_selected orchestrator || is_selected webui; } && [ -f .env.docker.example ]; then
    echo ".env が見つからないため .env.docker.example からコピーします / .env not found, copying from .env.docker.example"
    cp .env.docker.example .env
  else
    echo ".env が見つからないため .env.example からコピーします / .env not found, copying from .env.example"
    cp .env.example .env
  fi
fi

echo "起動するサービス / Starting services: ${SERVICES[*]}"

PROFILE_ARGS=()
for svc in "${SERVICES[@]}"; do
  PROFILE_ARGS+=(--profile "$svc")
done

docker compose "${PROFILE_ARGS[@]}" up -d --build

echo ""
echo "起動完了。状態確認: docker compose ps"
echo "Done. Check status with: docker compose ps"

if is_selected ollama; then
  echo "Ollama モデルの取得例 / pull the default models:"
  echo "  docker compose exec ollama ollama pull llama3:8b"
  echo "  docker compose exec ollama ollama pull phi3:mini"
fi

if is_selected webui || is_selected orchestrator; then
  echo ""
  is_selected webui && echo "Web UI: http://localhost:3000"
  is_selected orchestrator && echo "API:    http://localhost:8000"
fi
