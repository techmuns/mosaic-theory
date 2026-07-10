// DOSSIER VIEWER — render the structured dossier.json into styled, source-bound sections.
// Assembles facts · NO verdict. Every fact shows its [n] citation (source-binding is the signature).
// The synthesis is fenced as "the framing, not the answer." Read-only; verdicts are CLI-logged.
import { getDossier, getDossierIndex, getLedger, isBuyVerdict } from "../../lib/snapshots.js";
import { fmtPrice, fmtDate, fmtStamp, fmtPct, escapeHtml, DASH } from "../../lib/format.js";
import { barDomain, lineDomain, linScale, logScale, barLabelY, EXHIBIT } from "../../lib/exhibit.js";

// PDF export uses the browser's native print-to-PDF (no library — the frontend stays dependency-free).
// The browser derives the saved-file name from document.title, so on a dossier print we swap in a
// meaningful name ("VRRM · dossier · Nostra Vinci") and restore it afterward. Wiring it to the
// beforeprint/afterprint events (not the button) means a native Cmd+P gets the same filename. This
// runs once: the module is import-cached, so the listeners are registered a single time.
let _titleBeforePrint = null;
window.addEventListener("beforeprint", () => {
  const m = (location.hash || "").match(/#\/dossier\/([^/?#]+)/);
  if (!m) return; // only rename for a single-ticker dossier print; leave every other page alone
  let ticker;
  try { ticker = decodeURIComponent(m[1]); } catch { ticker = m[1]; } // tolerate a malformed-escape hash
  _titleBeforePrint = document.title;
  document.title = `${ticker.toUpperCase()} · dossier · Nostra Vinci`;
});
window.addEventListener("afterprint", () => {
  if (_titleBeforePrint != null) { document.title = _titleBeforePrint; _titleBeforePrint = null; }
  // Clear any menu-chosen PDF scope so a later native Cmd+P falls back to the on-screen tier — the
  // print CSS relies on ds-print-* being ABSENT for that fallback, and nothing else clears it.
  document.body.classList.remove("ds-print-full", "ds-print-brief");
});

// One document-level listener, registered ONCE (the module is import-cached), closes an open PDF
// scope-menu on any outside click. Registering it per-render (inside render()) would leak a stale
// listener on every dossier navigation, each closing over a now-detached menu. The toggle button
// calls stopPropagation, so this never fires on the button itself.
document.addEventListener("click", () => {
  const menu = document.querySelector("#ds-pdf-menu");
  if (menu && !menu.hidden) {
    menu.hidden = true;
    const btn = document.querySelector("#ds-pdf");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }
});

export async function render(root, params, { item, frame }) {
  const ticker = (params[0] || "").trim().toUpperCase();
  if (!ticker) return renderIndex(root, item, frame);

  const crumb = ` <span class="sep">/</span> <span class="mono">${escapeHtml(ticker)}</span>`;
  // bare: the detail page's own ticker header replaces the generic "Dossier" header block (no duplication)
  root.innerHTML = frame(item, { crumbExtra: crumb, bare: true, bodyHtml: `<div class="notice">Loading dossier…</div>` });

  const [d, led] = await Promise.all([getDossier(ticker), getLedger()]);
  if (!d) {
    root.innerHTML = frame(item, { crumbExtra: crumb, bare: true, bodyHtml: `
      <div class="notice">No dossier assembled for <b>${escapeHtml(ticker)}</b> in this deploy.
      Assemble it via <span class="mono">python -m vinci dossier --ticker ${escapeHtml(ticker)}</span> (then commit the derived
      <span class="mono">dossier.json</span> to the private repo).</div>` });
    return;
  }
  const verdict = led.entries.find((e) => e.ticker === ticker) || null;
  root.innerHTML = frame(item, { crumbExtra: crumb, bare: true, bodyHtml: renderDossier(d, verdict) });
  // (3-tier) client-side tabs — default Brief; toggle the active panel, no re-fetch, no router change.
  root.querySelectorAll(".ds-tab").forEach((tab) => tab.addEventListener("click", () => {
    const tier = tab.dataset.tier;
    root.querySelectorAll(".ds-tab").forEach((t) => t.classList.toggle("on", t === tab));
    root.querySelectorAll(".ds-tier").forEach((p) => p.classList.toggle("on", p.dataset.tier === tier));
    window.scrollTo(0, 0);
  }));
  // Export to PDF — a scope dropdown (Brief first-cut, or the full dossier). The print stylesheet
  // (@media print) strips the app chrome and shows the chosen tiers. Read-only: it prints what is
  // assembled, renders no new judgment.
  const pdfBtn = root.querySelector("#ds-pdf");
  const pdfMenu = root.querySelector("#ds-pdf-menu");
  if (pdfBtn && pdfMenu) {
    pdfBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      pdfMenu.hidden = !pdfMenu.hidden;
      pdfBtn.setAttribute("aria-expanded", String(!pdfMenu.hidden));
    });
    // (outside-click closes the menu via the once-registered module-scoped document listener near
    // the top of this file — NOT re-added here per-render, which leaked one stale listener per
    // dossier navigation, each closing over a now-detached menu.)
    pdfMenu.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      pdfMenu.hidden = true;
      const full = b.dataset.scope === "full";
      document.body.classList.toggle("ds-print-full", full);
      document.body.classList.toggle("ds-print-brief", !full);
      window.print();
    }));
  }
}

// --- dossier index (no ticker) ----------------------------------------------
async function renderIndex(root, item, frame) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading dossiers…</div>` });
  const tickers = await getDossierIndex();
  const search = `
    <form id="ds-search" style="display:flex; gap:10px; margin:4px 0 18px;">
      <input id="ds-q" type="search" placeholder="Jump to a ticker's dossier (e.g. VRRM)…" autocomplete="off"
        style="flex:1; max-width:380px; padding:9px 12px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
      <button type="submit" style="padding:9px 18px; border:1px solid var(--line-2); border-radius:8px; background:var(--surface); cursor:pointer; font-size:13px;">Open</button>
    </form>`;
  const body = tickers.length
    ? `<div class="grid cols-3">${tickers.map((t) => `
        <a class="ds-index-card" href="#/dossier/${escapeHtml(t)}">
          <div class="mono" style="font-size:16px; font-weight:650;">${escapeHtml(t)}</div>
          <div class="muted" style="font-size:12px; margin-top:4px;">assembled facts · no verdict →</div>
        </a>`).join("")}</div>`
    : `<div class="notice">No dossiers committed to this deploy yet. Assemble with <span class="mono">python -m vinci dossier</span>, then commit the derived <span class="mono">dossier.json</span> to the private repo.</div>`;
  root.innerHTML = frame(item, {
    bodyHtml: `${assembleHelp()}<div class="subtitle" style="margin-bottom:10px;">Search any ticker, open a finalist from the <a href="#/ranker">ranker</a>, or pick a committed one below.</div>${search}${body}`,
  });
  // client-side navigation only (no write path) — jump to any ticker's dossier
  root.querySelector("#ds-search").addEventListener("submit", (e) => {
    e.preventDefault();
    const t = root.querySelector("#ds-q").value.trim().toUpperCase();
    if (t) location.hash = `#/dossier/${encodeURIComponent(t)}`;
  });
}

// "How to assemble a dossier" — COPYABLE TEXT in the same compact, collapsible style as the
// Ingestion page's refresh block (never a button). The dashboard is read-only and runs nothing.
function assembleHelp() {
  return `
    <details class="card" style="margin-bottom:18px; background:var(--surface-2);">
      <summary style="cursor:pointer; font-size:12.5px; font-weight:600; color:var(--ink-2);">How to assemble a dossier <span class="muted" style="font-weight:400;">(read-only — copy &amp; run locally, then rebuild)</span></summary>
      <div class="subtitle muted" style="margin:10px 0 8px;">Replace <span class="mono">&lt;TICKER&gt;</span> with the name. Pull the licensed CIQ first, assemble, then rebuild the mirror — the dashboard runs nothing.</div>
      <pre style="background:var(--nav-bg); color:#c3cad6; padding:12px 14px; border-radius:8px; font-size:12px; overflow-x:auto; margin:0; line-height:1.6;"><code>python -m vinci dossier requirements --ticker &lt;TICKER&gt;  # which licensed CIQ to pull first
python -m vinci dossier --ticker &lt;TICKER&gt;               # assemble one finalist (facts + fenced synthesis)
python -m vinci dossier --top 10                         # or: the top 10 of the ranked queue
python3 frontend/build.py                                # mirror into this dashboard, then reload</code></pre>
    </details>`;
}

// (A2) PER-TIER endnotes — each cite becomes a numbered [n] marker (a superscript with a hover
// tooltip) resolving to that tier's own Sources list at its end. Per-tier, NOT one global list: the
// tabs + PDF-scope dropdown must each be self-contained (a [n] on the Brief tab can't resolve into a
// hidden Analysis tab; a "Brief" PDF lists only the Brief's sources). citeMark emits a placeholder;
// withEndnotes numbers them in READING order (two-pass) so the [n] are monotonic down the page even
// though cards may pre-compute their cites out of DOM order.
function citeMark(sourceRef) {
  if (!sourceRef) return "";  // a PRESENT fact always has a ref; guard defensively (no marker if absent)
  return `<sup class="cite-n" data-ref="${escapeHtml(sourceRef)}">[?]</sup>`;  // numbered by withEndnotes
}
// (review #9) ONE definition of the citeMark placeholder shape, parsed by BOTH withEndnotes and
// auditCitesInline — so a change to citeMark's markup can't leave one consumer's ad-hoc regex stale
// ("two divergent parsers of one string" is the documented bug class). A FRESH /g regex per call (no
// shared lastIndex across .replace). Capture group 1 = the (already HTML-escaped) source_ref.
const citePlaceholders = () => /<sup class="cite-n" data-ref="([^"]*)">\[\?\]<\/sup>/g;
function withEndnotes(prefix, fn) {
  // (L2) tier-prefix the markers ([B4]/[A4]/[X4]) so they stay UNAMBIGUOUS when all tiers print
  // together in a "Full dossier" PDF, while each tab / print-scope keeps its own self-contained list.
  const order = [];
  const body = fn().replace(citePlaceholders(), (_m, ref) => {
    let i = order.indexOf(ref);  // ref is already HTML-escaped (from citeMark) — dedup by exact string
    if (i < 0) { order.push(ref); i = order.length - 1; }
    return `<sup class="cite-n" title="${ref}">[${prefix}${i + 1}]</sup>`;
  });
  if (!order.length) return body;
  const items = order.map((r, i) =>
    `<li><span class="src-n">[${prefix}${i + 1}]</span> <span class="mono">${r}</span></li>`).join("");
  return body + `<div class="card ds-section ds-sources"><div class="ds-title">Sources</div><ol>${items}</ol></div>`;
}
// (L3) An on-demand audit <details> is print-EXCLUDED; render ITS provenance cites INLINE (source_ref
// shown) rather than as endnotes, so they leave no orphan [n] Sources entry with no visible marker in
// a printed "Full" dossier. Converts only this block's cite placeholders; the main body still endnotes.
function auditCitesInline(html) {
  return html.replace(citePlaceholders(), (_m, ref) => ` <span class="cite">${ref}</span>`);
}

// --- a single Sourced fact: value + [n] cite, or honest UNKNOWN/MISSING --
function fact(label, s, fmt, { hi = false } = {}) {
  s = s || {};
  const present = s.status === "present" && s.value != null;
  if (!present) {
    // "not applicable by fact" (e.g. negative earnings → no meaningful P/E) reads as N/A, not a data gap
    const na = s.status !== "missing" && /no positive eps|negative earnings|not applicable|^\s*n\/a/i.test(s.note || "");
    const badge = s.status === "missing" ? "MISSING" : (na ? "N/A" : "UNKNOWN");
    return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
      <div class="fact-val muted"><span class="pill unresolved">${badge}</span> ${escapeHtml(s.note || "")}</div></div>`;
  }
  const val = fmt ? fmt(s.value) : escapeHtml(String(s.value)); // fmt() returns safe formatted text
  const cite = citeMark(s.source_ref);
  // a note ON a present value is a caveat (e.g. a distorted P/E that must not read as a clean multiple)
  const caveat = s.note ? `<div class="fact-caveat">⚠ ${escapeHtml(s.note)}</div>` : "";
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div class="fact-val${hi ? " hi" : ""}">${val}${cite}${caveat}</div></div>`;
}

const sec = (title, sub, inner) => `<div class="card ds-section"><div class="ds-title">${escapeHtml(title)}</div>${sub ? `<div class="subtitle muted ds-sub">${escapeHtml(sub)}</div>` : ""}${inner}</div>`;
// (P7) a sub-heading WITHIN a card — used to club the three survival fragments under one Survival card.
const subhead = (t) => `<div class="ds-title" style="font-size:12px; margin-top:14px;">${escapeHtml(t)}</div>`;
const mult = (v) => escapeHtml(Number(v).toFixed(1)) + "&times;";
// (H3) the comparability gate renders VERBATIM once (Peer comps head); the G + Implied-Valuation
// headers cite it SHORT rather than repeating the full text. A non-heterogeneous gate stays verbatim.
const gateShortref = (gate) => (gate || "").includes("HETEROGENEOUS")
  ? "comparability: HETEROGENEOUS (see Peer comps gate)" : (gate || "");
const pctile = (v) => escapeHtml((Number(v) * 100).toFixed(0)) + "<span class='muted'>th %ile vs ~5y</span>";
const ret = (v) => fmtPct(v, { signed: true });
const signWord = (v) => (v > 0 ? "positive" : v < 0 ? "negative" : "breakeven");

// --- multi-period series (margin trend / trajectory / surprise) → a scannable metric×period table.
// The mechanical layer encodes these as a deterministic string ("<metric>: <period> [(basis)] <value>
// → …; …" with a trailing note). We parse it into a grid and render a table; anything that doesn't
// parse falls back to the plain-text fact() — presentation only, never breaks, never alters a value.
function parseSeries(text) {
  let s = String(text).trim();
  let note = "";
  const m = s.match(/\s*\[([^\]]*)\]\s*$/) || s.match(/\s*\(([^()]*)\)\s*$/);
  if (m) { note = m[1]; s = s.slice(0, m.index).trim(); }
  const series = [], scalars = [];
  for (const seg of s.split(";")) {
    const t = seg.trim();
    const ci = t.indexOf(": ");
    if (ci < 0) continue;
    const label = t.slice(0, ci).trim();
    const data = t.slice(ci + 2).trim();
    const sep = data.includes(" → ") ? " → " : (data.includes(", ") ? ", " : null);
    if (!sep) { scalars.push({ label, value: data }); continue; }
    const points = [];
    for (const raw of data.split(sep)) {
      const toks = raw.trim().split(/\s+/);
      if (toks.length < 2) continue;
      const b = toks[toks.length - 2];
      const hasBasis = b && b.startsWith("(") && b.endsWith(")");
      points.push({ period: toks.slice(0, hasBasis ? -2 : -1).join(" "),
                    basis: hasBasis ? b.slice(1, -1) : "", value: toks[toks.length - 1] });
    }
    if (points.length) series.push({ label, points });
  }
  return { series, scalars, note };
}

function fmtPeriod(p) {
  let m = p.match(/^([A-Za-z]{3})-\d{2}-(\d{4})$/);
  if (m) return `${m[1]} '${m[2].slice(2)}`;
  m = p.match(/^FY(\d{4})$/);
  return m ? `FY${m[1].slice(2)}` : p;
}

// Chronological sort key from a period label ("FY2018", "Dec-31-2024", "2024"): year*13 + month, so
// columns order by time even when sub-series span different ranges (EDGAR revenue runs further back
// than its EBITDA-margin). No parseable year → Infinity (sorts last). Stable on same-period ties.
const _MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
                  jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
function periodKey(p) {
  const y = (String(p).match(/(\d{4})/) || [])[1];
  if (!y) return Infinity;
  const mm = (String(p).toLowerCase().match(/jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec/) || [])[0];
  return Number(y) * 13 + (mm ? _MONTHS[mm] : 0);
}

// B4: series (margin/trajectory/surprise/trading-multiples) now route through the ONE shared
// dataTable — parse the metric×period string into a grid, then render via dataTable (no legacy path).
function seriesTable(label, s) {
  if (!s || s.status !== "present" || s.value == null) return fact(label, s);  // honest UNKNOWN/MISSING
  let parsed;
  try { parsed = parseSeries(s.value); } catch { parsed = { series: [], scalars: [], note: "" }; }
  if (!parsed.series.length) return fact(label, s);  // unparseable shape → raw-text fallback
  const periods = [];
  for (const sr of parsed.series) for (const p of sr.points) if (!periods.includes(p.period)) periods.push(p.period);
  periods.sort((a, b) => periodKey(a) - periodKey(b));  // chronological columns across uneven sub-series
  const cols = periods.map(fmtPeriod);
  const rows = parsed.series.map((sr) => {
    const by = Object.fromEntries(sr.points.map((p) => [p.period, p]));
    return { label: sr.label, cells: periods.map((p) => (by[p] ? by[p].value + (by[p].basis ? ` (${by[p].basis})` : "") : DASH)) };
  });
  let note = parsed.note || "";
  if (parsed.scalars.length) note = (note ? note + " · " : "") + parsed.scalars.map((x) => `${x.label}: ${x.value}`).join(" · ");
  return dataTable(label, s.source_ref, cols, rows, note);
}

