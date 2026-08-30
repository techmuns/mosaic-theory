// ============================================================================
// THE SINGLE DATA-ACCESS LAYER  (the swappable seam)
// ----------------------------------------------------------------------------
// Every view reads ALL data through the typed functions exported here, and
// consumes only their RETURN VALUES — never a file, path, or fetch directly.
//
// Today these read the committed snapshot files (static, no backend): the
// `vinci` CLI emits snapshots -> they are committed -> Cloudflare serves them
// -> we fetch them from our OWN private origin. That runtime fetch is NOT a
// backend; the site is a static mirror of the last pushed snapshots.
//
// SWAPPABILITY: each function's return SHAPE is defined by what the UI needs,
// independent of the source. If the data source ever changes (a backend API,
// R2 object storage, a DB-backed service), ONLY this file changes — every
// sub-screen stays untouched. Do NOT add backend/adapter scaffolding here; the
// functions read files, full stop. The clean boundary is the future-proofing.
//
// WRITE-PATH DISCIPLINE: there is NO write path. v1 is read-only. If a future
// OPERATIONAL write is ever added (resolve-at-horizon, re-run trigger), it
// lives HERE, behind a deliberate function — components never write directly.
// The integrity-critical writes (logging a verdict, freezing an entry price)
// are PERMANENTLY CLI-only/append-only/immutable by design and must never
// become a frontend action; the friction is the safeguard for the spread.
// ============================================================================
import { fmtMoney } from "./format.js";

const SNAPSHOTS = "./snapshots"; // copied from data/snapshots/ at deploy (build.py)
const DOSSIERS = "./dossiers"; // derived dossier.json only (committed to the PRIVATE repo when authed)
const THEMES = "./themes"; // derived theme-edge display JSON (committed, like dossiers; build.py)
const RADAR = "./radar"; // analyst-owned candidate registry (committed) + emitted sweep bar (build.py)
const SCENARIOS = "./scenarios"; // first-cut underwrite cards (committed, like dossiers; build.py)
const MONITOR = "./monitor"; // committed monitor history — dated marks, never a live fetch

async function _fetch(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) {
    const err = new Error(`snapshot fetch failed (${res.status}) for ${path}`);
    err.status = res.status;
    throw err;
  }
  return res;
}

async function _json(path) {
  return (await _fetch(path)).json();
}

async function _jsonl(path) {
  const text = await (await _fetch(path)).text();
  return text.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
}

// Memoize the in-flight PROMISE (not the resolved value) per key, so concurrent callers — e.g. an
// overview Promise.all where two helpers both want the manifest — share ONE fetch instead of racing
// to issue duplicates. Cleared on rejection so a failed load can be retried on a later call.
const _inflight = new Map();
function _once(key, load) {
  if (!_inflight.has(key)) {
    _inflight.set(key, Promise.resolve().then(load).catch((e) => { _inflight.delete(key); throw e; }));
  }
  return _inflight.get(key);
}

// --- the build-time index (cheap counts + dates + dossier list) --------------
// manifest.json is regenerated from the snapshots on every deploy, so it cannot
// drift from them; it exists only to keep the overview/ingestion cards fast
// without fetching the megabyte-scale candidate files.

function _getManifest() {
  return _once("manifest", () => _json(`${SNAPSHOTS}/manifest.json`));
}

// getSnapshotMeta() -> { sourceCommit, generatedAt }  (provenance for the footer)
export async function getSnapshotMeta() {
  const m = await _getManifest();
  return { sourceCommit: m.source_commit ?? null, generatedAt: m.generated_at ?? null };
}

// getUniverseHealth() -> {
//   universe: { count, asOf }, screen: { candidates, asOf },
//   eod: { asOf }   // prices are frozen as-of the screen's EOD date (point-in-time)
// }
export async function getUniverseHealth() {
  const m = await _getManifest();
  return {
    universe: { count: m.universe?.count ?? null, asOf: m.universe?.as_of ?? null },
    screen: { candidates: m.screen?.candidates ?? null, asOf: m.screen?.as_of ?? null },
    // queue counts come from the manifest (build-time) so the overview never loads the full queue;
    // `total` falls back to screen.candidates for an older manifest that predates the queue block.
    queue: { total: m.queue?.total ?? m.screen?.candidates ?? null, demoted: m.queue?.demoted ?? null },
    eod: { asOf: m.screen?.as_of ?? null },
    // THE LAST RUN'S OUTCOME — the one fact here that is not the age of a committed artifact.
    // ABSENT until the weekly job has reported once, and absent must render as UNKNOWN: a
    // missing status is exactly the "nobody can tell whether it ran" state, never a pass.
    run: m.run
      ? { job: m.run.job ?? null, attemptedAt: m.run.attempted_at ?? null,
          conclusion: m.run.conclusion ?? null, runUrl: m.run.run_url ?? null,
          remediation: m.run.remediation ?? "" }
      : null,
  };
}

