"""One record per line of text, with everything the rules can find in it.

record = the Leggio export row (manuscript, page, line, text, sum, date, expanded, translation, line ids …) plus
  kind        debit / credit / balance / None
  refs        [{folios, book, book_resolved, raw}]
  dates       [{day, month, year_written, year_modern, iso_modern, year_inferred, style, raw}]
  mentions    [{raw, amount}]       every sign+figure in the entry text
  amount      the sum of this entry, parsed (see money.py), with
  amount_written   what was parsed: the Sum column, or the end of the entry line, or both joined
  amount_source    "sum" | "end of entry" | "sum + end of entry"
  review      Laura's decision on the sum, if any, and its state (confirmed / changed since review)
  amount_final     the amount queries use: corrected > confirmed > parsed (None if "not a sum")
"""
from __future__ import annotations

import re

from . import data, dates, money, refs, source, tags as tagmod

_FIELDS = set(money._FIELD)


def _amount_for(row: dict):
    s = (row.get("sum") or "").strip()
    tr = money.trailing(row.get("text") or "")
    sa = money.parse(s) if s else None
    if sa is not None and not sa.empty:
        if tr:
            ta = money.from_tokens(tr[1])
            ranks_t = {money.RANK[k] for k, v in money._FIELD.items() if getattr(ta, v) is not None}
            ranks_s = {money.RANK[k] for k, v in money._FIELD.items() if getattr(sa, v) is not None}
            if ranks_t and ranks_s and max(ranks_t) < min(ranks_s):
                joined = tr[0] + " | " + s
                a = money.parse(joined)
                a.problems.insert(0, ("joined", f"joined with “{tr[0]}” at the end of the entry line"))
                return a, joined, "sum + end of entry"
        return sa, s, "sum"
    if tr:
        a = money.from_tokens(tr[1])
        if s:
            a.problems.insert(0, ("sum-unread", f"Sum column “{s}” has no figure; used the end of the entry"))
        return a, tr[0], "end of entry"
    if s:
        return sa, s, "sum"
    return None, "", ""


_ENTRY_START = re.compile(r"^\s*(?:it(?:em|ꝭ|\.)|in ?prima\b|an?ch?ora\b|e una\b|e uno\b|e un\b|qui\b|(?:\d+|[ivxlc]{2,}º?|[vxlc]º?)\s+\S)")
_cache: dict = {}


def _fp(p):
    try:
        return p.stat().st_mtime
    except OSError:
        return 0


def records(cid: str, statuses=None) -> list[dict]:
    """Cached by the page files' and Conti's data files' modification times."""
    st = data.settings(cid)
    statuses = tuple(sorted(statuses or st["statuses"]))
    pm = source.pages(cid)
    key = (cid, statuses, tuple((p["id"], p["status"]) for p in pm),
           tuple(_fp(source.WORKSPACE / cid / d / f"{p['id']}.json") for p in pm if p["status"] in statuses for d in ("pages", "reading")),
           _fp(data.DATA / cid / "sums_review.json"), _fp(data.DATA / cid / "tags.json"), _fp(data.DATA / "_names.json"),
           _fp(data.DATA / cid / "settings.json"))
    hit = _cache.get((cid, statuses))
    if hit and hit[0] == key:
        return hit[1]
    recs = _records(cid, set(statuses), st, pm)
    _cache[(cid, statuses)] = (key, recs)
    return recs


