"""QUEUE ITEM 26b — THE DECLARED EXTRACTION VERSION MUST MOVE WHEN EXTRACTION DOES (audit A-D14).

THE STAMP STOOD STILL FOR 45 COMMITS. `EXTRACTION_VERSION` names the extractor that built a page,
and it is declared by hand (`vinci/dossier/extraction_version.py`, 26a). From 2026-10-11 to 10-29
every commit to vinci/dossier, vinci/edgar and vinci/ciq appended no row — at least six of them
changed output — so the 155 layer refreshes dated 10-27 or later stamped `2026-10-09.3`, naming
code that did not make them. Nothing noticed, because nothing could: a version is a declaration.

THIS TEST NOTICES. Each module that can change what a dossier carries is PINNED to a hash of its
code (`WATCHED`), taken when `EXTRACTION_VERSIONS` held the rows `PINNED_TABLE` digests (`PINNED_AT`
names the last of them, for a reader). A module that moved since its pin — or joined or left the
watched set — is refused WHILE THE TABLE HOLDS NO ROW IT DID NOT HOLD THEN: the code moved and the
declared version did not. Once any row has been added, wherever it sits, the moves are accepted.

THAT RULE IS WHAT LETS PARALLEL PRS MERGE IN ANY ORDER. A sibling PR that changes a watched module
and adds its own row never reds main or a branch merging main — before or after this file last
re-pinned, its row last or (merged first) before another batch's — because the moves arrive with a
row the pins have not seen.

ITS COST IS AN ACCEPTED RISK, AND THE PROCEDURE BELOW IS PART OF THE RULE (coordinator review of
#861, 2026-10-29). Once the table holds a row the pins do not know, any further move of a watched
module passes until the next re-pin: after two batches each add a row, the pins reflect neither
tree, and an unrelated refactor merged in that window goes unseen. The strict alternative — a move
reds unless the pins are current — is not available, because it reds main whenever a batch merges
on a CI run that predates another batch's merge (`gate` is required but not strict). So:

  * A PR THAT ADDS A VERSION ROW RUNS `--repin` IN ITS FINAL COMMIT, and again in the merge of
    main that lands it, so main lands tight.
  * While the pins are stale, `test_stale_pins_are_said` warns, naming the rows the pins do not
    know — the window is printed in every CI log, never silent.
  * Falsifier: a watched-module change merged with no row while the pins were stale. It shows as a
    re-pin moving a module that no row since the last re-pin names.

    python -m tests.test_extraction_version_drift --repin   # recompute WATCHED, set PINNED_AT

ONE MECHANICAL STEP, NEVER A HAND-MERGE. It rewrites `WATCHED` to the tree's hashes (a new module
joins as watched; exclude one by adding it to `NOT_EXTRACTION` with the reason), `PINNED_TABLE` to
the table's digest and `PINNED_AT` to its last row. On a merge conflict in this file, take either
side and run it in the merge commit. A refactor that moves a watched module with no output change
re-pins too, and says so in its PR.

MERGING THE VERSION TABLE ITSELF: every row of `EXTRACTION_VERSIONS` (and of its web twin in
`frontend/views/shared/dossier.js`) is its own `(` … `),` block; a line-wise union of two branches'
table ends fuses two rows into one element. Keep each block whole, in merge order.

WHAT IS HASHED: the module's TOKENS, with comments, blank lines and docstrings dropped — the prose
this repo writes beside its code can change freely; a changed constant, condition or call cannot.

THE DECLARED SET, NOT A COMPUTED CLOSURE (26b's spec, corrected 2026-07-28: the import closure from
`assemble` is ~58 modules and a guard that always fires is switched off). Every module under
vinci/dossier and vinci/edgar is classified — `WATCHED`, or `NOT_EXTRACTION` with the reason — and a
module joining either package unclassified is a MOVE under the rule above, so the set cannot quietly
stop covering a new extractor (`--repin` then pins it as watched). Two modules outside them build
page fields and are watched too: vinci/verbatim.py (which quoted values a page keeps) and
vinci/finra.py (short interest). Prices (vinci/eod) are market data, not extraction, and vinci/ciq
feeds only the git-ignored graph test.

    python -m tests.test_extraction_version_drift            # print every watched module's hash
    python -m tests.test_extraction_version_drift --repin    # re-pin this file in place
"""
from __future__ import annotations

import ast
import hashlib
import io
import re
import sys
import tokenize
import warnings
from pathlib import Path

import pytest

from vinci.dossier.extraction_version import EXTRACTION_VERSION, EXTRACTION_VERSIONS

