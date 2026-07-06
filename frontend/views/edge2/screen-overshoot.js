// SCREEN · OVERSHOOT — THIS edge's admitted SET: the names that passed G1·G2·G3, with the
// screening timestamp. Distinct from the ranker (which is cross-edge priority order); here the
// question is "what passed this filter." Gate logic folds into a collapsible header. Read-only.
import { getScreenAdmitted } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, escapeHtml } from "../../lib/format.js";
import { refreshBlock } from "../../lib/ui.js";

let ADMITTED = null;
let q = "";

export async function render(root, _params, { item, frame }) {
  q = "";
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading admitted set…</div>` });
  const s = await getScreenAdmitted();
  ADMITTED = s.names;

  const cards = `
    <div class="grid cols-3" style="margin-bottom:16px;">
      <div class="card metric"><h3>Admitted (Overshoot)</h3><div class="value">${fmtInt(s.count)}</div>
        <div class="foot">passed G1·G2·G3 · screened ${fmtDate(s.asOf)}</div></div>
      <div class="card metric"><h3>This view</h3><div class="value" style="font-size:19px;">the admitted set</div>
        <div class="foot">what passed THIS edge's filter — not the ranker's priority order</div></div>
      <div class="card metric"><h3>Disposition</h3><div class="value" style="font-size:19px;">AND-gated</div>
        <div class="foot">all three gates; UNKNOWN inputs defer, never impute</div></div>
    </div>
    <details class="card" style="margin-bottom:16px;">
      <summary style="cursor:pointer; font-weight:600; font-size:13px;">Gate logic — G1 · G2 · G3 <span class="muted" style="font-weight:400;">(click to expand)</span></summary>
      <ul class="kv-list" style="margin-top:12px;">
        ${s.gates.map((g) => `<li><b>${escapeHtml(g.id)} · ${escapeHtml(g.name)}</b> — ${escapeHtml(g.rule)}</li>`).join("")}
      </ul>
      <div class="subtitle muted" style="margin-top:6px;">It filters; it does not rank or judge. The structural-demote channel is a <a href="#/ranker">ranker</a> overlay, not a screen gate — every admitted name appears here regardless.</div>
    </details>`;

  const controls = `
    <div style="display:flex; gap:14px; align-items:center; margin-bottom:12px;">
      <input id="ss-q" type="search" placeholder="Filter ticker, name, or industry…" autocomplete="off" value=""
        style="flex:1; min-width:200px; padding:8px 11px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
      <span class="muted" style="font-size:12px;">admitted set · sorted A→Z (order-agnostic)</span>
    </div>
    <table class="data"><thead><tr>
      <th>Ticker</th><th>Name</th><th>Industry</th><th>Band</th><th>G1 · drawdown</th><th>G2 · idiosyncratic</th><th>G3 · multiple</th>
    </tr></thead><tbody id="ss-body"></tbody></table>`;

  root.innerHTML = frame(item, { bodyHtml: cards + clusterRollup(ADMITTED) + controls + refreshBlock() });
  renderRows();
  root.querySelector("#ss-q").addEventListener("input", (e) => { q = e.target.value.toLowerCase(); renderRows(); });
}

function renderRows() {
  const body = document.getElementById("ss-body");
  if (!body) return;
  const rows = q ? ADMITTED.filter((r) => r.ticker.toLowerCase().includes(q) || (r.name || "").toLowerCase().includes(q) || (r.sector || "").toLowerCase().includes(q) || (r.industry || "").toLowerCase().includes(q)) : ADMITTED;
  body.innerHTML = rows.map((r) => `
    <tr>
      <td><a class="mono" style="font-weight:600;" href="#/dossier/${escapeHtml(r.ticker)}">${escapeHtml(r.ticker)}</a></td>
      <td class="muted" style="font-size:12px;">${escapeHtml((r.name || "").slice(0, 42))}</td>
      <td class="muted" style="font-size:12px;"><span style="display:inline-block; max-width:104px; line-height:1.25;">${escapeHtml(r.industry || "—")}</span></td>
      <td><span class="pill live">${escapeHtml(r.depthBand)}</span></td>
      <td>${escapeHtml(r.depthLabel || "")}</td>
      <td>${escapeHtml(r.idioLabel || "")}</td>
      <td${r.multipleUnknown ? ' class="muted" style="font-style:italic;"' : ""}>${escapeHtml(r.multipleLabel || "")}</td>
    </tr>`).join("") || `<tr><td colspan="7" class="muted" style="padding:18px;">No admitted names match the filter.</td></tr>`;
}

// CROSS-SECTIONAL CLUSTERS — a selection-time, TWO-LEVEL roll-up of the admitted set: coarse SEC-SIC
// sector (the scannable headline) → its finer sub-industries (what the sector actually splits into).
// Its job is de-confounding + concentration visibility: G2 strips MARKET beta (name vs IWM) but NOT
// sector, so a name that fell WITH its group still lands here looking idiosyncratic. A large cluster
// asks "did the GROUP fall, not the name?" — and the sub-industries tell you if it's ONE shared
// driver or several. Read by the human, gating/weighting/sorting NOTHING. SIC is a business
// classification, NOT a peer cohort, NOT a sector-adjusted control, and NOT a driver/theme (that is
// the theme edge). 'Unknown' (blank/unmapped SIC) is shown explicitly — coverage stays honest.
function clusterRollup(names) {
  if (!names || !names.length) return "";
  const total = names.length;
  const pct = (n) => Math.round((n / total) * 100);
  // group by sector → { total, industries:Map }
  const bySector = new Map();
  for (const n of names) {
    const sec = n.sector || "Unknown";
    const ind = n.industry || "Unknown";
    if (!bySector.has(sec)) bySector.set(sec, { total: 0, ind: new Map() });
    const g = bySector.get(sec);
    g.total += 1;
    g.ind.set(ind, (g.ind.get(ind) || 0) + 1);
  }
  const byCount = (a, b) => (a[0] === "Unknown") - (b[0] === "Unknown") || b[1] - a[1] || a[0].localeCompare(b[0]);
  const sectors = [...bySector.entries()].sort((a, b) =>
    (a[0] === "Unknown") - (b[0] === "Unknown") || b[1].total - a[1].total || a[0].localeCompare(b[0]));
  const rows = sectors.map(([sec, g]) => {
    const chips = [...g.ind.entries()].sort(byCount).map(([ind, c]) => {
      // the coarse-fallback bucket (industry == sector) reads as "the rest"; don't double up "Other"/"Unknown"
      const label = ind !== sec ? ind : (sec === "Other" || sec === "Unknown" ? sec : `Other ${sec}`);
      const cls = ind === "Unknown" ? "chip" : "chip accent";
      return `<span class="${cls}" style="font-size:11.5px; padding:3px 9px;">${escapeHtml(label)} <b>${fmtInt(c)}</b></span>`;
    }).join("");
    return `<div style="display:flex; gap:14px; align-items:baseline; padding:8px 0; border-top:1px solid var(--line);">
      <div style="flex:none; width:150px; font-size:13px;"><b>${escapeHtml(sec)}</b> <span class="muted">${fmtInt(g.total)} · ${pct(g.total)}%</span></div>
      <div class="chips" style="flex:1;">${chips}</div>
    </div>`;
  }).join("");
  const top = sectors.find(([s]) => s !== "Unknown") || sectors[0];
  const lead = top
    ? `Largest sector: <b>${escapeHtml(top[0])}</b> — ${fmtInt(top[1].total)} of ${fmtInt(total)} (${pct(top[1].total)}%); its sub-industries below show whether that is one shared driver or several.`
    : "";
  return `
    <div class="card" style="margin-bottom:16px;">
      <h3>Cross-sectional clusters <span class="muted" style="font-weight:400; text-transform:none; letter-spacing:0;">— sector → sub-industry, over the ${fmtInt(total)} admitted</span></h3>
      <div class="subtitle muted" style="margin:6px 0 9px;">Business classification (SEC SIC) — <b>not a peer cohort, not a sector-adjusted control</b>. G2 strips <i>market</i> beta, not sector, so a large cluster asks: did the <b>group</b> fall, not the name? Assemble / inform — it gates, weights, and sorts nothing.</div>
      ${lead ? `<div style="font-size:13px; margin-bottom:2px;">${lead}</div>` : ""}
      ${rows}
    </div>`;
}
