// DOSSIER VIEWER — render the structured dossier.json into styled, source-bound sections.
// Assembles facts · NO verdict. Every fact shows its ↳ citation (source-binding is the signature).
// The synthesis is fenced as "the framing, not the answer." Read-only; verdicts are CLI-logged.
import { getDossier, getDossierIndex, getLedger, isBuyVerdict } from "../lib/snapshots.js";
import { fmtPrice, fmtDate, fmtPct, escapeHtml, DASH } from "../lib/format.js";

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
  // Export this dossier to PDF — the print stylesheet (@media print) strips the app chrome so the
  // output is just the report. Read-only: it prints what is already shown, renders no new judgment.
  const pdfBtn = root.querySelector("#ds-pdf");
  if (pdfBtn) pdfBtn.addEventListener("click", () => window.print());
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

// --- a single Sourced fact: value + ↳ source_ref, or honest UNKNOWN/MISSING --
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
  const cite = s.source_ref ? `<span class="cite">${escapeHtml(s.source_ref)}</span>` : "";
  // a note ON a present value is a caveat (e.g. a distorted P/E that must not read as a clean multiple)
  const caveat = s.note ? `<div class="fact-caveat">⚠ ${escapeHtml(s.note)}</div>` : "";
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div class="fact-val${hi ? " hi" : ""}">${val}${cite}${caveat}</div></div>`;
}

const sec = (title, sub, inner) => `<div class="card ds-section"><div class="ds-title">${escapeHtml(title)}</div>${sub ? `<div class="subtitle muted ds-sub">${escapeHtml(sub)}</div>` : ""}${inner}</div>`;
const mult = (v) => escapeHtml(Number(v).toFixed(1)) + "&times;";
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

function seriesTable(label, s) {
  if (!s || s.status !== "present" || s.value == null) return fact(label, s);  // honest UNKNOWN/MISSING
  let parsed;
  try { parsed = parseSeries(s.value); } catch { parsed = { series: [], scalars: [], note: "" }; }
  if (!parsed.series.length) return fact(label, s);  // unparseable shape → raw-text fallback
  const periods = [];
  for (const sr of parsed.series) for (const p of sr.points) if (!periods.includes(p.period)) periods.push(p.period);
  periods.sort((a, b) => periodKey(a) - periodKey(b));  // chronological columns across uneven sub-series
  const sup = (b) => (b ? `<sup class="muted">${escapeHtml(b)}</sup>` : "");
  const head = `<tr><th></th>${periods.map((p) => `<th class="num">${escapeHtml(fmtPeriod(p))}</th>`).join("")}</tr>`;
  const body = parsed.series.map((sr) => {
    const by = Object.fromEntries(sr.points.map((p) => [p.period, p]));
    const cells = periods.map((p) => (by[p]
      ? `<td class="num">${escapeHtml(by[p].value)}${sup(by[p].basis)}</td>` : `<td class="num">${DASH}</td>`)).join("");
    return `<tr><td style="white-space:nowrap;">${escapeHtml(sr.label)}</td>${cells}</tr>`;
  }).join("");
  const scalars = parsed.scalars.map((x) =>
    `<div class="muted" style="font-size:12px; margin-top:6px;">${escapeHtml(x.label)}: <b style="color:var(--ink);">${escapeHtml(x.value)}</b></div>`).join("");
  const note = parsed.note ? `<div class="muted" style="font-size:11px; margin-top:5px;">${escapeHtml(parsed.note)}</div>` : "";
  const cite = s.source_ref ? `<span class="cite">${escapeHtml(s.source_ref)}</span>` : "";
  // a normal label-left / value-right fact ROW where the value IS the table — keeps it uniform with
  // every other fact; the value cell clamps to its grid column (min-width:0) and scrolls if too wide.
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div style="min-width:0;"><div style="overflow-x:auto;"><table class="data"><thead>${head}</thead><tbody>${body}</tbody></table></div>${scalars}${note}${cite}</div></div>`;
}

