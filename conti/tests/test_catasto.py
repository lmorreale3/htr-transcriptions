import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conti import catasto as C


def test_spelling():
    assert C.key("Francescho")[0] == "FRANCESCO"
    assert C.key("Jacopo")[0] == "IACOPO"
    assert C.key("Lionardo")[0] == "LEONARDO"
    assert C.key("Bartolomeo")[0] == "BARTOLOMEO"
    assert C.key("Gualterotto")[0] == "GUALTEROTT"          # the Catasto keeps 10 letters


def test_short_forms():
    v = dict(C.variants("Nanni"))
    assert "GIOVANNI" in v and v["NANNI"] == ""
    assert "NANNI" in dict(C.variants("Giovanni"))
    assert "DOMENICO" in dict(C.variants("Domenicuccio"))


def test_parse():
    p = C.parse("Pagolo di Jacopo dell'Aressa")
    assert (p["first"], p["father"]) == ("Pagolo", "Jacopo") and "DELLARESSA" in p["family"]
    p = C.parse("Domenicuccio d'Andrea")
    assert p["father"] == "Andrea" and not p["family"]
    p = C.parse("Tommaso di ser Francecho Masi")
    assert p["father"] == "Francecho" and p["family"] == ["MASI"]
    p = C.parse("Doffo di Giovanni de' Bardi")
    assert "BARDI" in p["family"]
    p = C.parse("Michele da Nobi")
    assert p["origin"] == "Nobi" and not p["family"]
    p = C.parse("Giovanni di Matteo di Caronbello")
    assert p["grandfather"] == "Caronbello"


def test_trade():
    assert C._trade_check(["notaio"], "21") == (True, "notaio")
    assert C._trade_check(["vinattiere"], "133") == (True, "vinattiere")    # employee of a wine dealer
    assert C._trade_check(["vinattiere"], "24")[0] is False
    assert C._trade_check([], "21") is None


def test_candidates_on_the_file():
    if not C.rows():
        return
    r = C.candidates("Michele di Fazio", ["notaio"], [1388])
    best = r["candidates"][0]
    assert best["kind"] == "same" and best["strength"] == "strong" and best["household"]["trade_code"] == "21"
    r = C.candidates("Pagolo di Jacopo dell'Aressa", [], [1388])
    rel = [c for c in r["candidates"] if c["kind"] == "relative"]
    assert rel and rel[0]["household"]["family_name"] == "DELLARESSA"
    assert C.candidates("Donato", [], [1388])["candidates"] == []
