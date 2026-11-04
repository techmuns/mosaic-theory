"""The fact layer's as-of pins, on FROZEN slices of two real cached companyfacts responses.

Fixtures (`tests/fixtures/facts/`, each carrying its provenance in `_note`):
- NFLX: FY2023 diluted EPS 12.03 as filed 2024-01-26 (accn …-24-000030) and 2025-01-27
  (…-25-000044), then 1.2 as RESTATED 2026-01-23 (…-26-000034) after the stock split.
- FUBO: the 2019-12-31 unamortized discount stated 710000 by a 10-K/A (…-20-015142) and 456000
  by a 10-Q/A (…-20-015144), BOTH filed 2020-08-11, so on that day no filing is latest.

Every assertion reads values out of those real rows; none is hand-rolled.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.edgar.concepts import facts_as_of
from vinci.facts import (
    FactAmbiguousError,
    FactStore,
    FactUnknownError,
    Period,
    RemoteStoreNotConfiguredError,
)
from vinci.facts.edgar_ingest import (
    EXTRACTOR,
    EXTRACTOR_VERSION,
    SOURCE,
    IngestShapeError,
    NotInCacheError,
    read_cached,
    rows_from_companyfacts,
)
from vinci.facts.parity import reference_latest
from vinci.facts.scope import scope_names
from vinci.facts.store import (
    FactsStoreError,
    build_manifest,
    parquet_bytes,
    store_root,
    verify_manifest,
    write_manifest,
    write_object,
    write_partitions,
)
from vinci.netcache import CachedHttp

FIX = Path(__file__).parent / "fixtures" / "facts"
NFLX, FUBO = "0001065280", "0001484769"
EPS = "us-gaap:EarningsPerShareDiluted"
FY2023 = Period.duration(date(2023, 1, 1), date(2023, 12, 31))
DISCOUNT = "us-gaap:DebtInstrumentUnamortizedDiscountCurrent"
YE2019 = Period.instant(date(2019, 12, 31))


def _load(name: str) -> dict[str, Any]:
    blob: dict[str, Any] = json.loads((FIX / name).read_text())
    return blob


def _publish(tmp: Path, blobs: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    entities = []
    for b in blobs:
        got = rows_from_companyfacts(b)
        rows += got.rows
        entities.append({"entity": got.entity, "rows_kept": len(got.rows)})
    files = write_partitions(rows, tmp / "objects")
    manifest = build_manifest(source=SOURCE, extractor=EXTRACTOR,
                              extractor_version=EXTRACTOR_VERSION, scope={"rule": "test"},
                              entities=entities, files=files)
    write_manifest(manifest, tmp)
    return manifest


@pytest.fixture
def store(tmp_path: Path) -> FactStore:
    _publish(tmp_path, [_load("NFLX-companyfacts-slice.json"),
                        _load("FUBO-companyfacts-slice.json")])
    return FactStore(facts_base=tmp_path, root=tmp_path / "objects")


# --- a fact filed after the as-of is absent ------------------------------------------------------

def test_a_fact_filed_after_the_as_of_is_absent(store: FactStore) -> None:
    """NEGATIVE: the day before FY2023's EPS was first filed, nothing is knowable."""
    with pytest.raises(FactUnknownError, match="nothing filed by 2024-01-25"):
        store.get(NFLX, EPS, FY2023, date(2024, 1, 25))


def test_the_filing_day_itself_is_inside_the_cut(store: FactStore) -> None:
    """POSITIVE: `filed == as_of` is kept, as in facts_as_of."""
    f = store.get(NFLX, EPS, FY2023, date(2024, 1, 26))
    assert (f.value, f.accession, f.filed_date) == (
        12.03, "0001065280-24-000030", date(2024, 1, 26))


