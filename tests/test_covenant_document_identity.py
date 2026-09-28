"""A covenant exhibit is identified by the DOCUMENT, not by the search that found it.

`_covenant_pointers` locates execution filings with a CLASS-GENERIC efts phrase ("Indenture",
"Credit Agreement"). Two instrument families sharing a phrase therefore partition ONE hit list
under a global `seen` set, and the second family is handed whatever the first did not take — the
label comes from arrival order, not evidence. Measured 2026-09-28 over the 26 committed dossiers,
11 have >=2 agreement-class families on one phrase, and the consequence reached the pages:

    BURL  ABL amendment (position 14 of "Indenture")  ->  labelled "Convertible Senior Notes 2.25%"
    VRRM  Amended & Restated Revolving Credit Agmt    ->  labelled "2021 Term Loan Due 2028"
    WERN  STOCK PURCHASE AGREEMENT                    ->  labelled "22 Unsecured Credit Agreement"
    NKE   a CFO OFFER LETTER                          ->  fed to the covenant extractor
    TGT   a CEO TRANSITION LETTER                     ->  fed to the covenant extractor

Every head below is the real first ~600 chars of the named EDGAR exhibit (public filings, not
licensed data). The corpus measurement behind these pins: 144 located exhibit heads across 24
names -> 68 kept, 76 refused, 0 non-debt titles wrongly kept.
"""

from __future__ import annotations

from vinci.dossier import covenant_extract
from vinci.dossier.covenant_extract import (
    agreement_title,
    governing_terms,
    is_amendment,
    is_debt_agreement,
)
from vinci.dossier.mechanical import _COVENANT_CLASS_RE
from vinci.dossier.schemas import (
    CapitalStructure,
    CovenantPointer,
    CovenantTerm,
    Sourced,
)

# BURL 0001193125-25-168007 — the ABL amendment that was published as a convertible note.
BURL_SIXTH = (
    "EX-10.1 2 d946952dex101.htm EX-10.1 EX-10.1 Exhibit 10.1 EXECUTION VERSION SIXTH AMENDMENT "
    "TO SECOND AMENDED AND RESTATED CREDIT AGREEMENT SIXTH AMENDMENT TO SECOND AMENDED AND "
    "RESTATED CREDIT AGREEMENT (this “ Amendment ”) dated as of July 25, 2025 by and amo")
# BURL 0001193125-22-200058 — an EARLIER amendment to the SAME contract.
BURL_FOURTH = (
    "EX-10.1 2 d393601dex101.htm EX-10.1 EX-10.1 Exhibit 10.1 FOURTH AMENDMENT TO SECOND AMENDED "
    "AND RESTATED CREDIT AGREEMENT FOURTH AMENDMENT TO SECOND AMENDED AND RESTATED CREDIT "
    "AGREEMENT (this “ Amendment ”) dated as of July 20, 2022 by and among BURLINGTON")
# WERN 0000793074-26-000090 — a real agreement, but not a debt one.
WERN_SPA = (
    "EX-10.1 2 wern-20260127ex101.htm EX-10.1 wern-20260127ex101 Execution Version 4907-7785-"
    "9703.29 ____________________________ STOCK PURCHASE AGREEMENT ______________________ by "
    "and among WERNER ENTERPRISES, INC., MARY B. WILSON, GARY L. WILSON FAMILY TRUS")
# NKE 0000320187-26-000088 — not an agreement at all.
NKE_OFFER_LETTER = (
    "EX-10.29 2 nke-5312026exhibit1029.htm EX-10.29 Document June 16, 2026 Dear David, This "
    "letter and your signature below confirm your acceptance of the offer for the position of "
    "Executive Vice President and Chief Financial Officer (“ CFO ”) of NIKE, Inc.")
# NFLX 0001193125-09-194962 — a plain credit agreement, no "(this ...)" anchor.
NFLX_CREDIT = (
    "EX-10.1 2 dex101.htm CREDIT AGREEMENT Credit Agreement Exhibit 10.1 CREDIT AGREEMENT among "
    "NETFLIX, INC., THE LENDERS NAMED HEREIN, and WELLS FARGO BANK, NATIONAL ASSOCIATION, as "
    "Administrative Agent and L/C Issuer, and WELLS FARGO SECURITIES, LLC, as Lead Arr")
