#!/bin/bash
# Streamlit Community Cloud へ API でデプロイするスクリプト
#
# 事前準備（初回のみ）:
# 1. https://share.streamlit.io に GitHub でログイン
# 2. アカウント設定 → API tokens でトークンを発行
# 3. 環境変数に設定:
#      export STREAMLIT_API_TOKEN="st_xxxx..."
#
# 実行:
#   ./deploy_streamlit.sh

set -euo pipefail

REPO="${STREAMLIT_REPO:-soukoyoga/line-yoga-system}"
BRANCH="${STREAMLIT_BRANCH:-main}"
MAIN_FILE="${STREAMLIT_MAIN_FILE:-timetree_assistant/app.py}"
APP_NAME="${STREAMLIT_APP_NAME:-timetree-assistant}"

if [ -z "${STREAMLIT_API_TOKEN:-}" ]; then
  echo "エラー: STREAMLIT_API_TOKEN が未設定です。"
  echo ""
  echo "1. https://share.streamlit.io を GitHub でログイン"
  echo "2. Settings → API tokens でトークンを発行"
  echo "3. export STREAMLIT_API_TOKEN=\"st_...\""
  echo "4. もう一度 ./deploy_streamlit.sh"
  exit 1
fi

echo "デプロイ中: ${REPO} (${BRANCH}) → ${MAIN_FILE}"

RESPONSE=$(curl -sS -w "\n%{http_code}" -X POST "https://api.streamlit.io/v1/apps" \
  -H "Authorization: Bearer ${STREAMLIT_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"repo\":\"${REPO}\",\"branch\":\"${BRANCH}\",\"mainFile\":\"${MAIN_FILE}\",\"appName\":\"${APP_NAME}\"}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
  echo "デプロイを開始しました。"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  URL=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('url',''))" 2>/dev/null || true)
  if [ -n "$URL" ]; then
    echo ""
    echo "公開 URL: $URL"
  fi
else
  echo "デプロイ失敗 (HTTP ${HTTP_CODE})"
  echo "$BODY"
  exit 1
fi
