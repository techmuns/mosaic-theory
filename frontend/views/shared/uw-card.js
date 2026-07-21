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

const leg = (c, name) => (c.scenarios || []).find((s) => s.name === name) || null;
const num = (v) => (typeof v === "number" && isFinite(v) ? v : null);

// signed % vs spot, e.g. "+95.3%" / "−13.5%" (true minus, not a hyphen)
function vsSpot(value, spot) {
  const v = num(value), s = num(spot);
  if (v === null || s === null || s === 0) return null;
  const p = ((v - s) / s) * 100;
  return (p >= 0 ? "+" : "−") + Math.abs(p).toFixed(1) + "%";
}
const signCls = (value, spot) => {
  const v = num(value), s = num(spot);
  return v === null || s === null ? "" : v >= s ? "pos" : "neg";
};

// --- THE STATE MACHINE ---------------------------------------------------------------------------
// `base_vps` is a COMPUTATION until a human verdict ratifies it; only then is it a target. So the
// headline label is state, not styling — and the fund's constitution decides it, not the renderer's
// taste. Three states, in priority order:
//   priced   — base at/below spot: there is no upside to target, whatever the status says. Reading
//              this as a "target" would invert the meaning of a WERN-shape avoid.
//   target   — a recorded verdict (confirmed / overridden) on a base ABOVE spot.
//   base     — still pending: the number exists, the human has not stood behind it yet.
// The machine never lands in `target` on its own: pending is the only state it can produce.
function headlineState(c) {
  const base = leg(c, "base");
  const bv = num(base && base.valuePerShare), spot = num(c.spot);
  const status = (c.verdict || {}).status || "";
  if (bv !== null && spot !== null && bv <= spot) return "priced";
  return status === "confirmed" || status === "overridden" ? "target" : "base";
}

const STATE_LABEL = {
  target: "Target — base case",
  base: "Base value — target on confirm",
  priced: "Priced — base below spot",
};

// The verdict OF RECORD is the ledger's BUY/AVOID (joined at build). The scenario record has no
// such field, so absent a ledger row the card shows the scenario status and says nothing more.
function verdictPills(c) {
  const v = c.verdict || {};
  const led = c.ledger;
  const out = [];
  if (led && led.verdict) {
    const buy = String(led.verdict).toUpperCase().startsWith("BUY");
    out.push(`<span class="pill ${buy ? "buy" : "avoid"}">${escapeHtml(led.verdict)}</span>`);
  } else if (v.status) {
    out.push(`<span class="pill ${v.status === "pending_analyst" ? "conditional" : "unresolved"}"
      >${escapeHtml(v.status.replace("_", " "))}</span>`);
  }
  return out.join(" ");
}

// PASS/FAIL is the machine's bar test. Once a human verdict is recorded it is subsumed by the
// verdict itself (a recorded BUY that FAILED its bar would be the override, and the status says
// so) — so it renders only while the call is still open, where it is the only signal present.
function ratioCell(c) {
  const open = headlineState(c) !== "target";
  const badge = open && c.passFail
    ? ` <span class="pill ${c.passFail === "PASS" ? "buy" : "avoid"} uw-mini">${escapeHtml(c.passFail)}</span>`
    : "";
  if (c.ratioUndefined) {
    return statCell("Reward : risk",
      `<span class="pill unresolved">UNDEFINED</span>`, escapeHtml(c.ratioUndefined), { txt: true });
  }
  if (typeof c.ratio !== "number") return statCell("Reward : risk", DASH, "no ratio recorded");
  // the bar comes from the RECORD (stamped by the recipe) — an absent bar renders honest, never
  // an invented 2 (LOW-11: the card carries no fund constants of its own)
  const bar = typeof c.bar === "number" ? `vs the ${escapeHtml(String(c.bar))} : 1 bar` : `bar ${DASH}`;
  return statCell("Reward : risk", c.ratio.toFixed(2) + " : 1" + badge, bar);
}

// --- MASTHEAD ------------------------------------------------------------------------------------
// One stat cell: uppercase micro-label / large tabular value / one line of context. `txt` drops the
// value to prose scale (the method cell), `tone` colours it (neg on a downside).
function statCell(label, valHtml, subHtml, { txt = false, tone = "" } = {}) {
  return `<div class="uw-stat">
    <div class="uw-stat-lab">${escapeHtml(label)}</div>
    <div class="uw-stat-val${txt ? " txt" : ""}${tone ? " " + tone : ""}">${valHtml}</div>
    ${subHtml ? `<div class="uw-stat-sub">${subHtml}</div>` : ""}</div>`;
}

