"""Read facts as of a date: DuckDB over a snapshot's Parquet. Embedded, in memory, read-only.

POINT-IN-TIME IS ONE PREDICATE. Every query in this module is built by :func:`_latest_sql` or
:func:`_rows_sql`, and both cut with ``filed_date <= ?`` bound to the caller's ``as_of``. A fact
filed after ``as_of`` cannot be returned, and among the filings made by then the LATEST wins, which
is how a restatement replaces its original from its own filing date onward and not before.

MISSING IS LOUD. :meth:`FactStore.get` raises :class:`FactUnknownError` when nothing was filed by
``as_of`` (no entity in the snapshot, no such concept, no such period, or only later filings). It
raises :class:`FactAmbiguousError` when the latest day's filings state DIFFERENT values for the
same period, as a 10-K/A and a 10-Q/A filed the same day can (measured on the committed pages'
companies, 2026-11-04: 14 such keys). Nothing is imputed, and no tie is broken by guesswork.

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
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

import duckdb

from vinci.edgar.concepts import ANNUAL_REPORT_FORMS
from vinci.facts.store import (
    DEFAULT_NAME,
    FactsStoreError,
    _sha256_file,
    is_r2,
    load_manifest,
    requested_location,
    store_root,
)

if TYPE_CHECKING:
    from vinci.facts.remote import R2Objects

#: The periodic reports (and, by prefix, their amendments: 10-K/A, 10-Q/A, 10-KT, 20-F/A). On a
#: same-day, same-value tie one of these is named over a proxy or any other form: NKE's FY2024 net
#: income is stated identically by its 10-K and its DEF 14A, both filed 2026-07-15, and the page's
#: readers filter on these same forms (`vinci.edgar.concepts`, `ANNUAL_REPORT_FORMS`, 10-Q/10-K).
PERIODIC_FORMS: tuple[str, ...] = (*ANNUAL_REPORT_FORMS, "10-Q")


def is_periodic(form: str | None) -> bool:
    return str(form or "").upper().startswith(PERIODIC_FORMS)


class FactUnknownError(LookupError):
    """No fact was filed by the as-of date: UNKNOWN, never a guess."""


class FactAmbiguousError(LookupError):
    """The latest filing day states different values for one period; the store will not choose."""


class FactsStoreNotPresentError(FactsStoreError):
    """A locally stored snapshot was opened where its objects are not."""


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

    @property
    def source_ref(self) -> SourceRef:
        return SourceRef(self.accession, self.taxonomy, self.concept)


@dataclass(frozen=True)
class FrameResult:
    """One concept and period across entities. EVERY requested entity lands in exactly one field."""

    facts: dict[str, Fact]
    unknown: tuple[str, ...]                      # nothing filed by as_of
    ambiguous: dict[str, str] = field(default_factory=dict)   # entity -> why


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


def _latest_sql(files: str, filters: Sequence[str]) -> str:
    """The latest filing by ``as_of`` (the first bound parameter) for every key that passes
    ``filters``: every row filed on that key's latest day, so a same-day disagreement is visible."""
    where = " AND ".join(["filed_date <= ?", *filters])
    return f"""
        WITH cut AS (SELECT * FROM read_parquet({files}) WHERE {where}),
        ranked AS (
            SELECT *, max(filed_date) OVER (
                PARTITION BY entity, taxonomy, concept, unit, period_start, period_end) AS latest
            FROM cut)
        SELECT {", ".join(_FACT_COLS)} FROM ranked WHERE filed_date = latest
        ORDER BY entity, taxonomy, concept, unit, period_start NULLS FIRST, period_end, accession
    """


#: A data object's content id, read back from the path DuckDB reports for each row.
_OBJECT_OF_PATH = r"([0-9a-f]{64})\.parquet$"


