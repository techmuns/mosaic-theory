"""MECHANICAL-ONLY REFRESH — rewrite derived fields from STORED inputs, keeping the synthesis.

WHY THIS EXISTS, and it is not cost. Until now the only way to change a mechanical number was a
full re-assembly, which re-rolls synthesis — and 2026-07-30 proved a re-roll can produce WRONG prose
from identical inputs (SMPL's bear case cited $249M against a −391.9 row). So every remaining
mechanical fix carried a stochastic tax that scaled with fleet size.

THE ARGUMENT THAT DECIDED IT (operator): **FUBO and MVST cannot be re-assembled at all** — both
sit outside the screen cohort, so ``load_finalists`` raises. A path that re-runs assembly
leaves them permanently unfixable; a path from STORED INPUTS reaches them.

**IT WORKS FROM STORED INPUTS — verified, not assumed.** Every primitive the derived subtree
needs is already in ``dossier.json`` for all 11 names including FUBO and MVST:
``stock_info.price``, ``stock_info.shares_out``, ``stock_info.market_cap``, and the peer-grid name
row's ``net_debt``. On SMPL, ``cap 909.4 + net_debt 324.6 == 1234.0``, the stored TEV, exactly.
No ``DataRecord``, no CIQ bundle, no network, no LLM.

WHAT IT REFUSES, AND AT WHAT GRAIN. Preserving a synthesis across changed numbers is how you
MANUFACTURE the 19c defect — prose citing a figure the tables no longer show. But refusing per
DOSSIER would force a re-roll for any change anywhere, including changes no sentence
mentions. So the grain is the CLAIM (operator):

  * a material figure that did not move            -> preserve
  * a figure that moved and the prose never cited  -> preserve
  * a figure that moved and the prose DID cite     -> REFUSE, naming the claim

The citation test is 19c's own ``_figure_cited``, reused rather than reimplemented — two
matchers for one question is the twin-drift class, and this copy would drift silently because
it would only ever run here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.dossier.synthesis import MATERIAL_FIGURE_FLOOR_MUSD, _figure_cited


class RefreshRefusedError(RuntimeError):
    """A stored claim cites a figure this refresh would move. Re-assemble the name instead."""


def _annual(mech: dict[str, Any]) -> dict[str, Any]:
    fs = mech.get("financial_summary") or {}
    ann = fs.get("annual") or {}
    return (ann.get("value") or {}) if isinstance(ann, dict) else {}


def material_figures(mech: dict[str, Any]) -> dict[str, float]:
    """``{"<row label>|<column>": value}`` for every MATERIAL, non-estimate, above-floor figure.

    Keyed by row+column rather than by value: two rows may legitimately carry the same number, and a
    value-keyed map would collapse them and under-report a move."""
    ann = _annual(mech)
    cols = list(ann.get("columns") or [])
    est = list(ann.get("is_estimate") or [])
    out: dict[str, float] = {}
    for row in ann.get("rows") or []:
        if not row.get("material"):
            continue
        for i, v in enumerate(row.get("values") or []):
            if not isinstance(v, (int, float)) or abs(v) < MATERIAL_FIGURE_FLOOR_MUSD:
                continue
            if (est[i] if i < len(est) else str(cols[i] if i < len(cols) else "")
                    .rstrip(")").endswith("E")):
                continue
            out[f"{row.get('label')}|{cols[i] if i < len(cols) else i}"] = float(v)
    return out


def _prose(doc: dict[str, Any]) -> str:
    """Every free-text claim the stored synthesis makes, as one blob."""
    syn = doc.get("synthesis") or {}
    parts: list[str] = []
    for block in ("bull_points", "bear_points", "key_unknowns"):
        for p in syn.get(block) or []:
            parts.append(p if isinstance(p, str) else json.dumps(p))
    return "\n".join(parts)


def moved_cited_claims(before: dict[str, Any], after: dict[str, Any],
                       doc: dict[str, Any]) -> list[str]:
    """Material figures that MOVED and that the stored prose CITES — the refusal set.

    A figure that vanished counts as moved: prose citing a number the tables no longer carry is the
    same defect as prose citing a stale one."""
    old, new = material_figures(before), material_figures(after)
    prose = _prose(doc)
    hits: list[str] = []
    for key, val in old.items():
        if new.get(key) == val:
            continue
        if _figure_cited(prose, val):
            hits.append(f"{key} = {val:,.1f} → "
                        f"{('absent' if key not in new else format(new[key], ',.1f'))}")
    return hits


def recompute_derived(mech: dict[str, Any]) -> dict[str, Any]:
    """Rebuild the fields that are pure functions of stored primitives, in place on a copy.

    Today that is TEV and the price-implied levels: ``TEV = market_cap + net_debt`` and
    ``implied_level = TEV ÷ multiple``. Both already reproduce the stored values exactly, which is
    what makes the no-op round-trip pin meaningful — a refresh that changed nothing must produce a
    byte-identical file, or the path is not preserving.

    NOT a re-derivation of the primitives themselves. ``market_cap`` stays whatever the stored field
    says; changing its BASIS is B1's job, and this function is the mechanism B1 will use rather than
    a place to pre-empt it."""
    out: dict[str, Any] = json.loads(json.dumps(mech))
    si = out.get("stock_info") or {}
    cap = (si.get("market_cap") or {}).get("value")
    grid = ((out.get("peer_comps") or {}).get("peer_grid") or {}).get("value") or []
    name_row = next((r for r in grid if r.get("is_name")), None)
    nd = name_row.get("net_debt") if name_row else None
    ie = ((out.get("valuation") or {}).get("implied_expectations") or {})
    ie = ie.get("value") if isinstance(ie, dict) and "value" in ie else ie
    if not isinstance(ie, dict) or cap is None or nd is None:
        return out
    tev = float(cap) + float(nd)
    if isinstance(ie.get("tev"), dict):
        ie["tev"]["value"] = round(tev, 1)
    for row in ie.get("rows") or []:
        mult = row.get("multiple")
        if isinstance(mult, (int, float)) and mult > 0:
            row["implied_level"] = round(tev / float(mult), 1)
    return out


def refresh_dossier(path: Path, *, transform: Any = None) -> tuple[bool, list[str]]:
    """Refresh one committed dossier IN PLACE, preserving its synthesis. ``(changed, notes)``.

    ``transform`` is an optional ``mech -> mech`` applied to the stored mechanical layer BEFORE the
    derived rebuild — the seam B1 plugs into. Absent, this is a pure no-op round-trip, which is
    exactly what the round-trip pin drives.

    Raises :class:`RefreshRefusedError` when a moved figure is one the stored prose cites."""
    doc = json.loads(path.read_text())
    before = doc.get("mechanical") or {}
    staged = transform(json.loads(json.dumps(before))) if transform else before
    after = recompute_derived(staged)
    if doc.get("synthesis") is not None and (bad := moved_cited_claims(before, after, doc)):
        raise RefreshRefusedError(
            f"{doc.get('ticker')}: this refresh moves figures the stored synthesis CITES — "
            f"{'; '.join(bad)}. Preserving the prose would leave the page citing numbers its own "
            "tables no longer show (item 19c, manufactured deliberately). Re-assemble this name "
            "instead; the other names in the batch are unaffected.")
    doc["mechanical"] = after
    # SERIALIZE THROUGH THE MODEL, not json.dumps. The assembler writes
    # `dossier.model_dump_json(indent=2)`; `json.dumps` differs on unicode escaping and float
    # repr, so a no-op refresh rewrote all 11 committed files with zero semantic change. The
    # round-trip pin caught it on the first run, which is what that pin is for — two serializers
    # for one artifact is the twin-drift class, and here the second one would have churned every
    # file it touched. Validating on the way out is the bonus: a refresh that broke the schema
    # would now fail here rather than ship.
    from vinci.dossier.schemas import Dossier

    new_text = Dossier.model_validate(doc).model_dump_json(indent=2)
    changed = new_text != path.read_text()
    if changed:
        path.write_text(new_text)
    return changed, []
