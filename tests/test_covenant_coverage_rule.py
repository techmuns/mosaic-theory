"""The covenant phase's COVERAGE RULE (STATE row 63, 2026-11-16; operator: "Order now, coverage next
(Recommended)").

Until this rule, `extract_covenant_terms` sent at most four exhibits per page, the first four debt
contracts its round-robin reached. So a page spent calls on documents that govern nothing and
dropped live ones past them:
- VRRM sent Amendment No. 4 to a revolving credit agreement that its own 2025-10-17 amended and
  restated revolver had replaced, and any term it returned would have printed as a separate, stale
  "REVOLVING CREDIT AGREEMENT" group;
- AMZN sent its 2022 364-day agreement, which its 2023 five-year agreement terminated, and left its
  June 2026 term loan agreement past the bound.

Now every target is read first, and every debt contract is sent unless:
- a located exhibit filed later displaces the agreement it is or amends: it names that agreement by
  name and date, in a recital or a definition, and amends and restates it, substitutes for it,
  supersedes it, or states it terminated (`superseded`, citing that exhibit and its words); or
- its title states notes whose maturity year is before the page's reference date, and the CIQ panel
  carries no instrument maturing that year (`terminated`).
Anything else is READ, however old it looks. A purchase agreement is still sent after every other
debt contract, and a guard of `_MAX_EXHIBITS` (10) calls stops only a runaway, loudly.

THE FIXTURES ARE THE REAL TYPE (`tests/fixtures/covenant_coverage_rule/`, see its README). Each is
one committed page's `capital_structure`, unmodified, and the text of every exhibit its pointer rows
target, read from the EDGAR cache and cut to the head plus the clauses the reader binds and
displaces with. Each cut reads exactly as the full exhibit reads. The loop runs unmodified, stubbed
only at the fetch and the model.
"""

from __future__ import annotations

import json
import pathlib
import re
import typing

import pytest

from tests.test_covenant_exhibit_outcomes import _committed, _md_line, _web_line
from vinci.dossier import covenant_extract as ce
from vinci.dossier.schemas import CapitalStructure, CovenantExhibitOutcome

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "covenant_coverage_rule"


def _fixture(ticker: str) -> dict[str, typing.Any]:
    page: dict[str, typing.Any] = json.loads((FIX / f"{ticker}.json").read_text())
    return page


class _Http:
    """Serves each target's cut text by its accession and filename; a None is a failed fetch."""

    def __init__(self, texts: dict[str, str | None]) -> None:
        self.texts = {(k.split(" · ")[0].replace("-", ""), k.split(" · ")[1]): v
                      for k, v in texts.items()}

    def get_text(self, url: str, **_: typing.Any) -> str:
        acc, doc = url.rsplit("/", 2)[1:]
        body = self.texts.get((acc, doc))
        if body is None:
            raise OSError(f"stub: {url} unavailable")
        return body


