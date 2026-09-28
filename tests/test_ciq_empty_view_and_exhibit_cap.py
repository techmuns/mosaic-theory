"""An empty CIQ view is a FACT, and an oversized covenant exhibit is not oversized.

Two constants were wrong for the same reason: each encoded an assumption nobody had measured.

1. `read_text` refused any >4KB RTF yielding under 50 words, blaming "an OLE-disguised Word doc".
   BURL's customers view is real RTF, parses perfectly, and says "There are no recently disclosed
   customers listed". The page reported customer concentration UNKNOWN on a true empty, blaming a
   disguised Word doc it had never checked for. Swept 2026-09-28 over the 26 ticker folders under
   data/manual/ciq/: BURL is the ONLY empty view — 25 parse rows, ROST and TGT among them — so
   this is one name's economics (0 customer rows beside 33 supplier rows), not a sector rule.

2. `_MAX_EXHIBIT_CHARS` was 600_000 "≈ 150K tokens, fits model's window". The configured model's
   window is 1M TOKENS. BURL refused four exhibits at 645K–745K chars; sent in full, the largest
   returned six of seven terms verbatim.
"""

from __future__ import annotations

import pathlib

import pytest

from vinci.dossier.ciq import CiqBundle, CiqParseError, read_text
from vinci.dossier.ciq_sheets import customers
from vinci.dossier.covenant_extract import _MAX_EXHIBIT_CHARS
from vinci.dossier.schemas import SourceStatus

#: The shape CIQ emits for a company with no disclosed counterparties — the real BURL export's text,
#: wrapped in the RTF header it actually carries. Padded past the 4KB gate the guard keys on.
_EMPTY_VIEW = (
    r"{\rtf1\ansi\deff0 " + r"{\*\padding " + "x" * 5000 + "}" + r"\par "
    r"Customize View\par Include Customers for:Current subsidiaries\par "
    r"Customers\par Recently Disclosed Customers\par "
    r"There are no recently disclosed customers listed\par "
    r"Prior and Not Recently Disclosed Customers\par "
    r"There are no additional customers listed\par "
    r"*denotes proprietary relationship\par }"
)
#: The failure the guard was actually written for: a multi-KB file that yields fragments, no
#: sentence, no sentinel.
_OLE_DISGUISE = r"{\rtf1\ansi " + ("}{" * 3000) + r" \par 12 \par - \par }"


def _write(tmp: pathlib.Path, name: str, body: str) -> pathlib.Path:
    p = tmp / name
    p.write_text(body, encoding="utf-8")
    assert p.stat().st_size > 4096, "fixture must clear the guard's size gate to test anything"
    return p


def test_an_empty_ciq_view_is_returned_not_refused(tmp_path: pathlib.Path) -> None:
    """⊕ A thin RTF carrying CIQ's own 'nothing to list' sentence parses.

    The consumer then records "none disclosed", which is a fact a reader wants — rather than
    UNKNOWN, which says the engine could not tell."""
    text = read_text(_write(tmp_path, "BURL Customers.rtf", _EMPTY_VIEW))
    assert "no recently disclosed customers listed" in text.lower()
    assert len(text.split()) < 50, "the point of the case is that it IS thin"


def test_a_thin_file_without_the_sentinel_still_raises(tmp_path: pathlib.Path) -> None:
    """⊖ THE GUARD IS NOT WEAKENED. An OLE-disguised doc yields fragments and no sentence, so it
    still fails loud — a silent empty there would be a parse failure read as 'no customers'."""
    with pytest.raises(CiqParseError, match="OLE-disguised"):
        read_text(_write(tmp_path, "Broken Customers.rtf", _OLE_DISGUISE))


def test_the_sentinel_does_not_fire_on_an_ordinary_sentence(tmp_path: pathlib.Path) -> None:
    """⊖ It matches CIQ's construction, not the word 'no'. A thin file whose few words merely
    contain 'no' must still raise."""
    body = r"{\rtf1\ansi " + ("}{" * 3000) + r" \par There is no reason to keep this file \par }"
    with pytest.raises(CiqParseError):
        read_text(_write(tmp_path, "Noise Customers.rtf", body))


