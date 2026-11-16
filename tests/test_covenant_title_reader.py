"""E5 reads a title-cased debt-agreement heading as it reads a capitals one (STATE row 63).

`agreement_title` read only capitals headings, so five real debt contracts on committed pointer
rows read as no title and were refused before any model call:
- VRRM's Amendment No. 4 to its Revolving Credit Agreement (a revolver VRRM amended and restated
  on 2025-10-17, so this amendment is superseded; see the record);
- CNXC's Third and Fourth Amendments to its Receivables Financing Agreement;
- NFLX's two senior-notes purchase agreements.

Two failure shapes, one root (`_TITLE`'s words and nouns are capitals only):
- A: a title-cased AMENDMENT heading naming its contract ("Third Amendment to Receivables Financing
  Agreement"; VRRM's mixed "Amendment No. 4 to REVOLVING CREDIT Agreement");
- B: a title-cased heading led by the issuer, the amount and the coupon, with a note's maturity in
  lowercase ("NETFLIX, INC. $1,900,000,000 5.875% Senior Notes due 2028 Purchase Agreement").

Every head here is a real one: `tests/fixtures/covenant_title_reader/heads.json` (see its README)
holds the first characters `_fetch_exhibit` returns for each exhibit E5 refused as not a debt
agreement on the 24 committed pages with pointer rows at main 032d2fde, plus three corpus heads.
Each entry's `kind` is the hand-read verdict of the audit (record
`docs/records/2026-11-16-covenant-title-cased-headings-are-read.md`).
"""

from __future__ import annotations

import json
import pathlib
import re
from collections import Counter
from typing import Any

import pytest

from vinci.dossier import covenant_extract
from vinci.dossier.covenant_extract import agreement_title, is_amendment, is_debt_agreement
from vinci.dossier.schemas import CapitalStructure

ROOT = pathlib.Path(__file__).resolve().parent
HEADS = ROOT / "fixtures" / "covenant_title_reader" / "heads.json"
DEBT = "debt agreement"


def _heads() -> list[dict[str, Any]]:
    return list(json.loads(HEADS.read_text()))


def _head(ticker: str, accession: str) -> str:
    [h] = [e["head"] for e in _heads() if e["ticker"] == ticker and accession in e["filing"]]
    return str(h)


def _audit() -> list[dict[str, Any]]:
    """The audit's rows: every exhibit E5 refused on a committed page (not the corpus heads)."""
    return [e for e in _heads() if not e["filing"].startswith("corpus ")]


# --- positive: each failure shape -----------------------------------------------------------------

#: (ticker, accession, title read, is an amendment)
SHAPE_A = (("VRRM", "0000950170-25-072679", "REVOLVING CREDIT AGREEMENT"),
           ("CNXC", "0001803599-24-000117", "RECEIVABLES FINANCING AGREEMENT"),
           ("CNXC", "0001803599-25-000014", "RECEIVABLES FINANCING AGREEMENT"))
SHAPE_B = (("NFLX", "0001193125-18-134734", "SENIOR NOTES DUE 2028 PURCHASE AGREEMENT"),
           ("NFLX", "0001193125-14-037000", "SENIOR NOTES DUE 2024 PURCHASE AGREEMENT"))


@pytest.mark.parametrize(("ticker", "accession", "title"), SHAPE_A, ids=lambda v: str(v))
def test_a_title_cased_amendment_heading_names_its_contract(ticker: str, accession: str,
                                                            title: str) -> None:
    """(+) SHAPE A. A title-cased amendment heading is read as a capitals one is: the amendment
    instance is stripped to the contract it amends, the gate passes it, and it is an amendment.
    VRRM's comes from its own heading, "REVOLVING CREDIT", not its recital's "Credit Agreement"."""
    head = _head(ticker, accession)
    got = agreement_title(head)
    assert got == title, got
    assert is_debt_agreement(got)
    assert is_amendment(head)


