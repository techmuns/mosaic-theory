// UNDERWRITE CARD — the ONE renderer for a first-cut underwrite record (the `scenarioCard` shape
// build.py emits, standalone in frontend/scenarios/ and embedded in theme watchlist entries).
// Canonical components only: .card h3 eyebrow, .fact rows, table.data for the 3-leg matrix,
// .pill (verbatim-cased), .kv-list, inline ↳ .cite, <details>. No private type scale.
//
// CITES: the card OWNS its citations (lib/cites.js) and renders identically on every surface — no
// host has to run an endnote pass, and there is no mode to get wrong. TWO scopes, because print
// fate differs:
//   main body   withEndnotes("U", …) — its Sources list sits inside the card, right after the body.
//   <details>   withEndnotes("I", …) — marker AND list both INSIDE the collapsed block, so they
//               share print fate (`details:not([open])` drops the block from a PDF; an [I n]
//               resolving into the card's outer list would orphan there).
// Earlier this was gated on a `cites` option so a host with no pass wouldn't render "[?]". That
// knob is gone: self-contained scopes make the failure impossible instead of merely defaulted-away,
// and it was leaving the theme page's copy of the card visibly different from the dossier's.
// Gaps render as pills (UNDEFINED), never blank.
import { escapeHtml, fmtPrice, fmtDate, DASH } from "../../lib/format.js";
import { citeMark, withEndnotes } from "../../lib/cites.js";

const mono = (s) => `<span class="mono">${escapeHtml(s)}</span>`;

// sign OUTSIDE the currency mark — "-$10.31", never fmtPrice's "$-10.31"
const money = (v) =>
  typeof v === "number" && isFinite(v)
    ? (v < 0 ? "-$" + Math.abs(v).toFixed(2) : "$" + v.toFixed(2))
    : DASH;

const oneDp = (v, suffix = "") =>
  typeof v === "number" && isFinite(v) ? v.toFixed(1) + suffix : DASH;

const pct = (v) =>
  typeof v === "number" && isFinite(v) ? (v * 100).toFixed(1) + "%" : DASH;

const thousands = (v) =>
  typeof v === "number" && isFinite(v) ? Math.round(v).toLocaleString("en-US") : DASH;

