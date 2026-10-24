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

TWO GUARDS, BECAUSE NEITHER PREDICTS THE OTHER. BRBR has the oldest panels (74d) and a middling
gap; MVST's panels are younger (56d) with a worse gap (+17.6%).

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
from typing import Any, NamedTuple

#: Days a build's OLDEST panel may be, measured against the build's own date, before it fails.
#: Re-measured 2026-07-29 (see PanelAge): the old oldest→newest form was price-driven, so a price
#: refresh could fail a build on unchanged CIQ panels.
#:
#: Set from the measured distribution, not guessed — RE-MEASURED with the ceiling, because the
#: figures below described the OLD gap and a constant justified by stale numbers is the
#: assertion-integrity defect wearing a comment: **8–74d, median 39d** across the 11 committed
#: dossiers. At 60d only BRBR fails; at 45d **BRBR, CNXC, MVST and VRRM** do — and CNXC is the
#: name cleared under 16c on comps that are 53 days old, whose peer multiples drive the
#: cross-sectional leg. Clearing a name on data we would fail at 45 is the reason for the tighter
#: number (operator 2026-07-29). The remedy is a manual re-export, ordinary workflow rather than a
#: code blocker. FUBO sits on exactly 45 and PASSES this ceiling; it fails the reconciliation.
MAX_PANEL_AGE_DAYS = 45

#: Beyond this the cap and the spot do not describe the same equity, and the cap must RENDER its own
#: vintage rather than sit unlabelled beside a live price.
RECONCILE_TOLERANCE = 0.02

#: How near a whole number the shares ratio must be to read as a corporate action rather than drift.
_INTEGER_TOLERANCE = 0.03

#: A PANEL date is an ARRIVAL — when an export was taken. A date that TRAVELS WITH A VALUE (an
#: own-history band's observation date, a per-point series date) is a different object, and mixing
#: them inverts the ranking: SMPL reads 115 days stale on the mixed measure and 8 days — the
#: TIGHTEST in the fleet — on panel dates alone. Excluded by name for that reason.
#:
#: ``price_as_of`` joined the list 2026-09-30, when the forward-multiple rows first carried one.
#: It is the same object as the rest: each row stamps the close ITS OWN multiple divides by, so
#: four rows produced four copies of one date. And it is a copy of a date that STILL GATES —
#: ``forward_multiples``' price and ``stock_info.as_of`` are both ``max(bars).bar_date`` from the
#: same ``store.get_price_history`` call (``_refresh_price_and_pe`` takes the max directly;
#: ``compute_price_features`` reads ``bars[-1]`` and uses its ``reference_date`` only to flag
#: staleness), so the ceiling, which reads the OLDEST panel, cannot move. Counting them would
#: have added N duplicates of an already-gating date to the inventory and nothing else.
#:
#: ``lease_basis`` joined it 2026-10-19 (#750's pages): its ex-lease band is an own-history band
#: rebuilt on one lease basis, and its ``as_of`` is that band's latest FILING date — the date its
#: current reading was struck at, travelling with the value exactly as ``own_history``'s does.
#: Counted as an arrival it read ten pages 47–103 days stale against a 45-day ceiling (AMZN 70d,
#: VITL 103d) while every export on them was current.
_NOT_A_PANEL = re.compile(
    r"own_history|stock_performance|gap_date|filing_date|maturity|expected_date|dated|points"
    r"|price_as_of|lease_basis")
_PANEL_KEY = re.compile(r"as_of|asof|detail_as_of", re.I)
_ISO = re.compile(r"(20\d\d-\d\d-\d\d)")


#: The largest bar-to-bar gap the STORE ITSELF exhibits — derived, not a calendar. Measured across
#: 7,225 consecutive-bar pairs, 2021-07→2026-07, 14 symbols, in the local store on 2026-07-30:
#: 1d 78.0%, 2d 1.2%, 3d 18.0%, 4d 2.9%, and NOTHING beyond 4. So a name whose latest bar trails the
#: fleet by more than this is not behind a weekend or a holiday — it is behind a fetch that did not
#: run. (4d is the Good-Friday / Monday-holiday shape; a Thanksgiving week peaks at 3d because the
#: Friday session is open.)
#:
#: THE EVIDENCE IS NOT IN THE REPO, and the figures above are therefore not reproducible from a
#: clone: ``data/`` is git-ignored and per-worktree, so another checkout re-deriving this would see
#: a different distribution. That is why the number is not merely asserted here —
#: ``test_the_tolerance_matches_the_stores_own_observed_gaps`` RE-DERIVES it from whatever store is
#: present and reds if that store exhibits a larger gap. The constant is a claim the suite re-checks
#: locally, not a measurement a reader can audit from the repo, and it is written down that way.
#:
#: SAME TRICK AS THE PRIOR-BAR RESOLUTION: derive the trading calendar from the data instead of
#: encoding one. A hardcoded 3 would have been right until the first four-day holiday week, and a
#: hardcoded holiday table is a maintenance obligation nobody will service.
MAX_STORE_LAG_DAYS = 4


