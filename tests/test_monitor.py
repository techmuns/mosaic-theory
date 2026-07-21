"""Position monitor — the spread math (incl. the AVOID sign), cap-band assignment, freshness.

These pin the three things that would silently corrupt the measurement: an AVOID leg contributing
with the wrong sign (the whole point of the spread), a cap-band edge slipping a name onto the
wrong yardstick, and a freshness check that fails to flag a print the record never read.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from vinci import monitor as mon

ROOT = Path(__file__).resolve().parents[1]


def _row(ticker: str, verdict: str, *, pos: float, bench: float,
         entry: date = date(2026, 1, 1), now: date = date(2026, 3, 1),
         horizon: int = 180) -> mon.PositionRow:
    """A leg whose position return is ``pos`` and benchmark return ``bench`` (both fractions)."""
    return mon.position_row(
        ticker=ticker, verdict=verdict, sector=None, entry_price=100.0, entry_date=entry,
        current_price=100.0 * (1 + pos), current_date=now, benchmark="IWM",
        benchmark_entry=100.0, benchmark_now=100.0 * (1 + bench), horizon_days=horizon)


def test_cap_bands_assign_the_stated_benchmarks_including_the_edges() -> None:
    """The band table is a design constant — pin every boundary. Edges are EXCLUSIVE upper
    bounds: exactly $4B is MID, not small (a name sitting on the edge must land somewhere
    deterministic, not on whichever comparison the code happened to use)."""
    assert mon.benchmark_for_cap(1e9)[0] == "IWM"
    assert mon.benchmark_for_cap(mon.CAP_BAND_SMALL_MAX - 1)[0] == "IWM"
    assert mon.benchmark_for_cap(mon.CAP_BAND_SMALL_MAX)[0] == "MDY"      # edge → mid
    assert mon.benchmark_for_cap(10e9)[0] == "MDY"
    assert mon.benchmark_for_cap(mon.CAP_BAND_MID_MAX - 1)[0] == "MDY"
    assert mon.benchmark_for_cap(mon.CAP_BAND_MID_MAX)[0] == "SPY"        # edge → large
    assert mon.benchmark_for_cap(500e9)[0] == "SPY"
    # a missing/zero cap must FAIL, never default to a yardstick nobody chose
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError, match="cap must be > 0"):
            mon.benchmark_for_cap(bad)


def test_avoid_leg_sign_convention_pays_into_the_spread() -> None:
    """THE measurement pin. An AVOID that FALLS against its benchmark must make the spread MORE
    positive — being right about a terminal decline pays exactly like being right about an
    overshoot. Inverting this sign would silently reverse the fund's headline number."""
    buy = _row("BUY1", "BUY", pos=0.10, bench=0.02)          # +8pp excess
    avoid_right = _row("AV1", "AVOID_TERMINAL", pos=-0.20, bench=0.02)   # −22pp excess
    s = mon.compute_spread([buy, avoid_right])
    assert s.buy_mean_excess == pytest.approx(0.08)
    assert s.avoid_mean_excess == pytest.approx(-0.22)
    assert s.spread == pytest.approx(0.30)                   # 0.08 − (−0.22) = +0.30
    # and the mirror: an AVOID that RISES against its benchmark must SHRINK the spread
    avoid_wrong = _row("AV2", "AVOID_TERMINAL", pos=0.20, bench=0.02)    # +18pp excess
    assert mon.compute_spread([buy, avoid_wrong]).spread == pytest.approx(-0.10)
    # BUY-family classification is by prefix, not equality (a future BUY_* must not count as avoid)
    assert mon.compute_spread([_row("B", "BUY_SOMETHING", pos=0.1, bench=0.0),
                               avoid_right]).buy_n == 1


