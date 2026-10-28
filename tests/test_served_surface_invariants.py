"""TWO INVARIANTS ON THE SURFACE A HUMAN ACTUALLY READS. Both close incidents from #319's review.

INCIDENT 1 — THE HORIZON VANISHED FROM THE SERVED PAGE. #319 changed the insider label from
"(Form 4, 6m)" to "(Form 4)" because the VALUE was about to state its own window. The value's
change is mechanical and needs a re-assembly; the label's is render-only and ships on deploy. So
between the two, the deployed line read `Insider activity (Form 4): … sells 0 (net +90.0K sh)` —
**no horizon anywhere**, where the label had supplied it before. A strict regression on the served
surface, in the flattering direction, inside the PR written to stop exactly that.

INCIDENT 2 — FUBO'S KNOWN-WRONG BANNER WAS MISSING FROM THE WEB MIRROR. `data/dossiers/FUBO/
dossier.md` carried the 22-line "⚠ KNOWN-WRONG — do not read the figures on this page as current"
block; `frontend/dossiers/FUBO.md` — the page actually served — did not. That sidecar exists so
FUBO "cannot LOOK VALID while resting on a wrong share base", and on the web it looked valid. The
suite checked only that the SET of mirrored names matched, never that the bytes did.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOSSIERS = sorted(d for d in (ROOT / "data" / "dossiers").iterdir() if (d / "dossier.md").exists())


def states_a_horizon(line: str) -> bool:
    """Does this rendered insider line say WHAT PERIOD it covers — in EITHER the label or the value?

    Deliberately permissive about WHERE: while the artifacts lag the code the label carries it, and
    after a re-assembly the value does. What is not permitted is NEITHER, because a bare
    `sells 0` invites the reader to believe there were no sales — SMPL's true answer is 16 of them,
    $24.7M, just outside 182 days.

    AN UNKNOWN COUNTS NOTHING, so it owes no window (STATE row 35): the label drops "6m" for it,
    because "(Form 4, 6m)" above "UNKNOWN — 1 of 17 Form 4 filings could not be read" claims a
    six-month read that never happened. Matched on the rendered UNKNOWN marker, never on wording.
    """
    if re.match(r"- \*\*Insider activity \(Form 4\):\*\* _(UNKNOWN|MISSING)_ — ", line):
        return True
    return ("Form 4, 6m" in line) or ("in the last " in line and " days" in line)


def test_the_insider_line_always_states_its_horizon() -> None:
    """POSITIVE, over every committed page. The label may carry it or the value may, but a line
    that states no period at all is the #319 regression."""
    checked = 0
    for folder in DOSSIERS:
        for line in (folder / "dossier.md").read_text().splitlines():
            # THE MECHANICAL LINE ONLY, selected by its bold label. A bare "Insider activity"
            # substring also catches SYNTHESIS PROSE: UBER's 2026-08-12 re-assembly produced the
            # point "Insider activity is net-sell over 182 days ($481M sold vs $22M bought)", which
            # states its horizon perfectly clearly — just not in either phrasing this guard knows.
            # Policing LLM-composed wording is the pin-rot the TEST-LAYER RULE forbids: that point
            # reworders on every re-assembly, so the guard would redden for a reason #319 was never
            # about. #319 was the MECHANICAL label/value losing its horizon, and that is what this
            # selects.
            if "**Insider activity" in line:
                assert states_a_horizon(line), (
                    f"{folder.name}: the insider line states NO horizon — "
                    f"neither the label nor the value says what period it covers:\n  {line}")
                checked += 1
    assert checked, "no committed dossier renders an insider line — the guard checked nothing"


def test_a_horizonless_insider_line_is_rejected() -> None:
    """NEGATIVE, with the REAL failing string from #319 — not a synthetic one. Without this the
    positive pin above could be satisfied by a checker that never says no."""
    shipped_bad = ("- **Insider activity (Form 4):** Open-market buys 2 · sells 0 "
                   "(net +90.0K sh) · grants 12 · last 2026-07-24 · other filings 4 [67]")
    assert not states_a_horizon(shipped_bad)
    # …and both legitimate forms are accepted, so the guard cannot be passed by deleting the line.
    assert states_a_horizon("- **Insider activity (Form 4, 6m):** Open-market buys 2 · sells 0")
    assert states_a_horizon("- **Insider activity (Form 4):** buys 2 — in the last 182 days")
    # an UNKNOWN states no count, so it needs no window — but only the rendered UNKNOWN marker
    # earns that, never a PRESENT count that merely mentions the word
    assert states_a_horizon("- **Insider activity (Form 4):** _UNKNOWN_ — 1 of 17 Form 4 filings "
                            "in the 1095d scanned could not be read")
    assert not states_a_horizon("- **Insider activity (Form 4):** Open-market buys 2 · sells 0 "
                                "(_UNKNOWN_ — )")


def test_every_web_mirror_is_byte_identical_to_its_source() -> None:
    """FUBO'S BANNER. The web page is a MIRROR, not a second render — if the bytes differ, one of
    the two surfaces is showing something the other is not, and nobody can say which is current.
    The pre-existing check compared only the SET of mirrored names, which is why a 22-line
    known-wrong warning could go missing from the served page and stay missing."""
    for folder in DOSSIERS:
        mirror = ROOT / "frontend" / "dossiers" / f"{folder.name}.md"
        assert mirror.exists(), f"{folder.name}: no web mirror"
        assert mirror.read_text() == (folder / "dossier.md").read_text(), (
            f"{folder.name}: frontend/dossiers/{folder.name}.md differs from its source — "
            "re-run frontend/build.py; the served page is not what data/ says it is")


def test_a_name_with_a_known_wrong_sidecar_carries_its_banner_on_both_surfaces() -> None:
    """The specific claim, conditional so it cannot rot when FUBO clears: IF a name declares a
    known-wrong sidecar THEN both surfaces must carry its warning. A page that says
    "do not trust these figures" on one surface and not the other is worse than either alone."""
    checked = 0
    for folder in DOSSIERS:
        sidecar = folder / "known_wrong.json"
        if not sidecar.exists():
            continue
        json.loads(sidecar.read_text())            # it must be readable to be authoritative
        mirror = ROOT / "frontend" / "dossiers" / f"{folder.name}.md"
        for surface in (folder / "dossier.md", mirror):
            assert "KNOWN-WRONG" in surface.read_text(), (
                f"{folder.name}: {surface} carries no known-wrong banner while "
                f"{sidecar} declares one")
        checked += 1
    if not checked:
        pytest.skip("no committed dossier declares a known-wrong sidecar")
