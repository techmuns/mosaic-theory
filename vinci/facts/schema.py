"""The fact layer's row schema: one data contract, written in code and committed as JSON.

ONE ROW IS ONE FACT AS ONE FILING STATED IT. A period re-reported by a later filing is a second
row, never an update to the first: a restatement, a 10-K's comparative and an amendment are all
kept with their own accession and ``filed_date``. "As of a date" is therefore one predicate,
``filed_date <= :as_of``, and the latest such filing wins.

THE CONTRACT IS DATA, AND THE CODE MUST MATCH IT. :data:`COLUMNS` is the single definition; the
committed ``data/facts/schema.json`` is :func:`contract`'s output, and
``tests/test_facts_contract.py`` fails when they disagree. A column change is therefore a reviewed
diff to a file, plus a :data:`SCHEMA_VERSION` bump, never a silent change in what the writer emits.

THE SNAPSHOT ID IS NOT A COLUMN. A partition that did not change between two snapshots is the SAME
content-addressed object in both; a ``snapshot_id`` column would make every partition change on
every snapshot. The reader stamps each fact with the snapshot it read, from the manifest.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]

#: Bumped on any change to :data:`COLUMNS`. A manifest records the version its files were written
#: at, and the reader refuses a manifest whose version it does not know.
SCHEMA_VERSION = 1

#: Where the committed contract lives, relative to the repository root.
CONTRACT_RELPATH = Path("data") / "facts" / "schema.json"

_TYPES: dict[str, pa.DataType] = {
    "string": pa.string(),
    "date32": pa.date32(),
    "float64": pa.float64(),
    "int32": pa.int32(),
    "int64": pa.int64(),
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
    Column("source_position", "int64", False,
           "The row's position in the source response, so a replay reproduces the filer's order."),
)


def arrow_schema() -> pa.Schema:
    """The Arrow schema every partition is written with."""
    return pa.schema([pa.field(c.name, _TYPES[c.type], nullable=c.nullable) for c in COLUMNS])


def contract() -> dict[str, Any]:
    """The contract as committed: the version; each column's name, type, nullability, meaning."""
    return {
        "schema_version": SCHEMA_VERSION,
        "columns": [{"name": c.name, "type": c.type, "nullable": c.nullable, "doc": c.doc}
                    for c in COLUMNS],
    }


def contract_text() -> str:
    """The contract's exact committed bytes (sorted keys, two-space indent, trailing newline)."""
    return json.dumps(contract(), indent=2, sort_keys=True) + "\n"
