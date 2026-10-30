"""'Free cash flow' meant two different things, and the page named neither.

THE FINDING, MEASURED ACROSS THE COMMITTED FLEET. `quality.free_cash_flow` reads CIQ's
`Levered Free Cash Flow` row. Against the SAME sheet's `Cash from Ops. − Capital Expenditure`, the
two agree on exactly ONE name — V, 0.97x. The other thirteen:

    NFLX 2.28x   MVST 1.54x   CNXC 1.51x   EPAM 1.35x   NCNO 1.25x   V 0.97x
    SMPL 0.89x   IT 0.85x     UBER 0.72x   BRBR 0.70x   VITL 0.60x   VRRM 0.51x
    FUBO 0.27x   AORT −0.47x  ← opposite signs

NFLX is why it reaches a reader: its page carried **$25,388M** while CFO − capex is **$11,152M**
and the company itself guides to roughly $12.5bn — the page's FCF was twice management's own
number, under a synthesis that quotes it as evidence of self-funding. The early years make the
divergence unmistakable: FY17 reads **+$6,673M** levered while CFO that year was **−$1,786M**.

AORT is the shape that cannot be waved through: +$14.6M derived against −$7.3M levered. One says
the business generated cash and the other says it consumed it.

THE CIQ FIGURE IS KEPT, NOT REPLACED — it is the panel's own measure, defined consistently across
the comp set, and swapping it for our arithmetic would put a derived number where a reader takes
the vendor's. Both are stated, each named.

AND THE ROWS HAD TO BE FIXED FIRST. `Revenue ($M)` carried 12 structured values while
`CFO`/`Capex`/`FCF` carried **zero** — display strings only, so anything wanting CFO − capex had to
re-parse `"11,971"` out of rendered text. That is the forbidden shape ("parsers consume structured
values, never rendered strings"), and the thousands-blind `$1,101.80M` re-parse is what it costs.
`clean_num` already produced the number; the old cell helper formatted it and threw it away.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.ciq_sheets import _fcf_basis_note

PERIOD = "LTM 12 months Jun-30-2026"


def _rows(cfo: float | None, capex: float | None) -> list[list[Any]]:
    """A Cash Flow sheet in the REAL shape `_find_row`/`latest_cell`/`_period_header` consume:
    a Fiscal Period header row, then labelled rows whose column 0 is the label."""
    return [
        ["Fiscal Period", PERIOD],
        ["Cash from Ops.", cfo if cfo is not None else ""],
        ["Capital Expenditure", capex if capex is not None else ""],
        ["Levered Free Cash Flow", 999.0],
    ]


# ─── the three readings ───────────────────────────────────────────────────────────────────────

def test_a_divergent_basis_states_both_figures_and_the_gap() -> None:
    """NFLX'S REAL NUMBERS. The reader is given the other basis and the multiple between them —
    without which $25,388M reads as the company's own free cash flow, which it is not."""
    note = _fcf_basis_note(_rows(11_970.8, -818.8), 25_387.6, PERIOD, 1)
    assert "NOT CFO − capex" in note
    assert "11,970.8" in note and "818.8" in note and "11,152.0" in note
    assert "2.28x apart" in note, note
    assert "should say which it used" in note


def test_opposite_signs_are_said_in_words_not_as_a_negative_multiple() -> None:
    """AORT'S REAL SHAPE, and the loudest case in the corpus: +$14.6M derived against −$7.3M
    levered. Rendered as a ratio it reads "−0.50x apart", which tells a reader nothing; the
    difference is cash-generative versus cash-consuming."""
    note = _fcf_basis_note(_rows(58.0, -43.4), -7.3, PERIOD, 1)
    assert "OPPOSITE SIGNS" in note, note
    assert "-0.50x" not in note and "−0.50x" not in note, "a bare negative multiple hides the sign"
    assert "generated cash" in note and "consumed it" in note


def test_agreement_is_stated_without_claiming_the_measures_are_the_same() -> None:
    """V IS THE ONE AGREEING NAME, and the wording has to keep agreement apart from identity: two
    different measures landing within 5% this period say nothing about next period. The first
    draft read 'NOT CFO − capex … the two agree', which contradicts itself."""
    note = _fcf_basis_note(_rows(22_580.0, -1_567.0), 20_404.0, PERIOD, 1)
    assert "within 5%" in note
    assert "NOT CFO − capex" not in note, "the note contradicts itself on an agreeing name"
    assert "still different measures" in note


