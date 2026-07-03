// WATCHLIST (#/themes/watchlist) — THE actionable surface: watchlist names grouped by theme, each
// card LED by its verbatim re-underwrite trigger (the actionable part), with the disposition
// rationale secondary/collapsible. The labeled AVOID-controls cohort is a separate section. The
// manual-monitoring surface until the delta-scan automation lands — read-only, nothing fires.
import { getThemesIndex, getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, escapeHtml, gradeLabel } from "../../lib/format.js";

export async function render(root, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading watchlist…</div>` });
  const idx = await getThemesIndex();
  if (!idx.drivers.length) {
    root.innerHTML = frame(item, { bodyHtml: `<div class="notice">No theme artifacts committed to this deploy yet.</div>` });
    return;
  }
  const drivers = await Promise.all(idx.drivers.map((d) => getThemeDriver(d.slug)));

  const intro = `<div class="banner-research">
    <b>The manual-monitoring surface.</b> The names to re-underwrite the instant a trigger fires —
    genuine tailwind-side exposure that failed only on price / materiality. <b>Read-only</b>: nothing
    here fires automatically (the backend delta-scan that watches filings is a later build).</div>`;

  // each card is LED by the verbatim trigger; the rationale is collapsible below.
  const nameBlock = (n) => `
    <div class="card" style="margin-bottom:12px;">
      <div style="display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; margin-bottom:9px;">
        <span class="mono" style="font-weight:650; font-size:15px;">${escapeHtml(n.ticker)}</span>
        <span class="pill unresolved">${escapeHtml(gradeLabel(n.basis))}</span>
        <span class="muted" style="font-size:12px;">${escapeHtml(n.substructureTag || "")}</span>
        ${n.edgarUrl ? `<a href="${encodeURI(n.edgarUrl)}" target="_blank" rel="noopener"
          style="font-size:11.5px; margin-left:auto;">EDGAR ${escapeHtml(n.accession || "")}</a>` : ""}
      </div>
      <div style="background:var(--conditional-bg); border:1px solid #ecdcae; border-left:3px solid var(--conditional);
        border-radius:var(--r); padding:12px 15px; font-size:13.5px; line-height:1.55; color:#5c451a;">
        <span style="display:block; font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:#9a7a2e; font-weight:600; margin-bottom:5px;">Re-underwrite when</span>
        ${escapeHtml(n.trigger || "—")}
      </div>
      ${n.rationale || n.gradeFact ? `<details style="margin-top:9px;">
        <summary style="cursor:pointer; font-size:12px; color:var(--ink-3);">Why it's on the watchlist — disposition rationale</summary>
        <div style="margin-top:7px; font-size:12.5px; color:var(--ink-2); line-height:1.5;">
          ${n.rationale ? escapeHtml(n.rationale) : ""}${n.gradeFact ? `<div class="cite">${escapeHtml(n.gradeFact)}</div>` : ""}
        </div></details>` : ""}
    </div>`;

  const avoidBlock = (d) => {
    if (!d.avoidControls || !d.avoidControls.length) return "";
    return `
      <div class="card" style="background:var(--surface-2); margin-top:8px;">
        <h3>Avoid-controls · ${fmtInt(d.avoidControls.length)}</h3>
        <div class="subtitle muted" style="margin:2px 0 10px;">Highest-value near-misses inside the
          PASSED leg — a labeled CONTROL cohort, NOT the watchlist. Tracks whether the human's PASS on
          the strongest almost-buys held up forward; not a re-underwrite candidate.</div>
        <table class="data"><thead><tr><th>Ticker</th><th>Category</th><th>Grade</th><th>Rationale</th></tr></thead>
        <tbody>${d.avoidControls.map((a) => `
          <tr><td class="mono" style="font-weight:600;">${escapeHtml(a.ticker)}</td>
            <td class="muted" style="font-size:12px; white-space:nowrap;">${escapeHtml(a.substructureTag || "")}</td>
            <td style="font-size:12px;">${escapeHtml(gradeLabel(a.basis))}</td>
            <td style="font-size:12px;">${escapeHtml(a.rationale || "")}</td></tr>`).join("")}
        </tbody></table>
      </div>`;
  };

  const sections = idx.drivers.map((meta, i) => {
    const d = drivers[i];
    if (!d) return "";
    const wl = d.watchlist || [];
    return `
      <div style="margin-bottom:26px;">
        <div style="font-size:16px; font-weight:650; margin:0 0 10px; padding-bottom:6px; border-bottom:1px solid var(--line);">
          ${escapeHtml(meta.label)} <span class="muted" style="font-weight:400; font-size:13px;">· ${fmtInt(wl.length)} watchlist</span></div>
        ${wl.length ? wl.map(nameBlock).join("") : `<div class="notice">No watchlist names for this driver.</div>`}
        ${avoidBlock(d)}
      </div>`;
  }).join("");

  root.innerHTML = frame(item, { bodyHtml: intro + sections });
}
