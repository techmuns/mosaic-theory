// RADAR (#/radar) — one nav stage, three internal sub-tabs: Map · Inbox · Log. READ-ONLY: the machine
// assembles and sorts (candidates on the map, unreviewed clusters in Inbox, dispositions in Log) but
// NEVER decides — reviews.json is the single record. Deep links #/radar/inbox and #/radar/log load the
// right tab; tab clicks sync the URL (replaceState) without re-fetching. Data contracts unchanged.
import { getRadarCandidates, getRadarSweep, getRadarInbox, getRadarLog } from "../../lib/snapshots.js";
import { escapeHtml } from "../../lib/format.js";

const STATUS_LABEL = { live: "Live", watch: "Watch", parked: "Parked", priced: "Too late", past: "Past" };
const DECISION_LABEL = { advanced: "Advanced", watch: "Watch", parked: "Parked", rejected: "Rejected" };
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// SVG quadrant geometry — the map is now full-width (the old inbox lane in the left margin is gone,
// which also removes the y-axis-label collision). y inverts so y=0 (not moved) is the BOTTOM.
const VB_W = 640, VB_H = 300, PX0 = 48, PX1 = 628, PY0 = 14, PY1 = 258;
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0));
const px = (x) => PX0 + clamp01(x) * (PX1 - PX0);
const py = (y) => PY1 - clamp01(y) * (PY1 - PY0);
const shortLabel = (label) => String(label).length > 15 ? String(label).split(/\s+/)[0] : String(label);
const todayIso = () => new Date().toISOString().slice(0, 10);
const daysSince = (iso) => (Date.parse(todayIso()) - Date.parse(iso)) / 86400000;
const fmtPct = (v) => (v == null || Number.isNaN(Number(v))) ? "—" : `${v >= 0 ? "+" : ""}${Math.round(v * 100)}%`;
const fmtNum = (v) => (v == null || Number.isNaN(Number(v))) ? "—" : String(Math.round(v * 100) / 100);
const fmtDate = (iso) => { const p = String(iso).split("-"); return p.length === 3 ? `${MON[+p[1] - 1]} ${+p[2]}` : String(iso); };
const pager = (attr, page, pages, start, per, total) => total > per
  ? `<div class="rd-pager foot">page ${page + 1} / ${pages} ·
      <button data-${attr}="-1" ${page === 0 ? "disabled" : ""}>‹ prev</button>
      <button data-${attr}="1" ${start + per >= total ? "disabled" : ""}>next ›</button></div>`
  : "";

// --- slim sweep line (one line above the tabs) -------------------------------------------------
function sweepLine(sweep) {
  if (!sweep || !sweep.next_due) return `<div class="rt-sweep foot">sweep status unavailable</div>`;
  const overdue = todayIso() > sweep.next_due, cmd = escapeHtml(sweep.command || "");
  return `<div class="rt-sweep">
    <span class="sweep-dot ${overdue ? "amber" : "green"}" title="${overdue ? "overdue" : "on cadence"}"></span>
    <span class="rt-sweep-txt" title="Component-A sweep · source ${escapeHtml(sweep.source)} · refreshes on the next site build after a run">scan <b>${fmtDate(sweep.last_run)}</b> · next <b>${fmtDate(sweep.next_due)}</b>${
    overdue ? ` <span class="sweep-over">(overdue)</span>` : ""}</span>
    <button class="sweep-run" data-copy="1" data-cmd="${cmd}" title="click to copy">▸ run command</button>
    <code class="sweep-cmd">${cmd}</code>
  </div>`;
}

// --- tab bar -----------------------------------------------------------------------------------
function tabBar(state, inbox, log) {
  const counts = { map: null, inbox: inbox.length, log: (log.reviews || []).length };
  const stale = inbox.some((e) => daysSince(e.first_seen) > 14);
  const tab = (k, label) => `<button class="rt-tab ${state.tab === k ? "on" : ""} ${
    k === "inbox" && stale ? "warn" : ""}" data-tab="${k}" role="tab" aria-selected="${state.tab === k}">${
    label}${counts[k] != null ? ` <span class="rt-badge">${counts[k]}</span>` : ""}</button>`;
  return `<div class="rt-tabs" role="tablist">${tab("map", "Map")}${tab("inbox", "Inbox")}${tab("log", "Log")}</div>`;
}

