/* Map (#/map): holdings tethered to places with known coordinates (parish churches, streets, villages), coloured by owner
   at the slider date; Places (#/places): the gazetteer, with sources and confidence, editable and placeable on the map. */
const MAP = { m: null, manuscripts: null, base: true, placing: null, t: null };
const KIND1 = { casa: "c", palagio: "P", "casa con bottega": "b", bottega: "b", casolare: "c", podere: "p", "pezzo di terra": "t", purgo: "u", vigna: "v" };

async function viewMap(placing) {
  if (!MAP.manuscripts) MAP.manuscripts = S.colls.map((c) => c.id);
  MAP.placing = placing || null;
  const d = await api("/api/map", { method: "POST", body: { manuscripts: MAP.manuscripts } });
  $("#main").innerHTML = `<div class="row"><h1>Map</h1>
      <span class="small muted">${d.holdings.length - d.unanchored.length} of ${d.holdings.length} holdings placed · each is tethered to the most specific place with known coordinates (street, parish church, village)</span>
      <span class="spacer"></span><a class="btn small" href="#/places">Places & sources</a></div>
    ${MAP.placing ? `<div class="card" style="margin:8px 0;border-color:var(--accent)"><b>Click on the map where “${esc(MAP.placing)}” was.</b> <button class="btn small" id="mpcancel">Cancel</button></div>` : ""}
    <div class="mapwrap"><div class="netbox card"><div class="tbar" id="mtbar"></div><div id="lmap"></div><div class="olegend" id="mlegend"></div></div>
      <aside class="card netside" id="mpanel"><div class="small muted">Squares are holdings (c casa, P palagio, b bottega, p podere, t pezzo di terra), drawn around the place they are tethered to. Their colour is the owner at the date on the slider. Dotted lines join holdings that name the same neighbour or each other.</div>
      <div class="small" style="margin-top:8px"><b>Pins:</b> filled = position secure (existing church or settlement); hollow = approximate (a lost church placed on today's piazza, a street's midpoint, or placed by you).</div>
      ${d.unanchored.length ? `<div class="small" style="margin-top:8px"><b>Not placed yet</b> (no located place): ${d.unanchored.map((u) => `${esc(u.id)} <span class="muted">(${esc(u.place)})</span>`).join(", ")} — <a href="#/places">add coordinates</a></div>` : ""}
      <label class="small" style="display:block;margin-top:8px"><input type="checkbox" id="mbase" ${MAP.base ? "checked" : ""}> modern street map underneath (OpenStreetMap; needs internet)</label></aside></div>`;
  if ($("#mpcancel")) $("#mpcancel").onclick = () => (location.hash = "#/places");
  if (MAP.m) { MAP.m.remove(); MAP.m = null; }
  const m = L.map("lmap", { zoomSnap: 0.5, preferCanvas: false });
  MAP.m = m;
  const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap contributors" });
  if (MAP.base) tiles.addTo(m);
  $("#mbase").onchange = (e) => { MAP.base = e.target.checked; if (MAP.base) tiles.addTo(m); else m.removeLayer(tiles); };
  const anchors = d.anchors;
  const pts = anchors.map((a) => [a.lat, a.lon]);
  if (pts.length) m.fitBounds(pts, { padding: [40, 40] }); else m.setView([43.7714, 11.2542], 13);
  const hById = {}; d.holdings.forEach((h) => (hById[h.id] = h));
  const layer = L.layerGroup().addTo(m);
  const sqMarkers = {};
  // pins
  anchors.forEach((a) => {
    const pin = L.circleMarker([a.lat, a.lon], { radius: 6, weight: 2, color: "#2b2420", fillColor: a.confidence === "secure" ? "#2b2420" : "#fff",
      fillOpacity: 1, dashArray: a.confidence === "secure" ? null : "3 2" }).addTo(m);
    pin.bindTooltip(`${a.place} · ${a.holdings.length}`, { direction: "top", offset: [0, -6] });
    pin.on("click", () => anchorPanel(a, hById));
  });
  // squares around each pin, in screen space so they stay readable at any zoom
  const draw = () => {
    layer.clearLayers();
    const pos = {};
    anchors.forEach((a) => {
      const c = m.latLngToLayerPoint([a.lat, a.lon]);
      a.holdings.forEach((id, i) => {
        const ring = i < 6 ? 0 : i < 18 ? 1 : 2, k = ring === 0 ? i : ring === 1 ? i - 6 : i - 18, n = ring === 0 ? Math.min(6, a.holdings.length) : ring === 1 ? Math.min(12, a.holdings.length - 6) : a.holdings.length - 18;
        const R = 34 + ring * 28, ang = -Math.PI / 2 + (2 * Math.PI * k) / Math.max(1, n) + ring * 0.3;
        const p = m.layerPointToLatLng(L.point(c.x + R * Math.cos(ang), c.y + R * Math.sin(ang)));
        pos[id] = p;
        L.polyline([[a.lat, a.lon], p], { color: "#6b5f55", weight: 1, opacity: 0.6, interactive: false }).addTo(layer);
      });
    });
    d.links.forEach((l) => {
      if (pos[l.a] && pos[l.b]) L.polyline([pos[l.a], pos[l.b]], { color: "#2f6f73", weight: 1.5, dashArray: "2 4", opacity: 0.8 })
        .bindTooltip(l.shared.length ? `both border ${l.shared.join(", ")}` : (l.related || []).join(", ")).addTo(layer);
    });
    Object.keys(pos).forEach((id) => {
      const h = hById[id];
      const mk = L.marker(pos[id], { icon: L.divIcon({ className: "", html: `<div class="msq ${h.status}" data-id="${esc(id)}">${KIND1[h.kind] || "·"}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] }) }).addTo(layer);
      mk.bindTooltip(`${h.kind || "holding"} ${h.id}`, { direction: "top", offset: [0, -10] });
      mk.on("click", () => { MAP.sel = h; mapHoldingPanel(h); });
      sqMarkers[id] = mk;
    });
    paint();
  };
  // time
  const hs = d.holdings;
  NB.range = timeRange(hs);
  const months = Math.round((NB.range[1] - NB.range[0]) / (30.44 * 864e5));
  const toT = (i) => { const x = new Date(NB.range[0]); return Date.UTC(x.getUTCFullYear(), x.getUTCMonth() + +i, 15); };
  if (!NB.t || NB.t < NB.range[0] || NB.t > NB.range[1]) NB.t = Date.UTC(1387, 6, 15);
  $("#mtbar").innerHTML = `<button class="btn small" id="mplay">▶</button><input type="range" id="mslide" min="0" max="${months}" value="${Math.round((NB.t - NB.range[0]) / (30.44 * 864e5))}" style="flex:1">
    <b id="mlabel" class="small" style="min-width:230px"></b>`;
  hs.forEach((h) => (h.timeline || []).forEach((p) => p.role === "owner" && ownerColour(ownerKey(p))));
  const panel = getComputedStyle(document.body).getPropertyValue("--panel").trim() || "#fffdf8";
  function paint() {
    $("#mlabel").textContent = dLabel(NB.t);
    const present = new Set();
    Object.entries(sqMarkers).forEach(([id, mk]) => {
      const el = mk.getElement() && mk.getElement().querySelector(".msq"); if (!el) return;
      const h = hById[id], st = stateAt(h, NB.t), key = st.owner ? ownerKey(st.owner) : null, col = ownerColour(key);
      if (key) present.add(key);
      el.style.background = col ? d3.interpolateRgb(panel, col)(st.owner.sure ? 0.75 : 0.45) : panel;
      el.style.borderColor = col || "#9a8f84";
      el.title = key ? `${h.id}: ${key}` : `${h.id}: owner not known at this date`;
    });
    const keys = Object.keys(OWNER_COL).filter((k) => hs.some((h) => (h.timeline || []).some((p) => p.role === "owner" && ownerKey(p) === k)));
    const shown = keys.filter((k) => present.has(k));
    $("#mlegend").innerHTML = `<b class="small">Owners at this date</b>` + shown.map((k) => `<span class="on"><i style="background:${OWNER_COL[k]}"></i>${esc(k)}</span>`).join("")
      + `<span><i style="background:var(--panel);border:1px solid #9a8f84"></i>not known at this date</span>`;
    if (MAP.sel) mapHoldingPanel(MAP.sel);
  }
  $("#mslide").oninput = (e) => { NB.t = toT(e.target.value); paint(); };
  let timer = null;
  $("#mplay").onclick = () => {
    if (timer) { clearInterval(timer); timer = null; $("#mplay").textContent = "▶"; return; }
    $("#mplay").textContent = "❚❚";
    timer = setInterval(() => { const sl = $("#mslide"); if (!sl) return clearInterval(timer); sl.value = +sl.value >= +sl.max ? 0 : +sl.value + 1; NB.t = toT(sl.value); paint(); }, 220);
  };
  m.on("zoomend", draw);
  draw();
  if (MAP.placing) {
    m.getContainer().style.cursor = "crosshair";
    m.once("click", async (ev) => {
      const basis = prompt(`Place “${MAP.placing}” here (${ev.latlng.lat.toFixed(5)}, ${ev.latlng.lng.toFixed(5)}).\nHow do you know? (basis, e.g. "Buonsignori 1584; behind S. Maria Maggiore")`, "placed on the map by Laura");
      if (basis === null) return;
      await api("/api/gazetteer", { method: "POST", body: { action: "place", name: MAP.placing, lat: ev.latlng.lat, lon: ev.latlng.lng, basis } });
      location.hash = "#/map";
    });
  }
}

function mapHoldingPanel(h) {
  holdingPanel(h, "#mpanel");
  const a = h.anchor;
  if (a) $("#mpanel").insertAdjacentHTML("afterbegin", `<div class="small" style="margin-bottom:4px">Tethered to <b>${esc(a.place)}</b> (${esc(a.kind)}, ${esc(a.confidence)}) from its ${esc(a.level)} “${esc(a.as_written)}”</div>`);
  $("#mpanel").insertAdjacentHTML("beforeend", ` <a class="btn small" href="#/neighbourhoods/${encodeURIComponent(h.place)}">Relational diagram of ${esc(h.place.split(" › ").pop())} →</a>`);
}

function anchorPanel(a, hById) {
  MAP.sel = null;
  $("#mpanel").innerHTML = `<div class="small muted">${esc(a.kind)} · position ${esc(a.confidence)}</div><h2 style="margin:2px 0">${esc(a.place)}</h2>
    <div class="small">${a.holdings.length} holding(s) tethered here:</div>
    <ul class="small">${a.holdings.map((id) => { const h = hById[id]; return `<li>${esc(id)} ${esc(h.kind || "")} <span class="muted">${esc(h.place)}</span></li>`; }).join("")}</ul>
    <a class="btn small" href="#/places">Source and position →</a>`;
}

/* ------------------------------------------------------------------ places / gazetteer */
async function viewPlaces() {
  const g = await api("/api/gazetteer");
  const missing = Object.keys(g.used).filter((k) => k.startsWith("(not in gazetteer)"));
  $("#main").innerHTML = `<div class="row"><h1>Places</h1><span class="spacer"></span><a class="btn small" href="#/map">Map →</a></div>
    <p class="muted small">Places that can tether holdings to topography. <b>secure</b>: an existing church or settlement whose position a source gives; <b>approximate</b>: placed relative to a known place (a lost church on today's piazza, a street's midpoint) or by you; <b>uncertain</b>: not located. Claude's research is marked “?” until you approve it. “Place on map” lets you click the spot yourself (e.g. from the Buonsignori map).</p>
    <table><thead><tr><th>Place</th><th>Kind</th><th>Position</th><th>Lat, lon</th><th>Basis and source</th><th class="num">Holdings</th><th></th></tr></thead><tbody>
    ${g.places.map((p, i) => `<tr data-i="${i}"><td><b>${esc(p.name)}</b>${p.status === "suggested" ? ' <span class="sg">?</span>' : ' <span class="ok">✓</span>'}${p.modern_name ? `<div class="small muted">today: ${esc(p.modern_name)}</div>` : ""}${p.within ? `<div class="small muted">${esc(p.within)}</div>` : ""}</td>
      <td class="small">${esc(p.kind || "")}</td>
      <td class="small"><select data-conf="${i}">${["secure", "approximate", "uncertain"].map((c) => `<option ${p.confidence === c ? "selected" : ""}>${c}</option>`).join("")}</select></td>
      <td class="small nowrap">${p.lat != null ? `${(+p.lat).toFixed(5)}, ${(+p.lon).toFixed(5)}` : "—"}</td>
      <td class="small">${esc(p.basis || "")}${p.note ? `<div class="muted">${esc(p.note)}</div>` : ""}${p.source ? ` <a href="${esc(p.source)}" target="_blank" rel="noopener">source ↗</a>` : ""}</td>
      <td class="num">${(g.used[p.name] || []).length}</td>
      <td class="nowrap">${p.status === "suggested" ? `<button class="btn small ok" data-ap="${i}">✓</button>` : ""}<a class="btn small" href="#/map/place/${encodeURIComponent(p.name)}">Place on map</a></td></tr>`).join("")}</tbody></table>
    ${missing.length ? `<h2>Named in holdings but not in the list</h2><div class="small">${missing.map((k) => `<span class="chip" data-add="${esc(k.replace("(not in gazetteer) ", ""))}">+ ${esc(k.replace("(not in gazetteer) ", ""))} <span class="n">${g.used[k].length}</span></span>`).join(" ")}</div>
      <p class="small muted">Click one to add it; then place it on the map. (Holdings already fall back to their parish or village when a lane is not located.)</p>` : ""}`;
  const P = g.places;
  document.querySelectorAll("[data-ap]").forEach((b) => b.onclick = async () => { await api("/api/gazetteer", { method: "POST", body: { action: "approve", name: P[+b.dataset.ap].name } }); viewPlaces(); });
  document.querySelectorAll("[data-conf]").forEach((s) => s.onchange = async () => { await api("/api/gazetteer", { method: "POST", body: { action: "edit", name: P[+s.dataset.conf].name, confidence: s.value } }); viewPlaces(); });
  document.querySelectorAll("[data-add]").forEach((b) => b.onclick = async () => { await api("/api/gazetteer", { method: "POST", body: { action: "add", name: b.dataset.add } }); viewPlaces(); });
}
