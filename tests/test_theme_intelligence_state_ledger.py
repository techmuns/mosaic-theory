"""The paid-call ledger survives `state pull` — runs, costs and run ids, never counted twice.

Observed 2026-10-11 on the GitHub state test (PR #703): a pull rebuilt the registry from the
branch and REPLAYED two paid local imports ($0.31 and $0.47) under new run ids, from the
cache at $0; the original runs and their paid-call records then survived only in the pre-pull
backup, so the branch under-reported what was spent.

A pull now CARRIES every run the branch lacks — run id, times, cost and every call row,
unchanged — marked `ledger_only`, and the replay names them (`replay_of`); the evidence is
derived once (by the replay), the ingestion dates are the originals, and the ledger is checked:
every paid call of the replaced registry and of the branch kept exactly once.

Documents are the SYNTHETIC fixtures; a scripted model reports token usage, so its calls are
PAID records exactly as a real call's; a local bare git repository stands in for the remote.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_state_sync import (
    AS_OF,
    MS_PDF,
    _bare,
    _ms_ext,
    _old_ext,
    _old_note,
    _scan,
)
from tests.theme_intelligence_support import JPM_DIR, FrozenSecHttp, make_pipeline
from vinci.theme_intelligence import state
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.ingest import ingest_file
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import build_dashboard, report_runs
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.securities import SecResolver
from vinci.theme_intelligence.store import Store


class LiveNetworkError(BaseException):
    """A BaseException on purpose: a broad `except Exception` must not swallow it."""


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def refuse(self: Any, request: Any) -> Any:
        raise LiveNetworkError(f"live network request in an offline test: {request.url}")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


class PaidModel:
    """Answers like the model and REPORTS USAGE (1,000 in / 400 out per call = $0.015 at the
    configured price), so every answer is a paid-call record; nothing added by completeness."""

    model = "claude-opus-4-8"

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.calls.append(tool["name"])
        self.last_usage = {"input_tokens": 1000, "output_tokens": 400}
        if tool["name"] == "record_article_evidence":
            return _ms_ext() if "gas turbine" in user else _old_ext()
        return {}


def _paid_pipeline(tmp: Path, model: PaidModel) -> Pipeline:
    resolver = SecResolver(tmp / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]
    return Pipeline(tmp / "ti", sources=load_sources(), taxonomy=load_taxonomy(),
                    client=model, resolver=resolver, review=False)  # type: ignore[arg-type]


def _import(pipe: Pipeline, path: Path) -> str:
    """One PAID import, in a run of its own."""
    run = pipe.start_run("ingest", as_of=AS_OF)
    res = ingest_file(pipe, path, Declared(source_id="ms_research", llm_permitted=True),
                      as_of=AS_OF)
    assert res.status == "INGESTED", res.note
    pipe.finish_run(RunStatus.SUCCEEDED)
    return run.run_id


def _evidence(st: Store, article_ids: set[str]) -> dict[str, tuple[int, int]]:
    """Per uploaded article: its claims, and the thesis links citing them (any thesis)."""
    out = {}
    for aid in article_ids:
        cids = {c.claim_id for c in st.claims_for_article(aid)}
        links = sum(1 for t in st.theses() for lk in st.links(t.thesis_id) if lk.claim_id in cids)
        out[aid] = (len(cids), links)
    return out


def _total(ledger: dict[str, tuple[str, float | None]]) -> float:
    return round(sum(c or 0.0 for _r, c in ledger.values()), 6)


def _laptop_with_two_paid_imports(tmp: Path) -> tuple[str, Path, PaidModel, list[str]]:
    """The branch holds week 1; a laptop pulls it and makes TWO paid imports it has not pushed
    when the branch moves on to week 2."""
    remote = _bare(tmp)
    actions = make_pipeline(tmp / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    root = tmp / "laptop" / "ti"
    state.pull(root, remote)
    model = PaidModel()
    laptop = _paid_pipeline(tmp / "laptop", model)
    ids = [_import(laptop, MS_PDF), _import(laptop, _old_note(tmp))]
    laptop.store.close()
    _scan(actions, "week-2")
    state.push(actions.paths.root, remote)
    return remote, root, model, ids


def test_paid_imports_survive_pull_replay_push_and_a_fresh_restore(tmp_path: Path) -> None:
    remote, root, model, ids = _laptop_with_two_paid_imports(tmp_path)
    before = Store(root / "registry.db")
    ledger0 = before.paid_ledger()
    runs0 = {r.run_id: r for r in before.runs()}
    docs0 = {d.doc_id: d for d in before.documents()}
    arts0 = {a.article_id: a for a in before.articles()}
    theses0 = {t.thesis_id: t for t in before.theses()}
    uploaded = {d.article_id for d in docs0.values() if d.article_id}
    evidence0 = _evidence(before, uploaded)
    before.close()
    assert len(uploaded) == 2 and all(n and k for n, k in evidence0.values())
    assert len(ledger0) == 4 and _total(ledger0) == pytest.approx(0.06)  # 2 imports x 2 calls
    assert {rid for rid, _c in ledger0.values()} == set(ids)
    with pytest.raises(state.StateSyncError, match="branch moved"):
        state.push(root, remote)
    paid_before = len(model.calls)

    replay_model = PaidModel()
    res = state.pull(root, remote, make_pipeline=lambda: _paid_pipeline(
        root.parent, replay_model))
    text = "\n".join(res.lines)
    assert "carried 2 run(s) the branch lacks" in text
    assert "every record of the replaced registry and of the branch kept once" in text
    assert replay_model.calls == [] and len(model.calls) == paid_before  # the replay paid $0

    after = Store(root / "registry.db")
    # the SPEND: every paid call, its run id and its cost — unchanged, none twice
    assert after.paid_ledger() == ledger0 and _total(after.paid_ledger()) == _total(ledger0)
    # the ORIGINAL runs: same ids, times and costs; kept for their record
    for rid in ids:
        r = after.run(rid)
        assert r is not None and r.ledger_only and r.started_at == runs0[rid].started_at
        assert r.cost_usd == runs0[rid].cost_usd and r.finished_at == runs0[rid].finished_at
    [replay] = [r for r in after.runs() if r.replay_of]
    assert replay.replay_of == tuple(sorted(ids)) and replay.cost_usd == 0
    assert not replay.ledger_only
    # the EVIDENCE once — not merged with a second copy; the INGESTION dates the originals
    for d in after.documents():
        assert d.received_at == docs0[d.doc_id].received_at and d.run_id == replay.run_id
    for a in after.articles():
        if a.article_id in arts0:
            assert a.first_seen_at == arts0[a.article_id].first_seen_at
    for t in after.theses():
        assert t.created_at == theses0[t.thesis_id].created_at
    assert _evidence(after, uploaded) == evidence0  # the same claims and links, never doubled
    after.close()

    state.push(root, remote)  # now a fast-forward
    fresh = tmp_path / "fresh" / "ti"
    state.pull(fresh, remote)
    restored = Store(fresh / "registry.db")
    assert restored.paid_ledger() == ledger0  # a fresh restore holds the same spend
    assert {r.run_id for r in restored.runs() if r.ledger_only} == set(ids)
    restored.close()
    again = state.pull(root, remote)  # a second pull: nothing local-only, nothing carried
    assert not any(ln.startswith("carried") for ln in again.lines)
    assert Store(root / "registry.db").paid_ledger() == ledger0


def test_the_weekly_report_counts_the_replay_once_never_the_carried_runs(
        tmp_path: Path) -> None:
    """The imports happen AFTER the branch's latest scan, so the carried originals fall inside
    the next week's window: only the replay — which holds their evidence — may count."""
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    root = tmp_path / "laptop" / "ti"
    state.pull(root, remote)
    _scan(actions, "week-2")
    state.push(actions.paths.root, remote)  # the branch moves on BEFORE the laptop imports
    laptop = _paid_pipeline(tmp_path / "laptop", PaidModel())
    ids = [_import(laptop, MS_PDF), _import(laptop, _old_note(tmp_path))]
    laptop.store.close()
    state.pull(root, remote, make_pipeline=lambda: _paid_pipeline(root.parent, PaidModel()))
    pipe = make_pipeline(root.parent)
    scan = _scan(pipe, "week-3")
    run = pipe.store.run(scan)
    assert run is not None
    covered = [r.run_id for r in report_runs(pipe.store, run)]
    assert not set(ids) & set(covered)  # the carried originals hold no evidence here
    [replay] = [r.run_id for r in pipe.store.runs() if r.replay_of]
    assert replay in covered
    d = build_dashboard(pipe.store, scan, cards={}, generated="t")
    manual = d.intake["manual"]["items"]
    assert len(manual) == 2  # each upload once


