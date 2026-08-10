"""The sleeve registry — the vocabulary that keeps one engine serving more than one strategy.

These pins guard the two things that make a registry cheaper than a fork: every sleeve is COMPLETE
(so sleeve N+1 cannot half-land and silently inherit overshoot's framing), and the module stays a
VOCABULARY (it concludes nothing and reads no returns).
"""

from __future__ import annotations

import ast
import pathlib
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from vinci import sleeves as sl
from vinci.schemas.market import PriceBar

SRC = pathlib.Path(sl.__file__)


def _mech() -> Any:
    """A REAL MechanicalLayer from a committed dossier — the synthesis path walks it, so a
    hand-rolled stand-in would shape the test rather than exercise the code (the fixture rule)."""
    import json

    from vinci.dossier.schemas import Dossier

    committed = sorted((SRC.parents[1] / "data" / "dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this worktree")
    return Dossier.model_validate(json.loads(committed[0].read_text())).mechanical


def test_every_sleeve_row_is_complete() -> None:
    """THE CONFORMANCE PIN — a half-added sleeve fails loud instead of inheriting a default.

    Phase 2 threads the registry into the synthesis prompt, the proposal mapping and the page
    copy. A row missing its bet or its twin would reach that code as an empty string and render as
    a blank question rather than an error, which is the silent-default failure the whole sleeve
    design exists to remove. Checked per FIELD rather than by counting rows, so adding a sleeve
    without filling it in reddens here.

    THE FIELD LIST IS DERIVED, NOT RESTATED. It used to name seven fields by hand while the row
    carries twenty-three, so the fifteen render/prompt strings the later PRs added — the case
    labels, the page headings, the CLI help copy — were unchecked: a new sleeve passing `""` for
    `bull_case` imported cleanly and rendered a blank prompt section, which is the exact
    silent-default failure this pin exists to catch. A hand-kept list guards the fields someone
    remembered, and the registry grows precisely when someone is not remembering.

    (Omitting a field outright is already impossible — no field carries a default, so the
    dataclass raises at import. This pin covers the case the type system cannot see: present but
    empty.)"""
    import dataclasses

    assert sl.SLEEVE_ROWS, "the registry is empty"
    # UNION of the declared annotation and the runtime value, because either alone leaves a hole:
    # matching only on the annotation re-introduces a hand-maintained assumption (the literal
    # spelling "str"), so a field annotated any other way would be SILENTLY skipped — the very
    # failure this derivation removes; matching only on the runtime value would skip a str-declared
    # field that a row filled with the wrong type, instead of failing on it.
    probe = sl.SLEEVE_ROWS[0]
    str_fields = [f.name for f in dataclasses.fields(probe)
                  if f.type in ("str", str) or isinstance(getattr(probe, f.name), str)]
    assert len(str_fields) >= 20, (
        f"only {len(str_fields)} string fields discovered ({str_fields}) — the derivation broke "
        f"and this pin is now checking less than it did when it was a hand-written list")
    for s in sl.SLEEVE_ROWS:
        for field in str_fields:
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


def test_pass_is_a_first_class_verdict_with_its_own_leg() -> None:
    """PASS BROUGHT FORWARD INTO PR-1b (operator decision). Without it `quality` had a vocabulary
    it could not record — a book able to log its long leg and not its short one accumulates a
    one-sided curve, which is worse than no curve.

    Pinned as BEHAVIOUR, not membership: the quality curve is BUY−PASS and the primary is unmoved
    by either. A membership-only assertion is what the old shelf pin was, and it went red the
    moment the enum grew rather than describing what must stay true."""
    from vinci.schemas.ledger import Verdict
    from vinci.scoring.metrics import VerdictScore, aggregate

    assert Verdict.PASS.value == "PASS"

    def s(tag: str, v: Verdict, ret: float, origin: str, sleeve: str) -> VerdictScore:
        return VerdictScore(entry_id=tag, ticker=tag, verdict=v, resolved=True, name_return=ret,
                            bench_return=0.0, origin=origin, sleeve=sleeve)

    screen = [s("A", Verdict.BUY, 0.20, "screen", "overshoot"),
              s("B", Verdict.AVOID_TERMINAL, 0.05, "screen", "overshoot")]
    both = aggregate([*screen,
                      s("U", Verdict.BUY, 0.40, "followed", "quality"),
                      s("V", Verdict.PASS, 0.05, "followed", "quality")],
                     cost_bps=0, n_pending=0)
    assert both.buy_avoid_spread == aggregate(screen, cost_bps=0, n_pending=0).buy_avoid_spread, (
        "a quality BUY/PASS pair moved the primary spread")
    q = both.by_sleeve["quality"]
    assert (q.n_long, q.n_short) == (1, 1), "the PASS row did not land in quality's short leg"
    assert q.spread == pytest.approx(0.35)


def test_a_verdict_outside_its_sleeve_is_refused_before_the_seal() -> None:
    """REFUSED AT WRITE, NOT AT SCORE. The ledger is append-only, so a row recording another book's
    label cannot be un-logged — and it would fall out of that book's curve without appearing
    anywhere else. Both directions are pinned: PASS on the overshoot book is as wrong as
    AVOID_TERMINAL on the quality book, and the second is the one that would write 'terminal
    decline' against a durable compounder."""
    from vinci.ledger.workflow import LedgerError, _require_verdict_in_sleeve
    from vinci.schemas.ledger import Verdict

    _require_verdict_in_sleeve(Verdict.BUY, "quality")            # in-vocabulary: silent
    _require_verdict_in_sleeve(Verdict.PASS, "quality")
    _require_verdict_in_sleeve(Verdict.AVOID_TERMINAL, "overshoot")
    _require_verdict_in_sleeve(Verdict.PASS, None)                # legacy/untagged row: unchanged

    with pytest.raises(LedgerError, match="quality"):
        _require_verdict_in_sleeve(Verdict.AVOID_TERMINAL, "quality")
    with pytest.raises(LedgerError, match="overshoot"):
        _require_verdict_in_sleeve(Verdict.PASS, "overshoot")


def test_a_proposal_from_another_books_vocabulary_is_refused() -> None:
    """THE SUBTLER HALF. `disposition` is stamped by comparing the human verdict to the sealed
    machine proposal, so a proposal drawn from another book's vocabulary does not merely look odd
    — it seals OVERRIDDEN onto a row where the two may well have agreed, and the override subset
    is the most decision-relevant data the pivot produces.

    The proposal mapping is still GLOBAL (strongly-bearish → AVOID_TERMINAL for every name); the
    per-sleeve mapping lands in PR-2b. Until then a bearish-leaning quality name cannot be logged,
    and refusing is the honest answer — the alternative is a disagreement statistic measuring a
    vocabulary mismatch."""
    from vinci.ledger.workflow import LedgerError, _require_verdict_in_sleeve
    from vinci.schemas.ledger import Verdict

    _require_verdict_in_sleeve(Verdict.BUY, "quality", machine_proposal=Verdict.BUY)
    _require_verdict_in_sleeve(Verdict.PASS, "quality", machine_proposal=Verdict.PASS)
    _require_verdict_in_sleeve(Verdict.BUY, "quality", machine_proposal=None)   # no read: fine

    with pytest.raises(LedgerError, match="machine proposal"):
        _require_verdict_in_sleeve(Verdict.BUY, "quality",
                                   machine_proposal=Verdict.AVOID_TERMINAL)


def test_the_per_sleeve_curves_reach_the_markdown_a_reader_actually_gets() -> None:
    """OPERATOR P1 ON #378, and it is the repo's own rule: a fix is satisfied at the SURFACE WHERE
    THE HARM OCCURS. `by_sleeve` existed in `to_dict()` only, while BOTH default paths — `vinci
    score` (cli) and `run_monthly`'s committed `scoring_report.md` (orchestrator) — emit ONLY the
    markdown, with JSON opt-in. So a resolved followed verdict was correctly kept out of the
    primary and then invisible to every reader: scored, recorded, and appearing nowhere. That is
    worse than pooling it, because pooling at least shows up.

    PINNED ON THE MARKDOWN, not on `to_dict()`, for exactly the reason the defect existed — a pin
    on the machine tier would have passed throughout. Asserted on the STRUCTURED facts the row must
    carry (its own leg labels and counts), never on the surrounding prose."""
    from vinci.schemas.ledger import Verdict
    from vinci.scoring.metrics import VerdictScore, aggregate

    def s(tag: str, v: Verdict, ret: float, origin: str, sleeve: str) -> VerdictScore:
        return VerdictScore(entry_id=tag, ticker=tag, verdict=v, resolved=True, name_return=ret,
                            bench_return=0.0, origin=origin, sleeve=sleeve)

    md = aggregate([s("A", Verdict.BUY, 0.20, "screen", "overshoot"),
                    s("B", Verdict.AVOID_TERMINAL, 0.05, "screen", "overshoot"),
                    s("U", Verdict.BUY, 0.40, "followed", "quality"),
                    s("V", Verdict.PASS, 0.05, "followed", "quality")],
                   cost_bps=0, n_pending=0).to_markdown()

    assert "quality" in md, (
        "the quality book is absent from the report a reader is given — the followed verdict was "
        "excluded from the primary and then shown nowhere at all")
    assert "BUY−PASS" in md, "the quality curve does not state the legs it measures"
    assert "BUY−AVOID_TERMINAL" in md, "the overshoot curve does not state the legs it measures"
    # each book's counts must appear in ITS OWN row, not pooled
    sleeve_rows = [ln for ln in md.splitlines() if ln.startswith("- **")]
    assert any("quality" in ln and "+35.0%" in ln for ln in sleeve_rows), (
        f"the quality spread is missing or wrong in the rendered rows: {sleeve_rows}")
    assert any("overshoot" in ln and "+15.0%" in ln for ln in sleeve_rows), (
        f"the overshoot row does not reproduce the primary: {sleeve_rows}")


def test_the_primary_line_states_that_it_is_screen_origin_only() -> None:
    """THE NUMBER'S MEANING NARROWED, so the report has to say so. `buy_avoid_spread` used to cover
    every logged verdict; it now covers screen-origin overshoot only. A reader meeting an unlabelled
    "primary spread" would carry forward the old meaning — the silent redefinition this
    segmentation exists to prevent, arriving through the report instead of through the math."""
    from vinci.scoring.metrics import aggregate

    md = aggregate([], cost_bps=0, n_pending=0).to_markdown()
    head = md.split("## ")[0]
    assert "primary" in head.lower() and "creen-origin" in head, (
        f"the primary spread does not state its scope:\n{head}")


# ------------------------------------------------------------------ the PROMPT side (PR-2a)


def test_the_overshoot_prompt_is_byte_identical_to_the_pre_registry_text() -> None:
    """THE LIVE BOOK'S PROMPT CANNOT DRIFT AS A SIDE EFFECT of making the others possible.

    Every committed dossier's synthesis was produced by the pre-registry constants. Parameterising
    them is only safe if overshoot reproduces them EXACTLY — a one-word difference would silently
    re-frame every re-assembly of the live fleet, and synthesis is stochastic enough that nobody
    would attribute the change to this build.

    THE BASELINE IS EXTRACTED FROM GIT, not transcribed: a hand-copied expected string would be a
    restatement of the code rather than an independent check, and the probe rule says an
    instrument that restates cannot measure. AST-extracted so no module import side-effects run."""
    import ast
    import subprocess
    from typing import Any

    from vinci.dossier import synthesis as syn

    src = subprocess.run(
        ["git", "show", "origin/feat/sleeve-ledger:vinci/dossier/synthesis.py"],
        capture_output=True, text=True, cwd=SRC.parents[1])
    if src.returncode != 0 or not src.stdout:
        pytest.skip("pre-registry revision unavailable in this checkout")
    ns: dict[str, Any] = {"Any": Any}
    for node in ast.parse(src.stdout).body:
        name = None
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
        if name in {"SYNTHESIS_TOOL", "_SYSTEM", "_POINT", "_UNVERIFIED"}:
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<pre>", "exec"), ns)

    assert syn.system_for("overshoot") == ns["_SYSTEM"], (
        "the overshoot SYSTEM prompt changed — every committed synthesis was written under the old "
        "one, and a re-assembly would silently re-frame the live fleet")
    assert syn.tool_for("overshoot") == ns["SYNTHESIS_TOOL"], (
        "the overshoot TOOL schema changed — same hazard, and it also changes what the model is "
        "allowed to emit")
    # the historical names still resolve to the same objects, so no existing reader moved
    assert ns["_SYSTEM"] == syn._SYSTEM and ns["SYNTHESIS_TOOL"] == syn.SYNTHESIS_TOOL


def test_every_sleeve_builds_a_prompt_stating_its_own_two_cases() -> None:
    """THE POINT OF THE SWAP, asserted structurally rather than on wording. Each book's prompt must
    carry ITS OWN case definitions and no other book's — a sleeve silently inheriting overshoot's
    text is the exact defect (a megacap asked what broke when nothing did), and it would be
    invisible in a test that only checked the prompt was non-empty."""
    from vinci.dossier import synthesis as syn

    for key in sorted(sl.SLEEVES):
        row = sl.BY_KEY[key]
        system = syn.system_for(key)
        tool = syn.tool_for(key)
        props = tool["input_schema"]["properties"]
        assert row.subject in system, f"{key}: the prompt does not name its own subject"
        assert row.both_cases in system, f"{key}: rule 3 does not name this book's two readings"
        assert props["bull_points"]["description"].startswith(row.bull_case), (
            f"{key}: the bull case is not this book's own definition")
        assert props["bear_points"]["description"].startswith(row.bear_case), (
            f"{key}: the bear case is not this book's own definition")
        # and it must NOT carry another book's case definitions
        for other in sl.SLEEVE_ROWS:
            if other.key != key:
                assert other.bull_case not in system + str(tool), (
                    f"{key} carries {other.key}'s bull case — a book inheriting another's framing "
                    f"is the defect the registry exists to remove")


def test_the_invariant_discipline_survives_in_every_sleeve() -> None:
    """WHAT MUST NOT BECOME PER-BOOK. Cite-or-drop, the no-conclusion contract, anti-balance and
    the evidence_balance vocabulary are the discipline, not the framing — if a sleeve could drop
    them, the registry would be a route around the constitution rather than a way to serve more
    than one strategy under it."""
    from vinci.dossier import synthesis as syn

    for key in sorted(sl.SLEEVES):
        system, tool = syn.system_for(key), syn.tool_for(key)
        assert "NEVER CONCLUDE" in system, f"{key}: the no-conclusion contract is missing"
        assert "source_ref" in system, f"{key}: the cite-or-drop rule is missing"
        assert "ANTI-BALANCE" in system, f"{key}: the anti-balance rule is missing"
        req = tool["input_schema"]["required"]
        assert "evidence_balance" in req, f"{key}: the committed lean is not required"
        assert not any("verdict" in k.lower() for k in tool["input_schema"]["properties"]), (
            f"{key}: a verdict-shaped field appeared in the tool schema")


def test_every_primary_report_input_is_screen_scoped_not_just_the_spread() -> None:
    """REVIEW FINDING (#378). `primary` correctly excluded followed rows from the SPREAD, but
    `score_ledger` still built beta/alpha from every resolved BUY and `n_pending` from every row —
    and the markdown prints all three under the same screen-scoped heading. So the first followed
    quality BUY would have moved the reported primary beta/alpha, and a followed pending row would
    have inflated the primary pending count.

    THE SCOPE CLAIM HAS TO HOLD FOR EVERY INPUT THE HEADING COVERS, not just the number the fix
    happened to start with — otherwise the report says "screen-origin ONLY" over figures that are
    not. Asserted on `aggregate` (the boundary both paths cross) rather than on the harness, so it
    holds however the caller assembles its inputs."""
    from vinci.schemas.ledger import Verdict
    from vinci.scoring.metrics import VerdictScore, aggregate

    def s(tag: str, v: Verdict, ret: float, origin: str, sleeve: str) -> VerdictScore:
        return VerdictScore(entry_id=tag, ticker=tag, verdict=v, resolved=True, name_return=ret,
                            bench_return=0.0, origin=origin, sleeve=sleeve)

    screen = [s("A", Verdict.BUY, 0.20, "screen", "overshoot"),
              s("B", Verdict.AVOID_TERMINAL, 0.05, "screen", "overshoot")]
    followed = s("U", Verdict.BUY, 5.00, "followed", "quality")

    base = aggregate(screen, cost_bps=0, n_pending=0)
    with_followed = aggregate([*screen, followed], cost_bps=0, n_pending=0)

    # every PRIMARY figure the screen-scoped heading covers
    for field in ("buy_avoid_spread", "n_resolved_buy", "n_resolved_avoid",
                  "buy_mean_return", "avoid_mean_return", "buy_hit_rate",
                  "buy_excess_gross", "buy_excess_net"):
        assert getattr(base, field) == getattr(with_followed, field), (
            f"a FOLLOWED row moved the primary figure {field!r} — the report's "
            f"'screen-origin ONLY' claim does not hold for it")
    # …and the row is not lost: it appears under its own book
    assert with_followed.by_sleeve["quality"].n_long == 1


def test_pending_from_the_no_price_branch_is_screen_scoped_too(tmp_path: Path) -> None:
    """REVIEW FINDING (#382), and a TEST-LAYER lesson about the fix above it.

    ``score_ledger`` increments ``pending`` in TWO places: the unresolved-horizon filter at the
    end (fixed with the sibling test above) and the earlier no-forward-price branch. That earlier
    branch ``continue``s before the row is ever appended to ``scores`` — so it is the one path
    that NO downstream origin filter can reach, and a followed name whose bars are not loaded yet
    inflated the screen-only pending count through it.

    THE PREVIOUS PIN COULD NOT HAVE CAUGHT THIS: it asserts on ``aggregate``, and ``n_pending`` is
    an *input* to aggregate — already an int by the time that layer sees it. The count is only
    ever wrong upstream, so this pin runs the real ``score_ledger`` over a real store (the layer
    where the arithmetic happens), per the test-layer rule.

    Both names deliberately have NO price bars at all: that is the branch under test."""
    from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
    from vinci.scoring import score_ledger
    from vinci.store import Store

    entry_d = date(2026, 6, 1)

    def row(ticker: str, iid: str, verdict: Verdict, origin: str, sleeve: str) -> LedgerEntry:
        return LedgerEntry(
            entry_id=f"V-{ticker}", candidate_id=f"{ticker}-c", internal_id=iid, ticker=ticker,
            verdict=verdict, twin_call="t", entry_price=100.0, entry_price_as_of=entry_d,
            thesis="t", kill_criteria="k", horizon_days=90, confidence=Confidence.MEDIUM,
            decided_at=datetime.combine(entry_d, datetime.min.time()),
            origin=origin, sleeve=sleeve)

    with Store(tmp_path / "s.db") as store:
        store.write_prices([
            PriceBar(internal_id="IDX-IWM", bar_date=d, open=c, high=c + 1, low=c - 1, close=c,
                     volume=1e6, source="t")
            for d, c in ((entry_d, 100.0), (date(2026, 6, 10), 101.0))
        ])
        # neither name has bars → both take the no-forward-price branch
        store.append_ledger(row("AAA", "SEC-A", Verdict.BUY, "screen", "overshoot"))
        store.append_ledger(row("UUU", "SEC-U", Verdict.BUY, "followed", "quality"))
        scores, report = score_ledger(store, as_of=date(2026, 6, 10))

    assert scores == []  # neither row could be scored — both hit the branch
    assert report.n_pending == 1, (
        "the FOLLOWED row was counted into the primary pending figure — the report prints it "
        "under a heading that claims screen-origin ONLY")


def test_the_llm_log_records_the_prompt_that_was_actually_sent() -> None:
    """REVIEW FINDING (#379) — a FALSE PROVENANCE RECORD, which is the worst kind of defect this
    repo has a name for. The call used `system_for(sleeve)` while the log recorded the module-level
    `_SYSTEM` (the OVERSHOOT constant), so every quality assembly persisted an `llm_call.log`
    claiming it had been framed as a sharply de-rated overshoot name — the one artifact whose whole
    purpose is to answer "what was this model actually asked", answering it wrongly, in exactly the
    case the sleeve work exists to serve.

    CAPTURED FROM A STUB CLIENT, so the assertion compares the log against what the call RECEIVED
    rather than against a second copy of what we think it should be. A test that rebuilt the
    expected prompt itself would have passed against the buggy code."""
    from vinci.dossier import synthesis as syn

    seen: dict[str, object] = {}

    class _Stub:
        model = "stub-model"

        def extract(self, *, system: str, user: str, tool: dict[str, object]) -> dict[str, object]:
            seen["system"], seen["tool"] = system, tool
            raise syn.LlmError("stop here — the prompt is already captured")

    for key in ("overshoot", "quality"):
        seen.clear()
        _, _, log = syn.synthesize(
            _mech(), llm=cast("Any", _Stub()), ticker="ZZZZ", name="Test", sleeve=key)
        assert seen, f"{key}: the stub client was never called"
        assert str(seen["system"]) in log, (
            f"{key}: the log does not contain the system prompt the model RECEIVED — the audit "
            f"artifact would describe a framing that was never sent")
        assert f"=== SLEEVE === {key}" in log, f"{key}: the log does not name the book it used"

    # and the two books really do differ, so the check above is not vacuous
    seen.clear()
    syn.synthesize(_mech(), llm=cast("Any", _Stub()), ticker="ZZZZ", name="T", sleeve="quality")
    q = str(seen["system"])
    seen.clear()
    syn.synthesize(_mech(), llm=cast("Any", _Stub()), ticker="ZZZZ", name="T", sleeve="overshoot")
    assert q != str(seen["system"]), "the two books sent the same prompt — nothing was proven"


# ------------------------------------------------------------------ the PROPOSAL side (PR-2b)


def test_the_proposal_maps_to_each_books_own_legs() -> None:
    """THE SAME LEAN, A DIFFERENT PROPOSAL PER BOOK — and overshoot's is unchanged.

    The mapping is DERIVED from `Sleeve.verdicts` rather than a per-sleeve table: a book already
    declares (long, measured-against), and the rule was only ever "bullish proposes the long leg,
    bearish proposes its twin". A second table would be a dual write, and adding a sleeve would
    mean remembering to add its row or silently getting the wrong one.

    THE SHAPE IS WHAT IS FROZEN and it has not moved: bullish → long, bearish → twin, mixed →
    NOTHING. Only the labels follow the book."""
    from vinci.dossier.verdict import derive_proposal

    # the LIVE book, unchanged — every committed row was sealed under exactly this
    assert derive_proposal("strongly-bearish — x").action_word == "AVOID"
    assert derive_proposal("strongly-bullish — x").action_word == "BUY"
    assert derive_proposal("mixed — x").action is None

    # the quality book proposes its OWN twin, never "terminal"
    assert derive_proposal("strongly-bearish — x", sleeve="quality").action_word == "PASS"
    assert derive_proposal("strongly-bullish — x", sleeve="quality").action_word == "BUY"
    assert derive_proposal("mixed — x", sleeve="quality").action is None, (
        "a two-sided read proposed something — mixed must propose NOTHING in every book")

    # derived, so it holds for every ledger-active book without a table
    for row in sl.SLEEVE_ROWS:
        if not row.ledger_active:
            continue
        assert derive_proposal("strongly-bullish — x", sleeve=row.key).action_word is not None
        got = derive_proposal("strongly-bearish — x", sleeve=row.key).action
        assert got is not None and got.value == row.verdicts[1], (
            f"{row.key}: the bearish lean did not propose the book's own twin")


def test_an_unknown_sleeve_and_a_non_ledger_book_give_different_reasons() -> None:
    """FOUND BY RUNNING IT, not by reading it. The first cut reported both as "records no ledger
    verdicts", which is TRUE of `theme` (it validates in its own ratification ledger) and FALSE of
    a typo — it would state something about the fund's design that is not so. Same class as a guard
    that refuses a value and reports it missing: one of the two has to be a lie.

    Neither raises: this is on the RENDER path, and a page that cannot be drawn because its sleeve
    is misspelled is worse than a page that says so."""
    from vinci.dossier.verdict import derive_proposal

    unknown = derive_proposal("strongly-bearish — x", sleeve="momentum")
    defined = derive_proposal("strongly-bearish — x", sleeve="theme")
    assert unknown.action is None and defined.action is None
    assert "unknown sleeve" in unknown.note, unknown.note
    # PIN MOVED WITH THE #380 FIX, and it moved to the MORE correct answer. `theme` is both dormant
    # AND labelled outside the Verdict enum; it used to report the second because the activation
    # property was never read. Activation is the PRIMARY reason — it is the registry's own stated
    # gate — so that is what a reader should be told. The distinction this test exists for is
    # unchanged: a DEFINED book and an UNKNOWN one still give different sentences.
    assert "NOT activated" in defined.note, defined.note
    assert unknown.note != defined.note, "two different absences share one sentence"


def test_the_js_proposal_twin_mirrors_the_python_registry() -> None:
    """THE TWIN RULE, on the one genuine second copy this design has. The JS cannot import
    `vinci.sleeves`, so `SLEEVE_LEGS` really is a duplicate — and the expectation here is DERIVED
    from the Python registry rather than transcribed, because a hand-typed table would be a THIRD
    copy rather than a check on the second. Adding a sleeve therefore reddens here until the mirror
    is updated, which is the only version that measures anything."""
    import re

    js = (SRC.parents[1] / "frontend" / "views" / "shared" / "dossier.js").read_text()
    m = re.search(r"const SLEEVE_LEGS = \{(.*?)\n\};", js, re.S)
    assert m, "the JS SLEEVE_LEGS mirror is gone"
    js_legs = {k: (a, b) for k, a, b in
               re.findall(r'(\w+):\s*\["([^"]+)",\s*"([^"]+)"\]', m.group(1))}
    assert js_legs == {r.key: tuple(r.verdicts) for r in sl.SLEEVE_ROWS}, (
        f"the JS proposal mirror drifted from the registry: {js_legs}")
    # the enum mirror too — the JS decides "can this book propose at all" from it
    mv = re.search(r"const LEDGER_VERDICTS = \[(.*?)\];", js)
    assert mv, "the JS LEDGER_VERDICTS mirror is gone"
    from vinci.schemas.ledger import Verdict

    assert {v.strip().strip('"') for v in mv.group(1).split(",") if v.strip()} == {
        v.value for v in Verdict}, "the JS verdict mirror drifted from the enum"


def test_a_dormant_sleeve_proposes_nothing_and_cannot_reach_the_ledger() -> None:
    """REVIEW FINDING (#380). The proposal gated on "are the labels enum members", which is not the
    activation question. `neglect` is explicitly DORMANT and shares overshoot's BUY/AVOID_TERMINAL
    labels, so it returned a LIVE proposal; `theme` was refused only by the accident of its own
    labels. The right property — `ledger_active` — was never read at either boundary, so a follow
    entry naming a dormant book could receive a proposal and append a row to the fund's proof
    ledger under a strategy that is not being measured there. The ledger is append-only, so that
    row could not have been taken back out.

    BOTH BOUNDARIES, because they fail independently: the proposal is fail-honest (it returns a
    reason, since this is the render path), the ledger write RAISES (append-only, so it refuses
    before the seal). Derived from `ledger_active` rather than a hardcoded roster, so activating a
    book flips both without touching this test."""
    from vinci.dossier.verdict import derive_proposal
    from vinci.ledger.workflow import LedgerError, _require_verdict_in_sleeve
    from vinci.schemas.ledger import Verdict

    for row in sl.SLEEVE_ROWS:
        prop = derive_proposal("strongly-bearish — x", sleeve=row.key)
        if row.ledger_active:
            assert prop.action is not None, f"{row.key} is active but proposes nothing"
            _require_verdict_in_sleeve(Verdict(row.verdicts[0]), row.key)   # must not raise
        else:
            assert prop.action is None, (
                f"{row.key} is DORMANT (ledger_active=False) but returned a live proposal "
                f"{prop.action_word!r} — the registry's activation gate is bypassed")
            assert "NOT activated" in prop.note, prop.note
            with pytest.raises(LedgerError, match="NOT activated"):
                _require_verdict_in_sleeve(Verdict.BUY, row.key)

    # the sharp case: neglect shares overshoot's LABELS, so a membership test let it through
    assert sl.BY_KEY["neglect"].verdicts == sl.BY_KEY["overshoot"].verdicts, (
        "neglect no longer shares overshoot's labels — this test's whole point was that identical "
        "labels are not an activation signal; re-check the gate if the registry changed")


# ------------------------------------------------------------------ the PAGE side (PR-2c)


def test_the_page_asks_each_books_own_question() -> None:
    """THE DEFECT, AT THE SURFACE A READER MEETS. "What broke — and did it fall alone?" is the right
    question for a name that broke and the WRONG one for a compounder that never did — a megacap
    was being asked it because the heading was hardcoded.

    THE SECTION IS UNCHANGED, only the heading: the gap-downs and the idiosyncratic-vs-shared split
    are real facts about ANY name's price path. It was the heading that made a claim about the
    name, which is why this is a copy change and not a data one."""
    from vinci.dossier.render import _drawdown_idio_lines
    from vinci.dossier.schemas import Dossier

    committed = sorted((SRC.parents[1] / "data" / "dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this worktree")
    mech = Dossier.model_validate_json(committed[0].read_text()).mechanical
    for row in sl.SLEEVE_ROWS:
        head = _drawdown_idio_lines(mech, sleeve=row.key)[0]
        assert head == f"## {row.drawdown_heading}", (
            f"{row.key}: the page asks {head!r}, not its own question")
    # and the live book's heading is the exact pre-existing string
    assert sl.BY_KEY["overshoot"].drawdown_heading == "What broke — and did it fall alone?"


def test_the_js_page_copy_mirrors_the_python_registry() -> None:
    """THE TWIN RULE on the page copy — the second genuine duplicate, pinned the same way as the
    proposal legs: the expectation is DERIVED from the registry, so adding a sleeve reddens here
    until the mirror is updated rather than letting the two renderers drift apart silently."""
    import re

    js = (SRC.parents[1] / "frontend" / "views" / "shared" / "dossier.js").read_text()
    m = re.search(r"const SLEEVE_COPY = \{(.*?)\n\};", js, re.S)
    assert m, "the JS SLEEVE_COPY mirror is gone — the web page lost its per-book headings"
    body = m.group(1)
    for row in sl.SLEEVE_ROWS:
        # EVERY per-book string, not just the ones the first pass moved. The section HEADING went
        # per-book while its own contents ("Read — what broke", the subtitle beneath it, the
        # copy-paste CLI help) stayed hardcoded — a heading asking one book's question over another
        # book's labels. Enumerating the fields is what stops the next addition being forgotten.
        for field in (row.drawdown_heading, row.bull_label, row.bear_label,
                      row.survive_heading, row.read_label, row.drawdown_subtitle,
                      row.twin_help, row.thesis_help):
            assert field in body, (
                f"{row.key}: the JS page copy is missing {field!r} — the md and web renderers "
                f"would print different questions for the same book")
    # the hardcoded overshoot strings must be GONE from the render paths
    assert "the decline is overdone</div>" not in js, (
        "a hardcoded case label survives in the JS — it would print over every other book")


def test_every_committed_page_renders_under_its_own_book() -> None:
    """E2E ON THE LIVING ARTIFACTS, phrasing-independent: each committed page must carry the
    heading its OWN sleeve declares, and none of the others'. This is the pin that would have
    caught a followed name inheriting the overshoot question — the exact live defect."""
    from vinci.dossier.schemas import Dossier

    root = SRC.parents[1] / "data" / "dossiers"
    if not root.is_dir():
        pytest.skip("no committed dossiers in this worktree")
    seen = 0
    for f in sorted(root.glob("*/dossier.json")):
        md = (f.parent / "dossier.md")
        if not md.exists():
            continue
        d = Dossier.model_validate_json(f.read_text())
        row, text = sl.BY_KEY[d.sleeve], md.read_text()
        assert f"## {row.drawdown_heading}" in text, (
            f"{f.parent.name} ({d.sleeve}) does not ask its own book's question")
        for other in sl.SLEEVE_ROWS:
            if other.drawdown_heading != row.drawdown_heading:
                assert f"## {other.drawdown_heading}" not in text, (
                    f"{f.parent.name} ({d.sleeve}) carries {other.key}'s question")
        seen += 1
    assert seen, "no committed page was checked"


# ------------------------------------------------------------------ the FRONTEND surface


def test_the_committed_index_tells_the_shelf_which_book_each_name_is_in() -> None:
    """THE SHELF HAD NO WAY TO KNOW. The per-name mirror carries `sleeve` for free (it is a byte
    copy of the source), but the INDEX is what the grid reads — so a quality name was
    indistinguishable from an overshoot one until you opened it, and its different question and
    BUY/PASS vocabulary then arrived unexplained.

    Derived from the committed dossiers rather than hardcoded, so it stays silent as names are
    added and still reddens if the index and the artifacts disagree."""
    import json

    root = SRC.parents[1]
    idx_path = root / "frontend" / "dossiers" / "index.json"
    if not idx_path.exists():
        pytest.skip("no committed dossier index in this worktree")
    idx = json.loads(idx_path.read_text())
    assert "sleeves" in idx, "the index lost its sleeve map — the shelf cannot label a book"
    for t in idx["tickers"]:
        src = root / "data" / "dossiers" / t / "dossier.json"
        if not src.exists():
            continue
        want = json.loads(src.read_text()).get("sleeve", sl.DEFAULT_SLEEVE)
        assert idx["sleeves"].get(t) == want, (
            f"{t}: the index says {idx['sleeves'].get(t)!r} but the dossier says {want!r}")
        assert idx["sleeves"][t] in sl.SLEEVES


def test_the_shelf_tags_only_the_non_default_book_and_never_in_colour() -> None:
    """TWO DELIBERATE CHOICES, pinned so they are decisions rather than drift.

    ONLY the non-default book is tagged: a label on every name is noise, and its ABSENCE on the
    overshoot majority carries the same information. And the tag is NEUTRAL ink — the book is
    context, not a call. A coloured pill would let the eye triage the shelf by strategy before
    reading anything, which is the same anchoring the sealed proposal exists to prevent (the
    existing `leanTag` guard makes exactly this argument for the machine's lean)."""
    import re

    js = (SRC.parents[1] / "frontend" / "views" / "shared" / "dossier.js").read_text()
    m = re.search(r"function sleeveTag\(sleeve\) \{(.*?)\n\}", js, re.S)
    assert m, "sleeveTag() is gone — the shelf stopped saying which book a name is in"
    body = m.group(1)
    assert "DEFAULT_SLEEVE" in body and 'return ""' in body, (
        "sleeveTag no longer suppresses the default book — every card would carry a tag")
    for banned in ("pill", "--danger", "--live", "--pos-text", "buy", "avoid"):
        assert banned not in body, (
            f"sleeveTag uses {banned!r} — the shelf would triage by strategy in COLOUR before a "
            f"single fact is read")
    assert "ds-lean" in body, "the tag lost the neutral class leanTag uses"


def test_the_web_page_refuses_to_frame_an_unknown_sleeve_as_overshoot() -> None:
    """REVIEW FINDING (#381). `sleeveCopy` fell back to overshoot copy for ANY value it did not
    recognise, so a corrupt or stale artifact carrying an unknown sleeve was rendered asking the
    de-rating question and labelling its cases as an overshoot — the exact misleading framing this
    work removes, reached through the error path instead of the default one.

    ABSENT AND UNKNOWN ARE DIFFERENT STATES. Missing is the legitimate legacy case (every dossier
    committed before the tag, plus the sealed FUBO record) and truthfully reads as the default
    book. A PRESENT unrecognised value is a defect and now says so — matching the fail-honest
    handling `deriveProposal` already had.

    EXECUTED, not grepped: the real resolver is lifted out of the module and run, so this asserts
    what a browser would actually render rather than that some source text is present."""
    import json
    import re
    import subprocess

    js_path = SRC.parents[1] / "frontend" / "views" / "shared" / "dossier.js"
    js = js_path.read_text()
    parts = [
        re.search(r'const DEFAULT_SLEEVE = "[^"]+";', js).group(0),
        re.search(r"const SLEEVE_COPY = \{.*?\n\};", js, re.S).group(0),
        "const escapeHtml = (x) => String(x);",
        re.search(r"function sleeveCopy\(sleeve\) \{.*?\n\}", js, re.S).group(0),
        "const out = {};",
        "for (const v of [null, '', 'quality', 'momentum']) out[String(v)] = sleeveCopy(v);",
        "console.log(JSON.stringify(out));",
    ]
    proc = subprocess.run(["node", "--input-type=module", "-e", "\n".join(parts)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.skip(f"node unavailable or module changed shape: {proc.stderr[:120]}")
    got = json.loads(proc.stdout)

    overshoot_q = sl.BY_KEY[sl.DEFAULT_SLEEVE].drawdown_heading
    assert got["null"]["drawdown"] == overshoot_q, "absent sleeve must read as the default book"
    assert got[""]["drawdown"] == overshoot_q, "blank sleeve must read as the default book"
    assert got["quality"]["drawdown"] == sl.BY_KEY["quality"].drawdown_heading
    unknown = got["momentum"]
    assert unknown.get("unknown") is True, "an unrecognised sleeve is not flagged as unknown"
    assert unknown["drawdown"] != overshoot_q, (
        "an UNRECOGNISED sleeve is rendered with the overshoot question — the page would ask what "
        "broke about a name the client was told is a different book")
    assert "momentum" in unknown["drawdown"], "the unknown state does not name the bad value"


# ------------------------------------------------------------------ the LEDGER-READING surfaces


def _row(tag: str, verdict: str, excess: float, origin: str, sleeve: str) -> Any:
    """One marked position. Built from the REAL constructor so field defaults and validation are
    the production ones."""
    from datetime import date

    from vinci.monitor import position_row

    r = position_row(
        ticker=tag, verdict=verdict, sector="Test", entry_price=100.0,
        entry_date=date(2026, 1, 1), current_price=100.0 * (1 + excess),
        current_date=date(2026, 6, 1), benchmark="IWM", benchmark_entry=100.0,
        benchmark_now=100.0, horizon_days=180, origin=origin, sleeve=sleeve)
    return r


def test_the_monitor_spread_is_screen_origin_like_the_scoring_report() -> None:
    """THE SAME HEADLINE NUMBER, PRINTED BY A DIFFERENT COMMAND — and it was not scoped. `vinci
    score` filtered to screen-origin while `vinci monitor` did not, so the operator's own console
    and the committed report would have disagreed about the fund's proof number the moment a
    followed row existed.

    A quality `PASS` made it worse than a rounding difference: `_is_buy` is a BUY-PREFIX test, so
    PASS lands in the AVOID leg and MOVES the spread rather than being ignored.

    THE FIXTURE IS BUILT SO POOLING WOULD CHANGE THE ANSWER — the audit's finding about
    `test_monitor.py` was that its pins use fixed inputs and stay green while production
    mis-routes. This one fails if the filter is removed."""
    from vinci.monitor import compute_spread

    screen = [_row("A", "BUY", 0.20, "screen", "overshoot"),
              _row("B", "AVOID_TERMINAL", 0.05, "screen", "overshoot")]
    base = compute_spread(screen)
    assert base.spread is not None

    polluted = compute_spread([*screen, _row("U", "PASS", -5.0, "followed", "quality")])
    assert polluted.spread == base.spread, (
        "a FOLLOWED quality PASS moved the monitor's BUY−AVOID spread — the operator's console "
        "and the scoring report now disagree about the fund's proof number")
    assert polluted.avoid_n == base.avoid_n, "the PASS row was counted into the AVOID leg"


def test_the_monitor_panel_names_a_non_default_book() -> None:
    """EXCLUDED FROM THE SPREAD IS NOT THE SAME AS ABSENT FROM THE PANEL. A followed row still
    marks to market and still belongs on the operator's screen — it simply does not feed the
    number underneath. Named only when it is NOT the default, the same rule the shelf uses."""
    from datetime import date

    from vinci.monitor import MonitorSnapshot, compute_spread, render_table

    rows = [_row("A", "BUY", 0.20, "screen", "overshoot"),
            _row("U", "BUY", 0.40, "followed", "quality")]
    text = render_table(MonitorSnapshot(
        as_of=date(2026, 6, 1), rows=rows, spread=compute_spread(rows),
        freshness=[], price_basis="test", notes=[]))
    assert "[quality]" in text, "the followed row does not say which book it belongs to"
    assert "[overshoot]" not in text, "the default book is tagged — that is noise on every row"
    assert "screen-origin" in text, "the spread does not state the scope it now measures"


def test_the_web_gate_stat_is_screen_origin_and_the_books_are_counted_beside_it() -> None:
    """THE DEPLOYED PAGE'S PROOF NUMBER. `getLedger().counts` fed a widget labelled "the BUY−AVOID
    spread that must prove positive before capital deploys" while pooling every book — so the site
    and the python side would have reported different things about the fund's own gate.

    The enabling defect was one layer down: the entry projection DROPPED `origin`/`sleeve`, so no
    consumer could filter even in principle.

    EXECUTED under node against a synthetic ledger payload, so this asserts what the browser
    computes rather than that some source text exists."""
    import json
    import re
    import subprocess

    lib = (SRC.parents[1] / "frontend" / "lib" / "snapshots.js").read_text()
    assert "origin: p.origin" in lib and "sleeve: p.sleeve" in lib, (
        "the ledger projection dropped origin/sleeve — nothing downstream can filter by book")

    body = re.search(r"const primary = entries\.filter.*?\n  return \{.*?\n  \};", lib, re.S)
    assert body, "the screen-origin scoping of the gate counts is gone"
    assert 'e.origin === "screen"' in body.group(0), (
        "the gate counts no longer filter to screen-origin — the deployed proof number pools books")
    assert "groupOtherBooks(entries)" in body.group(0), (
        "getLedger no longer groups the other books — a followed verdict would vanish from the "
        "app entirely. (Call-site pin: the behaviour test below imports the helper directly and "
        "would stay green if this call were deleted.)")

    # the display helper both views now share
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", "\n".join([
            re.search(r"export function verdictWord\(verdict\) \{.*?\n\}", lib, re.S)
            .group(0).replace("export ", ""),
            "console.log(JSON.stringify(['BUY','AVOID_TERMINAL','PASS'].map(verdictWord)));"])],
        capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.skip("node unavailable")
    assert json.loads(proc.stdout) == ["BUY", "AVOID", "PASS"], (
        "verdictWord no longer renders each label as itself (bar the documented AVOID shortening)")


def test_a_followed_row_under_the_default_book_is_still_counted_as_its_own_book() -> None:
    """REVIEW FINDING (#382) — the row that fell through every surface at once.

    A FOLLOWED name may legitimately sit in the DEFAULT book: `followed.json` accepts
    `sleeve: "overshoot"`, and `_finalist` refuses a screen/follow overlap only when the sleeve
    DIFFERS. Such a row is excluded from `primary` by its ORIGIN — but the grouping keyed on the
    SLEEVE, so it merged into the screen majority's `overshoot` bucket, which the renderer drops
    as "the default book". Net: absent from the proof number, absent from "Other books", and
    chip-less on its own line — counted nowhere and labelled nothing, while the overview tile
    said "1 in other books". Origin and sleeve are orthogonal, and the code has to treat them so.

    EXECUTED against the REAL module (node imports `snapshots.js` itself), not a regex-extracted
    copy and not a source grep — the pin this replaces asserted a variable NAME appeared in the
    file, which is precisely why the defect passed it. The call-site pin above covers the other
    direction, since a helper test alone stays green if the caller stops calling it."""
    import json
    import subprocess

    lib = SRC.parents[1] / "frontend" / "lib" / "snapshots.js"
    rows = [
        {"origin": "screen", "sleeve": "overshoot", "verdict": "BUY", "resolved": True},
        {"origin": "followed", "sleeve": "overshoot", "verdict": "BUY", "resolved": False},
        {"origin": "followed", "sleeve": "quality", "verdict": "PASS", "resolved": True},
        {"verdict": "AVOID_TERMINAL", "resolved": True},  # legacy: untagged ⇒ screen/overshoot
    ]
    proc = subprocess.run(
        ["node", "--input-type=module", "-e",
         f'const m = await import({json.dumps(str(lib))});'
         f'console.log(JSON.stringify(m.groupOtherBooks({json.dumps(rows)})));'],
        capture_output=True, text=True)
    if proc.returncode != 0:
        if "node" in proc.stderr.lower() and "not found" in proc.stderr.lower():
            pytest.skip("node unavailable")
        raise AssertionError(f"the real module failed to execute: {proc.stderr}")
    books = json.loads(proc.stdout)

    assert set(books) == {"followed:overshoot", "followed:quality"}, (
        f"grouping is not on the (origin, sleeve) pair: {sorted(books)}")
    fo = books["followed:overshoot"]
    assert fo["logged"] == 1 and fo["long"] == 1, (
        "the followed-overshoot row was folded into the screen majority and lost")
    assert fo["origin"] == "followed" and fo["sleeve"] == "overshoot", (
        "the bucket does not carry both parts, so the renderer cannot name the book")
    # the screen row and the legacy untagged row stay OUT — they are the composite itself
    assert sum(b["logged"] for b in books.values()) == 2, (
        "a screen-origin row leaked into the other-books tally — it is already in `counts`")


def test_the_resolved_fraction_never_mixes_two_populations() -> None:
    """REVIEW FINDING (#382). `resolved_n` counts SCOPED (screen-origin) rows, and both renderers
    divided it by the snapshot's TOTAL row count — so a book holding one screen row and one
    followed row printed "resolved 1/2" where the honest reading is 1/1. A fraction whose halves
    count different populations is not a fraction.

    TWO renderers made the identical mistake independently, which is why the fix puts `scoped_n`
    on the diagnostic instead of a filter in each caller."""
    from vinci.monitor import MonitorSnapshot, PositionRow, compute_spread, render_table

    def r(ticker: str, verdict: str, origin: str, sleeve: str) -> PositionRow:
        return PositionRow(
            ticker=ticker, verdict=verdict, sector=None, entry_price=100.0,
            entry_date=date(2026, 1, 1), current_price=110.0, current_date=date(2026, 6, 1),
            benchmark="IWM", benchmark_entry=100.0, benchmark_now=105.0,
            position_return=0.10, benchmark_return=0.05, excess=0.05,
            days_elapsed=151, horizon_days=90, horizon_date=date(2026, 4, 1), resolved=True,
            origin=origin, sleeve=sleeve)

    rows = [r("AAA", "BUY", "screen", "overshoot"), r("UUU", "PASS", "followed", "quality")]
    spread = compute_spread(rows)
    assert spread.resolved_n == 1 and spread.scoped_n == 1, (
        f"scope disagrees with itself: resolved {spread.resolved_n}/{spread.scoped_n}")

    text = render_table(MonitorSnapshot(as_of=date(2026, 6, 1), rows=rows, spread=spread))
    assert "resolved 1/1" in text, (
        f"the console prints a fraction across two populations:\n"
        f"{[ln for ln in text.splitlines() if 'resolved' in ln]}")
    assert "resolved 1/2" not in text

    # LEGACY SNAPSHOT (no scoped_n): falls back to the row count, which is right for it — every
    # row it holds is screen-origin, and a sealed snapshot is never rewritten.
    legacy = MonitorSnapshot(as_of=date(2026, 6, 1), rows=rows[:1],
                             spread=spread.model_copy(update={"scoped_n": 0}))
    assert "resolved 1/1" in render_table(legacy)


def test_the_decision_log_page_actually_renders() -> None:
    """THE INCIDENT PIN. `sleeveChip` was written as a `const` inside `render()` while its only
    caller, `entryCard`, is a module-scope function — so every call threw `sleeveChip is not
    defined` and the page stopped dead at "Loading ledger…". The whole decision log, including the
    fund's own proof number, was blank on every load.

    NOTHING IN THE SUITE NOTICED. Every pin on this file greps source text or executes one lifted
    function, and a scope error is invisible to both: the string is present, the function body is
    correct, and it is the WIRING between them that is broken. Same shape as the two unwired call
    sites the browser found in `dossier.js` — the third landing of this class, which is what makes
    it a guard rather than a fix.

    So this runs the REAL `render()` over the REAL committed snapshots, end-to-end, and asserts
    the page reaches its content. `root` is a plain object because render only assigns
    `innerHTML`, and `fetch` is stubbed onto the committed files — no DOM, no server."""
    import json
    import subprocess

    fe = SRC.parents[1] / "frontend"
    if not (fe / "snapshots" / "decision_ledger.jsonl").exists():
        pytest.skip("no committed frontend snapshots in this worktree")
    script = """
import { readFile } from 'node:fs/promises';
const ROOT = __ROOT__;
globalThis.fetch = async (p) => {
  const rel = String(p).replace(/^\\.\\//, '').replace(/^\\//, '');
  try {
    const buf = await readFile(ROOT + '/' + rel, 'utf8');
    return { ok: true, status: 200, json: async () => JSON.parse(buf), text: async () => buf };
  } catch {
    return { ok: false, status: 404, json: async () => ({}), text: async () => '' };
  }
};
const v = await import(ROOT + '/views/shared/decision-log.js');
const root = { innerHTML: '' };
await v.render(root, {}, { item: { title: 'Decision log', blurb: '' },
                           frame: (i, o) => o.bodyHtml });
console.log(JSON.stringify({ html: root.innerHTML }));
""".replace("__ROOT__", json.dumps(str(fe)))
    proc = subprocess.run(["node", "--input-type=module", "-e", script],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        if "not found" in proc.stderr.lower() and "node" in proc.stderr.lower():
            pytest.skip("node unavailable")
        raise AssertionError(
            f"the decision-log page THREW while rendering the committed ledger — in the browser "
            f"it shows nothing but its loading placeholder:\n{proc.stderr.strip()}")

    html = json.loads(proc.stdout)["html"]
    assert "Loading ledger" not in html, (
        "render returned with the loading placeholder still in place — the page never reached "
        "its content")
    assert "Verdicts logged" in html and len(html) > 2000, (
        f"the page rendered but produced no ledger body ({len(html)} chars)")


def test_the_cohort_read_uses_a_direction_neutral_verb() -> None:
    """`_idio_read` said "fell ALONE" / "fell WITH cohort". It is computed in the SLEEVE-BLIND
    mechanical layer and rendered under a heading the sleeve owns — and the quality book's heading
    asks whether the price "moved alone", so the body contradicted the heading directly above it
    on any name not being judged for a decline. The signed percentages beside it carry direction,
    so the verb was never the thing conveying it.

    LATENT WHEN FIXED — no committed dossier reaches this branch — which is precisely why it needs
    a guard rather than a memory: nothing renders it today, so a revert stays invisible until the
    first quality name with a graph cohort, by which point it is already in an artifact.

    Scoped by AST to that function's own STRING LITERALS, so prose in comments and docstrings —
    which legitimately discuss the old wording — cannot false-positive it."""
    import ast

    src = pathlib.Path(sl.__file__).resolve().parents[1] / "vinci" / "dossier" / "mechanical.py"
    fn = next((n for n in ast.walk(ast.parse(src.read_text()))
               if isinstance(n, ast.FunctionDef) and n.name == "_idio_read"), None)
    assert fn is not None, "_idio_read is gone — re-point this pin at the cohort read's new home"

    doc = ast.get_docstring(fn, clean=False)
    emitted = [n.value for n in ast.walk(fn)
               if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value != doc]
    assert emitted, "no string literals found in _idio_read — the pin is not reaching its subject"
    for text in emitted:
        low = text.lower()
        for verb in ("fell", "rose", "dropped", "crashed", "plunged"):
            assert verb not in low, (
                f"the cohort read emits a DIRECTIONAL verb ({verb!r}) in {text!r}. This layer is "
                f"sleeve-blind and renders under each book's own heading — the percentages beside "
                f"it already carry the direction.")


def test_the_shared_valuation_caveat_privileges_no_single_book() -> None:
    """The trailing-multiple blind-flag is attached to EVERY book's dossier, and it used to be
    written in one book's language: "cannot distinguish cheap-overshoot from cheap-terminal".

    IT DID NOT STAY IN THE CODE. The note is fed to the synthesis, and the LLM handed it back —
    UBER's committed QUALITY read carried "a trailing multiple that cannot disambiguate overshoot
    from terminal re-rate". A name judged on whether its runway is underpriced had its machine read
    phrased as a de-rating hunt, in an artifact the human decides from. A shared string is the one
    place per-book vocabulary does the most damage, because every book pays for it.

    ONE DEFINITION, ASSERTED: `cli.py`'s CIQ-ingest path carried a byte-copy with a comment saying
    it mirrored the original — so the wording sat unexamined in two places and would have been
    fixed in one. The literal must exist exactly once in the tree."""
    import pathlib as _pl

    from vinci.dossier.mechanical import TRAILING_ONLY_NOTE

    lowered = TRAILING_ONLY_NOTE.lower()
    for row in sl.SLEEVE_ROWS:
        assert row.key not in lowered, (
            f"the shared valuation caveat names the {row.key!r} book: {TRAILING_ONLY_NOTE!r}. "
            f"Every book receives this note, so naming one frames the others' evidence in a "
            f"vocabulary they are not judged in — and the synthesis repeats it back.")
    assert "terminal" not in lowered, (
        f"'terminal' is overshoot's twin, not a universal one: {TRAILING_ONLY_NOTE!r}")

    # SINGLE SOURCE — the duplicate is what let the wording go unexamined. Searched by a
    # DISTINCTIVE FRAGMENT, not the assembled string: the constant is an implicit concatenation
    # across two source lines, so the full text never appears contiguously in any file and a
    # whole-string grep silently matches nothing — a check that passes by finding zero copies of
    # a string that exists once is not a check. (It found 0 on the first run.)
    fragment = "no forward basis"
    assert fragment in TRAILING_ONLY_NOTE, "re-point this pin: the fragment left the note"
    root = _pl.Path(sl.__file__).resolve().parents[1]
    hits = sorted(p.name for p in (root / "vinci").rglob("*.py") if fragment in p.read_text())
    assert hits == ["mechanical.py"], (
        f"the caveat is declared in {hits} — it must have exactly one definition and every other "
        f"caller must import it, or the next wording fix lands in one copy and not the other")


def test_the_log_verdict_cli_help_privileges_no_single_book() -> None:
    """`--twin` help read "how the terminal-decline twin was ruled out" — one book's twin, asked
    of every book. A quality verdict was told to rule out terminal decline at the moment of
    logging it, which is the false framing the registry exists to remove, on the surface closest
    to the append-only record.

    IT CANNOT BE MADE PER-BOOK: argparse builds this help when the parser is constructed, before
    any ticker — and so any sleeve — is known. So the invariant is not "it matches the sleeve" but
    "it privileges NO sleeve", and the per-book wording reaches the analyst where the book IS
    known (`Sleeve.twin_help`, rendered into the dossier page's copy-paste command).

    Asserted against the REAL parser's formatted help, not the source line, so re-wording or
    moving the argument cannot quietly slip a book's twin back in.

    WHITESPACE IS NORMALISED FIRST, and the first cut of this pin was wrong without it: argparse
    wraps help to the terminal width, so at COLUMNS=50 and 60 the phrase "terminal-decline twin"
    straddles a line break and a raw substring test PASSES while the overshoot framing is sitting
    right there. It happened to catch the regression at 80 columns, which is the worst kind of
    guard — one that works on the machine where it was written."""
    import argparse

    from vinci.cli import build_parser

    parser = build_parser()
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    help_text = " ".join(sub.choices["log-verdict"].format_help().split())

    assert "--twin" in help_text, "the --twin argument is gone from log-verdict"
    for row in sl.SLEEVE_ROWS:
        assert " ".join(row.twin_help.split()) not in help_text, (
            f"the CLI help hardcodes the {row.key!r} book's twin wording ({row.twin_help!r}). "
            f"argparse cannot know the sleeve here, so naming one book asks every OTHER book's "
            f"verdict to rule out a twin that is not its own.")
    # and the overshoot twin specifically, in either tense — the exact string that was there
    for phrasing in ("terminal-decline twin", "terminal decline twin"):
        assert phrasing not in help_text, f"overshoot's twin is back in the shared help: {phrasing}"


def test_the_book_chip_is_gated_on_origin_not_only_on_the_sleeve() -> None:
    """REVIEW FINDING (#382), the display half. The chip was gated on the SLEEVE, so a
    followed-overshoot row rendered bare — reading as one of the screen majority while being
    excluded from their spread. Its own tooltip already claimed "excluded from the screen-origin
    spread", an ORIGIN claim on a SLEEVE test.

    The rule that stays: a chip on every row is noise, so the screen-origin default book keeps
    none — its absence carries the same information. EXECUTED (the arrow function is lifted from
    the view and run), because a source grep is what let this through the first time."""
    import json
    import re
    import subprocess

    src = (SRC.parents[1] / "frontend" / "views" / "shared" / "decision-log.js").read_text()
    # module scope (see the incident pin above) — the body closes at column 0
    fn = re.search(r"const sleeveChip = \(e\) => \{.*?\n\};", src, re.S)
    assert fn, "sleeveChip is gone or reshaped — re-point this pin at the chip's new home"
    cases = [
        {"origin": "screen", "sleeve": "overshoot"},    # the majority → no chip
        {},                                             # legacy untagged → reads as the majority
        {"origin": "followed", "sleeve": "overshoot"},  # THE DEFECT: must be chipped
        {"origin": "followed", "sleeve": "quality"},
    ]
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", "\n".join([
            "const escapeHtml = (s) => String(s);",
            fn.group(0),
            f"console.log(JSON.stringify({json.dumps(cases)}.map(sleeveChip)));"])],
        capture_output=True, text=True)
    if proc.returncode != 0:
        if "not found" in proc.stderr.lower():
            pytest.skip("node unavailable")
        raise AssertionError(f"sleeveChip failed to execute: {proc.stderr}")
    screen, legacy, followed_overshoot, followed_quality = json.loads(proc.stdout)

    assert screen == "" and legacy == "", "the default screen book is tagged — noise on every row"
    assert "followed" in followed_overshoot, (
        "a followed row under the DEFAULT book renders bare, so it reads as one of the "
        "screen-origin majority while being excluded from their spread")
    assert "quality" in followed_quality
    for chip in (followed_overshoot, followed_quality):
        assert "ds-lean" in chip and "pill" not in chip, (
            "the book must be neutral ink, never a coloured pill — a colour lets the eye triage "
            "the log by book before reading anything")


