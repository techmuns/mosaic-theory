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


def test_every_committed_gap_reads_the_state_its_record_actually_supports() -> None:
    """WAS a snapshot of a corpus in which NOTHING carried `leg_fy` ("every computed gap must say
    `unstated`"). EPAM broke it on 2026-08-07 by becoming the first record to state the field —
    correctly, and reading `disagrees` (base leg FY2027 against an FY2026 decomposition).

    THE SNAPSHOT HAD THE MIRROR OF THE HOLE `leg_fy_problems` WAS WRITTEN TO AVOID. That function
    refuses to fault an unstated year precisely because "the first record to state it would be the
    only one that could ever be written"; this test made the first record to state it turn the
    suite RED, which is the same adoption trap one layer over.

    BOTH ORIGINAL PROTECTIONS ARE KEPT AND ONE IS TIGHTENED. A record with no `leg_fy` must still
    read `unstated` — never `agrees`, which would claim a check that did not happen. A record that
    DOES state one must read the state its two years actually support, so `agrees` still cannot be
    asserted without the years matching, and a stated year can no longer hide as `unstated`."""
    import json as _json

    def _leg_fy(t: str) -> str | None:
        f = ROOT / "scenarios" / f"{t}.json"
        if not f.is_file():
            return None
        base = ((_json.loads(f.read_text()).get("scenarios") or {}).get("base")) or {}
        return None if base.get("leg_fy") is None else str(base["leg_fy"])

    seen = stated = 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        g = (json.loads(p.read_text())["mechanical"].get("ev_gap")) or {}
        lb = g.get("leg_basis")
        if lb is None:
            continue                      # a gap that was never struck carries no basis claim
        seen += 1
        t = p.parent.name
        fy = _leg_fy(t)
        if fy is None:
            assert lb["state"] == "unstated", f"{t}: no leg_fy on the record, but {lb}"
            continue
        stated += 1
        anchor = None if lb.get("anchor_fy") is None else str(lb["anchor_fy"])
        want = "agrees" if fy == anchor else "disagrees"
        assert lb["state"] == want, (
            f"{t}: record states leg_fy={fy} against anchor_fy={anchor}, so the gap must read "
            f"{want!r} — got {lb['state']!r}")
    assert seen, "no committed dossier carries a leg_basis — this sweep checked nothing"
    assert stated, (
        "no committed record states leg_fy — the stated branch above checked nothing, so this "
        "test has quietly reverted to the snapshot it replaced")


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


