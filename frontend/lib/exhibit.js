// EXHIBIT PRIMITIVES — the shared, tested math + placement behind the dossier's SVG exhibits
// (frontend/views/shared/dossier.js: revenue/EBITDA bars, own-history multiple band, ROIC trend).
// Extracted so the axis / scale / domain / label logic is solved and regression-pinned ONCE instead of
// re-derived per exhibit — that per-exhibit duplication is where the axis-rounding (592→1000),
// phantom-negative-tick, and label-placement bugs kept recurring.
//
// FUND-POV DESIGN RULES (these encode the repo guardrails in the render layer):
//  · NO FABRICATION. A null datum is a GAP, never bridged or interpolated. `extent` of an all-null
//    series is null — a loud signal — never `Infinity` from `Math.min(...[])`. No primitive here
//    invents a value the data didn't carry.
//  · HONEST AXES (don't round noise up to signal). A BAR encodes magnitude by LENGTH, so its axis MUST
//    include zero — `barDomain` always spans 0. A LINE reads RELATIVE change, so it may zoom, but
//    `lineDomain` extends beyond zero ONLY on a side that actually has data of that sign (no phantom
//    "-3%" tick under an all-positive margin, no phantom "+4%" over an all-negative ROIC).
//  · STRUCTURED-IN. Every primitive takes `number | null` arrays — never a rendered display string.
//  · DETERMINISTIC. Pure functions, no DOM / window / Date / random, so `node` can unit-test them
//    (tests/test_dossier.py, node-gated) exactly as the browser runs them.
//
// DELIBERATELY ABSENT (a guardrail, not an omission): there is NO trendline / regression / moving-
// average / extrapolation / projection / price-target primitive. Exhibits ASSEMBLE observed, cited
// facts; a fitted or forward-projected mark would be the machine CONCLUDING. A forward point may only
// come from a cited estimate series (e.g. the `is_estimate` columns), never from a curve fit here.
//
// EXTENSION POINTS (enabled by these primitives, to build when a real consumer lands — not before):
//  · Horizontal bars (peer comps, customer-concentration %): `linScale` on the x-range + `barDomain`.
//  · Multi-line (name vs peer-median multiple over time): one `lineDomain` over the flattened series,
//    N polylines. Stacked bars (segment mix, debt-maturity ladder): stack offsets + `barDomain` over
//    the stack totals. Sparklines: `linScale` + a polyline.
//  · Dense-label collision (many near-equal labels on one axis) is today handled structurally — sign-
//    aware placement (`barLabelY`), roomy-side anchoring (`labelAnchor`), auto-scaled headroom, and
//    haloed text. A general 1-D spread/resolver is the natural next primitive IF a denser exhibit
//    needs it; it composes on these scales. Not shipped unused.

// ---- numeric guards ----
export const nums = (a) => (Array.isArray(a) ? a.filter((x) => x != null && Number.isFinite(x)) : []);
// extent → [min, max] over the non-null finite values, or null if there are none.
// (Never returns the Infinity that `Math.min(...[])` / `Math.max(...[])` would.)
export function extent(a) { const v = nums(a); return v.length ? [Math.min(...v), Math.max(...v)] : null; }

// ---- nice-number rounding ----
// Round UP to a FINE nice-step ×10ⁿ. The old coarse 1/2/2.5/5/10 grid jumped 5.92→10 (592→1000),
// compressing bars into dead space; these finer steps land 592→600 (callers apply headroom first).
const NICE = [1, 1.1, 1.2, 1.5, 1.8, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10];
export function niceCeil(x) {
  if (!(x > 0)) return 1;                                   // guard 0 / negative / NaN
  const p = 10 ** Math.floor(Math.log10(x)), f = x / p;
  return (NICE.find((s) => s >= f - 1e-9) || 10) * p;       // epsilon so an exact 6.0 picks 6, not 7
}

// ---- scales (domain → range map); orientation-agnostic — feed a y-range OR an x-range ----
// A degenerate domain (lo === hi) maps every value to the range midpoint (never divide by zero).
export function linScale(dLo, dHi, rLo, rHi) {
  const s = dHi - dLo;
  return (v) => (s ? rLo + ((v - dLo) / s) * (rHi - rLo) : (rLo + rHi) / 2);
}
// Log scale for POSITIVE-only wide ranges (a multiples convention — tames a P/E blown out by a near-
// zero-EPS quarter). Returns null if the domain is not strictly positive, so the caller falls back to
// linScale — fail-loud: never take a log of a non-positive.
export function logScale(dLo, dHi, rLo, rHi) {
  if (!(dLo > 0 && dHi > 0)) return null;
  const a = Math.log(dLo), s = Math.log(dHi) - a;
  return (v) => (s ? rLo + ((Math.log(v) - a) / s) * (rHi - rLo) : (rLo + rHi) / 2);
}