def test_a_filing_id_before_a_title_cased_amendment_heading_does_not_hide_it() -> None:
    """(+) CODES FIRST, AS `agreement_title` STRIPS THEM. DERIVED from CNXC's real Third Amendment
    head with WERN's real filing-id lead ("20260605EX101 1758963679 24780046", the shape
    `_LEAD_CODE` exists for) put where its "Execution Version" stands. `agreement_title` strips
    the code and names the contract; `is_amendment` tested `_AMEND_PREFIX`, anchored at ^, on the
    unstripped heading and called the amendment a base contract (review round 0)."""
    real = _head("CNXC", "0001803599-24-000117")
    head = real.replace("Execution Version Third Amendment",
                        "20260605EX101 1758963679 24780046 Third Amendment", 1)
    assert head != real, "the derivation must apply"
    assert agreement_title(head) == "RECEIVABLES FINANCING AGREEMENT"
    assert is_amendment(head)


@pytest.mark.parametrize(("ticker", "accession", "title"), SHAPE_B, ids=lambda v: str(v))
def test_a_title_cased_heading_led_by_issuer_and_amount_is_read(ticker: str, accession: str,
                                                                title: str) -> None:
    """(+) SHAPE B. The issuer, the principal and the coupon lead the heading, and the note's
    maturity is in lowercase ("due 2028"). The title is what follows them, as `_TITLE` drops a
    leading amount from a capitals heading, and a purchase agreement is not an amendment."""
    head = _head(ticker, accession)
    got = agreement_title(head)
    assert got == title, got
    assert is_debt_agreement(got)
    assert not is_amendment(head)


# --- negative: each class of correct refusal ------------------------------------------------------

REFUSAL_KINDS = ("a titled contract that is not debt", "a plan, policy, award or notice",
                 "a letter or a dealer confirmation", "the 8-K's own cover document",
                 "a bank commitment letter", "an exchange agreement for convertible notes",
                 "a press release")


@pytest.mark.parametrize("kind", REFUSAL_KINDS)
def test_every_head_of_a_refused_kind_is_still_refused(kind: str) -> None:
    """(-) THE AUDIT'S CORRECT REFUSALS, BY CLASS. Every head the audit read as no debt agreement is
    refused by the gate: an LLC, registration rights, lease, award, put-call, subscription or stock
    purchase agreement; a plan, policy, award or notice; an offer, transition or put option letter
    or a capped-call confirmation; the 8-K cover; and the corpus's press releases and exchange
    agreements. A bank commitment letter is refused too: its head names no agreement, only a code
    name ("Project Cobra Commitment Letter"). Whether one should reach the extractor is a question
    for the gate's vocabulary, recorded as open, and not this reader's."""
    members = [e for e in _heads() if e["kind"] == kind]
    assert members, f"no head of kind {kind!r}"
    for e in members:
        got = agreement_title(e["head"])
        assert not is_debt_agreement(got), (e["ticker"], e["exhibit"], got)


def test_a_titled_refusal_keeps_the_title_it_had() -> None:
    """(-) A TITLE ALREADY READ IS NOT RE-READ. The title-cased branch runs only where the capitals
    branches read nothing, so each refusal the audit found titled keeps that exact title."""
    titled = {(e["ticker"], e["exhibit"]): agreement_title(e["head"]) for e in _audit()
              if e["kind"] == "a titled contract that is not debt"}
    assert titled == {
        ("BRBR", "d812149dex101.htm"): "AMENDED AND RESTATED LIMITED LIABILITY COMPANY AGREEMENT",
        ("FUBO", "ex10-1.htm"): "REGISTRATION RIGHTS AGREEMENT",
        ("NCNO", "exhibit1035secondamendment.htm"): "OFFICE LEASE",
        ("PARR", "a20251231ex1010-formofawar.htm"): "INC. RESTRICTED STOCK AWARD AGREEMENT",
        ("V", "exh22aroptionagreement.htm"): "AMENDED AND RESTATED PUT-CALL OPTION AGREEMENT",
        ("VRRM", "a18-15692_1ex10d1.htm"): "GORES II SUBSCRIPTION AGREEMENT",
        ("WERN", "wern-20260127ex101.htm"): "STOCK PURCHASE AGREEMENT",
    }


