"""The covenant phase's TARGET SELECTOR reads the live governing documents a located pointer row
lists (STATE row 63, 2026-11-16).

Until this, `_core_agreement_exhibits` targeted ONE exhibit per located pointer, chosen by its file
name, and nothing else in the filing was ever sent. Measured at main 51784e53 over the 24 committed
pages with pointer rows (EDGAR cache only): 60 other exhibits sat on located pointers, 3 of them
cache misses, and the gate passed 20 of the rest. 14 of those 20 are contracts that govern debt,
among them:
- VRRM's `vrrm-ex10_2.htm`, its 2025-10-17 Amendment and Restatement Agreement No. 2 of its
  first-lien term loan, beside its A&R revolver. The page sent the 2021 restatement it restates, so
  VRRM's next paid build would have extracted the 2021 terms (LIBO Rate + 3.25%);
- NKE's FIVE YEAR CREDIT AGREEMENT (the panel's facility to 2030-03-07), beside a 364-day one;
- NFLX's December 2025 delayed-draw term loan agreement, beside its revolver;
- TJX's "2030 REVOLVING CREDIT AGREEMENT", which restates the 2021 agreement the page sent.
The other 6 are credit support (pledges, guaranties, security and collateral agreements), which
secure obligations their credit agreement defines and which the selector leaves to it.

Now every document a located pointer row lists is read, and one whose own title names a contract
that governs debt (`_governs`) is a target, read by the coverage rule like any other: a 2025
restatement supersedes the 2021 one it restates. One that cannot be read is a target too, and its
outcome says so. The reader learns two forms, each read on VRRM's real restatements: a term defined
in the parenthetical at the agreement's date, however long its history (`_BIND_RECITAL_AFTER`), and
the operative clause in the passive ("The Existing Credit Agreement is, …, hereby amended and
restated").

THE FIXTURES ARE THE REAL TYPE: `tests/fixtures/covenant_coverage_rule/` (its README), seven
committed pages' layers, unmodified, and a cut of every exhibit their pointer rows list, each
reading as its full exhibit reads at this code. The loop runs unmodified, stubbed only at the fetch
and the model.
"""

from __future__ import annotations

import copy
import json
import pathlib
import typing

import pytest

from tests.test_covenant_coverage_rule import (
    NKE_FIVE,
    VRRM_AMD4,
    VRRM_AR,
    VRRM_EX102,
    VRRM_TL,
    _by,
    _fixture,
    _hosted,
    _run,
)
from tests.test_covenant_exhibit_outcomes import _committed, _md_line, _web_line
from vinci.dossier import covenant_extract as ce
from vinci.dossier.schemas import CapitalStructure

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --- the brief's pin: VRRM's term-loan restatement is targeted, and supersedes the 2021 one -------


def test_vrrm_term_loan_restatement_is_targeted_and_supersedes_the_2021_one() -> None:
    """(+) VRRM. Its A&R revolver's filing (`0001193125-25-242530`) also carries the term loan's
    "AMENDMENT AND RESTATEMENT AGREEMENT NO. 2" of October 17, 2025 (`vrrm-ex10_2.htm`), which E5
    titles CREDIT AGREEMENT. It is now a target, right after the revolver, and it is SENT. Its own
    words bind "the Amended and Restated First Lien Term Loan Credit Agreement dated as of March
    26, 2021 (… the “Existing Credit Agreement”)" and state "The Existing Credit Agreement is, …,
    hereby amended and restated". So the 2021 restatement (`vrrm-ex101_62.htm`), which main sent,
    reads superseded by it, citing those words. At main the 2025 restatement was never read."""
    r = _run("VRRM")
    keys = [f"{o.accession} · {o.filename}" for o in r.outcomes]
    assert keys.index(VRRM_EX102) == keys.index(VRRM_AR) + 1, keys
    assert r.by[VRRM_EX102].outcome != "superseded" and VRRM_EX102 in r.sent
    o = r.by[VRRM_TL]
    assert (o.outcome, _by(o)) == ("superseded", VRRM_EX102), o
    assert o.evidence is not None
    assert o.evidence.startswith("“The Existing Credit Agreement is, effective as of the Second "
                                 "Restatement Effective Date"), o.evidence
    assert "hereby amended and restated”" in o.evidence
    assert "FIRST LIEN TERM LOAN CREDIT AGREEMENT dated 2021-03-26 that this exhibit is" in (
        o.evidence)
    assert VRRM_TL not in r.sent
    assert r.sent == [VRRM_AR, VRRM_EX102]