def test_spread_is_none_not_zero_when_a_leg_is_empty() -> None:
    """A missing side means NOT MEASURABLE. Reporting 0.0 would read as "no edge" — the exact
    fabrication the fund refuses."""
    only_buys = mon.compute_spread([_row("B1", "BUY", pos=0.1, bench=0.0)])
    assert only_buys.spread is None and only_buys.avoid_mean_excess is None
    assert only_buys.undefined_reason and "AVOID" in only_buys.undefined_reason
    only_avoids = mon.compute_spread([_row("A1", "AVOID_TERMINAL", pos=-0.1, bench=0.0)])
    assert only_avoids.spread is None and "BUY" in (only_avoids.undefined_reason or "")
    assert mon.compute_spread([]).spread is None


def test_position_row_math_and_resolution() -> None:
    r = mon.position_row(ticker="X", verdict="BUY", sector="Industrials", entry_price=50.0,
                         entry_date=date(2026, 1, 1), current_price=55.0,
                         current_date=date(2026, 2, 1), benchmark="MDY", benchmark_entry=200.0,
                         benchmark_now=204.0, horizon_days=180)
    assert r.position_return == pytest.approx(0.10)
    assert r.benchmark_return == pytest.approx(0.02)
    assert r.excess == pytest.approx(0.08)
    assert r.days_elapsed == 31 and r.horizon_date == date(2026, 6, 30) and not r.resolved
    # resolved only ON/after the horizon date — the pre-registered read
    at_horizon = mon.position_row(ticker="X", verdict="BUY", sector=None, entry_price=50.0,
                                  entry_date=date(2026, 1, 1), current_price=55.0,
                                  current_date=date(2026, 6, 30), benchmark="MDY",
                                  benchmark_entry=200.0, benchmark_now=204.0, horizon_days=180)
    assert at_horizon.resolved
    # a zero/absent base price must fail loud, never produce a return off a fabricated base
    with pytest.raises(ValueError, match="must be > 0"):
        mon.position_row(ticker="X", verdict="BUY", sector=None, entry_price=0.0,
                         entry_date=date(2026, 1, 1), current_price=1.0,
                         current_date=date(2026, 2, 1), benchmark="IWM", benchmark_entry=1.0,
                         benchmark_now=1.0, horizon_days=180)


def test_last_evidence_date_prefers_a_later_amendment() -> None:
    """The record's evidence date is the LATEST of its underwrite date and any visible
    ``[amended YYYY-MM-DD …]`` tag — otherwise a record amended after a print would be judged
    stale against the print it had already read."""
    rec = {"underwrite_date": "2026-07-19",
           "scenarios": {"base": {"reason": "x [amended 2026-07-21 pre-verdict: guidance] y"},
                         "bull": {"reason": "no tag"}}}
    d, src = mon.last_evidence_date(rec)
    assert d == date(2026, 7, 21) and src == "base reason amendment"
    # no amendment → the underwrite date itself
    assert mon.last_evidence_date({"underwrite_date": "2026-07-19"})[0] == date(2026, 7, 19)
    # an EARLIER amendment never moves the date backwards
    older = {"underwrite_date": "2026-07-19",
             "scenarios": {"base": {"reason": "[amended 2026-01-01 x]"}}}
    assert mon.last_evidence_date(older)[0] == date(2026, 7, 19)
    # a record stating no date at all → (None, None), never a guessed today
    assert mon.last_evidence_date({}) == (None, None)


