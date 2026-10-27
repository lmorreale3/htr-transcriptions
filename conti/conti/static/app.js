/* Conti front end: plain JS, hash routes  #/  ·  #/m/<cid>/<tab>  (tab = overview | sums | dates | refs | settings) */
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
async function api(url, opts = {}) {
  if (opts.body && typeof opts.body !== "string") { opts.body = JSON.stringify(opts.body); opts.headers = { "Content-Type": "application/json" }; }
  const r = await fetch(url, opts);
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m; } catch (e) {} throw new Error(m); }
  return r.json();
}
const S = { status: null, colls: null, cid: null, statuses: null, data: null, sumFilter: "review", q: "", shown: 40, focus: 0 };
const TABS = [["overview", "Overview"], ["tags", "Tags"], ["holdings", "Holdings"], ["dates", "Dates"], ["refs", "References"], ["sums", "Sums"], ["settings", "Settings"]];
const TOP = [["#/", "Manuscripts"], ["#/ask", "Ask"], ["#/query", "Query"], ["#/datasets", "Datasets"], ["#/network", "Network"], ["#/neighbourhoods", "Neighbourhoods"], ["#/map", "Map"], ["#/names", "Names"], ["#/catasto", "Catasto 1427"]];
const TYPES = ["person", "place", "occupation", "institution", "goods"];
const TLABEL = { person: "Person", place: "Place", occupation: "Occupation / role", institution: "Institution", goods: "Goods" };
const KIND = { debit: "de dare", credit: "de avere / anno dato", balance: "resta" };

async function load(force) {
  const st = S.statuses.join(",");
  if (!force && S.data && S.data._cid === S.cid && S.data._st === st) return S.data;
  $("#main").innerHTML = `<div class="empty">Reading ${esc(S.cid)}…</div>`;
  S.data = await api(`/api/records/${encodeURIComponent(S.cid)}?statuses=${encodeURIComponent(st)}`);
  S.data._cid = S.cid; S.data._st = st;
  return S.data;
}

async function route() {
  if (!S.status) S.status = await api("/api/status");
  if (!S.colls) S.colls = await api("/api/collections");
  const h = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  try {
    if (h[0] === "ask") { S.cid = null; tabs(null, "#/ask"); filters(null); await viewAsk(h[1]); return; }
    if (h[0] === "query") { S.cid = null; tabs(null, "#/query"); filters(null); await viewQuery(h[1]); return; }
    if (h[0] === "datasets") { S.cid = null; tabs(null, "#/datasets"); filters(null); await (h[1] ? viewDataset(h[1]) : viewDatasets()); return; }
    if (h[0] === "network") { S.cid = null; tabs(null, "#/network"); filters(null); await viewNetwork(); return; }
    if (h[0] === "neighbourhoods") { S.cid = null; tabs(null, "#/neighbourhoods"); filters(null); await viewNeighbourhood(h.slice(1).join("/") || null); return; }
    if (h[0] === "map") { S.cid = null; tabs(null, "#/map"); filters(null); await viewMap(h[1] === "place" ? h.slice(2).join("/") : null); return; }
    if (h[0] === "places") { S.cid = null; tabs(null, "#/map"); filters(null); await viewPlaces(); return; }
    if (h[0] === "catasto") { S.cid = null; tabs(null, "#/catasto"); filters(null); await viewCatasto(h.slice(1).join("/") || null); return; }
    if (h[0] === "names") { S.cid = null; tabs(null, "#/names"); filters(null); await viewNames(h[1]); return; }
    if (h[0] === "m" && h[1]) {
      if (S.cid !== h[1]) { S.cid = h[1]; S.statuses = (await api(`/api/settings/${encodeURIComponent(h[1])}`)).statuses; S.data = null; S.focus = 0; }
      const tab = h[2] || "overview";
      tabs(tab); filters(tab);
      if (tab === "tags") { filters(null); await viewTags(h[3]); return; }
      if (tab === "holdings") { filters(null); await viewHoldings(h[3]); return; }
      await ({ overview: viewOverview, sums: viewSums, dates: viewDates, refs: viewRefs, settings: viewSettings }[tab] || viewOverview)();
    } else { S.cid = null; tabs(null, "#/"); filters(null); await viewHome(); }
  } catch (e) { $("#main").innerHTML = `<div class="empty err">${esc(e.message)}</div>`; }
}
window.addEventListener("hashchange", route);

