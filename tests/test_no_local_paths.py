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
text. So every tracked file under the three folders is scanned, as text, whatever key it sits in.

    python -m tests.test_no_local_paths     # print every hit, file:line, with the count

THE PATTERN, and what it does not catch. An absolute path under `/Users/`, `/private/` or
`/home/` (macOS home and temp roots, a Linux home or a CI runner's `/home/runner/…`), or a drive
letter (`C:\\…`, `D:/…`). The path must START there: a URL's `/home/` follows its host and is
not one, which is the false positive a bare substring check would raise on the first investor
page cited from `…/home/default.aspx`. NOT caught: a bare username or a relative path, a Linux
`/tmp/…` or `/var/…`, and a store whose checkout folder is itself a username (`store_checkout`
of `/Users/x/data/vinci.db` is `x`). Binary files are read too, as Latin-1 and for the POSIX
roots only (a PDF's metadata can carry its author's path; a drive letter is three bytes that
compressed data produces at random); none of the 16 in scope matches today.

FIX FOR A HIT IN A PRICE-STORE STAMP: `PYTHONPATH=$PWD python scripts/rewrite_store_stamps.py
<file> …` rewrites the two fields in place to their folder names and nothing else, then rebuild
the mirrors (`python frontend/build.py`). Any other hit is a new leak: remove it at its writer.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: The committed pages, their web mirrors and every test fixture.
SCANNED = ("data/dossiers", "frontend/dossiers", "tests/fixtures")

#: An absolute POSIX path under a home or temp root, where it begins. The lookbehind keeps a URL
#: out: a URL's path follows a host character (`sec.gov/…`, `:8080/…`), a local path follows a
#: quote, a space, a backtick, a `${VAR:-` default, a line start or `file://`.
POSIX_ROOT = re.compile(r"(?<![\w.])/(?:Users|private|home)/")
#: A drive letter standing alone (not `https:`, not `s3:`), then a separator that does not start a
#: `//` scheme. Three characters, so it is read in TEXT only: over the 547 binary files tracked on
#: 2026-11-05 (47 MB) it matched 82 times — random bytes, every one — and the POSIX roots 0.
DRIVE = re.compile(r"(?<![\w.+\-])[A-Za-z]:(?:\\|/(?!/))")


def local_paths(text: str, *, binary: bool = False) -> list[str]:
    """Each absolute local path in `text`, as the 60 characters from where it starts. In a
    `binary` file's Latin-1 text, the POSIX roots only (see `DRIVE`)."""
    found = sorted(m.start() for rx in ((POSIX_ROOT,) if binary else (POSIX_ROOT, DRIVE))
                   for m in rx.finditer(text))
    return [text[i:i + 60] for i in found]


def _tracked() -> list[Path]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--", *SCANNED],
                         capture_output=True, check=True).stdout
    return [ROOT / p for p in out.decode().split("\0") if p]


def scan() -> tuple[int, list[str]]:
    """(files scanned, every hit as `path:line: text`) over the committed corpus — never cut."""
    files = _tracked()
    hits: list[str] = []
    for f in files:
        raw = f.read_bytes()
        try:
            text, binary = raw.decode("utf-8"), False
        except UnicodeDecodeError:
            text, binary = raw.decode("latin-1"), True
        for n, line in enumerate(text.splitlines(), 1):
            for h in local_paths(line, binary=binary):
                hits.append(f"{f.relative_to(ROOT)}:{n}: {h.strip()}")
    return len(files), hits


# --- the matcher, on the shapes the corpus actually held -----------------------------------------

#: (+) Real stamps the committed corpus carried on 2026-11-05 (main c4c9f432) — one of each kind —
#: plus the CI runner's home and both drive-letter forms as they appear in JSON text.
LEAKED = (
    '"declared_path": "/Users/mac/Documents/GitHub/mosaic-theory/.claude/worktrees/'
    'eager-mendel-4c6d33/data/vinci.db",',
    '"resolved_path": "/Users/work/Documents/GitHub/mosaic-theory-wb/data/vinci.db",',
    '"declared_path": "/private/tmp/claude-501/-Users-work-Documents-GitHub-mosaic-theory/'
    'd46b7606/scratchpad/wt-pass/data/vinci.db",',
    "a reason quoting /home/runner/work/mosaic-theory/mosaic-theory/data/vinci.db",
    '"declared_path": "C:\\\\Users\\\\x\\\\mosaic-theory\\\\data\\\\vinci.db",',
    "`D:/a/mosaic-theory/data/vinci.db`",
    "file:///Users/x/report.pdf",
    # a shell default, the shape `bin/commit` carries (outside this guard's scope)
    'VENV="${VENV:-/Users/x/mosaic-theory/.venv/bin/python}"',
)

#: (−) What must not fire: the cleaned stamp, a relative store path, and URLs — the `https:` drive
#: letter is the false positive a first cut of this pattern raised on 12 committed `.md` pages.
CLEAN = (
    '"declared_path": "eager-mendel-4c6d33",',
    '"resolved_path": "mosaic-theory-wb",',
    "data/vinci.db",
    "https://www.sec.gov/Archives/edgar/data/1579298/000157929826000012/0001579298-26-000012.txt",
    "https://investor.example.com/home/default.aspx and https://x.com:8080/private/a",
    "s3://bucket/key r2://facts/objects/edgar/0000320187",
    "Monthly Active Users/Subscribers grew; EV/EBITDA 12.0x; Q3: 10:30 ET",
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


# --- the corpus -----------------------------------------------------------------------------------

def test_no_committed_page_mirror_or_fixture_carries_an_absolute_local_path() -> None:
    """THE GUARD. On main c4c9f432 it listed 118 hits in 59 files — every one a price-store stamp;
    on the cleaned tree it lists none. The count is printed beside the full list, never a cut."""
    n, hits = scan()
    pages = {p.relative_to(ROOT) for p in (ROOT / "data" / "dossiers").glob("*/dossier.json")}
    scanned = {f.relative_to(ROOT) for f in _tracked()}
    assert pages and pages <= scanned, (
        f"the scan ({n} tracked files under {SCANNED}) misses committed pages: "
        f"{sorted(map(str, pages - scanned))}")
    assert not hits, (
        f"{len(hits)} absolute local path(s) in the committed corpus ({n} files scanned); this "
        "repository is public. A price-store stamp is fixed by scripts/rewrite_store_stamps.py; "
        "anything else is a new leak, removed at its writer:\n" + "\n".join(hits))


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
        line = f"- **Price store:** {_price_store_line(PriceStoreStamp.model_validate(raw))}"
        assert line in (p.parent / "dossier.md").read_text(), (p.parent.name, line)
    assert stamped, "no committed page carries a price-store stamp — the test reads nothing"


if __name__ == "__main__":
    scanned, found = scan()
    print(f"{len(found)} absolute local path(s) in {scanned} tracked files under "
          f"{', '.join(SCANNED)}")
    print("\n".join(found))
    sys.exit(1 if found else 0)
