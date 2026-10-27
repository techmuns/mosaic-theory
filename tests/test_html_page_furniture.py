"""`html_to_text` drops PAGE FURNITURE — a page's number and running title at a page break — and
nothing else (2026-10-27, the #804 follow-up).

THE DEFECT. A filing printed for paper carries its page number, and often a running title, at
every CSS page break, and the flattened text kept them inside the clause they interrupt: EPAM's
credit agreement read "…Loans and/or Cash Collateralize Letters of Credit in an aggregate 76 amount
sufficient to reduce…". An extractor quoting the clause quotes it without the "76", so the span
check (`vinci.verbatim`) refused 11 of 49 covenant quotes at 545403de for furniture alone. Measured
2026-10-27 on that corpus, 9 of the 11 now pass and none newly fails; the 2 left are Artivion's list
bullets ("·"), which are the document's own text.

THE FIXTURES are real EDGAR HTML (tests/fixtures/page_furniture/), each cut to five pages around
one refused quote; the release excerpt is TJX's Q1 FY27 tables, whose pages end in figures. EDGAR
filings are public domain.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from vinci.graph.filings import _SENTINEL, _drop_page_furniture, html_to_text
from vinci.verbatim import SourceText

FIX = Path(__file__).parent / "fixtures" / "page_furniture"
CASES: dict[str, Any] = json.loads((FIX / "cases.json").read_text())


def _html(name: str) -> str:
    return (FIX / f"{name}.htm").read_text()


def _unmarked(html: str) -> str:
    """The text exactly as `html_to_text` produced it before page breaks were marked."""
    from bs4 import BeautifulSoup

    from vinci.graph.filings import normalize_text
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return normalize_text(soup.get_text(" ", strip=True))


@pytest.mark.parametrize("name", ["epam_credit_agreement", "tjx_credit_agreement",
                                  "v_credit_agreement"])
def test_a_quote_read_across_a_page_break_is_now_a_span(name: str) -> None:
    """The piece of each real refused quote that crosses a break: refused on the old text (the page
    number, or Visa's "33 364-Day Revolving Credit Agreement", sits inside it), a span now."""
    piece = CASES[name]["piece"]
    html = _html(name)
    assert not SourceText(_unmarked(html)).match(piece).found
    assert SourceText(html_to_text(html)).match(piece).found


def test_the_page_number_leaves_the_clause_it_interrupted() -> None:
    text = html_to_text(_html("epam_credit_agreement"))
    assert "in an aggregate amount sufficient to reduce" in text
    assert not re.search(r"\baggregate 76 amount\b", text)


def test_a_running_title_leaves_with_its_page_number() -> None:
    text = html_to_text(_html("v_credit_agreement"))
    assert "the Base Rate for such day plus (y)" in text
    assert "364-Day Revolving Credit Agreement for such day" not in text


def test_figures_that_end_a_page_stay_and_only_its_number_goes() -> None:
    """NEGATIVE: TJX's statements end pages 7–9 in figures ("…at end of period $ 5,580 $ 4,255 9").
    Every figure stays; the page number alone leaves. A first cut of this rule read every digit as
    alike and dropped "$ 5,580 $ 4,255" with it — a table row recurring 'digits aside'."""
    old, new = _unmarked(_html("tjx_q1_fy27_release")), html_to_text(_html("tjx_q1_fy27_release"))
    for row in ("Weighted average common shares – diluted 1,120 1,132",
                "Total liabilities and shareholders' equity $ 36,158 $ 31,858",
                "Cash and cash equivalents at end of period $ 5,580 $ 4,255"):
        assert row in old and row in new
    assert "$ 4,255 9 " in old and "$ 4,255 9 " not in new


#: Each fixture's furniture, word by word: its page numbers and the words of its running title.
_FURNITURE_WORDS = re.compile(r"[-–—]?\d{1,4}[-–—]?|[-–—]|364-Day|Revolving|Credit|Agreement|"
                              r"Werner|Enterprises,|Inc\.|Release|of|July|28,|Page")


def test_only_furniture_words_leave_and_the_rest_is_character_for_character() -> None:
    """Every fixture's new text is its old text with whole words deleted, and every deleted word is
    a page number or a word of a running title — nothing the filer wrote as content."""
    for name in CASES:
        old, new = _unmarked(_html(name)).split(), html_to_text(_html(name)).split()
        j, removed = 0, []
        for w in old:
            if j < len(new) and w == new[j]:
                j += 1
            else:
                removed.append(w)
        assert j == len(new), name                     # a pure deletion
        assert removed, name
        for w in removed:
            assert _FURNITURE_WORDS.fullmatch(w), (name, w)


def test_a_running_header_at_the_top_of_each_page_leaves_whole() -> None:
    """Werner heads every page "Werner Enterprises, Inc. - Release of July 28, 2026 Page N" — the
    title, its date and the page number leave together, and the text under it starts clean."""
    old, new = _unmarked(_html("wern_q2_2026_release")), html_to_text(_html("wern_q2_2026_release"))
    assert old.count("Release of July 28, 2026 Page") == 5
    assert "Release of July" not in new
    assert "lenders. 2026 Guidance Metrics and Assumptions" in new


def test_a_word_of_the_page_that_recurs_under_the_header_stays() -> None:
    """NEGATIVE, a mutation of Werner's real pages: put the same first word under every header (as
    Target heads its statements "…Page 5 of 11 TARGET CORPORATION…"). The run would recur with it,
    but a run ends on a number, so the word is the page's and stays."""
    html = re.sub(r"(<font>Page \d+</font></div></div><div><font>)", r"\1Consolidated ",
                  _html("wern_q2_2026_release"))
    assert html.count("Consolidated ") >= 4
    assert html_to_text(html).count("Consolidated ") == _unmarked(html).count("Consolidated ")
    assert "Release of July" not in html_to_text(html)


def test_a_number_that_does_not_page_is_not_a_page_number() -> None:
    """NEGATIVE, a mutation of EPAM's real pages: the same bare figure ending every page does not
    advance page to page, so it is the document's text and stays."""
    html = re.sub(r">(7[3-9])</font></div></div></div><hr", r">2025</font></div></div></div><hr",
                  _html("epam_credit_agreement"))
    assert html.count(">2025</font>") >= 3
    assert html_to_text(html) == _unmarked(html)


def test_fewer_than_three_breaks_keep_every_word() -> None:
    """NEGATIVE: nothing can recur across three pages, so a short document is left as it was."""
    text = "Revenue of $1.2 billion 12" + _SENTINEL + "Net income 13" + _SENTINEL + "End 14"
    assert _drop_page_furniture(text) == "Revenue of $1.2 billion 12 Net income 13 End 14"


def test_a_document_without_page_breaks_is_unchanged() -> None:
    html = "<html><body><p>Total revenue of $263.6 million</p><p>12</p><p>Outlook</p></body></html>"
    assert html_to_text(html) == _unmarked(html)