def store_lag(latest_by_name: dict[str, str]) -> dict[str, int]:
    """Per-name lag in days behind the FLEET's newest bar. ``{}`` when the store is empty.

    THE STORE AGAINST ITSELF, needing no calendar and no clock (operator): if one name trails the
    others, its fetch failed or it was halted — visible without knowing what day it is. The separate
    question of whether the whole fleet is behind is :func:`fleet_lag`, because the two have
    different remedies: refresh ONE name, versus run the refresh at all.

    LIVE INSTANCE at the time of writing: IWM and MDY — the BENCHMARKS, which feed
    ``rel_ret_vs_market`` and therefore a screen gate — trailed by 8 days while all eleven dossier
    names sat at 0. Nothing measured that, which is the gap this closes."""
    if not latest_by_name:
        return {}
    newest = max(latest_by_name.values())
    return {n: (dt.date.fromisoformat(newest) - dt.date.fromisoformat(d)).days
            for n, d in latest_by_name.items()}


def stale_names(latest_by_name: dict[str, str]) -> dict[str, int]:
    """Names trailing the fleet by more than :data:`MAX_STORE_LAG_DAYS`. Empty when all agree."""
    return {n: lag for n, lag in store_lag(latest_by_name).items() if lag > MAX_STORE_LAG_DAYS}


def fleet_lag(latest_by_name: dict[str, str], today: dt.date) -> int | None:
    """How far the WHOLE store trails ``today`` — the unrun-refresh signal. None on an empty store.

    KEYED ON AGE, NOT ON TODAY'S BAR (operator ruling, recorded in STATE). Assembly here runs in
    Indian daytime against a prior US close, so "no bar for today" is the NORMAL case and a guard
    that refused on it would refuse every run before the US close. What is reportable is a lag
    beyond what the store's own gaps can explain."""
    if not latest_by_name:
        return None
    return (today - dt.date.fromisoformat(max(latest_by_name.values()))).days


def store_freshness_note(latest_by_name: dict[str, str], today: dt.date) -> str | None:
    """The caveat, or None when the store is current. NEVER raises — see :func:`consensus_note`.

    Two distinct findings, because they have different remedies: individual names behind the fleet
    (that name's fetch failed), and the whole fleet behind today (the refresh was not run). IT's 6%
    divergence was the second, and nothing measured it."""
    if not latest_by_name:
        return "price store is EMPTY — no bar for any name; run the price refresh"
    parts: list[str] = []
    if (stale := stale_names(latest_by_name)):
        worst = sorted(stale.items(), key=lambda kv: -kv[1])
        parts.append("names behind the fleet: "
                     + ", ".join(f"{n} {lag}d" for n, lag in worst[:5]))
    lag = fleet_lag(latest_by_name, today)
    if lag is not None and lag > MAX_STORE_LAG_DAYS:
        parts.append(f"the whole store is {lag}d behind {today.isoformat()} — the refresh has not "
                     "been run")
    return "; ".join(parts) or None


class FreshnessError(RuntimeError):
    """A build whose dated inputs cannot honestly sit on one page."""


