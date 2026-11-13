"""The ledger safeguards of 2026-11-13 (#1004 item 5; operator: "yes need to do this reliably").

Five rules, every one additive — new optional fields, and no committed row rewritten:

1. THE UNDERWRITE SEAL. `log-verdict` reads the live `scenarios/<T>.json` and seals its path, the
   commit it was read at, the sha256 of its bytes and the ratio re-run at the frozen entry; a
   decision with no record states why or is refused; a record with no horizon LOADS and is refused
   only at the decision.
2. ORIGIN AND BOOK on every new row: the screen run or the follow entry (with `followed_since`),
   and the sleeve.
3. PRE-REGISTERED VOID REASONS: a data error at entry, the wrong instrument, the wrong identity. A
   change of mind is a CLOSE and stays scored. Voided rows' results print beside the curve, X-GOOGL
   (which predates the list) as it stands.
4. ONE OBSERVATION PER NAME: a same-call decision inside an earlier one's open window is a
   REAFFIRMATION, in no count. SMPL is the one live case.
5. THE READING FLOOR: a book's curve is read once it holds 20 resolved observations; below, the
   count prints and nothing else. A display rule — the computed numbers are unchanged.

PINNED AT THE SEATS (`log_verdict`, `void_decision`, `score_ledger` → `to_markdown`), on the REAL
committed records and ledger wherever one exists, with a negative pin beside every refusal.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.dividend_support import no_dividends, no_splits
from tests.test_ledger import _KW, _ident, _seed
from vinci import scenarios as sc
from vinci.ledger import LedgerError, log_verdict
from vinci.ledger.underwrite import read_underwrite
from vinci.ledger.workflow import follow_origin
from vinci.schemas.ledger import (
    EVENT_VOID,
    READING_FLOOR,
    VOID_REASONS,
    Confidence,
    LedgerEntry,
    OriginRef,
    Verdict,
    reaffirmations,
)
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.scoring.metrics import VerdictScore, aggregate
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
NO_RECORD: dict[str, Any] = {"underwrite": None,
                             "no_underwrite_reason": "fixture: no underwrite record"}
KW: dict[str, Any] = {k: v for k, v in _KW.items() if k not in NO_RECORD}


def _committed() -> list[LedgerEntry]:
    return [LedgerEntry.model_validate_json(json.loads(ln)["payload"])
            for ln in LEDGER.read_text().splitlines() if ln.strip()]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def _repo_with(tmp: Path, *tickers: str) -> Path:
    """A git repo holding the REAL committed records for ``tickers``, committed."""
    repo = tmp / "repo"
    (repo / "scenarios").mkdir(parents=True)
    for t in tickers:
        shutil.copy(ROOT / "scenarios" / f"{t}.json", repo / "scenarios" / f"{t}.json")
    _git(repo, "init", "-q")
    _git(repo, "add", "scenarios")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "records")
    return repo


def _legs(ticker: str) -> tuple[float, float]:
    """The committed record's base and bear value per share (its own result)."""
    res = sc.read_record(ticker, root=ROOT).result
    assert res is not None
    return (res.per_scenario["base"].value_per_share, res.per_scenario["bear"].value_per_share)


# ─── 1. THE UNDERWRITE SEAL ───────────────────────────────────────────────────────────────────

def test_the_link_names_the_record_its_commit_and_its_bytes(tmp_path: Path) -> None:
    """SMPL's committed record, read as `log-verdict` reads it. At the record's own spot the ratio
    is the record's own (2.0952), so the re-run is the recipe's arithmetic and no second one."""
    repo = _repo_with(tmp_path, "SMPL")
    link = read_underwrite("SMPL", root=repo)
    assert link is not None
    raw = (ROOT / "scenarios" / "SMPL.json").read_bytes()
    import hashlib
    assert (link.ref, link.commit, link.sha256) == (
        "scenarios/SMPL.json", _git(repo, "rev-parse", "HEAD"), hashlib.sha256(raw).hexdigest())
    rec = sc.read_record("SMPL", root=ROOT)
    assert rec.result is not None and link.ratio_at(rec.spot)[0] == pytest.approx(rec.result.ratio)
    base, bear = _legs("SMPL")
    assert link.ratio_at(12.0)[0] == pytest.approx((base - 12.0) / (12.0 - bear))
    assert link.horizon_years == 1.5


