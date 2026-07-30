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
    def __init__(self, rows: list[_Row], columns: list[str]) -> None:
        self.rows, self.columns = rows, columns


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