// The headline cell — the number the whole card exists to produce, labelled by state.
function headlineCell(c) {
  const st = headlineState(c);
  const base = leg(c, "base");
  const bv = num(base && base.valuePerShare);
  const delta = vsSpot(bv, c.spot);
  const cls = signCls(bv, c.spot);
  const val = `${money(bv)}${delta ? ` <span class="uw-pct ${cls}">${delta}</span>` : ""}`;
  const asOf = c.spotSource ? "" : "";
  const sub = `vs spot ${escapeHtml(fmtPrice(c.spot))}${asOf}`;
  return `<div class="uw-stat uw-stat-lead ${st}">
    <div class="uw-stat-lab uw-eyebrow">${escapeHtml(STATE_LABEL[st])}</div>
    <div class="uw-stat-val lead">${val}</div>
    <div class="uw-stat-sub">${sub}</div></div>`;
}

// Entry — the frozen anchor the forward spread is measured FROM. A verdict that opened no position
// says so plainly rather than rendering an empty slot.
function entryCell(c) {
  const v = c.verdict || {};
  const e = num(v.entryPrice);
  if (e === null) {
    return statCell("Entry", "— no position",
      headlineState(c) === "base" ? "confirm or override sets the target" : "no entry recorded",
      { txt: true });
  }
  const r = num(v.ratioAtEntry);
  const led = c.ledger;
  const sub = [r !== null ? `${r.toFixed(2)} : 1 at entry` : "",
    (led && led.entryPriceAsOf) || v.recorded || ""].filter(Boolean).join(" · ");
  return statCell("Entry", money(e), escapeHtml(sub));
}

// Downside — the risk leg as a percentage, which is how it is actually weighed.
function downsideCell(c) {
  const bear = leg(c, "bear");
  const bv = num(bear && bear.valuePerShare);
  const d = vsSpot(bv, c.spot);
  const floor = bear && typeof bear.margin === "number" ? `margin floor ${pct(bear.margin)}` : "";
  return statCell("Downside — bear", d || DASH, escapeHtml(floor), { tone: "neg" });
}

// Method — a target without its method and implied multiple is a bare assertion. The recipe DESC
// (prose) leads; the recipe ID stays in the provenance foot where an id belongs.
function methodCell(c) {
  const basis = c.multipleBasis || DASH;
  const base = leg(c, "base");
  const m = num(base && base.multiple);
  const desc = c.recipeDesc ? c.recipeDesc.split(":")[0] : `Exit ${basis}`;
  const st = headlineState(c);
  const word = st === "target" ? "target exit" : "base exit";
  // the band reference the multiple was set against, from the committed reference frames — never
  // an interpolated percentile (the card carries no series to compute one from)
  const ref = (c.assumptions || []).find((a) => a.axis === "multiple");
  const med = ref && (ref.references || []).find((p) => /median/i.test(p.label || ""));
  const sub = [m !== null ? `${word} ${oneDp(m, "×")}` : "",
    med ? `vs ${oneDp(med.value, "×")} own-history median` : ""].filter(Boolean).join(" · ");
  return statCell("Method", escapeHtml(desc), escapeHtml(sub), { txt: true });
}

// The foot states WHOSE call this is and where the verdict of record lives — the disclaimer is
// only true while no ledger row exists, so a logged name gets the pointer instead.
function mastheadFoot(c) {
  const v = c.verdict || {};
  const bits = [];
  if (v.recorded) bits.push(`recorded ${escapeHtml(v.recorded)}`);
  if (c.gateAdjudication) bits.push(escapeHtml(c.gateAdjudication));
  if (c.ledger && c.ledger.entryId) {
    bits.push(`ledger ${mono(c.ledger.entryId)}`);
  } else {
    bits.push("scenario verdict — NOT a ledger verdict of record");
  }
  if (v.avoidPriced) {
    bits.push(`⚠ avoid-priced${v.avoidPricedNote ? ` — ${escapeHtml(v.avoidPricedNote)}` : ""}`);
  }
  return `<div class="uw-mast-foot">${bits.join(" · ")}</div>`;
}

