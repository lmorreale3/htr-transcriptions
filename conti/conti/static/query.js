/* Query builder (#/query), datasets (#/datasets, #/datasets/<id>), names and merging (#/names) */
const FIELDS = [
  ["person", "Person", "tag"], ["place", "Place", "tag"], ["occupation", "Occupation / role", "tag"], ["institution", "Institution", "tag"],
  ["goods", "Goods", "tag"], ["any_tag", "Any tag", "tag"], ["text", "Text", "text"], ["kind", "Kind of entry", "kind"],
  ["year", "Year", "range"], ["date", "Date (modern)", "drange"], ["month", "Month", "month"], ["page", "Pages", "pages"],
  ["book", "Book referred to", "str"], ["folio", "Folio referred to", "num"], ["has_sum", "Has a sum", "bool"],
  ["florins", "Florins", "cmp"], ["lire", "Lire money (in lire)", "cmp"], ["flagged", "Flagged in Leggio", "flag"],
];
const OPS = {
  tag: [["contains", "name contains"], ["is", "name is"], ["exists", "is named"], ["not_exists", "is not named"]],
  text: [["contains", "contains"], ["not_contains", "does not contain"], ["regex", "matches (regex)"]],
  kind: [["is", "is"]], range: [["between", "between"]], drange: [["between", "between"]], month: [["is", "is"]],
  pages: [["between", "from … to"]], str: [["contains", "contains"]], num: [["is", "is"]], bool: [["is", "is"]],
  cmp: [["gte", "at least"], ["lte", "at most"]], flag: [["is", "is"]],
};
const MONTHS = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"];
const GROUPBY = [["", "—"], ["person", "person"], ["place", "place"], ["occupation", "occupation / role"], ["institution", "institution"], ["goods", "goods"],
  ["role", "role of person"], ["year_modern", "year (modern)"], ["year_written", "year (as written)"], ["month", "month"], ["kind", "kind of entry"],
  ["book", "book referred to"], ["page", "page"], ["manuscript", "manuscript"]];
let Q = null;
const QDEF = () => ({ manuscripts: [], statuses: null, unit: "lines", tag_types: [], approved_only: false, match: "all", conditions: [], group_by: "" });
function qSave() { try { sessionStorage.setItem("conti_q", JSON.stringify(Q)); } catch (e) {} }
function qLoad() { try { return JSON.parse(sessionStorage.getItem("conti_q")); } catch (e) { return null; } }

