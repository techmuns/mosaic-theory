"""Capture a synthesis request at $0 — the one implementation, importable AND runnable by path.

WHY ONE FILE THAT IMPORTS ONLY PRODUCTION. `replay.py` captures with the code it is imported from;
to prove a log against the code that WROTE it, the same capture runs in a child process whose
``PYTHONPATH`` is that commit's extracted ``vinci/`` (`replay.capture_at`). This file therefore
imports nothing from ``vinci.evals`` (which did not exist then), only the production entry points
#920 used — ``synthesize``, ``AnthropicLlmClient``, ``MechanicalLayer`` — whose signatures have
been stable since the five-draw gate.

THE METHOD (#920 §1-§2). Only the innermost SDK object (``client._client``) is replaced, by a
recorder that keeps each ``messages.create`` call's kwargs and raises ``LlmError``; ``synthesize``
logs an error draw and moves on. Every byte of the request is built by production code and nothing
is sent. The mechanical layer is the committed page's with the post-synthesis attachments undone
(read off ``assemble.py``): ``ev_gap`` is recomputed after synthesis, and
``capital_structure.covenant_term_rows`` is attached after it. A THIRD depends on the code version:
before #865 (``a15a2abf``, 2026-10-30) ``_mark_material`` ran AFTER ``synthesize``, so a page built
on older code carries marks its synthesis never read — ``unmark_material`` clears them (the annual
table's rows, the only ones ``_mark_material`` marks).

    python vinci/evals/capture_child.py --page P.json [--transcript T.txt] --out R.json \
        [--model M] [--max-tokens N] [--draws 5] [--expect-root DIR] [--transform NAME ...] \
        [--comps WORKBOOK] [--ciq FOLDER]

``--comps`` is the page's own CIQ comps export, which the transforms that need the comps sheet
read through the ref's own CIQ reader (`variants.own_comps` proves it is the page's own).
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from vinci.dossier import synthesis as syn
from vinci.dossier.schemas import MechanicalLayer
from vinci.graph.llm import AnthropicLlmClient, LlmError

#: The build's budget (the client's default max_tokens).
DEFAULT_MAX_TOKENS = 16384


def production_model() -> str:
    """THE MODEL IS PRODUCTION'S, read from the configuration of the code under test (fix request
    2, RG-D15). It was a constant here, a fifth copy of the model ID that no test pinned, so a
    candidate changing `config.graph_llm_model` was captured, drawn and priced on the old model and
    a model change could not be measured. In a child (`replay.capture_at`) this `vinci` is the
    code ref's, so the candidate's own configuration decides."""
    from vinci.config import get_config
    return get_config().graph_llm_model


def pre_synthesis_mech(page: dict[str, Any], *, unmark_material: bool = False) -> MechanicalLayer:
    """The committed mechanical layer as ``synthesize`` received it."""
    mech = MechanicalLayer.model_validate(page["mechanical"])
    fs = mech.financial_summary
    ann = fs.annual if fs is not None else None
    if unmark_material and fs is not None and ann is not None and ann.value is not None:
        rows = [r.model_copy(update={"material": False}) for r in ann.value.rows]
        mech = mech.model_copy(update={"financial_summary": fs.model_copy(update={
            "annual": ann.model_copy(update={"value": ann.value.model_copy(update={
                "rows": rows})})})})
    mech = mech.model_copy(update={"ev_gap": None})
    cs = mech.capital_structure
    if cs is not None and cs.covenant_term_rows is not None:
        mech = mech.model_copy(update={
            "capital_structure": cs.model_copy(update={"covenant_term_rows": None})})
    return mech


class Recorder:
    """Stands in for ``anthropic.Anthropic()``: records each request and raises, sending nothing."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.messages = self

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        raise LlmError("capture-only: no request sent")


Transform = Callable[[MechanicalLayer], MechanicalLayer]
#: A `variants.TRANSFORMS` entry: the layer and a ``variants.Context`` (the page, its comps).
ContextTransform = Callable[[MechanicalLayer, Any], MechanicalLayer]


