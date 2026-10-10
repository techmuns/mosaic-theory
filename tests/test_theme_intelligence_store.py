"""The registry's durability rules: migrations, append-only history, idempotent ids, export/import.

Pinned against a REAL populated registry (the authentic JPM fixture run), not an empty one — a
guard that only ever sees empty tables proves nothing (CLAUDE.md: corpus before synthetic).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from tests.theme_intelligence_support import JPM_AS_OF, ingest_jpm, make_pipeline
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.store import (
    APPEND_ONLY_TABLES,
    MIGRATIONS,
    Store,
    StoreIntegrityError,
)


@pytest.fixture()
def jpm(tmp_path: Path) -> Pipeline:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


def test_a_fresh_registry_migrates_to_the_latest_schema(tmp_path: Path) -> None:
    st = Store(tmp_path / "r.db")
    assert st.schema_version() == max(v for v, _ in MIGRATIONS)
    assert st.migrate() == []  # idempotent: nothing left to apply


def test_a_new_migration_appends_and_old_code_refuses_a_newer_db(tmp_path: Path) -> None:
    db = tmp_path / "r.db"
    Store(db).close()
    later = [*MIGRATIONS, (99, ["CREATE TABLE future_thing (x TEXT)"])]
    st = Store(db, migrations=later)
    assert st.schema_version() == 99
    st.close()
    with pytest.raises(StoreIntegrityError, match="newer than this code"):
        Store(db)  # the current code must not run against a newer registry


@pytest.mark.parametrize("table", APPEND_ONLY_TABLES)
def test_history_tables_refuse_update_and_delete(jpm: Pipeline, table: str) -> None:
    conn = jpm.store.conn
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if n == 0:
        pytest.skip(f"{table} has no rows in this run")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute(f"DELETE FROM {table}")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute(f"UPDATE {table} SET payload = payload")
    assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == n


def test_an_id_can_never_mean_two_things(jpm: Pipeline) -> None:
    t = jpm.store.theses()[0]
    v = jpm.store.thesis_version(t.thesis_id, 1)
    assert v is not None
    assert jpm.store.add_thesis_version(v) is False  # same id + same payload: no-op
    tampered = v.model_copy(update={"change_summary": "rewritten history"})
    with pytest.raises(StoreIntegrityError, match="DIFFERENT payload"):
        jpm.store.add_thesis_version(tampered)


def test_export_import_round_trip_keeps_history_and_drops_article_text(
        jpm: Pipeline, tmp_path: Path) -> None:
    counts = jpm.store.export_jsonl(tmp_path / "state")
    assert counts["thesis_versions"] == 3 and counts["claims"] > 0
    raw = (tmp_path / "state" / "article_versions.jsonl").read_text()
    assert "relative strength index" not in raw  # licensed full text is never exported
    back = Store.import_jsonl(tmp_path / "state", tmp_path / "imported.db")
    for t in jpm.store.theses():
        a = jpm.store.thesis_versions(t.thesis_id)
        b = back.thesis_versions(t.thesis_id)
        assert [x.content_sha for x in a] == [x.content_sha for x in b]
    assert {c.claim_id for c in back.claims_for_article(jpm.store.articles()[0].article_id)} \
        == {c.claim_id for c in jpm.store.claims_for_article(jpm.store.articles()[0].article_id)}
    with pytest.raises(StoreIntegrityError):
        Store.import_jsonl(tmp_path / "state", tmp_path / "imported.db")  # never over a live DB


def test_backup_is_a_consistent_copy(jpm: Pipeline, tmp_path: Path) -> None:
    path = jpm.store.backup(tmp_path / "bk")
    copy = Store(path)
    assert [t.thesis_id for t in copy.theses()] == [t.thesis_id for t in jpm.store.theses()]


def test_a_run_record_is_never_a_silent_zero(jpm: Pipeline, tmp_path: Path) -> None:
    run = jpm.store.runs()[-1]
    assert run.status is RunStatus.SUCCEEDED and run.counts["articles_processed"] == 1
    snap = jpm.store.snapshots(run.run_id)
    assert snap and len(snap[0].thesis_versions) == 3
    js = json.loads(run.model_dump_json())
    assert js["llm_model"] and js["extract_prompt_version"] and js["engine_version"]
