"""Test support (W62, 2026-11-18): derive an anchor with the stale-close check HELD OPEN.

Since W62 `compute_anchor` withholds the screen value when its band's current is not today's by
the band's own cadence (`anchor.close_age`): CIQ's history past 30 days before the page's price
date, the ex-lease history once a newer quarter could exist. Two pages of the cut at 4889ddba are
stale (BRBR 32 days, GOOGL 42, both CIQ's history), and several pins use them for something else:
BRBR for W61's two flags and the dilution input watch, GOOGL for the CIQ bridge. Such a pin derives
inside :func:`stale_gate_held_open`, so it keeps guarding its own subject, exactly as W50's pins
hold the multiple at the committed one.

What it holds open is the ANCHOR's check only: a measured stale verdict reads as fresh. The split's
own notice (`anchor_split.STALE_CLOSE_DAYS`) is untouched, so a split derived inside still states
it: the shape a page written before W62 carries until it is re-derived. An age that cannot be
measured still refuses, since holding a check open does not measure anything. W62's own pins
(`tests/test_w62_anchor_stale_multiple.py`) never hold it open.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest import mock

from vinci.dossier import anchor as anc


@contextmanager
def stale_gate_held_open() -> Iterator[None]:
    """`compute_anchor` as the code before W62 ran it: a dated close of any age prices."""
    real = anc.close_age

    def fresh(*args: Any, **kw: Any) -> anc.CloseAge:
        got = real(*args, **kw)
        return got._replace(stale=False) if got.stale else got

    with mock.patch.object(anc, "close_age", fresh):
        yield
