"""A spot that names no day cannot be checked by anything, ever — so the write refuses it.

WHAT THE GATE IS FOR. `vinci audit spot` compares a record's spot against the store's bar for the
day it claims to be. Against a record naming no day it checks NOTHING and reports UNAUDITABLE
forever. The fleet measurement was blunt about the stakes: every committed spot IS a real EOD
close, exact to the stored bar — but the ones carrying no date cannot be shown to be. This gate
does not verify the date (that is the audit's job, and deliberately a flag rather than a refusal);
it requires the CLAIM, so that something exists to check.

THE ADOPTION TRAP WAS THE GATING QUESTION, AND IT WAS CHECKED BEFORE ANY DESIGN. Two committed
records legitimately carry no date — BRBR and EPAM are struck at 2026-08-07, which only the `-sl`
worktree's store can see, and writing a date this checkout cannot verify would assert from another
store's authority. A blanket requirement makes those two unwritable. Measured:

    every committed record          schema 1.3   (8 live + 3 archived, one at 1.2)
    a NEW record defaults to        SCHEMA_VERSION
    `write_record` on an existing   PRESERVES its schema_version — driven, not read

So a 1.3 record stays 1.3 through every re-write and can never fall into a 1.5 gate. No trap. That
premise is pinned below, because the gate's safety rests on it: if a write path ever starts
re-stamping the version, BRBR and EPAM become unwritable and the failure would look like a bug in
something else entirely.

THE COHERENCE HALF IS NOT VERSION-GATED. A stated `spot_as_of` that postdates its own underwrite is
wrong at any schema and costs nothing to refuse — measured across the six stamped records, every
spot precedes its underwrite by 1-3 days. That is #416's lookahead lesson applied at the seat where
the value is WRITTEN rather than where it is rendered.
"""
from __future__ import annotations

import json
import warnings
from datetime import date
from pathlib import Path
from typing import Any

import pytest

import vinci.scenarios as sc

SMPL = Path("scenarios/SMPL.json")


def _v15(**over: Any) -> sc.ScenarioRecord:
    """A VALID schema-1.5 record, built from a REAL committed one rather than hand-rolled.

    The 1.4 vintage rule binds before this gate, so a record simply re-stamped to 1.5 is refused by
    `require_fielded_refs` and never reaches it — which is how the first draft of these tests
    "passed" while checking nothing. Every reference is given a vintage so the earlier gates are
    genuinely satisfied and the refusal under test is the one that fires.
    """
    doc = json.loads(SMPL.read_text())
    doc["schema_version"] = "1.5"
    for axis in (doc.get("assumptions") or {}).values():
        for ref in axis.get("references") or []:
            ref["vintage"] = ref.get("vintage") or "FY2025 (10-K filed 2026-01-28)"
    rec = sc.ScenarioRecord.model_validate(doc)
    return rec.model_copy(update=over) if over else rec


def _write(rec: sc.ScenarioRecord, tmp_path: Path) -> Path:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return sc.write_record(rec, root=tmp_path)


# ─── the trap that had to be checked first ────────────────────────────────────────────────────

def test_every_committed_record_sits_below_the_gate() -> None:
    """THE CHECK THAT GATED THE DESIGN. If any committed record were at or above the threshold
    while carrying no date, this gate would make it unwritable the moment it shipped."""
    threshold = sc._schema_ver(sc.SPOT_AS_OF_REQUIRED_FROM)
    trapped = []
    for p in sorted(Path("scenarios").rglob("*.json")):
        if p.stem.startswith("_"):
            continue
        doc = json.loads(p.read_text())
        ver = sc._schema_ver(str(doc.get("schema_version")))
        if ver >= threshold and not doc.get("spot_as_of"):
            trapped.append(f"{p.stem} (v{doc.get('schema_version')})")
    assert not trapped, (
        f"these records are at/above the {sc.SPOT_AS_OF_REQUIRED_FROM} gate with no spot_as_of, so "
        f"the gate makes them unwritable: {trapped}")


def test_a_re_write_preserves_the_records_own_schema_version(tmp_path: Path) -> None:
    """THE PREMISE THE GATE'S SAFETY RESTS ON, driven rather than assumed. If a write path ever
    re-stamps the version, BRBR and EPAM jump into the gate and become unwritable — and the failure
    would surface far from here, looking like a bug in something else."""
    for tk in ("BRBR", "EPAM"):
        rec = sc.ScenarioRecord.model_validate_json(Path(f"scenarios/{tk}.json").read_text())
        assert rec.spot_as_of is None, f"{tk} now has a date — this test's premise has moved"
        back = json.loads(_write(rec, tmp_path).read_text())
        assert back["schema_version"] == rec.schema_version, (
            f"{tk}: the write re-stamped {rec.schema_version} → {back['schema_version']}, which "
            f"walks it into the spot_as_of gate it cannot satisfy")


def test_the_two_dateless_records_still_write(tmp_path: Path) -> None:
    """The trap, driven end to end on the real records rather than argued from versions."""
    for tk in ("BRBR", "EPAM"):
        rec = sc.ScenarioRecord.model_validate_json(Path(f"scenarios/{tk}.json").read_text())
        assert _write(rec, tmp_path).is_file()


# ─── the gate itself ──────────────────────────────────────────────────────────────────────────

