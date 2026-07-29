// DOSSIER VIEWER — render the structured dossier.json into styled, source-bound sections.
// Assembles facts + a machine proposal SEALED until the human's verdict. Every fact shows its [n] cite.
// The synthesis is fenced as "the framing, not the answer." Read-only; verdicts are CLI-logged.
import { getDossier, getDossierIndex, getLedger, isBuyVerdict, getScenarioIndex, getScenarioCard, getMachineReads, getMonitorRow } from "../../lib/snapshots.js";
import { fmtPrice, fmtDate, fmtStamp, fmtPct, escapeHtml, DASH } from "../../lib/format.js";
// THE citation system now lives in lib/cites.js — one implementation, shared with uw-card.js
// (it was private here, which is why the underwrite card had to hardcode the inline form).
import { citeMark, withEndnotes, auditCitesInline } from "../../lib/cites.js";
import { barDomain, lineDomain, linScale, logScale, barLabelY, extent, EXHIBIT } from "../../lib/exhibit.js";
import { uwCard, uwCardParts, amendMarks } from "./uw-card.js";

// (26a) EXTRACTION VERSION — the twin of vinci/dossier/extraction_version.py. The dossier's date
// says WHEN it was built; this says WITH WHAT, which is what "are these two dossiers comparable?"
// actually turns on (#238 left the fleet holding two vintages that dated alike). Mirrored rather
// than imported — python↔JS twins cannot share a module — and PINNED in test_parity_pins.py, so a
// one-sided edit reddens the suite instead of shipping a web page that disagrees with the markdown.
// The table is append-only and the LAST row is current; a bump must say what it names.
const EXTRACTION_VERSIONS = [
  ["2026-07-28.1",
    "unusual-items surfacing in the financial summary (#238) · multiples read from the " +
    "latest close, NM rather than a stale figure (#241)"],
];
const UNSTAMPED = "unstamped";
// Normalise to ONE unstamped state — the twin of _declared() in extraction_version.py. null, "" and
// whitespace-only all mean "no version was recorded". Records are hand-edited so a blank is
// reachable, and review caught the untreated form diverging BOTH ways: label vs detail within a
// document, and this file vs the python twin on the same input.
const declaredVersion = (v) => (String(v ?? "").trim() || null);
// An absent stamp renders VISIBLY: "unstamped" and "I did not look" are different states, and only
// one of them is honest that the vintage is unknown.
const stampLabel = (v) => declaredVersion(v) || UNSTAMPED;
const stampDetail = (v) => {
  const c = declaredVersion(v);
  if (!c) return `${UNSTAMPED} — assembled before extraction versions were declared; vintage unknown`;
  const row = EXTRACTION_VERSIONS.find(([ver]) => ver === c);
  return row ? `${c} — ${row[1]}`
    : `${c} — not a version this code declares; built by a different extractor`;
};

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
document.addEventListener("click", (e) => {
  const menu = document.querySelector("#ds-pdf-menu");
  if (menu && !menu.hidden) {
    menu.hidden = true;
    const btn = document.querySelector("#ds-pdf");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }
  // the index assemble-help dropdown closes the same way; clicks inside it (the summary toggle,
  // selecting text in the panel) are ignored so native <details> behavior still opens it.
  const help = document.querySelector(".ds-help.dd[open]");
  if (help && !e.target.closest(".ds-help.dd")) help.open = false;
});

export async function render(root, params, { item, frame }) {
  const ticker = (params[0] || "").trim().toUpperCase();
  if (!ticker) return renderIndex(root, item, frame);

  const crumb = ` <span class="sep">/</span> <span class="mono">${escapeHtml(ticker)}</span>`;
  // bare: the detail page's own ticker header replaces the generic "Dossier" header block (no duplication)
  root.innerHTML = frame(item, { crumbExtra: crumb, bare: true, bodyHtml: `<div class="notice">Loading dossier…</div>` });

  // EXISTENCE COMES FROM THE COMMITTED INDEX, NEVER FROM A TRANSPORT ERROR CODE.
  // Probing for the file and reading "absent" off a 404 holds on a plain static server but NOT on
  // the authed Pages origin: functions/_middleware.js runs on EVERY request, and a miss that fails
  // inside ctx.next() falls through its bare `catch {}` to challenge() — a 401. getDossier only
  // tolerates 404, so it rethrew and this view died at "Loading dossier…". It bit exactly one name:
  // WERN, the only ticker with an underwrite but no dossier, i.e. the only page whose normal path
  // requires a MISSING file. The index lists exactly what the build emitted — ask it, don't probe.
  const [known, led] = await Promise.all([getDossierIndex(), getLedger()]);
  const d = known.includes(ticker) ? await getDossier(ticker) : null;
  // The underwrite record is read ONCE, for BOTH paths — a name may have a dossier, a record, or
  // both (IT has both; WERN only a record). Same rule as the dossier: the scenario index is the
  // source of truth for what the build emitted; never probe-and-interpret-the-error. One call site
  // keeps the "no unguarded probe can hide" pin checkable.
  const card = (await getScenarioIndex()).includes(ticker)
    ? await getScenarioCard(ticker) : null;
  // the committed monitor mark (dated; never a live fetch) — feeds the card's implied-odds line.
  // BOTH hosts pass it, so the card never differs between the dossier and theme surfaces.
  const mark = card ? await getMonitorRow(ticker) : null;
  if (!d) {
    // RICH DEGRADE — a name with a committed FIRST-CUT UNDERWRITE but no dossier renders its
    // record under explicit typing (an underwrite is NOT assembled facts, and its scenario
    // verdict is NOT a ledger verdict of record). Neither artifact → the plain notice, unchanged.
    if (card) {
      // BIND VIA THE CARD, NEVER BY `ticker` (2026-07-27). On this path `ticker` is the ROUTE key,
      // which for an archived record is `SMPL-2026-07-21` — no ledger row ever matches it, so the
      // archived page said "none yet" three inches under a masthead correctly reading "BUY —
      // closed 2026-07-22", and offered a CLI recipe with a fabricated candidate id. build.py's
      // _ledger_for_record already decided WHICH record a ledger row belongs to; re-deriving that
      // here would be a second parser of the same question. Take its answer and look the full
      // entry up by id. Real ticker for the recipe, always.
      const tk = card.ticker || ticker;
      const verdict = card.ledger && card.ledger.entryId
        ? (led.entries.find((e) => e.entryId === card.ledger.entryId) || null)
        : null;
      root.innerHTML = frame(item, { crumbExtra: crumb, bare: true, bodyHtml: `
        <div class="header-block">
          <h1 class="page-h"><span class="mono">${escapeHtml(ticker)}</span> · first analysis</h1>
          <div class="subtitle muted">underwrite record · no dossier assembled${card.underwriteDate ? ` · underwritten ${escapeHtml(card.underwriteDate)}` : ""}${card.recipeId ? ` · recipe ${escapeHtml(card.recipeId.split("_")[0])}` : ""}${card.multipleBasis ? ` · basis ${escapeHtml(card.multipleBasis)}` : ""}</div>
        </div>
        <div class="subtitle muted" style="margin:-6px 0 12px;">This is the analyst's scenario underwrite —
          not assembled facts. The full dossier is built on a re-underwrite trigger.</div>
        ${uwCard(card, { ticker: false, mark })}
        ${loggedVerdict(verdict, tk, card.underwriteDate)}
        ${assembleHelp()}` });
      return;
    }
    root.innerHTML = frame(item, { crumbExtra: crumb, bare: true, bodyHtml: `
      <div class="notice">No dossier assembled for <b>${escapeHtml(ticker)}</b> in this deploy.
      Assemble it via <span class="mono">python -m vinci dossier --ticker ${escapeHtml(ticker)}</span> (then commit the derived
      <span class="mono">dossier.json</span> to the private repo).</div>` });
    return;
  }
  // TICKER-SCOPED HERE, RECORD-SCOPED ABOVE — the asymmetry is deliberate, so don't "fix" it into
  // agreement. This path is a DOSSIER: `ticker` is a real ticker, and the Appendix's "Verdict
  // record" answers "has this NAME ever been logged?" — ledger history, which outlives any one
  // underwrite. The record-only path above answers a different question ("did THIS record make
  // that call?") and must bind by id, because its route key is not a ticker at all. Making either
  // one match the other reintroduces a bug: ticker-binding there showed a stale BUY on a reissued
  // watch record; id-binding here would blank the history the moment a record was superseded.
  const verdict = led.entries.find((e) => e.ticker === ticker) || null;
  root.innerHTML = frame(item, {
    crumbExtra: crumb, bare: true, bodyHtml: renderDossier(d, verdict, card, mark) });
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
    pdfMenu.querySelectorAll("button").forEach((b) => b.addEventListener("click", async () => {
      pdfMenu.hidden = true;
      pdfBtn.setAttribute("aria-expanded", "false");
      if (b.dataset.scope === "md") {
        // the MD download serves the COMMITTED render (frontend/dossiers/<T>.md) — the same file
        // the pipeline wrote, never a browser-side re-render: a second markdown generator in JS
        // would be a twin that silently drifts from vinci/dossier/render.py.
        const prev = b.innerHTML;
        try {
          const res = await fetch(`./dossiers/${encodeURIComponent(ticker)}.md`, { cache: "no-store" });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const url = URL.createObjectURL(new Blob([await res.text()], { type: "text/markdown" }));
          const a = document.createElement("a");
          a.href = url;
          a.download = `${ticker}-dossier.md`;
          a.click();
          URL.revokeObjectURL(url);
        } catch (err) {
          // fail LOUD in place — a silent no-op would read as "nothing to download"
          b.innerHTML = `<span class="muted">markdown unavailable — ${escapeHtml(String(err.message || err))}</span>`;
          setTimeout(() => { b.innerHTML = prev; }, 4000);
          pdfMenu.hidden = false;
        }
        return;
      }
      const full = b.dataset.scope === "full";
      document.body.classList.toggle("ds-print-full", full);
      document.body.classList.toggle("ds-print-brief", !full);
      window.print();
    }));
  }
}

// --- dossier index (no ticker) ----------------------------------------------
// The machine's evidence LEAN as a glance tag on an index card — the LABEL only ("Strongly
// bearish" / "Mixed"): the rationale stays on the Brief, where the read is shown WITH its
// reasoning. Deliberately NEUTRAL — no .pill buy/avoid vocabulary and no red/green — because a
// grid of directional colour lets the eye triage the shelf before a single fact is read, which is
// the same anchoring the sealed proposal exists to prevent. (The lean maps 1:1 onto the proposal,
// so the tag is one deterministic hop from AVOID/BUY; showing it as a COLOUR would make the shelf
// a recommendation screen.) Split by the ONE shared parser; an absent or unparseable read renders
// NOTHING at all — never a fabricated "neutral".
// ONE tag per shelf card, with the CONSTITUTION'S precedence: the human's logged verdict outranks
// the machine's read. Once a verdict is logged there is nothing left to anchor — the decision is
// made and sealed — so the verdict OF RECORD gets the colour it earns (the same buy/avoid pill the
// Brief uses). Only the still-undecided names show the machine's lean, and only in neutral ink.
// That split is the point: colour on this shelf means A HUMAN DECIDED, never that a model leaned.
function cardTag(ticker, reads, verdictBy) {
  const v = verdictBy[ticker];
  return v ? verdictTag(v) : leanTag(reads[ticker]);
}

// The human's verdict of record. AVOID_TERMINAL displays as AVOID — lossless, since BUY and
// AVOID_TERMINAL are the only two verdicts (mirrors MachineProposal.action_word on the py side).
function verdictTag(v) {
  const buy = isBuyVerdict(v.verdict);
  const at = [v.entryPrice != null ? `@ ${fmtPrice(v.entryPrice)}` : "", fmtDate(v.decidedAt)]
    .filter(Boolean).join(" · ");
  // CLOSE-AWARE (2026-07-27): a closed position never reads as a live BUY on the shelf. The word
  // of record stays — the call is still scored at its horizon, exits cannot launder the track
  // record — but the tag says it is closed, so the index cannot show a green BUY for a name the
  // book no longer holds.
  const cl = v.closed;
  const tone = cl ? "unresolved" : buy ? "buy" : "avoid";
  const tip = `your logged verdict${at ? " " + at : ""}${cl
    ? ` — closed ${cl.exitPriceAsOf || ""}${cl.exitPrice != null ? ` at ${fmtPrice(cl.exitPrice)}` : ""}`
    : ""}`;
  return `<span class="pill ${tone} ds-card-tag" title="${escapeHtml(tip)}">${
    buy ? "BUY" : "AVOID"}${cl ? " · closed" : ""}</span>`;
}

function leanTag(eb) {
  const p = splitLean(eb);
  if (!p) return "";
  const cased = p[0].charAt(0).toUpperCase() + p[0].slice(1).replace(/-/g, " ");
  return `<span class="ds-lean ds-card-tag" title="machine evidence lean — no verdict logged yet; its rationale is on the dossier, and the proposal stays sealed until you log one">${escapeHtml(cased)}</span>`;
}
async function renderIndex(root, item, frame) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading dossiers…</div>` });
  const [tickers, scenTickers, reads, led] = await Promise.all([
    getDossierIndex(), getScenarioIndex(), getMachineReads(), getLedger()]);
  // the human's logged verdicts, by ticker — the shelf's tag precedence resolves against these
  const verdictBy = {};
  for (const e of (led && led.entries) || []) if (e && e.ticker) verdictBy[e.ticker] = e;
  const uwOnly = scenTickers.filter((t) => !tickers.includes(t));

  // Repetition-reduced: identity lives ONCE per typed panel (not on every card), the search
  // placeholder is the instruction, and the assemble-help sits at the foot (on-demand tier).
  const search = `
    <div class="ds-toolbar">
      <form id="ds-search" style="display:flex; gap:10px; align-items:center; flex:1 1 380px; margin:0;">
        <input id="ds-q" type="search" placeholder="Jump to a ticker's dossier (e.g. VRRM)…" autocomplete="off"
          style="flex:1; max-width:380px; padding:9px 12px; border:1px solid var(--line-2); border-radius:8px; font-size:13px; background:var(--surface); color:var(--ink);" />
        <button type="submit" style="padding:9px 18px; border:1px solid var(--line-2); border-radius:8px; background:var(--surface); color:var(--ink); cursor:pointer; font-size:13px;">Open</button>
        <a class="foot" href="#/ranker">open a finalist from the ranker →</a>
      </form>
      ${assembleHelp(true)}
    </div>`;

  // TYPED PANELS behind segmented chips — one artifact type per panel, scalable past a single
  // scroll (100 dossiers stay one tab away from the underwrites, not one long page above them).
  const chips = `
    <div class="rt-tabs" id="ds-panels-tabs">
      <button type="button" class="rt-tab on" data-panel="dossiers">Dossiers · ${tickers.length}</button>
      <button type="button" class="rt-tab" data-panel="underwrites">First analysis · ${uwOnly.length}</button>
    </div>`;

  const dossierGrid = tickers.length
    ? `<div class="grid cols-3">${tickers.map((t) => `
        <a class="ds-index-card" href="#/dossier/${escapeHtml(t)}">
          <div class="mono" style="font-size:16px; font-weight:650;">${escapeHtml(t)}${cardTag(t, reads, verdictBy)}</div>
        </a>`).join("")}</div>`
    : `<div class="notice">No dossiers committed to this deploy yet. Assemble with <span class="mono">python -m vinci dossier</span>, then commit the derived <span class="mono">dossier.json</span> to the private repo.</div>`;
  const dossierPanel = `
    <div data-panel-body="dossiers">
      <div class="subtitle muted" style="margin:0 0 10px;">assembled facts · proposal sealed until the human logs</div>
      ${dossierGrid}
    </div>`;

  const uwGrid = uwOnly.length
    ? `<div class="grid cols-3">${uwOnly.map((t) => `
        <a class="ds-index-card uw" href="#/dossier/${escapeHtml(t)}">
          <div class="mono" style="font-size:16px; font-weight:650;">${escapeHtml(t)}
            <span class="pill conditional" style="margin-left:6px;">underwrite</span></div>
        </a>`).join("")}</div>`
    : `<div class="foot">none yet — a record lands as <span class="mono">scenarios/&lt;TICKER&gt;.json</span> and appears here.</div>`;
  const uwPanel = `
    <div data-panel-body="underwrites" hidden>
      <div class="subtitle muted" style="margin:0 0 10px;">scenario underwrite records — a screen-stage read with a recorded scenario verdict; not a dossier</div>
      ${uwGrid}
    </div>`;

  root.innerHTML = frame(item, {
    bodyHtml: `${search}${chips}${dossierPanel}${uwPanel}`,
  });
  // client-side navigation only (no write path) — jump to any ticker's dossier
  root.querySelector("#ds-search").addEventListener("submit", (e) => {
    e.preventDefault();
    const t = root.querySelector("#ds-q").value.trim().toUpperCase();
    if (t) location.hash = `#/dossier/${encodeURIComponent(t)}`;
  });
  // panel chips — client-side toggle, no route (the ds-tabs precedent)
  root.querySelectorAll("#ds-panels-tabs .rt-tab").forEach((b) => b.addEventListener("click", () => {
    root.querySelectorAll("#ds-panels-tabs .rt-tab").forEach((x) => x.classList.toggle("on", x === b));
    root.querySelectorAll("[data-panel-body]").forEach((pnl) =>
      pnl.hidden = pnl.dataset.panelBody !== b.dataset.panel);
  }));
}

// "How to assemble a dossier" — COPYABLE TEXT in the same compact, collapsible style as the
// Ingestion page's refresh block (never a button). The dashboard is read-only and runs nothing.
function assembleHelp(dd = false) {
  // dd=true -> the index-toolbar dropdown (collapsed control top-right, panel overlays on open —
  // the PDF-menu precedent); default -> the in-flow block the degrade page keeps.
  return `
    <details class="card ds-help${dd ? " dd" : ""}">
      <summary style="cursor:pointer; font-size:12.5px; font-weight:600; color:var(--ink-2);">How to assemble a dossier${dd ? "" : ` <span class="muted" style="font-weight:400;">(read-only — copy &amp; run locally, then rebuild)</span>`}</summary>
      <div class="ds-help-body">
      <div class="subtitle muted" style="margin:10px 0 8px;">Replace <span class="mono">&lt;TICKER&gt;</span> with the name. Pull the licensed CIQ first, assemble, then rebuild the mirror — the dashboard runs nothing.</div>
      <pre style="background:var(--nav-bg); color:var(--nav-ink); padding:12px 14px; border-radius:8px; font-size:12px; overflow-x:auto; margin:0; line-height:1.6;"><code>python -m vinci dossier requirements --ticker &lt;TICKER&gt;  # which licensed CIQ to pull first
python -m vinci dossier --ticker &lt;TICKER&gt;               # assemble one finalist (facts + fenced synthesis)
python -m vinci dossier --top 10                         # or: the top 10 of the ranked queue
python3 frontend/build.py                                # mirror into this dashboard, then reload</code></pre>
      </div>
    </details>`;
}


