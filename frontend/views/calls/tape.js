// ============================================================================
// THE CALLS TAPE — one screen, three panes, over one X account's posted calls.
//
// WHY ONE SCREEN AND NOT THREE. This is a LABELLING tool before it is a browser: the operator
// works through hundreds of cashtags, and a page transition costs their place, their scroll
// position and the chart they were reading. So calendar, posts and chart are panes of a single
// view. Keys move FOCUS (day -> post -> cashtag) and the chart re-draws for whatever is focused;
// nothing navigates.
//
// THE URL STILL CARRIES THE SELECTION (#/calls/<handle>/<date>/<TICKER>/<tweet_id>) so a call is
// linkable — but it is written with history.replaceState, NOT by assigning location.hash. app.js
// re-renders all of #main on every hashchange, which would tear down and rebuild this screen on
// every keystroke.
//
// ACCOUNTS ARE DATA. Every read is namespaced by handle and the selector is built from
// accounts.json, so adding a second voice is a directory drop plus `vinci calls accounts` — no
// route, view or schema change. Nothing below hardcodes a handle.
//
// MACHINE LABELS ARE GUESSES AND MUST LOOK LIKE GUESSES (55% on bias, 62% on targets): dashed,
// muted, prefixed `guess:`. Hand labels are ground truth and render in full colour. No aggregate
// hit-rate is displayed anywhere — at 83 hand labels against 8,102 machine ones, any headline
// number would describe the machine, not the author.
// ============================================================================
import { candleDomain, candleWidth, candles, extent, linScale } from "../../lib/exhibit.js";
import { DASH, escapeHtml, fmtPct } from "../../lib/format.js";

const DASH_ = DASH;
import {
  getCallAccounts, getCallBars, getCallDays, getCallLabels, getCallPosts, getCallResults,
} from "../../lib/snapshots.js";

const BIAS_COLOR = { bullish: "var(--pos-text)", bearish: "var(--danger)" };
const ACTIONS = ["", "enter_long", "enter_short", "add", "trim", "exit", "no_entry", "hold", "none"];
const BIASES = ["bullish", "bearish", "mixed", "neutral", "none"];
const TARGET_TYPES = ["none", "point", "range", "pct", "qualitative"];
//: What the specificity tiers actually contain, measured across the committed corpus rather than
//: asserted — the filter offered A/B/C/D with no definition anywhere, which is a scale you cannot
//: sort by. `n` is filled at render from the labels actually loaded.
const SPEC_DEF = [
  ["A", "direction + target, usually with a stated horizon", "the most actionable call"],
  ["B", "direction + target, no horizon stated", "a level, open-ended on timing"],
  ["C", "direction only, no target named", "a stance, not a number"],
  ["D", "no directional call", "commentary, retrospective, or flow"],
];

//: post_class comes from the upstream labeller and is NOT in the build spec, but a quarter of the
//: corpus is not signal at all (1,412 flow_spam + 474 promo + 219 noise + 61 engagement of 8,185).
//: Labelling throughput is the whole point of this screen, so being able to hide them matters more
//: than most of the filters that were specified.
const CLASSES = ["signal_candidate", "flow_spam", "pnl_report", "promo", "noise", "engagement"];

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

//: WHY THE UPSTREAM `needs_review` FLAG IS NOT USED AS A FILTER. It is true on 5,982 of 8,185 rows
//: (73%), and worse than merely unselective: it INCLUDES 1,410 flow_spam rows nobody should ever
//: read, and EXCLUDES 510 spec-A calls — the most specific, most reviewable rows in the corpus. As
//: a queue it points away from the work. The flag is still shown on the chip (it is the labeller's
//: own signal and not ours to delete); it is just not what the filter sorts by.
//:
//: These reasons are DERIVED, ordered most-actionable first, and every one excludes the non-signal
//: classes outright. Counts are computed at render from the corpus actually loaded.
const REVIEW_REASONS = [
  ["conflict", "target contradicts the stated bias",
   (l, r) => r && r.target_status === "sign_conflict"],
  ["unreadable", "a target was named and could not be read",
   (l, r) => r && r.target_status === "unparseable"],
  ["noprice", "no price data for the ticker",
   (l, r) => r && r.status === "NO_PRICE_DATA"],
  ["specific", "a specific call (spec A/B) still only guessed",
   (l) => l.src === "machine" && (l.spec === "A" || l.spec === "B")],
  ["undirected", "a target with no direction to score it by",
   (l) => l.target_type && l.target_type !== "none" && (!l.bias || l.bias === "none")],
  ["implausible", "a target nowhere near the price (a parse artifact)",
   (l, r) => r && r.target_status === "implausible"],
  ["counter", "a level on the wrong side of the entry for the stated bias",
   (l, r) => r && r.target_status === "counter_directional"],
  ["mixed", "a two-sided read", (l) => l.bias === "mixed"],
];
const NON_SIGNAL = new Set(["flow_spam", "promo", "noise", "engagement"]);

/** The reasons this row wants a human, most actionable first. Empty = it does not. */
function reviewReasons(key) {
  const l = labelFor(key);
  if (!l || l.src === "hand") return [];
  if (NON_SIGNAL.has(l.post_class)) return [];
  const r = S.results ? S.results.get(key) : null;
  return REVIEW_REASONS.filter(([, , test]) => {
    try { return Boolean(test(l, r)); } catch (e) { return false; }
  }).map(([id]) => id);
}

const S = {
  handle: null, day: null, ticker: null, tweetId: null,
  accounts: null, days: null, labels: null, results: null,
  posts: [], month: null,
  postIdx: 0, chipIdx: 0,
  filters: { ticker: "", spec: "", cls: "", bias: "", video: false, review: "", unlabelled: false },
  edits: {},                       // key -> patch, mirrored to localStorage
  window: null,                    // active chart window preset (see WINDOWS)
  seqFiltered: false,              // do the filters reach the chart's prior-post markers
  geom: null,                      // last drawn chart geometry, for the crosshair
};

// --- edits: local until exported. The pipeline's own file is the durable record. ---------------
const storeKey = () => `nv-calls-${S.handle}`;
function loadEdits() {
  try { S.edits = JSON.parse(localStorage.getItem(storeKey()) || "{}"); }
  catch (e) { S.edits = {}; }
}
function saveEdits() {
  try { localStorage.setItem(storeKey(), JSON.stringify(S.edits)); } catch (e) { /* private mode */ }
}

/** The label a human should see: the committed row, with any local edit laid over it. */
function labelFor(key) {
  const base = (S.labels && S.labels[key]) || null;
  const patch = S.edits[key] || null;
  if (!base && !patch) return null;
  return { ...(base || { src: "hand" }), ...(patch || {}), ...(patch ? { src: "hand" } : {}) };
}
const isHand = (l) => Boolean(l) && l.src === "hand";

// --- selection ---------------------------------------------------------------------------------
const monthOf = (iso) => String(iso).slice(0, 7);
const quarterOf = (iso) => `${iso.slice(0, 4)}Q${Math.floor((+iso.slice(5, 7) - 1) / 3) + 1}`;

function writeUrl() {
  // DERIVE FROM WHAT IS FOCUSED, never from separately-tracked state. S.ticker / S.tweetId were
  // set only by a chip click, so j/k and a marker jump left the URL naming the PREVIOUS post —
  // and a link shared from that state opened the wrong call. Reading the focus itself makes the
  // URL structurally unable to disagree with the screen.
  const fp = focusPost();
  const ft = focusTags()[S.chipIdx];
  if (fp) S.tweetId = String(fp.id);
  if (ft) S.ticker = ft;
  const parts = ["calls", S.handle, S.day, S.ticker, S.tweetId].filter(Boolean);
  const url = `#/${parts.join("/")}`;
  // replaceState, never location.hash: assigning the hash fires app.js's router, which would
  // re-render this whole screen and drop focus on every single keystroke.
  if (location.hash !== url) history.replaceState(null, "", url);
}

// --- data --------------------------------------------------------------------------------------
async function loadMonth(month) {
  if (S.month === month) return;
  S.posts = await getCallPosts(S.handle, month);
  S.posts.sort((a, b) => String(a.t).localeCompare(String(b.t)));
  S.month = month;
}

