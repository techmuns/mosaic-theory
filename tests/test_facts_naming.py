"""Slice 2a: an object is named by its rows' content, the response's order is its own object, the
writer's pyarrow is pinned, and a local snapshot fails loud where its objects are not.

On FROZEN slices of real cached companyfacts (`tests/fixtures/facts/`, provenance in each `_note`).
A "previous cache copy" is the response without its last filing day's rows, every other row
verbatim and in order. It leaves each `frame` where today's response puts it, so these pins test
that a POSITION never renames a partition. SEC moves a period's `frame` to its latest-filed row, and
`frame` is content, so a real refresh also renames the year a moved frame left (16 of 17 shared for
NFLX and NKE, measured in the slice-2a record): that is a content change, named correctly. On
NFLX's slice that day (2026-10-21) has rows at positions 315, 317, 322, 323 and 395 of 396, so
every row after 315 moves; under schema v1 that renamed every partition holding one of them.
"""
from __future__ import annotations

import copy
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
import pytest

from vinci.edgar.concepts import facts_as_of
from vinci.facts import FactsStoreNotPresentError, FactStore
from vinci.facts import store as fstore
from vinci.facts.edgar_ingest import EXTRACTOR, EXTRACTOR_VERSION, SOURCE, rows_from_companyfacts
from vinci.facts.parity import compare_rows
from vinci.facts.schema import arrow_schema, order_arrow_schema
from vinci.facts.store import (
    PINNED_PYARROW,
    FactsStoreError,
    build_manifest,
    content_id,
    load_manifest,
    store_root,
    verify_manifest,
    write_entity,
    write_manifest,
)

FIX = Path(__file__).parent / "fixtures" / "facts"
ROOT = Path(__file__).resolve().parents[1]
NFLX = "0001065280"


def _load(name: str) -> dict[str, Any]:
    blob: dict[str, Any] = json.loads((FIX / name).read_text())
    return blob


def _last_day(blob: dict[str, Any]) -> date:
    return max(date.fromisoformat(r["filed"]) for tags in blob["facts"].values()
               for body in tags.values() for rows in body["units"].values() for r in rows)


def _previous_copy(blob: dict[str, Any]) -> dict[str, Any]:
    return facts_as_of(blob, _last_day(blob) - timedelta(days=1))


def _write(blob: dict[str, Any], root: Path) -> tuple[list[fstore.FileEntry], fstore.OrderEntry]:
    return write_entity(rows_from_companyfacts(blob).rows, root)


def _publish(base: Path, blob: dict[str, Any], *, name: str = "pages",
             storage: str = "git") -> dict[str, Any]:
    got = rows_from_companyfacts(blob)
    files, order = write_entity(got.rows, store_root(None, storage=storage, base=base))
    manifest = build_manifest(
        source=SOURCE, extractor=EXTRACTOR, extractor_version=EXTRACTOR_VERSION,
        scope={"rule": "test", "excluded_by_operator_instruction": 0, "exclusions_listed": 0},
        entities=[{"entity": got.entity, "rows_kept": len(got.rows)}], files=files,
        orders={got.entity: order}, name=name, storage=storage)
    write_manifest(manifest, base)
    return manifest


# --- a partition no filing touched keeps its name across a refresh -------------------------------

@pytest.mark.parametrize("name", ["NFLX", "FUBO", "NKE"])
def test_an_earlier_year_partition_is_the_same_object_after_a_refresh(tmp_path: Path,
                                                                      name: str) -> None:
    """POSITIVE: the previous cache copy and the current one share every partition of a year
    before the new filing's (0 of 17, 0 of 14 and 0 of 17 under schema v1, review of #896)."""
    blob = _load(f"{name}-companyfacts-slice.json")
    before, _ = _write(_previous_copy(blob), tmp_path)
    after, _ = _write(blob, tmp_path)
    year = _last_day(blob).year
    old = {f.filed_year: f.path for f in before if f.filed_year < year}
    new = {f.filed_year: f.path for f in after if f.filed_year < year}
    assert old and old == new


def test_the_new_filings_year_and_the_order_are_new_objects(tmp_path: Path) -> None:
    blob = _load("NFLX-companyfacts-slice.json")
    before, order_before = _write(_previous_copy(blob), tmp_path)
    after, order_after = _write(blob, tmp_path)
    changed = {f.path for f in after} - {f.path for f in before}
    assert [p.split("/")[2] for p in changed] == ["2026"]
    assert order_after.path != order_before.path


def test_a_restated_row_renames_its_own_partition_and_no_other(tmp_path: Path) -> None:
    """NEGATIVE: a name is the content, so one changed value changes one name."""
    blob = _load("NFLX-companyfacts-slice.json")
    edited = copy.deepcopy(blob)
    row = edited["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"][0]
    row["val"] = row["val"] + 1
    a, _ = _write(blob, tmp_path)
    b, _ = _write(edited, tmp_path)
    moved = {f.filed_year for f in a} ^ {f.filed_year for f in b}
    renamed = sorted(fa.filed_year for fa in a for fb in b
                     if fa.filed_year == fb.filed_year and fa.path != fb.path)
    assert not moved and renamed == [int(row["filed"][:4])]


