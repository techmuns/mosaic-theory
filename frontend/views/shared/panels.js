// MONITOR PANELS — the grid, and the only renderer of it.
//
// The artifact carries STRUCTURED VALUES ONLY (`panels[]` in the monitor snapshot, produced by
// vinci/panels_emit.py). Every format decision lives here, so a change to how a figure READS never
// touches what the artifact SAYS. There is deliberately no second renderer: an earlier cut drew
// this design in Python too, which is the same page drawn twice in two languages.
//
// THE GATING RULE IS THE REASON THIS FILE EXISTS, and it is halfway enforced upstream: a panel that
// does not apply to a name EMITS NO ROW, so there is nothing here to hide. Every row that arrives
// renders — READY with its value, REFUSED loudly with the requirement that failed and the
// extractor's own words. The two must never look alike; that is this repo's absent-vs-broken class,
// and a grid of tiles is where it would recur most cheaply, because a reader scanning twelve tiles
// reads silence as "fine".
//
// EVERY TILE PRINTS WHAT WOULD CHANGE THE CALL, in the main body rather than an on-demand tier. It
// is decision text, not provenance: the design's guard is that a panel which cannot answer it is
// decoration, and hiding the answer behind a disclosure triangle would make the guard unreadable at
// exactly the moment it matters.
//
// EXHIBITS CITE VIA ENDNOTES, never an inline caption — house rule. Each exhibit's provenance
// resolves to the tile's own Sources tier; nothing prints "Source: …" beneath a chart.
import { getMonitor, verdictWord } from "../../lib/snapshots.js";
import { DASH, escapeHtml, fmtDate, fmtInt, fmtPrice } from "../../lib/format.js";

const pp = (v, d = 2) => (typeof v === "number" && isFinite(v)
  ? (v >= 0 ? "+" : "") + (v * 100).toFixed(d) + "pp" : DASH);
const x = (v, d = 1) => (typeof v === "number" && isFinite(v) ? v.toFixed(d) + "x" : DASH);
const pctc = (v, d = 0) => (typeof v === "number" && isFinite(v)
  ? (v * 100).toFixed(d) + "%" : DASH);
const rate = (v, d = 2) => (typeof v === "number" && isFinite(v) ? v.toFixed(d) + "%" : DASH);

// --- exhibits -------------------------------------------------------------------------------
// Geometry is computed from the SAME numbers that are printed beside it, so a bar can never
// disagree with its own label — the failure the design's first draft was rebuilt for.

function sparkline(series, { current, nClose, excludesCurrent }) {
  if (!Array.isArray(series) || series.length < 2) return "";
  const vals = series.map((p) => p[1]);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = (hi - lo) || 1;
  const W = 180, H = 34, step = W / (vals.length - 1);
  const pts = vals.map((v, i) => `${(i * step).toFixed(1)},${(H - (v - lo) / span * H).toFixed(1)}`);
  // THE HISTORICAL WINDOW IS SHADED, THE CURRENT MARK IS A SEPARATE DOT. The range band
  // (low/high/median/percentile) is struck over n_closes and EXCLUDES the appended current point,
  // so SMPL's 5.56x genuinely sits below its own 6.11x low. Drawn as one undifferentiated line it
  // reads as a glitch, and the tempting fix — widening the band — would restate the percentile the
  // panel turns on.
  const cut = excludesCurrent ? pts.length - 1 : pts.length;
  const hist = pts.slice(0, cut).join(" ");
  const last = pts[pts.length - 1].split(",");
  return `<svg class="pn-spark" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img"
    aria-label="${escapeHtml(String(nClose || vals.length))} historical closes, current mark marked separately">
    <polyline points="${hist}" fill="none" stroke="currentColor" stroke-width="1.2"/>
    ${excludesCurrent ? `<polyline points="${pts.slice(cut - 1).join(" ")}" fill="none"
       stroke="var(--pn-hot)" stroke-width="1.2" stroke-dasharray="2 2"/>` : ""}
    <circle cx="${last[0]}" cy="${last[1]}" r="2.6" fill="var(--pn-hot)"/></svg>`;
}