function masthead(c, showTicker) {
  return `<div class="uw-mast">
    <div class="uw-mast-head">
      <span class="uw-mast-t">${showTicker ? `${mono(c.ticker)} · ` : ""}Scenario underwrite
        <span class="muted">${escapeHtml(c.multipleBasis || "")}</span></span>
      <span class="uw-mast-pills">${verdictPills(c)}</span>
    </div>
    <div class="uw-statband">
      ${headlineCell(c)}
      ${ratioCell(c)}
      ${entryCell(c)}
      ${downsideCell(c)}
      ${methodCell(c)}
    </div>
    ${mastheadFoot(c)}
  </div>`;
}

// --- RISK / REWARD LADDER -------------------------------------------------------------------------
// The asymmetry, drawn to scale: the risk and reward zone WIDTHS are the ratio, so the shape is
// readable before a single number is. Degenerate legs (bear at/above spot → risk undefined) render
// the track with no zones and print `ratio_undefined` verbatim — fail-honest, never a drawn lie.
function ladder(c) {
  const b = num((leg(c, "bear") || {}).valuePerShare);
  const m = num((leg(c, "base") || {}).valuePerShare);
  const u = num((leg(c, "bull") || {}).valuePerShare);
  const s = num(c.spot);
  if (b === null || m === null || s === null) return "";
  const lo = Math.min(b, m, s, u === null ? m : u);
  const hi = Math.max(b, m, s, u === null ? m : u);
  if (!(hi > lo)) return "";
  const at = (v) => ((v - lo) / (hi - lo)) * 100;
  const st = headlineState(c);
  const zones = c.ratioUndefined || b >= s ? "" : `
    <div class="uw-lad-risk" style="left:${at(b)}%; width:${at(s) - at(b)}%;"></div>
    <div class="uw-lad-reward" style="left:${at(s)}%; width:${Math.max(0, at(m) - at(s))}%;"></div>`;
  const lab = (v, name, cls) => {
    const d = vsSpot(v, s);
    const pos = at(v);
    // labels near the right edge anchor from the right so nothing clips out of the track
    const side = pos > 88 ? `right:${(100 - pos).toFixed(2)}%` : `left:${pos.toFixed(2)}%`;
    const align = pos > 88 ? " end" : "";
    return `<span class="uw-lad-lab ${cls}${align}" style="${side}">
      ${mono(v.toFixed(2))}<span class="n">${escapeHtml(name)}</span>${
      d ? `<span class="uw-pct ${signCls(v, s)}">${d}</span>` : ""}</span>`;
  };
  const tgtName = st === "target" ? "TARGET" : st === "priced" ? "base (priced)" : "base";
  return `<div class="uw-ladder">
    <div class="uw-lad-track">
      ${zones}
      <span class="uw-lad-tick bear" style="left:${at(b)}%;"></span>
      <span class="uw-lad-tick spot" style="left:${at(s)}%;"></span>
      <span class="uw-lad-tick base ${st}" style="left:${at(m)}%;"></span>
      ${u === null ? "" : `<span class="uw-lad-tick bull" style="left:${at(u)}%;"></span>`}
      ${lab(b, "bear", "above")}
      <span class="uw-lad-lab below" style="left:${at(s).toFixed(2)}%;">
        ${mono(s.toFixed(2))}<span class="n">spot</span></span>
      ${lab(m, tgtName, "above " + st)}
      ${u === null ? "" : lab(u, "bull", "above")}
    </div>
    <div class="uw-lad-zone">
      <span>${c.ratioUndefined ? escapeHtml(c.ratioUndefined)
        : `risk ${escapeHtml(money(c.risk))}`}</span>
      <span>${c.ratioUndefined ? "" : `reward ${escapeHtml(money(c.reward))} — zone widths to scale`}</span>
    </div>
  </div>`;
}

