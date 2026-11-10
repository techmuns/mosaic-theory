"""Variant transforms — how a change to the MECHANICAL layer's words reaches a replay.

The replay reads a committed mechanical layer, so a change to a label ``mechanical.py`` writes
(fix 3a) does not reach the request by itself. A transform re-reads such a field from the code
version UNDER TEST. This file is loaded BY PATH in the capture child (`capture_child.py
--transform NAME`), so ``vinci.dossier.*`` below is the extracted ref's own code: the same
transform is the identity at main and the branch's wording at the branch. It imports nothing
from ``vinci.evals`` for that reason.

A transform must change ONLY the fields its change rewrites, from facts already on the page, and
its PR shows at $0 that the result equals what the candidate's own builder writes for those fields
(RUNBOOKS §n step 2). Each one takes the layer and a `Context` — the committed page it came from,
and the page's own comps export where one was given — and FAILS LOUD (`TransformError`) rather
than guess: a field it cannot regenerate from the ref's code and the page's facts is never written.

FIX 3A (#923) rewrites five labels; `FIX_3A` names the five transforms, in the order applied:

1. ``relabel_drawdown_shape`` — the no-gap-down shape (`mechanical._CURRENT_WORDS.none_shape`);
2. ``trailing_only_note`` — the trailing EV/EBITDA's note (`mechanical.ev_ebitda_note`);
3. ``survival_read`` — the survival line (`mechanical._survival_capacity`);
4. ``peer_gap_question`` — the peer-delta question (`ciq_sheets._comps_deltas`);
5. ``print_row_guide`` — the catalyst print row (`mechanical._catalyst_calendar`).

Items 2 and 4 read the comps sheet (the name's NTM cells; every peer's six multiples), which the
page does not carry. They read the page's OWN export only: before using it, the ref's code must
rebuild the page's committed `valuation.cross_sectional` and `peer_comps.trading_multiples` from
it byte for byte, or the transform refuses (#923 found four pages whose export on its disk was not
their own).

FIX 4A writes one new field, `FIX_4A`'s ``gap_types``: `disclosure_gaps` (the gap test,
`vinci.dossier.gaps`), from the layer and the segment count its committed segments line states.

FIX 3B rewrites two fields; `FIX_3B` names their transforms:

1. ``survival_read`` — the survival line, which loses its one-input self-funding leg (the
   transform fix 3a's item 3 already applies: it reads THIS ref's `_survival_capacity`);
2. ``current_buybacks`` — the three buyback fields, a leg more than a year before the page's
   price date no longer stated (`capital_allocation.buyback_legs`).

RG-D8 (fix request 2), `RG_D8`'s ``driver_facts``: the transcript driver rows' fact check,
re-run on each committed row's own metric, value and quote (`driver_extract.check_fact`).

THE AS-OF CUT (STATE row 57), `ASOF_CUT`'s ``asof_cut``: a page built before the cut keeps the
releases filed after its price date; this moves them out of `primary_source.releases` and
re-derives the two fields the assembly takes from that list (`current_guide`, a release-read
`adjusted_eps`). It refuses wherever it cannot write what a builder at the cut would.
"""
from __future__ import annotations

import inspect
import math
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace
from typing import Any

from vinci.dossier import capital_allocation, ciq_sheets, gaps, mechanical
from vinci.dossier import schemas as _schemas
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import ForwardMultipleHistory, MechanicalLayer, Sourced, SourceStatus
from vinci.edgar.concepts import ConceptPoint

PRESENT = SourceStatus.PRESENT

#: The source label `ciq_sheets.peer_comps` passes its comps readers (it reaches only their
#: ``source_ref``, never a value the transforms copy).
COMPS_SRC = "CIQ Comparable Analysis"


class TransformError(RuntimeError):
    """A transform cannot regenerate its field from the ref's code and the page's own facts."""


@dataclass(frozen=True)
class Context:
    """What a transform may read besides the layer: the committed page (its ticker, CIK,
    reference date and the forward-multiple history beside the layer), and the page's own comps
    export, read by the ref's own CIQ reader — None when none was given."""

    page: dict[str, Any]
    comps: CiqBundle | None = None


