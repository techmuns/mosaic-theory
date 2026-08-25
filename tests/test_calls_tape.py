"""Structural pins on views/calls/tape.js — the two defects that no fixture could have caught.

THESE ARE SOURCE PINS, AND THAT IS A WEAKER LAYER THAN THE HOUSE RULE ASKS FOR. Both behaviours
below live in DOM event flow and in an async paint, neither of which this suite can drive: there is
no jsdom here and the view's only entry point takes a live `root` element. A source pin cannot
prove the fix works — it can only fail loudly when the specific line that made it work is deleted,
which is the failure mode that actually happened (the guard was simply never written). Recorded as
such rather than dressed up as an end-to-end test.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TAPE = ROOT / "frontend" / "views" / "calls" / "tape.js"


def test_a_click_inside_the_editor_does_not_reach_the_post_card_handler() -> None:
    """THE EDITOR WAS UNUSABLE ON ANY CASHTAG BUT THE FIRST. The inline editor renders INSIDE
    `.pcard`, and the card's click handler set `S.chipIdx = 0` and repainted. So clicking a bias
    button on the second cashtag applied the edit to the right key and then re-rendered the editor
    for a DIFFERENT one; clicking into the Target field repainted the pane and tore the focus off
    the input before a character could be typed. `.lchip` already stopped propagation for exactly
    this reason — `.ed` did not."""
    src = TAPE.read_text()
    m = re.search(r'q\("\.pcard",\s*\(e\)\s*=>\s*\{(.*?)\},\s*"click"\);', src, re.S)
    assert m, "the .pcard click handler was renamed — re-point this pin"
    body = m.group(1)
    assert 'closest(".ed")' in body and "return" in body, (
        "the .pcard click handler no longer exempts clicks originating inside the editor")


def test_the_export_resolves_posts_across_months_not_just_the_open_one() -> None:
    """THE EXPORT LANDED DATELESS ROWS. `S.posts` holds ONE month; `S.edits` is restored from
    localStorage and accumulates across months and sessions. Every edited row outside the open
    month exported with `date`, `quarter`, `text` and `has_video` all null — and
    `vinci calls import-labels` writes them into `gold_labels.jsonl` unchallenged, because it keys
    on tweet_id|ticker and never reads the date. The ground truth this tool exists to grow would
    have been corrupted silently."""
    src = TAPE.read_text()
    assert "async function postsByIdFor" in src, "the cross-month post index is gone"
    m = re.search(r"async function exportJsonl\(\)\s*\{(.*?)\n\}", src, re.S)
    assert m, "exportJsonl was renamed or is no longer async — re-point this pin"
    assert "postsByIdFor" in m.group(1), (
        "exportJsonl builds its post index from S.posts again — that is one month only")
    assert "new Map(S.posts.map(" not in m.group(1), "the single-month index came back"


def test_a_superseded_paint_drops_its_chart_instead_of_winning_the_race() -> None:
    """`paneChart` awaits a fetch and the keyboard fires a paint per keystroke, so two held
    j-presses start two paints and whichever fetch settles LAST wrote the chart — not necessarily
    the last post focused. The chart would show one call while the posts pane highlighted another,
    and `S.geom` (the crosshair's source of truth) would belong to the stale draw."""
    src = TAPE.read_text()
    assert "let paintSeq" in src, "the paint sequence counter is gone"
    m = re.search(r"async function paint\(root\)\s*\{(.*?)\n\}", src, re.S)
    assert m, "paint() was renamed — re-point this pin"
    body = m.group(1)
    assert "++paintSeq" in body, "paint() no longer claims a sequence number"
    assert re.search(r"!==\s*paintSeq\)\s*return", body), (
        "paint() no longer drops a superseded chart before writing it to the DOM")
