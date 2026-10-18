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

#: Ledgered names for which EDGAR publishes NO SIC — the escape hatch for
#: `test_every_ledgered_name_carries_a_sic_in_the_committed_entity_master`, which would otherwise
#: be unsatisfiable for them. Empty today: the screen's `unknown_sic` gate keeps BDCs and funds out
#: of the universe, so one can only reach the ledger by a deliberate operator entry. Add a ticker
#: ONLY after confirming `resolver.sic_for(cik)` really returns None for it — never to green a
#: suite, which is what inventing a code to satisfy that pin would amount to.
NO_EDGAR_SIC: frozenset[str] = frozenset()


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


def test_freshness_panel_includes_pending_analyst_records(tmp_path: Path) -> None:
    """A record at status=pending_analyst is exactly the one that must not go stale unnoticed: the
    underwrite is RUN and the verdict is still owed, so the next print can move the decision before
    it is ever made. Previously the panel only picked up `watch`, so EPAM was invisible."""
    from vinci.cli import _FRESHNESS_STATUSES, _STATUS_LABEL, _watch_tickers

    d = tmp_path / "scenarios"
    d.mkdir()
    (d / "PEND.json").write_text(json.dumps(
        {"ticker": "PEND", "underwrite_date": "2026-07-21",
         "verdict": {"status": "pending_analyst"}}))
    (d / "WCH.json").write_text(json.dumps(
        {"ticker": "WCH", "underwrite_date": "2026-07-19", "verdict": {"status": "watch"}}))
    (d / "CONF.json").write_text(json.dumps(
        {"ticker": "CONF", "underwrite_date": "2026-07-01", "verdict": {"status": "confirmed"}}))

    picked = _watch_tickers(tmp_path)
    assert "PEND" in picked, "a pending_analyst record must reach the freshness panel"
    assert "WCH" in picked, "watch names must still be picked up"
    assert "CONF" not in picked, "a decided record is a ledger position, not a freshness watch"
    assert set(_FRESHNESS_STATUSES) == {"watch", "pending_analyst"}
    # the panel labels it in plain words, never the raw enum
    assert _STATUS_LABEL["pending_analyst"] == "verdict pending"


def test_dated_trigger_deadlines_flag_passed_windows_never_adjudicate() -> None:
    """(catalyst calendar) An analyst-DATED trigger whose deadline is on/before today lands in
    ``passed_trigger_deadlines`` as a FLAG ("… PASSED → re-underwrite due" — the window closed;
    whether the trigger FIRED stays the human's read); a future one joins the display triggers
    with its date; an unparseable analyst date is skipped here (it still renders verbatim in the
    dossier). Undated ``reunderwrite_triggers`` are untouched."""
    rec = {"underwrite_date": "2026-07-10", "verdict": {
        "reunderwrite_triggers": ["guidance cut"],
        "dated_triggers": [
            {"trigger": "Quest stalls two quarters", "deadline": "2026-07-20", "basis": "b"},
            {"trigger": "CV re-accelerates", "deadline": "2027-01-07"},
            {"trigger": "bad date", "deadline": "soonish"},
        ]}}
    row = mon.freshness_row(ticker="T", verdict="BUY", record=rec,
                            filings=[("10-Q", date(2026, 5, 1), "a")], today=date(2026, 7, 21))
    assert row.passed_trigger_deadlines == [
        "Quest stalls two quarters — deadline 2026-07-20 PASSED → re-underwrite due"]
    assert "guidance cut" in row.triggers
    assert "CV re-accelerates (by 2027-01-07)" in row.triggers
    assert not any("bad date" in t for t in row.triggers + row.passed_trigger_deadlines)


