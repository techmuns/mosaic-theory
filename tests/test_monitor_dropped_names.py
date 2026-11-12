"""STATE §5.0 row 42 (b): the monitor day carries the names it dropped, typed, and the web panel
states them (preview approved by the operator 2026-11-12: "Approve, build it").

A name whose freshness row `vinci monitor` cannot write — its EDGAR filings window unreadable
(#1020), or its record's evidence date unreadable — was said only in the day's `notes`, and the
web's freshness panel reads `freshness` alone: the deployed desk showed N−1 names with no word of
the missing one ("A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION"). #1020 widened it — one unreadable
window used to write no day at all.

Now the day carries `freshness_dropped` (`MonitorSnapshot`, one `FreshnessDrop` per name: ticker,
closed cause, whole detail), the note line is rendered from it, and the panel leads with "N of M
names read · <T> not read — <cause>", the detail one click down.

TWO LAYERS, both end to end (TEST-LAYER RULE):
- THE DAY: the real `vinci monitor` command over the committed ledger, securities and
  assignments (#1020's harness, `tests/test_monitor_unreadable_window.py` and
  `tests/test_monitor_ref_date_bound.py`), reading the day file it writes.
- THE PANEL: the real decision-log `render()` under node over the committed frontend (the
  driver of `tests/test_web_twin_corrections_and_voids.py`). The negative pin is the committed
  2026-11-02 day, which drops nothing; the other days are built from it through
  `MonitorSnapshot`, the type the command writes.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.test_monitor_ref_date_bound import IT_REC, WERN_REC, _run
from tests.test_monitor_unreadable_window import IT_2021, OLD_REF, WERN_2021, _recut, _Sec
from vinci import monitor as mon

ROOT = Path(__file__).resolve().parents[1]
_FE = ROOT / "frontend"
DAY = "2026-11-02"
TAIL = " · its freshness row is NOT written"


# --- the day the command writes ----------------------------------------------------------------

def test_an_unreadable_window_is_a_typed_drop_and_its_note_is_rendered_from_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """IT's window needs page -001 and SEC answers a 404: the day carries IT as a typed drop, and
    its FILINGS note is that drop's `note()` — one definition, byte for byte #1020's line."""
    snap = _recut(tmp_path, monkeypatch, OLD_REF, [IT_2021, WERN_2021], _Sec(page="404"))
    [drop] = snap["freshness_dropped"]
    assert drop["ticker"] == "IT" and drop["cause"] == "filings_unread"
    assert drop["detail"].startswith("its EDGAR filings window since 2021-08-02 could not be read")
    assert "CIK0000749251-submissions-001.json" in drop["detail"]
    assert [n for n in snap["notes"] if n.startswith("FILINGS IT:")] == [
        f"FILINGS IT: {drop['detail']}{TAIL}"]


def test_an_unreadable_record_date_is_a_typed_drop(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A hand-typo'd amendment date on WERN: the second drop site, cause `record_date_unreadable`,
    its RECORD note rendered from it."""
    bad = {**WERN_REC, "scenarios": {"bull": {"reason": "x [amended 2026-02-30 typo] y"}}}
    snap = _run(tmp_path, monkeypatch, "2026-09-22", [IT_REC, bad])
    [drop] = snap["freshness_dropped"]
    assert drop["ticker"] == "WERN" and drop["cause"] == "record_date_unreadable"
    assert drop["detail"].startswith("WERN: bull reason amendment '2026-02-30'")
    assert f"RECORD {drop['detail']}{TAIL}" in snap["notes"]


