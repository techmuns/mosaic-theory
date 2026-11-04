"""The web's realized return is the one the monitor day carries, never a quotient of its own.

STATE §5.0 row 40. `frontend/lib/snapshots.js` derived a closed position's realized return as
``exit_price / entry_price − 1`` from the ledger's two frozen prices. `vinci.monitor.pair_closes`
stopped using that formula on 2026-10-29 (#855): the sealed entry sits on the ENTRY date's split
basis and the exit on its own, so a split between them reads a flat 2-for-1 as −50%. The python
side puts the entry on the exit's basis through Polygon's splits reference, which the browser has
no source for; the realized row a monitor day carries is the one surface that has read it. So the
web reads that row by ``close_id``, and shows NO return until a close appears on a monitor day.

EXECUTED against the REAL module: node imports `snapshots.js` itself, with ``fetch`` stubbed onto
the committed `data/snapshots/decision_ledger.jsonl` and `frontend/monitor/` — the files the deploy
copies — so each pin reads `getLedger()` as the decision log and the dossier card do. The split
case is the committed SMPL close with its sealed entry put on a pre-split basis (21.84, a 2-for-1
of the committed 10.92); its monitor row is the committed one, on the exit's basis.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
from typing import Any

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIB = ROOT / "frontend" / "lib" / "snapshots.js"
LEDGER = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
MONITOR = ROOT / "frontend" / "monitor"


def _closed(overrides: dict[str, str | None]) -> dict[str, Any]:
    """``{entry_id: closed}`` from `getLedger()`, the committed files served unless overridden
    (a value of None serves a 404)."""
    script = """
import { readFile } from 'node:fs/promises';
const MAP = { './snapshots/': __SNAP__, './monitor/': __MON__ };
const OVERRIDES = __OVR__;
globalThis.fetch = async (p) => {
  const path = String(p);
  const miss = { ok: false, status: 404, text: async () => '' };
  if (path in OVERRIDES) {
    const body = OVERRIDES[path];
    return body === null ? miss : { ok: true, status: 200, text: async () => body };
  }
  for (const [prefix, dir] of Object.entries(MAP)) {
    if (path.startsWith(prefix)) {
      try {
        const buf = await readFile(dir + '/' + path.slice(prefix.length), 'utf8');
        return { ok: true, status: 200, text: async () => buf };
      } catch { return miss; }
    }
  }
  return miss;
};
const m = await import(__LIB__);
const led = await m.getLedger();
console.log(JSON.stringify(Object.fromEntries(
  led.entries.filter((e) => e.closed).map((e) => [e.entryId, e.closed]))));
"""
    for key, val in (("__SNAP__", str(LEDGER.parent)), ("__MON__", str(MONITOR)),
                     ("__OVR__", overrides), ("__LIB__", str(LIB))):
        script = script.replace(key, json.dumps(val))
    proc = subprocess.run(["node", "--input-type=module", "-e", script],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        if "not found" in proc.stderr.lower() and "node" in proc.stderr.lower():
            pytest.skip("node unavailable")
        raise AssertionError(f"the real module failed to execute: {proc.stderr.strip()}")
    out: dict[str, Any] = json.loads(proc.stdout)
    return out


def _latest_realized() -> dict[str, dict[str, Any]]:
    latest = json.loads((MONITOR / "index.json").read_text())["latest"]
    day = json.loads((MONITOR / f"{latest}.json").read_text())
    return {r["close_id"]: r for r in day.get("realized", [])}


def _ledger_with_sealed_entry(entry_id: str, price: float) -> str:
    """The committed ledger, one decision row's sealed entry price replaced (row and payload)."""
    lines = []
    for line in LEDGER.read_text().splitlines():
        row = json.loads(line)
        payload = json.loads(row["payload"])
        if payload.get("entry_id") == entry_id:
            row["entry_price"] = payload["entry_price"] = price
            row["payload"] = json.dumps(payload)
        lines.append(json.dumps(row))
    return "\n".join(lines) + "\n"


def test_a_close_across_a_split_reads_the_monitor_days_return() -> None:
    """THE RED. SMPL's sealed entry on a pre-split basis (21.84, a 2-for-1 of 10.92) closes at
    10.53. Main's web divided across the split: 10.53 / 21.84 − 1 = −51.8%. The monitor day's
    row, on the exit's basis, says −3.57%, and that is what the page shows."""
    realized = _latest_realized()["C-SMPL-screen2-20260706"]
    closed = _closed({"./snapshots/decision_ledger.jsonl":
                      _ledger_with_sealed_entry("V-SMPL-screen2-20260706", 21.84)})
    got = closed["V-SMPL-screen2-20260706"]["realizedReturn"]
    assert got == realized["realized_return"], (
        f"the web read {got}, not the monitor day's {realized['realized_return']}")
    assert abs(got - (10.53 / 21.84 - 1)) > 0.4, "the return still divides across the split"


def test_a_close_no_monitor_day_carries_yet_shows_no_return() -> None:
    """THE RED. With the latest monitor day before the closes (2026-07-20; IT closed 2026-07-21,
    SMPL 2026-07-22), no realized row exists, so the page shows none — main computed one."""
    index = json.loads((MONITOR / "index.json").read_text())
    early = json.dumps({**index, "latest": "2026-07-20"})
    assert not json.loads((MONITOR / "2026-07-20.json").read_text()).get("realized"), (
        "the early day already carries closes")
    closed = _closed({"./monitor/index.json": early})
    assert closed, "the closes themselves vanished — only their return should"
    for entry_id, cl in closed.items():
        assert cl["realizedReturn"] is None, f"{entry_id}: {cl['realizedReturn']} computed"
        assert cl["exitPrice"] is not None, f"{entry_id}: the close's own facts were lost"


