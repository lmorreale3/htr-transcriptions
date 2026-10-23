"""Conti's own data: ROOT/conti_data/<collection>/… (plain JSON, versioned with the project's git).

settings.json       per manuscript: date style (florentine / pisan / modern), pound sign, statuses to include,
                    account_holder (who is owed when an entry names no creditor: used by the Ask tab's debts)
sums_review.json    Laura's decisions on sums: {key: {written, decision: ok|corrected|not_sum, text, value, t}}
                    key = "<page id>|<line ids>"; a decision whose "written" no longer matches the transcription
                    is shown as "changed since review" and no longer counts as confirmed.
Every write keeps the previous file as <name>.bak.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from .source import ROOT, conventions

DATA = ROOT / "conti_data"
_lock = threading.Lock()

DEFAULT_SETTINGS = {"date_style": "florentine", "statuses": ["finished", "sent_to_training"],
                    "leggio_url": "http://127.0.0.1:8770"}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _path(cid: str, name: str) -> Path:
    return DATA / cid / name


def read(cid: str, name: str, default):
    p = _path(cid, name)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write(cid: str, name: str, obj) -> None:
    p = _path(cid, name)
    with _lock:
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.with_suffix(p.suffix + ".bak").write_bytes(p.read_bytes())
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, p)


def write_root(name: str, obj) -> None:
    """A file shared by all manuscripts: conti_data/<name>."""
    write("", name, obj)


def read_root(name: str, default):
    return read("", name, default)


def settings(cid: str) -> dict:
    s = dict(DEFAULT_SETTINGS)
    s["pound"] = (conventions(cid).get("params") or {}).get("pound") or "℔"
    s.update(read(cid, "settings.json", {}))
    return s


def save_settings(cid: str, body: dict) -> dict:
    cur = read(cid, "settings.json", {})
    for k in ("date_style", "pound", "statuses", "leggio_url", "account_holder"):
        if k in body:
            cur[k] = body[k]
    write(cid, "settings.json", cur)
    return settings(cid)


def reviews(cid: str) -> dict:
    return read(cid, "sums_review.json", {})


def set_review(cid: str, key: str, entry: dict | None) -> dict:
    r = reviews(cid)
    if entry is None:
        r.pop(key, None)
    else:
        entry["t"] = now()
        r[key] = entry
    write(cid, "sums_review.json", r)
    return r
