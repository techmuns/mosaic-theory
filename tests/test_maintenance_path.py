"""A name the fund maintains stays re-assemblable after it leaves the screen band.

WHY. The cap band is an ENTRY rule — it answers where the fund HUNTS. Membership was doubling as
the maintenance key, so a dossier could not be refreshed once its name left the band. IT is the
first instance and it is the benign one: it PASSED all three gates on 2026-07-29 and then
appreciated past the $10bn ceiling ($135.11 → $165.65, implied cap $11.19bn). The instance that
matters is the one behind it — **any held position that re-rates upward becomes un-maintainable**,
so the defect bites a WINNER first.

THE FIX IS NOT A FABRICATED ROW. `CandidateRecord` means "screen-admitted"; forging one would put
an invented screen verdict under a name about to be underwritten. The maintenance route builds a
`DataRecord` instead — via `build_data_record`, the same constructor the screen's own path composes
— and carries `record=None`, so nothing anywhere can mistake it for a screen admission.

GROWN OUT AND FAILED MUST NEVER RENDER ALIKE. That is `unstated`-versus-`disagrees` again, with a
position on the other side of it, so the caveat reports the LAST REAL VERDICT and its gates rather
than the bare fact of absence.
"""
from __future__ import annotations

import functools
import json
import pathlib
import tempfile
from collections.abc import Iterator
from datetime import date as dt_date

import pytest

import vinci.dossier.assemble as asm
from tests.sec_offline_support import no_network, seed_sec_cache
from vinci.config import Config

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRICE_FIXTURES = ROOT / "tests" / "fixtures" / "prices"

#: Everything under `data/` these pins legitimately read. Symlinked rather than copied so they run
#: against the REAL committed artifacts; only the store and the SEC cache are substituted. The cache
#: is seeded from committed fixtures (`tests/sec_offline_support.py`): the real `data/cache` is
#: git-ignored, so on a fresh checkout the resolver fetched `company_tickers.json` live inside
#: `-m "not network"`, and 8 pins failed with the network refused (2026-10-23).
_LINKED = ("dossiers", "snapshots", "manual", "monitor", "followed.json", "graph_coverage.json")


@pytest.fixture(autouse=True)
def _offline() -> Iterator[None]:
    """Every pin runs with outbound connections refused: a fixture gap fails, never fetches."""
    with no_network():
        yield


@functools.lru_cache(maxsize=1)
def _cfg() -> Config:
    """A Config whose STORE is the committed price fixture and whose every other path is the real
    repo.

    WHY NOT `get_config()`, WHICH THIS USED TO BE. `data/vinci.db` is git-ignored and bulk prices
    are deliberately never snapshotted, so on any fresh checkout — every CI run — the store is
    EMPTY and `_standalone_record` raises "no price history" for every maintained name. These six
    pins therefore passed on a developer's laptop and could not pass in CI: main ran RED for eleven
    consecutive merges on exactly this (2026-08-06 `017b155` onward), and the failure said nothing
    about the code it was supposedly guarding.

    THE FIX IS THE ONE D17 ALREADY ESTABLISHED — commit the small slice the pins actually read
    (`scripts/build_price_fixture.py`, mirroring `build_companfacts_fixture.py`) so the DB
    dependency disappears. Prices are the ONLY thing substituted; dossiers, snapshots and the
    resolver cache are symlinked, so these pins still read the real committed corpus.

    THE STORE IS ALWAYS THE FIXTURE, on every machine. Falling back to a populated local DB when
    one exists would make the pins mean something different on a laptop than in CI — which is the
    property that let this defect live for eleven merges without anyone's local run noticing.
    """
    from vinci.schemas.market import PriceBar
    from vinci.store import Store

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="vinci-maintenance-"))
    for name in _LINKED:
        src = ROOT / "data" / name
        if src.exists():
            (tmp / name).symlink_to(src)
    cfg = Config(data_dir=tmp)
    seed_sec_cache(cfg)
    with Store(cfg.db_path) as store:
        for f in sorted(PRICE_FIXTURES.glob("*.jsonl")):
            store.write_prices([
                PriceBar(**json.loads(line))
                for line in f.read_text().splitlines() if line.strip()
            ])
    return cfg


