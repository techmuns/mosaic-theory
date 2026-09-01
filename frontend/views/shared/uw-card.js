// UNDERWRITE CARD — the ONE renderer for a first-cut underwrite record (the `scenarioCard` shape
// build.py emits, standalone in frontend/scenarios/ and embedded in theme watchlist entries).
// Canonical components only: .card h3 eyebrow, .fact rows, table.data for the 3-leg matrix,
// .pill (verbatim-cased), .kv-list, inline ↳ .cite, <details>. No private type scale.
//
// CITES: the card OWNS its citations (lib/cites.js) and renders identically on every surface — no
// host has to run an endnote pass, and there is no mode to get wrong. TWO scopes, because print
// fate differs:
//   main body   withEndnotes("U", …) — its Sources list sits inside the card, right after the body.
//   <details>   withEndnotes("I", …) — marker AND list both INSIDE the block, so they share
//               fate on every surface (T1-amended 2026-07-21: print force-opens all details, so
//               both PRINT together; an [I n] resolving into the card's outer list would still
//               split them on screen).
// Earlier this was gated on a `cites` option so a host with no pass wouldn't render "[?]". That
// knob is gone: self-contained scopes make the failure impossible instead of merely defaulted-away,
// and it was leaving the theme page's copy of the card visibly different from the dossier's.
// Gaps render as pills (UNDEFINED), never blank.
import { escapeHtml, fmtPrice, fmtDate, DASH, tierPill } from "../../lib/format.js";
import { isBuyVerdict } from "../../lib/snapshots.js";
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
// A leg row belongs on the card when the RECORD ACTUALLY CARRIES ITS NUMBER — asked of the legs,
// never of a recipe list, so a recipe added later needs no edit here and cannot be forgotten.
// Every formatter already renders a missing number as an em-dash, so the failure this prevents is
// not `undefined` on the page: it is a P/E card printing "Revenue —, Op margin —" and NO EPS row,
// showing every input except the one that produced its value. That is the same half-wiring as the
// emitter fix in `frontend/build.py` (review of #542) — which emitted `eps` while this file, its
// only consumer, still had nowhere to display it.
const hasLegField = (c, k) =>
  (c.scenarios || []).some((s) => typeof s[k] === "number" && isFinite(s[k]));
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
    const buy = isBuyVerdict(led.verdict);
    // the BOOK, when it is not the default — a verdict word alone cannot tell a quality PASS
    // ("not at this price") from an overshoot AVOID_TERMINAL ("this is dying").
    const book = led.sleeve
      ? ` <span class="ds-lean" title="judged under the ${escapeHtml(led.sleeve)} book">${escapeHtml(led.sleeve)}</span>`
      : "";
    // CLOSE-AWARE (external-honesty pass 2026-07-27): a position that has been closed NEVER
    // headlines as a bare live verdict. The word of record stays (the call is still scored at its
    // horizon — exits cannot launder the track record), but it reads with its close attached.
    const cl = led.closed;
    const word = cl
      ? `${escapeHtml(led.verdict)} — closed ${escapeHtml(cl.exitPriceAsOf || "")}` +
        (typeof cl.exitPrice === "number" ? ` at $${cl.exitPrice.toFixed(2)}` : "")
      : escapeHtml(led.verdict);
    out.push(`<span class="pill ${cl ? "unresolved" : buy ? "buy" : "avoid"}">${word}</span>${book}`);
  } else if (v.status) {
    out.push(`<span class="pill ${v.status === "pending_analyst" ? "conditional" : "unresolved"}"
      >${escapeHtml(v.status.replace("_", " "))}</span>`);
  }
  // TIER rides beside the status: it is a standing property of the business, not an audit detail,
  // and it is what the reader weighs the verdict's confidence against.
  const t = tierBadge(c);
  if (t) out.push(t);
  // (2026-07-27, operator) The header is the RATING and nothing else. The holding label was
  // removed because the band already carries it: the ENTRY cell reads "— no position" for a
  // record that holds nothing, and a closed position states its close inside the verdict chip
  // itself. Saying it again beside the chip was the same redundancy the caption had.
  return out.join(" ");
}

