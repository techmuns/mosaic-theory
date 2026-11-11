"""THE WEB TWIN OF THE LEDGER'S CORRECTIONS (RF-D7) AND VOIDS (operator ruling 2026-11-11, GOOGL).

The page reads the ledger through two twins of `vinci.monitor`, because neither may import `vinci`:
`frontend/build.py`'s `_ledger_join` (the Cloudflare build step has no requirements.txt) and
`frontend/lib/snapshots.js`'s `_loadLedger` (the browser). A twin is only safe while it is PINNED
to the readers it copies, on the real ledger, so each one is checked here against
`monitor.apply_corrections` + `monitor.decision_rows`:
- on the COMMITTED ledger (two corrections, no void until the void's own artifact PR), and
- on the committed ledger with GOOGL's void appended. The VOID row is the one the real
  `vinci void-decision V-GOOGL` wrote in the dry run of #984, on a backup of the primary store
  (`tests/fixtures/ledger_void/x_googl_dry_run.jsonl`), never a hand-rolled shape. Once the void
  is committed the second case reads the committed row and the fixture is not added.

Then the pages END TO END: the decision log's audit tier, and GOOGL's committed dossier page
with the operator's one line above its sealed rationale (2026-11-11: "Approve + add a banner").
Every assertion is an id, a class, a date or a count, so nothing rots on a reworded sentence.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from vinci import monitor as mon
from vinci.schemas.ledger import EVENT_VOID, LedgerEntry, voids_by_decision

_ROOT = Path(__file__).resolve().parents[1]
_LEDGER = _ROOT / "data" / "snapshots" / "decision_ledger.jsonl"
_VOID_ROW = _ROOT / "tests" / "fixtures" / "ledger_void" / "x_googl_dry_run.jsonl"
_FE = _ROOT / "frontend"


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("_twin_build", _FE / "build.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BUILD: Any = _load_build()


def _committed() -> list[dict[str, Any]]:
    return [json.loads(ln) for ln in _LEDGER.read_text().splitlines() if ln.strip()]


def _voided() -> list[dict[str, Any]]:
    """The committed ledger with GOOGL's void — the committed row once it exists, else the dry
    run's real one appended."""
    rows = _committed()
    if any(mon.entry_of(r).get("event") == EVENT_VOID for r in rows):
        return rows
    return rows + [json.loads(_VOID_ROW.read_text())]


_LEDGERS = {"committed": _committed, "voided": _voided}


def _readers(raw: list[dict[str, Any]]) -> tuple[dict[str, tuple[str, float, str]], set[str]]:
    """What `vinci.monitor` reads: each live decision's (ticker, entry price, entry date) — at its
    correction where it has one — and the decisions a void rules out."""
    fixed, _notes = mon.apply_corrections(raw)
    live = {}
    for r in mon.decision_rows(fixed):
        e = mon.entry_of(r)
        live[str(e["entry_id"])] = (str(e["ticker"]), round(float(e["entry_price"]), 2),
                                    str(e["entry_price_as_of"]))
    voided = set(voids_by_decision([LedgerEntry.model_validate(mon.entry_of(r)) for r in raw]))
    return live, voided


def _write(rows: list[dict[str, Any]], path: Path) -> Path:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


