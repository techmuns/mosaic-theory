"""THE TRIAGE PASS ATTACHES A DOCUMENT — AND CLAIMS NOTHING ELSE.

WHY IT EXISTS. Every queued name's `cause_class` reads UNCLASSIFIED for a DATA reason, not a budget
one: all 525 de-rating events come from the EOD gap-down detector carrying `accession: null,
detail: null`. `vinci/rank/cause.py` says in its own docstring that its LLM pass needs "the
de-rating text wired onto events" first. This is that wiring, done deterministically off 8-K/6-K
item codes.

WHAT THESE PINS PROTECT is the line the pass must not cross. An item code names the EVENT ("this
was an earnings release"), never its CHARACTER ("this is a mean-reversion candidate"). The first is
filed; the second is an inference, and it would reach the ranker's character axis — a decision-path
change made on a code that never claimed it. So: provenance out, nothing scored.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest

from vinci.edgar.client import Filing
from vinci.triage import (
    CAUSAL_WINDOW,
    CAUSE_ITEMS,
    FORMS,
    OPAQUE_ITEMS,
    classify_event,
    nearest_filing,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROV = ROOT / "data" / "snapshots" / "event_provenance.jsonl"


def _filing(day: str, acc: str, items: list[str], form: str = "8-K") -> Filing:
    return Filing(cik="0000000001", form=form, filing_date=dt.date.fromisoformat(day),
                  accession=acc, items=items, primary_doc="x.htm", report_date=None)


def _rows() -> list[dict]:
    if not PROV.is_file():
        pytest.skip("no provenance artifact committed yet")
    return [json.loads(x) for x in PROV.read_text().splitlines() if x.strip()]


def test_the_nearest_filing_wins_not_the_first_in_the_feed() -> None:
    """THE SUBMISSIONS FEED IS NEWEST-FIRST, so `[0]` is whichever filing the company most recently
    made inside the window — not the one at the gap. On a name with seven gap-downs that is a
    different filing for most of them, and every one of those rows would carry a real accession
    for the wrong event, which is worse than carrying none."""
    gap = dt.date(2026, 5, 10)
    feed = [_filing("2026-05-11", "newest", ["8.01"]),
            _filing("2026-05-10", "at-the-gap", ["2.02"])]
    got = nearest_filing(feed, gap)
    assert got is not None and got.accession == "at-the-gap"


def test_ties_break_deterministically() -> None:
    """A COMMITTED ARTIFACT CANNOT WOBBLE. Two filings equidistant from the gap (the day before and
    the day after) must resolve the same way on every re-run, or the snapshot's diff churns without
    anything having changed."""
    gap = dt.date(2026, 5, 10)
    feed = [_filing("2026-05-11", "bbb", ["8.01"]), _filing("2026-05-09", "aaa", ["8.01"])]
    assert [nearest_filing(feed, gap).accession for _ in range(5)] == ["aaa"] * 5
    assert nearest_filing(list(reversed(feed)), gap).accession == "aaa", "order-dependent tiebreak"


def test_a_filing_outside_the_window_is_dark_not_attached() -> None:
    """An 8-K filed a week after the gap did not cause it. Widening to ±7d lifts apparent coverage
    from 67% to 91% — a number that reads like progress and is mostly filings that merely happened
    nearby."""
    gap = dt.date(2026, 5, 10)
    late = [_filing("2026-05-20", "late", ["2.02"])]
    assert nearest_filing(late, gap) is None
    p = classify_event(late, gap)
    # THE TIER ALONE IS NOT ENOUGH. A row labelled dark that still carries the out-of-window
    # accession and its cause is worse than a bare one: it reads as a filed attribution for an
    # event that filing had nothing to do with. Pinned field by field, because a mutation that
    # leaked exactly that survived a tier-only assertion.
    assert p.tier == "dark"
    assert (p.form, p.accession, p.filing_date, p.cause, p.primary_doc) == (None,) * 5
    assert p.items == ()


def test_an_exhibit_marker_is_never_a_cause() -> None:
    """9.01 IS AN ATTACHMENT MARKER, and counting it as a cause INVERTS the result: the first cut
    of this measurement reported it as the strongest signal (17 of 22 events), which reads as
    excellent mechanical coverage and is an artefact of nearly every 8-K carrying an exhibit."""
    assert "9.01" not in CAUSE_ITEMS and "9.01" in OPAQUE_ITEMS
    p = classify_event([_filing("2026-05-10", "a", ["9.01"])], dt.date(2026, 5, 10))
    assert p.tier == "opaque" and p.cause is None
    assert p.accession == "a", "an opaque filing still supplies its document — that is the LLM tier"


def test_a_foreign_issuers_6k_is_recovered_but_never_promoted() -> None:
    """THE 8-K PATH IS BLIND TO FOREIGN ISSUERS — FVRR files zero 8-Ks and 57 6-Ks, as do QFIN, BAK
    and SLI: four of the first 25 queued names. Their gap-downs read as "no document exists" when
    the document was on the other form. But a 6-K carries no item codes, so it is RECOVERED into
    the read-required tier, never promoted to a named cause."""
    assert "6-K" in FORMS
    gap = dt.date(2026, 5, 10)
    p = classify_event([_filing("2026-05-10", "a", [], form="6-K")], gap)
    assert p.tier == "opaque" and p.cause is None and p.form == "6-K"
    assert p.accession == "a"
    # AND WITH CAUSE-LOOKING ITEMS ON IT. 6-K items are free-form today, so the empty-items case
    # above passes through the "no named codes" branch and never exercises the FORM check at all
    # — a mutation deleting that check survived this test until this line existed. If EDGAR ever
    # populates them, the form is what must still refuse to name a cause off a code 6-K does not
    # file under.
    q = classify_event([_filing("2026-05-10", "b", ["2.02"], form="6-K")], gap)
    assert q.tier == "opaque" and q.cause is None, (
        "a 6-K was promoted to a named cause off an 8-K item code")


def test_the_committed_artifact_never_names_a_cause_without_a_filing() -> None:
    """CORPUS. A named cause with no accession is a fabricated attribution — the failure mode that
    matters here, because the row still looks complete."""
    for r in _rows():
        if r["tier"] == "named":
            assert r["accession"] and r["form"] and r["cause"], f"{r['ticker']} names a cause bare"
            assert r["cause"] in CAUSE_ITEMS.values(), f"{r['cause']} is not a filed item meaning"
        if r["tier"] == "dark":
            assert not r["accession"] and not r["cause"], f"{r['ticker']} is dark yet carries a doc"


def test_every_attached_filing_sits_inside_the_declared_window() -> None:
    """CORPUS. The window is recorded per row, so a later widening cannot silently re-date the
    existing ones."""
    for r in _rows():
        if not r["filing_date"]:
            continue
        gap = dt.date.fromisoformat(r["event_date"])
        filed = dt.date.fromisoformat(r["filing_date"])
        assert abs((filed - gap).days) <= r["window_days"] == CAUSAL_WINDOW, (
            f"{r['ticker']} {r['event_date']}: filing {filed} is outside ±{r['window_days']}d")


def test_the_pass_does_not_reach_the_ranker() -> None:
    """THE LINE. An item code names the event, not its character; turning 2.02 into a CauseClass
    would be an inference dressed as an extraction, reaching the ranker's character axis. Pinned
    structurally: nothing in the ranker may import the triage module."""
    for mod in ("rank/ranker.py", "rank/cause.py", "orchestrator.py", "screens/run.py"):
        src = (ROOT / "vinci" / mod).read_text()
        assert "vinci.triage" not in src and "from vinci import triage" not in src, (
            f"{mod} imports the triage module — provenance has reached the decision path")