def test_no_monitor_history_shows_no_return() -> None:
    """(−) No monitor history committed: the closes stay, with no return."""
    closed = _closed({"./monitor/index.json": None})
    assert closed and all(cl["realizedReturn"] is None for cl in closed.values()), closed


def test_the_committed_closes_read_their_monitor_rows() -> None:
    """(+) End to end on the committed files: IT and SMPL show exactly the latest monitor day's
    realized return. No committed close spans a split, so main showed the same numbers — this is
    the fence that the read changes nothing on the deployed page today."""
    realized = _latest_realized()
    closed = _closed({})
    assert set(closed) == {r["entry_id"] for r in realized.values()}, (sorted(closed), realized)
    for row in realized.values():
        assert closed[row["entry_id"]]["realizedReturn"] == row["realized_return"], row
        assert closed[row["entry_id"]]["closeEntryId"] == row["close_id"]


def test_a_realized_row_naming_another_position_is_not_read() -> None:
    """(−) The guard: a monitor row whose ``close_id`` matches but whose ``entry_id`` is another
    position's is a broken pair. That close shows no return rather than the other position's;
    the close beside it, intact, still reads its own."""
    index = json.loads((MONITOR / "index.json").read_text())
    day = json.loads((MONITOR / f"{index['latest']}.json").read_text())
    for r in day.get("realized", []):
        if r["close_id"] == "C-SMPL-screen2-20260706":
            r["entry_id"] = "V-IT-screen2-20260706"
    closed = _closed({f"./monitor/{index['latest']}.json": json.dumps(day)})
    assert closed["V-SMPL-screen2-20260706"]["realizedReturn"] is None
    assert closed["V-IT-screen2-20260706"]["realizedReturn"] == _latest_realized()[
        "C-IT-screen2-20260706"]["realized_return"]


def test_a_real_split_close_shows_what_pair_closes_derives() -> None:
    """THE RED, ON REAL DATA. MNST split 2-for-1 on 2026-08-11 (Polygon's splits reference,
    `tests/fixtures/realized_split/MNST.json`). A position sealed at the 2026-08-07 close as it
    printed (90.36) and closed on 2026-08-12 (45.98) is the committed SMPL pair retargeted.
    `vinci.monitor.pair_closes` puts the entry on the exit's basis (45.18) and derives +1.77%.
    Main's web divided across the split: 45.98 / 90.36 − 1 = −49.1%. The monitor day carries
    `pair_closes`' row, and the page now shows exactly that."""
    from vinci.eod.splits import parse_splits
    from vinci.monitor import pair_closes

    fx = json.loads((ROOT / "tests" / "fixtures" / "realized_split" / "MNST.json").read_text())
    split = next(r for r in fx["splits"] if r["execution_date"] == "2026-08-11")
    ratio = split["split_to"] / split["split_from"]          # 2-for-1: the bar is on today's basis
    sealed = round(fx["closes"]["2026-08-07"]["c"] * ratio, 2)
    exit_ = fx["closes"]["2026-08-12"]["c"]
    rows = [json.loads(line) for line in LEDGER.read_text().splitlines()]

    def retarget(entry_id: str, upd: dict[str, Any]) -> dict[str, Any]:
        row = next(r for r in rows if json.loads(r["payload"])["entry_id"] == entry_id)
        payload = {**json.loads(row["payload"]), **upd}
        return {**row, **{k: v for k, v in upd.items() if k in row}, "payload": json.dumps(payload)}

    who = {"ticker": "MNST", "internal_id": "SEC-0000865752-MNST", "candidate_id": "MNST-split",
           "entry_price": sealed, "entry_price_as_of": "2026-08-07"}
    ledger = rows + [
        retarget("V-SMPL-screen2-20260706", {**who, "entry_id": "V-MNST-split"}),
        retarget("C-SMPL-screen2-20260706", {
            **who, "entry_id": "C-MNST-split", "closes_entry_id": "V-MNST-split",
            "exit_price": exit_, "exit_price_as_of": "2026-08-12"}),
    ]
    splits = parse_splits(fx["splits"], symbol="MNST")
    derived = next(r for r in pair_closes(ledger, splits=lambda s: splits if s == "MNST" else [])
                   if r["ticker"] == "MNST")
    assert round(derived["entry_price"], 2) == round(sealed / ratio, 2), derived

    index = json.loads((MONITOR / "index.json").read_text())
    day = json.loads((MONITOR / f"{index['latest']}.json").read_text())
    day["realized"] = [*day.get("realized", []), {k: str(v) if k.endswith("_as_of") else v
                                          for k, v in derived.items() if k != "split_note"}]
    closed = _closed({"./snapshots/decision_ledger.jsonl":
                      "\n".join(json.dumps(r) for r in ledger) + "\n",
                      f"./monitor/{index['latest']}.json": json.dumps(day)})
    got = closed["V-MNST-split"]["realizedReturn"]
    assert got == derived["realized_return"], (got, derived["realized_return"])
    assert abs(got - (exit_ / sealed - 1)) > 0.4, "the page still divides across the split"
