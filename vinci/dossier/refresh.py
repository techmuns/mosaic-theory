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
import math
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from vinci.dossier.schemas import DROP_WHEN_NONE, Dossier, dossier_json
from vinci.dossier.synthesis import (
    MATERIAL_FIGURE_FLOOR_MUSD,
    SYNTHESIS_CLAIM_LISTS,
    SYNTHESIS_CLAIM_SCALARS,
    _figure_cited,
)

#: ``mech -> mech``, applied before the derived rebuild. The seam B1 plugs into.
Transform = Callable[[dict[str, Any]], dict[str, Any]]
#: ``doc -> {key: value}`` for DOSSIER-LEVEL fields that live outside ``mechanical``. Only the keys
#: in `_TOP_LEVEL_REFRESHABLE` may be set: the mechanical layer, the synthesis and the anchor each
#: have their own write path and guards, and this seam must not become a way around them.
TopLevelTransform = Callable[[dict[str, Any]], dict[str, Any]]
#: `caveats` since 2026-10-21, for ONE use: `leverage_caveat_transform` regenerates the leverage
#: caveat from the page's stored ratio, and refuses if any other caveat would move.
_TOP_LEVEL_REFRESHABLE = frozenset({"forward_consensus", "forward_multiple_history",
                                    "historical_forecast_error", "ev_bridge", "caveats"})


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
            # DECODED (`ensure_ascii=False`): an escaped minus (`\u2212`) put a digit against the
            # number after it and hid WLK's "rel −48%" from the returns check (2026-10-18)
            parts.append(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False))
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


#: A revision count as the catalyst-path strings print it: '41↑/4↓'.
_COUNT_TOKEN = re.compile(r"\d+↑/\d+↓")


def _count_tokens(obj: Any) -> set[str]:
    return set(_COUNT_TOKEN.findall(json.dumps(obj, ensure_ascii=False)))


def moved_cited_counts(before: dict[str, Any], after: dict[str, Any],
                       doc: dict[str, Any]) -> list[str]:
    """Revision counts the stored prose cites that the refreshed layer no longer carries ANYWHERE —
    the count-sized companion to `moved_cited_claims`, whose floor is money and lets every count
    through.

    A count still printed elsewhere on the page still traces, so only a VANISHED token refuses.
    `_prose` is decoded, so '↑' reads as itself. LIMIT, stated: a count the prose paraphrased
    ('41 upward revisions') is not a token and is not caught here."""
    prose = _prose(doc)
    return [f"revision count {t} (no longer on the page)"
            for t in sorted(_count_tokens(before) - _count_tokens(after)) if t in prose]


#: the market-relative RETURNS a page states, as (block, field) — the percentage-sized companion to
#: the money floor of `moved_cited_claims`, which lets every return through
_RETURN_FIELDS = (("idiosyncratic_vs_shared", "name_180d_return"),
                  ("idiosyncratic_vs_shared", "market_180d_return"),
                  ("idiosyncratic_vs_shared", "rel_vs_market"),
                  ("stock_performance", "name_return"),
                  ("stock_performance", "benchmark_return"))
#: a percentage as prose writes one: "16.9%", "~8.4pts", "28pt", "3 pp"
_PCT_UNIT = r"\s?(?:%|pts?\b|pp\b|percentage points?\b|points?\b)"
#: words that put a rounded percentage in the MARKET's context — a whole-number match counts only
#: within `_RETURN_CONTEXT_CHARS` of one, because "17%" alone is anything (GOOGL: "Search & Other
#: grew 17%" beside a 16.9% SPY return)
_RETURN_CONTEXT = (r"\b(?:benchmark|market|relative|rel|index|outperform\w*|underperform\w*"
                   r"|lag\w*)\b")
_RETURN_CONTEXT_CHARS = 60


def _claim_texts(doc: dict[str, Any]) -> list[str]:
    """Each claim's own WORDS, one string per claim — the free text a reader reads, never a
    claim's ``source_ref`` (a pointer, which names the benchmark and would vouch for a figure
    beside it). The block list is `_prose`'s, by the same import."""
    syn = doc.get("synthesis") or {}
    out: list[str] = []
    for block in SYNTHESIS_CLAIM_LISTS:
        for p in syn.get(block) or []:
            text = p if isinstance(p, str) else (p.get("claim") if isinstance(p, dict) else None)
            if isinstance(text, str):
                out.append(text)
    out.extend(v for attr in SYNTHESIS_CLAIM_SCALARS
               if isinstance(v := syn.get(attr), str))
    return out


def _forms(a: float, places: int) -> set[str]:
    """``a`` written to ``places`` decimals EITHER way a writer may round it: a value on a
    half-step (16.85) is "16.8" to one writer and "16.9" to another, and Python's binary
    half-even rounding picks only one (code review of #745)."""
    k = 10 ** places
    return {f"{math.floor(a * k) / k:.{places}f}", f"{math.ceil(a * k) / k:.{places}f}"}


def _stated_return(mech: dict[str, Any], block: str, field: str) -> float | None:
    b = mech.get(block)
    v = b.get(field) if isinstance(b, dict) else None
    v = v.get("value") if isinstance(v, dict) else v  # a Sourced field, or a plain float
    return float(v) if isinstance(v, (int, float)) else None


def return_cited(prose: str | list[str], fraction: float, *, symbol: str = "") -> bool:
    """Is a return (a FRACTION, as stored) cited in ``prose`` — one text, or one per claim — as a
    percentage?

    LEANS TO CITED, the safe direction for a REFUSAL: a false match refuses a correct refresh and
    sends the name to re-assembly; a miss leaves prose citing a number its tables no longer show.
    One decimal ("16.9%") stands alone — specific enough not to collide; a whole number ("11%")
    counts only beside a market word or the benchmark's symbol, because a rounded percentage
    alone is anything. Measured on the nine pages the 2026-09-16 benchmark hole touched
    (2026-10-18): the seven whose prose quotes the benchmark match, GOOGL and LLY — whose 17% and
    57% are a revenue growth rate and a P/E premium — do not.

    Both forms accept the value rounded EITHER way (`_forms`); the context for a whole number is
    searched within ITS OWN claim, never across into the next one (code review of #745)."""
    a = abs(fraction) * 100.0
    texts = [prose] if isinstance(prose, str) else prose
    near = _RETURN_CONTEXT + (rf"|\b{re.escape(symbol)}\b" if symbol else "")
    for text in texts:
        for form in _forms(a, 1):
            if re.search(rf"(?<![\d.]){re.escape(form)}{_PCT_UNIT}", text, re.I):
                return True
        for form in _forms(a, 0):
            for m in re.finditer(rf"(?<![\d.]){re.escape(form)}{_PCT_UNIT}", text, re.I):
                lo, hi = max(0, m.start() - _RETURN_CONTEXT_CHARS), m.end() + _RETURN_CONTEXT_CHARS
                if re.search(near, text[lo:hi], re.I):
                    return True
    return False


