"""The theme-intelligence registry — its OWN SQLite database, never the fund's.

`data/theme_intelligence/registry.db` (git-ignored, like every `*.db`). Nothing here opens, reads or
writes `data/vinci.db`, the decision ledger or any scoring state; a test pins that this package
imports none of those modules.

APPEND-ONLY BY CONSTRUCTION. Every history table (article versions, claims, mentions, thesis
versions, claim links, contributions, relations, change events, snapshots, verification issues,
LLM calls) carries BEFORE UPDATE / BEFORE DELETE triggers that ABORT, so a prior version cannot be
rewritten even by a bug — the same discipline as the fund's decision ledger, applied to research
state. Only three pointer tables move: `articles` (best-known metadata), `theses` (current version /
status), `runs` (status), plus the discovery queue.

IDEMPOTENT APPENDS. Re-inserting an identical record is a no-op; re-inserting a DIFFERENT payload
under an existing id raises — the same id meaning two things is corruption, never an update.

MIGRATIONS are explicit, numbered SQL steps applied in one transaction each and recorded in `meta`.
Durability beyond one machine is `export_jsonl` / `import_jsonl` (diff-able text, no binary) and
`backup` (SQLite online backup to a timestamped file).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from vinci.theme_intelligence.schemas import (
    Article,
    ArticleThesisContribution,
    ArticleVersion,
    ChangeEvent,
    Claim,
    CompletenessReport,
    DocumentRecord,
    EnrichmentSet,
    EvidenceSource,
    MarketContext,
    Mention,
    RetrievalState,
    ReviewResolution,
    SecurityResolution,
    Snapshot,
    SourceHealthCheck,
    ThemeRelation,
    Thesis,
    ThesisClaimLink,
    ThesisVersion,
    VerificationIssue,
    WeeklyRun,
)

M = TypeVar("M", bound=BaseModel)

#: The history tables migration v1 created — FROZEN with v1 (an applied step is never edited).
_V1_APPEND_ONLY = (
    "article_versions", "extractions", "claims", "mentions", "security_resolutions",
    "thesis_versions", "thesis_claim_links", "contributions", "relations", "change_events",
    "snapshots", "verification_issues", "llm_calls",
)
#: Every append-only history table at the current schema.
APPEND_ONLY_TABLES = (*_V1_APPEND_ONLY, "completeness", "source_health", "enrichments",
                      "market_contexts", "review_resolutions")
#: the verification-issue code that corrects a version's retrieval state FULL -> PARTIAL
RETRIEVAL_CORRECTED = "RETRIEVAL_CORRECTED"

#: (version, statements). Version 1 is the initial schema. A later change APPENDS a new entry —
#: never edits an applied one (a DB that already ran step N would silently diverge from one that
#: runs the edited step N).
MIGRATIONS: list[tuple[int, list[str]]] = [
    (1, [
        "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
        "CREATE TABLE articles (article_id TEXT PRIMARY KEY, canonical_url TEXT NOT NULL UNIQUE,"
        " source_id TEXT NOT NULL, published_at TEXT, payload TEXT NOT NULL)",
        "CREATE TABLE article_versions (version_id TEXT PRIMARY KEY, article_id TEXT NOT NULL,"
        " retrieved_at TEXT NOT NULL, retrieval_state TEXT NOT NULL, content_sha256 TEXT,"
        " payload TEXT NOT NULL)",
        "CREATE INDEX ix_av_article ON article_versions(article_id)",
        "CREATE TABLE extractions (extraction_id TEXT PRIMARY KEY,"
        " article_version_id TEXT NOT NULL,"
        " model TEXT NOT NULL, prompt_version TEXT NOT NULL, created_at TEXT NOT NULL,"
        " payload TEXT NOT NULL)",
        "CREATE TABLE evidence_sources (origin_id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
        "CREATE TABLE claims (claim_id TEXT PRIMARY KEY, article_id TEXT NOT NULL,"
        " article_version_id TEXT NOT NULL, measure_key TEXT NOT NULL, fingerprint TEXT NOT NULL,"
        " payload TEXT NOT NULL)",
        "CREATE INDEX ix_claims_article ON claims(article_id)",
        "CREATE INDEX ix_claims_fp ON claims(fingerprint)",
        "CREATE TABLE mentions (mention_id TEXT PRIMARY KEY, article_id TEXT NOT NULL,"
        " normalized_name TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE security_resolutions (resolution_id TEXT PRIMARY KEY,"
        " normalized_name TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE theses (thesis_id TEXT PRIMARY KEY, thesis_key TEXT NOT NULL UNIQUE,"
        " status TEXT NOT NULL, current_version INTEGER NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE thesis_versions (thesis_id TEXT NOT NULL, version INTEGER NOT NULL,"
        " as_of TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY (thesis_id, version))",
        "CREATE TABLE thesis_claim_links (thesis_id TEXT NOT NULL, claim_id TEXT NOT NULL,"
        " role TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY (thesis_id, claim_id))",
        "CREATE TABLE contributions (contribution_id TEXT PRIMARY KEY, article_id TEXT NOT NULL,"
        " thesis_id TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE relations (relation_id TEXT PRIMARY KEY, from_thesis TEXT NOT NULL,"
        " to_thesis TEXT NOT NULL, relation TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE change_events (event_id TEXT PRIMARY KEY, thesis_id TEXT NOT NULL,"
        " run_id TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE runs (run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL,"
        " status TEXT NOT NULL,"
        " payload TEXT NOT NULL)",
        "CREATE TABLE snapshots (snapshot_id TEXT PRIMARY KEY, run_id TEXT NOT NULL,"
        " payload TEXT NOT NULL)",
        "CREATE TABLE verification_issues (issue_id TEXT PRIMARY KEY, run_id TEXT NOT NULL,"
        " ref_id TEXT NOT NULL, severity TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE llm_calls (call_id TEXT PRIMARY KEY, run_id TEXT NOT NULL,"
        " purpose TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE candidates (url TEXT PRIMARY KEY, source_id TEXT NOT NULL,"
        " status TEXT NOT NULL, payload TEXT NOT NULL)",
        *[stmt for t in _V1_APPEND_ONLY for stmt in (
            f"CREATE TRIGGER {t}_no_update BEFORE UPDATE ON {t} "
            f"BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END",
            f"CREATE TRIGGER {t}_no_delete BEFORE DELETE ON {t} "
            f"BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END",
        )],
    ]),
    # v2 (2026-10-11): the per-article-version COMPLETENESS LEDGER — every figure the article
    # states and what happened to it (captured / added by the completeness pass / immaterial /
    # uncaptured). Append-only like every other history table.
    (2, [
        "CREATE TABLE completeness (article_version_id TEXT NOT NULL, run_id TEXT NOT NULL,"
        " payload TEXT NOT NULL, PRIMARY KEY (article_version_id, run_id))",
        "CREATE TRIGGER completeness_no_update BEFORE UPDATE ON completeness "
        "BEGIN SELECT RAISE(ABORT, 'completeness is append-only'); END",
        "CREATE TRIGGER completeness_no_delete BEFORE DELETE ON completeness "
        "BEGIN SELECT RAISE(ABORT, 'completeness is append-only'); END",
    ]),
    # v3 (2026-10-11): SOURCE HEALTH — one immutable observation per channel per check (status,
    # the seven tests, carried timestamps, changes, alert). Its history is what detects a change.
    (3, [
        "CREATE TABLE source_health (check_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,"
        " checked_at TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE INDEX ix_health_source ON source_health(source_id, checked_at)",
        "CREATE TRIGGER source_health_no_update BEFORE UPDATE ON source_health "
        "BEGIN SELECT RAISE(ABORT, 'source_health is append-only'); END",
        "CREATE TRIGGER source_health_no_delete BEFORE DELETE ON source_health "
        "BEGIN SELECT RAISE(ABORT, 'source_health is append-only'); END",
    ]),
    # v4 (2026-10-11): MANUAL DOCUMENTS — one row per supplied file (by its bytes): what the
    # operator stated, what it became (ingested / upgraded / duplicate / review / held), its
    # private stored copy. Mutable like `articles` (a held file is later released); its status
    # history rides in the payload.
    (4, [
        "CREATE TABLE documents (doc_id TEXT PRIMARY KEY, sha256 TEXT NOT NULL UNIQUE,"
        " status TEXT NOT NULL, payload TEXT NOT NULL)",
    ]),
    # v5 (2026-10-14): ENRICHMENT — the companies a thesis's mechanism implies, proposed by the
    # model and checked against the SEC, one set per pass over one thesis version. External
    # hypotheses, kept apart from the sealed thesis versions: no priority rule reads this table.
    (5, [
        "CREATE TABLE enrichments (set_id TEXT PRIMARY KEY, thesis_id TEXT NOT NULL,"
        " thesis_version INTEGER NOT NULL, run_id TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE INDEX ix_enrich_thesis ON enrichments(thesis_id, thesis_version)",
        "CREATE TRIGGER enrichments_no_update BEFORE UPDATE ON enrichments "
        "BEGIN SELECT RAISE(ABORT, 'enrichments is append-only'); END",
        "CREATE TRIGGER enrichments_no_delete BEFORE DELETE ON enrichments "
        "BEGIN SELECT RAISE(ABORT, 'enrichments is append-only'); END",
    ]),
    # v6 (2026-10-15, U42): the lookups every render repeats were full scans — a thesis's links
    # (`relations(thesis_id)`, from OR to) and a version's or a run's verification issues
    # (`issues(ref_id=)` behind every article version read, `issues(run_id=)`). Indexes only:
    # no row is touched.
    (6, [
        "CREATE INDEX ix_rel_from ON relations(from_thesis)",
        "CREATE INDEX ix_rel_to ON relations(to_thesis)",
        "CREATE INDEX ix_issues_ref ON verification_issues(ref_id)",
        "CREATE INDEX ix_issues_run ON verification_issues(run_id)",
    ]),
    # v7 (2026-10-16): MARKET CONTEXT — "is it priced?" for a thesis version, as of a date: price
    # position, return against the benchmark, P/E against its own history. Display only, kept
    # apart from the sealed thesis versions like an enrichment set: no priority rule reads it.
    (7, [
        "CREATE TABLE market_contexts (context_id TEXT PRIMARY KEY, thesis_id TEXT NOT NULL,"
        " thesis_version INTEGER NOT NULL, run_id TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE INDEX ix_market_thesis ON market_contexts(thesis_id, thesis_version)",
        "CREATE TRIGGER market_contexts_no_update BEFORE UPDATE ON market_contexts "
        "BEGIN SELECT RAISE(ABORT, 'market_contexts is append-only'); END",
        "CREATE TRIGGER market_contexts_no_delete BEFORE DELETE ON market_contexts "
        "BEGIN SELECT RAISE(ABORT, 'market_contexts is append-only'); END",
    ]),
    # v8 (2026-10-21): REVIEW RESOLUTIONS — a reviewer's dismissal (or reopening) of one
    # card-review finding, with who, when and why. Append-only: a finding's state is the row no
    # later row supersedes, every earlier one stays as history. No research-action rule reads it.
    (8, [
        "CREATE TABLE review_resolutions (resolution_id TEXT PRIMARY KEY, thesis_id TEXT NOT NULL,"
        " finding_key TEXT NOT NULL, run_id TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE INDEX ix_resolutions_thesis ON review_resolutions(thesis_id)",
        "CREATE TRIGGER review_resolutions_no_update BEFORE UPDATE ON review_resolutions "
        "BEGIN SELECT RAISE(ABORT, 'review_resolutions is append-only'); END",
        "CREATE TRIGGER review_resolutions_no_delete BEFORE DELETE ON review_resolutions "
        "BEGIN SELECT RAISE(ABORT, 'review_resolutions is append-only'); END",
    ]),
    # no table changes: a stored issue's payload may carry `copied_from` (a re-grade's copy keeps
    # its finding's origin, 2026-10-22). Payloads are validated with extra="forbid", so code
    # before it fails on such a row mid-command; the step makes that code refuse the registry
    # up front instead (`migrate`, `import_jsonl`)
    (9, []),
]


class StoreIntegrityError(RuntimeError):
    """An id was re-used for a different payload, or the schema is ahead of this code."""


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _dump(model: BaseModel) -> str:
    return model.model_dump_json()


#: Wall-clock stamps that say WHEN a record was written, not WHAT it says. Re-deriving the same
#: fact later (the same issue, event or SEC resolution) is the same record: first write wins.
_VOLATILE_KEYS = ("created_at", "resolved_at")


def _sans_volatile(payload: str) -> str:
    d = json.loads(payload)
    for k in _VOLATILE_KEYS:
        d.pop(k, None)
    return json.dumps(d, sort_keys=True)


class Store:
    def __init__(self, path: Path, migrations: Sequence[tuple[int, list[str]]] = MIGRATIONS):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path, isolation_level=None)  # explicit transactions only
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        #: article versions read inside `reading()` (U44), by version id and by article — None
        #: outside one
        self._memo: dict[str, ArticleVersion | None] | None = None
        self._memo_by_article: dict[str, list[ArticleVersion]] = {}
        #: views DERIVED from append-only rows inside `reading()` (`derived`, U41)
        self._derived: dict[Any, Any] = {}
        self.migrate(migrations)

    # -- schema ----------------------------------------------------------------------------------
    def schema_version(self) -> int:
        has = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'").fetchone()
        if not has:
            return 0
        row = self.conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        return int(row[0]) if row else 0

    def migrate(self, migrations: Sequence[tuple[int, list[str]]] = MIGRATIONS) -> list[int]:
        current = self.schema_version()
        latest = max(v for v, _ in migrations)
        if current > latest:
            raise StoreIntegrityError(
                f"{self.path} is at schema v{current}, newer than this code (v{latest}) — refusing "
                f"to run old code against a newer registry")
        applied: list[int] = []
        for version, statements in sorted(migrations):
            if version <= current:
                continue
            with self.tx():
                for stmt in statements:
                    self.conn.execute(stmt)
                self.conn.execute(
                    "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(version),))
                self.conn.execute(
                    "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET "
                    "value=excluded.value", (f"migrated_v{version}_at", _now()))
            applied.append(version)
        return applied

    @contextmanager
    def tx(self) -> Iterator[None]:
        """One explicit transaction. Nested use joins the outer one (SAVEPOINT semantics)."""
        if self.conn.in_transaction:
            name = f"sp_{id(object())}"
            self.conn.execute(f"SAVEPOINT {name}")
            try:
                yield
            except BaseException:
                self.conn.execute(f"ROLLBACK TO {name}")
                self.conn.execute(f"RELEASE {name}")
                raise
            self.conn.execute(f"RELEASE {name}")
            return
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        self.conn.execute("COMMIT")

    def close(self) -> None:
        self.conn.close()

    @contextmanager
    def reading(self) -> Iterator[None]:
        """A read-only pass (a render): each article version is parsed ONCE inside it (U44: one
        pilot render parsed 15 versions 1,344 times, each read also querying its corrections).
        Any write inside it drops what was read, and the memo ends with the pass — a version read
        here is never served to a later write path."""
        outer = self._memo is not None
        if not outer:
            self._memo = {}
        try:
            yield
        finally:
            if not outer:
                self._memo = None
                self._memo_by_article.clear()
                self._derived.clear()

    def derived(self) -> dict[Any, Any] | None:
        """Inside `reading()`: a memo for a view DERIVED from append-only rows only — written
        through `_append`, which drops it, as it drops the article versions read (U41: one
        52-week render derived a version's review findings 1,726 times for 913 versions). It ends
        with the pass; None outside one. Never for a view over an upserted table (theses, runs,
        articles, documents, candidates): their writes do not pass through `_append`."""
        return self._derived if self._memo is not None else None

    # -- generic append / upsert -------------------------------------------------------------------
    def _append(self, table: str, cols: dict[str, Any], model: BaseModel) -> bool:
        """Insert an immutable row. Same id + same payload = no-op (False); same id + different
        payload = StoreIntegrityError. Returns True when a row was actually written."""
        if self._memo is not None:  # a write inside a read pass: nothing read stays served
            self._memo.clear()
            self._memo_by_article.clear()
            self._derived.clear()
        payload = _dump(model)
        names = [*cols, "payload"]
        sql = (f"INSERT OR IGNORE INTO {table} ({', '.join(names)}) "
               f"VALUES ({', '.join('?' for _ in names)})")
        cur = self.conn.execute(sql, [*cols.values(), payload])
        if cur.rowcount == 1:
            return True
        pk_cols = self._pk_cols(table)
        where = " AND ".join(f"{c}=?" for c in pk_cols)
        row = self.conn.execute(f"SELECT payload FROM {table} WHERE {where}",
                                [cols[c] for c in pk_cols]).fetchone()
        if row is None:  # ignored for a UNIQUE clash on a non-pk column
            raise StoreIntegrityError(f"{table}: insert ignored on a unique constraint: {cols}")
        if row[0] != payload and _sans_volatile(row[0]) != _sans_volatile(payload):
            raise StoreIntegrityError(
                f"{table}: id {[cols[c] for c in pk_cols]} already stored with a DIFFERENT payload "
                f"— an id must never mean two things")
        return False

    def _pk_cols(self, table: str) -> list[str]:
        info = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        pks = sorted((r[5], r[1]) for r in info if r[5] > 0)
        return [name for _, name in pks]

    def _rows(self, sql: str, args: Sequence[Any], model: type[M]) -> list[M]:
        return [model.model_validate_json(r[0]) for r in self.conn.execute(sql, list(args))]

    # -- articles ---------------------------------------------------------------------------------
    def upsert_article(self, a: Article) -> None:
        self.conn.execute(
            "INSERT INTO articles (article_id, canonical_url, source_id, published_at, payload) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(article_id) DO UPDATE SET "
            "published_at=excluded.published_at, payload=excluded.payload",
            (a.article_id, a.canonical_url, a.source_id,
             a.published_at.isoformat() if a.published_at else None, _dump(a)))

    def article(self, article_id: str) -> Article | None:
        r = self._rows("SELECT payload FROM articles WHERE article_id=?", [article_id], Article)
        return r[0] if r else None

    def article_by_url(self, url: str) -> Article | None:
        r = self._rows("SELECT payload FROM articles WHERE canonical_url=?", [url], Article)
        return r[0] if r else None

    def articles(self) -> list[Article]:
        return self._rows("SELECT payload FROM articles ORDER BY article_id", [], Article)

    def add_article_version(self, v: ArticleVersion) -> bool:
        return self._append("article_versions", {
            "version_id": v.version_id, "article_id": v.article_id,
            "retrieved_at": v.retrieved_at.isoformat(), "retrieval_state": v.retrieval_state.value,
            "content_sha256": v.content_sha256}, v)

    def article_versions(self, article_id: str) -> list[ArticleVersion]:
        if self._memo is not None and article_id in self._memo_by_article:
            return list(self._memo_by_article[article_id])
        out = [self._as_read_now(v) for v in self._rows(
            "SELECT payload FROM article_versions WHERE article_id=? ORDER BY retrieved_at",
            [article_id], ArticleVersion)]
        if self._memo is not None:
            self._memo_by_article[article_id] = out
            self._memo.update({v.version_id: v for v in out})
        return list(out)

    def article_version(self, version_id: str) -> ArticleVersion | None:
        if self._memo is not None and version_id in self._memo:
            return self._memo[version_id]
        r = self._rows("SELECT payload FROM article_versions WHERE version_id=?", [version_id],
                       ArticleVersion)
        v = self._as_read_now(r[0]) if r else None
        if self._memo is not None:
            self._memo[version_id] = v
        return v

    def version_by_content(self, article_id: str, content_sha: str) -> ArticleVersion | None:
        r = self._rows("SELECT payload FROM article_versions WHERE article_id=? AND "
                       "content_sha256=? ORDER BY retrieved_at LIMIT 1", [article_id, content_sha],
                       ArticleVersion)
        return self._as_read_now(r[0]) if r else None

    def retrieval_corrected(self, version_id: str) -> bool:
        """A RETRIEVAL_CORRECTED record (append-only, in `verification_issues`) names this
        version: recorded FULL, read by the CURRENT parser as a preview."""
        return any(i.code == RETRIEVAL_CORRECTED for i in self.issues(ref_id=version_id))

    def _as_read_now(self, v: ArticleVersion) -> ArticleVersion:
        """The version as the CURRENT parser reads it. Pilot 2026-10-12: a long SemiAnalysis
        free preview was recorded FULL (its subscriber marker sat past the parser's old
        20,000-character window). Its row is never edited — the original version, first-seen
        date and spend stand — but every reader sees PARTIAL once the correction is recorded."""
        if v.retrieval_state is RetrievalState.FULL and self.retrieval_corrected(v.version_id):
            return v.model_copy(update={
                "retrieval_state": RetrievalState.PARTIAL,
                "retrieval_note": f"{v.retrieval_note}; CORRECTED to PARTIAL — recorded FULL at "
                                  f"ingestion, read as a preview by the current parser"})
        return v

    # -- extraction / evidence -------------------------------------------------------------------
    def add_extraction(self, extraction_id: str, article_version_id: str, model: str,
                       prompt_version: str, payload: dict[str, Any]) -> bool:
        text = json.dumps(payload, sort_keys=True)
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO extractions (extraction_id, article_version_id, model, "
            "prompt_version, created_at, payload) VALUES (?, ?, ?, ?, ?, ?)",
            (extraction_id, article_version_id, model, prompt_version, _now(), text))
        if cur.rowcount == 1:
            return True
        row = self.conn.execute("SELECT payload FROM extractions WHERE extraction_id=?",
                                (extraction_id,)).fetchone()
        if row and row[0] != text:
            raise StoreIntegrityError(f"extraction {extraction_id} re-used for different output")
        return False

    def extraction_ids(self, article_version_id: str) -> list[str]:
        return [str(r[0]) for r in self.conn.execute(
            "SELECT extraction_id FROM extractions WHERE article_version_id=? ORDER BY created_at",
            (article_version_id,)).fetchall()]

    def extraction(self, extraction_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT payload FROM extractions WHERE extraction_id=?",
                                (extraction_id,)).fetchone()
        return dict(json.loads(row[0])) if row else None

    def add_origin(self, o: EvidenceSource) -> None:
        self.conn.execute("INSERT OR IGNORE INTO evidence_sources (origin_id, payload) VALUES "
                          "(?, ?)", (o.origin_id, _dump(o)))

    def origin(self, origin_id: str) -> EvidenceSource | None:
        r = self._rows("SELECT payload FROM evidence_sources WHERE origin_id=?", [origin_id],
                       EvidenceSource)
        return r[0] if r else None

    def add_claim(self, c: Claim) -> bool:
        return self._append("claims", {
            "claim_id": c.claim_id, "article_id": c.article_id,
            "article_version_id": c.article_version_id, "measure_key": c.measure_key,
            "fingerprint": c.fingerprint}, c)

    def claim(self, claim_id: str) -> Claim | None:
        r = self._rows("SELECT payload FROM claims WHERE claim_id=?", [claim_id], Claim)
        return r[0] if r else None

    def claims_for_article(self, article_id: str) -> list[Claim]:
        return self._rows("SELECT payload FROM claims WHERE article_id=? ORDER BY claim_id",
                          [article_id], Claim)

    def add_mention(self, m: Mention) -> bool:
        return self._append("mentions", {"mention_id": m.mention_id, "article_id": m.article_id,
                                         "normalized_name": m.normalized_name}, m)

    def mentions_for_article(self, article_id: str) -> list[Mention]:
        return self._rows("SELECT payload FROM mentions WHERE article_id=? ORDER BY mention_id",
                          [article_id], Mention)

    def mention(self, mention_id: str) -> Mention | None:
        r = self._rows("SELECT payload FROM mentions WHERE mention_id=?", [mention_id], Mention)
        return r[0] if r else None

    def add_resolution(self, r: SecurityResolution) -> bool:
        return self._append("security_resolutions", {
            "resolution_id": r.resolution_id, "normalized_name": r.normalized_name}, r)

    # -- theses -----------------------------------------------------------------------------------
    def thesis_key(self, t: Thesis) -> str:
        return t.identity  # the engine's identity, segment and review tag included

    def upsert_thesis(self, t: Thesis) -> None:
        self.conn.execute(
            "INSERT INTO theses (thesis_id, thesis_key, status, current_version, payload) VALUES "
            "(?, ?, ?, ?, ?) ON CONFLICT(thesis_id) DO UPDATE SET status=excluded.status, "
            "current_version=excluded.current_version, payload=excluded.payload",
            (t.thesis_id, self.thesis_key(t), t.status.value, t.current_version,
             t.model_dump_json()))

    def rekey_thesis(self, t: Thesis) -> None:
        """A thesis's identity key CORRECTED (engine._correct_segment): the same id, versions and
        links — only the key it is found by changes. Raises on a key another thesis holds."""
        self.conn.execute("UPDATE theses SET thesis_key=?, payload=? WHERE thesis_id=?",
                          (self.thesis_key(t), t.model_dump_json(), t.thesis_id))

    def retire_thesis(self, t: Thesis) -> None:
        """A thesis RETIRED by re-analysis (`Pipeline.run_reanalyse`): its status and its key (which
        now carries the retiring run, freeing the bare key) move together; its id, versions,
        links and history stay."""
        assert t.retired, "retire_thesis takes a thesis with `retired` set"
        self.conn.execute("UPDATE theses SET thesis_key=?, status=?, payload=? WHERE thesis_id=?",
                          (self.thesis_key(t), t.status.value, t.model_dump_json(), t.thesis_id))

    def thesis(self, thesis_id: str) -> Thesis | None:
        r = self._rows("SELECT payload FROM theses WHERE thesis_id=?", [thesis_id], Thesis)
        return r[0] if r else None

    def thesis_by_key(self, key: str) -> Thesis | None:
        r = self._rows("SELECT payload FROM theses WHERE thesis_key=?", [key], Thesis)
        return r[0] if r else None

    def theses(self) -> list[Thesis]:
        return self._rows("SELECT payload FROM theses ORDER BY thesis_id", [], Thesis)

    def add_thesis_version(self, v: ThesisVersion) -> bool:
        return self._append("thesis_versions", {"thesis_id": v.thesis_id, "version": v.version,
                                                "as_of": v.as_of.isoformat()}, v)

    def thesis_versions(self, thesis_id: str) -> list[ThesisVersion]:
        return self._rows("SELECT payload FROM thesis_versions WHERE thesis_id=? ORDER BY "
                          "version", [thesis_id], ThesisVersion)

    def thesis_version(self, thesis_id: str, version: int) -> ThesisVersion | None:
        r = self._rows("SELECT payload FROM thesis_versions WHERE thesis_id=? AND version=?",
                       [thesis_id, version], ThesisVersion)
        return r[0] if r else None

    def add_link(self, link: ThesisClaimLink) -> bool:
        return self._append("thesis_claim_links", {
            "thesis_id": link.thesis_id, "claim_id": link.claim_id, "role": link.role.value},
            link)

    def linked_claim_ids(self, claim_ids: list[str]) -> set[str]:
        """Which of these claims a LIVE thesis links to (any role). A RETIRED thesis's links are
        its history: they carry nothing now — counting them hid a re-analysed claim no live
        thesis carries from the coverage check (the pilot's re-analysis, 2026-10-14)."""
        retired = {t.thesis_id for t in self.theses() if t.retired}
        out: set[str] = set()
        for i in range(0, len(claim_ids), 500):
            chunk = claim_ids[i:i + 500]
            out |= {str(r[0]) for r in self.conn.execute(
                f"SELECT claim_id, thesis_id FROM thesis_claim_links WHERE claim_id IN "
                f"({','.join('?' * len(chunk))})", chunk).fetchall() if r[1] not in retired}
        return out

    def links(self, thesis_id: str) -> list[ThesisClaimLink]:
        return self._rows("SELECT payload FROM thesis_claim_links WHERE thesis_id=? ORDER BY "
                          "claim_id", [thesis_id], ThesisClaimLink)

    def add_contribution(self, c: ArticleThesisContribution) -> bool:
        return self._append("contributions", {
            "contribution_id": c.contribution_id, "article_id": c.article_id,
            "thesis_id": c.thesis_id}, c)

    def contributions(self, thesis_id: str | None = None,
                      article_id: str | None = None) -> list[ArticleThesisContribution]:
        if thesis_id:
            return self._rows("SELECT payload FROM contributions WHERE thesis_id=? ORDER BY "
                              "contribution_id", [thesis_id], ArticleThesisContribution)
        if article_id:
            return self._rows("SELECT payload FROM contributions WHERE article_id=? ORDER BY "
                              "contribution_id", [article_id], ArticleThesisContribution)
        return self._rows("SELECT payload FROM contributions ORDER BY contribution_id", [],
                          ArticleThesisContribution)

    def add_relation(self, r: ThemeRelation) -> bool:
        return self._append("relations", {
            "relation_id": r.relation_id, "from_thesis": r.from_thesis,
            "to_thesis": r.to_thesis, "relation": r.relation.value}, r)

    def relations(self, thesis_id: str | None = None) -> list[ThemeRelation]:
        if thesis_id:
            return self._rows("SELECT payload FROM relations WHERE from_thesis=? OR to_thesis=? "
                              "ORDER BY relation_id", [thesis_id, thesis_id], ThemeRelation)
        return self._rows("SELECT payload FROM relations ORDER BY relation_id", [], ThemeRelation)

    def add_event(self, e: ChangeEvent) -> bool:
        return self._append("change_events", {"event_id": e.event_id, "thesis_id": e.thesis_id,
                                              "run_id": e.run_id}, e)

    def events(self, thesis_id: str | None = None, run_id: str | None = None) -> list[ChangeEvent]:
        if thesis_id:
            return self._rows("SELECT payload FROM change_events WHERE thesis_id=? ORDER BY "
                              "event_id", [thesis_id], ChangeEvent)
        if run_id:
            return self._rows("SELECT payload FROM change_events WHERE run_id=? ORDER BY "
                              "event_id", [run_id], ChangeEvent)
        return self._rows("SELECT payload FROM change_events ORDER BY event_id", [], ChangeEvent)

    # -- runs, snapshots, issues, llm calls ------------------------------------------------------
    def upsert_run(self, r: WeeklyRun) -> None:
        self.conn.execute(
            "INSERT INTO runs (run_id, started_at, status, payload) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(run_id) DO UPDATE SET status=excluded.status, payload=excluded.payload",
            (r.run_id, r.started_at.isoformat(), r.status.value, r.model_dump_json()))

    def run(self, run_id: str) -> WeeklyRun | None:
        r = self._rows("SELECT payload FROM runs WHERE run_id=?", [run_id], WeeklyRun)
        return r[0] if r else None

    def runs(self) -> list[WeeklyRun]:
        return self._rows("SELECT payload FROM runs ORDER BY started_at", [], WeeklyRun)

    def add_snapshot(self, s: Snapshot) -> bool:
        return self._append("snapshots", {"snapshot_id": s.snapshot_id, "run_id": s.run_id}, s)

    def snapshots(self, run_id: str | None = None) -> list[Snapshot]:
        if run_id:
            return self._rows("SELECT payload FROM snapshots WHERE run_id=? ORDER BY snapshot_id",
                              [run_id], Snapshot)
        return self._rows("SELECT payload FROM snapshots ORDER BY snapshot_id", [], Snapshot)

    def add_issue(self, i: VerificationIssue) -> bool:
        return self._append("verification_issues", {
            "issue_id": i.issue_id, "run_id": i.run_id, "ref_id": i.ref_id,
            "severity": i.severity.value}, i)

    def issues(self, run_id: str | None = None, ref_id: str | None = None
               ) -> list[VerificationIssue]:
        if run_id:
            return self._rows("SELECT payload FROM verification_issues WHERE run_id=? ORDER BY "
                              "issue_id", [run_id], VerificationIssue)
        if ref_id:
            return self._rows("SELECT payload FROM verification_issues WHERE ref_id=? ORDER BY "
                              "issue_id", [ref_id], VerificationIssue)
        return self._rows("SELECT payload FROM verification_issues ORDER BY issue_id", [],
                          VerificationIssue)

    def add_completeness(self, r: CompletenessReport) -> bool:
        return self._append("completeness", {"article_version_id": r.article_version_id,
                                             "run_id": r.run_id}, r)

    def completeness(self, article_version_id: str) -> list[CompletenessReport]:
        return self._rows("SELECT payload FROM completeness WHERE article_version_id=? ORDER BY "
                          "run_id", [article_version_id], CompletenessReport)

    def add_health_check(self, h: SourceHealthCheck) -> bool:
        return self._append("source_health", {"check_id": h.check_id, "source_id": h.source_id,
                                              "checked_at": h.checked_at.isoformat()}, h)

    def health_checks(self, source_id: str | None = None,
                      run_id: str | None = None) -> list[SourceHealthCheck]:
        """Oldest first."""
        rows = self._rows("SELECT payload FROM source_health" + (
            " WHERE source_id=?" if source_id else "") + " ORDER BY checked_at, check_id",
            [source_id] if source_id else [], SourceHealthCheck)
        return [h for h in rows if run_id is None or h.run_id == run_id]

    def latest_health(self, *, until: datetime | None = None) -> dict[str, SourceHealthCheck]:
        """The newest check of every channel (recorded no later than `until`, when given)."""
        out: dict[str, SourceHealthCheck] = {}
        for h in self.health_checks():
            if until is None or h.checked_at <= until:
                out[h.source_id] = h
        return out

    def upsert_document(self, d: DocumentRecord) -> None:
        self.conn.execute(
            "INSERT INTO documents (doc_id, sha256, status, payload) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(doc_id) DO UPDATE SET status=excluded.status, payload=excluded.payload",
            (d.doc_id, d.sha256, d.status, _dump(d)))

    def document(self, doc_id: str) -> DocumentRecord | None:
        r = self._rows("SELECT payload FROM documents WHERE doc_id=?", [doc_id], DocumentRecord)
        return r[0] if r else None

    def document_by_sha(self, sha256: str) -> DocumentRecord | None:
        r = self._rows("SELECT payload FROM documents WHERE sha256=?", [sha256], DocumentRecord)
        return r[0] if r else None

    def documents(self, status: str | None = None) -> list[DocumentRecord]:
        rows = self._rows("SELECT payload FROM documents ORDER BY doc_id", [], DocumentRecord)
        return [d for d in rows if status is None or d.status == status]

    def completeness_for_run(self, run_id: str) -> list[CompletenessReport]:
        return self._rows("SELECT payload FROM completeness WHERE run_id=? ORDER BY "
                          "article_version_id", [run_id], CompletenessReport)

    def add_enrichment(self, e: EnrichmentSet) -> bool:
        return self._append("enrichments", {"set_id": e.set_id, "thesis_id": e.thesis_id,
                                            "thesis_version": e.thesis_version,
                                            "run_id": e.run_id}, e)

    def enrichments(self, thesis_id: str) -> list[EnrichmentSet]:
        """Every enrichment set of a thesis, oldest first."""
        sets = self._rows("SELECT payload FROM enrichments WHERE thesis_id=?", [thesis_id],
                          EnrichmentSet)
        return sorted(sets, key=lambda x: (x.created_at, x.set_id))

    def add_market_context(self, m: MarketContext) -> bool:
        return self._append("market_contexts", {"context_id": m.context_id,
                                                "thesis_id": m.thesis_id,
                                                "thesis_version": m.thesis_version,
                                                "run_id": m.run_id}, m)

    def market_context(self, thesis_id: str, version: int, *,
                       until: datetime | None = None) -> MarketContext | None:
        """The LATEST market context computed for one thesis version — with `until`, the latest
        the registry held at that moment — or None."""
        got = [x for x in self._rows("SELECT payload FROM market_contexts WHERE thesis_id=? AND "
                                     "thesis_version=?", [thesis_id, version], MarketContext)
               if until is None or x.created_at <= until]
        return max(got, key=lambda x: (x.created_at, x.context_id)) if got else None

    def add_review_resolution(self, r: ReviewResolution) -> bool:
        return self._append("review_resolutions", {"resolution_id": r.resolution_id,
                                                   "thesis_id": r.thesis_id,
                                                   "finding_key": r.finding_key,
                                                   "run_id": r.run_id}, r)

    def review_resolutions(self, thesis_id: str | None = None, *,
                           run_id: str | None = None) -> list[ReviewResolution]:
        """Review resolutions — of one thesis, written by one run, or all — oldest first."""
        if run_id:
            rows = self._rows("SELECT payload FROM review_resolutions WHERE run_id=?", [run_id],
                              ReviewResolution)
        elif thesis_id:
            rows = self._rows("SELECT payload FROM review_resolutions WHERE thesis_id=?",
                              [thesis_id], ReviewResolution)
        else:
            rows = self._rows("SELECT payload FROM review_resolutions", [], ReviewResolution)
        return sorted(rows, key=lambda x: (x.created_at, x.resolution_id))

    def add_llm_call(self, call_id: str, run_id: str, purpose: str,
                     record: dict[str, Any]) -> None:
        self.conn.execute("INSERT OR IGNORE INTO llm_calls (call_id, run_id, purpose, payload) "
                          "VALUES (?, ?, ?, ?)",
                          (call_id, run_id, purpose, json.dumps(record, sort_keys=True)))

    def llm_calls(self, run_id: str) -> list[dict[str, Any]]:
        return [json.loads(r[0]) for r in self.conn.execute(
            "SELECT payload FROM llm_calls WHERE run_id=? ORDER BY call_id", (run_id,))]

    def llm_call_rows(self, run_id: str) -> list[tuple[str, str, dict[str, Any]]]:
        """(call id, purpose, record) — a call exactly as recorded, to carry it elsewhere."""
        return [(str(c), str(p), dict(json.loads(r))) for c, p, r in self.conn.execute(
            "SELECT call_id, purpose, payload FROM llm_calls WHERE run_id=? ORDER BY call_id",
            (run_id,))]

    def paid_ledger(self) -> dict[str, tuple[str, float | None]]:
        """Every PAID model call (not served from the cache): call id -> (run id, cost USD; None
        when the model had no price). The registry's spend history, call by call."""
        out: dict[str, tuple[str, float | None]] = {}
        for cid, rid, payload in self.conn.execute(
                "SELECT call_id, run_id, payload FROM llm_calls ORDER BY call_id"):
            rec = json.loads(payload)
            if not rec.get("cached"):
                cost = rec.get("cost_usd")
                out[str(cid)] = (str(rid), None if cost is None else float(cost))
        return out

    # -- discovery queue --------------------------------------------------------------------------
    def upsert_candidate(self, url: str, source_id: str, status: str,
                         record: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO candidates (url, source_id, status, payload) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(url) DO UPDATE SET status=excluded.status, payload=excluded.payload",
            (url, source_id, status, json.dumps(record, sort_keys=True, default=str)))

    def candidate(self, url: str) -> tuple[str, dict[str, Any]] | None:
        row = self.conn.execute("SELECT status, payload FROM candidates WHERE url=?",
                                (url,)).fetchone()
        return (str(row[0]), dict(json.loads(row[1]))) if row else None

    def candidates(self, status: str | None = None) -> list[tuple[str, str, dict[str, Any]]]:
        sql = "SELECT url, status, payload FROM candidates"
        args: list[Any] = []
        if status:
            sql += " WHERE status=?"
            args.append(status)
        return [(str(u), str(s), dict(json.loads(p)))
                for u, s, p in self.conn.execute(sql + " ORDER BY url", args)]

    # -- durability -------------------------------------------------------------------------------
    TABLES = ("meta", "articles", "article_versions", "extractions", "evidence_sources", "claims",
              "mentions", "security_resolutions", "theses", "thesis_versions",
              "thesis_claim_links", "contributions", "relations", "change_events", "runs",
              "snapshots", "verification_issues", "llm_calls", "candidates", "completeness",
              "source_health", "documents", "enrichments", "market_contexts",
              "review_resolutions")

    def export_jsonl(self, out_dir: Path, *, include_article_text: bool = False) -> dict[str, int]:
        """Deterministic text dump, one file per table, rows sorted by primary key. Article BODY
        TEXT is excluded by default (licensed third-party text never leaves this machine); block
        hashes stay, so provenance survives."""
        out_dir.mkdir(parents=True, exist_ok=True)
        counts: dict[str, int] = {}
        for table in self.TABLES:
            cols = [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})")]
            order = ", ".join(self._pk_cols(table) or cols[:1])
            rows = self.conn.execute(f"SELECT {', '.join(cols)} FROM {table} ORDER BY {order}")
            lines: list[str] = []
            for row in rows:
                rec = dict(zip(cols, row, strict=True))
                if table == "article_versions" and not include_article_text:
                    p = json.loads(rec["payload"])
                    p["blocks"] = [{**b, "text": ""} for b in p.get("blocks", [])]
                    rec["payload"] = json.dumps(p, sort_keys=True)
                lines.append(json.dumps(rec, sort_keys=True))
            (out_dir / f"{table}.jsonl").write_text("".join(f"{x}\n" for x in lines))
            counts[table] = len(lines)
        return counts

    @classmethod
    def import_jsonl(cls, src_dir: Path, db_path: Path,
                     migrations: Sequence[tuple[int, list[str]]] = MIGRATIONS) -> Store:
        """Rebuild a registry from an export into a NEW database (refuses an existing file).
        Refuses an export made at a NEWER schema than this code (its `meta` schema_version), as
        `migrate` refuses a newer database: its rows would insert and then fail validation
        mid-command (review of the v9 step, 2026-10-22)."""
        if db_path.exists():
            raise StoreIntegrityError(f"{db_path} exists — import only into a fresh database")
        meta = src_dir / "meta.jsonl"
        rows = [json.loads(x) for x in meta.read_text().splitlines()] if meta.exists() else []
        theirs = next((int(r["value"]) for r in rows if r.get("key") == "schema_version"), 0)
        latest = max(v for v, _ in migrations)
        if theirs > latest:
            raise StoreIntegrityError(
                f"{src_dir} was exported at schema v{theirs}, newer than this code (v{latest}) — "
                f"refusing to import a newer registry with old code: update this checkout")
        store = cls(db_path, migrations=migrations)
        with store.tx():
            for table in cls.TABLES:
                f = src_dir / f"{table}.jsonl"
                if not f.exists():
                    continue
                for line in f.read_text().splitlines():
                    rec = json.loads(line)
                    if table == "meta":
                        continue  # the fresh DB's own migration stamps are authoritative
                    cols = list(rec)
                    store.conn.execute(
                        f"INSERT INTO {table} ({', '.join(cols)}) VALUES "
                        f"({', '.join('?' for _ in cols)})", [rec[c] for c in cols])
        return store

    def backup(self, backup_dir: Path) -> Path:
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
        dest = backup_dir / f"registry-{stamp}.db"
        target = sqlite3.connect(dest)
        with target:
            self.conn.backup(target)
        target.close()
        return dest
