"""ONE STEP for a weekly upload (follow-up A of the research desk record, 2026-10-13; built
2026-10-21): a cache-only pull, a read-only preflight, the import within a stated budget, QA,
the paid-call ledger reconciled, a fast-forward push — and a refusal at any step pushes nothing.

Before: an upload was four commands run by hand (`state pull`, `ingest-file`, inspect, `state
push`), any of which could pay implicitly — a `--cache-only` rehearsal printed "$0" while it
skipped what the paid merge then spent $4.81 on (2026-10-21) — and nothing reconciled the spend
before the push.

The remote is a LOCAL bare git repository standing in for GitHub. The model is an OFFLINE fake
answering through the real spend guard and the real content-addressed cache (no network, no
paid call: its "cost" is the guard's arithmetic on fake token counts). The document is the
SYNTHETIC Morgan Stanley fixture (tests/fixtures/theme_intelligence/synthetic_documents).
"""

from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_long_articles import _listed
from tests.test_theme_intelligence_state_sync import AS_OF, MS_PDF, _ms_ext, _offline, _scan
from tests.theme_intelligence_support import make_pipeline
from vinci.theme_intelligence import state
from vinci.theme_intelligence import upload as up
from vinci.theme_intelligence.__main__ import main
from vinci.theme_intelligence.budget import GuardedClient
from vinci.theme_intelligence.config import Paths
from vinci.theme_intelligence.documents import Declared, read_document
from vinci.theme_intelligence.ingest import estimate_cost
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.qa import QaCheck, QaResult
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.upload import UploadError, upload

__all__ = ["_offline"]  # the state tests' guard against live network requests, applied here

_SID = re.compile(r"^\[(s\d\d\.\w+)\] \(", re.M)


class FakeModel:
    """Answers the extraction with the fixture, the completeness pass by judging every listed gap
    immaterial, and the card review SUPPORTED — each call at 1,000 in / 400 out tokens."""

    model = "claude-opus-4-8"

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_kw: Any) -> dict[str, Any]:
        self.last_usage = {"input_tokens": 1000, "output_tokens": 400}
        self.calls.append(tool["name"])
        if tool["name"] == "record_article_evidence":
            return _ms_ext()
        if tool["name"] == "record_review":
            return {"verdicts": [{"sentence_id": sid, "verdict": "SUPPORTED", "problem": "",
                                  "better_claim_ids": []} for sid in _SID.findall(user)]}
        gaps = _listed(user)
        return {"figure_reviews": [{"figure_id": g, "verdict": "immaterial", "claim_ids": [],
                                    "reason": "test: not material"} for g in sorted(gaps)
                                   if "#" in g],
                "block_reviews": [{"block_id": g, "verdict": "immaterial", "hypothesis_ids": [],
                                   "claim_ids": [], "reason": "test: not material"}
                                  for g in sorted(gaps) if "#" not in g],
                "added_claims": [], "added_mentions": [], "hypothesis_additions": [],
                "added_hypotheses": [], "added_risks": []}


def _remote(tmp: Path) -> str:
    remote = str(tmp / "remote.git")
    subprocess.run(["git", "init", "--quiet", "--bare", remote], check=True)
    return remote


def _head(remote: str) -> str | None:
    return state.remote_head(remote)


def _actions(tmp: Path, remote: str) -> Pipeline:
    """The scheduled run's registry: one scan, pushed — the branch of record."""
    a = make_pipeline(tmp / "actions")
    _scan(a, "week-1")
    a.store.close()
    state.push(a.paths.root, remote)
    return a


def _factories(tmp: Path, model: FakeModel | None) -> dict[str, Any]:
    def pipe(client: FakeModel | None) -> Pipeline:  # as the CLI builds them: reviews ON
        p = make_pipeline(tmp / "laptop")
        p.client = GuardedClient(client, p.guard) if client is not None else None
        p.review = True
        return p
    return {"make_pipeline": lambda: pipe(model), "make_replay_pipeline": lambda: pipe(None)}


DECLARED = Declared(source_id="ms_research", llm_permitted=True,
                    authors=("Synthetic Analyst",))


