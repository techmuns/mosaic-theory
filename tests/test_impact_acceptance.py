"""The impact check on real merged PRs — its acceptance runs, frozen (`tests/fixtures/impact/`).

Each fixture is a real report of `python -m vinci.impact run` on 2026-11-11, cut to what can be
published (local paths scrubbed, request text and CIQ file names dropped; the cut is stated in
the fixture's ``_cut``). The pins read the RENDERED SECTION, the thing pasted into a PR body, and
the JSON beside it: the known effect of each PR must show, and nothing else may.

- #976 (base c2a4d743, head 2b9b766c): no guide moves; refusal notes reach the page's caveats on
  NFLX (+3) and VITL (+2), as #976 states, and on WERN (+2, a release its committed page does not
  cite yet); the 21 default-period flags; and NO synthesis request moves — #976's body said NFLX's
  and VITL's would, but the notes are page flags, and the synthesis is sent the mechanical layer
  less `primary_source` (`synthesis.NOT_SENT`).
- #953 (base 586fdcfd, head 7ec84833): MCK's impairment headroom $12,950.0M → $15,214.0M on the
  page a re-assembly would publish, its intangibles leg read from the current tag (1,678 as at
  2012-06-30 → 3,942 as at 2026-09-30); the headroom field gained on all 27 pages. And, unseen
  by its frozen-panel replay, the facts its pages' next requests carry move on 23 of 27 — five
  panel pages among them — which the section puts to the operator.
"""
from __future__ import annotations

import collections
import json
import pathlib
from typing import Any

from vinci.impact.report import markdown

FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "impact"


