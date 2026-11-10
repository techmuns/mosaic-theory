"""A full-text-search hit on an 8-K/A is reported as an 8-K/A (TeamNostra fix request 2, RE1-D11).

efts states three forms for a hit: ``form``, the filing's own ("8-K/A"); ``root_forms``, its family
("8-K"); and ``file_type``, the document the phrase matched ("EX-99.3"). `parse_fts_hit` read the
family first, so every amendment came back "8-K", and the covenant pointer wrote the literal "8-K"
whatever the hit said.

On the 28 pages frozen at `bcda7ce3`, 92 covenant-pointer rows read "8-K", and their accessions
were looked up in the submissions documents read on 2026-11-09/10: one is an 8-K/A. It is WERN's
credit agreement of 2026-04-14, `0000793074-26-000090`. Its real efts hit is below, as this
machine's efts cache holds it (a search for "Operating Lease Liabilities", forms=8-K).
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vinci.dossier.schemas import CapitalInstrument, CovenantPointer, Sourced
from vinci.edgar.client import EdgarClient, Filing, FtsHit, FtsResult, parse_fts_hit

#: WERN's real efts hit for its 8-K/A of 2026-04-14 (the fields `parse_fts_hit` reads).
_WERN_8KA: dict[str, Any] = {
    "_id": "0000793074-26-000090:wern-20260127ex993.htm",
    "_source": {
        "ciks": ["0000793074"], "root_forms": ["8-K"], "form": "8-K/A", "file_type": "EX-99.3",
        "file_date": "2026-04-14", "adsh": "0000793074-26-000090",
        "display_names": ["WERNER ENTERPRISES INC  (WERN)  (CIK 0000793074)"],
    },
}
_WERN = "0000793074"


def test_an_amendments_hit_is_reported_as_an_amendment() -> None:
    """⊖ the real hit: its family is 8-K, its form 8-K/A, its document an EX-99.3."""
    hit = parse_fts_hit(_WERN_8KA)
    assert hit.form == "8-K/A"
    assert hit.accession == "0000793074-26-000090" and hit.file_date == date(2026, 4, 14)


def test_a_hit_stating_no_form_falls_back_to_its_family_never_its_document() -> None:
    """⊕ efts states no `form`: the family names it, as before — never the matched exhibit."""
    src = {k: v for k, v in _WERN_8KA["_source"].items() if k != "form"}
    assert parse_fts_hit({"_id": _WERN_8KA["_id"], "_source": src}).form == "8-K"


def test_an_exhibit_document_type_is_never_read_as_the_form() -> None:
    """⊖ efts states neither `form` nor `root_forms`: the matched exhibit's type ("EX-99.3") is no
    form, so the form is unknown — never "EX-99.3" written into a pointer row."""
    src = {k: v for k, v in _WERN_8KA["_source"].items() if k not in ("form", "root_forms")}
    assert parse_fts_hit({"_id": _WERN_8KA["_id"], "_source": src}).form is None
    main = {**src, "file_type": "8-K/A"}  # the main document matched: its type IS the form
    assert parse_fts_hit({"_id": _WERN_8KA["_id"], "_source": main}).form == "8-K/A"


def _pointer_rows(monkeypatch: pytest.MonkeyPatch, hits: list[FtsHit]) -> list[CovenantPointer]:
    """WERN's real revolver line through `_covenant_pointers`, efts answering ``hits``."""
    import vinci.dossier.mechanical as mech

    class _Edgar:
        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ()) -> list[Any]:
            return []

        def fulltext_search(self, phrase: str, *, forms: str = "", ciks: str = "") -> FtsResult:
            return FtsResult(hits=hits, total=len(hits))

    inst = CapitalInstrument.model_validate({
        "description": "22 Unsecured Credit Agreement - Revolving Credit Facility",
        "type": "Revolving Credit", "principal_musd": None, "coupon": "NA",
        "floating_rate": "SOFR", "maturity_date": "2031-01-27", "seniority": "Senior",
        "secured": False, "convertible": False, "currency": "USD"})
    monkeypatch.setattr(mech, "_exhibit_names", lambda http, cik, acc: ["wern-20260127ex101.htm"])
    out = mech._covenant_pointers(cast(EdgarClient, _Edgar()), cast(Any, None), _WERN,  # noqa: SLF001
                                  [inst], date(2026, 9, 16))
    return [r for r in (out.value or []) if r.accession]


def test_the_covenant_pointer_names_an_amendment_as_filed(monkeypatch: pytest.MonkeyPatch) -> None:
    """⊖ end to end: WERN's pointer row read "8-K" for its 8-K/A."""
    rows = _pointer_rows(monkeypatch, [parse_fts_hit(_WERN_8KA)])
    assert [(r.filing, r.accession) for r in rows] == [("8-K/A", "0000793074-26-000090")]


def test_an_original_8k_pointer_still_reads_8k(monkeypatch: pytest.MonkeyPatch) -> None:
    """⊕ the negative pin: an 8-K's hit is still an 8-K."""
    src = {**_WERN_8KA["_source"], "form": "8-K", "adsh": "0000793074-26-000120"}
    hit = parse_fts_hit({"_id": "0000793074-26-000120:x.htm", "_source": src})
    rows = _pointer_rows(monkeypatch, [hit])
    assert [r.filing for r in rows] == ["8-K"]


@pytest.mark.parametrize("label", ["8-K/A", "8-K", "8-K12B"])
def test_a_linked_amendment_is_still_read_for_its_maturities(label: str) -> None:
    """⊖ the maturity check reads the 8-Ks the covenant pointers link (`_maturity_sources`), and
    it took a link only from a row reading "8-K". Named "8-K/A", WERN's credit agreement would
    have dropped out of the filings its maturity check reads. The link is the ACCESSION, whatever
    the row's label: a form efts states that is neither 8-K nor 8-K/A does not drop it either."""
    import vinci.dossier.mechanical as mech

    amendment = Filing(cik=_WERN, form="8-K/A", filing_date=date(2026, 4, 14),
                       accession="0000793074-26-000090", items=["9.01"],
                       primary_doc="wern-20260127x8ka.htm")

    class _Edgar:
        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",)) -> list[Filing]:
            return [amendment] if "8-K/A" in forms else []

    http = SimpleNamespace(get_text=lambda url, ttl_seconds=None: "<html><body></body></html>")
    rows = Sourced.present([CovenantPointer(family="22 Unsecured Credit Agreement",
                                            filing=label, filing_date="2026-04-14",
                                            accession="0000793074-26-000090", exhibits=[])],
                           source_ref="test")
    sources = mech._maturity_sources(cast(EdgarClient, _Edgar()), cast(Any, http), _WERN,  # noqa: SLF001
                                     rows, None, date(2026, 9, 16))
    assert [s.accession for s in sources] == ["0000793074-26-000090"]
