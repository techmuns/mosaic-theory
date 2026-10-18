"""The active recipe's basis, the anchor's R1 eligibility, the page's dates, and the forward
history's latest close — the operator's dossier-schema correction (2026-10-09).

THE DEFECT. AMZN's page is tagged `R4_forward_ev_ebit`, but the block carrying the tag held R1's
screen arithmetic (EV/EBITDA, EDGAR net debt, a weighted-average share count) with nothing saying
which fields the active recipe may use; the forward history called its 2026-09-16 close `current`
beside CIQ's ≥2026-10-06 multiple; and `reference_date` (2026-09-22) was the only date at the top.

Pinned on the COMMITTED pages as INVARIANTS against each page's own layers (the test-layer rule:
a living artifact gets no value pins), and on CONSTRUCTED copies of real pages for the gate's
negative cases — none of which the committed corpus carries today, which is exactly why a gate that
finds nothing there must be shown it can find something.
"""
from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier import midcycle
from vinci.dossier import valuation_basis as vb
from vinci.dossier.anchor import R1_VALUE_FIELDS
from vinci.dossier.ciq_sheets import EV_BRIDGE_CIQ_TOL
from vinci.dossier.propose import ProposalRefusedError, build_r4_template, check_tier_agreement
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
PAGES = sorted(p.parent.name for p in DOSS.glob("*/dossier.json"))


