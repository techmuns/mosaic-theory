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

    # THE OTHER DIRECTION (2026-07-27) — an ORPHAN: emitted, read by nothing. `read - emitted`
    # above cannot see one, and neither could anything else: FOUR accumulated unnoticed
    # (`statusNote`, `held`, `holdingLabel`, `baseNormalMargin`), all orphaned the day a render was
    # deleted without its emitter. A key nothing reads is not harmless — it looks live in the
    # committed card, so the next author renders it back instead of asking whether it should exist.
    #
    # SCOPE, stated honestly: this covers the `currentState` block TOO, not just `verdict` — the
    # four orphans were all in `currentState`, so a verdict-only check would have caught none of
    # them. Matched as a BARE TOKEN across the views rather than through the `.verdict.<key>`
    # idiom, so the alias reads this pin deliberately does not trace (see above) still count; that
    # looseness is what keeps it quiet enough to be worth having.
    views_src = "\n".join(
        p.read_text() for p in sorted((ROOT / "frontend" / "views").rglob("*.js")))
    cur = build[build.index("def _current_state("):]
    cur = cur[:cur.index("\n\n\ndef ")]
    card_keys = emitted | set(re.findall(r'"(\w+)":', cur)) \
        | set(re.findall(r'out\["(\w+)"\]', cur))
    orphans = sorted(k for k in card_keys if not re.search(rf"\b{re.escape(k)}\b", views_src))
    assert not orphans, (
        f"build.py emits card keys no view names: {orphans} — either render them or retire them. "
        "Machine-derived keys can just be deleted (a rebuild recomputes them); an analyst-authored "
        "field needs an operator call, then vinci.scenarios.RETIRED_VERDICT_FIELDS.")


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
    committed names; render.py had NO screening renderer whatsoever, so every committed .md — and
    the `Full dossier MD` download that serves it — omitted the level that put the name in the
    funnel. (NOT the PDF: that download scope is window.print() on the WEB page, which always drew
    the block. The first write-up said "every PDF" and was corrected after a live preview.)
    On the five names carrying no scenario card that was the
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