function rangeBar({ low, high, median, current }) {
  if (![low, high, current].every((v) => typeof v === "number" && isFinite(v))) return "";
  const lo = Math.min(low, current), hi = Math.max(high, current);
  const span = (hi - lo) || 1;
  const at = (v) => ((v - lo) / span * 100).toFixed(2);
  const med = (typeof median === "number" && isFinite(median))
    ? `<line x1="${at(median)}" y1="1.5" x2="${at(median)}" y2="10.5" stroke="currentColor"
         stroke-width="0.9" opacity="0.55"/>` : "";
  return `<svg class="pn-range" viewBox="0 0 100 12" preserveAspectRatio="none" role="img"
    aria-label="position in its own historical range">
    <rect x="${at(low)}" y="4.5" width="${(at(high) - at(low)).toFixed(2)}" height="3"
      fill="currentColor" opacity="0.16"/>
    ${med}<circle cx="${at(current)}" cy="6" r="3" fill="var(--pn-hot)"/></svg>`;
}

function bars(items) {
  const nums = items.filter((i) => typeof i[1] === "number" && isFinite(i[1]));
  if (!nums.length) return "";
  // ONE SHARED SCALE. Three bars each normalised to themselves would make a 0.4pp excess look like
  // a 29pp one.
  const scale = Math.max(...nums.map((i) => Math.abs(i[1]))) || 1;
  return `<div class="pn-bars">${items.map(([label, v]) => {
    if (typeof v !== "number" || !isFinite(v)) {
      return `<div class="pn-bar"><span class="pn-bl">${escapeHtml(label)}</span>
        <span class="pn-bt"></span><span class="pn-bv">${DASH}</span></div>`;
    }
    const w = Math.abs(v) / scale * 50;
    const left = v >= 0 ? 50 : 50 - w;
    return `<div class="pn-bar"><span class="pn-bl">${escapeHtml(label)}</span>
      <span class="pn-bt"><i class="pn-bf ${v >= 0 ? "pos" : "neg"}"
        style="left:${left.toFixed(2)}%;width:${w.toFixed(2)}%"></i></span>
      <span class="pn-bv">${pp(v)}</span></div>`;
  }).join("")}</div>`;
}

function timeline({ last_evidence_date, newer_filings, next_expected_print }) {
  const li = [];
  if (last_evidence_date) {
    li.push(`<li class="read"><b>${escapeHtml(fmtDate(last_evidence_date))}</b>
      <span>last read</span></li>`);
  }
  for (const n of (newer_filings || []).slice(0, 4)) {
    li.push(`<li class="unread"><b>${escapeHtml(String(n).split(" acc ")[0])}</b>
      <span>filed since</span></li>`);
  }
  if (next_expected_print) {
    li.push(`<li class="next"><b>${escapeHtml(fmtDate(next_expected_print))}</b>
      <span>next (est)</span></li>`);
  }
  return li.length ? `<ol class="pn-time">${li.join("")}</ol>` : "";
}

// --- per-panel bodies -----------------------------------------------------------------------
// Each returns main-body HTML from the structured value. A body that cannot be built returns "" and
// the tile says so rather than printing an empty frame.

