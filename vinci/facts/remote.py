"""The fact layer's remote location: a Cloudflare R2 bucket, written by ONE machine, read anywhere.

``r2://`` (as ``$VINCI_FACTS_STORE`` or ``--store``) names the bucket the four ``R2_*`` variables
configure: ``R2_ACCOUNT_ID``, ``R2_ACCESS_KEY_ID``, ``R2_SECRET_ACCESS_KEY`` and ``R2_BUCKET``
(``.env`` locally, Actions secrets in CI). A missing one raises :class:`R2NotConfiguredError` naming
the VARIABLE, never a value.

THE KEY IS THE MANIFEST'S PATH. An object keeps its content-addressed name in the bucket
(``<source>/<entity>/<filed_year>/<content_id>.parquet``, and the entity's ``order/`` object), so
two snapshots that share a partition share one key, and the manifest in git is the only index.

IMMUTABLE REMOTELY TOO. :meth:`R2Client.put_new` writes with ``If-None-Match: *``, which R2
evaluates atomically ("at most one succeeds", Cloudflare's S3 API page, updated 2026-10-14), so an
existing key is never overwritten. When the key exists, its bytes are read back: the same bytes
are a no-op, different bytes raise :class:`RemoteBytesDifferError`. Every PUT carries the body's
``Content-MD5`` (R2 refuses a body that does not match it) and signs its sha256; after an upload
every object is read back and hashed against the manifest (:func:`upload_snapshot`).

A READER NEVER SERVES UNSEALED BYTES. :class:`R2Objects` fetches an object into a local cache
(``$VINCI_FACTS_CACHE``, else the git-ignored ``data/cache/facts``) by its manifest entry and checks
its sha256 before it is used. A key the bucket does not hold raises
:class:`RemoteObjectMissingError`; bytes that do not hash to the entry raise. There is no fallback
to another location.

ONE WRITER, READ-ONLY READERS. Only :func:`upload_snapshot` writes, from the machine that ingested
the snapshot. A reader needs only a token that can read the bucket.

THE ACCOUNT, THE ENDPOINT AND THE BUCKET ARE NEVER PRINTED. Every error names the operation, the
object key and the HTTP status (and S3's error code), never a URL; a transport error is re-raised
as its type name only. The ``httpx`` and ``httpcore`` loggers, which log each request's URL, get a
filter that replaces the four values (:func:`_redact_logs`).
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar
from xml.etree import ElementTree

import httpx

from vinci.facts.edgar_ingest import EXTRACTOR as EDGAR_EXTRACTOR
from vinci.facts.edgar_ingest import SOURCE as EDGAR_SOURCE
from vinci.facts.sigv4 import canonical_query, canonical_uri, sign
from vinci.facts.store import (
    FactsStoreError,
    RemoteStoreNotConfiguredError,
    _sha256_file,
    verify_manifest,
)

R2_VARS = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")
#: R2's region for SigV4 ("the region for an R2 bucket is `auto`", Cloudflare's S3 API page).
REGION = "auto"
CACHE_ENV = "VINCI_FACTS_CACHE"
DEFAULT_CACHE = Path("data") / "cache" / "facts"
#: What a transient failure looks like: retried with backoff, then raised.
_RETRY = frozenset({429, 500, 502, 503, 504})
_ACCOUNT = re.compile(r"^[A-Za-z0-9-]+$")
#: How every value in ``.env.example`` begins: copied unedited, it is refused by its name.
_PLACEHOLDER = "replace-with-"
_CODE = re.compile(r"<Code>([A-Za-z]+)</Code>")
#: A content-addressed key and nothing else: no ``..``, no absolute path, no other file.
_KEY = re.compile(
    r"^[a-z0-9_-]+/[A-Za-z0-9_-]+/(?:[0-9]{4}|order|filings)/[0-9a-f]{64}\.parquet$")
_S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


class R2NotConfiguredError(RemoteStoreNotConfiguredError):
    """``r2://`` was named, and a variable it needs is not set."""


class R2RequestError(FactsStoreError):
    """An R2 request failed: names the operation, the key and the status, never the endpoint."""


class RemoteObjectMissingError(FactsStoreError):
    """A manifest names an object the bucket does not hold."""


class RemoteBytesDifferError(FactsStoreError):
    """A key already holds bytes other than the ones being written: never overwritten."""