def test_no_per_book_string_is_hardcoded_outside_the_js_mirror() -> None:
    """FOUND BY THE BROWSER PREVIEW, not by any test — which is why this pin exists.

    Two per-book strings had been ADDED to `SLEEVE_COPY` and never WIRED to their call sites, so
    `dossier.js` still rendered "What happened — and can it survive?" and "Read — what broke" on a
    quality page while the markdown renderer had already moved on. The mirror-parity pin passed
    throughout: it checks the table CONTAINS each string, which an unwired literal satisfies twice
    over — once in the table and once at the hardcoded call site.

    THIS CHECKS THE INVERSE, which is the property that actually matters: outside the mirror table
    itself, no per-book string may appear as a literal at all. A call site that has not been wired
    fails here even though the table is complete. It is also the exact sweep that found the second
    instance after the preview surfaced the first — a defect one finds by hand is a defect that
    will recur, so the hand-sweep becomes the guard."""
    import re

    js = (SRC.parents[1] / "frontend" / "views" / "shared" / "dossier.js").read_text()
    body = re.sub(r"const SLEEVE_COPY = \{.*?\n\};", "", js, flags=re.S)
    fields = ("drawdown_heading", "bull_label", "bear_label", "survive_heading",
              "read_label", "drawdown_subtitle", "twin_help", "thesis_help")
    stray = [f"{row.key}.{name} = {getattr(row, name)!r}"
             for row in sl.SLEEVE_ROWS for name in fields
             if getattr(row, name) in body]
    assert not stray, (
        "per-book copy is hardcoded outside the mirror — the call site was never wired, so this "
        "string renders on EVERY book regardless of which one the page belongs to:\n  "
        + "\n  ".join(stray))