def _load(name: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((FIX / name).read_text())
    return doc


def _pages(r: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["ticker"]: p for p in r["pages"]["results"]}


def test_976_moves_no_guide_on_the_27_pages() -> None:
    r = _load("pr976.json")
    assert len(r["pages"]["results"]) == 27
    md = markdown(r, json_name="report.json")
    assert ("| `mechanical.primary_source.releases[].guidance[]` | 146 | 146 | 0 | none |"
            in md)
    assert not any(".guidance[" in m["path"] for p in r["pages"]["results"]
                   for m in p["moves"])


def test_976_lifts_its_refusal_notes_to_nflx_vitl_and_wern() -> None:
    r = _load("pr976.json")
    added = collections.Counter(p["ticker"] for p in r["pages"]["results"] for m in p["moves"]
                                if m["path"] == "caveats[+]")
    assert added == {"NFLX": 3, "VITL": 2, "WERN": 2}
    assert all(m["head"].startswith("Guidance stated but not attributable")
               for p in r["pages"]["results"] for m in p["moves"] if m["path"] == "caveats[+]")
    md = markdown(r, json_name="report.json")
    assert "### 2. Pages — built 27 of 27; 7 of 27 move (38 field change(s))" in md
    assert "- **The $0 build's page rendered** by each side's code: 3 of 27 differ — NFLX, VITL, " \
           "WERN" in md


def test_976_writes_its_21_default_period_flags_where_it_says() -> None:
    r = _load("pr976.json")
    flags = collections.Counter(
        p["ticker"] for p in r["pages"]["results"] for m in p["moves"]
        if m["kind"] == "added" and str(m["head"]).startswith("Guidance period not read"))
    assert flags == {"BURL": 1, "EPAM": 1, "SMPL": 13, "VITL": 1, "VRRM": 5}


def test_976_moves_no_synthesis_request_and_owes_no_panel_check() -> None:
    r = _load("pr976.json")
    assert {t: p["request"]["identical"] for t, p in _pages(r).items()} == dict.fromkeys(
        _pages(r), True)
    assert all(d["identical"] for d in r["panel_requests"]["pages"].values())
    md = markdown(r, json_name="report.json")
    assert "### 3. Synthesis requests — 0 of 27 pages' requests differ" in md
    assert "(`evals compare_requests`): 0 of 6 differ" in md
    assert "Row-53 panel check: **not owed**" in md


def test_976_fails_first_and_passes_at_head() -> None:
    r = _load("pr976.json")
    ff = r["fail_first"]
    assert ff["missing_at_base"] == ["vinci.edgar.release_parse.GUIDANCE_PERIOD_DEFAULT_PREFIX"]
    first = [c for c in ff["cases"] if c["base"]["outcome"] == "failed"
             and c["head"]["outcome"] == "passed"]
    assert len(first) == 29 and len(ff["cases"]) == 108
    assert not [c for c in ff["cases"] if c["head"]["outcome"] != "passed"]
    d1 = next(c for c in first if c["node"].endswith("::test_re2_d1_two_actuals_joined_by_and_"
                                                      "are_not_a_guide"))
    assert d1["base"]["where"] == "tests/test_guidance_fix2_e2.py:52"


def test_976s_inputs_were_one_set_for_both_codes() -> None:
    r = _load("pr976.json")
    assert all(not p["inputs_differ"] for p in r["pages"]["results"])
    assert r["stamp"]["inputs"]["store"]["written_by"] == []
    assert r["stamp"]["inputs"]["ciq_moved_during_run"] == []
    assert "<local>" not in json.dumps(r["stamp"]["inputs"])


def test_953_moves_mcks_headroom_from_12950_to_15214() -> None:
    r = _load("pr953.json")
    mck = _pages(r)["MCK"]
    lines = mck["built_md"]["lines"]
    assert "-- **Impairment headroom — goodwill + intangibles remaining:** $12,950.0M [12]" in lines
    assert ("+- **Impairment headroom — goodwill + intangibles remaining, as at 2026-09-30:** "
            "$15,214.0M [12]") in lines
    by = {m["path"]: m for m in mck["moves"]}
    leg = by["mechanical.capital_allocation.intangibles.value"]
    assert (leg["base"], leg["head"]) == (1678.0, 3942.0)
    assert by["mechanical.capital_allocation.intangibles.source_ref"]["base"].endswith(
        "IntangibleAssetsNetExcludingGoodwill (as at 2012-06-30)")
    gained = by["mechanical.capital_allocation.impairment_headroom"]
    assert gained["base"] == "ABSENT" and gained["head"]["value"]["value"] == 15214.0
    md = markdown(r, json_name="report.json")
    assert ("| MCK | `mechanical.capital_allocation.intangibles.value` | 1678.0 → 3942.0 | "
            "'EDGAR companyfacts FiniteLivedIntangibleAssetsNet (as at 2026-09-30)' |") in md


def test_953_moves_every_page_and_puts_its_request_move_to_the_operator() -> None:
    r = _load("pr953.json")
    assert {p["status"] for p in r["pages"]["results"]} == {"moves"}
    assert len(r["pages"]["results"]) == 27
    differ = sorted(t for t, p in _pages(r).items() if not p["request"]["identical"])
    assert len(differ) == 23
    assert {"BURL", "CNXC", "MCK", "ROST", "SMPL"} <= set(differ) and "LLY" not in differ
    assert all(set(_pages(r)[t]["request"]["sections"]) == {"facts"} for t in differ)
    md = markdown(r, json_name="report.json")
    assert "(`evals compare_requests`): 0 of 6 differ" in md
    assert ("Row-53 panel check: **ASK THE OPERATOR** — the request moves on panel page(s) "
            "BURL, CNXC, MCK, ROST, SMPL in its FACTS section only") in md


def test_977_a_docs_only_pr_moves_nothing() -> None:
    """#977 (bookkeeping: STATE.md, the fix log, a record): no behaviour path, byte-identical
    code, so nothing is built and the section says why. Its control — every page built twice
    from the one code — is the noise floor, measured in the record."""
    r = _load("pr977.json")
    assert r["stamp"]["diff_identity"]["patch_id"] is None
    assert r["stamp"]["diff_identity"]["paths"] == []
    assert r["same_code"] is True and "pages" not in r
    md = markdown(r, json_name="report.json")
    assert "**Nothing moves:** base and head carry byte-identical `vinci/`" in md
    assert "the PR changes no code (`vinci/`, `frontend/build.py`)" in md
    assert "### 2–5. Pages, requests, rendered surface, downstream readers — the same by " \
           "construction" in md


def test_the_section_names_no_local_path() -> None:
    """The section is pasted into a PUBLIC PR body: a path in a test's message (pytest prints the
    module it imported from) or in the run folder is scrubbed."""
    r = _load("pr976.json")
    case = r["fail_first"]["cases"][0]
    case["base"] = {"outcome": "failed", "where": "tests/x.py:1", "message":
                    "ImportError: from '/private/tmp/claude-501/run/base-tree/vinci/m.py'"}
    case["head"] = {"outcome": "failed", "where": "tests/x.py:1",
                    "message": "seen in /Users/someone/Documents/x"}
    md = markdown(r, json_name="report.json", run_dir="/private/tmp/claude-501/run")
    assert "/private/tmp" not in md and "/Users/" not in md
    assert "from '<run>/base-tree/vinci/m.py'" in md and "seen in <local>/Documents/x" in md


def test_953_owes_the_panel_when_the_frozen_replay_did_not_run() -> None:
    """ASK THE OPERATOR states that the frozen replay is identical; when the replay was refused
    nothing measured that, so the same moves read OWED (the conservative verdict)."""
    r = _load("pr953.json")
    r["panel_requests"] = {"status": "refused", "why": "ReplayError: no frozen blob", "pages": {}}
    md = markdown(r, json_name="report.json")
    assert "**ASK THE OPERATOR**" not in md
    assert ("Row-53 panel check: **OWED** — the request moves on panel page(s) "
            "BURL, CNXC, MCK, ROST, SMPL") in md


def test_976s_burl_and_smpl_flags_are_reported_and_reach_no_request() -> None:
    """The parser stream's requirement (coordinator, 2026-11-11): a parser fix must be read from
    each ref's FRESH build, never a replay of the committed layer (where #976's `compare` refused,
    "reaches no page's request"), and the section must say whether its moves reach a request.
    BURL's 1 and SMPL's 13 default-period flags sit in `primary_source`, which is NOT_SENT."""
    r = _load("pr976.json")
    for t, n in (("BURL", 1), ("SMPL", 13)):
        flags = [m for m in _pages(r)[t]["moves"]
                 if m["path"].startswith("mechanical.primary_source.releases[")
                 and str(m["head"]).startswith("Guidance period not read")]
        assert len(flags) == n, t
        assert _pages(r)[t]["request"]["identical"] is True
    md = markdown(r, json_name="report.json")
    assert ("- Pages whose fields move while their request stays byte-identical — their moves "
            "reach no synthesis request: 7 of 7 — BURL, EPAM, NFLX, SMPL, VITL, VRRM, WERN") in md


def test_a_page_not_built_at_a_side_is_named_and_out_of_the_count() -> None:
    """Coordinator, 2026-11-11 (#970's hand-built section built 17 of 27): the coverage leads, and
    every page not built is named with why — a "0 move" says nothing about it."""
    r = _load("pr976.json")
    vitl = _pages(r)["VITL"]
    vitl["status"] = "not compared"
    vitl["errors"]["base"]["build"] = ("DossierAssemblyError: VITL: no price history in the "
                                       "store")
    md = markdown(r, json_name="report.json")
    assert "### 2. Pages — built 26 of 27; 6 of 26 move" in md
    assert "- VITL — base: DossierAssemblyError: VITL: no price history in the store" in md
