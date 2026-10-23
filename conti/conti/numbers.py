"""Numbers as written in the account books: roman numerals (medieval, mostly additive: viiii, xxiiiiº, clxxxxiii,
j for final i), arabic figures, and Italian number words in period spellings (secte, octo, dugento, centosette)."""
from __future__ import annotations

import re

from .textnorm import plain

_ROMAN = {"i": 1, "j": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
ROMAN_RE = re.compile(r"^[ivxlcdmj]+$")
NOT_ROMAN = {"di", "mi", "ci", "li", "dì", "il", "lì", "vi'"}


def roman(tok: str) -> int | None:
    """Value of a roman numeral, or None. Trailing º/° and superscripts are ignored (written ends of iiii)."""
    t = tok.lower().rstrip("º°ᵒ.").replace("ᶜ", "c")
    if not t or not ROMAN_RE.match(t) or t in NOT_ROMAN:
        return None
    vals = [_ROMAN[c] for c in t]
    total = 0
    for i, v in enumerate(vals):
        total += -v if i + 1 < len(vals) and vals[i + 1] > v and v in (1, 10, 100) and vals[i + 1] <= v * 10 else v
    return total


_WORDS = {
    "un": 1, "uno": 1, "una": 1, "due": 2, "dua": 2, "duo": 2, "tre": 3, "quattro": 4, "quatro": 4, "quactro": 4,
    "cinque": 5, "cinqe": 5, "cinqua": 5, "cinqet": 5, "sei": 6, "sette": 7, "secte": 7, "sete": 7, "socte": 7,
    "otto": 8, "octo": 8, "nove": 9, "dieci": 10, "diece": 10, "dece": 10, "undici": 11, "undeci": 11,
    "dodici": 12, "dodeci": 12, "tredici": 13, "tredeci": 13, "quattordici": 14, "quatordici": 14,
    "quindici": 15, "quindeci": 15, "sedici": 16, "sedeci": 16, "diciassette": 17, "dicessette": 17,
    "dicesette": 17, "dicecte": 17, "diciotto": 18, "diciocto": 18, "dicotto": 18, "dicocto": 18,
    "diciannove": 19, "dicennove": 19, "dicenove": 19, "venti": 20, "vinti": 20, "vent": 20, "trenta": 30,
    "trent": 30, "quaranta": 40, "quarant": 40, "cinquanta": 50, "cinquant": 50, "sessanta": 60, "sessant": 60,
    "settanta": 70, "sectanta": 70, "settant": 70, "ottanta": 80, "octanta": 80, "ottant": 80, "novanta": 90,
    "novant": 90, "cento": 100, "secento": 600, "seciento": 600, "ciento": 100, "dugento": 200, "dugiento": 200, "duegento": 200, "mille": 1000,
    "milia": 1000, "mila": 1000,
}
_PARTS = sorted(_WORDS, key=len, reverse=True)


def word_number(tok: str) -> int | None:
    """'trenta' → 30, 'centosette' → 107, 'trecento' → 300; None if the word is not entirely a number."""
    w = plain(tok)
    if len(w) < 2:
        return None
    parts, i = [], 0
    while i < len(w):
        for p in _PARTS:
            if w.startswith(p, i):
                parts.append(_WORDS[p]); i += len(p); break
        else:
            return None
    total, cur = 0, 0
    for v in parts:
        if v == 100:
            cur = (cur or 1) * 100
        elif v == 1000:
            total += (cur or 1) * 1000; cur = 0
        elif v == 200:
            cur = cur * 100 + 200 if cur else 200
        else:
            cur += v
    return total + cur


def number(tok: str) -> int | None:
    t = tok.strip(".")
    if t.isdigit():
        return int(t)
    return roman(t)
