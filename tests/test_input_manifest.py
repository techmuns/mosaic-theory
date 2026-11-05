"""EVERY PAGE RECORDS WHAT IT WAS BUILT FROM — the input manifest (workstream B, slice 1).

`vinci.provenance` records each read where its bytes enter a build (`CachedHttp`, the price
`Store`, the CIQ bundle); `vinci.dossier.inputs` turns the reads into the page's ``inputs`` block
and into the assembly-run record; `inputs.backfill` gives a page built before the field a record
from its own stamps only. Record:
`docs/records/2026-11-05-every-page-records-what-it-was-built-from.md`.

Every guard here carries a positive and a negative pin. The fixtures are the real types: the
fact layer's frozen FUBO companyfacts slice (its note names the full response's sha256), the
committed fact-layer manifests, `PriceBar` rows through a real `Store`, and committed pages.
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from tests.sec_offline_support import no_network, seed_sec_cache
from vinci import provenance
from vinci.config import Config
from vinci.dossier import assemble as asm
from vinci.dossier import inputs, inputs_backfill, run_metrics
from vinci.dossier.schemas import Dossier, dossier_json
from vinci.facts.edgar_ingest import read_cached
from vinci.netcache import CachedHttp
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store.store import Store

ROOT = pathlib.Path(__file__).resolve().parents[1]
FUBO_SLICE = ROOT / "tests" / "fixtures" / "facts" / "FUBO-companyfacts-slice.json"
FUBO_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001484769.json"
#: the full FUBO response the slice was cut from — its own note states this sha256, and the
#: committed pages snapshot sealed that exact response
FUBO_RESPONSE_SHA = "ea10a688894936583797d7b152d6f44f1e825c45722945cc4cad36269ce3fc7a"
PAGES_SNAPSHOT = "edgar-4f3207f4da9fb71a"
#: A page held by a standing operator instruction is never read by any build or backfill
#: (2026-10-28, the six blind audit packs; BURL is the one with a committed page).
HELD = ("BURL",)


def _http(cache: pathlib.Path, namespace: str = "sec") -> CachedHttp:
    return CachedHttp(cache_dir=cache, user_agent="t", min_interval_sec=0, namespace=namespace)


# --- the recorder ------------------------------------------------------------------------------


def test_a_response_is_hashed_as_the_fact_layer_hashes_it(tmp_path: pathlib.Path) -> None:
    """ONE IDENTITY: the page's record of a cached response and the fact layer's own reader of the
    same cache entry give the same sha256, under the same URL."""
    text = FUBO_SLICE.read_text()
    with _http(tmp_path) as h:
        h._write_cache(FUBO_URL, text)
    with provenance.recording() as rec, _http(tmp_path) as h:
        assert h.get_text(FUBO_URL) == text
    (read,) = rec.reads().http
    assert (read.namespace, read.url) == ("sec", FUBO_URL)
    assert read.sha256 == read_cached(FUBO_URL, tmp_path).sha256
    assert read.fetched_at == pytest.approx(read_cached(FUBO_URL, tmp_path).fetched_at.timestamp())


def test_nothing_is_recorded_or_hashed_with_no_recorder_open(tmp_path: pathlib.Path) -> None:
    with _http(tmp_path) as h:
        h._write_cache(FUBO_URL, "{}")
        assert h.get_text(FUBO_URL) == "{}"
    assert provenance.active() is None
    # a file no build is reading is not even opened
    provenance.note_file("ciq", tmp_path / "absent.xls")


def test_a_nested_recorder_reports_to_the_one_around_it_and_not_to_a_sibling(
        tmp_path: pathlib.Path) -> None:
    with _http(tmp_path) as h:
        h._write_cache("https://x.test/a", "a")
        h._write_cache("https://x.test/b", "b")
        with provenance.recording() as outer:
            with provenance.recording() as first:
                h.get_text("https://x.test/a")
            with provenance.recording() as second:
                h.get_text("https://x.test/b")
    assert {r.url for r in first.reads().http} == {"https://x.test/a"}
    assert {r.url for r in second.reads().http} == {"https://x.test/b"}
    assert {r.url for r in outer.reads().http} == {"https://x.test/a", "https://x.test/b"}


def test_each_cohort_worker_records_only_its_own_reads(tmp_path: pathlib.Path) -> None:
    """`assemble_cohort` runs names on a thread pool: a worker starts with no recorder, so one
    page's reads never reach another's."""
    urls = [f"https://x.test/{i}" for i in range(8)]
    with _http(tmp_path) as h:
        for u in urls:
            h._write_cache(u, u)
    barrier = threading.Barrier(4)

    def task(u: str) -> set[str]:
        with provenance.recording() as rec, _http(tmp_path) as h:
            if urls.index(u) < 4:  # the first four run at once
                barrier.wait(timeout=5)
            h.get_text(u)
        return {r.url for r in rec.reads().http}

    with provenance.recording() as main, ThreadPoolExecutor(max_workers=4) as pool:
        got = list(pool.map(task, urls))
    assert got == [{u} for u in urls]
    assert not main.reads().http, "a worker's read reached the main thread's recorder"


def test_a_post_is_recorded_under_its_cache_key(tmp_path: pathlib.Path) -> None:
    body = {"compareFilters": [{"fieldName": "symbolCode", "fieldValue": "FUBO"}]}
    key = f"https://api.finra.test/data\n#POST#{json.dumps(body, sort_keys=True)}"
    with _http(tmp_path, "finra") as h:
        h._write_cache(key, "[]")
        with provenance.recording() as rec:
            assert h.post_json("https://api.finra.test/data", json_body=body) == []
    (read,) = rec.reads().http
    assert (read.namespace, read.url) == ("finra", key)


def test_a_secret_shaped_query_value_is_never_recorded() -> None:
    url = "https://api.polygon.test/v3/x?apiKey=s3cr3t&date=2026-11-04"
    out = provenance.redact_url(url)
    assert "s3cr3t" not in out and provenance.REDACTED in out and "date=2026-11-04" in out
    plain = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001484769.json?x=1"
    assert provenance.redact_url(plain) == plain


def test_a_price_read_records_the_series(tmp_path: pathlib.Path) -> None:
    with Store(tmp_path / "v.db") as store:
        store.init_schema()
        with provenance.recording() as rec:
            store.get_price_history("SEC-1-AAA")
            store.close_on("SEC-2-BBB", dt.date(2026, 11, 4))
        store.get_price_history("SEC-3-CCC")
    assert rec.reads().series == {"SEC-1-AAA", "SEC-2-BBB"}


# --- the manifest ------------------------------------------------------------------------------


def _bar(day: int, close: float = 10.0) -> PriceBar:
    return PriceBar(internal_id="SEC-0001484769-FUBO", bar_date=dt.date(2026, 10, day), open=close,
                    high=close, low=close, close=close, volume=1000.0, source="polygon-grouped")


def _store(tmp_path: pathlib.Path, bars: list[PriceBar]) -> pathlib.Path:
    db = tmp_path / "vinci.db"
    with Store(db) as store:
        store.init_schema()
        store.upsert_security(Identity(
            internal_id="SEC-0001484769-FUBO", issuer_id="ISS-0001484769", cik="0001484769",
            ticker="FUBO", mic="XNYS", exchange="NYSE", eod_symbol="FUBO", name="FuboTV Inc."))
        store.write_prices(bars)
    return db


def test_a_series_is_identified_through_its_newest_bar_and_survives_a_longer_store(
        tmp_path: pathlib.Path) -> None:
    """The elsewhere-check's property: a store that later holds MORE bars re-hashes the rows
    through the recorded newest bar to the same identity; a RESTATED bar changes it."""
    db = _store(tmp_path, [_bar(1), _bar(2), _bar(5)])
    reads = provenance.Reads(series=frozenset({"SEC-0001484769-FUBO"}))
    (series,) = inputs.manifest_for(reads, db_path=db, extraction_version="t").prices
    assert (series.ticker, series.bars, series.first_bar, series.newest_bar) == (
        "FUBO", 3, dt.date(2026, 10, 1), dt.date(2026, 10, 5))
    with Store(db) as store:
        store.write_prices([_bar(6)])
        through = [b for b in store.get_price_history("SEC-0001484769-FUBO")
                   if b.bar_date <= dt.date(2026, 10, 5)]
        assert inputs.series_rows_sha256(through) == series.rows_sha256
        store.restate_bars("SEC-0001484769-FUBO", 0.5, through=dt.date(2026, 10, 2))
        restated = [b for b in store.get_price_history("SEC-0001484769-FUBO")
                    if b.bar_date <= dt.date(2026, 10, 5)]
    assert inputs.series_rows_sha256(restated) != series.rows_sha256
    # a bar whose ONLY change is its source (`+refiled:<id>`, `+restated`) is another input
    bar = _bar(1)
    assert inputs.series_rows_sha256([bar]) != inputs.series_rows_sha256(
        [bar.model_copy(update={"source": "polygon-grouped+refiled:SEC-1-OLD"})])


def _http_read(sha: str, *, url: str = FUBO_URL, fetched: float = 1.0) -> provenance.HttpRead:
    return provenance.HttpRead("sec", url, fetched, sha, 10)


def test_a_response_a_snapshot_sealed_names_that_snapshot() -> None:
    """THE FACT LAYER'S IDS, REUSED: the response FUBO's slice was cut from is sealed by the
    committed pages snapshot, so the page input names it; an unsealed response names none."""
    m = inputs.manifest_for(
        provenance.Reads(http=frozenset({_http_read(FUBO_RESPONSE_SHA),
                                         _http_read("0" * 64, url="https://x.test/a")})),
        db_path=pathlib.Path("/nonexistent/vinci.db"), extraction_version="t")
    by_url = {r.source_url: r for r in m.responses}
    assert PAGES_SNAPSHOT in (by_url[FUBO_URL].sealed_by or [])
    assert by_url["https://x.test/a"].sealed_by is None


def test_the_id_names_the_inputs_and_only_a_complete_record_has_one(
        tmp_path: pathlib.Path) -> None:
    db = _store(tmp_path, [_bar(1)])
    ciq = tmp_path / "Fubo Inc NYSE FUBO EstimatesReport.xls"
    ciq.write_bytes(b"estimates")
    with provenance.recording() as rec:
        provenance.note_file("ciq", ciq, kind="estimates")
    base = rec.reads() | provenance.Reads(http=frozenset({_http_read("a" * 64)}),
                                          series=frozenset({"SEC-0001484769-FUBO"}))
    first = inputs.manifest_for(base, db_path=db, extraction_version="t")
    assert first.complete and first.inputs_id and first.inputs_id.startswith("inputs-")
    # the same inputs fetched at another time, recorded by other code: the same id
    again = inputs.manifest_for(
        rec.reads() | provenance.Reads(http=frozenset({_http_read("a" * 64, fetched=99.0)}),
                                       series=frozenset({"SEC-0001484769-FUBO"})),
        db_path=db, extraction_version="other")
    assert again.inputs_id == first.inputs_id
    # another response body: another id
    other = inputs.manifest_for(
        rec.reads() | provenance.Reads(http=frozenset({_http_read("b" * 64)}),
                                       series=frozenset({"SEC-0001484769-FUBO"})),
        db_path=db, extraction_version="t")
    assert other.inputs_id != first.inputs_id
    # NEGATIVE: an export that could not be hashed is unrecorded, never given a hash, and the
    # record loses its id
    with provenance.recording() as broken:
        provenance.note_file("ciq", tmp_path / "gone.xls", kind="comps")
    partial = inputs.manifest_for(base | broken.reads(), db_path=db, extraction_version="t")
    assert partial.inputs_id is None and not partial.complete
    assert [u.input for u in partial.unrecorded] == ["ciq:gone.xls"]
    assert all(e.file != "gone.xls" for e in partial.ciq)


def test_a_ciq_export_is_named_by_file_never_by_local_path(tmp_path: pathlib.Path) -> None:
    ciq = tmp_path / "deep" / "Fubo Inc NYSE FUBO EstimatesReport.xls"
    ciq.parent.mkdir()
    ciq.write_bytes(b"x")
    with provenance.recording() as rec:
        provenance.note_file("ciq", ciq, kind="estimates")
    m = inputs.manifest_for(rec.reads(), db_path=tmp_path / "v.db", extraction_version="t")
    assert str(tmp_path) not in m.model_dump_json()


def test_compare_names_what_moved_per_class(tmp_path: pathlib.Path) -> None:
    def m(ciq_sha: str, resp_sha: str) -> inputs.InputManifest:
        return inputs.InputManifest(
            recorded="build", extraction_version="t", covers=list(inputs.COVERS),
            ciq=[inputs.CiqExport(kind="estimates", file="e.xls", sha256=ciq_sha, bytes=1)],
            responses=[inputs.Response(namespace="sec", source_url=FUBO_URL, fetched_at=None,
                                       response_sha256=resp_sha, bytes=1)])
    same = {d.name: d for d in inputs.compare(m("a" * 64, "c" * 64), m("a" * 64, "c" * 64))}
    assert not any(d.moved for d in same.values()) and same["ciq"].same == 1
    moved = {d.name: d for d in inputs.compare(m("a" * 64, "c" * 64), m("b" * 64, "c" * 64))}
    assert moved["ciq"].changed == ("estimates",) and not moved["responses"].moved


def test_a_long_list_of_moved_inputs_says_it_was_cut() -> None:
    rec = inputs.InputManifest(recorded="build", extraction_version="t",
                               covers=list(inputs.COVERS), responses=[
                                   inputs.Response(namespace="sec", source_url=f"https://x/{i}",
                                                   fetched_at=None, response_sha256="a" * 64,
                                                   bytes=1) for i in range(8)])
    now = rec.model_copy(update={"responses": [
        r.model_copy(update={"response_sha256": "b" * 64}) for r in rec.responses]})
    text = "\n".join(inputs.summary_lines(now, rec, show=3))
    assert "(showing 3 of 8)" in text


# --- the build and its run record --------------------------------------------------------------


def test_assemble_one_records_its_reads_onto_the_page_it_writes() -> None:
    """THE WIRING, pinned against its source: the build runs inside its own recorder, notes its
    CIQ bundle, folds in what the finalist and the resolver's index read, and sets ``inputs``
    before the one write. (The live run is in the record: a $0 precheck on committed names.)"""
    tree = ast.parse((ROOT / "vinci" / "dossier" / "assemble.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "assemble_one")
    assert [ast.unparse(d) for d in fn.decorator_list] == ["provenance.recorded"]
    src = ast.unparse(fn)
    assert "page_inputs.note_bundle(bundle)" in src
    assert "reads.add_reads(fin.reads)" in src and "index_reads" in src
    ret = fn.body[-1]
    assert isinstance(ret, ast.Return) and ast.unparse(ret) == (
        "return _write(dossier, llm_log, out_root)")
    last = ast.unparse(fn.body[-2])
    assert "'inputs': page_inputs.for_page(page_inputs.manifest_for(" in last


def test_a_refused_build_still_records_what_it_read(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """A refusal leaves no page, so its run record is the only trace of the inputs that produced
    it: everything read before the refusal is there. A written build's record is the FULL one."""
    from vinci.rank import load_candidates_from_snapshot
    from vinci.sec import build_sec_http

    recs = load_candidates_from_snapshot(ROOT / "data" / "snapshots" / "candidate_records.jsonl")
    fins = [asm.Finalist(r, rank=i + 1, reference_date=dt.date(2026, 10, 1))
            for i, r in enumerate(recs[:2])]
    cfg = Config(data_dir=tmp_path)
    seed_sec_cache(cfg)
    url = "https://www.sec.gov/files/company_tickers.json"
    page = Dossier.model_validate_json(
        (ROOT / "data" / "dossiers" / "NFLX" / "dossier.json").read_text())

    def fake_one(fin: Any, **kw: Any) -> Dossier:
        with build_sec_http(cfg) as h:
            h.get_text(url)
        if fin is fins[1]:
            raise asm.DossierAssemblyError("TEST: refused after reading")
        return page

    monkeypatch.setattr(asm, "assemble_one", fake_one)
    with no_network():
        asm.assemble_cohort(fins, cfg=cfg, llm=None)
    (path,) = (tmp_path / "snapshots" / run_metrics.RUNS_DIR).glob("*.jsonl")
    lines = [json.loads(x) for x in path.read_text().splitlines()]
    by_outcome = {r["outcome"]: r for r in lines}
    assert {r["schema"] for r in lines} == {run_metrics.SCHEMA} == {2}
    refused = by_outcome["refused"]["inputs"]
    assert refused["recorded"] == "build"
    assert [r["source_url"] for r in refused["responses"]] == [url]
    written = by_outcome["written"]["inputs"]
    assert written["responses_listed"] == "all"
    assert [r["source_url"] for r in written["responses"]] == [url]


