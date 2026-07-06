"""TimeTree 日程調整アシスタント（ダミーデータ試作品）

TimeTree API 連携前のスマホ向け UI プロトタイプ。
本番利用は Streamlit Cloud 公開を想定（どこからでもアクセス可能）。
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
KEEPS_PATH = APP_DIR / "keeps.json"
BLOCKOUTS_PATH = APP_DIR / "blockouts.json"
RECURRING_RULES_PATH = APP_DIR / "recurring_rules.json"

DUMMY_SLOTS = [
    "7月6日(月) 10:00〜12:00",
    "7月6日(月) 14:00〜16:00",
    "7月7日(火) 13:00〜15:00",
    "7月9日(木) 11:00〜13:00",
]

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]
SLOT_RE = re.compile(r"\(([月火水木金土日])\)\s+(\d{2}:\d{2})〜(\d{2}:\d{2})")

RECURRING_PRESETS = {
    "weekend": {
        "label": "毎週土日",
        "weekdays": ["土", "日"],
        "start_time": None,
        "end_time": None,
    },
    "weekday_evening": {
        "label": "平日18時以降",
        "weekdays": ["月", "火", "水", "木", "金"],
        "start_time": "18:00",
        "end_time": "23:59",
    },
}

PLACEHOLDER_TOKENS = {"", "your_token_here", "ここにTimeTreeパーソナルアクセストークン"}


def load_file_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_secrets_config() -> dict:
    try:
        tt = st.secrets.get("timetree", {})
        return {
            "timetree_personal_token": tt.get("personal_token", ""),
            "calendar_id": tt.get("calendar_id", ""),
        }
    except (FileNotFoundError, KeyError, AttributeError):
        return {}


def is_cloud_deploy() -> bool:
    try:
        return st.secrets.get("deploy", {}).get("platform") == "cloud"
    except (FileNotFoundError, KeyError, AttributeError):
        return False


def valid_token(token: str) -> bool:
    t = (token or "").strip()
    return bool(t) and t not in PLACEHOLDER_TOKENS and "ここに自分の" not in t


def resolve_credentials() -> dict:
    """優先順: Streamlit Secrets > セッション入力 > config.json"""
    secrets_cfg = load_secrets_config()
    file_cfg = load_file_config()

    token = (
        secrets_cfg.get("timetree_personal_token")
        or st.session_state.get("user_token")
        or file_cfg.get("timetree_personal_token")
        or ""
    )
    calendar_id = (
        secrets_cfg.get("calendar_id")
        or st.session_state.get("user_calendar_id")
        or file_cfg.get("calendar_id")
        or ""
    )
    return {
        "token": token.strip(),
        "calendar_id": calendar_id.strip(),
        "from_secrets": valid_token(secrets_cfg.get("timetree_personal_token", "")),
    }


def load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_json_list(path: Path, items: list[dict]) -> None:
    if is_cloud_deploy():
        return
    path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_keeps() -> list[dict]:
    return load_json_list(KEEPS_PATH)


def save_keeps(keeps: list[dict]) -> None:
    save_json_list(KEEPS_PATH, keeps)


def load_blockouts() -> list[dict]:
    return load_json_list(BLOCKOUTS_PATH)


def save_blockouts(blockouts: list[dict]) -> None:
    save_json_list(BLOCKOUTS_PATH, blockouts)


def load_recurring_rules() -> list[dict]:
    return load_json_list(RECURRING_RULES_PATH)


def save_recurring_rules(rules: list[dict]) -> None:
    save_json_list(RECURRING_RULES_PATH, rules)


def init_keeps() -> None:
    if "keeps" in st.session_state:
        return
    st.session_state.keeps = [] if is_cloud_deploy() else load_keeps()


def init_blockouts() -> None:
    if "blockouts" in st.session_state:
        return
    st.session_state.blockouts = [] if is_cloud_deploy() else load_blockouts()


def init_recurring_rules() -> None:
    if "recurring_rules" in st.session_state:
        return
    st.session_state.recurring_rules = [] if is_cloud_deploy() else load_recurring_rules()


def parse_slot(slot: str) -> tuple[str, str, str] | None:
    match = SLOT_RE.search(slot)
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def time_to_minutes(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def times_overlap(slot_start: str, slot_end: str, rule_start: str, rule_end: str) -> bool:
    start_slot = time_to_minutes(slot_start)
    end_slot = time_to_minutes(slot_end)
    start_rule = time_to_minutes(rule_start)
    end_rule = time_to_minutes(rule_end)
    return start_slot < end_rule and start_rule < end_slot


def rule_signature(rule: dict) -> tuple:
    return (
        tuple(sorted(rule.get("weekdays", []))),
        rule.get("start_time"),
        rule.get("end_time"),
    )


def format_weekdays(weekdays: list[str]) -> str:
    if not weekdays:
        return ""
    ordered = [day for day in WEEKDAYS if day in weekdays]
    if ordered == ["月", "火", "水", "木", "金"]:
        return "月〜金"
    if ordered == ["土", "日"]:
        return "土・日"
    return "・".join(ordered)


def format_rule(rule: dict) -> str:
    days = format_weekdays(rule.get("weekdays", []))
    label = rule.get("label") or "繰り返しルール"
    start_time = rule.get("start_time")
    end_time = rule.get("end_time")
    if start_time and end_time:
        return f"{label}（{days} {start_time}〜{end_time}）"
    return f"{label}（{days} 終日）"


def slot_blocked_by_rule(slot: str, rule: dict) -> bool:
    parsed = parse_slot(slot)
    if not parsed:
        return False
    weekday, slot_start, slot_end = parsed
    if weekday not in rule.get("weekdays", []):
        return False
    rule_start = rule.get("start_time")
    rule_end = rule.get("end_time")
    if not rule_start or not rule_end:
        return True
    return times_overlap(slot_start, slot_end, rule_start, rule_end)


def slot_blocked_by_recurring(slot: str, rules: list[dict]) -> bool:
    return any(slot_blocked_by_rule(slot, rule) for rule in rules)


def is_slot_available(
    slot: str,
    keeps: list[dict],
    blockouts: list[dict],
    recurring_rules: list[dict],
) -> bool:
    if any(keep["slot"] == slot for keep in keeps):
        return False
    if any(blockout["slot"] == slot for blockout in blockouts):
        return False
    if slot_blocked_by_recurring(slot, recurring_rules):
        return False
    return True


def available_slots(
    keeps: list[dict],
    blockouts: list[dict],
    recurring_rules: list[dict],
) -> list[str]:
    return [
        slot
        for slot in DUMMY_SLOTS
        if is_slot_available(slot, keeps, blockouts, recurring_rules)
    ]


def blockable_slots(
    blockouts: list[dict],
    recurring_rules: list[dict],
) -> list[str]:
    return [
        slot
        for slot in DUMMY_SLOTS
        if not any(blockout["slot"] == slot for blockout in blockouts)
        and not slot_blocked_by_recurring(slot, recurring_rules)
    ]


def add_recurring_rule(rule: dict) -> bool:
    signature = rule_signature(rule)
    if any(rule_signature(existing) == signature for existing in st.session_state.recurring_rules):
        return False
    rule["id"] = str(uuid.uuid4())[:8]
    st.session_state.recurring_rules.append(rule)
    save_recurring_rules(st.session_state.recurring_rules)
    return True


def render_copyable_slot(slot: str) -> None:
    """空き枠表示。copy_button 非対応環境では code ブロックにフォールバック。"""
    st.info(f"🟢 {slot}")
    if hasattr(st, "copy_button"):
        st.copy_button("LINE用にコピー", slot, use_container_width=True)
    else:
        st.caption("下の枠をタップしてコピー")
        st.code(slot, language=None)


st.set_page_config(
    page_title="TimeTree調整アシスタント",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
  .stButton > button {
    min-height: 3rem;
    font-size: 1rem;
  }
  div[data-testid="stFormSubmitButton"] > button {
    min-height: 3rem;
    font-size: 1.05rem;
    font-weight: 600;
  }
  div[data-testid="stAlert"] {
    font-size: 1rem;
  }
  .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 640px;
  }
</style>
""",
    unsafe_allow_html=True,
)