def test_every_assembled_field_reaches_both_dossier_renderers() -> None:
    """THE BROAD TWIN-PARITY PIN (2026-07-27) — generalises the four ``screening_context`` pins
    above from one hand-picked section to EVERY assembled field.

    ``vinci/dossier/render.py`` (markdown, and therefore the committed ``dossier.md`` and the
    "Full dossier MD" download) and ``frontend/views/shared/dossier.js`` (the web page, and
    therefore both PDF scopes, which are ``window.print()`` on it) are twins over ONE artifact:
    ``dossier.json``. #227 was the failure this guards — the screening anchor reached the web and
    was silently absent from the markdown, and nothing caught it because the only parity checks
    were the ones written *after* someone noticed. A per-section pin only ever covers the section
    whose bug has already been paid for.

    So drive it from the DATA, not from a maintained list: harvest every key the committed
    dossiers actually carry in the three shared blocks, and require that a field named by one
    renderer is named by the other. Adding a field to the assembler now reddens the suite until
    BOTH surfaces acknowledge it.

    SCOPE, stated honestly. This is a COVERAGE floor, not a semantics check: it proves a field is
    named on both sides, never that both render it correctly, identically, or in the same tier.
    Semantics stay with the per-section pins. Matching is a bare-token search, so a name that
    survives only in a comment would pass — accepted, because the alternative (parsing two
    languages' access idioms) is the brittleness that made the existing key-name pin give up on
    alias reads. A DELIBERATE one-sidedness is expressible: add the key to ``twin_exempt`` with
    the reason, which is a decision in the diff rather than a silent gap."""
    import json

    # Keys one renderer legitimately need not carry — key → the reason, so an exemption is an
    # argument made in a diff rather than a hole nobody noticed. EMPTY TODAY: every harvested
    # field currently reaches both surfaces, and that is the state worth defending.
    twin_exempt: dict[str, str] = {}

    blocks = ("mechanical", "synthesis", "anchor")
    keys: set[str] = set()
    for p in sorted((ROOT / "frontend" / "dossiers").glob("*.json")):
        if p.stem == "index":                     # a manifest of what was emitted, not a dossier
            continue
        doc = json.loads(p.read_text())
        for b in blocks:
            sub = doc.get(b)
            if isinstance(sub, dict):
                keys |= set(sub)
    assert len(keys) > 30, (
        f"harvested only {len(keys)} fields from {blocks} — the committed dossiers moved or the "
        "block names changed; a pin that harvests nothing passes for the wrong reason")

    py, js = _src("vinci/dossier/render.py"), _src("frontend/views/shared/dossier.js")
    named = lambda src, k: bool(re.search(rf"\b{re.escape(k)}\b", src))  # noqa: E731
    one_sided = sorted(
        f"{k} (md={'Y' if named(py, k) else '-'} web={'Y' if named(js, k) else '-'})"
        for k in keys - set(twin_exempt) if named(py, k) != named(js, k))
    assert not one_sided, (
        "assembled fields that reach ONE dossier renderer and not the other: "
        f"{one_sided}. The markdown twin (and the 'Full dossier MD' download) and the web page "
        "(and both PDF scopes) must both acknowledge every assembled field — that asymmetry is "
        "#227. Render it on the missing side, or record the exemption in twin_exempt.")


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
    """The reference tables are ALIGNED but stay CONTENT-SIZED — two house rules, both easy to
    break in the same well-meaning edit.

    The card must not go back to the flat ``<ul>``: values then sit at as many different x as there
    are rows (24 of them on AORT), which is the whole reason the value column is right-aligned.

    And it must not be stretched to the container either. That WAS tried in this build and reverted
    on operator challenge: ``.vs-table`` stretches because it is a MULTI-column comparison whose
    number columns must group right against one wide label, but a reference list is TWO columns, so
    100% only opens a gulf — measured on AORT, 603–785px of empty space between a label and its own
    value, against 149–243px content-sized, with no row rules to carry the eye across it. The
    raggedness that motivated the override (32%/34%/97% in one card) was SMPL alone, caused by a
    380-char malformed label; clean records sit at 353–497px. CSS is not the place to compensate
    for one bad data row.

    Also pins what must NOT be added: row dividers. "rows rule-free, tighter rhythm; the section
    head carries the rule" is house policy in styles.css, applied to `.fact`, `.brief-snap-t` and
    `table.data tbody td` alike.
    """
    js = _src("frontend/views/shared/dossier.js")
    body = js.split("function assumptionMethodology(card) {")[1].split("\n}")[0]
    assert 'class="data ref-table"' in body, "the methodology tables lost the .ref-table class"
    assert "kv-list" not in body, "the methodology card reverted to the unaligned flat list"
    assert 'class="num mono"' in body, "the value cell lost its right-aligned numeric class"

    css = " ".join(_src("frontend/assets/styles.css").split())
    assert "table.data { width: auto; max-width: 100%;" in css, (
        "the K2 content-sized default for data tables is gone — .ref-table inherits it")
    for stretched in ("table.data.ref-table { width: 100%; }",
                      ".ref-table td:first-child { width: 100%; }"):
        assert stretched not in css, (
            f"{stretched!r} is back — stretching a TWO-column reference list to the container "
            "opens a 600px+ gulf between each label and its value; this was tried and reverted")
    assert "table.data tbody td { border-bottom: none; }" in css, (
        "the rule-free row policy was dropped — this card was designed against it")


