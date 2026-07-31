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


def test_the_overlay_serves_every_committed_name_and_none_falls_back() -> None:
    """NON-VACUOUS: runs on the real fleet, so an extraction that stops resolving reds here rather
    than in a rendered page. Measured when written: 11 of 11 servable, uplift 0.00%–15.88%."""
    db = ROOT / "data" / "dossiers"
    if not db.is_dir():
        pytest.skip("no local dossiers in this worktree")
    from vinci.config import get_config
    from vinci.edgar.client import EdgarClient
    from vinci.edgar.concepts import points_for_tag
    from vinci.resolver import EntityResolver

    cfg = get_config()
    res, ed = EntityResolver.from_config(cfg), EdgarClient.from_config(cfg)
    names = sorted(p.name for p in db.iterdir() if p.is_dir())
    served, zero = [], []
    for t in names:
        try:
            f = ed.companyfacts(res.resolve_ticker(t).cik)
        except Exception:  # noqa: BLE001 — offline worktree, not a failure of the overlay
            pytest.skip("EDGAR facts unavailable offline")
        pts = points_for_tag(f, "EntityCommonStockSharesOutstanding")
        out = max(pts, key=lambda p: (p.period_end, p.filed)).value if pts else None
        d = diluted_outstanding(f, basic_out=out)
        assert d.shares is not None, f"{t}: {d.reason}"
        assert d.shares >= d.basic_out, f"{t}: diluted below basic"
        served.append(t)
        if d.is_zero_dilution:
            zero.append(t)
    assert len(served) == len(names)
    # The zero-dilution set is REPORTED, not pinned to a fixed list — a filer that starts tagging
    # dilution must not red this. What must hold is that the state stays DISTINGUISHABLE on the
    # surface, since the number itself is identical to the basic count.
    # (Review finding: the first cut asserted `set(zero) <= set(names)`, which is true by
    # construction — `zero` is built from `names`. A vacuous assertion dressed as a check.)
    assert zero, "no zero-dilution name found — measured at 3 of 11; the state may have gone silent"
    for t in zero:
        f = ed.companyfacts(res.resolve_ticker(t).cik)
        pts = points_for_tag(f, "EntityCommonStockSharesOutstanding")
        out = max(pts, key=lambda p: (p.period_end, p.filed)).value
        assert "reported zero, not an unchecked one" in denominator_note(
            diluted_outstanding(f, basic_out=out)), t


#: Committed anchors whose ``anchor_base_value_per_share`` still carries the cumulative-period
#: defect and therefore diverges from a fresh recompute. These are the names the anchor backfill
#: has not yet been run on — measured, not chosen: SMPL 41.60→43.33 (+4.16%), BRBR 55.41→55.97
#: (+1.02%), CNXC 62.33→62.55 (+0.35%). The list SHRINKS to empty once the operator runs the
#: backfill, and this pin reds until STATE is updated with it — which is the point.
ANCHORS_AWAITING_BACKFILL = {"BRBR", "CNXC", "SMPL"}


def test_the_period_fix_moves_the_committed_anchor_and_exactly_these_names() -> None:
    """REVIEW FINDING — the fix has TWO consumers and only one was measured.

    `anchor_base_value_per_share` is `equity ÷ dil.value` (anchor.py), and `tagger._leverage` and
    `audit_r1.check_leverage` read it — so correcting the period moves a value committed in
    `dossier.json`, not just the scenario engine's reward:risk. The PR measured the engine and said
    nothing about the anchor.

    This pin is the invariant: the divergence set must be EXACTLY the recorded backfill list. A new
    name drifting in reds it; the backfill landing reds it too, which forces STATE to track the
    artifacts rather than describe them."""
    import json
    from datetime import UTC, datetime

    from vinci.dossier.anchor import compute_anchor

    dd = ROOT / "data" / "dossiers"
    if not dd.is_dir():
        pytest.skip("no local dossiers in this worktree")
    from vinci.config import get_config
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver

    cfg = get_config()
    res, ed = EntityResolver.from_config(cfg), EdgarClient.from_config(cfg)
    diverged, compared = set(), 0
    for p in sorted(dd.iterdir()):
        doc = p / "dossier.json"
        if not doc.is_file():
            continue
        d = json.loads(doc.read_text())
        committed = (d.get("anchor") or {}).get("anchor_base_value_per_share")
        if committed is None:
            continue  # anchor inapplicable — no base value to compare
        try:
            f = ed.companyfacts(res.resolve_ticker(p.name).cik)
        except Exception:  # noqa: BLE001 — offline worktree
            pytest.skip("EDGAR facts unavailable offline")
        fresh = compute_anchor(d.get("mechanical") or {}, facts=f,
                                 computed_at=datetime(2026, 7, 31, tzinfo=UTC), ciq=None)
        compared += 1
        if fresh.anchor_base_value_per_share is None:
            continue
        if abs(fresh.anchor_base_value_per_share / committed - 1) > 0.001:
            diverged.add(p.name)
    assert compared >= 5, f"only {compared} anchors reached the comparison — near-vacuous"
    assert diverged == ANCHORS_AWAITING_BACKFILL, (
        f"committed anchors diverging from a fresh recompute: {sorted(diverged)}, recorded: "
        f"{sorted(ANCHORS_AWAITING_BACKFILL)}. If the backfill has run, shrink the list and update "
        "STATE; if a NEW name drifted, something moved the anchor inputs without a record.")


def test_the_committed_records_dilution_matches_the_quarter_not_a_cumulative() -> None:
    """THE FLEET INSTANCE OF THE MIS-DATING. `facts.diluted_shares` agrees with the extraction on
    7 of 7 records — so a mis-dated extraction is a mis-dated record. SMPL is the one name where
    the committed value is a nine-month average; this pins the SELECTOR, so once the record is
    refreshed through the fixed path the two agree on the quarter."""
    import json

    from vinci.dossier.anchor import _DILUTED_TAG, _latest_point

    recs = ROOT / "scenarios"
    if not recs.is_dir():
        pytest.skip("no scenario records in this worktree")
    from vinci.config import get_config
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver

    cfg = get_config()
    res, ed = EntityResolver.from_config(cfg), EdgarClient.from_config(cfg)
    checked = 0
    for f_ in sorted(recs.glob("*.json")):
        if f_.stem.startswith("_"):
            continue
        ds = (json.loads(f_.read_text()).get("facts") or {}).get("diluted_shares") or {}
        if ds.get("value") is None:
            continue
        try:
            cf = ed.companyfacts(res.resolve_ticker(f_.stem).cik)
        except Exception:  # noqa: BLE001
            pytest.skip("EDGAR facts unavailable offline")
        p = _latest_point(cf, _DILUTED_TAG)
        assert p is not None, f_.stem
        span = (p.period_end - p.period_start).days if p.period_start else 0
        assert span <= 100, (
            f"{f_.stem}: the selector returned a {span}-day span — a cumulative period is being "
            "read as 'the latest 10-Q's weighted average' again")
        checked += 1
    assert checked >= 5, f"only {checked} records reached the assertion — the pin is near-vacuous"
