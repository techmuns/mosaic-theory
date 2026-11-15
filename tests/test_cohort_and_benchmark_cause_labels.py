"""(STATE row 41) Two render labels named a cause the record does not hold (after #1075).

1. THE MARKDOWN COHORT LIST printed "no bars" for every member with no 180-day return. Since #1075 a
   member WITH bars is refused when its close sits more than 4 days from either end of the window,
   and it has no return either. On the 2026-11-11 store (content sha256 598a3d2c...), at WLK's own
   2026-10-16, production's `_cohort` refuses ATKR and CLF (last close 2026-07-02) and finds no bars
   for LYB, NUE, STLD and WCC: the page printed "no bars" on all six. `CohortMember` records NO
   per-member cause — only the cohort's `source_ref` STRING names the refused members, and a
   renderer never parses a rendered string (CLAUDE.md) — so the line now names no cause
   (`render.COHORT_NO_RETURN`). The web's cohort cell was already a dash and is unchanged.
2. THE WEB STRIP printed a fixed "<benchmark> benchmark bars unavailable — relative read UNKNOWN"
   whenever the relative was absent. A benchmark that trails the name (#743) or has no close near
   the window start (#1075) HAS bars. That leg's cause IS in the record, as its own note, which the
   Markdown's market row already printed; the strip now prints it too.

BUILT FROM REAL DATA. The cohort is production's `_idiosyncratic_vs_shared` over the committed
fixture `tests/fixtures/prices-2026-11-11` (real Polygon bars cut from that store) at its 11-11 end
— the record #1075's own pins build: 4 of 12 refused, 7 with no bars, AMZN read. The benchmark
legs are production's `_market_legs` over the same real AMZN and SPY bars. NO OBSERVED CASE of a
refused benchmark exists on the committed corpus or on the 11-11 store: each is the real SPY series
with a hole cut at the window start, its tail cut, or emptied. Each record is hosted in a REAL
committed page and rendered through `render_markdown` and the production `renderDossier` in node.
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import shutil
import subprocess
import typing
from datetime import date

import pytest

from tests.test_price_date_bounds import END, _bars, _googl_idio
from vinci.dossier import mechanical as dm
from vinci.dossier.render import COHORT_NO_RETURN, render_markdown
from vinci.dossier.schemas import Dossier, IdiosyncraticVsShared
from vinci.schemas.market import PriceBar

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"

#: words that name a cause — a cohort member's line names none of them (the record holds none)
_CAUSES = ("no bars", "refused", "stale", "close", "fetch", "unavailable")
#: the web's no-value glyph (frontend/lib/format.js DASH)
_DASH = "—"
#: the strip's fixed wording before this fix — the wrong cause for a benchmark that has bars
_OLD_STRIP = "benchmark bars unavailable — relative read UNKNOWN"


def _host(ticker: str, idio: IdiosyncraticVsShared) -> dict[str, typing.Any]:
    """The committed dossier of ``ticker`` with its idiosyncratic-vs-shared block swapped."""
    d: dict[str, typing.Any] = json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    d["mechanical"]["idiosyncratic_vs_shared"] = idio.model_dump(mode="json")
    return d


def _md(doc: dict[str, typing.Any]) -> str:
    return render_markdown(Dossier.model_validate(doc))


def _web(doc: dict[str, typing.Any], tmp: pathlib.Path) -> str:
    """The page through the production `renderDossier`."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    src = tmp / "doc.json"
    src.write_text(json.dumps(doc))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(renderDossier(JSON.parse(readFileSync(process.argv[2])), null));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver, str(JS), str(src)],
                         capture_output=True, text=True, check=True)
    return out.stdout


def _md_members(md: str) -> dict[str, str]:
    """ticker → what the Markdown cohort list prints for its return."""
    return dict(re.findall(r"^  - \[\dh\] (\S+): (.*?) · via ", md, re.MULTILINE))


def _web_members(page: str) -> dict[str, str]:
    """ticker → the web cohort table's 180d-return cell (that table only: a ticker can recur in
    another table of the page)."""
    tables = re.findall(r"<th>Cohort name</th>.*?</table>", page, re.DOTALL)
    assert len(tables) == 1, len(tables)
    rows = re.findall(r'<tr><td class="mono">([^<]*)</td><td class="num">[^<]*</td>\s*'
                      r'<td class="num">([^<]*)</td>', tables[0])
    return {html.unescape(t): html.unescape(c) for t, c in rows}


