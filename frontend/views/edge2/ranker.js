// RANKER — the priority queue as a sortable read-only table with per-name structural profiles +
// a workflow state per row. Orders, never decides. Rows open the dossier. Sort/filter are purely
// client-side, in place — the queue is fetched once and never re-fetched on sort/filter.
import { getRankedQueue, getProcessedStates, getG3Reasons, getGicsLabels, WORKFLOW_STATES } from "../../lib/snapshots.js";
import { fmtScore, fmtMoney, fmtDate, fmtPct, escapeHtml, DASH, queueAgeChip } from "../../lib/format.js";
import { linScale } from "../../lib/exhibit.js";
import { refreshBlock } from "../../lib/ui.js";

const AXES = ["idiosyncrasy", "depth", "character", "multiple"];
const COLS = [
  { key: "rank", label: "#", num: true }, { key: "ticker", label: "Ticker" },
  { key: "industry", label: "Industry" },  // resolved label (CIQ-GICS overlay > official SIC) — inform, not a rank input
  { key: "state", label: "Workflow" },
  { key: "score", label: "Score", num: true }, { key: "depthBand", label: "Band" },
  // `num` stays TRUE: the cell still leads with the same right-aligned mono percentage it always
  // did, and dropping the flag left this one header left-aligned in a row of right-aligned numeric
  // headers (`table.data th.num`) while the figure beside Depth lost `var(--mono)`.
  { key: "idiosyncrasy", label: "Idio — industry vs name", num: true,
    title: "The name against the market benchmark, split into its INDUSTRY cohort's "
         + "median move and what is left over, which is the name's own. Inform-only: the split "
         + "never re-orders the queue. A call is withheld when the two are within 10 "
         + "points, and no cohort is formed under 5 screened peers." }, { key: "depth", label: "Depth (52w)", num: true },
  { key: "character", label: "Character" }, { key: "multiple", label: "Multiple" },
  // Tier-2, not an axis — sits after the four Tier-1 axes and before the tradeability figures,
  // mirroring the order the subtitle describes the composite in. The header carries the BASIS so
  // the cell can be the bare ratio; the title carries the one-session caveat, which the other
  // columns (windowed over 180d/52w) do not need.
  { key: "volumeSpike", label: "Volume vs 90d", num: true,
    title: "The latest single session's share volume ÷ its own 90-day average, as of the screen "
         + "date. A ONE-SESSION reading — unlike the windowed axes, it can differ the next day." },
  // Inform-only CONTEXT, never a rank input — it sits after everything the score is built from so
  // the row reads score-then-evidence. Sorts as text; there is no ordering claim in a strip.
  { key: "context", label: "Evidence (issuance ≤2y)",
    title: "Context the score does NOT use. Net share issuance across the name's XBRL points inside "
         + "a ≤2-year window — anchored on its LAST filed point, so the span is what that issuer "
         + "actually filed and is often shorter; shrinking is the bullish twin of the dilution "
         + "demote. Plus distance off the 52-week low. Drawdown is NOT repeated here — the Depth "
         + "column already carries it." },
  { key: "advUsd", label: "ADV", num: true }, { key: "marketCap", label: "Mkt cap", num: true },
];
const STATE_RANK = WORKFLOW_STATES;  // ONE vocab (lib/snapshots.js) — never re-typed here
const STATE_BADGE = {
  "not-started": `<span class="pill" style="background:var(--surface-2);color:var(--ink-3);">not started</span>`,
  // scenario-record PRESENCE (a first-cut underwrite exists) — an intermediate workflow state,
  // amber so it can never read as a ledger verdict.
  "underwritten": `<span class="pill conditional">underwritten</span>`,
  "dossier-built": `<span class="pill" style="background:var(--accent-bg);color:var(--accent-strong);">dossier</span>`,
  "verdict-logged": `<span class="pill" style="background:var(--live-bg);color:var(--pos-text);">verdict ✓</span>`,
};

