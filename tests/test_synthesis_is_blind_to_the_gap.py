"""THE SYNTHESIS MUST NOT SEE `ev_gap` — and today only statement ORDER stops it.

WHY IT MATTERS, and it is the whole point of the A2 comparison: `synthesize` dumps the ENTIRE
mechanical layer to the LLM (`mech.model_dump(exclude={"primary_source"})`). If `ev_gap` were
populated at that moment, the model would read `shape: multiple-dominant` and echo it — and a
thesis that agrees with the arithmetic because it was TOLD the arithmetic proves nothing. The
value of "does the blind synthesis match the gap's shape?" rests entirely on the blindness.

WHAT PROTECTS IT TODAY: nothing but the order of two statements — `synthesize(...)` runs before
`ev_gap_transform(...)` in `assemble`. Moving the transform up would silently destroy the
independence with no test complaining — the same shape as every declared-but-unenforced defect in
this stretch, one rung on: correct-by-accident-of-order.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

from vinci.dossier import assemble as da
from vinci.dossier import synthesis as ds

ROOT = Path(__file__).resolve().parents[1]


def _line_of(tree: ast.AST, needle: str) -> int:
    """The line of the first Call whose dump mentions ``needle``."""
    hits = [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.Call) and needle in ast.dump(n)]
    assert hits, f"no call to {needle} found in the assembly path"
    return min(hits)


def test_the_gap_is_computed_after_the_synthesis_not_before() -> None:
    """THE ORDER IS THE GUARANTEE, so the order is what gets pinned."""
    tree = ast.parse(inspect.getsource(da))
    synth_at = _line_of(tree, "synthesize")
    gap_at = _line_of(tree, "ev_gap_transform")
    assert synth_at < gap_at, (
        f"`ev_gap_transform` (line {gap_at}) now runs BEFORE `synthesize` (line {synth_at}). The "
        "synthesis would then read `shape: multiple-dominant` out of its own input and echo it — "
        "and the A2 comparison, which asks whether a BLIND thesis matches the arithmetic, would "
        "silently become a test of whether the model can copy.")


def test_the_synthesis_dumps_the_whole_mech_which_is_why_the_order_matters() -> None:
    """The premise, asserted so the test above cannot be read as arbitrary. If `synthesize` ever
    starts sending a CURATED digest instead of the full dump, this reddens and the ordering pin can
    be replaced by an explicit exclusion — which would be strictly better."""
    src = inspect.getsource(ds.synthesize)
    assert "model_dump(" in src and "primary_source" in src, (
        "synthesize no longer dumps the whole mechanical layer — if it now curates its input, "
        "exclude `ev_gap` explicitly and delete the ordering pin, which is the weaker guarantee.")
    assert "ev_gap" not in src, (
        "synthesize references ev_gap — the synthesis must not be given the machine's own shape "
        "label under any circumstances.")


def test_no_committed_dossier_has_a_synthesis_that_quotes_the_shape_label() -> None:
    """THE OUTCOME, not the mechanism. Even blind, a synthesis that used the vocabulary would be
    worth knowing about — the labels are house terms, so their appearance in analyst prose means
    either a leak or a coincidence that needs reading."""
    import json

    for folder in sorted((ROOT / "data" / "dossiers").iterdir()):
        f = folder / "dossier.json"
        if not f.exists():
            continue
        syn = json.dumps(json.loads(f.read_text()).get("synthesis") or {})
        for label in ("multiple-dominant", "timing-duration"):
            assert label not in syn, (
                f"{folder.name}: the synthesis uses the shape label {label!r} — the machine's own "
                "attribution vocabulary has reached the analyst prose")
