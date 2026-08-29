"""The anchoring falsifier, measured in the scoring report (brief Item 3, 2026-08-28).

CLAUDE.md records the pivot's accepted risk WITH its falsifier — override rate collapsing toward
~0, or the human spread tracking the machine spread within noise — and until this block nothing
computed either quantity: the recorded-criterion-nobody-measures class. Pinned ON THE RENDERED
MARKDOWN (the artifact both default paths emit — ``vinci score`` and ``run_monthly``'s committed
``scoring_report.md``), never on the helper alone: a helper-level pin stays green when the render
line is deleted (pin-the-artifact-not-the-helper).

The negative pins are the load-bearing ones: an empty denominator must render as *insufficient
rows*, never as a fabricated 0.0 — a 0.0 here would read as exactly the collapse-toward-~0 the
falsifier watches for (the false-reconcile class: a computed number standing in for missing data).
"""

from __future__ import annotations

from vinci.schemas.ledger import Disposition, Verdict
from vinci.scoring.metrics import VerdictScore, aggregate, override_rate


def _vs(
    ticker: str,
    verdict: Verdict,
    name_ret: float,
    *,
    machine: Verdict | None = None,
    disposition: Disposition | None = None,
) -> VerdictScore:
    return VerdictScore(
        entry_id=f"V-{ticker}", ticker=ticker, verdict=verdict, resolved=True,
        name_return=name_ret, bench_return=0.0,
        machine_proposal=machine, disposition=disposition,
    )


def test_override_rate_refuses_a_fabricated_zero() -> None:
    """No proposal-bearing rows → None, NEVER 0.0 — 0.0 is the reading the falsifier watches for."""
    assert override_rate(0, 0) is None
    assert override_rate(3, 1) == 1 / 4
    assert override_rate(0, 2) == 1.0


def test_block_renders_rate_and_delta_on_the_markdown() -> None:
    """POSITIVE PIN — a known confirmed/overridden mix renders the expected rate and delta.

    human spread = mean(.20,.10) − mean(−.30,−.10) = +35.0%; machine buckets the same rows by the
    SEALED proposal: mean(.20) − mean(.10,−.30) = +30.0% → delta +5.0%. rate = 1/(2+1) = 33%.
    """
    scores = [
        _vs("AAA", Verdict.BUY, 0.20, machine=Verdict.BUY, disposition=Disposition.CONFIRMED),
        _vs("BBB", Verdict.BUY, 0.10, machine=Verdict.AVOID_TERMINAL,
            disposition=Disposition.OVERRIDDEN),
        _vs("CCC", Verdict.AVOID_TERMINAL, -0.30, machine=Verdict.AVOID_TERMINAL,
            disposition=Disposition.CONFIRMED),
        _vs("DDD", Verdict.AVOID_TERMINAL, -0.10, disposition=Disposition.NO_PROPOSAL),
    ]
    md = aggregate(scores, cost_bps=25.0, n_pending=0).to_markdown()
    assert "### The anchoring falsifier, measured (never adjudicated)" in md
    assert "Override rate: 1/3 = 33%" in md
    assert ("Human−machine spread delta (SCREEN-ORIGIN rows only): +5.0% "
            "(human +35.0% − machine +30.0%") in md
    # The falsifier's own wording travels with the numbers — the reader concludes, not the block.
    assert "revisit verdict placement" in md
    # SCOPE PIN: the two quantities sit on DIFFERENT populations (the rate counts dispositions in
    # every book; the delta subtracts two screen-origin curves), so each must NAME its own — else
    # a reader takes them for one sample. This is the incomparability the module refuses one level
    # up, at the surface where it would actually mislead.
    assert "ALL resolved proposal-bearing rows (every book)" in md
    assert "delta (SCREEN-ORIGIN rows only)" in md


def test_block_prints_insufficient_not_zero_when_no_proposal_rows() -> None:
    """NEGATIVE PIN — resolved rows exist but none carries a proposal: rate must refuse."""
    scores = [
        _vs("AAA", Verdict.BUY, 0.20, disposition=Disposition.NO_PROPOSAL),
        _vs("CCC", Verdict.AVOID_TERMINAL, -0.30, disposition=Disposition.NO_PROPOSAL),
    ]
    md = aggregate(scores, cost_bps=25.0, n_pending=0).to_markdown()
    assert "Override rate: insufficient rows (n=0 proposal-bearing resolved)" in md
    assert "Override rate: 0/0" not in md
    # No machine leg resolved either → the delta refuses too, naming WHICH curve is missing.
    assert ("Human−machine spread delta (SCREEN-ORIGIN rows only): UNDEFINED — no "
            "two-leg resolved read yet for the machine curve") in md


def test_delta_refuses_and_names_both_curves_when_nothing_resolved_two_legged() -> None:
    """NEGATIVE PIN — one BUY only: neither curve has two legs, and the line says so for both."""
    scores = [
        _vs("AAA", Verdict.BUY, 0.20, machine=Verdict.BUY, disposition=Disposition.CONFIRMED),
    ]
    md = aggregate(scores, cost_bps=25.0, n_pending=0).to_markdown()
    # The rate half is computable (1 confirmed, 0 overridden) even while the delta half refuses —
    # the two quantities fail independently, each with its own honest reading.
    assert "Override rate: 0/1 = 0%" in md
    assert ("Human−machine spread delta (SCREEN-ORIGIN rows only): UNDEFINED — no two-leg "
            "resolved read yet for the human and machine curves") in md