def test_a_verdict_seals_the_link_and_the_ratio_at_its_frozen_entry(tmp_path: Path) -> None:
    """THE SEAT. The ratio is struck at the CLOSE `log_verdict` freezes (44.93), never at the
    record's spot (11.33): on these legs the two give different ratios, so a seal reading the
    spot would show here."""
    link = read_underwrite("SMPL", root=_repo_with(tmp_path, "SMPL"))
    assert link is not None
    with Store(tmp_path / "t.db") as store:
        cid = _seed(store, _ident("SMPL", "SEC-SMPL", "0001702744"), close=12.0)
        entry = log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                            decided_at=datetime(2026, 6, 15, 10, 0), underwrite=link, **KW)
    base, bear = _legs("SMPL")
    assert entry.entry_price == 12.0
    assert entry.ratio_at_entry == pytest.approx((base - 12.0) / (12.0 - bear))
    assert (entry.underwrite_ref, entry.underwrite_commit, entry.underwrite_sha256) == (
        link.ref, link.commit, link.sha256)
    assert entry.no_underwrite_reason is None and entry.ratio_at_entry_undefined is None


def test_a_ratio_undefined_at_the_entry_seals_the_recipes_reason(tmp_path: Path) -> None:
    """Entered BELOW the bear leg the risk is undefined: the seal is None WITH the recipe's own
    reason, never a number and never a silent None."""
    link = read_underwrite("SMPL", root=_repo_with(tmp_path, "SMPL"))
    assert link is not None
    _base, bear = _legs("SMPL")
    with Store(tmp_path / "t.db") as store:
        cid = _seed(store, _ident("SMPL", "SEC-SMPL", "0001702744"), close=round(bear - 1, 2))
        entry = log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                            decided_at=datetime(2026, 6, 15, 10, 0), underwrite=link, **KW)
    assert entry.ratio_at_entry is None
    assert "risk undefined" in (entry.ratio_at_entry_undefined or "")


def test_no_record_and_no_reason_is_refused_and_a_reason_is_sealed(tmp_path: Path) -> None:
    """The refusal and its negative pin, at the seat: nothing is written without one or the other,
    and a stated reason is sealed into the row."""
    with Store(tmp_path / "t.db") as store:
        cid = _seed(store, _ident("ACME", "SEC-ACME", "0000000001"))
        with pytest.raises(LedgerError, match="no live underwrite record"):
            log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 15, 10, 0), underwrite=None, **KW)
        with pytest.raises(LedgerError, match="no live underwrite record"):
            log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 15, 10, 0), underwrite=None,
                        no_underwrite_reason="   ", **KW)
        assert list(store.iter_ledger()) == []
        entry = log_verdict(store, candidate_id=cid, verdict=Verdict.AVOID_TERMINAL,
                            decided_at=datetime(2026, 6, 15, 10, 0), underwrite=None,
                            no_underwrite_reason="terminal call, no grid", **KW)
    assert entry.no_underwrite_reason == "terminal call, no grid"
    assert entry.underwrite_ref is None and entry.ratio_at_entry is None


def test_a_reason_beside_a_live_record_is_refused(tmp_path: Path) -> None:
    link = read_underwrite("SMPL", root=_repo_with(tmp_path, "SMPL"))
    with Store(tmp_path / "t.db") as store:
        cid = _seed(store, _ident("SMPL", "SEC-SMPL", "0001702744"), close=12.0)
        with pytest.raises(LedgerError, match="no reason for logging without one applies"):
            log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 15, 10, 0), underwrite=link,
                        no_underwrite_reason="x", **KW)


def test_a_record_with_no_horizon_loads_and_is_refused_only_at_the_decision(
    tmp_path: Path,
) -> None:
    """IT's committed record states no horizon. It LOADS — read, hashed, its recipe re-run (#762:
    refusing at load once made `run_recipe` refuse every R1 record) — and the decision refuses."""
    link = read_underwrite("IT", root=_repo_with(tmp_path, "IT"))
    assert link is not None and link.horizon_years is None
    assert link.ratio_at(140.19)[0] is not None
    with Store(tmp_path / "t.db") as store:
        cid = _seed(store, _ident("IT", "SEC-IT", "0000749251"), close=141.06)
        with pytest.raises(LedgerError, match="states no horizon"):
            log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 15, 10, 0), underwrite=link, **KW)
        assert list(store.iter_ledger()) == []


