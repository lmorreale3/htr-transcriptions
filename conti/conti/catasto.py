"""The Florentine Catasto of 1427 (city of Florence) as a reference list: who in the account books may appear in it.

Data: ROOT/reference/catasto_1427/catasto_1427_florence_decoded.csv (Brown University's Online Catasto, Herlihy &
Klapisch-Zuber; one row per household, the head's name only). Conti never changes that file.
Laura's decisions: conti_data/_catasto.json  {"<person name>": {"<stg_id>": {decision: same|relative|no, note, t}}}

How a person is matched (all of it shown as "reasons" next to each candidate):
- Names are compared in the Catasto's own spelling: upper case, no spaces, at most 10 letters (the file cuts longer names),
  Jacopo → IACOPO, Paolo → PAGOLO, Lionardo → LEONARDO, Francescho → FRANCESCO, ser / messer dropped, d'Andrea = di Andrea.
- A few well-known short forms count as a weaker match (Nanni / Vanni = Giovanni, Meo = Bartolomeo, Cecco = Francesco…).
- Same person: first name + father's name agree (and the family name, when both have one; a different family name rules
  the household out). A name shared by many households is marked "common".
- Relative: the Catasto head's father (or, for a widow, her late husband) has the person's name, and the family name agrees.
- Time: the Catasto head's age in 1427 is turned back to the years the person appears in the book. Someone under 15 then
  cannot be the same person (he may be a son or heir).
- Trade: the person's occupation tag is compared with the Catasto trade code (agrees / differs), never used to exclude.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from functools import lru_cache

from . import data, extract, source, tags

CSV = source.ROOT / "reference" / "catasto_1427" / "catasto_1427_florence_decoded.csv"
YEAR = 1427
MAXLEN = 10                      # the Catasto keeps at most 10 letters of a name

# written form (after normalisation) → the Catasto's form
SPELL = {"JACOPO": "IACOPO", "JACOMO": "IACOPO", "IACOMO": "IACOPO", "GIACOPO": "IACOPO", "GIACOMO": "IACOPO",
         "PAOLO": "PAGOLO", "PAULO": "PAGOLO", "LIONARDO": "LEONARDO", "NICCOLAO": "NICCOLAIO", "NICHOLAIO": "NICCOLAIO",
         "NICOLAIO": "NICCOLAIO", "NICOLO": "NICCOLO", "NICHOLO": "NICCOLO", "TOMASO": "TOMMASO", "TOMAXO": "TOMMASO",
         "FRANCECO": "FRANCESCO", "FRANCESHO": "FRANCESCO", "CHRISTOFANO": "CRISTOFANO", "CRISTOFORO": "CRISTOFANO",
         "BARTOLOMMEO": "BARTOLOMEO", "BARTOLOMEO": "BARTOLOMEO", "STEFANO": "STEFANO", "STEFFANO": "STEFANO",
         "GABRIELLO": "GABBRIELLO", "ZANOBRI": "ZANOBI", "SALVESTRO": "SALVESTRO", "SILVESTRO": "SALVESTRO",
         "DOMENICHO": "DOMENICO", "LODOVICHO": "LODOVICO", "LUDOVICO": "LODOVICO", "JOHANNI": "GIOVANNI"}
# short forms: a weaker match, named in the reasons
SHORT = {"NANNI": "GIOVANNI", "VANNI": "GIOVANNI", "GIANNI": "GIOVANNI", "MEO": "BARTOLOMEO", "BARTOLO": "BARTOLOMEO",
         "CECCO": "FRANCESCO", "CECCA": "FRANCESCA", "LAPO": "IACOPO", "PUCCIO": "IACOPO", "COPPO": "IACOPO",
         "NANNA": "GIOVANNA", "TONIO": "ANTONIO", "MENICO": "DOMENICO", "DOMENICUCCIO": "DOMENICO", "NARDO": "LEONARDO",
         "BETTO": "BENEDETTO", "SANDRO": "ALESSANDRO", "NICCOLAIO": "NICCOLO", "NICCOLOSA": "NICCOLOSA", "NOFRI": "ONOFRIO",
         "BICE": "BEATRICE", "TOSO": "TOSO", "BINDO": "ILDEBRANDO", "DUCCIO": "DURANTE", "DINO": "ALDOBRANDINO",
         "GHERARDO": "GHERARDO", "AGNOLO": "ANGELO", "ANGIOLO": "AGNOLO", "MINIATO": "MINIATO", "GIOVANNOZZO": "GIOVANNI"}
TITLES = {"SER", "MESSER", "MESSERE", "MAESTRO", "MAESTRA", "FRATE", "FRA", "DON", "DONNO", "MONNA", "MADONNA", "PRETE", "SUORA"}
ARTICLES = ("DEGLI", "DELLE", "DELLA", "DELLO", "DELL", "DALLA", "DAL", "DEL", "DE", "DEI", "DI", "DA")

# occupation tag (normalised Italian word) → Catasto trade codes that agree with it
TRADE = {"VINATTIERE": [33], "VINAIUOLO": [33], "SPEZIALE": [26], "SARTO": [67], "FORNAIO": [41], "BOTTAIO": [48],
         "BARILAIO": [48], "LINAIOLO": [31], "LINAIUOLO": [31], "RIGATTIERE": [31], "SETAIOLO": [25], "SENSALE": [79],
         "NOTAIO": [21], "GIUDICE": [21], "ALBERGATORE": [34], "TAVERNAIO": [34], "OSTE": [34], "CIABATTINO": [29, 65],
         "CALZOLAIO": [29], "STOVIGLIAIO": [51], "BICCHIERAIO": [51], "PIZZICAGNOLO": [47], "LAVORATORE": [1, 2, 3, 4, 50],
         "PRETE": [70], "CAPPELLANO": [70], "PRIORE": [70, 71], "RETTORE": [70], "MONACA": [71, 82], "FRATE": [71],
         "MAZZIERE": [13], "BANDITORE": [13, 69], "PORTATORE": [20], "VETTURALE": [20], "TRECCONA": [7], "TRECCONE": [7],
         "ORAFO": [49], "ORAFI": [49], "BECCAIO": [28], "BARBIERE": [44], "CARDATORE": [45], "TESSITORE": [46, 64],
         "TINTORE": [43], "FABBRO": [30, 57], "LEGNAIOLO": [40], "MUGNAIO": [42], "MURATORE": [54], "SCARPELLINO": [54],
         "MEDICO": [32], "CAMBIATORE": [23], "LANAIOLO": [24, 93], "PILLICCIAIO": [27], "VAIAIO": [27], "CORREGGIAIO": [37],
         "CHIAVAIOLO": [39], "CUOCO": [16], "CARTOLAIO": [56], "SELLAIO": [55, 73], "FARSETTAIO": [58], "PITTORE": [95],
         "BIADAIOLO": [96], "FUNAIOLO": [97], "MAESTRO": [77], "ALBERGATRICE": [34], "TESSITORE DI DRAPPI": [25, 64]}


def plain(s: str) -> str:
    """Upper case, letters only; abbreviation marks and accents dropped."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z' ]", "", s).upper()


