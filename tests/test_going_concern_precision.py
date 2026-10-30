"""Does the filing STATE going-concern doubt, or merely contain the phrase?

Every fixture below is REAL filing text, quoted from the filing named beside it. That is the whole
point: the previous detectors were written against what the sentences were *imagined* to look like,
and the sentences EDGAR actually ships are nothing like it.

THE TWO INCIDENTS THIS PINS (both measured 2026-09-01):

1. **The dossier.** TECX's page asserted ``substantial_doubt: true`` for a company holding $227.1M
   and guiding runway into Q1 2029 — and the synthesis then wrote a **strongly-bearish** verdict
   citing "a stated going-concern doubt". The matched text was the ASU 2014-15 sentence saying the
   assessment was PERFORMED; the very next sentence says the cash is sufficient.
2. **The ranker.** A bare ``going concern|substantial doubt`` match sank **10 of 268** queue names,
   **4 wrongly** — and the demote is DEMOTE-ONLY, so a wrong flag removes a name silently.

Both surfaces now read one detector, so the page and the demote cannot disagree about what a filer
said.
"""

from __future__ import annotations

import pytest

from vinci.edgar.going_concern import (
    find_going_concern_statement,
    states_going_concern_doubt,
)

# --- REAL text: the two 10-Q passages that sit either side of the distinction -------------------

#: TECX 10-Q 0001193125-26-338062. The ASU evaluation sentence, then its actual conclusion.
TECX_10Q = (
    "The Company will continue to need to raise additional capital to fund its operations. The "
    "Company had cash and cash equivalents of $227.1 million as of June 30, 2026. In accordance "
    'with Accounting Standards Update ("ASU") 2014-15, Disclosure of Uncertainties about an '
    "Entity's Ability to Continue as a Going Concern (Subtopic 205-40), the Company has evaluated "
    "whether there are conditions and events, considered in the aggregate, that raise substantial "
    "doubt about the Company's ability to continue as a going concern within one year after the "
    "date that these condensed consolidated financial statements are issued. The Company believes "
    "that its existing cash and cash equivalents will be sufficient to allow the Company to fund "
    "operations beyond twelve months from the date of issuance of these condensed consolidated "
    "financial statements."
)

#: MVST 10-Q 0001628280-26-055372. The SAME evaluation frame — then a real conclusion after it.
MVST_10Q = (
    "Management evaluated whether conditions and events considered in the aggregate raise "
    "substantial doubt about the Company's ability to continue as a going concern within one year "
    "after the date the consolidated financial statements are issued. Based on the Company's "
    "revised business plan, its projected cash flow may not be sufficient to fund operations and "
    "meet debt obligations over the next twelve months. Additionally, recent equity market "
    "conditions and business performance have rendered the equity funding unfavorable as a primary "
    "liquidity mechanism. These conditions and events raise substantial doubt about the Company's "
    "ability to continue as a going concern within one year after the date that these consolidated "
    "financial statements are issued."
)

# --- REAL text: the four 8-Ks the ranker sank WRONGLY -------------------------------------------

EOSE_8K = (  # 0000950103-26-009739 — "going concern VALUE" is a valuation term
    "CCM Frontier is expected to receive 50,000,001 Class A-1 Units of the JV Company as "
    "founder's equity in consideration for the contracts, contacts, investment opportunities, "
    "subject matter expertise and other going concern value with respect to the frontier power "
    "platform developed by affiliates of CCM Frontier."
)
TLRY_8K = (  # 0001437749-26-006389 — the M&A sense, and Tilray was the BUYER
    "Tilray UK acquired the business and assets of BrewDog plc through a pre-packaged "
    "administration process in Scotland under the Insolvency Act 1986, with the intent for Tilray "
    "UK to carry on the acquired business operations and assets as a going concern. The "
    "transactions contemplated by the Purchase Agreement closed on the same date."
)
BKKT_8K = (  # 0001628280-25-036239 — one item in a semicolon safe-harbor risk list
    "the Company's failure to implement the Company's business plans or strategies; the Company's "
    "ability to continue as a going concern; the Company's ability to grow and manage growth "
    "profitably; the possibility that the Company may be unable to obtain the applicable "
    "regulatory approvals."
)
PPTA_8K = (  # 0001104659-25-058655 — a forward-looking ASSUMPTION that they WILL continue
    "that general business and economic conditions will not change in a materially adverse manner "
    "and that permitting and operations costs will not materially increase; and that we will be "
    "able to discharge our liabilities as they become due and continue as a going concern."
)

