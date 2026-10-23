/* Networks (#/network), neighbourhood maps (#/neighbourhoods) and holdings review (#/m/<cid>/holdings/<page>). Uses d3 (vendor/). */
const NCLASS = (t) => "n-" + String(t || "other").replace(/[^a-z-]/g, "");
const NET = { kind: "people", types: ["person", "place", "occupation", "institution", "goods"], scope: "entry", min_weight: 1, source: "query", dataset: "", hidden: new Set(), manuscripts: null };
const SIDE_NOTE = "Sides are numbered in the order the scribe listed the confini (1º usually the street front), not compass points.";

function netSource() {
  if (NET.source === "dataset" && NET.dataset) return { dataset: NET.dataset };
  const q = Q ? clean(Q) : { manuscripts: NET.manuscripts || [], conditions: [] };
  return { query: q };
}

async function viewNetwork() {
  if (!Q) Q = qLoad() || QDEF();
  if (!NET.manuscripts) NET.manuscripts = Q.manuscripts.length ? Q.manuscripts : S.colls.map((c) => c.id);
  const ds = await api("/api/datasets");
  $("#main").innerHTML = `<div class="row"><h1>Network</h1><span class="spacer"></span>
      <button class="btn small" id="gexp">Export for Gephi (.zip)</button></div>
    <div class="card qb">
      <div class="row"><span class="lab">Show</span><div class="seg" id="nkind">${[["people", "People & things named together"], ["holdings", "Holdings & owners"], ["books", "Cross-references"]].map(([k, t]) => `<button data-k="${k}" class="${NET.kind === k ? "on" : ""}">${t}</button>`).join("")}</div></div>
      <div class="row" id="nsrc"></div>
      <div class="row" id="nopts"></div>
    </div>
    <div class="netwrap"><div class="netbox card"><svg id="net"></svg><div class="nethint small muted" id="nhint"></div></div><aside class="netside card" id="nside"><div class="muted small">Click a node to see its connections. Drag to move, scroll to zoom.</div></aside></div>`;
  document.querySelectorAll("#nkind button").forEach((b) => b.onclick = () => { NET.kind = b.dataset.k; NET.hidden.clear(); viewNetwork(); });
  const src = $("#nsrc");
  if (NET.kind === "holdings") {
    src.innerHTML = `<span class="lab">Manuscripts</span>${S.colls.map((c) => `<span class="chip ${NET.manuscripts.includes(c.id) ? "on" : ""}" data-ms="${esc(c.id)}">${esc(c.title)}</span>`).join("")}
      <label class="small"><input type="checkbox" id="nnb" ${NET.neighbours !== false ? "checked" : ""}> include neighbours (confini)</label>`;
    src.querySelectorAll("[data-ms]").forEach((el) => el.onclick = () => { const m = el.dataset.ms; NET.manuscripts = NET.manuscripts.includes(m) ? NET.manuscripts.filter((x) => x !== m) : [...NET.manuscripts, m]; el.classList.toggle("on"); drawNet(); });
    $("#nnb").onchange = (e) => { NET.neighbours = e.target.checked; drawNet(); };
  } else {
    src.innerHTML = `<span class="lab">From</span><select id="nsel"><option value="query" ${NET.source === "query" ? "selected" : ""}>the current query (${esc(describeShort(Q))})</option>
      ${ds.map((d) => `<option value="ds:${esc(d.id)}" ${NET.source === "dataset" && NET.dataset === d.id ? "selected" : ""}>dataset: ${esc(d.name)}</option>`).join("")}</select>
      <a class="small" href="#/query">change the query →</a>`;
    $("#nsel").onchange = (e) => { const v = e.target.value; if (v.startsWith("ds:")) { NET.source = "dataset"; NET.dataset = v.slice(3); } else NET.source = "query"; drawNet(); };
  }
  const opts = $("#nopts");
  if (NET.kind === "people") {
    opts.innerHTML = `<span class="lab">Include</span>${TYPES.map((t) => `<span class="chip ${NET.types.includes(t) ? "on" : ""}" data-nt="${t}"><i style="background:${TCOL[t]}"></i>${TLABEL[t]}</span>`).join("")}
      <select id="nscope"><option value="entry" ${NET.scope === "entry" ? "selected" : ""}>linked when named in the same entry</option><option value="line" ${NET.scope === "line" ? "selected" : ""}>… in the same line</option></select>
      <label class="small">at least <input type="number" id="nmin" min="1" value="${NET.min_weight}" style="width:52px"> shared entries</label>`;
    opts.querySelectorAll("[data-nt]").forEach((el) => el.onclick = () => { const t = el.dataset.nt; NET.types = NET.types.includes(t) ? NET.types.filter((x) => x !== t) : [...NET.types, t]; el.classList.toggle("on"); drawNet(); });
    $("#nscope").onchange = (e) => { NET.scope = e.target.value; drawNet(); };
    $("#nmin").onchange = (e) => { NET.min_weight = Math.max(1, +e.target.value || 1); drawNet(); };
  }
  opts.insertAdjacentHTML("beforeend", `<span class="spacer"></span><input type="search" id="nfind" placeholder="Find a name" style="width:180px">
    <button class="btn small" id="nunhide" ${NET.hidden.size ? "" : "hidden"}>Show hidden (${NET.hidden.size})</button>`);
  $("#nunhide").onclick = () => { NET.hidden.clear(); drawNet(); };
  $("#gexp").onclick = () => download("/api/network/export", netBody());
  drawNet();
}

function describeShort(q) { const n = (q.conditions || []).length; return `${(q.manuscripts || []).join(", ") || "all"}${n ? `, ${n} condition${n > 1 ? "s" : ""}` : ""}`; }
function netBody() {
  if (NET.kind === "holdings") return { kind: "holdings", manuscripts: NET.manuscripts, neighbours: NET.neighbours !== false };
  return { kind: NET.kind, ...netSource(), types: NET.types, scope: NET.scope, min_weight: NET.min_weight };
}