def moved_cited_returns(before: dict[str, Any], after: dict[str, Any],
                        doc: dict[str, Any]) -> list[str]:
    """Market-relative returns that MOVED and that the stored prose CITES — the percentage-sized
    companion to `moved_cited_claims`, whose floor is money and lets every return through.

    2026-10-18: correcting the nine pages whose benchmark read the 2026-09-16 close as 09-22 would
    have passed both existing checks on all nine — and seven of them quote the stale figure ("SPY
    rose ~16.9% (-47.6% relative)", NKE). The refresh would have left those pages contradicting
    their own tables, the 19c defect this module exists to refuse.

    Each claim is read on its own words (`_claim_texts`) — never its source_ref, never across into
    the next claim."""
    claims = _claim_texts(doc)
    io = before.get("idiosyncratic_vs_shared")
    symbol = str(io.get("benchmark_symbol") or "") if isinstance(io, dict) else ""
    hits: list[str] = []
    for block, field in _RETURN_FIELDS:
        old, new = _stated_return(before, block, field), _stated_return(after, block, field)
        if old is None or old == new:
            continue
        if return_cited(claims, old, symbol=symbol):
            hits.append(f"{block}.{field} = {old * 100:+.1f}% → "
                        + ("absent" if new is None else f"{new * 100:+.1f}%"))
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


def _rerender_only(path: Path) -> bool:
    """Re-render ``dossier.md`` from the STORED record, leaving ``dossier.json`` untouched.

    The sealed-name path. Reads, validates and renders — it never recomputes derived values and
    never writes the JSON, so a sealed record's figures cannot move through here. True when the
    page moved, matching :func:`refresh_dossier`'s contract."""
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    model = Dossier.model_validate(json.loads(path.read_text()))
    md_path = path.with_name("dossier.md")
    new_md = render_markdown(model, card=_read_scenario_card(model.ticker),
                             dossiers_root=path.parent.parent)
    if md_path.exists() and md_path.read_text() == new_md:
        return False
    md_path.write_text(new_md)
    return True


#: Optional mechanical fields added AFTER the artifacts were committed, each DROPPED when None —
#: the table and the writer that applies it now live in `schemas.DROP_WHEN_NONE` / `dossier_json`,
#: because the ASSEMBLER writes through the same function (see `dossier_json`'s own note). Re-named
#: here so the existing references — `mechanical.py`'s `sbc` comment, the `sbc` test's docstring —
#: still resolve to one table.
_DROP_WHEN_NONE = DROP_WHEN_NONE


def refresh_dossier(path: Path, *, transform: Transform | None = None,
                    top_level: TopLevelTransform | None = None) -> bool:
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
        if transform is not None or top_level is not None:
            raise RefreshRefusedError(
                f"{path.parent.name}: this record is SEALED by its own known_wrong.json — "
                "refreshing it would make a page that says 'do not trust these figures' look "
                "freshly computed. It clears when a re-assembly exists, not when a transform runs.")
        # SEALED FREEZES THE FIGURES; IT DOES NOT STOP THE PAGE TRACKING THE RENDERER.
        # The refusal above states what the seal is FOR — a refreshed page "looks freshly
        # computed" — and a pure re-render makes nothing look fresh: `dossier.json` is never
        # written, every figure and the known-wrong banner stay byte-identical, and only wording
        # the RENDERER owns can move. Refusing it left FUBO's committed page rendered by a renderer
        # that no longer exists: the R3 label fix (2026-08-04) turned this repo's own render-drift
        # pin RED on FUBO with no path to green, because the only writer refused the one name that
        # cannot re-assemble. A seal satisfiable only by re-assembly, on a name that cannot
        # re-assemble, is a permanent red.
        return _rerender_only(path)
    doc = json.loads(path.read_text())
    before = doc.get("mechanical") or {}
    staged = transform(json.loads(json.dumps(before))) if transform else before
    after = recompute_derived(staged)
    if doc.get("synthesis") is not None and (bad := [*moved_cited_claims(before, after, doc),
                                                     *moved_cited_counts(before, after, doc),
                                                     *moved_cited_returns(before, after, doc)]):
        raise RefreshRefusedError(
            f"{doc.get('ticker')}: this refresh moves figures the stored synthesis CITES — "
            f"{'; '.join(bad)}. Preserving the prose would leave the page citing numbers its own "
            "tables no longer show (item 19c, manufactured deliberately). Re-assemble this name "
            "instead; the other names in the batch are unaffected.")
    doc["mechanical"] = after
    if top_level is not None:
        extra = top_level(doc)
        if stray := sorted(set(extra) - _TOP_LEVEL_REFRESHABLE):
            raise ValueError(f"{doc.get('ticker')}: a top-level refresh may set only "
                             f"{sorted(_TOP_LEVEL_REFRESHABLE)}, not {stray}")
        doc.update(extra)
    # ONE SERIALIZER, SHARED WITH THE ASSEMBLER (`schemas.dossier_json`). This path used to re-dump
    # the model's payload with `json.dumps`, which differs from the assembler on unicode escaping
    # and on float repr. The escaping half was fixed by hand; the float half surfaced years later,
    # when PARR's page carried a dilution item at 0.0000245 of assets and a NO-OP refresh rewrote
    # two lines as `2.45e-05`. Two serializers for one artifact is the twin-drift class, so the fix
    # is one writer rather than a second patch. Validating on the way out is the bonus: a refresh
    # that broke the schema fails here rather than shipping.
    # Imported here, not at module scope: `assemble` imports this module's siblings and a top-level
    # import of the renderer would cycle (the `_read_scenario_card` precedent).
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown

    model = Dossier.model_validate(doc)
    new_json = dossier_json(model)
    # THE PAGE RECORDS THIS REFRESH, and the vintage that ran it (`layer_refresh`, the 2026-08-17
    # ruling's unlock). Only when a LAYER moved: a no-op refresh, or one that only re-renders the
    # page, leaves the JSON — and so the record — byte-identical.
    original = path.read_text()
    if new_json != original:
        from vinci.dossier import layer_refresh

        if moved := layer_refresh.moved_layers(json.loads(original), json.loads(new_json)):
            model = layer_refresh.append(model, layer_refresh.entry("refresh", moved))
            new_json = dossier_json(model)
    new_md = render_markdown(model, card=_read_scenario_card(model.ticker),
                             dossiers_root=path.parent.parent)
    md_path = path.with_name("dossier.md")
    old_md = md_path.read_text() if md_path.exists() else None
    changed = new_json != path.read_text() or (old_md is not None and new_md != old_md)
    if changed:
        path.write_text(new_json)
        md_path.write_text(new_md)
    return changed


