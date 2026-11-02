"""`ev_bridge` — CIQ's current TEV claims, the bridge an enterprise recipe (R4) subtracts from TEV.

CIQ's comps sheet builds TEV as market cap + Net Debt + preferred + minority interest. `claims` is
that less market cap, every line read at ONE dated balance-sheet column, the latest. CIQ's 'Net
Debt' nets long-term marketable securities when that column discloses them and nothing when it does
not.
On 2026-10-09 the claims equal CIQ's own current TEV less market cap on 26 of 26 names.

THE FIRST CUT WAS WRONG ON UBER (2026-10-08): it carried Q1's long-term securities ($3,873M) into
a Q2 press-release column, after Historical Capitalization's "last reported" footnote, and read
$6,550M against the $10,423M CIQ's current TEV — and the multiple R4 anchors on — uses. Its 26/26
check had validated the formula at filing dates, never the balance sheet the multiple uses. The pins
below compare against CIQ's CURRENT figure.

The exit default follows the operator's rule (2026-10-08): a same-basis, current consensus net-debt
line — matching the balance sheet in each of its last three reported years — with preferred and
minority held; else today's claims held. Never current − FCF, never manual.

The pins run on frozen DERIVED values (`tests/fixtures/ev_bridge_cases.json`), so they gate in CI.
The local pins re-read the exports.
"""
from __future__ import annotations

import inspect
import json
import pathlib
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.schemas import Dossier, EvBridge, dossier_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES: dict[str, dict[str, Any]] = json.loads(
    (ROOT / "tests" / "fixtures" / "ev_bridge_cases.json").read_text())["cases"]


def _bridge(ticker: str) -> EvBridge:
    return EvBridge.model_validate(CASES[ticker]["bridge"])


def _line(b: EvBridge, label: str) -> float | None:
    return next(ln.value for ln in b.lines if ln.label == label)


# --- the build-up -----------------------------------------------------------------------------

@pytest.mark.parametrize("ticker", sorted(CASES))
def test_claims_are_ciqs_current_tev_less_market_cap(ticker: str) -> None:
    """The quantity the multiple embeds: CIQ's own current TEV − market cap (comps export)."""
    b = _bridge(ticker)
    assert b.ciq_tev_claims is not None
    assert b.claims == pytest.approx(b.ciq_tev_claims, abs=0.5)
    assert b.note is None or "DISAGREES" not in b.note


@pytest.mark.parametrize("ticker", sorted(CASES))
def test_claims_are_the_signed_sum_of_the_lines(ticker: str) -> None:
    b = _bridge(ticker)
    # a claim CIQ does not state is unread WITH its reason, never a 0.0 (audit A-D2, 2026-10-30)
    assert all(ln.unread for ln in b.lines if ln.value is None)
    assert b.claims == pytest.approx(
        sum(ln.sign * ln.value for ln in b.lines if ln.value is not None), abs=1e-3)
    debt, cash = _line(b, "Total Debt"), _line(b, "Total Cash & ST Investments")
    netted = _line(b, cs._NETTED_LABEL)
    assert debt is not None and cash is not None and netted is not None
    assert b.net_debt == pytest.approx(debt - cash - netted, abs=1e-3)
    assert {ln.label for ln in b.lines} == {
        "Total Debt", "Total Cash & ST Investments", cs._NETTED_LABEL, "Total Pref. Equity",
        "Total Minority Interest"}
    assert len({ln.as_of for ln in b.lines}) == 1, "every line at ONE balance-sheet column"


def test_amzn_s_claims_are_its_net_debt() -> None:
    b = _bridge("AMZN")
    assert b.claims == b.net_debt == pytest.approx(128647.0)


def test_uber_carries_no_securities_its_latest_column_does_not_disclose() -> None:
    """THE REGRESSION. UBER's latest balance sheet is a Q2 press release that discloses no
    long-term securities, so CIQ nets none: claims = Net Debt $9,340M + minority $1,083M =
    $10,423M. The first cut subtracted Q1's $3,873M and read $6,550M."""
    b = _bridge("UBER")
    assert _line(b, cs._NETTED_LABEL) == 0.0
    assert b.net_debt == pytest.approx(9340.0)
    assert _line(b, "Total Minority Interest") == pytest.approx(1083.0)
    assert b.claims == pytest.approx(10423.0) and b.ciq_tev_claims == pytest.approx(10423.0)


def test_lly_s_net_debt_nets_the_securities_its_column_discloses() -> None:
    b = _bridge("LLY")
    assert _line(b, cs._NETTED_LABEL) == pytest.approx(796.0)
    assert b.claims == b.net_debt == pytest.approx(45162.0)


def test_googl_carries_its_preferred() -> None:
    b = _bridge("GOOGL")
    assert _line(b, "Total Pref. Equity") == pytest.approx(18023.0)
    assert b.claims == pytest.approx(b.net_debt + 18023.0)


