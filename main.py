import requests
from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ----------------
# Google Sheets接続
# ----------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

reserve_sheet = client.open("ヨガ予約管理").sheet1
event_sheet = client.open("ヨガ予約管理").worksheet("イベント管理")

# ----------------
# LINE TOKEN
# ----------------

LINE_TOKEN = "ここはそのまま"

# ----------------
# 状態管理
# ----------------

reserve_wait = {}
cancel_wait = {}

# ----------------
# LINE返信
# ----------------

def reply_message(reply_token, text, items=None):
    try:
        url = "https://api.line.me/v2/bot/message/reply"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        }

        message = {
            "type": "text",
            "text": text
        }

        if items:
            message["quickReply"] = {"items": items}

        data = {
            "replyToken": reply_token,
            "messages": [message]
        }

        requests.post(url, headers=headers, json=data, timeout=10)

    except Exception as e:
        print("reply_message エラー:", e)

# ----------------
# PUSH送信
# ----------------

def push_message(user_id, text):
    try:
        url = "https://api.line.me/v2/bot/message/push"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        }

        data = {
            "to": user_id,
            "messages": [{
                "type": "text",
                "text": text
            }]
        }

        requests.post(url, headers=headers, json=data, timeout=10)

    except Exception as e:
        print("push_message エラー:", e)

# ----------------
# 名前取得
# ----------------

def get_profile(user_id):
    try:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"
        headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=10)
        return r.json().get("displayName", "不明")
    except:
        return "不明"

# ----------------
# イベント取得
# ----------------

def get_events():
    try:
        return event_sheet.get_all_records()
    except:
        return []

def get_event_map():
    return {str(e["イベントID"]): e for e in get_events()}

# ----------------
# 予約メニュー
# ----------------

def show_events(reply_token):
    items = []

    for e in get_events():
        label = f"{e['イベント名']} {str(e['日付'])[5:10]}"

        items.append({
            "type": "action",
            "action": {
                "type": "message",
                "label": label[:20],
                "text": str(e["イベントID"])
            }
        })

    reply_message(reply_token, "予約するイベントを選んでください", items)

# ----------------
# 予約処理
# ----------------

def reserve_event(user_id, name, event_id, reply_token):

    event_map = get_event_map()

    if event_id not in event_map:
        reply_message(reply_token, "イベントが見つかりません")
        return

    event = event_map[event_id]
    records = reserve_sheet.get_all_records()

    latest = None
    for r in records:
        if r["ユーザーID"] == user_id and str(r["イベントID"]) == event_id:
            latest = r

    if latest and latest["ステータス"] in ["予約", "キャンセル待ち"]:
        reply_message(reply_token, "すでに予約しています")
        return

    count = sum(
        1 for r in records
        if str(r["イベントID"]) == event_id and r["ステータス"] == "予約"
    )

    status = "予約" if count < int(event["定員"]) else "キャンセル待ち"

    reserve_sheet.append_row([
        name,
        user_id,
        event_id,
        event["イベント名"],
        event["日付"],
        status
    ])

    # 🔥ここが追加
    message = f"{event['イベント名']}\n{event['日付']}\n{status}"

    if status == "キャンセル待ち":
        message += "\n\n※キャンセルが出た場合は自動で繰り上がります"

    reply_message(reply_token, message)

# ----------------
# CHECK
# ----------------

def check_reservation(user_id, reply_token):

    records = reserve_sheet.get_all_records()

    user_records = [
        r for r in records if r["ユーザーID"] == user_id
    ]

    if not user_records:
        reply_message(reply_token, "予約はありません")
        return

    event_map = {}

    for r in user_records:
        eid = str(r["イベントID"])

        if eid not in event_map:
            event_map[eid] = []

        event_map[eid].append(r)

    latest_list = [logs[-1] for logs in event_map.values()]

    result = []

    for r in latest_list:
        if r["ステータス"] == "キャンセル":
            continue

        result.append(
            f"{r['イベント名']}\n{r['日付']}\n{r['ステータス']}"
        )

    if not result:
        reply_message(reply_token, "予約はありません")
    else:
        reply_message(
            reply_token,
            "あなたの予約\n\n" + "\n\n".join(result)
        )

# ----------------
# CANCELメニュー
# ----------------

def cancel_menu(user_id, reply_token):

    records = reserve_sheet.get_all_records()

    items = []
    added = set()

    for r in records:

        if r["ユーザーID"] != user_id:
            continue

        if r["ステータス"] not in ["予約", "キャンセル待ち"]:
            continue

        eid = str(r["イベントID"])

        if eid in added:
            continue

        label = f"{r['イベント名']} {str(r['日付'])[5:10]}"

        items.append({
            "type": "action",
            "action": {
                "type": "message",
                "label": label[:20],
                "text": eid
            }
        })

        added.add(eid)

    if not items:
        reply_message(reply_token, "キャンセルできる予約がありません")
        return

    cancel_wait[user_id] = True
    reply_message(reply_token, "キャンセルするイベントを選択", items)

# ----------------
# CANCEL実行
# ----------------

def cancel_reservation(user_id, event_id, reply_token):

    records = reserve_sheet.get_all_records()

    target_row = None

    for i, r in enumerate(records, start=2):

        if (
            r["ユーザーID"] == user_id
            and str(r["イベントID"]) == event_id
            and r["ステータス"] in ["予約", "キャンセル待ち"]
        ):
            reserve_sheet.update_cell(i, 6, "キャンセル")
            target_row = i
            break

    if not target_row:
        reply_message(reply_token, "見つかりません")
        return

    records = reserve_sheet.get_all_records()

    for i, r in enumerate(records, start=2):

        if (
            str(r["イベントID"]) == event_id
            and r["ステータス"] == "キャンセル待ち"
        ):
            reserve_sheet.update_cell(i, 6, "予約")

            try:
                push_message(
                    r["ユーザーID"],
                    f"{r['イベント名']}\n繰り上げで予約確定しました！"
                )
            except:
                pass

            break

    reply_message(reply_token, "キャンセルしました")

# ----------------
# リマインド
# ----------------

def send_reminder():

    records = reserve_sheet.get_all_records()

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")

    for r in records:

        if str(r["日付"]).startswith(tomorrow) and r["ステータス"] == "予約":

            try:
                push_message(
                    r["ユーザーID"],
                    f"【リマインド】\n明日の予約です👇\n\n{r['イベント名']}\n{r['日付']}\nお待ちしてます！"
                )
            except:
                pass

# ----------------
# WEBHOOK
# ----------------

@app.route("/webhook", methods=["POST"])
def webhook():

    body = request.json

    for event in body["events"]:

        if event["type"] != "message":
            continue

        text = event["message"]["text"].strip()
        user_id = event["source"]["userId"]
        reply_token = event["replyToken"]

        name = get_profile(user_id)

        if text == "予約":
            reserve_wait[user_id] = True
            show_events(reply_token)
            continue

        if reserve_wait.get(user_id):
            reserve_event(user_id, name, text, reply_token)
            reserve_wait[user_id] = False
            continue

        if text == "CHECK":
            check_reservation(user_id, reply_token)
            continue

        if text == "CANCEL":
            cancel_menu(user_id, reply_token)
            continue

        if cancel_wait.get(user_id):
            cancel_reservation(user_id, text, reply_token)
            cancel_wait[user_id] = False
            continue

        reply_message(reply_token, "予約 / CHECK / CANCEL")

    return "OK"

# ----------------
# 起動
# ----------------

if __name__ == "__main__":
   port = int(os.environ.get("PORT", 5001))
app.run(host="0.0.0.0", port=port)