"""The fact layer's row schema: one data contract, written in code and committed as JSON.

ONE ROW IS ONE FACT AS ONE FILING STATED IT. A period re-reported by a later filing is a second
row, never an update to the first: a restatement, a 10-K's comparative and an amendment are all
kept with their own accession and ``filed_date``. "As of a date" is therefore one predicate,
``filed_date <= :as_of``, and the latest such filing wins.

THE CONTRACT IS DATA, AND THE CODE MUST MATCH IT. :data:`COLUMNS` is the single definition; the
committed ``data/facts/schema.json`` is :func:`contract`'s output, and
``tests/test_facts_contract.py`` fails when they disagree. A column change is therefore a reviewed
diff to a file, plus a :data:`SCHEMA_VERSION` bump, never a silent change in what the writer emits.

THE SNAPSHOT ID IS NOT A COLUMN, AND NEITHER IS THE ROW'S PLACE IN THE RESPONSE (schema v2,
slice 2a). An object is named by a hash of its rows' content (:func:`vinci.facts.store.content_id`),
so a partition no later filing touched is the SAME object in every snapshot. Version 1 stored
``source_position``, the row's index in the whole response; one new filing shifted every later
row's index and so rewrote every partition (0 of 17 earlier-year partitions shared on NFLX's
previous cache copy, review round 2 of #896). The response's order is kept in its own per-entity
object (:data:`ORDER_COLUMNS`), which a replay needs and a point-in-time query does not.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]

#: Bumped on any change to the contract. A manifest records the version its files were written at,
#: and the reader refuses a manifest whose version it does not know. 3 (TeamNostra fix request 2,
#: RFL-D2): a per-entity FILINGS object (:data:`FILING_COLUMNS`), each filing's SEC acceptance time,
#: beside the data and order objects. Version 3's data and order columns ARE version 2's, so a
#: version-2 manifest is still read, and verified against version 2's contract
#: (:func:`contract_text`); it states no acceptance time.
SCHEMA_VERSION = 3
READABLE_SCHEMA_VERSIONS: tuple[int, ...] = (2, 3)

#: Where the committed contract lives, relative to the repository root.
CONTRACT_RELPATH = Path("data") / "facts" / "schema.json"

_TYPES: dict[str, pa.DataType] = {
    "string": pa.string(),
    "date32": pa.date32(),
    "float64": pa.float64(),
    "int32": pa.int32(),
    "int64": pa.int64(),
    # naive, and always UTC: DuckDB moves a zone-aware value only through pytz, not a dependency
    "timestamp_utc": pa.timestamp("us"),
}


@dataclass(frozen=True)
class Column:
    name: str
    type: str          # a key of _TYPES
    nullable: bool
    doc: str


COLUMNS: tuple[Column, ...] = (
    Column("source", "string", False,
           "The writer that produced the row ('edgar'). One writer per source."),
    Column("entity", "string", False, "SEC CIK, zero-padded to 10 digits."),
    Column("taxonomy", "string", False,
           "XBRL namespace as the filer reported it ('us-gaap', 'dei')."),
    Column("concept", "string", False, "XBRL tag, verbatim."),
    Column("unit", "string", False, "Unit as reported ('USD', 'shares', 'USD/shares')."),
    Column("period_start", "date32", True, "Start of a duration; null for an instant."),
    Column("period_end", "date32", False, "End of a duration, or the instant."),
    Column("value", "float64", False,
           "The value as filed. Never imputed: an absent fact has no row."),
    Column("filed_date", "date32", False,
           "The day the filing carrying this value was filed: the knowable date the cut reads."),
    Column("accession", "string", False, "The filing's accession number: the source_ref."),
    Column("form", "string", True, "The filing's form type ('10-K', '10-Q/A')."),
    Column("fiscal_year", "int32", True, "The filing's fiscal year (companyfacts 'fy')."),
    Column("fiscal_period", "string", True, "The filing's fiscal period (companyfacts 'fp')."),
    Column("frame", "string", True, "SEC's calendar frame, when SEC assigned one."),
    Column("dimensions", "string", True,
           "Dimensional qualifiers as JSON; null when undimensioned (all of companyfacts)."),
    Column("extractor", "string", False, "The module that wrote the row."),
    Column("extractor_version", "string", False, "That module's version when it wrote the row."),
    Column("status", "string", False, "'present' for a stated fact."),
    Column("reason", "string", True, "Why a non-present status was recorded; null when present."),
)

#: One entity's response order: row ``row`` of data object ``object`` was the response's row
#: ``source_position``. One order object per entity per response, named by its content's hash.
ORDER_COLUMNS: tuple[Column, ...] = (
    Column("source_position", "int64", False,
           "The row's position in the source response, so a replay reproduces the filer's order."),
    Column("object", "string", False, "The content id of the data object holding the row."),
    Column("row", "int32", False, "The row's index in that object, in its stored order."),
)


#: One entity's filings as SEC's submissions documents list them (schema v3, RFL-D2): one row per
#: accession the entity's data rows carry and the documents date. A data row is knowable from its
#: filing's ``accepted_at``, not from the start of its ``filed_date``: companyfacts dates a filing
#: to the day, and a 10-Q accepted at 16:25 on its filing day was served to a replay priced at that
#: day's 16:00 close.
FILING_COLUMNS: tuple[Column, ...] = (
    Column("entity", "string", False, "SEC CIK, zero-padded to 10 digits."),
    Column("accession", "string", False,
           "The filing's accession number, as its data rows carry it."),
    Column("form", "string", True, "The form SEC's submissions document lists for the filing."),
    Column("filing_date", "date32", False,
           "SEC's filing date, which the filing's data rows carry as filed_date."),
    Column("accepted_at", "timestamp_utc", False,
           "When SEC accepted the filing (acceptanceDateTime), in UTC with no zone stored: "
           "the moment the cut reads."),
)


def _schema(columns: tuple[Column, ...]) -> pa.Schema:
    return pa.schema([pa.field(c.name, _TYPES[c.type], nullable=c.nullable) for c in columns])


def arrow_schema() -> pa.Schema:
    """The Arrow schema every data partition is written with."""
    return _schema(COLUMNS)


def order_arrow_schema() -> pa.Schema:
    """The Arrow schema every order object is written with."""
    return _schema(ORDER_COLUMNS)


def filing_arrow_schema() -> pa.Schema:
    """The Arrow schema every filings object is written with (schema v3)."""
    return _schema(FILING_COLUMNS)


def _doc(columns: tuple[Column, ...]) -> list[dict[str, Any]]:
    return [{"name": c.name, "type": c.type, "nullable": c.nullable, "doc": c.doc}
            for c in columns]


def contract(version: int = SCHEMA_VERSION) -> dict[str, Any]:
    """The contract as committed: the version; each column's name, type, nullability, meaning.
    ``version`` 2 is the contract version-2 manifests hashed, without the filings object."""
    if version not in READABLE_SCHEMA_VERSIONS:
        raise ValueError(f"schema version {version!r} is not one of {READABLE_SCHEMA_VERSIONS}")
    out: dict[str, Any] = {"schema_version": version, "columns": _doc(COLUMNS),
                           "order_columns": _doc(ORDER_COLUMNS)}
    if version >= 3:
        out["filing_columns"] = _doc(FILING_COLUMNS)
    return out


def contract_text(version: int = SCHEMA_VERSION) -> str:
    """The contract's exact committed bytes (sorted keys, two-space indent, trailing newline)."""
    return json.dumps(contract(version), indent=2, sort_keys=True) + "\n"
