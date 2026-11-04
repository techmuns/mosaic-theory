"""Where facts live, how a partition is written, and the manifest that names a snapshot.

IMMUTABLE AND CONTENT-ADDRESSED. A partition (source × entity × filed year) is named by the sha256
of its own bytes: ``<source>/<entity>/<filed_year>/<sha256>.parquet``. An object is never
overwritten. Writing bytes that already exist under their name is a no-op, and a name whose bytes
differ from it raises, because that can only mean the object was corrupted. A changed partition is
therefore a NEW object, and an unchanged one is shared by every snapshot that contains it.

THE MANIFEST IS THE SNAPSHOT. ``data/facts/manifests/<snapshot_id>.json`` lists every object with
its sha256, row count and byte size, plus the provenance of every entity's source response. The
snapshot id is derived from that content, so the same cache ingested twice yields the same id and
the same manifest. ``data/facts/current.json`` names each source's current snapshot, and only that
source's writer moves it.

THE LOCATION IS CONFIGURABLE, AND ONLY LOCAL TODAY. ``VINCI_FACTS_STORE`` names the object root,
and the default is ``data/facts/objects``. A remote location (``r2://``, ``s3://``) raises
:class:`RemoteStoreNotConfiguredError`: no bucket or credential exists yet (checked 2026-11-04), and
the upload path is not built until one does, since a real run could not prove it (STATE.md §5.0).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from vinci.facts.schema import SCHEMA_VERSION, arrow_schema, contract_text

MANIFEST_VERSION = 1
STORE_ENV = "VINCI_FACTS_STORE"
#: Repository-relative paths, resolved against the working directory as ``Config.data_dir`` is.
DEFAULT_FACTS_DIR = Path("data") / "facts"
_REMOTE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)
_SHA = re.compile(r"^[0-9a-f]{64}$")


class FactsStoreError(RuntimeError):
    """The store or a snapshot is not in the state its manifest says."""


class RemoteStoreNotConfiguredError(FactsStoreError):
    """A remote object store was named, and none is configured yet."""


def facts_dir() -> Path:
    return DEFAULT_FACTS_DIR


def manifests_dir(base: Path | None = None) -> Path:
    return (base or facts_dir()) / "manifests"


def current_path(base: Path | None = None) -> Path:
    return (base or facts_dir()) / "current.json"


def store_root(explicit: str | Path | None = None) -> Path:
    """The object root: ``explicit``, else ``$VINCI_FACTS_STORE``, else ``data/facts/objects``."""
    raw = str(explicit) if explicit is not None else os.environ.get(STORE_ENV, "")
    if not raw:
        return facts_dir() / "objects"
    if _REMOTE.match(raw):
        raise RemoteStoreNotConfiguredError(
            f"{STORE_ENV}={raw!r} names a remote store; only a local directory is supported until "
            "the R2 bucket and its credentials exist (STATE.md §5.0, the fact layer's R2 row)")
    return Path(raw)


@dataclass(frozen=True)
class FileEntry:
    path: str          # relative to the object root, POSIX separators
    sha256: str
    rows: int
    bytes: int
    source: str
    entity: str
    filed_year: int


def object_path(source: str, entity: str, filed_year: int, sha256: str) -> str:
    return f"{source}/{entity}/{filed_year}/{sha256}.parquet"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parquet_bytes(rows: list[dict[str, Any]]) -> bytes:
    """``rows`` as one Parquet file, in ``source_position`` order, with fixed writer options, so
    the same rows always produce the same bytes under the same pyarrow version."""
    ordered = sorted(rows, key=lambda r: int(r["source_position"]))
    table = pa.Table.from_pylist(ordered, schema=arrow_schema())
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="zstd", compression_level=9, use_dictionary=True,
                   write_statistics=True, row_group_size=max(len(ordered), 1))
    return buf.getvalue()


def write_object(root: Path, rel: str, data: bytes) -> None:
    """Write ``data`` at ``root/rel`` unless identical bytes are already there. Never overwrites."""
    target = root / rel
    if target.exists():
        if _sha256_file(target) != hashlib.sha256(data).hexdigest():
            raise FactsStoreError(f"{target} exists with different bytes: the object is corrupted")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, target)


def write_partitions(rows: list[dict[str, Any]], root: Path) -> list[FileEntry]:
    """Partition ``rows`` by (source, entity, filed year) and write each as one immutable object."""
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["source"], r["entity"], r["filed_date"].year)].append(r)
    out: list[FileEntry] = []
    for (source, entity, year), part in sorted(groups.items()):
        data = parquet_bytes(part)
        sha = hashlib.sha256(data).hexdigest()
        rel = object_path(source, entity, year, sha)
        write_object(root, rel, data)
        out.append(FileEntry(path=rel, sha256=sha, rows=len(part), bytes=len(data), source=source,
                             entity=entity, filed_year=year))
    return out


def _canonical(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def snapshot_id_for(body: dict[str, Any]) -> str:
    """``<source>-<16 hex>``: the sha256 of the manifest's content without its own id."""
    unstamped = {k: v for k, v in body.items() if k != "snapshot_id"}
    digest = hashlib.sha256(_canonical(unstamped).encode("utf-8")).hexdigest()
    return f"{body['source']}-{digest[:16]}"


