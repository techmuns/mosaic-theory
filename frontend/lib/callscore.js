// ============================================================================
// LOCAL PREVIEW SCORER — a deliberate py↔JS twin of vinci/calls/{targets,score}.py.
//
// WHY IT EXISTS. Editing a label in the tape changed the chip and nothing else: the readout, the
// target line, the horizon band and the FIT window all read `results.jsonl`, which was scored
// SERVER-SIDE from the label as it was BEFORE the edit. So marking a call bearish left a bearish
// chip sitting beside a bullish-signed return — the two disagreeing on one screen with nothing
// saying so. For a tool whose entire purpose is "read the post, label it, see whether he was
// right", that is the wrong failure.
//
// IT IS A PREVIEW, NOT THE RECORD. `vinci calls score` remains authoritative and writes
// `results.jsonl`; this only recomputes rows the operator has edited in THIS session, and the
// readout says so. The pre-registered conventions are mirrored exactly — entry is the open of the
// next trading day, returns are signed by bias, an unelapsed horizon is OPEN, the 63-day default is
// flagged, both benchmark legs end on the common last bar, and the touch test keys on the LEVEL's
// position rather than the bias.
//
// THE TWIN IS PINNED. tests/test_calls_parity.py runs this file under node against the committed
// corpus and asserts it agrees with the Python scorer row for row. A twin that can drift silently
// is the hazard test_duplicate_definitions.py exists for; this one cannot.
// ============================================================================

export const DEFAULT_HORIZON_DAYS = 63;
const PLAUSIBLE_LO = 0.1, PLAUSIBLE_HI = 10.0;

//: A signed number is recognised ONLY at the start; any later "-" is a range separator, never a
//: sign. Mirrors _PAIR in targets.py.
const PAIR = /^\s*([-+]?\d+(?:\.\d+)?)\s*(?:[-–—]\s*([-+]?\d+(?:\.\d+)?))?/;

/** parse_target() — resolve a stated target to a price, or say why it did not. */
export function parseTarget(target, targetType, entry, bias) {
  const none = (status) => ({ price: null, status });
  if (target == null || targetType == null || targetType === "none"
      || String(target).trim() === "") return none("absent");
  if (targetType === "qualitative") return none("qualitative");

  const raw = String(target).replace(/\$/g, "").replace(/,/g, "").trim();
  const m = PAIR.exec(raw);
  if (!m) return none("unparseable");
  const lo = parseFloat(m[1]);
  const hi = m[2] === undefined ? null : parseFloat(m[2]);

  const plausible = (price) => {
    if (!(price > 0)) return none("implausible");
    if (entry == null || !(entry > 0)) return { price, status: "resolved" };
    const r = price / entry;
    if (r < PLAUSIBLE_LO || r > PLAUSIBLE_HI) return none("implausible");
    return { price, status: "resolved" };
  };
  const directional = (p) => {
    if (p.price == null) return p;
    if (entry == null || !(entry > 0) || (bias !== "bullish" && bias !== "bearish")) return p;
    const against = (bias === "bullish" && p.price < entry) || (bias === "bearish" && p.price > entry);
    return { price: p.price, status: against ? "counter_directional" : "resolved" };
  };

  if (targetType === "point") return directional(plausible(lo));
  if (targetType === "range") {
    if (hi == null) return directional(plausible(lo));
    const low = Math.min(lo, hi), high = Math.max(lo, hi);
    return directional(plausible(bias === "bullish" ? high : low));
  }
  if (targetType === "pct") {
    if (bias !== "bullish" && bias !== "bearish") return none("no_bias");
    const s = raw.replace(/^\s+/, "");
    if ((s.startsWith("-") && bias === "bullish") || (s.startsWith("+") && bias === "bearish")) {
      return none("sign_conflict");
    }
    if (entry == null || !(entry > 0)) return none("no_entry");
    const mag = Math.abs(lo) / 100.0;
    return plausible(bias === "bullish" ? entry * (1 + mag) : entry * (1 - mag));
  }
  return none("unparseable");
}

export const signOf = (bias) => (bias === "bullish" ? 1 : -1);

/** touched() — keyed on WHERE THE LEVEL SITS, not on the stated bias. */
export function touched(price, entry, highs, lows) {
  return price >= entry ? highs.some((h) => h >= price) : lows.some((l) => l <= price);
}

/**
 * score_call() — bars/bench are [{d,o,h,l,c,v}] chronological. Returns the same shape the Python
 * writes into results.jsonl, so a caller can swap one for the other without branching.
 */
