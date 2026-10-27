#!/usr/bin/env python3
"""Attach Laura's TEI transcriptions (MPAP 4) to Leggio pages, without overwriting anything.

For each TEI file (matched to a Leggio page by its RS number):
  * readings.tei          = the TEI line, rendered semi-diplomatically (Leggio conventions)
  * readings.claude       = a suggestion: TEI letters + the abbreviation signs Kraken saw
                            (shown in Leggio as an open suggestion: Accept / Reject)
  * readings.tei_expanded = the TEI line with abbreviations expanded (Reading view "expanded")
  * reading/<pid>.json    = expanded text for the Reading view (never replaces a reviewed line)
  * page note             = the description from <quote>, if the page has no note yet
  * page["tei_unmatched"] = TEI lines that no machine line matched (missed by segmentation)
Pages that are finished, in progress or sent to training are skipped unless --force.

Usage (device shell, from HTR_exploration):
  python3 scripts/tei_import.py <tei_folder> RS1384 RS1630 [--dry-run] [--force]
  python3 scripts/tei_import.py <tei_folder> --all [--dry-run]
"""
import sys, os, re, json, glob, time, unicodedata, functools
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CID = "MPAP_4"
PAGES = os.path.join(ROOT, "workspace", CID, "pages")
READING = os.path.join(ROOT, "workspace", CID, "reading")
NS = "{http://www.tei-c.org/ns/1.0}"
PROTECT = {"finished", "sent_to_training", "in_progress"}
A0, A1 = "\x01", "\x02"          # placeholder around supplied letters in the diplomatic string


# ------------------------------------------------------------------ TEI -> lines
def render(el, out):
    """Append (diplomatic, expanded) text for element el to out = [d_list, e_list]."""
    tag = el.tag.replace(NS, "")
    d, e = out
    def text(s):
        if s:
            d.append(s); e.append(s)
    def kids():
        text(el.text)
        for c in el:
            render(c, out)
            text(c.tail)
    if tag in ("quote", "mute", "cb", "space"):
        return
    if tag in ("expan", "abbr"):
        s = "".join(el.itertext())
        d.append(A0 + s + A1); e.append(s)
    elif tag in ("hi", "sup") and (el.get("rend") == "superscript" or tag == "sup"):
        s = "".join(el.itertext())
        m = {"o": "º", "a": "ª"}.get(s, s)
        d.append(m); e.append(m)
    elif tag == "del":
        s = "".join(el.itertext()).replace("\n", " ")
        if s.strip():
            d.append(f"[del: {s}]")
    elif tag == "add":
        sub = [[], []]
        render_children(el, sub)
        s_d, s_e = "".join(sub[0]), "".join(sub[1])
        if s_d.strip():
            d.append(f"[ins: {s_d}]"); e.append(s_e)
    elif tag == "gap":
        d.append("[...]"); e.append("[...]")
    elif tag == "unclear":
        s = "".join(el.itertext())
        d.append((s + "[?]") if s else "[...]"); e.append(s or "[...]")
    elif tag == "metamark":
        if el.get("function") == "leader":
            d.append(" ___ "); e.append(" ")
    elif tag == "g":
        d.append("[?]")
    elif tag == "note":
        d.append("\n"); e.append("\n")
        kids()
        d.append("\n"); e.append("\n")
    else:                       # TEI, text, body, layout, ab, hi, w, pc, rs, name, date, measure, seg, subst, p, head, u
        kids()


def render_children(el, out):
    if el.text:
        out[0].append(el.text); out[1].append(el.text)
    for c in el:
        render(c, out)
        if c.tail:
            out[0].append(c.tail); out[1].append(c.tail)


def resolve_abbr(s):
    """Turn the placeholders into Leggio signs. Returns (string, list of guessed signs)."""
    guesses = []
    def rep(m):
        pre, sup = m.group(1), m.group(2)
        if pre.endswith("br") and sup.startswith("acci"):
            return pre[:-2] + "ƀ"                     # braccia: same sign Kraken uses (to confirm)
        if pre.endswith("p") and sup in ("er", "ar", "ro", "re", "or"):
            return pre[:-1] + "ꝓ"                     # MPAP 4: ꝓ for per/pro
        if pre and sup in ("n", "m"):
            return pre + "̄"                     # nasal: macron on the preceding letter
        if pre:
            guesses.append(pre + "+" + sup)
            return pre + "̄"                     # other: generic macron (flagged)
        return ""
    s = re.sub(r"(\S*?)" + A0 + r"([^" + A1 + r"]*)" + A1, rep, s)
    return unicodedata.normalize("NFC", s), guesses


