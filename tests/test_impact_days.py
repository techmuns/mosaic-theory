"""The build's UTC day is one of its inputs (`vinci.impact.run.build_days`).

A $0 page build stamps today's UTC date on the page (`statement_reconciliation.as_filed_by`), and
the date reaches the synthesis request. The sweep's run of #984 (2026-11-12) compared base sides
KEPT from before UTC midnight with head sides built after it: 5 of 27 pages "moved", their requests
with them, on that date alone. Pinned on that run's own dates, cut into
``tests/fixtures/impact/pr984-days.json``.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.impact import report as rp
from vinci.impact import run as rn

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "impact" / "pr984-days.json"


def _settings(tmp_path: pathlib.Path) -> rn.Settings:
    return rn.Settings(repo=tmp_path, base="b", head="h", out=tmp_path / "out",
                       ciq_root=tmp_path, cache_root=tmp_path, store=tmp_path, env_file=None)


def _page(folder: pathlib.Path, assembled_at: str, as_filed_by: str | None) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    recon = {"as_filed_by": as_filed_by} if as_filed_by else None
    (folder / "built.json").write_text(json.dumps({
        "assembled_at": assembled_at,
        "mechanical": {"financial_summary": {"statement_reconciliation": recon}}}))


def test_984s_sides_built_either_side_of_utc_midnight_are_re_built(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every page whose base side ran on 2026-11-11 is re-built, AMZN's among them: its build
    STARTED at 23:43Z and stamped 2026-11-12, so a start time alone does not name the day. The
    pages built on 2026-11-12 at both sides are left alone."""
    monkeypatch.setattr(rn, "utc_today", lambda: "2026-11-12")   # the run's own realign day
    fx = json.loads(FIXTURE.read_text())
    s = _settings(tmp_path)
    for t, sides in fx["pages"].items():
        for side, dates in sides.items():
            _page(s.out / "pages" / side / t, dates["assembled_at"], dates["as_filed_by"])
    rebuilt = {t: rn.off_day_sides(s, t) for t in fx["pages"]}
    assert {t: v for t, v in rebuilt.items() if v} == {
        t: ["base"] for t in ("AMZN", "BRBR", "BURL", "CNXC", "EPAM", "FUBO")}
    assert len(rebuilt) == 27
    assert set(fx["moved_in_that_run"]) <= {t for t, v in rebuilt.items() if v}
    assert rn.build_days(s.out / "pages" / "base" / "AMZN") == ["2026-11-11", "2026-11-12"]


def test_a_side_whose_build_ran_across_midnight_is_re_built_with_its_twin(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rn, "utc_today", lambda: "2026-11-12")
    s = _settings(tmp_path)
    _page(s.out / "pages" / "base" / "MCK", "2026-11-12T00:10:00Z", "2026-11-12")
    head = s.out / "pages" / "head" / "MCK"
    _page(head, "2026-11-11T23:55:00Z", None)
    (head / "clock.json").write_text(json.dumps({"utc_days": ["2026-11-11", "2026-11-12"]}))
    assert rn.off_day_sides(s, "MCK") == ["head"]
    (head / "clock.json").write_text(json.dumps({"utc_days": ["2026-11-12"]}))
    _page(head, "2026-11-12T00:01:00Z", None)
    assert rn.off_day_sides(s, "MCK") == []
    # a side not built is the comparison's to name, never re-built here
    (head / "built.json").unlink()
    assert rn.off_day_sides(s, "MCK") == []