# CNXC 0000200107 — an amendment whose own title never names its contract.
CNXC_AR = (
    "EX-10.1 2 form8-k04x26x23exhibit101.htm EX-10.1 Document Exhibit 10.1 EXECUTION VERSION "
    "AMENDMENT AND RESTATEMENT AGREEMENT dated as of April 21, 2023 (this “ Agreement ”), "
    "among CONCENTRIX CORPORATION, a Delaware corporation (the “ Borrower ”), the LENDERS "
    "party hereto, the L/C ISSUERS party hereto, JPMORGAN CHASE BANK, N.A., as successor "
    "administrative agent, and BANK OF AMERICA, N.A., as the Existing Administrative Agent. "
    "WHEREAS, reference is made to that certain Credit Agreement dated as of October 16, 2020")


def test_an_amendment_groups_with_the_contract_it_amends() -> None:
    """(+) The governing collapse keys on the family, so an amendment MUST normalise to its base or
    it stops superseding: BURL's Fourth and Sixth Amendments would both read as governing."""
    sixth, fourth = agreement_title(BURL_SIXTH), agreement_title(BURL_FOURTH)
    assert sixth == "SECOND AMENDED AND RESTATED CREDIT AGREEMENT", sixth
    assert sixth == fourth, f"the amendment chain breaks: {sixth!r} vs {fourth!r}"
    assert "SIXTH" not in sixth and "FOURTH" not in (fourth or ""), "the INSTANCE must be stripped"


def test_the_title_is_read_without_a_this_anchor() -> None:
    """(+) NFLX's credit agreement has no '(this "Agreement")' clause. An earlier draft anchored on
    that and matched 15 of 94 exhibits — a rule generalised from three BURL documents."""
    assert agreement_title(NFLX_CREDIT) == "CREDIT AGREEMENT"


def test_an_amendment_that_never_names_its_contract_recovers_the_base() -> None:
    """(+) 'AMENDMENT AND RESTATEMENT AGREEMENT' carries no debt word; the contract is named in the
    recital that follows. Without the recovery this real credit amendment is refused."""
    got = agreement_title(CNXC_AR)
    assert got == "CREDIT AGREEMENT", got
    assert is_debt_agreement(got)


def test_a_non_debt_agreement_is_refused() -> None:
    """(-) WERN's pointer called this an unsecured credit agreement. It is a stock purchase
    agreement, and a covenant extractor must never see it."""
    got = agreement_title(WERN_SPA)
    assert got == "STOCK PURCHASE AGREEMENT", got
    assert not is_debt_agreement(got), "a purchase agreement is not a debt contract"


def test_a_document_that_is_not_an_agreement_is_refused() -> None:
    """(-) An executive offer letter declares no agreement. It must yield no title at all, rather
    than a nearest-match one that would then be published as an instrument's covenant terms."""
    assert agreement_title(NKE_OFFER_LETTER) is None
    assert not is_debt_agreement(agreement_title(NKE_OFFER_LETTER))


def test_a_real_word_is_not_eaten_as_a_leading_code() -> None:
    """(-) OVER-STRIPPING REGRESSION. The CUSIP strip is '6+ alphanumerics', which also matches
    'AMENDED' (7 caps) and silently returned 'AND RESTATED CREDIT AGREEMENT'. The token must
    contain a DIGIT; a hyphenated one ('364-DAY') is part of the contract's real name."""
    amzn = ("Deal CUSIP Number: 02313HAE0 Revolving Credit Facility CUSIP Number: 02313HAF7 "
            "AMENDED AND RESTATED CREDIT AGREEMENT Dated as of")
    assert agreement_title(amzn) == "AMENDED AND RESTATED CREDIT AGREEMENT"
    day = "Exhibit 10.1 65410VAW81 364-DAY CREDIT AGREEMENT among"
    assert agreement_title(day) == "364-DAY CREDIT AGREEMENT"


