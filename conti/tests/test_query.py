"""Query engine on synthetic records (no Leggio workspace needed)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conti import query

def rec(key, text, tags, dates=(), kind=None, entry="p#1"):
    return {"key": key, "manuscript": "X", "page": "p", "line": 1, "entry": entry, "text": text, "expanded": "", "translation": "",
            "sum": "", "date": "", "kind": kind, "tags": [dict(t, canon=t.get("canon", t["name"]), status=t.get("status", "approved"), id=t["name"]) for t in tags],
            "dates": list(dates), "refs": [], "amount_final": None, "flag": False, "line_ids": "l1", "status": "Finished"}

R = [rec("a", "Guelfo di Nuto da fiesole de dare", [{"type": "person", "name": "Guelfo di Nuto", "attrs": {"role": "debtor"}}, {"type": "place", "name": "Fiesole"}], kind="debit"),
     rec("b", "Anno dato di xii di maggio 389", [{"type": "person", "name": "Miniato", "attrs": {"role": "recipient"}}],
         dates=[{"year_modern": 1389, "year_written": 1389, "iso_modern": "1389-05-12", "month": 5}], kind="credit"),
     rec("c", "Cēni da villanuova", [{"type": "person", "name": "Ceni", "status": "suggested"}, {"type": "place", "name": "Villanuova"}], entry="p#2")]

def run(conds, **kw):
    ctx = {"approved_only": kw.get("approved_only", False), "page_order": {}, "entry_tags": {"p#1": R[0]["tags"] + R[1]["tags"], "p#2": R[2]["tags"]}}
    return [r["key"] for r in R if all(query._cond(r, c, ctx) for c in conds)]

def test_tags():
    assert run([{"field": "place", "op": "is", "value": "fiesole"}]) == ["a"]
    assert run([{"field": "person", "op": "exists", "attr": {"role": "debtor"}}]) == ["a"]
    assert run([{"field": "place", "op": "exists", "scope": "entry"}]) == ["a", "b", "c"]
    assert run([{"field": "person", "op": "exists"}], approved_only=True) == ["a", "b"]

def test_text_and_dates():
    assert run([{"field": "text", "op": "contains", "value": "ceni"}]) == ["c"]      # macron ignored
    assert run([{"field": "year", "op": "between", "value": [1389, 1389]}]) == ["b"]
    assert run([{"field": "date", "op": "between", "value": ["1389-05", "1389-05"]}]) == ["b"]
    assert run([{"field": "kind", "op": "is", "value": "debit"}]) == ["a"]

def test_group():
    rows = [r for r in R]
    g = {x["value"]: x["rows"] for x in query.group(rows, "place", "lines")}
    assert g == {"Fiesole": 1, "Villanuova": 1}
