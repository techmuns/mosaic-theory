"""A truncated view must state its own truncation.

THE INCIDENT (2026-09-10, `docs/records/2026-09-10-cah-cor-verified-not-assumed.md` amendment 3):
a scan printed the first 3 of 5 GLP-1 mentions per filing and a conclusion was drawn from that
sample — *"no profit statement"* — when the disclosure sat in the 4th and 5th. **The count was
right and the population was read partially, and the output did not say which.** A sample knows it
is a sample; a truncated print does not, and the correct count beside it is what makes it
convincing.

Two live instances of the same shape sit in this renderer. The form-mix one is REAL on the
committed corpus: TECX carries 8 form types over 26 filings against 5 bars.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from vinci.panels_render import _FORM_BARS, _TIMELINE_DOTS, _timeline, payloads_for

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _dossiers() -> list[tuple[str, dict]]:
    return [(p.parent.name, json.loads(p.read_text()))
            for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))]


# --------------------------------------------------------------------------- timeline
def test_the_timeline_says_how_many_filings_it_did_not_draw() -> None:
    """THE REGRESSION. This panel's whole job is how far behind the evidence is; drawing the first
    four and stopping rendered a nine-filing gap identically to a four-filing one."""
    newer = [f"10-Q 2026-0{i}-01 acc x" for i in range(1, 10)]  # 9 filings
    html = _timeline(last="2025-12-31", newer=newer, nxt="2026-11-01")
    assert "+5 more" in html                      # 9 − 4 drawn
    assert "of 9 filed since" in html             # …and the population, not just the remainder


def test_the_timeline_stays_silent_when_nothing_was_dropped() -> None:
    """NEGATIVE PIN. An overflow note on a complete view is noise, and worse, it teaches the reader
    to ignore the note that matters."""
    html = _timeline(last="2025-12-31", newer=["10-Q 2026-01-01 acc x"] * _TIMELINE_DOTS, nxt=None)
    assert "more" not in html
    assert html.count('class="unread"') == _TIMELINE_DOTS


# --------------------------------------------------------------------------- form mix
def _form_counts(dossier: dict) -> dict[str, int]:
    m = dossier.get("mechanical") or {}
    forms: dict[str, int] = {}
    for f in ((m.get("dilution_pipeline") or {}).get("filings")) or []:
        forms[str(f.get("form"))] = forms.get(str(f.get("form")), 0) + 1
    return forms


def test_every_committed_dossier_that_overflows_the_bars_says_so() -> None:
    """CORPUS PIN, and PHRASING-INDEPENDENT so it survives re-assembly: the numbers are computed
    from the artifact, never hardcoded. TECX is the live case — 8 form types, 5 bars."""
    checked = overflowing = 0
    for ticker, d in _dossiers():
        body = (payloads_for(dossier=d, row=None, freshness=None).get("dilution") or {}).get("body")
        if not body:
            continue
        checked += 1
        forms = _form_counts(d)
        if len(forms) <= _FORM_BARS:
            assert "form types" not in body, f"{ticker}: nothing dropped, yet it claims a subset"
            continue
        overflowing += 1
        drawn = sum(sorted(forms.values(), reverse=True)[:_FORM_BARS])
        assert f"showing {_FORM_BARS} of {len(forms)} form types" in body, ticker
        assert f"({drawn} of {sum(forms.values())} filings)" in body, ticker
    assert checked, "no committed dossier rendered a dilution panel — this pin proves nothing"
    assert overflowing, (
        "no committed dossier overflows the bars — the pin cannot fail and must be re-anchored "
        "(TECX carried 8 form types over 26 filings at 2026-09-10)")


def test_the_bar_count_and_the_stated_total_cannot_drift_apart() -> None:
    """The failure this guards is a SILENT one: change `_FORM_BARS` and a hardcoded 'showing 5 of'
    would lie rather than break. Both numbers are read back out of the rendered body."""
    for ticker, d in _dossiers():
        body = (payloads_for(dossier=d, row=None, freshness=None).get("dilution") or {}).get("body")
        if not body or "form types" not in body:
            continue
        shown, total = map(int, re.search(r"showing (\d+) of (\d+) form types", body).groups())
        assert shown == body.count('class="barrow"') == _FORM_BARS, ticker
        assert total == len(_form_counts(d)) > shown, ticker


@pytest.mark.parametrize("n_types", [_FORM_BARS, _FORM_BARS + 1])
def test_the_boundary_is_at_more_than_the_bar_count_not_at_or_equal(n_types: int) -> None:
    """OFF-BY-ONE PIN on a frozen input: exactly `_FORM_BARS` types is COMPLETE and must stay
    silent; one more must speak."""
    d = {"mechanical": {"dilution_pipeline": {
        "line": {"value": "x", "source_ref": "r"},
        "filings": [{"form": f"F{i}"} for i in range(n_types)]}}}
    body = payloads_for(dossier=d, row=None, freshness=None)["dilution"]["body"]
    assert ("form types" in body) is (n_types > _FORM_BARS)