def benchmark_figures_transform(ticker: str, reference_date: date, *,
                                store_path: Path | None = None) -> Transform:
    """A `refresh_dossier` transform re-reading the BENCHMARK side of a page's market figures —
    ``idiosyncratic_vs_shared``'s market move and the difference, and ``stock_performance`` — at the
    page's own date (STATE row 32 (7): nine pages read SPY's or MDY's 2026-09-16 close as 09-22).

    THE CORRECTION MOVES ONLY WHAT THE BUG TOUCHED, OR IT IS REFUSED (`horizon_read_transform`'s
    rule). The name's side is recomputed too and must reproduce the stored page EXACTLY — its
    180-day move and its source, and, when the page has a 52-week exhibit, every point, the return
    and the end date of its line — proof the store holds the bars the page was built from. Any
    difference RAISES `RefreshRefusedError` naming it, never a silent "nothing moved" that reads
    like a page already correct (code review of #745). So does a missing store — opening one would
    CREATE an empty database — and a ticker that is not exactly one security. A page with no
    exhibit has its 180-day figures corrected alone. The cohort and its read are kept.

    UNDER A KEPT SYNTHESIS. A return the prose quotes refuses the refresh
    (`moved_cited_returns`): seven of the nine pages quote the stale figure and need a re-assembly.
    ``store_path`` defaults to the configured store; a test passes its own."""
    from vinci.config import get_config
    from vinci.dossier.mechanical import _market_legs, _stock_performance
    from vinci.store import Store
    from vinci.universe import benchmark_identity

    def refuse(why: str) -> RefreshRefusedError:
        return RefreshRefusedError(f"{ticker}: the benchmark figures cannot be re-read — {why}. "
                                   "Re-assemble this name instead.")

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        io, sp0 = out.get("idiosyncratic_vs_shared"), out.get("stock_performance")
        if not (isinstance(io, dict) and io.get("benchmark_symbol")):
            return out  # the page states no market-relative figures: nothing to correct
        db = store_path or get_config().db_path
        if not db.exists():
            raise refuse(f"no price store at {db}")
        bench = benchmark_identity(str(io["benchmark_symbol"]))
        with Store(db) as store:
            idents = store.securities_for_ticker(ticker)
            if len(idents) != 1:
                raise refuse(f"{len(idents)} securities carry the ticker, not one")
            ident = idents[0]
            name, market, rel, _end = _market_legs(
                store.get_price_history(ident.internal_id),
                store.get_price_history(bench.internal_id), reference_date,
                sym=ident.eod_symbol, bsym=bench.eod_symbol,
                bench_basis=str(io.get("benchmark_basis") or ""))
            sp = (_stock_performance(ident, store, reference_date, bench=bench)
                  if isinstance(sp0, dict) else None)
        stored = io.get("name_180d_return") or {}
        if name.value != stored.get("value") or name.source_ref != stored.get("source_ref"):
            raise refuse(f"the name's 180-day move does not reproduce ({name.value} "
                         f"'{name.source_ref}' vs stored {stored.get('value')} "
                         f"'{stored.get('source_ref')}')")
        if isinstance(sp0, dict) and (
                sp is None or sp.name_return != sp0.get("name_return")
                or str(sp.as_of) != sp0.get("as_of")
                or [(p.date, p.name) for p in sp.points]
                != [(p.get("date"), p.get("name")) for p in sp0.get("points") or []]):
            raise refuse("the name's 52-week line does not reproduce from this store")
        io["market_180d_return"] = market.model_dump(mode="json")
        io["rel_vs_market"] = rel.model_dump(mode="json")
        if sp is not None:
            out["stock_performance"] = sp.model_dump(mode="json")
        return out

    return _apply


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
    from vinci.dossier.ciq_sheets import estimates_as_of
    from vinci.dossier.ev_gap import build_ev_gap
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.schemas import SourceStatus

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        levels = ((out.get("consensus_context") or {}).get("consensus_levels")) or None

        # CARRY THE PRIOR VINTAGES FORWARD — a refresh must never ERASE provenance it cannot
        # re-read. The licensed CIQ workbooks are git-ignored and absent from CI and from any
        # machine without the export, so the first cut wrote `None` over both stamps whenever the
        # bundle was missing: running the pass anywhere without the workbooks would have silently
        # stripped the vintages off every dossier while leaving the gap itself computed — a number
        # keeping its value while losing the thing that says what it describes.
        # CI CAUGHT THIS, not the local gate, because this worktree HAS the exports. Same principle
        # `insider_transform` already states: a fetch that cannot run leaves the field alone.
        # THE TEV STAMP DESCRIBES THE STORED NUMBERS, and comes from where they came from.
        # REVIEW OF #321 caught the first cut re-reading `comps_as_of` off the CURRENT bundle while
        # the cap and net debt it stamps are the STORED ones — so AORT/IT/VITL got a 2026-07-30
        # stamp on figures extracted 2026-06-25, 35 days of false provenance, which is precisely
        # the class this block claims to guard. `implied_expectations.tev_as_of` is a STRUCTURED
        # stored field carrying the TEV's own vintage, and it matches the stored cap's as-of on all
        # 11 committed names.
        ie_stored = ((out.get("valuation") or {}).get("implied_expectations") or {})
        ie_stored = (ie_stored.get("value")
                     if isinstance(ie_stored, dict) and "value" in ie_stored else ie_stored)
        prior = (out.get("ev_gap") or {}).get("vintages") or {}
        tev_as_of = (ie_stored or {}).get("tev_as_of") or prior.get("tev_as_of")
        consensus_as_of = prior.get("consensus_as_of")
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            bundle = None
        if bundle is not None:
            e = estimates_as_of(bundle)
            # VERBATIM, floor marker and all. SMPL's estimates export carries no As-Of header, so
            # its date is a FLOOR ("≥2026-07-21"); flattening that to a plain date would
            # manufacture precision the workbook does not have.
            # A READABLE BUNDLE THAT CANNOT DATE ITSELF also keeps the prior stamp rather than
            # blanking it: "this export states no as-of" is a different fact from "we never had
            # one", and only the second justifies erasing what is already recorded.
            # ONLY THE CONSENSUS VINTAGE comes off the bundle. The TEV's does NOT: its numbers are
            # stored, so a freshly-read workbook date would describe a different extraction.
            consensus_as_of = e.value if e.status is SourceStatus.PRESENT else consensus_as_of

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


