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


def test_the_persisted_model_refuses_an_unlisted_sleeve() -> None:
    """REVIEW FINDING (PR-1a self-review). The registry validated the followed.json EDGE, but
    `Dossier.sleeve` was a bare `str` — so any OTHER writer could persist an unlisted strategy into
    a committed artifact, and a reader would meet a sleeve no registry row defines with no framing
    to apply. Edge-only validation guards one writer; the MODEL guards every writer, which is why
    `ScenarioInput.bear_basis` validates on the model rather than at its callers.

    The legacy case is pinned beside it: a dossier that OMITS the field — every artifact committed
    before the tag, and the sealed FUBO record that must not be rewritten — still loads and reads
    as `overshoot`, which is truthful for all of them since the screen was their only route.
    CORPUS BEFORE SYNTHETIC: the base document is a REAL committed dossier, not a dict hand-rolled
    to the shape this test wants — a fixture built to fit would have let the field's own model
    dictate what "valid" means, and `MechanicalLayer` alone has a dozen required blocks."""
    import json

    from pydantic import ValidationError

    from vinci.dossier.schemas import Dossier

    committed = sorted((SRC.parents[1] / "data" / "dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this worktree")
    base = json.loads(committed[0].read_text())
    base.pop("sleeve", None)

    for bad in ("momentum", "", "   ", "OVERSHOOT", "Quality"):
        with pytest.raises(ValidationError):
            Dossier.model_validate({**base, "sleeve": bad})
    for good in sorted(sl.SLEEVES):
        assert Dossier.model_validate({**base, "sleeve": good}).sleeve == good
    assert Dossier.model_validate(base).sleeve == sl.DEFAULT_SLEEVE, (
        "a dossier committed before the tag existed must still load, reading as the default")


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


# ------------------------------------------------------------------ the LEDGER side (PR-1b)


def test_a_legacy_ledger_row_reads_screen_and_overshoot() -> None:
    """THE ADDITIVE-FIELD CONTRACT, on the fields that decide which curve a row lands in.

    Every committed row predates these fields and carries None for both. Their truthful reading is
    screen/overshoot — not a convenient default: `log_verdict` REFUSED any name without a
    CandidateRecord, so no other route could reach this ledger at all, and overshoot was the only
    strategy. Read through the helpers so a legacy row and a tagged row answer identically."""
    import json
    import pathlib

    from vinci.schemas.ledger import LedgerEntry, origin_of, sleeve_of

    p = pathlib.Path(__file__).resolve().parents[1] / "data/snapshots/decision_ledger.jsonl"
    if not p.exists():
        pytest.skip("no committed ledger in this worktree")
    rows = [LedgerEntry.model_validate_json(json.loads(x)["payload"])
            for x in p.read_text().splitlines() if x.strip()]
    assert rows, "the committed ledger is empty — nothing to assert on"
    for e in rows:
        assert e.origin is None and e.sleeve is None, (
            f"{e.entry_id} was BACKFILLED — a sealed row is never rewritten to satisfy a later "
            f"schema; absent is the record of when it was logged")
        assert origin_of(e) == "screen" and sleeve_of(e) == sl.DEFAULT_SLEEVE


@pytest.mark.parametrize(("field", "bad"), [
    ("origin", "backdoor"), ("origin", ""), ("sleeve", "momentum"), ("sleeve", "OVERSHOOT")])
def test_the_ledger_row_refuses_an_unlisted_origin_or_sleeve(field: str, bad: str) -> None:
    """ABSENT is legal (legacy); PRESENT-BUT-UNKNOWN is a typo that would drop the row out of every
    filtered curve without saying so — the silent-drop this segmentation exists to prevent."""
    import json
    import pathlib

    from pydantic import ValidationError

    from vinci.schemas.ledger import LedgerEntry

    p = pathlib.Path(__file__).resolve().parents[1] / "data/snapshots/decision_ledger.jsonl"
    if not p.exists():
        pytest.skip("no committed ledger in this worktree")
    base = json.loads(json.loads(p.read_text().splitlines()[0])["payload"])
    with pytest.raises(ValidationError):
        LedgerEntry.model_validate({**base, field: bad})


def test_the_primary_spread_counts_screen_origin_only() -> None:
    """THE OPERATOR'S 2026-08-07 DECISION, pinned as behaviour rather than prose.

    The spread is the fund's proof and it measures the discriminator ON the $300M–$10B hunting
    ground. A followed megacap verdict must not move it — pooling silently changes what the number
    means. Built so the followed rows would CHANGE the answer if they counted, which is what makes
    this a measurement rather than a restatement."""
    from vinci.schemas.ledger import Verdict
    from vinci.scoring.metrics import VerdictScore, aggregate

    def score(tag: str, v: Verdict, ret: float, origin: str, sleeve: str) -> VerdictScore:
        return VerdictScore(entry_id=tag, ticker=tag, verdict=v, resolved=True,
                            name_return=ret, bench_return=0.0, origin=origin, sleeve=sleeve)

    screen_only = [score("A", Verdict.BUY, 0.20, "screen", "overshoot"),
                   score("B", Verdict.AVOID_TERMINAL, 0.05, "screen", "overshoot")]
    baseline = aggregate(screen_only, cost_bps=0, n_pending=0)
    with_followed = aggregate(
        [*screen_only, score("U", Verdict.BUY, 5.00, "followed", "quality")],
        cost_bps=0, n_pending=0)

    assert baseline.buy_avoid_spread == with_followed.buy_avoid_spread, (
        "a FOLLOWED verdict moved the primary spread — the fund's proof number now measures "
        "something other than the hunting ground it claims to measure")
    assert with_followed.n_resolved_buy == baseline.n_resolved_buy, (
        "the followed row was counted in the primary BUY leg")
    assert "quality" in with_followed.by_sleeve, "the followed row vanished from every curve"
    assert with_followed.by_sleeve["quality"].n_long == 1


def test_each_sleeve_curve_uses_its_own_leg_labels() -> None:
    """THE HAZARD THE EXACT-IDENTITY FILTERS COULD NOT SEE. `scoring` matched
    `Verdict.AVOID_TERMINAL` by identity, so a verdict belonging to another book's vocabulary would
    land in NEITHER leg and disappear from the report with nothing raised. The per-sleeve curve
    reads its labels from the registry, and a verdict matching neither leg RAISES."""
    from vinci.schemas.ledger import Verdict
    from vinci.scoring.metrics import VerdictScore, spread_by_sleeve

    rows = [VerdictScore(entry_id="A", ticker="A", verdict=Verdict.BUY, resolved=True,
                         name_return=0.2, bench_return=0.0, sleeve="overshoot"),
            VerdictScore(entry_id="B", ticker="B", verdict=Verdict.AVOID_TERMINAL, resolved=True,
                         name_return=0.05, bench_return=0.0, sleeve="overshoot")]
    out = spread_by_sleeve(rows)
    assert out["overshoot"].spread == pytest.approx(0.15)

    # AVOID_TERMINAL is not in quality's vocabulary — it must not be silently ignored.
    with pytest.raises(ValueError, match="neither of its legs"):
        spread_by_sleeve([VerdictScore(entry_id="U", ticker="U", verdict=Verdict.AVOID_TERMINAL,
                                       resolved=True, name_return=0.1, bench_return=0.0,
                                       sleeve="quality")])
