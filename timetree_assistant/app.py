"""TimeTree 日程調整アシスタント（ダミーデータ試作品）

TimeTree API 連携前のスマホ向け UI プロトタイプ。
本番利用は Streamlit Cloud 公開を想定（どこからでもアクセス可能）。
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from storage import (
    init_persistence,
    persist_session,
    sheets_configured,
    storage_status_label,
)

APP_DIR = Path(__file__).resolve().parent
MANUAL_PATH = APP_DIR / "MANUAL.md"
CONFIG_PATH = APP_DIR / "config.json"
SLOTS_PLACEHOLDER = "{slots}"

DUMMY_SLOTS = [
    "7月6日(月) 10:00〜12:00",
    "7月6日(月) 14:00〜16:00",
    "7月7日(火) 13:00〜15:00",
    "7月9日(木) 11:00〜13:00",
]

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]
FULL_SLOT_RE = re.compile(
    r"(\d+)月(\d+)日\(([月火水木金土日])\)\s+(\d{2}:\d{2})〜(\d{2}:\d{2})"
)
SLOT_RE = FULL_SLOT_RE

DURATION_PRESETS = {
    "30分": 30,
    "45分": 45,
    "1時間": 60,
    "1.5時間": 90,
    "2時間": 120,
}
STEP_OPTIONS = {"30分ごと": 30, "1時間ごと": 60}
BUFFER_OPTIONS = {"なし": 0, "15分": 15, "30分": 30}
DAYS_AHEAD_OPTIONS = {"7日": 7, "14日": 14, "30日": 30}

WEEKDAY_STYLES = {
    "月": {"bg": "#E3F2FD", "border": "#1976D2", "badge": "#1976D2"},
    "火": {"bg": "#FFF3E0", "border": "#EF6C00", "badge": "#EF6C00"},
    "水": {"bg": "#E8F5E9", "border": "#2E7D32", "badge": "#2E7D32"},
    "木": {"bg": "#F3E5F5", "border": "#7B1FA2", "badge": "#7B1FA2"},
    "金": {"bg": "#E0F2F1", "border": "#00695C", "badge": "#00695C"},
    "土": {"bg": "#E8EAF6", "border": "#3949AB", "badge": "#3949AB"},
    "日": {"bg": "#FFEBEE", "border": "#C62828", "badge": "#C62828"},
}

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


@dataclass(frozen=True)
class FreeWindow:
    month: int
    day: int
    weekday: str
    start: str
    end: str

    @property
    def label(self) -> str:
        return f"{self.month}月{self.day}日({self.weekday})"

    def to_source_string(self) -> str:
        return f"{self.label} {self.start}〜{self.end}"

    def on_date(self, year: int) -> date:
        return date(year, self.month, self.day)


@dataclass(frozen=True)
class SlotSearchSettings:
    duration_min: int
    step_min: int
    buffer_min: int
    use_business_hours: bool
    business_start: str
    business_end: str
    days_ahead: int


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


def save_keeps(keeps: list[dict]) -> None:
    st.session_state.keeps = keeps
    persist_session()


def save_blockouts(blockouts: list[dict]) -> None:
    st.session_state.blockouts = blockouts
    persist_session()


def save_recurring_rules(rules: list[dict]) -> None:
    st.session_state.recurring_rules = rules
    persist_session()


def format_keep_wait_status(keep: dict) -> tuple[str, bool]:
    created_at = keep.get("created_at")
    if not created_at:
        return "返事待ち", False
    try:
        kept_at = datetime.fromisoformat(created_at)
    except ValueError:
        return "返事待ち", False
    days = (datetime.now() - kept_at).days
    if days <= 0:
        return "今日キープ", False
    if days == 1:
        return "昨日キープ", False
    return f"{days}日前にキープ", days >= 3


def new_keep(name: str, slot: str) -> dict:
    return {
        "name": name,
        "slot": slot,
        "created_at": datetime.now().replace(second=0, microsecond=0).isoformat(),
    }


def load_manual_text() -> str:
    if MANUAL_PATH.exists():
        return MANUAL_PATH.read_text(encoding="utf-8")
    return "使い方ファイル（MANUAL.md）が見つかりません。"


def time_to_minutes(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def minutes_to_time(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def parse_slot(slot: str) -> tuple[str, str, str] | None:
    parsed = parse_slot_full(slot)
    if not parsed:
        return None
    return parsed["weekday"], parsed["start"], parsed["end"]


def parse_slot_full(slot: str) -> dict | None:
    match = FULL_SLOT_RE.search(slot)
    if not match:
        return None
    start_min = time_to_minutes(match.group(4))
    end_min = time_to_minutes(match.group(5))
    return {
        "month": int(match.group(1)),
        "day": int(match.group(2)),
        "weekday": match.group(3),
        "label": f"{match.group(1)}月{match.group(2)}日({match.group(3)})",
        "start": match.group(4),
        "end": match.group(5),
        "start_min": start_min,
        "end_min": end_min,
    }


def parse_free_window(slot: str) -> FreeWindow | None:
    parsed = parse_slot_full(slot)
    if not parsed:
        return None
    return FreeWindow(
        month=parsed["month"],
        day=parsed["day"],
        weekday=parsed["weekday"],
        start=parsed["start"],
        end=parsed["end"],
    )


def get_base_windows() -> list[FreeWindow]:
    windows = []
    for slot in DUMMY_SLOTS:
        window = parse_free_window(slot)
        if window:
            windows.append(window)
    return windows


def slots_overlap(a: str, b: str) -> bool:
    pa, pb = parse_slot_full(a), parse_slot_full(b)
    if not pa or not pb:
        return False
    if pa["label"] != pb["label"]:
        return False
    return pa["start_min"] < pb["end_min"] and pb["start_min"] < pa["end_min"]


def window_within_days(window: FreeWindow, days_ahead: int, today: date | None = None) -> bool:
    today = today or date.today()
    target = window.on_date(today.year)
    if target < today:
        return False
    return target <= today + timedelta(days=days_ahead)


def clip_window_to_business_hours(
    window: FreeWindow,
    business_start: str,
    business_end: str,
) -> FreeWindow | None:
    start = max(time_to_minutes(window.start), time_to_minutes(business_start))
    end = min(time_to_minutes(window.end), time_to_minutes(business_end))
    if end <= start:
        return None
    return FreeWindow(
        month=window.month,
        day=window.day,
        weekday=window.weekday,
        start=minutes_to_time(start),
        end=minutes_to_time(end),
    )


def generate_slots_from_window(
    window: FreeWindow,
    duration_min: int,
    step_min: int,
    buffer_min: int,
) -> list[str]:
    usable_start = time_to_minutes(window.start) + buffer_min
    usable_end = time_to_minutes(window.end) - buffer_min
    if usable_end - usable_start < duration_min:
        return []

    slots: list[str] = []
    cursor = usable_start
    while cursor + duration_min <= usable_end:
        slots.append(
            f"{window.label} {minutes_to_time(cursor)}〜{minutes_to_time(cursor + duration_min)}"
        )
        cursor += step_min
    return slots


def generate_candidate_slots(
    windows: list[FreeWindow],
    settings: SlotSearchSettings,
    today: date | None = None,
) -> list[str]:
    today = today or date.today()
    candidates: list[str] = []
    for window in windows:
        if not window_within_days(window, settings.days_ahead, today):
            continue
        active = window
        if settings.use_business_hours:
            clipped = clip_window_to_business_hours(
                window,
                settings.business_start,
                settings.business_end,
            )
            if not clipped:
                continue
            active = clipped
        candidates.extend(
            generate_slots_from_window(
                active,
                settings.duration_min,
                settings.step_min,
                settings.buffer_min,
            )
        )
    return candidates


def init_search_settings() -> None:
    defaults = {
        "search_duration_preset": "1時間",
        "search_custom_hours": 1,
        "search_custom_minutes": 0,
        "search_step_label": "30分ごと",
        "search_buffer_label": "15分",
        "search_use_business_hours": True,
        "search_business_start": "10:00",
        "search_business_end": "17:00",
        "search_days_label": "14日",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def build_search_settings() -> SlotSearchSettings:
    preset = st.session_state.search_duration_preset
    if preset == "カスタム":
        duration_min = (
            int(st.session_state.search_custom_hours) * 60
            + int(st.session_state.search_custom_minutes)
        )
    else:
        duration_min = DURATION_PRESETS[preset]

    duration_min = max(duration_min, 15)
    return SlotSearchSettings(
        duration_min=duration_min,
        step_min=STEP_OPTIONS[st.session_state.search_step_label],
        buffer_min=BUFFER_OPTIONS[st.session_state.search_buffer_label],
        use_business_hours=st.session_state.search_use_business_hours,
        business_start=st.session_state.search_business_start,
        business_end=st.session_state.search_business_end,
        days_ahead=DAYS_AHEAD_OPTIONS[st.session_state.search_days_label],
    )


def render_search_settings_panel() -> SlotSearchSettings:
    init_search_settings()
    with st.expander("🔍 空き枠の探し方", expanded=True):
        st.caption("所要時間に合う候補を、空き時間から自動で切り出します。")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.search_duration_preset = st.selectbox(
                "所要時間",
                list(DURATION_PRESETS.keys()) + ["カスタム"],
                index=(
                    list(DURATION_PRESETS.keys()) + ["カスタム"]
                ).index(st.session_state.search_duration_preset),
            )
        with col2:
            st.session_state.search_step_label = st.selectbox(
                "開始刻み",
                list(STEP_OPTIONS.keys()),
                index=list(STEP_OPTIONS.keys()).index(
                    st.session_state.search_step_label
                ),
            )

        if st.session_state.search_duration_preset == "カスタム":
            custom_col1, custom_col2 = st.columns(2)
            with custom_col1:
                st.session_state.search_custom_hours = st.number_input(
                    "時間",
                    min_value=0,
                    max_value=8,
                    value=int(st.session_state.search_custom_hours),
                )
            with custom_col2:
                st.session_state.search_custom_minutes = st.selectbox(
                    "分",
                    [0, 15, 30, 45],
                    index=[0, 15, 30, 45].index(
                        int(st.session_state.search_custom_minutes)
                    ),
                )

        col3, col4 = st.columns(2)
        with col3:
            st.session_state.search_buffer_label = st.selectbox(
                "前後のバッファ",
                list(BUFFER_OPTIONS.keys()),
                index=list(BUFFER_OPTIONS.keys()).index(
                    st.session_state.search_buffer_label
                ),
            )
        with col4:
            st.session_state.search_days_label = st.selectbox(
                "何日先まで",
                list(DAYS_AHEAD_OPTIONS.keys()),
                index=list(DAYS_AHEAD_OPTIONS.keys()).index(
                    st.session_state.search_days_label
                ),
            )

        st.session_state.search_use_business_hours = st.checkbox(
            "営業時間内だけ探す",
            value=st.session_state.search_use_business_hours,
        )
        if st.session_state.search_use_business_hours:
            biz_col1, biz_col2 = st.columns(2)
            with biz_col1:
                st.session_state.search_business_start = st.text_input(
                    "営業開始",
                    value=st.session_state.search_business_start,
                )
            with biz_col2:
                st.session_state.search_business_end = st.text_input(
                    "営業終了",
                    value=st.session_state.search_business_end,
                )

    settings = build_search_settings()
    persist_session()
    return settings


def slot_weekday(slot: str) -> str:
    parsed = parse_slot(slot)
    return parsed[0] if parsed else ""


def weekday_style(weekday: str) -> dict[str, str]:
    return WEEKDAY_STYLES.get(
        weekday,
        {"bg": "#F5F5F5", "border": "#9E9E9E", "badge": "#757575"},
    )


def group_slots_by_weekday(slots: list[str]) -> list[tuple[str, list[str]]]:
    buckets: dict[str, list[str]] = {day: [] for day in WEEKDAYS}
    for slot in slots:
        weekday = slot_weekday(slot)
        if weekday in buckets:
            buckets[weekday].append(slot)
    return [(day, buckets[day]) for day in WEEKDAYS if buckets[day]]


def render_weekday_legend(weekdays: list[str]) -> None:
    badges = []
    for day in weekdays:
        style = weekday_style(day)
        badges.append(
            f'<span class="weekday-legend" style="background:{style["badge"]};">{day}</span>'
        )
    st.markdown(
        '<div class="weekday-legend-row">' + "".join(badges) + "</div>",
        unsafe_allow_html=True,
    )


def render_slot_card(slot: str) -> None:
    weekday = slot_weekday(slot)
    style = weekday_style(weekday)
    st.markdown(
        f"""