def test_the_2021_term_loan_line_prints_its_superseder_on_both_renderers_e2e(
        tmp_path: pathlib.Path) -> None:
    """(+) END TO END: VRRM's committed page with the real loop's outcomes over its fixture. The
    2021 restatement's line names the 2025 restatement and its own words, the same on both
    renderers (`render_markdown`, the production `renderDossier`)."""
    page = _hosted("VRRM")
    md = _md_line(page)
    assert f"{VRRM_TL} — not sent: superseded by {VRRM_EX102} — “The Existing Credit Agreement" in (
        md), md
    assert "which names the FIRST LIEN TERM LOAN CREDIT AGREEMENT dated 2021-03-26" in md, md
    assert _web_line(tmp_path, page) == md


# --- the other governing documents a located pointer row lists -----------------------------------


@pytest.mark.parametrize("ticker,key,primary", [
    ("NKE", "0000320187-25-000008 · nikefiveyearcreditagreemen.htm",
     "0000320187-25-000008 · nike-364xdaycreditagreemen.htm"),
    ("NFLX", "0001193125-25-327462 · d82688dex102.htm",
     "0001193125-25-327462 · d82688dex101.htm"),
    ("TJX", "0000109198-25-000033 · exhibit102-secondamendment.htm",
     "0000109198-25-000033 · exhibit101-firstamendmentt.htm"),
    ("CNXC", "0001803599-25-000111 · exhibit102041125.htm",
     "0001803599-25-000111 · exhibit101041125.htm"),
    ("AMZN", "0001104659-23-113444 · tm2329405d1_ex10-2.htm",
     "0001104659-23-113444 · tm2329405d1_ex10-1.htm"),
    ("BURL", "0001193125-14-313404 · d772516dex102.htm",
     "0001193125-14-313404 · d772516dex101.htm"),
])
def test_a_governing_exhibit_beside_the_primary_is_targeted_and_sent(
        ticker: str, key: str, primary: str) -> None:
    """(+) The second exhibit a located pointer row lists, on six committed pages, each a contract
    that governs debt by its own title: NKE's five-year agreement, NFLX's delayed-draw term loan
    agreement, TJX's 2030 revolving credit agreement, CNXC's fifth amendment to its receivables
    financing agreement, AMZN's 2023 364-day agreement and BURL's 2014 first amendment to its ABL
    agreement. Each is a target right after its row's primary, and is sent. At main none was
    read."""
    r = _run(ticker)
    keys = [f"{o.accession} · {o.filename}" for o in r.outcomes]
    assert keys.index(key) == keys.index(primary) + 1, keys
    assert ce._governs(r.by[key].declared_title), r.by[key]
    assert key in r.sent, r.sent


def test_tjx_2030_agreement_supersedes_the_2021_agreement_it_restates() -> None:
    """(+) TJX. Its 2025 second amendment ("2030 REVOLVING CREDIT AGREEMENT") agrees to "amend and
    restate the 2026 Revolving Credit Agreement", the 2021 agreement main sent. That one now reads
    superseded, and the coverage rule still finds both 2020 exhibits superseded by it."""
    r = _run("TJX")
    o = r.by["0001193125-21-202939 · d169110dex101.htm"]
    assert (o.outcome, _by(o)) == (
        "superseded", "0000109198-25-000033 · exhibit102-secondamendment.htm"), o
    assert "“amend and restate the 2026 Revolving Credit Agreement”" in (o.evidence or "")


def test_credit_support_beside_the_primary_is_read_and_never_targeted_burl() -> None:
    """(−) BURL's 2020 filing carries, beside the security agreement its pointer targets, an
    INTELLECTUAL PROPERTY SECURITY AGREEMENT and a PLEDGE AGREEMENT (credit support, which the gate
    passes) and two intercreditor agreements (which it refuses). None governs debt, so none is a
    target, none is sent, and none writes an outcome: each is read only for who it is."""
    r = _run("BURL")
    for doc in ("d883886dex102.htm", "d883886dex103.htm", "d883886dex104.htm",
                "d883886dex105.htm"):
        key = f"0001193125-20-109457 · {doc}"
        assert key not in r.by and key not in r.sent, key
    assert "0001193125-20-109457 · d883886dex101.htm" in r.sent


def test_an_exhibit_that_is_not_debt_writes_no_outcome_vrrm() -> None:
    """(−) VRRM's 2018 filing carries, beside the subscription agreement its pointer targets (and E5
    refuses), a TAX RECEIVABLE AGREEMENT. It is read, and as no debt agreement it is never sent and
    writes no outcome: a page lists only its targets."""
    r = _run("VRRM")
    assert "0001104659-18-041476 · a18-15692_1ex10d2.htm" not in r.by
    assert r.by["0001104659-18-041476 · a18-15692_1ex10d1.htm"].outcome == "not_debt_agreement"


