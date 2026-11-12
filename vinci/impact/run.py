"""The impact check's run: base code against head code on ONE set of inputs, every part at $0.

Each part is measured, never asserted (`vinci.impact` names the five). The run lays out, OUTSIDE the
repository (captured requests carry licensed transcript text):

    <out>/code/<side>/            the side's ``vinci/`` and ``frontend/build.py`` (git archive)
    <out>/inputs-src/             the DATA REF's committed ``data/``, ``scenarios/``, ``frontend/``
    <out>/<side>/impact-inputs/   a clone of it, the side's cwd, with the git-ignored inputs linked:
                                  ``data/manual/ciq`` and ``data/cache`` (shared, read through the
                                  frozen cache) and ``data/vinci.db`` (the side's own store clone)
    <out>/<side>/impact-store/data/vinci.db   a clone of ONE store snapshot

Both sides' folders carry the same names, so the price-store stamp a page writes cannot differ by
side. The data ref is HEAD: the pages compared are the ones a merge would carry, and code is the
only thing that differs between the sides.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.impact import graph as ig
from vinci.impact import stamp as st
from vinci.impact.child import NO_VENDOR_PULLS
from vinci.impact.values import (
    VOLATILE,
    Change,
    clock_text,
    cut,
    member_families,
    moved_members,
    value_changes,
)

SIDES = ("base", "head")
HERE = Path(__file__).resolve().parent
CHILD = HERE / "child.py"
CAPTURE_CHILD = HERE.parent / "evals" / "capture_child.py"
#: The six frozen panel pages (STATE row 53; `vinci/evals/synthesis_panel.json`).
PANEL_FILE = HERE.parent / "evals" / "synthesis_panel.json"
#: Never handed to a child: it builds and captures, it sends nothing to a model.
SECRET_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE",
              "ANTHROPIC_IDENTITY_TOKEN", "ANTHROPIC_IDENTITY_TOKEN_FILE")
#: Never handed to the fail-first pytest: the gate's suite is hermetic, and so is this.
TEST_SECRET_ENV = (*SECRET_ENV, "POLYGON_API_KEY", "TIINGO_API_KEY", "R2_ACCOUNT_ID",
                   "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")
#: A page field that moves on every page when the extraction version is bumped: reported once,
#: not counted as a page move.
VERSION_FIELDS = ("extraction_version",)
#: Keys a consumer writes from its own clock (compared nowhere).
CONSUMER_VOLATILE = VOLATILE | {"generated_at", "screen_run_at", "run_at", "started_at",
                                "finished_at", "written_at", "source_commit"}


class ImpactError(RuntimeError):
    """An input the run cannot pin, or a step that cannot be made: never a guessed result."""


@dataclass
class Settings:
    repo: Path
    base: str
    head: str
    out: Path
    ciq_root: Path
    cache_root: Path
    store: Path
    env_file: Path | None
    workers: int = 6
    tickers: tuple[str, ...] = ()
    theme_data: Path | None = None
    run_screen: bool = False
    shortcut: bool = True
    #: reuse a folder an earlier run of the SAME stamp left: a page side already built is kept
    resume: bool = False
    #: list families the report censuses even when nothing in them moves (substrings)
    census: tuple[str, ...] = ()
    #: refuse a Polygon or Tiingo response the cache lacks (`NO_VENDOR_PULLS`)
    no_vendor_pulls: bool = True
    #: leave part 1 out (a sweep of merged PRs asks what moved, not their pins); the section says so
    skip_fail_first: bool = False
    python: str = sys.executable
    log: Callable[[str], None] = field(default=lambda m: print(m, file=sys.stderr, flush=True))


# ------------------------------------------------------------------------------------- the tree

def primary_checkout(repo: Path) -> Path:
    common = st.git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    return Path(common).resolve().parent


def _inside(path: Path, repo: Path) -> bool:
    here = path.resolve()
    roots = {repo.resolve(), primary_checkout(repo)}
    return any(r == here or r in here.parents for r in roots)


def _extract(repo: Path, ref: str, paths: Sequence[str], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    present = [p for p in paths if st.git(repo, "ls-tree", "--name-only", ref, p).strip()]
    tar = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", ref, *present],
                         capture_output=True, check=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".tar") as fh:
        fh.write(tar)
        fh.flush()
        with tarfile.open(fh.name) as tf:
            tf.extractall(dest, filter="data")


def _clone(src: Path, dst: Path) -> None:
    """An APFS clone where the volume supports one (instant, no space), else a copy."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    flag = ["-c"] if sys.platform == "darwin" else []
    done = subprocess.run(["cp", *flag, "-R", str(src), str(dst)], capture_output=True)
    if done.returncode != 0:
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=True)
        else:
            shutil.copy2(src, dst)


def snapshot_store(src: Path, dest: Path) -> None:
    """A consistent copy of a live SQLite store (``.backup``), read-only on the source."""
    if not src.exists():
        raise ImpactError(f"no price store at {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{src}?mode=ro", uri=True) as s, sqlite3.connect(dest) as d:
        s.backup(d)


def file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


_DIGEST = """
import sqlite3, hashlib, sys
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
h = hashlib.sha256(); n = 0
for (t,) in c.execute("select name from sqlite_master where type='table' and name!='meta' "
                      "order by name"):
    h.update(t.encode())
    for row in c.execute(f"select * from {t} order by rowid"):
        h.update(repr(row).encode()); n += 1
print(h.hexdigest(), n)
"""


def store_digest(db: Path, python: str) -> subprocess.Popen[str]:
    """The store's CONTENT, every table but ``meta`` (the schema stamp `Store` rewrites on each
    open), started in a child so three run at once."""
    return subprocess.Popen([python, "-c", _DIGEST, str(db)], stdout=subprocess.PIPE, text=True)


def _digest_result(p: subprocess.Popen[str]) -> dict[str, Any]:
    out, _ = p.communicate()
    digest, rows = out.split()
    return {"content_sha256": digest, "rows": int(rows)}


def store_identity(db: Path) -> dict[str, Any]:
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
        frontier = c.execute("select max(bar_date) from prices").fetchone()[0]
        names = c.execute("select count(distinct internal_id) from prices").fetchone()[0]
    return {"file_sha256": file_sha256(db), "frontier": frontier, "priced_ids": names}


