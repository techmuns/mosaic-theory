"""THE PROMPT ASKS FOR EVERY FIGURE THE 19c GUARD DEMANDS (audit D-D5, follow-up).

THE DEFECT. `uncited_material_figures` refuses a synthesis whose prose never states a MATERIAL
financial-summary figure, and #858 widened "material" to 5% of revenue. But the prompt never said
so: the rows were marked only AFTER the synthesis was asked (`assemble._mark_material` ran below
`synthesize`), so the facts the model read carried `"material": false` on the very rows the guard
then demanded, and no line of the prompt named them. The 2026-10-29 rebuild paid for five draws on
two pages and had both refused — a merger and restructuring charge of 5.63% of revenue on one, an
in-process R&D charge of 9.33% on the other — each a figure the model was never told it owed.

THE PINS. The guard is the oracle and the PROMPT SENT is the artifact: a capturing client records
the user message `synthesize` hands the model, and the lines of it that name a material row,
read back as a synthesis's prose, must satisfy the guard. On the five frozen annual tables
(c51c286a) and the frozen SMPL page, and as an invariant over every committed page — where a page
with no material row must get no section. A mutation of the one shared selection moves the guard
and the prompt together, and the marks must be set before the synthesis is asked.

No assertion reads LLM-composed text: the prompt is built by code from committed data.
"""
from __future__ import annotations

import ast
import inspect
import json
import typing
from pathlib import Path

import pytest

from vinci.dossier import assemble
from vinci.dossier import synthesis as syn
from vinci.dossier.schemas import MechanicalLayer
from vinci.graph.llm import LlmError

ROOT = Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
_TABLES = ROOT / "tests" / "fixtures" / "materiality_revenue" / "annual_tables.json"
_CARRIER = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"


class _Capture:
    """Records the prompt `synthesize` sends, then fails the draw — the prompt is what is pinned,
    and a failed draw returns before any validation reads a reply."""

    def __init__(self) -> None:
        self.users: list[str] = []

    @property
    def model(self) -> str:
        return "capture"

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        self.users.append(user)
        raise LlmError("captured")


class _Synth:
    """The fields the guard reads, with ``prose`` as the one bear point."""

    def __init__(self, prose: str) -> None:
        self.bull_points: list[object] = []
        self.bear_points: list[object] = [prose]
        self.key_unknowns: list[object] = []


def _sent(mech: MechanicalLayer) -> str:
    llm = _Capture()
    syn.synthesize(mech, llm=llm, ticker="X", name="X Co")  # type: ignore[arg-type]
    assert len(llm.users) == 1
    return llm.users[0]


def _stripped(m: dict[str, typing.Any]) -> dict[str, typing.Any]:
    """The state the assembler hands `_mark_material`: no row marked yet."""
    for r in ((m.get("financial_summary") or {}).get("annual") or {}).get("value", {}) \
            .get("rows", []):
        r["material"] = False
    return m


def _frozen(ticker: str) -> MechanicalLayer:
    """A frozen annual table and market cap (c51c286a) inside the frozen SMPL page's mechanical
    layer, so the input is the real type throughout; SMPL is that page as frozen. Unmarked."""
    m = json.loads(_CARRIER.read_text())["mechanical"]
    if ticker != "SMPL":
        page = json.loads(_TABLES.read_text())[ticker]
        m["financial_summary"]["annual"] = page["annual"]
        m["stock_info"]["market_cap"]["value"] = page["market_cap"]
    return MechanicalLayer.model_validate(_stripped(m))


def _material_labels(mech: MechanicalLayer) -> list[str]:
    ann = mech.financial_summary.annual.value if (
        mech.financial_summary and mech.financial_summary.annual) else None
    return [r.label for r in (ann.rows if ann is not None else []) if r.material]


def _assert_prompt_states_the_demands(mech: MechanicalLayer, where: str) -> int:
    """The lines of the sent prompt that name a material row satisfy the guard on their own, and
    each such row's figure line names the table's source_ref. Returns how many figures the guard
    demanded of an empty argument (the pin's bite)."""
    demanded = syn.uncited_material_figures(_Synth(""), mech)  # type: ignore[arg-type]
    user = _sent(mech)
    labels = _material_labels(mech)
    lines = [ln for ln in user.splitlines() if any(lab in ln for lab in labels)]
    left = syn.uncited_material_figures(_Synth("\n".join(lines)), mech)  # type: ignore[arg-type]
    assert left == [], (
        f"{where}: the prompt sent never states {left} — the guard will refuse every draw that "
        "does not happen to state it unprompted")
    ref = mech.financial_summary.annual.source_ref if mech.financial_summary \
        and mech.financial_summary.annual else None
    for lab in labels:
        if any(d.startswith(f"{lab} ") for d in demanded):
            assert ref and any(lab in ln and ref in ln for ln in lines), (
                f"{where}: no line names {lab!r} beside the source_ref a point stating it cites")
    if demanded:
        assert syn.MATERIAL_FIGURES_HEADER in user, where
    else:
        assert syn.MATERIAL_FIGURES_HEADER not in user, (
            f"{where}: a page with no material figure carries the section")
    return len(demanded)


