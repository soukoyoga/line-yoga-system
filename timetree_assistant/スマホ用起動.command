#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "仮想環境を作成しています..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")

echo "========================================"
echo "  スマホ用に起動します"
echo "========================================"
echo ""
echo "【Mac のブラウザ】"
echo "  http://localhost:8501"
echo ""
if [ -n "$IP" ]; then
  echo "【スマホのブラウザ】同じ Wi-Fi に接続してから"
  echo "  http://${IP}:8501"
  echo ""
  echo "  ↑ この URL を Safari / Chrome に入力"
else
  echo "【スマホ】Wi-Fi IP が取得できませんでした。"
  echo "  ターミナルに表示される Network URL を確認してください。"
fi
echo ""
echo "終了: この窓で Ctrl+C"
echo "========================================"
echo ""

.venv/bin/streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.headless true
