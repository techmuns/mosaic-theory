"""THE RENDERED QUEUE ROW — end-to-end over the committed snapshot.

The Tier-2 volume overlay has always been a term in `priority_score` (ranker.py: quality +
volume_overlay), and the ranker page's own subtitle tells the reader so — but the queue had no
column for it, so a ±0.05 swing in Score was asserted and unexplainable. `volume_state` was parsed
into the frontend snapshot object (snapshots.js) and rendered by nothing.

These pins are END-TO-END (real committed JSONL -> the REAL render() -> assertions on the HTML a
human reads), because the failure class here is WIRING: a source grep for `volCell` stays green
when the call site is deleted from the row template, and a unit call of `volCell` stays green when
the COLS entry and the <td> drift apart. Both are invisible to anything but a real render.

TWO RENDER PATHS, both pinned. After the 2026-08-12 audit the cell LEADS WITH THE RATIO from the
structured `volume_spike` field. A snapshot written before that field existed has no ratio, so the
cell falls back to the scorer's string rather than digging the number out of it. The committed
snapshot is currently a legacy one, so the fallback is what real traffic hits today and the
structured path is exercised by injecting the field — never by hand-rolling a fixture.

Living-artifact discipline (CLAUDE.md TEST-LAYER): the snapshot is re-drawn by every screen run, so
nothing here pins a VALUE that the screen produces. The invariants are structural, plus "the cell
is byte-identical to the field it came from" — the checkable form of "never re-parse the label".
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
VOL_COLUMN_LABEL = "Volume vs 90d"
# the two words the audit retired: they name a MECHANISM (who traded, why) that one session's
# volume cannot contain. "heavy distribution" was wrong on 2 of 10 names on the 2026-07-29 queue.
RETIRED_WORDS = ("distribution", "exhausted")

# The renderer touches only `root.innerHTML` plus two document sinks, so a handful of plain objects
# stands in for the DOM. `fetch` is redirected onto the committed files: ./snapshots/x is served
# from data/snapshots/x, so this runs without a build.py deploy copy in the worktree.
_DRIVER = """
import { readFile } from 'node:fs/promises';
const ROOT = __ROOT__, DATA = __DATA__, MODE = __MODE__;
globalThis.fetch = async (p) => {
  const rel = String(p).replace(/^\\.\\//, '').replace(/^\\//, '');
  for (const base of [ROOT, DATA]) {
    try {
      let buf = await readFile(base + '/' + rel, 'utf8');
      if (MODE && rel.endsWith('ranked_queue.jsonl')) {
        const lines = buf.split('\\n').filter((l) => l.trim()).map((l) => JSON.parse(l));
        if (MODE === 'unknown') {
          lines[0].volume_state = 'UNKNOWN';
          lines[0].volume_overlay = 0.0;
          delete lines[0].volume_spike;
        } else if (MODE === 'spike') {
          // the structured field a post-2026-08-12 screen emits, injected onto REAL rows
          const inj = [3.75, 0.4, 12.4];
          lines.forEach((r, i) => { r.volume_spike = inj[i] !== undefined ? inj[i] : 1.0; });
        } else if (MODE === 'trend') {
          // what a SCREEN run emits; injected because features.py computes it from bars
          const inj = [0.27, 0.31, 0.21, 3.7, 1.31, 1.09, 0.92, 0.89, 0.53, 0.59, 0.38, 1.1, 0.83];
          lines.forEach((r) => { r.volume_spike = 0.72; r.volume_trend = inj; });
        } else if (MODE === 'stale' || MODE === 'fresh') {
          // age is relative to the RUNNING clock, so both cases are stamped here rather than
          // relying on how old the committed snapshot happens to be on the day the suite runs
          const d = new Date(Date.now() - (MODE === 'stale' ? 40 : 0) * 86400000);
          lines.forEach((r) => { r.screen_run_at = d.toISOString().slice(0, 19); });
        }
        buf = lines.map((r) => JSON.stringify(r)).join('\\n');
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


def _render(mode: str = "") -> dict[str, str]:
    """Run the real ranker view over the committed queue; return its head/body/page html."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    if not QUEUE.exists():
        pytest.skip("no committed ranked_queue.jsonl in this worktree")
    script = (_DRIVER
              .replace("__ROOT__", json.dumps(str(FRONTEND)))
              .replace("__DATA__", json.dumps(str(ROOT / "data")))
              .replace("__MODE__", json.dumps(mode)))
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


def _vol_cells(body: str) -> list[str]:
    """The 11th cell of every row — the volume column, by position."""
    out = []
    for row in _rows(body):
        tds = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S)
        if len(tds) >= 11:
            out.append(re.sub(r"<[^>]+>", "", tds[10]).strip())
    return out


def test_the_queue_row_shows_the_volume_term_that_moves_its_score() -> None:
    """THE WIRING PIN. Score = quality + volume_overlay, and the page says so in its own subtitle,
    so the read must be visible on the row. Asserts the header exists AND that the value actually
    reaches the rendered cells — a COLS entry alone would satisfy the first and leave the column
    blank in every browser."""
    r = _render()
    assert VOL_COLUMN_LABEL in r["head"], f"no volume column header in the thead: {r['head'][:400]}"
    assert len(_rows(r["body"])) > 50, "queue body did not reach content"
    filled = [c for c in _vol_cells(r["body"]) if c and c != "—"]
    assert len(filled) > 50, f"only {len(filled)} rows carried a volume read — the column is blank"


def test_the_volume_header_discloses_that_it_is_a_single_session() -> None:
    """Every other column on this page is windowed (52w depth, 180d idio, ~5y multiple); this one
    is ONE session and flips band 43% of the time between adjacent sessions (audit, STATE.md §5).
    A reader comparing it to its neighbours will assume a window unless told, so the disclosure
    rides on the header itself, not on a doc nobody opens."""
    head = _render()["head"]
    # markup-agnostic: take that header's whole cell, then find its tip wherever inside it sits (on
    # the <button> since the a11y change — the pin should not have to move every time the tag does)
    cell = re.search(r'<th[^>]*data-sort="volumeSpike".*?</th>', head, re.S)
    assert cell, f"no volumeSpike header in the thead:\n{head[:600]}"
    m = re.search(r'title="([^"]+)"', cell.group(0))
    assert m, f"the volume header carries no title attribute:\n{cell.group(0)[:400]}"
    tip = m.group(1).lower()
    assert "session" in tip, f"the header tip does not say it is a single session: {m.group(1)}"
    assert "90-day" in tip or "90d" in tip, f"the header tip does not state the basis: {m.group(1)}"


def test_a_structured_spike_renders_as_the_bare_ratio_not_a_band_word() -> None:
    """THE AUDIT'S FIX. Post-2026-08-12 snapshots carry `volume_spike`, and the cell must lead with
    the RATIO — the page's own rule is "columns lead with the interpretable quantity", and the band
    word was both redundant with the number and, for two of the four bands, a mechanism claim the
    input cannot support. Values are INJECTED onto real committed rows, so this pins the format
    without pinning anything the screen produces."""
    cells = _vol_cells(_render("spike")["body"])
    assert cells[:3] == ["3.75×", "0.40×", "12.4×"], (
        f"expected the bare ratio, 2dp under 10 and 1dp above; got {cells[:3]}")
    for c in cells:
        assert re.fullmatch(r"\d+\.\d+×", c), f"volume cell is not a bare ratio: {c!r}"
        assert not any(w in c.lower() for w in RETIRED_WORDS), f"retired word led the cell: {c!r}"


def test_a_legacy_snapshot_without_the_structured_field_still_renders() -> None:
    """The committed snapshot predates `volume_spike`, so the fallback is what real traffic hits
    until the queue is regenerated. It shows the scorer's string BYTE-IDENTICALLY — the checkable
    form of "a display string is never re-parsed for its value", which is exactly the temptation
    here (the ratio is sitting right there inside the label)."""
    body = _render()["body"]
    snap = {json.loads(x)["ticker"]: json.loads(x)
            for x in QUEUE.read_text().splitlines() if x.strip()}
    if any(r.get("volume_spike") is not None for r in snap.values()):
        pytest.skip("the committed snapshot now carries volume_spike — fallback path not exercised")
    checked = 0
    for row in _rows(body):
        m = re.search(r'data-ticker="([^"]+)"', row)
        rec = snap.get(m.group(1)) if m else None
        if not rec or not rec.get("volume_state") or rec["volume_state"] == "UNKNOWN":
            continue
        assert f">{rec['volume_state']}<" in row, (
            f"{m.group(1)}: snapshot says {rec['volume_state']!r}, row does not carry it "
            f"verbatim:\n{row[:400]}")
        checked += 1
    assert checked > 50, f"only {checked} rows exercised the fallback — too few to pin"


def test_every_rendered_row_has_exactly_one_cell_per_header() -> None:
    """A <td> added to the row template without its COLS entry (or the reverse) silently shifts
    every column right of it — the whole table reads wrong while looking fine. Structural, so it
    guards the next column added here as much as this one."""
    r = _render()
    n_head = len(re.findall(r"<th\b", r["head"]))
    assert n_head >= 13, f"expected the queue's full header set, got {n_head}"
    for row in _rows(r["body"]):
        n_cells = len(re.findall(r"<td\b", row))
        assert n_cells == n_head, (
            f"row has {n_cells} cells against {n_head} headers — columns are misaligned:\n"
            f"{row[:400]}")


def test_an_unknown_volume_read_renders_a_dash_not_the_word_unknown() -> None:
    """THE NEGATIVE PIN, taken by mutating a REAL committed row rather than hand-rolling a fixture.
    `volume_overlay()` returns the literal string "UNKNOWN" when volume_spike is unevaluable; the
    cell must degrade to the muted dash every other unknown on this page uses, never print the
    sentinel. No committed row is UNKNOWN today, which is exactly why this needs a guard."""
    clean = _render()["body"]
    mutated = _render("unknown")["body"]
    assert clean != mutated, (
        "the mutation changed nothing — the guard cannot fail, so it is untested")
    first = _rows(mutated)[0]  # the mutation was applied to the first snapshot line
    assert "UNKNOWN" not in first, f"the UNKNOWN sentinel leaked into the row:\n{first[:400]}"
    assert "—" in first, f"the unknown volume read did not degrade to a dash:\n{first[:400]}"
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


def test_a_stale_queue_says_so_and_a_fresh_one_stays_quiet() -> None:
    """The queue only moves when the RANKER runs. `run_weekly()` writes it now, but a week where CI
    does not fire leaves this page serving a stale queue whose only signal is a date the reader has
    to do arithmetic on — which is how it once drifted 12 days and 95 names behind the screen that
    fed it (STATE.md §5). Both cases are stamped onto real committed rows against the running clock,
    so neither pin rots as the committed snapshot ages."""
    stale = _render("stale")["page"]
    fresh = _render("fresh")["page"]
    assert "may not have run" in stale, (
        f"a 40-day-old queue renders no staleness warning:\n{stale[:600]}")
    assert re.search(r"queue is \d+ days old", stale), "the warning does not say HOW old"
    assert "may not have run" not in fresh, (
        "a queue screened today is flagged stale — the threshold is firing on everything")


def test_the_volume_cell_draws_a_trend_sparkline_when_the_series_is_present() -> None:
    """The ratio says TODAY; the sparkline says which way volume has been moving — the distinction a
    one-session reading structurally cannot make, and the reason VRRM read 3.6× on 2026-07-29 and
    0.63× twelve days later. Injected onto real committed rows because `volume_trend` is computed
    from BARS in eod/features, so it only appears after a SCREEN run, not a rank.

    Also pins that it stays a DRAWING: no "building"/"fading" word may be derived from the series —
    that would be the same unearned mechanism claim the band labels were retired for."""
    cells = _vol_cells(_render("trend")["body"])
    body = _render("trend")["body"]
    assert body.count("<polyline") > 50, (
        f"only {body.count('<polyline')} sparklines drawn across the queue")
    assert 'role="img"' in body and "aria-label" in body, (
        "the sparkline is a silent decoration — it needs a role and a described series")
    for c in cells[:5]:
        assert re.fullmatch(r"\d+\.\d+×", c), f"the cell text is no longer the bare ratio: {c!r}"
    for word in ("building", "fading", "rising", "falling", "accumulat"):
        assert word not in body.lower(), (
            f"'{word}' derived from the volume series — draw the line, do not name a direction")


def test_a_snapshot_without_the_trend_series_still_renders_the_ratio() -> None:
    """`volume_trend` needs a SCREEN re-run, so between this change and the next weekly job every
    committed row has none. The cell must degrade to exactly the pre-sparkline state — the ratio,
    no empty SVG, no gap — or the column is broken for a week."""
    body = _render("spike")["body"]  # injects volume_spike but never volume_trend
    assert "<polyline" not in body, "a sparkline was drawn with no series behind it"
    cells = _vol_cells(body)
    assert cells[:3] == ["3.75×", "0.40×", "12.4×"], f"the ratio did not survive: {cells[:3]}"


def test_every_column_can_be_sorted_from_the_keyboard() -> None:
    """A <th> with a click handler is not focusable and has no activation semantics, so all 13
    columns were mouse-ONLY — surfaced by the operator's own inspector reporting the header as not
    keyboard-focusable. The control is now a real <button> inside a <th> carrying `aria-sort`: the
    W3C sortable-column-header shape, and the reason the sort is reachable at all.

    Structural, so it guards every column including the next one added."""
    head = _render()["head"]
    cells = re.findall(r"<th\b.*?</th>", head, re.S)
    assert len(cells) >= 13, f"expected the queue's full header set, got {len(cells)}"
    for th in cells:
        key = re.search(r'data-sort="([^"]+)"', th)
        assert key, f"header with no sort key:\n{th[:200]}"
        assert 'scope="col"' in th, f"{key.group(1)}: header is not scoped to its column"
        assert re.search(r'<button[^>]*type="button"', th), (
            f"{key.group(1)}: the sort control is not a button — it cannot be focused or activated "
            f"from the keyboard:\n{th[:250]}")
        assert re.search(r'aria-sort="(ascending|descending|none)"', th), (
            f"{key.group(1)}: no aria-sort, so which column is sorted is invisible to a screen "
            f"reader — the ▲/▼ is decoration and deliberately aria-hidden")

    active = [t for t in cells if re.search(r'aria-sort="(ascending|descending)"', t)]
    assert len(active) == 1, (
        f"{len(active)} columns claim to be the sorted one — aria-sort must name exactly one")
    arrows = re.findall(r"[▲▼]", head)
    assert arrows, "no sort direction is drawn at all"
    for a in arrows:
        assert re.search(rf'aria-hidden="true"[^>]*>[^<]*{a}', head), (
            "the ▲/▼ is not aria-hidden — a screen reader reads it as text beside the aria-sort "
            "that already says the same thing")


def test_sorting_from_the_keyboard_does_not_throw_focus_away() -> None:
    """renderHead() replaces the whole row, destroying the button that was just activated. Without
    restoring focus a keyboard sort drops the user to <body> and the next Tab restarts at the top
    of the page — reachable but unusable, which is the failure that makes "technically accessible"
    meaningless.

    Source-layer, and that is the honest limit: focus is a live-DOM behaviour and the node harness
    has no focus model. Verified for real in the browser; this stops it being deleted."""
    src = (ROOT / "frontend" / "views" / "edge2" / "ranker.js").read_text()
    handler = re.search(r'#rk-head"\)\.addEventListener\("click".*?\n  \}\);', src, re.S)
    assert handler, "the header click handler moved — re-point this pin"
    body = handler.group(0)
    assert "renderHead()" in body and ".focus()" in body, (
        "the sort handler re-renders the header without restoring focus — a keyboard sort silently "
        f"drops the user to <body>:\n{body}")