const BODY = {
  the_call(v) {
    const sub = [v.sleeve, v.entry_date ? `entered ${fmtDate(v.entry_date)} at ${fmtPrice(v.entry_price)}` : null]
      .filter(Boolean).join(" · ");
    // verdictWord, not the raw field: the decision log and the dossier both shorten AVOID_TERMINAL
    // to AVOID, and a third view printing the enum would be the same verdict spelled three ways.
    return `<p class="pn-big">${escapeHtml(verdictWord(v.verdict) || DASH)}<small>${escapeHtml(sub)}</small></p>
      <p class="pn-sub">now ${fmtPrice(v.current_price)} · ${v.closed ? "CLOSED" : "held"}${
      v.horizon_date ? ` · horizon ${escapeHtml(fmtDate(v.horizon_date))}` : ""}</p>`;
  },
  attribution(v) {
    return bars([["position", v.position_return],
      [`benchmark ${v.benchmark || ""}`.trim(), v.benchmark_return], ["excess", v.excess]])
      + (v.days_elapsed != null
        ? `<p class="pn-sub">${fmtInt(v.days_elapsed)} of ${fmtInt(v.horizon_days)} days</p>` : "");
  },
  multiple_and_price(v) {
    return `<p class="pn-big">${x(v.current)}<small>${escapeHtml(String(v.metric || ""))} · ${
      pctc(v.percentile)}ile of its historical range</small></p>`
      + rangeBar(v)
      // THE MARK'S OWN AS-OF LEADS THE LINE, and it is NOT the monitor day. The dossier's multiple
      // is stamped when the valuation panel was pulled: VRRM's reads 2026-03-31 and LLY's 2026-08-20
      // in the same 2026-08-11 snapshot. Calling the appended point "today's mark" under the page's
      // "As of <monitor day>" header asserted a vintage the payload contradicts — and this repo's
      // rule is that a vintage mark LEADS the numbers it governs, read after them it does not work.
      + `<p class="pn-sub">as of ${escapeHtml(fmtDate(v.as_of))} · range ${x(v.low)}–${x(v.high)} · median ${
        x(v.median)} · ${fmtInt(v.n_closes)} closes${v.range_excludes_current
        ? `, excluding the current mark (${escapeHtml(fmtDate(v.as_of))})` : ""}</p>`
      + sparkline(v.series, { current: v.current, nClose: v.n_closes,
        excludesCurrent: v.range_excludes_current });
  },
  filing_watch(v) {
    return timeline(v) + (v.unread_print
      ? `<p class="pn-flag">UNREAD PRINT — the call is being made on evidence older than the
         latest filing</p>` : "");
  },
  kills(v) {
    const cs = v.criteria || [];
    if (!cs.length) return "";
    // A READING SITS BESIDE ITS CRITERION AND NOTHING SAYS "FIRED". The machine surfaces; the human
    // concludes — there is no state in this renderer that could adjudicate, by construction.
    return `<ul class="pn-kills">${cs.map((c) => {
      const reading = typeof c.reading === "number" && isFinite(c.reading)
        ? `<span class="pn-read">${escapeHtml(String(c.metric || "reading"))} ${c.reading}${
          c.threshold != null ? ` vs ${c.threshold}` : ""}${
          c.unit_checked ? "" : ` <b class="pn-warn">⚠ UNIT UNCHECKED</b>`}</span>`
        : `<span class="pn-noread">no measured metric — re-printed only</span>`;
      return `<li>${escapeHtml(String(c.text))}${reading}</li>`;
    }).join("")}</ul>`;
  },
  dilution(v) {
    const f = v.forms || [];
    const mx = Math.max(1, ...f.map((i) => i[1]));
    return `<div class="pn-bars">${f.slice(0, 5).map(([k, n]) =>
      `<div class="pn-bar"><span class="pn-bl">${escapeHtml(k)}</span>
        <span class="pn-bt"><i class="pn-bf pos" style="left:0;width:${(n / mx * 100).toFixed(0)}%"></i></span>
        <span class="pn-bv">${fmtInt(n)}</span></div>`).join("")}</div>`
      + (v.line ? `<p class="pn-sub">${escapeHtml(String(v.line))}</p>` : "");
  },
  sources(v) {
    const refs = v.refs || [];
    return `<p class="pn-big">${fmtInt(refs.length)}<small>primary filings behind the numbers
      above</small></p>` + refs.slice(0, 5).map((r) =>
      `<p class="pn-mono">${escapeHtml(String(r))}</p>`).join("");
  },
  cost_of_borrowing(v) {
    // COVERAGE IS NEVER OPTIONAL BESIDE A RATE. AORT's fixed average is struck over one $0.9M bond
    // in a $220.9M stack; printing 6.05% alone repeats the lease defect one level down.
    const rows = [[`fixed · ${pctc(v.fixed_coverage)} of stack`, v.fixed_pct],
      [`all-in · ${pctc(v.all_in_coverage)} of stack`, v.all_in_pct]];
    return `<p class="pn-big">${rate(v.fixed_pct)}<small>weighted-average FIXED coupon, over ${
      pctc(v.fixed_coverage)} of principal</small></p>`
      + `<table class="pn-tbl"><tbody>${rows.map(([l, r]) =>
        `<tr><th>${escapeHtml(l)}</th><td>${rate(r)}</td></tr>`).join("")}
        <tr><th>floating share</th><td>${pctc(v.floating_share)}</td></tr>
        <tr><th>lease liabilities held out</th><td>${fmtInt(v.lease_musd)}m</td></tr>
        </tbody></table>`;
  },
};

