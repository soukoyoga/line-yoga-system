"""永続化レイヤー（ローカル JSON / Google スプレッドシート）"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
KEEPS_PATH = APP_DIR / "keeps.json"
BLOCKOUTS_PATH = APP_DIR / "blockouts.json"
RECURRING_RULES_PATH = APP_DIR / "recurring_rules.json"
LINE_TEMPLATE_PATH = APP_DIR / "line_template.json"
SEARCH_SETTINGS_PATH = APP_DIR / "search_settings.json"
SHEETS_DATA_CELL = "A1"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def is_cloud_deploy() -> bool:
    try:
        return st.secrets.get("deploy", {}).get("platform") == "cloud"
    except (FileNotFoundError, KeyError, AttributeError):
        return False


def sheets_configured() -> bool:
    try:
        sheets = st.secrets.get("sheets", {})
        spreadsheet_id = (sheets.get("spreadsheet_id") or "").strip()
        return bool(spreadsheet_id) and _has_service_account()
    except (FileNotFoundError, KeyError, AttributeError):
        return False


def _has_service_account() -> bool:
    try:
        if st.secrets.get("gcp_service_account"):
            return True
        raw = st.secrets.get("sheets", {}).get("service_account_json", "")
        return bool(raw and "{" in str(raw))
    except (FileNotFoundError, KeyError, AttributeError):
        return False


def _service_account_info() -> dict:
    if "gcp_service_account" in st.secrets:
        return dict(st.secrets["gcp_service_account"])
    raw = st.secrets["sheets"]["service_account_json"]
    if isinstance(raw, str):
        return json.loads(raw)
    return dict(raw)


def _load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _save_json_file(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def empty_snapshot() -> dict[str, Any]:
    return {
        "keeps": [],
        "blockouts": [],
        "recurring_rules": [],
        "line_template": None,
        "search_settings": {},
    }


@st.cache_resource(show_spinner=False)
def _get_worksheet():
    from google.oauth2.service_account import Credentials
    import gspread

    creds = Credentials.from_service_account_info(
        _service_account_info(),
        scopes=SHEETS_SCOPES,
    )
    client = gspread.authorize(creds)
    spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id).sheet1


def load_from_sheets() -> dict[str, Any]:
    try:
        ws = _get_worksheet()
        raw = ws.acell(SHEETS_DATA_CELL).value or ""
        if not raw.strip():
            return empty_snapshot()
        data = json.loads(raw)
        snapshot = empty_snapshot()
        snapshot.update(data)
        return snapshot
    except Exception as exc:
        st.session_state["_storage_error"] = f"スプレッドシート読込エラー: {exc}"
        return empty_snapshot()


def save_to_sheets(snapshot: dict[str, Any]) -> None:
    try:
        ws = _get_worksheet()
        ws.update_acell(SHEETS_DATA_CELL, json.dumps(snapshot, ensure_ascii=False))
        st.session_state.pop("_storage_error", None)
    except Exception as exc:
        st.session_state["_storage_error"] = f"スプレッドシート保存エラー: {exc}"


def load_from_files() -> dict[str, Any]:
    template_data = _load_json_file(LINE_TEMPLATE_PATH, {})
    template = template_data.get("template") if isinstance(template_data, dict) else None
    return {
        "keeps": _load_json_file(KEEPS_PATH, []),
        "blockouts": _load_json_file(BLOCKOUTS_PATH, []),
        "recurring_rules": _load_json_file(RECURRING_RULES_PATH, []),
        "line_template": template,
        "search_settings": _load_json_file(SEARCH_SETTINGS_PATH, {}),
    }


def save_to_files(snapshot: dict[str, Any]) -> None:
    _save_json_file(KEEPS_PATH, snapshot.get("keeps", []))
    _save_json_file(BLOCKOUTS_PATH, snapshot.get("blockouts", []))
    _save_json_file(RECURRING_RULES_PATH, snapshot.get("recurring_rules", []))
    template = snapshot.get("line_template")
    if template:
        _save_json_file(LINE_TEMPLATE_PATH, {"template": template})
    elif LINE_TEMPLATE_PATH.exists():
        LINE_TEMPLATE_PATH.unlink()
    settings = snapshot.get("search_settings") or {}
    if settings:
        _save_json_file(SEARCH_SETTINGS_PATH, settings)
    elif SEARCH_SETTINGS_PATH.exists():
        SEARCH_SETTINGS_PATH.unlink()


def load_snapshot() -> dict[str, Any]:
    if sheets_configured():
        return load_from_sheets()
    if is_cloud_deploy():
        return empty_snapshot()
    return load_from_files()


def save_snapshot(snapshot: dict[str, Any]) -> None:
    if sheets_configured():
        save_to_sheets(snapshot)
        return
    if not is_cloud_deploy():
        save_to_files(snapshot)


def current_snapshot() -> dict[str, Any]:
    return {
        "keeps": st.session_state.get("keeps", []),
        "blockouts": st.session_state.get("blockouts", []),
        "recurring_rules": st.session_state.get("recurring_rules", []),
        "line_template": st.session_state.get("saved_line_template"),
        "search_settings": _export_search_settings(),
    }


def _export_search_settings() -> dict[str, Any]:
    keys = [
        "search_duration_preset",
        "search_custom_hours",
        "search_custom_minutes",
        "search_step_label",
        "search_buffer_label",
        "search_use_business_hours",
        "search_business_start",
        "search_business_end",
        "search_days_label",
    ]
    return {key: st.session_state.get(key) for key in keys if key in st.session_state}


def _import_search_settings(settings: dict[str, Any]) -> None:
    for key, value in settings.items():
        st.session_state[key] = value


def persist_session() -> None:
    if sheets_configured() or not is_cloud_deploy():
        save_snapshot(current_snapshot())


def init_persistence() -> None:
    if st.session_state.get("_persistence_loaded"):
        return

    snapshot = load_snapshot()
    st.session_state.keeps = snapshot.get("keeps", [])
    st.session_state.blockouts = snapshot.get("blockouts", [])
    st.session_state.recurring_rules = snapshot.get("recurring_rules", [])
    st.session_state.saved_line_template = snapshot.get("line_template")
    if snapshot.get("search_settings"):
        _import_search_settings(snapshot["search_settings"])
    st.session_state._persistence_loaded = True


def storage_status_label() -> str:
    if sheets_configured():
        return "スプレッドシートに保存中"
    if is_cloud_deploy():
        return "このブラウザのセッション内のみ保存"
    return "この Mac に保存中"
