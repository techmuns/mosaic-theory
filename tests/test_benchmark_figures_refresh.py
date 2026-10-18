"""Correcting a page's benchmark figures under a kept synthesis (STATE row 32 (7)).

Nine committed pages read SPY's or MDY's 2026-09-16 close as the 2026-09-22 close.
`benchmark_figures_transform` re-reads the benchmark side through `refresh_dossier`, the one write
path, keeping the synthesis. Two things are pinned here.

1. `moved_cited_returns`. The write path refused a moved figure the prose cites only when the
   figure was MONEY; a return passed both existing checks. On 2026-10-18 seven of the nine pages
   quoted the stale return ("SPY rose ~16.9% (-47.6% relative)"), and a refresh would have left
   them contradicting their own tables. Its pins use FROZEN prose excerpts, copied verbatim from
   those pages on 2026-10-18, never the living synthesis: a model-written page rewords on every
   re-assembly.
2. The transform. It runs on TECX (IWM, dated 2026-09-22) against the committed price fixtures,
   which reproduce the page exactly. The stale page is made the way the incident made it: by the
   old unbounded lookup over IWM with 09-17..09-22 missing.
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import mechanical as dm
from vinci.dossier.refresh import (
    RefreshRefusedError,
    benchmark_figures_transform,
    moved_cited_returns,
    refresh_dossier,
    return_cited,
)
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
PRICES = ROOT / "tests" / "fixtures" / "prices"
HOLE = (date(2026, 9, 17), date(2026, 9, 22))

# FROZEN excerpts of the nine pages' prose, 2026-10-18 (verbatim; never the living synthesis)
NKE = ("The stock is idiosyncratically weak, down ~30.7% over 180d while SPY rose ~16.9% "
       "(-47.6% relative)")
PARR = "PARR is +112% over the trailing year vs +11% for MDY, and sits near its 52-week high"
WLK = ("The stock has moved alone to the downside — down 39% over 180 days versus a +8.5% "
       "market benchmark (rel −48%)")
GOOGL = ("the franchise remains a durable compounder: Search & Other grew 17% in Q2 2026 with "
         "AI Mode")


def _doc(*claims: str) -> dict[str, Any]:
    return {"synthesis": {"bear_points": [{"claim": c, "source_ref": "frozen"} for c in claims]}}


def _mech(*, market: float, rel: float, bench_ret: float, symbol: str = "SPY",
          name: float = -0.307) -> dict[str, Any]:
    return {"idiosyncratic_vs_shared": {
        "benchmark_symbol": symbol, "name_180d_return": {"value": name},
        "market_180d_return": {"value": market}, "rel_vs_market": {"value": rel}},
        "stock_performance": {"name_return": 0.5, "benchmark_return": bench_ret}}


def test_a_moved_return_the_prose_quotes_to_one_decimal_is_refused() -> None:
    before = _mech(market=0.1689, rel=-0.4757, bench_ret=0.137)
    after = _mech(market=0.1989, rel=-0.5057, bench_ret=0.137)
    hits = moved_cited_returns(before, after, _doc(NKE))
    assert [h.split(" =")[0] for h in hits] == ["idiosyncratic_vs_shared.market_180d_return",
                                                "idiosyncratic_vs_shared.rel_vs_market"]


def test_a_rounded_return_counts_only_beside_the_market() -> None:
    """'+11% for MDY' is the benchmark's 11.2%. NEGATIVE: GOOGL's 'grew 17%' is a revenue growth
    rate beside a 16.9% SPY return; with no market word or symbol near it, it is not a citation."""
    hits = moved_cited_returns(_mech(market=0.085, rel=0.17, bench_ret=0.112, symbol="MDY"),
                               _mech(market=0.085, rel=0.17, bench_ret=0.120, symbol="MDY"),
                               _doc(PARR))
    assert hits == ["stock_performance.benchmark_return = +11.2% → +12.0%"]
    assert moved_cited_returns(_mech(market=0.1689, rel=0.081, bench_ret=0.137),
                               _mech(market=0.1989, rel=0.051, bench_ret=0.166),
                               _doc(GOOGL)) == []
    assert not return_cited(GOOGL, 0.1689, symbol="SPY")


def test_a_return_behind_an_escaped_minus_is_still_read() -> None:
    """The stored claim is serialised with JSON's ASCII escaping, so WLK's 'rel −48%' arrives as
    'rel \\u221248%' — the escape's last digit sat against the 48 and hid it (2026-10-18)."""
    hits = moved_cited_returns(_mech(market=0.085, rel=-0.479, bench_ret=0.11, symbol="MDY"),
                               _mech(market=0.085, rel=-0.486, bench_ret=0.11, symbol="MDY"),
                               _doc(WLK))
    assert hits == ["idiosyncratic_vs_shared.rel_vs_market = -47.9% → -48.6%"]


def test_a_quoted_return_that_did_not_move_is_never_refused() -> None:
    same = _mech(market=0.1689, rel=-0.4757, bench_ret=0.137)
    assert moved_cited_returns(same, json.loads(json.dumps(same)), _doc(NKE)) == []


