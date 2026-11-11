"""Read facts as of a moment: DuckDB over a snapshot's Parquet. Embedded, in memory, read-only.

POINT-IN-TIME IS ONE PREDICATE, AND IT READS THE ACCEPTANCE TIME (TeamNostra fix request 2,
RFL-D2). Every query in this module is built by :func:`_latest_sql` or :func:`_rows_sql`, and both
cut with :func:`_visible`. A read ``as_of`` a DATE stands at that day's 16:00 New York close; a
read ``as_of`` a zone-aware DATETIME stands at that instant (:func:`cut_instant`). A row is in the
cut when its filing's SEC acceptance time (schema v3's filings object) is at or before that
moment. companyfacts dates a filing only to the DAY, and the old cut, ``filed_date <= as_of``,
served a 10-Q accepted at 16:25 to a replay priced at that day's 16:00 close: 84,466 of the
175,193 latest facts of the committed pages' companies whose filing is on the cached submissions
page were accepted after their own filing day's close. A row whose filing has NO acceptance time
(every row of a schema-v2 snapshot, or an accession the submissions documents do not list) is in
the cut when filed on an EARLIER day, out when filed on a later day, and, when filed ON the cut's
day, cannot be placed: a key that holds one raises :class:`FactCutUndeterminedError` rather than
guessing which side of the close it fell. ``basis="filed"`` is the old day-level cut, kept for
the shadow comparisons against the page's reader, which still cuts by day
(:func:`vinci.edgar.concepts.facts_as_of`). Among the filings in the cut the LATEST DAY wins, which
is how a restatement replaces its original from its own filing onward and not before.

MISSING IS LOUD, AND SAYS WHICH MISSING (RFL-D5). :meth:`FactStore.get` raises
:class:`FactNotHeldError` when the snapshot does not hold the entity at all (it was not ingested),
and :class:`FactUnknownError` when it holds the entity and nothing was filed by the cut (no such
concept, no such period, or only later filings). It raises :class:`FactAmbiguousError` when the
latest day's filings state DIFFERENT values for the same period, as a 10-K/A and a 10-Q/A filed the
same day can (measured on the committed pages' companies, 2026-11-04: 14 such keys). Nothing is
imputed, and no tie is broken by guesswork.

A COPY KNOWS ONLY WHAT WAS FILED BEFORE IT WAS FETCHED (RFL-D1). Each entity's facts are one
cached companyfacts response, fetched at the manifest's ``fetched_at``. A read whose cut is past
that moment would serve the copy's latest value as the value as of the cut, though a later filing
may have restated it. It raises :class:`FactStaleError`, unless the caller passes
``stale_ok=True``; then every fact carries ``fetched_at`` and ``stale=True``.

THE READER CHECKS WHAT THE MANIFEST SEALS (RFL-D4). On open it recomputes the snapshot id from the
manifest's own content; the first time an object is read, its bytes hash to its entry AND its rows
hash to its name. An object edited together with its manifest entry, which the byte check alone
served under the old snapshot id, is refused.

THE RESPONSE'S ORDER IS ITS OWN OBJECT (schema v2). A data object holds its rows in their canonical
order, so its name is its content; :meth:`FactStore.companyfacts_as_of` puts them back in the
response's order by joining each row to the entity's order object on (object, row), and a row the
order object does not map raises rather than being dropped or misplaced.

A LOCAL SNAPSHOT IS READ WHERE ITS OBJECTS ARE. A snapshot whose manifest says ``storage: local``
has its objects on the machine that wrote them and, once uploaded, in R2. Opened with ``r2://``
(``root`` or ``$VINCI_FACTS_STORE``), every object is fetched from the bucket into a local cache by
its manifest entry and its sha256 checked (:class:`vinci.facts.remote.R2Objects`); a key the bucket
lacks or bytes that do not match raise. Opened with neither, where the directory is absent, it
raises :class:`FactsStoreNotPresentError` at open. The location is the caller's choice: there is
no fallback from one to the other.

AGENTS ONLY READ. The connection is an in-memory DuckDB with no database file, so there is no
writable DuckDB file for two processes to share (DuckDB allows one read-write process). The one
writer per source publishes Parquet objects and a manifest (:mod:`vinci.facts.store`).
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from zoneinfo import ZoneInfo

import duckdb

from vinci.edgar.concepts import ANNUAL_REPORT_FORMS
from vinci.facts.store import (
    DEFAULT_NAME,
    FactsStoreError,
    _read_rows,
    _sha256_file,
    is_r2,
    load_manifest,
    requested_location,
    rows_match_name,
    snapshot_id_for,
    store_root,
)

if TYPE_CHECKING:
    from vinci.facts.remote import R2Objects

#: The periodic reports (and, by prefix, their amendments: 10-K/A, 10-Q/A, 10-KT, 20-F/A). On a
#: same-day, same-value tie one of these is named over a proxy or any other form: NKE's FY2024 net
#: income is stated identically by its 10-K and its DEF 14A, both filed 2026-07-15, and the page's
#: readers filter on these same forms (`vinci.edgar.concepts`, `ANNUAL_REPORT_FORMS`, 10-Q/10-K).
PERIODIC_FORMS: tuple[str, ...] = (*ANNUAL_REPORT_FORMS, "10-Q")

#: Where a date's cut stands: the US equity close, in New York's own clock (EST or EDT).
NEW_YORK = ZoneInfo("America/New_York")
MARKET_CLOSE = time(16, 0)

#: ``accepted``: a row is in the cut from its filing's SEC acceptance time (the default).
#: ``filed``: from the start of its ``filed_date`` — the day-level cut the page's reader still
#: makes, for the shadow comparisons only.
Basis = Literal["accepted", "filed"]
ACCEPTED: Basis = "accepted"
FILED: Basis = "filed"


def is_periodic(form: str | None) -> bool:
    return str(form or "").upper().startswith(PERIODIC_FORMS)


class FactUnknownError(LookupError):
    """The snapshot holds the entity and nothing was filed by the cut: UNKNOWN, never a guess."""


class FactNotHeldError(LookupError):
    """The snapshot does not hold the entity at all: it was not ingested, which says nothing about
    what the entity filed (RFL-D5)."""


class FactAmbiguousError(LookupError):
    """The latest filing day states different values for one period; the store will not choose."""


class FactCutUndeterminedError(LookupError):
    """A filing dated the cut's own day states no acceptance time, so whether it was public at the
    cut cannot be said (RFL-D2)."""


class FactStaleError(LookupError):
    """The read's cut is past the moment the entity's copy was fetched: the copy cannot know what
    was filed since, so its latest value is not the value as of the cut (RFL-D1)."""


class FactsStoreNotPresentError(FactsStoreError):
    """A locally stored snapshot was opened where its objects are not."""


def cut_instant(as_of: date | datetime) -> datetime:
    """The UTC moment a read ``as_of`` stands at: a date's 16:00 New York close, or the datetime
    itself, which must carry its zone. Returned naive, in UTC, as the filings object stores it."""
    if isinstance(as_of, datetime):
        if as_of.tzinfo is None:
            raise ValueError(f"as_of {as_of!r} is a datetime with no time zone: say which moment")
        return as_of.astimezone(UTC).replace(tzinfo=None)
    return datetime.combine(as_of, MARKET_CLOSE, NEW_YORK).astimezone(UTC).replace(tzinfo=None)


def cut_day(as_of: date | datetime) -> date:
    """The New York day a read ``as_of`` stands on."""
    if isinstance(as_of, datetime):
        cut_instant(as_of)                     # refuses a naive datetime
        return as_of.astimezone(NEW_YORK).date()
    return as_of


def knowable_by(as_of: date | datetime, basis: Basis) -> datetime:
    """The moment a copy must have been fetched at or after to know everything ``as_of``'s cut
    holds (naive UTC): the cut itself, or for the day-level cut the end of its day in New York."""
    if basis == FILED:
        nxt = datetime.combine(cut_day(as_of) + timedelta(days=1), time(0, 0), NEW_YORK)
        return nxt.astimezone(UTC).replace(tzinfo=None)
    return cut_instant(as_of)


@dataclass(frozen=True)
class Period:
    """A duration (``start``..``end``) or, with ``start`` None, an instant at ``end``."""

    end: date
    start: date | None = None

    @classmethod
    def instant(cls, end: date) -> Period:
        return cls(end=end)

    @classmethod
    def duration(cls, start: date, end: date) -> Period:
        return cls(end=end, start=start)


@dataclass(frozen=True)
class SourceRef:
    """Where a fact was stated: the filing's accession and the XBRL tag it was stated under."""

    accession: str
    taxonomy: str
    concept: str

    def __str__(self) -> str:
        return f"EDGAR XBRL {self.taxonomy}:{self.concept} accn {self.accession}"


