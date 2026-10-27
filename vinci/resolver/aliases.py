"""One share class, two tickers — the alias table that carries a renamed line's record forward.

A RENAME MINTS A NEW INTERNAL ID. `EntityResolver` keys a security as ``SEC-<cik>-<ticker>``, so
when Helix Energy Solutions became Hornbeck Offshore Services (HLX → HOS, CIK 866829, listed as
HOS on 2026-09-02) the population gained SEC-0000866829-HOS with no price history and lost
SEC-0000866829-HLX with all of it. The 2026-09-22 screen judged HOS on "only 20d history" and
could not evaluate it. Measured across eight Polygon reference pulls (2026-07-13 → 10-17), 49 share
classes changed ticker, and 10 of them touch a committed primary population.

THE KEY IS THE SHARE CLASS, NOT THE TICKER: CIK + Polygon's ``share_class_figi``. A FIGI is issued
to the share class and survives a ticker change — HLX on 2026-08-01 and HOS today both read
BBG001S978V8 — and Polygon's ticker details answer AS OF A DATE, so the old ticker's FIGI can be
read after it is gone. Two lines are one class only when both FIGIs are present and equal; a line
with no FIGI (PLGO carries none) is never aliased, because a guess here would splice two
companies' returns into one record.

EXISTING IDS ARE NEVER RE-KEYED. The ledger is append-only and the dossiers key on internal ids,
so the old id stays exactly as it was; the table only records that the new id CONTINUES it.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from vinci.schemas.data_record import Identity

#: the committed, accumulate-only table (one row per renamed share class and step)
ALIASES = "share_class_aliases.jsonl"

#: ``(ticker, as_of or None) -> Polygon ticker-details results, or None when unavailable``
Details = Callable[[str, "date | None"], "Mapping[str, Any] | None"]


@dataclass(frozen=True)
class ShareClassAlias:
    """``successor_id`` continues ``predecessor_id``: the same CIK and share-class FIGI, trading
    under a new ticker from ``listed`` (its first session as that ticker)."""

    predecessor_id: str
    successor_id: str
    cik: str
    share_class_figi: str
    predecessor_symbol: str
    successor_symbol: str
    listed: date
    evidence: str

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["listed"] = self.listed.isoformat()
        return row


def load_aliases(snapshots_dir: Path) -> list[ShareClassAlias]:
    """Every alias the committed table holds. A malformed row raises."""
    path = snapshots_dir / ALIASES
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            out.append(ShareClassAlias(**{**row, "listed": date.fromisoformat(row["listed"])}))
    return out


def write_aliases(snapshots_dir: Path, aliases: Iterable[ShareClassAlias]) -> int:
    """Merge ``aliases`` into the table, ACCUMULATE-ONLY: a row once written is never dropped or
    rewritten, so a successor's history can always be traced to its predecessor. Returns the
    number of rows added."""
    held = {(a.predecessor_id, a.successor_id): a for a in load_aliases(snapshots_dir)}
    added = 0
    for a in aliases:
        if (a.predecessor_id, a.successor_id) not in held:
            held[(a.predecessor_id, a.successor_id)] = a
            added += 1
    if added:
        rows = sorted(held.values(), key=lambda a: (a.cik, a.listed, a.successor_id))
        (snapshots_dir / ALIASES).write_text(
            "".join(json.dumps(a.to_row(), sort_keys=True) + "\n" for a in rows))
    return added


def detect_renames(lines: Iterable[Identity], master: Iterable[Identity],
                   active: Mapping[str, object], details: Details,
                   first_session: Callable[[Identity], date | None],
                   known: Iterable[ShareClassAlias] = ()) -> list[ShareClassAlias]:
    """The renames among ``lines``: for each line, an entity-master id of the SAME CIK and share
    class whose ticker is no longer ``active`` (absent from today's reference pull), confirmed by
    equal share-class FIGIs — the line's today, the old ticker's as of the day before the line's
    ``first_session`` under its own ticker. Only an inactive sibling is a candidate, so an issuer's
    other live classes cost no call; an alias already ``known`` costs none either.

    THE BOUNDARY IS THE NEW TICKER'S FIRST SESSION, NEVER ``list_date``. Polygon's ``list_date``
    is the share class's listing: HOS reads 2026-09-02, the rename, but SVIA reads 2025-12-08, the
    day the class listed as BRR — reading BRR "as of 2025-12-07" asks for a ticker that did not
    exist yet. The first bar the source serves under the new symbol is the day it started trading
    as that symbol (HOS: 2026-09-02; HLX's last: 2026-09-01)."""
    seen = {(a.predecessor_id, a.successor_id) for a in known}
    by_cik: dict[str, list[Identity]] = {}
    for m in master:
        by_cik.setdefault(m.cik, []).append(m)
    out: list[ShareClassAlias] = []
    for s in lines:
        olds = [p for p in by_cik.get(s.cik, ())
                if p.internal_id != s.internal_id and p.share_class == s.share_class
                and p.eod_symbol not in active
                and (p.internal_id, s.internal_id) not in seen]
        if not olds:
            continue
        now = details(s.eod_symbol, None)
        figi = (now or {}).get("share_class_figi")
        if not figi or (on := first_session(s)) is None:
            continue
        for p in olds:
            then = details(p.eod_symbol, on - timedelta(days=1))
            if (then or {}).get("share_class_figi") == figi and (then or {}).get("cik") == s.cik:
                out.append(ShareClassAlias(
                    predecessor_id=p.internal_id, successor_id=s.internal_id, cik=s.cik,
                    share_class_figi=str(figi), predecessor_symbol=p.eod_symbol,
                    successor_symbol=s.eod_symbol, listed=on,
                    evidence=(f"Polygon ticker details: {p.eod_symbol} as of "
                              f"{(on - timedelta(days=1)).isoformat()} and {s.eod_symbol} (first "
                              f"session {on.isoformat()}) carry share_class_figi {figi}")))
    return out


def predecessors(aliases: Iterable[ShareClassAlias]) -> dict[str, list[ShareClassAlias]]:
    """``{successor_id: [its aliases, oldest first]}`` — every step back, so a line renamed twice
    reaches both its predecessors."""
    back: dict[str, ShareClassAlias] = {}
    for a in aliases:
        back[a.successor_id] = a
    out: dict[str, list[ShareClassAlias]] = {}
    for succ in back:
        chain: list[ShareClassAlias] = []
        cur = succ
        while cur in back and len(chain) < len(back):
            chain.append(back[cur])
            cur = back[cur].predecessor_id
        out[succ] = list(reversed(chain))
    return out