@dataclass(frozen=True)
class PanelAge:
    """How old the OLDEST panel in a build is, measured against the build's own date.

    RE-MEASURED 2026-07-29, replacing an oldest→NEWEST spread. The old measure was PRICE-DRIVEN:
    ``stock_info.as_of`` was the newest panel on 11 of 11 committed dossiers, so the price set one
    end of the gap and **refreshing prices widened it**. Moving the frontier 07-24 → 07-28 pushed
    every name +4 days (NCNO +7) and took VRRM's OLD-measure gap from 45d to 49d — assemblable
    before the refresh, REFUSED after it, on unchanged CIQ panels. (Under THIS measure VRRM is
    48d and still over the ceiling — but because time passed, not because someone refreshed.)

    That is backwards, and it creates an incentive to skip refreshes, against everything else
    built here. MVST is the sharpest demonstration: its OLD-measure gap read 54d only because
    its price panel was stale at 07-08 — **not refreshing a name made its build look fresher**.

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


#: THE STALENESS SPLIT (operator, 2026-07-30). Two ages wore one number, and only one is ours.
#:
#: * **EXPORT staleness** — we have not pulled. An operator action fixes it, so it GATES the build.
#: * **CONSENSUS staleness** — no analyst has revised. Nothing we do moves it, so a name nobody
#:   revises is a CANDIDATE, not a defect. It prints, caveats past the same ceiling, feeds the
#:   neglect screen — and never gates.
#:
#: THE LIVE CASE: AORT's Estimates workbook was re-exported 2026-07-30 and still reads 2026-06-30,
#: because no analyst has revised it since. Under one merged number that is 30 days of "staleness"
#: no operator action can clear, counting down to a ceiling breach.
#:
#: MEMBERSHIP IS MEASURED, not assumed — each path classified by the source_ref its own node
#: carries: ``catalyst_path.as_of`` and ``financial_summary.as_of`` both stamp from *CIQ
#: Estimates→Recent Changes*, and ``implied_expectations.multiples_as_of`` is assigned from
#: ``catalyst.as_of`` in ``_implied_expectations``. (``financial_summary`` is the surprise — the
#: NAME says Financials workbook, the STAMP is the Estimates event.) The other two are ours:
#: ``tev_as_of`` parses from ``comps_market_cap``'s source_ref (Comparable Analysis → Financial
#: Data), and ``stock_info.as_of`` is the EOD store.
#:
#: WHY THIS IS NOT A LOOPHOLE: an Estimates workbook nobody re-exported is also stale, and this
#: classification cannot see that — it reads the embedded data date either way. What still catches a
#: missing pull is the export side, which still gates. What is removed is only the case where a
#: freshly-pulled file reads old because the street went quiet.
CONSENSUS_PANELS: frozenset[str] = frozenset({
    "catalyst_path.as_of",
    "financial_summary.as_of",
    "valuation.implied_expectations.multiples_as_of",
    # (A2b) The EV-gap's CONSENSUS vintage — the street's to revise, so it prints and never gates.
    # Its sibling `ev_gap.vintages.tev_as_of` is deliberately NOT here: the TEV comes off the comps
    # workbook, which is OURS to re-export, so it gates like every other export panel.
    #
    # ADDED AFTER IT SILENTLY RE-BROKE THE SPLIT. This list is an ALLOWLIST and everything else
    # defaults to the GATING class, so persisting a consensus date under a new key put MVST's
    # `≥2026-05-15` back in front of the export gate — 56d against the 45d ceiling — and refused it
    # for exactly the condition the 2026-07-30 staleness split had just stopped refusing it for:
    # "no analyst had revised it", which no operator action clears. Default-to-gating is the safe
    # direction, but it means a new consensus-dated field re-conflates the split unless it is
    # classified here. `test_freshness` now asserts every dated key is consciously classified.
    "ev_gap.vintages.consensus_as_of",
})


class CiqAsOf(NamedTuple):
    """The corrected stamp AND whether the correction actually ran.

    ``resolved`` is REPORTED, not inferred. The first cut returned a bare date and callers worked
    out "was this corrected?" from ``corrected != stated`` plus an empty-bars check — which is
    wrong in two live cases: a stamp older than every bar, and a bar list whose entries are all
    malformed. Both come back UNCHANGED with a non-empty list, so the caller concluded "corrected,
    nothing to change" and labelled an export stamp as a data date. Assert it or derive it — so the
    function that knows now says so."""

    as_of: str
    resolved: bool


def corrected_ciq_as_of(stated: str, bars: list[Any]) -> CiqAsOf:
    """CIQ's ``As-Of`` is the EXPORT date; the data is the PRIOR trading close. Return the real one.

    **MEASURED 11 OF 11, not inferred.** CIQ's printed ``Day Close Price Latest`` was compared
    to the Polygon store on every committed name: none matched the close ON the stated date, all
    eleven matched the close BEFORE it — SMPL's 07-24 stamp is the 07-23 close of 10.28, EPAM's
    07-29 stamp is 100.40 against 106.89 on the day itself. So every CIQ-derived as-of reads one
    trading day too new, panel ages are understated, and the ceiling passes a day early.

    RESOLVED FROM THE STORE'S PRIOR BAR, NEVER ``date - 1`` (operator). Two of the eleven stamps
    fall on a Monday — NCNO's 2026-07-20 and VITL's 2026-06-29 — where the correction is THREE
    calendar days, not one. A calendar-day version ships clean on nine names and is wrong on those
    two, and would be wrong again on every holiday. The prior bar handles both for free.

    Fail-safe: with no bar before ``stated`` (an empty or short store) the stamp is returned
    UNCHANGED. An uncorrected age is too NEW by a day, which the gate treats as fresher — but
    inventing a date from a store that cannot support it is the fabrication this repo refuses, and
    the honest miss is recoverable by refreshing the store.

    REVIEW FINDING: the first cut read ``getattr(b, "bar_date", "")`` and a malformed bar became the
    empty string, which sorts BELOW every date — so a list of malformed bars passed the "has a
    prior" test and returned ``""`` as the corrected stamp. A fail-safe branch that fabricates an
    empty date is worse than the defect it guards, so candidates are now filtered to real ISO dates
    and the unchanged-stamp path catches the rest."""
    dates = [d for b in bars
             if _ISO.fullmatch(d := str(getattr(b, "bar_date", "") or "")) and d < stated]
    if not dates:
        return CiqAsOf(stated, resolved=False)
    return CiqAsOf(max(dates), resolved=True)


#: The gap this allows: a Friday close to the following Tuesday when Monday is a holiday — the
#: widest ROUTINE separation between two consecutive trading days.
#:
#: NOT AN ABSOLUTE BOUND, and the comment used to say it was (review of #488). UNSCHEDULED
#: closures exceed it: Hurricane Sandy shut the NYSE Mon-Tue 2012-10-29/30, so Friday 10-26 to
#: Wednesday 10-31 is a FIVE-day gap between consecutive trading days. The error direction is
#: safe — a longer real gap makes this guard REFUSE a correction it could have made, leaving the
#: header stamp standing, which is the honest fallback either way. Widening it to cover every
#: historical closure would weaken the guard against exactly the coincidental match it exists to
#: stop, so the routine bound is kept and its limit is stated rather than overclaimed.
_COVERAGE_GAP_DAYS = 4


def date_of_close(close: float, bars: list[Any], *, not_after: dt.date | None = None,
                  tol: float = 0.005) -> dt.date | None:
    """The date whose close IS this price — or None when the store cannot say so unambiguously.

    IDENTIFIES rather than ASSUMES, which is why this exists beside `corrected_ciq_as_of`. That
    function encodes a measured CONVENTION ("the data is the prior trading close", 11 of 11) and
    cannot detect its own failure: if CIQ ever moved to same-day pricing, "prior trading bar" would
    shift every stamp back a day and every test would stay green. Matching the panel's own printed
    `Day Close Price Latest` against the store reads the answer out of the data instead.

    FAIL LOUD, NEVER GUESS. No bar carrying the price returns None and the caller leaves the stamp
    UNCORRECTED — the honest miss this repo prefers to an invented date.

    RECURRENCE RESOLVES BY RECENCY, BUT ONLY INSIDE A BOUND. Several bars may carry the price on a
    low-priced name; the latest one BEFORE ``not_after`` is the one CIQ's convention names, and on
    the four bundles that needed it the answer matched the offset method exactly. **Without
    ``not_after`` that same recency rule is dangerous** — the latest match may sit AFTER the panel
    and move the stamp FORWARD, the one thing this correction must never do — so an unbounded call
    that finds SEVERAL matches refuses rather than picking one."""
    def _as_date(v: Any) -> dt.date | None:
        if isinstance(v, dt.datetime):
            return v.date()
        if isinstance(v, dt.date):
            return v
        try:
            return dt.date.fromisoformat(str(v))
        except (TypeError, ValueError):
            return None

    # COVERAGE PRECONDITION (HLF, 2026-08-21). The panel names a bar; if the store's history STOPS
    # BEFORE the stamp, that bar is ABSENT BY CONSTRUCTION and every match below is a coincidence.
    #
    # THE BOUND WAS ONE-SIDED. `not_after` excludes bars at or after the stamp and the docstring
    # treats it as the cure for "an otherwise five-year scan that would eventually meet a
    # coincidental match — publishing a date years off". It only bounds the scan FORWARD; backward
    # it ran the full history. HLF is that case: its panel prints 12.45 as of 2026-08-20, the store
    # ends 2026-08-14, no bar within a half-cent exists after July (nearest 12.44 on 07-30, 12.47
    # on 07-15) — so the scan reached back to 2025-12-03, `max(hits)` correctly returned that
    # latest match, and the correction published a data date 261 DAYS OLD. The 45-day freshness
    # ceiling then refused the assembly, naming a stale panel that was exported the day before.
    #
    # WERN IS THE CONTROL and the reason this is a precondition rather than a distance knob: SAME
    # shape (stamp 2026-08-19, store ends 2026-08-14), no coincidental match, correctly returned
    # None. The difference between the two names was luck, not evidence — so the refusal must key
    # on the store's COVERAGE, which is knowable, rather than on how far back a match happened to
    # sit, which is a threshold nobody can set from face validity.
    #
    # Fails to the path the function already has: None leaves the stamp UNCORRECTED and the header
    # stands. A correction that cannot see the data it is correcting must not run.
    # THE FRONTIER MUST REACH THE PRIOR TRADING CLOSE, NOT THE STAMP — and the first cut of this
    # guard got that wrong. Requiring `frontier >= not_after` refused the legitimate case the
    # recurrence pin covers (bars ending 08-13 under an 08-14 stamp): the panel's data IS the
    # prior trading close, so a store ending exactly there COVERS it. The existing pin caught it.
    # `_COVERAGE_GAP_DAYS` spans a long weekend plus a holiday — it is a CALENDAR fact about how
    # far apart two consecutive trading days can sit, not a face-validity threshold, and no
    # market calendar is available here to do better.
    if not_after is not None and bars:
        frontier = max((d for b in bars if (d := _as_date(getattr(b, "bar_date", None)))),
                       default=None)
        if frontier is not None and (not_after - frontier).days > _COVERAGE_GAP_DAYS:
            return None

    hits = []
    for b in bars:
        d = _as_date(getattr(b, "bar_date", None))
        c = getattr(b, "close", None)
        if d is None or not isinstance(c, (int, float)):
            continue
        # STRICTLY BEFORE THE STAMP. An export cannot predate the data it carries, so a bar AFTER
        # the stamp can never be its source; and CIQ's measured convention (11 of 11) is that the
        # data is the PRIOR trading close, so a bar ON the stamp cannot be it either. Excluding
        # both also bounds an otherwise five-year scan that would eventually meet a coincidental
        # match — publishing a date years off, or moving the stamp FORWARD.
        if not_after is not None and d >= not_after:
            continue
        if abs(float(c) - close) <= tol:
            hits.append(d)
    if not hits:
        return None
    # UNBOUNDED + AMBIGUOUS = REFUSE (review of #469). Recency is only principled relative to the
    # export stamp; with no bound there is nothing to be "latest before", and the newest match can
    # be a coincidental later bar that drags the stamp FORWARD. One match is still an
    # identification, so it stands; several without a bound is a guess.
    if not_after is None and len(hits) > 1:
        return None
    # RECURRENCE IS RESOLVED BY RECENCY, NOT REFUSED (measured 2026-08-18). Requiring exactly one
    # match refused four of nineteen bundles — FUBO 9.70, MVST 0.92, UBER 68.18, VRRM 4.18 — all
    # LOW-PRICED names whose close simply recurs across the history. That is ambiguity in the
    # SEARCH, not in the data: the latest qualifying bar is the one CIQ's own convention names,
    # and on all four it lands exactly on the prior trading close the offset method predicts. Two
    # independent signals agreeing is stronger evidence than either alone, so refusing there threw
    # away an answer the corpus supports. Measured fleet-wide: 13 names unchanged, 4 resolved,
    # 0 moved — and NIKE, whose printed close matches NO bar, still correctly refuses above.
    return max(hits)


def panel_dates(mechanical: object, _path: str = "") -> list[tuple[str, str]]:
    """Every (key, ISO date) that is a PANEL arrival stamp. Value-borne dates are excluded — see
    ``_NOT_A_PANEL``; conflating the two is what produced an inverted staleness ranking twice.

    Returns BOTH classes; callers select via :func:`panel_age`'s mandatory ``kind``."""
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


