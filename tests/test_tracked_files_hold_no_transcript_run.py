"""THE 12-WORD RULE ON EVERY TRACKED FILE, AGAINST THE CALLS ON THIS DISK (operator ruling
2026-11-12, verbatim "Cut all 21 + guard (Recommended)": "A local-only test scans every tracked
file against the transcripts on disk, and skips in CI where they are absent").

CLAUDE.md: NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS, and this repo is
public. `test_public_transcript_text.py` holds the rule where code knows a field is transcript
text, and `synthesis._validate` holds it on a synthesis at build (#1036). Neither reads a record, a
test, a fixture or a comment against the calls themselves. An audit of main `407dc809` did: 21
runs of 13 or more of a call's words sat in five records written before the rule and in three
tests, and none of them was caught. This reads every tracked text file against every call it can
read here, and fails on any window of 13 consecutive words that a file shares with one.

LOCAL ONLY. The calls are licensed and never in git, so CI has none and this SKIPS there, saying
so. On a machine that holds them it runs, and prints its own boundary: calls read and unreadable,
excuse sources read and unreadable, files scanned and skipped, each with its reason.

WHERE THE CALLS ARE. The store production reads (`data/manual/ciq/<T>/`, `LocalFolderStore`), its
`ciq-archive/` of replaced exports (the rule `ciq_export_support.archive_roots` follows), and any
folder named in `VINCI_TRANSCRIPT_ROOTS` (separated by `os.pathsep`). A call is a file
`ciq.workbook_kind` names "transcript", read by production's reader `ciq.read_text`; one that does
not read is counted unreadable and named, never skipped quietly.

A WORD, as #1036's build guard counts it, read for files rather than for a synthesis: split at
whitespace, at every dash form and at a slash; lower-cased; apostrophes and primes folded; edge
punctuation read off, the markdown and code marks among it (`*`, `` ` ``, `$`, `%`). Each tracked
file is read raw, JSON/JS-unescaped where it holds a backslash, HTML-unescaped with its tags
dropped where it holds `<` or `&`, with each Markdown link read as its text, and, for a `.py` file,
as its string literals joined, so a run escaped, marked up, linked or split in one view is found in
another. A call on disk that does not read FAILS the test: only a disk with no call skips.

THE EXCUSE. Management reads its release on the call, so a filing's sentence is often a call's too.
A window is excused ONLY when this COMPUTES that it also appears in a source on this disk that is
not a transcript:
- an SEC document in the HTTP cache (`data/cache/sec`, `vinci.netcache`), or
- a CIQ Key Developments export in the store or its archive. These are COUNTED APART, because
  whether KD text may be public is the operator's separate, unruled question (STATE row 60,
  item 3b).
A window found in neither FAILS: an unconfirmable window never passes. No word of any call is
written here. A run is named by its file, line, length, call, offset and hash.

WHAT IT REMEMBERS. Production's reader converts each call through LibreOffice (about 1.4 s a call),
and folding every tracked file takes about 20 s. pytest's own git-ignored cache
(`.pytest_cache/`) therefore keeps three things:
- each call's window HASHES, keyed by the call's sha256 and by the fold's and `ciq.py`'s source;
- each tracked file's hits, keyed by its content hash and by the set of calls;
- where each window was last found outside a call.
It holds no word. Every excuse is recomputed from its source on each run. A changed fold, reader,
call set or file is read afresh.
"""

from __future__ import annotations

import hashlib
import html
import inspect
import io
import json
import os
import re
import string
import subprocess
import sys
import tokenize
from array import array
from base64 import b64decode, b64encode
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from tests.ciq_export_support import archive_roots
from vinci.config import get_config
from vinci.dossier.ciq import CiqParseError, read_sheets, read_text, workbook_kind
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.synthesis import MAX_TRANSCRIPT_RUN

ROOT = Path(__file__).resolve().parents[1]
#: a window one word longer than the rule allows
N = MAX_TRANSCRIPT_RUN + 1

#: a word's edge marks, read off before words are compared: punctuation, quote marks, dashes,
#: and the marks a markdown or code file wraps a quotation in
_EDGE = string.punctuation + "“”‘’«»…—–‐‑‒―−•·§¶©®™°′″‵‹›„‚¡¿​﻿"
#: A WORD ENDS at whitespace, at every dash form and at a slash (#1036's conservative reading)
_SPLIT = re.compile(r"[\s\-‐-―−/]+")
_APOS = str.maketrans(dict.fromkeys("’‘′″‵ʹʼ", "'"))
_ESC = re.compile(r"\\u([dD][89abAB][0-9a-fA-F]{2})\\u([dD][c-fC-F][0-9a-fA-F]{2})"
                  r"|\\u([0-9a-fA-F]{4})|\\([nrt])|\\([\"\\/'])")
_TAG = re.compile(r"<[^>\n]*>")
#: the letters-only words an excuse source is prefiltered on
_LETTERS = re.compile(r"[a-z]{5,}")
#: a JSON escape in a cached body's raw text: read as a space before the prefilter, or the letter
#: it ends in glues onto the next word (`\nmanagement` and `“management` hide "management")
_JSON_ESC = re.compile(r"\\(?:u[0-9a-fA-F]{4}|.)")
_SEC_DOC = re.compile(r"^https://www\.sec\.gov/Archives/edgar/data/")
#: a file must state its own source to be trusted as a source: the cache's own record shape
_CACHE_URL = re.compile(r'^\{"url": "([^"]+)"')


def _unescape(m: re.Match[str]) -> str:
    if m.group(1):
        hi, lo = int(m.group(1), 16), int(m.group(2), 16)
        return chr(0x10000 + ((hi - 0xD800) << 10) + (lo - 0xDC00))
    if m.group(3):
        c = chr(int(m.group(3), 16))
        return " " if c in "\n\r\t" else c
    if m.group(4):
        return " "
    return m.group(5)


