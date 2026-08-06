"""Capital created or destroyed — goodwill/intangibles remaining, buyback economics, acquisitions.

WHY. SMPL wrote off $391.9M of acquired brand value, borrowed ~$148M, and repurchased 11.65M
shares at an average $18.29 against an $11.33 market. The dossier could show none of it.

THE COVERAGE PROBE IS PART OF THE BUILD, and the first one was wrong in the direction that kills a
build: one tag per concept said "impairment 2/11, acquisition 3/11, SMPL has neither". Reading
SMPL's actual tag list found four impairment tags and a DIRECT average-price tag. Every pin below
runs against the LIVE COMMITTED CORPUS for that reason — a synthetic fixture would have agreed with
the wrong probe.
"""
from __future__ import annotations

import pathlib

import pytest

from vinci.dossier.capital_allocation import (
    ACQUISITION,
    BUYBACK_AVG_PRICE,
    build_capital_allocation,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.network        # reads EDGAR companyfacts (cached)


def _facts(ticker: str) -> dict:
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver
    return EdgarClient.from_config().companyfacts(
        EntityResolver.from_config().resolve_ticker(ticker).cik)


def _names() -> list[str]:
    return sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))


def test_balances_are_read_as_instants_not_annual_flows() -> None:
    """THE BUG THE CORPUS CAUGHT. Goodwill and intangibles are BALANCE-SHEET INSTANTS — SMPL
    reports 83 and 79 of them and ZERO annual durations — so the first cut asked `latest_annual`
    and rendered UNKNOWN on a name carrying a $1.5bn balance. A synthetic fixture built from the
    shape the code expected would have passed."""
    ca = build_capital_allocation(_facts("SMPL"))
    assert ca.goodwill.value and ca.goodwill.value > 500, ca.goodwill.note
    assert ca.intangibles.value and ca.intangibles.value > 900, ca.intangibles.note
    for f in (ca.goodwill, ca.intangibles):
        assert "as at" in (f.source_ref or ""), (
            f"a balance is stamped with a duration span: {f.source_ref}")


def test_smpl_reconciles_with_the_figures_already_on_its_page() -> None:
    """THE RECONCILIATION, against numbers a human already ruled on. `11.65M shares at $18.29` and
    the `$60.9M` intangible charge are on the committed page; if this block disagreed with them one
    of the two would be wrong and a reader could not tell which."""
    ca = build_capital_allocation(_facts("SMPL"))
    assert ca.buyback_shares.value == pytest.approx(11_651_767)
    assert ca.buyback_avg_price.value == pytest.approx(18.29)
    # …and the write-off the page calls "$391.9M LTM" is TWO periods, 60.9 + 331.0
    assert ca.intangible_impairment.value == pytest.approx(331.0, rel=1e-3)


def test_an_acquisition_is_the_largest_positive_never_the_latest_residual() -> None:
    """SIGN AND RECENCY BOTH MATTER, and 'latest' gets both wrong. SMPL carries +280.4 (FY2024) and
    −280.4 (FY2025, restating the SAME period_end), plus a −1.7 residual. Taking the latest annual
    point returned **−1.713** — a negative acquisition price, which is not a thing. Magnitude alone
    would coin-flip between the acquisition and its own reversal."""
    ca = build_capital_allocation(_facts("SMPL"))
    assert ca.acquisition_consideration.value == pytest.approx(280.409, rel=1e-4)
    for t in _names():
        v = build_capital_allocation(_facts(t)).acquisition_consideration.value
        assert v is None or v > 0, f"{t}: negative acquisition consideration {v}"