async function viewQuery(fromDataset) {
  if (fromDataset) { const d = await api(`/api/datasets/${encodeURIComponent(fromDataset)}?limit=1`); Q = { ...QDEF(), ...d.query, _dataset: d.id, _name: d.name }; }
  if (!Q) Q = qLoad() || QDEF();
  if (!Q.manuscripts.length) Q.manuscripts = S.colls.filter((c) => (c.counts.finished || 0) + (c.counts.sent_to_training || 0)).map((c) => c.id).slice(0, 1);
  await loadNames();
  $("#main").innerHTML = `<div class="row"><h1>Query</h1>${Q._dataset ? `<span class="badge">editing dataset “${esc(Q._name)}”</span>` : ""}<span class="spacer"></span>
      <button class="btn small" id="qnew">Clear</button></div>
    <div class="card qb">
      <div class="row"><span class="lab">Manuscripts</span>${S.colls.map((c) => `<span class="chip ${Q.manuscripts.includes(c.id) ? "on" : ""}" data-ms="${esc(c.id)}">${esc(c.title)}</span>`).join("")}
        <span class="small muted">pages: each manuscript's default statuses (Settings)</span></div>
      <div class="row"><span class="lab">Show</span><div class="seg" id="unit">${[["lines", "Lines"], ["entries", "Entries"], ["tags", "Tags"]].map(([k, t]) => `<button data-u="${k}" class="${Q.unit === k ? "on" : ""}">${t}</button>`).join("")}</div>
        <span id="ttypes">${Q.unit === "tags" ? TYPES.map((t) => `<span class="chip ${(Q.tag_types.length ? Q.tag_types.includes(t) : true) ? "on" : ""}" data-tt="${t}"><i style="background:${TCOL[t]}"></i>${TLABEL[t]}</span>`).join("") : ""}</span>
        <label class="small"><input type="checkbox" id="apo" ${Q.approved_only ? "checked" : ""}> only tags I have checked</label></div>
      <div class="row"><span class="lab">Where</span><select id="match"><option value="all" ${Q.match !== "any" ? "selected" : ""}>all of these are true</option><option value="any" ${Q.match === "any" ? "selected" : ""}>any of these is true</option></select></div>
      <div id="conds"></div>
      <div class="row"><button class="btn small" id="addc">+ Condition</button><span class="spacer"></span>
        <span class="lab">Count by</span><select id="gby">${GROUPBY.map(([k, t]) => `<option value="${k}" ${Q.group_by === k ? "selected" : ""}>${t}</option>`).join("")}</select>
        <button class="btn small" id="xl">Export .xlsx</button><button class="btn small" id="csv">.csv</button>
        <button class="btn small primary" id="savds">${Q._dataset ? "Update dataset" : "Save as dataset"}</button></div>
    </div>
    <div id="qres"></div>`;
  $("#qnew").onclick = () => { Q = QDEF(); qSave(); viewQuery(); };
  document.querySelectorAll("[data-ms]").forEach((el) => el.onclick = () => { const m = el.dataset.ms; Q.manuscripts = Q.manuscripts.includes(m) ? Q.manuscripts.filter((x) => x !== m) : [...Q.manuscripts, m]; el.classList.toggle("on"); runQ(); });
  document.querySelectorAll("#unit button").forEach((b) => b.onclick = () => { Q.unit = b.dataset.u; viewQuery(); });
  document.querySelectorAll("[data-tt]").forEach((el) => el.onclick = () => {
    const cur = Q.tag_types.length ? Q.tag_types : [...TYPES]; const t = el.dataset.tt;
    Q.tag_types = cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]; el.classList.toggle("on"); runQ(); });
  $("#apo").onchange = (e) => { Q.approved_only = e.target.checked; runQ(); };
  $("#match").onchange = (e) => { Q.match = e.target.value; runQ(); };
  $("#gby").onchange = (e) => { Q.group_by = e.target.value; runQ(); };
  $("#addc").onclick = () => { Q.conditions.push({ field: "person", op: "contains", value: "" }); drawConds(); };
  $("#xl").onclick = () => download("/api/query/export", { query: clean(Q), format: "xlsx", group_by: Q.group_by });
  $("#csv").onclick = () => download("/api/query/export", { query: clean(Q), format: "csv" });
  $("#savds").onclick = saveDatasetDialog;
  drawConds(); runQ();
}

function clean(q) { const { _dataset, _name, group_by, ...rest } = q; return rest; }

function condValue(c, kind, i) {
  const v = c.value;
  if (kind === "tag") return c.op === "exists" || c.op === "not_exists" ? "" : `<input type="text" data-v="${i}" value="${esc(v || "")}" list="nm-${c.field === "any_tag" ? "person" : c.field}" placeholder="name">`;
  if (kind === "kind") return `<select data-v="${i}">${[["debit", "de dare"], ["credit", "de avere / anno dato"], ["balance", "resta a dare"], ["none", "none of these"]].map(([k, t]) => `<option value="${k}" ${v === k ? "selected" : ""}>${t}</option>`).join("")}</select>`;
  if (kind === "range" || kind === "drange") {
    const a = (v || [])[0] || "", b = (v || [])[1] || "", ph = kind === "range" ? ["1388", "1390"] : ["1388-03-25", "1389-12"];
    return `<input type="text" data-v0="${i}" value="${esc(a)}" placeholder="${ph[0]}" style="width:110px"> and <input type="text" data-v1="${i}" value="${esc(b)}" placeholder="${ph[1]}" style="width:110px">`
      + (kind === "range" ? ` <select data-which="${i}"><option value="modern" ${c.which !== "written" ? "selected" : ""}>modern year</option><option value="written" ${c.which === "written" ? "selected" : ""}>year as written</option></select>` : "");
  }
  if (kind === "month") return `<select data-v="${i}">${MONTHS.map((m, k) => `<option value="${k + 1}" ${+v === k + 1 ? "selected" : ""}>${m}</option>`).join("")}</select>`;
  if (kind === "pages") return `<input type="text" data-v0="${i}" value="${esc((v || [])[0] || "")}" placeholder="RS1120…"> to <input type="text" data-v1="${i}" value="${esc((v || [])[1] || "")}" placeholder="RS1140…">`;
  if (kind === "bool") return `<select data-v="${i}"><option value="true" ${v !== "false" ? "selected" : ""}>yes</option><option value="false" ${v === "false" ? "selected" : ""}>no</option></select>`;
  if (kind === "flag") return `<select data-v="${i}"><option value="true">yes</option></select>`;
  return `<input type="text" data-v="${i}" value="${esc(v ?? "")}" ${kind === "num" || kind === "cmp" ? 'style="width:90px"' : ""}>`;
}

