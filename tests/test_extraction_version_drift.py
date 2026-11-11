"""QUEUE ITEM 26b — THE DECLARED EXTRACTION VERSION MUST MOVE WHEN EXTRACTION DOES (audit A-D14).

THE STAMP STOOD STILL FOR 45 COMMITS. `EXTRACTION_VERSION` names the extractor that built a page,
and it is declared by hand (`vinci/dossier/extraction_version.py`, 26a). From 2026-10-11 to 10-29
every commit to vinci/dossier, vinci/edgar and vinci/ciq appended no row — at least six of them
changed output — so the 155 layer refreshes dated 10-27 or later stamped `2026-10-09.3`, naming
code that did not make them. Nothing noticed, because nothing could: a version is a declaration.

THIS TEST NOTICES. Each module that can change what a dossier carries has ONE PIN FILE,
``tests/extraction_pins/<module path>.pin``, holding a hash of its code and WHY it was last pinned:
the extraction vintage that declared the change, or ``refactor`` (no output change, said in the
PR). The rule is STRICT — every watched module's hash equals its pin, always — and every pin names
a declared vintage or ``refactor``. So a PR that moves a watched module re-pins it, and the pin it
writes says, in the diff, which entry it added or that it changed no output.

STRICT, AND STILL MERGEABLE IN ANY ORDER (2026-11-11, fix request 2). The pins were one block here
with the table's digest and its last row beside them, and every re-pin rewrote those two lines, so
two PRs that each added a vintage always conflicted here, and a strict rule could not hold: a merge
leaves the digest matching neither branch. That forced the old rule — any move passes once the
table holds a row the pins have not seen — and its accepted risk: in that window an unrelated
move passed with only a WARNING, which every gate's ``-p no:warnings`` dropped (fix request 2,
RH-D1: the check could not fail and its one signal reached no log). With one file per module and
no shared line, two PRs that move DIFFERENT modules touch different files and merge clean, each
pin matching the merged tree; two that move the SAME module edit the same file, git refuses the
merge, and the re-sync re-pins it — correctly, because the merged module's hash is new. There is
no stale window left to warn about.

    python -m tests.test_extraction_version_drift                        # print every hash
    python -m tests.test_extraction_version_drift --repin --entry <id>   # output changed
    python -m tests.test_extraction_version_drift --repin --refactor     # no output change

ONE MECHANICAL STEP, NEVER A HAND-MERGE. ``--repin`` rewrites only the pins whose hash moved (a
module that joined is pinned; one that left loses its file) and names the entry, or ``refactor``,
in each. Exclude a module by adding it to `NOT_EXTRACTION` with the reason. On a conflict in a pin
file, take either side and re-pin in the merge commit.

WHAT IS HASHED: the module's TOKENS, with comments, blank lines and docstrings dropped — the prose
this repo writes beside its code can change freely; a changed constant, condition or call cannot.

WHAT IT DOES NOT CATCH, stated rather than implied: a pin naming an OLD vintage for a new hash. The
tree cannot tell a pin written today from one written last month, so whether the named entry is
the PR's own is read in the PR's diff (the old rule had the same limit: its refactor re-pin moved
no line a reviewer could not also see).

THE DECLARED SET, NOT A COMPUTED CLOSURE (26b's spec, corrected 2026-07-28: the import closure from
`assemble` is ~58 modules and a guard that always fires is switched off). Every module under
vinci/dossier and vinci/edgar is classified — watched (it has a pin), or `NOT_EXTRACTION` with the
reason — and a module joining either package unclassified has no pin, which is a MOVE, so the set
cannot quietly stop covering a new extractor (`--repin` then pins it as watched). Three modules
outside them build page fields and are watched too: vinci/verbatim.py (which quoted values a page
keeps), vinci/finra.py (short interest) and vinci/eod/features.py (the price box's 52-week range,
whose window C4 moved — review of #884). The rest of vinci/eod is market data, not extraction.
vinci/ciq, which built no page field, was removed on 2026-11-10 (fix request 2: A-D13, A-D16,
RBC-D7): its last caller, graph Test 0, left in #905, and vinci/graph/extract.py now holds the
SUPPLY_CHAIN_TYPES taxonomy it took from it.
"""
from __future__ import annotations

import ast
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path

import pytest

from vinci.dossier.extraction_version import EXTRACTION_VERSIONS

ROOT = Path(__file__).resolve().parents[1]

#: One file per watched module: ``<module path>.pin`` = ``<code hash> <why>``. The environment
#: override exists for ONE test, which runs this file under the gate's own flags against a copy.
PINS = Path(os.environ.get("EXTRACTION_PINS_DIR") or ROOT / "tests" / "extraction_pins")

#: A pin's WHY when the module moved without changing what a page carries.
REFACTOR = "refactor"

