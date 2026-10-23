"""Conti web app. Run with:  uv run conti   (then open http://127.0.0.1:8771). Leggio can run at the same time."""
from __future__ import annotations

import io
import os
import webbrowser
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from urllib.parse import quote
from fastapi.staticfiles import StaticFiles
from PIL import Image

from . import __version__, analyze, ask, data, datasets, extract, holdings, money, network, query, source, tags
from . import places as gaz

STATIC = os.path.join(os.path.dirname(__file__), "static")
app = FastAPI(title="Conti")


def _cid(cid: str) -> str:
    if cid not in {c["id"] for c in source.collections()}:
        raise HTTPException(404, "no such manuscript")
    return cid


def _statuses(s: str | None, cid: str):
    return [x for x in s.split(",") if x] if s else data.settings(cid)["statuses"]


@app.get("/api/status")
def status():
    return {"version": __version__, "root": str(source.ROOT), "statuses": source.STATUSES,
            "labels": source.STATUS_LABELS}


@app.get("/api/collections")
def collections():
    out = []
    for c in source.collections():
        counts = {}
        for p in source.pages(c["id"]):
            counts[p["status"]] = counts.get(p["status"], 0) + 1
        out.append({**c, "counts": counts})
    return out


@app.get("/api/settings/{cid}")
def get_settings(cid: str):
    return data.settings(_cid(cid))


@app.put("/api/settings/{cid}")
def put_settings(cid: str, body: dict):
    if body.get("date_style") not in (None, "florentine", "pisan", "modern"):
        raise HTTPException(400, "date_style must be florentine, pisan or modern")
    return data.save_settings(_cid(cid), body)


@app.get("/api/records/{cid}")
def records(cid: str, statuses: str | None = None):
    recs = extract.records(_cid(cid), _statuses(statuses, cid))
    return {"summary": extract.summary(recs), "records": recs, "settings": data.settings(cid)}


@app.get("/api/parse")
def parse(text: str, cid: str | None = None):
    pound = data.settings(cid)["pound"] if cid else "℔"
    return money.parse(text).as_dict(pound)


@app.post("/api/review/{cid}")
def review(cid: str, body: dict):
    """body: {key, written, decision: ok|corrected|not_sum|clear, text?}"""
    _cid(cid)
    key, dec = body.get("key"), body.get("decision")
    if not key or dec not in ("ok", "corrected", "not_sum", "clear"):
        raise HTTPException(400, "key and decision (ok, corrected, not_sum, clear) are required")
    if dec == "clear":
        data.set_review(cid, key, None)
        return {"key": key, "review": None}
    entry = {"written": body.get("written", ""), "decision": dec}
    if dec == "corrected":
        t = (body.get("text") or "").strip()
        a = money.parse(t)
        if a.empty:
            raise HTTPException(400, "the corrected sum has no figure")
        entry["text"] = t
        entry["value"] = a.as_dict(data.settings(cid)["pound"])
    data.set_review(cid, key, entry)
    return {"key": key, "review": {**entry, "state": "confirmed"}}


@lru_cache(maxsize=512)
def _crop(cid: str, pid: str, ids: str, key) -> bytes:
    pg = source.page(cid, pid)
    polys = [pg["geo"][i] for i in ids.split(",") if i in pg["geo"]]
    if not polys:
        raise HTTPException(404, "no outline for these lines")
    xs = [p[0] for poly in polys for p in poly]; ys = [p[1] for poly in polys for p in poly]
    pad = 6
    if not source.image_path(pg["meta"]).exists():
        raise HTTPException(404, "page image not found")
    with Image.open(source.image_path(pg["meta"])) as im:
        W, H = im.size
        sx = W / (pg["meta"].get("width") or W); sy = H / (pg["meta"].get("height") or H)
        box = (max(0, int(min(xs) * sx) - pad), max(0, int(min(ys) * sy) - pad),
               min(W, int(max(xs) * sx) + pad), min(H, int(max(ys) * sy) + pad))
        c = im.crop(box).convert("RGB")
    if c.width > 1100:
        c = c.resize((1100, max(1, int(c.height * 1100 / c.width))))
    buf = io.BytesIO()
    c.save(buf, "JPEG", quality=82)
    return buf.getvalue()


