"""NO LOCAL PATH IS STORED OR EXPORTED (operator, 2026-11-20: "No rewrite, fix paths ahead").

The registry of record is the `theme-intelligence-state` branch of this public repository, so a
path the registry stores is published. Three fields held one; at state a74c4e30 that was 77 fields
holding 92 path occurrences (review of #1143, findings 6 and 10):
- an article version's `evidence_location`: 17 absolute;
- a run's `output_dir`: 57 absolute or relative to a working directory;
- the tracebacks in a run's `warnings`: 3.

What this module does:
- **Where a path is CREATED** it is written relative to the data directory (`data_relative`). A
  traceback is scrubbed BEFORE its 1,500-character cut (`traceback_text`): a cut that falls
  inside `/Users/<name>` leaves `sers/<name>/…`, which no pattern written for whole paths
  recognizes.
- **An export** writes the rows stored before this change relative too (`exported_payload`). It
  touches those three fields only. The branch's history is not rewritten (the same ruling).
- **The guard** (`path_findings`, `export_findings`) refuses `export-state` and `state push` on
  any home-directory or username path shape anywhere in an export. It reads every string and never
  the rewrite's field list, so a path in a field the rewrite does not know is still refused.

Paths only: the operator ruled the same day that the licence covers publishing the reports' text
("Yes, full text may be public"), so nothing here cuts or drops source words.
"""

from __future__ import annotations

import json
import re
import site
import sys
import sysconfig
import traceback
from collections.abc import Iterator
from pathlib import Path
from typing import Any

#: the checkout this code runs from: a frame in it is named relative to it ("vinci/…", "tests/…")
REPO_ROOT = Path(__file__).resolve().parents[2]
#: a run's warning keeps the last this many characters of its traceback (the stored length)
TRACEBACK_CHARS = 1500
#: a path under no root this module knows keeps only its file name, after this
LOCAL = "⟨local path⟩"


def data_relative(path: Path | str, data_dir: Path) -> str:
    """`path` relative to the data directory, as stored ("runs/R-…", "http_cache/…"). A path
    outside it keeps its file name only, after `LOCAL`: it is never stored whole."""
    p = Path(path)
    try:
        return p.resolve().relative_to(Path(data_dir).resolve()).as_posix()
    except ValueError:
        return f"{LOCAL}/{p.name}"


def run_dir(data_dir: Path, run_id: str, stored: str | None) -> Path:
    """Where a run's readout is, from its stored `output_dir`:
    - stored relative ("runs/<run id>"), as since 2026-11-20 and as an export writes every run:
      under `data_dir`;
    - stored relative to some working directory before 2026-11-20 ("data/theme_intelligence/
      runs/<run id>"): still `data_dir`'s `runs/<run id>`, never the current directory's (#1143
      review, finding 10);
    - stored absolute before 2026-11-20: as it stands, on the machine that wrote it.
    """
    if not stored:
        return Path(data_dir) / "runs" / run_id
    p = Path(stored)
    if p.is_absolute():
        return p
    if p.parts[-2:] == ("runs", run_id):
        return Path(data_dir) / "runs" / run_id
    return Path(data_dir) / p


def _roots() -> list[tuple[str, str]]:
    """(root, the name it is shown as), longest root first: the checkout, then the Python
    installation's package and library folders."""
    paths = sysconfig.get_paths()
    pkgs = [*site.getsitepackages(), site.getusersitepackages(),
            paths.get("purelib", ""), paths.get("platlib", "")]
    found = [(str(REPO_ROOT), "")]
    found += [(p, "<site-packages>") for p in pkgs if p]
    found += [(paths.get(k, ""), "<python>") for k in ("stdlib", "platstdlib")]
    found += [(sys.prefix, "<python>"), (sys.base_prefix, "<python>")]
    roots: dict[str, str] = {}
    for root, label in found:
        if root:
            roots.setdefault(root.rstrip("/\\"), label)
    return sorted(roots.items(), key=lambda x: -len(x[0]))


def _file_name(path: str) -> str:
    """The last component of a POSIX or a Windows path."""
    return re.split(r"[\\/]", path)[-1]


def _absolute(name: str) -> bool:
    return name.startswith(("/", "\\")) or re.match(r"[A-Za-z]:[\\/]", name) is not None


def scrub_text(text: str) -> str:
    """`text` with every root this module knows replaced by its name, this machine's home
    directory by `LOCAL`, and any other home-directory or temporary path reduced to its file
    name: for an exception's MESSAGE, which can name a file on any machine."""
    for root, label in _roots():
        text = text.replace(root + "/", f"{label}/" if label else "")
    text = text.replace(str(Path.home()), LOCAL)
    return _HOME_PATH.sub(lambda m: _legacy_name(m.group(0)), text)


def traceback_text(limit: int = TRACEBACK_CHARS) -> str:
    """The exception being handled, its whole traceback scrubbed (`scrub_text`: each file named
    relative to the checkout or the Python installation, any other home-directory or temporary
    path reduced to its file name) and only THEN cut to its last `limit` characters. Scrubbed
    before the cut, a cut can never leave part of a home directory (#1143 review, finding 6: the
    old cut left one at 24 of 1,500 cut points)."""
    if sys.exc_info()[1] is None:
        return ""
    return scrub_text(traceback.format_exc())[-limit:]


# --- rows stored before 2026-11-20, written relative by an export --------------------------------