def test_a_record_whose_bytes_are_not_the_commits_is_refused(tmp_path: Path) -> None:
    """A seal names a commit and a hash; an edited or uncommitted record would name a commit that
    does not hold the bytes hashed. Both refuse; a clean one (above) does not."""
    repo = _repo_with(tmp_path, "SMPL")
    p = repo / "scenarios" / "SMPL.json"
    p.write_text(p.read_text().replace('"analyst"', '"analyst" ', 1))
    with pytest.raises(LedgerError, match="differs from its blob"):
        read_underwrite("SMPL", root=repo)
    shutil.copy(ROOT / "scenarios" / "IT.json", repo / "scenarios" / "IT.json")
    with pytest.raises(LedgerError, match="is not in the commit"):
        read_underwrite("IT", root=repo)


# ─── 2. ORIGIN AND BOOK ───────────────────────────────────────────────────────────────────────

def test_a_screen_row_names_its_run_and_its_book(tmp_path: Path) -> None:
    """Every committed screen row carries sleeve None and no origin_ref; a new one names both. The
    book is stamped, so the book's vocabulary applies: a screen PASS is refused (overshoot records
    BUY and AVOID_TERMINAL), where untagged it was sealed into a book that records none."""
    with Store(tmp_path / "t.db") as store:
        cid = _seed(store, _ident("ACME", "SEC-ACME", "0000000001"))
        with pytest.raises(LedgerError, match="records"):
            log_verdict(store, candidate_id=cid, verdict=Verdict.PASS,
                        decided_at=datetime(2026, 6, 15, 10, 0), **NO_RECORD, **KW)
        entry = log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                            decided_at=datetime(2026, 6, 15, 10, 0), **NO_RECORD, **KW)
    assert (entry.origin, entry.sleeve) == ("screen", "overshoot")
    assert entry.origin_ref == OriginRef(kind="screen_run", id=cid,
                                         screen_run_at=datetime(2026, 6, 12, 12, 0),
                                         screens_fired=("screen_2",))


def test_a_followed_row_names_its_follow_entry_or_is_refused(tmp_path: Path) -> None:
    ident = _ident("LLY", "SEC-LLY", "0000059478")
    with Store(tmp_path / "t.db") as store:
        store.upsert_security(ident)
        store.write_prices([PriceBar(internal_id=ident.internal_id, bar_date=date(2026, 6, 12),
                                     open=1.0, high=1.0, low=1.0, close=800.0, volume=1.0,
                                     source="polygon-grouped")])
        kw: dict[str, Any] = {**KW, "candidate_id": "LLY", "identity": ident, "origin": "followed",
              "sleeve": "quality", "verdict": Verdict.BUY,
              "decided_at": datetime(2026, 6, 15, 10, 0), **NO_RECORD}
        with pytest.raises(LedgerError, match="names its follow entry"):
            log_verdict(store, **kw)
        entry = log_verdict(store, **kw, origin_ref=follow_origin("LLY", date(2026, 8, 21)))
    assert entry.origin_ref is not None
    assert (entry.origin_ref.kind, entry.origin_ref.id, entry.origin_ref.followed_since) == (
        "follow_entry", "LLY", date(2026, 8, 21))


def test_the_cli_reads_followed_since_from_the_committed_follow_file() -> None:
    """The follow entry's date comes from the DATED reader of the committed file."""
    from vinci import cli
    from vinci.config import Config
    ref = cli._follow_origin(Config(data_dir=ROOT / "data"), "LLY")
    assert (ref.kind, ref.id, ref.followed_since) == ("follow_entry", "LLY", date(2026, 8, 21))


def test_no_committed_row_carries_a_new_field_and_every_one_still_loads() -> None:
    """ADDITIVE: the 10 committed rows load as they are, none re-serializes with a field of this
    change (each is written only when set), and X-GOOGL keeps no void code."""
    new = {"origin_ref", "underwrite_commit", "underwrite_sha256", "ratio_at_entry_undefined",
           "no_underwrite_reason", "void_reason_code"}
    rows = _committed()
    assert len(rows) == 10
    for r in rows:
        assert not new & set(json.loads(r.model_dump_json())), r.entry_id
    (x,) = [r for r in rows if r.event == EVENT_VOID]
    assert (x.entry_id, x.void_reason_code) == ("X-GOOGL", None)


# ─── 3. PRE-REGISTERED VOID REASONS ───────────────────────────────────────────────────────────