def test_freshness_flags_an_unread_print_and_never_adjudicates_a_trigger() -> None:
    """A filing NEWER than the record's evidence sets unread_print — a FLAG. The row carries the
    triggers verbatim and no fired/not-fired judgement anywhere (the machine surfaces; the human
    concludes)."""
    rec = {"underwrite_date": "2026-07-10",
           "verdict": {"reunderwrite_triggers": ["Quest ≤ 0% two quarters", "guidance cut"]}}
    filings = [("10-Q", date(2026, 5, 1), "acc-old"), ("8-K", date(2026, 7, 15), "acc-new")]
    row = mon.freshness_row(ticker="T", verdict="BUY", record=rec, filings=filings,
                            today=date(2026, 7, 21))
    assert row.unread_print is True
    assert row.newer_filings == ["8-K 2026-07-15 acc acc-new"]      # only the newer one
    assert row.triggers == ["Quest ≤ 0% two quarters", "guidance cut"]
    # NO adjudication anywhere in the model: the row may FLAG (unread_print) but must carry no
    # field claiming a trigger fired/passed — that judgement is the human's, never the machine's
    assert not [f for f in mon.FreshnessRow.model_fields
                if any(w in f for w in ("fired", "breach", "verdict_on", "adjudic"))]
    # NEG: nothing newer than the evidence → current, no flag
    fresh = mon.freshness_row(ticker="T", verdict="BUY", record={"underwrite_date": "2026-07-20"},
                              filings=filings, today=date(2026, 7, 21))
    assert fresh.unread_print is False and fresh.newer_filings == []


def test_next_expected_print_is_an_estimate_from_the_filers_own_cadence() -> None:
    today = date(2026, 7, 21)
    nxt, basis = mon.next_expected_print(
        [date(2025, 8, 5), date(2025, 11, 4), date(2026, 2, 3), date(2026, 5, 5)], today=today)
    assert nxt == date(2026, 8, 5)                     # 2025-08-05 + 365d, the next one ahead
    assert basis and "ESTIMATE" in basis               # labeled, never presented as evidence
    assert mon.next_expected_print([], today=today) == (None, None)


def test_committed_assignments_supersede_the_ledger_and_reproduce_their_own_caps() -> None:
    """The committed artifact is the yardstick of record. Re-derive each band from the row's OWN
    stamped inputs — a hand-edited benchmark that no longer matches its cap fails here."""
    asg = mon.read_assignments(ROOT)
    if not asg:
        pytest.skip("no committed benchmark assignments yet")
    ledger = [json.loads(ln) for ln
              in (ROOT / "data" / "snapshots" / "decision_ledger.jsonl").read_text().splitlines()
              if ln.strip()]
    assert {r["ticker"] for r in ledger} <= set(asg), "every ledger leg needs an assignment"
    for t, a in asg.items():
        assert a.cap_at_entry_usd == pytest.approx(a.entry_price * a.shares)
        assert (a.benchmark, a.band) == mon.benchmark_for_cap(a.cap_at_entry_usd)
        assert a.shares_source.strip(), f"{t}: share count with no source"
        row = next(r for r in ledger if r["ticker"] == t)
        assert a.entry_price == row["entry_price"] and \
            a.entry_date.isoformat() == row["entry_price_as_of"]   # assigned AT ENTRY, not now


def test_it_sector_resolves_industrials_not_other() -> None:
    """The 2026-07-21 family fix: SIC major group 87 (engineering/accounting/research/management
    services) fell through to "Other", mislabelling the IT ledger leg. Pinned at the FAMILY
    level — every 87xx name, not a per-name special case."""
    from vinci.sectors import sector_for_sic

    assert sector_for_sic("8741") == "Industrials"     # IT / Gartner — management services
    for sic in ("8711", "8721", "8731", "8742", "8748"):
        assert sector_for_sic(sic) == "Industrials", sic
    # the ledger row itself is NEVER mutated — it keeps whatever was frozen at log time
    ledger = (ROOT / "data" / "snapshots" / "decision_ledger.jsonl").read_text()
    it_row = next(json.loads(ln) for ln in ledger.splitlines()
                  if ln.strip() and json.loads(ln)["ticker"] == "IT")
    assert json.loads(it_row["payload"])["sector"] == "Other", (
        "the frozen ledger row must keep its logged sector — the fix is forward, at display")