let SIM = null;
async function drawNet() {
  const svg = d3.select("#net"); svg.selectAll("*").remove();
  if (SIM) SIM.stop();
  $("#nhint").textContent = "Building the network…";
  let g;
  try { g = await api("/api/network", { method: "POST", body: netBody() }); } catch (e) { $("#nhint").textContent = e.message; return; }
  const nodes = g.nodes.filter((n) => !NET.hidden.has(n.id)).map((n) => ({ ...n }));
  const ids = new Set(nodes.map((n) => n.id));
  const links = g.edges.filter((e) => ids.has(e.source) && ids.has(e.target)).map((e) => ({ ...e }));
  const deg = {}; links.forEach((e) => { deg[e.source] = (deg[e.source] || 0) + 1; deg[e.target] = (deg[e.target] || 0) + 1; });
  const shown = nodes.filter((n) => deg[n.id] || NET.kind !== "people");
  $("#nhint").textContent = `${shown.length} nodes, ${links.length} links${g.isolated ? ` · ${g.isolated} names with no link left out` : ""}${NET.hidden.size ? ` · ${NET.hidden.size} hidden` : ""}`;
  if ($("#nunhide")) { $("#nunhide").hidden = !NET.hidden.size; $("#nunhide").textContent = `Show hidden (${NET.hidden.size})`; }
  const box = $("#net").getBoundingClientRect(), W = box.width, H = box.height;
  const r = (n) => 4 + 3 * Math.sqrt(n.count || 1);
  const root = svg.append("g");
  const zoom = d3.zoom().scaleExtent([0.1, 6]).on("zoom", (ev) => root.attr("transform", ev.transform));
  svg.call(zoom);
  const maxw = d3.max(links, (l) => l.weight) || 1;
  const link = root.append("g").attr("class", "links").selectAll("line").data(links).join("line")
    .attr("class", (d) => "lk " + (d.kind.startsWith("same") ? "co" : "rel")).attr("stroke-width", (d) => 0.6 + 3 * (d.weight / maxw));
  link.append("title").text((d) => `${d.kind}${d.weight > 1 ? ` · ${d.weight}` : ""}${d.rent ? ` · ${d.rent}` : ""}`);
  const node = root.append("g").selectAll("g").data(shown).join("g").attr("class", (d) => "nd " + NCLASS(d.type)).call(drag());
  node.each(function (d) {
    const el = d3.select(this);
    if (d.type === "holding" || d.type === "folio" || d.type === "page") el.append("rect").attr("x", -r(d)).attr("y", -r(d)).attr("width", 2 * r(d)).attr("height", 2 * r(d)).attr("rx", d.type === "holding" ? 2 : 6);
    else if (d.type === "location" || d.type === "street") el.append("path").attr("d", d3.symbol(d3.symbolDiamond, 4 * r(d) * r(d)));
    else el.append("circle").attr("r", r(d));
  });
  node.append("title").text((d) => `${d.label} (${d.type}) · ${d.count}`);
  const top = new Set([...shown].sort((a, b) => (b.count || 0) - (a.count || 0)).slice(0, 30).map((n) => n.id));
  const label = root.append("g").selectAll("text").data(shown).join("text").attr("class", "nlabel").text((d) => d.label)
    .attr("dy", (d) => -r(d) - 3).style("display", (d) => (top.has(d.id) ? null : "none"));
  SIM = d3.forceSimulation(shown)
    .force("link", d3.forceLink(links).id((d) => d.id).distance((l) => (l.kind.startsWith("same") ? 70 : 50)).strength((l) => Math.min(1, 0.15 + 0.2 * l.weight)))
    .force("charge", d3.forceManyBody().strength(-160)).force("center", d3.forceCenter(W / 2, H / 2))
    .force("collide", d3.forceCollide().radius((d) => r(d) + 3)).force("x", d3.forceX(W / 2).strength(0.03)).force("y", d3.forceY(H / 2).strength(0.03))
    .stop();
  SIM.tick(300);
  const ticked = () => {
      link.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
      label.attr("x", (d) => d.x).attr("y", (d) => d.y);
  };
  ticked(); fitView(svg, zoom, shown.map((n) => [n.x, n.y]), W, H, 30);
  SIM.on("tick", ticked);
  const select = (d) => {
    const nb = new Set([d.id]); links.forEach((l) => { if (l.source.id === d.id) nb.add(l.target.id); if (l.target.id === d.id) nb.add(l.source.id); });
    node.classed("dim", (n) => !nb.has(n.id)); link.classed("dim", (l) => l.source.id !== d.id && l.target.id !== d.id);
    label.style("display", (n) => (nb.has(n.id) || top.has(n.id) ? null : "none")).classed("dim", (n) => !nb.has(n.id));
    netPanel(d, links);
  };
  node.on("click", (ev, d) => { ev.stopPropagation(); select(d); });
  svg.on("click", () => { node.classed("dim", false); link.classed("dim", false); label.classed("dim", false).style("display", (n) => (top.has(n.id) ? null : "none")); });
  $("#nfind").oninput = (e) => {
    const q = e.target.value.toLowerCase(); if (!q) return;
    const hit = shown.find((n) => n.label.toLowerCase().includes(q)); if (hit) select(hit);
  };
  function drag() {
    return d3.drag().on("start", (ev, d) => { if (!ev.active) SIM.alphaTarget(0.2).restart(); d.fx = d.x; d.fy = d.y; })
      .on("drag", (ev, d) => { d.fx = ev.x; d.fy = ev.y; }).on("end", (ev, d) => { if (!ev.active) SIM.alphaTarget(0); });
  }
}

function netPanel(d, links) {
  const con = links.filter((l) => l.source.id === d.id || l.target.id === d.id)
    .map((l) => ({ other: l.source.id === d.id ? l.target : l.source, kind: l.kind, w: l.weight, rent: l.rent })).sort((a, b) => b.w - a.w);
  const isTag = TYPES.includes(d.type);
  $("#nside").innerHTML = `<div class="small muted">${esc(d.type)}</div><h2 style="margin:2px 0 6px">${esc(d.label)}</h2>
    <div class="small">${d.count || 0} ${NET.kind === "people" ? "entries" : "mentions"}${d.pages ? ` · pages ${esc(d.pages.map((p) => p.split("_")[0]).join(", "))}` : ""}</div>
    ${d.roles && Object.keys(d.roles).length ? `<div class="small">roles: ${esc(Object.entries(d.roles).map(([k, v]) => `${k} ${v}`).join(", "))}</div>` : ""}
    <div class="row" style="margin:8px 0">${isTag ? `<button class="btn small" id="nq">Lines in Query →</button>` : ""}
      ${d.type === "holding" ? `<a class="btn small" href="#/m/${encodeURIComponent(d.manuscript)}/holdings/${encodeURIComponent(d.holding.split("-")[0])}">Holding →</a>
        <a class="btn small" href="#/neighbourhoods/${encodeURIComponent(d.place || "")}">Neighbourhood →</a>` : ""}
      <button class="btn small" id="nhide" title="Leave this node out (e.g. a hub such as the agent)">Hide</button></div>
    <div class="small muted">${con.length} connections</div>
    <table class="small"><tbody>${con.slice(0, 80).map((c) => `<tr><td><span class="dot ${NCLASS(c.other.type)}"></span>${esc(c.other.label)}</td><td class="muted">${esc(c.kind)}${c.rent ? ` · ${esc(c.rent)}` : ""}</td><td class="num">${c.w > 1 ? c.w : ""}</td></tr>`).join("")}</tbody></table>`;
  if ($("#nq")) $("#nq").onclick = () => {
    Q = { ...(Q || QDEF()), unit: "entries", conditions: [...((Q && Q.conditions) || []), { field: d.type, op: "is", value: d.label }] }; qSave(); location.hash = "#/query";
  };
  $("#nhide").onclick = () => { NET.hidden.add(d.id); drawNet(); };
}

