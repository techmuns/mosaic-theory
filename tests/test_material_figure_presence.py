"""ITEM 19c — a MATERIAL figure the synthesis prose never states.

THE INCIDENT, and it is the whole argument for a deterministic guard. SMPL's bear case was CORRECT
on 2026-07-29:

    "A $60.9M Atkins impairment (FY25) plus $391.9M LTM asset writedown drove GAAP net income to
     -$199M LTM…"

and WRONG on 2026-07-30, from IDENTICAL INPUTS:

    "A $60.9M non-cash Atkins impairment plus a $249M OWYN/Atkins brand-asset impairment (per the
     call context)…"

The table said -60.9 and -391.9; the prose said 60.9 and 249. **Synthesis correctness is
stochastic** — every figure in every run is a fresh roll, and no prompt care removes the need for a
check. The nine current pages each got one roll.

THE BAD RUN WAS NOT FABRICATING. $249M is a real Q2 charge, cited as though it were the total. So
the check cannot ask "is this figure plausible" — every number in it was. It asks the only question
that separates the two runs: **does the material row's own figure appear at all?**

WHY IT REFUSES RATHER THAN FLAGS: a flag moves the judgement to a human on every run. Refusing
means the bad roll fails and is re-rolled, and the good one ships — which is what makes the revert
of 07-30 a one-off rather than a practice.
"""
from __future__ import annotations

import pytest

from vinci.dossier.synthesis import (
    MATERIAL_FIGURE_FLOOR_MUSD,
    _figure_cited,
    uncited_material_figures,
)

# The two real SMPL bear points, verbatim.
GOOD = ("A $60.9M Atkins impairment (FY25) plus $391.9M LTM asset writedown drove GAAP net income "
        "to -$199M LTM and ROE to -12.2% — management has already written down brand value.")
BAD = ("A $60.9M non-cash Atkins impairment plus a $249M OWYN/Atkins brand-asset impairment (per "
       "the call context) confirm the write-down of acquired brand value.")


class _Row:
    def __init__(self, label: str, values: list[float | None], material: bool = True) -> None:
        self.label, self.values, self.material = label, values, material


class _Ann:
    def __init__(self, rows: list[_Row], columns: list[str],
                 is_estimate: list[bool] | None = None) -> None:
        self.rows, self.columns = rows, columns
        self.is_estimate = is_estimate if is_estimate is not None else [
            c.rstrip(")").endswith("E") for c in columns]


class _Val:
    def __init__(self, v: object) -> None:
        self.value = v


class _Mech:
    def __init__(self, ann: _Ann) -> None:
        self.financial_summary = _Val(None)
        self.financial_summary.annual = _Val(ann)  # type: ignore[attr-defined]


class _Synth:
    def __init__(self, claim: str) -> None:
        self.bull_points: list[object] = []
        self.bear_points: list[object] = [claim]
        self.key_unknowns: list[object] = []


def _smpl_mech() -> _Mech:
    """SMPL's real Asset Writedown row and its real column labels."""
    return _Mech(_Ann(
        [_Row("Asset Writedown ($M)",
              [None, None, None, -3.0, None, None, None, None, -60.9, -391.9, None, None])],
        ["FY17 (R)", "FY18", "FY19", "FY20", "FY21 (R)", "FY22 (R)", "FY23 (R)", "FY24", "FY25",
         "LTM", "FY26E", "FY27E"]))


# --- the two real runs --------------------------------------------------------------------------


def test_the_good_run_passes() -> None:
    """07-29 cites both figures. A guard that fired here would block every correct build."""
    assert uncited_material_figures(_Synth(GOOD), _smpl_mech()) == []  # type: ignore[arg-type]


def test_the_bad_run_is_refused_and_names_the_missing_figure() -> None:
    """THE RED. 07-30 omitted -391.9 while citing a real-but-wrong $249M."""
    out = uncited_material_figures(_Synth(BAD), _smpl_mech())  # type: ignore[arg-type]
    assert len(out) == 1, out
    assert "391.9" in out[0] and "LTM" in out[0], out[0]
    assert "60.9" not in out[0], "60.9 IS cited; only the uncited figure may be reported"


def test_a_plausible_wrong_figure_does_not_satisfy_the_check() -> None:
    """The distinction that makes this presence-based. $249M is a REAL charge — every number in the
    bad run was plausible, so a plausibility check would have passed it. Only the material row's
    own figure counts."""
    out = uncited_material_figures(_Synth(BAD), _smpl_mech())  # type: ignore[arg-type]
    assert out, "a prose full of plausible figures still omitted the material one"


# --- the matcher, which is where this guard could quietly certify a wrong page --------------------


