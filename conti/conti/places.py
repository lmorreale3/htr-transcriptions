"""Gazetteer: places that can anchor holdings to Florentine topography (shared by all manuscripts).

conti_data/_places.json = [{name, aliases[], kind, lat, lon, confidence: secure|approximate|uncertain, basis, source,
                            modern_name, note, within, status: suggested|approved, placed_by?}]
secure       an existing church/settlement whose position a source gives
approximate  placed relative to a known place (a lost church on today's piazza, a street's midpoint), or by Laura on the map
uncertain    not located (lat/lon empty): such holdings fall back to a less specific place (popolo → comune → city)

anchor(holding) picks the MOST SPECIFIC located place in the holding's location: via / luogo, then popolo, then
castello / comune, then city.
"""
from __future__ import annotations

import re

from . import data
from .textnorm import plain

ORDER = ("via", "luogo", "popolo", "castello", "comune", "city")


def load() -> list[dict]:
    return data.read_root("_places.json", [])


def save(ps: list[dict]) -> None:
    data.write_root("_places.json", ps)


def _norm(s: str) -> str:
    s = plain(s or "")
    s = re.sub(r"\((?:pieve|popolo|street|barberino)\)", "", s)
    s = re.sub(r"^(?:via di |via |il |la |lo |al |alla |a )", "", s.strip())
    s = s.replace("'", " ").replace("’", " ")
    return re.sub(r"\s+", " ", s).strip()


def index(ps=None) -> dict:
    ix = {}
    for p in ps if ps is not None else load():
        for n in [p["name"], *(p.get("aliases") or [])]:
            ix.setdefault(_norm(n), p)
    return ix


def anchor(h: dict, ix: dict) -> dict | None:
    loc = h.get("location") or {}
    for lvl in ORDER:
        v = loc.get(lvl)
        if not v:
            continue
        p = ix.get(_norm(v))
        if p is None and lvl in ("castello", "comune") and _norm(v) in ("barberino",):
            p = ix.get("barberino")
        if p is not None and p.get("lat") is not None and p.get("lon") is not None:
            return {"place": p["name"], "level": lvl, "kind": p.get("kind"), "lat": p["lat"], "lon": p["lon"],
                    "confidence": p.get("confidence"), "status": p.get("status", "suggested"), "as_written": v}
    return None


def import_list(entries: list[dict]) -> int:
    ps = load(); have = {_norm(p["name"]) for p in ps}; n = 0
    for e in entries:
        if _norm(e["name"]) in have:
            continue
        ps.append({**e, "status": "suggested"}); n += 1
    save(ps)
    return n


def update(body: dict) -> dict:
    ps = load(); name = body.get("name")
    p = next((x for x in ps if x["name"] == name), None)
    a = body.get("action")
    if a == "add":
        if p:
            raise ValueError("a place with this name exists")
        p = {"name": name, "aliases": [], "kind": body.get("kind", "area"), "lat": None, "lon": None,
             "confidence": "uncertain", "status": "approved", "basis": "", "source": ""}
        ps.append(p)
    if not p:
        raise ValueError("no such place")
    if a == "approve":
        p["status"] = "approved"
    elif a == "place":                          # Laura clicked the map
        p["lat"], p["lon"] = round(float(body["lat"]), 6), round(float(body["lon"]), 6)
        p["confidence"] = body.get("confidence") or "approximate"
        p["placed_by"] = "laura"; p["status"] = "approved"
        p["basis"] = (body.get("basis") or "placed on the map by Laura").strip()
    elif a in ("edit", "add"):
        for k in ("aliases", "kind", "lat", "lon", "confidence", "basis", "source", "modern_name", "note", "within"):
            if k in body:
                p[k] = body[k]
        if a == "edit":
            p["status"] = "approved"
    elif a == "delete":
        ps.remove(p); save(ps); return {"deleted": name}
    save(ps)
    return p