def test_the_acquisition_is_the_largest_across_the_whole_family_not_the_first_tag() -> None:
    """THE ONE KIND WHERE PREFERENCE ORDER IS THE WRONG RULE, caught on a name about to be
    underwritten for being acquisitive.

    Preference-first took the first tag carrying ANY data. EPAM states a **$7.0M**
    `BusinessCombinationConsiderationTransferred1` from **2017** and a **$912.2M**
    `PaymentsToAcquireBusinessesNetOfCashAcquired` from **2024** — so the block reported $7.0M, a
    **130x understatement** of acquisition spend. "What did they pay" is a question about the whole
    family; the tags are different definitions, which is why the winner is NAMED rather than
    blended."""
    ca = build_capital_allocation(_facts("EPAM"))
    assert ca.acquisition_consideration.value == pytest.approx(912.2, rel=1e-3), (
        f"EPAM's acquisition spend reads {ca.acquisition_consideration.value} — preference-first "
        "picks the 2017 $7.0M tag over the 2024 $912.2M one")
    # the property, over the corpus: no tag in the family holds a LARGER positive than the reported
    from vinci.edgar.concepts import points_for_tag
    for t in _names():
        facts, got = _facts(t), build_capital_allocation(_facts(t)).acquisition_consideration
        biggest = max((p.value for tag in ACQUISITION for p in points_for_tag(facts, tag)
                       if p.value and p.value > 0), default=None)
        if biggest is None:
            assert got.value is None, f"{t}: reported {got.value} with no positive point anywhere"
        else:
            assert got.value == pytest.approx(biggest / 1e6, rel=1e-6), (
                f"{t}: reported {got.value} but the family holds {biggest / 1e6}")


def test_the_average_price_is_labelled_a_period_average_not_a_purchase_price() -> None:
    """SMPL's $18.29 spans a stock that fell from roughly $30 to $11. Buying at $30 in September
    and $12 in June are OPPOSITE judgements and one number hides both, so the caveat travels ON the
    value — a reader must not take it as evidence of WHEN they bought."""
    ca = build_capital_allocation(_facts("SMPL"))
    note = ca.buyback_avg_price.note or ""
    assert "NOT a purchase price" in note and "timing" in note, note


def test_a_stale_average_is_either_replaced_by_a_current_derivation_or_flagged() -> None:
    """VINTAGE BEATS DIRECTNESS — `_latest_dep_amort`'s rule, same failure. EPAM's own
    average-price tag last reported **Q1 2023** ($283.69, on a stock now near $112) beside **Q1
    2026** repurchase cash. Two outcomes are acceptable and a silent third is not: derive over the
    current period when BOTH legs align there, else keep the stale figure and SAY the periods
    disagree. What must never happen is the two printed side by side as one window."""
    seen = 0
    for t in _names():
        ca = build_capital_allocation(_facts(t))
        avg, cash = ca.buyback_avg_price, ca.buyback_cash
        if avg.value is None or cash.value is None:
            continue
        seen += 1
        derived = str(avg.source_ref).startswith("DERIVED")
        same_window = str(avg.source_ref).split("(")[-1] == str(cash.source_ref).split("(")[-1]
        flagged = "PERIOD MISMATCH" in (avg.note or "")
        assert derived or same_window or flagged, (
            f"{t}: a direct average over a different window than the cash beside it, with nothing "
            f"saying so — avg {avg.source_ref} vs cash {cash.source_ref}")
    assert seen >= 5, f"only {seen} names exercised this — near-vacuous"


def test_every_absence_names_the_tags_that_were_tried() -> None:
    """"Not found" invites nothing; naming the family invites a correction. A reader who knows the
    filer uses a fifth tag can only say so if the four tried are on the page."""
    for t in _names():
        for name, f in build_capital_allocation(_facts(t)):
            if name == "brand_split" or f.value is not None:
                continue
            assert f.note and "EDGAR XBRL companyfacts" in f.note, f"{t}.{name}: {f.note}"
            if name == "acquisition_consideration":
                assert all(tag in f.note for tag in ACQUISITION), f"{t}: {f.note}"


def test_the_brand_split_is_a_stated_gap_on_every_name() -> None:
    """WHAT IS NOT HERE MUST SAY SO. Goodwill separates from intangibles by TAG, but the per-BRAND
    dimension (SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Left
    silent, the aggregate reads as though the split simply were not interesting."""
    for t in _names():
        bs = build_capital_allocation(_facts(t)).brand_split
        assert bs.value is None and bs.note
        assert "no XBRL axis" in bs.note and "10-K" in bs.note, bs.note