def test_masthead_median_selects_by_role_never_by_label_prose() -> None:
    """(schema 1.3) The uw-card masthead's "vs N× median" comparator is chosen by the ROLE field.

    The regex it replaces — ``find(/median/i)`` over labels — picked whichever label mentioned
    "median" FIRST: on MVST that was the PEER median (14.5x, a set the analyst called
    heterogeneous) while the own-history median sat two rows down labelled "unusable". Which
    comparator the masthead showed was decided by ARRAY ORDER — the display-string-parsing bug
    class, live in production.

    Three layers, mutation-tested: the source no longer contains a label regex; a FROZEN fixture
    (the MVST shape) proves the behaviour — peer_median first + own median excluded ⇒ NO sub-line
    (honest absence, never a guessed comparator); role-tagged clean median ⇒ selected.
    """
    import json
    import shutil
    import subprocess

    src = _src("frontend/views/shared/uw-card.js")
    assert "/median/i" not in src, (
        "uw-card matches labels for 'median' again — the comparator must come from the ROLE "
        "field; the regex showed the PEER median on MVST by array order")
    assert 'p.role === "median" && !p.excluded' in src, (
        "the masthead's median selection lost its role+excluded predicate")

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    # FROZEN fixture, not the living MVST mirror: the record's tags are analyst data and may
    # legitimately change on a re-underwrite; the SELECTION RULE may not.
    mvst_shape = {"assumptions": [{"axis": "multiple", "method": "m", "references": [
        {"label": "peer median, heterogeneous set", "value": 14.5, "unit": "x", "source": "s",
         "role": "peer_median"},
        {"label": "this company's trailing median", "value": 19.3, "unit": "x", "source": "s",
         "role": "median", "excluded": True, "excludedReason": "six closes over 1.3 years"},
    ]}]}
    clean_shape = {"assumptions": [{"axis": "multiple", "method": "m", "references": [
        {"label": "peer median, nine names", "value": 14.5, "unit": "x", "source": "s",
         "role": "peer_median"},
        {"label": "this company's trailing median", "value": 17.85, "unit": "x", "source": "s",
         "role": "median"},
    ]}]}
    legacy_shape = {"assumptions": [{"axis": "multiple", "method": "m", "references": [
        {"label": "own-history median (base set below it)", "value": 17.85, "unit": "x",
         "source": "s"},
    ]}]}
    driver = """
import { readFileSync } from "node:fs";
const src = readFileSync("frontend/views/shared/uw-card.js", "utf8");
const body = src.split("function methodCell(c) {")[1].split("\\n}")[0];
// stub the helpers methodCell closes over; statCell returns its sub text so we can read it
const statCell = (t, h, sub) => sub;
const leg = () => null; const num = () => null; const oneDp = (v, u) => `${v.toFixed(1)}${u}`;
const headlineState = () => "pending"; const escapeHtml = (s) => String(s);
const DASH = "—";
const methodCell = new Function(
  "statCell", "leg", "num", "oneDp", "headlineState", "escapeHtml", "DASH", "c",
  body).bind(null, statCell, leg, num, oneDp, headlineState, escapeHtml, DASH);
console.log(JSON.stringify(__CASES__.map((c) => methodCell(c))));
""".replace("__CASES__", json.dumps([mvst_shape, clean_shape, legacy_shape]))
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    mvst_sub, clean_sub, legacy_sub = json.loads(out.stdout)
    assert "median" not in mvst_sub, (
        f"excluded own median + peer_median present ⇒ NO comparator, got {mvst_sub!r} — a "
        "peer median must never masquerade as THE median")
    assert "vs 17.9× median" in clean_sub or "vs 17.8× median" in clean_sub, (
        f"a clean role-tagged median must be selected, got {clean_sub!r}")
    assert "median" not in legacy_sub, (
        f"an untagged legacy record shows NO sub-line (honest) — got {legacy_sub!r}")