function tabs(tab, top) {
  $("#crumbs").innerHTML = S.cid ? `<a href="#/">Manuscripts</a> › <b>${esc(S.cid)}</b> &nbsp; `
    + TABS.map(([k, t]) => `<a href="#/m/${encodeURIComponent(S.cid)}/${k}" class="sub ${k === tab ? "on" : ""}">${t}</a>`).join("") : "";
  $("#tabs").innerHTML = TOP.map(([h, t]) => `<a href="${h}" class="${h === top || (S.cid && h === "#/") ? "on" : ""}">${t}</a>`).join("");
}

function filters(tab) {
  const f = $("#filters");
  if (!S.cid || !tab || ["settings", "tags", "holdings"].includes(tab)) { f.hidden = true; return; }
  f.hidden = false;
  const c = S.colls.find((x) => x.id === S.cid) || { counts: {} };
  f.innerHTML = `<span class="muted">Pages:</span>` + S.status.statuses.map((s) =>
    `<span class="chip ${S.statuses.includes(s) ? "on" : ""}" data-s="${s}"><i style="background:var(--s-${s})"></i>${esc(S.status.labels[s] || s)} <span class="n">${c.counts[s] || 0}</span></span>`).join("")
    + `<span class="spacer"></span><button class="btn small" id="reload" title="Read the pages again (after editing in Leggio)">↻ Reload</button>`;
  f.querySelectorAll(".chip").forEach((el) => el.onclick = () => {
    const s = el.dataset.s;
    S.statuses = S.statuses.includes(s) ? S.statuses.filter((x) => x !== s) : [...S.statuses, s];
    route();
  });
  $("#reload").onclick = () => { S.data = null; route(); };
}

async function viewHome() {
  const ds = await api("/api/datasets");
  $("#main").innerHTML = `<div class="row"><h1>Manuscripts</h1><span class="spacer"></span><a class="btn primary" href="#/query">New query</a></div>
  <p class="muted">Conti reads Leggio's transcriptions (never changes them): people, places, occupations, institutions and goods (tags), dates, cross-references and sums.</p>
  <div class="grid">${S.colls.map((c) => {
    const tot = Object.values(c.counts).reduce((a, b) => a + b, 0);
    const done = (c.counts.finished || 0) + (c.counts.sent_to_training || 0);
    return `<a class="card" href="#/m/${encodeURIComponent(c.id)}/overview" style="color:inherit"><h2 style="margin:0 0 4px">${esc(c.title)}</h2>
      <div class="muted small">${tot} pages · ${done} finished or sent to training</div></a>`;
  }).join("")}</div>
  <h2>Datasets</h2>${ds.length ? `<div class="grid">${ds.map(dsCard).join("")}</div>` : `<p class="muted">None yet: build a query and save it as a dataset.</p>`}`;
}

async function viewOverview() {
  const d = await load();
  const s = d.summary;
  const t = (n, l) => `<div class="tile"><b>${n}</b><span>${l}</span></div>`;
  $("#main").innerHTML = `<h1>${esc(S.cid)}</h1>
  <p class="muted">${s.pages} pages, ${s.lines} lines of text (statuses chosen above). Dates are read in the <b>${esc(d.settings.date_style)}</b> style (change in Settings).</p>
  <div class="tiles">${t(s.sums, "lines with a sum")}${t(s.sums_confirmed, "sums you have checked")}${t(s.sums_with_problems, "sums with a problem, unchecked")}
  ${t(s.dates, "dates found")}${t(s.refs, "cross-references")}${t(s.debit, "de dare entries")}${t(s.credit, "de avere / anno dato")}${t(s.balance, "resta a dare")}${t(s.sums, "lines with a sum")}${t(s.sums_confirmed, "sums checked")}</div>
  <h2>Next</h2><p><a class="btn primary" href="#/m/${encodeURIComponent(S.cid)}/tags">Review the tags →</a> <a class="btn" href="#/query">Query →</a></p>`;
}

