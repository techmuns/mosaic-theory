"""The page's copy-paste `log-verdict` command names an id the CLI accepts.

THE DEFECT (2026-09-17). Every dossier page printed `python -m vinci log-verdict
<TICKER>-screen2-<reference date> …`. The CLI opens two doors (`vinci/cli.py` `_cmd_log_verdict`):
a SCREEN CANDIDATE by its candidate id, and a FOLLOWED name by its TICKER. So every followed page —
UBER, V, GOOGL, LLY, TECX, ORKA, NFLX — offered a command the CLI refuses ("neither a candidate in
the store nor a FOLLOWED ticker"), and a followed name the screen ALSO ranks would have sealed a
screen-origin overshoot row in the primary spread. The same block said the entry price "freezes
from the screen's as-of date", while the CLI freezes the latest close on or before `--ref`, which
defaults to today.

WHAT IS PINNED, at the layer the reader meets: every committed page, rendered through the real
`renderDossier` with the committed index's follow map, names the ticker for a followed name and
the candidate id for any other — checked against the CLI's own follow reader, not a restatement of
the rule. The rule's route table is pinned beside it, including the legacy index with no map.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
from typing import Any

import pytest

import vinci.dossier.assemble as asm
from vinci.config import get_config

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSSIER_JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"
MIRROR = ROOT / "frontend" / "dossiers"
FOLLOWED = ROOT / "data" / "followed.json"


def _node(script: str) -> Any:
    if not shutil.which("node"):
        pytest.skip("node not available")
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
const mod = await import("{DOSSIER_JS.resolve().as_uri()}");
{script}
"""
    proc = subprocess.run(["node", "--input-type=module", "-e", driver],
                          capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        raise AssertionError(f"node driver failed: {proc.stderr}")
    return json.loads(proc.stdout)


def test_every_committed_page_offers_a_log_command_the_cli_accepts_e2e() -> None:
    """THE ARTIFACT PIN. Each committed page is rendered from its committed JSON with the committed
    index's `followed` map; the command's id is read off the HTML. A followed name must print its
    TICKER and the CLI's own follow reader must open for it; any other name keeps the screen
    route's candidate id. The entry-price sentence must state the CLI's rule, not the screen
    date."""
    index = json.loads((MIRROR / "index.json").read_text())
    if not index.get("tickers"):
        pytest.skip("no committed dossier mirror in this worktree")
    pages = {t: json.loads((MIRROR / f"{t}.json").read_text()) for t in index["tickers"]}
    got = _node(f"""
const {{ readFileSync }} = await import("node:fs");
const index = JSON.parse(readFileSync({json.dumps(str(MIRROR / "index.json"))}, "utf8"));
const out = {{}};
for (const t of index.tickers) {{
  const d = JSON.parse(readFileSync({json.dumps(str(MIRROR))} + "/" + t + ".json", "utf8"));
  const html = mod.renderDossier(d, null, null, null, index.followed);
  const m = /log-verdict ([^ <]+) --verdict/.exec(html);
  out[t] = {{ id: m ? m[1] : null, screenDate: html.includes("from the screen's as-of date"),
             rule: html.includes("freezes at the latest close on or before the day you run it") }};
}}
console.log(JSON.stringify(out));
""")
    cfg = get_config()
    follow_file = json.loads(FOLLOWED.read_text())
    followed_pages = 0
    for ticker, row in sorted(got.items()):
        assert row["id"], f"{ticker}: the page offers no log-verdict command at all"
        assert row["rule"] and not row["screenDate"], (
            f"{ticker}: the entry-price sentence still claims the screen's as-of date")
        if ticker in follow_file:
            followed_pages += 1
            assert row["id"] == ticker, (
                f"{ticker} is followed, but its page prints `log-verdict {row['id']}` — the CLI "
                f"opens a followed name by TICKER only")
            assert asm._follow_entry(cfg, ticker) is not None, (
                f"{ticker}: the page prints the ticker route, but the CLI's follow reader is shut")
        else:
            ref = pages[ticker]["reference_date"].replace("-", "")
            assert row["id"] == f"{ticker}-screen2-{ref}", (
                f"{ticker} is not followed, so the screen route's candidate id applies; got "
                f"{row['id']!r}")
    assert followed_pages, "no committed page is followed — the pin checked nothing it exists for"


def test_the_log_id_follows_the_clis_two_doors() -> None:
    """The route table, including the shapes no committed page has yet. A non-default book is
    reached only through the follow list, so it logs by ticker even on an index that predates the
    map; a name followed under the default book logs by ticker unless the screen currently ranks
    it (then the screen route governs, as `_finalist` decides); a name on neither route is
    unchanged."""
    ref = "2026-08-24"
    cases = [
        ("UBER", {"sleeve": "quality"}, "UBER"),                       # legacy index, no map
        ("WLK", {"sleeve": "ultra_short_term", "rank": 183,
                 "followed": {"WLK": "ultra_short_term"}}, "WLK"),     # ruled: ranked AND followed
        ("NFLX", {"sleeve": "overshoot", "rank": None,
                  "followed": {"NFLX": "overshoot"}}, "NFLX"),         # followed, default book
        ("NFLX", {"sleeve": "overshoot", "rank": None}, "NFLX-screen2-20260824"),  # no map yet
        ("ACME", {"sleeve": "overshoot", "rank": 12,
                  "followed": {"ACME": "overshoot"}}, "ACME-screen2-20260824"),   # screen governs
        ("SMPL", {"sleeve": "overshoot", "rank": None}, "SMPL-screen2-20260824"),  # unchanged
        ("uber", {"sleeve": "quality"}, "UBER"),                       # the CLI upper-cases too
    ]
    got = _node(f"""
const cases = {json.dumps([[t, o] for t, o, _ in cases])};
console.log(JSON.stringify(cases.map(([t, o]) => mod.logVerdictId(t, "{ref}", o))));
""")
    assert got == [want for _, _, want in cases]


def test_the_mirror_carries_the_follow_file_verbatim() -> None:
    """The page decides from `index.json`'s `followed`, so the mirror must say exactly what the
    committed follow file says — every entry, with its book."""
    index = json.loads((MIRROR / "index.json").read_text())
    assert "followed" in index, "the committed mirror carries no follow map — rebuild frontend/"
    expect = {t.upper(): e["sleeve"] for t, e in json.loads(FOLLOWED.read_text()).items()}
    assert index["followed"] == expect


def test_the_page_reads_the_follow_map_off_the_committed_index() -> None:
    """`getFollowed` is the page's only way to the map. Driven against the committed index through
    a stubbed `fetch`, plus an index built before the field existed (→ {}, so the page falls back
    to the book alone rather than failing)."""
    if not shutil.which("node"):
        pytest.skip("node not available")
    snaps = (ROOT / "frontend" / "lib" / "snapshots.js").resolve().as_uri()
    index = (MIRROR / "index.json").read_text()
    out = []
    for body in (index, json.dumps({"tickers": ["X"], "sleeves": {"X": "overshoot"}})):
        driver = f"""
globalThis.fetch = async () => ({{ ok: true, status: 200, text: async () => {json.dumps(body)} }});
const {{ getFollowed }} = await import("{snaps}?v={len(out)}");
console.log(JSON.stringify(await getFollowed()));
"""
        proc = subprocess.run(["node", "--input-type=module", "-e", driver],
                              capture_output=True, text=True, cwd=ROOT)
        assert proc.returncode == 0, proc.stderr
        out.append(json.loads(proc.stdout))
    assert out[0] == json.loads(index)["followed"] and out[0], "getFollowed lost the committed map"
    assert out[1] == {}, "a legacy index must read as no map, not fail"


def test_both_log_command_call_sites_pass_the_follow_map() -> None:
    """The underwrite-only page renders the same block from `render()`; a call site that drops the
    map silently falls back to the book alone and mislabels a followed default-book name."""
    src = DOSSIER_JS.read_text()
    # every hop from the fetch to the block: render() → renderDossier → appendixTier →
    # recordAndReproduce → loggedVerdict (the e2e pin above enters at renderDossier)
    assert re.search(r"Promise\.all\(\[getDossierIndex\(\), getLedger\(\), getFollowed\(\)\]\)",
                     src), "render() no longer fetches the follow map"
    assert "renderDossier(d, verdict, card, mark, followed)" in src
    assert "appendixTier(d, verdict, m, card, followed)" in src
    assert "recordAndReproduce(d, verdict, card, followed)" in src
    calls = re.findall(r"\$\{loggedVerdict\((.*?)\}\)\}", src, re.S)
    assert len(calls) == 2, f"expected the dossier and underwrite call sites, found {len(calls)}"
    for call in calls:
        assert "followed" in call, f"a log-command call site omits the follow map: {call!r}"
