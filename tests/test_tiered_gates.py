"""THE TIERED LADDER (operator-ratified 2026-08-21) — fund-wide, all recipes, inform-only.

FOUR RULINGS pin this build (recorded in STATE §Next-steps): the BUY-eligibility line is
ratio ≥1.75 AND base IRR ≥12% with 2.0/15% becoming the PREFERRED tier; the line INFORMS and
never blocks (survival stays the only hard block); the sealed book FREEZES with the regime made
visible; the IRR stays price-only with the convention stamped.

THE ADD-BESIDE CONTRACT is the load-bearing property here, and it is the 2026-08-05 precedent
(`gate` arrived beside `pass_fail`, which kept its meaning) applied again: `pass_fail`,
`irr_pass_fail`, `gate`, `bar` and `irr_floor` keep their arithmetic on every record ever
written — the preferred lines ARE the legacy constants — and the new fields default None, so a
committed record round-trips byte-identical and its display card gains no keys.

CORPUS BEFORE SYNTHETIC: the e2e pins below run the engine over the REAL committed records in
memory. EPAM is the design's own acceptance case — 21.8% IRR (preferred) on a 1.50 ratio
(below_target) → NOT eligible: "a 40% IRR on a 1.2:1 spread is a levered bet, not a cheap one".
IT pins the determinate-false AND: ratio below the line + IRR undefined → False, never None.
"""
from __future__ import annotations

import functools
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier.render import _underwrite_lines

ROOT = Path(__file__).resolve().parents[1]
RECORDS = sorted(p for p in (ROOT / "scenarios").glob("*.json") if not p.name.startswith("_"))



