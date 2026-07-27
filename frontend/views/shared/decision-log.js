// DECISION LOG — the immutable, append-only ledger as a read-only list of frozen legs.
// Displayed here; logged ONLY via the CLI. No edit / delete / write path exists.
import { getLedger, isBuyVerdict, getMonitor } from "../../lib/snapshots.js";
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

  const counts = `
    <div class="grid cols-4" style="margin-bottom:16px;">
      <div class="card metric"><h3>Verdicts logged</h3><div class="value">${fmtInt(led.counts.logged)}</div><div class="foot">immutable legs of the spread</div></div>
      <div class="card metric"><h3>Resolved</h3><div class="value">${fmtInt(led.counts.resolved)}</div><div class="foot">reached horizon · feed the spread</div></div>
      <div class="card metric"><h3>Buy legs</h3><div class="value">${fmtInt(led.counts.buy)}</div><div class="foot">the long side</div></div>
      <div class="card metric"><h3>Avoid legs</h3><div class="value">${fmtInt(led.counts.avoid)}</div><div class="foot">the terminal-decline side</div></div>
    </div>`;

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
// horizon. The sign convention is printed beside the number, not assumed.
function spreadCard(mon) {
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
        <span class="muted" style="font-size:12px; margin-left:auto;">marked ${fmtDate(mon.as_of)}</span>
      </div>
      <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:8px; font-size:13px;">
        <div><span class="muted">BUY legs</span> <span class="mono">${fmtInt(s.buy_n)}</span> <span class="mono ${signCls(s.buy_mean_excess)}">${pct(s.buy_mean_excess)}</span> <span class="muted">mean excess</span></div>
        <div><span class="muted">AVOID legs</span> <span class="mono">${fmtInt(s.avoid_n)}</span> <span class="mono ${signCls(s.avoid_mean_excess)}">${pct(s.avoid_mean_excess)}</span> <span class="muted">mean excess</span></div>
        <div><span class="muted">Resolved</span> <span class="mono">${fmtInt(s.resolved_n)}/${fmtInt((mon.rows || []).length)}</span></div>
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
        <span class="pill ${cl ? "unresolved" : isBuy ? "buy" : "avoid"}">${escapeHtml(e.verdict)}</span>
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
function liveRow(mark) {
  if (!mark) return "";
  return `
    <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:8px; padding-top:8px; border-top:1px solid var(--line); font-size:13px;">
      <div><span class="muted">Current</span> <span class="mono">${fmtPrice(mark.current_price)}</span> <span class="muted">@ ${fmtDate(mark.current_date)}</span></div>
      <div><span class="muted">Return</span> <span class="mono ${signCls(mark.position_return)}">${pct(mark.position_return)}</span></div>
      <div><span class="muted">vs ${escapeHtml(mark.benchmark)}</span> <span class="mono ${signCls(mark.benchmark_return)}">${pct(mark.benchmark_return)}</span></div>
      <div><span class="muted">Excess</span> <span class="mono ${signCls(mark.excess)}" style="font-weight:600;">${pct(mark.excess)}</span></div>
      <div><span class="muted">Elapsed</span> <span class="mono">${fmtInt(mark.days_elapsed)}/${fmtInt(mark.horizon_days)}d</span></div>
    </div>`;
}
