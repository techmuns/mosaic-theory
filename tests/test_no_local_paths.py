"""NO COMMITTED PAGE, MIRROR OR FIXTURE CARRIES AN ABSOLUTE LOCAL PATH (2026-11-05).

THE REPOSITORY IS PUBLIC (since 2026-10-22), and on 2026-11-05 a review of #911 found every
committed page stamping its price store by absolute path: `price_store.declared_path` and
`resolved_path`, 54 paths across the 27 pages in `data/dossiers/*/dossier.json` and 54 more in
their `frontend/dossiers/*.json` mirrors, plus 10 in five test fixtures — 118 in all. They named
usernames (`/Users/<user>/…`), worktree names and Claude session scratch directories
(`/private/tmp/claude-501/…`). The rendered `.md` never printed them: `render._price_store_line`
shows only the checkout's folder name, and since this date the stamp keeps only that
(`assemble.store_checkout`).

THIS GUARD READS WHAT IS COMMITTED, NOT ONE FIELD. A check on `price_store` alone would pass the
next field that carries a path — #911's round 1 had already removed one, from an OSError's reason
text. So every file under every committed artifact folder — all of `data/`, `frontend/` and
`scenarios/`, plus `tests/fixtures/` — is scanned, whatever key the path sits in. That takes in
the build run records (`data/snapshots/assembly_runs/`), which carry free-text exception messages
(`run_metrics`) and, since #911, each build's input manifest. Widened in #915's round 2 at a
cost of nothing: every hit the four folders (1,100 files, 147 MB) held on main c4c9f432 was a
price-store stamp, and on the cleaned tree they hold none. Widened again on 2026-11-12 (STATE row
49) to the agent config and the local gate, `.claude/` and `bin/`, once their one per-machine file
was git-ignored: at main 407dc809 the widened scan found 18 hits in 1,441 files, all in the then
tracked `.claude/launch.json`, and none once it was ignored. The records' prose (`docs/records/`)
stays outside it, as written, by the same default. Widened a third time on 2026-11-13 (the
operator: "Guard them too (Recommended)") to the theme desk's committed logs
(`docs/theme_intelligence/`) and STATE.md: over main f2e31cea's blobs the two held 9 hits in 2 of
597 files, a session scratchpad in one run log (2) and row 38's machine folders (7), and none once
scrubbed.

    python -m tests.test_no_local_paths     # print every hit, file:line, with the count

THE PATTERN. An absolute path under a home, temp or mount root — `/Users/`, `/private/`, `/home/`
(a Linux home or a CI runner's `/home/runner/…`), `/Volumes/`, `/root/`, WSL's `/mnt/<drive>/` —
or a drive letter (`C:\\…`, `D:/…`), or the DASHED form a Claude project folder takes
(`-Users-<user>-Documents-…`), which a store stamped from inside one would carry. A path must
START there: a URL's `/home/` follows its host and is not one, which is the false positive a bare
substring check would raise on the first investor page cited from `…/home/default.aspx`; nor is a
relative `../home/…`.

WHAT IT DOES NOT CATCH, stated so nobody reads 0 as more than it is: a bare username, a relative
path, a Linux `/tmp/…` or `/var/…`, and the inside of a COMPRESSED binary (an `.xlsx`'s zip
members, a PDF's Flate streams, a Parquet page). A binary file is read as Latin-1 for the POSIX
roots only: a PDF's metadata can carry its author's path in the clear, while a drive letter is
three bytes compressed data produces at random. The writer side is narrower still:
`store_checkout` refuses any store not at `<checkout>/data/vinci.db`.

FIX FOR A HIT IN A PRICE-STORE STAMP: `PYTHONPATH=$PWD python scripts/rewrite_store_stamps.py
<file> …` rewrites the two fields in place to their folder names and nothing else, then rebuild
the mirrors (`python frontend/build.py`). Any other hit is a new leak: remove it at its writer.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Every committed artifact folder — pages, mirrors, run records, snapshots, scenarios, the web
#: app's data — and every test fixture. And since 2026-11-12 (STATE row 49, the coordinator's
#: default 6 — not an operator ruling) the agent config and the local gate: not artifacts, but
#: where a survey of every other tracked file at main c4c9f432 found per-machine paths outside the
#: records' prose — `.claude/launch.json` 18 (now git-ignored, so not read) and `bin/commit` 1
#: (removed by #996, RH-D3). And since 2026-11-13 (the operator: "Guard them too (Recommended)")
#: the theme desk's committed run logs and STATE.md, the two places that survey left: at main
#: f2e31cea, `docs/theme_intelligence/` 2 (a session scratchpad in one run log) and STATE.md 7
#: (row 38's two machines' user folders). `docs/records/` stays outside: records stay as written.
SCANNED = ("data", "frontend", "scenarios", "tests/fixtures", ".claude", "bin",
           "docs/theme_intelligence", "STATE.md")

#: An absolute POSIX path under a home, temp or mount root, where it begins. The lookbehind keeps a
#: URL out: a URL's path follows a host character (`sec.gov/…`, `:8080/…`), a local path follows a
#: quote, a space, a backtick, a `${VAR:-` default, a line start or `file://` — never a `.`
#: (`../home/` is relative). Matched on BYTES (a binary is read as is; UTF-8 text keeps its ASCII
#: bytes), so `\w` is ASCII: a non-ASCII letter before a root does not hide it.
POSIX_ROOT = re.compile(rb"(?<![\w.])/(?:Users|private|home|Volumes|root)/"
                        rb"|(?<![\w.])/mnt/[A-Za-z]/")
#: A Claude project folder's dashed path (`-Users-<user>-…`), standing alone.
DASHED = re.compile(rb"(?<![\w-])-(?:Users|home)-[\w.]")
#: A drive letter standing alone (not `https:`, not `s3:`, not `x.c:` or `a+b:`), then a separator
#: that does not start a `//` scheme. Three characters, so it is read in TEXT only: over the 547
#: binary files tracked on 2026-11-05 (47 MB) it matched 82 times — random bytes, every one — and
#: the POSIX roots 0.
DRIVE = re.compile(rb"(?<![\w.+\-])[A-Za-z]:(?:\\|/(?!/))")
#: SPEED ONLY, never a definition. A regex led by a lookbehind is tried at every byte — 20 s over
#: the 147 MB in scope (2026-11-05) — so a file runs `POSIX_ROOT` / `DASHED` only if it holds one
#: of their literal cores (`_TRIGGER`, which must cover both: the LEAKED pins go through it), and
#: `DRIVE` only at a `:` before a separator (`_COLON`). About 2 s.
_TRIGGER = re.compile(rb"/(?:Users|private|home|Volumes|root|mnt)/|-(?:Users|home)-")
_COLON = re.compile(rb":[\\/]")

#: How much of a hit is printed; a longer one ends in `CUT`, so a cut path never reads as whole.
SHOWN = 60
CUT = "… [cut]"


def _matches(raw: bytes, *, binary: bool) -> list[tuple[int, str]]:
    """(line number, the hit as printed) for each local path in `raw`. In a `binary` file, the
    POSIX roots only (see `DRIVE`). The printed hit runs to `SHOWN` bytes or its line's end,
    whichever is first, and carries `CUT` if its line goes on past it."""
    starts: set[int] = set()
    if _TRIGGER.search(raw):
        for rx in (POSIX_ROOT,) if binary else (POSIX_ROOT, DASHED):
            starts.update(m.start() for m in rx.finditer(raw))
    if not binary:
        starts.update(m.start() - 1 for m in _COLON.finditer(raw)
                      if m.start() and DRIVE.match(raw, m.start() - 1))
    out: list[tuple[int, str]] = []
    for i in sorted(starts):
        eol = raw.find(b"\n", i)
        eol = len(raw) if eol < 0 else eol
        stop = min(i + SHOWN, eol)
        hit = raw[i:stop].decode("latin-1" if binary else "utf-8", errors="replace")
        out.append((raw.count(b"\n", 0, i) + 1, hit + (CUT if stop < eol else "")))
    return out


def local_paths(text: str, *, binary: bool = False) -> list[str]:
    """Each absolute local path in `text`, as printed (`_matches`). A `binary` file's text is its
    Latin-1 decoding, read for the POSIX roots only."""
    raw = text.encode("latin-1" if binary else "utf-8")
    return [hit for _, hit in _matches(raw, binary=binary)]


def _corpus() -> list[Path]:
    """Every file under `SCANNED` that is committed or about to be: tracked, plus untracked and not
    ignored — an artifact pass runs the suite BEFORE `git add`, and a new page must be read then,
    not first in CI. A tracked file deleted in the working tree is not there to read."""
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others",
                          "--exclude-standard", "--", *SCANNED],
                         capture_output=True, check=True).stdout
    return sorted({ROOT / p for p in out.decode().split("\0") if p and (ROOT / p).is_file()})


def scan() -> tuple[list[Path], list[str]]:
    """(the files scanned, every hit as `path:line: text`) over the corpus — the list never cut."""
    files = _corpus()
    hits: list[str] = []
    for f in files:
        raw = f.read_bytes()
        try:
            raw.decode("utf-8")
            binary = False
        except UnicodeDecodeError:
            binary = True
        hits += [f"{f.relative_to(ROOT)}:{n}: {h.strip()}" for n, h in _matches(raw, binary=binary)]
    return files, hits


# --- the matcher, on the shapes the corpus actually held -----------------------------------------

#: (+) Real stamps the committed corpus carried on 2026-11-05 (main c4c9f432), one of each kind and
#: with each username replaced by `u` (this file is public too) —
#: plus the CI runner's home and both drive-letter forms as they appear in JSON text.
LEAKED = (
    '"declared_path": "/Users/u/Documents/GitHub/mosaic-theory/.claude/worktrees/'
    'eager-mendel-4c6d33/data/vinci.db",',
    '"resolved_path": "/Users/u/Documents/GitHub/mosaic-theory-wb/data/vinci.db",',
    '"declared_path": "/private/tmp/claude-501/-Users-u-Documents-GitHub-mosaic-theory/'
    'd46b7606/scratchpad/wt-pass/data/vinci.db",',
    "a reason quoting /home/runner/work/mosaic-theory/mosaic-theory/data/vinci.db",
    '"declared_path": "C:\\\\Users\\\\x\\\\mosaic-theory\\\\data\\\\vinci.db",',
    "`D:/a/mosaic-theory/data/vinci.db`",
    "file:///Users/x/report.pdf",
    # a shell default, the shape `bin/commit` carried until #996 (RH-D3)
    'VENV="${VENV:-/Users/x/mosaic-theory/.venv/bin/python}"',
    # the other mount and home roots, and WSL's view of a Windows drive (round 2: synthetic — the
    # corpus has held none)
    "`/Volumes/ext/mosaic-theory/data/vinci.db`",
    '"/root/mosaic-theory/data/vinci.db"',
    "a store at /mnt/c/Users/x/mosaic-theory/data/vinci.db",
    "/mnt/d/repos/mosaic-theory/data/vinci.db",   # no other root in it: the trigger alone
    # a store stamped from inside a Claude project folder: standalone here; on main c4c9f432 the
    # form sat inside all 26 `/private/tmp/claude-501/-Users-<user>-…` stamps (round 2)
    '"declared_path": "-Users-alice-Documents-GitHub-mosaic-theory",',
)

#: (−) What must not fire: the cleaned stamp, a relative store path, and URLs — the `https:` drive
#: letter is the false positive a first cut of this pattern raised in 24 committed `.md` files at
#: main c4c9f432 (12 pages' `dossier.md` and their 12 `frontend/dossiers/` mirrors).
CLEAN = (
    '"declared_path": "eager-mendel-4c6d33",',
    '"resolved_path": "mosaic-theory-wb",',
    "data/vinci.db",
    "https://www.sec.gov/Archives/edgar/data/1579298/000157929826000012/0001579298-26-000012.txt",
    "https://investor.example.com/home/default.aspx and https://x.com:8080/private/a",
    "s3://bucket/key r2://facts/objects/edgar/0000320187",
    "Monthly Active Users/Subscribers grew; EV/EBITDA 12.0x; Q3: 10:30 ET",
    # round 2, each killing a surviving mutant: `.` before a root is a relative path; `a://` is a
    # scheme (a digit precedes `s3:`'s colon, so it never reached the drive check); a letter after
    # `.`, `+` or `-` is the tail of a word, not a drive (synthetic)
    "../home/x/data/vinci.db",
    "a://x",
    "notes.a:/b  svn+a:/b  pre-a:/b",
    "Monthly-Active-Users-grew",
)


@pytest.mark.parametrize("text", LEAKED)
def test_the_matcher_catches_each_shape_of_local_path(text: str) -> None:
    assert local_paths(text), text


@pytest.mark.parametrize("text", CLEAN)
def test_the_matcher_passes_a_url_a_relative_path_and_a_folder_name(text: str) -> None:
    assert not local_paths(text), (text, local_paths(text))


def test_a_binary_file_is_read_for_the_posix_roots_and_not_the_drive_letter() -> None:
    """(+) A PDF's metadata path is still caught; (−) the three bytes `x:/` that compressed data
    throws up at random are not."""
    blob = b"%PDF-1.7\x00\x9cQ:/\xff\x00<xmp:CreatorTool>/Users/x/Downloads/a.pdf</xmp>"
    text = blob.decode("latin-1")
    assert [h[:9] for h in local_paths(text, binary=True)] == ["/Users/x/"]
    assert len(local_paths(text)) == 2, "as text, the drive-letter bytes would have matched too"


def test_a_hit_cut_short_says_so_and_a_whole_one_does_not() -> None:
    long = "/Users/x/" + "a" * 80
    assert local_paths(long) == [long[:SHOWN] + CUT]
    assert local_paths('"/Users/x/y"') == ['/Users/x/y"'], "a hit that fits must not claim a cut"


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tracked: dict[str, str | bytes],
          untracked: dict[str, str | bytes] | None = None) -> Path:
    """A throwaway git repository the scan is pointed at (`ROOT`), so a killed run leaves nothing
    in this one. The machine's own excludes are switched off for it (`core.excludesFile`, set
    through git's command-environment config, which outranks every config file): a global ignore
    of `bin/` or `.claude/` — common ones — would otherwise keep a tracked file out of `git add`
    and an untracked one out of the scan, and the pins would test that machine, not the repo's
    `.gitignore`."""
    for k, v in {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.excludesFile",
                 "GIT_CONFIG_VALUE_0": os.devnull}.items():
        monkeypatch.setenv(k, v)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    for batch, add in ((tracked, True), (untracked or {}, False)):
        for rel, body in batch.items():
            f = repo / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(body if isinstance(body, bytes) else body.encode())
        if add:
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    monkeypatch.setattr(sys.modules[__name__], "ROOT", repo)
    return repo


def test_every_folder_every_kind_of_file_and_every_line_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(+) One path per place the scan must reach (round 2: each line kills a surviving mutant):
    deep in a page laid out as the writer lays one out (`indent=2`), not on its first line; a
    rendered `.md`; a web mirror under `frontend/`; a scenario record; a build's run record; a
    Windows path in plain text (a binary-only read drops the drive letter); a PDF's metadata (a
    text-only read drops it). (−) A file outside the scanned folders is not read."""
    page = json.dumps({"ticker": "T", "mechanical": {"a": 1, "b": [1, 2]},
                       "price_store": {"declared_path": "/Users/x/w/data/vinci.db"}}, indent=2)
    _repo(tmp_path, monkeypatch, {
        "data/dossiers/T/dossier.json": page,
        "data/dossiers/T/dossier.md": "# T\n\n- **Price store:** `/home/x/w`\n",
        "frontend/dossiers/T.json": '{\n  "x": "/private/tmp/s/data/vinci.db"\n}\n',
        "scenarios/T.json": '{"spot_source": "read /Volumes/ext/vinci.db"}\n',
        "data/snapshots/assembly_runs/r.jsonl":
            '{"ticker": "A"}\n{"error": "OSError: [Errno 2] /Users/x/data/vinci.db"}\n',
        "tests/fixtures/win.txt": "store: C:\\Users\\x\\data\\vinci.db\n",
        "tests/fixtures/meta.pdf": b"%PDF-1.7\n\x9c\xff\x00/Author (/Users/x/a.pdf)\n",
        "docs/elsewhere.md": "/Users/x/outside the scope\n",
    })
    files, hits = scan()
    assert len(files) == 7, files
    where = sorted(h.split(": ", 1)[0] for h in hits)
    assert where == ["data/dossiers/T/dossier.json:11", "data/dossiers/T/dossier.md:3",
                     "data/snapshots/assembly_runs/r.jsonl:2", "frontend/dossiers/T.json:2",
                     "scenarios/T.json:1", "tests/fixtures/meta.pdf:2",
                     "tests/fixtures/win.txt:1"], hits