// ---- domains (the honest-axis rules) ----
// barDomain: bars encode magnitude → the axis ALWAYS includes zero. Extend to a nice ceiling with
// `head` headroom (room for the tallest value label), and only BELOW zero when a real negative exists
// (and only ABOVE zero when a real positive exists). Empty series → null (caller skips the exhibit).
export function barDomain(series, { head = 1.1 } = {}) {
  const e = extent(series);
  if (!e) return null;
  const [lo, hi] = e;
  const top = hi > 0 ? niceCeil(hi * head) : 0;
  const bot = lo < 0 ? -niceCeil(-lo * head) : 0;
  return { lo: bot, hi: top !== 0 ? top : bot < 0 ? 0 : 1 };  // all-zero series → [0,1], never [0,0]
}
// lineDomain: a line reads relative change. Zero is a meaningful threshold (profitability, value-
// creation), so the domain is floored/capped at 0 — but padded BEYOND zero only on a side that has
// real data of that sign. padFrac/minPad tune the feel per caller; minSpan guards a flat series.
export function lineDomain(series, { padFrac = 0.15, minPad = 0, minSpan = 0 } = {}) {
  const e = extent(series);
  if (!e) return null;
  const [rLo, rHi] = e;
  let lo = Math.min(0, rLo), hi = Math.max(0, rHi);
  if (hi - lo < minSpan) { const c = (hi + lo) / 2; lo = c - minSpan / 2; hi = c + minSpan / 2; }
  const pad = Math.max((hi - lo) * padFrac, minPad);
  if (rHi > 0) hi += pad;                                   // extend above 0 only if truly positive
  if (rLo < 0) lo -= pad;                                   // extend below 0 only if truly negative
  return { lo, hi };
}

// ---- shared design FRAME (the ONE visual system for the dossier's SVG exhibits) ----
// Size, plot y-band, left inset, typography, halo, and card margin — referenced by EVERY panel exhibit
// in dossier.js (revenue/EBITDA, return-ratios, ROIC trend) so they read as one system instead of each
// re-inventing its canvas + fonts (the drift this centralises). A SINGLE-metric exhibit uses `wSingle`
// (a lone chart is NOT stretched to the two-panel `wDual`); every exhibit shares H, the cy0/cy1 band,
// `padL`, and the `fs` font scale. NOT a chart-type layout — bar/line/band geometry stays per-exhibit;
// this only fixes the frame so "size / padding / spacing / labelling" match across them.
export const EXHIBIT = Object.freeze({
  H: 276,                 // canvas height (viewBox)
  cy0: 54, cy1: 234,      // plot band: title + panel titles above cy0, x-labels + legend below cy1
  padL: 44,               // left inset — the leftmost panel starts here; y-axis labels sit just left
  wSingle: 430, wDual: 760,  // one-panel vs two-panel canvas width (a single metric is not stretched)
  // font scale (px): main title · panel sub-title · y-axis · x-axis · point value · legend
  fs: Object.freeze({ title: 15, panel: 11.5, axis: 10.5, xlabel: 10, point: 10, legend: 11.5 }),
  halo: 'paint-order="stroke" stroke="var(--surface)" stroke-width="2.8"',  // readable text over marks
  margin: "18px 0 16px",  // .ds-exhibit vertical rhythm
});

// ---- label placement ----
// Anchor a value beside a marker on the roomier side of its panel midpoint (avoids running off-panel).
export const labelAnchor = (px, mid) => (px < mid ? "start" : "end");

// X-AXIS LABEL THINNING (2026-07-29). Every period label was drawn regardless of how many there
// were: AORT's revenue exhibit put 24 of them in one axis and TEN PAIRS physically overlapped
// (measured min gap −6px), which is worse than useless — a smear of ink where the reader looks
// for a date. Keep every Nth label instead, with the stride chosen from the space actually
// available, and ALWAYS keep the last one: on a time axis the most recent period is the one a
// reader looks for first, and dropping it to keep a tidy stride would be the wrong trade.
// Returns a predicate, so a caller renders the same loop and only decides whether to emit text.
export function xLabelKeeper(count, panelWidth, { minPitch = 26 } = {}) {
  if (count <= 1) return () => true;
  const slot = panelWidth / count;
  const stride = Math.max(1, Math.ceil(minPitch / Math.max(slot, 1)));
  if (stride === 1) return () => true;
  // count back FROM the last index so the newest period always lands on a kept tick
  return (i) => (count - 1 - i) % stride === 0;
}
// Sign-aware vertical position for a bar's value label: ABOVE a positive bar's top, BELOW a negative
// bar's bottom — so the label never lands inside the bar or collides across the zero baseline.
export const barLabelY = (barEdgeY, isNeg, above = 4, below = 11) => (isNeg ? barEdgeY + below : barEdgeY - above);