def panel_age(mechanical: object, as_of: dt.date | str, *,
              kind: str) -> PanelAge | None:
    """How old the build's OLDEST panel of ``kind`` is against ``as_of``, or None when that class
    carries no dated panel.

    ``kind`` is ``"export"`` (ours to refresh — this is what GATES) or ``"consensus"`` (the street's
    to revise — prints and caveats, never gates). See :data:`CONSENSUS_PANELS`.

    **NO DEFAULT, deliberately.** Before the split this function answered one merged question and
    both callers took it implicitly. Adding a default would let a caller keep the old meaning while
    the constant beside it says the classes are different — the unasserted-convention class, in the
    function whose whole purpose is now to distinguish them. Two callers; both state which they
    want.

    ``as_of`` is the BUILD's date — the reference date at assembly, and the stored ``assembled_at``
    when a committed artifact re-renders. That distinction matters: a committed dossier reports the
    age it had WHEN IT WAS BUILT, so re-reading last week's artifact does not silently age it.

    ONE dated panel is enough (the old spread needed two, since a gap needs two ends). A build
    with a single dated panel still has an oldest one, and its age is what is being measured."""
    if kind not in ("export", "consensus"):
        raise ValueError(f"panel_age kind must be 'export' or 'consensus', got {kind!r}")
    want_consensus = kind == "consensus"
    dates = [(k, d) for k, d in panel_dates(mechanical)
             if (k in CONSENSUS_PANELS) is want_consensus]
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


