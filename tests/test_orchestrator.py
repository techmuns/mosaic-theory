"""Verification — the lazy universe screen (``screen_universe``).

Fake EOD + EDGAR clients drive the whole loop deterministically (no network): the cheap price gates
run on every name, EDGAR is fetched only for the price-gate survivors, and one clean idiosyncratic
de-rating is admitted while a flat name is rejected without ever touching EDGAR.
"""

from __future__ import annotations

import shutil
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
    for mod, fn in (("vinci/orchestrator.py", "run_weekly"),
                    ("vinci/orchestrator.py", "refresh_queue"),
                    ("vinci/cli.py", "_cmd_rank")):
        tree = ast.parse((root / mod).read_text())
        node = next((n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == fn), None)
        assert node is not None, f"{fn} not found in {mod}"
        # STRIP comments/docstrings by unparsing the AST — a mention in prose must not satisfy this
        bodies[fn] = ast.unparse(node)

    # run_weekly reaches the ranker through refresh_queue (the weekly tail, extracted so its
    # empty-result and carry-forward cases are testable); follow that hop rather than pinning the
    # exact call shape, which would redden on any refactor that keeps the behaviour.
    # every weekly stage is UNCONDITIONAL — no flag may gate a piece of the scheduled run, which
    # is how the ranker and the structural scan each went missing for months (STATE.md §5)
    assert "build_universe" in bodies["run_weekly"], (
        "run_weekly no longer rebuilds the universe — the screen would run against whatever the "
        "last manual build left behind, and nothing rebuilds it on any other schedule")
    assert "structural=True" in bodies["run_weekly"], (
        "the structural scan is no longer hard-wired into the weekly run — making it optional on "
        "the scheduled path is what let the only demote channel go dormant")
    assert "refresh_queue" in bodies["run_weekly"], (
        "run_weekly does not reach the queue refresh — the weekly job is back to writing the "
        "screen output and leaving the served queue frozen until someone runs the ranker by hand")
    assert "rank_from_snapshots" in bodies["refresh_queue"], (
        "the weekly refresh no longer ranks through the shared path")
    assert "write_queue_snapshots" in bodies["refresh_queue"], (
        "the weekly refresh ranks but never writes the queue snapshots")
    assert "carry_forward_assessment" in bodies["refresh_queue"], (
        "the weekly refresh no longer carries the last explicit --structural/--cause-file "
        "assessment forward — an 8-K-disqualified name climbs back to the top on Monday")
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


# --- the weekly refresh's two dangerous cases (review findings on #420) -------------------------
def _stage(tmp: Path, *, records: bool = True, queue: bool = True,
           empty_records: bool = False) -> Path:
    """A snapshots dir built from the REAL committed artifacts, not hand-rolled rows."""
    src = Path(__file__).resolve().parent.parent / "data" / "snapshots"
    if not (src / "candidate_records.jsonl").exists():
        pytest.skip("no committed snapshots in this worktree")
    snaps = tmp / "snapshots"
    snaps.mkdir(parents=True, exist_ok=True)
    (tmp / "dossiers").mkdir(exist_ok=True)
    for name in ("universe_snapshot.jsonl", "securities.jsonl"):
        if (src / name).exists():
            shutil.copyfile(src / name, snaps / name)
    if records:
        snaps.joinpath("candidate_records.jsonl").write_text(
            "" if empty_records else (src / "candidate_records.jsonl").read_text())
    if queue:
        shutil.copyfile(src / "ranked_queue.jsonl", snaps / "ranked_queue.jsonl")
    return snaps


def test_a_screen_that_finds_nothing_clears_the_queue_instead_of_serving_last_week() -> None:
    """`screen_universe` clears candidates before the unconditional export, so a zero-candidate run
    leaves `candidate_records.jsonl` EMPTY. Guarding the write on `if ranked:` then kept the
    previous week's `ranked_queue.jsonl` — the site would show names the latest completed screen
    REJECTED, and the staleness banner could not catch it either, because a seven-day-old retained
    queue reads as fresh. An empty screen result is an answer, not a failure to produce one."""
    import tempfile

    from vinci.config import Config
    from vinci.orchestrator import refresh_queue

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        snaps = _stage(tmp, empty_records=True)
        before = len([x for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x])
        assert before > 50, "staging did not put a real previous queue in place"
        out = refresh_queue(Config(data_dir=tmp))
        after = [x for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x.strip()]
        assert out["ranked"] == 0
        assert after == [], (
            f"the empty screen result left {len(after)} stale rows being served as current")


