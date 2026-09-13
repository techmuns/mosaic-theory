"""(phase 6) THE EMITTER — panel decisions onto the monitor-day artifact, as structured rows.

This is the consumer phases 2–4 did not have. The spec, the gating rule, the declarations and the
computations all existed and nothing read them: `cli.py` still said "panel routing (planned)" and
no frontend file mentioned a panel. This module closes that, and it is the ONLY producer of the
`panels` block — the frontend mirrors `data/monitor/*.json` verbatim and renders from it.

WHAT IT REFUSES TO CARRY. No markup, no formatted number, no pre-rendered label: only values and
the decision. Display formatting is never load-bearing here, so the renderer can change how a
figure reads without the artifact changing what it says.

THE GATING RULE SURVIVES SERIALIZATION, which is the one thing that could quietly undo three
phases. A `not_in_set` panel EMITS NO ROW AT ALL — it is absent from the block, not present with a
falsy state — because a row saying "this does not apply" is a tile waiting to be rendered, and the
rule is that those never render. A `refused` row is present and carries its reason. The two are
therefore distinguishable in the JSON by a reader who has never seen this code.
"""
from __future__ import annotations

from datetime import date as _date
from typing import Any

from pydantic import BaseModel, Field

from vinci import panels_payload as pay
from vinci.panels import PanelDecision, PanelRegistry, default_registry
from vinci.panels_declare import read_declarations
from vinci.panels_resolve import resolve_cohort, resolve_universal, select_row
from vinci.panels_theme import resolve_theme, theme_registry
from vinci.panels_universal import universal_registry


class PanelRow(BaseModel):
    """One panel, for one name, on one monitor day.

    `state` is only ever "ready" or "refused" — see the module note on why `not_in_set` emits
    nothing. A reader can rely on that: every row in the block is a tile that renders.
    """

    ticker: str
    key: str
    tier: str
    title: str
    state: str
    #: The face-validity guard, carried to the surface rather than left in the code: every tile
    #: prints what would change the call.
    changes_the_call: str
    caveat: str = ""
    cadence: str = "event"
    #: REFUSED only — the requirement(s) that failed and the upstream words, verbatim.
    missing: list[dict[str, str]] = Field(default_factory=list)
    reason: str = ""
    #: READY only — structured values; shapes documented in `vinci/panels_payload`.
    value: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    #: The name's own RENDER config, resolved. Empty when the name declared none — and the renderer
    #: must then say nothing about it rather than assume a default, which is the whole point of the
    #: field: a panel that claims an axis for a name that never declared one is back to stating one
    #: position's archetype as universal.
    render_config: dict[str, str] = Field(default_factory=dict)


def _row(dec: PanelDecision, *, ticker: str, registry: PanelRegistry,
         value: dict[str, Any] | None, sources: list[str] | None,
         no_value_reason: str = "",
         render_config: dict[str, str] | None = None) -> PanelRow | None:
    """A decision → a row, or None for `not_in_set`.

    `no_value_reason` is the BUILDER'S OWN account of why it produced nothing, when it has one. A
    builder that knows the cause must not have it replaced by the generic wiring-bug sentence below:
    that sentence asserts a code defect, and asserting one about a name whose disclosure genuinely
    cannot be priced is a fabricated cause on a reader-facing refusal.
    """
    if dec.state == "not_in_set":
        return None
    spec = registry.get(dec.key)
    assert spec is not None  # decide() already refused an unregistered key, loudly
    # A READY panel with no value is a CONTRADICTION — the requirements said the data is there.
    # Demoting it to a refusal that says so is the honest outcome; rendering an empty ready tile is
    # the blank tile the gating rule exists to prevent.
    state, reason = dec.state, dec.reason
    if state == "ready" and not value:
        state = "refused"
        reason = no_value_reason or (
            f"every requirement for {dec.key!r} resolved, yet no value could be built from "
            f"the committed artifacts — the requirement check and the payload builder "
            f"disagree, which is a wiring bug rather than missing disclosure")
    return PanelRow(
        ticker=ticker, key=dec.key, tier=spec.tier, title=spec.title, state=state,
        changes_the_call=spec.changes_the_call, caveat=spec.caveat, cadence=spec.cadence,
        missing=[{"kind": r.kind, "detail": r.detail, "why": r.why} for r in dec.missing],
        reason=reason, value=value or {}, sources=sources or [],
        render_config=render_config or {},
    )