// getScreenStatus() -> {
//   asOf, candidates, gates: [{ id, name, rule }]   // gate rules are stable descriptive text
// }
export async function getScreenStatus() {
  const m = await _getManifest();
  return {
    asOf: m.screen?.as_of ?? null,
    candidates: m.screen?.candidates ?? null,
    gates: [
      { id: "G1", name: "Drawdown", rule: "−30% to −85% from the 52-week high — deep but not terminal-by-magnitude." },
      { id: "G2", name: "Idiosyncratic vs market", rule: "Underperformed the market (IWM) over the decline window — strips market beta so what remains is name-specific." },
      { id: "G3", name: "Multiple at its own floor", rule: "Current multiple in the bottom quartile of the name's own ~5-year range (UNKNOWN ⇒ deferred, never imputed)." },
    ],
  };
}

// getRankedQueue() -> {
//   asOf, weights: {idiosyncrasy,depth,character,multiple},
//   counts: { total, demoted, gated, unknownAxis },
//   rows: [{ rank, ticker, name, score, depthBand, quality, volumeOverlay, volumeState, volumeSpike,
//            liquidityTier, advUsd, marketCap, gated, unknownAxes:[],
//            structurallyDisqualified, structuralFlag: {signal,detail,source}|null,
//            axes: { idiosyncrasy, depth, character, multiple } each {score,label,coverage,raw,contribution} }]
// }
let _ranked = null;
export async function getRankedQueue() {
  if (_ranked) return _ranked; // immutable per page load — sorting/filtering is client-side, no re-fetch
  const raw = await _jsonl(`${SNAPSHOTS}/ranked_queue.jsonl`);
  const rows = raw
    .map((r) => ({
      rank: r.rank,
      ticker: r.ticker,
      name: r.name,
      sector: r.sector ?? null, // DERIVED coarse SIC sector — groups the cluster roll-up
      industry: r.industry ?? null, // DERIVED finer sub-industry — the per-name display + sub-breakdown
      score: r.priority_score,
      depthBand: r.depth_band,
      quality: r.quality,
      volumeOverlay: r.volume_overlay,
      volumeState: r.volume_state,
      // the structured ratio behind volumeState's multiple — null on a snapshot written before
      // 2026-08-12, which is why the queue cell keeps a volumeState fallback
      volumeSpike: r.volume_spike ?? null,
      // ~13 weekly volume means on the same 90d denominator, oldest→newest. Populated by a SCREEN
      // run (it is computed from bars in eod/features), so it stays null until the weekly job next
      // re-screens — the queue cell degrades to the bare ratio, which is the pre-sparkline state.
      volumeTrend: Array.isArray(r.volume_trend) ? r.volume_trend : null,
      // THE COHORT SPLIT — how much of the fall was the name's INDUSTRY's and how much its own.
      // Inform-only, attached by the queue writer AFTER ranking; it never re-orders anything.
      // null on a snapshot written before 2026-08-25, so the cell falls back to the bare number.
      cohort: r.cohort ?? null,
      // the evidence strip — inform-only context composed by the WRITER (vinci/evidence.py), null
      // when nothing is known for the name or the snapshot predates the field
      context: r.context ?? null,
      liquidityTier: r.liquidity_tier,
      advUsd: r.adv_usd,
      marketCap: r.market_cap,
      gated: !!r.tradeability_gated,
      unknownAxes: r.unknown_axes || [],
      structurallyDisqualified: !!r.structurally_disqualified,
      structuralFlag: r.structural_flag
        ? { signal: r.structural_flag.signal, detail: r.structural_flag.detail, source: r.structural_flag.source }
        : null,
      axes: Object.fromEntries(
        ["idiosyncrasy", "depth", "character", "multiple"].map((k) => {
          const a = r.axes?.[k] || {};
          return [k, {
            score: a.score, label: a.label, coverage: a.coverage, raw: a.raw,
            contribution: r.contributions?.[k] ?? null,
          }];
        })
      ),
    }))
    .sort((a, b) => a.rank - b.rank);
  _ranked = {
    asOf: raw[0]?.screen_run_at ? String(raw[0].screen_run_at).slice(0, 10) : null,
    weights: { idiosyncrasy: 0.3, depth: 0.25, character: 0.25, multiple: 0.2 },
    counts: {
      total: rows.length,
      demoted: rows.filter((r) => r.structurallyDisqualified).length,
      gated: rows.filter((r) => r.gated).length,
      unknownAxis: rows.filter((r) => r.unknownAxes.length).length,
    },
    rows,
  };
  return _ranked;
}