// (D3) deterministic render-side ordering of bull/bear points — MIRRORS render.py. Tier from the
// claim text (concession clause stripped first) via a face-validity keyword map; highest tier wins;
// ties keep emission order (stable). Human view shows NO tier tag (dev-only in the md).
const _TIERKW = [
  [1, ["free cash flow", "levered free cash", "fcf", "self-fund", "self fund", "cash generat",
       "cash burn", "cash-negative", "interest coverage", "maturity", "wall", "covenant", "refinanc",
       // (A4) BOTH space + hyphen — the hyphen variant was missed (parity with render.py)
       "liquidity", "going concern", "going-concern", "solven", "net-debt", "net debt",
       "total-debt", "total debt",
       "debt/ebitda", "adjusted ebitda negative", "adjusted ebitda was negative",
       "ebitda was negative"]],
  [2, ["revenue", "top-line", "topline", "volume", "shipment", "bookings", "backlog", "orders",
       "guide", "guidance", "deteriorat", "growth"]],
  [3, ["margin", "gross profit", "operating leverage", "opex", "cost structure", "profitab",
       "net profit", "non-operating", "earnings quality"]],
  [4, ["peer", "competit", "customer", "concentrat", "market share", "moat", "supplier", "segment"]],
  [5, ["valuation", "multiple", "p/e", "ev/ebitda", "discount", "re-rate", "rerate", "underperform",
       "percentile", "%ile", "cheap", "expensive", "vs iwm", "relative"]],
];
// (R1, mirrored from render.py `_TIER_REGEX`) interposition-tolerant Tier-1: "(adjusted) EBITDA …
// negative" (words may sit between, e.g. "EBITDA of NEGATIVE $5.5M"), a solvency/cash line "… turned
// negative", or "cash-negative". Checked BEFORE the keyword map. Bare "turned negative" was removed
// from the keywords (R1 audit) so a subject-less "guidance turned negative" no longer false-hits T1.
const _TIER_RE = /\b(?:adjusted\s+)?ebitda\b(?:\s+\w+){0,3}\s+negative\b|\badjusted\s+ebitda\b.{0,40}?(?:-\s*\$|\(|negative)|\b(?:cash[\s-]*flow|fcf|free\s+cash\s+flow|operating\s+(?:income|cash\s*flow)|ocf)\b(?:\s+\w+){0,3}\s+turned\s+negative\b|\bcash-negative\b/i;  /* (K6) mirrors render._TIER_REGEX[0] */
const _CONCESSION = /\b(?:though|although|but|however|offset by|posing whether|the human must weigh)\b/i;
function _pointTier(claim) {
  const m = (claim || "").match(_CONCESSION);
  const c = m ? (claim || "").slice(0, m.index) : (claim || "");
  if (_TIER_RE.test(c)) return 1;  // (R1) interposition-tolerant regex wins first, mirrors render.py
  const cl = c.toLowerCase();
  for (const [tier, kws] of _TIERKW) if (kws.some((k) => cl.includes(k))) return tier;
  return 4.5;  // unclassifiable → between competitive (4) and valuation (5); never dropped
}
function _citRank(p) {
  const s = (p.source_ref || "").toLowerCase();
  if (p.cited === false || s.includes("llm-suggested") || s.includes("unverified")) return 2;
  return s.includes("transcript") ? 1 : 0;
}
function orderPoints(pts) {  // stable sort by (tier, citation-class, emission index)
  return (pts || []).map((p, i) => ({ p, t: _pointTier(p.claim), c: _citRank(p), i }))
    .sort((a, b) => a.t - b.t || a.c - b.c || a.i - b.i).map((x) => x.p);
}

// (D2) merge 'Margin trend' + 'Multi-year trajectory' into ONE table (reuse parseSeries). Rows keyed
// by canonical label (revenue/EBITDA identical across the two → no drift); footnote fragments deduped.
function trajectoryTable(q) {
  const label = "Trajectory (revenue · EBITDA · margins · ROIC)";
  const srcs = [q.margin_trend, q.multi_year_trajectory].filter((s) => s && s.status === "present" && s.value != null);
  if (!srcs.length) return fact(label, q.margin_trend || q.multi_year_trajectory);
  const byLabel = new Map(); const scalars = []; const notes = []; const periods = [];
  for (const s of srcs) {
    let parsed; try { parsed = parseSeries(s.value); } catch { continue; }
    for (const sr of parsed.series) {
      byLabel.set(sr.label.toLowerCase(), sr);  // later wins; revenue/EBITDA identical → no drift
      for (const pt of sr.points) if (!periods.includes(pt.period)) periods.push(pt.period);
    }
    for (const sc of parsed.scalars || []) scalars.push(sc);
    if (parsed.note) notes.push(parsed.note);
  }
  if (!byLabel.size) return fact(label, srcs[0]);
  periods.sort((a, b) => periodKey(a) - periodKey(b));
  const DISP = { "absolute revenue": "Revenue ($M)", "revenue": "Revenue ($M)",
    "absolute ebitda": "EBITDA ($M)", "ebitda": "EBITDA ($M)", "ebitda margin": "EBITDA margin",
    "gross margin": "Gross margin", "roic": "ROIC" };  // canonical labels (match render.py)
  const order = Object.keys(DISP);
  const seen = new Set(); const rows = [];
  for (const key of order) {
    if (!byLabel.has(key) || seen.has(DISP[key])) continue;
    seen.add(DISP[key]);
    const sr = byLabel.get(key);
    const by = Object.fromEntries(sr.points.map((pt) => [String(pt.period).replace(/\s*\((?:R|LTM)\)/i, "").trim(), pt]));
    rows.push({ label: DISP[key], cells: periods.map((per) => {
      const k = String(per).replace(/\s*\((?:R|LTM)\)/i, "").trim();
      return by[k] ? by[k].value + (by[k].basis ? ` (${by[k].basis})` : "") : DASH;
    }) });
  }
  const frags = [];
  for (const n of notes) for (const f of n.split(";")) { const t = f.trim(); if (t && !frags.includes(t)) frags.push(t); }
  let note = scalars.map((x) => `${x.label}: ${x.value}`).join(" · ");
  note = [note, frags.join("; ")].filter(Boolean).join(". ");
  return dataTable(label, srcs[0].source_ref, periods.map(fmtPeriod), rows, note);
}

export function renderDossier(d, verdict) {  // exported for the module-load smoke test (renders the
  const m = d.mechanical || {};              // committed dossier JSON to HTML in node, no DOM/fetch)
  // (3-tier) Brief (first cut) · Analysis (full dossier) · Appendix (data & audit). ONE document; the
  // tabs are client-side chrome (default Brief, no re-fetch). Mirrors the # Brief / # Analysis /
  // # Appendix top-level sections in render.py. The machine still never concludes — the Brief leads
  // with the assembled READ, never a verdict.
  // (A2) each tier renders inside withEndnotes(): its cites become [n] markers + a per-tier Sources
  // list at its end (self-contained per tab / per PDF scope).
  return header(d) + tierTabs() + `<div class="ds-tiers">
    <section class="ds-tier on" data-tier="brief">${withEndnotes("B", () => briefTier(d, verdict, m))}</section>
    <section class="ds-tier" data-tier="analysis">${withEndnotes("A", () => analysisTier(d, m))}</section>
    <section class="ds-tier" data-tier="appendix">${withEndnotes("X", () => appendixTier(d, verdict, m))}</section>
  </div>`;
}

function tierTabs() {
  return `<div class="ds-tabs" role="tablist">
    <button class="ds-tab on" type="button" data-tier="brief" role="tab">Brief <span class="s">first cut</span></button>
    <button class="ds-tab" type="button" data-tier="analysis" role="tab">Analysis <span class="s">full dossier</span></button>
    <button class="ds-tab" type="button" data-tier="appendix" role="tab">Appendix <span class="s">data &amp; audit</span></button>
  </div>`;
}

// ANALYSIS tier — the full mechanical dossier + the FULL synthesis (today's dossier body). The caveats
// head it: verify before trusting the evidence below.
function analysisTier(d, m) {
  return flagsSection(d.caveats || d.flags || [])       // D1: caveats first (what to verify)
    + drawdownIdio(m)                                   // drawdown cause + idiosyncrasy, clubbed
    + leverageSurvival(m, d.reference_date)             // leverage & survival + capital structure
    + trajectorySection(m.quality || {})                // merged trajectory table + share-count
    + valuation(m.valuation)                            // valuation & own-history
    + peerComps(m.peer_comps)                           // peer comps (per-peer grid inside)
    + catalystPath(m.catalyst_path, m.consensus_context)
    + (m.catalyst_path ? "" : consensus(m.consensus_context))  // legacy fallback only for old JSON
    + concentration(m.concentration)
    + synthesis(d.synthesis);                           // D3 ordering + twins last — FULL synthesis here
}

// APPENDIX tier — data & audit: financial summary + cap-structure provenance + implied-val reference +
// mgmt pointer (appendixBlock), then the logged-verdict block and the no-BUY/AVOID footer.
function appendixTier(d, verdict, m) {
  return appendixBlock(m)
    + loggedVerdict(verdict, d.ticker, d.reference_date)
    + verdictFooter();
}

// --- (Brief) first-cut tier — leads with the machine READ (evidence_balance), the decisive question,
// a compact decision-data strip, and only the DECISION-THREATENING caveats. Assembles from existing
// fields, renders NO verdict; the human's logged verdict shows only as a read-only status chip (the
// machine never fills it). Mirrors _brief_lines() in vinci/dossier/render.py.
const _BRIEF_DECISION_KW = /leverage|covenant|going.?concern|maturity|wall|liquidity|dilut|solven|\bbasis\b|runway|refinanc|\bcash\b/i;

function briefVerifyFirst(caveats, limit = 2) {
  const out = [];
  for (const c of caveats || []) {
    if (!_BRIEF_DECISION_KW.test(c)) continue;
    let lead = String(c).split(/;|\s+—\s+/)[0].trim();
    if (lead.length > 120) lead = lead.slice(0, 117).trimEnd() + "…";
    out.push(lead);
    if (out.length >= limit) break;
  }
  return out;
}

function briefTile(label, value, danger) {
  return `<div class="brief-mc"><div class="l">${escapeHtml(label)}</div><div class="v${danger ? " dang" : ""}">${value}</div></div>`;
}

function briefStrip(m) {
  const tiles = [];
  const io = m.idiosyncratic_vs_shared;
  if (io && io.rel_vs_market && io.rel_vs_market.status === "present")
    tiles.push(briefTile("Idio (vs mkt, 180d)", fmtPct(io.rel_vs_market.value, { signed: true })));
  const q = m.quality || {};
  if (q.net_debt_to_ebitda && q.net_debt_to_ebitda.status === "present")
    tiles.push(briefTile("Net debt/EBITDA", mult(q.net_debt_to_ebitda.value)));
  if (q.fcf_sign && q.fcf_sign.status === "present")
    tiles.push(briefTile("Free cash flow", escapeHtml(signWord(q.fcf_sign.value))));
  const gc = (((m.primary_source || {}).filing || {}).going_concern) || null;
  if (gc) tiles.push(briefTile("Going concern", gc.substantial_doubt ? "⚠ substantial doubt" : "not flagged", gc.substantial_doubt));
  const strip = tiles.length ? `<div class="brief-strip">${tiles.join("")}</div>` : "";
  const val = (m.valuation && m.valuation.cross_sectional) ? fact("Valuation (vs peers)", m.valuation.cross_sectional) : "";
  return strip + val;
}

function briefVerdictChip(verdict) {
  if (!verdict) {
    return `<div class="brief-chip"><span class="pill unresolved">verdict — not yet logged</span>
      <span class="muted" style="font-size:11.5px;">the human logs it after reviewing the facts</span></div>`;
  }
  const isBuy = isBuyVerdict(verdict.verdict);
  return `<div class="brief-chip"><span class="pill ${isBuy ? "buy" : "avoid"}">${escapeHtml(verdict.verdict)}</span>
    <span class="muted" style="font-size:11.5px;">logged @ ${fmtPrice(verdict.entryPrice)} · ${fmtDate(verdict.decidedAt)}</span></div>`;
}

// (Brief) the market-standard first-cut, 7 sections: teaser → setup → company → case → financial
// snapshot → valuation → verify. Machine-assembled + source-bound throughout; the Recommendation /
// Target slot is the HUMAN's (never machine-filled). Mirrors _brief_lines() in render.py.
function briefTier(d, verdict, m) {
  const parts = teaserCard(d, verdict, m) + setupCard(m, d.synthesis) + companyCard(m)
    + briefCase(d.synthesis) + financialSnapshot(m) + valuationCard(m) + catalystCard(m) + verifyCard(d);
  return parts.trim() ? parts : "";
}

// first sentence of a CIQ business description ("{Co}, Inc. engages in …") — abbreviation-aware so
// the split doesn't stop at "Inc."/"Corp."; capped for the teaser.
function firstSentence(text, cap = 220) {
  const pieces = String(text).split(/(?<=\.)\s+/);
  let sent = "";
  for (const p of pieces) {
    sent = sent ? sent + " " + p : p;
    if (!/\b(Inc|Corp|Ltd|Co|LLC|LP|plc|Ltda|S\.A|N\.V)\.$/.test(sent)) break;
  }
  return sent.length <= cap ? sent : sent.slice(0, cap).replace(/\s+\S*$/, "") + "…";
}

const fmtCap = (v) => (v >= 1000 ? `$${(v / 1000).toFixed(1)}B` : `$${Math.round(v)}M`);  // v in $M

function fmtShares(v) { return v >= 1e9 ? `${(v / 1e9).toFixed(1)}B` : `${(v / 1e6).toFixed(1)}M`; }


// 1 — TEASER (at-a-glance): a 2/3 NARRATIVE (business one-liner · machine read · the human's
// Recommendation/Target slot) beside a 1/3 SNAPSHOT table (identity + exchange + stock-info + CIK),
// consolidated from what used to repeat across the header meta / brief-meta / stock-info line. The
// verdict slot is filled only from the ledger — never by the machine.
// The machine's evidence READ — a "{lean} — {why}" balance, e.g. "strongly-bearish — stated going-concern
// doubt …". The lean is an evidence sentiment, NOT a BUY/AVOID verdict (that stays the human's, in the
// Recommendation slot right below). We tint the lean by direction (bear→danger, bull→live, mixed/neutral→
// grey) and sentence-case it; the rest is plain body text. Fail-soft: an un-split read renders verbatim.
function machineReadHtml(eb) {
  const m = /^\s*([A-Za-z][A-Za-z\- ]*?)\s*[—–-]\s+([\s\S]+)$/.exec(eb || "");
  if (!m) return escapeHtml(eb || "");
  const lean = m[1].trim(), rest = m[2];
  const l = lean.toLowerCase();
  const col = l.includes("bear") ? "var(--danger)" : l.includes("bull") ? "var(--live)" : "var(--ink-2)";
  const cased = lean.charAt(0).toUpperCase() + lean.slice(1);
  return `<b class="brief-lean" style="color:${col}">${escapeHtml(cased)}</b> — ${escapeHtml(rest)}`;
}

function teaserCard(d, verdict, m) {
  const s = d.synthesis;
  const one = (d.business_description && d.business_description.status === "present")
    ? firstSentence(d.business_description.value) : "";
  const vslot = verdict
    ? `<span class="pill ${isBuyVerdict(verdict.verdict) ? "buy" : "avoid"}">${escapeHtml(verdict.verdict)}</span> <span class="muted" style="font-size:11.5px;">@ ${fmtPrice(verdict.entryPrice)} · ${fmtDate(verdict.decidedAt)}</span>`
    : `<span class="brief-slot">not yet logged</span> <span class="muted" style="font-size:11px;">the human's call — Buy / Avoid + target</span>`;
  const read = (s && s.evidence_balance)
    ? `<div class="brief-read">${machineReadHtml(s.evidence_balance)}</div>` : "";
  const narrative = `<div class="brief-narrative">
    ${one ? `<div class="brief-oneliner">${escapeHtml(one)}</div>` : ""}
    ${read}
    <div class="brief-verdict"><span class="brief-vlab">Recommendation / Target</span> ${vslot}</div>
  </div>`;
  return `<div class="card ds-section ds-brief">
    <div class="brief-body">${narrative}${briefSnapshot(d, m)}</div></div>`;
}

// the Brief SNAPSHOT — a MOFSL-style label|value table of the scalar facts (identity · exchange · CMP ·
// market cap · 52-wk · shares · book value/sh · CIK), consolidated from what used to be scattered across
// the header meta, brief-meta, and the stock-info line. Fail-honest: a row is dropped when its source is
// absent (e.g. AORT has no Book Value/Share row in its CIQ export → no Book/sh row, never a guess).
function briefSnapshot(d, m) {
  const si = m.stock_info || {};
  const ok = (f) => f && f.status === "present" && f.value != null;
  const rows = [];
  const push = (label, val) => { if (val) rows.push(`<tr><td>${label}</td><td>${val}</td></tr>`); };
  if (d.exchange) push("Exchange", escapeHtml(d.exchange));
  if (ok(si.price)) push("CMP", `$${si.price.value.toFixed(2)}${si.as_of ? ` <span class="muted">(${escapeHtml(si.as_of)})</span>` : ""}`);
  if (ok(si.market_cap)) push("Market cap", fmtCap(si.market_cap.value));
  if (ok(si.low_52w) && ok(si.high_52w)) push("52-wk range", `$${si.low_52w.value.toFixed(2)}–$${si.high_52w.value.toFixed(2)}`);
  if (ok(si.shares_out)) push("Shares out", fmtShares(si.shares_out.value));
  if (ok(si.book_value_ps)) push("Book / sh", `$${si.book_value_ps.value.toFixed(2)}`);
  if (d.cik) push("CIK", `<span class="mono">${escapeHtml(d.cik)}</span>`);
  if (!rows.length) return "";
  return `<div class="brief-snap">
    <div class="brief-snap-idn"><span class="mono">${escapeHtml(d.ticker)}</span> · ${escapeHtml(d.name || "")}</div>
    <table class="brief-snap-t"><tbody>${rows.join("")}</tbody></table></div>`;
}

// 2 — SETUP: why it's a candidate (drawdown, idiosyncratic) + the decisive question + decision snapshot.
function setupCard(m, s) {
  const io = m.idiosyncratic_vs_shared || {};
  const dd = (io.name_180d_return && io.name_180d_return.status === "present") ? fmtPct(io.name_180d_return.value, { signed: true }) : null;
  const idio = (io.rel_vs_market && io.rel_vs_market.status === "present") ? fmtPct(io.rel_vs_market.value, { signed: true }) : null;
  let setup = "";
  if (dd) setup = `<div style="font-size:12.5px;">Fell <span class="mono">${dd}</span> over 180d${idio ? `, idiosyncratic (<span class="mono">${idio}</span> vs market)` : ""} — an overshoot candidate.</div>`;
  else if (idio) setup = `<div style="font-size:12.5px;">Idiosyncratic <span class="mono">${idio}</span> vs the market over 180d — an overshoot candidate.</div>`;
  const dq = (s && s.decisive_question && s.decisive_question.question)
    ? `<div class="brief-dq" style="margin-top:6px;"><b>Decisive question:</b> ${escapeHtml(s.decisive_question.question)}</div>` : "";
  const strip = briefStrip(m);
  if (!setup && !dq && !strip) return "";
  return `<div class="card ds-section"><div class="ds-title">The setup</div>${setup}${dq}${strip}</div>`;
}

// 3 — COMPANY & BUSINESS: segments · geography · customer CONCENTRATION (the top-customer %, a real
// risk — NOT the raw customer names, which are noise in an institutional first cut).
function companyCard(m) {
  const c = m.concentration || {};
  const fil = (m.primary_source || {}).filing || {};
  const custs = ((fil.concentration || {}).customers || []).filter((x) => x && x.pct != null);
  let concLine = "";
  if (custs.length) {
    const top = custs.slice().sort((a, b) => b.pct - a.pct);
    const top2 = top.slice(0, 2).reduce((s, x) => s + x.pct, 0);
    const val = `top customer <span class="mono">${Math.round(top[0].pct)}%</span>${top[0].prior_pct != null ? ` <span class="muted">(from ${Math.round(top[0].prior_pct)}%)</span>` : ""}${top.length > 1 ? ` · top-2 ~<span class="mono">${Math.round(top2)}%</span>` : ""} of revenue`;
    concLine = `<div class="fact"><div class="fact-label">Customer concentration</div><div class="fact-val">${val}${citeMark(fil.source_ref)}</div></div>`;
  }
  const rows = [
    (c.segments && c.segments.status === "present") ? fact("Segments", c.segments) : "",
    (c.geographic && c.geographic.status === "present") ? fact("Geography", c.geographic) : "",
    concLine,
  ].join("");
  if (!rows) return "";
  return `<div class="card ds-section"><div class="ds-title">Company &amp; business</div>${rows}</div>`;
}

// 4 — THE CASE: condensed top-3 bull / top-3 bear (evidence-weighted, same order as Analysis) +
// top-3 key unknowns. The FULL bull/bear lives in the Analysis synthesis; source-bound throughout.
function briefCase(s) {
  if (!s || (!(s.bull_points || []).length && !(s.bear_points || []).length)) return "";
  const pt = (p, cls) => `<div class="point ${cls}">${escapeHtml(p.claim)}${citeMark(p.source_ref)}</div>`;
  const bulls = orderPoints(s.bull_points).slice(0, 3).map((p) => pt(p, "bull")).join("") || `<div class="muted">—</div>`;
  const bears = orderPoints(s.bear_points).slice(0, 3).map((p) => pt(p, "bear")).join("") || `<div class="muted">—</div>`;
  const uks = (s.key_unknowns || []).slice(0, 3);
  const uk = uks.length ? `<div class="ds-title" style="font-size:12px; margin-top:12px;">Key unknowns</div><ul class="kv-list">${uks.map((k) => `<li>${escapeHtml(k)}</li>`).join("")}</ul>` : "";
  return `<div class="card ds-section"><div class="ds-title">The case <span class="muted" style="font-weight:400; text-transform:none; letter-spacing:0;">— top points; full bull/bear in Analysis</span></div>
    <div class="brief-case">
      <div><div class="ds-title" style="font-size:12px; color:#16713e;">Bull — overshoot</div>${bulls}</div>
      <div><div class="ds-title" style="font-size:12px; color:var(--danger);">Bear — terminal</div>${bears}</div>
    </div>${uk}</div>`;
}

// (Phase-3) Revenue + EBITDA bars ($M) + EBITDA-margin % line — the institutional financial-trend
// exhibit as a dependency-free inline SVG (theme-aware via CSS vars; prints with the Brief). Consumes
// the STRUCTURED `values` + `is_estimate` (NEVER the display cells — parsers rule); estimate columns
// are shaded + reduced-opacity + labelled CONSENSUS (never the machine's own forecast). Fail-honest:
// absent structured series (a pre-P3 dossier.json) → no chart, the table below still renders.
function revEbitdaExhibit(fsa) {
  const v = fsa && fsa.value;
  if (!v || !Array.isArray(v.rows) || !Array.isArray(v.columns)) return "";
  const cols = v.columns, isE = v.is_estimate || [];
  const rowVals = (lbl) => ((v.rows.find((r) => r.label === lbl) || {}).values) || [];
  const rev = rowVals("Revenue ($M)"), ebitda = rowVals("EBITDA ($M)"), n = cols.length;
  if (!n || !rev.some((x) => x != null)) return "";  // no structured series → skip (the table stays)
  const marg = cols.map((_c, i) =>
    (rev[i] != null && ebitda[i] != null && rev[i]) ? (ebitda[i] / rev[i]) * 100 : null);

  // SIDE-BY-SIDE panels (compact vs stacked, but sized for readability): a $M bars panel LEFT + a %
  // margin panel RIGHT, each AUTO-SCALED to its own data with its own zero baseline so no scale is ever
  // shared/clamped (a negative EBITDA or margin — MVST — renders correctly). Haloed labels read over bars.
  // shared design FRAME (canvas / y-band / fonts / halo / margin) from lib/exhibit.js — the ONE visual
  // system every dossier exhibit references, so size/padding/spacing/labelling match across them.
  const { cy0, cy1, fs, halo } = EXHIBIT, W = EXHIBIT.wDual, H = EXHIBIT.H;
  // scales / honest domains / nice-ceiling also come from lib/exhibit.js (shared + node-tested) —
  // barDomain spans zero with a fine ceiling + label headroom; lineDomain pads beyond zero on a real side.
  const abbr = (c) => String(c).replace(" (R)", "");
  const firstE = isE.findIndex((b) => b);
  // estimate shade is a BACKGROUND — render BEFORE the bars/labels so the E-column figures sit on top
  // (were behind the overlay). x-labels render LAST, over everything.
  const estShade = (px1, cxf, slot) => firstE >= 0 ? `<rect x="${cxf(firstE) - slot / 2}" y="${cy0}" width="${px1 - (cxf(firstE) - slot / 2)}" height="${cy1 - cy0}" fill="var(--surface-2)" opacity="0.7"/><line x1="${cxf(firstE) - slot / 2}" y1="${cy0}" x2="${cxf(firstE) - slot / 2}" y2="${cy1}" stroke="var(--line-2)" stroke-dasharray="3 3"/>` : "";
  const xTicks = (cxf) => cols.map((c, i) => `<text x="${cxf(i)}" y="${cy1 + 16}" font-size="${fs.xlabel}" text-anchor="middle" fill="${isE[i] ? "var(--ink-3)" : "var(--ink-2)"}">${escapeHtml(abbr(c))}</text>`).join("");

  // ---- LEFT panel: Revenue + EBITDA bars ($M), zero baseline (handles a negative EBITDA) ----
  const lx0 = 44, lx1 = 366, slotL = (lx1 - lx0) / n, cxL = (i) => lx0 + slotL * i + slotL / 2;
  const bwL = Math.min(16, slotL * 0.4);
  const { lo: loL, hi: hiL } = barDomain([...rev, ...ebitda]);  // spans 0; fine ceiling + 1.1 headroom
  const sBL = linScale(loL, hiL, cy1, cy0), baseL = sBL(0);
  let left = estShade(lx1, cxL, slotL) + `<text x="${lx0}" y="${cy0 - 9}" font-size="${fs.panel}" font-weight="600" fill="var(--ink-2)">Revenue &amp; EBITDA ($M)</text><line x1="${lx0}" y1="${baseL}" x2="${lx1}" y2="${baseL}" stroke="var(--line-2)"/><text x="${lx0 - 4}" y="${cy0 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(hiL)}</text><text x="${lx0 - 4}" y="${baseL + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">0</text>`;
  if (loL < 0) left += `<text x="${lx0 - 4}" y="${cy1 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(loL)}</text>`;
  left += cols.map((c, i) => {
    const op = isE[i] ? 0.5 : 1, rx = cxL(i) - bwL - 1, ex = cxL(i) + 1;
    let s = "";
    if (rev[i] != null) { const yv = sBL(rev[i]); s += `<rect x="${rx}" y="${Math.min(yv, baseL)}" width="${bwL}" height="${Math.max(1, Math.abs(yv - baseL))}" fill="var(--accent)" opacity="${op}" rx="1"/><text x="${rx + bwL / 2}" y="${yv - 4}" font-size="9.5" text-anchor="middle" fill="var(--ink-2)" ${halo}>${Math.round(rev[i])}</text>`; }
    if (ebitda[i] != null) { const yv = sBL(ebitda[i]), neg = ebitda[i] < 0; s += `<rect x="${ex}" y="${Math.min(yv, baseL)}" width="${bwL}" height="${Math.max(1, Math.abs(yv - baseL))}" fill="var(--live)" opacity="${op}" rx="1"/><text x="${ex + bwL / 2}" y="${barLabelY(yv, neg)}" font-size="9.5" text-anchor="middle" fill="var(--ink-3)" ${halo}>${Math.round(ebitda[i])}</text>`; }
    return s;
  }).join("") + xTicks(cxL);

  // ---- RIGHT panel: EBITDA margin (%) line, own zero line (handles a negative margin) ----
  const rx0 = 412, rx1 = 748, slotR = (rx1 - rx0) / n, cxR = (i) => rx0 + slotR * i + slotR / 2;
  // margin line: honest zero-anchored domain — pads beyond zero only on a side with real data (no
  // phantom "-3%" under an all-positive margin). minSpan guards an all-zero-margin degenerate ([0,0] →
  // a divide-by-zero scale); the || fallback keeps an all-null-margin panel valid.
  const { lo: mLo, hi: mHi } = lineDomain(marg, { padFrac: 0.2, minPad: 2, minSpan: 2 }) || { lo: 0, hi: 2 };
  const sMR = linScale(mLo, mHi, cy1, cy0), zeroR = sMR(0);
  let right = estShade(rx1, cxR, slotR) + `<text x="${rx0}" y="${cy0 - 9}" font-size="${fs.panel}" font-weight="600" fill="var(--ink-2)">EBITDA margin (%)</text><line x1="${rx0}" y1="${zeroR}" x2="${rx1}" y2="${zeroR}" stroke="var(--line-2)" stroke-dasharray="3 2"/><text x="${rx0 - 4}" y="${cy0 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(mHi)}%</text>`;
  if (mLo < -0.5) right += `<text x="${rx0 - 4}" y="${cy1 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(mLo)}%</text>`;
  const mpts = marg.map((p, i) => (p != null ? `${cxR(i)},${sMR(p)}` : null)).filter(Boolean).join(" ");
  right += `<polyline points="${mpts}" fill="none" stroke="var(--ink-2)" stroke-width="2"/>`;
  right += marg.map((p, i) => (p != null ? `<circle cx="${cxR(i)}" cy="${sMR(p)}" r="3" fill="var(--ink-2)"/><text x="${cxR(i)}" y="${sMR(p) - 7}" font-size="${fs.point}" text-anchor="middle" fill="var(--ink)" font-weight="600" ${halo}>${Math.round(p)}%</text>` : "")).join("");
  right += xTicks(cxR);

  const eLbl = firstE >= 0 ? `<text x="${W - 4}" y="${cy0 - 9}" font-size="${fs.xlabel}" text-anchor="end" fill="var(--ink-3)" font-style="italic">shaded = consensus (E), not our forecast</text>` : "";
  const lg = `<g font-size="${fs.legend}" fill="var(--ink-2)"><rect x="44" y="${H - 14}" width="11" height="11" fill="var(--accent)" rx="1"/><text x="60" y="${H - 5}">Revenue</text><rect x="132" y="${H - 14}" width="11" height="11" fill="var(--live)" rx="1"/><text x="148" y="${H - 5}">EBITDA</text><line x1="224" y1="${H - 8}" x2="242" y2="${H - 8}" stroke="var(--ink-2)" stroke-width="2"/><circle cx="233" cy="${H - 8}" r="2.6" fill="var(--ink-2)"/><text x="248" y="${H - 5}">EBITDA margin %</text></g>`;

  // no inline subtitle (panel headers + x-axis already say it) and no inline "Source:" line — the
  // financial-summary source is cited once at the card level (goes to the tier's Sources list).
  return `<div class="ds-exhibit" style="margin:${EXHIBIT.margin};">
    <svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px; display:block;" role="img" aria-label="Revenue, EBITDA and EBITDA-margin trend">
      <text x="44" y="22" font-size="${fs.title}" font-weight="600" fill="var(--ink)">Revenue, EBITDA &amp; margin</text>
      ${eLbl}${left}${right}${lg}
    </svg>
  </div>`;
}

// 5b — RETURN RATIOS: RoE / RoCE / RoA over the CIQ Ratios fiscal-period columns. SHARES THE EXACT
// design frame of revEbitdaExhibit — canvas 760×276, the cy0/cy1 y-band, title/panel-title/axis/point-
// label fonts, slot centering, and the bottom legend — so every Financial-Snapshot exhibit reads as ONE
// system. TWO panels grouped by SCALE — RoE alone (it can run 10× the others when equity is small, e.g.
// Gartner) | RoCE + RoA together — each on its OWN honest axis, mirroring revEbitda's two-panel split.
// Consumes the STRUCTURED `values` (×100, never a cell re-parse). ACTUALS ONLY — no consensus shade, no
// extrapolation (no-conclude). Fail-honest: a panel with no data drops and the survivor renders at a
// single-panel width (NOT stretched); the YoY table below carries every ratio row.
function returnRatiosExhibit(rr) {
  if (!rr || rr.status !== "present" || !rr.value || !Array.isArray(rr.value.rows)) return "";
  const cols = rr.value.columns || [];
  if (cols.length < 2) return "";
  const pts = (key) => {
    const row = rr.value.rows.find((r) => r.label === key);
    const vals = row && row.values;
    return (Array.isArray(vals) && vals.some((v) => v != null)) ? vals.map((v) => (v == null ? null : v * 100)) : null;
  };
  const roe = pts("RoE %"), roce = pts("RoCE %"), roa = pts("RoA %");
  const { H, cy0, cy1, fs, halo } = EXHIBIT, n = cols.length;  // shared design frame (lib/exhibit.js)
  // one line-panel over [px0,px1] — same frame as revEbitda's margin panel: slot-centred x, own honest
  // domain (lineDomain, identical params), hi/lo % axis labels, a dashed zero line when the range spans
  // it, and per-point value labels (font 10 wt600 haloed). Multi-series: the HIGHER value at each column
  // labels above, the lower below, so a close RoCE/RoA pair separates.
  const panel = (series, px0, px1, title) => {
    const shown = series.filter((s) => s.pts);
    if (!shown.length) return "";
    const slot = (px1 - px0) / n, cx = (i) => px0 + slot * i + slot / 2;
    const all = shown.flatMap((s) => s.pts).filter((v) => v != null);
    const { lo, hi } = lineDomain(all, { padFrac: 0.2, minPad: 2, minSpan: 2 }) || { lo: 0, hi: 2 };
    const sc = linScale(lo, hi, cy1, cy0);
    let g = `<text x="${px0}" y="${cy0 - 9}" font-size="${fs.panel}" font-weight="600" fill="var(--ink-2)">${title}</text>`;
    g += `<text x="${px0 - 4}" y="${cy0 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(hi)}%</text>`;
    g += `<text x="${px0 - 4}" y="${cy1 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(lo)}%</text>`;
    if (lo < 0 && hi > 0) g += `<line x1="${px0}" y1="${sc(0)}" x2="${px1}" y2="${sc(0)}" stroke="var(--line-2)" stroke-dasharray="3 2"/>`;
    g += cols.map((c, i) => `<text x="${cx(i)}" y="${cy1 + 16}" font-size="${fs.xlabel}" text-anchor="middle" fill="var(--ink-2)">${escapeHtml(String(c))}</text>`).join("");
    shown.forEach((s) => {
      const seg = s.pts.map((v, i) => (v == null ? null : `${cx(i)},${sc(v)}`)).filter(Boolean).join(" ");
      g += `<polyline points="${seg}" fill="none" stroke="${s.color}" stroke-width="2"/>`;
      g += s.pts.map((v, i) => {
        if (v == null) return "";
        const top = shown.every((o) => o.pts[i] == null || v >= o.pts[i]);  // highest at column → above
        return `<circle cx="${cx(i)}" cy="${sc(v)}" r="3" fill="${s.color}"/><text x="${cx(i)}" y="${top ? sc(v) - 7 : sc(v) + 14}" font-size="${fs.point}" text-anchor="middle" fill="${s.color}" font-weight="600" ${halo}>${Math.round(v)}%</text>`;
      }).join("");
    });
    return g;
  };
  const roeS = [{ label: "RoE", color: "var(--ink)", pts: roe }];
  const capS = [{ label: "RoCE", color: "var(--accent)", pts: roce }, { label: "RoA", color: "var(--ink-2)", pts: roa }];
  const legendSeries = [...roeS, ...capS].filter((s) => s.pts);
  let body = "", W = EXHIBIT.wDual, note = "";
  if (roe && (roce || roa)) {
    body = panel(roeS, 44, 366, "RoE %") + panel(capS, 412, 748, "RoCE · RoA %");
    note = `<text x="${W - 4}" y="${cy0 - 9}" font-size="${fs.xlabel}" text-anchor="end" fill="var(--ink-3)" font-style="italic">actuals — no forward ratio estimates</text>`;
  } else if (roe) { body = panel(roeS, 44, 366, "RoE %"); W = EXHIBIT.wSingle; }
  else if (roce || roa) { body = panel(capS, 44, 366, "RoCE · RoA %"); W = EXHIBIT.wSingle; }
  else return "";
  // bottom legend — same mark + typography as revEbitda's (a line + dot per series)
  const lg = `<g font-size="${fs.legend}" fill="var(--ink-2)">${legendSeries.map((s, i) => {
    const lx = 44 + i * 78;
    return `<line x1="${lx}" y1="${H - 8}" x2="${lx + 18}" y2="${H - 8}" stroke="${s.color}" stroke-width="2"/><circle cx="${lx + 9}" cy="${H - 8}" r="2.6" fill="${s.color}"/><text x="${lx + 24}" y="${H - 5}">${s.label}</text>`;
  }).join("")}</g>`;
  return `<div class="ds-exhibit" style="margin:${EXHIBIT.margin};">
    <svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px; display:block;" role="img" aria-label="Return ratios (RoE; RoCE and RoA) per fiscal period">
      <text x="44" y="22" font-size="${fs.title}" font-weight="600" fill="var(--ink)">Return ratios</text>
      ${note}${body}${lg}
    </svg>
  </div>`;
}

// 5 — FINANCIAL SNAPSHOT: revenue / EBITDA / EBITDA-margin trajectory (from financial_summary.annual).
function financialSnapshot(m) {
  const fsa = (m.financial_summary || {}).annual;
  if (!fsa || fsa.status !== "present" || !fsa.value) return "";
  const cols = fsa.value.columns || [], want = ["Revenue ($M)", "Revenue growth", "EBITDA ($M)",
    "EBITDA margin", "EBIT ($M)", "Net income ($M)", "EPS (GAAP, dil.)", "FCF ($M)"];
  const rows = (fsa.value.rows || []).filter((r) => want.includes(r.label));
  if (!cols.length || !rows.length) return "";
  const isE = fsa.value.is_estimate || [], ec = (i) => (isE[i] ? " est-col" : "");  // (P3) shade E cols
  const head = `<tr><th></th>${cols.map((c, i) => `<th class="num${ec(i)}">${escapeHtml(String(c))}</th>`).join("")}</tr>`;
  const body = rows.map((r) => `<tr><td>${escapeHtml(r.label)}</td>${(r.cells || []).map((c, i) => `<td class="num mono${ec(i)}">${escapeHtml(String(c))}</td>`).join("")}</tr>`).join("");
  // (Phase-4) the return-ratios line exhibit + per-period YoY table REPLACE the old latest-only "Key
  // ratios" fact. Fail-honest fallback: a name without the CIQ Ratios panel (return_ratios UNKNOWN)
  // keeps the committed latest-period line — never a blank, never a fabricated series.
  const rr = m.return_ratios;
  const ratios = (rr && rr.status === "present" && rr.value && Array.isArray(rr.value.rows) && rr.value.rows.length)
    ? returnRatiosExhibit(rr) + finTable("Return ratios — per fiscal period", rr)
    : (m.key_ratios && m.key_ratios.status === "present") ? fact("Key ratios (latest)", m.key_ratios) : "";
  return `<div class="card ds-section"><div class="ds-title">Financial snapshot <span class="muted" style="font-weight:400; text-transform:none; letter-spacing:0;">— full table in Appendix</span></div>
    ${revEbitdaExhibit(fsa)}
    <table class="data">${`<thead>${head}</thead><tbody>${body}</tbody>`}</table>
    ${citeMark(fsa.source_ref)}${ratios}</div>`;
}

// 6 — VALUATION: cross-sectional read (the edge) + comparability gate + the implied-value REFERENCE
// ladder (peer-median implied equity per basis, juxtaposed vs cap — never a single machine target).
// (Phase-3b) Own-history valuation exhibit — the institutional "multiple band": a TIME-SERIES LINE of
// each multiple over its trailing quarterly closes, with mean / min / max reference levels and the
// current value labelled at the right end. Consumes the STRUCTURED own_history series (never re-parses
// range_position's string); log-scaled where positive (tames a P/E blown out by a near-zero-EPS
// quarter). EV/EBITDA + P/E side-by-side (one wide panel when a name has only one). Fail-honest: no
// structured series (pre-line dossier / no Multiples sheet) → no chart, the string still shows.
function ownHistoryExhibit(m) {
  const oh = m.valuation && m.valuation.own_history;
  if (!oh || oh.status !== "present" || !Array.isArray(oh.value)) return "";
  const bands = oh.value.filter((b) => Array.isArray(b.series) && b.series.length >= 2);
  if (!bands.length) return "";
  // mirror range_position's _MIN_CONFIDENT_CLOSES (ciq_sheets.py): below 8 closes the floor read is
  // unreliable, so the current marker de-escalates to neutral + a footnote — the chart must never read
  // MORE confident than the string it derives from (which prints an explicit LOW-CONFIDENCE caveat).
  const LOW_CONF_CLOSES = 8;
  const anyLowConf = bands.some((b) => b.n_closes < LOW_CONF_CLOSES);
  // a single metric keeps a NORMAL panel width (not stretched full-bleed — that breaks the familiar
  // line aspect); the exhibit just renders narrower. Two metrics sit side-by-side.
  const single = bands.length === 1;
  // cy0 leaves a clear gap under the subtitle so the panel-header row (metric + %ile) never crowds it.
  const W = single ? 430 : 760, H = 240, cy0 = 62, cy1 = 214;  // panels share this chart-area y-band
  const halo = 'paint-order="stroke" stroke="var(--surface)" stroke-width="2.6"';
  const yr = (s) => { const y = /(\d{4})/.exec(s || ""); return y ? "'" + y[1].slice(2) : ""; };
  const geo = single ? [[70, 372]] : [[70, 372], [452, 748]];

  const panel = (b, x0, x1) => {
    const label = b.metric.replace(" (TEV/LTM)", "").replace("P/LTM EPS", "P/E");
    const lowConf = b.n_closes < LOW_CONF_CLOSES;
    const pts = b.series.filter((p) => p && p[1] != null);
    const vals = pts.map((p) => p[1]).concat([b.low, b.high, b.mean]);  // refs stay in-domain
    const useLog = vals.every((v) => v > 0);  // multiples convention; linear guards a non-positive
    let dlo = Math.min(...vals), dhi = Math.max(...vals);
    if (useLog) { dlo *= 0.92; dhi *= 1.08; } else { const p = (dhi - dlo) * 0.08 || 1; dlo -= p; dhi += p; }
    const sc = (useLog && logScale(dlo, dhi, cy1, cy0)) || linScale(dlo, dhi, cy1, cy0);
    const px = (i) => x0 + (i / (pts.length - 1)) * (x1 - x0);
    // trailing-history reference levels: min / avg / max — neutral grey (avg dashed), value at the y-axis
    const ref = (v, dash, tag) => `<line x1="${x0}" y1="${sc(v)}" x2="${x1}" y2="${sc(v)}" stroke="var(--line-2)"${dash ? ' stroke-dasharray="3 3"' : ""}/><text x="${x0 - 5}" y="${sc(v) + 3}" font-size="8.5" text-anchor="end" fill="var(--ink-3)">${tag}</text>`;
    let s = `<text x="${x0}" y="${cy0 - 12}" font-size="11.5" font-weight="600" fill="var(--ink-2)">${escapeHtml(label)}</text>`;
    s += `<text x="${x1}" y="${cy0 - 12}" font-size="8.5" text-anchor="end" fill="var(--ink-3)">${Math.round(b.percentile * 100)}%ile${lowConf ? "*" : ""} · ${b.n_closes}q</text>`;
    s += ref(b.high, false, b.high.toFixed(1)) + ref(b.mean, true, "avg " + b.mean.toFixed(1)) + ref(b.low, false, b.low.toFixed(1));
    s += `<polyline points="${pts.map((p, i) => `${px(i)},${sc(p[1])}`).join(" ")}" fill="none" stroke="var(--accent)" stroke-width="1.6"/>`;
    // current = the last close: DIRECTIONAL color (below/above its own trailing range is a FACT) + value;
    // neutral grey when low-confidence. The human still judges cheap-vs-dear.
    const ci = pts.length - 1, cx = px(ci), cyv = sc(b.current);
    const col = lowConf ? "var(--ink-3)" : b.current < b.low ? "var(--danger)" : b.current > b.high ? "var(--live)" : "var(--accent)";
    const caret = b.current < b.low ? "▼" : b.current > b.high ? "▲" : "●";
    s += `<circle cx="${cx}" cy="${cyv}" r="3.5" fill="${col}" stroke="var(--surface)" stroke-width="1.2"/>`;
    s += `<text x="${cx}" y="${cyv - 8}" font-size="10.5" text-anchor="end" fill="${col}" font-weight="700" ${halo}>${caret} ${b.current.toFixed(1)}x</text>`;
    s += `<text x="${x0}" y="${cy1 + 15}" font-size="8.5" fill="var(--ink-3)">${escapeHtml(yr(pts[0][0]))}</text>`;
    s += `<text x="${x1}" y="${cy1 + 15}" font-size="8.5" text-anchor="end" fill="var(--ink-3)">${escapeHtml(yr(pts[ci][0]))}</text>`;
    return s;
  };

  // no inline "Source:" caption — the Multiples source is already cited at the card level (range_position's
  // endnote → the tier's Sources list). Exhibits cite via endnotes, never a duplicate inline caption.
  return `<div class="ds-exhibit" style="margin:18px 0 16px;">
    <svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px; display:block;" role="img" aria-label="Valuation multiples vs their own trailing range">
      <text x="0" y="18" font-size="13" font-weight="600" fill="var(--ink)">Multiple vs its own trailing range</text>
      <text x="0" y="32" font-size="9.5" fill="var(--ink-3)">each quarter's close vs its trailing average &amp; range · log scale${bands[0].as_of ? " · as-of " + escapeHtml(bands[0].as_of) : ""}</text>
      ${bands.map((b, i) => panel(b, geo[i][0], geo[i][1])).join("")}
    </svg>
    ${anyLowConf ? `<div class="muted" style="font-size:10px; margin-top:2px;">* fewer than ${LOW_CONF_CLOSES} closes — low-confidence read; current shown in neutral, not red/green.</div>` : ""}
  </div>`;
}

function valuationCard(m) {
  const cross = (m.valuation && m.valuation.cross_sectional) ? fact("Valuation (vs peers)", m.valuation.cross_sectional) : "";
  const comp = (m.peer_comps && m.peer_comps.comparability) ? fact("Comparability", m.peer_comps.comparability) : "";
  const rng = (m.valuation && m.valuation.range_position && m.valuation.range_position.status === "present")
    ? fact("Own-history range", m.valuation.range_position) : "";
  const cna = (m.catalyst_path || {}).cross_name_anchor;   // the forward-multiple ladder across years
  const mladder = (cna && cna.status === "present") ? ladderTable(cna) : "";
  const iv = m.implied_valuation || {};
  let impl = "";
  if (iv.implied_equity && iv.implied_equity.status === "present" && Array.isArray(iv.implied_equity.value)) {
    const capOk = iv.market_cap && iv.market_cap.status === "present";
    const rows = iv.implied_equity.value.map((r) =>
      `<tr><td>${escapeHtml(r.basis)}</td><td class="num mono">${r.median != null ? fmtCap(r.median) : "—"}</td></tr>`).join("");
    impl = `<div style="margin-top:10px;"><div class="muted" style="font-size:11.5px; margin-bottom:4px;">Implied equity at the peer-median multiple — <b>reference, not a target</b> (the human sets the target); juxtapose vs market cap${capOk ? ` <span class="mono">${fmtCap(iv.market_cap.value)}</span>` : ""}, never difference.</div>
      <table class="data"><thead><tr><th>Basis</th><th class="num">Peer-median implied equity</th></tr></thead><tbody>${rows}</tbody></table>
      ${citeMark(iv.implied_equity.source_ref)}</div>`;
  }
  if (!cross && !comp && !rng && !mladder && !impl) return "";
  return `<div class="card ds-section"><div class="ds-title">Valuation <span class="muted" style="font-weight:400; text-transform:none; letter-spacing:0;">— multiples across years + cross-sectional; full detail in Analysis</span></div>${cross}${comp}${rng}${ownHistoryExhibit(m)}${mladder}${impl}</div>`;
}

// 7 — CATALYST & CONSENSUS: the forward/street view — consensus target + ratings, positioning
// (insider activity, short interest). Context for a NON-consensus read, never a machine driver/target;
// the full estimate-revision log lives in the Analysis catalyst path.
function catalystCard(m) {
  const cp = m.catalyst_path || {};
  const rows = [
    (cp.consensus_stats && cp.consensus_stats.status === "present") ? fact("Consensus (target · ratings)", cp.consensus_stats) : "",
    (cp.insider_activity && cp.insider_activity.status === "present") ? fact("Insider activity (6m)", cp.insider_activity) : "",
    (cp.short_interest && cp.short_interest.status === "present") ? fact("Short interest", cp.short_interest) : "",
  ].join("");
  if (!rows) return "";
  return `<div class="card ds-section"><div class="ds-title">Catalyst &amp; consensus <span class="muted" style="font-weight:400; text-transform:none; letter-spacing:0;">— the street's view; full revisions in Analysis</span></div>
    <div class="subtitle muted ds-sub" style="margin-bottom:8px;">The street's forward view — context for a non-consensus read, not a driver.</div>${rows}</div>`;
}

// 8 — VERIFY FIRST: only the decision-threatening caveats (the verdict slot lives in the teaser).
function verifyCard(d) {
  const vf = briefVerifyFirst(d.caveats || []);
  if (!vf.length) return "";
  return `<div class="card ds-section"><div class="ds-title">Verify first</div><div class="brief-verify">${vf.map(escapeHtml).join("; ")}</div></div>`;
}

// (D1/R3) drawdown cause + idiosyncrasy under ONE section header (matches the md) — what happened,
// and did it happen alone?
function drawdownIdio(m) {
  const dd = drawdownCause(m.drawdown_cause), io = idioVsShared(m.idiosyncratic_vs_shared);
  if (!dd && !io) return "";
  const divider = `<div class="ds-title" style="font-size:12px; margin-top:14px;">Did it happen alone? (idiosyncratic vs shared)</div>`;
  return sec("Drawdown cause & idiosyncrasy — what happened, and did it happen alone?",
    "The event(s) that broke the name, then whether it fell alone (idiosyncratic) or with its graph cohort.",
    dd + (io ? divider + io : ""));
}

// (E2) $M principal → "$25.0M" / "–"
// $M with en-US thousands separators, matching the Python render._musd (`f"${v:,.1f}M"`) so the
// web/PDF thousands grouping matches the .md for a $1B+ bucket total (e.g. "$1,234.5M").
const _mM = (v) => (v == null ? DASH : `$${Number(v).toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`);

// (E2) deterministic month-precision maturity wall from the structured instruments (mirrors
// render._maturity_wall_lines): matured-pre-reference / due this ref year / due later years / undated.
function maturityWall(cs, refDate) {
  const inst = cs.instruments;
  if (!inst || inst.status !== "present" || !Array.isArray(inst.value)) return "";
  // Bucket by the ISO date STRING (YYYY-MM-DD), NOT a local Date: `new Date("…T00:00:00")` is LOCAL
  // midnight, so getUTCFullYear() rolls a Jan-1 maturity back a year for any UTC-ahead viewer (IST,
  // Europe, Asia) — mis-bucketing "2027-01-01" into "≤12m 2026". ISO strings compare
  // lexicographically = chronologically, timezone-free, and match the Python (date.year).
  const refYear = String(refDate).slice(0, 4);
  const matured = [], thisYear = [], later = [], undated = [];
  for (const i of inst.value) {
    if (!i.maturity_date) { undated.push(i); continue; }
    const m = i.maturity_date;
    (m < refDate ? matured : m.slice(0, 4) === refYear ? thisYear : later).push([m, i]);
  }
  const sum = (xs) => xs.reduce((a, x) => a + ((Array.isArray(x) ? x[1] : x).principal_musd || 0), 0);
  const li = [];
  if (matured.length) {
    li.push(`<li><b>matured (pre-reference): ${_mM(sum(matured))}</b> — resolution not in this data; verify each against its 8-K (never assume repaid/defaulted):<ul>` +
      matured.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0)).map(([m, i]) => `<li>${i.maturity_date}: ${_mM(i.principal_musd)} ${escapeHtml(i.description.slice(0, 34))}</li>`).join("") + "</ul></li>");
  }
  if (thisYear.length) li.push(`<li>due ≤12m (through ${refYear}): ${_mM(sum(thisYear))} — ${thisYear.map(([m, i]) => `${i.maturity_date} ${_mM(i.principal_musd)}`).join(", ")}</li>`);
  const byYr = {};
  for (const [m, i] of later) (byYr[m.slice(0, 4)] ||= []).push([m, i]);
  for (const yr of Object.keys(byYr).sort()) li.push(`<li>due ${yr}: ${_mM(sum(byYr[yr]))}</li>`);
  if (undated.length) li.push(`<li>undated (floor — no panel maturity): ${_mM(sum(undated))} — ${undated.map((i) => `${escapeHtml(i.description.slice(0, 26))} ${_mM(i.principal_musd)}`).join(", ")}</li>`);
  li.push(`<li class="muted"><i>reconciliation: itemized ${_mM(sum(inst.value))} (panel ${escapeHtml(cs.detail_as_of || "")}) vs the latest-quarter aggregates below — the gap is unitemized / newer term loans.</i></li>`);
  return `<div class="fact"><div class="fact-label">Maturity wall (deterministic, vs ${escapeHtml(refDate)})</div><ul class="kv-list">${li.join("")}</ul></div>`;
}