def full(word: str) -> str:
    """The Catasto's spelling of a written name, before the 10-letter cut."""
    w = plain(word).replace("'", "").replace(" ", "")
    if not w:
        return ""
    w = re.sub(r"([CG])H([AOU])", r"\1\2", w)          # Francescho → FRANCESCO, Domenicho → DOMENICO
    w = SPELL.get(w, w)
    if w.startswith("J"):
        w = SPELL.get("I" + w[1:], "I" + w[1:])
    return w


def key(word: str) -> tuple[str, str]:
    return full(word)[:MAXLEN], ""


def variants(word: str) -> list[tuple[str, str]]:
    """The Catasto forms a written name may take: (form, how) — how = "" (same name) or "short form of X"."""
    k = full(word)
    if not k:
        return []
    out = [(k[:MAXLEN], "")]
    if k in SHORT and SHORT[k] != k:
        out.append((SHORT[k][:MAXLEN], f"{k.title()} as a short form of {SHORT[k].title()}"))
    for s, long in SHORT.items():                       # the reverse: written Giovanni, Catasto NANNI
        if long == k and s != k:
            out.append((s[:MAXLEN], f"{s.title()} as a short form of {k.title()}"))
    return list(dict.fromkeys(out))


def family_key(words: list[str]) -> list[str]:
    """dell'Aressa → DELLARESSA and ARESSA; de' Bardi → DEBARDI and BARDI (the Catasto writes both ways)."""
    w = plain(" ".join(words)).replace("'", " ").split()
    if not w:
        return []
    joined = "".join(w)
    out = [joined[:MAXLEN]]
    core = [x for x in w if x not in ARTICLES]
    if core and core != w:
        out.append("".join(core)[:MAXLEN])
    if joined.startswith("DE") and not joined.startswith(("DEL", "DEGLI")):
        out.append(joined[2:][:MAXLEN])
    return list(dict.fromkeys(x for x in out if x))