function renderDossier(d, verdict) {
  const m = d.mechanical || {};
  return [
    header(d),
    flagsSection(d.caveats || d.flags || []),  // d.flags = pre-split fallback for un-re-assembled JSONs
    valuation(m.valuation),
    quality(m.quality),
    concentration(m.concentration),
    peerComps(m.peer_comps),
    drawdownCause(m.drawdown_cause),
    idioVsShared(m.idiosyncratic_vs_shared),
    consensus(m.consensus_context),
    sec("Management commentary", "Earnings-call transcript — a pointer for the human to read in full; never a machine-curated excerpt.",
      fact("Transcript", m.management_commentary)),
    synthesis(d.synthesis),
    loggedVerdict(verdict, d.ticker, d.reference_date),
  ].join("");
}

function header(d) {
  return `<div class="header-block ds-header">
    <div class="ds-header-main">
      <h1 class="page-h"><span class="mono">${escapeHtml(d.ticker)}</span> · ${escapeHtml(d.name || "")}</h1>
      <div class="subtitle">Assembled facts · <b>no verdict</b> — a source-bound mechanical layer plus a fenced framing. The BUY/AVOID call is the human's, logged via the CLI.</div>
      <div class="ds-meta">
        <span>Queue rank <span class="mono">#${d.rank ?? DASH}</span> <span class="muted">(ordering context, not a verdict on the name)</span></span>
        <span>CIK <span class="mono">${escapeHtml(d.cik || DASH)}</span></span>
        <span>Data as of <span class="mono">${fmtDate(d.reference_date)}</span></span>
        <span>Assembled <span class="mono">${fmtDate(d.assembled_at)}</span> <span class="muted">(may predate newer filings)</span></span>
        <span class="muted">${d.synthesis ? `synthesis: ${escapeHtml(d.llm_model || "llm")}` : "mechanical layer only"}</span>
      </div>
    </div>
    <button id="ds-pdf" class="ds-pdf-btn" type="button"
      title="Export this dossier to PDF — opens your browser's print dialog; choose &ldquo;Save as PDF&rdquo;.">&#x2913; Download PDF</button>
  </div>`;
}

function flagsSection(caveats) {
  // Decision caveats only (d.caveats) — the machine-QA self-checks live in d.qa_flags (dev/JSON),
  // deliberately kept out of this human view, matching the PDF/markdown render.
  if (!caveats.length) return "";
  const rows = caveats.map((f) => {
    const resolved = /^RESOLVED\b/i.test(f);
    return `<div class="flag ${resolved ? "resolved" : "open"}"><span class="fi">${resolved ? "✓" : "⚠"}</span><span>${escapeHtml(f)}</span></div>`;
  }).join("");
  return `<div class="card ds-section"><div class="ds-title">Analyst caveats — verify before the verdict</div>
    <div class="subtitle muted ds-sub">Resolved (✓) vs open (⚠). Open caveats need a human check; they are not conclusions.</div>${rows}</div>`;
}

function valuation(v) {
  if (!v) return "";
  return sec("Valuation", "Multiples vs the name's own ~5y history, and where it sits in that range.",
    fact("P/E", v.pe, (x) => escapeHtml(Number(x).toFixed(1)) + "&times;") +
    fact("P/E percentile", v.pe_percentile_5y, pctile) +
    fact("EV/EBITDA (TEV/LTM, GAAP)", v.ev_ebitda, mult) +
    fact("EV/EBITDA percentile", v.ev_ebitda_percentile_5y, pctile) +
    fact("EV/adj-EBITDA (forward)", v.ev_ebitda_adjusted_fwd) +
    fact("Adjusted EPS (guide)", v.adjusted_eps) +
    fact("Range position", v.range_position, null, { hi: true }));
}

