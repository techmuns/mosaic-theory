"""A ledger write must reach the COMMITTED record, and a close must be writable at all.

TWO BREAKS IN ONE CHAIN, both measured on a copy of the committed tree before this landed:

1. `log-verdict` wrote to the working SQLite DB and stopped. The DB is a CACHE — the durable
   record is `data/snapshots/decision_ledger.jsonl`, and it is what `vinci monitor`, the frontend
   mirror and every fresh clone read (`_cmd_monitor` says so in its own docstring). After a ledger
   write the DB held 7 rows and the committed snapshot still held 6, byte-identical. The verdict
   reached no reader until somebody happened to run the weekly screen or the monthly score, both
   of which export only as a side effect of doing something else.

2. There was NO close command. `4f34c11` shipped the close-row schema, the readers
   (`monitor.close_rows` / `pair_closes`), the display and the id helper — everything except a
   writer. Both committed closes were hand-authored JSON: rows that reached an append-only record
   without passing a single guard.

These pin the write path end to end (the committed FILE, not the helper), every refusal, and the
class-level rule that a ledger-writing command exports.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import shutil
from datetime import date, datetime

import pytest

from vinci.config import Config
from vinci.ledger import LedgerError, close_position
from vinci.monitor import close_rows, decision_rows, pair_closes
from vinci.store import Store

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED_SNAPSHOTS = ROOT / "data" / "snapshots"

#: The open decision used throughout — read from the committed ledger, not invented.
OPEN_CANDIDATE = "SMPL-screen2-20260729"


@pytest.fixture
def tree(tmp_path: pathlib.Path) -> Config:
    """A COPY of the committed snapshot tree — the corpus, not a fixture built to shape."""
    data = tmp_path / "data"
    data.mkdir()
    shutil.copytree(COMMITTED_SNAPSHOTS, data / "snapshots")
    cfg = Config(data_dir=data)
    cfg.ensure_dirs()
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
    return cfg


def _ledger_rows(cfg: Config) -> list[dict[str, object]]:
    path = cfg.snapshots_dir / "decision_ledger.jsonl"
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def _close_args(**kw: object) -> argparse.Namespace:
    base = {"candidate_id": OPEN_CANDIDATE, "exit_price": 10.86, "as_of": "2026-08-11",
            "reason": "closed for the test"}
    return argparse.Namespace(**{**base, **kw})


# --------------------------------------------------------------------------------------------
# The committed FILE is the assertion, not the store
# --------------------------------------------------------------------------------------------

def test_closing_a_position_reaches_the_committed_snapshot(
    tree: Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE CHAIN PIN. Asserted on the JSONL the monitor and the frontend actually read — a
    store-level assertion would have passed throughout the entire period this was broken."""
    from vinci import cli

    monkeypatch.setattr(cli, "get_config", lambda: tree)
    before = len(_ledger_rows(tree))
    assert cli._cmd_close_position(_close_args()) == 0
    after = _ledger_rows(tree)
    assert len(after) == before + 1, (
        f"the close did not reach data/snapshots/decision_ledger.jsonl ({before} → {len(after)}) "
        f"— the working DB is a cache; the snapshot is the durable record")