/* ------------------------------------------------------------------ boundary squares */
const SIDE_POS = { 1: "top", 2: "right", 3: "bottom", 4: "left" };
function sideText(cs) { return cs.map((c) => c.name + (c.note ? ` (${c.note})` : "")).join(" · "); }
function trunc(s, n) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }

/* draw one holding as a square into a d3 selection g (centred on 0,0) */
function drawSquare(g, h, S0 = 150) {
  const s = S0 / 2;
  g.attr("class", `hold ${h.status || ""}`);
  for (const k of ["1", "2", "3", "4"]) {
    const cs = (h.sides || {})[k] || [];
    if (cs.some((c) => c.type === "street")) {
      const band = { 1: [-s, -s - 9, S0, 9], 2: [s, -s, 9, S0], 3: [-s, s, S0, 9], 4: [-s - 9, -s, 9, S0] }[k];
      g.append("rect").attr("class", "street").attr("x", band[0]).attr("y", band[1]).attr("width", band[2]).attr("height", band[3]);
    }
  }
  g.append("rect").attr("class", "sq").attr("x", -s).attr("y", -s).attr("width", S0).attr("height", S0).attr("rx", 3);
  const lab = (k, x, y, rot) => {
    const cs = (h.sides || {})[k] || [];
    const t = g.append("text").attr("class", "side" + (cs.length ? "" : " none")).attr("transform", `translate(${x},${y}) rotate(${rot})`).attr("text-anchor", "middle");
    t.append("tspan").attr("class", "sn").text(`${["", "iº", "iiº", "iiiº", "iiiiº"][k]} `);
    t.append("tspan").text(cs.length ? trunc(sideText(cs), Math.round(S0 / 6.2)) : "—");
    t.append("title").text(cs.length ? cs.map((c) => `${c.name} — as written: ${c.as_written}`).join("\n") : "not stated");
  };
  lab(1, 0, -s + 13, 0); lab(2, s - 9, 0, 90); lab(3, 0, s - 6, 0); lab(4, -s + 9, 0, -90);
  const mid = g.append("text").attr("class", "mid").attr("text-anchor", "middle");
  mid.append("tspan").attr("x", 0).attr("y", -22).attr("class", "k").text(trunc(h.kind || "holding", 20));
  mid.append("tspan").attr("x", 0).attr("y", -8).attr("class", "hid").text(h.id);
  mid.append("tspan").attr("x", 0).attr("y", 8).attr("class", "own").text("");
  if (h.owner) mid.select(".own").remove();
  if (h.owner) mid.append("tspan").attr("x", 0).attr("y", 8).attr("class", "own").text(trunc(h.owner + (h.owner_relation ? " (" + h.owner_relation.replace(" of", "") + ")" : ""), Math.round(S0 / 7.5)));
  [0, 1].forEach((i) => { const o = (h.occupants || [])[i]; mid.append("tspan").attr("x", 0).attr("y", 22 + 12 * i).attr("class", "occ").text(o ? trunc(`${o.contract === "mezzadria" ? "worked by" : "held by"} ${o.name || "?"}`, Math.round(S0 / 7.2)) : ""); });
  const other = (h.sides || {}).other;
  if (other) g.append("text").attr("class", "side none").attr("x", 0).attr("y", s + 22).attr("text-anchor", "middle").text("+ " + sideText(other));
}

/* ------------------------------------------------------------------ neighbourhood map */
const NB = { place: null, manuscripts: null };
async function viewNeighbourhood(place) {
  if (!NB.manuscripts) NB.manuscripts = S.colls.map((c) => c.id);
  const places = await api("/api/places", { method: "POST", body: { manuscripts: NB.manuscripts } });
  NB.place = place != null ? place : NB.place || (places.find((p) => p.depth === 0) || {}).place;
  $("#main").innerHTML = `<div class="row"><h1>Neighbourhoods</h1><span class="spacer"></span>${S.colls.map((c) => `<span class="chip ${NB.manuscripts.includes(c.id) ? "on" : ""}" data-ms="${esc(c.id)}">${esc(c.title)}</span>`).join("")}</div>
    <p class="muted small">Each holding is drawn as a square with its confini on the four sides; grey bands are street fronts. Holdings that name the same neighbour, or name each other, are pulled together around that neighbour, so blocks of adjoining property appear. ${SIDE_NOTE} Not to scale.</p>
    <div class="nbwrap"><aside class="card nbside">${places.length ? places.map((p) => `<a class="pl ${p.place === NB.place ? "on" : ""}" style="padding-left:${6 + 12 * p.depth}px" href="#/neighbourhoods/${encodeURIComponent(p.place)}">${esc(p.place.split(" › ").pop())} <span class="n">${p.holdings}</span></a>`).join("") : '<div class="muted small">No holdings yet.</div>'}</aside>
      <div class="netbox card"><div class="tbar" id="tbar"></div><svg id="nbsvg"></svg><div class="nethint small muted" id="nbhint"></div><div class="olegend" id="olegend"></div></div>
      <aside class="card netside" id="nbpanel"><div class="muted small">Click a holding for its description.</div></aside></div>`;
  document.querySelectorAll("[data-ms]").forEach((el) => el.onclick = () => { const m = el.dataset.ms; NB.manuscripts = NB.manuscripts.includes(m) ? NB.manuscripts.filter((x) => x !== m) : [...NB.manuscripts, m]; viewNeighbourhood(NB.place); });
  if (NB.place) drawNeighbourhood(await api("/api/neighbourhood", { method: "POST", body: { manuscripts: NB.manuscripts, place: NB.place } }));
}

