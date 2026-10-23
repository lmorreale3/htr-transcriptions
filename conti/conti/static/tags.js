/* Tag review (people, places, occupations, institutions, goods) for one manuscript: #/m/<cid>/tags/<page> */
const TCOL = { person: "var(--t-person)", place: "var(--t-place)", occupation: "var(--t-occupation)", institution: "var(--t-institution)", goods: "var(--t-goods)" };
const ROLES = ["debtor", "creditor", "payer", "recipient", "agent", "heir", "tenant", "owner", "buyer", "seller", "guarantor", "testator", "beneficiary", "officer", "neighbour", "mentioned"];
const ATTRS = {
  person: [["title", ["", "ser", "monna", "maestro", "frate", "prete", "messer", "don"]], ["role", ["", ...ROLES]], ["relation", null], ["gender", ["", "m", "f"]]],
  place: [["kind", ["", "city", "town", "village", "parish", "street", "district", "valley", "church", "house", "farm", "property", "other"]], ["relation", ["", "origin", "residence", "location"]], ["of", null]],
  occupation: [["of", null]],
  institution: [["kind", ["", "church", "chapter", "confraternity", "hospital", "commune", "public debt", "tax office", "guild", "other"]]],
  goods: [["quantity", null], ["unit", null]],
};
const T = { cid: null, page: null, data: null, open: null, names: {} };

/* text with tag spans highlighted (longest spans first, no overlaps) */
function highlight(text, tags) {
  const marks = [];
  [...(tags || [])].filter((t) => t.span && t.status !== "rejected").sort((a, b) => b.span.length - a.span.length).forEach((t) => {
    let from = 0, i;
    while ((i = text.indexOf(t.span, from)) >= 0) {
      if (!marks.some((m) => i < m.e && i + t.span.length > m.s)) { marks.push({ s: i, e: i + t.span.length, t }); break; }
      from = i + 1;
    }
  });
  marks.sort((a, b) => a.s - b.s);
  let out = "", p = 0;
  for (const m of marks) {
    out += esc(text.slice(p, m.s)) + `<mark class="tg ${m.t.type} ${m.t.status}" data-id="${m.t.id || ""}" title="${esc(TLABEL[m.t.type])}: ${esc(m.t.canon || m.t.name)}">${esc(text.slice(m.s, m.e))}</mark>`;
    p = m.e;
  }
  return out + esc(text.slice(p));
}
function chip(t, extra = "") {
  const a = t.attrs || {};
  const sub = [a.title, a.role, a.relation, a.kind].filter(Boolean).join(", ");
  return `<span class="tchip ${t.type} ${t.status || ""} ${t.stale ? "stale" : ""}" data-id="${t.id || ""}" ${extra}>
    <i></i>${esc(t.canon || t.name)}${t.canon && t.canon !== t.name ? ` <span class="muted">(${esc(t.name)})</span>` : ""}${sub ? ` <span class="muted small">· ${esc(sub)}</span>` : ""}
    ${t.status === "suggested" ? '<span class="sg" title="Claude’s suggestion, not yet checked">?</span>' : t.status === "approved" ? '<span class="ok" title="checked">✓</span>' : t.status === "rejected" ? '<span class="no">✗</span>' : ""}
    ${t.stale ? '<span class="no" title="the words are no longer in the line (edited in Leggio)">⚠</span>' : ""}</span>`;
}

async function loadNames() {
  const ns = await api("/api/names");
  T.names = {}; ns.forEach((n) => (T.names[n.type] = T.names[n.type] || []).push(n.name));
  document.querySelectorAll("datalist.nm").forEach((d) => d.remove());
  for (const ty of TYPES) {
    const d = document.createElement("datalist"); d.id = "nm-" + ty; d.className = "nm";
    d.innerHTML = (T.names[ty] || []).map((n) => `<option value="${esc(n)}">`).join(""); document.body.append(d);
  }
}

