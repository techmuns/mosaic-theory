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
from datetime import date
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
    from vinci.dossier.ciq_sheets import consensus_levels as ciq_consensus_levels
    from vinci.dossier.manual_store import LocalFolderStore

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        # ABSENT AND BROKEN ARE DIFFERENT STATES. A name with no CIQ export legitimately skips;
        # a name whose export is CORRUPT must fail loud. The first cut caught bare `Exception`
        # and returned `mech` for both — and since nothing renders `consensus_levels` until A2, a
        # corrupt bundle would have made the fleet pass report success while silently injecting
        # nothing. That is #308's vanishing-marker defect in a new place: a warning that fails is
        # not a warning that was not needed.
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return mech                                    # no export for this name — skip, silent
        # THE SAME BUILDER ASSEMBLY USES. Two call sites constructing this structure would be the
        # twin-drift class, and silent: nothing renders it until A2, so a divergence would surface
        # as a name whose numbers depend on which path last wrote it.
        levels = {m: [{"fy": c.fy, "median": c.median, "high": c.high, "low": c.low,
                       "std_dev": c.std_dev, "estimates": c.estimates} for c in cells]
                  for m, cells in ciq_consensus_levels(bundle).items()}
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

    Raises :class:`RefreshRefusedError` when a moved figure is one the stored prose cites, or when
    the name's record is SEALED."""
    # A SEALED RECORD IS NOT REFRESHABLE. FUBO's `known_wrong.json` states the rule in its own
    # words — "`dossier.json` is untouched … it stays sealed" until a post-combination re-assembly
    # exists — and the A2b pass wrote `ev_gap` straight into it anyway. The seal test caught it,
    # which is the guard working; this makes the WRITE PATH refuse instead of relying on whoever
    # runs the pass remembering. Keyed on the sidecar's presence, so a name that acquires one is
    # sealed without anyone editing this file.
    if (path.parent / "known_wrong.json").exists():
        raise RefreshRefusedError(
            f"{path.parent.name}: this record is SEALED by its own known_wrong.json — refreshing "
            "it would make a page that says 'do not trust these figures' look freshly computed. "
            "It clears when a re-assembly exists, not when a transform runs.")
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


def ev_gap_transform(ticker: str) -> Transform:
    """(A2b) A `refresh_dossier` transform writing the EV-gap FORM into `mech.ev_gap`.

    ALWAYS WRITES, and that is the difference from `consensus_transform`. Consensus levels leave
    the field UNTOUCHED when absent, because `None` there means NOT REFRESHED and `[]` would claim
    the street has no view. Here the two states are told apart INSIDE the value: `None` still means
    not refreshed, while a written `status="not-computed"` with a stated reason means the refresh
    RAN and could not strike a gap. A render that shows an empty block instead of one of those two
    sentences is the two-speed defect the insider horizon just taught.

    OUR LEG IS THE `base` SCENARIO. The gap is "what our base case implies against what the street
    implies", so bear/bull would be answering a different question; a record without a `base` leg
    is a not-computed with a reason, never a silent substitution.
    """
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import comps_as_of, estimates_as_of
    from vinci.dossier.ev_gap import build_ev_gap
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.schemas import SourceStatus

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        levels = ((out.get("consensus_context") or {}).get("consensus_levels")) or None

        tev_as_of = consensus_as_of = None
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            bundle = None
        if bundle is not None:
            c, e = comps_as_of(bundle), estimates_as_of(bundle)
            # VERBATIM, floor marker and all. SMPL's estimates export carries no As-Of header, so
            # its date is a FLOOR ("≥2026-07-21"); flattening that to a plain date would
            # manufacture precision the workbook does not have.
            tev_as_of = c.value if c.status is SourceStatus.PRESENT else None
            consensus_as_of = e.value if e.status is SourceStatus.PRESENT else None

        cap = ((out.get("implied_valuation") or {}).get("market_cap") or {}).get("value")
        grid = ((out.get("peer_comps") or {}).get("peer_grid") or {}).get("value") or []
        self_row = next((r for r in grid if r.get("is_name")), None)
        nd = self_row.get("net_debt") if self_row else None
        # TEV IS STRUCK FROM THE SAME PANEL AS ITS VINTAGE. Both come off the comps workbook, so
        # the stamp describes the numbers rather than sitting near them.
        tev = (float(cap) + float(nd)) if isinstance(cap, (int, float)) and isinstance(
            nd, (int, float)) else None

        leg = _base_leg(ticker)
        out["ev_gap"] = build_ev_gap(
            levels, leg,
            tev=tev, net_debt=float(nd) if isinstance(nd, (int, float)) else None,
            shares=(leg or {}).get("shares"),
            tev_as_of=tev_as_of, consensus_as_of=consensus_as_of)
        return out

    return _apply