function quality(q) {
  if (!q) return "";
  return sec("Quality", "Durability: cash generation, margins, leverage, dilution, covenant flags.",
    fact("FCF sign", q.fcf_sign, signWord) +
    fact("Free cash flow ($M)", q.free_cash_flow) +
    seriesTable("Margin trend", q.margin_trend) +
    fact("Net debt / EBITDA (GAAP)", q.net_debt_to_ebitda, mult) +
    fact("Net debt / EBITDA (covenant adj.)", q.net_debt_to_ebitda_adjusted) +
    fact("Survival capacity", q.survival_capacity) +
    fact("Interest coverage", q.interest_coverage, mult) +
    fact("Share-count trend", q.share_count_trend) +
    fact("Liquidity / covenant flags", q.liquidity_covenant_flags) +
    seriesTable("Multi-year trajectory", q.multi_year_trajectory));
}

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
const PC_NAME = 'class="num" style="background:rgba(47,111,222,.06); font-weight:600; color:var(--ink);"';
const PC_PEER = 'class="num" style="color:var(--ink-2);"';

function peerFactTable(label, s, head, body, noteText) {
  const note = noteText ? `<div class="muted" style="font-size:11px; margin-top:5px;">${escapeHtml(noteText)}</div>` : "";
  const cite = s.source_ref ? `<span class="cite">${escapeHtml(s.source_ref)}</span>` : "";
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div style="min-width:0;"><div style="overflow-x:auto;"><table class="data">${head}${body}</table></div>${note}${cite}</div></div>`;
}

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
  const head = `<thead><tr><th>Multiple</th><th class="num">Name</th><th class="num">Low</th><th class="num">Median</th><th class="num">Mean</th><th class="num">High</th></tr></thead>`;
  const body = `<tbody>${p.rows.map((r) => `<tr><td style="white-space:nowrap;">${escapeHtml(r.metric)}</td><td ${PC_NAME}>${escapeHtml(r.name)}</td><td ${PC_PEER}>${escapeHtml(r.low)}</td><td ${PC_PEER}>${escapeHtml(r.median)}</td><td ${PC_PEER}>${escapeHtml(r.mean)}</td><td ${PC_PEER}>${escapeHtml(r.high)}</td></tr>`).join("")}</tbody>`;
  return peerFactTable(label, s, head, body, p.note);
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
  const head = `<thead><tr><th>Metric</th><th class="num">Name</th><th class="num">Peer median</th></tr></thead>`;
  const body = `<tbody>${p.rows.map((r) => `<tr><td style="white-space:nowrap;">${escapeHtml(r.metric)}</td><td ${PC_NAME}>${escapeHtml(r.name)}</td><td ${PC_PEER}>${escapeHtml(r.median)}</td></tr>`).join("")}</tbody>`;
  return peerFactTable(label, s, head, body, p.note);
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
  const head = `<thead><tr><th>Peer</th><th class="num">Mkt cap</th><th>Business</th></tr></thead>`;
  const body = `<tbody>${p.rows.map((r) => `<tr><td style="white-space:nowrap;">${escapeHtml(r.name)}</td><td class="num">${escapeHtml(r.cap)}</td><td style="color:var(--ink-2);">${escapeHtml(r.desc)}</td></tr>`).join("")}</tbody>`;
  return peerFactTable(label, s, head, body, p.nameCap ? `the name: ${p.nameCap}` : "");
}

function peerComps(pc) {
  if (!pc) return "";
  return sec("Peer comps", "CIQ Company Comparable Analysis — the consensus comp, framed to RESIST. The peer-vs-name gap is never a verdict: composition + fundamental deltas let the human judge the discount EARNED (value-trap) vs RESIDUAL (overshoot). The machine never re-draws the peer set or computes an implied upside.",
    peerRosterFact("Peer set (roster · caps · business)", pc.peer_set) +
    fact("Comparability (confidence gate)", pc.comparability, null, { hi: true }) +
    peerMultiplesFact("Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)", pc.trading_multiples) +
    peerDeltasFact("Fundamental deltas (earned-vs-residual inputs)", pc.fundamental_deltas));
}

function drawdownCause(dc) {
  if (!dc) return "";
  const filings = (dc.filings || []).map((f) => `
    <div class="filing">
      <div class="fh">${escapeHtml(f.form || "8-K")} · filed ${fmtDate(f.filing_date)} <span class="muted">(for the ${escapeHtml(f.gap_date || "")} gap-down)</span></div>
      <div class="muted" style="font-size:11.5px; margin-top:2px;">items: ${escapeHtml((f.item_types || f.items || []).join(" · "))}</div>
      ${(f.events || []).map((e) => `<div class="fe">↳ ${escapeHtml(e)}</div>`).join("")}
      ${f.url ? `<div style="margin-top:5px;"><a href="${encodeURI(f.url)}" target="_blank" rel="noopener">EDGAR ${escapeHtml(f.accession || "")}</a></div>` : ""}
    </div>`).join("");
  return sec("Drawdown cause", "Why the name fell — discrete event vs gradual bleed, with the 8-Ks at the gap-downs.",
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
      </tbody></table>${io.cohort.source_ref ? `<span class="cite">${escapeHtml(io.cohort.source_ref)}</span>` : ""}</div>`
    : `<div class="fact-val muted" style="margin-top:8px;"><span class="pill unresolved">${io.cohort?.status === "missing" ? "MISSING" : "UNKNOWN"}</span> ${escapeHtml(io.cohort?.note || "no graph cohort")}</div>`;
  return sec("Idiosyncratic vs shared", "Did the name fall alone (idiosyncratic) or with its graph cohort (shared/thematic)? The graph is a research input — it gates nothing.",
    fact("Read", io.read, null, { hi: true }) +
    fact("Name 180d return", io.name_180d_return, ret) +
    fact("Market (IWM) 180d", io.market_180d_return, ret) +
    fact("Relative vs market", io.rel_vs_market, ret) +
    `<div class="fact"><div class="fact-label">Graph cohort</div><div>${cohort}</div></div>`);
}

