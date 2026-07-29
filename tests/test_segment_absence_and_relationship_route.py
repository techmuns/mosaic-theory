"""BATCH B — item 19b (absence reasons) and item 21 (spreadsheet branch routing).

BOTH are EXTRACTION fixes, so code-closed and reader-closed are separate dates: these pins go
green the moment the code lands, but a committed dossier keeps its old note until that name is
re-assembled. The corpus tests below therefore assert against the WORKBOOKS (the object the
extractor reads), not against `data/dossiers/*.json` — pinning the artifact would red until the
fleet pass and would be pinning the wrong layer besides.

Licensed CIQ bundles are never committed, so every corpus test skips without them; the synthetic
tests carry the logic and always run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.ciq import CiqBundle
from vinci.dossier.ciq_sheets import (
    _absence_reason,
    _parse_business_relationships,
    _parse_relationship_sheet,
    customers,
    segment_ebitda,
)
from vinci.dossier.schemas import SourceStatus

ROOT = Path(__file__).resolve().parents[1]
CIQ = ROOT / "data" / "manual" / "ciq"

# the string item 19b exists to delete: a claim about the SHEET's shape standing in for a fact
# about the FILING. Pinned as a literal because it is OUR OWN text, not LLM-composed — the
# no-LLM-string-pin rule does not reach deterministic formatter output.
OLD_SHEET_SHAPE_NOTE = "as expected"


def _seg_rows(segments: list[tuple[str, float]]) -> list[list[Any]]:
    """A minimal Segments sheet carrying a Revenues roster and NO EBITDA section."""
    rows: list[list[Any]] = [["Fiscal Period", "FY 2025"]]
    rows.append(["Revenues", None])
    rows += [[name, val] for name, val in segments]
    rows.append(["Total Revenues", sum(v for _n, v in segments)])
    return rows


# --- item 19b: the absence reason names the filing fact, not the sheet's shape -----------------


def test_single_segment_absence_names_the_filing_fact() -> None:
    """THE POSITIVE PIN. Seven of eleven committed names report ONE segment, so there is no segment
    EBITDA to give and none is missing. The old note sent a reader looking for a better export."""
    rows = _seg_rows([("Eggs and Butter", 100.0)])
    note = _absence_reason(rows, "EBITDA", hdr=0)
    assert "single-segment reporting (Eggs and Butter)" in note
    assert OLD_SHEET_SHAPE_NOTE not in note, "the sheet-shape claim survived"


def test_multi_segment_absence_says_revenue_is_segmented_and_ebitda_is_not() -> None:
    """THE OTHER HALF of the population: three names ARE multi-segment and genuinely disclose no
    segment EBITDA. Their reason is a different fact and must read differently — collapsing both
    into one note would be the lumping this replaces."""
    rows = _seg_rows([("Products", 78.0), ("Preservation Services", 22.0)])
    note = _absence_reason(rows, "EBITDA", hdr=0)
    assert "reports 2 segments" in note
    assert "Products; Preservation Services" in note, note
    assert "single-segment" not in note


def test_segments_are_named_in_share_order_matching_the_rendered_field() -> None:
    """The note and the `segments` field describe the same roster, so they must order it the same
    way — a reader comparing them must not have to wonder whether they read different sheets."""
    rows = _seg_rows([("Small", 5.0), ("Big", 80.0), ("Middle", 15.0)])
    assert "Big; Middle; Small" in _absence_reason(rows, "EBITDA", hdr=0)


def test_an_unreadable_roster_admits_it_rather_than_guessing() -> None:
    """THE NEGATIVE PIN, and the one that matters most: with no roster to read there is no filing
    fact to assert, and the guard must NOT reach for the single-segment reason by default. A note
    that guesses is the fabricated-absence shape wearing item 19b's clothes."""
    note = _absence_reason([["Fiscal Period", "FY 2025"]], "EBITDA", hdr=0)
    assert "undetermined" in note
    assert "single-segment" not in note, "invented a filing fact from an unreadable sheet"


def test_a_missing_period_header_is_its_own_reason() -> None:
    """Three distinct causes were lumped into one note (`start`/`total`/`hdr` all None → same
    string). A header failure is a parse problem, not a disclosure fact — it must not be dressed
    as one. Follows the `net_lev` precedent: name the specific missing input."""
    note = _absence_reason(_seg_rows([("A", 1.0)]), "EBITDA", hdr=None)
    assert "no period header" in note
    assert "single-segment" not in note and "reports" not in note