# --- REAL text: 8-Ks that genuinely state doubt -------------------------------------------------

SOC_8K = (  # 0001831481-26-000097 — an auditor's explanatory paragraph
    "The reports did not contain an adverse opinion or a disclaimer of opinion, nor were they "
    "qualified or modified as to uncertainty, audit scope or accounting principles, except that "
    "such reports contained an explanatory paragraph regarding the Company's ability to continue "
    "as a going concern."
)
HYMC_8K = (  # 0001641172-25-014197 — "going concern uncertainty", no "substantial doubt"
    "except that Moss Adams' audit report on the Company's consolidated financial statements as of "
    "and for the year ended December 31, 2024 contained an explanatory paragraph regarding a going "
    "concern uncertainty."
)
USAR_8K = (  # 0001213900-26-007457 — a numbered risk item that ASSERTS the doubt
    "(23) the costs of production, capital expenditures and requirements for additional capital; "
    "(24) substantial doubt regarding the Company's ability to continue as a going concern for the "
    "twelve months following the issuance of its third quarter 2025 Condensed Consolidated "
    "Financial Statements; (25) the timing of regulatory approvals."
)


# --- the evaluation frame is not a conclusion ---------------------------------------------------
def test_the_asu_evaluation_sentence_alone_is_not_doubt() -> None:
    """THE DOSSIER INCIDENT. Every ASU 2014-15 filer writes this sentence; it says the assessment
    was PERFORMED. TECX's next sentence says the cash is sufficient — the opposite of doubt."""
    assert states_going_concern_doubt(TECX_10Q) is False


def test_a_conclusion_after_the_same_frame_still_fires() -> None:
    """THE CONTROL, and the reason the scan cannot stop at the first mention. MVST opens with the
    identical evaluation sentence and then states the conclusion. A fix that silenced TECX by
    matching only the first mention would silence MVST too — trading a false positive for a false
    negative on a genuinely distressed name, which is the worse error."""
    hit = find_going_concern_statement(MVST_10Q)
    assert hit is not None
    assert hit.sentence.startswith("These conditions and events raise substantial doubt"), hit


def test_the_quoted_sentence_is_the_conclusion_not_the_evaluation() -> None:
    """Provenance: the caveat's value is being source-bound to the sentence that makes the claim."""
    hit = find_going_concern_statement(MVST_10Q)
    assert hit is not None
    assert "evaluated whether" not in hit.sentence


# --- the three non-distress senses --------------------------------------------------------------
def test_going_concern_value_is_a_valuation_term() -> None:
    assert states_going_concern_doubt(EOSE_8K) is False


def test_acquiring_a_business_as_a_going_concern_is_not_distress() -> None:
    """TLRY was the BUYER. 'As a going concern' here means 'as an operating business' — the phrase
    signals the opposite of what the demote read it as."""
    assert states_going_concern_doubt(TLRY_8K) is False


def test_a_safe_harbour_risk_list_naming_the_topic_is_not_doubt() -> None:
    """Nearly every earnings release carries a list like this, so any 8-K with an EX-99.1 attached
    was exposed. The topic is named; no doubt is asserted."""
    assert states_going_concern_doubt(BKKT_8K) is False


def test_a_forward_looking_assumption_of_continuing_is_not_doubt() -> None:
    """PPTA assumes it WILL continue — the sentence asserts solvency, not doubt."""
    assert states_going_concern_doubt(PPTA_8K) is False


