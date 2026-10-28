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

A RE-DOMICILE IS THE SAME TABLE, ACROSS TWO CIKs (2026-10-28). Expro (XPRO) and Columbia
Financial (CLBK) each re-registered under a new filer with the ticker unchanged, so the resolver
minted ``SEC-<new cik>-<ticker>`` and the old id kept the history: L7 measured each pair abutting,
0 market sessions apart. A row then names the old filer (``predecessor_cik``) and is written only
on proof — the same share-class FIGI under both filers, or the new filer's own succession filing
(an 8-K12B) — never on the shared ticker alone (`detect_successions`).

A REUSED TICKER IS THE OPPOSITE FACT, AND IT IS KEPT APART (`TickerTenure`, 2026-10-28). The
store files a grouped-daily bar under whichever id holds its ticker TODAY, so a former holder's
bars sat under the current one's id: L7 measured ten such holes on the 2026-10-28 scorecard (CALY
held a BlackRock muni ETF's bars, 2023-07-13 → 2024-10-09). That row says the id does NOT continue
what traded before its first session. It is not an alias row, because every reader of this table
treats a row as a continuation, and one misread would splice the other company back in.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from functools import partial
from pathlib import Path
from typing import Any

from vinci.schemas.data_record import Identity

#: the committed, accumulate-only table (one row per renamed share class and step)
ALIASES = "share_class_aliases.jsonl"

#: the committed, accumulate-only table of reused tickers (one row per id whose ticker another
#: filer traded under before it)
TENURES = "ticker_tenure.jsonl"

#: The new filer's own notice that it succeeded to a registered security (Exchange Act Rule
#: 12g-3; Form 8-K, "12B" for a 12(b) security) — the filing both re-domiciles L7 measured made
#: (XPRO 2026-07-13, CLBK 2026-07-21). 8-K12G3, the 12(g) form, is not read: no measured case.
SUCCESSION_FORMS = ("8-K12B", "8-K12B/A")

#: A succession filing is read as THIS line's only within a year before the boundary (the session
#: after the old filer's last stored bar), and only where the successor's first stored bar comes
#: within two weeks of the old filer's last (about the `GAP_SESSIONS` an SEC suspension may run).
#: Face validity, not measured: the two real ones were filed 24 and 16 days before the boundary,
#: and each successor's first stored bar is the session after it. A filing older than that, or a
#: successor that began long after the old history ended, is another event — a reuse.
SUCCESSION_FILED_WITHIN = timedelta(days=365)
SUCCESSION_ABUTS = timedelta(days=14)

#: ``(ticker, as_of or None) -> Polygon ticker-details results, or None when unavailable``
Details = Callable[[str, "date | None"], "Mapping[str, Any] | None"]

#: ``cik -> [(form, filed, accession)]`` — a filer's succession filings (`SUCCESSION_FORMS`)
Filings = Callable[[str], "list[tuple[str, date, str]]"]


@dataclass(frozen=True)
class ShareClassAlias:
    """``successor_id`` continues ``predecessor_id``: one share class, trading under a new ticker
    — or, across a re-domicile, under a new filer (``predecessor_cik``) — from ``listed`` (its
    first session as that line)."""

    predecessor_id: str
    successor_id: str
    cik: str
    share_class_figi: str | None      # the FIGI both records carry; None: an 8-K12B proved it
    predecessor_symbol: str
    successor_symbol: str
    listed: date
    evidence: str
    predecessor_cik: str | None = None   # the old filer, on a re-domicile; None: ``cik``

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["listed"] = self.listed.isoformat()
        return row