function fact(label, valHtml, { hi = false } = {}) {
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div class="fact-val${hi ? " hi" : ""}">${valHtml}</div></div>`;
}

function verdictFact(c) {
  const v = c.verdict || {};
  const pills = [
    v.status ? `<span class="pill conditional">${escapeHtml(v.status)}</span>` : "",
    c.passFail
      ? `<span class="pill ${c.passFail === "PASS" ? "buy" : "avoid"}">${escapeHtml(c.passFail)}</span>`
      : "",
  ].filter(Boolean).join(" ");
  const rec = v.recorded ? ` <span class="muted">recorded ${escapeHtml(v.recorded)}</span>` : "";
  const caveat = v.avoidPriced
    ? `<div class="fact-caveat">⚠ avoid-priced — ${escapeHtml(v.avoidPricedNote || "")}</div>` : "";
  return fact("Verdict", (pills || `<span class="pill unresolved">pending</span>`) + rec + caveat);
}

function ratioFact(c) {
  if (c.ratioUndefined) {
    return fact("Ratio vs bar",
      `<span class="pill unresolved">UNDEFINED</span> <span class="muted">${escapeHtml(c.ratioUndefined)}</span>`);
  }
  if (typeof c.ratio !== "number") return fact("Ratio vs bar", `<span class="pill unresolved">${DASH}</span>`);
  // the bar comes from the RECORD (stamped by the recipe) — an absent bar renders honest, never
  // an invented 2 (LOW-11: the card carries no fund constants of its own)
  const bar = typeof c.bar === "number" ? `vs ${escapeHtml(String(c.bar))} : 1` : `bar ${DASH}`;
  // TWO ratios, both labeled: what the grid computed at the underwrite's spot, and what the human
  // actually accepted at entry (frozen in the ledger). They differ whenever price moved between
  // the underwrite and the log — showing only one would misreport the accepted asymmetry.
  const v = c.verdict || {};
  const atEntry = (typeof v.ratioAtEntry === "number" && typeof v.entryPrice === "number")
    ? ` <span class="muted">·</span> <span class="mono">${escapeHtml(v.ratioAtEntry.toFixed(2))} : 1</span>
        <span class="muted">at entry ${escapeHtml(fmtPrice(v.entryPrice))}</span>` : "";
  return fact("Ratio vs bar",
    `${mono(c.ratio.toFixed(2) + " : 1")} <span class="muted">${bar} (underwrite)</span>${atEntry}`,
    { hi: true });
}

// DERIVED, never asserted: under a two-point read of the grid, the price sits between the bear
// and base values, so (base − spot) / (base − bear) is the weight the market is putting on the
// bear leg. It is arithmetic ON the card's own numbers — not a probability the fund claims, and
// not a forecast. `spot` comes from the latest COMMITTED monitor mark (dated on screen), never a
// live fetch; with no mark the line renders nothing at all.
function impliedOdds(c, mark) {
  if (!mark || typeof mark.current_price !== "number") return "";
  const leg = (n) => (c.scenarios || []).find((s) => s.name === n);
  const base = leg("base"), bear = leg("bear");
  if (!base || !bear || typeof base.valuePerShare !== "number"
      || typeof bear.valuePerShare !== "number") return "";
  const span = base.valuePerShare - bear.valuePerShare;
  if (!(span > 0)) return "";                    // degenerate grid — say nothing, never divide
  const w = (base.valuePerShare - mark.current_price) / span;
  const note = w < 0 ? " — above base: the market prices better than the base case"
    : w > 1 ? " — below bear: the market prices worse than the bear case" : "";
  return `<div class="uw-odds">Market-implied bear weight at ${escapeHtml(fmtPrice(mark.current_price))}
    (${escapeHtml(fmtDate(mark.current_date))}) =
    (base ${escapeHtml(fmtPrice(base.valuePerShare))} − spot) ÷ (base − bear ${escapeHtml(fmtPrice(bear.valuePerShare))})
    = <b>${(w * 100).toFixed(0)}%</b>${escapeHtml(note)} <span class="muted">— derived from this
    grid at a committed mark; not a forecast.</span></div>`;
}

// the 3-leg matrix: assumptions → value/share → cross-checks. Bull column takes .est-col (the
// existing not-in-the-decision-math tint) — bull is printed for range honesty, never in the ratio.
function legsTable(c) {
  const order = ["bear", "base", "bull"];
  const legs = order.map((n) => (c.scenarios || []).find((s) => s.name === n)).filter(Boolean);
  if (!legs.length) return "";
  const cell = (leg, html) => `<td class="num${leg.name === "bull" ? " est-col" : ""}">${html}</td>`;
  const row = (label, fn, { name = false, mutedLabel = false } = {}) =>
    `<tr${name ? ` class="name-row"` : ""}><td${mutedLabel ? ` class="muted"` : ""}>${escapeHtml(label)}</td>` +
    legs.map((l) => cell(l, fn(l))).join("") + `</tr>`;
  const head = `<tr><th></th>` + legs.map((l) =>
    `<th class="num${l.name === "bull" ? " est-col" : ""}">${escapeHtml(l.name)}</th>`).join("") + `</tr>`;
  const reasons = legs.filter((l) => l.reason).map((l) =>
    `<li><b>${escapeHtml(l.name)}</b> — ${escapeHtml(l.reason)}</li>`).join("");
  const basis = c.multipleBasis || DASH;   // the RECORD stamps its basis; absent renders honest
  return fact(`Scenarios (${basis})`, `
    ${recipeLine(c)}
    <div style="overflow-x:auto;"><table class="data uw-legs-t">
      <thead>${head}</thead>
      <tbody>
        ${row("Revenue ($M)", (l) => thousands(l.revenue))}
        ${row("Op margin", (l) => pct(l.margin))}
        ${row(`Exit ${basis}`, (l) => oneDp(l.multiple, "×"))}
        ${row("Value / share", (l) => money(l.valuePerShare), { name: true })}
        ${row("EV/EBIT (cross-check)", (l) => oneDp(l.evEbit, "×"), { mutedLabel: true })}
        ${row("Norm FCF ($M, cross-check)", (l) => oneDp(l.normFcf), { mutedLabel: true })}
      </tbody>
    </table></div>
    <div class="uw-note muted">bull is printed for range honesty — never in the ratio</div>
    ${reasons ? `<ul class="kv-list" style="margin-top:8px;">${reasons}</ul>` : ""}`);
}

// --- methodology (schema 1.1) ------------------------------------------------------------------
// The recipe chain the record was computed under — stamped into the record from the ONE engine
// constant (midcycle.R1_FORMULA), so what this line SAYS is what scenario_value DID. Absent on
// pre-1.1 records → renders nothing (silence, never a fabricated chain).
function recipeLine(c) {
  const steps = c.recipeFormula || [];
  if (!steps.length) return "";
  return `<div class="uw-recipe mono muted">${steps.map(escapeHtml).join("&nbsp; →&nbsp; ")}</div>`;
}

// Axis → the EXACT legs-table row label + value formatter, so the derivation block and the table
// above it speak one vocabulary. An unknown axis (a future recipe) renders raw — never dropped.
function axisLabel(axis, basis) {
  return axis === "revenue" ? "Revenue ($M)"
    : axis === "margin" ? "Op margin"
    : axis === "multiple" ? `Exit ${basis}` : axis;
}
function axisFmt(axis) {
  return axis === "revenue" ? thousands
    : axis === "margin" ? pct
    : axis === "multiple" ? (v) => oneDp(v, "×") : (v) => String(v);
}
const AXIS_ORDER = ["revenue", "margin", "multiple"];
function orderedAssumptions(c) {
  const rank = (a) => { const i = AXIS_ORDER.indexOf(a.axis); return i < 0 ? 99 : i; };
  return [...(c.assumptions || [])].sort((x, y) => rank(x) - rank(y));
}

// Always-visible: ONE line per axis stating how it was modeled — the reviewer's at-a-glance
// methodology check. The reference numbers live one click deeper (methodRefsDetails).
function methodLines(c) {
  const items = orderedAssumptions(c).map((a) =>
    `<li><b>${escapeHtml(axisLabel(a.axis, c.multipleBasis || DASH))}</b> — ${escapeHtml(a.method)}</li>`);
  return items.length ? `<ul class="kv-list uw-methods">${items.join("")}</ul>` : "";
}

// On-demand: per-axis reference frames, source-cited, with the chosen bear/base/bull trio
// JUXTAPOSED as the closing row (juxtapose, never difference — the reader compares, the machine
// does not editorialize a gap). Own "M" endnote scope INSIDE the <details>: marker and Sources
// list share print fate (the same invariant as the Inputs block).
function methodRefsDetails(c) {
  const withRefs = orderedAssumptions(c).filter((a) => (a.references || []).length);
  if (!withRefs.length) return "";
  const legs = ["bear", "base", "bull"]
    .map((n) => (c.scenarios || []).find((s) => s.name === n)).filter(Boolean);
  const tables = () => withRefs.map((a) => {
    const fmt = axisFmt(a.axis);
    const rows = a.references.map((p) =>
      `<tr><td>${escapeHtml(p.label)}</td><td class="num">${mono(String(p.value))} ${escapeHtml(p.unit)}</td>
        <td class="uw-ref-cite">${citeMark(p.source)}</td></tr>`).join("");
    const chosen = legs.length
      ? `<tr class="name-row"><td>chosen (${legs.map((l) => escapeHtml(l.name)).join(" · ")})</td>
          <td class="num">${legs.map((l) => fmt(l[a.axis])).join(" · ")}</td><td></td></tr>` : "";
    return `<div class="uw-method-h">${escapeHtml(axisLabel(a.axis, c.multipleBasis || DASH))}</div>
      <div style="overflow-x:auto;"><table class="data uw-refs-t"><tbody>${rows}${chosen}</tbody></table></div>`;
  }).join("");
  return `<details class="uw-method"><summary>Reference frames &amp; chosen values</summary>${
    withEndnotes("M", tables)}</details>`;
}

function methodFact(c) {
  const lines = methodLines(c);
  if (!lines) return "";
  return fact("Method", lines + methodRefsDetails(c));
}

// The audit block carries its OWN endnote scope — markers AND their Sources list both live INSIDE
// the <details>, so the two share print fate: collapsed, the whole scope drops out of the PDF
// together; expanded, both print. That is the real invariant the L3/#10 rule protects (a marker
// must never outlive its Sources entry, nor the reverse) — routing these cites into the CARD's
// outer list instead would orphan them in every collapsed-block print.
function inputsDetails(c) {
  const facts = c.facts || [];
  if (!facts.length) return "";
  const rows = () => facts.map((f) => fact(f.key, `${mono(String(f.value))} ${escapeHtml(f.unit || "")}
      <span class="muted">· ${escapeHtml(f.basis || "")}</span>
      ${f.source ? citeMark(f.source) : ""}`)).join("");
  return `<details class="uw-inputs"><summary>Inputs &amp; sources</summary>${
    withEndnotes("I", rows)}</details>`;
}

// uwCard(cardJson) -> HTML string. `ticker:false` drops the ticker from the eyebrow when the host
// page already carries it as its h1 (the dossier degrade).
export function uwCard(c, { ticker = true, mark = null } = {}) {
  if (!c) return "";
  const v = c.verdict || {};
  const recipe = [c.recipeId ? c.recipeId.split("_")[0] : "", c.multipleBasis]
    .filter(Boolean).join(" · ");
  const trig = (v.reunderwriteTriggers || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("");
  const body = () => `
    <h3>Underwrite${ticker ? ` · ${mono(c.ticker)}` : ""}
      <span class="uw-h-sub">${escapeHtml(recipe)}</span></h3>
    ${verdictFact(c)}
    ${ratioFact(c)}
    ${fact("Reward · risk", `${mono(money(c.reward))} · ${mono(money(c.risk))}
      <span class="muted">— base − spot / spot − bear</span>`)}
    ${fact("Spot", `${mono(fmtPrice(c.spot))}
      ${c.spotSource ? citeMark(c.spotSource) : ""}`)}
    ${legsTable(c)}
    ${impliedOdds(c, mark)}
    ${methodFact(c)}
    ${v.rationale ? fact("Rationale", escapeHtml(v.rationale)) : ""}
    ${trig ? fact("Re-underwrite when", `<ul class="kv-list">${trig}</ul>`) : ""}`;
  return `
  <section class="card uw-card">
    ${withEndnotes("U", body)}
    ${inputsDetails(c)}
    <div class="foot uw-foot">underwritten ${escapeHtml(c.underwriteDate || DASH)} · analyst
      ${escapeHtml(c.analyst || DASH)}${c.recipeDesc ? ` · ${escapeHtml(c.recipeDesc)}` : ""}</div>
  </section>`;
}
