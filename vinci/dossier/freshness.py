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

TWO GUARDS, BECAUSE NEITHER PREDICTS THE OTHER. BRBR has the oldest panels (71d) and a middling
gap; MVST's panels are younger (54d) with a worse gap (+17.6%).

  * the AGE CEILING measures STALENESS — how old the oldest panel is, against the BUILD's date;
  * the RECONCILIATION measures INCOHERENCE — whether the numbers on the page agree with each other.

RE-MEASURED 2026-07-29. The age ceiling was originally an oldest→NEWEST spread, and
``stock_info.as_of`` is the newest panel on 11 of 11 dossiers — so the PRICE set one end and
refreshing prices widened the gap. Fresher market data degraded a build, which is backwards and
creates an incentive to skip refreshes. The two concerns had been merged into one number; they are
separated now, and the reconciliation already owned the price-coherence half.

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

#: Days a build's OLDEST panel may be, measured against the build's own date, before it fails.
#: Re-measured 2026-07-29 (see PanelAge): the old oldest→newest form was price-driven, so a price
#: refresh could fail a build on unchanged CIQ panels. Set from the measured
#: distribution (3–71d, median 36d), not guessed: at 60d only BRBR fails; at 45d, CNXC, MVST and
#: BRBR do — and CNXC is the name cleared under 16c this week on comps 49 days old, whose peer
#: multiples drive the cross-sectional leg. Clearing a name on data we would fail at 45 is the
#: reason for the tighter number (operator 2026-07-29). The remedy is a manual re-export, which is
#: ordinary workflow rather than a code blocker.
MAX_PANEL_AGE_DAYS = 45

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
class PanelAge:
    """How old the OLDEST panel in a build is, measured against the build's own date.

    RE-MEASURED 2026-07-29, replacing an oldest→NEWEST spread. The old measure was PRICE-DRIVEN:
    ``stock_info.as_of`` was the newest panel on 11 of 11 committed dossiers, so the price set one
    end of the gap and **refreshing prices widened it**. Moving the frontier 07-24 → 07-28 pushed
    every name +4 days (NCNO +7) and took VRRM from 45d to 49d — assemblable before the refresh,
    REFUSED after it, on unchanged CIQ panels.

    That is backwards, and it creates an incentive to skip refreshes, against everything else
    built here. MVST is the sharpest demonstration: its gap read 54d only because its price panel
    was stale at 07-08 — **not refreshing a name made its build look fresher**.

    Two concerns had been merged into one number. They are separated now:
      * *comps too old to be useful* → THIS measure, oldest panel vs the build date;
      * *price and cap incoherent* → :func:`reconcile_cap`, which already covered it.

    Same outcomes, honest cause, no perverse incentive: under this measure VRRM still fails, but
    because time passed rather than because someone refreshed."""

    oldest: str
    oldest_key: str
    as_of: str                       # the build's own date — what the age is measured against
    days: int

    def note(self) -> str:
        """The reader-facing line. Rendered on EVERY dossier, passing or failing — panel age is
        context a reader needs in order to read a multiple, not merely a failure condition."""
        return (f"oldest panel {self.days}d old — {self.oldest} ({self.oldest_key}), "
                f"against a {self.as_of} build")


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


def panel_age(mechanical: object, as_of: dt.date | str) -> PanelAge | None:
    """How old the build's OLDEST panel is against ``as_of``, or None when no panel carries a date.

    ``as_of`` is the BUILD's date — the reference date at assembly, and the stored ``assembled_at``
    when a committed artifact re-renders. That distinction matters: a committed dossier reports the
    age it had WHEN IT WAS BUILT, so re-reading last week's artifact does not silently age it.

    ONE dated panel is enough (the old spread needed two, since a gap needs two ends). A build
    with a single dated panel still has an oldest one, and its age is what is being measured."""
    dates = panel_dates(mechanical)
    if not dates:
        return None
    dates.sort(key=lambda kv: kv[1])
    ok, ov = dates[0]
    # `datetime` SUBCLASSES `date`, so an `isinstance(x, dt.date)` check accepts a datetime and
    # then `datetime - date` raises. `assembled_at` is a datetime and `reference_date` is a date,
    # and both reach this function — the datetime branch has to come FIRST.
    if isinstance(as_of, dt.datetime):
        ref = as_of.date()
    elif isinstance(as_of, dt.date):
        ref = as_of
    else:
        ref = dt.date.fromisoformat(str(as_of)[:10])
    return PanelAge(oldest=ov, oldest_key=ok, as_of=ref.isoformat(),
                    days=(ref - dt.date.fromisoformat(ov)).days)


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


#: The inputs the reconciliation needs. A build missing ANY of them cannot be checked — and the
#: page is unusable without the price regardless of any check.
_CAP_INPUTS = ("market cap", "shares outstanding", "spot price")


def absent_cap_inputs(*, cap_musd: float | None, shares: float | None,
                      spot: float | None) -> tuple[str, ...]:
    """Which reconciliation inputs are missing. Empty when the check can run.

    COMPLETENESS AND RECONCILIATION ARE DIFFERENT CHECKS, and conflating them shipped a live
    defect: `reconcile_cap` returns None when an input is absent, `check_freshness` treated None as
    "nothing to complain about", and a SMPL assembly with **no price bars at all** — no spot, no
    52-week range, no as-of — passed every gate and reported "1 done · 0 error(s)". The gate
    catches *cap ÷ shares disagrees with spot*; it did not catch *there is no spot*.

    The comment that justified it read "an absent input is its own fail-loud elsewhere". For a
    missing price at assembly there IS no elsewhere: the fields carry an honest
    `status=unknown, note="no price bars"` and nothing at BUILD level notices. That is the
    guard-that-cannot-fire class, inside a guard built to close it.

    The repo already answers this — the unusual-items guard raises when it cannot locate its block,
    because *a guard that cannot find its rows must not report a clean pass*. Same rule here."""
    return tuple(n for n, v in zip(_CAP_INPUTS, (cap_musd, shares, spot), strict=True) if not v)


def check_freshness(age: PanelAge | None, recon: CapReconciliation | None,
                    *, ticker: str, absent: tuple[str, ...] = ()) -> None:
    """FAIL LOUD on the two conditions a page cannot honestly carry. Ordinary drift is NOT one of
    them — it is a rendering obligation (clause (e)), because failing on it would fail 11 of 11 and
    a guard that stops every build is a freeze wearing a guard's name."""
    if absent:
        raise FreshnessError(
            f"{ticker}: the build is missing {', '.join(absent)} — every ratio on the page rests "
            "on the spot, and a dossier without one is not underwritable. The reconciliation "
            "cannot run either, so passing here would be a guard reporting a clean pass it never "
            "made. (A fresh worktree with an unpopulated EOD store produces exactly this: run the "
            "price refresh for this name before assembling.)")
    if age is not None and age.days > MAX_PANEL_AGE_DAYS:
        raise FreshnessError(
            f"{ticker}: {age.note()} — beyond the {MAX_PANEL_AGE_DAYS}d ceiling. The oldest "
            "panel drives the peer multiples and the cross-sectional leg; re-export it before "
            "underwriting from this page.")
    if recon is not None and recon.corporate_action:
        raise FreshnessError(
            f"{ticker}: {recon.note()} — the share basis disagrees with the cap's basis, so no "
            "per-share or EV figure on this page can be trusted. Fix the share basis; a panel "
            "re-export will NOT resolve it.")