// (E1/E2) instrument columns + one instrument → a {label, cells} row (mirrors render._CS_COLS /
// _instrument_row); the description is the row LABEL, Principal is right-aligned by dataTable's .num.
const _CS_COLS = ["Type", "Principal", "Coupon", "Floating", "Maturity", "Sec", "Conv", "Cur"];
const instrumentRow = (i) => ({
  label: i.description,
  cells: [i.type, _mM(i.principal_musd), i.coupon || DASH, i.floating_rate || DASH,
    i.maturity_date || "undated", i.secured ? "Y" : "N", i.convertible ? "Y" : "N", i.currency],
});

// (K1, mirrors covenant_extract._CONV_RATE_RE / _derive_conversion) a best-effort $/share from a
// stated conversion rate "N shares … per $D" → $D ÷ N (D is the CAPTURED denomination — $1.00 or the
// $1,000 bond convention — never assumed). "" when the rate isn't cleanly stated (the clause then
// carries it) — never a fabricated or mis-scaled number.
const _CONV_RATE_RE = /(?<![\d,.])\(?(\d{1,4}(?:\.\d+)?)\)?\s*shares?\b[^;]{0,80}?per\s*\$?\s*(1\.00|1,000|1000|100|1)(?![\d.,])/i;
function _deriveConversion(value) {
  const m = String(value).match(_CONV_RATE_RE);
  if (!m) return "";
  const rate = Number(m[1]), denom = Number(m[2].replace(/,/g, ""));
  if (!(rate > 0) || !(denom > 0)) return "";
  return ` (⇒ ~$${(denom / rate).toFixed(2)}/sh at ${m[1]} sh per $${m[2]})`;
}