# --- the exit default, per the operator's rule --------------------------------------------------

@pytest.mark.parametrize("ticker", sorted(CASES))
def test_the_exit_default_follows_the_rule(ticker: str) -> None:
    b = _bridge(ticker)
    c = b.consensus
    used = bool(c and c.same_basis and c.current and c.forward)
    assert b.exit_claims, "no exit default — R4 would need manual input, which the rule forbids"
    for e in b.exit_claims:
        if used:
            assert c is not None and e.method == "consensus"
            assert e.value == pytest.approx(c.forward[e.fiscal_year] + b.claims - b.net_debt,
                                            abs=1e-3)
        else:
            assert e.method == "held" and e.value == pytest.approx(b.claims)


def test_one_matching_year_is_a_coincidence_not_a_basis() -> None:
    """NKE's line matched in FY2026 (0.09%) after missing by 25–28% in FY2024–25. The first cut
    tested the last year only, passed it, and set NKE's exit from broker forecasts."""
    c = _bridge("NKE").consensus
    assert c is not None and len(c.years) == cs.CONSENSUS_SAME_BASIS_YEARS
    assert c.years[0].gap_ratio is not None and c.years[0].gap_ratio < cs.CONSENSUS_SAME_BASIS_MAX
    assert any(y.gap_ratio is not None and y.gap_ratio > 0.2 for y in c.years[1:])
    assert not c.same_basis
    assert {e.method for e in _bridge("NKE").exit_claims} == {"held"}


def test_a_line_checkable_on_one_year_is_not_a_basis() -> None:
    b = _bridge("MVST")
    assert b.consensus is not None and not b.consensus.same_basis
    assert {e.method for e in b.exit_claims} == {"held"}
    assert b.note is not None and "checked on only 1 of its last 3" in b.note


def test_a_stale_line_is_not_used_even_with_forward_values() -> None:
    """CONSTRUCTED from MVST's REAL check, marked same-basis and given a forward value: a line whose
    newest reported year is not the latest completed one is not a forecast."""
    b = _bridge("MVST")
    assert b.consensus is not None and not b.consensus.current
    check = b.consensus.model_copy(update={"same_basis": True, "forward": {"FY 2027": 50.0}})
    got, note = cs.exit_claims_for(b.claims, b.net_debt, check, ["FY 2027"])
    assert [e.method for e in got] == ["held"]
    assert note is not None and "stopped before the latest completed year" in note


def test_a_consensus_exit_keeps_preferred_and_minority() -> None:
    """CONSTRUCTED from UBER's REAL bridge — no committed line qualifies today. Marked usable, the
    line's forward net debt must carry UBER's $1,083M of minority interest into every exit year."""
    b = _bridge("UBER")
    assert b.consensus is not None and b.consensus.forward
    usable = b.consensus.model_copy(update={"same_basis": True, "current": True})
    fys = list(usable.forward)
    got, note = cs.exit_claims_for(b.claims, b.net_debt, usable, fys)
    assert note is None and [e.method for e in got] == ["consensus"] * len(fys)
    for e in got:
        assert e.value == pytest.approx(usable.forward[e.fiscal_year] + 1083.0, abs=1e-3)


def test_a_broker_basis_line_is_not_used() -> None:
    """AMZN's line reports −$57,381M for FY2025 against +$55,518M on CIQ's balance sheet."""
    c = _bridge("AMZN").consensus
    assert c is not None and not c.same_basis
    assert c.years[0].reported == pytest.approx(-57381.0)
    assert c.years[0].balance_sheet == pytest.approx(55518.0)


def test_a_52_53_week_year_end_still_finds_its_balance_sheet() -> None:
    """SMPL's year ends on a Saturday; matching the banner's date exactly found no column."""
    c = _bridge("SMPL").consensus
    assert c is not None
    y = c.years[0]
    assert y.balance_sheet is not None and y.balance_sheet_date is not None
    assert y.balance_sheet_date != y.fiscal_year_end


@pytest.mark.parametrize("cell,want", [("Q2\nJun-30-2026", "2026-06-30"),
                                       ("Press Release Q2 Jun-30-2026", "2026-06-30"),
                                       ("FQ3/CQ2\nJun-30-2026", "2026-06-30"),
                                       (46203.0, "2026-06-30"), ("Balance Sheet as of:", None)])
def test_a_ciq_column_label_decodes_to_its_date(cell: Any, want: str | None) -> None:
    got = cs._column_date(cell)
    assert (got.isoformat() if got else None) == want


# --- absent until built; one builder; refresh only from the page's own exports -----------------

