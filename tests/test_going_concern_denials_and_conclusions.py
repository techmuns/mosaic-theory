"""Going-concern denials and hypotheticals are not doubt, and real conclusions are (TeamNostra fix
request 2, RE2-D9 and RE2-D10).

`vinci.edgar.going_concern.find_going_concern_statement` sets a page's `substantial_doubt` and the
ranker's structural demote. Document 14 (E2-D9, D10) misread 7 of 9 constructed sentences:

* RE2-D9 — read as DOUBT: a doubt that "does not exist"; plans that "alleviate" it (present
  tense); an "alleviated" doubt followed by an unrelated "not"; "there will be substantial doubt".
  And at the FILING level: a note whose conditions "raise substantial doubt" and whose plans then
  "alleviate the substantial doubt" states ASC 205-40's alleviated outcome, not doubt — Solo
  Brands' 10-Q and Aeluma's 10-K, both live, both read as doubt on main.
* RE2-D10 — MISSED: a frame's own conclusion with the verb after the doubt ("determined that
  substantial doubt … exists"), or the company HAVING it, beside a cited standard; and a "no" four
  words back that governs another noun ("has no revenue and recurring losses raise substantial
  doubt").

Real sentences where the corpus has the shape (quoted from the filing named beside them, read
through `html_to_text`); the rest are TeamNostra's constructed cases, named as such.
"""
from __future__ import annotations

import pytest

from vinci.edgar.going_concern import find_going_concern_statement


def _doubt(text: str) -> bool:
    return find_going_concern_statement(text) is not None


# --- RE2-D9: not doubt ---------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "Management has concluded that substantial doubt about the Company's ability to continue as a "
    "going concern does not exist.",
    "Management's plans alleviate the substantial doubt about the Company's ability to continue "
    "as a going concern.",
    "Management's plans have alleviated the substantial doubt about the Company's ability to "
    "continue as a going concern, and the Company does not expect to need additional financing "
    "in the next twelve months.",
    "If the Company is unable to obtain additional financing, there will be substantial doubt "
    "about its ability to continue as a going concern.",
], ids=["does-not-exist", "alleviate-present-tense", "alleviated-then-a-later-not",
        "there-will-be"])
def test_re2_d9_a_denial_or_a_hypothetical_is_not_doubt(text: str) -> None:
    """CONSTRUCTED (TeamNostra, document 14 E2-D9): each read as DOUBT on main."""
    assert not _doubt(text)


#: 10-Q 0001870600-26-000044 (Solo Brands, quarter ended 2026-06-30), its going-concern note
_SOLO = (
    "However, the risks associated with variability in the Company’s operating performance could "
    "affect future covenant compliance, and raise substantial doubt about the Company’s ability "
    "to continue as a going concern within one year after the issuance of these unaudited "
    "consolidated financial statements. These plans alleviate the substantial doubt about the "
    "Company’s ability to continue as a going concern for at least the twelve months following "
    "the issuance of these unaudited consolidated financial statements."
)
#: 10-K 0001213900-25-086227 (Aeluma), its liquidity note
_AELUMA = (
    "As previously disclosed, we had expressed substantial doubt about our ability to continue as "
    "a going concern due to recurring losses and negative operating cash flows. With the "
    "successful completion of the Offering, we believe that substantial doubt about our ability "
    "to continue as a going concern has been alleviated for at least the next twelve months."
)


@pytest.mark.parametrize("text", [_SOLO, _AELUMA], ids=["SBDS-10-Q", "AELU-10-K"])
def test_re2_d9_a_filing_whose_plans_alleviate_the_doubt_states_none(text: str) -> None:
    """Real text: the conditions raised the doubt the plans alleviated — ASC 205-40's other
    outcome. Main quoted Solo Brands' alleviation, and Aeluma's past "had expressed", as doubt."""
    assert not _doubt(text)


@pytest.mark.parametrize("text", [
    "These conditions raise substantial doubt about the Company's ability to continue as a going "
    "concern, and management's plans to alleviate that doubt are described below.",
    "Management's plans have not alleviated the substantial doubt about the Company's ability to "
    "continue as a going concern.",
    "These conditions raise substantial doubt about the Company's ability to continue as a going "
    "concern. There can be no assurance that management's plans will have alleviated that doubt.",
    "The management plan cannot alleviate the substantial doubt of our ability to continue as a "
    "going concern.",
], ids=["plans-to-alleviate", "not-alleviated", "no-assurance", "cannot-alleviate"])
def test_re2_d9_a_doubt_not_yet_alleviated_stands(text: str) -> None:
    """NEGATIVE PINS — a purpose, a negation, an assurance and a "cannot" leave the doubt standing,
    for the sentence and for the filing (the last is 20-F 0001213900-26-057986's own sentence)."""
    assert _doubt(text)