def test_a_void_outside_the_registered_reasons_is_refused_before_anything(tmp_path: Path) -> None:
    from tests.test_ledger_void import _store, _void
    with _store(tmp_path / "s") as store:
        before = len(list(store.iter_ledger()))
        with pytest.raises(LedgerError, match="A change of mind is a CLOSE"):
            _void(store, reason_code="change_of_mind")
        # BEFORE ANYTHING: the ground is asked first, ahead of whether the decision even exists
        with pytest.raises(LedgerError, match="not pre-registered"):
            _void(store, entry_id="V-NOPE", reason_code="change_of_mind")
        assert len(list(store.iter_ledger())) == before
        row = _void(store, reason_code="wrong_identity")
    assert row.void_reason_code == "wrong_identity"
    assert {"data_error_at_entry", "wrong_instrument", "wrong_identity"} == VOID_REASONS


def test_the_schema_refuses_an_unregistered_code_and_a_code_off_a_void_row() -> None:
    (x,) = [r for r in _committed() if r.event == EVENT_VOID]
    with pytest.raises(ValueError, match="not pre-registered"):
        LedgerEntry.model_validate({**x.model_dump(), "void_reason_code": "change_of_mind"})
    decision = next(r for r in _committed() if r.event is None)
    with pytest.raises(ValueError, match="void_reason_code"):
        LedgerEntry.model_validate({**decision.model_dump(), "void_reason_code": "wrong_identity"})


