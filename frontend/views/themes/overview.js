// THEMES OVERVIEW (#/themes) — the theme-edge fund status. Per driver: a card with freeze date,
// tier shape, surfaced / frozen / RATIFIED / watchlist counts. Read-only; the honest 0-RATIFIED
// framing is prominent by design — the edge surfaces WATCHLISTS, not buys (yet).
import { getThemesIndex } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml } from "../../lib/format.js";

export async function render(root, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading theme-edge status…</div>` });
  const idx = await getThemesIndex();

  if (!idx.drivers.length) {
    root.innerHTML = frame(item, { bodyHtml: `
      <div class="notice">No theme artifacts committed to this deploy yet. Produce them with
      <code>python3 frontend/build.py --themes-src &lt;freeze dir(s)&gt;</code>, which writes the
      committed <span class="mono">frontend/themes/*.json</span> the theme views read.</div>` });
    return;
  }

  const cd = idx.crossDriver || {};
  const totalRat = cd.totalRatified ?? 0;
  const totalWl = cd.totalWatchlist ?? 0;
  const nDrivers = cd.driversFrozen ?? idx.drivers.length;

  // PROMINENT honest header — the theme edge is an unvalidated research surface, not a validated edge.
  const honest = `
    <div class="card gate-card" style="grid-column:1/-1; margin-bottom:16px;">
      <h3 class="g-label">Theme edge · unvalidated research surface</h3>
      <div class="g-spread" style="font-size:32px;">${totalRat} RATIFIED</div>
      <div class="g-status">
        <b>${totalRat} RATIFIED across ${nDrivers} theme${nDrivers !== 1 ? "s" : ""}</b> — the edge
        surfaces <b>watchlists, not buys</b> (yet). ${fmtInt(totalWl)} watchlist name${totalWl !== 1 ? "s" : ""}
        to re-underwrite when a trigger fires.
      </div>
      <div class="g-def">${escapeHtml(cd.line || "")}</div>
    </div>`;

  const tierPills = (t) => {
    const real = (t.binding || 0) + (t.quantified || 0);
    return `
      <span class="pill buy" title="binding + quantified">${fmtInt(real)} REAL</span>
      <span class="pill unresolved">${fmtInt(t.committed)} committed</span>
      <span class="pill conditional">${fmtInt(t.aspirational)} aspirational</span>
      <span class="pill locked">${t.none == null ? DASH : fmtInt(t.none)} none</span>`;
  };

  const card = (d) => {
    const t = d.tierShape || {};
    const frozenNote = d.frozenCount != null && d.frozenCount !== d.surfacedCount
      ? ` · <span title="the dispositioned / frozen tier">${fmtInt(d.frozenCount)} frozen tier</span>` : "";
    return `
      <div class="card">
        <h3>${escapeHtml(d.label)}</h3>
        <div class="foot" style="margin:2px 0 10px;">frozen ${fmtDate(d.freezeDate)} ·
          ${fmtInt(d.surfacedCount)} surfaced${frozenNote} ·
          of ${t.universe == null ? DASH : fmtInt(t.universe)} scanned</div>
        <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px;">${tierPills(t)}</div>
        <div style="display:flex; gap:20px; font-size:13px;">
          <span><b class="mono">${fmtInt(d.ratifiedCount)}</b> ratified</span>
          <span><b class="mono">${fmtInt(d.watchlistCount)}</b> watchlist</span>
        </div>
        <div class="foot" style="margin-top:12px;">
          <a href="#/themes/scan">Scan · tiers</a> ·
          <a href="#/themes/watchlist">Watchlist · triggers</a> ·
          <a href="#/themes/forward">Forward-track</a>
        </div>
      </div>`;
  };

  const cols = idx.drivers.length >= 2 ? "cols-2" : "";
  root.innerHTML = frame(item, {
    bodyHtml: honest + `<div class="grid ${cols}">${idx.drivers.map(card).join("")}</div>`,
  });
}