def views(text: str, py: bool = False) -> list[str]:
    """``text`` raw, JSON/JS-unescaped where it holds a backslash, HTML-unescaped with tags dropped
    where it holds markup, and with each Markdown link read as its text where it holds one. A
    Python file is also read as the string literals the code JOINS at run time (`py_strings`).
    Newlines are kept in each, so a line is the file's own."""
    out, base = [text], text
    if "\\" in text:
        unescaped = _ESC.sub(_unescape, text)
        if unescaped != text:
            out.append(unescaped)
            base = unescaped
    if "<" in base or "&" in base:
        stripped = _TAG.sub(" ", html.unescape(base).replace("\r", ""))
        if stripped != base:
            out.append(stripped)
    if "](" in base:
        # A MARKDOWN LINK reads as its text (Codex on #1046, P2): one word written `[word](url)`
        # was read as "word](https:" and broke the run around it
        linked = _MD_LINK.sub(lambda m: m.group(1), base)
        if linked != base:
            out.append(linked)
    if py and (joined := py_strings(text)) is not None:
        out.append(joined)
    return out


#: a Markdown link or image, `[text](url)` / `![alt](url "title")`: read as its text
_MD_LINK = re.compile(r"!?\[([^\]\n]*)\]\([^()\s]*(?:\s+\"[^\"\n]*\")?\)")
#: a string token's prefix (`f`, `r`, `b`, `rb`, …) and its opening quote
_STR_OPEN = re.compile(r"^([A-Za-z]*)(\"\"\"|\'\'\'|\"|\')")
#: a replacement field of an f-string read as ONE token (Python < 3.12): `{q}`, `{x!r:>10}`
_FIELD = re.compile(r"(?<!\{)\{[^{}]*\}(?!\})")
#: Python 3.12+ reads an f-string as start, text parts, fields and end (`FSTRING_*`; 3.14 adds
#: t-strings, `TSTRING_*`); older Pythons read it as one STRING token
_FSTRING_PARTS, _FSTRING_START, _FSTRING_END = (
    {getattr(tokenize, f"{k}_{part}") for k in ("FSTRING", "TSTRING")
     if hasattr(tokenize, f"{k}_{part}")} for part in ("MIDDLE", "START", "END"))


def py_strings(text: str) -> str | None:
    """A Python file's string literals as the code JOINS them, or None when it does not tokenize.

    REVIEW ROUND 1 of #1046 (operator ruling 2026-11-13, "Cut 27 + widen guard (Recommended)").
    Two runs of 20 and 13 call words sat in `tests/test_following_context.py` as two literals each
    (`q = "…"` then `tail = "…"`, and `q` inside an f-string after a blank line), and every other
    view read them as two short runs: an identifier between the strings, or an `f"` glued onto the
    first word, broke each. Here everything that is not a literal's own text is blanked (names,
    operators, comments, the `f`/`r`/`b` prefixes, the quotes, an f-string's `{…}` fields) and its
    newlines kept, so the joined words read as one run on the line each starts on. Escapes are read
    as the JSON view reads them."""
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        return None
    if any(t.type == tokenize.ERRORTOKEN and t.string.strip() for t in toks):
        return None  # an older tokenizer's way of saying the same
    starts = [0]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    chars = [c if c == "\n" else " " for c in text]

    def keep(a: int, b: int, piece: str) -> None:
        chars[a:b] = list(piece)

    depth: list[int] = []  # per open f-string: how deep in `{…}` fields its tokens sit
    for t in toks:
        a = starts[t.start[0] - 1] + t.start[1]
        b = starts[t.end[0] - 1] + t.end[1]
        if t.type in _FSTRING_START:
            depth.append(0)
        elif t.type in _FSTRING_END and depth:
            depth.pop()
        elif depth and t.type == tokenize.OP and t.string in "{}":
            depth[-1] += 1 if t.string == "{" else -1
        elif t.type in _FSTRING_PARTS:
            if depth and depth[-1] == 0:  # its text; inside a field it is a format spec
                keep(a, b, text[a:b])
        elif t.type == tokenize.STRING and (m := _STR_OPEN.match(t.string)):
            body_a, body_b = a + m.end(), b - len(m.group(2))
            body = text[body_a:body_b]
            if "f" in m.group(1).lower():
                body = _FIELD.sub(lambda f: " " * len(f.group()), body)
            keep(body_a, body_b, body)
    joined = "".join(chars)
    return _ESC.sub(_unescape, joined) if "\\" in joined else joined


def words(text: str) -> tuple[list[str], list[int]]:
    """Each word of ``text`` as this guard counts it, and the line it is on."""
    toks: list[str] = []
    lines: list[int] = []
    for ln, line in enumerate(text.translate(_APOS).lower().split("\n"), 1):
        for chunk in _SPLIT.split(line):
            w = chunk.strip(_EDGE)
            if w:
                toks.append(w)
                lines.append(ln)
    return toks, lines


_KEYS: dict[str, int] = {}


def key(word: str) -> int:
    """A word's stable 64-bit key. A window's key is the hash of its 13 keys as a tuple, which is
    stable across processes (an int's hash is its value) within one Python version."""
    k = _KEYS.get(word)
    if k is None:
        k = _KEYS[word] = int.from_bytes(
            hashlib.blake2b(word.encode(), digest_size=8).digest(), "big", signed=True)
    return k


def window_keys(ks: list[int]) -> list[int]:
    return [hash(tuple(ks[i:i + N])) for i in range(len(ks) - N + 1)]


def run_hash(ws: Iterable[str]) -> str:
    """How a run is named in a record, a log or a PR: the sha256 of its words joined by single
    spaces, its first 16 hex digits."""
    return hashlib.sha256(" ".join(ws).encode()).hexdigest()[:16]


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _source_sha() -> str:
    """What a remembered result depends on: the fold (its code and constants), production's
    reader's source and the Python version (a window key is a tuple hash). A change to any of them
    reads afresh; an edit elsewhere in this file does not."""
    h = hashlib.sha256()
    for f in (_unescape, views, py_strings, words, key, window_keys, scan_text):
        h.update(inspect.getsource(f).encode())
    h.update(f"{N}|{_EDGE}|{_SPLIT.pattern}|{_APOS}|{_ESC.pattern}|{_TAG.pattern}|"
             f"{_STR_OPEN.pattern}|{_FIELD.pattern}|{_MD_LINK.pattern}".encode())
    h.update((ROOT / "vinci/dossier/ciq.py").read_bytes())
    h.update(f"{sys.version_info[0]}.{sys.version_info[1]}".encode())
    return h.hexdigest()[:20]


