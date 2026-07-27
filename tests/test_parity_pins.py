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


def test_ref_value_py_js_parity() -> None:
    """(2026-07-27) `_ref_value` (render.py) and `refValue` (dossier.js) format the SAME
    source-bound reference point on two surfaces, so they must agree CHARACTER FOR CHARACTER.

    They did not. The first cut used py `,.6g` against a bare js `toLocaleString`, and three
    COMMITTED references already rendered differently in the PDF and on the web ($1,416.21M vs
    $1,416.208M). Two traps the fix must keep closed, both previously reachable: `g` flips to
    SCIENTIFIC at 1e6 ("$1.23457e+06M" in a PDF), and toLocaleString's default 3-fraction-digit
    cap silently rounds a non-zero source-bound value to "$0M" — a fabricated number.

    Pins EVERY reference value in EVERY committed record, plus the pathological set."""
    import json
    import shutil
    import subprocess

    from vinci.dossier.render import _ref_value

    cases: list[tuple[float, str]] = [
        (1e6, "$M"), (1234567.89, "$M"), (123456.7, "$M"),   # scientific-notation trap
        (0.000123, "$M"), (1e-7, "$M"),                       # round-to-zero trap
        (0.0, "$M"), (-45.5, "$M"), (12.3456789, "%"), (6.11, "x"), (100.0, "%"),
    ]
    for rec in sorted((ROOT / "scenarios").glob("*.json")):
        if rec.stem.startswith("_"):
            continue
        for axis in (json.loads(rec.read_text()).get("assumptions") or {}).values():
            cases += [(r["value"], r["unit"]) for r in (axis.get("references") or [])]
    assert len(cases) > 50, f"expected the committed reference corpus, got {len(cases)}"

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const mod = await import("__URI__");
// refValue is module-private; reach it through the rendered surface instead by re-declaring the
// same source. Keeping ONE copy honest is the point of this pin, so read it from the file.
import { readFileSync } from "node:fs";
const src = readFileSync("frontend/views/shared/dossier.js", "utf8");
const body = src.split("function refValue(value, unit) {")[1].split("\\n}")[0];
const refValue = new Function("value", "unit", body);
console.log(JSON.stringify(__CASES__.map(([v, u]) => refValue(v, u))));
""".replace("__URI__", dj).replace("__CASES__", json.dumps([[v, u] for v, u in cases]))
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    py = [_ref_value(v, u) for v, u in cases]
    bad = [(v, u, p, j) for (v, u), p, j in zip(cases, py, js, strict=True) if p != j]
    assert not bad, ("py/js reference formatting diverges — the SAME number renders differently in "
                     f"the PDF and on the web: {bad[:6]}")
    # and the two traps stay closed
    assert "e+" not in "".join(py), f"scientific notation reached a rendered value: {py}"
    assert _ref_value(0.000123, "$M") != "$0M", "a non-zero reference rounded away to zero"


def test_screening_context_py_js_parity() -> None:
    """(2026-07-27) The screening ANCHOR renders on BOTH surfaces and must carry the same numbers.

    It did not render on one of them at all. `anchorInner` (dossier.js) drew the block for all 11
    committed names; the print twin had NO screening renderer whatsoever, so every PDF omitted the
    level that put the name in the funnel. On the five names carrying no scenario card that was the
    ONLY valuation level in the document — `Valuation — first cut` is relative-only by the
    ImpliedValuation fence — and on the two INAPPLICABLE anchors it also swallowed the diagnostic
    saying why no screen value exists.

    Pins the VALUES (deterministic — computed in anchor.py, never LLM-composed) rather than the
    phrasing, on every committed anchor: whatever the web shows for margin/multiple/base/confidence,
    the markdown shows too.
    """
    import json
    import shutil
    import subprocess

    from vinci.dossier.anchor import Anchor
    from vinci.dossier.render import _screening_context_lines

    anchors: list[tuple[str, dict[str, Any]]] = []
    for p in sorted((ROOT / "data" / "dossiers").iterdir()):
        f = p / "dossier.json"
        if not f.exists():
            continue
        a = json.loads(f.read_text()).get("anchor")
        if a:
            anchors.append((p.name, a))
    assert len(anchors) >= 10, f"expected the committed anchor corpus, got {len(anchors)}"

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = """
import { readFileSync } from "node:fs";
import { escapeHtml } from "./frontend/lib/format.js";
const src = readFileSync("frontend/views/shared/dossier.js", "utf8");
const body = src.split("function anchorInner(a) {")[1].split("\\n}")[0];
const anchorInner = new Function("escapeHtml", "a", body).bind(null, escapeHtml);
// decode the entities escapeHtml emits BEFORE comparing — the py twin holds the RAW text, and a
// half-decoded compare is how this pin reports a false divergence on an apostrophe (it did:
// escapeHtml writes &#39; where python's html.escape writes &#x27;, the same mismatch that
// reddened the cover pin on correct output).
const ENT = {"&#39;": "'", "&#x27;": "'", "&quot;": '"', "&lt;": "<", "&gt;": ">", "&amp;": "&"};
const strip = (h) => h.replace(/<[^>]*>/g, " ")
  .replace(/&(#39|#x27|quot|lt|gt|amp);/g, (m) => ENT[m]).replace(/\\s+/g, " ");
console.log(JSON.stringify(__A__.map((a) => strip(anchorInner(a)))));
""".replace("__A__", json.dumps([a for _, a in anchors]))
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    web = json.loads(out.stdout)

    missing: list[str] = []
    for (tkr, raw), web_text in zip(anchors, web, strict=True):
        md = "\n".join(_screening_context_lines(Anchor.model_validate(raw)))
        assert md, f"{tkr}: the print twin rendered NO screening block for a committed anchor"
        mg, mu = raw.get("margin"), raw.get("multiple")
        want: list[str] = []
        if mg and mg.get("value") is not None:
            want.append(f"{mg['value'] * 100:.1f}%")
        if mu and mu.get("value") is not None:
            want.append(f"{mu['value']:.1f}x")
        if raw.get("anchor_base_value_per_share") is not None:
            want.append(f"${raw['anchor_base_value_per_share']:,.2f}")
        if raw.get("reason"):
            want.append(str(raw["reason"]))
        for v in want:
            if v not in md:
                missing.append(f"{tkr}: {v!r} absent from the MARKDOWN block")
            if v not in web_text:
                missing.append(f"{tkr}: {v!r} absent from the WEB block")
    assert not missing, "screening-context twins disagree on committed values: " + "; ".join(
        missing[:8])


def test_screening_context_never_differences_the_anchor_against_spot() -> None:
    """FENCE. The screen value is a LEVEL, labelled spot-independent. Differencing it against the
    price is precisely the machine-implied upside `ImpliedValuation` forbids ("no computed %,
    delta, discount, or upside"), and the anchor is the easiest place to reintroduce it — the base
    value and the spot both sit in scope at the render site.

    Negative pin: the block must not emit a signed percentage (the `vs spot` shape the SCENARIO
    table legitimately carries, which this section must never grow).
    """
    import json

    from vinci.dossier.anchor import Anchor
    from vinci.dossier.render import _screening_context_lines

    src = _src("vinci/dossier/render.py")
    body = src.split("def _screening_context_lines(")[1].split("\ndef ")[0]
    # scan the CODE, not the prose: the docstring states the fence, so it necessarily contains
    # every word the fence forbids. "spot-independent" is the legitimate BASIS LABEL and is the
    # one surviving mention — anything else means the price came into scope.
    code = body.split('"""', 2)[-1].replace("spot-independent", "")
    for bad in ("spot", "upside", "discount", "price"):
        assert bad not in code, (
            f"the screening renderer references {bad!r} — it must render the anchor as a LEVEL, "
            "never differenced against the price (ImpliedValuation fence)")

    rendered: list[tuple[str, float | None, str]] = []
    for p in sorted((ROOT / "data" / "dossiers").iterdir()):
        f = p / "dossier.json"
        if not f.exists():
            continue
        a = json.loads(f.read_text()).get("anchor")
        if a:
            rendered.append((p.name, a.get("anchor_base_value_per_share"),
                             "\n".join(_screening_context_lines(Anchor.model_validate(a)))))
    assert rendered, "no committed anchors to check the fence against"
    assert any(b is not None for _, b, _ in rendered), "no anchor carries a base value to fence"
    for tkr, base, md in rendered:
        assert not re.search(r"[+-]\d+(\.\d+)?%", md), (
            f"{tkr}: a signed percentage reached the screening block — implied upside: {md[:200]}")
        # the label rides the base-value ROW, so it exists exactly where a base value does — an
        # INAPPLICABLE anchor prints no such row and must not claim spot-independence of nothing.
        assert ("spot-independent" in md) is (base is not None), (
            f"{tkr}: spot-independence label and the base value must appear together")


def test_screening_context_reaches_every_committed_dossier_e2e() -> None:
    """E2E on the RENDERED artifact — the layer the failure was observed at.

    The unit pins above prove the helper works; they would ALL have stayed green while the section
    never reached a single committed dossier.md, because nothing wired the helper into the render.
    That is exactly how the gap shipped: `anchorInner` existed on the web for months and the print
    twin simply never called anything.

    Renders LIVE from committed JSON and compares to disk (the #221 lesson — an md pin that reads
    dossier.md alone passes happily while the RENDERER has drifted away from it).
    """
    import pathlib

    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier
    from vinci.scenarios import read_record

    seen = 0
    for d in sorted((ROOT / "data" / "dossiers").iterdir()):
        j = d / "dossier.json"
        if not j.exists():
            continue
        doc = Dossier.model_validate_json(j.read_text())
        if doc.anchor is None:
            continue
        seen += 1
        try:
            card = read_record(doc.ticker)
        except FileNotFoundError:
            card = None
        live = render_markdown(doc, card=card)
        disk = pathlib.Path(d / "dossier.md").read_text()
        assert live == disk, (
            f"{doc.ticker}: committed dossier.md has DRIFTED from the renderer — re-render the "
            "artifacts (a render change without an artifact pass leaves the record stale)")
        assert "### Screening context — how this name surfaced" in disk, (
            f"{doc.ticker}: the screening anchor renders on the web but NOT in the committed "
            "markdown — the print reader never sees the level that surfaced this name")
        # and the absence of an underwrite is STATED, never silently a shorter document
        if card is None:
            assert "_no scenario record for this name_" in disk, (
                f"{doc.ticker}: no scenario card, and the markdown does not say so")
    assert seen >= 10, f"expected the committed anchor corpus end-to-end, got {seen}"


def test_screening_context_prose_is_the_same_on_both_surfaces() -> None:
    """The two HAND-COPIED strings in the screening block, bound to their JS originals.

    `_screening_context_lines` cannot import from dossier.js, so the METHOD gloss and the
    attention-filter SUBTITLE exist twice. Both are load-bearing prose, not decoration: the gloss
    says what the number IS ("mid-cycle margin × the median multiple of its own history" rather
    than the raw `R1_midcycle_margin_evebitda` slug), and the subtitle is the DISCLAIMER — it is
    the sentence telling the reader a cheap screen still has to survive a full underwrite.

    Found by mutation during review of the PR that introduced them: editing BOTH strings in the JS
    left the whole suite green, so the PDF and the web could have described the same number two
    different ways — and the value-parity pin above would not have noticed, because it compares
    the NUMBERS and not the words framing them. That is the exact duplication class this module
    exists for (see its docstring).
    """
    from vinci.dossier.render import _SCREEN_METHOD_R1, _SCREEN_SUBTITLE

    js = _src("frontend/views/shared/dossier.js")
    for const, name in ((_SCREEN_METHOD_R1, "_SCREEN_METHOD_R1"),
                        (_SCREEN_SUBTITLE, "_SCREEN_SUBTITLE")):
        # the JS source wraps across lines — compare on collapsed whitespace, which is what the
        # rendered surface shows anyway (HTML collapses runs of space; markdown re-flows).
        assert " ".join(const.split()) in " ".join(js.split()), (
            f"{name} no longer matches its dossier.js original — the print twin and the web would "
            "describe the SAME screening number in different words")


def test_methodology_references_cite_by_endnote_on_both_twins() -> None:
    """"How these numbers were set" cites via ENDNOTES, like every other MAIN-BODY block.

    frontend/lib/cites.js states two sanctioned modes and says the choice is not stylistic:
    ``withEndnotes()`` for the main body, ``auditCitesInline()`` for on-demand <details> audit
    blocks. This card is main body on both surfaces (a plain card, not a <details>), and it used
    NEITHER — it hardcoded the source string into the markup, so no pass ever saw it.

    That is a RECURRENCE. cites.js exists because uw-card.js did exactly this; its module docstring
    names the defect. uw-card was fixed, then #222 shipped a new card that reintroduced it.

    Pins the CONTRACT, not the phrasing: the renderer must not paste a source string into the
    reference row on either twin, and every committed record's sources must still be reachable in
    the rendered markdown (moved to the endnote list, never dropped).
    """
    import json

    js = _src("frontend/views/shared/dossier.js")
    body = js.split("function assumptionMethodology(card) {")[1].split("\n}")[0]
    assert "citeMark(r.source)" in body, (
        "the web methodology card no longer emits a citeMark — a main-body cite must be an endnote")
    assert "escapeHtml(r.source)" not in body, (
        "the web methodology card pastes the source string inline again (the uw-card defect)")

    py = _src("vinci/dossier/render.py")
    pybody = py.split("def _assumption_methodology_lines(")[1].split("\ndef ")[0]
    assert "_cite(r.source)" in pybody, "the markdown twin no longer emits an endnote cite"
    assert "_md_cell(r.source)" not in pybody, (
        "the markdown twin renders the source as a table column again")

    # E2E — no source string may be LOST by the move; each must still resolve in the rendered md.
    checked = 0
    for p in sorted((ROOT / "scenarios").glob("*.json")):
        if p.stem.startswith("_"):
            continue
        md_p = ROOT / "data" / "dossiers" / p.stem / "dossier.md"
        if not md_p.exists():
            continue
        md = md_p.read_text()
        for a in (json.loads(p.read_text()).get("assumptions") or {}).values():
            for r in (a.get("references") or []):
                checked += 1
                assert r["source"] in md, (
                    f"{p.stem}: a reference source vanished from the rendered dossier — moving "
                    f"a cite to the endnote list must never drop it: {r['source'][:60]!r}")
    assert checked >= 60, f"expected the committed reference corpus end-to-end, got {checked}"


def test_methodology_reference_tables_share_one_grid() -> None:
    """Every axis of the card renders its own table; they must share ONE width.

    Content-sized (the K2 default, ``table.data { width: auto }``) they came out 32% / 34% / 97%
    of the card in a SINGLE dossier, so the value column began at a different x on every axis and
    the numbers formed no readable column — the whole point of right-aligning them. `.ref-table`
    applies the same slack-absorbing pair `.vs-table` already uses for the same reason.

    Also pins what must NOT be added: row dividers. "rows rule-free, tighter rhythm; the section
    head carries the rule" is house policy in styles.css, applied to `.fact`, `.brief-snap-t` and
    `table.data tbody td` alike — alignment carries this table, not hairlines.
    """
    js = _src("frontend/views/shared/dossier.js")
    body = js.split("function assumptionMethodology(card) {")[1].split("\n}")[0]
    assert 'class="data ref-table"' in body, "the methodology tables lost the .ref-table class"
    assert "kv-list" not in body, "the methodology card reverted to the unaligned flat list"

    css = " ".join(_src("frontend/assets/styles.css").split())
    assert "table.data.ref-table { width: 100%; }" in css, (
        ".ref-table has no width rule — the per-axis tables will shrink-wrap to different widths")
    assert ".ref-table td:first-child { width: 100%; }" in css, (
        "the label column must absorb the slack so the value columns align on one right edge")
    assert "table.data tbody td { border-bottom: none; }" in css, (
        "the rule-free row policy was dropped — this card was designed against it")
