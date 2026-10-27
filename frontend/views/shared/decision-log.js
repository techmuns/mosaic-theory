// DECISION LOG — the immutable, append-only ledger as a read-only list of frozen legs.
// Displayed here; logged ONLY via the CLI. No edit / delete / write path exists.
import { getLedger, isBuyVerdict, verdictWord, getMonitor } from "../../lib/snapshots.js";
import { fmtPrice, fmtDate, fmtInt, escapeHtml, DASH } from "../../lib/format.js";

// The LIVE columns come from the latest COMMITTED monitor snapshot (vinci monitor, manual
// cadence) — never a live fetch. Absent history → every live cell reads "—": the ledger's frozen
// facts still render, and no mark is invented. Sector is RE-RESOLVED here for display (the frozen
// row keeps whatever it logged; the fix is forward, never a mutation of an append-only row).
const pct = (v) => (typeof v === "number" && isFinite(v)
  ? (v >= 0 ? "+" : "") + (v * 100).toFixed(2) + "%" : DASH);
const signCls = (v) => (typeof v !== "number" || !isFinite(v) ? "" : v >= 0 ? "mon-up" : "mon-dn");

export async function render(root, _params, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading ledger…</div>` });
  const [led, mon] = await Promise.all([getLedger(), getMonitor()]);
  const marks = {};
  for (const r of (mon && mon.rows) || []) marks[String(r.ticker).toUpperCase()] = r;

  // EXCLUDED FROM THE PROOF NUMBER IS NOT THE SAME AS ABSENT FROM THE APP. The tiles above are
  // screen-origin only (that is what the spread measures); any other book is stated here so a
  // followed verdict is visible as its own line rather than silently missing from both.
  const books = (l) => {
    // NO "not overshoot" FILTER any more: the map now holds exactly the rows the tiles above
    // exclude, so filtering by sleeve here is what dropped a followed-OVERSHOOT row from the
    // only line that would have shown it (review #382). The label names the origin too — under
    // the default book the sleeve alone would read as the screen composite it is not.
    const rows = Object.values(l.otherBooks || {});
    if (!rows.length) return "";
    const cells = rows.map((b) =>
      `<span class="mono">${escapeHtml(b.sleeve === "overshoot" ? `${b.origin} · ${b.sleeve}` : b.sleeve)}</span> ${b.long} long / ${b.short} measured-against · ${b.resolved} resolved`
    ).join(" &nbsp;·&nbsp; ");
    return `<div class="subtitle muted" style="margin:-8px 0 16px;">Other books (their own curves, never pooled into the spread above) — ${cells}</div>`;
  };

  const counts = `
    <div class="grid cols-4" style="margin-bottom:16px;">
      <div class="card metric"><h3>Verdicts logged</h3><div class="value">${fmtInt(led.counts.logged)}</div><div class="foot">screen-origin · immutable legs of the spread</div></div>
      <div class="card metric"><h3>Resolved</h3><div class="value">${fmtInt(led.counts.resolved)}</div><div class="foot">reached horizon · feed the spread</div></div>
      <div class="card metric"><h3>Buy legs</h3><div class="value">${fmtInt(led.counts.buy)}</div><div class="foot">the long side</div></div>
      <div class="card metric"><h3>Avoid legs</h3><div class="value">${fmtInt(led.counts.avoid)}</div><div class="foot">the leg it is measured against</div></div>
    </div>
    ${books(led)}`;

  const banner = `
    <div class="subtitle muted" style="margin-bottom:16px;">
      Append-only and immutable — once written, a verdict's entry price is frozen and cannot be edited, deleted, or revised.
      The friction is the safeguard: the BUY−AVOID spread is only an honest forward prediction if verdicts are frozen before
      outcomes. Logging happens via the <span class="mono">log-verdict</span> CLI; this dashboard only displays it.
    </div>`;

  const spread = spreadCard(mon) + freshnessPanel(mon);
  const entries = led.entries.length
    ? led.entries.map((e) => entryCard(e, marks[String(e.ticker).toUpperCase()])).join("")
    : `<div class="notice">No verdicts logged yet.</div>`;

  root.innerHTML = frame(item, { bodyHtml: counts + banner + spread + entries });
}

// The BUY−AVOID spread, carrying its own caveats — a DIAGNOSTIC until every row reaches its
// horizon. The sign convention is printed beside the number, not assumed. Exported for the node pin.
export function spreadCard(mon) {
  if (!mon) {
    return `<div class="notice" style="margin-bottom:14px;">No monitor snapshot committed yet —
      live columns read ${DASH}. Run <span class="mono">python -m vinci monitor</span>.</div>`;
  }
  const s = mon.spread || {};
  const val = typeof s.spread === "number"
    ? `<span class="${signCls(s.spread)}" style="font-size:20px; font-weight:650;">${(s.spread * 100 >= 0 ? "+" : "")}${(s.spread * 100).toFixed(2)} pp</span>`
    : `<span class="pill unresolved">UNDEFINED</span> <span class="muted">${escapeHtml(s.undefined_reason || "")}</span>`;
  return `
    <div class="card" style="margin-bottom:16px;">
      <div style="display:flex; gap:14px; align-items:baseline; flex-wrap:wrap;">
        <span style="font-size:12px; text-transform:uppercase; letter-spacing:0.04em; color:var(--ink-3);">BUY−AVOID spread</span>
        ${val}
        <span class="pill conditional">diagnostic</span>
        <span class="muted" style="font-size:12px; margin-left:auto;">marked ${fmtDate(mon.as_of)}${
          (mon.rows || []).some((r) => r.resolved) ? " · resolved rows at their horizon close" : ""}</span>
      </div>
      <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:8px; font-size:13px;">
        <div><span class="muted">BUY legs</span> <span class="mono">${fmtInt(s.buy_n)}</span> <span class="mono ${signCls(s.buy_mean_excess)}">${pct(s.buy_mean_excess)}</span> <span class="muted">mean excess</span></div>
        <div><span class="muted">AVOID legs</span> <span class="mono">${fmtInt(s.avoid_n)}</span> <span class="mono ${signCls(s.avoid_mean_excess)}">${pct(s.avoid_mean_excess)}</span> <span class="muted">mean excess</span></div>
        <div><span class="muted">Resolved</span> <span class="mono">${fmtInt(s.resolved_n)}/${fmtInt(s.scoped_n || (mon.rows || []).length)}</span></div>
      </div>
      <div class="foot" style="margin-top:8px;">${escapeHtml(s.caveat || "")}</div>
      <div class="foot">${escapeHtml(s.sign_convention || "")}</div>
      <div class="foot">${escapeHtml(mon.price_basis || "")}</div>
    </div>`;
}

// FRESHNESS / TRIGGERS — the machine FLAGS (a filing newer than the record's evidence), it never
// adjudicates a trigger as fired. Triggers print verbatim so the human reads the actual wording.
function freshnessPanel(mon) {
  const rows = (mon && mon.freshness) || [];
  if (!rows.length) return "";
  const card = (f) => {
    const flag = f.unread_print
      ? `<span class="pill avoid">unread print</span>`
      : `<span class="pill live">current</span>`;
    const newer = (f.newer_filings || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
    const trigs = (f.triggers || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
    // (catalyst calendar) a PASSED analyst deadline is the loudest row on the card — a flag that
    // the window closed, never an adjudication that the trigger fired.
    const passed = (f.passed_trigger_deadlines || [])
      .map((x) => `<div class="fact-caveat" style="margin-top:6px;">⏰ ${escapeHtml(x)}</div>`).join("");
    // (ruling 3) THE EVALUATED CRITERIA. Three states, rendered as three DIFFERENT things, because
    // that is the whole property: UNKNOWN and NOT_FIRED recommend opposite actions and must never
    // look alike. FIRED is the loudest row on the card; UNKNOWN carries its cause where a reader
    // looks for a number; NOT_FIRED states the reading that makes it false. The number and its
    // source ride along so the human can check the machine rather than trust it — and the
    // disposition stays theirs: this is a highlight, never an action.
    const stateClass = { FIRED: "avoid", UNKNOWN: "conditional", NOT_FIRED: "live" };
    const measured = (f.measured || []).map((m) => {
      const num = (m.observed === null || m.observed === undefined)
        ? "" : ` <span class="mono">${escapeHtml(String(m.observed))}${m.unit ? " " + escapeHtml(m.unit) : ""}</span>`;
      const src = m.source ? `<div class="foot">${escapeHtml(m.source)}</div>` : "";
      return `<li><span class="pill ${stateClass[m.state] || "locked"}">${escapeHtml(m.state)}</span>
        ${escapeHtml(m.trigger)}${num}
        <div class="muted" style="font-size:11px;">${escapeHtml(m.reason)}</div>${src}</li>`;
    }).join("");
    // AN EMPTY LIST IS NOT "NOTHING FIRED". A record with no measured criterion has falsifiers
    // that are all judgments — a different sentence from a quiet page, and the panel says which
    // rather than leaving the absence to be read as reassurance.
    const measuredBlock = measured
      ? `<div style="margin-top:8px;"><span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:.05em;">measured criteria</span><ul>${measured}</ul></div>`
      : ((f.triggers || []).length
          ? `<div class="foot" style="margin-top:6px;">no measured criteria — every falsifier above is a judgment, so none is machine-checked</div>`
          : "");
    const stale = (f.stale_tags || []).length
      ? `<div class="fact-caveat" style="margin-top:6px;">stale tag(s), served but not current: ${escapeHtml((f.stale_tags || []).join(", "))}</div>`
      : "";
    return `
      <div class="card" style="margin-bottom:10px;">
        <div style="display:flex; gap:10px; align-items:baseline; flex-wrap:wrap;">
          <span class="mono" style="font-weight:650;">${escapeHtml(f.ticker)}</span>
          <span class="muted" style="font-size:12px;">${escapeHtml(f.verdict || "")}</span>
          ${flag}
          <span class="muted" style="font-size:12px; margin-left:auto;">evidence ${fmtDate(f.last_evidence_date)}${f.last_evidence_source ? ` · ${escapeHtml(f.last_evidence_source)}` : ""}</span>
        </div>
        ${passed}
        ${f.next_expected_print ? `<div class="foot" style="margin-top:6px;">next print ~${fmtDate(f.next_expected_print)} — ${escapeHtml(f.next_expected_basis || "estimate")}</div>` : ""}
        ${newer ? `<div style="margin-top:8px;"><span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">Filed since the record's evidence</span><ul class="kv-list">${newer}</ul></div>` : ""}
        ${trigs ? `<div style="margin-top:8px;"><span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">Re-underwrite triggers (verbatim — not adjudicated)</span><ul class="kv-list">${trigs}</ul></div>` : ""}
        ${measuredBlock}
        ${stale}
        ${f.watch_note ? `<div class="fact-caveat" style="margin-top:6px;">${escapeHtml(f.watch_note)}</div>` : ""}
      </div>`;
  };
  return `
    <div style="margin:18px 0 6px;">
      <div style="font-size:12px; text-transform:uppercase; letter-spacing:0.04em; color:var(--ink-3); margin-bottom:8px;">Trigger &amp; freshness panel</div>
      <div class="subtitle muted" style="margin-bottom:10px;">The machine flags a filing newer than each record's evidence; it never concludes that a trigger fired. Next-print dates are estimates from the filer's own cadence.</div>
      ${rows.map(card).join("")}
    </div>`;
}

// The book, named only when it is NOT the default — same rule as the dossier shelf: a chip on
// every row is noise, and its absence on the overshoot majority carries the same information.
// Neutral ink, never a coloured pill: the book is context, not a call.
//
// Chipped when the row is NOT part of the screen-origin composite — whether that is because of
// its BOOK or because of its ORIGIN. Gating on the sleeve alone left a followed-overshoot row
// bare, so it read as one of the screen majority while being excluded from their spread
// (review #382). Under the default book the chip names the origin, because "overshoot" is
// precisely the thing it must not be mistaken for.
//
// AT MODULE SCOPE, beside its only caller. It was first written as a `const` inside `render()`
// while `entryCard` is a module-scope function, so every call threw `sleeveChip is not defined`
// and the whole page stopped at "Loading ledger…". Found by loading the page, not by any test.
const sleeveChip = (e) => {
  const sv = e.sleeve || "overshoot";
  const origin = e.origin || "screen";
  if (origin === "screen" && sv === "overshoot") return "";
  const label = sv === "overshoot" ? origin : sv;
  return ` <span class="ds-lean" title="judged under the ${escapeHtml(sv)} book, ${escapeHtml(origin)} origin — excluded from the screen-origin spread above">${escapeHtml(label)}</span>`;
};

function entryCard(e, mark) {
  const isBuy = isBuyVerdict(e.verdict);
  const status = e.resolved
    ? `<span class="pill live">resolved</span>`
    : `<span class="pill unresolved">unresolved · ${e.daysToHorizon == null ? DASH : Math.max(0, e.daysToHorizon) + "d to horizon"}</span>`;
  const field = (k, v) => v ? `<div style="margin-top:8px;"><span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">${k}</span><div style="font-size:13px; color:var(--ink-2);">${escapeHtml(v)}</div></div>` : "";

  // CLOSE-AWARE (2026-07-27). The log had NO close handling at all: both closed positions read as
  // live BUYs. The verdict word and `resolved` are untouched — a call is scored at its horizon
  // whatever happened to the position, so exits can never launder the track record — but a closed
  // row now says so, with its realized return derived from the two frozen prices (never stored).
  const cl = e.closed;
  const closedChip = cl
    ? `<span class="pill unresolved">closed ${fmtDate(cl.exitPriceAsOf)}${
        cl.exitPrice != null ? ` @ ${fmtPrice(cl.exitPrice)}` : ""}${
        cl.realizedReturn != null
          ? ` · ${cl.realizedReturn >= 0 ? "+" : "−"}${Math.abs(cl.realizedReturn * 100).toFixed(2)}%`
          : ""}</span>`
    : "";
  const closeReason = cl && cl.reason
    ? `<div class="muted" style="font-size:11.5px; margin-top:6px;">Close reason — ${escapeHtml(cl.reason)}</div>`
    : "";
  return `
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex; gap:12px; align-items:baseline; flex-wrap:wrap;">
        <span class="mono" style="font-size:16px; font-weight:650;">${escapeHtml(e.ticker)}</span>
        <span class="pill ${cl ? "unresolved" : isBuy ? "buy" : "avoid"}">${escapeHtml(verdictWord(e.verdict))}</span>${sleeveChip(e)}
        ${closedChip}
        ${status}
        <span class="muted" style="font-size:12px; margin-left:auto;">decided ${fmtDate(e.decidedAt)}</span>
      </div>
      ${closeReason}
      <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:10px; font-size:13px;">
        <div><span class="muted">Frozen entry</span> <span class="mono" style="font-weight:600;">${fmtPrice(e.entryPrice)}</span> <span class="muted">@ ${fmtDate(e.entryPriceAsOf)}</span></div>
        <div><span class="muted">Horizon</span> <span class="mono">${fmtInt(e.horizonDays)}d</span> <span class="muted">→ ${fmtDate(e.horizonDate)}</span></div>
        <div><span class="muted">Confidence</span> ${escapeHtml(e.confidence || DASH)}</div>
        <div><span class="muted">Benchmark</span> <span class="mono">${escapeHtml((mark && mark.benchmark) || e.benchmark || DASH)}</span>${mark && mark.benchmark && mark.benchmark !== e.benchmark ? ` <span class="muted" style="font-size:11px;">(cap-band; supersedes ${escapeHtml(e.benchmark)})</span>` : ""}</div>
        ${mark && mark.sector ? `<div><span class="muted">Sector</span> ${escapeHtml(mark.sector)}</div>` : ""}
      </div>
      ${liveRow(mark)}
      ${field("Thesis", e.thesis)}
      ${field("Kill criteria", e.killCriteria)}
      ${field("Twin ruled out", e.twinCall)}
    </div>`;
}

