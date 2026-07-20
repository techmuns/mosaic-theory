// RANKER — the priority queue as a sortable read-only table with per-name structural profiles +
// a workflow state per row. Orders, never decides. Rows open the dossier. Sort/filter are purely
// client-side, in place — the queue is fetched once and never re-fetched on sort/filter.
import { getRankedQueue, getProcessedStates, getG3Reasons } from "../../lib/snapshots.js";
import { fmtScore, fmtMoney, fmtDate, fmtPct, escapeHtml, DASH } from "../../lib/format.js";
import { refreshBlock } from "../../lib/ui.js";

const AXES = ["idiosyncrasy", "depth", "character", "multiple"];
const COLS = [
  { key: "rank", label: "#", num: true }, { key: "ticker", label: "Ticker" },
  { key: "industry", label: "Industry" },  // DERIVED SIC sub-industry — assemble/inform, not a rank input
  { key: "state", label: "Workflow" },
  { key: "score", label: "Score", num: true }, { key: "depthBand", label: "Band" },
  { key: "idiosyncrasy", label: "Idio (vs mkt)", num: true }, { key: "depth", label: "Depth (52w)", num: true },
  { key: "character", label: "Character" }, { key: "multiple", label: "Multiple" },
  { key: "advUsd", label: "ADV", num: true }, { key: "marketCap", label: "Mkt cap", num: true },
];
const STATE_RANK = { "not-started": 0, "underwritten": 1, "dossier-built": 2, "verdict-logged": 3 };
const STATE_BADGE = {
  "not-started": `<span class="pill" style="background:var(--surface-2);color:var(--ink-3);">not started</span>`,
  // scenario-record PRESENCE (a first-cut underwrite exists) — an intermediate workflow state,
  // amber so it can never read as a ledger verdict.
  "underwritten": `<span class="pill conditional">underwritten</span>`,
  "dossier-built": `<span class="pill" style="background:var(--accent-bg);color:var(--accent-strong);">dossier</span>`,
  "verdict-logged": `<span class="pill" style="background:var(--live-bg);color:var(--pos-text);">verdict ✓</span>`,
};

let DATA = null;
let stateOf = null; // (ticker) => workflow state
let G3 = null; // ticker -> the specific G3 UNKNOWN reason
let state = null;

