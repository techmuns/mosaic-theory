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
      <input id="ss-q" type="search" placeholder="Filter ticker or name…" autocomplete="off" value=""
        style="flex:1; min-width:200px; padding:8px 11px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
      <span class="muted" style="font-size:12px;">admitted set · sorted A→Z (order-agnostic)</span>
    </div>
    <table class="data"><thead><tr>
      <th>Ticker</th><th>Name</th><th>Band</th><th>G1 · drawdown</th><th>G2 · idiosyncratic</th><th>G3 · multiple</th>
    </tr></thead><tbody id="ss-body"></tbody></table>`;

  root.innerHTML = frame(item, { bodyHtml: cards + controls + refreshBlock() });
  renderRows();
  root.querySelector("#ss-q").addEventListener("input", (e) => { q = e.target.value.toLowerCase(); renderRows(); });
}

function renderRows() {
  const body = document.getElementById("ss-body");
  if (!body) return;
  const rows = q ? ADMITTED.filter((r) => r.ticker.toLowerCase().includes(q) || (r.name || "").toLowerCase().includes(q)) : ADMITTED;
  body.innerHTML = rows.map((r) => `
    <tr>
      <td><a class="mono" style="font-weight:600;" href="#/dossier/${escapeHtml(r.ticker)}">${escapeHtml(r.ticker)}</a></td>
      <td class="muted" style="font-size:12px;">${escapeHtml((r.name || "").slice(0, 42))}</td>
      <td><span class="pill live">${escapeHtml(r.depthBand)}</span></td>
      <td>${escapeHtml(r.depthLabel || "")}</td>
      <td>${escapeHtml(r.idioLabel || "")}</td>
      <td${r.multipleUnknown ? ' class="muted" style="font-style:italic;"' : ""}>${escapeHtml(r.multipleLabel || "")}</td>
    </tr>`).join("") || `<tr><td colspan="6" class="muted" style="padding:18px;">No admitted names match the filter.</td></tr>`;
}