def test_an_unread_exhibit_beside_the_primary_is_a_target_and_supersedes_nothing() -> None:
    """(− / +) FAIL LOUD, DERIVED from VRRM's real fixture with the 2025 term-loan restatement
    unreadable (a failed fetch). It may govern debt, so it is a target: its outcome says it could
    not be fetched, and a flag says so. And as any unread exhibit, it may be an agreement a
    displaced name fits, so the page supersedes nothing: the 2021 restatement and Amendment No. 4
    are both read."""
    texts = dict(_fixture("VRRM")["texts"])
    texts[VRRM_EX102] = None
    r = _run("VRRM", texts=texts)
    assert r.by[VRRM_EX102].outcome == "fetch_failed", r.by[VRRM_EX102]
    assert any(f == f"(E5) covenant exhibit fetch failed — UNKNOWN: 8-K {VRRM_EX102}"
               for f in r.flags), r.flags
    assert r.by[VRRM_TL].outcome != "superseded" and VRRM_TL in r.sent
    assert r.by[VRRM_AMD4].outcome != "superseded" and VRRM_AMD4 in r.sent


# --- what governs: the document's own title -------------------------------------------------------

#: Real titles E5 reads (`agreement_title`) from the 92 cached EDGAR documents the gate passes.
GOVERNS = ("CREDIT AGREEMENT", "SENIOR UNSECURED DELAYED DRAW TERM LOAN CREDIT AGREEMENT",
           "FIVE YEAR CREDIT AGREEMENT", "2030 REVOLVING CREDIT AGREEMENT",
           "RECEIVABLES FINANCING AGREEMENT", "LOAN AGREEMENT", "TERM LOAN AGREEMENT",
           "LOAN AND SECURITY AGREEMENT", "CREDIT AND GUARANTY AGREEMENT",
           "SECOND AMENDMENT AND WAIVER TO ABL CREDIT AGREEMENT",
           "SENIOR NOTES DUE 2028 PURCHASE AGREEMENT", "SYNDICATED LOAN AGREEMENT")
#: Real titles of credit support among those 92: the gate passes each for a credit-support word
#: alone. Every one is a guaranty, a pledge, or a security or collateral agreement by its name.
SUPPORT = ("SECURITY AGREEMENT", "INTELLECTUAL PROPERTY SECURITY AGREEMENT", "PLEDGE AGREEMENT",
           "GUARANTY AGREEMENT", "LIMITED RECOURSE GUARANTY", "PERFORMANCE GUARANTY",
           "RESTATED GUARANTEE AND COLLATERAL AGREEMENT",
           "AMENDED AND RESTATED GUARANTY AND SECURITY AGREEMENT")


@pytest.mark.parametrize("title", GOVERNS)
def test_a_contract_that_creates_or_amends_debt_governs(title: str) -> None:
    """(+) A debt agreement the gate admits for a word that is not credit support governs, and a
    title with both ("LOAN AND SECURITY AGREEMENT", "CREDIT AND GUARANTY AGREEMENT") governs."""
    assert ce.is_debt_agreement(title) and ce._governs(title)


@pytest.mark.parametrize("title", SUPPORT)
def test_credit_support_does_not_govern(title: str) -> None:
    """(−) A title the gate admits only for credit-support words secures or guarantees what another
    agreement defines: it passes the gate, and does not govern."""
    assert ce.is_debt_agreement(title) and not ce._governs(title)


@pytest.mark.parametrize("title", [None, "TAX RECEIVABLE AGREEMENT", "EMPLOYMENT AGREEMENT",
                                   "AMENDED AND RESTATED INTERCREDITOR AGREEMENT"])
def test_what_is_not_debt_does_not_govern(title: str | None) -> None:
    """(−) No title, or one the gate refuses (real titles of three of those 60 exhibits)."""
    assert not ce._governs(title)


# --- the located order ----------------------------------------------------------------------------


def test_each_primary_is_followed_by_the_rest_of_its_filing() -> None:
    """(+) `_located_exhibits` over VRRM's real pointer rows: the primaries in
    `_core_agreement_exhibits`' order, each followed at once by the other exhibits its row lists, in
    the row's own order, each exhibit once."""
    cs = CapitalStructure.model_validate(_fixture("VRRM")["capital_structure"])
    assert cs.covenant_pointer_rows is not None
    rows = list(cs.covenant_pointer_rows.value or [])
    got = [(r.accession, f, p) for r, f, p in ce._located_exhibits(rows)]
    primaries = [(r.accession, f) for r, f in ce._core_agreement_exhibits(rows)]
    assert [(a, f) for a, f, p in got if p] == primaries
    assert len({(a, f) for a, f, _ in got}) == len(got) == sum(
        len(r.exhibits) for r in rows if r.accession)
    for i, (acc, _f, primary) in enumerate(got):
        if not primary:
            assert got[i - 1][0] == acc, got
    assert (VRRM_EX102.split(" · ")[0], VRRM_EX102.split(" · ")[1], False) in got


# --- the two forms the reader learns, each on a real clause ---------------------------------------

