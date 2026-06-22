# LINE 家計簿・ビジネス管理ボット v1（アーカイブ）

2026年6月時点で稼働していたシステムの完全バックアップです。

## 構成

| フォルダ | 内容 |
|---------|------|
| `gas/` | Google Apps Script（LINE Webhook・家計簿・ビジネスボット）16ファイル |
| `python/` | Python 予約システム（別系統） |

## GAS システム情報（復元時の参考）

- **Script ID**: `13xHyY5BQPaPnWmf9qDpWU1DysgTxygF4fYDqZmuUIYkBVAKHhYionGpY`
- **Webhook デプロイ ID**: `AKfycbwhK1hdWTMu-S8xYIbcDgEKhyhFUCVaHhmVg4pbWKwhqie916508PXBqT507RHbV1T-6A`
- **バージョン確認**: doGet → `line-yoga-bot ok (function-base-v1)`
- **アーキテクチャ**: 関数ベース（`xxx_()` 形式に統一）

### スクリプトプロパティ（GAS側・コードには含めない）

- `LINE_TOKEN` … LINE Channel Access Token（必須）
- `ADMIN_KEY` … メンテ用（既定: `souko-fix-menu`）

### 予約スプレッドシート

- ヨガ予約管理: `https://docs.google.com/spreadsheets/d/1xmws_P9LDCT5fY8F_KM7_AG3qEUJsuaqwNT5BuYLsDg/edit#gid=0`
- `Config.js` の `RESERVATION.URL` に設定

### 復元コマンド

```bash
cd gas/
clasp login
clasp push
clasp deploy -i AKfycbwhK1hdWTMu-S8xYIbcDgEKhyhFUCVaHhmVg4pbWKwhqie916508PXBqT507RHbV1T-6A --description "restore"
```

### メンテ用 URL

```
.../exec?action=fixMenu&key=souko-fix-menu
.../exec?action=fixBusinessMenu&key=souko-fix-menu
.../exec?action=fixReservationUrl&key=souko-fix-menu
```

## 主な機能

- 家計簿：食費・外食、返済2段階選択、備考付き記帳、月次レポート
- ビジネス：売上5種類、経費直接入力、予約確認リンク、ビジネスレポート
- リッチメニュー自動作成・切替

## 注意

- `LINE_TOKEN` 等の秘密情報はこのアーカイブに含まれていません
- 本番 GAS プロジェクトは Google 側にそのまま残っています（clasp で再デプロイ可能）