// PASS/FAIL is the machine's bar test. Once a human verdict is recorded it is subsumed by the
// verdict itself (a recorded BUY that FAILED its bar would be the override, and the status says
// so) — so it renders only while the call is still open, where it is the only signal present.
// THE TIERED LADDER (2026-08-21): `tierPill` lives in lib/format.js so this card and the themes
// watchlist render one vocabulary. A record WITHOUT `gateRegime` was judged under the 2:1/15%
// booleans alone and keeps the legacy PASS/FAIL pills (mastheadFoot says which regime applied).
function ratioCell(c) {
  const open = headlineState(c) !== "target";
  // new-regime records carry `asymmetryTier`; the tier pill replaces the bare PASS/FAIL — which
  // also retires this card's half of the PASS-chip / Verdict.PASS vocabulary collision.
  const badge = open && c.asymmetryTier ? tierPill(c.asymmetryTier)
    : open && c.passFail
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
  const ceil = (c.currentState || {}).ceiling2to1;
  const lim = (c.currentState || {}).limit;
  // new-regime sub-line names BOTH lines (eligibility + preferred); legacy keeps the bar wording
  const bar = (typeof c.eligibleRatio === "number" && typeof c.bar === "number"
    ? `at underwrite · eligible ≥${escapeHtml(String(c.eligibleRatio))} : 1 · preferred ≥${
        escapeHtml(String(c.bar))} : 1`
    : typeof c.bar === "number"
      ? `at underwrite · vs the ${escapeHtml(String(c.bar))} : 1 bar` : `at underwrite · bar ${DASH}`)
    // the eligibility ceiling rides beside the 2:1 ceiling when present
    + (typeof c.ceilingEligible === "number" ? ` · elig. ceiling $${c.ceilingEligible.toFixed(2)}` : "")
    // the price at which the ratio decays to the bar — a qualifier ON this cell, so it belongs in
    // this cell's sub-line rather than in a block of its own.
    + (typeof ceil === "number" ? ` · ceiling $${ceil.toFixed(2)}` : "")
    // the STATED limit beside the computed ceiling — the pair is the information, and the gap is
    // the conservatism the analyst added. Absent renders nothing; it never borrows the ceiling.
    + (typeof lim === "number" ? ` · limit $${lim.toFixed(2)}`
       // a DEFERRAL renders as a deferral. Falling through to "" here would make a deliberate
       // absence indistinguishable from never having looked.
       : (c.currentState || {}).limitDeferred ? " · limit deferred" : "");
  return statCell("Reward : risk", c.ratio.toFixed(2) + " : 1" + badge, bar);
}

