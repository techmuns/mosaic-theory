"""Which companies an ingest reads: the committed pages' (``pages``) or the screen's (``screen``).

``pages``: every company with a committed page, plus the followed names. ``screen``: every company
in one screen run's universe, the population its gates ran over (``data/snapshots/screen_runs``).

The rule is stated in the manifest beside the result, with every name the rule named but the ingest
could not read and why, so a count never stands without its population (CLAUDE.md, EVERY COUNT
STATES ITS BOUNDARY).

NO NAME IS HELD BACK (operator ruling 2026-11-05,
``docs/records/2026-11-05-mosaic-theory-holds-back-no-name.md``): an ingest selects its rule's
whole population. Only the parity's comparison skips a page (``scope_names``' ``exclude``), and it
writes nothing. The two snapshots written under the lifted hold each excluded one name of a list
of six, and their manifests say so (``excluded_by_operator_instruction`` 1,
``exclusions_listed`` 6); an ingest now writes both counts as 0
(``docs/records/2026-11-06-the-fact-layer-holds-back-no-name.md``).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from vinci.facts.edgar_ingest import NotInCacheError, cik_for_ticker, pad_cik
from vinci.facts.store import FactsStoreError
from vinci.followed import follow_records

RULE = "committed pages (data/dossiers/*/dossier.json) plus followed names (data/followed.json)"
SCREEN_RULE = ("the universe of screen run {run_id}: its candidate rows "
               "(data/snapshots/screen_runs/{run_id}.jsonl), each ticker's CIK from "
               "data/snapshots/securities.jsonl through data/snapshots/universe_snapshot.jsonl at "
               "the run's universe_as_of ({universe_as_of})")


@dataclass(frozen=True)
class ScopeName:
    ticker: str
    cik: str | None             # None when it could not be resolved from the cache
    page: Path | None           # the committed dossier.json, when the name has one
    followed: bool
    unresolved: str | None = None


def page_path(dossiers_dir: Path, ticker: str) -> Path:
    return dossiers_dir / ticker / "dossier.json"


def scope_names(dossiers_dir: Path, followed_path: Path, cache_dir: Path, *,
                exclude: frozenset[str] = frozenset()) -> tuple[list[ScopeName], int]:
    """The names the rule selects, minus ``exclude``; and how many the exclusion removed."""
    pages = {p.parent.name for p in dossiers_dir.glob("*/dossier.json")}
    # the follow list's own strict reader: a tombstoned name (`followed_until` set) is no longer
    # followed, and a malformed entry raises rather than being skipped
    followed = {r.ticker for r in follow_records(followed_path) if r.held_on(date.today())}
    named = pages | followed
    excluded = len(named & exclude)
    out: list[ScopeName] = []
    for ticker in sorted(named - exclude):
        page = page_path(dossiers_dir, ticker) if ticker in pages else None
        if page is not None:
            raw = json.loads(page.read_text()).get("cik")
            if raw:
                out.append(ScopeName(ticker, pad_cik(raw), page, ticker in followed))
                continue
        try:
            out.append(ScopeName(ticker, cik_for_ticker(ticker, cache_dir), page,
                                 ticker in followed))
        except NotInCacheError as exc:
            out.append(ScopeName(ticker, None, page, ticker in followed, unresolved=str(exc)))
    return out, excluded


@dataclass(frozen=True)
class ScreenPopulation:
    """One screen run's screened tickers, with the security each one was as the run's universe
    snapshot held it."""

    run_id: str
    reference_date: date
    universe_as_of: date
    #: every ticker with a candidate row, sorted
    screened: tuple[str, ...]
    #: ticker -> the universe snapshot's securities carrying it (one, unless the data is broken)
    securities: dict[str, list[dict[str, Any]]]

    @property
    def rule(self) -> str:
        return SCREEN_RULE.format(run_id=self.run_id,
                                  universe_as_of=self.universe_as_of.isoformat())


def screen_population(run_id: str, snapshots_dir: Path) -> ScreenPopulation:
    """Run ``run_id``'s population. The committed universe snapshot must be the run's own (its
    ``universe_as_of``): a later one could hold different members, and raises."""
    from vinci.screens.retention import CandidateRow, read_manifest, read_rows
    manifest = read_manifest(run_id, snapshots_dir)
    if manifest is None or manifest.universe_as_of is None:
        raise FactsStoreError(f"screen run {run_id} has no manifest stating its universe_as_of")
    screened = sorted({r.ticker for r in read_rows(run_id, snapshots_dir)
                       if isinstance(r, CandidateRow)})
    if not screened:
        raise FactsStoreError(f"screen run {run_id} retains no candidate rows")
    at = manifest.universe_as_of.isoformat()
    members = [json.loads(line) for line in
               (snapshots_dir / "universe_snapshot.jsonl").read_text().splitlines() if line]
    dates = {m["as_of"] for m in members}
    if dates != {at}:
        raise FactsStoreError(f"data/snapshots/universe_snapshot.jsonl is as of {sorted(dates)}, "
                              f"not run {run_id}'s universe ({at})")
    securities = {s["internal_id"]: s for s in (
        json.loads(line) for line in
        (snapshots_dir / "securities.jsonl").read_text().splitlines() if line)}
    by_ticker: dict[str, list[dict[str, Any]]] = {}
    for m in members:
        if m.get("in_universe") == 1 and (sec := securities.get(m["internal_id"])) is not None:
            by_ticker.setdefault(str(sec["ticker"]), []).append(sec)
    return ScreenPopulation(run_id=run_id, reference_date=manifest.reference_date,
                            universe_as_of=manifest.universe_as_of, screened=tuple(screened),
                            securities=by_ticker)


def screen_scope_names(run_id: str, snapshots_dir: Path) -> tuple[list[ScopeName], str]:
    """Every ticker run ``run_id`` screened, each with its CIK, and the rule, stated with the run's
    own universe date.

    The CIK is the security's as the run's universe snapshot held it, so a ticker that changed
    hands is read for the company the screen screened."""
    pop = screen_population(run_id, snapshots_dir)
    out: list[ScopeName] = []
    for ticker in pop.screened:
        secs = pop.securities.get(ticker, [])
        cik = secs[0].get("cik") if len(secs) == 1 else None
        if not cik:
            why = (f"{len(secs)} universe securities carry ticker {ticker}" if len(secs) != 1
                   else f"security {secs[0]['internal_id']} carries no CIK")
            out.append(ScopeName(ticker, None, None, False, unresolved=why))
        else:
            out.append(ScopeName(ticker, pad_cik(cik), None, False))
    return out, pop.rule
