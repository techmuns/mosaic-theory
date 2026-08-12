"""Verification — the lazy universe screen (``screen_universe``).

Fake EOD + EDGAR clients drive the whole loop deterministically (no network): the cheap price gates
run on every name, EDGAR is fetched only for the price-gate survivors, and one clean idiosyncratic
de-rating is admitted while a flat name is rejected without ever touching EDGAR.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from vinci.edgar.client import all_unknown_snapshot
from vinci.eod.client import RawBar
from vinci.resolver.index import pad_cik
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import DataField, SourceTier
from vinci.screens import screen_universe
from vinci.store import Store

REF = date(2026, 6, 12)
LOOKBACK = 500


def _ident(ticker: str, cik: str) -> Identity:
    return Identity(
        internal_id=f"SEC-{cik}-{ticker}", issuer_id=f"ISS-{cik}", cik=cik, ticker=ticker,
        mic="XNYS", exchange="NYSE", eod_symbol=ticker, name=f"{ticker} Inc.",
    )


class _FakeEod:  # duck-types EodClient.grouped_daily
    def __init__(self, paths: dict[str, object]) -> None:
        self._paths = paths

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        out = {}
        for t, fn in self._paths.items():
            c = fn(day)  # type: ignore[operator]
            out[t] = RawBar(ticker=t, open=c, high=c + 1, low=c - 1, close=c, volume=1e6)
        return out


class _FakeEdgar:  # duck-types the two EdgarClient methods enrich uses
    def __init__(self) -> None:
        self.fetched: list[str] = []

    def fundamental_snapshot(self, cik):  # type: ignore[no-untyped-def]
        self.fetched.append(pad_cik(cik))
        return all_unknown_snapshot(pad_cik(cik))

    def companyfacts(self, cik):  # type: ignore[no-untyped-def]
        return {}  # no EPS → G3 P/E-percentile defers (UNKNOWN)


def _drop(day: date) -> float:
    # flat at 100 until ~120 days before the ref date, then a sharp idiosyncratic decline to 55
    days_before = (REF - day).days
    return 100.0 if days_before > 120 else 100.0 - (120 - days_before) / 120 * 45.0


def _flat(_day: date) -> float:
    return 100.0


def test_screen_universe_lazy_admits_one_de_rating(tmp_path: Path) -> None:
    drop, flat = _ident("DROP", "0000000001"), _ident("FLAT", "0000000002")
    with Store(tmp_path / "u.db") as store:
        for s in (drop, flat):
            store.upsert_security(s)
            cap = DataField.present(1e9, as_of=REF, source="DERIVED", tier=SourceTier.DERIVED)
            store.record_universe(
                as_of=REF, internal_id=s.internal_id, in_universe=True, market_cap=cap
            )
        eod = _FakeEod({"DROP": _drop, "FLAT": _flat, "IWM": _flat})
        edgar = _FakeEdgar()
        cands, stats = screen_universe(
            store, eod, edgar, reference_date=REF, lookback_days=LOOKBACK, staleness_days=5
        )

    assert stats["universe"] == 2
    # the de-rating is admitted; the flat name is not
    assert {c.data_record.identity.ticker for c in cands} == {"DROP"}
    # EDGAR was fetched ONLY for the price-gate survivor (lazy), never for the flat name
    assert edgar.fetched == ["0000000001"]


def test_rescreen_replaces_not_accretes(tmp_path: Path) -> None:
    """A re-screen on a NEW reference date must REPLACE the candidate set, not pile on top of the
    prior run's — the run_weekly accretion bug (601-style duplicates). Run the screen TWICE against
    one store and assert the stored candidates are exactly the SECOND run's set, never the union.

    This catches the accretion specifically: a test that only checks "one run → N candidates" passes
    even with the bug. Here week-1's date-stamped ids can only survive into week-2 if the re-screen
    accreted, so asserting they are gone is the discriminating check.
    """
    drop, flat = _ident("DROP", "0000000001"), _ident("FLAT", "0000000002")
    with Store(tmp_path / "u.db") as store:
        for s in (drop, flat):
            store.upsert_security(s)
            cap = DataField.present(1e9, as_of=REF, source="DERIVED", tier=SourceTier.DERIVED)
            store.record_universe(
                as_of=REF, internal_id=s.internal_id, in_universe=True, market_cap=cap
            )
        eod = _FakeEod({"DROP": _drop, "FLAT": _flat, "IWM": _flat})
        edgar = _FakeEdgar()
        c1, _ = screen_universe(  # week 1
            store, eod, edgar, reference_date=REF, lookback_days=LOOKBACK, staleness_days=5
        )
        c2, _ = screen_universe(  # week 2 — a LATER reference date, like the next weekly run
            store, eod, edgar, reference_date=date(2026, 6, 19), lookback_days=LOOKBACK,
            staleness_days=5,
        )
        assert c1 and c2  # both runs admit the de-rating
        # week-1's candidate ids (date-stamped 20260612) must be GONE — the full-replace clear drops
        # the whole prior generation. Under the accretion bug they lingered and these asserts fail.
        for c in c1:
            assert store.get_candidate(c.candidate_id) is None
        # ...and only week-2's generation remains — the set is THIS run's, not the union of both.
        for c in c2:
            assert store.get_candidate(c.candidate_id) is not None


# --- the weekly job now writes the QUEUE, not just the screen ------------------------------------
def test_the_weekly_job_ranks_through_the_same_path_as_the_cli() -> None:
    """Until 2026-08-12 `run_weekly` stopped at the screen: `candidate_records.jsonl` advanced every
    week while `ranked_queue.jsonl` only moved when a human remembered to run `vinci rank`, and the
    served queue had drifted 12 days and 95 names behind the screen feeding it (STATE.md §5).

    Pinned at the SOURCE layer deliberately, and this is the honest limit: `run_weekly` builds its
    own Polygon/EDGAR clients from config, so exercising it end-to-end would mean faking the network
    rather than testing the wiring this guards. What must not silently regress is that the weekly
    job calls the ranker AT ALL, and that both callers go through the ONE path — the moment they
    diverge, a CI-built queue and a hand-built one stop being the same object."""
    import ast

    root = Path(__file__).resolve().parent.parent
    bodies: dict[str, str] = {}
    for mod, fn in (("vinci/orchestrator.py", "run_weekly"), ("vinci/cli.py", "_cmd_rank")):
        tree = ast.parse((root / mod).read_text())
        node = next((n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == fn), None)
        assert node is not None, f"{fn} not found in {mod}"
        # STRIP comments/docstrings by unparsing the AST — a mention in prose must not satisfy this
        bodies[fn] = ast.unparse(node)

    assert "rank_from_snapshots" in bodies["run_weekly"], (
        "run_weekly does not call rank_from_snapshots — the weekly job is back to writing the "
        "screen output and leaving the served queue frozen until someone runs the ranker by hand")
    assert "write_queue_snapshots" in bodies["run_weekly"], (
        "run_weekly ranks but never writes the queue snapshots")
    assert "rank_from_snapshots" in bodies["_cmd_rank"], (
        "`vinci rank` no longer shares the weekly job's ranking path — a CI queue and a hand-built "
        "one can now diverge")


def test_rank_from_snapshots_attaches_the_resolved_labels() -> None:
    """THE REGRESSION THIS CHANGE COULD HAVE SHIPPED. Sector/industry are attached by the WRITER,
    never the scorer (vinci.rank may not import vinci.labels — a separate AST fence asserts it), so
    a weekly job that called `rank_candidates` directly would have emitted a queue with both fields
    None and quietly broken the frontend's industry column and cluster roll-up. Run on the REAL
    committed screen output, not a fixture."""
    from vinci.config import Config
    from vinci.orchestrator import rank_from_snapshots

    cfg = Config(data_dir=Path(__file__).resolve().parent.parent / "data")
    if not (cfg.snapshots_dir / "candidate_records.jsonl").exists():
        pytest.skip("no committed candidate_records.jsonl in this worktree")
    ranked = rank_from_snapshots(cfg)
    assert len(ranked) > 50, f"only {len(ranked)} rows ranked from the committed screen output"
    labelled = [r for r in ranked if r.sector and r.industry]
    assert len(labelled) > len(ranked) * 0.8, (
        f"only {len(labelled)}/{len(ranked)} rows carry a resolved sector AND industry — the "
        "writer-side label enrichment is not being applied")
    # and the structured volume ratio rides along, so the queue cell never re-parses its own label
    assert all(r.volume_spike is not None for r in ranked if r.volume_state != "UNKNOWN")


def test_rank_from_snapshots_is_empty_not_fatal_when_the_screen_has_produced_nothing(
    tmp_path: Path,
) -> None:
    """A fresh checkout, or the very first run, has no candidate_records.jsonl. The weekly job must
    reach its return rather than dying between the screen export and the queue write — it returns
    [] and the caller skips the write, leaving any existing queue untouched."""
    from vinci.config import Config
    from vinci.orchestrator import rank_from_snapshots

    cfg = Config(data_dir=tmp_path)
    cfg.ensure_dirs()
    assert rank_from_snapshots(cfg) == []
