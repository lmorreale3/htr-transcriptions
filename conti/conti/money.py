"""Sums of money as written → a value, without ever changing what was written.

Florentine accounts keep two things apart, and so does Conti:
  florins  ƒ (gold coin, counted on its own)
  lire · soldi · denari  ℔/⫳/𝓎 · ß/β · 𝒹  (12 denari = 1 soldo, 20 soldi = 1 lira), often closed by pc̄ (piccioli)
  or marked "a fiorino" (lire a fiorino, the accounting money).
The florin–lira exchange changed over time, so florins are never converted into lire here.

parse(text)   → Amount (fields below) from a sum column: the sign comes before its figure ("ƒ ii ℔ x ß xii 𝒹 vi pc̄").
mentions(text) → amounts named anywhere in a line ("ƒ trenta", "⫳ 24 ß 8"), for queries; not used for totals.
trailing(text) → the amount at the very end of an entry line, if any (used when the sum was never cut off the line).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from .numbers import number, word_number
from .textnorm import clean

RANK = {"fl": 0, "li": 1, "so": 2, "de": 3}
SIGN_OF = {"fl": "ƒ", "so": "ß", "de": "𝒹"}

_TOK = re.compile(
    r"(?P<pc>p(?:c̄|ē|ē)(?![a-z]))"
    r"|(?P<aff>\ba\s?ƒƒ|\baff\b|\ba\s+fiorin[oi]\b)"
    r"|(?P<fl>ƒi[oō]̄?|ƒ[oō](?![a-z])|ƒƒ|ƒ|\bfl\b\.?|\bfio\b\.?|\bfior(?:ini|ino|\.)?(?![a-z]))"
    r"|(?P<li>℔|⫳|𝓎|ƀ|\b(?:lire|libre|lira|libra|lb)\b\.?)"
    r"|(?P<so>ß|β|\bsol(?:di|do)\b\.?)"
    r"|(?P<de>𝒹|\bdenari\b|\bdenaro\b|(?<![^\W\d_])d\b\.?)"
    r"|(?P<frac>\d+\s?/\s?\d+)"
    r"|(?P<ar>\d+(?:\.\d+)*)"
    r"|(?P<ro>(?<![^\W\d_ƒß𝒹β])[ivxlcdmjIVXLCDMJ]+[º°ᵒ]?(?![^\W\d_ƒß𝒹β]))"
    r"|(?P<wd>[^\W\d_ƒß𝒹β̀-ͯ][^\W\d_ƒß𝒹β]*[̀-ͯ]*(?:[^\W\d_ƒß𝒹β\s][̀-ͯ]*)*)"
    r"|(?P<bar>\|)"
)
IGNORE_WORDS = {"e", "et", "⁊", "a"}


def tokens(text: str) -> list[tuple[str, object, str]]:
    """[(kind, value, raw)]; kind = fl li so de (signs) pc aff num frac word bar."""
    out = []
    for m in _TOK.finditer(text):
        k = m.lastgroup; raw = m.group(k)
        if k in ("ar",):
            out.append(("num", raw, raw))
        elif k == "ro":
            v = number(raw)
            out.append(("num", v, raw) if v is not None else ("word", None, raw))
        elif k == "wd":
            v = word_number(raw)
            if v is None and raw.lower() in ("di", "mi", "ci", "li"):
                out.append(("word", None, raw))
            elif v is None:
                v2 = number(raw)
                out.append(("num", v2, raw) if v2 is not None else ("word", None, raw))
            else:
                out.append(("num", v, raw))
        else:
            out.append((k, None, raw))
    # numbers written as several words ("trecento dieci") are one number
    merged = []
    for t in out:
        if (t[0] == "num" and merged and merged[-1][0] == "num" and isinstance(t[1], int)
                and isinstance(merged[-1][1], int) and word_number(t[2]) is not None
                and word_number(merged[-1][2]) is not None and merged[-1][1] > t[1]):
            merged[-1] = ("num", merged[-1][1] + t[1], merged[-1][2] + " " + t[2])
        else:
            merged.append(t)
    return merged


@dataclass
class Amount:
    florins: int | None = None
    lire: int | None = None
    soldi: int | None = None
    denari: int | None = None
    piccioli: bool = False
    a_fiorino: bool = False
    problems: list = field(default_factory=list)   # [(code, message)]
    empty: bool = True                                # no figure at all
    florin_parts: bool = False                        # ƒ ß 𝒹 without lire: ß/𝒹 are soldi/denari a fiorino

    def lsd_denari(self) -> int | None:
        """Lire money in denari (lire·240 + soldi·12 + denari); None when there is none or ß/𝒹 belong to a florin."""
        if self.florin_parts or (self.lire is None and self.soldi is None and self.denari is None):
            return None
        return (self.lire or 0) * 240 + (self.soldi or 0) * 12 + (self.denari or 0)

    def display(self, pound: str = "℔") -> str:
        parts = []
        for key, sign in (("florins", "ƒ"), ("lire", pound), ("soldi", "ß"), ("denari", "𝒹")):
            v = getattr(self, key)
            if v is not None:
                parts.append(f"{sign} {v}")
        if self.piccioli:
            parts.append("pc̄")
        if self.a_fiorino:
            parts.append("a ƒ")
        return " ".join(parts)

    def as_dict(self, pound: str = "℔") -> dict:
        d = asdict(self)
        d["problems"] = [{"code": c, "msg": m} for c, m in self.problems]
        d["lsd_denari"] = self.lsd_denari()
        d["lire_decimal"] = round(self.lsd_denari() / 240, 4) if self.lsd_denari() is not None else None
        d["display"] = self.display(pound)
        return d


_FIELD = {"fl": "florins", "li": "lire", "so": "soldi", "de": "denari"}


def _value(raw_val, raw):
    if isinstance(raw_val, int):
        return raw_val
    try:
        return int(str(raw_val).split(".")[0])
    except ValueError:
        return None


def from_tokens(toks, *, allow_words=False) -> Amount:
    a = Amount()
    pending = None          # sign waiting for its figure
    order = []
    for kind, val, raw in toks:
        if kind in _FIELD:
            if raw == "ƀ":
                a.problems.append(("b-for-lira", "ƀ read as the lira sign (often a misreading of ℔)"))
            if kind == "de" and raw.strip(".") == "d":
                a.problems.append(("plain-d", "plain d read as denari (𝒹)"))
            pending = kind
        elif kind == "pc":
            a.piccioli = True
        elif kind == "aff":
            a.a_fiorino = True
        elif kind == "num":
            if pending is None:
                a.problems.append(("no-sign", f"figure {raw} has no money sign before it"))
                continue
            fld = _FIELD[pending]
            if kind == "num" and isinstance(val, str) and "." in val:          # dotted figure: 2.5 = lire 2 soldi 5
                bits = [int(b) for b in val.split(".") if b]
                if pending == "li" and len(bits) in (2, 3):
                    a.lire, a.soldi = bits[0], bits[1]
                    if len(bits) == 3:
                        a.denari = bits[2]
                    a.problems.append(("dotted", f"{raw} read as lire.soldi{'.denari' if len(bits) == 3 else ''}"))
                    order += ["li", "so"] + (["de"] if len(bits) == 3 else [])
                    a.empty = False; pending = None
                    continue
            v = _value(val, raw)
            if v is None:
                a.problems.append(("unreadable", f"cannot read the figure {raw}")); continue
            if getattr(a, fld) is not None:
                a.problems.append(("twice", f"{SIGN_OF.get(pending, 'lire')} given twice ({getattr(a, fld)} and {v})"))
            else:
                setattr(a, fld, v); order.append(pending)
            a.empty = False
            pending = None
        elif kind == "frac":
            a.problems.append(("fraction", f"fraction {raw} not counted"))
        elif kind == "word":
            if raw.lower() in IGNORE_WORDS:
                continue
            a.problems.append(("word", f"'{raw}' is not part of a sum"))
    # ƒ … ß … 𝒹 with no lire: soldi and denari are parts of the florin (a fiorino), not lire money
    a.florin_parts = a.florins is not None and a.lire is None and (a.soldi is not None or a.denari is not None)
    if order != sorted(order, key=RANK.get):
        a.problems.append(("order", "denominations not in the order ƒ · lire · ß · 𝒹"))
    if a.florin_parts:
        if a.soldi is not None and a.soldi >= 29:
            a.problems.append(("soldi>=29", f"{a.soldi} soldi of the florin (29 a fiorino make a florin)"))
    elif a.soldi is not None and a.soldi >= 20:
        a.problems.append(("soldi>=20", f"{a.soldi} soldi (20 make a lira)"))
    if a.denari is not None and a.denari >= 12:
        a.problems.append(("denari>=12", f"{a.denari} denari (12 make a soldo)"))
    return a


def parse(text: str) -> Amount:
    """A sum as written in the sums column (sub-lines joined with |)."""
    return from_tokens([t for t in tokens(clean(text)) if t[0] != "bar"])


def trailing(text: str):
    """(raw, tokens) of the amount closing an entry line, or None. Starts at the first money sign of the final run."""
    toks = [t for t in tokens(clean(text)) if t[0] != "bar"]
    i = len(toks)
    while i > 0 and toks[i - 1][0] in ("fl", "li", "so", "de", "pc", "aff", "num"):
        i -= 1
    run = toks[i:]
    while run and run[0][0] not in ("fl", "li", "so", "de", "pc", "aff"):
        run = run[1:]
    if not run or not any(t[0] == "num" for t in run) or not any(t[0] in _FIELD for t in run):
        return None
    return " ".join(t[2] for t in run), run


def mentions(text: str) -> list[dict]:
    """Every sign-plus-figure group in a line: [{raw, amount}]. ß before a name (di ß giovanni = ser) is skipped."""
    toks = [t for t in tokens(clean(text)) if t[0] != "bar"]
    out, cur = [], []

    def flush():
        if cur and any(t[0] == "num" for t in cur) and any(t[0] in _FIELD for t in cur):
            out.append({"raw": " ".join(t[2] for t in cur), "amount": from_tokens(cur)})
        cur.clear()

    for i, t in enumerate(toks):
        k = t[0]
        if k in _FIELD:
            seen = [RANK[c[0]] for c in cur if c[0] in _FIELD]
            if seen and RANK[k] <= max(seen):       # a new sum starts: ƒ … ß … then ℔ again
                flush()
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            if nxt and nxt[0] == "num":
                cur.append(t)
            elif cur and k in ("so", "de"):     # trailing empty sign: "β 10 𝒹"
                cur.append(t)
            else:
                flush()
        elif k == "num":
            if cur and cur[-1][0] in _FIELD:
                cur.append(t)
            else:
                flush()
        elif k in ("pc", "aff"):
            if cur:
                cur.append(t)
        else:
            flush()
    flush()
    return out