def test_13_fields_reach_both_twins_and_the_mirrors_e2e() -> None:
    """E2E, phrasing-independent, over every committed record: whatever a record declares in its
    1.3 fields is VISIBLE on both rendered surfaces and rides the mirrors — an excluded reference
    states its exclusion wherever the row renders, a leg tag renders as a chip/suffix, and an
    axis note renders dated. Conditional invariants (IF the record carries X…), so a legitimate
    re-underwrite that changes the tags cannot redden this.

    (31b) The conditional shape that keeps it robust is also what lets it go hollow: every
    assertion sits behind "IF the record carries X", so a corpus with no 1.3 fields at all passes
    without comparing anything. RELATIONAL floor on the corpus (every record was opened) plus a
    loud red if the 1.3 fields have vanished fleet-wide — the second is not a decaying number but
    a statement that this pin currently has a subject."""
    import json

    records = [p for p in sorted((ROOT / "scenarios").glob("*.json"))
               if not p.stem.startswith("_")]
    opened, compared = 0, 0
    for p in records:
        opened += 1
        rec = json.loads(p.read_text())
        md_p = ROOT / "data" / "dossiers" / p.stem / "dossier.md"
        md = md_p.read_text() if md_p.exists() else None
        mirror = json.loads((ROOT / "frontend" / "scenarios" / f"{p.stem}.json").read_text())
        m_axes = {a["axis"]: a for a in mirror.get("assumptions") or []}
        for axis, a in (rec.get("assumptions") or {}).items():
            for i, r in enumerate(a.get("references") or []):
                mr = m_axes[axis]["references"][i]
                compared += 1
                assert mr.get("role") == r.get("role"), f"{p.stem}/{axis}[{i}]: role lost"
                assert mr.get("leg") == r.get("leg"), f"{p.stem}/{axis}[{i}]: leg lost"
                if r.get("excluded"):
                    assert mr.get("excluded") and mr.get("excludedReason"), (
                        f"{p.stem}/{axis}[{i}]: exclusion lost from the mirror")
                    if md:
                        assert "excluded:" in md, (
                            f"{p.stem}: an excluded reference renders undimmed/unstated in md")
            for n in a.get("notes") or []:
                assert any(mn["text"] == n["text"] for mn in m_axes[axis].get("notes") or []), (
                    f"{p.stem}/{axis}: note lost from the mirror")
                if md:
                    assert n["date"] in md, f"{p.stem}/{axis}: note date absent from md"
    assert opened == len(records) and opened, (
        f"opened {opened} of {len(records)} committed records — a twin-parity sweep over an "
        "empty corpus compares nothing")
    assert compared, (
        "not one committed reference was compared against its mirror — every assertion here is "
        "conditional on a record CARRYING 1.3 fields, so a fleet that has lost them entirely "
        "passes this pin while proving nothing. This red means the pin has no subject, not that "
        "the invariant is wrong")


def test_brief_core_rows_py_js_parity() -> None:
    """The brief's static row set is maintained in TWO languages and must not drift.

    Found in review of the P1 brief fix: the set existed in THREE places — render.py, assemble.py
    and dossier.js. Two were python, so the repo's own rule applied (where a single import IS
    possible, import) and `assemble` now reads `render.BRIEF_CORE_ROWS`. The JS copy cannot import
    it, so it is pinned here — the py↔JS leftover this module exists for.

    Drift matters more than usual now: the guard's satisfying set is CORE ∪ MATERIAL, so a label
    silently missing from one side narrows what counts as "the reader met it" on that surface.
    """
    from vinci.dossier.render import BRIEF_CORE_ROWS

    js = _src("frontend/views/shared/dossier.js")
    m = re.search(r"const want = \[(.*?)\];", js, re.S)
    assert m, "dossier.js brief row whitelist not found"
    js_set = set(re.findall(r'"([^"]+)"', m.group(1)))
    assert js_set == set(BRIEF_CORE_ROWS), (
        "brief core rows diverge between render.py and dossier.js — one surface would show a "
        f"different snapshot: py-only={sorted(set(BRIEF_CORE_ROWS) - js_set)} "
        f"js-only={sorted(js_set - set(BRIEF_CORE_ROWS))}")

    # and BOTH twins must still admit the dynamic material rows on top of the static set
    assert "getattr(r, \"material\", False)" in _src("vinci/dossier/render.py"), (
        "the md brief lost its material-row promotion — an appendix-only charge again")
    assert "r.material === true" in js, (
        "the web brief lost its material-row promotion — an appendix-only charge again")


