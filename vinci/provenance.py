"""WHAT A BUILD READ — recorded at the places its bytes enter, never reconstructed afterwards.

WHY (workstream B of the 2026-11-04 root-cause review, approved 2026-11-05). A committed page did
not record its inputs. It stamped the first 10 hex digits of two CIQ exports' sha256 (and none for
the rest it read: GOOGL's comps carried no stamp), nothing for the SEC responses it read, and only
the price store's GLOBAL frontier. So no check run anywhere else could tell whether the inputs in
front of it were the page's, and the CIQ-dependent tests either skipped as a class (CI) or failed
on an export the page was not built from. Record:
`docs/records/2026-11-05-every-page-records-what-it-was-built-from.md`.

THREE ENTRY POINTS, EACH THE ONLY DOOR FOR ITS CLASS:

- :class:`vinci.netcache.CachedHttp` — every SEC, Polygon and FINRA response, served from the cache
  or fetched (no other module in `vinci/` opens an HTTP connection: `grep` for `httpx.`,
  `urlopen`, `requests.` outside `netcache.py` finds only theme intelligence, 2026-11-05);
- :class:`vinci.store.store.Store` — every per-name price read. A whole-history read
  (`Store.get_price_history`, the one every page reader uses) is identified AT READ TIME by its
  rows (:func:`series_rows_sha256`), never by re-reading a store another checkout may be writing;
  a read of part of a series (one close, the dates) is recorded as partial, identifying nothing;
- the assembler's CIQ bundle — every export the page's readers read
  (`vinci.dossier.inputs.note_bundle`).

A RESPONSE IS HASHED BY THE FACT LAYER'S OWN RULE: the sha256 of its cached TEXT, UTF-8
(`vinci.facts.edgar_ingest.CachedResponse.sha256`), so a page's companyfacts input and a fact-layer
snapshot's entity record are the same identity, compared without translation.

HOW IT IS SCOPED. A recorder is a context-local sink (:data:`_ACTIVE`): a read made while one is
open is added to it and to every recorder it is nested in. A ``ThreadPoolExecutor`` worker starts
with no recorder, so each cohort worker opens its own — one page's reads never reach another's.
Nothing is recorded while no recorder is open, and a recorder never changes what is read.

LEAF MODULE: the standard library only, so `netcache` and `store` can call it without a cycle.
"""
from __future__ import annotations

import functools
import hashlib
import json
import re
import threading
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import ParamSpec, TypeVar
from urllib.parse import unquote, urlsplit, urlunsplit

_P = ParamSpec("_P")
_R = TypeVar("_R")

#: A query parameter whose VALUE is never recorded: the whole name, or its last ``_ - .``-separated
#: part, is a credential word (``apiKey``, ``x-api-key``, ``access_token``, ``sig``, ``auth`` —
#: never ``keyword`` or ``monkey``). Every client in this repo sends its key in a header
#: (`eod/client.py`, `eod/tiingo.py`), so none matches today; a URL that ever carries one is still
#: recorded, with the value replaced — the record is committed to a public repository.
_SECRET_NAME = re.compile(
    r"(?:^|[_\-.])(?:api[_\-]?key|key|(?:access[_\-]?)?token|secret|pass(?:word|wd)?|pwd"
    r"|signature|sig|auth(?:orization)?|credentials?)$", re.I)
_QUERY_SEP = re.compile(r"([&;])")
_PATH_PARAM = re.compile(r";(?P<name>[^;=/]+)=(?P<value>[^;/]*)")
REDACTED = "REDACTED"


def redact_url(url: str) -> str:
    """``url`` with every secret-shaped query value, and any userinfo (``user:pass@``), replaced by
    ``REDACTED`` — and EVERY OTHER BYTE AS IT WAS, so a redacted URL still matches its cache key and
    the fact layer's ``source_url`` (review round 2: re-encoding the query moved ``%20`` to ``+``).

    NOT covered, stated: a key embedded in the path, and a POST body (``<url>\\n#POST#<body>``,
    `CachedHttp.post_json`), kept as it is — the bodies sent are FINRA's query filters."""
    head, sep, body = url.partition("\n")
    parts = urlsplit(head)
    netloc = parts.netloc
    if "@" in netloc:
        netloc = f"{REDACTED}@{netloc.rsplit('@', 1)[1]}"
    pieces = _QUERY_SEP.split(parts.query) if parts.query else []
    for i in range(0, len(pieces), 2):
        name, eq, _value = pieces[i].partition("=")
        if _SECRET_NAME.search(unquote(name)):
            pieces[i] = f"{name}{eq or '='}{REDACTED}"
    query = "".join(pieces)
    # a path parameter (``/a;apiKey=…``) is a query in all but position
    path = _PATH_PARAM.sub(
        lambda m: f";{m['name']}={REDACTED}" if _SECRET_NAME.search(unquote(m["name"]))
        else m[0], parts.path)
    if netloc == parts.netloc and query == parts.query and path == parts.path:
        return url
    return urlunsplit(parts._replace(netloc=netloc, path=path, query=query)) + sep + body