def capital_allocation_transform(cik: str | None) -> Transform:
    """A `refresh_dossier` transform writing `mech.capital_allocation` from EDGAR companyfacts.

    WHY A TRANSFORM AND NOT A RE-ASSEMBLY. The block is DETERMINISTIC — one EDGAR read, no LLM —
    while a full re-assembly also rerolls the synthesis. That is not a neutral cost: EPAM sits
    **0.4% from the 2:1 bar** (base $186.76, bear $74.06 → clears at $111.63 against a $112.06
    spot) and has already been rolled twice this week. Spending a variance event to land a
    deterministic block is paying the wrong price, and `refresh_dossier` exists precisely so a
    number can move under a KEPT synthesis.

    The `ev_gap_transform` precedent settles the shape question: a transform may read from OUTSIDE
    the stored JSON — that one opens CIQ workbooks off disk. This one calls EDGAR.

    ALWAYS WRITES, the `ev_gap_transform` rule rather than `consensus_transform`'s: every field of
    the block degrades to UNKNOWN-with-a-reason, so a written block always says something, and the
    absent/`None` state keeps its distinct meaning of NOT YET REFRESHED.

    NO REFUSAL RISK BY CONSTRUCTION: the block is a new key, so no committed synthesis can cite a
    figure it moves — `moved_cited_claims` has nothing to find. That is a property of it being
    additive, not a licence for the next transform.
    """
    from vinci.dossier.capital_allocation import build_capital_allocation
    from vinci.edgar.client import EdgarClient
    from vinci.netcache import HttpError

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        # A FETCH FAILURE IS NOT AN EMPTY FILING, and collapsing to `{}` made them identical. Every
        # field would then read "no goodwill balance under Goodwill — EDGAR XBRL companyfacts",
        # which states that the FILER reports none when the truth is that WE could not reach EDGAR.
        # Two opposite facts wearing one sentence is the shape this repo keeps closing (`unstated`
        # vs `disagrees`, grown-out vs failed), and here the wrong one is the reassuring one.
        #
        # So: write NOTHING. Absent already has a meaning — NOT YET REFRESHED — and that is exactly
        # what a failed fetch leaves behind. `refresh_dossier` then sees no change and reports the
        # name as unmoved, which is honest; re-running when EDGAR answers writes the block.
        if not cik:
            return out
        try:
            facts = EdgarClient.from_config().companyfacts(cik)
        except (HttpError, KeyError, ValueError):   # `_companyfacts_or_none`'s own exception set
            return out
        out["capital_allocation"] = json.loads(
            build_capital_allocation(facts).model_dump_json())
        return out

    return _apply



def peer_capital_intensity_transform() -> Transform:
    """A `refresh_dossier` transform writing `mech.peer_capital_intensity` from the STORED grid.

    THE PEER SET COMES OUT OF THE ARTIFACT, not the workbook. `peer_comps.peer_grid` already holds
    every peer's ticker and market cap, parsed and committed — so this reaches FUBO and MVST, which
    cannot be re-assembled at all, and it cannot disagree with the grid the page already shows. The
    goodwill/intangible/assets figures are EDGAR's: one cached companyfacts call per peer.

    NO GRID -> WRITE NOTHING. Absent keeps its meaning of NOT YET REFRESHED, and a block written
    without a peer set would be a claim about peers we never looked at.

    A WHOLE-SET RESOLUTION FAILURE ALSO WRITES NOTHING, and that guard cannot live in the builder.
    `build_peer_capital_intensity` is total by design: a peer that will not resolve gets a row
    saying so, which is right for ONE bad ticker. But if NOT ONE of eleven resolves, the fact being
    reported is that the resolver is unavailable — and eleven rows each reading "no CIK for 'UTZ'"
    states something false about eleven companies. #362's rule at set scope: a systemic failure
    must not be published as a per-item finding.
    """
    from vinci.dossier.capital_allocation import build_peer_capital_intensity
    from vinci.dossier.schemas import PeerRow
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        raw = ((out.get("peer_comps") or {}).get("peer_grid") or {}).get("value") or []
        if not raw:
            return out
        grid = [PeerRow.model_validate(r) for r in raw]
        built = build_peer_capital_intensity(
            grid, resolve=EntityResolver.from_config().resolve_ticker,
            companyfacts=EdgarClient.from_config().companyfacts)
        if built.rows and all(str(r.note or "").startswith("unresolved") for r in built.rows):
            return out          # see the docstring: a systemic failure, not eleven facts
        out["peer_capital_intensity"] = json.loads(built.model_dump_json())
        return out

    return _apply


