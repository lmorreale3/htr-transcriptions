/* Ask (#/ask, #/ask/<id>): plain-language questions answered with evidence. Conti computes; Claude plans and words. */
const ASK = { list: null, rec: null, timer: null, claude: null };
const ASK_BUSY = ["planning", "running", "writing"];
const ASK_STATUS = { waiting: "waiting for a chat", planning: "Claude is planning", running: "Conti is counting", writing: "Claude is writing",
  done: "answered", error: "stopped", "answered-without-text": "results ready, no written answer yet" };
const LEGGIO = () => "http://127.0.0.1:8770";
const fmt = (x, d = 2) => x == null ? "–" : (Math.round(x * 10 ** d) / 10 ** d).toLocaleString("en-GB");

async function viewAsk(id) {
  clearInterval(ASK.timer);
  ASK.list = await api("/api/ask");
  $("#main").innerHTML = `<div class="row"><h1>Ask</h1><span class="spacer"></span><span class="small muted" id="cst"></span></div>
    <p class="muted">Ask in ordinary language. Claude turns the question into a plan; <b>Conti</b> does every count and sum and shows the rows behind them,
      how many rest on sums and tags you have checked, and what the data cannot say yet.</p>
    <div class="askgrid">
      <aside>
        <div class="card">
          <textarea id="aq" rows="5" placeholder="e.g. Which occupation consistently borrowed the largest sums?"></textarea>
          <div class="row" style="margin-top:8px">
            <button class="btn primary" id="ago" title="Runs Claude Code on this Mac (your Claude account, no API key)">✦ Ask Claude</button>
            <button class="btn" id="achat" title="Keep the question for a Cowork chat: ask Claude there to answer the Conti questions waiting">Save for a chat</button>
          </div>
          <div class="small muted" style="margin-top:8px">Examples:</div>
          <div class="aex">${ASK.list.examples.map((e) => `<a href="#" class="small" data-ex="${esc(e)}">${esc(e)}</a>`).join("")}</div>
        </div>
        <h2>Questions</h2>
        <div class="alist">${ASK.list.questions.map((q) => `<a class="aitem ${q.id === id ? "on" : ""}" href="#/ask/${encodeURIComponent(q.id)}">
            <div>${esc(q.title || q.question)}</div>
            <div class="small muted"><span class="ast ast-${esc(q.status)}">${esc(ASK_STATUS[q.status] || q.status)}</span> · ${esc((q.t || "").replace("T", " ").slice(0, 16))}</div></a>`).join("")
          || `<div class="muted small">No questions yet.</div>`}</div>
      </aside>
      <section id="ares">${id ? "" : `<div class="empty">Ask a question, or pick one on the left.</div>`}</section>
    </div>`;
  document.querySelectorAll("[data-ex]").forEach((a) => a.onclick = (e) => { e.preventDefault(); $("#aq").value = a.dataset.ex; $("#aq").focus(); });
  const submit = async (mode) => {
    const q = $("#aq").value.trim(); if (!q) return;
    const rec = await api("/api/ask", { method: "POST", body: { question: q, mode } });
    location.hash = `#/ask/${encodeURIComponent(rec.id)}`;
  };
  $("#ago").onclick = () => submit("claude"); $("#achat").onclick = () => submit("chat");
  $("#aq").onkeydown = (e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit("claude"); };
  if (!ASK.claude) api("/api/ask/claude").then((c) => { ASK.claude = c; claudeBadge(); }).catch(() => {}); else claudeBadge();
  if (id) await showAsk(id);
}

function claudeBadge() {
  const c = ASK.claude, el = $("#cst"); if (!el || !c) return;
  el.innerHTML = c.found ? `Claude Code: ${esc(c.version || "found")}` : `<span class="err">Claude Code not found on this Mac — use “Save for a chat”</span>`;
}