def _strip_tail(page: str) -> str:
    tails = re.findall(r"· ([^<]*relative read UNKNOWN)</span>", page)
    assert len(tails) == 1, tails
    return html.unescape(tails[0])


def _md_market_note(md: str, bsym: str) -> str:
    """The Markdown market row's note. The page prints the row once, in the brief's "What
    happened" block, under a two-part label ("Market (SPY) 180d · Market (SPY) 180d return")."""
    rows = re.findall(rf"^- \*\*(?:[^*\n]* · )?Market \({bsym}\) 180d return:\*\* _UNKNOWN_ — "
                      r"(.*)$", md, re.MULTILINE)
    assert len(rows) == 1, rows
    return str(rows[0])


# --- 1. the cohort list -------------------------------------------------------------------------


def test_the_record_holds_no_cause_per_member_only_in_the_cohort_source(
        tmp_path: pathlib.Path) -> None:
    """(precondition) The real record: 4 members refused, 7 with no bars, AMZN read. A refused
    member and a no-bars member are the SAME structured value — `ret_180d` None, and `CohortMember`
    has no other field that could tell them apart — and only the cohort's `source_ref` string names
    the refused. So no renderer can name a member's cause without parsing that string."""
    idio = _googl_idio(tmp_path)
    assert idio.cohort.value is not None
    members = {m.ticker: m for m in idio.cohort.value}
    assert set(type(members["EXTR"]).model_fields) == {"ticker", "hops", "ret_180d", "via"}
    refused, absent = members["EXTR"], members["T"]  # EXTR's bars stop 07-02; T has none
    assert refused.ret_180d is None and absent.ret_180d is None
    src = idio.cohort.source_ref or ""
    assert "4 of 12 refused" in src and "EXTR 2026-07-02" in src and " T " not in src, src
    assert members["AMZN"].ret_180d is not None


def test_a_cohort_member_with_no_return_names_no_cause_on_the_markdown_e2e(
        tmp_path: pathlib.Path) -> None:
    """(−) The real record hosted in the committed GOOGL page → `render_markdown`. Every member
    with no return — the four refused and the seven with no bars alike — prints a line that names
    no cause, and the cohort's own source, naming the four, stays on the list's header line.
    RED AT BASE: the four refused members printed "no bars", a cause they do not have."""
    idio = _googl_idio(tmp_path)
    md = _md(_host("GOOGL", idio))
    printed = _md_members(md)
    assert idio.cohort.value is not None
    nulls = [m.ticker for m in idio.cohort.value if m.ret_180d is None]
    assert len(nulls) == 11 and set(nulls) <= set(printed), (nulls, printed)
    for t in nulls:
        assert printed[t] == COHORT_NO_RETURN, (t, printed[t])
        assert not [w for w in _CAUSES if w in printed[t]], (t, printed[t])
    assert f"- **Graph cohort** (`{idio.cohort.source_ref}`):" in md


def test_a_cohort_member_with_a_return_still_prints_it_e2e(tmp_path: pathlib.Path) -> None:
    """(+) The member that read keeps its return on both renderers: AMZN, priced on its own two
    closes (05-15 → 11-10)."""
    idio = _googl_idio(tmp_path)
    assert idio.cohort.value is not None
    amzn = next(m for m in idio.cohort.value if m.ticker == "AMZN")
    assert amzn.ret_180d is not None
    doc = _host("GOOGL", idio)
    assert _md_members(_md(doc))["AMZN"] == f"{amzn.ret_180d:.0%}"
    cell = _web_members(_web(doc, tmp_path))["AMZN"]
    assert cell != _DASH and cell.endswith("%"), cell


def test_the_web_cohort_cell_names_no_cause_either_e2e(tmp_path: pathlib.Path) -> None:
    """(− · py↔js) The same record through the web: every member with no return is the no-value
    dash, which names no cause, and the table's source line carries the cohort's source. The web
    was already right; this holds it there (passes at base by design)."""
    idio = _googl_idio(tmp_path)
    page = _web(_host("GOOGL", idio), tmp_path)
    cells = _web_members(page)
    assert idio.cohort.value is not None
    for m in idio.cohort.value:
        if m.ret_180d is None:
            assert cells[m.ticker] == _DASH, (m.ticker, cells[m.ticker])
    assert html.escape(idio.cohort.source_ref or "", quote=False) in page


