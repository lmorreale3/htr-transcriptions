"""Networks built from tags and holdings, for the Network and Neighbourhood views and for Gephi.

people(rows, …)  nodes = tagged names (person, place, occupation, institution, goods), sized by how many entries name them;
                 edges = named in the same entry (or line), weighted by the number of entries; plus explicit links from
                 tag details (occupation "of" a person, place of origin "of" a person, relation "wife of …").
holdings(hs)     nodes = holdings, owners, former owners, occupants, neighbours, named streets, locations;
                 edges = owns, formerly owned, occupies (contract), borders (side n), appurtenant to.
books(rows)      nodes = pages of this book and the books/folios they refer to; edges = cross-references.
neighbourhood(hs, place)  holdings of one location with their four sides, for the boundary map.
"""
from __future__ import annotations

import csv
import io
import itertools
import re
import zipfile

from . import holdings as hmod

SKIP_GENERIC = {"via", "altri confini", "strada", "chiasso", "via overo strada"}


def _nid(typ, name):
    return f"{typ}:{name}"


def people(rows: list[dict], types=None, scope="entry", min_weight=1, approved_only=False) -> dict:
    types = set(types or ["person", "place", "occupation", "institution", "goods"])
    groups = {}
    for r in rows:
        g = r.get("entry") if scope == "entry" and r.get("entry") else r["key"]
        groups.setdefault(g, []).append(r)
    nodes, edges = {}, {}
    explicit = {}
    for g, rs in groups.items():
        ents = {}
        for r in rs:
            for t in r.get("tags", []):
                if t["type"] not in types or (approved_only and t["status"] != "approved"):
                    continue
                nid = _nid(t["type"], t["canon"])
                n = nodes.setdefault(nid, {"id": nid, "label": t["canon"], "type": t["type"], "count": 0, "entries": set(),
                                           "roles": {}, "pages": set()})
                n["entries"].add(g); n["pages"].add(r["page"])
                role = (t.get("attrs") or {}).get("role")
                if role:
                    n["roles"][role] = n["roles"].get(role, 0) + 1
                ents[nid] = t
                of = (t.get("attrs") or {}).get("of")
                if of and t["type"] in ("occupation", "place"):
                    rel = "occupation" if t["type"] == "occupation" else ((t.get("attrs") or {}).get("relation") or "place")
                    explicit[(_nid("person", of), nid)] = rel
        for a, b in itertools.combinations(sorted(ents), 2):
            e = edges.setdefault((a, b), {"source": a, "target": b, "weight": 0, "kind": "same entry" if scope == "entry" else "same line"})
            e["weight"] += 1
    for (a, b), rel in explicit.items():
        if a in nodes and b in nodes:
            k = tuple(sorted((a, b)))
            e = edges.setdefault(k, {"source": k[0], "target": k[1], "weight": 0, "kind": rel})
            e["kind"] = rel; e["weight"] = max(e["weight"], 1)
    for n in nodes.values():
        n["count"] = len(n["entries"]); n["pages"] = sorted(n["pages"]); n.pop("entries")
    es = [e for e in edges.values() if e["weight"] >= min_weight or e["kind"] not in ("same entry", "same line")]
    used = {e["source"] for e in es} | {e["target"] for e in es}
    return {"nodes": list(nodes.values()), "edges": es, "isolated": sum(1 for n in nodes if n not in used)}


def holdings(hs: list[dict], include_neighbours=True) -> dict:
    nodes, edges = {}, []

    def node(nid, label, typ, **kw):
        n = nodes.setdefault(nid, {"id": nid, "label": label, "type": typ, "count": 0, **kw})
        n["count"] += 1
        return nid

    for h in hs:
        hid = node(f"holding:{h['manuscript']}:{h['id']}", f"{h.get('kind') or 'holding'} ({h['id']})", "holding",
                   place=hmod.place_key(h), holding=h["id"], manuscript=h["manuscript"], status=h.get("status"))
        loc = hmod.place_key(h)
        if loc != "(no location)":
            edges.append({"source": hid, "target": node(f"location:{loc}", loc, "location"), "kind": "located in", "weight": 1})
        o = h.get("owner") or {}
        if o.get("canon"):
            edges.append({"source": node(_nid("person", o["canon"]), o["canon"], "person"), "target": hid,
                          "kind": "owns" + (f" ({o['relation']})" if o.get("relation") else ""), "weight": 2})
        for f in h.get("former_owners") or []:
            if f.get("canon"):
                edges.append({"source": node(_nid("person", f["canon"]), f["canon"], "person"), "target": hid,
                              "kind": f.get("how") or "formerly owned", "weight": 1})
        for oc in h.get("occupants") or []:
            if oc.get("canon"):
                edges.append({"source": node(_nid("person", oc["canon"]), oc["canon"], "person"), "target": hid,
                              "kind": f"occupies ({oc.get('contract') or '?'})", "weight": 1, "rent": oc.get("rent") or ""})
        if include_neighbours:
            for c in h.get("confini") or []:
                nm = c.get("canon") or c.get("name")
                if not nm or nm.lower() in SKIP_GENERIC or c.get("type") == "other":
                    continue
                typ = {"street": "street", "institution": "institution", "holding": "holding-ref"}.get(c.get("type"), "person")
                if typ == "holding-ref":
                    continue
                edges.append({"source": hid, "target": node(_nid(typ, nm), nm, typ), "kind": f"borders (side {c.get('side') or '?'})", "weight": 1})
        for rl in h.get("related") or []:
            edges.append({"source": hid, "target": f"holding:{h['manuscript']}:{rl.get('id')}", "kind": rl.get("relation") or "related", "weight": 1})
    edges = [e for e in edges if e["target"] in nodes and e["source"] in nodes]
    return {"nodes": list(nodes.values()), "edges": edges}


