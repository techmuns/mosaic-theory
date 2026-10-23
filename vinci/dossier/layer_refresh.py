"""LAYER REFRESHES — a page records each change made to it after its assembly, and the code vintage
that made it (`Dossier.layer_refreshes`).

THE RULING THIS BUILDS (2026-08-17,
`docs/records/2026-08-17-extraction-vintage-residue-closed-2026-08-17-fix.md`): re-stamping on
refresh is the WRONG fix — a new `extraction_version` would claim the whole page was re-extracted —
and the old stamp under-claims. The unlock it named is "the artifact must record that a refresh ran
and at which vintage". This module is that record's one writer-side vocabulary:

* :func:`moved_layers` — what changed between two versions of a page, at the page's own grain;
* :func:`entry` — one record, stamped with the extraction version CURRENT when the writer ran;
* :func:`append` — for the writer that round-trips the model (`refresh_dossier`);
* :func:`upsert_text` — for the writers that splice JSON text to stay byte-preserving
  (`anchor-backfill`, `own-history-refresh`, `financials-backfill`).

A full assembly writes a fresh page, so it carries no entries forward: its stamp covers everything.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vinci.dossier.extraction_version import EXTRACTION_VERSION
from vinci.dossier.schemas import (
    LAYER_REFRESH_WRITERS,
    Dossier,
    LayerRefresh,
    dossier_json,
    write_dossier,
)

FIELD = "layer_refreshes"

#: Top-level keys that are not layers: the record itself, and the assembly's own identity.
_NOT_LAYERS = frozenset({FIELD})

#: The key the text writers splice before — `anchor` is the LAST field a page serialises, and
#: `layer_refreshes` is declared immediately before it (`schemas.Dossier`).
_ANCHOR_FIELD = '\n  "anchor": {'
_FIELD_HEAD = f'\n  "{FIELD}": '


def moved_layers(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """The layers that differ between two versions of a page: top-level keys, except that the
    `mechanical` layer is named by section (`mechanical.valuation`), which is the grain a reader
    asks about. Sorted, so one refresh always records one way."""
    moved: list[str] = []
    for key in sorted((set(old) | set(new)) - _NOT_LAYERS):
        a, b = old.get(key), new.get(key)
        if a == b:
            continue
        if key == "mechanical" and isinstance(a, dict) and isinstance(b, dict):
            moved += [f"mechanical.{k}" for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
        else:
            moved.append(key)
    return moved


def entry(writer: str, layers: list[str], *, on: datetime | None = None) -> LayerRefresh:
    """One record, at the extraction version this code declares — the vintage that ran it."""
    if writer not in LAYER_REFRESH_WRITERS:
        raise ValueError(f"unknown layer-refresh writer {writer!r}; known: {LAYER_REFRESH_WRITERS}")
    if not layers:
        raise ValueError("a layer refresh names the layers it moved — none were given")
    return LayerRefresh(date=(on or datetime.now(UTC)).date().isoformat(),
                        extraction_version=EXTRACTION_VERSION, writer=writer,
                        layers=sorted(layers))


def append(model: Dossier, rec: LayerRefresh) -> Dossier:
    """The page with `rec` appended to its refresh record (the model-round-trip writer)."""
    return model.model_copy(update={FIELD: [*(model.layer_refreshes or []), rec]})


def upsert_text(text: str, rec: LayerRefresh) -> str:
    """Append `rec` to a committed dossier.json TEXT, byte-preserving everywhere else.

    The field sits IMMEDIATELY BEFORE `anchor` — where `dossier_json` serialises it — so a later
    model round-trip writes the same bytes. Absent, it is inserted there (or as the last field on a
    page with no anchor); present, only its own block is replaced. Formatted as `dossier_json`
    formats it: two-space indent, one level in."""
    doc = json.loads(text)
    records = [*(doc.get(FIELD) or []), rec.model_dump(mode="json")]
    body = json.dumps(records, indent=2, ensure_ascii=False)
    field = f'  "{FIELD}": ' + "\n".join(
        ln if i == 0 else "  " + ln for i, ln in enumerate(body.split("\n")))
    anchor_at = text.rfind(_ANCHOR_FIELD)
    start = text.find(_FIELD_HEAD)
    if start != -1:
        if anchor_at == -1 or anchor_at < start:
            raise ValueError(f"`{FIELD}` is not the field before `anchor` — refusing to splice a "
                             "page whose layout this writer cannot see")
        return f"{text[:start]}\n{field},{text[anchor_at:]}"
    if anchor_at != -1:
        return f"{text[:anchor_at]}\n{field},{text[anchor_at:]}"
    end = text.rstrip()
    if not end.endswith("}"):
        raise ValueError("dossier.json is not a JSON object — refusing to splice")
    head = end[:-1].rstrip()
    return f"{head},\n{field}\n}}{text[len(end):]}"


def write_recorded(path: Path, original: str, model: Dossier, writer: str, *,
                   decision_change: bool = False) -> str:
    """Write `model` through the one serializer (`schemas.write_dossier`), recording the layers that
    moved against `original` — the page as the writer read it. The derived blocks
    (`valuation_basis`, `date_semantics`) are named when they move with their inputs, so the record
    says everything the write changed. Nothing moved, nothing recorded: a no-op stays
    byte-identical.
    Returns the text written."""
    staged = dossier_json(model)
    if staged != original and (moved := moved_layers(json.loads(original), json.loads(staged))):
        model = append(model, entry(writer, moved))
    return write_dossier(path, model, decision_change=decision_change)