@dataclass(frozen=True)
class TickerTenure:
    """``internal_id`` holds ``ticker`` from ``first_session`` on. The bars filed under it before
    then, through ``prior_last``, are another security's (`another_security`), and belong to
    ``prior_id``: the id the resolver gives the other filer's line, ``SEC-<prior_cik>-<ticker>``,
    when Polygon's record names another CIK — otherwise ``PRIOR-<ticker>-<prior_last>``, the
    security that traded as the ticker through that session (another class of the line's own
    filer, or a record naming no filer at all). ``prior_cik`` is the CIK that record names."""

    internal_id: str
    ticker: str
    cik: str
    first_session: date
    prior_id: str
    prior_cik: str | None
    prior_last: date
    evidence: str

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["first_session"] = self.first_session.isoformat()
        row["prior_last"] = self.prior_last.isoformat()
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


def load_tenures(snapshots_dir: Path) -> list[TickerTenure]:
    """Every reused-ticker row the committed table holds. A malformed row raises."""
    path = snapshots_dir / TENURES
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            out.append(TickerTenure(**{**row,
                                       "first_session": date.fromisoformat(row["first_session"]),
                                       "prior_last": date.fromisoformat(row["prior_last"])}))
    return out


def write_tenures(snapshots_dir: Path, tenures: Iterable[TickerTenure]) -> int:
    """Merge ``tenures`` into the table, ACCUMULATE-ONLY as the alias table is: a row once
    written is never dropped or rewritten. Returns the rows added."""
    held = {(t.internal_id, t.first_session): t for t in load_tenures(snapshots_dir)}
    added = 0
    for t in tenures:
        if (t.internal_id, t.first_session) not in held:
            held[(t.internal_id, t.first_session)] = t
            added += 1
    if added:
        rows = sorted(held.values(), key=lambda t: (t.ticker, t.first_session, t.internal_id))
        (snapshots_dir / TENURES).write_text(
            "".join(json.dumps(t.to_row(), sort_keys=True) + "\n" for t in rows))
    return added


def first_sessions(aliases: Iterable[ShareClassAlias],
                   tenures: Iterable[TickerTenure]) -> dict[str, date]:
    """``{internal_id: the first session its OWN bars may be filed from}`` — a reused ticker's
    current holder from its tenure, an alias's successor from its listing; the later where both
    apply. Before it, an id holds only what an alias carries to it (``polygon-alias:<old id>``)."""
    out: dict[str, date] = {}
    for iid, d in ([(a.successor_id, a.listed) for a in aliases]
                   + [(t.internal_id, t.first_session) for t in tenures]):
        out[iid] = max(d, out.get(iid, d))
    return out


#: Polygon's types for an exchange-traded basket (the universe's own non-equity list,
#: `config.py`): a fund under a ticker that an operating line holds today is another security
FUND_TYPES = frozenset({"ETF", "ETN", "ETV", "ETS", "FUND"})

#: the fields of a Polygon record that NAME a security, compared only where both records carry one
_IDENTITY = ("share_class_figi", "composite_figi")


def another_security(before: Mapping[str, Any], line_cik: str,
                     after: Callable[[], Mapping[str, Any] | None]) -> str | None:
    """Why Polygon's record of a ticker ``before`` a hole names a security other than the line
    that trades under it after the hole — or None when it does not say so. ``after`` reads the
    line's own record at its first bar after the hole, and is called only when the CIK alone
    cannot decide."""
    cik = str(before.get("cik") or "")
    if cik and cik != line_cik:
        return f"CIK {cik}, not {line_cik}"
    now = after() or {}
    for key in _IDENTITY:
        if before.get(key) and now.get(key) and before[key] != now[key]:
            return f"{key} {before[key]}, not {now[key]}"
    # the line's own type must be STATED and not a fund: no record, or no type, is unknown
    if before.get("type") in FUND_TYPES and now.get("type") and now["type"] not in FUND_TYPES:
        return f"type {before['type']}, not {now['type']}"
    return None


def load_first_sessions(snapshots_dir: Path) -> dict[str, date]:
    """`first_sessions` from the two committed tables — what every ingest files bars by."""
    return first_sessions(load_aliases(snapshots_dir), load_tenures(snapshots_dir))