def test_the_write_path_refuses_a_page_whose_prose_quotes_the_moved_return(
        tmp_path: Path) -> None:
    """At the call site: `refresh_dossier` on a copy of a committed page whose synthesis carries a
    frozen claim quoting its market return — refused, naming the figure, the page untouched."""
    shutil.copytree(ROOT / "data" / "dossiers" / "GOOGL", tmp_path / "GOOGL")
    path = tmp_path / "GOOGL" / "dossier.json"
    doc = json.loads(path.read_text())
    io = doc["mechanical"]["idiosyncratic_vs_shared"]
    old = io["market_180d_return"]["value"]
    doc["synthesis"]["key_unknowns"] = [
        *doc["synthesis"]["key_unknowns"],
        f"GOOGL beat SPY, which rose {old * 100:.1f}% over 180 days."]
    path.write_text(json.dumps(doc))
    before = path.read_text()

    def move(mech: dict[str, Any]) -> dict[str, Any]:
        mech["idiosyncratic_vs_shared"]["market_180d_return"]["value"] = old + 0.03
        return mech

    with pytest.raises(RefreshRefusedError, match="market_180d_return"):
        refresh_dossier(path, transform=move)
    assert path.read_text() == before


# --- the transform, on TECX against the committed price fixtures --------------------------------

def _tecx(tmp_path: Path, *, drop: tuple[date, date] | None = None) -> tuple[Path, Path, Identity]:
    """A copy of TECX's committed page (its synthesis removed: the transform is pinned apart from
    the citation guard above) and a store of the committed price fixtures."""
    shutil.copytree(ROOT / "data" / "dossiers" / "TECX", tmp_path / "dossiers" / "TECX")
    page = tmp_path / "dossiers" / "TECX" / "dossier.json"
    doc = json.loads(page.read_text())
    doc["synthesis"] = None
    page.write_text(json.dumps(doc))
    row = next(r for r in map(json.loads, (ROOT / "data" / "snapshots" / "securities.jsonl")
                              .read_text().splitlines()) if r["ticker"] == "TECX")
    ident = Identity(**{k: row[k] for k in ("internal_id", "issuer_id", "cik", "ticker", "mic",
                                            "exchange", "eod_symbol", "name")})
    db = tmp_path / "prices.db"
    with Store(db) as s:
        s.upsert_security(ident)
        for name in ("TECX", "IWM"):
            bars = [PriceBar(**json.loads(x)) for x in (PRICES / f"{name}.jsonl").read_text()
                    .splitlines() if x.strip()]
            s.write_prices([b for b in bars if drop is None or name != "IWM"
                            or not drop[0] <= b.bar_date <= drop[1]])
    refresh_dossier(page)  # the copy re-serialised once, so a later refresh measures only itself
    return page, db, ident


def test_the_transform_restores_a_page_built_on_a_benchmark_hole(tmp_path: Path) -> None:
    """The incident's shape on IWM: the page's benchmark side is rebuilt the way the stale pages
    were (the old lookup over IWM missing 09-17..09-22); the transform, on complete bars, restores
    every benchmark figure exactly — and leaves the name's side and the cohort as stored."""
    page, db, ident = _tecx(tmp_path)
    committed = json.loads(page.read_text())["mechanical"]
    ref = date(2026, 9, 22)
    iwm = [PriceBar(**json.loads(x)) for x in (PRICES / "IWM.jsonl").read_text().splitlines()
           if x.strip() and not HOLE[0] <= date.fromisoformat(json.loads(x)["bar_date"]) <= HOLE[1]]
    stale_mkt = dm._window_return(iwm, ref, 180)
    assert stale_mkt is not None and stale_mkt != committed["idiosyncratic_vs_shared"][
        "market_180d_return"]["value"]  # the hole really moves the figure
    doc = json.loads(page.read_text())
    io = doc["mechanical"]["idiosyncratic_vs_shared"]
    io["market_180d_return"]["value"] = stale_mkt
    io["rel_vs_market"]["value"] = io["name_180d_return"]["value"] - stale_mkt
    doc["mechanical"]["stock_performance"]["benchmark_return"] = 0.0
    page.write_text(json.dumps(doc))

    assert refresh_dossier(page, transform=benchmark_figures_transform("TECX", ref, store_path=db))
    fixed = json.loads(page.read_text())["mechanical"]
    for k in ("market_180d_return", "rel_vs_market", "name_180d_return", "cohort", "read"):
        assert fixed["idiosyncratic_vs_shared"][k] == committed["idiosyncratic_vs_shared"][k], k
    assert fixed["stock_performance"] == committed["stock_performance"]


def test_the_transform_is_a_no_op_on_a_correct_page(tmp_path: Path) -> None:
    """NEGATIVE: on the committed page and complete bars nothing moves — the file is untouched."""
    page, db, _ident = _tecx(tmp_path)
    before = page.read_text()
    assert not refresh_dossier(
        page, transform=benchmark_figures_transform("TECX", date(2026, 9, 22), store_path=db))
    assert page.read_text() == before


