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
import { escapeHtml, fmtPct } from "../../lib/format.js";
import {
  getCallAccounts, getCallBars, getCallDays, getCallLabels, getCallPosts, getCallResults,
} from "../../lib/snapshots.js";

const BIAS_COLOR = { bullish: "var(--pos-text)", bearish: "var(--danger)" };
const ACTIONS = ["", "enter_long", "enter_short", "add", "trim", "exit", "no_entry", "hold", "none"];
const BIASES = ["bullish", "bearish", "neutral", "none"];
const TARGET_TYPES = ["none", "point", "range", "pct", "qualitative"];
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const S = {
  handle: null, day: null, ticker: null, tweetId: null,
  accounts: null, days: null, labels: null, results: null,
  posts: [], month: null,
  postIdx: 0, chipIdx: 0,
  filters: { ticker: "", spec: "", video: false, review: false, unlabelled: false },
  edits: {},                       // key -> patch, mirrored to localStorage
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

/** Posts on the selected day, after filters. Filtering is what makes the tool usable at 5,641. */
function dayPosts() {
  const f = S.filters;
  return S.posts.filter((p) => {
    if (p.d !== S.day) return false;
    if (f.video && !p.v) return false;
    const tags = (p.tk || []).map((t) => t.replace(/^\$/, ""));
    if (f.ticker && !tags.includes(f.ticker)) return false;
    if (f.spec || f.review || f.unlabelled) {
      const ok = tags.some((t) => {
        const l = labelFor(`${p.id}|${t}`);
        if (f.spec && (!l || l.spec !== f.spec)) return false;
        if (f.review && !(l && l.needs_review)) return false;
        if (f.unlabelled && isHand(l)) return false;
        return true;
      });
      if (!ok) return false;
    }
    return true;
  });
}
const focusPost = () => dayPosts()[S.postIdx] || null;
function focusTags() {
  const p = focusPost();
  return p ? (p.tk || []).map((t) => t.replace(/^\$/, "")) : [];
}

// --- chart -------------------------------------------------------------------------------------
const WINDOW_BEFORE_M = 3, WINDOW_AFTER_M = 12;
function shift(iso, months) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCMonth(d.getUTCMonth() + months);
  return d.toISOString().slice(0, 10);
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
  const from = shift(postDate, -WINDOW_BEFORE_M), to = shift(postDate, WINDOW_AFTER_M);
  const win = bars.filter((b) => b.d >= from && b.d <= to);
  if (win.length < 2) return null;

  const W = 880, H = 470, padL = 44, padR = 12, cy0 = 26, cy1 = 300, by0 = 358, by1 = 448;
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
  const step = [1, 2, 5, 10, 20, 25, 50, 100, 200].find((g) => span / g <= 7) || 500;
  let grid = "";
  for (let v = Math.ceil(dom.lo / step) * step; v < dom.hi; v += step) {
    const y = sy(v).toFixed(1);
    grid += `<line x1="${px0}" y1="${y}" x2="${px1}" y2="${y}" stroke="var(--line)"/>`
      + `<text x="${px0 - 5}" y="${+y + 3.3}" font-size="10" text-anchor="end" fill="var(--ink-3)">${v}</text>`;
  }

  // (4) HORIZON BAND — post -> horizon end. Target touched inside it is the win condition.
  let band = "";
  const hzEndIdx = result && result.exit_date ? idxOf(result.exit_date) : -1;
  if (tIdx >= 0 && hzEndIdx > tIdx) {
    band = `<rect x="${sx(tIdx).toFixed(1)}" y="${cy0}" width="${(sx(hzEndIdx) - sx(tIdx)).toFixed(1)}"`
      + ` height="${cy1 - cy0}" fill="var(--target-fill)"/>`
      + `<line x1="${sx(hzEndIdx).toFixed(1)}" y1="${cy0}" x2="${sx(hzEndIdx).toFixed(1)}" y2="${cy1}"`
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
    marks += `<line x1="${x.toFixed(1)}" y1="${yp.toFixed(1)}" x2="${x.toFixed(1)}" y2="${yc.toFixed(1)}"`
      + ` stroke="${col}" stroke-width="0.8" opacity="0.7"/>`
      + `<circle cx="${x.toFixed(1)}" cy="${yc.toFixed(1)}" r="4.2" fill="var(--surface)" stroke="${col}" stroke-width="1.4"/>`;
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

  return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block" role="img"
    aria-label="${escapeHtml(ticker)} daily candles with the post marked, prior posts, the stated target, the horizon band, and SPY rebased to 100">
    ${band}${grid}${body}${tgt}${marks}${xl}${here}${lower}</svg>`;
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
    cells += `<div class="cal-cell" data-day="${iso}" style="background:${bg};color:${ink};${sel}">`
      + `<div class="cal-n">${d}</div><div class="cal-c">${rec.n || "·"}</div>`
      + `<div class="cal-dots">${dots}</div></div>`;
  }
  return `<div class="card cal-card">
    <div class="cal-head"><button class="cal-nav" data-mon="-1" aria-label="Previous month">◀</button>
      <span>${MON[m - 1]} ${y}</span>
      <button class="cal-nav" data-mon="1" aria-label="Next month">▶</button></div>
    <div class="cal-dow">${["S", "M", "T", "W", "T", "F", "S"].map((d) => `<div>${d}</div>`).join("")}</div>
    <div class="cal-grid">${cells}</div>
    <div class="cal-key"><div>Intensity = posts, <b>log-scaled</b></div>
      <div><span class="cal-dot" style="background:var(--conditional)"></span> spec A/B
      &nbsp;<span class="cal-dot" style="background:var(--pos-text)"></span> hand-labelled</div></div>
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
    if (l.needs_review) txt += ` <span class="gt partial">review</span>`;
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
  const others = [];
  for (const q of S.posts) {
    if ((q.tk || []).some((t) => t.replace(/^\$/, "") === tkr)) {
      const l = labelFor(`${q.id}|${tkr}`);
      others.push({ id: q.id, d: q.d, bias: l ? l.bias : "none" });
    }
  }
  const svg = chartSvg({ bars, bench, postDate: p.d, label, result: res, ticker: tkr, otherPosts: others });
  const st = (l, v, sub, c) => `<div class="rd-s"><div class="rd-l">${l}</div>`
    + `<div class="rd-v mono"${c ? ` style="color:${c}"` : ""}>${v}</div><div class="rd-sub">${sub || ""}</div></div>`;
  let readout;
  if (!res) {
    readout = `<div class="notice">Not scored — this row carries no directional bias, so there is no
      side to sign a return by. Set a bias and re-run <code>vinci calls score</code>.</div>`;
  } else if (res.status !== "CLOSED") {
    const why = res.status === "OPEN"
      ? `Its ${res.horizon_days}-day horizon has not elapsed, so it is excluded from every aggregate.`
      : escapeHtml(res.detail || "");
    readout = `<div class="rd-head"><span class="pill conditional">${res.status}</span>
      <span class="rd-why">${why}</span></div>`;
  } else {
    const tgtNote = { resolved: "", qualitative: "qualitative — no price", sign_conflict: "sign vs bias — refused",
                      absent: "none stated", no_bias: "no direction", unparseable: "could not be read" }[res.target_status] || "";
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
        ${st("Touched", res.target_hit == null ? "—" : (res.target_hit ? "YES" : "no"), "inside the band",
             res.target_hit ? "var(--pos-text)" : "var(--ink-2)")}
      </div>`;
  }
  return `<div class="card chart-card"><div class="chart-h"><span class="chart-bar"></span>
      <b class="mono">$${escapeHtml(tkr)}</b>
      <span class="muted">call of ${escapeHtml(p.d)} · −${WINDOW_BEFORE_M}mo / +${WINDOW_AFTER_M}mo</span>
      <span class="gt firm chart-follow">follows the focused chip</span></div>
      ${svg || `<div class="notice">Not enough bars inside the window to draw.</div>`}</div>
    <div class="card rd-card">${readout}</div>`;
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
      ${["A", "B", "C", "D"].map((x) => `<option value="${x}"${f.spec === x ? " selected" : ""}>Spec ${x}</option>`).join("")}</select>
    <label class="chip"><input type="checkbox" id="ct-vid"${f.video ? " checked" : ""}> video</label>
    <label class="chip"><input type="checkbox" id="ct-rev"${f.review ? " checked" : ""}> needs review</label>
    <label class="chip ct-hot"><input type="checkbox" id="ct-unl"${f.unlabelled ? " checked" : ""}> unlabelled only</label>
    <div class="ct-right">
      <span class="ct-count"><b class="mono">${a.n_hand_labels + Object.keys(S.edits).length}</b> hand labels</span>
      <span class="muted">· Scoreboard unlocks at 500</span>
      <button class="ct-exp" id="ct-export">Export JSONL</button>
    </div></div>`;
}

function timelineStrip() {
  const months = [...new Set(Object.keys(S.days).map(monthOf))].sort();
  const tot = {};
  for (const [iso, r] of Object.entries(S.days)) tot[monthOf(iso)] = (tot[monthOf(iso)] || 0) + (r.n || 0);
  const max = Math.max(...Object.values(tot), 1);
  return `<div class="card ct-strip"><div class="ct-strip-in">${months.map((m) => {
    const on = m === S.month;
    return `<div class="ct-mo${on ? " on" : ""}" data-mon-jump="${m}" title="${m}: ${tot[m] || 0} posts">
      <div class="ct-mo-b" style="height:${(30 * (tot[m] || 0) / max).toFixed(0)}px"></div>
      <div class="ct-mo-l">${(+m.slice(5) === 1 || +m.slice(5) === 7 || on) ? m.slice(2) : ""}</div></div>`;
  }).join("")}</div></div>`;
}

async function paint(root) {
  const tickers = [...new Set(Object.values(S.days).flatMap((d) => d.tk || []))]
    .map((t) => t.replace(/^\$/, "")).sort();
  root.querySelector("#ct-tools").innerHTML = toolbar(tickers) + timelineStrip();
  root.querySelector("#ct-cal").innerHTML = paneCalendar();
  root.querySelector("#ct-posts").innerHTML = panePosts();
  root.querySelector("#ct-chart").innerHTML = `<div class="card muted" style="font-size:12.5px">Drawing…</div>`;
  root.querySelector("#ct-chart").innerHTML = await paneChart();
  wire(root);
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
  bindF("#ct-vid", "video", "checked"); bindF("#ct-rev", "review", "checked");
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
    const pi = posts.findIndex((p) => String(p.id) === String(S.tweetId));
    if (pi >= 0) S.postIdx = pi;
    const tags = focusTags();
    const ci = tags.indexOf(String(S.ticker || "").toUpperCase());
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

  root.innerHTML = frame(item, {
    bodyHtml: `<div id="ct-tools"></div>
      <div class="ct-panes"><div id="ct-cal"></div><div id="ct-posts"></div><div id="ct-chart"></div></div>
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
