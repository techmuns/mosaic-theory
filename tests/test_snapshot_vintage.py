"""THE COHORT IS MEASURED OVER THE RUN THE CANDIDATES CAME FROM, NOT THE NEWEST ON DISK.

THE GAP. `rank_from_snapshots` ranks from `candidate_records.jsonl` and, until now, asked
`cohort_reads` for the cohort — which took the NEWEST `screen_runs/*.jsonl` on disk. Nothing
asserted the two were the same vintage. Today they agree, so nothing was visibly wrong; the moment
a re-rank runs against a stale candidate file, or a screen lands between those two steps, a median
measured over one 180-day window is subtracted from returns measured over another. Both numbers
look fine on their own — which is why this fails silently and why it needs a guard rather than
care.

WHAT THIS IS NOT. A review noted "two rows already mismatched" between the artifacts. Checked:
MRLN and OPI are IN the newest run, at `grain=candidate` with `outcome=NOT_EVALUATED` and no
return — the `carry_not_evaluated` routing policy, which `relatives_for_run` correctly skips. That
is routing, not drift. The gap is real; that particular symptom was not a symptom of it.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.cohort import cohort_reads, run_for_stamp, screen_run_files, sic_by_ticker

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"


def test_the_run_is_chosen_by_the_candidates_stamp_not_by_recency() -> None:
    """THE FIX ITSELF. Given a stamp, the earlier run must be selected even though a newer one sits
    on disk — otherwise the guard is a comment."""
    runs = screen_run_files(SNAP)
    if len(runs) < 2:
        pytest.skip("need two committed runs to tell recency from selection")
    older = runs[0]
    chosen = run_for_stamp(SNAP, older.stem[:10])
    assert chosen.stem.startswith(older.stem[:10]), (
        f"asked for {older.stem[:10]}, got {chosen.stem} — selection is falling back to recency")
    assert chosen != runs[-1] or runs[-1].stem.startswith(older.stem[:10])


def test_the_latest_run_wins_among_same_day_runs() -> None:
    """2026-07-29 has -01, -02 and -03. A later run of the same date supersedes its predecessors —
    the existing convention, pinned so a future change to sorting cannot silently pick -01."""
    runs = screen_run_files(SNAP)
    days = {}
    for p in runs:
        days.setdefault(p.stem[:10], []).append(p.stem)
    multi = {d: v for d, v in days.items() if len(v) > 1}
    if not multi:
        pytest.skip("no same-day runs committed")
    day, stems = next(iter(multi.items()))
    assert run_for_stamp(SNAP, day).stem == max(stems), (
        f"same-day runs {stems} resolved to something other than the latest")


def test_a_stamp_with_no_committed_run_fails_loud() -> None:
    """FAIL LOUD, NEVER FABRICATE. A cohort measured over a guessed window is worse than no cohort:
    the number is plausible and wrong, and nothing downstream can tell."""
    with pytest.raises(ValueError, match="no screen run for"):
        run_for_stamp(SNAP, "1999-01-01")


def test_a_stale_candidate_file_does_not_borrow_a_newer_window() -> None:
    """THE DRIFT CASE, WHICH HAS NEVER HAPPENED — simulated because waiting for it means shipping
    the bug. A candidate set stamped with an EARLIER run must produce that run's medians, not the
    newest run's. If both stamps returned identical reads, the selection is not doing anything."""
    runs = screen_run_files(SNAP)
    if len(runs) < 2:
        pytest.skip("need two committed runs")
    sic = sic_by_ticker(SNAP)
    older, newest = runs[0].stem[:10], runs[-1].stem[:10]
    if older == newest:
        pytest.skip("all committed runs share a date")
    a = cohort_reads(SNAP, sic, run_stamp=older)
    b = cohort_reads(SNAP, sic, run_stamp=newest)
    shared = set(a) & set(b)
    assert shared, "the two runs share no names — cannot compare"
    differing = [t for t in shared if a[t].median != b[t].median]
    assert differing, (
        f"reads for {older} and {newest} are identical across {len(shared)} names — the stamp is "
        f"being ignored and the newest run used regardless")