// (K1) governing-term key → short label for the curated main-body covenant line (survival-critical
// only). Mirrors render._SUMMARY_TERMS — matched against g.term.toLowerCase().
const _SUMMARY_TERMS = [
  ["financial-maintenance", "Financial maintenance"], ["conversion", "Conversion"],
  ["interest", "Interest / coupon"], ["maturity date", "Maturity"],
  ["mandatory prepayment", "Events of default"],
];
const _MONTHS_RE = "(?:January|February|March|April|May|June|July|August|September|October|November|December)";
const _DATE_RE_SRC = `(?:${_MONTHS_RE})\\s+\\d{1,2},\\s+\\d{4}|\\d{4}-\\d{2}-\\d{2}`;
const _CADENCE = { week: "weekly", month: "monthly", quarter: "quarterly", day: "daily", year: "annually" };

// (RC-1.5d, mirrors render._clause_numbers / _num_in_clause / _fmt_bps) the consistency-guard helpers:
// every number stated in the clause (thousands-commas stripped), a format-tolerant membership test
// (3.0 matches "3.00"), and a bps value AS DISCLOSED (integer when whole; never normalized to pct).
function clauseNumbers(raw) {
  return (String(raw).replace(/,/g, "").match(/\d+(?:\.\d+)?/g) || []).map(Number);
}
function numInClause(v, nums) { return nums.some((n) => Math.abs(v - n) < 1e-6); }
function fmtBps(v) { return v === Math.trunc(v) ? String(Math.trunc(v)) : String(v); }
// (RC-1.5d, mirrors render._fmt_pct) a percent component AS DISCLOSED — the value's EXACT shortest
// decimal, padded to a MINIMUM of 2 decimals (3.0→"3.00", 6.125→"6.125"). NEVER toFixed(2): that
// mis-rounds an eighth-of-a-point coupon (6.125→"6.13") AND diverges from Python's :.2f ("6.12") —
// the H2 mirror-drift hazard. Shortest round-trip repr keeps py↔js byte-identical.
// Named fmtPctExact (NOT fmtPct): lib/format.js already exports a SIGNED-DISPLAY fmtPct this module
// imports at the top — two names, two semantics (exact coupon repr vs signed % display), never merged.
function fmtPctExact(v) {
  const s = String(v);
  const dot = s.indexOf(".");
  const intpart = dot < 0 ? s : s.slice(0, dot);
  let frac = dot < 0 ? "" : s.slice(dot + 1);
  frac = frac.length <= 2 ? (frac + "00").slice(0, 2) : frac;
  return `${intpart}.${frac}`;
}