def test_a_press_release_naming_notes_is_not_titled_by_them() -> None:
    """(-) A CONTRACT NOUN ENDS A TITLE-CASED TITLE, NEVER AN INSTRUMENT. A press release headlines
    in title case and names what it announces: CNXC's "Concentrix Prices $600 Million Senior Notes
    Offering" read as "MILLION SENIOR NOTES" and passed the gate while NOTES could end a title-cased
    title."""
    head = _head("CNXC", "0001803599-26-000068")
    assert "Senior Notes Offering" in head, "the real headline"
    assert agreement_title(head) is None


def test_the_title_cased_heading_is_read_only_at_the_head() -> None:
    """(-) THE HEADING RUN ENDS AT THE FIRST PROSE WORD, for `_IS_AMENDMENT`'s reason: a body says
    "No amendment to this Agreement shall be effective", and prose is not a heading. DERIVED from
    TECX's real head, whose heading runs straight into its first sentence ("... Compensation Policy
    Each member of the Board of Directors ..."), with that sentence made to name a title-cased
    contract. A run read past "member" titled it "... POLICY EACH MEMBER IS A PARTY TO THE REVOLVING
    CREDIT AGREEMENT", which the gate passed."""
    head = _head("TECX", "0001193125-26-076793")
    derived = head.replace("Each member of the Board of Directors",
                           "Each member is a party to the Revolving Credit Agreement", 1)
    assert derived != head, "the derivation must apply"
    assert agreement_title(derived) is None
    assert not is_amendment(derived)


# --- the audit, counted ---------------------------------------------------------------------------

def test_the_audit_counts_five_wrong_refusals_and_twenty_five_right_ones() -> None:
    """(audit) ON THE COMMITTED FIXTURE. Of the 30 exhibits E5 refused as not a debt agreement on
    the 24 committed pages with pointer rows (main 032d2fde, the EDGAR cache, 0 of them unreadable;
    5 other located exhibits, MCK's 4 and WERN's 1, are cache misses and were never read), the
    hand read found 5 debt agreements: VRRM 1, CNXC 2, NFLX 2. The reader now passes exactly those
    5 and refuses the other 25, and each of the 25 is of a refused kind."""
    audit = _audit()
    assert len(audit) == 30
    passed = [e for e in audit if is_debt_agreement(agreement_title(e["head"]))]
    assert all(e["kind"] == DEBT for e in passed), [(e["ticker"], e["exhibit"]) for e in passed]
    assert Counter(e["ticker"] for e in passed) == {"VRRM": 1, "CNXC": 2, "NFLX": 2}
    refused = [e for e in audit if e not in passed]
    assert len(refused) == 25
    assert {e["kind"] for e in refused} <= set(REFUSAL_KINDS)
    assert Counter(e["kind"] for e in audit)[DEBT] == 5


# --- end to end: VRRM's revolver amendment reaches the model --------------------------------------

class _ServesHeads:
    """SEC reads served from the fixture's real heads, by accession and exhibit; any other read
    raises, which the loop records as a fetch failure."""

    def __init__(self) -> None:
        self.heads = {(e["filing"].split()[-1].replace("-", ""), e["exhibit"]): e["head"]
                      for e in _heads()}

    def get_text(self, url: str, **_: object) -> str:
        acc, doc = url.rsplit("/", 2)[-2:]
        return str(self.heads[(acc, doc)])


class _RecordsExhibits:
    """An LLM client that answers each exhibit with no terms and records which it was sent."""

    model = "none (test)"

    def __init__(self) -> None:
        self.sent: list[str] = []

    def extract(self, *, system: str, user: str, tool: dict[str, object],
                cache: bool = False) -> dict[str, object]:
        self.sent.append(user.split("Exhibit: ", 1)[1].split(". Extract", 1)[0])
        return {"terms": []}


