"""QUEUE ITEM 26b — THE DECLARED EXTRACTION VERSION MUST MOVE WHEN EXTRACTION DOES (audit A-D14).

THE STAMP STOOD STILL FOR 45 COMMITS. `EXTRACTION_VERSION` names the extractor that built a page,
and it is declared by hand (`vinci/dossier/extraction_version.py`, 26a). From 2026-10-11 to 10-29
every commit to vinci/dossier, vinci/edgar and vinci/ciq appended no row — at least six of them
changed output — so the 155 layer refreshes dated 10-27 or later stamped `2026-10-09.3`, naming
code that did not make them. Nothing noticed, because nothing could: a version is a declaration.

THIS TEST NOTICES. Each module that can change what a dossier carries is PINNED to a hash of its
code (`WATCHED`), taken at the version `PINNED_AT` names. A PR that moves one reds here until it
says, in this file, what the move was:

  * the output changed → append a row to `EXTRACTION_VERSIONS`, then re-pin under it (set
    `PINNED_AT` to the new version and the moved modules' hashes to the values this test prints);
  * the output did not (a refactor) → re-pin the moved modules' hashes alone, and say why in the PR.

Either way the call is made inside the PR, which is the point: the cost is a red build on a
refactor, and it buys a stamp that cannot drift silently (26b's spec, operator 2026-07-28).

WHAT IS HASHED: the module's TOKENS, with comments, blank lines and docstrings dropped — the prose
this repo writes beside its code can change freely; a changed constant, condition or call cannot.

THE DECLARED SET, NOT A COMPUTED CLOSURE (26b's spec, corrected 2026-07-28: the import closure from
`assemble` is ~58 modules and a guard that always fires is switched off). Every module under
vinci/dossier and vinci/edgar is classified — `WATCHED`, or `NOT_EXTRACTION` with the reason — and
a module joining either package unclassified reds (`test_every_module_is_classified`), so the set
cannot quietly stop covering a new extractor. Two modules outside them build page fields and are
watched too: vinci/verbatim.py (which quoted values a page keeps) and vinci/finra.py (short
interest). Prices (vinci/eod) are market data, not extraction, and vinci/ciq feeds only the
git-ignored graph test.

    python -m tests.test_extraction_version_drift   # print every watched module's current hash
"""
from __future__ import annotations

import ast
import hashlib
import io
import sys
import tokenize
from pathlib import Path

import pytest

from vinci.dossier.extraction_version import EXTRACTION_VERSION, EXTRACTION_VERSIONS

ROOT = Path(__file__).resolve().parents[1]

#: The version the pins below were taken at. A new `EXTRACTION_VERSIONS` row moves it.
PINNED_AT = "2026-10-29.1"