def own_comps(mech: MechanicalLayer, ctx: Context) -> CiqBundle:
    """The comps export, once the ref's code has rebuilt the page's committed comps lines from it
    byte for byte — the proof that it is the export the page was built from."""
    if ctx.comps is None:
        raise TransformError(f"{ctx.page.get('ticker')}: this field needs the page's own comps "
                             "export (`--comps`), and none was given")
    checks = {
        "valuation.cross_sectional": (ciq_sheets.cross_sectional_valuation(ctx.comps).value,
                                      mech.valuation.cross_sectional.value),
        "peer_comps.trading_multiples": (ciq_sheets._comps_multiples(ctx.comps, COMPS_SRC).value,
                                         mech.peer_comps.trading_multiples.value),
    }
    bad = [k for k, (got, want) in checks.items() if got != want]
    if bad:
        raise TransformError(f"{ctx.page.get('ticker')}: the comps export given does not rebuild "
                             f"the committed {bad} — it is not the page's own export")
    return ctx.comps


# ------------------------------------------------------------------------- 1. drawdown shape

def relabel_drawdown_shape(mech: MechanicalLayer, ctx: Context | None = None) -> MechanicalLayer:
    """A window the detector found NO gap-down in carries the shape THIS code writes for one
    (`mechanical._CURRENT_WORDS.none_shape`): "gradual bleed — …" on main, #920's tested neutral
    wording on fix 3a's branch. "Found none" is read from the detector's own ref — "EOD gap-down
    detector …: none", undated or dated by #906's window — and its dates field holding nothing. A
    window WITH gap-downs is left exactly as committed."""
    words = mechanical._CURRENT_WORDS
    dc = mech.drawdown_cause
    if dc is None or dc.gap_down_dates.status.value == "present":
        return mech
    ref = dc.shape.source_ref or ""
    if not (ref.startswith("EOD gap-down detector") and ref.endswith(": none")):
        return mech
    if dc.shape.value == words.none_shape:
        return mech
    shape = dc.shape.model_copy(update={"value": words.none_shape})
    return mech.model_copy(update={"drawdown_cause": dc.model_copy(update={"shape": shape})})


# ------------------------------------------------------------------- 2. the trailing-only note

def trailing_only_note(mech: MechanicalLayer, ctx: Context) -> MechanicalLayer:
    """The trailing EV/EBITDA's note as THIS code writes it. A ref with `mechanical.ev_ebitda_note`
    (fix 3a) decides it from the page's guided forward, its consensus forward multiples, its
    forward-multiple history and — only when those three leave the note standing — the name's NTM
    cells on its own comps sheet. A ref without it writes the note inline whenever the guided
    forward is absent, which is the note the committed page already carries, so the layer is
    returned unchanged. Only a note equal to `TRAILING_ONLY_NOTE` is ever rewritten: any other is
    the reader's own, which neither rule touches; a deleted note is None, the note
    `ciq_sheets.ev_ebitda_current` leaves on a present multiple."""
    rule = getattr(mechanical, "ev_ebitda_note", None)
    v = mech.valuation
    ev = v.ev_ebitda
    if rule is None or ev.status is not PRESENT or ev.note != mechanical.TRAILING_ONLY_NOTE:
        return mech
    fmh = ctx.page.get("forward_multiple_history")
    fm = v.forward_multiples
    args: dict[str, Any] = {
        "guided_forward": v.ev_ebitda_adjusted_fwd.status is PRESENT,
        "forward_multiples": fm is not None and fm.status is PRESENT and bool(fm.value),
        "forward_history": ForwardMultipleHistory.model_validate(fmh) if fmh else None,
    }
    note = rule(peer_ntm=[], **args)
    if note is not None:   # only the comps sheet's NTM cells can still delete it
        ntm_cells = getattr(ciq_sheets, "comps_ntm_multiples", None)
        if ntm_cells is None:
            raise TransformError("this ref's note rule reads the comps NTM cells, and it has no "
                                 "`ciq_sheets.comps_ntm_multiples` to read them with")
        note = rule(peer_ntm=ntm_cells(own_comps(mech, ctx)), **args)
    if note == ev.note:
        return mech
    return mech.model_copy(update={"valuation": v.model_copy(update={
        "ev_ebitda": ev.model_copy(update={"note": note})})})