def test_the_agent_config_and_the_local_gate_are_read_and_the_preview_config_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """STATE row 49, widened 2026-11-12 under the coordinator's default 6 (not an operator
    ruling). (+) A local path in `.claude/` or `bin/` is a hit, tracked or about to be: on main
    c4c9f432 `.claude/launch.json` held 18 and `bin/commit` 1 (removed by #996, RH-D3). (−) The
    per-machine preview config, `.claude/launch.json`, is not read: it names its own checkout's
    folders by design, so THIS repository's `.gitignore` (copied in, not restated) keeps it out of
    git and out of the scan. The shared settings beside it are still read (+)."""
    gitignore = (ROOT / ".gitignore").read_text()
    _repo(tmp_path, monkeypatch, {
        ".gitignore": gitignore,
        ".claude/settings.json": '{"hooks": {"command": "/Users/x/hooks/gate.py"}}\n',
        "bin/commit": 'VENV="${VENV:-/Users/x/mosaic-theory/.venv/bin/python}"\n',
    }, {
        ".claude/launch.json": '{"runtimeArgs": ["--directory", "/Users/x/m/frontend"]}\n',
        ".claude/hooks/new_hook.py": "# reads /private/tmp/claude-501/x/scratchpad\n",
    })
    files, hits = scan()
    assert ".claude/launch.json" not in {str(f.relative_to(ROOT)) for f in files}, files
    where = sorted(h.split(": ", 1)[0] for h in hits)
    assert where == [".claude/hooks/new_hook.py:1", ".claude/settings.json:1",
                     "bin/commit:1"], hits