def _budget() -> float:
    return float(math.ceil(estimate_cost(read_document(MS_PDF, DECLARED)).high) + 1)


def _upload(tmp: Path, remote: str, model: FakeModel | None, **kw: Any) -> up.UploadResult:
    return upload(tmp / "laptop" / "ti", remote, kw.pop("path", MS_PDF),
                  kw.pop("declared", DECLARED), budget=kw.pop("budget", _budget()), as_of=AS_OF,
                  **_factories(tmp, model), **kw)


def _laptop(tmp: Path) -> Store:
    return Store(Paths(tmp / "laptop" / "ti").db)


def test_one_step_pulls_imports_checks_reconciles_and_pushes(tmp_path: Path) -> None:
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    base = _head(remote)
    model = FakeModel()
    res = _upload(tmp_path, remote, model)
    assert res.outcome == "pushed" and res.status == "INGESTED"
    assert [x.split(" ")[0] for x in res.lines if re.match(r"^\d ", x)] == list("123456")
    # it paid, and only what the ledger shows: 1 extraction + completeness + reviews, priced
    assert "record_article_evidence" in model.calls and res.cost_usd and res.cost_usd > 0
    ledger = next(x for x in res.lines if x.startswith("5 ledger"))
    assert f"all the import's, ${res.cost_usd:.4f}" in ledger
    assert _head(remote) != base  # pushed, fast-forward
    # the scheduled side restores the branch and holds the upload, its paid calls with it
    back = tmp_path / "check" / "ti"
    state.pull(back, remote, replay=False)
    st = Store(Paths(back).db)
    [doc] = st.documents()
    assert doc.status == "INGESTED" and doc.filename == MS_PDF.name
    assert {rid for rid, _c in st.paid_ledger().values()} == {res.run_id}


def test_the_same_file_again_is_nothing_to_import_and_nothing_is_pushed(tmp_path: Path) -> None:
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    _upload(tmp_path, remote, FakeModel())
    head = _head(remote)
    again = FakeModel()
    res = _upload(tmp_path, remote, again)
    assert res.outcome == "nothing to push" and res.run_id is None
    assert any("the same file is on the registry as D-" in x for x in res.lines)
    assert again.calls == [] and _head(remote) == head


@pytest.mark.parametrize(("kw", "why"), [
    ({"budget": 0.01}, "does not cover the high end"),
    ({"declared": Declared(source_id="ms_research", authors=("A",))},
     "licence: not stated for this file"),
    ({"declared": Declared(source_id="ms_research", llm_permitted=False, authors=("A",))},
     "licence: the operator states third-party LLM processing is NOT permitted"),
    ({"declared": Declared(source_id="no_such_channel", llm_permitted=True)},
     "'no_such_channel' is not an active channel"),
    ({"same_as": "A-000000000000"}, "--same-as A-000000000000: no such article"),
    ({"budget": 0.0}, "--budget must be a positive amount"),
])
def test_a_refused_preflight_writes_nothing_pays_nothing_pushes_nothing(
        tmp_path: Path, kw: dict[str, Any], why: str) -> None:
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    head = _head(remote)
    model = FakeModel()
    with pytest.raises(UploadError, match=re.escape(why)) as err:
        _upload(tmp_path, remote, model, **kw)
    assert err.value.step == "preflight"
    assert model.calls == [] and _head(remote) == head
    if Paths(tmp_path / "laptop" / "ti").db.exists():
        st = _laptop(tmp_path)
        assert st.documents() == [] and [r.mode for r in st.runs()] == ["scan"]


def test_the_same_text_in_another_file_is_nothing_to_import(tmp_path: Path) -> None:
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    _upload(tmp_path, remote, FakeModel())
    head = _head(remote)
    copy = tmp_path / "copy.pdf"
    copy.write_bytes(MS_PDF.read_bytes() + b"\n%% a trailing comment: another file, same text\n")
    model = FakeModel()
    res = _upload(tmp_path, remote, model, path=copy,  # no author stated: never asked for one
                  declared=Declared(source_id="ms_research", llm_permitted=True))
    assert res.outcome == "nothing to push" and model.calls == [] and _head(remote) == head
    assert any("the same text is already registered" in x for x in res.lines)


