# 新規プロジェクト

前のシステム（LINE 家計簿・ビジネスボット）は  
`archive/line_yoga_system_v1/` に保存されています。

## 現在のプロジェクト

### `timetree_assistant/` — TimeTree 日程調整アシスタント

LINE 横で使うスマホ向けの日程調整ツール（空き枠・仮押さえ・確定）。  
**本番は Streamlit Cloud 公開**（どこからでも URL で利用）。現在はダミーデータ試作品。

```bash
cd timetree_assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

クラウド公開手順: `timetree_assistant/DEPLOY.md`  
詳細: `timetree_assistant/README.md`

### `folder_rotator/` — フォルダ自動仕分けツール（課題用）

妹さん向けのドラッグ＆ドロップ式フォルダローテーションアプリ。

```bash
cd folder_rotator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
# config.json を編集してから
python app.py
```

詳細は `folder_rotator/README.md` を参照。

## アーカイブの場所

```
archive/line_yoga_system_v1/
├── README.md    … システム情報・復元手順
├── gas/         … GAS コード一式（16ファイル）
└── python/      … Python 予約システム
```

## 旧システムを再開したい場合

```bash
cp -r archive/line_yoga_system_v1/gas/* .
clasp push
```

詳細は `archive/line_yoga_system_v1/README.md` を参照してください。