def detect_reuse(lines: Iterable[Identity], holes: Mapping[str, list[tuple[date, date]]],
                 details: Details, *, known: Iterable[TickerTenure] = ()
                 ) -> list[TickerTenure]:
    """The lines whose ticker another security traded under before them, among ``lines`` with a
    hole in their stored bars (``holes``: ``{internal_id: [(last bar before, first bar after),
    ...]}``, each a step across more than `GAP_SESSIONS` market sessions, oldest first).

    THE PROOF IS POLYGON'S RECORD OF THE TICKER AS OF THE LAST BAR BEFORE THE HOLE, set beside the
    line's own record at its first bar after it (`another_security`): another filer's CIK (CALY
    held a BlackRock muni ETF's bars), another share-class or composite FIGI under the same filer
    (CORZ's and OPI's equity before their restructurings — Tiingo starts a new series at each), or
    an exchange-traded fund where the line is an operating security (WLTH, whose ETF record names
    no CIK and no FIGI). The line's own first session is then the bar after the hole. Holes are
    read newest first, and the first that proves another security ends the walk; one that does not
    — a hole in one series (BANFP), or a record Polygon cannot serve — moves the walk to an
    earlier one. A dated record never changes, so each costs one call, once (`ticker_details`
    keeps a past date's record for good)."""
    seen = {t.internal_id for t in known}
    out: list[TickerTenure] = []
    for s in lines:
        if s.internal_id in seen:
            continue
        for before, after in reversed(holes.get(s.internal_id, [])):
            rec = details(s.eod_symbol, before)
            why = None if rec is None else another_security(
                rec, s.cik, lambda: details(s.eod_symbol, after))  # noqa: B023 — called at once
            if rec is None or why is None:
                continue
            cik = str(rec.get("cik") or "")
            prior = (f"SEC-{cik}-{s.ticker}" if cik and cik != s.cik
                     else f"PRIOR-{s.ticker}-{before.isoformat()}")
            out.append(TickerTenure(
                internal_id=s.internal_id, ticker=s.eod_symbol, cik=s.cik, first_session=after,
                prior_id=prior, prior_cik=cik or None, prior_last=before,
                evidence=(f"Polygon ticker details: {s.eod_symbol} as of {before.isoformat()} "
                          f"is {rec.get('name') or 'unnamed'} ({rec.get('type') or 'no type'}) — "
                          f"{why}; {s.internal_id}'s bars resume {after.isoformat()}")))
            break
    return out