def test_a_bare_number_is_not_a_citation() -> None:
    """MEASURED WHILE BUILDING THIS. An unanchored matcher reported 391.9 as cited when the only
    match was `$1,392M` of REVENUE, and reported 3.0 as cited off `3.6%`. A guard that reads a
    false citation is worse than no guard — it certifies the page."""
    assert not _figure_cited("revenue at $1,392M LTM remains far above pre-2021 levels", 391.9)
    assert not _figure_cited("OWYN grew 3.6% in Q3 2026", 3.0)
    assert not _figure_cited("a 60.9 percent gross margin", 60.9)


@pytest.mark.parametrize(
    "prose",
    ["a $391.9M LTM asset writedown", "a $391.9 million writedown", "391.9M of writedowns",
     "$392M written off", "a $1,234.5M charge"],
)
def test_currency_and_scale_markers_are_accepted(prose: str) -> None:
    """The forms filers and the model actually use — $X M, $X million, bare X M, and rounded."""
    val = 1234.5 if "1,234" in prose else 391.9
    assert _figure_cited(prose, val), prose


@pytest.mark.parametrize(
    "prose",
    ["a $1.5bn goodwill impairment", "a $1.5 billion goodwill impairment", "$1.5B written off",
     "the $1.52bn charge", "1.5bn of goodwill went", "a $1,523.3M impairment", "$1,523M gone"],
)
def test_a_figure_past_a_billion_may_be_cited_in_billions(prose: str) -> None:
    """THE RED, and it BLOCKED A DELIVERY. Rows are stored in $M and the matcher only knew millions
    forms, so `$1.5bn` against CNXC's −1,523.3 goodwill impairment read as UNCITED — the guard would
    have REFUSED a correct page. −1,523.3 is one of only TWO guarded figures on the corpus, so the
    blind spot sat exactly where the guard applies, and re-assembling CNXC had to wait for this.

    Worth its own line as a pattern: a guard's own coverage gap became the precondition for
    delivering the artifact pass that the PREVIOUS guard existed to make safe."""
    assert _figure_cited(prose, 1523.3), prose


@pytest.mark.parametrize(
    ("prose", "value"),
    [("a $391M writedown", 391.9),          # truncation, not rounding
     ("a $390M writedown", 391.9),          # two significant figures
     # THE case that pins the sub-$1bn guard: 391.9 → "0.4" at 1 dp, so without the guard this
     # WOULD match. Verified by mutation — removing the guard reds this one and nothing else.
     ("a $0.4bn writedown", 391.9),
     ("a $2bn impairment", 1523.3),         # "$2bn" is lossy for 1.5233bn
     ("a $1.6bn impairment", 1523.3),       # a NEARBY billions figure is not this one
     # a far-away billions figure, at the other scale. NOTE: this passes with or without the
     # sub-$1bn guard — the comment here used to claim it pinned that guard, which mutation
     # disproved. Kept as a plain distance case; `$0.4bn` above is the guard's actual pin.
     ("a $1.5bn impairment", 391.9)],
)
def test_the_scale_pass_does_not_widen_the_tolerance(prose: str, value: float) -> None:
    """The negative half, and the reason the fix is scale-only. Accepting a 2-s.f. restatement would
    let a NEARBY-BUT-DIFFERENT figure satisfy the check — the false certification this guard exists
    to prevent, and the exact shape of the original incident ($249M cited against a −391.9 row).
    Every case here is a form a careless synthesis could produce while omitting the real figure."""
    assert not _figure_cited(prose, value), f"{prose!r} must not satisfy {value}"


def test_the_one_dp_billions_form_loses_precision_the_millions_path_kept() -> None:
    """REVIEW FINDING, pinned as a KNOWN LIMITATION rather than fixed. "$1.5bn" spans a ±50M bucket,
    so two material rows inside one bucket would cross-satisfy: citing either would mark the other
    cited. That is the unavoidable cost of accepting the form a human actually writes, and it is
    strictly narrower than the millions path, which matches to 0.1M.

    NOT fixed here because detecting a collision needs every guarded figure at once, which
    ``_figure_cited`` does not have and ``uncited_material_figures`` does — the fix belongs in the
    caller, and only once a collision exists. Today's corpus has three distinct guarded figures and
    no two share a bucket. Pinned so the exposure is a recorded decision, and so this test reds the
    day someone widens the bucket further."""
    assert _figure_cited("a $1.5bn charge", 1549.0), (
        "the ±50M bucket is real — if this ever stops being true the limitation changed")
    # …and it is bounded: a figure a full bucket away is still refused.
    assert not _figure_cited("a $1.5bn charge", 1650.0)