def parse(name: str) -> dict:
    """'Pagolo di Jacopo dell'Aressa' → first PAGOLO, father IACOPO, grandfather '', family [DELLARESSA, ARESSA]."""
    s = re.sub(r"\b[dD]['’]\s*(?=[A-ZÀ-Üa-z])", "di ", name or "")    # d'Andrea → di Andrea
    s = s.replace("’", "'")
    words = [w for w in re.split(r"\s+", s.strip()) if w]
    words = [w for w in words if plain(w) not in TITLES]
    p = {"first": "", "father": "", "grandfather": "", "family": [], "origin": "", "written": name}
    if not words:
        return p
    p["first"] = words[0]; i = 1; fathers = []
    while i < len(words):
        w = plain(words[i])
        if w == "DI" and i + 1 < len(words):
            nxt = words[i + 1]
            if plain(nxt) in TITLES and i + 2 < len(words):
                nxt = words[i + 2]; i += 1
            fathers.append(nxt); i += 2; continue
        if w == "DA" and i + 1 < len(words):            # "da Nobi": where he came from, not a family name
            p["origin"] = " ".join(words[i + 1:]); break
        p["family"] = family_key(words[i:]); break
    if fathers:
        p["father"] = fathers[0]
        if len(fathers) > 1:
            p["grandfather"] = fathers[1]
    return p


