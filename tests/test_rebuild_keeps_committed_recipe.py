"""A re-assembly keeps the committed recipe; it shows its own proposal instead of applying it.

THE INCIDENT, four times. Every hand re-tag on record was erased by the next full re-assembly,
because `assemble._write` wrote a freshly computed anchor over the committed block: AORT's
`R2_NEEDED`, CNXC's `R1_NOT_ROBUST`, VITL's `R2_NEEDED` and GOOGL's `R3_forward_pe` — the last one
on the fund's first confirmed position, whose own R3 record the scenario gate then refused.
`anchor-backfill` had preserved re-tags since July; assembly was the second write path.

Driven through `_write` with the REAL incident blocks (frozen from git, see the fixture's
provenance) and READ BACK FROM DISK, because the failure lived on the write path: a test of
`preserve_operator_tag` alone stayed green the whole time the re-tags were being erased.

REVIEW OF #670 found the first cut kept two things that are not recipes — a placeholder hint
(`unknown`) and a machine refusal reason under an unchanged recipe. Both are pinned on real
transitions below (NCNO's 07-23/07-27 builds; NFLX's committed refusal).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.dossier import assemble as asm
from vinci.dossier.anchor import Anchor, preserve_operator_tag
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "anchor_retag_erasures.json").read_text())
INCIDENTS = sorted(k for k in FIXTURE if not k.startswith("_"))
RULES = json.loads((ROOT / "tests" / "fixtures" / "anchor_rule_transitions.json").read_text())
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


def _replay(ticker: str, committed: dict[str, object], rebuilt: dict[str, object],
            tmp_path: Path) -> dict[str, object]:
    """One build through the real write path: `committed` on disk, `rebuilt` handed in."""
    folder = tmp_path / ticker
    folder.mkdir()
    (folder / "dossier.json").write_text(json.dumps({"ticker": ticker, "anchor": committed}))
    asm._write(_carrier(ticker, rebuilt), "(test)", tmp_path)
    written: dict[str, object] = json.loads((folder / "dossier.json").read_text())
    return written


def test_a_placeholder_never_outlives_the_data_gap_that_wrote_it(tmp_path: Path) -> None:
    """REVIEW OF #670, FINDING 1, on NCNO's real 07-27 build: committed `unknown` (own-history
    missing), and the build computes `R2_NEEDED`. Keeping the placeholder would print "multiple
    missing" over a recipe that resolved — FUBO, ORKA and TECX sit committed as `unknown` today.
    The build's recipe and reason are written, and no caveat is added: no recipe was kept."""
    inc = RULES["NCNO_off_placeholder"]
    written = _replay("NCNO", inc["committed"], inc["rebuilt"], tmp_path)
    anchor = written["anchor"]
    assert isinstance(anchor, dict)
    assert anchor["recipe_hint"] == inc["rebuilt"]["recipe_hint"], "a placeholder was kept"
    assert anchor["reason"] == inc["rebuilt"]["reason"], "the placeholder's reason was kept"
    assert written["caveats"] == list(_carrier("NCNO", inc["rebuilt"]).caveats)


def test_a_real_recipe_is_kept_over_a_data_gap_placeholder(tmp_path: Path) -> None:
    """The other direction, NCNO's real 07-23 build: committed `R2_NEEDED`, and the build hit a
    data gap and could only say `unknown`. The recipe survives the gap, and the page names both
    with the build's own reason — the gap stays visible without erasing the recipe."""
    inc = RULES["NCNO_onto_placeholder"]
    written = _replay("NCNO", inc["committed"], inc["rebuilt"], tmp_path)
    anchor, caveats = written["anchor"], written["caveats"]
    assert isinstance(anchor, dict) and isinstance(caveats, list)
    assert anchor["recipe_hint"] == inc["committed"]["recipe_hint"], "a data gap erased a recipe"
    assert anchor["reason"] == inc["committed"]["reason"]
    assert any(inc["committed"]["recipe_hint"] in c and inc["rebuilt"]["recipe_hint"] in c
               and inc["rebuilt"]["reason"] in c for c in caveats), caveats


def test_a_reason_under_an_unchanged_recipe_is_the_builds_own(tmp_path: Path) -> None:
    """REVIEW OF #670, FINDING 2: NFLX's committed machine refusal ("R1 inputs incomplete")
    against a build still R1 and still not applicable, for a DIFFERENT cause. The page must state
    the cause this build found, with no caveat — the first cut kept the old cause and repeated a
    caveat on every rebuild until someone edited the reason by hand."""
    inc = RULES["NFLX_new_cause"]
    written = _replay("NFLX", inc["committed"], inc["rebuilt"], tmp_path)
    anchor = written["anchor"]
    assert isinstance(anchor, dict)
    assert anchor["reason"] == inc["rebuilt"]["reason"], "a machine refusal outlived its cause"
    assert written["caveats"] == list(_carrier("NFLX", inc["rebuilt"]).caveats)


@pytest.mark.parametrize(("case", "field", "winner"), [
    ("NCNO_off_placeholder", "recipe_hint", "rebuilt"),
    ("NCNO_onto_placeholder", "recipe_hint", "committed"),
    ("NFLX_new_cause", "reason", "rebuilt"),
])
def test_the_shared_rule_itself_carries_both_review_fixes(case: str, field: str,
                                                          winner: str) -> None:
    """`anchor-backfill` writes whatever `preserve_operator_tag` returns, with no recipe-only
    filter of its own — so the RULE must carry both fixes, not just the assembly guard in front of
    it. Measured: a mutant that froze the machine reason again INSIDE the rule survived every
    assembly-path test above, because that guard only ever applies a kept recipe."""
    inc = RULES[case]
    kept, _ = preserve_operator_tag(Anchor.model_validate(inc["committed"]),
                                    Anchor.model_validate(inc["rebuilt"]))
    assert getattr(kept, field) == inc[winner][field], (
        f"{case}: the rule kept the {'committed' if winner == 'rebuilt' else 'rebuilt'} {field}")


@pytest.mark.parametrize("ticker", COMMITTED)
def test_rewriting_a_committed_dossier_over_itself_changes_no_recipe(ticker: str) -> None:
    """NEGATIVE, on the whole committed corpus: where the build agrees with the committed anchor —
    every name today — the guard must change nothing and say nothing. Read-only: the committed
    folder is the prior, and nothing is written.

    ITS LIMIT, STATED (review of #670): a build that agrees with itself never DIVERGES, so this
    cannot catch a rule that keeps the wrong thing. The NCNO and NFLX pins above cover that."""
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