function drawConds() {
  const box = $("#conds");
  box.innerHTML = Q.conditions.map((c, i) => {
    const kind = FIELDS.find((f) => f[0] === c.field)[2];
    return `<div class="row cond">
      <select data-f="${i}">${FIELDS.map(([k, t]) => `<option value="${k}" ${k === c.field ? "selected" : ""}>${t}</option>`).join("")}</select>
      <select data-op="${i}">${OPS[kind].map(([k, t]) => `<option value="${k}" ${k === c.op ? "selected" : ""}>${t}</option>`).join("")}</select>
      ${condValue(c, kind, i)}
      ${c.field === "person" || c.field === "any_tag" ? `<select data-role="${i}" title="role in the entry"><option value="">any role</option>${ROLES.map((r) => `<option ${((c.attr || {}).role === r) ? "selected" : ""}>${r}</option>`).join("")}</select>` : ""}
      ${kind === "tag" ? `<select data-scope="${i}"><option value="line">in the line</option><option value="entry" ${c.scope === "entry" ? "selected" : ""}>anywhere in the entry</option></select>` : ""}
      <button class="btn small ghost" data-x="${i}" title="Remove">✕</button></div>`;
  }).join("") || `<div class="small muted" style="padding:4px 0">No conditions: everything in the chosen manuscripts.</div>`;
  const upd = () => { runQ(); };
  box.querySelectorAll("[data-f]").forEach((el) => el.onchange = () => {
    const c = Q.conditions[+el.dataset.f]; c.field = el.value; const kind = FIELDS.find((f) => f[0] === c.field)[2];
    c.op = OPS[kind][0][0]; c.value = kind === "bool" || kind === "flag" ? "true" : kind === "month" ? 1 : kind === "kind" ? "debit" : ""; delete c.attr; delete c.scope;
    drawConds(); upd(); });
  box.querySelectorAll("[data-op]").forEach((el) => el.onchange = () => { Q.conditions[+el.dataset.op].op = el.value; drawConds(); upd(); });
  let tm;
  const deb = () => { clearTimeout(tm); tm = setTimeout(upd, 350); };
  box.querySelectorAll("[data-v]").forEach((el) => el[el.tagName === "SELECT" ? "onchange" : "oninput"] = () => { Q.conditions[+el.dataset.v].value = el.value; deb(); });
  box.querySelectorAll("[data-v0],[data-v1]").forEach((el) => el.oninput = () => {
    const i = +(el.dataset.v0 ?? el.dataset.v1), c = Q.conditions[i]; c.value = [...(c.value || ["", ""])];
    c.value[el.dataset.v0 !== undefined ? 0 : 1] = el.value; deb(); });
  box.querySelectorAll("[data-which]").forEach((el) => el.onchange = () => { Q.conditions[+el.dataset.which].which = el.value; upd(); });
  box.querySelectorAll("[data-role]").forEach((el) => el.onchange = () => { Q.conditions[+el.dataset.role].attr = el.value ? { role: el.value } : undefined; upd(); });
  box.querySelectorAll("[data-scope]").forEach((el) => el.onchange = () => { Q.conditions[+el.dataset.scope].scope = el.value; upd(); });
  box.querySelectorAll("[data-x]").forEach((el) => el.onclick = () => { Q.conditions.splice(+el.dataset.x, 1); drawConds(); upd(); });
}