_ANCHORED = re.compile(r"^(?:.*?[\\/])?((?:vinci|tests|frontend|bin)[\\/].*)$")
_PKG = re.compile(r"^.*?[\\/]site-packages[\\/](.*)$")
_STDLIB = re.compile(r"^.*?[\\/]lib[\\/]python\d+(?:\.\d+)?[\\/](.*)$")
#: a file name in a traceback line, whole (`File "…"`) or cut at the traceback's start
_FRAME = re.compile(r'(?m)^(\s*File ")?([^"\n]*?)(", line \d+)')
#: a home-directory path anywhere else in a stored traceback or message
_HOME_PATH = re.compile(r"(?:[A-Za-z]:)?[\\/](?:Users|home|private|var[\\/]folders|tmp)[\\/]"
                        r"[^\s'\"<>()\[\]]+")


def _legacy_name(name: str) -> str:
    """A file name as a stored traceback held it, named the way `scrub_text` names one now:
    from the text alone, since the machine that wrote it is not this one."""
    if not re.search(r"[\\/]", name) or name.startswith("<"):
        return name
    for rx, label in ((_PKG, "<site-packages>"), (_STDLIB, "<python>"), (_ANCHORED, "")):
        m = rx.match(name)
        if m:
            rest = m.group(1).replace("\\", "/")
            return f"{label}/{rest}" if label else rest
    return f"{LOCAL}/{_file_name(name)}"


def legacy_traceback(text: str) -> str:
    """A stored warning with its traceback's files named relative, and any other home-directory
    path in it reduced the same way. A traceback cut before 2026-11-20 can start inside a path
    ('igence/vinci/…", line 1034'): its first line is read like any frame."""
    text = _FRAME.sub(lambda m: f"{m.group(1) or ''}{_legacy_name(m.group(2))}{m.group(3)}",
                      text)
    return _HOME_PATH.sub(lambda m: _legacy_name(m.group(0)), text)


def _legacy_location(value: str) -> str:
    """An `evidence_location` stored before 2026-11-20 (absolute, or relative to a working
    directory), relative to the data directory: from its last `http_cache` or `documents`."""
    parts = re.split(r"[\\/]", value)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] in ("http_cache", "documents"):
            return "/".join(parts[i:])
    return f"{LOCAL}/{parts[-1]}" if _absolute(value) else value


def exported_payload(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    """The payload an export writes: the SAME object when nothing changes, else a copy with the
    three path fields relative (a run's `output_dir` and `warnings`, a version's
    `evidence_location`). A row stored relative already is returned unchanged."""
    if table == "runs":
        out = dict(payload)
        od, rid = payload.get("output_dir"), payload.get("run_id")
        if isinstance(od, str) and isinstance(rid, str) and Path(od).parts[-2:] == ("runs", rid):
            out["output_dir"] = f"runs/{rid}"
        if isinstance(payload.get("warnings"), list):
            out["warnings"] = [legacy_traceback(w) if isinstance(w, str) else w
                               for w in payload["warnings"]]
        return out if out != payload else payload
    if table == "article_versions" and isinstance(payload.get("evidence_location"), str):
        loc = _legacy_location(payload["evidence_location"])
        if loc != payload["evidence_location"]:
            return {**payload, "evidence_location": loc}
    return payload


# --- the guard ------------------------------------------------------------------------------------

#: (what it is, its shape): a HOME DIRECTORY or a USERNAME, wherever it sits in a string. Never
#: every slash: "$40 /kW/month" and "(/kWh/yr)" are figures (#1143 review, finding 6).
PATH_SHAPES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("a macOS home directory", re.compile(r"/Users/[^/\s]")),
    ("a Windows home directory", re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]")),
    ("a Linux home directory", re.compile(r"(?:(?<![\w.-])|(?<=localhost))/home/[^/\s]+/")),
    ("a path from a home directory (~/)", re.compile(r"(?:^|[\s\"'(\[=`:])~/\S")),
    ("a network share", re.compile(r"\\\\[\w.$-]+\\[\w.$-]+")),
    ("a session folder named from a home directory", re.compile(r"-Users-[\w.]+-")),
    ("a home-directory path cut at its start",
     re.compile(r"(?m)^\s*(?:U?s?ers|h?ome|rs|me)/[^/\s\"']+/")),
)


def path_findings(text: str) -> list[str]:
    """The home-directory or username path shapes `text` holds: their names, never the path."""
    found = [name for name, rx in PATH_SHAPES if rx.search(text)]
    if str(Path.home()) in text:
        found.append("this machine's home directory")
    return found


def _strings(obj: Any, path: str) -> Iterator[tuple[str, str]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v, f"{path}[]")
    elif isinstance(obj, str):
        if obj[:1] in "[{":
            try:
                yield from _strings(json.loads(obj), path)
                return
            except ValueError:
                pass
        yield path, obj


def export_findings(export_dir: Path) -> list[str]:
    """Every string in every JSONL file of an export that holds a path shape, as "<file> <the
    row's first value> <field>: <shape>". Read from the files, independently of
    `exported_payload`: a path in a field the rewrite does not know is refused too."""
    out: list[str] = []
    for f in sorted(Path(export_dir).glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            key = (next((str(v) for k, v in row.items() if k.endswith("_id")), "")
                   if isinstance(row, dict) else "")
            for field, s in _strings(row, ""):
                out += [f"{f.name} {key} {field}: {shape}" for shape in path_findings(s)]
    return out
