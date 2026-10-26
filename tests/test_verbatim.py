"""The verbatim-span check (`vinci.verbatim`) — pinned on REAL committed quotes, end to end.

Every case in ``fixtures/verbatim/real_cases.json`` is a quote the committed corpus carried at
545403de (a covenant term, a maturity event or a graph edge), with a verbatim window of the EDGAR
document it was read from. The positives are the reductions the check makes, each on the real text
that needed it; the negatives are the refusal classes the corpus run found (2026-10-26), each on a
real refused quote. The end-to-end pins drive those same texts through the three extractors, so a
call site that stops consulting the check reddens here — not only the helper.
"""

from __future__ import annotations

import json
import pathlib
import typing

import pytest

from vinci.dossier import covenant_extract as ce
from vinci.dossier import schemas as ds
from vinci.graph import coverage as gcov
from vinci.graph import extract as gx
from vinci.graph.llm import LlmClient
from vinci.resolver import UnknownSymbolError
from vinci.schemas.data_record import Identity
from vinci.verbatim import SourceText, SpanMatch, comparison_key

_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "verbatim" / "real_cases.json"
_CASES: list[dict[str, typing.Any]] = json.loads(_FIXTURE.read_text())["cases"]


def _case(case_id: str) -> dict[str, typing.Any]:
    return next(c for c in _CASES if c["id"] == case_id)


# --- the check, on the real cases ----------------------------------------------------------------


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_real_case_gets_its_measured_answer(case: dict[str, typing.Any]) -> None:
    """(+/-) Each real quote against its real window: the answer measured on the whole document."""
    assert SourceText(case["window"]).match(case["quote"]).value == case["expect"], case["why"]


def test_fixture_spans_both_answers_and_every_corpus() -> None:
    """The fixture is not one-sided: real positives AND real negatives, from all three corpora."""
    expects = {c["expect"] for c in _CASES}
    assert {"verbatim", "elided", "not_found"} <= expects
    assert {c["corpus"] for c in _CASES} == {"covenant_term", "maturity_event", "graph_edge"}
    for c in _CASES:  # a piece of a committed quote is still a committed quote's text
        assert c["quote"] in c["committed_quote"]


def test_empty_quote_is_never_found() -> None:
    """(-) "" is a substring of every text, so an empty quote must not read as found — a value
    with no quote is bound to nothing."""
    src = SourceText(_case("amzn-maturity-tag-spaces")["window"])
    for q in ("", "   ", "\n\t", "...", "…"):
        m = src.match(q)
        assert not m.found, repr(q)
    assert src.match("").value == SpanMatch.EMPTY


def test_each_reduction_is_load_bearing_on_its_own_real_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(+) Undo one reduction and its real case stops matching — so no step is decorative. The
    corpus counts behind each (2026-10-26, 732 covenant + graph quotes): whitespace 83, quote marks
    97, NFKC 1, dashes 1, case 1."""
    import re
    import unicodedata

    from vinci import verbatim

    def without(step: str) -> typing.Callable[[str], str]:
        def key(text: str) -> str:
            s = text if step == "nfkc" else unicodedata.normalize("NFKC", text)
            table: dict[str, str] = {}
            if step != "quotes":
                table.update(dict.fromkeys(verbatim._QUOTE_MARKS, "'"))
            if step != "dashes":
                table.update(dict.fromkeys(verbatim._DASHES, "-"))
            s = s.translate(str.maketrans(table))
            s = s if step == "case" else s.casefold()
            return (re.sub(r"\s+", " ", s).strip() if step == "ws"
                    else verbatim._DROP.sub("", s))
        return key

    for step, case_id in [("ws", "amzn-maturity-tag-spaces"), ("quotes", "klic-quote-marks"),
                          ("nfkc", "amzn-unicode-ellipsis"), ("dashes", "aort-nonbreaking-hyphen"),
                          ("case", "mvst-case")]:
        c = _case(case_id)
        assert SourceText(c["window"]).match(c["quote"]).found, case_id
        with monkeypatch.context() as m:
            m.setattr(verbatim, "comparison_key", without(step))
            assert not SourceText(c["window"]).match(c["quote"]).found, (step, case_id)


def test_punctuation_is_trimmed_at_a_cut_and_nowhere_else() -> None:
    """(+/-) A stop the model closed its cut with (UBER) and a semicolon opening a piece after an
    ellipsis (AORT) belong to the cut: neither untrimmed quote is in its exhibit, both match. Inside
    a piece nothing is dropped — BKTI's filing reads 'LLC,,' and the corrected 'LLC,' is refused."""
    for case_id, how in [("uber-cut-stop", SpanMatch.VERBATIM),
                         ("uber-cut-stop-after-ellipsis", SpanMatch.ELIDED),
                         ("aort-punctuation-at-ellipsis", SpanMatch.ELIDED)]:
        c = _case(case_id)
        key = comparison_key(c["window"])
        pieces = [p for p in comparison_key(c["quote"]).split("...") if p]
        assert any(p not in key for p in pieces), case_id  # untrimmed, a piece is not a span
        assert SourceText(c["window"]).match(c["quote"]) is how, case_id
    bkti = _case("bkti-typo-corrected")
    assert "LLC,," in bkti["window"] and "LLC,," not in bkti["quote"]
    assert SourceText(bkti["window"]).match(bkti["quote"]) is SpanMatch.NOT_FOUND


