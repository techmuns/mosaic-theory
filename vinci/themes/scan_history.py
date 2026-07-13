"""Scan-history persistence — every themes-exposure scan ALSO lands in an append-only,
timestamped archive, so a re-scan never destroys the previous scan.

WHY: the CLI's ``--out`` is operator-named and OVERWRITES on re-use — before this module a
re-scan clobbered the only copy of the prior scan. The monitor/delta-scan needs a prior
snapshot to diff against ("what newly appeared / what changed grade" is only answerable if
history exists). The archive is ALWAYS-ON (independent of ``--out``), immutable (collision →
suffix, never overwrite), keyed by driver, and indexed by ONE ``manifest.jsonl``.

Output is DATA — git-ignored (``data/scan_history/``), fail-closed like the scan output.
Stdlib only: no network, no vinci imports; the caller hands in the already-dumped records.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def record_snapshot(
    dumped: list[dict[str, Any]],
    *,
    driver_slug: str,
    driver_desc: str,
    history_root: Path,
    now: datetime,
    git_sha: str | None,
    n_scanned: int,
    tier_field: str | None = "exposure_basis",
) -> Path:
    """Write ``dumped`` as an immutable snapshot under ``history_root/<driver_slug>/`` and append
    one index line to ``history_root/manifest.jsonl``; returns the snapshot path.

    Snapshot bytes are IDENTICAL to the CLI's ``--out`` writer (``json.dumps`` per record,
    newline-joined, no trailing newline), so an archived snapshot is a drop-in ``--out``
    replacement for any downstream reader. NON-OVERWRITING: a path collision (same second +
    sha) gets a ``__1``/``__2``/… suffix — an existing snapshot is never touched. Any write
    error propagates loud; a silently missing snapshot would fake history.

    ``tier_field`` keys the manifest ``tier_counts`` (default ``exposure_basis``; a missing key is
    FAIL-LOUD). Pass ``None`` for no-tier records (Component-A) → empty ``tier_counts``."""
    if now.tzinfo is None or now.utcoffset() != timedelta(0):  # aware-UTC only — the filename's
        # literal 'Z' would otherwise falsely imply UTC (verification obs A). Fail before any write.
        raise ValueError("record_snapshot requires an aware UTC datetime")
    # tier_counts index the display tier for exposure/assay; a missing key stays FAIL-LOUD (a
    # malformed exposure record must not pass silently). tier_field=None for records with no tier
    # concept (Component-A candidate themes) → empty tier_counts, never a KeyError. Default path is
    # byte-identical: str(r["exposure_basis"]) exactly as before.
    tier_counts: Counter[str] = (
        Counter(str(r[tier_field]) for r in dumped) if tier_field is not None else Counter())
    subdir = history_root / driver_slug
    subdir.mkdir(parents=True, exist_ok=True)
    stem = f"{now:%Y%m%dT%H%M%SZ}__{git_sha or 'nosha'}"
    path = subdir / f"{stem}.jsonl"
    n = 0
    while path.exists():  # immutable archive — never overwrite, suffix instead
        n += 1
        path = subdir / f"{stem}__{n}.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in dumped))

    entry = {
        "ts": now.isoformat().replace("+00:00", "Z"),
        "driver_slug": driver_slug,
        "driver_desc": driver_desc,
        "git_sha": git_sha,
        "path": str(path.relative_to(history_root)),
        "n_records": len(dumped),
        "n_scanned": n_scanned,
        "tier_counts": dict(tier_counts),
    }
    with (history_root / "manifest.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return path
