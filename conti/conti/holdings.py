"""Holdings: properties described in the text (casa, podere, pezzo di terra, bottega …) with owner, former owners,
occupants (tenants, sharecroppers), location (popolo, luogo detto, via) and confini (boundaries, sides 1º–4º as listed),
and a timeline: [{role owner|occupant, name, relation, contract, rent, from, from_basis, to, to_basis, evidence, note}]
(modern dates YYYY[-MM[-DD]]; basis stated | inferred | unknown | open) — who owned and who held it, when.

Stored per manuscript in conti_data/<collection>/holdings.json: {"<holding id>": holding}
holding = {id, page, lines[], kind, as_written, location{comune, castello, popolo, luogo, via, near, city}, size,
           owner{name, relation, basis}, former_owners[{name, how}], occupants[{name, occupation, contract, rent, from, as_written}],
           confini[{side, name, type: street|person|institution|holding|other, as_written, note?}], related[{id, relation}],
           note, uncertain, status: suggested|approved|rejected, source: claude|laura, t, written{line key: text}}
Names of people/institutions go through the same merge table as tags (conti_data/_names.json, type "person"/"institution").
The sides 1º–4º are the ORDER in which the scribe listed the confini (usually starting from the street), not compass points.
"""
from __future__ import annotations

from . import data, tags as tagmod

EDITABLE = ("kind", "as_written", "location", "size", "owner", "former_owners", "occupants", "confini", "related", "note",
            "uncertain", "lines", "timeline")


def load(cid: str) -> dict:
    return data.read(cid, "holdings.json", {})


def save(cid: str, h: dict) -> None:
    data.write(cid, "holdings.json", h)


def import_claude(cid: str, payload: dict, written: dict) -> int:
    allh = load(cid); n = 0; now = data.now()
    page = payload.get("page", "")
    for h in payload.get("holdings", []):
        cur = allh.get(h["id"])
        if cur and (cur.get("source") == "laura" or cur.get("status") in ("approved", "rejected") or cur.get("edited_by")):
            continue
        x = {k: h.get(k) for k in EDITABLE if k in h}
        x.update({"id": h["id"], "page": page, "status": "suggested", "source": "claude", "t": now,
                  "written": {k: written.get(k, "") for k in h.get("lines", [])}})
        allh[h["id"]] = x; n += 1
    save(cid, allh)
    return n


def import_timeline(cid: str, payload: dict) -> int:
    """Claude's timeline suggestions {holding id: [period…]}; holdings Laura has edited keep their own timeline."""
    allh = load(cid); n = 0
    for hid, periods in payload.items():
        h = allh.get(hid)
        if not h or (h.get("edited_by") and h.get("timeline")):
            continue
        h["timeline"] = [dict(p, source="claude") for p in periods]; n += 1
    save(cid, allh)
    return n


def update(cid: str, hid: str, body: dict) -> dict:
    allh = load(cid)
    if body.get("action") == "new":
        page = body.get("page") or ""
        i = 1
        short = page.split("_")[0]
        while f"{short}-h{i}" in allh:
            i += 1
        hid = f"{short}-h{i}"
        allh[hid] = {"id": hid, "page": page, "lines": [], "kind": "casa", "location": {}, "owner": {}, "former_owners": [],
                     "occupants": [], "confini": [], "related": [], "status": "approved", "source": "laura", "t": data.now()}
    h = allh.get(hid)
    if not h:
        raise ValueError("no such holding")
    a = body.get("action")
    if a in ("approve", "reject", "suggest"):
        h["status"] = {"approve": "approved", "reject": "rejected", "suggest": "suggested"}[a]
    elif a == "delete":
        allh.pop(hid); save(cid, allh); return {"deleted": hid}
    elif a in ("edit", "new"):
        for k in EDITABLE:
            if k in (body.get("holding") or {}):
                h[k] = body["holding"][k]
        if a == "edit":
            h["status"] = "approved"; h["edited_by"] = "laura"
    else:
        raise ValueError("unknown action")
    h["t"] = data.now()
    save(cid, allh)
    return h


def canon_all(cid: str, statuses=("suggested", "approved")) -> list[dict]:
    """Holdings with canonical names (merge table applied) — what the views use."""
    al = tagmod.aliases()
    out = []
    for h in load(cid).values():
        if h.get("status") not in statuses:
            continue
        x = dict(h); x["manuscript"] = cid

        def cn(name, typ="person"):
            return tagmod.canonical(typ, name, al) if name else name
        x["owner"] = dict(h.get("owner") or {}); x["owner"]["canon"] = cn(x["owner"].get("name"))
        x["former_owners"] = [dict(f, canon=cn(f.get("name"))) for f in h.get("former_owners") or []]
        x["occupants"] = [dict(o, canon=cn(o.get("name"))) for o in h.get("occupants") or []]
        x["timeline"] = [dict(p, canon=cn(p.get("name"))) for p in h.get("timeline") or []]
        x["confini"] = [dict(c, canon=cn(c.get("name"), "institution" if c.get("type") == "institution" else "person")
                        if c.get("type") in ("person", "institution") else c.get("name")) for c in h.get("confini") or []]
        out.append(x)
    return out


def place_key(h: dict) -> str:
    loc = h.get("location") or {}
    parts = [loc.get("castello") or loc.get("comune") or "", loc.get("popolo") or "", loc.get("luogo") or loc.get("via") or ""]
    return " › ".join(p for p in parts if p) or "(no location)"