# --- the calls ------------------------------------------------------------------------------------

def call_roots() -> list[Path]:
    """Where calls are looked for: the store, its archive and `VINCI_TRANSCRIPT_ROOTS`."""
    store = Path(LocalFolderStore.from_config(get_config()).location("X")).parent
    roots = [store, *archive_roots("X")]
    roots += [Path(p) for p in os.environ.get("VINCI_TRANSCRIPT_ROOTS", "").split(os.pathsep) if p]
    out: list[Path] = []
    for r in roots:
        if r.is_dir() and all(r.resolve() != s.resolve() for s in out):
            out.append(r)
    return out


def _files_of_kind(roots: list[Path], kind: str) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        for dp, _dn, fn in os.walk(root):
            out += [Path(dp) / f for f in sorted(fn)
                    if not f.startswith((".", "~$")) and workbook_kind(f) == kind]
    return sorted(out)


@dataclass
class Call:
    name: str
    sha256: str
    windows: array[int]


@dataclass
class Calls:
    calls: list[Call]
    vocab: set[int]
    index: set[int]
    unreadable: list[tuple[str, str]]
    duplicates: int


def read_calls(roots: list[Path], cache: Any) -> Calls:
    """Every call under ``roots``, as window keys (cached by the call's sha256), deduplicated by
    sha256. A call whose bytes or text do not read is named with its reason."""
    seen: dict[str, Call] = {}
    vocab: set[int] = set()
    unreadable: list[tuple[str, str]] = []
    dup = 0
    src = _source_sha()
    for p in _files_of_kind(roots, "transcript"):
        try:
            b = p.read_bytes()
        except OSError as exc:
            unreadable.append((p.name, f"{type(exc).__name__}: {exc.strerror or exc}"))
            continue
        sha = _sha256(b)
        if sha in seen:
            dup += 1
            continue
        got = cache.get(f"transcript-runs/call/{sha}", None) if cache else None
        if got and got.get("src") == src:
            ws = array("q", b64decode(got["w"]))
            vs = array("q", b64decode(got["v"]))
        else:
            try:
                text = read_text(p)
            except (CiqParseError, OSError, UnicodeDecodeError) as exc:
                unreadable.append((p.name, f"{type(exc).__name__}: {str(exc)[:160]}"))
                continue
            ks = [key(w) for w in words(text)[0]]
            ws = array("q", window_keys(ks))
            vs = array("q", sorted(set(ks)))
            if cache:
                cache.set(f"transcript-runs/call/{sha}", {
                    "src": src, "w": b64encode(ws.tobytes()).decode(),
                    "v": b64encode(vs.tobytes()).decode()})
        seen[sha] = Call(p.name, sha, ws)
        vocab.update(vs)
    calls = list(seen.values())
    index = {w for c in calls for w in c.windows}
    return Calls(calls, vocab, index, unreadable, dup)


# --- the tracked files --------------------------------------------------------------------------

@dataclass(frozen=True)
class Hit:
    view: int
    line: int
    pos: int
    window: int


def scan_text(text: str, calls: Calls, py: bool = False) -> list[Hit]:
    """Every window of 13 words that ``text`` (each of its views; ``py``: a Python file's joined
    literals too) shares with a call."""
    out: list[Hit] = []
    for vi, v in enumerate(views(text, py)):
        toks, lines = words(v)
        ks = [key(t) for t in toks]
        known = [k in calls.vocab for k in ks]
        i, n = 0, len(ks)
        while i < n:
            if not known[i]:
                i += 1
                continue
            j = i
            while j < n and known[j]:
                j += 1
            for p in range(i, j - N + 1):
                w = hash(tuple(ks[p:p + N]))
                if w in calls.index:
                    out.append(Hit(vi, lines[p], p, w))
            i = j
    return out


@dataclass
class Run:
    """Consecutive windows of one view of one file: a run of ``len(windows) + 12`` words."""
    path: str
    line: int
    view: int
    pos: int
    windows: list[int]
    #: the run's words, from the tracked file, for the excuse's prefilter: kept out of the repr,
    #: so a failure printed with `--showlocals` carries no word of a call
    words: list[str] = field(default_factory=list, repr=False)

    @property
    def length(self) -> int:
        return len(self.windows) + N - 1


def group_runs(path: str, hits: list[Hit]) -> list[Run]:
    """``hits`` as runs. A run is dropped only when every window it holds is held by a longer run
    kept on its line (one run read in two views, raw and unescaped), so no window goes unchecked;
    two runs on one line are two runs, even when they open with the same words."""
    by: dict[int, list[Hit]] = defaultdict(list)
    for hit in hits:
        by[hit.view].append(hit)
    found: list[Run] = []
    for vi, hs in by.items():
        hs.sort(key=lambda x: x.pos)
        group = [hs[0]]
        tail: list[Hit | None] = [*hs[1:], None]
        for h in tail:
            if h is not None and h.pos == group[-1].pos + 1:
                group.append(h)
                continue
            found.append(Run(path, group[0].line, vi, group[0].pos, [g.window for g in group]))
            if h is not None:
                group = [h]
    kept: list[Run] = []
    for r in sorted(found, key=lambda r: -r.length):
        held = {w for k in kept if k.line == r.line for w in k.windows}
        if not set(r.windows) <= held:
            kept.append(r)
    return sorted(kept, key=lambda r: (r.line, r.pos))


@dataclass
class Scan:
    runs: list[Run]
    scanned: int
    skipped: dict[str, list[str]]


def tracked_files() -> list[str]:
    """Every file git tracks, and every file it would offer to (untracked and not ignored): a
    record written and not yet staged is read before it can be committed, not after."""
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, check=True)
    return sorted({f for f in out.stdout.decode().split("\0") if f})