//: ONE DEFINITION OF "PASSES THE FILTERS", used by the posts list AND (optionally) by the chart's
//: prior-post markers. Two copies of this predicate would drift the moment a filter was added, and
//: the two surfaces would then disagree about the same post without anything saying so.
const tagsOf = (p) => (p.tk || []).map((t) => t.replace(/^\$/, ""));

/** Post-level filters — things true of the post itself, independent of which cashtag. */
function postPasses(p) {
  const f = S.filters;
  if (f.video && !p.v) return false;
  if (f.ticker && !tagsOf(p).includes(f.ticker)) return false;
  return true;
}

/** Chip-level filters — asked of ONE (post, ticker) pair, which is the unit of work here. */
function chipPasses(postId, tkr) {
  const f = S.filters;
  const key = `${postId}|${tkr}`;
  const l = labelFor(key);
  if (f.cls) {
    const raw = (S.labels || {})[key];
    if (!raw || raw.post_class !== f.cls) return false;
  }
  if (f.spec && (!l || l.spec !== f.spec)) return false;
  // `unlabelled` is a real bias value here, meaning "no chip at all" — distinct from the label
  // whose bias IS the string "none", which is the author declining to take a side.
  if (f.bias) {
    if (f.bias === "__none__") { if (l) return false; } else if (!l || l.bias !== f.bias) return false;
  }
  if (f.review) {
    const rs = reviewReasons(key);
    if (!rs.length || (f.review !== "any" && !rs.includes(f.review))) return false;
  }
  if (f.unlabelled && isHand(l)) return false;
  return true;
}

/** Posts on the selected day, after filters. Filtering is what makes the tool usable at 5,641. */
function dayPosts() {
  return S.posts.filter((p) => p.d === S.day && postPasses(p)
    && tagsOf(p).some((t) => chipPasses(p.id, t)));
}
const focusPost = () => dayPosts()[S.postIdx] || null;
function focusTags() {
  const p = focusPost();
  return p ? (p.tk || []).map((t) => t.replace(/^\$/, "")) : [];
}

// --- chart -------------------------------------------------------------------------------------
// WINDOWS ARE ANCHORED ON THE POST, NOT ON TODAY, and that is the whole reason these are not the
// usual 5D/1M/3M row. A normal chart's "6M" means the last six months from now; here the subject is
// a call made at a fixed point in the past, so a trailing window can miss the call entirely. Each
// preset is therefore [post − lead, post + span] in calendar days, which keeps the post and its
// outcome both on screen at every zoom level. FIT snaps to the scored horizon itself.
const WINDOWS = [
  ["5D", -4, 7], ["1M", -10, 31], ["3M", -25, 92], ["6M", -45, 183],
  ["1Y", -92, 365], ["5Y", -365, 1825], ["MAX", null, null], ["FIT", null, null],
];
const DEFAULT_WINDOW = "1Y";               // == the old fixed −3mo / +12mo

function shiftDays(iso, days) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/** Resolve the active preset to a concrete [from, to] for this post. */
function windowRange(postDate, result) {
  const key = S.window || DEFAULT_WINDOW;
  if (key === "MAX") return [null, null];
  if (key === "FIT") {
    // the scored horizon, padded — useless before a call is scored, so fall back to the default
    if (!result || !result.entry_date || !result.exit_date) {
      const [, lead, span] = WINDOWS.find((w) => w[0] === DEFAULT_WINDOW);
      return [shiftDays(postDate, lead), shiftDays(postDate, span)];
    }
    const days = Math.round(
      (Date.parse(result.exit_date) - Date.parse(result.entry_date)) / 86400000);
    const pad = Math.max(Math.round(days * 0.15), 3);
    return [shiftDays(result.entry_date, -pad), shiftDays(result.exit_date, pad)];
  }
  const w = WINDOWS.find((x) => x[0] === key) || WINDOWS.find((x) => x[0] === DEFAULT_WINDOW);
  return [shiftDays(postDate, w[1]), shiftDays(postDate, w[2])];
}

/**
 * The verification chart. Five overlays, each of which is what makes this more than a price
 * viewer: the post itself, every OTHER post on the same ticker (the sequence is the story), the
 * stated target, the horizon band, and the benchmark rebased to 100 AT THE POST.
 *
 * Two stacked panels share one x-axis because they cannot share a y-axis: candles are absolute
 * dollars and a rebased index is not, and the target line is an absolute price.
 */