def test_the_exhibit_cap_clears_the_largest_real_agreement() -> None:
    """⊕ Pinned on the MEASURED corpus, not on a round number. BURL's four refused exhibits ran
    645,693 / 648,641 / 662,704 / 744,759 chars; the cap must clear the largest with real margin,
    while staying far inside the model's 1M-token window (1.2M chars ≈ 300–340K tokens)."""
    largest_real_exhibit = 744_759
    assert largest_real_exhibit * 1.25 <= _MAX_EXHIBIT_CHARS, (
        "the cap no longer clears the largest agreement actually observed, so a real capital "
        "structure would go back to reading UNKNOWN")
    assert _MAX_EXHIBIT_CHARS <= 2_000_000, (
        "beyond ~2M chars the prompt approaches the model's window and the refusal stops being a "
        "conservative bound — raise this only with a measurement, as the constant's comment did")


# --- the layer the human actually reads -------------------------------------------------------
# read_text returning the text is necessary but NOT sufficient: the table parser then finds no
# rows, and the note the reader sees is written HERE. Pinning only the reader would have gone
# green while the page still said "could not parse" — the wrong layer for the observed symptom.


def test_an_empty_view_reports_ciqs_answer_not_a_parse_failure(tmp_path: pathlib.Path) -> None:
    """⊕ END-TO-END through the sheet function: an empty customers view must say CIQ disclosed
    none, bound to the file, carrying NO value — never blame this code for the source's answer."""
    path = _write(tmp_path, "Acme Inc NYSE ACME Customers.rtf", _EMPTY_VIEW)
    bundle = CiqBundle.from_files("ACME", [path])
    assert bundle.all_workbooks("customers"), "fixture must route as a customers export"

    got = customers(bundle)
    assert got.status is SourceStatus.UNKNOWN, "no rows ⇒ no value; UNKNOWN is the honest status"
    assert got.value is None, "an empty table must never acquire a value"
    note = (got.note or "").lower()
    assert "discloses no customers" in note, f"must state CIQ's own answer, got: {got.note}"
    assert "could not parse" not in note, "must not blame our reader for the source's answer"
    assert "ole-disguised" not in note, "must not blame a disguise it never checked for"
    # source-bind-everything: the note makes a CLAIM, so it points at the file behind it.
    assert "Customers.rtf" in (got.source_ref or ""), (
        f"an asserted absence must be checkable, got source_ref={got.source_ref!r}")


def test_a_view_that_fails_to_parse_still_says_so(tmp_path: pathlib.Path) -> None:
    """⊖ THE HONEST NOTE IS NOT A BLANKET ONE. A customers export with real content that the table
    parser cannot read must still report a parse failure — if this path also claimed "CIQ discloses
    none", a broken parser would render as a clean economic fact, which is the worse failure."""
    body = (r"{\rtf1\ansi\deff0 " + r"{\*\padding " + "x" * 5000 + "}" + r"\par "
            + r"\par ".join("word " * 12 for _ in range(30)) + r"}")
    path = _write(tmp_path, "Acme Inc NYSE ACME Customers.rtf", body)
    got = customers(CiqBundle.from_files("ACME", [path]))
    assert got.status is SourceStatus.UNKNOWN
    assert "could not parse" in (got.note or "").lower(), (
        f"a genuine parse failure must not be reported as an empty view, got: {got.note}")


@pytest.mark.skipif(
    not (pathlib.Path(__file__).resolve().parents[1] / "data/manual/ciq/BURL").is_dir(),
    reason="licensed CIQ bundles are never committed",
)
def test_the_real_burl_export_is_read_as_empty_not_broken() -> None:
    """⊕ CORPUS BEFORE SYNTHETIC — the fixture above is built to the shape; this is the file that
    caused the incident. Its sibling Suppliers export parses 33 rows from the same bundle, which
    is what makes the empty customers view a fact about BURL rather than about the reader."""
    root = pathlib.Path(__file__).resolve().parents[1] / "data/manual/ciq/BURL"
    got = customers(CiqBundle.from_files("BURL", sorted(p for p in root.glob("*") if p.is_file())))
    assert got.status is SourceStatus.UNKNOWN and got.value is None
    assert "discloses no customers" in (got.note or "").lower(), got.note
    assert "customers" in (got.source_ref or "").lower().rsplit(" ", 1)[-1]