# --- RE2-D10: doubt -------------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "In accordance with ASC 205-40, management determined that the Company has substantial doubt "
    "about its ability to continue as a going concern.",
    "In accordance with ASC 205-40, management determined that substantial doubt about the "
    "Company's ability to continue as a going concern exists.",
    "The Company has no revenue and recurring losses raise substantial doubt about its ability to "
    "continue as a going concern.",
], ids=["standard-cited-has-doubt", "standard-cited-exists-late", "no-four-words-back"])
def test_re2_d10_a_real_conclusion_is_doubt(text: str) -> None:
    """CONSTRUCTED (TeamNostra, document 14 E2-D10): each was missed on main, with no flag."""
    assert _doubt(text)


@pytest.mark.parametrize("text", [
    "These conditions do not raise substantial doubt about the Company's ability to continue as a "
    "going concern.",
    "There are no conditions or events, considered in the aggregate, that raise substantial doubt "
    "about the Company's ability to continue as a going concern.",
    "In accordance with ASC 205-40, management evaluates whether there are conditions or events "
    "that raise substantial doubt about the Company's ability to continue as a going concern.",
], ids=["do-not-raise", "no-conditions-or-events", "the-frame-alone"])
def test_re2_d10_a_denial_and_a_frame_are_still_not_doubt(text: str) -> None:
    """NEGATIVE PINS — the widened conclusion and the narrowed "no" leave these as they were."""
    assert not _doubt(text)


# --- review round 0: the widened rules, held to what they were widened for -----------------------
@pytest.mark.parametrize("text", [
    "In accordance with ASC 205-40, management determined that the Company does not have "
    "substantial doubt about its ability to continue as a going concern.",
    "In accordance with ASC 205-40, management determined that the Company no longer has "
    "substantial doubt about its ability to continue as a going concern.",
    "In accordance with ASC 205-40, management concluded that substantial doubt about the "
    "Company's ability to continue as a going concern no longer exists.",
    "These conditions do not individually or collectively raise substantial doubt about the "
    "Company's ability to continue as a going concern.",
], ids=["frame-does-not-have", "frame-no-longer-has", "frame-no-longer-exists",
        "not-individually-or-collectively"])
def test_a_negated_conclusion_is_not_doubt(text: str) -> None:
    """CONSTRUCTED (review): the widened conclusion read each negated verb as a result, and the
    clause-break "or" split a denial — each was None on main and read as DOUBT before the fix."""
    assert not _doubt(text)


_RAISED = ("These conditions raise substantial doubt about the Company's ability to continue as a "
           "going concern. ")


@pytest.mark.parametrize("text", [
    "In fiscal 2024, management's plans alleviated substantial doubt about the Company's ability "
    "to continue as a going concern. As of December 31, 2025, the Company has recurring losses "
    "and " + _RAISED[0].lower() + _RAISED[1:],
    "Absent the covenant breach, management's plans would have alleviated substantial doubt about "
    "the Company's ability to continue as a going concern. " + _RAISED,
    _RAISED + "Management believes its plans will help alleviate the substantial doubt about the "
    "Company's ability to continue as a going concern.",
    _RAISED + "Management's plans won't alleviate the substantial doubt about the Company's "
    "ability to continue as a going concern.",
    _RAISED + "Management believes its plans have alleviated the substantial doubt about the "
    "Company's ability to continue as a going concern, although there is no assurance that the "
    "financing will close.",
    _RAISED + "Management's plans alleviate the substantial doubt about the Company's ability to "
    "continue as a going concern, unless the lender declines to fund.",
], ids=["doubt-after-an-earlier-alleviation", "would-have-alleviated", "will-help-alleviate",
        "wont-alleviate", "later-no-assurance", "later-unless"])
def test_an_alleviation_that_is_not_one_leaves_the_doubt_standing(text: str) -> None:
    """CONSTRUCTED (review): the filing-wide alleviation erased each of these doubts — a later
    doubt, a modal alleviation, and one a later clause conditions. All DOUBT on main."""
    assert _doubt(text)