def _page(t: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((DOSS / t / "dossier.json").read_text())
    return doc


# --- the blocks on every committed page are the page's own --------------------------------------

def test_every_committed_page_carries_blocks_derived_from_itself() -> None:
    """Both blocks, the anchor's tag and the conflict flags are what the page derives TODAY. A text
    writer that edits a layer without re-serialising (`anchor-backfill`'s splice) leaves them stale;
    a no-op `refresh_dossier(path)` re-derives them."""
    for t in PAGES:
        text = (DOSS / t / "dossier.json").read_text()
        assert dossier_json(Dossier.model_validate_json(text)) == text, (
            f"{t}: the stored valuation_basis/date_semantics/flags are stale — run a no-op "
            "refresh_dossier on the page")
        doc = json.loads(text)
        assert {"valuation_basis", "date_semantics"} <= set(doc), t
        assert "scenario_eligibility" in doc["anchor"], t


def test_the_serializer_re_derives_on_every_write() -> None:
    """The write paths change layers with `model_copy`, which runs no validator — the assembler's
    keep-the-committed-recipe step swaps the anchor that way. The blocks written must describe the
    page written, not the page loaded. (A round-trip of an unchanged page cannot see this: the
    stored blocks are already right. A mutant skipping the re-derive survived until this pin.)"""
    model = Dossier.model_validate(_page("AMZN"))
    assert model.anchor is not None and model.valuation_basis is not None
    swapped = model.model_copy(update={
        "anchor": model.anchor.model_copy(update={"recipe_hint": sc.RECIPE_R1}),
        "ev_bridge": None})
    written = json.loads(dossier_json(swapped))
    assert written["valuation_basis"]["recipe"] == sc.RECIPE_R1
    assert written["valuation_basis"]["anchor_fields_eligible"] is True
    assert written["anchor"]["scenario_eligibility"]["eligible_for_scenario_valuation"] is True
    assert written["date_semantics"]["balance_sheet_date"] is None  # the bridge is gone


def test_the_anchors_r1_fields_are_tagged_by_the_scenario_gates_own_rule() -> None:
    """Eligible exactly where the gate would accept an R1 record — read off the gate itself, not a
    copy of its rule — and ineligible on every other page, AMZN's R4 among them."""
    seen = {True: 0, False: 0}
    for t in PAGES:
        doc = _page(t)
        tag = doc["anchor"]["scenario_eligibility"]
        try:
            check_tier_agreement(doc, sc.RECIPE_R1)
            accepts = True
        except ProposalRefusedError:
            accepts = False
        assert tag["eligible_for_scenario_valuation"] is accepts, (t, tag["reason"])
        assert tag["fields"] == list(R1_VALUE_FIELDS), t
        assert doc["valuation_basis"]["anchor_fields_eligible"] is accepts, t
        seen[accepts] += 1
    assert seen[True] >= 10 and seen[False] >= 5, seen
    amzn = _page("AMZN")["anchor"]["scenario_eligibility"]
    assert amzn["eligible_for_scenario_valuation"] is False


def test_the_tag_is_computed_so_a_hand_re_tag_cannot_leave_it_wrong() -> None:
    """Edit only the recipe, as a hand re-tag does, and the serialised tag follows."""
    from vinci.dossier.anchor import Anchor

    a = Anchor.model_validate(_page("BRBR")["anchor"])
    assert a.scenario_eligibility.eligible_for_scenario_valuation is True
    r4 = a.model_copy(update={"recipe_hint": sc.RECIPE_R4})
    assert json.loads(r4.model_dump_json())["scenario_eligibility"][
        "eligible_for_scenario_valuation"] is False


# --- R4: the active basis, and no R1 field consumed ----------------------------------------------

@pytest.mark.parametrize("t", ["AMZN", "UBER"])
def test_an_r4_page_states_r4s_basis_from_its_own_layers(t: str) -> None:
    doc = _page(t)
    b = doc["valuation_basis"]
    assert (b["recipe"], b["earnings_basis"], b["multiple_basis"], b["ev_bridge_basis"]) == (
        sc.RECIPE_R4, "NTM EBIT", sc.BASIS_EV_NTM_EBIT, "CIQ TEV-compatible")
    assert b["priceable"] is True and b["conflicts"] == []
    # today's multiple is CIQ Estimates' NTM TEV/EBIT — never the history's latest close
    cm = next(m for m in doc["forward_consensus"]["current_multiples"]
              if m["metric"] == "TEV/EBIT" and m["period"] == "NTM")
    assert b["current_multiple"]["value"] == cm["value"]
    assert b["current_multiple"]["as_of"] == doc["forward_consensus"]["as_of"]
    # the bridge is CIQ's, reconciled, and EDGAR's figure is a cross-check only
    eb = doc["ev_bridge"]
    assert b["ev_bridge"]["current_claims"] == eb["claims"]
    assert abs(eb["claims"] - eb["ciq_tev_claims"]) <= EV_BRIDGE_CIQ_TOL
    assert b["ev_bridge"]["reconciles_to_ciq_tev"] is True
    cc = b["ev_bridge"]["cross_check"]
    assert cc["value"] == eb["edgar_net_debt"] and cc["eligible_for_primary_bridge"] is False
    assert sum(c["sign"] * c["value"] for c in b["ev_bridge"]["components"]) == pytest.approx(
        eb["claims"], abs=EV_BRIDGE_CIQ_TOL)
    # the exit claims are the bridge's own default, automated, never a cash-flow roll-forward
    ex = b["exit_claims"]
    assert [(y["fiscal_year"], y["value"]) for y in ex["by_year"]] == [
        (x["fiscal_year"], x["value"]) for x in eb["exit_claims"]]
    assert ex["fcf_rollforward_used"] is False
    # the share count is the point-in-time count; the EPS count stays apart and ineligible
    sh = b["exit_share_count"]
    assert sh["default_method"] == "HOLD_CURRENT_SHARES_OUTSTANDING"
    assert sh["current_value"] == doc["mechanical"]["stock_info"]["shares_out"]["value"]
    dwa = sh["diluted_weighted_average"]
    assert dwa["value"] == doc["anchor"]["diluted_shares"]["value"] != sh["current_value"]
    assert dwa["eligible_as_point_in_time_denominator"] is False
    assert b["non_operating_assets"]["primary_treatment"] == "included_in_vendor_tev"
    assert b["non_operating_assets"]["carve_out"] is False


def test_held_and_consensus_exits_are_named_for_what_they_are() -> None:
    """`held` → HOLD_CURRENT_SAME_BASIS, an assumption; a same-basis consensus → a forecast. A mix
    is said to be one. CONSTRUCTED: no committed page carries a consensus exit."""
    doc = _page("AMZN")
    ex = vb.derive(doc).exit_claims
    assert ex is not None and (ex.method, ex.forecast_status) == (
        "HOLD_CURRENT_SAME_BASIS", "assumption")
    doc["ev_bridge"]["exit_claims"][0]["method"] = "consensus"
    ex = vb.derive(doc).exit_claims
    assert ex is not None and (ex.method, ex.forecast_status) == ("PER_YEAR", "mixed")
    assert ex.by_year[0].method == "SAME_BASIS_CONSENSUS"
    assert ex.by_year[0].forecast_status == "forecast"


def test_the_r4_template_reads_no_r1_field_from_the_anchor() -> None:
    """No active EV/EBITDA field is consumed by R4: scramble the anchor's R1 inputs and the R4
    template is unchanged — its net debt is the bridge's, its shares the point-in-time count."""
    doc = _page("AMZN")
    before = build_r4_template(copy.deepcopy(doc))
    a = doc["anchor"]
    a["multiple"]["value"], a["net_debt"]["value"] = 999.0, -1.0
    a["d_and_a"]["value"], a["margin"]["value"] = -1.0, 0.999
    a["multiple_basis"] = "EV/EBITDA (scrambled)"
    assert build_r4_template(copy.deepcopy(doc)) == before
    # the diluted weighted average is read ONLY as `resolve_shares`' 2% agreement check against the
    # point-in-time count (beyond it the template refuses) — moved within it, the value holds
    a["diluted_shares"]["value"] = doc["mechanical"]["stock_info"]["shares_out"]["value"] * 1.01
    after = build_r4_template(doc)
    assert after["facts"]["diluted_shares"]["value"] == before["facts"]["diluted_shares"]["value"]
    assert after["facts"]["net_debt"] == before["facts"]["net_debt"]


# --- the gate: each R4 input missing or disagreeing is a conflict, and nothing is substituted ----

def _r4_conflicts(doc: dict[str, Any]) -> list[str]:
    return vb.derive(doc).conflicts


def test_no_bridge_is_a_conflict_and_edgar_is_not_substituted() -> None:
    doc = _page("AMZN")
    del doc["ev_bridge"]
    b = vb.derive(doc)
    assert any("no CIQ TEV bridge" in c for c in b.conflicts) and b.priceable is False
    assert b.ev_bridge is None and b.exit_claims is None


def test_a_bridge_off_ciqs_tev_is_a_conflict_on_both_sides_of_the_tolerance() -> None:
    doc = _page("AMZN")
    doc["ev_bridge"]["claims"] = doc["ev_bridge"]["ciq_tev_claims"] + EV_BRIDGE_CIQ_TOL * 0.8
    assert not _r4_conflicts(doc)
    doc["ev_bridge"]["claims"] = doc["ev_bridge"]["ciq_tev_claims"] + EV_BRIDGE_CIQ_TOL * 2
    assert any("disagrees with CIQ's TEV" in c for c in _r4_conflicts(doc))
    doc["ev_bridge"]["ciq_tev_claims"] = None
    assert any("unchecked" in c for c in _r4_conflicts(doc))


@pytest.mark.parametrize("break_it,needle", [
    (lambda d: d["forward_consensus"].update(current_multiples=[
        m for m in d["forward_consensus"]["current_multiples"] if m["metric"] != "TEV/EBIT"]),
     "no CIQ Estimates NTM TEV/EBIT"),
    (lambda d: d["ev_bridge"].update(estimates_sha256="0000000000"), "two Estimates pulls"),
    (lambda d: d["ev_bridge"].update(exit_claims=[]), "no exit claims"),
    (lambda d: d["mechanical"]["stock_info"].update(
        shares_out={"value": None, "source_ref": None, "status": "missing", "note": "x"}),
     "stock_info.shares_out is absent"),
])
def test_each_missing_r4_input_is_a_named_conflict(break_it: Any, needle: str) -> None:
    doc = _page("AMZN")
    assert not _r4_conflicts(doc)
    break_it(doc)
    assert any(needle in c for c in _r4_conflicts(doc)), _r4_conflicts(doc)


def test_a_conflict_reaches_qa_flags_once_and_leaves_when_resolved() -> None:
    doc = _page("AMZN")
    clean = Dossier.model_validate(doc)
    del doc["ev_bridge"]
    broken = vb.with_derived(vb.with_derived(Dossier.model_validate(doc)))
    flags = [f for f in broken.qa_flags if f.startswith(vb.CONFLICT_FLAG)]
    assert len(flags) == 1 and "no CIQ TEV bridge" in flags[0]
    healed = vb.with_derived(broken.model_copy(update={"ev_bridge": clean.ev_bridge}))
    assert not [f for f in healed.qa_flags if f.startswith(vb.CONFLICT_FLAG)]
    assert healed.qa_flags == clean.qa_flags


# --- the other recipes, and the pages that name none ---------------------------------------------

def test_every_page_says_what_it_can_price() -> None:
    for t in PAGES:
        doc = _page(t)
        b, hint = doc["valuation_basis"], doc["anchor"]["recipe_hint"]
        assert b["recipe"] == hint, t
        if hint.startswith("R1"):
            assert b["multiple_basis"] == "EV/EBITDA" and b["ev_bridge_basis"].startswith("EDGAR")
            assert b["ev_bridge"]["current_claims"] == doc["anchor"]["net_debt"]["value"], t
            assert b["priceable"] is (doc["anchor"]["applicable"] and not b["conflicts"]), t
        elif hint == sc.RECIPE_R3:
            assert b["multiple_basis"] == sc.BASIS_PE and b["ev_bridge"] is None
            assert b["exit_share_count"] is None, "EPS × P/E is per share already"
        elif hint != sc.RECIPE_R4:
            assert b["priceable"] is False and b["earnings_basis"] is None, t
            assert hint in b["status_reason"], t


def test_the_ids_and_formulas_are_the_engines() -> None:
    assert (vb.RECIPE_R1, vb.RECIPE_R3, vb.RECIPE_R4) == (sc.RECIPE_R1, sc.RECIPE_R3, sc.RECIPE_R4)
    assert (vb.BASIS_PE, vb.BASIS_EV_NTM_EBIT) == (sc.BASIS_PE, sc.BASIS_EV_NTM_EBIT)
    assert (vb.R3_FORMULA, vb.R4_FORMULA) == (sc.R3_FORMULA, sc.R4_FORMULA)
    assert _page("BRBR")["valuation_basis"]["formula_steps"] == list(midcycle.R1_FORMULA)


# --- the forward history's latest close is an observation, not today's multiple ------------------

def test_no_forward_band_calls_its_latest_close_current() -> None:
    """Every band: the latest point IS `latest_observed_close`, dated `latest_close_date`, and the
    statistics are over the closes before it — measured, not taken from the flag."""
    bands = 0
    for t in PAGES:
        for s in (_page(t).get("forward_multiple_history") or {}).get("series", []):
            b = s.get("band")
            if not b:
                continue
            bands += 1
            assert "current" not in b, (t, s["metric"])
            nums = [p for p in s["points"] if p["close"] is not None]
            assert b["latest_observed_close"] == nums[-1]["close"], (t, s["metric"])
            assert b["latest_close_date"] == nums[-1]["date"] == b["as_of"], (t, s["metric"])
            earlier = [p["close"] for p in nums[:-1]]
            assert b["n_closes"] == len(earlier)
            assert b["latest_observed_close_in_distribution"] is False
            assert (b["low"], b["high"]) == (min(earlier), max(earlier)), (t, s["metric"])
    assert bands >= 60, f"only {bands} bands checked"


def test_a_band_written_with_current_still_reads() -> None:
    from vinci.dossier.schemas import ForwardHistoryBand

    raw = next(s for s in _page("AMZN")["forward_multiple_history"]["series"]
               if s["metric"] == "EV/NTM EBIT")["band"]
    old = {("current" if k == "latest_observed_close" else k): v for k, v in raw.items()
           if k not in ("latest_close_date", "latest_observed_close_in_distribution")}
    band = ForwardHistoryBand.model_validate(old)
    assert json.loads(band.model_dump_json()) == raw


def test_the_r4_template_names_the_history_close_as_an_observation() -> None:
    """The template called the 2026-09-16 close "today's"; it now names it, with its date."""
    t = build_r4_template(_page("AMZN"))
    ev = next(x for x in t["_evidence"]["multiple"] if x.startswith("own history EV/NTM EBIT"))
    assert "latest observed close" in ev and "current" not in ev and "today" not in ev
    why = t["scenarios"]["base"]["_multiple_why_no_anchor"]
    assert "today's" not in why


# --- the dates: each input's own, and the screen's date named as the screen's --------------------

def test_every_page_names_its_dates_from_its_layers() -> None:
    for t in PAGES:
        doc = _page(t)
        ds, m = doc["date_semantics"], doc["mechanical"]
        assert ds["screen_reference_date"] == str(doc["reference_date"])[:10], t
        assert "NOT the freshness date" in ds["reference_date_semantics"]
        assert ds["price_as_of"] == m["stock_info"].get("as_of"), t
        assert ds["market_cap_as_of"] == m["stock_info"].get("market_cap_as_of"), t
        assert ds["consensus_as_of"] == (doc.get("forward_consensus") or {}).get("as_of"), t
        assert ds["historical_multiple_latest_observation"] == (
            doc.get("forward_multiple_history") or {}).get("as_of"), t
        named = [ds[k] for k in ("price_as_of", "market_cap_as_of", "tev_as_of", "consensus_as_of",
                                 "balance_sheet_date", "historical_multiple_latest_observation")]
        days = [str(x).lstrip("≥")[:10] for x in named if x]
        assert ds["analysis_as_of"] == (max(days) if days else None), t


# --- (2026-10-10) the four folded fixes -----------------------------------------------------------

def test_every_dossier_writer_saves_through_the_one_write() -> None:
    """A SOURCE PIN, AND ITS LIMIT STATED. Every function that names `dossier.json` and writes must
    save the page through `write_dossier`/`dossier_json` — never pydantic's default dump (25 of 26
    pages rewritten with nulls), a raw `json.dumps`, or a text splice written as-is (the derived
    blocks left describing the old page). It finds writers by the literal `dossier.json`; one that
    takes its path from a caller without naming the file escapes it, which is why the corpus
    round-trip pin above stands beside it."""
    import ast

    bypass = ("model_dump_json", "json.dumps", "upsert_text", "replace_anchor_block",
              "replace_valuation_fields", "insert_anchor_block")
    not_pages = {("frontend/build.py", "main"),                       # index + snapshots
                 ("scripts/build_companyfacts_fixture.py", "main"),   # a test fixture
                 ("vinci/dossier/refresh.py", "_rerender_only")}      # markdown only
    writers = set()
    for f in sorted([*ROOT.joinpath("vinci").rglob("*.py"), *ROOT.joinpath("scripts").glob("*.py"),
                     ROOT / "frontend" / "build.py"]):
        src = f.read_text()
        if "dossier.json" not in src:
            continue
        rel = str(f.relative_to(ROOT))
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.FunctionDef):
                continue
            seg = ast.get_source_segment(src, node) or ""
            if "dossier.json" not in seg or (rel, node.name) in not_pages:
                continue
            calls = [c for c in ast.walk(node) if isinstance(c, ast.Call)
                     and isinstance(c.func, ast.Attribute) and c.func.attr == "write_text"]
            for c in calls:
                arg = ast.get_source_segment(src, c.args[0]) if c.args else ""
                assert not any(b in (arg or "") for b in bypass), (rel, node.name, arg)
            if calls or "write_dossier(" in seg or "write_recorded(" in seg:
                writers.add((rel, node.name))
                assert any(w in seg for w in ("write_dossier(", "write_recorded(",
                                              "dossier_json(")), (rel, node.name)
    # 10 → 8 on 2026-10-18: `scripts/refresh_stock_performance.py` and `refresh_concentration.py`
    # were retired (stale calls, writing outside `refresh_dossier`'s guards —
    # docs/records/2026-10-18-stale-refresh-scripts-retired.md)
    assert len(writers) >= 8, f"found {len(writers)} page writers: {sorted(writers)}"