def text_sha256(text: str) -> str:
    """The fact layer's response identity: sha256 of the text, UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> tuple[str, int]:
    """(full sha256, byte count) of a file's bytes. Raises ``OSError`` when it cannot be read."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


@dataclass(frozen=True)
class HttpRead:
    """One response a build read: which cache namespace, the URL (secret-shaped values redacted),
    when that copy was fetched (epoch seconds, None when the cache could not say) and its text's
    sha256 and length in bytes."""

    namespace: str
    url: str
    fetched_at: float | None
    sha256: str
    bytes: int


@dataclass(frozen=True)
class FileRead:
    """One file a build read: its role (``ciq``), its path, its bytes' sha256 and size — or the
    reason it could not be hashed (``sha256`` None), never a guessed hash."""

    role: str
    path: str
    sha256: str | None
    bytes: int | None
    kind: str | None = None
    freq: str | None = None
    error: str | None = None


#: How a whole-history price read is identified (`series_rows_sha256`): its rows' columns, in
#: order, each bar one canonical JSON line.
PriceRow = tuple[str, float, float, float, float, float, str]


def series_rows_sha256(rows: Iterable[PriceRow]) -> str:
    """THE ONE RULE for a price series' identity: sha256 over one canonical JSON line per bar
    (``[date, open, high, low, close, volume, source]``), oldest first. A store that later holds
    more bars re-hashes its rows through the recorded newest bar and compares; a restated or
    refiled bar (its ``source`` gains ``+restated`` / ``+refiled:``) is another identity."""
    digest = hashlib.sha256()
    for d, o, h, lo, c, v, src in sorted(rows, key=lambda r: r[0]):
        # every price column as a float, so the store's raw row (an integral volume) and the
        # `PriceBar` it becomes hash alike
        line = [str(d), float(o), float(h), float(lo), float(c), float(v), str(src)]
        digest.update(json.dumps(line, separators=(",", ":")).encode("utf-8") + b"\n")
    return digest.hexdigest()


@dataclass(frozen=True)
class SeriesRead:
    """One price read: by which `Store` method, and — for a whole-history read only — what it
    returned, identified at read time. A partial read (``rows_sha256`` None) identifies nothing."""

    internal_id: str
    via: str
    bars: int | None = None
    first_bar: str | None = None
    newest_bar: str | None = None
    rows_sha256: str | None = None


@dataclass(frozen=True)
class Reads:
    """A frozen set of reads, mergeable with ``|``."""

    http: frozenset[HttpRead] = frozenset()
    files: frozenset[FileRead] = frozenset()
    #: every price read from the store (`SeriesRead`)
    series: frozenset[SeriesRead] = frozenset()

    def __or__(self, other: Reads | None) -> Reads:
        if other is None:
            return self
        return Reads(self.http | other.http, self.files | other.files,
                     self.series | other.series)

    def __bool__(self) -> bool:
        return bool(self.http or self.files or self.series)