init_keeps()
init_blockouts()
init_recurring_rules()
creds = resolve_credentials()
token_ready = valid_token(creds["token"])
cloud_mode = is_cloud_deploy()

st.title("📱 日程調整アシスタント")
st.write("LINEの横に置いて使う、スケジュール管理ツール")

if cloud_mode:
    st.caption("🌐 クラウド版 — どこからでも利用できます")
elif token_ready:
    st.caption("TimeTree: トークン設定済み（API連携は今後実装）")
else:
    st.caption("TimeTree: ダミーデータモード")

with st.expander("TimeTree 設定"):
    if creds["from_secrets"]:
        st.success("トークンはクラウドの Secrets で設定済みです。")
    else:
        st.markdown(
            "自分の TimeTree パーソナルアクセストークンを入力してください。"
            "（この端末のセッション内だけ保持。ページを開き直すと再入力が必要です）"
        )
        token_input = st.text_input(
            "パーソナルアクセストークン",
            value=st.session_state.get("user_token", ""),
            type="password",
        )
        calendar_input = st.text_input(
            "カレンダー ID",
            value=st.session_state.get("user_calendar_id", ""),
        )
        if st.button("設定を反映", use_container_width=True):
            st.session_state.user_token = token_input.strip()
            st.session_state.user_calendar_id = calendar_input.strip()
            st.rerun()

    if cloud_mode:
        st.info(
            "仮押さえ・提示しない時間・繰り返しルールは、この端末のセッション中だけ保持されます"
            "（ブラウザを閉じると消えます）。"
        )

