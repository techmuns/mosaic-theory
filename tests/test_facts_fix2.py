"""TeamNostra fix request 2, the fact layer (`vinci.facts`), orders 5-7: RFL-D1 to RFL-D10.

Each defect is pinned on the input that showed it: the COMMITTED pages snapshot
(`edgar-4f3207f4da9fb71a`, schema v2) where the defect is live on it, the committed IT
companyfacts and submissions fixtures for an acceptance time SEC states, and constructed inputs for
shapes no real response carries (an unknown key, a missing `facts`). No value of a constructed
input is a real company's.

* RFL-D1 — a read past the copy's fetch served its latest value, no staleness flag.
* RFL-D2 — no acceptance time: a value filed on day D was visible to a replay at D's close.
* RFL-D4 — the reader trusted the manifest: a consistent object-and-entry edit was served.
* RFL-D5 — "not in the snapshot" and "nothing filed" raised the same error.
* RFL-D6 — uploads had no source check: a constructed `ciq` snapshot uploaded whole.
* RFL-D7 — after a cache refresh, parity reported store differences, not a changed response.
* RFL-D8 — duplicates the ingest drops showed as unexplained parity differences.
* RFL-D9 — one unknown-shape row aborted the ingest and left orphan objects.
* RFL-D10 — a response with no "facts" key was "no row with a filed date".
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq  # type: ignore[import-untyped]
import pytest

from vinci.facts import (
    FILED,
    FactCutUndeterminedError,
    FactNotHeldError,
    FactStaleError,
    FactStore,
    FactUnknownError,
    Period,
    cut_instant,
)
from vinci.facts.edgar_ingest import (
    EXTRACTOR,
    EXTRACTOR_VERSION,
    SOURCE,
    rows_from_companyfacts,
    unread_reason,
)
from vinci.facts.remote import upload_refusal, upload_snapshot
from vinci.facts.store import (
    FactsStoreError,
    _sha256_file,
    build_manifest,
    load_manifest,
    snapshot_id_for,
    write_manifest,
    write_partitions,
)
from vinci.netcache import CachedHttp

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "data" / "facts"
PAGES_ID = "edgar-4f3207f4da9fb71a"
FIX = ROOT / "tests" / "fixtures"
TGT, NFLX, IT = "0000027419", "0001065280", "0000749251"
SHARES = "dei:EntityCommonStockSharesOutstanding"


@pytest.fixture(scope="module")
def pages() -> FactStore:
    """The committed pages snapshot, read where it is committed."""
    return FactStore(PAGES_ID, facts_base=COMMITTED, root=COMMITTED / "objects")


def _cache(tmp: Path, entries: dict[str, str]) -> Path:
    cache = tmp / "cache"
    with CachedHttp(cache_dir=cache, user_agent="t", min_interval_sec=0, namespace="sec") as h:
        for url, text in entries.items():
            h._write_cache(url, text)
    return cache


def _cf_url(cik: str) -> str:
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def _sub_url(cik: str) -> str:
    return f"https://data.sec.gov/submissions/CIK{cik}.json"


def _pages_dir(tmp: Path, ciks: dict[str, str]) -> None:
    for ticker, cik in ciks.items():
        (tmp / "data" / "dossiers" / ticker).mkdir(parents=True)
        (tmp / "data" / "dossiers" / ticker / "dossier.json").write_text(
            json.dumps({"cik": cik, "reference_date": "2026-11-02"}))


def _ingest(tmp: Path, monkeypatch: pytest.MonkeyPatch, cache: Path) -> int:
    from vinci.facts.__main__ import main
    monkeypatch.chdir(tmp)
    monkeypatch.delenv("VINCI_FACTS_STORE", raising=False)
    return main(["ingest", "--cache-dir", str(cache)])


def _row(end: str, val: float, accn: str, filed: str, form: str = "10-K",
         start: str | None = None) -> dict[str, Any]:
    r: dict[str, Any] = {"end": end, "val": val, "accn": accn, "fy": int(end[:4]), "fp": "FY",
                         "form": form, "filed": filed}
    if start:
        r["start"] = start
    return r


# --- RFL-D1: a read past the copy's fetch ---------------------------------------------------------

def test_rfl_d1_a_read_past_the_copys_fetch_is_refused(pages: FactStore) -> None:
    """REAL: the committed snapshot's NFLX copy was fetched before 2026-11-11, so a read as of
    that day cannot know what NFLX filed since. It was served silently; it is refused, naming the
    fetch."""
    fetched = pages.fetched_at(NFLX)
    assert fetched is not None and fetched < datetime(2026, 11, 11, tzinfo=UTC)
    q4 = Period.instant(date(2025, 12, 31))
    with pytest.raises(FactStaleError, match="past the moment 1 of 1"):
        pages.get(NFLX, "us-gaap:Assets", q4, date(2026, 11, 11), unit="USD")
    got = pages.get(NFLX, "us-gaap:Assets", q4, date(2026, 11, 11), unit="USD", stale_ok=True)
    assert got.stale and got.fetched_at == fetched


def test_rfl_d1_negative_a_read_before_the_fetch_is_not_stale(pages: FactStore) -> None:
    fetched = pages.fetched_at(NFLX)
    assert fetched is not None
    day = fetched.date().replace(day=1)          # a day inside the copy's knowledge
    got = pages.get(NFLX, "us-gaap:Assets", Period.instant(date(2025, 12, 31)), day, unit="USD")
    assert not got.stale and got.fetched_at == fetched
    assert not pages.is_stale(NFLX, day)


# --- RFL-D2: the acceptance time ----------------------------------------------------------------

def test_rfl_d2_a_schema_v2_snapshot_cannot_place_a_filing_on_the_cuts_day(
        pages: FactStore) -> None:
    """REAL: TGT's 10-K 0000027419-17-000008 was filed 2017-03-08 and accepted 16:22 EST (SEC's
    submissions document). The committed snapshot states no acceptance time, and served it to a
    replay at that day's 16:00 close. The cut now cannot place it, and says so; the day-level cut
    the page's reader makes still holds it."""
    period = Period.instant(date(2017, 3, 2))
    with pytest.raises(FactCutUndeterminedError, match="dated 2017-03-08 .*0000027419-17-000008"):
        pages.get(TGT, SHARES, period, date(2017, 3, 8), stale_ok=True)
    by_day = pages.get(TGT, SHARES, period, date(2017, 3, 8), basis=FILED, stale_ok=True)
    assert (by_day.accession, by_day.value) == ("0000027419-17-000008", 552_675_341)
    # the next day the filing is known either way
    nxt = pages.get(TGT, SHARES, period, date(2017, 3, 9), stale_ok=True)
    assert nxt.accession == "0000027419-17-000008"