// getLedger() -> {
//   counts: { logged, resolved, buy, avoid },
//   entries: [{ ticker, verdict, entryPrice, entryPriceAsOf, horizonDays, horizonDate,
//               confidence, benchmark, decidedAt, resolved, daysToHorizon,
//               thesis, killCriteria, twinCall }]   // immutable, append-only
// }
export function getLedger() { return _once("ledger", _loadLedger); }
async function _loadLedger() {
  const raw = await _jsonl(`${SNAPSHOTS}/decision_ledger.jsonl`);
  const today = new Date().toISOString().slice(0, 10);
  // CLOSE ROWS ARE NOT POSITIONS (2026-07-27). Every row was mapped into `entries`, so a closed
  // name appeared TWICE — a close row repeats the ORIGINAL verdict for provenance. That made
  // `counts.logged` read 5 for 3 positions and `counts.buy` read 4 for 2, and left last-row-wins
  // deciding which row a per-ticker lookup returned. This is the JS twin of
  // vinci.monitor.decision_rows / pair_closes: partition first, attach each close to the decision
  // row it closes, and let no consumer mistake a close for a position.
  const payloads = raw.map((r) => (typeof r.payload === "string" ? JSON.parse(r.payload) : r));
  const closeBy = {};
  for (const p of payloads) {
    if (p.event === "CLOSE" && p.closes_entry_id) closeBy[p.closes_entry_id] = p;
  }
  const entries = payloads
    .filter((p) => !p.event)                                   // decision rows only
    .map((p) => {
      const horizonDate = _addDays(p.entry_price_as_of, p.horizon_days);
      const daysToHorizon = horizonDate ? _diffDays(today, horizonDate) : null;
      const cl = closeBy[p.entry_id];
      return {
        ticker: p.ticker,
        entryId: p.entry_id,
        verdict: p.verdict,
        entryPrice: p.entry_price,
        entryPriceAsOf: p.entry_price_as_of,
        horizonDays: p.horizon_days,
        horizonDate,
        confidence: p.confidence,
        benchmark: p.benchmark,
        decidedAt: p.decided_at,
        // WHICH ROUTE and WHICH BOOK. Dropped here, nothing downstream could filter or label by
        // them — which is why the gate stat below pooled every book into the fund's proof number.
        // Absent == a row logged before the fields existed, and its truthful reading is
        // screen/overshoot: no other route could reach this ledger then (mirrors origin_of /
        // sleeve_of on the python side — one meaning, two languages).
        origin: p.origin || "screen",
        sleeve: p.sleeve || "overshoot",
        // the call is STILL scored at its horizon after a close — exits never launder the track
        // record — so `resolved` is untouched; `closed` is a separate, additive fact.
        resolved: daysToHorizon !== null ? daysToHorizon <= 0 : false,
        daysToHorizon,
        ...(cl ? {
          closed: {
            exitPrice: cl.exit_price,
            exitPriceAsOf: cl.exit_price_as_of,
            reason: cl.reason,
            closeEntryId: cl.entry_id,
            // derived here, never stored — two frozen prices, one truth
            realizedReturn: (typeof cl.exit_price === "number" && p.entry_price)
              ? cl.exit_price / p.entry_price - 1 : null,
          },
        } : {}),
        thesis: p.thesis,
        killCriteria: p.kill_criteria,
        twinCall: p.twin_call,
      };
    })
    .sort((a, b) => String(b.decidedAt).localeCompare(String(a.decidedAt)));
  // (grouping lives in `groupOtherBooks` below — exported so a test can EXECUTE it against a
  // followed-overshoot row rather than grep this file for a variable name.)
  // THE PROOF NUMBER IS SCREEN-ORIGIN ONLY, matching scoring/metrics.py and vinci monitor. The
  // gate widget below is labelled "the BUY−AVOID spread that must prove positive before capital
  // deploys" — pooling a followed megacap verdict into it would silently change what the number
  // means on the deployed page while the python side reported something else.
  const primary = entries.filter((e) => e.origin === "screen");
  // …and the other books are counted BESIDE it, never inside it, so a followed row is excluded
  // from the proof number without disappearing from the app entirely.
  //
  // GROUPED ON (origin, sleeve) OVER THE NON-PRIMARY ROWS — not on the sleeve alone, and this is
  // the distinction the first cut got wrong (review #382). What excludes a row from the proof
  // number is its ORIGIN; the sleeve only says which book it belongs to. `followed.json`
  // legitimately admits a followed name under the DEFAULT book (assemble.py refuses a
  // screen/follow overlap only when the sleeve DIFFERS), so a followed-overshoot row keyed on
  // "overshoot" merged into the screen majority's bucket — and the only consumer of this map
  // drops the "overshoot" key. That row was therefore out of `primary`, invisible under "Other
  // books", and chip-less on its own line: counted nowhere and labelled nothing, while the
  // overview tile simultaneously announced "1 in other books". Keying on the pair makes the
  // fold impossible, and each bucket carries both parts so the renderer can name the book
  // without re-deriving them from the key string.
  const otherBooks = groupOtherBooks(entries);
  return {
    counts: {
      logged: primary.length,
      resolved: primary.filter((e) => e.resolved).length,
      buy: primary.filter((e) => isBuyVerdict(e.verdict)).length,
      avoid: primary.filter((e) => !isBuyVerdict(e.verdict)).length,
      loggedAllBooks: entries.length,
    },
    otherBooks,
    entries,
  };
}