def test_a_frame_query_cuts_the_same_way(store: FactStore) -> None:
    before = store.frame(EPS, FY2023, date(2024, 1, 25), entities=[NFLX, FUBO])
    assert before.facts == {} and before.unknown == (NFLX, FUBO)
    after = store.frame(EPS, FY2023, date(2024, 3, 5), entities=[NFLX, FUBO])
    assert {e: f.value for e, f in after.facts.items()} == {NFLX: 12.03, FUBO: -1.04}
    assert after.unknown == ()


# --- a restated value: the later filing at a later as-of, the earlier at an earlier one ---------

def test_a_restated_value_returns_the_earlier_filing_at_an_earlier_as_of(store: FactStore) -> None:
    f = store.get(NFLX, EPS, FY2023, date(2026, 1, 22))
    assert (f.value, f.accession, f.filed_date) == (
        12.03, "0001065280-25-000044", date(2025, 1, 27))


def test_a_restated_value_returns_the_later_filing_at_a_later_as_of(store: FactStore) -> None:
    f = store.get(NFLX, EPS, FY2023, date(2026, 1, 23))
    assert (f.value, f.accession, f.filed_date) == (1.2, "0001065280-26-000034", date(2026, 1, 23))
    assert f.snapshot_id == store.snapshot_id
    assert str(f.source_ref) == (
        "EDGAR XBRL us-gaap:EarningsPerShareDiluted accn 0001065280-26-000034")


def test_every_filing_version_is_kept(store: FactStore) -> None:
    rows = store.companyfacts_as_of(NFLX, date(2026, 12, 31))["facts"]["us-gaap"][
        "EarningsPerShareDiluted"]["units"]["USD/shares"]
    fy23 = [(r["val"], r["accn"]) for r in rows
            if r.get("start") == "2023-01-01" and r["end"] == "2023-12-31"]
    assert fy23 == [(12.03, "0001065280-24-000030"), (12.03, "0001065280-25-000044"),
                    (1.2, "0001065280-26-000034")]


# --- a missing concept is UNKNOWN; a same-day disagreement is refused ----------------------------

def test_a_missing_concept_raises_unknown(store: FactStore) -> None:
    with pytest.raises(FactUnknownError):
        store.get(NFLX, "us-gaap:NoSuchConcept", FY2023, date(2026, 12, 31))


def test_a_missing_period_raises_unknown(store: FactStore) -> None:
    with pytest.raises(FactUnknownError):
        store.get(NFLX, EPS, Period.duration(date(1990, 1, 1), date(1990, 12, 31)),
                  date(2026, 12, 31))


def test_an_entity_outside_the_snapshot_raises_unknown(store: FactStore) -> None:
    with pytest.raises(FactUnknownError, match="not in snapshot"):
        store.get(320193, EPS, FY2023, date(2026, 12, 31))
    outside = store.frame(EPS, FY2023, date(2026, 12, 31), entities=[320193])
    assert outside.unknown == ("0000320193",)


def test_an_unqualified_concept_is_refused(store: FactStore) -> None:
    with pytest.raises(ValueError, match="qualified"):
        store.get(NFLX, "EarningsPerShareDiluted", FY2023, date(2026, 12, 31))


def test_a_same_day_disagreement_is_ambiguous_never_chosen(store: FactStore) -> None:
    """NEGATIVE: a 10-K/A (710000) and a 10-Q/A (456000) both filed 2020-08-11."""
    with pytest.raises(FactAmbiguousError, match="0001493152-20-015142"):
        store.get(FUBO, DISCOUNT, YE2019, date(2020, 8, 11))
    fr = store.frame(DISCOUNT, YE2019, date(2020, 8, 11), entities=[FUBO])
    assert FUBO in fr.ambiguous and fr.facts == {} and fr.unknown == ()


def test_the_disagreement_resolves_when_a_later_filing_lands(store: FactStore) -> None:
    """POSITIVE on both sides of the ambiguous day."""
    assert store.get(FUBO, DISCOUNT, YE2019, date(2020, 8, 10)).value == 456000
    later = store.get(FUBO, DISCOUNT, YE2019, date(2020, 8, 13))
    assert (later.value, later.accession) == (710000, "0001493152-20-015517")


