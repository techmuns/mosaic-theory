"""A listed line's LISTING BASIS — what one traded unit is, in the issuer's own share count.

The structured value lives here, below the resolver that reads it (`vinci.resolver.ads_ratio`)
and the data record that carries it, so neither imports the other. STATE §5.0 row 4, FPI4.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class AdsRatio(BaseModel, frozen=True):
    """A depositary line's listing ratio, or the refusal to state one — never a default.

    ``ordinary_per_ads`` is ordinary shares per ADS: 2.0 for QFIN, 0.5 for KT. A per-ordinary-share
    figure times it is the per-ADS figure; an ordinary-share count divided by it is the
    ADS-equivalent count."""

    status: Literal["known", "refused"]
    ordinary_per_ads: float | None = None
    #: which statement decided: the cover's 12(b) title, or the filing's text
    source: Literal["12(b) title", "filing text"] | None = None
    #: the issuer's own words that state the ratio
    quote: str | None = None
    #: why no ratio is stated — set exactly when ``status`` is refused
    reason: str | None = None
    form: str | None = None
    filed: date | None = None
    accession: str | None = None

    @property
    def known(self) -> bool:
        return self.status == "known" and self.ordinary_per_ads is not None

    def describe(self) -> str:
        """One line a reader can check against the filing."""
        where = (f"{self.form} {self.accession}, filed {self.filed.isoformat()}"
                 if self.form and self.accession and self.filed else "no filing read")
        if self.known:
            return (f"{self.ordinary_per_ads:g} ordinary shares per ADS ({self.source}, {where}): "
                    f"“{self.quote}”")
        return f"ADS ratio REFUSED — {self.reason} ({where})"
