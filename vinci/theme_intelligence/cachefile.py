"""The answer caches' files — paid model answers, truncation markers, fetched pages — written so a
crash can never leave half a file, and read so a file that is torn anyway is set aside instead of
failing every later run (U22: a plain `write_text` torn by a kill, power loss or a full disk raised
JSONDecodeError on every run after). No imports from this package: any module may use it.
"""

from __future__ import annotations

import json
import os
import tempfile
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

#: every torn file set aside in this process, until a run takes them (`take_set_aside`) and
#: records each as an issue — a re-paid answer is never known only to stderr
_SET_ASIDE: list[Path] = []


def take_set_aside() -> list[Path]:
    """The torn files set aside since the last call, oldest first; the list is emptied."""
    out = list(_SET_ASIDE)
    _SET_ASIDE.clear()
    return out


def write_atomic(path: Path, data: str | bytes) -> None:
    """Write `data` to `path` whole or not at all: a temporary file in the same folder, flushed,
    then renamed over `path` (one atomic step on the same filesystem)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data.encode() if isinstance(data, str) else data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_json(path: Path, obj: Any, **dump: Any) -> None:
    write_atomic(path, json.dumps(obj, **dump))


def read_json(path: Path) -> dict[str, Any] | None:
    """A cached record, or None when the file is TORN (not JSON, or not an object): it is moved
    aside to `<name>.torn-<UTC time>` — kept for inspection, never deleted — and said, so the
    caller treats it as absent instead of failing on it forever."""
    try:
        rec = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        rec = None
    if isinstance(rec, dict):
        return rec
    aside = path.with_name(f"{path.name}.torn-{datetime.now(tz=UTC):%Y%m%dT%H%M%S%fZ}")
    path.replace(aside)
    _SET_ASIDE.append(aside)
    warnings.warn(f"a torn cache file was set aside, read as absent: {aside}", stacklevel=2)
    return None
