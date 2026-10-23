"""Debts and payments with their parties, for questions such as "who borrowed the most" or "who owed whom".

Built from the entries Conti already finds (extract.records + query._entries) and the tags; nothing is stored.

transactions(manuscripts, statuses=None) → [tx], each tx =
  id, kind "debt" | "payment", manuscript, page, entry, lines [line numbers], keys [line keys], line_ids
  debtors     [{name, type (person|institution), occupations [..], occupation_basis "same entry" | "elsewhere" | ""}]
  creditor    {name, basis "tagged" | "assumed (account holder)" | "unknown"}
  florins     decimal florins (ƒ ß 𝒹 a fiorino counted at 29 soldi a fiorino to the florin)   — kept apart from
  lire        decimal lire (℔ ß 𝒹, 12 𝒹 = 1 ß, 20 ß = 1 lira)                                    — never converted
  display, sum_written, sum_checked (Laura confirmed/corrected the sum), sum_problems (rules flagged it)
  tags_checked (every party tag approved by Laura), date (modern iso) / year / year_written, text

How an entry is read (heuristic, stated in every answer):
  * a DEBT starts on a line that says de dare / deono dare (or names a tagged debtor together with "dare");
    its sum is the first sum from that line until the first payment line.
  * a PAYMENT is a line saying anno dato / a me dato / a mone dato…; its sum is on that line or the next ones
    before the following payment. Payments are made by the debtors of the debt above them, to the creditor.
  * debtors = tags with role "debtor" (people or institutions) in the debt's lines, else anywhere in the entry.
  * creditor = a tag with role "creditor" in the entry; otherwise the manuscript's account holder (Settings),
    marked "assumed (account holder)"; otherwise "unknown".
  "de dare" means "owes": a debt to the estate may be rent, a purchase or a loan; the book rarely says which.
"""
from __future__ import annotations

import re
from statistics import median

from . import data, extract, query, source
from .textnorm import plain

SOLDI_A_FIORINO = 29
_PAY = re.compile(r"^\s*(?:e\s+)?(?:h?anno|hanne|anne|a\s*m[eo]\s*n?e?|amone|ame|a\s*noi|abbiamo|ha)\s+dat[oie]\b")
_DARE = re.compile(r"\bd(?:i|e|ee)?\s*d?dare\b|\bdeon?\s*dare\b|\bdeondare\b|\bdedare\b")


def florins_of(a: dict | None) -> float | None:
    if not a or a.get("florins") is None:
        return None
    x = float(a["florins"])
    if a.get("florin_parts"):
        x += (a.get("soldi") or 0) / SOLDI_A_FIORINO + (a.get("denari") or 0) / (SOLDI_A_FIORINO * 12)
    return round(x, 4)


def lire_of(a: dict | None) -> float | None:
    if not a or a.get("lire_decimal") is None:
        return None
    return float(a["lire_decimal"])


def account_holder(cid: str) -> str:
    return (data.settings(cid).get("account_holder") or "").strip()


def _occupations(recs: list[dict]) -> dict:
    """person name → {occupation: set(entries)} from occupation tags whose "of" names the person (all manuscripts given)."""
    occ = {}
    for r in recs:
        for t in r.get("tags", []):
            if t["type"] != "occupation":
                continue
            for who in re.split(r"\s*;\s*", (t.get("attrs") or {}).get("of") or ""):
                if who:
                    occ.setdefault(who.strip(), {}).setdefault(t["canon"], set()).add(r.get("entry"))
    return occ


def _party(t):
    return {"name": t["canon"], "type": t["type"], "status": t["status"]}


def _amount(lines):
    for r in lines:
        if r.get("amount_final"):
            return r
    return None


