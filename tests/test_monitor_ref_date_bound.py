"""A monitor day reads nothing dated after itself (2026-10-11).

OBSERVED: re-running `vinci monitor --ref 2026-09-22` on 2026-10-11 wrote IT's 2026-10-08 8-K and
WERN's 2026-10-06 and 2026-10-08 8-Ks into the 09-22 day as unread prints — EDGAR answers with
everything filed up to the call. The same re-cut carried three more inputs past the day: evidence
dates from records amended or underwritten later (the committed 2026-07-20 day already holds three,
cut on the 21st), a freshness set drawn from the whole ledger (GOOGL, entered 2026-08-14, got a BUY
row on 07-20), and — on a weekend `--ref` — deadlines and a prior day dated after the session the
file is named for.

The failure was a WRITTEN ARTIFACT, so the bound is pinned through the real command over the real
committed ledger (TEST-LAYER RULE); the record and filing fixtures are frozen copies of the real
IT / WERN / GOOGL / EPAM shapes, never the living `scenarios/` files.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci import monitor as mon

ROOT = Path(__file__).resolve().parents[1]

# --- frozen real shapes ----------------------------------------------------------------------
#: The records as the committed days read them: IT's evidence is its 2026-07-22 amendments,
#: WERN's its 2026-07-21 one (both values the committed 2026-09-22 day carries).
IT_REC: dict[str, Any] = {
    "ticker": "IT", "underwrite_date": "2026-07-20",
    "scenarios": {"base": {"reason": "x [amended 2026-07-22 Q2 print] y"},
                  "bear": {"reason": "x [amended 2026-07-22 Q2 print] y"}, "bull": {"reason": "z"}},
    "verdict": {"status": "watch", "reunderwrite_triggers": ["contract value turns negative"]}}
WERN_REC: dict[str, Any] = {
    "ticker": "WERN", "underwrite_date": "2026-07-19",
    "scenarios": {"bull": {"reason": "x [amended 2026-07-21 dedicated margin] y"}},
    "verdict": {"status": "watch", "reunderwrite_triggers": ["spot pulls to ~28-30"]}}
#: Ledgered 2026-08-14; its record is `confirmed`, so it reaches the freshness set ONLY through
#: the ledger — the path the as-of bound governs.
GOOGL_REC: dict[str, Any] = {
    "ticker": "GOOGL", "underwrite_date": "2026-09-01",
    "verdict": {"status": "confirmed", "reunderwrite_triggers": ["search share loss"]}}
#: A watch record underwritten after 2026-07-20 — every evidence date it states postdates that day.
EPAM_REC: dict[str, Any] = {
    "ticker": "EPAM", "underwrite_date": "2026-08-07",
    "verdict": {"status": "watch", "reunderwrite_triggers": ["deals slip again"]}}

#: The filings EDGAR returned on 2026-10-11 for the two names, accessions verbatim.
FILINGS: dict[str, list[tuple[str, date, str]]] = {
    "IT": [("10-Q", date(2026, 8, 4), "0000749251-26-000245"),
           ("8-K", date(2026, 8, 4), "0000749251-26-000243"),
           ("8-K", date(2026, 10, 8), "0001193125-26-417937")],
    "WERN": [("8-K", date(2026, 7, 28), "0000793074-26-000129"),
             ("8-K", date(2026, 8, 5), "0000793074-26-000132"),
             ("10-Q", date(2026, 8, 7), "0000793074-26-000140"),
             ("8-K", date(2026, 8, 10), "0000793074-26-000144"),
             ("8-K", date(2026, 8, 24), "0000793074-26-000154"),
             ("8-K", date(2026, 10, 6), "0000793074-26-000156"),
             ("8-K", date(2026, 10, 8), "0000793074-26-000159")],
}
DAY = date(2026, 9, 22)


def _dates(filings: list[str]) -> list[date]:
    return [date.fromisoformat(f.split()[1]) for f in filings]


# --- the pure function ------------------------------------------------------------------------
def test_a_filing_after_the_day_is_not_an_unread_print() -> None:
    """⊖ IT's 10-08 8-K and WERN's 10-06/10-08 8-Ks are not on the 09-22 day; ⊕ every filing on or
    before it still is, in order; ⊕ the same filings ARE read on a day after them — the bound
    moves with the day rather than dropping a form."""
    it = mon.freshness_row(ticker="IT", verdict="BUY", record=IT_REC, filings=FILINGS["IT"],
                           today=DAY)
    assert it.newer_filings == ["10-Q 2026-08-04 acc 0000749251-26-000245",
                                "8-K 2026-08-04 acc 0000749251-26-000243"]
    wern = mon.freshness_row(ticker="WERN", verdict="watch", record=WERN_REC,
                             filings=FILINGS["WERN"], today=DAY)
    assert max(_dates(wern.newer_filings)) == date(2026, 8, 24) and len(wern.newer_filings) == 5
    later = mon.freshness_row(ticker="WERN", verdict="watch", record=WERN_REC,
                              filings=FILINGS["WERN"], today=date(2026, 10, 9))
    assert _dates(later.newer_filings)[-2:] == [date(2026, 10, 6), date(2026, 10, 8)]
    # ON the day is knowable on the day — the bound is `>`, not `>=`
    on_day = mon.freshness_row(ticker="WERN", verdict="watch", record=WERN_REC,
                               filings=FILINGS["WERN"], today=date(2026, 10, 8))
    assert date(2026, 10, 8) in _dates(on_day.newer_filings)


def test_the_next_print_estimate_reads_only_filings_on_or_before_the_day() -> None:
    """The cadence estimate is a schedule, and a schedule built from a filing that has not happened
    is lookahead too: ⊖ a lone post-day filing yields no estimate; ⊕ the same filing on a later
    day yields its +365d."""
    after = [("8-K", date(2026, 10, 8), "0001193125-26-417937")]
    row = mon.freshness_row(ticker="IT", verdict="BUY", record=IT_REC, filings=after, today=DAY)
    assert (row.next_expected_print, row.next_expected_basis) == (None, None)
    row = mon.freshness_row(ticker="IT", verdict="BUY", record=IT_REC, filings=after,
                            today=date(2026, 10, 9))
    assert row.next_expected_print == date(2027, 10, 8)


def test_evidence_dated_after_the_day_is_not_that_days_evidence() -> None:
    """⊖ WERN's 07-21 amendment is not evidence on 07-20 — its underwrite date is; ⊖ EPAM's
    record, underwritten 08-07, states NO evidence on 07-20; ⊕ unbounded, the latest date is
    returned exactly as before; ⊕ `evidence_after` names what the bound dropped, oldest first."""
    july20 = date(2026, 7, 20)
    assert mon.last_evidence_date(WERN_REC, as_of=july20) == (date(2026, 7, 19), "underwrite_date")
    assert mon.evidence_after(WERN_REC, as_of=july20) == [
        (date(2026, 7, 21), "bull reason amendment")]
    assert mon.last_evidence_date(EPAM_REC, as_of=july20) == (None, None)
    assert mon.evidence_after(EPAM_REC, as_of=july20) == [(date(2026, 8, 7), "underwrite_date")]
    assert mon.last_evidence_date(WERN_REC) == (date(2026, 7, 21), "bull reason amendment")
    assert mon.last_evidence_date(IT_REC, as_of=date(2026, 7, 22))[0] == date(2026, 7, 22)
    assert mon.evidence_after(IT_REC, as_of=DAY) == []


# --- through the real command -----------------------------------------------------------------
def _tickers_needing_bars() -> set[str]:
    led = [json.loads(ln) for ln in (ROOT / "data/snapshots/decision_ledger.jsonl").read_text()
           .splitlines() if ln.strip()]
    asg = json.loads((ROOT / "data/monitor/benchmark_assignments.json").read_text())
    return ({str(r["ticker"]) for r in led}
            | {str(v["benchmark"]) for v in asg.values() if isinstance(v, dict)})


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ref: str,
         records: list[dict[str, Any]], prior: dict[str, dict[str, Any]] | None = None,
         ) -> dict[str, Any]:
    """`vinci monitor --ref <ref>` over the real committed ledger, securities and assignments, with
    frozen records, the real filing shapes served for EDGAR, and a flat price on every weekday
    (empty on weekends, so a weekend `ref` resolves to Friday as it does live)."""
    from vinci import cli
    for rel in ("data/snapshots/decision_ledger.jsonl", "data/snapshots/securities.jsonl",
                "data/monitor/benchmark_assignments.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    (tmp_path / "scenarios").mkdir()
    for rec in records:
        (tmp_path / "scenarios" / f"{rec['ticker']}.json").write_text(json.dumps(rec))
    for name, day in (prior or {}).items():
        (tmp_path / "data/monitor" / f"{name}.json").write_text(json.dumps(day))

    bars = {t: SimpleNamespace(close=100.0) for t in _tickers_needing_bars()}
    sec = [json.loads(ln) for ln in (ROOT / "data/snapshots/securities.jsonl").read_text()
           .splitlines() if ln.strip()]
    by_cik = {str(r["cik"]): str(r["ticker"]) for r in sec if r.get("cik")}

    class _Eod:
        @classmethod
        def from_config(cls, _cfg: object) -> _Eod:
            return cls()

        def grouped_daily(self, d: date) -> dict[str, object]:
            return {} if d.weekday() >= 5 else dict(bars)

    class _Edgar:
        @classmethod
        def from_config(cls, _cfg: object) -> _Edgar:
            return cls()

        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[SimpleNamespace]:
            return [SimpleNamespace(form=f, filing_date=d, accession=a)
                    for f, d, a in FILINGS.get(by_cik.get(str(cik), ""), [])
                    if f in forms and (since is None or d >= since)]

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "PolygonEodClient", _Eod)
    monkeypatch.setattr(cli, "EdgarClient", _Edgar)
    assert cli._cmd_monitor(argparse.Namespace(ref=ref)) == 0
    # the day the command wrote — a planted prior day carries no `spread`, a written one always does
    written = [d for p in sorted((tmp_path / "data/monitor").glob("2026-*.json"))
               if "spread" in (d := json.loads(p.read_text()))]
    assert len(written) == 1
    out: dict[str, Any] = written[0]
    return out


def _row(snap: dict[str, Any], ticker: str) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {r["ticker"]: r for r in snap["freshness"]}
    return rows[ticker]


def test_a_recut_day_writes_only_what_was_filed_by_that_day(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE OBSERVED SHAPE, END TO END. `--ref 2026-09-22` with EDGAR answering as it did on 10-11:
    ⊖ no filing after 09-22 reaches the written day; ⊕ IT's and WERN's newer filings are EXACTLY
    the committed 09-22 day's (an immutable superseded day), so the re-cut reproduces it; ⊕ GOOGL,
    ledgered 08-14, keeps its row on a day after its entry."""
    snap = _run(tmp_path, monkeypatch, "2026-09-22", [IT_REC, WERN_REC, GOOGL_REC])
    assert snap["as_of"] == "2026-09-22"
    for r in snap["freshness"]:
        assert all(d <= DAY for d in _dates(r["newer_filings"])), r["ticker"]
    committed = json.loads((ROOT / "data/monitor/2026-09-22.json").read_text())
    for t in ("IT", "WERN"):
        assert _row(snap, t)["newer_filings"] == _row(committed, t)["newer_filings"]
        assert _row(snap, t)["last_evidence_date"] == _row(committed, t)["last_evidence_date"]
    assert _row(snap, "GOOGL")["verdict"] == "BUY"
    assert not [n for n in snap["notes"] if "carries evidence dated after" in n]