def test_the_void_command_refuses_without_a_registered_reason(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Refused before the ledger is even read: the parser offers only the three, and the command
    refuses a Namespace without one."""
    import argparse

    from vinci import cli
    ns = argparse.Namespace(entry_id="V-X", reason="r", ruled_on="2026-11-13", dry_run=True,
                            void_reason=None)
    assert cli._cmd_void_decision(ns) == 1
    assert "A change of mind is a CLOSE" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["void-decision", "V-X", "--reason", "r", "--ruled-on",
                                       "2026-11-13", "--void-reason", "change_of_mind"])


# ─── 3 + 4, END TO END ON THE COMMITTED LEDGER ────────────────────────────────────────────────

def _score_committed(tmp_path: Path, as_of: date) -> tuple[list[VerdictScore], Any]:
    from tests.test_per_row_benchmark import _committed_ledger_store
    from vinci.monitor import read_assignments_file
    asg = read_assignments_file(ROOT / "data" / "monitor" / "benchmark_assignments.json")
    with _committed_ledger_store(tmp_path / f"{as_of}.db") as store:
        return score_ledger(store, as_of=as_of, dividends=no_dividends, splits=no_splits,
                            assignments=asg)


def test_smpl_is_the_one_live_reaffirmation() -> None:
    """THE LIVE CASE, on the committed ledger: SMPL's second BUY (entry 2026-08-04) entered the
    first's window (2026-07-20 → 2027-01-16; closed 07-24 and still scored, the 2026-08-12 ruling).
    No other row reaffirms anything."""
    got = reaffirmations(_committed())
    assert {k: v.entry_id for k, v in got.items()} == {
        "V-SMPL-screen2-20260729": "V-SMPL-screen2-20260706"}


def test_the_committed_report_counts_smpl_once_and_prints_the_void_beside_the_curve(
    tmp_path: Path,
) -> None:
    """E2E: committed ledger → score → markdown. Today the screen book holds IT, SMPL (07-06) and
    VRRM pending — 3, where it held 4 — and the reaffirmation and X-GOOGL's sealed result each
    print once, on their own lines."""
    scores, rep = _score_committed(tmp_path, date(2026, 11, 13))
    assert rep.n_pending == 3
    assert "V-SMPL-screen2-20260729" not in {s.entry_id for s in scores}
    md = rep.to_markdown()
    assert md.count("V-SMPL-screen2-20260729") == 1 and "REAFFIRMATION" in md
    assert md.count("VOIDED by X-GOOGL") == 1
    void_line = md[md.index("**Voided**"):]
    assert "-15.58% vs SPY -2.51%" in void_line.split("\n", 2)[1]
    assert not any("VOIDED" in n for n in rep.row_notes)


def test_at_the_first_resolved_read_smpl_is_one_observation(tmp_path: Path) -> None:
    """On 2027-01-20 IT, SMPL (07-06) and VRRM have resolved: two BUY and one AVOID, and NOTHING is
    pending. Before this change the second SMPL BUY was still pending there (its 549-day horizon
    runs to 2028-02-04), and from that date it would have entered the spread as a third BUY."""
    _scores, rep = _score_committed(tmp_path, date(2027, 1, 20))
    assert (rep.n_resolved_buy, rep.n_resolved_avoid, rep.n_pending) == (2, 1, 0)


def _row(eid: str, iid: str, verdict: Verdict, entry: date, **kw: Any) -> LedgerEntry:
    return LedgerEntry(entry_id=eid, candidate_id=eid[2:], internal_id=iid, ticker=iid,
                       verdict=verdict, twin_call="t", entry_price=10.0, entry_price_as_of=entry,
                       thesis="t", kill_criteria="k", horizon_days=180,
                       confidence=Confidence.MEDIUM,
                       decided_at=datetime.combine(entry, datetime.min.time()), **kw)


@pytest.mark.parametrize(("second", "reaffirms"), [
    (_row("V-B", "SEC-A", Verdict.BUY, date(2026, 3, 1)), True),
    (_row("V-B", "SEC-A", Verdict.BUY, date(2026, 1, 1) + timedelta(days=180)), False),
    (_row("V-B", "SEC-A", Verdict.AVOID_TERMINAL, date(2026, 3, 1)), False),
    (_row("V-B", "SEC-OTHER", Verdict.BUY, date(2026, 3, 1)), False),
    (_row("V-B", "SEC-A", Verdict.BUY, date(2026, 3, 1), sleeve="quality",
          origin="followed"), False),
], ids=["inside-the-window", "on-the-horizon", "opposite-call", "other-name", "other-book"])
def test_only_a_same_call_inside_the_window_is_a_reaffirmation(
    second: LedgerEntry, reaffirms: bool,
) -> None:
    first = _row("V-A", "SEC-A", Verdict.BUY, date(2026, 1, 1))
    assert (second.entry_id in reaffirmations([first, second])) is reaffirms


def test_a_voided_first_call_leaves_the_second_an_observation() -> None:
    """A void ends the window from its ruling date: the second call is then the observation."""
    first = _row("V-A", "SEC-A", Verdict.BUY, date(2026, 1, 1))
    second = _row("V-B", "SEC-A", Verdict.BUY, date(2026, 3, 1))
    (x,) = [r for r in _committed() if r.event == EVENT_VOID]
    void = x.model_copy(update={"entry_id": "X-A", "voids_entry_id": "V-A", "ticker": "SEC-A",
                                "internal_id": "SEC-A", "ruled_on": date(2026, 2, 1)})
    assert reaffirmations([first, second]) and not reaffirmations([first, second, void])
    assert reaffirmations([first, second, void], as_of=date(2026, 1, 15))


# ─── 5. THE READING FLOOR ─────────────────────────────────────────────────────────────────────

def _scores(n_buy: int, n_avoid: int, sleeve: str = "overshoot") -> list[VerdictScore]:
    avoid = Verdict.AVOID_TERMINAL if sleeve == "overshoot" else Verdict.PASS
    return ([VerdictScore(f"V-B{i}", f"B{i}", Verdict.BUY, True, 0.10, 0.0, sleeve=sleeve,
                          origin="screen" if sleeve == "overshoot" else "followed")
             for i in range(n_buy)]
            + [VerdictScore(f"V-A{i}", f"A{i}", avoid, True, -0.05, 0.0, sleeve=sleeve,
                            origin="screen" if sleeve == "overshoot" else "followed")
               for i in range(n_avoid)])


def test_a_book_below_the_floor_prints_its_count_and_no_reading() -> None:
    rep = aggregate(_scores(2, 1) + _scores(1, 1, sleeve="quality"), cost_bps=25.0, n_pending=0)
    md = rep.to_markdown()
    book = md[md.index("## Per-sleeve curves"):md.index("## Machine-proposal")]
    assert "**overshoot** — BUY−AVOID_TERMINAL: 3 resolved" in book
    assert "**quality** — BUY−PASS: 2 resolved" in book
    assert "below the reading floor of 20" in book and "spread" not in book.split("_\n")[-1]
    # A DISPLAY RULE: every number is still computed
    assert rep.by_sleeve["overshoot"].spread == pytest.approx(0.15)
    assert rep.to_dict()["by_sleeve"]["quality"]["spread"] == pytest.approx(0.15)  # type: ignore[index]
    assert rep.to_dict()["reading_floor"] == READING_FLOOR == 20


def test_a_book_at_the_floor_is_read() -> None:
    md = aggregate(_scores(10, 10), cost_bps=25.0, n_pending=0).to_markdown()
    book = md[md.index("## Per-sleeve curves"):md.index("## Machine-proposal")]
    assert "BUY−AVOID_TERMINAL spread +15.0% (10 buy / 10 avoid_terminal resolved)" in book
    assert "below the reading floor" not in book.split("_\n")[-1]


def test_the_primary_line_is_never_withheld_and_states_its_count() -> None:
    """The primary metric is unchanged: its line prints the spread at any count (coordinator,
    2026-11-13: "it never withholds the primary BUY−AVOID line"), with its count against the
    floor beside it."""
    md = aggregate(_scores(2, 1), cost_bps=25.0, n_pending=0).to_markdown()
    assert "**BUY−AVOID spread (primary): +15.0%** (3 of 20 resolved)" in md


def test_a_sector_below_the_floor_prints_its_count_and_no_spread() -> None:
    """The per-sector cuts are curves too. Two per leg cleared the old `sufficient` rule; below
    the floor the sector prints its count, and above it the spread as before."""
    below = [VerdictScore(s.entry_id, s.ticker, s.verdict, True, s.name_return, 0.0,
                          sector="Tech") for s in _scores(2, 2)]
    md = aggregate(below, cost_bps=25.0, n_pending=0).to_markdown()
    assert "- Tech: 4 resolved (2 buy / 2 avoid) — below the reading floor of 20" in md
    above = [VerdictScore(s.entry_id, s.ticker, s.verdict, True, s.name_return, 0.0,
                          sector="Tech") for s in _scores(10, 10)]
    md = aggregate(above, cost_bps=25.0, n_pending=0).to_markdown()
    assert "- Tech: spread +15.0% (10 buy / 10 avoid)" in md



# ─── review round 0 (/code-review high) ───────────────────────────────────────────────────────

def test_every_underwrite_refusal_is_asked_before_the_paid_confirmation() -> None:
    """STRUCTURAL, as the edge-basis gate's pin: the confirmation draws ten paid syntheses, so the
    one refusal function runs before it — a reason beside a live record was first refused only at
    the write, after the spend."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    body = src[src.index("def _cmd_log_verdict"):]
    body = body[:body.index("\ndef ", 10)]
    assert body.index("require_underwrite(") < body.index("_confirm_seal(") < body.index(
        "= log_verdict(")


def test_the_reader_finds_the_record_from_a_subdirectory(tmp_path: Path) -> None:
    """Run from below the repository root, the record still exists — never read as absent."""
    repo = _repo_with(tmp_path, "SMPL")
    link = read_underwrite("SMPL", root=repo / "scenarios")
    assert link is not None and link.ref == "scenarios/SMPL.json"


def test_a_screen_candidate_refuses_a_passed_origin(tmp_path: Path) -> None:
    with Store(tmp_path / "t.db") as store:
        cid = _seed(store, _ident("ACME", "SEC-ACME", "0000000001"))
        with pytest.raises(LedgerError, match="would be dropped"):
            log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 15, 10, 0),
                        origin_ref=follow_origin("ACME", date(2026, 1, 1)), **NO_RECORD, **KW)