def scan_tracked(calls: Calls, cache: Any, files: list[str] | None = None) -> Scan:
    """Every tracked file (or ``files``) read against ``calls``. A file's hits are remembered by
    its content hash and the call set, so only a changed file is folded again."""
    fp = hashlib.sha256((_source_sha() + "".join(sorted(c.sha256 for c in calls.calls)))
                        .encode()).hexdigest()[:20]
    memo = (cache.get("transcript-runs/files", None) if cache else None) or {}
    known: dict[str, list[list[int]]] = memo.get("files", {}) if memo.get("fp") == fp else {}
    fresh: dict[str, list[list[int]]] = {}
    skipped: dict[str, list[str]] = defaultdict(list)
    runs: list[Run] = []
    scanned = 0
    for f in files if files is not None else tracked_files():
        p = ROOT / f
        if p.is_symlink() or not p.is_file():
            skipped["not a regular file"].append(f)
            continue
        b = p.read_bytes()
        if b"\x00" in b[:8192]:
            skipped["binary (a NUL byte)"].append(f)
            continue
        try:
            text = b.decode("utf-8")
        except UnicodeDecodeError:
            skipped["not UTF-8"].append(f)
            continue
        scanned += 1
        ck = hashlib.blake2b(b, digest_size=16).hexdigest()
        if ck in known:
            raw = known[ck]
        else:
            raw = [[h.view, h.line, h.pos, h.window]
                   for h in scan_text(text, calls, f.endswith(".py"))]
        fresh[ck] = raw
        if raw:
            got = group_runs(f, [Hit(*h) for h in raw])
            vs = views(text, f.endswith(".py"))
            for r in got:
                r.words = words(vs[r.view])[0][r.pos:r.pos + r.length]
            runs += got
    if cache:
        cache.set("transcript-runs/files", {"fp": fp, "files": fresh})
    return Scan(runs, scanned, dict(skipped))


# --- the excuse ---------------------------------------------------------------------------------

@dataclass
class Sources:
    """Where windows were found outside a call — an SEC document (by URL) or a Key Developments
    export (by file) — and what was read, and what could not be."""
    sec: dict[int, str]
    kd: dict[int, str]
    read: dict[str, int]
    unreadable: dict[str, list[str]]


def _kd_text(p: Path) -> str:
    try:
        return read_text(p)
    except CiqParseError:
        # a Key Developments export saved as a workbook: its text cells, a row to a line
        return "\n".join(" ".join(str(c) for c in row if isinstance(c, str))
                         for rows in read_sheets(p).values() for row in rows)


def _sec_doc(raw: str) -> str | None:
    """The URL of a cached SEC Archives DOCUMENT (not an index or a JSON API reply), else None."""
    m = _CACHE_URL.match(raw)
    if not m or not _SEC_DOC.match(m.group(1)) or m.group(1).endswith((".json", ".xml")):
        return None
    return m.group(1)


def _windows_of(text: str) -> set[int]:
    out: set[int] = set()
    for v in views(text):
        out.update(window_keys([key(w) for w in words(v)[0]]))
    return out


def _listing(sec_dir: Path) -> str:
    """The cache's listing (names, sizes) and the search's own code: what a full read did not find
    stays unfound while both hold, so a changed prefilter reads afresh."""
    h = hashlib.sha256()
    h.update(f"{inspect.getsource(find_outside_calls)}|{_LETTERS.pattern}|{_JSON_ESC.pattern}"
             .encode())
    for p in sorted(sec_dir.iterdir()):
        h.update(f"{p.name}:{p.stat().st_size};".encode())
    return h.hexdigest()[:20]


def find_outside_calls(pending: dict[int, list[str]], kd: list[Path], sec_dir: Path | None,
                       cache: Any) -> Sources:
    """Where each window of ``pending`` (key → its 13 words) appears outside a call, COMPUTED
    from each source's text on every run:
    1. every Key Developments export (they are few);
    2. the cached SEC document where the window was found last time, read again;
    3. every cached SEC document, for what is still unfound — prefiltered on one long word of each
       window, since a document without that word cannot hold the window. A window this full read
       did not find is remembered as absent only while the cache's listing is unchanged AND every
       file in it read, so a file that comes back from offload is read again.
    A window both a KD export and an SEC document hold is the SEC document's: KD's publication is
    unruled, so a KD-only excuse is reported apart."""
    sec: dict[int, str] = {}
    kd_found: dict[int, str] = {}
    read: dict[str, int] = defaultdict(int)
    unreadable: dict[str, list[str]] = defaultdict(list)
    memo: dict[str, Any] = (cache.get("transcript-runs/sources", None) if cache else None) or {}
    remembered: dict[str, str] = dict(memo.get("sec", {}))

    for p in kd:
        try:
            hit = _windows_of(_kd_text(p)) & pending.keys()
        except (CiqParseError, OSError, UnicodeDecodeError) as exc:
            unreadable["KD"].append(f"{p.name} ({type(exc).__name__})")
            continue
        read["KD"] += 1
        for w in hit:
            kd_found.setdefault(w, p.name)

    def sec_read(p: Path) -> str | None:
        try:
            return p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            unreadable["SEC"].append(f"{p.name} ({type(exc).__name__})")
            return None

    def sec_look(raw: str, url: str, want: set[int]) -> None:
        try:
            body = json.loads(raw).get("text")
        except ValueError:
            unreadable["SEC"].append(f"{url} (not JSON)")
            return
        if not isinstance(body, str):
            return
        read["SEC"] += 1
        for w in _windows_of(body) & want:
            sec[w] = url
            want.discard(w)

    want = set(pending)
    if sec_dir is not None and sec_dir.is_dir():
        for url in sorted({remembered[str(w)] for w in want if str(w) in remembered}):
            p = sec_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.json"
            raw = sec_read(p) if p.is_file() else None
            if raw is not None and _sec_doc(raw) == url:
                sec_look(raw, url, want)
        listing = _listing(sec_dir)
        absent = set(memo.get("absent", [])) if memo.get("listing") == listing else set()
        todo = want - absent
        if todo:
            # an ASCII word only: a cached body is JSON, which escapes any other letter
            anchors = {w: max((x for x in pending[w] if x.isascii() and x.isalpha()
                               and len(x) >= 5), key=len, default="") for w in todo}
            failed = len(unreadable.get("SEC", []))
            for p in sorted(sec_dir.iterdir()):
                if not todo:
                    break
                raw = sec_read(p)
                doc = _sec_doc(raw) if raw is not None else None
                if raw is None or doc is None:
                    continue
                present = set(_LETTERS.findall(_JSON_ESC.sub(" ", raw).lower()))
                if any(not a or a in present for w, a in anchors.items() if w in todo):
                    sec_look(raw, doc, todo)
            if len(unreadable.get("SEC", [])) == failed:
                absent |= todo
            memo["listing"], memo["absent"] = listing, sorted(absent)
    if cache:
        remembered.update({str(w): url for w, url in sec.items()})
        memo["sec"] = remembered
        cache.set("transcript-runs/sources", memo)
    return Sources(sec, {w: f for w, f in kd_found.items() if w not in sec}, dict(read),
                   dict(unreadable))