ROOT = Path(__file__).resolve().parents[1]

#: The table the pins below were taken against — `--repin` sets both: the digest of every row id
#: (:func:`table_digest`, what the rule reads) and, for a reader, the last row then.
PINNED_TABLE = "95ad5268037d"
PINNED_AT = "2026-10-30.latest-cell"

#: Every module that can change what a dossier carries, ONE PER LINE so two PRs re-pinning
#: different modules merge without a conflict. The value is :func:`code_hash` of the module.
WATCHED: dict[str, str] = {
    "vinci/dossier/anchor.py": "a538abb9a405",
    "vinci/dossier/assemble.py": "6b9455e98818",
    "vinci/dossier/band_guards.py": "dceaef85746c",
    "vinci/dossier/capital_allocation.py": "77def45663a9",
    "vinci/dossier/ciq.py": "7cbdeee7b55f",
    "vinci/dossier/ciq_balance.py": "a1a1c371f356",
    "vinci/dossier/ciq_charting.py": "e25a753aae4f",
    "vinci/dossier/ciq_scale_backfill.py": "c3553ce65b72",
    "vinci/dossier/ciq_sheets.py": "8ac16dfe8179",
    "vinci/dossier/covenant_extract.py": "36044a98ac15",
    "vinci/dossier/dilution.py": "87d81ad77c04",
    "vinci/dossier/driver_extract.py": "28d08956a8f2",
    "vinci/dossier/ebitda_basis.py": "7f9996f712e1",
    "vinci/dossier/ebitda_recon.py": "a2d815700dc4",
    "vinci/dossier/edgar_fundamentals.py": "c8ecafb0bcb4",
    "vinci/dossier/ev_ebitda_basis.py": "ad13b0e13ca0",
    "vinci/dossier/ev_gap.py": "6a0c9a26afac",
    "vinci/dossier/flags.py": "0fde0b63ffba",
    "vinci/dossier/freshness.py": "e5852b313d22",
    "vinci/dossier/layer_refresh.py": "4be8899e5872",
    "vinci/dossier/lease_basis.py": "a93d880597ba",
    "vinci/dossier/ltm_quarters.py": "f6a3904e1011",
    "vinci/dossier/manual_store.py": "a3e48c8fbc1b",
    "vinci/dossier/materiality.py": "274e1447b37f",
    "vinci/dossier/mechanical.py": "6d17333aaeb7",
    "vinci/dossier/midcycle.py": "a67120583735",
    "vinci/dossier/recipe_proposal.py": "f890273f1d1b",
    "vinci/dossier/refresh.py": "0c07bfc551a1",
    "vinci/dossier/requirements.py": "0d49ceadcac7",
    "vinci/dossier/schemas.py": "ba1235fc60f1",
    "vinci/dossier/statement_recon.py": "4ecc1ea023b9",
    "vinci/dossier/synthesis.py": "9c732c86d48a",
    "vinci/dossier/terminal_margin.py": "35398ebe5918",
    "vinci/dossier/valuation_basis.py": "766d2ed17c7a",
    "vinci/dossier/verdict.py": "0b43167d2044",
    "vinci/edgar/client.py": "b09eb3cd3d9d",
    "vinci/edgar/commissioning.py": "dc2004432387",
    "vinci/edgar/concepts.py": "abaa46f51d9f",
    "vinci/edgar/debt_maturities.py": "a72fba167d94",
    "vinci/edgar/filing_sections.py": "568c36df04a2",
    "vinci/edgar/going_concern.py": "5097f25ade31",
    "vinci/edgar/net_debt.py": "6257a0464909",
    "vinci/edgar/primary_source.py": "80351248cc8a",
    "vinci/edgar/release_parse.py": "1d886c4d5a7b",
    "vinci/edgar/segment_facts.py": "9d3c07301296",
    "vinci/edgar/segments.py": "a25da92ebf20",
    "vinci/edgar/submissions.py": "6644355e5c3f",
    "vinci/finra.py": "5787c9793b1b",
    "vinci/verbatim.py": "cb75bef0a20e",
}

#: Modules in the classified packages that cannot change what a dossier carries, each with why.
NOT_EXTRACTION: dict[str, str] = {
    "vinci/dossier/__init__.py": "the package's docstring",
    "vinci/dossier/extraction_version.py": "the version table itself — editing it IS the bump",
    "vinci/dossier/propose.py": "writes scenario records from a committed page, never a page",
    "vinci/dossier/render.py": "renders a page's markdown from its JSON; re-rendered, never "
                               "re-extracted",
    "vinci/dossier/run_metrics.py": "the cost-and-outcome series beside a build, not the page",
    "vinci/dossier/tagger.py": "propose-only: reads committed pages, writes nothing",
    "vinci/edgar/__init__.py": "re-exports the client",
}

