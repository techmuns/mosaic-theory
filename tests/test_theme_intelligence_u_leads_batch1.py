"""Four verified review leads (`docs/records/2026-10-14-theme-intelligence-unverified-leads-
verified.md`):

- U24 two pages with no body share one content hash: one version id across two articles failed
  the whole scan (two cached BofA pages);
- U16 time windows: "since May 2026" read as May alone, "next four quarters" as 368 days, "$2050
  per ounce" as the year 2050, "Q1 FY27" as calendar 2027; "next N months" not read at all;
- U46 a therapy area with no segment took the pharma node's BARE key — the key the pilot's
  gene-editing thesis held;
- U49 a figure with an unknown glued unit was cut at its decimal point ("707.5GVA" → 707), and the
  grid and gas units were missed.

Articles are HYPOTHETICAL and labelled; extractions use the REAL types.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.completeness import scan_article
from vinci.theme_intelligence.config import load_taxonomy
from vinci.theme_intelligence.parse import parse_document
from vinci.theme_intelligence.schemas import (
    Claim,
    ClaimKind,
    Confidence,
    Epistemic,
    ThesisStatus,
)
from vinci.theme_intelligence.timewindow import timing_of

AS_OF = date(2026, 10, 14)
PHARMA = "healthcare.pharma_biotech"


# --- U24 ---------------------------------------------------------------------------------------

SHELL = ("<html><head><title>Loading</title></head><body><div id='root'><noscript>Please enable "
         "JavaScript to view this page.</noscript></div></body></html>")


def test_two_pages_with_no_body_are_two_articles_never_one_version(tmp_path: Path) -> None:
    from tests.theme_intelligence_support import fetched
    from vinci.theme_intelligence.schemas import RetrievalState

    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    got = []
    for url in ("https://example.test/hypothetical/a", "https://example.test/hypothetical/b",
                "https://example.test/hypothetical/a"):  # the first page, fetched again
        doc = parse_document(SHELL, url)
        assert doc.retrieval_state is RetrievalState.BLOCKED
        got.append(pipe.process_document(doc, fetched(doc, state=RetrievalState.BLOCKED),
                                         url=url, source_id="jpm_tmt", as_of=AS_OF, fixture={}))
    assert [r.status for r in got] == ["NO_BODY", "NO_BODY", "NO_BODY"]
    assert got[0].version_id != got[1].version_id  # one id per article, never shared
    assert got[2].version_id == got[0].version_id  # the same article's shell: the same version
    assert len(pipe.store.article_versions(got[0].article_id or "")) == 1


def test_a_page_with_a_body_keeps_its_content_id_and_a_copy_is_one_article(
        tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    text = "[HYPOTHETICAL] Optical shipments rose 14% in 3Q26 at a hypothetical supplier."
    a = Hypo(slug="one", publisher="Hypo", published=date(2026, 10, 2),
             blocks=[("paragraph", text)])
    ext = extraction([claim("c1", "b001", "Optical shipments rose 14% in 3Q26",
                            "Optical shipments +14%", value=14, value_text="14%", unit="%",
                            period="3Q26")], [])
    first = ingest(pipe, a.doc(), ext, as_of=AS_OF)
    copy = Hypo(slug="two", publisher="Hypo", published=date(2026, 10, 2),
                blocks=[("paragraph", text)]).doc()  # the same text at another URL
    assert copy.content_sha256 == a.doc().content_sha256
    second = ingest(pipe, copy, ext, as_of=AS_OF)
    assert first.version_id == "AV-" + a.doc().content_sha256[:16]
    assert second.status == "DUPLICATE_CONTENT"


# --- U16 ---------------------------------------------------------------------------------------

def _c(*, period: str | None, epistemic: Epistemic, kind: ClaimKind = ClaimKind.METRIC,
       quote: str = "[HYPOTHETICAL] a statement") -> Claim:
    return Claim(claim_id="C-1", article_id="A-1", article_version_id="AV-1", block_id="b001",
                 char_start=0, char_end=1, quote=quote, statement=quote, kind=kind,
                 epistemic=epistemic, period=period, confidence=Confidence.HIGH,
                 span_verified=True, number_verified=None, measure_key="k", fingerprint="f",
                 extraction_id="X-1")


PUBLISHED = date(2026, 10, 8)


@pytest.mark.parametrize(("period", "epistemic", "kind", "quote", "expected"), [
    # "since X" runs to the source's date: a current observation, never X's own end
    ("since May 2026", Epistemic.ACTUAL, ClaimKind.METRIC, "", "current"),
    ("since mid-2023", Epistemic.ACTUAL, ClaimKind.METRIC, "", "current"),
    ("since the start of 2024", Epistemic.ACTUAL, ClaimKind.METRIC, "", "current"),
    ("since 2019", Epistemic.FORECAST, ClaimKind.METRIC, "", "historical"),  # a past window
    # N quarters are N fourths of a year; N months are read
    ("next four quarters", Epistemic.FORECAST, ClaimKind.FORECAST, "", "near_term"),
    ("within two quarters", Epistemic.FORECAST, ClaimKind.FORECAST, "", "near_term"),
    ("next six months", Epistemic.FORECAST, ClaimKind.FORECAST, "", "near_term"),
    ("next 18 months", Epistemic.FORECAST, ClaimKind.FORECAST, "", "straddling"),
    # an amount is not a year
    (None, Epistemic.FORECAST, ClaimKind.FORECAST,
     "[HYPOTHETICAL] gold will reach $2050 per ounce", "undated"),
    (None, Epistemic.FORECAST, ClaimKind.FORECAST,
     "[HYPOTHETICAL] demand will double by 2050", "long_range"),
    # a fiscal quarter is not placed; a fiscal year is, approximately
    ("Q1 FY27", Epistemic.FORECAST, ClaimKind.FORECAST, "", "undated"),
    ("3Q26", Epistemic.ACTUAL, ClaimKind.METRIC, "", "current"),
])
def test_a_claims_time_window_is_read_as_the_source_states_it(
        period: str | None, epistemic: Epistemic, kind: ClaimKind, quote: str,
        expected: str) -> None:
    c = _c(period=period, epistemic=epistemic, kind=kind,
           quote=quote or "[HYPOTHETICAL] a statement")
    got, note = timing_of(c, AS_OF, PUBLISHED)
    assert got == expected, note


def test_since_with_an_end_is_a_closed_window_not_one_to_the_source_date() -> None:
    got, note = timing_of(_c(period="since May to end September 2026",
                             epistemic=Epistemic.ACTUAL), AS_OF, PUBLISHED)
    assert got == "current" and "measured 2026-09-30" in note  # its own end, not 10-08
    open_ended, note2 = timing_of(_c(period="since May 2026", epistemic=Epistemic.ACTUAL),
                                  AS_OF, PUBLISHED)
    assert open_ended == "current" and "measured 2026-10-08" in note2  # the source's date


def test_since_with_a_closing_year_is_that_range() -> None:
    got, note = timing_of(_c(period="since 2019 to 2023", epistemic=Epistemic.ACTUAL), AS_OF,
                          PUBLISHED)
    assert got == "historical" and "measured 2023-12-31" in note


@pytest.mark.parametrize(("period", "start"), [
    ("since mid-2023", date(2023, 7, 1)), ("since late 2024", date(2024, 10, 1)),
    ("since the start of 2024", date(2024, 1, 1)), ("since May 2026", date(2026, 5, 1)),
])
def test_a_since_window_starts_where_the_source_says(period: str, start: date) -> None:
    from vinci.theme_intelligence.timewindow import window_of

    w = window_of(period, AS_OF)
    assert w is not None and w.start == start and w.end == AS_OF and w.to_date


def test_a_fiscal_quarter_says_why_it_is_not_placed() -> None:
    got, note = timing_of(_c(period="Q1 FY27", epistemic=Epistemic.FORECAST,
                             kind=ClaimKind.FORECAST), AS_OF, PUBLISHED)
    assert got == "undated" and "fiscal calendar is not known" in note
    fy, fy_note = timing_of(_c(period="FY27", epistemic=Epistemic.FORECAST,
                               kind=ClaimKind.FORECAST), AS_OF, PUBLISHED)
    assert fy == "straddling" and "fiscal year read as the calendar year" in fy_note


# --- U46 ---------------------------------------------------------------------------------------

def _pharma_article(slug: str, sentence: str, title: str, *,
                    published: date) -> tuple[Hypo, dict[str, Any]]:
    art = Hypo(slug=slug, publisher=f"Hypothetical {slug.title()} Research", published=published,
               blocks=[("paragraph", f"[HYPOTHETICAL] {sentence}")])
    quote = sentence.rstrip(".")
    ext = extraction([claim("c1", "b001", quote, quote, kind="forecast", epistemic="forecast",
                            metric="addressable market", value=30, value_text="30%", unit="%",
                            period="2027")],
                     [hyp("h1", title, node=PHARMA, mechanism="demand_volume_shift",
                          supporting=["c1"])])
    return art, ext


GENE = ("In-vivo gene editing opens new organ markets above consensus by 2035",
        "In-vivo gene editing therapies are expected to grow their addressable market 30% in "
        "2027.")
IMMUNO = ("Immunology biologics (IL-23, TL1A) widen the autoimmune market",
          "Immunology biologics are expected to grow their addressable market 30% in 2027.")


def test_another_therapy_area_is_another_thesis(tmp_path: Path) -> None:
    """With only four pharma segments, an immunology thesis named none and took the BARE key the
    gene-editing thesis held — the second article silently updated the first thesis."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    for slug, (title, sentence), d in (("gene", GENE, date(2026, 10, 2)),
                                       ("immuno", IMMUNO, date(2026, 10, 6))):
        art, ext = _pharma_article(slug, sentence, title, published=d)
        ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)
    by_seg = {t.key_segment: t.title for t in pipe.store.theses()}
    assert by_seg == {"genetic_medicine": GENE[0], "immunology": IMMUNO[0]}