# --- the store reproduces facts_as_of row for row ------------------------------------------------

@pytest.mark.parametrize("as_of", [date(2019, 6, 30), date(2020, 8, 11), date(2024, 1, 26),
                                   date(2026, 1, 22), date(2026, 1, 23), date(2026, 12, 31)])
@pytest.mark.parametrize("name", ["NFLX-companyfacts-slice.json", "FUBO-companyfacts-slice.json"])
def test_the_store_reproduces_facts_as_of(store: FactStore, name: str, as_of: date) -> None:
    blob = _load(name)
    want = {ns: {t: b["units"] for t, b in tags.items()}
            for ns, tags in facts_as_of(blob, as_of)["facts"].items()}
    got = {ns: {t: b["units"] for t, b in tags.items()}
           for ns, tags in store.companyfacts_as_of(blob["cik"], as_of)["facts"].items()}
    assert got == want


def test_latest_agrees_with_the_plain_python_reference(store: FactStore) -> None:
    as_of = date(2020, 8, 11)
    ref = reference_latest(facts_as_of(_load("FUBO-companyfacts-slice.json"), as_of))
    got = store.latest(FUBO, as_of)
    assert len(got) == len(ref) > 0
    ambiguous = [k for k, v in got.items() if isinstance(v, FactAmbiguousError)]
    assert [(k[2], k[5]) for k in ambiguous] == [("DebtInstrumentUnamortizedDiscountCurrent",
                                                 date(2019, 12, 31))]


# --- ingest: every version kept, only exact duplicates dropped, unknown shapes refused ----------

def test_ingest_keeps_every_row_and_drops_only_exact_duplicates() -> None:
    blob = _load("NFLX-companyfacts-slice.json")
    n = sum(len(r) for ns in blob["facts"].values() for b in ns.values()
            for r in b["units"].values())
    assert len(rows_from_companyfacts(blob).rows) == n
    rows = blob["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"]
    rows.append(dict(rows[0]))                         # an EXACT duplicate of a real row
    rows.append({**rows[1], "val": rows[1]["val"] + 1})  # same period, different value: kept
    got = rows_from_companyfacts(blob)
    assert (len(got.rows), got.exact_duplicates_dropped) == (n + 1, 1)


def test_ingest_refuses_a_row_it_could_not_replay() -> None:
    blob = _load("NFLX-companyfacts-slice.json")
    blob["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"][0]["segment"] = "x"
    with pytest.raises(IngestShapeError, match="unknown keys"):
        rows_from_companyfacts(blob)


def test_a_row_with_no_filed_date_is_dropped_and_counted() -> None:
    blob = _load("NFLX-companyfacts-slice.json")
    blob["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"][0].pop("filed")
    assert rows_from_companyfacts(blob).rows_without_filed == 1


# --- the store: immutable, content-addressed, deterministic, verified ----------------------------

def test_the_same_rows_write_the_same_object(tmp_path: Path) -> None:
    rows = rows_from_companyfacts(_load("FUBO-companyfacts-slice.json")).rows
    assert parquet_bytes(rows) == parquet_bytes(list(reversed(rows)))
    a = write_partitions(rows, tmp_path / "a")
    b = write_partitions(rows, tmp_path / "a")      # a second write is a no-op
    assert a == b


def test_an_object_is_never_overwritten(tmp_path: Path) -> None:
    write_object(tmp_path, "x.parquet", b"one")
    write_object(tmp_path, "x.parquet", b"one")
    with pytest.raises(FactsStoreError, match="corrupted"):
        write_object(tmp_path, "x.parquet", b"two")
    assert (tmp_path / "x.parquet").read_bytes() == b"one"


def test_the_snapshot_id_is_derived_from_content(tmp_path: Path) -> None:
    one = _publish(tmp_path / "1", [_load("FUBO-companyfacts-slice.json")])
    two = _publish(tmp_path / "2", [_load("FUBO-companyfacts-slice.json")])
    assert one["snapshot_id"] == two["snapshot_id"] and one["snapshot_id"].startswith("edgar-")