def test_sides_kept_from_two_past_days_are_re_built_today_not_on_the_later_one(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--resume across three days: head kept from 11-11, base from 11-12, the run on 11-13.
    Re-building only the 11-11 side lands it on 11-13, a third day: both are re-built today.
    Two sides kept from ONE past day agree and are left alone."""
    monkeypatch.setattr(rn, "utc_today", lambda: "2026-11-13")
    s = _settings(tmp_path)
    _page(s.out / "pages" / "head" / "MCK", "2026-11-11T10:00:00Z", "2026-11-11")
    _page(s.out / "pages" / "base" / "MCK", "2026-11-12T10:00:00Z", "2026-11-12")
    assert rn.off_day_sides(s, "MCK") == ["base", "head"]
    _page(s.out / "pages" / "base" / "MCK", "2026-11-11T11:00:00Z", "2026-11-11")
    assert rn.off_day_sides(s, "MCK") == []


def test_skip_fail_first_holds_on_the_same_code_shortcut_too(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`run` answers a same-code pair early; part 1 there goes through `part_one` as well."""
    def boom(s: rn.Settings, shas: dict[str, str]) -> dict[str, object]:
        raise AssertionError("fail_first ran under --skip-fail-first")
    monkeypatch.setattr(rn, "fail_first", boom)
    s = rn.Settings(repo=tmp_path, base="b", head="h", out=tmp_path / "out", ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path, env_file=None, skip_fail_first=True)
    assert rn.part_one(s, {}) == {"tests": [], "cases": [], "skipped": True}


def _cache(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
           days: list[str]) -> tuple[rn.Settings, rn.Layout, list[str]]:
    s = _settings(tmp_path)
    monkeypatch.setattr(rn, "BUILD_CACHE", tmp_path / "kept")
    built: list[str] = []

    def fake_build(s: rn.Settings, lay: rn.Layout, side: str, t: str) -> None:
        f = s.out / "pages" / side / t
        _page(f, f"{days[-1]}T00:00:00Z", None)
        (f / "clock.json").write_text(json.dumps({"utc_days": days}))
        (f / "reads.json").write_text("{}")
        (f / "timing.json").write_text("{}")
        built.append(f"{side}/{t}")
    monkeypatch.setattr(rn, "_run_child", fake_build)
    return s, rn.Layout(s.out, {}, {}, {}, s.out), built


def test_a_kept_build_is_reused_only_on_the_utc_day_it_was_built(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#984's base sides were KEPT from 23:43Z the day before: the cache key had no day."""
    s, lay, built = _cache(tmp_path, monkeypatch, ["2026-11-11"])
    monkeypatch.setattr(rn, "utc_today", lambda: "2026-11-11")
    assert rn.run_child(s, lay, "base", "MCK", lambda day: f"k-{day}") == "built"
    assert (tmp_path / "kept" / "k-2026-11-11" / "clock.json").exists()
    assert rn.run_child(s, lay, "base", "MCK", lambda day: f"k-{day}") == "kept"
    monkeypatch.setattr(rn, "utc_today", lambda: "2026-11-12")
    assert rn.run_child(s, lay, "base", "MCK", lambda day: f"k-{day}") == "built"
    assert built == ["base/MCK", "base/MCK"]


def test_a_build_that_ran_across_utc_midnight_is_never_kept(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    s, lay, _ = _cache(tmp_path, monkeypatch, ["2026-11-11", "2026-11-12"])
    monkeypatch.setattr(rn, "utc_today", lambda: "2026-11-12")
    assert rn.run_child(s, lay, "base", "MCK", lambda day: f"k-{day}") == "built"
    assert not (tmp_path / "kept").exists()


def _result(t: str, status: str, realigned: dict[str, object] | None) -> dict[str, object]:
    out: dict[str, object] = {"ticker": t, "status": status, "moves": [],
                              "errors": {"base": {}, "head": {}},
                              "live": {"base": [], "head": []}, "reads": {"base": 1, "head": 1}}
    if realigned is not None:
        out["realigned"] = realigned
    return out


def test_the_section_names_each_re_built_page_and_counts_none_still_on_two_days() -> None:
    r = {"pages": {"built": True, "workers": 4, "seconds": 1.0, "results": [
        _result("BURL", "same", {"sides": ["base"], "still": False,
                                 "days": {"base": ["2026-11-11"], "head": ["2026-11-12"]}}),
        _result("CNXC", "noise", {"sides": ["base"], "still": True,
                                  "days": {"base": ["2026-11-11"], "head": ["2026-11-12"]}}),
        _result("MCK", "same", None)]}}
    lines = rp.pages_lines(r, 40)
    assert lines[0] == "### 2. Pages — built 2 of 3; 0 of 2 move (0 field change(s))"
    said = [ln for ln in lines if ln.startswith("Re-built so both sides were built within one")]
    assert len(said) == 1
    assert said[0].endswith(": BURL, CNXC; still on two days, so set apart as run noise and not "
                            "counted: CNXC")


def test_a_side_with_a_clock_is_dated_by_its_clock_not_by_its_filing_date(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """RULING 2 (2026-11-12): `as_filed_by` is the latest filing the reconciliation read, no longer
    the build's day, so it names no day the build ran on. BURL's two sides in that PR's own run,
    both built on 2026-11-12 (`clock.json`): base stamps the day, head the 10-Q of 2026-08-27. Read
    as a day, head "ran across" 2026-08-27 too, and 26 of 27 pages were set apart as noise. FAILED
    at #1025 (`["head"]`). A side kept from before `clock.json` existed still falls back to the
    page's dates, which #984's run pins above."""
    monkeypatch.setattr(rn, "utc_today", lambda: "2026-11-12")
    s = _settings(tmp_path)
    for side, stamp in (("base", "2026-11-12"), ("head", "2026-08-27")):
        folder = s.out / "pages" / side / "BURL"
        _page(folder, "2026-11-12T11:00:30Z", stamp)
        (folder / "clock.json").write_text(json.dumps({"utc_days": ["2026-11-12"]}))
    assert rn.build_days(s.out / "pages" / "head" / "BURL") == ["2026-11-12"]
    assert rn.off_day_sides(s, "BURL") == []
    # (−) a side WITHOUT a clock still reads the page's dates, as #984's sides do
    (s.out / "pages" / "head" / "BURL" / "clock.json").unlink()
    assert rn.build_days(s.out / "pages" / "head" / "BURL") == ["2026-08-27", "2026-11-12"]