def _base_leg(ticker: str) -> dict[str, Any] | None:
    """The `base` scenario leg plus the facts the decomposition needs, or None.

    READS THE RECORD THROUGH `vinci.scenarios.read_record` — the SAME reader the renderer and
    `assemble` use, so there is one definition of "the record" rather than a second path that can
    drift from it. Imported inside the function because `vinci.scenarios` imports
    `vinci.dossier.midcycle`; a module-scope import would cycle (the reason `_read_scenario_card`
    gives for the same move).

    ABSENT is normal — most names are never underwritten — and degrades to None, which
    `build_ev_gap` turns into a stated `not-computed`. A record that EXISTS but will not parse
    PROPAGATES: swallowing it would write "no scenario record" onto a name that has one.
    """
    from vinci.scenarios import read_record

    try:
        rec = read_record(ticker)
    except FileNotFoundError:
        return None
    base = rec.scenarios.get("base")
    if base is None:
        return None

    def fact(name: str) -> float | None:
        f = rec.facts.get(name)
        return float(f.value) if f is not None and isinstance(f.value, (int, float)) else None

    return {
        "revenue": base.revenue, "margin": base.margin, "multiple": base.multiple,
        # R1 RECORDS STORE AN OPERATING MARGIN — SMPL's 0.14 against a 12.5x EV/EBITDA multiple is
        # the case `our_ebitda` exists for. Stated as a constant rather than inferred from the
        # number's size, which would be a guess dressed as a lookup; a future recipe storing an
        # EBITDA margin must set this from `recipe_id`, and `our_ebitda` REFUSES rather than
        # silently dividing EBIT-margin by EBITDA-margin if it is wrong.
        "margin_basis": "operating",
        "multiple_basis": rec.multiple_basis,
        "d_and_a": fact("d_and_a"),
        "shares": fact("diluted_shares"),
        # THE D&A CONVENTION, CARRIED SO A2 CAN PRINT IT (operator ruling 2026-07-30). R1 stores a
        # FIXED $M anchor; R2 stores a RATIO OF REVENUE. They are not a contradiction but a horizon
        # difference — R1 is mid-cycle where a fixed asset base is right, R2 terminal where D&A
        # converges to maintenance capex as a share of revenue. Converting R2's ratio at the anchor
        # is the RESERVED ANALYST DECISION ("it moves committed numbers and is a decision, not a
        # build"), so it is surfaced here and never applied here.
        "d_and_a_convention": ("fixed $M anchor (R1, mid-cycle)" if fact("d_and_a") is not None
                               else "ratio of revenue (R2, terminal)"
                               if fact("d_and_a_ratio") is not None else None),
        "d_and_a_ratio": fact("d_and_a_ratio"),
        "recipe_id": rec.recipe_id,
    }


def insider_transform(ticker: str, cik: str | None, reference_date: date) -> Transform:
    """Re-fetch the Form 4 insider line so the VALUE states its own horizon.

    RIDES THE SAME PASS AS `ev_gap_transform`, deliberately. Both write the mechanical layer, and
    the render that drops "6m" from the label ships on deploy — so if the value lagged, the served
    page would state no horizon at all. That is the #319 regression exactly, and running the two
    transforms together is what makes the label change safe rather than merely intended.

    A FAILED FETCH LEAVES THE FIELD ALONE. Overwriting a good line with an UNKNOWN because EDGAR
    was briefly unreachable would trade a correct disclosure for a blank one.
    """
    from vinci.dossier.mechanical import _insider_activity
    from vinci.dossier.schemas import SourceStatus
    from vinci.edgar.client import EdgarClient
    from vinci.sec import build_sec_http

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        cp = mech.get("catalyst_path")
        if not isinstance(cp, dict) or not cik:
            return mech
        got = _insider_activity(
            EdgarClient.from_config(), build_sec_http(), cik, reference_date)
        if got.status is not SourceStatus.PRESENT:
            return mech
        out: dict[str, Any] = json.loads(json.dumps(mech))
        out["catalyst_path"]["insider_activity"] = json.loads(got.model_dump_json())
        return out

    return _apply


def chain(*transforms: Transform) -> Transform:
    """Apply transforms left to right — ONE pass, so a name is written once rather than N times.

    Sequential rather than merged because they read each other's output: nothing does today, but a
    merge would make the order invisible on the day something does."""
    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        for t in transforms:
            mech = t(mech)
        return mech
    return _apply