/* ------------------------------------------------------------------ sums */
const hasAmt = (r) => r.amount && !r.amount.empty;
const SUMF = [
  ["review", "To check", (r) => hasAmt(r) && !r.amount_confirmed],
  ["problems", "Problems", (r) => hasAmt(r) && !r.amount_confirmed && r.amount.problems.some((p) => p.code !== "joined")],
  ["changed", "Changed since checked", (r) => r.review && r.review.state === "changed"],
  ["confirmed", "Checked", (r) => r.amount_confirmed],
  ["nofig", "Sum box without a figure", (r) => r.sum && !hasAmt(r)],
  ["all", "All", (r) => hasAmt(r) || r.sum || r.review],
];
const valueHtml = (a) => a && !a.empty ? `<div class="value">${esc(a.display)}</div>` : `<div class="value none">no figure</div>`;

function sumList() {
  const d = S.data, f = SUMF.find((x) => x[0] === S.sumFilter)[2];
  const q = S.q.trim().toLowerCase();
  let xs = d.records.filter(f);
  if (q) xs = xs.filter((r) => (r.text + " " + r.sum + " " + r.page).toLowerCase().includes(q));
  if (S.sumFilter === "review") xs.sort((a, b) => (b.amount.problems.length > 0) - (a.amount.problems.length > 0));
  return xs;
}

async function viewSums() {
  await load();
  const counts = Object.fromEntries(SUMF.map(([k, , f]) => [k, S.data.records.filter(f).length]));
  $("#main").innerHTML = `<div class="row" style="margin-bottom:12px">
    <div class="seg">${SUMF.map(([k, t]) => `<button data-f="${k}" class="${k === S.sumFilter ? "on" : ""}">${t} <span class="small">${counts[k]}</span></button>`).join("")}</div>
    <input type="search" id="q" placeholder="Search text, sum, page" value="${esc(S.q)}" style="width:220px">
    <span class="spacer"></span>
    <span class="muted small"><span class="kbd">J</span>/<span class="kbd">K</span> move · <span class="kbd">A</span> right · <span class="kbd">C</span> correct · <span class="kbd">N</span> not a sum</span></div>
    <div id="list"></div>`;
  $("#main").querySelectorAll(".seg button").forEach((b) => b.onclick = () => { S.sumFilter = b.dataset.f; S.shown = 40; S.focus = 0; viewSums(); });
  $("#q").oninput = (e) => { S.q = e.target.value; S.shown = 40; drawSums(); };
  drawSums();
}

function drawSums() {
  const xs = sumList(), list = $("#list");
  SUMF.forEach(([k, , f]) => { const b = $(`.seg button[data-f="${k}"] .small`); if (b) b.textContent = S.data.records.filter(f).length; });
  if (!xs.length) { list.innerHTML = `<div class="empty">Nothing here.</div>`; return; }
  list.innerHTML = xs.slice(0, S.shown).map((r, i) => sumCard(r, i)).join("")
    + (xs.length > S.shown ? `<button class="btn more" id="more">Show more (${xs.length - S.shown} left)</button>` : "");
  if ($("#more")) $("#more").onclick = () => { S.shown += 40; drawSums(); };
  list.querySelectorAll(".sum").forEach(wireCard);
  const el = list.querySelectorAll(".sum")[Math.min(S.focus, xs.length - 1)];
  if (el) el.focus({ preventScroll: true });
}

function cropUrl(r, ids) { return `/api/crop/${encodeURIComponent(S.cid)}/${encodeURIComponent(r.page)}?ids=${encodeURIComponent(ids)}`; }

