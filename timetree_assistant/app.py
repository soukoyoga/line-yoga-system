"""TimeTree 日程調整アシスタント（ダミーデータ試作品）

TimeTree API 連携前のスマホ向け UI プロトタイプ。
本番利用は Streamlit Cloud 公開を想定（どこからでもアクセス可能）。
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
KEEPS_PATH = APP_DIR / "keeps.json"
BLOCKOUTS_PATH = APP_DIR / "blockouts.json"

DUMMY_SLOTS = [
    "7月6日(月) 10:00〜12:00",
    "7月6日(月) 14:00〜16:00",
    "7月7日(火) 13:00〜15:00",
    "7月9日(木) 11:00〜13:00",
]

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


def init_keeps() -> None:
    if "keeps" in st.session_state:
        return
    st.session_state.keeps = [] if is_cloud_deploy() else load_keeps()


def init_blockouts() -> None:
    if "blockouts" in st.session_state:
        return
    st.session_state.blockouts = [] if is_cloud_deploy() else load_blockouts()


def available_slots(keeps: list[dict], blockouts: list[dict]) -> list[str]:
    kept = {k["slot"] for k in keeps}
    blocked = {b["slot"] for b in blockouts}
    return [s for s in DUMMY_SLOTS if s not in kept and s not in blocked]


def blockable_slots(blockouts: list[dict]) -> list[str]:
    blocked = {b["slot"] for b in blockouts}
    return [s for s in DUMMY_SLOTS if s not in blocked]


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
            "仮押さえ・提示しない時間は、この端末のセッション中だけ保持されます"
            "（ブラウザを閉じると消えます）。"
        )

with st.expander("🚫 提示しない時間（プライベート）"):
    st.caption(
        "TimeTree に予定がなくても、実家・家族時間など"
        "「社外には出したくない時間」をここで除外します。"
    )
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
        st.write("除外中の時間はありません。")

    hideable = blockable_slots(st.session_state.blockouts)
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

slots = available_slots(st.session_state.keeps, st.session_state.blockouts)
if not slots:
    st.info(
        "空き枠がありません。"
        "「提示しない時間」や仮押さえを解除すると戻ります。"
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
