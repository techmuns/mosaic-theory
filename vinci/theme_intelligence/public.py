"""WHAT THE REGISTRY EXPORT MAY CARRY. The export (`Store.export_jsonl`, behind `state push`) is
the registry of record on the `theme-intelligence-state` branch of a PUBLIC repository, so
everything it writes is published. Operator ruling 2026-11-19 ("Fix source + scrub tip"): only
titles, figures and SHORT quotes may leave this machine.

On a74c4e30 the branch carried 31,207 distinct characters of report body misfiled as section
headings, plus a 2,042-character and five 911-character claim quotes, and 17 + 57 + 3 absolute
local paths. The rules, applied to every row as it is written (`public_payload`):
- a source's own words (a `quote`, a source-risk `sentence`, and a passage claim's `statement`,
  which is the source's sentence) are at most `DESK_QUOTE_MAX_CHARS`, the desk's cap;
- a claim's quote is cut at its HEAD, never windowed on its figure: a figure occurring twice in a
  table would put another cell's number in the window and let the number check pass on it (review
  of #1143). A card on an imported registry citing a claim whose figure lies past the cut has its
  line withheld instead, which fails loud;
- a block's `section` longer than `HEADING_MAX_CHARS` is no heading (body text the reader misfiled)
  and is dropped;
- an absolute local path becomes relative to the data directory, or `⟨local path⟩/<file name>`
  outside it.

An SEC filing's own sentence (`basis_quote`) is a public record, not a publisher's text, and is not
capped. Text the model wrote (card lines, reasons, rule traces) is not a source's words and is not
capped. A field the export shortens is shortened in the export ONLY: this machine's registry keeps
every word, and an import holds the shortened text.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path, PureWindowsPath
from typing import Any

from vinci.theme_intelligence.config import DEFAULT_DATA_DIR
from vinci.theme_intelligence.display import DESK_QUOTE_MAX_CHARS, desk_quote
from vinci.theme_intelligence.documents import HEADING_MAX_CHARS

#: keys whose string value is a SOURCE's own words, wherever they sit in a payload
SOURCE_TEXT_KEYS = frozenset({"quote", "sentence"})
#: an absolute path under ANY root (Codex on #1143: a named-root list let /workspace, /mnt, /srv
#: and /data through): two or more segments after a slash that STARTS a token (the text's start,
#: whitespace, a quote, "(", "[", "=" or "file://"), so a URL's path ("https://a.test/b/c"), a
#: unit ("$/kW/month"), a ratio ("2026/27") and a word pair ("AI/ML") are not paths; or a Windows
#: drive. Measured on a74c4e30: it finds the 78 paths, plus a runner's traceback path in a run
#: warning, and no unit, URL or identity field
_ABS_PATH = re.compile(r"(?:^|(?<=[\s'\"(\[=])|(?<=file://))(?:/[\w.-]+(?:/[^\s'\"()\[\]<>,;]+)+"
                       r"|[A-Za-z]:\\[^\s'\"()\[\]<>,;]+)")
LOCAL_PATH = "⟨local path⟩"


def public_path(text: str, data_dir: Path) -> str:
    """Every absolute path in `text`, relative to `data_dir` when under it, else the file name."""
    root = str(data_dir.resolve())
    # the conventional layout's own relative name ("data/theme_intelligence/…"), the form the
    # registry already holds for paths it recorded relative; any other folder by its name
    prefix = (DEFAULT_DATA_DIR.as_posix() if data_dir.resolve().parts[-2:] == DEFAULT_DATA_DIR.parts
              else data_dir.name)

    def one(m: re.Match[str]) -> str:
        p = m.group(0)
        for base in (root, str(data_dir)):
            if p == base or p.startswith(base.rstrip("/") + "/"):
                return f"{prefix}/{p[len(base):].lstrip('/')}".rstrip("/")
        # a drive path is read with Windows separators: on the POSIX host that pushes, `Path`
        # would keep "C:\\Users\\…" whole as one name (Codex on #1143)
        name = PureWindowsPath(p).name if re.match(r"[A-Za-z]:\\", p) else Path(p).name
        return f"{LOCAL_PATH}/{name}"

    return _ABS_PATH.sub(one, text)


def public_payload(table: str, payload: Any, data_dir: Path, cut: Counter[str]) -> Any:
    """`payload` as the export may carry it (the module rules). `cut` counts each rule's cuts by
    `table.field`, so a caller can say what an export shortened."""

    def walk(o: Any, path: str) -> Any:
        if isinstance(o, dict):
            out: dict[str, Any] = {}
            for k, v in o.items():
                here = f"{path}.{k}"
                # a source's words; a claims row's statement too (a passage claim's: the sentence)
                source = k in SOURCE_TEXT_KEYS or (table == "claims" and k == "statement")
                if source and isinstance(v, str) and len(v) > DESK_QUOTE_MAX_CHARS:
                    v = desk_quote(v)[0]
                    cut[here] += 1
                elif k == "section" and isinstance(v, str) and len(v) > HEADING_MAX_CHARS:
                    v = None
                    cut[here] += 1
                out[k] = walk(v, here)
            return out
        if isinstance(o, list):
            return [walk(v, f"{path}[]") for v in o]
        if isinstance(o, str) and _ABS_PATH.search(o):
            cut[f"{path} (local path)"] += 1
            return public_path(o, data_dir)
        return o

    return walk(payload, table)