#: Modules in the classified packages that cannot change what a dossier carries, each with why.
NOT_EXTRACTION: dict[str, str] = {
    "vinci/dossier/__init__.py": "the package's docstring",
    "vinci/dossier/confirmation.py": "the vote rule's ten-draw confirmation at log-verdict "
                                     "(C(iv)): seals a ledger row, never writes a page",
    "vinci/dossier/driver_evidence.py": "writes a page's transcript evidence to the operator's "
                                        "private spool, never a page field",
    "vinci/dossier/extraction_version.py": "the version table and the stamp it derives — a bump is "
                                           "a file in vinci/dossier/extraction_versions/",
    "vinci/dossier/prespend.py": "the $0 pre-spend check: builds into a deleted folder and "
                                 "compares, never writes a page",
    "vinci/dossier/propose.py": "writes scenario records from a committed page, never a page",
    "vinci/dossier/render.py": "renders a page's markdown from its JSON; re-rendered, never "
                               "re-extracted",
    "vinci/dossier/run_metrics.py": "the cost-and-outcome series beside a build, not the page",
    "vinci/dossier/tagger.py": "propose-only: reads committed pages, writes nothing",
    "vinci/edgar/__init__.py": "re-exports the client",
}

#: Watched beyond the two classified packages.
#: `vinci/provenance.py` (2026-11-05, review round 2): its hashing and redaction set values in every
#: page's `inputs` block.
EXTRA_WATCHED = ("vinci/verbatim.py", "vinci/finra.py", "vinci/eod/features.py",
                 "vinci/provenance.py")
CLASSIFIED_PACKAGES = ("vinci/dossier", "vinci/edgar")


def _docstring_starts(tree: ast.Module) -> set[tuple[int, int]]:
    """(line, column) of every module, class and function docstring."""
    out: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = node.body[0] if node.body else None
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                out.add((first.value.lineno, first.value.col_offset))
    return out


def code_hash(source: str) -> str:
    """sha256[:12] of a module's code tokens — comments, blank lines and docstrings dropped. Token
    NAMES, not their numbers, so the hash does not move with a tokenizer renumbering."""
    docs = _docstring_starts(ast.parse(source))
    kept: list[str] = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type in (tokenize.COMMENT, tokenize.NL):
            continue
        if tok.type == tokenize.STRING and tok.start in docs:
            continue
        kept.append(f"{tokenize.tok_name[tok.type]} {tok.string}")
    return hashlib.sha256("\n".join(kept).encode()).hexdigest()[:12]


def current_hashes() -> dict[str, str]:
    """Every watched module's hash as the tree stands — the set the pins must equal."""
    paths = [p.relative_to(ROOT).as_posix() for pkg in CLASSIFIED_PACKAGES
             for p in sorted((ROOT / pkg).glob("*.py"))]
    watched = [p for p in paths if p not in NOT_EXTRACTION] + list(EXTRA_WATCHED)
    return {p: code_hash((ROOT / p).read_text()) for p in sorted(watched)}


def read_pins(pins: Path = PINS) -> dict[str, tuple[str, str]]:
    """Every pin file as ``{module: (hash, why)}``. A pin that is not two fields raises."""
    out: dict[str, tuple[str, str]] = {}
    for path in sorted(pins.rglob("*.pin")):
        fields = path.read_text().split()
        if len(fields) != 2:
            raise ValueError(f"{path}: a pin is '<hash> <why>', found {fields}")
        out[path.relative_to(pins).as_posix().removesuffix(".pin")] = (fields[0], fields[1])
    return out


def refused_moves(pins: dict[str, str], now: dict[str, str]) -> dict[str, str | None]:
    """The watched modules whose code is not what their pin says — changed, joined (no pin) or gone
    (None). STRICT: a version entry landing elsewhere excuses nothing (fix request 2, RH-D1)."""
    moved: dict[str, str | None] = {p: h for p, h in now.items() if pins.get(p) != h}
    moved.update({p: None for p in pins if p not in now})
    return moved


def unexplained(pins: dict[str, tuple[str, str]], declared: set[str]) -> dict[str, str]:
    """Pins whose WHY is neither a declared vintage nor ``refactor``."""
    return {m: why for m, (_, why) in pins.items() if why != REFACTOR and why not in declared}


def repin(pins: Path, now: dict[str, str], why: str) -> list[str]:
    """Rewrite only the pins that differ from ``now`` (naming ``why``), delete the pins of modules
    no longer watched, and return every module touched — the whole of ``--repin``."""
    have = read_pins(pins)
    touched = []
    for module, h in now.items():
        if have.get(module, ("", ""))[0] != h:
            path = pins / f"{module}.pin"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{h} {why}\n")
            touched.append(module)
    for module in sorted(set(have) - set(now)):
        (pins / f"{module}.pin").unlink()
        touched.append(module)
    return touched