def _it_cache(tmp: Path) -> Path:
    sub = FIX / "submissions_pages"
    return _cache(tmp, {
        _cf_url(IT): (FIX / "companyfacts" / "IT.json").read_text(),
        _sub_url(IT): (sub / "IT.json").read_text(),
        "https://data.sec.gov/submissions/CIK0000749251-submissions-001.json":
            (sub / "IT-submissions-001.json").read_text(),
    })


@pytest.fixture
def it_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FactStore:
    """REAL: Gartner's committed companyfacts and submissions fixtures, ingested by the CLI."""
    _pages_dir(tmp_path, {"IT": IT})
    assert _ingest(tmp_path, monkeypatch, _it_cache(tmp_path)) == 0
    return FactStore(facts_base=tmp_path / "data" / "facts",
                     root=tmp_path / "data" / "facts" / "objects")


def test_rfl_d2_the_ingest_stores_each_filings_acceptance_time(it_store: FactStore) -> None:
    m = it_store.manifest
    assert m["schema_version"] == 3
    (e,) = m["entities"]
    acc = e["acceptance"]
    # the recent page and page 001 are cached; page 002 is not, and is named
    assert [d["url"].rsplit("/", 1)[1] for d in acc["documents"]] == [
        "CIK0000749251.json", "CIK0000749251-submissions-001.json"]
    assert list(acc["documents_unread"]) == [
        "https://data.sec.gov/submissions/CIK0000749251-submissions-002.json"]
    assert acc["stated"] + acc["unstated"] == acc["accessions"] == e["filings"]["rows"] + acc[
        "unstated"]
    assert acc["stated"] == 5 and acc["unstated"] == 60
    assert set(acc["unstated_named"].values()) == {"listed by no submissions document read"}


