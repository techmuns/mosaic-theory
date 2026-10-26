"""AN ANNOTATED SCREEN RUN — a committed result that stands, with what later data showed beside it.

WHY (operator ruling 2026-10-26, STATE.md §5.0 row 32 item 16). SFBS (band A, rank 5) and IESC
(band A, rank 48) passed the 2026-10-16 screen on bars where the price store had taken a 2:1 split
as a price fall. The ruling: annotate, never rewrite. These pins hold the annotation to the places a
reader meets the run — the committed `ranked_queue.md` and the app's queue — and hold the file to
its own numbers, so a hand-typed PASS that its value contradicts is refused, never shown.

Everything here runs on the COMMITTED files: the annotation, the queue, and the rendered Markdown.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
from typing import Any

import pytest
from pydantic import ValidationError

from vinci.orchestrator import QUEUE_MD_TOP, queue_annotations
from vinci.rank import render_queue_markdown
from vinci.rank.ranker import RankedCandidate
from vinci.screens.annotations import GateNote, RunAnnotations, for_screen_date, load_all

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAPS = ROOT / "data" / "snapshots"
FILE = SNAPS / "screen_runs" / "2026-10-16-01.annotations.json"


def _queue() -> list[RankedCandidate]:
    return [RankedCandidate.model_validate_json(line)
            for line in (SNAPS / "ranked_queue.jsonl").read_text().splitlines() if line.strip()]


def test_the_ruling_is_committed_and_loads() -> None:
    notes = for_screen_date(SNAPS, dt.date(2026, 10, 16))
    assert set(notes) == {"SFBS", "IESC"}
    assert {g.gate for g in notes["SFBS"].gates if not g.repaired.passes} == {"G1", "G2"}
    assert {g.gate for g in notes["IESC"].gates if not g.repaired.passes} == {"G2"}
    assert for_screen_date(SNAPS, dt.date(2026, 10, 15)) == {}


def test_the_committed_queue_markdown_is_what_the_code_renders() -> None:
    """END TO END: the committed `ranked_queue.md` equals the render of the committed queue with
    the committed annotations — so the file a reader opens carries the ruling, byte for byte."""
    rows = _queue()
    rendered = render_queue_markdown(rows, top=QUEUE_MD_TOP,
                                     annotations=queue_annotations(SNAPS, rows))
    assert rendered == (SNAPS / "ranked_queue.md").read_text()


def test_only_the_annotated_names_are_marked_and_each_is_listed() -> None:
    rows = _queue()
    md = render_queue_markdown(rows, top=QUEUE_MD_TOP, annotations=queue_annotations(SNAPS, rows))
    marked = {line.split("|")[2].strip() for line in md.splitlines()
              if line.startswith("| ") and "⚠" in line}
    assert marked == {"SFBS ⚠", "IESC ⚠"}
    section = md.split("## Annotations on this screen run", 1)[1]
    assert section.index("**SFBS** (rank 5)") < section.index("**IESC** (rank 48)")
    assert "on the corrected data -14.5% FAIL" in section and "+3.0% FAIL" in section


def test_without_annotations_the_markdown_is_unchanged() -> None:
    rows = _queue()
    plain = render_queue_markdown(rows, top=QUEUE_MD_TOP)
    assert "⚠" not in plain and "## Annotations" not in plain
    assert plain == render_queue_markdown(rows, top=QUEUE_MD_TOP, annotations={})


def test_an_annotated_name_below_the_table_cut_is_still_listed() -> None:
    """A warning on a name the table does not show must still be shown."""
    rows = _queue()
    md = render_queue_markdown(rows, top=3, annotations=queue_annotations(SNAPS, rows))
    assert "| 5 | SFBS" not in md and "**SFBS** (rank 5)" in md and "**IESC** (rank 48)" in md


def test_a_name_from_another_screen_date_is_not_marked() -> None:
    rows = _queue()
    later = [r.model_copy(update={"screen_run_at": dt.datetime(2026, 10, 23)})
             if r.ticker == "SFBS" else r for r in rows]
    ids = queue_annotations(SNAPS, later)
    assert {r.ticker for r in later if r.candidate_id in ids} == {"IESC"}


def _gate(**over: Any) -> dict[str, Any]:
    g: dict[str, Any] = {"gate": "G1", "label": "drawdown from high", "threshold": -0.30,
                         "as_committed": {"value": -0.571, "passes": True},
                         "repaired": {"value": -0.145, "passes": False}}
    g.update(over)
    return g


def test_a_pass_its_own_value_contradicts_is_refused() -> None:
    GateNote.model_validate(_gate())                                     # the committed shape
    with pytest.raises(ValidationError, match="contradicts"):
        GateNote.model_validate(_gate(repaired={"value": -0.145, "passes": True}))
    with pytest.raises(ValidationError, match="contradicts"):
        GateNote.model_validate(_gate(as_committed={"value": -0.10, "passes": True}))


def test_a_malformed_or_doubled_file_fails_loud(tmp_path: pathlib.Path) -> None:
    runs = tmp_path / "screen_runs"
    runs.mkdir()
    good = json.loads(FILE.read_text())
    (runs / "x.annotations.json").write_text(json.dumps({**good, "typo": 1}))
    with pytest.raises(ValidationError):
        load_all(tmp_path)
    doubled = {**good, "annotations": [good["annotations"][0]] * 2}
    (runs / "x.annotations.json").write_text(json.dumps(doubled))
    with pytest.raises(ValueError, match="two annotations"):
        load_all(tmp_path)


def test_the_app_receives_every_committed_annotation() -> None:
    """What `frontend/lib/snapshots.js` reads: the committed files, as written, keyed there by
    `reference_date|ticker` against the row's own `screen_run_at` date."""
    spec = importlib.util.spec_from_file_location("_notes_build", ROOT / "frontend" / "build.py")
    assert spec and spec.loader
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    mirrored = build._screen_annotations(SNAPS)  # noqa: SLF001
    assert [RunAnnotations.model_validate(m).run_id for m in mirrored] == ["2026-10-16-01"]
    keys = {f"{m['reference_date']}|{a['ticker']}" for m in mirrored for a in m["annotations"]}
    rows = {f"{str(r.screen_run_at)[:10]}|{r.ticker}" for r in _queue()}
    assert keys <= rows, "an annotation names a row the app's queue does not have"
    js = (ROOT / "frontend" / "lib" / "snapshots.js").read_text()
    assert "screen_annotations.json" in js and "String(r.screen_run_at).slice(0, 10)" in js


