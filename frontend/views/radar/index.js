// RADAR (#/radar) — every theme idea on one map (option A: quadrant hero, detail panel BELOW), PLUS
// the INBOX lane (current-sweep clusters not yet judged) and the REVIEW LOG (the analyst's recorded
// dispositions). READ-ONLY: reviews.json is the SINGLE record of decisions — this screen ASSEMBLES and
// SORTS (matched → log, unmatched → inbox) but NEVER decides. Quadrant axes: x = evidence the idea is
// real (0..1), y = price already moved (0..1). Inbox lane: y = 12mo rel-strength (clamped); NO x-axis.
import { getRadarCandidates, getRadarSweep, getRadarInbox, getRadarLog } from "../../lib/snapshots.js";
import { escapeHtml } from "../../lib/format.js";

// Plain on-screen words — no internal codenames in UI chrome ("priced" → "Too late").
const STATUS_LABEL = { live: "Live", watch: "Watch", parked: "Parked", priced: "Too late", past: "Past" };
const DECISION_LABEL = { advanced: "Advanced", watch: "Watch", parked: "Parked", rejected: "Rejected" };
const FILTERS = [["all", "All"], ["live", "Live"], ["watch", "Watch"], ["parked", "Parked"],
  ["priced", "Too late"], ["past", "Past"]];

// SVG geometry. The quadrant keeps its original 0..640 box; the INBOX LANE lives in the widened LEFT
// margin (negative x), so the quadrant is NEVER reshaped. y inverts so y=0 (not moved) is the BOTTOM.
const VB_X = -112, VB_W = 752, VB_H = 300, PX0 = 48, PX1 = 628, PY0 = 14, PY1 = 258;
const LANE_DOT_X = -98, LANE_LBL_X = -90, LANE_LO = -1.2, LANE_HI = 1.2;  // rel12 clamp for the lane
const LANE_Y0 = PY0 + 22;  // dots start below this — reserves the top of the lane for the header
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0));
const px = (x) => PX0 + clamp01(x) * (PX1 - PX0);
const py = (y) => PY1 - clamp01(y) * (PY1 - PY0);
const shortLabel = (label) => String(label).length > 15 ? String(label).split(/\s+/)[0] : String(label);
const todayIso = () => new Date().toISOString().slice(0, 10);
const daysSince = (iso) => (Date.parse(todayIso()) - Date.parse(iso)) / 86400000;
const fmtPct = (v) => (v == null || Number.isNaN(Number(v))) ? "—" : `${v >= 0 ? "+" : ""}${Math.round(v * 100)}%`;
const fmtNum = (v) => (v == null || Number.isNaN(Number(v))) ? "—" : String(Math.round(v * 100) / 100);

// --- sweep bar ---------------------------------------------------------------------------------
function sweepBar(sweep) {
  if (!sweep || !sweep.next_due) return `<div class="sweep-bar foot">Sweep status unavailable.</div>`;
  const overdue = todayIso() > sweep.next_due;
  const cmd = escapeHtml(sweep.command || "");
  return `
    <div class="sweep-bar">
      <span class="sweep-dot ${overdue ? "amber" : "green"}" title="${overdue ? "overdue" : "on cadence"}"></span>
      <span class="sweep-txt" title="sweep date refreshes on the next site build after a run">Component-A sweep · last run <b>${escapeHtml(sweep.last_run)}</b>
        <span class="foot">(${escapeHtml(sweep.source)})</span> · next due <b>${escapeHtml(sweep.next_due)}</b>${
    overdue ? ` <span class="sweep-over">(overdue)</span>` : ""}</span>
      <button class="sweep-run" data-copy="1" data-cmd="${cmd}" title="click to copy">▸ run command</button>
      <code class="sweep-cmd">${cmd}</code>
    </div>`;
}

// --- quadrant map + inbox lane -----------------------------------------------------------------
// Greedy label placement: try below, above, right, left; first non-overlapping wins (auto-offset).
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

