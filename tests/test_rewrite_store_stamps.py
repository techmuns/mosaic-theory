"""`scripts/rewrite_store_stamps.py` — the deterministic two-span rewrite that cleaned the committed
price-store stamps (2026-11-05), pinned because the next PRs to land an old-writer page run it.

(+) it reduces both absolute paths to their checkout folders and changes no other byte of the page;
(−) it refuses a span it would have to guess at, a path it cannot reduce, and touches a page whose
stamp is already clean not at all.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "rewrite_store_stamps", ROOT / "scripts" / "rewrite_store_stamps.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _page(**extra: Any) -> str:
    """A page in the writer's own layout (pydantic `indent=2`), stamped the old way."""
    return json.dumps({
        "ticker": "T",
        "price_store": {
            "declared_path": "/Users/x/Documents/GitHub/link-worktree/data/vinci.db",
            "resolved_path": "/private/tmp/claude-501/s/scratchpad/real-worktree/data/vinci.db",
            "frontier": "2026-08-04"},
        **extra}, indent=2) + "\n"


def test_both_paths_become_their_checkout_folders_and_nothing_else_moves() -> None:
    old = _page(note="kept, with a URL https://www.sec.gov/x")
    new, moved = _script().rewrite(old, name="T")
    assert moved == {"declared_path": "link-worktree", "resolved_path": "real-worktree"}
    changed = [(a, b) for a, b in zip(old.splitlines(), new.splitlines(), strict=True) if a != b]
    assert [b.strip() for _, b in changed] == ['"declared_path": "link-worktree",',
                                              '"resolved_path": "real-worktree",']


def test_a_second_run_and_a_page_with_no_stamp_are_left_alone() -> None:
    new, _ = _script().rewrite(_page(), name="T")
    assert _script().rewrite(new, name="T") == (new, {})
    bare = json.dumps({"ticker": "T"}, indent=2)
    assert _script().rewrite(bare, name="T") == (bare, {})


def test_a_span_that_occurs_twice_is_refused_rather_than_guessed() -> None:
    """A copy of the stamp elsewhere in the page (a reason quoting it, a manifest) would make the
    first-match replace pick one of two; the rewrite names the file and writes nothing."""
    path = "/Users/x/Documents/GitHub/link-worktree/data/vinci.db"
    with pytest.raises(ValueError, match="occurs 2 times"):
        _script().rewrite(_page(inputs={"declared_path": path}), name="T")


@pytest.mark.parametrize("value", ["data/vinci.db", "C:\\Users\\x\\w\\data\\vinci.db"])
def test_a_path_it_cannot_reduce_is_refused(value: str) -> None:
    doc = json.loads(_page())
    doc["price_store"]["declared_path"] = value
    with pytest.raises(ValueError, match="not a POSIX absolute"):
        _script().rewrite(json.dumps(doc, indent=2), name="T")


def test_a_span_it_cannot_find_is_refused_as_missing_not_as_a_guess() -> None:
    """Round 2: a non-ASCII path is written raw by the page's writer and escaped by `json.dumps`,
    so its span occurs 0 times — a case of its own, and not a choice between two."""
    doc = json.loads(_page())
    doc["price_store"]["declared_path"] = "/Users/zoë/w/link-worktree/data/vinci.db"
    with pytest.raises(ValueError, match="not in the text as `json.dumps` writes it"):
        _script().rewrite(json.dumps(doc, indent=2, ensure_ascii=False), name="T")


def test_a_stamp_missing_a_field_is_refused_naming_the_file() -> None:
    doc = json.loads(_page())
    del doc["price_store"]["resolved_path"]
    with pytest.raises(ValueError, match=r"^T\.json: price_store has no resolved_path"):
        _script().rewrite(json.dumps(doc, indent=2), name="T.json")


def test_the_rewrite_reduces_by_the_writers_own_function() -> None:
    """ONE FUNCTION (round 2): a stamp `store_checkout` refuses — a store not at
    `<checkout>/data/vinci.db`, whose grandparent folder here is a username — is refused by the
    rewrite too, naming the file. A script reducing by its own `parent.parent.name` would stamp
    `x`."""
    doc = json.loads(_page())
    doc["price_store"]["resolved_path"] = "/Users/x/stores/vinci.db"
    with pytest.raises(ValueError, match=r"^T: price_store\.resolved_path: .*not at <checkout>"):
        _script().rewrite(json.dumps(doc, indent=2), name="T")


def test_the_one_span_it_finds_must_be_the_stamps_own() -> None:
    """THE PARSE PROOF (round 2). A page whose stamp is written with JSON's escaped slashes
    (`\\/`, which parse to the same path) and which quotes the same path plainly elsewhere has
    exactly ONE plain span — the wrong one. The count check passes it; only the proof that the
    result parses to the input with the stamp alone changed refuses it."""
    path = "/Users/x/Documents/GitHub/link-worktree/data/vinci.db"
    text = _page(inputs={"declared_path": path}).replace(
        f'"declared_path": "{path}",', '"declared_path": "' + path.replace("/", "\\/") + '",', 1)
    assert json.loads(text)["price_store"]["declared_path"] == path
    with pytest.raises(ValueError, match="changed more than price_store's two paths"):
        _script().rewrite(text, name="T")


def test_main_writes_a_page_it_rewrote_and_leaves_a_clean_one_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    import os

    old, clean = tmp_path / "old.json", tmp_path / "clean.json"
    old.write_text(_page())
    clean.write_text(_script().rewrite(_page(), name="T")[0])
    os.utime(clean, (1_000_000_000, 1_000_000_000))
    assert _script().main([str(old), str(clean)]) == 0
    assert _script().rewrite(old.read_text(), name="old") == (old.read_text(), {}), (
        "the rewritten page was not written back")
    assert clean.stat().st_mtime == 1_000_000_000, "a page with nothing to rewrite was rewritten"
    printed = capsys.readouterr().out
    assert "declared_path → link-worktree" in printed and f"{clean}: unchanged" in printed


def test_every_committed_page_is_already_clean_by_the_rewrite() -> None:
    """End to end on the committed corpus: the rewrite finds nothing left to do on any page."""
    pages = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
    assert pages
    for p in pages:
        text = p.read_text()
        assert _script().rewrite(text, name=str(p)) == (text, {}), p.parent.name
