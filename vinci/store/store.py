"""The local SQLite store + durable snapshot persistence.

The SQLite DB is the *working* store and is never committed; durable, auditable provenance lives
in ``data/snapshots/`` as deterministic JSONL (one row per line, ordered by primary key → clean
git diffs). ``export_snapshots`` writes them; ``rebuild_from_snapshots`` reconstructs the DB. Bulk
price series are intentionally *not* snapshotted (large + re-pullable from Polygon); decisions,
the entity master, universe membership, and as-reported fundamentals are.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from vinci.schemas.candidate import CandidateRecord
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import CoverageStatus, DataField, SourceTier
from vinci.schemas.ledger import LedgerEntry
from vinci.schemas.market import PriceBar
from vinci.store.schema import DDL, SCHEMA_VERSION, SNAPSHOT_TABLES


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d is not None else None


# Snapshot tables that may never DROP a committed row: decision_ledger (append-only — INSERT-only,
# immutable) AND the securities/issuers ENTITY MASTER (accumulate-only — rows update via REPLACE but
# identities are never pruned; the master resolves a ledgered name after it leaves the universe).
# #121: a stale-DB full export shrank BOTH the ledger (1→0) and the entity master (−578 identities).
_NO_ROW_DROP_TABLES: frozenset[str] = frozenset({"decision_ledger", "securities", "issuers"})


def _assert_no_row_drop(path: Path, new_lines: list[str], pk: Sequence[str]) -> None:
    """Refuse (raise) if ``new_lines`` would drop any row already in ``path`` (compared by primary
    key ``pk``) or is shorter — these snapshots may only GROW. A silent shrink (e.g. a stale-DB
    ``export_snapshots``, the 2026-07-13 near-miss took decision_ledger.jsonl 1→0 and would have
    dropped 578 entity-master identities) must FAIL LOUD, never overwrite the committed record."""
    existing = [ln for ln in path.read_text().splitlines() if ln.strip()]
    if not existing:
        return

    def keyset(lines: list[str]) -> set[tuple[Any, ...]]:
        return {tuple(json.loads(ln)[c] for c in pk) for ln in lines if ln.strip()}

    dropped = keyset(existing) - keyset(new_lines)
    if len(new_lines) < len(existing) or dropped:
        raise RuntimeError(
            f"ROW-DROP on {path.name}: writing {len(new_lines)} row(s) over {len(existing)} "
            f"on disk would drop {len(dropped)} existing row(s) by PK. This snapshot may only grow "
            "(append-only ledger / accumulate-only entity master); a shrink is never valid.")


class Store:
    """Typed data-access layer over SQLite. Open via the constructor or :meth:`open`."""

    def __init__(self, db_path: Path | str) -> None:
        self._path = str(db_path)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self.init_schema()

    @classmethod
    def open(cls, db_path: Path | str) -> Store:
        return cls(db_path)

    def init_schema(self) -> None:
        self._conn.executescript(DDL)
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- entity master ------------------------------------------------------------------------
    def identities_first_seen_after(self, reference_date: date) -> list[str]:
        """Securities whose ``first_seen`` postdates ``reference_date`` — identities this store
        learned AFTER the moment a run claims to judge.

        THE FAILED-FORWARD-RUN LEAK (review finding, #442). A `run-weekly --end 2026-08-13` aborted
        after `build_universe` had already upserted three securities (BBAR, SSMR, AADX) with
        `first_seen 2026-08-13`. The backdated re-run at `--end 2026-08-12` then found them ALREADY
        IN THE STORE, admitted all three to the 2026-08-12 universe and filed candidate rows for
        them under that run's manifest — a committed historical screen containing names it could
        not have known. The store is mutable and shared; "I re-ran at the earlier date" does not
        undo what the later attempt wrote.
        """
        return [
            str(r["internal_id"]) for r in self._conn.execute(
                "SELECT internal_id FROM securities WHERE first_seen > ? ORDER BY internal_id",
                (_iso(reference_date),),
            )
        ]

    def upsert_security(self, identity: Identity, *, first_seen: date | None = None) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO issuers "
            "(cik, issuer_id, name, sic, sic_description, country, first_seen) "
            "VALUES (?,?,?,?,?,?, COALESCE((SELECT first_seen FROM issuers WHERE cik=?), ?))",
            (
                identity.cik,
                identity.issuer_id,
                identity.name,
                identity.sic,
                identity.sic_description,
                identity.country,
                identity.cik,
                _iso(first_seen),
            ),
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO securities "
            "(internal_id, issuer_id, cik, ticker, mic, exchange, eod_symbol, name, "
            " share_class, sic, currency, first_seen) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?, "
            " COALESCE((SELECT first_seen FROM securities WHERE internal_id=?), ?))",
            (
                identity.internal_id,
                identity.issuer_id,
                identity.cik,
                identity.ticker,
                identity.mic,
                identity.exchange,
                identity.eod_symbol,
                identity.name,
                identity.share_class,
                identity.sic,
                identity.currency,
                identity.internal_id,
                _iso(first_seen),
            ),
        )
        self._conn.commit()

    def get_security(self, internal_id: str) -> Identity | None:
        row = self._conn.execute(
            "SELECT * FROM securities WHERE internal_id = ?", (internal_id,)
        ).fetchone()
        return self._row_to_identity(row) if row else None

    def iter_securities(self) -> Iterator[Identity]:
        for row in self._conn.execute("SELECT * FROM securities ORDER BY internal_id"):
            yield self._row_to_identity(row)

    @staticmethod
    def _row_to_identity(row: sqlite3.Row) -> Identity:
        return Identity(
            internal_id=row["internal_id"],
            issuer_id=row["issuer_id"],
            cik=row["cik"],
            ticker=row["ticker"],
            mic=row["mic"],
            exchange=row["exchange"],
            eod_symbol=row["eod_symbol"],
            name=row["name"],
            share_class=row["share_class"],
            sic=row["sic"],
            sic_description=None,
            currency=row["currency"],
        )

    # --- universe membership ------------------------------------------------------------------
    def record_universe(
        self,
        *,
        as_of: date,
        internal_id: str,
        in_universe: bool,
        market_cap: DataField[float],
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO universe_snapshot "
            "(as_of, internal_id, in_universe, market_cap, source, coverage_status) "
            "VALUES (?,?,?,?,?,?)",
            (
                _iso(as_of),
                internal_id,
                int(in_universe),
                market_cap.value,
                market_cap.source,
                market_cap.coverage_status.value,
            ),
        )
        self._conn.commit()

    def clear_universe(self) -> None:
        """Drop the ENTIRE universe snapshot — a rebuild is a clean, single-generation snapshot (a
        FULL replace across ALL ``as_of``), not an accretion. The prior behaviour cleared only the
        rebuild's own ``as_of``, so on a persistent DB an earlier generation survived and layered on
        top (``run_weekly`` reloads an older snapshot, then ``build_universe`` writes today's → both
        lingered, doubling the exported ``universe_snapshot`` with duplicate ``internal_id``s across
        ``as_of``). Clearing all guarantees the stored/exported universe is exactly the latest
        build's; consumers read the single generation via ``latest_universe`` (MAX ``as_of``). Same
        clean-snapshot discipline as ``clear_candidates``."""
        self._conn.execute("DELETE FROM universe_snapshot")
        self._conn.commit()

    def clear_candidates(self) -> None:
        """Drop the ENTIRE candidate set — a re-screen is a clean snapshot (a FULL replace), not an
        accretion. The prior behaviour cleared only the current run's ``screen_run_at``, so a
        re-screen on a NEW reference date layered its candidates on top of earlier generations
        (e.g. ``run_weekly`` reloads last week's snapshot, then screens this week → both lingered).
        Clearing all guarantees the stored candidates are exactly the latest screen's, so a name
        dropped from the universe (or a whole prior screen run) never lingers as a candidate."""
        self._conn.execute("DELETE FROM candidate_records")
        self._conn.commit()

    def get_universe(self, as_of: date) -> list[str]:
        rows = self._conn.execute(
            "SELECT internal_id FROM universe_snapshot "
            "WHERE as_of = ? AND in_universe = 1 ORDER BY internal_id",
            (_iso(as_of),),
        ).fetchall()
        return [r["internal_id"] for r in rows]

    def latest_universe_as_of(self, on_or_before: date) -> date | None:
        """WHICH universe snapshot `latest_universe` would read — the population's own date.

        Split out because the members alone cannot say WHEN they were selected, and a run that
        records its members without their vintage is unattributable: `2026-07-29-01` screened the
        2026-07-06 snapshot while the build wrote 2026-07-29, and nothing on disk said so.
        Returns None when no snapshot exists at/before the date, which is a real state (the
        `iter_securities` fallback) and must not read as a date.
        """
        row = self._conn.execute(
            "SELECT MAX(as_of) m FROM universe_snapshot WHERE as_of <= ? AND in_universe = 1",
            (_iso(on_or_before),),
        ).fetchone()
        if row is None or row["m"] is None:
            return None
        return date.fromisoformat(row["m"])

    def universe_caps(self, as_of: date) -> dict[str, float]:
        """{internal_id: market_cap} for one snapshot — the input that decided membership."""
        return {r["internal_id"]: r["market_cap"] for r in self._conn.execute(
            "SELECT internal_id, market_cap FROM universe_snapshot "
            "WHERE as_of = ? AND in_universe = 1 AND market_cap IS NOT NULL", (_iso(as_of),))}

    def latest_universe(self, on_or_before: date) -> list[str]:
        """In-universe internal_ids from the most recent universe snapshot at/before a date."""
        row = self._conn.execute(
            "SELECT MAX(as_of) m FROM universe_snapshot WHERE as_of <= ? AND in_universe = 1",
            (_iso(on_or_before),),
        ).fetchone()
        if row is None or row["m"] is None:
            return []
        return self.get_universe(date.fromisoformat(row["m"]))

    # --- prices -------------------------------------------------------------------------------
    def write_prices(self, bars: Iterable[PriceBar]) -> int:
        n = 0
        for bar in bars:
            self._conn.execute(
                "INSERT OR REPLACE INTO prices "
                "(internal_id, bar_date, open, high, low, close, volume, source, coverage_status) "
                "VALUES (?,?,?,?,?,?,?,?, 'present')",
                (
                    bar.internal_id,
                    _iso(bar.bar_date),
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                    bar.source,
                ),
            )
            n += 1
        self._conn.commit()
        return n

    def get_price_history(self, internal_id: str) -> list[PriceBar]:
        rows = self._conn.execute(
            "SELECT * FROM prices WHERE internal_id = ? ORDER BY bar_date", (internal_id,)
        ).fetchall()
        return [
            PriceBar(
                internal_id=r["internal_id"],
                bar_date=date.fromisoformat(r["bar_date"]),
                open=r["open"],
                high=r["high"],
                low=r["low"],
                close=r["close"],
                volume=r["volume"],
                source=r["source"],
            )
            for r in rows
        ]

    def price_frontier(self) -> date | None:
        """The newest bar date in the store, across every name — or None when there are no bars.

        The last moment the price data actually REACHES. Used as an as-of of last resort, where the
        alternative would be a wall-clock date that the data does not support.
        """
        row = self._conn.execute("SELECT MAX(bar_date) AS d FROM prices").fetchone()
        return date.fromisoformat(row["d"]) if row and row["d"] else None

    def price_frontier_for(self, internal_id: str) -> date | None:
        """The newest bar date FOR ONE NAME — None when this store carries no bars for it at all.

        The per-name counterpart to :meth:`price_frontier`. The distinction is load-bearing for
        the spot audit: a store can be current overall and still hold nothing for one security
        (WERN has no bars in the ``-sl`` store while that store's global frontier is the newest
        of the three), and "this store has not refreshed that far" is a different statement from
        "this store does not carry this name".
        """
        row = self._conn.execute(
            "SELECT MAX(bar_date) AS d FROM prices WHERE internal_id = ?", (internal_id,)
        ).fetchone()
        return date.fromisoformat(row["d"]) if row and row["d"] else None

    def close_on(self, internal_id: str, bar_date: date) -> float | None:
        """The close on EXACTLY ``bar_date`` — never the nearest, never a reach-back.

        None when the store has no bar on that day.

        THE POINT OF THE METHOD IS WHAT IT REFUSES TO DO. :meth:`close_as_of` deliberately reaches
        BACKWARD to the latest bar on or before its reference date, which is correct for freezing
        an entry price and wrong for auditing one: a record claiming a close on 2026-08-07 checked
        through a reach-back silently gets the 2026-08-04 bar and reads as verified. That is not a
        hypothetical — it is how BRBR's spot passed its guards while sitting a date beyond this
        worktree's frontier. An audit needs the answer "this store has no bar on that day", so the
        absence comes back as None rather than as a neighbouring price.

        ``prices`` is keyed PRIMARY KEY (internal_id, bar_date), so a date lookup is one-to-one —
        unlike a lookup by VALUE, which is one-to-many on real data (MVST's 0.9188 matches four
        separate bars spanning 2024-02-06 to 2026-07-21).
        """
        row = self._conn.execute(
            "SELECT close FROM prices WHERE internal_id = ? AND bar_date = ?",
            (internal_id, _iso(bar_date)),
        ).fetchone()
        return float(row["close"]) if row is not None else None

    def latest_close(
        self, internal_id: str, *, reference_date: date, staleness_days: int
    ) -> DataField[float]:
        """Latest close as an enveloped datum: UNKNOWN if absent, STALE if too old, else PRESENT."""
        row = self._conn.execute(
            "SELECT bar_date, close, source FROM prices "
            "WHERE internal_id = ? ORDER BY bar_date DESC LIMIT 1",
            (internal_id,),
        ).fetchone()
        if row is None:
            return DataField.unknown(source="EOD", tier=SourceTier.EOD, note="no price bars")
        bar_date = date.fromisoformat(row["bar_date"])
        age = (reference_date - bar_date).days
        if age > staleness_days:
            return DataField.stale(
                row["close"], as_of=bar_date, source=row["source"], tier=SourceTier.EOD,
                note=f"{age}d old (> {staleness_days}d)",
            )
        return DataField.present(
            row["close"], as_of=bar_date, source=row["source"], tier=SourceTier.EOD
        )

    def close_as_of(
        self, internal_id: str, *, reference_date: date, staleness_days: int
    ) -> DataField[float]:
        """Latest close ON OR BEFORE ``reference_date`` — the point-in-time entry-price freeze.

        Unlike :meth:`latest_close` (which takes the globally-latest bar), this never reaches past
        ``reference_date``, so it cannot freeze an entry on a *future* price when the prices table
        has been backfilled — the lookahead trapdoor that would silently inflate a verdict's return
        and corrupt the BUY−AVOID spread. **Fails loud**: if there is no bar on or before
        ``reference_date`` it raises, rather than reaching forward or returning nothing to ignore.
        The staleness check still applies on top: a too-old *prior* bar comes back STALE (surfaced).
        """
        row = self._conn.execute(
            "SELECT bar_date, close, source FROM prices "
            "WHERE internal_id = ? AND bar_date <= ? ORDER BY bar_date DESC LIMIT 1",
            (internal_id, _iso(reference_date)),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"no price bar on or before {reference_date} for {internal_id} "
                "— cannot freeze a point-in-time entry price"
            )
        bar_date = date.fromisoformat(row["bar_date"])
        age = (reference_date - bar_date).days
        if age > staleness_days:
            return DataField.stale(
                row["close"], as_of=bar_date, source=row["source"], tier=SourceTier.EOD,
                note=f"{age}d old (> {staleness_days}d)",
            )
        return DataField.present(
            row["close"], as_of=bar_date, source=row["source"], tier=SourceTier.EOD
        )

    # --- candidate-records --------------------------------------------------------------------
    def save_candidate(self, rec: CandidateRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO candidate_records "
            "(candidate_id, internal_id, screen_run_at, triage_band, twin_to_rule_out, payload) "
            "VALUES (?,?,?,?,?,?)",
            (
                rec.candidate_id,
                rec.data_record.identity.internal_id,
                rec.screen_run_at.isoformat(),
                rec.triage_band.value,
                rec.twin_to_rule_out,
                rec.model_dump_json(),
            ),
        )
        self._conn.commit()

    def get_candidate(self, candidate_id: str) -> CandidateRecord | None:
        row = self._conn.execute(
            "SELECT payload FROM candidate_records WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
        return CandidateRecord.model_validate_json(row["payload"]) if row else None

    def candidate_internal_ids(self, *, band: str | None = None) -> list[str]:
        """Internal ids of the most recent screen run's candidates, optionally filtered to a band.

        The graph track builds its 1-hop graph on these (the small/mid-cap screen universe) — where
        the moat-bearing, concentration-disclosed edges live — not on the CIQ mega-cap focals.
        """
        q = "SELECT MAX(screen_run_at) AS m FROM candidate_records"
        latest = self._conn.execute(q).fetchone()
        if latest is None or latest["m"] is None:
            return []
        sql = "SELECT internal_id FROM candidate_records WHERE screen_run_at = ?"
        params: list[str] = [latest["m"]]
        if band is not None:
            sql += " AND triage_band = ?"
            params.append(band)
        return [r["internal_id"] for r in self._conn.execute(sql, params).fetchall()]

    # --- decision ledger (append-only) --------------------------------------------------------
    def append_ledger(self, entry: LedgerEntry) -> None:
        """Append one ledger row — RE-VALIDATED first, because this record cannot be edited.

        A ``LedgerEntry`` argument looks like proof of validity and is not: ``model_copy(update=)``
        skips every model validator, so a caller can hand over an instance the schema forbids and
        this method would serialize it faithfully. That happened (review P1 on #417) — a close row
        with a negative exit price was written, reported as success, and made ``iter_ledger()``
        raise from then on: one bad flag rendering the whole APPEND-ONLY ledger unreadable, with no
        way to remove the row.

        Validating on the way in costs nothing here (the ledger is tens of rows) and is the only
        place that covers EVERY writer, including ones not yet written.
        """
        try:
            entry = LedgerEntry.model_validate(entry.model_dump())
        except ValidationError as exc:
            raise ValueError(
                f"refusing to append an invalid ledger row {entry.entry_id!r} — the decision "
                f"ledger is append-only, so an invalid row could never be removed: {exc}") from exc
        self._conn.execute(
            "INSERT INTO decision_ledger "
            "(entry_id, candidate_id, internal_id, ticker, verdict, entry_price, "
            " entry_price_as_of, horizon_days, decided_at, payload) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                entry.entry_id,
                entry.candidate_id,
                entry.internal_id,
                entry.ticker,
                entry.verdict.value,
                entry.entry_price,
                _iso(entry.entry_price_as_of),
                entry.horizon_days,
                entry.decided_at.isoformat(),
                entry.model_dump_json(),
            ),
        )
        self._conn.commit()

    def get_ledger_entry(self, entry_id: str) -> LedgerEntry | None:
        row = self._conn.execute(
            "SELECT payload FROM decision_ledger WHERE entry_id = ?", (entry_id,)
        ).fetchone()
        return LedgerEntry.model_validate_json(row["payload"]) if row else None

    def iter_ledger(self) -> Iterator[LedgerEntry]:
        for row in self._conn.execute("SELECT payload FROM decision_ledger ORDER BY decided_at"):
            yield LedgerEntry.model_validate_json(row["payload"])

    # --- snapshots (durable, committed provenance) --------------------------------------------
    def _pk_columns(self, table: str) -> list[str]:
        info = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        pks = sorted((r for r in info if r["pk"]), key=lambda r: r["pk"])
        return [r["name"] for r in pks] or [r["name"] for r in info]

    def export_snapshots(
        self, snapshots_dir: Path, *, tables: Sequence[str] | None = None
    ) -> dict[str, int]:
        """Write each durable table to ``<table>.jsonl`` (ordered by PK). Returns row counts.

        ``tables`` restricts the export to a SUBSET — ``build_universe`` passes only the artifacts
        it actually builds (issuers/securities/universe_snapshot), so a stale working DB
        export can no longer rewrite candidate_records/decision_ledger (the 2026-07-13 near-miss).
        ``None`` exports all tables (full dump). The no-row-drop tables (decision_ledger +
        the securities/issuers entity master) are guarded on write regardless of caller — a shrink
        RAISES rather than silently deleting committed rows."""
        export_tables = tuple(SNAPSHOT_TABLES if tables is None else tables)
        unknown = set(export_tables) - set(SNAPSHOT_TABLES)
        if unknown:
            raise ValueError(f"export_snapshots: unknown table(s) {sorted(unknown)}")
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        counts: dict[str, int] = {}
        for table in export_tables:
            pk = self._pk_columns(table)
            rows = self._conn.execute(f"SELECT * FROM {table} ORDER BY {', '.join(pk)}").fetchall()
            lines = [json.dumps(dict(row), sort_keys=True) for row in rows]
            path = snapshots_dir / f"{table}.jsonl"
            if table in _NO_ROW_DROP_TABLES and path.exists():
                _assert_no_row_drop(path, lines, pk)
            with path.open("w") as f:
                for line in lines:
                    f.write(line + "\n")
            counts[table] = len(rows)
        return counts

    def rebuild_from_snapshots(self, snapshots_dir: Path) -> dict[str, int]:
        """Reconstruct the working DB from committed snapshots. Returns row counts imported."""
        counts: dict[str, int] = {}
        for table in SNAPSHOT_TABLES:
            path = snapshots_dir / f"{table}.jsonl"
            if not path.exists():
                counts[table] = 0
                continue
            n = 0
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                obj: dict[str, Any] = json.loads(line)
                cols = ", ".join(obj.keys())
                placeholders = ", ".join("?" for _ in obj)
                self._conn.execute(
                    f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})",
                    tuple(obj.values()),
                )
                n += 1
            counts[table] = n
        self._conn.commit()
        return counts

    def coverage_of_close(self, internal_id: str, *, reference_date: date) -> CoverageStatus:
        """Convenience for callers/tests: the coverage status of the latest close."""
        return self.latest_close(
            internal_id, reference_date=reference_date, staleness_days=5
        ).coverage_status
