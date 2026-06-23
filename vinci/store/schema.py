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
"""

# Tables exported to durable, committed snapshots (the working DB is rebuilt from these).
SNAPSHOT_TABLES: tuple[str, ...] = (
    "issuers",
    "securities",
    "universe_snapshot",
    "fundamentals",
    "events",
    "candidate_records",
    "decision_ledger",
)