def tidy(s):
    return re.sub(r"[ \t]+", " ", s).strip()


def parse_tei(path):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    root = ET.fromstring(raw)
    q = root.find(f".//{NS}quote")
    note = tidy(" ".join(q.itertext())) if q is not None else ""
    has_mute = root.find(f".//{NS}mute") is not None
    ncols = max([int(x.get("columns", 1)) for x in root.iter(f"{NS}layout")]
                + [len(list(x.iter(f"{NS}ab"))) for x in root.iter(f"{NS}layout")] + [1])
    out = [[], []]
    render(root, out)
    D, E = "".join(out[0]).split("\n"), "".join(out[1]).split("\n")
    assert len(D) == len(E), path
    lines = []
    for d, e in zip(D, E):
        d, e = tidy(d), tidy(e)
        d, e = re.sub(r"(?<=\w)-$", "", d), re.sub(r"(?<=\w)-$", "", e)
        if not d or re.fullmatch(r"\[?not transcribed\]?\.?", d, re.I):
            continue
        dd, g = resolve_abbr(d)
        lines.append({"dipl": dd, "exp": e, "guess": g})
    return {"note": note, "mute": has_mute, "lines": lines, "ncols": ncols}


# ------------------------------------------------------------------ alignment
SK = str.maketrans({"ꝓ": "p", "ꝑ": "p", "ƀ": "b", "℔": "b", "ß": "s", "𝒹": "d", "⁊": "e", "º": "o", "ƒ": "f",
                    "1": "i", "ſ": "s"})


def skel(s):
    """Letters only: no marks, no spaces, no markup, lower case; abbreviation signs as their base letter."""
    s = re.sub(r"\[(del|ins): [^\]]*\]|\[\.\.\.\]|\[\?\]", "", s or "")
    s = unicodedata.normalize("NFD", s.translate(SK).lower())
    return "".join(c for c in s if c.isalnum())


@functools.lru_cache(maxsize=200000)
def sim(a, b):
    a, b = skel(a), skel(b)
    if not a or not b:
        return 0.0
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i]
        for j in range(1, m + 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1])))
        prev = cur
    return 1 - prev[m] / max(n, m)


def reading_order(lines, width, ncols=1):
    """Machine lines sorted by column, then top to bottom. Columns = 1-D k-means on the x where
    each line starts, with k = the number of columns in the TEI (<layout columns=…>)."""
    items = []
    for l in lines:
        bl = l.get("baseline_before_tei") or l.get("baseline") or []
        if not bl or not (l.get("text") or "").strip():
            continue
        items.append((min(p[0] for p in bl), bl[0][1], l))
    if not items:
        return []
    xs = sorted(x for x, _, _ in items)
    k = max(1, min(ncols, len(xs)))
    cent = [xs[int((i + 0.5) * len(xs) / k)] for i in range(k)]
    for _ in range(20):
        groups = [[] for _ in cent]
        for x in xs:
            groups[min(range(k), key=lambda c: abs(x - cent[c]))].append(x)
        new = [sum(g) / len(g) if g else cent[i] for i, g in enumerate(groups)]
        if new == cent:
            break
        cent = new
    order = sorted(range(k), key=lambda c: cent[c])
    col = lambda x: order.index(min(range(k), key=lambda c: abs(x - cent[c])))
    return [l for _, _, l in sorted(items, key=lambda t: (col(t[0]), t[1]))]


