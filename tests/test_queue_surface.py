"""THE RENDERED QUEUE ROW — end-to-end over the committed snapshot.

The Tier-2 volume overlay has always been a term in `priority_score` (ranker.py: quality +
volume_overlay), and the ranker page's own subtitle tells the reader so — but the queue had no
column for it, so a ±0.05 swing in Score was asserted and unexplainable. `volume_state` was parsed
into the frontend snapshot object (snapshots.js) and rendered by nothing.

These pins are END-TO-END (real committed JSONL -> the REAL render() -> assertions on the HTML a
human reads), because the failure class here is WIRING: a source grep for `volCell` stays green
when the call site is deleted from the row template, and a unit call of `volCell` stays green when
the COLS entry and the <td> drift apart. Both are invisible to anything but a real render.

Living-artifact discipline (CLAUDE.md TEST-LAYER): the snapshot is re-drawn by every screen run, so
nothing here pins a VALUE. The invariants are structural — the column exists, every row has exactly
as many cells as there are headers, and the cell text is byte-identical to the snapshot field it
came from (which is what makes "never re-parse the label" checkable).
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
QUEUE = ROOT / "data" / "snapshots" / "ranked_queue.jsonl"
VOL_COLUMN_LABEL = "Volume (T2)"

# The renderer touches only `root.innerHTML` plus two document sinks, so a handful of plain objects
# stands in for the DOM. `fetch` is redirected onto the committed files: ./snapshots/x is served
# from data/snapshots/x, so this runs without a build.py deploy copy in the worktree.
_DRIVER = """
import { readFile } from 'node:fs/promises';
const ROOT = __ROOT__, DATA = __DATA__, MUTATE = __MUTATE__;
globalThis.fetch = async (p) => {
  const rel = String(p).replace(/^\\.\\//, '').replace(/^\\//, '');
  for (const base of [ROOT, DATA]) {
    try {
      let buf = await readFile(base + '/' + rel, 'utf8');
      if (MUTATE && rel.endsWith('ranked_queue.jsonl')) {
        const lines = buf.split('\\n').filter((l) => l.trim());
        const first = JSON.parse(lines[0]);
        first.volume_state = 'UNKNOWN';
        first.volume_overlay = 0.0;
        lines[0] = JSON.stringify(first);
        buf = lines.join('\\n');
      }
      return { ok: true, status: 200, json: async () => JSON.parse(buf), text: async () => buf };
    } catch { /* fall through to the next base */ }
  }
  return { ok: false, status: 404, json: async () => ({}), text: async () => '' };
};
const sinks = {};
globalThis.document = {
  getElementById: (id) => (sinks[id] ||= { innerHTML: '', querySelectorAll: () => [] }),
};
const noop = { addEventListener: () => {} };
const root = { innerHTML: '', querySelector: () => noop };
const v = await import(ROOT + '/views/edge2/ranker.js');
await v.render(root, {}, { item: { title: 'Ranker', blurb: '' }, frame: (i, o) => o.bodyHtml });
console.log(JSON.stringify({
  head: (sinks['rk-head'] || {}).innerHTML || '',
  body: (sinks['rk-body'] || {}).innerHTML || '',
  page: root.innerHTML,
}));
"""


def _render(mutate: bool = False) -> dict[str, str]:
    """Run the real ranker view over the committed queue; return its head/body/page html."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    if not QUEUE.exists():
        pytest.skip("no committed ranked_queue.jsonl in this worktree")
    script = (_DRIVER
              .replace("__ROOT__", json.dumps(str(FRONTEND)))
              .replace("__DATA__", json.dumps(str(ROOT / "data")))
              .replace("__MUTATE__", "true" if mutate else "false"))
    proc = subprocess.run(["node", "--input-type=module", "-e", script],
                          capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        raise AssertionError(
            f"the ranker page THREW while rendering the committed queue — in the browser it shows "
            f"nothing but its loading placeholder:\n{proc.stderr.strip()}")
    out: dict[str, str] = json.loads(proc.stdout)
    return out


def _rows(body: str) -> list[str]:
    return re.findall(r"<tr\b.*?</tr>", body, re.S)


def test_the_queue_row_shows_the_volume_term_that_moves_its_score() -> None:
    """THE WIRING PIN. Score = quality + volume_overlay, and the page says so in its own subtitle,
    so the read must be visible on the row. Asserts the header exists AND that the state text
    actually reaches the rendered cells — a COLS entry alone would satisfy the first and leave the
    column blank in every browser."""
    r = _render()
    head, body = r["head"], r["body"]
    assert VOL_COLUMN_LABEL in head, f"no volume column header in the rendered thead: {head[:400]}"
    rows = _rows(body)
    assert len(rows) > 50, f"queue body rendered {len(rows)} rows — the page did not reach content"

    snap = [json.loads(x) for x in QUEUE.read_text().splitlines() if x.strip()]
    by_ticker = {r["ticker"]: r for r in snap}
    checked = 0
    for row in rows:
        m = re.search(r'data-ticker="([^"]+)"', row)
        assert m, f"row without a ticker: {row[:200]}"
        rec = by_ticker.get(m.group(1))
        if not rec or not rec.get("volume_state") or rec["volume_state"] == "UNKNOWN":
            continue
        # BYTE-IDENTICAL to the snapshot field. This is the checkable form of "the label is never
        # re-parsed and never re-formatted" — any regex that lifted the multiple out, or any
        # rounding of it, breaks this without needing to know today's values.
        assert f">{rec['volume_state']}<" in row, (
            f"{m.group(1)}: snapshot says {rec['volume_state']!r} but the rendered row does not "
            f"carry it verbatim:\n{row[:400]}")
        checked += 1
    assert checked > 50, f"only {checked} rows carried a volume state — too few to pin"


def test_every_rendered_row_has_exactly_one_cell_per_header() -> None:
    """A <td> added to the row template without its COLS entry (or the reverse) silently shifts
    every column right of it — the whole table reads wrong while looking fine. Structural, so it
    guards the next column added here as much as this one."""
    r = _render()
    head, body = r["head"], r["body"]
    n_head = len(re.findall(r"<th\b", head))
    assert n_head >= 13, f"expected the queue's full header set, got {n_head}"
    for row in _rows(body):
        n_cells = len(re.findall(r"<td\b", row))
        assert n_cells == n_head, (
            f"row has {n_cells} cells against {n_head} headers — the columns are misaligned:\n"
            f"{row[:400]}")


def test_an_unknown_volume_read_renders_a_dash_not_the_word_unknown() -> None:
    """THE NEGATIVE PIN, taken by mutating a REAL committed row rather than hand-rolling a fixture.
    `volume_overlay()` returns the literal string "UNKNOWN" when volume_spike is unevaluable; the
    cell must degrade to the muted dash every other unknown on this page uses, never print the
    sentinel. No committed row is UNKNOWN today, which is exactly why this needs a guard."""
    clean = _render()["body"]
    mutated = _render(mutate=True)["body"]
    assert clean != mutated, (
        "the mutation changed nothing — the guard cannot fail, so it is untested")

    first = _rows(mutated)[0]  # the mutation was applied to the first snapshot line
    assert "UNKNOWN" not in first, f"the UNKNOWN sentinel leaked into the row:\n{first[:400]}"
    assert "—" in first, f"the unknown volume read did not degrade to a dash:\n{first[:400]}"
    # and the mutation is confined to the row it was applied to
    assert len(_rows(mutated)) == len(_rows(clean))


def test_the_wide_queue_table_scrolls_inside_its_own_container() -> None:
    """13 columns overruns the content area on a 1280px laptop — measured in the browser at 13px of
    page-level horizontal scroll before this wrapper, gone after. `table.data th` is
    white-space:nowrap globally, so the table cannot shrink below its headers and no amount of cell
    styling fixes it; the fix is the wrapper uw-card.js and dossier.js already use for wide tables.

    Layout is not observable from the node harness (no engine), so this pins the STRUCTURE that
    produces it: the queue table is inside an overflow-x container. Anyone removing the wrapper —
    or adding a 14th column and re-breaking the page — trips this."""
    page = _render()["page"]
    m = re.search(r'(<div[^>]*overflow-x:\s*auto[^>]*>)\s*<table[^>]*id="rk-table"', page)
    assert m, (
        "the queue table is not wrapped in an overflow-x container — a 13-column table pushes the "
        f"whole page sideways on a 1280px viewport. Rendered around the table:\n"
        f"{page[max(0, page.find('rk-table') - 300):page.find('rk-table') + 80]}")