def books(rows: list[dict]) -> dict:
    nodes, edges = {}, {}
    for r in rows:
        for x in r.get("refs") or []:
            src = f"page:{r['manuscript']}:{r['page']}"
            nodes.setdefault(src, {"id": src, "label": r["page"].split("_")[0], "type": "page", "count": 0})["count"] += 1
            book = x.get("book_resolved") or "(this book)"
            for f in x["folios"]:
                tgt = f"folio:{book}:{f}"
                nodes.setdefault(tgt, {"id": tgt, "label": f"{book} c. {f}", "type": "folio", "book": book, "count": 0})["count"] += 1
                e = edges.setdefault((src, tgt), {"source": src, "target": tgt, "weight": 0, "kind": "refers to"})
                e["weight"] += 1
    return {"nodes": list(nodes.values()), "edges": list(edges.values())}


def neighbourhood(hs: list[dict]) -> dict:
    """Holdings with their sides, and links between holdings that share a named neighbour or name each other's owner."""
    out = []
    for h in hs:
        sides = {}
        for c in h.get("confini") or []:
            sides.setdefault(str(c.get("side") or "other"), []).append(
                {"name": c.get("canon") or c.get("name"), "type": c.get("type"), "as_written": c.get("as_written", ""), "note": c.get("note", "")})
        out.append({"id": h["id"], "manuscript": h["manuscript"], "kind": h.get("kind"), "as_written": h.get("as_written"),
                    "place": hmod.place_key(h), "location": h.get("location") or {}, "owner": (h.get("owner") or {}).get("canon"),
                    "owner_relation": (h.get("owner") or {}).get("relation"),
                    "occupants": [{"name": o.get("canon"), "contract": o.get("contract"), "rent": o.get("rent"), "from": o.get("from")} for o in h.get("occupants") or []],
                    "former_owners": [f.get("canon") for f in h.get("former_owners") or []],
                    "sides": sides, "status": h.get("status"), "page": h.get("page"), "size": h.get("size"),
                    "related": h.get("related") or [],
                    "timeline": [{k: p.get(k) for k in ("role", "relation", "contract", "rent", "from", "from_basis", "to", "to_basis", "evidence", "note")}
                                 | {"name": p.get("canon") or p.get("name")} for p in h.get("timeline") or []]})
    links = []
    for a, b in itertools.combinations(out, 2):
        na = {(c["name"], c["type"]) for cs in a["sides"].values() for c in cs if c["type"] in ("person", "institution", "street") and c["name"] and c["name"].lower() not in SKIP_GENERIC}
        nb = {(c["name"], c["type"]) for cs in b["sides"].values() for c in cs if c["type"] in ("person", "institution", "street") and c["name"] and c["name"].lower() not in SKIP_GENERIC}
        shared = sorted(n for n, _ in na & nb)
        names_owner_b = any(n == b["owner"] for n, _ in na)
        names_owner_a = any(n == a["owner"] for n, _ in nb)
        rel = [r for r in a["related"] if r.get("id") == b["id"]] + [r for r in b["related"] if r.get("id") == a["id"]]
        if shared or rel:
            links.append({"a": a["id"], "b": b["id"], "shared": shared, "related": [r.get("relation") for r in rel],
                          "owner_named": names_owner_a or names_owner_b})
    return {"holdings": out, "links": links}


def to_gephi_zip(g: dict) -> bytes:
    """nodes.csv (Id, Label, Type, Count …) + edges.csv (Source, Target, Type=Undirected, Weight, Kind) for Gephi."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        s = io.StringIO(); w = csv.writer(s)
        extra = sorted({k for n in g["nodes"] for k in n if k not in ("id", "label", "type", "count") and not isinstance(n[k], (dict, list))})
        w.writerow(["Id", "Label", "Type", "Count"] + extra)
        for n in g["nodes"]:
            w.writerow([n["id"], n["label"], n["type"], n.get("count", 0)] + [n.get(k, "") for k in extra])
        z.writestr("nodes.csv", "﻿" + s.getvalue())
        s = io.StringIO(); w = csv.writer(s)
        w.writerow(["Source", "Target", "Type", "Weight", "Kind"])
        for e in g["edges"]:
            w.writerow([e["source"], e["target"], "Undirected", e.get("weight", 1), e.get("kind", "")])
        z.writestr("edges.csv", "﻿" + s.getvalue())
        z.writestr("README.txt", "Gephi: File > Import spreadsheet > nodes.csv (Nodes table), then edges.csv (Edges table), append to existing workspace.\n")
    return buf.getvalue()
