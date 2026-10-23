import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conti import network

def H(id, owner, confini, place="Santa Maria Maggiore", related=()):
    return {"id": id, "manuscript": "X", "kind": "casa", "location": {"popolo": place}, "owner": {"canon": owner, "name": owner},
            "former_owners": [], "occupants": [], "related": list(related), "status": "suggested", "page": "p",
            "confini": [dict(c, canon=c["name"]) for c in confini]}

def test_neighbourhood_links():
    a = H("h1", "Deo", [{"side": 1, "name": "via", "type": "street"}, {"side": 2, "name": "Marchi", "type": "person"}])
    b = H("h2", "Deo", [{"side": 1, "name": "via", "type": "street"}, {"side": 3, "name": "Marchi", "type": "person"}])
    c = H("h3", "Deo", [{"side": 2, "name": "Deo", "type": "person"}], related=[{"id": "h1", "relation": "borders"}])
    nb = network.neighbourhood([a, b, c])
    links = {(l["a"], l["b"]): l for l in nb["links"]}
    assert links[("h1", "h2")]["shared"] == ["Marchi"]          # unnamed 'via' does not join holdings
    assert links[("h1", "h3")]["related"] == ["borders"]
    assert nb["holdings"][0]["sides"]["2"][0]["name"] == "Marchi"

def test_people_cooccurrence():
    rows = [{"key": "k1", "entry": "e1", "page": "p", "tags": [
        {"type": "person", "canon": "A", "status": "approved", "attrs": {"role": "debtor"}},
        {"type": "place", "canon": "Sesto", "status": "approved", "attrs": {"of": "A", "relation": "origin"}}]},
        {"key": "k2", "entry": "e1", "page": "p", "tags": [{"type": "person", "canon": "B", "status": "suggested", "attrs": {}}]}]
    g = network.people(rows)
    kinds = {(e["source"], e["target"]): e["kind"] for e in g["edges"]}
    assert kinds[("person:A", "place:Sesto")] == "origin"
    assert ("person:A", "person:B") in kinds
    assert network.people(rows, approved_only=True)["edges"] and all("B" not in e["target"] for e in network.people(rows, approved_only=True)["edges"])

def test_gephi_zip():
    import zipfile, io
    z = zipfile.ZipFile(io.BytesIO(network.to_gephi_zip({"nodes": [{"id": "a", "label": "A", "type": "person", "count": 1}], "edges": []})))
    assert set(z.namelist()) == {"nodes.csv", "edges.csv", "README.txt"}