def _rows_sql(files: str, order: str) -> str:
    """Every row filed by ``as_of`` (the one bound parameter), in the source response's order: each
    row joined to its place in ``order`` on (its object's content id, its row in that object). A row
    the order object does not map comes back with a null position, and the caller raises."""
    return f"""
        WITH cut AS (
            SELECT taxonomy, concept, unit, period_start, period_end, value, accession,
                   fiscal_year, fiscal_period, form, filed_date, frame,
                   regexp_extract(filename, '{_OBJECT_OF_PATH}', 1) AS object,
                   file_row_number AS row
            FROM read_parquet({files}, filename=true, file_row_number=true)
            WHERE filed_date <= ?)
        SELECT cut.taxonomy, cut.concept, cut.unit, cut.period_start, cut.period_end, cut.value,
               cut.accession, cut.fiscal_year, cut.fiscal_period, cut.form, cut.filed_date,
               cut.frame, o.source_position
        FROM cut LEFT JOIN read_parquet({order}) AS o ON cut.object = o.object AND cut.row = o.row
        ORDER BY o.source_position NULLS FIRST
    """


Key = tuple[str, str, str, str, date | None, date]   # entity, taxonomy, concept, unit, start, end


def _group_latest(rows: Iterable[tuple[Any, ...]], snapshot_id: str
                  ) -> dict[Key, Fact | FactAmbiguousError]:
    grouped: dict[Key, list[tuple[Any, ...]]] = {}
    for r in rows:
        grouped.setdefault((r[0], r[1], r[2], r[3], r[4], r[5]), []).append(r)
    out: dict[Key, Fact | FactAmbiguousError] = {}
    for key, rs in grouped.items():
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
            concurrent_accessions=tuple(sorted(r[8] for r in rs if r[8] != top[8])))
    return out


