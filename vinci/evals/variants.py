"""Variant transforms — how a change to the MECHANICAL layer's words reaches a replay.

The replay reads a committed mechanical layer, so a change to a label ``mechanical.py`` writes
(fix 3a) does not reach the request by itself. A transform re-reads such a field from the code
version UNDER TEST. This file is loaded BY PATH in the capture child (`capture_child.py
--transform NAME`), so ``vinci.dossier.mechanical`` below is the extracted ref's own module: the
same transform is the identity at main and the branch's wording at the branch. It imports nothing
from ``vinci.evals`` for that reason.

A transform must change ONLY the fields its change rewrites, from facts already on the page, and
its PR shows at $0 that the result equals what the candidate's own builder writes for those fields
(RUNBOOKS §n step 2).
"""
from __future__ import annotations

from collections.abc import Callable

from vinci.dossier import mechanical
from vinci.dossier.schemas import MechanicalLayer


def relabel_drawdown_shape(mech: MechanicalLayer) -> MechanicalLayer:
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


TRANSFORMS: dict[str, Callable[[MechanicalLayer], MechanicalLayer]] = {
    "relabel_drawdown_shape": relabel_drawdown_shape,
}