function chartSvg({ bars, bench, postDate, label, result, ticker, otherPosts }) {
  if (!bars.length) return null;
  const [from, to] = windowRange(postDate, result);
  const win = bars.filter((b) => (from == null || b.d >= from) && (to == null || b.d <= to));
  if (win.length < 2) return null;

  const W = 1100, H = 560, padL = 46, padR = 14, cy0 = 26, cy1 = 380, by0 = 440, by1 = 540;
  const px0 = padL, px1 = W - padR;
  const idxOf = (iso) => {
    let best = -1;
    for (let i = 0; i < win.length; i++) if (win[i].d <= iso) best = i; else break;
    return best;
  };
  const tIdx = idxOf(postDate);
  const target = result && result.target_px != null ? result.target_px : null;
  const dom = candleDomain(win.map((b) => b.h), win.map((b) => b.l),
                           { include: target != null ? [target] : [] });
  if (!dom) return null;
  const sx = linScale(0, win.length - 1, px0, px1);
  const sy = linScale(dom.lo, dom.hi, cy1, cy0);

  // gridlines at a nice step
  const span = dom.hi - dom.lo;
  const step = [1, 2, 5, 10, 20, 25, 50, 100, 200].find((g) => span / g <= 9) || 500;
  let grid = "";
  for (let v = Math.ceil(dom.lo / step) * step; v < dom.hi; v += step) {
    const y = sy(v).toFixed(1);
    grid += `<line x1="${px0}" y1="${y}" x2="${px1}" y2="${y}" stroke="var(--line)"/>`
      + `<text x="${px0 - 5}" y="${+y + 3.3}" font-size="10" text-anchor="end" fill="var(--ink-3)">${v}</text>`;
  }

  // (4) HORIZON BAND — post -> horizon end. Target touched inside it is the win condition.
  // A LIVE CALL HAS A BAND TOO. It used to draw only when `exit_date` existed, so the 349 OPEN
  // calls — the ones whose outcome is still in play, and arguably the more interesting half —
  // showed no shaded window at all. For those the band runs to the last bar and its right edge is
  // left OPEN (no closing rule) so it reads as "still running", never as a horizon that ended.
  let band = "", hzEndIdx = -1, bandOpen = false;
  if (result && result.exit_date) {
    hzEndIdx = idxOf(result.exit_date);
  } else if (result && result.status === "OPEN") {
    hzEndIdx = win.length - 1;
    bandOpen = true;
  }
  if (tIdx >= 0 && hzEndIdx > tIdx) {
    band = `<rect x="${sx(tIdx).toFixed(1)}" y="${cy0}" width="${(sx(hzEndIdx) - sx(tIdx)).toFixed(1)}"`
      + ` height="${cy1 - cy0}" fill="var(--target-fill)"/>`;
    band += bandOpen
      ? `<text x="${(sx(hzEndIdx) - 4).toFixed(1)}" y="${cy0 + 12}" font-size="9.5" text-anchor="end"`
        + ` fill="var(--conditional)">horizon still running` +
        ` (${result.elapsed_days ?? "?"}/${result.horizon_days ?? "?"}d) ▸</text>`
      : `<line x1="${sx(hzEndIdx).toFixed(1)}" y1="${cy0}" x2="${sx(hzEndIdx).toFixed(1)}" y2="${cy1}"`
        + ` stroke="var(--pos-border)" stroke-dasharray="2 4"/>`;
  }

  // candles — geometry from lib/exhibit.js, markup here (chart-type geometry stays per-exhibit)
  const w = candleWidth(px1 - px0, win.length);
  const geo = candles(win.map((b) => b.o), win.map((b) => b.h), win.map((b) => b.l),
                      win.map((b) => b.c), { sx, sy, width: w });
  let body = "";
  for (const c of geo) {
    if (!c) continue;                       // a gap stays a gap
    const col = c.up ? "var(--pos-text)" : "var(--danger)";
    body += `<line x1="${c.x.toFixed(1)}" y1="${c.wickY0.toFixed(1)}" x2="${c.x.toFixed(1)}"`
      + ` y2="${c.wickY1.toFixed(1)}" stroke="${col}" stroke-width="0.7" opacity="0.8"/>`
      + `<rect x="${c.bodyX.toFixed(1)}" y="${c.bodyY.toFixed(1)}" width="${c.bodyW.toFixed(1)}"`
      + ` height="${c.bodyH.toFixed(1)}" fill="${col}" opacity="0.9"/>`;
  }

  // (3) TARGET LINE — only when the label actually resolves to a price. A qualitative or refused
  // target draws NOTHING; a line at a guessed level would be the machine inventing the author's number.
  let tgt = "";
  if (target != null) {
    const y = sy(target).toFixed(1);
    tgt = `<line x1="${px0}" y1="${y}" x2="${px1}" y2="${y}" stroke="var(--accent)" stroke-width="1.3"`
      + ` stroke-dasharray="6 3"/><text x="${px1 - 3}" y="${+y - 5}" font-size="10" text-anchor="end"`
      + ` fill="var(--accent)" font-weight="600">target ${target.toFixed(2)}</text>`;
  }

  // (2) EVERY OTHER POST ON THIS TICKER, coloured by bias, staggered across lanes on collision —
  // the same treatment drawdownChart() gives clustered gap-downs, for the same reason.
  const LANES = [-17, 17, -30, 30];
  let marks = "", prevX = -1e9, cluster = 0;
  for (const op of otherPosts) {
    const i = idxOf(op.d);
    if (i < 0 || op.id === (focusPost() || {}).id) continue;
    const x = sx(i);
    cluster = x - prevX < 18 ? cluster + 1 : 0;
    prevX = x;
    const yp = sy(win[i].c), yc = yp + LANES[cluster % LANES.length];
    const col = BIAS_COLOR[op.bias] || "var(--ink-3)";
    // CLICKABLE: the point of plotting the sequence is to read it, and a dot you cannot open is
    // just a tally mark. Clicking one selects that post's day and focuses this same cashtag on it,
    // so the two calls can be compared as TEXT, which is where the reasoning actually lives.
    marks += `<line x1="${x.toFixed(1)}" y1="${yp.toFixed(1)}" x2="${x.toFixed(1)}" y2="${yc.toFixed(1)}"`
      + ` stroke="${col}" stroke-width="0.8" opacity="0.7"/>`
      + `<circle class="pmark" cx="${x.toFixed(1)}" cy="${yc.toFixed(1)}" r="4.2" fill="var(--surface)"`
      + ` stroke="${col}" stroke-width="1.4" data-goto-post="${escapeHtml(op.id)}"`
      + ` data-goto-day="${escapeHtml(op.d)}" style="cursor:pointer">`
      + `<title>${escapeHtml(op.d)} · ${escapeHtml(op.bias || "no bias")} — click to open this post</title></circle>`;
  }

  // (1) THE POST ITSELF — a solid rule spanning both panels, so the eye lands on it first.
  let here = "";
  if (tIdx >= 0) {
    const x = sx(tIdx).toFixed(1);
    here = `<line x1="${x}" y1="${cy0 - 6}" x2="${x}" y2="${by1}" stroke="var(--accent-strong)" stroke-width="1.6"/>`
      + `<rect x="${(+x - 31).toFixed(1)}" y="${cy0 - 22}" width="62" height="16" rx="3" fill="var(--accent-strong)"/>`
      + `<text x="${x}" y="${cy0 - 10.5}" font-size="9.5" text-anchor="middle" fill="#fff" font-weight="600">THIS POST</text>`;
  }

  // x labels
  let xl = "";
  for (const [f, anc] of [[0, "start"], [0.33, "middle"], [0.66, "middle"], [1, "end"]]) {
    const i = Math.round((win.length - 1) * f), iso = win[i].d;
    xl += `<text x="${sx(i).toFixed(1)}" y="${cy1 + 15}" font-size="10" text-anchor="${anc}"`
      + ` fill="var(--ink-3)">${MON[+iso.slice(5, 7) - 1]} ${iso.slice(2, 4)}</text>`;
  }

  // (5) BENCHMARK PANEL — both series rebased to 100 AT THE POST. A raw move in a rising tape says
  // almost nothing; the gap against SPY is the signal.
  let lower = "";
  if (tIdx >= 0 && win[tIdx].c > 0) {
    const bw = bench.filter((b) => b.d >= win[0].d && b.d <= win[win.length - 1].d);
    const bAt = (() => { let last = null; for (const b of bw) { if (b.d <= postDate) last = b; } return last; })();
    const nameS = win.map((b) => (b.c / win[tIdx].c) * 100);
    const benchS = bAt && bAt.c > 0
      ? win.map((b) => { const m = bw.filter((x) => x.d <= b.d).pop(); return m ? (m.c / bAt.c) * 100 : null; })
      : [];
    const ex = extent([...nameS, ...benchS]);
    if (ex) {
      const pad = Math.max((ex[1] - ex[0]) * 0.1, 3);
      const by = linScale(ex[0] - pad, ex[1] + pad, by1, by0);
      const poly = (ser, col, wd, dash) => {
        const pts = ser.map((v, i) => (v == null ? null : `${sx(i).toFixed(1)},${by(v).toFixed(1)}`))
          .filter(Boolean).join(" ");
        return pts ? `<polyline points="${pts}" fill="none" stroke="${col}" stroke-width="${wd}"${dash} stroke-linejoin="round"/>` : "";
      };
      lower = (band ? `<rect x="${sx(tIdx).toFixed(1)}" y="${by0}" width="${(sx(hzEndIdx) - sx(tIdx)).toFixed(1)}" height="${by1 - by0}" fill="var(--target-fill)"/>` : "")
        + `<line x1="${px0}" y1="${by(100).toFixed(1)}" x2="${px1}" y2="${by(100).toFixed(1)}" stroke="var(--line-2)" stroke-dasharray="3 2"/>`
        + `<text x="${px0 - 5}" y="${(by(100) + 3.3).toFixed(1)}" font-size="10" text-anchor="end" fill="var(--ink-3)">100</text>`
        + poly(benchS, "var(--ink-3)", 1.4, ' stroke-dasharray="5 4"') + poly(nameS, "var(--accent)", 1.8, "")
        + `<text x="${px0}" y="${by0 - 7}" font-size="10.5" fill="var(--ink-2)" font-weight="600">Rebased = 100 at the post`
        + ` <tspan font-weight="400" fill="var(--ink-3)">· ${escapeHtml(ticker)} vs SPY</tspan></text>`;
    }
  }

  // THE CROSSHAIR reads from this, so it can never disagree with what was drawn.
  S.geom = { win, px0, px1, cy0, cy1, W, H,
             yOf: (v) => sy(v), xOf: (i) => sx(i),
             lo: dom.lo, hi: dom.hi };
  const cross = `<g id="ch-cross" style="display:none;pointer-events:none">
      <line id="ch-vx" y1="${cy0}" y2="${cy1}" stroke="var(--ink-3)" stroke-width="0.8" stroke-dasharray="3 3"/>
      <line id="ch-hz" x1="${px0}" x2="${px1}" stroke="var(--ink-3)" stroke-width="0.8" stroke-dasharray="3 3"/>
      <circle id="ch-dot" r="3" fill="var(--accent)" stroke="var(--surface)" stroke-width="1.5"/>
      <g id="ch-tip"><rect id="ch-tip-bg" rx="4" fill="var(--surface)" stroke="var(--line-2)"/>
        <text id="ch-tip-t" font-size="10" font-family="var(--mono)" fill="var(--ink)"></text></g>
      <g id="ch-ytag"><rect id="ch-ytag-bg" rx="3" fill="var(--ink-2)"/>
        <text id="ch-ytag-t" font-size="9.5" font-family="var(--mono)" fill="var(--surface)" text-anchor="end"></text></g>
    </g>
    <rect id="ch-hit" x="${px0}" y="${cy0}" width="${px1 - px0}" height="${cy1 - cy0}" fill="transparent" style="cursor:crosshair"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block" role="img"
    aria-label="${escapeHtml(ticker)} daily candles with the post marked, prior posts, the stated target, the horizon band, and SPY rebased to 100">
    ${band}${grid}${body}${tgt}${xl}${here}${lower}${cross}${marks}</svg>`;
}