@lru_cache(maxsize=2)
def _load(mtime: float) -> list[dict]:
    with open(CSV, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def rows() -> list[dict]:
    try:
        return _load(CSV.stat().st_mtime)
    except OSError:
        return []


@lru_cache(maxsize=2)
def _index(mtime: float):
    by_first, by_father, count = {}, {}, {}
    for r in _load(mtime):
        by_first.setdefault(r["name"], []).append(r)
        by_father.setdefault(r["patronymic"], []).append(r)
        count[(r["name"], r["patronymic"])] = count.get((r["name"], r["patronymic"]), 0) + 1
    return by_first, by_father, count


def index():
    return _index(CSV.stat().st_mtime)


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def household(r: dict) -> dict:
    """A Catasto row for the screen."""
    age = _int(r.get("age"))
    return {"stg_id": r["stg_id"], "name": r["name"], "patronymic": r["patronymic"], "family_name": r["family_name"],
            "written": " ".join(x for x in [r["name"].title(), ("di " + r["patronymic"].title()) if r["patronymic"] else "",
                                             r["family_name"].title()] if x),
            "series": r["series_label"], "gonfalone": r["location_label"], "quarter": r["quarter"],
            "trade_code": r["trade"], "trade": r["trade_label"], "sex": r["sex_label"], "marital": r["marital_status_label"],
            "age": age if age not in (79, None) else None, "age_note": {79: "age not known", 89: "under one year"}.get(age, ""),
            "bocche": _int(r["bocche"]), "total": _int(r["total"]), "deductions": _int(r["deductions"]),
            "taxable": _int(r["taxable"]), "real_estate": _int(r["real_estate"]),
            "public": _int(r["public_investment"]), "private": _int(r["private_investment"]),
            "volume": r["volume"], "page": r["page"], "declaration": r["type_of_declaration_label"],
            "heir": r.get("relation_to_head") == "0"}


def _trade_check(occs: list[str], code: str):
    c = _int(code)
    if not occs or c is None:
        return None
    c2 = c % 100 if c >= 100 else c
    known = [o for o in occs if plain(o).strip() in TRADE]
    if not known:
        return None
    ok = [o for o in known if c2 in TRADE[plain(o).strip()]]
    return (True, ok[0]) if ok else (False, known[0])


def candidates(name: str, occupations: list[str] | None = None, years: list[int] | None = None) -> dict:
    """Possible Catasto households for one tagged person."""
    p = parse(name)
    by_first, by_father, count = index()
    out = {}
    if not p["first"] or not (p["father"] or p["family"]):
        return {"parsed": _show(p), "candidates": [], "why_none": "only a first name: too little to look up"}
    yr = years[0] if years else None
    fam = set(p["family"])

    def fam_check(r):
        if fam and r["family_name"]:
            return (r["family_name"] in fam), True
        return True, False

    # 1. same person: first + father (+ family)
    for fk, fhow in variants(p["first"]):
        for r in by_first.get(fk, []):
            reasons, weak = [], bool(fhow)
            if fhow:
                reasons.append(fhow)
            if p["father"]:
                pv = dict(variants(p["father"]))
                if r["patronymic"] not in pv:
                    continue
                if pv[r["patronymic"]]:
                    reasons.append("father: " + pv[r["patronymic"]]); weak = True
                else:
                    reasons.append("same father's name")
            ok, both = fam_check(r)
            if not ok:
                continue
            if both:
                reasons.append("same family name")
            elif not p["father"]:
                continue                                    # first name + family only, and the Catasto has no family name
            n = count.get((r["name"], r["patronymic"]), 1)
            out[r["stg_id"]] = _cand(r, "same", reasons, weak, n, both, occupations, yr)
    # 2. relative: Catasto head's father (or late husband) has this person's name
    if fam:
        for fk, fhow in variants(p["first"]):
            for r in by_father.get(fk, []):
                if r["stg_id"] in out or not r["family_name"] or r["family_name"] not in fam:
                    continue
                h = household(r)
                rel = "widow" if h["sex"] == "Female" and h["marital"].startswith("Widow") else \
                      ("daughter" if h["sex"] == "Female" else "son")
                reasons = [f"the Catasto head's {'late husband' if rel == 'widow' else 'father'} has this name: "
                           f"perhaps his {rel}" + (" (or heir)" if rel == "son" else ""),
                           "same family name"] + ([fhow] if fhow else [])
                c = _cand(r, "relative", reasons, bool(fhow), count.get((r["name"], r["patronymic"]), 1), True, occupations, yr)
                c["relation"] = rel
                out[r["stg_id"]] = c
    cands = sorted(out.values(), key=lambda c: (-c["score"], c["household"]["written"]))
    return {"parsed": _show(p), "candidates": cands[:25], "more": max(0, len(cands) - 25),
            "why_none": "" if cands else "no household with this name" + (" and family name" if fam else " and father's name")}


def _show(p):
    return {"first": key(p["first"])[0], "father": key(p["father"])[0] if p["father"] else "",
            "grandfather": key(p["grandfather"])[0] if p["grandfather"] else "", "family": p["family"], "origin": p["origin"]}


def _cand(r, kind, reasons, weak, n_same, fam_both, occs, yr):
    h = household(r)
    score = 3 if kind == "same" else 1
    score += 1 if fam_both else 0
    score -= 1 if weak else 0
    notes = []
    if kind == "same" and n_same > 1 and r["patronymic"]:
        notes.append(f"common name: {n_same} households called {r['name'].title()} di {r['patronymic'].title()}")
        score -= 1 if n_same <= 3 else 2
    elif kind == "same" and r["patronymic"]:
        reasons.append("the only household with this name")
    tc = _trade_check(occs or [], r["trade"])
    if tc:
        if tc[0]:
            reasons.append(f"trade agrees ({tc[1]} ~ {h['trade']})"); score += 2
        else:
            notes.append(f"trade differs: book says {tc[1]}, Catasto {h['trade'] or '—'}")
    if yr and h["age"] is not None and kind != "relative":
        then = h["age"] - (YEAR - yr)
        if then < 15:
            notes.append(f"aged {h['age']} in 1427, so {'not yet born' if then < 0 else f'about {then}'} in {yr}: "
                         "probably not the same person (a son or heir?)")
            if kind == "same":
                score -= 3
        else:
            reasons.append(f"age fits (about {then} in {yr})") if kind == "same" else None
    strength = "strong" if score >= 4 else "possible" if score >= 2 else "weak"
    return {"kind": kind, "household": h, "reasons": reasons, "notes": notes, "score": score, "strength": strength}


# ---------------------------------------------------------------- people in the books
def people() -> list[dict]:
    """Every tagged person (canonical name) in all manuscripts: mentions, years, occupations, lines."""
    al = tags.aliases(); out = {}
    for c in source.collections():
        cid = c["id"]
        if not tags.load(cid):
            continue
        recs = extract.records(cid)
        ent_year = {}
        for r in recs:
            for d in r.get("dates") or []:
                if d.get("year_modern") and r["entry"] not in ent_year:
                    ent_year[r["entry"]] = d["year_modern"]
        book_years = sorted(set(ent_year.values()))
        for r in recs:
            for t in r.get("tags") or []:
                if t["type"] == "person":
                    o = out.setdefault(t["canon"], {"name": t["canon"], "mentions": 0, "approved": 0, "manuscripts": {},
                                                    "years": set(), "book_years": set(), "occupations": set(), "lines": []})
                    o["mentions"] += 1; o["approved"] += t["status"] == "approved"
                    o["manuscripts"][cid] = o["manuscripts"].get(cid, 0) + 1
                    y = ent_year.get(r["entry"])
                    if y:
                        o["years"].add(y)
                    o["book_years"].update(book_years)
                    if len(o["lines"]) < 12:
                        o["lines"].append({"manuscript": cid, "page": r["page"], "folio": r.get("folio") or "", "line": r["line"],
                                           "line_ids": r["line_ids"], "text": r["text"], "translation": r.get("translation") or "",
                                           "year": y})
                if t["type"] == "occupation" and (t.get("attrs") or {}).get("of"):
                    o = out.get(tags.canonical("person", t["attrs"]["of"], al))
                    pend = o if o else out.setdefault("__occ__", {}).setdefault(tags.canonical("person", t["attrs"]["of"], al), set())
                    (o["occupations"] if o else pend).add(t["canon"])
    pend = out.pop("__occ__", {})
    for n, occs in pend.items():
        if n in out:
            out[n]["occupations"].update(occs)
    res = []
    for o in out.values():
        o["years"] = sorted(o["years"]); o["book_years"] = sorted(o["book_years"]); o["occupations"] = sorted(o["occupations"])
        res.append(o)
    return sorted(res, key=lambda o: (-o["mentions"], o["name"]))


def decisions() -> dict:
    return data.read_root("_catasto.json", {})


def decide(person: str, stg_id: str, decision: str | None, note: str = "") -> dict:
    d = decisions()
    if decision in (None, "", "clear"):
        d.get(person, {}).pop(stg_id, None)
        if person in d and not d[person]:
            d.pop(person)
    elif decision in ("same", "relative", "no"):
        d.setdefault(person, {})[stg_id] = {"decision": decision, "note": note, "t": data.now()}
    else:
        raise ValueError("decision must be same, relative, no or clear")
    data.write_root("_catasto.json", d)
    return d.get(person, {})


def matches() -> dict:
    """All people with their candidates and Laura's decisions."""
    if not rows():
        return {"available": False, "file": str(CSV), "people": []}
    dec = decisions(); res = []
    by_id = {r["stg_id"]: r for r in rows()}
    for p in people():
        bk = p["book_years"]
        years = p["years"] or ([bk[len(bk) // 2]] if bk else [])     # the book's middle year if the entry is undated
        m = candidates(p["name"], p["occupations"], years)
        mine = dec.get(p["name"], {})
        shown = {c["household"]["stg_id"] for c in m["candidates"]}
        for sid in mine:                                  # households Laura linked by hand stay visible
            if sid not in shown and sid in by_id:
                c = _cand(by_id[sid], "by hand", ["linked by hand"], False, 1, False, p["occupations"], years[0] if years else None)
                m["candidates"].insert(0, c)
        for c in m["candidates"]:
            c["decision"] = (mine.get(c["household"]["stg_id"]) or {}).get("decision")
        p.update(m); p["years_basis"] = "entries" if p["years"] else ("book" if bk else "")
        p["year_used"] = years[0] if years else None
        res.append(p)
    return {"available": True, "people": res, "year": YEAR,
            "counts": {"people": len(res), "with_candidates": sum(1 for p in res if p["candidates"]),
                       "same": sum(1 for p in res for c in p["candidates"] if c.get("decision") == "same"),
                       "relative": sum(1 for p in res for c in p["candidates"] if c.get("decision") == "relative")}}


def search(q: str, limit: int = 40) -> list[dict]:
    """Free search by hand: words matched against name, father's name and family name (Catasto spelling)."""
    words = [key(w)[0] for w in re.split(r"[\s,]+", q or "") if plain(w).strip() and plain(w).strip() not in ("DI", "DE", "DEL")]
    if not words:
        return []
    out = []
    for r in rows():
        hay = {r["name"], r["patronymic"], r["family_name"]}
        if all(any(h.startswith(w) for h in hay if h) for w in words):
            out.append(household(r))
            if len(out) >= limit:
                break
    return out


def export_rows() -> list[dict]:
    """One row per decided link, for the spreadsheet."""
    m = matches(); out = []
    for p in m["people"]:
        for c in p["candidates"]:
            if c.get("decision") in ("same", "relative"):
                h = c["household"]
                out.append({"Person (account books)": p["name"], "Decision": c["decision"], "Relation": c.get("relation", ""),
                            "Manuscripts": ", ".join(p["manuscripts"]), "Years in books": ", ".join(map(str, p["years"])),
                            "Occupation (books)": ", ".join(p["occupations"]), "Catasto head": h["written"],
                            "Gonfalone": h["gonfalone"], "Trade (Catasto)": h["trade"], "Age 1427": h["age"],
                            "Bocche": h["bocche"], "Total (fl.)": h["total"], "Deductions (fl.)": h["deductions"],
                            "Taxable (fl.)": h["taxable"], "Campioni vol.": h["volume"], "Page": h["page"],
                            "Catasto ID": h["stg_id"], "Reasons": "; ".join(c["reasons"]), "Notes": "; ".join(c["notes"])})
    return out