# --- the real ones must still fire (the gate that matters more) ---------------------------------
def test_an_auditors_explanatory_paragraph_is_doubt() -> None:
    """No 'substantial doubt' appears in SOC's sentence; 'explanatory paragraph' carries the claim
    on its own — it is WHY an audit report is qualified."""
    assert states_going_concern_doubt(SOC_8K) is True


def test_a_going_concern_uncertainty_is_doubt() -> None:
    assert states_going_concern_doubt(HYMC_8K) is True


def test_a_risk_item_that_asserts_the_doubt_still_fires() -> None:
    """THE PIN THAT FORBIDS THE LAZY FIX. USAR's only mention sits in a numbered forward-looking
    risk list — the same shape as BKKT's. Excluding such lists wholesale would silence a name that
    really does state substantial doubt. What separates them is the ASSERTION, not the container:
    BKKT names the topic, USAR asserts the doubt."""
    assert states_going_concern_doubt(USAR_8K) is True


# --- explicit denials, and the empty case --------------------------------------------------------
def test_an_alleviated_or_denied_doubt_is_not_doubt() -> None:
    denied = ("Management concluded that these conditions do not raise substantial doubt about the "
              "Company's ability to continue as a going concern.")
    assert states_going_concern_doubt(denied) is False


def test_text_without_the_phrase_is_not_doubt() -> None:
    plain = "The Company reported record revenue for the quarter."
    assert states_going_concern_doubt(plain) is False
    assert find_going_concern_statement("") is None


# --- one detector, two consumers ----------------------------------------------------------------
def test_both_surfaces_read_the_same_detector() -> None:
    """The demote and the page must never disagree about whether a filer said this. Two private
    regexes is the twin-drift class; the ranker's was `going concern|substantial doubt` while the
    dossier's required `raise substantial doubt about … going concern`, so they already disagreed
    on the same text before this was shared."""
    import ast
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1] / "vinci"
    for rel in ("rank/structural.py", "edgar/filing_sections.py"):
        src = (root / rel).read_text()
        imported = {
            n.name for node in ast.walk(ast.parse(src)) if isinstance(node, ast.ImportFrom)
            and node.module == "vinci.edgar.going_concern" for n in node.names
        }
        assert "find_going_concern_statement" in imported, (
            f"{rel} no longer reads the shared going-concern detector — the demote and the page "
            "can now disagree about what a filer said")
        assert '"going concern|substantial doubt"' not in src, (
            f"{rel} has re-introduced a bare phrase match")


# --- audit E2-D17: negation, modality and the evaluation frame, on REAL sentences -----------------
# Each sentence is quoted verbatim from the filing named beside it (the SEC cache, read 2026-10-30
# through `html_to_text`). The 583 cached filings that mention a going concern are the corpus the
# rules were grown from; every marker below answers one of these sentences.