# --- the report ---------------------------------------------------------------------------------

def origin(calls: Calls, ws: set[int]) -> dict[int, tuple[str, int]]:
    """Each window's first place in the calls: (call file, word offset)."""
    out: dict[int, tuple[str, int]] = {}
    for c in calls.calls:
        for i, w in enumerate(c.windows):
            if w in ws and w not in out:
                out[w] = (c.name, i)
    return out


def _shown(items: list[str], n: int = 12) -> str:
    return "\n".join(items[:n]) + (f"\n… showing {min(n, len(items))} of {len(items)}"
                                   if len(items) > n else "")


def _excuses(scan: Scan, roots: list[Path], cache: Any) -> Sources:
    """Every window of ``scan``'s runs looked for outside the calls. Its words stay in this frame,
    never the test's, so no failure report can print one."""
    pending = {w: r.words[i:i + N] for r in scan.runs for i, w in enumerate(r.windows)}
    sec = get_config().cache_dir / "sec"
    return find_outside_calls(pending, _files_of_kind(roots, "key_developments"),
                              sec if sec.is_dir() else None, cache)


def _cache(request: pytest.FixtureRequest) -> Any:
    return getattr(request.config, "cache", None)


def _say(request: pytest.FixtureRequest, *lines: str) -> None:
    """The boundary, on the terminal whatever the capture mode. NOT through `capsys`: this test is
    where `xlrd` is first imported (a KD export read as a workbook), and xlrd binds `sys.stdout`
    as its default log file at import. Under `capsys` that is the fixture's buffer, closed when the
    test ends, so every later test whose workbook makes xlrd warn raised `ValueError: I/O
    operation on closed file` in place of its own error."""
    tr = request.config.pluginmanager.get_plugin("terminalreporter")
    if tr is None:
        print("\n".join(lines))
        return
    tr.ensure_newline()
    for line in lines:
        tr.write_line(line)


def test_no_tracked_file_shares_13_consecutive_words_with_a_call(
        request: pytest.FixtureRequest) -> None:
    roots = call_roots()
    cache = _cache(request)
    calls = read_calls(roots, cache)
    if not calls.calls and not calls.unreadable:
        pytest.skip(f"no transcript on this disk under {[str(r) for r in roots] or 'no root'} "
                    "(CI holds none): the 12-word rule on tracked files is checked only where the "
                    "licensed calls are")
    scan = scan_tracked(calls, cache)
    sources = _excuses(scan, roots, cache)
    where = origin(calls, {w for r in scan.runs for w in r.windows})
    bad, kd_runs, sec_runs = [], [], []
    for r in scan.runs:
        miss = [w for w in r.windows if w not in sources.sec and w not in sources.kd]
        name, off = where[r.windows[0]]
        tag = (f"{r.path}:{r.line} — {r.length} words, {len(miss)} of {len(r.windows)} window(s) "
               f"in no non-transcript source; call {name!r} at word {off:,}; run sha256 "
               f"{run_hash(r.words)}")
        if miss:
            bad.append(tag)
        elif any(w in sources.kd for w in r.windows):
            kd_runs.append(r)
        else:
            sec_runs.append(r)
    skipped = ", ".join(f"{len(v)} {k}" + (f" ({', '.join(v)})" if len(v) <= 3 else "")
                        for k, v in sorted(scan.skipped.items()))
    boundary = (
        f"transcript-run guard — roots: {', '.join(str(r) for r in roots)}\n"
        f"  calls: {len(calls.calls)} read ({calls.duplicates} duplicate file(s) by sha256), "
        f"{len(calls.unreadable)} unreadable"
        + "".join(f"\n    unreadable: {n} — {why}" for n, why in calls.unreadable)
        + f"\n  tracked files (and untracked, not ignored): {scan.scanned} scanned; skipped: "
          f"{skipped or 'none'}"
        + f"\n  runs of {N}+ words shared with a call: {len(scan.runs)} "
          f"({len({w for r in scan.runs for w in r.windows})} distinct windows)"
        + f"\n  excused by an SEC document in the cache: {len(sec_runs)} run(s)"
        + "\n  excused by a CIQ Key Developments export (KD's publication is unruled, STATE row "
          f"60 item 3b): {len(kd_runs)} run(s)"
        + f"\n  excuse sources read: {sources.read or 'none'}; unreadable: "
        + (", ".join(f"{len(v)} {k}" for k, v in sources.unreadable.items()) or "none")
        + f"\n  unexcused: {len(bad)} run(s)")
    _say(request, boundary, *(f"    KD-excused: {r.path}:{r.line} ({r.length} words, run sha256 "
                              f"{run_hash(r.words)})" for r in kd_runs))
    # FAIL LOUD (Codex on #1046, P1): a call that is on disk and does not read was never looked
    # for, so a run of its words would pass unseen. Only a disk with NO call skips (CI).
    assert not calls.unreadable, (
        f"{len(calls.unreadable)} call(s) on this disk do not read, so no tracked file was read "
        "against them, and a call left out of the scan is never a pass:\n"
        + _shown([f"{n} — {why}" for n, why in calls.unreadable]) + "\n" + boundary)
    assert not bad, (f"{len(bad)} run(s) of more than {MAX_TRANSCRIPT_RUN} consecutive words of a "
                     "call sit in tracked files, and no non-transcript source on this disk holds "
                     "them (CLAUDE.md's 12-word rule):\n" + _shown(bad) + "\n" + boundary)