def test_no_committed_cohort_member_line_names_a_cause() -> None:
    """(− · living corpus) Over every committed dossier.json with a cohort, the line THIS renderer
    prints for a member with no return names no cause, and a member with a return prints a
    percentage. Reads the JSON, not the committed dossier.md. Phrasing-independent.
    RED AT BASE: WLK's ATKR printed "no bars"."""
    checked = 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        doc = json.loads(p.read_text())
        cohort = doc["mechanical"]["idiosyncratic_vs_shared"]["cohort"]
        if cohort.get("status") != "present" or not cohort.get("value"):
            continue
        printed = _md_members(_md(doc))
        for m in cohort["value"]:
            line = printed[m["ticker"]]
            if m["ret_180d"] is None:
                assert not [w for w in _CAUSES if w in line], (p.parent.name, m["ticker"], line)
            else:
                assert line.endswith("%"), (p.parent.name, m["ticker"], line)
            checked += 1
    assert checked, "no committed page carries a cohort: this test has stopped testing anything"


# --- 2. the web strip's benchmark leg -----------------------------------------------------------


class _Leg(typing.NamedTuple):
    name: str
    spy: list[PriceBar]  # the real SPY series, cut to the case's shape
    says: str  # a phrase the leg's own note holds (production's deterministic wording)


def _legs() -> list[_Leg]:
    spy = _bars("SPY")
    return [
        _Leg("start_refused", [b for b in spy
                               if not date(2026, 4, 20) <= b.bar_date <= date(2026, 5, 20)],
             "window start"),
        _Leg("stale_vs_name", [b for b in spy if b.bar_date <= date(2026, 11, 3)],
             "missed fetch"),
        _Leg("no_bars", [], "SPY benchmark bars unavailable"),
    ]


_LEGS = _legs()


def _amzn_with(leg: _Leg) -> tuple[dict[str, typing.Any], str]:
    """The committed AMZN page with its market legs re-drawn by production `_market_legs` over the
    real AMZN bars and ``leg``'s SPY series at the 11-11 end; and that market leg's own note."""
    committed = Dossier.model_validate_json(
        (ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    io = committed.mechanical.idiosyncratic_vs_shared
    assert io.benchmark_symbol == "SPY"
    name, mkt, rel, _ = dm._market_legs(_bars("AMZN"), leg.spy, END, sym="AMZN", bsym="SPY",
                                        bench_basis=io.benchmark_basis or "")
    # the strip renders only beside a PRESENT name return, and this is the absent-relative branch
    assert name.value is not None and mkt.value is None and rel.value is None, leg.name
    assert mkt.note is not None and leg.says in mkt.note, mkt.note
    idio = io.model_copy(update={"name_180d_return": name, "market_180d_return": mkt,
                                 "rel_vs_market": rel})
    return _host("AMZN", idio), mkt.note


@pytest.mark.parametrize("leg", _LEGS, ids=[x.name for x in _LEGS])
def test_the_web_strip_prints_the_benchmark_legs_own_note_e2e(
        tmp_path: pathlib.Path, leg: _Leg) -> None:
    """(−/+) The strip's no-relative tail prints the market leg's own note. A refused benchmark
    is never called "bars unavailable"; one with genuinely no bars still is, from its own note.
    RED AT BASE on all three: the strip printed the fixed no-bars wording, which is the wrong
    cause for the two refused legs and, for the no-bars leg, still says "bars unavailable" but
    is not the leg's note (it dropped the note's `vinci refresh SPY`)."""
    doc, note = _amzn_with(leg)
    tail = _strip_tail(_web(doc, tmp_path))
    assert note in tail, (tail, note)
    if leg.name == "no_bars":
        assert "SPY benchmark bars unavailable" in tail, tail
    else:
        assert "bars unavailable" not in tail and _OLD_STRIP not in tail, tail


@pytest.mark.parametrize("leg", _LEGS, ids=[x.name for x in _LEGS])
def test_the_strip_and_the_markdown_market_row_say_the_same_thing_e2e(
        tmp_path: pathlib.Path, leg: _Leg) -> None:
    """(py↔js) The cause the web strip gives is the one the Markdown's market row gives: both print
    the leg's note, and the strip names the same leg the row does.
    RED AT BASE on all three: the strip's fixed wording was not the row's note."""
    doc, note = _amzn_with(leg)
    md_note = _md_market_note(_md(doc), "SPY")
    tail = _strip_tail(_web(doc, tmp_path))
    assert md_note == note
    assert tail == f"Market (SPY) 180d return UNKNOWN — {md_note} · relative read UNKNOWN", tail
