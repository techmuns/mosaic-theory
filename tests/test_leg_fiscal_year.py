"""The base leg states which fiscal year it is struck at — and the gap says when it disagrees.

WHY. `ev_gap` decomposes at ONE year: `revenue_ratio` against consensus revenue there,
`margin_ratio` against consensus EBITDA÷revenue there, `multiple_ratio` against `TEV ÷ consensus
EBITDA` there — commented in the source as *"the market's multiple ON THE ANCHOR YEAR"*. And
`EvGapInputs.revenue` has always been commented *"our leg's revenue at the anchor"*. That
assumption was never checkable, and SMPL's 2026-08-05 underwrite broke it: its base leg is the
FY2028 consensus median, read at an 18-month horizon, against an FY2026 anchor.

**THE TOTAL IS ANCHOR-INDEPENDENT — ONLY THE ATTRIBUTION MOVES.** `ev_gap = our_EV / TEV` and
neither term carries a year. Measured on SMPL: 1.6711 struck at FY2026, 1.6711 struck at FY2028.
What differs is the SPLIT — revenue 0.9913/1.0004, margin 1.0365/0.9862, multiple 1.6264/1.6939 —
and therefore which driver the page names as dominant. A retracted earlier claim said the total
would read 1.6864 on an FY2028 basis; that re-based revenue alone and violates the
`product == ev_gap` assertion, so no such state is reachable.

UNSTATED IS NOT DISAGREEING. Every committed record predates `leg_fy`. `unstated` means the record
never said — unverifiable, not wrong — and it renders as a different sentence.
"""
from __future__ import annotations

import json
import pathlib

import pytest

import vinci.scenarios as sc
from vinci.dossier.ev_gap import leg_basis

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _leg(fy: str | None) -> dict[str, object]:
    return {"revenue": 1340.0, "margin": 0.155, "multiple": 9.0, "leg_fy": fy}


def test_the_three_states_are_distinguishable_and_only_one_is_a_problem() -> None:
    """POSITIVE + both NEGATIVES. The `unstated` case is the one that matters most: it is the state
    every committed record is in, so a flag that folded it into `disagrees` would cry wolf on all
    eleven and a flag that folded it into `agrees` would be silent on all eleven."""
    assert leg_basis(_leg("2026"), "2026")["state"] == "agrees"
    assert leg_basis(_leg("2028"), "2026")["state"] == "disagrees"
    assert leg_basis(_leg(None), "2026")["state"] == "unstated"
    assert leg_basis(None, "2026")["state"] == "unstated"
    # nothing struck ⇒ nothing to check against
    assert leg_basis(_leg("2028"), None)["state"] == "unstated"

    # and the three carry DIFFERENT prose — the distinction has to survive to the reader
    dis = str(leg_basis(_leg("2028"), "2026")["note"])
    uns = str(leg_basis(_leg(None), "2026")["note"])
    assert leg_basis(_leg("2026"), "2026")["note"] is None, "agreement states nothing"
    assert dis != uns
    assert "FY2028" in dis and "FY2026" in dis, dis
    assert "does not state" in uns, uns
    # BOTH must say the total is safe, or a reader discounts the headline number for no reason
    for note in (dis, uns):
        assert "TOTAL gap is unaffected" in note or "carries no year" in note, note


def test_the_write_guard_refuses_only_an_unexplained_disagreement() -> None:
    """THE WRITE BOUNDARY. A leg struck at another year is LEGITIMATE — SMPL's 18-month thesis
    reads FY2028 deliberately — so the guard refuses only silence, through the same `reason` field
    that already carries "WHY this deviates from the anchor"."""
    rec = sc.read_record("SMPL", root=ROOT)

    def with_base(**over: object) -> sc.ScenarioInput:
        return rec.scenarios["base"].model_copy(update=over)

    assert sc.leg_fy_problems(with_base(leg_fy="2026"), "2026") == []
    assert sc.leg_fy_problems(with_base(leg_fy=None), "2026") == [], (
        "an UNSTATED year must not be refused — every committed record is in that state, and "
        "refusing it would make the field impossible to adopt")
    assert sc.leg_fy_problems(with_base(leg_fy="2028"), None) == []      # no anchor ⇒ no check

    explained = sc.leg_fy_problems(with_base(leg_fy="2028", reason="FY2028 at an 18-month horizon"),
                                   "2026")
    assert explained == [], "a STATED reason satisfies the guard — the deviation idiom"

    silent = sc.leg_fy_problems(with_base(leg_fy="2028", reason="  "), "2026")
    assert len(silent) == 1 and "FY2028" in silent[0] and "FY2026" in silent[0]
    assert "TOTAL gap is unaffected" in silent[0], (
        "the refusal must not imply the headline number is wrong — it is not")


