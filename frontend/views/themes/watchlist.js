// WATCHLIST (#/themes/watchlist) — a FLAT cross-theme checklist (NOT a drill-down; the standing
// monitoring surface, naturally bounded). Each name is a COLLAPSED row LED BY ITS VERBATIM TRIGGER
// (ticker · category · the re-underwrite trigger); the disposition rationale is behind a "why it's on
// the list" expand (collapsed by default) — the same trigger-led / rationale-on-demand principle as
// the surfaced-names row collapse. Per-theme sections (collapsible); avoid-controls a separate section.
import { getThemesIndex, getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, fmtPrice, DASH, escapeHtml, gradeLabel, gradeBucket } from "../../lib/format.js";

// --- underwrite card ------------------------------------------------------------------------
// A name with a committed `scenarios/<TICKER>.json` record carries a `scenarioCard` (attached by
// frontend/build.py). It renders IN PLACE here, and the VERDICT SUPERSEDES THE FREEZE: the
// re-underwrite trigger comes from the recorded verdict, not the scan note that preceded it —
// otherwise the row keeps advertising an underwrite that has already been decided.
// Names without a card are untouched (identical markup to before).
const oneDp = (v, suffix = "") =>
  typeof v === "number" && isFinite(v) ? v.toFixed(1) + suffix : DASH;

// sign OUTSIDE the currency mark — "-$10.31", never fmtPrice's "$-10.31"
const signedMoney = (v) =>
  typeof v === "number" && isFinite(v)
    ? (v < 0 ? "-$" + Math.abs(v).toFixed(2) : "$" + v.toFixed(2))
    : DASH;

const uwLeg = (s) => `
        <div class="uw-leg">
          <span class="uw-leg-n">${escapeHtml(s.name)}${s.name === "bull" ? ` <em>not in ratio</em>` : ""}</span>
          <b>${fmtPrice(s.valuePerShare)}</b>
          <span class="uw-sub">EV/EBIT ${oneDp(s.evEbit, "x")} · FCF ${s.normFcf == null ? DASH : "$" + oneDp(s.normFcf) + "M"}</span>
        </div>`;

const uwCard = (c) => {
  const v = c.verdict || {};
  const legs = ["bear", "base", "bull"]
    .map((name) => (c.scenarios || []).find((s) => s.name === name))
    .filter(Boolean);
  return `
      <div class="uw">
        <div class="uw-head">
          ${v.status ? `<span class="pill conditional">${escapeHtml(String(v.status).toUpperCase())}</span>` : ""}
          ${c.passFail ? `<span class="pill ${c.passFail === "PASS" ? "buy" : "avoid"}">${escapeHtml(c.passFail)}</span>` : ""}
          <span class="uw-ratio">${typeof c.ratio === "number" ? escapeHtml(c.ratio.toFixed(2)) + " : 1" : DASH}</span>
          <span class="uw-k">vs ${escapeHtml(String(c.bar == null ? 2 : c.bar))}:1 bar</span>
          <span class="uw-k" style="margin-left:auto;">spot ${fmtPrice(c.spot)}${v.recorded ? ` · recorded ${escapeHtml(v.recorded)}` : ""}</span>
        </div>
        <div class="uw-legs">${legs.map(uwLeg).join("")}</div>
        <div class="uw-rr">reward <b>${signedMoney(c.reward)}</b> · risk <b>${signedMoney(c.risk)}</b>
          <span class="uw-k">— base−spot / spot−bear; bull is printed but NEVER in the ratio</span></div>
        ${v.rationale ? `<div class="uw-why">${escapeHtml(v.rationale)}</div>` : ""}
        ${v.avoidPriced ? `<div class="uw-avoid"><b>avoid-priced</b> — ${escapeHtml(v.avoidPricedNote || "")}</div>` : ""}
      </div>`;
};

const uwTriggers = (c) => {
  const t = (c.verdict && c.verdict.reunderwriteTriggers) || [];
  return t.length
    ? `<ul class="uw-trig">${t.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ul>`
    : escapeHtml(DASH);
};

export async function render(root, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading watchlist…</div>` });
  const idx = await getThemesIndex();
  if (!idx.drivers.length) {
    root.innerHTML = frame(item, { bodyHtml: `<div class="notice">No theme artifacts committed to this deploy yet.</div>` });
    return;
  }
  const drivers = await Promise.all(idx.drivers.map((d) => getThemeDriver(d.slug)));

  // Repetition-reduced top: the stage subtitle already orients (names to re-underwrite on a trigger,
  // flat cross-theme surface, trigger-led rows). The read-only caveat + rationale-pointer — the only
  // facts the banner added — move to a footer, mirroring the Radar tab's subtitle-up / disclaimer-down.
  const wlFoot = `<div class="wl-foot foot muted" style="margin-top:16px; font-size:12px;">
    <b>Read-only</b> — nothing here fires automatically (the backend delta-scan that watches filings is a
    later build). Each row's rationale is behind “why it's on the list”.</div>`;

  const wlRow = (n) => {
    const c = n.scenarioCard;   // present only for names with a committed underwrite record
    return `
    <div class="wl-row">
      <div class="wl-top">
        <b class="mono">${escapeHtml(n.ticker)}</b>
        <span class="muted" style="font-size:12px;">${escapeHtml(n.substructureTag || "")}</span>
        <span class="gt ${gradeBucket(n.basis)}">${escapeHtml(gradeBucket(n.basis))}</span>
        ${n.edgarUrl ? `<a href="${encodeURI(n.edgarUrl)}" target="_blank" rel="noopener" style="font-size:11px; margin-left:auto;">EDGAR ${escapeHtml(n.accession || "")}</a>` : ""}
      </div>
      <div class="wl-trigger"><span class="k">re-underwrite when</span>${c ? uwTriggers(c) : escapeHtml(n.trigger || "—")}</div>
      ${c ? uwCard(c) : ""}
      ${n.rationale || n.gradeFact ? `<details class="wl-why">
        <summary>why it's on the list</summary>
        <div class="wl-why-body">${n.rationale ? escapeHtml(n.rationale) : ""}${n.gradeFact ? `<div class="cite">${escapeHtml(n.gradeFact)}</div>` : ""}</div>
      </details>` : ""}
    </div>`;
  };

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

  root.innerHTML = frame(item, { bodyHtml: sections + wlFoot });
}
