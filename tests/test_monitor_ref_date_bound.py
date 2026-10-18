"""A monitor day reads nothing dated after itself (2026-10-11).

OBSERVED: re-running `vinci monitor --ref 2026-09-22` on 2026-10-11 wrote IT's 2026-10-08 8-K and
WERN's 2026-10-06 and 2026-10-08 8-Ks into the 09-22 day as unread prints — EDGAR answers with
everything filed up to the call. The same re-cut carried more inputs past the day: evidence dates
from records amended or underwritten later (the committed 2026-07-20 day already holds three, cut
on the 21st), a freshness set drawn from the whole ledger (GOOGL, entered 2026-08-14, got a BUY row
on 07-20; IT, closed 07-21, read BUY ever after), and — on a weekend `--ref` — deadlines and a prior
day dated after the session the file is named for.

TWO ANCHORS (review of #707): a row is FILED under the session (`now_date`: deadlines, prior days)
and READS through the date asked for (`ref`: filings, evidence), so a routine run before today's
close still flags this morning's 8-K while a re-cut of a past day reads only what was filed by then.

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
#: WERN's its 2026-07-21 one (both values the committed 2026-09-22 day carries). Both are `watch`
#: records; IT is ALSO ledgered BUY on 2026-07-20 and that decision was closed on 2026-07-21.
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


def _ledger() -> list[dict[str, Any]]:
    return [json.loads(ln) for ln in (ROOT / "data/snapshots/decision_ledger.jsonl").read_text()
            .splitlines() if ln.strip()]


# --- the pure functions -----------------------------------------------------------------------
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


def test_the_row_reads_through_its_horizon_and_is_filed_under_its_session() -> None:
    """The two anchors, in the pure function: `known_through` past `today` ⊕ reads the later
    filing, ⊖ yet a deadline between the two is NOT passed — it is judged on the session."""
    rec = {**WERN_REC, "verdict": {**WERN_REC["verdict"], "dated_triggers": [
        {"trigger": "Monday check", "deadline": "2026-10-12"}]}}
    row = mon.freshness_row(ticker="WERN", verdict="watch", record=rec, filings=FILINGS["WERN"],
                            today=date(2026, 10, 7), known_through=date(2026, 10, 12))
    assert date(2026, 10, 8) in _dates(row.newer_filings)
    assert row.passed_trigger_deadlines == []
    assert "Monday check (by 2026-10-12)" in row.triggers


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
    returned exactly as before; ⊕ the row CARRIES what the bound dropped, typed, oldest first."""
    july20 = date(2026, 7, 20)
    assert mon.last_evidence_date(WERN_REC, as_of=july20) == (date(2026, 7, 19), "underwrite_date")
    assert mon.last_evidence_date(EPAM_REC, as_of=july20) == (None, None)
    assert mon.last_evidence_date(WERN_REC) == (date(2026, 7, 21), "bull reason amendment")
    assert mon.last_evidence_date(IT_REC, as_of=date(2026, 7, 22))[0] == date(2026, 7, 22)
    wern = mon.freshness_row(ticker="WERN", verdict="watch", record=WERN_REC, filings=[],
                             today=july20)
    assert wern.evidence_after_day == [
        mon.EvidenceDate(on=date(2026, 7, 21), source="bull reason amendment")]
    epam = mon.freshness_row(ticker="EPAM", verdict="watch", record=EPAM_REC, filings=[],
                             today=july20)
    assert (epam.last_evidence_date, epam.evidence_after_day) == (
        None, [mon.EvidenceDate(on=date(2026, 8, 7), source="underwrite_date")])
    it = mon.freshness_row(ticker="IT", verdict="BUY", record=IT_REC, filings=[], today=DAY)
    assert it.evidence_after_day == []


def test_an_unreadable_evidence_date_is_refused_by_name() -> None:
    """`2026-02-30` matches the amendment tag and is no date: ⊖ it never parses to a guess;
    ⊕ the refusal names the record and the field, so the caller can drop THAT row loudly."""
    bad = {**WERN_REC, "scenarios": {"bull": {"reason": "x [amended 2026-02-30 typo] y"}}}
    with pytest.raises(mon.UnreadableEvidenceDateError,
                       match=r"WERN: bull reason amendment '2026-02-30'"):
        mon.freshness_row(ticker="WERN", verdict="watch", record=bad, filings=[], today=DAY)
    with pytest.raises(mon.UnreadableEvidenceDateError, match=r"WERN: underwrite_date '2026-7-19'"):
        mon.last_evidence_date({**WERN_REC, "underwrite_date": "2026-7-19"})


