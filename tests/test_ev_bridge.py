"""`ev_bridge` — CIQ's TEV claims, the bridge an enterprise recipe (R4) subtracts from TEV.

CIQ STATES ITS BUILD-UP (Financials→Historical Capitalization): TEV = market cap − cash & ST
investments + total debt + preferred + minority interest − long-term marketable securities. `claims`
is that less market cap. CIQ's 'Net Debt' (Total Debt − Total Cash & ST Investments, the comps
figure) equals it only where the other three lines are nil: on 2026-10-08 they differ on 11 of 26
names (UBER $6,550M against $9,340M; GOOGL $18,023M of preferred).

The exit default follows the operator's rule (2026-10-08): a same-basis, current consensus net-debt
line with the other claims held, else today's claims held — never current − FCF, never manual.

The pins run on frozen DERIVED values (`tests/fixtures/ev_bridge_cases.json`), so they gate in CI.
The local pins re-read the exports and, the strongest test here, rebuild CIQ's own TEV − market cap
from balance-sheet rows on every committed name.
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


def _line(b: EvBridge, label: str) -> float:
    return next(ln.value for ln in b.lines if ln.label == label)


# --- the build-up -----------------------------------------------------------------------------

@pytest.mark.parametrize("ticker", sorted(CASES))
def test_claims_are_the_signed_sum_of_ciqs_build_up(ticker: str) -> None:
    b = _bridge(ticker)
    assert b.claims == pytest.approx(sum(ln.sign * ln.value for ln in b.lines), abs=1e-3)
    assert b.net_debt == pytest.approx(
        _line(b, "Total Debt") - _line(b, "Total Cash & ST Investments"), abs=1e-3)
    assert {ln.label for ln in b.lines} == {
        "Total Debt", "Total Pref. Equity", "Total Minority Interest",
        "Total Cash & ST Investments", "Long Term Marketable Securities"}


def test_amzn_s_claims_are_its_net_debt() -> None:
    b = _bridge("AMZN")
    assert b.claims == b.net_debt == pytest.approx(128647.0)


def test_uber_s_claims_are_not_its_net_debt() -> None:
    """Minority interest is ADDED and long-term marketable securities SUBTRACTED, the second at its
    last reported period (Q1) beside a Q2 press-release balance sheet — CIQ's own footnoted rule."""
    b = _bridge("UBER")
    assert b.net_debt == pytest.approx(9340.0)
    assert _line(b, "Total Minority Interest") == pytest.approx(1083.0)
    ltms = next(ln for ln in b.lines if ln.label == "Long Term Marketable Securities")
    assert ltms.value == pytest.approx(3873.0) and ltms.sign == -1
    assert ltms.as_of == "2026-03-31" and b.balance_sheet_date == "2026-06-30"
    assert b.claims == pytest.approx(6550.0)


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


def test_nke_s_same_basis_current_line_sets_the_exit() -> None:
    """NKE's reported FY2026 net debt ($2,006M) sits 0.09% from CIQ's balance sheet ($2,016M)."""
    c = _bridge("NKE").consensus
    assert c is not None and c.same_basis and c.current
    assert c.gap_ratio is not None and c.gap_ratio < cs.CONSENSUS_SAME_BASIS_MAX
    assert {e.method for e in _bridge("NKE").exit_claims} == {"consensus"}


def test_a_stale_same_basis_line_is_not_used() -> None:
    """MVST's line matches (0.31%) — on FY2021. A same-basis line that stopped is not a forecast."""
    b = _bridge("MVST")
    assert b.consensus is not None and b.consensus.same_basis and not b.consensus.current
    assert {e.method for e in b.exit_claims} == {"held"}


def test_a_stale_line_is_not_used_even_with_forward_values() -> None:
    """CONSTRUCTED from MVST's REAL check — its stale line has no forward values, so on the corpus
    the `current` guard changes nothing. Injected with one, the line must still not be used."""
    b = _bridge("MVST")
    assert b.consensus is not None
    check = b.consensus.model_copy(update={"forward": {"FY 2027": 50.0}})
    got, note = cs.exit_claims_for(b.claims, b.net_debt, check, ["FY 2027"])
    assert [e.method for e in got] == ["held"]
    assert note is not None and "stopped before the latest completed year" in note


