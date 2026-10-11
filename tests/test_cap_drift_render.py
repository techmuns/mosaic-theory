"""The cap and the price sit two fields apart, and the page now says how far apart they are.

WHY (UBER, from an analyst's reading of the committed page). The snapshot printed
`CMP $78.54 · cap $139.3B (2026-08-06)` and nothing else. Those two cannot both be true: the cap is
struck on a 2026-08-05 close of $68.18, and the stock ran 15% in the four sessions after it. Every
EV multiple on the page is built on the older cap — NTM EV/EBITDA reads 11.89x where the current
price gives ~13.6x — so the analyst had to fetch the share count and recompute to find it.

THE NUMBER ALREADY EXISTED. `reconcile_cap` runs on every build and produces exactly this
(`implied_price=68.18, gap=-13.19%`), and `check_freshness` deliberately does not fail on ordinary
drift — failing would stop 8 of the 14 committed names, "a freeze wearing a guard's name". Its own
docstring hands the disclosure to rendering instead, and rendering shipped half of it: clause (e)
gave the cap its VINTAGE and never its MAGNITUDE. A date does not tell a reader it is 13%.

KEYED ON THE GAP, NOT THE DATE, and that is the load-bearing choice: 8 of 14 names carry no
`market_cap_as_of` at all, so a vintage-keyed caveat is blank exactly where the drift is worst
(AORT -18.4%, VITL -19.0%, MVST +17.6% — all undated). The gap is computable whenever the three
inputs are present.

THESE PINS READ THE COMMITTED ARTIFACTS, so they hold what a human actually receives.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier import render as render_mod
from vinci.dossier.schemas import Dossier

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSSIERS = ROOT / "data" / "dossiers"


def _dossier(ticker: str) -> Dossier:
    p = DOSSIERS / ticker / "dossier.json"
    if not p.is_file():
        pytest.skip(f"no committed dossier for {ticker}")
    return Dossier.model_validate_json(p.read_text())


def _snapshot(ticker: str) -> str:
    d = _dossier(ticker)
    lines = render_mod._brief_snapshot(d.exchange, d.mechanical.stock_info)
    assert lines, f"{ticker}: no snapshot line rendered"
    return lines[0]


def test_a_drifting_name_states_its_drift_on_the_page() -> None:
    """THE REGRESSION, on every drifting committed artifact. UBER's page carried the cap and the
    price side by side and never said they disagree.

    MEASURED, NOT NAMED (2026-10-11). This pinned UBER's own figures ("implies $68.18/sh", cap
    $139.3B); the 2026-10-11 CIQ re-export struck UBER's cap on the same close as its price, so UBER
    now RECONCILES and correctly carries no mark — the pin broke on the page becoming right, which
    is the sibling test's lesson (2026-08-13) arriving here. What this owns is that EVERY page whose
    cap and price disagree SAYS so, with the implied price and the magnitude, beside the cap; which
    names drift is data (15 of 26 on 2026-10-11, NFLX -2.3% to MVST +57.1%)."""
    import re

    from vinci.dossier.freshness import RECONCILE_TOLERANCE, reconcile_cap
    from vinci.dossier.schemas import SourceStatus

    checked = 0
    for folder in sorted(DOSSIERS.iterdir()):
        if not (folder / "dossier.json").is_file():
            continue
        si = _dossier(folder.name).mechanical.stock_info
        if si is None or not all(f.status is SourceStatus.PRESENT
                   for f in (si.market_cap, si.shares_out, si.price)):
            continue
        recon = reconcile_cap(cap_musd=si.market_cap.value, shares=si.shares_out.value,
                              spot=si.price.value)
        if (recon is None or recon.gap is None or abs(recon.gap) <= RECONCILE_TOLERANCE
                or recon.corporate_action):
            continue                       # reconciling names and share-basis breaks are elsewhere
        checked += 1
        line = _snapshot(folder.name)
        implied = f"implies ${recon.implied_price:,.2f}/sh"
        assert implied in line, (
            f"{folder.name}: the cap's implied price is not on the page: {line!r}")
        assert re.search(r"\([+-]?\d+\.\d%\)", line), (
            f"{folder.name}: no drift magnitude on the page — a vintage alone does not say how far "
            f"apart they are: {line!r}")
        # the mark sits WITH the cap, not appended to the line, so the pairing is unambiguous
        assert line.index("cap ") < line.index(implied) < line.index("52-wk"), folder.name
    assert checked, "no committed name drifts — this pin checked nothing"


def test_a_reconciling_name_says_nothing() -> None:
    """The mark must mean something wherever it appears. A name whose cap and price agree carries
    no caveat at all — otherwise this becomes furniture and stops being read.

    MEASURED, NOT LISTED (2026-08-13). This named NFLX/BRBR/V as the reconciling three; the
    2026-08-12 re-assembly moved BRBR into DRIFT (+6.5%), so a roster written when the fleet looked
    one way failed on a page that had simply changed. Whether a given name reconciles is data, and
    the rule — reconciling names carry no mark — is what this owns."""
    from vinci.dossier.freshness import RECONCILE_TOLERANCE, reconcile_cap
    from vinci.dossier.schemas import SourceStatus

    checked = 0
    for folder in sorted(DOSSIERS.iterdir()):
        if not (folder / "dossier.json").is_file():
            continue
        si = _dossier(folder.name).mechanical.stock_info
        if not all(f.status is SourceStatus.PRESENT
                   for f in (si.market_cap, si.shares_out, si.price)):
            continue
        recon = reconcile_cap(cap_musd=si.market_cap.value, shares=si.shares_out.value,
                              spot=si.price.value)
        if recon.gap is None or abs(recon.gap) > RECONCILE_TOLERANCE:
            continue                       # drifting names are the other test's subject
        checked += 1
        line = _snapshot(folder.name)
        assert "implies" not in line, f"{folder.name} reconciles; it must not carry a drift mark"
        assert "⚠" not in line.split("· 52-wk")[0].split("cap ")[-1], (
            f"{folder.name}: a clean cap carries a warning mark")
    assert checked, "no committed name reconciles — this pin checked nothing"


def test_a_share_basis_mismatch_is_not_worded_as_drift() -> None:
    """A cap and count on different share bases is a CORPORATE ACTION, not a price that moved.
    Calling it drift would invite the reader to mentally re-date the cap and carry on — the wrong
    remedy for a page where no per-share figure can be trusted.

    CONSTRUCTED, AND THEREFORE UNCONDITIONAL (review finding, #441). This read FUBO, whose cap and
    count sat 11.13x apart; the 2026-08-12 re-assembly FIXED that, so a first rewrite derived the
    population and SKIPPED when the fleet was clean — which is now always. A skipping pin leaves the
    renderer branch that prints this warning unexercised, and the constructed pins in
    `test_freshness.py` cover `reconcile_cap` (the COMPUTATION) rather than the human-facing label.

    So the mismatch is MANUFACTURED here: a real committed record whose share count sits a whole
    number away from its cap, which is exactly what a split straddling the two panels does. Nothing
    has to stay broken in the fleet for the warning to keep being tested.
    """
    from vinci.dossier.freshness import reconcile_cap

    host = next((f.name for f in sorted(DOSSIERS.iterdir())
                 if (f / "dossier.json").is_file()), None)
    assert host is not None, "no committed dossier to build a mismatch from"
    d = _dossier(host)
    si = d.mechanical.stock_info
    assert si.shares_out.value and si.market_cap.value and si.price.value, (
        f"{host}: needs cap, shares and price present to construct a basis mismatch")

    # SOLVED, NOT SCALED. `reconcile_cap` keys on the ratio sitting ON a whole number, so simply
    # multiplying an existing count by 11 inherits whatever drift the host already carries (AORT
    # landed at 11.485 and missed the tolerance). Deriving the count that makes spot/implied exactly
    # 11 — shares = cap x 11 / spot — is what a pre-split count against a post-split cap IS.
    split_factor = 11
    split = si.model_copy(update={
        "shares_out": si.shares_out.model_copy(update={
            "value": si.market_cap.value * 1e6 * split_factor / si.price.value})})
    recon = reconcile_cap(cap_musd=split.market_cap.value, shares=split.shares_out.value,
                          spot=split.price.value)
    assert recon is not None and recon.corporate_action, (
        "the constructed record is not a basis break — the fixture no longer exercises the branch")

    line = render_mod._brief_snapshot(d.exchange, split)[0]
    assert "SHARE-BASIS MISMATCH" in line, (
        f"a whole-number basis break rendered without the mismatch label: {line}")
    assert "/sh" in line, "a mismatch must state the implied per-share figure"
    cap_seg = line.split("cap ")[-1].split("· 52-wk")[0]
    assert "%" not in cap_seg, (
        f"a share-basis mismatch must not print a drift percentage — the ratio is the diagnostic, "
        f"and a percentage invites the reader to re-date the cap and carry on: {cap_seg}")

    # …and the ORDINARY case still reads as drift, so the two states stay distinguishable.
    drift = si.model_copy(update={
        "price": si.price.model_copy(update={"value": si.price.value * 1.25})})
    drift_line = render_mod._brief_snapshot(d.exchange, drift)[0]
    if "implies" in drift_line:
        assert "SHARE-BASIS MISMATCH" not in drift_line, (
            "ordinary price drift is being labelled a corporate action")
        assert "%" in drift_line.split("cap ")[-1], "ordinary drift must state its percentage"


def test_the_undated_names_are_exactly_why_the_gap_keys_this() -> None:
    """THE DESIGN DECISION, pinned. These names carry NO cap vintage, so a date-keyed caveat would
    render blank on the three largest drifts in the fleet. Keying on the computed gap reaches them.
    If a future change re-keys this on the vintage, this pin is what should stop it."""
    # DERIVED (2026-08-13): the three were AORT/VITL/MVST when this was written, and the
    # 2026-08-12 re-assembly gave AORT a cap vintage (2026-07-30). The DESIGN CLAIM is not about
    # those tickers — it is that names WITHOUT a vintage still get their drift disclosed, which a
    # date-keyed caveat could not do. So the population is computed and the claim asserted over it.
    undated = [f.name for f in sorted(DOSSIERS.iterdir())
               if (f / "dossier.json").is_file()
               and _dossier(f.name).mechanical.stock_info.market_cap_as_of is None]
    if not undated:
        pytest.skip("every committed name now carries a cap vintage — the premise has cleared")
    for ticker in undated:
        line = _snapshot(ticker)
        if "implies" not in line:
            continue                        # undated AND reconciling — nothing owed
        assert "%" in line.split("cap ")[-1], (
            f"{ticker} has NO cap vintage and drifts, yet the page states no gap — a date-keyed "
            f"caveat would render blank here, which is exactly why this keys on the computed gap")


def test_every_committed_name_either_reconciles_or_says_why() -> None:
    """THE FLEET PIN. Measured rather than listed: whatever the reconciliation computes, the page
    must state it. A name silently drifting past the tolerance is the defect this closes."""
    from vinci.dossier.freshness import RECONCILE_TOLERANCE, reconcile_cap
    from vinci.dossier.schemas import SourceStatus

    silent: list[tuple[str, float]] = []
    for p in sorted(DOSSIERS.iterdir()):
        if not (p / "dossier.json").is_file():
            continue
        si = _dossier(p.name).mechanical.stock_info
        if not all(f.status is SourceStatus.PRESENT
                   for f in (si.market_cap, si.shares_out, si.price)):
            continue
        recon = reconcile_cap(cap_musd=si.market_cap.value, shares=si.shares_out.value,
                              spot=si.price.value)
        if recon is None or abs(recon.gap) <= RECONCILE_TOLERANCE:
            continue
        if "implies" not in _snapshot(p.name):
            silent.append((p.name, recon.gap))
    assert not silent, f"these drift past the tolerance and the page is silent on it: {silent}"


def test_the_committed_json_still_carries_the_inputs_to_reproduce_it() -> None:
    """The mark is DERIVED at render, not stored — so the JSON must keep the three inputs it is
    derived from, or the machine-complete tier stops being able to reproduce the page."""
    si = json.loads((DOSSIERS / "UBER" / "dossier.json").read_text())["mechanical"]["stock_info"]
    for field in ("market_cap", "shares_out", "price"):
        assert si[field]["value"] is not None, f"{field} must remain in the JSON"