async function showAsk(id) {
  const rec = await api(`/api/ask/${encodeURIComponent(id)}`);
  ASK.rec = rec;
  drawAsk(rec);
  clearInterval(ASK.timer);
  if (ASK_BUSY.includes(rec.status)) {
    ASK.timer = setInterval(async () => {
      if (!location.hash.startsWith("#/ask/" + encodeURIComponent(id))) { clearInterval(ASK.timer); return; }
      const r = await api(`/api/ask/${encodeURIComponent(id)}`);
      if (r.status !== ASK.rec.status || (r.log || []).length !== (ASK.rec.log || []).length) {
        ASK.rec = r; drawAsk(r);
        if (!ASK_BUSY.includes(r.status)) { clearInterval(ASK.timer); viewAsk(id); }
      }
    }, 2500);
  }
}

function txIndex(res) {
  const m = {};
  for (const s of Object.values(res.steps || {})) if (s.type === "transactions") for (const t of s.rows) m[t.id] = t;
  return m;
}

function drawAsk(rec) {
  const el = $("#ares"); if (!el) return;
  const res = rec.result, ans = rec.answer;
  const busy = ASK_BUSY.includes(rec.status);
  let h = `<div class="card">
    <div class="row"><span class="ast ast-${esc(rec.status)}">${esc(ASK_STATUS[rec.status] || rec.status)}</span>${busy ? `<span class="spin"></span>` : ""}<span class="spacer"></span>
      ${res ? `<a class="btn small" href="/api/ask/${encodeURIComponent(rec.id)}/export">⬇ Evidence .xlsx</a>
      <button class="btn small" id="arerun" title="Run the same plan again on today's transcriptions and tags (no Claude)">↻ Re-run on today's data</button>` : ""}
      ${!busy ? `<button class="btn small" id="aagain">✦ ${rec.plan ? "Ask Claude again" : "Ask Claude"}</button>` : ""}
      ${!busy && rec.status !== "waiting" ? `<button class="btn small" id="atochat">Save for a chat</button>` : ""}
      <button class="btn small ghost bad" id="adel" title="Delete this question">✕</button></div>
    <h2 style="margin-top:10px">${esc(rec.question)}</h2>`;
  if (rec.status === "waiting") h += `<p class="muted">Saved for a chat. In Cowork, ask Claude: <i>“Answer the Conti questions waiting in the Ask tab.”</i> The answer appears here.</p>`;
  if (rec.error) h += `<p class="err">${esc(rec.error)}</p>`;
  if (busy || rec.status === "error") h += `<pre class="alog small">${esc((rec.log || []).slice(-8).join("\n"))}</pre>`;
  if (ans) {
    const stale = res && ans.written_on_data_of && ans.written_on_data_of !== res.t;
    h += `<div class="ahead">${esc(ans.headline || "")}</div>
      ${stale ? `<p class="small chgc">The numbers below were re-run on ${esc(res.t.replace("T", " "))}; the written answer is from ${esc(ans.written_on_data_of.replace("T", " "))}. Ask Claude again to re-word it.</p>` : ""}
      <div class="aprose">${(ans.answer || "").split(/\n\s*\n/).map((p) => `<p>${linkSteps(esc(p))}</p>`).join("")}</div>`;
    if ((ans.claims || []).length) h += `<h3>Claims and their evidence</h3><ul class="aclaims">${ans.claims.map((c) =>
      `<li><span class="str str-${esc(c.strength || "")}">${esc(c.strength || "")}</span> ${esc(c.text)} <span class="small muted">— ${linkSteps(esc(c.evidence || ""))}</span></li>`).join("")}</ul>`;
  } else if (res) {
    h += `<p class="muted">Conti's results are below; there is no written answer yet.</p>`;
  }
  if (rec.understood || rec.limits) h += `<div class="small" style="margin-top:8px">${rec.understood ? `<b>How the question was read:</b> ${esc(rec.understood)}` : ""}
      ${rec.limits ? `<br><b>What the data cannot say yet:</b> ${esc(rec.limits)}` : ""}</div>`;
  h += `</div>`;
  if (res) {
    h += coverageCard(res, ans);
    for (const [k, s] of Object.entries(res.steps)) h += `<div class="card astep" id="step-${esc(k)}"><div class="row"><h3 style="margin:0">${esc(s.title || k)}</h3>
      <span class="small muted">[${esc(k)}] · ${esc(s.op)}</span><span class="spacer"></span>${stepButtons(rec, k, s)}</div><div class="sbody" data-step="${esc(k)}"></div></div>`;
    if ((ans?.followups || []).length) h += `<div class="card afollow"><h3 style="margin-top:0">To firm this up</h3><ul>${ans.followups.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      <div class="small muted">Click a follow-up to put it in the question box.</div></div>`;
    h += `<details class="card"><summary class="small">The plan Conti ran (JSON)</summary><pre class="small">${esc(JSON.stringify(rec.plan, null, 1))}</pre></details>`;
  }
  el.innerHTML = h;
  if (res) {
    const tx = txIndex(res);
    for (const [k, s] of Object.entries(res.steps)) {
      const b = el.querySelector(`.sbody[data-step="${CSS.escape(k)}"]`);
      ({ transactions: drawTx, table: drawAgg, network: drawDebtNet, query: drawQStep }[s.type] || (() => {}))(b, s, tx, rec);
    }
    el.querySelectorAll(".afollow li").forEach((li) => { li.style.cursor = "pointer"; li.onclick = () => { $("#aq").value = li.textContent; $("#aq").focus(); }; });
  }
  const on = (sel, f) => { const b = $(sel); if (b) b.onclick = f; };
  on("#arerun", async () => { $("#arerun").disabled = true; await api(`/api/ask/${encodeURIComponent(rec.id)}/rerun`, { method: "POST" }); showAsk(rec.id); });
  on("#aagain", async () => { await api(`/api/ask/${encodeURIComponent(rec.id)}/start`, { method: "POST" }); showAsk(rec.id); });
  on("#atochat", async () => { await api(`/api/ask/${encodeURIComponent(rec.id)}/chat`, { method: "POST" }); viewAsk(rec.id); });
  on("#adel", async () => { await api(`/api/ask/${encodeURIComponent(rec.id)}`, { method: "DELETE" }); location.hash = "#/ask"; });
  el.querySelectorAll("[data-ds]").forEach((b) => b.onclick = async () => {
    const d = await api(`/api/ask/${encodeURIComponent(rec.id)}/dataset`, { method: "POST", body: { step: b.dataset.ds } });
    alertBar(`Saved as dataset “${d.name}” (grows as pages are finished).`, true);
  });
}