def test_a_page_whose_own_bars_do_not_reproduce_is_refused_not_skipped(tmp_path: Path) -> None:
    """NEGATIVE: the name's side must reproduce the stored page exactly. If it does not, the
    refresh is REFUSED, naming why — never a silent "nothing moved" that reads like a page already
    correct (code review of #745). Here the stored name move is off by a basis point."""
    page, db, _ident = _tecx(tmp_path)
    doc = json.loads(page.read_text())
    io = doc["mechanical"]["idiosyncratic_vs_shared"]
    io["name_180d_return"]["value"] += 0.0001
    io["market_180d_return"]["value"] = 0.5  # a stale benchmark the transform would otherwise fix
    page.write_text(json.dumps(doc))
    before = page.read_text()
    with pytest.raises(RefreshRefusedError, match="180-day move does not reproduce"):
        refresh_dossier(page, transform=benchmark_figures_transform(
            "TECX", date(2026, 9, 22), store_path=db))
    assert page.read_text() == before


# --- code review of #745 ------------------------------------------------------------------------

def test_a_missing_store_is_refused_and_never_created(tmp_path: Path) -> None:
    """Opening a store that is not there would CREATE an empty one — the side effect that once
    contaminated a gate run. The transform refuses first, and nothing is written."""
    page, _db, _ident = _tecx(tmp_path)
    absent = tmp_path / "nowhere" / "vinci.db"
    with pytest.raises(RefreshRefusedError, match="no price store"):
        refresh_dossier(page, transform=benchmark_figures_transform(
            "TECX", date(2026, 9, 22), store_path=absent))
    assert not absent.exists() and not absent.parent.exists()


def test_a_ticker_that_is_not_exactly_one_security_is_refused(tmp_path: Path) -> None:
    page, db, ident = _tecx(tmp_path)
    for n in (0, 2):
        with Store(db) as s:
            s._conn.execute("DELETE FROM securities")  # noqa: SLF001 — the fixture's own table
            s._conn.commit()  # noqa: SLF001
            for i in range(n):
                s.upsert_security(
                    ident.model_copy(update={"internal_id": f"{ident.internal_id}-{i}"}))
        with pytest.raises(RefreshRefusedError, match=f"{n} securities carry the ticker"):
            refresh_dossier(page, transform=benchmark_figures_transform(
                "TECX", date(2026, 9, 22), store_path=db))


def test_a_page_without_a_52_week_exhibit_has_its_180_day_figures_corrected(
        tmp_path: Path) -> None:
    """A page with no exhibit still has a stale market figure to correct: the 180-day figures are
    re-read alone, and no exhibit is invented."""
    page, db, _ident = _tecx(tmp_path)
    committed = json.loads(page.read_text())["mechanical"]["idiosyncratic_vs_shared"]
    doc = json.loads(page.read_text())
    doc["mechanical"].pop("stock_performance", None)
    doc["mechanical"]["idiosyncratic_vs_shared"]["market_180d_return"]["value"] = 0.5
    page.write_text(json.dumps(doc))
    refresh_dossier(page)  # re-serialised, so the refresh below measures only itself
    assert refresh_dossier(page, transform=benchmark_figures_transform(
        "TECX", date(2026, 9, 22), store_path=db))
    fixed = json.loads(page.read_text())["mechanical"]
    assert fixed["idiosyncratic_vs_shared"]["market_180d_return"] == committed[
        "market_180d_return"]
    assert fixed.get("stock_performance") is None


def test_a_half_step_value_is_read_however_the_prose_rounded_it() -> None:
    """16.85% is "16.8%" to one writer and "16.9%" to another; Python's own rounding picks one."""
    for prose in ("SPY rose 16.8% over 180 days", "SPY rose 16.9% over 180 days"):
        assert return_cited(prose, 0.1685, symbol="SPY"), prose
    assert return_cited("the market gained ~17% in the window", 0.165)  # 16.5: "16" or "17"
    assert not return_cited("SPY rose 16.7% over 180 days", 0.1685)  # NEGATIVE: a real miss


def test_the_market_word_must_be_in_the_same_claim_and_never_its_source() -> None:
    """A rounded figure is vouched for only by its OWN claim's words — not the next claim's, not a
    claim's ``source_ref`` (which names the benchmark by construction)."""
    split = _doc("Operating margins expanded to 17% on mix.",
                 "The benchmark trailed the sector over the window.")
    assert moved_cited_returns(_mech(market=0.1689, rel=0.1, bench_ret=0.1),
                               _mech(market=0.1989, rel=0.1, bench_ret=0.1), split) == []
    sourced = {"synthesis": {"bear_points": [
        {"claim": "Operating margins expanded to 17% on mix.", "cited": True,
         "source_ref": "EOD SPY 180d to 2026-09-22 (cap-band) — benchmark context"}]}}
    assert moved_cited_returns(_mech(market=0.1689, rel=0.1, bench_ret=0.1),
                               _mech(market=0.1989, rel=0.1, bench_ret=0.1), sourced) == []
    together = _doc("Margins expanded while the benchmark rose 17% over the window.")
    assert moved_cited_returns(_mech(market=0.1689, rel=0.1, bench_ret=0.1),
                               _mech(market=0.1989, rel=0.1, bench_ret=0.1), together)