def test_a_spliced_anchor_is_written_with_blocks_that_describe_it(tmp_path: pathlib.Path) -> None:
    """The real failure shape, on NFLX: an anchor write that flips `applicable` left the stored
    block saying the R1 fields were ineligible while the anchor's own tag said eligible. Written
    through `write_recorded`, the block follows the anchor, and the page records that it moved."""
    from vinci.dossier import layer_refresh

    path = tmp_path / "dossier.json"
    original = (DOSS / "NFLX" / "dossier.json").read_text()
    path.write_text(original)
    d = Dossier.model_validate_json(original)
    assert d.anchor is not None
    layer_refresh.write_recorded(
        path, original, d.model_copy(update={"anchor": d.anchor.model_copy(
            update={"applicable": True})}), "anchor-backfill")
    doc = json.loads(path.read_text())
    assert doc["anchor"]["scenario_eligibility"]["eligible_for_scenario_valuation"] is True
    assert doc["valuation_basis"]["anchor_fields_eligible"] is True
    rec = doc["layer_refreshes"][-1]
    assert rec["writer"] == "anchor-backfill"
    assert {"anchor", "valuation_basis"} <= set(rec["layers"])


def test_the_gate_applies_the_templates_own_share_guard() -> None:
    """Wherever the share count enters (R1, R4), the block's verdict IS `resolve_shares`'s — read
    off the guard itself, on every page. IT and LLY (5.43%, 5.06%) are the live refusals."""
    from vinci.dossier.propose import resolve_shares

    refused = []
    for t in PAGES:
        doc = _page(t)
        b, a = doc["valuation_basis"], doc["anchor"]
        if not (b["recipe"] == sc.RECIPE_R4 or (b["recipe"].startswith("R1") and a["applicable"])):
            continue
        try:
            resolve_shares(doc)
            guard = None
        except ProposalRefusedError as exc:
            guard = str(exc)
            refused.append(t)
        share_conflicts = [c for c in b["conflicts"] if "share counts" in c or "shares_out" in c]
        assert share_conflicts == ([guard] if guard else []), t
        if guard:
            assert b["priceable"] is False
            assert f"{vb.CONFLICT_FLAG}: {guard}" in doc["qa_flags"], t
    assert {"IT", "LLY"} <= set(refused), refused


