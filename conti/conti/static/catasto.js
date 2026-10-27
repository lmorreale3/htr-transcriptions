/* Catasto (#/catasto, #/catasto/<person>): people in the account books who may appear in the Florentine Catasto of 1427.
   Conti proposes households (same person, or a son / daughter / widow); Laura decides. Decisions: conti_data/_catasto.json */
const CAT = { data: null, filter: "candidates", q: "" };
const CAT_DEC = { same: "Same person", relative: "Relative", no: "Not this one" };
const fl = (x) => x == null ? "–" : `ƒ ${Number(x).toLocaleString("en-GB")}`;

async function viewCatasto(person) {
  $("#main").innerHTML = `<div class="empty">Comparing the people in your books with 10,000 Catasto households…</div>`;
  CAT.data = await api("/api/catasto");
  const d = CAT.data;
  if (!d.available) {
    $("#main").innerHTML = `<div class="empty err">The Catasto file was not found: ${esc(d.file)}</div>`; return;
  }
  const c = d.counts;
  $("#main").innerHTML = `<div class="row"><h1>Catasto 1427</h1><span class="spacer"></span>
      <a class="btn" href="/api/catasto/export" title="Every link you confirmed, with the household's gonfalone, trade, age and wealth">⬇ Confirmed links .xlsx</a></div>
    <p class="muted">People tagged in your account books who may appear in the Florentine <b>Catasto of 1427</b> (city of Florence; Brown University's
      Online Catasto, Herlihy &amp; Klapisch-Zuber). The Catasto names only the <b>head of each household</b>. Conti proposes households that have the
      same name and father's name (<b>same person</b>), or whose head's father — or a widow's late husband — has the person's name and family name
      (<b>relative</b>: a son, daughter or widow). The Catasto's age in 1427 is turned back to the years the person appears in your books, so a
      head who was a child then is marked. <b>Nothing counts until you decide.</b></p>
    <div class="row" style="margin:6px 0 12px">
      <span class="chip ${CAT.filter === "candidates" ? "on" : ""}" data-f="candidates">With possible matches <span class="n">${c.with_candidates}</span></span>
      <span class="chip ${CAT.filter === "decided" ? "on" : ""}" data-f="decided">Decided <span class="n">${c.same + c.relative}</span></span>
      <span class="chip ${CAT.filter === "all" ? "on" : ""}" data-f="all">All people <span class="n">${c.people}</span></span>
      <input id="cq" placeholder="Find a person…" value="${esc(CAT.q)}" style="width:200px">
      <span class="spacer"></span><span class="small muted">${c.same} same person · ${c.relative} relatives confirmed</span>
    </div>
    <div class="catgrid"><aside id="clist"></aside><section id="cone"></section></div>`;
  document.querySelectorAll("[data-f]").forEach((el) => el.onclick = () => { CAT.filter = el.dataset.f; viewCatasto(person); });
  $("#cq").oninput = () => { CAT.q = $("#cq").value; drawCatList(person); };
  drawCatList(person);
  const p = person ? d.people.find((x) => x.name === person) : null;
  if (p) drawCatPerson(p); else $("#cone").innerHTML = `<div class="empty">Pick a person on the left.</div>`;
}

function catShown() {
  const q = CAT.q.trim().toLowerCase();
  return CAT.data.people.filter((p) => {
    if (q && !p.name.toLowerCase().includes(q)) return false;
    if (CAT.filter === "candidates") return p.candidates.length;
    if (CAT.filter === "decided") return p.candidates.some((c) => c.decision === "same" || c.decision === "relative");
    return true;
  });
}

function drawCatList(sel) {
  const ps = catShown();
  $("#clist").innerHTML = ps.map((p) => {
    const best = p.candidates[0];
    const dec = p.candidates.find((c) => c.decision === "same" || c.decision === "relative");
    return `<a class="aitem ${p.name === sel ? "on" : ""}" href="#/catasto/${encodeURIComponent(p.name)}">
      <div>${esc(p.name)} ${dec ? `<span class="badge credit">${esc(CAT_DEC[dec.decision])}</span>` : ""}</div>
      <div class="small muted">${p.mentions} mention${p.mentions === 1 ? "" : "s"}${p.occupations.length ? " · " + esc(p.occupations.join(", ")) : ""}
        · ${p.candidates.length ? `${p.candidates.length} possible${best ? ` (best: ${esc(best.strength)})` : ""}` : esc(p.why_none || "none")}</div></a>`;
  }).join("") || `<div class="muted small">Nobody here.</div>`;
}

