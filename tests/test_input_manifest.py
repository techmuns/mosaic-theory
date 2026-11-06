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
    assert {(r.internal_id, r.via, r.bars) for r in rec.reads().series} == {
        ("SEC-1-AAA", "get_price_history", 0), ("SEC-2-BBB", "close_on", None)}


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
    (series,) = inputs.manifest_for(_read_series(db), db_path=db, extraction_version="t").prices
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


def _read_series(db: pathlib.Path) -> provenance.Reads:
    """FUBO's series as a build reads it: through `Store.get_price_history`, inside a recorder."""
    with Store(db) as store, provenance.recording() as rec:
        store.get_price_history("SEC-0001484769-FUBO")
    return rec.reads()


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
    px = _read_series(db)
    base = rec.reads() | px | provenance.Reads(http=frozenset({_http_read("a" * 64)}))
    first = inputs.manifest_for(base, db_path=db, extraction_version="t")
    assert first.complete and first.inputs_id and first.inputs_id.startswith("inputs-")
    # the same inputs fetched at another time, recorded by other code: the same id
    again = inputs.manifest_for(
        rec.reads() | px | provenance.Reads(http=frozenset({_http_read("a" * 64, fetched=99.0)})),
        db_path=db, extraction_version="other")
    assert again.inputs_id == first.inputs_id
    # another response body: another id
    other = inputs.manifest_for(
        rec.reads() | px | provenance.Reads(http=frozenset({_http_read("b" * 64)})),
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
    assert "page_inputs.load_bundle(ticker, manual.files(ticker))" in src
    assert "reads.add_reads(fin.reads)" in src and "index_reads" in src
    ret = fn.body[-1]
    assert isinstance(ret, ast.Return) and ast.unparse(ret) == (
        "return _write(dossier, llm_log, out_root)")
    last = ast.unparse(fn.body[-2])
    assert "'inputs': _page_inputs(reads.reads(), cfg)" in last


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
    # a backfill's record is backfilled afresh, and the same page and files give the same bytes
    assert path.read_text() == written and "stamp(s) resolved" in out[-1]


# --- the committed corpus ----------------------------------------------------------------------


def _pages() -> list[tuple[str, dict[str, Any]]]:
    return [(p.parent.name, json.loads(p.read_text()))
            for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))]


def test_every_committed_page_says_what_it_was_built_from() -> None:
    """THE LIVING CORPUS (phrasing-independent invariants), on BOTH kinds of record:

    - every page carries one, stating what it does not cover;
    - a backfill covers only ``ciq``, accounts for each of the page's own stamps — keys and
      strings alike (`inputs.stamps`) — resolving it or listing it unrecorded, names every site a
      resolved stamp sits at, and claims no id;
    - a build covers all three classes, has an id exactly when nothing is unrecorded, lists only
      the fact layer's sources on the page, and its digest counts at least what it lists."""
    pages = _pages()
    assert len(pages) >= 20
    for t, doc in pages:
        assert doc.get("inputs"), f"{t}: the page records no inputs"
        m = inputs.InputManifest.model_validate(doc["inputs"])
        assert m.not_covered, f"{t}: the record does not say what it leaves out"
        unrecorded = {u.input for u in m.unrecorded}
        if m.recorded == "build":
            assert m.covers == list(inputs.COVERS), t
            assert (m.inputs_id is None) == bool(m.unrecorded), t
            assert m.responses_listed == "fact_layer_sources", t
            assert all(inputs.is_fact_source(r) for r in m.responses), t
            assert m.responses_digest is not None, t
            assert m.responses_digest.count >= len({(r.namespace, r.source_url,
                                                     r.response_sha256) for r in m.responses}), t
            continue
        assert m.covers == ["ciq"] and m.inputs_id is None, f"{t}: a backfill over-claims"
        sites = inputs.stamps(doc)
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
    from vinci.dossier.ciq import CiqAmbiguousError

    a = tmp_path / "Fubo Inc NYSE FUBO EstimatesReport.xls"
    b = tmp_path / "Fubo Inc  NYSE FUBO EstimatesReport.xls"
    a.write_bytes(b"one")
    b.write_bytes(b"two")
    with provenance.recording() as rec, pytest.raises(CiqAmbiguousError):
        inputs.load_bundle("FUBO", [a, b])
    m = inputs.manifest_for(rec.reads(), db_path=tmp_path / "v.db", extraction_version="t")
    assert sorted(e.file for e in m.ciq) == sorted([a.name, b.name])