# ----------------------------------------------------------------------- 3. the survival read

def survival_read(mech: MechanicalLayer, ctx: Context | None = None) -> MechanicalLayer:
    """The survival line — its value and its source — as THIS code's `_survival_capacity` writes it
    from the page's own net leverage and adjusted leverage (and its FCF sign, at a ref before fix
    3b, whose line still carried that leg), set in BOTH places the page carries it
    (`quality.survival_capacity` and its copy `leverage_survival.survival`). A page whose net
    leverage is not present needs the CIQ net debt, which the layer does not carry: refused."""
    q = mech.quality
    if q.net_debt_to_ebitda.status is not PRESENT or q.net_debt_to_ebitda.value is None:
        raise TransformError(f"{(ctx.page.get('ticker') if ctx else '?')}: the net leverage is "
                             "not present, so the survival line needs the CIQ net debt, which the "
                             "layer does not carry")
    args: list[Any] = [q.net_debt_to_ebitda, q.net_debt_to_ebitda_adjusted]
    if "fcf_sign" in inspect.signature(mechanical._survival_capacity).parameters:
        args.append(q.fcf_sign)
    new = mechanical._survival_capacity(*args)
    old = q.survival_capacity
    if (new.value, new.source_ref) == (old.value, old.source_ref):
        return mech
    ls = mech.leverage_survival
    if ls is not None and ls.survival is not None and ls.survival.value != old.value:
        raise TransformError("leverage_survival.survival is not the copy of "
                             "quality.survival_capacity the builder writes")
    moved = {"value": new.value, "source_ref": new.source_ref}
    line = old.model_copy(update=moved)
    out = mech.model_copy(update={"quality": q.model_copy(update={"survival_capacity": line})})
    if ls is not None and ls.survival is not None:
        out = out.model_copy(update={"leverage_survival": ls.model_copy(
            update={"survival": ls.survival.model_copy(update=moved)})})
    return out


# ------------------------------------------------------------------ 4. the peer-gap question

def peer_gap_question(mech: MechanicalLayer, ctx: Context) -> MechanicalLayer:
    """`peer_comps.fundamental_deltas` as THIS code's `_comps_deltas` writes it from the page's
    own comps export — its question in whatever direction this code asks it, or none. Only the
    value changes, and only where the rebuilt deltas before the question are the committed ones
    (the export's Operating Statistics are the page's too)."""
    fd = mech.peer_comps.fundamental_deltas
    if fd.status is not PRESENT or not fd.value:
        return mech
    new = ciq_sheets._comps_deltas(own_comps(mech, ctx), COMPS_SRC)
    if new.value == fd.value:
        return mech
    if not isinstance(new.value, str) or new.value.partition("  [")[0] != fd.value.partition(
            "  [")[0]:
        raise TransformError(f"{ctx.page.get('ticker')}: the export's operating statistics do "
                             "not rebuild the committed deltas")
    pc = mech.peer_comps
    return mech.model_copy(update={"peer_comps": pc.model_copy(update={
        "fundamental_deltas": fd.model_copy(update={"value": new.value})})})


# --------------------------------------------------------------------- 5. the print row

@contextmanager
def _replaced(module: Any, **attrs: Any) -> Iterator[None]:
    saved = {k: getattr(module, k) for k in attrs}
    for k, v in attrs.items():
        setattr(module, k, v)
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(module, k, v)


_CADENCE = "cadence: EDGAR submissions ("
_GUIDE = ") · guide: "


def cadence_basis(source_ref: str) -> str:
    """The cadence basis inside a print row's source — the ONE reading of it, the inverse of the
    two forms `mechanical._catalyst_calendar` writes: "cadence: EDGAR submissions (BASIS)" and
    "cadence: EDGAR submissions (BASIS) · guide: REF". The row carries the basis in no structured
    field, so the string is read here and nowhere else; anything else is refused (#926 review F8:
    harness-only, the identity on 28 of 28 pages)."""
    if not source_ref.startswith(_CADENCE):
        raise TransformError(f"the print row's source is not the cadence read: {source_ref!r}")
    rest = source_ref[len(_CADENCE):]
    if _GUIDE in rest:
        return rest.split(_GUIDE, 1)[0]
    if not rest.endswith(")"):
        raise TransformError(f"the print row's source is not the cadence read: {source_ref!r}")
    return rest[:-1]


