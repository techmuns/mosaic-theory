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

// ONE word in the rating box — the qualifier moves to the sub-line. "Target — base case" was
// tautological with the legs table's own "base · target" header directly beneath it.
const STATE_LABEL = { target: "Target", base: "Base value", priced: "Priced" };
const STATE_NOTE = { target: "", base: "target on confirm", priced: "base below spot" };

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
  // #165's two-ratio rule, kept under the masthead layout: the UNDERWRITE ratio lives here
  // (labelled), the AT-ENTRY ratio lives in the Entry cell — both shown, neither misreported.
  const bar = typeof c.bar === "number"
    ? `at underwrite · vs the ${escapeHtml(String(c.bar))} : 1 bar` : `at underwrite · bar ${DASH}`;
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
  // the spot CITE rides here, on the first and highest-prominence statement of the price. It used
  // to sit on its own line below the masthead — a citation that had lost its home when the
  // masthead replaced the old "Spot" fact row, restating a price the tile states one line above
  // and breaking the price/target pairing a tear-sheet header exists to make.
  const sub = [STATE_NOTE[st], `vs spot ${escapeHtml(fmtPrice(c.spot))}${
    c.spotSource ? " " + citeMark(c.spotSource) : ""}`].filter(Boolean).join(" · ");
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
  // terse on purpose: the cell is ~190px, and a sub that wraps costs a line on EVERY cell in the
  // band (they share a row height) — the long forms live in the table and the foot
  const sub = [r !== null ? `${r.toFixed(2)} : 1` : "",
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
    med ? `vs ${oneDp(med.value, "×")} median` : ""].filter(Boolean).join(" · ");
  return statCell("Method", escapeHtml(desc), escapeHtml(sub), { txt: true });
}

// A strip under the band for what the reader must WEIGH — a gate the human overrode, an inverted
// asymmetry, or the absence of a ledger verdict of record. It renders only when it has something
// to say. It used to also carry `recorded`/`ledger id`, which made it a permanent metadata rail
// duplicating the card foot's job: two metadata strips, one under the band and one at the bottom.
// Those moved to the foot, where the card's other metadata already lives.
function mastheadFoot(c) {
  const v = c.verdict || {};
  const bits = [];
  if (c.gateAdjudication) bits.push(escapeHtml(c.gateAdjudication));
  // only meaningful while no ledger row exists — a logged name says so in the foot instead
  if (!(c.ledger && c.ledger.entryId) && v.status && v.status !== "pending_analyst") {
    bits.push("scenario verdict — NOT a ledger verdict of record");
  }
  if (v.avoidPriced) {
    bits.push(`⚠ avoid-priced${v.avoidPricedNote ? ` — ${escapeHtml(v.avoidPricedNote)}` : ""}`);
  }
  return bits.length ? `<div class="uw-mast-foot">${bits.join(" · ")}</div>` : "";
}