# --- review round 1 (in-session /code-review high; Codex failed on its usage limit) -------------


def test_an_unhashable_export_names_no_local_path(tmp_path: pathlib.Path) -> None:
    """An OSError's text carries the file's full path; the reason recorded on a committed page in
    a public repository must not (round 1)."""
    with provenance.recording() as rec:
        provenance.note_file("ciq", tmp_path / "deep" / "gone.xls", kind="comps")
    m = inputs.manifest_for(rec.reads(), db_path=tmp_path / "v.db", extraction_version="t")
    (u,) = m.unrecorded
    assert u.input == "ciq:gone.xls" and "FileNotFoundError" in u.why
    assert str(tmp_path) not in m.model_dump_json()


def test_an_unreadable_fact_layer_manifest_never_fails_the_build(tmp_path: pathlib.Path) -> None:
    """The record is built after every paid phase, so a provenance lookup that cannot read the
    fact layer's manifests says so in the record instead of refusing the build (round 1)."""
    facts = tmp_path / "facts"
    (facts / "manifests").mkdir(parents=True)
    (facts / "manifests" / "edgar-0000000000000000.json").write_text('{"entities": [')
    reads = provenance.Reads(http=frozenset({_http_read(FUBO_RESPONSE_SHA)}))
    m = inputs.manifest_for(reads, db_path=tmp_path / "v.db", extraction_version="t",
                            facts_base=facts)
    assert [r.sealed_by for r in m.responses] == [None]
    assert [u.input for u in m.unrecorded] == ["responses:sealed_by"]
    assert m.inputs_id is None