class _Llm:
    """The model boundary: records each exhibit it is sent, and answers one name-only row."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        m = re.search(r"Exhibit: \S+ (\d{10}-\d{2}-\d{6} · \S+?)\. Extract", user)
        assert m is not None, user[:200]
        self.sent.append(m.group(1))
        return {"terms": [{"name": "Maturity date", "present": False}]}


class _Run(typing.NamedTuple):
    sent: list[str]  # "<accession> · <filename>", in the order sent
    by: dict[str, CovenantExhibitOutcome]  # "<accession> · <filename>" → its outcome
    flags: list[str]
    outcomes: list[CovenantExhibitOutcome]


def _run(ticker: str, *, texts: dict[str, str | None] | None = None,
         cs: CapitalStructure | None = None) -> _Run:
    fx = _fixture(ticker)
    layer = cs or CapitalStructure.model_validate(fx["capital_structure"])
    llm = _Llm()
    _rows, _summary, flags, _log, outcomes = ce.extract_covenant_terms(
        layer, llm=llm, http=_Http(texts or fx["texts"]),  # type: ignore[arg-type]
        cik=fx["cik"], ticker=ticker, name=fx["name"])
    assert outcomes is not None
    got = list(outcomes.value or [])
    assert layer.covenant_pointer_rows is not None
    targets = ce._core_agreement_exhibits(list(layer.covenant_pointer_rows.value or []))
    assert [(o.accession, o.filename) for o in got] == [(r.accession, f) for r, f in targets], \
        "one outcome per target, in the targets' order"
    return _Run(llm.sent, {f"{o.accession} · {o.filename}": o for o in got}, flags, got)


def _by(o: CovenantExhibitOutcome) -> str:
    """The superseding exhibit, as the line prints it, from its two structured values."""
    return f"{o.superseded_by} · {o.superseded_by_filename}"


def _edited(ticker: str, key: str, old: str, new: str) -> dict[str, str | None]:
    """The fixture's texts with one real clause of one exhibit replaced (a DERIVED negative)."""
    texts = dict(_fixture(ticker)["texts"])
    body = texts[key]
    assert body is not None and old in body, "the derivation must apply to the real clause"
    texts[key] = body.replace(old, new, 1)
    return texts


VRRM_AR = "0001193125-25-242530 · vrrm-ex10_1.htm"
VRRM_AMD4 = "0000950170-25-072679 · vrrm-ex10_1.htm"
VRRM_TL = "0001564590-21-015880 · vrrm-ex101_62.htm"


# --- the brief's five pins ------------------------------------------------------------------------


def test_vrrm_amendment_no_4_is_superseded_by_its_amended_and_restated_revolver() -> None:
    """(+) VRRM. Amendment No. 4 (filed 2025-05-15) amends the "Revolving Credit Agreement, dated as
    of March 1, 2018". The A&R revolver (filed 2025-10-17) names that agreement in its recital
    ("that certain Revolving Credit Agreement, dated as of the Original Closing Date", the date
    resolved by its own definition, "“Original Closing Date” shall mean March 1, 2018") and agrees
    "to amend and restate the Original ABL Credit Agreement". So the amendment is not sent, and its
    outcome cites the A&R and its words. At main it was sent, and any term it returned would have
    printed as a stale, separate group."""
    r = _run("VRRM")
    o = r.by[VRRM_AMD4]
    assert o.outcome == "superseded", o
    assert (o.superseded_by, o.superseded_by_filename) == tuple(VRRM_AR.split(" · "))
    assert o.evidence is not None
    assert "“amend and restate the Original ABL Credit Agreement”" in o.evidence
    assert "REVOLVING CREDIT AGREEMENT dated 2018-03-01 that this exhibit amends" in o.evidence
    assert VRRM_AMD4 not in r.sent
    assert r.sent == [VRRM_AR, VRRM_TL], "the A&R revolver and the term loan's restatement"


def test_a_live_amendment_chain_stays_sent_cnxc_receivables_financing() -> None:
    """(+ / −) CNXC. Its 2025 amendment and restatement supersedes its 2023 one ("the provisions of
    the Existing Credit Agreement shall be superseded"), which superseded the 2020 credit agreement
    its 2021 first amendment amends. Its receivables financing agreement's third and fourth
    amendments amend an agreement no later exhibit names, so that chain stays sent: a rule reading
    "a later restatement supersedes every earlier amendment" would drop it."""
    r = _run("CNXC")
    rfa3 = "0001803599-24-000117 · exhibit101-thirdamendmentt.htm"
    rfa4 = "0001803599-25-000014 · exhibit101-fourthamendment.htm"
    ar25 = "0001803599-25-000111 · exhibit101041125.htm"
    ar23 = "0001803599-23-000107 · form8-k04x26x23exhibit101.htm"
    am21 = "0001803599-21-000215 · exhibit101122721.htm"
    assert r.sent == [ar25, rfa3, rfa4], r.sent
    assert (r.by[ar23].outcome, _by(r.by[ar23])) == ("superseded", ar25)
    assert (r.by[am21].outcome, _by(r.by[am21])) == ("superseded", ar23)
    assert "CREDIT AGREEMENT dated 2020-10-16 that this exhibit amends" in (r.by[am21].evidence
                                                                          or "")