def test_rfl_d2_a_filing_accepted_after_the_close_is_not_in_that_days_cut(
        it_store: FactStore) -> None:
    """REAL: IT's FY2021 10-K 0000749251-22-000006, filed 2022-02-23, accepted 21:37:11 UTC
    (16:37 EST). At that day's 16:00 close it was not public; at 16:40 and the next day it is."""
    rows = it_store.latest(IT, date(2022, 2, 24), stale_ok=True)
    keys = [k for k, f in rows.items()
            if not isinstance(f, Exception) and f.accession == "0000749251-22-000006"]
    assert keys, "the 10-K's facts are in the next day's cut"
    k = keys[0]
    period = Period(end=k[5], start=k[4])
    concept = f"{k[1]}:{k[2]}"
    at_close = it_store.latest(IT, date(2022, 2, 23), stale_ok=True).get(k)
    assert at_close is None or getattr(at_close, "accession", None) != "0000749251-22-000006"
    after = datetime(2022, 2, 23, 21, 40, tzinfo=UTC)
    f = it_store.get(IT, concept, period, after, unit=k[3], stale_ok=True)
    assert f.accession == "0000749251-22-000006"
    assert f.accepted_at == datetime(2022, 2, 23, 21, 37, 11, tzinfo=UTC)
    # the day-level cut, the page's, still sees it at the close
    by_day = it_store.get(IT, concept, period, date(2022, 2, 23), unit=k[3], basis=FILED,
                          stale_ok=True)
    assert by_day.accession == "0000749251-22-000006"


