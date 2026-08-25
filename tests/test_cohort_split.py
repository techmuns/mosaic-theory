"""THE COHORT SPLIT — how much of a name's fall was its INDUSTRY's, and how much its own.

WHY IT EXISTS. Screen-2's G2 strips MARKET beta (the name against IWM) but not SECTOR, so a name
that fell with its whole industry lands in the candidate set looking idiosyncratic. PR #84 named
this on 2026-07-06 and shipped the SIC labels; nothing ever computed the split they were for. The
cost is concrete: BRBR, SMPL and VITL are three of the sixteen committed dossiers, one industry
cohort, all inside the top five — three CIQ pulls against substantially one de-rating.

WHAT IS PINNED HERE, and what deliberately is not. The FENCE (it cannot reach the score), the
ABSTENTION (a near-tie makes no call), the ABSENCE handling (too few peers is not a cohort), and
the COVERAGE GUARD. Not pinned: any specific median or residual on the living queue — those move
every screen, and a value-level pin on a re-drawn artifact is guaranteed to rot (TEST-LAYER RULE).
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from vinci.cohort import (
    MIN_PEERS,
    NEAR_TIE,
    cohort_reads,
    medians_for_run,
    relatives_for_run,
    screen_run_files,
    sic_by_ticker,
)
from vinci.config import get_config
from vinci.schemas.cohort import CohortCall

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"


# --- the fence: it must never be able to reach the score -----------------------------------------

def test_the_split_can_never_enter_the_scorer_or_the_gate() -> None:
    """``vinci.cohort`` is SECTOR-DERIVED, so it is fenced exactly as ``vinci.sectors`` is: the
    moment a cohort quantity reaches a weight, a threshold or a sort, the queue becomes a
    dressed-up sector-momentum screen — the trap Edge-3 was falsified into.

    The SCHEMA (`vinci.schemas.cohort`) is deliberately import-free of sectors so `RankedCandidate`
    can CARRY a read while the derivation stays outside; that split is what this pin protects."""
    for pkg in ("rank", "screens"):
        for src in (ROOT / "vinci" / pkg).glob("*.py"):
            for node in ast.walk(ast.parse(src.read_text())):
                mods: list[str] = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                elif isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                for m in mods:
                    assert not (m == "vinci.cohort" or m.startswith("vinci.cohort.")), (
                        f"{src.name} imports {m} — the cohort split must not gate or score")

    # ...and the schema itself must stay sector-free, or the fence above is bypassed by import.
    # AST, NOT TEXT — the schema's own docstring NAMES `vinci.sectors` to explain why it does not
    # import it, and a substring check duly failed on that prose. The same lesson the wall-clock
    # guard already carries: scan the executable shape, never the words describing it.
    schema_src = (ROOT / "vinci" / "schemas" / "cohort.py").read_text()
    imported: list[str] = []
    for node in ast.walk(ast.parse(schema_src)):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
    for banned in ("vinci.sectors", "vinci.cohort", "vinci.sic_table"):
        assert not any(m == banned or m.startswith(banned + ".") for m in imported), (
            f"the cohort SCHEMA imports {banned} — vinci.rank holds this type, so that would pull "
            f"the derivation back inside the fence (imports seen: {imported})")


def test_attaching_the_split_changes_no_order_and_no_score() -> None:
    """THE END-TO-END FENCE, on the real committed artifacts. The read is attached by the WRITER
    after ``rank_candidates`` has returned, so it is structurally incapable of re-ordering — this
    asserts that rather than trusting it.

    It matters because ranking BY the residual was pre-registered, measured across four snapshots
    and FALSIFIED: its top-25 churns more than the raw order at every interval, 28% inside two
    days. The split informs; it never sorts."""
    from vinci.orchestrator import carry_forward_assessment, rank_from_snapshots

    cfg = get_config()
    if not (cfg.snapshots_dir / "candidate_records.jsonl").is_file():
        pytest.skip("no committed candidate records")
    flags, causes = carry_forward_assessment(cfg)
    rows = rank_from_snapshots(cfg, structural_flags=flags, annotations=causes)
    committed = [json.loads(x) for x in
                 (cfg.snapshots_dir / "ranked_queue.jsonl").read_text().splitlines() if x.strip()]
    assert [r.ticker for r in rows] == [c["ticker"] for c in committed], (
        "re-ranking with the cohort attached changed the ORDER — the split has reached the sort")
    assert [r.priority_score for r in rows] == [c["priority_score"] for c in committed], (
        "re-ranking with the cohort attached changed a SCORE — the split has reached the scorer")


# --- the call ------------------------------------------------------------------------------------

def test_a_near_tie_makes_no_call() -> None:
    """ABSTENTION IS THE MEASURED RULE, not caution. Across four snapshots the cohort/own call is
    96% stable where the margin exceeds 25 points and 34% below 10 — so inside the band it reports
    UNRESOLVED rather than guessing, the same rule ``mixed`` follows when a two-sided read is the
    human's to settle."""
    cfg = get_config()
    reads = cohort_reads(cfg.snapshots_dir, sic_by_ticker(cfg.snapshots_dir))
    if not reads:
        pytest.skip("no committed screen runs")
    for read in reads.values():
        if read.margin is None:
            continue
        if abs(read.margin) < NEAR_TIE:
            assert read.call is CohortCall.UNRESOLVED, (
                f"{read.key} margin {read.margin:.3f} is inside the near-tie band but a call was "
                f"still made ({read.call})")
        else:
            assert read.call in (CohortCall.OWN, CohortCall.COHORT)