// THE SECOND TEST, its own cell beside the ratio (2026-08-05). The house convention is nominal
// 2:1 AND a base-case IRR floor AND a stated horizon; both must pass and IRR NEVER REPLACES
// ASYMMETRY, so it renders as a PEER of the ratio rather than a footnote under it.
//
// A record with no horizon renders UNDEFINED WITH ITS REASON rather than rendering nothing: an
// absent IRR line is indistinguishable from one that passed, and every R1 record committed before
// this convention is exactly that case. The horizon prints WITH the rate — a return without the
// period it is earned over is not a number a reader can act on, which is the same error the
// R2 PV/nominal split exists to prevent.
function irrCell(c) {
  const open = headlineState(c) !== "target";
  if (typeof c.irr !== "number") {
    if (!c.irrUndefined) return "";                  // pre-convention record: no cell at all
    return statCell("Base IRR", `<span class="pill unresolved">UNDEFINED</span>`,
      escapeHtml(c.irrUndefined), { txt: true });
  }
  // new-regime records carry `returnTier`; same pill-over-boolean swap as ratioCell
  const badge = open && c.returnTier ? tierPill(c.returnTier)
    : open && c.irrPassFail
      ? ` <span class="pill ${c.irrPassFail === "PASS" ? "buy" : "avoid"} uw-mini">${escapeHtml(c.irrPassFail)}</span>`
      : "";
  const sub = (typeof c.eligibleIrr === "number" && typeof c.irrFloor === "number"
    ? `eligible ≥${(c.eligibleIrr * 100).toFixed(0)}% · preferred ≥${(c.irrFloor * 100).toFixed(0)}%`
    : typeof c.irrFloor === "number"
      ? `vs the ${(c.irrFloor * 100).toFixed(0)}% floor` : `floor ${DASH}`)
    + (typeof c.horizonYears === "number" ? ` · over ${c.horizonYears}y` : "");
  return statCell("Base IRR", (c.irr * 100).toFixed(1) + "%" + badge, sub);
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
  // (item 1e) NO DATE IS STAMPED ON THIS PRICE, deliberately — see the review finding below.
  //
  // A first cut appended ` @ ${c.underwriteDate}`. That is FALSE on 6 of 6 committed records:
  // `underwriteDate` is when the call was FROZEN, and the close it was struck on is 1-5 days
  // older (SMPL 10.53 is a 07-22 close under a 07-27 underwrite date; IT 3d; AORT 2d; MVST,
  // NCNO, EPAM 1d). It reproduced audit P4 verbatim — "the page asserts 'underwritten 07-27'
  // over a 07-22 price" — and beside a live `CMP $10.22 (2026-07-24)` it made the FROZEN value
  // look NEWER than the live one, which is worse than leaving it undated.
  //
  // The struck date exists only inside `spotSource`, analyst free text phrased differently per
  // record ("Polygon daily aggregate close 2026-07-22 (store; latest bar at reissue)"). Parsing
  // it would be exactly the banned display-string parse. The honest surface is the CITE, which
  // already carries that text verbatim — so the date reaches the reader unparsed. A structured
  // `spot_as_of` on ScenarioRecord is the real fix and is queued.
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
  // an interpolated percentile (the card carries no series to compute one from).
  // (schema 1.3) selected by ROLE, never by label prose. The label regex this replaces picked
  // whichever label mentioned the word FIRST: on MVST that was the PEER median of a heterogeneous
  // set while the own-history median sat two rows down marked unusable, so which comparator the
  // masthead showed was decided by array order. `role === "median"` is the own-history median by
  // vocabulary (peer medians are `peer_median`), excluded rows never qualify, and an untagged
  // legacy record honestly shows no sub-line rather than a guessed one.
  const ref = (c.assumptions || []).find((a) => a.axis === "multiple");
  const med = ref && (ref.references || []).find((p) => p.role === "median" && !p.excluded);
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
  const s = c.currentState || {};
  const bits = [];
  // (at-a-glance v2, 2026-07-27) VINTAGE + FORWARD DATES live here, at the band's lowest weight.
  // They were briefly proposed as a 6th stat cell — wrong twice over: `.uw-statband` is
  // repeat(5,1fr), so a 6th cell drops Method to a ragged second row; and a DATE rendered at the
  // 16.5px mono of `.uw-stat-val` reads with the authority of a valuation number. This slot
  // already existed for exactly this class of fact.
  const ne = s.nextEvidence || {};
  if (ne.date && ne.date !== "UNKNOWN") {
    // the event label already NAMES the event ("Next results print"), so prefixing it with
    // "Next evidence" said Next twice. Strip the label's own "Next " and lead with the event.
    const what = String(ne.what || "").replace(/^next\s+/i, "").trim();
    const lead = what ? what.charAt(0).toUpperCase() + what.slice(1) : "Next evidence";
    bits.push(`${escapeHtml(lead)} ${escapeHtml(ne.date)}`);
  }
  if (s.underwriteDate) bits.push(`underwritten ${escapeHtml(s.underwriteDate)}`);
  // THE TIERED LADDER (2026-08-21): the regime + eligibility verdict, at the band's lowest
  // weight — a fact about how the record was judged, not a valuation number. A record without
  // `gateRegime` was judged under the 2:1/15% booleans alone, and the foot SAYS so: absence must
  // never read as the tiers having been applied and passed.
  if (c.gateRegime) {
    const el = c.eligible === true ? "ELIGIBLE"
      : c.eligible === false ? "BELOW ELIGIBILITY"
        : `eligibility UNDEFINED${c.eligibleUndefined ? ` — ${escapeHtml(c.eligibleUndefined)}` : ""}`;
    bits.push(`${el} · gate regime ${escapeHtml(c.gateRegime)}`);
    if (c.irrConvention) bits.push(`IRR ${escapeHtml(c.irrConvention)}`);
  } else if (c.gate) {
    bits.push("judged under the 2:1 / 15% regime (pre-2026-08-21)");
  }
  if (c.gateAdjudication) bits.push(escapeHtml(c.gateAdjudication));
  // only meaningful while no ledger row exists — a logged name says so in the foot instead
  if (!(c.ledger && c.ledger.entryId) && v.status && v.status !== "pending_analyst") {
    bits.push("no ledger verdict logged");
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
function masthead(c, showTicker, { eyebrow = true } = {}) {
  const pills = verdictPills(c);
  return `<div class="uw-mast">
    ${eyebrow ? `<div class="uw-mast-head">
      <span class="uw-mast-t">${showTicker ? `${mono(c.ticker)} · ` : ""}Scenario underwrite
        <span class="muted">${escapeHtml(c.multipleBasis || "")}</span></span>
      ${pills ? `<span class="uw-mast-pills"><span class="uw-vlab">Verdict</span>${pills}</span>` : ""}
    </div>` : ""}
    <div class="uw-statband">
      ${headlineCell(c)}
      ${ratioCell(c)}
      ${irrCell(c)}
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

// --- R2 (terminal-margin) ----------------------------------------------------------------------
// An R2 record values a business in the year it reaches a normal margin and discounts that back, so
// the card must show BOTH numbers: the terminal value the analyst modelled and its present value,
// which is the one the ratio uses. Showing only the terminal number would compare a five-year story
// against a price paid today; showing only the PV would hide what was actually assumed.
const isR2 = (c) => (c.recipeId || "").startsWith("R2");
// EV/Revenue values a business with NO profits to value: revenue × multiple, full stop. Margin and
// D&A never enter that arithmetic, so the card must not print them as though they did — a driver
// row beside a value it did not produce reads as evidence, and the reader cannot tell it is inert.
// The record makes this cheap to honour: those fields are absent, not zero.
const onRevenueBasis = (c) => (c.multipleBasis || "") === "EV/Revenue";

// TIER is a property of the BUSINESS, not of the answer — it feeds confidence and never the bar.
function tierBadge(c) {
  if (!c.tier) return "";
  const b = c.tier === "A";
  return `<span class="uw-tier ${b ? "uw-tier-a" : "uw-tier-b"}" title="${
    b ? "contracted or recurring revenue, gross-profitable, self-funded to breakeven"
      : "survival-gated or unproven unit economics"}">tier ${escapeHtml(c.tier)}</span>`;
}

// THE SURVIVAL GATE, with its arithmetic shown rather than its verdict asserted. A terminal value
// is worthless if the company never reaches the terminal year, so a FAIL is rendered as a blocking
// state — it is what stops a confirmed BUY in the record, and the card must not read softer than
// the guard behaves.
function survivalPanel(c) {
  const s = c.survival;
  if (!s) return "";
  const fail = s.status === "FAIL";
  const rows = [];
  if (s.burn != null) {
    rows.push(fact("Cash burn", `${money(s.burn)} a year`
      + (s.burnBasis ? ` <span class="muted">${escapeHtml(s.burnBasis)}</span>` : "")));
    const funds = [s.cash != null ? `cash ${money(s.cash)}` : null,
                   s.facilities ? `committed undrawn facilities ${money(s.facilities)}` : null]
      .filter(Boolean).join(" + ");
    // TWO decimals, matching the engine's own note verbatim: rounding the headline to 1.3y beside
    // a note reading 1.25y is the same number disagreeing with itself on one panel.
    rows.push(fact("Runway", `${funds} ÷ ${money(s.burn)} = <b>${
      s.runwayYears == null ? DASH : `${s.runwayYears.toFixed(2)}y`}</b>`));
  }
  if (s.yearsToBreakeven != null) rows.push(fact("To breakeven", oneDp(s.yearsToBreakeven, "y")));
  if (s.announcedRaise) {
    rows.push(fact("Announced raise", s.raiseAccession
      ? `committed <span class="mono">${escapeHtml(s.raiseAccession)}</span>`
      : `<span class="uw-bad">no accession on file — not counted</span>`));
  }
  // The DETAIL lines carry what the note cannot: the going-concern disclosure with its accession,
  // and any trailing-vs-latest sign contradiction. Both are the reason a gate failed, so a panel
  // that printed only the one-line note would show the verdict and hide the evidence.
  const detail = (s.detail || []).map((d) =>
    `<div class="uw-note ${/WARNING|going concern/i.test(d) ? "uw-bad" : "muted"}">${
      escapeHtml(d)}</div>`).join("");
  return `<div class="uw-survival${fail ? " uw-survival-fail" : ""}">
      <div class="uw-sec-h">Survival <span class="basis">${
        fail ? "GATE FAILED — blocks a confirmed buy" : "gate cleared"}</span></div>
      <div class="uw-surv-body">${rows.join("")}
        <div class="uw-note muted">${escapeHtml(s.note || "")}</div>${detail}</div></div>`;
}

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
        ${isR2(c) ? row("Terminal value / share", (l) => money(l.valueTerminal), { mutedLabel: true }) : ""}
        ${row(isR2(c) ? "Value / share, today" : "Value / share",
              (l) => money(l.valuePerShare), { name: true })}
        ${row("vs spot", delta, { cls: " uw-vs" })}
        ${isR2(c) ? row("Years to terminal", (l) => oneDp(l.years ?? l.yearsToTerminal, "y")) : ""}
        ${hasLegField(c, "revenue")
          ? row(isR2(c) ? "Terminal revenue ($M)" : "Revenue ($M)", (l) => thousands(l.revenue))
          : ""}
        ${onRevenueBasis(c) || !hasLegField(c, "margin") ? "" :
          row(isR2(c) ? "Terminal op margin" : "Op margin", (l) => pct(l.margin))}
        ${hasLegField(c, "eps") ? row("EPS ($)", (l) => money(l.eps)) : ""}
        ${row(`Exit ${basis}`, (l) => oneDp(l.multiple, "×"))}
      </tbody>
    </table></div>
    <div class="uw-note muted">bull is range context — never in the ratio${
      tgt ? ", never the target" : ""}${isR2(c) && c.hurdle != null
        ? ` · today's value discounts the terminal year at ${pct(c.hurdle)} a year`
        : ""}</div>`;
  const main = `<div class="uw-split-main">
      <div class="uw-sec-h">Scenarios <span class="basis">${escapeHtml(basis)}</span></div>
      ${tableHtml}</div>`;
  return rail ? `<div class="uw-split">${main}${rail}</div>` : main;
}

// The per-leg reasoning, full card width, placed AFTER the rationale + thesis-breaks: the read
// order runs verdict-level first (why the position, what breaks it), then leg-level (why each
// number), then methodology. Collapsed on screen; prints expanded like every details since the
// T1 amendment — a printed grid with no justification would contradict no-reason-no-compute.
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
    : axis === "multiple" ? `Exit ${basis}`
    : axis === "horizon" ? "Years to terminal" : axis;
}
function axisFmt(axis) {
  return axis === "revenue" ? thousands
    : axis === "margin" ? pct
    : axis === "multiple" ? (v) => oneDp(v, "×")
    : axis === "horizon" ? (v) => oneDp(v, "y") : (v) => String(v);
}

// An assumption AXIS is not always spelled the same as the LEG FIELD carrying its chosen value.
// R1's three axes happen to match their leg keys exactly, so the chosen-trio row could look the
// value up by axis name — until R2 added `horizon`, whose leg field is `yearsToTerminal`. The
// lookup then resolved to undefined and PRINTED it, in the first R2 record ever written and (via
// the T1 print rule, which force-opens every details block) in every PDF export of it.
// An axis whose leg field is named differently. `earnings` -> `eps` joins `horizon` here for the
// SAME reason the comment above records for `yearsToTerminal`: an axis with no mapping reads
// `leg[axis]`, finds nothing, and prints `undefined · undefined · undefined` in a row that
// force-opens in every PDF. R3 records model earnings/multiple, so without this line the chosen
// trio for a P/E underwrite prints undefined where its only driver belongs (review of #542).
const AXIS_LEG_KEY = { horizon: "yearsToTerminal", earnings: "eps" };
const axisLegValue = (leg, axis) => leg[AXIS_LEG_KEY[axis] || axis];
// R3's axes are appended, not interleaved: a record carries EITHER the R1/R2 trio or the R3 pair,
// so ordering both in one list costs nothing and keeps this a single source of truth.
const AXIS_ORDER = ["revenue", "margin", "earnings", "multiple", "horizon"];
function orderedAssumptions(c) {
  const rank = (a) => { const i = AXIS_ORDER.indexOf(a.axis); return i < 0 ? 99 : i; };
  return [...(c.assumptions || [])].sort((x, y) => rank(x) - rank(y));
}

// Always-visible: ONE line per axis stating how it was modeled — the reviewer's at-a-glance
// methodology check. The reference numbers live one click deeper (methodRefsDetails).
function methodLines(c) {
  const items = orderedAssumptions(c).map((a) =>
    `<li><b>${escapeHtml(axisLabel(a.axis, c.multipleBasis || DASH))}</b>${
      a.unratified ? ` <span class="uw-draft-badge">draft — unratified</span>` : ""
    } — ${escapeHtml(a.method)}</li>`);
  return items.length ? `<ul class="kv-list uw-methods">${items.join("")}</ul>` : "";
}

// On-demand: per-axis reference frames, source-cited, with the chosen bear/base/bull trio
// JUXTAPOSED as the closing row (juxtapose, never difference — the reader compares, the machine
// does not editorialize a gap). Own "M" endnote scope INSIDE the <details>: marker and Sources
// list share print fate (the same invariant as the Inputs block).
function methodRefsDetails(c) {
  // EVERY axis, not only the ones carrying references. Filtering to axes WITH references was a
  // corpus-shaped assumption — true of all eleven R1/R2 cards, false the moment a forward-P/E
  // record arrived: GOOGL's turns and normalized EPS are set by judgment, no committed statistic
  // anchors either, so the whole block vanished and took the chosen trio AND the recipe formula
  // with it. An absent block reads as "nothing to say" when the truth is "nothing anchors this" —
  // absent-vs-broken collapsed, which is exactly the distinction this card exists to keep.
  const axes = orderedAssumptions(c);
  if (!axes.length) return "";
  const legs = ["bear", "base", "bull"]
    .map((n) => (c.scenarios || []).find((s) => s.name === n)).filter(Boolean);
  const tables = () => axes.map((a) => {
    const fmt = axisFmt(a.axis);
    // (schema 1.3) the leg a reference anchors renders as a chip FROM THE FIELD (labels are never
    // parsed), and an excluded row dims with its reason stated — before this, "NOT a reference
    // for us" sat in the same confident column as the numbers that count.
    const rows = a.references.map((p) =>
      `<tr${p.excluded ? ` class="uw-ref-excl"` : ""}><td>${escapeHtml(p.label)}${
        p.leg ? ` <span class="uw-leg-chip">${escapeHtml(p.leg)}</span>` : ""}${
        p.excluded ? `<span class="muted"> — excluded: ${escapeHtml(p.excludedReason || "")}</span>` : ""
      }</td><td class="num">${mono(String(p.value))} ${escapeHtml(p.unit)}</td>
        <td class="uw-ref-cite">${citeMark(p.source)}</td></tr>`).join("");
    // Stated, never implied by an empty table. The words are the analyst's own, carried on the
    // axis method; this row only says that no reference number stands behind them.
    const unanchored = (a.references || []).length ? ""
      : `<tr class="uw-ref-excl"><td colspan="3" class="muted">no reference values — this axis was
          set by judgment, and the method above is where it says so</td></tr>`;
    const chosen = legs.length
      ? `<tr class="name-row"><td>chosen (${legs.map((l) => escapeHtml(l.name)).join(" · ")})</td>
          <td class="num">${legs.map((l) => fmt(axisLegValue(l, a.axis))).join(" · ")}</td><td></td></tr>` : "";
    // (schema 1.3) dated axis NOTES — the analyst finding that used to be smuggled into a fake
    // reference row (SMPL's boundary cells) renders as the prose it is, beside the honest numbers.
    const notes = (a.notes || []).map((n) =>
      `<div class="uw-axis-note muted"><b>${escapeHtml(n.date)}</b> — ${escapeHtml(n.text)}${
        n.source ? `${citeMark(n.source)}` : ""}</div>`).join("");
    return `<div class="uw-method-h">${escapeHtml(axisLabel(a.axis, c.multipleBasis || DASH))}</div>
      <div style="overflow-x:auto;"><table class="data uw-refs-t"><tbody>${rows}${unanchored}${chosen}</tbody></table></div>${notes}`;
  }).join("");
  return `<details class="uw-method"><summary>Reference values — what each assumption was set against</summary>${
    withEndnotes("M", tables)}${recipeLine(c)}</details>`;
}

// The verdict's reasoning — ONE field since 2026-07-22. `rationale` is canonical; the former
// `rationalePlain` second register is retired and no longer emitted.
//
// The two-field arrangement existed to keep the recorded wording safe while a plain restatement
// led. That job moved into the field itself: a recorded rationale is APPEND-ONLY (vinci/seal.py),
// growing by dated `[amended <date>: …]` tags, so the original survives inside the text and the
// reader sees the amendment beside the sentence it changed rather than in a separate expander.
// (record legibility, 2026-07-27) The rationale now sits BEHIND an expander, under the
// machine-derived current-state block. It is the state at DECISION time — accurate, sealed, and
// increasingly historical: SMPL's is correct as of 2026-07-21 and cannot mention the close, the
// watch transition or the margin re-set that followed. Leading with it made readers infer the
// present from the past. The expander force-opens in print (T1), so the PDF is still complete.
function rationaleFact(v, { constructionEra = false, index = [] } = {}) {
  if (!v.rationale) return "";
  // (2026-07-27) The sidecar's read of each PRE-GATE tag — its inferred class, and any later
  // finding that SUPERSEDED it. Rendered under the rationale rather than inside the sealed text,
  // which is never edited: a reader must meet the correction with the claim, not three tags later.
  const idx = (index || []).length
    ? `<div class="foot" style="margin-top:8px;">
        <span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:.04em;">Amendment index</span>
        ${index.map((t) => `<div style="margin-top:3px;">
          <span class="muted">${escapeHtml(String(t.date || ""))}</span>
          <span class="pill" style="font-size:10px;">${escapeHtml(String(t.inferredClass || ""))}</span>
          <span class="muted" style="font-size:11px;">inferred, not self-declared</span>
          ${t.supersededNote
            ? `<div class="fact-caveat" style="margin-top:3px;">SUPERSEDED — ${escapeHtml(t.supersededNote)}</div>`
            : ""}</div>`).join("")}</div>`
    : "";
  const banner = constructionEra
    ? '<div class="fact-caveat" style="margin-bottom:6px;">Recorded while the platform was under '
      + "construction; the amendment history includes system corrections as well as investment "
      + "judgment.</div>"
    : "";
  return `<details class="uw-recorded"><summary>Verdict as recorded${
    v.recorded ? ` — ${escapeHtml(v.recorded)}` : ""}</summary>
    ${banner}<div class="fact-val">${amendMarks(v.rationale)}</div>${idx}</details>`;
}

// Amendment tags are audit trail, not thesis — set them apart so a reader can see at a glance
// which words were recorded at the verdict and which were added afterwards, and WHEN.
// CLASSED tags (2026-07-27 on) also carry WHAT KIND of change they record, so a reader can tell a
// leg change from a system correction without parsing the prose.
//
// EXPORTED, and the ONLY marker (2026-07-27). The dossier's own thesis block used to carry a
// SECOND copy of this regex — which never learned about classed tags, so the same amendment
// rendered marked on the card and unmarked in the Brief. Two parsers of one string is the bug
// class the constitution names; there is now one shared helper and both surfaces call it.
export function amendMarks(text) {
  return escapeHtml(text)
    .replace(/\[amended (\d{4}-\d{2}-\d{2})\s*\((judgment|machine|process)\)\s*:/g,
      '<span class="muted">[amended $1</span> <span class="pill" style="font-size:10px;">$2</span><span class="muted">:</span>')
    .replace(/\[amended (\d{4}-\d{2}-\d{2})\s*:/g,
      '<span class="muted">[amended $1:</span>');
}

// (supersession 2026-07-27) THE LINK BANNERS — an archived record is never hidden and never a
// dead end. The archived card says what replaced it; the live card says what it replaced. Both
// clickable, so the chain walks in either direction without leaving the surface.
function supersessionBanner(c) {
  const dateOf = (key) => String(key || "").split("-").slice(1).join("-") || String(key || "");
  if (c.supersededBy) {
    return `<div class="fact-caveat" style="margin-bottom:10px;">
      <b>ARCHIVED</b> — superseded by the record of
      <a href="#/dossier/${encodeURIComponent(String(c.supersededBy).split("-")[0])}"
        >${escapeHtml(dateOf(c.supersededBy))}</a>.
      This record is kept intact and sealed; it is not the current view of the name.</div>`;
  }
  if (c.supersedes) {
    return `<div class="foot" style="margin-bottom:8px;">Supersedes the record of
      <a href="#/dossier/${encodeURIComponent(String(c.supersedes))}"
        >${escapeHtml(dateOf(c.supersedes))}</a> — archived, sealed, still readable.</div>`;
  }
  return "";
}

// A record carrying amendment tags written BEFORE the class gate (2026-07-27) mixes investment
// judgment with system corrections in one undifferentiated trail — say so rather than let a
// reader assume every amendment was a change of mind.
function hasPreAdoptionTags(v) {
  const m = String(v.rationale || "").match(/\[amended (\d{4}-\d{2}-\d{2})/g) || [];
  return m.some((t) => t.slice(9, 19) < "2026-07-27");
}

// COLLAPSED by default on screen: this is per-axis METHODOLOGY, one step toward provenance,
// and the masthead's Method cell already carries the headline. Since the T1 amendment
// (2026-07-21, operator decision) the audit tier PRINTS EXPANDED — the PDF is the complete
// record — so this block prints open, its summary as the section header.
function methodFact(c) {
  const lines = methodLines(c);
  if (!lines) return "";
  // no fact() wrapper: a "Method" label over a summary that says "How each axis was modeled"
  // is the same word twice — the summary IS the label
  // DERIVED FROM THE RECORD'S OWN AXES, not from a basis guess (review of #542). This read
  // "revenue, margin and multiple" over an R3 card whose axes are earnings and multiple — a
  // heading contradicting the list beneath it. Naming the axes the record actually carries is
  // both correcter and shorter than another basis branch.
  const named = orderedAssumptions(c).map((a) => a.axis);
  const axes = named.length
    ? named.slice(0, -1).join(", ") + (named.length > 1 ? " and " : "") + named[named.length - 1]
    : "each";
  return `<details class="uw-method-block">
    <summary>How each axis was modeled — ${axes} methodology</summary>
    <div>${lines}${methodRefsDetails(c)}</div></details>`;
}

// The audit block carries its OWN endnote scope — markers AND their Sources list both live
// INSIDE the <details>, so the two share fate everywhere: on screen they collapse together, and
// since the T1 amendment they PRINT together (every details force-opens in the PDF). That is the
// real invariant the L3/#10 rule protects (a marker must never outlive its Sources entry, nor
// the reverse) — routing these cites into the CARD's outer list would still split them on screen.
// The per-leg EV/EBIT + normalized-FCF cross-checks are VERIFICATION math, not decision drivers —
// the tier-redesign moved them off the first-cut grid into this audit block (the fund's own rule:
// verification sits one click deeper). Same numbers, same legs, just relocated.
function crossChecks(c) {
  const order = ["bear", "base", "bull"];
  const legs = order.map((n) => (c.scenarios || []).find((s) => s.name === n)).filter(Boolean);
  if (!legs.length || !legs.some((l) => l.evEbit != null || l.normFcf != null)) return "";
  const row = (label, fn) => `<tr><td>${escapeHtml(label)}</td>${
    legs.map((l) => `<td class="num">${fn(l)}</td>`).join("")}</tr>`;
  // own class, NOT uw-method-h: cross-checks are verification math, not methodology, and the
  // stripped-card pin asserts a bare card emits NO "uw-method" markup (no fabricated method block).
  return `<div class="uw-xcheck-h" style="margin-top:10px;">Cross-checks — per leg</div>
    <div style="overflow-x:auto;"><table class="data uw-refs-t">
      <thead><tr><th></th>${legs.map((l) => `<th class="num">${escapeHtml(l.name)}</th>`).join("")}</tr></thead>
      <tbody>${row("EV/EBIT", (l) => oneDp(l.evEbit, "×"))}${row("Norm FCF ($M)", (l) => oneDp(l.normFcf))}</tbody>
    </table></div>`;
}

function inputsDetails(c) {
  const facts = c.facts || [];
  if (!facts.length) return "";
  const rows = () => facts.map((f) => fact(f.key, `${mono(String(f.value))} ${escapeHtml(f.unit || "")}
      <span class="muted">· ${escapeHtml(f.basis || "")}</span>
      ${f.source ? citeMark(f.source) : ""}`)).join("") + crossChecks(c);
  return `<details class="uw-inputs"><summary>Inputs &amp; sources — the recorded facts and per-leg cross-checks</summary>${
    withEndnotes("I", rows)}</details>`;
}

// uwCard(cardJson) -> HTML string. `ticker:false` drops the ticker from the eyebrow when the host
// page already carries it as its h1 (the dossier degrade). `extra` injects host-supplied decision
// rows (the dossier's machine-assessment line + conditional caveat strip) after the rationale and
// before the triggers — themes pass nothing and render exactly as before (ONE-SHAPE preserved:
// the option's default is off, so the shared card never forks).
function trigChips(c, v) {
  const trig = (v.reunderwriteTriggers || []).map((t) =>
    `<span class="uw-chip">${escapeHtml(t)}</span>`).join("");
  return trig ? `<div class="uw-trig"><span class="uw-trig-lab">${
    headlineState(c) === "target" ? "Thesis breaks" : "Re-underwrite when"}</span>${trig}</div>` : "";
}

function uwFoot(c, v) {
  return `<div class="foot uw-foot">underwritten ${escapeHtml(c.underwriteDate || DASH)} · analyst
      ${escapeHtml(c.analyst || DASH)}${
      v.recorded ? ` · verdict recorded ${escapeHtml(v.recorded)}` : ""}${
      c.ledger && c.ledger.entryId ? ` · ledger ${mono(c.ledger.entryId)}` : ""}</div>`;
}

export function uwCard(c, { ticker = true, mark = null } = {}) {
  if (!c) return "";
  const v = c.verdict || {};
  // The masthead leads: the target/base number, the asymmetry, the entry, the downside, the method
  // — the five things a reader needs before deciding whether to read on. The spot cite rides in
  // the headline cell so the price on screen still resolves to its source.
  // ORDER: decision content runs contiguously (the answer, its shape, its derivation, its
  // reasoning, and what would break it), THEN the audit tier. Method sat between the table and the
  // rationale, putting a collapsed block in the middle of the decision read; grouped with the
  // other audit blocks it stops interrupting and starts belonging.
  const body = () => `
    ${masthead(c, ticker)}
    ${supersessionBanner(c)}
    ${legsTable(c)}
    ${survivalPanel(c)}
    ${impliedOdds(c, mark)}
    ${rationaleFact(v, { constructionEra: hasPreAdoptionTags(v), index: c.amendmentIndex })}
    ${trigChips(c, v)}
    ${legReasons(c)}
    ${methodFact(c)}`;
  return `
  <section class="card uw-card">
    ${withEndnotes("U", body)}
    ${inputsDetails(c)}
    ${uwFoot(c, v)}
  </section>`;
}

// The SPLIT composition (dossier tier redesign): the same pieces as uwCard, arranged as TWO
// fragments the host wraps in its own cards — `head` (the masthead strip) for an opener that
// pairs the decision headline with company identity, and `detail` (legs table → odds → rationale
// → host-injected rows → triggers → audit blocks → foot) for the underwrite-detail card. ONE
// implementation of every piece — this is an arrangement, not a fork; themes keep uwCard.
// Endnote scopes: `head` is returned RAW — the HOST wraps its whole opener card in one scope so
// the masthead citation and the company block citations share a single Sources list at the card
// END (a scope closed after the masthead alone dropped its Sources list mid-card). The detail
// keeps "U" (+ "M"/"I" inside its own blocks), self-contained.
export function uwCardParts(c, { mark = null, detailExtra = "", rationale = true } = {}) {
  if (!c) return null;
  const v = c.verdict || {};
  // `rationale: false` — the host lifted the analyst's rationale into its opener card (the
  // narrative slot), so the detail must not render it a second time.
  // (2026-07-27) the supersession banner does NOT render here. Lineage is filing-cabinet
  // information — which record this one replaced — not decision information, so on the dossier it
  // belongs in the Appendix's "Record & reproduce" beside the analyst, date and ledger id. The
  // standalone card KEEPS it (uwCard): an archived record's page has no appendix to carry it.
  const detail = () => `
    ${legsTable(c)}
    ${survivalPanel(c)}
    ${impliedOdds(c, mark)}
    ${rationale ? rationaleFact(v, { constructionEra: hasPreAdoptionTags(v), index: c.amendmentIndex }) : ""}
    ${detailExtra}
    ${trigChips(c, v)}
    ${legReasons(c)}
    ${methodFact(c)}`;
  return {
    head: masthead(c, false, { eyebrow: false }),
    chips: verdictPills(c),
    // no foot here: underwritten-date/analyst/ledger are provenance — the dossier's Record &
    // reproduce carries them (themes keep the foot via uwCard)
    detail: withEndnotes("U", detail) + inputsDetails(c),
  };
}