function consensus(cc) {
  if (!cc) return "";
  return sec("Consensus context", "Light context for 'am I non-consensus' — never a driver.",
    fact("EPS revisions", cc.eps_trend) +
    fact("Revenue revisions", cc.revenue_trend) +
    fact("Revision history", cc.revision_history) +
    seriesTable("Surprise history", cc.surprise_history));
}

function synthesis(s) {
  const fence = `<div class="synth-fence"><b>The framing, not the answer.</b> A verdict-free bull/bear structure for the human to reason about — there is no recommendation, score, direction, or probability anywhere in it, by design. The human decides and logs BUY/AVOID via the CLI. <b>Citations (↳) locate each claim in a source for you to verify — cited is not verified.</b></div>`;
  if (!s) {
    return `<div class="card ds-section"><div class="ds-title">Synthesis</div>${fence}
      <div class="notice">Synthesis not assembled — mechanical layer only (CIQ inputs too thin, or the LLM step was skipped). The facts above stand on their own.</div></div>`;
  }
  const point = (p, cls) => `<div class="point ${cls}">${escapeHtml(p.claim)}${p.source_ref ? `<span class="cite">${escapeHtml(p.source_ref)}</span>` : ""}${p.cited === false ? ` <span class="uncited">⚠ uncited — does not trace to a mechanical fact</span>` : ""}</div>`;
  const dq = s.decisive_question || {};
  const twins = (s.twin_reference_cases || []).map((t) => `
    <div class="point"><b>${escapeHtml(t.name || "")}</b> — ${escapeHtml(t.outcome || "")}
      <div class="muted" style="font-size:12px; margin-top:3px;">distinguished by: ${escapeHtml(t.distinguishing_fact || "")}</div>
      <span class="cite">${escapeHtml(t.source || "")}</span></div>`).join("");
  return `<div class="card ds-section"><div class="ds-title">Synthesis · framing</div>${fence}
    ${s.evidence_balance ? `<div style="margin:6px 0; padding:8px 11px; border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:4px; font-size:13px; line-height:1.5;"><b>Evidence balance:</b> ${escapeHtml(s.evidence_balance)}</div>` : ""}
    <div class="ds-title" style="font-size:12px; margin-top:6px;">Bull — the overshoot case</div>
    ${(s.bull_points || []).map((p) => point(p, "bull")).join("") || `<div class="muted">—</div>`}
    <div class="ds-title" style="font-size:12px; margin-top:14px;">Bear — the terminal-decline case</div>
    ${(s.bear_points || []).map((p) => point(p, "bear")).join("") || `<div class="muted">—</div>`}
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