@pytest.mark.parametrize("ticker", ["AMZN", "GOOGL", "LLY", "MVST", "SMPL", "WLK"])
def test_the_prompt_sent_states_every_figure_the_guard_demands(ticker: str) -> None:
    """(-) On main the material rows reach the model only as `"label": …` lines of the facts dump
    with `"material": false` beside them, so read back as prose they satisfy nothing the guard
    asks. Marked the way `assemble_one` marks them, the prompt must state each figure."""
    mech = assemble._mark_material(_frozen(ticker))
    assert _assert_prompt_states_the_demands(mech, ticker) >= 1, (
        f"{ticker}: the frozen table demands no figure — the pin is not biting")


def test_every_committed_page_prompt_states_what_its_guard_demands() -> None:
    """(-)(+) INVARIANT over every committed page, marked as assembly marks it: a page with a
    material figure is asked for each one, and a page with none gets no section. Phrasing-
    independent, so it holds across every re-assembly; the counts say it bit on both sides."""
    with_demands = without = 0
    for page in sorted(DOSS.glob("*/dossier.json")):
        m = json.loads(page.read_text())["mechanical"]
        mech = assemble._mark_material(MechanicalLayer.model_validate(_stripped(m)))
        if _assert_prompt_states_the_demands(mech, page.parent.name):
            with_demands += 1
        else:
            without += 1
    assert with_demands >= 5 and without >= 5, (with_demands, without)


def test_a_page_with_no_material_row_gets_no_section() -> None:
    """(+) The frozen SMPL page as the assembler hands it over before any mark: no row is material,
    so the guard demands nothing and the prompt carries no section."""
    mech = _frozen("SMPL")
    assert syn.uncited_material_figures(_Synth(""), mech) == []  # type: ignore[arg-type]
    assert syn.MATERIAL_FIGURES_HEADER not in _sent(mech)


def test_the_guard_and_the_prompt_read_one_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """A MUTATION OF THE SHARED SELECTION MOVES BOTH. Raising the floor above every figure empties
    the guard's demand and the prompt's section together; a selection returning a figure no table
    holds is demanded by the guard and listed by the prompt. Two copies of the loop would let one
    side move alone, which is the drift this exists to prevent."""
    mech = assemble._mark_material(_frozen("LLY"))
    assert syn.uncited_material_figures(_Synth(""), mech)  # type: ignore[arg-type]
    assert syn.MATERIAL_FIGURES_HEADER in _sent(mech)

    monkeypatch.setattr(syn, "MATERIAL_FIGURE_FLOOR_MUSD", 1e12)
    assert syn.uncited_material_figures(_Synth(""), mech) == []  # type: ignore[arg-type]
    assert syn.MATERIAL_FIGURES_HEADER not in _sent(mech)
    monkeypatch.undo()

    fake = syn.MaterialFigure(label="Mutant Row ($M)", periods=("FY99",), value=-777.7,
                              source_ref="mutant ref")
    monkeypatch.setattr(syn, "demanded_material_figures", lambda _m: [fake])
    assert syn.uncited_material_figures(_Synth(""), mech) == [  # type: ignore[arg-type]
        "Mutant Row ($M) FY99 = -777.7"]
    user = _sent(mech)
    line = next(ln for ln in user.splitlines() if "Mutant Row ($M)" in ln)
    assert "FY99" in line and "mutant ref" in line
    assert syn.uncited_material_figures(_Synth(line), mech) == []  # type: ignore[arg-type]


def test_the_rows_are_marked_before_the_synthesis_is_asked() -> None:
    """THE ORDER IS THE GUARANTEE. `synthesize` lists only rows already marked, so a mark set after
    it leaves the prompt with no section while the guard still demands — the 2026-10-29 refusals.
    The guard had the same shape once (`test_the_guard_runs_after_the_flags_it_reads`)."""
    tree = ast.parse(inspect.getsource(assemble.assemble_one))

    def first(name: str) -> int:
        hits = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == name]
        assert hits, f"assemble_one never calls {name}"
        return min(hits)

    assert first("_mark_material") < first("synthesize"), (
        "`_mark_material` runs after `synthesize`: the model is asked with no row marked, so the "
        "prompt names none of the figures `uncited_material_figures` then refuses the draw for")


def test_the_section_carries_no_direction() -> None:
    """The section lists figures and where they may be stated; it never names a lean, a verdict or
    a recommendation (the directional lint's vocabulary)."""
    mech = assemble._mark_material(_frozen("LLY"))
    user = _sent(mech)
    section = user[user.index(syn.MATERIAL_FIGURES_HEADER):]
    assert not syn._DIRECTIONAL.search(section), syn._DIRECTIONAL.findall(section)
    for word in ("bullish", "bearish", "lean", "verdict"):
        assert word not in section.lower(), word
