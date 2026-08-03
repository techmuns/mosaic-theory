"""BOTH WRITE PATHS PRODUCE THE SAME `consensus_levels` — the call-site parity residual.

WHAT THIS CLOSES. The corpus question is answered 11/11: every dossier carries levels and the
artifact pass moved 600 keys with 0 changed. What the CPB assembly-vs-refresh diff could NOT reach
is this field specifically — CPB has no CIQ bundle, and no name can exercise both halves, because
the set with bundles and the set with committed dossiers ARE THE SAME ELEVEN (bundles are manual
exports created FOR assembly). So `consensus_levels` parity was structural only: one builder, two
callers, therefore they cannot differ.

Structural is an argument, not a measurement. This measures it — at the call sites rather than at
the builder, because the builder agreeing with itself proves nothing about who calls it and how.

SCOPE, STATED SO A GREEN RUN IS NOT READ AS COVERING THE WHOLE LAYER. Three fields now have two
write paths, and this file treats them differently BECAUSE THEY ARE IN DIFFERENT STATES:

  * `consensus_levels`  — both paths produce it; VALUES COMPARED (the original claim).
  * `ev_gap`            — **ASSEMBLY DOES NOT PRODUCE IT AT ALL.** Pinned as the asymmetry it is,
                          with its consequence: a re-assembly DROPS the field.
  * `insider_activity`  — both paths produce it, but refresh's path FETCHES FROM EDGAR, so a
                          value comparison here would be a network test. Named, not tested.

Extending this file rather than leaving it at one field is the operator's call (2026-08-03): a
parity test covering one field, read as covering the layer, is worse than one that says which.
"""
from __future__ import annotations

import pytest

from vinci.config import get_config
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.mechanical import _consensus
from vinci.dossier.refresh import consensus_transform


def _bundle(ticker: str) -> CiqBundle:
    """The name's CIQ bundle, or SKIP when the licensed export is not on this machine.

    CONDITIONED ON THE FILE LIST, NOT ON AN EXCEPTION — the FOURTH instance of the
    guard-that-cannot-fire pattern (item 1's completeness gate, the absence-reason guard, #310's
    no-op `getattr`, and `test_consensus_rows`'s own skip in #318). With `data/manual/ciq/` absent,
    `files()` returns `[]` WITHOUT raising and `CiqBundle.from_files` accepts an empty list, so the
    except-handler never ran; this file passed in CI only because a SECOND skip caught it further
    down. Working by accident is not the same as working.
    """
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    try:
        return CiqBundle.from_files(ticker, files)
    except Exception as exc:                              # pragma: no cover - env-dependent
        pytest.skip(f"{ticker}: CIQ bundle unreadable ({type(exc).__name__})")


@pytest.mark.parametrize("ticker", ["SMPL", "EPAM", "VITL", "MVST", "CNXC"])
def test_assembly_and_refresh_write_identical_levels(ticker: str) -> None:
    """THE TWO CALL SITES, COMPARED DIRECTLY.

    Assembly builds a typed `ConsensusContext`; refresh injects plain dicts into a `mech` mapping.
    Different shapes on the way in, so the comparison normalises to the value each PERSISTS — a
    parity test that compared representations rather than values would pass on a real divergence
    or fail on a cosmetic one.

    Names chosen for the states they carry: SMPL (ragged pair 9/11), EPAM (Revenue 5fy vs EBITDA
    3fy — different spans per metric), VITL (median 3.3 on a 0.3-9.0 range), MVST (2/2 and 1/1,
    the coverage floor), CNXC (exactly two forward years).
    """
    bundle = _bundle(ticker)

    # PATH 1 — assembly.
    assembled = _consensus(bundle).consensus_levels
    # PATH 2 — the refresh transform, into an empty consensus_context.
    mech = consensus_transform(ticker)({"consensus_context": {"consensus_levels": None}})
    refreshed = mech["consensus_context"]["consensus_levels"]

    assert (assembled is None) == (refreshed is None), (
        f"{ticker}: one path produced levels and the other did not — "
        f"assembly={assembled is not None}, refresh={refreshed is not None}")
    if assembled is None:
        pytest.skip(f"{ticker}: no consensus levels from either path")

    fields = ("fy", "median", "high", "low", "std_dev", "estimates")

    def _norm(levels: object) -> dict[str, list[tuple[object, ...]]]:
        out: dict[str, list[tuple[object, ...]]] = {}
        for metric, cells in dict(levels).items():        # type: ignore[call-overload]
            rows = []
            for c in cells:
                d = c if isinstance(c, dict) else {k: getattr(c, k) for k in fields}
                rows.append(tuple(d[k] for k in fields))
            out[metric] = rows
        return out

    a, r = _norm(assembled), _norm(refreshed)
    assert set(a) == set(r), f"{ticker}: metric sets differ — assembly {set(a)}, refresh {set(r)}"
    for metric in a:
        assert a[metric] == r[metric], (
            f"{ticker} {metric}: the two write paths disagree\n"
            f"  assembly={a[metric][:3]}\n  refresh ={r[metric][:3]}")


# --- ev_gap: the two paths are NOT at parity, and that is the finding ---------------------------

def test_assembly_does_not_produce_ev_gap_so_a_re_assembly_drops_it() -> None:
    """THE ASYMMETRY, PINNED WITH ITS CONSEQUENCE.

    `ev_gap` is written ONLY by `refresh.ev_gap_transform`. `MechanicalLayer.ev_gap` defaults to
    None and nothing in the assembly path sets it — so **a fresh assembly writes `ev_gap: null`**
    and the page reverts to "MISSING REFRESH … nothing has been measured".

    THIS IS LIVE AND IT IS NEXT IN THE QUEUE: SMPL's re-assembly is scheduled, SMPL is one of only
    three names carrying a decomposition, and re-assembling it today would silently drop the EV gap
    the last two builds existed to produce. The render would be HONEST about it — that is what the
    three-state design bought — but the number would be gone.

    PINNED AS THE CURRENT STATE, NOT AS DESIRABLE. When assembly learns to produce `ev_gap`, this
    test REDDENS and forces a real value-parity assertion to be written in its place, which is
    exactly the argument that should happen at that moment rather than after.
    """
    import inspect

    from vinci.dossier import assemble
    from vinci.dossier import mechanical as dm
    from vinci.dossier.schemas import MechanicalLayer

    assert MechanicalLayer.model_fields["ev_gap"].default is None
    for mod in (assemble, dm):
        assert "ev_gap" not in inspect.getsource(mod), (
            f"{mod.__name__} now references ev_gap — assembly may have learned to produce it. If "
            "so, DELETE this test and assert value parity against ev_gap_transform instead; the "
            "two paths must not be allowed to diverge silently the way consensus_levels could not.")


def test_the_insider_line_has_two_write_paths_and_this_file_does_not_compare_them() -> None:
    """NAMED, NOT TESTED — so the omission is deliberate rather than discovered later.

    Both `assemble_mechanical` and `refresh.insider_transform` produce `catalyst_path.
    insider_activity`, but refresh's path fetches ~110 filings from EDGAR. A value comparison here
    would turn an offline parity test into a network one; the honest move is to say so.
    """
    import inspect

    from vinci.dossier import mechanical as dm
    from vinci.dossier import refresh as dr

    assert "_insider_activity(" in inspect.getsource(dm), "assembly no longer writes the line"
    assert "_insider_activity(" in inspect.getsource(dr), "refresh no longer writes the line"