def test_a_record_that_cannot_be_built_leaves_the_run_record_standing(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """run_metrics' contract: ``inputs`` is null only when the record of the reads could not be
    built, and the line says so in ``error`` — the cost-and-outcome line is never lost (round 1)."""
    from vinci.rank import load_candidates_from_snapshot

    rec = load_candidates_from_snapshot(ROOT / "data" / "snapshots" / "candidate_records.jsonl")[0]
    page = Dossier.model_validate_json(
        (ROOT / "data" / "dossiers" / "NFLX" / "dossier.json").read_text())
    monkeypatch.setattr(asm, "assemble_one", lambda fin, **kw: page)

    def broken(*a: Any, **k: Any) -> Any:
        raise ValueError("TEST: no record")

    monkeypatch.setattr(asm.page_inputs, "manifest_for", broken)
    cfg = Config(data_dir=tmp_path)
    seed_sec_cache(cfg)
    with no_network():
        dossiers, errors = asm.assemble_cohort(
            [asm.Finalist(rec, rank=1, reference_date=dt.date(2026, 10, 1))], cfg=cfg)
    (path,) = (tmp_path / "snapshots" / run_metrics.RUNS_DIR).glob("*.jsonl")
    (line,) = [json.loads(x) for x in path.read_text().splitlines()]
    assert line["outcome"] == "written" and line["inputs"] is None
    assert "TEST: no record" in (line["error"] or "")
    assert dossiers == [page] and errors and "input record NOT built" in errors[0]
    # round 2: the CLI exits 1 on any error, so the line says the build's outcome stands
    assert "page written" in errors[0] and "nothing to re-run" in errors[0]


# --- review round 2 (the coordinator's review of ed20e835) ---------------------------------------


def test_a_copy_refetched_with_the_same_bytes_is_the_same_input(tmp_path: pathlib.Path) -> None:
    """The id and the digest name DISTINCT (namespace, URL, body) — a URL re-fetched mid-build
    with unchanged bytes moved both (the reviewer's probe: one copy `inputs-d743199a559ab73b`, two
    same-body copies `inputs-ee0d7c0d8254dd73`). A re-fetch with NEW bytes is a second input."""
    db = tmp_path / "v.db"
    once = inputs.manifest_for(provenance.Reads(http=frozenset({_http_read("a" * 64)})),
                               db_path=db, extraction_version="t")
    twice = inputs.manifest_for(
        provenance.Reads(http=frozenset({_http_read("a" * 64),
                                         _http_read("a" * 64, fetched=2.0)})),
        db_path=db, extraction_version="t")
    assert twice.inputs_id == once.inputs_id and twice.responses_digest == once.responses_digest
    assert len(twice.responses) == 2, "both fetched copies stay listed"
    # NEGATIVE: the re-fetch brought new bytes — two inputs, and the recorder kept both
    with _http(tmp_path) as h, provenance.recording() as rec:
        h._write_cache("https://x.test/a", "old")
        h.get_text("https://x.test/a")
        h._write_cache("https://x.test/a", "new")
        h._fetched["https://x.test/a"] = 2.0
        h.get_text("https://x.test/a")
    moved = inputs.manifest_for(rec.reads(), db_path=db, extraction_version="t")
    assert moved.responses_digest is not None and moved.responses_digest.count == 2


def test_a_kind_read_with_and_without_a_period_type_never_fails_the_record(
        tmp_path: pathlib.Path) -> None:
    """`inputs_id_for` sorted `[kind, freq, sha]` with a None beside a string — a TypeError after
    every paid phase. The loader accepts `…Financials_Quarterly.rtf` beside an unread one."""
    files = []
    for name, body, freq in (("A Inc NYSE A Financials_Quarterly.rtf", b"q", "quarterly"),
                             ("A Inc NYSE A Income Statement.rtf", b"u", None)):
        (tmp_path / name).write_bytes(body)
        files.append((tmp_path / name, freq))
    with provenance.recording() as rec:
        for path, freq in files:
            provenance.note_file("ciq", path, kind="financials", freq=freq)
    m = inputs.manifest_for(rec.reads(), db_path=tmp_path / "v.db", extraction_version="t")
    assert m.inputs_id is not None and len(m.ciq) == 2


def test_a_manifest_entity_of_the_wrong_shape_is_said_not_raised(tmp_path: pathlib.Path) -> None:
    """Valid JSON with a non-object entity raised AttributeError from `_sealed_index` (the
    reviewer's probe: `'str' object has no attribute 'get'`)."""
    facts = tmp_path / "facts"
    (facts / "manifests").mkdir(parents=True)
    (facts / "manifests" / "edgar-1111111111111111.json").write_text(
        '{"snapshot_id": "edgar-1111111111111111", "entities": ["x"]}')
    m = inputs.manifest_for(provenance.Reads(http=frozenset({_http_read("a" * 64)})),
                            db_path=tmp_path / "v.db", extraction_version="t", facts_base=facts)
    assert [u.input for u in m.unrecorded] == ["responses:sealed_by"]


def test_the_page_record_is_said_when_it_cannot_be_built(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """assemble_one builds the page's record after every paid phase: a failure is a record saying
    so (`_page_inputs`), never a lost page."""
    def broken(*a: Any, **k: Any) -> Any:
        raise RuntimeError("TEST")

    monkeypatch.setattr(asm.page_inputs, "manifest_for", broken)
    m = asm._page_inputs(provenance.Reads(), Config(data_dir=tmp_path))
    assert m.recorded == "build" and m.inputs_id is None and not m.complete
    assert [(u.input, "RuntimeError" in u.why) for u in m.unrecorded] == [("all", True)]


def test_a_series_is_identified_by_what_was_read_not_by_a_later_store(
        tmp_path: pathlib.Path) -> None:
    """The store is shared across checkouts: a bar another session appends after the read must
    not appear in the record (the reviewer's probe: read through 10-02, recorded 10-03, complete).
    NEGATIVE: a read of part of a series identifies nothing and is unrecorded, not complete."""
    db = _store(tmp_path, [_bar(1), _bar(2)])
    with Store(db) as store, provenance.recording() as rec:
        read = store.get_price_history("SEC-0001484769-FUBO")
        store.write_prices([_bar(3)])            # another session appends mid-build
        with provenance.recording() as part:
            store.close_as_of("SEC-0001484769-FUBO", reference_date=dt.date(2026, 10, 3),
                              staleness_days=5)
            store.bars_on(dt.date(2026, 10, 3), ["SEC-0001484769-FUBO"])
        partial = part.reads()
    whole = provenance.Reads(series=frozenset(
        r for r in rec.reads().series if r.via == "get_price_history"))
    (series,) = inputs.manifest_for(whole, db_path=db, extraction_version="t").prices
    assert series.newest_bar == dt.date(2026, 10, 2) and series.bars == 2
    assert series.rows_sha256 == inputs.series_rows_sha256(read)
    m = inputs.manifest_for(partial, db_path=db, extraction_version="t")
    assert not m.prices and not m.complete
    assert sorted(u.why.split()[2] for u in m.unrecorded) == [
        "Store.bars_on,", "Store.close_as_of,"]


def test_the_folder_files_a_build_reads_beside_its_workbooks_are_recorded(
        tmp_path: pathlib.Path) -> None:
    """The AS_OF sidecar sets the comps and estimates as-of, and an unrecognised file's name moves
    a caveat: both are inputs (review round 2). What no record covers is said on the record."""
    folder = tmp_path / "FUBO"
    folder.mkdir()
    (folder / "FuboTVIncNYSEFUBOEstimatesReport.xls").write_bytes(b"e")
    (folder / "AS_OF").write_text("2026-10-30\n")
    (folder / "FUBO notes.docx").write_bytes(b"n")
    with provenance.recording() as rec:
        bundle = inputs.load_bundle("FUBO", sorted(folder.iterdir()))
    assert bundle.unrecognised
    m = inputs.manifest_for(rec.reads(), db_path=tmp_path / "v.db", extraction_version="t")
    assert {(e.kind, e.file) for e in m.ciq} == {
        ("estimates", "FuboTVIncNYSEFUBOEstimatesReport.xls"), ("as_of_sidecar", "AS_OF"),
        ("unrecognised", "FUBO notes.docx")}
    assert any("get_security" in n for n in m.not_covered)


def test_the_unrecorded_list_does_not_depend_on_the_hash_seed() -> None:
    """`_ciq` iterated a frozenset and `unrecorded` was never sorted: seeds 1, 2 and 3 gave three
    orders of one record."""
    import subprocess
    import sys

    code = ("import pathlib; from vinci import provenance; from vinci.dossier import inputs\n"
            "fs = frozenset(provenance.FileRead('ciq', f'/x/{c}.xls', None, None, error='E')"
            " for c in 'abcdefghijklmnop')\n"
            "m = inputs.manifest_for(provenance.Reads(files=fs),"
            " db_path=pathlib.Path('/nonexistent/v.db'), extraction_version='t')\n"
            "print([u.input for u in m.unrecorded])")
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env={**__import__("os").environ, "PYTHONHASHSEED": seed},
                           cwd=ROOT, check=True).stdout for seed in ("1", "2", "3")}
    assert len(outs) == 1, outs


