"""Test support: derive an anchor with the close's two checks HELD OPEN (W62, 2026-11-18;
re-cut for W73, 2026-11-19).

Since W73 `compute_anchor` withholds the screen value when the event rule refuses the close R1
prices (`anchor.close_verdict`: a report filed after it by the page's price date, a filing list
that could not be read, or a date that cannot be measured), and it flags the stock's move since
that close (`anchor.close_drift`). Several pins use pages for something else: the CIQ bridge
(GOOGL, whose 2026-09-30 close predates Alphabet's 2026-10-28 results) and the backfill path,
whose stub EDGAR client and config read no filings and no store. Such a pin derives inside
:func:`stale_gate_held_open`, so it keeps guarding its own subject, exactly as W50's pins hold the
multiple at the committed one.

What it holds open: a refused close reads as passed, EXCEPT a close after the page's price date
(W68), which no holding-open makes knowable; and the price-drift flag states nothing. The event
rule's and the flag's own pins (`tests/test_w73_dated_multiple.py`) never hold either open.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest import mock

from vinci.dossier import anchor as anc


@contextmanager
def stale_gate_held_open() -> Iterator[None]:
    """`compute_anchor` with the event rule passing every dated close at or before the page's date,
    and no price-drift flag."""
    real = anc.close_verdict

    def passed(*args: Any, **kw: Any) -> anc.CloseVerdict:
        got = real(*args, **kw)
        if got.after_page or got.age is None:
            return got
        # ONE held-open verdict whatever was read, so two paths that read different filings (the
        # assembly's stated list, the backfill's unread stub) derive one block
        return got._replace(stale=False, clears=None, filing=None,
                            rule="held open: the event rule is not this pin's subject",
                            cause="held open: the event rule is not this pin's subject")

    with (mock.patch.object(anc, "close_verdict", passed),
          mock.patch.object(anc, "close_drift", lambda *_a, **_k: (None, None))):
        yield