/**
 * Every post on `tkr` inside [from, to] — across MONTHS, not just the one on screen.
 *
 * THIS WAS A REAL DEFECT. The chart's whole claim is that the SEQUENCE is the story ("he called
 * $TSLA 1,371 times"), and it was drawing markers from `S.posts`, which holds ONE month. On $HOOD
 * at the 1Y window that showed 5 of the 30 posts actually in range — a sequence with 25 of its
 * members missing, presented as complete.
 *
 * `days.json` carries each day's ticker list, so the months worth opening are known WITHOUT
 * touching `posts/`; only those are fetched, and `getCallPosts` memoises them. A MAX window on a
 * heavily-covered name is the expensive case and is still bounded by the account's 25 months.
 */
async function postsForTicker(tkr, from, to) {
  const want = `$${tkr}`;
  const months = new Set();
  for (const [iso, rec] of Object.entries(S.days)) {
    if (from != null && iso < from) continue;
    if (to != null && iso > to) continue;
    if ((rec.tk || []).includes(want)) months.add(monthOf(iso));
  }
  const out = [];
  for (const m of [...months].sort()) {
    let posts;
    try { posts = await getCallPosts(S.handle, m); } catch (e) { continue; }
    for (const q of posts) {
      if (from != null && q.d < from) continue;
      if (to != null && q.d > to) continue;
      if (!(q.tk || []).some((t) => t.replace(/^\$/, "") === tkr)) continue;
      // DEFAULT: unfiltered. The chart is the RECORD of what he said about this ticker, and a
      // filtered record is a false one. The toggle exists because "only his spec-A calls on this
      // name" is a real question — it is just not the default reading.
      if (S.seqFiltered && !(postPasses(q) && chipPasses(q.id, tkr))) continue;
      const l = labelFor(`${q.id}|${tkr}`);
      out.push({ id: String(q.id), d: q.d, bias: l ? l.bias : "none" });
    }
  }
  out.sort((a, b) => a.d.localeCompare(b.d));
  return out;
}

// --- pane 1: the calendar ----------------------------------------------------------------------
// INTENSITY IS LOG-SCALED. Volume runs ~450 posts/month in late 2024 and ~150 by 2026, with a
// single 38-post day; on a linear ramp the whole of 2026 renders near-white and reads as "he
// stopped posting". Two signals per cell, not one: how much (intensity) and whether anything
// substantive is there (a spec A/B dot) — browsing for labelling means finding the latter.
function paneCalendar() {
  const [y, m] = S.month.split("-").map(Number);
  const first = new Date(Date.UTC(y, m - 1, 1));
  const lead = first.getUTCDay();
  const dim = new Date(Date.UTC(y, m, 0)).getUTCDate();
  const maxN = Math.max(...Object.values(S.days).map((d) => d.n || 0), 1);
  let cells = "";
  for (let i = 0; i < lead; i++) cells += `<div style="min-height:38px"></div>`;
  for (let d = 1; d <= dim; d++) {
    const iso = `${S.month}-${String(d).padStart(2, "0")}`;
    const rec = S.days[iso] || { n: 0, lab: 0, sig: 0 };
    const t = rec.n ? Math.log1p(rec.n) / Math.log1p(maxN) : 0;
    const bg = rec.n ? `color-mix(in srgb, var(--accent) ${(8 + t * 62).toFixed(0)}%, var(--surface))` : "var(--surface)";
    const ink = !rec.n ? "var(--ink-3)" : (t > 0.55 ? "#fff" : "var(--ink)");
    const sel = iso === S.day ? "box-shadow:0 0 0 2px var(--accent);" : "";
    const dots = (rec.sig ? `<span class="cal-dot" style="background:var(--conditional)"></span>` : "")
      + (rec.lab ? `<span class="cal-dot" style="background:var(--pos-text)"></span>` : "");
    cells += `<div class="cal-cell" data-day="${iso}" style="background:${bg};color:${ink};${sel}"`
      + ` title="${iso} · ${rec.n || 0} posts">`
      + `<div class="cal-top"><span class="cal-n">${d}</span>`
      + `<span class="cal-c">${rec.n || ""}</span></div>`
      + `<div class="cal-dots">${dots}</div></div>`;
  }
  // A DROPDOWN, not just arrows: 25 months is eight pages of clicking to reach the far end.
  const allMonths = [...new Set(Object.keys(S.days).map(monthOf))].sort();
  const opts = allMonths.map((mm) => {
    const [yy, m2] = mm.split("-").map(Number);
    return `<option value="${mm}"${mm === S.month ? " selected" : ""}>${MON[m2 - 1]} ${yy}</option>`;
  }).join("");
  return `<div class="card cal-card">
    <div class="cal-head"><button class="cal-nav" data-mon="-1" aria-label="Previous month">◀</button>
      <select class="cal-sel" id="cal-month" aria-label="Month">${opts}</select>
      <button class="cal-nav" data-mon="1" aria-label="Next month">▶</button></div>
    <div class="cal-dow">${["S", "M", "T", "W", "T", "F", "S"].map((d) => `<div>${d}</div>`).join("")}</div>
    <div class="cal-grid">${cells}</div>
  </div>`;
}

// --- pane 2: posts and their label chips -------------------------------------------------------
/** A target reads in its OWN units. A blanket `$` prefix produced "$+12.33%" and "$80%" on the
 *  chip — a currency mark on a relative move, which is the display-formatting-as-truth mistake the
 *  house rule about structured values exists to prevent. Only an absolute level takes a `$`. */
function targetText(l) {
  if (!l || l.target == null || l.target === "") return null;
  const raw = String(l.target).trim();
  if (l.target_type === "pct") return raw.endsWith("%") ? raw : `${raw}%`;
  if (l.target_type === "qualitative") return `“${raw}”`;
  if (l.target_type === "point" || l.target_type === "range") {
    return raw.startsWith("$") ? raw : `$${raw}`;
  }
  return raw;
}

function chipHtml(key, tkr, focused) {
  const l = labelFor(key);
  const cls = !l ? "lc-none" : (isHand(l) ? "lc-hand" : "lc-machine");
  const tone = l && isHand(l) && BIAS_COLOR[l.bias] ? ` style="--lc:${BIAS_COLOR[l.bias]}"` : "";
  let txt = `<b class="mono">$${escapeHtml(tkr)}</b>`;
  if (l) {
    const bits = [l.bias, l.action && l.action !== "none" ? l.action : null,
                  targetText(l), l.hhi || l.hlo ? `${l.hhi || l.hlo}d` : null].filter(Boolean);
    txt += (isHand(l) ? " " : ` <i>guess:</i> `) + escapeHtml(bits.join(" · "));
    const rs = reviewReasons(key);
    if (rs.length) {
      const [, what] = REVIEW_REASONS.find(([id]) => id === rs[0]) || [null, "review"];
      txt += ` <span class="gt partial" title="${escapeHtml(what)}">${escapeHtml(rs[0])}</span>`;
    }
  }
  return `<button class="lchip ${cls}${focused ? " lc-focus" : ""}" data-key="${key}" data-tkr="${tkr}"${tone}>${txt}</button>`;
}

/** The inline editor. `is_conditional` / `is_retrospective` exist in NEITHER labels.json NOR the
 *  post files, so without these two boxes the export cannot reproduce gold_labels.jsonl. */