def test_pulling_twice_before_pushing_carries_no_zero_cost_replay(tmp_path: Path) -> None:
    remote, root, _model, ids = _laptop_with_two_paid_imports(tmp_path)
    ledger0 = Store(root / "registry.db").paid_ledger()
    for _ in range(2):
        state.pull(root, remote, make_pipeline=lambda: _paid_pipeline(root.parent, PaidModel()))
    st = Store(root / "registry.db")
    assert st.paid_ledger() == ledger0
    replays = [r for r in st.runs() if r.replay_of]
    assert len(replays) == 1 and replays[0].replay_of == tuple(sorted(ids))  # back to originals
    assert {r.run_id for r in st.runs() if r.ledger_only} == set(ids)


def test_a_forced_pull_keeps_the_record_of_a_run_it_discards(tmp_path: Path) -> None:
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    root = tmp_path / "laptop" / "ti"
    state.pull(root, remote)
    laptop = _paid_pipeline(tmp_path / "laptop", PaidModel())
    rid = _import(laptop, MS_PDF)
    st0 = laptop.store
    with st0.tx():  # make it a local run a pull cannot replay (not a document import)
        st0.conn.execute("DELETE FROM documents")
        r = st0.run(rid)
        assert r is not None
        st0.upsert_run(r.model_copy(update={"mode": "article"}))
    ledger0 = st0.paid_ledger()
    st0.close()
    _scan(actions, "week-2")
    state.push(actions.paths.root, remote)
    with pytest.raises(state.StateSyncError, match="cannot replay"):
        state.pull(root, remote)
    res = state.pull(root, remote, force=True)
    st = Store(root / "registry.db")
    assert st.paid_ledger() == ledger0 and _total(ledger0) == pytest.approx(0.03)
    kept = st.run(rid)
    assert kept is not None and "forced state pull" in kept.ledger_only
    assert any(rid in ln for ln in res.lines)
    st.close()
    state.pull(root, remote)  # a run carried for its record never blocks a later pull
    assert Store(root / "registry.db").paid_ledger() == ledger0