function drawNeighbourhood(nb) {
  const svg = d3.select("#nbsvg"); svg.selectAll("*").remove();
  const box = $("#nbsvg").getBoundingClientRect(), W = box.width, H = box.height, SQ = 170;
  const hs = nb.holdings.map((h) => ({ ...h, nid: "h:" + h.manuscript + ":" + h.id, isH: true }));
  const owners = {}; hs.forEach((h) => { if (h.owner) (owners[h.owner] = owners[h.owner] || []).push(h); });
  // shared neighbours: a named neighbour that bounds two or more holdings here, or owns another holding here
  const use = {};
  hs.forEach((h) => Object.entries(h.sides || {}).forEach(([side, cs]) => cs.forEach((c) => {
    if (side === "other" || !c.name || ["via", "strada", "altri confini"].includes(c.name.toLowerCase()) || c.type === "other" || c.type === "holding") return;
    (use[c.name] = use[c.name] || { name: c.name, type: c.type, refs: [] }).refs.push({ h, side: +side });
  })));
  const nbrs = Object.values(use).filter((u) => u.refs.length >= 2 || owners[u.name]).map((u) => ({ ...u, nid: "n:" + u.name }));
  const anchors = [];
  nbrs.forEach((u) => u.refs.forEach((r) => anchors.push({ h: r.h, side: r.side, n: u })));
  const rel = nb.links.filter((l) => l.related.length).map((l) => ({ a: hs.find((h) => h.id === l.a), b: hs.find((h) => h.id === l.b), kind: l.related.join(", ") })).filter((l) => l.a && l.b);
  $("#nbhint").textContent = `${hs.length} holdings · ${nbrs.length} shared neighbours · ${nb.links.length} links between holdings`;
  const root = svg.append("g");
  const zoom = d3.zoom().scaleExtent([0.1, 4]).on("zoom", (ev) => root.attr("transform", ev.transform));
  svg.call(zoom);
  const nodes = [...hs, ...nbrs];
  nodes.forEach((n, i) => { n.x = W / 2 + 200 * Math.cos(i); n.y = H / 2 + 200 * Math.sin(i); });
  const DIR = { 1: [0, -1], 2: [1, 0], 3: [0, 1], 4: [-1, 0] };
  const relLine = root.append("g").selectAll("line").data(rel).join("line").attr("class", "lk rel dashed");
  relLine.append("title").text((d) => d.kind);
  const aLine = root.append("g").selectAll("line").data(anchors).join("line").attr("class", (d) => "lk anchor " + NCLASS(d.n.type));
  aLine.append("title").text((d) => `${d.h.id}, side ${d.side}: ${d.n.name}`);
  const hg = root.append("g").selectAll("g").data(hs).join("g").each(function (h) { drawSquare(d3.select(this), h, SQ); }).style("cursor", "pointer");
  const ng = root.append("g").selectAll("g").data(nbrs).join("g").attr("class", (d) => "nd " + NCLASS(d.type === "street" ? "street" : d.type === "institution" ? "institution" : "person"));
  ng.append("circle").attr("r", (d) => 7 + 2 * d.refs.length);
  ng.append("text").attr("class", "nlabel").attr("dy", (d) => -(10 + 2 * d.refs.length)).text((d) => d.name + (owners[d.name] ? " (owner here)" : ""));
  const dragH = d3.drag().on("start", (ev, d) => { if (!ev.active) sim.alphaTarget(0.2).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (ev, d) => { d.fx = ev.x; d.fy = ev.y; }).on("end", (ev, d) => { if (!ev.active) sim.alphaTarget(0); });
  hg.call(dragH); ng.call(dragH);
  const sideForce = (alpha) => {
    for (const a of anchors) {
      const [dx, dy] = DIR[a.side] || [0, 0];
      const tx = a.h.x + dx * (SQ / 2 + 55), ty = a.h.y + dy * (SQ / 2 + 55);
      const ex = (tx - a.n.x) * 0.12 * alpha, ey = (ty - a.n.y) * 0.12 * alpha;
      a.n.vx += ex; a.n.vy += ey; a.h.vx -= ex * 0.6; a.h.vy -= ey * 0.6;
    }
    for (const l of rel) {
      const ex = (l.b.x - l.a.x) * 0.02 * alpha, ey = (l.b.y - l.a.y) * 0.02 * alpha;
      l.a.vx += ex; l.a.vy += ey; l.b.vx -= ex; l.b.vy -= ey;
    }
  };
  const sim = d3.forceSimulation(nodes).force("side", sideForce)
    .force("collide", d3.forceCollide().radius((d) => (d.isH ? SQ * 0.8 : 42)).strength(0.9))
    .force("charge", d3.forceManyBody().strength((d) => (d.isH ? -300 : -80)))
    .force("x", d3.forceX(W / 2).strength(0.04)).force("y", d3.forceY(H / 2).strength(0.04)).stop();
  sim.tick(400);
  const ticked = () => {
      hg.attr("transform", (d) => `translate(${d.x},${d.y})`);
      ng.attr("transform", (d) => `translate(${d.x},${d.y})`);
      aLine.attr("x1", (d) => d.h.x + (DIR[d.side] || [0, 0])[0] * SQ / 2).attr("y1", (d) => d.h.y + (DIR[d.side] || [0, 0])[1] * SQ / 2).attr("x2", (d) => d.n.x).attr("y2", (d) => d.n.y);
      relLine.attr("x1", (d) => d.a.x).attr("y1", (d) => d.a.y).attr("x2", (d) => d.b.x).attr("y2", (d) => d.b.y);
  };
  ticked(); sim.on("tick", ticked);
  fitView(svg, zoom, nodes.flatMap((n) => (n.isH ? [[n.x - SQ / 2 - 12, n.y - SQ / 2 - 12], [n.x + SQ / 2 + 12, n.y + SQ / 2 + 30]] : [[n.x - 60, n.y - 25], [n.x + 60, n.y + 15]])), W, H, 20);
  hg.on("click", (ev, h) => { NB.sel = h; holdingPanel(h, "#nbpanel"); });
  timeControls(hs, hg);
  ng.on("click", (ev, n) => {
    $("#nbpanel").innerHTML = `<div class="small muted">${esc(n.type)}</div><h2 style="margin:2px 0">${esc(n.name)}</h2>
      ${owners[n.name] ? `<p class="small">Owns ${owners[n.name].length} holding(s) here: ${owners[n.name].map((h) => esc(h.id)).join(", ")}</p>` : ""}
      <p class="small">Named as a neighbour of:</p><ul class="small">${n.refs.map((r) => `<li>${esc(r.h.id)} (${esc(r.h.kind)}), side ${["", "iº", "iiº", "iiiº", "iiiiº"][r.side] || "?"}</li>`).join("")}</ul>`;
  });
}

function holdingPanel(h, sel) {
  $(sel).innerHTML = `<div class="small muted">${esc(h.manuscript)} · ${esc(h.page || "")}</div><h2 style="margin:2px 0">${esc(h.kind || "holding")} <span class="small muted">${esc(h.id)}</span></h2>
    <div class="ms">${esc(h.as_written || "")}</div>
    <div class="small" style="margin-top:6px"><b>Where:</b> ${esc(h.place)}${h.location && h.location.near ? ` · ${esc(h.location.near)}` : ""}${h.size ? ` · ${esc(h.size)}` : ""}</div>
    <div class="small"><b>Owner:</b> ${esc(h.owner || "?")}${h.owner_relation ? ` (${esc(h.owner_relation)})` : ""}</div>
    ${h.former_owners && h.former_owners.length ? `<div class="small"><b>Formerly:</b> ${esc(h.former_owners.join("; "))}</div>` : ""}
    ${(h.occupants || []).map((o) => `<div class="small"><b>${o.contract === "mezzadria" ? "Worked by" : "Held by"}:</b> ${esc(o.name || "?")} ${o.contract ? `(${esc(o.contract)})` : ""} ${o.rent ? `· ${esc(o.rent)}` : ""} ${o.from ? `· from ${esc(o.from)}` : ""}</div>`).join("")}
    <div class="small" style="margin-top:6px"><b>Confini</b></div>
    <ul class="small">${Object.entries(h.sides || {}).map(([k, cs]) => cs.map((c) => `<li>${k === "other" ? "" : ["", "iº", "iiº", "iiiº", "iiiiº"][k] + " "}${esc(c.name)} <span class="muted ms">“${esc(c.as_written)}”</span></li>`).join("")).join("")}</ul>
    <a class="btn small" href="#/m/${encodeURIComponent(h.manuscript)}/holdings/${encodeURIComponent(h.page || "")}">Check / edit this holding →</a>`;
  if (NB.range && (h.timeline || []).length) {
    const box = document.createElement("div"); box.className = "tl";
    $(sel).insertBefore(box, $(sel).children[3]);
    const st = stateAt(h, NB.t);
    box.innerHTML = `<div class="small" style="margin:6px 0 2px"><b>${esc(dLabel(NB.t))}:</b> ${st.owner ? `owned by <b style="color:${ownerColour(ownerKey(st.owner))}">${esc(ownerKey(st.owner))}</b>${st.owner.sure ? "" : " <span class=\"muted\">(dates partly inferred)</span>"}` : "owner at this date not known"}${st.occupants.length ? `; held by ${esc(st.occupants.map((o) => o.name + (o.contract ? " (" + o.contract + ")" : "")).join(", "))}` : ""}</div>`;
    drawGantt(box, h, NB.range, NB.t);
    if (st.undated.length) box.insertAdjacentHTML("beforeend", `<div class="small muted">Not dated: ${esc(st.undated.map((p) => `${p.role === "owner" ? "owner" : "occupant"} ${ownerKey(p)}`).join("; "))}</div>`);
    box.insertAdjacentHTML("beforeend", `<div class="small muted">Solid bars: dates stated in the text; faded/dashed: inferred; ◂ ▸ open-ended. Hover a bar for the evidence.</div>`);
  }
}

/* time slider over the neighbourhood: colour each holding by its owner at that date */
function timeControls(hs, hg) {
  NB.range = timeRange(hs);
  const months = Math.round((NB.range[1] - NB.range[0]) / (30.44 * 864e5));
  const toT = (i) => { const d = new Date(NB.range[0]); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + +i, 15); };
  if (!NB.t || NB.t < NB.range[0] || NB.t > NB.range[1]) NB.t = Date.UTC(1387, 6, 15);
  if (NB.t < NB.range[0] || NB.t > NB.range[1]) NB.t = toT(Math.round(months / 2));
  const idx = Math.round((NB.t - NB.range[0]) / (30.44 * 864e5));
  const dated = hs.filter((h) => (h.timeline || []).length).length;
  $("#tbar").innerHTML = `<button class="btn small" id="tplay" title="Play">▶</button>
    <input type="range" id="tslide" min="0" max="${months}" value="${idx}" style="flex:1">
    <b id="tlabel" class="small" style="min-width:230px">${esc(dLabel(NB.t))}</b>
    <span class="small muted">${dated}/${hs.length} with a timeline</span>`;
  const paint = () => {
    $("#tlabel").textContent = dLabel(NB.t);
    const present = new Set();
    hg.each(function (h) {
      const st = stateAt(h, NB.t), g = d3.select(this);
      const key = st.owner ? ownerKey(st.owner) : null, col = ownerColour(key);
      if (key) present.add(key);
      const panel = getComputedStyle(document.body).getPropertyValue("--panel").trim() || "#fffdf8";
      const ink3 = getComputedStyle(document.body).getPropertyValue("--ink-3").trim() || "#9a8f84";
      g.select("rect.sq").transition().duration(350)
        .style("fill", col ? d3.interpolateRgb(panel, col)(st.owner.sure ? 0.38 : 0.24) : panel)
        .style("stroke", col || ink3);
      g.classed("nodate", !key && (h.timeline || []).length > 0).classed("notl", !(h.timeline || []).length);
      g.select(".own").text(trunc(key ? key + (st.owner.sure ? "" : " ~") : (h.timeline || []).length ? "owner not known then" : (h.owner || ""), 26));
      const occ = g.selectAll(".occ").nodes();
      occ.forEach((n, i) => { const o = st.occupants[i]; d3.select(n).text(o ? trunc(`${o.contract === "mezzadria" ? "worked by" : "held by"} ${o.name}`, 26) : ""); });
    });
    const keys = Object.keys(OWNER_COL).filter((k) => hs.some((h) => (h.timeline || []).some((p) => p.role === "owner" && ownerKey(p) === k)));
    $("#olegend").innerHTML = keys.map((k) => `<span class="${present.has(k) ? "on" : ""}"><i style="background:${OWNER_COL[k]}"></i>${esc(k)}</span>`).join("")
      + `<span><i style="background:var(--panel);border:1px solid var(--ink-3)"></i>owner not known at this date</span>`;
    if (NB.sel) holdingPanel(NB.sel, "#nbpanel");
  };
  hs.forEach((h) => (h.timeline || []).forEach((p) => p.role === "owner" && ownerColour(ownerKey(p))));
  $("#tslide").oninput = (e) => { NB.t = toT(e.target.value); paint(); };
  let timer = null;
  $("#tplay").onclick = () => {
    if (timer) { clearInterval(timer); timer = null; $("#tplay").textContent = "▶"; return; }
    $("#tplay").textContent = "❚❚";
    timer = setInterval(() => {
      const sl = $("#tslide"); if (!sl) { clearInterval(timer); return; }
      if (+sl.value >= +sl.max) sl.value = 0; else sl.value = +sl.value + 1;
      NB.t = toT(sl.value); paint();
    }, 220);
  };
  paint();
}