def test_every_scenario_input_field_is_settable_from_the_template() -> None:
    """THE CLASS, MADE CHECKABLE — three instances this session, each caught only by self-review.

    A field the analyst is meant to supply must be reachable from `build_template`, or it is
    declared and readable but not WRITABLE from the path that creates records. `leg_fy` shipped in
    exactly that state: the fleet read `unstated 10` and nothing looked wrong, because that is also
    the correct reading when no record has stated one. A silent, permanent default.

    **SETTABLE FROM *SOME* LEG, NEVER FROM EVERY LEG — and this is the design, not a weakening.**
    Three fields are legitimately leg-specific: `years_to_terminal` and `leg_fy` are base-only (a
    horizon and a fiscal year belong to the case being valued, not to the downside sketch), and
    `bear_basis` is bear-only by definition. A per-leg assertion would fire three false positives
    on day one and would be "fixed" by exempting them — which is a pin narrowing its comparison
    until it passes, the shape this repo has already paid for. If you tighten this, you will delete
    the reason it works.

    The exemption list is EMPTY today. It is written as an exact set so a new field cannot be
    quietly excused: adding one to the model without a template cell reddens this, and adding it
    HERE requires stating why in the same breath."""
    import vinci.scenarios as _sc
    from vinci.dossier.propose import build_template

    #: Fields legitimately absent from every template cell, each with its reason. EMPTY — kept as a
    #: declared set so an addition is a deliberate, explained act rather than a quiet one.
    exempt: dict[str, str] = {}

    doc = json.loads((ROOT / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    cells = build_template(doc)["scenarios"]
    assert cells, "the template produced no legs — this sweep would check nothing"

    missing = {f for f in _sc.ScenarioInput.model_fields
               if not any(f in cell for cell in cells.values())} - set(exempt)
    assert not missing, (
        f"{sorted(missing)} exist on ScenarioInput but no template cell can set them, so a record "
        "created through `scenario-create` can never carry them — declared and readable but not "
        "writable from its own writer. Add a cell in `build_template`, or add the field "
        "to `exempt` with the reason it belongs there.")
    stale = set(exempt) - set(_sc.ScenarioInput.model_fields)
    assert not stale, f"`exempt` names {sorted(stale)}, which are not fields — a stale licence"


def test_a_declared_year_difference_that_does_not_move_the_shape_is_not_a_defect() -> None:
    """REVIEW FINDING on EPAM, the first record to state `leg_fy`. The caveat printed
    "⚠ … describes a comparison the leg does not make. Re-read the attribution on FY2027"
    DIRECTLY BENEATH the shape line reading "FY2027 gives the same shape — the label does not move
    with the year." Two adjacent sentences, one instructing work the other had just done, on the
    only page in the fleet showing this caveat. A correctly-declared difference read as a defect.

    Severity now follows the cross-year check the shape line already computed."""
    md = (ROOT / "data" / "dossiers" / "EPAM" / "dossier.md").read_text()
    lines = md.splitlines()
    # TWO lines start "- **Shape:**" — the drawdown character line and the EV-gap decomposition
    # line. Only the latter carries a fiscal year, which is what disambiguates them.
    i = next((k for k, ln in enumerate(lines)
              if ln.startswith("- **Shape:**") and " at FY" in ln), None)
    assert i is not None, "no EV-gap shape line on EPAM's page — this pin checked nothing"
    assert "same shape" in lines[i], f"expected an invariant shape: {lines[i]}"
    caveat = "\n".join(lines[i + 1:i + 4])          # the paragraph that rides with the shape
    assert "Declared, and immaterial to this label" in caveat, caveat
    assert "\u26a0" not in caveat, (
        "a declared year difference that does not move the shape still renders as a warning")
    assert "Re-read the attribution" not in caveat, (
        "instructs work the line above already reports as done")


def test_the_caveat_severity_is_driven_by_the_cross_year_check_on_all_three_states() -> None:
    """THE UNIT PIN, and the reason it exists is that my first two attempts could not fail.

    One read the COMMITTED `dossier.md` — a static file, so no change to `render.py` can move it.
    The other grepped `render.py`'s SOURCE TEXT for a sentence, which survives any logic edit that
    leaves the string in place. Both passed while mutations of the branch they were written to
    guard survived. A test that cannot fail on the change it covers is not a guard.

    This one CALLS the renderer over the three cross-year states and reads the emitted lines."""
    import json as _json

    from vinci.dossier.render import _ev_gap_lines
    from vinci.dossier.schemas import MechanicalLayer

    doc = _json.loads((ROOT / "data" / "dossiers" / "EPAM" / "dossier.json").read_text())

    def caveat(agree: object, leg_fy: str) -> str:
        mech = _json.loads(_json.dumps(doc["mechanical"]))
        g = mech["ev_gap"]
        g["shape"] = {**(g.get("shape") or {}), "agree": agree}
        g["leg_basis"] = {"leg_fy": leg_fy, "anchor_fy": str(g.get("anchor_fy")),
                          "state": "disagrees", "note": "n/a"}
        lines = _ev_gap_lines(MechanicalLayer.model_validate(mech))
        i = next(k for k, ln in enumerate(lines) if ln.startswith("- **Shape:**"))
        return "\n".join(lines[i + 1:i + 3])

    adj = str(doc["mechanical"]["ev_gap"]["adjacent_fy"])

    same = caveat(True, adj)
    assert "Declared, and immaterial" in same and "\u26a0" not in same, same

    moves = caveat(False, adj)
    assert "\u26a0" in moves and "shape MOVES between them" in moves, moves

    unchecked = caveat(None, adj)
    assert "\u26a0" in unchecked, unchecked