def align(K, T, gap=-0.3, thr=0.45):
    """Needleman-Wunsch: K machine lines, T TEI lines. Returns list of (k_index, t_index) pairs."""
    n, m = len(K), len(T)
    Ks = [k["text"] for k in K]; Ts = [t["dipl"] for t in T]
    S = [[0.0] * (m + 1) for _ in range(n + 1)]; B = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1): S[i][0] = i * gap; B[i][0] = 1
    for j in range(1, m + 1): S[0][j] = j * gap; B[0][j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = sim(Ks[i - 1], Ts[j - 1])
            diag = S[i - 1][j - 1] + (2 * s - 0.8 if s >= thr else -9)
            S[i][j], B[i][j] = max((diag, 0), (S[i - 1][j] + gap, 1), (S[i][j - 1] + gap, 2))
    pairs, i, j = [], n, m
    while i > 0 or j > 0:
        b = B[i][j]
        if i > 0 and j > 0 and b == 0:
            pairs.append((i - 1, j - 1)); i -= 1; j -= 1
        elif i > 0 and (j == 0 or b == 1):
            i -= 1
        else:
            j -= 1
    return pairs[::-1]


MARKS = "ꝓꝑß⁊"
UNIT_SIGNS = "ƀ℔𝒹"


def has_mark(s):
    return any(unicodedata.combining(c) for c in unicodedata.normalize("NFD", s)) or any(c in s for c in MARKS)


def kpattern(w):
    """Regex for the full words a Kraken abbreviation could stand for: cō → co…, don̄a → don…a, ꝓ → per/pro."""
    out, s = "", unicodedata.normalize("NFD", w.lower())
    for c in s:
        if unicodedata.combining(c):
            prev = out[-1:] if out else ""
            out += "[nm]{1,2}" if prev in "aeiouynm" else "[a-z]{1,4}"
        elif c in "ꝓꝑ":
            out += "p(?:er|ro|ar|re|or)?"
        elif c == "⁊":
            out += "e(?:t)?"
        elif c == "ß":
            out += "s(?:er|ar)?"
        elif c.isalnum():
            out += re.escape(c)
        else:
            return None
    return out


def merge_signs(tei, kraken):
    """TEI letters win. Where a TEI word is what a Kraken abbreviation stands for, write Kraken's sign
    (donna + Kraken don̄a → don̄a; con + cō → cō; per + ꝓ → ꝓ). braccia / libbre become ƀ / ℔ when
    Kraken saw a unit sign on the line."""
    kws = [w for w in kraken.split() if has_mark(w)]
    pats = [(w, kpattern(w)) for w in kws]
    unit_seen = any(c in kraken for c in UNIT_SIGNS)
    out = []
    for w in tei.split():
        bare = re.sub(r"[^\w]", "", w.lower())
        rep = None
        if not w.startswith("[") and bare and not has_mark(w):
            for k, p in pats:
                if p and re.fullmatch(p, bare):
                    rep = k
                    break
            if rep is None and unit_seen and bare in ("braccia", "libbre"):
                rep = {"braccia": "ƀ", "libbre": "℔"}[bare]
        elif has_mark(w) and not w.startswith("["):
            for k, p in pats:                     # TEI-made sign: prefer the sign Kraken saw
                if skel(k) == skel(w):
                    rep = k
                    break
        out.append(rep if rep else w)
    return " ".join(out)


# ------------------------------------------------------------------ main
ITEMNUM = re.compile(r"^(?:\d+(?: \d/\d)?|[ivxlc]+º?)\s")


def extend_left(poly, target, band=15):
    """Replace the polygon's left edge (its longest run of points near the leftmost x) by a straight
    vertical edge at x = target, spanning the same height. Keeps the rest of the outline unchanged."""
    pts = [list(p) for p in poly]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    n = len(pts)
    left = min(p[0] for p in pts)
    near = [p[0] <= left + band for p in pts]
    if all(near):
        return [[target, p[1]] if p[0] == left else p for p in pts]
    start = next(i for i in range(n) if not near[i])        # rotate so the list starts outside the run
    pts = pts[start:] + pts[:start]; near = near[start:] + near[:start]
    best, cur = None, None
    for i, f in enumerate(near):
        if f:
            cur = (cur[0], i) if cur else (i, i)
            if best is None or cur[1] - cur[0] > best[1] - best[0]:
                best = cur
        else:
            cur = None
    a, b = best
    run = pts[a:b + 1]
    ys = [p[1] for p in run]
    edge = [[target, min(ys)], [target, max(ys)]]
    if run[0][1] > run[-1][1]:
        edge.reverse()
    return pts[:a] + edge + pts[b + 1:]


def widen_for_item_numbers(K, pairs, T, page):
    """Item numbers sit left of where the model's boxes start. For each matched line whose TEI
    starts with an item number the model did not read, move the box's left edge out to the column's
    left edge (the leftmost line start in that column, less a margin). Old box kept in polygon_before_tei."""
    starts = {}
    for l in K:
        bl = l.get("baseline_before_tei") or l.get("baseline") or []
        if bl:
            starts[l["id"]] = min(p[0] for p in bl)
    n = 0
    xs = sorted(starts.values())
    for i, j in pairs:
        l, t = K[i], T[j]
        if not ITEMNUM.match(t["dipl"]) or ITEMNUM.match(l.get("text") or "") or not l.get("polygon"):
            continue
        x0 = starts.get(l["id"])
        if x0 is None:
            continue
        col = [x for x in xs if abs(x - x0) < 0.12 * (page.get("width") or 1280)]
        target = max(0, min(col) - 12)
        if x0 - target < 8:
            target = max(0, x0 - 30)
        poly = l.get("polygon_before_tei") or l["polygon"]
        if l.get("baseline_before_tei"):
            l["baseline"] = l["baseline_before_tei"]
        left = min(p[0] for p in poly)
        if target >= left:
            continue
        l.setdefault("polygon_before_tei", poly)
        l.setdefault("baseline_before_tei", l["baseline"])
        l["polygon"] = extend_left(poly, target)
        bl = l["baseline"]
        l["baseline"] = [[target, bl[0][1]]] + bl[1:] if bl[0][0] > target else bl
        n += 1
    return n


def tei_files(folder):
    m = {}
    for f in glob.glob(os.path.join(folder, "*.xml")):
        r = re.search(r"_RS(\d+)\.xml$", f)
        if r:
            m["RS" + r.group(1)] = f
    return m


def process(rs, f, dry, force):
    pf = glob.glob(os.path.join(PAGES, rs + "_*.json"))
    if not pf:
        return f"{rs}: no Leggio page"
    page = json.load(open(pf[0], encoding="utf-8"))
    if page.get("status") in PROTECT and not force:
        return f"{rs}: skipped (status {page['status']})"
    tei = parse_tei(f)
    if not tei["lines"]:
        return f"{rs}: no text in TEI (description only)" + (" — has <mute> text" if tei["mute"] else "")
    T = tei["lines"]
    best = None
    for k in sorted({1, 2, 3, tei["ncols"]}):
        Kk = reading_order(page["lines"], page.get("width"), k)
        pk = align(Kk, T)
        score = sum(sim(Kk[i]["text"], T[j]["dipl"]) for i, j in pk)
        if best is None or score > best[0]:
            best = (score, Kk, pk)
    _, K, pairs = best
    matched_t = {j for _, j in pairs}
    sugg = 0
    rf = os.path.join(READING, page["id"] + ".json")
    rd = json.load(open(rf, encoding="utf-8")) if os.path.exists(rf) else {"page": page["id"], "lines": {}}
    for i, j in pairs:
        l, t = K[i], T[j]
        r = l.setdefault("readings", {})
        new = merge_signs(t["dipl"], l["text"])
        r["tei"] = t["dipl"]; r["tei_expanded"] = t["exp"]
        if new.strip() != (l.get("text") or "").strip() and r.get("claude_status") != "accepted":
            r["claude"] = new; r.pop("claude_status", None); sugg += 1
        old = rd["lines"].get(l["id"]) or {}
        if not old.get("reviewed"):
            rd["lines"][l["id"]] = {**old, "expanded": t["exp"], "src": new, "draft": True, "from": "TEI"}
    widened = widen_for_item_numbers(K, pairs, T, page)
    unmatched = [t["dipl"] for j, t in enumerate(T) if j not in matched_t]
    guesses = sorted({g for t in T for g in t["guess"]})
    page["tei_unmatched"] = unmatched
    page["tei_file"] = os.path.basename(f)
    if tei["note"] and not (page.get("note") or "").strip():
        page["note"] = tei["note"]
    ev = (f"attached TEI {os.path.basename(f)}: {len(pairs)} of {len(T)} lines matched, {sugg} suggestion(s)"
          + (f"; {widened} box(es) widened for item numbers" if widened else "")
          + (f"; {len(unmatched)} TEI line(s) with no machine line" if unmatched else ""))
    if not dry:
        page["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        page.setdefault("history", []).append({"t": page["updated"], "event": ev})
        for path, data in ((pf[0], page), (rf, rd)):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            open(tmp, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))
            os.replace(tmp, path)
    rep = f"{rs}: {ev}" + (f"\n   guessed signs: {', '.join(guesses)}" if guesses else "")
    if unmatched:
        rep += "\n   no machine line for: " + " | ".join(unmatched[:12]) + (" …" if len(unmatched) > 12 else "")
    return rep


if __name__ == "__main__":
    a = sys.argv[1:]
    dry, force, allp = "--dry-run" in a, "--force" in a, "--all" in a
    a = [x for x in a if not x.startswith("--")]
    files = tei_files(a[0])
    targets = sorted(files) if allp else a[1:]
    for rs in targets:
        print(process(rs, files[rs], dry, force) if rs in files else f"{rs}: no TEI file", flush=True)