# --- the guard bites ------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def local_calls(request: pytest.FixtureRequest) -> Calls:
    calls = read_calls(call_roots(), _cache(request))
    if not calls.calls:
        pytest.skip("no transcript on this disk (CI holds none)")
    return calls


def _call_words(roots: list[Path]) -> list[str]:
    """One readable call's words, read at run time and never written anywhere."""
    for p in _files_of_kind(roots, "transcript"):
        try:
            ws = words(read_text(p))[0]
        except (CiqParseError, OSError, UnicodeDecodeError):
            continue
        if len(ws) > 400:
            return ws
    pytest.skip("no call on this disk reads to 400 words")


#: CLAUDE.md's number plus one, written out: a pin that read `N` would move with the code it pins
_RULE_PLUS_ONE = 13


def _bites(local_calls: Calls, at: int) -> dict[str, bool]:
    """Each bite pin's outcome by its label, on 13 words of a real call read at run time. The words
    stay in this frame: a failed pin prints its label and a boolean, never a call's word."""
    ws = _call_words(call_roots())[at:at + _RULE_PLUS_ONE]

    def caught(text: str) -> bool:
        return bool(scan_text(text, local_calls))

    escaped = json.dumps({"q": "\n".join(w.upper() for w in ws)})
    return {
        "13 words in a code comment": caught(f"# {' '.join(ws)}\n"),
        "13 words behind markdown marks, across a line": caught(
            f'> *"**{" ".join(ws[:6])}**\n> {" ".join(ws[6:])}"*'),
        "13 words in a JSON string, escaped and upper-cased": "\\n" in escaped and caught(escaped),
        "13 words joined by bare dashes": caught("—".join(ws)),
        "12 words": caught(f"# {' '.join(ws[:12])}\n"),
        "13 words with the 7th changed": caught(" ".join([*ws[:6], "zzqx", *ws[7:]])),
    }


def test_thirteen_words_of_a_call_are_caught_and_twelve_are_not(local_calls: Calls) -> None:
    """The positive and negative pins, on a REAL call read at run time (no call word is written
    here): 13 consecutive words are a run wherever they sit (in a code comment, behind markdown
    marks, JSON-escaped, joined by dashes, broken across lines); 12 are not; a word changed in the
    middle ends it."""
    assert _bites(local_calls, 200) == {
        "13 words in a code comment": True,
        "13 words behind markdown marks, across a line": True,
        "13 words in a JSON string, escaped and upper-cased": True,
        "13 words joined by bare dashes": True,
        "12 words": False,
        "13 words with the 7th changed": False,
    }


def _excused(local_calls: Calls, folder: Path, at: int) -> dict[str, bool]:
    """Each excuse pin's outcome by its label (13 words of a real call, held in this frame only).
    The sources it writes hold a call's words, so they are removed before it returns."""
    ws = _call_words(call_roots())[at:at + _RULE_PLUS_ONE]
    w = window_keys([key(x) for x in ws])[0]
    url = "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/ex99.htm"
    name = f"{hashlib.sha256(url.encode()).hexdigest()}.json"
    sec, short, lined = folder / "sec", folder / "short", folder / "lined"
    for d in (sec, short, lined):
        d.mkdir()
    kd = folder / "Acme Inc NYSE ACME Key Developments.rtf"
    try:
        (sec / name).write_text(json.dumps(
            {"url": url, "fetched_at": 0, "text": f"<p>{' '.join(ws)}</p>"}))
        (short / name).write_text(json.dumps(
            {"url": url, "fetched_at": 0, "text": " ".join(ws[:12])}))
        # every word after a line break: JSON writes `\n` before each, gluing an `n` onto it
        (lined / name).write_text(json.dumps(
            {"url": url, "fetched_at": 0, "text": "".join(f"\n“{x}" for x in ws)}))
        kd.write_text("{\\rtf1\\ansi " + " ".join(ws) + "}")
        both = find_outside_calls({w: ws}, [kd], sec, None)
        return {
            "an SEC document holding the window excuses it, by its URL":
                find_outside_calls({w: ws}, [], sec, None).sec == {w: url},
            "no source excuses nothing": find_outside_calls({w: ws}, [], None, None).sec == {},
            "a source holding 12 of its words excuses nothing":
                find_outside_calls({w: ws}, [], short, None).sec == {},
            "a KD export excuses it, reported apart":
                find_outside_calls({w: ws}, [kd], None, None).kd == {w: kd.name},
            "held by both, it is the SEC document's": both.sec == {w: url} and both.kd == {},
            "an SEC document holding it with each word after a JSON escape excuses it":
                find_outside_calls({w: ws}, [], lined, None).sec == {w: url},
        }
    finally:
        for f in (sec / name, short / name, lined / name, kd):
            f.unlink(missing_ok=True)


def test_a_window_is_excused_only_where_a_source_holds_it(local_calls: Calls,
                                                          tmp_path: Path) -> None:
    """The excuse is computed: a window an SEC document in the cache holds is excused and named;
    the same window with no source is not, and a source holding only 12 of its words excuses
    nothing. A Key Developments export excuses too, reported apart, and where an SEC document
    holds the same window the excuse is the document's (KD's publication is unruled). A document
    whose words each follow a JSON escape (`\\n`, `\\u201c`) still excuses it: the prefilter reads
    the escape as a space, never as a letter glued to the word."""
    got = _excused(local_calls, tmp_path, 300)
    assert got == dict.fromkeys(got, True)
    assert len(got) == 6