def test_card_shows_both_ratios_and_derives_implied_odds_node() -> None:
    """The two display changes, rendered end-to-end through the REAL card on committed data.

    Both ratios must be LABELED and distinct (the underwrite's, and the one the human accepted at
    entry — IT's diverge, 7.04 vs 6.69, because price moved between underwrite and log). The
    implied-odds line must be DERIVED from the card's own legs at the committed mark, and must
    vanish entirely when there is no mark — a spot the repo cannot reproduce is never shown."""
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    card_path = ROOT / "frontend" / "scenarios" / "IT.json"
    if "ratioAtEntry" not in json.loads(card_path.read_text()).get("verdict", {}):
        pytest.skip("committed card predates the entry-ratio emit")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const url = pathToFileURL(path.resolve("frontend/views/shared/uw-card.js")).href;
const { uwCard } = await import(url);
const card = JSON.parse(readFileSync("frontend/scenarios/IT.json"));
const snap = JSON.parse(readFileSync("frontend/monitor/index.json"));
const mon = JSON.parse(readFileSync(`frontend/monitor/${snap.latest}.json`));
const mark = mon.rows.find((r) => r.ticker === "IT");
const withMark = uwCard(card, { mark });
const noMark = uwCard(card, {});
const base = card.scenarios.find((s) => s.name === "base").valuePerShare;
const bear = card.scenarios.find((s) => s.name === "bear").valuePerShare;
const want = Math.round(((base - mark.current_price) / (base - bear)) * 100);
// TOKEN ANCHORS re-pointed for the tear-sheet masthead (merged after #165): the two ratios live
// in SEPARATE LABELED CELLS — the underwrite's in the Reward:risk cell (sub "at underwrite"),
// the accepted one in the Entry cell beside its frozen price. Same invariant, new home.
const entryRatioStr = card.verdict.ratioAtEntry.toFixed(2) + " : 1";
const bothRatios = (h) => h.includes("at underwrite")
  && /uw-stat-lab">Entry</.test(h) && h.includes(entryRatioStr);
console.log(JSON.stringify({
  underwriteLabeled: withMark.includes("at underwrite"),
  entryLabeled: /uw-stat-lab">Entry</.test(withMark) && withMark.includes(entryRatioStr),
  entryRatio: card.verdict.ratioAtEntry, underwriteRatio: card.ratio,
  oddsShown: withMark.includes("Market-implied bear weight"),
  oddsValueMatchesDerivation: withMark.includes(`<b>${want}%</b>`),
  notAForecast: withMark.includes("not a forecast"),
  noMarkNoOdds: !noMark.includes("Market-implied bear weight"),
  noMarkKeepsRatios: bothRatios(noMark),
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver], capture_output=True,
                         text=True, check=True, cwd=ROOT)
    res = json.loads(out.stdout)
    assert res["underwriteLabeled"] and res["entryLabeled"], res
    assert res["entryRatio"] != res["underwriteRatio"], (
        "IT's accepted ratio differs from the underwrite's — showing one number would misreport it")
    assert res["oddsShown"] and res["oddsValueMatchesDerivation"] and res["notAForecast"], res
    assert res["noMarkNoOdds"], "no committed mark → no odds line (never an invented spot)"
    assert res["noMarkKeepsRatios"], "the frozen ratios must render with or without a mark"


def test_monitor_mirror_is_emitted_for_the_frontend() -> None:
    """build.py mirrors the committed monitor history so the browser reads a DATED, committed
    mark — the frontend must never fetch a live price it cannot reproduce."""
    idx = ROOT / "frontend" / "monitor" / "index.json"
    if not idx.exists():
        pytest.skip("no monitor history committed yet")
    data = json.loads(idx.read_text())
    assert data["latest"] in data["days"]
    snap = json.loads((ROOT / "frontend" / "monitor" / f"{data['latest']}.json").read_text())
    assert snap["rows"] and snap["spread"] and snap["price_basis"]
    src = (ROOT / "frontend" / "views" / "shared" / "decision-log.js").read_text()
    assert "getMonitor" in src and "fetch(" not in src, (
        "the view must read the committed snapshot via the shared loader, never fetch prices")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
