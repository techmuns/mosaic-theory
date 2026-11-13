"""A SEAL IS THE PRICE THE DECISION WAS MADE AT (TeamNostra fix request 2, RF-D7, 2026-11-09).

THE DEFECT, reproduced on main 6fbbb4a2 before the fix: `log_verdict` asked the store for the
latest close on or before the reference date with ``staleness_days``, and `close_as_of` marked an
older bar STALE — but the seal checked `is_known`, which is TRUE for a stale value, so the
parameter had no effect. A close 31 days old was sealed (decided 2026-10-31, entry 20.0 as of
2026-09-30), and the row's forward clock, scored from `entry_price_as_of`, started 31 days before
the decision. LIVE on the committed ledger: GOOGL's BUY (`V-GOOGL`) was decided 2026-08-28 on the
2026-08-14 close.

THE FIX refuses a stale close at sealing: a decision is logged at the price it was made at, or
not at all — refresh the bars and log again. The committed rows are never rewritten (the ledger is
append-only); how GOOGL's is read is the operator's ruling, proposed in the PR, not made here.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from tests.test_ledger import _candidate, _ident
from vinci.config import Config
from vinci.ledger.workflow import LedgerError, log_verdict
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
#: the CLI's own bound (`Config.price_staleness_days`), so the corpus pin reads the rule as run
STALENESS: int = Config.model_fields["price_staleness_days"].default


class _Sic:
    def sic_for(self, cik: int | str) -> tuple[str | None, str | None]:
        return "7372", None


def _seal(tmp_path: Path, *, bar: date) -> tuple[Store, str]:
    """A store holding one screened candidate and ONE close, on ``bar`` — the latest any seal on
    or before the decision date can read."""
    ident = _ident("SEAL", "SEC-0000000009-SEAL", "0000000009")
    store = Store(tmp_path / "s.db")
    store.upsert_security(ident)
    cand = _candidate(ident)
    store.save_candidate(cand)
    store.write_prices([PriceBar(internal_id=ident.internal_id, bar_date=bar, open=20.0,
                                 high=20.0, low=20.0, close=20.0, volume=1e6,
                                 source="polygon-grouped")])
    return store, cand.candidate_id


def _log(store: Store, cid: str, decided: datetime) -> LedgerEntry:
    return log_verdict(
        store, resolver=_Sic(), candidate_id=cid, verdict=Verdict.BUY, twin_call="t",
        thesis="t", kill_criteria="k", horizon_days=180, confidence=Confidence.MEDIUM,
        decided_at=decided, reference_date=decided.date(), staleness_days=STALENESS,
        underwrite=None, no_underwrite_reason="fixture: no underwrite record")


def test_a_close_a_month_old_is_never_sealed(tmp_path: Path) -> None:
    """THE AUDIT'S CASE: on main this sealed 20.0 as of 2026-09-30 for a 2026-10-31 decision."""
    decided = datetime(2026, 10, 31, 12)
    store, cid = _seal(tmp_path, bar=date(2026, 9, 30))
    with store:
        with pytest.raises(LedgerError, match="31 days old") as err:
            _log(store, cid, decided)
        assert "refresh EOD bars" in str(err.value)
        assert "`vinci refresh SEAL --start 2026-09-30 --end 2026-10-31`" in str(err.value)
        assert list(store.iter_ledger()) == []          # nothing reached the append-only record


def test_a_close_inside_the_bound_is_sealed_as_before(tmp_path: Path) -> None:
    """THE NEGATIVE PIN, at the edge: a Friday close for a Wednesday decision is 5 days old."""
    decided = datetime(2026, 10, 7, 12)
    store, cid = _seal(tmp_path, bar=date(2026, 10, 2))
    with store:
        entry = _log(store, cid, decided)
    assert entry.entry_price == 20.0 and entry.entry_price_as_of == date(2026, 10, 2)


def _committed_decisions() -> list[dict[str, object]]:
    rows = [json.loads(json.loads(ln)["payload"]) for ln in
            (ROOT / "data/snapshots/decision_ledger.jsonl").read_text().splitlines() if ln.strip()]
    return [r for r in rows if r.get("event") is None]


@pytest.mark.parametrize("row", _committed_decisions(), ids=lambda r: str(r["entry_id"]))
def test_every_committed_seal_read_against_the_rule(tmp_path: Path, row: dict[str, object]) -> None:
    """THE CORPUS: each of the five committed decisions, sealed again at its own entry date and
    decided at its own `decided_at`. Four are 1–4 days old and seal; GOOGL's is 14 days old and is
    the one the rule refuses. The rows themselves are never touched — this re-runs the rule on
    their dates in a scratch store."""
    bar = date.fromisoformat(str(row["entry_price_as_of"]))
    decided = datetime.fromisoformat(str(row["decided_at"]))
    store, cid = _seal(tmp_path, bar=bar)
    age = (decided.date() - bar).days
    with store:
        if row["entry_id"] == "V-GOOGL":
            assert age == 14
            with pytest.raises(LedgerError, match="14 days old"):
                _log(store, cid, decided)
        else:
            assert age <= STALENESS
            _log(store, cid, decided)


def test_a_back_dated_reference_cannot_seal_an_old_close(tmp_path: Path) -> None:
    """REVIEW ROUND 0: `--ref` set back to the old close's own date made that close fresh against
    the reference, while `decided_at` was today — GOOGL's 08-14 close sealed on 2026-11-10, a
    forward clock 88 days before the decision. Held to the decision too."""
    store, cid = _seal(tmp_path, bar=date(2026, 8, 14))
    decided = datetime(2026, 11, 10, 9)
    with store:
        with pytest.raises(LedgerError, match="88 days before this verdict is logged"):
            log_verdict(
                store, resolver=_Sic(), candidate_id=cid, verdict=Verdict.BUY, twin_call="t",
                thesis="t", kill_criteria="k", horizon_days=180, confidence=Confidence.MEDIUM,
                decided_at=decided, reference_date=date(2026, 8, 14), staleness_days=STALENESS,
                underwrite=None, no_underwrite_reason="fixture: no underwrite record")
        assert list(store.iter_ledger()) == []


def test_a_decision_logged_a_day_after_its_reference_still_seals(tmp_path: Path) -> None:
    """THE NEGATIVE PIN: a verdict decided on the 2026-10-02 close and logged the next morning."""
    store, cid = _seal(tmp_path, bar=date(2026, 10, 2))
    with store:
        entry = log_verdict(
            store, resolver=_Sic(), candidate_id=cid, verdict=Verdict.BUY, twin_call="t",
            thesis="t", kill_criteria="k", horizon_days=180, confidence=Confidence.MEDIUM,
            decided_at=datetime(2026, 10, 3, 9), reference_date=date(2026, 10, 2),
            staleness_days=STALENESS,
            underwrite=None, no_underwrite_reason="fixture: no underwrite record")
    assert entry.entry_price_as_of == date(2026, 10, 2)
