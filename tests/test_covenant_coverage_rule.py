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
from vinci.dossier.schemas import CapitalStructure, CovenantExhibitOutcome, Sourced

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
    _one_outcome_per_target(list(layer.covenant_pointer_rows.value or []), got)
    return _Run(llm.sent, {f"{o.accession} · {o.filename}": o for o in got}, flags, got)


def _one_outcome_per_target(rows: list[typing.Any], got: list[CovenantExhibitOutcome]) -> None:
    """The outcomes are the TARGETS, each once, in the located order (`_located_exhibits`): every
    pointer's primary exhibit, and each other exhibit its row lists that governs debt or could not
    be read (the selector, STATE row 63, 2026-11-16)."""
    keys = [(o.accession, o.filename) for o in got]
    located = [(r.accession, f) for r, f, _ in ce._located_exhibits(rows)]
    assert len(set(keys)) == len(keys), "one outcome per target"
    assert keys == [k for k in located if k in set(keys)], "in the located order"
    assert {(r.accession, f) for r, f in ce._core_agreement_exhibits(rows)} <= set(keys), \
        "every pointer's primary exhibit has its outcome"


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
VRRM_EX102 = "0001193125-25-242530 · vrrm-ex10_2.htm"
NKE_FIVE = "0000320187-25-000008 · nikefiveyearcreditagreemen.htm"


# --- the brief's five pins ------------------------------------------------------------------------


def test_vrrm_amendment_no_4_is_superseded_by_its_amended_and_restated_revolver() -> None:
    """(+) VRRM. Amendment No. 4 (filed 2025-05-15) amends the "Revolving Credit Agreement, dated as
    of March 1, 2018". The A&R revolver (filed 2025-10-17) names that agreement in its recital
    ("that certain Revolving Credit Agreement, dated as of the Original Closing Date", the date
    resolved by its own definition, "“Original Closing Date” shall mean March 1, 2018") and agrees
    "to amend and restate the Original ABL Credit Agreement". So the amendment is not sent, and its
    outcome cites the A&R and its words. At main it was sent, and any term it returned would have
    printed as a stale, separate group.
    MOVED WITH THE SELECTOR (2026-11-16): the term loan's 2025 restatement (`vrrm-ex10_2.htm`,
    beside the A&R in its filing) is now sent in place of the 2021 restatement it restates."""
    r = _run("VRRM")
    o = r.by[VRRM_AMD4]
    assert o.outcome == "superseded", o
    assert (o.superseded_by, o.superseded_by_filename) == tuple(VRRM_AR.split(" · "))
    assert o.evidence is not None
    assert "“amend and restate the Original ABL Credit Agreement”" in o.evidence
    assert "REVOLVING CREDIT AGREEMENT dated 2018-03-01 that this exhibit amends" in o.evidence
    assert VRRM_AMD4 not in r.sent
    assert r.sent == [VRRM_AR, VRRM_EX102], "the A&R revolver and the term loan's restatement"


def test_a_live_amendment_chain_stays_sent_cnxc_receivables_financing() -> None:
    """(+ / −) CNXC. Its 2025 amendment and restatement supersedes its 2023 one ("the provisions of
    the Existing Credit Agreement shall be superseded"), which superseded the 2020 credit agreement
    its 2021 first amendment amends. Its receivables financing agreement's third and fourth
    amendments amend an agreement no later exhibit names, so that chain stays sent: a rule reading
    "a later restatement supersedes every earlier amendment" would drop it.
    MOVED WITH THE SELECTOR (2026-11-16): its fifth amendment, beside the 2025 restatement in its
    filing, is sent too, right after it."""
    r = _run("CNXC")
    rfa3 = "0001803599-24-000117 · exhibit101-thirdamendmentt.htm"
    rfa4 = "0001803599-25-000014 · exhibit101-fourthamendment.htm"
    ar25 = "0001803599-25-000111 · exhibit101041125.htm"
    ar23 = "0001803599-23-000107 · form8-k04x26x23exhibit101.htm"
    am21 = "0001803599-21-000215 · exhibit101122721.htm"
    rfa5 = "0001803599-25-000111 · exhibit102041125.htm"
    assert r.sent == [ar25, rfa3, rfa4, rfa5], r.sent  # every primary before any sibling
    assert (r.by[ar23].outcome, _by(r.by[ar23])) == ("superseded", ar25)
    assert (r.by[am21].outcome, _by(r.by[am21])) == ("superseded", ar23)
    assert "CREDIT AGREEMENT dated 2020-10-16 that this exhibit amends" in (r.by[am21].evidence
                                                                          or "")