@app.get("/api/crop/{cid}/{pid}")
def crop(cid: str, pid: str, ids: str):
    pg = source.page(_cid(cid), pid)
    return Response(_crop(cid, pid, ids, pg["key"]), media_type="image/jpeg",
                    headers={"Cache-Control": "max-age=300"})


# ---------------------------------------------------------------- tags
@app.get("/api/tags/{cid}/{pid}")
def page_tags(cid: str, pid: str, statuses: str | None = None):
    """The page's lines with their tags (all statuses, rejected included, for review)."""
    _cid(cid)
    pg = source.page(cid, pid)
    allt = tags.load(cid); al = tags.aliases()
    rows = []
    for r in pg["rows"]:
        key = f"{pid}|{r['line_ids']}"
        ent = allt.get(key) or {}
        ts = []
        for t in ent.get("tags", []):
            x = dict(t); x["canon"] = tags.canonical(t["type"], t["name"], al)
            x["stale"] = bool(t.get("span")) and t["span"] not in (r["text"] or "")
            ts.append(x)
        rows.append({"key": key, "line": r["line"], "text": r["text"], "translation": r["translation"],
                     "line_ids": r["line_ids"], "tags": ts, "text_changed": bool(ent) and ent.get("written") != r["text"]})
    pages = [p for p in source.pages(cid)]
    tagged = {k.split("|")[0] for k in allt}
    return {"page": pg["meta"], "rows": rows,
            "pages": [{"id": p["id"], "status": p["status"], "tagged": p["id"] in tagged} for p in pages]}


@app.get("/api/tagpages/{cid}")
def tag_pages(cid: str):
    """Pages with tags, and how many are still suggestions."""
    _cid(cid)
    out = {}
    for k, ent in tags.load(cid).items():
        pid = k.split("|")[0]
        o = out.setdefault(pid, {"id": pid, "tags": 0, "suggested": 0})
        for t in ent.get("tags", []):
            if t["status"] != "rejected":
                o["tags"] += 1
            if t["status"] == "suggested":
                o["suggested"] += 1
    order = {p["id"]: i for i, p in enumerate(source.pages(cid))}
    return sorted(out.values(), key=lambda o: order.get(o["id"], 0))


