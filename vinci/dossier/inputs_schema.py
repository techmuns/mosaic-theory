"""THE INPUT MANIFEST'S MODELS — the schema of a page's ``inputs`` block, and nothing else.

Kept apart from `vinci.dossier.inputs` (which builds the record and reads the price store) so the
page schema (`vinci.dossier.schemas`) imports models only: every module that reads a page imports
the schema, the monitor among them, and the monitor must reach no ledger writer
(`tests/test_outcome_import_fences.py`; `vinci.store` writes the ledger). Rules and design:
`vinci.dossier.inputs`, `docs/records/2026-11-05-every-page-records-what-it-was-built-from.md`.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, model_validator


class FiledThrough(BaseModel):
    """(2026-11-17, STATE row 64(a)) The latest filing date a CIQ Financials export's statement
    columns STATE (`ciq_sheets.financials_filed_through`): each period column of the Balance Sheet,
    Income Statement and Cash Flow sheets carries a 'Filing Date' row. CIQ stamps no Financials
    export date, and a CIQ export holds history as restated up to its export, so the export was
    made, and its facts are knowable, no earlier than this.

    THE SHAPE AND CONTRACT OF `schemas.Sourced[date]`, kept here because `schemas` imports this
    module, so it cannot import `Sourced` (pinned equal by
    `tests/test_analysis_as_of_financials_filed.py`). PRESENT carries the date and its
    ``source_ref`` (the workbook's sha256, the sheet, the row and the column); UNKNOWN carries no
    date and a ``note`` naming why — a row or cell that states none is never a guessed date."""

    value: date | None = None
    source_ref: str | None = None
    status: Literal["present", "unknown"]
    note: str | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _contract(self) -> FiledThrough:
        if self.status == "present":
            if self.value is None or not self.source_ref:
                raise ValueError("PRESENT filing date must carry both a value and a source_ref")
        elif self.value is not None or not self.note:
            raise ValueError("UNKNOWN filing date carries no value, and a note saying why")
        return self


class CiqExport(BaseModel):
    """One CIQ export the page's bundle held. ``file`` is the name only, never a local path."""

    kind: str
    freq: str | None = None
    file: str
    sha256: str
    bytes: int
    #: BACKFILL ONLY: the page sites whose own 10-hex stamp this file's sha256 begins with
    stamped_by: list[str] | None = None
    #: (2026-11-15) the export date this file STATES of itself (`inputs.export_dates`): today only
    #: the comps workbook's `As-Of Date:` header. A CIQ export holds history as restated up to its
    #: export, so its facts are KNOWABLE from this date and no earlier; `date_semantics` counts it.
    #: ABSENT on the page, never null, where the file states none or the record predates the field
    #: (`schemas.dossier_json`).
    export_date: date | None = None
    #: (2026-11-17, STATE row 64(a)) A FINANCIALS export only: the latest filing date its statement
    #: columns state (`inputs.filed_through`), with where it was read, or UNKNOWN naming why.
    #: `date_semantics` counts it where it is later than every other date. ABSENT on the page,
    #: never null, on any other export and on a record written before the field.
    filed_through: FiledThrough | None = None

    model_config = {"frozen": True}


class Response(BaseModel):
    """One HTTP response the build read, named as the fact layer's manifests name a response."""

    namespace: str
    source_url: str
    fetched_at: str | None          # ISO UTC (…Z) when the copy was fetched; None: unstated
    response_sha256: str
    bytes: int
    #: the committed fact-layer snapshots that sealed this exact response (`data/facts/manifests`)
    sealed_by: list[str] | None = None

    model_config = {"frozen": True}


class PriceSeries(BaseModel):
    """One price series read from the store, through its newest bar at build time."""

    internal_id: str
    ticker: str | None = None
    bars: int
    first_bar: date | None = None
    newest_bar: date | None = None
    #: `series_rows_sha256` of every bar through ``newest_bar``; None when the store held none
    rows_sha256: str | None = None

    model_config = {"frozen": True}


class ResponsesDigest(BaseModel):
    """Every response the build read, counted and hashed — on the page where the list is cut."""

    count: int
    by_namespace: dict[str, int]
    #: sha256 over the sorted ``namespace source_url response_sha256`` lines (`responses_digest`)
    sha256: str

    model_config = {"frozen": True}


class Unrecorded(BaseModel):
    """One input, or class of inputs, the record does not identify — and why."""

    input: str
    why: str

    model_config = {"frozen": True}


class InputManifest(BaseModel):
    """What one page was built from. See the module docstring for every rule."""

    schema_version: Literal[1] = 1
    #: ``build``: recorded by the build as it read; ``backfill``: resolved afterwards from the
    #: page's own stamps (`backfill`)
    recorded: Literal["build", "backfill"]
    #: the code vintage that wrote this record (on a backfill, NOT the page's assembly vintage)
    extraction_version: str
    #: the input classes this record identifies: all three on a build, ``ciq`` on a backfill
    covers: list[str]
    #: what a build reads that no record covers (`inputs.NOT_COVERED`): a complete record is
    #: complete within these bounds. Empty on a record written before the field (none committed)
    not_covered: list[str] = []
    #: ``inputs-<16 hex>`` over the recorded identities; None unless the record is complete
    inputs_id: str | None = None
    ciq: list[CiqExport] = []
    #: which recorded responses ``responses`` lists: ``all`` (the run record, a backfill), or only
    #: the fact layer's sources (`FACT_SOURCE`, the page — `for_page`)
    responses_listed: Literal["all", "fact_layer_sources"] = "all"
    responses: list[Response] = []
    #: every response read, listed or not; None when none was recorded (a backfill)
    responses_digest: ResponsesDigest | None = None
    prices: list[PriceSeries] = []
    unrecorded: list[Unrecorded] = []

    model_config = {"frozen": True}

    @property
    def complete(self) -> bool:
        return self.recorded == "build" and not self.unrecorded