def test_two_runs_sharing_an_id_are_refused_before_anything_changes(tmp_path: Path) -> None:
    remote, root, _model, ids = _laptop_with_two_paid_imports(tmp_path)
    st = Store(root / "registry.db")
    r = st.run(ids[0])
    assert r is not None
    st.close()
    # the branch gets a DIFFERENT run under the same id (a second-resolution id can repeat)
    actions = make_pipeline(Path(re.sub(r"/laptop/ti$", "/actions", str(root))))
    clone = actions.start_run("ingest", as_of=AS_OF, run_id=ids[0])
    assert clone.started_at != r.started_at
    actions.finish_run(RunStatus.SUCCEEDED)
    state.push(actions.paths.root, remote)
    db_before = (root / "registry.db").read_bytes()
    with pytest.raises(state.StateSyncError, match="name one run here and another"):
        state.pull(root, remote)
    assert (root / "registry.db").read_bytes() == db_before  # untouched
    # forced: the clashing run is not carried — said, with its cost; the other one is
    res = state.pull(root, remote, force=True)
    text = "\n".join(res.lines)
    assert f"NOT carried: {ids[0]}" in text and "2 paid call(s), $0.0300" in text
    assert "except the 2 of the run(s) not carried below" in text
    st2 = Store(root / "registry.db")
    kept = st2.run(ids[1])
    assert kept is not None and kept.ledger_only  # the other import is carried
    assert st2.run(ids[0]) is not None and not st2.run(ids[0]).ledger_only  # the branch's own


def test_a_ledger_that_does_not_reconcile_fails_loud(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    remote, root, _model, _ids = _laptop_with_two_paid_imports(tmp_path)
    real = state._carry

    def drops_calls(new: Store, carried: Any, forced: set[str]) -> list[str]:
        return real(new, [(r, []) for r, _rows in carried], forced)

    monkeypatch.setattr(state, "_carry", drops_calls)
    with pytest.raises(state.StateSyncError, match="does not reconcile"):
        state.pull(root, remote)


def test_a_carried_scan_never_bounds_the_week_nor_stands_for_a_channels_latest_scan(
        tmp_path: Path) -> None:
    """A scan carried by a forced pull holds none of its evidence or candidates: the weekly
    report's window starts at the previous REAL scan, and health reads the latest real scan."""
    from vinci.theme_intelligence.health import _scan_stats
    from vinci.theme_intelligence.schemas import SourceCoverage

    pipe = make_pipeline(tmp_path)
    cov = [SourceCoverage(source_id="jpm_tmt", publisher="J.P. Morgan", channel="c",
                          method="m", checked_at=None, status="OK", discovered=3)]
    real = pipe.start_run("scan", as_of=AS_OF)
    real.sources = cov
    pipe.finish_run(RunStatus.SUCCEEDED)
    manual = pipe.start_run("ingest", as_of=AS_OF)
    pipe.finish_run(RunStatus.SUCCEEDED)
    carried = pipe.start_run("scan", as_of=AS_OF)
    carried.sources = cov
    done_carried = pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.store.upsert_run(done_carried.model_copy(update={"ledger_only": "carried (test)"}))
    week = pipe.start_run("scan", as_of=AS_OF)
    week.sources = cov
    done = pipe.finish_run(RunStatus.SUCCEEDED)
    assert manual.run_id in [r.run_id for r in report_runs(pipe.store, done)]
    pipe.store.upsert_run(done.model_copy(update={"finished_at": None}))  # leave the two
    assert _scan_stats(pipe.store, "jpm_tmt")["run_id"] == real.run_id
