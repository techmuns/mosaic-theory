"""MARKET_REGIME is reserved for equity-market STRUCTURE (found 2026-10-11: the Citi Gridlock card
"Uneven US regional power-market regulation makes regional selection drive grid/generation
returns" was a market-regime record — its evidence is regulation, transmission capacity and
procurement windows, not breadth, dispersion, correlation or volatility).

Articles are HYPOTHETICAL and labelled; extractions use the REAL types. The real J.P. Morgan
calm-index dispersion record stays a market regime (pinned in the acceptance tests).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import ThesisKind

AS_OF = date(2026, 10, 11)


def _case(tmp_path: Path, node: str, texts: list[str], metric: str) -> tuple[Pipeline, Any]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    art = Hypo(slug=f"kind-{node}", publisher="Hypothetical Research", published=AS_OF,
               blocks=[("paragraph", t) for t in texts])
    claims = [claim(f"c{i}", f"b00{i}", t.rstrip("."), t[:50], metric=metric,
                    value=float(next(w for w in t.replace("%", " ").split() if w.isdigit())),
                    value_text=next(w for w in t.split() if any(ch.isdigit() for ch in w)),
                    unit="%" if "%" in t else "GW", period="2026")
              for i, t in enumerate(texts, 1)]
    h = hyp("h1", "Regional selection drives returns", node=node,
            mechanism="dispersion_selection", supporting=[c["local_id"] for c in claims],
            kind="market_regime")
    ext = extraction(claims, [h])
    Extraction.model_validate(ext)
    ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)
    [t] = [t for t in pipe.store.theses() if t.key_node == node]
    return pipe, t


def test_a_sector_regulation_record_is_an_investment_thesis(tmp_path: Path) -> None:
    pipe, t = _case(tmp_path, "ai_infrastructure.power_grid", [
        "ERCOT transmission infrastructure can handle about 160 GW of load before expansion.",
        "Texas regulators must prepare for organic load growth of 2% as the economy grows."],
        "grid capacity")
    assert t.kind is ThesisKind.INVESTMENT_THESIS
    [i] = [i for i in pipe.store.issues() if i.code == "RECORD_KIND_CORRECTED"]
    assert "measures equity-market structure" in i.detail and "power_grid" in i.detail
    v = pipe.store.thesis_versions(t.thesis_id)[-1]
    assert v.content.header.kind is ThesisKind.INVESTMENT_THESIS
    # its earnings transmission is TESTED (never waved through as "not applicable")
    trace = " ".join(v.priority.rules_fired)
    assert "market-regime record" not in trace
    assert all("market-regime record argues" not in s.text for s in v.content.s03_transmission)


def test_a_sector_record_measuring_market_structure_stays_a_regime(tmp_path: Path) -> None:
    pipe, t = _case(tmp_path, "ai_infrastructure.compute_semis", [
        "Dispersion across semiconductor stocks reached 35% this quarter."], "stock dispersion")
    assert t.kind is ThesisKind.MARKET_REGIME
    assert not [i for i in pipe.store.issues() if i.code == "RECORD_KIND_CORRECTED"]


def test_a_market_wide_record_stays_a_regime(tmp_path: Path) -> None:
    pipe, t = _case(tmp_path, "macro_market", [
        "Implied correlation across the index fell to 9% this month."], "implied correlation")
    assert t.kind is ThesisKind.MARKET_REGIME
