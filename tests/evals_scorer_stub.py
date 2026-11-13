"""A stand-in for RG-D12's WHOLE check, for tests that pin the harness's OTHER rules.

Since #1030's review round 1 (2026-11-12), the library's `run_compare` and `score_run` run
`compare.refuse_unless_registered_scorer` themselves: the registered fingerprint, BASE's
production files at `base_ref`, and the harness at a `scorer_ref` on origin/main. A test that
registers under a placeholder ref ("A", "B") or an old commit holds none of those, so before
round 1 it passed only the fingerprint comparison the library made then. This stands that
comparison back in, and nothing more; RG-D12's own pins live in `tests/test_evals_order8.py` and
`tests/test_evals_order8_round1.py`, which do NOT use it.
"""
from __future__ import annotations

from typing import Any


def fingerprint_only(reg: Any, **_: Any) -> None:
    """The fingerprint comparison the library made before round 1, and nothing more."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    if (here := cm.scorer_fingerprint()) != reg.scorer:
        raise ReplayError(f"the scorer here ({here[:12]}) is not the registered scorer "
                          f"({reg.scorer[:12]}): score from the registered code")
