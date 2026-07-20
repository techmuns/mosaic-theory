// THEME ALTITUDE (#/themes/<theme>) — one theme's detail. The metric-card row LEADS with the WATCH
// count (VERDICT · the analyst's actionable re-underwrite set — higher relevance than the scan tiers),
// then the SCAN tiers firm/partial/early (the drill affordance, scoped to this theme). The NONE tier is
// DROPPED — pure inventory; the "surfaced of scanned" subtitle already implies it. Then the watchlist
// inline (short) + this theme's forward cohorts. No full name dump — tap a scan count → the tier altitude.
import { getThemeDriver, getThemeContext } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml } from "../../lib/format.js";

function oneLine(s) {
  s = String(s || "").trim();
  return s.length <= 120 ? s : s.slice(0, 120).replace(/\s+\S*$/, "") + "…";
}

// "What this theme is" — the ratified driver definition (quoted) + the analyst's plain-language
// notes. Analyst-owned in themes/context.json; absent theme → "" (graceful, the page still renders).
function whatSection(cx) {
  if (!cx) return "";
  const ds = cx.driver_summary || {};
  const notes = Array.isArray(cx.analyst_notes) ? cx.analyst_notes : [];
  const quote = ds.quote
    ? `<blockquote class="tc-quote">${escapeHtml(ds.quote)}</blockquote>
       <div class="foot tc-src">— ${escapeHtml(ds.source || "ratified driver definition")}</div>`
    : "";
  const noteLines = notes.length
    ? `<div class="tc-notes">${notes
        .map((n) => `<div class="tc-note">${escapeHtml(n)}</div>`).join("")}</div>`
    : "";
  if (!quote && !noteLines) return "";
  return `<div class="card theme-context" style="margin-bottom:16px;">
      <h3>What this theme is</h3>${quote}${noteLines}
    </div>`;
}

export async function render(root, _ctx, slug) {
  const bc = `<div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span><a href="#/themes">Themes</a><span class="sep">/</span>${escapeHtml(slug)}</div>`;
  root.innerHTML = `${bc}<div class="notice">Loading theme…</div>`;
  const [d, cx] = await Promise.all([getThemeDriver(slug), getThemeContext(slug)]);
  if (!d) {
    root.innerHTML = `${bc}<div class="notice">Theme “${escapeHtml(slug)}” not found. <a href="#/themes">Back to portfolio</a>.</div>`;
    return;
  }

  const t = d.tierShape || {}, ft = d.frozenTiers || {}, f = d.forward || {}, c = f.cohorts || {};
  const wl = d.watchlist || [];
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
  // Lead with WATCH (verdict · analyst's re-underwrite candidates), then the scan tiers. NONE dropped.
  const watchCard = `<div class="card metric verdict-card">
      <h3>watch</h3>
      <div class="value"><span class="tier-count">${fmtInt(wl.length)}</span></div>
      <div class="foot">re-underwrite candidates · the analyst's call</div>
    </div>`;
  const tiers = `<div class="grid cols-4" style="margin-bottom:16px;">
    ${watchCard}
    ${tierCard("firm", ft.firm || 0, "binding / quantified — REAL")}
    ${tierCard("partial", ft.partial || 0, "committed capacity")}
    ${tierCard("early", ft.early || 0, "aspirational")}
  </div>`;

  const wlBlock = `
    <div class="card" style="margin-bottom:16px;">
      <h3>Watchlist · ${fmtInt(wl.length)}</h3>
      ${wl.map((n) => {
        // A recorded verdict SUPERSEDES the freeze trigger — otherwise the row keeps advertising
        // an underwrite that has already been decided. No card → unchanged.
        const c = n.scenarioCard, v = (c && c.verdict) || {};
        const tail = c
          ? `<span class="pill conditional">${escapeHtml(String(v.status || "").toUpperCase())}</span>
             <span class="pill ${c.passFail === "PASS" ? "buy" : "avoid"}">${escapeHtml(c.passFail || "")}</span>
             <b>${typeof c.ratio === "number" ? escapeHtml(c.ratio.toFixed(2)) + ":1" : DASH}</b>
             <span class="muted">vs ${escapeHtml(String(c.bar == null ? 2 : c.bar))}:1 —
             re-underwrite when ${escapeHtml(oneLine((v.reunderwriteTriggers || [])[0] || DASH))}</span>`
          : escapeHtml(oneLine(n.trigger));
        return `<div style="padding:7px 0; border-bottom:1px solid var(--line); font-size:12.5px; line-height:1.5;">
        <b class="mono">${escapeHtml(n.ticker)}</b> <span class="muted">${escapeHtml(n.substructureTag || "")}</span> —
        ${tail}</div>`;
      }).join("") || `<div class="foot">none</div>`}
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

  root.innerHTML = head + whatSection(cx) + tiers + wlBlock + fwd;
}