@pytest.mark.parametrize("which", sorted(_LEDGERS))
def test_the_build_twin_reads_the_book_the_monitor_reads(
        which: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _LEDGERS[which]()
    want_live, want_voided = _readers(raw)
    _write(raw, tmp_path / "decision_ledger.jsonl")
    monkeypatch.setattr(_BUILD, "SNAP", tmp_path)
    live: dict[str, tuple[str, float, str]] = {}
    voided: set[str] = set()
    for ticker, entries in _BUILD._ledger_join().items():
        for e in entries:
            if e.get("_voided"):
                voided.add(str(e["entry_id"]))
                continue
            fx = e.get("_correction") or {}
            live[str(e["entry_id"])] = (ticker, round(float(fx.get("entryPrice",
                                                                     e["entry_price"])), 2),
                                        str(fx.get("entryPriceAsOf", e["entry_price_as_of"])))
    assert live == want_live
    assert voided == want_voided
    assert bool(want_voided) == (which == "voided")      # the case is the one it names


def _node(script: str) -> Any:
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    proc = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True,
                          text=True, cwd=_ROOT)
    if proc.returncode != 0:
        raise AssertionError(f"the page THREW under node:\n{proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _driver(serve: dict[str, Path], body: str) -> str:
    """A node driver whose `fetch` reads the committed frontend, except the paths in ``serve``
    (relative to `frontend/`), which it reads from the given files. No DOM, no server."""
    return """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window", "document", "location"]) { try { globalThis[g] = stub; } catch {} }
import { readFile } from "node:fs/promises";
const FE = __FE__, SERVE = __SERVE__;
globalThis.fetch = async (p) => {
  const rel = String(p).split("?")[0].replace(/^\\.\\//, "").replace(/^\\//, "");
  try {
    const buf = await readFile(SERVE[rel] || (FE + "/" + rel), "utf8");
    return { ok: true, status: 200, json: async () => JSON.parse(buf), text: async () => buf };
  } catch {
    return { ok: false, status: 404, json: async () => ({}), text: async () => "" };
  }
};
const root = new Proxy({}, { set(t, k, v) { t[k] = v; return true; },
                             get(t, k) { return k in t ? t[k] : stub; } });
__BODY__
""".replace("__FE__", json.dumps(str(_FE))).replace(
        "__SERVE__", json.dumps({k: str(v) for k, v in serve.items()})).replace("__BODY__", body)


@pytest.mark.parametrize("which", sorted(_LEDGERS))
def test_the_page_twin_reads_the_book_the_monitor_reads(which: str, tmp_path: Path) -> None:
    raw = _LEDGERS[which]()
    want_live, want_voided = _readers(raw)
    led = _write(raw, tmp_path / "decision_ledger.jsonl")
    got = _node(_driver({"snapshots/decision_ledger.jsonl": led}, """
const { getLedger } = await import(FE + "/lib/snapshots.js");
const l = await getLedger();
console.log(JSON.stringify({
  live: l.entries.map((e) => [e.entryId, e.ticker, Math.round(e.entryPrice * 100) / 100,
                              e.entryPriceAsOf]),
  voided: (l.voided || []).map((v) => v.entryId) }));
"""))
    assert {eid: (t, p, d) for eid, t, p, d in got["live"]} == want_live
    assert set(got["voided"]) == want_voided


def test_the_decision_log_shows_a_voided_call_once_and_never_in_the_book(tmp_path: Path) -> None:
    """END TO END: the real decision-log `render()` over the voided ledger. The voided decision
    and its void's id sit in the audit tier exactly once, and nowhere before it; every live
    correction's id still reaches the page (the VRRM half: RF-D7)."""
    raw = _voided()
    live, voided = _readers(raw)
    fixes = {str(e.corrects_entry_id): e.entry_id for e in
             (LedgerEntry.model_validate(mon.entry_of(r)) for r in raw) if e.corrects_entry_id}
    led = _write(raw, tmp_path / "decision_ledger.jsonl")
    html = _node(_driver({"snapshots/decision_ledger.jsonl": led}, """
const v = await import(FE + "/views/shared/decision-log.js");
await v.render(root, {}, { item: { title: "Decision log", blurb: "" },
                           frame: (i, o) => o.bodyHtml });
console.log(JSON.stringify(root.innerHTML));
"""))
    assert html.count('class="ds-voided') == 1
    book, tier = html.split('class="ds-voided', 1)
    voids = {str(e.voids_entry_id): e.entry_id for e in
             (LedgerEntry.model_validate(mon.entry_of(r)) for r in raw) if e.voids_entry_id}
    for decision in voided:
        assert voids[decision] in tier and voids[decision] not in book
        assert decision not in book                      # the voided decision is in no live row
    for decision in live:
        if decision in fixes:
            assert fixes[decision] in book               # a live correction still shows


def _googl_card(raw: list[dict[str, Any]], tmp_path: Path,
                monkeypatch: pytest.MonkeyPatch) -> Path:
    """GOOGL's committed underwrite record, carded by the build's own `_scenario_card` over
    ``raw``."""
    _write(raw, tmp_path / "decision_ledger.jsonl")
    monkeypatch.setattr(_BUILD, "SNAP", tmp_path)
    card = _BUILD._scenario_cards()["GOOGL"]
    out = tmp_path / "GOOGL.card.json"
    out.write_text(json.dumps(card))
    return out


def _dossier_page(raw: list[dict[str, Any]], card: Path, tmp_path: Path) -> str:
    led = _write(raw, tmp_path / "decision_ledger.jsonl")
    return str(_node(_driver({"snapshots/decision_ledger.jsonl": led,
                              "scenarios/GOOGL.json": card}, """
const v = await import(FE + "/views/shared/dossier.js");
await v.render(root, ["GOOGL"], { item: { title: "Dossier", blurb: "" },
                                  frame: (i, o) => o.bodyHtml });
console.log(JSON.stringify(root.innerHTML));
""")))


def test_googls_committed_page_says_its_verdict_was_voided_above_the_sealed_text(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE BANNER (operator, 2026-11-11), on GOOGL's committed page and committed record: one line,
    above the sealed rationale, dated by the void row's own ruling; no BUY pill; and the record's
    Logged-verdict block says a verdict was voided, never that none was logged."""
    raw = _voided()
    card_path = _googl_card(raw, tmp_path, monkeypatch)
    card = json.loads(card_path.read_text())
    assert card["voided"]["voidId"] and "ledger" not in card and "supersededLedger" not in card
    html = _dossier_page(raw, card_path, tmp_path)
    assert html.count('class="fact-caveat brief-voided"') == 1
    banner_at, thesis_at = html.index("brief-voided"), html.index('class="brief-thesis"')
    assert banner_at < thesis_at
    banner = html[banner_at:thesis_at]
    assert card["voided"]["ruledOn"] in banner and "sealed record, unedited" in banner
    assert ">BUY<" not in html
    assert "no verdict logged yet" not in html


def test_a_page_whose_ledger_voids_nothing_carries_no_banner(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE NEGATIVE PIN: the same page over the ledger without a void row has no banner and no
    `voided` card field — the banner is the void's, never the record's."""
    raw = [r for r in _committed() if mon.entry_of(r).get("event") != EVENT_VOID]
    card_path = _googl_card(raw, tmp_path, monkeypatch)
    assert "voided" not in json.loads(card_path.read_text())
    assert "brief-voided" not in _dossier_page(raw, card_path, tmp_path)


def _repointed_void(decision: dict[str, Any], void_id: str) -> dict[str, Any]:
    """The dry run's REAL void row, re-pointed at ``decision`` — the one field a void names."""
    row = json.loads(_VOID_ROW.read_text())
    pl = json.loads(row["payload"])
    pl.update(entry_id=void_id, voids_entry_id=decision["entry_id"], ticker=decision["ticker"])
    return {**row, "entry_id": void_id, "ticker": decision["ticker"], "payload": json.dumps(pl)}


def _decision(raw: list[dict[str, Any]], entry_id: str) -> dict[str, Any]:
    return next(mon.entry_of(r) for r in raw if mon.entry_of(r).get("entry_id") == entry_id)


def test_a_newer_void_never_hides_an_older_live_row_the_record_owns(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`decision_rows` drops a voided row BEFORE anything is read, so a record owning a live row
    and a later voided one holds the live one. The build's tenure walk went newest-first over
    marked rows and returned the void — the card read "verdict voided" over a live position. The
    second IT decision is a copy of IT's real row, re-dated inside IT's own tenure."""
    raw = [r for r in _committed() if mon.entry_of(r).get("event") != EVENT_VOID]
    it = _decision(raw, "V-IT-screen2-20260706")
    second = {**it, "entry_id": "V-IT-second", "decided_at": "2026-08-01T00:00:00"}
    raw = raw + [{**second, "payload": json.dumps(second)},
                 _repointed_void(second, "X-IT-second")]
    live, voided = _readers(raw)
    assert "V-IT-screen2-20260706" in live and voided == {"V-IT-second"}   # the readers' book
    _write(raw, tmp_path / "decision_ledger.jsonl")
    monkeypatch.setattr(_BUILD, "SNAP", tmp_path)
    card = _BUILD._scenario_cards()["IT"]
    assert "voided" not in card
    assert card["ledger"]["entryId"] == "V-IT-screen2-20260706"


def test_a_record_page_names_only_its_own_voided_call(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The record-only page binds its verdict BY THE CARD, never by ticker — and so must its voided
    call. SMPL-2026-07-27 owns no row (it borrows SMPL-2026-07-21's closed one); voiding the LIVE
    record's SMPL decision must not tell this archived page that IT logged and lost a verdict."""
    raw = [r for r in _committed() if mon.entry_of(r).get("event") != EVENT_VOID]
    raw = raw + [_repointed_void(_decision(raw, "V-SMPL-screen2-20260729"), "X-SMPL-test")]
    _write(raw, tmp_path / "decision_ledger.jsonl")
    monkeypatch.setattr(_BUILD, "SNAP", tmp_path)
    cards = _BUILD._scenario_cards()
    assert cards["SMPL"]["voided"]["voidId"] == "X-SMPL-test"            # the void did land
    arch = tmp_path / "SMPL-2026-07-27.card.json"
    arch.write_text(json.dumps(cards["SMPL-2026-07-27"]))
    assert "voided" not in cards["SMPL-2026-07-27"]
    led = _write(raw, tmp_path / "decision_ledger.jsonl")
    html = str(_node(_driver({"snapshots/decision_ledger.jsonl": led,
                              "scenarios/SMPL-2026-07-27.json": arch}, """
const v = await import(FE + "/views/shared/dossier.js");
await v.render(root, ["SMPL-2026-07-27"], { item: { title: "Dossier", blurb: "" },
                                            frame: (i, o) => o.bodyHtml });
console.log(JSON.stringify(root.innerHTML));
""")))
    assert 'class="card ds-section"' in html and "Logged verdict" in html   # the block rendered
    assert "none live" not in html and "VOIDED" not in html                # …naming no void


def test_a_borrowed_correction_never_speaks_for_a_different_entry(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The masthead foot's "the ledger reads this entry at …" names the predecessor's correction.
    It holds only while the borrowed row IS the entry on the card — the identity the Entry cell
    already requires. GOOGL's card over the void-free ledger (sealed 345.90 = the record's
    entry) carries it; the same card with a record entry of its own does not."""
    raw = [r for r in _committed() if mon.entry_of(r).get("event") != EVENT_VOID]
    card = json.loads(_googl_card(raw, tmp_path, monkeypatch).read_text())
    assert card["supersededLedger"]["correction"]["correctionId"] == "R-GOOGL"
    other = {**card, "verdict": {**card["verdict"], "entryPrice": 300.0}}
    got = _node(_driver({}, """
const { uwCard } = await import(FE + "/views/shared/uw-card.js");
console.log(JSON.stringify([uwCard(__SAME__), uwCard(__OTHER__)]));
""".replace("__SAME__", json.dumps(card)).replace("__OTHER__", json.dumps(other))))
    same, diff = got
    assert "R-GOOGL" in same and "the ledger reads this entry" in same
    assert "the ledger reads this entry" not in diff