/* ------------------------------------------------------------------ holdings review */
const CONTRACTS = ["pigione", "affitto", "mezzadria", "habitation", "other"];
const CTYPES = ["street", "person", "institution", "holding", "other"];
async function viewHoldings(pid) {
  const cid = S.cid;
  let d = await api(`/api/holdings/${encodeURIComponent(cid)}`);
  if (!pid) pid = (d.pages.find((p) => p.suggested) || d.pages[0] || {}).id;
  if (!pid) { $("#main").innerHTML = `<div class="empty">No holdings yet in ${esc(cid)}. Ask Claude to extract them from property pages (suggestions to check here).</div>`; return; }
  const pages = d.pages;
  d = await api(`/api/holdings/${encodeURIComponent(cid)}?page=${encodeURIComponent(pid)}`);
  await loadNames();
  $("#main").innerHTML = `<div class="tagwrap"><aside class="tagside card"><div class="small muted" style="margin-bottom:6px">Pages with holdings</div>
      ${pages.map((p) => `<a class="pg ${p.id === pid ? "on" : ""}" href="#/m/${encodeURIComponent(cid)}/holdings/${encodeURIComponent(p.id)}">${esc((p.id || "").split("_")[0])}<span class="n">${p.holdings}${p.suggested ? ` · <b class="sgc">${p.suggested} ?</b>` : " ✓"}</span></a>`).join("")}</aside>
    <section><div class="row"><h1 style="margin:0">${esc(pid)}</h1><span class="spacer"></span>
      <button class="btn small" id="hnew">+ New holding on this page</button></div>
      <p class="small muted">Claude's suggestions are dashed. Check each holding against the lines on the left; Edit to correct, ✓ if right. ${SIDE_NOTE}</p>
      <div class="hgrid"><div class="hlines card">${d.lines.map((l) => `<div class="hl" data-key="${esc(l.key)}"><span class="ln">${l.line}</span> <span class="ms">${esc(l.text)}</span></div>`).join("")}</div>
      <div id="hcards">${d.holdings.map((h) => holdingCard(h)).join("") || '<div class="muted">No holdings on this page.</div>'}</div></div></section></div>`;
  $("#hnew").onclick = async () => { const h = await api(`/api/holdings/${encodeURIComponent(cid)}`, { method: "POST", body: { action: "new", page: pid, holding: { kind: "casa" } } }); viewHoldings(pid).then(() => editHolding(h.id, h)); };
  d.holdings.forEach((h) => wireHolding(h, d, pid));
}