def test_a_page_with_more_than_four_live_contracts_sends_them_all_burl() -> None:
    """(+) BURL. Six debt contracts, none displaced by a later located exhibit's words: its ABL
    agreement's four amendments, its term loan's 2014 Amendment No. 4 and a 2020 security
    agreement. All six are sent, where main sent four and left two past the bound. The guard is
    not reached, so no exhibit is cost bound and no flag says so."""
    r = _run("BURL")
    assert len(r.sent) == 6 > 4, r.sent
    assert "0001193125-22-200058 · d393601dex101.htm" in r.sent
    assert "0001193125-14-313404 · d772516dex101.htm" in r.sent
    assert not any(o.outcome == "cost_bound" for o in r.outcomes)
    assert not any("RUNAWAY GUARD" in f for f in r.flags)


def test_the_runaway_guard_fires_loudly_on_an_overflow() -> None:
    """(+) SYNTHETIC OVERFLOW from BURL's real exhibits: its pointer rows twice over, the copies
    under synthetic accessions serving the same real texts, so 12 live debt contracts. The guard
    sends 10 and marks the 2 past it cost bound, each with a RUNAWAY GUARD flag that names the
    count and the guard. At main the cap of four chose, quietly."""
    fx = _fixture("BURL")
    cs = CapitalStructure.model_validate(fx["capital_structure"])
    rows = list(cs.covenant_pointer_rows.value or []) if cs.covenant_pointer_rows else []
    texts = dict(fx["texts"])
    copies = []
    for n, row in enumerate(r for r in rows if r.accession):
        acc = f"9999999999-26-{n:06d}"
        copies.append(row.model_copy(update={"accession": acc, "family": f"copy of {row.family}"}))
        for key, body in fx["texts"].items():
            if key.startswith(row.accession + " · "):
                texts[f"{acc} · {key.split(' · ')[1]}"] = body
    assert cs.covenant_pointer_rows is not None
    doubled = cs.model_copy(update={"covenant_pointer_rows": cs.covenant_pointer_rows.model_copy(
        update={"value": rows + copies})})
    r = _run("BURL", texts=texts, cs=doubled)
    assert len(r.sent) == ce._MAX_EXHIBITS == 10
    past = [o for o in r.outcomes if o.outcome == "cost_bound"]
    assert len(past) == 2, past
    guard = [f for f in r.flags if f.startswith("(E5) RUNAWAY GUARD")]
    assert len(guard) == 2, r.flags
    assert all("12 live debt contracts" in f and "the guard is 10 calls" in f for f in guard)


def test_an_exhibit_the_words_cannot_classify_is_read_amzn() -> None:
    """(+ / −) AMZN. Its 2014 credit agreement is named by no later located exhibit (its 2018
    restatement names a May 20, 2016 agreement), so nothing shows it displaced and it is READ,
    never silently skipped. Its 2022 364-day agreement is superseded by the 2023 five-year
    agreement, whose definitions bind it ("“Existing 364-Day Credit Agreement” means that certain
    364-Day Revolving Credit Agreement dated as of November 18, 2022") and whose conditions say
    "all commitments thereunder shall have been terminated". Its 2018 restatement is superseded by
    the 2020 one. So its June 2026 term loan agreement, past the bound at main, is sent."""
    r = _run("AMZN")
    assert r.sent == ["0001104659-23-113444 · tm2329405d1_ex10-1.htm",
                      "0001193125-20-176528 · d948849dex101.htm",
                      "0001018724-14-000042 · amzn2014september5-ex101.htm",
                      "0001104659-26-072140 · tm2613616d4_ex10-1.htm"], r.sent
    o22 = r.by["0001193125-22-289041 · d413765dex101.htm"]
    assert (o22.outcome, _by(o22)) == (
        "superseded", "0001104659-23-113444 · tm2329405d1_ex10-1.htm")
    assert "364-DAY REVOLVING CREDIT AGREEMENT dated 2022-11-18 that this exhibit is" in (
        o22.evidence or "")
    assert _by(r.by["0001193125-18-139368 · d574720dex101.htm"]) == \
        "0001193125-20-176528 · d948849dex101.htm"


