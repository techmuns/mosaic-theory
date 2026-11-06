"""The synthesis eval harness's frozen gold set and its deterministic metrics, pinned on real data.

The gold is the 644 claims of the 2026-11-05/06 fidelity diagnosis
(`tests/fixtures/synthesis_gold`);
every metric pin below reads a REAL gold claim against its REAL committed page — positive (it must
fire) and negative (it must not) — and the frozen fired sets are re-derived for every page whose
facts have not moved since the freeze (design record `2026-11-06-synthesis-eval-harness-design`).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vinci.evals import gold as gd
from vinci.evals import metrics as mt
from vinci.evals import report
from vinci.evals.units import Unit, draw_units, gold_prose

ROOT = Path(__file__).resolve().parents[1]
HITS = json.loads((gd.GOLD_DIR / "metric_hits.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gold() -> list[gd.GoldClaim]:
    return gd.load_gold()


@pytest.fixture(scope="module")
def by_id(gold: list[gd.GoldClaim]) -> dict[str, gd.GoldClaim]:
    return {g.id: g for g in gold}


def _unmoved(ticker: str) -> bool:
    path = ROOT / f"data/dossiers/{ticker}/dossier.json"
    blob = subprocess.run(["git", "hash-object", str(path)], capture_output=True, text=True,
                          check=True).stdout.strip()
    return bool(blob == HITS["pages"][ticker])


def _fires(metric: str, claim: gd.GoldClaim) -> list[mt.Hit]:
    if not _unmoved(claim.page):
        pytest.skip(f"{claim.page}'s page moved since the freeze; its gold reading no longer holds")
    return mt.UNIT_METRICS[metric](claim.unit(), report.gold_context(claim.page))


# ------------------------------------------------------------------------------------- the gold

def test_gold_reproduces_the_diagnosis(gold: list[gd.GoldClaim]) -> None:
    s = gd.summary(gold)
    assert (s["claims"], s["errors"], s["material"], s["adjudicated"]) == (644, 283, 117, 172)
    assert s["material_by_class"] == {"LABEL": 23, "SELECTIVE": 22, "ABSENT": 21, "OVERREACH": 11,
                                      "BASIS": 10, "PATH": 10, "STALE": 9, "SIGN": 5,
                                      "CONFLICT": 5, "PERIOD": 1}
    halves = {h: {g.page for g in gold if g.half == h} for h in ("dev", "test")}
    assert not halves["dev"] & halves["test"]                      # page-disjoint
    assert sum(g.half == "dev" for g in gold) == 330 and len(halves["dev"]) == 14
    assert sum(g.half == "test" for g in gold) == 314 and len(halves["test"]) == 14


def test_a_disagreement_without_adjudication_is_refused(tmp_path: Path) -> None:
    for f in gd.GOLD_DIR.iterdir():
        shutil.copy(f, tmp_path / f.name)
    lines = (tmp_path / "adjudicated.jsonl").read_text(encoding="utf-8").splitlines()
    (tmp_path / "adjudicated.jsonl").write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no adjudication"):
        gd.load_gold(tmp_path)


def test_the_decisive_question_is_scored_as_prose_never_its_source_refs() -> None:
    obj = {"question": "Will it?", "evidence_for": [{"claim": "Up 5%.", "source_ref": "CIQ 2,800"}],
           "evidence_against": [{"claim": "Down.", "source_ref": "x"}]}
    assert gold_prose(obj) == "Will it? Up 5%. Down."
    assert gold_prose("plain text") == "plain text"
    units = draw_units({"bull_points": [{"claim": "a", "source_ref": "r"}], "bear_points": [],
                        "key_unknowns": ["k"], "decisive_question": obj,
                        "twin_reference_cases": [{"distinguishing_fact": "t"}],
                        "evidence_balance": "mixed — b"})
    assert [u.id for u in units] == ["bull_points:0", "key_unknowns:0",
                                     "decisive_question:question",
                                     "decisive_question:evidence_for:0",
                                     "decisive_question:evidence_against:0", "twin:0",
                                     "evidence_balance"]
    assert all("CIQ" not in u.text for u in units)


# ----------------------------------------------------------------- each metric, real claims, ±

@pytest.mark.parametrize(("metric", "claim_id", "family"), [
    # trailing-only on a page with a CIQ forward multiple (gold LABEL)
    ("M-LABEL", "NFLX:key_unknowns:0", "no-adjusted-forward"),
    # the bleed label repeated as fact (gold LABEL)
    ("M-LABEL", "NFLX:bear_points:0", "bleed"),
    # segment profit called undisclosed where the page states it (gold LABEL)
    ("M-LABEL", "GOOGL:key_unknowns:0", "segment-undisclosed"),
    # #921's case: +2,800.0 framed as a drag (gold SIGN)
    ("M-SIGN", "NFLX:bear_points:3", "material-direction"),
    # "compounded without interruption" over a series that dips in FY22 (gold PATH)
    ("M-PATH", "NFLX:bull_points:0", "EBITDA"),
    # a $924B commitment the facts never state (gold ABSENT)
    ("M-ABSENT", "GOOGL:key_unknowns:8", "nowhere"),
    # a quoted management phrase no fact carries (gold ABSENT)
    ("M-ABSENT", "EPAM:key_unknowns:5", "quote:nowhere"),
])
def test_metric_fires_on_its_gold_case(metric: str, claim_id: str, family: str,
                                       by_id: dict[str, gd.GoldClaim]) -> None:
    hits = _fires(metric, by_id[claim_id])
    assert family in {h.family for h in hits}, hits


@pytest.mark.parametrize(("metric", "claim_id"), [
    # single-segment filer: "no segment-EBITDA breakout" is TRUE (gold OK)
    ("M-LABEL", "CNXC:key_unknowns:5"),
    # "a gradual advance, not a drawdown" is not a bleed (gold OK)
    ("M-LABEL", "MCK:key_unknowns:7"),
    # the same NFLX row, stated as income: no flag (gold OK)
    ("M-SIGN", "NFLX:bull_points:0"),
    # "almost unbroken" hedges the path it describes (gold OK)
    ("M-PATH", "GOOGL:bull_points:2"),
    # "$578 billion" is written in a fact's own text (gold OK)
    ("M-ABSENT", "AMZN:bull_points:1"),
    # a possessive ("FY25's $707M and FY24's") is not a quotation (gold OK)
    ("M-ABSENT", "EPAM:bull_points:1"),
])
def test_metric_is_silent_on_a_true_claim(metric: str, claim_id: str,
                                          by_id: dict[str, gd.GoldClaim]) -> None:
    assert _fires(metric, by_id[claim_id]) == []


def test_every_frozen_fired_set_reproduces_on_unmoved_pages(gold: list[gd.GoldClaim]) -> None:
    """The metrics as frozen at a677d1a1, on every page whose facts have not moved: the fired
    claim ids must equal the frozen ones. A metric change moves this pin and owes the record a
    re-measurement on the gold (RUNBOOKS, "Changing the synthesis prompt")."""
    unmoved = {t for t in HITS["pages"] if _unmoved(t)}
    assert unmoved, "every gold page has moved — re-freeze the fixture"
    fired = report.fired_on_gold(gold, tickers=unmoved)
    for metric, ids in HITS["fired"].items():
        want = {i for i in ids if i.split(":")[0] in unmoved}
        assert fired[metric] == want, (metric, sorted(fired[metric] ^ want))


def test_precision_recall_counts_against_the_gold_class(gold: list[gd.GoldClaim]) -> None:
    label = {g.id for g in gold if g.verdict == "LABEL"}
    one_fp = next(g.id for g in gold if g.verdict == "OK")
    pr = gd.precision_recall("M-LABEL", "LABEL", gold, set(list(label)[:10]) | {one_fp}, "all")
    assert (pr.tp, pr.fp, pr.fn) == (10, 1, 46)
    assert pr.precision == pytest.approx(10 / 11) and pr.recall == pytest.approx(10 / 56)


# ------------------------------------------------------------------------ echo and prompt size

def test_echo_reads_instruction_words_and_not_the_facts() -> None:
    ctx = report.gold_context("NFLX")

    class Req:
        system = ("Frame a minority point as a genuine counter-point outweighed by the committed "
                  "lean whenever the lean is committed.")
        user = "Name: x. The ONLY facts you may use:\n\n{}"
        kwargs = {"tools": [{"description": "assemble the framing"}]}

    idx = mt.EchoIndex.of(Req(), ctx)
    echo = Unit("bear_points:0", "bear_points",
                "Margins fell: a genuine counter-point outweighed by the committed lean.")
    plain = Unit("bear_points:1", "bear_points", "EBITDA fell from 6,403 to 5,970 in FY22.")
    assert mt.instruction_echo(echo, ctx, idx)
    assert mt.instruction_echo(plain, ctx, idx) == []


def test_user_sections_split_on_the_prompts_own_headers() -> None:
    user = ("Name: A (A). The ONLY facts you may use:\n\n{\"a\": 1}"
            "\n\n=== PRIMARY-SOURCE CROSS-CHECKS (x) ===\nps"
            "\n\n=== Earnings-call transcripts, each fenced ===\n--- call ---\ntext"
            "\n\n=== MATERIAL FIGURES — STATE EACH ONE ===\nm")
    s = mt.user_sections(user)
    assert list(s) == ["facts", "primary_source", "transcripts", "material_figures"]
    assert sum(len(v) for v in s.values()) == len(user)
