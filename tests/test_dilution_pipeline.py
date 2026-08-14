"""FORWARD dilution capacity — the registered-offering pipeline from the EDGAR filing index.

THE GAP THIS CLOSES (audit 2026-08-13, the BioCatch/M&A seam applied forward). The stack measured
REALIZED dilution (share-count trend) and buybacks, but nothing watched the PIPELINE — an effective
shelf, prospectus supplements drawing on it, a fresh S-1. For a drawdown name, issuance into the
drawdown is the recovery-killer, and it is announced in exactly the filings nothing fetched:
S-3/F-3 shelfs, 424B supplements, S-1/F-1, S-8. Verified zero references anywhere before this.

MEASURED ON THE LIVE FLEET before these tests were written (window-bounded at 2026-08-12):
FUBO — 2 shelfs + 3 supplements (424B5/424B7, the equity machinery) + 3 S-8; MVST — S-3 + 424B5;
VRRM — nothing on file at all; BRBR/NCNO/SMPL/VITL — S-8 only. And the case that sets the LABEL:
**V's six supplements are 424B2/424B3 BOND takedowns** — the index cannot distinguish an ATM draw
from a debt deal, so the rendered label says "equity/debt not distinguished" rather than asserting
dilution for what may be bonds.

ASSEMBLE-AND-CITE ONLY: counts, forms and dates. Which pipeline is a risk is the human's call.
"""
from __future__ import annotations

from datetime import date

from vinci.dossier.mechanical import (
    _DILUTION_SCAN_DAYS,
    _dilution_line,
    _dilution_pipeline,
)
from vinci.edgar.client import Filing


def _f(form: str, d: str, acc: str = "0000000000-26-000001") -> Filing:
    """A REAL `Filing` (the type the submissions feed yields) — never a hand-rolled dict."""
    return Filing(cik="0000000000", form=form, filing_date=date.fromisoformat(d),
                  accession=acc, items=[], primary_doc=None)


REF = date(2026, 8, 12)


def test_the_fubo_shape_counts_by_group_and_keeps_s8_out_of_the_headline() -> None:
    """THE POSITIVE PIN, on the live FUBO shape: shelfs and supplements headline; S-8 is REAL
    dilution but routine, so it is counted on its own tail and never mixed into the headline —
    a reader scanning for the ATM machinery must not have to subtract employee plans first."""
    filings = [
        _f("S-3ASR", "2026-01-23"), _f("S-3ASR", "2024-02-01"),
        _f("424B5", "2026-01-23"), _f("424B7", "2025-06-11"), _f("424B5", "2024-03-09"),
        _f("S-8", "2026-08-05"), _f("S-8", "2025-08-01"), _f("S-8", "2024-08-02"),
    ]
    inwin, line = _dilution_line(filings, REF)
    assert len(inwin) == 8
    assert "shelf registrations 2 (S-3ASR, last 2026-01-23)" in line
    assert "prospectus supplements 3 (424B5/424B7, last 2026-01-23)" in line
    assert "employee-plan (S-8) 3" in line and "routine" in line
    head = line.split("employee-plan")[0]
    assert "S-8" not in head, "S-8 leaked into the headline groups"
    assert "3y window to 2026-08-12" in line, "the window must be stated on the face of the value"


def test_a_filing_after_the_as_of_never_enters_the_counts() -> None:
    """THE AS-OF BOUND, pinned as its own case — the post-as-of leak class item 9 measured (NFLX
    58 / UBER 91 dates past their own reference_date). `recent_filings` has only a lower bound, so
    the upper bound lives in `_dilution_line` and this is the pin that keeps it there."""
    filings = [_f("S-3ASR", "2026-01-23"), _f("424B5", "2026-08-13")]  # one day past the as-of
    inwin, line = _dilution_line(filings, REF)
    assert [f.form for f in inwin] == ["S-3ASR"], "a post-as-of filing entered the window"
    assert "prospectus supplements" not in line, (
        "a 424B5 filed AFTER the record's as-of is being counted — lookahead past the record")


def test_nothing_on_file_is_a_stated_finding_not_silence() -> None:
    """THE VRRM SHAPE. An empty register is decision-relevant (no standing capacity) and must
    print as a stated fact naming its window — never as a blank, and never as UNKNOWN."""
    inwin, line = _dilution_line([], REF)
    assert inwin == []
    assert line == ("no registration statements or prospectus supplements on file in the "
                    "3y to 2026-08-12")


