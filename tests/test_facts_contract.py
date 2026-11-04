"""The fact layer's committed state agrees with itself: the CI check that a manifest matches its
files.

- `data/facts/schema.json` IS the code's contract (`vinci.facts.schema.contract_text`), byte for
  byte.
- Every committed manifest's id recomputes and its totals add up. For a COMMITTED snapshot
  (``storage: git``), every object it names exists under `data/facts/objects`, its bytes are the
  sealed ones, its rows hash to its name, and every entity's order object is complete.
- A LOCAL snapshot's objects (``storage: local``, the screen's universe) are on the machine that
  ingested it and in no checkout, CI's included: its manifest is checked for content only.
- No object sits under `data/facts/objects` that no committed manifest names.
- `data/facts/current.json` names a committed manifest for each (source, name).

The committed objects stay under the 50 MB stopgap line; past it they move to R2 first.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.facts.schema import CONTRACT_RELPATH, contract_text
from vinci.facts.store import DEFAULT_NAME, load_manifest, verify_manifest

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "data" / "facts"
OBJECTS = FACTS / "objects"
MANIFESTS = sorted((FACTS / "manifests").glob("*.json"))


def _storage(path: Path) -> str:
    """A manifest's storage, or '' so `test_every_manifest_states_its_storage` names it."""
    return str(json.loads(path.read_text()).get("storage", ""))


COMMITTED = [p for p in MANIFESTS if _storage(p) == "git"]
LOCAL = [p for p in MANIFESTS if _storage(p) == "local"]


def _paths(manifest: dict[str, object]) -> set[str]:
    files = manifest["files"]
    entities = manifest["entities"]
    assert isinstance(files, list) and isinstance(entities, list)
    return {f["path"] for f in files} | {e["order"]["path"] for e in entities}


def test_the_committed_schema_is_the_codes_contract() -> None:
    assert (ROOT / CONTRACT_RELPATH).read_text() == contract_text(), (
        "data/facts/schema.json differs from vinci.facts.schema: a column change needs the "
        "contract regenerated (contract_text()) and SCHEMA_VERSION bumped, in one reviewed diff")


def test_there_is_a_committed_snapshot() -> None:
    assert MANIFESTS, "no manifest under data/facts/manifests"


def test_every_manifest_states_its_storage() -> None:
    assert [p.name for p in MANIFESTS if p not in COMMITTED and p not in LOCAL] == []


@pytest.mark.parametrize("path", COMMITTED, ids=lambda p: p.stem)
def test_every_committed_manifest_matches_its_objects(path: Path) -> None:
    manifest = json.loads(path.read_text())
    assert path.stem == manifest["snapshot_id"]
    assert verify_manifest(manifest, OBJECTS) == []


@pytest.mark.parametrize("path", LOCAL, ids=lambda p: p.stem)
def test_every_local_manifest_agrees_with_itself(path: Path) -> None:
    manifest = json.loads(path.read_text())
    assert path.stem == manifest["snapshot_id"]
    assert verify_manifest(manifest, OBJECTS, check_objects=False) == []


def test_no_object_is_outside_every_committed_manifest() -> None:
    named = {path for p in COMMITTED for path in _paths(json.loads(p.read_text()))}
    on_disk = {p.relative_to(OBJECTS).as_posix() for p in OBJECTS.rglob("*.parquet")}
    assert on_disk - named == set()


def test_current_names_a_committed_manifest() -> None:
    current = json.loads((FACTS / "current.json").read_text())
    assert current, "current.json names no source"
    for key, snapshot_id in current.items():
        source, _, name = key.partition(":")
        got = load_manifest(snapshot_id, source=source, name=name or DEFAULT_NAME, base=FACTS)
        assert (got["source"], got["name"]) == (source, name or DEFAULT_NAME)


def test_a_tampered_manifest_is_named(tmp_path: Path) -> None:
    """NEGATIVE: the check above can fail. A row count off by one, and an object that is gone."""
    manifest = json.loads(COMMITTED[-1].read_text())
    manifest["files"][0]["rows"] += 1
    problems = verify_manifest(manifest, OBJECTS)
    assert any("does not recompute" in p for p in problems)
    assert any("rows, manifest says" in p for p in problems)
    assert any("missing" in p for p in verify_manifest(json.loads(
        COMMITTED[-1].read_text()), tmp_path))


#: The stopgap cap (ADR): the Parquet stays in git only while it is under this.
STOPGAP_CAP_BYTES = 50 * 1024 * 1024


def _over_cap(facts: Path, cap: int) -> int | None:
    """The committed fact-layer bytes in the tree: the objects AND the manifests (round 2 of #904:
    a screen manifest is 10.1 MB and its objects are not in git at all). History is not counted."""
    total = sum(p.stat().st_size for p in (facts / "objects").rglob("*.parquet")) + sum(
        p.stat().st_size for p in (facts / "manifests").glob("*.json"))
    return total if total > cap else None


def test_the_committed_objects_stay_under_the_stopgap_cap() -> None:
    """Each refresh adds its changed partitions, its order objects and its manifest to public
    history: past 50 MB in the tree they leave git for R2 first."""
    assert _over_cap(FACTS, STOPGAP_CAP_BYTES) is None


def test_the_cap_check_can_fail() -> None:
    """NEGATIVE: the same check at a 1 MB cap names the committed 16.9 MB (slice 2a: 6.6 MB of
    pages objects, 10.3 MB of manifests)."""
    assert (_over_cap(FACTS, 1024 * 1024) or 0) > 16_000_000


def test_the_cap_counts_the_manifests_too(tmp_path: Path) -> None:
    """Manifests are committed bytes as well: a screen manifest is 10.1 MB with no object in git."""
    (tmp_path / "manifests").mkdir()
    (tmp_path / "manifests" / "edgar-x.json").write_bytes(b" " * (2 * 1024 * 1024))
    assert (_over_cap(tmp_path, 1024 * 1024) or 0) >= 2 * 1024 * 1024
