"""CLOSE-AWARE CARD HEADERS — the frontend ledger join, pinned against the backend it mirrors.

THE DEFECT (2026-07-27, external-honesty pass). `frontend/build.py` keyed the committed ledger by
ticker with last-row-wins and a docstring asserting "a ticker maps to at most one entry" — true
until close rows shipped (2026-07-22). From then a closed name carried TWO rows, and which one
reached the card was decided by FILE ORDER: IT's card rendered its CLOSE row's id as the decision,
and both closed positions headlined a bare "BUY" as though still open. An external reader — the IC
was sent exactly these artifacts — could not tell an open position from a closed one.

The join now anchors on the DECISION row and attaches `_closed` when a close pairs to it.

WHY A TWIN, not an import: build.py is the Cloudflare Pages build step, run as
`python frontend/build.py` with NO requirements.txt, so it must never import `vinci` (pydantic).
The same convention already covers the committed-GICS index. A twin is only safe if it is PINNED
to the original — `test_twin_agrees_with_pair_closes` is that pin, run on the REAL committed
ledger so the two cannot drift.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from vinci import monitor as mon

_ROOT = Path(__file__).resolve().parents[1]
_BUILD_PY = _ROOT / "frontend" / "build.py"
_LEDGER = _ROOT / "data" / "snapshots" / "decision_ledger.jsonl"


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("_card_build", _BUILD_PY)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BUILD: Any = _load_build()


def _rows() -> list[dict[str, Any]]:
    return [json.loads(ln) for ln in _LEDGER.read_text().splitlines() if ln.strip()]


def test_twin_agrees_with_pair_closes_on_the_committed_ledger() -> None:
    """THE TWIN PIN. The stdlib join must resolve exactly the same closed positions — and the same
    exit prices — as `vinci.monitor.pair_closes`, on the real committed ledger."""
    rows = _rows()
    # DIRECT EQUALITY over EVERY closed pair, on the joiner production actually runs. An earlier
    # cut of this pin restricted the backend side to each ticker's CURRENT position — a workaround
    # for a join that collapsed to one row per ticker and therefore could not see a superseded
    # pair. The join keeps every decision row now, so both sides enumerate the same set and the
    # restriction is gone. It was compensating for discarded information, which is the weaker
    # thing a pin can do.
    twin = {}
    for t, entries in _BUILD._ledger_join().items():
        for e in entries:
            if e.get("_closed"):
                twin[t] = e["_closed"]["exitPrice"]
    backend = {p["ticker"]: round(float(p["exit_price"]), 2) for p in mon.pair_closes(rows)}
    assert twin == backend, f"twin diverged from pair_closes: {twin} != {backend}"


def test_the_card_anchors_on_the_decision_row_never_the_close() -> None:
    """A closed ticker resolves to its DECISION row (V-), never its close (C-) — the exact drift
    that put a close-row id on IT's card while file order happened to favour it."""
    closed = [e for entries in _BUILD._ledger_join().values() for e in entries if e.get("_closed")]
    assert closed, "the committed ledger holds at least one closed position (IT, SMPL)"
    for e in closed:
        assert str(e["entry_id"]).startswith("V-"), e["entry_id"]
        assert e.get("event") is None, "a decision row carries no event"
        assert str(e["_closed"]["closeEntryId"]).startswith("C-")


def test_closed_position_emits_the_closed_block_and_open_stays_byte_identical() -> None:
    """THE FIXTURE, both ways. A decision row WITH a paired close carries `closed` onto the card;
    the SAME record without one emits no `closed` key at all — so every open card stays
    byte-identical to what it rendered before this fix (the degrade is silence, never a field)."""
    decision = {"entry_id": "V-X", "ticker": "XYZ", "verdict": "BUY", "entry_price": 10.0,
                "entry_price_as_of": "2026-07-01", "decided_at": "2026-07-01T00:00:00"}
    close_payload = {"entry_id": "C-X", "ticker": "XYZ", "verdict": "BUY", "event": "CLOSE",
                     "closes_entry_id": "V-X", "exit_price": 8.5,
                     "exit_price_as_of": "2026-07-20", "reason": "stated reason"}
    rec = {"ticker": "XYZ", "recipe_id": "R1", "recipe_desc": "d", "multiple_basis": "EV/EBITDA",
           "underwrite_date": "2026-07-01", "analyst": "a", "spot": 9.0, "spot_source": "s",
           "facts": {}, "scenarios": {}, "result": {}, "verdict": {"status": "watch"}}

    with_close = _BUILD._scenario_card(rec, {"XYZ": {**decision, "_closed": {
        "exitPrice": 8.5, "exitPriceAsOf": "2026-07-20", "reason": "stated reason",
        "closeEntryId": "C-X"}}})
    assert with_close["ledger"]["closed"]["exitPrice"] == 8.5
    assert with_close["ledger"]["closed"]["exitPriceAsOf"] == "2026-07-20"
    assert with_close["ledger"]["entryId"] == "V-X"          # decision row, not the close

    open_card = _BUILD._scenario_card(rec, {"XYZ": dict(decision)})
    assert "closed" not in open_card["ledger"], "an open position must emit no closed key"
    assert open_card["ledger"]["verdict"] == "BUY"

    # and the join itself produces exactly that shape from raw rows (payload-wrapped, as committed)
    joined = {}
    ledger_rows = [decision, {"entry_id": "C-X", "ticker": "XYZ",
                              "payload": json.dumps(close_payload)}]
    entries = [json.loads(r["payload"]) if isinstance(r.get("payload"), str) else r
               for r in ledger_rows]
    for e in entries:
        if not e.get("event"):
            joined[e["entry_id"]] = dict(e)
    assert "V-X" in joined and "C-X" not in joined, "close rows never become positions"


def test_a_stamped_vintage_reaches_the_card_and_an_unstamped_one_emits_nothing() -> None:
    """REVIEW FINDING (#302). The backend REQUIRES `vintage` from schema 1.4, and the card's
    reference builder is an explicit key ALLOWLIST — so the field was stamped in
    `scenarios/<T>.json` and silently dropped on the way to the human. A provenance field the
    reader never sees is not provenance; `source` says WHERE, `vintage` says WHEN, and the whole
    point is that the human can check the period without opening the JSON.

    BOTH WAYS, the allowlist's own idiom: stamped rides, unstamped emits NO key at all, so the
    7 committed 1.3 records — none of which carry a vintage — stay byte-identical."""
    def _rec(refs: list[dict[str, object]]) -> dict[str, object]:
        return {"ticker": "XYZ", "recipe_id": "R1", "recipe_desc": "d",
                "multiple_basis": "EV/EBITDA", "underwrite_date": "2026-07-01", "analyst": "a",
                "spot": 9.0, "spot_source": "s", "facts": {}, "scenarios": {}, "result": {},
                "verdict": {"status": "watch"},
                "assumptions": {"margin": {"method": "m", "references": refs}}}

    base = {"label": "own-history median", "value": 7.45, "unit": "%", "source": "EDGAR"}
    stamped = _BUILD._scenario_card(_rec([{**base, "vintage": "FY2025"}]))
    ref = stamped["assumptions"][0]["references"][0]
    assert ref["vintage"] == "FY2025", "a stamped vintage must reach the card"
    assert ref["source"] == "EDGAR", "and must not displace the source it complements"

    bare = _BUILD._scenario_card(_rec([dict(base)]))
    assert "vintage" not in bare["assumptions"][0]["references"][0], (
        "an unstamped reference must emit NO vintage key — the degrade is silence, never a null, "
        "or every committed 1.3 card re-renders with a diff")
