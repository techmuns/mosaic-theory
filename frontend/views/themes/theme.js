// THEME ALTITUDE (#/themes/<theme>) — the ONE coherent read for a theme: what it is (the ratified
// brief), who's in play (tier cards → drill), the watchlist with its re-underwrite triggers and
// FULL underwrite cards (the only full-fidelity render site), the avoid-controls, and the forward
// cohorts. Framed by the shared stage frame (tabs persist on drill-down); a recorded verdict
// SUPERSEDES the freeze trigger — the row never advertises an underwrite already decided.
import { getThemeDriver, getThemeContext, getRadarCandidates, getMonitor, getThemeThesis, getThemeEconomics } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml, gradeBucket, gradeLabel } from "../../lib/format.js";
import { uwCard } from "../shared/uw-card.js";

// ONE wording for the loud absent state, twinned with `vinci/themes/thesis.py::THESIS_UNSTATED`
// (pinned) so the page and the freeze gate can never drift into two different stamps.
const THESIS_UNSTATED = "THESIS UNSTATED";

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


// THE THEME — ONE identity band (brief Item 1 + the ratified definition, merged 2026-08-30).
// Two cards used to answer the same question in sequence: "THEME THESIS" (the operator's claim)
// sat ABOVE "WHAT THIS THEME IS" (the ratified definition), so the reader met an absence stamp
// before learning what the theme was, and the page opened with two competing mastheads. One card,
// read top-down: what it IS (quoted, ratified) → what we CLAIM (declared, or loudly not) → what
// would prove us wrong (dated). Analyst notes are context, not the claim, so they collapse.
//
// The unstated state stays LOUD (ruling R2 — absence must never look like passage) but sits in
// the GATE register (amber, the repo's warning-that-blocks tone) rather than danger-red: it is a
// state every driver holds until its card is declared, not an error, and a red alarm on every
// page teaches the reader to ignore red. The consequence is spelled out beside it.
function themeSection(card, cx, cands, slug, label) {
  const ds = (cx && cx.driver_summary) || {};
  const notes = (cx && Array.isArray(cx.analyst_notes)) ? cx.analyst_notes : [];
  const quote = ds.quote
    ? `<blockquote class="tc-quote">${escapeHtml(ds.quote)}</blockquote>
       <div class="foot tc-src">— ${escapeHtml(ds.source || "ratified driver definition")}</div>`
    : "";
  const meta = card
    ? `<span class="muted">declared ${fmtDate(card.declared_date)}</span>
       <span class="pill locked">${escapeHtml(card.mechanism || "")}</span>`
    : `<span class="chip gate">⚠ ${escapeHtml(THESIS_UNSTATED)}</span>`;

  const c = findRadar(cands, slug, label);
  const priced = c
    ? `${escapeHtml(c.px12m || c.status || "on the radar")}${
        c.map && c.map.basis ? ` <span class="muted">· ${escapeHtml(c.map.basis)}</span>` : ""
      } <a href="#/themes/radar">Radar →</a>`
    : `<span class="muted">no committed radar read — the claim has no priced companion on file</span>`;

  // THE CLAIM: declared, or the gate's consequence stated in full. Never blank either way.
  const claim = card
    ? `<div class="fact"><span class="fact-label">market mistake</span>
         <span class="fact-val">${escapeHtml(card.market_mistake || "")}</span></div>
       <div class="fact"><span class="fact-label">null thesis</span>
         <span class="fact-val">${escapeHtml(card.null_thesis || "")}</span></div>
       <div class="fact"><span class="fact-label">priced read</span>
         <span class="fact-val">${priced}</span></div>`
    : `<div class="fact"><span class="fact-label">not declared</span>
         <span class="fact-val">No thesis card for this driver: the mechanism, the market's
           mistake and the null thesis are unstated, and new Stage-4 freezes are gated until one
           exists — <span class="mono">vinci theme-thesis declare ${escapeHtml(slug)}</span>.
           <div class="cite">The scan below stands; only the claim behind it is missing.</div>
         </span></div>`;

  // WHAT WOULD PROVE IT WRONG — dated, so the monitor can flag the closed window. Only rendered
  // when declared: an empty falsifier list under a heading would read as "none needed".
  // A DEADLINE ALREADY PAST MUST NOT READ AS PENDING. Same date arithmetic the monitor runs,
  // and deliberately the same word — the window CLOSED. Whether the falsifier fired stays the
  // human's read, exactly as in the monitor panel; this is presentation of the date the row
  // already carries, not a second adjudicating surface.
  const today = new Date().toISOString().slice(0, 10);
  const trig = (t, kind) => `<div class="fact"><span class="fact-label">${kind}</span>
      <span class="fact-val">${escapeHtml(t.trigger)} — <b>due ${escapeHtml(t.deadline)}</b>${
        t.deadline && t.deadline <= today
          ? ` <span class="chip gate">deadline passed</span>` : ""}${
        t.basis ? ` <span class="muted">· ${escapeHtml(t.basis)}</span>` : ""}</span></div>`;
  const tests = card
    ? `<div class="uw-sec-h" style="margin-top:14px;">What would prove it wrong
         <span class="basis">— dated; the monitor flags a passed deadline</span></div>
       ${trig(card.first_confirming || {}, "first confirming")}
       ${(card.falsifiers || []).map((f) => trig(f, "falsifier")).join("")}
       ${card.note ? `<div class="cite">${escapeHtml(card.note)}</div>` : ""}`
    : "";

  const noteBlock = notes.length
    ? `<details class="wl-why" style="margin-top:12px;">
         <summary>analyst notes · ${fmtInt(notes.length)}</summary>
         <div class="tc-notes">${notes
           .map((n) => `<div class="tc-note">${escapeHtml(n)}</div>`).join("")}</div>
       </details>`
    : "";

  return `<div class="card theme-context" style="margin-bottom:16px;">
      <div class="tt-head"><h3>The theme</h3><div class="tt-meta">${meta}</div></div>
      ${quote}
      <div class="uw-sec-h" style="margin-top:12px;">The claim
        <span class="basis">— the operator's, never the machine's</span></div>
      ${claim}${tests}${noteBlock}
    </div>`;
}