let DATA = null;
let stateOf = null; // (ticker) => workflow state
let GICS = {};  // {TICKER: {industry, source_ref}} — the committed-dossier CIQ-GICS overlay

// the displayed Industry: CIQ-GICS when a committed dossier carries it, else the queue's official
// SIC title (the JS twin of vinci.labels.resolve_label's precedence — pinned by a source test)
function dispIndustry(r) {
  return (GICS[r.ticker] && GICS[r.ticker].industry) || r.industry || "—";
}

// A 13-week volume sparkline for the queue cell. The NUMBER says today; the LINE says which way it
// has been moving — the distinction a one-session ratio structurally cannot make, and the reason a
// name reads 3.6× on one screen date and 0.63× twelve days later. It DRAWS ONLY: no "building" /
// "fading" word is derived from it, because that would be the same unearned mechanism claim the
// band labels were retired for. y-domain is [0, max(2, series max)] so quiet names share a scale
// and a spike still fits, with a dashed reference at 1.0 = the name's own 90-day average.
const SPARK_W = 46, SPARK_H = 14, SPARK_REF = 1.0;
function volSpark(series) {
  if (!Array.isArray(series) || series.length < 2) return "";
  const hi = Math.max(SPARK_REF * 2, ...series);
  const x = linScale(0, series.length - 1, 0.5, SPARK_W - 0.5);
  const y = linScale(0, hi, SPARK_H - 1.5, 1.5);
  const pts = series.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const ref = y(SPARK_REF).toFixed(1);
  const label = `volume by week over the last quarter, oldest to newest, each as a multiple of the `
    + `name's 90-day average: ${series.join(", ")}`;
  return `<svg width="${SPARK_W}" height="${SPARK_H}" viewBox="0 0 ${SPARK_W} ${SPARK_H}"`
    + ` role="img" aria-label="${escapeHtml(label)}" style="vertical-align:middle; margin-right:5px;">`
    + `<line x1="0" y1="${ref}" x2="${SPARK_W}" y2="${ref}" stroke="var(--line-2)"`
    + ` stroke-width="0.75" stroke-dasharray="2 2"/>`
    + `<polyline fill="none" stroke="var(--ink-3)" stroke-width="1.15" stroke-linejoin="round"`
    + ` points="${pts}"/></svg>`;
}

// The queue only moves when the ranker runs. run_weekly() writes it now, but a week where CI does
// not fire leaves this page serving a stale queue with no signal beyond a date the reader has to do
// The queue-age chip moved to `lib/format.js` (2026-08-24) so home, ingestion and the ranker
// render one definition; its rationale — the queue only moves when the ranker runs, and it once
// drifted 12 days and 95 names behind the screen feeding it (STATE.md §5) — lives there now.
let G3 = null; // ticker -> the specific G3 UNKNOWN reason
let state = null;