# --- terminated: matured notes --------------------------------------------------------------------

NFLX_PA14 = "0001193125-14-037000 · d671121dex101.htm"
NFLX_PA18 = "0001193125-18-134734 · d567970dex101.htm"


def test_matured_notes_read_terminated_and_a_live_purchase_agreement_goes_last_nflx() -> None:
    """(+) NFLX. Its 2014 purchase agreement's title states notes due 2024, before the page's
    reference date, and its CIQ panel carries no instrument maturing in 2024: terminated, not sent.
    Its 2018 purchase agreement (notes due 2028, on the panel) is sent, after every other debt
    contract (operator, 2026-11-16)."""
    r = _run("NFLX")
    o = r.by[NFLX_PA14]
    assert o.outcome == "terminated" and o.superseded_by is None
    assert o.superseded_by_filename is None
    assert o.evidence is not None and "notes due 2024" in o.evidence
    assert "the CIQ panel carries no instrument maturing in 2024" in o.evidence
    assert r.sent[-1] == NFLX_PA18 and NFLX_PA14 not in r.sent
    assert len(r.sent) == 5, r.sent


def test_a_panel_that_still_carries_the_year_disagrees_and_the_notes_are_read() -> None:
    """(−) DERIVED from NFLX's real panel: one more instrument with principal, maturing in 2024.
    The title and the panel then disagree, so the 2014 purchase agreement is read, not skipped."""
    fx = _fixture("NFLX")
    cs = CapitalStructure.model_validate(fx["capital_structure"])
    insts = list(cs.instruments.value or [])
    extra = insts[0].model_copy(update={"description": "5.750% Senior Notes",
                                        "maturity_date": "2024-03-01", "principal_musd": 400.0})
    cs = cs.model_copy(update={"instruments": cs.instruments.model_copy(
        update={"value": [*insts, extra]})})
    r = _run("NFLX", cs=cs)
    assert r.by[NFLX_PA14].outcome != "terminated"
    assert NFLX_PA14 in r.sent


def test_a_panel_row_of_unknown_principal_in_the_year_is_not_an_absent_one() -> None:
    """(−) DERIVED from NFLX's real panel: one more instrument maturing in 2024 whose principal the
    panel does not state. Unknown is not absent, so the 2014 purchase agreement is read (review of
    the coverage rule: `principal_musd` None read as "the panel carries no instrument")."""
    fx = _fixture("NFLX")
    cs = CapitalStructure.model_validate(fx["capital_structure"])
    insts = list(cs.instruments.value or [])
    extra = insts[0].model_copy(update={"description": "5.750% Senior Notes",
                                        "maturity_date": "2024-03-01", "principal_musd": None})
    cs = cs.model_copy(update={"instruments": cs.instruments.model_copy(
        update={"value": [*insts, extra]})})
    r = _run("NFLX", cs=cs)
    assert r.by[NFLX_PA14].outcome != "terminated"
    assert NFLX_PA14 in r.sent