def test_a_scoped_absence_does_not_describe_the_unscoped_roster() -> None:
    """REVIEW FINDING on this PR — item 19b's own defect, reintroduced inside the function written
    to remove it.

    ``geographic`` searches for 'Revenues' UNDER a 'Geographic Segment' label. When that subsection
    is missing, the first cut answered with the BUSINESS roster from the top of the sheet: "reports
    2 segments (Products; Preservation Services) but discloses no segment Revenues" — a stamp
    naming an object the caller never read, and self-contradictory besides ("revenue is segmented
    in the filing and Revenues is not").

    Latent on today's corpus (``geographic`` is PRESENT on all 11), which is exactly why it needs a
    pin rather than a re-measurement."""
    rows = _seg_rows([("Products", 78.0), ("Preservation Services", 22.0)])
    rows.append(["Geographic Segment", None])

    scoped = _absence_reason(rows, "Revenues", hdr=0, after_label="Geographic Segment")
    assert "Geographic Segment" in scoped
    assert "Products" not in scoped, f"the scoped note described the business roster: {scoped}"
    assert "reports 2 segments" not in scoped
    # the UNSCOPED call on the SAME sheet still answers with the roster — without this the fixture
    # would pass by making both branches say nothing, which pins the absence of a feature.
    assert "reports 2 segments" in _absence_reason(rows, "EBITDA", hdr=0)


def test_an_empty_row_in_the_roster_block_does_not_crash_the_build() -> None:
    """REVIEW FINDING on this PR. ``_segment_roster`` indexed ``rows[i][0]`` unguarded, so a blank
    row between 'Revenues' and 'Total Revenues' raised IndexError. The sibling loop in
    ``_segment_section`` has the same shape but runs on the SUCCESS path; this one runs on the
    FAILURE path, so the unguarded read turned a graceful UNKNOWN into a crash that kills the whole
    dossier build — strictly worse than the note it was trying to write."""
    rows: list[list[Any]] = [["Fiscal Period", "FY 2025"], ["Revenues", None],
                             ["A", 60.0], [], ["B", 40.0], ["Total Revenues", 100.0]]
    note = _absence_reason(rows, "EBITDA", hdr=0)      # must not raise
    assert "reports 2 segments" in note and "A; B" in note


@pytest.mark.skipif(not CIQ.is_dir(), reason="licensed CIQ bundles unavailable (never committed)")
def test_no_committed_bundle_still_asserts_sheet_shape() -> None:
    """THE CORPUS RED. Ten of eleven names carried the sheet-shape note; none may now."""
    seen = single = 0
    for d in sorted(CIQ.iterdir()):
        if not d.is_dir():
            continue
        s = segment_ebitda(CiqBundle.from_files(d.name, sorted(d.glob("*"))))
        if s.status is SourceStatus.PRESENT:
            continue
        seen += 1
        assert OLD_SHEET_SHAPE_NOTE not in (s.note or ""), f"{d.name}: {s.note}"
        single += "single-segment reporting" in (s.note or "")
    assert seen >= 5, f"expected the committed bundle corpus, saw {seen}"
    assert single >= 5, f"expected the single-segment majority to say so, saw {single}"


# --- item 21: spreadsheet exports route to read_sheets, and columns are found by header --------


_XLS_HEADER = ["Customer Name", "Exchange:Ticker Symbol", "Relationship Type",
               "Primary Industry", "Source", "Business Description"]


def test_the_sheet_route_does_not_read_the_ticker_as_the_relationship_type() -> None:
    """THE RED FOR THE ROUTE'S REAL TRAP. The .rtf parser reads cells[0], cells[1], cells[2] as
    name/type/industry; the .xls puts the TICKER in column 1, so reusing that parser produces a
    fluent, plausible, WRONG line. The fixture is built so positional and header-keyed reads give
    different answers — with the ticker column absent both would agree and this would pin nothing.
    """
    rows = [["Simply Good Foods"], ["Customers"], _XLS_HEADER,
            ["Amazon.com, Inc. (NasdaqGS:AMZN)", "NasdaqGS:AMZN", "Distributor",
             "Broadline Retail", "SMPL 2025 Form 10-K", "Amazon engages in…"]]
    out = _parse_relationship_sheet(rows)
    assert out is not None and len(out) == 1
    assert out[0] == ("Amazon.com, Inc. (NasdaqGS:AMZN) — Distributor · Broadline Retail "
                      "· src: SMPL 2025 Form 10-K"), out[0]
    assert "NasdaqGS:AMZN —" not in out[0], "the ticker was read as the relationship type"


