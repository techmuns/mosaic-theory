// THEME ALTITUDE (#/themes/<theme>) — the ONE coherent read for a theme: what it is (the ratified
// brief), who's in play (tier cards → drill), the watchlist with its re-underwrite triggers and
// FULL underwrite cards (the only full-fidelity render site), the avoid-controls, and the forward
// cohorts. Framed by the shared stage frame (tabs persist on drill-down); a recorded verdict
// SUPERSEDES the freeze trigger — the row never advertises an underwrite already decided.
import { getThemeDriver, getThemeContext, getRadarCandidates, getMonitor } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml, gradeBucket, gradeLabel } from "../../lib/format.js";
import { uwCard } from "../shared/uw-card.js";

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

// resolve this theme to a radar candidate (provenance chip) — explicit theme_route, then slug,
// then case-insensitive label. Mirrors the radar view's resolver; no link is ever fabricated.
function radarChip(cands, slug, label) {
  const c = (cands || []).find((x) =>
    (x.theme_route || "").replace(/^#?\/?themes\//, "") === slug ||
    x.slug === slug ||
    (x.label || "").toLowerCase() === (label || "").toLowerCase());
  if (!c) return "";
  return `<span class="muted"> · on the radar: ${escapeHtml(c.status || "tracked")}
    <a href="#/themes/radar">Radar →</a></span>`;
}

// One watch name, full fidelity: header row → re-underwrite trigger (verdict supersedes freeze) →
// the canonical underwrite card when a record exists → the disposition rationale on demand.
function watchRow(n, marks = {}) {
  const c = n.scenarioCard;
  const trig = c && (c.verdict?.reunderwriteTriggers || []).length
    ? `<ul class="kv-list">${c.verdict.reunderwriteTriggers
        .map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>`
    : escapeHtml(n.trigger || DASH);
  return `
    <div class="wl-row">
      <div class="wl-top">
        <b class="mono">${escapeHtml(n.ticker)}</b>
        <span class="muted" style="font-size:12px;">${escapeHtml(n.substructureTag || "")}</span>
        <span class="gt ${gradeBucket(n.basis)}">${escapeHtml(gradeBucket(n.basis))}</span>
        ${n.edgarUrl ? `<a href="${encodeURI(n.edgarUrl)}" target="_blank" rel="noopener" style="font-size:11px; margin-left:auto;">EDGAR ${escapeHtml(n.accession || "")}</a>` : ""}
      </div>
      <div class="wl-trigger"><span class="k">re-underwrite when</span>${trig}</div>
      ${c ? uwCard(c, { mark: marks[String(n.ticker).toUpperCase()] || null }) : ""}
      ${n.rationale || n.gradeFact ? `<details class="wl-why">
        <summary>why it's on the list</summary>
        <div class="wl-why-body">${n.rationale ? escapeHtml(n.rationale) : ""}${n.gradeFact ? `<div class="cite">${escapeHtml(n.gradeFact)}</div>` : ""}</div>
      </details>` : ""}
    </div>`;
}

function avoidBlock(d) {
  if (!d.avoidControls || !d.avoidControls.length) return "";
  return `
    <div class="card" style="background:var(--surface-2); margin-bottom:16px;">
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
}

export async function render(root, { item, frame }, slug) {
  root.innerHTML = frame(item, {
    title: slug, crumbExtra: `<span class="sep">/</span>${escapeHtml(slug)}`,
    bodyHtml: `<div class="notice">Loading theme…</div>`,
  });
  const [d, cx, cands, mon] = await Promise.all([
    getThemeDriver(slug), getThemeContext(slug),
    getRadarCandidates().then((r) => r.candidates || []).catch(() => []),
    getMonitor().catch(() => null),
  ]);
  // committed monitor marks by ticker — the embedded card's implied-odds line reads the SAME
  // dated mark the dossier page uses, so one name never shows two different spots.
  const marks = {};
  for (const r of (mon && mon.rows) || []) marks[String(r.ticker).toUpperCase()] = r;
  if (!d) {
    root.innerHTML = frame(item, {
      title: slug, crumbExtra: `<span class="sep">/</span>${escapeHtml(slug)}`,
      bodyHtml: `<div class="notice">Theme “${escapeHtml(slug)}” not found. <a href="#/themes">Back to the themes landing</a>.</div>`,
    });
    return;
  }

  const t = d.tierShape || {}, ft = d.frozenTiers || {}, f = d.forward || {}, c = f.cohorts || {};
  const wl = d.watchlist || [];
  const sub = `
    <div class="subtitle muted" style="margin:-6px 0 14px;">snapshot ${fmtDate(d.freezeDate)} ·
      ${fmtInt(d.surfacedCount)} surfaced of ${t.universe == null ? DASH : fmtInt(t.universe)} scanned ·
      ${fmtInt(d.ratifiedCount)} buys${radarChip(cands, d.slug || slug, d.label)}</div>`;

  const tierCard = (tier, n, label) => {
    const drill = n > 0 && tier !== "none";
    const val = drill
      ? `<a class="tier-count" href="#/themes/${escapeHtml(slug)}/${tier}">${fmtInt(n)}</a>`
      : `<span class="tier-count zero">${n == null ? DASH : fmtInt(n)}</span>`;
    return `<div class="card metric"><h3>${tier}</h3><div class="value">${val}</div><div class="foot">${label}</div></div>`;
  };
  // Lead with WATCH (verdict · the analyst's actionable set — a cue, not a link: the full section
  // is directly below), then the scan tiers (the drill affordance). NONE dropped (pure inventory).
  const tiers = `<div class="grid cols-4" style="margin-bottom:16px;">
    <div class="card metric verdict-card">
      <h3>watch</h3>
      <div class="value"><span class="tier-count">${fmtInt(wl.length)}</span></div>
      <div class="foot">re-underwrite candidates · the analyst's call</div>
    </div>
    ${tierCard("firm", ft.firm || 0, "binding / quantified — REAL")}
    ${tierCard("partial", ft.partial || 0, "committed capacity")}
    ${tierCard("early", ft.early || 0, "aspirational")}
  </div>`;

  const wlBlock = `
    <div class="card" style="margin-bottom:16px;">
      <h3>Watchlist · ${fmtInt(wl.length)} <span class="uw-h-sub">re-underwrite on trigger</span></h3>
      ${wl.map((n) => watchRow(n, marks)).join("") || `<div class="foot">none</div>`}
    </div>`;

  const fwd = `
    <div class="card" style="border-left:3px solid var(--conditional);">
      <h3>Forward · snapshot cohorts</h3>
      <div class="subtitle muted" style="margin:2px 0 10px;">Buy-dependent spreads UNDEFINED (0 buys → no
        buy leg); diagnostics beta-confounded, pending forward. Pooled cross-theme state is on the
        <a href="#/themes">themes landing</a>.</div>
      <div style="display:flex; flex-wrap:wrap; gap:8px;">
        <span class="pill unresolved">${fmtInt(c.buy)} buys</span>
        <span class="pill unresolved">NAIVE ${fmtInt(c.naive)}</span>
        <span class="pill unresolved">${fmtInt(c.watchlist)} watchlist</span>
        <span class="pill unresolved">${fmtInt(c.avoidControls)} avoid-controls</span>
        <span class="pill unresolved">${fmtInt(c.realTier)} real-tier</span>
      </div>
      <div class="cite">${escapeHtml(f.honestyLabel || "")}</div>
    </div>`;

  root.innerHTML = frame(item, {
    title: d.label, crumbExtra: `<span class="sep">/</span>${escapeHtml(d.label)}`,
    bodyHtml: sub + whatSection(cx) + tiers + wlBlock + avoidBlock(d) + fwd,
  });
}