#: Watched beyond the two classified packages.
EXTRA_WATCHED = ("vinci/verbatim.py", "vinci/finra.py")
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
    """Every watched module's hash as the tree stands — the set `WATCHED` must equal."""
    paths = [p.relative_to(ROOT).as_posix() for pkg in CLASSIFIED_PACKAGES
             for p in sorted((ROOT / pkg).glob("*.py"))]
    watched = [p for p in paths if p not in NOT_EXTRACTION] + list(EXTRA_WATCHED)
    return {p: code_hash((ROOT / p).read_text()) for p in sorted(watched)}


def _pin_lines(hashes: dict[str, str]) -> str:
    return "\n".join(f'    "{p}": "{h}",' for p, h in hashes.items())


def table_digest(versions: tuple[tuple[str, str], ...] | list[tuple[str, str]]) -> str:
    """sha256[:12] of the table's row ids, sorted — the same whatever order a merge put them in."""
    return hashlib.sha256("\n".join(sorted(v for v, _ in versions)).encode()).hexdigest()[:12]


def refused_moves(pins: dict[str, str], pinned_table: str, now: dict[str, str],
                  current_table: str) -> dict[str, str | None]:
    """The watched modules that moved since their pins — changed, joined or gone (None) — IF the
    version table holds no row it did not hold then; empty once it does, because then the
    declared version moved too."""
    if current_table != pinned_table:
        return {}
    moved: dict[str, str | None] = {p: h for p, h in now.items() if pins.get(p) != h}
    moved.update({p: None for p in pins if p not in now})
    return moved


def test_a_watched_module_never_moves_while_the_version_stands_still() -> None:
    """THE 26b INVARIANT. A watched module that moved — or joined vinci/dossier or vinci/edgar
    unclassified, or left it — while the last row is still the one the pins were taken at."""
    gone = sorted(p for p in NOT_EXTRACTION if not (ROOT / p).exists())
    now_table = table_digest(EXTRACTION_VERSIONS)
    moved = refused_moves(WATCHED, PINNED_TABLE, current_hashes(), now_table)
    moved.update({p: None for p in gone if now_table == PINNED_TABLE})
    assert not moved, (
        f"{sorted(moved)} moved since the pins were taken (last row then {PINNED_AT}), and "
        "the version table has gained no row since. To clear it, in order: (1) take main "
        "first — `git merge origin/main` — keeping every EXTRACTION_VERSIONS row its own "
        "`(` … `),` block, in merge order (a line-wise union fuses two rows); (2) run "
        "`python -m tests.test_extraction_version_drift` to print the hashes as they now "
        "stand — a module two branches both touched has a merged hash that matches neither "
        "pin, so read the printed value, never pick a side; (3) if extraction OUTPUT changed, "
        "append your row to vinci/dossier/extraction_version.py and the same row to "
        "frontend/views/shared/dossier.js; (4) run "
        "`python -m tests.test_extraction_version_drift --repin`, which re-pins every moved "
        "line and the table digest. A refactor alone skips (3) and says so in its PR. A PR "
        "that adds a version row runs (4) in its final commit, and again in the merge of "
        "main that lands it. A module that cannot change a dossier goes in NOT_EXTRACTION "
        "with the reason.")


def test_stale_pins_are_said() -> None:
    """The accepted risk's window, printed: while the version table holds rows the pins do not
    know, every CI log carries a warning naming them — a stale pin is never silent."""
    if table_digest(EXTRACTION_VERSIONS) != PINNED_TABLE:
        warnings.warn(
            "extraction-version drift pins are STALE: the table has rows they do not know "
            f"(pinned at {PINNED_AT}; last row now {EXTRACTION_VERSION}). A moved watched "
            "module passes unseen until `python -m tests.test_extraction_version_drift "
            "--repin` runs — the PR that added the row owes it.", UserWarning, stacklevel=1)


def test_the_failure_tells_a_merger_each_step(monkeypatch: pytest.MonkeyPatch) -> None:
    """The red a merger meets names every step in order: take main keeping each version row whole,
    print the hashes, append a row if output changed, re-pin — and warns that a module two branches
    both touched has a merged hash matching neither pin (PR #861 round 1)."""
    monkeypatch.setitem(WATCHED, "vinci/dossier/ciq.py", "0" * 12)
    with pytest.raises(AssertionError) as red:
        test_a_watched_module_never_moves_while_the_version_stands_still()
    msg = str(red.value)
    steps = ["git merge origin/main", "`(` … `),` block",
             "python -m tests.test_extraction_version_drift`", "matches neither pin",
             "append your row", "frontend/views/shared/dossier.js", "--repin"]
    for step in steps:
        assert step in msg, step
    at = [msg.index(s) for s in steps]
    assert at == sorted(at), "the steps are out of order"


