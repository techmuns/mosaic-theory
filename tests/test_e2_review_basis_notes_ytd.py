"""#1027's independent pre-draw review (2026-11-13), FIX FIRST: four readers that answered where the
filing does not.

1. A period inside a header's "Based on …" clause is the outlook's BASIS, never the guided period:
   Verra Mobility's Q3 2025 header read its "fourth quarter" (basis) as three full-year guides' Q4.
2. "Checked, absent" means the NOTES were read: the notes' title matched as prose or as a contents
   entry, so a 10-Q cut to its cover and contents read CHECKED-ABSENT before any note, and Lilly's
   and McKesson's only match was an ASU 2024-03 sentence while their real headings were missed.
3. An item whose own sentence names no period, after a sentence comparing YEAR-TO-DATE figures, is
   that span's, never the release's quarter (Microvast's $11.1M write-down).
4. The release's OWN year in a Q1–Q3 release is that year to date, never its full year.

THE FIXTURES are real SEC text (tests/fixtures/e2_review/real_text_cuts.json): each document decoded
as production decodes it (`normalize_text(html_to_text(body))`) and cut to spans in filing order,
each span's offsets and the document's sha256 recorded. At generation each cut emitted, for every
item pinned here, exactly what its full document emits, at `32f4d6a4` and at the fix. EDGAR filings
are public domain. Item 4 has no case in the corpus; its pin is built on Gartner's real footnote
shape (`test_fix2_e2_remainder.py::test_re2_d17_a_bare_year_is_the_year`).
"""
from __future__ import annotations

import json
import pathlib

from vinci.dossier.mechanical import _fy_impairment
from vinci.edgar import filing_sections as fs
from vinci.edgar.release_parse import GUIDANCE_PERIOD_DEFAULT_PREFIX, parse_release

_CUTS = json.loads((pathlib.Path(__file__).parent / "fixtures" / "e2_review"
                    / "real_text_cuts.json").read_text(encoding="utf-8"))


def _text(name: str) -> str:
    return str(_CUTS[name]["text"])


def _state(name: str) -> str | None:
    gc = fs._going_concern(_text(name), str(_CUTS[name]["source_ref"]))
    return None if gc is None else ("doubt" if gc.substantial_doubt else "checked-absent")


# --- 1. a period inside "Based on …," is the basis ------------------------------------------------

def test_review_a_basis_clauses_quarter_is_never_the_guides_period_vrrm() -> None:
    """(+) THE RED, on `32f4d6a4`: "Based on our year-to-date 2025 results and our outlook for the
    fourth quarter, we are increasing revenue guidance as follows …" heads Verra Mobility's 2025
    FULL YEAR guidance (8-K 0001193125-25-256337). With "year-to-date 2025" skipped as basis, "the
    fourth quarter" — basis too — was the only period left, and three full-year guides read Q4 with
    their default flag removed: a fabricated period. The clause names no guided period, so they
    stay on the flagged default. Free cash flow, whose clause runs into the next list's "2025 Full
    Year" header, reads 2025 at both refs and is unchanged."""
    c = _CUTS["vrrm_q3_2025_release"]
    r = parse_release(_text("vrrm_q3_2025_release"), source_ref=str(c["source_ref"]))
    got = {g.metric: g.period for g in r.guidance}
    assert got == {"revenue": "next-fy", "adjusted ebitda": "next-fy", "adjusted eps": "next-fy",
                   "free cash flow": "2025"}, got
    flagged = [f for f in r.qa_flags if f.startswith(GUIDANCE_PERIOD_DEFAULT_PREFIX)]
    assert len(flagged) == 3, flagged


# --- 2. "checked, absent" means the notes were read ----------------------------------------------

def test_review_a_contents_entry_is_not_the_notes_tecx() -> None:
    """(+) THE RED, on `32f4d6a4`: TECX's 10-Q (0001193125-26-450019) cut to its cover and table of
    contents, 200 characters past the contents entry "Notes to Unaudited Condensed Consolidated
    Financial Statements 9 Item 2.", holds no note, and read CHECKED-ABSENT. It makes no claim."""
    assert _state("tecx_cover_and_contents") is None


def test_review_prose_naming_the_notes_is_not_their_heading_lly() -> None:
    """(+) THE RED, on `32f4d6a4`: Lilly's ASU 2024-03 sentence ("… in the notes to the financial
    statements") was the only match in its 10-Q (0000059478-26-000108), and alone it read
    CHECKED-ABSENT. A sentence that names the notes is not their heading."""
    assert _state("lly_asu_prose") is None


