# 新規プロジェクト

前のシステム（LINE 家計簿・ビジネスボット）は  
`archive/line_yoga_system_v1/` に保存されています。

ここから新しいシステムを作れます。

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