def test_a_page_with_more_than_four_live_contracts_sends_them_all_burl() -> None:
    """(+) BURL. Six debt contracts, none displaced by a later located exhibit's words: its ABL
    agreement's four amendments, its term loan's 2014 Amendment No. 4 and a 2020 security
    agreement. All six are sent, where main sent four and left two past the bound. The guard is
    not reached, so no exhibit is cost bound and no flag says so.
    MOVED WITH THE SELECTOR (2026-11-16): seven: the ABL agreement's 2014 first amendment, beside
    the term loan's Amendment No. 4 in its filing, is sent too. Its 2020 filing's intellectual
    property security agreement and pledge agreement are credit support, and are not."""
    r = _run("BURL")
    assert len(r.sent) == 7 > 4, r.sent
    assert "0001193125-14-313404 · d772516dex102.htm" in r.sent
    assert not {"0001193125-20-109457 · d883886dex102.htm",
                "0001193125-20-109457 · d883886dex103.htm"} & set(r.by)
    assert "0001193125-22-200058 · d393601dex101.htm" in r.sent
    assert "0001193125-14-313404 · d772516dex101.htm" in r.sent
    assert not any(o.outcome == "cost_bound" for o in r.outcomes)
    assert not any("RUNAWAY GUARD" in f for f in r.flags)


def test_the_runaway_guard_fires_loudly_on_an_overflow() -> None:
    """(+) SYNTHETIC OVERFLOW from BURL's real exhibits: its pointer rows twice over, the copies
    under synthetic accessions serving the same real texts, so 12 live debt contracts. The guard
    sends 10 and marks the 2 past it cost bound, each with a RUNAWAY GUARD flag that names the
    count and the guard. At main the cap of four chose, quietly.
    MOVED WITH THE SELECTOR (2026-11-16): BURL has seven live contracts, so the doubled page has 14
    and the guard marks 4."""
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
    assert len(past) == 4, past
    guard = [f for f in r.flags if f.startswith("(E5) RUNAWAY GUARD")]
    assert len(guard) == 4, r.flags
    assert all("14 live debt contracts" in f and "the guard is 10 calls" in f for f in guard)


def test_an_exhibit_the_words_cannot_classify_is_read_amzn() -> None:
    """(+ / −) AMZN. Its 2014 credit agreement is named by no later located exhibit (its 2018
    restatement names a May 20, 2016 agreement), so nothing shows it displaced and it is READ,
    never silently skipped. Its 2022 364-day agreement is superseded by the 2023 five-year
    agreement, whose definitions bind it ("“Existing 364-Day Credit Agreement” means that certain
    364-Day Revolving Credit Agreement dated as of November 18, 2022") and whose conditions say
    "all commitments thereunder shall have been terminated". Its 2018 restatement is superseded by
    the 2020 one. So its June 2026 term loan agreement, past the bound at main, is sent.
    MOVED WITH THE SELECTOR (2026-11-16): its 2023 364-day agreement, beside the five-year one in
    its filing, is sent too. Nothing located shows it displaced, so it is read."""
    r = _run("AMZN")
    assert r.sent == ["0001104659-23-113444 · tm2329405d1_ex10-1.htm",
                      "0001193125-20-176528 · d948849dex101.htm",
                      "0001018724-14-000042 · amzn2014september5-ex101.htm",
                      "0001104659-26-072140 · tm2613616d4_ex10-1.htm",
                      "0001104659-23-113444 · tm2329405d1_ex10-2.htm"], r.sent  # primaries first
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
    contract (operator, 2026-11-16).
    MOVED WITH THE SELECTOR (2026-11-16): six sends: its December 2025 delayed-draw term loan
    agreement, beside its revolver in its filing, is sent too."""
    r = _run("NFLX")
    o = r.by[NFLX_PA14]
    assert o.outcome == "terminated" and o.superseded_by is None
    assert o.superseded_by_filename is None
    assert o.evidence is not None and "notes due 2024" in o.evidence
    assert "the CIQ panel carries no instrument maturing in 2024" in o.evidence
    assert r.sent[-1] == NFLX_PA18 and NFLX_PA14 not in r.sent
    assert len(r.sent) == 6 and "0001193125-25-327462 · d82688dex102.htm" in r.sent, r.sent


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
    2026 agreement is sent; the 2023, 2024 and 2025 ones are each superseded by the next.
    MOVED WITH THE SELECTOR (2026-11-16): its 2025 FIVE YEAR CREDIT AGREEMENT (the panel's facility
    to 2030-03-07), beside the 2025 364-day agreement in its filing, is sent too: no 364-day
    agreement names it."""
    r = _run("NKE")
    assert r.sent == ["0000320187-26-000020 · a364-daycreditagreementxni.htm", NKE_FIVE], r.sent
    chain = [("0000320187-25-000008", "0000320187-26-000020"),
             ("0000320187-24-000009", "0000320187-25-000008"),
             ("0000320187-23-000006", "0000320187-24-000009")]
    for old, new in chain:
        [o] = [o for k, o in r.by.items() if k.startswith(old) and k != NKE_FIVE]
        assert o.outcome == "superseded" and o.superseded_by == new, o


