"""Read-only access to Leggio's workspace. Conti NEVER writes into workspace/ or leggio/.

Leggio's own export code (leggio/leggio/export_data.page_rows) is used to turn a page into lines, so Conti groups
sums and dates with their entry lines exactly as Leggio's spreadsheet export does. Results are cached per page by
file modification time, so edits made in Leggio show up on the next request.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

ROOT = Path(os.environ.get("CONTI_ROOT") or Path(__file__).resolve().parents[2]).resolve()
os.environ.setdefault("LEGGIO_ROOT", str(ROOT))
sys.path.insert(0, str(ROOT / "leggio"))
sys.dont_write_bytecode = True       # do not leave .pyc files inside leggio/
from leggio import export_data as _lx  # noqa: E402  (read-only helpers)
from leggio import store as _ls        # noqa: E402

WORKSPACE = ROOT / "workspace"
STATUS_LABELS = dict(_ls.STATUS_LABELS)
STATUSES = list(_ls.STATUSES)
_lock = threading.Lock()
_page_cache: dict[tuple, dict] = {}     # (cid, pid) -> {"key": mtimes, "meta":…, "rows":…, "lines":…}


def _mt(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def collections() -> list[dict]:
    out = []
    for d in sorted(WORKSPACE.iterdir()) if WORKSPACE.exists() else []:
        if (d / "pages").is_dir():
            c = {}
            try:
                c = json.loads((d / "collection.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
            out.append({"id": d.name, "title": c.get("title") or d.name})
    return out


def conventions(cid: str) -> dict:
    try:
        return json.loads((WORKSPACE / cid / "conventions.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _load(cid: str, pid: str) -> dict:
    pf = WORKSPACE / cid / "pages" / f"{pid}.json"
    rf = WORKSPACE / cid / "reading" / f"{pid}.json"
    key = (_mt(pf), _mt(rf))
    with _lock:
        hit = _page_cache.get((cid, pid))
        if hit and hit["key"] == key:
            return hit
    page = json.loads(pf.read_text(encoding="utf-8"))
    _, rows = _lx.page_rows(cid, pid)
    geo = {l["id"]: l.get("polygon") for l in page.get("lines", []) if l.get("polygon")}
    entry = {"key": key, "rows": rows, "geo": geo,
             "meta": {"id": pid, "order": page.get("order", 0), "folio": page.get("folio", ""),
                      "status": page.get("status", "new"), "image": page.get("image", ""),
                      "width": page.get("width"), "height": page.get("height"), "updated": page.get("updated", "")}}
    with _lock:
        _page_cache[(cid, pid)] = entry
    return entry


_meta_cache: dict[tuple, dict] = {}


def pages(cid: str) -> list[dict]:
    """Page summaries in Leggio's order (order, id); status read from each page file (cached by mtime)."""
    d = WORKSPACE / cid / "pages"
    out = []
    for f in d.glob("*.json"):
        k = (cid, f.stem); mt = _mt(f)
        m = _meta_cache.get(k)
        if not m or m["mt"] != mt:
            try:
                p = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            m = {"mt": mt, "id": f.stem, "order": p.get("order", 0), "folio": p.get("folio", ""),
                 "status": p.get("status", "new"), "image": p.get("image", ""), "lines": len(p.get("lines", []))}
            _meta_cache[k] = m
        out.append({k2: v for k2, v in m.items() if k2 != "mt"})
    out.sort(key=lambda x: (x["order"], x["id"]))
    return out


def page(cid: str, pid: str) -> dict:
    return _load(cid, pid)


def image_path(meta: dict) -> Path:
    return ROOT / meta["image"]