def transactions(manuscripts: list[str] | None = None, statuses=None) -> list[dict]:
    mss = manuscripts or [c["id"] for c in source.collections()]
    recs = []
    for cid in mss:
        recs += extract.records(cid, statuses or data.settings(cid)["statuses"])
    occ = _occupations(recs)
    from . import tags as tagmod
    al = tagmod.aliases()
    out = []
    for eid, rs in query._entries(recs).items():
        cid = rs[0]["manuscript"]
        holder = account_holder(cid)
        # --- split the entry into blocks: debt blocks and payment blocks
        blocks, cur = [], None
        for r in rs:
            p = plain(r.get("text") or "")
            debtor_here = any((t.get("attrs") or {}).get("role") == "debtor" for t in r["tags"])
            if r["kind"] == "credit" and _PAY.search(p) or _PAY.search(p):
                cur = {"kind": "payment", "lines": [r]}; blocks.append(cur)
            elif r["kind"] in ("debit", "balance") or (debtor_here and _DARE.search(p)):
                cur = {"kind": "debt", "lines": [r]}; blocks.append(cur)
            elif cur is None:
                cur = {"kind": "other", "lines": [r]}; blocks.append(cur)
            else:
                cur["lines"].append(r)
        all_tags = [t for r in rs for t in r["tags"]]
        creditors = [t for t in all_tags if (t.get("attrs") or {}).get("role") == "creditor"]
        if creditors:
            creditor = {"name": creditors[0]["canon"], "basis": "tagged", "status": creditors[0]["status"]}
        elif holder:
            creditor = {"name": tagmod.canonical("person", holder, al), "basis": "assumed (account holder)", "status": "setting"}
        else:
            creditor = {"name": "(unknown)", "basis": "unknown", "status": ""}
        entry_debtors = [t for t in all_tags if (t.get("attrs") or {}).get("role") == "debtor"]
        last_debtors = None
        for i, b in enumerate(blocks):
            if b["kind"] == "other":
                continue
            ds = [t for r in b["lines"] for t in r["tags"] if (t.get("attrs") or {}).get("role") == "debtor"]
            if b["kind"] == "debt":
                ds = ds or (entry_debtors if sum(1 for x in blocks if x["kind"] == "debt") == 1 else [])
                last_debtors = ds
            else:
                ds = ds or last_debtors or entry_debtors
            seen, debtors = set(), []
            for t in ds:
                if t["canon"] in seen:
                    continue
                seen.add(t["canon"])
                o = occ.get(t["canon"]) or occ.get(t["name"]) or {}
                here = [k for k, es in o.items() if eid in es]
                debtors.append({**_party(t), "occupations": here or sorted(o),
                                "occupation_basis": "same entry" if here else ("elsewhere" if o else "")})
            ar = _amount(b["lines"])
            a = ar["amount_final"] if ar else None
            dated = next((d for r in b["lines"] for d in r.get("dates") or [] if d.get("iso_modern") or d.get("year_modern")), None)
            if not dated:
                dated = next((d for r in rs for d in r.get("dates") or [] if d.get("year_modern")), None)
            party_tags = ds + creditors[:1]
            out.append({
                "id": f"{eid}/{i + 1}", "kind": b["kind"], "manuscript": cid, "page": rs[0]["page"], "entry": eid,
                "lines": [r["line"] for r in b["lines"]], "keys": [r["key"] for r in b["lines"]],
                "line_ids": ",".join(r["line_ids"] for r in b["lines"]),
                "sum_line_ids": ar["line_ids"] if ar else "",
                "debtors": debtors, "creditor": creditor,
                "florins": florins_of(a), "lire": lire_of(a), "display": a["display"] if a else "",
                "sum_written": ar["amount_written"] if ar else "",
                "sum_checked": bool(ar and ar.get("amount_confirmed")),
                "sum_problems": bool(a and a.get("problems")) and not (ar and ar.get("amount_confirmed")),
                "tags_checked": bool(party_tags) and all(t["status"] == "approved" for t in party_tags),
                "date": (dated or {}).get("iso_modern") or "", "year": (dated or {}).get("year_modern"),
                "year_written": (dated or {}).get("year_written"), "year_inferred": bool((dated or {}).get("year_inferred")),
                "text": " / ".join(r["text"] for r in b["lines"]),
                "translation": " ".join(r.get("translation") or "" for r in b["lines"]).strip(),
            })
    return out


# ------------------------------------------------------------------ small statistics helpers
def stats(vals: list[float]) -> dict:
    v = sorted(x for x in vals if x is not None)
    if not v:
        return {"n": 0, "total": 0, "mean": None, "median": None, "max": None, "min": None}
    return {"n": len(v), "total": round(sum(v), 2), "mean": round(sum(v) / len(v), 2), "median": round(median(v), 2),
            "max": round(v[-1], 2), "min": round(v[0], 2)}
