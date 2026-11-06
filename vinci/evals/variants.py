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
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace
from typing import Any

from vinci.dossier import ciq_sheets, mechanical
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import ForwardMultipleHistory, MechanicalLayer, SourceStatus

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
    """The survival line as THIS code's `_survival_capacity` writes it from the page's own net
    leverage, adjusted leverage and FCF sign, set in BOTH places the page carries it
    (`quality.survival_capacity` and its copy `leverage_survival.survival`). A page whose net
    leverage is not present needs the CIQ net debt, which the layer does not carry: refused."""
    q = mech.quality
    if q.net_debt_to_ebitda.status is not PRESENT or q.net_debt_to_ebitda.value is None:
        raise TransformError(f"{(ctx.page.get('ticker') if ctx else '?')}: the net leverage is "
                             "not present, so the survival line needs the CIQ net debt, which the "
                             "layer does not carry")
    new = mechanical._survival_capacity(q.net_debt_to_ebitda, q.net_debt_to_ebitda_adjusted,
                                        q.fcf_sign)  # type: ignore[arg-type]  # the builder's own
    old = q.survival_capacity
    if new.value == old.value:
        return mech
    ls = mech.leverage_survival
    if ls is not None and ls.survival is not None and ls.survival.value != old.value:
        raise TransformError("leverage_survival.survival is not the copy of "
                             "quality.survival_capacity the builder writes")
    line = old.model_copy(update={"value": new.value})
    out = mech.model_copy(update={"quality": q.model_copy(update={"survival_capacity": line})})
    if ls is not None and ls.survival is not None:
        out = out.model_copy(update={"leverage_survival": ls.model_copy(
            update={"survival": ls.survival.model_copy(update={"value": new.value})})})
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


def print_row_guide(mech: MechanicalLayer, ctx: Context) -> MechanicalLayer:
    """The catalyst calendar's print row as THIS code's `_catalyst_calendar` writes it for the
    page's own drawdown guide and primary-source releases. The row's DATE is the committed one:
    the builder's two EDGAR reads (the 8-K list and the cadence estimate from it) are replaced, for
    this one call, by the committed estimate and its stated basis, so only what the row TESTS — and
    the source it names for that — is re-derived. The basis is read back from the committed row's
    own source (its one string read); the pins show the rebuilt row equals the committed one at
    main on every corpus page."""
    calendar = mech.catalyst_calendar
    if calendar is None:
        return mech
    rows = [r for r in calendar.rows if r.event == mechanical.PRINT_EVENT]
    if not rows:
        return mech
    if len(rows) != 1:
        raise TransformError(f"{len(rows)} print rows on one calendar")
    row = rows[0]
    src = row.source_ref or ""
    if not src.startswith(_CADENCE):
        raise TransformError(f"the print row's source is not the cadence read: {src!r}")
    rest = src[len(_CADENCE):]
    basis = rest.split(") · guide: ", 1)[0] if ") · guide: " in rest else rest.removesuffix(")")
    est = (date.fromisoformat(row.expected_date), basis)
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


Transform = Callable[[MechanicalLayer, Context], MechanicalLayer]

TRANSFORMS: dict[str, Transform] = {
    "relabel_drawdown_shape": relabel_drawdown_shape,
    "trailing_only_note": trailing_only_note,
    "survival_read": survival_read,
    "peer_gap_question": peer_gap_question,
    "print_row_guide": print_row_guide,
}

#: Fix 3a's five labels (#923), in the order applied.
FIX_3A: tuple[str, ...] = ("relabel_drawdown_shape", "trailing_only_note", "survival_read",
                           "peer_gap_question", "print_row_guide")