async function viewTags(pid) {
  const cid = S.cid;
  const pages = await api(`/api/tagpages/${encodeURIComponent(cid)}`);
  if (!pid) pid = (pages.find((p) => p.suggested) || pages[0] || {}).id;
  if (!pid) { $("#main").innerHTML = `<div class="empty">No tags yet in ${esc(cid)}. Ask Claude to tag pages (suggestions), or open a page and select words to tag them yourself.</div>`; return; }
  await loadNames();
  T.settings = await api(`/api/settings/${encodeURIComponent(cid)}`);
  T.cid = cid; T.page = pid; T.open = null;
  T.data = await api(`/api/tags/${encodeURIComponent(cid)}/${encodeURIComponent(pid)}`);
  const all = T.data.pages, idx = all.findIndex((p) => p.id === pid);
  $("#main").innerHTML = `<div class="tagwrap">
    <aside class="tagside card"><div class="small muted" style="margin-bottom:6px">Pages with tags</div>
      ${pages.map((p) => `<a href="#/m/${encodeURIComponent(cid)}/tags/${encodeURIComponent(p.id)}" class="pg ${p.id === pid ? "on" : ""}">${esc(p.id.split("_")[0])}
        <span class="n">${p.tags}${p.suggested ? ` · <b class="sgc">${p.suggested} ?</b>` : " ✓"}</span></a>`).join("")}
      <div class="small muted" style="margin:10px 0 4px">Any page</div>
      <select id="anypage" style="width:100%">${all.map((p) => `<option value="${esc(p.id)}" ${p.id === pid ? "selected" : ""}>${esc(p.id)} · ${esc(S.status.labels[p.status] || p.status)}</option>`).join("")}</select>
    </aside>
    <section>
      <div class="row" style="margin-bottom:10px">
        <h1 style="margin:0">${esc(pid)}</h1>
        <a class="btn small" href="${esc(T.settings.leggio_url)}/#/p/${encodeURIComponent(cid)}/${encodeURIComponent(pid)}" target="leggio">Open in Leggio ↗</a>
        <span class="spacer"></span>
        ${idx > 0 ? `<a class="btn small" href="#/m/${encodeURIComponent(cid)}/tags/${encodeURIComponent(all[idx - 1].id)}">‹ prev page</a>` : ""}
        ${idx < all.length - 1 ? `<a class="btn small" href="#/m/${encodeURIComponent(cid)}/tags/${encodeURIComponent(all[idx + 1].id)}">next page ›</a>` : ""}
        <button class="btn small primary" id="apprpage">✓ Approve all suggestions on this page</button>
      </div>
      <p class="muted small">Click a tag to check or edit it. To add a tag, select words in a line and pick a type.
        <span class="tchip person"><i></i>person</span> <span class="tchip place"><i></i>place</span> <span class="tchip occupation"><i></i>occupation / role</span>
        <span class="tchip institution"><i></i>institution</span> <span class="tchip goods"><i></i>goods</span> &nbsp; ? = Claude's suggestion · ✓ = checked</p>
      <div id="tlines"></div>
    </section></div>
    <div id="selbar" class="selbar card" hidden>${TYPES.map((t) => `<button class="btn small tbtn ${t}" data-t="${t}">+ ${TLABEL[t]}</button>`).join("")}</div>`;
  $("#anypage").onchange = (e) => (location.hash = `#/m/${encodeURIComponent(cid)}/tags/${encodeURIComponent(e.target.value)}`);
  $("#apprpage").onclick = async () => {
    const r = await api(`/api/tags/${encodeURIComponent(cid)}`, { method: "POST", body: { action: "approve_page", keys: T.data.rows.map((x) => x.key) } });
    alertBar(`${r.approved} tags approved`); viewTags(pid);
  };
  drawTagLines();
  wireSelection();
}