def test_the_theme_desk_logs_and_state_are_read_and_the_records_are_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The operator, 2026-11-13: "Guard them too (Recommended)". (+) A local path in a committed
    theme-desk run log, or in STATE.md, is a hit: at main f2e31cea the guard did not read either,
    and `docs/theme_intelligence/state-pull-ledger-2026-10-11/run-log.txt` held 2 (one session
    scratchpad, matched by the root and its dashed form) and STATE.md row 38 held 7 (the two
    machines' user folders). (−) A record is not read: records stay as written, and a record's
    body is immutable once merged."""
    _repo(tmp_path, monkeypatch, {
        "STATE.md": "| 38 | score on `/Users/x`'s store |\n",
        # the shape line 16 held at main f2e31cea, its user replaced by `u`: the root and the
        # dashed project folder inside it, two hits on one line
        "docs/theme_intelligence/a-2026-10-11/run-log.txt":
            "$ ingest-file --path /private/tmp/claude-501/-Users-u-Documents-GitHub-m/s/"
            "scratchpad/input/a.md\n",
        "docs/records/2026-11-05-r.md": "a record quoting /Users/x/Documents/a\n",
        "docs/README.md": "/Users/x/elsewhere in docs\n",
    })
    files, hits = scan()
    assert {str(f.relative_to(ROOT)) for f in files} == {
        "STATE.md", "docs/theme_intelligence/a-2026-10-11/run-log.txt"}, files
    where = sorted(h.split(": ", 1)[0] for h in hits)
    assert where == ["STATE.md:1", "docs/theme_intelligence/a-2026-10-11/run-log.txt:1",
                     "docs/theme_intelligence/a-2026-10-11/run-log.txt:1"], hits


def test_a_printed_hit_stops_at_its_line() -> None:
    assert local_paths('"/Users/x/y"\nnext line') == ['/Users/x/y"']


def test_a_file_not_yet_added_is_read_and_an_ignored_one_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An artifact pass runs the suite before `git add`, so a new page or fixture is read while it
    is still untracked — not first in CI (+); a git-ignored file (`llm_call.log`) is not (−). In a
    scratch repository, so a killed run leaves nothing in this one."""
    _repo(tmp_path, monkeypatch,
          {".gitignore": "*.log\n", "tests/fixtures/tracked.json": '{"a": 1}\n'},
          {"tests/fixtures/new.json": '{"reason": "read /Users/x/data/vinci.db"}\n',
           "tests/fixtures/llm_call.log": "read /Users/x/data/vinci.db\n"})

    files, hits = scan()
    assert {f.name for f in files} == {"tracked.json", "new.json"}
    assert hits == ["tests/fixtures/new.json:1: /Users/x/data/vinci.db\"}"], hits


def test_a_tracked_file_deleted_in_the_working_tree_is_skipped_not_a_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """git still lists a tracked file deleted but not staged; reading it would raise."""
    gone = "tests/fixtures/_deleted_but_tracked.json"
    real = subprocess.run

    def ls_files(args: list[str], **kw: object) -> subprocess.CompletedProcess[bytes]:
        done = real(args, **kw)  # type: ignore[call-overload]
        return subprocess.CompletedProcess(args, 0, done.stdout + gone.encode() + b"\0", b"")

    monkeypatch.setattr(subprocess, "run", ls_files)
    files = _corpus()
    assert files and ROOT / gone not in files


# --- the corpus -----------------------------------------------------------------------------------

def test_no_committed_page_mirror_or_fixture_carries_an_absolute_local_path() -> None:
    """THE GUARD. On main c4c9f432, over the four folders (1,100 files), it lists 144 hits on 118
    lines of 59 files — every line a price-store stamp, 26 of them carrying both `/private/` and
    the dashed `-Users-` session folder; on the cleaned tree it lists none. Over the six folders
    at main 407dc809 (1,441 files) it listed 18, every one in the then-tracked
    `.claude/launch.json`; with that file git-ignored it lists none. Over all eight scopes on the
    scrubbed tree of 2026-11-13 (2,037 files) it lists none. The count is printed beside the full
    list, never a cut."""
    files, hits = scan()
    pages = set((ROOT / "data" / "dossiers").glob("*/dossier.json"))
    assert pages and pages <= set(files), (
        f"the scan ({len(files)} files under {SCANNED}) misses pages: "
        f"{sorted(str(p.relative_to(ROOT)) for p in pages - set(files))}")
    assert not hits, (
        f"{len(hits)} absolute local path(s) in the corpus ({len(files)} files scanned); this "
        "repository is public. A price-store stamp is fixed by scripts/rewrite_store_stamps.py; "
        "a machine's folder in STATE.md is named by its role instead; anything else is a new "
        "leak, removed at its writer:\n" + "\n".join(hits))


def test_every_committed_page_prints_the_price_store_line_its_stamp_renders() -> None:
    """END TO END, committed JSON → render → committed `.md`: the folder-name stamp each page now
    carries renders the very line its committed page prints, so the rewrite changed no rendered
    page. A phrasing-independent invariant on living artifacts — it pins that the two agree, not
    what either says."""
    from vinci.dossier.render import _price_store_line
    from vinci.dossier.schemas import PriceStoreStamp

    pages = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
    assert pages, "no committed pages — this test would pass vacuously"
    stamped = 0
    for p in pages:
        raw = json.loads(p.read_text()).get("price_store")
        if raw is None:
            continue
        stamped += 1
        line = _price_store_line(PriceStoreStamp.model_validate(raw))
        assert line in (p.parent / "dossier.md").read_text(), (p.parent.name, line)
    assert stamped, "no committed page carries a price-store stamp — the test reads nothing"


if __name__ == "__main__":
    scanned, found = scan()
    print(f"{len(found)} absolute local path(s) in {len(scanned)} files under "
          f"{', '.join(SCANNED)}")
    print("\n".join(found))
    sys.exit(1 if found else 0)
