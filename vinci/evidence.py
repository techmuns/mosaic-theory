"""The queue's EVIDENCE STRIP — inform-only context printed beside the score.

WHY IT EXISTS. The queue tells a human WHERE a name ranks and, since #420, why its volume term
moved the score. It says nothing about whether anyone is *doing* anything: issuing stock, buying,
shorting. The 2026-08-12 panel killed the price-based answer to that question — every trend state
was one 2025–26 regime measured nine ways — and the published evidence for this exact pool points
at positioning instead (Pontiff-Woodgate on net issuance; Cohen-Malloy-Pomorski on insider buys;
Rapach-Ringgenberg-Zhou on short interest). This module renders that, as it lands.

THE FENCE. Nothing here may ever reach a weight, a gate or a sort. `vinci.rank` and `vinci.screens`
must not import this module — asserted by an AST test, the same shape as the sector/label fence that
keeps a derived view from becoming a dressed-up screen. The strip is composed by the WRITER, after
ranking is finished, from data the screen already assembled.

IT DESCRIBES, IT DOES NOT CONCLUDE. Every element is a measured quantity with its direction shown
and its source recoverable from the underlying `DataField.note`. No element is allowed to name a
mechanism the input cannot support — the lesson of "heavy distribution", a label that asserted WHO
was trading from a number containing no direction, and was wrong on 2 of 10 names.
"""

from __future__ import annotations

from vinci.schemas.data_record import DataRecord


def _pct(v: float) -> str:
    """A signed percentage with an arrow, so direction survives a glance and a screen reader."""
    return f"{'↑' if v > 0 else '↓'}{abs(v):.1%}"


def evidence_strip(rec: DataRecord) -> str | None:
    """A compact context line for one name, or None when nothing is known.

    None rather than an empty string or a row of dashes: a strip with nothing in it should not
    occupy the column at all, and "—" would read as a measured absence rather than a gap.

    Elements appear in order of evidence strength, strongest first, and each is omitted rather than
    guessed when its input is UNKNOWN. Adding a leg means adding it here and nowhere else.
    """
    parts: list[str] = []

    # 1. NET SHARE ISSUANCE — the strongest leg currently wired. Shrinking share count is the
    #    bullish twin of the dilution channel; both read the same trailing window through the one
    #    shared `share_count_change`, so this number and the demote can never disagree.
    sc = rec.fundamentals.share_count_change_730d
    if sc.is_evaluable and sc.value is not None:
        parts.append(f"shares {_pct(sc.value)} 2y")

    # 2. DISTANCE FROM THE 52-WEEK LOW — descriptive only, and computed since day one while being
    #    consumed by nothing. It says whether a name has begun to come back, which nothing else on
    #    the row does. NOT a claim about what happens next: the 2026-08-12 panel found the states
    #    built on it are one regime measured many ways.
    #
    #    DRAWDOWN IS DELIBERATELY ABSENT even though the plan listed it in the price tail: the
    #    queue's `Depth (52w)` column already shows exactly that number. Printing it twice makes a
    #    dense table worse and invites the two copies to disagree.
    lo = rec.prices.dist_from_low
    if lo.is_evaluable and lo.value is not None:
        parts.append(f"+{lo.value:.0%} off low")

    return " · ".join(parts) if parts else None