def test_an_exact_three_dp_billions_citation_is_accepted() -> None:
    """REVIEW FINDING. `$1.523bn` is an EXACT citation of −1,523.3 and was refused — the same false
    refusal this PR exists to close, one scale up. Adding 3 dp is exactness, not tolerance."""
    assert _figure_cited("the $1.523bn goodwill charge", 1523.3)


def test_the_bare_integer_threshold_matches_the_millions_path_on_relative_error() -> None:
    """REVIEW FINDING, and it is a widening the PR claimed not to make. The first cut gated the bare
    integer on ``|b - round(b)| < 0.05`` — an ABSOLUTE ±50M rule on a check whose other branch is
    effectively relative. Measured, that accepted:

        $2bn vs 1,951.0  ->  True   (2.51% off)

    while the millions path REFUSES:

        $391M vs 391.9   ->  False  (0.23% off)

    An order of magnitude looser, on the one branch whose whole claim was "scale, not tolerance",
    and it is exactly the failure this guard exists to prevent — a nearby-but-different figure
    satisfying the check while the real one goes uncited. At 0.005 the worst accepted error is
    ~0.25%, in line with the millions path.

    Distinct from the ±50M bucket pinned above: that bucket buys a form humans actually write
    ("$1.5bn"), whereas the bare integer has an exact alternative already accepted ("$2.0bn")."""
    assert _figure_cited("a $2bn impairment", 2000.4)        # 0.02% — a genuinely round billion
    assert not _figure_cited("a $2bn impairment", 1990.0)    # 0.50% — millions refuses 0.48%
    assert not _figure_cited("a $2bn impairment", 1951.0)    # 2.51% — accepted by the first cut
    assert not _figure_cited("a $2bn impairment", 1523.3)    # 31%  — never in doubt
    # the exact form stays available at every scale, which is why tightening costs nothing
    assert _figure_cited("a $1.951bn impairment", 1951.0)


def test_a_round_billion_is_accepted_as_a_bare_integer() -> None:
    """The one place the integer form is legitimate: when the value really is that round. Pinned
    beside its refusal above so the boundary is a decision rather than an accident."""
    assert _figure_cited("a $2bn impairment", 2000.4)      # 2.0004bn → "$2bn" is fair
    assert not _figure_cited("a $2bn impairment", 1523.3)  # 1.5233bn → "$2bn" is not


def test_tiny_figures_are_out_of_scope_and_say_why() -> None:
    """SMPL's row also carries -3.0. It is excluded: a bare "3" cannot be told from prose noise,
    and a $3M writedown is not the class of error this exists to catch. Pinned so the floor is a
    decision rather than an accident."""
    assert MATERIAL_FIGURE_FLOOR_MUSD == 10.0
    out = uncited_material_figures(_Synth(GOOD), _smpl_mech())  # type: ignore[arg-type]
    assert not any("-3.0" in o for o in out)


# --- scope: the guard must not fire where there is nothing to check -------------------------------


def test_a_non_material_row_is_not_guarded() -> None:
    """Only rows the materiality pass flagged. Guarding every row would demand the synthesis recite
    the whole financial summary, which is not an argument."""
    mech = _Mech(_Ann([_Row("Revenue ($M)", [1000.0, 2000.0], material=False)], ["FY24", "FY25"]))
    assert uncited_material_figures(_Synth("no figures here"), mech) == []  # type: ignore[arg-type]


def test_a_build_with_no_financial_summary_is_not_refused() -> None:
    """Absent input is not a violation — the guard has nothing to check, and refusing there would
    be the guard-that-cannot-fire class inverted into a guard that fires on absence."""
    class _Empty:
        financial_summary = None

    assert uncited_material_figures(_Synth("x"), _Empty()) == []  # type: ignore[arg-type]


def test_a_forecast_column_is_not_guarded() -> None:
    """REVIEW FINDING. The summary carries FY26E/FY27E and a per-column `is_estimate` mask.
    Demanding the prose state a FORECAST would require the argument to cite a projection as though
    it were a fact. No material value lands in an estimate column on today's corpus, so this was a
    LATENT false positive — closed because the flag exists and ignoring it is an unasserted
    assumption about which columns are actuals."""
    mech = _Mech(_Ann([_Row("Asset Writedown ($M)", [None, -500.0])], ["FY25", "FY26E"],
                      is_estimate=[False, True]))
    assert uncited_material_figures(_Synth("no figures"), mech) == []  # type: ignore[arg-type]
    # and the same value in an ACTUAL column is still guarded
    mech2 = _Mech(_Ann([_Row("Asset Writedown ($M)", [-500.0, None])], ["FY25", "FY26E"],
                       is_estimate=[False, True]))
    assert uncited_material_figures(_Synth("no figures"), mech2)  # type: ignore[arg-type]