def basis_triangulation_transform(ticker: str) -> Transform:
    """Rebuild `primary_source.basis_triangulation` FROM ITS SOURCES after a record appears.

    WHY THIS EXISTS. Writing an underwrite record changes what the covenant-basis line should say —
    `_covenant_basis(card)` feeds it — but the line is built during FULL ASSEMBLY and no refresh
    path touched it. Creating BellRing's record made its committed page stale by one line, and the
    only remedy on offer was a re-assembly that would re-roll the synthesis its own underwrite
    cites. This is the narrow alternative.

    IT REBUILDS, IT DOES NOT EDIT. Rewriting the one line in the stored string would make the other
    four identical BY CONSTRUCTION — which is assuming the answer, not verifying it. Re-deriving
    all five from the sources and finding four unchanged is the proof; the caller asserts it.

    IT READS NO PRICE STORE, which is what makes it safe to run from any worktree. Its inputs are
    the committed mechanical layer, the local CIQ bundle, the EDGAR releases (cached) and the card.
    `data/vinci.db` is per-worktree — this checkout's is a symlink to a different one at a
    different frontier — so a recompute that read prices could silently derive against a store the
    page was never built from.

    AND IT WRITES BACK EXACTLY ONE FIELD. `_primary_source` also returns operating drivers and the
    rest of the primary-source layer; taking anything but `basis_triangulation` would smuggle a
    wider rebuild into a targeted fix.

    THE REAL DEFECT IS ONE LAYER DOWN. `basis_triangulation` stores a RENDERED FIVE-LINE STRING
    with no structured backing, so no single component can be recomputed without re-deriving all
    five — the house rule about display strings, inverted: the field publishes its rendering and
    keeps its values private. Exposing the components is the fix; this is the bridge.
    """
    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        import pathlib as _pl

        from vinci.config import Config
        from vinci.dossier import mechanical as dm
        from vinci.dossier.assemble import _read_scenario_card, load_finalists
        from vinci.dossier.ciq import CiqBundle
        from vinci.dossier.schemas import MechanicalLayer
        from vinci.edgar.client import EdgarClient
        from vinci.sec import build_sec_http

        out: dict[str, Any] = json.loads(json.dumps(mech))
        card = _read_scenario_card(ticker)
        if card is None:
            return out                      # no record — nothing about the line has changed
        node = (out.get("primary_source") or {}).get("basis_triangulation") or {}
        old = str(node.get("value") or "")
        if not old:
            return out

        cfg = Config.load() if hasattr(Config, "load") else Config()
        fin = load_finalists(cfg, ticker=ticker)[0]
        bundle = CiqBundle.from_files(
            ticker, sorted(_pl.Path(f"data/manual/ciq/{ticker}").glob("*")))
        primary, _lat, _drv = dm._primary_source(
            fin.data_record, EdgarClient.from_config(cfg), build_sec_http(cfg),
            bundle, fin.reference_date, MechanicalLayer.model_validate(out), card)
        rebuilt = primary.basis_triangulation.value or ""
        if not rebuilt:
            return out

        # FOUR LINES MUST COME BACK BYTE-IDENTICAL. Anything else means the rebuild is wider than
        # a covenant-basis restatement, and a wider rebuild is not what this transform promises.
        a, b = old.splitlines(), rebuilt.splitlines()
        moved = [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y]
        if len(moved) > 1 or any(not a[i].strip().startswith("covenant basis:") for i in moved):
            raise ValueError(
                f"{ticker}: rebuilding basis_triangulation moved {len(moved)} line(s) "
                f"{[a[i][:48] for i in moved]} — expected only the covenant-basis line")
        if not moved:
            return out
        out["primary_source"]["basis_triangulation"] = {**node, "value": rebuilt}
        return out

    return _apply


def credit_health_transform(ticker: str) -> Transform:
    """A `refresh_dossier` transform writing `mech.leverage_survival.credit_health_panels` — both
    relative credit-health panels, each naming its peer group, under a KEPT synthesis.

    WHY A TRANSFORM: the panels are deterministic reads of two CIQ exports, so re-assembling to land
    them would re-draw every synthesis — a variance event per name spent on a table.

    THE COMPS PANEL DESCRIBES THE STORED NUMBERS OR IS WITHHELD (the `ev_gap_transform` lesson). The
    page already carries a comps reading as prose (`credit_health`), extracted at assembly. The
    comps export may have been re-pulled since, so the panel is built only when today's comps
    reading is the SAME as the stored one — and then it carries the stored citation, as-of and all.
    When they differ the panel is withheld with a note, never published beside prose it
    contradicts. The industry panel is new data with nothing stored to contradict.

    A FOLDER THAT CANNOT BE READ LEAVES THE PAGE ALONE: no exports on this machine is not evidence
    that the name has no panel, so nothing is written."""
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import INDUSTRY_CREDIT_REF, credit_health, credit_health_panels
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.schemas import CreditHealthPanel, Sourced

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        lv = out.get("leverage_survival")
        if not isinstance(lv, dict):
            return out                  # a pre-B2 page has no leverage block to extend
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return out
        built = credit_health_panels(bundle)
        if built is None:
            return out
        stored = lv.get("credit_health") or {}
        today = credit_health(bundle)
        panels: list[CreditHealthPanel] = list(built.value or [])
        notes = [built.note] if built.note else []
        if any(p.population_kind == "comps" for p in panels) and today.value != stored.get("value"):
            panels = [p for p in panels if p.population_kind != "comps"]
            notes.append("comps panel withheld: the comps export changed since this page was "
                         "assembled — re-assemble to refresh it")
        if not panels:
            return out
        refs = ([INDUSTRY_CREDIT_REF] if any(p.population_kind == "industry" for p in panels)
                else [])
        if any(p.population_kind == "comps" for p in panels) and stored.get("source_ref"):
            refs.append(str(stored["source_ref"]))
        lv["credit_health_panels"] = json.loads(Sourced.present(
            panels, source_ref=" · ".join(refs), note="; ".join(notes) or None).model_dump_json())
        return out

    return _apply


def forward_consensus_transform(ticker: str) -> TopLevelTransform:
    """A `refresh_dossier` top-level step writing `forward_consensus` — FY+0..FY+2 paths, spreads
    and revision counts — from the on-disk Estimates export, under a KEPT synthesis.

    WHY A REFRESH: the layer is a deterministic read of one CIQ export, so re-assembling to land it
    would re-draw every synthesis — a variance event per name spent on a table. It lives OUTSIDE
    `mechanical`, so the synthesis never saw it and nothing the prose cites can move.

    A FOLDER THAT CANNOT BE READ LEAVES THE PAGE ALONE: no export on this machine is not evidence
    that the name has no consensus, so nothing is written (the `credit_health_transform` rule)."""
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import forward_consensus
    from vinci.dossier.manual_store import LocalFolderStore

    def _apply(doc: dict[str, Any]) -> dict[str, Any]:
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return {}
        built = forward_consensus(bundle)
        return {} if built is None else {"forward_consensus": json.loads(built.model_dump_json())}

    return _apply


def forward_multiple_history_transform(ticker: str) -> TopLevelTransform:
    """A `refresh_dossier` top-level step writing `forward_multiple_history` — the forward
    multiples' quarterly history — from the on-disk Financials export, under a KEPT synthesis.

    ONLY FROM THE EXPORT THE PAGE WAS BUILT FROM. The page's trailing own-history bands stamp the
    sha256 of the Financials file they were read from; the layer is written only when that stamp is
    the file on disk. A page whose bands carry no stamp cannot say which export it came from, so it
    is left alone and its layer waits for a re-assembly — on 2026-10-07 that is FUBO, ORKA and TECX,
    which have no trailing band. FUBO's and ORKA's hash also sits inside a display string; reading
    it from there would be the parse-the-rendered-string class this repo forbids.

    A FOLDER THAT CANNOT BE READ LEAVES THE PAGE ALONE (the `credit_health_transform` rule)."""
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import forward_multiple_history
    from vinci.dossier.manual_store import LocalFolderStore

    def _apply(doc: dict[str, Any]) -> dict[str, Any]:
        valuation = (doc.get("mechanical") or {}).get("valuation") or {}
        bands = (valuation.get("own_history") or {}).get("value") or []
        stamps = {b.get("source_sha256") for b in bands if isinstance(b, dict)}
        if len(stamps) != 1 or None in stamps:
            return {}               # no single stamped export behind the page: re-assemble instead
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return {}
        built = forward_multiple_history(bundle)
        if built is None or built.source_sha256 not in stamps:
            return {}               # the export on disk is not the page's: re-assemble instead
        return {"forward_multiple_history": json.loads(built.model_dump_json())}

    return _apply