def test_a_title_with_a_live_tranche_is_not_terminated() -> None:
    """(−) DERIVED from NFLX's real 2014 purchase agreement head, given a second tranche due 2028
    (a year NFLX's panel carries). Only one of its notes has matured, so the agreement is read
    (review of the coverage rule: only the title's FIRST "NOTES DUE" year was checked)."""
    texts = _edited("NFLX", NFLX_PA14, "5.750% Senior Notes due 2024 Purchase Agreement",
                    "5.750% Senior Notes due 2024 and 2028 Purchase Agreement")
    title = ce.agreement_title(texts[NFLX_PA14] or "")
    assert title == "SENIOR NOTES DUE 2024 AND 2028 PURCHASE AGREEMENT", title
    r = _run("NFLX", texts=texts)
    assert r.by[NFLX_PA14].outcome != "terminated", r.by[NFLX_PA14]
    assert NFLX_PA14 in r.sent


# --- the chains the reader reads ------------------------------------------------------------------


def test_each_years_364_day_agreement_terminates_the_last_nke() -> None:
    """(+) NKE. Each March, a new 364-day agreement states the last one "has been, or concurrently
    with the effectiveness of this Agreement will be, terminated", naming it by its date. Only the
    2026 agreement is sent; the 2023, 2024 and 2025 ones are each superseded by the next."""
    r = _run("NKE")
    assert r.sent == ["0000320187-26-000020 · a364-daycreditagreementxni.htm"], r.sent
    chain = [("0000320187-25-000008", "0000320187-26-000020"),
             ("0000320187-24-000009", "0000320187-25-000008"),
             ("0000320187-23-000006", "0000320187-24-000009")]
    for old, new in chain:
        [o] = [o for k, o in r.by.items() if k.startswith(old)]
        assert o.outcome == "superseded" and o.superseded_by == new, o


def test_a_collective_definition_supersedes_both_its_agreements_tjx() -> None:
    """(+) TJX. Its 2021 agreement defines its "Existing Credit Agreements" as "(x) that certain
    2022 Revolving Credit Agreement, dated as of March 11, 2016 … and (y) that certain 364 Day
    Revolving Credit Agreement" and requires "evidence of termination of the Existing Credit
    Agreements". So the 2020 second amendment to the first and the 2020 364-day agreement are
    superseded."""
    r = _run("TJX")
    for key in ("0001157523-20-000793 · a52222014ex10_1.htm",
                "0000109198-20-000015 · exhibit101364dayrevolv.htm"):
        assert r.by[key].outcome == "superseded", r.by[key]
        assert _by(r.by[key]) == "0001193125-21-202939 · d169110dex101.htm"
    assert len(r.sent) == 2, r.sent


# --- what the reader refuses: each guard on a real clause, derived ------------------------------


def test_a_conditional_termination_displaces_nothing() -> None:
    """(−) DERIVED from TJX's real condition precedent. "upon termination of the Existing Credit
    Agreements" is a condition, not a statement that they ended, so neither 2020 exhibit is
    superseded and both are read."""
    texts = _edited("TJX", "0001193125-21-202939 · d169110dex101.htm",
                    "evidence of termination of the Existing Credit Agreements",
                    "upon termination of the Existing Credit Agreements")
    r = _run("TJX", texts=texts)
    assert not any(o.outcome == "superseded" for o in r.outcomes)
    assert len(r.sent) == 4


def test_a_part_of_the_agreement_displaces_nothing() -> None:
    """(−) DERIVED from NKE's real clause: "Section 2.5.12 of the 2025 Credit Agreement has been …
    terminated" ends a part, not the agreement, so the 2025 agreement is read (`_A_PART_OF`). No
    committed or cached clause has this shape (0 of the 29 displacing reads over the 92 cached
    documents the gate passes); the guard is pinned here."""
    texts = _edited("NKE", "0000320187-26-000020 · a364-daycreditagreementxni.htm",
                    "the 2025 Credit Agreement has been",
                    "Section 2.5.12 of the 2025 Credit Agreement has been")
    r = _run("NKE", texts=texts)
    assert r.by["0000320187-25-000008 · nike-364xdaycreditagreemen.htm"].outcome != "superseded"