function editorHtml(key) {
  const l = labelFor(key) || {};
  const opt = (v, cur) => `<option value="${v}"${v === (cur || "") ? " selected" : ""}>${v || "—"}</option>`;
  return `<div class="ed" data-ed="${key}">
    <div class="ed-row"><span class="ed-l">Bias</span><div class="ed-seg">
      ${BIASES.map((b) => `<button class="ed-b${l.bias === b ? " on" : ""}" data-bias="${b}">${b}`
        + `${b === "bullish" ? "<kbd>b</kbd>" : b === "bearish" ? "<kbd>s</kbd>" : ""}</button>`).join("")}
    </div></div>
    <div class="ed-row"><span class="ed-l">Action</span>
      <select class="filter-select ed-i" data-f="action">${ACTIONS.map((a) => opt(a, l.action)).join("")}</select>
      <button class="ed-b${l.action === "no_entry" ? " on" : ""}" data-action="no_entry">no_entry<kbd>n</kbd></button></div>
    <div class="ed-row"><span class="ed-l">Target</span>
      <input class="filter-select ed-i ed-sm" data-f="target" value="${escapeHtml(l.target ?? "")}">
      <select class="filter-select ed-i" data-f="target_type">${TARGET_TYPES.map((t) => opt(t, l.target_type)).join("")}</select></div>
    <div class="ed-row"><span class="ed-l">Horizon</span>
      <input class="filter-select ed-i ed-xs" data-f="hlo" value="${l.hlo ?? ""}"><span class="ed-d">–</span>
      <input class="filter-select ed-i ed-xs" data-f="hhi" value="${l.hhi ?? ""}">
      <span class="ed-note">${l.hhi || l.hlo ? "trading days · <b>stated</b>" : "none stated → <b>63d default</b>, flagged"}</span></div>
    <div class="ed-row"><span class="ed-l">Flags</span>
      <label class="chip ed-ck"><input type="checkbox" data-f="is_conditional"${l.is_conditional ? " checked" : ""}> conditional <span class="ed-note">“if X, then…”</span></label>
      <label class="chip ed-ck"><input type="checkbox" data-f="is_retrospective"${l.is_retrospective ? " checked" : ""}> retrospective <span class="ed-note">a call being recalled, not made</span></label>
    </div></div>`;
}

function panePosts() {
  const posts = dayPosts();
  if (!posts.length) {
    return `<div class="card"><div class="muted" style="font-size:12.5px">No posts on ${escapeHtml(S.day || "—")} match the current filters.</div></div>`;
  }
  const tags = focusTags();
  return posts.map((p, i) => {
    const foc = i === S.postIdx;
    const badges = [p.v && "VIDEO", p.p && "PHOTO", p.q && "QUOTE"].filter(Boolean)
      .map((b) => `<span class="gt early">${b}</span>`).join("");
    const chips = (p.tk || []).map((t) => t.replace(/^\$/, ""))
      .map((t, ci) => chipHtml(`${p.id}|${t}`, t, foc && ci === S.chipIdx)).join("");
    const ed = foc && tags[S.chipIdx] ? editorHtml(`${p.id}|${tags[S.chipIdx]}`) : "";
    return `<div class="pcard${foc ? " pfocus" : ""}" data-post="${i}">
      <div class="phead"><span class="mono ptime">${String(p.t).slice(11, 16)}</span>${badges}
        <span class="mono peng">${(p.lk ?? 0).toLocaleString()} · ${(p.vw ?? 0).toLocaleString()}</span>
        <a href="${escapeHtml(p.url || "#")}" target="_blank" rel="noopener" class="plink">open on X ↗</a></div>
      <div class="ptxt">${escapeHtml(p.txt || "")}</div>
      <div class="pchips">${chips}</div>${ed}</div>`;
  }).join("");
}

// --- pane 3: the chart + readout ---------------------------------------------------------------
async function paneChart() {
  const p = focusPost(), tkr = focusTags()[S.chipIdx];
  if (!p || !tkr) return `<div class="card muted" style="font-size:12.5px">Focus a cashtag to draw its chart.</div>`;
  const key = `${p.id}|${tkr}`;
  const [bars, bench] = await Promise.all([getCallBars(S.handle, tkr), getCallBars(S.handle, "SPY")]);
  if (!bars.length) {
    return `<div class="card"><div class="chart-h"><b class="mono">$${escapeHtml(tkr)}</b></div>
      <div class="notice" style="margin-top:8px">No committed bars for <b>$${escapeHtml(tkr)}</b> — delisted,
      renamed, or an index. The tape carries three such symbols; the pane states it rather than failing.</div></div>`;
  }
  const label = labelFor(key), res = S.results.get(key) || null;
  const [wfrom, wto] = windowRange(p.d, res);
  const others = await postsForTicker(tkr, wfrom, wto);
  const svg = chartSvg({ bars, bench, postDate: p.d, label, result: res, ticker: tkr, otherPosts: others });
  const wk = S.window || DEFAULT_WINDOW;
  const [wf, wt] = windowRange(p.d, res);
  const winLabel = wk === "MAX" ? " · every fetched bar"
    : wk === "FIT" ? " · fitted to the horizon"
    : ` · ${wf} → ${wt}`;
  const st = (l, v, sub, c) => `<div class="rd-s"><div class="rd-l">${l}</div>`
    + `<div class="rd-v mono"${c ? ` style="color:${c}"` : ""}>${v}</div><div class="rd-sub">${sub || ""}</div></div>`;
  let readout;
  if (!res) {
    readout = `<div class="notice">Not scored — this row carries no directional bias, so there is no
      side to sign a return by. Set a bias and re-run <code>vinci calls score</code>.</div>`;
  } else if (res.status === "OPEN") {
    // PROVISIONAL, AND SAID SO. The settled figures do not exist yet and are not invented; what is
    // shown is the entry (known), the clock (running) and the path so far (a fact). Every value
    // here is marked "so far" and the row is still excluded from every aggregate.
    const pct = (v) => (v == null ? DASH_ : fmtPct(v, { signed: true }));
    const tone = (v) => (v == null ? "var(--ink-2)" : v >= 0 ? "var(--pos-text)" : "var(--danger)");
    const done = res.elapsed_days != null && res.horizon_days
      ? Math.min(100, Math.round((res.elapsed_days / res.horizon_days) * 100)) : 0;
    readout = `<div class="rd-head"><span class="pill conditional">OPEN</span>
        <span class="rd-why">${res.elapsed_days ?? "?"} of ${res.horizon_days ?? "?"} trading days —
          <b>excluded from every aggregate</b> until the horizon elapses</span>
        <span class="gt ${res.horizon_assumed ? "partial" : "firm"}">${res.horizon_days}d ·
          ${res.horizon_assumed ? "63d DEFAULT, assumed" : "STATED"}</span></div>
      <div class="rd-prog"><div class="rd-prog-fill" style="width:${done}%"></div></div>
      <div class="rd-grid">
        ${st("Entry", `$${res.entry.toFixed(2)}`, `open ${res.entry_date}`)}
        ${st("Mark", res.mark == null ? DASH_ : `$${res.mark.toFixed(2)}`,
             `close ${res.mark_date ?? DASH_}`, "var(--ink-2)")}
        ${st("Unrealised", pct(res.unrealised), "so far, by bias", tone(res.unrealised))}
        ${st("SPY", pct(res.bench_unrealised), "same window", "var(--ink-2)")}
        ${st("Excess", pct(res.unrealised != null && res.bench_unrealised != null
             ? res.unrealised - res.bench_unrealised : null), "so far",
             tone(res.unrealised != null && res.bench_unrealised != null
                  ? res.unrealised - res.bench_unrealised : null))}
        ${st("MFE", pct(res.mfe_to_date), "so far", "var(--pos-text)")}
        ${st("MAE", pct(res.mae_to_date), "so far", "var(--danger)")}
        ${st("Target", res.target_px == null ? DASH_ : `$${res.target_px.toFixed(2)}`,
             res.target_px != null ? "" : (res.target_status === "implausible"
               ? "nowhere near the price — refused" : "none stated"))}
        ${st("Touched", res.target_hit_to_date == null ? DASH_
             : (res.target_hit_to_date ? "YES" : "not yet"),
             res.target_status === "counter_directional" ? "zone, so far" : "so far",
             res.target_hit_to_date ? "var(--pos-text)" : "var(--ink-2)")}
      </div>`;
  } else if (res.status !== "CLOSED") {
    readout = `<div class="rd-head"><span class="pill avoid">${res.status}</span>
      <span class="rd-why">${escapeHtml(res.detail || "")}</span></div>`;
  } else {
    const tgtNote = { resolved: "", qualitative: "qualitative — no price",
                      sign_conflict: "sign vs bias — refused", absent: "none stated",
                      no_bias: "no direction", unparseable: "could not be read",
                      implausible: "nowhere near the price — refused",
                      counter_directional: "a LEVEL against the bias, not a target"
                    }[res.target_status] || "";
    const touchNote = res.target_status === "counter_directional"
      ? "reached the zone" : "inside the band";
    readout = `<div class="rd-head"><span class="pill live">CLOSED</span>
      <span class="rd-why">horizon elapsed — counts toward aggregates</span>
      <span class="gt ${res.horizon_assumed ? "partial" : "firm"}">${res.horizon_days}d · ${res.horizon_assumed ? "63d DEFAULT, assumed" : "STATED"}</span></div>
      <div class="rd-grid">
        ${st("Entry", `$${res.entry.toFixed(2)}`, `open ${res.entry_date}`)}
        ${st("Exit", `$${res.exit.toFixed(2)}`, `close ${res.exit_date}`)}
        ${st("Return", fmtPct(res.ret, { signed: true }), "signed by bias", res.ret >= 0 ? "var(--pos-text)" : "var(--danger)")}
        ${st("SPY", res.bench_ret == null ? "—" : fmtPct(res.bench_ret, { signed: true }), "same window", "var(--ink-2)")}
        ${st("Excess", res.excess == null ? "—" : fmtPct(res.excess, { signed: true }), "vs SPY", res.excess >= 0 ? "var(--pos-text)" : "var(--danger)")}
        ${st("MFE", fmtPct(res.mfe, { signed: true }), "best", "var(--pos-text)")}
        ${st("MAE", fmtPct(res.mae, { signed: true }), "worst", "var(--danger)")}
        ${st("Target", res.target_px == null ? "—" : `$${res.target_px.toFixed(2)}`, tgtNote)}
        ${st("Touched", res.target_hit == null ? "—" : (res.target_hit ? "YES" : "no"), touchNote,
             res.target_hit ? "var(--pos-text)" : "var(--ink-2)")}
      </div>`;
  }
  return `<div class="card chart-card"><div class="chart-h"><span class="chart-bar"></span>
      <b class="mono">$${escapeHtml(tkr)}</b>
      <span class="muted">call of ${escapeHtml(p.d)}${winLabel}</span>
      <button class="chart-seq${S.seqFiltered ? " on" : ""}" id="ct-seqf"
        title="${S.seqFiltered
          ? "Filtered: the markers honour the filters above. Fewer dots than he actually posted."
          : "Unfiltered: every post on this ticker in the window. The chart is the record of what he said, and a filtered record is a false one."}">
        ${others.length} post${others.length === 1 ? "" : "s"} on $${escapeHtml(tkr)} ·
        ${S.seqFiltered ? "filtered" : "unfiltered"}</button>
      <span class="chart-follow">
        ${WINDOWS.map(([k]) => `<button class="wbtn${(S.window || DEFAULT_WINDOW) === k ? " on" : ""}" data-win="${k}"`
          + ` title="${k === "FIT" ? "fit the scored horizon" : k === "MAX" ? "every fetched bar" : "around the post"}">${k}</button>`).join("")}
      </span></div>
      ${svg || `<div class="notice">Not enough bars inside the window to draw.</div>`}</div>
    <div class="card rd-card">${readout}</div>`;
}

