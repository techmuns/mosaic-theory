"""RG-D8 and RG-D19 (TeamNostra fix request 2): a transcript driver row carries the FACT code read
from its quote, checked against the model's value, and a LOCATOR — so the page can carry the fact
without the quote.

Transcript text is licensed and never committed, so the extraction pins run on INVENTED calls laid
out as `ciq_sheets.transcript_for_synthesis` writes them, through the real
`extract_transcript_drivers` with a fake model. TeamNostra's three reproductions (document 14,
G-D8) are rebuilt here in their own shapes; each FAILED on 6fbbb4a2, where the row was kept with no
status. The corpus pins read every committed transcript row and assert only what the check
guarantees by construction, or a mutation of the row's own quote — never a classifier's verdict on
a model-written value, which rewords on every re-assembly (CLAUDE.md TEST-LAYER RULE).
"""

from __future__ import annotations

import json
import typing
from pathlib import Path

import pytest

from vinci.dossier import driver_extract as dx
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.evals import variants
from vinci.graph.llm import LlmClient

ROOT = Path(__file__).resolve().parents[1]

_Q3 = "Acme, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf"
_Q2 = "Acme, Inc., Q2 2026 Earnings Call, May 05, 2026.rtf"
#: Two calls, each with CIQ's speaker blocks (a name line and a title line in their own paragraph).
_CALLS = (
    f"--- {_Q3} ---\n"
    "hand the call over to Jane.\n \n"
    "Jane  Roe \nHead of Investor Relations \n\n"
    "Good morning and welcome.\n \n"
    "Paul A. Smith \nChief Financial Officer \n\n"
    "Thanks, Jane. Widget shipments were down 7% in the quarter, as we expected.\n \n"
    "Average selling price rose 7% effective March 1 across the fleet. We now serve more than "
    "175 million households. Lower list pricing reduced year-over-year revenue growth by "
    "approximately 4%.\n\n"
    f"--- {_Q2} ---\n"
    "Paul A. Smith \nChief Financial Officer \n\n"
    "Membership was relatively flat on a constant currency basis. We gained 5 points of share "
    "in widgets, more than any other top 5 brand.\n \n"
    "Revenue in Asia increased 6%, Europe 23% and Africa decreased 23%. It's in the 20 to 40 "
    "basis point range."
)
_DOWN_7 = "Widget shipments were down 7% in the quarter, as we expected."