def test_a_past_day_names_every_record_written_after_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`--ref 2026-07-20`: ⊖ GOOGL (ledgered 08-14) has NO freshness row, though its record sits in
    `scenarios/`; ⊖ no evidence date after 07-20 is written; ⊕ every evidence date the bound
    dropped is NAMED in the day's notes — WERN's amendment and EPAM's whole record — so a missing
    date never reads as a record that states none; ⊕ IT, ledgered ON 07-20, keeps its row."""
    snap = _run(tmp_path, monkeypatch, "2026-07-20", [IT_REC, WERN_REC, GOOGL_REC, EPAM_REC])
    day = date(2026, 7, 20)
    assert "GOOGL" not in {r["ticker"] for r in snap["freshness"]}
    assert _row(snap, "IT")["verdict"] == "BUY"
    for r in snap["freshness"]:
        ev = r["last_evidence_date"]
        assert ev is None or date.fromisoformat(ev) <= day, r["ticker"]
    assert _row(snap, "WERN")["last_evidence_date"] == "2026-07-19"
    assert _row(snap, "EPAM")["last_evidence_date"] is None
    for rec in (IT_REC, WERN_REC, EPAM_REC):
        late = mon.evidence_after(rec, as_of=day)
        assert late, rec["ticker"]
        note = next(n for n in snap["notes"] if n.startswith(f"{rec['ticker']}: scenarios/"))
        assert all(f"{src} {d}" in note for d, src in late)
    assert not [n for n in snap["notes"] if n.startswith("GOOGL: scenarios/")]


def test_a_weekend_ref_is_read_as_the_session_it_is_filed_under(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`--ref 2026-09-20` (Sunday) writes FRIDAY 2026-09-18. ⊖ a deadline on Saturday 09-19 is not
    PASSED in Friday's file; ⊕ one on Friday is; ⊖ an existing 2026-09-18 file is not read as a
    PRIOR day of itself; ⊕ the 09-16 day still is."""
    rec = {**IT_REC, "verdict": {**IT_REC["verdict"], "dated_triggers": [
        {"trigger": "Friday check", "deadline": "2026-09-18"},
        {"trigger": "Saturday check", "deadline": "2026-09-19"}]}}
    seen: list[list[str]] = []
    real = mon.freshness_row

    def _spy(**kw: Any) -> mon.FreshnessRow:
        seen.append([str(d.get("as_of")) for d in kw.get("prior_days") or []])
        return real(**kw)

    monkeypatch.setattr(mon, "freshness_row", _spy)
    prior = {"2026-09-16": {"as_of": "2026-09-16", "freshness": []},
             "2026-09-18": {"as_of": "2026-09-18", "freshness": []}}
    snap = _run(tmp_path, monkeypatch, "2026-09-20", [rec], prior=prior)
    assert snap["as_of"] == "2026-09-18"
    it = _row(snap, "IT")
    assert it["passed_trigger_deadlines"] == [
        "Friday check — deadline 2026-09-18 PASSED → re-underwrite due"]
    assert "Saturday check (by 2026-09-19)" in it["triggers"]
    assert seen and all(days == ["2026-09-16"] for days in seen)


def test_the_verdict_beside_a_row_is_the_ledgers_as_of_the_day(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """IT is a WATCH record AND was ledgered BUY on 2026-07-20. On 07-17 (Friday), before that
    entry: ⊖ its row does not read BUY — the decision did not exist; ⊕ it reads its record's
    status, as any watch name does."""
    snap = _run(tmp_path, monkeypatch, "2026-07-17", [IT_REC])
    assert snap["as_of"] == "2026-07-17"
    assert _row(snap, "IT")["verdict"] == "watch"