export async function render(root, _params, { item, frame }) {
  state = { sort: "rank", dir: 1, q: "", hideSunk: false };
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading queue…</div>` });
  [DATA, stateOf, G3, GICS] = await Promise.all([
    getRankedQueue(), getProcessedStates(), getG3Reasons(), getGicsLabels()]);

  const w = DATA.weights;
  const edge = `
    <div class="chips" style="margin-bottom:12px;">
      <span class="chip live"><span class="dot live"></span> Edge · Overshoot</span>
      <span class="chip locked">🔒 Neglected (locked until the gate clears)</span>
    </div>`;
  const legend = `
    <div class="card" style="padding:11px 16px; margin-bottom:14px; background:var(--surface-2);">
      <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink-3); font-weight:600; margin-bottom:5px;">Axis legend</div>
      <div style="display:grid; grid-template-columns:repeat(2,1fr); gap:3px 24px; font-size:12px; color:var(--ink-2);">
        <div><b>Idiosyncrasy</b> — name-specific drawdown vs the market (G2)</div>
        <div><b>Character</b> — the shape of the decline (sharp/discrete vs grind)</div>
        <div><b>Depth</b> — distance from the 52-week high (G1)</div>
        <div><b>Multiple</b> — cheapness vs the name's own ~5-year history (G3)</div>
      </div>
    </div>`;

  const controls = `
    <div style="display:flex; gap:14px; align-items:center; flex-wrap:wrap; margin-bottom:12px;">
      <input id="rk-q" type="search" placeholder="Filter ticker, name, or industry…" autocomplete="off" value=""
        style="flex:1; min-width:200px; padding:8px 11px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
      <label style="font-size:12.5px; color:var(--ink-2); display:flex; gap:6px; align-items:center; cursor:pointer;">
        <input id="rk-hide" type="checkbox" /> hide structurally-sunk (${DATA.counts.demoted})
      </label>
      <span class="muted" style="font-size:12px;">${DATA.counts.total} candidates · screened ${escapeHtml(fmtDate(DATA.asOf))}</span>
      ${queueAgeChip(DATA.asOf)}
    </div>
    <div class="subtitle muted" style="margin-bottom:12px;">
      Columns lead with the interpretable quantity (depth/idio as % moves, multiple as the percentile or reason); hover a cell
      for the 0–1 sub-score that the composite (idiosyncrasy ${w.idiosyncrasy} · depth ${w.depth} · character ${w.character} · multiple ${w.multiple}
      + volume overlay, then a tradeability gate) is built from. Click a row for the dossier; the <b>Workflow</b> column shows where to
      spend effort next. Face-validity weights — never tuned on returns.
    </div>`;

  root.innerHTML = frame(item, {
    bodyHtml: edge + legend + controls
      // 13 columns overruns the content area on a 1280px laptop (th is white-space:nowrap, so the
      // table cannot shrink below its headers). Scrolls inside its own container rather than
      // pushing the page sideways — the same wrapper uw-card/dossier use for their wide tables.
      + `<div style="overflow-x:auto;"><table class="data" id="rk-table"><thead><tr id="rk-head"></tr></thead><tbody id="rk-body"></tbody></table></div>`
      + refreshBlock(),
  });
  renderHead();
  renderRows();

  root.querySelector("#rk-q").addEventListener("input", (e) => { state.q = e.target.value.toLowerCase(); renderRows(); });
  root.querySelector("#rk-hide").addEventListener("change", (e) => { state.hideSunk = e.target.checked; renderRows(); });
  root.querySelector("#rk-head").addEventListener("click", (e) => {
    const th = e.target.closest("th[data-sort]");
    if (!th) return;
    const k = th.dataset.sort;
    if (state.sort === k) state.dir *= -1;
    else { state.sort = k; state.dir = (k === "rank" || k === "ticker" || k === "depthBand" || k === "state") ? 1 : -1; }
    renderHead();
    renderRows();
    // renderHead() replaced the whole row, so the button just activated no longer exists. Without
    // this a KEYBOARD sort drops focus to <body> and the next Tab restarts from the top of the
    // page — the sort would be reachable but unusable. :focus-visible keeps the ring off for mice.
    const again = document.querySelector(`#rk-head th[data-sort="${k}"] button`);
    if (again) again.focus();
  });
}

function renderHead() {
  const head = document.getElementById("rk-head");
  if (!head) return;
  head.innerHTML = COLS.map((c) => {
    const active = state.sort === c.key;
    const arrow = active ? (state.dir > 0 ? " ▲" : " ▼") : "";
    const tip = c.title ? ` title="${escapeHtml(c.title)}"` : "";
    // The control is a real <button>, not the <th> itself: a th with a click handler is not
    // focusable and has no activation semantics, so all 13 columns were mouse-ONLY. The button
    // brings native focus + Enter/Space for free; `aria-sort` on the th is what announces WHICH
    // column is sorted and which way — the ▲/▼ is decoration and hidden from assistive tech.
    const sort = active ? (state.dir > 0 ? "ascending" : "descending") : "none";
    return `<th scope="col" data-sort="${c.key}" class="${c.num ? "num" : ""}" aria-sort="${sort}"`
      + ` style="user-select:none;"><button type="button" class="col-sort"${tip}>${c.label}`
      + `<span aria-hidden="true">${arrow}</span></button></th>`;
  }).join("");
}