def ev_bridge_transform(ticker: str) -> TopLevelTransform:
    """A `refresh_dossier` top-level step writing `ev_bridge` — CIQ's TEV claims and the exit
    default an enterprise recipe subtracts — under a KEPT synthesis.

    ONLY FROM THE EXPORTS THE PAGE WAS BUILT FROM, BOTH OF THEM. The claims come off the Financials
    export, which the page's trailing own-history bands stamp; the consensus check reads the
    Estimates export the page's `forward_consensus` names by hash. A page that cannot name either,
    or names another, is left alone and waits for a re-assembly. The EDGAR cross-check is
    lease-INCLUSIVE, as CIQ's claims are: the anchor's figure where its bridge is, EDGAR's own
    where the anchor prices ex-lease (review of #750). A folder that cannot be read leaves the page
    alone too (the `credit_health_transform` rule)."""
    from vinci.config import get_config
    from vinci.dossier.anchor import NET_DEBT_EX_LEASE, lease_inclusive_net_debt
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import ev_bridge
    from vinci.dossier.manual_store import LocalFolderStore

    def _apply(doc: dict[str, Any]) -> dict[str, Any]:
        valuation = (doc.get("mechanical") or {}).get("valuation") or {}
        bands = (valuation.get("own_history") or {}).get("value") or []
        stamps = {b.get("source_sha256") for b in bands if isinstance(b, dict)}
        fc = doc.get("forward_consensus") or {}
        if len(stamps) != 1 or None in stamps or not fc.get("source_sha256"):
            return {}               # the page cannot name both exports: re-assemble instead
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return {}
        # THE CROSS-CHECK IS LEASE-INCLUSIVE (review of #750): the anchor's figure where its
        # bridge is, EDGAR's lease-inclusive figure where the anchor prices ex-lease
        nd = (doc.get("anchor") or {}).get("net_debt") or {}
        edgar_nd: tuple[Any, Any] = (nd.get("value"), nd.get("source"))
        if nd.get("basis") == NET_DEBT_EX_LEASE:
            from vinci.edgar.client import EdgarClient
            edgar_nd = lease_inclusive_net_debt(
                EdgarClient.from_config(get_config()).companyfacts(str(doc.get("cik"))))
        built = ev_bridge(bundle, fy_periods=list(fc.get("periods") or []),
                          edgar_net_debt=edgar_nd[0], edgar_source=edgar_nd[1])
        if (built is None or built.source_sha256 not in stamps
                or built.estimates_sha256 != fc.get("source_sha256")):
            return {}               # an export on disk is not the page's: re-assemble instead
        return {"ev_bridge": json.loads(built.model_dump_json())}

    return _apply


def historical_forecast_error_transform(ticker: str) -> TopLevelTransform:
    """A `refresh_dossier` top-level step writing `historical_forecast_error` — the final
    consensus's miss per completed fiscal year — from the on-disk Estimates export, under a KEPT
    synthesis.

    ONLY FROM THE EXPORT THE PAGE WAS BUILT FROM. The page's `forward_consensus` names its Estimates
    export: by hash where the page carries one, else by the export's as-of. A page that names
    neither, or names another export, is left alone. A folder that cannot be read leaves the page
    alone too (the `credit_health_transform` rule)."""
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import estimates_as_of, file_provenance, historical_forecast_error
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.schemas import SourceStatus

    def _apply(doc: dict[str, Any]) -> dict[str, Any]:
        fc = doc.get("forward_consensus") or {}
        if not fc.get("source_sha256") and not fc.get("as_of"):
            return {}
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return {}
        wb = bundle.workbook("estimates")
        if wb is None:
            return {}
        if fc.get("source_sha256"):
            if file_provenance(wb.path)[0] != fc["source_sha256"]:
                return {}       # another export than the page's: re-assemble instead
        else:
            as_of = estimates_as_of(bundle)
            if as_of.status is not SourceStatus.PRESENT or as_of.value != fc["as_of"]:
                return {}
        built = historical_forecast_error(bundle)
        return ({} if built is None
                else {"historical_forecast_error": json.loads(built.model_dump_json())})

    return _apply


