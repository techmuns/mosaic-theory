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
// A NONZERO SHARE NEVER PRINTS AS "0%". AORT's fixed average is struck over 0.4% of its stack and
// rounded to "over 0% of principal" — a rate presented over apparently nothing, which reads as a
// bug rather than as the warning it is. The floor is a display fix, not the coverage THRESHOLD
// still open for a ruling; it makes the small number visible rather than deciding what to do about
// it.
const pctc = (v, d = 0) => {
  if (typeof v !== "number" || !isFinite(v)) return DASH;
  const pct = v * 100;
  // WORDS, NOT A BARE "<". These strings are interpolated straight into HTML, so "<1%" is read as
  // the start of a tag and the browser swallows it — the label vanished entirely on AORT and the
  // tile read "over  of principal". Caught only because the rendered text was checked, not the
  // formatter.
  if (pct > 0 && pct < 1) return "under 1%";
  if (pct < 0 && pct > -1) return "under 1% (negative)";
  return pct.toFixed(d) + "%";
};
const rate = (v, d = 2) => (typeof v === "number" && isFinite(v) ? v.toFixed(d) + "%" : DASH);

// A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION (CLAUDE.md, 2026-09-10). These three caps were
// ported from vinci/panels_render.py, which #601 fixed and this branch then RENAMED — so the fix
// landed on a file that no longer exists here while the identical `[:N]` lived on in the renderer
// that replaced it. A sample knows it is a sample; a truncated print does not, and a correct count
// beside a partial body is what makes it convincing.
const TIMELINE_DOTS = 4;   // "filed since" dots before the overflow dot
const FORM_BARS = 5;       // form-mix bars before the summary line
const SOURCE_REFS = 5;     // primary filings listed before the summary line

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
  const newer = newer_filings || [];
  for (const n of newer.slice(0, TIMELINE_DOTS)) {
    li.push(`<li class="unread"><b>${escapeHtml(String(n).split(" acc ")[0])}</b>
      <span>filed since</span></li>`);
  }
  // Without this, a nine-filing gap renders identically to a four-filing one — in the panel that
  // exists to show the size of the gap. The overflow dot carries the remainder so the drawn
  // distance cannot understate the real one.
  if (newer.length > TIMELINE_DOTS) {
    li.push(`<li class="unread"><b>+${fmtInt(newer.length - TIMELINE_DOTS)} more</b>
      <span>of ${fmtInt(newer.length)} filed since</span></li>`);
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
  multiple_and_price(v, row) {
    // THE COMPARISON LEADS. A bare "25.8x" answers nothing; "25.8x vs 17.4x median" is a reading.
    const med = (typeof v.median === "number" && isFinite(v.median))
      ? `<b>${x(v.current)}</b> vs ${x(v.median)} median` : `<b>${x(v.current)}</b>`;
    return `<p class="pn-big">${med}${staleBadge(row, v.as_of)}<small>${
      escapeHtml(String(v.metric || ""))} · ${pctc(v.percentile)}ile of its own range · as of ${
      escapeHtml(fmtDate(v.as_of))}</small></p>`
      + rangeBar(v)
      // THE MARK'S OWN AS-OF LEADS THE LINE, and it is NOT the monitor day. The dossier's multiple
      // is stamped when the valuation panel was pulled: VRRM's reads 2026-03-31 and LLY's 2026-08-20
      // in the same 2026-08-11 snapshot. Calling the appended point "today's mark" under the page's
      // "As of <monitor day>" header asserted a vintage the payload contradicts — and this repo's
      // rule is that a vintage mark LEADS the numbers it governs, read after them it does not work.
      // The as-of and the median BOTH moved up into the headline, so this line stops repeating
      // them. It printed the date twice in one sentence and the median twice on one tile.
      + `<p class="pn-sub">range ${x(v.low)}–${x(v.high)} over ${fmtInt(v.n_closes)} closes${
        v.range_excludes_current ? ", which exclude the mark above" : ""}</p>`
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
    // FORM CODES ARE NOT ENGLISH. "424B5" tells a reader nothing; "drawdown from a shelf" does.
    // Grouping by MEANING also stops the chart ranking 424B5 against 424B2, a distinction that
    // carries no decision content — both are draws on the same shelf.
    const MEANS = {
      "S-3ASR": "shelf registered", "S-3": "shelf registered", "F-3": "shelf registered",
      "424B2": "drawn from shelf", "424B5": "drawn from shelf", "424B3": "drawn from shelf",
      "S-8": "employee plans", "S-1": "new registration", "F-1": "new registration",
      "S-4": "merger shares",
    };
    // AMENDMENTS AND POST-EFFECTIVE VARIANTS ARE THE SAME FILING. The corpus carries "S-3/A",
    // "S-8 POS" and "S-4/A", which a first cut passed through untranslated — so the tile still
    // showed three codes as jargon beside the plain-English groups. The base form is what carries
    // the meaning; the suffix says it is a revision of one.
    const base = (code) => String(code).replace(/\s*(POS|POSASR)$/i, "").replace(/\/A$/i, "").trim();
    const grouped = {};
    for (const [code, n] of (v.forms || [])) {
      const k = MEANS[base(code)] || base(code);
      grouped[k] = (grouped[k] || 0) + n;
    }
    v = { ...v, forms: Object.entries(grouped).sort((a, b) => b[1] - a[1]) };
    const f = v.forms || [];
    const top = f.slice(0, FORM_BARS);
    const mx = Math.max(1, ...top.map((i) => i[1]));
    // One committed dossier carries 8 form types against 5 bars; without the summary the chart
    // reads as the whole mix.
    const drawn = top.reduce((a, i) => a + i[1], 0);
    const total = f.reduce((a, i) => a + i[1], 0);
    const more = f.length > top.length
      ? `<p class="pn-sub">showing ${fmtInt(top.length)} of ${fmtInt(f.length)} form types
         (${fmtInt(drawn)} of ${fmtInt(total)} filings)</p>` : "";
    return `<div class="pn-bars">${top.map(([k, n]) =>
      `<div class="pn-bar"><span class="pn-bl">${escapeHtml(k)}</span>
        <span class="pn-bt"><i class="pn-bf pos" style="left:0;width:${(n / mx * 100).toFixed(0)}%"></i></span>
        <span class="pn-bv">${fmtInt(n)}</span></div>`).join("")}</div>${more}`
      + (v.line ? `<p class="pn-sub">${escapeHtml(String(v.line))}</p>` : "");
  },
  sources(v) {
    const refs = v.refs || [];
    const shown = refs.slice(0, SOURCE_REFS);
    // The count in the headline is CORRECT and the body is PARTIAL — exactly the pair the rule
    // names as what makes a truncation convincing. This is the tile a reader opens to CHECK rather
    // than trust, so an unstated remainder here is the worst-placed instance of the three.
    const more = refs.length > shown.length
      ? `<p class="pn-sub">showing ${fmtInt(shown.length)} of ${fmtInt(refs.length)} —
         the full list is in the day's monitor JSON</p>` : "";
    return `<p class="pn-big">${fmtInt(refs.length)}<small>primary filings behind the numbers
      above</small></p>` + shown.map((r) =>
      `<p class="pn-mono">${escapeHtml(String(r))}</p>`).join("") + more;
  },
  theme_thesis(v) {
    const ts = v.triggers || [];
    if (!ts.length) return "";
    // THE BASIS RENDERS BESIDE THE TRIGGER, because a criterion nobody can check is not a
    // criterion — and a basis naming a source OUTSIDE this repo is marked as such rather than
    // sharing the look of one checkable against filing cadence. An unchecked claim must not borrow
    // the credibility of a checked one.
    return `<ul class="pn-theme">${ts.map((t) => {
      const days = typeof t.days_remaining === "number"
        ? (t.days_remaining < 0 ? `${fmtInt(-t.days_remaining)}d past`
          : `${fmtInt(t.days_remaining)}d left`) : DASH;
      const kind = t.basis_kind === "timing" ? "checkable"
        : t.basis_kind === "external" ? "outside this repo" : "no basis stated";
      return `<li class="${t.deadline_passed ? "passed" : ""}">
        <span class="pn-tk">${escapeHtml(String(t.kind || ""))}</span>
        ${escapeHtml(String(t.trigger || ""))}
        <span class="pn-tmeta">${escapeHtml(fmtDate(t.deadline))} · ${days}${
        t.deadline_passed ? " · WINDOW CLOSED" : ""}</span>
        <span class="pn-tbasis ${t.basis_kind}">basis (${kind}): ${
        escapeHtml(String(t.basis || "—"))}</span></li>`;
    }).join("")}</ul>`;
  },
  cost_of_borrowing(v) {
    // COVERAGE IS NEVER OPTIONAL BESIDE A RATE. AORT's fixed average is struck over one $0.9M bond
    // in a $220.9M stack; printing 6.05% alone repeats the lease defect one level down.
    // THE ALL-IN ROW EARNS ITS PLACE ONLY WHEN IT DIFFERS. With no floating debt the two bases
    // are identical, and printing "4.16%" three times on one tile (headline + two rows) reads as
    // three findings. AORT's 5.63% fixed against 7.81% all-in is the case worth the row.
    const differs = typeof v.all_in_pct === "number" && typeof v.fixed_pct === "number"
      && Math.abs(v.all_in_pct - v.fixed_pct) >= 0.01;
    // Coverage is already in the headline; repeating it as a table row was the same duplication
    // the all-in row had. The table now carries only what the headline does NOT say.
    const rows = [];
    if (differs) {
      rows.push([`all-in (incl. floating at today's rate)`, v.all_in_pct]);
    }
    return `<p class="pn-big">${rate(v.fixed_pct)}<small>weighted-average FIXED coupon, covering ${
      pctc(v.fixed_coverage)} of principal</small></p>`
      + `<table class="pn-tbl"><tbody>${rows.map(([l, r]) =>
        `<tr><th>${escapeHtml(l)}</th><td>${r === null ? "" : rate(r)}</td></tr>`).join("")}
        ${v.floating_share ? `<tr><th>floating</th><td>${pctc(v.floating_share)}</td></tr>` : ""}
        ${v.lease_musd ? `<tr><th>leases held out</th><td>$${fmtInt(v.lease_musd)}m</td></tr>` : ""}
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
  // The ROW travels with the value: a body needs the page's as-of and the panel's cadence to age
  // its own figure, and reaching for them any other way would be a second lookup that can disagree.
  return f ? f(row.value || {}, row) : "";
}

export function rendersAsRefusal(row) {
  return row.state === "refused" || !renderedBody(row);
}

//: The per-name half of "what would change the call". SILENT WHEN UNDECLARED, and that is the
//: point: the panel text was rewritten to claim no axis precisely so a name that has not named one
//: gets a distance and no story about what it costs. Inventing a default here would put one
//: position's archetype back on every name, which is the defect this field exists to close.
const AXIS = {
  // Phrased against what the tile now SHOWS. The earlier wording said "closing this distance",
  // which referred to a distance the retitled panel no longer claims to display.
  multiple: "This name rests on the MULTIPLE — the multiple moving back toward its range is the "
    + "call breaking.",
  earnings: "This name rests on EARNINGS ARRIVAL — the multiple can travel a long way here "
    + "without the thesis moving.",
};

function axisLine(row) {
  const a = (row.render_config || {}).load_bearing_axis;
  if (!a) return "";
  // An unrecognised value is SHOWN, not swallowed: the declare-time check already refuses one, so
  // seeing it here means the artifact predates that check — and a silent drop would hide it.
  const said = AXIS[a] || `Declared load-bearing axis: ${escapeHtml(String(a))} (unrecognised).`;
  return `<span class="pn-axis">${AXIS[a] ? escapeHtml(said) : said}</span>`;
}

//: Days after which a figure's own as-of is worth flagging on the tile. Quarterly data is normally
//: a quarter old, so a bare date is not news — a figure OLDER than its own cadence is.
const STALE_AFTER = {event: 120, quarterly: 120, monthly: 45, weekly: 14, daily: 5};

function staleBadge(row, asOf) {
  if (!asOf || !row.as_of_page) return "";
  const age = Math.round((new Date(row.as_of_page) - new Date(asOf)) / 86400000);
  const limit = STALE_AFTER[row.cadence] ?? 120;
  if (!isFinite(age) || age <= limit) return "";
  return `<span class="pn-stale" title="this figure is older than the page">${fmtInt(age)}d old</span>`;
}

function tile(row) {
  let body = renderedBody(row);
  const isRefused = rendersAsRefusal(row);
  if (isRefused) {
    // A REFUSAL IS A TILE — bordered, badged, and carrying its reason in full. And a READY row whose
    // body could not be built is shown the same way rather than as an empty frame: an empty tile is
    // indistinguishable from a panel that does not apply, which is the one thing the rule forbids.
    // THE `why` IS NOT REPEATED HERE. `reason` is composed upstream as "<kind> <detail> — <why>.
    // <upstream>", so printing `m.why` in this list too rendered the same sentence twice in every
    // refused tile, one paragraph apart — which reads as two different findings on a first pass.
    // The list names WHAT is missing; the block below says why and carries the extractor's words.
    // ...and the `why` is dropped from this list ONLY when `reason` already carries it. `decide()`
    // composes reason as "<kind> <detail> — <why>. <upstream>" on the normal path, but its
    // MISSING-CONFIG branch builds its own sentence from `config_schema` and never mentions `why` —
    // so an unconditional drop would lose the explanation entirely on exactly the refusal a name
    // hits when it has been half-onboarded. Latent today (0 of 124 committed rows take that
    // branch) and cheap to keep correct.
    const req = (row.missing || []).map((m) => {
      const dup = m.why && String(row.reason || "").includes(m.why);
      return `<li><code>${escapeHtml(m.kind)}</code> ${escapeHtml(m.detail)}${
        dup ? "" : `<span>${escapeHtml(m.why || "")}</span>`}</li>`;
    }).join("");
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
    // SUBJECT-AWARE. The h3 was taught that a theme tile is about a DRIVER and this sentence was
    // not, so all six committed theme tiles read "applies to this name" under a driver heading.
    const subject = row.tier === "theme" ? "this driver" : "this name";
    body = `<p class="pn-why">This panel applies to ${subject} and <b>cannot be computed</b>.</p>
      ${req ? `<ul class="pn-missing">${req}</ul>` : ""}
      ${why ? `<p class="pn-up">${escapeHtml(why)}</p>` : ""}
      ${partial ? `<p class="pn-partial-head">The criteria themselves, unmeasured:</p>${partial}` : ""}`;
  }
  const srcs = (row.sources || []).filter(Boolean);
  return `<section class="pn-panel ${isRefused ? "refused" : "ready"}">
    <h3>${escapeHtml(row.tier === "theme" ? `${row.ticker} — ${row.title}` : row.title)}<span
      class="pn-badge">${isRefused ? "REFUSED" : ""}</span></h3>
    <div class="pn-body">${body}</div>
    ${!isRefused && row.caveat ? `<p class="pn-caveat">${escapeHtml(row.caveat)}</p>` : ""}
    <p class="pn-changes"><span>What would change the call</span>${escapeHtml(row.changes_the_call)}${
      axisLine(row)}</p>
    ${srcs.length ? `<details class="pn-prov"><summary>Sources</summary><ol>${
      srcs.map((s) => `<li>${escapeHtml(String(s))}</li>`).join("")}</ol></details>` : ""}
  </section>`;
}

export function tabTickers(rows) {
  // THE TAB STRIP IS A NAME STRIP. Theme rows carry a DRIVER KEY in `ticker` (the tier attaches to
  // the driver, not the name), so deriving tabs from every row appended six driver tabs that could
  // not be selected: clicking one set the asked-for value to something absent from this list, the
  // view fell back to the first ticker, and NO tab highlighted. A control that looks live and does
  // nothing is worse than an absent one — the reader concludes the data is empty, not the link dead.
  //
  // EXPORTED because it was the one part of this fix a test could not reach: tabs are built inside
  // `render()`, which needs the DOM, so the first pin passed against the un-fixed code.
  return [...new Set((rows || []).filter((r) => r.tier !== "theme")
    .map((r) => String(r.ticker)))].sort();
}

export function panelGridHtml(rows, { ticker, asOf } = {}) {
  // A THEME ROW'S `ticker` IS A DRIVER KEY — the tier attaches to the driver, not the name. The
  // ticker filter must therefore let theme rows through, or the whole tier disappears from every
  // page while looking exactly like a tier that emitted nothing.
  const mine = (rows || []).filter((r) => r.tier === "theme" || !ticker
    || String(r.ticker).toUpperCase() === String(ticker).toUpperCase());
  if (!mine.length) return "";
  const byTier = { universal: [], cohort: [], theme: [], name: [] };
  // The PAGE's as-of, carried onto each row so a body can age its own figure against it. Without
  // it a tile cannot know that its number is older than the day it is being read on.
  for (const r of mine) (byTier[r.tier] || byTier.name).push(asOf ? { ...r, as_of_page: asOf } : r);
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
  const tickers = tabTickers(rows);
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
     <div class="pn-tabs">${tabs}</div>${panelGridHtml(rows, { ticker: want, asOf: mon.as_of })}` });
}
