# クラウド公開手順（どこからでも使う）

このアプリを **Streamlit Community Cloud（無料）** に載せると、

`https://xxxx.streamlit.app`

のような URL がもらえます。スマホの LTE からでも、外出先からでも開けます。

---

## 1. GitHub にコードを置く

リポジトリに `timetree_assistant/` フォルダごと push します。

---

## 2. Streamlit Cloud でデプロイ

1. https://share.streamlit.io にアクセス（GitHub アカウントでログイン）
2. **New app** をクリック
3. 設定:
   - **Repository**: このリポジトリ
   - **Branch**: `main`（または使っているブランチ）
   - **Main file path**: `timetree_assistant/app.py`
4. **Advanced settings** → **Secrets** に以下を貼る:

```toml
[timetree]
personal_token = "使う人のTimeTreeトークン"
calendar_id = "カレンダーID"

[deploy]
platform = "cloud"
```

5. **Deploy** をクリック

数分後、公開 URL が表示されます。

---

## 3. スマホで使う

1. 公開 URL を Safari / Chrome で開く
2. **共有 → ホーム画面に追加** でアイコン化
3. LINE と並べて使う

Mac を起動したままにする必要は **ありません**。

---

## 相手に渡すとき

### パターン A: URL だけ渡す（おすすめ）

あなたが Streamlit Cloud にデプロイし、**相手のトークンを Secrets に設定**してから URL を渡します。

相手は Python 不要。URL をブックマークするだけです。

### パターン B: 相手が自分でトークンを入れる

Secrets にトークンを書かずにデプロイし、相手がアプリ内の **「TimeTree 設定」** から自分のトークンを入力します。

- トークンはそのブラウザのセッション内だけ（サーバーにファイル保存しない）
- ページを開き直すと再入力が必要

---

## 注意

| 項目 | ローカル（Mac起動） | クラウド公開 |
|------|---------------------|--------------|
| どこからでも使える | ×（同じ Wi-Fi のみ） | ○ |
| Mac 常時起動 | 必要 | 不要 |
| 仮押さえの保存 | ファイルに永続 | セッション中のみ |
| トークン | config.json | Secrets またはアプリ内入力 |

仮押さえをクラウドでも永続化するには、今後 DB 連携が必要です（TimeTree API 実装時に一緒に検討）。

---

## ローカル開発（任意）

クラウド公開前の UI 確認用:

```bash
cd timetree_assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
