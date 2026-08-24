"""A FAILED RUN LEAVES A TRACE, AND THE QUEUE'S AGE IS VISIBLE WHERE IT IS READ.

THE BLIND SPOT (2026-08-03 → 08-24). The weekly screen failed four consecutive times and nothing
on the served surface said so. It could not: the frontend reads COMMITTED snapshots, a failed run
commits nothing, and therefore "the job died" and "nobody started one" render byte-identically.
The only trace was the Actions tab.

TWO SEPARATE FACTS, and conflating them is what made the outage invisible:
  * QUEUE AGE — how old the committed queue is. Derivable from the manifest, always was. A chip
    existed for it, on the ranker ONLY, so learning the queue was stale required opening the
    queue — the screen you are least likely to open during an outage, because it looks unchanged.
  * RUN OUTCOME — whether the last attempt worked. NOT derivable from committed data at all. It
    needs the job to report, which is why `weekly-screen.yml` gained an `if: always()` step that
    writes `run_status.json` past its own gate, deliberately and by name.

ABSENT IS UNKNOWN, NEVER PASS. A missing status is precisely the state the outage was in, so it
must never render as health.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _node(driver: str, *args: str) -> dict:
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    out = subprocess.run(["node", "--input-type=module", "-e", driver, *args],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout.strip().splitlines()[-1])


_FMT = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const m = await import(pathToFileURL(path.resolve("frontend/lib/format.js")).href);
const arg = JSON.parse(process.argv[1]);
console.log(JSON.stringify({
  chipFresh: m.queueAgeChip(arg.fresh),
  chipStale: m.queueAgeChip(arg.stale),
  chipNull: m.queueAgeChip(null),
  ageNull: m.queueAgeDays(null),
  healthMissing: m.runHealth(null),
  healthUnset: m.runHealth({ conclusion: null }),
  healthOk: m.runHealth({ conclusion: "success" }),
  healthFail: m.runHealth({ conclusion: "failure", remediation: "REMEDY-TEXT" }),
  staleDays: m.QUEUE_STALE_DAYS,
}));
"""


def _dates() -> dict[str, str]:
    import datetime as dt

    today = dt.date.today()
    return {"fresh": (today - dt.timedelta(days=1)).isoformat(),
            "stale": (today - dt.timedelta(days=30)).isoformat()}


def test_a_missing_run_status_reads_unknown_and_never_as_health() -> None:
    """THE STATE THE OUTAGE WAS IN. Until the job reports once there is no status at all, and the
    surface must say it cannot tell — a default of "OK" would restate the exact blind spot as
    reassurance."""
    r = _node(_FMT, json.dumps(_dates()))
    for missing in (r["healthMissing"], r["healthUnset"]):
        assert missing["label"] == "UNKNOWN"
        assert missing["tone"] == "unresolved"
        assert "cannot tell a failure from a run nobody started" in missing["detail"]


def test_a_failed_run_carries_its_remediation_not_just_its_verdict() -> None:
    """A red chip that does not say what to do sends the reader to the Actions tab, which is where
    the four weeks were lost. The remediation the job recorded is what renders."""
    r = _node(_FMT, json.dumps(_dates()))
    assert r["healthFail"]["label"] == "FAILED" and r["healthFail"]["tone"] == "avoid"
    assert r["healthFail"]["detail"] == "REMEDY-TEXT"
    assert r["healthOk"]["label"] == "OK" and r["healthOk"]["tone"] == "buy"


def test_the_age_chip_is_quiet_when_fresh_and_names_the_date_when_not() -> None:
    """It must add no furniture on a healthy queue, or it becomes noise nobody reads — which is how
    a real warning gets skipped."""
    r = _node(_FMT, json.dumps(_dates()))
    assert r["chipFresh"] == "" and r["chipNull"] == ""
    assert "queue is 30 days old" in r["chipStale"]
    assert r["staleDays"] == 10


def test_the_chip_no_longer_claims_a_missed_appointment() -> None:
    """WORDING, and it is a correctness point rather than a style one. The old text read "the
    weekly screen may not have run", which implies a schedule was missed. There is no schedule —
    the operator triggers it — so the honest statement is the queue's AGE plus how to run it."""
    r = _node(_FMT, json.dumps(_dates()))
    chip = r["chipStale"]
    assert "may not have run" not in chip, "the missed-appointment wording is back"
    assert "operator-triggered" in chip or "Run workflow" in chip, (
        "the chip must say how to run the screen, not merely that it is old")


# --- the three surfaces actually render it ------------------------------------------------------