function drawTagLines() {
  $("#tlines").innerHTML = T.data.rows.map((r, i) => {
    const live = r.tags.filter((t) => t.status !== "rejected"), rej = r.tags.filter((t) => t.status === "rejected");
    return `<div class="tline ${r.text.replace(/[_\s]/g, "") ? "" : "empty"}" data-i="${i}">
      <div class="ln">${r.line}</div>
      <div class="lbody">
        <div class="ms ltext" data-i="${i}">${highlight(r.text, live)}</div>
        ${r.translation ? `<div class="small muted">${esc(r.translation)}</div>` : ""}
        <div class="chips">${live.map((t) => chip(t)).join(" ")}
          ${live.some((t) => t.status === "suggested") ? `<button class="btn small" data-apl="${i}">✓ line</button>` : ""}
          <button class="btn small ghost" data-img="${i}" title="Show the line on the page image">🖼</button>
          ${rej.length ? `<span class="small muted">${rej.length} rejected: ${rej.map((t) => chip(t)).join(" ")}</span>` : ""}
          ${r.text_changed ? `<span class="small" style="color:var(--chg)">text edited in Leggio since tagging</span>` : ""}</div>
        <div class="img" hidden></div>
        <div class="editor" hidden></div>
      </div></div>`;
  }).join("");
  $("#tlines").querySelectorAll(".tchip[data-id], mark.tg").forEach((el) => el.onclick = (e) => {
    const line = el.closest(".tline"); openEditor(+line.dataset.i, el.dataset.id); e.stopPropagation();
  });
  $("#tlines").querySelectorAll("[data-apl]").forEach((b) => b.onclick = () => tagOp(+b.dataset.apl, { action: "approve_line" }));
  $("#tlines").querySelectorAll("[data-img]").forEach((b) => b.onclick = () => {
    const r = T.data.rows[+b.dataset.img], box = $(".img", b.closest(".lbody"));
    box.hidden = !box.hidden;
    if (!box.innerHTML) box.innerHTML = `<img class="crop" src="/api/crop/${encodeURIComponent(T.cid)}/${encodeURIComponent(T.page)}?ids=${encodeURIComponent(r.line_ids)}" onerror="this.replaceWith('no image')">`;
  });
}

function attrInputs(type, attrs) {
  return (ATTRS[type] || []).map(([k, opts]) => `<label>${k}<br>${opts
    ? `<select data-attr="${k}">${opts.map((o) => `<option ${String(attrs[k] || "") === o ? "selected" : ""}>${o}</option>`).join("")}</select>`
    : `<input type="text" data-attr="${k}" value="${esc(attrs[k] || "")}" ${k === "of" ? 'list="nm-person"' : ""}>`}</label>`).join("")
    + `<label>note<br><input type="text" data-attr="note" value="${esc(attrs.note || "")}"></label>`;
}

