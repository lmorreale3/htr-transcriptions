import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conti import places

G = [{"name": "Santa Maria Maggiore", "lat": 43.77, "lon": 11.25, "confidence": "secure", "kind": "parish church"},
     {"name": "Chiasso de' Buoi", "lat": None, "lon": None, "confidence": "uncertain", "kind": "lane"},
     {"name": "Santo Stefano a Campi", "aliases": [], "lat": 43.82, "lon": 11.13, "confidence": "secure", "kind": "pieve"}]

def test_anchor_most_specific_located():
    ix = places.index(G)
    a = places.anchor({"location": {"popolo": "Santa Maria Maggiore", "luogo": "Chiasso de' Buoi"}}, ix)
    assert a["place"] == "Santa Maria Maggiore" and a["level"] == "popolo"      # lane not located → parish
    a = places.anchor({"location": {"popolo": "Santo Stefano a Campi (pieve)"}}, ix)
    assert a and a["place"] == "Santo Stefano a Campi"
    assert places.anchor({"location": {"luogo": "Gaville"}}, ix) is None
