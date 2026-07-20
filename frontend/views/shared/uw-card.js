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
import { escapeHtml, fmtPrice, DASH } from "../../lib/format.js";
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
  return fact("Ratio vs bar",
    `${mono(c.ratio.toFixed(2) + " : 1")} <span class="muted">${bar}</span>`,
    { hi: true });
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
export function uwCard(c, { ticker = true } = {}) {
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