def _maintained_names() -> list[str]:
    """Committed dossiers that are NOT current screen candidates — the maintenance-route set."""
    cands = _candidate_tickers()
    return [p.parent.name for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
            if p.parent.name not in cands]


def test_every_maintained_name_has_committed_price_bars() -> None:
    """THE FIXTURE TRACKS THE FLEET, and says so loudly when it stops.

    A maintained name with no committed bars cannot be re-assembled in CI, and the failure it
    produces ("no price history in the store") points at the store rather than at the missing
    fixture — which is exactly how the eleven-merge red streak read. This pin names the remedy.
    """
    missing = [t for t in _maintained_names()
               if not (PRICE_FIXTURES / f"{t}.jsonl").is_file()]
    assert not missing, (
        f"{missing} take the maintenance route but have no committed price bars, so they cannot be "
        f"re-assembled on a checkout with no local DB. Run "
        f"`python scripts/build_price_fixture.py` — in the SAME PR that makes the name maintained, "
        f"so the fixture cannot drift from the fleet it serves.")


def _candidate_tickers() -> set[str]:
    from vinci.rank import load_candidates_from_snapshot
    snaps = _cfg().snapshots_dir
    return {c.data_record.identity.ticker
            for c in load_candidates_from_snapshot(snaps / "candidate_records.jsonl")}


def _a_maintained_orphan() -> str:
    """A committed-dossier name that is NOT a current candidate — the case under test."""
    cands = _candidate_tickers()
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        if p.parent.name not in cands:
            return p.parent.name
    pytest.skip(
        "vacuous: every committed dossier is also a current screen candidate, so the maintenance "
        "route has no live case to exercise. It begins covering names as soon as one leaves the "
        "band — which is the condition it exists for, not a reason to weaken the pin.")


def test_a_maintained_name_assembles_without_a_candidate_record() -> None:
    """THE POSITIVE CASE. `load_finalists` returns a Finalist whose facts came from the store, and
    `record` is None — no `CandidateRecord` was invented to get there."""
    t = _a_maintained_orphan()
    fin = asm.load_finalists(_cfg(), ticker=t)[0]

    assert fin.record is None, (
        f"{t} routed through the maintenance path but still carries a CandidateRecord — that type "
        "asserts screen admission, and this name has none")
    assert fin.standalone is not None
    assert fin.data_record.identity.ticker == t
    # the facts assembly actually consumes must be PRESENT, not a hollow shell
    assert fin.data_record.prices.last.value, "no last price — the record would assemble to nothing"
    assert fin.data_record.prices.adv_90d_shares.value, "no 90d ADV — the liquidity denominator"


def test_the_cohort_path_maintains_the_same_names_as_the_ticker_path() -> None:
    """BOTH CALLERS, not one. The first cut taught only the `--ticker` branch, so `--ticker IT`
    assembled while `--top 20` silently dropped IT at rank 5 — the exact name the path exists for.
    That asymmetry is worse than the symmetric failure it replaced, because a cohort run would have
    reported success while omitting the name.

    Asserted through `load_finalists` itself: a maintained orphan inside the queue's top-N must
    appear in the cohort result, not merely be reachable one at a time."""
    cfg = _cfg()
    t = _a_maintained_orphan()
    queue = [json.loads(x) for x in
             (cfg.snapshots_dir / "ranked_queue.jsonl").read_text().splitlines() if x.strip()]
    queue.sort(key=lambda r: int(r.get("rank", 1_000_000)))
    tickers = [r.get("ticker") for r in queue]
    if t not in tickers:
        pytest.skip(f"{t} has no ranked-queue row, so the cohort loop never reaches it")
    depth = tickers.index(t) + 1

    got = {f.data_record.identity.ticker for f in asm.load_finalists(cfg, top=depth)}
    assert t in got, (
        f"{t} sits at queue position {depth} and is maintained, but the cohort path omitted it — "
        "`--ticker` and `--top` disagree about which names the fund can still assemble")
    fin = next(f for f in asm.load_finalists(cfg, top=depth)
               if f.data_record.identity.ticker == t)
    assert fin.record is None and fin.screen_status, (
        "the cohort path produced a Finalist without the maintenance caveat — the name would "
        "assemble with nothing on the page saying it is outside the candidate set")