/** TRADING-VIEW-STYLE READOUT. Hovering the plot names the bar under the pointer — date, OHLC, and
 *  the price at the cursor's own height — because a chart you cannot interrogate forces the reader
 *  back to the raw file to answer "what was it on the 14th". Reads S.geom, which is written by the
 *  same call that drew the SVG, so the crosshair can never report a bar that was not plotted. */
function wireCrosshair(root) {
  const svg = root.querySelector("#ct-chart svg");
  const g = S.geom;
  if (!svg || !g || !g.win.length) return;
  const cross = svg.querySelector("#ch-cross");
  if (!cross) return;
  const el = (id) => svg.querySelector(id);
  const pt = svg.createSVGPoint();

  const move = (ev) => {
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    pt.x = ev.clientX; pt.y = ev.clientY;
    const loc = pt.matrixTransform(ctm.inverse());
    const n = g.win.length;
    const frac = (loc.x - g.px0) / Math.max(g.px1 - g.px0, 1);
    const i = Math.max(0, Math.min(n - 1, Math.round(frac * (n - 1))));
    const b = g.win[i];
    if (!b) return;
    const x = g.xOf(i), y = Math.max(g.cy0, Math.min(g.cy1, loc.y));
    cross.style.display = "";
    el("#ch-vx").setAttribute("x1", x); el("#ch-vx").setAttribute("x2", x);
    el("#ch-hz").setAttribute("y1", y); el("#ch-hz").setAttribute("y2", y);
    el("#ch-dot").setAttribute("cx", x); el("#ch-dot").setAttribute("cy", g.yOf(b.c));

    // the price at the CURSOR's height, not the bar's close — that is what a reader is measuring
    const atCursor = g.lo + (1 - (y - g.cy0) / Math.max(g.cy1 - g.cy0, 1)) * (g.hi - g.lo);
    const ytag = el("#ch-ytag"), ybg = el("#ch-ytag-bg"), ytxt = el("#ch-ytag-t");
    ytxt.textContent = atCursor.toFixed(2);
    ytag.setAttribute("transform", `translate(0, ${y})`);
    ytxt.setAttribute("x", g.px0 - 5); ytxt.setAttribute("y", 3.4);
    ybg.setAttribute("x", g.px0 - 5 - (ytxt.getComputedTextLength() + 8));
    ybg.setAttribute("y", -7.5); ybg.setAttribute("height", 15);
    ybg.setAttribute("width", ytxt.getComputedTextLength() + 8);

    const pct = b.o > 0 ? ((b.c / b.o - 1) * 100).toFixed(2) : "0.00";
    const txt = el("#ch-tip-t"), bg = el("#ch-tip-bg");
    txt.textContent = `${b.d}  O ${b.o.toFixed(2)}  H ${b.h.toFixed(2)}  `
      + `L ${b.l.toFixed(2)}  C ${b.c.toFixed(2)}  ${pct >= 0 ? "+" : ""}${pct}%`;
    txt.setAttribute("y", g.cy0 + 12);
    const w = txt.getComputedTextLength() + 12;
    // flip the tip to the left of the cursor near the right edge, so it never runs off the canvas
    const tx = x + 8 + w > g.px1 ? x - 8 - w : x + 8;
    txt.setAttribute("x", tx + 6);
    bg.setAttribute("x", tx); bg.setAttribute("y", g.cy0 + 1);
    bg.setAttribute("width", w); bg.setAttribute("height", 16);
  };
  // Listen on the SVG ROOT, not the capture rect: the post markers sit above that rect so they can
  // be clicked, and a rect-only listener would drop the crosshair whenever the pointer crossed one.
  svg.addEventListener("mousemove", move);
  svg.addEventListener("mouseleave", () => { cross.style.display = "none"; });
  svg.addEventListener("click", async (ev) => {
    const m = ev.target.closest && ev.target.closest("[data-goto-post]");
    if (!m) return;
    ev.stopPropagation();
    const day = m.dataset.gotoDay, id = m.dataset.gotoPost;
    if (monthOf(day) !== S.month) await loadMonth(monthOf(day));
    S.day = day;
    const posts = dayPosts();
    const pi = posts.findIndex((q) => String(q.id) === id);
    // A post can be filtered OUT of the day list (unlabelled-only, a class filter). Jumping to a
    // day and landing on the wrong post would be worse than saying so, so the filters are cleared
    // for this jump rather than silently mis-focusing.
    if (pi < 0) {
      S.filters = { ticker: "", spec: "", cls: "", bias: "", video: false, review: "",
                    unlabelled: false };
    }
    const posts2 = dayPosts();
    S.postIdx = Math.max(0, posts2.findIndex((q) => String(q.id) === id));
    const tags = focusTags();
    const ci = tags.indexOf(String(S.ticker || "").toUpperCase());
    S.chipIdx = ci >= 0 ? ci : 0;
    await paint(root);
  });
}

