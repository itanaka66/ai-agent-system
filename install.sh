#!/usr/bin/env bash
# Select which optional Docker services (Qdrant, PostgreSQL, Ollama, Flowise)
# to start for this project, via CLI flags or an interactive prompt, then
# start them with `docker compose` using matching Compose profiles.
#
# Usage:
#   ./install.sh [--qdrant] [--postgres] [--ollama] [--flowise] [--all]
#   ./install.sh              # no flags: interactive picker
#   ./install.sh --qdrant --postgres
#
set -euo pipefail
cd "$(dirname "$0")"

ALL_SERVICES=(qdrant postgres ollama flowise)
SERVICES=()

usage() {
  cat <<EOF
Usage: $0 [--qdrant] [--postgres] [--ollama] [--flowise] [--all]

Selects which optional backing services to start via docker compose
profiles. Run with no flags for an interactive yes/no prompt per service.

  --qdrant     Vector database (RAG / conversation memory)
  --postgres   PostgreSQL (chat/session logs)
  --ollama     Local Ollama server (LLM inference)
  --flowise    Flowise (visual workflow designer)
  --all        Start every service above
  -h, --help   Show this help
EOF
}

if [ "$#" -gt 0 ]; then
  for arg in "$@"; do
    case "$arg" in
      --qdrant|--postgres|--ollama|--flowise) SERVICES+=("${arg#--}") ;;
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

if [ ! -f .env ]; then
  echo ".env が見つからないため .env.example からコピーします / .env not found, copying from .env.example"
  cp .env.example .env
fi

echo "起動するサービス / Starting services: ${SERVICES[*]}"

PROFILE_ARGS=()
for svc in "${SERVICES[@]}"; do
  PROFILE_ARGS+=(--profile "$svc")
done

docker compose "${PROFILE_ARGS[@]}" up -d

echo ""
echo "起動完了。状態確認: docker compose ps"
echo "Done. Check status with: docker compose ps"

for svc in "${SERVICES[@]}"; do
  if [ "$svc" = "ollama" ]; then
    echo "Ollama モデルの取得例 / pull a model: docker compose exec ollama ollama pull qwen2.5:32b-q4_K_M"
  fi
done