function asSquare(h) {
  const sides = {}; (h.confini || []).forEach((c) => (sides[String(c.side || "other")] = sides[String(c.side || "other")] || []).push(c));
  return { ...h, sides, owner: (h.owner || {}).name, owner_relation: (h.owner || {}).relation };
}

function holdingCard(h) {
  return `<div class="card hcard ${h.status}" id="hc-${esc(h.id)}" data-id="${esc(h.id)}">
    <div class="row"><b>${esc(h.id)}</b> <span class="ms">${esc(h.as_written || h.kind || "")}</span><span class="spacer"></span>
      <span class="small ${h.status === "approved" ? "ok" : h.status === "rejected" ? "no" : "sgc"}">${h.status === "suggested" ? "? suggestion" : h.status === "approved" ? "✓ checked" : "✗ rejected"}</span></div>
    <div class="hbody"><svg class="mini" viewBox="-110 -110 220 220"></svg>
      <div class="small">
        <div><b>Where:</b> ${esc(Object.entries(h.location || {}).filter(([, v]) => v).map(([k, v]) => `${k} ${v}`).join(" · ") || "—")}${h.size ? ` · ${esc(h.size)}` : ""}</div>
        <div><b>Owner:</b> ${esc((h.owner || {}).name || "—")}${(h.owner || {}).relation ? ` (${esc(h.owner.relation)})` : ""}</div>
        ${(h.former_owners || []).length ? `<div><b>Formerly:</b> ${esc(h.former_owners.map((f) => `${f.name}${f.how ? ` (${f.how})` : ""}`).join("; "))}</div>` : ""}
        ${(h.occupants || []).map((o) => `<div><b>Occupant:</b> ${esc(o.name || "?")}${o.occupation ? `, ${esc(o.occupation)}` : ""} · ${esc(o.contract || "")}${o.rent ? ` · ${esc(o.rent)}` : ""}${o.from ? ` · from ${esc(o.from)}` : ""}</div>`).join("")}
        <div><b>Confini:</b> ${esc((h.confini || []).map((c) => `${c.side ? ["", "iº", "iiº", "iiiº", "iiiiº"][c.side] : ""} ${c.name}`).join(" · ") || "—")}</div>
        ${(h.timeline || []).length ? `<div><b>Timeline:</b> ${(h.timeline || []).map((p) => `${p.role === "owner" ? "owner" : "occupant"} ${esc(ownerKey(p))} ${esc(p.from || "?")}–${esc(p.to || (p.to_basis === "open" ? "…" : "?"))}${p.from_basis === "stated" ? "" : " ~"}`).join(" · ")}</div>` : ""}
        ${(h.related || []).length ? `<div><b>Related:</b> ${esc(h.related.map((r) => `${r.relation} ${r.id}`).join("; "))}</div>` : ""}
        ${h.note ? `<div class="muted">${esc(h.note)}</div>` : ""}${h.uncertain ? `<div style="color:var(--chg)">Claude was unsure</div>` : ""}
      </div></div>
    <div class="actions">${h.status !== "approved" ? `<button class="btn small ok" data-ha="approve">✓ Right</button>` : ""}<button class="btn small" data-ha="edit">✎ Edit</button>
      ${h.status !== "rejected" ? `<button class="btn small bad" data-ha="reject">✗ Not a holding</button>` : `<button class="btn small" data-ha="suggest">↺ Restore</button>`}
      ${h.source === "laura" ? `<button class="btn small bad" data-ha="delete">Delete</button>` : ""}</div>
    <div class="hedit" hidden></div></div>`;
}

