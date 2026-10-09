"""Aggregate the ledger — by article, author/team, publisher, thesis category, region, industry and
publication year — WITHOUT letting a small or overlapping sample read as a track record.

UNITS. One signal = one (publication, company) with a stated rating (duplicates inside a
publication are counted once, ``engine.primary_mentions``). One observation = one signal at one
horizon. Only ``direction == LONG`` (Overweight) enters a win rate; Equal-Weight and Underweight
are summarised in their own rows and never pooled with longs.

FLAGS travel with every row: ``SMALL_SAMPLE`` (< 10 completed observations at every horizon),
``SINGLE_ENTRY_DATE`` (every observation shares one entry close — cross-sectionally correlated, not
independent trials), ``OVERLAPPING_POSITIONS`` (the same security re-recommended under another
signal while still held), ``PARTIAL_COVERAGE`` (rated names that could not be priced) and
``NO_SCORED_OBSERVATIONS``. Nothing is inferred from a missing observation.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Iterable
from typing import Any

from vinci.research_audit.engine import (
    COMPLETE,
    DUPLICATE_MENTION,
    HORIZONS,
    NOT_SCORED_NONDIRECTIONAL,
    Obs,
)

SMALL_SAMPLE_N = 10
DIRECTIONS = ("LONG", "NEUTRAL", "UNDERWEIGHT")
PUBLISHERS = ("Morgan Stanley", "Bank of America", "Citi", "J.P. Morgan", "Goldman Sachs", "Nomura")


def _q(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _val(x: Any) -> float:
    """Sort key: a missing value sorts last (never read as zero)."""
    return float(x) if x is not None else float("-inf")


def _mean(xs: list[float]) -> float | None:
    return statistics.fmean(xs) if xs else None


def _win(xs: list[float]) -> float | None:
    return sum(1 for x in xs if x > 0) / len(xs) if xs else None


def horizon_stats(obs: list[Obs], h: int) -> dict[str, Any]:
    done = [o for o in obs if o.months == h and o.status == COMPLETE]
    xw = [o.excess_vs_world for o in done if o.excess_vs_world is not None]
    xs = [o.excess_vs_sp500 for o in done if o.excess_vs_sp500 is not None]
    xc = [o.excess_vs_sector for o in done if o.excess_vs_sector is not None]
    cohorts: dict[tuple[str, str], list[float]] = {}
    for o in done:
        if o.excess_vs_world is not None:
            cohorts.setdefault((o.pub_id, o.signal_id or o.pub_id), []).append(o.excess_vs_world)
    worst = min((o for o in done if o.excess_vs_world is not None),
                key=lambda o: _val(o.excess_vs_world), default=None)
    p = f"{h}m"
    return {
        f"{p}_completed": len(done),
        f"{p}_win_rate_vs_world": _win(xw),
        f"{p}_median_excess_vs_world": _q(xw, 0.5),
        f"{p}_mean_excess_vs_world": _mean(xw),
        f"{p}_ew_cohort_excess_vs_world": _mean([statistics.fmean(v) for v in cohorts.values()]),
        f"{p}_n_cohorts": len(cohorts),
        f"{p}_median_excess_vs_sp500_net": _q(xs, 0.5),
        f"{p}_win_rate_vs_sector": _win(xc),
        f"{p}_median_excess_vs_sector": _q(xc, 0.5),
        f"{p}_mean_excess_vs_sector": _mean(xc),
        f"{p}_n_sector_adjusted": len(xc),
        f"{p}_worst_excess_vs_world": worst.excess_vs_world if worst else None,
        f"{p}_worst_name": (f"{worst.audit_ticker} ({worst.pub_id})" if worst else ""),
    }


def _signals(obs: Iterable[Obs]) -> dict[tuple[str, str], Obs]:
    """One representative row per (publication, ticker) signal."""
    out: dict[tuple[str, str], Obs] = {}
    for o in obs:
        out.setdefault((o.pub_id, o.audit_ticker), o)
    return out


def _flags(rows: list[Obs], sigs: dict[tuple[str, str], Obs], stats: dict[str, Any]) -> str:
    flags: list[str] = []
    n_max = max(int(stats[f"{h}m_completed"]) for h in HORIZONS)
    if n_max == 0:
        flags.append("NO_SCORED_OBSERVATIONS")
    elif n_max < SMALL_SAMPLE_N:
        flags.append("SMALL_SAMPLE")
    entries = {o.entry_date for o in rows if o.status == COMPLETE}
    if len(entries) == 1:
        flags.append("SINGLE_ENTRY_DATE")
    if any(f.startswith("OVERLAPS") for o in rows for f in o.flags):
        flags.append("OVERLAPPING_POSITIONS")
    priced = {k for k, o in sigs.items()
              if any(r.status == COMPLETE for r in rows
                     if (r.pub_id, r.audit_ticker) == k)}
    if len(priced) < len(sigs):
        flags.append("PARTIAL_COVERAGE")
    return "; ".join(flags)


def group_table(ledger: list[Obs], level: str, key: Callable[[Obs], list[str]],
                directions: tuple[str, ...] = DIRECTIONS) -> list[dict[str, Any]]:
    """Rows of {level, group, direction, counts..., per-horizon stats..., flags}. ``key`` returns
    the group(s) an observation belongs to — a list, so a co-authored signal credits each author."""
    rated = [o for o in ledger if o.months is not None]
    groups: dict[tuple[str, str], list[Obs]] = {}
    for o in rated:
        for g in key(o):
            groups.setdefault((g, o.direction), []).append(o)
    out: list[dict[str, Any]] = []
    for (g, d) in sorted(groups, key=lambda t: (t[0], DIRECTIONS.index(t[1]))):
        if d not in directions:
            continue
        rows = groups[(g, d)]
        sigs = _signals(rows)
        n_priceable = sum(1 for k in sigs if any(
            r.status == COMPLETE or r.status.startswith("INCOMPLETE")
            for r in rows if (r.pub_id, r.audit_ticker) == k))
        row: dict[str, Any] = {
            "level": level, "group": g, "direction": d,
            "n_signals": len(sigs),
            "n_unique_securities": len({k[1] for k in sigs}),
            "n_publications": len({k[0] for k in sigs}),
            "n_priceable_signals": n_priceable,
            "n_unresolved_signals": len(sigs) - n_priceable,
        }
        for h in HORIZONS:
            row.update(horizon_stats(rows, h))
        row["flags"] = _flags(rows, sigs, row)
        out.append(row)
    return out


def _split_names(text: str) -> list[str]:
    return [t.strip() for t in text.replace(" / ", ";").split(";") if t.strip()]


def aggregates(ledger: list[Obs]) -> dict[str, list[dict[str, Any]]]:
    return {
        "article": group_table(ledger, "article", lambda o: [f"{o.pub_id} — {o.title}"]),
        "thesis_category": group_table(ledger, "thesis_category", lambda o: [o.thesis_category]),
        "publisher": group_table(ledger, "publisher", lambda o: [o.publisher]),
        "region": group_table(ledger, "region", lambda o: [o.region]),
        "sector": group_table(ledger, "sector (Vanguard sector-fund N-PORT holding)",
                              lambda o: [o.sector]),
        "industry": group_table(ledger, "industry (SEC SIC title)", lambda o: [o.industry]),
        "publication_year": group_table(ledger, "publication_year",
                                        lambda o: [o.public_date[:4]]),
        "covering_analyst": group_table(ledger, "covering analyst (rating owner)",
                                        lambda o: [o.covering_analyst]),
        "thesis_team": group_table(ledger, "thesis team (publication lead)",
                                   lambda o: [o.thesis_team]),
        "named_author": group_table(ledger, "named author (shared credit)",
                                    lambda o: _split_names(o.authors)),
    }


#: A rank needs this many publication cohorts at 12m as well as SMALL_SAMPLE_N observations: names
#: sharing ONE entry close are one cross-sectional draw, however many of them there are.
MIN_RANK_COHORTS = 2


def _person_key(name: str) -> str:
    """First + last name, middle initials dropped — used ONLY to flag variants, never to merge."""
    parts = [p for p in name.replace(".", " ").split() if len(p) > 1]
    return f"{parts[0]} {parts[-1]}".lower() if len(parts) >= 2 else name.lower()


def leaderboard(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sorted for reading, ranked only where the sample can bear it. A rank is assigned only to a
    LONG group with >= SMALL_SAMPLE_N completed 12-month observations from >= MIN_RANK_COHORTS
    publication cohorts; everything else is listed UNRANKED with its n, so a 1-observation (or a
    one-cohort) 'leader' never reads as a leader. Names that look like spelling variants of one
    person ('Michelle Weaver' / 'Michelle M. Weaver') are FLAGGED, never merged."""
    longs = [dict(r) for r in rows if r["direction"] == "LONG"]
    longs.sort(key=lambda r: (-int(r["12m_completed"]), -_val(r["12m_median_excess_vs_world"])))
    eligible = [r for r in longs if int(r["12m_completed"]) >= SMALL_SAMPLE_N
                and int(r["12m_n_cohorts"]) >= MIN_RANK_COHORTS]
    eligible.sort(key=lambda r: -_val(r["12m_median_excess_vs_world"]))
    rank = {id(r): i + 1 for i, r in enumerate(eligible)}
    for r in longs:
        r["rank_12m_median_excess"] = rank.get(
            id(r), f"UNRANKED (needs n>={SMALL_SAMPLE_N} and >={MIN_RANK_COHORTS} cohorts at 12m)")
    groups: dict[str, set[str]] = {}
    for r in rows:
        groups.setdefault(_person_key(str(r["group"])), set()).add(str(r["group"]))
    for r in longs:
        twins = sorted(groups[_person_key(str(r["group"]))] - {str(r["group"])})
        if twins:
            r["flags"] = "; ".join(x for x in (r["flags"], f"NAME_VARIANT_OF {twins} (not merged)")
                                   if x)
    others = [dict(r) for r in rows if r["direction"] != "LONG"]
    for r in others:
        r["rank_12m_median_excess"] = "NOT RANKED (not a long rating)"
    return longs + others


