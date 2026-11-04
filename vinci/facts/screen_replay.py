"""SHADOW REPLAY OF THE SCREEN: its EDGAR inputs from the fact store, against what its code reads.

For one name, everything the screen reads from EDGAR is one call (``vinci.screens.assemble.
enrich_with_fundamentals``): ``edgar.fundamental_snapshot_and_facts(cik, as_of=cut)``, which
answers with the fundamentals snapshot computed at ``cut`` and the companyfacts it came from, and
``cut`` is the run's price date for that name (``frontier`` of its bars, its newest close on or
before the reference date; ``vinci.edgar.asof.page_price_date`` semantics, as #884 cut them). Each
retained candidate row stamps that close (``gate_inputs.last``), so the cut is read off the run's
own record, never re-derived.

Both sides run the SCREEN'S OWN CODE on the same name, the same cut and the same close:
- REFERENCE: the cached companyfacts response, handed over whole as ``EdgarClient`` hands it (the
  screen cuts it itself);
- STORE: ``FactStore.companyfacts_as_of(entity, cut)``.

Compared, field by field, as each side's model dumps them: every field of the record's
``Fundamentals`` (P/E and its percentile, both signs, both leverages, the share-count change, the
deferred EV/EBITDA pair), every field of the fundamentals snapshot (with the three the record does
not carry: EBITDA, net debt, annual diluted EPS), and the annual diluted EPS series the P/E
percentile is computed over, point by point. The rows themselves are compared too
(:func:`vinci.facts.parity.compare_rows`), so a difference that no field happens to read still
shows.

THE CLOSE IS THE RUN'S OWN, CARRIED TO THE CUT. One bar, the row's ``last`` close dated at the
cut, gives the record a frontier equal to the cut and a P/E LEVEL that is the same close over each
side's EPS. It is never stored or shown as a price; the percentile needs the run's full bar history
and so is UNKNOWN on both sides here, its EDGAR input (the EPS series) compared in full instead.

THE POPULATION IS THE SNAPSHOT'S. Every name the screen snapshot's manifest holds or names as
unread, and nothing else: a name excluded by operator instruction is in neither, so it is never
read here and never printed. NOTHING IS SWITCHED: the screen still reads EDGAR (slice 2b).
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, cast

from vinci.edgar.asof import page_price_date
from vinci.edgar.client import EdgarClient, FundamentalSnapshot, compute_fundamental_snapshot
from vinci.edgar.concepts import REPORTING, extract_points, facts_as_of
from vinci.facts.edgar_ingest import NotInCacheError, pad_cik, read_cached_companyfacts
from vinci.facts.parity import compare_rows, filing_eve
from vinci.facts.reader import FactStore, FactUnknownError
from vinci.facts.scope import ScreenPopulation, screen_population
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import build_price_record, enrich_with_fundamentals

#: How stale a close may be before the record marks it so. The replay compares no price feature,
#: so this only has to be a number build_price_record accepts.
_STALENESS_DAYS = 7


class _OneResponseEdgar:
    """The one EDGAR call the screen makes, answered from one companyfacts blob exactly as
    ``EdgarClient.fundamental_snapshot_and_facts`` answers it from a response it has read."""

    def __init__(self, blob: dict[str, Any]) -> None:
        self.blob = blob
        #: the snapshot it answered with, so the replay compares the one the screen computed
        self.answered: FundamentalSnapshot | None = None

    def fundamental_snapshot_and_facts(self, cik: int | str, *, as_of: date | None = None
                                       ) -> tuple[FundamentalSnapshot, dict[str, Any]]:
        self.answered = compute_fundamental_snapshot(pad_cik(cik), self.blob, as_of=as_of)
        return self.answered, self.blob


def screen_inputs(identity: Identity, blob: dict[str, Any], *, cut: date, close: float,
                  reference_date: date) -> dict[str, Any]:
    """Everything the screen reads from ``blob`` for one name at ``cut``, as JSON values."""
    bar = PriceBar(internal_id=identity.internal_id, bar_date=cut, open=close, high=close,
                   low=close, close=close, volume=0.0, source="replay: the run's last close")
    rec = build_price_record(identity, price_bars=[bar], benchmark_bars=[],
                             reference_date=reference_date, staleness_days=_STALENESS_DAYS)
    edgar = _OneResponseEdgar(blob)
    full = enrich_with_fundamentals(rec, edgar=cast(EdgarClient, edgar),
                                    price_bars=[bar], reference_date=reference_date)
    out: dict[str, Any] = {f"fundamentals.{k}": v
                           for k, v in full.fundamentals.model_dump(mode="json").items()}
    snap = edgar.answered
    if snap is None:
        raise RuntimeError("enrich_with_fundamentals made no EDGAR call")
    out.update({f"snapshot.{k}": v for k, v in snap.model_dump(mode="json").items()})
    facts = facts_as_of(blob, cut) if blob else {}
    out["annual_eps"] = [p.model_dump(mode="json") for p in (
        extract_points(facts, "eps_diluted", currency=REPORTING, as_of=reference_date)
        if facts else []) if p.is_annual]
    return out


@dataclass
class NameReplay:
    ticker: str
    entity: str | None
    cut_kind: str                 # 'price date' or 'filing eve'
    cut: str | None
    reached_g3: bool
    fetched_at: str = ""
    rows_compared: int = 0
    store_rows: int = 0
    row_diffs: int = 0
    order_diffs: int = 0
    fields_compared: int = 0
    #: every field whose two sides differ: {field, reference, store}
    mismatches: list[dict[str, Any]] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    #: why this name could not be compared; such a name is never zero-diff
    unread: str | None = None

    @property
    def zero_diff(self) -> bool:
        return (self.unread is None and not self.mismatches and self.row_diffs == 0
                and self.order_diffs == 0 and self.rows_compared == self.store_rows)


@dataclass
class ReplayResult:
    run_id: str
    reference_date: str
    snapshot_id: str
    names: list[NameReplay]
    #: the tickers the snapshot's manifest names as unread; any OTHER unread name is a failure
    declared_unread: frozenset[str] = frozenset()

    def as_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "reference_date": self.reference_date,
                "snapshot_id": self.snapshot_id, "declared_unread": sorted(self.declared_unread),
                "names": [asdict(n) for n in self.names]}


def _identity(sec: dict[str, Any]) -> Identity:
    return Identity.model_validate({k: sec[k] for k in Identity.model_fields if k in sec})


def _compare(n: NameReplay, ref: dict[str, Any], got: dict[str, Any]) -> None:
    n.fields_compared = len(set(ref) | set(got))
    for k in sorted(set(ref) | set(got)):
        if ref.get(k) != got.get(k):
            n.mismatches.append({"field": k, "reference": ref.get(k), "store": got.get(k)})


def replay_name(pop: ScreenPopulation, row: Any, store: FactStore, cache_dir: Path, *,
                eve: bool) -> list[NameReplay]:
    """``row``'s name at the run's price date, and (``eve``) at the eve of its last filing day."""
    ticker = row.ticker
    reached = "g3_multiple_floor" in row.per_gate
    secs = pop.securities.get(ticker, [])
    kinds = ["price date", *(["filing eve"] if eve else [])]
    if len(secs) != 1 or not secs[0].get("cik"):
        why = f"{len(secs)} universe securities carry ticker {ticker}" if len(secs) != 1 \
            else "the security carries no CIK"
        return [NameReplay(ticker, None, k, None, reached, unread=why) for k in kinds]
    identity = _identity(secs[0])
    entity = pad_cik(identity.cik)
    # THE SECURITIES SNAPSHOT IS READ AS IT IS NOW and nothing dates it (round 2 of #904): a ticker
    # it maps to another CIK than the snapshot ingested would be replayed against another company
    held = next((e["entity"] for e in store.manifest["entities"] if ticker in e["tickers"]), None)
    if held is not None and held != entity:
        return [NameReplay(ticker, entity, k, None, reached,
                           unread=(f"securities.jsonl maps {ticker} to {entity}, not the CIK "
                                   f"snapshot {store.snapshot_id} ingested ({held})"))
                for k in kinds]
    last = row.gate_inputs.get("last")
    if last is None or last.value is None or last.as_of is None:
        return [NameReplay(ticker, entity, k, None, reached,
                           unread="the run's row stamps no last close") for k in kinds]
    price_date = page_price_date(last.as_of, pop.reference_date)
    try:
        resp = read_cached_companyfacts(entity, cache_dir)
    except NotInCacheError as exc:
        return [NameReplay(ticker, entity, k, price_date.isoformat(), reached, unread=str(exc))
                for k in kinds]
    # THE REFERENCE MUST BE THE RESPONSE THE SNAPSHOT INGESTED (round 1 of #904): the cache is read
    # as it is now, and a copy refetched since the ingest would be compared as if it were the same
    ingested = next((e for e in store.manifest["entities"] if e["entity"] == entity), None)
    if ingested is not None and ingested["response_sha256"] != resp.sha256:
        return [NameReplay(ticker, entity, k, price_date.isoformat(), reached,
                           fetched_at=resp.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                           unread=(f"the SEC cache now holds not the response snapshot "
                                   f"{store.snapshot_id} ingested (fetched "
                                   f"{ingested['fetched_at']}, sha256 "
                                   f"{ingested['response_sha256'][:12]}…)")) for k in kinds]
    full = json.loads(resp.text)
    out: list[NameReplay] = []
    for kind in kinds:
        cut = price_date if kind == "price date" else filing_eve(full, price_date)
        n = NameReplay(ticker, entity, kind, cut.isoformat() if cut else None, reached,
                       fetched_at=resp.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
        out.append(n)
        if cut is None:
            n.unread = f"nothing filed by {price_date}: no filing eve"
            continue
        try:
            stored = store.companyfacts_as_of(entity, cut)
        except FactUnknownError as exc:
            n.unread = str(exc)
            continue
        rows = compare_rows(facts_as_of(full, cut), stored, n.examples)
        n.row_diffs, n.order_diffs, n.rows_compared, n.store_rows = rows
        close = float(last.value)
        _compare(n, screen_inputs(identity, full, cut=cut, close=close,
                                  reference_date=pop.reference_date),
                 screen_inputs(identity, stored, cut=cut, close=close,
                               reference_date=pop.reference_date))
    return out


def replay_run(run_id: str, snapshots_dir: Path, store: FactStore, cache_dir: Path, *,
               eve: bool = False) -> ReplayResult:
    """Every name the screen snapshot holds or names as unread, at the run's price date."""
    from vinci.screens.retention import CandidateRow, read_rows
    if store.manifest["name"] != "screen":
        raise ValueError(f"snapshot {store.snapshot_id} is the {store.manifest['name']!r} "
                         "snapshot, not the screen's")
    pop = screen_population(run_id, snapshots_dir)
    scope = store.manifest["scope"]
    if pop.rule != scope["rule"]:
        raise ValueError(f"snapshot {store.snapshot_id} was ingested for {scope['rule']!r}, "
                         f"not run {run_id}")
    declared = frozenset(str(u["ticker"]) for u in scope["unread"])
    population = {t for e in store.manifest["entities"] for t in e["tickers"]} | declared
    rows = [r for r in read_rows(run_id, snapshots_dir)
            if isinstance(r, CandidateRow) and r.ticker in population]
    want = scope["names_selected"] - scope["excluded_by_operator_instruction"]
    if len(rows) != want or len(population) != want:
        raise ValueError(f"run {run_id} holds {len(rows)} rows of the snapshot's {len(population)} "
                         f"names; its manifest selected {want}")
    names = [n for r in rows for n in replay_name(pop, r, store, cache_dir, eve=eve)]
    return ReplayResult(run_id=run_id, reference_date=pop.reference_date.isoformat(),
                        snapshot_id=store.snapshot_id, names=names, declared_unread=declared)


