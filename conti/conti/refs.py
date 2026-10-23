"""Cross-references and the kind of entry.

refs(text)  folio references: "ac̄ 41", "acār 309", "a carte 39", "c̄ 14", "acār 72/⁊/73/74/105", each with the book
            it points to when the line names one ("a libro giallo ac̄ 312", "al memoriale delle rede ac̄ 38",
            "a entrata di miniato c̄ 14"). "libro detto" (the said book) is resolved later to the last book named.
kind(text)  debit  = de dare / deono dare / dedare / deondare / debbe dare
            credit = de avere / deono avere / anno dato (= hanno dato) / a me dato
            balance = resta a dare / resta adare
"""
from __future__ import annotations

import re

from .numbers import roman
from .textnorm import plain

_NUMS = r"(\d+|[ivxlj]+)((?:(?:\s*(?:/|,|\be\b)\s*)+(?:\d+|[ivxlj]+)\b)*)"
_REF = re.compile(r"(?:\ba\s*c(?:ar(?:te|ta|t)?|arte|\.)?|(?<![a-z])c(?:ar|arte|arta)?\.?)\s*" + _NUMS + r"(?![a-z]{2})")
_BOOKS = r"libr[oi]|memoriale|quaderno|quadernuccio|giornale|entrata|uscita|ricordanze|debitori|creditori|squartafoglio|stracciafoglio"
_BOOK = re.compile(rf"(?:{_BOOKS})\b((?:\s+(?!a\b|ac\b|acar\b|al\b|de\b|e\b|che\b|c\b|car\b|i\b|in\b|ne\b|posti\b)[a-z]+){{0,3}})")
_STOP_TAIL = {"di", "del", "delle", "della", "a", "al", "e", "posti", "detto"}


def _n(s):
    return int(s) if s.isdigit() else roman(s)


def refs(text: str) -> list[dict]:
    p = plain(text)
    out = []
    for m in _REF.finditer(p):
        if not m.group(1).isdigit():          # roman folio: "a c̄ xi" needs a space, and not "carlo", "cii"
            end = m.end(1)
            if not p[m.start(1) - 1].isspace() or (end < len(p) and p[end].isalpha()):
                continue
        nums = [m.group(1)] + re.findall(r"\d+|[ivxlj]+\b", m.group(2) or "")
        folios = [v for v in (_n(x) for x in nums) if v]
        if not folios:
            continue
        book = None
        before = p[max(0, m.start() - 70):m.start()]
        bm = list(_BOOK.finditer(before))
        if bm:
            b = bm[-1]
            words = (b.group(0)).split()
            while len(words) > 1 and words[-1] in _STOP_TAIL - {"detto"}:
                words.pop()
            if len(words) > 2 and words[-1] in ("detto", "detta"):     # "entrata di miniato detta" = that same book
                words.pop()
            book = " ".join(words)
            between = before[b.end():]
            if re.search(r"\b(?:e|et)\s+a\b", between) and not between.strip().endswith(("a", "al")):
                pass
        out.append({"folios": folios, "book": book, "raw": m.group(0).strip()})
    return out


_DEBIT = re.compile(r"\bd(?:e|ee|ebbe|eono|eon|ebbono|evono|ebono)\s*(?:a\s*)?d?dare\b")
_CREDIT = re.compile(r"\bd(?:e|ee|ebbe|eono|eon|ebbono|evono|ebono)\s*(?:a\s*)?d?avere\b|\b(?:h?anno|ha|a\s*me|ame|abbiamo)\s+dato\b")
_BAL = re.compile(r"\bresta\s*(?:a|ad|da)?\s*d?dare\b|\bresta\s+a\s*d?avere\b")


def kind(text: str) -> str | None:
    p = plain(text)
    if _BAL.search(p):
        return "balance"
    d, c = _DEBIT.search(p), _CREDIT.search(p)
    if d and c:
        return "debit" if d.start() < c.start() else "credit"
    return "debit" if d else ("credit" if c else None)


def book_type(book: str) -> str:
    w = book.split()[0]
    return "libro" if w.startswith("libr") else w


def is_said(book: str) -> bool:
    """'libro detto', 'entrata detta', 'libro' alone: points back to the last book of that kind named before."""
    words = book.split()
    return len(words) == 1 or (len(words) == 2 and words[1] in ("detto", "detta", "dette", "detti"))