def build_manifest(*, source: str, extractor: str, extractor_version: str,
                   scope: dict[str, Any], entities: list[dict[str, Any]],
                   files: list[FileEntry]) -> dict[str, Any]:
    ordered = sorted(files, key=lambda f: f.path)
    body: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "schema_version": SCHEMA_VERSION,
        "schema_sha256": hashlib.sha256(contract_text().encode("utf-8")).hexdigest(),
        "source": source,
        "extractor": extractor,
        "extractor_version": extractor_version,
        "scope": scope,
        "entities": sorted(entities, key=lambda e: str(e["entity"])),
        "files": [asdict(f) for f in ordered],
        "totals": {
            "entities": len({f.entity for f in ordered}),
            "files": len(ordered),
            "rows": sum(f.rows for f in ordered),
            "bytes": sum(f.bytes for f in ordered),
        },
    }
    body["snapshot_id"] = snapshot_id_for(body)
    return body


def write_manifest(manifest: dict[str, Any], base: Path | None = None) -> Path:
    """Write the manifest under its snapshot id (immutable) and point ``current.json`` at it."""
    target = manifests_dir(base) / f"{manifest['snapshot_id']}.json"
    text = _canonical(manifest)
    if target.exists() and target.read_text() != text:
        raise FactsStoreError(f"{target} exists with different content under the same id")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    cur = current_path(base)
    pointer = json.loads(cur.read_text()) if cur.exists() else {}
    pointer[manifest["source"]] = manifest["snapshot_id"]
    cur.write_text(_canonical(pointer))
    return target


def load_manifest(snapshot_id: str | None = None, *, source: str = "edgar",
                  base: Path | None = None) -> dict[str, Any]:
    """``snapshot_id``'s manifest, else the one ``current.json`` names for ``source``."""
    if snapshot_id is None:
        cur = current_path(base)
        if not cur.exists():
            raise FactsStoreError(f"no {cur}: no snapshot has been written")
        snapshot_id = json.loads(cur.read_text()).get(source)
        if not snapshot_id:
            raise FactsStoreError(f"{cur} names no snapshot for source {source!r}")
    path = manifests_dir(base) / f"{snapshot_id}.json"
    if not path.exists():
        raise FactsStoreError(f"no manifest {path}")
    manifest: dict[str, Any] = json.loads(path.read_text())
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        raise FactsStoreError(f"{path}: manifest_version {manifest.get('manifest_version')!r} "
                              f"is not {MANIFEST_VERSION}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise FactsStoreError(f"{path}: schema_version {manifest.get('schema_version')!r} "
                              f"is not {SCHEMA_VERSION}")
    return manifest


def verify_manifest(manifest: dict[str, Any], root: Path, *,
                    check_objects: bool = True) -> list[str]:
    """Every way ``manifest`` disagrees with itself or with its objects under ``root``; [] if none.

    Checked: the id recomputes from the content; the contract hash is today's; totals add up; each
    path is the content-addressed name its entry implies; and (``check_objects``) each object
    exists, hashes to its name, and holds the stated rows under the contract's schema."""
    problems: list[str] = []
    if snapshot_id_for(manifest) != manifest.get("snapshot_id"):
        problems.append(f"snapshot_id {manifest.get('snapshot_id')} does not recompute")
    want_schema = hashlib.sha256(contract_text().encode("utf-8")).hexdigest()
    if manifest.get("schema_sha256") != want_schema:
        problems.append("schema_sha256 is not the committed contract's")
    files = manifest.get("files") or []
    totals = manifest.get("totals") or {}
    if totals.get("files") != len(files) or totals.get("rows") != sum(f["rows"] for f in files) \
            or totals.get("bytes") != sum(f["bytes"] for f in files) \
            or totals.get("entities") != len({f["entity"] for f in files}):
        problems.append(f"totals {totals} do not add up over {len(files)} files")
    schema = arrow_schema()
    for f in files:
        if not _SHA.match(str(f.get("sha256"))) or f["path"] != object_path(
                f["source"], f["entity"], f["filed_year"], f["sha256"]):
            problems.append(f"{f['path']}: not the content-addressed name of its entry")
            continue
        if not check_objects:
            continue
        p = root / f["path"]
        if not p.exists():
            problems.append(f"{f['path']}: missing under {root}")
            continue
        if p.stat().st_size != f["bytes"]:
            problems.append(f"{f['path']}: {p.stat().st_size} bytes, manifest says {f['bytes']}")
        if _sha256_file(p) != f["sha256"]:
            problems.append(f"{f['path']}: sha256 does not match its name")
            continue
        meta = pq.read_metadata(p)
        if meta.num_rows != f["rows"]:
            problems.append(f"{f['path']}: {meta.num_rows} rows, manifest says {f['rows']}")
        if not meta.schema.to_arrow_schema().equals(schema):
            problems.append(f"{f['path']}: schema is not the contract's")
    return problems