function openEditor(i, id, fresh) {
  const r = T.data.rows[i];
  const t = fresh || r.tags.find((x) => x.id === id);
  if (!t) return;
  document.querySelectorAll(".editor").forEach((e) => { e.hidden = true; e.innerHTML = ""; });
  const ed = $(`.tline[data-i="${i}"] .editor`);
  ed.hidden = false;
  ed.innerHTML = `<div class="row">
      <label>type<br><select class="e-type">${TYPES.map((x) => `<option value="${x}" ${x === t.type ? "selected" : ""}>${TLABEL[x]}</option>`).join("")}</select></label>
      <label>as written<br><input type="text" class="e-span ms" value="${esc(t.span || "")}"></label>
      <label style="flex:1">name (normalized)<br><input type="text" class="e-name" value="${esc(t.name || "")}" list="nm-${t.type}" style="width:100%"></label></div>
    <div class="row attrs">${attrInputs(t.type, t.attrs || {})}</div>
    ${t.attrs && t.attrs.uncertain ? `<div class="small" style="color:var(--chg)">Claude was unsure${t.attrs.note ? "" : ""}.</div>` : ""}
    <div class="row" style="margin-top:8px">
      <button class="btn small primary e-save">${fresh ? "Add tag" : "Save (and approve)"}</button>
      ${!fresh && t.status !== "approved" ? `<button class="btn small ok e-ok">✓ Right as it is</button>` : ""}
      ${!fresh && t.status !== "rejected" ? `<button class="btn small bad e-rej">✗ Wrong tag</button>` : ""}
      ${!fresh && t.status === "rejected" ? `<button class="btn small e-unrej">↺ Restore</button>` : ""}
      ${!fresh && t.source === "laura" ? `<button class="btn small bad e-del">Delete</button>` : ""}
      <button class="btn small e-cancel">Close</button>
      <span class="small muted">${fresh ? "" : `by ${esc(t.source)}${t.edited_by ? ", edited by you" : ""} · ${esc(t.status)}`}</span></div>`;
  $(".e-type", ed).onchange = (e) => { $(".attrs", ed).innerHTML = attrInputs(e.target.value, {}); $(".e-name", ed).setAttribute("list", "nm-" + e.target.value); };
  const val = () => {
    const attrs = {}; ed.querySelectorAll("[data-attr]").forEach((x) => { if (x.value.trim()) attrs[x.dataset.attr] = x.value.trim(); });
    if (t.attrs && t.attrs.uncertain && !("uncertain" in attrs)) attrs.uncertain = true;
    return { type: $(".e-type", ed).value, span: $(".e-span", ed).value, name: $(".e-name", ed).value.trim(), attrs };
  };
  $(".e-save", ed).onclick = () => tagOp(i, fresh ? { action: "add", tag: val() } : { action: "edit", id: t.id, tag: val() });
  if ($(".e-ok", ed)) $(".e-ok", ed).onclick = () => tagOp(i, { action: "approve", id: t.id });
  if ($(".e-rej", ed)) $(".e-rej", ed).onclick = () => tagOp(i, { action: "reject", id: t.id });
  if ($(".e-unrej", ed)) $(".e-unrej", ed).onclick = () => tagOp(i, { action: "suggest", id: t.id });
  if ($(".e-del", ed)) $(".e-del", ed).onclick = () => tagOp(i, { action: "delete", id: t.id });
  $(".e-cancel", ed).onclick = () => { ed.hidden = true; ed.innerHTML = ""; };
  ed.querySelectorAll("input").forEach((x) => x.onkeydown = (e) => { if (e.key === "Enter") $(".e-save", ed).click(); if (e.key === "Escape") $(".e-cancel", ed).click(); });
  $(".e-name", ed).focus();
}

async function tagOp(i, op) {
  const r = T.data.rows[i];
  try {
    await api(`/api/tags/${encodeURIComponent(T.cid)}`, { method: "POST", body: { key: r.key, written: r.text, ...op } });
    const fresh = await api(`/api/tags/${encodeURIComponent(T.cid)}/${encodeURIComponent(T.page)}`);
    T.data.rows = fresh.rows;
    if (op.action === "add" && op.tag) (T.names[op.tag.type] = T.names[op.tag.type] || []).push(op.tag.name);
    drawTagLines();
    S.data = null;   // query/overview caches are stale now
  } catch (e) { alertBar(e.message); }
}

function wireSelection() {
  const bar = $("#selbar");
  let sel = null;
  document.onmouseup = (e) => {
    if (!location.hash.includes("/tags")) return;
    if (bar.contains(e.target)) return;
    const s = window.getSelection(); const txt = s && s.toString().trim();
    const host = s && s.anchorNode && s.anchorNode.parentElement && s.anchorNode.parentElement.closest(".ltext");
    if (!txt || !host) { bar.hidden = true; return; }
    sel = { i: +host.dataset.i, text: txt };
    const rc = s.getRangeAt(0).getBoundingClientRect();
    bar.style.top = `${window.scrollY + rc.bottom + 6}px`; bar.style.left = `${Math.max(8, rc.left)}px`; bar.hidden = false;
  };
  bar.querySelectorAll("[data-t]").forEach((b) => b.onclick = () => {
    bar.hidden = true;
    if (!sel) return;
    openEditor(sel.i, null, { type: b.dataset.t, span: sel.text, name: sel.text, attrs: {}, status: "new" });
  });
}