def test_a_missing_screen_snapshot_leaves_the_existing_queue_alone() -> None:
    """The other side of the same coin, and why the distinction is made on the INPUT rather than on
    the output being empty: a fresh checkout has no `candidate_records.jsonl` at all, and must not
    have its committed queue blanked by a job that never screened anything."""
    import tempfile

    from vinci.config import Config
    from vinci.orchestrator import refresh_queue

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        snaps = _stage(tmp, records=False)
        before = (snaps / "ranked_queue.jsonl").read_text()
        out = refresh_queue(Config(data_dir=tmp))
        assert out["ranked"] == 0
        assert (snaps / "ranked_queue.jsonl").read_text() == before, (
            "a run with no screen output blanked the existing queue")


def test_a_manual_structural_disqualifier_survives_the_weekly_refresh() -> None:
    """`vinci rank --structural` writes `structural_flag` into `ranked_queue.jsonl` and NOWHERE
    else. A scheduled refresh that supplies no flags would rewrite that artifact and drop them, so
    a name capped at 0.05 by an 8-K disqualifier would climb back to the top of the queue on Monday
    with no operator action. The flag is carried forward instead — demote-only, so a stale one can
    only keep a name down, and an 8-K does not un-happen."""
    import json
    import tempfile

    from vinci.config import Config
    from vinci.orchestrator import refresh_queue
    from vinci.rank import RankedCandidate

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        snaps = _stage(tmp)
        rows = [json.loads(x) for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x]
        victim = rows[0]["ticker"]  # the CURRENT top name — the most visible thing to lose
        assert rows[0]["structurally_disqualified"] is False
        rows[0]["structural_flag"] = {
            "signal": "going-concern", "detail": "substantial doubt language in the 8-K",
            "source": "8-K 0000000000-26-000001 item 8.01 filed 2026-08-01"}
        rows[0]["structurally_disqualified"] = True
        (snaps / "ranked_queue.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n")

        out = refresh_queue(Config(data_dir=tmp))
        assert out["carried_structural"] == 1, "the operator's assessment was not carried forward"
        after = {r.ticker: r for r in (
            RankedCandidate.model_validate_json(x)
            for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x.strip())}
        got = after[victim]
        assert got.structurally_disqualified, f"{victim} came back un-sunk after the refresh"
        assert got.structural_flag is not None and got.structural_flag.signal == "going-concern"
        assert got.priority_score <= 0.05, (
            f"{victim} kept its flag but not its cap — score {got.priority_score}")
        assert got.rank > len(after) // 2, f"{victim} is still ranked {got.rank} of {len(after)}"