with st.expander("🚫 提示しない時間（プライベート）"):
    st.caption(
        "TimeTree に予定がなくても、実家・家族時間など"
        "「社外には出したくない時間」をここで除外します。"
    )

    st.markdown("**繰り返しルール**")
    if st.session_state.recurring_rules:
        for i, rule in enumerate(st.session_state.recurring_rules):
            col_info, col_remove = st.columns([4, 1])
            with col_info:
                st.error(f"🔁 {format_rule(rule)}")
            with col_remove:
                if st.button("解除", key=f"unrule_{i}", use_container_width=True):
                    st.session_state.recurring_rules.pop(i)
                    save_recurring_rules(st.session_state.recurring_rules)
                    st.session_state.flash_info = True
                    st.session_state.flash_info_msg = "繰り返しルールを解除しました。"
                    st.rerun()
    else:
        st.write("繰り返しルールはありません。")

    preset_cols = st.columns(2)
    with preset_cols[0]:
        if st.button("毎週土日を非表示", use_container_width=True):
            if add_recurring_rule(dict(RECURRING_PRESETS["weekend"])):
                st.session_state.flash_success = True
                st.session_state.flash_success_msg = "毎週土日を非表示に設定しました。"
            else:
                st.session_state.flash_info = True
                st.session_state.flash_info_msg = "同じ繰り返しルールがすでにあります。"
            st.rerun()
    with preset_cols[1]:
        if st.button("平日18時以降を非表示", use_container_width=True):
            if add_recurring_rule(dict(RECURRING_PRESETS["weekday_evening"])):
                st.session_state.flash_success = True
                st.session_state.flash_success_msg = "平日18時以降を非表示に設定しました。"
            else:
                st.session_state.flash_info = True
                st.session_state.flash_info_msg = "同じ繰り返しルールがすでにあります。"
            st.rerun()

    with st.form("recurring_rule_form", clear_on_submit=True):
        custom_days = st.multiselect(
            "曜日（カスタム）",
            WEEKDAYS,
            default=["土", "日"],
        )
        all_day = st.checkbox("終日", value=True)
        custom_start = st.text_input("開始時刻", value="18:00", disabled=all_day)
        custom_end = st.text_input("終了時刻", value="21:00", disabled=all_day)
        custom_label = st.text_input("ルール名（任意）", placeholder="例：家族時間")
        add_rule_btn = st.form_submit_button(
            "カスタムルールを追加",
            use_container_width=True,
        )
        if add_rule_btn:
            if not custom_days:
                st.error("曜日を1つ以上選んでください。")
            else:
                rule = {
                    "label": custom_label.strip() or "カスタムルール",
                    "weekdays": custom_days,
                    "start_time": None if all_day else custom_start.strip(),
                    "end_time": None if all_day else custom_end.strip(),
                }
                if add_recurring_rule(rule):
                    st.session_state.flash_success = True
                    st.session_state.flash_success_msg = f"🔁 {format_rule(rule)} を追加しました。"
                else:
                    st.session_state.flash_info = True
                    st.session_state.flash_info_msg = "同じ繰り返しルールがすでにあります。"
                st.rerun()

    st.divider()
    st.markdown("**この日だけ非表示**")
    if st.session_state.blockouts:
        for i, block in enumerate(st.session_state.blockouts):
            label = block.get("reason") or "プライベート"
            col_info, col_remove = st.columns([4, 1])
            with col_info:
                st.error(f"🚫 {block['slot']}\n（{label}）")
            with col_remove:
                if st.button("解除", key=f"unblock_{i}", use_container_width=True):
                    st.session_state.blockouts.pop(i)
                    save_blockouts(st.session_state.blockouts)
                    st.session_state.flash_info = True
                    st.session_state.flash_info_msg = "提示しない時間を解除しました。"
                    st.rerun()
    else:
        st.write("単発の除外はありません。")

    hideable = blockable_slots(
        st.session_state.blockouts,
        st.session_state.recurring_rules,
    )
    if hideable:
        with st.form("blockout_form", clear_on_submit=True):
            hide_slot = st.selectbox("除外する日時", hideable)
            hide_reason = st.text_input("理由（任意）", placeholder="例：実家、家族時間")
            hide_btn = st.form_submit_button(
                "この時間を非表示",
                use_container_width=True,
            )
            if hide_btn:
                st.session_state.blockouts.append(
                    {"slot": hide_slot, "reason": hide_reason.strip()}
                )
                save_blockouts(st.session_state.blockouts)
                st.session_state.flash_success = True
                st.session_state.flash_success_msg = f"🚫 「{hide_slot}」を空き枠から除外しました。"
                st.rerun()
    else:
        st.info("すべての枠が除外済みです。上の「解除」で戻せます。")

