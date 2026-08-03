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
from collections.abc import Callable
from pathlib import Path
from typing import Any

from vinci.dossier.synthesis import (
    MATERIAL_FIGURE_FLOOR_MUSD,
    SYNTHESIS_CLAIM_LISTS,
    SYNTHESIS_CLAIM_SCALARS,
    _figure_cited,
)

#: ``mech -> mech``, applied before the derived rebuild. The seam B1 plugs into.
Transform = Callable[[dict[str, Any]], dict[str, Any]]


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
    """Every free-text claim the stored synthesis makes, as one blob.

    Reads the STORED dict rather than a ``Synthesis`` model, so it cannot call
    ``synthesis._synthesis_prose`` directly — but it takes that function's BLOCK LIST from it by
    import, so the two cannot disagree about which fields carry claims. REVIEW FINDING: the first
    cut retyped the tuple here, which is the twin-drift class this file's own docstring warns about
    two paragraphs up. Adding a fourth claim block to the synthesis would have silently left this
    path checking three."""
    syn = doc.get("synthesis") or {}
    parts: list[str] = []
    for block in SYNTHESIS_CLAIM_LISTS:
        for p in syn.get(block) or []:
            parts.append(p if isinstance(p, str) else json.dumps(p))
    for attr in SYNTHESIS_CLAIM_SCALARS:
        v = syn.get(attr)
        if isinstance(v, str):
            parts.append(v)
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


#: The metrics A1 persists. Both verified 11/11 against values that distinguish the consensus
#: block from its twin; a third metric must be re-checked PER NAME (the block-membership evidence
#: is SMPL-only).
CONSENSUS_METRICS = ("Revenue", "EBITDA")


def consensus_transform(ticker: str) -> Transform:
    """(A1) A `refresh_dossier` transform injecting forward-year consensus levels.

    THE BLOCK IS RESOLVED ONCE PER NAME and passed to both metric reads. Re-resolving it per
    metric is the coupling #311 removed one level down — and resolving once also makes the
    double-sheet-read question moot rather than needing a cache.

    Absent bundle, absent block, or a metric that does not resolve leaves the field UNTOUCHED
    rather than writing an empty list: `None` means NOT REFRESHED and `[]` would mean THE STREET
    HAS NO VIEW, which are different claims.
    """
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import consensus_block, consensus_rows
    from vinci.dossier.manual_store import LocalFolderStore

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except Exception:                                 # noqa: BLE001 - no bundle, no injection
            return mech
        if consensus_block(bundle) is None:
            return mech
        levels: dict[str, list[dict[str, Any]]] = {}
        for metric in CONSENSUS_METRICS:
            try:
                cells = consensus_rows(bundle, metric=metric)
            except CiqUnavailableError:
                raise                                     # LOW <= MEDIAN <= HIGH refusal propagates
            if cells:
                levels[metric] = [
                    {"fy": c.fy, "median": c.median, "high": c.high, "low": c.low,
                     "std_dev": c.std_dev, "estimates": c.estimates} for c in cells]
        if not levels:
            return mech
        out: dict[str, Any] = json.loads(json.dumps(mech))
        cc = out.get("consensus_context")
        if not isinstance(cc, dict):
            return mech
        cc["consensus_levels"] = levels
        return out

    return _apply


def refresh_dossier(path: Path, *, transform: Transform | None = None) -> bool:
    """Refresh one committed dossier IN PLACE, preserving its synthesis. True when anything moved.

    Writes BOTH artifacts — ``dossier.json`` and ``dossier.md`` — because the assembler does, and
    the point of this path is to fix numbers a READER sees. REVIEW FINDING: the first cut wrote only
    the JSON, so a refresh that moved SMPL's cap 909.4 → 1,000.0 updated TEV to 1,324.6 in the
    record while the page still showed the old figure. Two committed artifacts that disagree, and
    the repo's own e2e staleness pins would have caught it on the next run — after the diff had
    already been reviewed as correct.

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
    # Imported here, not at module scope: `assemble` imports this module's siblings and a top-level
    # import of the renderer would cycle (the `_read_scenario_card` precedent).
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    model = Dossier.model_validate(doc)
    # VERSION-SCOPED WRITE, the #303 principle applied to the dossier. `consensus_levels` is
    # optional-with-None, so a plain dump writes `"consensus_levels": null` into all eleven
    # committed artifacts and a NO-OP refresh stops being byte-identical — the 119-null-keys
    # defect in a new place. Omitted when None, which also keeps ABSENT meaning "not refreshed"
    # rather than "the street has no view". Dropped by KEY, not by value: a name that HAS levels
    # writes them.
    payload = json.loads(model.model_dump_json())
    cc = (payload.get("mechanical") or {}).get("consensus_context")
    if isinstance(cc, dict) and cc.get("consensus_levels") is None:
        cc.pop("consensus_levels", None)
    new_json = json.dumps(payload, indent=2, ensure_ascii=False)
    new_md = render_markdown(model, card=_read_scenario_card(model.ticker))
    md_path = path.with_name("dossier.md")
    old_md = md_path.read_text() if md_path.exists() else None
    changed = new_json != path.read_text() or (old_md is not None and new_md != old_md)
    if changed:
        path.write_text(new_json)
        md_path.write_text(new_md)
    return changed