#: Every module that can change what a dossier carries, ONE PER LINE so two PRs re-pinning
#: different modules merge without a conflict. The value is :func:`code_hash` of the module.
WATCHED: dict[str, str] = {
    "vinci/dossier/anchor.py": "31ad4e6be5a2",
    "vinci/dossier/assemble.py": "8aad5818f641",
    "vinci/dossier/band_guards.py": "dceaef85746c",
    "vinci/dossier/capital_allocation.py": "77def45663a9",
    "vinci/dossier/ciq.py": "4208de3f08a1",
    "vinci/dossier/ciq_balance.py": "d5a1ffcff8a7",
    "vinci/dossier/ciq_charting.py": "e25a753aae4f",
    "vinci/dossier/ciq_scale_backfill.py": "c3553ce65b72",
    "vinci/dossier/ciq_sheets.py": "5c1171e4ba13",
    "vinci/dossier/covenant_extract.py": "36044a98ac15",
    "vinci/dossier/dilution.py": "87d81ad77c04",
    "vinci/dossier/driver_extract.py": "332fb2039a9a",
    "vinci/dossier/ebitda_basis.py": "7f9996f712e1",
    "vinci/dossier/ebitda_recon.py": "ecb11157c1e6",
    "vinci/dossier/edgar_fundamentals.py": "c8ecafb0bcb4",
    "vinci/dossier/ev_ebitda_basis.py": "ad13b0e13ca0",
    "vinci/dossier/ev_gap.py": "6a0c9a26afac",
    "vinci/dossier/flags.py": "1ce8a4a057ad",
    "vinci/dossier/freshness.py": "e5852b313d22",
    "vinci/dossier/layer_refresh.py": "4be8899e5872",
    "vinci/dossier/lease_basis.py": "f249b900f0b6",
    "vinci/dossier/manual_store.py": "a3e48c8fbc1b",
    "vinci/dossier/materiality.py": "9a26612228a7",
    "vinci/dossier/mechanical.py": "93fb67627fb2",
    "vinci/dossier/midcycle.py": "dfa24e1bc15a",
    "vinci/dossier/recipe_proposal.py": "f890273f1d1b",
    "vinci/dossier/refresh.py": "0c07bfc551a1",
    "vinci/dossier/requirements.py": "0d49ceadcac7",
    "vinci/dossier/schemas.py": "977cc8e15a10",
    "vinci/dossier/statement_recon.py": "4ecc1ea023b9",
    "vinci/dossier/synthesis.py": "c40f86522872",
    "vinci/dossier/terminal_margin.py": "35398ebe5918",
    "vinci/dossier/valuation_basis.py": "766d2ed17c7a",
    "vinci/dossier/verdict.py": "0b43167d2044",
    "vinci/edgar/client.py": "b09eb3cd3d9d",
    "vinci/edgar/commissioning.py": "dc2004432387",
    "vinci/edgar/concepts.py": "abaa46f51d9f",
    "vinci/edgar/debt_maturities.py": "a72fba167d94",
    "vinci/edgar/filing_sections.py": "e66ac473d51f",
    "vinci/edgar/going_concern.py": "5097f25ade31",
    "vinci/edgar/net_debt.py": "6257a0464909",
    "vinci/edgar/primary_source.py": "b7085cdfbc31",
    "vinci/edgar/release_parse.py": "0f4e3f5e4c90",
    "vinci/edgar/segment_facts.py": "9d3c07301296",
    "vinci/edgar/segments.py": "a25da92ebf20",
    "vinci/edgar/submissions.py": "6644355e5c3f",
    "vinci/finra.py": "5787c9793b1b",
    "vinci/verbatim.py": "b7a2346d323b",
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


def test_every_module_is_classified() -> None:
    """A module joining vinci/dossier or vinci/edgar must be pinned or excluded with a reason —
    never silently outside the watched set. And no entry names a module that no longer exists."""
    now = current_hashes()
    unpinned = sorted(set(now) - set(WATCHED))
    assert not unpinned, (
        f"{unpinned} can change what a dossier carries and are not pinned — add them to WATCHED "
        f"(or to NOT_EXTRACTION with the reason they cannot):\n{_pin_lines(now)}")
    gone = sorted(set(WATCHED) - set(now)) + sorted(
        p for p in NOT_EXTRACTION if not (ROOT / p).exists())
    assert not gone, f"{gone} no longer exist — remove them from this file"


def test_a_watched_module_never_moves_while_the_version_stands_still() -> None:
    """THE 26b INVARIANT. A watched module whose code moved since its pin reds here: say whether
    output changed (append a version row, re-pin under it) or not (re-pin alone)."""
    now = current_hashes()
    moved = {p: h for p, h in now.items() if WATCHED.get(p) not in (None, h)}
    assert not moved, (
        f"{len(moved)} watched module(s) changed since they were pinned at {PINNED_AT}: "
        f"{sorted(moved)}. If extraction OUTPUT changed, append a row to EXTRACTION_VERSIONS "
        "(vinci/dossier/extraction_version.py) and set PINNED_AT to it; if it did not, say why "
        "in the PR. Either way, re-pin:\n" + _pin_lines(moved))


def test_the_pins_name_the_current_version() -> None:
    """A row appended without re-pinning reds: the pins must say which version they were taken
    at, or a later move under the new version would be read against the old one."""
    assert PINNED_AT in {v for v, _ in EXTRACTION_VERSIONS}, PINNED_AT
    assert PINNED_AT == EXTRACTION_VERSION, (
        f"EXTRACTION_VERSION is {EXTRACTION_VERSION} but the pins were taken at {PINNED_AT} — "
        "set PINNED_AT to the new version and re-pin the modules this PR moved")


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
    sys.stdout.write(_pin_lines(current_hashes()) + "\n")