def test_one_figure_repeated_across_columns_is_reported_once() -> None:
    """REVIEW FINDING. CNXC's -1,523.3 appears in BOTH FY25 and LTM. Citing it once satisfies the
    reader for both, so reporting it twice would inflate the count and read as two distinct
    omissions. The refusal names a FIGURE and lists the periods it spans."""
    mech = _Mech(_Ann([_Row("Impairment of Goodwill ($M)", [-1523.3, -1523.3])], ["FY25", "LTM"]))
    out = uncited_material_figures(_Synth("no figures here"), mech)  # type: ignore[arg-type]
    assert len(out) == 1, out
    assert "FY25/LTM" in out[0] and "1,523.3" in out[0], out[0]


# --- the wiring: a guard nobody calls is not a guard ---------------------------------------------


def test_the_guard_is_wired_as_a_refusal_before_the_write() -> None:
    """THE WIRING PIN. Everything above drives `uncited_material_figures` directly, which leaves the
    CALL SITE unpinned — and disabling the call reds none of it. That is the same gap that let the
    freshness gate ship measuring the wrong date.

    Three properties, all of which the incident depends on: the guard is CALLED, it RAISES rather
    than appending a flag (a flag moves the judgement back to a human on every run), and it raises
    BEFORE `_write` (a refusal after the write leaves the bad artifact on disk)."""
    import inspect

    from vinci.dossier import assemble as asm

    src = inspect.getsource(asm.assemble_one)
    # the EXACT condition, not just the call appearing: `if False and uncited_material_figures(...)`
    # still contains the call, and a pin that matched the name alone passed that mutation.
    cond = "if (uncited := uncited_material_figures(synthesis, mech)):"
    assert cond in src, "the guard is not called, or its condition was disabled"
    call = src.index(cond)
    assert "raise DossierAssemblyError" in src[call:call + 700], (
        "the guard must REFUSE, not flag — a flag re-delegates the judgement to a human")
    assert call < src.index("_write(dossier"), "the refusal must precede the artifact write"


def test_the_guard_runs_after_the_flags_it_reads() -> None:
    """IT HAD NEVER FIRED. The guard sat ABOVE `_mark_material`, so it read a table on which no row
    carried `material=True` — `uncited_material_figures` skips unflagged rows, so it found nothing
    to check and returned `[]` on every build since it shipped.

    THE PINS IN THIS FILE PASSED THROUGHOUT, because they CONSTRUCT rows with `material=True`: the
    fixture supplied the exact state production never reached. That is the sharpest form of the
    ladder — a unit test can hand a function an input the caller never produces, and no amount of
    green says the caller does.

    ORDER IS THE WHOLE GUARANTEE HERE, so order is what gets pinned.
    """
    import ast
    import inspect

    from vinci.dossier import assemble as da

    tree = ast.parse(inspect.getsource(da))
    calls = {name: min(n.lineno for n in ast.walk(tree)
                       if isinstance(n, ast.Call) and name in ast.dump(n))
             for name in ("_mark_material", "uncited_material_figures")}
    assert calls["_mark_material"] < calls["uncited_material_figures"], (
        f"`uncited_material_figures` (line {calls['uncited_material_figures']}) runs BEFORE "
        f"`_mark_material` (line {calls['_mark_material']}) — so it reads a table with no material "
        "rows, finds nothing, and CANNOT FIRE. That is how it shipped, and how SMPL re-assembled "
        "green while omitting its own -$391.9M writedown.")


#: FROZEN. The shape the 2026-07-30 page actually shipped: a bear point arguing impairment while
#: naming NO figure. Frozen because the committed synthesis was REPAIRED on 2026-08-03 and now
#: cites $391.9M — driving this off the living page made the assertion VACUOUS (`[]` with the flags
#: stripped and `[]` with them applied), so a test written to prove the guard can fire would have
#: passed while proving nothing. TEST-LAYER RULE: a value-level pin lives on a frozen fixture,
#: never on the re-drawn artifact.
_PRE_REPAIR_PROSE = (
    "GAAP earnings have crossed to loss driven by impairments on acquired brand assets — "
    "evidence the OWYN/Atkins asset values are being written down."
)