def test_a_missing_cfo_or_capex_row_says_so_rather_than_going_silent() -> None:
    """FAIL LOUD, and still name the basis: the CIQ figure's DEFINITION is worth stating even when
    the other basis cannot be computed — that is the half a reader needs most."""
    rows = [["Fiscal Period", PERIOD], ["Levered Free Cash Flow", 100.0]]
    note = _fcf_basis_note(rows, 100.0, PERIOD, 1)
    assert "NOT CFO − capex" in note and "no 'Cash from Ops.'" in note
    empty = _fcf_basis_note(_rows(None, None), 100.0, PERIOD, 1)
    assert "cannot be stated for" in empty and "no value in that column" in empty, empty


# ─── the structured values the note depends on ────────────────────────────────────────────────

@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_the_cash_flow_rows_carry_structured_values_not_only_display_strings() -> None:
    """THE SHAPE RULE, pinned on the committed artifacts. `CFO`/`Capex`/`FCF` shipped with `cells`
    and an EMPTY `values`, so a consumer had to re-parse rendered text to get a number — while
    `Revenue ($M)` beside them carried its values all along. The fix is not cosmetic: it is what
    lets anything downstream compute CFO − capex without a display-string parse.

    Asserts the INVARIANT (values present and as long as cells), never a figure — these tables are
    re-assembled and their numbers move."""
    checked = 0
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        if (p.parent / "known_wrong.json").exists():
            continue          # sealed BY DERIVATION — `refresh_dossier` refuses a transform on it
        ann = (((json.loads(p.read_text()).get("mechanical") or {})
                .get("financial_summary") or {}).get("annual") or {}).get("value") or {}
        for row in ann.get("rows") or []:
            if str(row.get("label", "")).split(" ")[0] not in {"CFO", "Capex", "FCF"}:
                continue
            checked += 1
            vals, cells = row.get("values") or [], row.get("cells") or []
            assert vals, (
                f"{p.parent.name}: {row['label']} carries {len(cells)} display cells and NO "
                f"structured values — a consumer must re-parse the strings")
            assert len(vals) == len(cells), (
                f"{p.parent.name}: {row['label']} has {len(vals)} values for {len(cells)} cells")
    assert checked, "no cash-flow rows found — this test checked nothing"


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_every_committed_fcf_states_its_basis() -> None:
    """A note nobody renders ships nothing (#415's lesson, in a new form): `_fact` prints a note
    only when the fact is NOT present, so a PRESENT figure's note reaches the JSON and never the
    page. The FCF line is rendered specially for exactly that reason, and this pins that every
    committed record actually carries the basis."""
    missing = []
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        if (p.parent / "known_wrong.json").exists():
            continue          # sealed BY DERIVATION, not by name — the same carve-out as PR-3
        q = ((json.loads(p.read_text()).get("mechanical") or {}).get("quality") or {})
        fcf = q.get("free_cash_flow") or {}
        if fcf.get("status") != "present":
            continue
        if "Levered Free Cash Flow" not in (fcf.get("note") or ""):
            missing.append(p.parent.name)
    assert not missing, (
        f"these committed records state an FCF figure with no basis note: {missing} — re-run the "
        f"artifact pass, or the page ships a number whose definition it never gives")


# ─── the wiring, EXECUTED ─────────────────────────────────────────────────────────────────────
#
# MUTATION FINDING, and the pins above earned it: dropping `values=` from the row builder AND
# dropping `note=` from `free_cash_flow` both left this file GREEN. The artifact pins read the
# committed JSON — which the artifact pass had already fixed — and the note tests call
# `_fcf_basis_note` directly, so neither touched the code that wires them together. A pin that
# observes an artifact instead of executing the code is the rung this repo keeps hitting.

