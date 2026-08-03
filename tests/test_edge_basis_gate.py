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
    BASIS_BY_KEY,
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
    # A NOTE IS NOW REQUIRED for these five — `needs` is enforced (review of #322). Supplying one
    # here is the point: the claim under test is that agreement is ALLOWED, not that it is free.
    line = require_edge_basis(key, ev_gap=gap(ticker), note="2026-11-14 — the stated evidence")
    assert line and "No variant" in line


def test_the_cross_section_option_renders_as_pending_until_a5() -> None:
    """A SLOT ONLY. The machine cannot verify a cross-sectional claim yet, and a slot that read as
    verified would be the false-confirmation defect — worse than not having the option."""
    line = require_edge_basis("variant-vs-cross-section", ev_gap=gap("SMPL"),
                              note="cheapest decile on EV/S with above-median growth")
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


# --- `needs` IS ENFORCED (review of #322) ------------------------------------------------------

def _cli_args(argv: list[str]):
    """Parse through the REAL CLI parser, so these tests exercise the actual flag contract.

    Not a hand-built namespace: the review's finding was that the CLI accepted a command, so the
    test has to go through the CLI's own argument surface or it is checking a different thing."""
    from vinci.cli import build_parser

    return build_parser().parse_args(argv)


BASE = ["log-verdict", "X-1", "--verdict", "BUY", "--twin", "t", "--thesis", "th",
        "--kill", "k", "--horizon-days", "180", "--confidence", "medium"]
NEEDS_A_NOTE = [b.key for b in EDGE_BASES if b.note_required]


@pytest.mark.parametrize("key", NEEDS_A_NOTE)
def test_a_basis_without_its_evidence_is_refused_through_the_cli_surface(key: str) -> None:
    """THE REVIEW'S FINDING, PER BASIS. `--edge-basis watchlist` used to succeed with no note,
    sealing "awaiting a named observation" while naming none — a label asserting that evidence
    exists without recording it, which is the non-actionable edge this gate refuses."""
    args = _cli_args([*BASE, "--edge-basis", key])
    with pytest.raises(EdgeBasisError) as exc:
        require_edge_basis(args.edge_basis, ev_gap=gap("SMPL"), note=args.edge_note)
    assert BASIS_BY_KEY[key].needs in str(exc.value), "the refusal does not say what is needed"


@pytest.mark.parametrize("key", NEEDS_A_NOTE)
@pytest.mark.parametrize("blank", ["   ", "\t", "n/a", "TBD", "-", "?"])
def test_a_placeholder_note_is_refused_like_a_blank_one(key: str, blank: str) -> None:
    """A PLACEHOLDER THAT SATISFIES A CHECK IS WORSE THAN A BLANK — the blank at least fails
    loudly. Same rule the Form-4 role derivation applies to EDGAR's "See Remarks"."""
    args = _cli_args([*BASE, "--edge-basis", key, "--edge-note", blank])
    with pytest.raises(EdgeBasisError):
        require_edge_basis(args.edge_basis, ev_gap=gap("SMPL"), note=args.edge_note)


@pytest.mark.parametrize("key", NEEDS_A_NOTE)
def test_a_real_note_passes(key: str) -> None:
    """NEGATIVE CONTROL — the enforcement must not be satisfiable by refusing everything, which
    would push every verdict into the one option that takes no note."""
    args = _cli_args([*BASE, "--edge-basis", key, "--edge-note", "2026-11-14 FDA decision"])
    line = require_edge_basis(args.edge_basis, ev_gap=gap("SMPL"), note=args.edge_note)
    assert "2026-11-14 FDA decision" in line


def test_the_variant_option_needs_no_note_because_the_gate_checks_its_evidence() -> None:
    """Its `needs` is the persisted EV gap, which the machine already holds. Demanding a note would
    make the human retype a number the row can read — and a retyped number can disagree."""
    line = require_edge_basis("variant-expectation", ev_gap=gap("SMPL"))
    assert "total gap" in line


def test_a_dateless_event_trigger_is_marked_rather_than_refused() -> None:
    """"A named date OR trigger" — only the date half is machine-checkable. Refusing a dateless
    trigger would push the analyst to invent a date, which is the failure the escape options exist
    to prevent, so the absence is made VISIBLE instead of assumed away."""
    dated = require_edge_basis("event-structural", ev_gap=None, note="FDA decision 2026-11-14")
    bare = require_edge_basis("event-structural", ev_gap=None, note="index deletion at rebalance")
    assert "NO DATE given" not in dated
    assert "NO DATE given" in bare


def test_every_basis_declares_whether_its_needs_are_note_backed() -> None:
    """`needs` WAS DEAD METADATA — it read like a contract and enforced nothing. This asserts the
    field that now makes it binding is set deliberately on every option, so a seventh basis added
    later cannot inherit silence by omission."""
    for b in EDGE_BASES:
        assert b.needs, f"{b.key} declares no evidence requirement"
        assert isinstance(b.note_required, bool)
    assert [b.key for b in EDGE_BASES if not b.note_required] == ["variant-expectation"], (
        "only the variant option's evidence is machine-held; any other exemption needs an argument")