def test_run_recipe_never_refuses_on_the_leg_year() -> None:
    """THE PLACEMENT, pinned. A guard added after a record was written must never make that record
    unrecomputable: refusing inside `run_recipe` would blind
    `test_every_committed_record_result_matches_its_own_facts` on the only open position. Same
    argument that put the horizon refusal at the write boundary in #346."""
    rec = sc.read_record("SMPL", root=ROOT)
    mismatched = rec.model_copy(update={"scenarios": {
        **rec.scenarios,
        "base": rec.scenarios["base"].model_copy(update={"leg_fy": "2033", "reason": ""})}})
    out = sc.run_recipe(mismatched)                       # must not raise
    assert out.result.ratio is not None and out.result.gate is not None


def test_every_committed_dossier_reads_unstated_and_none_reads_disagrees() -> None:
    """THE CORPUS TODAY. No committed record carries `leg_fy`, so every computed gap must say
    `unstated` — never `agrees` (which would claim a check that did not happen) and never
    `disagrees` (which would fault a record for a field that did not exist)."""
    seen = 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        g = (json.loads(p.read_text())["mechanical"].get("ev_gap")) or {}
        lb = g.get("leg_basis")
        if lb is None:
            continue                      # a gap that was never struck carries no basis claim
        seen += 1
        assert lb["state"] == "unstated", f"{p.parent.name}: {lb}"
    assert seen, "no committed dossier carries a leg_basis — this sweep checked nothing"


def test_the_total_gap_does_not_move_with_the_year_but_the_split_does() -> None:
    """THE CLAIM THE WHOLE FLAG RESTS ON, measured on the committed SMPL inputs rather than
    asserted. If the total DID move with the year, the caveat's promise that the headline number is
    unaffected would be false and the flag would be misleading in the reassuring direction."""
    from vinci.dossier import ev_gap as eg
    from vinci.dossier.refresh import _base_leg

    doc = json.loads((ROOT / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    m = doc["mechanical"]
    levels = (m["consensus_context"] or {})["consensus_levels"]
    leg, br = _base_leg("SMPL"), (m["ev_gap"] or {})["bridge"]
    assert leg, "SMPL has no base leg"
    got = {}
    for fy in ("2026", "2028"):
        d = eg._decompose_at(levels, fy, leg, br["tev"], br["net_debt"], leg["shares"])
        assert d is not None
        got[fy] = d
    assert got["2026"]["ev_gap"] == pytest.approx(got["2028"]["ev_gap"], rel=1e-12), (
        "the TOTAL gap moved with the anchor year — it is our_EV/TEV and carries no year, so this "
        "is either a real regression or the caveat's central claim is wrong")
    assert got["2026"]["revenue_ratio"] != pytest.approx(got["2028"]["revenue_ratio"], rel=1e-6), (
        "the SPLIT did not move between years — then there is nothing for this flag to warn about")


def test_both_write_paths_call_the_guard_and_the_template_can_state_the_year() -> None:
    """THE CALL SITES, not the helper — the rule this session has had to learn twice.

    The first cut wired `leg_fy_problems` into `scenario-supersede` ONLY. `scenario-create` had no
    template cell for the field, never read it, and never checked it — so a record created through
    the normal path could only ever read "unstated", permanently. Declared and readable but not
    WRITABLE from its own writer is the same class as a helper nothing calls, and every test in
    this file passed while it was true.

    Asserted on the SOURCE of both commands, and on the TEMPLATE a real dossier produces."""
    import inspect

    from vinci import cli
    from vinci.dossier.propose import build_template

    for fn in (cli._cmd_scenario_create, cli._cmd_scenario_supersede):
        src = inspect.getsource(fn)
        assert "leg_fy_problems" in src, (
            f"{fn.__name__} does not run the leg-year guard — the field is enforced on one write "
            "path and not the other, so the unguarded one is the one an analyst will use")

    doc = json.loads((ROOT / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    base = build_template(doc)["scenarios"]["base"]
    assert "leg_fy" in base, "the template has no cell for the leg year — it cannot be stated"
    anchor = ((doc["mechanical"].get("ev_gap") or {}).get("anchor_fy"))
    assert base["leg_fy"] == str(anchor), (
        f"the template proposes leg_fy={base['leg_fy']!r} against an anchor of {anchor!r}; it must "
        "state the year `propose_anchors` actually struck the revenue at, or the default is a "
        "guess rather than a statement")
