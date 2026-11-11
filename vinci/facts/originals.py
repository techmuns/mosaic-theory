"""The ORIGINALS: every response an ingest reads, kept write-once, so every fact can be rebuilt.

THE STORE HELD DERIVED ROWS ONLY (TeamNostra fix request 2, RFL-D3). A snapshot kept each
response's URL, ``fetched_at`` and sha256, but the bytes stayed in the SEC cache, which a refetch
overwrites in place. Of the committed pages snapshot's 26 ingested responses, only 22 still
existed anywhere on the ingest-side machine eleven days later (by sha256, across 52 local caches).
For the other four, nothing could show what the store had read. The operator ruled 2026-11-11:
*"Keep the pages' originals (Recommended)"*.

ONE OBJECT PER RESPONSE, NAMED BY THE SHA256 OF ITS STORED BYTES:
``originals/sec/<sha256>.json.gz``, the response's UTF-8 text gzipped (``mtime=0``). The same body
is the same name, so a second write of it is a no-op, and other bytes under a name are refused
(:func:`vinci.facts.store.write_object`, and in R2 ``put_new``'s ``If-None-Match: *``). The
manifest records each original beside what it was read for: the response's own sha256 (the
manifest's ``response_sha256``), its URL and its ``fetched_at``. :func:`read_original` checks both
hashes before it returns the text.

WHERE THEY ARE KEPT. Never in git: the repository is public, and a snapshot's originals run to
tens of MB raw. Locally they sit under the git-ignored object root of a LOCAL snapshot
(``$VINCI_FACTS_STORE``, else ``data/facts/local``), beside any screen objects, and
``python -m vinci.facts upload`` sends them to R2 with the snapshot's own objects. A reader given
``r2://`` fetches them from there (:class:`vinci.facts.remote.R2Objects`).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vinci.facts.store import (
    FactsStoreError,
    facts_dir,
    is_r2,
    requested_location,
    store_root,
    write_object,
)

if TYPE_CHECKING:
    from vinci.facts.edgar_ingest import CachedResponse

#: The one namespace kept today: SEC responses (companyfacts and submissions documents).
NAMESPACE = "sec"
ORIGINAL_KEY = re.compile(r"^originals/[a-z]+/[0-9a-f]{64}\.json\.gz$")


def original_path(namespace: str, stored_sha256: str) -> str:
    return f"originals/{namespace}/{stored_sha256}.json.gz"


def originals_root(explicit: str | Path | None = None, *, base: Path | None = None) -> Path:
    """Where originals are kept locally: the object root of a local snapshot, never git.

    ``$VINCI_FACTS_STORE=r2://`` tells a READER to fetch a local snapshot from R2; it names no
    local directory, so it leaves the originals at the default local root rather than refusing a
    pages ingest, verify or upload that never reads the screen's objects."""
    if explicit is None and is_r2(requested_location(None, storage="local")):
        return (base or facts_dir()) / "local"
    return store_root(explicit, storage="local", base=base)


@dataclass(frozen=True)
class OriginalEntry:
    path: str              # originals/<namespace>/<sha256>.json.gz: the key, here and in R2
    sha256: str            # of the stored (gzipped) bytes: the name
    bytes: int             # of the stored bytes
    response_sha256: str   # of the response's UTF-8 text, as the manifest records it
    response_bytes: int
    url: str
    fetched_at: str        # YYYY-MM-DDTHH:MM:SSZ, when the cache fetched the copy


def stored_bytes(text: str) -> bytes:
    """The bytes an original is kept as: the text, UTF-8, gzipped with no timestamp."""
    return gzip.compress(text.encode("utf-8"), compresslevel=9, mtime=0)


def keep(resp: CachedResponse, root: Path, *, namespace: str = NAMESPACE) -> OriginalEntry:
    """Keep ``resp`` write-once under ``root`` and return its manifest entry. Writing the same
    response again is a no-op; other bytes under its name raise."""
    data = stored_bytes(resp.text)
    sha = hashlib.sha256(data).hexdigest()
    path = original_path(namespace, sha)
    write_object(root, path, data)
    return OriginalEntry(path=path, sha256=sha, bytes=len(data),
                         response_sha256=resp.sha256, response_bytes=len(resp.text.encode()),
                         url=resp.url, fetched_at=resp.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"))


def entry_dict(entry: OriginalEntry) -> dict[str, Any]:
    return asdict(entry)


_KEYS = ("path", "sha256", "bytes", "response_sha256", "response_bytes", "url", "fetched_at")


def check_entry(entry: Mapping[str, Any]) -> list[str]:
    """Every way an original's manifest entry is malformed; [] if none."""
    lack = [k for k in _KEYS if k not in entry]
    if lack:
        return [f"original {entry.get('path', '<no path>')} lacks {lack}"]
    if not ORIGINAL_KEY.fullmatch(str(entry["path"])) or not str(entry["path"]).endswith(
            f"/{entry['sha256']}.json.gz"):
        return [f"{entry['path']}: not the content-addressed name of its entry"]
    return []


def manifest_originals(manifest: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    """Every original a manifest records: each entity's response, then each submissions document
    its acceptance times were read from."""
    for e in manifest["entities"]:
        if "original" in e:
            yield e["original"]
        for d in (e.get("acceptance") or {}).get("documents", []):
            if "original" in d:
                yield d["original"]


def read_original(entry: Mapping[str, Any], root: Path) -> str:
    """The response text ``entry`` names, from ``root``: its stored bytes hashed against the
    entry, its text against the response's own sha256. Anything else raises."""
    problems = check_entry(entry)
    if problems:
        raise FactsStoreError(problems[0])
    p = root / str(entry["path"])
    if not p.is_file():
        raise FactsStoreError(f"{entry['path']}: the original is not under {root}")
    data = p.read_bytes()                     # read ONCE: the bytes hashed are the bytes decoded
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise FactsStoreError(f"{entry['path']}: its bytes do not hash to its name")
    text = gzip.decompress(data).decode("utf-8")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != entry["response_sha256"]:
        raise FactsStoreError(f"{entry['path']}: it does not hold the response "
                              f"{str(entry['response_sha256'])[:12]}… its entry names")
    return text


def verify_originals(manifest: Mapping[str, Any], root: Path) -> list[str]:
    """Every original the manifest records, read back from ``root`` and checked; [] if none."""
    problems: list[str] = []
    for entry in manifest_originals(manifest):
        try:
            read_original(entry, root)
        except FactsStoreError as exc:
            problems.append(str(exc))
        except (OSError, ValueError, EOFError) as exc:   # a torn gzip, a bad encoding
            problems.append(f"{entry.get('path')}: unreadable ({type(exc).__name__})")
    return problems


def parse(text: str) -> dict[str, Any]:
    body = json.loads(text)
    if not isinstance(body, dict):
        raise FactsStoreError(f"an original holds a {type(body).__name__}, not a JSON object")
    return body