// getMonitor() -> the LATEST committed monitor snapshot {as_of, rows[], spread, freshness[],
// price_basis, notes[]} or null when no history is committed. The browser NEVER fetches a live
// price: every mark it shows is a dated, committed number the repo can reproduce. Absent history
// degrades the live columns to "—" rather than inventing a mark.
export function getMonitor() { return _once("monitor", _loadMonitor); }
async function _loadMonitor() {
  try {
    const idx = await _json(`${MONITOR}/index.json`);
    if (!idx || !idx.latest) return null;
    return await _json(`${MONITOR}/${idx.latest}.json`);
  } catch (e) {
    if (e.status === 404) return null;   // none committed yet
    throw e;
  }
}

// getMonitorRow(ticker) -> that name's row in the latest snapshot, or null. The spot the card
// shows for its implied-odds line comes from HERE — a committed mark, dated on screen.
export async function getMonitorRow(ticker) {
  const snap = await getMonitor();
  const t = String(ticker || "").toUpperCase();
  return (snap && (snap.rows || []).find((r) => String(r.ticker).toUpperCase() === t)) || null;
}

// The long leg is any BUY-family verdict; everything else (AVOID_TERMINAL, …) is the avoid leg.
// Classify by family, not exact equality, so a future BUY_* verdict isn't miscounted as avoid.
// The DISPLAY WORD for a verdict of record. HERE, beside isBuyVerdict, because BOTH views
// need it: the shelf and the decision log were printing the same verdict two different ways
// (AVOID vs AVOID_TERMINAL) because only one of them had this function. Mirrors MachineProposal.action_word on the py side.
// AVOID_TERMINAL still shortens to AVOID; every other label prints ITSELF.
//
// IT USED TO SHORTEN BY ASSUMING THERE WERE ONLY TWO. `buy ? "BUY" : "AVOID"` was lossless while
// BUY and AVOID_TERMINAL were the whole vocabulary — and the moment a sleeve added its own
// negative leg it would have printed "AVOID" over a PASS, which is precisely the false record the
// separate label exists to prevent: PASS says "not at this price", never "this is dying".
export function verdictWord(verdict) {
  const v = String(verdict || "").toUpperCase();
  return v === "AVOID_TERMINAL" ? "AVOID" : v;
}

export function isBuyVerdict(v) {
  return String(v || "").toUpperCase().startsWith("BUY");
}

// The books counted BESIDE the primary composite — every ledger entry the screen-origin proof
// number excludes, grouped so none of them can go uncounted.
//
// KEYED ON (origin, sleeve), NOT on the sleeve alone. What excludes a row is its ORIGIN; the
// sleeve only says which book it is. `followed.json` legitimately admits a followed name under
// the DEFAULT book — assemble.py refuses a screen/follow overlap only when the sleeve DIFFERS —
// so keying on the sleeve merged a followed-overshoot row into the screen majority's bucket,
// which the renderer then dropped as "the default book". The row was out of `primary`, absent
// from "Other books" and chip-less, while the overview tile announced "1 in other books"
// (review #382). Each bucket carries both parts so the renderer names the book without
// re-parsing the key.
export function groupOtherBooks(entries) {
  const out = {};
  for (const e of entries || []) {
    if ((e.origin || "screen") === "screen") continue;  // in the composite; `counts` has it
    const origin = e.origin, sleeve = e.sleeve || "overshoot";
    const b = (out[`${origin}:${sleeve}`] ||=
      { origin, sleeve, logged: 0, resolved: 0, long: 0, short: 0 });
    b.logged += 1;
    if (e.resolved) b.resolved += 1;
    if (isBuyVerdict(e.verdict)) b.long += 1; else b.short += 1;
  }
  return out;
}

// getSpreadStatus() -> {
//   spread, resolvedCount, buyLegs, avoidLegs, gateMet, definition
// }   // spread is null until verdicts resolve — the gate's headline number
export async function getSpreadStatus() {
  const led = await getLedger();
  const resolved = led.counts.resolved;
  return {
    spread: resolved > 0 ? null : null, // computed from RESOLVED forward returns only; none yet
    resolvedCount: resolved,
    buyLegs: led.counts.buy,
    avoidLegs: led.counts.avoid,
    loggedCount: led.counts.logged,
    gateMet: false, // requires >=2 quarters of resolved verdicts, both legs, positive & real
    definition: "the BUY−AVOID spread that must prove positive before capital deploys",
  };
}

// ONE fetch for the dossier index — getDossierIndex + getGicsLabels both want it (the ranker
// calls both via getProcessedStates + the overlay), so they share the repo's _once memoizer
// instead of racing two no-store requests. 404 -> null (none committed yet, authed-deploy gate).
function _dossierIndex() {
  return _once("dossier-index", () =>
    _json(`${DOSSIERS}/index.json`).catch((e) => {
      if (e.status === 404) return null;
      throw e;
    }));
}