def test_the_queue_writer_carries_the_annotation(tmp_path: pathlib.Path) -> None:
    """The path every rank run takes: `write_queue_snapshots` re-writes the Markdown, and must keep
    the ruling on a re-write of the same run's queue."""
    from vinci.config import Config
    from vinci.orchestrator import write_queue_snapshots

    cfg = Config(data_dir=tmp_path)
    (cfg.snapshots_dir / "screen_runs").mkdir(parents=True)
    (cfg.snapshots_dir / "screen_runs" / FILE.name).write_text(FILE.read_text())
    _, md = write_queue_snapshots(cfg, _queue())
    assert md.read_text() == (SNAPS / "ranked_queue.md").read_text()


def test_a_bad_annotation_file_stops_the_writer_before_it_writes(tmp_path: pathlib.Path) -> None:
    """Review finding: the JSONL was replaced before the Markdown step could raise, leaving a new
    queue beside the old Markdown. Both are now composed first."""
    from vinci.config import Config
    from vinci.orchestrator import write_queue_snapshots

    cfg = Config(data_dir=tmp_path)
    (cfg.snapshots_dir / "screen_runs").mkdir(parents=True)
    (cfg.snapshots_dir / "screen_runs" / FILE.name).write_text('{"run_id": "x"}')
    (cfg.snapshots_dir / "ranked_queue.jsonl").write_text("old\n")
    with pytest.raises(ValidationError):
        write_queue_snapshots(cfg, _queue())
    assert (cfg.snapshots_dir / "ranked_queue.jsonl").read_text() == "old\n"


def test_one_ticker_on_two_screen_dates_marks_only_the_annotated_run() -> None:
    """Codex review of #799 (P2). A mixed-vintage queue can hold one ticker from two screen runs;
    keyed by ticker alone, the 2026-10-16 note marked BOTH rows, putting post-run corrections
    against a run they are not about. Each row is matched on its own candidate."""
    rows = _queue()
    sfbs = next(r for r in rows if r.ticker == "SFBS")
    later = sfbs.model_copy(update={"candidate_id": "SFBS-screen2-20261023", "rank": 344,
                                    "screen_run_at": dt.datetime(2026, 10, 23)})
    md = render_queue_markdown([*rows, later], annotations=queue_annotations(SNAPS, [*rows, later]))
    marked = [line.split("|")[1].strip() for line in md.splitlines()
              if line.startswith("| ") and "SFBS" in line and "⚠" in line]
    assert marked == ["5"], f"rows marked for SFBS: {marked}"
    assert "**SFBS** (rank 344)" not in md