def test_a_name_is_independent_of_row_order_and_of_position() -> None:
    rows = rows_from_companyfacts(_load("FUBO-companyfacts-slice.json")).rows
    shifted = [{**r, "source_position": r["source_position"] + 7} for r in rows]
    assert content_id(rows) == content_id(list(reversed(rows))) == content_id(shifted)


def test_a_name_changes_with_any_stored_field() -> None:
    rows = rows_from_companyfacts(_load("FUBO-companyfacts-slice.json")).rows
    for col in ("accession", "form", "frame", "extractor_version"):
        edited = [dict(r) for r in rows]
        edited[0][col] = "X"
        assert content_id(edited) != content_id(rows), col


# --- the response's order is its own object, and a replay reads it --------------------------------

def test_the_store_returns_the_responses_order_of_lists_and_of_rows(tmp_path: Path) -> None:
    blob = _load("NFLX-companyfacts-slice.json")
    _publish(tmp_path, blob)
    got = FactStore(facts_base=tmp_path).companyfacts_as_of(NFLX, date(2026, 11, 2))
    want = facts_as_of(blob, date(2026, 11, 2))
    assert compare_rows(want, got, []) == (0, 0, 396, 396)
    assert list(got["facts"]) == list(want["facts"]) == ["us-gaap", "dei"]


def test_the_row_comparison_sees_lists_in_another_order() -> None:
    """NEGATIVE: the same lists, namespaces swapped. A reader takes the FIRST namespace present."""
    blob = facts_as_of(_load("NFLX-companyfacts-slice.json"), date(2026, 11, 2))
    swapped = {**blob, "facts": dict(reversed(list(blob["facts"].items())))}
    assert compare_rows(blob, swapped, []).order_diffs == 1


def test_a_row_the_order_object_does_not_map_raises(tmp_path: Path) -> None:
    manifest = _publish(tmp_path, _load("FUBO-companyfacts-slice.json"))
    order = tmp_path / "objects" / manifest["entities"][0]["order"]["path"]
    table = pq.read_table(order)
    pq.write_table(table.slice(1), order)        # the first response row is no longer mapped
    with pytest.raises(FactsStoreError, match="not in the entity's order object"):
        FactStore(facts_base=tmp_path, verify=False).companyfacts_as_of("1484769",
                                                                        date(2026, 11, 2))


def test_verify_names_an_object_whose_rows_are_not_its_name(tmp_path: Path) -> None:
    manifest = _publish(tmp_path, _load("FUBO-companyfacts-slice.json"))
    root = tmp_path / "objects"
    f = manifest["files"][0]
    rows = pq.read_table(root / f["path"]).to_pylist()
    rows[0]["value"] += 1
    (root / f["path"]).write_bytes(fstore._parquet(rows, arrow_schema()))
    tampered = copy.deepcopy(manifest)
    tampered["files"][0]["sha256"] = fstore._sha256_file(root / f["path"])
    tampered["files"][0]["bytes"] = (root / f["path"]).stat().st_size
    problems = verify_manifest(tampered, root)
    assert any("do not hash to its name" in p for p in problems)
    assert not any("do not hash" in p for p in verify_manifest(tampered, root,
                                                               check_content=False))


def test_verify_names_an_order_that_maps_a_row_twice(tmp_path: Path) -> None:
    manifest = _publish(tmp_path, _load("FUBO-companyfacts-slice.json"))
    root = tmp_path / "objects"
    o = manifest["entities"][0]["order"]
    rows = pq.read_table(root / o["path"]).to_pylist()
    rows[1] = {**rows[1], "object": rows[0]["object"], "row": rows[0]["row"]}
    (root / o["path"]).write_bytes(fstore._parquet(rows, order_arrow_schema(), order=True))
    tampered = copy.deepcopy(manifest)
    tampered["entities"][0]["order"]["sha256"] = fstore._sha256_file(root / o["path"])
    tampered["entities"][0]["order"]["bytes"] = (root / o["path"]).stat().st_size
    assert any("mapped twice" in p for p in verify_manifest(tampered, root))


# --- the writer's pyarrow is pinned ---------------------------------------------------------------

def test_the_writer_refuses_any_pyarrow_but_the_pinned_one(tmp_path: Path,
                                                           monkeypatch: pytest.MonkeyPatch) -> None:
    rows = rows_from_companyfacts(_load("FUBO-companyfacts-slice.json")).rows
    write_entity(rows, tmp_path / "a")                     # POSITIVE: the pinned version writes
    monkeypatch.setattr(pa, "__version__", "27.0.0")
    with pytest.raises(FactsStoreError, match=f"pinned to pyarrow {PINNED_PYARROW}"):
        write_entity(rows, tmp_path / "b")
    assert not (tmp_path / "b").exists()