def print_row_guide(mech: MechanicalLayer, ctx: Context) -> MechanicalLayer:
    """The catalyst calendar's print row as THIS code's `_catalyst_calendar` writes it for the
    page's own drawdown guide and primary-source releases. The row's DATE is the committed one:
    the builder's two EDGAR reads (the 8-K list and the cadence estimate from it) are replaced, for
    this one call, by the committed estimate and its stated basis, so only what the row TESTS — and
    the source it names for that — is re-derived. The basis is read back from the committed row's
    own source by `cadence_basis`; the pins show the rebuilt row equals the committed one at main
    on every corpus page."""
    calendar = mech.catalyst_calendar
    if calendar is None:
        return mech
    rows = [r for r in calendar.rows if r.event == mechanical.PRINT_EVENT]
    if not rows:
        return mech
    if len(rows) != 1:
        raise TransformError(f"{len(rows)} print rows on one calendar")
    row = rows[0]
    est = (date.fromisoformat(row.expected_date), cadence_basis(row.source_ref or ""))
    with _replaced(mechanical,
                   eight_k_events=lambda *_a, **_k: [SimpleNamespace(filing_date=est[0],
                                                                     items=["2.02"])],
                   _next_print_estimate=lambda *_a, **_k: est):
        cal = mechanical._catalyst_calendar(
            None, str(ctx.page.get("cik") or ""),  # type: ignore[arg-type]
            date.fromisoformat(str(ctx.page["reference_date"])[:10]), mech)
    new = [r for r in cal.rows if r.event == mechanical.PRINT_EVENT]
    if len(new) != 1 or new[0].expected_date != row.expected_date:
        raise TransformError("the rebuilt calendar has no print row on the committed date")
    if (new[0].tests_what, new[0].source_ref) == (row.tests_what, row.source_ref):
        return mech
    fixed = row.model_copy(update={"tests_what": new[0].tests_what,
                                   "source_ref": new[0].source_ref})
    rows_out = [fixed if r is row else r for r in calendar.rows]
    return mech.model_copy(update={"catalyst_calendar": calendar.model_copy(
        update={"rows": rows_out})})


# ------------------------------------------------------------------- 6. the gap test (fix 4a)

_SINGLE = " — single segment"
_SHARE = re.compile(r"([^%;]+) (-?\d+)%")   # a name carries no share of its own


def segment_count_from_line(segments: Sourced[str]) -> int | None:
    """The segment count inside the committed `concentration.segments` line — the ONE reading of
    it, the inverse of the lean form `ciq_sheets._segment_section` writes: "<name> — single
    segment" is 1; "<a> 59%; <b> 23%; …" counts its shares less the reconciling lines
    (`ciq_sheets.is_segment_line`, the builder's own test), a lone segment then short of the
    collapse (a share under 100% as printed) being None; a line that is not PRESENT is None.
    Anything else is refused. HARNESS ONLY: the builder reads the roster itself
    (`ciq_sheets.segment_count`), and the pins show the two agree on every panel page's own
    export."""
    if segments.status is not PRESENT or segments.value is None:
        return None
    line = segments.value
    if line.endswith(_SINGLE) and ";" not in line:
        return 1
    parts = line.split("; ")
    shares = [_SHARE.fullmatch(p) for p in parts]
    if not all(shares):
        raise TransformError(f"the segments line is not the lean roster: {line!r}")
    named = [int(m.group(2)) for m in shares if m and ciq_sheets.is_segment_line(m.group(1))]
    if len(named) == 1:
        return 1 if named[0] >= 100 else None
    return len(named) or None


def gap_types(mech: MechanicalLayer, ctx: Context | None = None) -> MechanicalLayer:
    """`disclosure_gaps` as THIS code's `mechanical.disclosure_gaps` writes it from the page's own
    layer and its segment roster (`segment_count_from_line`). A ref without the gap test is left
    unchanged — the identity at main. Only that one field is written."""
    rule = getattr(mechanical, "disclosure_gaps", None)
    if rule is None:
        return mech
    gaps = rule(mech, segment_count=segment_count_from_line(mech.concentration.segments))
    if gaps == mech.disclosure_gaps:
        return mech
    return mech.model_copy(update={"disclosure_gaps": gaps})