// Inbox lane: hollow gray dots at y = CLAMPED rel12, de-collided so labels stay legible. RULE: inbox
// dots NEVER receive a quadrant x-position — they live in the left lane at a fixed column; x is the
// lane, not evidence. An unjudged cluster has no "how real" reading until the analyst reviews it.
function laneLayout(inbox) {
  const yFor = (r) => PY1
    - (Math.max(LANE_LO, Math.min(LANE_HI, Number(r) || 0)) - LANE_LO) / (LANE_HI - LANE_LO) * (PY1 - LANE_Y0);
  const items = inbox.map((e) => ({ e, y: yFor(e.rel12) })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < items.length; i++) {
    if (items[i].y - items[i - 1].y < 16) items[i].y = items[i - 1].y + 16;
  }
  return items;
}

function inboxLane(inbox, scanDate, selId) {
  if (!inbox.length) return "";
  const head = `
    <text x="${VB_X + 4}" y="11" class="rq-lane-h">inbox — ${escapeHtml(scanDate || "")}</text>
    <text x="${VB_X + 4}" y="23" class="rq-lane-sub">not yet judged</text>
    <line x1="-6" y1="${PY0}" x2="-6" y2="${PY1}" class="rq-mid"/>`;
  const dots = laneLayout(inbox).map(({ e, y }) => {
    const sel = selId === e.cluster_id;
    const tip = [e.label, `rel12 ${fmtPct(e.rel12)} · mom12 ${fmtPct(e.mom12)} · coh ${fmtNum(e.coherence)}`,
      `first seen ${e.first_seen}`, e.members.join(" ")].join(" · ");
    return `<g class="rq-lane-dot ${sel ? "sel" : ""}" data-inbox="${escapeHtml(e.cluster_id)}">
      <title>${escapeHtml(tip)}</title>
      ${sel ? `<circle cx="${LANE_DOT_X}" cy="${y}" r="7" class="rq-ring"/>` : ""}
      <circle cx="${LANE_DOT_X}" cy="${y}" r="4.5" class="rq-lane-c"/>
      <text x="${LANE_LBL_X}" y="${y + 3}" class="rq-lane-lbl">${escapeHtml(e.label)} ${fmtPct(e.rel12)}</text>
    </g>`;
  }).join("");
  return head + dots;
}

function mapSvg(shown, state, inbox, scanDate) {
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
  const lane = inboxLane(inbox, scanDate, state.sel.type === "inbox" ? state.sel.id : null);
  const pos = shown.map((c) => ({ c, x: px(c.map && c.map.x), y: py(c.map && c.map.y) }));
  const labels = placeLabels(pos);
  const dots = pos.map(({ c, x, y }, i) => {
    const sel = state.sel.type === "candidate" && c.slug === state.sel.id, lb = labels[i];
    const tip = [`${c.label} · ${STATUS_LABEL[c.status] || c.status}`, c.tip, c.px12m].filter(Boolean).join(" · ");
    return `<g class="rq-dot ${escapeHtml(c.status)} ${sel ? "sel" : ""}" data-dot="${escapeHtml(c.slug)}">
      <title>${escapeHtml(tip)}</title>
      ${sel ? `<circle cx="${x}" cy="${y}" r="10" class="rq-ring"/>` : ""}
      <circle cx="${x}" cy="${y}" r="6" class="rq-c"/>
      <text x="${lb.x}" y="${lb.y}" text-anchor="${lb.anchor}" class="rq-lbl">${escapeHtml(shortLabel(c.label))}</text>
    </g>`;
  }).join("");
  return `<svg viewBox="${VB_X} 0 ${VB_W} ${VB_H}" class="radar-svg" width="100%" role="img"
    aria-label="theme radar quadrant map with inbox lane">${bg}${axes}${lane}${dots}</svg>`;
}

// --- filter row (status chips + the inbox indicator) -------------------------------------------
function filtersHtml(cands, inbox, state) {
  const chips = FILTERS.map(([k, l]) => {
    const n = k === "all" ? cands.length : cands.filter((c) => c.status === k).length;
    return `<button class="chip radar-chip ${state.filter === k ? "on" : ""}" data-filter="${k}">${
      escapeHtml(l)} <span class="rc-n">${n}</span></button>`;
  }).join("");
  if (!inbox.length) return chips;
  const stale = inbox.some((e) => daysSince(e.first_seen) > 14);
  return chips + `<button class="chip radar-chip inbox-chip ${stale ? "warn" : ""}" data-inbox-chip="1"
    title="unreviewed clusters from the latest sweep — the analyst records the verdict, not this screen"
    >Inbox · ${inbox.length} unreviewed</button>`;
}