def test_extraction_version_changelog_py_js_parity() -> None:
    """(26a) The extraction-version changelog is maintained in TWO languages and must not drift.

    The stamp answers "are these two dossiers comparable?". If the python bumps a vintage and the JS
    copy does not, the web page describes an artifact with the WRONG set of changes while the
    markdown twin describes it correctly — a disagreement about provenance, which is worse than
    either surface simply omitting it. The two copies cannot share an import (py↔JS), which is the
    leftover this module exists for.

    Binds BOTH columns: the version identifiers AND what each one names. A version pair that agreed
    on the id but disagreed on the description would still tell a reader two different stories."""
    from vinci.dossier.extraction_version import EXTRACTION_VERSIONS

    js = _src("frontend/views/shared/dossier.js")
    m = re.search(r"const EXTRACTION_VERSIONS = \[(.*?)\n\];", js, re.S)
    assert m, "dossier.js EXTRACTION_VERSIONS table not found — the web twin lost its copy"

    # rows are ["<version>", "<names>"] with the names possibly split across a JS "+" concat
    rows = re.findall(r'\["([^"]+)",\s*((?:"[^"]*"\s*\+?\s*)+)\]', m.group(1))
    js_table = [(v, re.sub(r'"\s*\+\s*"', "", names.strip()).strip('"')) for v, names in rows]

    assert js_table == list(EXTRACTION_VERSIONS), (
        "the extraction-version changelog diverges between vinci/dossier/extraction_version.py and "
        f"dossier.js — the two surfaces would describe the same artifact differently.\n"
        f"  py={list(EXTRACTION_VERSIONS)}\n  js={js_table}")

    # and BOTH twins must render the stamp where the assembly date is stated, not only in the audit
    # tier — a stamp confined to Record & reproduce is 17b's failure repeated (the record complete,
    # the harm intact), so the header site is pinned on each side.
    assert "· extraction {stamp_label(d.extraction_version)}_" in _src("vinci/dossier/render.py"), (
        "the md header lost the extraction stamp — it must ride the document date")
    web_header = '· extraction <span class="mono">${escapeHtml(stampLabel(d.extraction_version))}'
    assert web_header in js, (
        "the web header lost the extraction stamp — it must ride the document date")

def test_panel_date_exclusions_py_js_parity() -> None:
    """(item 1) The panel-date harvester exists in BOTH languages and its EXCLUSION LIST is the
    load-bearing part — the distinction between a date that TRAVELS WITH A VALUE and one that
    describes an ARRIVAL. Get it wrong and SMPL reads 115 days stale instead of 3, the tightest in
    the fleet, and the whole staleness ranking inverts. That error was made twice while measuring
    this, so a one-sided edit to either list must redden rather than quietly re-invert it."""
    import re as _re

    from vinci.dossier.freshness import _NOT_A_PANEL

    py_terms = set(_NOT_A_PANEL.pattern.split("|"))
    js = _src("frontend/views/shared/dossier.js")
    m = _re.search(r"const _NOT_A_PANEL = /([^/]+)/", js)
    assert m, "dossier.js lost its _NOT_A_PANEL exclusion list"
    js_terms = set(m.group(1).split("|"))

    assert py_terms == js_terms, (
        "panel-date EXCLUSIONS diverge between freshness.py and dossier.js — one twin would count "
        f"a value-borne date as a panel arrival.\n  py-only={sorted(py_terms - js_terms)}\n"
        f"  js-only={sorted(js_terms - py_terms)}")
    assert {"own_history", "stock_performance"} <= py_terms, (
        "the two exclusions that inverted the ranking are gone from BOTH sides, so this pin would "
        "pass while the defect returned")