_STEPS = (
    "To clear it: (1) take main first — `git merge origin/main`; a conflict in a pin file means "
    "both sides moved that module, so take either side; (2) if extraction OUTPUT changed and this "
    "PR has no vintage yet, add one — `python -m vinci.dossier.extraction_version new <slug> "
    "--names \"...\"`, which writes one file in vinci/dossier/extraction_versions/; (3) run "
    "`python -m tests.test_extraction_version_drift --repin --entry <its id>`, or `--repin "
    "--refactor` when no output changed (say so in the PR). It re-pins only the modules whose "
    "hash moved — a module both sides touched has a merged hash matching neither side, so never "
    "hand-pick one. A module that cannot change a dossier goes in NOT_EXTRACTION with the reason.")


def test_a_watched_module_never_moves_without_its_pin() -> None:
    """THE 26b INVARIANT, STRICT. A watched module whose code is not its pin's — changed, joined
    vinci/dossier or vinci/edgar unclassified, or left it — reds, whatever the table holds."""
    gone = sorted(p for p in NOT_EXTRACTION if not (ROOT / p).exists())
    moved = refused_moves({m: h for m, (h, _) in read_pins().items()}, current_hashes())
    moved.update(dict.fromkeys(gone))
    assert not moved, f"{sorted(moved)} moved since their pins were written. {_STEPS}"


def test_every_pin_says_why_it_was_written() -> None:
    """A pin names the vintage that declared its module's change, or `refactor` — never a typo or
    a stamp this code does not declare, so the re-pin in a PR's diff always says which it was."""
    pins = read_pins()
    assert pins, f"no pin under {PINS} — the guard would pass vacuously"
    bad = unexplained(pins, {v for v, _ in EXTRACTION_VERSIONS})
    assert not bad, f"pins naming neither a declared vintage nor {REFACTOR!r}: {bad}"


def test_the_failure_tells_a_merger_each_step(monkeypatch: pytest.MonkeyPatch) -> None:
    """The red a merger meets names every step in order: take main, add a vintage if output
    changed, re-pin naming it — and warns that a module both sides touched matches neither."""
    real = read_pins()
    some = next(iter(real))
    monkeypatch.setattr(sys.modules[__name__], "read_pins",
                        lambda pins=PINS: {**real, some: ("0" * 12, real[some][1])})
    with pytest.raises(AssertionError) as red:
        test_a_watched_module_never_moves_without_its_pin()
    msg = str(red.value)
    steps = [some, "git merge origin/main", "a conflict in a pin file",
             "python -m vinci.dossier.extraction_version new", "--repin --entry",
             "--refactor", "matching neither side"]
    for step in steps:
        assert step in msg, step
    at = [msg.index(s) for s in steps]
    assert at == sorted(at), "the steps are out of order"


def test_a_move_is_refused_even_after_a_version_entry_lands() -> None:
    """RH-D1, on the pure function. The old rule let ANY move pass once the table held a row the
    pins had not seen, and said so only in a warning the gates suppress; now the table is not an
    argument at all — a module whose code is not its pin's is refused, joined and gone included."""
    pins = {"vinci/dossier/a.py": "aaa", "vinci/dossier/b.py": "bbb"}
    moved = {"vinci/dossier/a.py": "AAA", "vinci/dossier/b.py": "bbb", "vinci/dossier/c.py": "ccc"}
    assert refused_moves(pins, moved) == {"vinci/dossier/a.py": "AAA", "vinci/dossier/c.py": "ccc"}
    assert refused_moves(pins, {"vinci/dossier/a.py": "aaa"}) == {"vinci/dossier/b.py": None}
    assert refused_moves(pins, dict(pins)) == {}


def _gate(pins: Path) -> subprocess.CompletedProcess[str]:
    """The strict test, run exactly as gate.yml and bin/commit run pytest, against ``pins``."""
    node = f"{Path(__file__).relative_to(ROOT).as_posix()}::" \
           "test_a_watched_module_never_moves_without_its_pin"
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-m", "not network", "-p", "no:warnings", "--tb=short",
         "-rs", "-p", "no:cacheprovider", node],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
        env={**os.environ, "EXTRACTION_PINS_DIR": str(pins)})


def test_a_stale_pin_fails_under_the_gates_own_flags(tmp_path: Path) -> None:
    """RH-D1, end to end: the stale state the old rule printed only as a warning — a watched module
    whose pin is behind its code — must turn the gate's own command red, ``-p no:warnings`` and
    all. The control is the same command on an unmodified copy of the pins: green."""
    good, stale = tmp_path / "good", tmp_path / "stale"
    good.mkdir()
    repin(good, current_hashes(), REFACTOR)  # current whatever this tree's own pins say
    shutil.copytree(good, stale)
    module = "vinci/dossier/anchor.py"
    (stale / f"{module}.pin").write_text(f"{'0' * 12} {REFACTOR}\n")
    ok, red = _gate(good), _gate(stale)
    assert ok.returncode == 0, ok.stdout[-2000:]
    assert red.returncode == 1, red.stdout[-2000:]
    assert module in red.stdout and "1 failed" in red.stdout, red.stdout[-2000:]