// --- MAP tab: quadrant + drawer + compact judged list ------------------------------------------
// Greedy label placement: below, above, right, left — first non-overlapping wins.
function placeLabels(pos) {
  const placed = [];
  return pos.map(({ c, x, y }) => {
    const w = shortLabel(c.label).length * 5.4;
    const opts = [
      { x, y: y + 17, anchor: "middle", x1: x - w / 2, x2: x + w / 2, y1: y + 9, y2: y + 21 },
      { x, y: y - 11, anchor: "middle", x1: x - w / 2, x2: x + w / 2, y1: y - 19, y2: y - 7 },
      { x: x + 10, y: y + 4, anchor: "start", x1: x + 10, x2: x + 10 + w, y1: y - 4, y2: y + 8 },
      { x: x - 10, y: y + 4, anchor: "end", x1: x - 10 - w, x2: x - 10, y1: y - 4, y2: y + 8 },
    ];
    const hit = (o) => placed.some((p) => o.x1 < p.x2 && o.x2 > p.x1 && o.y1 < p.y2 && o.y2 > p.y1);
    const chosen = opts.find((o) => !hit(o)) || opts[0];
    placed.push(chosen);
    return { x: chosen.x, y: chosen.y, anchor: chosen.anchor };
  });
}

function mapSvg(cands, drawerSlug) {
  const MX = (PX0 + PX1) / 2, MY = (PY0 + PY1) / 2;
  const bg = `
    <rect x="${MX}" y="${MY}" width="${PX1 - MX}" height="${PY1 - MY}" class="rq-target"/>
    <rect x="${PX0}" y="${PY0}" width="${PX1 - PX0}" height="${PY1 - PY0}" class="rq-frame"/>
    <line x1="${MX}" y1="${PY0}" x2="${MX}" y2="${PY1}" class="rq-mid"/>
    <line x1="${PX0}" y1="${MY}" x2="${PX1}" y2="${MY}" class="rq-mid"/>
    <text x="${PX1 - 8}" y="${PY1 - 8}" class="rq-cap tgt" text-anchor="end">real · not yet moved — target</text>
    <text x="${PX1 - 8}" y="${PY0 + 15}" class="rq-cap" text-anchor="end">real · already moved — late</text>
    <text x="${PX0 + 8}" y="${PY0 + 15}" class="rq-cap">story only · price up</text>
    <text x="${PX0 + 8}" y="${PY1 - 8}" class="rq-cap">quiet</text>`;
  const axes = `
    <text x="${MX}" y="${VB_H - 3}" class="rq-axis" text-anchor="middle">evidence the idea is real →</text>
    <text x="11" y="${MY}" class="rq-axis" text-anchor="middle" transform="rotate(-90 11 ${MY})">price already moved →</text>`;
  const pos = cands.map((c) => ({ c, x: px(c.map && c.map.x), y: py(c.map && c.map.y) }));
  const labels = placeLabels(pos);
  const dots = pos.map(({ c, x, y }, i) => {
    const sel = c.slug === drawerSlug, lb = labels[i];
    const tip = [`${c.label} · ${STATUS_LABEL[c.status] || c.status}`, c.tip, c.px12m].filter(Boolean).join(" · ");
    return `<g class="rq-dot ${escapeHtml(c.status)} ${sel ? "sel" : ""}" data-drawer-open="${escapeHtml(c.slug)}">
      <title>${escapeHtml(tip)}</title>
      ${sel ? `<circle cx="${x}" cy="${y}" r="10" class="rq-ring"/>` : ""}
      <circle cx="${x}" cy="${y}" r="6" class="rq-c"/>
      <text x="${lb.x}" y="${lb.y}" text-anchor="${lb.anchor}" class="rq-lbl">${escapeHtml(shortLabel(c.label))}</text>
    </g>`;
  }).join("");
  return `<svg viewBox="0 0 ${VB_W} ${VB_H}" class="radar-svg" width="100%" role="img"
    aria-label="theme radar quadrant map">${bg}${axes}${dots}</svg>`;
}