def test_a_collective_definition_supersedes_both_its_agreements_tjx() -> None:
    """(+) TJX. Its 2021 agreement defines its "Existing Credit Agreements" as "(x) that certain
    2022 Revolving Credit Agreement, dated as of March 11, 2016 … and (y) that certain 364 Day
    Revolving Credit Agreement" and requires "evidence of termination of the Existing Credit
    Agreements". So the 2020 second amendment to the first and the 2020 364-day agreement are
    superseded.
    MOVED WITH THE SELECTOR (2026-11-16): three sends: its 2025 second amendment ("2030 REVOLVING
    CREDIT AGREEMENT", beside the first amendment in its filing) and its 2020 second amendment to
    the 2024 agreement (beside the first 2020 exhibit) are sent, and the 2021 agreement, which the
    2025 one amends and restates, reads superseded."""
    r = _run("TJX")
    for key in ("0001157523-20-000793 · a52222014ex10_1.htm",
                "0000109198-20-000015 · exhibit101364dayrevolv.htm"):
        assert r.by[key].outcome == "superseded", r.by[key]
        assert _by(r.by[key]) == "0001193125-21-202939 · d169110dex101.htm"
    assert len(r.sent) == 3, r.sent


# --- what the reader refuses: each guard on a real clause, derived ------------------------------


def test_a_conditional_termination_displaces_nothing() -> None:
    """(−) DERIVED from TJX's real condition precedent. "upon termination of the Existing Credit
    Agreements" is a condition, not a statement that they ended, so neither 2020 exhibit is
    superseded and both are read.
    MOVED WITH THE SELECTOR (2026-11-16): the 2025 second amendment is now read too, and it carries
    the same real condition (it restates the 2021 agreement), so the derivation is made in both. The
    2021 agreement still reads superseded, by the 2025 one's "amend and restate", which no condition
    touches."""
    old, new = ("evidence of termination of the Existing Credit Agreements",
                "upon termination of the Existing Credit Agreements")
    texts = _edited("TJX", "0001193125-21-202939 · d169110dex101.htm", old, new)
    k25 = "0000109198-25-000033 · exhibit102-secondamendment.htm"
    assert old in (texts[k25] or "")
    texts[k25] = (texts[k25] or "").replace(old, new, 1)
    r = _run("TJX", texts=texts)
    for key in ("0001157523-20-000793 · a52222014ex10_1.htm",
                "0000109198-20-000015 · exhibit101364dayrevolv.htm"):
        assert r.by[key].outcome != "superseded" and key in r.sent, r.by[key]
    assert [_by(o) for o in r.outcomes if o.outcome == "superseded"] == [k25]
    assert len(r.sent) == 5