def test_out_of_order_pieces_are_refused_though_each_piece_is_present() -> None:
    """(-) TGT's interest quote: every piece is in the exhibit, but in a different order. Elision
    forgives an OMISSION; it never forgives a rearrangement."""
    c = _case("tgt-elided-out-of-order")
    key = comparison_key(c["window"])
    pieces = [p for p in comparison_key(c["quote"]).split("...") if p.strip(".")]
    assert len(pieces) >= 2 and all(p.strip(".;:,") in key for p in pieces)
    assert SourceText(c["window"]).match(c["quote"]) is SpanMatch.NOT_FOUND


def test_page_furniture_is_not_forgiven() -> None:
    """(-) TJX: the quote is the clause without the page number '- 31 -' the exhibit prints inside
    it. Most likely read correctly; refused anyway. A gap of digits is the one gap a span check must
    never forgive — it is where a figure would hide. Removing the page number from the window
    shows the rest of the quote is the document's own text."""
    c = _case("tjx-page-furniture")
    assert "- 31 -" in c["window"]
    assert SourceText(c["window"]).match(c["quote"]) is SpanMatch.NOT_FOUND
    assert SourceText(c["window"].replace("- 31 - ", "")).match(c["quote"]) is SpanMatch.VERBATIM


# --- end to end: covenant terms ------------------------------------------------------------------


