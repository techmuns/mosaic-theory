"""THE UNIVERSE BUILD SEEDS THE ENTITY MASTER BEFORE IT WRITES OVER IT.

THE OUTAGE (2026-08-03 → 08-24, four consecutive weekly runs). `data/vinci.db` is git-ignored, so
on any fresh checkout — every CI run — the store starts EMPTY. `build_universe` upserts only what
THIS fetch admits, then exports `issuers`/`securities`/`universe_snapshot`. The first two are
accumulate-only (an identity is never pruned: the master has to resolve a ledgered name after it
leaves the universe), so writing one fetch's subset over the committed master is a shrink, and the
no-row-drop guard refused it:

    ROW-DROP on issuers.jsonl: writing 1810 row(s) over 2304 on disk
    would drop 503 existing row(s) by PK.

The served queue sat frozen at `screen_run_at 2026-08-14` for four weeks while a red job re-ran
itself every Monday.

WHY IT HID FOR FOUR WEEKS, AND WHY THIS FILE EXISTS. It passed on every laptop the entire time,
because a developer's store already holds the accumulation — "green everywhere except where it
matters", the same shape as the eleven-merge maintenance-pin streak. A pin that runs against a
populated store proves nothing here, so every test below builds an EMPTY store and seeds it only
from committed snapshots, which is exactly CI's condition.

`run_weekly` DOES seed the store — at its own line, AFTER `build_universe` has already exported.
The seed has to happen inside the context that writes.
"""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from vinci.config import Config
from vinci.store import NO_ROW_DROP_TABLES, Store
from vinci.universe import BUILD_UNIVERSE_SEED_TABLES, BUILD_UNIVERSE_TABLES

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "data" / "snapshots"


def _ci_like(tmp_path: Path) -> tuple[Config, Path]:
    """A fresh checkout: committed snapshots present, NO working DB — exactly what CI has."""
    snaps = tmp_path / "snapshots"
    snaps.mkdir(parents=True)
    for name in BUILD_UNIVERSE_TABLES:
        src = COMMITTED / f"{name}.jsonl"
        if src.exists():
            shutil.copy(src, snaps / f"{name}.jsonl")
    cfg = Config(data_dir=tmp_path)
    assert not cfg.db_path.exists(), "the point of this fixture is that no store exists yet"
    return cfg, snaps


def _rows(path: Path) -> int:
    return len([ln for ln in path.read_text().splitlines() if ln.strip()])


# --- the seed set is DERIVED, not hand-listed --------------------------------------------------

def test_the_seed_set_is_exactly_the_export_tables_that_may_never_shrink() -> None:
    """DERIVED FROM THE STORE'S OWN DECLARATION. A hand-copied list is one edit away from silently
    missing a table the day another accumulate-only one joins the export — and the failure mode of
    missing one is this whole outage, again, on a different file."""
    assert set(BUILD_UNIVERSE_SEED_TABLES) == set(BUILD_UNIVERSE_TABLES) & NO_ROW_DROP_TABLES
    assert set(BUILD_UNIVERSE_SEED_TABLES) == {"issuers", "securities"}


def test_the_point_in_time_table_is_deliberately_not_seeded() -> None:
    """`universe_snapshot` is replaced on each run — the committed file holds exactly ONE `as_of`.
    Seeding it back would make it accumulate dates it was never meant to keep, turning a fix for
    one table into a silent semantic change in another. This is the half a naive "just seed
    everything" fix gets wrong."""
    assert "universe_snapshot" in BUILD_UNIVERSE_TABLES
    assert "universe_snapshot" not in BUILD_UNIVERSE_SEED_TABLES
    committed = COMMITTED / "universe_snapshot.jsonl"
    as_ofs = {json.loads(ln)["as_of"] for ln in committed.read_text().splitlines() if ln.strip()}
    assert len(as_ofs) == 1, (
        f"universe_snapshot holds {len(as_ofs)} as_of generations — it is supposed to be "
        f"point-in-time; if that changed, this test's premise needs re-reading: {sorted(as_ofs)}")


# --- the outage itself, reproduced on an EMPTY store -------------------------------------------

def test_an_unseeded_export_over_the_committed_master_is_refused(tmp_path: Path) -> None:
    """THE FAILURE, REPRODUCED. Without the seed, an empty store exporting one fetch's worth of
    identities over the committed master raises — which is the guard being RIGHT. The bug was never
    the guard; it was writing an unseeded subset at it."""
    cfg, snaps = _ci_like(tmp_path)
    with Store(cfg.db_path) as store:                      # empty, no seed
        store.clear_universe()
        with pytest.raises(RuntimeError, match="ROW-DROP on issuers.jsonl"):
            store.export_snapshots(snaps, tables=BUILD_UNIVERSE_TABLES)


