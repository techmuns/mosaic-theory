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

from tests.pre_strip import pre_strip_text
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
        out[t] = mt.PageContext(page=page, mech=pre_synthesis_mech(page),
                                blob=PANEL["pages"][t]["dossier_blob"])
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
    blob, entries = pages["MCK"]
    pages["MCK"] = (blob, [{**g, "type": mt.GAP_CHANGE} if g["item"] == "segment profit by segment"
                           else g for g in entries])
    monkeypatch.setattr(mt, "_gap_pages", lambda: pages)
    seg = Unit("key_unknowns:0", "key_unknowns", "Segment EBITDA is NOT disclosed — a risk.")
    fcf = Unit("key_unknowns:1", "key_unknowns", "The FCF sign is UNKNOWN — a risk.")
    assert mt.gap_framing(seg, ctxs["MCK"]) == []
    assert mt.gap_framing(fcf, ctxs["MCK"])


# ------------------------------------------------------- undefined off its pages, never zero

def test_m_gap_is_undefined_off_the_frozen_pages() -> None:
    nflx = json.loads(pre_strip_text("NFLX"))
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


# ------------------------------------------- #929 review F1: a negated framing word is no framing

#: The six lines the coordinator wrote on MCK (four hit before the negation window).
COORDINATOR_LINES = [
    "Segment profit by segment is our gap (the 10-K XBRL read failed) — an unknown to resolve from "
    "the filing, never bearish.",
    "The company-adjusted EBITDA figures (ev_ebitda_adjusted_fwd) are UNKNOWN: type not "
    "determined, an unknown rather than a risk; the next 10-Q would resolve it.",
    "a company adjusted-EBITDA guide is the company's normal practice (no adjusted-EBITDA guide in "
    "any release read) — not bearish, an unknown only.",
    "Segment profit by segment is UNKNOWN — our gap, which lowers no confidence in the company and "
    "carries no risk signal.",
    "Segment profit by segment is our gap, not a risk about the company; resolve it from the 10-K "
    "segment note.",
    "valuation.adjusted_eps is our gap — not a signal, never a bear point.",
]
#: Compliant typed lines in rule 8's own wording (#927: "an unknown for key_unknowns with what
#: would resolve it and when — never bearish"), every type.
TYPED_LINES = [
    "Segment profit by segment is our gap: the 10-K segment-profit read failed — an unknown; the "
    "10-K's segment note would resolve it at the next annual filing, never bearish.",
    "valuation.adjusted_eps is our gap: the release parser did not read the EPS guide CIQ records "
    "— an unknown until the next release is parsed; not a risk about the company.",
    "The outlook a gap-down's 8-K furnished does not apply: no gap-down 8-K is in the window, so "
    "there is nothing to resolve.",
    "A company adjusted-EBITDA guide is the company's normal practice: no adjusted-EBITDA guide in "
    "any release read — an unknown, not bearish; a first guide in the next release would resolve "
    "it.",
    "The current guide is our gap (no guide parsed from the newest release) — an unknown rather "
    "than a risk; the November release would resolve it.",
    "The FCF sign behind the survival line's runway leg is our gap: the sign was not stored — an "
    "unknown; the 10-Q cash-flow statement would resolve it, and it carries no risk signal.",
    "Segment profit by segment does not apply: a single-segment filer reports no segment profit — "
    "nothing to resolve and no risk.",
    "The covenant basis is type not determined: the credit agreement's definition was not read — "
    "an unknown, never bearish; the exhibit would resolve it.",
    "ev_ebitda_adjusted_fwd is UNKNOWN: type not determined, an unknown rather than a risk; the "
    "next 10-Q would resolve it.",
    "A company adjusted-EBITDA guide (net_debt_to_ebitda_adjusted UNKNOWN) is the company's normal "
    "practice — not bearish and not a risk; the next release would show whether it changes.",
    "The adjusted-EPS guide is our gap, without any risk to the thesis: CIQ's guidance row dated "
    "2026-11-04 would resolve it once the parser reads it.",
    "Segment EBITDA is UNKNOWN — our gap, instead of a risk signal; resolve it from the 10-K "
    "segment note in February.",
]
#: The old rule 8's register ("a missing disclosure is a BEARISH risk"): each must still fire.
OLD_STYLE = [
    ("key_unknowns", "Segment EBITDA is NOT disclosed — an expected disclosure gap; treat this "
                     "missing disclosure as a BEARISH risk."),
    ("key_unknowns", "No revised guidance at the drawdown (ev_ebitda_adjusted_fwd UNKNOWN) — an "
                     "opacity risk to the overshoot case."),
    ("key_unknowns", "The FCF sign is UNKNOWN, a risk, not a neutral gap."),
    ("key_unknowns", "Not neutral — surface the missing segment profit (UNKNOWN) as a BEARISH "
                     "risk."),
    ("key_unknowns", "Covenant headroom is opaque: the covenant basis is UNKNOWN, a red flag "
                     "given 4.0x leverage."),
    ("bear_points", "Segment profit is undisclosed, so the margin mix could be deteriorating."),
    # the negator's window stops at a clause boundary: "not neutral" does not govern "bearish"
    ("key_unknowns", "Segment EBITDA is UNKNOWN; not neutral: a bearish gap."),
]