def test_rfl_d2_negative_a_filing_accepted_before_the_close_is_in_its_days_cut(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cik = "0000999999"
    facts = {"cik": 999999, "entityName": "Constructed", "facts": {"us-gaap": {
        "Revenues": {"units": {"USD": [
            _row("2025-12-31", 900.0, "0000999999-26-000001", "2026-02-20",
                 start="2025-01-01"),
            _row("2024-12-31", 800.0, "0000999999-26-000002", "2026-02-20", form="10-K/A",
                 start="2024-01-01")]}}}}}
    sub = {"cik": cik, "filings": {"files": [], "recent": {
        "accessionNumber": ["0000999999-26-000001", "0000999999-26-000002"],
        "filingDate": ["2026-02-20", "2026-02-20"], "form": ["10-K", "10-K/A"],
        # 15:00 EST (before the close) and 16:30 EST (after it)
        "acceptanceDateTime": ["2026-02-20T20:00:00.000Z", "2026-02-20T21:30:00.000Z"]}}}
    _pages_dir(tmp_path, {"XYZ": cik})
    cache = _cache(tmp_path, {_cf_url(cik): json.dumps(facts), _sub_url(cik): json.dumps(sub)})
    assert _ingest(tmp_path, monkeypatch, cache) == 0
    with FactStore(facts_base=tmp_path / "data" / "facts",
                   root=tmp_path / "data" / "facts" / "objects") as s:
        fy25 = Period.duration(date(2025, 1, 1), date(2025, 12, 31))
        fy24 = Period.duration(date(2024, 1, 1), date(2024, 12, 31))
        assert s.get(cik, "us-gaap:Revenues", fy25, date(2026, 2, 20)).value == 900.0
        with pytest.raises(FactUnknownError):
            s.get(cik, "us-gaap:Revenues", fy24, date(2026, 2, 20))
        assert s.get(cik, "us-gaap:Revenues", fy24, date(2026, 2, 23)).value == 800.0


def test_rfl_d2_a_datetime_cut_must_say_its_zone() -> None:
    with pytest.raises(ValueError, match="no time zone"):
        cut_instant(datetime(2026, 2, 20, 16, 0))
    assert cut_instant(date(2026, 2, 20)) == datetime(2026, 2, 20, 21, 0)      # EST
    assert cut_instant(date(2026, 7, 20)) == datetime(2026, 7, 20, 20, 0)      # EDT


def test_rfl_d2_a_frame_names_an_entity_it_cannot_place(pages: FactStore) -> None:
    got = pages.frame(SHARES, Period.instant(date(2017, 3, 2)), date(2017, 3, 8),
                      entities=[TGT], stale_ok=True)
    assert list(got.undetermined) == [TGT] and got.facts == {} and got.unknown == ()


def _one_filer(tmp: Path, monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]],
               listed: list[tuple[str, str, str, str]]) -> int:
    """Ingest a constructed filer (CIK 0000999999) whose submissions recent page lists
    ``listed`` = [(accession, filingDate, form, acceptanceDateTime)]."""
    cik = "0000999999"
    facts = {"cik": 999999, "entityName": "Constructed",
             "facts": {"us-gaap": {"Revenues": {"units": {"USD": rows}}}}}
    sub = {"cik": cik, "filings": {"files": [], "recent": {
        "accessionNumber": [x[0] for x in listed], "filingDate": [x[1] for x in listed],
        "form": [x[2] for x in listed], "acceptanceDateTime": [x[3] for x in listed]}}}
    _pages_dir(tmp, {"XYZ": cik})
    return _ingest(tmp, monkeypatch, _cache(tmp, {_cf_url(cik): json.dumps(facts),
                                                  _sub_url(cik): json.dumps(sub)}))