// (RC-1.5d, mirrors render._compose_interest_lead) the interest value-lead COMPOSED FROM STRUCTURE —
// never re-parsed from the clause. Returns [lead, qa]: the composed lead (e.g.
// "Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK)") or "" when components are absent/incomplete, plus a
// QA note when the consistency guard tripped (else ""). REQUIRED: baseRateLabel + exactly one of
// marginPct/marginBps; floorPct/pikPct optional. GUARD: each numeric's digits must appear in the
// parent clause; a mismatch OR both margins present ⇒ no lead + QA (a slip must never headline the
// row). Units render AS DISCLOSED (bps stays bps). term == null (pre-RC-1.5d JSON) ⇒ no lead, no crash.
function composeInterestLead(term, raw) {
  if (!term) return ["", ""];
  const base = (term.baseRateLabel || "").trim();
  const mPct = term.marginPct, mBps = term.marginBps;
  if (!base || (mPct == null && mBps == null)) return ["", ""];  // required components absent → clause
  if (mPct != null && mBps != null)
    return ["", "both a percent and a bps margin given — ambiguous, lead suppressed"];
  const nums = clauseNumbers(raw);
  for (const comp of [mPct, mBps, term.floorPct, term.pikPct]) {
    if (comp == null) continue;
    if (!Number.isFinite(comp))  // defence-in-depth: a non-finite never headlines, never crashes
      return ["", "a rate component is not a finite number — lead suppressed"];
    if (!numInClause(comp, nums))
      return ["", `rate component ${fmtBps(comp)} not stated in the clause — lead suppressed`];
  }
  const margin = mPct != null ? `${fmtPctExact(mPct)}%` : `${fmtBps(mBps)} bps`;
  const extras = [
    term.floorPct != null ? `Floor ${fmtPctExact(term.floorPct)}%` : "",
    term.pikPct != null ? `+${fmtPctExact(term.pikPct)}% PIK` : ""].filter(Boolean);
  const lead = `${base} + ${margin}` + (extras.length ? ` (${extras.join(", ")})` : "");
  return [lead, ""];
}

// (K1, mirrors render._covenant_value_lead) the extractable VALUE a curated covenant line LEADS with,
// before the ≤120c clip — RIGHT or ABSENT, never wrong. The interest lead is COMPOSED FROM the term's
// structured rate components (RC-1.5d) — no clause re-parse; the other branches stay ANCHORED on the
// verbatim clause so ambiguous prose yields "" and the clause alone carries it. NEVER fabricates.
function covenantValueLead(label, raw, term) {
  if (label === "Conversion") return _deriveConversion(raw).trim().replace(/^\(/, "").replace(/\)$/, "");
  if (label === "Financial maintenance") {
    const thr = raw.match(/not less than\s+\$[\d,]*\d(?:\.\d+)?/);  // end on a digit (no trailing ,)
    if (!thr) return "";
    // cadence ONLY when anchored to the TEST ("as of/tested … each <unit>") — not a forecast
    const cad = raw.match(/(?:as of|tested)\b[^.;]{0,40}?\beach\s+(?:calendar\s+|fiscal\s+)?(week|month|quarter|day|year)/i);
    return `${thr[0]} ${cad ? (_CADENCE[cad[1].toLowerCase()] || "") : ""}`.trim();
  }
  if (label === "Interest / coupon") return composeInterestLead(term, raw)[0];  // composed from structure
  if (label === "Maturity") {
    const repl = raw.match(new RegExp(`replaced with[^.;]*?(${_DATE_RE_SRC})`, "i"));  // amendment wins
    const anch = raw.match(new RegExp(`(?:maturity\\s*date|matur\\w+)[^.;]{0,40}?(${_DATE_RE_SRC})`, "i"));  // else a maturity-anchored date, not a random first date
    const m = repl || anch || raw.match(new RegExp(_DATE_RE_SRC));  // else first date (case-sensitive on months)
    return m ? (repl || anch ? m[1] : m[0]) : "";
  }
  if (label === "Events of default") {
    const nums = new Set([...raw.matchAll(/(?<![\$\d.])\b(\d{1,2})\.\s/g)].map((x) => Number(x[1])));  // contiguous 1..k
    let k = 0;
    while (nums.has(k + 1)) k += 1;  // a section number / dollar figure can't inflate the count
    const acc = /acceler/i.test(raw) ? "acceleration" : "";
    return [k >= 2 ? `${k} enumerated` : "", acc].filter(Boolean).join("; ");
  }
  return "";
}

// (K1, mirrors render._clip120) collapse whitespace + clip a verbatim clause to ≤120 chars for the
// curated main body — the full verbatim lives in the appendix table + JSON.
function clip120(s) {
  s = String(s).replace(/\s+/g, " ").trim();
  return s.length <= 120 ? s : s.slice(0, 119).replace(/\s+$/, "") + "…";
}

// (T2, mirrors render._clip) collapse whitespace + clip a verbatim clause to ≤n chars (… when cut).
// Returns [clipped, trimmed] — the caller appends a "full verbatim in JSON" note ONLY when trimmed.
function clipTrim(s, n) {
  s = String(s).replace(/\s+/g, " ").trim();
  return s.length <= n ? [s, false] : [s.slice(0, n - 1).replace(/\s+$/, "") + "…", true];
}

// (K1, mirrors render._covenant_summary_lines) CURATED covenant summary for the MAIN body — the
// governing VALUES that drive survival (financial-maintenance / conversion / interest / maturity /
// a 1-line events-of-default), each leading with its extractable value then a ≤120-char clause.
// Debt families only — the RSU/equity-incentive family is appendix-only. Returns "" when there are no
// governing rows (the appendix carries the full detail). Mirrors the per-family grouping in the md.
function covenantSummary(cs) {
  const rs = cs.covenant_term_rows;
  if (!rs || rs.status !== "present" || !Array.isArray(rs.value) || !rs.value.length) return "";
  const ptrs = cs.covenant_pointer_rows;
  const gov = governingTerms(rs.value, (ptrs && ptrs.value) || []);
  const fams = [];
  for (const g of gov) {
    const fl = (g.fam || "").toLowerCase();
    if (fl.includes("material contract") || fl.includes("incentive")) continue;  // RSU exhibit → appendix-only
    if (!fams.includes(g.fam)) fams.push(g.fam);
  }
  let out = "";
  for (const fam of fams) {
    const parts = [];
    for (const g of gov.filter((t) => t.fam === fam)) {
      const v = g.value || {};
      if (v.status !== "present") continue;
      const entry = _SUMMARY_TERMS.find(([key]) => (g.term || "").toLowerCase().includes(key));
      if (!entry) continue;
      const label = entry[1];
      const raw = String(v.value);
      const lead = covenantValueLead(label, raw, g);  // (K1) lead with the extractable value
      const clause = lead ? `${lead} · ${clip120(raw)}` : clip120(raw);
      parts.push(`<li><b>${escapeHtml(label)}:</b> ${escapeHtml(clause)}</li>`);
    }
    if (parts.length) {
      out += `<div class="fact"><div class="fact-label">Covenants — ${escapeHtml(fam)} ` +
        `<span class="muted">(governing values; full verbatim in appendix)</span></div>` +
        `<ul class="kv-list">${parts.join("")}</ul></div>`;
    }
  }
  return out;
}

// (E1/E2 · K1) capital structure — MAIN body (CURATED): the live near-dated tranches (maturity year
// ≤ refYear+1) with their economics, the month-precision wall + reconciliation, the QoQ aggregates,
// the maturity-resolution verbatim, and the curated covenant-values summary. The full instrument
// panel, the 8-K/covenant pointer tables, and the full per-family covenant tables move to the
// appendix (capitalStructureAppendix). Mirrors render._capital_structure_lines.
function capitalStructureInner(cs, refDate) {
  const inst = cs.instruments;
  let table = fact("Capital structure (instruments)", inst);
  if (inst && inst.status === "present" && Array.isArray(inst.value)) {
    // (K1) near-dated = maturity year ≤ refYear+1 (mirrors render._near_dated); undated → appendix.
    const refYearNext = Number(String(refDate).slice(0, 4)) + 1;
    const near = inst.value.filter((i) => i.maturity_date && Number(i.maturity_date.slice(0, 4)) <= refYearNext);
    const moved = inst.value.length - near.length;
    const note = moved ? `${moved} undated / later aggregate line item(s) in the appendix panel` : "";
    table = dataTable(`Live instruments — near-dated (≤12m + ${refYearNext}) — panel ${cs.detail_as_of || ""}`,
      inst.source_ref, _CS_COLS, near.map(instrumentRow), note);
  }
  // (P3) the verbatim maturity-resolution event, when captured (a pre-P3 JSON has no field → nothing)
  const matEv = cs.maturity_event && (cs.maturity_event.status !== "present" || cs.maturity_event.value)
    ? fact("Maturity resolution (8-K verbatim)", cs.maturity_event) : "";
  return subhead("Capital structure & maturity wall") +
    table + maturityWall(cs, refDate) +
    fact("Aggregates (latest quarter)", cs.summary) + matEv +
    covenantSummary(cs);  // (K1) curated per-family survival covenant VALUES; "" → appendix carries it
}

// (K1, mirrors render._capital_structure_appendix_lines) capital-structure PROVENANCE for the
// appendix: the FULL instrument panel (incl. undated line items), the 8-K maturity-filing pointers,
// the covenant/contract pointer table, and the full per-family governing covenant tables. Nothing is
// deleted from the surface — relocated here + kept in JSON. Always renders (render_markdown guards on
// capital_structure existing); the 8-K/pointer/covenant facts are UNKNOWN-safe.
function capitalStructureAppendix(cs) {
  const inst = cs.instruments;
  // (audit C1) NO instruments-empty early-return — the 8-K/pointer/covenant flat facts below are
  // UNKNOWN-safe and always render, so relocated facts are never dropped when the panel is empty.
  let panel = "";
  if (inst && inst.status === "present" && Array.isArray(inst.value)) {
    panel = dataTable(`Capital structure — full instrument panel ${cs.detail_as_of || ""}`,
      inst.source_ref, _CS_COLS, inst.value.map(instrumentRow), "");
  }
  const inner = panel +
    fact("8-Ks at instrument maturities", cs.maturity_filings) +
    covenantPointers(cs) +
    covenantTerms(cs);
  // (T1) the ON-DEMAND / audit tier: web collapses the provenance in a <details> that print excludes
  // (styles.css @media print: details:not([open]){display:none}); the JSON stays machine-complete.
  // Nothing deleted — the panel/pointers/terms are relocated here, not dropped. Mirrors the md marker
  // in render._capital_structure_appendix_lines.
  return auditCitesInline(`<details class="card ds-section">
    <summary style="cursor:pointer; font-size:12.5px; font-weight:600; color:var(--ink-2);">Capital-structure provenance — on-demand (audit) <span class="muted" style="font-weight:400;">— full panel · pointers · terms (web collapsed · print-excluded · JSON)</span></summary>
    <div style="margin-top:10px;">${inner}</div></details>`);
}

// (H1) covenant/contract pointers → table (CIK-verified execution filings); old JSON → flat fact.
function covenantPointers(cs) {
  const rs = cs.covenant_pointer_rows;
  if (!rs || rs.status !== "present" || !Array.isArray(rs.value) || !rs.value.length)
    return fact("Covenant exhibit pointers", cs.covenant_pointers);
  const rows = rs.value.map((r) => ({
    label: r.family,
    cells: [r.filing, r.filing_date || "—",
      r.accession ? `${r.accession} — ${(r.exhibits || []).slice(0, 3).join(", ")}` : r.note],
  }));
  return dataTable("Covenant / contract pointers (CIK-verified execution filings)", rs.source_ref,
    ["Filing", "Date", "Accession / exhibit (or note)"], rows, "");
}

// (P5, mirrors covenant_extract.governing_terms) collapse per-exhibit rows to ONE governing value
// per (family, term): the latest-dated PRESENT value wins (amendment over base), base ref + an
// "amended by" chain; grouped by family via the pointers' accession→(family, date) map.
const _accOf = (s) => { const m = (s || "").match(/\b(\d{10}-\d{2}-\d{6})\b/); return m ? m[1] : ""; };
function governingTerms(rows, pointers) {
  const meta = {};
  (pointers || []).forEach((p) => { if (p.accession) meta[p.accession] = [p.family, p.filing_date || ""]; });
  const grouped = new Map(), order = [];
  (rows || []).forEach((r) => {
    const v = r.value || {};
    const [fam, dt] = meta[_accOf(v.source_ref) || _accOf(v.note)] || ["(unmapped)", ""];
    const key = fam + " " + r.name;
    if (!grouped.has(key)) { grouped.set(key, { fam, term: r.name, list: [] }); order.push(key); }
    grouped.get(key).list.push([dt, r]);  // (RC-1.5d) store the whole row — components ride along
  });
  return order.map((key) => {
    const { fam, term, list } = grouped.get(key);
    list.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));  // oldest → newest
    const present = list.filter(([, r]) => (r.value || {}).status === "present");
    let govRow, baseRef, amendedBy;
    if (present.length) {
      // (X-4) assert amendedBy only on a REAL chronology (distinct, non-empty dates); tied/empty
      // dates can't establish supersession — don't fabricate the chain from input order (py parity).
      const pdates = present.map(([dt]) => dt);
      const ordered = pdates.every(Boolean) && new Set(pdates).size === pdates.length;
      govRow = present[present.length - 1][1];  // latest PRESENT governs — components ride along
      baseRef = present[0][1].value.source_ref;
      amendedBy = ordered ? present.slice(1).map(([, r]) => _accOf(r.value.source_ref)).filter(Boolean) : [];
    } else {
      govRow = list[list.length - 1][1];
      baseRef = null; amendedBy = [];
    }
    return { fam, term, value: govRow.value, baseRef, amendedBy,
      baseRateLabel: govRow.base_rate_label ?? null, marginPct: govRow.margin_pct ?? null,
      marginBps: govRow.margin_bps ?? null, floorPct: govRow.floor_pct ?? null,
      pikPct: govRow.pik_pct ?? null };
  });
}

// (P5/E5) fenced Tier-2 covenant terms, TERM-GOVERNED → ONE table per family, each term collapsed to
// its GOVERNING value (amendment over base), source citing the base § + "amended by". No UNKNOWN row
// above a present answer. Old JSON (no rows) → flat fact.
function covenantTerms(cs) {
  const rs = cs.covenant_term_rows;
  if (!rs || rs.status !== "present" || !Array.isArray(rs.value) || !rs.value.length)
    return fact("Covenant terms (from the filed agreement)", cs.covenant_terms);
  const ptrs = cs.covenant_pointer_rows;
  const gov = governingTerms(rs.value, (ptrs && ptrs.value) || []);
  if (!gov.length) return fact("Covenant terms (from the filed agreement)", cs.covenant_terms);
  const families = [];
  gov.forEach((g) => { if (!families.includes(g.fam)) families.push(g.fam); });
  const cols = ["Governing value (lead · clause ≤200c)", "Source §"];
  const tables = families.map((fam) => {
    const famTerms = gov.filter((g) => g.fam === fam);
    // (T2) the family source lineage moves to the table FOOTER, not repeated on every row: the base
    // accession/exhibit + the amendment-accession chain (mirrors render._covenant_term_lines footer).
    const presentBases = famTerms
      .filter((g) => (g.value || {}).status === "present" && g.baseRef).map((g) => g.baseRef);
    const famBase = presentBases.length ? presentBases[0] : rs.source_ref;
    const amendAccs = [...new Set(famTerms.flatMap((g) => g.amendedBy))].sort();
    const footer = `Source §: ${famBase}` + (amendAccs.length ? ` · amended by ${amendAccs.join(", ")}` : "");
    const rows = famTerms.map((g) => {
      const v = g.value || {};
      if (v.status !== "present") return { label: g.term, cells: ["UNKNOWN", v.note || "not stated"] };
      // (T2) value = the extractable value-lead + a ≤200c clause; "full verbatim in JSON" only when trimmed.
      const entry = _SUMMARY_TERMS.find(([key]) => (g.term || "").toLowerCase().includes(key));
      const verbatim = String(v.value);
      // (RC-1.5d) the interest lead composes from structure and carries a QA note when the
      // consistency guard trips; the QA note is an audit-tier annotation (this table is on-demand).
      let lead, qa;
      if (entry && entry[1] === "Interest / coupon") { [lead, qa] = composeInterestLead(g, verbatim); }
      else { lead = entry ? covenantValueLead(entry[1], verbatim, g) : ""; qa = ""; }
      const [clause, trimmed] = clipTrim(verbatim, 200);
      const cell = (lead ? `${lead} · ${clause}` : clause) + (trimmed ? " — full verbatim in JSON" : "")
        + (qa ? ` — ⚠ QA: ${qa}` : "");
      // source §: an off-family base (≠ the family footer) annotates inline; an amended row keeps its
      // amendment ref; a plain base row points at the footer.
      const ref = (g.baseRef && g.baseRef !== famBase) ? g.baseRef
        : g.amendedBy.length ? `amended by ${g.amendedBy.join(", ")}` : "base (footer)";
      return { label: g.term, cells: [cell, ref] };
    });
    return dataTable(`Covenant terms — ${fam} (governing agreement)`, rs.source_ref, cols, rows, footer);
  }).join("");
  // (FIX-2 · D-1) mirror the Python transparency line — located pointer accessions minus the ones
  // the extraction actually read → "N located agreement exhibit(s) not extracted this run". Without
  // it the web view silently drops a covenant-completeness signal the .md/PDF shows (py↔js parity).
  const located = new Set(((ptrs && ptrs.value) || []).map((p) => p.accession).filter(Boolean));
  const extracted = new Set(rs.value
    .map((r) => _accOf((r.value && (r.value.source_ref || r.value.note)) || "")).filter(Boolean));
  const missing = [...located].filter((a) => !extracted.has(a)).sort();
  const note = missing.length
    ? `<div class="muted" style="font-size:11.5px; margin-top:4px;"><i>${missing.length} located ` +
      `agreement exhibit(s) not extracted this run (cost bound / fetch fail) — see the pointer ` +
      `table: ${escapeHtml(missing.join(", "))}</i></div>`
    : "";
  return tables + note;
}

