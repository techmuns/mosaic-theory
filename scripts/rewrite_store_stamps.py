"""Rewrite a committed page's price-store stamp from absolute local paths to checkout folder names,
in place, touching nothing else (2026-11-05).

    PYTHONPATH=$PWD python scripts/rewrite_store_stamps.py <dossier.json> …

WHY. Until 2026-11-05 `assemble._price_store_stamp` wrote `price_store.declared_path` and
`resolved_path` as absolute paths, which named the user and the session on a public page
(`tests/test_no_local_paths.py`). The writer now stamps only each checkout's folder name
(`assemble.store_checkout`); this brings a page stamped before then to the same form, by the same
function, so the clean and the writer cannot disagree.

DETERMINISTIC AND SURGICAL. It reads the committed JSON and nothing else — no store, no CIQ
export, no extractor, no LLM — so it may run on any committed page, a held audit name's included
(operator ruling D-D4). It replaces each of the two `"key": "value"` spans in the file's own text
(never a `json.load → json.dump` round trip, which would reformat the page), then proves the
result parses to the input with exactly those two values changed. A value that is already a
folder name is left alone, so a second run is a no-op. A file whose stamp it cannot rewrite that
way raises, naming the file, and nothing is written for it.

It does not rebuild the web mirrors: run `python frontend/build.py` after it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from vinci.dossier.assemble import store_checkout

KEYS = ("declared_path", "resolved_path")


def rewrite(text: str, *, name: str) -> tuple[str, dict[str, str]]:
    """(the page's new text, {key: new value} for each field rewritten). `name` labels errors."""
    doc: dict[str, Any] = json.loads(text)
    stamp = doc.get("price_store")
    if not stamp:
        return text, {}
    out, moved = text, {}
    for key in KEYS:
        value = stamp[key]
        if not PurePosixPath(value).is_absolute():
            if "/" in value or "\\" in value:
                raise ValueError(f"{name}: price_store.{key} is a path, but not a POSIX absolute "
                                 "one this rewrite knows how to reduce")
            continue                      # already a folder name
        new = store_checkout(Path(value))
        span = f"{json.dumps(key)}: {json.dumps(value)}"
        if out.count(span) != 1:
            raise ValueError(f"{name}: price_store.{key}'s text occurs {out.count(span)} times, "
                             "not once — refusing to guess which to rewrite")
        out = out.replace(span, f"{json.dumps(key)}: {json.dumps(new)}")
        moved[key] = new
    expect = json.loads(text)
    expect["price_store"].update(moved)
    if json.loads(out) != expect:
        raise ValueError(f"{name}: the rewrite changed more than price_store's two paths")
    return out, moved


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    for arg in argv:
        path = Path(arg)
        text = path.read_text()
        out, moved = rewrite(text, name=arg)
        if moved:
            path.write_text(out)
        print(f"{arg}: " + (", ".join(f"{k} → {v}" for k, v in moved.items()) or "unchanged"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