def panel_rows_for(
    ticker: str,
    *,
    dossier: dict[str, Any] | None,
    row: dict[str, Any] | None,
    freshness: dict[str, Any] | None,
    record: dict[str, Any] | None,
    declarations: dict[str, dict[str, dict[str, str]]],
    row_absence_reason: str = "",
) -> list[PanelRow]:
    """Every renderable panel for one name — universal seven first, then declared cohort panels.

    `row_absence_reason` is `select_row`'s own account of WHY there is no single live row, when the
    reason is something other than "this name has no rows". It must travel: a name with two OPEN
    decisions has rows, and a refusal telling the reader the position is "invisible to the book" is
    false about the one fact the reader would act on.
    """
    m = (dossier or {}).get("mechanical") or {}
    ureg = universal_registry()
    creg = default_registry()
    out: list[PanelRow] = []

    builders: dict[str, tuple[dict[str, Any] | None, list[str]]] = {}
    #: Per-key cause for an empty payload, when the builder knows it. See `_row`.
    why_empty: dict[str, str] = {}
    if row:
        builders["the_call"] = (pay.the_call(row), [
            f"monitor snapshot row · entry {row.get('entry_date')} · benchmark "
            f"{row.get('benchmark')} (cap band, assigned at entry)"])
        builders["attribution"] = (pay.attribution(row), [
            "Polygon daily closes, price return both sides (dividends excluded on the position "
            "AND the benchmark alike)"])
    val = m.get("valuation") or {}
    if val:
        # THE NAME'S DECLARED BASIS reaches the payload builder, not just the renderer: which
        # metric to read is a selection, and selections happen before markup. Undeclared, the
        # builder uses the repo default and stamps the payload so the tile can say which.
        _mp_cfg = (declarations.get(ticker) or {}).get("multiple_and_price") or {}
        _want = _mp_cfg.get("valuation_metric")
        try:
            mp = pay.multiple_and_price(val, metric=_want)
        except pay.MetricNotFoundError as exc:
            # A DECLARED METRIC THAT IS NOT THERE IS A LOUD REFUSAL, never a substitution: showing
            # a different multiple under a heading the name chose is the defect this replaced.
            mp = None
            why_empty["multiple_and_price"] = str(exc)
        # The payload's OWN citation, not one picked per metric by the caller.
        builders["multiple_and_price"] = (mp, [str((mp or {}).get("source_ref") or "")])
    if freshness:
        builders["filing_watch"] = (pay.filing_watch(freshness), [
            f"last evidence via {freshness.get('last_evidence_source')}",
            str(freshness.get("next_expected_basis") or "")])
        builders["kills"] = (pay.kills(freshness, record), ["scenario record measured_triggers"])
    dil = m.get("dilution_pipeline") or {}
    if dil:
        _dil = pay.dilution(dil)
        # The assembler's own sentence is PROVENANCE, not body text — it names the form codes the
        # tile now translates, and its dates travel structurally above.
        builders["dilution"] = (_dil, [
            str((dil.get("line") or {}).get("source_ref") or ""),
            str(_dil.get("line") or "")])
    cs = m.get("capital_structure") or {}
    if cs:
        cob, cob_why = pay.cost_of_borrowing(cs)
        builders["cost_of_borrowing"] = (cob, [
            str((cs.get("instruments") or {}).get("source_ref") or "")])
        if cob_why:
            why_empty["cost_of_borrowing"] = cob_why

    # SOURCES IS BUILT LAST, because it describes the panels above it. Deferring one decision out
    # of the loop is the price of the tile's title being true: a provenance tile assembled from a
    # dossier section it does not share with any other panel is how the first cut came to cite four
    # filings that sourced nothing on the page.
    deferred: PanelDecision | None = None
    for dec in resolve_universal(
        dossier=dossier, row=row, freshness=freshness, record=record, registry=ureg,
    ):
        if dec.key == "sources":
            deferred = dec
            continue
        v, src = builders.get(dec.key, (None, []))
        # THE NAME'S OWN RENDER CONFIG, resolved here so the renderer needs no second lookup. Only
        # keys the SPEC declares are carried: a stray key in `followed.json` is already refused at
        # read, and this keeps a later one from riding through as if the panel understood it.
        uspec = ureg.get(dec.key)
        declared_cfg = (declarations.get(ticker) or {}).get(dec.key) or {}
        rc = {k: str(declared_cfg[k]) for k in (uspec.render_config if uspec else {})
              if k in declared_cfg}
        r = _row(dec, ticker=ticker, registry=ureg, value=v, sources=src,
                 no_value_reason=why_empty.get(dec.key, ""), render_config=rc)
        if r is not None:
            out.append(r)

    # COHORT PANELS RUN WITHOUT A NOTE PROBE HERE, deliberately. The monitor run is offline by
    # contract (`emit_monitor`: "the browser must not be able to show a mark the repo cannot
    # reproduce"), so an R-file note's presence is unknown and those panels refuse, naming the
    # absent probe. `cost_of_borrowing` needs no filing and resolves normally.
    for dec in resolve_cohort(
        ticker, dossier=dossier, declarations=declarations, registry=creg, note_probe=None,
    ):
        v, src = builders.get(dec.key, (None, []))
        r = _row(dec, ticker=ticker, registry=creg, value=v, sources=src,
                 no_value_reason=why_empty.get(dec.key, ""))
        if r is not None:
            out.append(r)

    # ...and now the sources tile, from what the page above it actually cites. A panel that
    # REFUSED cites nothing, so it contributes nothing — the tile indexes the numbers on show, not
    # the ones that could not be built.
    if deferred is not None:
        cited = [(r.key, r.title, list(r.sources)) for r in out
                 if r.state == "ready" and r.sources]
        payload = pay.sources(cited)
        r = _row(deferred, ticker=ticker, registry=ureg, value=payload, sources=[],
                 no_value_reason=(
                     "no panel on this page cites a source, so there is no provenance to index — "
                     "which means every figure above is either refused or unsourced"))
        if r is not None:
            out.append(r)
    # THE AMBIGUITY REASON TRAVELS, appended rather than substituted: the requirement's own `why`
    # still says which field was wanted, and this says why no row could supply it. Only rows that
    # refused FOR WANT OF A ROW are touched.
    if row is None and row_absence_reason:
        for r in out:
            if r.state == "refused" and any(
                    mi.get("kind") in ("ledger_row", "snapshot_field") for mi in r.missing):
                r.reason = f"{r.reason} {row_absence_reason}".strip()
    return out