// --- (buy-side layout) a RUN of scalar facts as one stat grid — label over value, basis tag
// visible in the cell (never tooltip-only: NET vs TOTAL on adjacent leverage rows is disclosure,
// not decoration), UNKNOWN as chip + its note in visible small text (prints — the PDF is the
// record). Entries are an EXPLICIT field map ({label, s, fmt, basis}) — layout is chosen per field
// by the renderer, never by string length. Prose/composite values stay individual fact() rows.
// hero mode: the DECISION comparison register (large signed values, negatives in the danger
// tone, hairline cell separators) — for the name/market/relative strips. Reference scalars keep
// the standard register.
function factGrid(entries, { hero = false } = {}) {
  const cells = entries.filter((e) => e && e.s).map((e) => {
    const s = e.s;
    const basis = e.basis ? ` <span class="fg-basis">${escapeHtml(e.basis)}</span>` : "";
    // e.sub: a NON-caveat subline (e.g. the idio read under the relative cell) — no ⚠
    const sub = e.sub ? `<div class="fg-note">${escapeHtml(e.sub)}</div>` : "";
    if (!(s.status === "present" && s.value != null)) {
      const badge = s.status === "missing" ? "MISSING" : "UNKNOWN";
      return `<div class="fg-cell"><div class="fg-lab">${escapeHtml(e.label)}${basis}</div>
        <div class="fg-val muted"><span class="pill unresolved">${badge}</span></div>
        ${s.note ? `<div class="fg-note">${escapeHtml(s.note)}</div>` : ""}</div>`;
    }
    const val = e.fmt ? e.fmt(s.value) : escapeHtml(String(s.value));
    const caveat = s.note ? `<div class="fg-note">⚠ ${escapeHtml(s.note)}</div>` : "";
    return `<div class="fg-cell"><div class="fg-lab">${escapeHtml(e.label)}${basis}</div>
      <div class="fg-val">${val}${citeMark(s.source_ref)}</div>${caveat}${sub}</div>`;
  });
  return cells.length ? `<div class="fg-grid${hero ? " fg-hero" : ""}">${cells.join("")}</div>` : "";
}

// signed % for the HERO comparison cells — negatives carry the danger tone (the reference
// register: a −45% drawdown reads red; a positive market leg stays ink, never celebratory green)
function retHero(v) {
  const txt = fmtPct(v, { signed: true });
  return Number(v) < 0 ? `<span class="fg-neg">${txt}</span>` : txt;
}

