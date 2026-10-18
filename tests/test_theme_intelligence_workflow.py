"""The weekly theme-intelligence workflow: manual trigger only, state never on main.

A text lint, like `test_scheduled_workflows.py` (no YAML parser for a file we author ourselves).
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "theme-intelligence-weekly.yml"
WRAPPER = ROOT / "bin" / "theme-intelligence-weekly"


def _code_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def _timers(text: str) -> list[str]:
    """Every line of `text` that would start the job without a person: a schedule or a cron."""
    return [ln for ln in _code_lines(text) if ln.startswith(("schedule:", "- cron:"))
            or "vars.THEME_INTELLIGENCE_SCHEDULE_ENABLED" in ln]


def test_the_weekly_run_is_started_by_hand_only() -> None:
    """The operator's ruling (2026-10-16): the weekly run is MANUAL, as weekly-screen.yml is — it
    had a Monday cron gated by a repository variable. NEGATIVE pin: the check finds the old one."""
    text = WF.read_text()
    assert _timers(text) == []
    assert any(ln.startswith("workflow_dispatch:") for ln in _code_lines(text))
    old = ('on:\n  schedule:\n    - cron: "0 3 * * 1"\n  workflow_dispatch:\njobs:\n  scan:\n'
           "    if: github.event_name == 'workflow_dispatch' || "
           "vars.THEME_INTELLIGENCE_SCHEDULE_ENABLED == 'true'\n")
    assert len(_timers(old)) == 3


def test_it_pushes_only_to_the_state_branch_after_the_gate() -> None:
    lines = _code_lines(WF.read_text())
    pushes = [ln for ln in lines if ln.startswith("git push")]
    assert pushes == ["git push origin HEAD:theme-intelligence-state"]  # never main
    assert lines.index(next(ln for ln in lines if ln.startswith("python -m pytest"))) < \
        lines.index(pushes[0])
    assert not any("data/theme_intelligence/http_cache" in ln for ln in lines)  # no page text


def test_a_failed_scan_is_still_recorded_and_still_fails_the_job() -> None:
    text = WF.read_text()
    assert "if: always()" in text  # the run record + readout are committed even on failure
    assert "steps.scan.outputs.code != '0' && steps.scan.outputs.code != '2'" in text


def test_the_local_wrapper_runs_the_same_pipeline() -> None:
    src = WRAPPER.read_text()
    assert src.startswith("#!/usr/bin/env bash")
    assert "-m vinci.theme_intelligence scan" in src and "-m vinci.theme_intelligence qa" in src
    assert "-m vinci.theme_intelligence backup" in src
    assert WRAPPER.stat().st_mode & 0o111  # executable


def test_the_state_branch_is_never_pushed_after_a_failed_restore() -> None:
    """A restore that fails (a state branch exported by newer code: the import raises after the
    database was created) leaves an EMPTY registry here; exporting and pushing it would make an
    empty registry the head of the registry of record. The commit runs only after the restore
    succeeded — a failed SCAN is still committed. NEGATIVE pin: the condition is not plain
    `always()`."""
    lines = _code_lines(WF.read_text())
    restore = lines.index("- name: Restore the durable registry from the state branch")
    assert lines[restore + 1] == "id: restore"
    commit = lines.index("- name: Commit the registry and this run's readout to the state branch")
    assert lines[commit + 1] == "if: always() && steps.restore.outcome == 'success'"
