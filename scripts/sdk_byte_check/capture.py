"""THE $0 SDK BYTE CHECK — what every `anthropic` bump goes behind (operator, 2026-11-13: "Check,
then pin newest (Recommended)"; `docs/records/2026-11-13-the-anthropic-sdk-is-pinned-at-2-6-0-
behind-a-byte-check.md`).

The question: does the candidate SDK send the bytes the pinned one sends, for every paid call path?
Every request goes through the REAL SDK of a venv, whose HTTP client is given a MockTransport. The
transport keeps the exact bytes the SDK would send (method, URL, every header in order, the body)
and answers with a canned message that stops at max_tokens, so production's `extract` raises
`LlmError`, as `capture_child.Recorder` makes it do. No socket can connect (`block_network`) and no
key is real: $0.

THE PROCEDURE, all $0, every output OUTSIDE the repo (bodies carry licensed transcript text):

1. Two throwaway venvs, never a shared one. A installs `requirements.lock`. B installs the lock
   with the candidate SDK (`uv pip compile … --upgrade-package anthropic==<X>` into a scratch copy).
   Then `pip freeze` both: they should differ only in the SDK and its own dependencies.
2. Inputs, built once by either venv: every committed page's synthesis inputs, from the impact
   check's own $0 builds (RUNBOOKS §o; pass its `--store`, `--ciq-root`, `--cache-root` and
   `--env-file` at the primary checkout):

       SDKCHECK_INPUTS=<inputs> PYTHONPATH=$PWD python -P scripts/sdk_byte_check/build_inputs.py \\
           run --base HEAD --head HEAD --no-shortcut --skip-fail-first --out <dir> --store …

   A page whose build refuses gets `committed_input.py` (its committed page, as a fallback).
3. In EACH venv, from the repo root:

       PYTHONPATH=$PWD <venv>/bin/python -P scripts/sdk_byte_check/capture.py \\
           --inputs <inputs>/head [--fallback <dir>] --out <A or B>

   then `python scripts/sdk_byte_check/compare.py <A> <B>`, which exits 1 when any body differs.
   Headers are reported apart from the bodies: the SDK's own version headers always differ.

THE PATHS: every page's synthesis at its five draws (cached) and at one (uncached); the
confirmation's ten draws through its own `_Recording`; the evals judge on the frozen gold pages;
the theme desk's plain call and its split, cached-article call; and `validate_keys.py`'s ping.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anthropic
import anthropic._base_client as _bc

from vinci.evals.capture_child import block_network, pre_synthesis_mech

# the SDK's HTTP library, by name: httpx2 from 1.x on, httpx before (neither exported)
HX: Any = getattr(_bc, "httpx2", None) or getattr(_bc, "httpx")  # noqa: B009
KEY = "sk-ant-sdkcheck-not-a-key"
REPO = Path(__file__).resolve().parents[2]


class Capture:
    """Keeps every request of one path: its bytes on disk, its envelope in `index`."""

    def __init__(self, out: Path, path: str) -> None:
        self.out, self.path, self.n, self.label = out, path, 0, ""
        self.index: list[dict[str, Any]] = []

    def handler(self, request: Any) -> Any:
        body: bytes = request.read()
        self.n += 1
        name = f"{self.path}/{self.label}-{self.n:02d}.body"
        (self.out / name).parent.mkdir(parents=True, exist_ok=True)
        (self.out / name).write_bytes(body)
        self.index.append({
            "path": self.path, "label": self.label, "n": self.n, "method": request.method,
            "url": str(request.url),
            "headers": [[str(k).lower(), str(v)] for k, v in request.headers.multi_items()],
            "body_file": name, "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_bytes": len(body)})
        model = json.loads(body).get("model", "unknown")
        return HX.Response(200, headers={"request-id": "req_sdkcheck"}, json={
            "id": "msg_sdkcheck", "type": "message", "role": "assistant", "model": model,
            "content": [{"type": "text", "text": "sdkcheck"}], "stop_reason": "max_tokens",
            "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}})

    def http_client(self) -> Any:
        return anthropic.DefaultHttpxClient(transport=HX.MockTransport(self.handler))

    def sdk(self) -> Any:
        return anthropic.Anthropic(api_key=KEY, max_retries=0, http_client=self.http_client())


def client_for(cap: Capture, model: str, max_tokens: int, cls: Any = None) -> Any:
    """Production's client (or a subclass), its SDK object the real one on the mock transport."""
    from vinci.graph.llm import AnthropicLlmClient
    c = (cls or AnthropicLlmClient)(model=model, max_tokens=max_tokens, api_key=KEY)
    c._client = cap.sdk()
    return c


def synthesis(cap: Capture, inputs: Path, draws: int | None,
              wrap: Callable[[Any], Any] | None = None) -> int:
    """Each saved input through production's `synthesize`, as `capture_child.capture_calls`
    sends it — its `draws` unless given."""
    from vinci.dossier import synthesis as syn
    from vinci.evals.capture_child import DEFAULT_MAX_TOKENS, production_model
    files = sorted(inputs.glob("*.json"))
    if not files:   # a mis-pointed folder would capture nothing on both sides, and compare equal
        raise RuntimeError(f"no saved synthesis input in {inputs}")
    done = 0
    for f in files:
        inp = json.loads(f.read_text(encoding="utf-8"))
        page, kw = inp["page"], inp["kw"]
        n = draws if draws is not None else int(kw.get("draws", 5))
        cap.label, cap.n = str(page["ticker"]), 0
        llm = client_for(cap, str(kw.get("model") or production_model()),
                         int(kw.get("max_tokens") or DEFAULT_MAX_TOKENS))
        syn.synthesize(pre_synthesis_mech(page), llm=wrap(llm) if wrap else llm,
                       ticker=str(page["ticker"]), name=str(page["name"]),
                       transcript=inp["transcript"], sleeve=str(page["sleeve"]), draws=n)
        done += 1
    return done