// A bare green "BUY" chip in a report header IS the sell-side ratings idiom — a reader parses it
// as a recommendation. Here it is the HUMAN's verdict of record, sealed in the append-only ledger
// and explicitly not a machine call, so the header says which it is. It also restores the band's
// label-over-value grammar (every other cell has a micro-label) and repairs the weak states:
// "Verdict · pending analyst" reads as a state; a lone grey chip reads as an error.
function masthead(c, showTicker) {
  const pills = verdictPills(c);
  return `<div class="uw-mast">
    <div class="uw-mast-head">
      <span class="uw-mast-t">${showTicker ? `${mono(c.ticker)} · ` : ""}Scenario underwrite
        <span class="muted">${escapeHtml(c.multipleBasis || "")}</span></span>
      ${pills ? `<span class="uw-mast-pills"><span class="uw-vlab">Verdict</span>${pills}</span>` : ""}
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

// --- RANGE RAIL -----------------------------------------------------------------------------------
// The bear/base/bull bar BESIDE the scenario table — one row of a football field, kept horizontal
// (the conventional read; a vertical bar is not a research object). The zone widths are still the
// ratio drawn to scale. The table's height gives this slot ~130px of vertical room, so each label
// takes its OWN row, tied to its tick by a hairline lead — their widths stop competing, which is
// what forced the old full-width single-row ladder. FOUR labels is this layout's ceiling: a fifth
// has no row to take.
// Degenerate legs (bear at/above spot → risk undefined) render the track with no zones and print
// `ratio_undefined` verbatim in the foot — fail-honest, never a drawn lie.
function rangeRail(c) {
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
  // a centred label at either extreme would hang outside the slot — near an edge it anchors
  // flush. The threshold is set by the WIDEST label's half-width (~130px target ≈ 19% of the
  // 337px track): a tick in the 12–20% band with a centred label would clip into the rail's
  // border, so anything inside 20% of an edge anchors to it. The LEAD is unaffected — it stays
  // at the true tick position, so an edge-anchored label still points at its mark.
  const place = (pos) => (pos <= 20 ? "left:0"
    : pos >= 80 ? "right:0" : `left:${pos.toFixed(2)}%`);
  const anchor = (pos) => (pos > 20 && pos < 80 ? " mid" : "");
  const lab = (v, name, row, cls = "", { delta = true } = {}) => {
    const d = delta ? vsSpot(v, s) : null;   // spot carries no delta against itself
    const pos = at(v);
    return `<span class="uw-rr-lab r${row}${anchor(pos)}${cls}" style="${place(pos)}">
      ${mono(v.toFixed(2))}<span class="n">${escapeHtml(name)}</span>${
      d ? `<span class="uw-pct ${signCls(v, s)}">${d}</span>` : ""}</span>`;
  };
  // fixed row grid (px from the stack top): labels at 0 / 28 / 86 / 110, track at 62.
  // Each lead runs from its label's row to the track at the TICK's x — the stagger costs nothing
  // if the eye can trace label to position.
  const lead = (pos, top, height) =>
    `<span class="uw-rr-lead" style="${pos >= 99 ? "right:0" : `left:${pos.toFixed(2)}%`}; top:${top}px; height:${height}px;"></span>`;
  const tgtName = st === "target" ? "TARGET" : st === "priced" ? "base (priced)" : "base";
  return `<div class="uw-rail">
    <div class="uw-sec-h">Range vs spot</div>
    <div class="uw-rr">
      ${lab(m, tgtName, 1, " t " + st)}
      ${u === null ? "" : lab(u, "bull", 2)}
      ${lead(at(m), 16, 46)}
      ${u === null ? "" : lead(at(u), 44, 18)}
      <div class="uw-rr-track">
        ${zones}
        <span class="uw-lad-tick bear" style="left:${at(b)}%;"></span>
        <span class="uw-lad-tick spot" style="left:${at(s)}%;"></span>
        <span class="uw-lad-tick base ${st}" style="left:${at(m)}%;"></span>
        ${u === null ? "" : `<span class="uw-lad-tick bull" style="left:${at(u)}%;"></span>`}
      </div>
      ${lead(at(b), 70, 16)}
      ${lab(b, "bear", 3)}
      ${lead(at(s), 70, 40)}
      ${lab(s, "spot", 4, "", { delta: false })}
    </div>
    <div class="uw-rr-foot">${c.ratioUndefined
      ? `<div class="row"><span class="k">${escapeHtml(c.ratioUndefined)}</span></div>`
      : `<div class="row"><span class="k">Reward</span><span class="val">${escapeHtml(money(c.reward))}</span></div>
         <div class="row"><span class="k">Risk</span><span class="val">${escapeHtml(money(c.risk))}</span></div>`}
    </div>
  </div>`;
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
  const basis = c.multipleBasis || DASH;   // the RECORD stamps its basis; absent renders honest
  const delta = (l) => {
    const d = vsSpot(l.valuePerShare, c.spot);
    return d ? `<span class="uw-pct ${signCls(l.valuePerShare, c.spot)}">${d}</span>` : DASH;
  };
  // DECISION VALUES LEAD: value/share then its % vs spot, before the inputs that produced them.
  // The table shares its row with the range rail (SPLIT layout): the old full-width table carried
  // ~350px of dead column while the ladder occupied a full-width band of its own — side by side,
  // the table's columns size to their ink and the rail reuses the table's height. No fact() label
  // column here: it would starve both halves; each half carries its own section heading.
  const rail = rangeRail(c);
  const tableHtml = `
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
      tgt ? ", never the target" : ""}</div>`;
  const main = `<div class="uw-split-main">
      <div class="uw-sec-h">Scenarios <span class="basis">${escapeHtml(basis)}</span></div>
      ${tableHtml}</div>`;
  return rail ? `<div class="uw-split">${main}${rail}</div>` : main;
}

// The per-leg reasoning, full card width, placed AFTER the rationale + thesis-breaks: the read
// order runs verdict-level first (why the position, what breaks it), then leg-level (why each
// number), then methodology. Collapsed on screen; the print carve-out forces it into the PDF —
// a printed grid with no justification would contradict the no-reason-no-compute rule.
function legReasons(c) {
  const reasons = ["bear", "base", "bull"]
    .map((n) => leg(c, n)).filter((l) => l && l.reason)
    .map((l) => `<li><b>${escapeHtml(l.name)}</b> — ${escapeHtml(l.reason)}</li>`).join("");
  if (!reasons) return "";
  return `<details class="uw-reasons">
      <summary>Why each leg sits where it does — the analyst's reasoning</summary>
      <div class="uw-reasons-body"><ul class="kv-list">${reasons}</ul></div></details>`;
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
  return `<details class="uw-method"><summary>Reference values — what each assumption was set against</summary>${
    withEndnotes("M", tables)}${recipeLine(c)}</details>`;
}

// COLLAPSED by default: this is per-axis METHODOLOGY, one step toward provenance, and the
// masthead's Method cell already carries the headline. Unlike the leg reasons (which justify the
// numbers in the table and therefore belong in the printed record), methodology is audit-tier —
// so the normal `details:not([open])` print exclusion is the correct fate here.
function methodFact(c) {
  const lines = methodLines(c);
  if (!lines) return "";
  // no fact() wrapper: a "Method" label over a summary that says "How each axis was modeled"
  // is the same word twice — the summary IS the label
  return `<details class="uw-method-block">
    <summary>How each axis was modeled — revenue, margin and multiple methodology</summary>
    <div>${lines}${methodRefsDetails(c)}</div></details>`;
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
  return `<details class="uw-inputs"><summary>Inputs &amp; sources — the recorded facts behind the math</summary>${
    withEndnotes("I", rows)}</details>`;
}

// uwCard(cardJson) -> HTML string. `ticker:false` drops the ticker from the eyebrow when the host
// page already carries it as its h1 (the dossier degrade).
export function uwCard(c, { ticker = true, mark = null } = {}) {
  if (!c) return "";
  const v = c.verdict || {};
  const trig = (v.reunderwriteTriggers || []).map((t) =>
    `<span class="uw-chip">${escapeHtml(t)}</span>`).join("");
  // The masthead leads: the target/base number, the asymmetry, the entry, the downside, the method
  // — the five things a reader needs before deciding whether to read on. The spot cite rides in
  // the headline cell so the price on screen still resolves to its source.
  // ORDER: decision content runs contiguously (the answer, its shape, its derivation, its
  // reasoning, and what would break it), THEN the audit tier. Method sat between the table and the
  // rationale, putting a collapsed block in the middle of the decision read; grouped with the
  // other audit blocks it stops interrupting and starts belonging.
  const body = () => `
    ${masthead(c, ticker)}
    ${legsTable(c)}
    ${impliedOdds(c, mark)}
    ${v.rationale ? fact("Rationale", escapeHtml(v.rationale)) : ""}
    ${trig ? `<div class="uw-trig"><span class="uw-trig-lab">${
      headlineState(c) === "target" ? "Thesis breaks" : "Re-underwrite when"}</span>${trig}</div>` : ""}
    ${legReasons(c)}
    ${methodFact(c)}`;
  return `
  <section class="card uw-card">
    ${withEndnotes("U", body)}
    ${inputsDetails(c)}
    <div class="foot uw-foot">underwritten ${escapeHtml(c.underwriteDate || DASH)} · analyst
      ${escapeHtml(c.analyst || DASH)}${c.recipeId ? ` · recipe ${escapeHtml(c.recipeId)}` : ""}${
      v.recorded ? ` · verdict recorded ${escapeHtml(v.recorded)}` : ""}${
      c.ledger && c.ledger.entryId ? ` · ledger ${mono(c.ledger.entryId)}` : ""}</div>
  </section>`;
}