def test_negative_a_day_that_reads_every_name_drops_none(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Page -001 served: IT and WERN both have rows, and the day's typed list is empty."""
    snap = _recut(tmp_path, monkeypatch, OLD_REF, [IT_2021, WERN_2021], _Sec())
    assert snap["freshness_dropped"] == []
    assert {r["ticker"] for r in snap["freshness"]} == {"IT", "WERN"}


def test_every_committed_day_states_its_drops_in_both_forms() -> None:
    """A LIVING ARTIFACT, so an invariant, never a count: on every committed day the drop notes
    are exactly the typed drops' `note()`s. A day written before the field carries neither — it
    loads with an empty list, and none of the ten (2026-07-20 → 2026-11-11) dropped a name —
    and a day written since carries both."""
    days = sorted((ROOT / "data" / "monitor").glob("20*.json"))
    assert days
    for p in days:
        raw = json.loads(p.read_text())
        snap = mon.MonitorSnapshot.model_validate(raw)
        assert [n for n in raw["notes"] if n.endswith(TAIL)] == [
            d.note() for d in snap.freshness_dropped], p.name


def test_the_note_is_rendered_from_the_typed_drop() -> None:
    f = mon.FreshnessDrop(ticker="IT", cause="filings_unread",
                          detail="its EDGAR filings window since 2024-07-06 could not be read "
                                 "(HttpError: x)")
    assert f.note() == ("FILINGS IT: its EDGAR filings window since 2024-07-06 could not be read "
                        "(HttpError: x) · its freshness row is NOT written")
    r = mon.FreshnessDrop(ticker="WERN", cause="record_date_unreadable",
                          detail="WERN: underwrite_date '2026-13-01' is not an ISO date (x)")
    assert r.note() == ("RECORD WERN: underwrite_date '2026-13-01' is not an ISO date (x) · its "
                        "freshness row is NOT written")


# --- the panel ---------------------------------------------------------------------------------

def _render(day: dict[str, Any] | None, tmp_path: Path, at: str = DAY) -> str:
    """The decision log's HTML, the committed day ``at`` served as the latest — or ``day`` in its
    place."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    ledger = str(ROOT / "data/snapshots/decision_ledger.jsonl")
    served = {"snapshots/decision_ledger.jsonl": ledger}
    if day is not None:
        (tmp_path / "day.json").write_text(json.dumps(day))
        served[f"monitor/{at}.json"] = str(tmp_path / "day.json")
    index = json.loads((_FE / "monitor" / "index.json").read_text())
    index["latest"] = at
    (tmp_path / "index.json").write_text(json.dumps(index))
    served["monitor/index.json"] = str(tmp_path / "index.json")
    script = """
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
  } catch { return { ok: false, status: 404, json: async () => ({}), text: async () => "" }; }
};
const root = new Proxy({}, { set(t, k, v) { t[k] = v; return true; },
                             get(t, k) { return k in t ? t[k] : stub; } });
const v = await import(FE + "/views/shared/decision-log.js");
await v.render(root, {}, { item: { title: "Decision log", blurb: "" },
                           frame: (i, o) => o.bodyHtml });
console.log(JSON.stringify(root.innerHTML));
""".replace("__FE__", json.dumps(str(_FE))).replace("__SERVE__", json.dumps(served))
    proc = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True,
                          text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    return str(json.loads(proc.stdout))


def _esc(s: str) -> str:
    """Text as the page's `escapeHtml` writes it (`frontend/lib/format.js`)."""
    for c, e in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&#39;")):
        s = s.replace(c, e)
    return s


def _committed_day(at: str = DAY) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads((ROOT / "data" / "monitor" / f"{at}.json").read_text())
    return raw


def _dropping(*drops: mon.FreshnessDrop, at: str = DAY) -> dict[str, Any]:
    """The committed day ``at`` with each named row not written and typed as dropped, as the
    command writes such a day — validated through `MonitorSnapshot`."""
    raw = _committed_day(at)
    gone = {d.ticker for d in drops}
    assert gone <= {f["ticker"] for f in raw["freshness"]}
    day = {**raw, "freshness": [f for f in raw["freshness"] if f["ticker"] not in gone],
           "freshness_dropped": [d.model_dump(mode="json") for d in drops],
           "notes": [*raw["notes"], *(d.note() for d in drops)]}
    mon.MonitorSnapshot.model_validate(day)
    return day


def _filings(t: str) -> mon.FreshnessDrop:
    since = date.fromisoformat(DAY) - timedelta(days=760)
    return mon.FreshnessDrop(ticker=t, cause="filings_unread",
                             detail=f"its EDGAR filings window since {since} could not be read "
                                    f"(HttpError: Exhausted retries for the {t} document)")


def _record(t: str) -> mon.FreshnessDrop:
    return mon.FreshnessDrop(ticker=t, cause="record_date_unreadable",
                             detail=f"{t}: underwrite_date '2026-7-19' is not an ISO date")