def test_revision_broker_day_order_is_identical_on_both_twins() -> None:
    """THE CAP MAKES ORDER A CONTRACT. `_GROUP_CAP` truncates the revision log to six broker-days,
    so whichever six each renderer picks IS the published fact — and the two picked differently.

    `render._grouped_events_lines` sorted by DATE alone (ties kept insertion order); dossier.js
    reverse-sorted the composite "date|broker" string (ties broke by broker DESCENDING). AORT's md
    and web disagreed on rows 5-6. Fixing that to "date DESC, broker ASC" then exposed a second,
    finer split: JS `localeCompare` collates case-insensitively while python `sorted` orders by code
    point, so "Morningstar Inc." vs "broker undisclosed" flipped IT's sixth row.

    Pin the ORDERING RULE on both sides — the ordering is not incidental, it selects what prints."""
    py = _src("vinci/dossier/render.py")
    seg = py[py.index("def _grouped_events_lines"):]
    seg = seg[:seg.index("\ndef ")]
    assert "sorted(sorted(groups, key=lambda k: k[1]), key=lambda k: k[0], reverse=True)" in seg, (
        "the md must sort date DESC then broker ASC — a date-only sort leaves ties to "
        "insertion order")
    js = _src("frontend/views/shared/dossier.js")
    jseg = js[js.index("function eventGroups"):]
    jseg = jseg[:jseg.index("\nfunction ")]
    # STRIP COMMENTS FIRST. The note above the comparator names `localeCompare` as the thing not to
    # use, and scanning raw source flagged that explanation as the violation — the same way the CSS
    # suppression pin flagged its own comment. Assert against CODE, never against prose about code.
    jseg = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", jseg, flags=re.S))
    assert "localeCompare" not in jseg, (
        "localeCompare collates case-insensitively and cannot agree with python's code-point sort")
    assert "cmp(db, da) || cmp(ba, bb)" in jseg, "date DESC then broker ASC, by code point"


def test_print_chunk_probe_mirrors_the_print_rules_it_cannot_see() -> None:
    """(P7) Wide tables split into continued blocks at print time, and the split is decided by an
    OFF-SCREEN PROBE — because at `beforeprint` the page is still laid out for screen, and column
    widths differ per table (a quarterly cell is narrower than an annual one), so a fixed column
    count would be wrong for one of them.

    THE COUPLING THIS GUARDS: a media rule cannot be read on screen, so the probe HAND-COPIES the
    print declarations that change a table's MINIMUM width. Copying only the padding and not the
    wrap rules read the peer grid at 981px min-content when it prints at 848 — and split a table
    that fits perfectly well. Every rule the probe replicates must still exist in @media print;
    if one is edited there and not here, the probe silently mis-measures again."""
    js = _src("frontend/views/shared/dossier.js")
    seg = js[js.index("function _colWidthsAtPrintScale"):]
    seg = seg[:seg.index("\nfunction splitWideTablesForPrint")]
    css = _src("frontend/assets/styles.css")
    block = css[css.index("\n@media print {"):]

    # (1) cell padding — probe and print block must agree on the value
    assert 'padding = "4px 9px"' in seg
    assert "table.data td, table.data th { padding: 4px 9px; }" in block
    # (2) the row-label wrap — without it a long label holds the table wide in the probe only
    assert 'whiteSpace = "normal"' in seg and 'maxWidth = "280px"' in seg
    assert "table.data td.row-label { white-space: normal; max-width: 280px; }" in block
    # (3) P6's full-measure rule for wide grids
    assert 'style.width = "100%"' in seg
    assert "table.data:has(thead th:nth-child(5))" in block
    # the measure itself, and that the split is PRINT-ONLY and reversible
    assert "_PRINT_MEASURE = 880" in js
    assert 'addEventListener("beforeprint", splitWideTablesForPrint)' in js
    assert 'addEventListener("afterprint", unsplitWideTablesAfterPrint)' in js
    # a suppressed bulk tier must never be measured or split (P5)
    assert 'closest(".ds-bulk")' in js