def whole_number_ratio(ratio: float) -> bool:
    """Is a positive ``ratio`` a share-basis change rather than drift — within `_INTEGER_TOLERANCE`
    of a whole number ≥2, either way up? One rule for `reconcile_cap` and the prices source's
    split-shaped step (`vinci.quality.sources.prices`).

    A share-basis mismatch has NO PREFERRED DIRECTION: a PRE-split share count against a POST-split
    cap gives ~11x (FUBO), and the reverse assignment gives ~1/11. Testing only ratio >= 2 catches
    one and silently reports the other as ordinary drift — so fold the inverse in. Review finding
    on #253; nothing guarantees which side of the pair is the stale one, and the remediation is
    identical either way."""
    folded = max(ratio, 1.0 / ratio)
    nearest = round(folded)
    return nearest >= 2 and abs(folded - nearest) / nearest <= _INTEGER_TOLERANCE


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
    return CapReconciliation(
        cap_musd=cap_musd, shares=shares, spot=spot, implied_price=implied,
        gap=(implied - spot) / spot, ratio=ratio, corporate_action=whole_number_ratio(ratio))


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


def consensus_note(age: PanelAge | None) -> str | None:
    """The CAVEAT for a name the street has stopped revising, or None inside the ceiling.

    NEVER raises. Consensus staleness is not ours to fix — an operator can re-export every workbook
    and the date will not move — so gating on it would refuse a build for a condition no action
    clears. The same ceiling is reused deliberately: a second threshold would be a second number to
    justify, and the question ("is this data old enough to distrust?") is identical. What differs is
    only who can act on the answer."""
    if age is None or age.days <= MAX_PANEL_AGE_DAYS:
        return None
    return (f"consensus is {age.days}d old ({age.oldest}, {age.oldest_key}) — beyond the "
            f"{MAX_PANEL_AGE_DAYS}d ceiling. No analyst has revised this name in that window; a "
            "re-export will NOT move it. Treat as a neglect signal, not a stale pull.")


def check_freshness(age: PanelAge | None, recon: CapReconciliation | None,
                    *, ticker: str, absent: tuple[str, ...] = ()) -> None:
    """FAIL LOUD on the two conditions a page cannot honestly carry. Ordinary drift is NOT one of
    them — it is a rendering obligation (clause (e)), because failing on it would fail 11 of 11 and
    a guard that stops every build is a freeze wearing a guard's name.

    ``age`` MUST be the EXPORT age (``panel_age(..., kind="export")``). Passing the consensus age
    here would restore exactly the defect the split removed — refusing a build because the street
    went quiet. :func:`consensus_note` carries that side, and it cannot raise."""
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
