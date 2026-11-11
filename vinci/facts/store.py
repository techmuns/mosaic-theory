"""Where facts live, how a partition is written, and the manifest that names a snapshot.

IMMUTABLE, AND NAMED BY CONTENT. A data partition (source × entity × filed year) is named by
:func:`content_id`, a hash of its rows' canonical text, never of its bytes:
``<source>/<entity>/<filed_year>/<content_id>.parquet``. A partition no later filing touched
therefore has the same name in every snapshot and is written once. Schema v1 named an object by
its bytes, and its rows carried ``source_position`` (the row's index in the WHOLE response), so one
new filing shifted every later row and renamed every partition: the coordinator measured 0 of 17,
0 of 14 and 0 of 17 earlier-year partitions shared on NFLX, FUBO and NKE's previous cache copies
(review round 2 of #896). The response's order now lives in one ORDER object per entity
(``<source>/<entity>/order/<content_id>.parquet``): for each response row, which data object holds
it and at which row. A replay reads it; a point-in-time query never needs it.

THE BYTES ARE PINNED AS WELL AS THE NAME. A name does not depend on pyarrow (it hashes decoded
values), but the bytes do: they embed the writer's version and its encoder's choices. The writer
refuses any pyarrow other than :data:`PINNED_PYARROW`, which ``pyproject.toml`` pins exactly, so the
same rows always write the same bytes. An object is never overwritten: writing it again with the
same bytes is a no-op, and different bytes under its name raise.

THE MANIFEST IS THE SNAPSHOT. ``data/facts/manifests/<snapshot_id>.json`` lists every data object
and every entity's order object with its content id, byte hash, row count and size, plus the
provenance of every entity's source response. The snapshot id is derived from that content, so the
same cache ingested twice yields the same id. ``data/facts/current.json`` names the current
snapshot of each (source, name): ``edgar`` for the committed pages, ``edgar:screen`` for the
screen's universe.

WHERE THE WRITER KEEPS THE OBJECTS IS THE MANIFEST'S ``storage``. ``git``: committed under
``data/facts/objects`` (the stopgap while it stays under 50 MB). ``local``: on the machine that
wrote them, at ``$VINCI_FACTS_STORE`` or the git-ignored ``data/facts/local``; only the manifest is
committed.

R2 HOLDS A COPY OF EVERY UPLOADED SNAPSHOT, read anywhere (:mod:`vinci.facts.remote`). ``r2://``,
as ``$VINCI_FACTS_STORE`` or an explicit root, makes a READER fetch the objects from the bucket by
their manifest entries. It is not a directory, so :func:`store_root` (where a writer writes)
refuses it: a writer writes locally, and ``python -m vinci.facts upload`` copies a snapshot up.
Where the objects are read from is chosen by the reader, never recorded in the manifest, so an
upload changes no manifest and no snapshot id. Any other remote scheme raises
:class:`RemoteStoreNotConfiguredError`.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from vinci.facts.schema import (
    COLUMNS,
    FILING_COLUMNS,
    ORDER_COLUMNS,
    READABLE_SCHEMA_VERSIONS,
    SCHEMA_VERSION,
    arrow_schema,
    contract_text,
    filing_arrow_schema,
    order_arrow_schema,
)

MANIFEST_VERSION = 2
#: The one pyarrow the writer runs under (``pyproject.toml`` pins it exactly). A reader may run
#: under any version: it hashes nothing it reads back except in :func:`verify_manifest`.
PINNED_PYARROW = "26.0.1"
STORE_ENV = "VINCI_FACTS_STORE"
#: Repository-relative paths, resolved against the working directory as ``Config.data_dir`` is.
DEFAULT_FACTS_DIR = Path("data") / "facts"
#: The snapshot name ``current.json`` keys by the bare source.
DEFAULT_NAME = "pages"
STORAGES = ("git", "local")
_REMOTE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)
#: The one remote location: the Cloudflare R2 bucket the four ``R2_*`` variables configure.
R2_LOCATION = "r2://"
_SHA = re.compile(r"^[0-9a-f]{64}$")


class FactsStoreError(RuntimeError):
    """The store or a snapshot is not in the state its manifest says."""


class RemoteStoreNotConfiguredError(FactsStoreError):
    """A remote location was named that is not configured, or where a directory is needed."""


def facts_dir() -> Path:
    return DEFAULT_FACTS_DIR


def manifests_dir(base: Path | None = None) -> Path:
    return (base or facts_dir()) / "manifests"


def current_path(base: Path | None = None) -> Path:
    return (base or facts_dir()) / "current.json"


def pointer_key(source: str, name: str = DEFAULT_NAME) -> str:
    """The key ``current.json`` names a snapshot under: ``edgar``, ``edgar:screen``."""
    return source if name == DEFAULT_NAME else f"{source}:{name}"


def read_pointers(base: Path | None = None) -> dict[str, str]:
    cur = current_path(base)
    if not cur.exists():
        return {}
    raw = json.loads(cur.read_text())
    if not isinstance(raw, dict) or not all(isinstance(v, str) for v in raw.values()):
        raise FactsStoreError(f"{cur} is not a mapping of names to snapshot ids")
    return {str(k): str(v) for k, v in raw.items()}


def requested_location(explicit: str | Path | None = None, *, storage: str = "git") -> str:
    """The location asked for: ``explicit``; else, for a ``local`` snapshot, ``$VINCI_FACTS_STORE``;
    else ``""`` (the default directory)."""
    if storage not in STORAGES:
        raise FactsStoreError(f"storage {storage!r} is not one of {STORAGES}")
    if explicit is not None:
        return str(explicit)
    return os.environ.get(STORE_ENV, "") if storage == "local" else ""


def is_r2(raw: str | Path | None) -> bool:
    """``r2://`` exactly: the bucket the ``R2_*`` variables name. Anything after the scheme is
    refused rather than read as a bucket or a prefix."""
    s = str(raw or "")
    if s.lower().startswith("r2://") and s.lower() != R2_LOCATION:
        raise RemoteStoreNotConfiguredError(
            f"{s!r}: the R2 location is {R2_LOCATION!r} alone; the bucket is $R2_BUCKET")
    return s.lower() == R2_LOCATION


def store_root(explicit: str | Path | None = None, *, storage: str = "git",
               base: Path | None = None) -> Path:
    """The local object root of a snapshot stored as ``storage``: ``explicit`` when given; else,
    for ``git``, ``<base>/objects``; for ``local``, ``$VINCI_FACTS_STORE`` or ``<base>/local``.
    A remote location is not a directory and raises: a reader resolves ``r2://`` itself
    (:class:`vinci.facts.reader.FactStore`), and a writer never writes to one."""
    raw = requested_location(explicit, storage=storage)
    if is_r2(raw):
        raise RemoteStoreNotConfiguredError(
            "r2:// is read by FactStore and `python -m vinci.facts verify`, and written only by "
            "`python -m vinci.facts upload`: an ingest writes to a local directory (--store)")
    if raw and _REMOTE.match(raw):
        raise RemoteStoreNotConfiguredError(
            f"{raw!r} names a remote store; the only one configured is R2 ({R2_LOCATION!r})")
    if raw:
        return Path(raw)
    return (base or facts_dir()) / ("objects" if storage == "git" else "local")


# --- canonical content ---------------------------------------------------------------------------

_DATA_NAMES = tuple(c.name for c in COLUMNS)
_ORDER_NAMES = tuple(c.name for c in ORDER_COLUMNS)
#: The first line every content id hashes: what kind of object, and its columns with their types,
#: so a column change renames every object and an unchanged schema renames none.
_DATA_HEADER = json.dumps({"object": "data", "columns": [[c.name, c.type] for c in COLUMNS]})
_ORDER_HEADER = json.dumps({"object": "order",
                            "columns": [[c.name, c.type] for c in ORDER_COLUMNS]})
_FILING_NAMES = tuple(c.name for c in FILING_COLUMNS)
_FILING_HEADER = json.dumps({"object": "filings",
                             "columns": [[c.name, c.type] for c in FILING_COLUMNS]})


#: The float64 columns: a value given as an int is stored as a float, so it is NAMED as one too.
_FLOAT_NAMES = frozenset(c.name for c in COLUMNS if c.type == "float64")


def _jsonable(name: str, v: Any) -> Any:
    if isinstance(v, date):
        return v.isoformat()
    if name in _FLOAT_NAMES and isinstance(v, int) and not isinstance(v, bool):
        return float(v)
    return v


def row_text(row: Mapping[str, Any]) -> str:
    """A data row's canonical text: its stored columns' values AS STORED, in contract order, as
    JSON (an int in a float64 column reads back as a float: round 2 of #904). A key outside the
    contract (an ingest's ``source_position``) is not part of it."""
    return json.dumps([_jsonable(c, row[c]) for c in _DATA_NAMES], ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def _digest(header: str, lines: Iterable[str]) -> str:
    h = hashlib.sha256(header.encode("utf-8") + b"\n")
    for line in lines:
        h.update(line.encode("utf-8") + b"\n")
    return h.hexdigest()


def canonical_order(rows: Iterable[Mapping[str, Any]]) -> list[tuple[str, Mapping[str, Any]]]:
    """``rows`` with their canonical text, in the stored order: sorted by that text, so the order
    is a function of the rows' content and nothing else (the input's order, a position)."""
    return sorted(((row_text(r), r) for r in rows), key=lambda t: t[0])


def content_id(rows: Iterable[Mapping[str, Any]]) -> str:
    """A data object's name: sha256 over the header and every row's canonical text, sorted."""
    return _digest(_DATA_HEADER, (t for t, _ in canonical_order(rows)))


def _order_text(source_position: int, obj: str, row: int) -> str:
    return json.dumps([source_position, obj, row], separators=(",", ":"))


def order_content_id(order: Iterable[tuple[int, str, int]]) -> str:
    return _digest(_ORDER_HEADER, (_order_text(*o) for o in sorted(order)))


def _filing_text(row: Mapping[str, Any]) -> str:
    return json.dumps([_jsonable(c, row[c]) for c in _FILING_NAMES], ensure_ascii=False,
                      separators=(",", ":"))


def filings_content_id(rows: Iterable[Mapping[str, Any]]) -> str:
    """A filings object's name: sha256 over its header and every row's text, sorted."""
    return _digest(_FILING_HEADER, sorted(_filing_text(r) for r in rows))


def rows_match_name(rows: Sequence[Mapping[str, Any]], entry: Mapping[str, Any],
                    kind: str = "data") -> bool:
    """Whether an object's decoded ``rows`` hash to the content id its entry names it by — the
    ONE definition the reader (on first read) and :func:`verify_manifest` both apply. ``kind`` is
    ``data``, ``order`` or ``filings``."""
    want = str(entry["content_id"])
    if kind == "order":
        return order_content_id([(r["source_position"], r["object"], r["row"])
                                 for r in rows]) == want
    if kind == "filings":
        return filings_content_id(rows) == want
    if kind != "data":
        raise ValueError(f"no object kind {kind!r}")
    return content_id(rows) == want


# --- writing -------------------------------------------------------------------------------------

@dataclass(frozen=True)
class FileEntry:
    path: str          # relative to the object root, POSIX separators
    content_id: str    # the hash the name is: content_id() of its rows
    sha256: str        # the hash of its bytes, which the reader checks before it reads them
    rows: int
    bytes: int
    source: str
    entity: str
    filed_year: int


@dataclass(frozen=True)
class OrderEntry:
    path: str
    content_id: str
    sha256: str
    rows: int
    bytes: int


def object_path(source: str, entity: str, filed_year: int, cid: str) -> str:
    return f"{source}/{entity}/{filed_year}/{cid}.parquet"


def order_path(source: str, entity: str, cid: str) -> str:
    return f"{source}/{entity}/order/{cid}.parquet"


def filings_path(source: str, entity: str, cid: str) -> str:
    return f"{source}/{entity}/filings/{cid}.parquet"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_pinned_writer() -> None:
    if pa.__version__ != PINNED_PYARROW:
        raise FactsStoreError(
            f"the fact layer's writer is pinned to pyarrow {PINNED_PYARROW}; this is "
            f"{pa.__version__}. Another version writes different bytes under the same names")


#: The order object's integer columns run in near-unit steps, which delta encoding stores in a few
#: bits a row: 0.63 MB for the committed pages' 467,887 rows, against 2.18 MB dictionary-encoded.
_ORDER_ENCODING = {"source_position": "DELTA_BINARY_PACKED", "row": "DELTA_BINARY_PACKED"}


def _parquet(rows: Sequence[Mapping[str, Any]], schema: pa.Schema, *,
             order: bool = False) -> bytes:
    require_pinned_writer()
    table = pa.Table.from_pylist(list(rows), schema=schema)
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="zstd", compression_level=9,
                   use_dictionary=["object"] if order else True,
                   column_encoding=_ORDER_ENCODING if order else None,
                   write_statistics=True, row_group_size=max(len(rows), 1))
    return buf.getvalue()


def parquet_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    """``rows`` as one data object, in their canonical order (:func:`canonical_order`)."""
    return _parquet([r for _, r in canonical_order(rows)], arrow_schema())


def write_object(root: Path, rel: str, data: bytes) -> None:
    """Write ``data`` at ``root/rel`` unless identical bytes are already there. Never overwrites."""
    target = root / rel
    if target.exists():
        if _sha256_file(target) != hashlib.sha256(data).hexdigest():
            raise FactsStoreError(
                f"{target} exists with different bytes: the object is corrupted, or was written "
                f"by a pyarrow other than the pinned {PINNED_PYARROW}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, target)


def write_entity(rows: list[dict[str, Any]], root: Path) -> tuple[list[FileEntry], OrderEntry]:
    """One entity's rows (each carrying its ingest ``source_position``) as one data object per
    filed year plus one order object. Returns their manifest entries."""
    keys = {(r["source"], r["entity"]) for r in rows}
    if len(keys) != 1:
        raise FactsStoreError(f"write_entity takes one entity's rows, got {sorted(keys)}")
    ((source, entity),) = keys
    by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_year[r["filed_date"].year].append(r)
    files: list[FileEntry] = []
    order: list[tuple[int, str, int]] = []
    for year, part in sorted(by_year.items()):
        ordered = canonical_order(part)
        cid = _digest(_DATA_HEADER, (t for t, _ in ordered))
        data = _parquet([r for _, r in ordered], arrow_schema())
        rel = object_path(source, entity, year, cid)
        write_object(root, rel, data)
        files.append(FileEntry(path=rel, content_id=cid, sha256=hashlib.sha256(data).hexdigest(),
                               rows=len(part), bytes=len(data), source=source, entity=entity,
                               filed_year=year))
        order.extend((int(r["source_position"]), cid, i) for i, (_, r) in enumerate(ordered))
    order.sort()
    positions = [o[0] for o in order]
    if len(set(positions)) != len(positions):
        raise FactsStoreError(f"{entity}: two rows claim one source_position")
    ocid = order_content_id(order)
    obytes = _parquet([dict(zip(_ORDER_NAMES, o, strict=True)) for o in order],
                      order_arrow_schema(), order=True)
    orel = order_path(source, entity, ocid)
    write_object(root, orel, obytes)
    return files, OrderEntry(path=orel, content_id=ocid,
                             sha256=hashlib.sha256(obytes).hexdigest(), rows=len(order),
                             bytes=len(obytes))


def write_filings(source: str, entity: str, rows: list[dict[str, Any]], root: Path
                  ) -> OrderEntry:
    """One entity's filings object (schema v3): every row ``{entity, accession, form,
    filing_date, accepted_at}``, one per accession, sorted by its text. Returns its entry."""
    if any(r["entity"] != entity for r in rows):
        raise FactsStoreError(f"write_filings takes {entity}'s filings only")
    accessions = [r["accession"] for r in rows]
    if len(set(accessions)) != len(accessions):
        raise FactsStoreError(f"{entity}: an accession is listed twice in its filings")
    ordered = sorted(rows, key=_filing_text)
    cid = filings_content_id(ordered)
    data = _parquet(ordered, filing_arrow_schema())
    rel = filings_path(source, entity, cid)
    write_object(root, rel, data)
    return OrderEntry(path=rel, content_id=cid, sha256=hashlib.sha256(data).hexdigest(),
                      rows=len(ordered), bytes=len(data))


def write_partitions(rows: list[dict[str, Any]], root: Path
                     ) -> tuple[list[FileEntry], dict[str, OrderEntry]]:
    """:func:`write_entity` for every entity in ``rows``."""
    by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_entity[r["entity"]].append(r)
    files: list[FileEntry] = []
    orders: dict[str, OrderEntry] = {}
    for entity, part in sorted(by_entity.items()):
        got, orders[entity] = write_entity(part, root)
        files.extend(got)
    return files, orders


# --- the manifest --------------------------------------------------------------------------------

def _canonical(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def snapshot_id_for(body: dict[str, Any]) -> str:
    """``<source>-<16 hex>``: the sha256 of the manifest's content without its own id."""
    unstamped = {k: v for k, v in body.items() if k != "snapshot_id"}
    digest = hashlib.sha256(_canonical(unstamped).encode("utf-8")).hexdigest()
    return f"{body['source']}-{digest[:16]}"


def build_manifest(*, source: str, extractor: str, extractor_version: str,
                   scope: dict[str, Any], entities: list[dict[str, Any]],
                   files: list[FileEntry], orders: Mapping[str, OrderEntry],
                   name: str = DEFAULT_NAME, storage: str = "git",
                   filings: Mapping[str, OrderEntry] | None = None) -> dict[str, Any]:
    """The manifest naming every object. With ``filings`` (one filings object per entity) it is
    schema v3 and states each filing's acceptance time; without, schema v2, which states none."""
    if storage not in STORAGES:
        raise FactsStoreError(f"storage {storage!r} is not one of {STORAGES}")
    named = {str(e["entity"]) for e in entities}
    if named != set(orders):
        raise FactsStoreError(f"entities without an order object: {sorted(named - set(orders))}; "
                              f"order objects without an entity: {sorted(set(orders) - named)}")
    if filings is not None and named != set(filings):
        raise FactsStoreError(f"entities without a filings object: "
                              f"{sorted(named - set(filings))}; filings objects without an "
                              f"entity: {sorted(set(filings) - named)}")
    version = SCHEMA_VERSION if filings is not None else 2
    ordered = sorted(files, key=lambda f: f.path)
    body: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "schema_version": version,
        "schema_sha256": hashlib.sha256(contract_text(version).encode("utf-8")).hexdigest(),
        "source": source,
        "name": name,
        "storage": storage,
        "writer": {"pyarrow": PINNED_PYARROW},
        "extractor": extractor,
        "extractor_version": extractor_version,
        "scope": scope,
        "entities": sorted(({**e, "order": asdict(orders[str(e["entity"])]),
                             **({"filings": asdict(filings[str(e["entity"])])}
                                if filings is not None else {})} for e in entities),
                           key=lambda e: str(e["entity"])),
        "files": [asdict(f) for f in ordered],
        "totals": {
            "entities": len(named),
            "files": len(ordered),
            "rows": sum(f.rows for f in ordered),
            "bytes": sum(f.bytes for f in ordered),
            "order_files": len(orders),
            "order_bytes": sum(o.bytes for o in orders.values()),
            **({"filings_files": len(filings),
                "filings_bytes": sum(o.bytes for o in filings.values())}
               if filings is not None else {}),
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
    pointer = read_pointers(base)
    pointer[pointer_key(manifest["source"], manifest["name"])] = manifest["snapshot_id"]
    current_path(base).write_text(_canonical(pointer))
    return target


def manifest_path(snapshot_id: str, base: Path | None = None) -> Path:
    return manifests_dir(base) / f"{snapshot_id}.json"


def load_manifest(snapshot_id: str | None = None, *, source: str = "edgar",
                  name: str = DEFAULT_NAME, base: Path | None = None) -> dict[str, Any]:
    """``snapshot_id``'s manifest, else the one ``current.json`` names for (source, name)."""
    if snapshot_id is None:
        cur = current_path(base)
        if not cur.exists():
            raise FactsStoreError(f"no {cur}: no snapshot has been written")
        snapshot_id = read_pointers(base).get(pointer_key(source, name))
        if not snapshot_id:
            raise FactsStoreError(f"{cur} names no snapshot for {pointer_key(source, name)!r}")
    path = manifest_path(snapshot_id, base)
    if not path.exists():
        raise FactsStoreError(f"no manifest {path}")
    manifest: dict[str, Any] = json.loads(path.read_text())
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        raise FactsStoreError(f"{path}: manifest_version {manifest.get('manifest_version')!r} "
                              f"is not {MANIFEST_VERSION}")
    if manifest.get("schema_version") not in READABLE_SCHEMA_VERSIONS:
        raise FactsStoreError(f"{path}: schema_version {manifest.get('schema_version')!r} "
                              f"is not one of {READABLE_SCHEMA_VERSIONS}")
    check_manifest_shape(manifest)
    return manifest


#: Every key a manifest's entries must carry.
_FILE_KEYS = ("path", "content_id", "sha256", "rows", "bytes", "source", "entity", "filed_year")
_ORDER_KEYS = ("path", "content_id", "sha256", "rows", "bytes")
_ENTITY_KEYS = ("entity", "rows_kept", "order")
_TOP_KEYS = ("snapshot_id", "source", "name", "storage", "schema_version", "files", "entities",
             "totals")


def check_manifest_shape(manifest: dict[str, Any]) -> None:
    """Raise :class:`FactsStoreError` naming the first entry that lacks a required key."""
    missing = [k for k in _TOP_KEYS if k not in manifest]
    if missing:
        raise FactsStoreError(f"manifest lacks {missing}")
    if manifest["storage"] not in STORAGES:
        raise FactsStoreError(f"manifest storage {manifest['storage']!r} is not one of {STORAGES}")
    for i, f in enumerate(manifest["files"]):
        lack = [k for k in _FILE_KEYS if k not in f]
        if lack:
            raise FactsStoreError(f"manifest file entry {i} ({f.get('path', '<no path>')}) "
                                  f"lacks {lack}")
    # schema v3 states every entity's filings (its acceptance times); v2 states none
    filed = manifest.get("schema_version", SCHEMA_VERSION) >= 3
    for i, e in enumerate(manifest["entities"]):
        lack = [k for k in (*_ENTITY_KEYS, *(("filings",) if filed else ())) if k not in e]
        if not lack and isinstance(e["order"], dict):
            lack = [f"order.{k}" for k in _ORDER_KEYS if k not in e["order"]]
        if not lack and filed and isinstance(e["filings"], dict):
            lack = [f"filings.{k}" for k in _ORDER_KEYS if k not in e["filings"]]
        if lack:
            raise FactsStoreError(f"manifest entity entry {i} ({e.get('entity', '<no entity>')}) "
                                  f"lacks {lack}")


def _read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = pq.read_table(path).to_pylist()
    return rows


def _check_object(p: Path, entry: dict[str, Any], schema: pa.Schema) -> list[str]:
    """The byte checks every object gets: present, its size, its hash, its rows, its schema."""
    rel = entry["path"]
    if not p.exists():
        return [f"{rel}: missing"]
    problems = []
    if p.stat().st_size != entry["bytes"]:
        problems.append(f"{rel}: {p.stat().st_size} bytes, manifest says {entry['bytes']}")
    if _sha256_file(p) != entry["sha256"]:
        return [*problems, f"{rel}: sha256 does not match its entry"]
    meta = pq.read_metadata(p)
    if meta.num_rows != entry["rows"]:
        problems.append(f"{rel}: {meta.num_rows} rows, manifest says {entry['rows']}")
    if not meta.schema.to_arrow_schema().equals(schema):
        problems.append(f"{rel}: schema is not the contract's")
    return problems


def verify_manifest(manifest: dict[str, Any], root: Path, *, check_objects: bool = True,
                    check_content: bool = True) -> list[str]:
    """Every way ``manifest`` disagrees with itself or with its objects under ``root``; [] if none.

    Checked: the id recomputes from the content; the contract hash is today's; totals add up;
    every path is the content-addressed name its entry implies; each entity's order object holds
    one row per kept row. With ``check_objects``: each object exists, its bytes hash to its entry,
    and it holds the stated rows under the contract's schema. With ``check_content`` too: each
    object's rows, decoded, hash to its NAME, and each order object maps every response position
    to exactly one row of that entity's data objects, and every row to one position."""
    check_manifest_shape(manifest)
    problems: list[str] = []
    if snapshot_id_for(manifest) != manifest.get("snapshot_id"):
        problems.append(f"snapshot_id {manifest.get('snapshot_id')} does not recompute")
    version = int(manifest["schema_version"])
    want_schema = hashlib.sha256(contract_text(version).encode("utf-8")).hexdigest()
    if manifest.get("schema_sha256") != want_schema:
        problems.append(f"schema_sha256 is not the schema v{version} contract's")
    filed = version >= 3
    files = manifest["files"]
    entities = manifest["entities"]
    totals = manifest.get("totals") or {}
    want_totals = {"entities": len(entities), "files": len(files),
                   "rows": sum(f["rows"] for f in files), "bytes": sum(f["bytes"] for f in files),
                   "order_files": len(entities),
                   "order_bytes": sum(e["order"]["bytes"] for e in entities),
                   **({"filings_files": len(entities),
                       "filings_bytes": sum(e["filings"]["bytes"] for e in entities)}
                      if filed else {})}
    if totals != want_totals or len({f["entity"] for f in files}) != len(entities):
        problems.append(f"totals {totals} do not add up over {len(files)} files and "
                        f"{len(entities)} entities ({want_totals})")
    by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in files:
        by_entity[f["entity"]].append(f)
    for e in entities:
        held = sum(f["rows"] for f in by_entity.get(e["entity"], []))
        if e["rows_kept"] != held:
            problems.append(f"entity {e['entity']}: rows_kept {e['rows_kept']}, its files hold "
                            f"{held}")
        if e["order"]["rows"] != held:
            problems.append(f"entity {e['entity']}: its order object maps {e['order']['rows']} "
                            f"rows, its files hold {held}")
    named_ok: list[dict[str, Any]] = []
    for f in files:
        if not _SHA.match(str(f["content_id"])) or not _SHA.match(str(f["sha256"])) \
                or f["path"] != object_path(f["source"], f["entity"], f["filed_year"],
                                            f["content_id"]):
            problems.append(f"{f['path']}: not the content-addressed name of its entry")
        else:
            named_ok.append(f)
    for e in entities:
        o = e["order"]
        if not _SHA.match(str(o["content_id"])) or not _SHA.match(str(o["sha256"])) \
                or o["path"] != order_path(manifest["source"], e["entity"], o["content_id"]):
            problems.append(f"{o['path']}: not the content-addressed name of its entry")
        if filed:
            g = e["filings"]
            if not _SHA.match(str(g["content_id"])) or not _SHA.match(str(g["sha256"])) \
                    or g["path"] != filings_path(manifest["source"], e["entity"], g["content_id"]):
                problems.append(f"{g['path']}: not the content-addressed name of its entry")
    # THE ORIGINALS ARE NAMED BY THEIR BYTES, and each entity's is the response it read (RFL-D3);
    # their bytes are read back by `vinci.facts.originals.verify_originals`, from their own root
    from vinci.facts.originals import check_entry, manifest_originals
    for org in manifest_originals(manifest):
        problems.extend(check_entry(org))
    for e in entities:
        if (org := e.get("original")) is not None and (
                org.get("response_sha256"), org.get("url"), org.get("fetched_at")) != (
                e.get("response_sha256"), e.get("source_url"), e.get("fetched_at")):
            problems.append(f"entity {e['entity']}: its original is not the response it read")
        # and each submissions document's original is the document it read
        for d in (e.get("acceptance") or {}).get("documents", []):
            if (org := d.get("original")) is not None and (
                    org.get("response_sha256"), org.get("url"), org.get("fetched_at")) != (
                    d.get("response_sha256"), d.get("url"), d.get("fetched_at")):
                problems.append(f"entity {e['entity']}: the original of {d.get('url')} is not "
                                "the document it read")
    if not check_objects:
        return problems
    schema, oschema = arrow_schema(), order_arrow_schema()
    readable: set[str] = set()
    for f in named_ok:
        got = _check_object(root / f["path"], f, schema)
        problems.extend(got)
        if not got:
            readable.add(f["path"])
            if check_content and not rows_match_name(_read_rows(root / f["path"]), f):
                problems.append(f"{f['path']}: its rows do not hash to its name")
    for e in entities:
        o = e["order"]
        got = _check_object(root / o["path"], o, oschema)
        problems.extend(got)
        if got or not check_content:
            continue
        orows = _read_rows(root / o["path"])
        order = [(r["source_position"], r["object"], r["row"]) for r in orows]
        if not rows_match_name(orows, o, "order"):
            problems.append(f"{o['path']}: its rows do not hash to its name")
        problems.extend(_check_order(e["entity"], order, by_entity.get(e["entity"], [])))
    if filed:
        gschema = filing_arrow_schema()
        for e in entities:
            g = e["filings"]
            got = _check_object(root / g["path"], g, gschema)
            problems.extend(got)
            if got or not check_content:
                continue
            rows = _read_rows(root / g["path"])
            if not rows_match_name(rows, g, "filings"):
                problems.append(f"{g['path']}: its rows do not hash to its name")
            if any(r["entity"] != e["entity"] for r in rows):
                problems.append(f"{g['path']}: holds another entity's filings")
    return problems


def _check_order(entity: str, order: list[tuple[int, str, int]],
                 files: list[dict[str, Any]]) -> list[str]:
    """The order object is a bijection between response positions and the entity's stored rows."""
    problems = []
    positions = [o[0] for o in order]
    if positions != sorted(set(positions)):
        problems.append(f"entity {entity}: order positions are not strictly increasing")
    want = {(f["content_id"], i) for f in files for i in range(f["rows"])}
    have = [(obj, row) for _, obj, row in order]
    if len(set(have)) != len(have) or set(have) != want:
        missing, extra = len(want - set(have)), len(set(have) - want)
        problems.append(f"entity {entity}: order maps {len(have)} rows ({missing} stored rows "
                        f"unmapped, {extra} mapped rows not stored, "
                        f"{len(have) - len(set(have))} mapped twice)")
    return problems