// --- detail panel (below the map) — candidate OR inbox --------------------------------------------
function candidateDetail(c) {
  if (!c) return `<div class="rd-empty foot">Select a dot or a row to read its detail.</div>`;
  const d = c.detail || {}, out = [];
  out.push(`<div class="rd-head"><span class="rd-name">${escapeHtml(c.label)}</span>
    <span class="pill rd-${escapeHtml(c.status)}">${escapeHtml(STATUS_LABEL[c.status] || c.status)}</span>${
    c.px12m ? `<span class="foot"> · ${escapeHtml(c.px12m)}</span>` : ""}</div>`);
  if (d.summary) out.push(`<div class="rd-summary">${escapeHtml(d.summary)}</div>`);
  if (d.lead) out.push(`<div class="rd-lead foot">Lead name: <b>${escapeHtml(d.lead)}</b></div>`);
  if (Array.isArray(d.watch) && d.watch.length) {
    out.push(`<div class="rd-sec"><div class="rd-sec-h">Watch — wake-up rule (verbatim)</div>` +
      d.watch.map((w) => `<div class="rd-rule"><span class="rd-tk">${escapeHtml(w.ticker)}</span>
        <span class="rd-rt">${escapeHtml(w.rule)}</span></div>`).join("") + `</div>`);
  }
  if (Array.isArray(d.rules) && d.rules.length) {
    out.push(`<div class="rd-sec"><div class="rd-sec-h">Wake-up rule${d.rules.length > 1 ? "s" : ""} (verbatim)</div>
      <ul class="rd-rules">${d.rules.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul></div>`);
  }
  if (Array.isArray(d.comparison) && d.comparison.length) {
    out.push(`<div class="rd-sec"><div class="rd-sec-h">Comparison legs</div>` +
      d.comparison.map((x) => `<div class="rd-cmp"><span class="rd-tk">${escapeHtml(x.ticker)}</span>
        <span class="foot">${escapeHtml(x.note)}</span></div>`).join("") + `</div>`);
  }
  if (d.note) out.push(`<div class="rd-note foot">${escapeHtml(d.note)}</div>`);
  if (c.theme_route) out.push(`<div class="rd-link"><a href="#/${escapeHtml(c.theme_route)}">full page →</a></div>`);
  return out.join("");
}

function inboxDetail(e) {
  if (!e) return `<div class="rd-empty foot">Select a dot or a row to read its detail.</div>`;
  const stats = `rel vs mkt ${fmtPct(e.rel12)} · momentum ${fmtPct(e.mom12)} · coherence ${fmtNum(e.coherence)}`
    + ` · breadth-exp ${fmtNum(e.breadth_exp)} · crowding ${fmtNum(e.crowding)}`;
  return `<div class="rd-head"><span class="rd-name">${escapeHtml(e.label)}</span>
      <span class="pill rd-inbox">Inbox · not yet judged</span></div>
    <div class="rd-sec"><div class="rd-sec-h">Members (${e.members.length})</div>
      <div class="rd-mem">${e.members.map((t) => `<span class="rd-tk">${escapeHtml(t)}</span>`).join(" ")}</div></div>
    <div class="rd-sec"><div class="rd-sec-h">Signals · 12 mo (display only)</div>
      <div class="foot">${escapeHtml(stats)}</div></div>
    <div class="rd-note foot">first seen ${escapeHtml(e.first_seen)}</div>
    <div class="rd-note foot">review is recorded in reviews.json — this screen never decides.</div>`;
}

function detailPanel(state, cands, shown, inbox) {
  if (state.sel.type === "inbox") return inboxDetail(inbox.find((e) => e.cluster_id === state.sel.id));
  const c = cands.find((x) => x.slug === state.sel.id);
  return candidateDetail(c && shown.includes(c) ? c : null);
}