#: VRRM's real 2025 recital (454 characters between the date and the term) and its real operative
#: clause, from `vrrm-ex10_2.htm`.
VRRM_RECITAL = (
    "that certain Amended and Restated First Lien Term Loan Credit Agreement dated as of March 26, "
    "2021 (as amended by that certain Amendment No. 1, dated as of December 7, 2021, as amended by "
    "that certain Amendment No. 2, dated as of March 29, 2023, as amended by that certain "
    "Amendment No. 3, dated as of February 8, 2024, as amended by that certain Amendment No. 4, "
    "dated as of October 3, 2024 and as further amended, restated, amended and restated, "
    "supplemented or otherwise modified prior to the Second Restatement Effective Date, the “ "
    "Existing Credit Agreement ”)")
VRRM_RESTATED = ("3.01 Amendments to Existing Credit Agreement . The Existing Credit Agreement is, "
                 "effective as of the Second Restatement Effective Date and immediately after "
                 "giving effect to the incurrence of the Initial Term Loans, hereby amended and "
                 "restated in the form attached as Exhibit B hereto")
VRRM_2021 = ce.AgreementKey("FIRST LIEN TERM LOAN CREDIT AGREEMENT", ce.date(2021, 3, 26))


def test_the_parenthetical_at_the_date_binds_and_the_passive_restates() -> None:
    """(+) VRRM's two real clauses together displace the 2021 agreement, with the operative words.
    Each alone does not: the binding has no displacing verb, and the verb has no bound term."""
    got = ce.displaced_agreements(f"{VRRM_RECITAL} … {VRRM_RESTATED}")
    assert [d.key for d in got] == [VRRM_2021], got
    assert got[0].words.startswith("The Existing Credit Agreement is, effective as of")
    assert ce.displaced_agreements(VRRM_RECITAL) == []
    assert ce.displaced_agreements(VRRM_RESTATED) == []


def test_a_restated_part_displaces_nothing() -> None:
    """(−) PARR's real amendment (`0000821483-17-000034 · ex102-midpacxhiekeybankxam.htm`): its
    recital binds “Credit Agreement” to the agreement of December 17, 2015, and "Section 6.01(d) of
    the Credit Agreement is hereby amended and restated" restates a PART. Over the 92 cached gate
    passes the passive form reads 49 times, and 46 are such parts."""
    recital = ("the Credit Agreement, dated as of December 17, 2015 (as the same may from time to "
               "time be amended, restated or otherwise modified, the “ Credit Agreement ”)")
    part = "2.2 Section 6.01(d) of the Credit Agreement is hereby amended and restated"
    assert ce.displaced_agreements(f"{recital} … {part}") == []
    whole = "The Credit Agreement is hereby amended and restated"
    assert [d.key.dated for d in ce.displaced_agreements(f"{recital} … {whole}")] == [
        ce.date(2015, 12, 17)], "the control: the same binding, the whole agreement"


def test_a_restated_part_displaces_nothing_whatever_the_case_of_its_the() -> None:
    """(−) DERIVED from PARR's real part clause above (code review of the selector): the passive
    form admits "The" as well as "the", and the subject guard must read both. "Section 6.01(d) of
    The Credit Agreement" is still a part, so it displaces nothing; red before the guard folded
    the case."""
    recital = ("the Credit Agreement, dated as of December 17, 2015 (as the same may from time to "
               "time be amended, restated or otherwise modified, the “ Credit Agreement ”)")
    part = "2.2 Section 6.01(d) of The Credit Agreement is hereby amended and restated"
    assert ce.displaced_agreements(f"{recital} … {part}") == []


def test_a_past_restatement_is_history_not_the_operative_clause() -> None:
    """(−) DERIVED from VRRM's real recital and its own conformed copy's history ("the Original
    Credit Agreement was amended and restated on the First Restatement Effective Date"): a clause
    that says the agreement WAS amended and restated reports history. Only the operative present,
    "is … hereby amended and restated", displaces."""
    history = ("the Existing Credit Agreement was amended and restated on the First Restatement "
               "Effective Date")
    assert ce.displaced_agreements(f"{VRRM_RECITAL} … {history}") == []


def test_an_instrument_to_the_agreement_in_the_parenthetical_is_its_history_vrrm() -> None:
    """(+ / −) VRRM's real recital of its security agreement: "that certain First Lien Security
    Agreement, dated as of March 1, 2018 (as supplemented by the Joinder Agreement to the Security
    Agreement, dated as of December 7, 2021, …, the “Existing Security Agreement”)". A joinder TO
    the agreement is its history, as an amendment is: the term binds the First Lien Security
    Agreement of March 1, 2018, and never the joinder's December 7, 2021 (round 1 of #1091's
    review, extending N1 past "Amendment … to"). At #1091's head the joinder read as a second
    agreement, the true bind was refused, and a recital restarting inside the joinder's name bound
    "Security Agreement" to the joinder's date."""
    recital = ("that certain First Lien Security Agreement, dated as of March 1, 2018 (as "
               "supplemented by the Joinder Agreement to the Security Agreement, dated as of "
               "December 7, 2021, by and among the Credit Parties party thereto and the Collateral "
               "Agent and as it may have been further amended, restated, amended and restated, "
               "supplemented or otherwise modified prior to the date hereof, the “ Existing "
               "Security Agreement ”)")
    clause = VRRM_RESTATED.replace("Existing Credit Agreement", "Existing Security Agreement")
    keys = [d.key for d in ce.displaced_agreements(f"{recital} … {clause}")]
    assert keys == [ce.AgreementKey("FIRST LIEN SECURITY AGREEMENT", ce.date(2018, 3, 1))], keys
    assert ce.AgreementKey("SECURITY AGREEMENT", ce.date(2021, 12, 7)) not in keys