def test_every_ledgered_name_carries_a_sic_in_the_committed_entity_master() -> None:
    """THE PIN AT THE RIGHT LAYER (#464 regression, found 2026-08-31).

    `test_it_sector_resolves_industrials_not_other` above pins the MAPPING — `sector_for_sic`
    ("8741") — and it stayed green for two weeks while the input to that mapping was destroyed: a
    `vinci refresh IT NFLX` price backfill upserted Gartner un-enriched and `INSERT OR REPLACE`
    nulled its 8741. A helper pin cannot see that; only the ARTIFACT can. The monitor re-resolves
    each position's sector from THIS file on every run, so a ledgered name without a SIC here is a
    decision surface printing "Unknown" where a real sector exists.

    THIS PIN IS NOT SUBSUMED by `test_an_issuer_never_half_carries_its_sic`. Gartner's CIK owns
    exactly ONE security, so its destroyed row left no sibling to disagree with and the
    partial-hole rule was satisfied by the very row that was wrong. Single-security issuers are
    only reachable from here. Keep both.

    AND IT IS NOT ALWAYS REPAIRABLE, which the failure message has to say. EDGAR publishes NO SIC
    for BDCs and funds — 40 issuers in the committed master — so a ledgered name from that class
    would fail this pin with nothing to fetch. The honest resolution there is to record the name
    in `NO_EDGAR_SIC` below, never to invent a code to green the suite.
    """
    snaps = ROOT / "data" / "snapshots"
    sic_by_ticker = {r["ticker"]: r.get("sic") for r in
                     (json.loads(ln) for ln in
                      (snaps / "securities.jsonl").read_text().splitlines() if ln.strip())
                     if r.get("ticker")}
    ledgered = {json.loads(ln)["ticker"] for ln in
                (snaps / "decision_ledger.jsonl").read_text().splitlines() if ln.strip()}
    assert ledgered, "no ledgered names — this pin would be vacuous"
    unresolved = sorted(t for t in ledgered - NO_EDGAR_SIC
                        if mon.sector_for_display(sic_by_ticker.get(t)) is None)
    assert not unresolved, (
        f"ledgered name(s) with NO SIC in the entity master: {unresolved}. The monitor will print "
        f"an UNRESOLVED sector for them. If EDGAR publishes a SIC, the row lost it — repair it "
        f"(`scripts/backfill_entity_master_sic.py`). If EDGAR publishes NONE (a BDC or fund), add "
        f"the ticker to NO_EDGAR_SIC above. Never invent a code to green this.")


def test_it_row_still_carries_the_87xx_sic_the_sector_is_read_from() -> None:
    """The repaired row, pinned at the FAMILY level — the same discipline the mapping test states
    ("never a per-name special case"), so an in-family EDGAR re-classification does not rot it
    while a NULL still fails."""
    sec = next(json.loads(ln) for ln in
               (ROOT / "data" / "snapshots" / "securities.jsonl").read_text().splitlines()
               if ln.strip() and json.loads(ln)["ticker"] == "IT")
    assert (sec["sic"] or "").startswith("87"), f"IT's SIC is {sec['sic']!r}, not the 87xx family"
    assert mon.sector_for_display(sec["sic"]) == "Industrials"


def test_an_absent_sic_is_reported_as_absent_never_as_a_resolved_sector() -> None:
    """ABSENT ≠ RESOLVED — the display half of the same incident.

    `resolve_label(None).sector` answers "Unknown", and so does a PRESENT-but-unmappable SIC, so
    the old note said "IT: sector re-resolved to Unknown for display" — a broken lookup wearing a
    resolved label. Absence now returns None (the artifact records that nothing was read) and says
    so in words that cannot be mistaken for a reading."""
    for absent in (None, "", "   "):
        assert mon.sector_for_display(absent) is None
        note = mon.sector_note(ticker="IT", sic=absent, frozen_sector="Other")
        assert note is not None
        assert "ABSENT" in note and "UNRESOLVED" in note
        # the old note's exact claim shape — "sector re-resolved to <label>" — must not appear
        assert "sector re-resolved to" not in note, (
            "an absence must never be phrased as a resolution")
        assert "Other" in note, "the frozen ledger value is still surfaced, never rewritten"

    # a PRESENT SIC keeps its one meaning, and the forward-only correction note is unchanged
    assert mon.sector_for_display("8741") == "Industrials"
    live = mon.sector_note(ticker="IT", sic="8741", frozen_sector="Other")
    assert live is not None and "re-resolved to Industrials" in live and "ABSENT" not in live
    # agreement between frozen and live says nothing — no note
    assert mon.sector_note(ticker="IT", sic="8741", frozen_sector="Industrials") is None