// Drawer: collapsed by default, one open at a time. Compact by default; the VERBATIM wake-up rules
// (the wall of text) live behind the "Wake-up rules ▾" expander.
function drawer(c, rulesOpen) {
  if (!c) return "";
  const d = c.detail || {};
  const summary = d.summary || d.note || (d.lead ? `Lead name: ${d.lead}` : "");
  const watch = Array.isArray(d.watch) ? d.watch : [];
  const cmp = Array.isArray(d.comparison) ? d.comparison : [];
  const rules = Array.isArray(d.rules) ? d.rules : [];
  const hasRules = watch.length || rules.length;
  const verbatim = watch.map((w) => `<div class="rd-rule"><span class="rd-tk">${escapeHtml(w.ticker)}</span>
      <span class="rd-rt">${escapeHtml(w.rule)}</span></div>`).join("")
    + (rules.length ? `<ul class="rd-rules">${rules.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul>` : "")
    + cmp.map((x) => `<div class="rd-cmp"><span class="rd-tk">${escapeHtml(x.ticker)}</span>
      <span class="foot">${escapeHtml(x.note)}</span></div>`).join("");
  return `<div class="rt-drawer">
    <div class="rd-head"><span class="rd-name">${escapeHtml(c.label)}</span>
      <span class="pill rd-${escapeHtml(c.status)}">${escapeHtml(STATUS_LABEL[c.status] || c.status)}</span>${
    c.px12m ? `<span class="foot"> · ${escapeHtml(c.px12m)}</span>` : ""}
      <button class="rt-x" data-drawer-close="1" title="close" aria-label="close">×</button></div>
    ${summary ? `<div class="rd-summary">${escapeHtml(summary)}</div>` : ""}
    ${watch.length ? `<div class="rd-line"><span class="rd-k">Watching:</span> ${
      watch.map((w) => escapeHtml(w.ticker)).join(", ")}</div>` : ""}
    ${cmp.length ? `<div class="rd-line"><span class="rd-k">Comparison:</span> ${
      cmp.map((x) => escapeHtml(x.ticker)).join(", ")}</div>` : ""}
    <div class="rd-line foot">found by ${escapeHtml(c.source || "machine scan")}</div>
    ${c.theme_route ? `<div class="rd-link"><a href="#/${escapeHtml(c.theme_route)}">full page →</a></div>` : ""}
    ${hasRules ? `<div class="rt-rules-x">
      <button class="rt-expander" data-drawer-rules="1">Wake-up rules ${rulesOpen ? "▴" : "▾"}</button>
      ${rulesOpen ? `<div class="rt-rules">${verbatim}</div>` : ""}</div>` : ""}
  </div>`;
}

function judgedList(cands, state) {
  const rank = { live: 0, watch: 1, parked: 2 };
  const primary = cands.filter((c) => c.status in rank).sort((a, b) => rank[a.status] - rank[b.status]);
  const low = cands.filter((c) => c.status === "priced" || c.status === "past");
  const row = (c) => `<tr data-drawer-open="${escapeHtml(c.slug)}" class="${c.slug === state.drawer ? "sel" : ""}">
    <td><b>${escapeHtml(c.label)}</b></td>
    <td><span class="pill rd-${escapeHtml(c.status)}">${escapeHtml(STATUS_LABEL[c.status] || c.status)}</span></td>
    <td class="num">${escapeHtml(c.px12m || "—")}</td></tr>`;
  const lowBlock = low.length ? `<tr class="rt-low" data-low-toggle="1"><td colspan="3" class="foot">${
    state.showLow ? "▴" : "▾"} ${low.length} too-late / past · story-placed, not measured</td></tr>${
    state.showLow ? low.map(row).join("") : ""}` : "";
  return `<table class="data rt-judged"><tbody>${primary.map(row).join("")}${lowBlock}</tbody></table>`;
}

function mapTab(cands, state) {
  return `${mapSvg(cands, state.drawer)}
    <div class="rt-hint foot">click a dot for its thesis</div>
    ${state.drawer ? drawer(cands.find((c) => c.slug === state.drawer), state.drawerRules) : ""}
    ${judgedList(cands, state)}`;
}

// --- INBOX tab: least-moved first ---------------------------------------------------------------
const INBOX_PER = 15;
function inboxRow(e, expanded) {
  const isEx = expanded === e.cluster_id;
  const group = e.members.slice(0, 3).join(" ") + (e.members.length > 3 ? ` +${e.members.length - 3}` : "");
  const head = `<tr data-inbox-row="${escapeHtml(e.cluster_id)}" class="${isEx ? "ex" : ""}">
    <td><b>${escapeHtml(group)}</b></td>
    <td class="num">${fmtPct(e.rel12)}</td>
    <td class="num">${fmtNum(e.coherence)}</td>
    <td class="foot">${escapeHtml(e.first_seen)}</td></tr>`;
  if (!isEx) return head;
  return head + `<tr class="rd-log-ex"><td colspan="4">
    <div class="foot"><b>members</b> (${e.members.length}): ${e.members.map(escapeHtml).join(", ")}</div>
    <div class="foot">momentum ${fmtPct(e.mom12)} · breadth-exp ${fmtNum(e.breadth_exp)} · crowding ${fmtNum(e.crowding)}</div>
    </td></tr>`;
}