// (D1) leverage & survival — the survival story in one place (+ FCF + capital structure). Falls back
// to the pre-B2 Quality leverage lines + the flat liquidity string for an old dossier.json.
// (P7) ONE Survival section clubbing the three fragments: leverage ratios · cash/FCF · instruments +
// wall + covenant pointers/terms. leverageBlock/capitalStructureInner return INNER content (no card).
function leverageSurvival(m, refDate) {
  const q = m.quality || {};
  const leverage = m.leverage_survival ? leverageBlock(m) : (
    fact("Net debt / EBITDA (GAAP)", q.net_debt_to_ebitda, mult) +
    fact("Net debt / OCF", q.net_debt_to_ocf, mult) +
    fact("Net debt / EBITDA (covenant adj.)", q.net_debt_to_ebitda_adjusted) +
    fact("Survival capacity", q.survival_capacity) +
    fact("Interest coverage", q.interest_coverage, mult));
  const cash = subhead("Cash & liquidity — self-funding, the survival input") +
    fact("FCF sign", q.fcf_sign, signWord) + fact("Free cash flow ($M)", q.free_cash_flow) +
    (m.capital_structure ? "" : fact("Liquidity / covenant flags", q.liquidity_covenant_flags));
  const capital = m.capital_structure ? capitalStructureInner(m.capital_structure, refDate) : "";
  return sec("Survival — leverage · cash/FCF · capital structure & maturity wall",
    "One block: the leverage bases, self-funding, the month-precision wall, and the covenant "
    + "pointers/terms.", leverage + cash + capital);
}

// (D2/D1) trajectory — the merged table + the share-count trend.
// (Phase-3) ROIC (return on capital) trend — a dependency-free line of the per-period ROIC, from the
// STRUCTURED roic_trend series (never re-parsing the trajectory string). Values are fractions → ×100
// for the % display. Zero baseline when the series crosses zero (a distressed name). Fail-honest:
// no structured series → no chart (the trajectory table still renders).
function trajectorySection(q) {
  if (!q) return "";
  // (P4) the ROIC-trend CHART was removed — its RoCE-over-time is the return-ratios exhibit's RoCE line
  // (Financial Snapshot), a strict duplicate. ROIC stays as a row in the trajectory table below; the
  // structured q.roic_trend series stays in the JSON (machine-complete), just no longer charted here.
  return sec("Trajectory", "Revenue · EBITDA · margins · ROIC per period; the same-quarter YoY footnoted.",
    trajectoryTable(q) + fact("Share-count trend", q.share_count_trend));
}

// (D1) verdict footer — the no-BUY/AVOID reminder closes the document (caveats opened it).
function verdictFooter() {
  return `<div class="card ds-section" style="text-align:center; color:var(--ink-2); font-size:12.5px;">
    <b>No BUY/AVOID here — this dossier only assembles and cites.</b> The verdict is the human's,
    logged separately via the ledger with a frozen entry price.</div>`;
}

function header(d) {
  return `<div class="header-block ds-header">
    <div class="ds-header-main">
      <h1 class="page-h"><span class="mono">${escapeHtml(d.ticker)}</span> · ${escapeHtml(d.name || "")}</h1>
      <div class="ds-meta">Assembled facts, <b>no verdict</b> · data as of <span class="mono">${fmtDate(d.reference_date)}</span> · assembled <span class="mono">${fmtStamp(d.assembled_at)}</span>${d.synthesis ? ` · synthesis <span class="mono">${escapeHtml(d.llm_model || "llm")}</span>` : " · mechanical layer only"}</div>
    </div>
    <div class="ds-pdf-wrap">
      <button id="ds-pdf" class="ds-pdf-btn" type="button" aria-haspopup="true" aria-expanded="false"
        title="Export to PDF — opens your browser's print dialog; choose &ldquo;Save as PDF&rdquo;.">&#x2913; Download PDF &#x25be;</button>
      <div class="ds-pdf-menu" id="ds-pdf-menu" role="menu" hidden>
        <button type="button" data-scope="brief" role="menuitem">Brief <span class="muted">· first cut</span></button>
        <button type="button" data-scope="full" role="menuitem">Full dossier <span class="muted">· all tiers</span></button>
      </div>
    </div>
  </div>`;
}

// (D4) a guardrail caveat is "Lead (a bull point): '<full claim>' — <explanation>". Parse it into the
// what / where / why-it-matters / how-to-verify shape (offending sentence IN FULL). A mechanical /
// 'pull CIQ …' caveat is already a complete advisory → one full-sentence bullet.
const _CAVEAT_RE = /^(.*?)\(([^)]*?\bpoint[^)]*?)\):\s*'([\s\S]*?)'\s*—\s*([\s\S]*)$/;
function caveatBlock(f) {
  const resolved = /^RESOLVED\b/i.test(f);
  const icon = resolved ? "✓" : "⚠";
  const m = f.match(_CAVEAT_RE);
  if (!m) {
    return `<div class="flag ${resolved ? "resolved" : "open"}"><span class="fi">${icon}</span><span>${escapeHtml(f)}</span></div>`;
  }
  const why = m[4].trim(); const i = why.lastIndexOf("; ");
  const whyText = i >= 0 ? why.slice(0, i).trim() : why;
  const how = i >= 0 ? why.slice(i + 2).trim() : "";
  return `<div class="flag open"><span class="fi">${icon}</span><span>
    <b>${escapeHtml(m[1].trim())}</b> — ${escapeHtml(m[3].trim())}
    <div class="muted" style="font-size:11.5px; margin-top:3px;"><i>where:</i> ${escapeHtml(m[2].trim())}</div>
    <div class="muted" style="font-size:11.5px;"><i>why it matters:</i> ${escapeHtml(whyText)}</div>
    ${how ? `<div class="muted" style="font-size:11.5px;"><i>how to verify:</i> ${escapeHtml(how)}</div>` : ""}
  </span></div>`;
}

function flagsSection(caveats) {
  // Decision caveats only (d.caveats) — the machine-QA self-checks live in d.qa_flags (dev/JSON),
  // deliberately kept out of this human view, matching the PDF/markdown render. (D4) each renders in
  // the what/where/why/how-to-verify shape, the offending sentence IN FULL.
  if (!caveats.length) return "";
  const rows = caveats.map(caveatBlock).join("");
  return `<div class="card ds-section"><div class="ds-title">Analyst caveats — verify before the verdict</div>
    <div class="subtitle muted ds-sub">Open caveats (⚠) need a human check before the verdict; they are not conclusions.</div>${rows}</div>`;
}

// (G) implied expectations — price-inverted, multiples-space. Mirrors the md: each stated multiple
// → the fundamental level price implies (TEV ÷ multiple); consensus anchors juxtaposed, NEVER
// differenced (no %, gap, upside, or implied price/equity). "" for a pre-G dossier.json.
function impliedExpectations(ie) {
  if (!ie) return "";
  // label (the multiple's name) + one cell PER column: dataTable prepends a blank <th> for the
  // label, so cells.length must equal cols.length (here 2: multiple, implied level).
  const rows = (ie.rows || []).map((r) => ({
    label: r.label,
    cls: r.is_identity ? "name" : "",
    cells: [
      r.multiple != null ? Number(r.multiple) + "×" : "NM",
      r.implied_level != null
        ? `$${Number(r.implied_level).toFixed(1)}M ${r.metric}${r.is_identity ? " †" : ""}`
        : `UNKNOWN — ${r.note || ""}`,
    ],
  }));
  const intro = `<div class="fact"><div class="fact-label">What the current price implies (at stated multiples)</div>
    <div style="min-width:0;"><div class="muted" style="font-size:12px;">${escapeHtml(gateShortref(ie.heterogeneity_gate || ""))}</div>
    <div class="muted" style="font-size:11px; margin-top:4px;">price-implied fundamental levels at stated multiples — the human judges earned vs residual; identity (†): at the name's own multiple the implied level IS consensus.</div>
    <div class="muted" style="font-size:11px;">TEV as-of ${escapeHtml(ie.tev_as_of || "")} · multiples as-of ${escapeHtml(ie.multiples_as_of || "")}</div></div></div>`;  // (K4) human-facing rename
  const table = dataTable("Price-implied levels (at each stated multiple)", ie.tev && ie.tev.source_ref,
    ["Multiple (× used)", "Implied level"], rows, "");  // (K5) renamed
  // (K4) reads-against line — juxtapose vs consensus, never subtract (avoids %/upside/gap/discount).
  const readsAgainst = `<div class="muted" style="font-size:11px; margin-top:4px;">Reads AGAINST the consensus path anchors below — juxtapose the price-implied level vs consensus per metric; never subtract one from the other.</div>`;
  // the parallel REVENUE anchors substantiate the TEV/Rev name-row identity (†); only when present.
  const revAnchors = (ie.rev_anchors && ie.rev_anchors.value)
    ? `<div style="margin-top:4px;"><b>Consensus path anchors (Revenue — juxtapose, do NOT difference):</b> ${escapeHtml(ie.rev_anchors.value)}</div>` : "";
  // (audit) H7 EBITDA anchors can be UNKNOWN (Trends may lack FY26/FY27) — show the note, not blank.
  const anchorsTxt = (ie.anchors && ie.anchors.value) || (ie.anchors && ie.anchors.note) || "n/a";
  const anchors = `<div class="fact"><div class="fact-label">Consensus path anchors (EBITDA — juxtapose, do NOT difference)</div>
    <div style="min-width:0;">${escapeHtml(anchorsTxt)}${revAnchors}
    <div class="muted" style="font-size:11px; margin-top:4px;">${ie.vintage_coherent ? "" : "⚠ "}${escapeHtml(ie.coherence_note || "")}</div>
    ${ie.net_debt_reconciled ? "" : `<div class="muted" style="font-size:11px;">⚠ net-debt input disagrees with the cash/debt bridge — see the TEV source</div>`}
    <div class="muted" style="font-size:11px;">Fixed multiple set (declared in code, no per-name curation): name NTM + peer-median NTM/LTM, on TEV/EBITDA and TEV/Rev.</div></div></div>`;
  return intro + table + readsAgainst + anchors;  // (K4) reads-against between the table and the anchors
}

function valuation(v) {
  if (!v) return "";
  // Mirrors the md render (PR #48): lead with the CROSS-SECTIONAL read (the edge); the own-history
  // percentile barely discriminates across finalists, so it's folded into the range line below.
  // (G) implied expectations slot in AFTER cross-sectional, BEFORE the own-history reads.
  return sec("Valuation", "Cross-sectional vs peers (the edge); own-history range as secondary context.",
    fact("Cross-sectional (vs peers — the edge)", v.cross_sectional, null, { hi: true }) +
    impliedExpectations(v.implied_expectations) +
    fact("P/E", v.pe, (x) => escapeHtml(Number(x).toFixed(1)) + "&times;") +
    fact("EV/EBITDA (TEV/LTM, GAAP)", v.ev_ebitda, mult) +
    fact("EV/adj-EBITDA (forward)", v.ev_ebitda_adjusted_fwd) +
    fact("Adjusted EPS (guide)", v.adjusted_eps) +
    fact("Own-history range position", v.range_position, null, { hi: true }));
}

// (D1/D2) `quality` split into leverageSurvival + trajectorySection (see renderDossier); the two
// seriesTable calls merged into trajectoryTable. `seriesTable` is retained (catalyst path uses it).

function concentration(c) {
  if (!c) return "";
  return sec("Concentration", "Segment / customer / geographic exposure. Segment-EBITDA share is the decision-relevant profit view.",
    fact("Segments (revenue share)", c.segments) +
    fact("Segment EBITDA share", c.segment_ebitda, null, { hi: true }) +
    fact("Customers", c.customers) +
    fact("Geographic", c.geographic));
}

// --- peer comps → scannable tables. The mechanical layer encodes these as deterministic composite
// strings; we parse each into a grid, EXACTLY like seriesTable — anything that doesn't parse falls
// back to the plain-text fact() (never breaks, never alters a value). The NAME column is a FOCAL
// highlight, not a verdict; the deltas carry NO better/worse colour because the earned-vs-residual
// call is the human's, not the UI's. Comparability stays prose (a narrative gate, not a grid).
// B.1: the legacy peerFactTable + PC_NAME/PC_PEER are deleted — the peer roster/multiples/deltas
// now route through the ONE shared dataTable (parsers below just build the rows).

function parsePeerMultiples(text) {
  let s = String(text).trim(), note = "";
  const nm = s.match(/\s*\[([^\]]*)\]\s*$/);
  if (nm) { note = nm[1]; s = s.slice(0, nm.index).trim(); }
  const rows = [];
  for (const seg of s.split(";")) {
    const t = seg.trim();
    if (!t) continue;
    const m = t.match(/^(.+?):\s*name\s+(\S+)\s+vs peers\s+Low\s+(\S+)\s*\/\s*Median\s+(\S+)\s*\/\s*Mean\s+(\S+)\s*\/\s*High\s+(\S+)$/i);
    if (!m) return null;  // any segment off-format → bail to the plain-text fallback
    rows.push({ metric: m[1].trim(), name: m[2], low: m[3], median: m[4], mean: m[5], high: m[6] });
  }
  return rows.length ? { rows, note } : null;
}

function peerMultiplesFact(label, s) {
  if (!s || s.status !== "present" || s.value == null) return fact(label, s);
  const p = parsePeerMultiples(s.value);
  if (!p) return fact(label, s);
  const rows = p.rows.map((r) => ({ label: r.metric, cells: [r.name, r.low, r.median, r.mean, r.high] }));
  return dataTable(label, s.source_ref, ["Name", "Low", "Median", "Mean", "High"], rows, p.note || "");
}

function parsePeerDeltas(text) {
  let s = String(text).trim(), note = "";
  const nm = s.match(/\s*\[([^\]]*)\]\s*$/);
  if (nm) { note = nm[1]; s = s.slice(0, nm.index).trim(); }
  const rows = [];
  for (const seg of s.split(";")) {
    const t = seg.trim();
    if (!t) continue;
    const m = t.match(/^(.+?)\s+name\s+(\S+)\s+vs peer-median\s+(\S+)$/i);
    if (!m) return null;
    rows.push({ metric: m[1].trim(), name: m[2], median: m[3] });
  }
  return rows.length ? { rows, note } : null;
}

function peerDeltasFact(label, s) {
  if (!s || s.status !== "present" || s.value == null) return fact(label, s);
  const p = parsePeerDeltas(s.value);
  if (!p) return fact(label, s);
  const rows = p.rows.map((r) => ({ label: r.metric, cells: [r.name, r.median] }));
  return dataTable(label, s.source_ref, ["Name", "Peer median"], rows, p.note || "");
}

function parsePeerRoster(text) {
  let s = String(text).trim(), nameCap = "";
  const tm = s.match(/\|\s*the name:\s*([^|]+)$/i);
  if (tm) { nameCap = tm[1].trim(); s = s.slice(0, tm.index).trim(); }
  const pm = s.match(/^(\d+)\s+peers?\s+—\s+/i);
  if (!pm) return null;
  s = s.slice(pm[0].length);
  const rows = [];
  for (const seg of s.split(";")) {
    const t = seg.trim();
    if (!t) continue;
    const di = t.indexOf(" — ");
    const head = di >= 0 ? t.slice(0, di).trim() : t;
    let desc = di >= 0 ? t.slice(di + 3).trim() : "";
    const hm = desc.match(/\s*\(([^)]*)\)\s*$/);
    if (hm) desc = desc.slice(0, hm.index).trim();
    const cm = head.match(/^(.*?)\s+(\$[\d.]+[MBK]?)$/);
    rows.push({ name: cm ? cm[1].trim() : head, cap: cm ? cm[2] : "", desc });
  }
  return rows.length ? { rows, nameCap } : null;
}

function peerRosterFact(label, s) {
  if (!s || s.status !== "present" || s.value == null) return fact(label, s);
  const p = parsePeerRoster(s.value);
  if (!p) return fact(label, s);
  const rows = p.rows.map((r) => ({ label: r.name, cells: [r.cap || DASH, r.desc] }));
  return dataTable(label, s.source_ref, ["Mkt cap", "Business"], rows, p.nameCap ? `the name: ${p.nameCap}` : "");
}

function peerComps(pc) {
  if (!pc) return "";
  return sec("Peer comps", "CIQ Company Comparable Analysis — the consensus comp, framed to RESIST. The peer-vs-name gap is never a verdict: composition + fundamental deltas let the human judge the discount EARNED (value-trap) vs RESIDUAL (overshoot). The machine never re-draws the peer set or computes an implied upside.",
    peerRosterFact("Peer set (roster · caps · business)", pc.peer_set) +
    fact("Comparability (confidence gate)", pc.comparability, null, { hi: true }) +
    peerMultiplesFact("Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)", pc.trading_multiples) +
    // B1: the per-peer grid (name + median footer) replaces the median-only deltas line
    (pc.peer_grid ? peerGridTable(pc.peer_grid)
      : peerDeltasFact("Fundamental deltas (earned-vs-residual inputs)", pc.fundamental_deltas)));
}

