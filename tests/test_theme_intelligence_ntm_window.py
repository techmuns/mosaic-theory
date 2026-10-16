"""A next-twelve-months forecast covers the twelve months after it was READ (2026-10-16).

J.P. Morgan's "Software Shock" states NTM net margins "At Feb '26". The extraction wrote the period
three ways across registries — "Feb 2026", "NTM" and "NTM at Feb 2026" (the committed fixture) —
and the timing test dated them three ways:
- a one-month forecast window, February 2026 (the reading date read as the period);
- the twelve months after the RUN's as-of — so the same stored figure moved forward on every later
  reassessment and stayed "near-term" for ever;
- the union of both.
All three now read 2026-02-02 → 2027-02-02: the twelve months after the figure was read.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from tests.theme_intelligence_support import JPM_AS_OF, ingest_jpm, make_pipeline
from vinci.theme_intelligence.schemas import Claim, ClaimKind, Confidence, Epistemic
from vinci.theme_intelligence.timewindow import timing_of

READ = date(2026, 2, 2)
QUOTE = "At Feb ’26 (S&P 500 14.5%, AI Usage 16.4%, and Ex AI Usage 13.0%"
WANT = "2026-02-02..2027-02-02"


def _claim(period: str | None, *, metric: str = "NTM net margin",
           measured: date | None = READ, quote: str = QUOTE) -> Claim:
    """The shape the extraction gave this figure (the real fields of the acceptance registry's
    claims C-243c202ac46ff1 and C-0fcf9590c230d2), with the period varied."""
    return Claim(claim_id="C-x", article_id="A-x", article_version_id="AV-x", block_id="b022",
                 char_start=0, char_end=len(quote), quote=quote, statement=quote,
                 kind=ClaimKind.METRIC, epistemic=Epistemic.FORECAST, metric=metric,
                 period=period, value=16.4, value_text="16.4%", unit="%", measured_as_of=measured,
                 confidence=Confidence.HIGH, span_verified=True, number_verified=True,
                 measure_key="k", fingerprint="f", extraction_id="X-1")


def test_the_committed_fixtures_ntm_margins_cover_the_twelve_months_after_they_were_read(
        tmp_path: Path) -> None:
    """The real claims ("NTM at Feb 2026", read 2026-02-02): one window, from the reading."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    ntm = [c for t in pipe.store.theses() for lk in pipe.store.links(t.thesis_id)
           if (c := pipe.store.claim(lk.claim_id)) is not None and c.metric == "NTM net margin"]
    assert ntm and {c.period for c in ntm} == {"NTM at Feb 2026"}
    for c in ntm:
        cls, note = timing_of(c, JPM_AS_OF, JPM_AS_OF)
        assert cls == "near_term" and WANT in note, note


@pytest.mark.parametrize("period", ["Feb 2026", "NTM", "NTM at Feb 2026", None])
def test_every_way_the_period_was_written_reads_one_window(period: str | None) -> None:
    cls, note = timing_of(_claim(period), JPM_AS_OF, JPM_AS_OF)
    assert cls == "near_term" and WANT in note, note


def test_a_stored_ntm_figure_does_not_stay_near_term_for_ever() -> None:
    """THE DRIFT: reassessed in March 2027, the February 2026 figure's twelve months have ended —
    it is history, not a near-term window. (Before: "NTM" was read from the run's date, so it was
    near-term on every reassessment.) Still near-term in October 2026, inside its window."""
    assert timing_of(_claim("NTM"), date(2026, 10, 14), JPM_AS_OF)[0] == "near_term"
    cls, note = timing_of(_claim("NTM"), date(2027, 3, 1), JPM_AS_OF)
    assert cls == "historical" and WANT in note


def test_the_reading_date_is_the_measurement_else_a_one_month_period_else_the_source_date() -> None:
    assert "2026-02-01..2027-02-01" in timing_of(_claim("Feb 2026", measured=None),
                                                 JPM_AS_OF, JPM_AS_OF)[1]
    assert "2026-02-09..2027-02-09" in timing_of(_claim("NTM", measured=None),
                                                 JPM_AS_OF, JPM_AS_OF)[1]


def test_what_is_not_an_ntm_reading_keeps_its_window() -> None:
    """NEGATIVE: an NTM measure whose period names its OWN window ("2027") keeps it; a forecast
    that is not NTM, written "Feb 2026", is a February 2026 window; an NTM period with no reading
    date anywhere keeps the run's twelve months (nothing to anchor it to)."""
    assert "2027-01-01..2027-12-31" in timing_of(_claim("2027"), JPM_AS_OF, JPM_AS_OF)[1]
    plain = _claim("Feb 2026", metric="contract price change", quote="Prices rise in Feb 2026")
    assert "2026-02-01..2026-02-28" in timing_of(plain, JPM_AS_OF, JPM_AS_OF)[1]
    assert "2026-02-09..2027-02-09" in timing_of(_claim("NTM", measured=None), JPM_AS_OF,
                                                 None)[1]