def test_the_wall_clock_is_unreachable_from_the_reference_date() -> None:
    """A DATE STAMPED ON AN ARTIFACT MUST NAME A MOMENT THE DATA REACHES.

    `_ref_of` used to fall back to `date.today()`. Harmless while every name had a queue row —
    and a live defect the moment one does not, which is exactly the state the maintenance path
    creates. It fails three ways at once: the artifact becomes IRREPRODUCIBLE (identical inputs,
    a different dossier tomorrow — the property temperature-0 protects, broken with no test that
    would notice); every relative-return window the page quotes moves silently; and the stamp can
    land BEYOND the store frontier and still pass a 5-day staleness check, because that check
    compares against the same clock.

    Asserted on the SOURCE as well as the behaviour: the behaviour test alone would pass on any
    day the fleet as-of happened to equal today."""
    import datetime as dt
    import inspect

    src = inspect.getsource(asm)
    # AST, not text: a `date.today()` inside a docstring explaining why it is forbidden must not
    # trip the guard that forbids it. This scans CALLS — the executable shape, not the prose.
    import ast
    clock = [f"{n.lineno}: {ast.unparse(n)}" for n in ast.walk(ast.parse(src))
             if isinstance(n, ast.Call) and ast.unparse(n.func).endswith(
                 ("date.today", "datetime.today", "datetime.utcnow"))]
    assert not clock, (
        f"assemble.py still reaches the wall clock for a date: {clock}. A stamp must name a moment "
        "the data reaches, never the moment the build ran. (`datetime.now(UTC)` for `built_at` is "
        "a BUILD INSTANT and is deliberately not matched here — it records when, not as-of what.)")
    assert "_ref_of(row or {}, fallback=" in src, "the fallback is not stated at the call site"

    cfg = _cfg()
    fleet = asm._fleet_reference_date(cfg)
    assert isinstance(fleet, dt.date)
    # it must name a REAL moment — the newest screen run, or the store's last bar
    manifests = sorted((cfg.snapshots_dir / "screen_runs").glob("*.manifest.json"), reverse=True)
    stamped = {dt.date.fromisoformat(str(json.loads(p.read_text())["reference_date"])[:10])
               for p in manifests}
    from vinci.store import Store
    with Store(cfg.db_path) as store:
        frontier = store.price_frontier()
    assert fleet in stamped or fleet == frontier, (
        f"the fleet as-of {fleet} is neither a screen run's reference_date {sorted(stamped)} nor "
        f"the store frontier {frontier} — it names no moment the data reaches")
    # and it must never outrun the data, which is what the wall clock did
    assert frontier is None or fleet <= frontier, (
        f"the fleet as-of {fleet} is AFTER the store's last bar {frontier}; a 5-day staleness "
        "window would still call that fresh, which is how the wall-clock bug hid")


def test_a_row_without_a_screen_run_takes_the_fleet_date_not_the_clock() -> None:
    """THE UNIT, with the row absent — the case the maintenance path creates and the only case the
    old fallback ever fired on."""
    import datetime as dt

    fleet = asm._fleet_reference_date(_cfg())
    assert asm._ref_of({}, fallback=lambda: fleet) == fleet
    assert asm._ref_of({}, fallback=lambda: fleet) != dt.date.today() or fleet == dt.date.today()
    # a row that HAS a screen run still wins — the fallback must not override real provenance
    assert asm._ref_of({"screen_run_at": "2026-07-06T00:00:00"},
                       fallback=lambda: fleet) == dt.date(2026, 7, 6)


