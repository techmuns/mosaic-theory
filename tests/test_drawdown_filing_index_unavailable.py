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
    cause, _flags = _drawdown_cause(_Record(gaps, cik), edgar, _NoHttp())  # type: ignore[arg-type]
    return cause


def _cause_and_flags(edgar: object, gaps: list[date], cik: str = _CIK) -> Any:
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


# --- the degraded-feed flag, and WHICH AUDIENCE it reaches ---------------------------------------


def test_a_degraded_feed_raises_a_flag_naming_how_many_dates_lost_their_cause() -> None:
    """The UNKNOWN note renders at the point of use, but a blank cause under a real price gap is a
    decision fact, so it also gets a top-level flag — the `stock-info:` twin pattern."""
    _cause, flags = _cause_and_flags(_FailingEdgar(), [_GAP, _GAP + timedelta(days=30)])

    assert len(flags) == 1
    assert flags[0].startswith("drawdown-cause: EDGAR filing index unavailable")
    assert "2 gap-down date(s)" in flags[0]
    assert "re-assemble" in flags[0]


def test_the_outage_flag_is_hidden_because_the_block_itself_already_says_so() -> None:
    """THE AUDIENCE PIN — operator ruling 2026-09-02, and it asserts BOTH halves on purpose.

    `flags.partition` routes by PREFIX: anything matching `flags._QA_MARKERS` is hidden (dev/JSON
    only), everything else is re-voiced to the human caveat channel. That module's default is to
    show a new flag ("fail toward transparency"), and by that default this one would be a caveat —
    it is data completeness, not machine discipline. It is hidden by explicit ruling instead.

    The ruling is only safe while the human is told AT THE POINT OF USE, so this pins the hiding and
    the rendered UNKNOWN line TOGETHER. If the drawdown block ever stops saying "EDGAR filing index
    unavailable" on the human surface, this test fails even though the routing is untouched — which
    is the whole point: hiding the flag must never be what makes an outage silent.
    """
    from vinci.dossier.flags import partition
    from vinci.dossier.render import _fact, _fmt_shape

    cause, flags = _cause_and_flags(_FailingEdgar(), [_GAP])
    caveats, qa_flags = partition(flags)

    # (a) the flag is machine-tier — dev/JSON only, off the analyst's surface
    assert qa_flags and qa_flags[0].startswith("drawdown-cause: EDGAR filing index unavailable")
    assert caveats == []

    # (b) ...which is ONLY acceptable because the rendered block itself carries the message
    rendered = _fact("Shape", cause.shape, _fmt_shape)
    assert "_UNKNOWN_" in rendered
    assert "EDGAR filing index unavailable" in rendered


def test_a_healthy_feed_raises_no_flag() -> None:
    """The negative pin. A flag that fired on a working feed would appear on every dossier and
    train the reader to ignore the channel."""
    assert _cause_and_flags(_WorkingEdgar(), [_GAP])[1] == []
    assert _cause_and_flags(_WorkingEdgar(), [])[1] == []


def test_a_healthy_feed_that_genuinely_finds_nothing_raises_no_flag() -> None:
    """"The company filed nothing" is a FINDING, established from a readable feed. It is not a
    degradation and must not be flagged as one."""

    class _EmptyEdgar:
        def recent_filings(self, cik: str | int, **kw: Any) -> list[Filing]:
            return []

    assert _cause_and_flags(_EmptyEdgar(), [_GAP])[1] == []


# --- the review fixes: no-CIK, and the flag's date count ----------------------------------------


def test_a_record_with_no_cik_does_not_manufacture_no_company_filing() -> None:
    """A missing CIK means the index was never READ, so "no company filing" — a finding about the
    issuer — was never established. Before this fix `lookup_failed` was set only on the HttpError
    path, so the `if cik else []` arm fell straight through to the healthy branch and stated it.
    Five siblings guard the same way (mechanical.py:1938, 2083, 2384, 2592, 2933)."""
    cause, flags = _cause_and_flags(_WorkingEdgar(), [_GAP], cik="")

    assert cause.shape.value is None
    assert "no company filing" not in str(cause.shape.note)
    assert "no CIK" in (cause.shape.note or "")
    assert flags and "no CIK" in flags[0]
    # the advice must match the cause — "re-assemble when the feed recovers" is wrong here
    assert "resolve the CIK" in flags[0]


def test_the_flag_counts_distinct_dates_not_events() -> None:
    """`gaps` is not de-duplicated upstream, and this count is the only number the machine tier
    reports about the outage — so two events on one date must not read as two dates."""
    _c, flags = _cause_and_flags(_FailingEdgar(), [_GAP, _GAP, _GAP])

    assert "1 gap-down date(s)" in flags[0]


def test_no_edgar_failure_escapes_the_drawdown_path() -> None:
    """THE PROPERTY PIN (carried from #570, in the tuple-returning form). Two earlier versions
    asserted the SHAPE of the source while claiming to assert the property."""
    import json as _json

    class _Raises:
        def __init__(self, exc: BaseException) -> None:
            self.exc = exc

        def recent_filings(self, cik: str | int, **kw: Any) -> Any:
            raise self.exc

    failures: list[BaseException] = [
        HttpError("Exhausted retries for https://data.sec.gov/submissions/CIK1.json"),
        HttpError("Non-retryable 403 from data.sec.gov: rate limited"),
        KeyError("form"),
        ValueError("Invalid isoformat string"),
        _json.JSONDecodeError("Expecting value", "<html>", 0),
        IndexError("list index out of range"),
    ]
    for exc in failures:
        cause, flags = _cause_and_flags(_Raises(exc), [_GAP])  # must not raise
        assert cause.shape.value is None, f"{type(exc).__name__} was not degraded"
        assert flags, f"{type(exc).__name__} degraded silently — no flag"


def test_the_drawdown_path_reads_submissions_exactly_once() -> None:
    """An N+1 guard on `_drawdown_filings` (carried from #570)."""
    import ast
    import pathlib as _pathlib

    root = _pathlib.Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "vinci" / "dossier" / "mechanical.py").read_text())
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_drawdown_filings"
    )
    calls = [
        n for n in ast.walk(fn)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "recent_filings"
    ]
    assert len(calls) == 1, "the drawdown path should read the submissions index exactly once"
