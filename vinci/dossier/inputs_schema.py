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

from pydantic import BaseModel


class CiqExport(BaseModel):
    """One CIQ export the page's bundle held. ``file`` is the name only, never a local path."""

    kind: str
    freq: str | None = None
    file: str
    sha256: str
    bytes: int
    #: BACKFILL ONLY: the page sites whose own 10-hex stamp this file's sha256 begins with
    stamped_by: list[str] | None = None

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
    covers: list[str]
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