function stepLink(k, label) { return `<a href="#" onclick="document.getElementById('step-${k}').scrollIntoView({behavior:'smooth'});return false">${label}</a>`; }
function linkSteps(html) {
  const steps = Object.keys(ASK.rec?.result?.steps || {});
  return html.replace(/\[([A-Za-z0-9_\-]+)\]/g, (m, k) => steps.includes(k) ? stepLink(k, `[${k}]`) : m)
    .replace(/(^|[\s(])([A-Za-z0-9_\-]+):/g, (m, pre, k) => steps.includes(k) ? `${pre}${stepLink(k, k)}:` : m);
}

function stepButtons(rec, k, s) {
  if (s.type === "network") return `<a class="btn small" href="/api/ask/${encodeURIComponent(rec.id)}/gephi?step=${encodeURIComponent(k)}">Export for Gephi (.zip)</a>`;
  if (s.type === "query") return `<button class="btn small" data-ds="${esc(k)}">Save as dataset</button>`;
  return "";
}

function coverageCard(res, ans) {
  const ms = res.coverage.manuscripts.filter((m) => m.pages_included);
  const cav = [...res.caveats, ...((ans && ans.caveats) || [])];
  return `<div class="card"><h3 style="margin-top:0">What this rests on</h3>
    <table class="gtable small"><thead><tr><th>Manuscript</th><th class="num">pages included</th><th class="num">pages tagged</th><th class="num">tags you approved</th><th class="num">sums you checked</th><th>creditor if none written</th></tr></thead><tbody>
    ${ms.map((m) => `<tr><td>${esc(m.id)}</td><td class="num">${m.pages_included} / ${m.pages_total}</td><td class="num">${m.pages_tagged}</td>
      <td class="num">${m.tags_approved} / ${m.tags}</td><td class="num">${m.sums_checked} / ${m.sums}</td><td>${esc(m.account_holder || "—")}</td></tr>`).join("")}</tbody></table>
    <ul class="small acav">${cav.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></div>`;
}

/* ---------------- transactions: the evidence rows */
const PAGE = (p) => String(p).split("_")[0];
const leggioLink = (ms, page, ids, label) => `<a href="${LEGGIO()}/#/p/${encodeURIComponent(ms)}/${encodeURIComponent(page)}/${encodeURIComponent(String(ids || "").split(",")[0])}" target="leggio" title="Open in Leggio">${label}</a>`;
function txRow(t) {
  const occ = [...new Set(t.debtors.flatMap((d) => d.occupations))].join(", ");
  return `<tr data-tx="${esc(t.id)}"><td class="nowrap">${leggioLink(t.manuscript, t.page, t.line_ids, `${esc(PAGE(t.page))} l.${esc(t.lines.join(","))}`)}</td>
    <td>${esc(t.kind)}</td><td>${esc(t.debtors.map((d) => d.name).join("; ") || "—")}</td><td>${esc(occ)}</td>
    <td>${t.creditor.basis === "tagged" ? esc(t.creditor.name) : `<i class="muted" title="${esc(t.creditor.basis)}">${esc(t.creditor.name)}</i>`}</td>
    <td class="num">${fmt(t.florins)}</td><td class="num">${fmt(t.lire)}</td>
    <td class="nowrap">${esc(t.display)} ${t.sum_checked ? `<span class="ok" title="you checked this sum">✓</span>` : t.sum_problems ? `<span class="chgc" title="the rules flagged this sum">⚠</span>` : ""}</td>
    <td class="nowrap">${esc(t.date || "")}</td><td><button class="btn small ghost" data-img="${esc(t.id)}" title="Show the line">🖼</button></td></tr>`;
}
function txTable(rows, limit = 40) {
  return `<table class="small atx"><thead><tr><th>Page · lines</th><th>Kind</th><th>Debtor(s)</th><th>Occupation</th><th>Creditor</th><th class="num">ƒ</th><th class="num">lire</th><th>Sum read</th><th>Date</th><th></th></tr></thead>
    <tbody>${rows.slice(0, limit).map(txRow).join("")}</tbody></table>${rows.length > limit ? `<div class="small muted">${limit} of ${rows.length} shown; all are in the .xlsx.</div>` : ""}`;
}
function wireTx(el, tx) {
  el.querySelectorAll("[data-img]").forEach((b) => b.onclick = () => {
    const t = tx[b.dataset.img], tr = b.closest("tr");
    if (tr.nextElementSibling?.classList.contains("imgrow")) { tr.nextElementSibling.remove(); return; }
    const r = document.createElement("tr"); r.className = "imgrow";
    r.innerHTML = `<td colspan="10"><img class="crop" src="/api/crop/${encodeURIComponent(t.manuscript)}/${encodeURIComponent(t.page)}?ids=${encodeURIComponent(t.line_ids)}" alt="">
      <div class="ms">${esc(t.text)}</div>${t.translation ? `<div class="small muted">${esc(t.translation)}</div>` : ""}</td>`;
    tr.after(r);
  });
}
function drawTx(el, s, tx) {
  const c = s.counts;
  el.innerHTML = `<div class="row small abadges">
      <span><b>${s.count}</b> rows</span><span>${c.with_debtor} with a tagged debtor</span><span>${c.with_occupation} with an occupation</span>
      <span>${c.with_sum} with a sum</span><span class="${c.sum_checked ? "" : "chgc"}">${c.sum_checked} sums checked</span><span>${c.sum_problems} sums flagged ⚠</span>
      <span class="${c.tags_checked ? "" : "chgc"}">${c.tags_checked} rows on approved tags</span><span>${c.creditor_tagged} creditors written · ${c.creditor_assumed} assumed</span><span>${c.dated} dated</span></div>
    <details><summary class="small">Show the rows</summary>${txTable(s.rows)}</details>`;
  wireTx(el, tx);
}

/* ---------------- aggregate: chart, table, consistency */
const METRIC_LABEL = { median: "median sum", total: "total", mean: "mean sum", max: "largest sum", count: "number of debts" };
function drawAgg(el, s, tx) {
  const curs = s.currencies, rb = s.rank_by, c0 = curs[0];
  const metric = (r, c) => rb === "count" ? r.transactions : r[`${c}_${rb}`];
  const rows = s.rows.filter((r) => metric(r, c0) != null);
  const max = Math.max(1, ...rows.map((r) => metric(r, c0) || 0));
  const unit = rb === "count" ? "" : (c0 === "florins" ? "ƒ " : "lire ");
  let h = `<div class="small muted">Ranked by ${esc(METRIC_LABEL[rb] || rb)}${rb === "count" ? "" : ` in ${c0}`} · groups with at least ${s.min_n} ${rb === "count" ? "row" : "sum"}${s.min_n > 1 ? "s" : ""} · joint debts ${s.split === "equal" ? "shared equally among debtors" : "counted in full for each debtor"} · ${s.groups_total} groups · darker bar = includes a sum you checked</div>
    <div class="bars">${rows.map((r) => `<div class="bar" data-g="${esc(r.value)}" title="click for the rows"><span class="bl">${esc(r.value)}</span>
      <span class="bt"><i style="width:${(100 * (metric(r, c0) || 0) / max).toFixed(1)}%" class="${r.sums_checked ? "chk" : ""}"></i></span>
      <span class="bv">${unit}${fmt(metric(r, c0))} <span class="muted">· n=${rb === "count" ? r.transactions : r[`${c0}_n`]}</span></span></div>`).join("")}</div>`;
  h += `<details><summary class="small">Table</summary><div class="hscroll"><table class="gtable small"><thead><tr><th>${esc(s.by)}</th><th class="num">rows</th><th class="num">people</th>
    ${curs.map((c) => `<th class="num">${c} n</th><th class="num">median</th><th class="num">mean</th><th class="num">total</th><th class="num">max</th>`).join("")}<th class="num">checked</th><th class="num">⚠</th></tr></thead><tbody>
    ${s.rows.map((r) => `<tr data-g="${esc(r.value)}"><td>${esc(r.value)}</td><td class="num">${r.transactions}</td><td class="num" title="${esc(r.people_names.join("; "))}">${r.people}</td>
      ${curs.map((c) => `<td class="num">${r[`${c}_n`]}</td><td class="num">${fmt(r[`${c}_median`])}</td><td class="num">${fmt(r[`${c}_mean`])}</td><td class="num">${fmt(r[`${c}_total`])}</td><td class="num">${fmt(r[`${c}_max`])}</td>`).join("")}
      <td class="num">${r.sums_checked}</td><td class="num">${r.sums_flagged}</td></tr>`).join("")}</tbody></table></div></details>`;
  if (s.consistency) {
    const per = s.periods.filter((p) => !p.startsWith("("));
    const cell = {}; s.matrix.forEach((m) => cell[`${m.value}|${m.period}`] = m);
    h += `<h4>Does the ranking hold ${s.over === "year" ? "year by year" : `${s.over} by ${s.over}`}?</h4>
      ${per.length < 2 ? `<p class="small chgc">Only ${per.length} ${s.over === "year" ? "dated year" : s.over}${per.length === 1 ? "" : "s"} with data, so “consistently” cannot be tested yet.</p>` : ""}
      <div class="hscroll"><table class="gtable small cons"><thead><tr><th>${esc(s.by)}</th><th class="num">ranked 1st</th><th class="num">top 3</th><th class="num">present</th><th class="num">mean rank</th>
      ${s.periods.map((p) => `<th class="num">${esc(p)}</th>`).join("")}</tr></thead><tbody>
      ${s.consistency.map((c) => `<tr><td>${esc(c.value)}</td><td class="num">${c.periods_first}</td><td class="num">${c.periods_top3}</td><td class="num">${c.periods_present} / ${c.periods_total}</td><td class="num">${fmt(c.mean_rank)}</td>
        ${s.periods.map((p) => { const m = cell[`${c.value}|${p}`]; return m ? `<td class="num rk rk${Math.min(m.rank, 4)}" title="${esc(METRIC_LABEL[rb] || rb)} ${fmt(m.metric)} · ${m.transactions} rows · rank ${m.rank} of ${m.of}">${m.rank}</td>` : `<td class="num muted">·</td>`; }).join("")}</tr>`).join("")}
      </tbody></table></div>`;
  }
  h += `<div class="aev"></div>`;
  el.innerHTML = h;
  el.querySelectorAll("[data-g]").forEach((b) => b.onclick = () => {
    const r = s.rows.find((x) => String(x.value) === b.dataset.g); const box = el.querySelector(".aev");
    box.innerHTML = `<h4>${esc(r.value)}: the ${r.ids.length} rows behind it</h4>${txTable(r.ids.map((i) => tx[i]).filter(Boolean), 200)}`;
    wireTx(box, tx); box.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
}

/* ---------------- network: who owed whom (directed) */
function drawDebtNet(el, s, tx) {
  const sm = s.summary;
  el.innerHTML = `<div class="small muted">${sm.shown} of ${sm.people_total} parties shown (top ${s.top} by ${esc(s.rank_by === "count" ? "number of debts and payments" : s.rank_by)}, plus everyone they owed or who owed them) ·
      ${sm.edges} links · ${sm.lenders} creditor${sm.lenders === 1 ? "" : "s"} · ${sm.edges_tagged} links with the creditor written, ${sm.edges_assumed} assumed (dashed).
      Arrows point from debtor to creditor; node size = number of debts; colour = owes / is owed / both.</div>
    ${sm.lenders <= 1 ? `<p class="small chgc">Every debt here runs to one creditor, so the network is a star: it shows who owed the estate, not lending between people. Tag creditors (role “creditor”) to see more.</p>` : ""}
    <div class="netwrap"><div class="netbox card"><svg class="dnet"></svg></div><aside class="netside card"><div class="muted small">Click a node for its debts and the rows behind them. Drag to move, scroll to zoom.</div></aside></div>
    <details><summary class="small">Nodes table</summary><div class="hscroll"><table class="gtable small"><thead><tr><th>#</th><th>Party</th><th>Role</th><th>Occupations</th><th class="num">debts owed</th><th class="num">ƒ owed</th><th class="num">lire owed</th><th class="num">debts owed to</th><th class="num">ƒ owed to</th><th class="num">lire owed to</th></tr></thead><tbody>
    ${s.nodes.map((n) => `<tr><td class="num">${n.rank}</td><td>${esc(n.label)}${n.assumed ? ` <i class="muted">(assumed)</i>` : ""}</td><td>${esc(n.role)}</td><td>${esc(n.occupations.join(", "))}</td>
      <td class="num">${n.owed_n}</td><td class="num">${fmt(n.owed_florins)}</td><td class="num">${fmt(n.owed_lire)}</td><td class="num">${n.owed_to_n}</td><td class="num">${fmt(n.owed_to_florins)}</td><td class="num">${fmt(n.owed_to_lire)}</td></tr>`).join("")}</tbody></table></div></details>`;
  const svg = d3.select(el.querySelector("svg.dnet")); const W = el.querySelector(".netbox").clientWidth || 800, H = 560;
  svg.attr("viewBox", [0, 0, W, H]).attr("height", H);
  const nodes = s.nodes.map((n) => ({ ...n })), links = s.edges.map((e) => ({ ...e }));
  const size = (n) => 5 + 3 * Math.sqrt(n.owed_n + n.owed_to_n);
  svg.append("defs").append("marker").attr("id", "arr").attr("viewBox", "0 -4 8 8").attr("refX", 8).attr("markerWidth", 7).attr("markerHeight", 7).attr("orient", "auto")
    .append("path").attr("d", "M0,-4L8,0L0,4").attr("class", "arrowhead");
  const g = svg.append("g");
  svg.call(d3.zoom().scaleExtent([0.2, 5]).on("zoom", (e) => g.attr("transform", e.transform)));
  const link = g.append("g").selectAll("line").data(links).join("line").attr("class", (d) => "dlink" + (d.basis.startsWith("assumed") ? " assumed" : ""))
    .attr("stroke-width", (d) => Math.min(8, 1 + Math.sqrt(d.n))).attr("marker-end", "url(#arr)");
  const node = g.append("g").selectAll("g").data(nodes).join("g").attr("class", (d) => "dnode r-" + d.role.replace(/[^a-z]/g, "")).style("cursor", "pointer");
  node.append("circle").attr("r", size);
  node.append("text").attr("dx", (d) => size(d) + 3).attr("dy", 4).text((d) => d.top && (d.rank <= 25 || d.owed_to_n) ? d.label : "");
  node.append("title").text((d) => `${d.label} — ${d.role}${d.occupations.length ? " · " + d.occupations.join(", ") : ""}`);
  const sim = d3.forceSimulation(nodes).force("link", d3.forceLink(links).id((d) => d.id).distance(90))
    .force("charge", d3.forceManyBody().strength(-160)).force("center", d3.forceCenter(W / 2, H / 2)).force("collide", d3.forceCollide((d) => size(d) + 4));
  node.call(d3.drag().on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; }).on("end", (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));
  sim.on("tick", () => {
    link.each(function (d) {
      const dx = d.target.x - d.source.x, dy = d.target.y - d.source.y, L = Math.hypot(dx, dy) || 1, r = size(d.target) + 2;
      d3.select(this).attr("x1", d.source.x).attr("y1", d.source.y).attr("x2", d.target.x - dx * r / L).attr("y2", d.target.y - dy * r / L);
    });
    node.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });
  node.on("click", (e, d) => {
    const side = el.querySelector(".netside");
    const mine = s.edges.filter((x) => x.source === d.id || x.target === d.id);
    const ids = mine.flatMap((x) => x.ids);
    side.innerHTML = `<b>${esc(d.label)}</b> <span class="small muted">${esc(d.role)}${d.assumed ? " (assumed account holder)" : ""}</span>
      ${d.occupations.length ? `<div class="small">${esc(d.occupations.join(", "))}</div>` : ""}
      <div class="small" style="margin:6px 0">Owed: ${d.owed_n} · ƒ ${fmt(d.owed_florins)} · lire ${fmt(d.owed_lire)}<br>Owed to: ${d.owed_to_n} · ƒ ${fmt(d.owed_to_florins)} · lire ${fmt(d.owed_to_lire)}</div>
      ${mine.slice(0, 40).map((x) => `<div class="small">${esc(x.source)} → ${esc(x.target)}: ${x.n} · ƒ ${fmt(x.florins)} · lire ${fmt(x.lire)}</div>`).join("")}
      <div class="small muted" style="margin-top:8px">${ids.length} rows${ids.length > 30 ? " (first 30)" : ""}</div>
      ${ids.slice(0, 30).map((i) => tx[i]).filter(Boolean).map((t) => `<div class="small">${leggioLink(t.manuscript, t.page, t.line_ids, `${esc(PAGE(t.page))} l.${esc(t.lines.join(","))}`)} ${esc(t.display)} <span class="ms">${esc(t.text.slice(0, 90))}</span></div>`).join("")}`;
  });
}

/* ---------------- query steps */
function drawQStep(el, s) {
  let h = `<div class="small muted">${esc(s.describe)} · <b>${s.count}</b> ${esc(s.unit)}</div>`;
  if (s.groups) h += `<table class="gtable small"><thead><tr><th>${esc(s.group_by)}</th><th class="num">rows</th><th>first date</th><th>last date</th></tr></thead><tbody>
    ${s.groups.slice(0, 40).map((g) => `<tr><td>${esc(g.value)}</td><td class="num">${g.rows}</td><td>${esc(g.first || "")}</td><td>${esc(g.last || "")}</td></tr>`).join("")}</tbody></table>`;
  h += `<details><summary class="small">Rows</summary><table class="small"><thead><tr><th>Page · line</th><th>Text</th></tr></thead><tbody>
    ${s.rows.slice(0, 60).map((r) => `<tr><td class="nowrap">${leggioLink(r.manuscript, r.page, r.line_ids, `${esc(PAGE(r.page))} l.${esc(r.line)}`)}</td>
      <td class="ms">${esc(r.text || r.name || "")}</td></tr>`).join("")}</tbody></table></details>`;
  el.innerHTML = h;
}