function inboxTab(inbox, state) {
  const sorted = inbox.slice().sort((a, b) => Math.abs(Number(a.rel12) || 0) - Math.abs(Number(b.rel12) || 0));
  const pages = Math.max(1, Math.ceil(sorted.length / INBOX_PER));
  const page = Math.min(state.inbox.page, pages - 1), start = page * INBOX_PER;
  const body = sorted.slice(start, start + INBOX_PER).map((e) => inboxRow(e, state.inbox.expanded)).join("");
  return `<div class="rt-note foot">least-moved first — the interesting end</div>
    <table class="data rt-inbox"><thead><tr><th>Group</th>
      <th class="num">Price vs market · 12 mo</th><th class="num">Cohesion</th><th>First seen</th></tr></thead>
      <tbody>${body || `<tr><td colspan="4" class="foot">inbox is empty</td></tr>`}</tbody></table>${
    pager("inbox-page", page, pages, start, INBOX_PER, sorted.length)}
    <div class="rt-foot foot">reviews are recorded off-screen; this screen never decides.</div>`;
}

// --- LOG tab -----------------------------------------------------------------------------------
const LOG_PER = 15;
function logRow(r, expanded) {
  const isEx = expanded === r.key, m = r.match || {};
  const added = m.added || [], dropped = m.dropped || [];
  const note = m.status === "gone" ? "no current match (group dissolved)"
    : (added.length || dropped.length) ? `+${added.length} / −${dropped.length} members since review`
    : "unchanged since review";
  const head = `<tr data-log-row="${escapeHtml(r.key)}" class="${isEx ? "ex" : ""}">
    <td><b>${escapeHtml(r.display_name)}</b></td>
    <td class="foot">${escapeHtml(r.reviewed)}</td>
    <td><span class="pill dec-${escapeHtml(r.decision)}">${escapeHtml(DECISION_LABEL[r.decision] || r.decision)}</span></td>
    <td>${escapeHtml(r.reason)}</td></tr>`;
  if (!isEx) return head;
  return head + `<tr class="rd-log-ex"><td colspan="4">
    <div class="foot"><b>members</b> (${r.members.length}): ${r.members.map(escapeHtml).join(", ")}</div>
    <div class="foot"><b>changed since</b>: ${escapeHtml(note)}${
      added.length ? ` · added ${added.map(escapeHtml).join(", ")}` : ""}${
      dropped.length ? ` · dropped ${dropped.map(escapeHtml).join(", ")}` : ""}</div>
    ${r.map_ref ? `<div class="rd-link"><a href="#/themes/${escapeHtml(r.map_ref)}">full page →</a></div>` : ""}
    <div class="foot rd-log-src">recorded by ${escapeHtml(r.by)} · reviews.json is the single record</div>
    </td></tr>`;
}

function logTab(log, state) {
  const reviews = log.reviews || [];
  const ql = state.log.q.trim().toLowerCase();
  let rows = state.log.rejectedOnly ? reviews.filter((r) => r.decision === "rejected") : reviews.slice();
  if (ql) {
    rows = rows.filter((r) => r.display_name.toLowerCase().includes(ql)
      || (r.members || []).some((t) => t.toLowerCase().includes(ql)));
  }
  const pages = Math.max(1, Math.ceil(rows.length / LOG_PER));
  const page = Math.min(state.log.page, pages - 1), start = page * LOG_PER;
  const body = rows.slice(start, start + LOG_PER).map((r) => logRow(r, state.log.expanded)).join("");
  return `<div class="rd-log-controls">
      <input class="rd-log-search" type="search" placeholder="search name or ticker…"
        value="${escapeHtml(state.log.q)}" aria-label="search the review log">
      <button class="chip ${!state.log.rejectedOnly ? "on" : ""}" data-log-tab="all">All</button>
      <button class="chip ${state.log.rejectedOnly ? "on" : ""}" data-log-tab="rejected">Rejected only</button>
      <span class="foot rd-log-count">${rows.length} shown</span>
    </div>
    <table class="data rd-log-tbl"><thead><tr><th>Group</th><th>Reviewed</th><th>Decision</th><th>Reason</th></tr></thead>
      <tbody>${body || `<tr><td colspan="4" class="foot">no matches</td></tr>`}</tbody></table>${
    pager("log-page", page, pages, start, LOG_PER, rows.length)}
    <div class="rt-foot foot">nothing is deleted — rejected means decided.</div>`;
}