@pytest.mark.parametrize("text", COORDINATOR_LINES + TYPED_LINES)
def test_a_compliant_typed_line_is_not_a_misread(ctxs: dict[str, mt.PageContext],
                                                 text: str) -> None:
    u = Unit("key_unknowns:0", "key_unknowns", text)
    assert mt.gap_framing(u, ctxs["MCK"]) == [], text


@pytest.mark.parametrize(("section", "text"), OLD_STYLE)
def test_the_old_rule_8_framing_still_fires(ctxs: dict[str, mt.PageContext], section: str,
                                            text: str) -> None:
    assert mt.gap_framing(Unit(f"{section}:0", section, text), ctxs["MCK"]), text


def test_the_negation_window_left_the_gold_unchanged(ctxs: dict[str, mt.PageContext]) -> None:
    """The F1 rule: DEV and TEST keep their hit sets unit for unit (the scores above pin the
    counts; this pins each unit's framing, as recorded before the change)."""
    want = json.loads((GOLD / "m_gap_hits.json").read_text())
    got = {u["id"]: [h.family for h in mt.gap_framing(Unit(u["unit"], u["section"], u["text"]),
                                                        ctxs[u["page"]])]
           for u in _rows("units.jsonl")}
    assert got == want


# ------------------------------------------- #929 review F3: the frozen PAGE, not just its ticker

def test_m_gap_is_undefined_on_another_version_of_a_frozen_ticker(
        ctxs: dict[str, mt.PageContext]) -> None:
    """A re-assembled page of the same ticker would read freeze-time types; it reads none."""
    frozen = ctxs["MCK"]
    u = Unit("key_unknowns:0", "key_unknowns", "Segment EBITDA is NOT disclosed — a risk.")
    assert mt.gap_framing(u, frozen)
    for blob in ("0" * 40, None):
        other = mt.PageContext(page=frozen.page, mech=frozen.mech, blob=blob)
        assert mt.gap_framing(u, other) == []
        assert "M-GAP" not in mt.score_units([u], other)


def _moved_panel() -> dict[str, Any]:
    moved = json.loads(json.dumps(PANEL))
    moved["pages"]["MCK"]["dossier_blob"] = "0" * 40
    return moved


def test_a_registration_refuses_m_gap_on_a_refrozen_page() -> None:
    _history()
    with pytest.raises(rp.ReplayError, match=r"defined only on the pages.*\['MCK'\]"):
        cm.register("dc5b8787", "b109e26c", targets=["M-GAP"], panel=_moved_panel())


def test_a_score_refuses_m_gap_on_a_page_that_is_not_the_frozen_one(tmp_path: Path) -> None:
    reg = cm.Registration(base_ref="A", cand_ref="B", transforms=(), pages=("MCK",), draws=5,
                          targets=("M-GAP",), held_out=(), scorer=cm.scorer_fingerprint())
    out = tmp_path / "run"
    out.mkdir()
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    (out / "draws.jsonl").write_text("")
    with pytest.raises(rp.ReplayError, match=r"not the pages its gap types were frozen on"):
        cm.score_run(out, reg, panel=_moved_panel())