@dataclass(frozen=True)
class Fact:
    entity: str
    taxonomy: str
    concept: str
    unit: str
    period: Period
    value: float
    filed_date: date
    accession: str
    form: str | None
    fiscal_year: int | None
    fiscal_period: str | None
    snapshot_id: str
    #: other filings made the SAME day that state the SAME value for this period (usually none).
    #: ``accession`` is a periodic report's (:data:`PERIODIC_FORMS`) when any of them is one, and
    #: among those the greatest accession, so the choice is deterministic and never a proxy's
    concurrent_accessions: tuple[str, ...] = ()
    #: when SEC accepted ``accession``'s filing (UTC), None where the snapshot states none
    accepted_at: datetime | None = None
    #: when the entity's copy was fetched (UTC): the copy knows nothing filed after it
    fetched_at: datetime | None = None
    #: the read's cut is past ``fetched_at`` (served only with ``stale_ok=True``)
    stale: bool = False

    @property
    def source_ref(self) -> SourceRef:
        return SourceRef(self.accession, self.taxonomy, self.concept)


@dataclass(frozen=True)
class FrameResult:
    """One concept and period across entities. EVERY requested entity lands in exactly one field."""

    facts: dict[str, Fact]
    unknown: tuple[str, ...]                      # held, and nothing filed by the cut
    ambiguous: dict[str, str] = field(default_factory=dict)   # entity -> why
    not_held: tuple[str, ...] = ()                # the snapshot does not hold the entity
    undetermined: dict[str, str] = field(default_factory=dict)  # entity -> why (RFL-D2)