def test_the_queue_age_reaches_the_home_screen_not_only_the_ranker() -> None:
    """THE PLACEMENT IS THE POINT. The chip already existed on the ranker; during an outage that is
    the screen you are least likely to open, because it looks unchanged. Both views must render the
    SHARED helper — a second copy is how the grade-bucket trio came to need a three-way parity pin.
    """
    fmt = (ROOT / "frontend" / "lib" / "format.js").read_text()
    assert "export function queueAgeChip" in fmt

    ranker = (ROOT / "frontend" / "views" / "edge2" / "ranker.js").read_text()
    overview = (ROOT / "frontend" / "views" / "shared" / "overview.js").read_text()
    # THE CALL, NOT THE IMPORT (caught by mutation): emptying the chip while leaving the import in
    # place passed an `in src` check, which is the pin-the-helper trap one level down. Each view
    # must invoke the helper WITH its own as-of, and interpolate the result.
    assert "queueAgeChip(DATA.asOf)" in ranker, "the ranker imports the chip but does not call it"
    assert "queueAgeChip(health.screen.asOf)" in overview, (
        "the overview imports the chip but does not call it with the screen as-of")
    assert "${ageChip}" in overview or "${statusStrip}" in overview, (
        "the overview computes the chip and never renders it")
    assert "function stalenessChip" not in ranker, (
        "the ranker still declares its own chip — one definition, imported")


def test_the_ops_dashboard_renders_run_health_and_the_command() -> None:
    """Run health belongs on the ingestion dashboard, which already says of itself that it is the
    freshness/health surface — not on the analysis screens. The home screen gets a one-line chip;
    the detail and the command live here."""
    src = (ROOT / "frontend" / "views" / "edge2" / "ingestion.js").read_text()
    assert "runHealth" in src and "Last weekly run" in src
    assert "vinci run-weekly" in src and "Run workflow" in src, (
        "the ops surface must name the command, not merely report the state")


# --- the pipe from the job to the page ----------------------------------------------------------

def test_the_manifest_carries_run_status_only_when_present() -> None:
    """THE PIPE, end to end on the real builder: `run_status.json` -> manifest -> the views. Folded
    into the manifest rather than mirrored as its own file, because the manifest is already fetched
    on every screen. OMITTED when absent, so a corpus that predates the reporting step renders
    UNKNOWN rather than gaining a wall of nulls."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_rv_build", ROOT / "frontend" / "build.py")
    assert spec and spec.loader
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)

    src = (ROOT / "frontend" / "build.py").read_text()
    assert '"run": json.loads((SNAP / "run_status.json").read_text())' in src
    assert '(SNAP / "run_status.json").exists()' in src, (
        "the run block must be conditional — absent status is UNKNOWN, not an empty object")

    # THE MIRROR IS GIT-IGNORED, so it does not exist on a fresh checkout — every CI run. The
    # first cut asserted against it unconditionally and passed locally while failing in CI: the
    # same passes-everywhere-except-where-it-matters shape as the outage this work exists for.
    # The CONTRACT is the conditional above, asserted always; the consistency check runs only
    # where a built mirror is present, and says so rather than pretending to have checked.
    mirror = ROOT / "frontend" / "snapshots" / "manifest.json"
    if not mirror.is_file():
        pytest.skip("frontend/snapshots is git-ignored and unbuilt here — source contract asserted")
    status_on_disk = (ROOT / "data" / "snapshots" / "run_status.json").exists()
    assert ("run" in json.loads(mirror.read_text())) == status_on_disk, (
        "the built manifest and the presence of run_status.json disagree — the mirror is stale")


def test_the_reporting_step_stages_only_the_status_file() -> None:
    """THE GATE EXCEPTION IS NARROW, AND THAT IS WHAT MAKES IT ALLOWABLE. The step runs
    `if: always()`, so on a RED run it executes after the gate refused — it must therefore be
    incapable of carrying anything else out with it. It stages `run_status.json` by name; a
    `git add data/snapshots` here would let a failed run push the half-built snapshots its own
    gate had just rejected."""
    wf = (ROOT / ".github" / "workflows" / "weekly-screen.yml").read_text()
    step = wf.split("Report the run's outcome", 1)[1]
    assert "if: always()" in step
    assert "git add data/snapshots/run_status.json" in step
    for forbidden in ("git add data/snapshots\n", "git add -A", "git add ."):
        assert forbidden not in step, (
            f"the reporting step stages more than the status file ({forbidden!r}) — a red run "
            f"could push artifacts the gate refused")