def test_a_page_without_the_field_writes_no_null() -> None:
    doc = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    doc.pop("ev_bridge", None)
    got = json.loads(dossier_json(Dossier.model_validate(doc)))
    assert "ev_bridge" not in got
    # nothing else moves but what is DERIVED from the page (valuation_basis, date_semantics, and the
    # gate's flag) — and on this R4 page the missing bridge is that gate's conflict (2026-10-09)
    derived = {"valuation_basis", "date_semantics", "qa_flags"}
    assert {k: v for k, v in got.items() if k not in derived} == {
        k: v for k, v in doc.items() if k not in derived}
    assert any(f.startswith("VALUATION_RECIPE_BASIS_CONFLICT") and "no CIQ TEV bridge" in f
               for f in got["qa_flags"])


def test_assembly_builds_the_layer_through_the_one_builder() -> None:
    """A SOURCE PIN, AND ITS LIMIT STATED: assembly needs the network and an LLM."""
    from vinci.dossier import assemble as asm

    assert "ev_bridge=ciq_sheets.ev_bridge(" in inspect.getsource(asm.assemble_one)


def _bundle(ticker: str) -> Any:
    from vinci.dossier.ciq import CiqBundle

    folder = ROOT / "data" / "manual" / "ciq" / ticker
    if not folder.is_dir():
        pytest.skip("no CIQ export on this machine")
    return CiqBundle.from_files(ticker, sorted(p for p in folder.iterdir() if p.is_file()))


@pytest.mark.parametrize("ticker", sorted(CASES))
def test_the_live_read_matches_the_frozen_case(ticker: str) -> None:
    b = _bundle(ticker)
    case = CASES[ticker]
    got = cs.ev_bridge(b, fy_periods=case["fy_periods"], edgar_net_debt=case["edgar_net_debt"],
                       edgar_source=case["edgar_source"])
    if got is None or (got.source_sha256, got.estimates_sha256) != (
            case["bridge"]["source_sha256"], case["bridge"]["estimates_sha256"]):
        pytest.skip("the on-disk exports are not the frozen ones")
    assert got == _bridge(ticker)


def test_claims_equal_ciqs_current_figure_on_every_committed_name() -> None:
    """THE INDEPENDENT CHECK, on the quantity the multiple uses: CIQ's current TEV − market cap from
    the comps export, on every committed name with an export on this machine."""
    from vinci.dossier.ciq import CiqBundle

    root = ROOT / "data" / "manual" / "ciq"
    if not root.is_dir():
        pytest.skip("no CIQ exports on this machine")
    compared = 0
    for page in sorted((ROOT / "data" / "dossiers").iterdir()):
        folder = root / page.name
        if not folder.is_dir():
            continue
        b = CiqBundle.from_files(page.name, sorted(p for p in folder.iterdir() if p.is_file()))
        got = cs.ev_bridge(b, fy_periods=[])
        assert got is not None and got.ciq_tev_claims is not None, page.name
        assert got.claims == pytest.approx(got.ciq_tev_claims, abs=0.5), page.name
        compared += 1
    assert compared >= 20, f"only {compared} names compared — near-vacuous"


def test_a_bridge_off_ciqs_current_figure_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    """CONSTRUCTED on AMZN's real exports: if the comps export sits on another balance sheet, the
    bridge must flag it rather than pass a mismatched figure to R4 in silence."""
    b = _bundle("AMZN")
    monkeypatch.setattr(cs, "_ciq_tev_claims", lambda _b: (120000.0, "test"))
    got = cs.ev_bridge(b, fy_periods=[])
    assert got is not None and got.note is not None and "DISAGREES" in got.note


def test_the_refresh_lands_the_layer_only_from_the_pages_own_exports(
    tmp_path: pathlib.Path,
) -> None:
    """END TO END on AMZN: both exports are the page's, so the layer lands — and nothing else moves.
    NEGATIVE: another Estimates export, or no stamped bands, leaves the page alone."""
    from vinci.dossier.refresh import ev_bridge_transform, refresh_dossier

    _bundle("AMZN")
    src = ROOT / "data" / "dossiers" / "AMZN"
    folder = tmp_path / "AMZN"
    folder.mkdir()
    for name in ("dossier.json", "dossier.md"):
        (folder / name).write_text((src / name).read_text())
    path = folder / "dossier.json"
    before = json.loads(path.read_text())
    step = ev_bridge_transform("AMZN")
    other = json.loads(json.dumps(before))
    other["forward_consensus"]["source_sha256"] = "0000000000"
    assert step(other) == {}
    unstamped = json.loads(json.dumps(before))
    unstamped["mechanical"]["valuation"]["own_history"]["value"] = []
    assert step(unstamped) == {}
    if not step(before):
        pytest.skip("the on-disk AMZN exports are not the page's")
    refresh_dossier(path, top_level=step)
    after = json.loads(path.read_text())
    assert EvBridge.model_validate(after["ev_bridge"]).claims == pytest.approx(128647.0)
    for key in ("mechanical", "synthesis", "anchor", "forward_consensus"):
        assert after[key] == before[key], f"{key} moved"
    assert list(after)[-1] == "anchor"