class FactStore:
    """One snapshot, opened for reading.

    ``verify`` (default True) hashes every object an entity's query touches the first time it is
    touched, and raises :class:`FactsStoreError` if one is missing or does not match its manifest
    entry: a reader never serves a fact from bytes the manifest did not seal.

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
        self.storage: str = self.manifest["storage"]
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
        self._orders: dict[str, dict[str, Any]] = {
            e["entity"]: e["order"] for e in self.manifest["entities"]}
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

    def _path(self, entry: dict[str, Any]) -> Path:
        """An object's path, its bytes checked against the manifest the first time it is read."""
        if self._remote is not None:
            if entry["path"] not in self._verified:
                self._remote.fetch(entry)        # raises on a missing key or unsealed bytes
                self._verified.add(entry["path"])
            return Path(self.root / entry["path"])
        p = self.root / entry["path"]
        if self._verify and entry["path"] not in self._verified:
            if not p.exists():
                raise FactsStoreError(f"{p}: in snapshot {self.snapshot_id}, not on disk")
            if _sha256_file(p) != entry["sha256"]:
                raise FactsStoreError(f"{p}: bytes do not match snapshot {self.snapshot_id}")
            self._verified.add(entry["path"])
        return Path(p)

    def _paths(self, entities: Iterable[str]) -> list[Path]:
        return [self._path(f) for e in entities for f in self._files.get(e, [])]

    def _latest(self, entities: Sequence[str], as_of: date, *, taxonomy: str | None = None,
                concept: str | None = None, unit: str | None = None,
                period: Period | None = None) -> dict[Key, Fact | FactAmbiguousError]:
        paths = self._paths(entities)
        if not paths:
            return {}
        filters: list[str] = [f"entity IN ({', '.join('?' for _ in entities)})"]
        params: list[Any] = [as_of, *entities]
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
        rows = self._con.execute(_latest_sql(_file_list(paths), filters), params).fetchall()
        return _group_latest(rows, self.snapshot_id)

    def get(self, entity: int | str, concept: str, period: Period, as_of: date, *,
            unit: str | None = None) -> Fact:
        """The fact as filed latest by ``as_of``. ``concept`` is '<taxonomy>:<tag>'. With ``unit``
        None the concept must carry exactly one unit for the period, else this raises."""
        ent = pad_entity(entity)
        taxonomy, tag = _split_concept(concept)
        if ent not in self._files:
            raise FactUnknownError(f"{ent}: not in snapshot {self.snapshot_id}")
        found = self._latest([ent], as_of, taxonomy=taxonomy, concept=tag, unit=unit,
                             period=period)
        if not found:
            raise FactUnknownError(
                f"{ent} {concept} [{unit or 'any unit'}] {period.start}..{period.end}: nothing "
                f"filed by {as_of} in snapshot {self.snapshot_id}")
        if len(found) > 1:
            units = sorted(k[3] for k in found)
            raise FactAmbiguousError(f"{ent} {concept}: {len(found)} units {units}; name one")
        (hit,) = found.values()
        if isinstance(hit, FactAmbiguousError):
            raise hit
        return hit

    def frame(self, concept: str, period: Period, as_of: date, *,
              entities: Iterable[int | str] | None = None, unit: str | None = None
              ) -> FrameResult:
        """``concept`` for ``period`` across ``entities`` (default: all in the snapshot)."""
        taxonomy, tag = _split_concept(concept)
        wanted = sorted({pad_entity(e) for e in entities} if entities is not None
                        else set(self._files))
        present = [e for e in wanted if e in self._files]
        found = self._latest(present, as_of, taxonomy=taxonomy, concept=tag, unit=unit,
                             period=period) if present else {}
        by_entity: dict[str, list[Fact | FactAmbiguousError]] = {}
        for key, hit in found.items():
            by_entity.setdefault(key[0], []).append(hit)
        facts: dict[str, Fact] = {}
        ambiguous: dict[str, str] = {}
        for ent, hits in by_entity.items():
            if len(hits) > 1:
                ambiguous[ent] = f"{len(hits)} units; name one"
            elif isinstance(hits[0], FactAmbiguousError):
                ambiguous[ent] = str(hits[0])
            else:
                facts[ent] = hits[0]
        unknown = tuple(e for e in wanted if e not in facts and e not in ambiguous)
        return FrameResult(facts=facts, unknown=unknown, ambiguous=ambiguous)

    def latest(self, entity: int | str, as_of: date) -> dict[Key, Fact | FactAmbiguousError]:
        """Every key the entity had filed by ``as_of``, each with its latest filing (or the
        disagreement that stops one being chosen). The bulk form of :meth:`get`, on the same SQL."""
        ent = pad_entity(entity)
        return self._latest([ent], as_of) if ent in self._files else {}

    def companyfacts_as_of(self, entity: int | str, as_of: date) -> dict[str, Any]:
        """The entity's facts in companyfacts' own shape, every row filed by ``as_of`` kept: the
        fact layer's counterpart of ``facts_as_of(edgar.companyfacts(cik), as_of)``.

        Rows only: a tag's ``label`` and ``description`` are not stored in this slice."""
        ent = pad_entity(entity)
        if ent not in self._files:
            raise FactUnknownError(f"{ent}: not in snapshot {self.snapshot_id}")
        sql = _rows_sql(_file_list(self._paths([ent])), _file_list([self._path(self._orders[ent])]))
        rows = self._con.execute(sql, [as_of]).fetchall()
        if rows and rows[0][-1] is None:
            unmapped = sum(1 for r in rows if r[-1] is None)
            raise FactsStoreError(f"{ent}: {unmapped} row(s) of snapshot {self.snapshot_id} are "
                                  "not in the entity's order object")
        tree: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
        for (taxonomy, concept, unit, start, end, value, accn, fy, fp, form, filed,
             frame, _position) in rows:
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
    return (f"{manifest['snapshot_id']}: {t['entities']} entities, {t['files']} objects, "
            f"{t['rows']:,} rows, {t['bytes']:,} bytes (schema v{manifest['schema_version']})")