# ----------------------------- #929 review F2: M-LABEL's no-worsening check, on some families only

GATED = ["bleed", "trailing-only", "pe-percentile-blocked"]


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads(pre_strip_text("NFLX"))
    return page


def _with(raw: dict[str, Any], line: str) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(raw))
    out["key_unknowns"] = [*out["key_unknowns"], line]
    return out


def _score(tmp_path: Path, nflx: dict[str, Any], cand_line: str,
           families: dict[str, list[str]] | None) -> cm.Score:
    reg = cm.Registration(base_ref="A", cand_ref="B", transforms=(), pages=("NFLX",), draws=5,
                          targets=("M-SIGN",), held_out=(), scorer=cm.scorer_fingerprint(),
                          no_worsening_families=families or {})
    out = tmp_path / "run"
    out.mkdir()
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    raw = nflx["synthesis"]
    with (out / "draws.jsonl").open("w") as f:
        for cond, r in (("BASE", raw), ("CAND", _with(raw, cand_line))):
            for _ in range(5):
                f.write(json.dumps({"label": f"NFLX:{cond}", "raw": r,
                                    "stop_reason": "tool_use"}) + "\n")
    return cm.score_run(out, reg, pages={"NFLX": nflx})


STATED = "There is no revised guidance available for the drawdown."      # no-adjusted-forward


def test_a_gap_statement_family_blocks_when_the_whole_metric_gates(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    s = _score(tmp_path, nflx, STATED, None)
    assert any(r.startswith("M-LABEL worsens") for r in s.reasons), s.reasons


def test_a_gap_statement_family_is_reported_not_gated_under_the_ruling(
        tmp_path: Path, nflx: dict[str, Any]) -> None:
    """Option A (coordinator, 2026-11-09): a compliant CAND that states more gaps raises the
    gap-statement families; that is reported, never a block."""
    s = _score(tmp_path, nflx, STATED, {"M-LABEL": GATED})
    assert not any("worsens" in r for r in s.reasons), s.reasons
    rest = s.metrics[cm.ungated("M-LABEL", GATED)]
    assert rest.cand_total > rest.base_total and rest.p_upper <= cm.ALPHA
    assert s.metrics["M-LABEL"].cand_total > s.metrics["M-LABEL"].base_total     # still reported


def test_a_gated_family_still_blocks_under_the_ruling(tmp_path: Path,
                                                      nflx: dict[str, Any]) -> None:
    s = _score(tmp_path, nflx, "The share price is in a gradual bleed.", {"M-LABEL": GATED})
    name = cm.gated("M-LABEL", GATED)
    assert any(r.startswith(f"{name} worsens") for r in s.reasons), s.reasons


def test_the_no_worsening_families_field_refuses_what_it_cannot_mean() -> None:
    base: dict[str, Any] = {"base_ref": "A", "cand_ref": "B", "transforms": (), "pages": ("MCK",),
                            "draws": 5, "targets": ("M-GAP",), "held_out": (), "scorer": "x"}
    for fams, why in [({"M-LABEL": ["bleed", "no-such-family"]}, "must be distinct names"),
                      ({"M-LABEL": []}, "must be distinct names"),
                      ({"M-LABEL": ["bleed", "bleed"]}, "must be distinct names"),
                      ({"M-ABSENT": ["nowhere"]}, "named families"),
                      ({"M-GAP": ["risk"]}, "named families")]:
        with pytest.raises(ValueError, match=why):
            cm.Registration(**{**base, "no_worsening_families": fams})
    with pytest.raises(ValueError, match="is a target"):
        cm.Registration(**{**base, "targets": ("M-LABEL",),
                           "no_worsening_families": {"M-LABEL": GATED}})
    ok = cm.Registration(**{**base, "no_worsening_families": {"M-LABEL": GATED}})
    assert cm.Registration.from_json(ok.to_json()) == ok
    plain = cm.Registration(**base)
    assert "no_worsening_families" not in json.loads(plain.to_json())        # old shas kept