@pytest.mark.parametrize("at", [DAY, "2026-11-11"])
def test_negative_the_committed_day_renders_as_it_did(tmp_path: Path, at: str) -> None:
    """The committed days — 2026-11-02 (9 names) and 2026-11-11, the deployed latest (7 names, the
    first after GOOGL's void) — drop none and carry no field: each prints no dropped line and no
    tier, and renders byte for byte as it does with an empty list, so a day committed before the
    field reads as one that dropped none."""
    html = _render(None, tmp_path, at)
    assert "names read" not in html and "ds-dropped" not in html
    assert _render({**_committed_day(at), "freshness_dropped": []}, tmp_path, at) == html


def test_a_dropped_name_is_stated_with_its_count_and_its_reason(tmp_path: Path) -> None:
    drop = _filings("IT")
    html = _render(_dropping(drop), tmp_path)
    assert ('8 of 9 names read · <span class="mono" style="font-weight:650;">IT</span> not read — '
            "its EDGAR filings could not be read") in html
    tier = html.split('class="ds-dropped"', 1)[1]
    assert "Why it was not read" in tier and f"IT</span> — {_esc(drop.detail)}" in tier
    assert html.count('class="ds-dropped"') == 1


def test_two_dropped_names_are_both_listed_under_the_plural(tmp_path: Path) -> None:
    """Coordinator's condition: a two-drop day states both, in the plural — and never cut short."""
    it, wern = _filings("IT"), _record("WERN")
    html = _render(_dropping(it, wern), tmp_path)
    assert ('7 of 9 names read · <span class="mono" style="font-weight:650;">IT</span> not read — '
            'its EDGAR filings could not be read · <span class="mono" style="font-weight:650;">'
            "WERN</span> not read — its record&#39;s evidence date could not be read") in html
    tier = html.split('class="ds-dropped"', 1)[1]
    assert "Why they were not read" in tier
    assert f"IT</span> — {_esc(it.detail)}" in tier
    assert f"WERN</span> — {_esc(wern.detail)}" in tier


def test_a_voided_call_is_neither_counted_nor_listed_as_dropped(tmp_path: Path) -> None:
    """Coordinator's condition: GOOGL's call was ruled out of the record on 2026-11-11, after this
    day, and no live GOOGL decision is open — the cards' own void filter. Dropped beside IT, it is
    not in the count and not in the list; dropped alone, no line prints."""
    html = _render(_dropping(_filings("IT"), _filings("GOOGL")), tmp_path)
    assert "7 of 8 names read · " in html
    line = html.split("names read · ", 1)[1].split("</div>", 1)[0]
    assert "IT</span> not read" in line and "GOOGL" not in line
    assert "GOOGL" not in html.split('class="ds-dropped"', 1)[1].split("</details>", 1)[0]
    alone = _render(_dropping(_filings("GOOGL")), tmp_path)
    assert "names read" not in alone and "ds-dropped" not in alone


def test_a_day_that_drops_every_name_still_prints_the_panel(tmp_path: Path) -> None:
    """PR round 1 (the coordinator's mutant, which survived): with `if (!rows.length) return "";`
    in place of the panel's guard, a day that drops EVERY name in its freshness set — a bad SEC
    day — rendered no panel at all, the exact silence this PR closes. The deployed latest day,
    2026-11-11 (7 names, the first after GOOGL's void), with every row dropped: the panel prints
    "0 of 7 names read" and lists every name."""
    at = "2026-11-11"
    names = [str(f["ticker"]) for f in _committed_day(at)["freshness"]]
    assert len(names) == 7
    html = _render(_dropping(*(_filings(t) for t in names), at=at), tmp_path, at)
    assert "Trigger &amp; freshness panel" in html
    assert "0 of 7 names read · " in html
    line = html.split("names read · ", 1)[1].split("</div>", 1)[0]
    assert all(f'font-weight:650;">{t}</span> not read' in line for t in names), line
    tier = html.split('class="ds-dropped"', 1)[1].split("</details>", 1)[0]
    assert "Why they were not read" in tier and all(f"{t}</span> — " in tier for t in names)