# --- (2026-09-22) a failed price fetch is not a holiday ------------------------------------------
_GROUPED = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{}"


def _fetcher(bars: dict[date, dict[str, float]], failing: set[date]):  # type: ignore[no-untyped-def]
    from vinci.netcache import HttpError

    def fetch(d: date) -> dict[str, float]:
        if d in failing:  # the observed shape: a 429 whose retries ran out
            raise HttpError(f"Exhausted retries for {_GROUPED.format(d)}")
        return bars.get(d, {})
    return fetch


def test_a_failed_price_fetch_stops_the_run_and_never_moves_the_date() -> None:
    """OBSERVED 2026-09-22: a Polygon 429 exhausted its retries on 09-16 and 09-15; the monitor
    filed both as holidays and wrote 2026-09-14.json for `--ref 2026-09-16`, two sessions early.
    ⊖ a failed fetch raises, naming the date — it never steps back; ⊕ a real holiday (an EMPTY
    day) still steps back to the session before it; ⊖ a week of empty days is still refused."""
    bars = {date(2026, 9, 14): {"SPY": 1.0}, date(2026, 9, 15): {"SPY": 2.0}}
    with pytest.raises(RuntimeError, match="2026-09-16.*not a holiday"):
        mon.session_on_or_before(_fetcher(bars, {date(2026, 9, 16), date(2026, 9, 15)}),
                                 date(2026, 9, 16), {})
    assert mon.session_on_or_before(_fetcher(bars, set()), date(2026, 9, 16), {}) == (
        date(2026, 9, 15), {"SPY": 2.0})
    with pytest.raises(RuntimeError, match="no EOD session found within 7 days"):
        mon.session_on_or_before(_fetcher({}, set()), date(2026, 9, 16), {})


def test_the_monitor_command_writes_no_snapshot_when_the_price_source_fails(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-LAYER RULE — the failure was a WRITTEN ARTIFACT (a snapshot dated two sessions early),
    so it is pinned through the real command over the real committed ledger: with the price source
    throttled on the reference day, `vinci monitor` raises and the monitor directory gains nothing
    — above all no earlier-dated day."""
    import argparse
    import shutil

    from vinci import cli
    from vinci.netcache import HttpError
    for rel in ("data/snapshots/decision_ledger.jsonl", "data/snapshots/securities.jsonl",
                "data/monitor/benchmark_assignments.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)

    class _Throttled:
        @classmethod
        def from_config(cls, _cfg: object) -> _Throttled:
            return cls()

        def grouped_daily(self, d: date) -> dict[str, object]:
            raise HttpError(f"Exhausted retries for {_GROUPED.format(d)}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "PolygonEodClient", _Throttled)
    monitor = tmp_path / "data" / "monitor"
    before = sorted(p.name for p in monitor.iterdir())
    # A past `--ref` into the book is refused before any fetch since #708, so the observed
    # 2026-09-16 shape now reaches the price source as the analysis re-cut it would be today —
    # through `--out` — and must still write nothing anywhere.
    scratch = tmp_path / "scratch"
    with pytest.raises(RuntimeError, match="2026-09-16.*not a holiday"):
        cli._cmd_monitor(argparse.Namespace(ref="2026-09-16", out=str(scratch)))
    assert sorted(p.name for p in monitor.iterdir()) == before == ["benchmark_assignments.json"]
    assert not (scratch / "data" / "monitor").exists() or not any(
        (scratch / "data" / "monitor").iterdir())