def test_seeding_first_lets_the_same_export_through(tmp_path: Path) -> None:
    """THE FIX, on the real committed corpus: seed the never-shrink tables, and the identical
    export succeeds with the master intact rather than truncated."""
    cfg, snaps = _ci_like(tmp_path)
    before = _rows(snaps / "issuers.jsonl")
    assert before > 0
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(snaps, tables=BUILD_UNIVERSE_SEED_TABLES)
        store.clear_universe()
        store.export_snapshots(snaps, tables=BUILD_UNIVERSE_TABLES)
    assert _rows(snaps / "issuers.jsonl") == before, "the master must survive the round trip whole"


def test_the_seed_survives_clear_universe(tmp_path: Path) -> None:
    """ORDERING, pinned. `build_universe` seeds and THEN calls `clear_universe()`, which drops the
    entire `universe_snapshot` table. If clearing ever reached the entity master the seed would be
    pointless, and the outage would return with the fix apparently still in place."""
    cfg, snaps = _ci_like(tmp_path)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(snaps, tables=BUILD_UNIVERSE_SEED_TABLES)
        seeded = len(list(store.iter_securities()))
        assert seeded > 0, "nothing was seeded — the fixture or the seed set is wrong"
        store.clear_universe()
        assert len(list(store.iter_securities())) == seeded, (
            "clear_universe() pruned the entity master — the seed cannot protect the export")


def test_a_genuinely_new_identity_still_reaches_the_master(tmp_path: Path) -> None:
    """THE SEED MUST NOT BECOME A FREEZE. Accumulate-only means the master GROWS; a fix that made
    the export merely reproduce the committed file would quietly stop recording new names, which
    is the same outage wearing the opposite sign."""
    cfg, snaps = _ci_like(tmp_path)
    before = _rows(snaps / "issuers.jsonl")
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(snaps, tables=BUILD_UNIVERSE_SEED_TABLES)
        # BUILT FROM THE REAL TYPE, not hand-rolled to the shape this test wants: a fixture
        # invented field-by-field dictates the production signature instead of testing it (#305).
        # A committed identity is copied and re-keyed, so every required field is whatever the
        # model actually requires today.
        template = next(iter(store.iter_securities()))
        newcomer = template.model_copy(update={
            "internal_id": "SEC-0000000000-ZZTEST", "ticker": "ZZTEST",
            "eod_symbol": "ZZTEST", "name": "Test Newcomer Inc"})
        store.upsert_security(newcomer, first_seen=None)
        store.export_snapshots(snaps, tables=BUILD_UNIVERSE_TABLES)
    assert _rows(snaps / "issuers.jsonl") >= before, "the master shrank"
    tickers = {json.loads(ln).get("ticker")
               for ln in (snaps / "securities.jsonl").read_text().splitlines() if ln.strip()}
    assert "ZZTEST" in tickers, "a newly seen identity did not reach the exported master"


# --- the subset loader itself -------------------------------------------------------------------

def test_rebuild_refuses_an_unknown_table(tmp_path: Path) -> None:
    """Same refusal `export_snapshots` already makes, in the same shape — a typo'd table name is a
    silent no-op otherwise, and a seed that silently loaded nothing is how this returns."""
    cfg, snaps = _ci_like(tmp_path)
    with Store(cfg.db_path) as store, pytest.raises(ValueError, match="unknown table"):
        store.rebuild_from_snapshots(snaps, tables=("issuers", "not_a_table"))


def test_rebuild_defaults_to_every_table_when_no_subset_is_given(tmp_path: Path) -> None:
    """The existing callers pass no `tables` and must keep loading everything — the subset is an
    ADDITION, never a narrowing of the default."""
    cfg, snaps = _ci_like(tmp_path)
    with Store(cfg.db_path) as store:
        counts = store.rebuild_from_snapshots(snaps)
    from vinci.store import SNAPSHOT_TABLES
    assert set(counts) == set(SNAPSHOT_TABLES)


