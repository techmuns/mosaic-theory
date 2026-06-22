// DECISION LOG — the immutable, append-only ledger as a read-only list of frozen legs.
// Displayed here; logged ONLY via the CLI. No edit / delete / write path exists.
import { getLedger, isBuyVerdict } from "../lib/snapshots.js";
import { fmtPrice, fmtDate, fmtInt, escapeHtml, DASH } from "../lib/format.js";

export async function render(root, _params, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading ledger…</div>` });
  const led = await getLedger();

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

  const entries = led.entries.length
    ? led.entries.map(entryCard).join("")
    : `<div class="notice">No verdicts logged yet.</div>`;

  root.innerHTML = frame(item, { bodyHtml: counts + banner + entries });
}

function entryCard(e) {
  const isBuy = isBuyVerdict(e.verdict);
  const status = e.resolved
    ? `<span class="pill live">resolved</span>`
    : `<span class="pill unresolved">unresolved · ${e.daysToHorizon == null ? DASH : Math.max(0, e.daysToHorizon) + "d to horizon"}</span>`;
  const field = (k, v) => v ? `<div style="margin-top:8px;"><span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">${k}</span><div style="font-size:13px; color:var(--ink-2);">${escapeHtml(v)}</div></div>` : "";

  return `
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex; gap:12px; align-items:baseline; flex-wrap:wrap;">
        <span class="mono" style="font-size:16px; font-weight:650;">${escapeHtml(e.ticker)}</span>
        <span class="pill ${isBuy ? "buy" : "avoid"}">${escapeHtml(e.verdict)}</span>
        ${status}
        <span class="muted" style="font-size:12px; margin-left:auto;">decided ${fmtDate(e.decidedAt)}</span>
      </div>
      <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:10px; font-size:13px;">
        <div><span class="muted">Frozen entry</span> <span class="mono" style="font-weight:600;">${fmtPrice(e.entryPrice)}</span> <span class="muted">@ ${fmtDate(e.entryPriceAsOf)}</span></div>
        <div><span class="muted">Horizon</span> <span class="mono">${fmtInt(e.horizonDays)}d</span> <span class="muted">→ ${fmtDate(e.horizonDate)}</span></div>
        <div><span class="muted">Confidence</span> ${escapeHtml(e.confidence || DASH)}</div>
        <div><span class="muted">Benchmark</span> <span class="mono">${escapeHtml(e.benchmark || DASH)}</span></div>
      </div>
      ${field("Thesis", e.thesis)}
      ${field("Kill criteria", e.killCriteria)}
      ${field("Twin ruled out", e.twinCall)}
    </div>`;
}
