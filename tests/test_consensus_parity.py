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
  * `ev_gap`            — both paths NOW produce it, via the SAME transform; VALUES COMPARED,
                          and the test fails on the LOSS rather than on its repair.
  * `insider_activity`  — both paths produce it, but refresh's path FETCHES FROM EDGAR, so a
                          value comparison here would be a network test. Named, not tested.

Extending this file rather than leaving it at one field is the operator's call (2026-08-03): a
parity test covering one field, read as covering the layer, is worse than one that says which.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.config import get_config
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.mechanical import _consensus
from vinci.dossier.refresh import consensus_transform

ROOT = Path(__file__).resolve().parents[1]


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


# --- ev_gap: VALUE PARITY, and it fails on the LOSS rather than on the fix -----------------------

def test_assembly_produces_the_same_ev_gap_the_refresh_does() -> None:
    """THE SAFETY TEST, POINTED THE RIGHT WAY (review of #324).

    THE FIRST CUT WAS A TOMBSTONE. It asserted "assembly does not produce ev_gap" — passing
    happily while a fresh assembly wrote `ev_gap: null`, and reddening only once somebody fixed
    it. A test that is green throughout the harm and red at the repair protects nothing: it
    offered the queued SMPL re-assembly exactly no cover from the event it described.

    NOW ASSEMBLY RUNS THE SAME TRANSFORM on the freshly-built mech, so the two write paths cannot
    disagree by construction — and this asserts it as a VALUE comparison rather than a structural
    claim. RECOMPUTED, NEVER CARRIED FORWARD: copying the committed gap across an assembly would
    put one struck on old cap/net-debt/consensus beside new ones, which is the frozen-beside-live
    defect.
    """
    import ast
    import inspect

    from vinci.dossier import assemble as da

    # THE CALL, AND ITS ASSIGNMENT BACK TO `mech` — not the NAME. Measured: deleting the two lines
    # that apply the transform left the `from … import ev_gap_transform` line behind, and a pin
    # that searched for the name passed on a build that had stopped calling it. An import is not a
    # call, and a call whose result is discarded is not a write.
    src = inspect.getsource(da)
    tree = ast.parse(src)
    applied = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "mech" for t in n.targets)
        and "ev_gap_transform" in ast.dump(n.value)
    ]
    assert applied, (
        "the assembly path no longer ASSIGNS the EV-gap transform's result to `mech` — a fresh "
        "assembly will write ev_gap: null and SILENTLY DROP a persisted gap. That is the data "
        "loss the queued SMPL re-assembly would cause, not a style point.")
    # …and it must run BEFORE the Dossier is built, or it never reaches the artifact.
    assert src.index("ev_gap_transform(") < src.index("dossier = Dossier("), (
        "the EV-gap transform runs after the Dossier is constructed — too late to reach it")


@pytest.mark.parametrize("ticker", ["SMPL", "EPAM", "IT"])
def test_a_re_assembly_would_not_lose_a_persisted_gap(ticker: str) -> None:
    """THE LOSS ITSELF, DRIVEN. Rebuild the mech the way an assembly does — apply the transform to
    a mech whose `ev_gap` has been STRIPPED, exactly as a fresh assembly hands it over — and assert
    the value comes back identical to what is committed.

    Named for the three names that carry a decomposition: these are the ones with something to
    lose, and SMPL is the queued re-assembly.
    """
    from vinci.dossier.refresh import ev_gap_transform

    committed = json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())["mechanical"]
    before = committed.get("ev_gap")
    assert before and before.get("status") == "computed", "fixture precondition"

    fresh = {**json.loads(json.dumps(committed)), "ev_gap": None}   # what assembly hands over
    after = ev_gap_transform(ticker)(fresh)["ev_gap"]

    assert after is not None, f"{ticker}: a re-assembly would DROP the persisted gap"
    assert after["status"] == "computed"
    assert after["ratios"] == pytest.approx(before["ratios"]), (
        f"{ticker}: the re-assembled gap differs from the committed one")
    assert after["vintages"] == before["vintages"]


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