def test_the_sheet_route_refuses_a_table_it_cannot_locate() -> None:
    """THE NEGATIVE PIN. No header row → None, so `customers` reports an honest parse failure.
    Returning [] would render as 'no customers disclosed', which is a different claim."""
    assert _parse_relationship_sheet([["Simply Good Foods"], ["Customize View"]]) is None
    assert _parse_relationship_sheet([]) is None


def test_the_footnote_row_is_not_parsed_as_a_counterparty() -> None:
    """The export's trailing '*denotes proprietary relationship' line sits in the name column."""
    rows = [_XLS_HEADER,
            ["Walmart Inc. (NasdaqGS:WMT)", "NasdaqGS:WMT", "Distributor", "Retail", "10-K", ""],
            ["*denotes proprietary relationship", "", "", "", "", ""]]
    out = _parse_relationship_sheet(rows)
    assert out is not None and len(out) == 1 and out[0].startswith("Walmart")


def test_the_rtf_route_is_untouched_by_the_split() -> None:
    """The .rtf parser serves ten of eleven names; the routing change must not perturb it."""
    raw = ("Customer Name|Relationship Type|Primary Industry|Source\n"
           "Amazon.com, Inc. (NasdaqGS:AMZN)|Distributor|Broadline Retail|BRBR 2025 Form 10-K\n")
    out = _parse_business_relationships(raw)
    assert out == ["Amazon.com, Inc. (NasdaqGS:AMZN) — Distributor · Broadline Retail "
                   "· src: BRBR 2025 Form 10-K"]


@pytest.mark.skipif(not CIQ.is_dir(), reason="licensed CIQ bundles unavailable (never committed)")
def test_no_bundle_renders_our_own_parse_error_as_its_customer_field() -> None:
    """THE CORPUS RED for item 21. `read_text` on a .xls raises 'format biff_xls is not text — use
    read_sheets()', and `customers` caught that and shipped it INTO the dossier as the field's
    UNKNOWN note. SMPL carried it live; WERN's export is the second instance."""
    seen = 0
    for d in sorted(CIQ.iterdir()):
        if not d.is_dir():
            continue
        s = customers(CiqBundle.from_files(d.name, sorted(d.glob("*"))))
        assert "use read_sheets()" not in (s.note or ""), f"{d.name}: {s.note}"
        assert "is not text" not in (s.note or ""), f"{d.name}: {s.note}"
        seen += 1
    assert seen >= 5, f"expected the committed bundle corpus, saw {seen}"


@pytest.mark.skipif(not CIQ.is_dir(), reason="licensed CIQ bundles unavailable (never committed)")
def test_the_customers_export_is_chosen_by_name_not_by_file_order() -> None:
    """The 'customers' workbook kind matches BOTH exports (its keywords include 'supplier'), and
    `workbook()` returns the first — so before this change the choice rested on 'Customers' sorting
    before 'Suppliers'. Harmless only while the .xls route failed loud; once routed, the same
    accident would have rendered SUPPLIER rows as customer concentration. Reversing the file order
    must change nothing."""
    checked = 0
    for d in sorted(CIQ.iterdir()):
        if not d.is_dir():
            continue
        paths = sorted(p for p in d.glob("*") if p.is_file())
        if not any("supplier" in p.name.lower() for p in paths):
            continue
        fwd = customers(CiqBundle.from_files(d.name, paths))
        rev = customers(CiqBundle.from_files(d.name, list(reversed(paths))))
        assert fwd.value == rev.value and fwd.source_ref == rev.source_ref, d.name
        # the source_ref's own PREFIX is the literal "CIQ Customers&Suppliers", so a substring
        # search for "supplier" matches every name regardless of which file was read. Assert on
        # the FILENAME the ref ends with — the only part that identifies the export.
        chosen = (fwd.source_ref or "").rsplit(" ", 1)[-1]
        assert "supplier" not in chosen.lower(), f"{d.name} read {chosen}"
        assert "customer" in chosen.lower(), f"{d.name} read {chosen}"
        checked += 1
    assert checked >= 5, f"expected names carrying both exports, saw {checked}"