def test_the_live_verdict_is_the_newest_open_decision_on_the_day() -> None:
    """Over the REAL ledger: ⊖ IT, ledgered 07-20 and closed 07-21, has no live verdict after its
    close; ⊕ it is BUY on 07-20; ⊖ GOOGL has none before its 08-14 entry. And with SMPL's real
    08-04 re-entry carried at a different verdict (the shape a reversal would take): ⊕ the newest
    open decision wins after 08-04, ⊕ the old one before it, while still open."""
    led = _ledger()
    assert mon.live_verdicts(led, as_of=date(2026, 7, 20)) == {
        "IT": "BUY", "SMPL": "BUY", "VRRM": "AVOID_TERMINAL"}
    on = mon.live_verdicts(led, as_of=DAY)
    assert "IT" not in on and on["GOOGL"] == "BUY" and on["SMPL"] == "BUY"
    reversed_ = [({**r, "verdict": "AVOID_TERMINAL"}
                  if r.get("entry_id") == "V-SMPL-screen2-20260729" else r) for r in led]
    assert mon.live_verdicts(reversed_, as_of=DAY)["SMPL"] == "AVOID_TERMINAL"
    assert mon.live_verdicts(reversed_, as_of=date(2026, 7, 21))["SMPL"] == "BUY"
    # and with the 07-20 decision NEVER closed (its real close row dropped), BOTH are open on
    # 09-22: ⊕ the newer one still wins — open-ness alone does not pick between two
    never_closed = [r for r in reversed_ if r.get("entry_id") != "C-SMPL-screen2-20260706"]
    assert len([r for r in mon.decisions_as_of(never_closed, as_of=DAY)
                if r["ticker"] == "SMPL"]) == 2
    assert mon.live_verdicts(never_closed, as_of=DAY)["SMPL"] == "AVOID_TERMINAL"


# --- through the real command -----------------------------------------------------------------
def _tickers_needing_bars() -> set[str]:
    asg = json.loads((ROOT / "data/monitor/benchmark_assignments.json").read_text())
    return ({str(r["ticker"]) for r in _ledger()}
            | {str(v["benchmark"]) for v in asg.values() if isinstance(v, dict)})


def _wire(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, records: list[dict[str, Any]],
          prior: dict[str, dict[str, Any]] | None = None,
          extra_filings: dict[str, list[tuple[str, date, str]]] | None = None,
          no_close: frozenset[date] = frozenset()) -> dict[str, int]:
    """Lay out the real committed ledger, securities and assignments under ``tmp_path`` with
    frozen records, serve the real filing shapes for EDGAR and a flat price on every weekday —
    empty on weekends and on ``no_close`` days, so a weekend or before-the-close date resolves to
    the previous session as it does live. Returns the live count of source CALLS, so a refusal can
    be shown to have fetched nothing."""
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
    served = {t: FILINGS.get(t, []) + (extra_filings or {}).get(t, [])
              for t in set(FILINGS) | set(extra_filings or {})}
    calls = {"prices": 0, "filings": 0}

    class _Eod:
        @classmethod
        def from_config(cls, _cfg: object) -> _Eod:
            return cls()

        def grouped_daily(self, d: date) -> dict[str, object]:
            calls["prices"] += 1
            return {} if d.weekday() >= 5 or d in no_close else dict(bars)

    class _Edgar:
        @classmethod
        def from_config(cls, _cfg: object) -> _Edgar:
            return cls()

        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[SimpleNamespace]:
            calls["filings"] += 1
            return [SimpleNamespace(form=f, filing_date=d, accession=a)
                    for f, d, a in served.get(by_cik.get(str(cik), ""), [])
                    if f in forms and (since is None or d >= since)]

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "PolygonEodClient", _Eod)
    monkeypatch.setattr(cli, "EdgarClient", _Edgar)
    return calls