def test_the_page_lists_the_fact_layers_sources_and_hashes_the_rest(
        tmp_path: pathlib.Path) -> None:
    """THE PAGE'S CUT (`for_page`): companyfacts responses stay listed, every other response is
    counted and hashed, and the id is the full record's — so the run record carrying the same id
    is the full list. NEGATIVE: the cut drops a filing document from the list, not the digest."""
    doc_url = "https://www.sec.gov/Archives/edgar/data/1484769/000148476926000001/x.htm"
    full = inputs.manifest_for(
        provenance.Reads(http=frozenset({_http_read(FUBO_RESPONSE_SHA),
                                         _http_read("d" * 64, url=doc_url)})),
        db_path=tmp_path / "v.db", extraction_version="t")
    page = inputs.for_page(full)
    assert [r.source_url for r in page.responses] == [FUBO_URL]
    assert page.responses_listed == "fact_layer_sources"
    assert page.responses_digest == full.responses_digest
    assert page.responses_digest is not None and page.responses_digest.count == 2
    assert page.inputs_id == full.inputs_id and page.inputs_id is not None
    # the digest moves when a cut response moves, though the listed ones did not
    moved = inputs.manifest_for(
        provenance.Reads(http=frozenset({_http_read(FUBO_RESPONSE_SHA),
                                         _http_read("e" * 64, url=doc_url)})),
        db_path=tmp_path / "v.db", extraction_version="t")
    text = "\n".join(inputs.summary_lines(moved, page))
    assert "responses, all of them: MOVED" in text


