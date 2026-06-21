"""Dossier-assembler (STATE.md §5 step 2) — **assembles and cites, never concludes**.

A per-finalist artifact: a deterministic, source-bound *mechanical* layer (valuation, quality,
concentration, drawdown-cause, idiosyncratic-vs-shared, consensus context — every fact a
``{value, source_ref}``), plus a *fenced* LLM synthesis (bull/bear cases, historical analogues,
the decisive question, key unknowns) whose only input is the mechanical facts. The synthesis schema
has no field for a verdict/score/direction/probability — the conclude-step is the human's, logged
separately via the ledger. The graph is a research INPUT, never a predictor.
"""

from mosaic.dossier.requirements import (
    CIQ_MODULES,
    EDGAR_FREE_INPUTS,
    CiqModuleRequirement,
    as_payload,
    manifest_flags,
    missing_required,
    render_checklist,
)
from mosaic.dossier.schemas import (
    Dossier,
    MechanicalLayer,
    Sourced,
    SourceStatus,
    Synthesis,
)

__all__ = [
    "CIQ_MODULES",
    "EDGAR_FREE_INPUTS",
    "CiqModuleRequirement",
    "Dossier",
    "MechanicalLayer",
    "Sourced",
    "SourceStatus",
    "Synthesis",
    "as_payload",
    "manifest_flags",
    "missing_required",
    "render_checklist",
]