def test_todays_multiple_names_its_snapshot_and_its_value_at_the_page_price() -> None:
    """Struck at CIQ's market cap on its own date, measured: every FY TEV/EBIT × that year's EBIT
    consensus equals market cap + CIQ claims. At the page's price it is the entry multiple an R4
    record carries, on the record's own share basis."""
    for t in ("AMZN", "UBER"):
        doc = _page(t)
        cm, si = doc["valuation_basis"]["current_multiple"], doc["mechanical"]["stock_info"]
        eb = doc["ev_bridge"]
        assert (cm["snapshot_as_of"], cm["snapshot_market_cap"]) == (
            si["market_cap_as_of"], si["market_cap"]["value"])
        assert cm["snapshot_tev"] == pytest.approx(si["market_cap"]["value"] + eb["ciq_tev_claims"])
        assert cm["snapshot_reconciles"] is True
        ntm_ebit = cm["snapshot_tev"] / cm["value"]
        at_price = (si["price"]["value"] * si["shares_out"]["value"] / 1e6
                    + eb["ciq_tev_claims"]) / ntm_ebit
        assert cm["value_at_page_price"] == pytest.approx(at_price, rel=1e-6)
        assert cm["days_price_after_snapshot"] == doc["date_semantics"][
            "price_days_after_valuation_snapshot"]