def test_repin_is_one_mechanical_step(tmp_path: Path) -> None:
    """``--repin`` touches only what moved: re-pinning at the tree's own hashes is a no-op; a moved
    module rewrites its one file naming the entry; a module that joined gains a file; one that left
    loses it — and no other file changes, which is what keeps two PRs' re-pins apart."""
    pins = tmp_path / "pins"
    shutil.copytree(PINS, pins)
    now = current_hashes()
    repin(pins, now, REFACTOR)  # current whatever this tree's own pins say (the invariant's job)
    assert repin(pins, now, "never-written") == []
    before = {p: p.read_text() for p in pins.rglob("*.pin")}
    moved, joined = "vinci/dossier/anchor.py", "vinci/dossier/new_reader.py"
    gone = "vinci/finra.py"
    tree = {**{m: h for m, h in now.items() if m != gone}, moved: "f" * 12, joined: "e" * 12}
    assert sorted(repin(pins, tree, "2099-01-01.an-entry")) == sorted([moved, joined, gone])
    after = {p: p.read_text() for p in pins.rglob("*.pin")}
    changed = sorted(p.relative_to(pins).as_posix() for p in set(before) | set(after)
                     if before.get(p) != after.get(p))
    assert changed == sorted(f"{m}.pin" for m in (moved, joined, gone))
    assert (pins / f"{moved}.pin").read_text() == f"{'f' * 12} 2099-01-01.an-entry\n"
    assert not (pins / f"{gone}.pin").exists()


def test_a_pin_naming_no_declared_vintage_is_refused() -> None:
    """Both halves: a declared vintage and `refactor` explain a pin; a typo or a joined stamp
    (a page's, never a change's) does not."""
    declared = {"2026-11-11.guides-as-stated"}
    pins = {"a": ("x", "2026-11-11.guides-as-stated"), "b": ("y", REFACTOR),
            "c": ("z", "2026-11-11.guides-as-stat"), "d": ("w", "2026-11-11.a+2026-11-11.b")}
    assert unexplained(pins, declared) == {"c": "2026-11-11.guides-as-stat",
                                           "d": "2026-11-11.a+2026-11-11.b"}


# --- the hash itself: blind to prose, never to code ----------------------------------------------

_MODULE = '''"""A module docstring."""
LIMIT = 0.25  # a tolerance


def check(x: float) -> bool:
    """Is x in range?"""
    return x <= LIMIT
'''


@pytest.mark.parametrize("prose_only", [
    _MODULE.replace("# a tolerance", "# a wider explanation of the tolerance"),
    _MODULE.replace('"""Is x in range?"""', '"""Is x inside the band?\n\n    More words."""'),
    _MODULE.replace('"""A module docstring."""', '"""Rewritten."""\n\n'),
    _MODULE.replace("    return x <= LIMIT", "\n    return x  \\\n        <=  LIMIT"),
])
def test_prose_and_layout_never_move_the_hash(prose_only: str) -> None:
    assert code_hash(prose_only) == code_hash(_MODULE)


@pytest.mark.parametrize("code_change", [
    _MODULE.replace("LIMIT = 0.25", "LIMIT = 0.30"),
    _MODULE.replace("x <= LIMIT", "x < LIMIT"),
    _MODULE.replace("return x <= LIMIT", 'return x <= LIMIT or str(x) == "nan"'),
])
def test_any_code_change_moves_the_hash(code_change: str) -> None:
    """NEGATIVE PIN for the guard: a changed constant, comparison or expression is never prose."""
    assert code_hash(code_change) != code_hash(_MODULE)


if __name__ == "__main__":
    args = sys.argv[1:]
    declared = {v for v, _ in EXTRACTION_VERSIONS}
    if args[:1] == ["--repin"]:
        if args[1:] == ["--refactor"]:
            why = REFACTOR
        elif len(args) == 3 and args[1] == "--entry" and args[2] in declared:
            why = args[2]
        else:
            sys.exit("usage: --repin --entry <a declared vintage id> | --repin --refactor")
        touched = repin(PINS, current_hashes(), why)
        sys.stdout.write(f"re-pinned {len(touched)} module(s) as {why}: {', '.join(touched)}\n")
    else:
        sys.stdout.write("\n".join(f"{m} {h}" for m, h in current_hashes().items()) + "\n")
