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
    EvidenceSource,
    Mention,
    SecurityResolution,
    Snapshot,
    ThemeRelation,
    Thesis,
    ThesisClaimLink,
    ThesisVersion,
    VerificationIssue,
    WeeklyRun,
)

M = TypeVar("M", bound=BaseModel)

APPEND_ONLY_TABLES = (
    "article_versions", "extractions", "claims", "mentions", "security_resolutions",
    "thesis_versions", "thesis_claim_links", "contributions", "relations", "change_events",
    "snapshots", "verification_issues", "llm_calls",
)

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
        *[stmt for t in APPEND_ONLY_TABLES for stmt in (
            f"CREATE TRIGGER {t}_no_update BEFORE UPDATE ON {t} "
            f"BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END",
            f"CREATE TRIGGER {t}_no_delete BEFORE DELETE ON {t} "
            f"BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END",
        )],
    ]),
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

    # -- generic append / upsert -------------------------------------------------------------------
    def _append(self, table: str, cols: dict[str, Any], model: BaseModel) -> bool:
        """Insert an immutable row. Same id + same payload = no-op (False); same id + different
        payload = StoreIntegrityError. Returns True when a row was actually written."""
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
        return self._rows("SELECT payload FROM article_versions WHERE article_id=? "
                          "ORDER BY retrieved_at", [article_id], ArticleVersion)

    def article_version(self, version_id: str) -> ArticleVersion | None:
        r = self._rows("SELECT payload FROM article_versions WHERE version_id=?", [version_id],
                       ArticleVersion)
        return r[0] if r else None

    def version_by_content(self, article_id: str, content_sha: str) -> ArticleVersion | None:
        r = self._rows("SELECT payload FROM article_versions WHERE article_id=? AND "
                       "content_sha256=? ORDER BY retrieved_at LIMIT 1", [article_id, content_sha],
                       ArticleVersion)
        return r[0] if r else None

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

    def claims_by_fingerprint(self, fingerprint: str) -> list[Claim]:
        return self._rows("SELECT payload FROM claims WHERE fingerprint=? ORDER BY claim_id",
                          [fingerprint], Claim)

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

    def latest_resolution(self, normalized_name: str) -> SecurityResolution | None:
        rows = self._rows("SELECT payload FROM security_resolutions WHERE normalized_name=?",
                          [normalized_name], SecurityResolution)
        return max(rows, key=lambda x: x.resolved_at) if rows else None

    # -- theses -----------------------------------------------------------------------------------
    def thesis_key(self, t: Thesis) -> str:
        return f"{t.key_node}|{t.key_mechanism}|{t.key_direction.value}|{t.key_geography}"

    def upsert_thesis(self, t: Thesis) -> None:
        self.conn.execute(
            "INSERT INTO theses (thesis_id, thesis_key, status, current_version, payload) VALUES "
            "(?, ?, ?, ?, ?) ON CONFLICT(thesis_id) DO UPDATE SET status=excluded.status, "
            "current_version=excluded.current_version, payload=excluded.payload",
            (t.thesis_id, self.thesis_key(t), t.status.value, t.current_version,
             t.model_dump_json()))

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

    def add_llm_call(self, call_id: str, run_id: str, purpose: str,
                     record: dict[str, Any]) -> None:
        self.conn.execute("INSERT OR IGNORE INTO llm_calls (call_id, run_id, purpose, payload) "
                          "VALUES (?, ?, ?, ?)",
                          (call_id, run_id, purpose, json.dumps(record, sort_keys=True)))

    def llm_calls(self, run_id: str) -> list[dict[str, Any]]:
        return [json.loads(r[0]) for r in self.conn.execute(
            "SELECT payload FROM llm_calls WHERE run_id=? ORDER BY call_id", (run_id,))]

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
              "snapshots", "verification_issues", "llm_calls", "candidates")

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
    def import_jsonl(cls, src_dir: Path, db_path: Path) -> Store:
        """Rebuild a registry from an export into a NEW database (refuses an existing file)."""
        if db_path.exists():
            raise StoreIntegrityError(f"{db_path} exists — import only into a fresh database")
        store = cls(db_path)
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