function wireHolding(h, d, pid) {
  const el = document.getElementById("hc-" + h.id);
  drawSquare(d3.select(el.querySelector("svg.mini")).append("g"), asSquare(h), 170);
  el.onmouseenter = () => document.querySelectorAll(".hl").forEach((l) => l.classList.toggle("hi", (h.lines || []).includes(l.dataset.key)));
  el.querySelectorAll("[data-ha]").forEach((b) => b.onclick = async () => {
    const a = b.dataset.ha;
    if (a === "edit") return editHolding(h.id, h);
    if (a === "delete" && !confirm("Delete this holding?")) return;
    await api(`/api/holdings/${encodeURIComponent(S.cid)}`, { method: "POST", body: { id: h.id, action: a } }); viewHoldings(pid);
  });
}

function editHolding(id, h) {
  const el = document.getElementById("hc-" + id); if (!el) return;
  h = h || {};
  const ed = el.querySelector(".hedit"); ed.hidden = false;
  const loc = h.location || {}, own = h.owner || {};
  const rowsOf = (list, cols) => (list || []).map((x) => `<div class="row hrow">${cols.map(([k, opts, w]) => opts
    ? `<select data-k="${k}">${opts.map((o) => `<option ${String(x[k] ?? "") === String(o) ? "selected" : ""}>${o}</option>`).join("")}</select>`
    : `<input type="text" data-k="${k}" value="${esc(x[k] ?? "")}" placeholder="${k}" style="width:${w || 140}px" ${k === "name" ? 'list="nm-person"' : ""}>`).join("")}<button class="btn small ghost" data-del>✕</button></div>`).join("");
  const FO = [["name"], ["how", ["formerly of (che fu di)", "bought from", "inherited from", ""]]];
  const OC = [["name"], ["occupation", null, 110], ["contract", CONTRACTS], ["rent", null, 120], ["from", null, 100]];
  const CF = [["side", ["1", "2", "3", "4", ""]], ["name", null, 170], ["type", CTYPES], ["as_written", null, 170], ["note", null, 100]];
  const BASIS = ["stated", "inferred", "unknown", "open"];
  const TL = [["role", ["owner", "occupant"]], ["name", null, 150], ["relation", null, 90], ["contract", ["", ...CONTRACTS]], ["rent", null, 90],
    ["from", null, 90], ["from_basis", BASIS], ["to", null, 90], ["to_basis", BASIS], ["evidence", null, 160]];
  ed.innerHTML = `<div class="row"><label>kind<br><input type="text" id="e-kind" value="${esc(h.kind || "")}"></label><label style="flex:1">as written<br><input type="text" id="e-aw" class="ms" value="${esc(h.as_written || "")}" style="width:100%"></label><label>size<br><input type="text" id="e-size" value="${esc(h.size || "")}"></label></div>
    <div class="row">${["city", "comune", "castello", "popolo", "luogo", "via", "near"].map((k) => `<label>${k}<br><input type="text" data-loc="${k}" value="${esc(loc[k] || "")}" style="width:130px"></label>`).join("")}</div>
    <div class="row"><label>owner<br><input type="text" id="e-own" value="${esc(own.name || "")}" list="nm-person"></label><label>relation<br><input type="text" id="e-ownr" value="${esc(own.relation || "")}" placeholder="heirs of"></label></div>
    <div class="small muted">Former owners</div><div id="e-fo">${rowsOf(h.former_owners, FO)}</div><button class="btn small" data-add="fo">+</button>
    <div class="small muted">Occupants (tenants, sharecroppers)</div><div id="e-oc">${rowsOf(h.occupants, OC)}</div><button class="btn small" data-add="oc">+</button>
    <div class="small muted">Confini (side = order written)</div><div id="e-cf">${rowsOf((h.confini || []).map((c) => ({ ...c, side: c.side ?? "" })), CF)}</div><button class="btn small" data-add="cf">+</button>
    <div class="small muted">Timeline (modern dates YYYY, YYYY-MM or YYYY-MM-DD; basis: stated / inferred / unknown / open)</div><div id="e-tl">${rowsOf(h.timeline, TL)}</div><button class="btn small" data-add="tl">+</button>
    <div class="row"><label style="flex:1">note<br><input type="text" id="e-note" value="${esc(h.note || "")}" style="width:100%"></label></div>
    <div class="row" style="margin-top:8px"><button class="btn small primary" id="e-save">Save (and mark checked)</button><button class="btn small" id="e-cx">Cancel</button></div>`;
  const tmpl = { fo: FO, oc: OC, cf: CF, tl: TL };
  ed.querySelectorAll("[data-add]").forEach((b) => b.onclick = () => {
    const box = ed.querySelector("#e-" + b.dataset.add); box.insertAdjacentHTML("beforeend", rowsOf([{}], tmpl[b.dataset.add])); wireDel();
  });
  const wireDel = () => ed.querySelectorAll("[data-del]").forEach((b) => b.onclick = () => b.closest(".hrow").remove());
  wireDel();
  const read = (sel) => [...ed.querySelectorAll(sel + " .hrow")].map((r) => { const o = {}; r.querySelectorAll("[data-k]").forEach((x) => { if (x.value.trim()) o[x.dataset.k] = x.value.trim(); }); return o; }).filter((o) => o.name);
  ed.querySelector("#e-cx").onclick = () => { ed.hidden = true; ed.innerHTML = ""; };
  ed.querySelector("#e-save").onclick = async () => {
    const location = {}; ed.querySelectorAll("[data-loc]").forEach((x) => { if (x.value.trim()) location[x.dataset.loc] = x.value.trim(); });
    const holding = { kind: ed.querySelector("#e-kind").value.trim(), as_written: ed.querySelector("#e-aw").value, size: ed.querySelector("#e-size").value.trim(), location,
      owner: { ...(h.owner || {}), name: ed.querySelector("#e-own").value.trim(), relation: ed.querySelector("#e-ownr").value.trim() },
      former_owners: read("#e-fo"), occupants: read("#e-oc"),
      confini: read("#e-cf").map((c) => ({ ...c, side: c.side ? +c.side : null })),
      timeline: read("#e-tl").map((p) => ({ from: null, to: null, ...p })), note: ed.querySelector("#e-note").value, uncertain: false };
    try { await api(`/api/holdings/${encodeURIComponent(S.cid)}`, { method: "POST", body: { id, action: "edit", holding } }); viewHoldings(h.page || location.page || undefined); }
    catch (e) { alertBar(e.message); }
  };
}