def test_something_under_the_agreement_terminated_displaces_nothing() -> None:
    """(−) DERIVED from NKE's real clause: "the Revolving Commitments under the 2025 Credit
    Agreement has been … terminated" ends a tranche's commitments, not the agreement (its other
    loans may stay outstanding), so the 2025 agreement is read (review of the coverage rule: the
    clause's subject was never checked, only `_A_PART_OF`'s part words)."""
    texts = _edited("NKE", "0000320187-26-000020 · a364-daycreditagreementxni.htm",
                    "the 2025 Credit Agreement has been",
                    "the Revolving Commitments under the 2025 Credit Agreement has been")
    r = _run("NKE", texts=texts)
    assert r.by["0000320187-25-000008 · nike-364xdaycreditagreemen.htm"].outcome != "superseded"


def test_a_possessive_displaces_nothing() -> None:
    """(−) DERIVED from VRRM's real recital: "amend and restate the Original ABL Credit Agreement’s
    Schedule 1.1" restates a schedule of it, not it, so Amendment No. 4 is read. No committed or
    cached clause has this shape either."""
    texts = _edited("VRRM", VRRM_AR, "amend and restate the Original ABL Credit Agreement",
                    "amend and restate the Original ABL Credit Agreement’s Schedule 1.1")
    assert _run("VRRM", texts=texts).by[VRRM_AMD4].outcome != "superseded"


def test_an_agreement_named_two_ways_on_the_page_decides_neither() -> None:
    """(−) AMBIGUITY, DERIVED from VRRM's real recital with its name cut to "Credit Agreement".
    VRRM's revolver and its first-lien term loan agreement are both dated March 1, 2018, so
    "Credit Agreement, dated as of the Original Closing Date" fits both: it identifies neither,
    and both the revolver amendment and the term loan restatement are read."""
    texts = _edited("VRRM", VRRM_AR, "that certain Revolving Credit Agreement, dated as of",
                    "that certain Credit Agreement, dated as of")
    r = _run("VRRM", texts=texts)
    assert r.by[VRRM_AMD4].outcome != "superseded" and r.by[VRRM_TL].outcome != "superseded"
    assert VRRM_AMD4 in r.sent and VRRM_TL in r.sent


def test_a_page_with_an_unread_exhibit_supersedes_nothing() -> None:
    """(−) FAIL CLOSED, DERIVED from VRRM's real fixture with its term loan restatement unreadable
    (a failed fetch). That exhibit may be another agreement the A&R's words fit, so no name on the
    page can be shown unambiguous: Amendment No. 4 is read, and a flag says why (review round 0)."""
    texts = dict(_fixture("VRRM")["texts"])
    texts[VRRM_TL] = None
    r = _run("VRRM", texts=texts)
    assert r.by[VRRM_TL].outcome == "fetch_failed"
    assert r.by[VRRM_AMD4].outcome != "superseded" and VRRM_AMD4 in r.sent
    assert any(f.startswith("(E5) coverage: 1 located exhibit(s) could not be read")
               for f in r.flags), r.flags


def test_a_one_word_name_matches_only_itself() -> None:
    """(+ / −) A NAME TAIL IS AT LEAST TWO WORDS. EPAM's restatement names "Credit Agreement, dated
    as of May 24, 2017", which E5 titles by its cover, "REVOLVING CREDIT FACILITY CREDIT AGREEMENT":
    one agreement. A bare "INDENTURE" is not a "FIRST SUPPLEMENTAL INDENTURE" of the same date,
    often signed the same day (derived; review round 0)."""
    day = ce.date(2017, 5, 24)
    assert ce._same_agreement(ce.AgreementKey("CREDIT AGREEMENT", day),
                              ce.AgreementKey("REVOLVING CREDIT FACILITY CREDIT AGREEMENT", day))
    assert not ce._same_agreement(ce.AgreementKey("INDENTURE", day),
                                  ce.AgreementKey("FIRST SUPPLEMENTAL INDENTURE", day))
    assert ce._same_agreement(ce.AgreementKey("INDENTURE", day), ce.AgreementKey("INDENTURE", day))