def test_the_derivation_requires_both_legs_on_the_same_period() -> None:
    """SAME PERIOD ON BOTH LEGS OR NOTHING — `_latest_dep_amort`'s rule, and the first cut broke it
    while ASSERTING it: the note read "both legs are the same fiscal year" and nothing checked.

    VITL divided **Q1-2026 cash ($20.0M) by a 2019 share count** and published **$7.01** as a
    derived average — a seven-year straddle and a number that never existed. An assertion the code
    does not enforce is worse than no assertion, because it tells the reader not to look.

    Asserted over the CORPUS, not a fixture: the straddle was invisible until the live names ran."""
    from vinci.dossier.capital_allocation import BUYBACK_CASH, BUYBACK_SHARES, _pick

    checked = 0
    for t in _names():
        facts = _facts(t)
        c, s = _pick(facts, BUYBACK_CASH, kind="flow"), _pick(facts, BUYBACK_SHARES, kind="flow")
        avg = build_capital_allocation(facts).buyback_avg_price
        if c is None or s is None or str(avg.source_ref or "").startswith("EDGAR"):
            continue                      # no legs, or the filer's own direct tag answered
        checked += 1
        aligned = (c[0].period_start == s[0].period_start and c[0].period_end == s[0].period_end)
        if aligned:
            assert avg.value is not None and "verified on" in (avg.note or ""), (
                f"{t}: aligned legs but no derivation — {avg.note}")
        else:
            assert avg.value is None and "DIFFERENT periods" in (avg.note or ""), (
                f"{t}: derived an average across MISMATCHED periods — cash "
                f"{c[0].period_start}→{c[0].period_end} vs shares "
                f"{s[0].period_start}→{s[0].period_end}, value {avg.value}")
    assert checked >= 3, f"only {checked} names exercised the derivation branch — near-vacuous"


def test_the_derivation_is_refused_rather_than_imputed_from_one_leg() -> None:
    """FAIL LOUD, NEVER FABRICATE. Cash without a share count says nothing about price. An average
    invented from one leg would be a decision figure in the strict sense."""
    cash_only = {"facts": {"us-gaap": {"PaymentsForRepurchaseOfCommonStock": {"units": {"USD": [
        {"start": "2025-01-01", "end": "2025-12-31", "val": 1e8, "filed": "2026-01-15",
         "fy": 2025, "fp": "FY", "form": "10-K", "accn": "x"}]}}}}}
    ca = build_capital_allocation(cash_only)
    assert ca.buyback_cash.value == pytest.approx(100.0)
    assert ca.buyback_avg_price.value is None
    assert "imputed" in (ca.buyback_avg_price.note or "")


def test_an_empty_facts_dict_yields_a_fully_stated_block_not_a_crash() -> None:
    """TOTAL ON ITS INPUT. The assembler passes `{}` when companyfacts is unavailable, so every
    field must degrade to UNKNOWN-with-reason rather than raising into the build."""
    ca = build_capital_allocation({})
    for name, f in ca:
        assert f.value is None and f.note, name
    assert BUYBACK_AVG_PRICE[0] in (ca.buyback_avg_price.note or "")


def test_a_failed_fetch_leaves_the_block_absent_not_a_block_of_stated_absences() -> None:
    """A FETCH FAILURE IS NOT AN EMPTY FILING, and the first cut made them identical.

    On an EDGAR error the transform collapsed to `{}`, so every field wrote "no goodwill balance
    under Goodwill — EDGAR XBRL companyfacts": a sentence stating the FILER reports none, when the
    truth is WE could not reach EDGAR. Two opposite facts in one sentence — `unstated` vs
    `disagrees`, grown-out vs failed — and here the wrong reading is the reassuring one.

    ABSENT already means NOT YET REFRESHED, which is exactly what a failed fetch leaves behind."""
    import vinci.dossier.refresh as rf
    from vinci.netcache import HttpError

    class _Boom:
        @staticmethod
        def from_config() -> _Boom:
            return _Boom()

        def companyfacts(self, cik: str) -> dict:
            raise HttpError("EDGAR unreachable")

    import vinci.edgar.client as ec
    real = ec.EdgarClient
    ec.EdgarClient = _Boom  # type: ignore[misc,assignment]
    try:
        out = rf.capital_allocation_transform("0001702744")({"stock_info": {"x": 1}})
    finally:
        ec.EdgarClient = real  # type: ignore[misc]
    assert "capital_allocation" not in out, (
        "a failed fetch wrote a block of stated absences — indistinguishable from a filer that "
        "genuinely reports none")
    assert out == {"stock_info": {"x": 1}}, "the transform mutated something else on failure"

    # …and a name with NO cik is the same case, not a filing full of nothing
    assert "capital_allocation" not in rf.capital_allocation_transform(None)({})