def test_rfl_d2_a_later_visible_filing_wins_over_an_unplaced_same_day_one(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review round 0: a key was refused whenever any row in its cut was unplaced, though a
    filing of a LATER day in the cut supersedes it whatever its time. Filing A is dated
    2026-02-20 and no document lists it; filing B was accepted 2026-02-20 18:00 EST, after the
    17:30 rule, so SEC dates it 2026-02-23. A cut at 2026-02-20 23:00 New York serves B."""
    fy = Period.duration(date(2025, 1, 1), date(2025, 12, 31))
    rows = [_row("2025-12-31", 900.0, "0000999999-26-000001", "2026-02-20", start="2025-01-01"),
            _row("2025-12-31", 950.0, "0000999999-26-000002", "2026-02-23", form="10-K/A",
                 start="2025-01-01")]
    assert _one_filer(tmp_path, monkeypatch, rows, [
        ("0000999999-26-000002", "2026-02-23", "10-K/A", "2026-02-20T23:00:00.000Z")]) == 0
    with FactStore(facts_base=tmp_path / "data" / "facts",
                   root=tmp_path / "data" / "facts" / "objects") as s:
        late = datetime(2026, 2, 21, 4, 0, tzinfo=UTC)          # 2026-02-20 23:00 EST
        got = s.get("0000999999", "us-gaap:Revenues", fy, late)
        assert (got.value, got.accession) == (950.0, "0000999999-26-000002")
        # NEGATIVE: at the 2026-02-20 close B is not public, and A cannot be placed
        with pytest.raises(FactCutUndeterminedError, match="0000999999-26-000001"):
            s.get("0000999999", "us-gaap:Revenues", fy, date(2026, 2, 20))


def test_rfl_d2_an_odd_time_on_a_filing_no_row_carries_does_not_stop_the_ingest(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review round 0: every filing a submissions page lists was parsed strictly, so one odd
    acceptance time on a Form 4 the store never reads stopped the whole ingest."""
    rows = [_row("2025-12-31", 900.0, "0000999999-26-000001", "2026-02-20", start="2025-01-01")]
    assert _one_filer(tmp_path, monkeypatch, rows, [
        ("0000999999-26-000001", "2026-02-20", "10-K", "2026-02-20T20:00:00.000Z"),
        ("0000999999-26-000099", "2026-02-21", "4", "not a time")]) == 0


def test_rfl_d2_negative_an_odd_time_on_a_filing_a_row_carries_stops_the_ingest(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    rows = [_row("2025-12-31", 900.0, "0000999999-26-000001", "2026-02-20", start="2025-01-01")]
    assert _one_filer(tmp_path, monkeypatch, rows, [
        ("0000999999-26-000001", "2026-02-20", "10-K", "not a time")]) == 1
    assert "acceptanceDateTime 'not a time'" in capsys.readouterr().out


# --- RFL-D4: the reader verifies what the manifest seals ---------------------------------------

def _edited_copy(tmp: Path, *, recompute_id: bool) -> tuple[Path, str]:
    """A copy of the committed facts in which one data object holds one value x10, as valid
    Parquet, its manifest entry's sha256 and size updated to match (the audit's E2 (d))."""
    facts = tmp / "facts"
    shutil.copytree(COMMITTED, facts)
    m = load_manifest(PAGES_ID, base=facts)
    entry = next(f for f in m["files"] if f["entity"] == NFLX and f["filed_year"] == 2025)
    p = facts / "objects" / entry["path"]
    table = pq.read_table(p)
    rows = table.to_pylist()
    rows[0]["value"] = rows[0]["value"] * 10
    buf = io.BytesIO()
    pq.write_table(table.from_pylist(rows, schema=table.schema), buf)
    p.write_bytes(buf.getvalue())
    entry["sha256"], entry["bytes"] = _sha256_file(p), p.stat().st_size
    sid = PAGES_ID
    if recompute_id:
        m["snapshot_id"] = sid = snapshot_id_for(m)
        write_manifest(m, facts)
    else:
        (facts / "manifests" / f"{PAGES_ID}.json").write_text(json.dumps(m, indent=2))
    return facts, sid


def test_rfl_d4_a_consistent_object_and_entry_edit_is_refused_on_open(tmp_path: Path) -> None:
    facts, sid = _edited_copy(tmp_path, recompute_id=False)
    with pytest.raises(FactsStoreError, match="does not recompute to its id"):
        FactStore(sid, facts_base=facts, root=facts / "objects")


def test_rfl_d4_an_edit_under_a_new_id_is_refused_by_its_rows(tmp_path: Path) -> None:
    """The id recomputes, so the manifest is self-consistent: only the rows, hashed against the
    object's content-addressed NAME, can show the edit."""
    facts, sid = _edited_copy(tmp_path, recompute_id=True)
    with FactStore(sid, facts_base=facts, root=facts / "objects") as s, \
            pytest.raises(FactsStoreError, match="rows do not hash to its name"):
        s.latest(NFLX, date(2026, 1, 31), basis=FILED, stale_ok=True)


def test_rfl_d4_negative_the_committed_snapshot_opens_and_reads(pages: FactStore) -> None:
    assert pages.latest(NFLX, date(2025, 6, 30), basis=FILED, stale_ok=True)


# --- RFL-D5: not held is not "nothing filed" ----------------------------------------------------

@pytest.mark.parametrize("cik", ["0001579298", "0000927653"])     # BURL, MCK: pages, not held
def test_rfl_d5_a_company_the_snapshot_does_not_hold_is_not_held(pages: FactStore,
                                                                  cik: str) -> None:
    """REAL: two committed pages' companies are not in the pages snapshot."""
    with pytest.raises(FactNotHeldError, match="not in snapshot"):
        pages.get(cik, "us-gaap:Assets", Period.instant(date(2025, 12, 31)), date(2026, 1, 31))
    with pytest.raises(FactNotHeldError):
        pages.companyfacts_as_of(cik, date(2026, 1, 31))


def test_rfl_d5_negative_a_held_company_with_nothing_filed_is_unknown(pages: FactStore) -> None:
    with pytest.raises(FactUnknownError, match="nothing filed by"):
        pages.get(NFLX, "us-gaap:Assets", Period.instant(date(1990, 12, 31)), date(2026, 1, 31),
                  unit="USD", stale_ok=True)


# --- RFL-D6: the upload checks the source --------------------------------------------------------

class _NoRequests:
    """An R2 client that fails the test on any request."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"a request was made: {name}")


def _ciq_manifest() -> dict[str, Any]:
    m = copy.deepcopy(load_manifest(PAGES_ID, base=COMMITTED))
    m["source"] = "ciq"
    for f in m["files"]:
        f["source"] = "ciq"
        f["path"] = "ciq" + f["path"][len("edgar"):]
    for e in m["entities"]:
        e["order"]["path"] = "ciq" + e["order"]["path"][len("edgar"):]
    m["snapshot_id"] = snapshot_id_for(m)
    return m


def test_rfl_d6_a_ciq_snapshot_is_refused_before_any_request(tmp_path: Path) -> None:
    m = _ciq_manifest()
    assert "source 'ciq' has no writer in this code" in str(upload_refusal(m))
    with pytest.raises(FactsStoreError, match="nothing was uploaded — source 'ciq'"):
        upload_snapshot(m, tmp_path, _NoRequests())  # type: ignore[arg-type]


def test_rfl_d6_an_object_outside_the_source_is_refused() -> None:
    m = copy.deepcopy(load_manifest(PAGES_ID, base=COMMITTED))
    m["files"][0]["source"] = "ciq"
    assert "1 object(s) it names are not source 'edgar''s" in str(upload_refusal(m))
    m = copy.deepcopy(load_manifest(PAGES_ID, base=COMMITTED))
    m["extractor"] = "someone.elses.writer"
    assert "is not source 'edgar''s writer" in str(upload_refusal(m))


def test_rfl_d6_negative_the_committed_edgar_snapshots_may_be_uploaded() -> None:
    for sid in json.loads((COMMITTED / "current.json").read_text()).values():
        assert upload_refusal(load_manifest(sid, base=COMMITTED)) is None


# --- RFL-D7 and RFL-D8: parity states the real cause ---------------------------------------------

def _publish(facts: Path, blob: dict[str, Any], text: str) -> dict[str, Any]:
    got = rows_from_companyfacts(blob)
    files, orders = write_partitions(got.rows, facts / "objects")
    m = build_manifest(source=SOURCE, extractor=EXTRACTOR, extractor_version=EXTRACTOR_VERSION,
                       scope={"rule": "test"}, files=files, orders=orders, entities=[{
                           "entity": got.entity, "rows_kept": len(got.rows),
                           "fetched_at": "2027-01-02T00:00:00Z",
                           "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                           "exact_duplicates_dropped": got.exact_duplicates_dropped}])
    write_manifest(m, facts)
    return m


def _nflx_slice() -> tuple[dict[str, Any], str]:
    text = (FIX / "facts" / "NFLX-companyfacts-slice.json").read_text()
    return json.loads(text), text


def _parity(tmp: Path, cache_text: str) -> Any:
    from vinci.facts.parity import compare_page
    cache = _cache(tmp, {_cf_url(NFLX): cache_text})
    with FactStore(facts_base=tmp / "facts", root=tmp / "facts" / "objects") as s:
        return compare_page("NFLX", {"cik": NFLX, "reference_date": "2026-11-02"}, s, cache,
                            at=date(2026, 11, 2))


def test_rfl_d7_a_refreshed_copy_is_reported_changed_not_as_store_differences(
        tmp_path: Path) -> None:
    blob, text = _nflx_slice()
    m = _publish(tmp_path / "facts", blob, text)
    newer = copy.deepcopy(blob)
    tag = next(iter(newer["facts"]["us-gaap"].values()))
    next(iter(tag["units"].values())).append(_row("2026-09-30", 1.0, "0001065280-26-999999",
                                                  "2026-10-20", form="10-Q"))
    r = _parity(tmp_path, json.dumps(newer))
    assert r.changed is not None and r.unread is None and not r.zero_diff
    assert f"the snapshot's copy was fetched {m['entities'][0]['fetched_at']}" in r.changed
    assert (r.row_diffs, r.fetched_at) == (0, m["entities"][0]["fetched_at"])


def test_rfl_d7_negative_the_ingested_copy_is_compared(tmp_path: Path) -> None:
    blob, text = _nflx_slice()
    _publish(tmp_path / "facts", blob, text)
    r = _parity(tmp_path, text)
    assert r.changed is None and r.zero_diff and r.rows_compared > 0


def _with_duplicate(blob: dict[str, Any]) -> dict[str, Any]:
    dup = copy.deepcopy(blob)
    rows = next(iter(next(iter(dup["facts"]["us-gaap"].values()))["units"].values()))
    rows.append(copy.deepcopy(rows[0]))
    return dup


def test_rfl_d8_an_exact_duplicate_the_ingest_holds_once_is_named_not_a_difference(
        tmp_path: Path) -> None:
    blob, _ = _nflx_slice()
    dup = _with_duplicate(blob)
    text = json.dumps(dup)
    m = _publish(tmp_path / "facts", dup, text)
    assert m["entities"][0]["exact_duplicates_dropped"] == 1
    r = _parity(tmp_path, text)
    assert (r.duplicates_held_once, r.duplicates_dropped_by_ingest, r.row_diffs) == (1, 1, 0)
    assert r.zero_diff


def test_rfl_d8_negative_a_duplicate_the_snapshot_does_not_account_for_is_a_difference(
        tmp_path: Path) -> None:
    blob, _ = _nflx_slice()
    dup = _with_duplicate(blob)
    text = json.dumps(dup)
    facts = tmp_path / "facts"
    got = rows_from_companyfacts(dup)
    files, orders = write_partitions(got.rows, facts / "objects")
    write_manifest(build_manifest(
        source=SOURCE, extractor=EXTRACTOR, extractor_version=EXTRACTOR_VERSION,
        scope={"rule": "test"}, files=files, orders=orders, entities=[{
            "entity": got.entity, "rows_kept": len(got.rows), "fetched_at": "2027-01-02T00:00:00Z",
            "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "exact_duplicates_dropped": 0}]), facts)
    r = _parity(tmp_path, text)
    assert r.duplicates_held_once == 1 and not r.zero_diff


# --- RFL-D9 and RFL-D10: the ingest's failures --------------------------------------------------

def test_rfl_d9_an_unknown_shape_row_writes_nothing(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch,
                                                    capsys: pytest.CaptureFixture[str]) -> None:
    """Two companies, the SECOND (its CIK sorts after NFLX's) carrying a row with a key no
    companyfacts row has. On main the ingest wrote NFLX's objects, then aborted with no manifest:
    19 objects left on disk, which no manifest names (the audit's run: 6)."""
    good, _ = _nflx_slice()
    bad = {"cik": 9999999, "entityName": "Constructed", "facts": {"us-gaap": {"Revenues": {
        "units": {"USD": [{**_row("2025-12-31", 1.0, "0009999999-26-000001", "2026-02-20"),
                           "segment": "X"}]}}}}}
    _pages_dir(tmp_path, {"NFLX": NFLX, "XYZ": "0009999999"})
    cache = _cache(tmp_path, {_cf_url(NFLX): json.dumps(good),
                              _cf_url("0009999999"): json.dumps(bad)})
    assert _ingest(tmp_path, monkeypatch, cache) == 1
    out = capsys.readouterr().out
    assert "SHAPE XYZ 0009999999: IngestShapeError" in out and "unknown keys ['segment']" in out
    assert "nothing written" in out
    objects = tmp_path / "data" / "facts" / "objects"
    assert not objects.exists() or not any(p.is_file() for p in objects.rglob("*"))
    assert not (tmp_path / "data" / "facts" / "current.json").exists()


def test_rfl_d9_a_response_for_another_cik_writes_nothing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """The writing pass's CIK check ran after earlier companies' objects were written: a cached
    response for another CIK, sorting after NFLX, left NFLX's objects with no manifest."""
    good, _ = _nflx_slice()
    other = {"cik": 8888888, "entityName": "Constructed", "facts": {"us-gaap": {"Revenues": {
        "units": {"USD": [_row("2025-12-31", 1.0, "0008888888-26-000001", "2026-02-20")]}}}}}
    _pages_dir(tmp_path, {"NFLX": NFLX, "XYZ": "0009999999"})
    cache = _cache(tmp_path, {_cf_url(NFLX): json.dumps(good),
                              _cf_url("0009999999"): json.dumps(other)})
    assert _ingest(tmp_path, monkeypatch, cache) == 1
    out = capsys.readouterr().out
    assert "SHAPE XYZ 0009999999: the cached response is for CIK 0008888888" in out
    objects = tmp_path / "data" / "facts" / "objects"
    assert not objects.exists() or not any(p.is_file() for p in objects.rglob("*"))
    assert not (tmp_path / "data" / "facts" / "current.json").exists()


def test_rfl_d9_negative_clean_responses_are_written(tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    good, text = _nflx_slice()
    _pages_dir(tmp_path, {"NFLX": NFLX})
    assert _ingest(tmp_path, monkeypatch, _cache(tmp_path, {_cf_url(NFLX): text})) == 0
    cur = json.loads((tmp_path / "data" / "facts" / "current.json").read_text())
    m = load_manifest(cur["edgar"], base=tmp_path / "data" / "facts")
    # no submissions document cached: every accession is stated without a time, and why
    (e,) = m["entities"]
    assert e["acceptance"]["stated"] == 0 and e["filings"]["rows"] == 0
    assert set(e["acceptance"]["unstated_named"].values()) == {
        "no submissions document in the SEC cache"}


@pytest.mark.parametrize(("response", "why"), [
    ({"cik": 999999, "entityName": "X"}, "has no 'facts' key (its keys: ['cik', 'entityName'])"),
    ({"cik": 999999, "facts": {}}, "'facts' holds no fact row"),
    ({"cik": 999999, "facts": {"us-gaap": {"Revenues": {"units": {"USD": [
        {k: v for k, v in _row("2025-12-31", 1.0, "0000999999-26-000001", "2026-02-20").items()
         if k != "filed"} | {"filed": None}]}}}}}, "1 fact rows all lack a filed date"),
])
def test_rfl_d10_an_unread_response_names_its_real_cause(response: dict[str, Any],
                                                         why: str) -> None:
    assert why in unread_reason(response, rows_from_companyfacts(response))


def test_rfl_d10_the_cli_records_the_cause_in_the_manifest(tmp_path: Path,
                                                           monkeypatch: pytest.MonkeyPatch) -> None:
    good, text = _nflx_slice()
    _pages_dir(tmp_path, {"NFLX": NFLX, "XYZ": "0000999999"})
    cache = _cache(tmp_path, {_cf_url(NFLX): text,
                              _cf_url("0000999999"): json.dumps({"cik": 999999,
                                                                 "entityName": "X"})})
    assert _ingest(tmp_path, monkeypatch, cache) == 0
    cur = json.loads((tmp_path / "data" / "facts" / "current.json").read_text())
    m = load_manifest(cur["edgar"], base=tmp_path / "data" / "facts")
    (u,) = m["scope"]["unread"]
    assert u["ticker"] == "XYZ" and "has no 'facts' key" in u["reason"]