function sumCard(r, i) {
  const ids = r.line_ids.split(","), sub = ids.slice(1).join(",");
  const a = r.amount, rv = r.review;
  const leggio = `${S.data.settings.leggio_url}/#/p/${encodeURIComponent(S.cid)}/${encodeURIComponent(r.page)}`;
  const probs = (a ? a.problems : []).map((p) => `<li class="${p.code === "joined" ? "info" : ""}">${esc(p.msg)}</li>`).join("");
  let stateHtml = "";
  if (rv) {
    const what = rv.decision === "ok" ? "checked: right" : rv.decision === "not_sum" ? "checked: not a sum" : `corrected to ${rv.value ? rv.value.display : rv.text}`;
    stateHtml = rv.state === "confirmed" ? `<div class="state confirmed">✓ ${esc(what)}</div>`
      : `<div class="state changed">⚠ ${esc(what)} — but the transcription changed since (was “${esc(rv.written)}”)</div>`;
  }
  return `<div class="sum card" tabindex="0" data-i="${i}" data-key="${esc(r.key)}">
    <div>
      <div class="meta"><b>${esc(r.page)}</b><span>line ${r.line}</span>${r.folio ? `<span>f. ${esc(r.folio)}</span>` : ""}
        ${r.kind ? `<span class="badge ${r.kind}">${esc(KIND[r.kind])}</span>` : ""}<span class="badge">${esc(r.amount_source || "")}</span>
        <a href="${leggio}" target="leggio">Open in Leggio ↗</a></div>
      <div class="crops"><img class="crop" loading="lazy" src="${cropUrl(r, ids[0])}" alt="" onerror="this.hidden=true">${sub ? `<img class="crop sumcrop" loading="lazy" src="${cropUrl(r, sub)}" alt="" onerror="this.hidden=true">` : ""}</div>
      <div class="ms">${esc(r.text)}</div>
      <div class="written small muted">Sum box: ${r.sum ? `<code>${esc(r.sum)}</code>` : "—"} &nbsp; Read from: <code>${esc(r.amount_written || "—")}</code></div>
    </div>
    <div>
      ${rv && rv.state === "confirmed" && rv.decision === "corrected" ? valueHtml(rv.value) + `<div class="small muted">machine reading: ${esc(a && !a.empty ? a.display : "—")}</div>`
        : rv && rv.state === "confirmed" && rv.decision === "not_sum" ? `<div class="value none"><s>${esc(a && !a.empty ? a.display : "")}</s> not a sum</div>` : valueHtml(a)}
      ${a && a.lsd_denari != null ? `<div class="small muted">lire money = ${a.lsd_denari} denari${a.florins != null ? "; florins kept apart" : ""}</div>` : ""}
      ${a && a.florin_parts ? `<div class="small muted">ß and 𝒹 here are parts of the florin (a fiorino)</div>` : ""}
      ${probs && !(rv && rv.state === "confirmed") ? `<ul class="probs">${probs}</ul>` : ""}
      ${stateHtml}
      <div class="actions">
        <button class="btn small ok" data-a="ok" title="A">✓ Right</button>
        <button class="btn small" data-a="fix" title="C">✎ Correct</button>
        <button class="btn small bad" data-a="not_sum" title="N">✗ Not a sum</button>
        ${rv ? `<button class="btn small" data-a="clear">↺ Undo</button>` : ""}
      </div>
      <div class="fix" hidden>
        <input type="text" placeholder="e.g. ƒ ii ℔ x ß xii 𝒹 vi pc̄  or  ƒ 2 ℔ 10 ß 12 𝒹 6">
        <div class="small muted prev">Type the sum; signs before figures.</div>
        <div class="row"><button class="btn small primary" data-a="save">Save</button><button class="btn small" data-a="cancel">Cancel</button>
        <span class="small muted">${["ƒ", S.data.settings.pound, "ß", "𝒹", "pc̄"].map((c) => `<button class="btn small" data-ins="${c}">${c}</button>`).join(" ")}</span></div>
      </div>
    </div></div>`;
}

function wireCard(el) {
  const key = el.dataset.key;
  const r = S.data.records.find((x) => x.key === key);
  el.onfocus = () => { S.focus = +el.dataset.i; };
  el.querySelectorAll("[data-a]").forEach((b) => b.onclick = (ev) => { ev.stopPropagation(); act(el, r, b.dataset.a); });
  const inp = $(".fix input", el);
  let t;
  inp.oninput = () => { clearTimeout(t); t = setTimeout(async () => {
    if (!inp.value.trim()) { $(".prev", el).textContent = ""; return; }
    const a = await api(`/api/parse?cid=${encodeURIComponent(S.cid)}&text=${encodeURIComponent(inp.value)}`);
    $(".prev", el).innerHTML = a.empty ? `<span class="err">no figure yet</span>` : `→ ${esc(a.display)} ${a.problems.length ? `<span class="err">(${esc(a.problems.map((p) => p.msg).join("; "))})</span>` : ""}`;
  }, 200); };
  inp.onkeydown = (e) => { e.stopPropagation(); if (e.key === "Enter") act(el, r, "save"); if (e.key === "Escape") act(el, r, "cancel"); };
  el.querySelectorAll("[data-ins]").forEach((b) => b.onclick = (e) => {
    e.stopPropagation(); const p = inp.selectionStart ?? inp.value.length;
    inp.value = inp.value.slice(0, p) + b.dataset.ins + " " + inp.value.slice(p); inp.focus(); inp.oninput();
  });
}