def test_vrrm_real_restatement_binds_its_security_agreement_not_the_joinders_date() -> None:
    """(+ / −) END TO END on VRRM's real `vrrm-ex10_2.htm` cut: what it displaces is the 2021 term
    loan agreement and the First Lien Security Agreement of March 1, 2018, never a "SECURITY
    AGREEMENT" of the joinder's December 7, 2021."""
    keys = {d.key for d in ce.displaced_agreements(_fixture("VRRM")["texts"][VRRM_EX102] or "")}
    assert keys == {ce.AgreementKey("FIRST LIEN TERM LOAN CREDIT AGREEMENT", ce.date(2021, 3, 26)),
                    ce.AgreementKey("FIRST LIEN SECURITY AGREEMENT", ce.date(2018, 3, 1))}, keys


def test_a_primary_of_any_pointer_stays_a_primary() -> None:
    """(−) DERIVED from VRRM's real rows: a second pointer carries the A&R revolver's filing with
    only `vrrm-ex10_2.htm`, so that exhibit is THIS pointer's primary and the other's sibling. It
    stays a primary whichever pointer lists it first, so it is targeted and gets an outcome even
    when its text (here VRRM's real tax receivable agreement head) is no debt agreement, as every
    primary does."""
    from vinci.dossier.schemas import CovenantPointer
    fx = _fixture("VRRM")
    cs = CapitalStructure.model_validate(fx["capital_structure"])
    assert cs.covenant_pointer_rows is not None
    acc, doc = VRRM_EX102.split(" · ")
    extra = CovenantPointer(family="derived: Senior Secured Term Loan", filing="8-K",
                            filing_date="2025-10-17", accession=acc, exhibits=[doc])
    for rows in ([*(cs.covenant_pointer_rows.value or []), extra],
                 [extra, *(cs.covenant_pointer_rows.value or [])]):
        assert (acc, doc, True) in [(r.accession, f, p) for r, f, p in ce._located_exhibits(rows)]
        layer = cs.model_copy(update={"covenant_pointer_rows": cs.covenant_pointer_rows.model_copy(
            update={"value": rows})})
        texts = dict(fx["texts"])
        texts[VRRM_EX102] = texts["0001104659-18-041476 · a18-15692_1ex10d2.htm"]
        r = _run("VRRM", texts=texts, cs=layer)
        assert r.by[VRRM_EX102].outcome == "not_debt_agreement", r.by[VRRM_EX102]


# --- the same-filing tie: two exhibits of one filing never share a governing group ----------------
# (coordinator's ruling (a), 2026-11-16). A filing's exhibits share its filing date, so in one group
# `governing_terms` could not order them: the later in the list governed every term, and the earlier
# one's base was cited for it. One exhibit per pointer was sent until this selector, so the tie
# could not arise (0 groups at #1090's head over the 24 pages; 3 at this selector's: WLK's pair and
# PARR's two pairs).

WLK_ACC = "0001193125-10-276447"
#: WLK's REAL IKE Zone loan agreement clause (`…10-276447 · dex102.htm`, read from the EDGAR cache),
#: the twin of the GO Zone clause its committed row quotes.
WLK_IKE_CLAUSE = ("To provide funds for paying the Costs of the Projects, the Authority agrees, as "
                  "soon as practicable after the execution of this Agreement, that it will issue, "
                  "sell and deliver the Bonds in the aggregate principal amount of $65,000,000")
PRINCIPAL = "Principal / commitment amount"


SELECTOR_FIX = ROOT / "tests" / "fixtures" / "covenant_selector"


def _frozen(name: str) -> dict[str, typing.Any]:
    """A frozen copy of committed page data (`tests/fixtures/covenant_selector/README.md`)."""
    out: dict[str, typing.Any] = json.loads((SELECTOR_FIX / f"{name}.json").read_text())
    return out