#: #1036's parent, which still held the three synthesis claims #1036 cut: LLY `bull_points[5]`
#: (14 words), VITL `bull_points[2]` (13) and WERN `bull_points[5]` (14), in these files.
_PARENT_1036 = "68bd4b33f3af8e14e575c901eb28085d9e564d03"
_FILES_1036 = (
    "data/dossiers/LLY/dossier.json", "data/dossiers/LLY/dossier.md",
    "data/dossiers/VITL/dossier.json", "data/dossiers/WERN/dossier.json",
    "data/dossiers/WERN/dossier.md", "frontend/dossiers/LLY.json", "frontend/dossiers/LLY.md",
    "frontend/dossiers/VITL.json", "frontend/dossiers/WERN.json", "frontend/dossiers/WERN.md",
    "tests/fixtures/material_direction/pages.json", "tests/fixtures/synthesis_gold/claims.jsonl")


def test_the_guard_finds_the_three_runs_1036_cut_in_its_parent(local_calls: Calls) -> None:
    """CORPUS BEFORE SYNTHETIC. On #1036's parent, the files #1036 cut hold runs in its three
    claims. They are 13 and 14 words by the build guard's count. Here a run also takes in the
    page's own words that follow a claim and match its call, so it can read longer. The guard must
    find each claim's run, and it must find nothing in those files at the head of this branch."""
    names = {c.name for c in local_calls.calls}
    if not any(t in n for t in ("Eli Lilly", "Vital Farms", "Werner") for n in names):
        pytest.skip("LLY's, VITL's and WERN's calls are not on this disk")
    hits_then: dict[str, set[str]] = defaultdict(set)
    for f in _FILES_1036:
        text = subprocess.run(["git", "show", f"{_PARENT_1036}:{f}"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout
        for r in group_runs(f, scan_text(text, local_calls)):
            name, _ = origin(local_calls, {r.windows[0]})[r.windows[0]]
            hits_then[name.split(",")[0]].add(f)
    assert {"Eli Lilly and Company", "Vital Farms", "Werner Enterprises"} <= set(hits_then), (
        f"the guard missed a run #1036 cut; it found runs against {sorted(hits_then)}")
    now = scan_tracked(local_calls, None, files=list(_FILES_1036))
    assert now.runs == [], [f"{r.path}:{r.line}" for r in now.runs]


# --- what is read, and what is reported (no call needed: these run in CI too) ---------------------

def test_two_runs_that_open_alike_are_both_kept_and_one_read_twice_is_one() -> None:
    """REVIEW ROUND 0. Runs were kept once per (line, first window): two runs on one line opening
    with the same 13 words collapsed into the longer, and the shorter's later windows were never
    looked for outside the calls. A run is now dropped only when a longer run kept on its line
    holds every window it holds — one run read raw and unescaped is still one."""
    a = [Hit(0, 7, p, w) for p, w in ((0, 101), (1, 102), (2, 103))]
    b = [Hit(0, 7, p, w) for p, w in ((20, 101), (21, 104))]
    runs = group_runs("x.md", a + b)
    assert sorted(tuple(r.windows) for r in runs) == [(101, 102, 103), (101, 104)]
    same_run_two_views = [Hit(1, 7, p, w) for p, w in ((0, 101), (1, 102))]
    assert [r.windows for r in group_runs("x.md", a + same_run_two_views)] == [[101, 102, 103]]


def test_a_file_written_and_not_yet_staged_is_read(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """REVIEW ROUND 0. `git ls-files` alone lists the index, so a record written and not yet
    staged was never read, and the guard passed it. What git ignores is still not read."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("ignored.md\n")
    for name in ("staged.md", "unstaged.md", "ignored.md"):
        (tmp_path / name).write_text("x\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "staged.md", ".gitignore"], check=True)
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    assert tracked_files() == [".gitignore", "staged.md", "unstaged.md"]


# --- review round 1: the literals a Python file joins at run time ---------------------------------

def test_a_python_files_literals_are_read_as_the_code_joins_them() -> None:
    """REVIEW ROUND 1 (operator ruling 2026-11-13, "Cut 27 + widen guard (Recommended)"), no call
    needed. Everything between literals is blanked (a name, an `=`, an f-string's `{field}`, the
    `f`/`r`/`b` prefixes, the quotes), each literal's words stay on their own line, and a file that
    does not tokenize yields no view rather than a guess."""
    src = ('q = "alpha beta"\n'
           'tail = f"{q} gamma" + rb"delta"\n'
           'x = ("epsilon "\n     f"zeta {q!r:>4}")  # a comment is not a literal\n'
           'doc = """eta\ntheta"""\n')
    joined = py_strings(src)
    assert joined is not None
    assert words(joined) == (["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"],
                             [1, 1, 2, 2, 3, 4, 5, 6])
    assert py_strings('x = "unterminated\n') is None


def _joined_bites(local_calls: Calls, at: int) -> dict[str, bool]:
    """The review's two planted shapes and a 12-word negative, each as a .py file and as any other
    file, on 13 words of a real call read at run time (held in this frame only)."""
    ws = _call_words(call_roots())[at:at + _RULE_PLUS_ONE]

    def caught(text: str, py: bool) -> bool:
        return bool(scan_text(text, local_calls, py))

    split = f'q = "{" ".join(ws[:7])}"\ntail = "{" ".join(ws[7:])}"\n'
    fcont = f'x = ("{" ".join(ws[:6])} "\n     f"{{y}} {" ".join(ws[6:])}")\n'
    twelve = f'q = "{" ".join(ws[:6])}"\ntail = "{" ".join(ws[6:12])}"\n'
    return {
        "13 words as two assignments, read as Python": caught(split, True),
        "13 words, an implicit concatenation with an f-string, read as Python": caught(fcont, True),
        "13 words as two assignments, read as any other file": caught(split, False),
        "12 words as two assignments, read as Python": caught(twelve, True),
    }


def test_thirteen_words_split_across_python_literals_are_caught(local_calls: Calls) -> None:
    """THE BLIND SPOT REVIEW ROUND 1 FOUND. Thirteen call words split over two string literals —
    two assignments the code joins, or an implicit concatenation whose second part is an f-string —
    were read by every other view as two runs of under 13. The joined view reads each as one, and
    12 words split the same way are still not a run."""
    assert _joined_bites(local_calls, 500) == {
        "13 words as two assignments, read as Python": True,
        "13 words, an implicit concatenation with an f-string, read as Python": True,
        "13 words as two assignments, read as any other file": False,
        "12 words as two assignments, read as Python": False,
    }


#: main before this PR, still holding the two joined runs round 1 cut (VRRM's and SMPL's)
_MAIN_BEFORE_ROUND_1 = "98707f297a16982f1281c76ec2477ce1c5ab76dc"


def test_the_guard_finds_the_two_joined_runs_round_1_cut(local_calls: Calls) -> None:
    """CORPUS BEFORE SYNTHETIC. On main before this PR, `tests/test_following_context.py` held a
    20-word run of VRRM's Q1 2026 call and a 13-word run of SMPL's Q3 2026 call, each split over
    two literals. The joined view must find both there, and nothing in that file at head."""
    names = {c.name for c in local_calls.calls}
    want = ("Verra Mobility Corporation, Q1 2026", "The Simply Good Foods Company, Q3 2026")
    if not all(any(n.startswith(w) for n in names) for w in want):
        pytest.skip("VRRM's Q1 2026 and SMPL's Q3 2026 calls are not both on this disk")
    f = "tests/test_following_context.py"
    then = subprocess.run(["git", "show", f"{_MAIN_BEFORE_ROUND_1}:{f}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
    found = {origin(local_calls, {r.windows[0]})[r.windows[0]][0]
             for r in group_runs(f, scan_text(then, local_calls, True))}
    assert all(any(n.startswith(w) for n in found) for w in want), (
        f"found runs against {sorted(found)} only")
    assert scan_tracked(local_calls, None, files=[f]).runs == []


# --- Codex on #1046: a call that does not read, and a word inside a Markdown link ---------------

def _stub_request() -> Any:
    """What the corpus test reads off pytest's request: no cache, no terminal reporter."""
    from types import SimpleNamespace
    return SimpleNamespace(config=SimpleNamespace(
        cache=None, pluginmanager=SimpleNamespace(get_plugin=lambda name: None)))


def test_a_call_on_disk_that_does_not_read_fails_the_guard(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CODEX ON #1046, P1 — FAIL LOUD. A call that is on disk and does not read was dropped from
    the scan, and the guard passed on the calls that did: a run of the dropped call's words would
    have passed unseen. Now it fails, naming the file and its error. A store holding only calls
    that do not read fails too, and only a disk with NO call skips (CI). No call is needed: the
    store here is built in the test, of words no call holds."""
    me = sys.modules[__name__]
    store = tmp_path / "ciq"
    (store / "ACME").mkdir(parents=True)
    good = store / "ACME" / "Acme, Inc., Q1 2026 Earnings Call, Jan 02, 2026.rtf"
    bad = store / "ACME" / "Acme, Inc., Q2 2026 Earnings Call, Apr 02, 2026.rtf"
    good.write_text("{\\rtf1\\ansi " + " ".join(f"zqxw{i}" for i in range(40)) + "}")
    bad.write_bytes(b"\x00\x01 neither RTF nor any export")
    monkeypatch.setattr(me, "call_roots", lambda: [store])
    monkeypatch.setattr(me, "tracked_files", lambda: ["README.md"])
    with pytest.raises(AssertionError, match="Q2 2026 Earnings Call"):
        test_no_tracked_file_shares_13_consecutive_words_with_a_call(_stub_request())
    good.unlink()
    with pytest.raises(AssertionError, match="do not read"):
        test_no_tracked_file_shares_13_consecutive_words_with_a_call(_stub_request())
    monkeypatch.setattr(me, "call_roots", lambda: [])
    with pytest.raises(pytest.skip.Exception, match="CI holds none"):
        test_no_tracked_file_shares_13_consecutive_words_with_a_call(_stub_request())


def test_a_markdown_link_reads_as_its_text() -> None:
    """CODEX ON #1046, P2, no call needed: `[text](url)` and `![alt](url "title")` read as their
    text, the words around them kept; brackets and parentheses that are not a link stay."""
    text = ('one [two three](https://example.com/a/b) four ![five](img/x.png "t") six (seven) '
            '[eight]')
    assert words(views(text)[-1])[0] == ["one", "two", "three", "four", "five", "six", "seven",
                                         "eight"]


def _link_bites(local_calls: Calls, at: int) -> dict[str, bool]:
    """13 words of a real call (held in this frame only) with one inside a Markdown link, as a
    link and as an image, and 12 words the same way."""
    ws = _call_words(call_roots())[at:at + _RULE_PLUS_ONE]

    def caught(text: str) -> bool:
        return bool(scan_text(text, local_calls))

    head, tail = " ".join(ws[:6]), " ".join(ws[7:])
    return {
        "13 words, one inside a Markdown link":
            caught(f"{head} [{ws[6]}](https://example.com/a/b) {tail}"),
        "13 words, one as an image's alt text": caught(f"{head} ![{ws[6]}](img/x.png) {tail}"),
        "12 words, one inside a Markdown link":
            caught(f"{head} [{ws[6]}](https://example.com/a/b) {' '.join(ws[7:12])}"),
    }


def test_thirteen_words_with_one_inside_a_markdown_link_are_caught(local_calls: Calls) -> None:
    """CODEX ON #1046, P2. One word written as a Markdown link (`[word](url)`) read as
    "word](https:" and broke a 13-word run into two short ones, though the rendered page shows the
    words consecutively. The link view reads it as one run; 12 words the same way are not one."""
    assert _link_bites(local_calls, 600) == {
        "13 words, one inside a Markdown link": True,
        "13 words, one as an image's alt text": True,
        "12 words, one inside a Markdown link": False,
    }
