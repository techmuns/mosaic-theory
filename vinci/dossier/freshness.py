"""FRESHNESS CONTRACT — item 1. Two guards over one build's dated inputs.

THE DEFECT, measured across all 11 committed dossiers 2026-07-29 (not inferred from one name):
**every rendered market cap fails to reconcile to the spot price beside it.** Cap comes from the
CIQ Comparable Analysis panel — June on most names — and the spot from the EOD store, July. Cap
feeds TEV, TEV feeds every EV/EBITDA and EV/Revenue multiple and the FCF yield, so the error
propagates into the cross-sectional leg of any thesis built on the page.

  SMPL  −2.4%   NCNO  +3.3%   IT   −7.1%   VRRM  +8.6%   CNXC  +8.9%   AORT −12.9%
  BRBR −13.0%   VITL −14.1%   EPAM −14.4%   MVST +17.6%   FUBO −91.0%

SMPL — the audited name, the one that motivated all of this — has the SMALLEST gap. A fix built to
close SMPL would have closed the least of eleven instances.

TWO GUARDS, BECAUSE NEITHER PREDICTS THE OTHER. BRBR has the worst panel spread (71d) and a middling
gap; MVST has a shorter spread (54d) and a worse gap (+17.6%). The gap is spread × volatility, so:

  * the SPREAD CEILING measures STALENESS — how old the oldest panel is;
  * the RECONCILIATION measures INCOHERENCE — whether the numbers on the page agree with each other.

WHY THE RECONCILIATION IS NOT FATAL BY DEFAULT. At any tolerance it fails 11 of 11, which is a
freeze, not a guard. But a June cap is not WRONG — it is UNLABELLED, which is item 1 clause (e):
*a frozen or older-vintage value must render marked as such, with its vintage date, wherever it
appears beside a live value.* So ordinary drift is a RENDERING obligation. What IS fatal is a cap
that cannot be a price-times-shares figure at all.

THE RATIO TELLS YOU WHICH, and reporting it is the design (operator 2026-07-29): a ratio near a
whole number is the signature of a CORPORATE ACTION straddling the panel dates — pre-split shares
against a post-split cap — while a fractional ratio is price drift. FUBO is the live instance at
**11.13×**: EDGAR's 342.4M pre-split share count against CIQ's post-split $256.4M cap and an $8.33
post-split close. Half of that was already recorded in STATE item 4 ("an 11x gap; reverse split?")
and left open. The two remediations are entirely different — re-export a panel vs fix a share
basis — so a gate that reported only pass/fail would flag it without diagnosing it.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

#: Days between a build's oldest and newest PANEL as-of before it fails. Set from the measured
#: distribution (3–71d, median 36d), not guessed: at 60d only BRBR fails; at 45d, CNXC, MVST and
#: BRBR do — and CNXC is the name cleared under 16c this week on comps 49 days old, whose peer
#: multiples drive the cross-sectional leg. Clearing a name on data we would fail at 45 is the
#: reason for the tighter number (operator 2026-07-29). The remedy is a manual re-export, which is
#: ordinary workflow rather than a code blocker.
MAX_PANEL_SPREAD_DAYS = 45

#: Beyond this the cap and the spot do not describe the same equity, and the cap must RENDER its own
#: vintage rather than sit unlabelled beside a live price.
RECONCILE_TOLERANCE = 0.02

#: How near a whole number the shares ratio must be to read as a corporate action rather than drift.
_INTEGER_TOLERANCE = 0.03

#: A PANEL date is an ARRIVAL — when an export was taken. A date that TRAVELS WITH A VALUE (an
#: own-history band's observation date, a per-point series date) is a different object, and mixing
#: them inverts the ranking: SMPL reads 115 days stale on the mixed measure and 3 days — the
#: TIGHTEST in the fleet — on panel dates alone. Excluded by name for that reason.
_NOT_A_PANEL = re.compile(
    r"own_history|stock_performance|gap_date|filing_date|maturity|expected_date|dated|points")
_PANEL_KEY = re.compile(r"as_of|asof|detail_as_of", re.I)
_ISO = re.compile(r"(20\d\d-\d\d-\d\d)")


class FreshnessError(RuntimeError):
    """A build whose dated inputs cannot honestly sit on one page."""


@dataclass(frozen=True)
class PanelSpread:
    """The oldest and newest PANEL as-of in a build, and the gap between them."""

    oldest: str
    oldest_key: str
    newest: str
    newest_key: str
    days: int

    def note(self) -> str:
        """The reader-facing line. Rendered on EVERY dossier, passing or failing — the spread is
        context a reader needs in order to read a multiple, not merely a failure condition."""
        return (f"panel spread {self.days}d — oldest {self.oldest} ({self.oldest_key}), "
                f"newest {self.newest} ({self.newest_key})")


@dataclass(frozen=True)
class CapReconciliation:
    """Whether the rendered market cap can be the rendered price times the rendered shares."""

    cap_musd: float
    shares: float
    spot: float
    implied_price: float
    gap: float                       # (implied - spot) / spot
    ratio: float                     # spot / implied — the diagnostic
    corporate_action: bool           # ratio sits on a whole number → a split straddles the panels

    def note(self) -> str:
        if self.corporate_action:
            fold = max(self.ratio, 1.0 / self.ratio) if self.ratio else self.ratio
            return (f"market cap implies ${self.implied_price:,.2f}/sh against a ${self.spot:,.2f} "
                    f"close — a ratio of {self.ratio:.4g}x ({fold:.2f}x either way), which is a "
                    f"SHARE-BASIS mismatch (a corporate action between the panels), not price "
                    f"drift")
        return (f"market cap implies ${self.implied_price:,.2f}/sh against a ${self.spot:,.2f} "
                f"close ({self.gap:+.1%}) — the cap is an older panel's, and is labelled with its "
                f"own as-of")


def panel_dates(mechanical: object, _path: str = "") -> list[tuple[str, str]]:
    """Every (key, ISO date) that is a PANEL arrival stamp. Value-borne dates are excluded — see
    ``_NOT_A_PANEL``; conflating the two is what produced an inverted staleness ranking twice."""
    out: list[tuple[str, str]] = []
    if isinstance(mechanical, dict):
        for k, v in mechanical.items():
            path = f"{_path}.{k}".lstrip(".")
            if _PANEL_KEY.search(k) and not _NOT_A_PANEL.search(path):
                raw = v.get("value") if isinstance(v, dict) else v
                m = _ISO.search(str(raw))
                if m:
                    out.append((path, m.group(1)))
            out.extend(panel_dates(v, path))
    elif isinstance(mechanical, list):
        for i, v in enumerate(mechanical):
            out.extend(panel_dates(v, f"{_path}[{i}]"))
    return out


def panel_spread(mechanical: object) -> PanelSpread | None:
    """The build's oldest→newest panel gap, or None when fewer than two panels carry a date."""
    dates = panel_dates(mechanical)
    if len(dates) < 2:
        return None
    dates.sort(key=lambda kv: kv[1])
    (ok, ov), (nk, nv) = dates[0], dates[-1]
    days = (dt.date.fromisoformat(nv) - dt.date.fromisoformat(ov)).days
    return PanelSpread(oldest=ov, oldest_key=ok, newest=nv, newest_key=nk, days=days)