// --- candidate list ----------------------------------------------------------------------------
const PER_PAGE = 12;
function listTable(shown, state) {
  const total = shown.length, pages = Math.max(1, Math.ceil(total / PER_PAGE));
  const page = Math.min(state.page, pages - 1), start = page * PER_PAGE;
  const selId = state.sel.type === "candidate" ? state.sel.id : null;
  const rows = shown.slice(start, start + PER_PAGE).map((c) => `
    <tr data-row="${escapeHtml(c.slug)}" class="${c.slug === selId ? "sel" : ""}">
      <td><b>${escapeHtml(c.label)}</b></td>
      <td><span class="pill rd-${escapeHtml(c.status)}">${escapeHtml(STATUS_LABEL[c.status] || c.status)}</span></td>
      <td class="foot">${escapeHtml(c.source || "")}</td>
      <td class="num">${escapeHtml(c.px12m || "—")}</td>
    </tr>`).join("");
  const pager = total > PER_PAGE ? `<div class="rd-pager foot">page ${page + 1} / ${pages} ·
    <button data-page="-1" ${page === 0 ? "disabled" : ""}>‹ prev</button>
    <button data-page="1" ${start + PER_PAGE >= total ? "disabled" : ""}>next ›</button></div>` : "";
  return `<table class="data radar-tbl"><thead><tr><th>Theme</th><th>Status</th><th>Found by</th>
    <th class="num">Price vs market · 12 mo</th></tr></thead><tbody>${rows || ""}</tbody></table>${pager}`;
}

