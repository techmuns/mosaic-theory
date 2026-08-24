// Pure presentation helpers — formatting only, no data access, no DOM.
// (Kept tiny and dependency-free; the dashboard is static and lightweight by design.)

export const DASH = "—"; // the honest "no value" glyph used across the UI

export function fmtInt(n) {
  return typeof n === "number" && isFinite(n) ? n.toLocaleString("en-US") : DASH;
}

export function fmtMoney(n, { compact = true } = {}) {
  if (typeof n !== "number" || !isFinite(n)) return DASH;
  if (!compact) return "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 });
  const a = Math.abs(n);
  // unary + drops trailing zeros: 10.00→10, 3.05→3.05, 300.0→300 ($10B / $3.05B / $300M)
  if (a >= 1e9) return "$" + +(n / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return "$" + +(n / 1e6).toFixed(1) + "M";
  if (a >= 1e3) return "$" + (n / 1e3).toFixed(0) + "K";
  return "$" + n.toFixed(2);
}

export function fmtPrice(n) {
  return typeof n === "number" && isFinite(n) ? "$" + n.toFixed(2) : DASH;
}

export function fmtPct(frac, { digits = 0, signed = false } = {}) {
  if (typeof frac !== "number" || !isFinite(frac)) return DASH;
  const v = (frac * 100).toFixed(digits);
  return (signed && frac > 0 ? "+" : "") + v + "%";
}

export function fmtScore(n) {
  return typeof n === "number" && isFinite(n) ? n.toFixed(3) : DASH;
}

// ISO date/datetime string -> "Jun 17, 2026" (date-only, UTC-safe, no time drift).
export function fmtDate(iso) {
  if (!iso) return DASH;
  const d = new Date(String(iso).slice(0, 10) + "T00:00:00Z");
  if (isNaN(d)) return DASH;
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
}

// A full datetime stamp (date + HH:MM) for the assembly timestamp, so two same-day re-assemblies are
// distinguishable. A tz-aware ISO (…Z / +hh:mm) renders in UTC and is labeled "UTC"; a legacy naive
// ISO (no zone) preserves the stored wall-clock and is labeled "(local)" — never a false UTC claim.
export function fmtStamp(iso) {
  if (!iso) return DASH;
  const s = String(iso);
  const aware = /([zZ])|([+-]\d\d:?\d\d)$/.test(s);
  const d = new Date(aware ? s : s + "Z"); // naive → read the stored wall-clock as UTC, label local
  if (isNaN(d)) return DASH;
  const t = d.toLocaleString("en-US", {
    year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    hour12: false, timeZone: "UTC",
  });
  return `${t} ${aware ? "UTC" : "(local)"}`;
}

// Whole days between two ISO dates (b - a). Positive => b is later.
export function daysBetween(aIso, bIso) {
  const a = new Date(String(aIso).slice(0, 10) + "T00:00:00Z");
  const b = new Date(String(bIso).slice(0, 10) + "T00:00:00Z");
  if (isNaN(a) || isNaN(b)) return null;
  return Math.round((b - a) / 86400000);
}

export function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

// The GRADE vocabulary — the classifier's real output + the analyst's working language. KEPT (never
// renamed or collapsed — it is the source of truth), only rendered CLEAN from the short basis key.
export const GRADE_LABEL = {
  binding: "binding contract",
  quantified: "quantified revenue",
  committed: "committed capacity",
  aspirational: "aspirational",
  none: "no exposure",
};
// one-line definitions for the inline key/legend shown on any screen that uses grades
export const GRADE_DEF = {
  binding: "a signed agreement with binding terms",
  quantified: "a $/% of revenue attributed to the driver",
  committed: "committed capex / capacity, no paying customer yet",
  aspirational: "stated intent — a mention, not exposure",
  none: "no driver exposure disclosed",
};
export function gradeLabel(basis) {
  return GRADE_LABEL[String(basis)] || String(basis || "");
}
// clean a RAW enum ("committed-capacity", "binding-contract", "stated-intent") for display — hyphens
// to spaces, never shown as the raw string
export function cleanGrade(s) {
  return String(s || "").replace(/-/g, " ");
}

// magnitude bucket — the coarse firm/partial/early grouping of the fine basis (the machine's SCAN
// read). firm = binding|quantified (contracted/quantified) · partial = committed · early = aspirational.
// One source of truth for the bucketing shared by the Overview table + the watchlist firmness tag.
export const GRADE_BUCKET = {
  binding: "firm", quantified: "firm", committed: "partial", aspirational: "early", none: "none",
};
export function gradeBucket(basis) {
  return GRADE_BUCKET[String(basis)] || "none";
}

// THE TIERED LADDER's display vocabulary (#487), living HERE and not in a view — `uw-card.js`
// and `themes/portfolio.js` both render it, and a second copy is how the grade-bucket trio came
// to need a three-way parity pin. Labels are the UI's pill caps; render.py carries the md-prose
// wording separately and deliberately (different register, same keys — pinned).
export const TIER_LABEL = {
  poor: "POOR", below_target: "BELOW TARGET", target_met: "TARGET MET",
  preferred: "PREFERRED", fails: "FAILS", minimum_met: "MINIMUM MET", undefined: "UNDEFINED",
};
// EXPLICIT PER TIER — never a ternary with a fallthrough. The first cut defaulted anything
// unlisted to red `avoid`, so a tier added to the enum would have rendered as a FAILURE at a
// reader until someone noticed (review, #489). An unknown key now renders neutral.
export const TIER_TONE = {
  poor: "avoid", below_target: "avoid", fails: "avoid",
  target_met: "buy", minimum_met: "buy", preferred: "buy",
  undefined: "unresolved",
};
// QUEUE AGE AND RUN HEALTH — one definition, three consumers (overview, ingestion, ranker). The
// age chip lived only on the ranker, so you had to open the queue to learn the queue was stale;
// during a four-week outage that is the screen you are least likely to open, because it looks
// unchanged. 10 days = the weekly cadence plus slack, a face-validity threshold tuned on nothing.
export const QUEUE_STALE_DAYS = 10;

export function queueAgeDays(asOf) {
  if (!asOf) return null;
  const d = Math.floor((Date.now() - Date.parse(`${asOf}T00:00:00Z`)) / 86400000);
  return Number.isFinite(d) ? d : null;
}

// WORDING FIXED WITH THE CRON REMOVAL (2026-08-24): this used to say "the weekly screen may not
// have run", which implied a missed appointment. There is no schedule any more — the screen runs
// when the operator triggers it — so the honest statement is the queue's AGE, and the prompt is
// an invitation rather than an alarm about a broken timer.
export function queueAgeChip(asOf) {
  const days = queueAgeDays(asOf);
  if (days === null || days < QUEUE_STALE_DAYS) return "";
  return `<span class="chip gate" title="This queue was written by the weekly screen on ${
    escapeHtml(String(asOf))}. The names, ranks and price-derived reads are all as of that date, `
    + `not today. The screen is operator-triggered: Actions -> weekly-screen -> Run workflow, or `
    + `run vinci run-weekly locally.">⚠ queue is ${days} days old — screened ${
      escapeHtml(String(asOf))}</span>`;
}

// The last run's OUTCOME, which no age can tell you: a failed run commits nothing, so silence and
// failure look identical on a surface that reads only committed data. `null` is UNKNOWN and says
// so — never a pass.
export function runHealth(run) {
  if (!run || !run.conclusion) {
    return { tone: "unresolved", label: "UNKNOWN",
             detail: "no run has reported its outcome yet — a failed run commits nothing, so this "
                     + "surface cannot tell a failure from a run nobody started" };
  }
  const ok = run.conclusion === "success";
  return {
    tone: ok ? "buy" : "avoid",
    label: ok ? "OK" : "FAILED",
    detail: ok ? "the last attempt completed and committed"
               : (run.remediation || "the last attempt failed"),
  };
}

export function tierPill(tier) {
  if (!tier) return "";
  const key = String(tier);
  const cls = TIER_TONE[key] || "unresolved";
  return ` <span class="pill ${cls} uw-mini">${escapeHtml(TIER_LABEL[key] || key)}</span>`;
}