def _records(cid, statuses, st, pages) -> list[dict]:
    style, pound = st["date_style"], st["pound"]
    rev = data.reviews(cid)
    alltags = tagmod.load(cid)
    al = tagmod.aliases()
    out = []
    year = None            # running year (as written) through the manuscript
    year_src = None
    last_book = {}          # book type ('libro', 'entrata', …) -> last book of that type named explicitly
    for pm in pages:
        if pm["status"] not in statuses:
            continue
        pg = source.page(cid, pm["id"])
        n_entry = 0
        prev_sep = True
        for row in pg["rows"]:
            r = dict(row)
            r["page_order"] = pm["order"]
            r["status_code"] = pm["status"]
            r["key"] = f"{pm['id']}|{row['line_ids']}"
            text = row.get("text") or ""
            # --- years standing alone (heading line, date box) set the running year
            for cand in (row.get("date") or "", text):
                y = dates.year_only(cand)
                if y:
                    year, year_src = y, f"{pm['id']} line {row['line']}"
            # --- dates in the entry
            found = []
            for d in dates.find(text) + dates.find(row.get("date") or ""):
                fd = dates.finish(d, year, style)
                if fd["year_inferred"]:
                    fd["year_from"] = year_src
                elif d.get("year_written"):
                    year, year_src = d["year_written"], f"{pm['id']} line {row['line']}"
                found.append(fd)
            r["dates"] = found
            # --- kind, references
            r["kind"] = refs.kind(text)
            # --- entry: an account (X de dare … Anno dato …) or an item (Item…, E una casa…) runs until the next one
            pl = dates.plain(text)
            is_sep = not re.search(r"[^\W_]", text) or dates.year_only(text) is not None
            starts = (r["kind"] in ("debit", "balance") or (r["kind"] == "credit" and not re.match(r"^\s*(?:h?anno|a me|ame)\s", pl))
                      or bool(_ENTRY_START.match(pl)) or prev_sep)
            if is_sep:
                r["entry"] = None
            else:
                if starts or n_entry == 0:
                    n_entry += 1
                r["entry"] = f"{pm['id']}#{n_entry}"
            prev_sep = is_sep
            # --- tags
            r["tags"] = tagmod.for_line(alltags.get(r["key"]), text, al)
            rr = refs.refs(text)
            for x in rr:
                b = x["book"]
                if not b:
                    x["book_resolved"] = "(this book)"
                elif refs.is_said(b):
                    x["book_resolved"] = last_book.get(refs.book_type(b), b)
                else:
                    last_book[refs.book_type(b)] = b
                    x["book_resolved"] = b
            r["refs"] = rr
            # --- money
            r["mentions"] = [{"raw": m["raw"], "amount": m["amount"].as_dict(pound)} for m in money.mentions(text)]
            a, written, src = _amount_for(row)
            r["amount"] = a.as_dict(pound) if a else None
            r["amount_written"] = written
            r["amount_source"] = src
            # --- Laura's decision
            rv = rev.get(r["key"])
            final = r["amount"] if (a and not a.empty) else None
            r["review"] = None
            if rv:
                state = "confirmed" if rv.get("written") == written else "changed"
                r["review"] = {**rv, "state": state}
                if state == "confirmed":
                    if rv["decision"] == "not_sum":
                        final = None
                    elif rv["decision"] == "corrected":
                        final = money.parse(rv.get("text", "")).as_dict(pound)
            r["amount_final"] = final
            r["amount_confirmed"] = bool(rv and r["review"]["state"] == "confirmed")
            out.append(r)
    return out


def summary(recs: list[dict]) -> dict:
    with_amt = [r for r in recs if r["amount"] and not r["amount"]["empty"]]
    return {
        "lines": len(recs),
        "pages": len({r["page"] for r in recs}),
        "sums": len(with_amt),
        "sums_with_problems": sum(1 for r in with_amt if r["amount"]["problems"] and not r["amount_confirmed"]),
        "sums_confirmed": sum(1 for r in recs if r["amount_confirmed"]),
        "dates": sum(len(r["dates"]) for r in recs),
        "refs": sum(len(r["refs"]) for r in recs),
        "debit": sum(1 for r in recs if r["kind"] == "debit"),
        "credit": sum(1 for r in recs if r["kind"] == "credit"),
        "balance": sum(1 for r in recs if r["kind"] == "balance"),
        "tags": sum(len(r["tags"]) for r in recs),
        "tags_approved": sum(1 for r in recs for t in r["tags"] if t["status"] == "approved"),
        "entries": len({r["entry"] for r in recs if r.get("entry")}),
    }