async function act(el, r, a) {
  if (a === "fix") { $(".fix", el).hidden = false; const i = $(".fix input", el); i.value = (r.review && r.review.text || r.amount_written || "").replace(/\s*\|\s*/g, " "); i.focus(); i.select(); i.oninput(); return; }
  if (a === "save") {
    const chk = await api(`/api/parse?cid=${encodeURIComponent(S.cid)}&text=${encodeURIComponent($(".fix input", el).value)}`);
    const bad = chk.problems.filter((p) => ["word", "twice", "no-sign", "unreadable", "order"].includes(p.code));
    if (chk.empty || bad.length) { $(".prev", el).innerHTML = `<span class="err">Not saved: ${esc(chk.empty ? "no figure" : bad.map((p) => p.msg).join("; "))}</span>`; return; }
  }
  if (a === "cancel") { $(".fix", el).hidden = true; el.focus(); return; }
  const body = { key: r.key, written: r.amount_written, decision: a === "save" ? "corrected" : a };
  if (a === "save") body.text = $(".fix input", el).value;
  try {
    const res = await api(`/api/review/${encodeURIComponent(S.cid)}`, { method: "POST", body });
    r.review = res.review;
    r.amount_confirmed = !!(res.review && res.review.state === "confirmed");
    if (a !== "clear") S.focus = +el.dataset.i + (SUMF.find((x) => x[0] === S.sumFilter)[2](r) ? 1 : 0);
    drawSums();
  } catch (e) { alertBar(e.message); }
}

function alertBar(m, good) { const d = document.createElement("div"); d.className = "card" + (good ? "" : " err"); d.style.cssText = "position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:50"; d.textContent = m; document.body.append(d); setTimeout(() => d.remove(), 4000); }

document.addEventListener("keydown", (e) => {
  if (!location.hash.includes("/sums") || e.target.tagName === "INPUT" || e.metaKey || e.ctrlKey) return;
  const cards = [...document.querySelectorAll(".sum")];
  const cur = document.activeElement && document.activeElement.classList.contains("sum") ? document.activeElement : cards[S.focus];
  if (!cur) return;
  const k = e.key.toLowerCase();
  const go = (d) => { const n = cards[Math.max(0, Math.min(cards.length - 1, cards.indexOf(cur) + d))]; if (n) { n.focus(); n.scrollIntoView({ block: "nearest" }); } };
  if (k === "j" || e.key === "ArrowDown") { e.preventDefault(); go(1); }
  else if (k === "k" || e.key === "ArrowUp") { e.preventDefault(); go(-1); }
  else if (k === "a") { e.preventDefault(); $('[data-a="ok"]', cur).click(); }
  else if (k === "n") { e.preventDefault(); $('[data-a="not_sum"]', cur).click(); }
  else if (k === "c") { e.preventDefault(); $('[data-a="fix"]', cur).click(); }
});

/* ------------------------------------------------------------------ dates */
async function viewDates() {
  const d = await load();
  const rows = d.records.flatMap((r) => r.dates.map((x) => ({ r, x })));
  const style = d.settings.date_style;
  $("#main").innerHTML = `<h1>Dates</h1>
  <p class="muted">${rows.length} dates. Each keeps the year <b>as written</b> and the <b>modern</b> year (${style === "florentine" ? "Florentine style: the year begins 25 March, so 1 January – 24 March is one year later in modern reckoning" : style === "pisan" ? "Pisan style: 25 March – 31 December is one year earlier in modern reckoning" : "modern style: no change"}).
  <span class="inf">Orange</span> years were not written in the entry: they are carried forward from the last year written above.</p>
  <table><thead><tr><th>Page</th><th>Line</th><th>As written</th><th>Day</th><th>Month</th><th>Year as written</th><th>Modern year</th><th>Modern date</th><th>Entry</th></tr></thead><tbody>
  ${rows.map(({ r, x }) => `<tr><td>${esc(r.page)}</td><td class="num">${r.line}</td><td class="ms">${esc(x.raw)}</td><td class="num">${x.day ?? ""}</td><td>${esc(x.month_name)}</td>
    <td class="num ${x.year_inferred ? "inf" : ""}" ${x.year_inferred ? `title="carried forward from ${esc(x.year_from || "")}"` : ""}>${x.year_written ?? "?"}</td>
    <td class="num">${x.year_modern ?? "?"}${x.year_modern !== x.year_written && x.year_modern ? " ↑" : ""}${x.ambiguous ? ' <span class="inf" title="March without a day: before or after the 25th?">?</span>' : ""}</td>
    <td>${esc(x.iso_modern || "")}</td><td class="ms small">${esc(r.text.slice(0, 90))}</td></tr>`).join("")}
  </tbody></table>`;
}

