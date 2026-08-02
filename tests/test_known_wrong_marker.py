"""FUBO'S KNOWN-WRONG MARKER — a sealed record marked as false without being written to.

THE RULE IT WORKS AROUND, AND WHY THAT IS NOT A DODGE. FUBO's standing rule (STATE.md, 2026-07-22)
seals `dossier.json` until a post-combination re-assembly exists, because a FUBO record could pass
every existing check while resting on the wrong share base. **The marker serves that purpose rather
than evading it**: every item asserts a number is FALSE, so a page carrying it cannot look valid.
Operator ruling 2026-08-01: build it as a SIDECAR — `known_wrong.json` beside the record, the
record untouched, the rendered view carrying the banner because a rendered view is not the record.

GAP vs ERROR is the whole point. A gap is a number we do not have; an error is a number we have and
can demonstrate is wrong. FUBO's page carries errors, and a reader who files them under "stale"
will underestimate them by a corporate action.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
FUBO = ROOT / "data" / "dossiers" / "FUBO"
MARKER = FUBO / "known_wrong.json"
#: The five, by id. Named here so DROPPING one reddens — the set is the finding, not a sample.
EXPECTED = {"share-count", "g3-never-valued", "caveat-text-pre-fix", "agreement-bug",
            "pre-combination-entity"}


def test_the_marker_exists_and_names_all_five() -> None:
    """MUTATION: marker absent -> red. Also reds if an item is dropped: five distinct known-false
    claims were established, and a marker naming four would under-report a sealed page."""
    assert MARKER.is_file(), (
        "FUBO's known-wrong marker is missing — the page then presents figures that are "
        "demonstrably false with nothing saying so")
    doc = json.loads(MARKER.read_text())
    ids = {i["id"] for i in doc["items"]}
    assert ids == EXPECTED, (
        f"marker items changed: missing {EXPECTED - ids}, extra {ids - EXPECTED}")
    for item in doc["items"]:
        # EVERY item states the false claim AND why it is not merely stale. The second field is
        # what carries the gap/error distinction; without it the banner reads as a staleness note.
        assert item["known_false"].strip(), f"{item['id']}: no known_false statement"
        assert item["not_merely_stale"].strip(), f"{item['id']}: no gap-vs-error distinction"


def test_the_marker_reaches_the_rendered_page_above_the_numbers() -> None:
    """MUTATION: marker present but not rendered -> red. A marker nobody meets is not a marker —
    17b's failure exactly. Asserted ABOVE the brief, because a reader who reaches the figures
    first has already been misled."""
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    md = render_markdown(Dossier.model_validate_json((FUBO / "dossier.json").read_text()),
                         card=_read_scenario_card("FUBO"))
    assert "KNOWN-WRONG" in md, "the marker file exists but never reaches the page"
    body = md.index("KNOWN-WRONG")
    for later in ("## Brief", "## What broke", "Valuation"):
        if later in md:
            assert body < md.index(later), f"the marker renders BELOW {later!r} — too late to help"
    committed = (FUBO / "dossier.md").read_text()
    assert "KNOWN-WRONG" in committed, "the committed FUBO page does not carry the marker"


def test_a_name_without_a_marker_renders_unchanged() -> None:
    """The banner is per-name and silent by default — ten other dossiers must be untouched."""
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    for ticker in ("SMPL", "AORT"):
        path = ROOT / "data" / "dossiers" / ticker / "dossier.json"
        md = render_markdown(Dossier.model_validate_json(path.read_text()))
        assert "KNOWN-WRONG" not in md, f"{ticker} rendered a marker it has no file for"


def test_the_sealed_record_itself_is_untouched() -> None:
    """MUTATION: dossier.json modified -> red. THE RULE'S ACTUAL SUBJECT. The marker is legitimate
    only because it never writes the record — asserted against git, not against intent, since the
    whole point is that a well-meaning write is still a write.

    Skips when the object is unreachable rather than failing: an unavailable fixture is not a
    defect in the code under test (#280)."""
    proc = subprocess.run(["git", "diff", "--name-only", "origin/main", "--",
                           "data/dossiers/FUBO/dossier.json"],
                          cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:                                  # pragma: no cover - env-dependent
        import pytest
        pytest.skip("git/origin unavailable in this checkout")
    assert not proc.stdout.strip(), (
        "data/dossiers/FUBO/dossier.json was modified — FUBO's standing rule seals it until a "
        "post-combination re-assembly exists, and the marker is a sidecar precisely so that "
        "stays true")