def test_pyproject_pins_the_writers_pyarrow_exactly() -> None:
    import tomllib
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    assert f"pyarrow=={PINNED_PYARROW}" in [d.split(";")[0].strip() for d in deps]


def test_the_same_rows_write_the_same_bytes_and_a_second_write_is_a_no_op(tmp_path: Path) -> None:
    blob = _load("NKE-companyfacts-slice.json")
    a = _write(blob, tmp_path)
    b = _write(blob, tmp_path)
    assert a == b


# --- a snapshot is named; a local one is not shared -----------------------------------------------

def test_two_named_snapshots_are_current_side_by_side(tmp_path: Path) -> None:
    pages = _publish(tmp_path, _load("FUBO-companyfacts-slice.json"))
    screen = _publish(tmp_path, _load("NKE-companyfacts-slice.json"), name="screen",
                      storage="local")
    assert json.loads((tmp_path / "current.json").read_text()) == {
        "edgar": pages["snapshot_id"], "edgar:screen": screen["snapshot_id"]}
    assert load_manifest(base=tmp_path)["snapshot_id"] == pages["snapshot_id"]
    assert load_manifest(name="screen", base=tmp_path)["snapshot_id"] == screen["snapshot_id"]


def test_a_local_snapshot_opens_where_its_objects_are(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VINCI_FACTS_STORE", raising=False)
    _publish(tmp_path, _load("NKE-companyfacts-slice.json"), name="screen", storage="local")
    with FactStore(name="screen", facts_base=tmp_path) as store:
        assert store.root == tmp_path / "local" and store.entities == ("0000320187",)


def test_a_local_snapshot_fails_loud_where_its_objects_are_not(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: CI, or another checkout, holds the committed manifest and none of its objects."""
    monkeypatch.delenv("VINCI_FACTS_STORE", raising=False)
    _publish(tmp_path, _load("NKE-companyfacts-slice.json"), name="screen", storage="local")
    (tmp_path / "local").rename(tmp_path / "elsewhere")
    with pytest.raises(FactsStoreNotPresentError, match="if uploaded, in R2"):
        FactStore(name="screen", facts_base=tmp_path)
    monkeypatch.setenv("VINCI_FACTS_STORE", str(tmp_path / "elsewhere"))
    with FactStore(name="screen", facts_base=tmp_path) as store:     # pointed at, it opens
        assert store.root == tmp_path / "elsewhere"


def test_the_store_variable_moves_only_a_local_snapshot(tmp_path: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VINCI_FACTS_STORE", str(tmp_path / "x"))
    assert store_root(storage="git", base=tmp_path) == tmp_path / "objects"
    assert store_root(storage="local", base=tmp_path) == tmp_path / "x"


# --- review round 2 of #904 (coordinator) ---------------------------------------------------------

def test_the_row_comparison_sees_one_value_changed() -> None:
    """NEGATIVE: one `val` moved, the count and the order unchanged: two rows differ (the one gone
    and the one come). A comparison blind to `val` passed every other pin."""
    blob = facts_as_of(_load("NFLX-companyfacts-slice.json"), date(2026, 11, 2))
    edited = copy.deepcopy(blob)
    edited["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"][0]["val"] += 1
    assert compare_rows(blob, edited, []) == (2, 0, 396, 396)


def test_an_integer_value_names_its_object_as_the_stored_float_does(tmp_path: Path) -> None:
    """The name hashes the values as STORED: an int given for a float64 column is 5.0 once
    written, so it must be named as 5.0, or the object does not hash to its own name."""
    rows = rows_from_companyfacts(_load("FUBO-companyfacts-slice.json")).rows
    as_int = [{**r, "value": int(r["value"])} if r["value"].is_integer() else r for r in rows]
    assert content_id(as_int) == content_id(rows)
    files, order = write_entity(as_int, tmp_path / "objects")
    manifest = build_manifest(
        source=SOURCE, extractor=EXTRACTOR, extractor_version=EXTRACTOR_VERSION,
        scope={"rule": "test"}, entities=[{"entity": "0001484769", "rows_kept": len(rows)}],
        files=files, orders={"0001484769": order})
    assert verify_manifest(manifest, tmp_path / "objects") == []


def test_a_corrupt_cache_entry_is_named_unreadable_not_absent(tmp_path: Path) -> None:
    from vinci.facts.edgar_ingest import NotInCacheError, read_cached
    from vinci.netcache import CachedHttp
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{NFLX}.json"
    with CachedHttp(cache_dir=tmp_path, user_agent="t", min_interval_sec=0, namespace="sec") as h:
        h._write_cache(url, (FIX / "NFLX-companyfacts-slice.json").read_text())
        h._cache_path(url).write_text("{not json")
    with pytest.raises(NotInCacheError, match="unreadable"):
        read_cached(url, tmp_path)
