#!/usr/bin/env bash
# Select which Docker services to start for this project - the app itself
# (backend + web UI) and/or its optional backing services (Qdrant,
# PostgreSQL, Ollama, Flowise) - via CLI flags or an interactive prompt, then
# start them with `docker compose` using matching Compose profiles.
#
# Works on Linux, macOS, and Windows (inside WSL or Git Bash). Native
# Windows PowerShell users: see install.ps1 instead.
#
# Usage:
#   ./install.sh [--app] [--qdrant] [--postgres] [--ollama] [--flowise] [--all]
#   ./install.sh              # no flags: interactive picker
#   ./install.sh --all        # everything: full beginner quick start
#
set -euo pipefail
cd "$(dirname "$0")"

ALL_SERVICES=(app qdrant postgres ollama flowise)
SERVICES=()

usage() {
  cat <<EOF
Usage: $0 [--app] [--qdrant] [--postgres] [--ollama] [--flowise] [--all]

Selects which services to start via docker compose profiles. Run with no
flags for an interactive yes/no prompt per service.

  --app        This project's own backend API + web UI (built locally)
  --qdrant     Vector database (RAG / conversation memory)
  --postgres   PostgreSQL (chat/session logs)
  --ollama     Local Ollama server (LLM inference)
  --flowise    Flowise (visual workflow designer)
  --all        Start every service above (recommended for a first try)
  -h, --help   Show this help

First time on Windows/macOS/Linux/cloud? Run: $0 --all
EOF
}

if [ "$#" -gt 0 ]; then
  for arg in "$@"; do
    case "$arg" in
      --app|--qdrant|--postgres|--ollama|--flowise) SERVICES+=("${arg#--}") ;;
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

if [ ! -f .env ]; then
  if is_selected app && [ -f .env.docker.example ]; then
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

if is_selected app; then
  echo ""
  echo "Web UI: http://localhost:3000"
  echo "API:    http://localhost:8000"
fi