// --- tiles ----------------------------------------------------------------------------------

// A row renders as a refusal when it SAYS it is one, or when its body could not be built — and the
// two must be indistinguishable on the page, because an empty ready tile is indistinguishable from a
// panel that does not apply. The upstream demotion (`panels_emit._row`) only fires on a FALSY
// payload, and several payloads are never falsy (`kills` is always `{criteria: [...]}`, empty or
// not), so the renderer is the layer that has to settle it. Exported as one predicate so the tile's
// border, its badge and the header's ready/refused COUNT cannot disagree about the same row.
function renderedBody(row) {
  if (row.state === "refused") return "";
  const f = BODY[row.key];
  return f ? f(row.value || {}) : "";
}

export function rendersAsRefusal(row) {
  return row.state === "refused" || !renderedBody(row);
}

function tile(row) {
  let body = renderedBody(row);
  const isRefused = rendersAsRefusal(row);
  if (isRefused) {
    // A REFUSAL IS A TILE — bordered, badged, and carrying its reason in full. And a READY row whose
    // body could not be built is shown the same way rather than as an empty frame: an empty tile is
    // indistinguishable from a panel that does not apply, which is the one thing the rule forbids.
    const req = (row.missing || []).map((m) =>
      `<li><code>${escapeHtml(m.kind)}</code> ${escapeHtml(m.detail)}
        <span>${escapeHtml(m.why)}</span></li>`).join("");
    // A REFUSAL STILL SHOWS WHAT IT DOES HAVE. `kills` refuses on every name in the corpus because
    // no record carries a measured criterion — but the criteria PROSE exists, and hiding it behind
    // the refusal would leave the reader with less than the terminal view already gives them. The
    // badge says the NUMBERS are missing; the list says what the numbers would have been about.
    const partial = row.key === "kills" && (row.value?.criteria || []).length
      ? `<ul class="pn-kills pn-partial">${row.value.criteria.map((c) =>
          `<li>${escapeHtml(String(c.text))}</li>`).join("")}</ul>` : "";
    // A REFUSAL WITH NO REASON IS THE BLANK TILE THIS BLOCK EXISTS TO PREVENT, so a row the
    // RENDERER demoted (the artifact called it ready and carried a payload nothing could be drawn
    // from) states that as its cause rather than leaving the tile to explain nothing.
    const why = row.reason || (row.state === "refused" ? "" : `the artifact marks this panel READY \
but its committed value carries nothing this surface can draw — the requirement check and the \
payload disagree, which is a wiring bug rather than missing disclosure`);
    body = `<p class="pn-why">This panel applies to this name and <b>cannot be computed</b>.</p>
      ${req ? `<ul class="pn-missing">${req}</ul>` : ""}
      ${why ? `<p class="pn-up">${escapeHtml(why)}</p>` : ""}
      ${partial ? `<p class="pn-partial-head">The criteria themselves, unmeasured:</p>${partial}` : ""}`;
  }
  const srcs = (row.sources || []).filter(Boolean);
  return `<section class="pn-panel ${isRefused ? "refused" : "ready"}">
    <h3>${escapeHtml(row.title)}<span class="pn-badge">${isRefused ? "REFUSED" : ""}</span></h3>
    <div class="pn-body">${body}</div>
    ${!isRefused && row.caveat ? `<p class="pn-caveat">${escapeHtml(row.caveat)}</p>` : ""}
    <p class="pn-changes"><span>What would change the call</span>${escapeHtml(row.changes_the_call)}</p>
    ${srcs.length ? `<details class="pn-prov"><summary>Sources</summary><ol>${
      srcs.map((s) => `<li>${escapeHtml(String(s))}</li>`).join("")}</ol></details>` : ""}
  </section>`;
}