def test_the_block_reads_differently_on_a_name_that_impaired_and_one_that_never_has() -> None:
    """THE LAYOUT TEST. If the block reads the same on SMPL (a live charge) and EPAM ($1.59bn never
    written down), it is not telling the reader the thing they came for.

    The first cut FAILED this: EPAM printed "Goodwill impairment: $0.7M" from FY2022 beside a
    2026-03-31 balance, which reads as a measurement of the current period. The staleness IS the
    finding — so the extractor marks it (it holds both dates) and the render says so in words.

    AND THE STALE RULE IS TRAILING-TWELVE-MONTHS, not a calendar-year compare. The year rule was
    too blunt by exactly the amount that matters: IT's $150.0M FY2025 charge ends 2025-12-31
    against a 2026-06-30 balance — six months apart, different years — and was SUPPRESSED off the
    page entirely."""
    from vinci.dossier.render import _capital_allocation
    from vinci.dossier.schemas import MechanicalLayer

    def block(t: str) -> str:
        import json
        doc = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
        m = MechanicalLayer.model_validate(doc["mechanical"]).model_copy(
            update={"capital_allocation": build_capital_allocation(_facts(t))})
        return "\n".join(_capital_allocation(m))

    smpl, epam, it = block("SMPL"), block("EPAM"), block("IT")
    assert "Intangible impairment" in smpl and "NONE IN THE CURRENT PERIOD" not in smpl
    assert "NONE IN THE CURRENT PERIOD" in epam, "a name that never impaired reads as one that did"
    assert "years before the balance" in epam, "the staleness is not quantified"
    # IT impaired RECENTLY — six months is inside the balance's trailing year, so it must PRINT
    assert "Goodwill impairment" in it and "150.0" in it, (
        "IT's $150.0M FY2025 charge was suppressed — the stale rule is comparing calendar years "
        "rather than trailing twelve months")
    assert "NONE IN THE CURRENT PERIOD" not in it
    assert smpl != epam != it, "three names, three shapes"


def test_every_caveat_reaches_the_surface_not_just_the_json() -> None:
    """CAVEATS TRAVEL ONTO THE PAGE. `_fact` prints a note only when the fact is ABSENT, so a
    PERIOD MISMATCH on two PRESENT values is silently dropped — EPAM states buyback cash over 89
    days and its share count over 364, and printed adjacent they invite the exact division the
    average-price guard refuses."""
    import json

    from vinci.dossier.render import _capital_allocation
    from vinci.dossier.schemas import MechanicalLayer
    doc = json.loads((ROOT / "data" / "dossiers" / "EPAM" / "dossier.json").read_text())
    m = MechanicalLayer.model_validate(doc["mechanical"]).model_copy(
        update={"capital_allocation": build_capital_allocation(_facts("EPAM"))})
    page = "\n".join(_capital_allocation(m))
    assert page.count("PERIOD MISMATCH") == 2, (
        "both mismatches must surface: the average vs cash, AND cash vs the share count")
    assert "NOT a purchase price" in page and "not evidence of when they bought" in page
    assert "NOT AVAILABLE FROM XBRL" in page and "10-K impairment note" in page
    assert page.count("NOT AVAILABLE FROM XBRL") == 1, "the stated gap is doubled"


def test_every_css_class_the_web_twin_emits_is_defined() -> None:
    """THE WEB TWIN WAS NEVER PREVIEWED — only the markdown was, and the two fail differently.

    The first cut used `.ds-sub` as a WRAPPER (it is a margin utility applied to a `subtitle muted`
    line) and invented `.ds-subtitle`, which has ZERO rules in `styles.css`. The markdown preview
    looked correct throughout, because markdown has no classes. A class that does not exist fails
    SILENTLY — the block renders unstyled rather than erroring — which is why this is a pin and not
    a thing to remember to check.

    Scoped to the function this PR adds. Widening it to the whole file is a separate decision."""
    import re

    js = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    css = (ROOT / "frontend" / "assets" / "styles.css").read_text()
    body = js[js.index("function capitalAllocation(m) {"):]
    body = body[:body.index("\nfunction ")]
    emitted = {c for attr in re.findall(r'class="([^"$]+)"', body) for c in attr.split()}
    assert emitted, "no classes found — the extraction is wrong, not the markup"
    missing = sorted(c for c in emitted if not re.search(rf"\.{re.escape(c)}\b", css))
    assert not missing, (
        f"the web twin emits CSS classes with no rule in styles.css: {missing}. They fail "
        "silently — the block renders unstyled and the markdown preview cannot show it.")
