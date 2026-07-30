"""ITEM 33 — the .rtf Business-Relationships parser read columns BY POSITION.

THE MECHANISM, and the recorded one was WRONG. STATE described it as "drops empty cells then reads
positionally". Measuring the real exports shows the cause is a VARIABLE HEADER — the export ships
two layouts:

    4-col: Customer Name | Relationship Type | Primary Industry | Source
    5-col: Customer Name | Supplier Name | Relationship Type | Primary Industry | Source

``cells[1]`` is the relationship type in the first and the SUPPLIER NAME in the second. So the
positional read was correct for exactly half the fleet and silently wrong for the other half:
Artivion rendered as ``Artivion, Inc. (NYSE:AORT) — Endospan Ltd. · Distributor`` — the focal
company named as its own counterparty, the counterparty as the relationship, the relationship as
the industry.

MEASURED, not inferred: the 5-column names are AORT, CNXC, EPAM, FUBO and IT — EXACTLY the five
that rendered a company name in the relationship slot. 40 rows across them; 0 after.

Same class as the `[-1]` rule and item 21's `.xls` route: an unasserted assumption about layout.
The fix is the same one — map columns by HEADER TEXT.
"""
from __future__ import annotations

import re

import pytest

from vinci.dossier.ciq_sheets import _parse_business_relationships

# A COMPANY NAME where a relationship type belongs — the defect itself, detected by company
# markers rather than by a whitelist of types. The whitelist version of this check produced six
# FALSE positives (`Borrower`, `Client Services` are real CIQ types); the corpus is the authority
# on the vocabulary, so the detector must not encode a guess about it.
_COMPANY = re.compile(
    r"\(|\b(Inc|Ltd|LLC|S\.A|A\.S|GmbH|plc|Corp|Corporation|Limited|Company|Group|SAS|B\.V)\b")

FOUR_COL = (
    "Customer Name|Relationship Type|Primary Industry|Source|\n"
    "Amazon.com, Inc. (NasdaqGS:AMZN)|Distributor|Broadline Retail|BRBR 2025 Form 10-K|\n"
    "Business Description: Amazon.com, Inc. engages in retail…|\n"
)
FIVE_COL = (
    "Customer Name|Supplier Name|Relationship Type|Primary Industry|Source|\n"
    "Artivion, Inc. (NYSE:AORT)|Endospan Ltd.|Distributor|Health Care Equipment|AORT 2026 10-K|\n"
    "Business Description: Artivion, Inc. manufactures medical devices…|\n"
)


def _rel(line: str) -> str:
    m = re.match(r"^(.*?) — ([^·]+?)(?: ·|$)", line)
    assert m, f"unparseable rendered line: {line!r}"
    return m.group(2).strip()


def test_the_five_column_layout_does_not_put_a_company_in_the_relationship_slot() -> None:
    """THE RED. Positionally, ``cells[1]`` on this layout is 'Endospan Ltd.' — and that is exactly
    what shipped on five names."""
    out = _parse_business_relationships(FIVE_COL)
    assert out is not None and len(out) == 1
    assert _rel(out[0]) == "Distributor", out[0]
    assert not _COMPANY.search(_rel(out[0])), (
        f"a company name is in the relationship slot: {out[0]}")


def test_the_four_column_layout_is_unchanged() -> None:
    """THE CONTROL. Five names were already correct and a header-keyed read must not disturb them —
    a fix that repairs half a fleet and breaks the other half is not a fix."""
    out = _parse_business_relationships(FOUR_COL)
    assert out == ["Amazon.com, Inc. (NasdaqGS:AMZN) — Distributor · Broadline Retail "
                   "· src: BRBR 2025 Form 10-K"]


def test_both_parties_are_rendered_when_both_are_named() -> None:
    """The 5-column view names BOTH sides, and which one is the focal company varies row to row
    (Artivion is the customer in one row and the supplier in the next). Rendering the pair as
    stated preserves that; inferring 'the counterparty' would be a new conclusion the export does
    not make, and the direction is what ``Relationship Type`` already says."""
    out = _parse_business_relationships(FIVE_COL)
    assert out is not None
    assert "Artivion, Inc. (NYSE:AORT) ← Endospan Ltd." in out[0]


def test_a_blank_cell_is_a_position_not_nothing() -> None:
    """The previous parser filtered empty cells before indexing, so a blank column shifted every
    later field left. Keeping the split unfiltered is what makes header indices mean anything."""
    txt = ("Customer Name|Supplier Name|Relationship Type|Primary Industry|Source|\n"
           "Acme Corp|  |Customer|Software|Acme 10-K|\n")
    out = _parse_business_relationships(txt)
    assert out is not None and _rel(out[0]) == "Customer", out[0]
    assert "Acme Corp — Customer · Software" in out[0]


def test_an_unknown_header_order_still_maps_correctly() -> None:
    """Header-keyed, not header-shaped: columns are located by NAME, so a reordered export (or one
    that gains a column) keeps working rather than shifting silently — the point of not reading by
    position."""
    txt = ("Source|Primary Industry|Relationship Type|Customer Name|\n"
           "ACME 10-K|Software|Customer|Acme Corp|\n")
    out = _parse_business_relationships(txt)
    assert out is not None and _rel(out[0]) == "Customer", out[0]


def test_a_table_without_the_required_columns_is_refused() -> None:
    """The negative pin. No 'Relationship Type' column → None, so ``customers`` reports an honest
    parse failure rather than rendering rows whose relationship is unknown."""
    assert _parse_business_relationships("Foo|Bar|\nA|B|\n") is None
    assert _parse_business_relationships("") is None


# --- the corpus gate ----------------------------------------------------------------------------


@pytest.mark.skipif(
    not (__import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "manual"
         / "ciq").is_dir(),
    reason="licensed CIQ bundles unavailable (never committed)")
def test_no_committed_name_renders_a_company_in_the_relationship_slot() -> None:
    """THE CORPUS RED, per-name as specified. 40 rows across AORT, CNXC, EPAM, FUBO and IT carried
    a company name where the relationship belongs; none may now, and the five already-clean names
    must stay clean."""
    import pathlib
    import warnings

    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import customers

    warnings.filterwarnings("ignore")
    root = pathlib.Path(__file__).resolve().parents[1] / "data" / "manual" / "ciq"
    offenders, seen = {}, 0
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        b = CiqBundle.from_files(d.name, sorted(p for p in d.glob("*") if p.is_file()))
        val = customers(b).value or ""
        if not val:
            continue
        seen += 1
        # `customers` caps the rendered list at 30 and appends "…(+N more)" — a marker, not a row
        entries = [e for e in val.split("; ") if " — " in e]
        n = sum(1 for e in entries if _COMPANY.search(_rel(e)))
        if n:
            offenders[d.name] = n
    assert seen >= 5, f"expected the committed bundle corpus, saw {seen}"
    assert not offenders, f"a company name sits in the relationship slot: {offenders}"