let qSeq = 0;
async function runQ() {
  qSave();
  const seq = ++qSeq, box = $("#qres");
  box.innerHTML = `<div class="muted" style="padding:12px">Searching…</div>`;
  try {
    const res = await api("/api/query", { method: "POST", body: { query: clean(Q), group_by: Q.group_by, limit: 300 } });
    if (seq !== qSeq) return;
    box.innerHTML = resultsHtml(res, Q.group_by);
    wireResults(box, res);
  } catch (e) { box.innerHTML = `<div class="empty err">${esc(e.message)}</div>`; }
}

function unitWord(u, n) { return { lines: n === 1 ? "line" : "lines", entries: n === 1 ? "entry" : "entries", tags: n === 1 ? "tag" : "tags" }[u]; }

function resultsHtml(res, gby, opts = {}) {
  const head = `<div class="row" style="margin:14px 0 8px"><b>${res.count} ${unitWord(res.unit, res.count)}</b>
    <span class="muted small">${res.lines_searched != null ? `searched ${res.lines_searched} lines · ` : ""}${res.truncated ? `showing the first ${res.rows.length}; export for all` : ""}</span></div>`;
  const groups = res.groups ? `<div class="groups card"><div class="small muted" style="margin-bottom:6px">Count by ${esc(gby)} — click a ${["person", "place", "occupation", "institution", "goods"].includes(gby) ? "name to add it as a condition" : "row"}</div>
    <table class="gtable"><thead><tr><th>${esc(gby)}</th><th class="num">${unitWord(res.unit, 2)}</th><th>first date</th><th>last date</th><th></th></tr></thead><tbody>
    ${res.groups.length ? "" : `<tr><td colspan="5" class="muted">No ${esc(gby)} in these results.</td></tr>`}${res.groups.slice(0, 200).map((g) => { const max = res.groups[0].rows || 1; return `<tr data-g="${esc(g.value)}"><td>${esc(g.value)}</td><td class="num">${g.rows}</td><td>${esc(g.first || "")}</td><td>${esc(g.last || "")}</td>
      <td style="width:35%"><div class="gbar" style="width:${(100 * g.rows / max).toFixed(1)}%"></div></td></tr>`; }).join("")}</tbody></table></div>` : "";
  let body;
  if (res.unit === "tags") {
    body = `<table><thead><tr><th>Type</th><th>Name</th><th>As written</th><th>Details</th><th>Page · line</th><th>Date</th><th>Line</th>${opts.exclude ? "<th></th>" : ""}</tr></thead><tbody>
    ${res.rows.map((r, i) => `<tr data-i="${i}"><td><span class="tchip ${r.type}"><i></i>${esc(TLABEL[r.type])}</span></td><td><b>${esc(r.name)}</b>${r.tag_status === "suggested" ? ' <span class="sg" title="not yet checked">?</span>' : ""}</td>
      <td class="ms">${esc(r.span)}</td><td class="small">${esc(Object.entries(r.attrs || {}).filter(([k]) => k !== "uncertain").map(([k, v]) => `${k}: ${v}`).join(" · "))}</td>
      <td class="small">${esc(r.page)} · ${r.line}</td><td class="small">${esc((r.dates || []).map((d) => d.iso_modern).filter(Boolean).join(", "))}</td>
      <td class="ms small">${highlight(r.text, [{ span: r.span, type: r.type, status: r.tag_status, canon: r.name }])}</td>${opts.exclude ? `<td><button class="btn small ghost" data-ex="${esc(r.key)}" title="Take out of the dataset">✕</button></td>` : ""}</tr>`).join("")}</tbody></table>`;
  } else {
    body = `<table><thead><tr><th>Page · line</th><th>Text</th><th>Tags</th><th>Date</th><th>Kind</th>${opts.exclude ? "<th></th>" : ""}</tr></thead><tbody>
    ${res.rows.map((r, i) => `<tr data-i="${i}" class="rrow"><td class="small nowrap">${esc(r.manuscript === (res.rows[0] || {}).manuscript ? "" : r.manuscript + " ")}${esc(r.page)}<br>line ${r.line}${r.last_line && r.last_line !== r.line ? `–${r.last_line}` : ""}</td>
      <td class="ms">${highlight(r.text, r.tags)}${r.sum ? ` <span class="small muted">[${esc(r.sum)}]</span>` : ""}</td>
      <td>${dedupe(r.tags).map((t) => chip(t)).join(" ")}</td>
      <td class="small nowrap">${esc((r.dates || []).map((d) => d.iso_modern + (d.year_modern !== d.year_written ? ` (${d.year_written} fl.)` : "")).filter((x) => x && !x.startsWith("null")).join("\n"))}</td>
      <td class="small">${esc(KIND[r.kind] || "")}</td>${opts.exclude ? `<td><button class="btn small ghost" data-ex="${esc(r.key)}" title="Take out of the dataset">✕</button></td>` : ""}</tr>
      <tr class="detail" hidden><td></td><td colspan="${opts.exclude ? 5 : 4}"></td></tr>`).join("")}</tbody></table>`;
  }
  return head + groups + (res.rows.length ? body : `<div class="empty">No results.</div>`);
}