def _split_concept(concept: str) -> tuple[str, str]:
    taxonomy, sep, tag = concept.partition(":")
    if not sep or not taxonomy or not tag:
        raise ValueError(f"concept {concept!r} must be qualified as '<taxonomy>:<tag>'")
    return taxonomy, tag


def pad_entity(entity: int | str) -> str:
    return f"{int(entity):010d}"


def _file_list(paths: Sequence[Path]) -> str:
    """A DuckDB list literal of object paths (content hashes; anything carrying a quote raises)."""
    out = []
    for p in paths:
        s = p.as_posix()
        if "'" in s:
            raise FactsStoreError(f"object path {s!r} carries a quote")
        out.append(f"'{s}'")
    return "[" + ", ".join(out) + "]"


#: The columns a Fact is built from, in this order.
_FACT_COLS = ("entity", "taxonomy", "concept", "unit", "period_start", "period_end", "value",
              "filed_date", "accession", "form", "fiscal_year", "fiscal_period")


def _visible(basis: Basis) -> str:
    """Whether a row is in the cut: TRUE, FALSE, or NULL when it cannot be placed. Its bound
    parameters are :func:`_cut_params`'."""
    if basis == FILED:
        return "filed_date <= ?::DATE"
    return ("CASE WHEN accepted_at IS NOT NULL THEN accepted_at <= ?::TIMESTAMP "
            "WHEN filed_date < ?::DATE THEN TRUE WHEN filed_date = ?::DATE THEN NULL "
            "ELSE FALSE END")


def _cut_params(as_of: date | datetime, basis: Basis) -> list[Any]:
    day = cut_day(as_of)
    return [day] if basis == FILED else [cut_instant(as_of), day, day]


def _accepted(data: str, filings: str | None, *, on: str) -> str:
    """``data`` (a FROM item aliased ``d``) with each row's filing acceptance time, NULL where
    the snapshot states none."""
    if filings is None:
        return f"SELECT d.*, NULL::TIMESTAMP AS accepted_at FROM {data}"
    return (f"SELECT d.*, g.accepted_at FROM {data} LEFT JOIN read_parquet({filings}) AS g "
            f"ON {on}")