def test_a_thesis_keyed_before_its_segment_existed_is_found_and_re_keyed(tmp_path: Path) -> None:
    """A segment added to the taxonomy: the thesis created before it holds the bare key. The next
    article on its subject finds it there — and re-keys it — never a duplicate under the new key."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    full = pipe.engine.taxonomy
    pipe.engine.taxonomy = replace(full, segments=tuple(s for s in full.segments
                                                        if s.id != "genetic_medicine"))
    art, ext = _pharma_article("gene", GENE[1], GENE[0], published=date(2026, 10, 2))
    ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)
    [old] = pipe.store.theses()
    assert old.key_segment == ""  # created under the bare key
    pipe.engine.taxonomy = full  # the segment exists now
    later = "Gene editing programs are expected to grow their addressable market 30% in 2027."
    art2, ext2 = _pharma_article("gene2", later, "Gene editing reaches new organs",
                                 published=date(2026, 10, 9))
    ingest(pipe, art2.doc(), ext2, as_of=AS_OF, publisher=art2.publisher)
    [t] = pipe.store.theses()
    assert t.thesis_id == old.thesis_id and t.key_segment == "genetic_medicine"
    assert "KEY_CORRECTED" in {i.code for i in pipe.store.issues()}


def test_two_unsegmented_theses_on_one_bare_key_are_flagged_never_silent(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    for slug, title, sentence, d in (
            ("eyes", "Retinal therapies reach more patients",
             "Retinal therapies are expected to grow their addressable market 30% in 2027.",
             date(2026, 10, 2)),
            ("ears", "Hearing-loss therapies reach more patients",
             "Hearing-loss therapies are expected to grow their addressable market 30% in 2027.",
             date(2026, 10, 6))):
        art, ext = _pharma_article(slug, sentence, title, published=d)
        ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)
    [t] = pipe.store.theses()  # one bare key: updated, as before …
    flagged = [i for i in pipe.store.issues() if i.code == "UNSEGMENTED_KEY"]
    assert len(flagged) == 1 and t.thesis_id in flagged[0].detail  # … and said
    assert t.status is not ThesisStatus.ARCHIVED


# --- U49 ---------------------------------------------------------------------------------------

def _figures(text: str) -> list[str]:
    doc = Hypo(slug="figs", publisher="Hypo", published=date(2026, 10, 2),
               blocks=[("paragraph", f"[HYPOTHETICAL] {text}")]).doc()
    return [f.core for f in scan_article(doc).figures]


@pytest.mark.parametrize(("text", "cores"), [
    ("Analysts estimate a 707.5GVA annual shortfall against 2,358.5GVA of supply.",
     ["707.5", "2,358.5"]),
    ("Demand for high voltage (>110kV) and 345kV transformers keeps growing.", ["110", "345"]),
    ("Pipelines point to ~7.5bcf/d of incremental gas demand and $38bln of projects.",
     ["7.5", "38"]),
    ("Inflation rose by around 1.3ppt while NOx fell to 0.10g/kWh.", ["1.3", "0.10"]),
])
def test_grid_and_gas_units_are_read_with_their_whole_figure(text: str, cores: list[str]) -> None:
    assert _figures(text) == cores


@pytest.mark.parametrize("text", [
    "capacity reached 12.5ZW and then 8.75QQ.",  # unknown units: missed, never "12" and "8"
    "The 4.5G network and B200 chips use 800V and 5G parts.",  # labels, not figures
])
def test_an_unknown_glued_unit_is_missed_never_cut_at_the_decimal(text: str) -> None:
    assert _figures(text) == []


def test_the_taxonomy_lists_the_four_new_pharma_segments() -> None:
    ids = {s.id for s in load_taxonomy().segments_of(PHARMA)}
    assert {"genetic_medicine", "immunology", "vaccines", "cardiovascular"} <= ids
