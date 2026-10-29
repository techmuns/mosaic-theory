"""Dividend, split and session sources for SYNTHETIC tests. Since 2026-10-26 (operator ruling B)
every return in scoring and the monitor is a total return, and the dividend source is a required
argument — so a test over a synthetic store states, here, that its names pay nothing in any window.

Never production: production reads Tiingo (`vinci.eod.dividends`), and a window it cannot read
raises. This file exists so no production module has to offer a "no dividends" source a caller
could reach for to land back on price return.
"""
from __future__ import annotations

from datetime import date, timedelta

from vinci.eod.splits import Split


def no_dividends(symbol: str, start: date, end: date) -> list[tuple[date, float]]:
    """Every window read, with no ex-date inside it."""
    return []


def no_splits(symbol: str) -> list[Split]:
    """Every symbol read, with no split recorded (audit item F-D1: the split source, like the
    dividend source, is a required argument, so a synthetic test states it here)."""
    return []


def weekday_sessions(start: date, end: date) -> list[date]:
    """Every weekday in [start, end] — a synthetic name's sessions (audit item F-D3)."""
    return [start + timedelta(days=i) for i in range((end - start).days + 1)
            if (start + timedelta(days=i)).weekday() < 5]


def weekday_calendar(symbol: str, start: date, end: date) -> list[date]:
    """A `SessionCalendar` in which every synthetic symbol traded every weekday."""
    return weekday_sessions(start, end)