# --- the backfill ------------------------------------------------------------------------------


def _export(folder: pathlib.Path, name: str, body: bytes) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(body)
    return provenance.file_sha256(folder / name)[0]


def test_a_stamp_is_resolved_only_by_a_file_that_hashes_to_it(tmp_path: pathlib.Path) -> None:
    live = tmp_path / "ciq"
    archive = tmp_path / "ciq-archive"
    est = _export(live / "FUBO", "FuboTVIncNYSEFUBOEstimatesReport.xls", b"estimates bytes")
    fin = _export(archive / "replaced-2026-10-28" / "FUBO",
                  "FuboTV Inc NYSE FUBO Financials_Quarterly.xls", b"financials bytes")
    doc = {"forward_consensus": {"source_sha256": est[:10]},
           "ev_bridge": {"estimates_sha256": est[:10], "source_sha256": fin[:10]},
           "mechanical": {"x": [{"source_sha256": "0123456789"}]},
           "price_store": {"frontier": "2026-10-31"}}
    m = inputs.backfill(doc, ticker="FUBO", roots=[live, archive], extraction_version="t")
    assert m.recorded == "backfill" and m.inputs_id is None and not m.complete
    by_sha = {e.sha256: e for e in m.ciq}
    assert by_sha[est].kind == "estimates" and by_sha[est].stamped_by == [
        "ev_bridge.estimates_sha256", "forward_consensus.source_sha256"]
    assert by_sha[fin].kind == "financials" and by_sha[fin].freq == "quarterly"
    # NEGATIVE: a stamp no file on this machine hashes to is unrecorded, never given a hash
    unrec = {u.input: u.why for u in m.unrecorded}
    assert "mechanical.x.source_sha256" in unrec["ciq:0123456789"]
    assert all(not e.sha256.startswith("0123456789") for e in m.ciq)
    assert {"ciq:unstamped", "responses", "prices"} <= set(unrec)
    assert "2026-10-31" in unrec["prices"]
    # deterministic: the same page and files give the same bytes
    again = inputs.backfill(doc, ticker="FUBO", roots=[live, archive], extraction_version="t")
    assert again.model_dump_json() == m.model_dump_json()


