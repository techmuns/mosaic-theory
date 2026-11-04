"""The fact layer's committed state agrees with itself: the CI check that a manifest matches its
files.

- `data/facts/schema.json` IS the code's contract (`vinci.facts.schema.contract_text`), byte for
  byte.
- Every committed manifest's id recomputes, its totals add up, and every object it names exists
  under `data/facts/objects`, hashes to its own name and holds the stated rows under the contract.
- No object sits under `data/facts/objects` that no manifest names (drift in the other direction).
- `data/facts/current.json` names a committed manifest for each source.

Slice 1 commits the objects (7.2 MB, under the 50 MB stopgap line). When they move to R2 the
object half of this check reads from there, and the content half stays here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.facts.schema import CONTRACT_RELPATH, contract_text
from vinci.facts.store import load_manifest, verify_manifest

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "data" / "facts"
OBJECTS = FACTS / "objects"
MANIFESTS = sorted((FACTS / "manifests").glob("*.json"))


def test_the_committed_schema_is_the_codes_contract() -> None:
    assert (ROOT / CONTRACT_RELPATH).read_text() == contract_text(), (
        "data/facts/schema.json differs from vinci.facts.schema: a column change needs the "
        "contract regenerated (contract_text()) and SCHEMA_VERSION bumped, in one reviewed diff")


def test_there_is_a_committed_snapshot() -> None:
    assert MANIFESTS, "no manifest under data/facts/manifests"


@pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: p.stem)
def test_every_manifest_matches_its_objects(path: Path) -> None:
    manifest = json.loads(path.read_text())
    assert path.stem == manifest["snapshot_id"]
    assert verify_manifest(manifest, OBJECTS) == []


def test_no_object_is_outside_every_manifest() -> None:
    named = {f["path"] for p in MANIFESTS for f in json.loads(p.read_text())["files"]}
    on_disk = {p.relative_to(OBJECTS).as_posix() for p in OBJECTS.rglob("*.parquet")}
    assert on_disk - named == set()


def test_current_names_a_committed_manifest() -> None:
    current = json.loads((FACTS / "current.json").read_text())
    assert current, "current.json names no source"
    for source, snapshot_id in current.items():
        assert load_manifest(snapshot_id, source=source, base=FACTS)["source"] == source


def test_a_tampered_manifest_is_named(tmp_path: Path) -> None:
    """NEGATIVE: the check above can fail. A row count off by one, and an object that is gone."""
    manifest = json.loads(MANIFESTS[-1].read_text())
    manifest["files"][0]["rows"] += 1
    problems = verify_manifest(manifest, OBJECTS)
    assert any("does not recompute" in p for p in problems)
    assert any("rows, manifest says" in p for p in problems)
    assert any("missing under" in p for p in verify_manifest(json.loads(
        MANIFESTS[-1].read_text()), tmp_path))


#: The stopgap cap (ADR): the Parquet stays in git only while it is under this.
STOPGAP_CAP_BYTES = 50 * 1024 * 1024


def _over_cap(objects: Path, cap: int) -> int | None:
    total = sum(p.stat().st_size for p in objects.rglob("*.parquet"))
    return total if total > cap else None


def test_the_committed_objects_stay_under_the_stopgap_cap() -> None:
    """A refresh rewrites partitions rather than sharing them (round 2 of #896), so each one adds
    to public history: past 50 MB the objects leave git for R2 first."""
    assert _over_cap(OBJECTS, STOPGAP_CAP_BYTES) is None


def test_the_cap_check_can_fail() -> None:
    """NEGATIVE: the same check at a 1 MB cap names the committed 7.2 MB."""
    assert (_over_cap(OBJECTS, 1024 * 1024) or 0) > 7_000_000