def test_a_consensus_exit_keeps_the_other_claims() -> None:
    """CONSTRUCTED from UBER's REAL bridge — the one consensus name, NKE, has no preferred, minority
    or long-term securities, so on the corpus "forward net debt" and "forward net debt + the other
    claims" coincide. Marked usable, UBER's line must carry its −$2,790M of other claims (minority
    +$1,083M, long-term marketable securities −$3,873M) into every exit year."""
    b = _bridge("UBER")
    assert b.consensus is not None and b.consensus.forward
    usable = b.consensus.model_copy(update={"same_basis": True, "current": True})
    fys = list(usable.forward)
    got, note = cs.exit_claims_for(b.claims, b.net_debt, usable, fys)
    assert note is None and [e.method for e in got] == ["consensus"] * len(fys)
    for e in got:
        assert e.value == pytest.approx(usable.forward[e.fiscal_year] - 2790.0, abs=1e-3)


def test_a_broker_basis_line_is_not_used() -> None:
    """AMZN's line reports −$57,381M for FY2025 against +$55,518M on CIQ's balance sheet."""
    c = _bridge("AMZN").consensus
    assert c is not None and not c.same_basis
    assert c.reported == pytest.approx(-57381.0) and c.balance_sheet == pytest.approx(55518.0)


def test_a_52_53_week_year_end_still_finds_its_balance_sheet() -> None:
    """SMPL's year ends on a Saturday; matching the banner's date exactly found no column."""
    c = _bridge("SMPL").consensus
    assert c is not None and c.balance_sheet is not None and c.balance_sheet_date is not None
    assert c.balance_sheet_date != c.fiscal_year_end


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
    out = dossier_json(Dossier.model_validate(doc))
    assert '"ev_bridge"' not in out and json.loads(out) == doc


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


def test_the_build_up_reproduces_ciqs_own_tev_less_market_cap_on_every_name() -> None:
    """THE INDEPENDENT CHECK. Historical Capitalization prints CIQ's TEV and market cap per filing.
    Rebuilt from the balance-sheet rows at the quarter that filing priced, plus its long-term
    marketable securities, the claims must equal TEV − market cap — on every committed name."""
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
        hc = b.sheet("financials", "Historical Capitalization", freq="quarterly")
        bs = b.sheet("financials", "Balance Sheet", freq="quarterly")
        hh, bh = cs._dated_header(hc), cs._dated_header(bs)
        assert hh is not None and bh is not None, page.name
        j = max(k for k in range(1, len(hc[hh])) if cs._column_date(hc[hh][k]))
        tev = cs._row_at(hc, "= Total Enterprise Value (TEV)", j)
        mcap = cs._row_at(hc, "Market Capitalization", j)
        debt = cs._row_at(hc, "+ Total Debt", j)
        when = cs._column_date(hc[hh][j])
        assert tev is not None and mcap is not None and when is not None, page.name
        k = next(k for k in range(len(bs[bh]) - 1, 0, -1)
                 if (d := cs._column_date(bs[bh][k])) and d <= when
                 and cs._row_at(bs, "Total Debt", k) == debt)
        rebuilt = (sum(s * (cs._row_at(bs, lbl, k) or 0.0) for lbl, s in cs._TEV_CLAIM_ROWS)
                   - (cs._row_at(hc, cs._LTMS_ROW, j) or 0.0))
        assert rebuilt == pytest.approx(tev - mcap, abs=0.5), page.name
        compared += 1
    assert compared >= 20, f"only {compared} names compared — near-vacuous"


def test_the_refresh_lands_the_layer_only_from_the_pages_own_exports(
    tmp_path: pathlib.Path,
) -> None:
    """END TO END on AMZN: both exports are the page's, so the layer lands — equal to the
    builder's — and nothing else moves. NEGATIVE: another Estimates export, or no stamped bands,
    leaves the page alone."""
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
    landed = step(before)
    if not landed:
        pytest.skip("the on-disk AMZN exports are not the page's")
    refresh_dossier(path, top_level=step)
    after = json.loads(path.read_text())
    assert EvBridge.model_validate(after["ev_bridge"]).claims == pytest.approx(128647.0)
    for key in ("mechanical", "synthesis", "anchor", "forward_consensus"):
        assert after[key] == before[key], f"{key} moved"
    assert list(after)[-1] == "anchor"