def test_a_revolving_facility_is_agreement_class() -> None:
    """(+/-) The stem fix. `\\bfacilit\\b` never matched 'Facility', so three real revolvers were
    published as aggregate line items with 'no contract-level filing expected'. The genuine
    aggregates must STAY generic — that is what the note is for."""
    for real in ("ABL Senior Secured Revolving Facility", "Securitization Facility",
                 "Senior Unsecured Revolving Loans", "Convertible Bonds"):
        assert _COVENANT_CLASS_RE.search(real), f"{real} must reach a contract search"
    for aggregate in ("Finance Lease Obligations", "Operating Lease Liabilities",
                      "Short-term Promissory Note"):
        assert not _COVENANT_CLASS_RE.search(aggregate), f"{aggregate} has no contract to find"


def _term(name: str, value: str, acc: str, title: str | None,
          amend: bool | None = None) -> CovenantTerm:
    return CovenantTerm(
        name=name,
        value=Sourced.present(value, source_ref=f"8-K {acc} · ex.htm"),
        agreement_title=title,
        agreement_is_amendment=amend,
    )


def test_the_document_outranks_the_pointers_guess_when_grouping() -> None:
    """(+) END-TO-END through the collapse that feeds the render's headings. Two pointers claim two
    DIFFERENT instruments; both documents are the same contract. The terms must land in ONE group
    named by the document, and the later amendment must govern — which is exactly what the pointer
    labels prevented: BURL's two amendments sat under a convertible note and a term loan."""
    base = "SECOND AMENDED AND RESTATED CREDIT AGREEMENT"
    rows = [
        # BOTH ARE AMENDMENTS to the one contract — that is why a title may merge them across two
        # different guessed instruments. Two BASE documents sharing a title must NOT merge; see
        # test_two_base_contracts_sharing_a_title_do_not_merge.
        _term("Maturity date", "December 22, 2026", "0001193125-22-200058", base, True),
        _term("Maturity date", "July 25, 2030", "0001193125-25-168007", base, True),
    ]
    pointers = [
        CovenantPointer(family="Convertible Senior Notes 2.25%", filing="8-K",
                        filing_date="2022-07-22", accession="0001193125-22-200058",
                        exhibits=["ex.htm"]),
        CovenantPointer(family="Senior Secured Term Loan Facility", filing="8-K",
                        filing_date="2025-07-29", accession="0001193125-25-168007",
                        exhibits=["ex.htm"]),
    ]
    got = governing_terms(rows, pointers)
    assert len(got) == 1, f"one contract must collapse to one group, got {[g.family for g in got]}"
    assert got[0].family == base, got[0].family
    assert "Convertible" not in got[0].family and "Term Loan" not in got[0].family
    assert got[0].value.value == "July 25, 2030", "the LATER amendment governs"


def test_a_row_without_a_read_title_still_groups_by_the_pointer() -> None:
    """(-) BACKWARD COMPATIBILITY. A dossier assembled before the title was read carries None, and
    must keep grouping as it did — the fallback is not allowed to collapse those into one bucket."""
    rows = [_term("Maturity date", "2027", "0001193125-20-109457", None)]
    pointers = [CovenantPointer(family="Convertible Senior Notes 1.25%", filing="8-K",
                                filing_date="2020-04-16", accession="0001193125-20-109457",
                                exhibits=["ex.htm"])]
    assert governing_terms(rows, pointers)[0].family == "Convertible Senior Notes 1.25%"


def test_an_unread_title_is_omitted_from_the_serialized_artifact() -> None:
    """(-) ARTIFACT STABILITY. `refresh_dossier` compares serialized text, so a new optional field
    that always serializes would rewrite every committed dossier on the next pass and bury the real
    diff. Absent when unread; present the moment it is read."""
    assert "agreement_title" not in _term("Maturity date", "2027", "acc", None).model_dump()
    assert _term("Maturity date", "2027", "acc", "CREDIT AGREEMENT").model_dump()[
        "agreement_title"] == "CREDIT AGREEMENT"


