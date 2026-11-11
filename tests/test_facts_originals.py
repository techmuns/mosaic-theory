"""TeamNostra fix request 2, RFL-D3: the fact layer keeps the originals it read, write-once.

Operator ruling 2026-11-11: "Keep the pages' originals (Recommended)". Every response an ingest
reads (each company's companyfacts, and each submissions document its acceptance times come
from) is kept by the sha256 of its stored bytes, recorded in the manifest with its own sha256,
URL and fetch time, uploaded to R2 beside the snapshot, and read back to rebuild a fact. The
inputs are the committed fixtures (NFLX's companyfacts slice; Gartner's companyfacts and
submissions pages).
"""
from __future__ import annotations

import gzip
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.test_facts_remote import FakeBucket, _client
from vinci.edgar.concepts import facts_as_of
from vinci.facts import FILED, FactStore, Period
from vinci.facts.edgar_ingest import CachedResponse
from vinci.facts.originals import (
    keep,
    manifest_originals,
    originals_root,
    read_original,
    stored_bytes,
    verify_originals,
)
from vinci.facts.remote import check_key, manifest_objects, upload_snapshot
from vinci.facts.store import FactsStoreError, load_manifest, verify_manifest
from vinci.netcache import CachedHttp

FIX = Path(__file__).resolve().parent / "fixtures"
NFLX, IT = "0001065280", "0000749251"
EPS = "us-gaap:EarningsPerShareDiluted"


def _cache(tmp: Path, entries: dict[str, str]) -> Path:
    cache = tmp / "cache"
    with CachedHttp(cache_dir=cache, user_agent="t", min_interval_sec=0, namespace="sec") as h:
        for url, text in entries.items():
            h._write_cache(url, text)
    return cache


