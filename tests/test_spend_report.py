"""THE MONTHLY SPEND REPORT reads the spend records that exist and refuses nothing (operator,
2026-11-13: "Report only"; issue 1004, lane 4, part B). `vinci/spend.py`.

Every fixture is built from a REAL record: a committed `assembly_runs` line, a budget ledger written
by the real `vinci.evals.replay.Budget`, a theme-desk row in the shape the state branch exports, and
a confirmation row with `vinci.dossier.confirmation`'s keys. The corpus test reads the committed run
records and checks the month's total two independent ways.
"""
from __future__ import annotations

import ast
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci import spend
from vinci.evals.replay import Budget

ROOT = Path(__file__).resolve().parent.parent
SNAPS = ROOT / "data" / "snapshots"
RUNS = SNAPS / "assembly_runs"


def _real_line() -> dict[str, Any]:
    """A committed assembly line, priced — the newest one, read from the corpus."""
    for path in sorted(RUNS.glob("*.jsonl"), reverse=True):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("usd"):
                return dict(row)
    pytest.skip("no priced assembly line is committed")


def _snaps(tmp_path: Path, rows: list[dict[str, Any]]) -> Path:
    runs = tmp_path / "snapshots" / "assembly_runs"
    runs.mkdir(parents=True)
    (runs / "2026-11-01T00-00-00Z-test0001.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return tmp_path / "snapshots"


# --- pages: the committed corpus, two ways -------------------------------------------------------
@pytest.mark.parametrize("month", ["2026-10", "2026-11"])
def test_pages_on_the_committed_runs_equals_the_sum_of_that_months_run_files(month: str) -> None:
    """(+) CORPUS: the month's pages total, dated line by line from `started_at`, equals the sum
    over the run files whose NAME carries that month (the run's own start stamp). Two fields, one
    total — a dating error in either reads as a mismatch here."""
    files = [p for p in sorted(RUNS.glob("*.jsonl")) if p.name.startswith(month)]
    if not files:
        pytest.skip(f"no run file for {month} is committed")
    lines = [json.loads(x) for p in files for x in p.read_text(encoding="utf-8").splitlines()
             if x.strip()]
    b = spend.pages(SNAPS, month)
    assert b.rows == len(lines)
    assert b.unpriced == sum(1 for r in lines if r["usd"] is None)
    assert b.usd == pytest.approx(sum(r["usd"] for r in lines if r["usd"] is not None), abs=1e-4)
    assert b.usd is not None and b.usd > 0


def test_a_line_is_dated_by_its_own_start_in_utc(tmp_path: Path) -> None:
    """(+/-) A line started at 23:59:59Z on 31 Oct is October's; one at 00:00Z on 1 Nov is
    November's; a stamp written at +05:30 is read in UTC, so 04:00 on 1 Nov there is October."""
    base = _real_line()
    rows = [{**base, "usd": 1.0, "started_at": "2026-10-31T23:59:59Z"},
            {**base, "usd": 2.0, "started_at": "2026-11-01T00:00:00Z"},
            {**base, "usd": 4.0, "started_at": "2026-11-01T04:00:00+05:30"}]
    snaps = _snaps(tmp_path, rows)
    assert (spend.pages(snaps, "2026-10").usd, spend.pages(snaps, "2026-10").rows) == (5.0, 2)
    assert (spend.pages(snaps, "2026-11").usd, spend.pages(snaps, "2026-11").rows) == (2.0, 1)


def test_an_unpriced_line_is_counted_apart_never_as_zero(tmp_path: Path) -> None:
    base = _real_line()
    snaps = _snaps(tmp_path, [{**base, "usd": 3.0, "started_at": "2026-11-02T00:00:00Z"},
                              {**base, "usd": None, "started_at": "2026-11-03T00:00:00Z"}])
    b = spend.pages(snaps, "2026-11")
    assert (b.usd, b.rows, b.unpriced) == (3.0, 2, 1)
    assert "1 row(s) unpriced, not counted as zero" in spend.render("2026-11", [b])


@pytest.mark.parametrize("edit", [{"usd": "1.0"}, {"started_at": "2026-11-02"},
                                  {"started_at": "yesterday"}])
def test_a_malformed_line_raises_rather_than_being_skipped(tmp_path: Path,
                                                           edit: dict[str, Any]) -> None:
    """(-) A string cost, a naive stamp and a non-date each raise: a skipped line would print a
    total smaller than the spend."""
    row = {**_real_line(), "usd": 1.0, "started_at": "2026-11-02T00:00:00Z", **edit}
    with pytest.raises(spend.SpendRecordError):
        spend.pages(_snaps(tmp_path, [row]), "2026-11")
    del row["usd"]
    with pytest.raises(spend.SpendRecordError, match="without usd"):
        spend.pages(_snaps(tmp_path / "b", [row]), "2026-11")


# --- evals: ledgers written by the real Budget ---------------------------------------------------
def _ledger(path: Path, rows: list[dict[str, Any]], opened_at: str,
            last_write: str | None = None) -> Path:
    """A ledger written by the real `Budget`. Its file time is SET — the last write bounds an
    undated draw's time — to ``last_write``, by default a minute after its latest stamp, so no
    test depends on the day it runs."""
    budget = Budget.open(path, cap_usd=35.0, approval="test approval")
    first, *_ = path.read_text(encoding="utf-8").splitlines()
    head = json.loads(first)
    head["approval"]["opened_at"] = opened_at          # Budget.open stamps the wall clock
    path.write_text(json.dumps(head) + "\n", encoding="utf-8")
    for r in rows:
        budget.record(r)
    stamps = [opened_at] + [r["build_start"]["started_at"] for r in rows if "build_start" in r]
    latest = max(datetime.fromisoformat(x.replace("Z", "+00:00")) for x in stamps)
    _last_write(path, last_write or (latest + timedelta(minutes=1)).isoformat())
    return path


def _last_write(path: Path, at: str) -> None:
    t = datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp()
    os.utime(path, (t, t))


def _draw(usd: float) -> dict[str, Any]:
    return {"label": "arm-a", "draw": 1, "usage": {"input_tokens": 10, "output_tokens": 5},
            "usd": usd, "served_model": "claude-opus-4-8", "stop_reason": "tool_use",
            "seconds": 1.0}


def test_a_draw_whose_bounds_span_months_is_not_placed_and_the_figure_is_a_floor(
        tmp_path: Path) -> None:
    """(-) Two draws sit between an approval opened 30 Nov in India (04:30Z) and a `build_start`
    on 1 Dec (03:30Z): they ran in November OR December, so neither month takes them; each
    month's figure is a floor naming them. (+) The draw after the `build_start`, bounded by it
    and the last write the same morning, is December's."""
    led = _ledger(tmp_path / "ledger.jsonl", [
        _draw(1.0), _draw(2.0),
        {"build_start": {"started_at": "2026-12-01T09:00:00+0530"}, "usd": 0.0},
        _draw(4.0)], opened_at="2026-11-30T10:00:00+0530", last_write="2026-12-01T04:00:00Z")
    nov, dec = spend.evals([led], "2026-11"), spend.evals([led], "2026-12")
    assert (nov.usd, nov.rows) == (0.0, 0)
    assert (dec.usd, dec.rows) == (4.0, 2)        # the build_start row and its draw
    for b in (nov, dec):
        assert b.unknown == ["2 undated row(s) in evals ($3.00) that ran across a month "
                             "boundary and may belong to this month"]
    assert "≥$0.00" in spend.render("2026-11", [nov])
    assert "at least $4.00 — 2 undated row(s) in evals ($3.00)" in spend.render("2026-12", [dec])


def test_a_resumed_run_compare_is_never_put_in_the_month_its_ledger_opened(
        tmp_path: Path) -> None:
    """(-) Codex P1 on #1061: a `run-compare` ledger opened 28 Oct and resumed in November has
    undated draws; they took the approval's month, so November's spend landed in October as a
    definite figure. Bounded by the last write (3 Nov), they now belong to neither month for
    sure. (+) The same draws with the ledger last written on 29 Oct are October's."""
    rows = [_draw(1.0), _draw(2.5)]
    resumed = _ledger(tmp_path / "a" / "ledger.jsonl", rows, opened_at="2026-10-28T10:00:00Z",
                      last_write="2026-11-03T10:00:00Z")
    for month in ("2026-10", "2026-11"):
        b = spend.evals([resumed], month)
        assert (b.usd, b.rows) == (0.0, 0) and b.unknown, month
    done = _ledger(tmp_path / "b" / "ledger.jsonl", rows, opened_at="2026-10-28T10:00:00Z",
                   last_write="2026-10-29T10:00:00Z")
    oct_ = spend.evals([done], "2026-10")
    assert (oct_.usd, oct_.rows, oct_.unknown) == (3.5, 2, [])
    assert spend.evals([done], "2026-11").usd == 0.0


def test_a_build_end_bounds_the_draws_before_it(tmp_path: Path) -> None:
    """(+) A `build_end`'s ``t`` (epoch seconds) is a stamp: the draws between a 31 Oct
    `build_start` and its 31 Oct `build_end` are October's, though the file was last written in
    November. Without it they would span the boundary and be named as may-belong."""
    end_t = datetime(2026, 10, 31, 23, 20, tzinfo=UTC).timestamp()
    led = _ledger(tmp_path / "l.jsonl", [
        {"build_start": {"started_at": "2026-10-31T23:10:00Z"}, "usd": 0.0}, _draw(2.0),
        {"build_end": {"t": end_t}, "usd": 0.0}], opened_at="2026-10-31T23:00:00Z",
        last_write="2026-11-02T10:00:00Z")
    b = spend.evals([led], "2026-10")
    assert (b.usd, b.rows, b.unknown) == (2.0, 3, [])


def test_a_build_start_is_no_upper_bound_for_the_draws_above_it(tmp_path: Path) -> None:
    """(-) Review of #1064: a `build_start`'s time is taken BEFORE its request is captured, under a
    lock a concurrent build's draws do not take, so a draw appended above it can be later than its
    stamp. A draw above a 31 Oct 23:59Z `build_start`, in a ledger last written 1 Nov, may be
    November's: it is not placed in October. (+) The draw after the `build_start` is November's
    only if bounded there — here it spans too, so October holds nothing for sure."""
    led = _ledger(tmp_path / "l.jsonl", [
        _draw(1.0), {"build_start": {"started_at": "2026-10-31T23:59:00Z"}, "usd": 0.0},
        _draw(2.0)], opened_at="2026-10-31T23:00:00Z", last_write="2026-11-01T00:05:00Z")
    oct_ = spend.evals([led], "2026-10")
    assert (oct_.usd, oct_.rows) == (0.0, 1)           # the build_start row alone, at its stamp
    assert oct_.unknown == ["2 undated row(s) in evals ($3.00) that ran across a month boundary "
                            "and may belong to this month"]


def test_a_byte_identical_copy_bounds_by_the_earliest_last_write(tmp_path: Path) -> None:
    """(+) Review of #1064: two byte-identical copies are one ledger, and each was complete by its
    own file time, so the earliest bounds its draws — not whichever path sorts first. A copy made
    in November that sorts first must not push an October draw across the boundary."""
    orig = _ledger(tmp_path / "b" / "ledger.jsonl", [_draw(2.0)],
                   opened_at="2026-10-20T10:00:00Z", last_write="2026-10-20T11:00:00Z")
    copy = tmp_path / "a" / "ledger.jsonl"
    copy.parent.mkdir()
    copy.write_bytes(orig.read_bytes())
    _last_write(copy, "2026-11-05T10:00:00Z")
    b = spend.evals([orig, copy], "2026-10")
    assert (b.usd, b.rows, b.unknown) == (2.0, 1, [])


def test_a_ledger_opened_on_the_first_in_india_is_the_previous_utc_month(tmp_path: Path) -> None:
    led = _ledger(tmp_path / "l.jsonl", [_draw(1.5)], opened_at="2026-12-01T03:00:00+0530")
    assert spend.evals([led], "2026-11").usd == 1.5
    assert spend.evals([led], "2026-12").usd == 0.0


def test_a_byte_identical_copy_counts_once_and_a_non_ledger_is_refused(tmp_path: Path) -> None:
    """(+) Two copies of one ledger are one spend. (-) A file passed as a ledger whose first line
    is no approval raises; a root scan skips it."""
    led = _ledger(tmp_path / "a" / "ledger.jsonl", [_draw(2.0)], opened_at="2026-11-10T10:00:00Z")
    copy = tmp_path / "b" / "ledger.jsonl"
    copy.parent.mkdir()
    copy.write_bytes(led.read_bytes())
    b = spend.evals([led, copy], "2026-11")
    assert (b.usd, b.rows) == (2.0, 1) and "1 copy(ies) of another ledger" in b.note
    other = tmp_path / "a" / "draws.jsonl"
    other.write_text(json.dumps(_draw(9.0)) + "\n", encoding="utf-8")
    with pytest.raises(spend.SpendRecordError, match="not a budget ledger"):
        spend.evals([other], "2026-11")
    assert spend._ledgers([], [str(tmp_path)]) == [led, copy]


def test_an_earlier_copy_of_a_ledger_counts_once_and_no_ledger_is_not_read(tmp_path: Path) -> None:
    """(+) A copy taken before the budget drew more is a prefix of the live ledger: its draws are
    the live ledger's, so they count once, not twice. (-) No ledger passed is NOT READ (None) —
    a $0 there would sit in the total as a bucket read."""
    led = _ledger(tmp_path / "a" / "ledger.jsonl", [_draw(2.0)], opened_at="2026-11-10T10:00:00Z")
    early = tmp_path / "b" / "ledger.jsonl"
    early.parent.mkdir()
    early.write_bytes(led.read_bytes())
    Budget.load(led).record(_draw(3.0))
    _last_write(led, "2026-11-10T11:00:00Z")          # the append set it to today
    b = spend.evals([early, led], "2026-11")
    assert (b.usd, b.rows) == (5.0, 2) and "1 copy(ies) of another ledger" in b.note
    none = spend.evals([], "2026-11")
    assert none.usd is None and none.note.startswith("NOT READ")
    assert "NOT included: evals" in spend.render("2026-11", [none])


# --- theme desk: the state branch's export shape -------------------------------------------------
def _call(at: str, cost: float | None, cached: bool = False) -> str:
    payload = {"at": at, "cached": cached, "cost_usd": cost, "model": "claude-opus-4-8",
               "prompt_version": "ti-enrich-2", "purpose": "enrich", "ref": "TH-TEST",
               "seconds": 8.0, "usage": {"input_tokens": 2235, "output_tokens": 729}}
    return json.dumps({"call_id": "LC-test", "payload": json.dumps(payload),
                       "purpose": "enrich", "run_id": "R-test"}) + "\n"


def test_theme_calls_sum_live_costs_and_never_price_a_missing_one() -> None:
    """(+) Live calls sum; a cache hit spends nothing; (-) a live call with no cost is unpriced,
    never zero; a call outside the month is not counted."""
    text = (_call("2026-11-02T10:00:00+00:00", 0.5) + _call("2026-11-03T10:00:00+00:00", 0.0, True)
            + _call("2026-11-04T10:00:00+00:00", None) + _call("2026-10-31T23:00:00+00:00", 9.0))
    b = spend.theme_calls(text, "2026-11", source="test")
    assert (b.usd, b.rows, b.unpriced) == (0.5, 3, 1)
    assert "1 of 3 call row(s) served from its cache" in b.note
    with pytest.raises(spend.SpendRecordError, match="without cost_usd or at"):
        spend.theme_calls(json.dumps({"payload": json.dumps({"at": "2026-11-02T00:00:00Z"})}),
                          "2026-11", source="test")


def test_an_unreadable_theme_ref_is_named_not_read_as_zero() -> None:
    b = spend.theme_desk(ROOT, "2026-11", ref="refs/heads/no-such-branch-for-this-test")
    assert b.usd is None and b.note.startswith("NOT READ")


# --- confirmations, graph judge, validate-keys ---------------------------------------------------
def test_confirmations_are_counted_and_never_priced(tmp_path: Path) -> None:
    """(+) Rows are counted by `drawn_at`; the spend is NOT RECORDED, so its usd is None — the
    total names the bucket as left out rather than adding a zero."""
    absent = spend.confirmations(tmp_path, "2026-11")
    assert absent.usd is None and "no proposal_confirmations.jsonl is committed" in absent.note
    row = {"ticker": "SMPL", "assembled_at": "2026-11-01T00:00:00Z",
           "drawn_at": "2026-11-12T10:00:00+0530", "model": "claude-opus-4-8", "draws": 10}
    (tmp_path / "proposal_confirmations.jsonl").write_text(json.dumps(row) + "\n")
    b = spend.confirmations(tmp_path, "2026-11")
    assert (b.usd, b.rows, b.note) == (None, 1, "NOT RECORDED")


def test_the_graph_judge_reads_the_committed_rejudge() -> None:
    """CORPUS: the committed map's `judged_by` is one re-judge, priced and dated."""
    judged = json.loads((ROOT / "data" / "graph_coverage.json").read_text())["judged_by"]
    month = str(judged["on"])[:7]
    b = spend.graph_judge(ROOT / "data", month)
    assert b.rows == 1 and b.usd == pytest.approx(judged["cost_usd"])
    # its own month is a floor: an earlier re-judge it overwrote, or a stopped one, is unseen
    assert b.unknown and f"≥${judged['cost_usd']:,.2f}" in spend.render(month, [b])
    # (-) a month before the recorded re-judge: any re-judge in it was overwritten — NOT READ,
    # never $0
    before = spend.graph_judge(ROOT / "data", "1999-01")
    assert (before.usd, before.rows) == (None, 0) and before.note.startswith("NOT READ")


def test_a_month_after_the_latest_rejudge_is_not_read() -> None:
    """(-) Codex P1 on #1061: a re-judge that STOPPED (over budget, or a judge error) after the
    latest recorded one spent and wrote nothing, so a later month printed a definite $0.00. It
    is NOT READ, and the total names it as left out."""
    after = spend.graph_judge(ROOT / "data", "2999-01")
    assert (after.usd, after.rows) == (None, 0) and after.note.startswith("NOT READ")
    assert "NOT included: graph judge" in spend.render("2999-01", [after])


def test_the_total_names_every_bucket_it_left_out() -> None:
    buckets = [spend.Bucket("pages", 2.0, 1, "s", "x"), spend.Bucket("evals", 3.5, 2, "s", "x"),
               spend.confirmations(Path("/nonexistent"), "2026-11"), spend.validate_keys()]
    out = spend.render("2026-11", buckets)
    assert ("total of the 2 bucket(s) read: $5.50 — NOT included: confirmations, validate-keys"
            in out)
    assert "UTC calendar month" in out and "refuses nothing" in out
    assert out.count("cannot see: ") == len(buckets)


def test_a_month_that_is_not_yyyy_mm_is_refused() -> None:
    for bad in ("2026-1", "11-2026", "2026/11", "2026-11-01", "2026-13", "2026-00"):
        with pytest.raises(spend.SpendRecordError, match="YYYY-MM"):
            spend.report(bad, repo=ROOT, snapshots=SNAPS, data_dir=ROOT / "data", ledgers=[])


def test_the_report_spends_nothing_and_refuses_nothing() -> None:
    """The module imports no model client and no HTTP layer: it reads files and git."""
    tree = ast.parse((ROOT / "vinci" / "spend.py").read_text(encoding="utf-8"))
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    forbidden = ("anthropic", "vinci.graph.llm", "vinci.theme_intelligence.llm", "vinci.netcache",
                 "vinci.evals.replay", "urllib", "requests", "httpx")
    assert not [n for n in names if n.startswith(forbidden)], names


# --- review round 1 (the independent review of 09913271) -----------------------------------------
def test_pages_with_no_run_file_is_not_read(tmp_path: Path) -> None:
    """(-) No assembly run file at all is NOT READ, never $0.00 'read' (round 1, finding 2)."""
    b = spend.pages(tmp_path, "2026-11")
    assert b.usd is None and b.note.startswith("NOT READ")


def test_the_command_reads_the_repos_data_from_any_folder(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """(+) END TO END from another folder: the config's `data` is relative, and read from the
    caller's folder it found no run file and printed the repo's pages as $0.00 (round 1, finding
    2). The command now reads the repo's own `data/`."""
    files = sorted(RUNS.glob("*.jsonl"))
    if not files:
        pytest.skip("no assembly run file is committed")
    month = files[-1].name[:7]
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(spend.LEDGER_ROOTS_ENV, raising=False)
    assert spend.main(["--month", month, "--json"]) == 0
    got = {b["name"]: b for b in json.loads(capsys.readouterr().out)["buckets"]}
    assert got["pages"]["usd"] is not None and got["pages"]["usd"] > 0
    assert got["pages"]["usd"] == spend.pages(SNAPS, month).usd


def test_a_map_with_no_judged_by_is_not_read(tmp_path: Path) -> None:
    """(-) `graph-coverage --json` rewrites the map without `judged_by`; a month then reads NOT
    READ, never $0.00, since a re-judge's cost may have been overwritten (round 1, finding 3)."""
    (tmp_path / "graph_coverage.json").write_text(json.dumps({"model": "claude-opus-4-8"}))
    b = spend.graph_judge(tmp_path, "2026-11")
    assert b.usd is None and b.note.startswith("NOT READ")


def test_the_report_returns_all_six_buckets_by_name() -> None:
    """(-) A bucket dropped from `report()` reds here (round 1, finding 4). The names are spelled
    out, so editing `BUCKETS` with it does not hide the drop."""
    names = [b.name for b in spend.report("2026-11", repo=ROOT, snapshots=SNAPS,
                                          data_dir=ROOT / "data", ledgers=[])]
    assert names == ["pages", "confirmations", "evals", "theme desk", "graph judge",
                     "validate-keys"] == list(spend.BUCKETS)


def test_every_root_searched_and_every_ledger_read_is_printed(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) The report prints each root it searched and each ledger it read, a ledger with no row
    in the month included, never a claim of a wider search (round 1, finding 1). The roots
    default to `VINCI_LEDGER_ROOTS`. (-) No root and no ledger prints that it searched none."""
    a = _ledger(tmp_path / "a" / "ledger.jsonl", [_draw(2.0)], opened_at="2026-11-10T10:00:00Z")
    b = _ledger(tmp_path / "b" / "ledger-oct.jsonl", [_draw(1.0)],
                opened_at="2026-10-10T10:00:00Z")
    monkeypatch.setenv(spend.LEDGER_ROOTS_ENV,
                       os.pathsep.join([str(tmp_path / "a"), str(tmp_path / "b")]))
    roots = spend.ledger_roots([])
    assert roots == [str(tmp_path / "a"), str(tmp_path / "b")]
    out = spend.render("2026-11", [spend.evals(spend._ledgers([], roots), "2026-11",
                                               roots=roots)])
    for root in roots:
        assert f"searched: {root}" in out
    assert f"read: {a.resolve()} — 1 draw(s) in the month, $2.00" in out
    assert f"read: {b.resolve()} — 0 draw(s) in the month, $0.00" in out
    assert spend.ledger_roots(["/given"]) == ["/given"]          # a given root wins
    none = spend.render("2026-11", [spend.evals([], "2026-11")])
    assert "searched: no root" in none and "NOT READ" in none


def test_draws_are_counted_apart_from_zero_cost_rows(tmp_path: Path) -> None:
    """(+) The rows column counts every ledger row; the note says how many are draws (round 1,
    finding 5): a `build_start` row is a zero-cost row, not a draw."""
    led = _ledger(tmp_path / "l.jsonl", [
        {"build_start": {"started_at": "2026-11-11T09:00:00+0530"}, "usd": 0.0},
        _draw(1.0), _draw(2.0)], opened_at="2026-11-10T10:00:00Z")
    b = spend.evals([led], "2026-11")
    assert (b.usd, b.rows) == (3.0, 3)
    assert "2 of the 3 row(s) are draws" in b.note


def test_each_bucket_says_what_its_rows_count_and_the_total_is_not_a_floor() -> None:
    """(+) The units differ by bucket, so each prints what its rows are; and the total says it is
    neither a floor nor exact for one month (round 1, finding 5)."""
    out = spend.render("2026-11", spend.report("2026-11", repo=ROOT, snapshots=SNAPS,
                                               data_dir=ROOT / "data", ledgers=[]))
    assert out.count("rows: ") == len(spend.BUCKETS)
    assert "neither a floor nor exact for one month" in out


def test_a_bucket_with_unpriced_rows_never_yields_a_definite_total() -> None:
    """(-) Codex P1 on 40c33550: a bucket holding unpriced rows put its priced part into a total
    printed as definite, so the month read lower than it was with nothing on the total line to
    say so. Its figure and the total now read as a floor ("≥", "at least") and name the rows that
    are not in it. (+) With every row priced, the total stays a plain figure."""
    partial = [spend.Bucket("pages", 3.0, 2, "s", "x", unpriced=1),
               spend.Bucket("evals", 2.0, 1, "s", "x")]
    out = spend.render("2026-11", partial)
    assert "≥$3.00" in out
    assert ("total of the 2 bucket(s) read: at least $5.00 — 1 unpriced row(s) in pages are "
            "not in it") in out
    whole = spend.render("2026-11", [spend.Bucket("pages", 3.0, 2, "s", "x")])
    assert "total of the 1 bucket(s) read: $3.00" in whole and "at least" not in whole
