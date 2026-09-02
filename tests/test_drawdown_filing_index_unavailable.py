"""A degraded EDGAR feed must not drop the name, and must not invent "no company filing".

`_drawdown_filings` held the ONE submissions call site of 13 with no handler, and `_drawdown_cause`
runs it FIRST in `assemble_mechanical`. So on a degraded feed a name carrying `earnings_gap_down`
events raised out of the whole assembly; `assemble_cohort`'s per-name `task` caught it and dropped
the name into its `errors` list. The run survived and the name silently did not appear — 9 of 17
committed dossiers are in that class (AORT, BRBR, CNXC, EPAM, FUBO, MVST, SMPL, VITL, VRRM).

THE OBVIOUS FIX IS THE DANGEROUS ONE. Wrapping the call and returning `[]` makes every gap date
render "no company filing" — the string this module reaches for when the company genuinely filed
nothing, chosen deliberately to "state the WORLD, not our process". A tooling outage would then be
published as a finding about the issuer, on a rendered decision surface, with the suite green.
`test_a_degraded_feed_never_renders_no_company_filing` is the pin that refuses that, and it is the
one to keep if the others are ever pruned.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from vinci.dossier.mechanical import _drawdown_cause
from vinci.edgar.client import Filing
from vinci.netcache import HttpError

_CIK = "0001739104"
_GAP = date(2026, 5, 8)


class _Event:
    """Duck-typed `record.events` row — `_drawdown_cause` reads only `.event_type.value` and
    `.event_date`."""

    def __init__(self, day: date) -> None:
        self.event_date = day
        self.event_type = type("_T", (), {"value": "earnings_gap_down"})()


class _Identity:
    def __init__(self, cik: str) -> None:
        self.cik = cik


class _Record:
    def __init__(self, gaps: list[date], cik: str = _CIK) -> None:
        self.events = [_Event(g) for g in gaps]
        self.identity = _Identity(cik)


class _FailingEdgar:
    """An `EdgarClient` stand-in whose submissions read is down — the real degraded-feed shape,
    where `_fetch_with_retries` has exhausted its 5 attempts and raises."""

    def __init__(self) -> None:
        self.calls = 0

    def recent_filings(self, cik: str | int, **kw: Any) -> list[Filing]:
        self.calls += 1
        raise HttpError(f"Exhausted retries for https://data.sec.gov/submissions/CIK{cik}.json")


class _WorkingEdgar:
    """Serves one real-shaped 8-K at the gap date, so the healthy path stays pinned beside the
    degraded one — a fix that quietly broke the working case would otherwise pass."""

    def recent_filings(self, cik: str | int, **kw: Any) -> list[Filing]:
        return [
            Filing(
                cik=_CIK,
                form="8-K",
                filing_date=_GAP,
                accession="0001739104-26-000017",
                items=["2.02", "9.01"],
                primary_doc=None,
                report_date=_GAP,
            )
        ]


class _NoHttp:
    """Archive double serving an EMPTY filing index.

    `_drawdown_cause` reaches `http` through `_revised_guidance`, which looks up the exhibit-99.1
    URL by ACCESSION (not, as first assumed here, only when a filing carries a `primary_doc`). An
    empty index is a legitimate answer that resolves to "no exhibit", which keeps these cases on the
    drawdown-cause behaviour under test rather than on release-parsing."""

    def __init__(self) -> None:
        self.calls = 0

    def get_text(self, *a: Any, **k: Any) -> str:
        self.calls += 1
        return ""  # unreadable SGML header -> release_parse falls back to the index below

    def get_json(self, *a: Any, **k: Any) -> dict[str, Any]:
        self.calls += 1
        return {"directory": {"item": []}}  # a filing furnishing no Ex-99.1


def _cause(edgar: object, gaps: list[date], cik: str = _CIK) -> Any:
    return _drawdown_cause(_Record(gaps, cik), edgar, _NoHttp())  # type: ignore[arg-type]


# --- the regression this PR fixes ---------------------------------------------------------------


def test_a_degraded_feed_no_longer_drops_the_name() -> None:
    """THE FIX. Before: `HttpError` propagated out of `assemble_mechanical` and the name produced
    no dossier at all. Now the block degrades and the assembly continues."""
    edgar = _FailingEdgar()

    cause = _cause(edgar, [_GAP])

    assert edgar.calls == 1
    assert cause is not None


def test_a_degraded_feed_never_renders_no_company_filing() -> None:
    """THE PIN THAT MATTERS. "no company filing" is a claim about the issuer — this module picks it
    deliberately to state the world rather than the tooling. A failed lookup must never reach it,
    or an EDGAR outage is published as a finding on the decision surface."""
    cause = _cause(_FailingEdgar(), [_GAP])

    assert "no company filing" not in str(cause.shape.value or "")
    assert cause.shape.value is None, "an unreadable index must be UNKNOWN, not a rendered claim"
    assert "unavailable" in (cause.shape.note or "").lower()


def test_the_gap_dates_survive_the_outage_because_they_are_known_independently() -> None:
    """The dates come from the data-record's own events, not from EDGAR. Blanking them too would
    discard something the outage never put in doubt."""
    cause = _cause(_FailingEdgar(), [_GAP, _GAP + timedelta(days=30)])

    assert cause.gap_down_dates.value == ["2026-05-08", "2026-06-07"]


def test_the_revised_guidance_note_says_outage_not_absence() -> None:
    """The same distinction one field over: `revised_guidance` degrades to UNKNOWN either way, so
    only its NOTE can tell "we could not look" from "there was nothing to find"."""
    failed = _cause(_FailingEdgar(), [_GAP])
    healthy_but_empty = _cause(_WorkingEdgar(), [])

    assert "unavailable" in (failed.revised_guidance.note or "").lower()
    assert "no catalyst 8-K to follow" in (healthy_but_empty.revised_guidance.note or "")


# --- the healthy paths, pinned so the fix cannot silently degrade them ---------------------------


def test_a_healthy_feed_still_attributes_the_gap_to_its_filing() -> None:
    cause = _cause(_WorkingEdgar(), [_GAP])

    assert cause.shape.value is not None
    assert "2026-05-08" in cause.shape.value
    assert "no company filing" not in cause.shape.value
    assert cause.gap_down_dates.value == ["2026-05-08"]


def test_a_healthy_feed_that_finds_nothing_still_says_no_company_filing() -> None:
    """The negative half of the outage pin: when the feed IS readable and the company genuinely
    filed nothing near the gap, that finding must still be stated. A fix that suppressed it
    everywhere would pass the outage pins and destroy a real signal."""

    class _EmptyEdgar:
        def recent_filings(self, cik: str | int, **kw: Any) -> list[Filing]:
            return []

    cause = _cause(_EmptyEdgar(), [_GAP])

    assert cause.shape.value is not None
    assert "no company filing" in cause.shape.value


def test_a_name_with_no_gap_downs_is_unaffected() -> None:
    cause = _cause(_WorkingEdgar(), [])

    assert cause.shape.value == "gradual bleed — no discrete gap-down detected"
    assert cause.gap_down_dates.value is None