def ciq_identity(ciq_root: Path, tickers: Iterable[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for t in tickers:
        folder = ciq_root / t
        files = sorted(p for p in folder.iterdir()
                       if p.is_file() and not p.name.startswith(".")) if folder.is_dir() else []
        out[t] = {p.name: file_sha256(p) for p in files}
    return out


def child_env(code: Path, env_file: Path | None, strip: Sequence[str] = SECRET_ENV
              ) -> dict[str, str]:
    env = dict(os.environ)
    if env_file is not None and env_file.exists():
        from dotenv import dotenv_values
        for k, v in dotenv_values(env_file).items():
            if v is not None and k not in env:
                env[k] = v
    for k in strip:
        env.pop(k, None)
    env["PYTHONPATH"] = str(code)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def page_env(s: Settings, code: Path) -> dict[str, str]:
    """A page or consumer child's environment: `child_env`, plus the vendor-pull refusal."""
    env = child_env(code, s.env_file)
    if s.no_vendor_pulls:
        env[NO_VENDOR_PULLS] = "1"
    return env


@dataclass
class Layout:
    out: Path
    code: dict[str, Path]
    cwd: dict[str, Path]
    store: dict[str, Path]
    inputs_src: Path


def lay_out(s: Settings, shas: dict[str, str]) -> Layout:
    """Extract both sides' code and the data ref's inputs, then clone the inputs and the store per
    side (module docstring)."""
    out = s.out
    code = {side: out / "code" / side for side in SIDES}
    for side in SIDES:
        _extract(s.repo, shas[side], ["vinci", "frontend/build.py"], code[side])
    src = out / "inputs-src"
    _extract(s.repo, shas["head"], ["data", "scenarios", "frontend"], src)
    snap = out / "store-snapshot" / "data" / "vinci.db"
    snapshot_store(s.store, snap)
    cwd: dict[str, Path] = {}
    store: dict[str, Path] = {}
    for side in SIDES:
        store[side] = out / side / "impact-store" / "data" / "vinci.db"
        _clone(snap, store[side])
        cwd[side] = out / side / "impact-inputs"
        _clone(src, cwd[side])
        _link_ignored(cwd[side], s, store[side])
    return Layout(out, code, cwd, store, src)


def resume_layout(s: Settings) -> Layout:
    out = s.out
    return Layout(out, {side: out / "code" / side for side in SIDES},
                  {side: out / side / "impact-inputs" for side in SIDES},
                  {side: out / side / "impact-store" / "data" / "vinci.db" for side in SIDES},
                  out / "inputs-src")


def _link_ignored(root: Path, s: Settings, db: Path) -> None:
    data = root / "data"
    (data / "manual").mkdir(parents=True, exist_ok=True)
    for link, target in ((data / "manual" / "ciq", s.ciq_root), (data / "cache", s.cache_root),
                         (data / "vinci.db", db)):
        if link.is_symlink() or link.exists():
            raise ImpactError(f"{link} is committed at the data ref; it must be git-ignored")
        link.symlink_to(target.resolve())


# ------------------------------------------------------------------------------ 1. fail first

def changed_tests(s: Settings, shas: dict[str, str]) -> list[str]:
    paths = st.changed_paths(s.repo, shas["base"], shas["head"])
    head_files = set(st.git(s.repo, "ls-tree", "-r", "--name-only", shas["head"], "tests")
                     .splitlines())
    return sorted(p for p in paths if p.startswith("tests/") and Path(p).name.startswith("test_")
                  and p.endswith(".py") and p in head_files)


def _junit(path: Path) -> dict[str, dict[str, Any]]:
    """Each test case's outcome from a pytest junit file (xunit1, so it carries file and line)."""
    if not path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        file, name = case.get("file") or "", case.get("name") or ""
        cls = (case.get("classname") or "").split(".")
        klass = cls[-1] if cls and cls[-1][:1].isupper() else None
        node = f"{file}::{klass}::{name}" if klass else f"{file}::{name}"
        if not case.get("classname"):   # a file that failed to collect
            node = f"{file or name} (collection)"
        outcome, text = "passed", ""
        for tag in ("failure", "error", "skipped"):
            el = case.find(tag)
            if el is not None:
                outcome = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                text = (el.text or "") or (el.get("message") or "")
                if tag == "skipped":
                    text = el.get("message") or text
                break
        out[node] = {"outcome": outcome, "where": _failing_line(text, file),
                     "message": _first_e_line(text)}
    return out


def _failing_line(text: str, file: str) -> str | None:
    """The last ``path:line`` of the traceback inside the test file, else the last one at all."""
    hits = [ln.split(": ", 1)[0] for ln in text.splitlines()
            if ":" in ln and ln.split(":", 1)[0].endswith(".py") and ln.split(":")[1].isdigit()]
    pick = [h for h in hits if file and h.startswith(file)] or hits
    return pick[-1] if pick else None


def _first_e_line(text: str) -> str:
    for ln in text.splitlines():
        if ln.startswith("E "):
            return cut(ln[1:].strip(), 300)
    return cut(text.strip().splitlines()[0], 300) if text.strip() else ""


#: A placeholder for a name the tests import and base's code does not define: it lets the file
#: collect, and fails the first test that USES the name, at that line (`fail_first`).
_SHIM = """
import importlib, json, os

class _Missing:
    def __init__(self, where):
        object.__setattr__(self, "_where", where)
    def _fail(self, *a, **k):
        raise AssertionError(f"{object.__getattribute__(self, '_where')} does not exist at base")
    __call__ = __getattr__ = __getitem__ = __iter__ = __len__ = __bool__ = __str__ = _fail
    __eq__ = __ne__ = __lt__ = __le__ = __gt__ = __ge__ = __add__ = __radd__ = __contains__ = _fail
    __hash__ = __int__ = __float__ = __format__ = _fail

def pytest_configure(config):
    for mod, name in json.loads(os.environ["IMPACT_MISSING"]):
        m = importlib.import_module(mod)
        if not hasattr(m, name):
            setattr(m, name, _Missing(f"{mod}.{name}"))
"""
_CANNOT_IMPORT = re.compile(r"cannot import name '(\w+)' from '([\w.]+)'")


def _pytest(s: Settings, tree: Path, tests: Sequence[str], log: Path, junit: Path,
            missing: Sequence[tuple[str, str]] = ()) -> subprocess.Popen[bytes]:
    env = child_env(tree, None, TEST_SECRET_ENV)
    shim: list[str] = []
    if missing:
        (tree / "_impact_shim.py").write_text(_SHIM, encoding="utf-8")
        env["IMPACT_MISSING"] = json.dumps(list(missing))
        shim = ["-p", "_impact_shim"]
    return subprocess.Popen(
        [s.python, "-m", "pytest", *tests, *shim, "-m", "not network", "-q", "-p",
         "no:cacheprovider", "-p", "no:warnings", "--tb=short", "-o", "junit_family=xunit1",
         "--continue-on-collection-errors", f"--junitxml={junit}"],
        cwd=tree, env=env, stdout=log.open("wb"), stderr=subprocess.STDOUT)


def fail_first(s: Settings, shas: dict[str, str]) -> dict[str, Any]:
    """Head's changed test files, run on base's ``vinci/`` and on head's (both in head's tree).

    A test file that imports a name base's code does not define fails to COLLECT at base, which
    would report one error for the file and no test. Each such name gets a placeholder that raises
    when used (`_SHIM`, ``cannot import name X from M`` only — a missing MODULE stays a
    collection error), and base is run again, up to eight times: every test then fails at the
    line that uses the new name, or runs on base's code when it never does."""
    tests = changed_tests(s, shas)
    if not tests:
        return {"tests": [], "cases": [], "note": "the PR changes no test file"}
    t0 = time.monotonic()
    root = s.out / "failfirst"
    if root.exists():
        shutil.rmtree(root)
    trees = {"head": root / "head-tree", "base": root / "base-tree"}
    _extract(s.repo, shas["head"], ["."], trees["head"])
    _clone(trees["head"], trees["base"])
    shutil.rmtree(trees["base"] / "vinci")
    _extract(s.repo, shas["base"], ["vinci"], trees["base"])
    procs = {side: _pytest(s, tree, tests, root / f"pytest-{side}.log",
                           root / f"junit-{side}.xml") for side, tree in trees.items()}
    codes = {side: p.wait() for side, p in procs.items()}
    missing: list[tuple[str, str]] = []
    for _ in range(8):
        found = {(m.group(2), m.group(1)) for m in _CANNOT_IMPORT.finditer(
            (root / "pytest-base.log").read_text(errors="replace"))} - set(missing)
        if not found:
            break
        missing += sorted(found)
        codes["base"] = _pytest(s, trees["base"], tests, root / "pytest-base.log",
                                root / "junit-base.xml", missing).wait()
    res = {side: _junit(root / f"junit-{side}.xml") for side in SIDES}
    # a file that did not collect at base: each of its tests failed there, at the import
    uncollected = {n.removesuffix(" (collection)"): r for n, r in res["base"].items()
                   if n.endswith(" (collection)")}
    for node in res["head"]:
        f = node.split("::", 1)[0]
        if f in uncollected and node not in res["base"]:
            res["base"][node] = {**uncollected[f], "collection": True}
    cases = []
    for node in sorted(set(res["base"]) | set(res["head"])):
        b = res["base"].get(node, {"outcome": "absent", "where": None, "message": ""})
        h = res["head"].get(node, {"outcome": "absent", "where": None, "message": ""})
        cases.append({"node": node, "base": b, "head": h})
    return {"tests": tests, "cases": cases, "exit": codes,
            "missing_at_base": [f"{m}.{n}" for m, n in missing],
            "seconds": round(time.monotonic() - t0, 1)}


def part_one(s: Settings, shas: dict[str, str]) -> dict[str, Any]:
    """`fail_first`, or its NOT RUN record under ``--skip-fail-first`` — on every path."""
    if s.skip_fail_first:
        return {"tests": [], "cases": [], "skipped": True}
    return fail_first(s, shas)


# ----------------------------------------------------------------------------------- 2–4. pages

#: Where page builds are kept across runs, keyed by everything they read (`build_key`).
BUILD_CACHE = Path.home() / ".cache" / "vinci" / "impact-builds"
#: The files of a page side the cache keeps. The request is among them and can carry licensed
#: transcript text, so the cache folder sits outside every repository, as the run folder does.
_KEPT = ("built.json", "built.md", "committed.md", "request.json", "reads.json", "timing.json",
         "store_written.json", "ciq.json", "clock.json",
         "build.error.json", "render.error.json", "request.error.json",
         "committed_render.error.json")


def build_key(s: Settings, lay: Layout, side: str, ticker: str, shas: dict[str, str],
              inputs: dict[str, Any], day: str) -> str:
    """Everything a page side's build reads, hashed: the side's ``vinci/`` tree, the check's own
    child and capture code, the data ref's committed trees, the store snapshot, the page's CIQ
    exports, the cache root and the UTC DAY it was built on (`build_days`). The HTTP responses it
    read are checked on reuse (`_reusable`)."""
    def tree(ref: str, path: str) -> str:
        return st.git(s.repo, "rev-parse", f"{ref}:{path}").strip()
    parts = {"vinci": tree(shas[side], "vinci"), "child": file_sha256(CHILD),
             "capture": file_sha256(CAPTURE_CHILD), "data": tree(shas["head"], "data"),
             "scenarios": tree(shas["head"], "scenarios"),
             "store": inputs["store"]["file_sha256"], "ciq": inputs["ciq"].get(ticker),
             "cache": str(s.cache_root), "ticker": ticker, "day": day}
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


# THE BUILD'S UTC DAY IS ONE OF ITS INPUTS (#984, 2026-11-12). A build stamped today's UTC date on
# the page: `statement_reconciliation.as_filed_by` was ``datetime.now(UTC).date()``
# (`mechanical.py`, `statement_recon.attach`; ruling 2, 2026-11-12, dates it by its filings
# since), and it reached the synthesis request's facts. The
# sweep's #984 run compared base sides KEPT from 23:43Z on 2026-11-11 with head sides built after
# 01:26Z on 2026-11-12: 5 of 27 pages "moved" on that date alone, the requests with them. AMZN's
# base build STARTED at 23:43Z and stamped 2026-11-12, so a build's start time does not name its
# day: the child records every UTC day a build ran across (``clock.json``).
def utc_today() -> str:
    return dt.datetime.now(dt.UTC).date().isoformat()


def build_days(folder: Path) -> list[str]:
    """Every UTC day a page side's build ran across: the child's ``clock.json`` (its first and
    last day) and the page's ``assembled_at``; for a side built before ``clock.json`` existed, its
    ``as_filed_by`` too. Empty when nothing names a day.

    ``as_filed_by`` is read only WITHOUT a clock (ruling 2, 2026-11-12): since then it is the
    latest filing the reconciliation read, which names no day a build ran on, and every build
    since this module's clock writes ``clock.json``. A side kept from before it was built by code
    that stamped the build's day there."""
    clock = _read(folder / "clock.json")
    days = set((clock or {}).get("utc_days") or [])
    page = _read(folder / "built.json") or {}
    if page.get("assembled_at"):
        days.add(str(page["assembled_at"])[:10])
    recon = ((page.get("mechanical") or {}).get("financial_summary") or {}).get(
        "statement_reconciliation") or {}
    if clock is None and recon.get("as_filed_by"):
        days.add(str(recon["as_filed_by"]))
    return sorted(days)


def off_day_sides(s: Settings, ticker: str) -> list[str]:
    """The sides to re-build so that both were built within ONE and the same UTC day: the side(s)
    whose days are not exactly the day a re-build lands on — today, or the latest day either side
    ran on if later. Two sides built within one past day agree and are left alone. A side not
    built is left to the comparison, which names it."""
    folders = {side: s.out / "pages" / side / ticker for side in SIDES}
    if not all((f / "built.json").exists() for f in folders.values()):
        return []
    days = {side: build_days(f) for side, f in folders.items()}
    if days["base"] == days["head"] and len(days["base"]) == 1:
        return []
    # NOT the latest day the sides carry: two sides KEPT by --resume from two past days would
    # re-build the earlier one TODAY, a third day, and set the page apart as noise for nothing
    target = max([utc_today(), *(d for ds in days.values() for d in ds)])
    return [side for side in SIDES if days[side] != [target]]


def _reusable(s: Settings, folder: Path) -> bool:
    """A kept build is reused only while every response it read is still byte-identical in the
    cache (another checkout's ordinary run can rewrite an entry)."""
    reads = _read(folder / "reads.json")
    if reads is None or not (folder / "timing.json").exists() or any(folder.glob("*.error.json")):
        return False
    for r in reads.values():
        f = s.cache_root / str(r.get("file", ""))
        if not r.get("file") or not f.is_file():
            return False
        try:
            text = json.loads(f.read_text())["text"]
        except (ValueError, KeyError):
            return False
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != r["sha256"]:
            return False
    return True


def run_child(s: Settings, lay: Layout, side: str, ticker: str,
              key: Callable[[str], str] | None = None) -> str:
    """Build one page side; returns how: ``built``, ``kept`` (an earlier run of the same key)
    or ``resumed``. ``key`` maps a UTC day to the side's `build_key`: a kept build is looked up
    under today's, and kept under the one day it was built on — never when it ran across two."""
    out = s.out / "pages" / side
    if s.resume and (out / ticker / "timing.json").exists():
        # KEPT ONLY WHILE ITS INPUTS ARE (Codex P1, #1000): every response it read re-hashes the
        # same, and the page's CIQ exports are the ones it was built from — else rebuilt
        if _reusable(s, out / ticker) and _read(out / ticker / "ciq.json") == ciq_identity(
                s.ciq_root, [ticker])[ticker]:
            return "resumed"
        shutil.rmtree(out / ticker)
    kept = BUILD_CACHE / key(utc_today()) if key else None
    if kept is not None and _reusable(s, kept):
        (out / ticker).mkdir(parents=True, exist_ok=True)
        for name in _KEPT:
            if (kept / name).exists():
                shutil.copy2(kept / name, out / ticker / name)
        return "kept"
    _run_child(s, lay, side, ticker)
    if (out / ticker).is_dir():   # what this side was built from, for a later --resume
        _write_side(out / ticker / "ciq.json", ciq_identity(s.ciq_root, [ticker])[ticker])
    # A FAILED STEP IS NEVER KEPT: a failure can be the machine's, not the code's (three page
    # sides of the first 27-page run hit "database is locked" and were kept, then reused)
    failed = any((out / ticker).glob("*.error.json"))
    days = build_days(out / ticker)
    kept = BUILD_CACHE / key(days[0]) if key and len(days) == 1 else None
    if kept is not None and not failed and (out / ticker / "timing.json").exists():
        tmp = kept.with_name(kept.name + f".{os.getpid()}.tmp")
        tmp.mkdir(parents=True, exist_ok=True)
        for name in _KEPT:
            if (out / ticker / name).exists():
                shutil.copy2(out / ticker / name, tmp / name)
        if kept.exists():
            shutil.rmtree(kept)
        tmp.rename(kept)
    return "built"


def store_fingerprint(db: Path) -> dict[str, list[int]]:
    """Each table's (rows, highest rowid), ``meta`` aside: cheap, and moved by any insert, delete
    or ``INSERT OR REPLACE`` (a replaced row takes a new rowid). The full content digest
    (`store_digest`) is the snapshot's identity; this is each build's write check."""
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
        names = [r[0] for r in c.execute("select name from sqlite_master where type='table' "
                                         "and name != 'meta' order by name")]
        return {t: list(c.execute(f"select count(*), coalesce(max(rowid), 0) from {t}")
                        .fetchone()) for t in names}


def _run_child(s: Settings, lay: Layout, side: str, ticker: str) -> None:
    """One page side in a SANDBOX of its own: a clone of the inputs tree and of the store
    snapshot (APFS clones: instant, no space). Parallel builds sharing one store collided on the
    schema stamp `Store` writes at every open ("database is locked", three pages of the first
    27-page run), and a build that wrote its store would have moved the next build's inputs."""
    out = s.out / "pages" / side
    env = page_env(s, lay.code[side])
    log = (out / ticker).with_suffix(".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    box = s.out / "sandboxes" / side / ticker
    if box.exists():
        shutil.rmtree(box)
    cwd, db = box / "impact-inputs", box / "impact-store" / "data" / "vinci.db"
    snap = s.out / "store-snapshot" / "data" / "vinci.db"
    _clone(lay.inputs_src, cwd)
    _clone(snap, db)
    _link_ignored(cwd, s, db)
    with log.open("wb") as fh:
        rc = subprocess.run([s.python, "-P", str(CHILD), "--tickers", ticker, "--out", str(out),
                             "--expect-root", str(lay.code[side]), "--capture-child",
                             str(CAPTURE_CHILD), "--frozen-cache", "--soffice-profile",
                             str(s.out / "soffice" / f"{side}-{ticker}")],
                            cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT).returncode
    # a child that dies before its steps (an import, the --expect-root refusal) writes no step
    # error: say so, or the page reads "not compared" with no reason — and is never kept
    page_dir = out / ticker
    if rc != 0 and not (page_dir / "built.json").exists() \
            and not (page_dir / "build.error.json").exists():
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "build.error.json").write_text(json.dumps({
            "error": "ChildExit", "message": f"the {side} child exited {rc} before writing the "
            f"page — see {log.name}", "where": ""}), encoding="utf-8")
    if page_dir.is_dir():
        was = store_fingerprint(snap)
        wrote = {t: v for t, v in store_fingerprint(db).items() if was.get(t) != v}
        (page_dir / "store_written.json").write_text(json.dumps(wrote), encoding="utf-8")
    shutil.rmtree(box)


def _read(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _error(folder: Path, step: str) -> str | None:
    e = _read(folder / f"{step}.error.json")
    return f"{e['error']}: {e['message']}" if e else None


def compare_page(s: Settings, ticker: str) -> dict[str, Any]:
    f = {side: s.out / "pages" / side / ticker for side in SIDES}
    built = {side: _read(f[side] / "built.json") for side in SIDES}
    out: dict[str, Any] = {"ticker": ticker,
                           "errors": {side: {step: e for step in ("build", "render", "request",
                                                                   "committed_render")
                                             if (e := _error(f[side], step))}
                                      for side in SIDES},
                           "timing": {side: _read(f[side] / "timing.json") for side in SIDES}}
    reads = {side: _read(f[side] / "reads.json") or {} for side in SIDES}
    shared = set(reads["base"]) & set(reads["head"])
    out["inputs_differ"] = sorted(u for u in shared
                                  if reads["base"][u]["sha256"] != reads["head"][u]["sha256"])
    out["reads"] = {side: len(reads[side]) for side in SIDES}
    out["store_written"] = {side: _read(f[side] / "store_written.json") or {} for side in SIDES}
    out["live"] = {side: sorted(u for u, r in reads[side].items() if r["live"]) for side in SIDES}
    out["one_side_reads"] = {side: len(set(reads[side]) - shared) for side in SIDES}
    if built["base"] is None or built["head"] is None:
        out["status"] = "not compared"
        return out
    changes = value_changes(built["base"], built["head"], ignore=VOLATILE | {"inputs"})
    out["version_moves"] = [c.to_dict() for c in changes if c.path in VERSION_FIELDS]
    moves = [c for c in changes if c.path not in VERSION_FIELDS]
    out["moves"] = [c.to_dict() for c in moves]
    # every list family's population on each side, and how many of its members moved
    fam = {side: member_families(built[side]) for side in SIDES}
    moved = moved_members(c.path for c in moves)
    out["families"] = {f: {"base": fam["base"].get(f, 0), "head": fam["head"].get(f, 0),
                           "moved": moved.get(f, 0)}
                       for f in sorted(set(fam["base"]) | set(fam["head"]) | set(moved))}
    out["status"] = "moves" if moves else "same"
    # the synthesis request each side's own build would send
    req = {side: _read(f[side] / "request.json") for side in SIDES}
    out["request"] = request_diff(req["base"], req["head"])
    # the rendered surface: the $0 build's page, and the committed JSON, each by each side's code
    vers = sorted({str(built[side].get("extraction_version") or "") for side in SIDES})
    versions = vers if len(vers) > 1 else []
    for kind in ("built", "committed"):
        md = {side: (f[side] / f"{kind}.md") for side in SIDES}
        if all(p.exists() for p in md.values()):
            out[f"{kind}_md"] = text_diff(md["base"].read_text(), md["head"].read_text(),
                                          versions if kind == "built" else ())
    return out


#: A page flag naming a transcript the build could not convert (`ciq_sheets.unparsed_transcript_
#: flag`). On ONE side only, on one input, it is the machine (LibreOffice under load), not the code.
NOISE_FLAGS = ("transcripts on file but unparseable",)


def one_sided_noise(s: Settings, ticker: str) -> str | None:
    """The side whose build alone carries a `NOISE_FLAGS` flag, or None."""
    def noisy(side: str) -> bool:
        page = _read(s.out / "pages" / side / ticker / "built.json") or {}
        return any(f.startswith(NOISE_FLAGS) for f in page.get("qa_flags") or [])
    b, h = noisy("base"), noisy("head")
    return None if b == h else ("base" if b else "head")


def compare_unbuilt_renders(s: Settings, ticker: str, out: dict[str, Any]) -> None:
    """A page refused at a build still has its committed JSON re-rendered: compare that."""
    if "committed_md" in out:
        return
    md = {side: s.out / "pages" / side / ticker / "committed.md" for side in SIDES}
    if all(p.exists() for p in md.values()):
        out["committed_md"] = text_diff(md["base"].read_text(), md["head"].read_text())


def text_diff(a: str, b: str, versions: Sequence[str] = ()) -> dict[str, Any]:
    """Two texts line by line, the build's clock text normalised (`values.clock_text`). A line
    naming one of ``versions`` (the two sides' extraction versions, when they differ) is set
    apart and counted: a version bump moves it on every page, as `VERSION_FIELDS` does the JSON."""
    a, b = clock_text(a), clock_text(b)
    # the two file headers are the first two lines only: a content line removed or added that
    # itself begins "--" or "++" (a markdown rule, "---") prints as "----" and must stay counted
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0))[2:]
    body = [ln for ln in lines if not ln.startswith("@@")]
    marked = [ln for ln in body if any(v and v in ln for v in versions)]
    body = [ln for ln in body if ln not in marked]
    return {"identical": not body, "removed": sum(1 for ln in body if ln.startswith("-")),
            "added": sum(1 for ln in body if ln.startswith("+")), "lines": body,
            "version_lines": len(marked)}


def request_diff(base: Any, head: Any) -> dict[str, Any]:
    if base is None or head is None:
        return {"status": "not compared", "missing": [s for s, r in (("base", base), ("head", head))
                                                      if r is None]}
    from vinci.evals.metrics import user_sections
    from vinci.evals.replay import wire

    out: dict[str, Any] = {}
    reqs = {}
    for side, r in (("base", base), ("head", head)):
        calls = r["calls"]
        if not calls or any(wire(c) != wire(calls[0]) for c in calls[1:]):
            return {"status": "not compared", "why": f"{side}'s draws sent different requests"}
        reqs[side] = calls[0]
    b, h = reqs["base"], reqs["head"]
    out["identical"] = wire(b) == wire(h)
    out["sha256"] = {side: hashlib.sha256(wire(reqs[side]).encode()).hexdigest()
                     for side in SIDES}
    if not out["identical"]:
        bu, hu = user_sections(str(b["messages"][0]["content"])), user_sections(
            str(h["messages"][0]["content"]))
        out["sections"] = sorted(k for k in set(bu) | set(hu) if bu.get(k) != hu.get(k))
        out["system_equal"] = b.get("system") == h.get("system")
        out["tools_equal"] = json.dumps(b.get("tools")) == json.dumps(h.get("tools"))
        out["other_kwargs"] = sorted(k for k in set(b) | set(h)
                                     if k not in ("system", "messages", "tools")
                                     and json.dumps(b.get(k)) != json.dumps(h.get(k)))
        out["user_diff"] = text_diff(str(b["messages"][0]["content"]),
                                     str(h["messages"][0]["content"]))
    out["status"] = "compared"
    return out


def panel_requests(s: Settings, shas: dict[str, str]) -> dict[str, Any]:
    """The six frozen panel pages' requests at both refs, from the frozen inputs
    (`compare.compare_requests`): what a prompt change reaches, the page held fixed."""
    from vinci.evals import compare as cmp
    from vinci.evals import replay as rp

    # `compare_requests`' own loop, with the repository named: its defaults resolve git from the
    # module's location, which is not a checkout when the check runs from a copy of its code
    panel = rp.load_panel_file(PANEL_FILE)
    pages: dict[str, Any] = {}
    _own_profile_here(s.out / "soffice" / "panel")
    try:
        for t in panel["panel"]:
            meta = panel["pages"][t]
            page = rp.page_at(t, panel["freeze_ref"], expect_blob=meta["dossier_blob"],
                              repo=s.repo)
            tx = rp.transcript_for(t, ciq_root=s.ciq_root, expected=meta["transcripts"],
                                   page=page)
            d = cmp.page_diff(t, rp.capture_at(shas["base"], page, tx, repo=s.repo),
                              rp.capture_at(shas["head"], page, tx, repo=s.repo))
            pages[t] = {"identical": d.identical, "system_equal": d.system_equal,
                        "user_diff_lines": d.user_diff_lines}
    except (rp.ReplayError, OSError, subprocess.CalledProcessError) as exc:
        return {"status": "refused", "why": cut(f"{type(exc).__name__}: {exc}", 1200),
                "pages": pages}
    return {"status": "compared", "pages": pages}


def _own_profile_here(profile: Path) -> None:
    """The parent's own transcript reads (the panel replay) under a LibreOffice profile of its
    own, as each child's (`child.own_soffice_profile`, loaded by path: one implementation)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_impact_child", CHILD)
    if spec is None or spec.loader is None:
        raise ImpactError(f"cannot load {CHILD}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.own_soffice_profile(profile)


def stale_at_head(lay: Layout, ticker: str, s: Settings) -> dict[str, Any] | None:
    """Whether the committed ``dossier.md`` is what each side's code renders from the committed
    JSON: a page head's renderer moves and the PR did not re-render reads True for ``head``."""
    committed = lay.inputs_src / "data" / "dossiers" / ticker / "dossier.md"
    if not committed.exists():
        return None
    text = committed.read_text()
    out = {}
    for side in SIDES:
        md = s.out / "pages" / side / ticker / "committed.md"
        out[side] = None if not md.exists() else md.read_text() == text
    return out


# ------------------------------------------------------------------------------- 4b. the frontend

def frontend_build(s: Settings, lay: Layout, side: str, tickers: Sequence[str]) -> Path:
    """``frontend/build.py`` of the side's code, over the data ref's tree with every committed
    ``dossier.md`` replaced by the side's own render of the committed JSON. The side's ``vinci/``
    sits beside it: the build reads the extraction-version table from it (#988)."""
    root = s.out / "fe" / side
    if root.exists():
        shutil.rmtree(root)
    _clone(lay.inputs_src, root)
    _clone(lay.code[side] / "vinci", root / "vinci")
    shutil.copy2(lay.code[side] / "frontend" / "build.py", root / "frontend" / "build.py")
    for t in tickers:
        md = s.out / "pages" / side / t / "committed.md"
        if md.exists():
            shutil.copy2(md, root / "data" / "dossiers" / t / "dossier.md")
    done = subprocess.run([s.python, "frontend/build.py"], cwd=root, capture_output=True,
                          text=True, env=child_env(root, None))
    if done.returncode != 0:
        raise ImpactError(f"frontend build at {side} failed: {done.stderr.strip()[-800:]}")
    return root / "frontend"


def tree_diff(a: Path, b: Path) -> dict[str, Any]:
    """Files under two trees that differ; a JSON file is compared without its build clock."""
    fa = {str(p.relative_to(a)) for p in a.rglob("*") if p.is_file()}
    fb = {str(p.relative_to(b)) for p in b.rglob("*") if p.is_file()}
    differ: list[str] = []
    for rel in sorted(fa & fb):
        x, y = (a / rel).read_bytes(), (b / rel).read_bytes()
        if x == y:
            continue
        if rel.endswith(".json"):
            try:
                if not value_changes(json.loads(x), json.loads(y), ignore=CONSUMER_VOLATILE):
                    continue
            except ValueError:
                pass
        differ.append(rel)
    return {"only_base": sorted(fa - fb), "only_head": sorted(fb - fa), "differ": differ,
            "files": len(fa | fb)}


# ------------------------------------------------------------------------- 5. downstream readers

@dataclass(frozen=True)
class Consumer:
    name: str
    #: the consumer's own packages (their modules and what they import), and ``module:function``
    #: for a command handler whose reach is its own imports (`graph.function_imports`)
    entries: tuple[str, ...]
    #: ``python -m`` argv run in the side's tree, ``{ref}`` the store frontier, ``{out}`` a scratch
    #: folder; None: no offline runner (the frontend build is part 4's)
    argv: tuple[str, ...] | None
    outputs: tuple[str, ...] = ()
    #: committed snapshot tables loaded into the consumer's store first, by the ref's own
    #: ``Store.rebuild_from_snapshots`` — the working DB is a cache of them
    seed: tuple[str, ...] = ()


CONSUMERS = (
    Consumer("screens / G3", ("vinci.screens", "vinci.universe", "vinci.cli:_cmd_screen"),
             ("vinci.cli", "screen", "--ref", "{ref}"),
             ("data/snapshots/candidate_records.jsonl", "data/snapshots/screen_runs")),
    Consumer("decision ledger", ("vinci.ledger", "vinci.cli:_cmd_ledger"),
             ("vinci.cli", "ledger"), (), ("decision_ledger",)),
    # the production path: `run_monthly` seeds the store from the committed snapshots itself
    Consumer("scoring report", ("vinci.scoring", "vinci.orchestrator",
                                "vinci.cli:_cmd_run_monthly"),
             ("vinci.cli", "run-monthly", "--as-of", "{ref}"),
             ("data/snapshots/scoring_report.json", "data/snapshots/scoring_report.md")),
    Consumer("monitor", ("vinci.monitor", "vinci.cli:_cmd_monitor"),
             ("vinci.cli", "monitor", "--ref", "{ref}", "--out", "{out}"), ("{out}",)),
    Consumer("theme desk", ("vinci.theme_intelligence",
                            "vinci.theme_intelligence.__main__:cmd_publish"),
             ("vinci.theme_intelligence", "--data-dir", "{theme}", "publish", "--out", "{out}"),
             ("{out}",)),
    Consumer("frontend build", ("frontend/build.py",), None),
)


def run_consumer(s: Settings, lay: Layout, c: Consumer, side: str, ref: str) -> dict[str, Any]:
    root = s.out / "consumers" / c.name.split()[0].strip("/") / side
    if root.exists():
        shutil.rmtree(root)
    tree = root / "impact-inputs"
    _clone(lay.inputs_src, tree)
    db = root / "impact-store" / "data" / "vinci.db"
    _clone(s.out / "store-snapshot" / "data" / "vinci.db", db)   # a consumer may write its store
    _link_ignored(tree, s, db)
    scratch = root / "out"
    theme = None
    if "{theme}" in (c.argv or ()):
        if s.theme_data is None:
            return {"status": "not run", "why": "no theme registry given (--theme-data)"}
        theme = root / "theme-data"
        theme.mkdir(parents=True)
        for p in s.theme_data.iterdir():
            if p.name == "registry.db":
                snapshot_store(p, theme / "registry.db")
            else:
                (theme / p.name).symlink_to(p.resolve())
    argv = [a.format(ref=ref, out=str(scratch), theme=str(theme)) for a in (c.argv or ())]
    t0 = time.monotonic()
    seed = [x for t in c.seed for x in ("--seed", t)]
    try:
        done = subprocess.run([s.python, "-P", str(CHILD), "--expect-root", str(lay.code[side]),
                               "--frozen-cache", "--out", str(root / "reads.json"),
                               "--soffice-profile", str(root / "soffice"), *seed,
                               "--run-module", *argv],
                              cwd=tree, env=page_env(s, lay.code[side]),
                              capture_output=True, text=True, timeout=3600)
    except subprocess.TimeoutExpired:
        return {"status": "not run", "why": f"timed out after 3600 s at {side}"}
    outputs: dict[str, str] = {}
    for o in c.outputs:
        p = Path(o.format(out=str(scratch))) if "{out}" in o else tree / o
        for f in ([p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file())
                  if p.is_dir() else []):
            rel = str(f.relative_to(scratch if "{out}" in o else tree))
            outputs[rel] = f.read_text(errors="replace")
    stdout = done.stdout.replace(str(tree), "<tree>").replace(str(scratch), "<out>")
    return {"status": "ran", "exit": done.returncode, "stdout": stdout,
            "stderr_tail": done.stderr[-1500:], "outputs": outputs,
            "seconds": round(time.monotonic() - t0, 1)}


def consumer_diff(base: dict[str, Any], head: dict[str, Any]) -> dict[str, Any]:
    if base.get("status") != "ran" or head.get("status") != "ran":
        return {"status": "not run", "why": base.get("why") or head.get("why")}
    out: dict[str, Any] = {"status": "compared", "exit": {"base": base["exit"],
                                                         "head": head["exit"]},
                           "stdout": text_diff(base["stdout"], head["stdout"])}
    files: dict[str, Any] = {}
    for rel in sorted(set(base["outputs"]) | set(head["outputs"])):
        x, y = base["outputs"].get(rel), head["outputs"].get(rel)
        if x == y:
            continue
        if x is not None and y is not None and rel.endswith((".json", ".jsonl")):
            ch = _json_changes(x, y)
            if ch is not None and not ch:
                continue
        files[rel] = text_diff(x or "", y or "")
    out["files"] = files
    out["identical"] = (base["exit"] == head["exit"] and out["stdout"]["identical"]
                        and not files)
    # what it produced, so two empty runs never read as agreement
    out["produced"] = {side: {"stdout_lines": len(r["stdout"].splitlines()),
                              "files": len(r["outputs"]),
                              "bytes": sum(len(t) for t in r["outputs"].values())}
                       for side, r in (("base", base), ("head", head))}
    return out


def _json_changes(x: str, y: str) -> list[Change] | None:
    try:
        if x.lstrip().startswith(("{", "[")) and "\n{" not in x.strip():
            return value_changes(json.loads(x), json.loads(y), ignore=CONSUMER_VOLATILE)
        return value_changes([json.loads(ln) for ln in x.splitlines() if ln.strip()],
                             [json.loads(ln) for ln in y.splitlines() if ln.strip()],
                             ignore=CONSUMER_VOLATILE)
    except ValueError:
        return None


def downstream(s: Settings, lay: Layout, shas: dict[str, str], changed: Sequence[str],
               ref: str) -> dict[str, Any]:
    graph = merged_graph(lay)
    mods = sorted({m for p in changed if (m := ig.module_of(p)) is not None})
    importers = {m: {"direct": sorted(ig.direct_importers(graph, m)),
                     "transitive": sorted(ig.importers(graph, [m]))} for m in mods}
    rows = []
    for c in CONSUMERS:
        if c.name == "frontend build":
            why = sorted(p for p in changed if p == "frontend/build.py"
                         or p.startswith(("data/", "scenarios/")))
            hit = why
        else:
            starts = {m for m in graph for e in c.entries if ":" not in e
                      and (m == e or m.startswith(e + "."))}
            handlers = set()
            for e in c.entries:
                if ":" in e:
                    mod, _, fn = e.partition(":")
                    handlers.add(mod)   # the handler's own module changed: it may have
                    try:
                        starts |= ig.function_imports(lay.code["head"], mod, fn)
                    except LookupError:   # head renamed or removed it: reached, by assumption
                        starts |= set(graph)
            closure = ig.closure(graph, starts)
            hit = sorted(m for m in mods if m in closure or m in handlers)
        row: dict[str, Any] = {"name": c.name, "reached_by": hit}
        if not hit:
            row["result"] = {"status": "not reached"}
        elif c.argv is None:
            row["result"] = {"status": "see part 4"}
        elif c.name.startswith("screens") and not s.run_screen:
            row["result"] = {"status": "not run",
                             "why": "the screen re-ingests five years of grouped-daily bars and "
                                    "reads EDGAR for every survivor: pass --run-screen"}
        else:
            res = {side: run_consumer(s, lay, c, side, ref) for side in SIDES}
            row["result"] = consumer_diff(res["base"], res["head"])
        rows.append(row)
    return {"changed_modules": mods, "importers": importers, "consumers": rows}


# ---------------------------------------------------------------------------------- page reach

#: What a page build, its render and its synthesis capture import from (`child.page`).
PAGE_ROOTS = ("vinci.dossier.prespend", "vinci.dossier.assemble", "vinci.dossier.render",
              "vinci.dossier.synthesis")
#: Code that loads other code by name, which the static graph cannot follow: a change under it
#: is taken to reach the pages.
DYNAMIC = ("vinci.quality",)


def merged_graph(lay: Layout) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for side in SIDES:
        for m, deps in ig.import_graph(lay.code[side]).items():
            out.setdefault(m, set()).update(deps)
    return out


def page_reach(lay: Layout, paths: Sequence[str]) -> list[str]:
    """The PR's paths that can move a page, its request or its render: a module in the page
    builder's import closure at either ref, a committed input (``data/``, ``scenarios/``), the
    capture child, or a dynamically loaded package. Empty: the pages are the same by construction
    (static), and are not built unless ``--no-shortcut``."""
    closure = ig.closure(merged_graph(lay), PAGE_ROOTS)
    out = []
    for p in paths:
        m = ig.module_of(p)
        if (m is not None and (m in closure or any(m == d or m.startswith(d + ".")
                                                   for d in DYNAMIC))) \
                or p.startswith(("data/", "scenarios/")) or p == "vinci/evals/capture_child.py":
            out.append(p)
    return sorted(out)


# --------------------------------------------------------------------------------------- the run

#: Published files under `frontend/` — mirrors and artifacts the build or a pass writes. Every
#: other path there is SOURCE the browser runs (`app.js`, `lib/`, `views/` — proposal and verdict
#: presentation among it), and a change to it is a code change (Codex P1 on #1000, round 2).
FRONTEND_ARTIFACTS = ("frontend/dossiers/", "frontend/scenarios/", "frontend/monitor/",
                      "frontend/theme-intelligence/", "frontend/snapshots/")


def frontend_source_changes(s: Settings, shas: dict[str, str]) -> list[str]:
    out = st.git(s.repo, "diff", "--name-only", "--no-renames", shas["base"], shas["head"],
                 "--", "frontend")
    return sorted(p for p in out.splitlines() if p and not p.startswith(FRONTEND_ARTIFACTS))


def _same_code(s: Settings, shas: dict[str, str]) -> bool:
    def tree(ref: str, path: str) -> str:
        return st.git(s.repo, "rev-parse", f"{ref}:{path}").strip()
    return (tree(shas["base"], "vinci") == tree(shas["head"], "vinci")
            and not frontend_source_changes(s, shas))


def _write_side(path: Path, obj: Any) -> None:
    """A page side's own bookkeeping beside its build (its CIQ inputs) — never a page."""
    path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")


def _write_marker(path: Path, run_id: dict[str, str]) -> None:
    """The run folder's own identity (``--resume`` reads it) — never a page."""
    path.write_text(json.dumps(run_id), encoding="utf-8")


def run(s: Settings) -> dict[str, Any]:
    t_start = time.monotonic()
    if _inside(s.out, s.repo):
        raise ImpactError(f"--out {s.out} is inside the repository: requests carry licensed "
                          "transcript text, so the run is written outside it")
    # BASE IS THE MERGE BASE, never main's tip: a tip the branch has not merged carries commits
    # head lacks, and their reversal would read as the PR's own effect (review of this PR)
    tip = st.sha(s.repo, s.base)
    shas = {"base": st.merge_base(s.repo, tip, s.head), "head": st.sha(s.repo, s.head)}
    marker = s.out / "run.json"
    if s.out.exists() and any(s.out.iterdir()):
        was = _read(marker) if s.resume else None
        if was is None or was != {**shas, "store": str(s.store)}:
            raise ImpactError(f"--out {s.out} is not empty: one run, one folder (--resume only "
                              "continues a run of the same base, head and store)")
    s.out.mkdir(parents=True, exist_ok=True)
    _write_marker(marker, {**shas, "store": str(s.store)})
    ident = st.diff_identity(s.repo, shas["base"], shas["head"])
    report: dict[str, Any] = {
        "tool": "vinci.impact", "schema": 1,
        "stamp": {"date": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "base": {"ref": s.base, "sha": shas["base"], "tip": tip},
                  "head": {"ref": s.head, "sha": shas["head"]},
                  "diff_identity": ident},
    }
    same = _same_code(s, shas)
    report["same_code"] = same
    report["census"] = list(s.census)
    if same and s.shortcut:
        s.log("base and head carry the same vinci/ and frontend/build.py: nothing to run")
        report["shortcut"] = ("base and head carry byte-identical `vinci/` trees and no "
                              "frontend source change, so every page, request, render and "
                              "consumer is the same by construction")
        report["fail_first"] = part_one(s, shas)
        report["wall_seconds"] = round(time.monotonic() - t_start, 1)
        return report
    s.log("laying out code, inputs and the store …")
    lay = resume_layout(s) if s.resume and (s.out / "inputs-src").exists() else lay_out(s, shas)
    tickers = list(s.tickers) or sorted(
        p.name for p in (lay.inputs_src / "data" / "dossiers").iterdir()
        if (p / "dossier.json").is_file())
    snap = s.out / "store-snapshot" / "data" / "vinci.db"
    digest_jobs = {"snapshot": store_digest(snap, s.python)}
    report["stamp"]["inputs"] = {
        "data_ref": shas["head"], "pages": tickers, "ciq_root": s.ciq_root.name,
        "ciq": ciq_identity(s.ciq_root, tickers), "cache_root": str(s.cache_root.name),
        "store": {"source": s.store.parent.parent.name, **store_identity(snap)}}
    frontier = report["stamp"]["inputs"]["store"]["frontier"]
    reach = page_reach(lay, ident["paths"])
    report["page_reach"] = reach
    build_pages = bool(reach) or not s.shortcut
    with cf.ThreadPoolExecutor(max_workers=3) as side_pool:
        ff = side_pool.submit(part_one, s, shas)
        panel = (side_pool.submit(panel_requests, s, shas) if build_pages else None)
        t0 = time.monotonic()

        how: dict[str, dict[str, str]] = {}

        def key_for(side: str, t: str) -> Callable[[str], str] | None:
            # NO CACHE ON THE CONTROL: with one `vinci/` tree both sides share a key, so a
            # kept build would compare one build with itself and measure no noise at all
            if not s.shortcut:
                return None
            memo: dict[str, str] = {}   # one key per day: each costs four `git rev-parse`

            def key(day: str) -> str:
                if day not in memo:
                    memo[day] = build_key(s, lay, side, t, shas, report["stamp"]["inputs"], day)
                return memo[day]
            return key

        def page_task(t: str) -> None:
            for side in ("head", "base"):   # head first: base reads any response head fetched
                how.setdefault(t, {})[side] = run_child(s, lay, side, t, key_for(side, t))
            s.log(f"  {t}: head {how[t]['head']}, base {how[t]['base']}")
        if build_pages:
            with cf.ThreadPoolExecutor(max_workers=s.workers) as pool:
                list(pool.map(page_task, tickers))
        retried: dict[str, Any] = {}
        for t in (tickers if build_pages else []):
            side = one_sided_noise(s, t)
            if side is not None:   # a conversion failed on ONE side: the machine's, try once more
                shutil.rmtree(s.out / "pages" / side / t)
                _run_child(s, lay, side, t)
                retried[t] = {"side": side, "still": one_sided_noise(s, t) is not None}
                s.log(f"  {t}: {side} re-built after a one-sided transcript failure")
        realigned: dict[str, Any] = {}

        def realign(t: str) -> None:
            """Both sides built within one UTC day (`build_days`), or the off-day side once more."""
            sides = off_day_sides(s, t)
            if not sides:
                return
            was = {side: build_days(s.out / "pages" / side / t) for side in SIDES}
            for side in (x for x in ("head", "base") if x in sides):   # head first, as above
                shutil.rmtree(s.out / "pages" / side / t)
                how[t][side] = run_child(s, lay, side, t, key_for(side, t))
            realigned[t] = {"sides": sides, "days": was, "still": bool(off_day_sides(s, t))}
            if t in retried:   # the re-build replaced the side the transcript retry judged
                retried[t]["still"] = one_sided_noise(s, t) is not None
            s.log(f"  {t}: {', '.join(sides)} re-built — the sides were built on "
                  f"{was['base']} and {was['head']} (UTC)")
        if build_pages:
            with cf.ThreadPoolExecutor(max_workers=s.workers) as pool:
                list(pool.map(realign, tickers))
        pages_seconds = round(time.monotonic() - t0, 1)
        pages = []
        for t in (tickers if build_pages else []):
            res = compare_page(s, t)
            if t in retried:
                res["retried"] = retried[t]
                if retried[t]["still"]:
                    res["status"] = "noise"
            if t in realigned:
                res["realigned"] = realigned[t]
                if realigned[t]["still"]:
                    res["status"] = "noise"
            compare_unbuilt_renders(s, t, res)
            res["committed_md_matches"] = stale_at_head(lay, t, s)
            pages.append(res)
        report["pages"] = {"seconds": pages_seconds, "workers": s.workers, "results": pages,
                           "built": build_pages, "how": how}
        fe = {side: frontend_build(s, lay, side, tickers) for side in SIDES}
        report["frontend"] = tree_diff(fe["base"], fe["head"])
        report["frontend"]["pr_edits"] = sorted(p for p in ident["all_paths"]
                                                if p.startswith("frontend/"))
        report["frontend"]["source_edits"] = frontend_source_changes(s, shas)
        report["downstream"] = downstream(s, lay, shas, ident["paths"], frontier)
        report["panel_requests"] = (panel.result() if panel is not None else
                                    {"status": "not reached"})
        report["fail_first"] = ff.result()
    ciq_after = ciq_identity(s.ciq_root, tickers)
    report["stamp"]["inputs"]["ciq_moved_during_run"] = sorted(
        t for t in tickers if ciq_after[t] != report["stamp"]["inputs"]["ciq"][t])
    digests = {k: _digest_result(p) for k, p in digest_jobs.items()}
    report["stamp"]["inputs"]["store"]["content"] = digests["snapshot"]
    # each page side built on its own clone of the snapshot (`_run_child`): which wrote it
    report["stamp"]["inputs"]["store"]["written_by"] = sorted(
        f"{p['ticker']} ({side}: {', '.join(sorted(p['store_written'][side]))})"
        for p in report.get("pages", {}).get("results", []) for side in SIDES
        if (p.get("store_written") or {}).get(side))
    report["wall_seconds"] = round(time.monotonic() - t_start, 1)
    return report
