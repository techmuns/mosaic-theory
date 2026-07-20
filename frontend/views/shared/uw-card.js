// UNDERWRITE CARD — the ONE renderer for a first-cut underwrite record (the `scenarioCard` shape
// build.py emits, standalone in frontend/scenarios/ and embedded in theme watchlist entries).
// Canonical components only: .card h3 eyebrow, .fact rows, table.data for the 3-leg matrix,
// .pill (verbatim-cased), .kv-list, inline ↳ .cite, <details>. No private type scale.
//
// CITES follow the dossier's two-mode convention (lib/cites.js), selected by the `cites` option:
//   "inline"  (DEFAULT) every cite renders inline. SAFE for a host that runs no endnote pass —
//             the theme page embeds this card as a supporting exhibit and has no Sources list.
//   "endnote" MAIN-BODY cites emit citeMark placeholders for the host's withEndnotes() pass; the
//             on-demand <details> block STAYS inline either way (print-excluded — an endnote there
//             would leave an orphan [n] in a printed Sources list, pointing at an unseeable marker).
// A host passing "endnote" MUST wrap the result in withEndnotes(), or the placeholder renders "[?]".
// Defaulting to "inline" makes forgetting harmless rather than visibly broken.
// and self-contained on theme pages. Gaps render as pills (UNDEFINED), never blank.
import { escapeHtml, fmtPrice, DASH } from "../../lib/format.js";
import { citeMark } from "../../lib/cites.js";

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

function inputsDetails(c) {
  const facts = c.facts || [];
  if (!facts.length) return "";
  const rows = facts.map((f) => fact(f.key, `${mono(String(f.value))} ${escapeHtml(f.unit || "")}
      <span class="muted">· ${escapeHtml(f.basis || "")}</span>
      ${f.source ? `<span class="cite">${escapeHtml(f.source)}</span>` : ""}`)).join("");
  return `<details class="uw-inputs"><summary>Inputs &amp; sources</summary>${rows}</details>`;
}

// uwCard(cardJson) -> HTML string. `ticker:false` drops the ticker from the eyebrow when the host
// page already carries it as its h1 (the dossier degrade).
// MAIN-BODY provenance — an endnote when the host runs the pass, inline when it doesn't.
function spotCite(ref, cites) {
  if (!ref) return "";
  return cites === "endnote" ? citeMark(ref) : `<span class="cite">${escapeHtml(ref)}</span>`;
}

export function uwCard(c, { ticker = true, cites = "inline" } = {}) {
  if (!c) return "";
  const v = c.verdict || {};
  const recipe = [c.recipeId ? c.recipeId.split("_")[0] : "", c.multipleBasis]
    .filter(Boolean).join(" · ");
  const trig = (v.reunderwriteTriggers || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("");
  return `
  <section class="card uw-card">
    <h3>Underwrite${ticker ? ` · ${mono(c.ticker)}` : ""}
      <span class="uw-h-sub">${escapeHtml(recipe)}</span></h3>
    ${verdictFact(c)}
    ${ratioFact(c)}
    ${fact("Reward · risk", `${mono(money(c.reward))} · ${mono(money(c.risk))}
      <span class="muted">— base − spot / spot − bear</span>`)}
    ${fact("Spot", `${mono(fmtPrice(c.spot))}
      ${spotCite(c.spotSource, cites)}`)}
    ${legsTable(c)}
    ${v.rationale ? fact("Rationale", escapeHtml(v.rationale)) : ""}
    ${trig ? fact("Re-underwrite when", `<ul class="kv-list">${trig}</ul>`) : ""}
    ${inputsDetails(c)}
    <div class="foot uw-foot">underwritten ${escapeHtml(c.underwriteDate || DASH)} · analyst
      ${escapeHtml(c.analyst || DASH)}${c.recipeDesc ? ` · ${escapeHtml(c.recipeDesc)}` : ""}</div>
  </section>`;
}
