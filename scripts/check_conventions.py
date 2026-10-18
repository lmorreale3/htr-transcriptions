#!/usr/bin/env python3
"""Check Leggio pages against a collection's conventions (workspace/<cid>/conventions.json).

  python3 scripts/check_conventions.py MPAP_4                    # every page
  python3 scripts/check_conventions.py MPAP_4 RS1141 RS1142      # pages whose id starts with these
  python3 scripts/check_conventions.py MPAP_4 --status finished,sent_to_training
  python3 scripts/check_conventions.py MPAP_4 RS1141 --suggestions   # check Claude's suggestions instead of the text
  python3 scripts/check_conventions.py --file suggestions.json      # check a suggestions file before applying it
Read-only: nothing is changed.
"""
import argparse, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("LEGGIO_ROOT", str(ROOT))
sys.path.insert(0, str(ROOT / "leggio"))
from leggio import conventions, store  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("collection", nargs="?")
ap.add_argument("pages", nargs="*")
ap.add_argument("--status")
ap.add_argument("--suggestions", action="store_true")
ap.add_argument("--file")
a = ap.parse_args()

def show(label, hits, text):
    for h in hits:
        to = f" → {h['to']!r}" if "to" in h else ""
        print(f"  {label:6} [{h['level']}] {h['rule']}: {h['match']!r}{to}   ({h['msg']})")

total = 0
if a.file:
    d = json.load(open(a.file, encoding="utf-8"))
    rules = conventions.compile_rules(conventions.load(d["collection"]))
    for lid, t in d["lines"].items():
        hs = conventions.check(t, rules); total += len(hs); show(lid, hs, t)
else:
    rules = conventions.compile_rules(conventions.load(a.collection))
    st = set(a.status.split(",")) if a.status else None
    for f in sorted((store.coll_dir(a.collection) / "pages").glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        if a.pages and not any(p["id"].startswith(x) for x in a.pages): continue
        if st and p["status"] not in st: continue
        out = []
        for l in p["lines"]:
            t = (l.get("readings") or {}).get("claude") if a.suggestions else l.get("text")
            if not t: continue
            hs = conventions.check(t, rules, l.get("conv_ignore"))
            if hs: out.append((l["id"], hs, t))
        if out:
            print(f"{p['id']}  ({p['status']})")
            for lid, hs, t in out:
                total += len(hs); show(lid, hs, t)
print(f"{total} flag(s)")