def test_the_backfill_writes_only_the_block_and_keeps_a_record_it_finds(
        tmp_path: pathlib.Path) -> None:
    """END TO END on a committed page (NFLX), its block stripped: the write adds ``inputs`` and
    moves nothing else; a second run keeps the record; an excluded page is never read."""
    page = json.loads((ROOT / "data" / "dossiers" / "NFLX" / "dossier.json").read_text())
    page.pop("inputs", None)
    cfg = Config(data_dir=tmp_path / "data")
    folder = cfg.data_dir / "dossiers" / "NFLX"
    folder.mkdir(parents=True)
    path = folder / "dossier.json"
    path.write_text(dossier_json(Dossier.model_validate(page)))
    before = json.loads(path.read_text())
    (cfg.data_dir / "dossiers" / "ZZZZ").mkdir()
    (cfg.data_dir / "dossiers" / "ZZZZ" / "dossier.json").write_text("not json")
    out: list[str] = []
    assert inputs_backfill.run(cfg, tickers=[], exclude=["ZZZZ"], roots=[tmp_path / "none"],
                               write=True, emit=out.append) == 0
    after = json.loads(path.read_text())
    assert {k: v for k, v in after.items() if k != "inputs"} == before
    assert after["inputs"]["recorded"] == "backfill"
    assert not any("ZZZZ" in line for line in out[1:]), "an excluded page was read"
    written = path.read_text()
    inputs_backfill.run(cfg, tickers=["NFLX"], exclude=[], roots=[tmp_path / "none"],
                        write=True, emit=out.append)
    assert path.read_text() == written and "keeps its record" in out[-1]


