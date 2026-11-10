"""(RG-D19 PR 3) The $0 page pass: each committed page's transcript driver rows become their fact
and their locator, and their words go to the operator's private spool.

This is the one-off for the pages built before PR 1. A page assembled after it already has the
fact and the locator, and its words are spooled and stripped by `assemble._write`. For each
committed page, the pass does the following, with no model call, no network and no re-assembly:

1. **The fact.** A transcript row that has no fact yet gets the one code reads from its own
   committed quote (`driver_extract.check_fact`). It is the same function on the same inputs that
   the extractor runs, and the panel was measured on it (#952).
2. **The locator.**
   - It is read from the call ON DISK (`ciq_sheets.transcript_for_synthesis`, read only) when that
     call is there and holds the quote.
   - Otherwise it is call-only: the call's name and the quote's hash, with no paragraph and no file
     hash. It is never a guessed position.
3. **The spool.** The row's passage and its claim are written to the spool (`driver_evidence.
   spool_dossier`). THIS IS THE FIRST REAL WRITE to the operator's folder.
4. **The page** is written through `layer_refresh.write_recorded` as writer ``driver-facts-pass``.
   The one serializer leaves the row's quote, context and stated value off it
   (`schemas.PRIVATE_TRANSCRIPT_FIELDS`).

A page is REFUSED, unwritten, when a transcript row cites no call: there would be nowhere to file
its words. There are none on the committed corpus.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from vinci.dossier import driver_evidence, layer_refresh
from vinci.dossier.driver_extract import (
    _call_sections,
    check_fact,
    locate_quote,
    quote_key,
    transcript_sha256s,
)
from vinci.dossier.schemas import Dossier, OperatingDriver, TranscriptLocator

WRITER = "driver-facts-pass"
_CITED = "CIQ transcript: "


@dataclass
class PassOutcome:
    ticker: str
    status: str  # "written" | "unchanged" | "refused" | "would write" (dry run)
    detail: str
    rows: int = 0
    located: int = 0
    call_only: int = 0
    facts_added: int = 0
    spool: driver_evidence.SpoolReport = field(default_factory=driver_evidence.SpoolReport)


def _calls_on_disk(ticker: str, ciq_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """``({call: its section text}, {call: its file's sha256})`` for the name's calls on disk."""
    from vinci.dossier import ciq_sheets
    from vinci.dossier.ciq import CiqBundle

    folder = ciq_root / ticker
    files = sorted(p for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []
    bundle = CiqBundle.from_files(ticker, files)
    tx = ciq_sheets.transcript_for_synthesis(bundle)
    shas = transcript_sha256s(w.path for w in bundle.all_workbooks("transcript"))
    bodies = {lab: body for lab, body in _call_sections(tx or "") if lab is not None}
    return bodies, shas


def prepare(dossier: Dossier, ciq_root: Path) -> tuple[Dossier, PassOutcome]:
    """The page with each unstripped transcript row given its fact and its locator — nothing
    written. Refused (outcome ``refused``, the page returned unchanged) when a row cites no call."""
    out = PassOutcome(dossier.ticker, "unchanged", "")
    od = dossier.mechanical.operating_drivers
    todo = [r for r in (od.rows if od is not None else []) if r.tier == "llm-fenced" and r.verbatim]
    if od is None or not todo:
        out.detail = "no transcript row holds text"
        return dossier, out
    uncited = [r.metric for r in todo if not r.source_ref.startswith(_CITED)]
    if uncited:
        out.status = "refused"
        out.detail = (f"{len(uncited)} transcript row(s) cite no call ({uncited[0]!r}…): their "
                      "words would have nowhere to be filed")
        return dossier, out
    bodies, shas = _calls_on_disk(dossier.ticker, ciq_root)
    rows: list[OperatingDriver] = []
    for r in od.rows:
        if r.tier != "llm-fenced" or not r.verbatim:
            rows.append(r)
            continue
        out.rows += 1
        update: dict[str, object] = {}
        if r.value_status is None and r.value is not None:
            f = check_fact(r.metric, r.value, r.verbatim)
            update.update(figures=list(f.figures), value_status=f.status, unknown_reason=f.reason)
            out.facts_added += 1
        if r.locator is None:
            call = r.source_ref[len(_CITED):]
            loc = locate_quote(r.verbatim, call, bodies.get(call), shas) if call in bodies else None
            if loc is None:
                loc = TranscriptLocator(call=call, quote_sha256=quote_key(r.verbatim))
                out.call_only += 1
            else:
                out.located += 1
            update["locator"] = loc
        rows.append(r.model_copy(update=update) if update else r)
    mech = dossier.mechanical.model_copy(update={
        "operating_drivers": od.model_copy(update={"rows": rows})})
    return dossier.model_copy(update={"mechanical": mech}), out


def run(jp: Path, ciq_root: Path, *, spool: driver_evidence.EvidenceSpool | None,
        dry_run: bool) -> PassOutcome:
    """One committed page through the pass. ``spool`` is required unless ``dry_run``: a page's
    words are never dropped before they are filed."""
    raw = jp.read_text(encoding="utf-8")
    dossier = Dossier.model_validate(json.loads(raw))
    prepared, out = prepare(dossier, ciq_root)
    if out.status == "refused" or not out.rows:
        return out
    if dry_run:
        out.status = "would write"
        out.detail = (f"{out.rows} transcript row(s): {out.located} located, {out.call_only} "
                      f"call-only, {out.facts_added} given their fact (dry run: nothing written)")
        return out
    if spool is None:
        raise driver_evidence.SpoolNotConfiguredError(
            f"${driver_evidence.SPOOL_ENV} is not set: the pass files each row's words before it "
            "takes them off the page")
    prepared, out.spool = driver_evidence.spool_dossier(prepared, spool)
    if out.spool.no_evidence:   # `prepare` gave every row a locator; this would be a bug
        raise driver_evidence.EvidenceError(
            f"{dossier.ticker}: {out.spool.no_evidence} row(s) were not filed — page not written")
    layer_refresh.write_recorded(jp, raw, prepared, WRITER)
    out.status = "written"
    out.detail = (f"{out.rows} transcript row(s): {out.located} located, {out.call_only} "
                  f"call-only, {out.facts_added} given their fact; spool {out.spool.written} "
                  f"written, {out.spool.already} already held")
    return out
