"""A scheduled job that pushes to main is gated like every other commit to main.

THE INCIDENT (2026-08-10). The weekly screen pushed `607e7d1 weekly screen: refresh snapshots
[skip ci]`. Its new candidate snapshot moved NCNO out of the band and onto the MAINTENANCE route —
where a name needs COMMITTED price bars, because `data/vinci.db` is git-ignored and CI has no store.
NCNO had none, so five maintenance-path pins failed ON EVERY OPEN PR REGARDLESS OF ITS CONTENTS:
#393 was docs-only and went red identically to #394, both having passed forty minutes earlier.
Main's own last gate had run BEFORE the push and stayed green, which is what made the
misattribution so easy.

THE SKIPPED GATE WAS THE HOLE, NOT THE SNAPSHOT. The one commit that changes the fleet's ROUTING
was the one commit nothing gated, so the breakage landed on main invisibly and first surfaced on
the next unrelated PR — where it read as that PR's regression.

THERE IS NO SECOND GATE DOWNSTREAM (review finding, #456). A push authenticated with the workflow's
own GITHUB_TOKEN does not create a new workflow run — GitHub's anti-recursion rule, with only
`workflow_dispatch` and `repository_dispatch` excepted — so `gate.yml`'s `on: push` never fires for
a commit these jobs make, whatever its message says. Dropping `[skip ci]` does not buy main an
attestation; the gating has to happen BEFORE the push or it does not happen at all. That makes
properties 2 and 3 load-bearing and property 1 hygiene: the marker suppresses nothing today, WOULD
suppress the gate the day the push moves to an App/PAT token, and meanwhile says a gate is being
skipped when none would have run.

THREE PROPERTIES, checked on the real committed workflow files:
  1. no scheduled push carries a skip-CI marker (see above — hygiene, and a live hole if the token
     ever changes);
  2. the offline suite runs BEFORE the push and not only after it, so an artifact that breaks a pin
     fails its own job and never reaches main at all — the ARTIFACT-PASS RULE, which bound every
     human artifact pass and not the two that no human runs;
  3. the checkout takes FULL HISTORY. Pins reading real historical blobs — `test_state_identifiers`
     reads `c112f25:STATE.md`, this module reads `607e7d1`'s — SKIP on a shallow clone, so at the
     default depth 1 the only gate these commits get is quietly weaker than the one every PR gets.
     A gate that silently checks less than it appears to is how this whole incident happened.

A TEXT LINT, DELIBERATELY. Nothing in this project depends on a YAML parser, and adding one to read
two files we author ourselves would be the larger change. Steps run in file order, so a line number
IS the ordering property 2 asserts. Comment lines are exempt from property 1 — a comment cannot set
a commit message, and the workflows have to be able to explain why the marker is absent.
"""
from __future__ import annotations

import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

#: The five spellings GitHub Actions itself honours, plus two that it does NOT — a hyphenated form
#: and the Travis/Cloud-Build marker. The near-misses are rejected too: they do not suppress
#: anything, so a commit carrying one states an intent to skip that the repo has ruled against
#: while quietly not skipping, which is worse than either.
SKIP_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]",
                "[skip-ci]", "***NO_CI***")

#: The commit that caused the incident this module exists to prevent. Its workflow violates BOTH
#: properties, so it is the negative pin — a real observed failure shape, never a hand-rolled one.
INCIDENT_COMMIT = "607e7d1"
INCIDENT_WORKFLOW = ".github/workflows/weekly-screen.yml"


def violations(name: str, text: str) -> list[str]:
    """Every way `text` would let a scheduled commit reach main ungated. Empty == compliant."""
    out: list[str] = []
    lines = text.splitlines()

    def _cmd_line(needle: str) -> int | None:
        """1-based line number of the first COMMAND line starting with `needle`, else None."""
        for i, raw in enumerate(lines, 1):
            stripped = raw.strip()
            if stripped.startswith(needle):
                return i
        return None

    push = _cmd_line("git push")
    if push is None:
        return out  # cannot move main; nothing to gate

    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue
        for marker in SKIP_MARKERS:
            if marker in stripped:
                out.append(
                    f"{name}:{i} pushes to main behind {marker} — the commit that changes routing "
                    f"is then the one commit nothing gates, and its breakage first surfaces on the "
                    f"next unrelated PR as that PR's regression")

    gate = _cmd_line("python -m pytest")
    if gate is None:
        out.append(
            f"{name} pushes to main without running the offline suite first — the ARTIFACT-PASS "
            f"RULE applies to a pass no human runs too. Add a `python -m pytest -m 'not network'` "
            f"step before the push, so a broken artifact fails this job instead of main")
    elif gate > push:
        out.append(
            f"{name}: the offline suite runs at line {gate}, AFTER the push at line {push} — a "
            f"gate downstream of the push cannot stop the push")

    if "fetch-depth: 0" not in text:
        out.append(
            f"{name} checks out at the default depth 1, so its pre-push gate — the ONLY gate this "
            f"commit gets — silently skips every pin that reads a historical blob "
            f"(`test_state_identifiers`, and this module's own negative pin). Add `fetch-depth: 0` "
            f"to the checkout, as gate.yml does and for the same reason")
    return out


def _pushing_workflows() -> list[pathlib.Path]:
    return [p for p in sorted(WORKFLOWS.glob("*.yml")) if "git push" in p.read_text()]