def detect_successions(lines: Iterable[Identity], master: Iterable[Identity],
                       details: Details, filings: Filings,
                       spans: Callable[[str], tuple[date, date] | None], *, as_of: date,
                       known: Iterable[ShareClassAlias] = ()) -> list[ShareClassAlias]:
    """The re-domiciles among ``lines``: an entity-master id of the SAME ticker and share class
    under ANOTHER CIK, with stored bars (``spans``: first and last held bar, or None).

    THE BOUNDARY (``listed``) IS THE SESSION AFTER THE OLD FILER'S LAST STORED BAR, never the
    line's own first bar (Codex, #839 round 2). The weekly build looks for a succession before the
    screen ingests the new id, which then holds no bar; and that ingest's restate window files the
    ticker's last weeks under it, so its first bar can fall before the old filer's last. One
    ticker trades one series a day, so such an overlap is the same series, not two.

    TWO PROOFS, AND THE TICKER IS NEITHER (brief, 2026-10-28):
    1. the same share-class FIGI — Polygon's record of the line as of ``as_of`` (the build's date,
       never today, as `detect_renames` reads it) and of the ticker as of the day before the
       boundary, where that record still names the OLD filer;
    2. the new filer's own succession filing (`SUCCESSION_FORMS`), filed within
       `SUCCESSION_FILED_WITHIN` before the boundary, the old history ending within
       `SUCCESSION_ABUTS` of it. XPRO carries no FIGI at all, so this is its proof."""
    seen = {(a.predecessor_id, a.successor_id) for a in known}
    by_ticker: dict[str, list[Identity]] = {}
    for m in master:
        by_ticker.setdefault(m.eod_symbol, []).append(m)
    out: list[ShareClassAlias] = []
    for s in lines:
        olds = [p for p in by_ticker.get(s.eod_symbol, ())
                if p.cik != s.cik and p.share_class == s.share_class
                and (p.internal_id, s.internal_id) not in seen]
        if not olds:
            continue
        mine = spans(s.internal_id)
        # the line's FIGI only from a record naming ITS filer: the ticker's record as of the build
        # can be the new filer's while ``s`` is the old line
        now = details(s.eod_symbol, as_of) or {}
        figi = now.get("share_class_figi") if now.get("cik") == s.cik else None
        for p in olds:
            if (theirs := spans(p.internal_id)) is None:
                continue                          # no history to continue
            if mine is not None and mine[1] <= theirs[1]:
                continue                          # a successor's history outruns its predecessor's
            listed = theirs[1] + timedelta(days=1)
            row = partial(ShareClassAlias, predecessor_id=p.internal_id,
                          successor_id=s.internal_id, cik=s.cik, predecessor_symbol=p.eod_symbol,
                          successor_symbol=s.eod_symbol, listed=listed, predecessor_cik=p.cik)
            # with no FIGI on the line the FIGI proof cannot hold, and its record is not asked
            then = (details(p.eod_symbol, listed - timedelta(days=1)) or {}) if figi else {}
            if figi and then.get("cik") == p.cik and then.get("share_class_figi") == figi:
                out.append(row(share_class_figi=str(figi), evidence=(
                    f"Polygon ticker details: {p.eod_symbol} as of "
                    f"{(listed - timedelta(days=1)).isoformat()} (CIK {p.cik}) and "
                    f"{s.eod_symbol} as of {as_of.isoformat()} (CIK {s.cik}) carry "
                    f"share_class_figi {figi}")))
                continue
            if mine is not None and mine[0] - theirs[1] > SUCCESSION_ABUTS:
                continue
            notice = [(form, filed, acc) for form, filed, acc in filings(s.cik)
                      if form in SUCCESSION_FORMS
                      and listed - SUCCESSION_FILED_WITHIN <= filed <= listed]
            if notice:
                form, filed, acc = max(notice, key=lambda f: f[1])
                out.append(row(share_class_figi=None, evidence=(
                    f"SEC {form} {acc} filed {filed.isoformat()} by CIK {s.cik}, the successor "
                    f"to CIK {p.cik} under {s.eod_symbol}; {p.internal_id}'s bars end "
                    f"{theirs[1].isoformat()}, so {s.internal_id} holds the ticker from "
                    f"{listed.isoformat()}")))
    return out


def detect_renames(lines: Iterable[Identity], master: Iterable[Identity],
                   active: Mapping[str, object], details: Details,
                   first_session: Callable[[Identity], date | None], *, as_of: date,
                   known: Iterable[ShareClassAlias] = ()) -> list[ShareClassAlias]:
    """The renames among ``lines``: for each line, an entity-master id of the SAME CIK and share
    class whose ticker is no longer ``active`` (absent from today's reference pull), confirmed by
    equal share-class FIGIs — the line's as of ``as_of`` (the build's date, never today: a
    replayed build must not be swayed by what the source says later — Codex, #833), the old
    ticker's as of the day before the line's ``first_session`` under its own ticker. Only an
    inactive sibling is a candidate, so an issuer's other live classes cost no call; an alias
    already ``known`` costs none either.

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
        now = details(s.eod_symbol, as_of)
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


def heirs(aliases: Iterable[ShareClassAlias], incumbents: Iterable[str]) -> set[str]:
    """Every id that continues an incumbent through ANY number of renames (A → B → C makes C the
    heir of an incumbent A even when B never sat in a population)."""
    held = set(incumbents)
    return {succ for succ, chain in predecessors(aliases).items()
            if any(a.predecessor_id in held for a in chain)}


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
