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
file is read raw, JSON/JS-unescaped where it holds a backslash, and HTML-unescaped with its tags
dropped where it holds `<` or `&`, so a run escaped or marked up in one view is found in another.

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
import json
import os
import re
import string
import subprocess
import sys
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


def views(text: str) -> list[str]:
    """``text`` raw, JSON/JS-unescaped where it holds a backslash, and HTML-unescaped with tags
    dropped where it holds markup. Newlines are kept in each, so a line is the file's own."""
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
    return out


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
    for f in (_unescape, views, words, key, window_keys, scan_text):
        h.update(inspect.getsource(f).encode())
    h.update(f"{N}|{_EDGE}|{_SPLIT.pattern}|{_APOS}|{_ESC.pattern}|{_TAG.pattern}".encode())
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


def scan_text(text: str, calls: Calls) -> list[Hit]:
    """Every window of 13 words that ``text`` (each of its views) shares with a call."""
    out: list[Hit] = []
    for vi, v in enumerate(views(text)):
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
    """``hits`` as runs. One run read in two views (raw and unescaped) is kept once, the longer;
    two runs on one line are two runs."""
    by: dict[int, list[Hit]] = defaultdict(list)
    for hit in hits:
        by[hit.view].append(hit)
    best: dict[tuple[int, int], Run] = {}
    for vi, hs in by.items():
        hs.sort(key=lambda x: x.pos)
        group = [hs[0]]
        tail: list[Hit | None] = [*hs[1:], None]
        for h in tail:
            if h is not None and h.pos == group[-1].pos + 1:
                group.append(h)
                continue
            r = Run(path, group[0].line, vi, group[0].pos, [g.window for g in group])
            k = (r.line, r.windows[0])
            if k not in best or best[k].length < r.length:
                best[k] = r
            if h is not None:
                group = [h]
    return sorted(best.values(), key=lambda r: (r.line, r.pos))


@dataclass
class Scan:
    runs: list[Run]
    scanned: int
    skipped: dict[str, list[str]]


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    return [f for f in out.stdout.decode().split("\0") if f]


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
            raw = [[h.view, h.line, h.pos, h.window] for h in scan_text(text, calls)]
        fresh[ck] = raw
        if raw:
            got = group_runs(f, [Hit(*h) for h in raw])
            vs = views(text)
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
    """The cache's listing (names, sizes): what a full read did not find stays unfound while it
    holds."""
    h = hashlib.sha256()
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
            failed = len(unreadable["SEC"])
            for p in sorted(sec_dir.iterdir()):
                if not todo:
                    break
                raw = sec_read(p)
                doc = _sec_doc(raw) if raw is not None else None
                if raw is None or doc is None:
                    continue
                present = set(_LETTERS.findall(raw.lower()))
                if any(not a or a in present for w, a in anchors.items() if w in todo):
                    sec_look(raw, doc, todo)
            want -= set(sec)
            if len(unreadable["SEC"]) == failed:
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


def test_no_tracked_file_shares_13_consecutive_words_with_a_call(
        request: pytest.FixtureRequest, capsys: pytest.CaptureFixture[str]) -> None:
    roots = call_roots()
    cache = _cache(request)
    calls = read_calls(roots, cache)
    if not calls.calls:
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
        + f"\n  tracked files: {scan.scanned} scanned; skipped: {skipped or 'none'}"
        + f"\n  runs of {N}+ words shared with a call: {len(scan.runs)} "
          f"({len({w for r in scan.runs for w in r.windows})} distinct windows)"
        + f"\n  excused by an SEC document in the cache: {len(sec_runs)} run(s)"
        + "\n  excused by a CIQ Key Developments export (KD's publication is unruled, STATE row "
          f"60 item 3b): {len(kd_runs)} run(s)"
        + f"\n  excuse sources read: {sources.read or 'none'}; unreadable: "
        + (", ".join(f"{len(v)} {k}" for k, v in sources.unreadable.items()) or "none")
        + f"\n  unexcused: {len(bad)} run(s)")
    with capsys.disabled():
        print("\n" + boundary)
        for r in kd_runs:
            print(f"    KD-excused: {r.path}:{r.line} ({r.length} words, run sha256 "
                  f"{run_hash(r.words)})")
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


def _call_words(calls: Calls, roots: list[Path]) -> list[str]:
    """One readable call's words, read at run time and never written anywhere."""
    for p in _files_of_kind(roots, "transcript"):
        try:
            ws = words(read_text(p))[0]
        except (CiqParseError, OSError):
            continue
        if len(ws) > 400:
            return ws
    pytest.skip("no call on this disk reads to 400 words")


#: CLAUDE.md's number plus one, written out: a pin that read `N` would move with the code it pins
_RULE_PLUS_ONE = 13


def _bites(local_calls: Calls, at: int) -> dict[str, bool]:
    """Each bite pin's outcome by its label, on 13 words of a real call read at run time. The words
    stay in this frame: a failed pin prints its label and a boolean, never a call's word."""
    ws = _call_words(local_calls, call_roots())[at:at + _RULE_PLUS_ONE]

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
    ws = _call_words(local_calls, call_roots())[at:at + _RULE_PLUS_ONE]
    w = window_keys([key(x) for x in ws])[0]
    url = "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/ex99.htm"
    name = f"{hashlib.sha256(url.encode()).hexdigest()}.json"
    sec, short = folder / "sec", folder / "short"
    sec.mkdir()
    short.mkdir()
    kd = folder / "Acme Inc NYSE ACME Key Developments.rtf"
    try:
        (sec / name).write_text(json.dumps(
            {"url": url, "fetched_at": 0, "text": f"<p>{' '.join(ws)}</p>"}))
        (short / name).write_text(json.dumps(
            {"url": url, "fetched_at": 0, "text": " ".join(ws[:12])}))
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
        }
    finally:
        for f in (sec / name, short / name, kd):
            f.unlink(missing_ok=True)


def test_a_window_is_excused_only_where_a_source_holds_it(local_calls: Calls,
                                                          tmp_path: Path) -> None:
    """The excuse is computed: a window an SEC document in the cache holds is excused and named;
    the same window with no source is not, and a source holding only 12 of its words excuses
    nothing. A Key Developments export excuses too, reported apart, and where an SEC document
    holds the same window the excuse is the document's (KD's publication is unruled)."""
    got = _excused(local_calls, tmp_path, 300)
    assert got == dict.fromkeys(got, True)
    assert len(got) == 5


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
