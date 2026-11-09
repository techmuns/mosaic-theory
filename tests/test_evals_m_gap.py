"""M-GAP — the gap-framing metric, and the gold it was calibrated on (2026-11-09).

Fix 4a (#927) replaces the prompt's rule 8 ("a missing disclosure is a BEARISH risk") with the
gap test: only a change or deviation may be raised as a risk. M-GAP counts the misread — a
`key_unknowns` line or bear point that states a gap and holds it against the company, where the
page's gap test types none of the named entries a change. The pins read FROZEN data only: the
221-unit gold (`tests/fixtures/synthesis_gap_gold/`, #926's draws, double-coded blind) and each
panel page's gap types (`vinci/evals/synthesis_gap_types.json`, #927's code at 601d2f7e).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from vinci.evals import compare as cm
from vinci.evals import metrics as mt
from vinci.evals import replay as rp
from vinci.evals.capture_child import pre_synthesis_mech
from vinci.evals.units import Unit

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "tests/fixtures/synthesis_gap_gold"
PANEL = rp.load_panel_file()


def _rows(name: str) -> list[dict[str, Any]]:
    return [json.loads(x) for x in (GOLD / name).read_text().splitlines() if x.strip()]


def _history() -> None:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                       f"{PANEL['freeze_ref']}^{{commit}}"], capture_output=True).returncode != 0:
        pytest.skip("the panel's freeze commit is not in this history")


@pytest.fixture(scope="module")
def ctxs() -> dict[str, mt.PageContext]:
    _history()
    out = {}
    for t in PANEL["panel"]:
        page = rp.page_at(t, PANEL["freeze_ref"], expect_blob=PANEL["pages"][t]["dossier_blob"])
        out[t] = mt.PageContext(page=page, mech=pre_synthesis_mech(page))
    return out


# ----------------------------------------------------------------------------------- the gold

def test_the_gold_is_the_registered_sample_double_coded() -> None:
    units, a, b, gold = (_rows(n) for n in ("units.jsonl", "coder_a.jsonl", "coder_b.jsonl",
                                            "gold.jsonl"))
    adj = _rows("adjudication.jsonl")
    assert len(units) == len(a) == len(b) == len(gold) == 221 and len(adj) == 11
    assert {u["stratum"] for u in units} == {"subject", "random"}
    assert sum(u["stratum"] == "random" for u in units) == 60
    halves = {h: {u["page"] for u in units if u["half"] == h} for h in ("dev", "test")}
    assert halves == {"dev": {"CNXC", "LLY", "MCK"}, "test": {"BURL", "ROST", "SMPL"}}
    assert {u["section"] for u in units} == {"key_unknowns", "bear_points"}
    ea, eb = {r["id"]: r["error"] for r in a}, {r["id"]: r["error"] for r in b}
    assert ea == eb                                         # kappa 1.000 on `error`
    final = {r["id"]: r for r in gold}
    assert sum(r["error"] for r in gold) == 51
    assert {r["id"] for r in adj} == {i for i, r in final.items() if r["decided"] == "adjudicated"}


def test_the_gap_types_are_the_frozen_panel_pages_and_none_is_a_change() -> None:
    data = json.loads(mt.GAP_TYPES_FILE.read_text())
    assert sorted(data["pages"]) == sorted(PANEL["panel"])
    for t, v in data["pages"].items():
        assert v["dossier_blob"] == PANEL["pages"][t]["dossier_blob"], t
        assert v["gaps"] and all(g["type"] != mt.GAP_CHANGE for g in v["gaps"]), t


# ------------------------------------------------------------------------- the metric, scored

def _scores(ctxs: dict[str, mt.PageContext], half: str) -> tuple[int, int, int]:
    gold = {r["id"]: r["error"] for r in _rows("gold.jsonl")}
    tp = fp = fn = 0
    for u in _rows("units.jsonl"):
        if u["half"] != half:
            continue
        hit = bool(mt.gap_framing(Unit(u["unit"], u["section"], u["text"]), ctxs[u["page"]]))
        tp += hit and gold[u["id"]]
        fp += hit and not gold[u["id"]]
        fn += gold[u["id"]] and not hit
    return tp, fp, fn


def test_m_gap_reproduces_its_dev_fit_and_its_one_test_score(
        ctxs: dict[str, mt.PageContext]) -> None:
    """DEV (fit): 34 / 2 / 0. TEST (scored once, 2026-11-09, after the bar was written): 15 / 3 / 2
    — precision 0.833, recall 0.882, kappa 0.827; the bar (0.80 / 0.80 / 0.70) MET."""
    assert _scores(ctxs, "dev") == (34, 2, 0)
    assert _scores(ctxs, "test") == (15, 3, 2)


def test_the_gap_tests_own_typed_lines_are_not_misreads(ctxs: dict[str, mt.PageContext]) -> None:
    """The three compliant lines #927's record quotes on MCK. M-LABEL counts two of them; M-GAP,
    which reads the framing, counts none."""
    lines = [
        "Segment profit by segment (concentration.segment_profit) is our gap: the 10-K "
        "segment-profit read is UNKNOWN.",
        "ev_ebitda_adjusted_fwd does not apply: no gap-down 8-K is in the window.",
        "valuation.adjusted_eps is our gap: CIQ records an EPS guide dated 2026-11-04 the release "
        "parser does not read.",
    ]
    units = [Unit("key_unknowns:0", "key_unknowns", s) for s in lines]
    assert [bool(mt.gap_framing(u, ctxs["MCK"])) for u in units] == [False, False, False]
    assert [bool(mt.label_echo(u, ctxs["MCK"])) for u in units] == [True, True, False]


def test_a_framed_gap_is_a_misread_and_a_neutral_one_is_not(
        ctxs: dict[str, mt.PageContext]) -> None:
    ctx = ctxs["MCK"]

    def hit(section: str, text: str) -> list[str]:
        return [h.family for h in mt.gap_framing(Unit(f"{section}:0", section, text), ctx)]
    gap = "Segment EBITDA is NOT disclosed"
    assert hit("key_unknowns", f"{gap} — an opacity risk.") == ["risk"]
    assert hit("key_unknowns", f"{gap} — a bearish gap.") == ["bearish"]
    assert hit("key_unknowns", f"{gap} — treat it as a risk, not a neutral gap.") == ["risk"]
    assert hit("bear_points", f"{gap}, so the core could be eroding.") == ["bear-rest"]
    assert hit("key_unknowns", f"{gap} — a neutral gap to resolve.") == []
    assert hit("key_unknowns", f"{gap}.") == []
    assert hit("bull_points", f"{gap} — a risk.") == []           # only the two gap sections
    assert hit("key_unknowns", "GLP-1 pricing is a risk to margins.") == []   # no gap stated


def test_a_quoted_label_is_not_the_units_framing_and_a_possessive_is_no_quote(
        ctxs: dict[str, mt.PageContext]) -> None:
    ctx = ctxs["LLY"]
    quoted = "FCF sign is UNKNOWN; the panel reads 'runway not assessable (a risk)'."
    assert mt.gap_framing(Unit("key_unknowns:0", "key_unknowns", quoted), ctx) == []
    possessive = ("The company's segment EBITDA is UNKNOWN, a risk to the thesis the market's "
                  "consensus rests on.")
    assert mt.gap_framing(Unit("key_unknowns:0", "key_unknowns", possessive), ctx)


def test_a_gap_the_page_types_a_change_may_be_raised_as_a_risk(
        ctxs: dict[str, mt.PageContext], monkeypatch: pytest.MonkeyPatch) -> None:
    """The gap test's one exception: on a page whose entry is a change or deviation, framing THAT
    gap as a risk is not a misread — and a gap on another entry still is."""
    pages = dict(mt._gap_pages())
    pages["MCK"] = [{**g, "type": mt.GAP_CHANGE} if g["item"] == "segment profit by segment"
                    else g for g in pages["MCK"]]
    monkeypatch.setattr(mt, "_gap_pages", lambda: pages)
    seg = Unit("key_unknowns:0", "key_unknowns", "Segment EBITDA is NOT disclosed — a risk.")
    fcf = Unit("key_unknowns:1", "key_unknowns", "The FCF sign is UNKNOWN — a risk.")
    assert mt.gap_framing(seg, ctxs["MCK"]) == []
    assert mt.gap_framing(fcf, ctxs["MCK"])


# ------------------------------------------------------- undefined off its pages, never zero

def test_m_gap_is_undefined_off_the_frozen_pages() -> None:
    nflx = json.loads((ROOT / "data/dossiers/NFLX/dossier.json").read_text())
    ctx = mt.PageContext(page=nflx, mech=pre_synthesis_mech(nflx))
    u = Unit("key_unknowns:0", "key_unknowns", "Segment EBITDA is NOT disclosed — a risk.")
    assert "M-GAP" not in mt.score_units([u], ctx)
    assert mt.gap_framing(u, ctx) == []


def test_a_registration_refuses_m_gap_off_its_pages() -> None:
    _history()
    with pytest.raises(rp.ReplayError, match="defined only on the pages"):
        cm.register("dc5b8787", "b109e26c", targets=["M-GAP"], pages=["NFLX"])
    reg = cm.register("dc5b8787", "b109e26c", targets=["M-GAP"])          # the panel: allowed
    assert reg.targets == ("M-GAP",)


def test_the_gap_types_decide_a_score_so_the_scorer_pins_them() -> None:
    assert "vinci/evals/synthesis_gap_types.json" in cm.SCORER_FILES