def _latest_sql(files: str, filings: str | None, filters: Sequence[str], basis: Basis) -> str:
    """The latest filing in the cut for every key that passes ``filters``: every row filed on that
    key's latest day, so a same-day disagreement is visible, each with whether the key holds a
    row the cut cannot place (and one such accession). Parameters: :func:`_cut_params`, then the
    filters'."""
    base = _accepted(f"read_parquet({files}) AS d", filings,
                     on="d.entity = g.entity AND d.accession = g.accession")
    return f"""
        WITH base AS ({base}),
        cut AS (SELECT *, ({_visible(basis)}) AS visible FROM base WHERE {" AND ".join(filters)}),
        ranked AS (
            SELECT *, max(filed_date) OVER w AS latest,
                   max(CASE WHEN visible IS NULL THEN accession END) OVER w AS unplaced
            FROM cut WHERE visible IS NOT FALSE
            WINDOW w AS (PARTITION BY entity, taxonomy, concept, unit, period_start, period_end))
        SELECT {", ".join(_FACT_COLS)}, accepted_at, unplaced FROM ranked WHERE filed_date = latest
        ORDER BY entity, taxonomy, concept, unit, period_start NULLS FIRST, period_end, accession
    """


#: A data object's content id, read back from the path DuckDB reports for each row.
_OBJECT_OF_PATH = r"([0-9a-f]{64})\.parquet$"


def _rows_sql(files: str, order: str, filings: str | None, basis: Basis) -> str:
    """Every row in the cut (parameters :func:`_cut_params`), in the source response's order: each
    row joined to its place in ``order`` on (its object's content id, its row in that object). A
    row the order object does not map comes back with a null position, and the caller raises; so
    does a row the cut cannot place (``visible`` NULL)."""
    data = f"""(SELECT taxonomy, concept, unit, period_start, period_end, value, accession,
                       fiscal_year, fiscal_period, form, filed_date, frame,
                       regexp_extract(filename, '{_OBJECT_OF_PATH}', 1) AS object,
                       file_row_number AS row
                FROM read_parquet({files}, filename=true, file_row_number=true)) AS d"""
    base = _accepted(data, filings, on="d.accession = g.accession")
    return f"""
        WITH base AS ({base}),
        cut AS (SELECT *, ({_visible(basis)}) AS visible FROM base)
        SELECT cut.taxonomy, cut.concept, cut.unit, cut.period_start, cut.period_end, cut.value,
               cut.accession, cut.fiscal_year, cut.fiscal_period, cut.form, cut.filed_date,
               cut.frame, o.source_position, cut.visible
        FROM cut LEFT JOIN read_parquet({order}) AS o ON cut.object = o.object AND cut.row = o.row
        WHERE cut.visible IS NOT FALSE
        ORDER BY o.source_position NULLS FIRST
    """


Key = tuple[str, str, str, str, date | None, date]   # entity, taxonomy, concept, unit, start, end
#: A key the store will not answer, and why.
Unresolved = FactAmbiguousError | FactCutUndeterminedError


def _utc(t: datetime | None) -> datetime | None:
    return t.replace(tzinfo=UTC) if t is not None else None


def _parse_fetched(raw: Any) -> datetime | None:
    """A manifest's ``fetched_at`` (``YYYY-MM-DDTHH:MM:SSZ``) as naive UTC, None if absent."""
    if not raw:
        return None
    return datetime.strptime(str(raw), "%Y-%m-%dT%H:%M:%SZ")


def _group_latest(rows: Iterable[tuple[Any, ...]], snapshot_id: str, *, day: date,
                  fetched: dict[str, datetime | None], stale: frozenset[str]
                  ) -> dict[Key, Fact | Unresolved]:
    grouped: dict[Key, list[tuple[Any, ...]]] = {}
    for r in rows:
        grouped.setdefault((r[0], r[1], r[2], r[3], r[4], r[5]), []).append(r)
    out: dict[Key, Fact | Unresolved] = {}
    for key, rs in grouped.items():
        # A ROW THE CUT CANNOT PLACE DECIDES THE KEY ONLY ON ITS OWN DAY (review round 0): a
        # later day's filing in the cut (one accepted after 17:30, which SEC dates the next
        # business day, read at an evening cut) supersedes it whichever side of the cut it fell
        if (unplaced := rs[0][13]) is not None and rs[0][7] == day:
            out[key] = FactCutUndeterminedError(
                f"{key[0]} {key[1]}:{key[2]} [{key[3]}] {key[4]}..{key[5]}: a filing dated "
                f"{day} ({unplaced}) states no acceptance time in snapshot {snapshot_id}, so "
                "whether it was public at the cut cannot be said")
            continue
        values = {r[6] for r in rs}
        if len(values) > 1:
            stated = ", ".join(f"{r[6]!r} in {r[8]} ({r[9]})" for r in rs)
            out[key] = FactAmbiguousError(
                f"{key[0]} {key[1]}:{key[2]} [{key[3]}] {key[4]}..{key[5]}: filings of {rs[0][7]} "
                f"state different values ({stated})")
            continue
        top = max(rs, key=lambda r: (is_periodic(r[9]), r[8]))
        out[key] = Fact(
            entity=key[0], taxonomy=key[1], concept=key[2], unit=key[3],
            period=Period(end=key[5], start=key[4]), value=float(top[6]), filed_date=top[7],
            accession=top[8], form=top[9], fiscal_year=top[10], fiscal_period=top[11],
            snapshot_id=snapshot_id,
            concurrent_accessions=tuple(sorted(r[8] for r in rs if r[8] != top[8])),
            accepted_at=_utc(top[12]), fetched_at=_utc(fetched.get(key[0])),
            stale=key[0] in stale)
    return out


