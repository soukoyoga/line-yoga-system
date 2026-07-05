# TimeTree 日程調整アシスタント

LINE の横に置いて使う、スマホ向けの日程調整ツールです。

- 空き枠の確認・コピー
- 提示した枠の仮押さえ（バッティング防止）
- 確定後の TimeTree 登録（本番想定・API 連携は今後）

現在は **ダミーデータ** で UI を試せる試作品です。

---

## 本番の使い方（どこからでも・おすすめ）

**Streamlit Cloud（無料）** に公開すると、固定 URL でスマホの LTE からも使えます。  
Mac を起動したままにする必要はありません。

👉 **手順は [`DEPLOY.md`](DEPLOY.md) を参照**

ざっくり:

1. GitHub に push
2. https://share.streamlit.io でデプロイ（Main file: `timetree_assistant/app.py`）
3. 相手に `https://xxxx.streamlit.app` を渡す
4. スマホで「ホーム画面に追加」

---

## ローカルで試す（開発用）

UI の確認だけなら Mac 上で起動できます。

```bash
cd timetree_assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

または **`起動.command`** をダブルクリック → http://localhost:8501

※ ローカル起動は **同じ Wi-Fi 内のスマホ** からしか触れません。  
外出先から使うには上記のクラウド公開が必要です。

---

## トークン設定

| 方法 | 向いている人 |
|------|-------------|
| Streamlit Cloud の Secrets | 相手に URL だけ渡す（おすすめ） |
| アプリ内「TimeTree 設定」 | 各自が自分で入力 |
| `config.json`（ローカル） | 開発・テスト |

トークンはチャットで送らないでください。

```bash
cp config.example.json config.json   # ローカル開発時のみ
```

---

## 相手に渡すとき

**クラウド公開後:**

- 渡すもの: **URL だけ**
- 渡さないもの: トークン、config.json

**ソースごと渡す場合:**

- `app.py`, `requirements.txt`, `.streamlit/`, `DEPLOY.md`, `config.example.json`
- 相手が自分で Streamlit Cloud にデプロイ

---

## 画面の使い方

1. **空き枠** … 「LINE用にコピー」で貼り付け
2. **仮押さえ** … 相手名と日時を選んでキープ
3. **一覧** … 「確定」または「解除」

- **ローカル**: 仮押さえは `keeps.json` に保存
- **クラウド**: 仮押さえはセッション中のみ（永続化は今後 DB 連携予定）
