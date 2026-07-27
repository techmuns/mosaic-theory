"""Cross-file PARITY PINS — duplicated constants/vocab that CANNOT share one import.

Each pin binds two (or three) maintained copies of one truth so a one-sided edit reddens the
suite instead of shipping silent drift (the 2026-07-20 duplication audit: MED-3/4/5/6, LOW-9/10).
Where a single import IS possible the repo does that instead (BAR, WORKFLOW_STATES,
CONCEPT_ALIASES) — these are the py↔JS / py↔stdlib-fence leftovers, pinned with source-string
checks (the ``test_web_brief_proposal_mirror_static`` pattern).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _src(rel: str) -> str:
    return (ROOT / rel).read_text()


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("fe_build_pins", ROOT / "frontend" / "build.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_med3_tier_bucket_trio_agree() -> None:
    """firm/partial/early ↔ grade-tier bucketing is maintained in THREE places (build.py
    frozen_tiers, format.js GRADE_BUCKET, tier.js TIER_BASES) — one mapping, three languages."""
    canonical = {"firm": {"binding", "quantified"}, "partial": {"committed"},
                 "early": {"aspirational"}}
    bp = _src("frontend/build.py")
    m = re.search(r'"firm":.*?\("binding", "quantified"\)', bp, re.S)
    assert m, "build.py frozen_tiers no longer buckets binding+quantified as firm"
    assert '"partial": sum(1 for n in names if n["basis"] == "committed")' in bp
    assert '"early": sum(1 for n in names if n["basis"] == "aspirational")' in bp
    fj = _src("frontend/lib/format.js")
    gb = re.search(r"GRADE_BUCKET\s*=\s*\{([^}]*)\}", fj)
    assert gb, "format.js GRADE_BUCKET missing"
    pairs = dict(re.findall(r"(\w+)\s*:\s*\"(\w+)\"", gb.group(1)))
    js_map: dict[str, set[str]] = {}
    for basis, bucket in pairs.items():
        js_map.setdefault(bucket, set()).add(basis)
    assert {k: v for k, v in js_map.items() if k in canonical} == canonical
    tj = _src("frontend/views/themes/tier.js")
    tb = re.search(r"TIER_BASES\s*=\s*\{([^}]*)\}", tj)
    assert tb, "tier.js TIER_BASES missing"
    tiers = {k: set(re.findall(r'"(\w+)"', v)) for k, v in
             re.findall(r"(\w+):\s*\[([^\]]*)\]", tb.group(1))}
    assert tiers == canonical


def test_med4_ranker_weights_js_mirror() -> None:
    """The queue ships contributions but NOT weights, so snapshots.js hand-copies the defaults —
    pin the JS literals to RankWeights so a re-weight cannot ship a stale legend."""
    from vinci.rank.ranker import RankWeights

    w = RankWeights()
    js = _src("frontend/lib/snapshots.js")
    # the FIRST "weights:" hit is a shape comment — take the literal that carries numbers
    blocks = [b for b in re.findall(r"weights:\s*\{([^}]*)\}", js) if re.search(r"[\d.]", b)]
    assert blocks, "snapshots.js weights literal missing"
    got = {k: float(v) for k, v in re.findall(r"(\w+):\s*([\d.]+)", blocks[0])}
    assert got == {"idiosyncrasy": w.idiosyncrasy, "depth": w.depth,
                   "character": w.character, "multiple": w.multiple}


def test_med5_screen_gate_prose_matches_thresholds() -> None:
    """The G1/G3 prose in the frontend must state the backend thresholds (−30%/−85%, bottom
    quartile) — change a threshold and this reddens until the prose follows."""
    from vinci.screens.screen2 import Screen2Thresholds

    th = Screen2Thresholds()
    assert th.drawdown_max == -0.30 and th.drawdown_terminal_floor == -0.85
    assert th.multiple_floor_pctile == 0.25
    js = _src("frontend/lib/snapshots.js")
    assert "−30% to −85%" in js, "G1 prose no longer states -30%/-85%"
    assert "bottom quartile" in js, "G3 prose no longer states the bottom quartile"


def test_med6_power_floor_mirrors_backend() -> None:
    """build.py's _MIN_THEMES + _POWER_NOTE mirror vinci.themes.forward's a-priori floor
    (MIN_DRIVERS / MIN_THEME_QUARTERS) — the one build↔backend mirror test_build_themes missed."""
    from vinci.themes.forward import MIN_DRIVERS, MIN_THEME_QUARTERS

    b = _load_build()
    assert b._MIN_THEMES == MIN_DRIVERS
    assert f">={MIN_THEME_QUARTERS} theme-quarters" in b._POWER_NOTE
    assert f">={MIN_DRIVERS} drivers" in b._POWER_NOTE


def test_low9_scan_basis_keys_equal_exposure_enum() -> None:
    """build.py's _SCAN_BASIS keys are a hand-copy of the ExposureBasis enum values (stdlib
    fence) — pin them equal BY NAME so enum drift is caught here, not by a downstream KeyError."""
    from vinci.themes.schemas import ExposureBasis

    b = _load_build()
    genuine = {e.value for e in ExposureBasis} - {ExposureBasis.UNASSESSED_ERROR.value}
    # UNASSESSED_ERROR is deliberately NOT a scan-basis bucket (a scan FAILURE, not a disclosure
    # read) — the map must cover exactly the genuine bases, no more, no fewer.
    assert set(b._SCAN_BASIS) == genuine


def test_low10_reserved_slugs_match_router_normalizer() -> None:
    """The reserved first-segment set lives in build.py (_RESERVED_SLUGS, the build-time guard)
    and in app.js's parseHash legacy normalizer — pin the sets equal."""
    b = _load_build()
    app = _src("frontend/app.js")
    js_set = set()
    if re.search(r'h === "radar" \|\| h\.startsWith\("radar/"\)', app):
        js_set.add("radar")
    js_set |= set(re.findall(r'h === "themes/(\w+)"', app))
    assert js_set == set(b._RESERVED_SLUGS), (
        f"app.js normalizer handles {js_set} but build.py reserves {set(b._RESERVED_SLUGS)}")


