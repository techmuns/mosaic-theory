"""The sleeve registry — the vocabulary that keeps one engine serving more than one strategy.

These pins guard the two things that make a registry cheaper than a fork: every sleeve is COMPLETE
(so sleeve N+1 cannot half-land and silently inherit overshoot's framing), and the module stays a
VOCABULARY (it concludes nothing and reads no returns).
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from vinci import sleeves as sl

SRC = pathlib.Path(sl.__file__)


def test_every_sleeve_row_is_complete() -> None:
    """THE CONFORMANCE PIN — a half-added sleeve fails loud instead of inheriting a default.

    Phase 2 threads the registry into the synthesis prompt, the proposal mapping and the page
    copy. A row missing its bet or its twin would reach that code as an empty string and render as
    a blank question rather than an error, which is the silent-default failure the whole sleeve
    design exists to remove. Checked per FIELD rather than by counting rows, so adding a sleeve
    without filling it in reddens here."""
    assert sl.SLEEVE_ROWS, "the registry is empty"
    for s in sl.SLEEVE_ROWS:
        for field in ("key", "label", "bet", "twin", "question", "entry", "kill"):
            value = getattr(s, field)
            assert isinstance(value, str) and value.strip(), (
                f"sleeve {s.key!r} has an empty {field!r} — an incomplete row reaches Phase 2 as a "
                f"blank prompt/question rather than an error")
        assert len(s.verdicts) == 2, (
            f"sleeve {s.key!r} must name exactly two verdict labels (the long leg and the leg it "
            f"is measured against); got {s.verdicts!r}")
        assert all(v and v.isupper() for v in s.verdicts), (
            f"sleeve {s.key!r} verdict labels must be non-empty and upper-case: {s.verdicts!r}")
        assert s.verdicts[0] != s.verdicts[1], (
            f"sleeve {s.key!r} names one label twice — a spread of a leg against itself is zero "
            f"by construction and would read as 'no edge' forever")


def test_keys_derive_from_the_rows_and_never_drift() -> None:
    """SLEEVES is DERIVED, never a second hand-maintained list — the dual-write this repo refuses.
    A hardcoded copy is how a row gets added and the validator keeps rejecting it."""
    assert frozenset(s.key for s in sl.SLEEVE_ROWS) == sl.SLEEVES
    assert set(sl.BY_KEY) == sl.SLEEVES
    assert len({s.key for s in sl.SLEEVE_ROWS}) == len(sl.SLEEVE_ROWS), "duplicate sleeve key"
    assert sl.DEFAULT_SLEEVE in sl.SLEEVES


def test_the_default_is_overshoot_because_that_is_what_the_screen_finds() -> None:
    """Not an arbitrary default: `screens/screen2.py` finds overshoot SETUPS, so a screen-route
    name is overshoot by construction. Pinned because changing it silently re-frames every
    screen-route dossier and every legacy artifact that omits the field."""
    assert sl.DEFAULT_SLEEVE == "overshoot"


def test_the_two_ledger_active_sleeves_are_overshoot_and_quality() -> None:
    """v1 SCOPE, pinned so it is a DECISION rather than a drift. `theme` validates in its own
    append-only ratification ledger and `neglect` is defined but dormant; a defined-but-inactive
    sleeve is deliberately not the same thing as an unknown one, and flipping one on is a
    deliberate edit that reddens here first."""
    assert {s.key for s in sl.SLEEVE_ROWS if s.ledger_active} == {"overshoot", "quality"}


def test_the_quality_twin_is_priced_not_terminal() -> None:
    """THE DEFECT THIS REGISTRY EXISTS TO FIX. Recording "terminal" on a fully-priced compounder
    would be a FALSE RECORD in an append-only ledger. Asserted on the STRUCTURED fields — the twin
    text and the verdict label — never on prose that could be reworded."""
    q = sl.BY_KEY["quality"]
    assert q.verdicts == ("BUY", "PASS")
    assert "terminal" not in q.twin.lower()
    assert "AVOID_TERMINAL" not in q.verdicts
    assert sl.BY_KEY["overshoot"].verdicts == ("BUY", "AVOID_TERMINAL"), (
        "the live book's vocabulary moved — every committed ledger row uses it")


@pytest.mark.parametrize(
    "bad", [None, "", "   ", "momentum", "OVERSHOOT", "Quality", 7, True, ["quality"]])
def test_require_sleeve_refuses_and_names_the_admissible_set(bad: object) -> None:
    """CASE-SENSITIVE ON PURPOSE. Quietly upper/lower-casing a key is the silent coercion the
    fail-loud rule refuses — the value is persisted in committed artifacts, so one spelling has to
    win and the file has to say which. Every refusal names the set, because the fix is a hand-edit
    elsewhere and a bare "unknown sleeve" leaves the reader hunting."""
    with pytest.raises(sl.UnknownSleeveError) as exc:
        sl.require_sleeve(bad, where="data/followed.json: ZZZZ")
    msg = str(exc.value)
    assert "overshoot" in msg and "quality" in msg, f"refusal hides the admissible set: {msg}"
    assert "data/followed.json: ZZZZ" in msg, (
        f"refusal does not name WHERE the bad value lives, so the fix is unlocatable: {msg}")


def test_require_sleeve_accepts_every_defined_key_and_trims() -> None:
    for key in sorted(sl.SLEEVES):
        assert sl.require_sleeve(key, where="t") == key
        assert sl.require_sleeve(f"  {key}  ", where="t") == key


def test_the_registry_concludes_nothing_and_reads_no_returns() -> None:
    """THE LINE THAT MUST NOT BLUR (the ranker/themes AST-guard class, applied here). A sleeve is a
    VOCABULARY — it says which question to ask, never what the answer is. If this module ever
    imports scoring/ledger or grows a returns-shaped name, the registry has started deciding, and
    a face-validity-frozen mapping tuned on outcomes is the exact failure this fund exists to
    avoid. Checked on the AST, so a mention inside a docstring cannot trip it."""
    tree = ast.parse(SRC.read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    for mod in imported:
        assert not mod.startswith(("vinci.scoring", "vinci.ledger", "vinci.schemas.ledger")), (
            f"the registry imports {mod} — a vocabulary must not reach the decision/scoring layer")
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    forbidden = {"forward_return", "forward_returns", "name_return", "excess_gross", "spread"}
    assert not (names & forbidden), f"registry reads outcome data: {sorted(names & forbidden)}"