def _wlk_with_ike() -> dict[str, typing.Any]:
    """WLK's committed page, hosting its FROZEN capital structure (round 1 of #1091's review: a
    value is pinned on a frozen fixture, never on the living page), plus ONE DERIVED row: its GO
    Zone principal row (`dex101.htm`, $89m) copied to the IKE Zone agreement beside it
    (`dex102.htm`), with that exhibit's own real clause and figure, placed right after GO Zone's
    rows, as the loop sends `dex102.htm` right after `dex101.htm`: the page as WLK's next paid
    build would write it."""
    page = _committed("WLK")
    page["mechanical"]["capital_structure"] = _frozen("WLK")["capital_structure"]
    rows = page["mechanical"]["capital_structure"]["covenant_term_rows"]["value"]
    go = next(r for r in rows if r["name"] == PRINCIPAL
              and f"{WLK_ACC} · dex101.htm" in (r["value"].get("source_ref") or ""))
    assert go["value"]["value"] == "$89,000,000" and go["agreement_title"] == "LOAN AGREEMENT"
    ike = copy.deepcopy(go)
    ike["value"].update(value="$65,000,000", source_ref=f"8-K {WLK_ACC} · dex102.htm",
                        note=f"verbatim: “{WLK_IKE_CLAUSE}”")
    last = max(i for i, r in enumerate(rows) if f"{WLK_ACC} · dex101.htm" in (
        (r["value"].get("source_ref") or "") + " " + (r["value"].get("note") or "")))
    rows.insert(last + 1, ike)
    return page


def _principals(page: dict[str, typing.Any]) -> dict[str, tuple[str, str, str]]:
    """file → (group label, governing value, base_ref) of each 2010-filing principal group."""
    cs = CapitalStructure.model_validate(page["mechanical"]["capital_structure"])
    assert cs.covenant_term_rows is not None and cs.covenant_pointer_rows is not None
    out = {}
    for g in ce.governing_terms(list(cs.covenant_term_rows.value or []),
                                list(cs.covenant_pointer_rows.value or [])):
        if g.term == PRINCIPAL and WLK_ACC in (g.value.source_ref or ""):
            out[(g.value.source_ref or "").rsplit(" · ", 1)[1]] = (
                g.family, str(g.value.value), g.base_ref or "")
    return out


def test_two_exhibits_of_one_filing_never_share_a_group_wlk() -> None:
    """(+) WLK's 2010 filing sends two different bond loan agreements, GO Zone ($89m) and IKE Zone
    ($65m), both "LOAN AGREEMENT" of November 1, 2010 under one pointer family. Each now governs
    its own group, labelled with its file, citing its own base. In one group, IKE's value governed
    and GO Zone's base was cited for it."""
    got = _principals(_wlk_with_ike())
    assert set(got) == {"dex101.htm", "dex102.htm"}, got
    (fam1, v1, b1), (fam2, v2, b2) = got["dex101.htm"], got["dex102.htm"]
    assert (v1, v2) == ("$89,000,000", "$65,000,000")
    assert b1.endswith(f"{WLK_ACC} · dex101.htm") and b2.endswith(f"{WLK_ACC} · dex102.htm")
    assert fam1 != fam2 and fam1.endswith(" · dex101.htm") and fam2.endswith(" · dex102.htm")
    assert fam1.removesuffix(" · dex101.htm") == fam2.removesuffix(" · dex102.htm")


def test_each_exhibit_prints_its_own_value_on_both_renderers_wlk_e2e(
        tmp_path: pathlib.Path) -> None:
    """(+) END TO END, WLK's page with the derived IKE row through `render_markdown` and the
    production `renderDossier`: each agreement's covenant table states its own principal, and the
    web table row equals the Markdown one."""
    from tests.test_covenant_refused_newer import _md_row, _node_render, _norm, _web_row
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    page = _wlk_with_ike()
    md = render_markdown(Dossier.model_validate(page))
    web = _node_render(tmp_path, "WLK", host=page)
    for doc, figure in (("dex101.htm", "$89,000,000"), ("dex102.htm", "$65,000,000")):
        fam = _principals(page)[doc][0]
        row = _md_row(md, fam, PRINCIPAL)
        assert figure in " ".join(row), (fam, row)
        assert _web_row(web, fam, PRINCIPAL) == [_norm(x) for x in row]


def _split_only_where_one_filing_pairs(cs: CapitalStructure) -> None:
    """THE INVARIANT a page holds, whatever its next build sends (round 1 of #1091's review): a
    governing group is labelled with a file ONLY when that file is one of two or more files of one
    filing among the page's term rows, and no group governs with one file of a filing while it
    cites another file of the same filing as its base."""
    rows = list(cs.covenant_term_rows.value or []) if cs.covenant_term_rows else []
    files: dict[str, set[str]] = {}
    for r in rows:
        acc, doc = ce._exhibit_of(r)
        if acc and doc:
            files.setdefault(acc, set()).add(doc)
    pairs = {doc for docs in files.values() if len(docs) > 1 for doc in docs}
    gov = ce.governing_terms(rows, list((cs.covenant_pointer_rows.value or [])
                                        if cs.covenant_pointer_rows else []))
    for g in gov:
        named = g.family.rsplit(" · ", 1)[-1] if " · " in g.family else ""
        assert named not in {d for docs in files.values() for d in docs} or named in pairs, g.family
        base = ce._EXHIBIT_RE.search(g.base_ref or "")
        shown = ce._EXHIBIT_RE.search(g.value.source_ref or g.value.note or "")
        if base and shown and base.group(1) == shown.group(1):
            assert base.group(2) == shown.group(2), (g.family, g.term, g.base_ref, shown.group(0))


