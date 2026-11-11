"""The impact run's shortcuts (`vinci.impact.run`): each one is a claim that something is the same
by construction, so each is pinned on what would make it false."""
from __future__ import annotations

import hashlib
import json
import pathlib

from vinci.impact import run as rn

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _lay() -> rn.Layout:
    here = {"base": ROOT, "head": ROOT}
    return rn.Layout(ROOT, here, {}, {}, ROOT)


def test_pages_are_built_when_the_diff_reaches_the_page_builder() -> None:
    reach = rn.page_reach(_lay(), [
        "vinci/edgar/release_parse.py",          # #976: read by `mechanical`
        "vinci/dossier/capital_allocation.py",   # #953
        "vinci/monitor.py",                      # `assemble` imports it
        "data/dossiers/MCK/dossier.json",        # a committed input
        "vinci/evals/capture_child.py",          # the request capture itself
        "vinci/quality/core.py",                 # loads modules by name: assumed to reach
        "tests/test_x.py", "docs/x.md"])
    assert reach == ["data/dossiers/MCK/dossier.json", "vinci/dossier/capital_allocation.py",
                     "vinci/edgar/release_parse.py", "vinci/evals/capture_child.py",
                     "vinci/monitor.py", "vinci/quality/core.py"]


def test_pages_are_not_built_when_the_diff_cannot_reach_them() -> None:
    """#955 changed the ledger correction module only, which only the CLI imports."""
    assert rn.page_reach(_lay(), ["vinci/ledger/correction.py",
                                  "tests/test_ledger_correction.py", "STATE.md"]) == []


def _entry(cache: pathlib.Path, rel: str, url: str, text: str) -> None:
    (cache / rel).parent.mkdir(parents=True, exist_ok=True)
    (cache / rel).write_text(json.dumps({"url": url, "fetched_at": 1.0, "text": text}))


def test_a_kept_build_is_reused_only_while_every_response_it_read_is_unchanged(
        tmp_path: pathlib.Path) -> None:
    cache, kept = tmp_path / "cache", tmp_path / "kept"
    kept.mkdir()
    _entry(cache, "sec/a.json", "https://x/a", "A")
    (kept / "timing.json").write_text("{}")
    (kept / "reads.json").write_text(json.dumps({"https://x/a": {
        "sha256": hashlib.sha256(b"A").hexdigest(), "live": False, "file": "sec/a.json"}}))
    s = rn.Settings(repo=ROOT, base="b", head="h", out=tmp_path / "o", ciq_root=tmp_path,
                    cache_root=cache, store=tmp_path, env_file=None)
    assert rn._reusable(s, kept)
    _entry(cache, "sec/a.json", "https://x/a", "A, refetched by another checkout")
    assert not rn._reusable(s, kept)
    (kept / "reads.json").write_text(json.dumps({"https://x/a": {"sha256": "x", "live": False}}))
    assert not rn._reusable(s, kept)   # a read with no cache file named is never reused


def test_a_failed_build_is_never_reused(tmp_path: pathlib.Path) -> None:
    """Found on the first 27-page run (#976): three page sides failed with "database is locked"
    (a machine fault, since fixed by a store of each build's own), were kept, and a later run
    reused the failures as if they were the code's."""
    cache, kept = tmp_path / "cache", tmp_path / "kept"
    kept.mkdir()
    (kept / "timing.json").write_text("{}")
    (kept / "reads.json").write_text("{}")
    s = rn.Settings(repo=ROOT, base="b", head="h", out=tmp_path / "o", ciq_root=tmp_path,
                    cache_root=cache, store=tmp_path, env_file=None)
    assert rn._reusable(s, kept)
    (kept / "build.error.json").write_text('{"error": "OperationalError"}')
    assert not rn._reusable(s, kept)


def test_a_text_diff_counts_a_removed_line_that_starts_with_dashes() -> None:
    """The unified diff's two FILE headers start "---"/"+++"; a content line removed that itself
    starts "--" (a markdown rule, "---") prints as "----" and was dropped as a header, so a page
    losing its rule read identical. Real committed page, one rule inserted then removed."""
    md = (ROOT / "data" / "dossiers" / "MCK" / "dossier.md").read_text()
    lines = md.splitlines()
    ruled = "\n".join([*lines[:3], "---", *lines[3:]])
    d = rn.text_diff(ruled, md)
    assert (d["identical"], d["removed"], d["added"], d["lines"]) == (False, 1, 0, ["----"])
    assert rn.text_diff(md, md)["identical"]


def test_a_child_that_dies_before_its_steps_names_why_and_is_never_kept(
        tmp_path: pathlib.Path) -> None:
    """The real child on a ``vinci/`` with no ``netcache``: it dies freezing the cache, before any
    step, so no step wrote an error and the page read "not compared" with no reason. The exit is
    now the page's build error, and a build with an error is never kept (`run_child`)."""
    import sqlite3
    import sys

    src = tmp_path / "inputs-src"
    (src / "data" / "dossiers").mkdir(parents=True)
    snap = tmp_path / "out" / "store-snapshot" / "data" / "vinci.db"
    snap.parent.mkdir(parents=True)
    with sqlite3.connect(snap) as c:
        c.execute("create table prices (bar_date text)")
    for d in ("ciq", "cache", "code/head/vinci"):
        (tmp_path / d).mkdir(parents=True)
    s = rn.Settings(repo=ROOT, base="HEAD", head="HEAD", out=tmp_path / "out",
                    ciq_root=tmp_path / "ciq", cache_root=tmp_path / "cache", store=snap,
                    env_file=None, python=sys.executable, log=lambda m: None)
    lay = rn.Layout(s.out, {"head": tmp_path / "code" / "head"}, {}, {}, src)
    lay.code["head"].joinpath("vinci", "__init__.py").write_text("")
    rn._run_child(s, lay, "head", "MCK")
    page = s.out / "pages" / "head" / "MCK"
    assert rn._error(page, "build") == ("ChildExit: the head child exited 1 before writing the "
                                        "page — see MCK.log")
    assert rn.compare_page(s, "MCK")["errors"]["head"]["build"].startswith("ChildExit")