def test_the_guard_fires_on_the_real_committed_shape() -> None:
    """BEHAVIOURAL COMPANION to the ordering pin. The MECHANICAL side stays LIVE — read from the
    committed artifact and flagged by `_mark_material` itself, because a constructed row is exactly
    what hid the defect and `_mark_material` is the function whose ordering was wrong. Only the
    prose is frozen."""
    import json
    from pathlib import Path

    from vinci.dossier.assemble import _mark_material
    from vinci.dossier.schemas import MechanicalLayer

    root = Path(__file__).resolve().parents[1]
    doc = json.loads((root / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    stripped = json.loads(json.dumps(doc["mechanical"]))
    for r in stripped["financial_summary"]["annual"]["value"]["rows"]:
        r["material"] = False                    # the state the assembler hands over
    unflagged = MechanicalLayer.model_validate(stripped)
    synth = _Synth(_PRE_REPAIR_PROSE)
    assert uncited_material_figures(synth, unflagged) == [], (
        "precondition: with no rows flagged the guard is blind — this is the defect, pinned so "
        "the ordering test above cannot be read as arbitrary")
    fired = uncited_material_figures(synth, _mark_material(unflagged))
    assert fired, (
        "with the flags applied the guard must see SMPL's writedown against prose that names no "
        "figure; empty here means the committed financial summary lost its material row")
    assert any("391.9" in f for f in fired), fired


# --- LARGEST-VALUE KEYING (operator ruling 2026-08-03) -----------------------------------------

#: SMPL's real row: one event at two horizons. LTM 391.9 = YTD FY26 331.0 + FY25 Q4 60.9.
_SMPL_ROW = _Row("Asset Writedown ($M)", [None, -3.0, -60.9, -391.9], material=True)
_SMPL_ANN = _Ann([_SMPL_ROW], ["FY23", "FY24", "FY25", "LTM"])


def _uncited(prose: str, ann=_SMPL_ANN) -> list[str]:
    return uncited_material_figures(_Synth(prose), _Mech(ann))


def test_the_original_audit_defect_still_refuses() -> None:
    """THE ACCEPTANCE CASE, and it had never been tested against production state. Citing only the
    $60.9M FY25 impairment beside a row showing −392 IS audit P1 — the bear case arguing from a
    figure 5.3x smaller than the event. A per-ROW rule would accept this; largest-value does not."""
    assert _uncited("A $60.9M non-cash Atkins impairment drove the FY25 loss.")


def test_citing_the_largest_alone_is_enough() -> None:
    """THE ASYMMETRY, AND ITS REASON. Citing 60.9 without 391.9 UNDERSTATES by 6.4x; citing 391.9
    without 60.9 misleads nobody, because 60.9 is a COMPONENT of it. The harm runs one way, so the
    rule does too — and this is what makes the guard satisfiable at all."""
    assert _uncited("Management wrote down $391.9M of brand assets over the trailing year.") == []


def test_citing_both_is_also_enough() -> None:
    assert _uncited("A $60.9M FY25 Atkins impairment, part of $391.9M written down LTM.") == []


def test_a_repeated_charge_still_needs_one_citation() -> None:
    """CNXC'S SHAPE — the same value in two columns. It passed before and must keep passing: one
    citation covers both cells because there is only one number."""
    ann = _Ann([_Row("Impairment of Goodwill ($M)", [None, -1523.3, -1523.3], material=True)],
               ["FY24", "FY25", "LTM"])
    assert _uncited("A $1,523.3M goodwill impairment.", ann) == []
    assert _uncited("Goodwill was written down.", ann)


def test_a_figure_below_the_floor_is_never_demanded() -> None:
    """The −3.0 cell must not become the demanded figure just because it is the only other one."""
    ann = _Ann([_Row("Asset Writedown ($M)", [-3.0, -391.9], material=True)], ["FY23", "LTM"])
    out = _uncited("Management wrote down $391.9M.", ann)
    assert out == [], out


def test_the_known_limit_is_a_limit_not_a_bug() -> None:
    """RECORDED RATHER THAN DISCOVERED (operator). A row whose LARGEST value is OLD and whose
    RECENT value is small demands the stale event and lets the current one pass unmentioned.

    NOT LIVE on today's corpus — SMPL's and CNXC's largest values are both current — and pinned so
    the behaviour is a documented edge rather than a surprise. If a real name ever takes this shape,
    the keying needs a recency term and this test is where that argument starts.
    """
    ann = _Ann([_Row("Asset Writedown ($M)", [-500.0, -25.0], material=True)], ["FY22", "LTM"])
    assert _uncited("A $25M writedown this year.", ann), "the stale-largest limit changed"
    assert _uncited("A $500M writedown back in FY22.", ann) == [], (
        "citing the old, larger figure satisfies the guard while the CURRENT $25M goes unmentioned "
        "— this is the known limit, not a regression")