def first_occurrence(ledger: list[Obs]) -> list[Obs]:
    """Drop a LONG re-recommendation of a security still held under the same publisher's earlier
    signal at the same horizon (the double-counting sensitivity)."""
    keep: list[Obs] = []
    for o in sorted(ledger, key=lambda o: (o.entry_date, o.pub_id)):
        if o.status == COMPLETE and o.direction == "LONG" and any(
            k.status == COMPLETE and k.direction == "LONG" and k.audit_ticker == o.audit_ticker
            and k.publisher == o.publisher and k.months == o.months and k.pub_id != o.pub_id
            and k.entry_date <= o.entry_date < k.exit_date
            for k in keep
        ):
            continue
        keep.append(o)
    return keep


def publisher_comparison(ledger: list[Obs], wb_publications: list[Any],
                         wb_signals: list[Any]) -> list[dict[str, Any]]:
    by_pub = {p: [o for o in ledger if o.publisher == p] for p in PUBLISHERS}
    dedup = first_occurrence(ledger)
    out: list[dict[str, Any]] = []
    for pub in PUBLISHERS:
        rows = by_pub[pub]
        arts = [p for p in wb_publications if p.publisher == pub]
        sigs = [s for s in wb_signals if s.publisher == pub]
        unique = {(o.pub_id, o.audit_ticker) for o in rows if o.status != DUPLICATE_MENTION}
        rated = _signals(o for o in rows if o.months is not None)
        longs = {k: o for k, o in rated.items() if o.direction == "LONG"}
        long_rows = [o for o in rows if o.direction == "LONG" and o.months is not None]
        priced_long = {(o.pub_id, o.audit_ticker) for o in long_rows if o.status == COMPLETE}
        row: dict[str, Any] = {
            "publisher": pub,
            "articles_in_registry": len(arts),
            "articles_day_dated": sum(1 for p in arts if p.granularity == "Day"),
            "articles_month_only": sum(1 for p in arts if p.granularity != "Day"),
            "thesis_signals_in_workbook": len(sigs),
            "thesis_signals_testable_yes": sum(1 for s in sigs
                                               if s.testability.lower().startswith("yes")),
            "company_mentions_unique": len(unique),
            "mentions_nondirectional": sum(1 for o in rows
                                           if o.status == NOT_SCORED_NONDIRECTIONAL),
            "rated_signals": len(rated),
            "long_signals_overweight": len(longs),
            "long_signals_priced": len(priced_long),
            "long_signals_unresolved": len(longs) - len(priced_long),
            "neutral_signals": sum(1 for o in rated.values() if o.direction == "NEUTRAL"),
            "underweight_signals": sum(1 for o in rated.values() if o.direction == "UNDERWEIGHT"),
        }
        for h in HORIZONS:
            row.update(horizon_stats(long_rows, h))
        dd = [o for o in dedup if o.publisher == pub and o.direction == "LONG"]
        for h in HORIZONS:
            st = horizon_stats(dd, h)
            row[f"{h}m_first_occurrence_completed"] = st[f"{h}m_completed"]
            row[f"{h}m_first_occurrence_median_excess_vs_world"] = \
                st[f"{h}m_median_excess_vs_world"]
        row["flags"] = _flags(long_rows, longs, row) if long_rows else "NO_SCORED_OBSERVATIONS"
        blocked = [f"{s.signal_id}: {s.testability} — {s.blocked_because}" for s in sigs
                   if not s.testability.lower().startswith("yes")]
        row["missing_coverage"] = " | ".join(blocked)
        n12 = row["12m_completed"]
        row["finding"] = (
            "NO SCORED OBSERVATIONS — no track record inferred from absence" if n12 == 0 else
            f"{n12} completed 12m long observations from {row['12m_n_cohorts']} publication "
            f"cohort(s) — a pilot sample of one research channel, not a publisher track record"
        )
        out.append(row)
    return out


def distribution(ledger: list[Obs], direction: str = "LONG") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for h in HORIZONS:
        xs = [o.excess_vs_world for o in ledger if o.months == h and o.status == COMPLETE
              and o.direction == direction and o.excess_vs_world is not None]
        out.append({
            "direction": direction, "horizon_months": h, "n": len(xs),
            "min": _q(xs, 0.0), "p10": _q(xs, 0.1), "p25": _q(xs, 0.25), "median": _q(xs, 0.5),
            "p75": _q(xs, 0.75), "p90": _q(xs, 0.9), "max": _q(xs, 1.0), "mean": _mean(xs),
            "stdev": statistics.stdev(xs) if len(xs) > 1 else None,
            "share_below_minus_20pct": (sum(1 for x in xs if x < -0.20) / len(xs)) if xs else None,
        })
    return out


def worst_outcomes(ledger: list[Obs], n: int = 15) -> list[Obs]:
    done = [o for o in ledger if o.status == COMPLETE and o.direction == "LONG"
            and o.excess_vs_world is not None]
    return sorted(done, key=lambda o: _val(o.excess_vs_world))[:n]