def theme_panel_rows(
    *,
    driver_keys: list[str],
    declared_cards: set[str],
    theme_falsifiers: list[dict[str, Any]],
    today: _date,
) -> list[PanelRow]:
    """Theme panels, keyed by DRIVER rather than by ticker.

    `ticker` carries the `driver_key` — the tier's whole point is that a theme panel attaches to the
    driver, not the name, so the row's subject is the driver and the renderer groups on it. Named
    `ticker` because `PanelRow` is one shape for every tier and a second identity field would let a
    consumer read the wrong one.
    """
    reg = theme_registry()
    out: list[PanelRow] = []
    for key, dec, payload in resolve_theme(
        driver_keys, declared_cards=declared_cards,
        theme_falsifiers=theme_falsifiers, today=today, registry=reg,
    ):
        # The driver key is in hand, so the citation names the FILE a reader can open. A literal
        # "<driver>.json" in a sources list is a placeholder that reads as provenance.
        r = _row(dec, ticker=key, registry=reg, value=payload,
                 sources=[f"data/themes/thesis/{key}.json — the operator's declared card"]
                 if payload else [])
        if r is not None:
            out.append(r)
    return out


def emit_panels(
    *,
    rows: list[dict[str, Any]],
    freshness: list[dict[str, Any]],
    dossier_for: Any,
    record_for: Any,
    root: Any = None,
) -> list[PanelRow]:
    """Every panel row for every name the book or the follow list knows about.

    THE NAME SET IS THE UNION, not the snapshot's rows. A followed name with no ledger row still
    has panels — GOOGL had none in the 2026-08-11 snapshot while carrying a live position — and
    taking only `rows` would have made the grid invisible for exactly the names it was built for.
    """
    # EVERY TIER, not the cohort one — the file describes a name's whole grid.
    decl = read_declarations(root=root)
    fresh = {str(f.get("ticker")): f for f in freshness}
    row_tickers = {str(r.get("ticker")) for r in rows}
    out: list[PanelRow] = []
    for ticker in sorted(row_tickers | set(fresh) | set(decl)):
        sel, ambiguous = select_row(rows, ticker)
        out.extend(panel_rows_for(
            ticker,
            dossier=dossier_for(ticker), row=sel, freshness=fresh.get(ticker),
            record=record_for(ticker), declarations=decl, row_absence_reason=ambiguous,
        ))
    return out
