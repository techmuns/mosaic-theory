// WATCHLIST · TRIGGERS (#/themes/watchlist) — THE actionable surface: the watchlist names across
// both drivers, each with its VERBATIM re-underwrite trigger + disposition rationale, plus the
// labeled AVOID-CONTROLS cohort. This is the manual-monitoring surface until the delta-scan
// automation lands (a later build). Read-only — nothing here fires.
import { getThemesIndex, getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, escapeHtml } from "../../lib/format.js";

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
    here fires automatically (the backend delta-scan that watches filings is a later build). Each name
    carries its verbatim re-underwrite trigger and the disposition rationale.</div>`;

  const nameBlock = (n) => `
    <div class="card" style="margin-bottom:12px;">
      <div style="display:flex; gap:10px; align-items:baseline; flex-wrap:wrap;">
        <span class="mono" style="font-weight:650; font-size:15px;">${escapeHtml(n.ticker)}</span>
        <span class="pill unresolved">${escapeHtml(n.substructureTag || "")}</span>
        <span class="muted" style="font-size:12px;">${escapeHtml(n.grade || "")}</span>
        ${n.edgarUrl ? `<a href="${encodeURI(n.edgarUrl)}" target="_blank" rel="noopener"
          style="font-size:11.5px; margin-left:auto;">EDGAR ${escapeHtml(n.accession || "")}</a>` : ""}
      </div>
      <div style="margin-top:10px; background:var(--conditional-bg); border:1px solid #ecdcae;
        border-left:3px solid var(--conditional); border-radius:var(--r); padding:11px 14px; font-size:12.5px; line-height:1.55;">
        <span style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink-3); display:block; margin-bottom:4px;">Re-underwrite trigger · verbatim</span>
        ${escapeHtml(n.trigger || "—")}
      </div>
      ${n.rationale ? `<div style="margin-top:8px; font-size:12.5px; color:var(--ink-2); line-height:1.5;">
        <span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em;">Disposition rationale · </span>${escapeHtml(n.rationale)}</div>` : ""}
      ${n.gradeFact ? `<div class="cite">${escapeHtml(n.gradeFact)}</div>` : ""}
    </div>`;

  const avoidBlock = (d) => {
    if (!d.avoidControls || !d.avoidControls.length) return "";
    return `
      <div class="card" style="background:var(--surface-2); margin-top:8px;">
        <h3>Avoid-controls · ${fmtInt(d.avoidControls.length)}</h3>
        <div class="subtitle muted" style="margin:2px 0 10px;">Highest-value near-misses inside the PASSED
          leg — a labeled CONTROL cohort, NOT the watchlist. Tracks whether the human's PASS on the
          strongest almost-buys held up forward; not a re-underwrite candidate.</div>
        <table class="data"><thead><tr><th>Ticker</th><th>Category</th><th>Grade</th><th>Rationale</th></tr></thead>
        <tbody>${d.avoidControls.map((a) => `
          <tr><td class="mono" style="font-weight:600;">${escapeHtml(a.ticker)}</td>
            <td class="muted" style="font-size:12px; white-space:nowrap;">${escapeHtml(a.substructureTag || "")}</td>
            <td style="font-size:12px;">${escapeHtml(a.grade || "")}</td>
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
