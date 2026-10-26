"""SQLite schema — the ingestion contract made physical.

Keyed by the resolver's internal ids (security ``internal_id`` / issuer ``cik``). Every *data* row
carries envelope columns (``source`` / ``as_of`` / ``coverage_status``, default ``unknown``), so a
missing datum is an explicit UNKNOWN rather than a silent zero. Fundamentals are stored
**as-reported with the filing/report date** (point-in-time), never restated in place.

This SQLite file is the *working* store and is **rebuildable** — durable provenance lives in the
committed append-only snapshots (see :mod:`vinci.store.store`).
"""

from __future__ import annotations

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Entity master ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS issuers (
    cik             TEXT PRIMARY KEY,
    issuer_id       TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    sic             TEXT,
    sic_description TEXT,
    country         TEXT NOT NULL DEFAULT 'US',
    first_seen      TEXT
);

CREATE TABLE IF NOT EXISTS securities (
    internal_id  TEXT PRIMARY KEY,
    issuer_id    TEXT NOT NULL,
    cik          TEXT NOT NULL,
    ticker       TEXT NOT NULL,
    mic          TEXT NOT NULL,
    exchange     TEXT NOT NULL,
    eod_symbol   TEXT NOT NULL,
    name         TEXT NOT NULL,
    share_class  TEXT,
    sic          TEXT,
    currency     TEXT NOT NULL DEFAULT 'USD',
    first_seen   TEXT,
    FOREIGN KEY (cik) REFERENCES issuers (cik)
);
CREATE INDEX IF NOT EXISTS idx_securities_cik ON securities (cik);
CREATE INDEX IF NOT EXISTS idx_securities_ticker ON securities (ticker);

-- Universe membership over time (survivorship discipline: snapshot, never overwrite) --------
CREATE TABLE IF NOT EXISTS universe_snapshot (
    as_of           TEXT NOT NULL,
    internal_id     TEXT NOT NULL,
    in_universe     INTEGER NOT NULL,
    market_cap      REAL,
    source          TEXT NOT NULL,
    coverage_status TEXT NOT NULL DEFAULT 'unknown',
    PRIMARY KEY (as_of, internal_id)
);

-- The PARALLEL THEME BAND's membership (operator ruling 2026-08-31). Same columns, same
-- point-in-time discipline, SEPARATE table on purpose: the primary `universe_snapshot` is the
-- forward-validation population and must not gain rows it was never screened on. Read ONLY at the
-- theme altitude; screens/ranker/ledger never join it.
CREATE TABLE IF NOT EXISTS theme_universe_snapshot (
    as_of           TEXT NOT NULL,
    internal_id     TEXT NOT NULL,
    in_universe     INTEGER NOT NULL,
    market_cap      REAL,
    source          TEXT NOT NULL,
    coverage_status TEXT NOT NULL DEFAULT 'unknown',
    PRIMARY KEY (as_of, internal_id)
);

-- EOD price bars (point-in-time; bar_date is the knowable date) ------------------------------
CREATE TABLE IF NOT EXISTS prices (
    internal_id     TEXT NOT NULL,
    bar_date        TEXT NOT NULL,
    open            REAL NOT NULL,
    high            REAL NOT NULL,
    low             REAL NOT NULL,
    close           REAL NOT NULL,
    volume          REAL NOT NULL,
    source          TEXT NOT NULL,
    coverage_status TEXT NOT NULL DEFAULT 'present',
    PRIMARY KEY (internal_id, bar_date)
);

-- XBRL fundamentals, stored as-reported with the filing/report date (point-in-time) ---------
CREATE TABLE IF NOT EXISTS fundamentals (
    cik             TEXT NOT NULL,
    concept         TEXT NOT NULL,
    unit            TEXT,
    value           REAL,
    period_start    TEXT,
    period_end      TEXT NOT NULL,
    filed_date      TEXT NOT NULL,    -- as_of / knowable date
    fy              INTEGER,
    fp              TEXT,
    form            TEXT,
    accession       TEXT,
    source          TEXT NOT NULL DEFAULT 'EDGAR',
    coverage_status TEXT NOT NULL DEFAULT 'present',
    PRIMARY KEY (cik, concept, period_end, filed_date, accession)
);
CREATE INDEX IF NOT EXISTS idx_fundamentals_cik ON fundamentals (cik);

