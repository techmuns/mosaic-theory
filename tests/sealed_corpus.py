"""Test support: how many LIVE underwrite records the seal manifest holds.

A walk of `scenarios/*.json` that asserts it saw "the committed records" needs a count that does not
come from the same walk. The seal manifest is that count: every live record is sealed under its
ticker and every archived one under its archive key (`TICKER-YYYY-MM-DD`), and archiving a record
renames its key. So a pin that compares its walk with this number moves when a record is archived
only through the seal entry the archive already rewrites, never by hand (W27: MVST's retirement,
#1044, edited eight such counts)."""
from __future__ import annotations

import re
from pathlib import Path

from vinci import seal

_ARCHIVE_KEY = re.compile(r".+-\d{4}-\d{2}-\d{2}")


def live_sealed(root: Path) -> set[str]:
    """The seal manifest's keys that name a live record (a ticker, not an archive key).

    NEVER EMPTY: the walks that compare with this replaced a `seen >= 7` floor, and an absent
    manifest reads as {} — so an empty set would let an empty walk pass as "the corpus"."""
    live = {k for k in seal.load_manifest(root) if not _ARCHIVE_KEY.fullmatch(k)}
    assert live, f"no live record in the seal manifest under {root} — the corpus walk is vacuous"
    return live
