"""The capture module the impact child loads BY PATH in step 2 of the SDK byte check
(`capture.py`'s docstring has the whole procedure).

It saves each page's synthesis INPUTS exactly as the child hands them over (the page as built, its
material marked, and the transcript text), so step 3 can send the same inputs through two SDKs.
Then it delegates to the ref's own `vinci/evals/capture_child.py`, so `request.json` is written as
usual. Every other name the child reads is forwarded to that module (`__getattr__`), so this file
follows the child's interface as it changes. It imports only production modules, which bind to the
ref's extracted code.

The inputs carry licensed transcript text: `SDKCHECK_INPUTS` names a folder outside the repo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from vinci.evals import capture_child as _cc


def __getattr__(name: str) -> Any:   # every other name the impact child reads: the ref's own
    return getattr(_cc, name)


def _side() -> str:
    """`base` or `head`: the child runs in `<out>/sandboxes/<side>/<ticker>/impact-inputs`."""
    parts = Path.cwd().parts
    if "sandboxes" not in parts:   # fail loud: step 3 reads `<inputs>/head`, never a guess
        raise RuntimeError(f"the impact child is not in a sandbox (cwd {Path.cwd()}); "
                           "its side, base or head, is unknown")
    return parts[parts.index("sandboxes") + 1]


def capture_calls(page: dict[str, Any], transcript: str | None,
                  **kw: Any) -> list[dict[str, Any]]:
    out = Path(os.environ["SDKCHECK_INPUTS"]) / _side()
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{page['ticker']}.json").write_text(json.dumps(
        {"page": page, "transcript": transcript,
         "kw": {k: v for k, v in kw.items() if isinstance(v, (str, int, float, bool))}}),
        encoding="utf-8")
    calls: list[dict[str, Any]] = _cc.capture_calls(page, transcript, **kw)
    return calls