function drawdownCause(dc) {
  if (!dc) return "";
  const filings = (dc.filings || []).map((f) => `
    <div class="filing">
      <div class="fh">${escapeHtml(f.form || "8-K")} · filed ${fmtDate(f.filing_date)} <span class="muted">(for the ${escapeHtml(f.gap_date || "")} gap-down)</span></div>
      <div class="muted" style="font-size:11.5px; margin-top:2px;">items: ${escapeHtml((f.item_types || f.items || []).join(" · "))}</div>
      ${(f.drivers && f.drivers.status === "present")
        ? `<div class="fe"><b>what the results showed:</b> ${escapeHtml(f.drivers.value)}${citeMark(f.drivers.source_ref)}</div>`
        : (f.events || []).map((e) => `<div class="fe">${escapeHtml(e)}</div>`).join("")}
      ${f.url ? `<div style="margin-top:5px;"><a href="${encodeURI(f.url)}" target="_blank" rel="noopener">EDGAR ${escapeHtml(f.accession || "")}</a></div>` : ""}
    </div>`).join("");
  return (  // (R3) body only — drawdownIdio wraps it in the shared section header
    fact("Shape", dc.shape) +
    fact("Gap-down dates", listFact(dc.gap_down_dates)) +
    fact("Revised guidance", dc.revised_guidance) +
    (filings ? `<div style="margin-top:12px;">${filings}</div>` : ""));
}

function idioVsShared(io) {
  if (!io) return "";
  const cohort = io.cohort && io.cohort.status === "present" && Array.isArray(io.cohort.value)
    ? `<div style="margin-top:10px;"><table class="data"><thead><tr><th>Cohort name</th><th class="num">Hops</th><th class="num">180d return</th><th>Via</th></tr></thead><tbody>
        ${io.cohort.value.map((c) => `<tr><td class="mono">${escapeHtml(c.ticker || "")}</td><td class="num">${c.hops ?? DASH}</td>
          <td class="num">${c.ret_180d == null ? DASH : fmtPct(c.ret_180d, { signed: true })}</td>
          <td class="muted" style="font-size:11.5px;">${escapeHtml(c.via || "")}</td></tr>`).join("")}
      </tbody></table><div class="muted" style="font-size:11.5px; margin-top:4px;">source: ${escapeHtml(io.cohort.source_ref || "")}</div></div>`
    : `<div class="fact-val muted" style="margin-top:8px;"><span class="pill unresolved">${io.cohort?.status === "missing" ? "MISSING" : "UNKNOWN"}</span> ${escapeHtml(io.cohort?.note || "no graph cohort")}</div>`;
  return (  // (R3) body only — drawdownIdio wraps it in the shared section header
    fact("Read", io.read, null, { hi: true }) +
    fact("Name 180d return", io.name_180d_return, ret) +
    fact("Market (IWM) 180d", io.market_180d_return, ret) +
    fact("Relative vs market", io.rel_vs_market, ret) +
    `<div class="fact"><div class="fact-label">Graph cohort</div><div>${cohort}</div></div>`);
}

// --- catalyst path (the five CIQ Estimates sheets, horizon-matched). Fix 4: the string fields are
// TABLE-rendered (reuse the margin-trend mini-table idiom) + curated (collapse/trim/group/cap); the
// full data always stays in dossier.json. Returns "" for a pre-catalyst_path JSON (back-compat).
const _GROUP_CAP = 6;  // (T3, mirrors render._GROUP_CAP) revision-event broker-day LINES shown; rest counted
const _LADDER_KEEP = ["NTM", "FY 2026", "FY 2027", "FY 2028"];
const _LOOKBACKS = ["12m", "9m", "6m", "3m", "2m", "1m", "latest", "now"];

// strip the trailing "  [as-of …]" / "  [data ≥ …]" suffix an extractor appends (as-of is on the header)
function catBody(v) {
  const s = String(v);
  const i = s.lastIndexOf("  [");
  return i !== -1 && s.trimEnd().endsWith("]") ? s.slice(0, i) : s;
}

// floor-aware as-of: a "≥"-prefixed value is an unverified export FLOOR, never a plain as-of
function catAsof(cp) {
  const a = cp.as_of || {};
  if (a.status !== "present" || !a.value) return "as-of UNKNOWN";
  const v = String(a.value);
  return v.startsWith("≥") ? `export date unverified (data ≥ ${v.slice(1)})` : `as-of ${v}`;
}

// a fact-row whose value IS a table — same wrapper as seriesTable, so it stays uniform + scrolls
// B4: the ONE shared table renderer (the compact idiom). Every dossier table routes through here —
// series (margin/trajectory/surprise/trading-multiples), the catalyst tables, and the B1/B3 grids.
// A row may carry `cls` (e.g. "name-row"/"median-row") for the distinguished B1 rows.
function dataTable(label, cite, cols, rows, note, estimate = []) {
  const ec = (i) => (estimate[i] ? " est-col" : "");  // (P3) shade consensus / forward-FY columns
  const head = `<tr><th></th>${cols.map((c, i) => `<th class="num${ec(i)}">${escapeHtml(c)}</th>`).join("")}</tr>`;
  const body = rows.map((r) =>
    `<tr${r.cls ? ` class="${r.cls}"` : ""}><td style="white-space:nowrap;">${escapeHtml(r.label)}</td>${r.cells.map((c, i) => `<td class="num${ec(i)}">${escapeHtml(c)}</td>`).join("")}</tr>`).join("");
  const noteHtml = note ? `<div class="muted" style="font-size:11px; margin-top:5px;">${escapeHtml(note)}</div>` : "";
  const citeHtml = citeMark(cite);
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div style="min-width:0;"><div style="overflow-x:auto;"><table class="data"><thead>${head}</thead><tbody>${body}</tbody></table></div>${noteHtml}${citeHtml}</div></div>`;
}

// $M/%/number cell formatters for the B1 grid + B3 implied table
// B.1 shared numeric formatters (ONE place): thousands-consistent, no negative-zero, net-cash
// en-US pinned (not the runtime locale) so the web/PDF thousands separators match the Python .md.
const _thou = (v, d = 0) => v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const _capC = (v) => (v == null ? DASH : (Math.abs(v) >= 1000 ? `$${_thou(v / 1000, 1)}B` : `$${_thou(v)}M`));
// NaN → dash (not a fabricated "0%"); Math.round is half-up, matching render._pctc's floor(x+0.5).
const _pctC = (v) => (v == null || Number.isNaN(v) ? DASH : `${Math.round(v * 100) || 0}%`);
// a blank/whitespace ratio → dash, NOT a fabricated "0.0" (Number("") === 0); "NM" passes through.
// half-up at 1dp (Math.round(n*10)/10) to MATCH render._ratioc's floor(x*10+0.5)/10 — a bare toFixed
// disagreed with the Python .md at a quarter-tie (7.25 → 7.3 vs banker's 7.2); Math.round(n*10) ===
// floor(n*10+0.5) on the same IEEE double, so the two renderers now format identically.
const _ratioC = (s) => { const t = s == null ? "" : String(s).trim(); if (t === "") return DASH; const n = Number(t); return Number.isNaN(n) ? t : (Math.round(n * 10) / 10).toFixed(1); };
const _netDebtC = (v) => (v == null ? DASH : (v < 0 ? `${_thou(-v)} (net cash)` : _thou(v)));
const _numC = (v) => (v == null ? DASH : _thou(v > -0.05 && v < 0 ? 0 : v, 1));  // small negative → "0.0", never "-0.0"

// (B1) per-peer grid → the shared table; name row + median footer visually distinct
function peerGridTable(s) {
  const label = "Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)";
  if (!s || s.status !== "present" || !Array.isArray(s.value)) return fact(label, s);
  const cols = ["Cap", "TEV/EBITDA", "TEV/Rev", "P/E", "EBITDA margin", "Rev growth (1y)",
                "Total debt/EBITDA", "Net debt ($M)"];  // B2: valuation multiples lead (≤8 cols)
  const rows = s.value.map((r) => ({
    label: r.name + (r.is_name ? " · the name" : (r.is_median ? " (peers)" : "")),
    cls: r.is_name ? "name-row" : (r.is_median ? "median-row" : ""),
    cells: [_capC(r.market_cap), _ratioC(r.tev_ebitda), _ratioC(r.tev_rev), _ratioC(r.pe),
            _pctC(r.ebitda_margin), _pctC(r.rev_growth_1y), _ratioC(r.debt_to_ebitda),
            _netDebtC(r.net_debt)],
  }));
  return dataTable(label, s.source_ref, cols, rows, "");
}

// (K3, mirrors render._credit_health_lines / _CH_NAME_RE / _CH_PEER_RE) credit health as a 4-row
// mini-table (dimension | name | peer median) parsed from the prose credit_health value, scale +
// issuer-rating in the note. Falls back to the plain fact if the shape doesn't match — never a
// fabricated score. Name/Peer are the `cells` (dataTable marks them .num → right-aligned); the
// dimension is the ROW LABEL under dataTable's prepended blank column (NOT a col — else scores shift).
const _CH_DIMS = ["Overall", "Operational", "Solvency", "Liquidity"];
const _CH_NAME_RE = /Overall\/Operational\/Solvency\/Liquidity\s+([\d.]+)\/([\d.]+)\/([\d.]+)\/([\d.]+)/;
const _CH_PEER_RE = /peer-median\s+O\/Op\/S\/L\s+([\d.]+)\/([\d.]+)\/([\d.]+)\/([\d.]+)/;
function creditHealth(lv) {
  const ch = lv.credit_health;
  if (!ch || ch.status !== "present" || ch.value == null) return fact("Credit health", ch);
  const text = String(ch.value);
  const nm = text.match(_CH_NAME_RE), pr = text.match(_CH_PEER_RE);
  if (!nm || !pr) return fact("Credit health", ch);  // unknown shape → plain fact, never a fabricated table
  const rows = _CH_DIMS.map((dim, i) => ({ label: dim, cells: [nm[i + 1], pr[i + 1]] }));
  const scale = text.match(/scale\b.*/);
  const rating = text.match(/\(([^)]*(?:issuer rating|unrated|rated)[^)]*)\)/);
  const note = [rating ? rating[1] : "", scale ? scale[0] : ""].filter(Boolean).join(" · ");
  // (audit) the dimension is the ROW LABEL (the blank column `dataTable` prepends) — NOT a col, else
  // the 2-cell rows sit under a 3-cell header and every score shifts one column left.
  return dataTable("Credit health", ch.source_ref, ["Name", "Peer median"], rows, note);
}

// (B2) unified leverage & survival — both bases labeled + credit health; "" when the block is absent
// (P7) INNER leverage content (no card) — clubbed under the one Survival section by leverageSurvival.
function leverageBlock(m) {
  const lv = m.leverage_survival;
  if (!lv) return "";
  return subhead("Leverage & survival") +  /* (K5) header humanized; net-vs-total discipline is per-row */
    fact("Net debt / EBITDA (CIQ NET basis)", lv.net_debt_to_ebitda, mult) +
    fact("Total debt / EBITDA (comps — name vs peer median)", lv.total_debt_to_ebitda) +
    fact("Net debt / OCF", m.quality.net_debt_to_ocf, mult) +
    fact("Net debt / EBITDA (fwd-adj)", m.quality.net_debt_to_ebitda_adjusted) +
    fact("Interest coverage", lv.interest_coverage, mult) +
    fact("Survival (self-funding + nearest wall)", lv.survival) +
    creditHealth(lv);  // (K3) 4-row mini-table; fail-soft to fact("Credit health", …)
}

// (B3 · K4) DEMOTED to the appendix, reference-only (mirrors render._implied_lines): implied EQUITY
// at the peer-MEDIAN multiple for the 3 decision bases (LTM EBITDA · NTM EBITDA · NTM Revenue), with
// the name's ACTUAL market cap adjacent. MEDIAN column only — full Low/Mean/High + all other bases
// stay in JSON. No computed %/discount/upside; the heterogeneity gate renders short on the header.
function impliedBlock(iv) {
  if (!iv) return "";
  const g = iv.comparability_gate || {};
  const gate = g.status === "present" ? g.value : "";
  const eq = iv.implied_equity || {};
  let table = fact("Implied equity", eq);
  if (eq.status === "present" && Array.isArray(eq.value)) {
    const keep = ["LTM EBITDA", "NTM EBITDA", "NTM Revenue"];  // (K4) the 3 decision bases only
    // (audit C4) word-boundary, not substring — so "NTM EBITDA" doesn't match "NTM EBITDAR"
    const rows = eq.value.filter((r) => keep.some((k) => new RegExp("^" + k + "\\b").test(String(r.basis))))
      .map((r) => ({ label: r.basis, cells: [_numC(r.median)] }));  // (K4) MEDIAN column only
    table = dataTable("Implied equity at peer-median ($M, CIQ)", eq.source_ref,
      ["Implied equity (median)"], rows, "");
  }
  return sec("Reference: CIQ implied equity at peer-median multiples",  // (K5) renamed + demoted
    (gate ? gateShortref(gate) + " — " : "") + "Reference only — the human judges earned vs residual "
    + "(not a machine upside); the full Low/Mean/High and all bases are in the JSON.",
    fact("Name market cap ($M) — the ADJACENT fact to compare against", iv.market_cap) +
    fact("Bridge (TEV → equity)", iv.bridge) +
    table);
}

// (C) as-of header, floor-aware — mirrors render._asof_header ('≥' = an unverified export floor)
function asOfHeader(s) {
  if (!s || s.status !== "present" || !s.value) return "as-of UNKNOWN";
  const v = String(s.value);
  return v.startsWith("≥") ? `export date unverified (data ≥ ${v.slice(1)})` : `as-of ${v}`;
}

// (C1/C2) a Sourced[FinTable] → the shared dataTable; UNKNOWN/MISSING falls through to a fact badge
function finTable(label, s) {
  if (!s || s.status !== "present" || !s.value) return fact(label, s);
  const ft = s.value;
  const rows = (ft.rows || []).map((r) => ({ label: r.label, cells: r.cells }));
  return dataTable(label, s.source_ref, ft.columns || [], rows, ft.note || "", ft.is_estimate || []);
}

// (D5b) relabel the levered-FCF row + footnote (display-only; the FinTable is rebuilt in place).
function fcfRelabel(s) {
  if (!s || s.status !== "present" || !s.value) return s;
  const ft = s.value;
  if (!(ft.rows || []).some((r) => r.label === "FCF ($M)")) return s;
  const rows = ft.rows.map((r) => (r.label === "FCF ($M)" ? { ...r, label: "FCF (levered, CIQ)" } : r));
  const fn = "FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex";
  return { ...s, value: { ...ft, rows, note: ft.note ? `${ft.note} · ${fn}` : fn } };
}

// (C1–C4 · D1 · K1 · K4) FINANCIAL-SUMMARY appendix — actuals + consensus estimates, then (K1) the
// relocated capital-structure PROVENANCE (full instrument panel + 8-K/covenant pointers + full
// per-family covenant tables), (K4) the demoted implied-valuation REFERENCE card, and the relocated
// management-commentary pointer. Mirrors render_markdown's appendix order: financial summary →
// cap-structure provenance → implied-valuation reference → mgmt pointer. Every table routes through
// dataTable; the mgmt pointer renders even for a pre-C dossier.json (no financial summary).
function appendixBlock(m) {
  const fs = m.financial_summary;
  const mgmt = fact("Management commentary (transcript POINTER — read the file; not a machine excerpt)",
    m.management_commentary);
  const cap = m.capital_structure ? capitalStructureAppendix(m.capital_structure) : "";  // (K1) provenance
  const implied = impliedBlock(m.implied_valuation);  // (K4) reference-only card ("" for a pre-B3 JSON)
  // (mirrors render_markdown) order: financial summary → cap-structure provenance → implied-valuation
  // reference → management-commentary pointer LAST.
  if (!fs) return sec("Appendix", "", cap) + implied + mgmt;
  return sec(`Appendix — financial summary (actuals + consensus estimates) — ${asOfHeader(fs.as_of)}`,
    "Consensus (E) columns are marked + as-of-stamped; growth never spans a basis change (— basis); actuals fail loud on gaps. The machine assembles — no verdict.",
    finTable("Annual ($M; E = consensus) — last-4-FY + LTM + FY26E/FY27E", fcfRelabel(fs.annual)) +
    finTable("Trailing 8 quarters — the recent-quarter trajectory", fs.quarterly) +
    fact("Balance-sheet posture", fs.balance_sheet) +
    fact("Coherence — balance sheet vs implied-valuation bridge", fs.coherence) +
    cap) +     // (K1) capital-structure provenance (subhead + full panel/pointers/terms)
    implied +  // (K4) implied-valuation reference as its own card, after the appendix card
    mgmt;      // (D1) management-commentary pointer LAST
}

// (4a) horizon → metric × [FQ2, FQ3] table; zero-breadth-across-all-windows rows collapse to a line
function horizonTable(s) {
  const label = "Horizon read (FQ — next-2Q revision breadth)";
  if (!s || s.status !== "present" || !s.value) return fact(label, s);
  const byMetric = new Map(), periods = [];
  for (const seg of catBody(s.value).split("; ")) {
    const t = seg.trim(), ci = t.indexOf(": ");
    if (ci < 0) continue;
    const head = t.slice(0, ci), pm = head.match(/\s(FQ\d\s*\d{4})$/);
    if (!pm) continue;
    const period = pm[1], metric = head.slice(0, head.length - period.length).trim();
    if (!periods.includes(period)) periods.push(period);
    if (!byMetric.has(metric)) byMetric.set(metric, {});
    byMetric.get(metric)[period] = t.slice(ci + 2);
  }
  periods.sort();
  const nonzero = [], zero = [];
  for (const [metric, cells] of byMetric)
    (Object.values(cells).some((c) => /[1-9]\d*[↑↓]/.test(c)) ? nonzero : zero).push(metric);
  const rows = nonzero.map((m) => ({ label: m, cells: periods.map((p) => byMetric.get(m)[p] || DASH) }));
  const note = zero.length ? `no revisions in any window: ${zero.join(", ")}` : "";
  return dataTable(label, s.source_ref, periods, rows, note);
}

const _baseMetric = (m) => m.replace(/\s*(Normalized|\(GAAP\)|\(Excl\. Excep\))/g, "").trim();

// (4b) acceleration → metric rows × lookback columns + net; GAAP kept adjacent to Normalized
function accelTable(s) {
  const label = "Acceleration read (monthly consensus path)";
  if (!s || s.status !== "present" || !s.value) return fact(label, s);
  const entries = [];
  for (const entry of catBody(s.value).split(" | ")) {
    const semi = entry.indexOf("; "), chain = semi >= 0 ? entry.slice(0, semi) : entry;
    const change = semi >= 0 ? entry.slice(semi + 2).trim() : "";
    const ci = chain.indexOf(": ");
    if (ci < 0) continue;
    const metric = chain.slice(0, ci).replace(/^FY\s*\d{4}\s*/, "").trim(), pts = {};
    for (const pair of chain.slice(ci + 2).split(" → ")) {
      const m = pair.trim().match(/^(-?[\d.,]+)\s*\((\w+)\)$/);
      if (m) pts[m[2]] = m[1];
    }
    entries.push({ metric, pts, change });
  }
  entries.sort((a, b) =>
    _baseMetric(a.metric).localeCompare(_baseMetric(b.metric)) ||
    (a.metric.includes("GAAP") ? 1 : 0) - (b.metric.includes("GAAP") ? 1 : 0));
  const cols = _LOOKBACKS.filter((lb) => entries.some((e) => e.pts[lb] != null));
  const rows = entries.map((e) => ({ label: e.metric, cells: [...cols.map((c) => e.pts[c] || DASH), e.change || DASH] }));
  return dataTable(label, s.source_ref, [...cols, "net"], rows, "");
}

// (4c) ladder → period × multiple table; NTM + FY26–FY28 only, later years noted (full in JSON)
function ladderTable(s) {
  const label = "Cross-name anchor (NTM forward-multiple ladder)";
  if (!s || s.status !== "present" || !s.value) return fact(label, s);
  const segs = catBody(s.value).split(" | ").map((x) => x.trim()).filter(Boolean);
  const cols = [], rows = [];
  let kept = 0;
  for (const seg of segs) {
    const ci = seg.indexOf(": ");
    if (ci < 0) continue;
    const period = seg.slice(0, ci).trim();
    if (!_LADDER_KEEP.includes(period)) continue;
    kept++;
    const by = {};
    for (const cell of seg.slice(ci + 2).split(" · ")) {
      const m = cell.trim().match(/^(.+?)\s+(\S+)$/);
      if (m) { if (!cols.includes(m[1])) cols.push(m[1]); by[m[1]] = m[2]; }
    }
    rows.push({ label: period, cells: cols.map((c) => by[c] || DASH), _by: by });
  }
  for (const r of rows) r.cells = cols.map((c) => r._by[c] || DASH);
  const extra = segs.length - kept;
  return dataTable(label, s.source_ref, cols, rows, extra > 0 ? `+${extra} later fiscal years in JSON` : "");
}

// (T3, mirrors render._pct_delta) |%Δ| of a revision — |current − prior| / |prior|; -1 when either
// side is non-numeric or prior is 0. Cross-metric RAW deltas are unit-incoherent, so the headline
// ranks on |%Δ|, never raw |Δ| (a big-number Revenue move would otherwise always outrank a bigger-%
// EBITDA cut).
const _pctDelta = (e) => {
  const prior = Number(e.broker_prior), cur = Number(e.broker_current);
  if (isNaN(prior) || isNaN(cur) || prior === 0) return -1;
  return Math.abs(cur - prior) / Math.abs(prior);
};

// (T3, mirrors render._n1) a revision value → 1-decimal, or verbatim when non-numeric ("-").
const _n1 = (x) => { const f = Number(x); return isNaN(f) ? String(x) : f.toFixed(1); };

// (T3, mirrors render._HEADLINE_PRIORITY) headline metric PRIORITY — each tuple is the substrings a
// metric must contain (ALL of them): EBITDA > Revenue > EPS-Normalized.
const _HEADLINE_PRIORITY = [["ebitda"], ["revenue"], ["eps", "normal"]];

// (T3, mirrors render._revision_headline) the headline revision for a broker-day, by metric PRIORITY
// (EBITDA > Revenue > EPS-Normalized) — the largest-|%Δ| revision of the first priority metric
// present; else the largest-|%Δ| of ANY metric. null when no event carries a clean |%Δ|. Never raw |Δ|.
function _revisionHeadline(evs) {
  const numeric = evs.filter((e) => _pctDelta(e) >= 0);
  if (!numeric.length) return null;
  for (const kws of _HEADLINE_PRIORITY) {
    const tier = numeric.filter((e) => kws.every((k) => e.metric.toLowerCase().includes(k)));
    if (tier.length) return tier.reduce((a, b) => (_pctDelta(b) > _pctDelta(a) ? b : a));
  }
  return numeric.reduce((a, b) => (_pctDelta(b) > _pctDelta(a) ? b : a));
}

// (4d · T3) revision events COMPRESSED to ONE line per broker-day — date · broker · action mix
// (n↑/n↓, initiations) · the headline revision (largest-|Δ|, EBITDA-preferred, 1-decimal) · "+N items
// in JSON". Cap _GROUP_CAP broker-days, the remainder counted. The expanded per-item view (every
// event) is the web ON-DEMAND tier — a collapsed <details> after the compressed lines — + the JSON.
// Full list always in dossier.json. Mirrors render._grouped_events_lines.
function eventGroups(s) {
  const label = "Revision-event log";
  if (!s || s.status !== "present" || !Array.isArray(s.value) || !s.value.length) return fact(label, s);
  const events = s.value, groups = new Map();
  for (const e of events) {
    const k = `${e.date}|${e.broker}`;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(e);
  }
  const keys = [...groups.keys()].sort().reverse(); // date|broker, most recent first
  const lines = keys.slice(0, _GROUP_CAP).map((k) => {
    const evs = groups.get(k), [dt, broker] = k.split("|");
    let ups = 0, downs = 0, inits = 0;
    for (const e of evs) {
      const t = (e.change_type || "").toLowerCase();
      if (t.includes("upward")) ups += 1;
      if (t.includes("downward")) downs += 1;
      if (t.includes("initiation")) inits += 1;
    }
    const mix = `${ups}↑/${downs}↓` + (inits ? `, ${inits} initiations` : "");
    const head = _revisionHeadline(evs);
    const headline = head ? ` · ${escapeHtml(head.metric)} ${escapeHtml(head.period)} ${_n1(head.broker_prior)}&rarr;${_n1(head.broker_current)}` : "";
    const rest = evs.length - (head ? 1 : 0);
    return `<div style="margin-top:5px;"><b>${escapeHtml(dt)} · ${escapeHtml(broker)}</b> <span class="muted">· ${escapeHtml(mix)}</span>${headline}${rest > 0 ? ` <span class="muted">· +${rest} items in JSON</span>` : ""}</div>`;
  }).join("");
  const moreGroups = keys.length > _GROUP_CAP ? `<div class="muted" style="font-size:12px; margin-top:4px;">+${keys.length - _GROUP_CAP} more broker-days in JSON</div>` : "";
  // (T3) ON-DEMAND expansion: the full per-item list — every event (metric period prior→current),
  // grouped by broker-day — collapsed in a <details>. This is the web on-demand tier of the moved facts.
  const expanded = keys.map((k) => {
    const evs = groups.get(k), [dt, broker] = k.split("|");
    const items = evs.map((e) =>
      `<li><b>${escapeHtml(e.metric)}</b> ${escapeHtml(e.period)}: ${escapeHtml(e.broker_prior)}&rarr;${escapeHtml(e.broker_current)} <span class="muted">(cons ${escapeHtml(e.consensus_before)}&rarr;${escapeHtml(e.consensus_after)})</span></li>`).join("");
    return `<div style="margin-top:7px;"><b>${escapeHtml(dt)} · ${escapeHtml(broker)}</b><ul class="event-log">${items}</ul></div>`;
  }).join("");
  const details = `<details style="margin-top:6px;"><summary style="cursor:pointer; font-size:12px; color:var(--ink-2);">Expand all ${events.length} revisions per broker-day (on-demand)</summary><div>${expanded}</div></details>`;
  const cite = citeMark(s.source_ref);
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)} <span class="muted">(${events.length} events · ${keys.length} broker-days)</span></div><div>${lines}${moreGroups}${details}${cite}</div></div>`;
}