def horizon_read_transform(ticker: str) -> Transform:
    """A `refresh_dossier` transform correcting `catalyst_path.horizon_read`: the revision counts a
    mis-bounded Revisions read took from the wrong block (STATE §5.0 row 30 (A)).

    THE CORRECTION MOVES ONLY WHAT THE BUG TOUCHED, OR NOTHING. The stored string is rebuilt from
    the on-disk export under the bounding that wrote it (`horizon_read_as_assembled`), and the field
    is replaced only when that rebuild is byte-identical — proof the page came from THIS export. Any
    difference means the export was re-pulled or the renderer has moved since; the page is left
    alone and the name needs a re-assembly instead.

    UNDER A KEPT SYNTHESIS. A count the prose cites and the page no longer carries refuses the
    refresh (`moved_cited_counts`), the same rule `moved_cited_claims` applies to money."""
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import horizon_read, horizon_read_as_assembled
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.schemas import SourceStatus

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        cp = out.get("catalyst_path")
        hr = cp.get("horizon_read") if isinstance(cp, dict) else None
        if not isinstance(cp, dict) or not isinstance(hr, dict) or not hr.get("value"):
            return out
        try:
            bundle = CiqBundle.from_files(
                ticker, LocalFolderStore.from_config(get_config()).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return out
        as_of = (cp.get("as_of") or {}).get("value")
        if horizon_read_as_assembled(bundle, as_of=as_of) != hr["value"]:
            return out          # not this export, or not this renderer: re-assemble instead
        fixed = horizon_read(bundle, as_of=as_of)
        if fixed.status is SourceStatus.PRESENT and fixed.value:
            hr["value"] = fixed.value
        return out

    return _apply


def lease_basis_transform(ticker: str, cik: str | None) -> Transform:
    """A `refresh_dossier` transform writing `mech.valuation.lease_basis` — whether rent is
    material and, where it is, the ex-lease EV/EBITDA history R1 prices on (2026-10-19) — under a
    KEPT synthesis. Run `anchor-backfill` after it: the anchor reads this block.

    ONLY FROM THE EXPORT THE PAGE'S HISTORY WAS BUILT FROM. The block reads the same quarterly
    export as `own_history`, so it is written only when that export's hash is the one the page's
    bands carry; a page built from another pull is left alone (re-assemble or run
    `own-history-refresh`, which moves the whole cluster together). A folder that cannot be read
    leaves the page alone too (the `credit_health_transform` rule).

    NO CITED FIGURE MOVES: the block is a new key. The page's basis line reads the ANCHOR, so until
    `anchor-backfill` re-derives it the line says the anchor predates the page's lease basis, and
    the valuation-basis block lists that as a conflict — the half-done pass is visible, never a
    page claiming a pricing its anchor does not do."""
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import file_provenance
    from vinci.dossier.lease_basis import lease_basis
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.edgar.client import EdgarClient

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        val = out.get("valuation")
        if not isinstance(val, dict) or not cik:
            return out
        bands = (val.get("own_history") or {}).get("value") or []
        stamps = {b.get("source_sha256") for b in bands if isinstance(b, dict)}
        if len(stamps) != 1 or None in stamps:
            return out              # the page cannot name its export: re-assemble instead
        cfg = get_config()
        try:
            bundle = CiqBundle.from_files(ticker, LocalFolderStore.from_config(cfg).files(ticker))
        except (FileNotFoundError, CiqUnavailableError):
            return out
        wb = bundle.workbook("financials", freq="quarterly")
        if wb is None or file_provenance(wb.path)[0] not in stamps:
            return out              # the export on disk is not the page's: re-assemble instead
        built = lease_basis(bundle, EdgarClient.from_config(cfg).companyfacts(cik))
        if built is not None:
            val["lease_basis"] = json.loads(built.model_dump_json())
        return out

    return _apply


def valuation_bases_transform(ticker: str, cik: str | None) -> Transform:
    """A `refresh_dossier` transform writing the three basis blocks of 2026-10-21 under a KEPT
    synthesis, through the assembler's own builder (`mechanical.with_valuation_bases`):
    `valuation.ev_ebitda_basis` (what CIQ's headline multiple divides, measured),
    `valuation.ev_ebitda_ex_lease_at_price` (R1's basis at the page's price) and
    `financial_summary.ebitda_reconciliation` (CIQ's EBITDA against the filings). It also renames
    the triangulation's two CIQ rows, which called CIQ's EBITDA "GAAP basis".

    NEW KEYS AND A RELABEL; NO STORED FIGURE MOVES. The reconciliation reads the quarterly CIQ
    export, so it is written only when that export is the one the page's bands were built from (the
    `lease_basis_transform` rule) — otherwise the other two still land and it stays absent."""
    from vinci.config import get_config
    from vinci.dossier import mechanical as dm
    from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
    from vinci.dossier.ciq_sheets import file_provenance
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.schemas import MechanicalLayer
    from vinci.edgar.client import EdgarClient
    from vinci.edgar.primary_source import OLD_TRIANGULATION_LABELS
    from vinci.sec import build_sec_http

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        if not isinstance(out.get("valuation"), dict) or not cik:
            return out
        cfg = get_config()
        facts = EdgarClient.from_config(cfg).companyfacts(cik)
        bundle: CiqBundle | None = None
        bands = ((out["valuation"].get("own_history") or {}).get("value")) or []
        stamps = {b.get("source_sha256") for b in bands if isinstance(b, dict)}
        try:
            cand = CiqBundle.from_files(ticker, LocalFolderStore.from_config(cfg).files(ticker))
            wb = cand.workbook("financials", freq="quarterly")
            if (wb is not None and len(stamps) == 1 and None not in stamps
                    and file_provenance(wb.path)[0] in stamps):
                bundle = cand
        except (FileNotFoundError, CiqUnavailableError):
            bundle = None
        # REBUILT, NEVER CARRIED: a block the builder no longer writes must not survive the refresh
        # (and a block in an older shape must not fail the validation below). The reconciliation is
        # dropped only when it is rebuilt — without the page's own export, the one built from it at
        # assembly stands.
        for key in ("ev_ebitda_basis", "ev_ebitda_ex_lease_at_price"):
            out["valuation"].pop(key, None)
        if bundle is not None and isinstance(out.get("financial_summary"), dict):
            out["financial_summary"].pop("ebitda_reconciliation", None)
        built = dm.with_valuation_bases(MechanicalLayer.model_validate(out), facts, bundle,
                                        text_for=dm.release_text_fn(build_sec_http(cfg), cik))
        for key in ("ev_ebitda_basis", "ev_ebitda_ex_lease_at_price"):
            v = getattr(built.valuation, key)
            if v is not None:
                out["valuation"][key] = json.loads(v.model_dump_json())
        fs = built.financial_summary
        if fs is not None and fs.ebitda_reconciliation is not None:
            out["financial_summary"]["ebitda_reconciliation"] = json.loads(
                fs.ebitda_reconciliation.model_dump_json())
        node = (out.get("primary_source") or {}).get("basis_triangulation") or {}
        text = node.get("value")
        if isinstance(text, str):
            for old, new in OLD_TRIANGULATION_LABELS:
                text = text.replace(old, new)
            node["value"] = text
        return out

    return _apply


def leverage_caveat_transform() -> TopLevelTransform:
    """A top-level step REGENERATING the leverage caveat from the page's stored ratio — the one
    caveat that called CIQ's EBITDA "(CIQ / consolidated GAAP)" (2026-10-21). Rebuilt through the
    assembler's own `_leverage_basis_flag`, never string-edited, and REFUSED unless exactly that one
    caveat moves: the seam that admits `caveats` must not carry any other change."""
    from vinci.dossier import mechanical as dm
    from vinci.dossier.schemas import Sourced

    def _apply(doc: dict[str, Any]) -> dict[str, Any]:
        cav = list(doc.get("caveats") or [])
        old = [i for i, c in enumerate(cav) if isinstance(c, str)
               and c.startswith("Net debt/EBITDA (") and "(CIQ / consolidated GAAP)" in c]
        if not old:
            return {}
        raw = ((doc.get("mechanical") or {}).get("quality") or {}).get("net_debt_to_ebitda")
        fresh = dm._leverage_basis_flag(Sourced[float].model_validate(raw)) if raw else None
        if fresh is None or len(old) != 1:
            raise ValueError(f"{doc.get('ticker')}: the leverage caveat cannot be regenerated "
                             f"from the stored ratio ({len(old)} candidate(s)) — re-assemble")
        cav[old[0]] = fresh
        return {"caveats": cav}

    return _apply


def ebitda_basis_transform() -> Transform:
    """A `refresh_dossier` transform writing `mech.financial_summary.ebitda_basis`.

    THE PUREST TRANSFORM SO FAR, and that is the point: `ev_gap_transform` opens CIQ workbooks and
    `capital_allocation_transform` calls EDGAR, but this one reads NOTHING outside the stored JSON.
    The annual table already carries `EBITDA ($M)` and `EBIT ($M)` per column plus `is_estimate`,
    so the implied-D&A comparison is a function of the artifact itself. Nothing can fail to fetch,
    so unlike the capital-allocation transform there is no write-nothing branch to reason about.

    WHY A TRANSFORM AND NOT A RE-ASSEMBLY, restated because the arithmetic changed: six committed
    names carry an actual-vs-estimate EBITDA step and none of their pages says so. Re-assembling
    them to land a DETERMINISTIC block would reroll six syntheses — six variance events spent on a
    number that was already sitting in the file. `refresh_dossier` exists precisely so a value can
    move under a KEPT synthesis.

    ALWAYS WRITES (the `ev_gap_transform` / capital-allocation rule): `read_basis` states a reason
    in every branch including the un-computable ones, so a written block always says something, and
    ABSENT keeps its distinct meaning of NOT YET REFRESHED.

    NO REFUSAL RISK BY CONSTRUCTION — the block is a new key, so no committed synthesis can cite a
    figure it moves and `moved_cited_claims` has nothing to find. A property of being additive, not
    a licence for the next transform.
    """
    from vinci.dossier.ebitda_basis import read_basis
    from vinci.dossier.schemas import FinTable

    def _apply(mech: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(json.dumps(mech))
        fs = out.get("financial_summary")
        if not isinstance(fs, dict):
            return out          # no appendix on this build — nothing to describe
        ann = fs.get("annual")
        raw = ann.get("value") if isinstance(ann, dict) else None
        # VALIDATED THROUGH THE REAL TYPE, never read as a bare dict: `read_basis` takes a FinTable
        # and a hand-walked dict here would be a second reader of the same shape — the twin-drift
        # class, one artifact over.
        table = FinTable.model_validate(raw) if isinstance(raw, dict) else None
        fs["ebitda_basis"] = json.loads(read_basis(table).model_dump_json())
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
        # THE YEAR THE LEG IS STRUCK AT, carried so `build_ev_gap` can check it against the year it
        # decomposes on. None on every record written before 2026-08-05 — UNSTATED, which is a
        # different state from disagreeing and is reported as one.
        "leg_fy": base.leg_fy,
        "d_and_a": fact("d_and_a"),
        "shares": fact("diluted_shares"),
        # CARRIED SO THE TOTAL GAP CAN BE STRUCK. Converting OUR OWN D&A share crosses no horizon;
        # only the comparison to a near-term consensus margin does, and that is suppressed
        # separately (operator, revised 2026-08-03).
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


def mirror_to_frontend() -> None:
    """Re-run the frontend mirror — the LAST step of any pass that touches `data/dossiers`.

    WIRED IN BECAUSE A MANUAL STEP IN THE DELIVERY PATH IS ONE FORGETTING FROM A STALE PAGE, and
    the repo has the receipt: FUBO's `dossier.md` carried a 22-line "⚠ KNOWN-WRONG — do not read
    the figures on this page as current" banner while `frontend/dossiers/FUBO.md` — **the page
    actually served** — did not. The suite compared only the SET of mirrored names, so the warning
    could go missing and stay missing.

    #319's byte-identity pin made forgetting LOUD; this makes it unnecessary. Both stay: the pin
    still catches a mirror written by some other route.

    Imported inside the function — `frontend/build.py` is a script at the repo root, not part of
    the `vinci` package, so a module-scope import would couple the library to the build tree.
    """
    import importlib.util
    import sys

    # CWD, the same root  uses. Every caller already runs from the repo root (the
    # CLI, the pass, the suite), and inventing a second root convention here would be the
    # duplicate-definition class in path form.
    script = Path.cwd() / "frontend" / "build.py"
    if not script.exists():                      # a checkout without the frontend tree is legal
        return
    spec = importlib.util.spec_from_file_location("_vinci_frontend_build", script)
    if spec is None or spec.loader is None:      # pragma: no cover - import machinery
        raise RuntimeError(f"cannot load the frontend mirror from {script}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.main([])


def refresh_fleet(
    root: Path | None = None, *, transform_for: Callable[[str], Transform] | None = None,
) -> dict[str, list[str]]:
    """Refresh every committed dossier, then mirror to the frontend ONCE. The pass orchestrator.

    THIS IS WHERE `mirror_to_frontend` IS CALLED, and the review of #321 is why it exists: the
    function was defined and never invoked, so the "wired in" claim was false and the
    `data/dossiers` -> `frontend/dossiers` drift it was meant to close stayed open. A helper nobody
    calls is not a fix; it is a fix-shaped object.

    ONCE, AFTER ALL OF THEM — not per dossier. The mirror rebuilds the whole `frontend/` tree from
    every source each time, so calling it per name would do N passes to produce the state the last
    one produces anyway, and would leave the tree briefly reflecting a half-refreshed fleet.

    SEALED NAMES ARE REPORTED, NOT SWALLOWED. `refresh_dossier` refuses a record carrying a
    `known_wrong.json`; that refusal is a RESULT of the pass, so it comes back in the summary
    rather than vanishing into a log line.
    """
    base = (root or Path.cwd()) / "data" / "dossiers"
    out: dict[str, list[str]] = {"moved": [], "unchanged": [], "refused": []}
    for folder in sorted(base.iterdir()) if base.is_dir() else []:
        path = folder / "dossier.json"
        if not path.exists():
            continue
        try:
            changed = refresh_dossier(
                path, transform=transform_for(folder.name) if transform_for else None)
        except RefreshRefusedError:
            out["refused"].append(folder.name)
            continue
        out["moved" if changed else "unchanged"].append(folder.name)
    # UNCONDITIONAL. Even a pass that moved nothing re-mirrors: the mirror can be stale from a
    # PREVIOUS pass that forgot, and refusing to fix that because this pass was a no-op would make
    # the guarantee depend on which run you happened to notice it in.
    mirror_to_frontend()
    return out