// --- review log --------------------------------------------------------------------------------
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
    <div class="foot"><b>current</b>: ${escapeHtml(note)}${
      added.length ? ` · added ${added.map(escapeHtml).join(", ")}` : ""}${
      dropped.length ? ` · dropped ${dropped.map(escapeHtml).join(", ")}` : ""}</div>
    ${r.map_ref ? `<div class="rd-link"><a href="#/themes/${escapeHtml(r.map_ref)}">full page →</a></div>` : ""}
    <div class="foot rd-log-src">reason recorded by ${escapeHtml(r.by)} · reviews.json is the single record</div>
    </td></tr>`;
}

function logSection(log, state) {
  const reviews = (log && log.reviews) || [];
  const ql = state.log.q.trim().toLowerCase();
  let rows = state.log.rejectedOnly ? reviews.filter((r) => r.decision === "rejected") : reviews.slice();
  if (ql) {
    rows = rows.filter((r) => r.display_name.toLowerCase().includes(ql)
      || (r.members || []).some((t) => t.toLowerCase().includes(ql)));
  }
  const pages = Math.max(1, Math.ceil(rows.length / LOG_PER));
  const page = Math.min(state.log.page, pages - 1), start = page * LOG_PER;
  const body = rows.slice(start, start + LOG_PER).map((r) => logRow(r, state.log.expanded)).join("");
  const pager = rows.length > LOG_PER ? `<div class="rd-pager foot">page ${page + 1} / ${pages} ·
    <button data-log-page="-1" ${page === 0 ? "disabled" : ""}>‹ prev</button>
    <button data-log-page="1" ${start + LOG_PER >= rows.length ? "disabled" : ""}>next ›</button></div>` : "";
  return `<div class="rd-log-h">Review log <span class="foot">· ${reviews.length} groups reviewed ·
      the analyst's recorded dispositions (reasons verbatim from reviews.json)</span></div>
    <div class="rd-log-controls">
      <input class="rd-log-search" type="search" placeholder="search name or ticker…"
        value="${escapeHtml(state.log.q)}" aria-label="search the review log">
      <button class="chip ${!state.log.rejectedOnly ? "on" : ""}" data-log-tab="all">All</button>
      <button class="chip ${state.log.rejectedOnly ? "on" : ""}" data-log-tab="rejected">Rejected only</button>
      <span class="foot rd-log-count">${rows.length} shown</span>
    </div>
    <table class="data rd-log-tbl"><thead><tr><th>Group</th><th>Reviewed</th><th>Decision</th><th>Reason</th></tr></thead>
      <tbody>${body || `<tr><td colspan="4" class="foot">no matches</td></tr>`}</tbody></table>${pager}`;
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

export async function render(root, _params, { item, frame }) {
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
  const scanDate = inboxData.scan_date || logData.scan_date || "";
  const state = {
    filter: "all",
    sel: { type: "candidate", id: (cands.find((c) => c.status === "live") || cands[0]).slug },
    page: 0,
    log: { q: "", rejectedOnly: false, page: 0, expanded: null },
  };

  root.innerHTML = frame(item, { bodyHtml: `<div class="radar-body">
    ${sweepBar(sweep)}
    <div class="radar-filters chips"></div>
    <div class="radar-map"></div>
    <div class="radar-detail rd-panel"></div>
    <div class="radar-list"></div>
    <div class="radar-foot foot">Read-only mirror of the analyst's dispositions — no run buttons; nothing
      fires here. Past markers are story-placed, not measured.</div>
    <div class="radar-log"></div>
    </div>` });

  const q = (s) => root.querySelector(s);
  const paintLog = () => {  // re-render the log, restoring search focus + caret when typing
    const el = q(".radar-log");
    const a = document.activeElement;
    const wasSearch = a && a.classList && a.classList.contains("rd-log-search");
    const caret = wasSearch ? a.selectionStart : null;
    el.innerHTML = logSection(log, state);
    if (wasSearch) {
      const inp = el.querySelector(".rd-log-search");
      if (inp) { inp.focus(); if (caret != null) inp.setSelectionRange(caret, caret); }
    }
  };
  const paint = () => {
    const shown = cands.filter((c) => state.filter === "all" || c.status === state.filter);
    q(".radar-filters").innerHTML = filtersHtml(cands, inbox, state);
    q(".radar-map").innerHTML = mapSvg(shown, state, inbox, scanDate);
    q(".radar-detail").innerHTML = detailPanel(state, cands, shown, inbox);
    q(".radar-list").innerHTML = listTable(shown, state);
    paintLog();
  };

  // Delegate on the re-rendered .radar-body child, NOT the persistent #main: attaching to #main would
  // stack a new listener on every #/radar visit. Every other view delegates on a fresh child.
  const body = root.querySelector(".radar-body");
  body.addEventListener("click", (e) => {
    const f = e.target.closest("[data-filter]");
    if (f) { state.filter = f.dataset.filter; state.page = 0; return paint(); }
    const ic = e.target.closest("[data-inbox-chip]");
    if (ic) { if (inbox.length) state.sel = { type: "inbox", id: inbox[0].cluster_id }; return paint(); }
    const ib = e.target.closest("[data-inbox]");
    if (ib) { state.sel = { type: "inbox", id: ib.dataset.inbox }; return paint(); }
    const dot = e.target.closest("[data-dot]");
    if (dot) { state.sel = { type: "candidate", id: dot.dataset.dot }; return paint(); }
    const rowEl = e.target.closest("[data-row]");
    if (rowEl) { state.sel = { type: "candidate", id: rowEl.dataset.row }; return paint(); }
    const pg = e.target.closest("[data-page]");
    if (pg) { state.page = Math.max(0, state.page + Number(pg.dataset.page)); return paint(); }
    const lt = e.target.closest("[data-log-tab]");
    if (lt) { state.log.rejectedOnly = lt.dataset.logTab === "rejected"; state.log.page = 0; return paintLog(); }
    const lr = e.target.closest("[data-log-row]");
    if (lr) { state.log.expanded = state.log.expanded === lr.dataset.logRow ? null : lr.dataset.logRow; return paintLog(); }
    const lp = e.target.closest("[data-log-page]");
    if (lp) { state.log.page = Math.max(0, state.log.page + Number(lp.dataset.logPage)); return paintLog(); }
    const cp = e.target.closest("[data-copy]");
    if (cp) return copyCmd(cp);
  });
  body.addEventListener("input", (e) => {
    const s = e.target.closest(".rd-log-search");
    if (s) { state.log.q = s.value; state.log.page = 0; paintLog(); }
  });

  paint();
}
