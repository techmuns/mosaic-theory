"""A fresh assembly's anchor carries the CIQ-bridged inputs the backfill writes (STATE row 27 (7)).

`assemble.py` called `compute_anchor` with no `ciq=`, so an input EDGAR does not tag and the CIQ
workbook does went UNKNOWN on every re-assembly: on the 2026-10-26 pass GOOGL's D&A (its anchor
turned inapplicable) and ORKA's net debt, until `anchor-backfill` restored both. FUBO's net debt,
LLY's FCF and MVST's D&A and net debt sat on that EDGAR-only read on main (7 of the 27 pages a
fresh assembly degraded, measured at `47d8ca27`).

These pins run the assembly's own anchor chain — `_assembly_anchor`, the R4 proposal, and the
committed-recipe rule `_keep_committed_recipe` applies — on a FROZEN cut of the real inputs
(`tests/fixtures/anchor_ciq_bridge.json`: the page subset the chain reads, the backfilled anchor
block, the four CIQ facts the bridge reads, companyfacts trimmed to the tags the chain's output
depends on). The workbook itself is licensed and git-ignored, so the one thing replaced here is
`ciq_balance.extract`, with the derived facts it returned on the real workbook.
"""
from __future__ import annotations

import inspect
import json
import pathlib
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.dossier import assemble as asm
from vinci.dossier import ciq_balance, recipe_proposal
from vinci.dossier.anchor import DQ_VENDOR_BRIDGE, Anchor, preserve_operator_tag
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.ciq_balance import CiqFact, CiqFacts

ROOT = pathlib.Path(__file__).resolve().parents[1]
CUT: dict[str, dict[str, Any]] = json.loads(
    (ROOT / "tests" / "fixtures" / "anchor_ciq_bridge.json").read_text())["names"]
T0 = datetime(2026, 10, 27, tzinfo=UTC)

#: The input only CIQ supplies on each name — the one the 2026-10-26 pass dropped.
VENDOR_INPUT = {"GOOGL": "d_and_a", "ORKA": "net_debt"}

#: Fields a fresh assembly now writes differently from the committed block, ON PURPOSE: the anchor's
#: D&A must be the filer's current year (`docs/records/2026-10-27-the-anchors-dep-amort-reads-the-
#: guarded-line.md`). ORKA's EDGAR D&A is FY2023 ($0.015M), two years behind its FY2025, so the
#: bridge fills it from the workbook ($0.134M) and the vendor list names it. The page refreshes in
#: the next artifact pass; until then this is a recorded difference. GOOGL's bridged D&A keeps its
#: value and source and changes only its BASIS text: the workbook's last column is its LTM to
#: 2026-06-30, which was labelled "consolidated latest FY" (review of #830; the period is read off
#: the column header, `ciq_balance.header_period`, and frozen here beside the fact).
MOVED_BY_THE_DA_GUARD = {"ORKA": ("d_and_a", "data_quality_detail"), "GOOGL": ("d_and_a",)}


def _vendor_filled(a: Anchor) -> set[str]:
    """The inputs the anchor's own detail line says the CIQ workbook supplied."""
    for line in a.data_quality_detail or []:
        if line.startswith("vendor bridge: "):
            return set(line.removeprefix("vendor bridge: ").split(" supplied by")[0].split(", "))
    return set()


def _fact(v: dict[str, Any]) -> CiqFact:
    """A frozen fact; its period end (the column header's date) is stored as ISO text, and the
    export(s) it was read from (audit A-D6) as JSON lists."""
    end = v.get("period_end")
    return CiqFact(**{**v, "period_end": date.fromisoformat(end) if end else None,
                      "workbooks": tuple(tuple(w) for w in v.get("workbooks", []))})


def _ciq(t: str, *, drop: str | None = None, failures: list[str] | None = None) -> CiqFacts:
    c = CUT[t]["ciq"]
    return CiqFacts(ticker=t, as_of=None, source_file=c["source_file"],
                    source_sha256=c["source_sha256"],
                    facts={k: _fact(v) for k, v in c["facts"].items() if k != drop},
                    checks=list(c["checks"]), failures=list(failures or []))


def _committed(t: str) -> Anchor:
    return Anchor.model_validate(CUT[t]["anchor"])


def _fields(a: Anchor) -> dict[str, Any]:
    out = a.model_dump(mode="json")
    out.pop("computed_at")
    # the bridge's scale-check outcome (2026-10-27) postdates the frozen cut; it is pinned on its
    # own in tests/test_ciq_bridge_currency_and_scale.py
    out.pop("ciq_scale_check")
    return out


def _assembled(t: str, ciq: CiqFacts | None, monkeypatch: pytest.MonkeyPatch) -> Anchor:
    """The anchor a fresh assembly writes for ``t``. ``ciq`` None = the real read of a name with no
    CIQ pull (an empty bundle); otherwise the workbook read returns ``ciq``."""
    if ciq is not None:
        monkeypatch.setattr(ciq_balance, "extract", lambda _bundle, _ticker: ciq)
    page = CUT[t]["page"]
    fresh = asm._assembly_anchor(page["mechanical"], facts=CUT[t]["companyfacts"],
                                 bundle=CiqBundle.from_files(t, []), ticker=t, computed_at=T0)
    kept, _notes = preserve_operator_tag(_committed(t), recipe_proposal.propose(page, fresh))
    return kept


# --- POSITIVE: the fresh assembly writes the backfilled block ---------------------------------

