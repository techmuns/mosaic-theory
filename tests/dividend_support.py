"""Dividend sources for SYNTHETIC tests. Since 2026-10-26 (operator ruling B) every return in
scoring and the monitor is a total return, and the dividend source is a required argument — so a
test over a synthetic store states, here, that its names pay nothing in any window.

Never production: production reads Tiingo (`vinci.eod.dividends`), and a window it cannot read
raises. This file exists so no production module has to offer a "no dividends" source a caller
could reach for to land back on price return.
"""
from __future__ import annotations

from datetime import date


def no_dividends(symbol: str, start: date, end: date) -> list[tuple[date, float]]:
    """Every window read, with no ex-date inside it."""
    return []