// getDossierIndex() -> [ticker, ...]  (committed, derived dossiers available to the viewer)
export async function getDossierIndex() {
  const idx = await _dossierIndex();
  return Array.isArray(idx?.tickers) ? idx.tickers : [];
}

// getGicsLabels() -> {TICKER: {industry, source, source_ref}} — the CIQ-GICS overlay build.py
// emits into the dossier index (present-status only). A name with a committed dossier upgrades
// its Industry label everywhere this is consumed, the moment the dossier commits — no queue
// re-emit. Old committed index without `labels` -> {} (today's behavior, no overlay).
export async function getGicsLabels() {
  const idx = await _dossierIndex();
  return idx && typeof idx.labels === "object" && idx.labels ? idx.labels : {};
}

// getMachineReads() -> {TICKER: "<lean> — <why>"} — each committed dossier's synthesis evidence
// balance, RAW and unparsed (the one shared lean parser lives in dossier.js; nothing here splits
// it). This is the machine's evidence LEAN — already shown openly on the Brief with its rationale
// — NOT the sealed BUY/AVOID proposal, which stays hidden until the human logs their verdict.
export async function getMachineReads() {
  const idx = await _dossierIndex();
  return idx && typeof idx.reads === "object" && idx.reads ? idx.reads : {};
}

// getSleeves() -> {TICKER: sleeve} — WHICH STRATEGY BOOK each committed dossier is judged under
// (vinci/sleeves.py). The shelf uses it to say so without opening the page: a quality name asks a
// different question and records a different verdict vocabulary, and a reader meeting that with no
// label has to infer the book from the copy. An index committed before the tag existed -> {}, and
// consumers fall back to the default book, which is truthful for every one of those names.
export async function getSleeves() {
  const idx = await _dossierIndex();
  return idx && typeof idx.sleeves === "object" && idx.sleeves ? idx.sleeves : {};
}

// The per-name WORKFLOW-state vocabulary — ONE definition (MED-7): getProcessedStates() returns
// these keys; consumers (the ranker badge/sort) import THIS object instead of re-typing strings.
export const WORKFLOW_STATES = {
  "not-started": 0, "underwritten": 1, "dossier-built": 2, "verdict-logged": 3,
};

// getScenarioIndex() -> [ticker, ...] (committed first-cut underwrite records; NOT dossiers)
export async function getScenarioIndex() {
  try {
    const idx = await _json(`${SCENARIOS}/index.json`);
    return Array.isArray(idx?.tickers) ? idx.tickers : [];
  } catch (e) {
    if (e.status === 404) return []; // none committed yet
    throw e;
  }
}