#: A filer that concluded it has NO doubt, or that its plans ALLEVIATED it — not doubt.
DENIED = {
    "EOSE 10-K 0001628280-26-011961":
        "In light of the significant amount of capital raised in 2025 and our anticipated ability "
        "to meet the covenants associated with the debt instruments held by the Company, "
        "management has concluded that there is no longer substantial doubt about our ability to "
        "continue as a going concern within one year after the date that the Consolidated "
        "Financial Statements are issued.",
    "PHAT 10-Q 0001193125-26-193946":
        "Including our existing cash and cash equivalents, we believe that we have sufficient "
        "working capital on hand to fund operations such that there is no substantial doubt as to "
        "our ability to continue as a going concern at the date the unaudited interim condensed "
        "financial statements were issued.",
    "ACRS 10-K 0001104659-26-020540":
        "As of the report date, the Company does not believe that substantial doubt exists about "
        "its ability to continue as a going concern.",
    "10-K 0001140361-26-006977":
        "After considering the Group’s current cash position, the proceeds from the equity "
        "financings completed subsequent to year‑end, the Group’s forecasted cash flows, and its "
        "planned operating and investment activities, management has concluded that no "
        "substantial doubt exists regarding the Group’s ability to continue as a going concern for "
        "at least 12 months from the date these financial statements are issued.",
    "MAR 10-K 0001997464-26-000018":
        "On this basis, the Directors have concluded that no material uncertainty exists that may "
        "cast significant doubt on the Group's ability to continue as a going concern for a period "
        "of at least 12 months from the date these financial statements were approved and "
        "authorized for issuance.",
    "RLMD 10-K 0001213900-26-031862":
        "As a result, the Company concluded that management’s plans alleviated substantial doubt "
        "about the Company’s ability to continue as a going concern as of December 31, 2025 and "
        "the Company has sufficient funds to maintain operations for at least 12 months from the "
        "issuance of these audited consolidated financial statements.",
    "10-K 0001213900-25-086227":
        "With the successful completion of the Offering, we believe that substantial doubt about "
        "our ability to continue as a going concern has been alleviated for at least the next "
        "twelve months.",
}

#: A HYPOTHETICAL — a risk factor saying what COULD happen — not a statement that it has.
MODAL = {
    "ZURA 10-K 0001104659-26-032080":
        "Our recurring losses from operations and financial condition could raise substantial "
        "doubt about our ability to continue as a going concern.",
    "MNLK 10-K 0001821586-26-000002":
        "In our own required quarterly assessments, we may conclude that there is substantial "
        "doubt about our ability to continue as a going concern, and future reports from our "
        "independent registered public accounting firm may also contain statements expressing "
        "substantial doubt about our ability to continue as a going concern.",
}

#: The ASSESSMENT or the POLICY, not a result — every one names the doubt as a question.
FRAME = {
    "WOLF 10-Q 0000895419-25-000071":
        "GAAP, management considers whether there are conditions or events that raise substantial "
        "doubt about the Company's ability to continue as a going concern for the twelve months "
        "following the issuance date of its financial statements.",
    "WVE 10-K 0001193125-26-073472":
        "The Company is required to make certain additional disclosures if the Company concludes "
        "substantial doubt exists and it is not alleviated by the Company’s plans or when the "
        "Company’s plans alleviate substantial doubt about the Company’s ability to continue as a "
        "going concern.",
    "10-K 0001171843-26-000374 (the auditor's responsibilities)":
        "• Conclude whether, in our judgment, there are conditions or events, considered in the "
        "aggregate, that raise substantial doubt about the Company’s ability to continue as a "
        "going concern for a reasonable period of time.",
}

#: A CONCLUSION OF DOUBT that cites the standard, or that denies its own alleviation — doubt.
CONCLUDED = {
    "WOLF 10-Q 0000895419-25-000071":
        "However, due to the Company’s ongoing consideration of an in-court restructuring that "
        "would result in an event of default during the implementation of that potential "
        "solution, management has concluded that there is substantial doubt about the Company’s "
        "ability to continue as a going concern as of the issuance date, in accordance with the "
        "requirements of ASC 205-40, “Presentation of Financial Statements – Going Concern.”",
    "10-Q 0001493152-26-024413":
        "In connection with our assessment of going concern considerations in accordance with FASB "
        "ASU 2014-15, “Disclosures of Uncertainties about an Entity’s Ability to Continue as a "
        "Going Concern,” management has determined that the conditions described above raise "
        "substantial doubt about the Company’s ability to continue as a going concern through "
        "twelve months from the date these unaudited condensed consolidated financial statements "
        "are available to be issued.",
    "VSTM 10-Q 0001104659-26-057114":
        "As a result of the assessment in accordance with the applicable accounting standards, "
        "these conditions raise substantial doubt about the Company’s ability to continue as a "
        "going concern for twelve months after the date the condensed consolidated financial "
        "statements are issued.",
    "20-F 0001213900-26-057986":
        "The management plan cannot alleviate the substantial doubt of our ability to continue as "
        "a going concern.",
}