# --- the committed corpus ----------------------------------------------------------------------


def _pages() -> list[tuple[str, dict[str, Any]]]:
    return [(p.parent.name, json.loads(p.read_text()))
            for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
            if p.parent.name not in HELD]


def test_every_committed_page_says_what_it_was_built_from() -> None:
    """THE LIVING CORPUS (phrasing-independent invariants): every page carries a record; a
    backfilled one resolves each of its own stamps or lists it unrecorded, each resolved export's
    sha256 begins with the stamp at every site it names, and it never claims an id."""
    pages = _pages()
    assert len(pages) >= 20
    for t, doc in pages:
        assert doc.get("inputs"), f"{t}: the page records no inputs"
        m = inputs.InputManifest.model_validate(doc["inputs"])
        if m.recorded != "backfill":
            continue
        assert m.inputs_id is None, f"{t}: a backfill claims an id"
        sites = inputs.stamps(doc)
        unrecorded = {u.input for u in m.unrecorded}
        for stamp in sites:
            resolved = [e for e in m.ciq if e.sha256.startswith(stamp)]
            assert resolved or f"ciq:{stamp}" in unrecorded, f"{t}: stamp {stamp} is unaccounted"
            for e in resolved:
                assert e.stamped_by == sites[stamp], f"{t}: {e.file} names other sites"
        assert {"ciq:unstamped", "responses", "prices"} <= unrecorded