@pytest.mark.parametrize("filed", ["2025-05-15", ""])
def test_a_later_document_must_be_filed_later(filed: str) -> None:
    """(−) DERIVED from VRRM's real pointer rows, the A&R's filing date set to the amendment's
    (2025-05-15), then blanked. A tied or empty date cannot order two documents (the (X-4) rule of
    `governing_terms`), so the amendment is read."""
    cs = CapitalStructure.model_validate(_fixture("VRRM")["capital_structure"])
    assert cs.covenant_pointer_rows is not None
    rows = [r.model_copy(update={"filing_date": filed}) if r.accession == "0001193125-25-242530"
            else r for r in cs.covenant_pointer_rows.value or []]
    cs = cs.model_copy(update={"covenant_pointer_rows": cs.covenant_pointer_rows.model_copy(
        update={"value": rows})})
    assert _run("VRRM", cs=cs).by[VRRM_AMD4].outcome != "superseded"


# --- the fixtures read as the exhibits read -------------------------------------------------------


@pytest.mark.parametrize("ticker", ["AMZN", "BURL", "CNXC", "NFLX", "NKE", "TJX", "VRRM"])
def test_every_fixture_target_is_a_committed_pointer_target(ticker: str) -> None:
    """(precondition) The fixture's layer is the committed page's, unmodified, so its targets are
    the page's own. A page re-assembled since moves its pointers, and this pin names it."""
    p = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not p.exists():
        pytest.skip(f"no committed {ticker} dossier")
    committed = json.loads(p.read_text())["mechanical"]["capital_structure"]
    fx = _fixture(ticker)
    assert fx["capital_structure"]["covenant_pointer_rows"] == committed["covenant_pointer_rows"]
    layer = CapitalStructure.model_validate(fx["capital_structure"])
    assert layer.covenant_pointer_rows is not None
    targets = {f"{r.accession} · {f}" for r, f in ce._core_agreement_exhibits(
        list(layer.covenant_pointer_rows.value or []))}
    assert set(fx["texts"]) == targets


# --- the render: both renderers print each cause, with its evidence -------------------------------


def _hosted(ticker: str) -> dict[str, typing.Any]:
    """`ticker`'s committed page with the real loop's outcomes over its fixture attached."""
    page = _committed(ticker)
    run = _run(ticker)
    page["mechanical"]["capital_structure"]["covenant_exhibit_outcomes"] = {
        "value": [json.loads(o.model_dump_json()) for o in run.outcomes],
        "source_ref": ce.OUTCOMES_SOURCE_REF, "status": "present"}
    return page


def test_a_superseded_exhibit_prints_its_cause_on_both_renderers_e2e(
        tmp_path: pathlib.Path) -> None:
    """(+) VRRM's committed page with the real loop's outcomes: the line names Amendment No. 4,
    the A&R that superseded it and that exhibit's own words, the same on both renderers."""
    page = _hosted("VRRM")
    md = _md_line(page)
    assert (f"{VRRM_AMD4} — not sent: superseded by {VRRM_AR} — “amend and restate the Original "
            f"ABL Credit Agreement”, which names the REVOLVING CREDIT AGREEMENT dated 2018-03-01 "
            f"that this exhibit amends") in md, md
    assert _web_line(tmp_path, page) == md


def test_a_terminated_exhibit_prints_its_cause_on_both_renderers_e2e(
        tmp_path: pathlib.Path) -> None:
    """(+) NFLX's committed page with the real loop's outcomes: the 2014 purchase agreement's line
    states the maturity its title states and the panel's agreement, the same on both renderers."""
    page = _hosted("NFLX")
    md = _md_line(page)
    assert f"{NFLX_PA14} — not sent: terminated — its title states notes due 2024" in md, md
    assert _web_line(tmp_path, page) == md
