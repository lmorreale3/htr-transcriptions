"""Dates written in the entries ("Anno dato di xviii di Novēƀre 389", "adi 13 di marzo", "di vii di gen̄aio 388").

Every date keeps BOTH years:
  year_written  the year as the scribe wrote it (or as carried forward from the last year written above it)
  year_modern   the same day in modern reckoning (year starting 1 January)
Style of the manuscript (per-manuscript setting):
  florentine  year begins 25 March (ab incarnatione, stile fiorentino): 1 Jan–24 Mar → year_modern = written + 1
  pisan       year begins 25 March of the year before: 25 Mar–31 Dec → year_modern = written − 1
  modern      year_modern = year_written
Three-figure years are read with the thousand left out (389 → 1389). A date with no year takes the last year
written above it in the same manuscript (pages in Leggio's order); such years are marked inferred.
"""
from __future__ import annotations

import datetime as _dt
import re

from .numbers import number, word_number
from .textnorm import plain

MONTHS = [
    (1, r"gen+[a-z]{0,4}|ienn?[a-z]{0,4}|ianuar[a-z]*|zen+ar[a-z]*"),
    (2, r"feb+r?[a-z]{0,5}|febr[a-z]*"),
    (3, r"mar?z+[oi]|marzo"),
    (4, r"ap?pril[ea]?|aprile"),
    (5, r"mag+i?o|maggio"),
    (6, r"g?i?ug+n[oi]?|giugnio"),
    (7, r"l?u?gl[i]?[oi]|lugl[a-z]*"),
    (8, r"ag[ou]st[oa]"),
    (9, r"se[ct]+[a-z]{0,5}b?re|setten[a-z]*|setem[a-z]*"),
    (10, r"o?t+o?b+re|ott[a-z]*bre|octob[a-z]*"),
    (11, r"no[vbu]e?[mn]?b+r?e|novem[a-z]*|nove?bre"),
    (12, r"(?:di|de)?ce[mn]?b+r?e|dicem[a-z]*|decem[a-z]*"),
]
_MONTH_RES = [(m, re.compile(rf"^(?:{p})$")) for m, p in MONTHS]
NAMES = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
         "ottobre", "novembre", "dicembre"]
CONNECT = {"di", "de", "d", "del", "a", "adi", "ad", "il", "dì"}
_WORD = re.compile(r"[a-z0-9ß]+")


def month_of(w: str) -> int | None:
    for cand in (w, w[1:] if w.startswith("d") and len(w) > 4 else None):
        if not cand:
            continue
        for m, rx in _MONTH_RES:
            if rx.match(cand):
                return m
    return None


def _num(w: str) -> int | None:
    if w.isdigit():
        return int(w)
    return number(w) if number(w) is not None else word_number(w)


def year_value(w: str) -> int | None:
    """'1389' → 1389, '389' → 1389, 'mccclxxxviii' → 1388; else None."""
    if w.isdigit():
        n = int(w)
        if len(w) == 4 and 1100 <= n <= 1699:
            return n
        if len(w) == 3 and 100 <= n <= 699:
            return 1000 + n
        return None
    v = number(w)
    if v is not None and (w.startswith("m") and 1100 <= v <= 1699 or w.startswith("c") and 100 <= v <= 699):
        return v if v >= 1000 else 1000 + v
    return None


def modern_year(day, month, year, style: str):
    if year is None or month is None:
        return year
    if style == "florentine":
        before = month < 3 or (month == 3 and (day or 1) < 25)
        return year + 1 if before else year
    if style == "pisan":
        after = month > 3 or (month == 3 and (day or 25) >= 25)
        return year - 1 if after else year
    return year


def find(text: str) -> list[dict]:
    """Dates in one line, without year inference: [{day, month, year_written, raw}]."""
    words = _WORD.findall(plain(text))
    out = []
    for k, w in enumerate(words):
        m = month_of(w)
        if m is None:
            continue
        j = k - 1
        while j >= 0 and words[j] in CONNECT and k - j <= 2:       # "xviii di di cēƀre", "adi 13 di marzo"
            j -= 1
        day = _num(words[j]) if j >= 0 else None
        if day is not None and not (1 <= day <= 31):
            day = None
        yw = None
        for nxt in words[k + 1:k + 3]:
            if nxt in ("anno", "ano", "an", "nel", "del"):
                continue
            yw = year_value(nxt)
            break
        if day is None and yw is None:
            continue                     # a lone month word ("maggio") is too weak to be a date
        start = j if day is not None else k
        out.append({"day": day, "month": m, "year_written": yw, "raw": " ".join(words[start:k + 2 if yw else k + 1])})
    return out


def year_only(text: str) -> int | None:
    """A line (or date box) that is just a year, e.g. 'mcclxxxviii', '1458', 'Mccccxviiii'."""
    words = [w for w in _WORD.findall(plain(text)) if w not in ("anno", "ano", "domini", "mcc")]
    if len(words) == 1:
        return year_value(words[0])
    return None


def finish(d: dict, context_year, style: str) -> dict:
    d = dict(d)
    d["year_inferred"] = d.get("year_written") is None and context_year is not None
    if d["year_inferred"]:
        d["year_written"] = context_year
    d["style"] = style
    d["year_modern"] = modern_year(d.get("day"), d.get("month"), d.get("year_written"), style)
    d["month_name"] = NAMES[d["month"]] if d.get("month") else ""
    iso = None
    if d.get("year_modern") and d.get("month"):
        try:
            iso = _dt.date(d["year_modern"], d["month"], d.get("day") or 1).isoformat()
            if not d.get("day"):
                iso = iso[:7]
        except ValueError:
            iso = None
    d["iso_modern"] = iso
    d["ambiguous"] = style == "florentine" and d.get("month") == 3 and d.get("day") is None
    return d