def load_variants() -> Any:
    """``variants.py`` beside this file, loaded BY PATH so it binds to whichever ``vinci`` is
    importable — the code under test."""
    spec = importlib.util.spec_from_file_location(
        "_evals_variants", Path(__file__).with_name("variants.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("variants.py not found beside capture_child.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module   # a dataclass resolves its annotations through it
    spec.loader.exec_module(module)
    return module


def resolve_transforms(names: Sequence[str]) -> list[ContextTransform]:
    """Each name → a transform taking the layer and the page's context: a key of
    ``variants.TRANSFORMS``, or ``module:function`` naming a layer-only one in the code under
    test. An unknown name raises; nothing is skipped."""
    out: list[ContextTransform] = []
    table: dict[str, ContextTransform] | None = None
    for name in names:
        if ":" in name:
            mod, _, fn = name.partition(":")
            f: Transform = getattr(importlib.import_module(mod), fn)
            out.append(lambda m, _ctx, f=f: f(m))   # type: ignore[misc]
            continue
        if table is None:
            table = dict(load_variants().TRANSFORMS)
        if name not in table:
            raise KeyError(f"no transform {name!r}; known: {sorted(table)}")
        out.append(table[name])
    return out


def capture_calls(
    page: dict[str, Any], transcript: str | None, *, model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS, draws: int = 5,
    transform: Callable[[MechanicalLayer], MechanicalLayer] | None = None,
    unmark_material: bool = False, transforms: Sequence[str] = (), comps: Path | None = None,
    ciq: Path | None = None,
) -> list[dict[str, Any]]:
    """Every request ``synthesize`` would send for ``page``, recorded at $0.

    ``transform`` is the VARIANT hook (#920's V2): a function from the committed layer to the layer
    a candidate's code writes, for a change to the mechanical layer's words, which a replay of the
    committed layer cannot see."""
    client = AnthropicLlmClient(model=model or production_model(), max_tokens=max_tokens,
                                api_key="capture-only-not-a-key")
    rec = Recorder()
    client._client = rec  # type: ignore[assignment]  # the one swapped object
    mech = transformed_mech(page, unmark_material=unmark_material, transforms=transforms,
                            comps=comps, ciq=ciq)
    if transform is not None:
        mech = transform(mech)
    syn.synthesize(mech, llm=client, ticker=str(page["ticker"]), name=str(page["name"]),
                 transcript=transcript, sleeve=str(page["sleeve"]), draws=draws)
    return rec.calls


def transformed_mech(page: dict[str, Any], *, unmark_material: bool = False,
                     transforms: Sequence[str] = (), comps: Path | None = None,
                     ciq: Path | None = None) -> MechanicalLayer:
    """The layer a capture hands ``synthesize``: the committed one, with the named transforms
    applied in order by the code this module runs against (`capture_calls`, `--layer-only`)."""
    mech = pre_synthesis_mech(page, unmark_material=unmark_material)
    named = resolve_transforms(transforms)
    if named:
        from vinci.dossier.ciq import CiqBundle
        variants = load_variants()
        ctx = variants.Context(page=page, comps=(
            CiqBundle.from_files(str(page["ticker"]), [comps]) if comps is not None else None),
            ciq=(CiqBundle.from_files(str(page["ticker"]), sorted(
                f for f in ciq.iterdir() if f.is_file() and not f.name.startswith(".")))
                 if ciq is not None else None))
        for t in named:
            mech = t(mech, ctx)
    return mech


def jsonable(kwargs: dict[str, Any]) -> dict[str, Any]:
    """A request as JSON would carry it — the form two captures, or a capture and a guard's live
    request, are compared in. KEY ORDER IS KEPT: the paid path SENDS this form, and the SDK
    serialises dicts in insertion order, so a sorted copy would send production's tool schema
    with its fields reordered (PR 2 found its steps 1–2 drawn that way). Equality of two such
    dicts ignores order, so comparing never needed the sort."""
    out: dict[str, Any] = json.loads(json.dumps(kwargs, default=str))
    return out


def block_network() -> None:
    """No socket from this process can connect: a capture builds requests and sends none. A
    candidate whose code built its own client inside ``synthesize`` would otherwise spend,
    unguarded, during a $0 ``compare`` (the parent also strips the key: `replay.child_env`)."""
    import socket

    def refuse(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError("network is blocked in the $0 capture child")
    socket.socket.connect = refuse  # type: ignore[method-assign]
    socket.socket.connect_ex = refuse  # type: ignore[method-assign]
    socket.create_connection = refuse


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", required=True, type=Path)
    ap.add_argument("--transcript", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--model", help="unset: the model the code under test configures (RG-D15)")
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    ap.add_argument("--draws", type=int, default=5)
    ap.add_argument("--unmark-material", action="store_true")
    ap.add_argument("--transform", action="append", default=[],
                    help="a variants.py name or module:function, applied in order")
    ap.add_argument("--comps", type=Path, help="the page's own CIQ comps export")
    ap.add_argument("--ciq", type=Path, help="the page's own CIQ folder (read only)")
    ap.add_argument("--expect-root", type=Path,
                    help="refuse unless the imported vinci package lives under this folder")
    ap.add_argument("--layer-only", action="store_true",
                    help="write the transformed layer, build no request (STATE row 53 item 6)")
    a = ap.parse_args(argv)
    import vinci
    where = Path(vinci.__file__).resolve()
    if a.expect_root is not None and a.expect_root.resolve() not in where.parents:
        print(f"capture_child: imported vinci from {where}, not under {a.expect_root}",
              file=sys.stderr)
        return 2
    page = json.loads(a.page.read_text(encoding="utf-8"))
    if a.layer_only:
        mech = transformed_mech(page, unmark_material=a.unmark_material, transforms=a.transform,
                                comps=a.comps, ciq=a.ciq)
        a.out.write_text(json.dumps({"layer": mech.model_dump(mode="json")}), encoding="utf-8")
        return 0
    tx = a.transcript.read_text(encoding="utf-8") if a.transcript else None
    calls = capture_calls(page, tx, model=a.model, max_tokens=a.max_tokens, draws=a.draws,
                          unmark_material=a.unmark_material, transforms=a.transform,
                          comps=a.comps, ciq=a.ciq)
    a.out.write_text(json.dumps({"calls": [jsonable(c) for c in calls]}), encoding="utf-8")
    return 0


if __name__ == "__main__":
    block_network()   # the child process only — never a caller that imports `main`
    raise SystemExit(main())