class _Bundle:
    """The one method `free_cash_flow` touches. Duck-typed so the wiring runs offline — the real
    workbooks are licensed and git-ignored, so a test that needed them could never run in CI."""

    def __init__(self, rows: list[list[Any]]) -> None:
        self._rows = rows

    def sheet(self, book: str, name: str, *, freq: str = "annual") -> list[list[Any]]:
        return self._rows


def test_free_cash_flow_attaches_the_basis_note_to_the_fact_it_returns() -> None:
    """THE WIRING, driven. `_fcf_basis_note` being correct is worth nothing if the fact ships
    without it — and that mutation passed this file until this test existed."""
    from vinci.dossier.ciq_sheets import free_cash_flow
    out = free_cash_flow(_Bundle(_rows(11_970.8, -818.8)))
    assert out.value == 999.0, out
    assert out.note and "Levered Free Cash Flow" in out.note, (
        "the fact shipped with no basis note — the figure's definition never reaches the record")
    assert "CFO" in out.note and "capex" in out.note


def test_the_row_builder_keeps_the_number_beside_the_display_string() -> None:
    """THE OTHER WIRING: `CFO`/`Capex`/`FCF` must carry structured values, not just rendered cells,
    or a consumer wanting CFO − capex is back to re-parsing "11,971" out of a string — the shape the
    house rule forbids, and the thousands-blind `$1,101.80M` re-parse is what it costs.

    REWRITTEN TO OBSERVE THE ROW, NOT THE SOURCE (2026-08-12, PR-C). The first version asserted the
    literal call `values=[*nums, None, None]`, and PR-C had to change that expression — the estimate
    columns are no longer a fixed pair, so the padding became `[None] * n_est`. The pin reddened for
    a reason with nothing to do with the behaviour it protects, which is the standing hazard of a
    test that reads code instead of running it. It now builds the real table and checks the rows
    themselves: a re-spelling cannot break it, and dropping the values genuinely does.
    """
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import financial_summary_annual
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files("NFLX")
    if not files:
        pytest.skip("licensed CIQ bundle for NFLX unavailable (never committed)")
    table = financial_summary_annual(CiqBundle.from_files("NFLX", files)).value
    assert table is not None
    by_label = {r.label: r for r in table.rows}
    for label in ("CFO ($M)", "Capex ($M)", "FCF ($M)"):
        row = by_label.get(label)
        assert row is not None, f"{label} is missing from the summary entirely"
        assert row.values, f"{label} carries no structured values — a consumer must re-parse cells"
        assert len(row.values) == len(table.columns), (
            f"{label} carries {len(row.values)} values against {len(table.columns)} columns")
        assert any(v is not None for v in row.values), f"{label}'s values are all None"


def test_the_two_legs_are_read_from_the_levered_column_not_each_rows_own_latest() -> None:
    """REVIEW FINDING (P1, #421), and the irony is the point: the note exists to make a basis claim
    auditable, and it was itself making an unaudited same-period claim.

    `_latest_col` picked the rightmost POPULATED cell **per row**. A newly added period is routinely
    filled for one row before the others — so Levered FCF lands in the new column while CFO still
    ends in the previous one, the subtraction spans two periods, and the sentence says "on the same
    sheet and period [LTM …]" about it. That is the same-window defect the buyback average was
    refused for.

    Here FCF has a value in column 2 that CFO and capex do not. Reading each row's own latest would
    silently pair column 2 against column 1; reading the LEVERED column says so instead."""
    staggered = [
        ["Fiscal Period", "FY25", "LTM"],
        ["Cash from Ops.", 100.0, ""],          # not yet filled for LTM
        ["Capital Expenditure", -10.0, ""],
        ["Levered Free Cash Flow", 80.0, 250.0],
    ]
    note = _fcf_basis_note(staggered, 250.0, "LTM", 2)
    assert "cannot be stated for [LTM]" in note, note
    assert "CFO and capex has no value in that column" in note, note
    assert "90.0" not in note, "it subtracted the PRIOR period's legs and called them this period's"
    # …and when the column IS populated for all three, the arithmetic runs
    full = [r[:] for r in staggered]
    full[1][2], full[2][2] = 300.0, -50.0
    ok = _fcf_basis_note(full, 250.0, "LTM", 2)
    assert "CFO $300.0M − capex $50.0M = $250.0M" in ok, ok