def test_the_committed_artifacts_agree_on_their_vintage() -> None:
    """AND THE CORPUS ITSELF. The queue, the candidate records and the newest screen-run LOG must
    all name the same run — a disagreement here means one of the three was written against a
    different world.

    KEYED ON THE `.jsonl` RUN LOG, NOT THE MANIFEST, because the run log is the artifact
    `cohort_reads` actually selects and reads. The two are not interchangeable: `next_run_id`
    records that a manifest can be committed for a run whose rows were never written
    (`2026-08-12-01.manifest.json` sat on disk with no row file), and `run_weekly` files the
    manifest at the UNIVERSE stage — so an aborted run leaves a newer manifest while the newest
    thing the cohort can be measured over is still the previous run. Asserting against the manifest
    reddens on that, which is a state this pin is not about, and says nothing about the file the
    medians come from.
    """
    cands = [json.loads(x) for x in
             (SNAP / "candidate_records.jsonl").read_text().splitlines() if x.strip()]
    queue = [json.loads(x) for x in
             (SNAP / "ranked_queue.jsonl").read_text().splitlines() if x.strip()]
    cstamps = {str(c["screen_run_at"])[:10] for c in cands}
    qstamps = {str(q["screen_run_at"])[:10] for q in queue}
    assert len(cstamps) == 1, f"candidate records carry mixed stamps: {sorted(cstamps)}"
    assert cstamps == qstamps, (
        f"candidate records say {sorted(cstamps)} but the queue says {sorted(qstamps)} — one was "
        f"written against a different screen run")
    newest = screen_run_files(SNAP)[-1]
    assert run_for_stamp(SNAP, next(iter(cstamps))) == newest, (
        f"the committed candidates are stamped {sorted(cstamps)} but the newest committed screen "
        f"run is {newest.stem} — the queue on disk was ranked against a run that is no longer the "
        f"latest, so its cohort column is measured over an older window than a re-screen would")


def test_a_missing_run_degrades_to_no_cohort_rather_than_losing_the_queue() -> None:
    """INFORM-ONLY MUST NOT BE ABLE TO STOP THE QUEUE (the rule #503 established). `run_for_stamp`
    raises `ValueError` on an unknown stamp; the writer must turn that into "no cohort", not a lost
    queue.

    AST, NOT A TEXT SCAN. The first cut asserted the word "except" appeared within 400 characters
    either side of the call — and the 400 characters BEFORE it are a free-text comment block, so
    any future comment containing "except"/"exception" would have satisfied this with the
    `try` deleted. It also never checked WHICH exceptions are caught: `run_for_stamp` raises
    `ValueError`, and a handler narrowed to `OSError` would leave a stale-candidates re-rank
    aborting the whole queue write for a display column.
    """
    import ast

    src = (ROOT / "vinci" / "orchestrator.py").read_text()
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "rank_from_snapshots")
    guarded = {
        id(call)
        for node in ast.walk(fn) if isinstance(node, ast.Try)
        # ValueError must be among the types caught, by name or via a bare `except:`.
        if any(h.type is None or "ValueError" in ast.unparse(h.type) for h in node.handlers)
        for body in node.body for call in ast.walk(body)
        if isinstance(call, ast.Call) and ast.unparse(call.func).endswith("cohort_reads")
    }
    calls = [n for n in ast.walk(fn)
             if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("cohort_reads")]
    assert calls, "rank_from_snapshots no longer calls cohort_reads"
    for call in calls:
        assert id(call) in guarded, (
            "the cohort_reads call is not inside a try that catches ValueError — run_for_stamp "
            "raises one on an unknown stamp, and an unguarded raise here takes the whole queue "
            "down for a display column")