function catalystPath(cp, cc) {
  if (!cp) return "";
  // Fix 5: the legacy consensus facts are gone (duplicated by the reads); fold in the one
  // non-duplicate — Surprise history.
  const surprise = cc ? seriesTable("Surprise history (annual beat/miss)", cc.surprise_history) : "";
  return sec(`Catalyst path — ${catAsof(cp)}`,
    "Horizon-matched estimates, guidance & revision events (CIQ Estimates). Native cadence — FQ horizon, monthly path, NTM anchor. Assembles and cites; renders no upside, fair value, or direction.",
    horizonTable(cp.horizon_read) +
    accelTable(cp.acceleration_read) +
    ladderTable(cp.cross_name_anchor) +
    guidanceBridge(cp) +
    fact("Consensus stats (target + ratings)", cp.consensus_stats) +
    eventGroups(cp.revision_events) +
    surprise +
    // (F) positioning inputs — free DATED feeds; only when present (pre-F JSON omits both fields).
    // Counts / shares / dates only, no interpretation.
    (cp.insider_activity ? fact("Insider activity (Form 4, 6m)", cp.insider_activity) : "") +
    (cp.short_interest ? fact("Short interest (FINRA)", cp.short_interest) : ""));
}

// (H4) guidance bridge → table (metric | latest guide | for | dated | age | record | most recent);
// old JSON (no guidance_bridge_rows) → the flat fact.
function guidanceBridge(cp) {
  const rs = cp.guidance_bridge_rows;
  if (!rs || rs.status !== "present" || !Array.isArray(rs.value) || !rs.value.length)
    return fact("Guidance bridge (latest guide + track-record)", cp.guidance_bridge);
  const rows = rs.value.map((r) => ({
    label: r.metric,
    cells: [r.latest_guide, r.period, r.dated, r.age, r.record, r.most_recent],
  }));
  return dataTable("Guidance bridge (latest guide + sign-aware delivery track-record)", rs.source_ref,
    ["Latest guide", "For", "Dated", "Age", "Record (met/resolved)", "Most recent"], rows, "");
}

// Legacy fallback — ONLY rendered for a pre-catalyst_path dossier.json (no catalyst_path field).
function consensus(cc) {
  if (!cc) return "";
  return sec("Consensus context", "Light context for 'am I non-consensus' — never a driver.",
    fact("EPS revisions", cc.eps_trend) +
    fact("Revenue revisions", cc.revenue_trend) +
    fact("Revision history", cc.revision_history) +
    seriesTable("Surprise history", cc.surprise_history));
}

function synthesis(s) {
  const fence = `<div class="synth-fence"><b>The framing, not the answer.</b> A verdict-free bull/bear structure for the human to reason about — there is no recommendation, score, direction, or probability anywhere in it, by design. The human decides and logs BUY/AVOID via the CLI. <b>Citations [n] locate each claim in a numbered source (listed at the end of each tab) for you to verify — cited is not verified.</b></div>`;
  if (!s) {
    return `<div class="card ds-section"><div class="ds-title">Synthesis</div>${fence}
      <div class="notice">Synthesis not assembled — mechanical layer only (CIQ inputs too thin, or the LLM step was skipped). The facts above stand on their own.</div></div>`;
  }
  const point = (p, cls) => `<div class="point ${cls}">${escapeHtml(p.claim)}${citeMark(p.source_ref)}${p.cited === false ? ` <span class="uncited">⚠ uncited — does not trace to a mechanical fact</span>` : ""}</div>`;
  const dq = s.decisive_question || {};
  // (H6) an '[LLM-suggested, unverified]' twin's outcome is the MODEL's claim → suffix "(LLM-claimed
  // — verify)"; a roster/self-sourced twin renders plain. Deterministic, render-side.
  const twinOutcome = (t) => {
    const src = (t.source || "").toLowerCase();
    const unverified = src.includes("llm-suggested") || src.includes("unverified");
    return (t.outcome || "") + (unverified ? " (LLM-claimed — verify)" : "");
  };
  // (review #5/#8) twin source rendered INLINE, matching the md renderer's "- source: …" line —
  // NOT citeMark → an LLM-suggested/unverified twin never becomes a numbered # Sources entry (a
  // Sources list is for primary cells, not "[LLM-suggested, unverified]"), and the two renderers
  // agree (neither lists a twin source in its endnotes).
  const twins = (s.twin_reference_cases || []).map((t) => `
    <div class="point"><b>${escapeHtml(t.name || "")}</b> — ${escapeHtml(twinOutcome(t))}
      <div class="muted" style="font-size:12px; margin-top:3px;">distinguished by: ${escapeHtml(t.distinguishing_fact || "")}</div>
      <div class="muted" style="font-size:12px; margin-top:3px;">source: ${escapeHtml(t.source || "")}</div></div>`).join("");
  return `<div class="card ds-section"><div class="ds-title">Synthesis · framing</div>${fence}
    ${s.evidence_balance ? `<div style="margin:6px 0; padding:8px 11px; border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:4px; font-size:13px; line-height:1.5;"><b>Evidence balance:</b> ${escapeHtml(s.evidence_balance)}</div>` : ""}
    <div class="ds-title" style="font-size:12px; margin-top:6px;">Bull — the overshoot case</div>
    ${orderPoints(s.bull_points).map((p) => point(p, "bull")).join("") || `<div class="muted">—</div>`}
    <div class="ds-title" style="font-size:12px; margin-top:14px;">Bear — the terminal-decline case</div>
    ${orderPoints(s.bear_points).map((p) => point(p, "bear")).join("") || `<div class="muted">—</div>`}
    <div class="ds-title" style="font-size:12px; margin-top:14px;">The decisive question</div>
    <div style="font-size:13.5px; font-weight:600; margin:4px 0 8px;">${escapeHtml(dq.question || DASH)}</div>
    <div class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">Evidence for</div>
    ${(dq.evidence_for || []).map((p) => point(p, "bull")).join("") || `<div class="muted">—</div>`}
    <div class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em; margin-top:8px;">Evidence against</div>
    ${(dq.evidence_against || []).map((p) => point(p, "bear")).join("") || `<div class="muted">—</div>`}
    <div class="ds-title" style="font-size:12px; margin-top:14px;">Key unknowns</div>
    <ul class="kv-list">${(s.key_unknowns || []).map((k) => `<li>${escapeHtml(k)}</li>`).join("") || "<li class='muted'>—</li>"}</ul>
    ${twins ? `<div class="ds-title" style="font-size:12px; margin-top:14px;">Twin analogues</div><div class="muted" style="font-size:11px; margin:-2px 0 6px;">LLM-selected analogies — accept or reject each. A citation means the data is sourced, not that the analogy holds.</div>${twins}` : ""}
  </div>`;
}

function loggedVerdict(v, ticker, refDate) {
  if (!v) {
    const cid = `${ticker}-screen2-${String(refDate || "").replace(/-/g, "")}`;
    return `<details class="card ds-section">
      <summary style="cursor:pointer; font-size:12.5px; font-weight:600; color:var(--ink-2);">Logged verdict <span class="muted" style="font-weight:400;">— none yet for ${escapeHtml(ticker)} · how to log it (read-only — run locally)</span></summary>
      <div class="logged-verdict none" style="margin-top:10px;">Verdicts are logged via the CLI only — never from this dashboard (the friction is the safeguard). After deciding from the facts above, run this locally from the repo root:</div>
      <pre style="background:var(--nav-bg); color:#c3cad6; padding:12px 14px; border-radius:8px; font-size:12px; overflow-x:auto; margin:10px 0 0; line-height:1.6;"><code>python -m vinci log-verdict ${escapeHtml(cid)} \\
  --verdict &lt;BUY|AVOID_TERMINAL&gt; \\
  --twin "how the terminal-decline twin is ruled out" \\
  --thesis "the overshoot thesis (or AVOID rationale)" \\
  --kill "what would falsify it" \\
  --horizon-days 180 --confidence &lt;low|medium|high&gt;</code></pre>
      <div class="subtitle muted" style="margin-top:8px;">Append-only — the entry price is frozen from the screen's as-of date (<span class="mono">${escapeHtml(String(refDate || DASH))}</span>); a logged verdict cannot be edited or deleted.</div></details>`;
  }
  const isBuy = isBuyVerdict(v.verdict);
  return `<div class="card ds-section"><div class="ds-title">Logged verdict — immutable</div>
    <div class="subtitle muted ds-sub">The human's call, logged via the CLI and frozen. This dashboard displays it; it cannot edit, delete, or revise it.</div>
    <div class="logged-verdict">
      <div style="display:flex; gap:12px; align-items:baseline; flex-wrap:wrap;">
        <span class="pill ${isBuy ? "buy" : "avoid"}">${escapeHtml(v.verdict)}</span>
        <span class="pill ${v.resolved ? "live" : "unresolved"}">${v.resolved ? "resolved" : "unresolved · " + (v.daysToHorizon == null ? DASH : Math.max(0, v.daysToHorizon) + "d to horizon")}</span>
        <span class="muted" style="font-size:12px; margin-left:auto;">decided ${fmtDate(v.decidedAt)}</span>
      </div>
      <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:10px; font-size:13px;">
        <div><span class="muted">Frozen entry</span> <span class="mono" style="font-weight:600;">${fmtPrice(v.entryPrice)}</span> <span class="muted">@ ${fmtDate(v.entryPriceAsOf)}</span></div>
        <div><span class="muted">Horizon</span> <span class="mono">${v.horizonDays}d</span> → ${fmtDate(v.horizonDate)}</div>
        <div><span class="muted">Confidence</span> ${escapeHtml(v.confidence || DASH)}</div>
        <div><span class="muted">Benchmark</span> <span class="mono">${escapeHtml(v.benchmark || DASH)}</span></div>
      </div>
      ${v.thesis ? `<div style="margin-top:10px;"><span class="muted" style="font-size:11px; text-transform:uppercase;">Thesis</span><div style="font-size:13px; color:var(--ink-2);">${escapeHtml(v.thesis)}</div></div>` : ""}
      ${v.killCriteria ? `<div style="margin-top:8px;"><span class="muted" style="font-size:11px; text-transform:uppercase;">Kill criteria</span><div style="font-size:13px; color:var(--ink-2);">${escapeHtml(v.killCriteria)}</div></div>` : ""}
    </div></div>`;
}

// a Sourced[list[str]] rendered inline (e.g. gap-down dates)
function listFact(s) {
  if (!s || s.status !== "present" || !Array.isArray(s.value)) return s || {};
  return { status: "present", value: s.value.map((x) => fmtDate(x)).join(" · "), source_ref: s.source_ref };
}