# ------------------------------------------------------------------ fix 3b. the buyback legs

#: The leg a buyback field names, in the two forms `capital_allocation` writes: a stated field's
#: source ("EDGAR companyfacts TAG (START→END, Nd)", `_span` of a flow) and a not-current field's
#: note ("no current figure — the latest TAG covers START→END, Nd, which ends …").
_LEG_REF = re.compile(r"EDGAR companyfacts (\w+) "
                      r"\((\d{4}-\d{2}-\d{2})→(\d{4}-\d{2}-\d{2}), \d+d\)")
_LEG_STALE = re.compile(r"no current figure — the latest (\w+) covers "
                        r"(\d{4}-\d{2}-\d{2})→(\d{4}-\d{2}-\d{2}), \d+d, which ends ")


def buyback_point(field: Sourced[float], *, scale: float = 1.0) -> tuple[ConceptPoint, str] | None:
    """The point `capital_allocation._pick` chose for one buyback field, read back from the field —
    the ONE reading of it, the inverse of the two forms in `_LEG_REF`/`_LEG_STALE`: the tag and the
    span from its source (or, for a leg the code already found not current, from its note), the
    value from the field (× ``scale``: the cash is stored in $M). The layer carries the span in no
    structured field, so it is read here and nowhere else (HARNESS ONLY; the pins show the code
    rebuilds every committed buyback field from it on the 28 frozen pages). A not-current leg
    carries no value, and none is read: `capital_allocation._current` drops it first, so it is NaN.
    A field neither stated nor not-current names no point (None); a stated field whose source is
    not that form is refused."""
    if field.status is PRESENT and field.value is not None:
        m = _LEG_REF.fullmatch(field.source_ref or "")
        if m is None:
            raise TransformError(f"a buyback source is not the companyfacts span: "
                                 f"{field.source_ref!r}")
        value = field.value * scale
    else:
        m = _LEG_STALE.match(field.note or "")
        if m is None:
            return None
        value = math.nan
    start, end = date.fromisoformat(m.group(2)), date.fromisoformat(m.group(3))
    return ConceptPoint(concept="", tag=m.group(1), unit="", value=value, period_start=start,
                        period_end=end, filed=end, fy=None, fp=None, form=None,
                        accession=None), m.group(1)


def current_buybacks(mech: MechanicalLayer, ctx: Context | None = None) -> MechanicalLayer:
    """The three buyback fields as THIS code's `capital_allocation.buyback_legs` writes them from
    each field's own point (`buyback_point`) at the page's price date (`stock_info.as_of`, the cut
    the builder reads EDGAR at). A ref without it is left unchanged — the identity at main. A page
    with no price date is refused: the legs are dated against it and nothing else."""
    rule = getattr(capital_allocation, "buyback_legs", None)
    ca = mech.capital_allocation
    if rule is None or ca is None:
        return mech
    as_of = mech.stock_info.as_of if mech.stock_info is not None else None
    if as_of is None:
        raise TransformError(f"{(ctx.page.get('ticker') if ctx else '?')}: no price date "
                             "(stock_info.as_of) to date the buyback legs against")
    cash, shares, avg = rule(buyback_point(ca.buyback_cash, scale=1_000_000.0),
                             buyback_point(ca.buyback_shares), buyback_point(ca.buyback_avg_price),
                             as_of=as_of)
    if (cash, shares, avg) == (ca.buyback_cash, ca.buyback_shares, ca.buyback_avg_price):
        return mech
    return mech.model_copy(update={"capital_allocation": ca.model_copy(update={
        "buyback_cash": cash, "buyback_shares": shares, "buyback_avg_price": avg})})


# ------------------------------------------------------------------- 7. the as-of cut (row 57)

#: The fields `asof_cut` rewrites; a dropped release cited ANYWHERE ELSE on the layer is a read
#: it cannot regenerate, so it refuses.
_CUT_REWRITES: dict[str, Any] = {"primary_source": {"releases", "current_guide"},
                                 "valuation": {"adjusted_eps"}, "disclosure_gaps": True}


