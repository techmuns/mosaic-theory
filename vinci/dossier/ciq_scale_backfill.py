"""THE BACK-FILL of `anchor.ciq_scale_check` onto committed pages (2026-10-27).

ITS OWN MODULE, NOT `ciq_balance`'s: writing a page needs the assembler's scenario-card reader and
the renderer, and `ciq_balance` sits on the import path of `anchor` → `schemas` → `scenarios` and
the monitor. A page writer there gave the monitor a static path to the store's ledger writers
(`tests/test_outcome_import_fences.py`) — nothing on that path imports this module.
"""
from __future__ import annotations

import json
from pathlib import Path

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.ciq_balance import scale_outcome


def scale_check_backfill(path: Path, *, bundle: CiqBundle, refused: list[str]) -> bool:
    """Write `anchor.ciq_scale_check` onto ONE committed page, under a KEPT synthesis and every
    other anchor value as committed. True when the page moved.

    THE OUTCOME IS NOT ON THE PAGE, so the Financials exports are read — and only behind proof that
    each is the one the page was built from (`refresh.ciq_currency_transform`'s two proofs): the
    quarterly by the sha256 the page stamps (`ev_bridge.source_sha256`), the annual by its revenue
    and operating cash flow reproducing the page's annual table. A page that does not prove, has
    no anchor, or already holds a different outcome is named in ``refused`` — absent reads as not
    run, never as a pass."""
    from vinci.dossier import layer_refresh
    from vinci.dossier import statement_recon as sr
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier, dossier_json, write_dossier

    original = path.read_text()
    doc = json.loads(original)
    t = str(doc.get("ticker"))
    a, mech = doc.get("anchor"), doc.get("mechanical") or {}
    if (path.parent / "known_wrong.json").exists():
        refused.append(f"{t}: SEALED by its own known_wrong.json")
        return False
    if not isinstance(a, dict):
        refused.append(f"{t}: no anchor block")
        return False
    stamp = (doc.get("ev_bridge") or {}).get("source_sha256")
    q = bundle.workbook("financials", freq="quarterly")
    if stamp is None or q is None or cs.file_provenance(q.path)[0] != stamp:
        refused.append(f"{t}: the quarterly Financials is not the export the page stamps")
        return False
    if bundle.workbook("financials", freq="annual") is not None:
        table = ((mech.get("financial_summary") or {}).get("annual") or {}).get("value")
        got = {(f.line, f.column): f.value for f in sr.ciq_figures(bundle)}
        if not isinstance(table, dict) or got != sr.table_figures(table):
            refused.append(f"{t}: the annual Financials does not reproduce the page's annual "
                           "table")
            return False
    new = scale_outcome(bundle, t)
    held = a.get("ciq_scale_check")
    if held is not None:
        if held != new:
            refused.append(f"{t}: ciq_scale_check on the page differs from the rebuild — kept")
        return False
    a["ciq_scale_check"] = new
    model = Dossier.model_validate(doc)
    if moved := layer_refresh.moved_layers(json.loads(original), json.loads(dossier_json(model))):
        model = layer_refresh.append(model, layer_refresh.entry("refresh", moved))
    write_dossier(path, model)       # the one writer: the operator's decision is guarded there
    path.with_name("dossier.md").write_text(render_markdown(
        model, card=_read_scenario_card(model.ticker), dossiers_root=path.parent.parent))
    return True
