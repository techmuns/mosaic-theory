"""Scoring a labelled call against realised prices — ``tracker.py``'s conventions, preserved.

THESE CONVENTIONS ARE PRE-REGISTERED. They were chosen before any result was seen, and changing one
changes every number downstream, so each is copied deliberately rather than re-derived:

  entry      OPEN of the next trading day after the post. Never the post-day close — that is
             look-ahead, and it manufactures alpha out of the author's own timing.
  exit       CLOSE ``horizon`` trading days after the entry bar.
  horizon    the stated high end, else the stated low end, else 63 days — and when the default is
             applied it is FLAGGED, never silently folded in.
  sign       returns are signed by the stated bias, so a bearish call that falls is a win.
  benchmark  SPY over the identical window; a raw return in a rising tape says almost nothing.
  path       MFE / MAE from the window's highs and lows, and whether the target was touched at all
             before the horizon expired.
  OPEN       a call whose horizon has not yet elapsed is scored OPEN and excluded from aggregates.

ONE DEPARTURE, and it is a bug fix rather than a convention change: the target parser. See
``vinci.calls.targets`` — a negative percentage used to crash internally and return a silent None,
so 40 calls in this corpus were scored as though no target had been named.

BOTH LEGS END ON THE COMMON LAST BAR. ``vinci/eod/features.py`` learned this the expensive way: a
benchmark that stops early while the name runs on is not merely stale, it is ASYMMETRIC, and the
sign of the error is set by whichever way the market moved in the gap. Four candidates once passed
a gate on that alone. Here the window is trimmed to the last bar BOTH series carry.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from vinci.calls.targets import TargetStatus, parse_target

#: Applied only where the author stated no horizon, and always surfaced as ``horizon_assumed``.
DEFAULT_HORIZON_DAYS = 63

Bar = tuple[date, float, float, float, float, float]   # (date, open, high, low, close, volume)


class CallStatus(BaseModel, frozen=True):
    """Not an enum: the reason a call is unscored is data, and it is rendered to a human."""

    code: str
    detail: str


class CallResult(BaseModel, frozen=True):
    """One scored call. Every ``None`` here has a stated reason beside it."""

    tweet_id: str
    ticker: str
    posted: date
    bias: str
    status: str                      # CLOSED | OPEN | NO_PRICE_DATA | NO_ENTRY_BAR
    detail: str = ""

    entry: float | None = None
    entry_date: date | None = None
    exit: float | None = None
    exit_date: date | None = None
    horizon_days: int | None = None
    horizon_assumed: bool = False

    ret: float | None = None
    bench_ret: float | None = None
    excess: float | None = None
    mfe: float | None = None
    mae: float | None = None

    target_px: float | None = None
    target_status: str | None = None
    target_hit: bool | None = None
    direction_correct: bool | None = None


def _after(bars: list[Bar], d: date) -> list[Bar]:
    return [b for b in bars if b[0] > d]


def _from(bars: list[Bar], d: date) -> list[Bar]:
    return [b for b in bars if b[0] >= d]


def score_call(
    *, tweet_id: str, ticker: str, posted: date, bias: str,
    target: object, target_type: str | None,
    horizon_lo: int | None, horizon_hi: int | None,
    bars: list[Bar], bench: list[Bar],
) -> CallResult:
    """Score one labelled call. Pure: every input is passed in, nothing is fetched or read here."""
    base = {"tweet_id": tweet_id, "ticker": ticker, "posted": posted, "bias": bias}
    if not bars:
        return CallResult(**base, status="NO_PRICE_DATA",
                          detail=f"no committed bars for {ticker} (delisted, renamed, or an index)")

    fwd = _after(bars, posted)
    if not fwd:
        return CallResult(**base, status="NO_ENTRY_BAR",
                          detail="no trading day after the post inside the fetched window")

    entry_bar = fwd[0]
    entry, entry_date = entry_bar[1], entry_bar[0]          # OPEN of the next trading day

    hz = horizon_hi or horizon_lo or DEFAULT_HORIZON_DAYS
    assumed = not (horizon_hi or horizon_lo)

    tp = parse_target(target, target_type, entry, bias)
    tgt_fields = {"target_px": tp.price, "target_status": tp.status.value}

    win_all = _from(bars, entry_date)
    if len(win_all) <= hz:
        return CallResult(**base, **tgt_fields, status="OPEN",
                          detail=f"horizon of {hz} trading days has not elapsed",
                          entry=entry, entry_date=entry_date,
                          horizon_days=hz, horizon_assumed=assumed)

    exit_bar = win_all[hz]
    exit_date, exit_px = exit_bar[0], exit_bar[4]           # CLOSE at the horizon end
    sign = 1.0 if bias == "bullish" else -1.0
    ret = sign * (exit_px / entry - 1.0)

    # THE COMMON LAST BAR — the benchmark leg is trimmed to what both series actually carry.
    b_win = [b for b in bench if entry_date <= b[0] <= exit_date]
    bench_ret: float | None = None
    if len(b_win) > 1:
        common_end = min(b_win[-1][0], exit_date)
        b_trim = [b for b in b_win if b[0] <= common_end]
        if len(b_trim) > 1 and b_trim[0][4] > 0:
            bench_ret = sign * (b_trim[-1][4] / b_trim[0][4] - 1.0)

    win = [b for b in win_all if b[0] <= exit_date]
    highs, lows = [b[2] for b in win], [b[3] for b in win]
    mfe = sign * ((max(highs) if sign > 0 else min(lows)) / entry - 1.0)
    mae = sign * ((min(lows) if sign > 0 else max(highs)) / entry - 1.0)

    hit: bool | None = None
    if tp.price is not None:
        hit = any(h >= tp.price for h in highs) if sign > 0 else any(lo <= tp.price for lo in lows)

    return CallResult(
        **base, **tgt_fields, status="CLOSED",
        entry=entry, entry_date=entry_date, exit=exit_px, exit_date=exit_date,
        horizon_days=hz, horizon_assumed=assumed,
        ret=ret, bench_ret=bench_ret,
        excess=(ret - bench_ret) if bench_ret is not None else None,
        mfe=mfe, mae=mae, target_hit=hit, direction_correct=ret > 0,
    )


def is_scoreable(bias: str | None) -> bool:
    """``tracker.py`` scores only a stated direction. `none`/`mixed`/`neutral` carry no direction to
    sign a return by, so they are excluded here too rather than silently treated as bullish."""
    return bias in ("bullish", "bearish")


__all__ = ["CallResult", "CallStatus", "DEFAULT_HORIZON_DAYS", "TargetStatus",
           "is_scoreable", "score_call"]
