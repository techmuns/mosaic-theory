"""Orchestration for the two OPERATOR-TRIGGERED jobs (GitHub Actions `workflow_dispatch`).

No cron: both jobs move DECISION SURFACES — the weekly rebuilds the universe, re-screens
and re-ranks the queue; the monthly commits the report the BUY-AVOID spread is read from —
so the operator decides when they run (ruling 2026-08-24).

Each run is self-contained and idempotent: **rebuild** the working DB from the committed JSONL
snapshots, **refresh** EOD prices for the stored universe (the immutable per-day grouped-daily
responses are cached, so only new days hit the network), run the **screen** (weekly) or the
**scoring** (monthly), then **export** the snapshots back for the workflow to commit. Bulk prices
are not snapshotted (re-pullable + cached); the durable state is the entity master, universe,
candidates, ledger, and as-reported fundamentals.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

from vinci.cohort import cohort_reads, sic_by_ticker
from vinci.config import Config, get_config
from vinci.edgar import EdgarClient
from vinci.eod import PolygonEodClient, ingest_prices
from vinci.eod.dividends import default_dividends
from vinci.evidence import evidence_strip
from vinci.labels import resolve_label
from vinci.progress import ProgressFn
from vinci.rank import (
    CauseClass,
    RankedCandidate,
    RankWeights,
    StructuralDisqualifier,
    load_candidates_from_snapshot,
    load_market_caps_from_snapshot,
    rank_candidates,
    render_queue_markdown,
    scan_structural,
)
from vinci.scoring import score_ledger
from vinci.scoring.baseline import resolve_baskets
from vinci.screens import screen_universe
from vinci.screens.annotations import ScreenAnnotation
from vinci.screens.annotations import for_screen_date as annotations_for_screen_date
from vinci.screens.retention import (
    BandConfig,
    RunManifest,
    ScreenConfig,
    next_run_id,
    write_manifest,
)
from vinci.screens.screen2 import Screen2Thresholds
from vinci.sec import build_sec_http
from vinci.store import Store
from vinci.universe import (
    BUILD_UNIVERSE_SEED_TABLES,
    DROP_STAGES,
    benchmark_identity,
    build_universe,
)

# ~5y: enough history for the 52w drawdown AND the G3 multiple-at-floor range (Polygon Starter).
_SCREEN_LOOKBACK_DAYS = 1825
# Monthly scoring refreshes ~2y so verdicts in that window have forward prices to score against.
_SCORE_LOOKBACK_DAYS = 730
# Queue-writing defaults, shared by the weekly job and the `vinci rank` CLI so the two cannot drift.
QUEUE_MD_TOP = 50
QUEUE_ADV_FLOOR = 3_000_000.0  # = the universe ADV floor; mirrors vinci.rank's own default


def rank_from_snapshots(
    cfg: Config,
    *,
    annotations: dict[str, CauseClass] | None = None,
    structural_flags: dict[str, StructuralDisqualifier] | None = None,
    deep_work_adv_floor: float = QUEUE_ADV_FLOOR,
) -> list[RankedCandidate]:
    """Rank the committed screen output, with the resolved sector/industry labels attached.

    THE ONE RANKING PATH — `vinci rank` and the weekly job both come through here, so a queue built
    by CI is the same object as one built by hand. Reads the committed snapshots only (no DB, no
    network): ``candidate_records.jsonl`` for the screen output, ``universe_snapshot.jsonl`` for
    size. Returns [] when the screen produced nothing, so a caller can skip the write.
    """
    snaps = cfg.snapshots_dir
    records = snaps / "candidate_records.jsonl"
    # ABSENT is a legitimate state (a fresh checkout, or the very first run) and means "nothing has
    # been screened", not "invent something" — so it returns empty and the caller skips the write,
    # leaving any existing queue untouched. Only the missing FILE is tolerated; a malformed one
    # still raises. run_weekly reports `ranked` in its result dict, so a screen that found
    # candidates while the rank found none is visible in the job output rather than silent.
    if not records.exists():
        return []
    cands = load_candidates_from_snapshot(records)
    if not cands:
        return []
    ranked = rank_candidates(
        cands,
        weights=RankWeights(),
        annotations=annotations,
        market_caps=load_market_caps_from_snapshot(snaps / "universe_snapshot.jsonl"),
        structural_flags=structural_flags or None,
        deep_work_adv_floor=deep_work_adv_floor,
    )
    # The RESOLVED labels are attached HERE, in the writer, never in the scorer — vinci.rank and
    # vinci.screens stay label-free and an AST fence test asserts it. Assemble/inform ONLY: they
    # feed the human cluster roll-up, never a gate/weight/sort. gics=None at universe scale: the
    # CIQ-GICS overlay joins at the frontend build from the committed dossier index, so a dossier
    # landing between rank runs upgrades its name without a re-rank.
    sic_by_id = {c.candidate_id: c.data_record.identity.sic for c in cands}
    # THE COHORT SPLIT is derived HERE, in the writer, for the same reason the labels are: it is
    # sector-derived, and the scorer must never be able to reach it. Ranking is finished by this
    # line. The medians are taken over the SCREEN LOG — every name that reached the gates, pass and
    # fail — never over the admitted candidates, which would define the cohort by the very
    # selection under test and guarantee a deeply-negative median. Reads committed artifacts only.
    queue_tickers = [c.data_record.identity.ticker for c in cands]
    # INFORM-ONLY MUST NOT BE ABLE TO STOP THE QUEUE (review, #503). This ran unguarded, so a
    # missing or truncated `securities.jsonl` raised out of the writer and NO QUEUE WAS WRITTEN AT
    # ALL — a display column taking down the decision surface it decorates. The failure is reported
    # loudly and the rank proceeds with every row reading "no cohort", which is the honest state
    # and exactly what the cell renders when a name has none.
    #
    # AND IT IS MEASURED OVER THE RUN THE CANDIDATES CAME FROM, not the newest on disk. Both
    # artifacts are read here and nothing asserted they were the same vintage — so a re-rank
    # against a stale candidate file, or a screen landing between these two steps, would subtract a
    # median measured over one window from returns measured over another. Silent, because each
    # number looks fine on its own. `run_for_stamp` raises when the stamp names no run, and the
    # guard below turns that into "no cohort" rather than a lost queue.
    #
    # AND THE STAMP IS THE CANDIDATES', PLURAL — not row zero's. Taking `cands[0]` asserts by
    # accident that the file is single-vintage: a `candidate_records.jsonl` carrying rows from two
    # runs (an export interrupted mid-rewrite, or a hand-merged file) would bind the cohort to
    # whichever run happens to sit first in the file while the queue is ranked over both. That is
    # the same silent mixed-vintage read this guard exists to close, one level up, so it is refused
    # rather than resolved — inside the guard, so it degrades to "no cohort", never a lost queue.
    candidate_screen_run_at = sorted({str(c.screen_run_at)[:10] for c in cands})
    try:
        if len(candidate_screen_run_at) != 1:
            raise ValueError(
                f"candidate_records.jsonl carries {len(candidate_screen_run_at)} screen stamps "
                f"({', '.join(candidate_screen_run_at)}) — there is no single run the cohort could "
                f"be measured over, so it is not measured at all"
            )
        cohorts = cohort_reads(snaps, sic_by_ticker(snaps), tickers=queue_tickers,
                               run_stamp=candidate_screen_run_at[0])
    except (ValueError, OSError) as exc:
        print(f"WARNING: cohort split unavailable, ranking without it — {exc}", file=sys.stderr)
        cohorts = {}
    # The EVIDENCE STRIP is composed HERE, in the writer, for the same reason the labels are: it is
    # presented context, and the scorer must never be able to read it. Ranking is already finished
    # by this line, so the strip cannot influence an order it is attached to.
    rec_by_id = {c.candidate_id: c.data_record for c in cands}
    return [
        r.model_copy(update={
            "sector": (lbl := resolve_label(sic_by_id.get(r.candidate_id))).sector,
            "industry": lbl.industry,
            "context": (evidence_strip(rec) if (rec := rec_by_id.get(r.candidate_id)) else None),
            "cohort": cohorts.get(r.ticker),
        })
        for r in ranked
    ]


def carry_forward_assessment(
    cfg: Config,
) -> tuple[dict[str, StructuralDisqualifier], dict[str, CauseClass]]:
    """The last EXPLICIT operator assessment, recovered from the queue about to be replaced.

    `vinci rank --structural` / `--cause-file` write `structural_flag` and `cause_class` into
    `ranked_queue.jsonl` ONLY — nothing durable upstream holds them. A scheduled refresh that
    supplied neither would therefore wipe them, and **a name capped at 0.05 by an 8-K disqualifier
    would climb back to the top of the queue on Monday with no operator action** (review, #420).

    Carrying them is safe in the one direction that matters: the structural channel is DEMOTE-ONLY,
    so a stale flag can only keep a name down, never lift one. An 8-K does not un-happen, so the
    flag stays factually true; it is `source_ref`-bound to its accession either way. What this does
    NOT do is DISCOVER new signals — that still needs an explicit `--structural` run. And it
    self-clears: if an operator re-scans and the signal no longer fires, the queue they write has no
    flag, and the next carry-forward reads that absence.

    Keyed by ticker, which is what `rank_candidates` falls back to and what survives a re-screen.
    """
    prior = cfg.snapshots_dir / "ranked_queue.jsonl"
    flags: dict[str, StructuralDisqualifier] = {}
    causes: dict[str, CauseClass] = {}
    if not prior.exists():
        return flags, causes
    for line in prior.read_text().splitlines():
        if not line.strip():
            continue
        r = RankedCandidate.model_validate_json(line)
        if r.structural_flag is not None:
            flags[r.ticker] = r.structural_flag
        if r.cause_class != CauseClass.UNCLASSIFIED:
            causes[r.ticker] = r.cause_class
    return flags, causes


def write_queue_snapshots(
    cfg: Config, ranked: list[RankedCandidate], *, md_top: int = QUEUE_MD_TOP
) -> tuple[Path, Path]:
    """Write ranked_queue.jsonl + .md. Returns both paths so a caller can report what it wrote."""
    cfg.ensure_dirs()
    snaps = cfg.snapshots_dir
    # BOTH FILES ARE COMPOSED BEFORE EITHER IS WRITTEN: a malformed annotation file raises here,
    # before the JSONL is replaced, so the committed pair can never disagree.
    md_text = render_queue_markdown(ranked, top=md_top,
                                    annotations=queue_annotations(snaps, ranked))
    jsonl = snaps / "ranked_queue.jsonl"
    with jsonl.open("w") as f:
        for r in ranked:
            f.write(r.model_dump_json() + "\n")
    md = snaps / "ranked_queue.md"
    md.write_text(md_text)
    return jsonl, md


def queue_annotations(snapshots_dir: Path, ranked: list[RankedCandidate]
                      ) -> dict[str, ScreenAnnotation]:
    """The annotations on the screen run(s) this queue came from, keyed by CANDIDATE id. A row is
    matched on its OWN screen date, and keyed by its own candidate, so a later run of the same
    ticker in a mixed-vintage queue is never marked (Codex review of #799)."""
    out: dict[str, ScreenAnnotation] = {}
    for day in sorted({r.screen_run_at.date() for r in ranked}):
        on_day = annotations_for_screen_date(snapshots_dir, day)
        out |= {r.candidate_id: on_day[r.ticker] for r in ranked
                if r.screen_run_at.date() == day and r.ticker in on_day}
    return out


def refresh_queue(cfg: Config, *, structural: bool = False) -> dict[str, int]:
    """Rank the screen's committed output and REPLACE the queue. The weekly job's tail.

    Extracted from :func:`run_weekly` so its dangerous cases are testable without the network —
    they were review findings on #420, and none is reachable through a function that builds
    Polygon and EDGAR clients from config.

    ``structural=True`` runs the deterministic 8-K disqualifier scan (network). A LIVE SCAN IS
    AUTHORITATIVE AND REPLACES THE CARRY-FORWARD outright — it re-checks all five signals against
    current filings, so a name that no longer fires must come back clean rather than have a stale
    flag resurrected underneath it. The carry-forward exists for the runs that DON'T scan.
    """
    flags, causes = carry_forward_assessment(cfg)
    scanned = 0
    if structural:
        records = cfg.snapshots_dir / "candidate_records.jsonl"
        cands = load_candidates_from_snapshot(records) if records.exists() else []
        if cands:
            scan = scan_structural(
                cands, edgar=EdgarClient.from_config(cfg), http=build_sec_http(cfg)
            )
            scanned = len(scan.covered)
            # REPLACE ONLY WHERE THE SCAN ACTUALLY LOOKED. `scan_structural` fails soft per name, so
            # a transient EDGAR outage yields no flag for that name — indistinguishable from a clean
            # result unless coverage is consulted. A blanket replacement would therefore let one bad
            # response erase a real 8-K disqualifier and lift the name back above its 0.05 cap: the
            # #420 failure, reintroduced by the fix for it (review, #431). Prior flags survive for
            # every name the scan did not cover; covered names take the scan's verdict, flag or
            # no flag.
            by_id = {c.data_record.identity.internal_id: c.data_record.identity.ticker
                     for c in cands}
            covered_tickers = {by_id[i] for i in scan.covered if i in by_id}
            flags = {t: f for t, f in flags.items() if t not in covered_tickers}
            for iid, flag in scan.flags.items():
                flags[by_id.get(iid, iid)] = flag
    ranked = rank_from_snapshots(cfg, annotations=causes or None, structural_flags=flags or None)
    # WRITE EVEN WHEN EMPTY. The screen has completed by this point, so no candidates is an ANSWER —
    # the latest screen rejected everything — not a failure to produce one. Skipping the write left
    # the previous week's names served as current, and the staleness banner could not catch it
    # either: the retained queue is only seven days old, so it reads as fresh (review, #420).
    #
    # The two cases are told apart on the INPUT, never on the output being empty: a MISSING
    # candidate_records.jsonl means nothing has been screened (fresh checkout) and must not clobber
    # an existing queue; a PRESENT-but-empty one is a real screen result and must replace it.
    if (cfg.snapshots_dir / "candidate_records.jsonl").exists():
        write_queue_snapshots(cfg, ranked)
    return {"ranked": len(ranked), "structural_scanned": scanned,
            "structural_flagged": sum(1 for r in ranked if r.structurally_disqualified),
            "carried_structural": len(flags), "carried_cause": len(causes)}


def run_weekly(
    config: Config | None = None,
    *,
    end: date,
    benchmark: str = "IWM",
    lookback_days: int = _SCREEN_LOOKBACK_DAYS,
    progress: ProgressFn | None = None,
) -> dict[str, object]:
    """Weekly: rebuild the universe, screen it, rank the result, and export the lot.

    ONE CALL IS THE WHOLE WEEK, and every stage below is UNCONDITIONAL. A scheduled job with
    opt-in pieces is one that can be run with parts switched off and emit a queue that looks
    complete — which is exactly how two stages came to be silently missing for months: nothing
    ranked (the served queue froze 12 days behind its own screen) and nothing scanned for
    structural disqualifiers (0 flags across 284 names). Flags on a cron are how that happens, so
    there are none here.
    """
    cfg = config or get_config()
    cfg.ensure_dirs()
    # 1. UNIVERSE — the screen's INPUT, and the artifact that decides which names are eligible to
    #    be screened AT ALL (cap band, ADV floor, operating-co gates). Nothing rebuilt it on a
    #    schedule until 2026-08-12: the committed snapshot was stamped 2026-07-29 while the screen
    #    consuming it ran 2026-08-12, so a name that fell into the band in between was never
    #    screened and one that left it still was. It writes its own snapshots and closes its own
    #    Store, so the rebuild below reads the universe this just produced.
    # RETENTION IS ON, AND ONE RUN ID SPANS BOTH GRAINS. `build_universe` and `screen_universe`
    # each accept `retain_run_id`/`retain_dir` and NO production path supplied them, so the whole
    # retention layer — universe rows, candidate rows, and the write-once manifest — was dark:
    # `write_manifest` had no caller outside its own tests, and `_fleet_reference_date` (which reads
    # `screen_runs/*.manifest.json`) therefore sat frozen on whatever manifest last reached the repo
    # by hand while `ranked_queue`'s `screen_run_at` moved on. That divergence split the fleet
    # across two as-ofs on 2026-08-12.
    #
    # THE RUN IS THE WEEK, NOT THE SUBCOMMAND. Wiring this into `vinci screen` would file a run_id
    # carrying candidate rows and no universe rows — and the manifest's own `universe_as_of` field
    # exists because run `2026-07-29-01` screened the 2026-07-06 universe while `build_universe`
    # wrote the 2026-07-29 one, leaving 72 tickers in both grains. That field's docstring names the
    # cause exactly: "nothing binds that to a `build_universe` run in the same session (the build is
    # a separate CLI subcommand)". This function IS that session, so the binding belongs here.
    # NO FUTURE IDENTITIES IN A BACKDATED RUN (review finding, #442). The store is mutable and
    # SHARED, so a forward-dated attempt that died mid-flight leaves its upserts behind: a
    # `--end 2026-08-13` abort left BBAR/SSMR/AADX at `first_seen 2026-08-13`, and the re-run at
    # `--end 2026-08-12` admitted all three to the 2026-08-12 universe and filed them under that
    # run's manifest. RAISE rather than filter: silently dropping them would make the leak
    # invisible and the operator would never learn the store needs rolling back.
    # NO FUTURE IDENTITIES IN A BACKDATED RUN — AND THE CHECK NEEDS DATA TO INSPECT.
    # TWO CONSTRAINTS, BOTH REAL, AND THE FIRST FIX SATISFIED ONLY ONE (review, #494).
    #   * it must run BEFORE `build_universe`, or the leaked identities are already in the
    #     universe snapshot and filed under this run's id (`test_a_backdated_run_refuses_
    #     identities_the_store_learned_later` pins exactly that, and caught the wrong fix);
    #   * it must run AFTER the entity master is loaded, or on a fresh checkout — every CI run,
    #     where `data/vinci.db` is git-ignored — it inspects an EMPTY store, sees nothing, and
    #     `build_universe`'s own seed then loads the very identities it exists to refuse.
    # So the seed moves HERE, ahead of both. It is the same idempotent subset load
    # `build_universe` performs, so doing it twice costs a re-read and changes nothing.
    with Store(cfg.db_path) as _s:
        _s.rebuild_from_snapshots(cfg.snapshots_dir, tables=BUILD_UNIVERSE_SEED_TABLES)
        ahead = _s.identities_first_seen_after(end)
    if ahead:
        # TWO CAUSES, TWO REMEDIES (review, 2026-08-31). The guard now also returns identities
        # whose `first_seen` is UNRECORDED, and for those the original wording was simply wrong:
        # nothing later-dated wrote them, and rolling them back fixes nothing. Naming only the
        # first cause sends an operator to undo work that is not the problem.
        raise RuntimeError(
            f"{len(ahead)} identities in the store are not known to predate {end} "
            f"({', '.join(ahead[:5])}{'…' if len(ahead) > 5 else ''}) — a run claiming {end} must "
            f"not judge names it could not have known. Either a LATER-DATED run wrote them (roll "
            f"those identities back before re-running at this date), or their `first_seen` is "
            f"UNRECORDED, which cannot confirm they predate {end} and so fails closed — stamp it "
            f"from evidence (`vinci refresh` has stamped since 2026-08-31; older rows may not)."
        )
    run_id = next_run_id(end, cfg.snapshots_dir)
    universe = build_universe(cfg, reference_date=end,
                              retain_run_id=run_id, retain_dir=cfg.snapshots_dir)
    eod = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
        # THE GUARD READS THE UNIVERSE, NOT THE ENTITY MASTER (review finding, #494). It always
        # MEANT to — its message says "universe rebuilt EMPTY" — but it asked
        # `iter_securities()`, which is the accumulate-only master and answers a different
        # question. That was survivable only by accident: on CI's empty store a zero-admit run
        # died earlier, at the ROW-DROP the seed now fixes. Removing that accidental failure
        # exposed the real one — seeded, the master is never empty, so the guard could no longer
        # fire and a zero-admit run would export a BLANK `universe_snapshot`, pass here, and reach
        # `screen_universe`, whose own `if ids:` falls back to screening the ENTIRE master with
        # `caps = {}` (screens/run.py). A fix for one failure must not delete the alarm for
        # another.
        if not store.latest_universe(end):
            # RAISE, never return. build_universe has ALREADY cleared and exported
            # universe_snapshot.jsonl, so a soft return would exit 0, and the workflow's next step
            # commits data/snapshots — publishing a blank universe beside the previous candidates
            # and queue while reporting a clean run. A transient resolver/price/shares outage must
            # fail the job before that commit (review, #431).
            raise RuntimeError(
                f"universe rebuilt EMPTY at {end} ({universe}) — refusing to continue: the "
                "snapshot has already been cleared and exported, so proceeding would commit a "
                "blank universe over a good one"
            )
        # THE MANIFEST IS A PRE-COMMITMENT, WRITTEN BEFORE THE SCREEN READS IT BACK.
        # `screen_universe` refuses a run whose `routing_policy` disagrees with its own record, so
        # this cannot be an after-the-fact log. It is written HERE — after the universe exists, so
        # `universe_as_of` names the population the gates will actually judge rather than a guess.
        write_manifest(
            RunManifest(
                run_id=run_id, reference_date=end,
                screen=ScreenConfig(
                    thresholds=Screen2Thresholds().model_dump(),
                    benchmark=benchmark, lookback_days=lookback_days),
                band=BandConfig(
                    market_cap_min_usd=cfg.universe.market_cap_min_usd,
                    market_cap_max_usd=cfg.universe.market_cap_max_usd,
                    exchanges=tuple(cfg.universe.exchanges)),
                universe_as_of=store.latest_universe_as_of(end),
                stages=DROP_STAGES,
            ),
            snapshots_dir=cfg.snapshots_dir,
        )
        _cands, stats = screen_universe(
            store, eod, edgar, reference_date=end, lookback_days=lookback_days,
            staleness_days=cfg.price_staleness_days, benchmark=benchmark, progress=progress,
            retain_run_id=run_id, retain_dir=cfg.snapshots_dir,
        )
        store.export_snapshots(cfg.snapshots_dir)
    # 3. RANK + the structural scan, from the snapshot the screen just exported, through the same
    #    path `vinci rank` uses. Until 2026-08-12 this job stopped at the screen, so the served
    #    queue drifted 12 days and 95 names behind the screen that fed it; and the scan ran only
    #    when a human typed the flag, which nobody had — 0 disqualifiers across 284 names.
    #    `structural=True` is HARD-WIRED: it is a demote-only, source-bound channel, and making it
    #    optional on the scheduled path is what let it go dormant in the first place.
    return {**stats, "ref": end.isoformat(), "universe": universe,
            **refresh_queue(cfg, structural=True)}


def run_monthly(
    config: Config | None = None,
    *,
    as_of: date,
    benchmark: str = "IWM",
    cost_bps: float = 25.0,
    lookback_days: int = _SCORE_LOOKBACK_DAYS,
    progress: ProgressFn | None = None,
) -> dict[str, object]:
    """Monthly: refresh prices, score the decision ledger, and write the report to snapshots.

    Prices are not snapshotted (re-pullable), so we refresh them before scoring — else a fresh CI
    checkout would have no forward prices to score against. The grouped-daily cache keeps this fast.
    """
    cfg = config or get_config()
    cfg.ensure_dirs()
    client = PolygonEodClient.from_config(cfg)
    bench = benchmark_identity(benchmark)
    start = as_of - timedelta(days=lookback_days)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
        universe = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
        if universe:
            ingest_prices(client, store, universe, start=start, end=as_of, progress=progress)
            store.upsert_security(bench)
            ingest_prices(client, store, [bench], start=start, end=as_of)
        _scores, report = score_ledger(
            store, as_of=as_of, cost_bps=cost_bps, benchmark_internal_id=f"IDX-{benchmark}",
            # Wired here as well as in `vinci score` — see that call site's note.
            # `scoring_report.md` is the artifact most readers open, so a kill test missing
            # from it is missing.
            baskets=resolve_baskets(cfg.data_dir / "followed.json", store.iter_securities()),
            # TOTAL RETURN (operator ruling 2026-10-26): Tiingo's dividends over the ledger's
            # whole span. Without TIINGO_API_KEY every window reads unknown, so a RESOLVED row
            # stops this run rather than scoring on price return (the CI secret is an operator
            # item — docs/records/2026-10-26-split-restatement-and-total-return.md).
            dividends=default_dividends(
                start=min((e.entry_price_as_of for e in store.iter_ledger()), default=as_of),
                end=as_of),
        )
        store.export_snapshots(cfg.snapshots_dir)
    (cfg.snapshots_dir / "scoring_report.md").write_text(report.to_markdown())
    return report.to_dict()
