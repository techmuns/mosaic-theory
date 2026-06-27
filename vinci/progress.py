"""Progress reporting for the long, network-bound batch loops (EOD ingest, the universe screen).

Why this exists: those loops run silent today, so a *slow* run is indistinguishable from a *hung*
one without forensics (``lsof``/``sample``/cache-file watching). A :class:`ProgressReporter` emits
``<label> <done>/<total> · <rate>/min · ETA <eta>`` to an injected sink. The library default
is ``None`` (silent) so importing the package or running tests stays quiet — callers opt in. The CLI
wires :func:`stderr_reporter`, which writes to **stderr** so progress never pollutes stdout (which
carries the parsable run summary). ``now`` is injectable so the rate/ETA arithmetic is unit-testable
without real time.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable

ProgressFn = Callable[[str], None]

# Below this elapsed, a rate is meaningless (one sub-millisecond sample → millions/min). The first
# line then reads "0/min · ETA 0s" — an honest "just started" rather than an absurd rate.
_MIN_ELAPSED_SEC = 0.5


def stderr_reporter(message: str) -> None:
    """Default CLI sink: one progress line to STDERR (stdout carries the parsable run summary)."""
    print(message, file=sys.stderr, flush=True)


def _format_eta(seconds: float) -> str:
    if seconds <= 0:
        return "0s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m{secs:02d}s" if minutes else f"{secs}s"


class ProgressReporter:
    """Emit progress to ``emit`` at a fixed step (and on the first and final item).

    Silent when ``emit`` is ``None`` — the library default, so nothing is forced on importers/tests.
    One instance per loop; call :meth:`tick` once per item with the running count.
    """

    def __init__(
        self,
        label: str,
        total: int,
        *,
        emit: ProgressFn | None,
        step: int = 25,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._label = label
        self._total = total
        self._emit = emit
        self._step = max(1, step)
        self._now = now
        self._start = now()

    def tick(self, done: int, *, suffix: str = "") -> None:
        """Call once per item. Emits on the first item, every ``step``-th item, and the last."""
        if self._emit is None:
            return
        if done == 1 or done % self._step == 0 or done >= self._total:
            self._emit(self._line(done, suffix))

    def _line(self, done: int, suffix: str) -> str:
        elapsed = self._now() - self._start
        # No rate until elapsed is meaningful (else the first line shows millions/min).
        rate = (done / elapsed * 60.0) if elapsed >= _MIN_ELAPSED_SEC else 0.0
        eta = (max(0, self._total - done) / rate * 60.0) if rate > 0 else 0.0
        line = f"{self._label} {done}/{self._total} · {rate:.0f}/min · ETA {_format_eta(eta)}"
        return f"{line} · {suffix}" if suffix else line