/* ------------------------------------------------------------------ references */
async function viewRefs() {
  const d = await load();
  const rows = d.records.flatMap((r) => r.refs.map((x) => ({ r, x })));
  const byBook = {};
  rows.forEach(({ x }) => { const b = x.book_resolved || "?"; byBook[b] = (byBook[b] || 0) + 1; });
  const books = Object.entries(byBook).sort((a, b) => b[1] - a[1]);
  $("#main").innerHTML = `<h1>Cross-references</h1>
  <p class="muted">${rows.length} references to folios (ac̄ 41, acār 309, a carte …). “Book” is the book named before the reference; “libro detto” / “entrata detta” point back to the last book of that kind named; “(this book)” = no book named.</p>
  <div class="row" style="margin-bottom:12px">${books.map(([b, n]) => `<span class="chip">${esc(b)} <span class="n">${n}</span></span>`).join("")}</div>
  <table><thead><tr><th>Page</th><th>Line</th><th>As written</th><th>Folio(s)</th><th>Book (as written)</th><th>Book (resolved)</th><th>Entry</th></tr></thead><tbody>
  ${rows.map(({ r, x }) => `<tr><td>${esc(r.page)}</td><td class="num">${r.line}</td><td class="ms">${esc(x.raw)}</td><td class="num">${x.folios.join(", ")}</td>
    <td>${esc(x.book || "")}</td><td>${esc(x.book_resolved || "")}</td><td class="ms small">${esc(r.text.slice(0, 90))}</td></tr>`).join("")}
  </tbody></table>`;
}

/* ------------------------------------------------------------------ settings */
async function viewSettings() {
  const s = await api(`/api/settings/${encodeURIComponent(S.cid)}`);
  const radio = (v, t, d) => `<label style="display:block;margin:6px 0"><input type="radio" name="ds" value="${v}" ${s.date_style === v ? "checked" : ""}> <b>${t}</b> <span class="muted small">${d}</span></label>`;
  $("#main").innerHTML = `<h1>Settings for ${esc(S.cid)}</h1><div class="card" style="max-width:720px">
    <h2 style="margin-top:0">Dating style</h2>
    ${radio("florentine", "Florentine", "year begins 25 March; 1 Jan – 24 Mar of 1388 is 1389 in modern reckoning")}
    ${radio("pisan", "Pisan", "year begins 25 March of the year before")}
    ${radio("modern", "Modern", "year begins 1 January")}
    <h2>Pound sign</h2><input type="text" id="pound" value="${esc(s.pound)}" style="width:60px"> <span class="muted small">used when showing sums (from Leggio's conventions for this manuscript)</span>
    <h2>Pages included by default</h2>
    ${S.status.statuses.map((x) => `<label style="margin-right:12px"><input type="checkbox" class="st" value="${x}" ${s.statuses.includes(x) ? "checked" : ""}> ${esc(S.status.labels[x] || x)}</label>`).join("")}
    <h2>Account holder</h2><input type="text" id="holder" value="${esc(s.account_holder || "")}" style="width:260px" placeholder="e.g. Heirs of Deo di Vanni">
    <span class="muted small">who is owed when a <i>de dare</i> entry names no creditor (Ask tab: shown as “assumed”)</span>
    <h2>Leggio address</h2><input type="text" id="lurl" value="${esc(s.leggio_url)}" style="width:260px">
    <p style="margin-top:20px"><button class="btn primary" id="save">Save</button> <span id="msg" class="muted"></span></p></div>`;
  $("#save").onclick = async () => {
    const body = { date_style: $('input[name="ds"]:checked').value, pound: $("#pound").value.trim() || "℔",
      statuses: [...document.querySelectorAll(".st:checked")].map((x) => x.value), leggio_url: $("#lurl").value.trim(), account_holder: $("#holder").value.trim() };
    await api(`/api/settings/${encodeURIComponent(S.cid)}`, { method: "PUT", body });
    S.statuses = body.statuses; S.data = null; $("#msg").textContent = "Saved.";
  };
}

route();