@dataclass(frozen=True)
class R2Config:
    account_id: str = field(repr=False)
    access_key_id: str = field(repr=False)
    secret_access_key: str = field(repr=False)
    bucket: str = field(repr=False)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> R2Config:
        env = os.environ if env is None else env
        missing = [n for n in R2_VARS if not env.get(n)]
        if missing:
            raise R2NotConfiguredError(
                f"r2:// needs {', '.join(missing)} in the environment (.env on this machine, the "
                "Actions secrets in CI); .env.example lists all four")
        placeholder = [n for n in R2_VARS if env[n].startswith(_PLACEHOLDER)]
        if placeholder:
            raise R2NotConfiguredError(
                f"{', '.join(placeholder)} is still .env.example's placeholder: set the real "
                "value in .env")
        padded = [n for n in R2_VARS if env[n] != env[n].strip()]
        if padded:
            raise R2NotConfiguredError(f"{', '.join(padded)} has leading or trailing whitespace")
        if not _ACCOUNT.match(env["R2_ACCOUNT_ID"]):
            raise R2NotConfiguredError("R2_ACCOUNT_ID is not an account id (letters, digits, -)")
        return cls(*(env[n] for n in R2_VARS))

    @property
    def host(self) -> str:
        """No jurisdiction (the bucket was created without one, 2026-11-05)."""
        return f"{self.account_id}.r2.cloudflarestorage.com"

    def secrets(self) -> tuple[str, ...]:
        return (self.account_id, self.access_key_id, self.secret_access_key, self.bucket)


# --- never print the endpoint ----------------------------------------------------------------

#: The loggers that print a request's URL or host: httpx at INFO, httpcore at DEBUG.
_URL_LOGGERS = ("httpx", "httpcore.connection", "httpcore.http11", "httpcore.http2",
                "httpcore.proxy", "httpcore.socks")
_installed: set[tuple[str, ...]] = set()
_install_lock = threading.Lock()


class _Redact(logging.Filter):
    def __init__(self, secrets: Sequence[str]) -> None:
        super().__init__()
        self._secrets = tuple(s for s in secrets if s)

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if any(s in msg for s in self._secrets):
            for s in self._secrets:
                msg = msg.replace(s, "<r2>")
            record.msg, record.args = msg, None
        return True


def _redact_logs(config: R2Config) -> None:
    key = config.secrets()
    with _install_lock:
        if key in _installed:
            return
        for name in _URL_LOGGERS:
            logging.getLogger(name).addFilter(_Redact(key))
        _installed.add(key)


# --- the client ------------------------------------------------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _code(r: httpx.Response) -> str:
    m = _CODE.search(r.text) if r.content else None
    return f" {m.group(1)}" if m else ""