def test_a_multiple_off_its_snapshot_is_not_carried_to_the_page_price() -> None:
    """CONSTRUCTED from AMZN (VRRM, NCNO and CNXC carry the real shape, on pages no EV recipe
    prices): an FY row struck at another TEV breaks the reconciliation, the scaling is withheld,
    and on R4 it is a conflict."""
    doc = _page("AMZN")
    fy = next(m for m in doc["forward_consensus"]["current_multiples"]
              if m["metric"] == "TEV/EBIT" and m["period"] == "FY 2027")
    fy["value"] *= 1.01
    b = vb.derive(doc)
    assert b.current_multiple is not None and b.current_multiple.snapshot_reconciles is False
    assert b.current_multiple.value_at_page_price is None
    assert any("not struck at the page's CIQ snapshot" in c for c in b.conflicts)


def test_the_share_count_says_it_is_the_basic_count() -> None:
    for t in ("AMZN", "UBER", "BRBR"):
        sh = _page(t)["valuation_basis"]["exit_share_count"]
        assert sh["count_basis"].startswith("BASIC") and sh["includes_dilutive_increment"] is False
        assert "dilutive increment" in sh["override_rule"]
        assert "never the diluted weighted average" in sh["override_rule"]


def test_the_valuation_snapshot_date_is_named_beside_the_price() -> None:
    for t in PAGES:
        doc = _page(t)
        ds, si = doc["date_semantics"], doc["mechanical"]["stock_info"]
        assert ds["valuation_snapshot_as_of"] == si.get("market_cap_as_of"), t
        if si.get("as_of") and si.get("market_cap_as_of"):
            from datetime import date
            gap = (date.fromisoformat(str(si["as_of"])[:10])
                   - date.fromisoformat(str(si["market_cap_as_of"])[:10])).days
            assert ds["price_days_after_valuation_snapshot"] == gap, t