def test_a_group_splits_only_where_one_filing_carries_two_exhibits_every_page() -> None:
    """(− · living corpus) Every committed page holds the invariant, today and after any paid
    build: today none sends two exhibits of one filing, so none splits; WLK's and PARR's next builds
    will split by design (round 1 of #1091's review: the pin was "no page splits", which those
    builds would turn red)."""
    pages = 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        raw = json.loads(p.read_text()).get("mechanical", {}).get("capital_structure")
        if raw:
            _split_only_where_one_filing_pairs(CapitalStructure.model_validate(raw))
            pages += 1
    assert pages


def test_a_group_splits_only_where_one_filing_carries_two_exhibits_wlk_next_build() -> None:
    """(+) The same invariant on WLK's page as its next paid build would write it (`_wlk_with_ike`):
    the GO Zone and IKE Zone agreements of one filing split, each governing its own value. At main's
    `governing_terms` this page breaks the invariant: one group governs with IKE's `dex102.htm`
    and cites GO Zone's `dex101.htm` as its base."""
    _split_only_where_one_filing_pairs(
        CapitalStructure.model_validate(_wlk_with_ike()["mechanical"]["capital_structure"]))


# --- #1090 verification's N1 and N3, deferred to this PR ------------------------------------------

#: UBER's REAL recital (`0001552781-21-000058 · e21071_ex10-1.htm`, EDGAR cache).
UBER_RECITAL = ("that certain Term Loan Agreement, dated as of July 13, 2016 (as amended by that "
                "certain Amendment No. 1 to the Term Loan Agreement, dated as of June 13, 2018 and "
                "as further amended, restated, extended, supplemented or otherwise modified from "
                "time to time prior to the date hereof, the “ Existing 2016 Loan Agreement ”)")
#: A DERIVED displacing clause, so the bind reaches `displaced_agreements` (the review's own).
UBER_ENDS = "On the Effective Date the Existing 2016 Loan Agreement shall be terminated."


def test_n1_a_recital_binds_the_agreement_not_its_amendments_date_uber() -> None:
    """(+ / −) N1, UBER's real recital. "Existing 2016 Loan Agreement" is the Term Loan Agreement of
    July 13, 2016. "Amendment No. 1 to the Term Loan Agreement, dated as of June 13, 2018" is its
    history: an amendment named in the gap, never a second agreement, and the June 13, 2018 date
    is the amendment's. At #1090's head the term bound to 2018-06-13 only: the gap's chain broke at
    "No." and refused the true bind, and a recital restarting inside the amendment's name bound
    the amendment's date."""
    keys = [d.key for d in ce.displaced_agreements(f"{UBER_RECITAL} … {UBER_ENDS}")]
    assert keys == [ce.AgreementKey("TERM LOAN AGREEMENT", ce.date(2016, 7, 13))], keys
    assert not ce._second_agreement("as amended by that certain Amendment No. 1 to the Term Loan "
                                    "Agreement, dated as of June 13, 2018 and as further amended")


NKE_RECITALS = (
    "(as amended by the First Amendment to the Credit Agreement, dated as of March 8, 2024, the “ "
    "2022 Credit Agreement ”)",
    "(as amended by that certain Amendment No. 1 to the Credit Agreement, dated as of March 8, "
    "2024, the “ 2022 Credit Agreement ”)",
    # round 1 of #1091's review: any instrument TO the agreement is its history, not only an
    # amendment
    "(as supplemented by the Joinder Agreement to the Credit Agreement, dated as of March 8, 2024, "
    "the “ 2022 Credit Agreement ”)",
    "(as modified by the Waiver to the Credit Agreement, dated as of March 8, 2024, the “ 2022 "
    "Credit Agreement ”)",
    "(as modified by the Consent to the Credit Agreement, dated as of March 8, 2024, the “ 2022 "
    "Credit Agreement ”)",
    "(as supplemented by the Incremental Assumption Agreement to the Credit Agreement, dated as of "
    "March 8, 2024, the “ 2022 Credit Agreement ”)",
)


@pytest.mark.parametrize("history", NKE_RECITALS, ids=["first-amendment", "amendment-no-1",
                                                     "joinder", "waiver", "consent",
                                                     "incremental-assumption"])
