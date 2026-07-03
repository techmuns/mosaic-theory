// THEME ALTITUDE (#/themes/<theme>) — one theme's detail: its tier counts (again the drill
// affordance, scoped to this theme), its watchlist inline (short), and its per-theme forward detail
// (this theme's snapshot cohorts). Still NO full name dump — the early/partial names are counts with
// a "view" affordance (tap the count → the tier altitude). Self-rendered breadcrumb + back (below the
// top tabs).
import { getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml } from "../../lib/format.js";

function oneLine(s) {
  s = String(s || "").trim();
  return s.length <= 120 ? s : s.slice(0, 120).replace(/\s+\S*$/, "") + "…";
}

export async function render(root, _ctx, slug) {
  const bc = `<div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span><a href="#/themes">Themes</a><span class="sep">/</span>${escapeHtml(slug)}</div>`;
  root.innerHTML = `${bc}<div class="notice">Loading theme…</div>`;
  const d = await getThemeDriver(slug);
  if (!d) {
    root.innerHTML = `${bc}<div class="notice">Theme “${escapeHtml(slug)}” not found. <a href="#/themes">Back to portfolio</a>.</div>`;
    return;
  }

  const t = d.tierShape || {}, ft = d.frozenTiers || {}, f = d.forward || {}, c = f.cohorts || {};
  const head = `
    <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span><a href="#/themes">Themes</a><span class="sep">/</span>${escapeHtml(d.label)}</div>
    <div class="header-block">
      <h1 class="page-h">${escapeHtml(d.label)}</h1>
      <div class="subtitle muted">snapshot ${fmtDate(d.freezeDate)} · ${fmtInt(d.surfacedCount)} surfaced of ${t.universe == null ? DASH : fmtInt(t.universe)} scanned · ${fmtInt(d.ratifiedCount)} buys</div>
    </div>`;

  const tierCard = (tier, n, label) => {
    const drill = n > 0 && tier !== "none";
    const val = drill
      ? `<a class="tier-count" href="#/themes/${escapeHtml(slug)}/${tier}">${fmtInt(n)}</a>`
      : `<span class="tier-count zero">${n == null ? DASH : fmtInt(n)}</span>`;
    return `<div class="card metric"><h3>${tier}</h3><div class="value">${val}</div><div class="foot">${label}</div></div>`;
  };
  const tiers = `<div class="grid cols-4" style="margin-bottom:16px;">
    ${tierCard("firm", ft.firm || 0, "binding / quantified — REAL")}
    ${tierCard("partial", ft.partial || 0, "committed capacity")}
    ${tierCard("early", ft.early || 0, "aspirational")}
    ${tierCard("none", t.none, "no exposure · not in snapshot")}
  </div>`;

  const wl = d.watchlist || [];
  const wlBlock = `
    <div class="card" style="margin-bottom:16px;">
      <h3>Watchlist · ${fmtInt(wl.length)}</h3>
      ${wl.map((n) => `<div style="padding:7px 0; border-bottom:1px solid var(--line); font-size:12.5px; line-height:1.5;">
        <b class="mono">${escapeHtml(n.ticker)}</b> <span class="muted">${escapeHtml(n.substructureTag || "")}</span> —
        ${escapeHtml(oneLine(n.trigger))}</div>`).join("") || `<div class="foot">none</div>`}
      <div class="foot" style="margin-top:9px;"><a href="#/themes/watchlist">Full watchlist →</a></div>
    </div>`;

  const fwd = `
    <div class="card" style="border-left:3px solid var(--conditional);">
      <h3>Forward · snapshot cohorts</h3>
      <div class="subtitle muted" style="margin:2px 0 10px;">Buy-dependent spreads UNDEFINED (0 buys → no
        buy leg); diagnostics beta-confounded, pending forward. Pooled cross-theme state is on the
        <a href="#/themes">portfolio</a>.</div>
      <div style="display:flex; flex-wrap:wrap; gap:8px;">
        <span class="pill unresolved">${fmtInt(c.buy)} buys</span>
        <span class="pill unresolved">NAIVE ${fmtInt(c.naive)}</span>
        <span class="pill unresolved">${fmtInt(c.watchlist)} watchlist</span>
        <span class="pill unresolved">${fmtInt(c.avoidControls)} avoid-controls</span>
        <span class="pill unresolved">${fmtInt(c.realTier)} real-tier</span>
      </div>
      <div class="cite">${escapeHtml(f.honestyLabel || "")}</div>
    </div>`;

  root.innerHTML = head + tiers + wlBlock + fwd;
}
