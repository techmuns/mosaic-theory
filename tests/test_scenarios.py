"""Versioned scenario records — schema, round-trip, recipe run, and the unit guards.

Pins: the record round-trips byte-stably; the recipe REFUSES a mismatched multiple_basis or a
missing source-bound fact (never assumes); the machine records PASS/FAIL honestly and never moves
the verdict off ``pending_analyst``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci import scenarios as sc


def _rec(**over: object) -> sc.ScenarioRecord:
    base = {
        "ticker": "TEST", "recipe_id": sc.RECIPE_R1,
        "recipe_desc": "mid-cycle operating margin x exit EV/EBITDA",
        "multiple_basis": "EV/EBITDA", "underwrite_date": "2026-07-19", "analyst": "tester",
        "spot": 46.0, "spot_source": "test",
        "facts": {
            "d_and_a": sc.Fact(value=286.321, unit="$M", basis="consolidated FY2025",
                               source="10-K"),
            "net_debt": sc.Fact(value=979.776, unit="$M", basis="incl leases", source="10-Q"),
            "diluted_shares": sc.Fact(value=59.91, unit="M shares", basis="Q1-2026", source="10-Q"),
        },
        "scenarios": {
            "bear": sc.ScenarioInput(revenue=2850.0, margin=0.015, multiple=6.0, reason="trough"),
            "base": sc.ScenarioInput(revenue=3100.0, margin=0.0625, multiple=6.5, reason="mid"),
            "bull": sc.ScenarioInput(revenue=3400.0, margin=0.080, multiple=7.0, reason="turn"),
        },
    }
    base.update(over)
    return sc.ScenarioRecord(**base)  # type: ignore[arg-type]


def test_record_roundtrips(tmp_path: Path) -> None:
    rec = _rec()
    p = sc.write_record(rec, root=tmp_path)
    back = sc.read_record("TEST", root=tmp_path)
    assert back == rec
    assert p.read_text().endswith("\n")                 # newline-terminated, diff-able
    assert sc.all_records(root=tmp_path)["TEST"] == rec


def test_schema_file_excluded_from_records(tmp_path: Path) -> None:
    sc.write_record(_rec(), root=tmp_path)
    sc.write_json_schema(root=tmp_path)
    assert (tmp_path / "scenarios" / "_schema.json").exists()
    assert list(sc.all_records(root=tmp_path)) == ["TEST"]   # `_schema.json` is not a record


def test_recipe_computes_on_ebitda_and_records_fail() -> None:
    """The WERN shape: reward negative at spot → an honest FAIL, recorded not hidden."""
    out = sc.run_recipe(_rec())
    per = out.result.per_scenario
    assert per["base"].ebitda == pytest.approx(480.071)      # EBIT 193.75 + D&A 286.321
    assert per["base"].value_per_share == pytest.approx(35.73, abs=0.02)
    assert per["bear"].value_per_share == pytest.approx(16.60, abs=0.02)
    assert per["bull"].value_per_share == pytest.approx(48.88, abs=0.02)
    assert out.result.reward == pytest.approx(-10.27, abs=0.02)
    assert out.result.risk == pytest.approx(29.40, abs=0.02)
    assert out.result.ratio == pytest.approx(-0.349, abs=0.005)
    assert out.result.pass_fail == "FAIL" and out.result.bar == 2.0
    # the machine records, it does NOT ratify
    assert out.verdict.status == "pending_analyst" and out.verdict.recorded is None


def test_recipe_refuses_mismatched_basis() -> None:
    with pytest.raises(ValueError, match="multiple_basis"):
        sc.run_recipe(_rec(multiple_basis="EV/EBIT"))


def test_recipe_refuses_missing_fact() -> None:
    r = _rec()
    facts = {k: v for k, v in r.facts.items() if k != "d_and_a"}
    with pytest.raises(ValueError, match="d_and_a"):
        sc.run_recipe(r.model_copy(update={"facts": facts}))


def test_recipe_refuses_unknown_recipe() -> None:
    with pytest.raises(ValueError, match="unknown recipe_id"):
        sc.run_recipe(_rec(recipe_id="R9_not_a_recipe"))


def test_blank_reason_is_refused_at_the_record_boundary() -> None:
    """F2: ``run_recipe`` builds its Scenario directly, bypassing build_scenario's no-reason guard,
    so the refusal binds on the RECORD — the durable artifact — instead."""
    for blank in ("", "   ", "\n\t"):
        with pytest.raises(ValueError, match="reason is required"):
            sc.ScenarioInput(revenue=3100.0, margin=0.0625, multiple=6.5, reason=blank)
    ok = sc.ScenarioInput(revenue=3100.0, margin=0.0625, multiple=6.5, reason="stated why")
    assert ok.reason == "stated why"


def test_norm_fcf_is_none_without_its_inputs_never_ebit() -> None:
    """F1: with cash interest/tax absent the FCF formula collapses to EBIT. Printing EBIT under a
    'normalized FCF' label would be a fabricated number — it must be None instead."""
    r = _rec()
    facts = {k: v for k, v in r.facts.items() if k not in ("cash_interest", "cash_tax_rate")}
    out = sc.run_recipe(r.model_copy(update={"facts": facts}))
    base = out.result.per_scenario["base"]
    assert base.norm_fcf is None                       # NOT 193.75 (EBIT) under an FCF label
    assert base.op_income == pytest.approx(193.75)     # EBIT itself is still reported, as EBIT
    assert base.ev_ebit is not None                    # the other cross-check is unaffected
    # supplied → it computes: EBIT 193.75 − tax 38.674 − interest 39.053
    full = sc.run_recipe(_rec(facts={
        **facts,
        "cash_interest": sc.Fact(value=39.053, unit="$M", basis="FY2025", source="10-K"),
        "cash_tax_rate": sc.Fact(value=0.25, unit="rate", basis="assumption", source="analyst"),
    }))
    assert full.result.per_scenario["base"].norm_fcf == pytest.approx(116.02, abs=0.05)


def test_committed_schema_matches_the_model() -> None:
    """F4: ``scenarios/_schema.json`` is committed — pin it so a model change cannot silently
    leave a stale schema behind."""
    committed = json.loads((Path(__file__).resolve().parents[1] / "scenarios" /
                            "_schema.json").read_text())
    assert committed == sc.json_schema(), (
        "scenarios/_schema.json is stale — regenerate with vinci.scenarios.write_json_schema()")


def test_frontend_build_stays_stdlib_only() -> None:
    """F3: docs/DEPLOY.md pins frontend/build.py as the Cloudflare Pages build step — run as
    `python frontend/build.py` with NO requirements.txt. Importing `vinci` there would pull in
    pydantic and break the deploy, so the scenario-card renderer reads the records as plain JSON."""
    src = (Path(__file__).resolve().parents[1] / "frontend" / "build.py").read_text()
    offenders = [ln.strip() for ln in src.splitlines()
                 if ln.strip().startswith(("import vinci", "from vinci"))]
    assert not offenders, f"frontend/build.py must stay stdlib-only; found: {offenders}"


def _load_build():  # type: ignore[no-untyped-def]
    """Import frontend/build.py as a module (it is a script, not a package member)."""
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "frontend" / "build.py"
    spec = importlib.util.spec_from_file_location("fe_build", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_emit_scenarios_matches_theme_embedded_card_and_is_deterministic() -> None:
    """The standalone `frontend/scenarios/<T>.json` must be the EXACT `_scenario_card()` shape the
    theme JSON embeds (one contract), and two emits must be byte-identical (committed output never
    churns). Runs against the real committed `scenarios/` + `frontend/themes/` artifacts."""
    build = _load_build()
    root = Path(__file__).resolve().parents[1]
    cards = build._scenario_cards()
    assert "WERN" in cards                                  # the committed record reaches the emit
    theme = json.loads((root / "frontend" / "themes" / "truckload-supply-purge.json").read_text())
    embedded = next(w["scenarioCard"] for w in theme["watchlist"]
                    if w["ticker"] == "WERN" and "scenarioCard" in w)
    assert cards["WERN"] == embedded                        # ONE shape, wherever the card renders
    out = root / "frontend" / "scenarios"
    if out.is_dir():                                        # emitted by the build → pinned stable
        first = {p.name: p.read_bytes() for p in sorted(out.glob("*.json"))}
        build.emit_scenarios()
        second = {p.name: p.read_bytes() for p in sorted(out.glob("*.json"))}
        assert first == second                              # idempotent, byte-for-byte
        idx = json.loads(second["index.json"].decode())
        assert idx == {"tickers": sorted(cards)}


def test_reserved_theme_slugs_fail_loud() -> None:
    """A theme slug that collides with a themes-route first segment (radar/watchlist/scan/forward)
    would be unroutable — the build must refuse it, never ship a shadowed page."""
    build = _load_build()
    with pytest.raises(SystemExit, match="reserved themes route"):
        build._slug("Radar")
    assert build._slug("Truckload Supply Purge")[0] == "truckload-supply-purge"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
