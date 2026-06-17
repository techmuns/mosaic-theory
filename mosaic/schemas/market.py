"""Market-data schema — the daily EOD bar produced by the EOD client and stored point-in-time."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, model_validator


class PriceBar(BaseModel, frozen=True):
    """One adjusted daily OHLCV bar for a security. ``bar_date`` is the knowable/as-of date."""

    internal_id: str
    bar_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str  # e.g. "polygon-grouped"

    @model_validator(mode="after")
    def _sane(self) -> PriceBar:
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < self.low:
            raise ValueError("high < low")
        if self.volume < 0:
            raise ValueError("negative volume")
        return self