function axisVal(row, key) {
  if (AXES.includes(key)) return row.axes[key]?.score;
  if (key === "state") return STATE_RANK[stateOf(row.ticker)] ?? 0;
  if (key === "industry") return dispIndustry(row);   // sort by the DISPLAYED label (GICS overlay)
  return row[key];
}

function renderRows() {
  const body = document.getElementById("rk-body");
  if (!body) return;
  let rows = DATA.rows.slice();
  if (state.q) rows = rows.filter((r) => r.ticker.toLowerCase().includes(state.q) || (r.name || "").toLowerCase().includes(state.q) || (r.sector || "").toLowerCase().includes(state.q) || dispIndustry(r).toLowerCase().includes(state.q));
  if (state.hideSunk) rows = rows.filter((r) => !r.structurallyDisqualified);

  rows.sort((a, b) => {
    const va = axisVal(a, state.sort), vb = axisVal(b, state.sort);
    if (typeof va === "string" || typeof vb === "string")
      return String(va ?? "").localeCompare(String(vb ?? "")) * state.dir;
    return ((va ?? -Infinity) - (vb ?? -Infinity)) * state.dir;
  });

  // 3b/3c: lead with the interpretable raw quantity; the 0–1 sub-score is secondary (hover title).
  const rawCell = (r, k) => {
    const a = r.axes[k] || {};
    const v = a.raw == null ? `<span class="muted">${DASH}</span>` : fmtPct(a.raw, { signed: true });
    return `<td class="num" title="sub-score ${a.score == null ? "—" : a.score.toFixed(2)} · ${escapeHtml(a.label || "")}">${v}</td>`;
  };
  // THE COHORT SPLIT, inside the cell that makes the claim.
  //
  // `Idio (vs mkt)` asserts a name fell for its OWN reasons — but G2 strips MARKET beta, not
  // SECTOR, so a name that fell with its whole industry lands here looking idiosyncratic. For
  // roughly one in five persistent decliners that assertion is false. The split goes INSIDE this
  // cell rather than into a 14th column: the table already runs to 13 and overruns a 1280px
  // laptop (see the scroll container below).
  //
  // It NEVER re-orders the queue. Ranking by the residual was pre-registered, measured across four
  // snapshots and FALSIFIED — its top-25 churns more than the raw order at every interval. The
  // sort key is untouched; this is display only.
  // PLAIN WORDS ON THE SURFACE. The code's terms are `own` / `cohort`; neither says what it means
  // to someone reading a queue, and shipping them raw broke this repo's own coin-time translation
  // rule. The label states the FINDING, and the tooltip states the arithmetic behind it.
  //
  // The JS twin of `vinci.cohort.MIN_PEERS` — display only, used to pick WHICH reason to print for
  // an empty read. Kept as one named constant rather than a number written into three sentences,
  // because it was: the first cut said "6" in the header tooltip, the label map and the glossary
  // while the code's floor was 5, so 11 rows of the committed queue carried a cohort the surface
  // said could not exist.
  const COHORT_MIN_PEERS = 5;
  //: mirrors vinci.cohort.UNRESOLVED_INDUSTRY — the bucket `industry_for_sic` returns for a SIC
  //: that is blank, null or unparseable. It is never made a cohort, so a name in it has no peers
  //: to compare against and must not be described as one that was skipped by the screen.
  const UNRESOLVED_INDUSTRY = "Unknown";
  const NO_INDUSTRY = ["no industry",
    "This name was screened, but its SIC code is missing or unreadable, so there is no industry "
    + "to compare it against. Not a judgement about the name."];
  const COHORT_LABEL = {
    own: ["name-specific",
          "Its industry barely moved — this fall is the company's own, which is what an overshoot "
          + "thesis needs."],
    cohort: ["industry-wide",
             "Its industry fell too, and by more than this name did on its own — most of this "
             + "drop is not company-specific."],
    unresolved: ["too close",
                 "No call is made. The gap between the industry's move and the name's own does "
                 + "not clear BOTH bars it has to: 10 points (below that the read holds only 34% "
                 + "of the time week to week) and this cohort's own median uncertainty, which is "
                 + "in the cell's own tooltip."],
    "no-cohort": ["too few peers",
                  "Fewer than 5 same-industry names in the peer pool — the screened names plus "
                  + "the peers the screen dropped for cap or liquidity — not enough to take a "
                  + "median over, so no comparison is offered. (An industry the SIC code does "
                  + "not resolve is never a cohort either, at any size.)"],
  };
  // A no-cohort read has TWO causes and they are not the same statement. `too few peers` is about
  // the INDUSTRY; this one is about the NAME — its industry is well populated, the name just is
  // not in the newest screen log (the queue was ranked off an older candidate snapshot). Two rows
  // of the committed queue are this case, and both read "too few peers" beside a 12-name cohort
  // until the pill learned to tell them apart.
  const NOT_SCREENED = ["not screened",
                        "This name is not in the latest screen log — the queue was ranked from an "
                        + "earlier candidate snapshot — so there is no current return to split. "
                        + "Its industry is not the problem; the cell's tooltip gives its size."];
  const idioCell = (r) => {
    const a = r.axes.idiosyncrasy || {};
    const raw = a.raw == null ? `<span class="muted">${DASH}</span>` : fmtPct(a.raw, { signed: true });
    const c = r.cohort;
    // No cohort block at all = a snapshot written before the split shipped. Degrade to the bare
    // number rather than rendering an empty scaffold.
    if (!c) {
      return `<td class="num" title="sub-score ${a.score == null ? "—" : a.score.toFixed(2)} · ${escapeHtml(a.label || "")}">${raw}</td>`;
    }
    // THREE REASONS A NAME HAS NO COHORT, and they are different statements (review, #503). The
    // first cut had two, so a screened name whose SIC does not resolve was told "name not
    // screened" — false, and its own "cohort" was N Unknown-industry names. `key` is the
    // discriminator: the unresolved bucket is never made a cohort, so it always lands here.
    const thin = c.peers < COHORT_MIN_PEERS;
    const unresolved = c.key === UNRESOLVED_INDUSTRY;
    const [lbl, tip] = (c.median == null && !thin)
      ? (unresolved ? NO_INDUSTRY : NOT_SCREENED)
      : (COHORT_LABEL[c.call] || COHORT_LABEL["no-cohort"]);
    // `c.call` is data-derived and reaches a class attribute, so it is escaped like every other
    // interpolation in this cell rather than trusted for being an enum today.
    const pill = `<span class="pill ck-${escapeHtml(c.call)}" title="${escapeHtml(tip)}">${lbl}</span>`;
    // When there is no cohort the PILL already says so — repeating it on the split line just
    // renders "no cohort no cohort". The line carries the reason only when it adds one, and there
    // are TWO distinct ones the peer count separates: a same-industry set that exists but is too
    // small to take a median over, versus a name that simply is not in the latest screen log while
    // its industry is well populated. Saying "only 12 screened peers" for the second would be a
    // false reason, so each gets its own words.
    const split = (c.median == null || c.residual == null)
      ? (thin
          ? `<span class="muted">only ${c.peers} pooled peer${c.peers === 1 ? "" : "s"}</span>`
          : unresolved
            ? `<span class="muted">industry not on file</span>`
            : `<span class="muted">${c.peers} peers, name not screened</span>`)
      : `<span class="ck-k">industry</span><b>${fmtPct(c.median, { signed: true })}</b>`
        + `<span class="ck-sep">→</span><span class="ck-k">name</span><b>${fmtPct(c.residual, { signed: true })}</b>`;
    // The tooltip carries the arithmetic AND the cohort's membership, because "industry" is doing
    // a lot of work in one word: it is the SIC industry AS REPRESENTED IN THE PEER POOL — the
    // screened names PLUS the peers the screen dropped for cap or liquidity (`cohort_pool.jsonl`),
    // still not literally every listed peer. It said "in the screened universe" until #509 widened
    // the pool, at which point the phrase became false: Software is measured over ~160 names of
    // which only ~60 are screened. Say which set, and how many.
    //
    // "MEASURED AGAINST" IS ONLY TRUE WHEN SOMETHING WAS MEASURED. With no median there is no
    // comparison, so the phrasing switches to a plain count of what exists — the earlier wording
    // asserted "measured against the 0 Aircraft names" on all 75 no-cohort rows of the committed
    // queue, which was both a false count and a claim of a measurement that never happened.
    const key = !c.key ? ""
      : c.median == null
        ? ` — no comparison: ${c.peers} ${c.key} name${c.peers === 1 ? "" : "s"} in the peer pool`
        : ` — measured against the ${c.peers} ${c.key} names in the peer pool`
          + (c.uncertainty == null ? ""
             : `, whose median is pinned to ±${fmtPct(c.uncertainty)}`)
          + `; the name is ${fmtPct(c.median + c.residual, { signed: true })}`
          + ` vs the market, its industry ${fmtPct(c.median, { signed: true })}, leaving`
          + ` ${fmtPct(c.residual, { signed: true })} that is the name's own`;
    return `<td class="num ck-cell" title="sub-score ${a.score == null ? "—" : a.score.toFixed(2)} · ${escapeHtml(a.label || "")}${escapeHtml(key)}">`
      + `<div class="ck-top">${raw}${pill}</div><div class="ck-split">${split}</div></td>`;
  };
  // 3d: character qualitatively — its sub-signals (sharp-discrete vs grind/bleed, gap count, recency)
  // are translatable, so lead with the interpretable form; 0–1 sub-score + full read on hover.
  const charCell = (r) => {
    const a = r.axes.character || {};
    if (a.score == null) return `<td><span class="muted">${DASH}</span></td>`;
    const lbl = a.label || "";
    let q;
    if (/grind|bleed/i.test(lbl)) {
      q = "grind/bleed";
    } else {
      const n = (lbl.match(/(\d+)\s+gap-down/) || [])[1];
      const age = (lbl.match(/(\d+)d ago/) || [])[1];
      q = "sharp" + (n ? ` · ${n} gap${n === "1" ? "" : "s"}` : "") + (age ? ` · ${age}d ago` : "");
    }
    if (/mean.?revert/i.test(lbl)) q += " · revert";
    else if (/structural.?break/i.test(lbl)) q += " · break";
    return `<td style="font-size:12px;" title="sub-score ${a.score.toFixed(2)} · ${escapeHtml(lbl)}">${escapeHtml(q)}</td>`;
  };
  const multCell = (r) => {
    const a = r.axes.multiple || {};
    if (a.coverage === "unknown") {
      const reason = G3[r.ticker] || "multiple unavailable";
      return `<td class="muted" style="font-style:italic; font-size:11.5px;" title="${escapeHtml(a.label || "")}">${escapeHtml(reason)}</td>`;
    }
    const short = (a.label || "").split(" of ")[0]; // "P/E 0%ile of own 5y range" → "P/E 0%ile"
    return `<td title="sub-score ${a.score == null ? "—" : a.score.toFixed(2)} · ${escapeHtml(a.label || "")}">${escapeHtml(short)}</td>`;
  };
  // Tier-2 volume — the one component of Score with no column of its own. LEADS WITH THE RATIO,
  // like every other column on this page ("columns lead with the interpretable quantity"): the
  // band word is only a bucketing of a number the reader can now see, and the two words it used to
  // lead with named a MECHANISM the input cannot contain — one session's volume carries no
  // direction, so "distribution" was a guess that was wrong on 2 of 10 names (audit, STATE.md §5).
  // The word survives in the hover as the scorer's own read, never as the headline.
  const volCell = (r) => {
    const s = r.volumeState;
    const adj = r.volumeOverlay;
    const note = adj == null ? "overlay unavailable"
      : adj ? `${adj > 0 ? "+" : ""}${adj.toFixed(2)} to quality` : "no adjustment";
    const vs = r.volumeSpike;
    if (vs == null) {
      // legacy snapshot (pre-2026-08-12): no structured ratio, so fall back to the scorer's string
      // rather than digging the number out of it — a display string is never re-parsed for a value.
      if (!s || s === "UNKNOWN") return `<td><span class="muted">${DASH}</span></td>`;
      return `<td style="font-size:12px;" title="${escapeHtml(s)} · ${note}">${escapeHtml(s)}</td>`;
    }
    const trend = r.volumeTrend;
    const scale = Array.isArray(trend) && trend.length
      ? ` · sparkline: 13 weekly means, 0 to ${Math.max(SPARK_REF * 2, ...trend).toFixed(1)}×, dashed line = 1.0×`
      : "";
    return `<td class="num" title="${escapeHtml(s || "")} · ${note} · one session, as of the screen `
      + `date${escapeHtml(scale)}">${volSpark(trend)}`
      + `${vs < 10 ? vs.toFixed(2) : vs.toFixed(1)}×</td>`;
  };

  // The evidence strip. Rendered as the writer composed it — no re-parsing, no re-formatting, and
  // no direction word derived from it beyond the arrows the composer already put in.
  const evidenceCell = (r) => (r.context
    ? `<td class="muted" style="font-size:11.5px; line-height:1.3;"><span style="display:inline-block; max-width:150px;">${escapeHtml(r.context)}</span></td>`
    : `<td><span class="muted">${DASH}</span></td>`);

  body.innerHTML = rows.map((r) => {
    const sunk = r.structurallyDisqualified;
    const flag = sunk && r.structuralFlag
      ? `<div class="cite" style="color:var(--danger);">⛔ ${escapeHtml(r.structuralFlag.signal)} · ${escapeHtml(r.structuralFlag.source)}</div>` : "";
    const gated = r.gated ? ` <span class="pill locked" title="below the deep-work ADV floor">thin</span>` : "";
    return `
      <tr data-ticker="${escapeHtml(r.ticker)}" style="cursor:pointer;${sunk ? "opacity:0.62;" : ""}">
        <td class="num muted">${r.rank}</td>
        <td><span class="mono" style="font-weight:600;">${escapeHtml(r.ticker)}</span>${sunk ? " ⛔" : ""}
          <div class="muted" style="font-size:11.5px;">${escapeHtml((r.name || "").slice(0, 40))}</div>${flag}</td>
        <td class="muted" style="font-size:12px;"><span style="display:inline-block; max-width:92px; line-height:1.25;">${escapeHtml(dispIndustry(r))}${GICS[r.ticker] ? ` <span class="gics-mark" title="CIQ GICS Primary Industry Classification — ${escapeHtml(GICS[r.ticker].source_ref || "committed dossier")}">CIQ</span>` : ""}</span></td>
        <td>${STATE_BADGE[stateOf(r.ticker)] || ""}</td>
        <td class="num" style="font-weight:600;">${fmtScore(r.score)}</td>
        <td><span class="pill ${sunk ? "unresolved" : "live"}">${escapeHtml(r.depthBand)}</span>${gated}</td>
        ${idioCell(r)}${rawCell(r, "depth")}${charCell(r)}${multCell(r)}${volCell(r)}${evidenceCell(r)}
        <td class="num">${fmtMoney(r.advUsd)}</td>
        <td class="num">${r.marketCap == null ? `<span class="muted">${DASH}</span>` : fmtMoney(r.marketCap)}</td>
      </tr>`;
  }).join("") || `<tr><td colspan="${COLS.length}" class="muted" style="padding:18px;">No rows match the filter.</td></tr>`;

  body.querySelectorAll("tr[data-ticker]").forEach((tr) =>
    tr.addEventListener("click", () => { location.hash = `#/dossier/${tr.dataset.ticker}`; }));
}
