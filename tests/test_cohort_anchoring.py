"""THE ANCHORING FALSIFIER MUST STAY ABLE TO FAIL, AND MUST NOT PASS ON NOISE.

#501 proved the cohort split never reaches the sort key. It did NOT prove the split fails to steer
WHICH names a human works — a `name-specific` / `industry-wide` pill sits on the queue read before
any CIQ pull, and if `industry-wide` names stop being worked the split is a screen whatever the
sort key does.

These pins protect the two properties that make the falsifier worth having: it can FIRE, and it
refuses to report a pass it cannot support. The second is not hypothetical — the first cut reported
"within tolerance" on a band holding one worked name out of twenty-nine.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cohort_anchoring_falsifier.py"


def _run() -> str:
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=ROOT,
                       env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr[-400:]
    return r.stdout


def test_it_refuses_to_pass_on_a_band_with_almost_nothing_worked() -> None:
    """A RATE NEEDS A NUMERATOR. Arm SIZE says how many names COULD have been worked; it says
    nothing about how many were. Reporting "within tolerance" off one worked name reads as
    reassurance and is worse than no answer, because it would have sat there for months while
    nothing was actually measured."""
    out = _run()
    src = SCRIPT.read_text()
    assert "MIN_WORKED_IN_BAND" in src, "the worked-count floor is gone — arm size alone can pass"
    for line in out.splitlines():
        if re.match(r"\s+\d+-\d+\s", line) and "not yet testable" not in line:
            nums = re.findall(r"(\d+)/(\d+)", line)
            worked = sum(int(a) for a, _ in nums)
            assert worked >= 5, (
                f"a band was judged on {worked} worked name(s): {line.strip()}")


def test_the_falsifier_can_actually_fire() -> None:
    """A FALSIFIER THAT CANNOT FAIL IS DECORATION. Simulated here rather than asserted: a human who
    works ONLY `own` names in one band must produce a FIRED verdict. If a future change to the
    thresholds or the bands makes that impossible, this reddens."""
    queue = ROOT / "data" / "snapshots" / "ranked_queue.jsonl"
    if not queue.is_file():
        pytest.skip("no committed queue")
    rows = [json.loads(x) for x in queue.read_text().splitlines() if x.strip()]
    band = [r for r in rows if 101 <= r.get("rank", 0) <= 200
            and (r.get("cohort") or {}).get("call") == "own"]
    if len(band) < 12:
        pytest.skip("the live queue no longer has enough `own` names in the 101-200 band")
    made = []
    try:
        for r in band[:12]:
            d = ROOT / "data" / "dossiers" / r["ticker"]
            if (d / "dossier.json").exists():
                continue
            d.mkdir(parents=True, exist_ok=True)
            (d / "dossier.json").write_text("{}")
            made.append(d)
        out = _run()
        assert "FIRED" in out and "FALSIFIED in" in out, (
            "a human working only `own` names did NOT trip the falsifier — it cannot detect the "
            "behaviour it exists to detect:\n" + out)
    finally:
        for d in made:
            shutil.rmtree(d, ignore_errors=True)


def test_the_threshold_and_its_control_are_stated_where_they_are_set() -> None:
    """PRE-REGISTERED MEANS WRITTEN DOWN BEFORE THE DATA. The number and the confound it controls
    for must live at the constant, not only in a record — a threshold whose reasoning is one file
    away is a threshold someone tunes."""
    # WHITESPACE-NORMALISED, because the source is wrapped at 100 columns and the phrases this
    # checks for straddle line breaks ("face\nvalidity", "median rank\nown=110"). A raw `in`
    # reported both as absent — the same wrapped-text trap that made an earlier mutation a silent
    # no-op. Compare on the prose, not on where the lines happen to end.
    src = re.sub(r"\s+", " ", SCRIPT.read_text().replace("#:", " ").replace("#", " "))
    assert "DIVERGENCE_POINTS" in SCRIPT.read_text()
    assert "face validity" in src, "the threshold does not say it was set on face validity"
    assert "median rank own=110 vs cohort=172" in src, (
        "the measured confound is no longer stated at the point the control is applied")


def test_the_accepted_risk_is_recorded_with_its_falsifier() -> None:
    """CLAUDE.md's INVARIANT RULE: an incident closes with a machine check OR is recorded as
    consciously accepted risk WITH its falsifier. This is the second kind."""
    state = (ROOT / "STATE.md").read_text()
    assert "ANCHORING THE HUMAN" in state, "the accepted risk is not in STATE.md"
    block = state.split("ANCHORING THE HUMAN", 1)[1][:900]
    assert "cohort_anchoring_falsifier" in block, "the risk names no harness"
    assert "20-point" in block or "20 point" in block, "the risk records no falsifier threshold"


def test_the_test_is_two_sided_because_the_pre_registration_is() -> None:
    """STEERING IS STEERING WHICHEVER WAY IT RUNS (review, #509).

    The pre-registered falsifier says the worked-rate "differs between `own` and `cohort`" — and
    the first cut tested `gap > threshold`, so a 35-point gap the OTHER way (a human preferentially
    working industry-driven names) would have reported "within tolerance". A one-sided test against
    a two-sided pre-registration is the code quietly narrowing the claim it exists to check, and it
    would have read as a pass forever in that scenario.

    Pinned on the SOURCE because the live corpus cannot produce a negative gap yet — there is not
    enough worked data for any band to be testable at all, so a behavioural pin would be vacuous
    and would go green whatever the comparison said."""
    src = SCRIPT.read_text()
    assert "abs(gap) > DIVERGENCE_POINTS" in src, (
        "the divergence test is not two-sided — a gap favouring `cohort` would report 'within "
        "tolerance' against a pre-registration that says 'differs'")
    assert "gap > DIVERGENCE_POINTS" not in src.replace("abs(gap) > DIVERGENCE_POINTS", ""), (
        "a one-sided comparison survives somewhere in the script")