// (buy-side layout) a card's READ — the one-line answer to the card's question, styled as the
// lead. Reads lead when they exist; a grid never holds an interpretive sentence.
function factRead(label, s, fmt) {
  if (!s || s.status !== "present" || s.value == null) return "";
  const val = fmt ? fmt(s.value) : escapeHtml(String(s.value));
  return `<div class="fg-read"><div class="fg-read-lab">${escapeHtml(label)}</div>
    <div class="fg-read-txt">${val}${citeMark(s.source_ref)}</div></div>`;
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
const _TIER_RE = /\b(?:adjusted\s+)?ebitda\b(?:\s+\w+){0,3}\s+negative\b|\badjusted\s+ebitda\b.{0,40}?(?:-\s*\$|\(\s*\$|\$\s*\(|negative)|\b(?:cash[\s-]*flow|fcf|free\s+cash\s+flow|operating\s+(?:income|cash\s*flow)|ocf)\b(?:\s+\w+){0,3}\s+turned\s+negative\b|\bcash-negative\b/i;  /* (K6, narrowed) mirrors render._TIER_REGEX[0] */
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
// (D3 hybrid, mirrors render.py _ordered_points — the twin must not drift) side-aware tier rank:
// bear keeps solvency-first (a survival fact is never demoted below a narrative point); bull leads
// with the mean-revert mechanism and demotes the balance sheet to the enabler slot.
const _BULL_RANK = { 2: 0, 3: 1, 1: 2, 4: 3, 4.5: 4, 5: 5 };
const _BEAR_RANK = { 1: 0, 2: 1, 3: 2, 4: 3, 4.5: 4, 5: 5 };
function decisiveRefs(s, side) {  // same-side decisive-question evidence refs (rule-2 verbatim)
  const dq = (s || {}).decisive_question || {};
  const ev = side === "bull" ? dq.evidence_for : dq.evidence_against;
  return new Set((ev || []).map((p) => p.source_ref));
}
function driverRefs(m) {  // operating-driver rows' refs → mechanism-bearing tiebreak
  return new Set((((m || {}).operating_drivers || {}).rows || [])
    .map((r) => r.source_ref).filter(Boolean));
}
function orderPoints(pts, side, cruxRefs, drvRefs) {
  // stable hybrid sort — bull: (crux, side-rank, mech, citation, emission);
  // bear: (side-rank, crux, mech, citation, emission). Twin of render.py `_ordered_points`.
  const rank = side === "bull" ? _BULL_RANK : _BEAR_RANK;
  const cx = cruxRefs || new Set(), dv = drvRefs || new Set();
  return (pts || []).map((p, i) => ({
    p, i, t: rank[_pointTier(p.claim)], c: _citRank(p),
    x: cx.has(p.source_ref) ? 0 : 1, m: dv.has(p.source_ref) ? 0 : 1,
  })).sort((a, b) => (side === "bull"
    ? a.x - b.x || a.t - b.t || a.m - b.m || a.c - b.c || a.i - b.i
    : a.t - b.t || a.x - b.x || a.m - b.m || a.c - b.c || a.i - b.i)).map((x) => x.p);
}

// (D2) merge 'Margin trend' + 'Multi-year trajectory' into ONE table (reuse parseSeries). Rows keyed
// by canonical label (revenue/EBITDA identical across the two → no drift); footnote fragments deduped.
function trajectoryTable(q, m = {}) {
  const label = "Trajectory (per period)";
  // (declutter P2) rows that duplicate another table on this page are dropped — revenue/EBITDA/
  // EBITDA margin are cell-identical to the financial summary; ROIC to the return-ratios RoCE row.
  // Conditional on those tables being present (a dossier without them keeps its rows here).
  const fsPresent = !!(m.financial_summary && m.financial_summary.annual
    && m.financial_summary.annual.status === "present");
  const rrPresent = !!(m.return_ratios && m.return_ratios.status === "present");
  const dup = new Set([
    ...(fsPresent ? ["Revenue ($M)", "EBITDA ($M)", "EBITDA margin"] : []),
    ...(rrPresent ? ["ROIC"] : []),
  ]);
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
    if (!byLabel.has(key) || seen.has(DISP[key]) || dup.has(DISP[key])) continue;
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
  if (!rows.length) {
    // everything deduplicated away — keep the decision-relevant footnote, skip the empty table
    return note ? `<div class="muted" style="font-size:11.5px; margin:4px 0;">${escapeHtml(note)}</div>` : "";
  }
  return dataTable(label, srcs[0].source_ref, periods.map(fmtPeriod), rows, note);
}

// `card` is the OPTIONAL committed underwrite record (frontend/scenarios/<T>.json) — passed in by
// render() because it needs a fetch; defaulted so the node smoke test keeps calling with two args.
export function renderDossier(d, verdict, card = null, mark = null) {  // exported for the module-load smoke test
  const m = d.mechanical || {};              // (renders committed dossier JSON to HTML, no DOM/fetch)
  // (3-tier) Brief (first cut) · Analysis (full dossier) · Appendix (data & audit). ONE document; the
  // tabs are client-side chrome (default Brief, no re-fetch). Mirrors the # Brief / # Analysis /
  // # Appendix top-level sections in render.py. The machine still never concludes — the Brief leads
  // with the assembled READ, never a verdict.
  // (A2) each tier renders inside withEndnotes(): its cites become [n] markers + a per-tier Sources
  // list at its end (self-contained per tab / per PDF scope).
  return header(d) + tierTabs() + `<div class="ds-tiers">
    <section class="ds-tier on" data-tier="brief">${withEndnotes("B", () => briefTier(d, verdict, m, card, mark))}</section>
    <section class="ds-tier" data-tier="analysis">${withEndnotes("A", () => analysisTier(d, m, card))}</section>
    <section class="ds-tier" data-tier="appendix">${withEndnotes("X", () => appendixTier(d, verdict, m, card))}</section>
  </div>`;
}

function tierTabs() {
  return `<div class="ds-tabs" role="tablist">
    <button class="ds-tab on" type="button" data-tier="brief" role="tab">Brief <span class="s">first cut</span></button>
    <button class="ds-tab" type="button" data-tier="analysis" role="tab">Analysis <span class="s">full dossier</span></button>
    <button class="ds-tab" type="button" data-tier="appendix" role="tab">Appendix <span class="s">data &amp; audit</span></button>
  </div>`;
}

// ANALYSIS tier — ordered by DECISION question (re-ordered 2026-07-27; the order itself is stated
// on analysisTier below). Ownership moved to the APPENDIX; the section formerly named for it
// carried only business mix and is now "Business quality". Caveats are ANALYST caveats only — the
// `primary-source:` assembly-log line renders in
// Record & reproduce, not here (process telemetry is not a caveat).
function analysisTier(d, m, card) {
  const analystCaveats = (d.caveats || d.flags || []).filter((c) => !isProcessCaveat(c));
  // (content re-order 2026-07-27) DECISION order, not provenance order. The old sequence led with
  // caveats and closed with the argument — evidence-assembly order. It now reads as the questions
  // a decision asks: what broke → what the business IS → the argument → when reality votes → what
  // it's worth → vs whom → how it's trending → what the street thinks → can it survive → what to
  // verify. Twin: render.py's analysis composition (which also drops its "Mechanical layer"
  // wrapper — a grouping by who PRODUCED the content, which this side never had).
  return drawdownIdio(m, d.reference_date)              // what broke — and did it fall alone?
    + concentration(m.concentration)                    // business quality — what this IS
    + synthesis(d.synthesis, m)                         // the argument
    + catalystCalendar(m, card)                         // when reality votes on it
    + valuation(m.valuation)                            // the ONLY home of the full multiples read
    + peerComps(m.peer_comps)                           // peer comps (per-peer grid inside)
    + trajectorySection(m.quality || {}, m)             // trajectory + the return-ratios table
    + catalystPath(m.catalyst_path, m.consensus_context, m.drawdown_cause)  // the street
    + (m.catalyst_path ? "" : consensus(m.consensus_context))  // legacy fallback only for old JSON
    + leverageSurvival(m, d.reference_date)             // balance sheet & survival
    + flagsSection(analystCaveats);                     // what to verify before the verdict
}

// (catalyst calendar, ratified 2026-07-24 · PLACEMENT B — twin of render.py _calendar_entries /
// _catalyst_calendar_lines) merged machine rows + the analyst's dated triggers, sorted by date.
function calendarEntries(m, card) {
  const out = [];
  for (const r of (((m || {}).catalyst_calendar || {}).rows || [])) {
    out.push({ date: r.expected_date, event: r.event, basis: r.date_basis,
               tests: r.tests_what, src: r.source_ref });
  }
  // camelCase: the CARD is emitted by frontend/build.py, which camelCases every key (the dossier
  // JSON beside it stays snake_case — hence `m.catalyst_calendar` above and `datedTriggers` here).
  for (const t of (((card || {}).verdict || {}).datedTriggers || [])) {
    const note = t.basis ? ` (${t.basis})` : "";
    out.push({ date: t.deadline, event: `Re-underwrite trigger: ${t.trigger}`,
               basis: "trigger-deadline",
               tests: "the analyst's own falsifier — unresolved by this date, the monitor flags re-underwrite due",
               src: `underwrite record (analyst-typed${note})` });
  }
  out.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  return out;
}
function catalystCalendar(m, card) {
  const cal = (m || {}).catalyst_calendar;
  const trig = (((card || {}).verdict || {}).datedTriggers || []);
  if (!cal && !trig.length) return "";  // pre-build JSON round-trips without a phantom card
  const entries = calendarEntries(m, card);
  const chip = (b) => `<span class="pill" style="font-size:10px; text-transform:uppercase; letter-spacing:.03em;">${escapeHtml(b)}</span>`;
  const rows = entries.map((e) => `<div class="point">
      <b>${escapeHtml(e.event)}</b> — ~<span style="font-variant-numeric:tabular-nums; font-weight:600;">${escapeHtml(e.date)}</span> ${chip(e.basis)}
      <div style="font-size:12.5px; margin-top:2px;">${escapeHtml(e.tests)}${citeMark(e.src)}</div>
    </div>`).join("");
  const empty = `<div class="muted">no dated catalysts could be assembled — a missing date is stated, never guessed</div>`;
  const qa = (cal && cal.qa_flags && cal.qa_flags.length)
    ? `<div class="muted" style="font-size:11px; margin-top:4px;">${cal.qa_flags.map(escapeHtml).join(" · ")}</div>` : "";
  return `<div class="card ds-section"><div class="ds-title">Catalyst calendar<span class="ds-route">what tests the thesis, and when</span></div>
    ${rows || empty}${qa}
    <div class="muted" style="font-size:11px; margin-top:8px;">Dates assembled from sources or the analyst's own triggers; no probabilities, no weighting, no direction — weighing catalysts is the verdict's job.</div></div>`;
}

// assembly telemetry ("primary-source: N EX-99.1 release(s) + 1 10-Q parsed (+0.3s fetch)") is a
// PROCESS log line, not an analyst caveat — it renders in the Appendix's Record & reproduce.
function isProcessCaveat(c) { return String(c).startsWith("primary-source:"); }

// APPENDIX tier — verify & reproduce: nothing here is needed to DECIDE; everything is needed to
// AUDIT. Reading guide first, then the full statements + cap-structure provenance + implied-equity
// reference + mgmt pointer (appendixBlock), then ownership & positioning (insider + short
// interest, relocated here from "The street"), and Record & reproduce closing the document. (The
// screening-context panel moved to the Brief's underwrite-detail card — user decision.)
// verdictFooter is GONE — it was a third copy of the pivot statement (beside the decision strip's
// sealed-proposal suffix and Record & reproduce's verdict row).
function appendixTier(d, verdict, m, card) {
  return howToRead()
    // (addition #1) the ANALYST's own inputs are audited first — everything below is
    // machine-assembled evidence, so "why these numbers" opens the audit tier.
    + assumptionMethodology(card)
    + appendixBlock(m)
    + positioning(m)                    // (relocation) insider + short interest, from "The street"
    + recordAndReproduce(d, verdict, card);
}

// The reading guide — the discipline/methodology language that used to repeat as per-card
// subtitles, stated ONCE. A <details>: collapsed on screen, print-expanded (T1) so the PDF still
// carries the contract.
function howToRead() {
  return `<details class="card ds-section ds-howto">
    <summary>How to read this dossier</summary>
    <ul class="kv-list" style="margin-top:8px;">
      <li>The machine assembles and cites; <b>the analyst decides</b>. Nothing in this document is a
        recommendation — the verdict of record is the human's, logged to an append-only ledger with
        a frozen entry price.</li>
      <li>The machine's proposed verdict is derived deterministically from its written assessment
        and stays <b>sealed until the analyst's verdict is recorded</b>, so it cannot anchor the
        decision. A two-sided assessment proposes nothing.</li>
      <li>Citations [n] resolve in the Sources list at the end of each tab. <b>Cited is not
        verified</b> — the reference locates the claim so you can check it.</li>
      <li>Reference values (peer-implied equity, price-implied levels) are shown <b>beside</b> the
        figures they contextualize, never differenced into an upside — the reader judges the gap.</li>
      <li>A value shown as UNKNOWN is honestly absent at the source — nothing here is imputed.</li>
    </ul></details>`;
}

// RECORD & REPRODUCE — everything needed to date, audit, or regenerate this document. Absorbs the
// old header meta (assembly stamp, model), the assembly-log caveat line, the identifiers, and the
// logged-verdict block (with its CLI how-to when no verdict exists — process documentation lives
// with process). The queued assembly-provenance stamp (STATE §5 item 1) lands here when built.
// (item 1) PANEL SPREAD — twin of panel_spread()/_panel_spread_note() in vinci/dossier/freshness.py
// and render.py. A PANEL date is an ARRIVAL (when an export was taken). A date that TRAVELS WITH A
// VALUE — an own-history band's observation date, a per-point series date — is a different object,
// and counting the second as the first inverts the ranking: SMPL reads 115d stale on the mixed
// measure and 3d, the tightest in the fleet, on arrivals alone. Exclusions pinned in test_parity_pins.
const _NOT_A_PANEL = /own_history|stock_performance|gap_date|filing_date|maturity|expected_date|dated|points/;
function panelDates(node, path = "") {
  const out = [];
  if (node && typeof node === "object" && !Array.isArray(node)) {
    for (const [k, v] of Object.entries(node)) {
      const p = path ? `${path}.${k}` : k;
      if (/as_of|asof|detail_as_of/i.test(k) && !_NOT_A_PANEL.test(p)) {
        const raw = v && typeof v === "object" && "value" in v ? v.value : v;
        const m = /(20\d\d-\d\d-\d\d)/.exec(String(raw));
        if (m) out.push([p, m[1]]);
      }
      out.push(...panelDates(v, p));
    }
  } else if (Array.isArray(node)) {
    node.forEach((v, i) => out.push(...panelDates(v, `${path}[${i}]`)));
  }
  return out;
}
function panelSpreadNote(m) {
  const ds = panelDates(m || {});
  if (ds.length < 2) return null;
  ds.sort((a, b) => (a[1] < b[1] ? -1 : 1));
  const [ok, ov] = ds[0], [nk, nv] = ds[ds.length - 1];
  const days = Math.round((Date.parse(nv + "T00:00:00Z") - Date.parse(ov + "T00:00:00Z")) / 86400000);
  return `panel spread ${days}d — oldest ${ov} (${ok}), newest ${nv} (${nk})`;
}

function recordAndReproduce(d, verdict, card = null) {
  const proc = (d.caveats || []).filter(isProcessCaveat);
  const row = (label, val) => `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div class="fact-val">${val}</div></div>`;
  return `<div class="card ds-section"><div class="ds-title">Record &amp; reproduce</div>
    <div class="subtitle muted ds-sub">Everything needed to date, audit, or regenerate this document.</div>
    ${row("Data window", `screened as of <span class="mono">${fmtDate(d.reference_date)}</span> · assembled <span class="mono">${fmtStamp(d.assembled_at)}</span>`)}
    ${row("Extraction", escapeHtml(stampDetail(d.extraction_version)))}
    ${(() => { const n = panelSpreadNote(d.mechanical); return n ? row("Panel spread", escapeHtml(n)) : ""; })()}
    ${row("Synthesis", d.synthesis
      ? `model <span class="mono">${escapeHtml(d.llm_model || "llm")}</span> — facts assembled mechanically; the synthesis frames, the analyst decides`
      : "not assembled — mechanical layer only")}
    ${row("Identifiers", `CIK <span class="mono">${escapeHtml(d.cik || DASH)}</span>${d.exchange ? ` · ${escapeHtml(d.exchange)}` : ""} : <span class="mono">${escapeHtml(d.ticker)}</span>`)}
    ${card ? row("Underwrite record", `underwritten <span class="mono">${escapeHtml(card.underwriteDate || DASH)}</span> · analyst ${escapeHtml(card.analyst || DASH)}${card.ledger && card.ledger.entryId ? ` · ledger <span class="mono">${escapeHtml(card.ledger.entryId)}</span>` : ""}${
      // LINEAGE (2026-07-27): which record this one replaced, or what replaced it. Housekeeping —
      // it helps a reader find the paperwork, not judge the name — so it sits here with the other
      // provenance rather than above the numbers.
      card.supersedes ? ` · supersedes <a href="#/dossier/${escapeHtml(card.supersedes)}">${escapeHtml(card.supersedes)}</a>` : ""}${
      card.supersededBy ? ` · superseded by <a href="#/dossier/${escapeHtml(String(card.supersededBy).split("-")[0])}">${escapeHtml(card.supersededBy)}</a>` : ""}`) : ""}
    ${proc.length ? row("Assembly log", proc.map(escapeHtml).join("; ")) : ""}
    ${row("Re-run", `<pre class="ds-rerun"><code>python -m vinci dossier --ticker ${escapeHtml(d.ticker)}</code></pre>
      <span class="muted" style="font-size:11px;">regenerates every assembled fact from the same sources; committed values change only when the sources have</span>`)}
    ${loggedVerdict(verdict, d.ticker, d.reference_date, { bare: true })}
  </div>`;
}

// --- (Brief) first-cut tier — leads with the machine READ (evidence_balance), the decisive question,
// a compact decision-data strip, and only the DECISION-THREATENING caveats. Assembles from existing
// fields, renders NO verdict; the human's logged verdict shows only as a read-only status chip (the
// machine never fills it). Mirrors _brief_lines() in vinci/dossier/render.py.
const _BRIEF_DECISION_KW = /leverage|covenant|going.?concern|maturity|wall|liquidity|dilut|solven|\bbasis\b|runway|refinanc|\bcash\b/i;

function briefVerifyFirst(caveats, limit = 2) {
  const out = [];
  for (const c of caveats || []) {
    // a RESOLVED caveat is a record of a check that PASSED — it must never demand verification
    // (surfaced by VRRM: "RESOLVED (P/E basis)" fired the warning strip).
    if (/^RESOLVED\b/i.test(c)) continue;
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

// the Brief DECISION TILES — the "why it's a candidate" metrics as a compact 2×2 grid, surfaced up in
// the teaser card (the MOFSL stat-sidebar pattern): price action (the raw 180d drawdown) + idiosyncratic
// drawdown vs the market + leverage + FCF sign (+ going-concern when flagged). Fail-honest: a tile
// renders only when its source is present. (The "Valuation (vs peers)" line moved OUT — it is already
// rendered by valuationCard; showing it here was a literal duplicate.)
// (buy-side what-happened) the Brief's decision numbers as ONE stat strip — the name/market/
// relative comparison (with the idio read as the relative cell's subline) + the two survival
// scalars. Replaces the pill tiles; same suppression discipline as the Analysis idio grid
// (an UNKNOWN market cell is dropped when the relative is present — declutter P1).
function briefTilesGrid(m) {
  const io = m.idiosyncratic_vs_shared || {};
  const q = m.quality || {};
  const marketCell = (io.market_180d_return && io.market_180d_return.status === "present")
    || !(io.rel_vs_market && io.rel_vs_market.status === "present")
    ? { label: `Market (${io.benchmark_symbol || "IWM"}) 180d`, s: io.market_180d_return, fmt: retHero }
    : null;
  const idioRead = (io.read && io.read.status === "present") ? String(io.read.value) : "";
  // the comparison is the HERO register (large, negatives red); the survival scalars ride a
  // standard reference line under it
  const heroGrid = factGrid([
    { label: "Price (180d)", s: io.name_180d_return, fmt: retHero },
    marketCell,
    { label: "Relative vs market", s: io.rel_vs_market, fmt: retHero, sub: idioRead },
  ].filter((e) => e && e.s && (e.s.status === "present" || e === marketCell)), { hero: true });
  const refGrid = factGrid([
    { label: "Net debt / EBITDA", basis: "NET", s: q.net_debt_to_ebitda, fmt: mult },
    { label: "Free cash flow", s: q.fcf_sign, fmt: (v) => escapeHtml(signWord(v)) },
  ].filter((e) => e && e.s && e.s.status === "present"));
  const gc = (((m.primary_source || {}).filing || {}).going_concern) || null;
  const gcLine = gc
    ? `<div class="fg-note" style="margin-top:4px;${gc.substantial_doubt ? " color:var(--danger-text); font-weight:600;" : ""}">Going concern: ${gc.substantial_doubt ? "⚠ substantial doubt" : "not flagged"}</div>`
    : "";
  return heroGrid || refGrid || gcLine ? `${heroGrid}${refGrid}${gcLine}` : "";
}

function briefVerdictChip(verdict) {
  if (!verdict) {
    return `<div class="brief-chip"><span class="pill unresolved">verdict — not yet logged</span>
      <span class="muted" style="font-size:11.5px;">the human logs it after reviewing the facts</span></div>`;
  }
  const isBuy = isBuyVerdict(verdict.verdict);
  // CLOSE-AWARE (2026-07-27) — same rule as the shelf tag and the card: the verdict word of
  // record stays, but it never renders as a live call once the position is closed.
  const cl = verdict.closed;
  const tone = cl ? "unresolved" : isBuy ? "buy" : "avoid";
  const meta = cl
    ? `logged @ ${fmtPrice(verdict.entryPrice)} · ${fmtDate(verdict.decidedAt)} — closed ${
        fmtDate(cl.exitPriceAsOf)}${cl.exitPrice != null ? ` @ ${fmtPrice(cl.exitPrice)}` : ""}`
    : `logged @ ${fmtPrice(verdict.entryPrice)} · ${fmtDate(verdict.decidedAt)}`;
  return `<div class="brief-chip"><span class="pill ${tone}">${escapeHtml(verdict.verdict)}${
    cl ? " · closed" : ""}</span>
    <span class="muted" style="font-size:11.5px;">${meta}</span></div>`;
}

// (Brief · tier redesign 2026-07-21, card split per user) SIX decision-ordered cards:
//   1 opener — the underwrite masthead + assessment + company identity (one read: the decision
//     headline and what the business is)
//   2 underwrite detail — scenarios table + rationale + machine proposal (sealed) + audit blocks
//     + the screening context (how the name surfaced beside how it was underwritten)
//   3 what happened — the drawdown events + the decision tiles
//   4 the case — decisive question + top bull/bear + unknowns
//   5 financial snapshot — trend exhibit + the compact annual table
//   6 valuation first-cut — trailing-range read + peers + one consensus line
// Everything needed to decide PASS vs READ DEEPER, nothing else; each card's router note names
// where its depth lives. The underwrite still LEADS (2026-07-21 order decision) and the machine's
// proposal stays SEALED until the human's verdict (the 2026-07-13 pivot — anti-anchoring intact;
// it now rides as the assessment line's suffix instead of a standing row). Mirrors _brief_lines().
function briefTier(d, verdict, m, card, mark) {
  // (brief re-order 2026-07-27) WHAT HAPPENED precedes the underwrite detail — the reader met the
  // valuation grid before the problem it values. Setup, then what it is worth. Twin of render.py.
  const parts = openerCard(d, verdict, m, card, mark)
    + whatHappened(m)
    + underwriteDetail(d, verdict, m, card, mark)
    + briefCase(d.synthesis, m)
    + financialSnapshot(m) + valuationCard(m);
  return parts.trim() ? parts : "";
}

// The machine's read + its DERIVED proposal in ONE row (the proposal is a deterministic mapping of
// this same lean — vinci/dossier/verdict.py — so a second standing row was the same fact twice).
// Sealed until the human's verdict is logged; revealed after (mirrors the md brief + ledger CLI).
function assessmentRow(d) {
  const s = d.synthesis;
  if (!s || !s.evidence_balance) return "";
  return `<div class="fact"><div class="fact-label">Assessment</div>
    <div class="fact-val">${machineReadHtml(s.evidence_balance)}</div></div>`;
}

// The opener's NARRATIVE slot (user decisions, 2026-07-21 + buy-side cover 2026-07-22): a logged
// name leads the narrative column with the ANALYST'S rationale under its own "Thesis — our
// rationale" heading, ABOVE the About block — the variant perception is the thesis, the company
// description is context. A pending name (no rationale yet) keeps the machine Assessment inside
// the About block, NEVER titled as a thesis — machine framing and the human's verdict of record
// are different voices, and the heading marks authorship. The rationale renders HERE only — the
// detail card suppresses its copy (rationale: false), so the words appear once.
function thesisBlock(card) {
  const v = (card && card.verdict) || {};
  // ONE field since 2026-07-22 — `rationale` is canonical, `rationalePlain` retired. Amendment
  // tags are set apart here for the same reason as on the card: a reader must be able to tell
  // what was recorded at the verdict from what was appended after it.
  const thesis = v.rationale;
  if (!thesis) return "";
  // ONE marker, shared with the card (uw-card.js). This block used to carry its own copy of the
  // regex, which never learned about CLASSED tags — the same amendment rendered marked on the
  // card and unmarked here. Two parsers of one string; now there is one.
  return `<div class="brief-vlab brief-eyebrow">Thesis — our rationale</div>
    <div class="brief-thesis">${amendMarks(thesis)}</div>`;
}

// (user decision) the standing proposal row is GONE from the web brief. The pivot
// MECHANISM is untouched: the proposal is still derived + sealed to the shadow ledger at assembly,
// the disposition is recorded at log time, and the reveal lives in the ledger CLI and the md
// renderer's --show-proposal peek. deriveProposal stays: it is the tested JS twin of
// vinci/dossier/verdict.py's mapping.

// CONDITIONAL caveat strip — renders ONLY when a decision-threatening caveat exists (going-concern,
// covenant, maturity wall, liquidity…). Replaces the standing "Verify first" section, which sat on
// every Brief while its real content was usually empty: an exception surfaces as an exception.
function warningStrip(d) {
  const vf = briefVerifyFirst(d.caveats || []);
  if (!vf.length) return "";
  return `<div class="uw-warn">⚠ <b>Verify before the verdict:</b> ${vf.map(escapeHtml).join("; ")}
    <span class="muted" style="font-size:11px;">— full caveats in Analysis</span></div>`;
}

// 1 — OPENER (user decision, 2026-07-21 phase-1 round): the underwrite MASTHEAD + the machine
// assessment (proposal line NOT here — it lives in the detail card) + the conditional warning +
// the company identity (one-liner · segments · geography · concentration · key figures). The
// decision headline and what-the-business-is in one opening read. Without an underwrite record
// (VRRM): the verdict chip + assessment open the card instead of the masthead.
function openerCard(d, verdict, m, card, mark) {
  const parts = card ? uwCardParts(card, { mark }) : null;
  // the card carries a REAL heading like every other Brief card; the verdict pills ride the title
  // row (the uw eyebrow that used to carry them is suppressed in split mode)
  const chips = parts && parts.chips
    ? `<span class="uw-title-chips"><span class="uw-vlab">Verdict</span>${parts.chips}</span>` : "";
  const title = `<div class="ds-title">At a glance${chips}</div>`;
  const lead = parts ? parts.head : briefVerdictChip(verdict);
  const warn = warningStrip(d);
  const about = companyInner(d, m, card);
  const crux = cruxInner(d.synthesis, m, card);
  if (!lead && !(warn + about + crux).trim()) return "";
  // one divider only (the company block's own border-top); the thesis leads the narrative column
  // inside it; the crux CLOSES the cover (the memo convention: open with the thesis, end with
  // what would change our mind).
  const body = () => `${lead}${warn}${about}${crux}`;
  return `<div class="card ds-section uw-card uw-open">${title}${withEndnotes("S", body)}</div>`;
}

// (buy-side cover) THE CRUX — the decisive question + the top unknowns, closing the cover. Pure
// render-tier: the decisive QUESTION only + an honest count-pointer (twin of render.py's crux
// block). The former key_unknowns[:2] teaser was REMOVED (2026-07-24 weather audit): the unknowns'
// set survives consecutive draws ~17% and the top-2 slots ~7% — the teaser presented weather as a
// curated "top-2", a judgment the machine never made. Fail-honest: no question → no block.
function cruxInner(s, m, card) {
  const q = s && s.decisive_question && s.decisive_question.question;
  if (!q) return "";
  const n = ((s && s.key_unknowns) || []).length;
  // (catalyst calendar) ONE line: the earliest dated entry — when the crux next gets tested.
  // Twin of render.py's crux Next-catalyst line; renders only when a dated entry exists.
  const up = calendarEntries(m, card);
  const next = up.length
    ? `<div style="font-size:12.5px; margin-top:7px; padding-top:7px; border-top:1px solid var(--line,#eee);"><b>Next catalyst:</b> ${escapeHtml(up[0].event)} ~<span style="font-variant-numeric:tabular-nums;">${escapeHtml(up[0].date)}</span> <span class="pill" style="font-size:10px; text-transform:uppercase;">${escapeHtml(up[0].basis)}</span> <span class="muted">— calendar in Analysis</span></div>`
    : "";
  return `<div class="brief-crux"><div class="brief-vlab brief-eyebrow">The crux — what decides this, and what would change our mind</div>
    <div class="brief-dq">${escapeHtml(q)}</div>
    <div class="muted" style="font-size:11px; margin-top:4px;">${n} key unknown${n === 1 ? "" : "s"} + the evidence for/against — in Analysis</div>${next}</div>`;
}

// 2 — UNDERWRITE DETAIL (user decision): the scenarios table + range rail, the analyst's rationale,
// the machine-proposal row (sealed until the verdict — the pivot, placement only), the thesis-break
// chips, the collapsed audit blocks, and the SCREENING CONTEXT (returned from the Appendix — how
// the name surfaced belongs beside how it was underwritten). Fail-honest without a record: renders
// the proposal + screening context alone when either exists.
function underwriteDetail(d, verdict, m, card, mark) {
  const screen = anchorInner(d.anchor);
  if (!card) {
    if (!screen) return "";
    return `<div class="card ds-section"><div class="ds-title">Scenario analysis<span class="ds-route">no scenario record for this name</span></div>
      ${screen}</div>`;
  }
  const title = `<div class="ds-title">Scenario analysis <span class="muted" style="font-weight:400; text-transform:none; letter-spacing:0;">${escapeHtml(card.multipleBasis || "")}</span><span class="ds-route">every assumption &amp; source recorded below</span></div>`;
  const parts = uwCardParts(card, { mark, rationale: false });
  return `<div class="card ds-section uw-card">${title}${parts.detail}${screen}</div>`;
}

// the company-identity block shared by the opener: one-liner · segments / geography / customer
// concentration · the key-figures table + 52-week relative path. CIK lives in Record & reproduce.
function companyInner(d, m, card = null) {
  const thesis = thesisBlock(card);
  const narrative = thesis ? "" : assessmentRow(d);  // unlogged names keep the machine read here
  const one = (d.business_description && d.business_description.status === "present")
    ? firstSentence(d.business_description.value) : "";
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
  const left = `${one ? `<div class="brief-oneliner">${escapeHtml(one)}</div>` : ""}` +
    narrative +
    ((c.segments && c.segments.status === "present") ? fact("Segments", c.segments) : "") +
    ((c.geographic && c.geographic.status === "present") ? fact("Geography", c.geographic) : "") +
    concLine;
  const right = briefSnapshot(d, m);
  if (!left && !right && !thesis) return "";
  // (buy-side cover) the thesis leads the narrative column; About demotes below it with its heading
  return `<div class="uw-company"><div class="brief-body">${
    (thesis || left)
      ? `<div class="brief-narrative">${thesis}${
        left ? `<div class="brief-vlab brief-eyebrow">About the company</div>${left}` : ""}</div>`
      : ""}${right}</div></div>`;
}

// 3 — WHAT HAPPENED: the drawdown events + the decision tiles. The Brief used to show the raw
// drawdown % with no WHY — but the fund's whole question (overshoot vs terminal) starts from what
// broke, so the shape belongs on page 1. The narrative names the EVENTS; the tiles carry the
// NUMBERS (never both in one surface). Full event log + filings stay in Analysis.
function whatHappened(m) {
  const dc = m.drawdown_cause || {};
  const shape = (dc.shape && dc.shape.status === "present") ? fact("Shape", dc.shape, fmtShape) : "";
  const tiles = briefTilesGrid(m);
  if (!shape && !tiles) return "";
  // (content relocation 2026-07-24) title matches the contents: the tiles carry survival triage
  // (net debt/EBITDA, FCF, going concern) beside the event. Twin of render.py.
  return `<div class="card ds-section"><div class="ds-title">What happened — and can it survive?<span class="ds-route">full event log in Analysis</span></div>
    ${shape}${tiles}</div>`;
}

// (log-a) SCREENING ANCHOR — the committed R1 anchor block (vinci/dossier/anchor.py), read-only.
// A mechanical re-rate of the name to its OWN-history median multiple on a NAIVE reported median
// margin: an ATTENTION FILTER, never a verdict and never a target — it applies no structural
// adjustment. Absent anchor → renders nothing, so pre-anchor dossiers are untouched.
function anchorInner(a) {
  if (!a) return "";
  const conf = (c) => `<span class="pill${c === "firm" ? "" : " conditional"}">${escapeHtml(c || "—")}</span>`;
  const row = (label, val, note, { prose = false } = {}) =>
    `<tr><td>${escapeHtml(label)}</td><td class="${prose ? "uw-screen-m" : "num mono"}">${val}</td><td class="muted">${note}</td></tr>`;
  const mg = a.margin, mu = a.multiple;
  const base = a.anchor_base_value_per_share;
  const methodName = String(a.recipe_hint || "").startsWith("R1")
    ? "mid-cycle margin × the median multiple of its own history" : (a.recipe_hint || "—");
  const rows = [
    row("Method", escapeHtml(methodName), a.applicable ? "applicable" : "NOT applicable",
        { prose: true }),
    mg ? row("Mid-cycle margin", mg.value != null ? `${(mg.value * 100).toFixed(1)}%` : "—",
             `${mg.anchor_years}y history · ${conf(mg.confidence)}`) : "",
    mu ? row("Median multiple, own history", mu.value != null ? `${mu.value.toFixed(1)}x` : "—",
             `${mu.history_quarters} closes · ${conf(mu.confidence)} · ${escapeHtml(a.multiple_basis || "")}`) : "",
    base != null ? row("Screen value / share", `$${base.toFixed(2)}`,
                       `spot-independent · EV/EBIT ${a.anchor_ev_ebit != null ? a.anchor_ev_ebit.toFixed(1) : "—"}x`) : "",
    row("Overall confidence", conf(a.overall_confidence), ""),
  ].join("");
  const dq = a.data_quality
    ? `<div class="notice" style="margin-top:8px;"><b>data_quality: ${escapeHtml(a.data_quality)}</b>${
        (a.data_quality_detail || []).map((x) =>
          `<div class="mono" style="font-size:11px;">${escapeHtml(x)}</div>`).join("")}</div>` : "";
  const why = a.reason ? `<div class="muted" style="margin-top:6px;">${escapeHtml(a.reason)}</div>` : "";
  return `<div class="uw-screen"><div class="ds-title" style="font-size:12px; margin-top:14px;">Screening context — how this name surfaced<span class="ds-route">not a verdict</span></div>
    <div class="subtitle muted" style="margin:2px 0 8px;">A mechanical re-rate to the median multiple of this name's own trading history, on its naive reported median margin. An attention filter only — it applies no structural adjustment, so a cheap-looking screen still has to survive the full bear/base/bull underwrite.</div>
    <table class="data"><tbody>${rows}</tbody></table>${dq}${why}</div>`;
}

// (tier redesign) scenarioPanel is GONE — the Brief composes uwCardParts() directly: the masthead
// opens card 1 beside the company identity; the legs/audit detail forms card 2.

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


// THE one shared lean parser (mirrors vinci/dossier/verdict.py split_lean) — "{lean} — {why}" →
// [lean, rest] (both trimmed) else null. machineReadHtml AND deriveProposal both consume it; two
// divergent copies of this regex is the "two parsers of one string" drift the shared-parser rule kills.
function splitLean(eb) {
  const m = /^\s*([A-Za-z][A-Za-z\- ]*?)\s*[—–-]\s+([\s\S]+)$/.exec(eb || "");
  return m ? [m[1].trim(), m[2].trim()] : null;
}

function machineReadHtml(eb) {
  const p = splitLean(eb);
  if (!p) return escapeHtml(eb || "");
  const [lean, rest] = p;
  const l = lean.toLowerCase();
  const col = l.includes("bear") ? "var(--danger)" : l.includes("bull") ? "var(--live)" : "var(--ink-2)";
  const cased = lean.charAt(0).toUpperCase() + lean.slice(1);
  return `<b class="brief-lean" style="color:${col}">${escapeHtml(cased)}</b> — ${escapeHtml(rest)}`;
}

// The machine's PROPOSED verdict (2026-07-13 pivot) — the JS mirror of vinci/dossier/verdict.py:
// a face-validity-frozen mapping over the committed lean label; deterministic, NEVER outcome-tuned,
// never the LLM. "mixed" proposes NOTHING (a two-sided read is the human's call — no coin-flip);
// an absent/unparseable/unrecognized read proposes nothing, fail-honest. The human's logged
// confirm/override (the ledger) is the verdict of record. AVOID_TERMINAL displays as AVOID.
const PROPOSAL_BY_LEAN = { "strongly-bearish": "AVOID", "strongly-bullish": "BUY", "mixed": null };
function deriveProposal(eb) {
  if (!eb || !String(eb).trim()) return { action: null, note: "no machine read on this dossier" };
  const p = splitLean(eb);
  if (!p) return { action: null, note: "machine read did not parse — no proposal" };
  const label = p[0], reason = p[1];
  const key = label.toLowerCase().replace(/\s+/g, "-");
  // Object.hasOwn, NOT `key in` — `in` walks Object.prototype, so lean 'constructor'/'toString'
  // would falsely resolve to a garbage action (parity break vs Python's plain-dict membership).
  if (!Object.hasOwn(PROPOSAL_BY_LEAN, key)) {
    return { action: null, lean: label, note: `unrecognized lean '${label}' — no proposal (fail-honest)` };
  }
  const action = PROPOSAL_BY_LEAN[key];
  if (!action) return { action: null, lean: label, note: "evidence two-sided (mixed) — the human's call" };
  return { action, lean: label, reason };
}

// (tier redesign) teaserCard is GONE: its one-liner + snapshot sidebar merged into companyInner,
// its assessment/proposal rows folded into the decision strip (assessmentRow), its verdict slot was
// redundant three ways (the uw-card's status chip, the ENTRY masthead cell, and the card foot), and
// its tiles moved to whatHappened beside the drawdown shape they qualify.

// the key-figures sidebar — a label|value table of the scalar facts (exchange · CMP · market cap ·
// 52-wk · shares · book value/sh). CIK moved to Record & reproduce (an identifier, not a decision
// figure). Fail-honest: a row is dropped when its source is absent (e.g. AORT has no
// Book Value/Share row in its export → no Book/sh row, never a guess).
function briefSnapshot(d, m) {
  const si = m.stock_info || {};
  const ok = (f) => f && f.status === "present" && f.value != null;
  const rows = [];
  const push = (label, val) => { if (val) rows.push(`<tr><td>${label}</td><td>${val}</td></tr>`); };
  if (ok(si.price)) push("CMP", `$${si.price.value.toFixed(2)}${si.as_of ? ` <span class="muted">(${escapeHtml(si.as_of)})</span>` : ""}${si.price.note ? ` <span class="pill unresolved" title="${escapeHtml(si.price.note)}">STALE</span>` : ""}`);
  // (item 1, clause (e)) The cap is the CIQ comps panel's and the price is the EOD store's;
  // on all 11 committed dossiers they disagree. An unlabelled cap beside a live price reads
  // as one moment when it is two. Twin of _brief_snapshot() in render.py.
  if (ok(si.market_cap)) {
    const capAsOf = String((((m || {}).valuation || {}).implied_expectations
      || {}).multiples_as_of || "").slice(0, 10);
    const siAsOf = String(si.as_of || "").slice(0, 10);
    const vint = capAsOf && capAsOf !== siAsOf ? ` (${escapeHtml(capAsOf)})` : "";
    push("Market cap", fmtCap(si.market_cap.value) + vint);
  }
  if (ok(si.low_52w) && ok(si.high_52w)) push("52-wk range", `$${si.low_52w.value.toFixed(2)}–$${si.high_52w.value.toFixed(2)}`);
  if (ok(si.shares_out)) push("Shares out", fmtShares(si.shares_out.value));
  if (ok(si.book_value_ps)) push("Book / sh", `$${si.book_value_ps.value.toFixed(2)}`);
  // the 52-week stock-vs-benchmark path sits BELOW the scalar table (MOFSL-style sidebar) — web-only.
  const chart = stockPerfExhibit(m.stock_performance);
  if (!rows.length && !chart) return "";
  const table = rows.length ? `<table class="brief-snap-t"><tbody>${rows.join("")}</tbody></table>` : "";
  const kf = rows.length ? `<div class="brief-vlab brief-eyebrow">Key figures</div>` : "";
  // no identity line here — the page h1 two inches above already says it (was a literal duplicate)
  return `<div class="brief-snap">
    ${kf}${table}${chart}</div>`;
}

// (tier redesign) setupCard is GONE — one line does not earn a card; the decisive question now
// leads "The case". companyCard is GONE — merged into companyInner above.

// 4 — THE CASE: the decisive question LEADS (it framed a card of its own — one line does not earn
// a card), then top-3 bull / top-3 bear (evidence-weighted, same order as Analysis) + top-3 key
// unknowns. Labels state the claim, not the house shorthand: "the decline is overdone" /
// "the decline is real" (was "overshoot" / "terminal"). Full argument lives in Analysis.
function briefCase(s, m) {
  if (!s || (!(s.bull_points || []).length && !(s.bear_points || []).length)) return "";
  // (buy-side cover) the decisive question + key unknowns moved to the opener's CRUX block — this
  // card carries the condensed bull/bear alone, so the question renders once per tier.
  const pt = (p, cls) => `<div class="point ${cls}">${escapeHtml(p.claim)}${citeMark(p.source_ref)}</div>`;
  const dv = driverRefs(m);
  const bulls = orderPoints(s.bull_points, "bull", decisiveRefs(s, "bull"), dv).slice(0, 3).map((p) => pt(p, "bull")).join("") || `<div class="muted">—</div>`;
  const bears = orderPoints(s.bear_points, "bear", decisiveRefs(s, "bear"), dv).slice(0, 3).map((p) => pt(p, "bear")).join("") || `<div class="muted">—</div>`;
  return `<div class="card ds-section"><div class="ds-title">The case<span class="ds-route">full argument in Analysis</span></div>
    <div class="brief-case">
      <div><div class="ds-title" style="font-size:12px; color:var(--pos-text);">Bull case — the decline is overdone</div>${bulls}</div>
      <div><div class="ds-title" style="font-size:12px; color:var(--danger);">Bear case — the decline is real</div>${bears}</div>
    </div></div>`;
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

// BRIEF stock-performance exhibit — the 52-week rebased price path, the name vs its cap-band benchmark,
// both indexed to 100 at the window start (mechanical.stock_performance). A COMPACT sidebar exhibit:
// it reuses the shared design LANGUAGE (EXHIBIT.fs fonts · halo · margin · the honest lineDomain /
// linScale math from lib/exhibit.js) at a brief-snapshot-column size — NOT the wSingle/wDual main-
// exhibit canvas. It VISUALIZES the same EOD closes the G2 idio comparison already cites (assemble,
// never conclude; no trendline/projection). Fail-loud: <2 points → no exhibit; a null benchmark point
// breaks that line, never bridged. Provenance is the JSON source_ref (its brief-tier siblings carry no
// citeMark) — never an inline caption (the endnote-cite guard).
const _MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const _monYr = (iso) => { const p = String(iso).split("-"); return `${_MON[(+p[1]) - 1] || "?"} '${(p[0] || "").slice(2)}`; };

function stockPerfExhibit(sp) {
  if (!sp || !Array.isArray(sp.points) || sp.points.length < 2) return "";
  const pts = sp.points;
  const nameS = pts.map((p) => (p && Number.isFinite(p.name) ? p.name : null));
  const benchS = pts.map((p) => (p && Number.isFinite(p.benchmark) ? p.benchmark : null));
  if (!nameS.some((v) => v != null)) return "";
  const { fs, halo } = EXHIBIT;  // shared design language (lib/exhibit.js) — compact frame below
  // compact sidebar frame — this sits inside .brief-snap, so it is NOT stretched to the main canvas.
  const W = 285, H = 154, padL = 27, padR = 6, cy0 = 30, cy1 = 112, px0 = padL, px1 = W - padR;
  // A rebased-INDEX series (base 100), not a return series — its threshold is 100, not 0. Every series
  // starts at exactly 100, so `extent` always includes it; zoom to the real data range (padded) instead
  // of lineDomain's floor-at-0, which would waste the whole 0..min band. No fabrication: extent is the
  // observed min/max, never bridged.
  const ex = extent([...nameS, ...benchS]);
  if (!ex) return "";
  const pad = Math.max((ex[1] - ex[0]) * 0.1, 6), dom = { lo: ex[0] - pad, hi: ex[1] + pad };
  const sx = linScale(0, pts.length - 1, px0, px1), sy = linScale(dom.lo, dom.hi, cy1, cy0);
  const line = (series, color, w) => {
    const seg = series.map((v, i) => (v == null ? null : `${sx(i).toFixed(1)},${sy(v).toFixed(1)}`)).filter(Boolean).join(" ");
    return seg ? `<polyline points="${seg}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round"/>` : "";
  };
  const nameCol = "var(--accent)", benchCol = "var(--ink-3)";
  // the 100 rebase anchor — a faint dashed reference, the same grammar as the ratio panels' zero line.
  const base = (dom.lo <= 100 && 100 <= dom.hi)
    ? `<line x1="${px0}" y1="${sy(100).toFixed(1)}" x2="${px1}" y2="${sy(100).toFixed(1)}" stroke="var(--line-2)" stroke-dasharray="3 2"/>` : "";
  const yLab = `<text x="${px0 - 4}" y="${cy0 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(dom.hi)}</text>`
    + `<text x="${px0 - 4}" y="${cy1 + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${Math.round(dom.lo)}</text>`;
  const xLab = `<text x="${px0}" y="${cy1 + 14}" font-size="${fs.xlabel}" text-anchor="start" fill="var(--ink-3)">${_monYr(pts[0].date)}</text>`
    + `<text x="${px1}" y="${cy1 + 14}" font-size="${fs.xlabel}" text-anchor="end" fill="var(--ink-3)">${_monYr(pts[pts.length - 1].date)}</text>`;
  const sym = escapeHtml(sp.name_symbol || "Name"), bsym = escapeHtml(sp.benchmark_symbol || "IWM");
  const nr = fmtPct(sp.name_return, { signed: true });
  const br = (typeof sp.benchmark_return === "number") ? fmtPct(sp.benchmark_return, { signed: true }) : DASH;
  // bottom legend — mark + symbol + windowed return in each series' colour (the returnRatios grammar).
  const ly = H - 5;
  const leg = `<g font-size="${fs.legend}">`
    + `<circle cx="${px0 + 3}" cy="${ly - 3}" r="2.6" fill="${nameCol}"/><text x="${px0 + 10}" y="${ly}" fill="var(--ink-2)">${sym} <tspan fill="${nameCol}" font-weight="600">${nr}</tspan></text>`
    + `<circle cx="${px0 + 120}" cy="${ly - 3}" r="2.6" fill="${benchCol}"/><text x="${px0 + 127}" y="${ly}" fill="var(--ink-2)">${bsym} <tspan fill="${benchCol}" font-weight="600">${br}</tspan></text>`
    + `</g>`;
  return `<div class="ds-exhibit brief-perf" style="margin:14px 0 0;">
    <svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px; display:block;" role="img" aria-label="52-week price performance, ${sym} versus ${bsym}, rebased to 100">
      <text x="0" y="15" font-size="${fs.panel}" font-weight="600" fill="var(--ink-2)">Stock performance <tspan font-size="${fs.xlabel}" fill="var(--ink-3)" font-weight="400">· 52-wk, =100</tspan></text>
      ${yLab}${base}${xLab}${line(benchS, benchCol, 1.4)}${line(nameS, nameCol, 2)}${leg}
    </svg>
  </div>`;
}

// 5 — FINANCIAL SNAPSHOT: revenue / EBITDA / EBITDA-margin trajectory (from financial_summary.annual).
// The BRIEF's window over the (now full-history) annual series: the last 4 actual fiscal years +
// LTM + every consensus column. Curated at the RENDER layer — the record and the Appendix keep
// every exported year; a first cut that ran ten columns wide would stop being a first cut.
const _BRIEF_FY = 4;
function briefWindow(v) {
  const cols = v.columns || [], isE = v.is_estimate || [];
  const keep = cols.map((c, i) => ({ c, i }))
    .filter(({ c, i }) => isE[i] || /^LTM/i.test(String(c)));           // LTM + estimates always
  const actual = cols.map((c, i) => ({ c, i }))
    .filter(({ c, i }) => !isE[i] && !/^LTM/i.test(String(c)));
  const idx = [...actual.slice(-_BRIEF_FY), ...keep].map((x) => x.i).sort((a, b) => a - b);
  return { idx, hidden: Math.max(0, actual.length - _BRIEF_FY) };
}

function financialSnapshot(m) {
  const fsa = (m.financial_summary || {}).annual;
  if (!fsa || fsa.status !== "present" || !fsa.value) return "";
  const want = ["Revenue ($M)", "Revenue growth", "EBITDA ($M)",
    "EBITDA margin", "EBIT ($M)", "Net income ($M)", "EPS (GAAP, dil.)", "FCF ($M)"];
  // (P1 brief fix, 2026-07-28) static labels PLUS any row flagged material at assembly. Surfacing
  // the writedown into the appendix closed P1's data half but not the harm — a brief-only reader
  // still never met a 43%-of-market-cap charge. Only rows over the floor, and the flag is computed
  // ONCE in the extractor: this renderer reads it, never recomputes. Twin: render._brief_fin_lines.
  const rows = (fsa.value.rows || []).filter((r) => want.includes(r.label) || r.material === true);
  const { idx, hidden } = briefWindow(fsa.value);
  const cols = idx.map((i) => (fsa.value.columns || [])[i]);
  if (!cols.length || !rows.length) return "";
  const isE = fsa.value.is_estimate || [], ec = (i) => (isE[i] ? " est-col" : "");  // (P3) shade E cols
  const head = `<tr><th></th>${idx.map((i) => `<th class="num${ec(i)}">${escapeHtml(String(fsa.value.columns[i]))}</th>`).join("")}</tr>`;
  const body = rows.map((r) => `<tr><td>${escapeHtml(r.label)}</td>${idx.map((i) => `<td class="num mono${ec(i)}">${escapeHtml(String((r.cells || [])[i]))}</td>`).join("")}</tr>`).join("");
  // (tier redesign) the return-ratios EXHIBIT stays on the first cut; its per-period TABLE is
  // depth and moved to the Analysis trajectory section. Fail-honest fallback unchanged: a name
  // without the Ratios panel keeps the committed latest-period line.
  const rr = m.return_ratios;
  const ratios = (rr && rr.status === "present" && rr.value && Array.isArray(rr.value.rows) && rr.value.rows.length)
    ? returnRatiosExhibit(rr)
    : (m.key_ratios && m.key_ratios.status === "present") ? fact("Key ratios (latest)", m.key_ratios) : "";
  // the exhibit above spans the FULL series, so the note points at the TABLE's window only
  const more = hidden
    ? `<div class="muted" style="font-size:11px; margin-top:4px;">table shows the last ${
        _BRIEF_FY} fiscal years · ${hidden} earlier ${hidden === 1 ? "year is" : "years are"
        } charted above and tabulated in the Appendix</div>` : "";
  return `<div class="card ds-section"><div class="ds-title">Financial snapshot<span class="ds-route">full statements in Appendix</span></div>
    ${revEbitdaExhibit(fsa)}
    <table class="data">${`<thead>${head}</thead><tbody>${body}</tbody>`}</table>
    ${citeMark(fsa.source_ref)}${more}${ratios}</div>`;
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
  const single = bands.length === 1;
  // SHARES revEbitda / return-ratios' EXHIBIT frame (canvas / y-band / fonts / halo / margin) so every
  // dossier exhibit reads as ONE system: same 760×276 (single metric → 430, NOT stretched), same
  // cy0/cy1 plot band, same panel columns (44→366 | 412→748), title/panel/axis/label fonts, and halo.
  // The axis + vintage metadata (this chart's extra info) sits BELOW the SVG as a muted caption, so the
  // in-SVG frame stays identical to the others (title-only, no subtitle band eating into cy0).
  const { H, cy0, cy1, fs, halo } = EXHIBIT;
  const W = single ? EXHIBIT.wSingle : EXHIBIT.wDual;
  const geo = single ? [[44, 366]] : [[44, 366], [412, 748]];
  const yr = (s) => { const y = /(\d{4})/.exec(s || ""); return y ? "'" + y[1].slice(2) : ""; };

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
    // trailing-history reference levels: min / avg (DASHED) / max — grey, value at the y-axis. Value-only
    // (no "avg" prefix) so the label fits the shared left inset; the dashed line marks the average.
    const ref = (v, dash, tag) => `<line x1="${x0}" y1="${sc(v)}" x2="${x1}" y2="${sc(v)}" stroke="var(--line-2)"${dash ? ' stroke-dasharray="3 3"' : ""}/><text x="${x0 - 4}" y="${sc(v) + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${tag}</text>`;
    let s = `<text x="${x0}" y="${cy0 - 9}" font-size="${fs.panel}" font-weight="600" fill="var(--ink-2)">${escapeHtml(label)}</text>`;
    s += `<text x="${x1}" y="${cy0 - 9}" font-size="${fs.xlabel}" text-anchor="end" fill="var(--ink-3)">${Math.round(b.percentile * 100)}%ile${lowConf ? "*" : ""} · ${b.n_closes}q</text>`;
    s += ref(b.high, false, b.high.toFixed(1)) + ref(b.mean, true, b.mean.toFixed(1)) + ref(b.low, false, b.low.toFixed(1));
    s += `<polyline points="${pts.map((p, i) => `${px(i)},${sc(p[1])}`).join(" ")}" fill="none" stroke="var(--accent)" stroke-width="1.8"/>`;
    // current = the last close: DIRECTIONAL color (below/above its own trailing range is a FACT) + value;
    // neutral grey when low-confidence. The human still judges cheap-vs-dear.
    const ci = pts.length - 1, cx = px(ci), cyv = sc(b.current);
    const col = lowConf ? "var(--ink-3)" : b.current < b.low ? "var(--danger)" : b.current > b.high ? "var(--live)" : "var(--accent)";
    const caret = b.current < b.low ? "▼" : b.current > b.high ? "▲" : "●";
    s += `<circle cx="${cx}" cy="${cyv}" r="3.5" fill="${col}" stroke="var(--surface)" stroke-width="1.2"/>`;
    s += `<text x="${cx}" y="${cyv - 8}" font-size="${fs.point}" text-anchor="end" fill="${col}" font-weight="700" ${halo}>${caret} ${b.current.toFixed(1)}x</text>`;
    s += `<text x="${x0}" y="${cy1 + 16}" font-size="${fs.xlabel}" fill="var(--ink-3)">${escapeHtml(yr(pts[0][0]))}</text>`;
    s += `<text x="${x1}" y="${cy1 + 16}" font-size="${fs.xlabel}" text-anchor="end" fill="var(--ink-3)">${escapeHtml(yr(pts[ci][0]))}</text>`;
    return s;
  };

  // "log scale" only claimed when EVERY panel is actually log — the axis is chosen per-panel (useLog
  // above), falling back to linear on a non-positive multiple. Mirrors panel()'s vals.every(v > 0) so
  // the label can't drift from the transform.
  const allLog = bands.every((b) => b.series.filter((p) => p && p[1] != null).map((p) => p[1])
    .concat([b.low, b.high, b.mean]).every((v) => v > 0));
  const meta = `each quarter's close vs its trailing avg (dashed) &amp; range${allLog ? " · log scale" : ""}${bands[0].as_of ? " · as-of " + escapeHtml(bands[0].as_of) : ""}`;
  // no inline "Source:" caption — the Multiples source is already cited at the card level (range_position's
  // endnote → the tier's Sources list). Exhibits cite via endnotes, never a duplicate inline caption.
  return `<div class="ds-exhibit" style="margin:${EXHIBIT.margin};">
    <svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px; display:block;" role="img" aria-label="Valuation multiples vs their own trailing range">
      <text x="44" y="22" font-size="${fs.title}" font-weight="600" fill="var(--ink)">Multiple vs its own trailing range</text>
      ${bands.map((b, i) => panel(b, geo[i][0], geo[i][1])).join("")}
    </svg>
    <div class="muted" style="font-size:11px; margin-top:2px;">${meta}</div>
    ${anyLowConf ? `<div class="muted" style="font-size:10px; margin-top:1px;">* fewer than ${LOW_CONF_CLOSES} closes — low-confidence read; current shown in neutral, not red/green.</div>` : ""}
  </div>`;
}

// 6 — VALUATION, FIRST CUT: the trailing-range read + the peers read + ONE consensus line (enough
// to know whether the view is variant, no more — the street's full machinery lives in Analysis).
// The forward-multiple ladder moved to Analysis (its only home) and the implied-equity table to
// the Appendix (its only home) — each appeared in two or three tiers before.
function valuationCard(m) {
  const cross = (m.valuation && m.valuation.cross_sectional) ? fact("vs peers", m.valuation.cross_sectional) : "";
  const comp = (m.peer_comps && m.peer_comps.comparability) ? fact("Comparability", m.peer_comps.comparability) : "";
  const rng = (m.valuation && m.valuation.range_position && m.valuation.range_position.status === "present")
    ? fact("vs own trading history", m.valuation.range_position) : "";
  const cs = (m.catalyst_path || {}).consensus_stats;
  // (content relocation 2026-07-24) framed as CONTRAST — the rows above are OUR read, this is the
  // street's. Listing it as a peer of our own valuation blurs the variant view. Twin of render.py.
  const cons = (cs && cs.status === "present")
    ? fact("The street, for contrast (target · ratings)", cs) : "";
  if (!cross && !comp && !rng && !cons) return "";
  return `<div class="card ds-section"><div class="ds-title">Valuation — first cut<span class="ds-route">full multiples, implied levels &amp; the forward ladder in Analysis</span></div>${rng}${ownHistoryExhibit(m)}${cross}${comp}${cons}</div>`;
}

// --- (declutter P3) display transforms — JS twins of render.py's _fmt_* helpers. Display-ONLY:
// dossier.json is untouched; each transform is mirrored across the two renderers.
function fmtInsider(v) {
  const m = /other ((?:[A-Z]×\d+\/?)+)$/.exec(String(v));
  if (!m) return String(v);
  const total = (m[1].match(/×(\d+)/g) || []).reduce((s, x) => s + Number(x.slice(1)), 0);
  return String(v).slice(0, m.index) + `other filings ${total}`;
}

function fmtCustomers(v) {
  const text = String(v);
  if (!text.includes("src:")) return text;
  const n = text.split(";").filter((x) => x.trim()).length;
  return `${n} mapped client relationship(s) — roster in JSON; concentration %, when disclosed, `
    + "is the 10-Q read above";
}

function fmtShape(v) { return String(v).replace(/\s*\(\d\.\d{2}\)/g, ""); }

// (event study) parse the committed shape "discrete gap-downs — DATE cause; DATE cause" into
// per-gap [date, cause] rows; null (→ fall through to the run-on) for a gradual-bleed read or any
// shape that doesn't parse. Cosmetic; twin of render.py _gap_list.
function gapList(shape) {
  const m = /^discrete gap-downs — (.+)$/.exec(String(shape).trim());
  if (!m) return null;
  const rows = [];
  for (const part of m[1].split("; ")) {
    const dm = /^(\d{4}-\d{2}-\d{2})\s+(.+)$/.exec(part.trim());
    if (!dm) return null;
    rows.push([dm[1], dm[2].trim()]);
  }
  return rows.length ? rows : null;
}

// nearest point index to a gap date — fallback for pre-daily committed JSON only (the marker still
// lands near the right week); the % derivation below never uses it (exact-date or nothing).
function nearestPtIdx(pts, dateStr) {
  const t = Date.parse(dateStr);
  let best = 0, bd = Infinity;
  for (let i = 0; i < pts.length; i++) {
    const d = Math.abs(Date.parse(pts[i].date) - t);
    if (d < bd) { bd = d; best = i; }
  }
  return best;
}

// Is bDate the immediately-next TRADING day after aDate? 1 calendar day (adjacent weekday), or a
// Fri→Mon weekend (3 days, aDate a Friday → getUTCDay()===5). Any other spacing — 2 (a weekday was
// skipped ⇒ a downsampled step≥2 series), 4 (skip/post-holiday), 7 (weekly) — can't be proven
// consecutive. The ONE definition of "a true 1-day move", shared by the gap-% derivation AND the
// chart's pre-window drop detector so the two can never drift apart (mirrors render.py's rule).
export function isNextTradingDay(aDateStr, bDateStr) {  // exported for the equivalence test
  const spacing = Math.round((Date.parse(bDateStr) - Date.parse(aDateStr)) / 86400000);
  return spacing === 1 || (spacing === 3 && new Date(aDateStr).getUTCDay() === 5);
}

// The exact 1-day close-to-close move at `dateStr`, derived from consecutive DAILY perf points —
// the detector's own formula on the same closes (a rebased-index ratio IS the close ratio). null
// when the series doesn't carry the date, or the previous point isn't the prior trading day
// (old weekly-downsampled JSON): REFUSE rather than misstate a multi-day move as the 1-day gap.
// Twin of render.py _gap_pct_from_perf.
export function gapPctFromPerf(sp, dateStr) {  // exported for the py-twin equivalence test
  const pts = (sp && sp.points) || [];
  const i = pts.findIndex((p) => p && p.date === dateStr);
  if (i <= 0) return null;
  const a = pts[i - 1], b = pts[i];
  if (!a || !Number.isFinite(a.name) || !Number.isFinite(b.name) || a.name <= 0) return null;
  // b must be the immediately-next trading day (shared rule), else a multi-day move would be
  // misread as the 1-day gap — refuse (twin of render.py _gap_pct_from_perf).
  if (!isNextTradingDay(a.date, b.date)) return null;
  return b.name / a.name - 1;
}
const fmtGapPct = (p) => `${p > 0 ? "+" : "−"}${Math.abs(p * 100).toFixed(1)}%`;
const _monDay = (iso) => { const p = String(iso).split("-"); return `${_MON[(+p[1]) - 1] || "?"} ${+p[2]}`; };
const _circled = (n) => (n >= 1 && n <= 20 ? String.fromCharCode(0x245F + n) : `#${n}`);

// (event study) the "what broke" price chart — name vs benchmark rebased to 100 (the committed
// stock_performance series), gridlined axes, NUMBERED gap markers staggered on collision, hollow
// markers for real ≤threshold drops BEFORE the detector window + the window boundary (both only
// when the dossier carries the detector params — no frontend magic numbers). Returns {svg, preDrops}
// ({svg:"", preDrops:[]} when the series is absent) — preDrops feeds the ledger's honesty footnote.
export function drawdownChart(sp, rows, det) {  // exported for the SVG-renderer smoke test
  const none = { svg: "", preDrops: [] };
  if (!sp || !Array.isArray(sp.points) || sp.points.length < 2) return none;
  const pts = sp.points;
  const nameS = pts.map((p) => (p && Number.isFinite(p.name) ? p.name : null));
  const benchS = pts.map((p) => (p && Number.isFinite(p.benchmark) ? p.benchmark : null));
  if (!nameS.some((v) => v != null)) return none;
  const { fs } = EXHIBIT;
  const ex = extent([...nameS, ...benchS]);
  if (!ex) return none;
  const pad = Math.max((ex[1] - ex[0]) * 0.1, 6), dom = { lo: ex[0] - pad, hi: ex[1] + pad };
  const W = 720, H = 258, padL = 36, padR = 14, cy0 = 24, cy1 = 200, px0 = padL, px1 = W - padR;
  const sx = linScale(0, pts.length - 1, px0, px1), sy = linScale(dom.lo, dom.hi, cy1, cy0);
  const line = (series, color, w, dash) => {
    const seg = series.map((v, i) => (v == null ? null : `${sx(i).toFixed(1)},${sy(v).toFixed(1)}`)).filter(Boolean).join(" ");
    return seg ? `<polyline points="${seg}" fill="none" stroke="${color}" stroke-width="${w}"${dash ? ` stroke-dasharray="${dash}"` : ""} stroke-linejoin="round"/>` : "";
  };
  const nameCol = "var(--accent)", benchCol = "var(--ink-3)";
  // real axes: horizontal gridlines at a nice step, labelled; the 100-rebase line emphasized
  const span = dom.hi - dom.lo;
  const step = [10, 20, 25, 50, 100].find((g) => span / g <= 6) || 100;
  let grid = "";
  for (let v = Math.ceil(dom.lo / step) * step; v < dom.hi; v += step) {
    const y = sy(v).toFixed(1), is100 = v === 100;
    grid += `<line x1="${px0}" y1="${y}" x2="${px1}" y2="${y}" stroke="${is100 ? "var(--line-2)" : "var(--line)"}" stroke-width="1"${is100 ? ` stroke-dasharray="3 2"` : ""}/>`
      + `<text x="${px0 - 4}" y="${+y + 3}" font-size="${fs.axis}" text-anchor="end" fill="var(--ink-3)">${v}</text>`;
  }
  // x labels: four evenly spaced dates (dedup consecutive repeats)
  let xLab = "", lastTxt = "";
  for (const frac of [0, 1 / 3, 2 / 3, 1]) {
    const i = Math.round((pts.length - 1) * frac);
    const txt = _monYr(pts[i].date);
    if (txt === lastTxt) continue;
    lastTxt = txt;
    const anchor = frac === 0 ? "start" : frac === 1 ? "end" : "middle";
    xLab += `<text x="${sx(i).toFixed(1)}" y="${cy1 + 15}" font-size="${fs.xlabel}" text-anchor="${anchor}" fill="var(--ink-3)">${txt}</text>`;
  }
  // detector-coverage honesty: boundary + real pre-window drops as HOLLOW markers. Daily-only —
  // a downsampled series can neither find 1-day drops nor place them truthfully.
  const spacingDays = [];
  for (let i = 1; i < Math.min(pts.length, 24); i++) spacingDays.push((Date.parse(pts[i].date) - Date.parse(pts[i - 1].date)) / 86400000);
  const isDaily = spacingDays.length > 0 && spacingDays.slice().sort((a, b) => a - b)[Math.floor(spacingDays.length / 2)] <= 4;
  const gapSet = new Set((rows || []).map((r) => r[0]));
  let boundary = "";
  const preDrops = [];
  if (det && det.windowDays != null && det.refDate && isDaily) {
    const bMs = Date.parse(det.refDate) - det.windowDays * 86400000;
    const bIdx = pts.findIndex((p) => Date.parse(p.date) >= bMs);
    if (bIdx > 3 && bIdx < pts.length - 3) {
      const bx = sx(bIdx).toFixed(1);
      boundary = `<line x1="${bx}" y1="${cy0}" x2="${bx}" y2="${cy1}" stroke="var(--line-2)" stroke-width="1" stroke-dasharray="2 4"/>`
        + `<text x="${+bx - 5}" y="${cy0 + 8}" font-size="9" text-anchor="end" fill="var(--ink-3)">◂ before detector window (${det.windowDays}d)</text>`;
      if (det.threshold != null) {
        for (let i = 1; i < bIdx; i++) {
          const a = nameS[i - 1], b = nameS[i];
          // the SAME "true 1-day move" rule the ledger uses — a downsampled step-2 pair (a weekday
          // skipped) is NOT a 1-day drop and must not get a hollow marker (was a loose 1–4d check).
          if (a != null && b != null && a > 0 && isNextTradingDay(pts[i - 1].date, pts[i].date)
              && b / a - 1 <= det.threshold && !gapSet.has(pts[i].date)) {
            preDrops.push({ date: pts[i].date, pct: b / a - 1 });
            boundary += `<circle cx="${sx(i).toFixed(1)}" cy="${sy(b).toFixed(1)}" r="5" fill="none" stroke="var(--ink-3)" stroke-width="1.3"/>`;
          }
        }
      }
    }
  }
  // numbered markers, STAGGERED on collision (adjacent-day gaps overlap at daily resolution). A run
  // of 3+ near markers steps through extra lanes so it doesn't just flip between two that re-collide
  // (a mere flip puts marker 1 and marker 3 back on the same lane). Lanes 0/1 keep the ±16 an
  // isolated or paired marker has always used, so all current (≤2-cluster) charts are unchanged.
  const LANES = [-16, 16, -30, 30];
  let markers = "", prevX = -1e9, cluster = 0;
  (rows || []).forEach(([gd], i) => {
    const exact = pts.findIndex((p) => p && p.date === gd);
    const idx = exact >= 0 ? exact : nearestPtIdx(pts, gd);
    const x = sx(idx), yPt = sy(nameS[idx] != null ? nameS[idx] : dom.lo);
    cluster = (x - prevX < 18) ? cluster + 1 : 0;
    prevX = x;
    const off = LANES[cluster % LANES.length], above = off < 0;
    const yC = yPt + off;
    markers += `<line x1="${x.toFixed(1)}" y1="${yPt.toFixed(1)}" x2="${x.toFixed(1)}" y2="${(above ? yC + 7 : yC - 7).toFixed(1)}" stroke="var(--danger)" stroke-width="0.8"/>`
      + `<circle cx="${x.toFixed(1)}" cy="${yC.toFixed(1)}" r="7.5" fill="var(--surface)" stroke="var(--danger)" stroke-width="1.5"/>`
      + `<text x="${x.toFixed(1)}" y="${(yC + 3.2).toFixed(1)}" text-anchor="middle" font-size="9.5" font-weight="600" fill="var(--danger)">${i + 1}</text>`;
  });
  const sym = escapeHtml(sp.name_symbol || "Name"), bsym = escapeHtml(sp.benchmark_symbol || "IWM");
  const nr = fmtPct(sp.name_return, { signed: true });
  const br = (typeof sp.benchmark_return === "number") ? fmtPct(sp.benchmark_return, { signed: true }) : DASH;
  const ly = H - 6;
  const leg = `<g font-size="${fs.legend}">`
    + `<circle cx="${px0 + 3}" cy="${ly - 3}" r="2.6" fill="${nameCol}"/><text x="${px0 + 10}" y="${ly}" fill="var(--ink-2)">${sym} <tspan fill="${nameCol}" font-weight="600">${nr}</tspan></text>`
    + `<circle cx="${px0 + 150}" cy="${ly - 3}" r="2.6" fill="${benchCol}"/><text x="${px0 + 157}" y="${ly}" fill="var(--ink-2)">${bsym} <tspan fill="${benchCol}" font-weight="600">${br}</tspan></text>`
    + `<text x="${px0 + 300}" y="${ly}" fill="var(--ink-3)">52-wk · rebased = 100</text></g>`;
  const svg = `<div class="ds-exhibit" style="margin:4px 0 2px; flex:1 1 400px; min-width:0;">
    <svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;" role="img" aria-label="Price performance ${sym} versus ${bsym}, rebased to 100, gap-down events marked">
      ${grid}${xLab}${boundary}${line(benchS, benchCol, 1.4, "5 4")}${line(nameS, nameCol, 1.9)}${markers}${leg}
    </svg></div>`;
  return { svg, preDrops };
}

// (event study) the gap-down read: chart + numbered EVENT LEDGER side-by-side for MULTIPLE
// gap-downs (№ · date · true 1-day % · cause), the one-liner otherwise. The % derives from the
// daily perf series (gapPctFromPerf) and is OMITTED, never estimated, when the series can't carry
// it. A repeat filing reads "same 8-K as №" instead of restating the cause.
function readWhatBroke(s, sp, dc, refDate) {
  const rows = gapList(fmtShape(s.value));
  // ANY discrete-gap name gets the chart+ledger (a 1-gap name still needs "did it fall alone" and
  // its true 1-day %); only a gradual-bleed / unparseable shape stays the one-liner.
  if (!rows) return factRead("Read — what broke", s, (v) => escapeHtml(fmtShape(v)));
  const det = { threshold: dc && dc.gap_threshold, windowDays: dc && dc.gap_window_days, refDate };
  const { svg, preDrops } = drawdownChart(sp, rows, det);
  // accession per gap-date (explanatory filings only) → "same 8-K as №" cross-refs
  const accByDate = new Map();
  for (const f of ((dc && dc.filings) || [])) {
    if (f.explanatory === false || !f.gap_date) continue;
    accByDate.set(f.gap_date, f.accession || `${f.form}|${f.filing_date}`);
  }
  const firstRowOfAcc = new Map();
  rows.forEach(([d], i) => {
    const a = accByDate.get(d);
    if (a && !firstRowOfAcc.has(a)) firstRowOfAcc.set(a, i + 1);
  });
  const items = rows.map(([d, c], i) => {
    const pct = gapPctFromPerf(sp, d);
    const acc = accByDate.get(d);
    const first = acc ? firstRowOfAcc.get(acc) : null;
    const causeTxt = (first && first < i + 1) ? `same 8-K as ${_circled(first)}` : c;
    return `<div style="display:flex; gap:7px; align-items:baseline; padding:3.5px 0; border-bottom:1px solid var(--line);">
      <span style="flex:none; width:15px; height:15px; border-radius:50%; border:1.5px solid var(--danger); color:var(--danger); font-size:9.5px; font-weight:600; display:flex; align-items:center; justify-content:center;">${i + 1}</span>
      <span style="font-variant-numeric:tabular-nums; color:var(--ink-2); white-space:nowrap;">${escapeHtml(_monDay(d))}</span>
      ${pct == null ? "" : `<span style="font-variant-numeric:tabular-nums; color:var(--danger); font-weight:600; white-space:nowrap;">${fmtGapPct(pct)}</span>`}
      <span>${escapeHtml(causeTxt)}</span></div>`;
  }).join("");
  const hdr = (det.threshold != null && det.windowDays != null)
    ? `Gap-downs · 1-day ≤ −${Math.round(Math.abs(det.threshold) * 100)}% · ${det.windowDays}d window`
    : "Gap-downs";
  const pre = preDrops.length
    ? `<div style="color:var(--ink-3); font-size:10.5px; margin-top:7px; line-height:1.55;">○ before the ${det.windowDays}d detector window:<br>${preDrops.map((q) => `${escapeHtml(_monDay(q.date))} ${fmtGapPct(q.pct)}`).join(" · ")} (not classified)</div>`
    : "";
  const key = `<div style="flex:0 1 236px; font-size:11.5px;">
    <div style="font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink-3); margin:2px 0 6px;">${hdr}</div>
    ${items}${pre}${citeMark(s.source_ref)}</div>`;
  return `<div class="fg-read"><div class="fg-read-lab">Read — what broke</div>
    <div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">${svg}${key}</div></div>`;
}

function cleanNote(note) {
  return String(note)
    .replace(/\s*for 8-Ks \['([^']+)'\]/, " for the filed 8-K $1")
    .replace("Credit Health Panel: scale direction ambiguous — not rendered",
             "credit-health panel scale is ambiguous in the export");
}

// (D1/R3 · buy-side restructure) drawdown cause + idiosyncrasy under ONE section header — the
// READ leads, the alone-or-with-market comparison follows DIRECTLY (the card's question), and the
// 8-K evidence closes as provenance. Revised guidance moved to the street card (it is a guidance
// fact, not a what-broke fact); the cohort-absence row collapsed to a footnote (idioVsShared).
function drawdownIdio(m, refDate) {
  const dd = drawdownCause(m.drawdown_cause, m.stock_performance, refDate);
  const io = idioVsShared(m.idiosyncratic_vs_shared, m.stock_performance && m.stock_performance.name_symbol);
  // legacy no-street-card JSON: the guidance fact renders here so it is never dropped
  const legacyGuide = (!m.catalyst_path && m.drawdown_cause)
    ? fact("Revised guidance", m.drawdown_cause.revised_guidance) : "";
  if (!dd.read && !dd.evidence && !io && !legacyGuide) return "";
  const divider = `<div class="ds-title" style="font-size:12px; margin-top:10px;">Company-specific or market-wide?</div>`;
  return sec("What broke — and did it fall alone?",
    "The event(s) that broke the name, then whether it fell alone (idiosyncratic) or with its graph cohort.",
    dd.read + (io ? divider + io : "") + legacyGuide + dd.evidence);
}

// (E2) $M principal → "$25.0M" / "–"
// $M with en-US thousands separators, matching the Python render._musd (`f"${v:,.1f}M"`) so the
// web/PDF thousands grouping matches the .md for a $1B+ bucket total (e.g. "$1,234.5M").
const _mM = (v) => (v == null ? DASH : `$${Number(v).toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`);

// (E2) deterministic month-precision maturity wall from the structured instruments (mirrors
// render._maturity_wall_lines): matured-pre-reference / due this ref year / due later years / undated.
function maturityWall(cs, refDate, { column = false } = {}) {
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
  // (buy-side layout) the by-year run is a same-schema series → a year→amount STRIP, not list
  // lines; matured/≤12m keep their loud list form above (they carry warnings, not just amounts).
  const byYr = {};
  for (const [m, i] of later) (byYr[m.slice(0, 4)] ||= []).push([m, i]);
  const chips = Object.keys(byYr).sort().map((yr) =>
    `<div class="wall-yr"><span>${yr}</span><b>${_mM(sum(byYr[yr]))}</b></div>`);
  const shortName = (n, cap = 34) =>
    (n.length <= cap ? n : n.slice(0, cap).split(" ").slice(0, -1).join(" ") + "…");
  let undatedFoot = "";
  if (undated.length) {
    chips.push(`<div class="wall-yr"><span>undated†</span><b>${_mM(sum(undated))}</b></div>`);
    undatedFoot = `† floor — no panel maturity: ${undated.map((i) => `${escapeHtml(shortName(i.description))} ${_mM(i.principal_musd)}`).join(", ")}. `;
  }
  const strip = chips.length ? `<div class="wall-strip">${chips.join("")}</div>` : "";
  const foot = `<div class="wall-foot">${undatedFoot}reconciliation: itemized ${_mM(sum(inst.value))} (panel ${escapeHtml(cs.detail_as_of || "")}) vs the latest-quarter aggregates below — the gap is unitemized / newer term loans.</div>`;
  const body = `${li.length ? `<ul class="kv-list">${li.join("")}</ul>` : ""}${strip}${foot}`;
  // column mode (buy-side two-column survival card): the wall carries its own sub-head and fills
  // the right column — no label|value grid wasting the column's width
  if (column) {
    return `<div class="ls-wall"><div class="ds-title" style="font-size:12px;">Maturity wall · vs ${escapeHtml(refDate)}</div>${body}</div>`;
  }
  return `<div class="fact"><div class="fact-label">Maturity wall · vs ${escapeHtml(refDate)}</div><div>${body}</div></div>`;
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
function capitalStructureInner(cs, refDate, { skipWall = false } = {}) {
  const inst = cs.instruments;
  let table = fact("Capital structure (instruments)", inst);
  if (inst && inst.status === "present" && Array.isArray(inst.value)) {
    // (K1) near-dated = maturity year ≤ refYear+1 (mirrors render._near_dated); undated → appendix.
    const refYearNext = Number(String(refDate).slice(0, 4)) + 1;
    const near = inst.value.filter((i) => i.maturity_date && Number(i.maturity_date.slice(0, 4)) <= refYearNext);
    const moved = inst.value.length - near.length;
    const note = moved ? `${moved} undated / later aggregate line item(s) in the appendix panel` : "";
    // (declutter) zero tranches in the window → one honest line, never an all-header empty table
    table = near.length
      ? dataTable(`Live instruments — near-dated (≤12m + ${refYearNext}) — panel ${cs.detail_as_of || ""}`,
          inst.source_ref, _CS_COLS, near.map(instrumentRow), note)
      : fact(`Live instruments — near-dated (≤12m + ${refYearNext})`,
          { status: "present", value: `none due in the window — ${note || "full panel in the appendix"}`,
            source_ref: inst.source_ref });
  }
  // (P3) the verbatim maturity-resolution event, when captured (a pre-P3 JSON has no field → nothing)
  const matEv = cs.maturity_event && (cs.maturity_event.status !== "present" || cs.maturity_event.value)
    ? fact("Maturity resolution (8-K verbatim)", cs.maturity_event) : "";
  // the sub-head stops claiming the wall once the wall renders in the column above
  return subhead(skipWall ? "Capital structure" : "Capital structure & maturity wall") +
    table + (skipWall ? "" : maturityWall(cs, refDate)) +
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
    <summary style="cursor:pointer; font-size:12.5px; font-weight:600; color:var(--ink-2);">Capital-structure provenance — on-demand (audit) <span class="muted" style="font-weight:400;">— full panel · pointers · terms (web collapsed · prints in full · JSON)</span></summary>
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
    const key = fam + "\x00" + r.name;
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
  const lb = m.leverage_survival ? leverageBlock(m) : {
    grid: "",
    rows: fact("Net debt / EBITDA (GAAP)", q.net_debt_to_ebitda, mult) +
      fact("Net debt / OCF", q.net_debt_to_ocf, mult) +
      fact("Net debt / EBITDA (covenant adj.)", q.net_debt_to_ebitda_adjusted) +
      fact("Survival capacity", q.survival_capacity) +
      fact("Interest coverage", q.interest_coverage, mult),
  };
  // (declutter P1) "FCF sign: UNKNOWN" above a present FCF value read as a contradiction
  const fcfSign = (q.fcf_sign && q.fcf_sign.status === "present")
    || !(q.free_cash_flow && q.free_cash_flow.status === "present")
    ? fact("FCF sign", q.fcf_sign, signWord) : "";
  const cash = subhead("Cash & liquidity") +
    fcfSign + fact("Free cash flow ($M)", q.free_cash_flow) +
    (m.capital_structure ? "" : fact("Liquidity / covenant flags", q.liquidity_covenant_flags));
  // (buy-side two-column) the SCALAR GRID pairs with the maturity wall side-by-side — two compact
  // blocks of like density; the prose rows (long values) stay FULL-WIDTH below the columns.
  // Narrow screens collapse to one column (CSS); no wall → single column (fail-honest).
  const cs = m.capital_structure;
  const wallCol = cs ? maturityWall(cs, refDate, { column: true }) : "";
  const capital = cs ? capitalStructureInner(cs, refDate, { skipWall: !!wallCol }) : "";
  const top = wallCol && lb.grid
    ? `<div class="ls-cols"><div>${lb.grid}</div><div>${wallCol}</div></div>` + lb.rows
    : lb.grid + (wallCol || "") + lb.rows;
  return sec("Survival — leverage · cash/FCF · capital structure & maturity wall",
    "One block: the leverage bases, self-funding, the month-precision wall, and the covenant "
    + "pointers/terms.", top + cash + capital);
}

// (D2/D1) trajectory — the merged table + the share-count trend.
// (Phase-3) ROIC (return on capital) trend — a dependency-free line of the per-period ROIC, from the
// STRUCTURED roic_trend series (never re-parsing the trajectory string). Values are fractions → ×100
// for the % display. Zero baseline when the series crosses zero (a distressed name). Fail-honest:
// no structured series → no chart (the trajectory table still renders).
function trajectorySection(q, m = {}) {
  if (!q) return "";
  // (P4) the ROIC-trend CHART was removed — its RoCE-over-time is the return-ratios exhibit's RoCE line
  // (Financial Snapshot), a strict duplicate. ROIC stays as a row in the trajectory table below; the
  // structured q.roic_trend series stays in the JSON (machine-complete), just no longer charted here.
  // (tier redesign) the return-ratios PER-PERIOD table moved here from the Brief — its exhibit stays
  // on the first cut; the table is depth and belongs with the operating arc.
  const rr = m.return_ratios;
  const rrTable = (rr && rr.status === "present" && rr.value && Array.isArray(rr.value.rows) && rr.value.rows.length)
    ? finTable("Return ratios — per fiscal period", rr) : "";
  return sec("Operating trajectory", "The per-period arc; the same-quarter YoY footnoted.",
    trajectoryTable(q, m) + fact("Share-count trend", q.share_count_trend) + rrTable);
}

// SLIM HEADER (tier redesign): ticker · name · the DOCUMENT date. The old meta line was process
// telemetry ("proposal sealed · assembled … UTC · synthesis claude-…") worn as a subtitle, and its
// "data as of <screen-date>" CONTRADICTED the body (the price and estimates carry their own, newer
// and older, as-ofs). Market convention dates a note by publication: the assembly date. The full
// vintage map + model + pivot mechanics live in the Appendix's Record & reproduce section.
function header(d) {
  return `<div class="header-block ds-header">
    <div class="ds-header-main">
      <h1 class="page-h">${escapeHtml(d.name || d.ticker)} <span class="page-h-id">(${d.exchange ? `${escapeHtml(d.exchange)}: ` : ""}<span class="mono">${escapeHtml(d.ticker)}</span>)</span></h1>
      <div class="ds-meta">${fmtDate(d.assembled_at)} · extraction <span class="mono">${escapeHtml(stampLabel(d.extraction_version))}</span></div>
    </div>
    <div class="ds-pdf-wrap">
      <button id="ds-pdf" class="ds-pdf-btn" type="button" aria-haspopup="true" aria-expanded="false"
        title="Download this dossier — PDF via your browser's print dialog (choose &ldquo;Save as PDF&rdquo;), or the rendered Markdown file.">&#x2913; Download &#x25be;</button>
      <div class="ds-pdf-menu" id="ds-pdf-menu" role="menu" hidden>
        <button type="button" data-scope="brief" role="menuitem">Brief PDF <span class="muted">· first cut</span></button>
        <button type="button" data-scope="full" role="menuitem">Full dossier PDF <span class="muted">· all tiers</span></button>
        <button type="button" data-scope="md" role="menuitem">Full dossier MD <span class="muted">· markdown file</span></button>
      </div>
    </div>
  </div>`;
}

// (D4) a guardrail caveat is "Lead (a bull point): '<full claim>' — <explanation>". Parse it into the
// what / where / why-it-matters / how-to-verify shape (offending sentence IN FULL). A mechanical /
// 'pull CIQ …' caveat is already a complete advisory → one full-sentence bullet.
const _CAVEAT_RE = /^(.*?)\(([^)]*?\bpoint[^)]*?)\):\s*'([\s\S]*?)'\s*—\s*([\s\S]*)$/;
// (A) Render-time caveat cleanup — the human tier never shows the synthesis's field tokens or the
// internal rule numbers a guardrail cites; the committed JSON keeps the raw strings. Twin of
// render.py _dejargon_caveat. AS_OF (a real sidecar name) is deliberately left intact.
function dejargonCaveat(s) {
  return String(s)
    .replace(/evidence_balance/g, "the written assessment")
    .replace(/bull_points/g, "bull points")
    .replace(/bear_points/g, "bear points")
    .replace(/\s*\(rule \d+\)/g, "");
}

// (D) Financial acronyms render uppercase even when a parser lower-cased them ("adjusted ebitda
// outlook"). Word-boundary only — never mid-word. Twin of render.py _fix_acronyms.
function fixAcronyms(s) {
  return String(s).replace(/\b(ebitda|eps|fcf|ebit|roic|roe)\b/gi, (m) => m.toUpperCase());
}

// (Option 1) Lead the catalyst-staleness caveat with the name-specific discriminator (days stale vs
// the tolerance) instead of the structural "no as-of stamp" preamble that buried it. Deterministic;
// fails through unchanged if the template differs. Twin of render.py _reword_catalyst_stale.
const _CATALYST_STALE_RE = /Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; its data is on\/after ([\d-]+) \(the latest embedded revision event\), so it is up to (\d+)d before the [\d-]+ reference — beyond the (\d+)d tolerance — and the true export date is unknown, so freshness cannot be confirmed\. (.+)/;
function rewordCatalystStale(s) {
  const m = String(s).match(_CATALYST_STALE_RE);
  if (!m) return String(s);
  return `Estimates data up to ${m[2]}d stale (beyond the ${m[3]}d tolerance) — freshness UNVERIFIABLE: the CIQ Estimates export has no as-of stamp, and its data is on/after ${m[1]} (its latest embedded revision event — a worst-case floor on the true export date). ${m[4]}`;
}

function caveatBlock(f) {
  f = rewordCatalystStale(dejargonCaveat(f));
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

// One guard type firing on N synthesis points was rendering N near-identical cards (BRBR's two
// "Unreconciled margin-compression" flags, same title + same why-it-matters). Collapse caveats that
// share a lead + the what/where/why shape into ONE card — the lead once, each offending claim
// nested with its own where, one shared why/how when identical. The action item is singular; the
// audit trail keeps every claim. Grouping keys off the DETERMINISTIC lead (flags.revoice), never
// LLM-composed text; non-matching caveats (mechanical, false-balance) stay one-per-card.
function caveatGroupBlock(group) {
  const parsed = group.map((f) => dejargonCaveat(f).match(_CAVEAT_RE));
  const lead = parsed[0][1].trim();
  const parts = parsed.map((m) => {
    const why = m[4].trim(); const i = why.lastIndexOf("; ");
    return { where: m[2].trim(), what: m[3].trim(),
      why: i >= 0 ? why.slice(0, i).trim() : why, how: i >= 0 ? why.slice(i + 2).trim() : "" };
  });
  const sameWhy = parts.every((p) => p.why === parts[0].why);
  const sameHow = parts.every((p) => p.how === parts[0].how);
  // LOSSLESS: a shared why/how prints once below; a why/how that DIFFERS across the group prints
  // per-claim on the where line — the collapse never drops a claim's why-it-matters or how-to-verify.
  const claims = parts.map((p) => `
    <div style="margin-top:8px; padding-left:11px; border-left:2px solid var(--warn-border);">${escapeHtml(p.what)}
      <div class="muted" style="font-size:11.5px; margin-top:2px;"><i>where:</i> ${escapeHtml(p.where)}${sameWhy ? "" : ` · <i>why:</i> ${escapeHtml(p.why)}`}${!sameHow && p.how ? ` · <i>how:</i> ${escapeHtml(p.how)}` : ""}</div>
    </div>`).join("");
  return `<div class="flag open"><span class="fi">⚠</span><span>
    <b>${escapeHtml(lead)}</b> <span style="font-size:11px; font-weight:500; border:1px solid var(--warn-border); border-radius:20px; padding:0 7px; margin-left:4px;">${parts.length} points</span>${claims}
    ${sameWhy ? `<div class="muted" style="font-size:11.5px; margin-top:6px;"><i>why it matters:</i> ${escapeHtml(parts[0].why)}</div>` : ""}
    ${sameHow && parts[0].how ? `<div class="muted" style="font-size:11.5px;"><i>how to verify:</i> ${escapeHtml(parts[0].how)}</div>` : ""}
  </span></div>`;
}

function flagsSection(caveats) {
  // Decision caveats only (d.caveats) — the machine-QA self-checks live in d.qa_flags (dev/JSON),
  // deliberately kept out of this human view, matching the PDF/markdown render. (D4) each renders in
  // the what/where/why/how-to-verify shape, the offending sentence IN FULL. Same-type caveats
  // collapse into one grouped card (caveatGroupBlock); everything else stays one-per-card.
  if (!caveats.length) return "";
  const groups = [];
  const byLead = new Map();
  for (const f of caveats) {
    const m = dejargonCaveat(f).match(_CAVEAT_RE);
    if (!m) { groups.push([f]); continue; }
    const lead = m[1].trim();
    if (byLead.has(lead)) byLead.get(lead).push(f);
    else { const g = [f]; byLead.set(lead, g); groups.push(g); }
  }
  const rows = groups.map((g) => g.length === 1 ? caveatBlock(g[0]) : caveatGroupBlock(g)).join("");
  // (B) count = DISTINCT advisories (grouped cards), so the human sees the surface size at a glance
  const count = `<span style="font-size:11.5px; font-weight:500; color:var(--warn-text); background:var(--conditional-bg); border:1px solid var(--warn-border); border-radius:20px; padding:1px 9px; margin-left:8px; vertical-align:middle;">${groups.length} to verify</span>`;
  return `<div class="card ds-section"><div class="ds-title">Analyst caveats — verify before the verdict${count}</div>
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
  // (declutter P3) the discipline lectures live ONCE in "How to read this dossier"; this block
  // keeps the gate, the vintages, and a terse † key.
  const intro = `<div class="fact"><div class="fact-label">What the current price implies (at stated multiples)</div>
    <div style="min-width:0;"><div class="muted" style="font-size:12px;">${escapeHtml(gateShortref(ie.heterogeneity_gate || ""))}</div>
    <div class="muted" style="font-size:11px;">TEV as-of ${escapeHtml(ie.tev_as_of || "")} · multiples as-of ${escapeHtml(ie.multiples_as_of || "")} · † at the name's own multiple the implied level is consensus by identity</div></div></div>`;
  const table = dataTable("Price-implied levels (at each stated multiple)", ie.tev && ie.tev.source_ref,
    ["Multiple (× used)", "Implied level"], rows, "");  // (K5) renamed
  const readsAgainst = "";  // (declutter) the juxtapose rule is stated once, in the reading guide
  // the parallel REVENUE anchors substantiate the TEV/Rev name-row identity (†); only when present.
  const revAnchors = (ie.rev_anchors && ie.rev_anchors.value)
    ? `<div style="margin-top:4px;"><b>Consensus path anchors (Revenue):</b> ${escapeHtml(ie.rev_anchors.value)}</div>` : "";
  // (audit) H7 EBITDA anchors can be UNKNOWN (Trends may lack FY26/FY27) — show the note, not blank.
  const anchorsTxt = (ie.anchors && ie.anchors.value) || (ie.anchors && ie.anchors.note) || "n/a";
  // (declutter) the coherence SELF-CHECK prints only when it FAILS — a passing residual line is
  // assembly QA; the fixed-multiple-set note was internal provenance ("declared in code").
  const anchors = `<div class="fact"><div class="fact-label">Consensus path anchors (EBITDA)</div>
    <div style="min-width:0;">${escapeHtml(anchorsTxt)}${revAnchors}
    ${ie.vintage_coherent ? "" : `<div class="muted" style="font-size:11px; margin-top:4px;">⚠ ${escapeHtml(ie.coherence_note || "")}</div>`}
    ${ie.net_debt_reconciled ? "" : `<div class="muted" style="font-size:11px;">⚠ net-debt input disagrees with the cash/debt bridge — see the TEV source</div>`}</div></div>`;
  return intro + table + readsAgainst + anchors;  // (K4) reads-against between the table and the anchors
}

function valuation(v) {
  if (!v) return "";
  // Mirrors the md render (PR #48): lead with the CROSS-SECTIONAL read (the edge); the own-history
  // percentile barely discriminates across finalists, so it's folded into the range line below.
  // (G) implied expectations slot in AFTER cross-sectional, BEFORE the own-history reads.
  // (declutter P1) the bare P/E and EV/EBITDA facts are GONE — both numbers already render inside
  // tables carrying their context, and the two sheets disagree by vintage (P/E 14.1 vs the comps
  // grid's 13), which read as a contradiction rather than information.
  return sec("Valuation", "Cross-sectional vs peers; the trailing-range read as secondary context.",
    fact("Cross-sectional (vs peers)", v.cross_sectional, null, { hi: true }) +
    impliedExpectations(v.implied_expectations) +
    fact("EV/adj-EBITDA (forward)", v.ev_ebitda_adjusted_fwd) +
    fact("Adjusted EPS (guide)", v.adjusted_eps) +
    fact("Own-history range position", v.range_position, null, { hi: true }));
}

// (D1/D2) `quality` split into leverageSurvival + trajectorySection (see renderDossier); the two
// seriesTable calls merged into trajectoryTable. `seriesTable` is retained (catalyst path uses it).

function concentration(c) {
  if (!c) return "";
  // (content relocation 2026-07-24) renamed from "Ownership & concentration" — it carries NO
  // ownership; all four facts are the business MIX. Real ownership (insider, short interest) moved
  // to the appendix. Twin of render.py's "## Business quality".
  return sec("Business quality", "What it sells, where the profit sits, to whom, and where.",
    fact("Segments (revenue share)", c.segments) +
    fact("Segment EBITDA share", c.segment_ebitda, null, { hi: true }) +
    fact("Customers", c.customers, fmtCustomers) +
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

function peerMultiplesFact(label, s, { gridPresent = false } = {}) {
  if (!s || s.status !== "present" || s.value == null) return fact(label, s);
  const p = parsePeerMultiples(s.value);
  if (!p) return fact(label, s);
  // (declutter P2) with the per-peer grid on the same page, the LTM rows here are its summary
  // statistics restated (the grid carries every peer AND a median row) — only the FORWARD (NTM)
  // rows survive, which exist nowhere else.
  const kept = gridPresent ? p.rows.filter((r) => /^NTM/i.test(r.metric)) : p.rows;
  if (!kept.length) return fact(label, s);
  const rows = kept.map((r) => ({ label: r.metric, cells: [r.name, r.low, r.median, r.mean, r.high] }));
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
  // (buy-side polish) the business descriptor is PROSE, not a numeric cell: left-aligned, small
  // muted sans, wrapped — never mono/right-aligned. The stored text is clipped AT EXTRACTION
  // (CIQ profile cap), so a non-terminal fragment gets an honest ellipsis marker — display only,
  // the record is unchanged; widening the capture is an extractor item, not a render one.
  const desc = (t) => {
    const x = String(t || "").trim();
    if (!x) return DASH;
    return escapeHtml(x) + (/[.!?)]$/.test(x) ? "" : "…");
  };
  const body = p.rows.map((r) => `<tr><td style="white-space:nowrap;">${escapeHtml(r.name)}</td>
    <td class="num">${escapeHtml(r.cap || DASH)}</td><td class="peer-desc">${desc(r.desc)}</td></tr>`).join("");
  const note = p.nameCap ? `<div class="muted" style="font-size:11px; margin-top:5px;">the name: ${escapeHtml(p.nameCap)}</div>` : "";
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div>
    <div style="min-width:0;"><div style="overflow-x:auto;"><table class="data"><thead><tr><th></th><th class="num">Mkt cap</th><th class="peer-desc-h">Business</th></tr></thead><tbody>${body}</tbody></table></div>${note}${citeMark(s.source_ref)}</div></div>`;
}

function peerComps(pc) {
  if (!pc) return "";
  return sec("Peer comparison", "The roster, the comparability gate, and the per-peer grid — the reader judges whether the discount is earned or residual.",
    peerRosterFact("Peer set (roster · caps · business)", pc.peer_set) +
    fact("Comparability (confidence gate)", pc.comparability, null, { hi: true }) +
    peerMultiplesFact(pc.peer_grid
      ? "Forward multiples (name vs peer Low/Median/Mean/High · NTM)"
      : "Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)",
      pc.trading_multiples, { gridPresent: !!pc.peer_grid }) +
    // B1: the per-peer grid (name + median footer) replaces the median-only deltas line
    (pc.peer_grid ? peerGridTable(pc.peer_grid)
      : peerDeltasFact("Fundamental deltas (earned-vs-residual inputs)", pc.fundamental_deltas)));
}

// One parsed 8-K item line ("CODE Title: body") → the body with the DOUBLED leading title and the
// defined-term legalese parentheticals stripped, truncated at a cross-reference stub. null when
// nothing informative remains. Display trim of a parse-summary (never a verbatim quote — those
// live untouched in JSON); twin of render.py _clean_item_event.
export function cleanItemEvent(ev) {  // exported for the py-twin equivalence test
  const m = /^(\d\.\d\d)\s+([^:]{1,90}):\s*([\s\S]*)$/.exec(String(ev));
  if (!m) return String(ev);
  const code = m[1];
  let title = m[2].replace(/^Item\s+\d\.\d\d:?\s*/i, "").trim();
  let body = m[3].trim();
  // cross-reference stub truncation FIRST — otherwise the title-recovery fallback below reads the
  // stub text itself as a "title" and mangles instead of dropping (caught by the twin test)
  const stub = body.search(/The information set forth in/i);
  if (stub >= 0) body = body.slice(0, stub).trim();
  if (!title) { const t2 = /^([^.:]{2,80})[.:]\s*/.exec(body); if (t2) title = t2[1].trim(); }
  if (title) {
    const esc = title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    body = body.replace(new RegExp(`^(?:Item\\s+\\d\\.\\d\\d[.:]?\\s*)?${esc}\\s*[.:]\\s*`, "i"), "");
  }
  body = body.replace(/\s*\(\s*(?:the\s+)?[“"][^)]{1,70}[”"]\s*\)/g, "");
  body = body.trim();
  if (!body) return null;  // pure cross-reference / heading-only item — nothing informative
  return title ? `${code} ${title}: ${body}` : `${code}: ${body}`;
}

function drawdownCause(dc, sp, refDate) {
  if (!dc) return { read: "", evidence: "" };
  // GROUP BY ACCESSION: two consecutive gap-downs can share ONE 8-K (SMPL 04-09/04-10, CNXC
  // 02-11/02-12), and rendering the identical block per gap-date read as a duplicate. One card per
  // filing, naming every gap-down it explains.
  const byAcc = new Map();
  for (const f of (dc.filings || [])) {
    // An administrative-only 8-K (5.07 annual-meeting vote, etc.) does not explain the gap: the
    // shape line already reads "no earnings/guidance filing" for it, so suppress its card here.
    // Explicit === false only — pre-flag JSON (undefined) keeps rendering (default = explanatory).
    if (f.explanatory === false) continue;
    const k = f.accession || `${f.form}|${f.filing_date}`;
    if (!byAcc.has(k)) byAcc.set(k, { f, gaps: [] });
    if (f.gap_date) byAcc.get(k).gaps.push(f.gap_date);
  }
  // ledger №s for the header chips ("⑤ 8-K · filed …") — same numbering as the event ledger
  const shapeV = dc.shape || {};
  const ledgerRows = (shapeV.status === "present" && shapeV.value != null)
    ? gapList(fmtShape(shapeV.value)) : null;
  const numByDate = new Map((ledgerRows || []).map(([d], i) => [d, i + 1]));
  const nums = (gaps) => gaps.map((g) => numByDate.get(g)).filter(Boolean).map(_circled).join("");
  // (#2) SUBSTANTIVE non-2.02 item narratives BELONG on the visible card — the parsed EX-99.1 driver
  // (metrics) often isn't the catalyst (VRRM's Avis-termination 8.01, AORT's 1.01 purchase-option
  // were dropdown-only). 7.01 (Reg-FD "will host a webcast") and 9.01 (exhibits) stay noise.
  const _SUBSTANTIVE = /^(1\.01|1\.02|2\.05|2\.06|3\.01|4\.02|5\.02|8\.01)\b/;
  const substantiveEvents = (f) => (f.events || [])
    .filter((e) => _SUBSTANTIVE.test(String(e))).map(cleanItemEvent).filter(Boolean);
  // (event study) the VISIBLE tier carries the INFORMATIVE cards — a filing has a card when it
  // parsed a driver OR carries a substantive non-earnings item. A filing with neither (a lone 7.01,
  // or an unparsed 2.02) has no card; its items live only in the provenance tier below.
  const grouped = [...byAcc.values()];
  const isCarded = ({ f }) => (f.drivers && f.drivers.status === "present") || substantiveEvents(f).length;
  const carded = grouped.filter(isCarded);
  const driverCards = carded.map(({ f, gaps }) => {
    const forWhich = gaps.length
      ? `(for the ${gaps.map(escapeHtml).join(" and ")} gap-down${gaps.length > 1 ? "s" : ""})`
      : "";
    const driverLine = (f.drivers && f.drivers.status === "present")
      ? `<div class="fe"><b>what the results showed:</b> ${escapeHtml(fixAcronyms(f.drivers.value))}${citeMark(f.drivers.source_ref)}</div>`
      : "";
    const eventLines = substantiveEvents(f)
      .map((e) => `<div class="fe">${escapeHtml(fixAcronyms(String(e).slice(0, 260)))}</div>`).join("");
    // items line: the 8-K's codes in words (9.01/7.01 dropped), so the card names what the filing is
    const items = (f.item_types || f.items || [])
      .filter((t) => !/^(9\.01|7\.01)\b/.test(String(t)));
    return `
    <div class="filing">
      <div class="fh"><span style="color:var(--danger);">${nums(gaps)}</span> ${escapeHtml(f.form || "8-K")} · filed ${fmtDate(f.filing_date)} <span class="muted">${forWhich}</span></div>
      <div class="muted" style="font-size:11px; margin:1px 0 3px;">items: ${escapeHtml(items.join(" · ") || "—")}</div>
      ${driverLine}${eventLines}
      ${f.url ? `<div style="margin-top:5px;"><a href="${encodeURI(f.url)}" target="_blank" rel="noopener">EDGAR ${escapeHtml(f.accession || "")}</a></div>` : ""}
    </div>`;
  }).join("");
  // (#3b) on-demand provenance lists ONLY the NON-carded filings (a carded filing is already shown
  // in full — repeating it here was the duplication). Disappears entirely when every filing is
  // carded. The complete raw record always stays in dossier.json regardless.
  const uncarded = grouped.filter((g) => !isCarded(g));
  const provEntries = uncarded.map(({ f, gaps }) => {
    const items = (f.item_types || f.items || []).filter((t) => !String(t).startsWith("9.01"));
    const evs = (f.events || []).map(cleanItemEvent).filter(Boolean)
      .map((e) => `<div style="margin:2px 0 0 14px;">${escapeHtml(String(e).slice(0, 300))}</div>`).join("");
    return `<div style="margin-top:7px;"><b>${nums(gaps) || "—"}</b> · filed ${fmtDate(f.filing_date)} · items: ${escapeHtml(items.join(" · ") || "—")}
      ${f.url ? ` · <a href="${encodeURI(f.url)}" target="_blank" rel="noopener">EDGAR ${escapeHtml(f.accession || "")}</a>` : ""}${evs}</div>`;
  }).join("");
  const provenance = uncarded.length
    ? `<details style="margin-top:10px; font-size:12px; color:var(--ink-2);">
        <summary style="cursor:pointer; font-size:11.5px; color:var(--ink-3);">Other 8-Ks at the gap dates — items &amp; EDGAR links (${uncarded.length})</summary>
        <div style="padding:2px 2px 4px;">${provEntries}</div></details>`
    : "";
  // (declutter) the dates row repeats the shape line whenever every date already appears there
  const gd = dc.gap_down_dates || {};
  const datesDup = gd.status === "present" && shapeV.status === "present"
    && (gd.value || []).every((d) => String(shapeV.value).includes(String(d)));
  // (buy-side anatomy) the Shape classification IS this card's read — it leads when present;
  // an absent shape stays a loud UNKNOWN row (fail-honest, never silently dropped)
  const shapeLead = (shapeV.status === "present" && shapeV.value != null)
    ? readWhatBroke(dc.shape, sp, dc, refDate)
    : fact("Shape", dc.shape, fmtShape);
  // (restructure) read + evidence returned SEPARATELY: the idio comparison renders between them
  // (the card's question directly after its read; the 8-K callout closes as provenance). Revised
  // guidance is a street/guidance fact — it renders on the street card (catalystPath); the legacy
  // no-catalyst-path JSON keeps it here so the fact is never dropped.
  return {
    read: shapeLead + (datesDup ? "" : fact("Gap-down dates", listFact(dc.gap_down_dates))),
    evidence: (driverCards || provenance)
      ? `<div style="margin-top:12px;">${driverCards}${provenance}</div>` : "",
  };
}

function idioVsShared(io, sym) {
  if (!io) return "";
  const cohort = io.cohort && io.cohort.status === "present" && Array.isArray(io.cohort.value)
    ? `<div style="margin-top:10px;"><table class="data"><thead><tr><th>Cohort name</th><th class="num">Hops</th><th class="num">180d return</th><th>Via</th></tr></thead><tbody>
        ${io.cohort.value.map((c) => `<tr><td class="mono">${escapeHtml(c.ticker || "")}</td><td class="num">${c.hops ?? DASH}</td>
          <td class="num">${c.ret_180d == null ? DASH : fmtPct(c.ret_180d, { signed: true })}</td>
          <td class="muted" style="font-size:11.5px;">${escapeHtml(c.via || "")}</td></tr>`).join("")}
      </tbody></table><div class="muted" style="font-size:11.5px; margin-top:4px;">source: ${escapeHtml(io.cohort.source_ref || "")}</div></div>`
    : `<div class="fact-val muted" style="margin-top:8px;"><span class="pill unresolved">${io.cohort?.status === "missing" ? "MISSING" : "UNKNOWN"}</span> ${escapeHtml(io.cohort?.note || "no graph cohort")}</div>`;
  const cohortPresent = io.cohort && io.cohort.status === "present" && Array.isArray(io.cohort.value);
  // (declutter P1) an UNKNOWN market row above a PRESENT relative read as a contradiction; and the
  // two cohort-absence rows said one absence twice, one citing an internal filename.
  const marketCell = (io.market_180d_return && io.market_180d_return.status === "present")
    || !(io.rel_vs_market && io.rel_vs_market.status === "present")
    ? { label: `Market (${io.benchmark_symbol || "IWM"}) 180d`, s: io.market_180d_return, fmt: retHero }
    : null;
  const readLead = (io.read && io.read.status === "present" && io.read.value != null)
    ? factRead("Read — alone or with the cohort?", io.read)
    : fact("Read", io.read, null, { hi: true });  // an UNKNOWN read stays loud, never dropped
  // (restructure) cohort ABSENCE is one honest footnote line, not a full labelled row
  const cohortBlock = cohortPresent
    ? readLead
      + `<div class="fact"><div class="fact-label">Graph cohort</div><div>${cohort}</div></div>`
    : `<div class="fg-note" style="margin-top:2px;">no supplier/customer cohort mapped for this name — the comparison is vs the market only</div>`;
  // (event study) the returns compress to ONE strip line — the chart above already SHOWS the
  // divergence, a tile grid restated it at hero scale. The strip renders whenever the NAME return
  // is present; an absent market leg drops the "vs IWM" middle (same P1 honesty the tile grid used),
  // an absent relative leg drops the arrow. Only a fully-UNKNOWN name return → the loud tile grid.
  const nm = io.name_180d_return, mk = io.market_180d_return, rel = io.rel_vs_market;
  const has = (x) => x && x.status === "present" && x.value != null;
  const comparison = has(nm)
    ? `<div style="display:flex; gap:8px; align-items:baseline; flex-wrap:wrap; background:var(--surface-2); border:1px solid var(--line); border-radius:8px; padding:8px 12px; margin-top:8px; font-size:13px;">
        <span class="muted" style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">180d</span>
        <span>${escapeHtml(sym || "Name")} <b style="color:var(--danger);">${fmtPct(nm.value, { signed: true })}</b>${citeMark(nm.source_ref)}</span>
        ${has(mk) ? `<span class="muted">vs</span>
        <span>${escapeHtml(io.benchmark_symbol || "IWM")} <b>${fmtPct(mk.value, { signed: true })}</b>${citeMark(mk.source_ref)}</span>` : ""}
        ${has(rel) ? `<span class="muted">→</span>
        <span><b style="color:var(--danger);">${fmtPct(rel.value, { signed: true }).replace("%", "pp")}</b> idiosyncratic${citeMark(rel.source_ref)}</span>`
        : `<span class="muted" style="font-size:11.5px;">· ${escapeHtml((io.benchmark_symbol || "IWM"))} benchmark bars unavailable — relative read UNKNOWN</span>`}
      </div>`
    : factGrid([
      { label: "Name 180d return", s: io.name_180d_return, fmt: retHero },
      marketCell,
      { label: "Relative vs market", s: io.rel_vs_market, fmt: retHero },
    ], { hero: true });
  // (R3) body only — drawdownIdio wraps it in the shared section header
  return comparison + cohortBlock;
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
  // (declutter P1) when the two-input self-funding read exists it REPLACES the one-input survival
  // claim (the md used to print both, the second announcing it superseded the first); the web now
  // mirrors the corrected shape. No subhead — the section title directly above already says it.
  const sf = ((m.primary_source || {}).self_funding) || null;
  const survival = (sf && sf.status === "present")
    ? fact("Self-funding", sf)  // (terse label) the two-input rule reads in the value itself
    : fact("Survival", lv.survival);
  // (buy-side layout) the numeric leverage scalars are ONE reference block — a stat grid with the
  // BASIS VISIBLE in each cell (NET vs TOTAL vs FWD-ADJ is disclosure, never tooltip-only). The
  // grid alone pairs with the wall column; the prose rows (long values) render FULL-WIDTH below
  // the columns — half-width cramming is exactly the misfit the field map exists to avoid.
  return {
    grid: factGrid([
      { label: "Net debt / EBITDA", basis: "NET", s: lv.net_debt_to_ebitda, fmt: mult },
      { label: "Net debt / OCF", s: m.quality.net_debt_to_ocf, fmt: mult },
      { label: "Net debt / EBITDA", basis: "FWD-ADJ", s: m.quality.net_debt_to_ebitda_adjusted },
      { label: "Interest coverage", s: lv.interest_coverage, fmt: mult },
    ]),
    rows: fact("Total debt / EBITDA vs peers", lv.total_debt_to_ebitda) +
      survival +
      creditHealth(lv),  // (K3) 4-row mini-table; fail-soft to fact("Credit health", …)
  };
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
    table = dataTable("Implied equity at the peer median ($M)", eq.source_ref,
      ["Implied equity (median)"], rows, "");
  }
  return sec("Implied equity at peer multiples",  // (tier redesign) vendor name out of the title
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

// "FY17–FY25 + LTM + 2 estimates" — the table says what it actually spans, so a reader never has
// to infer the window (and a truncated one can never masquerade as the whole history).
function spanLabel(s, unit) {
  const cols = (s && s.status === "present" && s.value && s.value.columns) || [];
  if (!cols.length) return `every ${unit} on file`;
  const est = (s.value.is_estimate || []).filter(Boolean).length;
  const act = cols.filter((c) => !/^LTM/i.test(String(c)));
  const span = act.length > 1 ? `${act[0]}–${act[act.length - 1 - (est ? est : 0)] || act[0]}` : act[0];
  const bits = [`${span}`];
  if (cols.some((c) => /^LTM/i.test(String(c)))) bits.push("LTM");
  if (est) bits.push(`${est} consensus`);
  return bits.join(" + ");
}

// (C1/C2) a Sourced[FinTable] → the shared dataTable; UNKNOWN/MISSING falls through to a fact badge
function finTable(label, s) {
  if (!s || s.status !== "present" || !s.value) return fact(label, s);
  const ft = s.value;
  // (declutter) a row whose every cell literally reads "none" is furniture (IT's Dividend/sh)
  const rows = (ft.rows || [])
    .filter((r) => !((r.cells || []).length
      && (r.cells || []).every((c) => String(c).trim().toLowerCase() === "none")))
    .map((r) => ({ label: r.label, cells: r.cells }));
  return dataTable(label, s.source_ref, ft.columns || [], rows, ft.note || "", ft.is_estimate || []);
}

// (D5b) relabel the levered-FCF row + footnote (display-only; the FinTable is rebuilt in place).
function fcfRelabel(s) {
  if (!s || s.status !== "present" || !s.value) return s;
  const ft = s.value;
  if (!(ft.rows || []).some((r) => r.label === "FCF ($M)")) return s;
  const rows = ft.rows.map((r) => (r.label === "FCF ($M)" ? { ...r, label: "FCF (levered)" } : r));
  const fn = "FCF (levered) = levered free cash flow as sourced — NOT CFO − capex";
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
  if (!fs) return sec("Financial statements", "", cap) + implied + mgmt;
  return sec(`Financial statements (actuals + consensus estimates) — ${asOfHeader(fs.as_of)}`,
    "Consensus (E) columns are marked and as-of-stamped; growth never spans a basis change (— basis).",
    finTable(`Annual ($M; E = consensus) — ${spanLabel(fs.annual, "fiscal year")}`,
             fcfRelabel(fs.annual)) +
    finTable(`Quarterly ($M) — ${spanLabel(fs.quarterly, "quarter")}`, fs.quarterly) +
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
  // (declutter P2) HEADLINE metrics only — the ones the synthesis argues from; interest/EBT/the
  // GAAP-vs-excl splits made an 18-row wall. Counted, machine-complete in JSON. (Mirrors
  // render.py's _HORIZON_KEEP.)
  const KEEP = /^(Revenue|EBITDA|EBIT|EPS)\b/i;
  const nonzero = [], zero = [];
  let skipped = 0;
  for (const [metric, cells] of byMetric) {
    if (!KEEP.test(metric)) { skipped += 1; continue; }
    (Object.values(cells).some((c) => /[1-9]\d*[↑↓]/.test(c)) ? nonzero : zero).push(metric);
  }
  const rows = nonzero.map((m) => ({ label: m, cells: periods.map((p) => byMetric.get(m)[p] || DASH) }));
  const bits = [];
  if (zero.length) bits.push(`no revisions in any window: ${zero.join(", ")}`);
  if (skipped) bits.push(`+${skipped} non-headline metric rows in JSON`);
  return dataTable(label, s.source_ref, periods, rows, bits.join(" · "));
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
  // ENTITLEMENT-RUN COMPRESSION (2026-07-21, from the first T1-expanded export): an item whose
  // four value fields are all withheld-or-blank carries zero information — the license withholds
  // the numbers — yet the expanded print rendered 64 of IT's 250 as full line items (~2 pages of
  // literally nothing). Such a set compresses to ONE counted line per broker-day; the JSON keeps
  // every item, so no fact is deleted — the line says where they live. An item with ANY real
  // field stays verbatim (partial information is information), and at least one field must
  // actually read "Entitlement Needed" for the line's label to be honest — an all-blank item
  // (none exist today) would render verbatim rather than be mislabeled as entitlement-gated.
  const _BLANKS = new Set(["", "-", "—", "NM", "NA"]);           // the pinned blank class
  const fullyGated = (e) => {
    const vals = ["broker_prior", "broker_current", "consensus_before", "consensus_after"]
      .map((f) => String(e[f] ?? "").trim());
    return vals.every((v) => v === "Entitlement Needed" || _BLANKS.has(v))
      && vals.some((v) => v === "Entitlement Needed");
  };
  const expanded = keys.map((k) => {
    const evs = groups.get(k), [dt, broker] = k.split("|");
    const shown = evs.filter((e) => !fullyGated(e));
    const gatedN = evs.length - shown.length;
    const items = shown.map((e) =>
      `<li><b>${escapeHtml(e.metric)}</b> ${escapeHtml(e.period)}: ${escapeHtml(e.broker_prior)}&rarr;${escapeHtml(e.broker_current)} <span class="muted">(cons ${escapeHtml(e.consensus_before)}&rarr;${escapeHtml(e.consensus_after)})</span></li>`).join("");
    const gatedLine = gatedN
      ? `<li class="muted">${gatedN} entitlement-gated item${gatedN === 1 ? "" : "s"} — values withheld by CIQ entitlement; retained in JSON</li>` : "";
    return `<div style="margin-top:7px;"><b>${escapeHtml(dt)} · ${escapeHtml(broker)}</b><ul class="event-log">${items}${gatedLine}</ul></div>`;
  }).join("");
  const details = `<details style="margin-top:6px;"><summary style="cursor:pointer; font-size:12px; color:var(--ink-2);">Expand all ${events.length} revisions per broker-day (on-demand)</summary><div>${expanded}</div></details>`;
  const cite = citeMark(s.source_ref);
  return `<div class="fact"><div class="fact-label">${escapeHtml(label)} <span class="muted">(${events.length} events · ${keys.length} broker-days)</span></div><div>${lines}${moreGroups}${details}${cite}</div></div>`;
}

function catalystPath(cp, cc, dc = null) {
  if (!cp) return "";
  // Fix 5: the legacy consensus facts are gone (duplicated by the reads); fold in the one
  // non-duplicate — Surprise history.
  const surprise = cc ? seriesTable("Surprise history (annual beat/miss)", cc.surprise_history) : "";
  // (restructure) revised guidance is a GUIDANCE fact — it lives here beside the guidance bridge,
  // not on the what-broke card (which keeps read → idio → 8-K evidence).
  const revised = dc ? fact("Revised guidance (8-K 99.1)", dc.revised_guidance) : "";
  // (content relocation 2026-07-24) positioning (insider activity, short interest) moved OUT of
  // this section into the appendix — it is estimates & guidance. Subtitle follows. Twin of
  // render.py's _catalyst_section / _positioning_lines.
  return sec("The street — estimates & guidance",
    "Revision breadth, the monthly consensus path, and guidance delivery.",
    `<div class="muted" style="font-size:11px; margin:-2px 0 8px;">${escapeHtml(catAsof(cp))}</div>` +
    horizonTable(cp.horizon_read) +
    accelTable(cp.acceleration_read) +
    ladderTable(cp.cross_name_anchor) +
    revised +
    guidanceBridge(cp) +
    fact("Consensus stats (target + ratings)", cp.consensus_stats) +
    eventGroups(cp.revision_events) +
    surprise);
}

// (content relocation 2026-07-24) OWNERSHIP & POSITIONING — insider activity + short interest,
// relocated out of "The street". Free DATED feeds: counts, shares and dates only, never an
// interpretation. Omitted entirely when absent (pre-F JSON has neither field) rather than printing
// two empty rows. Twin of render.py's _positioning_lines.
function positioning(m) {
  const cp = (m || {}).catalyst_path;
  if (!cp) return "";
  const rows = (cp.insider_activity
      ? fact("Insider activity (Form 4, 6m)", cp.insider_activity, fmtInsider) : "")
    + (cp.short_interest ? fact("Short interest (FINRA)", cp.short_interest) : "");
  return rows ? sec("Ownership & positioning",
    "Who is buying, selling and short — counts and dates only.", rows) : "";
}

// A reference point in DISPLAY-natural form. The record stores value + unit separately, already in
// display units ("%" / "x" suffix), but a CURRENCY unit prefixes its symbol — "1450.9$M" is not a
// number anyone reads. Twin of render.py _ref_value().
function refValue(value, unit) {
  // EXACT TWIN of render.py _ref_value — pinned by test_ref_value_py_js_parity. The first cut was
  // NOT: py used ",.6g" and this used a bare toLocaleString, so three committed references already
  // rendered differently in the PDF and on the web ($1,416.21M vs $1,416.208M). Two traps that fix
  // avoids: "g" flips to SCIENTIFIC at 1e6, and toLocaleString's default 3-fraction-digit cap
  // silently rounds a non-zero source-bound value to "$0M". Fixed 6 decimals (every committed
  // value carries <=3), trailing zeros trimmed, manual grouping.
  const n = Number(value);
  let s = n.toFixed(6);
  if (Number(s) === 0 && n !== 0) s = n.toFixed(10);   // never display a non-zero as 0
  s = s.replace(/0+$/, "").replace(/\.$/, "");
  const neg = s.startsWith("-");
  if (neg) s = s.slice(1);
  const [ip, fp] = s.split(".");
  s = (neg ? "-" : "") + ip.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (fp ? "." + fp : "");
  const u = String(unit || "");
  return u.startsWith("$") ? "$" + s + u.slice(1) : s + u;
}

// (addition #1, 2026-07-27) "How these numbers were set" — the per-AXIS methodology behind the
// underwrite: the method sentence and the SOURCE-BOUND reference points each leg was chosen
// against. Schema 1.1 has captured this on every record since it shipped and NOTHING rendered it.
// Appendix, because it audits the ANALYST's inputs — the legs themselves live in the Brief grid.
// An UNRATIFIED axis is badged (the card carries `unratified` only when it is). Twin of
// render.py _assumption_methodology_lines().
function assumptionMethodology(card) {
  const axes = ((card || {}).assumptions) || [];
  if (!axes.length) return "";
  const body = axes.map((a) => {
    const badge = a.unratified
      ? ` <span class="pill" style="font-size:10px;">draft — not ratified</span>` : "";
    const name = String(a.axis || "").replace(/^./, (c) => c.toUpperCase());
    // An ALIGNED table, not the old flat <ul>. The original objection — that dataTable right-aligns
    // the SOURCE string as if numeric — was right about dataTable, and dissolved once the source
    // became an endnote: the row is now label + value, and a value column is exactly what
    // right-alignment is for. `.ref-table` is a HOOK, not a width override — these keep the K2
    // content-sized width. A 100% version was tried and REVERTED: it opened a 603–785px gulf
    // between a label and its own value (see the .ref-table note in styles.css).
    // (schema 1.3) leg and exclusion render FROM FIELDS — labels are printed verbatim and never
    // parsed. An excluded row dims with its reason stated; before this, "NOT a reference for us"
    // sat in the same confident aligned column as the numbers that count.
    const refs = (a.references || []).length
      ? `<table class="data ref-table"><tbody>${(a.references || []).map((r) =>
          `<tr${r.excluded ? ` class="uw-ref-excl"` : ""}><td>${escapeHtml(r.label)}${
            r.leg ? ` <span class="uw-leg-chip">${escapeHtml(r.leg)}</span>` : ""}${
            r.excluded
              ? `<span class="muted"> — excluded: ${escapeHtml(r.excludedReason || "")}</span>` : ""
          }</td>`
          + `<td class="num mono">${escapeHtml(refValue(r.value, r.unit))}${citeMark(r.source)}</td>`
          + `</tr>`).join("")}</tbody></table>`
      : `<div class="muted">No reference points recorded — stated as judgment.</div>`;
    // (schema 1.3) dated axis NOTES — analyst findings beside the numbers they interpret (the
    // home the SMPL boundary-cells narrative never had).
    const notes = (a.notes || []).map((n) =>
      `<div class="uw-axis-note muted"><b>${escapeHtml(n.date)}</b> — ${escapeHtml(n.text)}${
        n.source ? `${citeMark(n.source)}` : ""}</div>`).join("");
    // the house in-card sub-head (12px .ds-title), as briefCase/argument use: a bare <b> left the
    // axis NAME, its method prose and its data all at 13px — three roles with no typographic step.
    return `<div class="point"><div class="ds-title" style="font-size:12px;">${escapeHtml(name)}${badge}</div>
      <div style="font-size:13px; margin:3px 0 6px;">${escapeHtml(a.method || "")}</div>
      ${refs}${notes}</div>`;
  }).join("");
  return sec("How these numbers were set",
    "Per-axis methodology from the underwrite record — the reference frame each leg was chosen "
    + "against, not a re-derivation.", body);
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

function synthesis(s, m) {
  // one lead line, not a boxed lecture — the full reading guide lives in the Appendix's
  // "How to read this dossier". The fence's substance (no recommendation anywhere, by design;
  // cited is not verified) is stated once there.
  const fence = `<div class="subtitle muted ds-sub">A verdict-free framing for the analyst — no recommendation or direction anywhere in it, by design. Reading guide in the Appendix.</div>`;
  if (!s) {
    return `<div class="card ds-section"><div class="ds-title">The argument</div>${fence}
      <div class="notice">Synthesis not assembled (source inputs too thin, or the synthesis step was skipped). The mechanical evidence in this tier stands on its own.</div></div>`;
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
  const dv = driverRefs(m);
  return `<div class="card ds-section"><div class="ds-title">The argument</div>${fence}
    ${s.evidence_balance ? `<div style="margin:6px 0 10px; font-size:13.5px; line-height:1.5;">${machineReadHtml(s.evidence_balance)}</div>` : ""}
    <div class="ds-title" style="font-size:12px; margin-top:6px;">Bull case — the decline is overdone</div>
    ${orderPoints(s.bull_points, "bull", decisiveRefs(s, "bull"), dv).map((p) => point(p, "bull")).join("") || `<div class="muted">—</div>`}
    <div class="ds-title" style="font-size:12px; margin-top:14px;">Bear case — the decline is real</div>
    ${orderPoints(s.bear_points, "bear", decisiveRefs(s, "bear"), dv).map((p) => point(p, "bear")).join("") || `<div class="muted">—</div>`}
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

function loggedVerdict(v, ticker, refDate, { bare = false } = {}) {
  const wrap = (inner) => bare
    ? `<div class="fact"><div class="fact-label">Verdict record</div><div class="fact-val">${inner}</div></div>`
    : inner;
  if (!v) {
    const cid = `${ticker}-screen2-${String(refDate || "").replace(/-/g, "")}`;
    if (bare) {
      return wrap(`no verdict logged yet — verdicts are logged via the CLI only, never from this
        dashboard (the friction is the safeguard):
        <pre class="ds-rerun"><code>python -m vinci log-verdict ${escapeHtml(cid)} --verdict &lt;BUY|AVOID_TERMINAL&gt; …</code></pre>
        <span class="muted" style="font-size:11px;">append-only — the entry price freezes from the screen's as-of date (<span class="mono">${escapeHtml(String(refDate || DASH))}</span>); a logged verdict cannot be edited or deleted</span>`);
    }
    return `<details class="card ds-section">
      <summary style="cursor:pointer; font-size:12.5px; font-weight:600; color:var(--ink-2);">Logged verdict <span class="muted" style="font-weight:400;">— none yet for ${escapeHtml(ticker)} · how to log it (read-only — run locally)</span></summary>
      <div class="logged-verdict none" style="margin-top:10px;">Verdicts are logged via the CLI only — never from this dashboard (the friction is the safeguard). After deciding from the facts above, run this locally from the repo root:</div>
      <pre style="background:var(--nav-bg); color:var(--nav-ink); padding:12px 14px; border-radius:8px; font-size:12px; overflow-x:auto; margin:10px 0 0; line-height:1.6;"><code>python -m vinci log-verdict ${escapeHtml(cid)} \\
  --verdict &lt;BUY|AVOID_TERMINAL&gt; \\
  --twin "how the terminal-decline twin is ruled out" \\
  --thesis "the overshoot thesis (or AVOID rationale)" \\
  --kill "what would falsify it" \\
  --horizon-days 180 --confidence &lt;low|medium|high&gt;</code></pre>
      <div class="subtitle muted" style="margin-top:8px;">Append-only — the entry price is frozen from the screen's as-of date (<span class="mono">${escapeHtml(String(refDate || DASH))}</span>); a logged verdict cannot be edited or deleted.</div></details>`;
  }
  const isBuy = isBuyVerdict(v.verdict);
  // CLOSE-AWARE (2026-07-27) — the FIFTH surface of the same defect. The other four were fixed
  // when the ledger row was bound to the record that justified it; this one still read a closed
  // position as a live "BUY · unresolved". Same rule as decision-log.js: the verdict word and
  // `resolved` are untouched (a call is scored at its horizon whatever happened to the position,
  // so exits never launder the track record) — the close is stated as an additive fact.
  const cl = v.closed;
  const closedChip = cl
    ? `<span class="pill unresolved">closed ${fmtDate(cl.exitPriceAsOf)}${
        cl.exitPrice != null ? ` @ ${fmtPrice(cl.exitPrice)}` : ""}${
        cl.realizedReturn != null
          ? ` · ${cl.realizedReturn >= 0 ? "+" : "−"}${Math.abs(cl.realizedReturn * 100).toFixed(2)}%`
          : ""}</span>`
    : "";
  const body = `<div class="logged-verdict">
      <div style="display:flex; gap:12px; align-items:baseline; flex-wrap:wrap;">
        <span class="pill ${cl ? "unresolved" : isBuy ? "buy" : "avoid"}">${escapeHtml(v.verdict)}</span>
        ${closedChip}
        <span class="pill ${v.resolved ? "live" : "unresolved"}">${v.resolved ? "resolved" : "unresolved · " + (v.daysToHorizon == null ? DASH : Math.max(0, v.daysToHorizon) + "d to horizon")}</span>
        <span class="muted" style="font-size:12px; margin-left:auto;">decided ${fmtDate(v.decidedAt)}</span>
      </div>
      ${cl && cl.reason ? `<div class="muted" style="font-size:11.5px; margin-top:6px;">Close reason — ${escapeHtml(cl.reason)}</div>` : ""}
      <div style="display:flex; gap:22px; flex-wrap:wrap; margin-top:10px; font-size:13px;">
        <div><span class="muted">Frozen entry</span> <span class="mono" style="font-weight:600;">${fmtPrice(v.entryPrice)}</span> <span class="muted">@ ${fmtDate(v.entryPriceAsOf)}</span></div>
        <div><span class="muted">Horizon</span> <span class="mono">${v.horizonDays}d</span> → ${fmtDate(v.horizonDate)}</div>
        <div><span class="muted">Confidence</span> ${escapeHtml(v.confidence || DASH)}</div>
        <div><span class="muted">Benchmark</span> <span class="mono">${escapeHtml(v.benchmark || DASH)}</span></div>
      </div>
      ${v.thesis ? `<div style="margin-top:10px;"><span class="muted" style="font-size:11px; text-transform:uppercase;">Thesis</span><div style="font-size:13px; color:var(--ink-2);">${escapeHtml(v.thesis)}</div></div>` : ""}
      ${v.killCriteria ? `<div style="margin-top:8px;"><span class="muted" style="font-size:11px; text-transform:uppercase;">Kill criteria</span><div style="font-size:13px; color:var(--ink-2);">${escapeHtml(v.killCriteria)}</div></div>` : ""}
    </div>`;
  if (bare) return wrap(`logged via the CLI and immutable — this dashboard displays it; it cannot
    edit, delete, or revise it.${body}`);
  return `<div class="card ds-section"><div class="ds-title">Logged verdict — immutable</div>
    <div class="subtitle muted ds-sub">The human's call, logged via the CLI and frozen. This dashboard displays it; it cannot edit, delete, or revise it.</div>
    ${body}</div>`;
}

// a Sourced[list[str]] rendered inline (e.g. gap-down dates)
function listFact(s) {
  if (!s || s.status !== "present" || !Array.isArray(s.value)) return s || {};
  return { status: "present", value: s.value.map((x) => fmtDate(x)).join(" · "), source_ref: s.source_ref };
}
