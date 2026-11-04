"""Which companies an ingest reads: the committed pages' (``pages``) or the screen's (``screen``).

``pages``: every company with a committed page, plus the followed names. ``screen``: every company
in one screen run's universe, the population its gates ran over (``data/snapshots/screen_runs``).

The rule is stated in the manifest beside the result, with every name the rule named but the ingest
could not read and why, so a count never stands without its population (CLAUDE.md, EVERY COUNT
STATES ITS BOUNDARY). A name excluded by an operator instruction is counted there and never named.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from vinci.facts.edgar_ingest import NotInCacheError, cik_for_ticker, pad_cik
from vinci.facts.store import (
    FactsStoreError,
    manifest_path,
    pointer_key,
    read_pointers,
)
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


def _prior_scope(base: Path | None, key: str, snapshot_id: str) -> dict[str, Any]:
    """The scope a current snapshot was written with, read raw: a manifest of an older version
    still states its exclusions, and an unreadable one refuses rather than passing the check."""
    path = manifest_path(snapshot_id, base)
    if not path.exists():
        raise FactsStoreError(f"current.json names {snapshot_id} for {key!r}; {path} is missing")
    scope = json.loads(path.read_text()).get("scope")
    return scope if isinstance(scope, dict) else {}


def require_exclusions(excluded: int, *, listed: int, source: str, name: str,
                       base: Path | None = None) -> None:
    """Refuse a run that excludes FEWER names than a current snapshot did.

    The exclusion is a command-line flag, so a run that forgets it would select a held name and put
    its ticker and CIK into a manifest that is public and permanent (review round 2 of #896). Two
    counts are checked, before anything is read or written, and the refusal names COUNTS, never a
    name:
    - ``listed``, how many names the run was told to exclude, against EVERY current snapshot of the
      source: the operator's list does not depend on the scope, so a scope's FIRST snapshot is
      held to it too (slice 2a; a per-scope count alone has nothing to compare a first run to);
    - ``excluded``, how many of them this scope selected, against the current snapshot of the same
      name."""
    pointers = read_pointers(base)
    own = pointer_key(source, name)
    for key, snapshot_id in sorted(pointers.items()):
        if key != source and not key.startswith(f"{source}:"):
            continue
        scope = _prior_scope(base, key, snapshot_id)
        in_scope = scope.get("excluded_by_operator_instruction")
        # a manifest written before `exclusions_listed` existed states only the in-scope count,
        # which the list was at least as long as
        prior_listed = scope.get("exclusions_listed", in_scope)
        if not isinstance(in_scope, int) or not isinstance(prior_listed, int):
            # never read an absent count as zero: that is exactly the run this guard exists to stop
            raise FactsStoreError(
                f"the current snapshot {snapshot_id} ({key!r}) states no exclusion count "
                "(scope.excluded_by_operator_instruction), so this run cannot be checked "
                "against it")
        if listed < prior_listed:
            raise FactsStoreError(
                f"this run was told to exclude {listed} name(s) by operator instruction; the "
                f"current snapshot {snapshot_id} ({key!r}) was written excluding {prior_listed}. "
                "Writing it could publish a held name in a permanent manifest: pass every "
                "--exclude the current snapshots were written with")
        if key == own and excluded < in_scope:
            raise FactsStoreError(
                f"this run excludes {excluded} name(s) by operator instruction; the current "
                f"snapshot {snapshot_id} excludes {in_scope}. Writing it would publish a held "
                "name in a permanent manifest: pass every --exclude it was written with")


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


def screen_scope_names(run_id: str, snapshots_dir: Path, *,
                       exclude: frozenset[str] = frozenset()) -> tuple[list[ScopeName], int, str]:
    """Every ticker run ``run_id`` screened, minus ``exclude``, each with its CIK; how many the
    exclusion removed; and the rule, stated with the run's own universe date.

    The CIK is the security's as the run's universe snapshot held it, so a ticker that changed
    hands is read for the company the screen screened."""
    pop = screen_population(run_id, snapshots_dir)
    excluded = len(set(pop.screened) & exclude)
    out: list[ScopeName] = []
    for ticker in pop.screened:
        if ticker in exclude:
            continue
        secs = pop.securities.get(ticker, [])
        cik = secs[0].get("cik") if len(secs) == 1 else None
        if not cik:
            why = (f"{len(secs)} universe securities carry ticker {ticker}" if len(secs) != 1
                   else f"security {secs[0]['internal_id']} carries no CIK")
            out.append(ScopeName(ticker, None, None, False, unresolved=why))
        else:
            out.append(ScopeName(ticker, pad_cik(cik), None, False))
    return out, excluded, pop.rule
