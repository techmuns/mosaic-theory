"""THE PER-SHARE DENOMINATOR HAD NO DILUTED POINT-IN-TIME FORM, and the input it used was mis-dated.

Two defects, one field. EDGAR reports a BASIC point-in-time count (dei cover page) and a DILUTED
AVERAGE over a period; neither is a diluted valuation-date divisor, so it is derived by overlay.

THE MIS-DATING, measured on the committed fleet before the fix: `_latest_point` sorted by
`(period_end, filed)`, and a 10-Q tags the discrete quarter AND the year-to-date span with the SAME
end and the SAME filed date — so the tie broke arbitrarily and **4 of 11 names got a cumulative
period**: SMPL a 272-day nine-month figure 4.16% above its quarter (93,677,801 vs 89,940,680), FUBO
181-day −2.17%, BRBR +1.02%, CNXC +0.35%. SMPL's committed scenario record carries the basis string
"diluted weighted-average (latest 10-Q)" over the nine-month number — a denominator whose stated
basis is not what it is, which is the defect class this work exists to close.

THE FORM WAS MEASURED, NOT ARGUED. additive vs multiplicative agree within 0.033% on every fleet
name; additive is picked on robustness (no division by a possibly-small basic average) and its
assumption is stated in the units the instruments exist in.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest

from vinci.dossier.dilution import (
    BASIC_WA_TAG,
    DILUTED_WA_TAG,
    denominator_note,
    diluted_outstanding,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _facts(rows: list[tuple[str, str | None, str, float, str]]) -> dict:
    """companyfacts shaped as EDGAR ships it: (tag, start, end, val, filed)."""
    out: dict[str, dict] = {}
    for tag, start, end, val, filed in rows:
        node = out.setdefault(tag, {"units": {"shares": []}})
        node["units"]["shares"].append(
            {"start": start, "end": end, "val": val, "filed": filed, "form": "10-Q"})
    return {"facts": {"us-gaap": out}}


# SMPL's real shape: one 10-Q tagging a discrete quarter and a nine-month cumulative, same end
# date, same filing date. The cumulative average is HIGHER because the company is buying back.
SMPL_SHAPE = _facts([
    (BASIC_WA_TAG, "2025-08-31", "2026-05-30", 93_677_801, "2026-07-09"),
    (BASIC_WA_TAG, "2026-03-01", "2026-05-30", 89_940_680, "2026-07-09"),
    (DILUTED_WA_TAG, "2025-08-31", "2026-05-30", 93_677_801, "2026-07-09"),
    (DILUTED_WA_TAG, "2026-03-01", "2026-05-30", 89_940_680, "2026-07-09"),
])


def test_the_discrete_quarter_wins_over_the_cumulative_sharing_its_end_date() -> None:
    """THE RED. Both spans end 2026-05-30 and were filed 2026-07-09, so `(period_end, filed)` alone
    cannot separate them and picked the nine-month figure 4.16% high. The quarter must win."""
    d = diluted_outstanding(SMPL_SHAPE, basic_out=88_460_545)
    assert d.basic_wa == 89_940_680, "the nine-month cumulative was selected again"
    assert d.period_start == dt.date(2026, 3, 1) and d.period_end == dt.date(2026, 5, 30)
    # the value the old ordering returned, pinned so a regression is unmistakable
    assert d.basic_wa != 93_677_801


def test_the_latest_point_selector_itself_prefers_the_shortest_span() -> None:
    """The fix lives in `anchor._latest_point`, which is what the committed anchor blocks read —
    fixing only the new module would leave the shipped denominator mis-dated."""
    from vinci.dossier.anchor import _DILUTED_TAG, _latest_point

    p = _latest_point(SMPL_SHAPE, _DILUTED_TAG)
    assert p is not None and p.value == 89_940_680, "the anchor still reads the cumulative"
    assert (p.period_end - p.period_start).days == 90  # type: ignore[operator]


def test_both_legs_come_from_the_same_period_even_when_only_one_tag_has_the_quarter() -> None:
    """A delta taken across two different periods is not a dilution figure. Where the tags do not
    share the quarter, the pairing must fall back to a period BOTH report, not mix them."""
    mixed = _facts([
        (BASIC_WA_TAG, "2026-01-01", "2026-03-31", 100_000_000, "2026-05-01"),
        (DILUTED_WA_TAG, "2026-01-01", "2026-03-31", 104_000_000, "2026-05-01"),
        # a diluted-only stub at a LATER end date — pairing it with the basic above would report a
        # 20% increment that no filing states
        (DILUTED_WA_TAG, "2026-04-01", "2026-06-30", 120_000_000, "2026-08-01"),
    ])
    d = diluted_outstanding(mixed, basic_out=100_000_000)
    assert d.increment == 4_000_000, d
    assert d.period_end == dt.date(2026, 3, 31), "an unpaired later period was used"


def test_a_restated_period_takes_the_later_filing() -> None:
    """The same quarter is re-reported in later filings; the newest restatement is the live one."""
    restated = _facts([
        (BASIC_WA_TAG, "2026-01-01", "2026-03-31", 100_000_000, "2026-05-01"),
        (BASIC_WA_TAG, "2026-01-01", "2026-03-31", 100_500_000, "2026-08-01"),
        (DILUTED_WA_TAG, "2026-01-01", "2026-03-31", 104_000_000, "2026-05-01"),
        (DILUTED_WA_TAG, "2026-01-01", "2026-03-31", 104_900_000, "2026-08-01"),
    ])
    d = diluted_outstanding(restated, basic_out=100_000_000)
    assert (d.basic_wa, d.diluted_wa) == (100_500_000, 104_900_000), d


# --- the refusals: never a basic count behind a diluted label ------------------------------------


def test_a_missing_pair_refuses_rather_than_returning_the_basic_count() -> None:
    """THE SUBSTITUTION THIS EXISTS TO STOP. Falling back to `basic_out` would put an undilated
    number behind a diluted label — invisible, and wrong in the permissive direction for a name
    with heavy dilution (MVST's increment is 15.9% of its count)."""
    basic_only = _facts([(BASIC_WA_TAG, "2026-01-01", "2026-03-31", 100_000_000, "2026-05-01")])
    d = diluted_outstanding(basic_only, basic_out=100_000_000)
    assert d.shares is None, "a basic count came back wearing a diluted label"
    assert DILUTED_WA_TAG in d.reason


def test_no_cover_page_count_refuses() -> None:
    """The overlay needs something to dilute; there is no defaulting to the weighted average."""
    for absent in (None, 0.0, -5.0):
        d = diluted_outstanding(SMPL_SHAPE, basic_out=absent)
        assert d.shares is None and "nothing to dilute" in d.reason


def test_a_diluted_average_below_basic_is_refused_as_a_tagging_error() -> None:
    """Impossible under ASC 260, and the failure mode is the dangerous direction: a negative
    increment would hand back a denominator SMALLER than the basic count, inflating per-share
    value. Refuse rather than subtract."""
    inverted = _facts([
        (BASIC_WA_TAG, "2026-01-01", "2026-03-31", 100_000_000, "2026-05-01"),
        (DILUTED_WA_TAG, "2026-01-01", "2026-03-31", 96_000_000, "2026-05-01"),
    ])
    d = diluted_outstanding(inverted, basic_out=100_000_000)
    assert d.shares is None and "below its basic" in d.reason.lower()


def test_an_instant_fact_is_never_taken_as_a_weighted_average() -> None:
    """A weighted average is always a duration. A `start`-less point is a balance-sheet instant and
    must not be paired, or the increment is a difference between two unlike things."""
    instants = _facts([
        (BASIC_WA_TAG, None, "2026-03-31", 100_000_000, "2026-05-01"),
        (DILUTED_WA_TAG, None, "2026-03-31", 104_000_000, "2026-05-01"),
    ])
    assert diluted_outstanding(instants, basic_out=100_000_000).shares is None


# --- zero dilution is a REPORTED state, not an unchecked one -------------------------------------


def test_zero_dilution_is_a_distinct_state_and_the_note_says_it_was_reported() -> None:
    """VISIBLE-ABSENCE RULE on the denominator. Three of eleven fleet names report basic == diluted
    (FUBO correctly, on a loss; SMPL and VITL by the filer's tagging). The number is identical to
    the basic count either way, so only the note distinguishes 'the filer reports none' from 'we
    never looked' — and for a profitable name that distinction is the whole finding."""
    d = diluted_outstanding(SMPL_SHAPE, basic_out=88_460_545)
    assert d.is_zero_dilution and d.shares == 88_460_545
    note = denominator_note(d)
    assert "reports NO dilutive difference" in note
    assert "reported zero, not an unchecked one" in note


def test_zero_dilution_is_false_on_a_refused_result() -> None:
    """REVIEW FINDING. The property tested the increment alone, so a REFUSED pair whose increment
    was a small NEGATIVE — an inverted tagging error of half a share — answered True. A property
    that speaks for a result which does not exist reads as "checked, none found" on exactly the
    pair the module refused, which is the guard-that-cannot-fire class in a different costume."""
    inverted = _facts([
        (BASIC_WA_TAG, "2026-01-01", "2026-03-31", 100_000_000.0, "2026-05-01"),
        (DILUTED_WA_TAG, "2026-01-01", "2026-03-31", 99_999_999.5, "2026-05-01"),
    ])
    d = diluted_outstanding(inverted, basic_out=100_000_000)
    assert d.shares is None and d.increment == pytest.approx(-0.5)
    assert not d.is_zero_dilution, "a refused result claimed the filer reported no dilution"


def test_the_note_states_the_carry_forward_assumption_and_the_exclusions() -> None:
    """A per-share value whose divisor is unexplained cannot be checked by the human, which is what
    source-binding is for. Both the assumption and what the filer's average omits must print."""
    diluting = _facts([
        (BASIC_WA_TAG, "2026-01-01", "2026-03-31", 332_360_000, "2026-05-01"),
        (DILUTED_WA_TAG, "2026-01-01", "2026-03-31", 385_272_000, "2026-05-01"),
    ])
    note = denominator_note(diluted_outstanding(diluting, basic_out=333_157_384))
    assert "has not moved since" in note                 # the carry-forward assumption
    assert "antidilutive" in note and "treasury-stock" in note
    assert "386,069,384" in note                          # the derived count itself


def test_a_refusal_note_says_unavailable_rather_than_printing_a_number() -> None:
    """The note is the surface; a refusal must not reach it as a silent basic count."""
    note = denominator_note(diluted_outstanding({"facts": {}}, basic_out=100_000_000))
    assert note.startswith("Diluted share count UNAVAILABLE")


# --- the corpus ----------------------------------------------------------------------------------
#
# THESE PINS ARE CACHE-ONLY, AND THE WIRE IS BLOCKED WHILE THEY RUN (review finding on #283).
#
# The first cut built a live ``EdgarClient`` and wrapped each fetch in ``except Exception:
# pytest.skip("EDGAR facts unavailable offline")``. `data/dossiers` is COMMITTED but `data/cache` is
# git-ignored, so on a fresh checkout the `is_dir()` guard passes, the cache misses, and
# ``companyfacts`` goes to the wire — inside ``pytest -m "not network"``. MEASURED in a cleanroom
# with `socket.create_connection` blocked: a cold cache attempts a live call, it does not degrade.
#
# Both outcomes were wrong. With egress, ~33 live SEC requests run in the gate that exists to be
# offline; without it, the broad `except` swallows the failure and every corpus pin SILENTLY passes
# by skipping — the guard-that-cannot-fire class, in the pins written to prevent it. Every other
# EDGAR test in this suite (`test_anchor`, `test_band_guards`) uses a synthetic fixture; these were
# the only ones reaching for a real client, and the repo already has `@pytest.mark.network` for
# tests that mean it.
#
# The fixture skips on an ABSENT CACHE — a deterministic, stated condition — and blocks outbound
# connections for the duration, so a cache miss fails LOUDLY instead of quietly fetching.


FIXTURE_DIR = ROOT / "tests" / "fixtures" / "companyfacts"


@pytest.fixture
def facts_for() -> object:
    """Committed companyfacts subsets — the pins GATE now, they no longer depend on a warm cache.

    THE CLOSE OF D17. `data/cache` is git-ignored, so on any fresh checkout — including every CI
    run — these three pins found a cold cache and skipped. They had never gated since the day they
    were written. The fixture is generated by `scripts/build_companyfacts_fixture.py`, which keeps
    only the tags a real instrumented run showed these pins reading, and it is VERIFIED EQUIVALENT
    to the live cache on all eleven names across every field the pins consume.

    A MISSING FIXTURE FAILS. It does not skip — that is the whole point of the change, and a skip
    here would restore exactly the state this removes. The network stays blocked so nothing can
    silently fall back to a live fetch.
    """
    import socket

    real = socket.create_connection

    def refuse(*_a: object, **_k: object) -> object:
        raise AssertionError(
            "a corpus pin reached for the network — these read committed fixtures only. If a pin "
            "needs a tag the fixture lacks, add it to FIXTURE_TAGS and regenerate; never fetch.")

    socket.create_connection = refuse  # type: ignore[assignment]

    def load(ticker: str) -> dict:
        path = FIXTURE_DIR / f"{ticker}.json"
        assert path.is_file(), (
            f"no committed companyfacts fixture for {ticker} ({path}). Run "
            "`python scripts/build_companyfacts_fixture.py` — in the SAME PR that re-assembles the "
            "name, so the fixture cannot drift from the artifacts the pins check it against.")
        return json.loads(path.read_text())

    try:
        yield load
    finally:
        socket.create_connection = real  # type: ignore[assignment]



def _basic_out(f: dict) -> float | None:
    """The point-in-time basic count, resolved through the "shares" CONCEPT — never one tag.

    ISSUED IS NOT OUTSTANDING (review of #512). The concept chain ends in
    ``CommonStockSharesIssued``, which for a filer holding treasury stock exceeds the outstanding
    count; feeding it to the overlay as ``basic_out`` would inflate the denominator and the failure
    would read as the overlay's fault. No committed name falls through to it today (measured), so
    this REFUSES rather than silently accepting the wrong basis the day one does.
    """
    from vinci.edgar.concepts import extract_points

    pts = extract_points(f, "shares")
    if not pts:
        return None
    c = max(pts, key=lambda p: (p.period_end, p.filed))
    assert c.tag != "CommonStockSharesIssued", (
        f"shares resolved via {c.tag}: issued shares are not outstanding shares for a filer with "
        f"treasury stock — the overlay needs the outstanding count, not the issued one")
    return c.value

def test_the_overlay_serves_every_committed_name_and_none_falls_back(
    facts_for: object,
) -> None:
    """NON-VACUOUS: runs on the real fleet, so an extraction that stops resolving reds here rather
    than in a rendered page. Measured when written: 11 of 11 servable, uplift 0.00%–15.88%."""
    db = ROOT / "data" / "dossiers"
    if not db.is_dir():
        pytest.skip("no local dossiers in this worktree")

    #: EXEMPTIONS, KEYED ON THE REASON — never a bare roster, so a new name is in scope the day it
    #: lands and an exemption self-clears if the filer's tagging changes.
    #:
    #: V reports every common-share figure PER SHARE CLASS, and this API view surfaces only
    #: undimensioned facts: no period carries both the basic and diluted weighted-average tags, so
    #: the overlay has nothing to compute from and refuses. That refusal is CORRECT and it holds
    #: the line — V's committed anchor is None, and no per-share figure on its page is built from
    #: the 2010 cover-page count the same gap leaves behind (tests/test_share_basis.py).
    exempt = {"V": "multi-class filer: no undimensioned basic+diluted weighted-average pair"}

    names = sorted(p.name for p in db.iterdir() if p.is_dir())
    served, zero = [], []
    for t in names:
        f = facts_for(t)  # type: ignore[operator]
        # THE CONCEPT, NOT ONE TAG (MC1, 2026-08-28). This read
        # `points_for_tag("EntityCommonStockSharesOutstanding")` — the dei cover-page tag alone —
        # while `concepts.py` has mapped the "shares" CONCEPT to that tag with us-gaap fallbacks
        # all along. ALPHABET DOES NOT TAG THE COVER-PAGE COUNT AT ALL: live EDGAR for CIK
        # 0001652044 carries exactly one dei tag, EntityPublicFloat. Its count is there under
        # us-gaap:CommonStockSharesOutstanding (12,230,000,000 at 2026-06-30), which the chain
        # already reaches — so this call site was the only thing withholding it. Resolving through
        # the concept changes NOTHING for the names that do tag the cover page (SMPL and V both
        # still resolve via EntityCommonStockSharesOutstanding, byte-identical values).
        out = _basic_out(f)
        d = diluted_outstanding(f, basic_out=out)
        if t in exempt:
            assert d.shares is None, (
                f"{t} is exempt ({exempt[t]}) but the overlay now SERVES it — the filer changed "
                f"its tagging, so drop the exemption rather than keep a stale carve-out")
            continue
        assert d.shares is not None, f"{t}: {d.reason}"
        assert d.shares >= d.basic_out, f"{t}: diluted below basic"
        served.append(t)
        if d.is_zero_dilution:
            zero.append(t)
    assert len(served) == len(names) - len(exempt)
    # The zero-dilution set is REPORTED, not pinned to a fixed list — a filer that starts tagging
    # dilution must not red this. What must hold is that the state stays DISTINGUISHABLE on the
    # surface, since the number itself is identical to the basic count.
    # (Review finding: the first cut asserted `set(zero) <= set(names)`, which is true by
    # construction — `zero` is built from `names`. A vacuous assertion dressed as a check.)
    assert zero, "no zero-dilution name found — measured at 3 of 11; the state may have gone silent"
    for t in zero:
        f = facts_for(t)  # type: ignore[operator]
        out = _basic_out(f)   # SIBLING of the lookup above — same concept, same reason
        assert "reported zero, not an unchecked one" in denominator_note(
            diluted_outstanding(f, basic_out=out)), t


#: Committed anchors whose ``anchor_base_value_per_share`` diverges from a fresh recompute.
#:
#: It held ``{BRBR, CNXC, SMPL}`` for exactly one PR (the backfill ran 2026-07-31): SMPL
#: 41.60→43.33 (+4.16%), BRBR 55.41→55.97 (+1.02%), CNXC 62.33→62.55 (+0.35%), each the
#: cumulative-period defect leaving the committed artifact.
#:
#: It held ``{AMZN, VRRM, WLK}`` for one PR (#684, 2026-10-08, §5.0 row 27): the net-debt cash leg
#: began netting short-term securities at the cash instant, and the backfill landed it on the
#: pages the same day — AMZN 245.46→249.57, WLK 104.35→105.98, VRRM 21.75→21.79 (GOOGL
#: 197.01→212.17 and UBER's net debt moved too; this pin cannot see either). **EMPTY AGAIN**, the
#: load-bearing state: committed JSON and a fresh recompute agree on every applicable anchor.
#:
#: It holds ``{BURL, TGT, WERN}`` from §5.0 row 27 (1) (2026-10-19): net debt is read by ONE builder
#: with every line at one balance-sheet date. BURL 183.42→185.55 (+1.16%; net debt 5,338→5,202,
#: CIQ's own figure), TGT 137.57→140.10 (+1.84%; 14,804→13,650 against CIQ's 13,785), WERN
#: 30.82→30.96 (+0.46%; 897→888 against CIQ's 889). This pin cannot see the rest: AMZN's net debt
#: +1,096 (base −0.04%, under the bar), UBER's 7,565→9,562, NFLX's UNKNOWN→7,512 (its committed
#: base is null), TECX's −208→refused (`docs/records/2026-10-19-net-debt-one-builder.md`).
ANCHORS_AWAITING_BACKFILL: set[str] = {"BURL", "TGT", "WERN"}

#: Committed anchors whose base cannot be reproduced from EDGAR alone — the CIQ workbook supplied a
#: fact EDGAR does not carry, and this recompute passes ``ciq=None`` deliberately. Named rather than
#: skipped: the first cut counted them toward the anti-vacuity floor while never comparing them, so
#: the floor could be met entirely by anchors nothing had checked.
BRIDGE_ONLY_ANCHORS: set[str] = {"GOOGL", "NFLX", "IT", "LLY"}


def test_the_period_fix_moves_the_committed_anchor_and_exactly_these_names(
    facts_for: object,
) -> None:
    """REVIEW FINDING — the fix has TWO consumers and only one was measured.

    `anchor_base_value_per_share` is `equity ÷ dil.value` (anchor.py), and `tagger._leverage` and
    `audit_r1.check_leverage` read it — so correcting the period moves a value committed in
    `dossier.json`, not just the scenario engine's reward:risk. The PR measured the engine and said
    nothing about the anchor.

    This pin is the invariant: the divergence set must be EXACTLY the recorded backfill list. A new
    name drifting in reds it; the backfill landing reds it too, which forces STATE to track the
    artifacts rather than describe them. **The backfill has now run and the list is EMPTY**, so from
    here this asserts committed JSON and a fresh recompute agree on every applicable anchor.

    The recompute passes ``ciq=None`` DELIBERATELY. With the workbook bridge attached, FUBO and IT
    also read as changed — but for PRE-EXISTING vendor fills (FUBO's `net_debt` None→170.4, IT's
    `ltm_fcf` None→1257.9) that predate this work and belong to their own decision. Including the
    bridge here would fold two unrelated backlogs into one pin and neither would be actionable."""
    import json
    from datetime import UTC, datetime

    from vinci.dossier.anchor import compute_anchor

    dd = ROOT / "data" / "dossiers"
    if not dd.is_dir():
        pytest.skip("no local dossiers in this worktree")
    diverged, unvalued, compared = set(), set(), 0
    for p in sorted(dd.iterdir()):
        doc = p / "dossier.json"
        if not doc.is_file():
            continue
        d = json.loads(doc.read_text())
        committed = (d.get("anchor") or {}).get("anchor_base_value_per_share")
        if committed is None:
            continue  # anchor inapplicable — no base value to compare
        f = facts_for(p.name)  # type: ignore[operator]
        fresh = compute_anchor(d.get("mechanical") or {}, facts=f,
                                 computed_at=datetime(2026, 7, 31, tzinfo=UTC), ciq=None)
        # COUNT WHAT WAS ACTUALLY COMPARED (review of #534). `compared` was incremented BEFORE the
        # None-skip, so a name the recompute could not value still raised the floor — the
        # anti-vacuity guard counted anchors it never compared. GOOGL and NFLX are exactly that
        # case: their committed bases come from the CIQ bridge, this recompute passes `ciq=None`
        # deliberately, so both yield None here and neither is a comparison.
        if fresh.anchor_base_value_per_share is None:
            unvalued.add(p.name)
            continue
        compared += 1
        if abs(fresh.anchor_base_value_per_share / committed - 1) > 0.001:
            diverged.add(p.name)
    assert compared >= 5, f"only {compared} anchors reached the comparison — near-vacuous"
    assert unvalued <= BRIDGE_ONLY_ANCHORS, (
        f"a committed anchor the ciq=None recompute cannot value, and not a known bridge-only "
        f"name: {sorted(unvalued - BRIDGE_ONLY_ANCHORS)}. Either its base stopped being "
        f"reproducible from EDGAR alone, or it belongs in BRIDGE_ONLY_ANCHORS with its reason")
    assert diverged == ANCHORS_AWAITING_BACKFILL, (
        f"committed anchors diverging from a fresh recompute: {sorted(diverged)}, recorded: "
        f"{sorted(ANCHORS_AWAITING_BACKFILL)}. If the backfill has run, shrink the list and update "
        "STATE; if a NEW name drifted, something moved the anchor inputs without a record.")


def test_the_committed_records_dilution_matches_the_quarter_not_a_cumulative(
    facts_for: object,
) -> None:
    """THE FLEET INSTANCE OF THE MIS-DATING. `facts.diluted_shares` agrees with the extraction on
    7 of 7 records — so a mis-dated extraction is a mis-dated record. SMPL is the one name where
    the committed value is a nine-month average; this pins the SELECTOR, so once the record is
    refreshed through the fixed path the two agree on the quarter."""
    import json

    from vinci.dossier.anchor import _DILUTED_TAG, _latest_point

    recs = ROOT / "scenarios"
    if not recs.is_dir():
        pytest.skip("no scenario records in this worktree")
    checked = 0
    for f_ in sorted(recs.glob("*.json")):
        if f_.stem.startswith("_"):
            continue
        ds = (json.loads(f_.read_text()).get("facts") or {}).get("diluted_shares") or {}
        if ds.get("value") is None:
            continue
        cf = facts_for(f_.stem)  # type: ignore[operator]
        p = _latest_point(cf, _DILUTED_TAG)
        assert p is not None, f_.stem
        span = (p.period_end - p.period_start).days if p.period_start else 0
        assert span <= 100, (
            f"{f_.stem}: the selector returned a {span}-day span — a cumulative period is being "
            "read as 'the latest 10-Q's weighted average' again")
        checked += 1
    assert checked >= 5, f"only {checked} records reached the assertion — the pin is near-vacuous"


# --- the writer: a value that changes MEANING must move its basis with it ------------------------


def test_a_refresh_may_restate_the_basis_and_logs_it_separately() -> None:
    """THE WRITER HAD THE ITEM'S OWN DEFECT. `refresh_record` moved the VALUE and froze the basis,
    so swapping `diluted_shares` from a weighted average to a point-in-time outstanding count would
    have left the string "diluted weighted-average (latest 10-Q)" over a number that is neither
    weighted nor an average. `Fact.basis` documents itself as naming WHAT the number is; a writer
    that moves one and not the other MANUFACTURES a mislabelled figure."""
    import vinci.scenarios as sc

    rec = sc.read_record("SMPL", root=ROOT)
    old = rec.facts["diluted_shares"]
    # THE QUANTITY IS DECLARED (2026-08-21). This pin genuinely IS about `diluted_shares` — its
    # subject is the weighted-average -> outstanding swap — so it keeps the fact and states the
    # quantity, which is what the guard asks of every caller on this path. Declaring the SAME
    # quantity the record already carries is a restatement; declaring the other one is the swap
    # `test_quantity_kind_guard` refuses.
    new = sc.Fact(value=old.value - 1.0, unit=old.unit, basis="diluted shares OUTSTANDING",
                  source="EDGAR dei + us-gaap weighted averages", quantity_kind="outstanding")
    out = sc.refresh_record(rec, facts={"diluted_shares": new}, source="s", on_date="2026-07-31")
    assert out.facts["diluted_shares"].basis == "diluted shares OUTSTANDING"
    assert out.facts["diluted_shares"].source == "EDGAR dei + us-gaap weighted averages"
    added = {e.field for e in out.refresh_log[len(rec.refresh_log):]}
    assert added == {"facts.diluted_shares", "facts.diluted_shares.basis",
                     "facts.diluted_shares.source"}, added
    for e in out.refresh_log[len(rec.refresh_log):]:
        assert e.old != e.new, f"{e.field}: a log entry claiming a change that did not happen"


def test_a_source_only_restatement_does_not_log_a_phantom_basis_change() -> None:
    """REVIEW FINDING. The first cut logged a `.basis` entry whenever EITHER basis or source moved,
    so a source-only restatement wrote `old == new` — a log claiming a change that did not happen,
    in the record whose whole job is to say what changed. The suite's own
    `test_refresh_moves_machine_inputs_and_logs_provenance` already asserts `e.old != e.new`."""
    import vinci.scenarios as sc

    rec = sc.read_record("SMPL", root=ROOT)
    old = rec.facts["net_debt"]
    src_only = sc.Fact(value=old.value, unit=old.unit, basis=old.basis,
                       source=old.source + " (re-cited)")
    out = sc.refresh_record(rec, facts={"net_debt": src_only}, source="s",
                            on_date="2026-07-31")
    added = out.refresh_log[len(rec.refresh_log):]
    assert [e.field for e in added] == ["facts.net_debt.source"], [e.field for e in added]
    assert all(e.old != e.new for e in added)


def test_a_basis_restatement_alone_is_recorded_even_when_the_value_holds() -> None:
    """A number that keeps its value while changing MEANING is the move a reader most needs to see
    — and the one a value-diff cannot show. It must still write, and still log."""
    import vinci.scenarios as sc

    rec = sc.read_record("SMPL", root=ROOT)
    old = rec.facts["net_debt"]
    same_value = sc.Fact(value=old.value, unit=old.unit, basis="restated meaning, same amount",
                         source=old.source)
    out = sc.refresh_record(rec, facts={"net_debt": same_value}, source="s",
                            on_date="2026-07-31")
    assert out is not rec, "a basis-only restatement was dropped as a no-op"
    assert out.facts["net_debt"].value == old.value
    assert [e.field for e in out.refresh_log[len(rec.refresh_log):]] == \
        ["facts.net_debt.basis"]


def test_a_unit_change_is_refused_because_it_rescales_the_denominator() -> None:
    """Basis is prose about the same quantity; UNIT is its scale. Letting a refresh move the unit is
    how a per-share value goes wrong by a factor of a million — the same class as the
    thousands-blind re-parse, arriving through the writer instead of a parser."""
    import vinci.scenarios as sc

    rec = sc.read_record("SMPL", root=ROOT)
    old = rec.facts["diluted_shares"]
    rescaled = sc.Fact(value=old.value * 1e6, unit="shares" if old.unit != "shares" else "M shares",
                       basis=old.basis, source=old.source)
    with pytest.raises(sc.RefreshRefusedError, match="never the UNIT"):
        sc.refresh_record(rec, facts={"diluted_shares": rescaled}, source="s", on_date="2026-07-31")


def test_a_bare_float_still_refreshes_the_same_quantity_without_touching_the_basis() -> None:
    """The ordinary case must not regress: re-reading the SAME line to a new value keeps its basis,
    and logs one entry, exactly as before."""
    import vinci.scenarios as sc

    rec = sc.read_record("SMPL", root=ROOT)
    old = rec.facts["net_debt"]
    out = sc.refresh_record(rec, facts={"net_debt": old.value - 1.0}, source="s",
                            on_date="2026-07-31")
    assert out.facts["net_debt"].basis == old.basis
    assert [e.field for e in out.refresh_log[len(rec.refresh_log):]] == ["facts.net_debt"]


def test_every_committed_record_states_the_denominator_it_actually_uses() -> None:
    """THE ARTIFACT PIN. After the swap, no record may still describe its denominator as a weighted
    average — that phrase over a point-in-time count is the mislabel this work exists to remove.
    Phrasing-independent on the LLM axis (nothing here is LLM-composed) but deliberately anchored on
    the two deterministic tokens the note is built from."""
    import json as _json

    recs = ROOT / "scenarios"
    if not recs.is_dir():
        pytest.skip("no scenario records in this worktree")
    checked = 0
    for f_ in sorted(recs.glob("*.json")):
        if f_.stem.startswith("_"):
            continue
        fact = (_json.loads(f_.read_text()).get("facts") or {}).get("diluted_shares")
        if not fact:
            continue
        basis = fact["basis"]
        checked += 1
        assert "weighted-average (latest 10-Q)" not in basis, (
            f"{f_.stem}: the denominator is described as a weighted average but the value is a "
            "point-in-time outstanding count")
        low = basis.lower()
        assert ("diluted shares outstanding" in low
                or "no dilutive difference" in low), f_.stem
        assert "Excluded from the filer's diluted average" in basis, (
            f"{f_.stem}: the exclusions are not stated beside the denominator")
    assert checked >= 5, f"only {checked} records reached the assertion — near-vacuous"


def test_the_fleet_check_resolves_shares_through_the_concept_not_one_tag() -> None:
    """STRUCTURAL, because the defect was a CALL SITE and not the mapping.

    `concepts.py` has always mapped the "shares" concept to the dei cover-page tag WITH us-gaap
    fallbacks; the fleet check above read the single dei tag directly and so withheld every filer
    that does not tag the cover page. Alphabet is one: live EDGAR for CIK 0001652044 carries
    exactly one dei tag (EntityPublicFloat), while its count sits under
    us-gaap:CommonStockSharesOutstanding. There were TWO such call sites in one function and the
    first fix caught only one — pin the file, not the line.
    """
    import pathlib as _pl

    # SCAN THE WHOLE FILE, MINUS THIS GUARD (review of #512). The first cut split on this test's
    # own `def` and scanned only what came BEFORE it — which is where the guard was appended, so a
    # fleet lookup added later was invisible to the very check meant to catch it. The exact `== 2`
    # was brittle for the same reason: a third legitimate call site would red it while being right.
    src = _pl.Path(__file__).read_text()
    marker = "def test_the_fleet_check_resolves_shares"
    head, _, tail = src.partition(marker)
    body = head + "\n".join(tail.split("\n\n\n")[1:])      # every OTHER test, before and after
    assert 'points_for_tag(f, "EntityCommonStockSharesOutstanding")' not in body, (
        "a fleet lookup went back to the single dei cover-page tag — that withholds every filer "
        "which tags shares only under us-gaap, and the concept chain already handles them")
    assert body.count("_basic_out(f)") >= 2, (
        "both fleet lookups must resolve through the shared `_basic_out` — one fixed sibling and "
        "one left behind is the defect this pin exists to catch")
    resolver = src.split("def _basic_out", 1)[1].split("\ndef ", 1)[0]
    assert 'extract_points(f, "shares")' in resolver, (
        "the shared resolver must read the shares CONCEPT, not a hand-rolled tag list — the "
        "concept is what carries the us-gaap fallbacks a non-cover-page filer needs")
