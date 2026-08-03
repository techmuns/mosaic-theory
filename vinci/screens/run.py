"""Run Screen 2 across the stored universe — lazily, so it scales to thousands of names.

The price gates (G1 drawdown, G2 idiosyncratic) are computed from EOD bars for **every** name;
only the survivors pay an EDGAR fetch (G3 multiple-at-floor + non-distress). That confines the
per-name EDGAR cost to the handful of genuine de-ratings rather than the whole universe — the
cheap-gates-gate-the-expensive-ones discipline made operational.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from vinci.edgar import EdgarClient
from vinci.eod import EodClient, ingest_prices
from vinci.eod.features import YEAR_DAYS, window_facts
from vinci.progress import ProgressFn, ProgressReporter
from vinci.schemas.candidate import CandidateRecord, GateResult, RoutingPolicy
from vinci.schemas.envelope import DataField
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import (
    DECLINE_WINDOW_DAYS,
    build_price_record,
    enrich_with_fundamentals,
)
from vinci.screens.retention import (
    CandidateRow,
    GateOutcome,
    Outcome,
    StampedInput,
    append_rows,
    outcome_from_gate,
    read_manifest,
    rollup,
)
from vinci.screens.screen2 import (
    Screen2Thresholds,
    evaluate_screen2,
    gate_g1_drawdown,
    gate_g2_idiosyncratic,
    gate_g3_multiple_floor,
)
from vinci.store import Store
from vinci.universe import benchmark_identity


def screen_universe(
    store: Store,
    eod: EodClient,
    edgar: EdgarClient,
    *,
    reference_date: date,
    lookback_days: int,
    staleness_days: int,
    benchmark: str = "IWM",
    thresholds: Screen2Thresholds | None = None,
    progress: ProgressFn | None = None,
    retain_run_id: str | None = None,
    retain_dir: Path | None = None,
    policy: RoutingPolicy = RoutingPolicy.CARRY,
) -> tuple[list[CandidateRecord], dict[str, int | str | None]]:
    """Refresh prices, lazily screen the universe, persist candidates; return them + stats.

    RETENTION (``retain_run_id`` + ``retain_dir``, both or neither). Every name the screen TOUCHES
    gets a candidate row — all ~1,800, not the ~318 that survive. The gates ran on them, so the
    record says what the gates saw; a name dropped at G1 simply carries one gate rather than five.

    The reject set is the population that makes the gates falsifiable. Retaining survivors only can
    confirm the screen and never contradict it, and the 2026-07-27 benchmark bound was recoverable
    only because the survivors' values happened to persist — luck, not method.
    """
    # BOTH OR NEITHER, ENFORCED (review finding). The first cut COLLECTED rows on `retain_run_id`
    # but only WROTE them when `retain_dir` was also set — so a caller passing one and not the other
    # got 1,800 rows built, silently dropped, and a stats dict REPORTING them as retained. A
    # partially-configured retention that claims success is worse than one that refuses.
    if (retain_run_id is None) != (retain_dir is None):
        raise ValueError(
            "retain_run_id and retain_dir must be given together — one without the other builds "
            "retention rows and discards them while reporting them as retained")
    # THE MANIFEST MUST AGREE WITH THE RUN (review finding). `routing_policy` was recorded on the
    # manifest and passed to this function, with NOTHING binding them — so a run could execute under
    # DROP while its own record said CARRY. That is the record stating something the run did not do,
    # which is the precise failure the manifest was added to prevent: a pool count is meaningless
    # without the policy, and worse than meaningless if the policy is wrong.
    if retain_run_id is not None and retain_dir is not None:
        recorded = read_manifest(retain_run_id, retain_dir)
        if recorded is not None and recorded.routing_policy is not policy:
            raise ValueError(
                f"manifest for {retain_run_id} records routing_policy="
                f"{recorded.routing_policy.value!r} but the run is executing "
                f"{policy.value!r} — the record would state a policy the run did not use")
    th = thresholds or Screen2Thresholds()
    # Screen the cap-band universe membership (not every security ever stored). Fall back to all
    # non-benchmark securities when no universe snapshot exists yet (e.g. a small test seed).
    # THE POPULATION'S OWN VINTAGE, read BEFORE the members so the two cannot disagree.
    universe_as_of = store.latest_universe_as_of(reference_date)
    caps = store.universe_caps(universe_as_of) if universe_as_of else {}
    ids = store.latest_universe(reference_date)
    if ids:
        universe = [s for iid in ids if (s := store.get_security(iid)) is not None]
    else:
        universe = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
    start = reference_date - timedelta(days=lookback_days)

    ingest_prices(eod, store, universe, start=start, end=reference_date, progress=progress)
    bench = benchmark_identity(benchmark)
    store.upsert_security(bench)
    ingest_prices(eod, store, [bench], start=start, end=reference_date)
    bench_bars = store.get_price_history(bench.internal_id)

    run_at = datetime.combine(reference_date, datetime.min.time())
    store.clear_candidates()  # FULL replace — a re-screen is a clean snapshot, never an accretion
    candidates: list[CandidateRecord] = []
    g1_survivors = 0
    reporter = ProgressReporter("screen", len(universe), emit=progress, step=200)
    retained: list[CandidateRow] = []

    # EACH INPUT'S OWN WINDOW START — G2 compares over the decline window, G1 over 52 weeks. One
    # start for both would mis-describe whichever it did not belong to.
    win_start = {"rel_ret_vs_market": reference_date - timedelta(days=DECLINE_WINDOW_DAYS),
                 "drawdown_from_high": reference_date - timedelta(days=YEAR_DAYS)}

    def _keep(sec_ticker: str, rec: object, gates: dict[str, GateOutcome],
              name_bars: list[PriceBar]) -> None:
        if retain_run_id is None:
            return
        retained.append(CandidateRow(
            ticker=sec_ticker, run_id=retain_run_id, reference_date=reference_date,
            outcome=rollup(gates),
            gate_inputs=_gate_inputs(rec, name_bars, window_start=win_start), per_gate=gates,
            not_evaluated_reason=_first_unrun(gates),
            deciding_cap=_deciding_cap(caps, getattr(rec, "internal_id", None), universe_as_of)))

    for i, s in enumerate(universe, start=1):
        reporter.tick(i, suffix=f"{g1_survivors} enriched")
        bars = store.get_price_history(s.internal_id)
        rec = build_price_record(
            s, price_bars=bars, benchmark_bars=bench_bars,
            reference_date=reference_date, staleness_days=staleness_days,
        )
        # cheap price gates first — reject without any EDGAR call
        g1, g1_why = gate_g1_drawdown(rec, th)
        gates = {"g1_drawdown": GateOutcome(outcome=outcome_from_gate(g1), reason=g1_why)}
        if g1 is not GateResult.PASS:
            _keep(s.ticker, rec, gates, bars)
            continue
        g2, g2_why = gate_g2_idiosyncratic(rec, th)
        gates["g2_idiosyncratic"] = GateOutcome(outcome=outcome_from_gate(g2), reason=g2_why)
        # THE SECOND FORWARD POINT, and it read "not FAIL" — so a G2 that returned UNKNOWN sent the
        # name on to G3. Three names did exactly that on the 2026-07-29 run, reaching a stage only
        # 410 had passed. Under DROP the forward requires an actual PASS.
        if g2 is GateResult.FAIL or (policy is RoutingPolicy.DROP and g2 is not GateResult.PASS):
            _keep(s.ticker, rec, gates, bars)
            continue
        g1_survivors += 1
        full = enrich_with_fundamentals(
            rec, edgar=edgar, price_bars=bars, reference_date=reference_date
        )
        cand = evaluate_screen2(full, screen_run_at=run_at, thresholds=th,
                                policy=policy)
        if cand is not None:
            store.save_candidate(cand)
            candidates.append(cand)
        # THE GATE'S OWN RESULT, not the admission decision (2026-07-31). The row previously
        # recorded PASS whenever a candidate was produced — so a name G3 could not value was
        # written down as PASSED-G3, which is the silent pass one layer along from the gate's.
        # 186 of the 281 in the 2026-07-29 pool were never valued and every one read PASS.
        #
        # ADMISSION IS RECORDED SEPARATELY because routing is not decided here: the runner still
        # admits an unvalued name, and the row now says the gate did not evaluate it. Whoever
        # chooses the routing can count both from the same rows.
        g3, g3_why = gate_g3_multiple_floor(full, th)
        gates["g3_multiple_floor"] = GateOutcome(
            outcome=outcome_from_gate(g3), reason=g3_why)
        gates["admitted"] = GateOutcome(
            outcome=(Outcome.PASS if cand is not None else Outcome.FAIL),
            reason=("admitted to the candidate set" if cand is not None
                    else "rejected by the multiple floor or a distress signal"))
        _keep(s.ticker, full, gates, bars)

    written = 0
    if retain_run_id is not None and retain_dir is not None:
        written = append_rows(retained, run_id=retain_run_id, snapshots_dir=retain_dir)

    stats: dict[str, int | str | None] = {
        "universe": len(universe),
        "g1_g2_survivors": g1_survivors,
        "candidates": len(candidates),
        # WHAT WAS WRITTEN, not what was built — the stat a caller trusts must be the one the
        # writer returned, or it reports evidence that does not exist on disk.
        "retained_candidate_rows": written,
        # THE POLICY TRAVELS WITH THE COUNT. 331 and 49 are the same screen under different
        # routing, so a caller that reports `candidates` without it reports a number nobody can
        # interpret.
        "routing_policy": policy.value,
        "universe_as_of": universe_as_of.isoformat() if universe_as_of else None,
    }
    return candidates, stats


#: The G1/G2 price inputs. Windowed, so each also carries span_days + observations.
_PRICE_INPUTS = ("drawdown_from_high", "rel_ret_vs_market", "last")

#: THE G3 INPUTS — the valuation gate's, on `rec.fundamentals`. Recorded in G3'S OWN PREFERENCE
#: ORDER, and BOTH are recorded even though the gate decides on one: `gate_g3_multiple_floor`
#: tries EV/EBITDA and falls back to P/E, so a row carrying only the winner cannot say WHY that
#: one was used. Both present is what makes the fallback legible after the fact.
#:
#: WITHOUT THESE THE ROW SAID WHAT G3 DECIDED AND WHY, BUT NOT THE NUMBER IT DECIDED ON — so for
#: the valuation gate, retention could not do the one thing it exists for: falsify the screen.
#: G1 and G2 were falsifiable from their rows since the grain shipped; G3 was not.
_G3_INPUTS = ("ev_ebitda_pctile_vs_history", "pe_pctile_vs_history")


def _stamped(f: DataField[Any], *, default_source: str,
             span: tuple[int, int] | None = None) -> StampedInput:
    """ONE conversion from a `DataField` to a `StampedInput`, shared by every gate's inputs.

    The `as_of` is DROPPED when the value is absent and KEPT whenever it is present — never
    replaced by the run date. That is the whole point: `pe_pctile_vs_history` is stamped with the
    EPS PERIOD END (typically ~210d before the run, bounded at 470 by the reach-back guard), so a
    row stamping it "today" would claim a freshness the number does not have. The stale-benchmark
    incident was exactly this shape on a price field.

    TYPED, AND THE ATTRIBUTES ARE READ DIRECTLY — never `getattr(f, "value", None)`. Review of the
    first cut caught that: a defaulting getattr turns a renamed or mistyped attribute into a silent
    `None`, which here would write "the gate could not see this" onto EVERY row — a fabricated
    NOT_EVALUATED across the whole corpus, inside the rows that exist to BE the evidence. Fail
    loud. (The first cut used getattr only because the test fixtures were duck-typed: the test
    shape had driven the production signature, which is backwards. The fixtures are real
    `DataField`s now.)
    """
    return StampedInput(
        value=f.value, as_of=f.as_of if f.value is not None else None,
        source=f.source or default_source, note=f.note,
        span_days=span[0] if span else None, observations=span[1] if span else None)


def _gate_inputs(rec: object, bars: list[PriceBar], *, window_start: dict[str, date]
                 ) -> dict[str, StampedInput]:
    """The gate inputs with THEIR OWN stamps — never the run's.

    A gate input claiming the reference date while its data stopped days earlier is exactly what
    made the benchmark incident invisible, so the field's own ``as_of`` and ``note`` travel with it.

    Covers G1/G2 (price) AND G3 (valuation). An UNKNOWN input is still written — value None, no
    stamp, `note` carrying the cause — because "the gate could not see this" is the finding for
    282 of the 413 names that reached G3, not an absence to skip.
    """
    prices = getattr(rec, "prices", None)
    out: dict[str, StampedInput] = {}
    for name in _PRICE_INPUTS:
        f = getattr(prices, name, None)
        if f is None:
            continue
        start = window_start.get(name)
        win = (window_facts(bars, start=start, end=f.as_of)
               if start is not None and f.value is not None and f.as_of is not None else None)
        out[name] = _stamped(f, default_source="EOD", span=win)

    fundamentals = getattr(rec, "fundamentals", None)
    for name in _G3_INPUTS:
        f = getattr(fundamentals, name, None)
        if f is None:
            continue
        # No span/observations: the percentile's window (1825d) and its point count live in the
        # field's NOTE as prose, and the structured values do not reach here. Parsing them back
        # out would be the display-string re-parse this repo bans — left absent and said so,
        # rather than reconstructed.
        out[name] = _stamped(f, default_source="EDGAR")
    return out


def _deciding_cap(caps: dict[str, float], internal_id: str | None,
                  as_of: date | None) -> StampedInput | None:
    """The cap that admitted this name, stamped with the SNAPSHOT's date — never the run's.

    All 331 candidates of the `-03` pool carried `market_cap: null ("needs shares")` while the
    universe that admitted them was cap-banded on exactly that number. The input that decided the
    population was absent from the record of the decision. Absent when the run took the
    no-snapshot fallback: no snapshot, no cap that decided anything, and inventing one would be
    the fabrication this records against.
    """
    if internal_id is None or as_of is None:
        return None
    cap = caps.get(internal_id)
    if cap is None:
        return None
    return StampedInput(value=cap, as_of=as_of, source="Polygon close x EDGAR XBRL shares",
                        note="the universe snapshot's cap — what decided band membership")


def _first_unrun(gates: dict[str, GateOutcome]) -> str | None:
    """The reason a row reads NOT_EVALUATED — the first gate that could not be assessed."""
    for g, o in gates.items():
        if o.outcome is Outcome.NOT_EVALUATED:
            return f"{g}: {o.reason}"
    return None