def reconcile_cap(*, cap_musd: float | None, shares: float | None,
                  spot: float | None) -> CapReconciliation | None:
    """Does ``cap / shares`` agree with the rendered spot? None when any input is absent — an
    absent input is its own fail-loud elsewhere, and inventing one here would be the fabrication
    this repo refuses."""
    if not cap_musd or not shares or not spot:
        return None
    implied = cap_musd * 1e6 / shares
    if implied <= 0:
        return None
    ratio = spot / implied
    # A share-basis mismatch has NO PREFERRED DIRECTION: a PRE-split share count against a
    # POST-split cap gives ~11x (FUBO), and the reverse assignment gives ~1/11. Testing only
    # ratio >= 2 catches one and silently reports the other as ordinary drift — so fold the
    # inverse in. Review finding on #253; nothing guarantees which side of the pair is the stale
    # one, and the remediation is identical either way.
    folded = max(ratio, 1.0 / ratio)
    nearest = round(folded)
    corporate = nearest >= 2 and abs(folded - nearest) / nearest <= _INTEGER_TOLERANCE
    return CapReconciliation(
        cap_musd=cap_musd, shares=shares, spot=spot, implied_price=implied,
        gap=(implied - spot) / spot, ratio=ratio, corporate_action=corporate)


def check_freshness(spread: PanelSpread | None, recon: CapReconciliation | None,
                    *, ticker: str) -> None:
    """FAIL LOUD on the two conditions a page cannot honestly carry. Ordinary drift is NOT one of
    them — it is a rendering obligation (clause (e)), because failing on it would fail 11 of 11 and
    a guard that stops every build is a freeze wearing a guard's name."""
    if spread is not None and spread.days > MAX_PANEL_SPREAD_DAYS:
        raise FreshnessError(
            f"{ticker}: {spread.note()} — beyond the {MAX_PANEL_SPREAD_DAYS}d ceiling. The oldest "
            "panel drives the peer multiples and the cross-sectional leg; re-export it before "
            "underwriting from this page.")
    if recon is not None and recon.corporate_action:
        raise FreshnessError(
            f"{ticker}: {recon.note()} — the share basis disagrees with the cap's basis, so no "
            "per-share or EV figure on this page can be trusted. Fix the share basis; a panel "
            "re-export will NOT resolve it.")
