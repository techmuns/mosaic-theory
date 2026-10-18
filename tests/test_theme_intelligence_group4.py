"""Group 4 of the review leads — EFFICIENCY (U42, U43, U44). Verified on main d304ea16
(`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`); the real runs (the
pilot rendered identically, the 52-week stress registry measured) are in the build record.

End to end through the REAL engine on HYPOTHETICAL articles (invented text on the reserved `.test`
domain); the store pins run on real `Store` files. No network, no model call.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import (
    DB_SCHEMA_VERSION,
    ArticleVersion,
    IssueSeverity,
    RetrievalState,
    RunStatus,
    VerificationIssue,
    same_area,
)
from vinci.theme_intelligence.store import (
    MIGRATIONS,
    RETRIEVAL_CORRECTED,
    Store,
    StoreIntegrityError,
)

AS_OF = date(2026, 10, 14)


def _x(line: str, title: str, node: str, metric: str, *, mechanism: str = "demand_volume_shift"
       ) -> dict[str, Any]:
    return extraction([claim("c1", "b001", line.rstrip("."), title, metric=metric, value=9,
                             value_text="9%", unit="%", period="2026")],
                      [hyp("h1", title, node=node, mechanism=mechanism, supporting=["c1"])])


def _registry(tmp_path: Path, items: list[tuple[str, str, str, str]]) -> Pipeline:
    """One ingest run, one HYPOTHETICAL article per (slug, node, title, line)."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    for slug, node, title, line in items:
        art = Hypo(slug, "Test Publisher", date(2026, 10, 1), [("paragraph", line)])
        ingest(pipe, art.doc(), _x(line, title, node, f"{slug} metric"), as_of=AS_OF,
               publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


# --- U42: the lookups every render repeats are indexed --------------------------------------------

def _plan(conn: sqlite3.Connection, sql: str, *args: str) -> str:
    return " ".join(str(r[-1]) for r in conn.execute(f"EXPLAIN QUERY PLAN {sql}", args))


def test_a_registry_at_the_current_schema_answers_its_hot_lookups_from_indexes(
        tmp_path: Path) -> None:
    """`relations(thesis_id)` (from OR to) and `issues(ref_id=)` / `issues(run_id=)` were full
    scans — the issues lookup runs behind EVERY article-version read. NEGATIVE pin: a lookup no
    index covers still scans (the plan is read, not assumed)."""
    st = Store(tmp_path / "r.db")
    assert st.schema_version() == DB_SCHEMA_VERSION == max(v for v, _ in MIGRATIONS) >= 6
    c = st.conn
    rel = _plan(c, "SELECT payload FROM relations WHERE from_thesis=? OR to_thesis=?", "a", "a")
    assert "ix_rel_from" in rel and "ix_rel_to" in rel
    assert "ix_issues_ref" in _plan(c, "SELECT payload FROM verification_issues WHERE ref_id=?",
                                    "x")
    assert "ix_issues_run" in _plan(c, "SELECT payload FROM verification_issues WHERE run_id=?",
                                    "x")
    assert "SCAN" in _plan(c, "SELECT payload FROM verification_issues WHERE severity=?", "BLOCK")


def test_a_v5_registry_migrates_to_the_indexes_without_touching_a_row_and_old_code_refuses_it(
        tmp_path: Path) -> None:
    """A registry built at v5 gains the indexes on open; every row is unchanged. NEGATIVE pin: code
    at v5 refuses the v6 registry instead of running against a schema it does not know."""
    path = tmp_path / "r.db"
    old = Store(path, migrations=[m for m in MIGRATIONS if m[0] <= 5])
    old.add_issue(VerificationIssue(issue_id="VI-1", run_id="R-1", scope="article", ref_id="AV-1",
                                    severity=IssueSeverity.INFO, code="X", detail="a fact",
                                    created_at=datetime(2026, 10, 14, tzinfo=UTC)))
    before = old.conn.execute("SELECT * FROM verification_issues").fetchall()
    assert old.schema_version() == 5
    old.close()
    new = Store(path)
    assert new.schema_version() == DB_SCHEMA_VERSION  # v6's indexes, and every later step
    assert new.conn.execute("SELECT * FROM verification_issues").fetchall() == before
    names = {r[0] for r in new.conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert {"ix_rel_from", "ix_rel_to", "ix_issues_ref", "ix_issues_run"} <= names
    new.close()
    with pytest.raises(StoreIntegrityError, match="newer than this code"):
        Store(path, migrations=[m for m in MIGRATIONS if m[0] <= 5])


# --- U44: one read pass parses each article version once ------------------------------------------

def _counting(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    n = [0]
    orig = Store._rows

    def rows(self: Store, sql: str, args: Any, model: Any) -> Any:
        out = orig(self, sql, args, model)
        if model is ArticleVersion:
            n[0] += len(out)
        return out

    monkeypatch.setattr(Store, "_rows", rows)
    return n


def test_inside_a_read_pass_a_version_is_parsed_once_and_outside_it_every_time(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = _registry(tmp_path, [("a", "healthcare.pharma_biotech", "Biopharma volumes climb",
                                 "Biopharma volumes rose 9% in 2026.")])
    st = pipe.store
    (art,) = st.articles()
    (v,) = st.article_versions(art.article_id)
    n = _counting(monkeypatch)
    with st.reading():
        for _ in range(5):
            assert st.article_version(v.version_id) == v
            assert st.article_versions(art.article_id) == [v]
    assert n[0] == 2  # once by id, once by article
    n[0] = 0
    for _ in range(3):  # NEGATIVE pin: no pass, no memo
        st.article_version(v.version_id)
    assert n[0] == 3


def test_a_correction_recorded_inside_a_read_pass_is_read_at_once(tmp_path: Path) -> None:
    """A write inside the pass drops what was read: a version recorded FULL and corrected to a
    preview mid-pass reads PARTIAL on the next read, never the memo's FULL."""
    pipe = _registry(tmp_path, [("a", "healthcare.pharma_biotech", "Biopharma volumes climb",
                                 "Biopharma volumes rose 9% in 2026.")])
    st = pipe.store
    (art,) = st.articles()
    (v,) = st.article_versions(art.article_id)
    assert v.retrieval_state is RetrievalState.FULL
    with st.reading():
        assert st.article_version(v.version_id).retrieval_state is RetrievalState.FULL  # type: ignore[union-attr]
        st.add_issue(VerificationIssue(
            issue_id="VI-corr", run_id="R-x", scope="article_version", ref_id=v.version_id,
            severity=IssueSeverity.INFO, code=RETRIEVAL_CORRECTED, detail="read as a preview",
            created_at=datetime(2026, 10, 15, tzinfo=UTC)))
        assert st.article_version(v.version_id).retrieval_state is RetrievalState.PARTIAL  # type: ignore[union-attr]
        assert st.article_versions(art.article_id)[0].retrieval_state is RetrievalState.PARTIAL


def test_a_render_is_one_read_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """End to end: one render parsed the pilot's 15 versions 1,510 times. NEGATIVE pin: the same
    reads outside a pass parse each time."""
    pipe = _registry(tmp_path, [
        ("a", "healthcare.pharma_biotech", "Biopharma volumes climb",
         "Biopharma volumes rose 9% in 2026."),
        ("b", "healthcare.medtech", "Device orders recover", "Device orders rose 4% in 2026.")])
    n = _counting(monkeypatch)
    write_run_outputs(pipe.store, pipe.store.runs()[-1].run_id, tmp_path / "out")
    distinct = len({v.version_id for a in pipe.store.articles()
                    for v in pipe.store.article_versions(a.article_id)})
    assert distinct == 2 and n[0] - 2 <= 2 * distinct  # (the census above parsed 2 itself)


# --- U43: theses that only share a broader area are counted, never linked pair by pair ------------

@pytest.mark.parametrize(("a", "b", "same"), [
    ("healthcare", "healthcare.pharma_biotech", True),   # an area root and a node in it
    ("healthcare.medtech", "healthcare.pharma_biotech", True),  # two nodes of one area
    ("healthcare.medtech", "healthcare.medtech", False),  # one node: not merely an area
    ("healthcare.medtech", "ai_infrastructure.memory", False),  # two areas
    ("a.b", "a.b.c", False),  # a deeper parent and its child: a chain, not only an area
])
def test_same_area_is_one_rule(a: str, b: str, same: bool) -> None:
    assert same_area(a, b) is same and same_area(b, a) is same


def test_two_nodes_of_one_area_are_counted_on_the_card_and_listed_by_the_desk_never_stored(
        tmp_path: Path) -> None:
    """At 52 weeks the engine stored 15,204 such links (of 18,259) and 42,182 card lines, each
    sent to the paid review, growing with the square of a sector's theses. Now: no stored link,
    ONE count line on the later card, and the desk still folds the other thesis into "same broader
    area". NEGATIVE pin: a meaningful link (two theses on ONE node, the same direction — adjacent
    support) is still stored and still carded."""
    pipe = _registry(tmp_path, [
        ("mem", "ai_infrastructure.memory", "HBM prices climb", "HBM prices rose 9% in 2026."),
        ("grid", "ai_infrastructure.power_grid", "Grid queues lengthen",
         "Grid queues rose 9% in 2026.")])
    by = {t.key_node: t for t in pipe.store.theses()}
    mem, grid = by["ai_infrastructure.memory"], by["ai_infrastructure.power_grid"]
    assert pipe.store.relations() == []
    later = max((mem, grid), key=lambda t: t.created_at)
    v = pipe.store.thesis_version(later.thesis_id, 1)
    assert v is not None
    lines = [s.text for s in v.content.s07_what_could_go_wrong.alternative_mechanisms
             if s.text.startswith("Registry link")]
    assert lines == ["Registry link — 1 other thesis in the same broader area (ai_infrastructure) "
                     "— context only, never evidence; the desk lists them"]
    out = Path(write_run_outputs(pipe.store, pipe.store.runs()[-1].run_id, tmp_path / "out")["dir"])
    page = BeautifulSoup((out / "theses" / f"{mem.thesis_id}.html").read_text(), "html.parser")
    folded = {a["href"] for d in page.select("details.more-rows") for a in d.select("ul.rel a")}
    assert folded == {f"{grid.thesis_id}.html"}
    # the negative: the same node, another mechanism, the same direction — adjacent support
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("mem2", "Test Publisher", date(2026, 10, 2),
               [("paragraph", "HBM shipments rose 9% in 2026.")])
    ingest(pipe, art.doc(), _x("HBM shipments rose 9% in 2026.", "HBM volumes ramp",
                               "ai_infrastructure.memory", "HBM shipments",
                               mechanism="supply_constraint"),
           as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    rels = pipe.store.relations(mem.thesis_id)
    assert len(rels) == 1 and rels[0].relation.value == "SIBLING"
    assert rels[0].evidence_role == "ADJACENT_SUPPORT"