@pytest.mark.parametrize("t", sorted(VENDOR_INPUT))
def test_a_fresh_assembly_writes_the_backfilled_anchor(
        t: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every field of the block `anchor-backfill` wrote on 2026-10-26, `computed_at` aside —
    GOOGL's operator decision and base value included, because its D&A is what makes R1 applicable
    there."""
    got = _assembled(t, _ciq(t), monkeypatch)
    moved = MOVED_BY_THE_DA_GUARD.get(t, ())
    fresh, committed = _fields(got), _fields(_committed(t))
    assert {k: v for k, v in fresh.items() if k not in moved} == {
        k: v for k, v in committed.items() if k not in moved}
    if moved:   # the recorded move, pinned rather than skipped
        assert got.d_and_a is not None and got.d_and_a.basis == (
            "consolidated trailing twelve months to 2026-06-30 (CIQ workbook, vendor basis)")
        assert got.d_and_a.value == CUT[t]["ciq"]["facts"]["d_and_a"]["value"]
        assert got.d_and_a.source.startswith("CIQ")
    if t == "ORKA":
        assert fresh["d_and_a"]["value"] != committed["d_and_a"]["value"]
        assert "EDGAR D&A withheld" in (got.d_and_a.source if got.d_and_a else "")
    if t == "GOOGL":   # the label only
        assert {k: v for k, v in fresh["d_and_a"].items() if k != "basis"} == {
            k: v for k, v in committed["d_and_a"].items() if k != "basis"}
    vin = getattr(got, VENDOR_INPUT[t])
    assert vin.value is not None and vin.source.startswith("CIQ"), (
        f"{t}: {VENDOR_INPUT[t]} must be the workbook's figure, stamped as the vendor's")
    assert DQ_VENDOR_BRIDGE in (got.data_quality or "")


def test_the_backfill_reads_the_same_bridge(monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: pathlib.Path) -> None:
    """The two write paths read ONE bridge: `anchor-backfill`'s computation (`_machine_anchor`) on
    the same frozen inputs gives the same block as the assembly's."""
    from vinci import cli

    for t in sorted(VENDOR_INPUT):
        ciq = _ciq(t)
        monkeypatch.setattr(ciq_balance, "extract", lambda _bundle, _ticker, c=ciq: c)
        page = CUT[t]["page"]
        d = SimpleNamespace(mechanical=SimpleNamespace(
            model_dump=lambda mode, m=page["mechanical"]: m))
        resolver = SimpleNamespace(resolve_ticker=lambda _t: SimpleNamespace(cik="0"))
        edgar = SimpleNamespace(companyfacts=lambda _cik, f=CUT[t]["companyfacts"]: f)
        machine = cli._machine_anchor(t, d, json.dumps(page), SimpleNamespace(data_dir=tmp_path),
                                      resolver, edgar)
        assert machine is not None
        backfilled, _notes = preserve_operator_tag(_committed(t), machine)
        assert _fields(backfilled) == _fields(_assembled(t, ciq, monkeypatch)), t


def test_assemble_one_builds_its_anchor_through_the_bridge() -> None:
    """`assemble_one` cannot be driven offline (CIQ + EDGAR + LLM), so its wiring is read off the
    source: the anchor comes from `_assembly_anchor`, never a bare `compute_anchor` call — the call
    that had no `ciq=`."""
    src = inspect.getsource(asm.assemble_one)
    # the exact call, not the bare name: a comment naming the helper would satisfy a name search
    assert ("anchor = _assembly_anchor(mech.model_dump(mode=\"json\"), facts=anchor_facts, "
            "bundle=bundle,") in src
    assert "compute_anchor(" not in src


# --- NEGATIVE: no CIQ value, no number ---------------------------------------------------------

@pytest.mark.parametrize("t", sorted(VENDOR_INPUT))
def test_a_name_with_no_ciq_pull_still_reads_unknown(
        t: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """The state main's assembly wrote, and the one every universe name without a CIQ pull keeps:
    the hole stays UNKNOWN and nothing is flagged as vendor-filled. It also shows the positive pin
    can fail — this block differs from the backfilled one."""
    got = _assembled(t, None, monkeypatch)
    vin = getattr(got, VENDOR_INPUT[t])
    assert vin.value is None and vin.source.startswith("UNKNOWN")
    assert DQ_VENDOR_BRIDGE not in (got.data_quality or "")
    assert _fields(got) != _fields(_committed(t))


@pytest.mark.parametrize("t", sorted(VENDOR_INPUT))
def test_a_workbook_without_the_value_leaves_it_unknown(
        t: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A workbook on file that carries no row for the input fills nothing — never a guess. (ORKA's
    D&A is still bridge-filled here, its own row being present: the vendor list must not name
    the dropped input.)"""
    got = _assembled(t, _ciq(t, drop=VENDOR_INPUT[t]), monkeypatch)
    vin = getattr(got, VENDOR_INPUT[t])
    assert vin.value is None and vin.source.startswith("UNKNOWN")
    assert VENDOR_INPUT[t] not in _vendor_filled(got)
    if t not in MOVED_BY_THE_DA_GUARD:
        assert DQ_VENDOR_BRIDGE not in (got.data_quality or "")


@pytest.mark.parametrize("t", sorted(VENDOR_INPUT))
def test_a_refused_extraction_hands_on_nothing(t: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A sheet that failed a coherence check is not handed on in part: its value is withheld."""
    got = _assembled(t, _ciq(t, failures=["D&A: income-statement line EXCEEDS the total"]),
                     monkeypatch)
    vin = getattr(got, VENDOR_INPUT[t])
    assert vin.value is None and vin.source.startswith("UNKNOWN")
    assert DQ_VENDOR_BRIDGE not in (got.data_quality or "")
