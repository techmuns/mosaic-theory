// THEME ALTITUDE (#/themes/<theme>) — the ONE coherent read for a theme: what it is (the ratified
// brief), who's in play (tier cards → drill), the watchlist with its re-underwrite triggers and
// FULL underwrite cards (the only full-fidelity render site), the avoid-controls, and the forward
// cohorts. Framed by the shared stage frame (tabs persist on drill-down); a recorded verdict
// SUPERSEDES the freeze trigger — the row never advertises an underwrite already decided.
import { getThemeDriver, getThemeContext, getRadarCandidates, getMonitor, getThemeThesis, getThemeEconomics } from "../../lib/snapshots.js";
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

// resolve this theme to its radar candidate — explicit theme_route, then slug, then
// case-insensitive label. Mirrors the radar view's resolver; no link is ever fabricated. ONE
// finder for both consumers (the provenance chip and the thesis card's priced line), so the two
// can never resolve the same theme to different candidates.
function findRadar(cands, slug, label) {
  return (cands || []).find((x) =>
    (x.theme_route || "").replace(/^#?\/?themes\//, "") === slug ||
    x.slug === slug ||
    (x.label || "").toLowerCase() === (label || "").toLowerCase()) || null;
}

function radarChip(cands, slug, label) {
  const c = findRadar(cands, slug, label);
  if (!c) return "";
  return `<span class="muted"> · on the radar: ${escapeHtml(c.status || "tracked")}
    <a href="#/themes/radar">Radar →</a></span>`;
}

// THE THESIS CARD (brief Item 1) — the operator's declared record of WHY this driver is a bet.
// The vintage LEADS the card (stamp-position rule: read after the fields, it doesn't work);
// mechanism is a grouping chip (theme-tier panel routing later — the PanelSpec plan); the
// mistake/null pair renders WITH the committed radar priced read, so the claimed mistake and
// "has the price already moved" sit on one screen. Falsifier deadline FLAGS are the monitor's
// job (Item 2), not this card's — it lists the falsifiers; it never adjudicates them.
// Absent card → the loud stamp (ruling R2): absence must never look like passage.
function thesisSection(card, cands, slug, label) {
  if (!card) {
    return `<div class="card" style="margin-bottom:16px;">
      <h3>Theme thesis</h3>
      <span class="thesis-unstated mono">THESIS UNSTATED</span>
      <div class="foot" style="margin-top:8px;">No thesis card declared for this driver. New
        Stage-4 freezes are gated until one exists —
        <span class="mono">vinci theme-thesis declare</span>.</div>
    </div>`;
  }
  const trig = (t) => `<li>${escapeHtml(t.trigger)} — <b>due ${escapeHtml(t.deadline)}</b>${
    t.basis ? ` <span class="muted">· ${escapeHtml(t.basis)}</span>` : ""}</li>`;
  const c = findRadar(cands, slug, label);
  const priced = c
    ? `${escapeHtml(c.px12m || c.status || "on the radar")}${
        c.map && c.map.basis ? ` <span class="muted">· ${escapeHtml(c.map.basis)}</span>` : ""
      } <a href="#/themes/radar">Radar →</a>`
    : `<span class="muted">no committed radar read for this theme — the claim has no priced
       companion on file</span>`;
  return `<div class="card theme-thesis" style="margin-bottom:16px;">
      <div class="tt-vintage mono">THEME THESIS CARD · declared ${fmtDate(card.declared_date)} ·
        <span class="pill locked">${escapeHtml(card.mechanism || "")}</span></div>
      <div class="fact"><span class="fact-label">market mistake</span>
        <span class="fact-val">${escapeHtml(card.market_mistake || "")}</span></div>
      <div class="fact"><span class="fact-label">null thesis</span>
        <span class="fact-val">${escapeHtml(card.null_thesis || "")}</span></div>
      <div class="fact"><span class="fact-label">priced read (radar)</span>
        <span class="fact-val">${priced}</span></div>
      <div class="fact"><span class="fact-label">first confirming</span>
        <span class="fact-val">${escapeHtml(card.first_confirming?.trigger || "")} —
          <b>due ${escapeHtml(card.first_confirming?.deadline || "")}</b></span></div>
      <div class="fact"><span class="fact-label">falsifiers</span>
        <span class="fact-val"><ul class="kv-list" style="margin:0;">${
          (card.falsifiers || []).map(trig).join("")}</ul></span></div>
      ${card.note ? `<div class="cite">${escapeHtml(card.note)}</div>` : ""}
    </div>`;
}

// THE ECONOMICS ROLL-UP (brief Item 4, ruling R5) — inform-only, per-member, NO COMPOSITE: it
// assembles the name-level economics the repo already computes (ladder tiers, eligibility,
// ev_gap WITH its vintages) and concludes nothing. Sparse coverage is the finding, printed as
// such. A member without a record is a stated "no underwrite", never a blank; an unstamped
// (pre-ladder) record says so rather than letting absence read as passage.
function economicsSection(econ) {
  if (!econ) {
    return `<div class="card" style="margin-bottom:16px;">
      <h3>Economics roll-up</h3>
      <div class="foot">not yet assembled for this driver —
        <span class="mono">vinci theme-economics</span> writes the committed artifact.</div>
    </div>`;
  }
  const rows = econ.rows || [];
  const uw = rows.filter((r) => r.underwritten);
  const bare = rows.filter((r) => !r.underwritten);
  const tiers = (r) => (r.gate_regime == null
    ? `<span class="chip gate">unstamped (pre-ladder)</span>`
    : `${escapeHtml(r.asymmetry_tier || DASH)} · ${escapeHtml(r.return_tier || DASH)}`);
  const elig = (r) => (r.eligible === true ? `<span class="pill live">eligible</span>`
    : r.eligible === false ? `<span class="muted">not eligible</span>`
    : r.gate_regime == null ? `<span class="muted">${DASH}</span>`
    : `<span class="muted">undefined${
        r.eligible_undefined ? ` — ${escapeHtml(r.eligible_undefined)}` : ""}</span>`);
  const gap = (r) => (r.ev_gap == null
    ? `<span class="muted">${escapeHtml(r.ev_gap_status || DASH)}${
        r.ev_gap_reason ? ` — ${escapeHtml(r.ev_gap_reason)}` : ""}</span>`
    : `${Number(r.ev_gap).toFixed(2)}× <span class="cite">tev ${
        escapeHtml(r.ev_gap_vintages?.tev_as_of || "?")} · cons ${
        escapeHtml(r.ev_gap_vintages?.consensus_as_of || "?")}</span>`);
  const body = uw.length
    ? `<div style="overflow-x:auto;"><table class="data"><thead><tr><th>name</th><th>tag</th>
        <th>asymmetry · return</th><th>eligible</th><th>underwritten</th>
        <th>ev_gap (ours/TEV)</th></tr></thead><tbody>${uw.map((r) => `<tr>
        <td class="mono">${escapeHtml(r.ticker)}</td>
        <td>${escapeHtml(r.substructure_tag || "")}</td>
        <td>${tiers(r)}</td><td>${elig(r)}</td>
        <td>${escapeHtml(r.underwrite_date || DASH)}</td><td>${gap(r)}</td></tr>`).join("")}
        </tbody></table></div>`
    : `<div class="foot">no member carries an underwritten scenario record — that sparseness is
       the finding this surface exists to make visible.</div>`;
  const bareList = bare.length
    ? `<details class="wl-why"><summary class="muted" style="font-size:12px;">no underwrite ·
        ${fmtInt(bare.length)} member(s)</summary>
        <div class="mono" style="font-size:12px; margin-top:6px;">${
          bare.map((r) => escapeHtml(r.ticker)).join(" · ")}</div></details>`
    : "";
  return `<div class="card" style="margin-bottom:16px;">
      <h3>Economics roll-up <span class="uw-h-sub">inform-only · per-member · no
        composite</span></h3>
      <div class="foot" style="margin:2px 0 8px;">${fmtInt(econ.n_underwritten)} of
        ${fmtInt(econ.n_members)} members underwritten — ${escapeHtml(econ.membership_note || "")}
        · as of ${fmtDate(econ.as_of)}</div>
      ${body}${bareList}
    </div>`;
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
  const [d, cx, cands, mon, thesis, econ] = await Promise.all([
    getThemeDriver(slug), getThemeContext(slug),
    getRadarCandidates().then((r) => r.candidates || []).catch(() => []),
    getMonitor().catch(() => null),
    getThemeThesis(slug), getThemeEconomics(slug),
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
    bodyHtml: sub + thesisSection(thesis, cands, d.slug || slug, d.label) + whatSection(cx)
      + tiers + economicsSection(econ) + wlBlock + avoidBlock(d) + fwd,
  });
}