def test_the_precheck_census_counts_no_record_hash_as_an_export_stamp() -> None:
    """The precheck's stamp census walks every key ending ``sha256``; the page's own input record
    carries full sha256s that are no export stamps, so it is left out (found on GOOGL's first
    precheck after the backfill, which listed both of its exports twice, once as NOT on disk)."""
    from vinci.dossier.prespend import _stamps

    for t, doc in _pages():
        assert all(len(s) == 10 for s in _stamps(doc)), t
        assert set(_stamps(doc)) == set(inputs.stamps(doc)), t


def test_a_page_with_no_record_reads_as_none_and_round_trips() -> None:
    """NEGATIVE: the field is ABSENT, never null, on a page without it."""
    t, doc = _pages()[0]
    doc = {k: v for k, v in doc.items() if k != "inputs"}
    model = Dossier.model_validate(doc)
    assert model.inputs is None
    assert '"inputs"' not in dossier_json(model)


def test_only_a_ten_hex_value_is_read_as_an_export_stamp() -> None:
    """NEGATIVE (review round 0): another hash a page carries is no CIQ export stamp."""
    doc = {"forward_consensus": {"source_sha256": "abcdef0123"},
           "anchor": {"operator_decision": {"rationale_sha256": "f" * 64}}}
    assert inputs.stamps(doc) == {"abcdef0123": ["forward_consensus.source_sha256"]}


def test_a_folder_the_loader_refuses_is_still_recorded(tmp_path: pathlib.Path) -> None:
    """A build refused by the CIQ loader itself (two exports of one kind) records the files it
    read (review round 0): `assemble_one` notes the folder before re-raising."""
    from vinci.dossier.ciq import CiqAmbiguousError, CiqBundle

    a = tmp_path / "Fubo Inc NYSE FUBO EstimatesReport.xls"
    b = tmp_path / "Fubo Inc  NYSE FUBO EstimatesReport.xls"
    a.write_bytes(b"one")
    b.write_bytes(b"two")
    with provenance.recording() as rec:
        with pytest.raises(CiqAmbiguousError):
            CiqBundle.from_files("FUBO", [a, b])
        inputs.note_files([a, b])
    m = inputs.manifest_for(rec.reads(), db_path=tmp_path / "v.db", extraction_version="t")
    assert sorted(e.file for e in m.ciq) == sorted([a.name, b.name])
    src = (ROOT / "vinci" / "dossier" / "assemble.py").read_text()
    assert "page_inputs.note_files(folder_files)" in src
