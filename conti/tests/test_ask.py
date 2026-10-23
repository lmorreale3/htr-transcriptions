import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conti import analyze, ledger


def T(id, debtors, fl=None, li=None, kind="debt", year=None, creditor=("Heirs", "assumed (account holder)"), checked=False, problems=False):
    return {"id": id, "kind": kind, "manuscript": "X", "page": "p", "entry": id.split("/")[0], "lines": [1], "keys": [], "line_ids": "l1",
            "debtors": [{"name": n, "type": "person", "status": "suggested", "occupations": occ, "occupation_basis": "same entry" if occ else ""}
                        for n, occ in debtors],
            "creditor": {"name": creditor[0], "basis": creditor[1]}, "florins": fl, "lire": li, "display": "", "sum_written": "",
            "sum_checked": checked, "sum_problems": problems, "tags_checked": False, "date": "", "year": year,
            "year_written": None, "year_inferred": False, "text": "", "translation": ""}


def ctx(rows):
    return {"steps": {"tx": {"type": "transactions", "rows": rows}}, "tx": {}}


ROWS = [T("e1/1", [("A", ["vinattiere"])], fl=100, year=1388), T("e2/1", [("B", ["vinattiere"])], fl=20, year=1389),
        T("e3/1", [("C", ["sarto"])], fl=50, year=1388), T("e4/1", [("D", ["sarto"])], fl=60, year=1389),
        T("e5/1", [("E", []), ("F", [])], fl=10, li=4), T("e5/2", [("E", []), ("F", [])], fl=2, kind="payment")]


def test_florins_a_fiorino_and_lire_apart():
    assert ledger.florins_of({"florins": 2, "soldi": 29, "denari": 0, "florin_parts": True}) == 3.0
    assert ledger.florins_of({"florins": 2, "soldi": 5, "florin_parts": False}) == 2.0
    assert ledger.lire_of({"lire_decimal": 1.5}) == 1.5 and ledger.lire_of(None) is None


def test_payment_lines():
    for s in ("anno dato di xii di maggio 389", "a me dato di vi dottobre", "amone dato di xiii di febraio", "a mone date di xviiii"):
        assert ledger._PAY.search(s), s
    assert not ledger._PAY.search("pagolo di jacopo de dare a libro detto")


def test_aggregate_median_and_consistency():
    r = analyze._aggregate({"from": "tx", "by": "occupation", "currency": "florins", "rank_by": "median", "over": "year"}, {}, ctx(ROWS[:4]))
    assert [x["value"] for x in r["rows"]] == ["vinattiere", "sarto"]           # medians 60 vs 55
    cons = {c["value"]: c for c in r["consistency"]}
    assert cons["vinattiere"]["periods_first"] == 1 and cons["sarto"]["periods_first"] == 1   # each leads one year: not consistent
    r = analyze._aggregate({"from": "tx", "by": "occupation", "currency": "florins", "rank_by": "total"}, {}, ctx(ROWS[:4]))
    assert r["rows"][0]["value"] == "vinattiere" and r["rows"][0]["florins_total"] == 120


def test_joint_debt_shared_and_people_per_debtor():
    r = analyze._aggregate({"from": "tx", "by": "debtor", "currency": "florins", "rank_by": "total"}, {}, ctx(ROWS[4:5]))
    by = {x["value"]: x for x in r["rows"]}
    assert by["E"]["florins_total"] == 5 and by["E"]["people"] == 1


def test_network_payments_not_added_to_debts():
    g = analyze._network({"from": "tx", "top": 50}, {}, ctx(ROWS))
    n = {x["id"]: x for x in g["nodes"]}
    assert n["E"]["owed_florins"] == 5 and n["E"]["paid_florins"] == 1 and n["E"]["paid_n"] == 1
    assert n["Heirs"]["role"] == "lender" and n["Heirs"]["assumed"] and n["Heirs"]["owed_to_florins"] == 240
    e = next(x for x in g["edges"] if x["source"] == "E")
    assert e["n"] == 1 and e["paid_n"] == 1 and e["target"] == "Heirs"


def test_plan_validation():
    for bad in ({}, {"steps": [{"id": "a", "op": "nope"}]}, {"steps": [{"id": "a", "op": "aggregate", "from": "zz"}]}):
        try:
            analyze.validate(bad)
        except analyze.PlanError:
            continue
        raise AssertionError(bad)