// Live marks for one leg — all four cells or none (an absent snapshot shows nothing rather than
// a half-populated row). Excess is against the leg's ASSIGNED benchmark over the same window.
// A RESOLVED row is marked at its HORIZON SESSION's close (the monitor, 2026-10-27), never the
// run's — so its price is labelled as that, not "Current". Exported for the node pin.
export function liveRow(mark) {
  if (!mark) return "";
  return `
    <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:8px; padding-top:8px; border-top:1px solid var(--line); font-size:13px;">
      <div><span class="muted">${mark.resolved ? "Horizon close" : "Current"}</span> <span class="mono">${fmtPrice(mark.current_price)}</span> <span class="muted">@ ${fmtDate(mark.current_date)}</span></div>
      <div><span class="muted">Return</span> <span class="mono ${signCls(mark.position_return)}">${pct(mark.position_return)}</span></div>
      <div><span class="muted">vs ${escapeHtml(mark.benchmark)}</span> <span class="mono ${signCls(mark.benchmark_return)}">${pct(mark.benchmark_return)}</span></div>
      <div><span class="muted">Excess</span> <span class="mono ${signCls(mark.excess)}" style="font-weight:600;">${pct(mark.excess)}</span></div>
      <div><span class="muted">Elapsed</span> <span class="mono">${fmtInt(mark.days_elapsed)}/${fmtInt(mark.horizon_days)}d</span></div>
    </div>`;
}
