"""The ACCOUNT REGISTRY — one directory per X account, so a second voice is data, not a rewrite.

LAYOUT. Everything about one account lives under ``data/calls/<handle>/``::

    data/calls/accounts.json              the index (DERIVED — rebuilt, never hand-edited)
    data/calls/<handle>/meta.json         handle, date span, counts, priced tickers
                        days.json         per-day post/ticker/label counts (the calendar)
                        posts/YYYY-MM.json  the posts themselves, one file per month
                        labels.json        {"<tweet_id>|<TICKER>": {...}} machine + hand
                        gold_labels.jsonl  the hand labels, in the pipeline's own export shape
                        tickers.json       per-ticker mention span + Polygon fetch window
                        bars/<TICKER>.json fetched daily OHLCV (see vinci.calls.bars)

Adding an account is dropping a directory and re-running the rebuild: no route, view, scorer or
schema changes, because nothing below this module names a handle. The registry is DERIVED from each
account's own ``meta.json``, so the index cannot drift from the corpus it describes — the same
reason ``frontend/snapshots/manifest.json`` is regenerated rather than maintained.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

CALLS_DIR = Path("data/calls")
ACCOUNTS_JSON = "accounts.json"


class Account(BaseModel, frozen=True):
    """One X account's corpus, summarised. Every field is read from its own ``meta.json``."""

    handle: str
    display: str
    first: str
    last: str
    n_posts: int
    n_days: int
    #: distinct cashtags the account has ever mentioned — NOT the tracked set (see n_tracked)
    n_cashtags: int
    #: tickers carrying a Polygon fetch window, i.e. the ones a chart can be drawn for
    n_tracked: int
    n_hand_labels: int
    n_machine_labels: int


class AccountIndex(BaseModel, frozen=True):
    """``accounts.json`` — the list plus which handle opens by default."""

    default: str
    accounts: list[Account]

    def get(self, handle: str | None) -> Account:
        """The named account, or the default when ``handle`` is None. Fail loud if unknown."""
        want = handle or self.default
        for a in self.accounts:
            if a.handle == want:
                return a
        known = ", ".join(a.handle for a in self.accounts) or "(none)"
        raise KeyError(f"no calls account {want!r} under {CALLS_DIR}/ — known: {known}")


def account_dir(handle: str, *, root: Path = CALLS_DIR) -> Path:
    return root / handle


def load_accounts(*, root: Path = CALLS_DIR) -> AccountIndex:
    p = root / ACCOUNTS_JSON
    if not p.is_file():
        raise FileNotFoundError(f"{p} missing — run `vinci calls rebuild-accounts`")
    return AccountIndex.model_validate_json(p.read_text())


def rebuild_accounts(*, root: Path = CALLS_DIR, default: str | None = None) -> AccountIndex:
    """Regenerate ``accounts.json`` from every ``<handle>/meta.json`` present. Idempotent."""
    accounts: list[Account] = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        meta_p = d / "meta.json"
        if not meta_p.is_file():
            continue
        m = json.loads(meta_p.read_text())
        tickers_p = d / "tickers.json"
        tracked = len(json.loads(tickers_p.read_text())["tickers"]) if tickers_p.is_file() else 0
        accounts.append(Account(
            handle=m["handle"], display=f"@{m['handle']}",
            first=m["first"], last=m["last"],
            n_posts=m["n_posts"], n_days=m["n_days"],
            n_cashtags=len(m.get("tickers", [])), n_tracked=tracked,
            n_hand_labels=m["n_hand_labels"], n_machine_labels=m["n_machine_labels"],
        ))
    if not accounts:
        raise FileNotFoundError(f"no account directories with a meta.json under {root}/")
    # THE DEFAULT IS THE ONE THING HERE THAT IS NOT DERIVED — it is a choice, so a rebuild must not
    # silently overwrite it. Without this, dropping in a second account whose handle sorts first
    # moved the dashboard's opening account on the next `vinci calls accounts`, with nothing said.
    prev: str | None = None
    idx_p = root / ACCOUNTS_JSON
    if idx_p.is_file():
        try:
            prev = json.loads(idx_p.read_text()).get("default")
        except (OSError, ValueError):
            prev = None
    handles = {a.handle for a in accounts}
    keep = prev if prev in handles else None
    idx = AccountIndex(default=default or keep or accounts[0].handle, accounts=accounts)
    (root / ACCOUNTS_JSON).write_text(idx.model_dump_json(indent=2) + "\n")
    return idx
