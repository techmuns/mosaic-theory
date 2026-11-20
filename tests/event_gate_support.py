"""Test support (W82, 2026-11-20): the gate a committed page's OWN build ran, judged exactly.

Since W82 the event rule counts a filing ON an export panel's own day as after it
(`freshness.first_event_after`). A page built before that ran the STRICT gate (``day < filed``),
so a walk over the committed pages at their own build dates must hold each page to the gate that
built it. That gate is read from the page's stamp (`extraction_version.includes`), never from its
build date: a page built today on older code ran the old gate (review round 0 of #1146).

ONE helper for every roster walk (review round 1 of #1146): a walk that accepted a refusal
whenever each stale panel's FIRST filing fell on the panel's own day passed a page that a LATER
filing, behind that one, had refused at its build. Here the strict gate is applied whole.
"""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from vinci.dossier import freshness as fr
from vinci.dossier.extraction_version import includes

#: The vintage of the gate that counts a filing on a panel's own day.
W82_VINTAGE = "2026-11-20.a-report-on-a-dated-values-own-day-counts-as-after-it"


def own_gate_refusal(mechanical: object, filings: Sequence[fr.FilingEvent], *,
                     built_at: dt.date | str, stamp: str | None) -> str | None:
    """Why the event gate the page's own build ran would refuse it at ``built_at``, or None.

    A stamp including W82's vintage ran `freshness.event_verdict` as it is now. An older stamp ran
    the strict gate: every export panel against the first filing strictly after its day. A stamp
    this code does not declare is a refusal: which gate built the page is unknown, never "the
    old one"."""
    ran_w82 = includes(stamp, W82_VINTAGE)
    if ran_w82 is None:
        return f"stamp {stamp!r} is not one this code declares, so its gate is unknown"
    if ran_w82:
        v = fr.event_verdict(mechanical, filings, built_at=built_at)
        return v.note() if v.stale else None
    for key, day in fr.export_panels(mechanical):
        f = fr.first_event_after(day, filings, upto=built_at, same_day_counts=False)
        if f is not None:
            return f"the strict gate it ran: {key} dated {day} predates {f.label()}"
    return None