def test_the_fallback_is_not_computed_when_it_is_not_used() -> None:
    """LAZY, and the reason is correctness before cost.

    The first cut passed the fallback by VALUE, so Python evaluated it on every row: measured at
    275 calls for 0 uses, because every queue row carries a `screen_run_at`. The wasted work was
    the smaller half — `_fleet_reference_date` RAISES on a store with no manifest and no bars, so
    an eager argument made that raise reachable from rows that never needed the fallback. A
    fallback's failure mode must not be able to break the path that does not take it.

    Pinned by making the fallback EXPLODE: if it is evaluated when a row has a screen_run_at, this
    test fails with that explosion rather than a subtle count mismatch."""
    def boom() -> object:
        raise AssertionError(
            "the fallback was evaluated for a row that carries its own screen_run_at — it is being "
            "passed by value, so a raising fallback can break rows that never use it")

    assert asm._ref_of({"screen_run_at": "2026-07-06T00:00:00"},
                       fallback=boom) == dt_date(2026, 7, 6)   # type: ignore[arg-type]

    # …and a real end-to-end count over the whole queue, so this cannot pass on a one-row fluke
    calls = 0
    real = asm._fleet_reference_date

    def counted(cfg: object) -> object:
        nonlocal calls
        calls += 1
        return real(cfg)                                        # type: ignore[arg-type]

    asm._fleet_reference_date = counted                         # type: ignore[assignment]
    try:
        fins = asm.load_finalists(_cfg(), top=None)
    finally:
        asm._fleet_reference_date = real                        # type: ignore[assignment]
    maintained = sum(1 for f in fins if f.record is None)
    assert calls <= maintained, (
        f"_fleet_reference_date ran {calls} times for {maintained} name(s) that could need it — "
        "the fallback is being computed for rows that already carry a screen_run_at")


def test_an_unmaintained_name_is_still_refused() -> None:
    """THE NEGATIVE. The path opens for names the fund already carries — NOT for anything absent
    from the candidate set. Without this the guard is 'assemble whatever you are asked for', which
    is the screen's whole purpose deleted."""
    cands = _candidate_tickers()
    ghost = next(t for t in ("ZZZZ", "QQQQ", "XXXX")
                 if t not in cands and not (ROOT / "data" / "dossiers" / t).exists())
    with pytest.raises(LookupError, match="not maintained"):
        asm.load_finalists(_cfg(), ticker=ghost)


def test_the_caveat_reports_the_last_real_verdict_not_the_bare_absence() -> None:
    """GROWN OUT != FAILED. The caveat must carry the last run that actually EVALUATED the name and
    what its gates said, so a reader can tell an appreciation from a rejection. A caveat that only
    said "not a candidate" would render those two identically."""
    t = _a_maintained_orphan()
    fin = asm.load_finalists(_cfg(), ticker=t)[0]
    cav = fin.screen_status or ""

    assert "NOT A CURRENT SCREEN CANDIDATE" in cav
    assert "not a rejection" in cav, "absence must not be presented as a verdict"
    assert "read the verdict, not the absence" in cav
    assert "HUNTS" in cav, "the caveat must state the band's actual scope"
    verdict = asm._last_screen_verdict(_cfg(), t)
    if verdict is not None:
        run_id, outcome = verdict
        assert run_id in cav and outcome.split(" ")[0] in cav, (
            f"the caveat omits the last real verdict ({run_id}: {outcome}) — without it, a name "
            "that PASSED and then grew out of the band reads exactly like one that FAILED")