def test_too_few_peers_is_not_a_cohort() -> None:
    """ABSENCE IS ABSENCE. A median over five names is an anecdote; the read says NO_COHORT and
    carries no numbers rather than producing a plausible-looking one."""
    cfg = get_config()
    reads = cohort_reads(cfg.snapshots_dir, sic_by_ticker(cfg.snapshots_dir))
    if not reads:
        pytest.skip("no committed screen runs")
    thin = [r for r in reads.values() if r.call is CohortCall.NO_COHORT]
    assert thin, "no NO_COHORT reads at all — the guard is not exercised by the live corpus"
    for read in thin:
        assert read.median is None and read.residual is None and read.margin is None, (
            f"{read.key} reports NO_COHORT but still carries numbers")


def test_the_median_is_taken_over_the_whole_screened_set_not_the_admitted_one() -> None:
    """THE CIRCULARITY GUARD. Candidates are SELECTED for having fallen, so a median over them
    would be deeply negative by construction and the split would measure its own selection. The
    screen log carries every name that reached the gates, pass AND fail."""
    runs = screen_run_files(SNAP)
    if not runs:
        pytest.skip("no committed screen runs")
    screened = relatives_for_run(runs[-1])
    cand_path = SNAP / "candidate_records.jsonl"
    admitted = ({json.loads(x)["candidate_id"] for x in cand_path.read_text().splitlines()
                 if x.strip()} if cand_path.is_file() else set())
    assert len(screened) > 2 * len(admitted), (
        f"the split reads {len(screened)} names against {len(admitted)} admitted — that is not the "
        f"full screened set, and the medians would be defined by the selection under test")


def test_a_partial_sic_map_is_refused_rather_than_silently_wrong() -> None:
    """THE BUG THIS GUARD WAS BUILT FROM, and it was mine. The first wiring passed the map built
    from the 268 ADMITTED names while the medians are taken over ~1,750 SCREENED ones. The ~1,480
    unmapped tickers all resolved to one 'unknown' bucket and silently corrupted every median —
    the output still looked entirely plausible, which is exactly what makes it the fabrication
    class CLAUDE.md forbids."""
    cfg = get_config()
    runs = screen_run_files(cfg.snapshots_dir)
    if not runs:
        pytest.skip("no committed screen runs")
    full = sic_by_ticker(cfg.snapshots_dir)
    partial = dict(list(full.items())[:50])
    with pytest.raises(ValueError, match="SIC map covers"):
        cohort_reads(cfg.snapshots_dir, partial)
    cohort_reads(cfg.snapshots_dir, full)  # the full map must still be accepted


def test_cohorts_under_the_floor_are_dropped_not_imputed() -> None:
    """``medians_for_run`` omits a thin cohort entirely. Imputing one — a global median, a parent
    sector — would put a fabricated number behind a real-looking call."""
    rel = {f"T{i}": -0.5 for i in range(MIN_PEERS - 1)}
    sic = dict.fromkeys(rel, "2000")
    assert medians_for_run(rel, sic) == {}
    rel[f"T{MIN_PEERS}"] = -0.5
    sic[f"T{MIN_PEERS}"] = "2000"
    assert len(medians_for_run(rel, sic)) == 1


# --- the surfaces --------------------------------------------------------------------------------

def test_the_queue_cell_carries_the_split_and_the_header_says_so() -> None:
    """THE CALL SITE, NOT THE HELPER. A correct `vinci.cohort` that the ranker view never renders
    is worth nothing. Asserted on the view source plus the committed artifact it reads."""
    src = (ROOT / "frontend" / "views" / "edge2" / "ranker.js").read_text()
    assert "idioCell(r)" in src, "the ranker still renders the bare idiosyncrasy cell"
    assert "cohort vs own" in src, "the column header does not say the cell carries a split"
    assert "COHORT_LABEL" in src
    norm = (ROOT / "frontend" / "lib" / "snapshots.js").read_text()
    assert "cohort: r.cohort ?? null" in norm, "the normaliser drops the cohort block"


def test_the_committed_queue_actually_carries_reads() -> None:
    """END-TO-END on the living artifact — PHRASING-INDEPENDENT only. Presence, shape and the
    abstention invariant; never a specific median, which moves every screen."""
    lines = (SNAP / "ranked_queue.jsonl").read_text().splitlines()
    rows = [json.loads(x) for x in lines if x.strip()]
    with_cohort = [r for r in rows if r.get("cohort")]
    if not with_cohort:
        pytest.skip("queue predates the split — it is populated by the next rank")
    calls = {r["cohort"]["call"] for r in with_cohort}
    assert calls <= {c.value for c in CohortCall}, f"unknown call in the committed queue: {calls}"
    for r in with_cohort:
        c = r["cohort"]
        if c["call"] == CohortCall.NO_COHORT.value:
            assert c["median"] is None and c["residual"] is None
        else:
            assert c["median"] is not None and c["residual"] is not None
            assert c["peers"] >= MIN_PEERS


def test_the_rank_cli_carries_forward_the_structural_flags() -> None:
    """FOUND WHILE WIRING THIS, AND IT IS A DATA-LOSS BUG. #420 added
    ``carry_forward_assessment`` so a refresh could not un-sink a name an 8-K had capped — but
    wired it into ``run_weekly`` ONLY. A hand-run ``vinci rank`` passed no flags and wiped all of
    them: on the committed queue a plain re-rank restored 58 disqualified names, and SOC — carrying
    a going-concern 8-K, capped at 0.05 and sunk to rank 212 — came back at RANK 7. The manual path
    is the one an operator uses precisely when working the queue by hand."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "_cmd_rank")
    called = {ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)}
    assert "carry_forward_assessment" in called, (
        "`vinci rank` does not carry the prior assessment forward — a hand re-rank silently "
        "un-sinks every structurally disqualified name")