def test_a_debt_word_inside_a_non_debt_contract_is_still_refused() -> None:
    """(-) THE OVERLAP CASE, and the one that makes the refusal list load-bearing. A tax receivables
    agreement (FUBO, VRRM) contains 'RECEIVABLES', which IS a debt word — so a gate that only asked
    'does a debt word appear?' would admit it. Testing a title with NO debt word (a stock purchase
    agreement) cannot catch that: it is refused either way."""
    assert not is_debt_agreement("TAX RECEIVABLES AGREEMENT")
    assert not is_debt_agreement("RESTRICTED STOCK UNIT AWARD AGREEMENT")
    assert is_debt_agreement("ASSET-BASED REVOLVING CREDIT AGREEMENT"), "a real one must pass"


def test_a_non_debt_document_never_reaches_the_extractor(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """(-) END-TO-END through `extract_covenant_terms`, which is where the refusal actually lives.
    The unit pins above all passed while the gate itself was deleted — they exercise the two
    predicates, never the branch. NKE's pointer really does aim at a CFO offer letter; the extractor
    must not be called on it, and the refusal must be FLAGGED rather than silent."""
    seen: list[dict[str, object]] = []

    class _Llm:
        def extract(self, **kw: object) -> dict[str, object]:
            seen.append(kw)
            return {"terms": [{"name": "Maturity date", "present": True, "value": "2030"}]}

    monkeypatch.setattr(covenant_extract, "_fetch_exhibit", lambda *a, **k: NKE_OFFER_LETTER)
    ptr = CovenantPointer(family="material contracts (10-K exhibit index)", filing="latest 10-K",
                          filing_date="2026-07-24", accession="0000320187-26-000088",
                          exhibits=["nke-5312026exhibit1029.htm"])
    cs = CapitalStructure(
        instruments=Sourced.unknown(note="n/a"), summary=Sourced.unknown(note="n/a"),
        detail_as_of="n/a", maturity_filings=Sourced.unknown(note="n/a"),
        covenant_pointers=Sourced.present("1 pointer", source_ref="EDGAR"),
        covenant_pointer_rows=Sourced.present([ptr], source_ref="EDGAR"),
        covenant_terms=Sourced.unknown(note="n/a"),
    )
    rows, summary, flags, _log = covenant_extract.extract_covenant_terms(
        cs, llm=_Llm(), http=None, cik="0000320187", ticker="NKE", name="NIKE, Inc.")

    assert not seen, "an executive offer letter was sent to the covenant extractor"
    assert rows is None, "a refused document must yield no covenant rows"
    assert any("not a debt agreement" in f for f in flags), flags
    assert any("no agreement at all" in f for f in flags), "the refusal states what it found"


# --- REVIEW FIXES (2026-09-28) — three document classes the first gate refused wrongly ----------
# Each pin below is a document the gate MUST see. All three were REFUSED by the shipped gate:
# a bare "INDENTURE" head yielded no title at all, "TRUST INDENTURE" tripped a bare \bTRUST\b,
# and a securities purchase agreement / warrant carried no word in the debt list — although
# `_CORE_AGREEMENT` names ``securitiespurchase`` and ``warrant`` as exhibits to FETCH.

# UBER 0001552781-21-000027 shape — the canonical note-indenture head: the title is ONE word, and
# `_TITLE` needs a word BEFORE the noun, so it matched nothing.
BARE_INDENTURE = (
    "EX-4.1 2 e21027_ex4-1.htm EX-4.1 Exhibit 4.1 EXECUTION VERSION INDENTURE Dated as of "
    "March 5, 2021 UBER TECHNOLOGIES, INC., as Issuer and U.S. BANK NATIONAL ASSOCIATION, as "
    "Trustee 0.00% Convertible Senior Notes due 2025")


def test_a_bare_indenture_head_is_still_an_agreement() -> None:
    """(+) An indenture is THE convertible document this extractor exists for, and its head is
    routinely the single word 'INDENTURE'. Refusing it loses the conversion terms outright."""
    got = agreement_title(BARE_INDENTURE)
    assert got == "INDENTURE", got
    assert is_debt_agreement(got)


def test_the_bare_noun_is_anchored_at_the_head() -> None:
    """(-) The fallback must not scavenge a noun from the BODY — an offer letter that happens to
    mention an indenture downstream is still not an agreement."""
    assert agreement_title(NKE_OFFER_LETTER) is None
    assert agreement_title(
        "Dear David, This letter confirms your offer. See the Indenture for details.") is None


def test_a_trust_indenture_is_a_debt_agreement() -> None:
    """(-) OVERLAP, the other way round. 'TRUST' is a non-debt word (voting trust, trust agreement)
    but a bond's own contract is titled 'TRUST INDENTURE'. The refusal list must not eat it."""
    assert is_debt_agreement("TRUST INDENTURE")
    assert is_debt_agreement("INDENTURE OF TRUST")
    assert not is_debt_agreement("VOTING TRUST AGREEMENT"), "a voting trust is still refused"
    assert not is_debt_agreement("TRUST AGREEMENT")


def test_the_convertible_issuance_documents_reach_the_extractor() -> None:
    """(+) `_CORE_AGREEMENT` deliberately FETCHES ``securitiespurchase``/``notepurchase``/
    ``warrant``
    exhibits — MVST's convertible original is a securities purchase agreement. A gate that then
    refuses them makes the selector fetch documents it can never extract from."""
    for fetched in ("SECURITIES PURCHASE AGREEMENT", "NOTE PURCHASE AGREEMENT",
                    "WARRANT AGREEMENT"):
        assert is_debt_agreement(fetched), f"{fetched} is a targeted core exhibit"
    assert not is_debt_agreement("STOCK PURCHASE AGREEMENT"), "an equity SPA is still refused"
    assert not is_debt_agreement("SUBSCRIPTION AGREEMENT")


# --- a title may RELABEL a group, never MERGE two contracts ------------------------------------
# #652 grouped on the title alone. Review demonstrated the cost: two convertible series whose
# indentures are both titled "INDENTURE" collapsed into one group, the earlier series' conversion
# price vanished, and the later indenture was published as an `amended_by` of it. Silent data loss
# plus a fabricated supersession — worse, for that case, than the mislabelling it replaced.

def _row(name: str, val: str, acc: str, title: str | None, amend: bool | None) -> CovenantTerm:
    return CovenantTerm(name=name, value=Sourced.present(val, source_ref=f"8-K {acc} · ex.htm"),
                        agreement_title=title, agreement_is_amendment=amend)


def _ptr(family: str, acc: str, when: str) -> CovenantPointer:
    return CovenantPointer(family=family, filing="8-K", filing_date=when, accession=acc,
                           exhibits=["ex.htm"])


def test_two_base_contracts_sharing_a_title_do_not_merge() -> None:
    """(+) THE DEMONSTRATED BUG. Two convertible SERIES, each with its own indenture, both heads
    titled "INDENTURE". They must stay two groups with both values intact and no amendment
    relationship invented between them."""
    rows = [_row("Conversion price", "$12.34", "0001000000-21-100000", "INDENTURE", False),
            _row("Conversion price", "$56.78", "0001000000-22-200000", "INDENTURE", False)]
    ptrs = [_ptr("2025 Convertible Notes", "0001000000-21-100000", "2021-03-01"),
            _ptr("2027 Convertible Notes", "0001000000-22-200000", "2022-05-01")]
    got = governing_terms(rows, ptrs)
    assert len(got) == 2, f"two contracts collapsed into {len(got)}"
    assert {g.value.value for g in got} == {"$12.34", "$56.78"}, "a conversion price was deleted"
    for g in got:
        assert not getattr(g, "amended_by", ()), "an amendment relationship was fabricated"


def test_amendments_to_one_contract_still_merge_across_guessed_instruments() -> None:
    """(+) THE CASE THE TITLE EXISTS FOR, and the one the fix must not break. BURL's amendments
    arrive under different guessed instruments; they are one facility and must collapse, with the
    later amendment governing."""
    base = "SECOND AMENDED AND RESTATED CREDIT AGREEMENT"
    rows = [_row("Maturity date", "December 22, 2026", "0001193125-22-200058", base, True),
            _row("Maturity date", "July 25, 2030", "0001193125-25-168007", base, True)]
    ptrs = [_ptr("Convertible Senior Notes 2.25%", "0001193125-22-200058", "2022-07-22"),
            _ptr("Senior Secured Term Loan Facility", "0001193125-25-168007", "2025-07-29")]
    got = governing_terms(rows, ptrs)
    assert len(got) == 1 and got[0].family == base, [g.family for g in got]
    assert got[0].value.value == "July 25, 2030", "the later amendment must govern"


def test_two_bases_under_one_pointer_family_are_left_alone() -> None:
    """(-) THE RULE MUST NOT OVER-FIRE. Nike's two successive 364-day agreements share a pointer
    family, so they were ALREADY one group before titles existed — a renewal collapsing onto its
    predecessor is pre-existing behaviour, not something to change here. Withholding the title must
    key on bases from DIFFERENT families, not on 'more than one base'."""
    title = "364-DAY CREDIT AGREEMENT"
    rows = [_row("Maturity date", "2025", "0000320187-25-000008", title, False),
            _row("Maturity date", "2026", "0000320187-26-000020", title, False)]
    fam = "364-day Committed Credit Facility"
    got = governing_terms(rows, [_ptr(fam, "0000320187-25-000008", "2025-01-01"),
                                 _ptr(fam, "0000320187-26-000020", "2026-01-01")])
    assert len(got) == 1, "a same-family renewal pair must stay one group"
    # AND IT MUST STILL BE NAMED BY THE DOCUMENT. Asserting only the COUNT cannot see an
    # over-firing withhold: falling back to the pointer family here also yields one group, just
    # under the guessed name — which is the whole thing this change exists to stop publishing.
    assert got[0].family == title, (
        f"the title was withheld although both bases share one family — got {got[0].family!r}")


def test_an_amendment_is_read_from_the_head_not_the_body() -> None:
    """(-) A base agreement's BODY is full of the word 'amendment' — amendment clauses, defined
    terms, 'no amendment shall be effective unless'. Searching the document would call almost
    everything an amendment and re-open the merge from the other side."""
    assert is_amendment(BURL_SIXTH)
    assert not is_amendment(NFLX_CREDIT)
    body = ("Exhibit 10.1 CREDIT AGREEMENT dated as of May 1, 2024 among ACME, INC. "
            + "Section 9.1 Amendments. No amendment to this Agreement shall be effective. " * 12)
    assert not is_amendment(body), "an amendment CLAUSE is not an amendment DOCUMENT"


def test_a_leading_year_survives_because_it_distinguishes_facilities() -> None:
    """(-) '2021 CREDIT AGREEMENT' and '2024 CREDIT AGREEMENT' are different facilities; stripping
    the year manufactures the collision the collapse then has to resolve. A CUSIP and an amount
    fragment are still stripped."""
    assert agreement_title("Exhibit 10.1 2021 CREDIT AGREEMENT among X") == "2021 CREDIT AGREEMENT"
    assert agreement_title("Exhibit 10.1 000 CREDIT AGREEMENT among X") == "CREDIT AGREEMENT"
    assert agreement_title(
        "Exhibit 10.1 65410VAW81 364-DAY CREDIT AGREEMENT among X") == "364-DAY CREDIT AGREEMENT"


def test_an_unread_amendment_flag_is_omitted_from_the_artifact() -> None:
    """(-) Same artifact-stability contract as the title: absent until read, so a committed dossier
    does not churn on the next pass."""
    unread = _row("m", "v", "a", "CREDIT AGREEMENT", None).model_dump()
    assert "agreement_is_amendment" not in unread
    assert _row("m", "v", "a", "CREDIT AGREEMENT", True).model_dump()["agreement_is_amendment"]