function fitView(svg, zoom, pts, W, H, pad) {
  if (!pts.length) return;
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const k = Math.min(1.1, 0.95 * Math.min((W - 2 * pad) / Math.max(1, x1 - x0), (H - 2 * pad) / Math.max(1, y1 - y0)));
  svg.call(zoom.transform, d3.zoomIdentity.translate(W / 2 - k * (x0 + x1) / 2, H / 2 - k * (y0 + y1) / 2).scale(k));
}

/* ------------------------------------------------------------------ time: who owned / held a holding when */
const MONTHN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
function dParse(s, end) {          // "1387" | "1387-06" | "1387-06-12" → ms (start, or end of the period when end=true)
  if (!s) return null;
  const m = /^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?/.exec(String(s)); if (!m) return null;
  const y = +m[1], mo = m[2] ? +m[2] - 1 : null, d = m[3] ? +m[3] : null;
  if (!end) return Date.UTC(y, mo ?? 0, d ?? 1);
  if (d) return Date.UTC(y, mo, d);
  if (mo != null) return Date.UTC(y, mo + 1, 0);
  return Date.UTC(y, 11, 31);
}
function dLabel(t) {
  const d = new Date(t), y = d.getUTCFullYear(), m = d.getUTCMonth(), day = d.getUTCDate();
  const flor = m < 2 || (m === 2 && day < 25) ? ` (${y - 1} in Florentine style)` : "";
  return `${MONTHN[m]} ${y}${flor}`;
}
function ownerKey(p) { return (p.relation === "heirs of" ? "heirs of " : "") + (p.name || "?"); }

/* resolve the periods of one role into [start, end] (ms; ±Infinity = open; null = cannot be placed in time) */
function resolvePeriods(tl, role) {
  const ps = (tl || []).filter((p) => p.role === role);
  const out = ps.map((p) => ({ ...p, s: dParse(p.from), e: dParse(p.to, true) }));
  out.forEach((p, i) => {
    if (p.s == null) p.s = i === 0 ? -Infinity : (out[i - 1].e != null && isFinite(out[i - 1].e) ? out[i - 1].e : null);
    if (p.e == null) {
      const nxt = out.slice(i + 1).find((q) => dParse(q.from) != null);
      if (role === "owner") p.e = nxt ? dParse(nxt.from) : (p.to_basis === "open" || i === out.length - 1 ? Infinity : null);
      else p.e = p.to_basis === "open" || p.to_basis === "unknown" ? Infinity : null;
    }
    p.sure = p.from_basis === "stated" && (p.to_basis === "stated" || p.to_basis === "open");
  });
  return out;
}
function stateAt(h, t) {
  const own = resolvePeriods(h.timeline, "owner"), occ = resolvePeriods(h.timeline, "occupant");
  const cover = (p) => p.s != null && p.e != null && p.s <= t && t <= p.e;
  const owners = own.filter(cover), occs = occ.filter(cover);
  return { owner: owners[owners.length - 1] || null, occupants: occs, own, occ, undated: [...own, ...occ].filter((p) => p.s == null || p.e == null) };
}
function timeRange(hs) {
  const ts = [];
  hs.forEach((h) => (h.timeline || []).forEach((p) => { [dParse(p.from), dParse(p.to, true)].forEach((t) => t != null && ts.push(t)); }));
  if (!ts.length) return [Date.UTC(1380, 0, 1), Date.UTC(1395, 11, 31)];
  const a = new Date(Math.min(...ts)), b = new Date(Math.max(...ts));
  return [Date.UTC(a.getUTCFullYear() - 1, 0, 1), Date.UTC(b.getUTCFullYear() + 1, 11, 31)];
}
const OWNER_COL = {};
function ownerColour(key) {
  if (!key) return null;
  if (!OWNER_COL[key]) { const pal = [...d3.schemeTableau10, ...d3.schemeSet2]; OWNER_COL[key] = pal[Object.keys(OWNER_COL).length % pal.length]; }
  return OWNER_COL[key];
}

/* gantt of one holding's owners and occupants, with a line at time t */
function drawGantt(el, h, range, t) {
  const st = stateAt(h, t);
  const rows = [...st.own.filter((p) => p.s != null && p.e != null), ...st.occ.filter((p) => p.s != null && p.e != null)];
  const W = 280, rowH = 30, H = 24 + rows.length * rowH;
  const x = d3.scaleUtc().domain(range).range([4, W - 4]);
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("width", "100%").attr("class", "gantt");
  svg.append("g").attr("transform", `translate(0,${H - 18})`).call(d3.axisBottom(x).ticks(5).tickFormat(d3.utcFormat("%Y")));
  rows.forEach((p, i) => {
    const y = 4 + i * rowH, x0 = x(Math.max(range[0], p.s)), x1 = x(Math.min(range[1], p.e));
    const col = p.role === "owner" ? ownerColour(ownerKey(p)) : "var(--ink-3)";
    svg.append("rect").attr("x", x0).attr("y", y + 12).attr("width", Math.max(2, x1 - x0)).attr("height", 10).attr("rx", 3)
      .attr("fill", col).attr("opacity", p.sure ? 0.95 : 0.55).attr("stroke", col).attr("stroke-dasharray", p.sure ? null : "3 2")
      .append("title").text(`${p.role}: ${p.name} ${p.relation ? "(" + p.relation + ")" : ""}\nfrom ${p.from || "?"} (${p.from_basis}) to ${p.to || "?"} (${p.to_basis})${p.evidence ? "\n“" + p.evidence + "”" : ""}${p.note ? "\n" + p.note : ""}`);
    if (!isFinite(p.s)) svg.append("text").attr("x", x0).attr("y", y + 21).attr("class", "gopen").text("◂");
    if (!isFinite(p.e)) svg.append("text").attr("x", x1 - 8).attr("y", y + 21).attr("class", "gopen").text("▸");
    svg.append("text").attr("x", Math.min(Math.max(x0, 4), W - 150)).attr("y", y + 9).attr("class", "glab")
      .text(`${p.role === "owner" ? "" : p.contract === "mezzadria" ? "worked by " : "held by "}${ownerKey(p)}${p.rent ? " · " + p.rent : ""}`);
  });
  svg.append("line").attr("x1", x(t)).attr("x2", x(t)).attr("y1", 0).attr("y2", H - 18).attr("class", "gnow");
  return st;
}
