"""A DECISION THE OPERATOR RULES OUT OF THE RECORD IS VOIDED BY AN APPENDED ROW, AND EVERY READER
LEAVES IT OUT (operator ruling 2026-11-11, GOOGL: "we want to remove the buy card/ buy verdict
altogether given it was done based on really old and wrong data and we dont want this buy verdict
to interfere in future at all").

The ledger is append-only and has no delete, so the decision is VOIDED: a `EVENT_VOID` row names
it, states the ruling and its date, and seals the decision's result to date as the monitor marks
it. Its decision, correction and void rows stay as audit history. Every test runs on the committed
ledger — GOOGL's real BUY, sealed 345.90 on 2026-08-14 and corrected to 340.65 on 2026-08-27 — with
the void appended on a COPY; the committed ledger is never written.
"""
from __future__ import annotations

import argparse
import json
import shutil
import types
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from vinci import monitor as mon
from vinci.config import Config
from vinci.ledger.correction import correct_entry, void_decision
from vinci.ledger.workflow import LedgerError, close_position
from vinci.schemas.ledger import (
    EVENT_VOID,
    LedgerEntry,
    LedgerFact,
    VoidMark,
    corrected,
    corrections_by_decision,
    origin_of,
    sleeve_of,
    void_entry_id,
    voids_by_decision,
)
from vinci.schemas.market import PriceBar
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
GOOGL = "V-GOOGL"
RULING = date(2026, 11, 11)
REASON = ("operator ruling 2026-11-11: \"we want to remove the buy card/ buy verdict altogether "
          "given it was done based on really old and wrong data and we dont want this buy verdict "
          "to interfere in future at all\"; the entry was sealed on the 2026-08-14 close, 14 days "
          "before the decision (RF-D7)")


def _committed_all() -> list[LedgerEntry]:
    return [LedgerEntry.model_validate(json.loads(json.loads(ln)["payload"]))
            for ln in LEDGER.read_text().splitlines() if ln.strip()]


def _committed() -> list[LedgerEntry]:
    """The committed ledger WITHOUT its void rows: these tests append GOOGL's void themselves, so
    they read the same once the real void is committed (V2) — the lesson of #955, for voids."""
    return [e for e in _committed_all() if e.event != EVENT_VOID]


def _googl_read() -> LedgerEntry:
    rows = _committed()
    d = next(e for e in rows if e.entry_id == GOOGL)
    return corrected(d, corrections_by_decision(rows).get(GOOGL))


def _mark(**update: Any) -> VoidMark:
    """A mark on GOOGL's entry AS READ (its correction's), the shape `vinci void-decision`
    seals."""
    r = _googl_read()
    base = {"entry_price": r.entry_price, "entry_date": r.entry_price_as_of,
            "as_of": date(2026, 11, 6), "price": 284.78, "position_return": -0.1635,
            "benchmark": "SPY", "benchmark_return": -0.0441, "excess": -0.1194,
            "return_basis": "total"}
    return VoidMark(**{**base, **update})


def _store(tmp_path: Path) -> Store:
    tmp_path.mkdir(parents=True, exist_ok=True)
    store = Store(tmp_path / "l.db")
    for e in _committed():
        store.append_ledger(e)
    return store


def _void(store: Store, **kw: Any) -> LedgerEntry:
    args: dict[str, Any] = {"entry_id": GOOGL, "reason": REASON, "ruled_on": RULING,
                            "mark": _mark(), "voided_at": datetime(2026, 11, 11, 12),
                            "reason_code": "data_error_at_entry"}
    return void_decision(store, **{**args, **kw})


def test_the_committed_ledger_is_what_these_tests_assume() -> None:
    """GOOGL's BUY and its correction are committed; a committed void, if any, is GOOGL's alone."""
    rows = {e.entry_id: e for e in _committed_all()}
    assert rows[GOOGL].verdict.value == "BUY" and rows[GOOGL].entry_price == 345.9
    assert "R-GOOGL" in rows and set(voids_by_decision(rows.values())) <= {GOOGL}


# --- the row -------------------------------------------------------------------------------------