def test_the_stale_warning_fires_only_when_the_pins_are_stale(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Both halves: pins taken against another table warn; pins taken against this one do not."""
    mod = sys.modules[__name__]
    monkeypatch.setattr(mod, "PINNED_TABLE", "0" * 12)
    with pytest.warns(UserWarning, match="drift pins are STALE"):
        test_stale_pins_are_said()
    monkeypatch.setattr(mod, "PINNED_TABLE", table_digest(EXTRACTION_VERSIONS))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        test_stale_pins_are_said()


def test_the_pins_name_a_declared_version() -> None:
    """`PINNED_AT` names a real row — a re-pin can only take the pins at a version that exists."""
    assert PINNED_AT in {v for v, _ in EXTRACTION_VERSIONS}, PINNED_AT


def test_the_table_digest_ignores_merge_order() -> None:
    """Two batches' rows merged in either order are one table; a new row is a new table."""
    a, b, c = ("v1", "x"), ("v2.A", "y"), ("v2.B", "z")
    assert table_digest([a, b, c]) == table_digest([a, c, b])
    assert table_digest([a, b]) != table_digest([a, b, c])


def test_a_move_is_refused_only_while_the_version_stands_still() -> None:
    """Both halves of the rule, on the pure function: the same move is refused against the pinned
    table and accepted once the table has a new row (a sibling PR merging with its own row, in
    either order), and a module that joins or leaves the set is a move."""
    pins = {"vinci/dossier/a.py": "aaa", "vinci/dossier/b.py": "bbb"}
    moved = {"vinci/dossier/a.py": "AAA", "vinci/dossier/b.py": "bbb", "vinci/dossier/c.py": "ccc"}
    assert refused_moves(pins, "v1", moved, "v1") == {"vinci/dossier/a.py": "AAA",
                                                      "vinci/dossier/c.py": "ccc"}
    assert refused_moves(pins, "v1", moved, "v2") == {}
    assert refused_moves(pins, "v1", {"vinci/dossier/a.py": "aaa"}, "v1") == {
        "vinci/dossier/b.py": None}
    assert refused_moves(pins, "v1", dict(pins), "v1") == {}


def repinned(source: str, hashes: dict[str, str], table: str, version: str) -> str:
    """This file's source with `WATCHED` set to ``hashes``, `PINNED_TABLE` to ``table`` and
    `PINNED_AT` to ``version``."""
    out = re.sub(r"(?ms)^WATCHED: dict\[str, str\] = \{\n.*?^\}",
                 "WATCHED: dict[str, str] = {\n" + _pin_lines(hashes).replace("\\", "\\\\")
                 + "\n}", source, count=1)
    out = re.sub(r'(?m)^PINNED_TABLE = "[^"]*"', f'PINNED_TABLE = "{table}"', out, count=1)
    return re.sub(r'(?m)^PINNED_AT = "[^"]*"', f'PINNED_AT = "{version}"', out, count=1)


def test_repin_is_one_mechanical_step() -> None:
    """`--repin` rewrites exactly the pinned values: re-pinning this file at its own pins is a
    no-op, and a re-pin at other values changes only those lines."""
    src = Path(__file__).read_text()
    assert repinned(src, WATCHED, PINNED_TABLE, PINNED_AT) == src
    other = repinned(src, {"vinci/dossier/x.py": "0" * 12}, "f" * 12, "2099-01-01.X")
    changed = [ln for ln in other.splitlines() if ln not in src.splitlines()]
    assert sorted(changed) == ['    "vinci/dossier/x.py": "000000000000",',
                               'PINNED_AT = "2099-01-01.X"', f'PINNED_TABLE = "{"f" * 12}"']


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
    if sys.argv[1:] == ["--repin"]:
        me = Path(__file__)
        me.write_text(repinned(me.read_text(), current_hashes(), table_digest(EXTRACTION_VERSIONS),
                               EXTRACTION_VERSION))
        sys.stdout.write(f"re-pinned {len(current_hashes())} modules at {EXTRACTION_VERSION}\n")
    else:
        sys.stdout.write(_pin_lines(current_hashes()) + "\n")
