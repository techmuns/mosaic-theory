"""Scan-history persistence (vinci.themes.scan_history) — the archive must be ADDITIVE
(a re-scan never touches a prior snapshot), NON-OVERWRITING on path collision, correctly
indexed in the manifest, and byte-identical to the CLI's --out writer. Network-free."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from vinci.themes.scan_history import record_snapshot

DUMPED: list[dict[str, object]] = [
    {"ticker": "AAA", "exposure_basis": "committed-capacity", "disclosed_facts": [{"n": 1}]},
    {"ticker": "BBB", "exposure_basis": "none-disclosed", "disclosed_facts": []},
    {"ticker": "CCC", "exposure_basis": "committed-capacity", "disclosed_facts": []},
]
T1 = datetime(2026, 7, 4, 12, 0, 0, tzinfo=UTC)
T2 = datetime(2026, 7, 4, 12, 5, 0, tzinfo=UTC)


def test_two_scans_additive_first_snapshot_untouched(tmp_path: Path) -> None:
    """(a) Two scans, same driver, distinct timestamps → 2 files + a 2-line manifest, and the
    FIRST file's bytes are unchanged after the second write — the archive is additive."""
    p1 = record_snapshot(DUMPED, driver_slug="ai-datacenter", driver_desc="d",
                         history_root=tmp_path, now=T1, git_sha="abc1234", n_scanned=10)
    first_bytes = p1.read_bytes()
    p2 = record_snapshot(DUMPED[:1], driver_slug="ai-datacenter", driver_desc="d",
                         history_root=tmp_path, now=T2, git_sha="abc1234", n_scanned=10)
    assert p1 != p2 and p1.exists() and p2.exists()
    assert p1.read_bytes() == first_bytes  # write #2 did not touch snapshot #1
    assert len(list((tmp_path / "ai-datacenter").glob("*.jsonl"))) == 2
    assert len((tmp_path / "manifest.jsonl").read_text().splitlines()) == 2


def test_same_timestamp_and_sha_suffixes_never_overwrites(tmp_path: Path) -> None:
    """(b) The same now+sha twice → the second gets a __1 suffix; the first is untouched."""
    p1 = record_snapshot(DUMPED, driver_slug="ai-datacenter", driver_desc="d",
                         history_root=tmp_path, now=T1, git_sha="abc1234", n_scanned=3)
    first_bytes = p1.read_bytes()
    p2 = record_snapshot(DUMPED[:1], driver_slug="ai-datacenter", driver_desc="d",
                         history_root=tmp_path, now=T1, git_sha="abc1234", n_scanned=3)
    assert p2 != p1
    assert p2.name == "20260704T120000Z__abc1234__1.jsonl"
    assert p1.read_bytes() == first_bytes  # collision suffixed, never overwritten
    p3 = record_snapshot(DUMPED[:2], driver_slug="ai-datacenter", driver_desc="d",
                         history_root=tmp_path, now=T1, git_sha="abc1234", n_scanned=3)
    assert p3.name == "20260704T120000Z__abc1234__2.jsonl"  # __2 next, still no overwrite


def test_manifest_line_counts_and_fields(tmp_path: Path) -> None:
    """(c) tier_counts + n_records + n_scanned (and the identifying fields) are correct."""
    record_snapshot(DUMPED, driver_slug="defense", driver_desc="demand-shift",
                    history_root=tmp_path, now=T1, git_sha=None, n_scanned=42)
    entry = json.loads((tmp_path / "manifest.jsonl").read_text().splitlines()[0])
    assert entry["n_records"] == 3
    assert entry["n_scanned"] == 42
    assert entry["tier_counts"] == {"committed-capacity": 2, "none-disclosed": 1}
    assert entry["driver_slug"] == "defense"
    assert entry["driver_desc"] == "demand-shift"
    assert entry["git_sha"] is None  # no-sha is a logged None, never a fabricated value
    assert entry["ts"] == "2026-07-04T12:00:00Z"
    assert entry["path"] == "defense/20260704T120000Z__nosha.jsonl"


def test_archive_bytes_match_the_out_writer(tmp_path: Path) -> None:
    """(d) Snapshot bytes == the --out writer's exactly: json.dumps per record, newline-joined,
    NO trailing newline — an archived snapshot is a drop-in --out replacement."""
    p = record_snapshot(DUMPED, driver_slug="x", driver_desc="d",
                        history_root=tmp_path, now=T1, git_sha="abc1234", n_scanned=3)
    expected = "\n".join(json.dumps(r) for r in DUMPED)
    assert p.read_text() == expected
    assert not p.read_text().endswith("\n")


def test_utc_guard_rejects_naive_and_nonutc(tmp_path: Path) -> None:
    """UTC guard (verification obs A): a naive or non-UTC `now` fails LOUD before any write; a real
    UTC now passes — the filename's literal 'Z' is only truthful for aware-UTC input."""
    manifest = tmp_path / "manifest.jsonl"
    with pytest.raises(ValueError, match="aware UTC"):  # naive
        record_snapshot(DUMPED, driver_slug="x", driver_desc="d", history_root=tmp_path,
                        now=datetime(2026, 7, 4, 12, 0, 0), git_sha="s", n_scanned=1)
    with pytest.raises(ValueError, match="aware UTC"):  # tz = +05:30
        record_snapshot(DUMPED, driver_slug="x", driver_desc="d", history_root=tmp_path,
                        now=datetime(2026, 7, 4, 12, 0, 0,
                                     tzinfo=timezone(timedelta(hours=5, minutes=30))),
                        git_sha="s", n_scanned=1)
    assert not manifest.exists()  # both rejections failed BEFORE any side effect
    p = record_snapshot(DUMPED, driver_slug="x", driver_desc="d", history_root=tmp_path,
                        now=datetime(2026, 7, 4, 12, 0, 0, tzinfo=UTC),
                        git_sha="s", n_scanned=1)
    assert p.exists() and manifest.exists()  # an aware UTC now passes