def _ingested(tmp: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """NFLX's slice and Gartner's companyfacts with its two cached submissions pages, ingested
    by the CLI as the pages scope; returns the manifest."""
    from vinci.facts.__main__ import main
    sub = FIX / "submissions_pages"
    cache = _cache(tmp, {
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{NFLX}.json":
            (FIX / "facts" / "NFLX-companyfacts-slice.json").read_text(),
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{IT}.json":
            (FIX / "companyfacts" / "IT.json").read_text(),
        f"https://data.sec.gov/submissions/CIK{IT}.json": (sub / "IT.json").read_text(),
        "https://data.sec.gov/submissions/CIK0000749251-submissions-001.json":
            (sub / "IT-submissions-001.json").read_text(),
    })
    for ticker, cik in (("NFLX", NFLX), ("IT", IT)):
        (tmp / "data" / "dossiers" / ticker).mkdir(parents=True)
        (tmp / "data" / "dossiers" / ticker / "dossier.json").write_text(
            json.dumps({"cik": cik, "reference_date": "2026-11-02"}))
    monkeypatch.chdir(tmp)
    monkeypatch.delenv("VINCI_FACTS_STORE", raising=False)
    assert main(["ingest", "--cache-dir", str(cache)]) == 0
    cur = json.loads((tmp / "data" / "facts" / "current.json").read_text())
    return load_manifest(cur["edgar"], base=tmp / "data" / "facts")


def _resp(text: str) -> CachedResponse:
    return CachedResponse(url="https://data.sec.gov/x.json", text=text,
                          fetched_at=datetime(2026, 11, 11, 4, 0, tzinfo=UTC))


# --- write-once, named by content -----------------------------------------------------------

def test_an_original_is_named_by_its_bytes_and_a_second_put_is_a_no_op(tmp_path: Path) -> None:
    text = (FIX / "facts" / "NFLX-companyfacts-slice.json").read_text()
    a = keep(_resp(text), tmp_path)
    assert a.sha256 == hashlib.sha256(stored_bytes(text)).hexdigest()
    assert a.path == f"originals/sec/{a.sha256}.json.gz"
    assert a.response_sha256 == hashlib.sha256(text.encode()).hexdigest()
    first = (tmp_path / a.path).stat().st_mtime_ns
    assert keep(_resp(text), tmp_path) == a                    # the same body: a no-op
    assert (tmp_path / a.path).stat().st_mtime_ns == first


def test_other_bytes_under_an_originals_name_are_refused_never_overwritten(
        tmp_path: Path) -> None:
    text = (FIX / "facts" / "NFLX-companyfacts-slice.json").read_text()
    a = keep(_resp(text), tmp_path)
    (tmp_path / a.path).write_bytes(b"tampered")
    with pytest.raises(FactsStoreError, match="exists with different bytes"):
        keep(_resp(text), tmp_path)
    assert (tmp_path / a.path).read_bytes() == b"tampered"     # refused, not overwritten


def test_reading_an_original_checks_both_hashes(tmp_path: Path) -> None:
    text = (FIX / "facts" / "NFLX-companyfacts-slice.json").read_text()
    entry = keep(_resp(text), tmp_path).__dict__
    assert read_original(entry, tmp_path) == text
    (tmp_path / entry["path"]).write_bytes(stored_bytes(text + " "))
    with pytest.raises(FactsStoreError, match="do not hash to its name"):
        read_original(entry, tmp_path)
    forged = {**entry, "sha256": hashlib.sha256(stored_bytes(text + " ")).hexdigest()}
    forged["path"] = f"originals/sec/{forged['sha256']}.json.gz"
    (tmp_path / forged["path"]).write_bytes(stored_bytes(text + " "))
    with pytest.raises(FactsStoreError, match="does not hold the response"):
        read_original(forged, tmp_path)


# --- the ingest keeps every response it reads, and records it ---------------------------------

def test_the_ingest_keeps_every_response_it_reads(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    m = _ingested(tmp_path, monkeypatch)
    by = {e["entity"]: e for e in m["entities"]}
    for ent in (NFLX, IT):
        o = by[ent]["original"]
        assert (o["response_sha256"], o["url"], o["fetched_at"]) == (
            by[ent]["response_sha256"], by[ent]["source_url"], by[ent]["fetched_at"])
    docs = by[IT]["acceptance"]["documents"]
    assert [d["url"].rsplit("/", 1)[1] for d in docs] == [
        "CIK0000749251.json", "CIK0000749251-submissions-001.json"]
    assert all(d["original"]["response_sha256"] == d["response_sha256"] for d in docs)
    kept = list(manifest_originals(m))
    assert len(kept) == 4                                       # 2 companyfacts + 2 documents
    root = originals_root(base=tmp_path / "data" / "facts")
    assert verify_originals(m, root) == []
    # never in git: the committed object root holds no original
    assert not list((tmp_path / "data" / "facts" / "objects").rglob("*.json.gz"))
    assert {o["path"] for o in kept} <= {e["path"] for e in manifest_objects(m)}


def test_a_fact_rebuilds_from_its_original(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader rebuilds NFLX's response from its original, and the fact the store serves is
    the one that response states, at the same cut."""
    m = _ingested(tmp_path, monkeypatch)
    facts = tmp_path / "data" / "facts"
    with FactStore(m["snapshot_id"], facts_base=facts, root=facts / "objects") as s:
        original = s.original(NFLX, originals=originals_root(base=facts))
        fy23 = Period.duration(date(2023, 1, 1), date(2023, 12, 31))
        served = s.get(NFLX, EPS, fy23, date(2024, 3, 1), basis=FILED, stale_ok=True)
    rows = facts_as_of(original, date(2024, 3, 1))["facts"]["us-gaap"][
        "EarningsPerShareDiluted"]["units"]["USD/shares"]
    stated = [r for r in rows if r.get("start") == "2023-01-01" and r["end"] == "2023-12-31"]
    assert {(r["val"], r["accn"]) for r in stated} == {(served.value, served.accession)}


def test_verify_names_a_misnamed_or_mismatched_original(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    m = _ingested(tmp_path, monkeypatch)
    root = originals_root(base=tmp_path / "data" / "facts")
    bad = json.loads(json.dumps(m))
    e = next(x for x in bad["entities"] if x["entity"] == NFLX)
    e["original"]["path"] = "originals/sec/" + "0" * 64 + ".json.gz"
    assert any("not the content-addressed name" in p
               for p in verify_manifest(bad, tmp_path, check_objects=False))
    e["original"] = next(x for x in m["entities"] if x["entity"] == IT)["original"]
    assert any("its original is not the response it read" in p
               for p in verify_manifest(bad, tmp_path, check_objects=False))
    (root / m["entities"][0]["original"]["path"]).unlink()
    assert verify_originals(m, root)                        # a missing original is a problem


# --- the upload sends them, write-once, and reads them back -----------------------------------

def test_the_upload_sends_the_originals_and_reads_each_back(tmp_path: Path,
                                                           monkeypatch: pytest.MonkeyPatch) -> None:
    m = _ingested(tmp_path, monkeypatch)
    facts = tmp_path / "data" / "facts"
    bucket = FakeBucket()
    with _client(bucket) as client:
        rep = upload_snapshot(m, facts / "objects", client, workers=2,
                              originals_root=originals_root(base=facts))
    kept = {o["path"]: o for o in manifest_originals(m)}
    assert rep.problems == [] and rep.read_back == rep.objects
    assert set(kept) <= set(bucket.objects)
    for path, o in kept.items():
        assert hashlib.sha256(bucket.objects[path]).hexdigest() == o["sha256"]
        assert hashlib.sha256(gzip.decompress(bucket.objects[path])).hexdigest() == o[
            "response_sha256"]
    # a second upload writes nothing: every original is already there with the same bytes
    with _client(bucket) as client:
        again = upload_snapshot(m, facts / "objects", client, workers=2,
                                originals_root=originals_root(base=facts))
    assert again.written == 0 and again.present == again.objects


def test_an_upload_without_its_originals_root_sends_nothing(tmp_path: Path,
                                                           monkeypatch: pytest.MonkeyPatch) -> None:
    m = _ingested(tmp_path, monkeypatch)
    bucket = FakeBucket()
    with _client(bucket) as client, pytest.raises(FactsStoreError, match="no originals root"):
        upload_snapshot(m, tmp_path / "data" / "facts" / "objects", client)
    assert bucket.objects == {} and bucket.requests == []


def test_an_originals_key_is_content_addressed_or_refused() -> None:
    assert check_key("originals/sec/" + "a" * 64 + ".json.gz")
    for bad in ("originals/sec/../x.json.gz", "originals/sec/" + "a" * 63 + ".json.gz",
                "originals/SEC/" + "a" * 64 + ".json.gz", "originals/sec/" + "a" * 64 + ".json"):
        with pytest.raises(FactsStoreError):
            check_key(bad)


def test_parity_reads_the_original_not_a_refetched_cache(tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """With the original kept, a refetched cache copy no longer stops the comparison
    (#992 reported such a page CHANGED)."""
    from vinci.facts.parity import compare_page
    m = _ingested(tmp_path, monkeypatch)
    facts = tmp_path / "data" / "facts"
    moved = _cache(tmp_path / "moved", {
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{NFLX}.json": json.dumps(
            {"cik": int(NFLX), "facts": {}})})
    with FactStore(m["snapshot_id"], facts_base=facts, root=facts / "objects") as s:
        r = compare_page("NFLX", {"cik": NFLX, "reference_date": "2026-11-02"}, s, moved,
                         at=date(2026, 11, 2), originals=originals_root(base=facts))
    assert r.changed is None and r.unread is None and r.zero_diff and r.rows_compared > 0


def test_the_screens_ingest_keeps_no_original(tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    """The operator kept the PAGES' originals, not the screen universe's: a screen ingest writes
    its snapshot and no original."""
    import shutil

    from vinci.facts.__main__ import main
    shutil.copytree(FIX / "facts" / "screen_run", tmp_path / "data" / "snapshots")
    cache = _cache(tmp_path, {
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0001029199.json":
            (FIX / "facts" / "EEFT-companyfacts-slice.json").read_text(),
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0001484769.json":
            (FIX / "facts" / "FUBO-companyfacts-slice.json").read_text()})
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VINCI_FACTS_STORE", raising=False)
    assert main(["ingest", "--scope", "screen", "--run", "2026-10-16-01",
                 "--cache-dir", str(cache)]) == 0
    m = load_manifest(name="screen", base=tmp_path / "data" / "facts")
    assert m["entities"] and list(manifest_originals(m)) == []
    assert not (tmp_path / "data" / "facts" / "local" / "originals").exists()


# --- review round 0 ---------------------------------------------------------------------------

def test_a_pages_ingest_keeps_its_originals_when_the_store_env_says_r2(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """$VINCI_FACTS_STORE=r2:// tells a reader to fetch the SCREEN from R2; it names no local
    directory, so a pages ingest keeps its originals at the default root rather than refusing."""
    monkeypatch.setenv("VINCI_FACTS_STORE", "r2://")
    assert originals_root(base=tmp_path) == tmp_path / "local"
    monkeypatch.delenv("VINCI_FACTS_STORE")
    assert originals_root(base=tmp_path) == tmp_path / "local"
    assert originals_root(tmp_path / "x") == tmp_path / "x"


def test_the_reader_finds_originals_beside_its_own_facts_base(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no ``originals`` given, `FactStore.original` reads under its own ``facts_base``, not
    the working directory's ``data/facts``."""
    m = _ingested(tmp_path, monkeypatch)
    facts = tmp_path / "data" / "facts"
    monkeypatch.chdir(tmp_path / "data")                 # cwd's data/facts holds nothing
    with FactStore(m["snapshot_id"], facts_base=facts, root=facts / "objects") as s:
        assert s.original(NFLX)["facts"]


def test_an_unparseable_original_is_a_store_error_so_parity_reports_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An original whose sealed text is not JSON raises FactsStoreError (reported by the parity
    as one unread page), never a bare JSONDecodeError that aborts every other page."""
    from vinci.facts.parity import compare_page
    m = _ingested(tmp_path, monkeypatch)
    facts = tmp_path / "data" / "facts"
    root = originals_root(base=facts)
    bad = keep(CachedResponse(url="u", text="not json",
                              fetched_at=datetime(2026, 11, 11, tzinfo=UTC)), root)
    with FactStore(m["snapshot_id"], facts_base=facts, root=facts / "objects") as s:
        e = next(x for x in s.manifest["entities"] if x["entity"] == NFLX)
        e["original"] = {**bad.__dict__}
        with pytest.raises(FactsStoreError, match="unreadable"):
            s.original(NFLX, originals=root)
        r = compare_page("NFLX", {"cik": NFLX, "reference_date": "2026-11-02"}, s,
                         tmp_path / "no-cache", at=date(2026, 11, 2), originals=root)
    assert r.unread and "unreadable" in r.unread


def test_verify_names_a_submissions_documents_mismatched_original(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = _ingested(tmp_path, monkeypatch)
    assert not [p for p in verify_manifest(m, tmp_path, check_objects=False)
                if "original" in p and "content-addressed" not in p]
    bad = json.loads(json.dumps(m))
    docs = next(x for x in bad["entities"] if x["entity"] == IT)["acceptance"]["documents"]
    docs[0]["original"] = docs[1]["original"]
    assert any("is not the document it read" in p
               for p in verify_manifest(bad, tmp_path, check_objects=False))


def test_verify_reports_a_malformed_original_once_and_does_not_crash(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    from vinci.facts.__main__ import main
    m = _ingested(tmp_path, monkeypatch)
    facts = tmp_path / "data" / "facts"
    path = facts / "manifests" / f"{m['snapshot_id']}.json"
    body = json.loads(path.read_text())
    del body["entities"][0]["original"]["bytes"]
    path.write_text(json.dumps(body))
    capsys.readouterr()
    assert main(["verify", "--snapshot", m["snapshot_id"]]) == 1
    out = capsys.readouterr().out
    lacks = [ln for ln in out.splitlines() if "PROBLEM" in ln and "lacks ['bytes']" in ln]
    assert len(lacks) == 2       # once from the manifest's check, once from the read-back