function dedupe(tags) { const seen = new Set(); return (tags || []).filter((t) => { const k = t.type + "|" + t.canon; if (seen.has(k)) return false; seen.add(k); return true; }); }

function wireResults(box, res, opts = {}) {
  box.querySelectorAll("tr[data-g]").forEach((tr) => tr.onclick = () => {
    if (!opts.dataset && TYPES.includes(Q.group_by)) { Q.conditions.push({ field: Q.group_by, op: "is", value: tr.dataset.g }); drawConds(); runQ(); }
  });
  box.querySelectorAll("tr.rrow").forEach((tr) => tr.onclick = (e) => {
    if (e.target.closest("button,a,.tchip")) return;
    const r = res.rows[+tr.dataset.i], det = tr.nextElementSibling;
    det.hidden = !det.hidden;
    if (!det.hidden && !det.dataset.done) {
      det.dataset.done = 1;
      const ids = r.line_ids.split(",");
      det.children[1].innerHTML = `${r.translation ? `<div class="small">${esc(r.translation)}</div>` : ""}
        <img class="crop" src="/api/crop/${encodeURIComponent(r.manuscript)}/${encodeURIComponent(r.page)}?ids=${encodeURIComponent(ids.join(","))}" onerror="this.replaceWith('')" style="max-height:220px">
        <div class="small"><a href="http://127.0.0.1:8770/#/p/${encodeURIComponent(r.manuscript)}/${encodeURIComponent(r.page)}" target="leggio">Open in Leggio ↗</a> ·
        <a href="#/m/${encodeURIComponent(r.manuscript)}/tags/${encodeURIComponent(r.page)}">Review tags on this page</a></div>`;
    }
  });
}