def test_a_part_of_the_agreement_displaces_nothing() -> None:
    """(−) DERIVED from NKE's real clause: "Section 2.5.12 of the 2025 Credit Agreement has been …
    terminated" ends a part, not the agreement, so the 2025 agreement is read. The subject guard
    (`_UNDER_THE`) holds it: a part reaches the term only through "of", "to", "in" or "under". The
    separate part guard the rule first shipped was redundant and is removed (review round 2, F6).
    No committed or cached clause has this shape (0 of the 29 displacing reads over the 92 cached
    documents the gate passes)."""
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
    and both the revolver amendment and the term loan restatement are read.
    MOVED WITH THE SELECTOR (2026-11-16): the term loan's 2021 restatement now reads superseded, by
    its 2025 restatement's own words, never by the A&R revolver's ambiguous name."""
    texts = _edited("VRRM", VRRM_AR, "that certain Revolving Credit Agreement, dated as of",
                    "that certain Credit Agreement, dated as of")
    r = _run("VRRM", texts=texts)
    assert r.by[VRRM_AMD4].outcome != "superseded" and VRRM_AMD4 in r.sent
    assert _by(r.by[VRRM_TL]) == VRRM_EX102, r.by[VRRM_TL]


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


def test_an_untitled_exhibit_dated_as_the_displaced_agreement_blocks_the_supersession() -> None:
    """(−) FAIL CLOSED, DERIVED from VRRM's real term-loan restatement with its heading removed,
    so E5 reads no title and refuses it ("This instrument (this “Restatement”) dated as of March
    26, 2021 to the First Lien Term Loan Credit Agreement dated as of March 1, 2018"). Its name is
    unread, and its head carries March 1, 2018, the date of the agreement the A&R displaces: it may
    be that agreement, so Amendment No. 4 is read (Codex, PR #1090 round 1)."""
    texts = _edited("VRRM", VRRM_TL,
                    "AMENDMENT AND RESTATEMENT AGREEMENT NO. 1 This AMENDMENT AND RESTATEMENT "
                    "AGREEMENT NO. 1 (this “ Restatement ”)",
                    "This instrument (this “ Restatement ”)")
    r = _run("VRRM", texts=texts)
    assert (r.by[VRRM_TL].outcome, r.by[VRRM_TL].declared_title) == ("not_debt_agreement", None)
    assert r.by[VRRM_AMD4].outcome != "superseded" and VRRM_AMD4 in r.sent


def test_an_unknown_instrument_panel_is_not_an_empty_one() -> None:
    """(−) DERIVED from NFLX's real layer with its CIQ panel UNKNOWN (an extraction failure). No
    panel says nothing about which notes remain, so the 2014 purchase agreement is read, never
    found terminated on a missing panel (Codex, PR #1090 round 1)."""
    fx = _fixture("NFLX")
    cs = CapitalStructure.model_validate(fx["capital_structure"])
    cs = cs.model_copy(update={"instruments": Sourced.unknown(note="CIQ panel not read")})
    r = _run("NFLX", cs=cs)
    assert r.by[NFLX_PA14].outcome != "terminated" and NFLX_PA14 in r.sent


def test_a_one_word_name_matches_only_itself() -> None:
    """(+ / −) A bare "INDENTURE" is not a "FIRST SUPPLEMENTAL INDENTURE" of the same date, often
    signed the same day (derived; review round 0). Since round 2 (F1) a name matches only itself:
    `test_f1_a_name_must_be_the_same_name`."""
    day = ce.date(2017, 5, 24)
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
    """(precondition) The fixture's layer is the committed page's, unmodified, so its exhibits are
    the page's own: every target, and every other exhibit a pointer row lists, which the loop reads
    for who it is (review round 2, F1). A page re-assembled since moves its pointers, and this pin
    names it."""
    p = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not p.exists():
        pytest.skip(f"no committed {ticker} dossier")
    committed = json.loads(p.read_text())["mechanical"]["capital_structure"]
    fx = _fixture(ticker)
    assert fx["capital_structure"]["covenant_pointer_rows"] == committed["covenant_pointer_rows"]
    layer = CapitalStructure.model_validate(fx["capital_structure"])
    assert layer.covenant_pointer_rows is not None
    rows = list(layer.covenant_pointer_rows.value or [])
    every = {f"{r.accession} · {f}" for r in rows if r.accession for f in r.exhibits}
    targets = {f"{r.accession} · {f}" for r, f in ce._core_agreement_exhibits(rows)}
    assert targets <= every and set(fx["texts"]) == every


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


# --- independent review, round 2: on any doubt about identity, READ ------------------------------

ROUND2 = FIX / "round2_heads.json"
NKE_2024 = "0000320187-24-000009 · nike-364xdaycreditagreemen.htm"
NKE_2023 = "0000320187-23-000006 · nike-364xdaycreditagreemen.htm"


def _round2(key: str) -> str:
    heads: dict[str, str] = json.loads(ROUND2.read_text())
    return heads[key]


def _with_rows(ticker: str, extra: list[tuple[str, str, str]]) -> CapitalStructure:
    """``ticker``'s committed layer plus DERIVED pointer rows (accession, exhibit, filing date)."""
    from vinci.dossier.schemas import CovenantPointer
    cs = CapitalStructure.model_validate(_fixture(ticker)["capital_structure"])
    assert cs.covenant_pointer_rows is not None
    rows = list(cs.covenant_pointer_rows.value or [])
    rows += [CovenantPointer(family=f"derived {acc}", filing="8-K", filing_date=filed,
                             accession=acc, exhibits=[doc]) for acc, doc, filed in extra]
    return cs.model_copy(update={"covenant_pointer_rows": cs.covenant_pointer_rows.model_copy(
        update={"value": rows})})


def test_f1_a_same_day_sibling_makes_the_displaced_name_ambiguous_vrrm() -> None:
    """(−) F1, on VRRM's REAL `vrrm-ex10_2.htm` (its 2025-10-17 term-loan Amendment and
    Restatement Agreement No. 2, which E5 titles CREDIT AGREEMENT), targeted as a widened selector
    would. A DERIVED later revolver restatement (VRRM's real A&R recital re-dated) displaces the
    "Revolving Credit Agreement" dated October 17, 2025. Two agreements share that date and the
    tail cannot tell them apart, so the displaced name decides neither: both are READ. At the PR
    head the live term-loan restatement read superseded (independent review, round 1)."""
    later = "9999999999-27-000001 · later-ex10_1.htm"
    texts = dict(_fixture("VRRM")["texts"])
    ar = texts[VRRM_AR] or ""
    for old, new in (("Dated as of October 17, 2025", "Dated as of June 1, 2027"),
                     ("shall mean March 1, 2018", "shall mean October 17, 2025")):
        assert old in ar, old
        ar = ar.replace(old, new)
    texts[later] = ar
    texts[VRRM_EX102] = _round2(VRRM_EX102)
    cs = _with_rows("VRRM", [("0001193125-25-242530", "vrrm-ex10_2.htm", "2025-10-17"),
                             ("9999999999-27-000001", "later-ex10_1.htm", "2027-06-01")])
    r = _run("VRRM", texts=texts, cs=cs)
    assert r.by[VRRM_EX102].outcome != "superseded", r.by[VRRM_EX102]
    assert r.by[VRRM_AR].outcome != "superseded", r.by[VRRM_AR]


#: BURL's real clause naming its 2020 security agreement (`…21-364998 · d275638dex101.htm`, the ABL
#: agreement's third amendment), and VRRM's real operative clause restating its security agreement
#: (`…25-242530 · vrrm-ex10_2.htm`), its term renamed: the derived later exhibit's two clauses.
BURL_SA_RECITAL = ("the Security Agreement, dated as of April 16, 2020 (the “Security Agreement”), "
                   "by and among the Grantors party thereto and the Additional Pari Passu "
                   "Collateral Agent")
VRRM_SA_RESTATED = ("The Existing Security Agreement is, effective as of the Second Restatement "
                    "Effective Date and immediately after giving effect to the incurrence of the "
                    "Initial Term Loans, hereby amended and restated")
BURL_SA = "0001193125-20-109457 · d883886dex101.htm"
BURL_IPSA = "0001193125-20-109457 · d883886dex102.htm"


def test_f1_an_untargeted_same_filing_sibling_makes_the_name_ambiguous_burl() -> None:
    """(− / +) F1, the SIBLING half: an exhibit a located pointer row lists that the selector does
    not target is still read for WHO it is. BURL's 2020 filing carries its SECURITY AGREEMENT (the
    target) and, beside it, its INTELLECTUAL PROPERTY SECURITY AGREEMENT of the same date, which is
    credit support and never sent. A DERIVED later exhibit (BURL's real head and clause naming "the
    Security Agreement, dated as of April 16, 2020", and VRRM's real operative restatement, its term
    renamed) restates "the Security Agreement" of that date. The name fits both agreements of that
    day, so it decides neither, and the security agreement is READ. With the sibling gone from the
    filing, the same words supersede it: the sibling is what blocks. MOVED WITH THE SELECTOR
    (2026-11-16): this pin first stood on VRRM's `vrrm-ex10_2.htm`, which governs debt and is now a
    target (`test_f1_a_same_day_sibling_makes_the_displaced_name_ambiguous_vrrm` keeps that
    half)."""
    fx = _fixture("BURL")
    texts = dict(fx["texts"])
    third = texts["0001193125-21-364998 · d275638dex101.htm"] or ""
    assert ce._governs(ce.agreement_title(third))
    assert ce.agreement_title(texts[BURL_IPSA] or "") == "INTELLECTUAL PROPERTY SECURITY AGREEMENT"
    assert not ce._governs("INTELLECTUAL PROPERTY SECURITY AGREEMENT")
    clause = VRRM_SA_RESTATED.replace("Existing Security Agreement", "Security Agreement")
    texts["9999999999-26-000009 · later-ex10_1.htm"] = f"{third} … {BURL_SA_RECITAL} … {clause}"
    cs = _with_rows("BURL", [("9999999999-26-000009", "later-ex10_1.htm", "2026-06-01")])
    r = _run("BURL", texts=texts, cs=cs)
    assert BURL_IPSA not in r.by, "credit support is read for who it is, never targeted"
    assert r.by[BURL_SA].outcome != "superseded" and BURL_SA in r.sent, r.by[BURL_SA]
    # the control: the same page with the sibling dropped from its filing
    assert cs.covenant_pointer_rows is not None
    rows = [row.model_copy(update={"exhibits": [f for f in row.exhibits
                                                if f != BURL_IPSA.split(" · ")[1]]})
            for row in cs.covenant_pointer_rows.value or []]
    alone = cs.model_copy(update={"covenant_pointer_rows": cs.covenant_pointer_rows.model_copy(
        update={"value": rows})})
    r = _run("BURL", texts=texts, cs=alone)
    assert (r.by[BURL_SA].outcome, _by(r.by[BURL_SA])) == (
        "superseded", "9999999999-26-000009 · later-ex10_1.htm"), r.by[BURL_SA]


def test_f1_the_nke_shape_two_agreements_one_date_and_a_plain_amendment() -> None:
    """(− / +) F1, the NKE SHAPE, DERIVED from NKE's real heads.
    - Its 364-day CREDIT AGREEMENT and its FIVE YEAR CREDIT AGREEMENT both dated March 11, 2022.
      NKE's 2023 agreement terminates its "2022 Credit Agreement": the name fits both, so neither
      is superseded.
    - A FIRST AMENDMENT to the five-year agreement dated March 8, 2024, the day of the 2024 364-day
      agreement. A plain amendment's own date is not an agreement's: only what it amends identifies
      it. So the 2025 agreement's displacement of the 2024 one supersedes the 2024 agreement and
      never the five-year amendment."""
    texts = dict(_fixture("NKE")["texts"])
    c364 = (texts[NKE_2024] or "").replace("March 8, 2024", "March 11, 2022")
    five = _round2(NKE_FIVE)
    assert "March 7, 2025" in five and "March 8, 2024" in (texts[NKE_2024] or "")
    texts["9999999999-22-000001 · c364-2022.htm"] = c364
    texts["9999999999-22-000002 · five-2022.htm"] = five.replace("March 7, 2025", "March 11, 2022")
    amd = five.replace("FIVE YEAR CREDIT AGREEMENT Dated as of March 7, 2025",
                       "FIRST AMENDMENT TO FIVE YEAR CREDIT AGREEMENT dated as of March 8, 2024, "
                       "to the Five Year Credit Agreement, dated as of March 11, 2022,")
    assert amd != five
    texts["9999999999-24-000003 · five-amd1.htm"] = amd
    cs = _with_rows("NKE", [("9999999999-22-000001", "c364-2022.htm", "2022-03-14"),
                            ("9999999999-22-000002", "five-2022.htm", "2022-03-14"),
                            ("9999999999-24-000003", "five-amd1.htm", "2024-03-11")])
    r = _run("NKE", texts=texts, cs=cs)
    assert r.by["9999999999-22-000002 · five-2022.htm"].outcome != "superseded"
    assert r.by["9999999999-22-000001 · c364-2022.htm"].outcome != "superseded"
    assert r.by["9999999999-24-000003 · five-amd1.htm"].outcome != "superseded"
    assert r.by[NKE_2024].outcome == "superseded", r.by[NKE_2024]


def test_f1_a_name_must_be_the_same_name() -> None:
    """(+ / −) F1. One agreement is the same NAME and the same date. EPAM's restatement names a
    "Credit Agreement" of May 24, 2017, which E5 titles by its cover, "REVOLVING CREDIT FACILITY
    CREDIT AGREEMENT": the names differ, so on that doubt it is read. The tail still makes two
    namings CONFUSABLE, which is what makes a displaced name ambiguous."""
    day = ce.date(2017, 5, 24)
    generic, cover = ce.AgreementKey("CREDIT AGREEMENT", day), ce.AgreementKey(
        "REVOLVING CREDIT FACILITY CREDIT AGREEMENT", day)
    assert not ce._same_agreement(generic, cover) and ce._confusable(generic, cover)
    assert ce._same_agreement(generic, ce.AgreementKey("CREDIT AGREEMENT", day))
    assert not ce._confusable(ce.AgreementKey("CREDIT AGREEMENT", day),
                              ce.AgreementKey("SECURITY AGREEMENT", day))


def test_f2_an_amendments_base_is_read_from_its_heading_not_its_recitals_history() -> None:
    """(+) F2, UBER's REAL head (`…21-000058`). Its heading names no date; its recital names
    "that certain Term Loan Agreement, dated as of July 13, 2016 (as amended by that certain
    Amendment No. 1 to the Term Loan Agreement, dated as of June 13, 2018 …". The base is the
    2016 agreement, not Amendment No. 1's date."""
    head = _round2("0001552781-21-000058 · e21071_ex10-1.htm")
    title = ce.agreement_title(head)
    assert title == "TERM LOAN AGREEMENT"
    _own, base = ce.exhibit_identity(head, title, ce.is_amendment(head))
    assert base == ce.AgreementKey("TERM LOAN AGREEMENT", ce.date(2016, 7, 13)), base


NKE_2026 = "0000320187-26-000020 · a364-daycreditagreementxni.htm"
NKE_DEFN = ("“ 2025 Credit Agreement ” means that certain 364-Day Credit Agreement, dated as of "
            "March 7, 2025")


def test_f3_a_second_agreement_binds_only_inside_its_own_collective_definition() -> None:
    """(−) F3, DERIVED from NKE's real definition of its "2025 Credit Agreement", which has no
    "(x)", followed by the NEXT definition naming "(y)" an agreement. That (y) is the next
    definition's, never the 2025 Credit Agreement's."""
    body = _fixture("NKE")["texts"][NKE_2026] or ""
    assert NKE_DEFN in body
    derived = body.replace(NKE_DEFN, NKE_DEFN + ". “ Other Facilities ” means, collectively, (x) "
                           "the facilities listed in Schedule 1 and (y) that certain Five Year "
                           "Credit Agreement, dated as of March 11, 2022", 1)
    keys = {d.key for d in ce.displaced_agreements(derived)}
    assert ce.AgreementKey("364-DAY CREDIT AGREEMENT", ce.date(2025, 3, 7)) in keys
    assert ce.AgreementKey("FIVE YEAR CREDIT AGREEMENT", ce.date(2022, 3, 11)) not in keys, keys


def test_f3_a_y_in_the_body_after_a_definition_without_x_binds_nothing() -> None:
    """(−) F3, the "(x)" half, DERIVED from NKE's real definition (no "(x)") followed, with no
    definition between, by body prose listing "(y) that certain Five Year Credit Agreement". A
    "(y)" binds only inside a definition that has its "(x)"."""
    body = _fixture("NKE")["texts"][NKE_2026] or ""
    derived = body.replace(NKE_DEFN, NKE_DEFN + ", as amended. The Company has delivered (y) that "
                           "certain Five Year Credit Agreement, dated as of March 11, 2022", 1)
    keys = {d.key for d in ce.displaced_agreements(derived)}
    assert ce.AgreementKey("FIVE YEAR CREDIT AGREEMENT", ce.date(2022, 3, 11)) not in keys, keys


def test_f3_a_y_in_the_next_definition_is_that_definitions() -> None:
    """(− / +) F3, the next-definition half, DERIVED from TJX's real collective definition, its
    "(y)" moved into a definition of its own: the first definition has its "(x)", and the "(y)"
    after the next definition begins is not the first's. TJX's real definition, (x) and (y) in
    one, still binds both (`test_a_collective_definition_supersedes_both_its_agreements_tjx`)."""
    key = "0001193125-21-202939 · d169110dex101.htm"
    body = _fixture("TJX")["texts"][key] or ""
    old = "; and (y) that certain 364 Day Revolving Credit Agreement"
    assert old in body
    derived = body.replace(old, ". “ Other Agreements ” means (y) that certain 364 Day Revolving "
                           "Credit Agreement", 1)
    keys = {d.key for d in ce.displaced_agreements(derived)}
    assert ce.AgreementKey("2022 REVOLVING CREDIT AGREEMENT", ce.date(2016, 3, 11)) in keys
    assert ce.AgreementKey("364 DAY REVOLVING CREDIT AGREEMENT", ce.date(2020, 8, 10)) not in keys


def test_a_recital_never_binds_a_definitions_own_term() -> None:
    """(−) Found writing F3's pin, DERIVED from the same real definition: a sentence naming "that
    certain Five Year Credit Agreement, dated as of March 11, 2022" just before it. The recital
    binder's gap reached across the sentence end to the definition's own term, “2025 Credit
    Agreement”, and bound the five-year agreement to it."""
    body = _fixture("NKE")["texts"][NKE_2026] or ""
    derived = body.replace(NKE_DEFN, "The facilities include that certain Five Year Credit "
                           "Agreement, dated as of March 11, 2022. " + NKE_DEFN, 1)
    keys = {d.key for d in ce.displaced_agreements(derived)}
    assert ce.AgreementKey("364-DAY CREDIT AGREEMENT", ce.date(2025, 3, 7)) in keys
    assert ce.AgreementKey("FIVE YEAR CREDIT AGREEMENT", ce.date(2022, 3, 11)) not in keys, keys


@pytest.mark.parametrize("old,new", [
    ("all the principal, interest and fees outstanding under the Existing Credit Agreements",
     "all the Revolving Loans outstanding under the Existing Credit Agreements"),
    ("all the principal, interest and fees outstanding under the Existing Credit Agreements shall "
     "have been paid in full and all commitments thereunder",
     "all revolving commitments under the Existing Credit Agreements"),
])
def test_f4_a_tranche_ending_is_not_the_agreement_ending(old: str, new: str) -> None:
    """(−) F4, DERIVED from AMZN's real condition precedent, edited to a tranche: "all the Revolving
    Loans outstanding under the … shall have been paid in full" and "all revolving commitments
    under the … shall have been terminated" end a tranche, and the agreement may live on, so its
    2022 364-day agreement is read.
    MOVED WITH THE SELECTOR (2026-11-16): the 2023 364-day agreement beside the five-year one is now
    read too, and states the same real condition, so the derivation is made in both."""
    key = "0001104659-23-113444 · tm2329405d1_ex10-1.htm"
    texts = _edited("AMZN", key, old, new)
    k364 = "0001104659-23-113444 · tm2329405d1_ex10-2.htm"
    assert old in (texts[k364] or "")
    texts[k364] = (texts[k364] or "").replace(old, new, 1)
    r = _run("AMZN", texts=texts)
    assert r.by["0001193125-22-289041 · d413765dex101.htm"].outcome != "superseded"


def test_f5_a_recital_binds_its_term_to_the_agreement_beside_it() -> None:
    """(−) F5, DERIVED from VRRM's real recital with a second agreement before the term: "that
    certain Credit Agreement, dated as of … and that certain Revolving Credit Agreement, dated as of
    the Original Closing Date (… the “Original ABL Credit Agreement”)". The term binds to the
    agreement beside it, never across the first."""
    texts = _fixture("VRRM")["texts"]
    body = texts[VRRM_AR] or ""
    old = "that certain Revolving Credit Agreement, dated as of the Original Closing Date"
    assert old in body
    derived = body.replace(old, "that certain Term Loan Credit Agreement, dated as of June 1, 2016 "
                           "and " + old, 1)
    keys = {d.key for d in ce.displaced_agreements(derived)}
    assert ce.AgreementKey("REVOLVING CREDIT AGREEMENT", ce.date(2018, 3, 1)) in keys
    assert ce.AgreementKey("TERM LOAN CREDIT AGREEMENT", ce.date(2016, 6, 1)) not in keys, keys


def test_codex_round2_an_undated_notes_row_is_not_an_absent_one() -> None:
    """(−) Codex, PR #1090 round 2, DERIVED from NFLX's real panel: one more Bonds and Notes row
    with principal and NO maturity date. It may be the 2024 notes, so the 2014 purchase agreement is
    read. NFLX's own undated rows (commercial paper, a lease, a term loan) are not notes and do not
    block it (`test_matured_notes_read_terminated_and_a_live_purchase_agreement_goes_last_nflx`)."""
    fx = _fixture("NFLX")
    cs = CapitalStructure.model_validate(fx["capital_structure"])
    insts = list(cs.instruments.value or [])
    notes = next(i for i in insts if i.type == "Bonds and Notes")
    extra = notes.model_copy(update={"description": "5.750% Senior Notes", "maturity_date": None,
                                     "ciq_maturity_date": None, "principal_musd": 400.0})
    cs = cs.model_copy(update={"instruments": cs.instruments.model_copy(
        update={"value": [*insts, extra]})})
    r = _run("NFLX", cs=cs)
    assert r.by[NFLX_PA14].outcome != "terminated" and NFLX_PA14 in r.sent