def test_a_void_is_appended_and_every_googl_row_stays(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        row = _void(store)
        rows = {e.entry_id: e for e in store.iter_ledger()}
    assert (row.entry_id, row.event, row.voids_entry_id) == ("X-GOOGL", EVENT_VOID, GOOGL)
    assert row.entry_id == void_entry_id(GOOGL)
    assert (row.ruled_on, row.void_mark) == (RULING, _mark())
    assert (row.origin, row.sleeve) == (origin_of(rows[GOOGL]), sleeve_of(rows[GOOGL]))
    assert {GOOGL, "R-GOOGL", "X-GOOGL"} <= set(rows)               # audit history, all kept
    assert rows[GOOGL].entry_price == 345.9                          # the sealed row, unchanged


@pytest.mark.parametrize("kw, expect", [
    ({"entry_id": "V-NOPE"}, "no decision row"),
    ({"entry_id": "C-IT-screen2-20260706"}, "no decision row"),
    ({"entry_id": "V-IT-screen2-20260706", "mark": None}, "was closed by C-IT"),
    ({"reason": "  "}, "only on stated grounds"),
    ({"mark": "at the sealed entry"}, "the result sealed with a void is the decision's own"),
])
def test_a_void_that_does_not_belong_is_refused(tmp_path: Path, kw: dict[str, Any],
                                                expect: str) -> None:
    """A void names a live decision, on stated grounds, sealing the result of the entry the
    decision is READ at — a mark taken at GOOGL's sealed 345.90 is not its result."""
    if kw.get("mark") == "at the sealed entry":
        kw = {"mark": _mark(entry_price=345.9, entry_date=date(2026, 8, 14))}
    elif "mark" in kw and kw["mark"] is None:
        kw = {k: v for k, v in kw.items() if k != "mark"}
    with _store(tmp_path) as store:
        n = len(list(store.iter_ledger()))
        with pytest.raises(LedgerError, match=expect):
            _void(store, **kw)
        assert len(list(store.iter_ledger())) == n


def test_a_mark_on_the_split_basis_is_the_decisions_own(tmp_path: Path) -> None:
    """The monitor's row states the entry on the MARK's split basis (`entry_on_basis`): a name that
    split since its entry reads a restated entry price on the SAME session. That mark is the
    decision's own, and is sealed as the row states it — never refused for the restatement."""
    split = _mark(entry_price=340.65 / 2, price=284.78 / 2)
    with _store(tmp_path) as store:
        row = _void(store, mark=split)
    assert row.void_mark == split and row.entry_price == 340.65


def test_a_second_void_is_refused(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _void(store)
        with pytest.raises(LedgerError, match="already voided"):
            _void(store, voided_at=datetime(2026, 11, 11, 13))


def _void_row(**update: Any) -> dict[str, Any]:
    with_void = _committed()
    d = next(e for e in with_void if e.entry_id == GOOGL)
    row = d.model_copy(update={
        "entry_id": "X-GOOGL", "event": EVENT_VOID, "voids_entry_id": GOOGL, "reason": REASON,
        "ruled_on": RULING, "void_mark": _mark(), "facts": {}, "machine_proposal": None,
        "machine_lean": None, "proposal_assembled_at": None, "disposition": None,
        "stated_limit": None})
    return {**row.model_dump(), **update}


def test_a_well_formed_void_row_validates() -> None:
    """THE POSITIVE PIN for the shape guards below."""
    assert LedgerEntry.model_validate(_void_row()).event == EVENT_VOID


@pytest.mark.parametrize("update, expect", [
    ({"voids_entry_id": None}, "names no decision"),
    ({"voids_entry_id": "X-GOOGL"}, "voids itself"),
    ({"reason": " "}, "only on stated grounds"),
    ({"ruled_on": None}, "has no ruled_on"),
    ({"void_mark": None}, "has no void_mark"),
    ({"exit_price": 300.0}, "a void is not a close"),
    ({"corrects_entry_id": GOOGL}, "a void is not a close or a correction"),
    ({"facts": "a sealed fact"}, "carries facts"),
])
def test_a_malformed_void_row_is_refused(update: dict[str, Any], expect: str) -> None:
    if update.get("facts") == "a sealed fact":
        fact = LedgerFact(value=340.65, unit="$/share", basis="GOOGL close, 2026-08-27",
                          source="Polygon daily aggregates, GOOGL, 2026-08-27")
        update = {"facts": {"entry_close": fact.model_dump()}}
    with pytest.raises(ValueError, match=expect):
        LedgerEntry.model_validate(_void_row(**update))


def test_only_a_void_row_carries_the_void_fields() -> None:
    """A decision, a close or a correction carrying a void field is refused: it would read as a
    void no reader treats as one."""
    rows = {e.entry_id: e for e in _committed()}
    for eid in (GOOGL, "C-IT-screen2-20260706", "R-GOOGL"):
        with pytest.raises(ValueError, match="belong to a void row"):
            LedgerEntry.model_validate({**rows[eid].model_dump(), "ruled_on": RULING})


def test_an_orphan_or_a_double_void_raises_in_every_reader() -> None:
    rows = _committed()
    void = LedgerEntry.model_validate(_void_row())
    assert voids_by_decision([*rows, void])[GOOGL] is void
    with pytest.raises(ValueError, match="name no decision row"):
        voids_by_decision([e for e in rows if e.entry_id != GOOGL] + [void])
    twice = LedgerEntry.model_validate(_void_row(entry_id="X-GOOGL-2"))
    with pytest.raises(ValueError, match="voided twice"):
        voids_by_decision([*rows, void, twice])
    with pytest.raises(ValueError, match="voided twice"):
        mon.apply_corrections([{"payload": e.model_dump_json()} for e in [*rows, void, twice]])


# --- the writers refuse a voided decision --------------------------------------------------------

def test_a_voided_decision_is_never_closed_or_corrected(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _void(store)
        with pytest.raises(LedgerError, match="VOIDED by X-GOOGL"):
            close_position(store, candidate_id="GOOGL", exit_price=300.0,
                           exit_price_as_of=date(2026, 11, 10), reason="test",
                           closed_at=datetime(2026, 11, 11, 13))
        with pytest.raises(LedgerError, match="VOIDED"):
            correct_entry(store, entry_id=GOOGL, entry_price=341.0,
                          entry_price_as_of=date(2026, 8, 26), reason="test",
                          corrected_at=datetime(2026, 11, 11, 13))


# --- the readers leave it out --------------------------------------------------------------------

def _raw(with_void: bool) -> list[dict[str, Any]]:
    raw = [r for r in (json.loads(ln) for ln in LEDGER.read_text().splitlines() if ln.strip())
           if mon.entry_of(r).get("event") != EVENT_VOID]
    if with_void:
        v = LedgerEntry.model_validate(_void_row())
        raw.append({"entry_id": v.entry_id, "ticker": v.ticker, "verdict": v.verdict.value,
                    "payload": v.model_dump_json()})
    return raw


def test_the_monitors_book_leaves_a_voided_decision_out() -> None:
    """`decision_rows` — the book, the spread, `live_verdicts`, the supersede guard — and
    `apply_corrections` (the first thing `vinci monitor` does) leave GOOGL out, and name the void
    ONCE, with the result its void sealed. Without the void (the negative pin) GOOGL is there."""
    assert GOOGL in {r["entry_id"] for r in mon.decision_rows(_raw(False))}
    raw = _raw(True)
    assert GOOGL not in {r["entry_id"] for r in mon.decision_rows(raw)}
    assert "GOOGL" not in mon.live_verdicts(raw, as_of=date(2026, 11, 11))
    kept, notes = mon.apply_corrections(raw)
    assert not [r for r in kept if mon.entry_of(r).get("ticker") == "GOOGL"]
    (note,) = [n for n in notes if "VOIDED" in n]
    assert "X-GOOGL" in note and "2026-11-11" in note and "-16.35%" in note


def _snapshots_without_void(out: Path) -> Path:
    from tests.test_per_row_benchmark import snapshots_without_void
    return snapshots_without_void(out)


# --- a void is in effect FROM ITS RULING DATE (operator, 2026-11-11: "From 2026-11-11 on") ------

BEFORE_RULING = date(2026, 11, 6)


def test_the_monitor_reads_a_void_from_its_ruling_date() -> None:
    """THE CODEX P1 ON #984, in both directions. Cut before 2026-11-11, the book holds GOOGL as it
    was live that day, and names no void; cut on or after it, GOOGL is out and the void is named
    once. Without ``as_of`` (a writer's read of the ledger as it stands) every void counts."""
    raw = _raw(True)
    kept, notes = mon.apply_corrections(raw, as_of=BEFORE_RULING)
    assert GOOGL in {r["entry_id"] for r in mon.decisions_as_of(kept, as_of=BEFORE_RULING)}
    assert not [n for n in notes if "VOIDED" in n]
    assert GOOGL in {r["entry_id"] for r in mon.decision_rows(raw, as_of=BEFORE_RULING)}
    assert mon.live_verdicts(raw, as_of=BEFORE_RULING)["GOOGL"] == "BUY"
    for on in (RULING, date(2026, 12, 15)):
        kept, notes = mon.apply_corrections(raw, as_of=on)
        assert GOOGL not in {r["entry_id"] for r in mon.decisions_as_of(kept, as_of=on)}
        assert len([n for n in notes if "VOIDED by X-GOOGL" in n]) == 1
        assert "GOOGL" not in mon.live_verdicts(raw, as_of=on)
    assert GOOGL not in {r["entry_id"] for r in mon.decision_rows(raw)}


def test_every_committed_monitor_day_reproduces_with_a_void_ruled_after_it() -> None:
    """A PAST DAY RE-CUT IS THE DAY AS COMMITTED. For every committed `data/monitor/<day>.json`, the
    book `vinci monitor --ref <day>` derives from the ledger WITH GOOGL's void — its tickers, as the
    day's rows name them — is the committed day's. Before the fix, the seven days from 2026-09-16
    to 2026-11-02 lost GOOGL."""
    raw = _raw(True)
    days = sorted((ROOT / "data" / "monitor").glob("2026-*.json"))
    assert days, "no committed monitor day to reproduce"
    for p in days:
        day = json.loads(p.read_text())
        on = date.fromisoformat(str(day["as_of"])[:10])
        if on >= RULING:
            continue                      # a day on or after the ruling is the void's to change
        kept, _ = mon.apply_corrections(raw, as_of=on)
        book = sorted(str(r["ticker"]) for r in mon.decisions_as_of(kept, as_of=on))
        assert book == sorted(str(r["ticker"]) for r in day["rows"]), p.name


def test_a_report_cut_before_the_ruling_scores_the_decision_as_it_was(tmp_path: Path) -> None:
    """THE SCORING HALF: as of 2026-11-06 the report with GOOGL's void is the report without it —
    every score, count and note; as of the ruling it leaves GOOGL out and names the void once."""
    from tests.dividend_support import no_dividends, no_splits
    from tests.test_per_row_benchmark import _committed_ledger_store
    from vinci.monitor import read_assignments_file
    from vinci.scoring import score_ledger
    asg = read_assignments_file(ROOT / "data" / "monitor" / "benchmark_assignments.json")
    snaps = _snapshots_without_void(tmp_path / "snaps")
    out = {}
    for name, void in (("plain", False), ("voided", True)):
        with _committed_ledger_store(tmp_path / f"{name}.db", snaps) as store:
            if void:
                _void(store)
            out[name] = {on: score_ledger(store, as_of=on, dividends=no_dividends,
                                          splits=no_splits, assignments=asg)
                         for on in (BEFORE_RULING, RULING)}
    assert out["voided"][BEFORE_RULING] == out["plain"][BEFORE_RULING]
    scores, report = out["voided"][RULING]
    assert GOOGL not in {s.entry_id for s in scores}
    # BESIDE THE CURVE since 2026-11-13 (#1004 item 5): its own line, no longer a pending note
    assert sum("VOIDED by X-GOOGL" in n for n in report.void_notes) == 1
    assert not any("VOIDED" in n for n in report.row_notes)
    plain = out["plain"][RULING][1]
    assert not any("VOIDED" in n for n in (*plain.row_notes, *plain.void_notes))


def test_a_ruling_dated_after_its_append_is_refused(tmp_path: Path) -> None:
    """A void records a ruling already made: the pages key on the row's presence, so a row dated
    after its own append would take the decision off the web before any report drops it."""
    with _store(tmp_path) as store:
        with pytest.raises(LedgerError, match="a void records a ruling already made"):
            _void(store, ruled_on=date(2026, 11, 20))
        assert not voids_by_decision(store.iter_ledger())


def test_scoring_leaves_a_voided_decision_out_and_the_primary_spread_does_not_move(
        tmp_path: Path) -> None:
    """THE REPORT: on the committed ledger with flat bars (`test_per_row_benchmark`'s store), GOOGL
    resolves by 2027-03-19 and sits in the quality sleeve's curve; voided, it is in no score and no
    curve, the report names the void once, and the PRIMARY screen-origin spread is unchanged (GOOGL
    is followed-origin)."""
    from tests.dividend_support import no_dividends, no_splits
    from tests.test_per_row_benchmark import _committed_ledger_store
    from vinci.monitor import read_assignments_file
    from vinci.scoring import score_ledger
    asg = read_assignments_file(ROOT / "data" / "monitor" / "benchmark_assignments.json")
    as_of = date(2027, 3, 19)
    snaps = _snapshots_without_void(tmp_path / "snaps")
    with _committed_ledger_store(tmp_path / "a.db", snaps) as store:
        before, rb = score_ledger(store, as_of=as_of, dividends=no_dividends, splits=no_splits,
                                  assignments=asg)
    with _committed_ledger_store(tmp_path / "b.db", snaps) as store:
        _void(store)
        after, ra = score_ledger(store, as_of=as_of, dividends=no_dividends, splits=no_splits,
                                 assignments=asg)
    assert GOOGL in {s.entry_id for s in before} and "quality" in rb.by_sleeve
    assert GOOGL not in {s.entry_id for s in after} and "quality" not in ra.by_sleeve
    assert [s for s in before if s.entry_id != GOOGL] == after
    assert ra.buy_avoid_spread == rb.buy_avoid_spread
    assert (ra.n_resolved_buy, ra.n_resolved_avoid) == (rb.n_resolved_buy, rb.n_resolved_avoid)
    assert sum("VOIDED by X-GOOGL" in n for n in ra.void_notes) == 1
    assert "**Voided**" in ra.to_markdown() and "-16.35%" in ra.to_markdown(), (
        "the voided row's result is not printed beside the curve")


# --- the command ---------------------------------------------------------------------------------

@pytest.fixture
def tree(tmp_path: Path) -> Config:
    data = tmp_path / "data"
    data.mkdir()
    shutil.copytree(ROOT / "data" / "snapshots", data / "snapshots")
    # the command voids GOOGL itself, so its tree holds the ledger without a committed void
    (data / "snapshots" / "decision_ledger.jsonl").write_text("".join(
        json.dumps(r) + "\n" for r in _raw(False)))
    cfg = Config(data_dir=data)
    cfg.ensure_dirs()
    return cfg


def _run(tree: Config, monkeypatch: pytest.MonkeyPatch, *, dry: bool) -> int:
    from vinci import cli
    monkeypatch.setattr(cli, "get_config", lambda: tree)
    monkeypatch.setattr(cli, "_void_mark", lambda _d: _mark())
    return cli._cmd_void_decision(argparse.Namespace(entry_id=GOOGL, reason=REASON,
                                                     ruled_on=RULING.isoformat(), dry_run=dry,
                                                     void_reason="data_error_at_entry"))


def _lines(tree: Config) -> list[str]:
    return [ln for ln in (tree.snapshots_dir / "decision_ledger.jsonl").read_text().splitlines()
            if ln.strip()]


def test_the_dry_run_prints_the_void_and_writes_nothing(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    before = _lines(tree)
    assert _run(tree, monkeypatch, dry=True) == 0
    out = capsys.readouterr().out
    assert "read at 340.65 on 2026-08-27" in out and "-16.35%" in out and "DRY RUN" in out
    assert _lines(tree) == before and not tree.db_path.exists()


def test_the_command_appends_the_void_and_keeps_every_committed_line(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    before = _lines(tree)
    assert _run(tree, monkeypatch, dry=False) == 0
    after = _lines(tree)
    assert len(after) == len(before) + 1 and all(ln in after for ln in before)
    (new,) = [json.loads(ln) for ln in after if ln not in before]
    assert new["entry_id"] == "X-GOOGL"
    assert _run(tree, monkeypatch, dry=False) == 1
    assert "already voided" in capsys.readouterr().out


def test_the_sealed_mark_is_the_monitors_own_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """END TO END: `_void_mark` runs `vinci monitor` into a scratch root (on the monitor tests'
    wired vendors) and seals GOOGL's own row of that day — the entry it is read at, the mark, the
    returns — never a second computation."""
    from tests.test_monitor_ref_date_bound import _wire
    from vinci import cli
    _wire(tmp_path, monkeypatch, [])
    # the mark is taken BEFORE the void is appended, so the wired ledger holds none (once GOOGL's
    # void is committed, today's book rightly leaves it out)
    (tmp_path / "data" / "snapshots" / "decision_ledger.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in _raw(False)))
    mark = cli._void_mark(_googl_read())
    assert (mark.entry_price, mark.entry_date) == (340.65, date(2026, 8, 27))
    assert cli._cmd_monitor(argparse.Namespace(ref=None, out=str(tmp_path / "m"))) == 0
    (day,) = [json.loads(p.read_text()) for p in (tmp_path / "m" / "data" / "monitor").glob("2*")]
    (row,) = [r for r in day["rows"] if r["ticker"] == "GOOGL"]
    assert (mark.as_of.isoformat(), mark.price, mark.position_return, mark.excess) == (
        row["current_date"], row["current_price"], row["position_return"], row["excess"])


def test_a_monitor_that_cannot_mark_is_a_refusal_not_a_traceback(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """`vinci monitor` raises RuntimeError when it refuses to mark a leg (a missing bar, UNKNOWN
    dividends or splits); `_void_mark` says that as a LedgerError, which the command prints as
    REFUSED with nothing written."""
    from vinci import cli

    def refuse(_args: argparse.Namespace) -> int:
        raise RuntimeError("GOOGL: no position bar for GOOGL — refusing to guess a price")
    monkeypatch.setattr(cli, "_cmd_monitor", refuse)
    with pytest.raises(LedgerError, match="could not mark the book.*refusing to guess"):
        cli._void_mark(_googl_read())


# --- a fresh decision after a void (the id scheme)-----------------------------------------------

def test_every_committed_follow_up_row_keeps_its_id() -> None:
    """THE CORPUS: every committed close and correction is named as `follow_up_id` names it from
    its decision's id — the scheme renames nothing that exists."""
    from vinci.schemas.ledger import (
        CLOSE_ID_PREFIX,
        CORRECTION_ID_PREFIX,
        EVENT_CLOSE,
        EVENT_CORRECTION,
        follow_up_id,
    )
    rows = _committed()
    follow = [(e, CLOSE_ID_PREFIX, e.closes_entry_id) for e in rows if e.event == EVENT_CLOSE] + [
        (e, CORRECTION_ID_PREFIX, e.corrects_entry_id) for e in rows
        if e.event == EVENT_CORRECTION]
    assert len(follow) >= 4
    for e, prefix, target in follow:
        assert e.entry_id == follow_up_id(prefix, str(target)), e.entry_id


def test_a_fresh_decision_is_refused_while_one_is_open_and_numbered_after_a_void(
        tmp_path: Path) -> None:
    """GOOGL's BUY is open: a fresh GOOGL decision is refused. Voided, the next is ``V-GOOGL-2``.
    IT's decision is CLOSED, so its next is ``-2`` too; a new candidate starts at ``V-…``."""
    from vinci.ledger.workflow import next_decision_id
    with _store(tmp_path) as store:
        with pytest.raises(LedgerError, match="already holds an open decision 'V-GOOGL'"):
            next_decision_id(store, "GOOGL")
        _void(store)
        assert next_decision_id(store, "GOOGL") == "V-GOOGL-2"
        assert next_decision_id(store, "IT-screen2-20260706") == "V-IT-screen2-20260706-2"
        assert next_decision_id(store, "NEW-screen2-20261111") == "V-NEW-screen2-20261111"


def test_a_follow_up_id_is_named_from_the_decision_never_a_candidate() -> None:
    """A candidate id may itself start with ``V-`` (Visa's screen candidates do): the decision id
    carries one more prefix, and the close is named from that — never stripped twice."""
    from vinci.schemas.ledger import CLOSE_ID_PREFIX, decision_entry_id, follow_up_id
    assert decision_entry_id("V-screen2-20261016") == "V-V-screen2-20261016"
    assert follow_up_id(CLOSE_ID_PREFIX, "V-V-screen2-20261016") == "C-V-screen2-20261016"
    assert follow_up_id(CLOSE_ID_PREFIX, "V-GOOGL-2") == "C-GOOGL-2"
    with pytest.raises(ValueError, match="not a decision id"):
        follow_up_id(CLOSE_ID_PREFIX, "GOOGL")


def test_a_close_names_the_one_open_decision_of_a_candidate(tmp_path: Path) -> None:
    """GOOGL voided, then a fresh GOOGL decision (``V-GOOGL-2``): a close of candidate GOOGL closes
    the fresh one, named ``C-GOOGL-2``; the voided one is never touched."""
    with _store(tmp_path) as store:
        _void(store)
        d = next(e for e in store.iter_ledger() if e.entry_id == GOOGL)
        store.append_ledger(LedgerEntry.model_validate(d.model_copy(update={
            "entry_id": "V-GOOGL-2", "entry_price": 300.0,
            "entry_price_as_of": date(2026, 11, 10),
            "decided_at": datetime(2026, 11, 11, 9)}).model_dump()))
        close = close_position(store, candidate_id="GOOGL", exit_price=310.0,
                               exit_price_as_of=date(2026, 11, 11), reason="test",
                               closed_at=datetime(2026, 11, 11, 13))
    assert (close.entry_id, close.closes_entry_id) == ("C-GOOGL-2", "V-GOOGL-2")


# --- the vote rule's paid confirmation (#982) never runs for a log the id scheme refuses ---------

def test_a_log_on_an_open_decision_is_refused_before_the_confirmations_draws(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`vinci log-verdict GOOGL` while V-GOOGL is open can never land (`next_decision_id`), and the
    confirmation (#982) draws ten paid syntheses before the write. So the open decision is refused
    FIRST: nothing drawn, nothing written. Once the decision is voided, the same log reaches the
    confirmation (the negative pin), as any fresh decision does."""
    from vinci import cli
    data = tmp_path / "data"
    shutil.copytree(ROOT / "data" / "snapshots", data / "snapshots")
    (data / "snapshots" / "decision_ledger.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in _raw(False)))
    cfg = Config(data_dir=data)
    cfg.ensure_dirs()
    with _store(tmp_path / "s"):
        pass
    shutil.copy(tmp_path / "s" / "l.db", cfg.db_path)
    drawn: list[str] = []

    class _ReachedError(Exception):
        pass

    def _seal(_cfg: Config, _args: argparse.Namespace, ticker: str) -> Any:
        drawn.append(ticker)
        raise _ReachedError
    monkeypatch.setattr(cli, "get_config", lambda: cfg)
    monkeypatch.setattr(cli.EntityResolver, "from_config", classmethod(lambda c, _cfg=None: None))
    monkeypatch.setattr(cli, "_confirm_seal", _seal)
    monkeypatch.setattr(cli, "_screen_id_book_conflict", lambda *_a: None)
    monkeypatch.setattr(cli, "_followed_identity",
                        lambda *_a: (types.SimpleNamespace(ticker="GOOGL"), "quality"))
    monkeypatch.setattr(cli, "require_edge_basis", lambda *_a, **_k: "")
    monkeypatch.setattr(cli, "_committed_ev_gap", lambda *_a: None)
    from vinci.ledger.workflow import follow_origin
    monkeypatch.setattr(cli, "_follow_origin",
                        lambda *_a: follow_origin("GOOGL", date(2026, 8, 17)))
    # the underwrite read needs a git checkout (`read_underwrite`), which a sandboxed run of this
    # file is not; the refusal pinned here comes before it, and the draw after it
    import vinci.ledger.underwrite as uw
    monkeypatch.setattr(uw, "read_underwrite", lambda *_a, **_k: None)
    args = argparse.Namespace(candidate_id="GOOGL", ref=None, dry_run=True,
                              no_underwrite_reason="fixture: no underwrite record")
    assert cli._cmd_log_verdict(args) == 1
    assert drawn == []
    with Store(cfg.db_path) as store:
        _void(store)
    with pytest.raises(_ReachedError):
        cli._cmd_log_verdict(args)
    assert drawn == ["GOOGL"]


# --- a fresh decision never enters before the earlier one left the book (Codex round 2, #984) ---

def test_a_back_dated_fresh_decision_is_refused_and_one_from_the_exit_on_is_not(
        tmp_path: Path) -> None:
    """THROUGH `log_verdict`: XYZ's AVOID entered 2026-06-12 and was CLOSED at the 2026-06-16
    close. A fresh decision logged on 06-17 with ``--ref 2026-06-15`` would enter at the 06-12 close
    — inside the closed decision's life, so every cut from 06-12 to 06-16 would hold both. It is
    refused, nothing written. Entered at the 06-17 close (on or after the exit), it is
    ``V-…-2``."""
    from tests.test_ledger import _KW, _ident, _seed
    from vinci.ledger import log_verdict
    from vinci.schemas.ledger import Verdict
    with Store(tmp_path / "t.db") as store:
        ident = _ident("XYZ", "SEC-0000000009-XYZ", "0000000009")
        cid = _seed(store, ident)
        log_verdict(store, candidate_id=cid, verdict=Verdict.AVOID_TERMINAL,
                    decided_at=datetime(2026, 6, 15, 10, 0), **_KW)
        close_position(store, candidate_id=cid, exit_price=40.0,
                       exit_price_as_of=date(2026, 6, 16), reason="test",
                       closed_at=datetime(2026, 6, 16, 22))
        rows = len(list(store.iter_ledger()))
        with pytest.raises(LedgerError, match="before .* left the book on 2026-06-16"):
            log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 17, 10, 0), **_KW)
        assert len(list(store.iter_ledger())) == rows
        store.write_prices([PriceBar(internal_id=ident.internal_id, bar_date=date(2026, 6, 17),
                                     open=41.0, high=42.0, low=40.0, close=41.5, volume=1e7,
                                     source="polygon-grouped")])
        fresh = log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                            decided_at=datetime(2026, 6, 17, 22, 0),
                            **{**_KW, "reference_date": date(2026, 6, 17)})
    assert (fresh.entry_id, fresh.entry_price_as_of) == (f"V-{cid}-2", date(2026, 6, 17))


def test_a_fresh_decision_after_a_void_enters_on_or_after_its_ruling(tmp_path: Path) -> None:
    """THE VOID HALF: GOOGL voided on the ruling of 2026-11-11 — a fresh GOOGL decision entering
    on 11-10 is refused, one entering on 11-11 is ``V-GOOGL-2``. Without an entry date (the id
    alone) nothing changes."""
    from vinci.ledger.workflow import next_decision_id
    with _store(tmp_path) as store:
        _void(store)
        with pytest.raises(LedgerError, match="before 'V-GOOGL' left the book on 2026-11-11"):
            next_decision_id(store, "GOOGL", entering_on=date(2026, 11, 10))
        assert next_decision_id(store, "GOOGL", entering_on=RULING) == "V-GOOGL-2"
        assert next_decision_id(store, "GOOGL") == "V-GOOGL-2"


# --- a monitor day keys a void on the SESSION it files, as a close is (the 2026-11-11 case) ------

def test_a_day_filed_before_the_ruling_keeps_the_voided_decision_and_reproduces(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE REAL CASE, 2026-11-11. The routine `vinci monitor` ran on the ruling day before that
    session closed, so it filed 2026-11-10. Keyed on the run's ``--ref``, that day dropped GOOGL
    while a re-cut of 2026-11-10 kept it: the committed day did not reproduce, and V2's first gate
    refused it. Keyed on the filed session, as closes are, the 11-10 day keeps GOOGL and equals its
    re-cut, and the 11-11 session's day is the first to leave it out. The void row is the one the
    real `vinci void-decision` wrote (#984's dry run); a committed void is used as committed."""
    from tests.test_monitor_ref_date_bound import _wire, _written
    from vinci import cli
    void_row = json.loads((ROOT / "tests" / "fixtures" / "ledger_void" / "x_googl_dry_run.jsonl")
                          .read_text())

    # THE REAL RECORD TOO: the routine day also dropped GOOGL from the FRESHNESS panel, which
    # reads `live_verdicts` on the same ledger read — with no record served it is empty either way
    record = json.loads((ROOT / "scenarios" / "GOOGL.json").read_text())
    ruled = str(mon.entry_of(void_row)["ruled_on"])

    def run(name: str, ref: str, no_close: frozenset[date]) -> dict[str, Any]:
        root = tmp_path / name
        _wire(root, monkeypatch, [record], no_close=no_close)
        led = root / "data" / "snapshots" / "decision_ledger.jsonl"
        rows = [json.loads(ln) for ln in led.read_text().splitlines() if ln.strip()]
        if not any(mon.entry_of(r).get("event") == EVENT_VOID for r in rows):
            led.write_text("".join(json.dumps(r) + "\n" for r in [*rows, void_row]))
        scratch = root / "scratch"
        assert cli._cmd_monitor(argparse.Namespace(ref=ref, out=str(scratch))) == 0
        return _written(scratch / "data" / "monitor")

    def book(day: dict[str, Any]) -> list[str]:
        return sorted(str(r["ticker"]) for r in day["rows"])

    def fresh(day: dict[str, Any]) -> set[str]:
        return {str(f["ticker"]) for f in day["freshness"]}

    def voided_call(day: dict[str, Any]) -> list[dict[str, Any]]:
        # THE VOIDED DECISION, not the ticker: a fresh GOOGL decision may enter on or after the
        # ruling (`next_decision_id`), so "GOOGL in the book" alone reddens on the living ledger
        return [r for r in day["rows"] if r["ticker"] == "GOOGL" and str(r["entry_date"]) < ruled]

    routine = run("routine", "2026-11-11", frozenset({date(2026, 11, 11)}))
    recut = run("recut", "2026-11-10", frozenset())
    after = run("after", "2026-11-11", frozenset())
    assert str(routine["as_of"])[:10] == str(recut["as_of"])[:10] == "2026-11-10"
    assert voided_call(routine) and book(routine) == book(recut)
    assert "GOOGL" in fresh(routine) and fresh(routine) == fresh(recut)
    assert not any("VOIDED" in n for n in routine["notes"])
    assert str(after["as_of"])[:10] == "2026-11-11" and not voided_call(after)
    assert sum("VOIDED by X-GOOGL" in n for n in after["notes"]) == 1