def test_the_standalone_record_is_truncated_to_its_own_reference_date() -> None:
    """THE VINTAGE PIN, and the bug it caught. `compute_price_features` takes `bars[-1]` as
    "latest" and never filters — it uses `reference_date` only for staleness and window starts. The
    screen cuts the same way since 2026-10-28 (`screens.run._bars_to`); before, a past-dated replay
    read later prices. Here the frontier is rarely the reference date, and the first cut stamped
    IT's 2026-08-04 close ($185.79) onto a 2026-07-06 record: a value contradicting its own vintage
    mark, which is the class this repo keeps paying for.

    Asserted against the STORE, not a literal, so it cannot rot as bars accumulate."""
    import datetime as dt

    from vinci.store import Store

    t = _a_maintained_orphan()
    cfg = _cfg()
    fin = asm.load_finalists(cfg, ticker=t)[0]
    ref = fin.reference_date

    from vinci.resolver import EntityResolver
    iid = EntityResolver.from_config(cfg).resolve_ticker(t).internal_id
    with Store(cfg.db_path) as store:
        bars = store.get_price_history(iid)
    upto = [b for b in bars if b.bar_date <= ref]
    if not upto:
        pytest.skip(f"{t} has no bars at or before {ref} — nothing to compare")
    assert fin.data_record.prices.last.value == pytest.approx(upto[-1].close), (
        f"the record's last price is not the last bar at or before its own reference_date {ref} — "
        "it is carrying a price from the future of its own stamp")
    assert isinstance(ref, dt.date)

    # --- THE HALF THAT MUST NEVER GO DORMANT ---------------------------------------------------
    #
    # This used to read `later = [b for b in bars if b.bar_date > ref]; if later: assert ...`, with
    # `ref` riding the LIVE fleet as-of. That is fine only while the committed fixture happens to
    # end after the last screen run. The weekly job now regenerates the fixture from the same
    # refreshed store the screen just used, so the fixture frontier CATCHES UP to the fleet as-of —
    # `later` becomes empty, `if later:` quietly stops running, and the only assertion that catches
    # the actual bug (a record carrying the frontier's close under an older stamp) disappears
    # without ever going red. A guard that cannot fire is worse than no guard, because the green
    # tick still gets counted.
    #
    # So the vintage is FROZEN INSIDE THE FIXTURE instead of inherited from the fleet: ten bars back
    # from whatever the fixture's own frontier is. Bars after it exist BY CONSTRUCTION, on every
    # machine and every week, so the assertion cannot be skipped — and it is still derived from the
    # fixture rather than hardcoded, so it does not rot as bars accumulate. (TEST-LAYER RULE: a
    # value-level pin belongs on a frozen construction, never on the re-drawn artifact.)
    frozen_ref = bars[-10].bar_date
    before = [b for b in bars if b.bar_date <= frozen_ref]
    after = [b for b in bars if b.bar_date > frozen_ref]
    assert after, (
        f"{t}'s fixture has no bars after {frozen_ref} — the truncation assertion below would be "
        f"testing nothing. Rebuild it: python scripts/build_price_fixture.py")
    frozen = asm._standalone_record(cfg, t, frozen_ref)
    assert frozen.prices.last.value == pytest.approx(before[-1].close), (
        f"at a reference date of {frozen_ref} the record's last price is not that date's bar")
    assert frozen.prices.last.value != pytest.approx(after[-1].close), (
        "the record carries the STORE FRONTIER's close under an older reference_date stamp")


def test_assembly_reads_the_property_not_the_candidate_record() -> None:
    """THE CALL SITE, not the helper — the rule this session has had to learn repeatedly. A
    `Finalist` on the maintenance route has `record=None`, so any surviving `fin.record.data_record`
    raises AttributeError at assembly time on exactly the names this path exists to serve. Asserted
    on the SOURCE, because the failure is in a branch a unit test of the property never enters."""
    import inspect

    src = inspect.getsource(asm)
    assert "fin.record.data_record" not in src, (
        "assemble.py still reaches through `fin.record` for the data record; on the maintenance "
        "route `record` is None and that is an AttributeError, not a caught failure")
    assert "fin.data_record" in src, "nothing reads the property — the route is unreachable"


def test_the_maintenance_reason_names_what_makes_a_name_maintained() -> None:
    """THE KEY ITSELF: a committed dossier or an open underwrite. Both are things the fund already
    carries; neither is a screen verdict."""
    cfg = _cfg()
    t = _a_maintained_orphan()
    assert asm._maintenance_reason(cfg, t) is not None
    assert asm._maintenance_reason(cfg, "ZZZZ") is None
    # and it is keyed on the ARTIFACT, so the reason it gives is checkable
    assert (ROOT / "data" / "dossiers" / t / "dossier.json").exists()