def _short(v: Any, width: int = 160) -> str:
    text = json.dumps(v, sort_keys=True, default=str)
    return text if len(text) <= width else text[:width] + f"… ({len(text):,} chars)"


def print_replay(result: ReplayResult, *, shown: int = 20) -> list[NameReplay]:
    """The replay's table, per cut and for the names that reached G3; returns every name-cut that
    failed: one with a difference, or one unread that the snapshot does not itself name unread."""
    print(f"screen run {result.run_id} (reference {result.reference_date}), snapshot "
          f"{result.snapshot_id}")
    head = ("cut", "names", "of them reached G3", "unread", "rows compared", "store rows",
            "row diffs", "order diffs", "fields compared", "field mismatches",
            "names with a diff")
    print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
    for kind in sorted({n.cut_kind for n in result.names}, reverse=True):
        for label, sel in (("all", lambda n: True), ("reached G3", lambda n: n.reached_g3)):
            ns = [n for n in result.names if n.cut_kind == kind and sel(n)]
            cells = (f"{kind} ({label})", len(ns), sum(n.reached_g3 for n in ns),
                     sum(n.unread is not None for n in ns), f"{sum(n.rows_compared for n in ns):,}",
                     f"{sum(n.store_rows for n in ns):,}", sum(n.row_diffs for n in ns),
                     sum(n.order_diffs for n in ns), f"{sum(n.fields_compared for n in ns):,}",
                     sum(len(n.mismatches) for n in ns),
                     sum(1 for n in ns if n.unread is None and not n.zero_diff))
            print("| " + " | ".join(str(c) for c in cells) + " |")
    differ = [n for n in result.names if n.unread is None and not n.zero_diff]
    lines = [f"{n.ticker} {n.cut_kind} {n.cut}: {m['field']}: reference {_short(m['reference'])}"
             f" | store {_short(m['store'])}" for n in differ for m in n.mismatches]
    lines += [f"{n.ticker} {n.cut_kind} {n.cut}: {e} ({len(n.examples)} example line(s) for "
              f"{n.row_diffs:,} differing row(s) and {n.order_diffs:,} list(s) out of order)"
              for n in differ for e in n.examples]
    print(f"\nmismatches: showing {min(shown, len(lines))} of {len(lines)}")
    for line in lines[:shown]:
        print(f"  {line}")
    unread = [n for n in result.names if n.unread is not None]
    reasons = Counter((n.unread or "").split(":")[0] for n in unread)
    print(f"unread: {len(unread)} name-cuts, by reason: {dict(reasons)}")
    undeclared = [n for n in unread if n.ticker not in result.declared_unread]
    print(f"unread that the snapshot does not name unread: showing {min(shown, len(undeclared))} "
          f"of {len(undeclared)}")
    for n in undeclared[:shown]:
        print(f"  {n.ticker} {n.cut_kind}: {n.unread}")
    return differ + undeclared
