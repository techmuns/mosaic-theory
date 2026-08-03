"""(A4) THE EDGE-BASIS GATE — silence refused, agreement allowed.

THE TWO HALVES ARE ONE DESIGN. A gate that accepted only "we hold a variant expectation" would
manufacture views to satisfy a field, and a fabricated gap is worse than an honest none: it survives
into the ledger, the spread and every retrospective wearing the same shape as a real one. So the
refusal pins and the ACCEPTANCE pins carry equal weight here — a gate nobody can pass honestly is
not a stricter gate, it is a liar factory.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.edge_basis import (
    EDGE_BASES,
    PENDING_MARK,
    EdgeBasisError,
    require_edge_basis,
)

ROOT = Path(__file__).resolve().parents[1]


def gap(ticker: str) -> object:
    doc = json.loads((ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    return (doc.get("mechanical") or {}).get("ev_gap")


COMPUTED = sorted(t.name for t in (ROOT / "data" / "dossiers").iterdir()
                  if (t / "dossier.json").exists()
                  and isinstance(gap(t.name), dict)
                  and gap(t.name).get("status") == "computed")  # type: ignore[union-attr]
NO_GAP = sorted(t.name for t in (ROOT / "data" / "dossiers").iterdir()
                if (t / "dossier.json").exists() and t.name not in COMPUTED)


def test_silence_is_refused_and_the_refusal_lists_the_honest_alternatives() -> None:
    """A BARE REFUSAL WOULD PUSH THE HUMAN TOWARD THE VARIANT OPTION — the one place a fabricated
    answer does real damage. The message must show the five escapes, or the gate makes the problem
    it exists to prevent."""
    with pytest.raises(EdgeBasisError) as exc:
        require_edge_basis(None, ev_gap=gap("SMPL"))
    msg = str(exc.value)
    for b in EDGE_BASES:
        assert b.key in msg, f"the refusal does not offer {b.key}"
    assert "agreement is allowed" in msg
    assert "fabricated variant is worse than an honest none" in msg


def test_an_unknown_basis_is_refused() -> None:
    with pytest.raises(EdgeBasisError, match="unknown edge basis"):
        require_edge_basis("gut-feel", ev_gap=gap("SMPL"))


@pytest.mark.parametrize("ticker", COMPUTED)
def test_a_variant_claim_is_allowed_where_a_total_gap_is_stated(ticker: str) -> None:
    """THE ACCEPTANCE HALF. Option 1 requires the ratios; on a name that has them it must PASS and
    the sealed line must carry the number, so the claim is checkable later rather than asserted."""
    line = require_edge_basis("variant-expectation", ev_gap=gap(ticker))
    assert "Variant expectation stated" in line
    assert "total gap" in line and "x" in line


@pytest.mark.parametrize("ticker", NO_GAP)
def test_a_variant_claim_is_refused_where_no_gap_is_stated(ticker: str) -> None:
    """8 OF 11 NAMES CANNOT STATE A VARIANT TODAY. The refusal must NAME the alternatives rather
    than merely block — otherwise the gate's practical effect is to teach people to type
    `variant-expectation` and invent a number."""
    with pytest.raises(EdgeBasisError) as exc:
        require_edge_basis("variant-expectation", ev_gap=gap(ticker))
    msg = str(exc.value)
    assert "valuation-asymmetry" in msg and "watchlist" in msg
    assert "the normal path, not a failure" in msg


@pytest.mark.parametrize("key", [b.key for b in EDGE_BASES if not b.requires_variant])
@pytest.mark.parametrize("ticker", ["SMPL", "VITL", "FUBO"])
def test_every_no_variant_option_passes_regardless_of_the_gap(key: str, ticker: str) -> None:
    """AGREEMENT IS ALLOWED, on ANY name. These five say "no variant" out loud; conditioning them
    on the gap would make honesty conditional on data the name may never have."""
    line = require_edge_basis(key, ev_gap=gap(ticker))
    assert line and "No variant" in line


def test_the_cross_section_option_renders_as_pending_until_a5() -> None:
    """A SLOT ONLY. The machine cannot verify a cross-sectional claim yet, and a slot that read as
    verified would be the false-confirmation defect — worse than not having the option."""
    line = require_edge_basis("variant-vs-cross-section", ev_gap=gap("SMPL"))
    assert PENDING_MARK in line


def test_a_routed_away_decomposition_still_states_the_total_with_its_coverage() -> None:
    """THE OPERATOR'S RULE: option 1 is satisfied by a stated TOTAL gap; attribution reads
    SUPPRESSED with its coverage where routing sent the decomposition away. Refusing those names
    would deny a variant claim to a name whose gap IS known."""
    routed = {"status": "computed", "form": "two-ratio",
              "ratios": {"ev_gap": 1.42}, "routes": {"EBITDA": {"n": 3}}}
    line = require_edge_basis("variant-expectation", ev_gap=routed)
    assert "total gap 1.42x" in line
    assert "attribution suppressed" in line and "n=3" in line


def test_the_note_is_sealed_beside_the_basis() -> None:
    line = require_edge_basis("event-structural", ev_gap=None, note="FDA decision 2026-11-14")
    assert line.endswith("FDA decision 2026-11-14")


def test_the_gate_runs_before_the_ledger_write() -> None:
    """STRUCTURAL, and load-bearing: the ledger is APPEND-ONLY, so a verdict that reaches it cannot
    be un-logged. The gate must refuse BEFORE `log_verdict`, not validate afterwards."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    body = src[src.index("def _cmd_log_verdict"):]
    body = body[:body.index("def ", 10)]
    # ANCHOR ON THE CALL, not the substring: `def _cmd_log_verdict(` contains `log_verdict(`, so a
    # bare search matched the function's own name at offset ~5 and the comparison was meaningless.
    assert body.index("require_edge_basis") < body.index("= log_verdict("), (
        "the edge-basis gate runs AFTER the ledger write — an append-only row cannot be recalled")


def test_the_gate_reads_the_committed_artifact_not_a_fresh_computation() -> None:
    """The question is what the human could POINT AT when they decided. A recompute could pass a
    verdict the page in front of them did not support."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    body = src[src.index("def _committed_ev_gap"):src.index("def _cmd_log_verdict")]
    assert "dossiers" in body and "dossier.json" in body
    assert "build_ev_gap" not in body and "ev_gap_transform" not in body