def _written(monitor: Path) -> dict[str, Any]:
    """The one day the command wrote under ``monitor`` — a planted prior day carries no
    `spread`, a written one always does."""
    written = [d for p in sorted(monitor.glob("*.json"))
               if "spread" in (d := json.loads(p.read_text()))]
    assert len(written) == 1
    out: dict[str, Any] = written[0]
    return out


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ref: str,
         records: list[dict[str, Any]], prior: dict[str, dict[str, Any]] | None = None,
         extra_filings: dict[str, list[tuple[str, date, str]]] | None = None,
         no_close: frozenset[date] = frozenset()) -> dict[str, Any]:
    """A PAST-DAY RE-CUT: `vinci monitor --ref <ref> --out <scratch>` over the wired corpus. Since
    the review of #708 a past `--ref` is refused unless it writes to a scratch root, so the
    re-cut lands in `<scratch>/data/monitor/` while the history is still read from the book."""
    from vinci import cli
    _wire(tmp_path, monkeypatch, records, prior, extra_filings, no_close)
    scratch = tmp_path / "scratch"
    assert cli._cmd_monitor(argparse.Namespace(ref=ref, out=str(scratch))) == 0
    return _written(scratch / "data/monitor")


def _rows(snap: dict[str, Any]) -> dict[str, mon.FreshnessRow]:
    return {r["ticker"]: mon.FreshnessRow.model_validate(r) for r in snap["freshness"]}


