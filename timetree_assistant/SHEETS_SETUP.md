# Google スプレッドシート連携の設定

仮押さえ・除外ルール・送信文の言い回しを **永続保存** する手順です。

## 1. スプレッドシートを作る

1. [Google スプレッドシート](https://sheets.google.com) で新規作成
2. 名前は例: `日程調整アシスタントデータ`
3. URL から ID をコピー  
   `https://docs.google.com/spreadsheets/d/【ここがID】/edit`

## 2. サービスアカウントを作る

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. **APIとサービス → ライブラリ** で **Google Sheets API** を有効化
3. **APIとサービス → 認証情報 → サービスアカウント** で作成
4. キー → **鍵を追加 → JSON** をダウンロード

## 3. スプレッドシートを共有

JSON 内の `client_email`（例: `xxx@xxx.iam.gserviceaccount.com`）を  
スプレッドシートの **共有 → 編集者** として追加します。

## 4. Streamlit Cloud の Secrets に設定

https://share.streamlit.io → アプリ → **Settings → Secrets**

```toml
[deploy]
platform = "cloud"

[sheets]
spreadsheet_id = "あなたのスプレッドシートID"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

`private_key` は JSON ファイルの値をそのまま貼ります（`\n` を含む）。

## 5. 動作確認

アプリを再読み込みし、画面上部が **「スプレッドシートに保存中」** になれば OK です。

データはシートの **A1 セル** に JSON 形式で保存されます。
