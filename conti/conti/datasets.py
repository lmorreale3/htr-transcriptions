"""Saved datasets, shared by all manuscripts: conti_data/_datasets/<id>.json

dataset = {id, name, description, query, mode: "live" | "snapshot", pinned: [row keys], excluded: [row keys],
           created, updated, snapshot: {t, rows} (snapshot mode only)}
live      re-runs the query each time: grows as more pages are finished and tagged ("cumulative")
snapshot  keeps the rows as they were when saved (a fixed set for a paper, a figure …)
pinned    rows added by hand even if the query does not find them; excluded: rows taken out by hand.
"""
from __future__ import annotations

import json
import re

from . import data, query

DIR = data.DATA / "_datasets"


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50] or "dataset"


def all_() -> list[dict]:
    out = []
    for f in sorted(DIR.glob("*.json")) if DIR.exists() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out.append({k: d.get(k) for k in ("id", "name", "description", "mode", "created", "updated")}
                   | {"describe": query.describe(d.get("query") or {}), "unit": (d.get("query") or {}).get("unit", "lines"),
                      "pinned": len(d.get("pinned") or []), "excluded": len(d.get("excluded") or [])})
    return sorted(out, key=lambda d: d.get("updated") or "", reverse=True)


def get(did: str) -> dict | None:
    return data.read("_datasets", f"{did}.json", None)


def save(body: dict) -> dict:
    did = body.get("id")
    cur = get(did) if did else None
    if not cur:
        base = _slug(body.get("name") or "dataset"); did = base; i = 2
        while get(did):
            did = f"{base}-{i}"; i += 1
        cur = {"id": did, "created": data.now(), "pinned": [], "excluded": []}
    for k in ("name", "description", "query", "mode", "pinned", "excluded"):
        if k in body:
            cur[k] = body[k]
    cur["mode"] = cur.get("mode") or "live"
    if cur["mode"] == "snapshot" and (body.get("refresh_snapshot") or "snapshot" not in cur):
        cur["snapshot"] = {"t": data.now(), "rows": _rows_live(cur)}
    if cur["mode"] == "live":
        cur.pop("snapshot", None)
    cur["updated"] = data.now()
    data.write("_datasets", f"{did}.json", cur)
    return cur


def _rows_live(d: dict) -> list[dict]:
    q = d.get("query") or {}
    res = query.run(q)["rows"]
    keys = {r["key"] for r in res}
    pinned = [k for k in d.get("pinned") or [] if k not in keys]
    if pinned:
        allq = {**q, "conditions": []}
        res += [r for r in query.run(allq)["rows"] if r["key"] in set(pinned)]
    ex = set(d.get("excluded") or [])
    return [r for r in res if r["key"] not in ex]


def rows(d: dict) -> list[dict]:
    if d.get("mode") == "snapshot" and d.get("snapshot"):
        return d["snapshot"]["rows"]
    return _rows_live(d)


def delete(did: str) -> None:
    p = DIR / f"{did}.json"
    if p.exists():
        trash = data.DATA / "_datasets_deleted"; trash.mkdir(parents=True, exist_ok=True)
        p.replace(trash / f"{did}_{data.now().replace(':', '')}.json")