@app.post("/api/tags/{cid}")
def tag_op(cid: str, body: dict):
    """body: {key, written, action, id?, tag?}  or  {action: approve_page, keys: [...]}"""
    _cid(cid)
    try:
        if body.get("action") == "approve_page":
            return {"approved": tags.approve_page(cid, body.get("keys") or [])}
        return tags.update(cid, body["key"], body.get("written", ""), body)
    except (ValueError, KeyError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/names")
def names(type: str | None = None):
    """Every tagged name in all manuscripts (canonical), with counts and variants: for suggestions and merging."""
    al = tags.aliases(); out = {}
    for c in source.collections():
        for k, ent in tags.load(c["id"]).items():
            for t in ent.get("tags", []):
                if t["status"] == "rejected" or (type and t["type"] != type):
                    continue
                cn = tags.canonical(t["type"], t["name"], al)
                o = out.setdefault((t["type"], cn), {"type": t["type"], "name": cn, "count": 0, "variants": {}, "approved": 0})
                o["count"] += 1; o["approved"] += t["status"] == "approved"
                o["variants"][t["name"]] = o["variants"].get(t["name"], 0) + 1
    return sorted(out.values(), key=lambda o: (o["type"], -o["count"], o["name"]))


@app.post("/api/names/merge")
def names_merge(body: dict):
    if body.get("type") not in tags.TYPES or not body.get("into"):
        raise HTTPException(400, "type and into are required")
    if body.get("unmerge"):
        return tags.unmerge(body["type"], body["into"])
    return tags.merge(body["type"], body.get("names") or [], body["into"])


# ---------------------------------------------------------------- queries & datasets
@app.post("/api/query")
def run_query(body: dict):
    q = body.get("query") or body
    try:
        res = query.run(q)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(400, f"query: {e}")
    gb = body.get("group_by")
    if gb:
        res["groups"] = query.group(res["rows"], gb, res["unit"])
    lim = int(body.get("limit") or 300)
    res["truncated"] = len(res["rows"]) > lim
    res["rows"] = res["rows"][:lim]
    res["describe"] = query.describe(q)
    return res


def _export(rows, unit, fmt, title, about, group_by=None):
    if fmt == "csv":
        content, mt, ext = query.to_csv(rows, unit), "text/csv", "csv"
    else:
        groups = {g: query.group(rows, g, unit) for g in (group_by or [])}
        content = query.to_xlsx(rows, unit, about, groups)
        mt, ext = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
    name = f"{title}_{data.now()[:10]}.{ext}"
    exp = data.DATA / "_exports"; exp.mkdir(parents=True, exist_ok=True)
    (exp / name).write_bytes(content)
    return Response(content, media_type=mt, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


@app.post("/api/query/export")
def export_query(body: dict):
    q = body.get("query") or {}
    res = query.run(q)
    about = [("Query", query.describe(q)), ("Rows", str(len(res["rows"]))), ("Exported", data.now() + " from Conti"),
             ("Note", "Tags marked 'suggested' were made by Claude and not yet checked. Dates: modern = year beginning 1 January.")]
    gb = [body["group_by"]] if body.get("group_by") else []
    return _export(res["rows"], res["unit"], body.get("format", "xlsx"), "conti_query", about, gb)


@app.get("/api/datasets")
def list_datasets():
    return datasets.all_()


@app.get("/api/datasets/{did}")
def get_dataset(did: str, group_by: str | None = None, limit: int = 300):
    d = datasets.get(did)
    if not d:
        raise HTTPException(404, "no such dataset")
    rows = datasets.rows(d)
    unit = (d.get("query") or {}).get("unit", "lines")
    out = {**{k: v for k, v in d.items() if k != "snapshot"}, "describe": query.describe(d.get("query") or {}),
           "count": len(rows), "rows": rows[:limit], "truncated": len(rows) > limit, "unit": unit,
           "snapshot_t": (d.get("snapshot") or {}).get("t")}
    if group_by:
        out["groups"] = query.group(rows, group_by, unit)
    return out


@app.post("/api/datasets")
def save_dataset(body: dict):
    if not (body.get("name") or body.get("id")):
        raise HTTPException(400, "a dataset needs a name")
    return datasets.save(body)


@app.delete("/api/datasets/{did}")
def delete_dataset(did: str):
    datasets.delete(did)
    return {"deleted": did}


@app.get("/api/datasets/{did}/export")
def export_dataset(did: str, format: str = "xlsx"):
    d = datasets.get(did)
    if not d:
        raise HTTPException(404, "no such dataset")
    rows = datasets.rows(d); unit = (d.get("query") or {}).get("unit", "lines")
    about = [("Dataset", d.get("name", "")), ("Description", d.get("description", "")),
             ("Kind", "live (re-run on export)" if d.get("mode") != "snapshot" else f"snapshot of {(d.get('snapshot') or {}).get('t')}"),
             ("Query", query.describe(d.get("query") or {})), ("Rows", str(len(rows))), ("Exported", data.now() + " from Conti")]
    gb = [g for g in ("person", "place", "occupation") if unit != "tags"] or ["person", "place", "occupation"]
    return _export(rows, unit, format, d["id"], about, gb)


# ---------------------------------------------------------------- holdings
@app.get("/api/holdings/{cid}")
def list_holdings(cid: str, page: str | None = None):
    _cid(cid)
    hs = list(holdings.load(cid).values())
    order = {p["id"]: i for i, p in enumerate(source.pages(cid))}
    hs.sort(key=lambda h: (order.get(h.get("page"), 0), int((h["id"].split("-h") + ["0"])[1]) if h["id"].split("-h")[-1].isdigit() else 0))
    pages = {}
    for h in hs:
        o = pages.setdefault(h.get("page"), {"id": h.get("page"), "holdings": 0, "suggested": 0})
        o["holdings"] += 1; o["suggested"] += h.get("status") == "suggested"
    out = {"pages": sorted(pages.values(), key=lambda o: order.get(o["id"], 0)), "holdings": [h for h in hs if not page or h.get("page") == page]}
    if page:
        pg = source.page(cid, page)
        out["lines"] = [{"key": f"{page}|{r['line_ids']}", "line": r["line"], "text": r["text"], "translation": r["translation"]} for r in pg["rows"]]
    return out


@app.post("/api/holdings/{cid}")
def holding_op(cid: str, body: dict):
    _cid(cid)
    try:
        return holdings.update(cid, body.get("id", ""), body)
    except ValueError as e:
        raise HTTPException(400, str(e))


def _holdings_for(mss, place=None, statuses=("suggested", "approved"), approved_only=False):
    hs = []
    for cid in mss or [c["id"] for c in source.collections()]:
        hs += holdings.canon_all(cid, ("approved",) if approved_only else statuses)
    if place:
        hs = [h for h in hs if holdings.place_key(h) == place or holdings.place_key(h).startswith(place + " › ")]
    return hs


@app.post("/api/places")
def places(body: dict):
    hs = _holdings_for(body.get("manuscripts"))
    counts = {}
    for h in hs:
        parts = holdings.place_key(h).split(" › ")
        for i in range(1, len(parts) + 1):
            k = " › ".join(parts[:i]); counts[k] = counts.get(k, 0) + 1
    return sorted(({"place": k, "holdings": v, "depth": k.count(" › ")} for k, v in counts.items()), key=lambda x: x["place"])


@app.post("/api/neighbourhood")
def neighbourhood(body: dict):
    return network.neighbourhood(_holdings_for(body.get("manuscripts"), body.get("place"), approved_only=bool(body.get("approved_only"))))


# ---------------------------------------------------------------- map: holdings anchored to places
@app.get("/api/gazetteer")
def gazetteer():
    ps = gaz.load(); ix = gaz.index(ps)
    use = {}
    for c in source.collections():
        for h in holdings.canon_all(c["id"]):
            loc = h.get("location") or {}
            for lvl in gaz.ORDER:
                v = loc.get(lvl)
                if v:
                    p = ix.get(gaz._norm(v))
                    k = p["name"] if p else f"(not in gazetteer) {v}"
                    use.setdefault(k, set()).add(h["id"])
    return {"places": ps, "used": {k: sorted(v) for k, v in use.items()}}


@app.post("/api/gazetteer")
def gazetteer_op(body: dict):
    try:
        return gaz.update(body)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/map")
def map_data(body: dict):
    hs = _holdings_for(body.get("manuscripts"), approved_only=bool(body.get("approved_only")))
    ix = gaz.index()
    nb = network.neighbourhood(hs)
    anchored, loose = [], []
    byid = {(h["manuscript"], h["id"]): h for h in hs}
    for x in nb["holdings"]:
        a = gaz.anchor(byid[(x["manuscript"], x["id"])], ix)
        x["anchor"] = a
        (anchored if a else loose).append(x)
    groups = {}
    for x in anchored:
        g = groups.setdefault(x["anchor"]["place"], {**{k: x["anchor"][k] for k in ("place", "kind", "lat", "lon", "confidence", "status")}, "holdings": []})
        g["holdings"].append(x["id"])
    return {"holdings": anchored + loose, "anchors": list(groups.values()), "links": nb["links"],
            "unanchored": [{"id": x["id"], "place": x["place"]} for x in loose]}


# ---------------------------------------------------------------- networks
def _graph(body):
    kind = body.get("kind", "people")
    if kind == "holdings":
        return network.holdings(_holdings_for(body.get("manuscripts"), body.get("place"), approved_only=bool(body.get("approved_only"))),
                                include_neighbours=body.get("neighbours", True))
    q = dict(body.get("query") or {})
    if body.get("dataset"):
        d = datasets.get(body["dataset"])
        if not d:
            raise HTTPException(404, "no such dataset")
        q = dict(d.get("query") or {})
    q["unit"] = "lines"
    rows = query.run(q)["rows"]
    if kind == "books":
        return network.books(rows)
    return network.people(rows, body.get("types"), body.get("scope", "entry"), int(body.get("min_weight") or 1),
                          bool(q.get("approved_only")))


@app.post("/api/network")
def get_network(body: dict):
    try:
        return _graph(body)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/network/export")
def export_network(body: dict):
    content = network.to_gephi_zip(_graph(body))
    name = f"conti_network_{body.get('kind', 'people')}_{data.now()[:10]}.zip"
    return Response(content, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


# ---------------------------------------------------------------- Ask: plain-language questions
@app.get("/api/ask")
def ask_list():
    return {"questions": ask.all_(), "examples": ask.EXAMPLES}


@app.get("/api/ask/claude")
def ask_claude():
    return ask.claude_status()


@app.post("/api/ask")
def ask_new(body: dict):
    try:
        rec = ask.new(body.get("question", ""), "chat" if body.get("mode") == "chat" else "claude-code")
    except ValueError as e:
        raise HTTPException(400, str(e))
    if rec["status"] != "waiting":
        rec = ask.start(rec["id"])
    return rec


def _q(qid):
    rec = ask.get(qid)
    if not rec:
        raise HTTPException(404, "no such question")
    return rec


@app.get("/api/ask/{qid}")
def ask_get(qid: str):
    return _q(qid)


@app.post("/api/ask/{qid}/start")
def ask_start(qid: str):
    _q(qid)
    return ask.start(qid)


@app.post("/api/ask/{qid}/rerun")
def ask_rerun(qid: str):
    _q(qid)
    try:
        return ask.rerun(qid)
    except (ValueError, analyze.PlanError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/ask/{qid}/chat")
def ask_to_chat(qid: str):
    rec = _q(qid); rec["status"] = "waiting"; rec["source"] = "chat"
    return ask.save(rec)


@app.delete("/api/ask/{qid}")
def ask_delete(qid: str):
    ask.delete(qid)
    return {"deleted": qid}


@app.get("/api/ask/{qid}/export")
def ask_export(qid: str):
    rec = _q(qid)
    if not rec.get("result"):
        raise HTTPException(400, "no results yet")
    content = analyze.to_xlsx(rec)
    name = f"conti_ask_{qid}.xlsx"
    exp = data.DATA / "_exports"; exp.mkdir(parents=True, exist_ok=True)
    (exp / name).write_bytes(content)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


@app.get("/api/ask/{qid}/gephi")
def ask_gephi(qid: str, step: str):
    rec = _q(qid)
    s = ((rec.get("result") or {}).get("steps") or {}).get(step)
    if not s or s.get("type") != "network":
        raise HTTPException(404, "no network step with that id")
    name = f"conti_ask_{qid}_{step}.zip"
    return Response(analyze.gephi_zip(s), media_type="application/zip",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


@app.post("/api/ask/{qid}/dataset")
def ask_dataset(qid: str, body: dict):
    """Save a query step of the answer as a Conti dataset (live = grows with the edition)."""
    rec = _q(qid)
    s = ((rec.get("result") or {}).get("steps") or {}).get(body.get("step"))
    if not s or s.get("type") != "query":
        raise HTTPException(400, "only query steps can become datasets")
    return datasets.save({"name": body.get("name") or f"{rec.get('title') or rec['question'][:40]} ({body['step']})",
                          "description": f"From the question: {rec['question']}", "query": s["query"],
                          "mode": body.get("mode") or "live"})


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"), headers={"Cache-Control": "no-cache"})


app.mount("/static", StaticFiles(directory=STATIC), name="static")


def main():
    import uvicorn
    port = int(os.environ.get("CONTI_PORT", "8771"))
    print(f"\n  Conti is running at http://127.0.0.1:{port}\n  Project folder: {source.ROOT}\n"
          f"  (Reads Leggio's workspace; never changes it. Press Ctrl+C to stop.)\n")
    if not os.environ.get("CONTI_NO_BROWSER"):
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:  # noqa: BLE001
            pass
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