def test_a_mixed_vintage_candidate_file_gets_no_cohort_and_still_gets_a_queue(
    tmp_path: pathlib.Path) -> None:
    """END-TO-END, ON A STAGED COPY OF THE REAL CORPUS. `cands[0].screen_run_at` asserted by
    accident that `candidate_records.jsonl` is single-vintage — a file carrying rows from two runs
    (an export interrupted mid-rewrite, a hand-merged file) would bind the cohort to whichever run
    sits FIRST in the file while the queue is ranked over every row. Same silent mixed-vintage read,
    one level up.

    So it is REFUSED, not resolved — and refused INSIDE the guard, so the queue still gets written
    with every row reading "no cohort" (rule #503: inform-only must never stop the queue)."""
    from vinci.config import Config
    from vinci.orchestrator import rank_from_snapshots

    if not (SNAP / "candidate_records.jsonl").is_file():
        pytest.skip("no committed candidate records")
    snaps = tmp_path / "snapshots"
    snaps.mkdir(parents=True)
    for src in SNAP.iterdir():
        (snaps / src.name).symlink_to(src)
    rows = [x for x in (SNAP / "candidate_records.jsonl").read_text().splitlines() if x.strip()]
    if len(rows) < 2:
        pytest.skip("need two candidate rows to mix their stamps")
    (snaps / "candidate_records.jsonl").unlink()
    # One row moved to a DIFFERENT run — and one that exists on disk, so nothing else can be
    # blamed for the refusal.
    # BOTH STAMPS ARE DERIVED, NEVER LITERAL (2026-09-23). This read
    # `.replace("2026-08-24T00:00:00", "2026-07-29T00:00:00")`, so the moment the committed
    # candidates advanced to the 2026-09-22 screen the replace matched NOTHING: the file stayed
    # single-vintage, cohorts were produced exactly as they should be, and the test reddened
    # claiming the mixed-vintage guard had failed. The guard was fine; the mutation had silently
    # stopped happening. A pin whose SETUP is pinned to a moving artifact tests the artifact.
    stamp = json.loads(rows[0])["screen_run_at"]
    others = sorted(p.stem for p in (SNAP / "screen_runs").glob("*.jsonl")
                    if not p.stem.startswith(stamp[:10]))
    assert others, "no other committed screen run to move a row to"
    other = f"{others[-1][:10]}T00:00:00"
    moved = rows[0].replace(stamp, other)
    assert moved != rows[0], f"the row's stamp {stamp!r} was not replaced — the file is unmixed"
    (snaps / "candidate_records.jsonl").write_text("\n".join([moved, *rows[1:]]) + "\n")

    ranked = rank_from_snapshots(Config(data_dir=tmp_path))
    assert len(ranked) == len(rows), "the mixed-vintage refusal cost the queue its rows"
    assert all(r.cohort is None for r in ranked), (
        "a mixed-vintage candidate file still produced cohort reads — the cohort was measured "
        "over whichever run happened to be first in the file")


def test_the_writer_actually_passes_the_candidates_stamp() -> None:
    """PIN THE CALL SITE, NOT THE HELPER — the fifth time this exact trap has bitten in this
    session, and it bit here too: every other pin in this file went green with the writer no longer
    passing `run_stamp` at all.

    `cohort_reads` defaults to the newest run when given no stamp, precisely so a caller that does
    not care still works. That default is what makes dropping the argument silent: the queue keeps
    building, the cohorts keep computing, and the vintage guarantee is simply gone."""
    import ast

    src = (ROOT / "vinci" / "orchestrator.py").read_text()
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "rank_from_snapshots")
    calls = [n for n in ast.walk(fn)
             if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("cohort_reads")]
    assert calls, "rank_from_snapshots no longer calls cohort_reads"
    for call in calls:
        kwargs = {k.arg for k in call.keywords}
        assert "run_stamp" in kwargs, (
            "the writer calls cohort_reads WITHOUT run_stamp, so the cohort silently reverts to "
            "the newest run on disk while the queue is ranked from the candidate file — the exact "
            "mixed-vintage drift this module exists to prevent")
        stamp = next(k.value for k in call.keywords if k.arg == "run_stamp")
        # ONE ASSIGNMENT HOP, so the pin survives the stamp being hoisted into a local (it has to
        # be, to refuse a mixed-vintage candidate file before the call) WITHOUT degrading into a
        # substring check on a variable NAME — `run_stamp=whatever_screen_run_at` would otherwise
        # satisfy a bare `in` while sourcing the stamp from anywhere at all.
        derived = {
            t.id
            for node in ast.walk(fn) if isinstance(node, ast.Assign)
            if "screen_run_at" in ast.unparse(node.value)
            for t in node.targets if isinstance(t, ast.Name)
        }
        used = {n.id for n in ast.walk(stamp) if isinstance(n, ast.Name)}
        assert ".screen_run_at" in ast.unparse(stamp) or used & derived, (
            f"run_stamp is {ast.unparse(stamp)!r} — it must come from the CANDIDATES' own "
            f"screen_run_at, directly or through one local, not from anything else")

