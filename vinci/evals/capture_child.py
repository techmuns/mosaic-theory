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
        [--model M] [--max-tokens N] [--draws 5] [--expect-root DIR]
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

#: The build's model and budget (``config.graph_llm_model``; the client's default max_tokens).
DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 16384


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


def resolve_transforms(names: Sequence[str]) -> list[Transform]:
    """Each name → a transform: a key of ``variants.TRANSFORMS`` (``variants.py`` beside this file,
    loaded BY PATH so it binds to whichever ``vinci`` is importable — the code under test), or
    ``module:function`` naming one in that code. An unknown name raises; nothing is skipped."""
    out: list[Transform] = []
    table: dict[str, Transform] | None = None
    for name in names:
        if ":" in name:
            mod, _, fn = name.partition(":")
            out.append(getattr(importlib.import_module(mod), fn))
            continue
        if table is None:
            spec = importlib.util.spec_from_file_location(
                "_evals_variants", Path(__file__).with_name("variants.py"))
            if spec is None or spec.loader is None:
                raise RuntimeError("variants.py not found beside capture_child.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            table = dict(module.TRANSFORMS)
        if name not in table:
            raise KeyError(f"no transform {name!r}; known: {sorted(table)}")
        out.append(table[name])
    return out


def capture_calls(
    page: dict[str, Any], transcript: str | None, *, model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS, draws: int = 5,
    transform: Callable[[MechanicalLayer], MechanicalLayer] | None = None,
    unmark_material: bool = False, transforms: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Every request ``synthesize`` would send for ``page``, recorded at $0.

    ``transform`` is the VARIANT hook (#920's V2): a function from the committed layer to the layer
    a candidate's code writes, for a change to the mechanical layer's words, which a replay of the
    committed layer cannot see."""
    client = AnthropicLlmClient(model=model, max_tokens=max_tokens,
                                api_key="capture-only-not-a-key")
    rec = Recorder()
    client._client = rec  # type: ignore[assignment]  # the one swapped object
    mech = pre_synthesis_mech(page, unmark_material=unmark_material)
    for t in resolve_transforms(transforms):
        mech = t(mech)
    if transform is not None:
        mech = transform(mech)
    syn.synthesize(mech, llm=client, ticker=str(page["ticker"]), name=str(page["name"]),
                 transcript=transcript, sleeve=str(page["sleeve"]), draws=draws)
    return rec.calls


def jsonable(kwargs: dict[str, Any]) -> dict[str, Any]:
    """A request as JSON would carry it — the form two captures, or a capture and a guard's live
    request, are compared in."""
    out: dict[str, Any] = json.loads(json.dumps(kwargs, default=str, sort_keys=True))
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
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    ap.add_argument("--draws", type=int, default=5)
    ap.add_argument("--unmark-material", action="store_true")
    ap.add_argument("--transform", action="append", default=[],
                    help="a variants.py name or module:function, applied in order")
    ap.add_argument("--expect-root", type=Path,
                    help="refuse unless the imported vinci package lives under this folder")
    a = ap.parse_args(argv)
    import vinci
    where = Path(vinci.__file__).resolve()
    if a.expect_root is not None and a.expect_root.resolve() not in where.parents:
        print(f"capture_child: imported vinci from {where}, not under {a.expect_root}",
              file=sys.stderr)
        return 2
    page = json.loads(a.page.read_text(encoding="utf-8"))
    tx = a.transcript.read_text(encoding="utf-8") if a.transcript else None
    calls = capture_calls(page, tx, model=a.model, max_tokens=a.max_tokens, draws=a.draws,
                          unmark_material=a.unmark_material, transforms=a.transform)
    a.out.write_text(json.dumps({"calls": [jsonable(c) for c in calls]}), encoding="utf-8")
    return 0


if __name__ == "__main__":
    block_network()   # the child process only — never a caller that imports `main`
    raise SystemExit(main())