@functools.lru_cache(maxsize=1)
def _build() -> Any:
    """`frontend/build.py` loaded lazily, matching the six other test files that exec it (mine
    was the only module-level load — review, #487). build.py is `__main__`-guarded so importing
    it is side-effect-free either way; the cost of the outlier is that an import-time failure
    there would break COLLECTION of this file rather than one test."""
    spec = importlib.util.spec_from_file_location("_tg_build", ROOT / "frontend" / "build.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

#: Every camelCase key the ladder adds to the display card. Named ONCE here so the three pins
#: (absent-on-legacy, present-on-new-regime, rendered-by-the-view) cannot drift apart.
NEW_CARD_KEYS = ("gateRegime", "asymmetryTier", "returnTier", "eligibleRatio", "eligibleIrr",
                 "eligible", "eligibleUndefined", "ceilingEligible", "irrConvention")


def _load(p: Path) -> sc.ScenarioRecord:
    return sc.ScenarioRecord.model_validate(json.loads(p.read_text()))


def _fresh(rec: sc.ScenarioRecord) -> sc.ScenarioRecord:
    """The record as a FIRST compute would see it — `result=None`. The ladder is
    legacy-preserving, so simulating a fresh underwrite (`scenario-create`: validate ->
    run_recipe -> write) means dropping the committed result; recomputing WITH it is the
    refresh path and must preserve the legacy regime instead."""
    return rec.model_copy(update={"result": None})


# --- the pure ladders, pinned at their exact half-open edges -----------------------------------

@pytest.mark.parametrize(("ratio", "tier"), [
    (None, "undefined"),
    (0.999, "poor"), (1.0, "below_target"),            # 1.0 belongs UP — "1.0–<1.75 below target"
    (1.7499, "below_target"), (1.75, "target_met"),    # 1.75 belongs UP — the eligibility edge
    (1.9999, "target_met"), (2.0, "preferred"),        # 2.0 belongs UP — the preferred edge
    (-0.7, "poor"),
])
def test_the_asymmetry_ladder_at_its_edges(ratio: float | None, tier: str) -> None:
    assert sc.asymmetry_tier(ratio) == tier


@pytest.mark.parametrize(("irr", "tier"), [
    (None, "undefined"),
    (0.1199, "fails"), (0.12, "minimum_met"),          # 12% belongs UP — the eligibility edge
    (0.1499, "minimum_met"), (0.15, "preferred"),      # 15% belongs UP — the preferred edge
    (-0.08, "fails"),
])
def test_the_return_ladder_at_its_edges(irr: float | None, tier: str) -> None:
    assert sc.return_tier(irr) == tier


def test_the_preferred_lines_are_the_legacy_constants() -> None:
    """The whole add-beside trick: 2.0/15% must BE `BAR`/`IRR_FLOOR`, or `pass_fail` and the
    preferred tier could disagree about the same number."""
    from vinci.dossier.midcycle import BAR
    assert sc.asymmetry_tier(BAR) == "preferred" and sc.asymmetry_tier(BAR - 1e-9) == "target_met"
    assert sc.return_tier(sc.IRR_FLOOR) == "preferred"
    assert sc.ELIGIBLE_RATIO < BAR and sc.ELIGIBLE_IRR < sc.IRR_FLOOR, (
        "the eligibility line must sit BELOW the preferred line — otherwise the ladder inverts")


# --- the live corpus, recomputed in memory ------------------------------------------------------

@pytest.mark.parametrize("path", RECORDS, ids=lambda p: p.stem)
def test_recompute_stamps_the_regime_and_keeps_the_old_booleans(path: Path) -> None:
    """PHRASING-INDEPENDENT INVARIANTS on the living corpus (TEST-LAYER RULE): a FRESH compute
    of each record's own legs stamps the regime, the tiers agree with their own pure functions,
    and — the freeze that matters — every legacy boolean reproduces the COMMITTED value, because
    the preferred lines are the old constants."""
    committed = json.loads(path.read_text())
    out = sc.run_recipe(_fresh(_load(path)))
    r = out.result
    assert r is not None and r.gate_regime == sc.GATE_REGIME
    assert r.irr_convention == sc.IRR_CONVENTION
    assert r.eligible_ratio == sc.ELIGIBLE_RATIO and r.eligible_irr == sc.ELIGIBLE_IRR
    assert r.asymmetry_tier == sc.asymmetry_tier(r.ratio)
    assert r.return_tier == sc.return_tier(r.irr)
    cres = committed.get("result") or {}
    for legacy_field in ("pass_fail", "irr_pass_fail", "gate"):
        assert getattr(r, legacy_field) == cres.get(legacy_field), (
            f"recompute moved the LEGACY boolean {legacy_field}: {cres.get(legacy_field)!r} → "
            f"{getattr(r, legacy_field)!r} — the preferred lines must be the old constants, or "
            f"sealed meanings shift under a refresh")
    # eligibility is the determinate-false AND of the two lines
    if (r.ratio is not None and r.ratio < sc.ELIGIBLE_RATIO) or \
            (r.irr is not None and r.irr < sc.ELIGIBLE_IRR):
        assert r.eligible is False
    elif r.ratio is None or r.irr is None:
        assert r.eligible is None and r.eligible_undefined
    else:
        assert r.eligible is True and r.eligible_undefined is None


def test_epam_is_the_levered_bet_refusal() -> None:
    """THE DESIGN'S ACCEPTANCE CASE, on the real record: preferred return on below-target
    asymmetry is NOT eligible. If EPAM's legs are ever superseded out of this shape, the pure-fn
    edge pins above still hold the boundary — this pin holds the *meaning*."""
    r = sc.run_recipe(_fresh(_load(ROOT / "scenarios" / "EPAM.json"))).result
    assert r is not None
    if r.return_tier == "preferred" and r.asymmetry_tier == "below_target":
        assert r.eligible is False, "high IRR must never rescue thin asymmetry"
    else:  # pragma: no cover - supersede moved the legs; the invariant test still covers it
        pytest.skip(f"EPAM's legs moved ({r.asymmetry_tier}/{r.return_tier}) — shape gone")


def test_a_failing_side_decides_without_the_other() -> None:
    """IT, on the real record: ratio 1.52 (below the line) + IRR undefined (no horizon) must be
    eligible=False — the WERN lesson from the boolean gate, applied to eligibility: a record that
    cannot pass must not sit UNDEFINED awaiting a field that could not rescue it."""
    r = sc.run_recipe(_fresh(_load(ROOT / "scenarios" / "IT.json"))).result
    assert r is not None
    if r.irr is None and r.ratio is not None and r.ratio < sc.ELIGIBLE_RATIO:
        assert r.eligible is False and r.eligible_undefined is None
    else:  # pragma: no cover - record gained a horizon or moved
        pytest.skip("IT no longer carries the below-line + undefined-IRR shape")


def test_an_undefined_side_with_nothing_failing_says_why() -> None:
    """The None-with-reason branch, on a frozen derivative of the real SMPL record: strip the
    base leg's horizon → IRR undefined while the 2.09 ratio clears — eligibility must be None
    AND carry the reason, never a silent None."""
    rec = _fresh(_load(ROOT / "scenarios" / "SMPL.json"))
    legs = dict(rec.scenarios)
    legs["base"] = legs["base"].model_copy(update={"years_to_terminal": None})
    r = sc.run_recipe(rec.model_copy(update={"scenarios": legs})).result
    assert r is not None and r.irr is None and r.ratio is not None
    assert r.ratio >= sc.ELIGIBLE_RATIO, "fixture drifted — ratio must clear the line"
    assert r.eligible is None
    assert r.eligible_undefined and "horizon" in r.eligible_undefined


def test_the_divergence_zone_eligible_but_not_preferred() -> None:
    """THE ZONE THE LADDER EXISTS FOR — and the corpus cannot exercise it (no committed record
    has an IRR inside 12–15%), which is exactly how the M4 mutation survived the first sweep:
    `irr_pass_fail` rebased onto the 12% line changed nothing observable. So the zone gets a
    frozen derivative of the real SMPL record: stretch the base horizon until the IRR lands
    inside the gap, then assert the OLD boolean FAILs (15% floor) while the NEW tier reads
    minimum_met and the record is ELIGIBLE — old and new must DISAGREE here, or one of them is
    reading the other's line."""
    import math

    rec = _fresh(_load(ROOT / "scenarios" / "SMPL.json"))
    r0 = sc.run_recipe(rec).result
    assert r0 is not None and r0.irr is not None and r0.horizon_years
    # (1+irr0)^y0 == V/S, so the horizon that lands a target rate t is y0·ln(1+irr0)/ln(1+t)
    y = r0.horizon_years * math.log(1 + r0.irr) / math.log(1.13)
    legs = dict(rec.scenarios)
    legs["base"] = legs["base"].model_copy(update={"years_to_terminal": y})
    r = sc.run_recipe(rec.model_copy(update={"scenarios": legs})).result
    assert r is not None and r.irr is not None
    assert sc.ELIGIBLE_IRR <= r.irr < sc.IRR_FLOOR, f"fixture missed the gap: irr={r.irr}"
    assert r.irr_pass_fail == "FAIL", "the legacy boolean must still test the 15% floor"
    assert r.gate == "FAIL", "the legacy conjunction must still test the 15% floor"
    assert r.return_tier == "minimum_met"
    assert r.eligible is True, "ratio ≥1.75 and IRR ≥12% — the new line must clear"


@pytest.mark.parametrize("path", RECORDS, ids=lambda p: p.stem)
def test_a_recompute_never_migrates_a_legacy_record(path: Path) -> None:
    """THE FREEZE RULING AT THE ENGINE: recomputing a committed record WITH its result present is
    the refresh path, and it must reproduce the committed result EXACTLY — no regime, no tiers,
    no convention stamp. Migration to the new regime happens on a FIRST compute
    (`scenario-create`), never as a side effect of touching a record. This is also what keeps
    the no-op refresh a no-op (`test_refresh_path`'s preservation pin)."""
    rec = _load(path)
    out = sc.run_recipe(rec)
    assert out.result is not None and out.result.gate_regime is None
    assert out.result == rec.result, (
        f"{path.stem}: recompute of a legacy record changed its result — refresh churn")


def test_the_regime_survives_its_own_recompute() -> None:
    """Idempotence on the other side: once a record carries the regime, recomputing it keeps the
    regime (it is not `legacy`), so a refresh of a NEW record cannot silently strip the ladder."""
    first = sc.run_recipe(_fresh(_load(ROOT / "scenarios" / "SMPL.json")))
    again = sc.run_recipe(first)
    assert again.result is not None and again.result.gate_regime == sc.GATE_REGIME
    assert again.result.eligible is True


# --- the sealed book stays frozen ---------------------------------------------------------------

@pytest.mark.parametrize("path", RECORDS, ids=lambda p: p.stem)
def test_committed_records_carry_no_regime_and_their_cards_gain_no_keys(path: Path) -> None:
    """THE FREEZE RULING, at both layers: the committed JSON has no ladder fields, and the
    display card built from it emits none of the new keys — absence is what lets the card render
    the 'judged under the 2:1 / 15% regime' line instead of the tiers."""
    rec = json.loads(path.read_text())
    assert "gate_regime" not in (rec.get("result") or {}), (
        f"{path.name} carries a regime stamp on disk — the sealed book was supposed to freeze")
    r = _load(path)
    assert r.result is not None and r.result.gate_regime is None
    card = _build()._scenario_card(rec, {})
    leaked = [k for k in NEW_CARD_KEYS if k in card]
    assert not leaked, f"legacy card gained ladder keys {leaked} — byte-identical rule broken"


def test_a_new_regime_card_emits_the_keys_and_the_view_renders_them() -> None:
    """The other half: a recomputed record's card carries the ladder, and every emitted key is
    named in uw-card.js — the card-key parity discipline, asserted here for the new keys since
    the committed corpus cannot exercise them yet."""
    rec = sc.run_recipe(_fresh(_load(ROOT / "scenarios" / "SMPL.json")))
    card = _build()._scenario_card(json.loads(rec.model_dump_json()), {})
    for k in ("gateRegime", "asymmetryTier", "returnTier", "eligible", "eligibleRatio",
              "eligibleIrr", "ceilingEligible", "irrConvention"):
        assert k in card, f"new-regime card is missing {k}"
    assert card["eligible"] is True and card["asymmetryTier"] == "preferred"
    js = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    unrendered = [k for k in NEW_CARD_KEYS if k not in js]
    assert not unrendered, f"uw-card.js never names {unrendered} — emitted keys must be rendered"


def test_eligible_false_reaches_the_card() -> None:
    """False is a REAL answer and must not be dropped by a truthiness emit — the three-state
    trap named in build.py's own comment, pinned on EPAM's recomputed card."""
    rec = sc.run_recipe(_fresh(_load(ROOT / "scenarios" / "EPAM.json")))
    card = _build()._scenario_card(json.loads(rec.model_dump_json()), {})
    assert card.get("gateRegime") and card.get("eligible") is False


def test_a_stamped_record_serializes_its_ladder_and_round_trips(tmp_path: Path) -> None:
    """The other half of the drop-group: a NEW-regime record must KEEP all nine keys on disk —
    including `eligible: null` beside its reason on a half-computed record — and survive a
    write→read→write cycle byte-identically. Over-dropping here would silently un-judge a record
    the next time it was touched."""
    fresh = sc.run_recipe(_fresh(_load(ROOT / "scenarios" / "SMPL.json")))
    path = sc.write_record(fresh, root=tmp_path)
    on_disk = json.loads(path.read_text())["result"]
    for k in ("gate_regime", "asymmetry_tier", "return_tier", "eligible", "irr_convention",
              "ceiling_eligible", "eligible_ratio", "eligible_irr"):
        assert k in on_disk, f"stamped record lost {k} at the serializer"
    back = sc.read_record("SMPL", root=tmp_path)
    assert back.result is not None and back.result.gate_regime == sc.GATE_REGIME
    assert sc.write_record(back, root=tmp_path).read_text() == path.read_text()


# --- the rendered surface -----------------------------------------------------------------------

def test_the_md_brief_prints_tiers_on_new_records_and_names_the_regime_on_old_ones() -> None:
    """E2E at the artifact layer (TEST-LAYER RULE): real committed record → render. The legacy
    record must SAY which regime judged it; the recomputed one must carry the eligibility line.
    Anchors only — components present, order/phrasing free."""
    legacy = _load(ROOT / "scenarios" / "SMPL.json")
    md_legacy = "\n".join(_underwrite_lines(legacy))
    assert "judged under the 2:1 / 15% regime" in md_legacy
    assert "Eligibility" not in md_legacy

    fresh = sc.run_recipe(_fresh(legacy))
    md_fresh = "\n".join(_underwrite_lines(fresh))
    assert "ELIGIBLE" in md_fresh and sc.GATE_REGIME in md_fresh
    assert "price-only" in md_fresh, "the IRR convention must reach the print reader"
    assert "judged under the 2:1 / 15% regime" not in md_fresh

def test_the_rendered_card_shows_tiers_on_new_records_and_the_regime_on_old(
    tmp_path: Path,
) -> None:
    """RENDER IT, DON'T GREP IT (the #469 standing rule): the card is executed under node for
    BOTH states. The committed legacy card must say which regime judged it and show NO tier
    pills; the new-regime card must show the tier pills, the eligibility foot, and the
    price-only IRR convention."""
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    fresh = sc.run_recipe(_fresh(_load(ROOT / "scenarios" / "SMPL.json")))
    card = _build()._scenario_card(json.loads(fresh.model_dump_json()), {})
    fresh_path = tmp_path / "fresh_card.json"
    fresh_path.write_text(json.dumps(card))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const url = pathToFileURL(path.resolve("frontend/views/shared/uw-card.js")).href;
const { uwCard } = await import(url);
const legacy = uwCard(JSON.parse(readFileSync("frontend/scenarios/SMPL.json")), {});
const fresh = uwCard(JSON.parse(readFileSync(process.argv[1])), {});
console.log(JSON.stringify({
  legacySaysRegime: legacy.includes("judged under the 2:1 / 15% regime"),
  legacyNoTierPills: !legacy.includes("TARGET MET") && !legacy.includes("ELIGIBLE"),
  legacyKeepsPassFail: legacy.includes("at underwrite"),
  freshTierPill: fresh.includes("PREFERRED"),
  freshEligible: fresh.includes("ELIGIBLE") && fresh.includes("gate regime 2026-08-21"),
  freshConvention: fresh.includes("price-only"),
  freshBothLines: fresh.includes("eligible ≥1.75 : 1") && fresh.includes("preferred ≥2 : 1"),
  freshNoLegacyLine: !fresh.includes("judged under the 2:1 / 15% regime"),
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver, str(fresh_path)],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    res = json.loads(out.stdout.strip().splitlines()[-1])
    assert all(res.values()), f"rendered-card invariants failed: {res}"


def test_supersede_writes_the_payloads_result_verbatim() -> None:
    """THE CORRECTED CLAIM, PINNED (review finding, #487). The first cut of this PR asserted in
    STATE and in the engine comment that a "superseded reissue" stamps the ladder. It does not:
    `_cmd_scenario_supersede` never calls `run_recipe`, so the incoming payload's `result` is
    written verbatim.

    PRE-EXISTING, NOT THIS LADDER'S DOING — the 2026-08-05 IRR gate has the identical exposure,
    which the committed corpus shows directly: both archived SMPL records carry
    `gate: UNDEFINED, irr: null` while the live record carries a computed gate.

    Pinned as BEHAVIOUR so the corrected sentence is machine-checked rather than merely reworded:
    if supersede ever starts recomputing, this reddens and the STATE record must be re-ruled."""
    live_rec = _load(ROOT / "scenarios" / "SMPL.json")
    assert live_rec.result is not None and live_rec.result.gate_regime is None

    incoming = live_rec.model_copy(update={"supersedes": None, "superseded_by": None})
    _archived, live = sc.supersede_record(live_rec, incoming)
    assert live.result is not None and live.result.gate_regime is None, (
        "supersede recomputed the incoming payload — the engine comment and the STATE record "
        "both say it does not; re-rule the migration path before changing this")

    # the source-of-truth for "pre-existing": the archived corpus predates the IRR gate too
    arch = ROOT / "scenarios" / "archive"
    pre_gate = [p for p in arch.glob("SMPL-*.json")
                if (json.loads(p.read_text()).get("result") or {}).get("irr") is None]
    assert pre_gate, "expected archived SMPL records with no computed IRR — the same exposure"


def test_scenario_create_is_the_migration_path() -> None:
    """The other half of the corrected claim: `scenario-create` runs the engine, so a record
    written through it carries the regime. Asserted on the CLI's own source (the command is an
    argparse handler with side effects; the claim under test is which path CALLS the engine)."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    create = src.split("def _cmd_scenario_create", 1)[1].split("\ndef _cmd_", 1)[0]
    supersede = src.split("def _cmd_scenario_supersede", 1)[1].split("\ndef _cmd_", 1)[0]
    assert "run_recipe" in create, "scenario-create no longer runs the engine — migration path gone"
    assert "run_recipe" not in supersede, (
        "supersede now runs the engine — the corrected STATE claim and the test above are stale")


def test_both_tier_label_maps_cover_the_whole_enum() -> None:
    """THE PY/JS MIRROR, pinned the way this repo pins every other one (`test_med3_tier_bucket_
    trio_agree` is the precedent). The two maps are deliberately DIFFERENT presentations — md
    prose ("below target") vs UI pill caps ("BELOW TARGET") — so their VALUES must not be
    compared. Their KEY SETS must both cover the enum: add a tier, update one side, and the other
    renders the raw enum token at a reader. Correct at the time of writing; unguarded until now
    (review, #487)."""
    import re
    import typing

    enum_vals = set(typing.get_args(sc.AsymmetryTier)) | set(typing.get_args(sc.ReturnTier))
    py_src = (ROOT / "vinci" / "dossier" / "render.py").read_text()
    py_map = re.search(r"_tl = \{(.*?)\}", py_src, re.S)
    assert py_map, "render.py no longer carries the _tl humanisation map"
    py_keys = set(re.findall(r'"(\w+)":', py_map.group(1)))

    js_src = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    js_map = re.search(r"TIER_LABEL = \{(.*?)\};", js_src, re.S)
    assert js_map, "uw-card.js no longer carries TIER_LABEL"
    js_keys = set(re.findall(r"(\w+):", js_map.group(1)))

    assert not enum_vals - py_keys, f"render.py _tl misses {sorted(enum_vals - py_keys)}"
    assert not enum_vals - js_keys, f"uw-card.js TIER_LABEL misses {sorted(enum_vals - js_keys)}"
