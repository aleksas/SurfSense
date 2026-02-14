#!/bin/sh
set -eu

# Keeps selected Ollama models warm to avoid cold-load latency.
#
# This uses Ollama's per-request `keep_alive` to pin runners in memory.
# Tune the context sizes to fit your GPU VRAM budget.

OLLAMA_URL="${OLLAMA_URL:-http://ollama:11434}"

CHAT_MODEL="${OLLAMA_KEEPALIVE_CHAT_MODEL:-qwen3:30b-a3b}"
CHAT_NUM_CTX="${OLLAMA_KEEPALIVE_CHAT_NUM_CTX:-8192}"

RERANK_MODEL="${OLLAMA_KEEPALIVE_RERANK_MODEL:-dengcao/Qwen3-Reranker-0.6B:Q8_0}"
RERANK_NUM_CTX="${OLLAMA_KEEPALIVE_RERANK_NUM_CTX:-2048}"

KEEP_ALIVE="${OLLAMA_KEEPALIVE_DURATION:-2h}"
REFRESH_SECS="${OLLAMA_KEEPALIVE_REFRESH_SECS:-3600}"

echo "[keepalive] waiting for ollama at $OLLAMA_URL ..."
until curl -sf "$OLLAMA_URL/api/tags" >/dev/null; do
  sleep 1
done

post_chat() {
  curl -sS -X POST "$OLLAMA_URL/api/chat" \
    -H 'Content-Type: application/json' \
    -d "{
      \"model\": \"${CHAT_MODEL}\",
      \"messages\": [{\"role\": \"user\", \"content\": \"ping\"}],
      \"stream\": false,
      \"keep_alive\": \"${KEEP_ALIVE}\",
      \"options\": {\"temperature\": 0, \"num_predict\": 8, \"num_ctx\": ${CHAT_NUM_CTX}}
    }" >/dev/null
}

post_rerank() {
  curl -sS -X POST "$OLLAMA_URL/api/generate" \
    -H 'Content-Type: application/json' \
    -d "{
      \"model\": \"${RERANK_MODEL}\",
      \"prompt\": \"Return only one number between 0 and 1.\\n\\nQuery: ping\\n\\nDocument: pong\\n\\nScore:\",
      \"stream\": false,
      \"keep_alive\": \"${KEEP_ALIVE}\",
      \"options\": {\"temperature\": 0, \"num_predict\": 8, \"num_ctx\": ${RERANK_NUM_CTX}}
    }" >/dev/null
}

while true; do
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[keepalive] $ts warming chat=${CHAT_MODEL} ctx=${CHAT_NUM_CTX} keep_alive=${KEEP_ALIVE}"
  post_chat || echo "[keepalive] WARN: chat warmup failed"

  echo "[keepalive] $ts warming rerank=${RERANK_MODEL} ctx=${RERANK_NUM_CTX} keep_alive=${KEEP_ALIVE}"
  post_rerank || echo "[keepalive] WARN: rerank warmup failed"

  sleep "${REFRESH_SECS}"
done