async function download(url, body) {
  try {
    const r = await fetch(url, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
    const cd = r.headers.get("Content-Disposition") || ""; const m = /filename\*=UTF-8''([^;]+)/.exec(cd);
    const name = m ? decodeURIComponent(m[1]) : "conti_export";
    const a = document.createElement("a"); a.href = URL.createObjectURL(await r.blob()); a.download = name; a.click();
    alertBar(`Saved ${name} (also in conti_data/_exports)`, true);
  } catch (e) { alertBar(e.message); }
}

function saveDatasetDialog() {
  const d = document.createElement("div"); d.className = "modal";
  d.innerHTML = `<div class="card" style="width:min(520px,92vw)"><h2 style="margin-top:0">${Q._dataset ? "Update dataset" : "Save as dataset"}</h2>
    <label>Name<br><input type="text" id="dsn" value="${esc(Q._name || "")}" style="width:100%"></label>
    <label style="display:block;margin-top:8px">Description<br><input type="text" id="dsd" style="width:100%" placeholder="what it is for"></label>
    <div style="margin-top:10px"><label><input type="radio" name="dsm" value="live" checked> <b>Growing</b> <span class="small muted">re-runs the query each time, so it grows as pages are finished and tagged</span></label><br>
    <label><input type="radio" name="dsm" value="snapshot"> <b>Fixed snapshot</b> <span class="small muted">keeps exactly today's results</span></label></div>
    <p class="small muted">${esc(Q.manuscripts.length > 1 ? "Across " + Q.manuscripts.join(", ") : "Manuscript: " + Q.manuscripts.join(", "))}. Add more manuscripts to the query for a cumulative dataset.</p>
    <div class="row"><button class="btn primary" id="dsok">Save</button><button class="btn" id="dsc">Cancel</button></div></div>`;
  document.body.append(d);
  $("#dsc", d).onclick = () => d.remove();
  $("#dsok", d).onclick = async () => {
    const body = { id: Q._dataset, name: $("#dsn", d).value.trim(), description: $("#dsd", d).value.trim(), query: clean(Q),
      mode: d.querySelector('input[name="dsm"]:checked').value, refresh_snapshot: true };
    try { const ds = await api("/api/datasets", { method: "POST", body }); d.remove(); Q._dataset = ds.id; Q._name = ds.name; qSave(); location.hash = `#/datasets/${encodeURIComponent(ds.id)}`; }
    catch (e) { alertBar(e.message); }
  };
  $("#dsn", d).focus();
}

function dsCard(d) {
  return `<a class="card" href="#/datasets/${encodeURIComponent(d.id)}" style="color:inherit"><h2 style="margin:0 0 4px">${esc(d.name)}</h2>
    <div class="small muted">${d.mode === "snapshot" ? "fixed snapshot" : "growing"} · ${esc(d.unit)} · updated ${esc((d.updated || "").slice(0, 10))}</div>
    ${d.description ? `<div class="small">${esc(d.description)}</div>` : ""}<div class="small muted" style="margin-top:4px">${esc(d.describe)}</div></a>`;
}

async function viewDatasets() {
  const ds = await api("/api/datasets");
  $("#main").innerHTML = `<div class="row"><h1>Datasets</h1><span class="spacer"></span><a class="btn primary" href="#/query">New query</a></div>
    <p class="muted">A dataset is a saved query. <b>Growing</b> datasets re-run each time (cumulative as you finish and tag pages, across all the manuscripts chosen); <b>fixed</b> ones keep the rows from the day they were saved.</p>
    ${ds.length ? `<div class="grid">${ds.map(dsCard).join("")}</div>` : `<div class="empty">No datasets yet.</div>`}`;
}

async function viewDataset(id, gby) {
  const d = await api(`/api/datasets/${encodeURIComponent(id)}?limit=500${gby ? `&group_by=${encodeURIComponent(gby)}` : ""}`);
  $("#main").innerHTML = `<div class="row"><h1>${esc(d.name)}</h1><span class="badge">${d.mode === "snapshot" ? `fixed snapshot of ${esc((d.snapshot_t || "").replace("T", " "))}` : "growing"}</span><span class="spacer"></span>
      <a class="btn small" href="#/query/${encodeURIComponent(d.id)}">Edit query</a>
      ${d.mode === "snapshot" ? `<button class="btn small" id="refr">Refresh snapshot</button>` : ""}
      <button class="btn small" id="dxl">Export .xlsx</button><button class="btn small" id="dcsv">.csv</button><button class="btn small bad" id="ddel">Delete</button></div>
    ${d.description ? `<p>${esc(d.description)}</p>` : ""}<p class="muted small">${esc(d.describe)}${d.excluded && d.excluded.length ? ` · ${d.excluded.length} rows taken out by hand` : ""}</p>
    <div class="row"><span class="lab">Count by</span><select id="dgby">${GROUPBY.map(([k, t]) => `<option value="${k}" ${gby === k ? "selected" : ""}>${t}</option>`).join("")}</select></div>
    <div id="dres"></div>`;
  const box = $("#dres");
  box.innerHTML = resultsHtml(d, gby, { exclude: d.mode !== "snapshot" });
  wireResults(box, d, { dataset: true });
  box.querySelectorAll("[data-ex]").forEach((b) => b.onclick = async () => {
    await api("/api/datasets", { method: "POST", body: { id: d.id, excluded: [...(d.excluded || []), b.dataset.ex] } }); viewDataset(id, gby); });
  $("#dgby").onchange = (e) => viewDataset(id, e.target.value);
  $("#dxl").onclick = () => download(`/api/datasets/${encodeURIComponent(id)}/export?format=xlsx`);
  $("#dcsv").onclick = () => download(`/api/datasets/${encodeURIComponent(id)}/export?format=csv`);
  if ($("#refr")) $("#refr").onclick = async () => { await api("/api/datasets", { method: "POST", body: { id: d.id, refresh_snapshot: true } }); viewDataset(id, gby); };
  $("#ddel").onclick = async () => { if (!confirm(`Delete dataset “${d.name}”? (kept in conti_data/_datasets_deleted)`)) return; await api(`/api/datasets/${encodeURIComponent(id)}`, { method: "DELETE" }); location.hash = "#/datasets"; };
}

/* ------------------------------------------------------------------ names: one person, many spellings */
async function viewNames(type) {
  type = type || "person";
  const ns = await api(`/api/names?type=${encodeURIComponent(type)}`);
  $("#main").innerHTML = `<h1>Names</h1>
    <p class="muted">Every name tagged in all manuscripts. Tick names that are the same ${type === "person" ? "person" : "thing"} and merge them: the tags are not changed, the spellings are simply grouped (and can be separated again).</p>
    <div class="row" style="margin-bottom:10px"><div class="seg">${TYPES.map((t) => `<button data-nt="${t}" class="${t === type ? "on" : ""}">${TLABEL[t]}</button>`).join("")}</div>
      <input type="search" id="nq" placeholder="Filter"><span class="spacer"></span>
      <button class="btn small primary" id="mrg" disabled>Merge ticked…</button></div>
    <table><thead><tr><th></th><th>Name</th><th class="num">tags</th><th class="num">checked</th><th>Spellings / merged names</th><th></th></tr></thead><tbody id="nbody">
    ${ns.map((n, i) => `<tr data-name="${esc(n.name.toLowerCase())}"><td><input type="checkbox" data-n="${i}"></td><td><b>${esc(n.name)}</b></td><td class="num">${n.count}</td><td class="num">${n.approved}</td>
      <td class="small">${Object.keys(n.variants).filter((v) => v !== n.name).map((v) => `${esc(v)} <button class="btn small ghost" data-um="${esc(v)}" title="Separate again">↶</button>`).join(" · ")}</td>
      <td><a class="small" href="#/query" data-q="${i}">query →</a></td></tr>`).join("")}</tbody></table>`;
  document.querySelectorAll("[data-nt]").forEach((b) => b.onclick = () => (location.hash = `#/names/${b.dataset.nt}`));
  $("#nq").oninput = (e) => { const q = e.target.value.toLowerCase(); document.querySelectorAll("#nbody tr").forEach((tr) => tr.hidden = !tr.dataset.name.includes(q)); };
  const ticked = () => [...document.querySelectorAll("[data-n]:checked")].map((x) => ns[+x.dataset.n]);
  document.querySelectorAll("[data-n]").forEach((x) => x.onchange = () => { $("#mrg").disabled = ticked().length < 2; });
  $("#mrg").onclick = async () => {
    const t = ticked(); const into = prompt("Merge into which name? (type it as it should appear)", t.sort((a, b) => b.count - a.count)[0].name);
    if (!into) return;
    await api("/api/names/merge", { method: "POST", body: { type, names: t.map((n) => n.name), into } }); S.data = null; viewNames(type);
  };
  document.querySelectorAll("[data-um]").forEach((b) => b.onclick = async () => { await api("/api/names/merge", { method: "POST", body: { type, into: b.dataset.um, unmerge: true } }); S.data = null; viewNames(type); });
  document.querySelectorAll("[data-q]").forEach((a) => a.onclick = () => { Q = { ...QDEF(), manuscripts: S.colls.map((c) => c.id), conditions: [{ field: type, op: "is", value: ns[+a.dataset.q].name }] }; qSave(); });
}