def judge(cap: Capture) -> int:
    """The evals judge's request for every gold page, built by `judge.judge_request`."""
    from vinci.evals import gold as gd
    from vinci.evals import judge as jd
    from vinci.evals import report
    from vinci.graph.llm import LlmError
    pool = gd.load_gold()
    pages = sorted({g.page for g in pool})
    for t in pages:
        claims = [(g.id, g.text) for g in pool if g.page == t]
        req = jd.judge_request(report._frozen_page(t, report.GOLD_REF), claims)
        cap.label, cap.n = t, 0
        with contextlib.suppress(LlmError):
            client_for(cap, req.model, req.max_tokens).extract(
                system=req.system, user=req.user, tool=req.kwargs["tools"][0])
    return len(pages)


def theme(cap: Capture) -> int:
    """The theme desk's two request shapes, on the authentic J.P. Morgan excerpt fixture: its
    pass-1 extraction, and a split completeness part whose article goes as a cached block."""
    sys.path.insert(0, str(REPO))
    from tests.theme_intelligence_support import JPM_AS_OF, jpm_document
    from vinci.graph.llm import LlmError
    from vinci.theme_intelligence import completeness as cm
    from vinci.theme_intelligence import extract as ex
    from vinci.theme_intelligence.config import LLM_MAX_TOKENS, LLM_MODEL, load_taxonomy
    from vinci.theme_intelligence.llm import ARTICLE_END, ThemeLlmClient
    tax = load_taxonomy()
    user = ex.user_message(jpm_document(), publisher="J.P. Morgan", as_of=JPM_AS_OF.isoformat())
    if ARTICLE_END not in user:
        raise RuntimeError("the theme desk's message no longer ends its article where the split "
                           "client looks for it; the split case would not split")
    cases = [("extract", ex.system_prompt(tax), user, ex.tool_schema(tax), False),
             ("completeness-split", cm.completeness_system(tax),
              user + "\n<first_pass_record>\nClaims:\n(sdkcheck tail)", cm.completeness_tool(tax),
              True)]
    for label, system, u, tool, cache in cases:
        cap.label, cap.n = label, 0
        with contextlib.suppress(LlmError):
            # production's cap (`__main__._client`): the SDK derives its timeout from it
            client_for(cap, LLM_MODEL, LLM_MAX_TOKENS, cls=ThemeLlmClient).extract(
                system=system, user=u, tool=tool, cache=cache)
    return len(cases)


def validate_keys(cap: Capture) -> int:
    """`.github/scripts/validate_keys.py`'s ping, with its own `anthropic.Anthropic(...)` given
    the mock transport."""
    spec = importlib.util.spec_from_file_location(
        "_validate_keys", REPO / ".github" / "scripts" / "validate_keys.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("validate_keys.py not found")
    vk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vk)
    real = anthropic.Anthropic
    cap.label, cap.n = "ping", 0

    def factory(**kw: Any) -> Any:
        return real(**{**kw, "max_retries": 0, "http_client": cap.http_client()})
    anthropic.Anthropic = factory  # type: ignore[misc,assignment]
    prior = os.environ.get("ANTHROPIC_API_KEY")   # restored: a test process keeps its own key
    os.environ["ANTHROPIC_API_KEY"] = KEY
    try:
        vk.check_anthropic()
    finally:
        anthropic.Anthropic = real  # type: ignore[misc]
        if prior is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = prior
    return 1


def paths(inputs: Path | None, fallback: Path | None
          ) -> list[tuple[str, Callable[[Capture], int]]]:
    from vinci.dossier.confirmation import CONFIRM_DRAWS, _Recording
    out: list[tuple[str, Callable[[Capture], int]]] = []
    if inputs is not None:
        out += [("synthesis-5draws", lambda c: synthesis(c, inputs, None)),
                ("synthesis-1draw", lambda c: synthesis(c, inputs, 1)),
                ("confirmation-10draws",
                 lambda c: synthesis(c, inputs, CONFIRM_DRAWS, wrap=_Recording))]
    if fallback is not None:
        out.append(("synthesis-5draws-committed-fallback",
                    lambda c: synthesis(c, fallback, None)))
    return out + [("judge", judge), ("theme", theme), ("validate-keys", validate_keys)]


def run(out: Path, inputs: Path | None, fallback: Path | None) -> dict[str, Any]:
    from vinci.evals.replay import refuse_inside_repo
    refuse_inside_repo(out, "the SDK byte check's captures (they carry transcript text)")
    out.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"anthropic": anthropic.__version__, "http_lib": HX.__name__,
                               "paths": {}}
    index: list[dict[str, Any]] = []
    for name, fn in paths(inputs, fallback):
        cap = Capture(out, name)
        units = fn(cap)
        index += cap.index
        summary["paths"][name] = {"units": units, "requests": len(cap.index)}
        print(f"{name}: {units} unit(s), {len(cap.index)} request(s)", flush=True)
    (out / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", type=Path, help="step 2's inputs/head")
    ap.add_argument("--fallback", type=Path, help="committed_input.py's folder")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    for k in [k for k in os.environ if k.startswith("ANTHROPIC")]:
        os.environ.pop(k)
    block_network()
    run(a.out, a.inputs, a.fallback)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