// the 3-leg matrix: assumptions → value/share → cross-checks. Bull column takes .est-col (the
// existing not-in-the-decision-math tint) — bull is printed for range honesty, never in the ratio.
function legsTable(c) {
  const order = ["bear", "base", "bull"];
  const legs = order.map((n) => (c.scenarios || []).find((s) => s.name === n)).filter(Boolean);
  if (!legs.length) return "";
  // the base column carries the decision — tinted when it IS the target, plain while pending
  const tgt = headlineState(c) === "target";
  const colCls = (l) => (l.name === "bull" ? " est-col" : l.name === "base" && tgt ? " uw-tgt-col" : "");
  const cell = (leg, html, extra = "") =>
    `<td class="num${colCls(leg)}${extra}">${html}</td>`;
  const row = (label, fn, { name = false, mutedLabel = false, cls = "" } = {}) =>
    `<tr${name ? ` class="name-row"` : ""}><td${mutedLabel ? ` class="muted"` : ""}>${escapeHtml(label)}</td>` +
    legs.map((l) => cell(l, fn(l), cls)).join("") + `</tr>`;
  const head = `<tr><th></th>` + legs.map((l) =>
    `<th class="num${colCls(l)}">${escapeHtml(l.name)}${
      l.name === "base" && tgt ? ` <span class="uw-tgt-tag">target</span>` : ""}</th>`).join("") + `</tr>`;
  const reasons = legs.filter((l) => l.reason).map((l) =>
    `<li><b>${escapeHtml(l.name)}</b> — ${escapeHtml(l.reason)}</li>`).join("");
  const basis = c.multipleBasis || DASH;   // the RECORD stamps its basis; absent renders honest
  const delta = (l) => {
    const d = vsSpot(l.valuePerShare, c.spot);
    return d ? `<span class="uw-pct ${signCls(l.valuePerShare, c.spot)}">${d}</span>` : DASH;
  };
  // DECISION VALUES LEAD: value/share then its % vs spot, before the inputs that produced them.
  return fact(`Scenarios (${basis})`, `
    <div style="overflow-x:auto;"><table class="data uw-legs-t">
      <thead>${head}</thead>
      <tbody>
        ${row("Value / share", (l) => money(l.valuePerShare), { name: true })}
        ${row("vs spot", delta, { cls: " uw-vs" })}
        ${row("Revenue ($M)", (l) => thousands(l.revenue))}
        ${row("Op margin", (l) => pct(l.margin))}
        ${row(`Exit ${basis}`, (l) => oneDp(l.multiple, "×"))}
        ${row("EV/EBIT (cross-check)", (l) => oneDp(l.evEbit, "×"), { mutedLabel: true })}
        ${row("Norm FCF ($M, cross-check)", (l) => oneDp(l.normFcf), { mutedLabel: true })}
      </tbody>
    </table></div>
    <div class="uw-note muted">bull is range context — never in the ratio${
      tgt ? ", never the target" : ""}</div>
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
  return `<details class="uw-method"><summary>References &amp; chosen values</summary>${
    withEndnotes("M", tables)}${recipeLine(c)}</details>`;
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
export function uwCard(c, { ticker = true } = {}) {
  if (!c) return "";
  const v = c.verdict || {};
  const trig = (v.reunderwriteTriggers || []).map((t) =>
    `<span class="uw-chip">${escapeHtml(t)}</span>`).join("");
  // The masthead leads: the target/base number, the asymmetry, the entry, the downside, the method
  // — the five things a reader needs before deciding whether to read on. The spot cite rides in
  // the headline cell so the price on screen still resolves to its source.
  const body = () => `
    ${masthead(c, ticker)}
    ${c.spotSource ? `<div class="uw-spot-cite muted">spot ${mono(fmtPrice(c.spot))} ${
      citeMark(c.spotSource)}</div>` : ""}
    ${ladder(c)}
    ${legsTable(c)}
    ${methodFact(c)}
    ${v.rationale ? fact("Rationale", escapeHtml(v.rationale)) : ""}
    ${trig ? `<div class="uw-trig"><span class="uw-trig-lab">${
      headlineState(c) === "target" ? "Thesis breaks" : "Re-underwrite when"}</span>${trig}</div>` : ""}`;
  return `
  <section class="card uw-card">
    ${withEndnotes("U", body)}
    ${inputsDetails(c)}
    <div class="foot uw-foot">underwritten ${escapeHtml(c.underwriteDate || DASH)} · analyst
      ${escapeHtml(c.analyst || DASH)}${c.recipeId ? ` · recipe ${escapeHtml(c.recipeId)}` : ""}</div>
  </section>`;
}
