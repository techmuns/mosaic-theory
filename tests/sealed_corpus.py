"""Test support: the LIVE underwrite records a walk of `scenarios/*.json` must see.

A walk that asserts it saw "the committed records" needs a count that does not come from the same
walk. For a SEALED record that count is the seal manifest: a record at a decided status is sealed
under its ticker, an archived one under its archive key (`TICKER-YYYY-MM-DD`), and archiving a
record renames its key. So a sealed record the walk drops is still named by the manifest, and the
pin goes red; and a retirement moves the count only through the seal entry the archive already
rewrites, never by hand (W27: MVST's retirement, #1044, edited eight such counts).

A record at an UNSEALED status (`seal.UNSEALED_STATUSES`: `pending_analyst`, the status the
machine writes on a name's next underwrite) is live and, by design, has no seal entry. It is
counted apart, from the records themselves, so a pending record reddens nothing — and a dropped
pending record is not caught here, as no count caught it before (review of #1092, R1)."""
from __future__ import annotations

import json
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


def live_pending(root: Path) -> set[str]:
    """The live records at an unsealed status, by file stem, read from the records themselves."""
    out = set()
    for p in sorted((root / "scenarios").glob("*.json")):
        if p.stem.startswith("_"):
            continue
        status = (json.loads(p.read_text()).get("verdict") or {}).get("status")
        if not seal.is_sealed(status):
            out.add(p.stem)
    return out


def live_records(root: Path) -> set[str]:
    """Every live record a walk must see: the sealed ones the manifest names, plus the pending
    ones counted apart."""
    return live_sealed(root) | live_pending(root)