@pytest.mark.parametrize("url", [
    "https://x.test/a?sig=abc&date=2026-11-04",
    "https://x.test/a?auth=abc",
    "https://x.test/a?access_token=abc",
    "https://x.test/a?x-api-key=abc",
    "https://x.test/a;apiKey=abc",
    "https://x.test/a?q=1;apiKey=abc",
    "https://user:abc@x.test/a",
])
def test_every_credential_shape_in_a_url_is_redacted(url: str) -> None:
    assert "abc" not in provenance.redact_url(url) and provenance.REDACTED in (
        provenance.redact_url(url))


def test_redaction_leaves_every_other_byte_and_every_other_name() -> None:
    """NEGATIVE: ``keyword`` is no credential, and a redacted URL keeps its other bytes, so it
    still matches its cache key and the fact layer's ``source_url`` (`%20` stayed `%20`)."""
    plain = "https://efts.sec.gov/LATEST/search-index?keyword=x&q=%22Credit%20Agreement%22"
    assert provenance.redact_url(plain) == plain
    assert provenance.redact_url("https://x.test/a?q=%22A%20B%22&token=s") == (
        "https://x.test/a?q=%22A%20B%22&token=REDACTED")


def test_a_backfill_that_would_move_more_than_its_block_writes_nothing(
        tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN for the pre-write refusal: a page whose re-serialisation would drop a key the
    schema does not know is refused, and its file is not touched."""
    page = json.loads((ROOT / "data" / "dossiers" / "NFLX" / "dossier.json").read_text())
    page.pop("inputs", None)
    page["zzz_not_in_the_schema"] = 1
    cfg = Config(data_dir=tmp_path / "data")
    path = cfg.data_dir / "dossiers" / "NFLX" / "dossier.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(page, indent=2))
    before = path.read_text()
    out: list[str] = []
    assert inputs_backfill.run(cfg, tickers=["NFLX"], exclude=[], roots=[tmp_path / "none"],
                               write=True, emit=out.append) == 1
    assert path.read_text() == before and "REFUSED" in out[-1]


def test_a_whole_corpus_backfill_runs_without_exclude(tmp_path: pathlib.Path) -> None:
    """``--all`` names no page to leave out: mosaic-theory holds back no name (operator ruling
    2026-11-05, `docs/records/2026-11-05-mosaic-theory-holds-back-no-name.md`). With no
    ``--exclude`` every committed page is backfilled; ``--exclude`` stays an ordinary skip."""
    page = json.loads((ROOT / "data" / "dossiers" / "NFLX" / "dossier.json").read_text())
    page.pop("inputs", None)
    cfg = Config(data_dir=tmp_path / "data")
    for t in ("BURL", "NFLX"):
        (cfg.data_dir / "dossiers" / t).mkdir(parents=True)
        (cfg.data_dir / "dossiers" / t / "dossier.json").write_text(
            dossier_json(Dossier.model_validate(page | {"ticker": t})))
    out: list[str] = []
    assert inputs_backfill.run(cfg, tickers=[], exclude=[], roots=[tmp_path / "none"],
                               write=False, emit=out.append) == 0
    assert "2 page(s)" in out[0] and "REFUSED" not in out[0]
    assert {line.split()[0] for line in out[1:]} == {"BURL", "NFLX"}
    skipped: list[str] = []
    assert inputs_backfill.run(cfg, tickers=[], exclude=["NFLX"], roots=[tmp_path / "none"],
                               write=False, emit=skipped.append) == 0
    assert {line.split()[0] for line in skipped[1:]} == {"BURL"}


def test_a_file_held_under_two_names_is_named_by_the_least(tmp_path: pathlib.Path) -> None:
    """The recorded `file` was whichever copy the directory scan met last; and the unresolved
    reason counted the files searched — both machine-specific."""
    est = _export(tmp_path / "b" / "FUBO", "z-copy EstimatesReport.xls", b"same bytes")
    _export(tmp_path / "a" / "FUBO", "a EstimatesReport.xls", b"same bytes")
    doc = {"forward_consensus": {"source_sha256": est[:10]},
           "mechanical": {"x": {"source_sha256": "0123456789"}}}
    for roots in ([tmp_path / "a", tmp_path / "b"], [tmp_path / "b", tmp_path / "a"]):
        m = inputs.backfill(doc, ticker="FUBO", roots=roots, extraction_version="t")
        assert [e.file for e in m.ciq] == ["a EstimatesReport.xls"]
        why = {u.input: u.why for u in m.unrecorded}["ciq:0123456789"]
        assert "file(s)" not in why and "root(s)" not in why
        assert m.covers == ["ciq"]


def test_a_stamp_written_into_a_string_is_read_by_the_one_reader() -> None:
    """`CiqBridge.stamp` writes ``<file> sha <10 hex>`` into an anchor input's source, and the
    bridge's claims source writes ``(<file>, sha <10 hex>)``: both read through
    `ciq_balance.stamps_in_text`. Real strings from the committed pages (TECX's anchor, AMZN's
    claims source). NEGATIVE: ``sha ?`` is no stamp, and neither is a 64-hex digest."""
    from vinci.dossier.ciq_balance import stamps_in_text

    tecx = ("CIQ classified balance sheet (vendor basis; EDGAR debt tags absent or under-captured) "
            "[Tectonic Therapeutic Inc NasdaqGM TECX Financials_Quarterly.xls sha dce450e41b]")
    amzn = ("ev_bridge.claims — CIQ Net Debt + preferred + minority interest at the 2026-09-30 "
            "balance sheet (Amazon com Inc NasdaqGS AMZN Financials_Quarterly.xls, sha 796a53f316)")
    two = "[A.xls sha 0123456789 + B.xls sha abcdefabcd]"
    assert stamps_in_text(tecx) == ["dce450e41b"] and stamps_in_text(amzn) == ["796a53f316"]
    assert stamps_in_text(two) == ["0123456789", "abcdefabcd"]
    assert stamps_in_text("A.xls sha ?") == [] and stamps_in_text("sha " + "f" * 64) == []
    assert inputs.stamps({"anchor": {"net_debt": {"source": tecx}}}) == {
        "dce450e41b": ["anchor.net_debt.source"]}


def test_a_finalist_carries_what_building_it_read(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """A maintained name's record reads companyfacts and its price history BEFORE its build
    starts; `_recorded_finalist` keeps those reads on the finalist for the page's record."""
    with _http(tmp_path) as h:
        h._write_cache("https://x.test/facts", "{}")

    def built(cfg: Any, t: str, rec: Any, row: Any) -> Any:
        with _http(tmp_path) as http:
            http.get_text("https://x.test/facts")
        return asm.Finalist(None, None, dt.date(2026, 10, 1))

    monkeypatch.setattr(asm, "_finalist", built)
    fin = asm._recorded_finalist(Config(data_dir=tmp_path), "FUBO", None, None)
    assert fin is not None and fin.reads is not None
    assert [r.url for r in fin.reads.http] == ["https://x.test/facts"]


def test_the_resolver_index_names_the_responses_it_was_built_from(
        tmp_path: pathlib.Path) -> None:
    from vinci.resolver import EntityResolver

    cfg = Config(data_dir=tmp_path)
    seed_sec_cache(cfg)
    with no_network():
        resolver = EntityResolver.from_config(cfg)
        assert resolver.index_reads is None
        _ = resolver.index
    reads = resolver.index_reads
    assert reads is not None and {r.url.rsplit("/", 1)[-1] for r in reads.http} == {
        "company_tickers.json", "company_tickers_exchange.json"}


def test_a_series_whose_label_cannot_be_read_keeps_its_identity(tmp_path: pathlib.Path) -> None:
    """The ticker is a label looked up as the record is written: a store that cannot answer it
    leaves the label empty, never the series unrecorded or the record unbuilt."""
    db = _store(tmp_path, [_bar(1)])
    reads = _read_series(db)

    class NoSecurities(Store):
        def get_security(self, internal_id: str) -> Any:
            raise RuntimeError("TEST")

    with NoSecurities(db) as store:
        m = inputs.from_reads(reads, store=store, extraction_version="t")
    (series,) = m.prices
    assert series.ticker is None and series.rows_sha256 and m.complete