def test_a_gradual_decline_name_still_gets_its_price_path() -> None:
    """A NAME THAT BLED RATHER THAN BROKE USED TO RENDER ONE SENTENCE AND NO CHART.

    The section asks what MOVED the price and whether it moved alone; both halves are answerable
    whether or not the move arrived in discrete steps. UBER is the live case — −18.8% over the year
    with a worst single day of −6.9%, so the −10% detector fires never and the reader was shown a
    line of text where every other name got a chart.

    THE SCREEN SELECTS FOR GAPS, which is why this looked like an edge case and is not: a
    compounder followed deliberately is exactly the name that bleeds. Today UBER is the only
    committed name with zero gaps and the only quality name — that correlation is the point.

    Asserted on the RENDERER's contract rather than on a browser: `drawdownChart` consumes `rows`
    only to build gap markers, so an empty list must still yield a chart. If that stops being true
    the gradual branch silently returns to a bare sentence."""
    import re

    js = (SRC.parents[1] / "frontend" / "views" / "shared" / "dossier.js").read_text()
    fn = re.search(r"function readWhatBroke\(.*?\n\}\n", js, re.S)
    assert fn, "readWhatBroke is gone"
    body = fn.group(0)
    assert "drawdownChart(sp, [], det)" in body, (
        "the no-gap branch no longer draws the price path — a gradual-decline name is back to one "
        "line of text while every gap name gets a chart")
    # the same chart, not a second renderer: rows are consumed ONLY for markers
    chart = re.search(r"export function drawdownChart\(sp, rows, det\) \{(.*?)\n\}\n", js, re.S)
    assert chart, "drawdownChart is gone"
    uses = re.findall(r"\brows\b", chart.group(1))
    assert len(uses) <= 2, (
        f"drawdownChart now reads `rows` in {len(uses)} places — passing an empty list may no "
        f"longer produce a usable chart, which is what the gradual branch depends on")
    # and it must say WHY nothing is marked, rather than leaving a bare unannotated chart
    assert "No discrete gap-downs" in body and "detector" in body, (
        "the gradual branch does not state why nothing is marked — an unannotated chart beside a "
        "gap-annotated one on every other page reads as a missing annotation, not an absent event")