def test_s8_only_names_state_the_absence_of_the_headline_groups() -> None:
    """THE BRBR/NCNO SHAPE — routine employee plans and nothing else. The headline must say the
    shelf/supplement/fresh groups are empty rather than letting the S-8 count read as pipeline."""
    _, line = _dilution_line([_f("S-8", "2026-03-31")], REF)
    assert line.startswith("no shelf/supplement/fresh registration"), line
    assert "employee-plan (S-8) 1" in line and "routine" in line


def test_a_failed_read_is_unknown_and_never_renders_like_none_on_file() -> None:
    """TWO STATES THAT MUST NOT RENDER ALIKE: "the register is empty" (a finding, PRESENT) vs
    "the register could not be read" (no CIK / fetch failure, UNKNOWN).

    BOTH STATES GO THROUGH THE WRAPPER, deliberately. The first cut asserted the empty state on
    the pure composer only, and a mutation that made the WRAPPER return UNKNOWN for an empty
    register passed green — the pure half stayed honest while the shipped object lied. The stub
    drives the same path production takes (pin the artifact, not the helper)."""
    dp = _dilution_pipeline(None, None, REF)  # type: ignore[arg-type]  # edgar unused on this path
    assert dp.line.value is None and dp.filings == []
    assert "no CIK" in (dp.line.note or "")

    class _EmptyIndex:
        """An EdgarClient whose submissions feed has no matching filings — the VRRM shape."""

        def recent_filings(self, cik, *, forms, since):  # noqa: ANN001, ANN201
            return []

    empty = _dilution_pipeline(_EmptyIndex(), "0000000000", REF)  # type: ignore[arg-type]
    assert empty.line.value is not None, (
        "an EMPTY register came back UNKNOWN — the finding and the failed read collapsed into "
        "one state, and a reader cannot tell 'no capacity on file' from 'could not check'")
    assert "no registration statements" in empty.line.value
    assert (dp.line.note or "") != empty.line.value


def test_committed_dossiers_round_trip_with_the_field_absent() -> None:
    """BACK-COMPAT: every committed dossier predates the field; it must parse (defaulting None)
    and render byte-identically — the pages change on their next assembly, not on this merge."""
    import pathlib

    import pytest

    from vinci.dossier.render import _dilution_pipeline_lines
    from vinci.dossier.schemas import Dossier

    committed = sorted(pathlib.Path("data/dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this checkout")
    d = Dossier.model_validate_json(committed[0].read_text())
    assert d.mechanical.dilution_pipeline is None, (
        "a committed dossier parsed with a NON-None pipeline — the default is wrong and old "
        "records are inventing a block they never carried")
    assert _dilution_pipeline_lines(d.mechanical) == [], (
        "a None field rendered lines — committed pages would change on merge, not on assembly")
    # and the md really does not carry the label yet
    md = committed[0].with_name("dossier.md").read_text()
    assert "Registered offering pipeline" not in md


def test_the_rendered_line_carries_the_equity_debt_disclaimer() -> None:
    """THE LABEL IS THE LIMITATION. V's six supplements are BOND takedowns (424B2/424B3) and the
    index cannot tell them from an ATM draw — a label reading "dilution" would assert equity
    issuance the source cannot support. The disclaimer lives in the LABEL so it prints on every
    name, not in a note that curates away."""
    from vinci.dossier.render import _dilution_pipeline_lines
    from vinci.dossier.schemas import DilutionPipeline, RegistrationFiling, Sourced

    dp = DilutionPipeline(
        filings=[RegistrationFiling(form="424B2", filing_date="2026-04-13",
                                    accession="0001403161-26-000001")],
        window_days=_DILUTION_SCAN_DAYS,
        line=Sourced.present("prospectus supplements 1 (424B2, last 2026-04-13)",
                             source_ref="EDGAR filing index"))
    lines = _dilution_pipeline_lines(_MechStub(dp))  # type: ignore[arg-type]
    assert len(lines) == 1
    assert "equity/debt not distinguished" in lines[0], (
        "the disclaimer left the label — a 424B2 bond deal now reads as dilution")


class _MechStub:
    """Duck-typed mechanical layer for the render helper — only the field it reads."""

    def __init__(self, dp) -> None:  # noqa: ANN001
        self.dilution_pipeline = dp