def _compliant_substrate() -> str:
    """The live weekly workflow, for the two mutation pins to derive their variants from.

    They mutate REAL text rather than a hand-rolled snippet, which means an already-broken workflow
    would redden them too and bury the one failure that matters under three. Skip instead, and let
    `test_a_scheduled_push_is_gated_before_it_can_reach_main` be the single reporter of that state.
    """
    path = WORKFLOWS / "weekly-screen.yml"
    text = path.read_text()
    if violations(path.name, text):
        pytest.skip(f"{path.name} is itself non-compliant — mutating it proves nothing; see "
                    f"test_a_scheduled_push_is_gated_before_it_can_reach_main")
    return text


def test_the_corpus_actually_contains_workflows_that_push() -> None:
    """CORPUS BEFORE SYNTHETIC. A selector that matches nothing makes the two pins below vacuous —
    they would stay green through any edit, including deleting the gate they exist to protect."""
    names = [p.name for p in _pushing_workflows()]
    assert {"weekly-screen.yml", "monthly-score.yml"} <= set(names), (
        f"the scheduled jobs that commit to main are not being selected: {names}")


@pytest.mark.parametrize("path", _pushing_workflows(), ids=lambda p: p.name)
def test_a_scheduled_push_is_gated_before_it_can_reach_main(path: pathlib.Path) -> None:
    found = violations(path.name, path.read_text())
    assert not found, "\n".join(found)


def test_the_lint_rejects_the_workflow_that_actually_caused_the_incident() -> None:
    """THE NEGATIVE PIN IS THE REAL FAILURE, not a mutation drawn from the lint's own marker list.

    Skips ONLY on a genuinely shallow clone, the same way `test_state_identifiers` handles its
    historical collision — gate.yml checks out at `fetch-depth: 0` for exactly this. The shallowness
    is CHECKED rather than inferred from the failure: a negative pin that quietly skips itself
    wherever it cannot read its evidence is a pin that reports green for the wrong reason, which is
    the defect class this whole module is about. On a full clone an unreadable blob RAISES.
    """
    try:
        text = subprocess.run(
            ["git", "show", f"{INCIDENT_COMMIT}:{INCIDENT_WORKFLOW}"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                                 cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if shallow != "true":
            raise AssertionError(
                f"{INCIDENT_COMMIT}:{INCIDENT_WORKFLOW} is unreadable on a FULL clone — the "
                f"negative pin has no evidence to check and must not pass quietly: {exc}") from exc
        pytest.skip(f"{INCIDENT_COMMIT} unreachable — shallow clone, needs full history")

    found = violations(INCIDENT_WORKFLOW, text)
    assert any("[skip ci]" in v for v in found), (
        f"the lint does not reject the [skip ci] that hid the 2026-08-10 breakage: {found}")
    assert any("without running the offline suite first" in v for v in found), (
        f"the lint does not reject a push with no gate before it: {found}")
    assert any("default depth 1" in v for v in found), (
        f"the lint does not reject the shallow checkout that would gut the gate: {found}")


def test_a_gate_moved_below_the_push_is_rejected() -> None:
    """PROPERTY 2 ISOLATED. The incident workflow violates both properties at once, so it cannot
    show that ORDER is checked rather than mere presence. This reorders the LIVE weekly workflow —
    the gate still exists, it just runs too late to stop anything."""
    text = _compliant_substrate()
    lines = text.splitlines()
    gate = next(i for i, ln in enumerate(lines) if ln.strip().startswith("python -m pytest"))
    push = next(i for i, ln in enumerate(lines) if ln.strip().startswith("git push"))

    moved = lines[:gate] + lines[gate + 1:]
    moved.insert(push, lines[gate])            # the same step, now after the push
    found = violations("mutated", "\n".join(moved))
    assert any("cannot stop the push" in v for v in found), (
        f"a gate running after the push was accepted: {found}")


def test_a_shallow_checkout_is_rejected() -> None:
    """PROPERTY 3 ISOLATED. The default depth is the ABSENCE of a line, so this mutation deletes
    rather than edits — the failure mode is a checkout nobody thought about, not one written wrong.
    """
    text = _compliant_substrate()
    shallow = "\n".join(ln for ln in text.splitlines() if "fetch-depth: 0" not in ln)
    found = violations("mutated", shallow)
    assert any("default depth 1" in v for v in found), (
        f"a depth-1 checkout was accepted, so the gate could skip its history pins: {found}")


def test_a_marker_inside_a_comment_is_not_a_violation() -> None:
    """The exemption that lets the workflows explain themselves. A comment cannot set a commit
    message, and a lint that forbade the words would force the reasoning out of the file."""
    text = _compliant_substrate()
    commented = text.replace(
        "      - name: Commit refreshed snapshots",
        "      # the push below deliberately carries no [skip ci] marker\n"
        "      - name: Commit refreshed snapshots")
    assert not violations("commented", commented)
    # ...and the same text OUTSIDE a comment still fires, so the exemption is not a hole
    uncommented = text.replace(
        'git commit -m "weekly screen: refresh snapshots"',
        'git commit -m "weekly screen: refresh snapshots [skip ci]"')
    assert any("[skip ci]" in v for v in violations("uncommented", uncommented))
