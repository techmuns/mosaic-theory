// RADAR (#/radar) — every theme idea on one map (option A: quadrant hero, detail panel BELOW). A
// READ-ONLY mirror of the analyst-owned candidate registry (radar/candidates.json) + the build-emitted
// sweep bar (radar/sweep.json). No run buttons; nothing fires. Dispositions + wake-up rules render
// VERBATIM. Map axes: x = evidence the idea is real (0..1), y = price already moved (0..1).
import { getRadarCandidates, getRadarSweep } from "../../lib/snapshots.js";
import { escapeHtml } from "../../lib/format.js";

// Plain on-screen words — no internal codenames in UI chrome ("priced" → "Too late").
const STATUS_LABEL = { live: "Live", watch: "Watch", parked: "Parked", priced: "Too late", past: "Past" };
const FILTERS = [["all", "All"], ["live", "Live"], ["watch", "Watch"], ["parked", "Parked"],
  ["priced", "Too late"], ["past", "Past"]];

// SVG plot geometry (viewBox 640x300; width 100%). y inverts so y=0 (not moved) is the BOTTOM.
const VB_W = 640, VB_H = 300, PX0 = 48, PX1 = 628, PY0 = 14, PY1 = 258;
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0));
const px = (x) => PX0 + clamp01(x) * (PX1 - PX0);
const py = (y) => PY1 - clamp01(y) * (PY1 - PY0);
const shortLabel = (label) => String(label).length > 15 ? String(label).split(/\s+/)[0] : String(label);
const todayIso = () => new Date().toISOString().slice(0, 10);

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

// --- quadrant map ------------------------------------------------------------------------------
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

function mapSvg(shown, selSlug) {
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
  const pos = shown.map((c) => ({ c, x: px(c.map && c.map.x), y: py(c.map && c.map.y) }));
  const labels = placeLabels(pos);
  const dots = pos.map(({ c, x, y }, i) => {
    const sel = c.slug === selSlug, lb = labels[i];
    const tip = [`${c.label} · ${STATUS_LABEL[c.status] || c.status}`, c.tip, c.px12m].filter(Boolean).join(" · ");
    return `<g class="rq-dot ${escapeHtml(c.status)} ${sel ? "sel" : ""}" data-dot="${escapeHtml(c.slug)}">
      <title>${escapeHtml(tip)}</title>
      ${sel ? `<circle cx="${x}" cy="${y}" r="10" class="rq-ring"/>` : ""}
      <circle cx="${x}" cy="${y}" r="6" class="rq-c"/>
      <text x="${lb.x}" y="${lb.y}" text-anchor="${lb.anchor}" class="rq-lbl">${escapeHtml(shortLabel(c.label))}</text>
    </g>`;
  }).join("");
  return `<svg viewBox="0 0 ${VB_W} ${VB_H}" class="radar-svg" width="100%" role="img"
    aria-label="theme radar quadrant map">${bg}${axes}${dots}</svg>`;
}

// --- detail panel (below the map) --------------------------------------------------------------
function detailPanel(c) {
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

// --- list --------------------------------------------------------------------------------------
const PER_PAGE = 12;
function listTable(shown, state) {
  const total = shown.length, pages = Math.max(1, Math.ceil(total / PER_PAGE));
  const page = Math.min(state.page, pages - 1), start = page * PER_PAGE;
  const rows = shown.slice(start, start + PER_PAGE).map((c) => `
    <tr data-row="${escapeHtml(c.slug)}" class="${c.slug === state.selected ? "sel" : ""}">
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
  const [cand, sweep] = await Promise.all([getRadarCandidates(), getRadarSweep()]);
  const cands = cand.candidates;
  if (!cands.length) {
    root.innerHTML = frame(item, { bodyHtml: `
      <div class="notice">No radar candidates committed to this deploy. Seed
      <code>frontend/radar/candidates.json</code> (analyst-owned) and rebuild.</div>` });
    return;
  }
  const state = { filter: "all", selected: (cands.find((c) => c.status === "live") || cands[0]).slug, page: 0 };

  root.innerHTML = frame(item, { bodyHtml: `<div class="radar-body">
    ${sweepBar(sweep)}
    <div class="radar-filters chips"></div>
    <div class="radar-map"></div>
    <div class="radar-detail rd-panel"></div>
    <div class="radar-list"></div>
    <div class="radar-foot foot">Read-only mirror of the analyst's dispositions — no run buttons; nothing
      fires here. Past markers are story-placed, not measured.</div>
    </div>` });

  const q = (s) => root.querySelector(s);
  const paint = () => {
    const shown = cands.filter((c) => state.filter === "all" || c.status === state.filter);
    q(".radar-filters").innerHTML = FILTERS.map(([k, l]) => {
      const n = k === "all" ? cands.length : cands.filter((c) => c.status === k).length;
      return `<button class="chip radar-chip ${state.filter === k ? "on" : ""}" data-filter="${k}">${
        escapeHtml(l)} <span class="rc-n">${n}</span></button>`;
    }).join("");
    q(".radar-map").innerHTML = mapSvg(shown, state.selected);
    const sel = cands.find((c) => c.slug === state.selected && shown.includes(c));
    q(".radar-detail").innerHTML = detailPanel(sel);
    q(".radar-list").innerHTML = listTable(shown, state);
  };

  // Delegate on the re-rendered .radar-body child, NOT the persistent #main: attaching to #main would
  // stack a new click listener on every #/radar visit. Every other view delegates on a fresh child.
  root.querySelector(".radar-body").addEventListener("click", (e) => {
    const f = e.target.closest("[data-filter]");
    if (f) { state.filter = f.dataset.filter; state.page = 0; return paint(); }
    const dot = e.target.closest("[data-dot]");
    if (dot) { state.selected = dot.dataset.dot; return paint(); }
    const rowEl = e.target.closest("[data-row]");
    if (rowEl) { state.selected = rowEl.dataset.row; return paint(); }
    const pg = e.target.closest("[data-page]");
    if (pg) { state.page = Math.max(0, state.page + Number(pg.dataset.page)); return paint(); }
    const cp = e.target.closest("[data-copy]");
    if (cp) return copyCmd(cp);
  });

  paint();
}