def test_n1_an_amendments_date_never_displaces_a_live_agreement_of_that_day_nke(
        history: str) -> None:
    """(−) N1, DERIVED from NKE's real five-year agreement, which defines its "2022 Credit
    Agreement" and requires it "has been, or concurrently … will be, terminated". A recital is
    added carrying the 2022 agreement's amendment history in two common forms. That amendment is
    dated March 8, 2024, the day of NKE's 2024 364-day CREDIT AGREEMENT. Only the 2022 agreement is
    displaced, never an agreement of the amendment's date: at #1090's head the 2024 agreement, live
    then, read superseded."""
    five = _fixture("NKE")["texts"][NKE_FIVE] or ""
    recital = ("WHEREAS, the Company is party to that certain Credit Agreement, dated as of "
               f"March 11, 2022 {history}; ")
    keys = {d.key for d in ce.displaced_agreements(f"{recital} … {five}")}
    assert ce.AgreementKey("CREDIT AGREEMENT", ce.date(2022, 3, 11)) in keys, keys
    assert ce.AgreementKey("CREDIT AGREEMENT", ce.date(2024, 3, 8)) not in keys, keys


def _epam_rows() -> list[typing.Any]:
    """EPAM's frozen pointer rows, as the real type."""
    from vinci.dossier.schemas import CovenantPointer
    return [CovenantPointer.model_validate(r)
            for r in _frozen("EPAM")["covenant_pointer_rows"]["value"]]


def _layer(rows: list[typing.Any]) -> CapitalStructure:
    """A capital-structure layer carrying only ``rows`` as its located pointers."""
    from vinci.dossier.schemas import Sourced
    u = Sourced[str].unknown(note="n/a")
    return CapitalStructure(
        instruments=Sourced.unknown(note="n/a"), summary=u, detail_as_of="n/a", maturity_filings=u,
        covenant_pointers=Sourced.present(f"{len(rows)} pointers", source_ref="EDGAR"),
        covenant_pointer_rows=Sourced.present(rows, source_ref="EDGAR"), covenant_terms=u)


class _Records:
    """An SEC stub that records every URL read and serves nothing (each read fails)."""

    def __init__(self) -> None:
        self.urls: list[str] = []

    def get_text(self, url: str, **_: typing.Any) -> str:
        self.urls.append(url)
        raise OSError("stub: nothing served")


def test_n3_an_image_is_never_read_or_targeted_epam() -> None:
    """(−) N3, EPAM's pointer rows, FROZEN (round 1 of #1091's review): its 2026 10-K row lists six
    page images (`.jpg`) beside the exhibit it targets. An image holds no text: it is never fetched
    and never a target, so one that cannot be fetched never switches the page to "supersedes
    nothing". At #1090's head all six were fetched as siblings."""
    fx = _frozen("EPAM")
    rows = _epam_rows()
    cs = _layer(rows)
    images = [f for r in rows for f in r.exhibits if f.lower().endswith(".jpg")]
    assert len(images) == 6, images
    http = _Records()
    *_, outcomes = ce.extract_covenant_terms(cs, llm=typing.cast(typing.Any, None),
                                             http=typing.cast(typing.Any, http), cik=fx["cik"],
                                             ticker="EPAM", name=fx["name"])
    assert http.urls and not any(u.lower().endswith(".jpg") for u in http.urls), http.urls
    assert outcomes is not None
    assert not any(o.filename.lower().endswith(".jpg") for o in outcomes.value or [])
    assert not any(f.lower().endswith(".jpg") for _r, f, _p in ce._located_exhibits(rows))


def test_n3_an_image_listed_first_is_never_the_primary() -> None:
    """(−) N3, DERIVED from EPAM's real 10-K row (frozen) with its images moved ahead of its
    document: the primary is still the document, never a page image."""
    rows = [r.model_copy(update={"exhibits": sorted(r.exhibits,
                                                    key=lambda f: not f.endswith(".jpg"))})
            for r in _epam_rows()]
    assert any(r.exhibits and r.exhibits[0].endswith(".jpg") for r in rows)
    assert not any(f.endswith(".jpg") for _r, f in ce._core_agreement_exhibits(rows))


def test_past_the_guard_every_primary_is_sent_before_any_sibling_amzn(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) The round-robin's purpose survives the selector (code review): every family's primary is
    sent before any filing's second exhibit, so a row listing many exhibits that govern debt cannot
    spend the guard on one facility while other facilities' primaries go unsent. AMZN's real
    fixture with the guard lowered to 2 calls: its 2023 five-year agreement and its next family's
    primary are sent, and the 364-day agreement beside the five-year one is the one past the guard.
    Outcomes stay in the located order."""
    monkeypatch.setattr(ce, "_MAX_EXHIBITS", 2)
    r = _run("AMZN")
    sibling = "0001104659-23-113444 · tm2329405d1_ex10-2.htm"
    assert r.sent[0] == "0001104659-23-113444 · tm2329405d1_ex10-1.htm", r.sent
    assert sibling not in r.sent and r.by[sibling].outcome == "cost_bound", r.sent
    assert len(r.sent) == 2