def test_a_recut_day_writes_only_what_was_filed_by_that_day(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE OBSERVED SHAPE, END TO END. `--ref 2026-09-22` with EDGAR answering as it did on 10-11:
    ⊖ no filing after 09-22 reaches the written day; ⊕ IT's and WERN's newer filings and evidence
    dates are EXACTLY the committed 09-22 day's (an immutable superseded day); ⊕ GOOGL, ledgered
    08-14, keeps its BUY; ⊖ IT, CLOSED 07-21, no longer reads BUY — it is a watch record."""
    snap = _run(tmp_path, monkeypatch, "2026-09-22", [IT_REC, WERN_REC, GOOGL_REC])
    assert snap["as_of"] == "2026-09-22"
    rows = _rows(snap)
    for r in rows.values():
        assert all(d <= DAY for d in _dates(r.newer_filings)), r.ticker
    committed = _rows(json.loads((ROOT / "data/monitor/2026-09-22.json").read_text()))
    for t in ("IT", "WERN"):
        assert rows[t].newer_filings == committed[t].newer_filings
        assert rows[t].last_evidence_date == committed[t].last_evidence_date
    assert rows["GOOGL"].verdict == "BUY"
    assert rows["IT"].verdict == "watch"
    assert all(not r.evidence_after_day for r in rows.values())


def test_a_past_day_holds_no_record_written_after_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`--ref 2026-07-20`: ⊖ GOOGL (ledgered 08-14) has NO row, though its record sits in
    `scenarios/`; ⊖ EPAM, whose record states nothing before 08-07, has NO row — its triggers are
    all later ones — and the day says so by name; ⊕ WERN, amended after the day, keeps its row with
    its bounded date and the dropped amendment TYPED on the row, the note rendered from it; ⊕ IT,
    ledgered and still open ON 07-20, reads BUY."""
    snap = _run(tmp_path, monkeypatch, "2026-07-20", [IT_REC, WERN_REC, GOOGL_REC, EPAM_REC])
    day = date(2026, 7, 20)
    rows = _rows(snap)
    assert set(rows) == {"IT", "WERN"}
    assert rows["IT"].verdict == "BUY"
    for r in rows.values():
        assert r.last_evidence_date is not None and r.last_evidence_date <= day, r.ticker
    assert rows["WERN"].last_evidence_date == date(2026, 7, 19)
    assert rows["WERN"].evidence_after_day == [
        mon.EvidenceDate(on=date(2026, 7, 21), source="bull reason amendment")]
    for t in ("IT", "WERN"):
        assert mon.later_evidence_note(rows[t], through=day) in snap["notes"]
    epam = mon.freshness_row(ticker="EPAM", verdict="watch", record=EPAM_REC, filings=[],
                             today=day)
    assert mon.record_after_day_note(epam, through=day) in snap["notes"]


def test_a_routine_run_before_the_close_still_flags_this_mornings_filing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE REVIEW'S REGRESSION (#707 first cut). Monday 2026-10-12 has no close yet, so the day is
    filed under Friday 10-09 — and: ⊕ a Monday 07:00 8-K is still an unread print (the first cut
    hid it until Monday's file); ⊕ a record underwritten Monday morning keeps its row with no
    'after this day' note; ⊖ a deadline falling on Monday is NOT passed in Friday's file."""
    monday = date(2026, 10, 12)
    rec = {**WERN_REC, "verdict": {**WERN_REC["verdict"], "dated_triggers": [
        {"trigger": "Monday check", "deadline": "2026-10-12"}]}}
    fresh = {**EPAM_REC, "underwrite_date": "2026-10-12"}
    snap = _run(tmp_path, monkeypatch, "2026-10-12", [rec, fresh],
                extra_filings={"WERN": [("8-K", monday, "0000793074-26-000161")]},
                no_close=frozenset({monday}))
    assert snap["as_of"] == "2026-10-09"
    rows = _rows(snap)
    assert "8-K 2026-10-12 acc 0000793074-26-000161" in rows["WERN"].newer_filings
    assert rows["WERN"].passed_trigger_deadlines == []
    assert rows["EPAM"].last_evidence_date == monday and not rows["EPAM"].evidence_after_day
    assert not [n for n in snap["notes"] if "no freshness row" in n or "dated after" in n]


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
    it = _rows(snap)["IT"]
    assert it.passed_trigger_deadlines == [
        "Friday check — deadline 2026-09-18 PASSED → re-underwrite due"]
    assert "Saturday check (by 2026-09-19)" in it.triggers
    assert seen and all(days == ["2026-09-16"] for days in seen)


def test_one_unreadable_record_drops_its_row_not_the_day(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A hand-typo'd amendment date on WERN: ⊕ the day is still written, with IT's row; ⊖ WERN has
    no row; ⊕ the day's notes name WERN and the bad value — never a silent drop."""
    bad = {**WERN_REC, "scenarios": {"bull": {"reason": "x [amended 2026-02-30 typo] y"}}}
    snap = _run(tmp_path, monkeypatch, "2026-09-22", [IT_REC, bad])
    assert set(_rows(snap)) == {"IT"}
    assert [n for n in snap["notes"]
            if n.startswith("RECORD WERN: bull reason amendment '2026-02-30'")]


@pytest.mark.parametrize("ref", ["2026-10-14", "2026-10-01"])
def test_a_past_ref_into_the_book_is_refused_before_anything_is_fetched(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        ref: str) -> None:
    """THE REVIEWS' SHAPES (#708), through the real command over the real ledger, with 2026-10-09
    committed: ⊖ `--ref 2026-10-14` — NEWER than the newest day, older than the latest close, the
    case no later file can reveal — and ⊖ `--ref 2026-10-01`, back-dated, are both refused with a
    clean message and exit 1; ⊖ no price or filing is fetched and no book is printed; ⊖ nothing is
    written."""
    from vinci import cli
    calls = _wire(tmp_path, monkeypatch, [IT_REC],
                  prior={"2026-10-09": {"as_of": "2026-10-09", "freshness": []}})
    assert cli._cmd_monitor(argparse.Namespace(ref=ref, out=None)) == 1
    said = capsys.readouterr().out
    assert f"--ref {ref} is before today" in said and "BOOK as of" not in said
    assert calls == {"prices": 0, "filings": 0}
    assert sorted(p.name for p in (tmp_path / "data/monitor").glob("*.json")) == [
        "2026-10-09.json", "benchmark_assignments.json"]


def test_an_out_root_that_is_the_book_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """`--out .` would make the scratch root the repo itself, so the past day would land in the
    book after all: ⊖ refused, exit 1, nothing fetched."""
    from vinci import cli
    calls = _wire(tmp_path, monkeypatch, [IT_REC])
    assert cli._cmd_monitor(argparse.Namespace(ref="2026-09-22", out=str(tmp_path))) == 1
    assert "the book, not a scratch root" in capsys.readouterr().out
    assert calls == {"prices": 0, "filings": 0}


def test_a_run_with_no_ref_still_writes_into_the_book(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """⊕ The routine run — no `--ref`, no `--out` — is untouched by the refusal: it files the
    latest session on or before today and writes it into the book's own `data/monitor/`."""
    from vinci import cli
    _wire(tmp_path, monkeypatch, [IT_REC])
    assert cli._cmd_monitor(argparse.Namespace(ref=None, out=None)) == 0
    snap = _written(tmp_path / "data/monitor")
    assert date.fromisoformat(snap["as_of"]) <= date.today()