def test_an_uncertain_identity_is_the_operators_call(tmp_path: Path) -> None:
    """Another document of the same publisher under the held report's title, with other text: an
    uncertain match — refused at the preflight, never analysed (and paid for) on a guess."""
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    _upload(tmp_path, remote, FakeModel())
    head = _head(remote)
    note = tmp_path / "same-title.md"
    note.write_text("---\ntitle: Synthetic Utilities Note: AI Power Demand\ndate: 2026-10-01\n"
                    "author: Synthetic Analyst\n---\n\n[SYNTHETIC TEST FIXTURE — invented "
                    "content]\n\nTransformer lead times in the US stretched to 120 weeks in "
                    "2026 as utilities ordered ahead of data-centre load, in this invented note, "
                    "which exists only to test that a document sharing a held report's "
                    "publisher and title, but none of its text, is never merged with it or "
                    "analysed on a guess about which article it is.\n")
    model = FakeModel()
    with pytest.raises(UploadError, match="identity uncertain") as err:
        _upload(tmp_path, remote, model, path=note)
    assert err.value.step == "preflight" and "--same-as" in str(err.value)
    assert model.calls == [] and _head(remote) == head


def test_a_dry_run_stops_after_the_preflight(tmp_path: Path) -> None:
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    head = _head(remote)
    model = FakeModel()
    res = upload(tmp_path / "laptop" / "ti", remote, MS_PDF, DECLARED, budget=_budget(),
                 as_of=AS_OF, dry_run=True, **_factories(tmp_path, None))  # no model client
    assert res.outcome == "dry run"
    res = _upload(tmp_path, remote, model, dry_run=True)
    assert res.outcome == "dry run" and res.lines[-1].startswith("dry run — nothing imported")
    assert any(x.strip().startswith("cost: estimated $") for x in res.lines)
    # review of #775: the dry run names who the import will credit, and from where
    assert "author: Synthetic Analyst (stated by you)" in [x.strip() for x in res.lines]
    assert model.calls == [] and _head(remote) == head and _laptop(tmp_path).documents() == []


def test_a_replay_that_would_pay_stops_the_upload(tmp_path: Path) -> None:
    """A local import the branch lacks, whose answers are NOT in this machine's cache (it was
    analysed from a fixture): the cache-only pull cannot replay it, and the upload stops — a
    paid replay is a deliberate `state pull`, never a side effect."""
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    head = _head(remote)
    local = tmp_path / "laptop" / "ti"
    state.pull(local, remote)
    laptop = make_pipeline(tmp_path / "laptop")
    from tests.test_theme_intelligence_state_sync import _upload as fixture_upload

    fixture_upload(laptop, MS_PDF, _ms_ext())  # not pushed, no cached answers
    laptop.store.close()
    model = FakeModel()
    with pytest.raises(UploadError, match="could not be replayed from the cache") as err:
        _upload(tmp_path, remote, model)
    assert err.value.step == "pull" and model.calls == [] and _head(remote) == head


def test_a_replay_that_skips_a_paid_step_stops_the_upload(tmp_path: Path) -> None:
    """A local import made with the card review OFF: its extraction and completeness answers are
    cached, its review never was. The cache-only replay skips the review — a step a paid replay
    would run and bill — and the upload stops at the pull, naming it (lead (m), 2026-10-21: a
    rehearsal printed $0 while it skipped what the paid merge then spent $4.81 on)."""
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    head = _head(remote)
    state.pull(tmp_path / "laptop" / "ti", remote)
    laptop = make_pipeline(tmp_path / "laptop")  # reviews OFF
    laptop.client = GuardedClient(FakeModel(), laptop.guard)
    laptop.start_run("ingest", as_of=AS_OF)
    from vinci.theme_intelligence.ingest import ingest_file

    ingest_file(laptop, MS_PDF, DECLARED, as_of=AS_OF)
    laptop.finish_ingest(RunStatus.SUCCEEDED)
    laptop.store.close()  # not pushed
    model = FakeModel()
    with pytest.raises(UploadError, match=r"skipped R-\S+: 0 completeness pass\(es\), 1 card "
                                          r"review\(s\)") as err:
        _upload(tmp_path, remote, model, path=tmp_path / "unused.pdf")
    assert err.value.step == "pull" and model.calls == [] and _head(remote) == head