def test_review_financial_notes_is_mckessons_heading() -> None:
    """(+) THE RED, on `32f4d6a4`: McKesson's notes are headed "FINANCIAL NOTES (UNAUDITED) 1.
    Significant Accounting Policies" (10-Q 0000927653-26-000281). The fixed title missed it, so its
    contents entry and its real heading read no claim; its full 10-Q read CHECKED-ABSENT only off
    the ASU prose. The heading is read, and the contents entry beside it is not what reads it."""
    assert _state("mck_contents_and_heading") == "checked-absent"
    h = fs._notes_heading(_text("mck_contents_and_heading"))
    assert h is not None and h.group(0) == "FINANCIAL NOTES"


def test_review_lilly_is_read_from_its_real_heading() -> None:
    """(+) Lilly's cut holds its notes' heading, "Notes to Consolidated Condensed Financial
    Statements (Tables present dollars …) Note 1: Basis of Presentation …", and the ASU sentence
    after it. It is CHECKED-ABSENT at both refs; what is new (it fails on `32f4d6a4`, which has no
    heading reader) is that the HEADING reads it, the title in Lilly's word order, not the prose."""
    assert _state("lly_heading_and_asu_prose") == "checked-absent"
    h = fs._notes_heading(_text("lly_heading_and_asu_prose"))
    assert h is not None and h.start() == 0
    assert h.group(0) == "Notes to Consolidated Condensed Financial Statements"


def test_review_neg_fubos_going_concern_note_is_still_read() -> None:
    """(-) Green on both: FuboTV's "Note 3 - Liquidity, Going Concern and Management Plans", under
    its notes' heading (10-Q 0001628280-26-053535), states no substantial doubt: CHECKED-ABSENT."""
    assert _state("fubo_heading_and_going_concern_note") == "checked-absent"


# --- 3. a year-to-date paragraph's item is not the quarter's --------------------------------------

def test_review_a_year_to_date_paragraphs_item_is_never_the_quarters_mvst() -> None:
    """(+/-) Microvast's Q3 2026 release (8-K 0001628280-26-072310): "Gross margin decreased to
    24.4% from 36.6% in YTD 2025. This change was primarily attributable to an $11.1 million
    write-down …" is the nine months', and the frame filed it as Q3 2026 — RE2-D17's own failure
    shape (THE RED, on `32f4d6a4`). Now unread. Its quarter's paragraph, "… from 37.6% in Q3 2025.
    This change … a $9.3 million write-down …", stays the quarter's (green on both)."""
    c = _CUTS["mvst_q3_2026_writedowns"]
    r = parse_release(_text("mvst_q3_2026_writedowns"), source_ref=str(c["source_ref"]))
    got = {o.amount: o.period for o in r.one_offs}
    assert got == {9.3: "Q3 2026", 11.1: None}, got


# --- 4. the release's own year, mid-year, is not its full year ------------------------------------

def test_review_the_releases_own_year_mid_year_is_not_its_full_year() -> None:
    """(+) THE RED, on `32f4d6a4`; CONSTRUCTED on Gartner's real footnote (8-K 0000749251-26-000028,
    a fourth-quarter release: "$150 million of goodwill impairment related to Digital Markets in
    2025", which IS the year's), moved into a SECOND-quarter release of the same year. There "in
    2026" is the year to date, so the item is unread, and it is never the full-year impairment."""
    text = ("Gartner Reports Second Quarter 2026 Financial Results. (d) Includes "
            "$150 million of goodwill impairment related to Digital Markets in 2026 in addition to "
            "impairment loss for lease related assets, net of a reduction in lease liabilities.")
    r = parse_release(text, source_ref="8-K x EX-99.1")
    assert {o.amount: o.period for o in r.one_offs}.get(150.0, "missing") is None
    assert _fy_impairment([r]) is None


def test_review_neg_a_prior_full_year_mid_year_is_still_the_year() -> None:
    """(-) Green on both: in the same second-quarter release, "in 2025" is the PRIOR year, which is
    over — the year's."""
    text = ("Gartner Reports Second Quarter 2026 Financial Results. (d) Includes "
            "$150 million of goodwill impairment related to Digital Markets in 2025 in addition to "
            "impairment loss for lease related assets, net of a reduction in lease liabilities.")
    r = parse_release(text, source_ref="8-K x EX-99.1")
    assert {o.amount: o.period for o in r.one_offs}.get(150.0) == "2025"
