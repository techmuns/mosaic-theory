"""The eval panel's rule and the exact tests the decision rule reads — real pages, exact math.

The panel is re-derived from its frozen attribute rows (CI has no CIQ copy and a shallow history),
and each committed page whose blob has not moved must still yield its frozen row. The stratified
test is checked against brute-force enumeration and Fisher's exact against #920's own table.
"""
from __future__ import annotations

import json
import re
import subprocess
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path

import pytest

from vinci.evals import panel as pn
from vinci.evals import replay as rp
from vinci.evals import stats as sx

ROOT = Path(__file__).resolve().parents[1]
FROZEN = rp.load_panel_file()


def test_the_rule_reproduces_the_frozen_panel() -> None:
    sel = pn.select_panel(pn.rows_from_json(FROZEN["rows"]), salt=FROZEN["salt"])
    assert list(sel.panel) == FROZEN["panel"] == ["BURL", "CNXC", "LLY", "MCK", "ROST", "SMPL"]
    assert (sel.eligible, sel.subsets, sel.feasible, sel.tied_at_best) == (16, 8008, 906, 7)
    assert FROZEN["v1"]["panel"] == ["CNXC", "LLY", "MCK", "NKE", "ROST", "SMPL"]
    assert [list(t) for t in sel.tied] == FROZEN["search"]["tied_in_hash_order"]


#: AORT's frozen fixture as the RG-D19 page pass wrote it (2026-11-10): its transcript rows' words
#: off it, their fact and locator on it, nothing else moved. The pass moves no input of a panel
#: row (measured on all 28 pages: `docs/records/2026-11-10-driver-facts-page-pass.md`), so this
#: blob still yields the frozen row. Any other move takes the page out of the check.
_AORT_PASSED_BLOB = "983a4b92eee87723dde2b254e6f83dd375dcbe73"


def test_each_unmoved_page_still_yields_its_frozen_row() -> None:
    checked = 0
    for row in FROZEN["rows"]:
        t = row["ticker"]
        path = ROOT / f"data/dossiers/{t}/dossier.json"
        if t == "AORT":  # retired 2026-11-09: its page as committed on 2026-10-26, frozen
            path = ROOT / "tests/fixtures/frozen_pages/2026-10-26/AORT/dossier.json"
        blob = subprocess.run(["git", "hash-object", str(path)], capture_output=True, text=True,
                              check=True).stdout.strip()
        unmoved = {FROZEN["pages"][t]["dossier_blob"]} | ({_AORT_PASSED_BLOB} if t == "AORT"
                                                           else set())
        if blob not in unmoved:
            continue
        page = json.loads(path.read_text(encoding="utf-8"))
        got = pn.page_row(page, transcripts=row["transcripts"], motivated=row["motivated"])
        assert pn.rows_json([got])[0] == row, t
        checked += 1
    assert checked > 0


def test_a_rule_no_subset_meets_is_refused_never_relaxed() -> None:
    rows = [r for r in pn.rows_from_json(FROZEN["rows"]) if r.sleeve != "quality"]
    with pytest.raises(ValueError, match="meets the rule"):
        pn.select_panel(rows, salt=FROZEN["salt"])


@pytest.mark.parametrize(("draws", "modal", "proposal"), [
    ({"mixed": 3, "strongly-bullish": 2}, True, False),     # UBER: one draw flips the modal lean
    ({"strongly-bullish": 3, "mixed": 2}, True, False),     # ROST
    ({"strongly-bullish": 5}, False, True),                 # LLY: one dissent withholds BUY
    ({"strongly-bullish": 4, "mixed": 1}, False, True),     # V: one more agreeing draw proposes
    ({"mixed": 5}, False, False),                           # NKE: mixed proposes nothing
    ({"mixed": 4, "strongly-bearish": 1}, False, False),    # SMPL
])
def test_boundaries_follow_productions_unanimity_gate(draws: dict[str, int], modal: bool,
                                                      proposal: bool) -> None:
    assert pn._boundaries(draws) == (modal, proposal)


def test_fisher_reproduces_920s_table() -> None:
    table = {(5, 0): "0.008", (5, 1): "0.048", (4, 0): "0.048", (5, 2): "0.167", (3, 0): "0.167",
             (4, 1): "0.206", (2, 0): "0.444", (1, 0): "1.000"}
    for (a, b), want in table.items():
        assert f"{float(sx.fisher_two_sided(a, 5, b, 5)):.3f}" == want


def test_the_stratified_test_equals_brute_force_enumeration() -> None:
    pages = [sx.PageDraws("A", (2, 1, 3), (0, 1, 0)), sx.PageDraws("B", (1, 1), (0, 2))]
    r = sx.stratified_exact(pages)
    splits = []
    for p in pages:
        pooled = list(p.base) + list(p.cand)
        splits.append([sum(pooled[i] for i in idx)
                       for idx in combinations(range(len(pooled)), len(p.cand))])
    totals = [sum(c) for c in product(*splits)]
    assert r.observed == 3
    assert r.p_lower == Fraction(sum(t <= 3 for t in totals), len(totals))
    assert r.p_upper == Fraction(sum(t >= 3 for t in totals), len(totals))


def test_the_panel_detectability_the_record_states() -> None:
    def p_lower(base: int, cand: int) -> float:
        return float(sx.stratified_exact([
            sx.PageDraws(str(i), tuple([1] * base + [0] * (5 - base)),
                        tuple([1] * cand + [0] * (5 - cand))) for i in range(6)]).p_lower)
    assert round(p_lower(1, 0), 3) == 0.016
    assert round(p_lower(2, 1), 3) == 0.089
    assert round(p_lower(3, 2), 3) == 0.108       # one draw fewer per page is not evidence


def test_a_page_with_no_draws_in_a_condition_is_refused() -> None:
    with pytest.raises(ValueError, match="no draws"):
        sx.stratified_exact([sx.PageDraws("A", (1, 0), ())])
    with pytest.raises(ValueError, match="no pages"):
        sx.stratified_exact([])


def test_nothing_on_the_decision_path_imports_the_harness() -> None:
    """The harness, and the impact check that replays its frozen panel (`vinci/impact/`, a
    PR-verification tool, 2026-11-11), may import `vinci.evals`; nothing else may. And the decision
    path reaches the impact check only through its comparator, `vinci.impact.values`, which
    imports neither package — so the harness stays off the decision path through it too."""
    def grep(pattern: str, *paths: str) -> list[str]:
        done = subprocess.run(["git", "-C", str(ROOT), "grep", "--untracked", "-l", "-E",
                               pattern, "--", *paths], capture_output=True, text=True)
        return done.stdout.split()
    hits = grep(r"(from|import) vinci\.evals", "vinci")
    assert all(h.startswith(("vinci/evals/", "vinci/impact/")) for h in hits), hits
    users = [h for h in grep(r"(from|import) vinci\.impact", "vinci")
             if not h.startswith(("vinci/impact/", "vinci/evals/"))]
    for h in users:
        lines = [ln.strip() for ln in (ROOT / h).read_text().splitlines()
                 if re.search(r"(from|import) vinci\.impact\b", ln)]
        assert lines and all(ln.startswith("from vinci.impact.values import ") for ln in lines), \
            (h, lines)
    assert not grep(r"(from|import) vinci\.(evals|impact)", "vinci/impact/values.py")
