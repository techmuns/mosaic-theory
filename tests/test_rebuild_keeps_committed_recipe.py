"""A re-assembly keeps the committed recipe; it shows its own proposal instead of applying it.

THE INCIDENT, four times. Every hand re-tag on record was erased by the next full re-assembly,
because `assemble._write` wrote a freshly computed anchor over the committed block: AORT's
`R2_NEEDED`, CNXC's `R1_NOT_ROBUST`, VITL's `R2_NEEDED` and GOOGL's `R3_forward_pe` — the last one
on the fund's first confirmed position, whose own R3 record the scenario gate then refused.
`anchor-backfill` had preserved re-tags since July; assembly was the second write path.

Driven through `_write` with the REAL incident blocks (frozen from git, see the fixture's
provenance) and READ BACK FROM DISK, because the failure lived on the write path: a test of
`preserve_operator_tag` alone stayed green the whole time the re-tags were being erased.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.dossier import assemble as asm
from vinci.dossier.anchor import Anchor
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "anchor_retag_erasures.json").read_text())
INCIDENTS = sorted(k for k in FIXTURE if not k.startswith("_"))
COMMITTED = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))


def _carrier(ticker: str, anchor: dict[str, object]) -> Dossier:
    """Today's committed dossier for the name, carrying the anchor the erasing build produced. Only
    the anchor is the incident's; everything else is the real artifact the write path renders."""
    path = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    live = Dossier.model_validate_json(path.read_text())
    return live.model_copy(update={"anchor": Anchor.model_validate(anchor)})


@pytest.mark.parametrize("ticker", INCIDENTS)
def test_a_rebuild_keeps_the_hand_retag_it_used_to_erase(ticker: str, tmp_path: Path) -> None:
    """The erasing build replayed: the committed block (hand re-tag) is on disk, the build hands the
    write path the machine's proposal. The written artifact must keep the committed recipe and its
    reason, and the page must say the build proposed something else."""
    inc = FIXTURE[ticker]
    committed, rebuilt = inc["committed"], inc["rebuilt"]
    assert committed["recipe_hint"] != rebuilt["recipe_hint"], "fixture lost its divergence"
    folder = tmp_path / ticker
    folder.mkdir()
    (folder / "dossier.json").write_text(json.dumps({"ticker": ticker, "anchor": committed}))

    returned = asm._write(_carrier(ticker, rebuilt), "(test)", tmp_path)

    written = json.loads((folder / "dossier.json").read_text())
    assert written["anchor"]["recipe_hint"] == committed["recipe_hint"], (
        f"{ticker}: the rebuild overwrote the committed recipe "
        f"{committed['recipe_hint']!r} with {written['anchor']['recipe_hint']!r}")
    assert written["anchor"]["reason"] == committed["reason"], "the re-tag's reason was not kept"
    # The divergence reaches the HUMAN surface — both recipes named, in the page's caveats.
    said = [c for c in written["caveats"]
            if committed["recipe_hint"] in c and rebuilt["recipe_hint"] in c]
    assert said, f"{ticker}: no caveat names both the kept and the proposed recipe"
    page = (folder / "dossier.md").read_text()
    assert committed["recipe_hint"] in page and rebuilt["recipe_hint"] in page, (
        "the rendered page does not show the kept recipe beside the build's proposal")
    # What assembly returns is what it wrote — callers never see the erased version.
    assert returned.anchor is not None and returned.anchor.recipe_hint == committed["recipe_hint"]


@pytest.mark.parametrize("ticker", COMMITTED)
def test_rewriting_a_committed_dossier_over_itself_changes_no_recipe(ticker: str) -> None:
    """NEGATIVE, on the whole committed corpus: where the build agrees with the committed anchor —
    every name today — the guard must change nothing and say nothing. Read-only: the committed
    folder is the prior, and nothing is written."""
    folder = ROOT / "data" / "dossiers" / ticker
    d = Dossier.model_validate_json((folder / "dossier.json").read_text())
    assert asm._keep_committed_recipe(d, folder) is d, (
        f"{ticker}: the guard altered a dossier whose build agrees with its committed anchor")


def test_a_committed_anchor_that_does_not_validate_is_refused_not_overwritten(
        tmp_path: Path) -> None:
    """A readable file whose anchor block cannot be read as an Anchor holds a recipe this build
    cannot see — writing over it is the incident reached another way. Refused, and the committed
    bytes are left as they were."""
    inc = FIXTURE["GOOGL"]
    broken = {**inc["committed"], "applicable": "not-a-bool"}
    folder = tmp_path / "GOOGL"
    folder.mkdir()
    before = json.dumps({"ticker": "GOOGL", "anchor": broken})
    (folder / "dossier.json").write_text(before)
    with pytest.raises(asm.DossierAssemblyError, match="does not validate"):
        asm._write(_carrier("GOOGL", inc["rebuilt"]), "(test)", tmp_path)
    assert (folder / "dossier.json").read_text() == before, "the refusal wrote anyway"