#: An EDGAR accession number, as a release's ``source_ref`` carries it ("8-K <accession> EX-99.1").
_ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}")


def asof_cut(mech: MechanicalLayer, ctx: Context | None = None) -> MechanicalLayer:
    """The release list as THIS code's assembly holds it at the page's price date
    (`gaps.price_date`, cut by `gaps.releases_by_cut`): a release filed after it leaves
    `primary_source.releases` for `releases_after_price_date`, and the two fields the assembly
    derives from the list are re-derived from what is left — `primary_source.current_guide`
    (`mechanical._current_guide`) and, where the page read it from the releases, `valuation.
    adjusted_eps` (`mechanical._release_adjusted_eps`). The identity at main (no
    `releases_by_cut`) and on every page with nothing after its price date.

    Before re-deriving, THIS code must rebuild both fields byte for byte from the page's own
    committed list — the proof that the page was built by these readers. It REFUSES
    (`TransformError`) where it cannot write what a builder at the cut would:
    - a CIQ guide row dated after the price date: the guide standing on the price date is on the
      export, not the page (`ciq_sheets._guidance_reads` picks it there);
    - a dropped release carrying a guide, a reconciliation, a one-off or an event impact, which
      readers it does not re-derive take (the triangulation, the guide check, the EBITDA
      reconciliation, the digest's blocks);
    - a dropped release cited by any field outside the three it rewrites;
    - a release with no filing date (`releases_by_cut` cannot place it)."""
    cut_rule = getattr(gaps, "releases_by_cut", None)
    if cut_rule is None:
        return mech
    # the ref's own rule; absent at main, so imported only past the check above
    from vinci.edgar.asof import within_cut

    cut = gaps.price_date(mech)
    ps = mech.primary_source
    if cut is None:
        return mech
    cp = mech.catalyst_path
    rows = cp.guidance_bridge_rows if cp is not None else None
    try:
        late = [r for r in (rows.value or [] if rows is not None else [])
                if not within_cut(date.fromisoformat(r.dated), cut)]
    except ValueError as exc:   # a row it cannot place on either side of the cut
        raise TransformError(f"a CIQ guide row's date does not parse: {exc}") from exc
    if late:
        raise TransformError(f"{len(late)} CIQ guide row(s) dated after the page's price date "
                             f"({cut.isoformat()}): the guide standing on it is on the export")
    if ps is None or not ps.releases:
        return mech
    try:
        kept, after = cut_rule(ps.releases, cut)
    except ValueError as exc:
        raise TransformError(str(exc)) from exc
    if not after:
        return mech
    full = [r for r in after if r.guidance or r.reconciliation or r.one_offs or r.event_impacts]
    if full:
        raise TransformError(f"{full[0].source_ref}, filed after the price date, carries content "
                             "readers this does not re-derive take")
    rest = mech.model_dump_json(exclude=_CUT_REWRITES)
    # by ACCESSION, dashed or not: a field may cite the 8-K without the exhibit suffix
    cited = [r.source_ref for r in after
             if any(a in rest or a.replace("-", "") in rest
                    for a in _ACCESSION.findall(r.source_ref) or [r.source_ref])]
    if cited:
        raise TransformError(f"{cited[0]}, filed after the price date, is cited by a field this "
                             "does not re-derive")
    v, dc = mech.valuation, mech.drawdown_cause
    absent = mechanical.no_adjusted_figure(dc.revised_guidance)
    rec = _last_close(mech)
    eps = v.adjusted_eps
    if mechanical._release_adjusted_eps(list(ps.releases), rec, absent) == eps:
        eps = mechanical._release_adjusted_eps(kept, rec, absent)
    elif not (eps.status is PRESENT
              and eps.source_ref == (dc.revised_guidance.source_ref or "EDGAR 8-K Ex-99.1")):
        raise TransformError("valuation.adjusted_eps reproduces from neither the releases nor "
                             "the drawdown guide")
    if mechanical._current_guide(list(ps.releases)) != ps.current_guide:
        raise TransformError("primary_source.current_guide does not reproduce from the page's "
                             "own releases")
    gone = [_schemas.ReleaseAfterPriceDate(filed=r.filed, source_ref=r.source_ref) for r in after]
    ps2 = ps.model_copy(update={"releases": kept, "current_guide": mechanical._current_guide(kept),
                                "releases_after_price_date": gone})
    return mech.model_copy(update={"primary_source": ps2,
                                   "valuation": v.model_copy(update={"adjusted_eps": eps})})