def test_a_live_structural_scan_replaces_the_carry_forward_rather_than_merging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The carry-forward exists for runs that DON'T scan. When a scan DOES run it is authoritative:
    it re-checks all five signals against current filings, so a name whose signal no longer fires
    must come back CLEAN. Merging instead would make a flag permanent — an 8-K disqualifier could
    never be cleared by the very scan designed to re-evaluate it, and the demote would outlive its
    own evidence.

    The scan itself is network; only the compose-with-carry-forward decision is under test, so
    `scan_structural` is stubbed to return a DIFFERENT verdict from the one on the prior queue."""
    import json
    import tempfile

    from vinci import orchestrator
    from vinci.config import Config
    from vinci.rank import RankedCandidate, StructuralDisqualifier
    from vinci.rank.structural import StructuralScan

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        snaps = _stage(tmp)
        rows = [json.loads(x) for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x]
        stale, fresh = rows[0]["ticker"], rows[1]["ticker"]
        rows[0]["structural_flag"] = {"signal": "going-concern", "detail": "d", "source": "8-K old"}
        rows[0]["structurally_disqualified"] = True
        (snaps / "ranked_queue.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

        # the live scan clears `stale` and fires on `fresh` instead
        # A scan that COVERED every candidate, cleared `stale`, and fired on `fresh`. Keyed by
        # internal_id off the real candidates — the same key scan_structural returns, so the stub
        # cannot pass by using a key the production mapping would never see.
        def _fake_scan(cands, **_k):  # type: ignore[no-untyped-def]
            by_ticker = {c.data_record.identity.ticker: c.data_record.identity.internal_id
                         for c in cands}
            return StructuralScan(
                flags={by_ticker[fresh]: StructuralDisqualifier(
                    signal="delisting/deficiency notice (3.01)", detail="d", source="8-K new")},
                covered=frozenset(by_ticker.values()))
        monkeypatch.setattr(orchestrator, "scan_structural", _fake_scan)
        monkeypatch.setattr(
            orchestrator.EdgarClient, "from_config", classmethod(lambda cls, c: None))
        monkeypatch.setattr(orchestrator, "build_sec_http", lambda cfg: None)

        out = orchestrator.refresh_queue(Config(data_dir=tmp), structural=True)
        assert out["carried_structural"] == 1  # the prior flag WAS read...
        after = {r.ticker: r for r in (
            RankedCandidate.model_validate_json(x)
            for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x.strip())}
        assert not after[stale].structurally_disqualified, (
            f"{stale} kept a flag the live scan no longer fires — the carry-forward was merged in, "
            "so a disqualifier can never be cleared by the scan meant to re-evaluate it")
        assert after[fresh].structurally_disqualified, f"{fresh}: the live scan's verdict was lost"
        assert after[fresh].priority_score <= 0.05


def test_a_name_the_scan_could_not_reach_keeps_its_prior_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE FAILURE-MODE REGRESSION (#431). `scan_structural` fails SOFT per name — a transient EDGAR
    or cache error yields no flag for that name, which is indistinguishable from a clean result
    unless coverage is consulted. Replacing prior flags wholesale therefore let ONE bad response
    erase a real 8-K disqualifier and lift the name back above its 0.05 cap: the #420 failure,
    reintroduced by the fix for it.

    Prior flags must survive for exactly the names the scan did not cover, and nothing else."""
    import json
    import tempfile

    from vinci import orchestrator
    from vinci.config import Config
    from vinci.rank import RankedCandidate
    from vinci.rank.structural import StructuralScan

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        snaps = _stage(tmp)
        rows = [json.loads(x) for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x]
        unreachable = rows[0]["ticker"]
        rows[0]["structural_flag"] = {
            "signal": "going-concern", "detail": "substantial doubt",
            "source": "8-K 0000000000-26-000001 item 8.01 filed 2026-08-01"}
        rows[0]["structurally_disqualified"] = True
        (snaps / "ranked_queue.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

        # the scan reaches every name EXCEPT `unreachable`, and finds nothing on the ones it reached
        def _partial_scan(cands, **_k):  # type: ignore[no-untyped-def]
            reached = frozenset(c.data_record.identity.internal_id for c in cands
                                if c.data_record.identity.ticker != unreachable)
            return StructuralScan(flags={}, covered=reached)
        monkeypatch.setattr(orchestrator, "scan_structural", _partial_scan)
        monkeypatch.setattr(
            orchestrator.EdgarClient, "from_config", classmethod(lambda cls, c: None))
        monkeypatch.setattr(orchestrator, "build_sec_http", lambda cfg: None)

        out = orchestrator.refresh_queue(Config(data_dir=tmp), structural=True)
        assert out["structural_scanned"] > 0
        after = {r.ticker: r for r in (
            RankedCandidate.model_validate_json(x)
            for x in (snaps / "ranked_queue.jsonl").read_text().splitlines() if x.strip())}
        assert after[unreachable].structurally_disqualified, (
            f"{unreachable} was never scanned, yet its 8-K disqualifier was erased and the name "
            "lifted back above the 0.05 cap — a transient EDGAR failure must not clear a flag")
        assert after[unreachable].priority_score <= 0.05
        # and the names the scan DID reach came back clean, so a stale flag is not made permanent
        assert sum(1 for r in after.values() if r.structurally_disqualified) == 1


def test_an_empty_universe_rebuild_fails_the_run_instead_of_reporting_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`build_universe()` CLEARS and exports `universe_snapshot.jsonl` before returning. If an empty
    rebuild were a soft return, `_cmd_run_weekly` would print the status and exit 0, and the
    workflow's next step commits `data/snapshots` — publishing a blank universe beside the previous
    candidates and queue while reporting a clean run. A transient resolver/price/shares outage must
    fail the job BEFORE that commit (#431)."""
    import tempfile

    from vinci import orchestrator
    from vinci.config import Config

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "snapshots").mkdir(parents=True)
        monkeypatch.setattr(orchestrator, "build_universe", lambda cfg, **k: {"admitted": 0})
        monkeypatch.setattr(
            orchestrator.PolygonEodClient, "from_config", classmethod(lambda cls, c: None))
        monkeypatch.setattr(
            orchestrator.EdgarClient, "from_config", classmethod(lambda cls, c: None))
        with pytest.raises(RuntimeError, match="universe rebuilt EMPTY"):
            orchestrator.run_weekly(Config(data_dir=tmp), end=date(2026, 8, 12))