// getScenarioCard(ticker) -> the display-card shape build.py emits (same shape the theme JSON
// embeds as `scenarioCard` — ONE contract), or null if absent.
export async function getScenarioCard(ticker) {
  try {
    return await _json(`${SCENARIOS}/${String(ticker).toUpperCase()}.json`);
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

// getDossier(ticker) -> the Dossier shape (mechanical + synthesis + flags + meta), or null if absent.
export async function getDossier(ticker) {
  try {
    return await _json(`${DOSSIERS}/${String(ticker).toUpperCase()}.json`);
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

// --- theme edge (read-only display JSON produced by build.py from the frozen freeze) -----------
// getThemesIndex() -> { drivers: [{ slug, label, freezeDate, ratifiedCount, surfacedCount,
//   frozenCount, watchlistCount, tierShape:{binding,quantified,committed,aspirational,none,
//   surfaced,universe} }], crossDriver: { driversFrozen, totalRatified, totalWatchlist, line } | null }
// Empty ({ drivers: [], crossDriver: null }) when no theme artifacts are committed to this deploy.
export async function getThemesIndex() {
  try {
    const idx = await _json(`${THEMES}/index.json`);
    return {
      drivers: Array.isArray(idx?.drivers) ? idx.drivers : [],
      crossDriver: idx?.crossDriver ?? null,
      pooledForward: idx?.pooledForward ?? null,
    };
  } catch (e) {
    if (e.status === 404) return { drivers: [], crossDriver: null, pooledForward: null };
    throw e;
  }
}

// getRadarCandidates() -> { candidates: [{ slug, label, status, source, px12m, map:{x,y,basis}, tip,
//   theme_route?, detail:{summary?, watch?, comparison?, rules?, lead?, note?} }] }. Empty on 404 (no
// committed registry). Analyst-owned — rules render VERBATIM; the view never fabricates a disposition.
export async function getRadarCandidates() {
  try {
    const d = await _json(`${RADAR}/candidates.json`);
    return { candidates: Array.isArray(d?.candidates) ? d.candidates : [] };
  } catch (e) {
    if (e.status === 404) return { candidates: [] };
    throw e;
  }
}

// getRadarSweep() -> { last_run, source, next_due, command } | null (404 = no committed sweep). Emitted
// by build.py from the component-a scan_history manifest; DISPLAY-only reminder, nothing fires.
export async function getRadarSweep() {
  try {
    return await _json(`${RADAR}/sweep.json`);
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

// getRadarInbox() -> { scan_date, inbox: [{ cluster_id, first_seen, members, label, rel12, mom12,
//   coherence, breadth_exp, crowding }] }. Emitted by build.py — current sweep clusters NOT yet
//   matched to a review. Empty on 404. The machine sorts here; reviews.json holds the decisions.
export async function getRadarInbox() {
  try {
    const d = await _json(`${RADAR}/inbox.json`);
    return { scan_date: d?.scan_date || "", inbox: Array.isArray(d?.inbox) ? d.inbox : [] };
  } catch (e) {
    if (e.status === 404) return { scan_date: "", inbox: [] };
    throw e;
  }
}

// getRadarLog() -> { scan_date, reviews: [{...reviews.json entry, match:{status, cluster_id, added,
//   dropped}}] }. Emitted by build.py — the analyst's recorded dispositions + current match status.
//   Reasons render VERBATIM from reviews.json (the single record); empty on 404.
export async function getRadarLog() {
  try {
    const d = await _json(`${RADAR}/log.json`);
    return { scan_date: d?.scan_date || "", reviews: Array.isArray(d?.reviews) ? d.reviews : [] };
  } catch (e) {
    if (e.status === 404) return { scan_date: "", reviews: [] };
    throw e;
  }
}

// getThemeDriver(slug) -> the per-driver display object (cohorts, tierShape, names, watchlist +
// triggers, avoidControls, realTier, forward:{cohorts, undefinedMeasures, diagnostics, honestyLabel,
// powerNote}), or null if that driver is not committed.
export async function getThemeDriver(slug) {
  try {
    return await _json(`${THEMES}/${String(slug).toLowerCase()}.json`);
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

// getThemeContext(slug) -> { driver_summary:{quote, source}, analyst_notes:[string] } for one theme,
// or null (theme absent, or context.json not committed to this deploy → graceful absence). One
// committed analyst-owned file joined at view time; driver_summary is quoted from the ratified spec.
export async function getThemeContext(slug) {
  try {
    const all = await _once("theme-context", () => _json(`${THEMES}/context.json`));
    return all?.[String(slug).toLowerCase()] ?? null;
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

// getThemeThesis(slug) -> the driver's declared thesis card (operator-typed only; mirrored
// VERBATIM by the build under the registry-stamped slug), or null — and null IS the
// "THESIS UNSTATED" state the page stamps loudly (ruling R2: absence must never look like
// passage). Shape: vinci.themes.thesis.ThemeThesis.
export async function getThemeThesis(slug) {
  try {
    return await _json(`${THEMES}/thesis/${String(slug).toLowerCase()}.json`);
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

// getThemeEconomics(slug) -> the inform-only per-member economics roll-up (NO composite, by pin;
// vinci.themes.rollup.ThemeEconomicsRollup), or null — not yet assembled, and the page says so
// rather than rendering nothing.
export async function getThemeEconomics(slug) {
  try {
    return await _json(`${THEMES}/economics/${String(slug).toLowerCase()}.json`);
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

// getGraphCoverage() -> {
//   available, model, stats: {names,withEdges,totalEdges,realEdges,realUsListed},
//   edges: [{focal, counterpartyName, counterpartyTicker, relType, direction, resolution, evidence}],
//   sharedNodes: [{name,ticker,focals,degree,...}], superConnectors: [ticker,...]
// }
// The graph is a RESEARCH INPUT — it gates nothing and predicts nothing (Edge-3 falsified).
let _graph = null;
export async function getGraphCoverage() {
  if (_graph) return _graph;
  try {
    const g = await _json(`${SNAPSHOTS}/graph.json`);
    _graph = { available: true, ...g };
  } catch (e) {
    if (e.status === 404) _graph = { available: false, edges: [], sharedNodes: [], superConnectors: [] };
    else throw e;
  }
  return _graph;
}

// getGraphExposure(entity) -> {
//   available, entity, found,
//   asFocal:  [{counterparty, ticker, relType, direction, resolution, evidence}],   // entity's own 10-K disclosures
//   namedBy:  [{focal, relType, direction, evidence}],                              // who discloses exposure to entity
//   coExposed:[{ticker, via}]                                                       // names sharing a counterparty (cross-section)
// }
// Pure client-side traversal of the committed exposure map. Research lookup only.
export async function getGraphExposure(entity) {
  const g = await getGraphCoverage();
  if (!g.available) return { available: false, entity, found: false };
  const q = String(entity || "").trim().toUpperCase();
  if (!q) return { available: true, entity: "", found: false, asFocal: [], namedBy: [], coExposed: [] };

  const matchCp = (e) =>
    (e.counterpartyTicker && e.counterpartyTicker.toUpperCase() === q) ||
    (e.counterpartyName && e.counterpartyName.toUpperCase().includes(q));

  const asFocal = g.edges.filter((e) => (e.focal || "").toUpperCase() === q).map((e) => ({
    counterparty: e.counterpartyName, ticker: e.counterpartyTicker, relType: e.relType,
    direction: e.direction, resolution: e.resolution, evidence: e.evidence,
  }));
  const namedBy = g.edges.filter(matchCp).map((e) => ({
    focal: e.focal, relType: e.relType, direction: e.direction, evidence: e.evidence,
  }));

  // co-exposed cross-section: other focals that share any counterparty with this entity (2-hop)
  const myCps = new Set(asFocal.map((e) => (e.ticker || e.counterparty || "").toUpperCase()).filter(Boolean));
  const coExposed = [];
  if (myCps.size) {
    const seen = new Set([q]);
    for (const e of g.edges) {
      const f = (e.focal || "").toUpperCase();
      const cp = (e.counterpartyTicker || e.counterpartyName || "").toUpperCase();
      if (f && f !== q && myCps.has(cp) && !seen.has(f)) {
        seen.add(f);
        coExposed.push({ ticker: e.focal, via: e.counterpartyName });
      }
    }
  }
  return { available: true, entity: q, found: asFocal.length + namedBy.length > 0, asFocal, namedBy, coExposed };
}

// getScreenAdmitted() -> { asOf, count, gates:[{id,name,rule}],
//   names:[{ticker, name, depthBand, depthLabel, idioLabel, multipleLabel}] }
// THIS edge's admitted set — the names that passed the Overshoot gates (G1/G2/G3). Order-agnostic
// (sorted by ticker), distinct from the ranker's cross-edge priority order. The structural demote is
// a RANKER overlay, not a screen gate, so it is intentionally absent here.
let _g3 = null;
export async function getG3Reasons() {
  if (_g3) return _g3;
  try { _g3 = await _json(`${SNAPSHOTS}/g3_reasons.json`); }
  catch (e) { if (e.status === 404) _g3 = {}; else throw e; }
  return _g3;
}

export async function getScreenAdmitted() {
  const [q, status, g3] = await Promise.all([getRankedQueue(), getScreenStatus(), getG3Reasons()]);
  const names = q.rows
    .map((r) => {
      const mUnknown = r.axes.multiple?.coverage === "unknown";
      return {
        ticker: r.ticker, name: r.name, depthBand: r.depthBand,
        sector: r.sector ?? null, industry: r.industry ?? null,
        depthLabel: r.axes.depth?.label, idioLabel: r.axes.idiosyncrasy?.label,
        // G3 UNKNOWN → the specific per-name reason (negative earnings vs XBRL gap), never a slash-menu
        multipleLabel: mUnknown ? (g3[r.ticker] || "multiple unavailable") : r.axes.multiple?.label,
        multipleUnknown: mUnknown,
      };
    })
    .sort((a, b) => a.ticker.localeCompare(b.ticker));
  return { asOf: q.asOf, count: names.length, gates: status.gates, names };
}

// getUniverseStats() -> { available, asOf, considered, inUniverse, gates:[{label, count, sub}] }
// The universe builder's fail-closed gate-exclusion counts (HEALTH, not analytics — a wrong count
// signals a gate bug). The two structural gates (SIC denylist, security-type allowlist) each carry a
// confirmed-drop count + an unconfirmable-input sub-count, both fail-closed (excluded, never admitted).
export async function getUniverseStats() {
  try {
    const s = await _json(`${SNAPSHOTS}/universe_stats.json`);
    const n = (k) => s[k] ?? 0;
    const band = { capMin: s.market_cap_min_usd ?? null, capMax: s.market_cap_max_usd ?? null, advFloor: s.adv_floor_usd ?? null };
    const capTxt = band.capMin != null ? `outside ${fmtMoney(band.capMin)}–${fmtMoney(band.capMax)}` : "outside the market-cap window";
    const advTxt = band.advFloor != null ? `below ${fmtMoney(band.advFloor)} 90-day ADV — too thin to build a position` : "too thin to build a position";
    return {
      available: true, asOf: s.as_of ?? null, considered: n("considered"), inUniverse: n("in_universe"), band,
      gates: [
        // 2a: the exclusion is a genuine no-bar, not a swallowed error — a degraded Polygon fetch
        // raises EodError and aborts the whole refresh, so only a legitimate no-trade lands here.
        { label: "Missing price", count: n("no_price"), sub: "no trade in the 90-day window (delisted / illiquid) — fetch errors fail loud, never counted here" },
        { label: "Missing shares", count: n("no_shares"), sub: "EDGAR reported no shares-outstanding figure — market cap can't be computed" },
        { label: "Out of cap band", count: n("out_of_band"), sub: capTxt },
        { label: "Below ADV floor", count: n("below_adv_floor"), sub: advTxt },
        { label: "SIC denylist", count: n("non_operating") + n("unknown_sic"), sub: `fund / ETP / blank-check (${n("non_operating")}) + unconfirmable SIC (${n("unknown_sic")})` },
        { label: "Security-type allowlist", count: n("non_common_equity") + n("unknown_type"), sub: `not common equity (${n("non_common_equity")}) + unconfirmable type (${n("unknown_type")})` },
      ],
    };
  } catch (e) {
    if (e.status === 404) return { available: false };
    throw e;
  }
}

// getProcessedStates() -> (ticker) => "verdict-logged" | "dossier-built" | "underwritten" | "not-started"
// Per-name WORKFLOW state, derived (read-only) from committed dossier presence + ledger presence
// + scenario-record PRESENCE (never the scenario verdict — workflow state, not a ledger read).
// Turns the queue into a workflow surface; it reads those snapshots, it never writes them.
export async function getProcessedStates() {
  const [dossiers, led, scen] = await Promise.all([
    getDossierIndex(), getLedger(), getScenarioIndex()]);
  const built = new Set(dossiers.map((t) => String(t).toUpperCase()));
  const logged = new Set(led.entries.map((e) => String(e.ticker).toUpperCase()));
  const underwritten = new Set(scen.map((t) => String(t).toUpperCase()));
  return (ticker) => {
    const t = String(ticker).toUpperCase();
    if (logged.has(t)) return "verdict-logged";
    if (built.has(t)) return "dossier-built";
    if (underwritten.has(t)) return "underwritten";
    return "not-started";
  };
}

// --- the CALLS TAPE (one X account per directory) -----------------------------
// Everything is namespaced by HANDLE so a second account is a directory drop, never a code change.
// The month files and per-ticker bars are the only large payloads here, so both are fetched lazily
// and memoised per key — a browse across one month must not pull 2.6 MB of posts or 6 MB of bars.
const CALLS = "./calls";

// getCallAccounts() -> { default, accounts:[{handle, display, first, last, n_posts, ...}] }
export async function getCallAccounts() {
  return _once("calls-accounts", () => _json(`${CALLS}/accounts.json`));
}

// getCallDays(handle) -> { "YYYY-MM-DD": {n, tk[], lab, sig} }  — drives the calendar + timeline
export async function getCallDays(handle) {
  return _once(`calls-days-${handle}`, () => _json(`${CALLS}/${handle}/days.json`));
}

// getCallPosts(handle, "YYYY-MM") -> [{id, t, d, txt, tk[], v, p, q, lk, vw, url}]
export async function getCallPosts(handle, month) {
  return _once(`calls-posts-${handle}-${month}`, () => _json(`${CALLS}/${handle}/posts/${month}.json`));
}

// getCallLabels(handle) -> { "<tweet_id>|<TICKER>": {bias, action, target, target_type, hlo, hhi,
//                                                    spec, src, needs_review, post_class} }
export async function getCallLabels(handle) {
  return _once(`calls-labels-${handle}`, () => _json(`${CALLS}/${handle}/labels.json`));
}

// getCallTickers(handle) -> { renamed:{OLD:NEW|null}, tickers:[{ticker, mentions, ...}] }
export async function getCallTickers(handle) {
  return _once(`calls-tickers-${handle}`, () => _json(`${CALLS}/${handle}/tickers.json`));
}

// getCallBars(handle, ticker) -> [{d, o, h, l, c, v}]  (chronological; [] when the symbol has none)
// A DELISTED OR RENAMED SYMBOL RESOLVES TO [], NEVER A THROW: three of this account's tickers carry
// no bars at all (BRKB, DOGE, SPX), and the chart pane must render an empty state rather than take
// the screen down — the reader is mid-labelling and would lose their place.
export async function getCallBars(handle, ticker) {
  return _once(`calls-bars-${handle}-${ticker}`, async () => {
    try {
      const raw = await _json(`${CALLS}/${handle}/bars/${ticker}.json`);
      // STRUCTURED VALUES, not display strings: the file stores compact rows
      // [iso, open, high, low, close, volume] to keep 214 tickers off the wire as repeated keys.
      return (raw.bars || []).map((r) => ({ d: r[0], o: r[1], h: r[2], l: r[3], c: r[4], v: r[5] }));
    } catch (e) {
      if (e && e.status === 404) return [];
      throw e;
    }
  });
}

// getCallResults(handle) -> Map("<tweet_id>|<TICKER>" -> scored row)  — written by `vinci calls score`
export async function getCallResults(handle) {
  return _once(`calls-results-${handle}`, async () => {
    try {
      const rows = await _jsonl(`${CALLS}/${handle}/results.jsonl`);
      return new Map(rows.map((r) => [`${r.tweet_id}|${r.ticker}`, r]));
    } catch (e) {
      if (e && e.status === 404) return new Map();
      throw e;
    }
  });
}

// --- internal date helpers (UTC-safe) ----------------------------------------
function _addDays(iso, days) {
  if (!iso || typeof days !== "number") return null;
  const d = new Date(String(iso).slice(0, 10) + "T00:00:00Z");
  if (isNaN(d)) return null;
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
function _diffDays(aIso, bIso) {
  const a = new Date(aIso + "T00:00:00Z");
  const b = new Date(bIso + "T00:00:00Z");
  return Math.round((b - a) / 86400000);
}