def _last_close(mech: MechanicalLayer) -> Any:
    """The record `_release_adjusted_eps` reads — its latest close only — from the page's own
    price box, which shows that close."""
    si = mech.stock_info
    price = si.price.value if si is not None and si.price.status is PRESENT else None
    return SimpleNamespace(prices=SimpleNamespace(last=SimpleNamespace(
        is_known=price is not None, value=price, as_of=si.as_of if si is not None else None)))


def driver_facts(mech: MechanicalLayer, ctx: Context) -> MechanicalLayer:
    """(RG-D8) The transcript driver rows' fact check (`driver_extract.check_fact`), run on each
    committed row's own metric, value and quote — the three inputs the extractor hands it, so
    the result is what the candidate's extractor writes for them. It writes only ``figures``,
    ``value_status`` and ``unknown_reason``; the prompt reads one of them, through
    `synthesis.prompt_driver_value`. The locator needs the call itself and reaches no field of
    the prompt, so it is not written. The identity at main (no `check_fact`) and on a page with
    no transcript row.

    A row that already carries a status (a page built with the check) must reproduce it, or the
    transform refuses (`TransformError`): its code is not the code under test."""
    from vinci.dossier import driver_extract

    check = getattr(driver_extract, "check_fact", None)
    od = mech.operating_drivers
    if check is None or od is None:
        return mech
    rows = []
    for r in od.rows:
        if r.tier != "llm-fenced":
            rows.append(r)
            continue
        if not r.verbatim:   # taken off the page (RG-D19 PR 3): its committed fact stands
            if r.value_status is None:
                raise TransformError(f"{ctx.page.get('ticker')}: driver row {r.metric!r} has "
                                     "neither words nor a fact on the page")
            rows.append(r)
            continue
        f = check(r.metric, r.value, r.verbatim)
        fields = {"figures": list(f.figures), "value_status": f.status, "unknown_reason": f.reason}
        if r.value_status is not None and (r.figures, r.value_status, r.unknown_reason) != tuple(
                fields.values()):
            raise TransformError(f"{ctx.page.get('ticker')}: the committed fact of driver row "
                                 f"{r.metric!r} does not reproduce from this code's check")
        rows.append(r.model_copy(update=fields))
    return mech.model_copy(update={"operating_drivers": od.model_copy(update={"rows": rows})})


Transform = Callable[[MechanicalLayer, Context], MechanicalLayer]

TRANSFORMS: dict[str, Transform] = {
    "relabel_drawdown_shape": relabel_drawdown_shape,
    "trailing_only_note": trailing_only_note,
    "survival_read": survival_read,
    "peer_gap_question": peer_gap_question,
    "print_row_guide": print_row_guide,
    "gap_types": gap_types,
    "current_buybacks": current_buybacks,
    "asof_cut": asof_cut,
    "driver_facts": driver_facts,
}

#: Fix 3a's five labels (#923), in the order applied.
FIX_3A: tuple[str, ...] = ("relabel_drawdown_shape", "trailing_only_note", "survival_read",
                           "peer_gap_question", "print_row_guide")

#: Fix 4a's one mechanical field (the gap test). Its other two changes — rule 8 and the
#: trailing-only ask — live in the prompt itself and reach a replay without a transform.
FIX_4A: tuple[str, ...] = ("gap_types",)

#: Fix 3b's two fields, in the order applied: the survival line (`survival_read`, shared with
#: `FIX_3A`) and the buyback legs.
FIX_3B: tuple[str, ...] = ("survival_read", "current_buybacks")

#: STATE row 57's one transform: the release list cut at the page's price date. Applied FIRST,
#: before the transforms that read the releases (`print_row_guide`, `gap_types`).
ASOF_CUT: tuple[str, ...] = ("asof_cut",)

#: RG-D8's one transform: the transcript driver rows' fact check, which the prompt reads as an
#: unverified row's value.
RG_D8: tuple[str, ...] = ("driver_facts",)