export function scoreCall({ tweetId, ticker, posted, bias, target, targetType,
                            horizonLo, horizonHi, bars, bench }) {
  const base = { tweet_id: tweetId, ticker, posted, bias, detail: "",
                 entry: null, entry_date: null, exit: null, exit_date: null,
                 horizon_days: null, horizon_assumed: false,
                 ret: null, bench_ret: null, excess: null, mfe: null, mae: null,
                 target_px: null, target_status: null, target_hit: null, direction_correct: null,
                 mark: null, mark_date: null, elapsed_days: null, unrealised: null,
                 bench_unrealised: null, mfe_to_date: null, mae_to_date: null,
                 target_hit_to_date: null, local: true };
  if (!bars || !bars.length) {
    return { ...base, status: "NO_PRICE_DATA",
             detail: `no committed bars for ${ticker} (delisted, renamed, or an index)` };
  }
  const fwd = bars.filter((b) => b.d > posted);
  if (!fwd.length) {
    return { ...base, status: "NO_ENTRY_BAR",
             detail: "no trading day after the post inside the fetched window" };
  }
  const entry = fwd[0].o, entryDate = fwd[0].d;
  if (!(entry > 0)) {
    // Every figure below divides by the entry — refuse by name rather than emit NaN/Infinity.
    return { ...base, status: "NO_ENTRY_BAR",
             detail: `entry bar ${entryDate} carries a non-positive open (${entry})` };
  }
  const hz = horizonHi || horizonLo || DEFAULT_HORIZON_DAYS;
  const assumed = !(horizonHi || horizonLo);
  // MIRRORS score.py's horizon guard. The Horizon boxes in the tape take free text, so hz can
  // arrive negative, fractional or non-numeric. `winAll[hz]` is then `undefined` and reading
  // `.c` off it throws — inside an awaited paint, which leaves the chart pane stuck on "Drawing…"
  // with the bad value already persisted to localStorage, so a reload reproduces it. Refused by
  // name instead, and by the same rule the CLI uses, so the two cannot disagree about the row.
  if (!Number.isInteger(hz) || hz <= 0) {
    return { ...base, status: "BAD_HORIZON",
             detail: `horizon must be a positive whole number of trading days, got ${JSON.stringify(hz)}` };
  }
  const tp = parseTarget(target, targetType, entry, bias);
  const sign = signOf(bias);
  const winAll = bars.filter((b) => b.d >= entryDate);

  if (winAll.length <= hz) {
    const markBar = winAll[winAll.length - 1];
    const highs = winAll.map((b) => b.h), lows = winAll.map((b) => b.l);
    const bo = (bench || []).filter((b) => b.d >= entryDate && b.d <= markBar.d);
    const bSpans = Boolean(bench && bench.length)
      && bench[0].d <= entryDate && bench[bench.length - 1].d >= markBar.d;
    const bUn = bSpans && bo.length > 1 && bo[0].c > 0
      ? sign * (bo[bo.length - 1].c / bo[0].c - 1) : null;
    return { ...base, status: "OPEN",
             detail: `horizon of ${hz} trading days has not elapsed (${winAll.length - 1} of ${hz} so far)`,
             entry, entry_date: entryDate, horizon_days: hz, horizon_assumed: assumed,
             target_px: tp.price, target_status: tp.status,
             mark: markBar.c, mark_date: markBar.d, elapsed_days: winAll.length - 1,
             unrealised: entry > 0 ? sign * (markBar.c / entry - 1) : null,
             bench_unrealised: bUn,
             mfe_to_date: sign * ((sign > 0 ? Math.max(...highs) : Math.min(...lows)) / entry - 1),
             mae_to_date: sign * ((sign > 0 ? Math.min(...lows) : Math.max(...highs)) / entry - 1),
             target_hit_to_date: tp.price == null ? null : touched(tp.price, entry, highs, lows) };
  }

  const exitBar = winAll[hz];
  const ret = sign * (exitBar.c / entry - 1);
  // THE COMMON LAST BAR — the benchmark must actually SPAN the name's window. If its series stops
  // short of exitBar (or starts after the entry) the two legs measure different windows, so no
  // excess is reported at all rather than one whose sign is set by the gap. (The old trim to
  // `min(bWin.last, exitBar)` could never fire: bWin is already bounded by exitBar.)
  const bWin = (bench || []).filter((b) => b.d >= entryDate && b.d <= exitBar.d);
  const spans = Boolean(bench && bench.length)
    && bench[0].d <= entryDate && bench[bench.length - 1].d >= exitBar.d;
  let benchRet = null;
  if (spans && bWin.length > 1 && bWin[0].c > 0) {
    benchRet = sign * (bWin[bWin.length - 1].c / bWin[0].c - 1);
  }
  const win = winAll.filter((b) => b.d <= exitBar.d);
  const highs = win.map((b) => b.h), lows = win.map((b) => b.l);
  return { ...base, status: "CLOSED",
           entry, entry_date: entryDate, exit: exitBar.c, exit_date: exitBar.d,
           horizon_days: hz, horizon_assumed: assumed,
           ret, bench_ret: benchRet, excess: benchRet == null ? null : ret - benchRet,
           mfe: sign * ((sign > 0 ? Math.max(...highs) : Math.min(...lows)) / entry - 1),
           mae: sign * ((sign > 0 ? Math.min(...lows) : Math.max(...highs)) / entry - 1),
           target_px: tp.price, target_status: tp.status,
           target_hit: tp.price == null ? null : touched(tp.price, entry, highs, lows),
           direction_correct: ret > 0 };
}

export const isScoreable = (bias) => bias === "bullish" || bias === "bearish";