function copyCmd(btn) {
  const chip = btn.parentElement.querySelector(".sweep-cmd");
  if (chip) chip.classList.add("show");
  try {
    navigator.clipboard.writeText(btn.getAttribute("data-cmd") || "").then(() => {
      if (chip) { chip.classList.add("flash"); setTimeout(() => chip.classList.remove("flash"), 420); }
    }).catch(() => {});
  } catch (_) { /* clipboard blocked — the chip is revealed for manual copy */ }
}

export async function render(root, params, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading radar…</div>` });
  const [cand, sweep, inboxData, logData] = await Promise.all(
    [getRadarCandidates(), getRadarSweep(), getRadarInbox(), getRadarLog()]);
  const cands = cand.candidates;
  if (!cands.length) {
    root.innerHTML = frame(item, { bodyHtml: `
      <div class="notice">No radar candidates committed to this deploy. Seed
      <code>frontend/radar/candidates.json</code> (analyst-owned) and rebuild.</div>` });
    return;
  }
  const inbox = inboxData.inbox, log = logData;
  const first = params && params[0];
  const state = {
    tab: (first === "inbox" || first === "log") ? first : "map",
    drawer: null, drawerRules: false, showLow: false,
    inbox: { expanded: null, page: 0 },
    log: { q: "", rejectedOnly: false, page: 0, expanded: null },
  };

  root.innerHTML = frame(item, { bodyHtml: `<div class="radar-body">
    ${sweepLine(sweep)}
    <div class="rt-tabbar"></div>
    <div class="rt-content"></div>
  </div>` });

  const q = (s) => root.querySelector(s);
  const syncHash = () => {
    const h = "#/radar" + (state.tab === "map" ? "" : "/" + state.tab);
    if (location.hash !== h) history.replaceState(null, "", h);  // URL follows the tab; no re-dispatch
  };
  const paintTabs = () => { q(".rt-tabbar").innerHTML = tabBar(state, inbox, log); };
  const paintContent = () => {  // full re-render of the active tab; restore log-search focus + caret
    const a = document.activeElement;
    const wasSearch = a && a.classList && a.classList.contains("rd-log-search");
    const caret = wasSearch ? a.selectionStart : null;
    q(".rt-content").innerHTML = state.tab === "inbox" ? inboxTab(inbox, state)
      : state.tab === "log" ? logTab(log, state) : mapTab(cands, state);
    if (wasSearch) {
      const inp = q(".rd-log-search");
      if (inp) { inp.focus(); if (caret != null) inp.setSelectionRange(caret, caret); }
    }
  };

  // Delegate on the re-rendered .radar-body child, NOT the persistent #main (avoids listener stacking).
  const body = root.querySelector(".radar-body");
  body.addEventListener("click", (e) => {
    const t = e.target.closest("[data-tab]");
    if (t) { state.tab = t.dataset.tab; syncHash(); paintTabs(); return paintContent(); }
    const dr = e.target.closest("[data-drawer-open]");
    if (dr) { const s = dr.dataset.drawerOpen; state.drawer = state.drawer === s ? null : s; state.drawerRules = false; return paintContent(); }
    if (e.target.closest("[data-drawer-close]")) { state.drawer = null; return paintContent(); }
    if (e.target.closest("[data-drawer-rules]")) { state.drawerRules = !state.drawerRules; return paintContent(); }
    if (e.target.closest("[data-low-toggle]")) { state.showLow = !state.showLow; return paintContent(); }
    const ir = e.target.closest("[data-inbox-row]");
    if (ir) { state.inbox.expanded = state.inbox.expanded === ir.dataset.inboxRow ? null : ir.dataset.inboxRow; return paintContent(); }
    const ip = e.target.closest("[data-inbox-page]");
    if (ip) { state.inbox.page = Math.max(0, state.inbox.page + Number(ip.dataset.inboxPage)); return paintContent(); }
    const ltab = e.target.closest("[data-log-tab]");
    if (ltab) { state.log.rejectedOnly = ltab.dataset.logTab === "rejected"; state.log.page = 0; return paintContent(); }
    const lr = e.target.closest("[data-log-row]");
    if (lr) { state.log.expanded = state.log.expanded === lr.dataset.logRow ? null : lr.dataset.logRow; return paintContent(); }
    const lp = e.target.closest("[data-log-page]");
    if (lp) { state.log.page = Math.max(0, state.log.page + Number(lp.dataset.logPage)); return paintContent(); }
    const cp = e.target.closest("[data-copy]");
    if (cp) return copyCmd(cp);
  });
  body.addEventListener("input", (e) => {
    if (e.target.closest(".rd-log-search")) { state.log.q = e.target.value; state.log.page = 0; paintContent(); }
  });

  syncHash();
  paintTabs();
  paintContent();
}