if st.session_state.pop("flash_success", None):
    st.balloons()
    st.success(st.session_state.pop("flash_success_msg", "完了しました。"))
elif st.session_state.pop("flash_info", None):
    st.info(st.session_state.pop("flash_info_msg", ""))

# --- 1. 空き枠 ---
st.subheader("1. 空き枠を選んでコピー")

slots = available_slots(
    st.session_state.keeps,
    st.session_state.blockouts,
    st.session_state.recurring_rules,
)
if not slots:
    st.info(
        "空き枠がありません。"
        "「提示しない時間」・繰り返しルール・仮押さえを解除すると戻ります。"
    )
else:
    for slot in slots:
        render_copyable_slot(slot)

# --- 2. 仮押さえ ---
st.subheader("2. 提示した枠をキープ")

if not slots:
    st.warning("キープできる空き枠がありません。")
else:
    with st.form("keep_form", clear_on_submit=True):
        keep_name = st.text_input("相手のお名前（例：田中様）")
        keep_slot = st.selectbox("キープする日時", slots)
        submit_btn = st.form_submit_button(
            "仮押さえキープ",
            use_container_width=True,
        )

        if submit_btn:
            name = keep_name.strip()
            if not name:
                st.error("お名前を入力してください。")
            elif any(k["slot"] == keep_slot for k in st.session_state.keeps):
                st.error("その枠はすでに仮押さえされています。")
            else:
                st.session_state.keeps.append({"name": name, "slot": keep_slot})
                save_keeps(st.session_state.keeps)
                st.session_state.flash_success = True
                st.session_state.flash_success_msg = (
                    f"📌 【{name}】に「{keep_slot}」を仮押さえしました！"
                )
                st.rerun()

# --- 3. 仮押さえ一覧 ---
st.subheader("3. 仮押さえ中のリスト")

if not st.session_state.keeps:
    st.write("現在、仮押さえはありません。")
else:
    for i, keep in enumerate(st.session_state.keeps):
        st.warning(f"⏳ {keep['name']}\n{keep['slot']}")
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("確定", key=f"confirm_{i}", use_container_width=True, type="primary"):
                done = st.session_state.keeps.pop(i)
                save_keeps(st.session_state.keeps)
                st.session_state.flash_success = True
                st.session_state.flash_success_msg = (
                    f"🎉 【{done['name']}】{done['slot']} を TimeTree に登録しました！（本番想定）"
                )
                st.rerun()
        with col_cancel:
            if st.button("解除", key=f"cancel_{i}", use_container_width=True):
                st.session_state.keeps.pop(i)
                save_keeps(st.session_state.keeps)
                st.session_state.flash_info = True
                st.session_state.flash_info_msg = "仮押さえを解除しました。"
                st.rerun()

with st.expander("公開・渡し方"):
    st.markdown(
        """
**どこからでも使う**には Streamlit Cloud に公開します（無料）。

1. GitHub に push
2. [share.streamlit.io](https://share.streamlit.io) でデプロイ
3. Main file path: `timetree_assistant/app.py`
4. 相手に URL を渡す（スマホでホーム画面に追加）

詳しくは `DEPLOY.md` を参照してください。
        """.strip()
    )