def test_verify_passes_a_clean_snapshot_and_names_a_tampered_object(tmp_path: Path) -> None:
    manifest = _publish(tmp_path, [_load("FUBO-companyfacts-slice.json")])
    root = tmp_path / "objects"
    assert verify_manifest(manifest, root) == []
    victim = root / manifest["files"][0]["path"]
    victim.write_bytes(victim.read_bytes()[:-1] + b"\0")
    assert any("sha256 does not match" in p for p in verify_manifest(manifest, root))
    with pytest.raises(FactsStoreError, match="do not match snapshot"):
        FactStore(facts_base=tmp_path, root=root).companyfacts_as_of(FUBO, date(2026, 1, 1))


def test_a_remote_store_is_refused_until_one_is_configured() -> None:
    with pytest.raises(RemoteStoreNotConfiguredError, match="R2"):
        store_root("r2://facts")


# --- the cache is read, never fetched ------------------------------------------------------------

def test_the_ingest_reads_the_cache_and_never_fetches(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    def no_network(*_a: object, **_k: object) -> str:
        raise AssertionError("the fact layer fetched")

    monkeypatch.setattr(CachedHttp, "_fetch_with_retries", no_network)
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001484769.json"
    with pytest.raises(NotInCacheError):
        read_cached(url, tmp_path)
    (tmp_path / "sec").mkdir()
    with pytest.raises(NotInCacheError):
        read_cached(url, tmp_path)
    with CachedHttp(cache_dir=tmp_path, user_agent="t", min_interval_sec=0, namespace="sec") as h:
        h._write_cache(url, (FIX / "FUBO-companyfacts-slice.json").read_text())
    got = read_cached(url, tmp_path)
    assert json.loads(got.text)["cik"] == 1484769 and got.fetched_at.year >= 2026


# --- the scope reads the follow list through its own reader --------------------------------------

def test_a_tombstoned_follow_leaves_the_scope(tmp_path: Path) -> None:
    """A name unfollowed by `followed_until` (the follow list's documented removal) is not in scope;
    a still-followed name with a page is. Review round 0: the raw keys of followed.json counted
    both."""
    pages = tmp_path / "dossiers"
    (pages / "FUBO").mkdir(parents=True)
    (pages / "FUBO" / "dossier.json").write_text(json.dumps({"cik": "0001484769"}))
    followed = tmp_path / "followed.json"
    followed.write_text(json.dumps({
        "FUBO": {"followed_since": "2026-01-01", "sleeve": "quality", "reason": "r"},
        "NFLX": {"followed_since": "2026-01-01", "followed_until": "2026-02-01",
                 "sleeve": "quality", "reason": "r"}}))
    names, excluded = scope_names(pages, followed, tmp_path / "no-cache")
    assert [(n.ticker, n.cik, n.followed) for n in names] == [("FUBO", "0001484769", True)]
    assert excluded == 0


# --- review round 1 ----------------------------------------------------------------------------

def test_a_page_the_parity_cannot_read_is_reported_not_raised(store: FactStore,
                                                              tmp_path: Path) -> None:
    """One page whose companyfacts is not cached is reported as unread (and not zero-diff); it
    does not abort the run for every other page."""
    from vinci.facts.parity import compare_page
    doc = {"cik": "0001484769", "reference_date": "2026-01-02", "mechanical": {}}
    got = compare_page("FUBO", doc, store, tmp_path / "no-cache")
    assert got.unread and "cache" in got.unread
    assert not got.zero_diff


def test_verify_names_an_entity_whose_rows_disagree_with_its_files(tmp_path: Path) -> None:
    manifest = _publish(tmp_path, [_load("FUBO-companyfacts-slice.json")])
    assert verify_manifest(manifest, tmp_path / "objects") == []
    manifest["entities"][0]["rows_kept"] += 1
    assert any("rows_kept" in p for p in verify_manifest(manifest, tmp_path / "objects",
                                                         check_objects=False))
