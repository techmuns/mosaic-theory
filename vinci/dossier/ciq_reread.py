"""$0 RE-READS OF ONE CIQ FIELD ON A COMMITTED PAGE (2026-11-09, audits RBC-D1 and RA-D1).

A fix to a CIQ reader reaches a committed page only when the page is re-assembled, which re-rolls
its synthesis and costs LLM calls. Two fixes change one field each, read from one export, with no
prose depending on them, so this writer re-reads that field from the export on disk — no
assembly, no LLM, no network — and REFUSES whenever it cannot show the export is the one the page
was built from. Each field carries its own proof of that, because the pages record their inputs
unevenly:

* ``customers_listed`` (RBC-D1). The structured count of the roster the page already stores. The
  Customers export is not stamped in `inputs` (no build before 2026-11-05 recorded it), so the proof
  is the roster itself: the one re-read from disk must equal the stored field byte for byte —
  value, note, status and source_ref. Only then is the count written, beside the roster it counts.
  The roster is never rewritten here.
* ``surprise_history`` (RA-D1). The value CHANGES — that is the fix — so it cannot prove its own
  vintage. The proof is the Estimates export's sha256, which the page's `inputs` stamps: the file on
  disk must hash to it. And no synthesis claim may cite the field (its source_ref): prose written
  against the old read would then be left describing a figure the page no longer shows.

Each write goes through the one serializer and records itself (`layer_refresh`, writer
``ciq-reread``); the page is then re-rendered from the stored record (`refresh._rerender_only`).
"""
from __future__ import annotations

import contextlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vinci import provenance
from vinci.dossier import ciq_sheets
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import Dossier

WRITER = "ciq-reread"
FIELDS = ("customers_listed", "surprise_history")
#: The surprise field's source_ref, as every reading of it starts — what a synthesis claim citing
#: it would carry.
_SURPRISE_REF = "CIQ Estimates→Surprise"


@dataclass(frozen=True)
class Outcome:
    """One page's result: ``written`` / ``would write`` / ``unchanged`` / ``refused`` /
    ``skipped``, and why."""

    ticker: str
    status: str
    detail: str


def _bundle(ticker: str, ciq_root: Path) -> CiqBundle | None:
    files = LocalFolderStore(ciq_root).files(ticker)
    if not files:
        return None
    # the BIFF reader prints a sector-size warning per file on stdout; it is not this writer's
    with contextlib.redirect_stdout(io.StringIO()):
        return CiqBundle.from_files(ticker, files)


def _dump(model: Any) -> Any:
    return json.loads(model.model_dump_json())


def _customers(doc: dict[str, Any], bundle: CiqBundle) -> tuple[str, str, int | None]:
    conc = doc["mechanical"]["concentration"]
    stored = conc.get("customers") or {}
    if stored.get("status") != "present":
        return ("skipped", "the page's customer roster is not PRESENT — there is no count to state",
                None)
    with contextlib.redirect_stdout(io.StringIO()):
        fresh, listed = ciq_sheets.customer_roster(bundle)
    if _dump(fresh) != stored:
        return "refused", (
            "the Customers export on disk is not the one this page was built from: the roster "
            "re-read from it differs from the stored one — re-assemble the name instead"), None
    if listed is None:
        # A PRESENT roster withholds its count when its RTF view may be cut short (audit RBC-D3):
        # a cut list's length is not the company's count, so there is none to write. Refused, not
        # raised, so one cut export does not stop a sweep of every page; the note says why.
        return ("refused", "the roster re-read from disk carries no count — "
                f"{fresh.note or 'no reason given'}", None)
    if conc.get("customers_listed") == listed:
        return "unchanged", f"already carries customers_listed={listed}", None
    return "write", f"customers_listed={listed} (the stored roster re-read byte for byte)", listed


def _surprise(doc: dict[str, Any], bundle: CiqBundle) -> tuple[str, str, Any]:
    stamped = [c for c in (doc.get("inputs") or {}).get("ciq") or []
               if c.get("kind") == "estimates"]
    wb = bundle.workbook("estimates")
    if wb is None:
        return "skipped", "no Estimates export on disk", None
    if not stamped:
        return "refused", "the page stamps no Estimates export, so the one on disk cannot be " \
                          "shown to be the one it was built from", None
    sha, _size = provenance.file_sha256(wb.path)
    if sha != stamped[0].get("sha256"):
        return "refused", (f"the Estimates export on disk ({wb.path.name}, sha256 {sha[:12]}) is "
                           f"not the one the page stamps ({str(stamped[0].get('sha256'))[:12]}) — "
                           "re-assemble the name instead"), None
    if _SURPRISE_REF in json.dumps(doc.get("synthesis"), ensure_ascii=False):
        return "refused", ("a synthesis claim cites the surprise history; a re-read would leave "
                           "it describing a figure the page no longer shows — re-assemble"), None
    with contextlib.redirect_stdout(io.StringIO()):
        fresh = _dump(ciq_sheets.surprise_history(bundle))
    stored = doc["mechanical"]["consensus_context"]["surprise_history"]
    if fresh == stored:
        return "unchanged", "the re-read equals the stored field", None
    return "write", f"surprise_history re-read from {wb.path.name} (sha256 {sha[:12]}, as " \
                    f"stamped)", fresh


def reread(path: Path, field: str, ciq_root: Path, *, dry_run: bool = False) -> Outcome:
    """Re-read ``field`` on the committed page at ``path`` from the export under ``ciq_root``."""
    from vinci.dossier import layer_refresh
    from vinci.dossier.refresh import _rerender_only

    if field not in FIELDS:
        raise ValueError(f"{field!r} is not a field this writer re-reads ({list(FIELDS)})")
    raw = path.read_text()
    doc = json.loads(raw)
    t = str(doc["ticker"])
    bundle = _bundle(t, ciq_root)
    if bundle is None:
        return Outcome(t, "skipped", f"no CIQ export on disk under {ciq_root / t}")
    if field == "customers_listed":
        verdict, detail, listed = _customers(doc, bundle)
        if verdict == "write":
            doc["mechanical"]["concentration"]["customers_listed"] = listed
    else:
        verdict, detail, fresh = _surprise(doc, bundle)
        if verdict == "write":
            doc["mechanical"]["consensus_context"]["surprise_history"] = fresh
    if verdict != "write":
        return Outcome(t, verdict, detail)
    if dry_run:
        return Outcome(t, "would write", detail)
    layer_refresh.write_recorded(path, raw, Dossier.model_validate(doc), WRITER)
    rendered = _rerender_only(path)
    return Outcome(t, "written", detail + ("; dossier.md re-rendered" if rendered else
                                           "; dossier.md unchanged"))