// THE ECONOMICS ROLL-UP (brief Item 4, ruling R5) — inform-only, per-member, NO COMPOSITE: it
// assembles the name-level economics the repo already computes (ladder tiers, eligibility,
// ev_gap WITH its vintages) and concludes nothing. Coverage leads as a COUNT, because sparse
// coverage is the finding this surface exists to make visible; the table is the house
// `table.data` so it reads like every other tabular block in the app.
function economicsSection(econ) {
  if (!econ) {
    return `<div class="card" style="margin-bottom:16px;">
      <h3>Economics <span class="uw-h-sub">per member · inform-only</span></h3>
      <div class="foot">not yet assembled —
        <span class="mono">vinci theme-economics</span> writes the committed artifact.</div>
    </div>`;
  }
  const rows = econ.rows || [];
  const uw = rows.filter((r) => r.underwritten);
  const bare = rows.filter((r) => !r.underwritten);
  const tiers = (r) => (r.gate_regime == null
    ? `<span class="chip gate">unstamped · pre-ladder</span>`
    : `${escapeHtml(r.asymmetry_tier || DASH)} · ${escapeHtml(r.return_tier || DASH)}`);
  const elig = (r) => (r.eligible === true ? `<span class="pill live">eligible</span>`
    : r.eligible === false ? `<span class="muted">not eligible</span>`
    : r.gate_regime == null ? `<span class="muted">${DASH}</span>`
    : `<span class="muted">undefined${
        r.eligible_undefined ? ` — ${escapeHtml(r.eligible_undefined)}` : ""}</span>`);
  const gap = (r) => (r.ev_gap == null
    ? `<span class="muted">${escapeHtml(r.ev_gap_status || DASH)}${
        r.ev_gap_reason ? ` — ${escapeHtml(r.ev_gap_reason)}` : ""}</span>`
    : `${Number(r.ev_gap).toFixed(2)}×<div class="cite">tev ${
        escapeHtml(r.ev_gap_vintages?.tev_as_of || "?")} · cons ${
        escapeHtml(r.ev_gap_vintages?.consensus_as_of || "?")}</div>`);
  const body = uw.length
    ? `<div style="overflow-x:auto;"><table class="data"><thead><tr><th>name</th><th>tag</th>
        <th>asymmetry · return</th><th>eligible</th><th>underwritten</th>
        <th>ev_gap (ours/TEV)</th></tr></thead><tbody>${uw.map((r) => `<tr>
        <td class="mono">${escapeHtml(r.ticker)}</td>
        <td>${escapeHtml(r.substructure_tag || "")}</td>
        <td>${tiers(r)}</td><td>${elig(r)}</td>
        <td class="mono">${escapeHtml(r.underwrite_date || DASH)}</td><td>${gap(r)}</td></tr>`)
        .join("")}</tbody></table></div>`
    : `<div class="foot">No member carries an underwritten scenario record — that sparseness is
       the finding this surface exists to make visible.</div>`;
  const bareList = bare.length
    ? `<details class="wl-why"><summary>no underwrite · ${fmtInt(bare.length)} member(s)</summary>
        <div class="mono" style="font-size:12px; margin-top:6px; line-height:1.7;">${
          bare.map((r) => escapeHtml(r.ticker)).join(" · ")}</div></details>`
    : "";
  return `<div class="card" style="margin-bottom:16px;">
      <div class="tt-head">
        <h3>Economics <span class="uw-h-sub">per member · inform-only · no composite</span></h3>
        <div class="tt-meta"><span class="muted">${escapeHtml(econ.membership_note || "")}
          · as of ${fmtDate(econ.as_of)}</span></div>
      </div>
      <div class="tt-stat"><span class="tt-stat-n">${fmtInt(econ.n_underwritten)}</span>
        <span class="muted">of ${fmtInt(econ.n_members)} members underwritten</span></div>
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
  const tiers = `<div class="uw-sec-h" style="margin:18px 0 8px;">Exposure scan
      <span class="basis">— disclosed-evidence tiers across the frozen universe; counts drill
      through</span></div>
    <div class="grid cols-4" style="margin-bottom:16px;">
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
    bodyHtml: sub + themeSection(thesis, cx, cands, d.slug || slug, d.label)
      + tiers + economicsSection(econ) + wlBlock + avoidBlock(d) + fwd,
  });
}