class R2Client:
    """The four kinds of request the fact layer makes (HeadBucket, GetObject, PutObject and
    ListObjectsV2), signed with :func:`vinci.facts.sigv4.sign`.

    Thread-safe: each thread gets its own ``httpx.Client``. ``transport`` replaces the network
    (tests pass an ``httpx.MockTransport``); ``sleep`` the backoff."""

    def __init__(self, config: R2Config, *, transport: httpx.BaseTransport | None = None,
                 retries: int = 4, timeout: float = 60.0,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self._cfg = config
        self._transport = transport
        self._retries = retries
        self._timeout = timeout
        self._sleep = sleep
        self._local = threading.local()
        self._clients: list[httpx.Client] = []
        self._lock = threading.Lock()
        _redact_logs(config)

    @classmethod
    def from_env(cls, **kw: Any) -> R2Client:
        return cls(R2Config.from_env(), **kw)

    def __repr__(self) -> str:
        return "R2Client(<the bucket the R2_* variables name>)"

    def _http(self) -> httpx.Client:
        c: httpx.Client | None = getattr(self._local, "client", None)
        if c is None:
            c = httpx.Client(transport=self._transport, timeout=self._timeout)
            self._local.client = c
            with self._lock:
                self._clients.append(c)
        return c

    def close(self) -> None:
        with self._lock:
            for c in self._clients:
                c.close()
            self._clients.clear()

    def __enter__(self) -> R2Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _request(self, method: str, key: str, what: str, *,
                 query: Sequence[tuple[str, str]] = (), headers: Mapping[str, str] | None = None,
                 body: bytes = b"", retry: frozenset[int] = _RETRY) -> httpx.Response:
        cfg = self._cfg
        path = f"/{cfg.bucket}" + (f"/{key}" if key else "")
        url = f"https://{cfg.host}{canonical_uri(path)}"
        if query:
            url += "?" + canonical_query(query)
        payload = _sha256(body)
        err = ""
        for attempt in range(self._retries + 1):
            signed = sign(method, cfg.host, path, query=query,
                          headers={"accept-encoding": "identity", **(headers or {})},
                          payload_sha256=payload, access_key=cfg.access_key_id,
                          secret_key=cfg.secret_access_key, region=REGION)
            try:
                r = self._http().request(method, url, headers=signed,
                                         content=body if method == "PUT" else None)
            except httpx.HTTPError as exc:        # a transport error, or any other httpx one
                err = type(exc).__name__          # its message carries the URL: never shown
            else:
                if r.status_code not in retry:
                    return r
                err = f"HTTP {r.status_code}{_code(r)}"
            if attempt < self._retries:
                self._sleep(0.5 * 2 ** attempt)
        raise R2RequestError(f"{what}: {err} after {self._retries + 1} attempts")

    def head_bucket(self) -> int:
        """HeadBucket's status: 200 when the token can read the bucket."""
        return self._request("HEAD", "", "HeadBucket").status_code

    def get(self, key: str) -> bytes:
        r = self._request("GET", key, f"GetObject {key}")
        if r.status_code == 200:
            return r.content
        if r.status_code == 404:
            raise RemoteObjectMissingError(f"{key}: not in the R2 bucket")
        raise R2RequestError(f"GetObject {key}: HTTP {r.status_code}{_code(r)}")

    def put_new(self, key: str, data: bytes) -> bool:
        """Write ``data`` at ``key`` unless the key exists. True when written; False when the
        identical bytes were already there. Different bytes there raise."""
        md5 = base64.b64encode(hashlib.md5(data, usedforsecurity=False).digest()).decode()
        r = self._request("PUT", key, f"PutObject {key}", body=data,
                          headers={"if-none-match": "*", "content-md5": md5,
                                   "content-type": "application/octet-stream"},
                          retry=_RETRY | {409})     # 409: a concurrent conditional write
        if r.status_code == 200:
            return True
        if r.status_code != 412:
            raise R2RequestError(f"PutObject {key}: HTTP {r.status_code}{_code(r)}")
        held = self.get(key)
        if _sha256(held) != _sha256(data):
            raise RemoteBytesDifferError(
                f"{key}: the bucket holds other bytes under this name (sha256 {_sha256(held)}, "
                f"{len(held)} bytes; writing {_sha256(data)}, {len(data)} bytes). An object is "
                "never overwritten")
        return False

    def list_objects(self, prefix: str = "") -> Iterator[tuple[str, int]]:
        """Every (key, size) under ``prefix``, a page of up to 1,000 per request."""
        token: str | None = None
        while True:
            query = [("list-type", "2"), ("max-keys", "1000")]
            if prefix:
                query.append(("prefix", prefix))
            if token:
                query.append(("continuation-token", token))
            r = self._request("GET", "", "ListObjectsV2", query=query)
            if r.status_code != 200:
                raise R2RequestError(f"ListObjectsV2: HTTP {r.status_code}{_code(r)}")
            try:
                root = ElementTree.fromstring(r.content)
            except ElementTree.ParseError:
                raise R2RequestError("ListObjectsV2: not S3's XML (HTTP 200 from something "
                                     "other than the bucket)") from None
            for c in root.iter(f"{_S3_NS}Contents"):
                yield (c.findtext(f"{_S3_NS}Key") or "", int(c.findtext(f"{_S3_NS}Size") or -1))
            if root.findtext(f"{_S3_NS}IsTruncated") != "true":
                return
            token = root.findtext(f"{_S3_NS}NextContinuationToken")
            if not token:
                raise R2RequestError("ListObjectsV2: truncated with no continuation token")


# --- what a snapshot holds -----------------------------------------------------------------

def check_key(rel: str) -> str:
    """``rel`` when it is a content-addressed object key; else raise. A manifest is data: a path
    it names is never joined to a directory or sent as a key until it is checked."""
    if not _KEY.match(rel):
        raise FactsStoreError(f"{rel!r} is not a content-addressed object key")
    return rel


def manifest_objects(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every object a manifest names, data, order and (schema v3) filings, once each, sorted by
    path; each path checked (:func:`check_key`)."""
    entries = {f["path"]: f for f in manifest["files"]}
    for e in manifest["entities"]:
        entries.setdefault(e["order"]["path"], e["order"])
        if "filings" in e:
            entries.setdefault(e["filings"]["path"], e["filings"])
    return [entries[check_key(str(p))] for p in sorted(entries)]


#: The sources a snapshot may be uploaded for, each with the ONE writer of this code that makes
#: its rows (TeamNostra fix request 2, RFL-D6). Only EDGAR has one.
UPLOADABLE: dict[str, str] = {EDGAR_SOURCE: EDGAR_EXTRACTOR}


def upload_refusal(manifest: Mapping[str, Any]) -> str | None:
    """Why ``manifest`` may not be uploaded, or None (RFL-D6: a constructed ``ciq`` snapshot was
    uploaded whole, 2 of 2 objects, because nothing checked where its rows came from).

    A snapshot is uploaded only for a source this code writes, made by that source's writer, and
    every object it names is under that source. A CIQ snapshot has no writer here: nothing says its
    rows carry what the licence ruling of 2026-11-04 requires of a published CIQ value (the
    workbook's sha256, sheet and cell, and its export date as the knowable date), and the ADR's
    slice 4 keeps CIQ outputs local. Sending one is a decision for its slice, not for the
    uploader."""
    source, extractor = manifest.get("source"), manifest.get("extractor")
    if source not in UPLOADABLE:
        return (f"source {source!r} has no writer in this code ({sorted(UPLOADABLE)} do): its "
                "rows were not made here, so nothing shows they carry what the licence ruling of "
                "2026-11-04 requires of a published value, and the ADR keeps CIQ outputs local "
                "(slice 4, docs/records/2026-11-04-fact-layer-adr.md)")
    if extractor != UPLOADABLE[source]:
        return (f"its extractor {extractor!r} is not source {source!r}'s writer "
                f"{UPLOADABLE[source]!r}")
    wrong = sorted({str(f["path"]) for f in manifest["files"] if f.get("source") != source}
                   | {str(e["path"]) for e in manifest_objects(manifest)
                      if not str(e["path"]).startswith(f"{source}/")})
    if wrong:
        return f"{len(wrong)} object(s) it names are not source {source!r}'s ({_shown(wrong)})"
    return None


_T = TypeVar("_T")
_R = TypeVar("_R")


def _parallel(fn: Callable[[_T], _R], items: Sequence[_T], workers: int) -> list[_R]:
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return list(pool.map(fn, items))


def _shown(problems: Sequence[str], k: int = 5) -> str:
    """A truncated list prints its own truncation (CLAUDE.md)."""
    head = "; ".join(problems[:k])
    return f"showing {min(k, len(problems))} of {len(problems)}: {head}"


# --- reading from R2 -------------------------------------------------------------------------

@dataclass
class FetchReport:
    objects: int = 0
    bytes: int = 0
    fetched: int = 0
    fetched_bytes: int = 0
    cached: int = 0
    problems: list[str] = field(default_factory=list)


class R2Objects:
    """A snapshot's objects read from R2 into a local cache by their manifest entries."""

    def __init__(self, client: R2Client, cache: Path) -> None:
        self.client = client
        self.cache = cache

    @classmethod
    def from_env(cls, cache: Path | None = None, **kw: Any) -> R2Objects:
        raw = os.environ.get(CACHE_ENV, "")
        return cls(R2Client.from_env(**kw), cache or (Path(raw) if raw else DEFAULT_CACHE))

    def fetch(self, entry: Mapping[str, Any]) -> tuple[Path, bool]:
        """The entry's object on disk, its sha256 checked; True when it came from R2 now. A
        cached copy that does not hash to the entry is fetched again; R2's bytes that do not
        raise."""
        rel, want = check_key(str(entry["path"])), str(entry["sha256"])
        p = self.cache / rel
        if p.is_file() and p.stat().st_size == entry["bytes"] and _sha256_file(p) == want:
            return p, False
        data = self.client.get(rel)
        if _sha256(data) != want:
            raise FactsStoreError(
                f"{rel}: the bytes R2 holds (sha256 {_sha256(data)}, {len(data)} bytes) are not "
                f"the manifest's ({want}, {entry['bytes']} bytes)")
        tmp = p.with_name(f".{p.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(data)
            os.replace(tmp, p)                # never a partial object at its name
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            raise FactsStoreError(f"{rel}: could not be written to the cache "
                                  f"({type(exc).__name__})") from None
        return p, True

    def fetch_all(self, entries: Sequence[Mapping[str, Any]], *, workers: int = 16
                  ) -> FetchReport:
        """Every entry fetched (or found cached), each checked; every failure counted, none
        raised, so a verify reports them all."""
        def one(e: Mapping[str, Any]) -> tuple[Mapping[str, Any], bool | None, str]:
            try:
                return e, self.fetch(e)[1], ""
            except FactsStoreError as exc:
                return e, None, str(exc)
        rep = FetchReport(objects=len(entries), bytes=sum(int(e["bytes"]) for e in entries))
        for e, fresh, problem in _parallel(one, list(entries), workers):
            if fresh is None:
                rep.problems.append(problem)
            elif fresh:
                rep.fetched += 1
                rep.fetched_bytes += int(e["bytes"])
            else:
                rep.cached += 1
        return rep


# --- writing to R2 ---------------------------------------------------------------------------

@dataclass
class UploadReport:
    snapshot_id: str
    objects: int = 0
    bytes: int = 0
    written: int = 0
    written_bytes: int = 0
    present: int = 0
    present_bytes: int = 0
    not_attempted: int = 0
    read_back: int = 0
    read_back_bytes: int = 0
    problems: list[str] = field(default_factory=list)


def upload_snapshot(manifest: dict[str, Any], local_root: Path, client: R2Client, *,
                    workers: int = 16, read_back: bool = True) -> UploadReport:
    """Upload every object ``manifest`` names from ``local_root``, then read each one back.

    Refused before any request when the local copy does not verify against the manifest (an
    object missing, or its bytes not the sealed ones): only sealed bytes are uploaded. Objects are
    read from the manifest's entries, never by listing ``local_root``, so nothing the manifest
    does not name (another snapshot's objects, say) can be sent.

    Every object's outcome is counted: written, already there with the same bytes, or a problem
    (other bytes under its key are never overwritten). A request that fails outright (a token
    that may not write, say) stops the objects not yet sent, which are counted as not attempted."""
    sid = str(manifest["snapshot_id"])
    if (why := upload_refusal(manifest)) is not None:
        raise FactsStoreError(f"{sid}: nothing was uploaded — {why}")
    local = verify_manifest(manifest, local_root, check_content=False)
    if local:
        raise FactsStoreError(f"{sid}: the local copy under {local_root} does not verify, so "
                              f"nothing was uploaded ({_shown(local)})")
    entries = manifest_objects(manifest)
    rep = UploadReport(snapshot_id=sid, objects=len(entries),
                       bytes=sum(int(e["bytes"]) for e in entries))
    stop = threading.Event()

    def put(e: dict[str, Any]) -> str:
        if stop.is_set():
            return "not attempted"
        try:
            data = (local_root / e["path"]).read_bytes()
        except OSError as exc:
            return f"{e['path']}: unreadable on disk ({type(exc).__name__}); not uploaded"
        if _sha256(data) != e["sha256"]:
            return f"{e['path']}: changed on disk since it was verified; not uploaded"
        try:
            return "written" if client.put_new(str(e["path"]), data) else "present"
        except RemoteBytesDifferError as exc:
            return str(exc)
        except FactsStoreError as exc:
            stop.set()
            return str(exc)

    for e, outcome in zip(entries, _parallel(put, entries, workers), strict=True):
        if outcome == "written":
            rep.written += 1
            rep.written_bytes += int(e["bytes"])
        elif outcome == "present":
            rep.present += 1
            rep.present_bytes += int(e["bytes"])
        elif outcome == "not attempted":
            rep.not_attempted += 1
        else:
            rep.problems.append(outcome)
    if not read_back or rep.problems or rep.not_attempted:
        return rep

    def back(e: dict[str, Any]) -> str:
        try:
            data = client.get(str(e["path"]))
        except FactsStoreError as exc:
            return str(exc)
        if _sha256(data) != e["sha256"]:
            return (f"{e['path']}: read back as sha256 {_sha256(data)}, the manifest says "
                    f"{e['sha256']}")
        return ""

    for e, problem in zip(entries, _parallel(back, entries, workers), strict=True):
        if problem:
            rep.problems.append(problem)
        else:
            rep.read_back += 1
            rep.read_back_bytes += int(e["bytes"])
    return rep


def bucket_against_manifests(client: R2Client, manifests: Iterable[Mapping[str, Any]]
                             ) -> dict[str, int]:
    """The bucket's keys against every object the given manifests name: how many keys and bytes
    it holds, how many of those some manifest names, how many no manifest names, and how many
    named objects it lacks."""
    named = {e["path"]: int(e["bytes"]) for m in manifests for e in manifest_objects(m)}
    keys = dict(client.list_objects())
    return {"bucket_keys": len(keys), "bucket_bytes": sum(keys.values()),
            "named_by_a_manifest": len(keys.keys() & named.keys()),
            "named_by_none": len(keys.keys() - named.keys()),
            "named_and_absent": len(named.keys() - keys.keys()),
            "size_differs": sum(1 for k in keys.keys() & named.keys() if keys[k] != named[k]),
            "manifest_objects": len(named), "manifest_bytes": sum(named.values())}