def _vrrm_run() -> tuple[list[str], list[str], list[Any]]:
    frozen = json.loads((ROOT / "fixtures" / "covenant_unextracted" / "VRRM.json").read_text())
    cs = CapitalStructure.model_validate(frozen["capital_structure"])
    llm = _RecordsExhibits()
    _rows, _summary, flags, _log, outcomes = covenant_extract.extract_covenant_terms(
        cs, llm=llm, http=_ServesHeads(),  # type: ignore[arg-type]
        cik="0001682745", ticker="VRRM", name="Verra Mobility Corporation")
    assert outcomes is not None
    return llm.sent, flags, list(outcomes.value or [])


def test_vrrm_revolver_amendment_reaches_the_extractor() -> None:
    """(+) END TO END ON VRRM'S FROZEN BLOCK (its committed pointer rows, #1084), the reads served
    from the real heads: Amendment No. 4 to the Revolving Credit Agreement is sent to the model,
    named for its own heading. Before this, E5 refused it before any call, and its committed QA
    flag said it "declares itself no agreement at all". The GORES II subscription agreement is still
    refused, with the title it declares."""
    sent, flags, outcomes = _vrrm_run()
    assert "8-K 0000950170-25-072679 · vrrm-ex10_1.htm" in sent, sent
    by = {(o.accession, o.filename): o for o in outcomes}
    amend = by[("0000950170-25-072679", "vrrm-ex10_1.htm")]
    assert amend.outcome != "not_debt_agreement"
    assert amend.declared_title == "REVOLVING CREDIT AGREEMENT"
    gores = by[("0001104659-18-041476", "a18-15692_1ex10d1.htm")]
    assert (gores.outcome, gores.declared_title) == ("not_debt_agreement",
                                                     "GORES II SUBSCRIPTION AGREEMENT")
    assert any("“GORES II SUBSCRIPTION AGREEMENT”" in f for f in flags), flags


# --- the flag states what the reader did ----------------------------------------------------------

def test_an_untitled_refusal_says_no_title_was_read_not_what_the_document_is() -> None:
    """(-) THE FALSE STATEMENT (STATE row 63). With no title read, the reader knows only that, and
    the flag said the exhibit "declares itself no agreement at all", which VRRM's revolver
    amendment did not. The flag now states what the reader did, in the renderer's words ("no
    agreement title was read from its head"), and claims neither that the document is no agreement
    nor that it is not debt. END TO END on TECX's frozen block: its one located exhibit, a director
    compensation policy, is still refused."""
    frozen = json.loads((ROOT / "fixtures" / "covenant_unextracted" / "TECX.json").read_text())
    cs = CapitalStructure.model_validate(frozen["capital_structure"])
    llm = _RecordsExhibits()
    _rows, _summary, flags, _log, outcomes = covenant_extract.extract_covenant_terms(
        cs, llm=llm, http=_ServesHeads(),  # type: ignore[arg-type]
        cik="0001680367", ticker="TECX", name="Tectonic Therapeutic, Inc.")
    assert not llm.sent
    [flag] = [f for f in flags if "tecx-ex10_4.htm" in f]
    assert "no agreement title was read from the head of" in flag, flag
    assert "no agreement at all" not in flag and "not a debt agreement" not in flag, flag
    assert outcomes is not None
    assert [(o.outcome, o.declared_title) for o in outcomes.value or []] == [
        ("not_debt_agreement", None)]


# --- purchase contracts last (operator, 2026-11-16: "Order now, coverage next (Recommended)") -----

NFLX_FIXTURE = ROOT / "fixtures" / "covenant_title_reader" / "NFLX.json"
NFLX_PAS = ("0001193125-18-134734", "0001193125-14-037000")
#: what NFLX's committed page sends at base, and what the ruling keeps it sending
NFLX_BASE_FOUR = ["8-K 0001193125-09-194962 · dex101.htm",
                  "8-K 0001193125-21-193187 · d552068dex101.htm",
                  "8-K 0001193125-25-327462 · d82688dex101.htm",
                  "8-K 0001193125-19-094705 · d721020dex101.htm"]


class _ServesNflx(_ServesHeads):
    """The fixture's heads plus NFLX's own (its credit agreements and amendments)."""

    def __init__(self) -> None:
        super().__init__()
        nflx = json.loads(NFLX_FIXTURE.read_text())
        self.heads.update({(h["filing"].split()[-1].replace("-", ""), h["exhibit"]): h["head"]
                           for h in nflx["heads"]})