-- Typed events (pointers for depth; never a count or score) ----------------------------------
CREATE TABLE IF NOT EXISTS events (
    cik         TEXT,
    internal_id TEXT,
    event_type  TEXT NOT NULL,
    event_date  TEXT NOT NULL,
    source      TEXT NOT NULL,
    accession   TEXT,
    detail      TEXT,
    PRIMARY KEY (event_type, event_date, source, accession)
);

-- Screen output: candidate-records handed to the manual discriminator ------------------------
CREATE TABLE IF NOT EXISTS candidate_records (
    candidate_id  TEXT PRIMARY KEY,
    internal_id   TEXT NOT NULL,
    screen_run_at TEXT NOT NULL,
    triage_band   TEXT NOT NULL,
    twin_to_rule_out TEXT NOT NULL,
    payload       TEXT NOT NULL          -- full CandidateRecord JSON
);
CREATE INDEX IF NOT EXISTS idx_candidates_internal ON candidate_records (internal_id);

-- Decision ledger: append-only paper verdicts (BUY and AVOID alike) -------------------------
CREATE TABLE IF NOT EXISTS decision_ledger (
    entry_id          TEXT PRIMARY KEY,
    candidate_id      TEXT NOT NULL,
    internal_id       TEXT NOT NULL,
    ticker            TEXT NOT NULL,
    verdict           TEXT NOT NULL,
    entry_price       REAL NOT NULL,
    entry_price_as_of TEXT NOT NULL,
    horizon_days      INTEGER NOT NULL,
    decided_at        TEXT NOT NULL,
    payload           TEXT NOT NULL          -- full LedgerEntry JSON
);

-- APPEND-ONLY IN THE ENGINE, not by convention alone (2026-10-26) — the same BEFORE UPDATE /
-- BEFORE DELETE abort the theme-intelligence registry installs, so a bug cannot rewrite a verdict.
-- The third trigger closes the door those two leave open: `INSERT OR REPLACE` (the snapshot
-- rebuild's write) deletes a conflicting row WITHOUT firing delete triggers unless
-- `recursive_triggers` is on, so a replace under an existing entry_id is refused unless the new
-- row is identical — an identical re-seed stays a no-op. `IF NOT EXISTS` makes `init_schema`
-- the migration: an existing working DB gains the triggers the next time it is opened.
-- Not a defence against a deliberate `DROP TRIGGER`; the committed JSONL's history is that.
CREATE TRIGGER IF NOT EXISTS decision_ledger_no_update BEFORE UPDATE ON decision_ledger
BEGIN SELECT RAISE(ABORT, 'decision_ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS decision_ledger_no_delete BEFORE DELETE ON decision_ledger
BEGIN SELECT RAISE(ABORT, 'decision_ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS decision_ledger_no_rewrite BEFORE INSERT ON decision_ledger
WHEN EXISTS (
    SELECT 1 FROM decision_ledger AS d WHERE d.entry_id = NEW.entry_id AND (
        d.candidate_id IS NOT NEW.candidate_id OR d.internal_id IS NOT NEW.internal_id
        OR d.ticker IS NOT NEW.ticker OR d.verdict IS NOT NEW.verdict
        OR d.entry_price IS NOT NEW.entry_price OR d.entry_price_as_of IS NOT NEW.entry_price_as_of
        OR d.horizon_days IS NOT NEW.horizon_days OR d.decided_at IS NOT NEW.decided_at
        OR d.payload IS NOT NEW.payload))
BEGIN SELECT RAISE(ABORT, 'decision_ledger is append-only: entry_id already holds a different row');
END;
"""

# Tables exported to durable, committed snapshots (the working DB is rebuilt from these).
SNAPSHOT_TABLES: tuple[str, ...] = (
    "issuers",
    "securities",
    "universe_snapshot",
    "theme_universe_snapshot",
    "fundamentals",
    "events",
    "candidate_records",
    "decision_ledger",
)
