#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "仮想環境を作成しています..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

echo "日程調整アシスタントを起動します..."
echo "ブラウザが開かない場合は http://localhost:8501 を開いてください"
echo "終了するときはこの窓で Ctrl+C を押してください"
echo ""

.venv/bin/streamlit run app.py --server.headless false
