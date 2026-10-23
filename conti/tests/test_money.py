import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conti.money import parse, trailing, mentions
from conti.numbers import roman, word_number

def test_roman():
    assert roman("xviiiiº") == 19 and roman("clxxxxiii") == 193 and roman("dccclxxxx") == 890
    assert roman("mccclxxxvi") == 1386 and roman("iij") == 3 and roman("ix") == 9 and roman("di") is None

def test_words():
    assert word_number("trenta") == 30 and word_number("centosette") == 107 and word_number("trecento") == 300
    assert word_number("dieci") == 10 and word_number("dugento") == 200 and word_number("casa") is None

def P(s): return parse(s)

def test_full():
    a = P("ƒ ii ℔x ß xii 𝒹 vi pc̄")
    assert (a.florins, a.lire, a.soldi, a.denari, a.piccioli) == (2, 10, 12, 6, True) and not a.problems

def test_split_sublines():
    a = P("℔ v | ß iiiiº | 𝒹 iiiiº")
    assert (a.lire, a.soldi, a.denari) == (5, 4, 4)

def test_attached_signs():
    a = P("ßxviii 𝒹ii"); assert (a.soldi, a.denari) == (18, 2)
    a = P("⫳5 ß14 𝒹"); assert (a.lire, a.soldi, a.denari) == (5, 14, None) and not a.problems

def test_problems():
    assert any(c == "no-sign" for c, _ in P("1 ƒ xxiiiiº").problems)
    assert any(c == "twice" for c, _ in P("ƒ ii ƒ 1 ℔ ii ß ii 𝒹 viii").problems)
    assert P("di deo").empty
    assert any(c == "word" for c, _ in P("lesore 𝒹x ßxnio").problems)

def test_dotted():
    a = P("⫳ 1.14"); assert (a.lire, a.soldi) == (1, 14)

def test_trailing():
    raw, _ = trailing("Cēni ⁊ figluoli da villanuova deondare al memoriale delle rede ac̄ 38 pc̄ ℔ vi")
    assert raw == "pc̄ ℔ vi"
    assert trailing("Niccolo di ß bartolo da mangone de dare alibro detto acār 44") is None

def test_mentions():
    m = mentions("Anno dato di iiiiº di gugno 389 ƒ due 𝒹i cōt aentrata di miniato ac̄ x1")
    assert m[0]["amount"].florins == 2
    m = mentions("rede carta ꝑ ß lapo mazei di 3 di gen̄aio 1389 ƒ x")
    assert len(m) == 1 and m[0]["amount"].florins == 10
    m = mentions("decto quaderno di chasa a  60 ī tucto lire octo ß 10___𝓎 8 β 10 𝒹")
    assert [x["amount"].lire for x in m] == [8, 8]

def test_florin_parts():
    a = P("ƒ lxxxvii ß xxii 𝒹 xi aff")
    assert a.florins == 87 and a.soldi == 22 and a.florin_parts and a.a_fiorino and a.lsd_denari() is None
    assert not [c for c, _ in a.problems]
    a = P("ƒ dxxvii ß xxiii 𝒹 iii pc̄"); assert a.florins == 527
    raw, _ = trailing("nella bottegha di borgo san lorēzo stimate ƒ dxxvii ß xxiii 𝒹 iii pc̄"); assert raw.startswith("ƒ dxxvii")
