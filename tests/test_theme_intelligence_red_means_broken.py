"""Red means broken; a replay says what it skipped (operator, 2026-10-21: leads (l) and (m)).

(l) One restated figure the reading could not verify turned the weekly job red (2026-10-21, run
39565710165: QA 21/22, "'36%' [capture_not_verified]"), and a quarter of the locally tested
articles carried such an open figure — so red would stop meaning broken. Research left OPEN is
now said (exit 3, a warning), and the job fails only on an integrity check.

(m) A cache-only replay printed "every model answer from the cache, $0" while it skipped the
completeness pass and the card reviews it held no answer for (the one-registry rehearsal read $0
where the paid merge spent $4.81). It now names what it did not run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from tests.test_theme_intelligence_open_leads import _insert_version, _jpm_run
from tests.test_theme_intelligence_state_sync import MS_PDF, _bare, _ms_ext, _scan, _upload
from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import state
from vinci.theme_intelligence.__main__ import QA_RESEARCH_OPEN, cmd_qa
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import RunStatus

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "theme-intelligence-weekly.yml"
LOCAL = ROOT / "bin" / "theme-intelligence-weekly"
AS_OF = date(2026, 10, 12)
LINE = "Memory suppliers raised HBM contract prices 12% in 3Q26 while DRAM output fell 7%."
#: an argument paragraph no claim anchors and no account covers — an open argument block
ARGUMENT = ("We expect the shortage to persist through the next upgrade cycle because suppliers "
            "are adding capacity far more slowly than hyperscalers are adding demand.")


def _open_figure_run(tmp_path: Path, *, pass_runs: bool = True) -> tuple[Any, str]:
    """A run whose reading leaves one stated figure open ("7%": no claim, no account of it) and
    one argument paragraph unaccounted for."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("qa-open", "Test Publisher", date(2026, 10, 6),
               [("paragraph", LINE), ("paragraph", ARGUMENT)])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", "Memory suppliers raised HBM contract prices 12% in 3Q26",
               "HBM prices up", metric="price change", value=12, value_text="12%", unit="%",
               period="3Q26")],
        [hyp("h1", "HBM contract prices rise", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", geography="US", supporting=["c1"])]),
        as_of=AS_OF, publisher=art.publisher,
        completeness={"figure_reviews": [], "block_reviews": []} if pass_runs else None)
    rid = pipe.finish_run(RunStatus.SUCCEEDED).run_id
    write_run_outputs(pipe.store, rid, None)  # rendered, as `ingest-file` renders every run
    return pipe, rid


def _qa_exit(pipe: Any, run_id: str, capsys: Any) -> tuple[int, str]:
    code = cmd_qa(argparse.Namespace(data_dir=str(pipe.paths.root), run=run_id))
    return code, capsys.readouterr().out


def test_open_research_is_said_and_never_fails_the_run(tmp_path: Path, capsys: Any) -> None:
    """END TO END through the CLI the weekly job runs: an open figure prints OPEN, never FAIL,
    and `qa` exits 3 — the job's warning — not 1."""
    pipe, rid = _open_figure_run(tmp_path)
    res = run_qa(pipe.store, rid)
    assert res.ok and [c.name for c in res.open_research] == [
        "every reported figure captured or judged immaterial",
        "every argument block accounted for"]
    failing = [c.name for c in res.checks if not c.ok and not c.research]
    assert not failing, failing
    code, out = _qa_exit(pipe, rid, capsys)
    assert code == QA_RESEARCH_OPEN == 3
    assert "[OPEN] every reported figure captured or judged immaterial" in out
    assert "[OPEN] every argument block accounted for" in out
    assert "'7%'" in out and "[FAIL]" not in out
    assert "[PASS] the completeness pass ran for every analysed article" in out


def test_a_completeness_pass_that_never_ran_is_broken_not_open(
        tmp_path: Path, capsys: Any) -> None:
    """The review of #765: with no model and no saved answer the completeness pass does not run,
    leaving every figure and argument open. That is the machine not doing its job — a FAIL and
    exit 1 — never research left open (it would have passed green as a warning)."""
    pipe, rid = _open_figure_run(tmp_path, pass_runs=False)
    res = run_qa(pipe.store, rid)
    assert not res.ok
    code, out = _qa_exit(pipe, rid, capsys)
    assert code == 1 and "[FAIL] the completeness pass ran for every analysed article" in out
    assert "[pass_not_run]" in out  # the open figures still say why they are open


def test_a_broken_record_still_fails_the_run(tmp_path: Path, capsys: Any) -> None:
    """NEGATIVE: an integrity failure (stored content that no longer matches its hash) is a FAIL
    and exit 1, open research or not."""
    pipe, rid = _jpm_run(tmp_path)
    th = pipe.store.theses()[0]
    payload = json.loads(pipe.store.conn.execute(
        "SELECT payload FROM thesis_versions WHERE thesis_id=? AND version=1",
        (th.thesis_id,)).fetchone()[0])
    content = payload["content"]
    content["header"]["title"] += " (edited)"
    _insert_version(pipe, th.thesis_id, content, payload["content_sha"])
    assert not run_qa(pipe.store, rid).ok
    code, out = _qa_exit(pipe, rid, capsys)
    assert code == 1 and "[FAIL] version content hashes recompute" in out


def _step(text: str, name: str) -> str:
    return next(s for s in re.split(r"\n(?=      - (?:name|uses):)", text) if name in s)


def test_the_weekly_job_warns_on_open_research_and_fails_only_when_broken() -> None:
    """The QA step maps exit 3 to a ::warning:: and success; any other non-zero stays a failure,
    which the last step turns red. The commit names the result."""
    text = WORKFLOW.read_text()
    qa = _step(text, "- name: QA the run's stored records")
    assert "continue-on-error: true" in qa and "::warning::research verification INCOMPLETE" in qa
    assert re.search(r"3\)\s+echo \"result=research-open\"", qa) and "code=0" in qa
    assert 'echo "result=failed"' in qa and "exit $code" in qa
    assert "steps.qa.outputs.result" in text
    fail = _step(text, "- name: Fail the job when the scan failed or QA did not pass")
    assert "steps.qa.outcome == 'failure'" in fail


def test_the_local_weekly_script_treats_open_research_as_a_warning() -> None:
    script = LOCAL.read_text()
    assert re.search(r'if \[ "\$qa" -eq 3 \]', script) and "INCOMPLETE" in script
    assert re.search(r'elif \[ "\$qa" -ne 0 \]; then\n\s+code=1', script)


def test_a_replay_says_what_it_did_not_run(tmp_path: Path) -> None:
    """(m), END TO END through `state.pull`: a replay with no model and reviews off names the
    completeness pass and the card review it skipped — never "every model answer from the
    cache"."""
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    root = tmp_path / "laptop" / "ti"
    state.pull(root, remote)
    laptop = make_pipeline(tmp_path / "laptop")
    _upload(laptop, MS_PDF, _ms_ext())
    laptop.store.close()
    _scan(actions, "week-2")
    state.push(actions.paths.root, remote)
    res = state.pull(root, remote, make_pipeline=lambda: make_pipeline(tmp_path / "laptop"),
                     fixtures={hashlib.sha256(MS_PDF.read_bytes()).hexdigest(): _ms_ext()})
    [line] = [x for x in res.lines if x.startswith("replay run")]
    assert "every model answer from the cache" not in line
    assert "— NOT run: the completeness pass for 1 document(s) and " in line
    assert "card review(s); a paid replay would run (and bill) them" in line


def test_a_replay_that_skipped_nothing_still_says_every_answer(
        tmp_path: Path, monkeypatch: Any) -> None:
    """NEGATIVE, END TO END: with nothing skipped, "every model answer from the cache" is true
    and is said; nothing is appended."""
    monkeypatch.setattr(state, "not_run", lambda _store, _rid: "")
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    root = tmp_path / "laptop" / "ti"
    state.pull(root, remote)
    laptop = make_pipeline(tmp_path / "laptop")
    _upload(laptop, MS_PDF, _ms_ext())
    laptop.store.close()
    _scan(actions, "week-2")
    state.push(actions.paths.root, remote)
    res = state.pull(root, remote, make_pipeline=lambda: make_pipeline(tmp_path / "laptop"),
                     fixtures={hashlib.sha256(MS_PDF.read_bytes()).hexdigest(): _ms_ext()})
    [line] = [x for x in res.lines if x.startswith("replay run")]
    assert line.endswith("every model answer from the cache, $0:") and "NOT run" not in line


def test_a_replay_that_skipped_nothing_says_nothing_more() -> None:
    """NEGATIVE: with nothing skipped the line adds nothing."""
    class _Store:
        def completeness_for_run(self, _rid: str) -> list[Any]:
            return []

        def issues(self, run_id: str | None = None) -> list[Any]:
            return []

    assert state.not_run(_Store(), "R-x") == ""  # type: ignore[arg-type]