def test_card_verdict_keys_read_by_js_are_emitted_by_build() -> None:
    """(catalyst-calendar drift, 2026-07-24) ``frontend/build.py`` camelCases every card key; the
    dossier renderer reads them back by hand. ``dated_triggers`` was read in SNAKE case and never
    emitted at all, so the WEB silently rendered a SHORTER catalyst calendar than the PDF — SMPL
    showed 2 of 3 entries and the missing row was the analyst's own falsifier. Pin the contract in
    BOTH directions: every ``card.verdict.<key>`` the JS reads must be a key build.py emits."""
    build = _src("frontend/build.py")
    # EMITTED — brace-BALANCE the verdict dict. A naive terminator (a fixed indent) silently ran
    # 200 lines past its close and swallowed three unrelated emitters, inflating the set to 32
    # names and letting foreign keys pass as "emitted" (incl. `ledger`, a top-level card SIBLING —
    # exactly the wrong-nesting drift this pin exists to catch).
    tail = build.split('"verdict": {', 1)[1]
    depth, end = 1, len(tail)
    for i, ch in enumerate(tail):
        depth += (ch == "{") - (ch == "}")
        if depth == 0:
            end = i
            break
    emitted = set(re.findall(r'"(\w+)":', tail[:end]))
    assert 5 < len(emitted) < 20, f"verdict-block extraction looks wrong: {sorted(emitted)}"

    # READ — DIRECT verdict reads across EVERY view file (the original pin scanned one file).
    # SCOPE, stated honestly: only reads that name `verdict` at the access site are traced. The
    # alias form (`const v = c.verdict || {}` … `v.key`) is NOT traced — a regex cannot tell which
    # object a re-used single-letter variable holds, and attempting it pulled in JS builtins
    # (`toFixed`, `slice`) and mechanical-layer snake fields, i.e. noise that would redden the
    # suite for no defect. Behaviour on the alias paths is covered by the e2e pin below and the
    # twin-parity tests; this pin owns the KEY-NAME contract on the direct idiom.
    read: set[str] = set()
    for path in sorted((ROOT / "frontend" / "views").rglob("*.js")):
        src = path.read_text()
        read |= set(re.findall(r"\.verdict\s*\|\|\s*\{\}\)\s*\.\s*(\w+)", src))
        read |= set(re.findall(r"\.verdict\s*\.\s*(\w+)", src))
        read |= set(re.findall(r"\.verdict\?\.\s*(\w+)", src))
    assert read, "no card.verdict.<key> reads found — the regexes went stale, not the code"

    # A read key that build.py never writes renders SILENTLY EMPTY — the catalyst-calendar bug.
    missing = read - emitted
    assert not missing, (
        f"views read card.verdict keys build.py never emits: {sorted(missing)} — "
        f"emitted={sorted(emitted)}. A read key that is never written renders SILENTLY EMPTY.")
    # and no snake_case survives on the card side (build.py camelCases every key it emits)
    snake = {k for k in read if "_" in k}
    assert not snake, f"card keys must be camelCase (build.py's convention): {sorted(snake)}"


def test_committed_web_card_carries_the_same_dated_triggers_as_its_record() -> None:
    """(e2e) The analyst's dated falsifiers must reach the WEB card, not just the md tier — the
    web calendar merges them with the machine rows exactly as ``render.py`` does. Structural count
    parity only: the trigger TEXT is analyst prose and is never pinned."""
    import json

    recs = sorted((ROOT / "scenarios").glob("*.json"))
    checked = carrying = 0
    for src in recs:
        if src.stem.startswith("_"):
            continue
        card_p = ROOT / "frontend" / "scenarios" / f"{src.stem}.json"
        if not card_p.exists():
            continue
        want = (json.loads(src.read_text()).get("verdict") or {}).get("dated_triggers") or []
        got = (json.loads(card_p.read_text()).get("verdict") or {}).get("datedTriggers") or []
        assert len(got) == len(want), (
            f"{src.stem}: record has {len(want)} dated trigger(s) but the web card carries "
            f"{len(got)} — the web calendar would render short of the PDF")
        checked += 1
        carrying += 1 if want else 0
    assert checked, "no committed underwrite cards found to check"
    # NON-VACUITY: with zero triggers anywhere every comparison is 0 == 0 and this pin guards
    # nothing while still printing green. At least one committed record must carry a trigger.
    assert carrying, (
        "no committed record carries dated_triggers — this pin is passing vacuously. Either a "
        "record lost its triggers, or the emit broke upstream; check before deleting this guard.")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