#: DOUBT that must survive the new rules: an idiom "if at all", and a "may not be" beside the
#: conclusion — neither is a hypothetical about the doubt itself.
STILL_DOUBT = {
    "SOCC 10-K 0001831481-26-000026":
        "Due to the uncertainty regarding our resumption of sales of production volumes, and lack "
        "of assurance that new financing, or refinancing of the Senior Secured Term Loan, will be "
        "available to us on commercially acceptable terms, if at all, substantial doubt exists "
        "about the Company’s ability to continue as a going concern.",
    "SANA 10-Q 0001193125-26-216769":
        "Management has determined that the Company’s current capital resources may not be "
        "sufficient to fund its planned operations for at least one year from the date of this "
        "Quarterly Report, and there is substantial doubt as to the Company's ability to continue "
        "as a going concern.",
}


@pytest.mark.parametrize("filing", DENIED)
def test_a_denied_or_alleviated_doubt_is_not_doubt(filing: str) -> None:
    """(−) Audit E2-D17 GC1: "management has concluded that there is no longer substantial doubt"
    read as DOUBT — the denial named the doubt, and only "do not RAISE substantial doubt" was
    read as one."""
    assert find_going_concern_statement(DENIED[filing]) is None, filing


@pytest.mark.parametrize("filing", MODAL)
def test_a_hypothetical_doubt_is_not_doubt(filing: str) -> None:
    """(−) A risk factor's "could raise substantial doubt" says what may happen, not what has."""
    assert find_going_concern_statement(MODAL[filing]) is None, filing


@pytest.mark.parametrize("filing", FRAME)
def test_an_assessment_or_a_policy_is_not_doubt(filing: str) -> None:
    """(−) The question asked ("considers whether", "Conclude whether") and the disclosure policy
    ("required to make certain additional disclosures if …") are frames, not results."""
    assert find_going_concern_statement(FRAME[filing]) is None, filing


@pytest.mark.parametrize("filing", CONCLUDED)
def test_a_conclusion_that_cites_the_standard_or_cannot_alleviate_is_doubt(filing: str) -> None:
    """(+) Audit E2-D17 GC4: "in accordance with ASC 205-40" CITES the standard; it is not the
    evaluation frame, and a sentence that concludes doubt while citing it is doubt. "cannot
    alleviate the substantial doubt" says the doubt remains."""
    assert find_going_concern_statement(CONCLUDED[filing]) is not None, filing


@pytest.mark.parametrize("filing", STILL_DOUBT)
def test_doubt_beside_an_idiom_or_a_modal_elsewhere_still_fires(filing: str) -> None:
    """(+) The negative pins of the new rules: "if at all" and "may not be sufficient" sit in real
    conclusions of doubt."""
    assert find_going_concern_statement(STILL_DOUBT[filing]) is not None, filing


def test_the_briefs_two_sentences() -> None:
    """(−/+) The audit's own two cases, verbatim from the brief."""
    assert states_going_concern_doubt(
        "Management concluded that there is no substantial doubt about the Company's ability to "
        "continue as a going concern.") is False
    assert states_going_concern_doubt(
        "In accordance with ASC 205-40, management has concluded that these conditions raise "
        "substantial doubt about the Company's ability to continue as a going concern.") is True


def test_review_round_0_tense_and_abbreviation() -> None:
    """(+/−) A frame that concludes in the past tense is a conclusion; "Amendment No. 2" is not a
    negator of "alleviated"."""
    assert states_going_concern_doubt(
        "Management evaluated whether there are conditions and events that raise substantial doubt "
        "about the Company's ability to continue as a going concern and determined that these "
        "conditions raised substantial doubt about the Company's ability to continue as a going "
        "concern.") is True
    assert states_going_concern_doubt(
        "Following Amendment No. 2, management's plans alleviated substantial doubt about the "
        "Company's ability to continue as a going concern.") is False