def test_logging_a_verdict_reaches_the_committed_snapshot(
    tree: Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same pin for the other writer, exercised through `_export_ledger` directly: the full
    log-verdict path needs a resolver and a candidate record, but the EXPORT is the half that was
    missing and it is the half asserted here."""
    from vinci import cli

    monkeypatch.setattr(cli, "get_config", lambda: tree)
    with Store(tree.db_path) as store:
        rows = list(store.iter_ledger())
        store.append_ledger(rows[0].model_copy(update={"entry_id": "V-EXPORT-PROBE"}))
    assert len(_ledger_rows(tree)) == len(rows), "fixture broken: the snapshot changed too early"
    cli._export_ledger(tree, "probe")
    ids = {json.loads(r["payload"])["entry_id"] if isinstance(r["payload"], str)
           else r["payload"]["entry_id"] for r in _ledger_rows(tree)}
    assert "V-EXPORT-PROBE" in ids, "the export did not flush the ledger to the committed snapshot"


def test_the_close_pairs_with_its_decision_and_carries_its_provenance(tree: Config) -> None:
    """A close exists to be PAIRED. `pair_closes` refuses an unpairable or duplicated close, so a
    close that does not pair breaks every later monitor run at a point far from the command that
    wrote it."""
    with Store(tree.db_path) as store:
        # RELATIVE, NOT ABSOLUTE (2026-08-28). This counted decisions against a hardcoded 4 while
        # claiming to test that a close is not counted as one. Recording a real 5th verdict — the
        # first quality-book position — reddened it, and the failure message named the wrong cause.
        # The property is that writing a CLOSE leaves the decision count UNCHANGED; pin that.
        before = len(decision_rows([json.loads(r.model_dump_json()) for r in store.iter_ledger()]))
        close = close_position(
            store, candidate_id=OPEN_CANDIDATE, exit_price=10.86,
            exit_price_as_of=date(2026, 8, 11), reason="closed for the test",
            closed_at=datetime(2026, 8, 12))
        raw = [json.loads(r.model_dump_json()) for r in store.iter_ledger()]

    assert close.entry_id == f"C-{OPEN_CANDIDATE}"
    assert close.closes_entry_id == f"V-{OPEN_CANDIDATE}"
    # provenance COPIED, so the realized view can pair and price it
    assert (close.ticker, close.verdict, close.entry_price) == ("SMPL", close.verdict, 11.33)
    assert close.machine_proposal is None and close.disposition is None
    paired = pair_closes(raw)
    assert len(paired) == len(close_rows(raw)), "the close did not pair"
    assert len(decision_rows(raw)) == before, "a close was counted as a decision row"


def test_facts_are_cleared_because_they_belong_to_the_decision(tree: Config) -> None:
    """MUTATION FINDING: the first version of this assertion tested NOTHING.

    It asserted `close.facts == {}` against the committed corpus — where **no decision carries a
    fact at all** (verified: all six rows have zero). Removing the clear from the writer therefore
    left the test green. A check that cannot fail is not a check.

    SYNTHETIC, narrowly and by necessity: the corpus cannot supply a fact-bearing decision, and the
    schema REFUSES facts on a close row, so without the clear `close_position` would either write a
    row that violates its own schema or raise. `model_copy` does not re-validate, so the clear is
    the only thing standing between a fact-bearing decision and an invalid committed close.
    """
    from vinci.schemas.ledger import LedgerFact

    fact = LedgerFact(value=1.0, unit="x", basis="test fact", source="10-K 0000000000-00-000000")
    with Store(tree.db_path) as store:
        rows = list(store.iter_ledger())
        decision = next(r for r in rows if r.candidate_id == OPEN_CANDIDATE and r.event is None)
        store.append_ledger(decision.model_copy(update={
            "entry_id": "V-FACTBEARER", "candidate_id": "FACTBEARER", "facts": {"leverage": fact}}))
        seeded = next(r for r in store.iter_ledger() if r.entry_id == "V-FACTBEARER")
        assert seeded.facts, "fixture broken: the seeded decision carries no fact to clear"

        close = close_position(
            store, candidate_id="FACTBEARER", exit_price=10.0,
            exit_price_as_of=date(2026, 8, 11), reason="r", closed_at=datetime(2026, 8, 12))

    assert close.facts == {}, (
        f"facts rode along onto the close: {sorted(close.facts)}. They belong to the decision they "
        f"justified — on a close they read as a second, later-dated underwrite of the same call, "
        f"which is why the schema refuses them outright.")


# --------------------------------------------------------------------------------------------
# Every refusal, and none of them writes
# --------------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("label", "kw", "expect"),
    [
        ("unknown candidate", {"candidate_id": "NOPE-1"}, "nothing to close"),
        ("exit before entry", {"as_of": "2020-01-01"}, "cannot close before it opened"),
        # OPERATOR REVIEW P1 ON #417, covered THROUGH THE CLI as asked. `model_copy(update=...)`
        # runs no validators and `append_ledger` only serialized, so this exact invocation wrote a
        # schema-invalid row into an APPEND-ONLY record, printed success, and made every later
        # `iter_ledger()` raise.
        ("negative exit price", {"exit_price": -1.0}, "must be positive"),
        ("zero exit price", {"exit_price": 0.0}, "must be positive"),
    ],
    ids=["unknown-candidate", "exit-before-entry", "negative-exit-price", "zero-exit-price"],
)
def test_a_refused_close_writes_nothing(
    tree: Config, monkeypatch: pytest.MonkeyPatch, label: str, kw: dict[str, object], expect: str,
) -> None:
    from vinci import cli

    monkeypatch.setattr(cli, "get_config", lambda: tree)
    before = _ledger_rows(tree)
    assert cli._cmd_close_position(_close_args(**kw)) == 1, f"{label} was accepted"
    assert _ledger_rows(tree) == before, f"{label} was refused but still wrote to the record"
    # AND THE RECORD IS STILL READABLE. This is the half that made the P1 severe: the bad row was
    # written, so the NEXT read of the ledger raised — one flag rendering the append-only record
    # unusable, with no way to remove the row.
    with Store(tree.db_path) as store:
        assert len(list(store.iter_ledger())) == len(before)


def test_the_store_refuses_an_invalid_row_from_any_writer(tree: Config) -> None:
    """THE BACKSTOP. Validating inside `close_position` fixes the caller that had the hole; this
    covers every OTHER writer, including ones not yet written.

    A `LedgerEntry` argument LOOKS like proof of validity and is not — `model_copy(update=...)`
    skips every model validator — so `append_ledger` re-validates on the way in. Cheap here (the
    ledger is tens of rows) and it is the only place that covers all writers at once."""
    with Store(tree.db_path) as store:
        decision = next(r for r in store.iter_ledger() if r.event is None)
        invalid = decision.model_copy(update={
            "entry_id": "C-BYPASS", "event": "CLOSE", "closes_entry_id": decision.entry_id,
            "exit_price": -5.0, "exit_price_as_of": decision.entry_price_as_of, "reason": "r"})
        with pytest.raises(ValueError, match="append-only"):
            store.append_ledger(invalid)
        assert not [r for r in store.iter_ledger() if r.entry_id == "C-BYPASS"]


def test_a_second_close_is_refused(tree: Config) -> None:
    """`pair_closes` raises on a duplicated close, so the damage from a second one surfaces far
    from the command that caused it. Refused at the writer instead."""
    with Store(tree.db_path) as store:
        close_position(store, candidate_id=OPEN_CANDIDATE, exit_price=10.86,
                       exit_price_as_of=date(2026, 8, 11), reason="first",
                       closed_at=datetime(2026, 8, 12))
        with pytest.raises(LedgerError, match="already closed"):
            close_position(store, candidate_id=OPEN_CANDIDATE, exit_price=9.0,
                           exit_price_as_of=date(2026, 8, 11), reason="second",
                           closed_at=datetime(2026, 8, 12))


def test_a_close_without_a_reason_is_refused_in_the_operators_words(
    tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """MUTATION FINDING: asserting only the exit code pinned NOTHING here.

    Since `close_position` re-validates (the P1 fix), the schema refuses a blank reason on its own
    — so deleting the CLI's check left the command still returning 1 and the test still green. The
    CLI guard's actual contribution is not the refusal, it is the MESSAGE: the operator gets the
    rule in one line instead of a pydantic traceback quoting the whole row. That is what is pinned.
    """
    from vinci import cli

    monkeypatch.setattr(cli, "get_config", lambda: tree)
    before = _ledger_rows(tree)
    assert cli._cmd_close_position(_close_args(reason="   ")) == 1
    out = capsys.readouterr().out
    assert "--reason is required" in out, (
        f"a blank reason was refused, but not in terms the operator can act on — they got a "
        f"validation dump instead of the rule:\n{out}")
    assert _ledger_rows(tree) == before


def test_an_already_closed_position_cannot_be_closed_through_the_cli(
    tree: Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The committed ledger already holds two closed decisions — real corpus, not a setup step."""
    from vinci import cli

    monkeypatch.setattr(cli, "get_config", lambda: tree)
    before = _ledger_rows(tree)
    assert cli._cmd_close_position(_close_args(candidate_id="IT-screen2-20260706")) == 1
    assert _ledger_rows(tree) == before


# --------------------------------------------------------------------------------------------
# The class-level rule
# --------------------------------------------------------------------------------------------

def test_every_ledger_writing_command_flushes_to_the_committed_snapshot() -> None:
    """THE RULE, MADE MECHANICAL. `log-verdict` shipped without an export and nothing noticed for
    months, because the defect is INVISIBLE to any test that reads the store.

    Any `_cmd_*` in the CLI that reaches a ledger writer must also call `_export_ledger`. AST-scoped
    per function so a writer added to a NEW command fails here rather than being discovered when a
    verdict silently fails to appear on the site.
    """
    tree_ast = ast.parse((ROOT / "vinci" / "cli.py").read_text())
    writers = {"log_verdict", "close_position", "append_ledger"}
    offenders: list[str] = []
    for fn in ast.walk(tree_ast):
        if not isinstance(fn, ast.FunctionDef) or not fn.name.startswith("_cmd_"):
            continue
        called = {
            n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            for n in ast.walk(fn) if isinstance(n, ast.Call)
        }
        if called & writers and "_export_ledger" not in called:
            offenders.append(f"{fn.name} (line {fn.lineno}) calls {sorted(called & writers)}")
    assert not offenders, (
        "CLI command(s) write to the ledger without flushing it to the committed snapshot:\n  "
        + "\n  ".join(offenders)
        + "\nThe working DB is a cache; `data/snapshots/decision_ledger.jsonl` is what the "
          "monitor, the frontend and a fresh clone read.")