def test_build_universe_itself_seeds_before_it_exports(tmp_path: Path, monkeypatch) -> None:
    """THE CALL SITE, not just the mechanism (the pin-the-helper trap, caught by mutation).

    The pins above exercise `rebuild_from_snapshots` + `export_snapshots` directly, so deleting the
    seed line from `build_universe` left every one of them GREEN — a guard on the primitives that
    survives its only caller being removed, which is precisely the shape that let this outage run
    four weeks.

    So this runs the REAL `build_universe` against an EMPTY store with an EMPTY universe feed. No
    name is admitted, the loop body never executes, and the function goes straight to its export —
    which without the seed writes 0 rows over the committed master and must raise, and with the
    seed writes the master back intact. Nothing about the fetch is faked beyond returning nothing:
    the three clients are stubbed to their narrowest honest answer rather than to a shape this test
    invented."""
    import vinci.universe as uni

    cfg, snaps = _ci_like(tmp_path)
    before = _rows(snaps / "issuers.jsonl")

    class _Resolver:
        @classmethod
        def from_config(cls, _cfg): return cls()
        def iter_universe(self, _exchanges): return iter(())

    class _Eod:
        @classmethod
        def from_config(cls, _cfg): return cls()
        def security_types(self): return {}
        def grouped_daily(self, _d): return {}
        def share_class_counts(self, _tickers): return {}

    class _Edgar:
        @classmethod
        def from_config(cls, _cfg): return cls()
        def shares_outstanding_with_provenance(
            self, _periods, *, include_period_average=False): return {}, {}

    monkeypatch.setattr(uni, "EntityResolver", _Resolver)
    monkeypatch.setattr(uni, "PolygonEodClient", _Eod)
    monkeypatch.setattr(uni, "EdgarClient", _Edgar)

    uni.build_universe(cfg, reference_date=date(2026, 8, 24))

    assert _rows(snaps / "issuers.jsonl") == before, (
        "build_universe exported without seeding — the committed entity master was truncated")


# --- the seed must not delete the alarms it now runs past ---------------------------------------

def test_the_blank_universe_guard_reads_the_universe_not_the_entity_master() -> None:
    """THE REGRESSION THE SEED WOULD HAVE INTRODUCED (review finding, #494).

    `run_weekly`'s #431 guard always MEANT to catch a zero-admit rebuild — its message says
    "universe rebuilt EMPTY" — but it asked `iter_securities()`, which is the accumulate-only
    ENTITY MASTER and answers a different question. That was survivable only by accident: on CI's
    empty store a zero-admit run died earlier, at the very ROW-DROP this PR fixes. Seeded, the
    master is never empty, so the guard could no longer fire — and `screen_universe` falls back to
    screening the ENTIRE master with `caps = {}` when the universe is empty, so the run would have
    committed a blank universe and exited 0.

    Asserted on the source because the alternative is a live `run_weekly` (network, keys, an hour):
    what is under test is WHICH TABLE the guard consults, and that is visible without running it.
    """
    import inspect

    from vinci.orchestrator import run_weekly

    src = inspect.getsource(run_weekly)
    guard = "if not store.latest_universe(end):"
    assert guard in src, (
        "the blank-universe guard no longer reads the universe snapshot — if it is back on "
        "`iter_securities()` the seed makes it unfireable and a zero-admit run publishes blank")
    # and it must GUARD the raise, not merely appear somewhere near it
    assert src.index(guard) < src.index('raise RuntimeError(\n                f"universe rebuilt')
    # the old emptiness test must not be what decides it
    decider = src[src.index(guard):src.index("universe rebuilt EMPTY")]
    assert "iter_securities" not in decider


def test_the_future_identity_check_is_seeded_and_still_precedes_build_universe() -> None:
    """TWO CONSTRAINTS, BOTH REAL — and the first attempt at this fix satisfied only one.

    The #442 check must run BEFORE `build_universe`, or the leaked identities are already in the
    universe snapshot and filed under the run's id — `test_a_backdated_run_refuses_identities_the
    _store_learned_later` pins that, and it caught the wrong fix when the check was simply moved
    after the seed.

    It must ALSO run after the entity master is loaded, or on a fresh checkout — every CI run —
    it inspects an EMPTY store, sees nothing, and `build_universe`'s own seed then loads the very
    identities it exists to refuse (the load is INSERT-OR-REPLACE and COALESCE preserves the
    seeded `first_seen`).

    So the invariant is an ORDER of three: seed, then check, then build."""
    import inspect

    from vinci.orchestrator import run_weekly

    src = inspect.getsource(run_weekly)
    seed = src.index("rebuild_from_snapshots(cfg.snapshots_dir, tables=BUILD_UNIVERSE_SEED_TABLES)")
    check = src.index("identities_first_seen_after")
    build = src.index("build_universe(cfg,")
    assert seed < check, (
        "the future-identity check runs before any seed — on a fresh checkout it inspects an "
        "empty store and the seed then admits exactly what it exists to refuse")
    assert check < build, (
        "the check runs after build_universe — by then the leaked identities are in the universe "
        "snapshot and filed under this run's id, which is what #442 exists to prevent")


def test_a_subset_loads_in_schema_order_whatever_order_the_caller_names(tmp_path: Path) -> None:
    """FOREIGN KEYS ARE ON (review finding, #494). A subset naming children before parents —
    `("securities", "issuers")` — raised `FOREIGN KEY constraint failed`. The caller states WHICH
    tables; the schema decides in what order, because only it knows the dependencies."""
    cfg, snaps = _ci_like(tmp_path)
    with Store(cfg.db_path) as store:
        counts = store.rebuild_from_snapshots(snaps, tables=("securities", "issuers"))
    assert counts["issuers"] > 0 and counts["securities"] > 0
