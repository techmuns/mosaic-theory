// WATCHLIST (#/themes/watchlist) — a FLAT cross-theme checklist (NOT a drill-down; the standing
// monitoring surface, naturally bounded). Each name is a COLLAPSED row LED BY ITS VERBATIM TRIGGER
// (ticker · category · the re-underwrite trigger); the disposition rationale is behind a "why it's on
// the list" expand (collapsed by default) — the same trigger-led / rationale-on-demand principle as
// the surfaced-names row collapse. Per-theme sections (collapsible); avoid-controls a separate section.
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
    <b>The manual-monitoring surface.</b> A flat cross-theme checklist — the names to re-underwrite the
    instant a trigger fires. <b>Read-only</b>: nothing here fires automatically (the backend delta-scan
    that watches filings is a later build). Each row is led by its verbatim trigger; the rationale is
    behind “why it's on the list”.</div>`;

  const wlRow = (n) => `
    <div class="wl-row">
      <div class="wl-top">
        <b class="mono">${escapeHtml(n.ticker)}</b>
        <span class="muted" style="font-size:12px;">${escapeHtml(n.substructureTag || "")}</span>
        <span class="pill unresolved" style="font-size:10px;">${escapeHtml(gradeLabel(n.basis))}</span>
        ${n.edgarUrl ? `<a href="${encodeURI(n.edgarUrl)}" target="_blank" rel="noopener" style="font-size:11px; margin-left:auto;">EDGAR ${escapeHtml(n.accession || "")}</a>` : ""}
      </div>
      <div class="wl-trigger"><span class="k">re-underwrite when</span>${escapeHtml(n.trigger || "—")}</div>
      ${n.rationale || n.gradeFact ? `<details class="wl-why">
        <summary>why it's on the list</summary>
        <div class="wl-why-body">${n.rationale ? escapeHtml(n.rationale) : ""}${n.gradeFact ? `<div class="cite">${escapeHtml(n.gradeFact)}</div>` : ""}</div>
      </details>` : ""}
    </div>`;

  const avoidBlock = (d) => {
    if (!d.avoidControls || !d.avoidControls.length) return "";
    return `
      <div class="card" style="background:var(--surface-2); margin-top:10px;">
        <h3>Avoid-controls · ${fmtInt(d.avoidControls.length)}</h3>
        <div class="subtitle muted" style="margin:2px 0 10px;">Highest-value near-misses inside the
          PASSED leg — a labeled CONTROL cohort, NOT the watchlist. Not a re-underwrite candidate.</div>
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
      <details class="wl-section" open>
        <summary><b>${escapeHtml(meta.label)}</b> <span class="muted">· ${fmtInt(wl.length)} watchlist</span></summary>
        <div class="wl-section-body">
          ${wl.length ? wl.map(wlRow).join("") : `<div class="foot">none</div>`}
          ${avoidBlock(d)}
        </div>
      </details>`;
  }).join("");

  root.innerHTML = frame(item, { bodyHtml: intro + sections });
}