def _nflx_run(drop: tuple[str, ...] = (), heads: dict[tuple[str, str], str] | None = None
              ) -> tuple[list[str], list[Any], list[str]]:
    from vinci.dossier.schemas import CovenantPointer, Sourced
    nflx = json.loads(NFLX_FIXTURE.read_text())
    rows = [CovenantPointer.model_validate(r) for r in nflx["covenant_pointer_rows"]
            if r["accession"] not in drop]
    cs = CapitalStructure(
        instruments=Sourced.unknown(note="n/a"), summary=Sourced.unknown(note="n/a"),
        detail_as_of="n/a", maturity_filings=Sourced.unknown(note="n/a"),
        covenant_pointers=Sourced.present(f"{len(rows)} pointers", source_ref="EDGAR"),
        covenant_pointer_rows=Sourced.present(rows, source_ref="EDGAR"),
        covenant_terms=Sourced.unknown(note="n/a"))
    llm = _RecordsExhibits()
    http = _ServesNflx()
    http.heads.update(heads or {})
    _rows, _summary, flags, _log, outcomes = covenant_extract.extract_covenant_terms(
        cs, llm=llm, http=http,  # type: ignore[arg-type]
        cik=nflx["cik"], ticker="NFLX", name="Netflix, Inc.")
    assert outcomes is not None
    got = list(outcomes.value or [])
    targets = covenant_extract._core_agreement_exhibits(rows)
    assert [(o.accession, o.filename) for o in got] == [(r.accession, f) for r, f in targets], \
        "one outcome per target, in the targets' order"
    return llm.sent, got, flags


def test_a_purchase_agreement_fills_a_slot_only_after_the_credit_agreements() -> None:
    """(+) NFLX'S REAL POINTER SET (its committed rows, frozen at main 8d0c562c). Its pointer files
    two notes purchase agreements under a bridge-loan family, so the round-robin reached them first,
    and they took two of the four slots (#1088 as first built). That pushed its December 2025
    revolver and its 2019 amendment past the bound. Ruled: a purchase agreement is admitted, but
    it takes a slot only after every other debt contract the loop reached.
    MOVED WITH THE COVERAGE RULE (2026-11-16): the cap of four no longer chooses, so both purchase
    agreements are now sent, and still only after NFLX's four credit agreements, under the titles E5
    read. (This layer carries no maturity check, so no reference date says the 2014 notes matured;
    NFLX's page does, in tests/test_covenant_coverage_rule.py.) No flag names them, because none is
    past the guard."""
    sent, outcomes, flags = _nflx_run()
    assert sent == [*NFLX_BASE_FOUR, "8-K 0001193125-18-134734 · d567970dex101.htm",
                    "8-K 0001193125-14-037000 · d671121dex101.htm"], sent
    by = {o.accession: o for o in outcomes}
    assert [(by[a].outcome, by[a].declared_title) for a in NFLX_PAS] == [
        ("no_terms_returned", "SENIOR NOTES DUE 2028 PURCHASE AGREEMENT"),
        ("no_terms_returned", "SENIOR NOTES DUE 2024 PURCHASE AGREEMENT")]
    assert not any("ranked after every other debt contract" in f for f in flags), flags


def test_a_purchase_agreement_still_reaches_the_model_when_a_slot_is_free() -> None:
    """(-) LAST, NOT REFUSED. DERIVED from NFLX's real pointer set without its December 2025
    revolver and its 2019 amendment, which frees two slots: both notes purchase agreements are
    sent, after the credit agreements, in the targets' order (2018, then 2014)."""
    sent, outcomes, _flags = _nflx_run(drop=("0001193125-25-327462", "0001193125-19-094705"))
    assert sent == [NFLX_BASE_FOUR[0], NFLX_BASE_FOUR[1],
                    "8-K 0001193125-18-134734 · d567970dex101.htm",
                    "8-K 0001193125-14-037000 · d671121dex101.htm"], sent
    by = {o.accession: o for o in outcomes}
    assert all(by[a].outcome == "no_terms_returned" for a in NFLX_PAS)