class FactStore:
    """One snapshot, opened for reading.

    ``verify`` (default True) recomputes the snapshot id from the manifest on open, and the first
    time an object is touched hashes its bytes against its manifest entry and its rows against its
    name: :class:`FactsStoreError` if one is missing or does not match. A reader never serves a
    fact from bytes, or rows, the manifest did not seal.

    ``name`` picks which current snapshot of ``source`` (``pages``, the committed one, or
    ``screen``); ``root`` overrides where its objects are read from: a directory, or ``r2://``.
    ``remote`` supplies the R2 reader ``r2://`` uses (tests; else one from the ``R2_*``
    variables). An object fetched from R2 is checked against its entry whatever ``verify`` says."""

    def __init__(self, snapshot_id: str | None = None, *, source: str = "edgar",
                 name: str = DEFAULT_NAME, facts_base: Path | None = None,
                 root: str | Path | None = None, verify: bool = True,
                 remote: R2Objects | None = None) -> None:
        self.manifest = load_manifest(snapshot_id, source=source, name=name, base=facts_base)
        self.snapshot_id: str = self.manifest["snapshot_id"]
        if snapshot_id is not None and self.snapshot_id != snapshot_id:
            raise FactsStoreError(f"the manifest filed as {snapshot_id} says it is "
                                  f"{self.snapshot_id}")
        # THE ID IS THE CONTENT'S (RFL-D4): an object edited together with its entry left a
        # manifest whose id no longer recomputes, and the reader served it under the old id
        if verify and snapshot_id_for(self.manifest) != self.snapshot_id:
            raise FactsStoreError(f"snapshot {self.snapshot_id}: the manifest's content does not "
                                  "recompute to its id — it was edited after it was sealed")
        self.storage: str = self.manifest["storage"]
        self._facts_base = facts_base          # where `original()` finds the local originals root
        self._remote: R2Objects | None = None
        self._owns_remote = False
        if is_r2(requested_location(root, storage=self.storage)):
            from vinci.facts.remote import R2Objects
            self._remote = remote if remote is not None else R2Objects.from_env()
            self._owns_remote = remote is None
            self.root = self._remote.cache
        else:
            self.root = store_root(root, storage=self.storage, base=facts_base)
        if self._remote is None and self.storage == "local" and not self.root.is_dir():
            raise FactsStoreNotPresentError(
                f"snapshot {self.snapshot_id} is stored locally and its objects are not here "
                f"({self.root} does not exist): they are on the machine that wrote them and, if "
                "uploaded, in R2. Read them from R2 with root='r2://' (or $VINCI_FACTS_STORE=r2://"
                "), set $VINCI_FACTS_STORE to where they are, or ingest here from the SEC cache")
        self._verify = verify
        self._verified: set[str] = set()
        self._files: dict[str, list[dict[str, Any]]] = {}
        for f in self.manifest["files"]:
            self._files.setdefault(f["entity"], []).append(f)
        held = self.manifest["entities"]
        self._orders: dict[str, dict[str, Any]] = {e["entity"]: e["order"] for e in held}
        #: schema v3: each entity's filings object; v2 states no acceptance time
        self._filings: dict[str, dict[str, Any]] = {
            e["entity"]: e["filings"] for e in held if "filings" in e}
        self._fetched: dict[str, datetime | None] = {
            e["entity"]: _parse_fetched(e.get("fetched_at")) for e in held}
        self._con = duckdb.connect(":memory:")

    def close(self) -> None:
        self._con.close()
        if self._remote is not None and self._owns_remote:
            self._remote.client.close()

    def __enter__(self) -> FactStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def entities(self) -> tuple[str, ...]:
        return tuple(sorted(self._files))

    def original(self, entity: int | str, *, originals: Path | None = None) -> dict[str, Any]:
        """The response the snapshot ingested for ``entity``, rebuilt from its ORIGINAL (RFL-D3):
        from R2 when the store reads ``r2://``, else from ``originals`` (default: the local
        originals root beside this store's ``facts_base``). Its bytes and its text are checked
        against both hashes the manifest records; a snapshot that kept none, or an original that
        cannot be read or parsed, raises :class:`FactsStoreError`."""
        from vinci.facts.originals import originals_root, parse, read_original
        ent = self._held(entity)
        entry = next((e.get("original") for e in self.manifest["entities"]
                      if e["entity"] == ent), None)
        if entry is None:
            raise FactsStoreError(f"{ent}: snapshot {self.snapshot_id} kept no original of the "
                                  "response it read")
        if self._remote is not None:
            self._remote.fetch(entry)                 # raises on a missing key or other bytes
            root = self._remote.cache
        else:
            root = originals if originals is not None else originals_root(base=self._facts_base)
        try:
            return parse(read_original(entry, root))
        except (OSError, ValueError, EOFError) as exc:   # a torn gzip, a bad encoding, bad JSON
            raise FactsStoreError(f"{entry.get('path')}: the original is unreadable "
                                  f"({type(exc).__name__})") from exc

    def fetched_at(self, entity: int | str) -> datetime | None:
        """When the snapshot's copy of ``entity``'s facts was fetched (UTC), None if not stated."""
        return _utc(self._fetched.get(pad_entity(entity)))

    def is_stale(self, entity: int | str, as_of: date | datetime, *,
                 basis: Basis = ACCEPTED) -> bool:
        """``as_of``'s cut is past the moment the entity's copy was fetched (RFL-D1). A copy with
        no stated fetch time is stale at every cut: it cannot say what it knows."""
        fetched = self._fetched.get(pad_entity(entity))
        return fetched is None or fetched < knowable_by(as_of, basis)

    def _path(self, entry: dict[str, Any], kind: str = "data") -> Path:
        """An object's path, its bytes and rows checked against the manifest the first time it is
        read: the bytes against its entry's sha256, the rows against its content-addressed name."""
        if self._remote is not None:
            if entry["path"] not in self._verified:
                p, _ = self._remote.fetch(entry)    # raises on a missing key or unsealed bytes
                if not rows_match_name(_read_rows(p), entry, kind):
                    raise FactsStoreError(f"{entry['path']}: its rows do not hash to its name in "
                                          f"snapshot {self.snapshot_id}")
                self._verified.add(entry["path"])
            return Path(self.root / entry["path"])
        p = self.root / entry["path"]
        if self._verify and entry["path"] not in self._verified:
            if not p.exists():
                raise FactsStoreError(f"{p}: in snapshot {self.snapshot_id}, not on disk")
            if _sha256_file(p) != entry["sha256"]:
                raise FactsStoreError(f"{p}: bytes do not match snapshot {self.snapshot_id}")
            if not rows_match_name(_read_rows(p), entry, kind):
                raise FactsStoreError(f"{p}: its rows do not hash to its name in snapshot "
                                      f"{self.snapshot_id}")
            self._verified.add(entry["path"])
        return Path(p)

    def _paths(self, entities: Iterable[str]) -> list[Path]:
        return [self._path(f) for e in entities for f in self._files.get(e, [])]

    def _filings_list(self, entities: Iterable[str]) -> str | None:
        paths = [self._path(self._filings[e], "filings") for e in entities if e in self._filings]
        return _file_list(paths) if paths else None

    def _stale(self, entities: Sequence[str], as_of: date | datetime, basis: Basis,
               stale_ok: bool) -> frozenset[str]:
        stale = [e for e in entities if self.is_stale(e, as_of, basis=basis)]
        if stale and not stale_ok:
            shown = ", ".join(f"{e} (fetched {self._fetched.get(e)})" for e in stale[:5])
            raise FactStaleError(
                f"snapshot {self.snapshot_id}: the cut ({as_of}, {basis}) is past the moment "
                f"{len(stale)} of {len(entities)} entities' copies were fetched — showing "
                f"{min(5, len(stale))} of {len(stale)}: {shown}. A copy knows nothing filed "
                "after it was fetched; refresh it, or pass stale_ok=True to be served the copy "
                "with each fact marked stale")
        return frozenset(stale)

    def _latest(self, entities: Sequence[str], as_of: date | datetime, *, basis: Basis,
                stale_ok: bool, taxonomy: str | None = None, concept: str | None = None,
                unit: str | None = None, period: Period | None = None
                ) -> dict[Key, Fact | Unresolved]:
        stale = self._stale(entities, as_of, basis, stale_ok)
        paths = self._paths(entities)
        if not paths:
            return {}
        filters: list[str] = [f"entity IN ({', '.join('?' for _ in entities)})"]
        params: list[Any] = [*_cut_params(as_of, basis), *entities]
        for col, val in (("taxonomy", taxonomy), ("concept", concept), ("unit", unit)):
            if val is not None:
                filters.append(f"{col} = ?")
                params.append(val)
        if period is not None:
            filters.append("period_end = ?")
            params.append(period.end)
            if period.start is None:
                filters.append("period_start IS NULL")
            else:
                filters.append("period_start = ?")
                params.append(period.start)
        # joined on either basis, so a fact read by day still states when it was accepted
        sql = _latest_sql(_file_list(paths), self._filings_list(entities), filters, basis)
        rows = self._con.execute(sql, params).fetchall()
        return _group_latest(rows, self.snapshot_id, day=cut_day(as_of), fetched=self._fetched,
                             stale=stale)

    def _held(self, entity: int | str) -> str:
        ent = pad_entity(entity)
        if ent not in self._files:
            raise FactNotHeldError(f"{ent}: not in snapshot {self.snapshot_id} — it was not "
                                   "ingested, which says nothing about what it filed")
        return ent

    def get(self, entity: int | str, concept: str, period: Period, as_of: date | datetime, *,
            unit: str | None = None, basis: Basis = ACCEPTED, stale_ok: bool = False) -> Fact:
        """The fact as filed latest by ``as_of``'s cut. ``concept`` is '<taxonomy>:<tag>'. With
        ``unit`` None the concept must carry exactly one unit for the period, else this raises."""
        taxonomy, tag = _split_concept(concept)
        ent = self._held(entity)
        found = self._latest([ent], as_of, basis=basis, stale_ok=stale_ok, taxonomy=taxonomy,
                             concept=tag, unit=unit, period=period)
        if not found:
            raise FactUnknownError(
                f"{ent} {concept} [{unit or 'any unit'}] {period.start}..{period.end}: nothing "
                f"filed by {as_of} ({basis}) in snapshot {self.snapshot_id}")
        if len(found) > 1:
            units = sorted(k[3] for k in found)
            raise FactAmbiguousError(f"{ent} {concept}: {len(found)} units {units}; name one")
        (hit,) = found.values()
        if isinstance(hit, (FactAmbiguousError, FactCutUndeterminedError)):
            raise hit
        return hit

    def frame(self, concept: str, period: Period, as_of: date | datetime, *,
              entities: Iterable[int | str] | None = None, unit: str | None = None,
              basis: Basis = ACCEPTED, stale_ok: bool = False) -> FrameResult:
        """``concept`` for ``period`` across ``entities`` (default: all in the snapshot)."""
        taxonomy, tag = _split_concept(concept)
        wanted = sorted({pad_entity(e) for e in entities} if entities is not None
                        else set(self._files))
        present = [e for e in wanted if e in self._files]
        found = self._latest(present, as_of, basis=basis, stale_ok=stale_ok, taxonomy=taxonomy,
                             concept=tag, unit=unit, period=period) if present else {}
        by_entity: dict[str, list[Fact | Unresolved]] = {}
        for key, hit in found.items():
            by_entity.setdefault(key[0], []).append(hit)
        facts: dict[str, Fact] = {}
        ambiguous: dict[str, str] = {}
        undetermined: dict[str, str] = {}
        for ent, hits in by_entity.items():
            if any(isinstance(h, FactCutUndeterminedError) for h in hits):
                undetermined[ent] = str(next(h for h in hits
                                             if isinstance(h, FactCutUndeterminedError)))
            elif len(hits) > 1:
                ambiguous[ent] = f"{len(hits)} units; name one"
            elif isinstance(hits[0], FactAmbiguousError):
                ambiguous[ent] = str(hits[0])
            elif isinstance(hits[0], Fact):
                facts[ent] = hits[0]
        not_held = tuple(e for e in wanted if e not in self._files)
        unknown = tuple(e for e in present
                        if e not in facts and e not in ambiguous and e not in undetermined)
        return FrameResult(facts=facts, unknown=unknown, ambiguous=ambiguous, not_held=not_held,
                           undetermined=undetermined)

    def latest(self, entity: int | str, as_of: date | datetime, *, basis: Basis = ACCEPTED,
               stale_ok: bool = False) -> dict[Key, Fact | Unresolved]:
        """Every key the entity had filed by ``as_of``'s cut, each with its latest filing (or the
        reason none can be chosen). The bulk form of :meth:`get`, on the same SQL."""
        ent = self._held(entity)
        return self._latest([ent], as_of, basis=basis, stale_ok=stale_ok)

    def companyfacts_as_of(self, entity: int | str, as_of: date | datetime, *,
                           basis: Basis = ACCEPTED, stale_ok: bool = False) -> dict[str, Any]:
        """The entity's facts in companyfacts' own shape, every row in ``as_of``'s cut kept: the
        fact layer's counterpart of ``facts_as_of(edgar.companyfacts(cik), as_of)`` (with
        ``basis="filed"``). A row the cut cannot place raises :class:`FactCutUndeterminedError`.

        Rows only: a tag's ``label`` and ``description`` are not stored in this slice."""
        ent = self._held(entity)
        self._stale([ent], as_of, basis, stale_ok)
        sql = _rows_sql(_file_list(self._paths([ent])),
                        _file_list([self._path(self._orders[ent], "order")]),
                        self._filings_list([ent]), basis)
        rows = self._con.execute(sql, _cut_params(as_of, basis)).fetchall()
        if rows and rows[0][-2] is None:
            unmapped = sum(1 for r in rows if r[-2] is None)
            raise FactsStoreError(f"{ent}: {unmapped} row(s) of snapshot {self.snapshot_id} are "
                                  "not in the entity's order object")
        unplaced = sorted({r[6] for r in rows if r[-1] is None})
        if unplaced:
            raise FactCutUndeterminedError(
                f"{ent}: {len(unplaced)} filing(s) dated {cut_day(as_of)} state no acceptance "
                f"time in snapshot {self.snapshot_id} (showing {min(3, len(unplaced))} of "
                f"{len(unplaced)}: {', '.join(unplaced[:3])}), so whether they were public at "
                "the cut cannot be said")
        tree: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
        for (taxonomy, concept, unit, start, end, value, accn, fy, fp, form, filed,
             frame, _position, _in_cut) in rows:
            row: dict[str, Any] = {}
            if start is not None:
                row["start"] = start.isoformat()
            v = float(value)
            row.update({"end": end.isoformat(), "val": int(v) if v.is_integer() else v,
                        "accn": accn, "fy": fy, "fp": fp, "form": form,
                        "filed": filed.isoformat()})
            if frame is not None:
                row["frame"] = frame
            tree.setdefault(taxonomy, {}).setdefault(concept, {}).setdefault(unit, []).append(row)
        nested = {ns: {tag: {"units": units} for tag, units in tags.items()}
                  for ns, tags in tree.items()}
        return {"cik": int(ent), "facts": nested}


def manifest_summary(manifest: dict[str, Any]) -> str:
    """One line naming a snapshot and its boundary."""
    t = manifest["totals"]
    # a count, never a bare "stated": a v3 snapshot can hold zero acceptance times
    acceptance = (f"acceptance times for "
                  f"{sum(int(e['filings']['rows']) for e in manifest['entities']):,} filings"
                  if int(manifest["schema_version"]) >= 3 else "no acceptance times")
    return (f"{manifest['snapshot_id']}: {t['entities']} entities, {t['files']} objects, "
            f"{t['rows']:,} rows, {t['bytes']:,} bytes (schema v{manifest['schema_version']}, "
            f"{acceptance})")