@dataclass
class InputRecorder:
    """The reads made while this recorder was open (and while any recorder nested in it was)."""

    parent: InputRecorder | None = None
    _http: dict[tuple[str, str, float | None, str], HttpRead] = field(default_factory=dict)
    _seen: set[tuple[str, str, float | None]] = field(default_factory=set)
    _files: set[FileRead] = field(default_factory=set)
    _series: set[SeriesRead] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _chain(self) -> Iterator[InputRecorder]:
        node: InputRecorder | None = self
        while node is not None:
            yield node
            node = node.parent

    def add_http(self, namespace: str, url: str, text: str, fetched_at: float | None) -> None:
        """Record one response. The text is hashed once per (namespace, url, fetched copy): the
        same cached copy read again adds nothing, while a copy re-fetched mid-build is a second
        read and is kept beside the first."""
        safe = redact_url(url)
        key = (namespace, safe, fetched_at)
        if all(key in node._seen for node in self._chain()):
            return
        raw = text.encode("utf-8")
        read = HttpRead(namespace, safe, fetched_at, hashlib.sha256(raw).hexdigest(), len(raw))
        for node in self._chain():
            with node._lock:
                node._seen.add(key)
                node._http[(namespace, safe, fetched_at, read.sha256)] = read

    def add_file(self, read: FileRead) -> None:
        for node in self._chain():
            with node._lock:
                node._files.add(read)

    def add_series(self, read: SeriesRead) -> None:
        for node in self._chain():
            with node._lock:
                node._series.add(read)

    def add_reads(self, reads: Reads | None) -> None:
        """Fold reads made elsewhere (a finalist built before this build, a resolver index loaded
        once per cohort) into this recorder and every one it is nested in."""
        if not reads:
            return
        for node in self._chain():
            with node._lock:
                for r in reads.http:
                    node._seen.add((r.namespace, r.url, r.fetched_at))
                    node._http[(r.namespace, r.url, r.fetched_at, r.sha256)] = r
                node._files |= reads.files
                node._series |= reads.series

    def reads(self) -> Reads:
        with self._lock:
            return Reads(frozenset(self._http.values()), frozenset(self._files),
                         frozenset(self._series))


_ACTIVE: ContextVar[InputRecorder | None] = ContextVar("vinci_input_recorder", default=None)


@contextmanager
def recording() -> Iterator[InputRecorder]:
    """Open a recorder for the reads made in this context, nested in any recorder already open."""
    rec = InputRecorder(parent=_ACTIVE.get())
    token = _ACTIVE.set(rec)
    try:
        yield rec
    finally:
        _ACTIVE.reset(token)


def recorded(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    """Run ``fn`` inside its own recorder (`recording`), which the body reads with `current`.
    A decorator rather than a ``with`` block so a long build function keeps its body as it is."""
    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        with recording():
            return fn(*args, **kwargs)
    return wrapper


def active() -> InputRecorder | None:
    return _ACTIVE.get()


def current() -> InputRecorder:
    """The open recorder. Raises when none is: a caller that needs one and has none is a bug."""
    rec = _ACTIVE.get()
    if rec is None:
        raise RuntimeError("no input recorder is open (see `vinci.provenance.recording`)")
    return rec


def note_http(namespace: str, url: str, text: str, fetched_at: float | None) -> None:
    """Called by `CachedHttp` for every response it returns. Nothing happens with no recorder."""
    rec = _ACTIVE.get()
    if rec is not None:
        rec.add_http(namespace, url, text, fetched_at)


def note_series(internal_ids: str | Iterable[str], *, via: str) -> None:
    """Called by `Store` for a read of PART of a series (one close, the dates, a session's bars):
    recorded as partial, identifying nothing. Nothing happens with no recorder."""
    rec = _ACTIVE.get()
    if rec is None:
        return
    for iid in ([internal_ids] if isinstance(internal_ids, str) else internal_ids):
        rec.add_series(SeriesRead(iid, via))


def note_series_read(internal_id: str, rows: list[PriceRow], *, via: str) -> None:
    """Called by `Store.get_price_history` with the rows it is about to return: the read is
    identified by them, at read time (`series_rows_sha256`). Nothing is hashed with no recorder."""
    rec = _ACTIVE.get()
    if rec is None:
        return
    ordered = sorted(rows, key=lambda r: r[0])
    rec.add_series(SeriesRead(
        internal_id, via, bars=len(ordered),
        first_bar=ordered[0][0] if ordered else None,
        newest_bar=ordered[-1][0] if ordered else None,
        rows_sha256=series_rows_sha256(ordered) if ordered else None))


def note_file(role: str, path: Path, *, kind: str | None = None,
              freq: str | None = None) -> None:
    """Hash and record one file a build reads. An unreadable file is recorded with its error and
    no hash. Nothing happens (and nothing is read) with no recorder."""
    rec = _ACTIVE.get()
    if rec is None:
        return
    try:
        sha, size = file_sha256(path)
        read = FileRead(role, str(path), sha, size, kind, freq)
    except OSError as exc:
        # the error's CLASS and reason only: an OSError's text carries the full local path, and
        # the record lands on a committed page in a public repository
        read = FileRead(role, str(path), None, None, kind, freq,
                        error=f"{type(exc).__name__}: {exc.strerror or 'unreadable'}")
    rec.add_file(read)
