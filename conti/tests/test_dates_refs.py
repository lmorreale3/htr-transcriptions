import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conti.dates import find, finish, year_only
from conti.refs import refs, kind

def test_dates():
    d = find("Anno dato di xviii di Novēƀre 389 posti a entrata di miniato attore")[0]
    assert (d["day"], d["month"], d["year_written"]) == (18, 11, 1389)
    ds = find("Anno dato di xii dt̄oƀre 388 ƒ x e di vii di gen̄āio 388 ƒ dieci ebbe miniato loro")
    assert [(x["day"], x["month"], x["year_written"]) for x in ds] == [(12, 10, 1388), (7, 1, 1388)]
    f = finish(ds[1], None, "florentine"); assert f["year_modern"] == 1389 and f["iso_modern"] == "1389-01-07"
    f = finish(ds[0], None, "florentine"); assert f["year_modern"] == 1388
    d = find("Anne dato 𝒹i xviii di di cēƀre 389 ƒ uno 𝒹 āƀ aentrata detta ac̄")[0]
    assert (d["day"], d["month"], d["year_written"]) == (18, 12, 1389)
    d = find("Anno dato 𝒹 29 di novēƀe 389 ebbe miniato detto a sua entrata ac̄")[0]
    assert (d["day"], d["month"]) == (29, 11)
    d = find("E de avere adi xxviii di giugnº 1420 ƒ uno ꝓ")[0]
    assert (d["day"], d["month"], d["year_written"]) == (28, 6, 1420)
    d = find("Anno dato di xv di mãzo 388 ƒ ii ß42")[0]
    f = finish(d, None, "florentine"); assert f["year_modern"] == 1389
    d = find("E piu adi x di marzo 1460 ebbi")[0]; assert finish(d, None, "florentine")["year_modern"] == 1461
    d = find("Anno dato di xiii dluglio 38 9ƒ uno")[0]; assert (d["day"], d["month"]) == (13, 7)
    f = finish(find("adi 13 di marzo")[0], 1388, "florentine")
    assert f["year_inferred"] and f["year_written"] == 1388 and f["year_modern"] == 1389
    assert find("piero mazei lascia la casa") == []
    assert year_only("mcclxxxviii") == 1288 and year_only("1458") == 1458 and year_only("1465.") == 1465

def test_refs():
    r = refs("Guelfo di Nuto da fiesole de dare alibro detto ac̄ 41 E a libro giallo di")
    assert r[0]["folios"] == [41] and r[0]["book"] == "libro detto"
    r = refs("di firenze deondare alibro detto acār 41 Ealibro giallo ac̄ 312")
    assert [x["folios"] for x in r] == [[41], [312]] and r[1]["book"] == "libro giallo"
    r = refs("E a libro rosso di deo acār 72/⁊/73/74/105 ⁊ a libro giallo c̄ 316 ƒclxxviº")
    assert r[0]["folios"] == [72, 73, 74, 105] and r[0]["book"] == "libro rosso di deo" and r[1]["folios"] == [316]
    r = refs("A me dato di xvi di novēƀ 389 ƒ trenta 𝒹 cōt a entrata di miniato c̄ 14 ƒ xxx")
    assert r[0]["folios"] == [14] and r[0]["book"] == "entrata di miniato"
    r = refs("Cēni ⁊ figluoli da villanuova deondare al memoriale delle rede ac̄ 38 pc̄ ℔ vi")
    assert r[0]["folios"] == [38] and r[0]["book"].startswith("memoriale")

def test_kind():
    assert kind("francescho di piero bicchieraio ī borgo salorēzo de dare alibro detto ac̄ 43") == "debit"
    assert kind("Cēni ⁊ figluoli deondare al memoriale") == "debit"
    assert kind("Anno dato di xii di maggio 389") == "credit"
    assert kind("E deono avere adi xij di genaio 1419 ƒ due") == "credit"
    assert kind("Resta addare ꝓ lacchatto del sale ƒ 21") == "balance"
    assert kind("la detta cappella") is None