<div class="slot-card" style="background:{style['bg']}; border-left:5px solid {style['border']};">
  <span class="weekday-badge" style="background:{style['badge']};">{weekday}</span>
  <span class="slot-text">{slot}</span>
</div>
        """.strip(),
        unsafe_allow_html=True,
    )


def render_copyable_slot(slot: str) -> None:
    """空き枠表示。曜日ごとに色分け。"""
    render_slot_card(slot)
    render_copy_action("LINE用にコピー", slot)


DEFAULT_LINE_TEMPLATE = (
    "お世話になっております。\n"
    "ご都合いかがでしょうか。以下の日程でご検討いただけますと幸いです。\n\n"
    f"{SLOTS_PLACEHOLDER}\n\n"
    "よろしくお願いいたします。"
)


def format_slots_block(slots: list[str]) -> str:
    return "\n".join(f"・{slot}" for slot in slots)


def build_message_from_template(template: str, slots: list[str]) -> str:
    if SLOTS_PLACEHOLDER in template:
        return template.replace(SLOTS_PLACEHOLDER, format_slots_block(slots))
    return template


def build_bulk_line_message(slots: list[str]) -> str:
    if not slots:
        return ""
    return build_message_from_template(DEFAULT_LINE_TEMPLATE, slots)


def get_saved_template() -> str | None:
    return st.session_state.get("saved_line_template")


def save_user_template(template: str) -> None:
    st.session_state.saved_line_template = template
    persist_session()


def clear_user_template() -> None:
    st.session_state.saved_line_template = None
    persist_session()


def extract_template_from_message(message: str, slots: list[str]) -> str:
    block = format_slots_block(slots)
    if block and block in message:
        return message.replace(block, SLOTS_PLACEHOLDER, 1)
    return message.strip()


def compose_line_message(slots: list[str]) -> str:
    template = get_saved_template()
    if template:
        return build_message_from_template(template, slots)
    return build_bulk_line_message(slots)


def render_copy_action(label: str, text: str) -> None:
    if hasattr(st, "copy_button"):
        st.copy_button(label, text, use_container_width=True)
    else:
        st.caption("下の枠をタップしてコピー")
        st.code(text, language=None)


def sync_line_draft(slots: list[str]) -> tuple[str, str]:
    """保存済みの言い回しがあればそれを使い、空き枠だけ差し替える。"""
    default = build_bulk_line_message(slots)
    text = compose_line_message(slots)
    return default, text


def render_line_message_composer(slots: list[str]) -> None:
    """まとめて送る LINE 文面。編集してからコピーできる。"""
    default, text = sync_line_draft(slots)
    st.markdown("**LINE用にまとめて送る**")
    if get_saved_template():
        st.caption("保存した言い回しを使用中です。空き枠だけ自動で差し替わります。")

    if st.session_state.get("line_compose_editing"):
        edited = st.text_area(
            "送信文を編集",
            value=text,
            height=220,
            key="line_compose_editor",
            help="編集完了を押すと、この言い回しが保存されます。",
        )

        col_copy, col_done, col_reset = st.columns(3)
        with col_copy:
            render_copy_action("編集した文面をコピー", edited)
        with col_done:
            if st.button("編集完了", use_container_width=True):
                save_user_template(extract_template_from_message(edited, slots))
                st.session_state.line_compose_editing = False
                st.rerun()
        with col_reset:
            if st.button("定型文に戻す", use_container_width=True):
                clear_user_template()
                st.session_state.line_compose_editing = False
                st.rerun()
        return

    render_copy_action("候補をまとめてコピー", text)
    col_edit, col_reset = st.columns(2)
    with col_edit:
        if st.button("✏️ 送信文を編集", use_container_width=True):
            st.session_state.line_compose_editing = True
            st.rerun()
    with col_reset:
        if st.button("定型文に戻す", use_container_width=True):
            clear_user_template()
            st.rerun()


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
    if any(slots_overlap(slot, keep["slot"]) for keep in keeps):
        return False
    if any(slots_overlap(slot, blockout["slot"]) for blockout in blockouts):
        return False
    if slot_blocked_by_recurring(slot, recurring_rules):
        return False
    return True


def available_slots(
    keeps: list[dict],
    blockouts: list[dict],
    recurring_rules: list[dict],
    settings: SlotSearchSettings,
) -> list[str]:
    candidates = generate_candidate_slots(get_base_windows(), settings)
    return [
        slot
        for slot in candidates
        if is_slot_available(slot, keeps, blockouts, recurring_rules)
    ]


def blockable_slots(
    blockouts: list[dict],
    recurring_rules: list[dict],
) -> list[str]:
    return [
        window.to_source_string()
        for window in get_base_windows()
        if not any(slots_overlap(window.to_source_string(), b["slot"]) for b in blockouts)
        and not slot_blocked_by_recurring(window.to_source_string(), recurring_rules)
    ]


def add_recurring_rule(rule: dict) -> bool:
    signature = rule_signature(rule)
    if any(rule_signature(existing) == signature for existing in st.session_state.recurring_rules):
        return False
    rule["id"] = str(uuid.uuid4())[:8]
    st.session_state.recurring_rules.append(rule)
    save_recurring_rules(st.session_state.recurring_rules)
    return True


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
  .slot-card {
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin: 0.35rem 0 0.75rem 0;
    display: flex;
    align-items: center;
    gap: 0.65rem;
  }
  .weekday-badge {
    color: #fff;
    font-weight: 700;
    font-size: 0.9rem;
    min-width: 1.8rem;
    height: 1.8rem;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .slot-text {
    font-size: 1rem;
    line-height: 1.4;
    color: #212121;
  }
  .weekday-legend-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 0.75rem;
  }
  .weekday-legend {
    color: #fff;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
  }
</style>
""",
    unsafe_allow_html=True,
)

