"""Which companies slice 1 ingests: those with a committed page, plus the followed names.

The rule is stated in the manifest beside the result, with every name the rule named but the ingest
could not read and why, so a count never stands without its population (CLAUDE.md, EVERY COUNT
STATES ITS BOUNDARY). A name excluded by an operator instruction is counted there and never named.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from vinci.facts.edgar_ingest import NotInCacheError, cik_for_ticker, pad_cik
from vinci.followed import follow_records

RULE = "committed pages (data/dossiers/*/dossier.json) plus followed names (data/followed.json)"


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