export async function render(root, _params, { item, frame }) {
  state = { sort: "rank", dir: 1, q: "", hideSunk: false };
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading queue…</div>` });
  [DATA, stateOf, G3] = await Promise.all([getRankedQueue(), getProcessedStates(), getG3Reasons()]);

  const w = DATA.weights;
  const edge = `
    <div class="chips" style="margin-bottom:12px;">
      <span class="chip live"><span class="dot live"></span> Edge · Overshoot</span>
      <span class="chip locked">🔒 Neglected (locked until the gate clears)</span>
    </div>`;
  const legend = `
    <div class="card" style="padding:11px 16px; margin-bottom:14px; background:var(--surface-2);">
      <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink-3); font-weight:600; margin-bottom:5px;">Axis legend</div>
      <div style="display:grid; grid-template-columns:repeat(2,1fr); gap:3px 24px; font-size:12px; color:var(--ink-2);">
        <div><b>Idiosyncrasy</b> — name-specific drawdown vs the market (G2)</div>
        <div><b>Character</b> — the shape of the decline (sharp/discrete vs grind)</div>
        <div><b>Depth</b> — distance from the 52-week high (G1)</div>
        <div><b>Multiple</b> — cheapness vs the name's own ~5-year history (G3)</div>
      </div>
    </div>`;

  const controls = `
    <div style="display:flex; gap:14px; align-items:center; flex-wrap:wrap; margin-bottom:12px;">
      <input id="rk-q" type="search" placeholder="Filter ticker, name, or industry…" autocomplete="off" value=""
        style="flex:1; min-width:200px; padding:8px 11px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
      <label style="font-size:12.5px; color:var(--ink-2); display:flex; gap:6px; align-items:center; cursor:pointer;">
        <input id="rk-hide" type="checkbox" /> hide structurally-sunk (${DATA.counts.demoted})
      </label>
      <span class="muted" style="font-size:12px;">${DATA.counts.total} candidates · screened ${escapeHtml(fmtDate(DATA.asOf))}</span>
    </div>
    <div class="subtitle muted" style="margin-bottom:12px;">
      Columns lead with the interpretable quantity (depth/idio as % moves, multiple as the percentile or reason); hover a cell
      for the 0–1 sub-score that the composite (idiosyncrasy ${w.idiosyncrasy} · depth ${w.depth} · character ${w.character} · multiple ${w.multiple}
      + volume overlay, then a tradeability gate) is built from. Click a row for the dossier; the <b>Workflow</b> column shows where to
      spend effort next. Face-validity weights — never tuned on returns.
    </div>`;

  root.innerHTML = frame(item, {
    bodyHtml: edge + legend + controls
      + `<table class="data" id="rk-table"><thead><tr id="rk-head"></tr></thead><tbody id="rk-body"></tbody></table>`
      + refreshBlock(),
  });
  renderHead();
  renderRows();

  root.querySelector("#rk-q").addEventListener("input", (e) => { state.q = e.target.value.toLowerCase(); renderRows(); });
  root.querySelector("#rk-hide").addEventListener("change", (e) => { state.hideSunk = e.target.checked; renderRows(); });
  root.querySelector("#rk-head").addEventListener("click", (e) => {
    const th = e.target.closest("th[data-sort]");
    if (!th) return;
    const k = th.dataset.sort;
    if (state.sort === k) state.dir *= -1;
    else { state.sort = k; state.dir = (k === "rank" || k === "ticker" || k === "depthBand" || k === "state") ? 1 : -1; }
    renderHead();
    renderRows();
  });
}

function renderHead() {
  const head = document.getElementById("rk-head");
  if (!head) return;
  head.innerHTML = COLS.map((c) => {
    const arrow = state.sort === c.key ? (state.dir > 0 ? " ▲" : " ▼") : "";
    return `<th data-sort="${c.key}" class="${c.num ? "num" : ""}" style="cursor:pointer; user-select:none;">${c.label}${arrow}</th>`;
  }).join("");
}

function axisVal(row, key) {
  if (AXES.includes(key)) return row.axes[key]?.score;
  if (key === "state") return STATE_RANK[stateOf(row.ticker)] ?? 0;
  return row[key];
}

function renderRows() {
  const body = document.getElementById("rk-body");
  if (!body) return;
  let rows = DATA.rows.slice();
  if (state.q) rows = rows.filter((r) => r.ticker.toLowerCase().includes(state.q) || (r.name || "").toLowerCase().includes(state.q) || (r.sector || "").toLowerCase().includes(state.q) || (r.industry || "").toLowerCase().includes(state.q));
  if (state.hideSunk) rows = rows.filter((r) => !r.structurallyDisqualified);

  rows.sort((a, b) => {
    const va = axisVal(a, state.sort), vb = axisVal(b, state.sort);
    if (typeof va === "string" || typeof vb === "string")
      return String(va ?? "").localeCompare(String(vb ?? "")) * state.dir;
    return ((va ?? -Infinity) - (vb ?? -Infinity)) * state.dir;
  });

  // 3b/3c: lead with the interpretable raw quantity; the 0–1 sub-score is secondary (hover title).
  const rawCell = (r, k) => {
    const a = r.axes[k] || {};
    const v = a.raw == null ? `<span class="muted">${DASH}</span>` : fmtPct(a.raw, { signed: true });
    return `<td class="num" title="sub-score ${a.score == null ? "—" : a.score.toFixed(2)} · ${escapeHtml(a.label || "")}">${v}</td>`;
  };
  // 3d: character qualitatively — its sub-signals (sharp-discrete vs grind/bleed, gap count, recency)
  // are translatable, so lead with the interpretable form; 0–1 sub-score + full read on hover.
  const charCell = (r) => {
    const a = r.axes.character || {};
    if (a.score == null) return `<td><span class="muted">${DASH}</span></td>`;
    const lbl = a.label || "";
    let q;
    if (/grind|bleed/i.test(lbl)) {
      q = "grind/bleed";
    } else {
      const n = (lbl.match(/(\d+)\s+gap-down/) || [])[1];
      const age = (lbl.match(/(\d+)d ago/) || [])[1];
      q = "sharp" + (n ? ` · ${n} gap${n === "1" ? "" : "s"}` : "") + (age ? ` · ${age}d ago` : "");
    }
    if (/mean.?revert/i.test(lbl)) q += " · revert";
    else if (/structural.?break/i.test(lbl)) q += " · break";
    return `<td style="font-size:12px;" title="sub-score ${a.score.toFixed(2)} · ${escapeHtml(lbl)}">${escapeHtml(q)}</td>`;
  };
  const multCell = (r) => {
    const a = r.axes.multiple || {};
    if (a.coverage === "unknown") {
      const reason = G3[r.ticker] || "multiple unavailable";
      return `<td class="muted" style="font-style:italic; font-size:11.5px;" title="${escapeHtml(a.label || "")}">${escapeHtml(reason)}</td>`;
    }
    const short = (a.label || "").split(" of ")[0]; // "P/E 0%ile of own 5y range" → "P/E 0%ile"
    return `<td title="sub-score ${a.score == null ? "—" : a.score.toFixed(2)} · ${escapeHtml(a.label || "")}">${escapeHtml(short)}</td>`;
  };

  body.innerHTML = rows.map((r) => {
    const sunk = r.structurallyDisqualified;
    const flag = sunk && r.structuralFlag
      ? `<div class="cite" style="color:var(--danger);">⛔ ${escapeHtml(r.structuralFlag.signal)} · ${escapeHtml(r.structuralFlag.source)}</div>` : "";
    const gated = r.gated ? ` <span class="pill locked" title="below the deep-work ADV floor">thin</span>` : "";
    return `
      <tr data-ticker="${escapeHtml(r.ticker)}" style="cursor:pointer;${sunk ? "opacity:0.62;" : ""}">
        <td class="num muted">${r.rank}</td>
        <td><span class="mono" style="font-weight:600;">${escapeHtml(r.ticker)}</span>${sunk ? " ⛔" : ""}
          <div class="muted" style="font-size:11.5px;">${escapeHtml((r.name || "").slice(0, 40))}</div>${flag}</td>
        <td class="muted" style="font-size:12px;"><span style="display:inline-block; max-width:92px; line-height:1.25;">${escapeHtml(r.industry || "—")}</span></td>
        <td>${STATE_BADGE[stateOf(r.ticker)] || ""}</td>
        <td class="num" style="font-weight:600;">${fmtScore(r.score)}</td>
        <td><span class="pill ${sunk ? "unresolved" : "live"}">${escapeHtml(r.depthBand)}</span>${gated}</td>
        ${rawCell(r, "idiosyncrasy")}${rawCell(r, "depth")}${charCell(r)}${multCell(r)}
        <td class="num">${fmtMoney(r.advUsd)}</td>
        <td class="num">${r.marketCap == null ? `<span class="muted">${DASH}</span>` : fmtMoney(r.marketCap)}</td>
      </tr>`;
  }).join("") || `<tr><td colspan="${COLS.length}" class="muted" style="padding:18px;">No rows match the filter.</td></tr>`;

  body.querySelectorAll("tr[data-ticker]").forEach((tr) =>
    tr.addEventListener("click", () => { location.hash = `#/dossier/${tr.dataset.ticker}`; }));
}