def test_a_new_record_without_a_spot_date_is_refused(tmp_path: Path) -> None:
    """THE WHOLE POINT. A 1.5 record naming no day for its spot cannot be written."""
    with pytest.raises(ValueError) as exc:
        _write(_v15(spot_as_of=None), tmp_path)
    msg = str(exc.value)
    assert "requires `spot_as_of`" in msg, msg
    assert "UNAUDITABLE" in msg, "the refusal does not say what is lost without it"
    assert "scenario-propose" in msg, "the refusal does not say where the date comes from"


def test_a_new_record_with_a_spot_date_writes(tmp_path: Path) -> None:
    """THE NEGATIVE HALF. A gate that refuses everything is a freeze, and this one has to let the
    ordinary case through — SMPL's real date, 1 day before its underwrite."""
    assert _write(_v15(), tmp_path).is_file()


def test_a_spot_dated_after_its_own_underwrite_is_refused_at_any_schema(tmp_path: Path) -> None:
    """THE COHERENCE HALF, deliberately NOT version-gated (#416's lookahead lesson, moved to the
    write seat). Legs cannot have been struck against a close that had not happened yet — true at
    schema 1.3 as much as 1.5, and no committed record pays for it: all six stamped spots precede
    their underwrite by 1-3 days."""
    old = sc.ScenarioRecord.model_validate_json(SMPL.read_text())   # a 1.3 record
    assert sc._schema_ver(old.schema_version) < sc._schema_ver(sc.SPOT_AS_OF_REQUIRED_FROM)
    with pytest.raises(ValueError) as exc:
        _write(old.model_copy(update={"spot_as_of": date(2027, 1, 1)}), tmp_path)
    assert "AFTER the underwrite date" in str(exc.value), str(exc.value)


def test_the_six_stamped_records_all_precede_their_underwrite() -> None:
    """The measurement the rule above rests on, pinned so a later record cannot quietly invert it
    and be excused as 'how it has always been'."""
    checked = 0
    for p in sorted(Path("scenarios").glob("*.json")):
        if p.stem.startswith("_"):
            continue
        doc = json.loads(p.read_text())
        if not doc.get("spot_as_of"):
            continue
        checked += 1
        assert str(doc["spot_as_of"]) <= str(doc["underwrite_date"])[:10], (
            f"{p.stem}: spot dated {doc['spot_as_of']} against underwrite {doc['underwrite_date']}")
    assert checked >= 6, f"only {checked} records carry a spot date — expected the six stamped"


# ─── the template that has to satisfy it ──────────────────────────────────────────────────────

def test_the_proposal_template_prefills_the_date_from_the_dossiers_own_bar() -> None:
    """A REQUIREMENT NO PATH CAN SATISFY IS A FREEZE. `scenario-propose` is the one route into a
    record, so it must emit the field — pre-filled from `stock_info.as_of`, which IS the bar date
    the price came from (`Sourced` carries no date of its own, so it lives one level up)."""
    import inspect

    from vinci.dossier import propose
    src = inspect.getsource(propose)
    assert '"spot_as_of": _get(doc, "mechanical", "stock_info", "as_of")' in src, (
        "the template no longer pre-fills spot_as_of — the gate becomes unsatisfiable from the "
        "only path that is supposed to satisfy it")


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_every_committed_dossier_can_supply_the_date() -> None:
    """The prefill is only real if the source exists. All 14 carry `stock_info.as_of`; a name
    without one would produce a template that cannot pass the gate."""
    missing = [p.parent.name for p in sorted(Path("data/dossiers").glob("*/dossier.json"))
               if not (((json.loads(p.read_text()).get("mechanical") or {})
                        .get("stock_info") or {}).get("as_of"))]
    assert not missing, f"these dossiers cannot pre-fill spot_as_of: {missing}"


# ─── the adjacent write path ──────────────────────────────────────────────────────────────────

def test_supersede_refuses_before_it_writes_the_archive(tmp_path: Path) -> None:
    """SELF-REVIEW FINDING, and it is the pattern that has caught this batch four times: fix the
    case in front of you, leave the one beside it.

    `scenario-supersede` writes the ARCHIVE first and the live record second. A refusal on the
    second therefore left an orphan archive on disk — a superseded record with no successor, and a
    seal manifest never updated. Demonstrated before the fix:

        write_archived  → SMPL-2026-08-05.json   on disk: True
        write_record    → RAISED
        orphan archive present: True · live record written: False

    The window predates this PR (the basis and fielded-ref gates raise at the same point), but the
    spot gate makes it far likelier to fire, because a fresh hand-written payload commonly omits
    `spot_as_of` until the field is habit. `validate_for_write` is the same refusals as one
    callable, so the pre-check cannot drift from the write."""
    bad = _v15(spot_as_of=None)
    with pytest.raises(ValueError):
        sc.validate_for_write(bad)
    # …and the same record passes once the field is stated, so this is a gate and not a freeze
    sc.validate_for_write(_v15())

    # the CLI seat: the refusal must come BEFORE anything reaches disk
    import inspect

    import vinci.cli as cli
    src = inspect.getsource(cli._cmd_scenario_supersede)
    pre = src.index("sc.validate_for_write(live)")
    assert pre < src.index("sc.write_archived("), (
        "the pre-check runs after the archive is written — the orphan window is open again")


def test_validate_for_write_is_the_writes_own_refusal_set() -> None:
    """ONE DEFINITION, TWO CALL SITES. If `write_record` stopped calling it, the pre-check would
    still pass records the write then refused — and a gate added later could be enforced at the
    write and skipped at the pre-check, which is the drift this extraction exists to prevent."""
    import inspect
    assert "validate_for_write(rec)" in inspect.getsource(sc.write_record), (
        "write_record no longer routes through the shared validator")