// --- export ------------------------------------------------------------------------------------
/** JSONL in gold_labels.jsonl's exact shape, so it merges straight back into the pipeline. */
function exportJsonl() {
  const byId = new Map(S.posts.map((p) => [String(p.id), p]));
  const rows = [];
  for (const [key, patch] of Object.entries(S.edits)) {
    const [id, tkr] = key.split("|");
    const post = byId.get(id);
    const l = labelFor(key) || {};
    rows.push(JSON.stringify({
      tweet_id: id, date: post ? post.d : null,
      quarter: post ? quarterOf(post.d) : null, ticker: tkr,
      bias: l.bias ?? null, action: l.action ?? "none",
      target: l.target ?? null, target_type: l.target_type ?? "none",
      horizon_lo_days: l.hlo ?? null, horizon_hi_days: l.hhi ?? null,
      is_conditional: Boolean(l.is_conditional), is_retrospective: Boolean(l.is_retrospective),
      specificity: l.spec ?? null, has_video: post ? Boolean(post.v) : null,
      labeller: "hand", text: post ? post.txt : null,
    }));
  }
  const blob = new Blob([rows.join("\n") + (rows.length ? "\n" : "")], { type: "application/x-ndjson" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `gold_labels_${S.handle}.jsonl`;
  a.click();
  URL.revokeObjectURL(a.href);
  return rows.length;
}

// --- shell -------------------------------------------------------------------------------------
function toolbar(tickers) {
  const counts = {};
  for (const v of Object.values(S.labels || {})) {
    if (v && v.spec) counts[v.spec] = (counts[v.spec] || 0) + 1;
  }
  // review-queue counts, computed over the whole corpus so the operator can see how much work
  // each reason actually represents before choosing one
  const rev = { any: 0 };
  for (const key of Object.keys(S.labels || {})) {
    const rs = reviewReasons(key);
    if (!rs.length) continue;
    rev.any += 1;
    for (const r of rs) rev[r] = (rev[r] || 0) + 1;
  }
  const bcount = {};
  for (const v of Object.values(S.labels || {})) {
    if (v && v.bias) bcount[v.bias] = (bcount[v.bias] || 0) + 1;
  }
  const accs = S.accounts.accounts;
  const a = accs.find((x) => x.handle === S.handle) || accs[0];
  const f = S.filters;
  const sel = accs.length > 1 || true
    ? `<select class="filter-select" id="ct-acct" title="X account">
         ${accs.map((x) => `<option value="${x.handle}"${x.handle === S.handle ? " selected" : ""}>${escapeHtml(x.display)}</option>`).join("")}
       </select>` : "";
  return `<div class="ct-bar">
    ${sel}
    <select class="filter-select" id="ct-tkr"><option value="">All tickers (${tickers.length})</option>
      ${tickers.map((t) => `<option value="${t}"${f.ticker === t ? " selected" : ""}>$${t}</option>`).join("")}</select>
    <select class="filter-select" id="ct-spec"><option value="">Spec: any</option>
      ${SPEC_DEF.map(([x, what]) => `<option value="${x}"${f.spec === x ? " selected" : ""}>Spec ${x} — ${escapeHtml(what)}</option>`).join("")}</select>
    <select class="filter-select" id="ct-bias"><option value="">Bias: any</option>
      ${BIASES.map((b) => `<option value="${b}"${f.bias === b ? " selected" : ""}>${b}${
        bcount[b] ? ` (${bcount[b].toLocaleString()})` : ""}</option>`).join("")}
      <option value="__none__"${f.bias === "__none__" ? " selected" : ""}>unlabelled (no chip)</option>
    </select>
    <select class="filter-select" id="ct-class"><option value="">All classes</option>
      ${CLASSES.map((c) => `<option value="${c}"${f.cls === c ? " selected" : ""}>${c.replace(/_/g, " ")}</option>`).join("")}</select>
    <label class="chip"><input type="checkbox" id="ct-vid"${f.video ? " checked" : ""}> video</label>
    <select class="filter-select" id="ct-rev" title="A derived queue — not the upstream needs_review flag, which is true on 73% of rows">
      <option value="">Review: off</option>
      <option value="any"${f.review === "any" ? " selected" : ""}>Review queue — any reason (${(rev.any || 0).toLocaleString()})</option>
      ${REVIEW_REASONS.map(([id, what]) => `<option value="${id}"${f.review === id ? " selected" : ""}>· ${escapeHtml(what)} (${(rev[id] || 0).toLocaleString()})</option>`).join("")}
    </select>
    <label class="chip ct-hot"><input type="checkbox" id="ct-unl"${f.unlabelled ? " checked" : ""}> unlabelled only</label>
    <div class="ct-right">
      <span class="ct-count"><b class="mono">${a.n_hand_labels + Object.keys(S.edits).length}</b> hand labels</span>
      <span class="muted">· Scoreboard unlocks at 500</span>
      <button class="ct-exp" id="ct-export">Export JSONL</button>
    </div>
    <details class="ct-key"><summary>What do Spec A–D mean?</summary>
      <div class="ct-key-body">
        ${SPEC_DEF.map(([t, what, why]) => {
          const n = counts[t] || 0;
          return `<div class="ct-key-row"><span class="gt ${t === "A" ? "firm" : t === "D" ? "none" : "early"}">${t}</span>
            <span class="ct-key-w">${escapeHtml(what)}</span>
            <span class="ct-key-y">${escapeHtml(why)}</span>
            <span class="ct-key-n mono">${n.toLocaleString()}</span></div>`;
        }).join("")}
        <div class="ct-key-foot">Measured across all ${Object.values(counts).reduce((a, b) => a + b, 0).toLocaleString()}
          labelled rows in this account, not asserted. A and B both name a target and a direction;
          they differ on whether the author put a clock on it.</div>
      </div></details></div>`;
}


async function paint(root) {
  const tickers = [...new Set(Object.values(S.days).flatMap((d) => d.tk || []))]
    .map((t) => t.replace(/^\$/, "")).sort();
  root.querySelector("#ct-tools").innerHTML = toolbar(tickers);
  root.querySelector("#ct-cal").innerHTML = paneCalendar();
  root.querySelector("#ct-posts").innerHTML = panePosts();
  root.querySelector("#ct-chart").innerHTML = `<div class="card muted" style="font-size:12.5px">Drawing…</div>`;
  root.querySelector("#ct-chart").innerHTML = await paneChart();
  wire(root);
  wireCrosshair(root);
  writeUrl();
  const foc = root.querySelector(".pfocus");
  if (foc) foc.scrollIntoView({ block: "nearest" });
}

// --- interaction -------------------------------------------------------------------------------
function setPatch(key, patch) {
  S.edits[key] = { ...(S.edits[key] || {}), ...patch };
  saveEdits();
}

function wire(root) {
  const repaint = () => paint(root);
  const q = (sel, fn, ev = "change") => root.querySelectorAll(sel).forEach((el) => el.addEventListener(ev, fn));

  const acct = root.querySelector("#ct-acct");
  if (acct) acct.addEventListener("change", async (e) => {
    S.handle = e.target.value; S.day = null; S.month = null; S.postIdx = 0; S.chipIdx = 0;
    await boot(root); });
  const bindF = (id, key, prop) => {
    const el = root.querySelector(id);
    if (el) el.addEventListener("change", (e) => {
      S.filters[key] = prop === "checked" ? e.target.checked : e.target.value;
      S.postIdx = 0; S.chipIdx = 0; repaint(); });
  };
  bindF("#ct-tkr", "ticker", "value"); bindF("#ct-spec", "spec", "value");
  bindF("#ct-class", "cls", "value"); bindF("#ct-bias", "bias", "value");
  const msel = root.querySelector("#cal-month");
  if (msel) msel.addEventListener("change", async (e) => {
    await gotoMonth(e.target.value); repaint(); });
  bindF("#ct-vid", "video", "checked"); bindF("#ct-rev", "review", "value");
  bindF("#ct-unl", "unlabelled", "checked");

  const exp = root.querySelector("#ct-export");
  if (exp) exp.addEventListener("click", () => {
    const n = exportJsonl();
    exp.textContent = n ? `Exported ${n}` : "Nothing edited yet";
    setTimeout(() => { exp.textContent = "Export JSONL"; }, 1800);
  });

  q(".cal-cell", (e) => {
    S.day = e.currentTarget.dataset.day; S.postIdx = 0; S.chipIdx = 0; repaint(); }, "click");
  q(".cal-nav", async (e) => {
    const [y, m] = S.month.split("-").map(Number);
    const d = new Date(Date.UTC(y, m - 1 + Number(e.currentTarget.dataset.mon), 1));
    await gotoMonth(d.toISOString().slice(0, 7)); repaint(); }, "click");
  q(".ct-mo", async (e) => { await gotoMonth(e.currentTarget.dataset.monJump); repaint(); }, "click");
  const sq = root.querySelector("#ct-seqf");
  if (sq) sq.addEventListener("click", (e) => {
    e.stopPropagation(); S.seqFiltered = !S.seqFiltered; repaint(); });
  q(".wbtn", (e) => {
    e.stopPropagation();
    S.window = e.currentTarget.dataset.win; repaint(); }, "click");
  q(".pcard", (e) => {
    S.postIdx = Number(e.currentTarget.dataset.post); S.chipIdx = 0; repaint(); }, "click");
  q(".lchip", (e) => {
    e.stopPropagation();
    const card = e.currentTarget.closest(".pcard");
    S.postIdx = Number(card.dataset.post);
    S.chipIdx = [...card.querySelectorAll(".lchip")].indexOf(e.currentTarget);
    S.ticker = e.currentTarget.dataset.tkr;
    S.tweetId = e.currentTarget.dataset.key.split("|")[0];
    repaint(); }, "click");

  const edKey = () => { const p = focusPost(), t = focusTags()[S.chipIdx]; return p && t ? `${p.id}|${t}` : null; };
  q(".ed-b", (e) => {
    const k = edKey(); if (!k) return;
    const b = e.currentTarget.dataset.bias, a = e.currentTarget.dataset.action;
    setPatch(k, b ? { bias: b } : { action: a }); repaint(); }, "click");
  q(".ed .ed-i", (e) => {
    const k = edKey(); if (!k) return;
    const f = e.currentTarget.dataset.f;
    let v = e.currentTarget.value;
    if (f === "hlo" || f === "hhi") v = v.trim() === "" ? null : Number(v);
    setPatch(k, { [f]: v }); repaint(); });
  q(".ed input[type=checkbox]", (e) => {
    const k = edKey(); if (!k) return;
    setPatch(k, { [e.currentTarget.dataset.f]: e.currentTarget.checked }); repaint(); });
}

async function gotoMonth(month) {
  await loadMonth(month);
  const inMonth = Object.keys(S.days).filter((d) => monthOf(d) === month && S.days[d].n).sort();
  S.day = inMonth[inMonth.length - 1] || `${month}-01`;
  S.postIdx = 0; S.chipIdx = 0;
}

/** Keys move FOCUS; the chart follows. Nothing here navigates. */
function keyboard(root) {
  if (window.__ctKeys) document.removeEventListener("keydown", window.__ctKeys);
  const handler = async (e) => {
    if (!document.body.contains(root)) { document.removeEventListener("keydown", handler); return; }
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "select" || tag === "textarea") {
      if (e.key === "Escape") e.target.blur();
      return;                                   // never steal keys from a field being typed into
    }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const posts = dayPosts(), tags = focusTags(), key = tags[S.chipIdx]
      ? `${focusPost().id}|${tags[S.chipIdx]}` : null;
    const days = Object.keys(S.days).filter((d) => monthOf(d) === S.month).sort();
    let hit = true;
    switch (e.key) {
      case "j": S.postIdx = Math.min(S.postIdx + 1, Math.max(posts.length - 1, 0)); S.chipIdx = 0; break;
      case "k": S.postIdx = Math.max(S.postIdx - 1, 0); S.chipIdx = 0; break;
      case "l": S.chipIdx = Math.min(S.chipIdx + 1, Math.max(tags.length - 1, 0)); break;
      case "h": S.chipIdx = Math.max(S.chipIdx - 1, 0); break;
      case "b": if (key) setPatch(key, { bias: "bullish" }); break;
      case "s": if (key) setPatch(key, { bias: "bearish" }); break;
      case "n": if (key) setPatch(key, { action: "no_entry" }); break;
      case "Backspace": if (key) { delete S.edits[key]; saveEdits(); } break;
      case "ArrowLeft": case "ArrowRight": {
        const i = days.indexOf(S.day);
        const j = e.key === "ArrowLeft" ? i - 1 : i + 1;
        if (j >= 0 && j < days.length) { S.day = days[j]; S.postIdx = 0; S.chipIdx = 0; }
        break;
      }
      default: hit = false;
    }
    if (!hit) return;
    e.preventDefault();
    await paint(root);
  };
  window.__ctKeys = handler;
  document.addEventListener("keydown", handler);
}

// --- entry -------------------------------------------------------------------------------------
async function boot(root) {
  loadEdits();
  [S.days, S.labels, S.results] = await Promise.all([
    getCallDays(S.handle), getCallLabels(S.handle), getCallResults(S.handle),
  ]);
  if (!S.day) {
    const withPosts = Object.keys(S.days).filter((d) => S.days[d].n).sort();
    S.day = withPosts[withPosts.length - 1] || Object.keys(S.days).sort().pop();
  }
  await loadMonth(monthOf(S.day));
  // A DEEP LINK MUST LAND ON ITS OWN CALL. The URL carries the post and the cashtag; without this
  // an incoming #/calls/<h>/<date>/TSLA/<id> opened the right DAY and then focused whatever
  // happened to be first — so a shared link pointed at the wrong chart, silently.
  if (S.tweetId || S.ticker) {
    const posts = dayPosts();
    const want = String(S.ticker || "").toUpperCase();
    let pi = S.tweetId ? posts.findIndex((p) => String(p.id) === String(S.tweetId)) : -1;
    // A TICKER-ONLY LINK (#/calls/<h>/<date>/HOOD) must find the post that names it. Without this
    // the ticker was matched against whatever post happened to be first, missed, and the screen
    // opened on an unrelated cashtag — the link looked honoured and was not.
    if (pi < 0 && want) {
      pi = posts.findIndex((p) => (p.tk || []).some((t) => t.replace(/^\$/, "").toUpperCase() === want));
    }
    if (pi >= 0) S.postIdx = pi;
    const tags = focusTags();
    const ci = tags.indexOf(want);
    if (ci >= 0) S.chipIdx = ci;
  }
  await paint(root);
}

export async function render(root, params, { item, frame }) {
  S.accounts = await getCallAccounts();
  const known = new Set(S.accounts.accounts.map((a) => a.handle));
  // The handle segment is OPTIONAL, so an old #/calls/<date> link keeps working on the default.
  const rest = [...(params || [])];
  S.handle = known.has(rest[0]) ? rest.shift() : S.accounts.default;
  S.day = /^\d{4}-\d{2}-\d{2}$/.test(rest[0] || "") ? rest.shift() : null;
  S.ticker = rest.shift() || null;
  S.tweetId = rest.shift() || null;

  // TWO COLUMNS, not three. The chart is the evidence and was getting the narrowest share of a
  // 1760px screen; navigation (calendar) and the work queue (posts) are both narrow by nature, so
  // they stack in one rail and the chart takes everything else.
  root.innerHTML = frame(item, {
    bodyHtml: `<div id="ct-tools"></div>
      <div class="ct-panes">
        <div class="ct-rail"><div id="ct-cal"></div><div id="ct-posts"></div></div>
        <div id="ct-chart"></div>
      </div>
      <div class="ct-hints">
        <span><kbd>j</kbd><kbd>k</kbd> post</span><span><kbd>h</kbd><kbd>l</kbd> cashtag</span>
        <span><kbd>b</kbd><kbd>s</kbd> bias</span><span><kbd>n</kbd> no_entry</span>
        <span><kbd>←</kbd><kbd>→</kbd> day</span><span><kbd>⌫</kbd> clear</span>
        <span class="ct-hint-r">nothing here navigates — every key moves focus, and the chart follows</span>
      </div>`,
  });
  await boot(root);
  keyboard(root);
}