def test_a_ratio_with_no_reason_is_sealed_with_one(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """No committed record returns a None ratio without its reason, so the recipe is stood in
    by its own Result with both cleared: the seal still says why, never a silent None."""
    link = read_underwrite("SMPL", root=_repo_with(tmp_path, "SMPL"))
    assert link is not None
    rec = sc.read_record("SMPL", root=ROOT)
    blank = rec.model_copy(update={"result": rec.result.model_copy(
        update={"ratio": None, "ratio_undefined": None})})
    monkeypatch.setattr(sc, "run_recipe", lambda _r: blank)
    assert link.ratio_at(12.0) == (None, "the recipe returned no ratio and no reason")


def test_a_call_held_through_its_open_reaffirmation_is_still_held(tmp_path: Path) -> None:
    """PR-FEEDBACK ROUND 1. The still-held split asks which calls the book still HOLDS. SMPL's
    07-06 BUY was closed on 07-24, but the book holds SMPL through its 08-05 reaffirmation, which
    is open — so at the first resolved read only IT counts as closed, not IT and SMPL."""
    scores, rep = _score_committed(tmp_path, date(2027, 1, 20))
    assert {s.entry_id: s.closed for s in scores} == {
        "V-IT-screen2-20260706": True, "V-SMPL-screen2-20260706": False,
        "V-VRRM-screen2-20260617": False}
    assert rep.n_closed == 1 and rep.n_open_buy == 1
