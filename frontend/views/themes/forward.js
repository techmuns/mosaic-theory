// FORWARD-TRACK (#/themes/forward) — the validation-gate analogue, per driver: the frozen cohorts
// (empty BUY / NAIVE / watchlist), the RATIFIED-dependent spreads shown UNDEFINED-with-reason (NEVER
// 0.0), the two beta-confounded diagnostics PENDING (0 days forward), the verbatim honesty label, and
// the power-floor note. It must NOT oversell — this is an unvalidated forward track, not an edge.
import { getThemesIndex, getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, escapeHtml } from "../../lib/format.js";

export async function render(root, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading forward-track…</div>` });
  const idx = await getThemesIndex();
  if (!idx.drivers.length) {
    root.innerHTML = frame(item, { bodyHtml: `<div class="notice">No theme artifacts committed to this deploy yet.</div>` });
    return;
  }
  const drivers = await Promise.all(idx.drivers.map((d) => getThemeDriver(d.slug)));

  const section = (meta, d) => {
    const f = d.forward || {};
    const c = f.cohorts || {};
    const honesty = `<div class="banner-research" style="background:#fcfaf2; border-color:#ecdcae; color:#79571a;">
      ${escapeHtml(f.honestyLabel || "")}</div>`;
    const cohorts = `
      <div class="grid cols-3" style="margin-bottom:14px;">
        <div class="card metric"><h3>BUY · ratified</h3><div class="value">${fmtInt(c.buy)}</div>
          <div class="foot">empty by design — 0 RATIFIED</div></div>
        <div class="card metric"><h3>NAIVE · equal-weight</h3><div class="value">${fmtInt(c.naive)}</div>
          <div class="foot">the hold-none control basket</div></div>
        <div class="card metric"><h3>Watchlist</h3><div class="value">${fmtInt(c.watchlist)}</div>
          <div class="foot">${fmtInt(c.avoidControls)} avoid-controls · ${fmtInt(c.realTier)} real-tier</div></div>
      </div>`;
    const undef = `
      <div class="card" style="border-left:3px solid var(--conditional); margin-bottom:12px;">
        <h3>RATIFIED-dependent spreads · UNDEFINED</h3>
        <div class="subtitle muted" style="margin:2px 0 10px;">Zero RATIFIED → no BUY leg → every
          RATIFIED-dependent spread is UNDEFINED and NOT computed. Never <b>0.0</b> — a fabricated
          number is the exact dishonesty this fund guards against.</div>
        <ul class="kv-list">${(f.undefinedMeasures || []).map(([m, r]) =>
          `<li><b>${escapeHtml(m)}</b> — <span class="muted">UNDEFINED: ${escapeHtml(r)}</span></li>`).join("")}
        </ul>
      </div>`;
    const diags = `
      <div class="card" style="margin-bottom:12px;">
        <h3>Beta-confounded diagnostics · PENDING</h3>
        <div class="subtitle muted" style="margin:2px 0 8px;">NOT the edge measure — beta-confounded
          reads that accrue forward. 0 days forward from the freeze (${fmtDate(meta.freezeDate)}) → pending.</div>
        ${(f.diagnostics || []).map((dg) => `
          <div style="padding:10px 0; border-bottom:1px solid var(--line);">
            <div><b>${escapeHtml(dg.name)}</b> <span class="pill unresolved">${escapeHtml(dg.status || "PENDING")}</span></div>
            <div class="foot" style="margin-top:4px;">${escapeHtml(dg.note || "")}</div>
            <div class="cite">${escapeHtml(dg.confound || "")}</div>
          </div>`).join("")}
      </div>`;
    const power = `<div class="foot" style="margin-top:6px;"><b>Power floor:</b> ${escapeHtml(f.powerNote || "")}</div>`;
    return `
      <div style="margin-bottom:28px;">
        <div style="font-size:16px; font-weight:650; margin:0 0 10px; padding-bottom:6px; border-bottom:1px solid var(--line);">
          ${escapeHtml(meta.label)} <span class="muted" style="font-weight:400; font-size:13px;">· frozen ${fmtDate(meta.freezeDate)}</span></div>
        ${honesty}${cohorts}${undef}${diags}${power}
      </div>`;
  };

  const body = idx.drivers.map((meta, i) => (drivers[i] ? section(meta, drivers[i]) : "")).join("");
  root.innerHTML = frame(item, { bodyHtml: body });
}