class _Drivers(LlmClient):
    """The model's reply, fixed — the validator is what is under test."""

    def __init__(self, *rows: dict[str, str]) -> None:
        self._rows = list(rows)

    @property
    def model(self) -> str:
        return "fake-drivers"

    def extract(  # type: ignore[override]
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        return {"drivers": self._rows}


def _row(quote: str, value: str, metric: str = "widget shipments",
         kind: str = "leading_indicator") -> dict[str, str]:
    return {"kind": kind, "metric": metric, "period": "", "value": value, "quote": quote}


def _one(quote: str, value: str, metric: str = "widget shipments",
         kind: str = "leading_indicator") -> tuple[ds.OperatingDriver, list[str]]:
    rows, flags, _ = dx.extract_transcript_drivers(
        _CALLS, llm=_Drivers(_row(quote, value, metric, kind)), ticker="ACME", name="Acme",
        transcript_sha256={_Q3: "a" * 64, _Q2: "b" * 64})
    (r,) = rows
    return r, flags


# --- RG-D8: TeamNostra's three reproductions, each in its own shape -------------------------------

def test_a_value_whose_direction_its_quote_contradicts_reads_unknown() -> None:
    """G-D8 (1): "up 7%" read off "…were down 7%…" was KEPT on 6fbbb4a2, and reached the synthesis
    as a validated fact. Kept now as a located statement — with no figure, and a flag."""
    r, flags = _one(_DOWN_7, "up 7%")
    assert r.value_status == "unknown"
    assert r.figures == []
    assert r.unknown_reason is not None and "up" in r.unknown_reason
    assert any("Tier-B value UNKNOWN" in f for f in flags), flags


def test_the_same_figure_in_its_quotes_own_direction_is_verified_and_read_from_the_quote() -> None:
    """The control beside it: the figure, its unit and its change are the QUOTE's, not the
    value's — a value that leaves the change off still carries the quote's."""
    for value in ("down 7%", "7%"):
        r, flags = _one(_DOWN_7, value)
        assert r.value_status == "verified" and r.unknown_reason is None, value
        assert r.figures == [ds.DriverFigure(value=7.0, unit="%", change="down")], value
        assert flags == [], value


def test_a_value_with_no_figure_is_qualitative_only_when_it_is_its_quotes_words() -> None:
    """G-D8 (2): "price increase taken", no figure, was kept — a value with no number traces
    vacuously. It is not the quote's words, so it is UNKNOWN; "relatively flat" is."""
    quote = "Membership was relatively flat on a constant currency basis."
    r, _ = _one(quote, "relatively flat", metric="membership")
    assert (r.value_status, r.figures) == ("qualitative", [])
    r, flags = _one(quote, "membership growth paused", metric="membership")
    assert r.value_status == "unknown" and r.figures == []
    assert any("Tier-B value UNKNOWN" in f for f in flags)


@pytest.mark.parametrize("quote", ["500", "It's in the 20 to 40 basis point range."])
def test_a_quote_that_names_nothing_of_its_metric_reads_unknown(quote: str) -> None:
    """G-D8 (3): a quote that is only "500" was kept as a figure of any metric. The second shape
    is a committed one (a pronoun-led answer in Q&A): the figure is real, the label is not
    checkable from the quote."""
    slice_text = f"--- {_Q3} ---\n{quote}"
    value = "500" if quote == "500" else "20 to 40 basis point range"
    rows, _, _ = dx.extract_transcript_drivers(
        slice_text, llm=_Drivers(_row(quote, value, metric="excess capacity margin impact")),
        ticker="ACME", name="Acme")
    (r,) = rows
    assert r.value_status == "unknown" and r.figures == []
    assert "does not name the metric" in (r.unknown_reason or "")


def test_an_acronym_names_its_metric_either_way() -> None:
    """A loose check must not refuse an abbreviation: "ASP" is "Average selling price"."""
    quote = "Average selling price rose 7% effective March 1 across the fleet."
    assert dx.names_metric("ASP", quote)
    assert dx.names_metric("average unit retail", "AUR increased 3%.")
    assert not dx.names_metric("ASP", "Membership was relatively flat.")


@pytest.mark.xfail(strict=True, reason="RG-D8's binding half is NOT built: a clause-binding rule "
                   "misfired on 6 of the 6 committed rows it fired on (record 2026-11-10-driver-"
                   "facts-not-quotes.md §3). This reds when a rule that holds on the corpus lands.")
def test_a_metric_named_in_another_clause_than_its_figure_reads_unknown() -> None:
    """TeamNostra's third case: metric "shipments", value "500 units", quote "Orders reached 500
    units, while shipments were 320 units". The quote names the metric, so the row passes."""
    quote = "Orders reached 500 units, while shipments were 320 units."
    assert dx.check_fact("shipments", "500 units", quote).status == "unknown"


# --- what the figure carries, read from the quote -------------------------------------------------

def test_a_bound_word_is_carried_so_a_lower_bound_is_never_the_value() -> None:
    quote = "We now serve more than 175 million households."
    f = dx.check_fact("households served", "175 million households", quote)
    assert f.figures == (ds.DriverFigure(value=175.0, scale="e6", qualifier="at_least"),)


def test_a_by_figure_reads_its_verb_never_the_noun_beside_it() -> None:
    """MCK's committed shape: the nearest direction word is the NOUN "growth" — reading it said up
    until a corpus mutation caught it. The verb "reduced" says down."""
    quote = ("Lower list pricing reduced year-over-year revenue growth by approximately 4%.")
    (fig,) = dx.check_fact("revenue growth", "approximately 4%", quote).figures
    assert (fig.change, fig.qualifier) == ("down", "approximately")
    assert dx.check_fact("revenue growth", "raised revenue growth by 4%", quote).status == "unknown"


def test_judgment_words_and_noun_lookalikes_carry_no_change() -> None:
    """Churn that "improved" fell, so "improved" is not a direction; an "accelerator" is a chip
    (AMZN's committed row read it as a rise before the lexicon listed inflections)."""
    for quote, metric in (("Churn improved 2 points year over year.", "churn"),
                          ("We install an AI accelerator about every 14 seconds.", "accelerator")):
        (fig,) = dx.check_fact(metric, quote.split(" ", 2)[2], quote).figures
        assert fig.change is None, quote


def test_a_value_stitched_with_an_ellipsis_cannot_hide_its_direction() -> None:
    """Two committed values join words with "..."; a flipped change word across it was missed by
    the corpus mutation until the value's own change was read across the elision."""
    quote = "Today, we are increasing our store potential by 500 stores to 7,500 stores."
    assert dx.check_fact("store potential", "increasing ... by 500 stores", quote).status == \
        "verified"
    assert dx.check_fact("store potential", "decreasing ... by 500 stores", quote).status == \
        "unknown"


def test_a_number_said_twice_is_read_at_its_place_or_refused() -> None:
    """When the value IS the quote's words, each figure is the one at its place (NKE's committed
    "top 5 brand" beside "5 points"). When it is not, a number the quote reads two ways is
    ambiguous (AORT's committed "Europe 23% … decreased 23%")."""
    nke = "We gained 5 points of share in widgets, more than any other top 5 brand."
    f = dx.check_fact("widget share", "gained 5 points of share in widgets, more than any other "
                      "top 5 brand", nke)
    assert f.status == "verified"
    assert [g.change for g in f.figures] == ["up", None]
    aort = "Revenue in Asia increased 6%, Europe 23% and Africa decreased 23%."
    assert dx.check_fact("Europe revenue", "23%", aort).status == "unknown"


def test_a_hyphenated_range_is_two_figures_never_a_fall() -> None:
    """FAILED before the review fix: "20-40%" read its second figure as -40 with change "down" and
    published it verified — a range its quote never said was a fall. A printed sign still reads."""
    f = dx.check_fact("margin", "20-40%", "We expect margin in the 20-40% range.")
    assert f.status == "verified"
    assert [(g.value, g.change) for g in f.figures] == [(20.0, None), (40.0, None)]
    (neg,) = dx.check_fact("margin", "-50 bps", "Margin was -50 bps.").figures
    assert (neg.value, neg.change) == (-50.0, "down")


def test_a_change_word_directly_before_the_next_figure_is_that_figures() -> None:
    """FAILED before the review fix: "Revenue of $5 billion up 7%" published the $5 billion as up
    — the "up" is the 7%'s. A word with anything after it stays its own figure's: "24% revenue
    growth and 80 basis points" is growth of the 24%, and "by" carries a fall to its own figure."""
    q = "Revenue of $5 billion up 7% year over year."
    assert [g.change for g in dx.check_fact("revenue", "$5 billion up 7%", q).figures] == \
        [None, "up"]
    wern = "In the second quarter, we delivered 24% revenue growth and 80 basis points of margin."
    (g,) = dx.check_fact("revenue growth", "24% revenue growth", wern).figures
    assert g.change == "up"
    ebitda = "First quarter EBITDA of $36 million decreased by $9 million from the fourth quarter."
    assert [g.change for g in dx.check_fact("EBITDA", "$36 million decreased by $9 million",
                                            ebitda).figures] == [None, "down"]


# --- RG-D19: the locator --------------------------------------------------------------------------

def test_the_locator_names_the_call_paragraph_speaker_and_both_hashes() -> None:
    r, _ = _one(_DOWN_7, "down 7%")
    loc = r.locator
    assert loc is not None
    assert loc.call == _Q3 and loc.transcript_sha256 == "a" * 64
    # paragraphs of the call: 0 hand-over, 1 Jane's block, 2 welcome, 3 Paul's block, 4 the quote
    assert (loc.paragraph, loc.speaker) == (4, "Paul A. Smith")
    assert loc.quote_sha256 == dx.quote_key(_DOWN_7)
    # the key is the containment rule's: a re-wrapped, re-cased quote keys the same passage
    assert dx.quote_key("widget SHIPMENTS were down 7%\nin the quarter,  as we expected.") == \
        dx.quote_key(_DOWN_7)


def test_a_call_with_no_speaker_block_before_the_quote_names_none() -> None:
    slice_text = f"--- {_Q3} ---\n{_DOWN_7}"
    rows, _, _ = dx.extract_transcript_drivers(slice_text, llm=_Drivers(_row(_DOWN_7, "down 7%")),
                                               ticker="ACME", name="Acme")
    (r,) = rows
    assert r.locator is not None
    assert (r.locator.paragraph, r.locator.speaker, r.locator.transcript_sha256) == (0, None, None)


def test_a_quote_cited_to_no_call_has_no_locator() -> None:
    """A sentence said on both calls, with no period naming one: cited to no call (G-V1), and so
    located nowhere — never at the first match."""
    said = "Widget shipments were down 7% in the quarter, as we expected."
    slice_text = f"--- {_Q3} ---\n{said}\n\n--- {_Q2} ---\n{said}"
    rows, _, _ = dx.extract_transcript_drivers(slice_text, llm=_Drivers(_row(said, "down 7%")),
                                               ticker="ACME", name="Acme")
    assert rows[0].source_ref == "CIQ transcript" and rows[0].locator is None


def test_the_locator_states_no_number_to_the_synthesis_trace() -> None:
    """FAILED before the review fix: the trace walked the locator as a fact, so its sha256 hex
    digit runs and paragraph index became numbers the cited call "states" — a claim writing any of
    them traced silently instead of earning its verify-against-the-call note."""
    r, _ = _one(_DOWN_7, "down 7%")
    assert r.locator is not None and r.locator.paragraph == 4

    def stated(row: ds.OperatingDriver) -> list[float]:
        return sorted(syn._values_by_ref(_layer_with(row))[syn.comparison_key(row.source_ref)]
                      .values)
    assert stated(r) == stated(r.model_copy(update={"locator": None}))


def test_an_unknown_rows_reason_states_no_number_to_the_synthesis_trace() -> None:
    """The reason may print a count that is no figure of the row ("its quote states 23 2 times");
    the trace never reads it as one."""
    aort = "Revenue in Asia increased 6%, Europe 23% and Africa decreased 23%."
    rows, _, _ = dx.extract_transcript_drivers(
        f"--- {_Q3} ---\n{aort}", llm=_Drivers(_row(aort, "23%", metric="Europe revenue")),
        ticker="ACME", name="Acme")
    (r,) = rows
    assert r.value_status == "unknown" and "2 times" in (r.unknown_reason or "")

    def stated(row: ds.OperatingDriver) -> list[float]:
        return sorted(syn._values_by_ref(_layer_with(row))[syn.comparison_key(row.source_ref)]
                      .values)
    assert stated(r) == stated(r.model_copy(update={"unknown_reason": None}))


def test_transcript_sha256s_hashes_each_files_bytes(tmp_path: Path) -> None:
    p = tmp_path / _Q3
    p.write_bytes(b"call body")
    import hashlib
    assert dx.transcript_sha256s([p]) == {_Q3: hashlib.sha256(b"call body").hexdigest()}


# --- the synthesis reads an unverified row as UNKNOWN, and every other row as before --------------

def _layer_with(*rows: ds.OperatingDriver) -> ds.MechanicalLayer:
    from tests.test_dossier import _minimal_mech
    return _minimal_mech().model_copy(update={
        "operating_drivers": ds.OperatingDriversExtract(rows=list(rows))})


def test_an_unknown_rows_value_reaches_the_synthesis_as_unknown_in_the_facts_and_the_digest(
) -> None:
    """FAILED on 6fbbb4a2: the digest printed "up 7%" under "validated, cited facts"."""
    bad, _ = _one(_DOWN_7, "up 7%")
    good, _ = _one(_DOWN_7, "down 7%")
    od = ds.OperatingDriversExtract(rows=[bad, good])
    digest = syn._operating_drivers_digest(od)
    assert "widget shipments: up 7%" not in digest
    assert "widget shipments: UNKNOWN — not verified against its quote" in digest
    assert "widget shipments: down 7%" in digest
    dumped = _layer_with(bad, good).model_dump(exclude=syn.NOT_SENT)
    syn._mark_unverified_drivers(dumped, od)
    values = [r["value"] for r in dumped["operating_drivers"]["rows"]]
    assert values[0].startswith("UNKNOWN — ") and values[1] == "down 7%"


def test_the_prompt_keeps_every_driver_rows_shape() -> None:
    """The new fields are the page's: the facts dump sends each row's earlier fields, in their
    earlier order, and nothing else — so a verified row's bytes do not move."""
    good, _ = _one(_DOWN_7, "down 7%")
    (row,) = _layer_with(good).model_dump(exclude=syn.NOT_SENT)["operating_drivers"]["rows"]
    assert list(row) == ["kind", "metric", "period", "value", "value_num", "unit", "verbatim",
                         "following_context", "source_ref", "tier"]


def _committed() -> list[tuple[str, dict[str, typing.Any]]]:
    return [(p.parent.name, json.loads(p.read_text()))
            for p in sorted((ROOT / "data/dossiers").glob("*/dossier.json"))]


def test_on_every_committed_page_the_check_moves_only_unverified_rows_values() -> None:
    """END TO END, on the real committed JSON: the layer, the transform the panel measures with
    (`variants.driver_facts`), and the facts dump the synthesis is sent. The only bytes that move
    are the values of the rows the check marks unknown, each now reading UNKNOWN. Which rows those
    are is not pinned — that is a classifier on model-written values (TEST-LAYER RULE)."""
    moved = pages = 0
    for ticker, page in _committed():
        mech = ds.MechanicalLayer.model_validate(page["mechanical"])
        after = variants.driver_facts(mech, variants.Context(page=page))
        base = mech.model_dump(exclude=syn.NOT_SENT)
        cand = after.model_dump(exclude=syn.NOT_SENT)
        syn._mark_unverified_drivers(base, mech.operating_drivers)
        syn._mark_unverified_drivers(cand, after.operating_drivers)
        assert {k: v for k, v in base.items() if k != "operating_drivers"} == \
            {k: v for k, v in cand.items() if k != "operating_drivers"}, ticker
        b_rows = (base.get("operating_drivers") or {}).get("rows") or []
        c_rows = (cand.get("operating_drivers") or {}).get("rows") or []
        assert len(b_rows) == len(c_rows), ticker
        unknown = [r for r in (after.operating_drivers.rows if after.operating_drivers else [])
                   if r.value_status == "unknown"]
        diff = [(b, c) for b, c in zip(b_rows, c_rows, strict=True) if b != c]
        assert len(diff) == len(unknown), ticker
        for b, c in diff:
            assert {k for k in b if b[k] != c[k]} == {"value"}, ticker
            assert c["value"].startswith("UNKNOWN — "), ticker
        moved += len(diff)
        pages += bool(b_rows)
    assert pages >= 20 and moved >= 1, (pages, moved)


# --- the transform the panel measures with --------------------------------------------------------

def test_the_transform_writes_what_the_extractor_writes_and_only_the_fact() -> None:
    """RUNBOOKS §n step 2: the transform's fields equal what the candidate's extractor writes for
    the same row — here, every committed transcript row re-extracted from a call holding just its
    own quote (in memory: the text is the committed row's, never written anywhere)."""
    checked = 0
    for ticker, page in _committed():
        mech = ds.MechanicalLayer.model_validate(page["mechanical"])
        after = variants.driver_facts(mech, variants.Context(page=page))
        for r0, r1 in zip(mech.operating_drivers.rows if mech.operating_drivers else [],
                          after.operating_drivers.rows if after.operating_drivers else [],
                          strict=True):
            if r0.tier != "llm-fenced":
                assert r1 == r0, ticker
                continue
            assert r1.model_dump(exclude={"figures", "value_status", "unknown_reason"}) == \
                r0.model_dump(exclude={"figures", "value_status", "unknown_reason"}), ticker
            if checked % 9 == 0:   # one in nine, all fields, through the real extractor
                rows, _, _ = dx.extract_transcript_drivers(
                    f"--- {_Q3} ---\n{r0.verbatim}", ticker=ticker, name=ticker,
                    llm=_Drivers({"kind": r0.kind.value, "metric": r0.metric, "period": "",
                                  "value": r0.value, "quote": r0.verbatim}))
                (x,) = rows
                assert (x.figures, x.value_status, x.unknown_reason) == \
                    (r1.figures, r1.value_status, r1.unknown_reason), (ticker, r0.metric)
            checked += 1
    assert checked > 500


def test_the_transform_is_the_identity_without_the_check_and_refuses_a_fact_it_does_not_make(
        monkeypatch: pytest.MonkeyPatch) -> None:
    good, _ = _one(_DOWN_7, "down 7%")
    mech = _layer_with(good.model_copy(update={"figures": None, "value_status": None,
                                                "unknown_reason": None}))
    ctx = variants.Context(page={"ticker": "ACME"})
    assert variants.driver_facts(mech, ctx).operating_drivers == ds.OperatingDriversExtract(
        rows=[good])
    forged = _layer_with(good.model_copy(update={"value_status": "qualitative"}))
    with pytest.raises(variants.TransformError):
        variants.driver_facts(forged, ctx)
    monkeypatch.delattr(dx, "check_fact")
    assert variants.driver_facts(mech, ctx) is mech


# --- CORPUS BEFORE SYNTHETIC: the direction check bites on the committed quotes -------------------

def _committed_transcript_rows() -> list[dict[str, typing.Any]]:
    return [r for _, page in _committed()
            for r in (page["mechanical"].get("operating_drivers") or {}).get("rows", [])
            if r.get("tier") == "llm-fenced"]


def test_every_committed_figure_with_a_change_refuses_the_opposite_claim() -> None:
    """The committed corpus holds NO row whose value contradicts its quote (881 rows, main
    6fbbb4a2), so the check is shown to bite by mutation: for every committed row whose quote
    prints a change beside a figure, TeamNostra's shape — the opposite word and that figure, as
    the quote prints it — read against the REAL quote is UNKNOWN. What varies is the quote, which
    is transcript text, not a model's wording."""
    rows = _committed_transcript_rows()
    assert len(rows) > 500, "the committed corpus no longer carries transcript rows"
    bitten = 0
    for r in rows:
        fact = dx.check_fact(r["metric"], r["value"], r["verbatim"])
        figs = dx._figures(r["verbatim"])
        for g in fact.figures:
            if g.change is None:
                continue
            q = next(x for x in figs if (x.value, x.scale, x.unit) == (g.value, g.scale, g.unit))
            claim = ("down " if g.change == "up" else "up ") + (g.currency or "") + \
                r["verbatim"][q.start:q.end]
            assert dx.check_fact(r["metric"], claim, r["verbatim"]).status == "unknown", claim
            bitten += 1
            break
    assert bitten > 200


def test_every_committed_rows_figures_are_its_quotes() -> None:
    """By construction, checked on the corpus: each figure a row carries is a figure its quote
    prints, with the quote's own axes — the value is never the source of a figure."""
    for r in _committed_transcript_rows():
        quote_figs = {(f.value, f.currency, f.scale, f.unit) for f in dx._figures(r["verbatim"])}
        for g in dx.check_fact(r["metric"], r["value"], r["verbatim"]).figures:
            assert (g.value, g.currency, g.scale, g.unit) in quote_figs, r["metric"]