function drawCatPerson(p) {
  const yrs = p.years.length ? `in entries dated ${p.years.join(", ")}` : (p.year_used ? `undated entries; book's middle year ${p.year_used} used` : "no dates");
  const parsed = p.parsed || {};
  $("#cone").innerHTML = `<div class="card">
      <div class="row"><h2 style="margin:0">${esc(p.name)}</h2><span class="spacer"></span>
        <span class="small muted">${Object.entries(p.manuscripts).map(([m, n]) => `${esc(m)} (${n})`).join(", ")} · ${esc(yrs)}</span></div>
      <div class="small muted" style="margin-top:4px">Looked up as: <b>${esc(parsed.first || "?")}</b>${parsed.father ? ` di <b>${esc(parsed.father)}</b>` : ""}${
        parsed.grandfather ? ` di ${esc(parsed.grandfather)} (grandfather: not in the Catasto)` : ""}${parsed.family && parsed.family.length ? ` · family <b>${esc(parsed.family[0])}</b>` : ""}${
        parsed.origin ? ` · from ${esc(parsed.origin)}` : ""}${p.occupations.length ? ` · occupation in the books: <b>${esc(p.occupations.join(", "))}</b>` : ""}</div>
      <details style="margin-top:8px"><summary class="small">Where the books name ${esc(p.name)} (${p.mentions})</summary>
        ${p.lines.map((l) => `<div class="small" style="margin:4px 0"><a href="${LEGGIO()}/#/p/${encodeURIComponent(l.manuscript)}/${encodeURIComponent(l.page)}/${encodeURIComponent(l.line_ids.split(",")[0])}" target="leggio">${esc(l.manuscript)} ${esc(l.folio || l.page)}, line ${l.line}</a>${l.year ? ` (${l.year})` : ""}: ${esc(l.text)}${l.translation ? `<div class="muted">${esc(l.translation)}</div>` : ""}</div>`).join("")}
      </details></div>
    <h3>${p.candidates.length ? "Possible households" : "No household found"}</h3>
    ${p.candidates.length ? "" : `<p class="muted">${esc(p.why_none || "")}. You can search the Catasto by hand below.</p>`}
    ${p.candidates.map((c) => catCard(p, c)).join("")}
    ${p.more ? `<p class="small muted">${p.more} weaker possibilities not shown.</p>` : ""}
    <div class="card" style="margin-top:14px"><b>Search the Catasto by hand</b>
      <div class="row" style="margin-top:6px"><input id="chs" placeholder="e.g. Bartolo Nese, or a family name" style="width:260px">
        <button class="btn" id="chgo">Search</button></div><div id="chres"></div></div>`;
  document.querySelectorAll("[data-dec]").forEach((b) => b.onclick = () => catDecide(p, b.dataset.id, b.dataset.dec));
  const go = async () => {
    const r = await api(`/api/catasto/search?q=${encodeURIComponent($("#chs").value)}`);
    $("#chres").innerHTML = r.length ? `<table class="small" style="margin-top:8px"><tr><th>Head of household</th><th>Gonfalone</th><th>Trade</th><th>Age</th><th>Total</th><th></th></tr>${
      r.map((h) => `<tr><td>${esc(h.written)}</td><td>${esc(h.gonfalone)}</td><td>${esc(h.trade)}</td><td>${h.age ?? "–"}</td><td>${fl(h.total)}</td>
        <td><button class="btn small" data-dec="same" data-id="${esc(h.stg_id)}">Same person</button> <button class="btn small" data-dec="relative" data-id="${esc(h.stg_id)}">Relative</button></td></tr>`).join("")}</table>`
      : `<p class="small muted">Nothing found.</p>`;
    $("#chres").querySelectorAll("[data-dec]").forEach((b) => b.onclick = () => catDecide(p, b.dataset.id, b.dataset.dec));
  };
  $("#chgo").onclick = go; $("#chs").onkeydown = (e) => { if (e.key === "Enter") go(); };
}

function catCard(p, c) {
  const h = c.household;
  const kind = c.kind === "same" ? "Same person?" : c.kind === "relative" ? `His or her ${c.relation}?` : "Linked by hand";
  const btn = (k, t) => `<button class="btn small ${c.decision === k ? "primary" : ""}" data-dec="${c.decision === k ? "clear" : k}" data-id="${esc(h.stg_id)}">${t}</button>`;
  return `<div class="card catc ${c.decision === "no" ? "dim" : ""}" style="margin-top:10px">
    <div class="row"><b>${esc(h.written)}</b><span class="badge">${esc(kind)}</span><span class="badge cs-${esc(c.strength)}">${esc(c.strength)}</span>
      <span class="spacer"></span>${btn("same", "Same person")}${btn("relative", "Relative")}${btn("no", "Not this one")}</div>
    <div class="small" style="margin-top:6px">${esc(h.gonfalone || "–")} · ${esc(h.trade || "no trade given")} · ${h.age != null ? `age ${h.age}` : esc(h.age_note || "age not given")}
      · ${esc(h.sex || "")}${h.marital ? ", " + esc(h.marital.toLowerCase()) : ""} · ${h.bocche ?? "?"} bocche${h.heir ? " · registered as heir" : ""}</div>
    <div class="small" style="margin-top:2px">Total ${fl(h.total)} (real estate ${fl(h.real_estate)}, Monte ${fl(h.public)}, other ${fl(h.private)}) · deductions ${fl(h.deductions)} · taxable ${fl(h.taxable)}
      · <span class="muted">ASF Catasto, Campioni ${esc(h.volume)}, c. ${esc(h.page)} · ${esc(h.series)}${h.declaration ? " · " + esc(h.declaration) : ""}</span></div>
    <div class="small" style="margin-top:6px">${c.reasons.map((r) => `<span class="ok">✓</span> ${esc(r)}`).join(" &nbsp; ")}</div>
    ${c.notes.length ? `<div class="small" style="margin-top:2px">${c.notes.map((r) => `<span class="warn">!</span> ${esc(r)}`).join(" &nbsp; ")}</div>` : ""}
  </div>`;
}

async function catDecide(p, id, dec) {
  await api("/api/catasto/decide", { method: "POST", body: { person: p.name, stg_id: id, decision: dec } });
  await viewCatasto(p.name);
}