export function panelGridHtml(rows, { ticker } = {}) {
  const mine = (rows || []).filter((r) => !ticker
    || String(r.ticker).toUpperCase() === String(ticker).toUpperCase());
  if (!mine.length) return "";
  const byTier = { universal: [], cohort: [], theme: [], name: [] };
  for (const r of mine) (byTier[r.tier] || byTier.name).push(r);
  const groups = Object.entries(byTier).filter(([, v]) => v.length).map(([t, v]) =>
    `<h4 class="pn-tier">${escapeHtml(t)}</h4><div class="pn-grid">${
      v.map(tile).join("")}</div>`).join("");
  // COUNTED BY THE SAME PREDICATE THE TILE USES. Counting `state === "refused"` while the tile drew
  // a refusal for an unbuildable body let the header say "1 ready · 0 refused" over a tile reading
  // "cannot be computed" — the header would have been the reassuring half of an absent-vs-broken
  // mismatch, which is the defect the whole block exists to prevent.
  const nRef = mine.filter(rendersAsRefusal).length;
  return `<div class="pn-wrap" data-ticker="${escapeHtml(String(ticker || ""))}">
    <p class="pn-note"><b>${fmtInt(mine.length - nRef)} ready · ${fmtInt(nRef)} refused.</b>
      A panel that does not apply to this name is not here at all — it emits no tile. A panel that
      applies and cannot be computed is marked REFUSED and names the requirement that failed.</p>
    ${groups}</div>`;
}

export async function render(root, params, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading monitor…</div>` });
  const mon = await getMonitor();
  if (!mon) {
    root.innerHTML = frame(item, { bodyHtml:
      `<div class="notice">No monitor snapshot committed yet — run
       <span class="mono">python -m vinci monitor</span>.</div>` });
    return;
  }
  const rows = mon.panels || [];
  if (!rows.length) {
    // ABSENT IS NOT BROKEN, at the block level too: a snapshot predating the panel grid carries no
    // `panels` key, and that is different from a run whose grid failed (which appends a note).
    const failed = (mon.notes || []).filter((n) => String(n).startsWith("PANEL GRID UNAVAILABLE"));
    root.innerHTML = frame(item, { bodyHtml: failed.length
      ? `<div class="notice">The panel grid did not build on this run — ${
        escapeHtml(failed.join("; "))}</div>`
      : `<div class="notice">This snapshot (${escapeHtml(fmtDate(mon.as_of))}) predates the panel
         grid. Re-run <span class="mono">python -m vinci monitor</span> to emit it.</div>` });
    return;
  }
  const tickers = [...new Set(rows.map((r) => String(r.ticker)))].sort();
  // `params` is the ARRAY of path segments after the route (see app.js `parseHash`), matching
  // `dossier.js`. An earlier cut read `params.ticker`, which is always undefined here and would
  // have pinned every deep link to the first ticker without erroring.
  const asked = ((params && params[0]) || "").trim().toUpperCase();
  const want = tickers.includes(asked) ? asked : tickers[0];
  const tabs = tickers.map((t) => `<a class="pn-tab ${t === want ? "on" : ""}"
    href="#/monitor-panels/${encodeURIComponent(t)}">${escapeHtml(t)}</a>`).join("");
  root.innerHTML = frame(item, { bodyHtml:
    `<p class="subtitle muted">As of ${escapeHtml(fmtDate(mon.as_of))} — every figure a dated,
      committed number. The browser never fetches a live price.</p>
     <div class="pn-tabs">${tabs}</div>${panelGridHtml(rows, { ticker: want })}` });
}