@pytest.mark.parametrize("heading", ["Note Purchase Agreement", "Securities Purchase Agreement"])
def test_a_governing_purchase_agreement_keeps_its_place_in_the_order(heading: str) -> None:
    """(-) ONLY THE INITIAL PURCHASERS' KIND IS RANKED LAST (#1088 review, round 1). A private
    placement's NOTE PURCHASE AGREEMENT carries its notes' financial covenants with no indenture
    behind it, and a PIPE convertible's SECURITIES PURCHASE AGREEMENT is the document `_DEBT`
    admits SECURITIES PURCHASE for: each governs, so each keeps its round-robin place. DERIVED from
    NFLX's real 2018 head with its heading's name swapped. It is sent first, where (a) sent the
    purchase agreement, and not held behind the credit agreements."""
    acc, doc = "0001193125-18-134734", "d567970dex101.htm"
    real = re.sub(r"\s+", " ", _head("NFLX", acc))
    name = "Senior Notes due 2028 Purchase Agreement"
    assert name in real, "the derivation must apply"
    sent, outcomes, _flags = _nflx_run(heads={(acc.replace("-", ""), doc):
                                              real.replace(name, heading, 1)})
    assert sent[0] == f"8-K {acc} · {doc}", sent
    [got] = [o for o in outcomes if o.accession == acc]
    assert (got.outcome, got.declared_title) == ("no_terms_returned", heading.upper())


# --- a title-cased run ABOUT a contract is not its heading (#1088 review, round 1) ----------------

PR_HEADLINE = "Concentrix Prices $600 Million Senior Notes Offering"


@pytest.mark.parametrize(("shape", "headline"), [
    ("a reporting verb", "Concentrix Announces Amendment to Credit Agreement"),
    ("a reporting verb and an amount in words",
     "Concentrix Closes $500 Million Revolving Credit Agreement"),
    ("an amount in words", "Concentrix $500 Million Revolving Credit Agreement"),
    ("an exhibit index", "Exhibit Index Exhibit No. Description 10.1 Credit Agreement"),
    ("a notice", "Notice of Borrowing Under Credit Agreement"),
], ids=lambda v: str(v)[:24])
def test_a_title_cased_run_about_a_contract_is_not_its_heading(shape: str, headline: str) -> None:
    """(-) A HEADLINE, AN INDEX OR A NOTICE NAMES A CONTRACT WITHOUT BEING ONE. Read in capitals,
    each of these passed the gate under the contract it names, and a press release quoting a
    facility's terms would pass the quote checks and print as those terms. DERIVED from CNXC's real
    press-release head with its headline swapped; no such head is in the corpus."""
    real = re.sub(r"\s+", " ", _head("CNXC", "0001803599-26-000068"))
    assert PR_HEADLINE in real, "the derivation must apply"
    head = real.replace(PR_HEADLINE, headline, 1)
    got = agreement_title(head)
    assert got is None, (shape, got)
    assert not is_amendment(head), shape


def test_a_contents_listing_is_not_a_heading() -> None:
    """(-) A TABLE OF CONTENTS, WITH ITS LEAD OR WITHOUT IT. DERIVED from FUBO's real exchange
    agreement, its cover cut so the head opens at its contents, and its first two entries made
    "Article I Definitions Article II The Guaranty": read in capitals, that is a GUARANTY."""
    real = re.sub(r"\s+", " ", _head("FUBO", "0001493152-24-000126"))
    entries = "Section 1. Definitions 1 Section 2. Rules of Construction"
    assert "Table of Contents" in real and entries in real, "the derivation must apply"
    toc = (real[:real.index("fuboTV")]
           + real[real.index("Table of Contents"):].replace(
               entries, "Article I Definitions Article II The Guaranty", 1))
    for head in (toc, toc.replace("Table of Contents Page ", "", 1)):
        assert agreement_title(head) is None, head[:120]
