"""GAAP diluted EPS guidance, read as its OWN basis — never folded into adjusted EPS (2026-10-21).

THE DEFECT (a review of TJX's page). TJX guides three FY27 earnings figures that are not
interchangeable: GAAP diluted EPS $5.31–$5.36, adjusted $5.15–$5.20 (ex the tariff-refund benefit)
and the Street's normalized $5.25. The page carried the adjusted guide alone, so a reader could not
see the GAAP figure the adjusted one is reconciled from.

THE CORPUS, measured before any pin: the 118 EX-99.1s the 27 committed pages cite (main 4b514dca),
re-parsed — 100 → 120 guidance items, all 20 additions `gaap diluted eps` (TJX ×12, EPAM ×8), every
one with a period READ from its own text (each quarter beside its year), none on the `next-fy`
default, nothing else moved. Two parser refinements came out of that run and are pinned here: the
forward-run check reads through the guide's own clause, and "continues to plan" is a plan verb.
"""
from __future__ import annotations

from tests.test_dossier import _min_record
from tests.test_guidance_opener_period import _TJX
from tests.test_release_adjusted_eps import _ABSENT, _g, _rel
from vinci.dossier import mechanical as dm
from vinci.dossier.schemas import GuidanceItem, SourceStatus
from vinci.edgar.release_parse import _guidance


def _by(items: list[GuidanceItem]) -> list[tuple[str, str, float | None, float | None, str]]:
    return [(g.metric, g.period, g.low, g.high, g.unit) for g in items]


def test_tjx_reads_four_guides_on_two_bases() -> None:
    """THE RED. TJX's outlook section, verbatim: the GAAP year ($5.31–$5.36) beside the adjusted
    year ($5.15–$5.20), each quarter beside its year, under two metric names."""
    got = sorted(_by(_guidance(_TJX, "x")))
    assert got == sorted([
        ("adjusted eps", "Q3 2027", 1.30, 1.32, "$/sh"),
        ("adjusted eps", "Fiscal 2027", 5.15, 5.20, "$/sh"),
        ("gaap diluted eps", "Q3 2027", 1.36, 1.38, "$/sh"),
        ("gaap diluted eps", "Fiscal 2027", 5.31, 5.36, "$/sh")]), got


def test_the_gaap_range_beside_a_non_gaap_one_is_the_gaap_one() -> None:
    """EPAM 8-K 0001352010-26-000010, verbatim: one sentence, both bases. The GAAP range is read;
    the non-GAAP one is not read as GAAP (and stays unread — non-GAAP EPS is row 30's held form)."""
    text = ("Full Year EPAM expects the following for the full year: • EPAM expects GAAP diluted "
            "EPS will be in the range of $7.95 to $8.25 for the year, and non-GAAP diluted EPS "
            "will be in the range of $12.60 to $12.90 for the year.")
    got = _by(_guidance(text, "x"))
    assert [g[:2] + g[2:4] for g in got] == [("gaap diluted eps", got[0][1], 7.95, 8.25)], got
    assert not any(g[2] == 12.60 for g in got)


def test_a_non_gaap_diluted_eps_is_never_read_as_gaap() -> None:
    """Concentrix 8-K, verbatim: "Non-GAAP diluted EPS of $2.65 to $2.77" — both the `non-` and the
    `non-GAAP ` lookbehinds, on the real sentence. Since 2026-10-27 (§5.0 row 30) the range IS read,
    as ADJUSTED EPS; it was unread before, which is what this pin first asserted."""
    got = _by(_guidance("• Non-GAAP diluted EPS of $2.65 to $2.77, assuming approximately 62.4 "
                        "million diluted common shares outstanding", "x"))
    assert [(g[0], g[2], g[3]) for g in got] == [("adjusted eps", 2.65, 2.77)], got


def test_continues_to_plan_opens_a_run_and_a_plan_noun_does_not() -> None:
    """POSITIVE: TJX's Q3 FY26 release, verbatim — "continues to plan" read as the plan VERB, so the
    quarter's range is Q4 2026 (it fell to `next-fy` — annual — before). NEGATIVE: a results
    sentence ending "above the Company's plan" is not an opener's verb, so the guide below it is
    never labelled with that closed quarter."""
    q4 = ("For the fourth quarter of Fiscal 2026, the Company continues to plan consolidated "
          "comparable sales to be up 2% to 3%, pretax profit margin to be in the range of 11.7% to "
          "11.8%, and diluted earnings per share to be in the range of $1.33 to $1.36.")
    assert _by(_guidance(q4, "x")) == [("gaap diluted eps", "Q4 2026", 1.33, 1.36, "$/sh")]
    noun = ("For the second quarter of Fiscal 2027, comparable sales increased 4%, above the "
            "Company's plan. The Company expects diluted earnings per share to be in the range of "
            "$1.36 to $1.38.")
    assert _by(_guidance(noun, "x")) == [("gaap diluted eps", "next-fy", 1.36, 1.38, "$/sh")]


def test_the_adjusted_eps_field_never_takes_the_gaap_guide() -> None:
    """The valuation's adjusted-EPS field reads `adjusted eps` only: a release whose annual guide is
    GAAP alone leaves it UNKNOWN, rather than printing a GAAP figure as earnings power."""
    out = dm._release_adjusted_eps(
        [_rel("a", "2026-08-19", [_g("Fiscal 2027", 5.31, 5.36, metric="gaap diluted eps")])],
        _min_record(pe=30.0, price=146.99), _ABSENT)
    assert out.status is SourceStatus.UNKNOWN