class _FakeLlm(LlmClient):
    def __init__(self, payload: dict[str, typing.Any]) -> None:
        self._payload = payload

    @property
    def model(self) -> str:
        return "fake-model-1"

    def extract(
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        return self._payload


class _FakeSecHttp:
    """An SEC http serving one document's text (get_text) and one filing index (get_json)."""

    def __init__(self, text: str, index: list[str] | None = None) -> None:
        self._text, self._index = text, index or []

    def get_text(self, url: str, ttl_seconds: object = None) -> str:
        return self._text

    def get_json(self, url: str, ttl_seconds: object = None) -> dict[str, typing.Any]:
        return {"directory": {"item": [{"name": n} for n in self._index]}}


_TJX_ACC, _TJX_DOC = "0000109198-25-000033", "exhibit101-firstamendmentt.htm"
_TJX_PTR = ds.CovenantPointer(family="Revolving Credit Facility", filing="8-K",
                              filing_date="2025-05-13", accession=_TJX_ACC, exhibits=[_TJX_DOC])


def _tjx_capital_structure() -> ds.CapitalStructure:
    u = ds.Sourced[str].unknown(note="n/a")
    return ds.CapitalStructure(
        instruments=ds.Sourced.unknown(note="n/a"), summary=u, detail_as_of="2026-10-26",
        maturity_filings=u, covenant_pointers=ds.Sourced.present("located", source_ref="efts"),
        covenant_pointer_rows=ds.Sourced.present([_TJX_PTR], source_ref="efts"),
        covenant_terms=ds.Sourced.unknown(note="(E5) pending"))


def test_covenant_terms_keep_a_span_and_refuse_the_rest_end_to_end() -> None:
    """(+/-) Through `extract_covenant_terms` on TJX's real exhibit text: the clause's first piece
    is a span and stays PRESENT; TJX's committed quote (read across '- 31 -') and a present term
    with no quote are each UNKNOWN + a flag naming the term; an absent term is 'not stated'.
    A refused note keeps the exhibit's accession (the collapse dates rows by it), and the
    governing collapse — what the synthesis digest is built from — never revives a refused
    value."""
    c = _case("tjx-page-furniture")
    exhibit = f"{c['document_head']} … {c['window']}"
    first_piece = c["quote"].split("; and (ii)")[0] + "; and"
    payload = {"terms": [
        {"name": "Interest / coupon rate", "present": True,
         "value": "Adjusted Term SOFR plus the Applicable Margin", "quote": c["quote"]},
        {"name": "Term SOFR Loans", "present": True,
         "value": "Adjusted Term SOFR plus the Applicable Margin", "quote": first_piece},
        {"name": "Maturity date", "present": True, "value": "June 2029", "quote": ""},
        {"name": "Conversion price / mechanics", "present": False, "value": "", "quote": ""},
    ]}
    rows, summary, flags, _ = ce.extract_covenant_terms(
        _tjx_capital_structure(), llm=_FakeLlm(payload),
        http=typing.cast(typing.Any, _FakeSecHttp(exhibit)),
        cik="0000109198", ticker="TJX", name="TJX Companies")
    assert rows is not None
    by = {r.name: r for r in rows.value}
    src = f"8-K {_TJX_ACC} · {_TJX_DOC}"

    kept = by["Term SOFR Loans"].value
    assert kept.status is ds.SourceStatus.PRESENT and kept.source_ref == src
    assert kept.note == f"verbatim: “{first_piece}”"

    for name, why in [("Interest / coupon rate", "quote is not in"),
                      ("Maturity date", "gave no quote from")]:
        v = by[name].value
        assert v.status is ds.SourceStatus.UNKNOWN and v.value is None, name
        assert why in (v.note or "") and ce._acc_of(v.note) == _TJX_ACC, name
        assert any(name in f and "refused" in f and _TJX_ACC in f for f in flags), name
    assert by["Interest / coupon rate"].margin_pct is None  # no component rides on a refusal
    assert "not stated" in (by["Conversion price / mechanics"].value.note or "")
    assert len([f for f in flags if "covenant term refused" in f]) == 2
    assert summary.value is not None and summary.value.startswith("1 of 4 ")

    governing = {g.term: g for g in ce.governing_terms(list(rows.value), [_TJX_PTR])}
    assert governing["Term SOFR Loans"].value.status is ds.SourceStatus.PRESENT
    for name in ("Interest / coupon rate", "Maturity date"):
        assert governing[name].value.status is ds.SourceStatus.UNKNOWN, name


# --- end to end: the maturity event --------------------------------------------------------------


def _maturity_cs() -> ds.CapitalStructure:
    u = ds.Sourced[str].unknown(note="n/a")
    return ds.CapitalStructure(
        instruments=u, summary=u, detail_as_of="2026-10-26", covenant_pointers=u,
        covenant_terms=u, maturity_filings=ds.Sourced.present(
            "8-K at maturity 2026-08-14: filed 2026-08-14 [0000027419-26-000032] 1.01",
            source_ref="EDGAR"))


def test_maturity_event_refuses_the_label_the_model_added_end_to_end() -> None:
    """(-/+) TGT's committed maturity verbatim opens 'Section 3.01(e):', which the 8-K body does not
    print — UNKNOWN + a flag. The same clause as the body prints it is kept."""
    c = _case("tgt-label-added")
    http = typing.cast(typing.Any, _FakeSecHttp(c["window"], index=[
        "0000027419-26-000032-index.html", "five-yearcreditagreementex.htm"]))
    ev, flags, _ = ce.extract_maturity_event(
        _maturity_cs(), llm=_FakeLlm({"present": True, "verbatim": c["quote"]}), http=http,
        cik="0000027419", ticker="TGT", name="Target")
    assert ev is not None and ev.status is ds.SourceStatus.UNKNOWN and ev.value is None
    assert "refused" in (ev.note or "") and "0000027419-26-000032" in (ev.note or "")
    assert len(flags) == 1 and "maturity event refused" in flags[0]

    as_printed = c["quote"].replace("Section 3.01(e): ", "(e) ", 1)
    ev2, flags2, _ = ce.extract_maturity_event(
        _maturity_cs(), llm=_FakeLlm({"present": True, "verbatim": as_printed}), http=http,
        cik="0000027419", ticker="TGT", name="Target")
    assert ev2 is not None and ev2.status is ds.SourceStatus.PRESENT and not flags2


# --- end to end: graph edges ---------------------------------------------------------------------


class _UnresolvingResolver:
    def resolve_ticker(self, ticker: str) -> typing.Any:
        raise UnknownSymbolError(ticker)

    def resolve_name(self, name: str) -> typing.Any:
        raise UnknownSymbolError(name)


class _GraphLlm(_FakeLlm):
    """Answers the extractor with ``payload`` and the evidence judge with a fixed verdict."""

    def extract(
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        if tool["name"] == gx.EXTRACT_TOOL["name"]:
            return self._payload
        return {"verdict": "real_supply_chain", "reason": "named"}


_ATOM = Identity(internal_id="SEC-0001420520-ATOM", issuer_id="ISS-0001420520",
                 cik="0001420520", ticker="ATOM", mic="XNAS", exchange="Nasdaq",
                 eod_symbol="ATOM", name="Atomera Inc")


def _atom_payload() -> dict[str, typing.Any]:
    c = _case("atom-sentences-reordered")
    span = "electronic design automation software companies, such as Synopsys"
    assert span in c["window"]
    return {"relationships": [
        {"counterparty_name": "Synopsys", "relationship": "supplier", "evidence": c["quote"]},
        {"counterparty_name": "Synopsys", "relationship": "supplier", "evidence": span},
    ]}


def _serve_atom_excerpts(monkeypatch: pytest.MonkeyPatch) -> None:
    c = _case("atom-sentences-reordered")
    monkeypatch.setattr(gx, "latest_10k_excerpts",
                        lambda edgar, cik, http=None: ("0001683168-26-001291", c["window"]))


def test_graph_edge_with_reordered_evidence_is_refused_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(-/+) Through `extract_graph_edges` on ATOM's real 10-K excerpt: its committed evidence
    (a sentence's end placed before the sentence) is refused and counted; a real span is kept."""
    _serve_atom_excerpts(monkeypatch)
    edges, info = gx.extract_graph_edges(
        typing.cast(typing.Any, None), typing.cast(typing.Any, _UnresolvingResolver()),
        _GraphLlm(_atom_payload()), _ATOM)
    assert [e.evidence for e in edges] == [_atom_payload()["relationships"][1]["evidence"]]
    assert info["evidence_refused"] == 1 and info["resolution"]["evidence_refused"] == 1


def test_coverage_report_states_the_refusals(monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) A refused edge is not silently absent from the coverage read: the count reaches the
    name's row and the report total, beside the edges that survived."""
    _serve_atom_excerpts(monkeypatch)
    rep = gcov.graph_coverage(
        typing.cast(typing.Any, None), typing.cast(typing.Any, _UnresolvingResolver()),
        _GraphLlm(_atom_payload()), [_ATOM])
    assert rep["total_edges"] == 1 and rep["evidence_refused"] == 1
    assert rep["per_name"][0]["evidence_refused"] == 1


# --- provenance: the fixture is the real text ----------------------------------------------------


@pytest.mark.network
def test_fixture_windows_are_the_cited_documents_text() -> None:
    """Every window is a verbatim slice of the EDGAR document it cites, read the way its extractor
    read it, and the whole document gives the same answer as the window."""
    import re

    from vinci.graph.filings import html_to_text, relevant_excerpts
    from vinci.resolver.index import pad_cik
    from vinci.sec import build_sec_http

    http = build_sec_http()
    for c in _CASES:
        m = re.match(r"^\S+ (\d{10}-\d{2}-\d{6}) · (.+)$", c["source"])
        assert m is not None, c["id"]
        url = (f"https://www.sec.gov/Archives/edgar/data/{int(pad_cik(c['cik']))}/"
               f"{m.group(1).replace('-', '')}/{m.group(2)}")
        text = html_to_text(http.get_text(url, ttl_seconds=None))
        if c["source_text"].startswith("relevant_excerpts"):
            text = relevant_excerpts(text)
        assert c["window"] in text, c["id"]
        assert SourceText(text).match(c["quote"]).value == c["expect"], c["id"]