def test_a_moved_branch_refuses_the_push_and_the_rerun_carries_it_at_no_cost(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    from vinci.theme_intelligence import ingest

    real = ingest.ingest_file

    def and_the_weekly_run_lands(*a: Any, **kw: Any) -> Any:
        out = real(*a, **kw)
        weekly = tmp_path / "weekly"
        state.pull(weekly / "ti", remote, replay=False)
        w = make_pipeline(weekly)
        _scan(w, "week-2")
        w.store.close()
        state.push(w.paths.root, remote)
        return out

    monkeypatch.setattr(ingest, "ingest_file", and_the_weekly_run_lands)
    model = FakeModel()
    with pytest.raises(UploadError, match="the branch moved") as err:
        _upload(tmp_path, remote, model)
    assert err.value.step == "push"
    paid = _laptop(tmp_path).paid_ledger()
    assert paid and len(model.calls) == len(paid)
    monkeypatch.undo()
    rerun = FakeModel()
    res = _upload(tmp_path, remote, rerun)
    assert rerun.calls == []  # the replay read every answer from the cache
    assert res.outcome == "pushed" and res.run_id is None  # nothing imported: it was held
    back = tmp_path / "check" / "ti"
    state.pull(back, remote, replay=False)
    st = Store(Paths(back).db)
    assert [d.filename for d in st.documents()] == [MS_PDF.name]
    assert st.paid_ledger() == paid  # the paid calls crossed once, unchanged


def test_an_integrity_failure_stops_the_push(tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    """QA's verdict on the import, failing one integrity check (the real result type): nothing
    is pushed, and the paid import stays in the local registry."""
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    head = _head(remote)

    def broken(_store: Store, run_id: str) -> QaResult:
        return QaResult(run_id, [QaCheck("version content hashes recompute", False, "1 differs"),
                                 QaCheck("every argument block accounted for", False, "OPEN",
                                         research=True)])

    monkeypatch.setattr(up, "run_qa", broken)
    with pytest.raises(UploadError, match="version content hashes recompute — 1 differs") as err:
        _upload(tmp_path, remote, FakeModel())
    assert err.value.step == "qa" and _head(remote) == head
    assert "every argument block" not in str(err.value)  # open research is never a failure
    assert _laptop(tmp_path).documents()  # the paid import kept locally, never dropped


def test_a_document_with_no_author_is_asked_for_one_before_anything_is_paid(
        tmp_path: Path) -> None:
    """The synthetic report names no author and none is stated. QA's integrity check needs one,
    and the model credits one from the text only sometimes (3 of the registry's 9 uploads stayed
    without, 2026-10-21): refused at the preflight, before a cent is spent."""
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    model = FakeModel()
    with pytest.raises(UploadError, match="names no author .* --author NAME") as err:
        _upload(tmp_path, remote, model,
                declared=Declared(source_id="ms_research", llm_permitted=True))
    assert err.value.step == "preflight" and model.calls == []


def test_a_paid_call_outside_the_import_stops_the_push(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    head = _head(remote)
    from vinci.theme_intelligence import ingest

    real = ingest.ingest_file

    def and_another_bill(pipe: Pipeline, *a: Any, **kw: Any) -> Any:
        out = real(pipe, *a, **kw)
        pipe.store.add_llm_call("call-elsewhere", "R-some-other-run", "extract",
                                {"cached": False, "cost_usd": 0.5})
        return out

    monkeypatch.setattr(ingest, "ingest_file", and_another_bill)
    with pytest.raises(UploadError, match="1 new call\\(s\\) not the import's") as err:
        _upload(tmp_path, remote, FakeModel())
    assert err.value.step == "ledger" and _head(remote) == head


@pytest.mark.parametrize(("before", "after", "cost", "why"), [
    ({"a": ("R1", 0.1)}, {"a": ("R1", 0.2)}, 0.0, "1 earlier call(s) changed or missing"),
    ({"a": ("R1", 0.1)}, {}, 0.0, "1 earlier call(s) changed or missing"),
    ({}, {"b": ("RUN", None)}, None, "without a price — cost UNKNOWN"),
    ({}, {"b": ("RUN", 0.3)}, 0.2, "the new calls sum to $0.3000, the run records $0.2000"),
    ({}, {"b": ("RUN", 3.0)}, 3.0, "$3.0000 spent against a $2.00 budget"),
])
def test_the_ledger_reconciliation_refuses(before: dict[str, tuple[str, float | None]],
                                           after: dict[str, tuple[str, float | None]],
                                           cost: float | None, why: str) -> None:
    with pytest.raises(UploadError, match=re.escape(why)):
        up._reconcile(before, after, "RUN", cost, 2.0)
    assert "1 new, all the import's, $0.3000" in up._reconcile(
        {"a": ("R1", 0.1)}, {"a": ("R1", 0.1), "b": ("RUN", 0.3)}, "RUN", 0.3, 2.0)


def test_a_new_version_of_an_article_whose_authors_are_held_needs_none_stated(
        tmp_path: Path) -> None:
    """Review of #769: the author gate read only the new file, so a fuller version of an article
    whose authors the registry holds was refused — though it keeps them (ingest._as_version_of)
    and QA would pass. And the gate ran before the identity check (pinned above: a copy of a
    held text is nothing to import, author or not)."""
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    _upload(tmp_path, remote, FakeModel())  # held, its author stated
    st = _laptop(tmp_path)
    [doc] = st.documents()
    art = st.article(doc.article_id or "")
    assert art is not None and art.authors
    st.close()
    fuller = tmp_path / "fuller.md"
    fuller.write_text("---\ntitle: Synthetic Utilities Note: AI Power Demand (full)\n"
                      "date: 2026-10-01\n---\n\n[SYNTHETIC TEST FIXTURE — invented content]\n\n"
                      + " ".join(["On-site gas turbine orders are projected to grow 30% in 2027 "
                                  "as AI load outruns the grid, in this invented note."] * 6)
                      + "\n")
    unauthored = Declared(source_id="ms_research", llm_permitted=True)
    res = _upload(tmp_path, remote, None, path=fuller, declared=unauthored,
                  same_as=art.article_id, dry_run=True)
    assert res.outcome == "dry run"
    assert any(f"a version of {art.article_id}" in x for x in res.lines)
    assert [x.strip() for x in res.lines if x.strip().startswith("author:")] == [
        "author: " + "; ".join(f"{a.name} (kept from {art.article_id})" for a in art.authors)]
    with pytest.raises(UploadError, match="names no author"):  # a NEW article still needs one
        _upload(tmp_path, remote, None, path=fuller, declared=unauthored, as_new=True,
                dry_run=True)


def test_a_refusal_says_what_the_upload_did_before_it(
        tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Review of #769: a refusal printed only its reason — the pull's backup path, the replay and
    the import's cost were lost with it."""
    remote = _remote(tmp_path)
    _actions(tmp_path, remote)
    _upload(tmp_path, remote, FakeModel())  # a local registry exists: the next pull backs it up
    with pytest.raises(UploadError) as err:
        _upload(tmp_path, remote, FakeModel(), budget=0.01, path=tmp_path / "x.md")
    assert err.value.lines[0] == "1 pull (cache-only):"
    assert any("local registry backed up to" in x for x in err.value.lines)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    note = tmp_path / "new.md"
    note.write_text("---\ntitle: Another Synthetic Note\ndate: 2026-10-01\nauthor: A\n---\n\n"
                    + " ".join(["Invented sentence about grid queues for this test only."] * 8)
                    + "\n")
    code = main(["--data-dir", str(tmp_path / "laptop" / "ti"), "upload", "--remote", remote,
                 "--path", str(note), "--source", "ms_research", "--budget", "0.01",
                 "--llm-permitted"])
    out = capsys.readouterr().out
    assert code == 1
    assert out.index("1 pull (cache-only):") < out.index("upload refused at preflight: cost")
    assert "local registry backed up to" in out