init_persistence()
init_search_settings()
creds = resolve_credentials()
token_ready = valid_token(creds["token"])
cloud_mode = is_cloud_deploy()

st.title("📱 日程調整アシスタント")
st.write("LINEの横に置いて使う、スケジュール管理ツール")
st.caption(f"💾 {storage_status_label()}")

if st.session_state.get("_storage_error"):
    st.warning(st.session_state["_storage_error"])

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
        if sheets_configured():
            st.info("仮押さえ・除外ルール・送信文はスプレッドシートに保存されます。")
        else:
            st.info(
                "仮押さえ・除外ルールはこの端末のセッション中だけ保持されます。"
                "永続保存するにはスプレッドシート連携を設定してください（使い方参照）。"
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

search_settings = render_search_settings_panel()
settings_summary = (
    f"条件: {search_settings.duration_min}分枠 / "
    f"{search_settings.step_min}分刻み / "
    f"バッファ{search_settings.buffer_min}分 / "
    f"{search_settings.days_ahead}日先まで"
)
if search_settings.use_business_hours:
    settings_summary += (
        f" / 営業時間 {search_settings.business_start}〜{search_settings.business_end}"
    )
st.caption(settings_summary)

slots = available_slots(
    st.session_state.keeps,
    st.session_state.blockouts,
    st.session_state.recurring_rules,
    search_settings,
)
if not slots:
    st.info(
        "条件に合う空き枠がありません。"
        "所要時間・営業時間・バッファを変えるか、"
        "「提示しない時間」・繰り返しルール・仮押さえを解除してください。"
    )
else:
    render_line_message_composer(slots)
    st.divider()

    grouped = group_slots_by_weekday(slots)
    render_weekday_legend([day for day, _ in grouped])
    for weekday, day_slots in grouped:
        style = weekday_style(weekday)
        st.markdown(
            f'<p style="margin:1rem 0 0.25rem 0; font-weight:700; color:{style["badge"]};">'
            f"■ {weekday}曜日</p>",
            unsafe_allow_html=True,
        )
        for slot in day_slots:
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
            elif any(slots_overlap(keep_slot, k["slot"]) for k in st.session_state.keeps):
                st.error("その時間帯はすでに仮押さえされています。")
            else:
                st.session_state.keeps.append(new_keep(name, keep_slot))
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
        wait_label, urgent = format_keep_wait_status(keep)
        if urgent:
            st.error(f"⏳ {keep['name']}\n{keep['slot']}\n📅 {wait_label}")
        else:
            st.warning(f"⏳ {keep['name']}\n{keep['slot']}\n📅 {wait_label}")

        if st.session_state.get("pending_confirm_index") == i:
            st.error(
                f"**登録の最終確認**\n\n"
                f"相手: **{keep['name']}**\n\n"
                f"日時: **{keep['slot']}**\n\n"
                f"TimeTree に登録します。（本番想定）"
            )
            col_ok, col_back = st.columns(2)
            with col_ok:
                if st.button(
                    "登録する",
                    key=f"confirm_yes_{i}",
                    use_container_width=True,
                    type="primary",
                ):
                    done = st.session_state.keeps.pop(i)
                    save_keeps(st.session_state.keeps)
                    st.session_state.pending_confirm_index = None
                    st.session_state.flash_success = True
                    st.session_state.flash_success_msg = (
                        f"🎉 【{done['name']}】{done['slot']} を TimeTree に登録しました！（本番想定）"
                    )
                    st.rerun()
            with col_back:
                if st.button("戻る", key=f"confirm_no_{i}", use_container_width=True):
                    st.session_state.pending_confirm_index = None
                    st.rerun()
            continue

        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("確定", key=f"confirm_{i}", use_container_width=True, type="primary"):
                st.session_state.pending_confirm_index = i
                st.rerun()
        with col_cancel:
            if st.button("解除", key=f"cancel_{i}", use_container_width=True):
                st.session_state.keeps.pop(i)
                save_keeps(st.session_state.keeps)
                st.session_state.flash_info = True
                st.session_state.flash_info_msg = "仮押さえを解除しました。"
                st.rerun()

with st.expander("📖 使い方ガイド"):
    st.markdown(load_manual_text())

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
