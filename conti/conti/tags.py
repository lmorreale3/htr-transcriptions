"""Tags: people, places, occupations, institutions, goods named in a line.

Stored per manuscript in conti_data/<collection>/tags.json:
  {"<line key>": {"written": "<line text when tagged>", "tags": [tag, …]}}
  tag = {id, type, span, name, attrs{…}, status: suggested|approved|rejected, source: claude|laura, t, note?}
  span  = the words exactly as written in the line; name = the normalized form records are grouped by.
Names are merged across ALL manuscripts through conti_data/_names.json: {type: {variant name: canonical name}}.
Merging never rewrites the tags, so it can be undone (unmerge removes the alias).
If a line's text has changed in Leggio since it was tagged, tags whose span is no longer in the text are "stale".
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from . import data

TYPES = ["person", "place", "occupation", "institution", "goods"]
TYPE_LABELS = {"person": "People", "place": "Places", "occupation": "Occupations & roles",
               "institution": "Institutions", "goods": "Goods"}


def load(cid: str) -> dict:
    return data.read(cid, "tags.json", {})


def save(cid: str, t: dict) -> None:
    data.write(cid, "tags.json", t)


def aliases() -> dict:
    try:
        return json.loads((data.DATA / "_names.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_aliases(a: dict) -> None:
    data.write_root("_names.json", a)


def canonical(typ: str, name: str, al: dict | None = None) -> str:
    al = aliases() if al is None else al
    m = al.get(typ, {})
    seen = set()
    while name in m and name not in seen:      # follow chains (a → b → c)
        seen.add(name); name = m[name]
    return name


def for_line(entry: dict | None, text: str, al: dict) -> list[dict]:
    """Tags of one line, with canonical names and a stale flag; rejected tags are left out."""
    if not entry:
        return []
    out = []
    for t in entry.get("tags", []):
        if t.get("status") == "rejected":
            continue
        x = dict(t)
        x["canon"] = canonical(t["type"], t["name"], al)
        x["stale"] = bool(t.get("span")) and t["span"] not in (text or "")
        out.append(x)
    return out


def new_id() -> str:
    return "t" + uuid.uuid4().hex[:10]


def import_claude(cid: str, payload: dict, written: dict) -> int:
    """Add Claude's suggestions for a page: payload = {"page", "tags": {key: [tag…]}}; written = {key: text}.
    Lines that already carry tags made or approved by Laura are not touched."""
    allt = load(cid); n = 0; now = data.now()
    for key, tags in payload.get("tags", {}).items():
        cur = allt.get(key)
        if cur and any(t.get("source") == "laura" or t.get("status") in ("approved", "rejected") for t in cur["tags"]):
            continue
        allt[key] = {"written": written.get(key, ""), "tags": [
            {"id": new_id(), "type": t["type"], "span": t.get("span", ""), "name": t["name"],
             "attrs": t.get("attrs") or {}, "status": "suggested", "source": "claude", "t": now} for t in tags
            if t.get("type") in TYPES and t.get("name")]}
        n += len(allt[key]["tags"])
    save(cid, allt)
    return n


def update(cid: str, key: str, written: str, op: dict) -> dict:
    """op: {action: approve|reject|suggest|edit|add|delete|approve_line, id?, tag?{type,span,name,attrs}}"""
    allt = load(cid)
    ent = allt.setdefault(key, {"written": written, "tags": []})
    a = op.get("action"); now = data.now()
    if a == "add":
        t = op.get("tag") or {}
        if t.get("type") not in TYPES or not (t.get("name") or "").strip():
            raise ValueError("a tag needs a type and a name")
        ent["tags"].append({"id": new_id(), "type": t["type"], "span": t.get("span", ""), "name": t["name"].strip(),
                            "attrs": t.get("attrs") or {}, "status": "approved", "source": "laura", "t": now})
        ent["written"] = written
    elif a == "approve_line":
        for t in ent["tags"]:
            if t["status"] == "suggested":
                t["status"] = "approved"; t["t"] = now
    else:
        t = next((x for x in ent["tags"] if x["id"] == op.get("id")), None)
        if not t:
            raise ValueError("no such tag")
        if a == "approve":
            t["status"] = "approved"
        elif a == "reject":
            t["status"] = "rejected"
        elif a == "suggest":
            t["status"] = "suggested"
        elif a == "delete":
            ent["tags"].remove(t)
        elif a == "edit":
            nt = op.get("tag") or {}
            for k in ("type", "span", "name"):
                if nt.get(k) is not None:
                    t[k] = nt[k].strip() if isinstance(nt[k], str) else nt[k]
            if "attrs" in nt:
                t["attrs"] = {k: v for k, v in (nt["attrs"] or {}).items() if v not in ("", None)}
            t["status"] = "approved"; t["edited_by"] = "laura"
        else:
            raise ValueError("unknown action")
        t["t"] = now
    save(cid, allt)
    return ent


def approve_page(cid: str, keys: list[str]) -> int:
    allt = load(cid); n = 0; now = data.now()
    for k in keys:
        for t in (allt.get(k) or {}).get("tags", []):
            if t["status"] == "suggested":
                t["status"] = "approved"; t["t"] = now; n += 1
    save(cid, allt)
    return n


def merge(typ: str, names: list[str], into: str) -> dict:
    al = aliases(); m = al.setdefault(typ, {})
    for n in names:
        if n != into:
            m[n] = into
    m.pop(into, None)
    save_aliases(al)
    return al


def unmerge(typ: str, name: str) -> dict:
    al = aliases(); al.get(typ, {}).pop(name, None); save_aliases(al)
    return al
