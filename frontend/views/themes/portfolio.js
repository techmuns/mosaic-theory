// PORTFOLIO ALTITUDE (#/themes) — the theme-edge landing. The POOLED forward state (0 buys,
// on-watch, power-floor progress, undefined-spread honesty + pending diagnostics) at the top — these
// are cross-theme facts, so they live here, NOT in a per-driver tab. Then ONE ROW PER THEME with the
// tier COUNTS (firm / partial / early / none) — the counts ARE the drill affordance (tap → that
// theme's that-tier names). No individual names on this screen. N themes = N rows, scannable at 20.
import { getThemesIndex } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml } from "../../lib/format.js";

const GRADE_KEY = `<div class="grade-key">
  <span class="gk"><b>firm</b> — binding contract / quantified revenue (REAL)</span>
  <span class="gk"><b>partial</b> — committed capacity, no paying customer yet</span>
  <span class="gk"><b>early</b> — aspirational, a stated-intent mention</span>
  <span class="gk"><b>none</b> — no exposure disclosed</span>
</div>`;

export async function render(root, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading theme-edge portfolio…</div>` });
  const idx = await getThemesIndex();
  if (!idx.drivers.length) {
    root.innerHTML = frame(item, { bodyHtml: `
      <div class="notice">No theme artifacts committed to this deploy yet. Produce them with
      <code>python3 frontend/build.py --themes-src &lt;snapshot dir(s)&gt;</code>.</div>` });
    return;
  }

  const pf = idx.pooledForward || {};
  const pw = pf.powerFloor || {};
  const cd = idx.crossDriver || {};

  // POOLED forward — the cross-theme state, prominent + honest.
  const honest = `
    <div class="card gate-card" style="margin-bottom:14px;">
      <h3 class="g-label">Theme edge · unvalidated research surface</h3>
      <div class="g-spread" style="font-size:32px;">${fmtInt(pf.totalBuys ?? 0)} buys</div>
      <div class="g-status">
        <b>${fmtInt(pf.totalBuys ?? 0)} buys across ${fmtInt(cd.driversFrozen ?? idx.drivers.length)} themes</b> —
        the edge surfaces <b>watchlists, not buys</b> (yet). ${fmtInt(pf.totalWatchlist ?? 0)} names on watch.
      </div>
      <div style="margin-top:13px;">
        <div class="foot" style="margin-bottom:5px;">Power floor · <b>${escapeHtml(pw.label || "")}</b></div>
        <div class="power-bar"><div class="power-fill" style="width:${pw.pct ?? 0}%;"></div></div>
      </div>
    </div>`;

  const pooled = `
    <div class="card" style="border-left:3px solid var(--conditional); margin-bottom:16px;">
      <h3>Pooled forward · buy-dependent spreads UNDEFINED</h3>
      <div class="subtitle muted" style="margin:2px 0 8px;">Zero buys → no buy leg → every buy-dependent
        spread is UNDEFINED and NOT computed. Never <b>0.0</b>.</div>
      <ul class="kv-list" style="margin-bottom:10px;">${(pf.undefinedMeasures || []).map(([m, r]) =>
        `<li><b>${escapeHtml(m)}</b> — <span class="muted">UNDEFINED: ${escapeHtml(r)}</span></li>`).join("")}
      </ul>
      <div class="foot" style="margin-bottom:6px;">Beta-confounded diagnostics — pooled across themes, 0 days forward → pending:</div>
      ${(pf.diagnostics || []).map((d) => `
        <div style="padding:4px 0;"><b>${escapeHtml(d.name)}</b>
          <span class="pill unresolved">${escapeHtml(d.status || "PENDING")}</span>
          <span class="foot"> ${escapeHtml(d.note || "")}</span></div>`).join("")}
      <div class="cite">${escapeHtml(pf.honestyLabel || "")}</div>
    </div>`;

  const drill = (slug, tier, n) => n > 0
    ? `<a class="tier-count" href="#/themes/${escapeHtml(slug)}/${tier}">${fmtInt(n)}</a>`
    : `<span class="tier-count zero">0</span>`;
  const row = (d) => {
    const ft = d.frozenTiers || {}, t = d.tierShape || {};
    return `
      <tr>
        <td><a href="#/themes/${escapeHtml(d.slug)}" style="font-weight:650;">${escapeHtml(d.label)}</a>
          <div class="foot">snapshot ${fmtDate(d.freezeDate)} · ${fmtInt(d.surfacedCount)} surfaced of ${t.universe == null ? DASH : fmtInt(t.universe)} scanned</div></td>
        <td class="num">${drill(d.slug, "firm", ft.firm || 0)}</td>
        <td class="num">${drill(d.slug, "partial", ft.partial || 0)}</td>
        <td class="num">${drill(d.slug, "early", ft.early || 0)}</td>
        <td class="num muted">${t.none == null ? DASH : fmtInt(t.none)}</td>
        <td class="num">${fmtInt(d.watchlistCount)}</td>
        <td class="num">${fmtInt(d.ratifiedCount)}</td>
      </tr>`;
  };

  const table = `
    <table class="data"><thead><tr>
      <th>Theme</th><th class="num">firm</th><th class="num">partial</th><th class="num">early</th>
      <th class="num">none</th><th class="num">watch</th><th class="num">buys</th>
    </tr></thead><tbody>${idx.drivers.map(row).join("")}</tbody></table>
    <div class="foot" style="margin-top:8px;">Tap a theme to drill in · tap a tier count for that tier's names.</div>`;

  root.innerHTML = frame(item, { bodyHtml: honest + pooled + GRADE_KEY + table });
}