def test_a_finalist_with_neither_source_fails_loud() -> None:
    """FAIL LOUD, never fabricate. A Finalist carrying no record at all is a construction bug; it
    must raise rather than return an empty shell that assembles into a dossier of UNKNOWNs."""
    import datetime as dt

    empty = asm.Finalist(None, rank=None, reference_date=dt.date(2026, 7, 6))
    with pytest.raises(asm.DossierAssemblyError, match="nothing to assemble"):
        _ = empty.data_record


def test_every_committed_dossier_can_still_be_located() -> None:
    """THE FLEET-WIDE CONSEQUENCE. Before this path, a committed dossier whose name had left the
    candidate set could not be re-assembled at all — the artifact was frozen. Every name the fund
    carries must now resolve by one route or the other."""
    cfg = _cfg()
    unreachable = []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        t = p.parent.name
        try:
            asm.load_finalists(cfg, ticker=t)
        except Exception as exc:                                  # noqa: BLE001 - reported below
            unreachable.append(f"{t}: {type(exc).__name__}: {exc}")
    assert not unreachable, (
        "committed dossiers that cannot be re-assembled by either route — a frozen artifact is a "
        f"name the fund can no longer maintain: {unreachable}")


def test_the_caveat_reaches_the_artifact_as_a_caveat_not_a_qa_flag() -> None:
    """THE TIER. `screen_status` is DECISION surface — a reader who does not know the name sits
    outside the candidate set reads every screen-relative number on the page as current. It must
    land in `caveats` (main body, always printed) and must LEAD them, for the same reason a vintage
    stamp leads the block it marks: read after the numbers, it no longer changes how they are
    read."""
    import inspect

    src = inspect.getsource(asm)
    assert "caveats.insert(0, fin.screen_status)" in src, (
        "the screen-status caveat is not inserted at the head of `caveats` — either it is not a "
        "caveat at all (wrong tier: audit, not decision) or it trails the numbers it qualifies")
    # and it must NOT be routed into qa_flags, which are dev/JSON-only
    assert "qa_flags.append(fin.screen_status)" not in src
    assert "qa_flags.insert(0, fin.screen_status)" not in src


def test_the_fleet_snapshot_of_which_names_take_which_route(capsys) -> None:
    """AN INVENTORY, not an assertion about any one name. Records which committed dossiers now
    route through maintenance, so a change in that set is visible in a diff rather than silent."""
    cfg = _cfg()
    cands = _candidate_tickers()
    rows = []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        t = p.parent.name
        rows.append((t, "candidate" if t in cands else "maintenance"))
    maint = [t for t, r in rows if r == "maintenance"]
    # the property under test: routing agrees with candidate-set membership, by construction
    for t, route in rows:
        fin = asm.load_finalists(cfg, ticker=t)[0]
        assert (fin.record is None) is (route == "maintenance"), (
            f"{t} is {route} by the candidate set but routed the other way")
    with capsys.disabled():
        print(f"\n    maintenance-route dossiers ({len(maint)}/{len(rows)}): {maint or 'none'}")


def test_json_snapshots_are_not_mutated_by_reading_them() -> None:
    """A read path must not write. `load_finalists` now touches the screen-run snapshots and the
    dossier tree; none of it may change a committed byte."""
    snaps = _cfg().snapshots_dir
    before = {p: p.read_bytes() for p in sorted(snaps.glob("*.jsonl"))}
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        asm.load_finalists(_cfg(), ticker=p.parent.name)
    after = {p: p.read_bytes() for p in sorted(snaps.glob("*.jsonl"))}
    assert before == after, "reading finalists mutated a committed snapshot"
    assert json.loads((snaps / "ranked_queue.jsonl").read_text().splitlines()[0])
