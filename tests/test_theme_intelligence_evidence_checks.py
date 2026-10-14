"""Evidence checks that let a wrong fact through as verified (code review of PR #703, 2026-10-14).

- A non-verbatim quote re-anchored to a source sentence that says the OPPOSITE ("rose 9%" /
  "fell 9%"; a dropped "not").
- A figure matched as a raw substring ('5' inside '15%'), a unit the figure contradicts ('8x'
  with unit '%'), a name inside another word ("Meta" in "metadata", "AI" in "said").
- A card line's numbers checked against the model's own statement, and an empty quote verified.

End to end through the REAL engine on HYPOTHETICAL articles (invented text, `.test` domain);
extractions in the real type. The corpus check is in the build record.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
    mention,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import Claim
from vinci.theme_intelligence.verify import _number_check

AS_OF = date(2026, 10, 1)
MEMORY = "ai_infrastructure.memory"


def _run(tmp: Path, blocks: list[str], claims: list[dict[str, Any]], *, fact: str | None = None,
         title: str = "DRAM contract prices are rising", fact_cites: list[str] | None = None,
         mentions: list[dict[str, Any]] | None = None,
         sectors: list[tuple[str, str, str]] | None = None) -> tuple[Pipeline, str]:
    art = Hypo(slug="evidence-checks", publisher="Hypo Research E", published=date(2026, 9, 28),
               blocks=[("paragraph", b) for b in blocks])
    h = hyp("h1", title, node=MEMORY, mechanism="pricing_cycle",
            supporting=[c["local_id"] for c in claims], sectors=sectors)
    if fact is not None:
        h["bottom_line_fact"] = {"text": fact, "provenance": "source_stated",
                                 "claim_ids": fact_cites or [claims[0]["local_id"]]}
    pipe = make_pipeline(tmp)
    pipe.start_run("fixture", as_of=AS_OF)
    res = ingest(pipe, art.doc(), extraction(claims, [h], mentions=mentions), as_of=AS_OF)
    return pipe, res.article_id


def _claims(pipe: Pipeline, aid: str) -> list[Claim]:
    return pipe.store.claims_for_article(aid)


def _linked(pipe: Pipeline) -> set[str]:
    return {lk.claim_id for t in pipe.store.theses() for lk in pipe.store.links(t.thesis_id)}


# --- 1. a re-anchor never reverses the quote --------------------------------------------------

def test_a_misquote_that_reverses_the_source_is_never_re_anchored_into_evidence(
        tmp_path: Path) -> None:
    """The model's quote and statement say 'rose 9%'; the source says 'fell 9%'. The re-anchor
    used to swap in the 'fell' sentence and keep the 'rose' statement — span- and number-verified,
    linked SUPPORTS, printed as a MEASURED OBSERVATION. Now it is not re-anchored: the quote is
    not verbatim, so the claim is not verified and supports nothing."""
    pipe, aid = _run(tmp_path, ["Conventional DRAM contract prices fell 9% in the third quarter, "
                                "the survey shows."],
                     [claim("c1", "b001", "Conventional DRAM contract prices rose 9% in the third "
                            "quarter", "DRAM contract prices rose 9% in 3Q26", value=9,
                            value_text="9%", unit="%", period="3Q26")])
    [c] = _claims(pipe, aid)
    assert c.span_verified is False and "fell" not in c.quote
    assert c.claim_id not in _linked(pipe)


def test_a_misquote_that_drops_a_not_is_never_re_anchored(tmp_path: Path) -> None:
    """'are expected to rise 10%' against the source's '…are not expected to rise 10%': "not" is a
    stop word, so the content overlap was 1.0."""
    pipe, aid = _run(tmp_path, ["Analysts say DRAM contract prices are not expected to rise 10% "
                                "next quarter."],
                     [claim("c1", "b001", "Analysts say DRAM contract prices are expected to rise "
                            "10% next quarter", "DRAM prices expected to rise 10%", value=10,
                            value_text="10%", unit="%", epistemic="forecast", kind="forecast")])
    [c] = _claims(pipe, aid)
    assert c.span_verified is False and c.claim_id not in _linked(pipe)


def test_a_paraphrase_that_agrees_with_the_source_is_still_re_anchored(tmp_path: Path) -> None:
    """NEGATIVE pin: a non-verbatim quote saying the SAME thing (same direction, no negation) is
    re-anchored to the source sentence and verified, as before."""
    src = "Conventional DRAM contract prices rose 9% in the third quarter, the survey shows."
    pipe, aid = _run(tmp_path, [src],
                     [claim("c1", "b001", "Conventional DRAM contract prices rose about 9% in the "
                            "third quarter of the year", "DRAM contract prices rose 9% in 3Q26",
                            value=9, value_text="9%", unit="%", period="3Q26")])
    [c] = _claims(pipe, aid)
    assert c.span_verified is True and c.quote == src
    assert c.claim_id in _linked(pipe)


# --- 2. a figure, a unit and a name are matched whole ------------------------------------------

def test_a_figure_is_matched_whole_never_inside_another_number(tmp_path: Path) -> None:
    """Value 5 against 'grew 15%' was number-verified and printed 'grew 5%' as a MEASURED
    OBSERVATION. NEGATIVE pins (real corpus shapes): a currency prefix or a unit glued on stays
    verbatim."""
    pipe, aid = _run(tmp_path, ["DRAM revenue grew 15% in 3Q26, the survey shows."],
                     [claim("c1", "b001", "DRAM revenue grew 15% in 3Q26", "DRAM revenue grew 5%",
                            value=5, value_text="5%", unit="%", period="3Q26")])
    [c] = _claims(pipe, aid)
    assert c.number_verified is False
    assert c.claim_id not in _linked(pipe)
    for value, vt, unit, quote in [
            (2600, "2,600", "units", "shipments reached 12,600 units"),
            (2600, "2,600", "units", "shipments reached 2,600,000 units"),
            (1.5, "1.5", "%", "margin reached 21.5%"),
            (-7, "7%", "%", "a 27% decline in orders"),
            (8, "8x", "%", "valuations reached 8x sales")]:
        assert _number_check(value, vt, unit, quote)[0] is False, (vt, quote)
    for value, vt, unit, quote in [
            (1.655, "$1.655 billion", "$bn", "It will spend US$1.655 billion on a plant"),
            (707.5, "707.5", "GVA", "a 707.5GVA annual shortfall in 2025"),
            (-7, "7%", "%", "a 7% decline in orders"),
            (15, "15%", "%", "DRAM revenue grew 15% in 3Q26")]:
        assert _number_check(value, vt, unit, quote)[0] is True, (vt, quote)


def test_a_name_must_occur_as_whole_words_in_the_text(tmp_path: Path) -> None:
    """"Meta" verified from "metadata" and the sector "AI" from "said". NEGATIVE pins: a footnote
    marker glued to a name ("COP2814") and a plural ("data centers") still verify."""
    text = ("Analysts said the metadata layer grows as data centers add memory; the COP2814 "
            "pledge and Micron's guidance point the same way, with DRAM prices up 9%.")
    pipe, _aid = _run(
        tmp_path, [text],
        [claim("c1", "b001", "DRAM prices up 9%", "DRAM prices up 9%", value=9, value_text="9%",
               unit="%")],
        mentions=[mention("Meta", "b001", "the metadata layer"),
                  mention("COP28", "b001", "the COP2814 pledge", entity_type="other_organization",
                          role="context", direction="neutral"),
                  mention("Micron", "b001", "Micron's guidance")],
        sectors=[("AI", "b001", "Analysts said the metadata layer"),
                 ("data center", "b001", "data centers add memory")])
    names = {m.name_as_written for m in _stored_mentions(pipe)}
    assert "Meta" not in names and {"COP28", "Micron"} <= names
    [t] = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    assert [s.name for s in v.content.s05_affected.sector_exposures] == ["data center"]


def _stored_mentions(pipe: Pipeline) -> list[Any]:
    from vinci.theme_intelligence.schemas import Mention
    return [Mention.model_validate_json(r[0])
            for r in pipe.store.conn.execute("SELECT payload FROM mentions")]


# --- 3. a card line is checked against the verbatim evidence -----------------------------------

def _card_issues(pipe: Pipeline) -> list[tuple[str, str]]:
    assert pipe.run is not None
    return [(i.code, i.detail) for i in pipe.store.issues(run_id=pipe.run.run_id)
            if i.scope == "card_sentence"]


def test_a_card_line_never_vouches_for_its_own_numbers(tmp_path: Path) -> None:
    """The quote carries no figure; the model's statement says 'rise 40% to $900bn in 2027' and
    the bottom line prints it. The check pooled the statement, so the line was checked against
    itself: no issue. Now every unsupported figure is a NUMBER_NOT_IN_CITED_CLAIMS BLOCK."""
    q = "Hyperscaler capex will rise sharply next year"
    pipe, _aid = _run(tmp_path, [f"{q}, the note says."],
                      [claim("c1", "b001", q, "Hyperscaler capex will rise 40% to $900bn in 2027",
                             kind="forecast", epistemic="forecast")],
                      fact="Hyperscaler capex will rise 40% to $900bn in 2027.")
    flagged = {d.split(" prints ")[1].split(",")[0] for code, d in _card_issues(pipe)
               if code == "NUMBER_NOT_IN_CITED_CLAIMS" and d.startswith("s01.0")}
    assert flagged == {"'40'", "'900'", "'2027'"}


def test_a_line_printing_its_claims_period_or_a_version_name_passes(tmp_path: Path) -> None:
    """NEGATIVE pin: the period the claim is stated for ('2027') and a version NAME the line
    adds ("Opus 4.5", the pilot's shape: "Era 3", "Industry 5.0" on lines whose quotes do not
    name them) are not figures the line asserts beyond its evidence — no issue."""
    q = "Inference demand doubled DRAM orders next year, the note says"
    pipe, _aid = _run(tmp_path, [f"{q}."],
                      [claim("c1", "b001", q, "Inference demand doubled DRAM orders in 2027",
                             kind="forecast", epistemic="forecast", value=2,
                             value_text="doubled", period="2027")],
                      fact="Opus 4.5 inference demand doubled DRAM orders in 2027.")
    assert not [d for code, d in _card_issues(pipe) if code == "NUMBER_NOT_IN_CITED_CLAIMS"]


def test_an_empty_quote_is_never_a_verified_span(tmp_path: Path) -> None:
    """`locate("", text)` found "" at 0 in every text: a claim with an empty quote was
    span-verified, linked SUPPORTS and printed as a MEASURED OBSERVATION."""
    pipe, aid = _run(tmp_path, ["DRAM makers are adding capacity, the survey shows."],
                     [claim("c1", "b001", "", "DRAM makers are adding capacity", kind="event")])
    [c] = _claims(pipe, aid)
    assert c.span_verified is False and c.claim_id not in _linked(pipe)


# --- 4. one name resolved two ways is two records ------------------------------------------------

def test_one_name_resolved_two_ways_in_one_article_is_two_records_never_a_clash(
        tmp_path: Path) -> None:
    """The resolution id hashed only name, status, cik and tickers, while the store compares the
    whole record: "Citi" named as a data source with hint C (refused: the hint names another
    issuer) and as context without a hint (refused on identity) got ONE id with two payloads —
    StoreIntegrityError rolled back the article and failed the scan, on every resume too. Here
    the same shape on the authentic SEC subset: "Meta Critical" partly matches Meta Critical
    Minerals — with hint NVDA it is refused as another issuer's; typed a private company it is
    refused as a partial name. Both UNRESOLVED, no CIK. NEGATIVE pin: the same resolution
    written again is still one record."""
    text = "Meta Critical data show DRAM prices up 9%; Meta Critical expects more increases."
    pipe, aid = _run(
        tmp_path, [text],
        [claim("c1", "b001", "DRAM prices up 9%", "DRAM prices up 9%", value=9, value_text="9%",
               unit="%")],
        mentions=[mention("Meta Critical", "b001", "Meta Critical data show DRAM prices up 9%",
                          role="data_source", direction="neutral", ticker="NVDA"),
                  mention("Meta Critical", "b001", "Meta Critical expects more increases",
                          entity_type="private_company", role="context", direction="neutral")])
    assert [c.claim_id for c in _claims(pipe, aid)]  # the article was applied, not rolled back
    rows = pipe.store.conn.execute(
        "SELECT resolution_id, payload FROM security_resolutions").fetchall()
    assert len(rows) == 2 and len({r[0] for r in rows}) == 2
    from vinci.theme_intelligence.schemas import SecurityResolution
    again = SecurityResolution.model_validate_json(rows[0][1])
    assert pipe.store.add_resolution(again) is False  # identical content: the same record
