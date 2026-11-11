"""THE DOSSIER SHELF'S TAGS — a logged verdict outranks the machine's lean; the lean stays neutral.

`frontend/views/shared/dossier.js` tags each card on the shelf: `cardTag` prefers the verdict OF
RECORD (`verdictTag`, the only coloured tag) and falls back to the machine's lean (`leanTag`,
neutral ink, through the ONE shared lean parser). `frontend/build.py` ships the index's `labels`
and `reads` that those tags read. RUNBOOKS §f lists the Verdicts as sacred: without these pins an
undecided name can wear a BUY colour on the shelf with the suite green.

MOVED VERBATIM from `tests/test_build_themes.py` (last held by `05b2529b`) when the theme viewer's
build pins retired with `vinci.themes` (#908, round 2): they pinned the dossier shelf, not themes.
"""
from __future__ import annotations

import json

from vinci.dossier.verdict import split_lean


def test_lean_tag_is_label_only_and_never_directional() -> None:
    """ANTI-ANCHORING pin on the index cards' lean tag (guard behavior, not phrasing).

    The lean maps 1:1 onto the machine proposal (strongly-bearish -> AVOID), so the glance tag is
    one deterministic hop from a verdict. It must therefore render the LABEL through the ONE shared
    parser and stay visually NEUTRAL — no .pill buy/avoid vocabulary, no danger/live tint. Colour
    here would turn the dossier shelf into a recommendation screen, which is exactly the anchoring
    the sealed proposal exists to prevent."""
    import re
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "frontend" / "views" / "shared" / "dossier.js"
          ).read_text()
    m = re.search(r"function leanTag\(eb(?:, voided = null)?\) \{(.*?)\n\}", js, re.S)
    assert m, "leanTag() is gone — the index cards' lean tag lost its guarded implementation"
    body = m.group(1)
    assert "splitLean(" in body, "leanTag must use the ONE shared lean parser, not its own regex"
    assert 'return ""' in body, "an unparseable/absent read must render NOTHING (fail-honest)"
    for banned in ("pill", "buy", "avoid", "--danger", "--live", "--warn"):
        assert banned not in body, (
            f"leanTag renders {banned!r} — the lean tag must stay neutral (anti-anchoring); "
            "directional colour/verdict vocabulary belongs to the logged verdict, not the shelf")
    css = (Path(__file__).resolve().parents[1] / "frontend" / "assets" / "styles.css").read_text()
    rule = re.search(r"\.ds-lean \{([^}]*)\}", css)
    assert rule and "--ink-2" in rule.group(1), ".ds-lean must stay the muted/neutral ink"


def test_shelf_tag_prefers_the_logged_human_verdict() -> None:
    """The shelf tag's PRECEDENCE, which is the constitution in miniature: a logged human verdict
    outranks the machine's lean.

    Colour on this shelf must mean A HUMAN DECIDED — never that a model leaned. So the coloured
    buy/avoid pill lives in verdictTag (the verdict OF RECORD, where nothing is left to anchor)
    while leanTag stays neutral for the still-undecided names; the guard above pins that half.
    Invert the dispatch and an unlogged name would wear a decision colour."""
    import re
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "frontend" / "views" / "shared" / "dossier.js"
          ).read_text()
    m = re.search(r"function cardTag\(ticker, reads, verdictBy(?:, voidedBy = \{\})?\) \{(.*?)\n\}",
                  js, re.S)
    assert m, "cardTag() is gone — the shelf lost its tag-precedence dispatcher"
    assert re.search(r"return\s+v\s*\?\s*verdictTag\(v\)\s*:\s*leanTag\(", m.group(1)), (
        "cardTag must prefer the LOGGED verdict over the machine lean — inverted, an undecided "
        "name would wear a decision colour")
    vt = re.search(r"function verdictTag\(v\) \{(.*?)\n\}", js, re.S)
    assert vt, "verdictTag() is gone"
    assert "isBuyVerdict(" in vt.group(1), "verdictTag lost its buy/avoid TONE classifier"
    # THIS PIN MOVED WITH THE ENUM (PR-1b); it did not loosen. It used to assert the enum held
    # exactly {BUY, AVOID_TERMINAL}, on its own stated premise: `buy ? "BUY" : "AVOID"` is lossless
    # ONLY while those are the whole vocabulary. `PASS` made that premise false — and the old
    # collapse would have printed "AVOID" over a PASS, which is precisely the false record the
    # separate label exists to prevent. So the WORD now comes from `verdictWord`, and what is
    # pinned is the property the old assertion stood in for: every member renders as ITSELF except
    # the one documented shortening. That is strictly stronger — it stays true as the enum grows,
    # instead of going red and being loosened.
    assert '"BUY" : "AVOID"' not in vt.group(1), (
        "verdictTag still collapses the verdict to two words — a third label prints as AVOID")
    assert "verdictWord(v.verdict)" in vt.group(1), (
        "verdictTag must render through verdictWord — the one place the shortening lives")
    # MOVED TO THE SHARED LIB (PR-2f): the decision log was printing AVOID_TERMINAL in full where
    # the shelf printed AVOID, because only ONE view had this function. It now lives beside
    # `isBuyVerdict` — its sibling classifier — and both views import it, which is the single home
    # this assertion was always about. Checked THERE, not here, or the pin would pass while the
    # two surfaces disagreed again.
    lib = (Path(__file__).resolve().parents[1] / "frontend" / "lib" / "snapshots.js").read_text()
    vw = re.search(r"export function verdictWord\(verdict\) \{(.*?)\n\}", lib, re.S)
    assert vw, "verdictWord() is gone from the shared lib — the display shortening lost its home"
    assert "function verdictWord" not in js, (
        "verdictWord was re-declared in dossier.js — one definition, imported, or the shelf and "
        "the decision log drift apart again")
    for view in ("dossier.js", "decision-log.js"):
        src = (Path(__file__).resolve().parents[1] / "frontend" / "views" / "shared" / view
               ).read_text()
        assert "verdictWord" in src, f"{view} does not route its verdict word through the helper"
    from vinci.schemas.ledger import Verdict

    body = vw.group(1)
    assert '"AVOID_TERMINAL" ? "AVOID"' in body, "the documented AVOID_TERMINAL shortening is gone"
    for member in Verdict:
        if member.value != "AVOID_TERMINAL":
            assert f'"{member.value}"' not in body, (
                f"{member.value} is special-cased in verdictWord — every other member must render "
                f"as ITSELF, or the shelf and the sealed record disagree about what was decided")


def test_dossier_index_labels_match_the_backend_resolver() -> None:
    """The stdlib twin: build.py's index `labels` map must equal vinci.labels.committed_gics_index
    over the real committed dossier tree — the build fence forbids the import, so the two
    implementations are pinned against each other instead."""
    from pathlib import Path

    from vinci.labels import committed_gics_index

    root = Path(__file__).resolve().parents[1]
    committed = json.loads((root / "frontend" / "dossiers" / "index.json").read_text())
    expect = {t: {"industry": v["industry"], "source": "ciq-gics", "source_ref": v["source_ref"]}
              for t, v in committed_gics_index(root / "data" / "dossiers").items()}
    assert committed.get("labels") == expect


def test_dossier_index_reads_are_verbatim_and_complete() -> None:
    """The index `reads` map carries each committed dossier's synthesis evidence_balance VERBATIM
    (the index cards' lean tag splits it client-side with the ONE shared parser).

    Phrasing-independent BY CONSTRUCTION: it asserts coverage + byte-equality against the dossiers
    themselves, never a literal lean string — evidence_balance is LLM-composed and re-words on
    every re-assembly, so a value pin here would rot the committed artifact (TEST-LAYER RULE)."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    committed = json.loads((root / "frontend" / "dossiers" / "index.json").read_text())
    reads = committed.get("reads")
    assert isinstance(reads, dict) and reads, "index.json carries no reads map"
    expect = {}
    for folder in sorted(p for p in (root / "data" / "dossiers").iterdir() if p.is_dir()):
        f = folder / "dossier.json"
        if not f.is_file():
            continue
        eb = ((json.loads(f.read_text()).get("synthesis") or {}).get("evidence_balance") or "")
        if eb.strip():
            expect[folder.name.upper()] = eb.strip()
    assert reads == expect, "index reads drifted from the committed dossiers (not verbatim)"
    # every read must SPLIT under the shared lean grammar, else the card silently renders no tag
    for ticker, eb in reads.items():
        assert split_lean(eb) is not None, f"{ticker}'s read does not split — its card loses a tag"


def test_build_never_grows_a_second_lean_parser() -> None:
    """TOMBSTONE: the '<lean> — <why>' split has ONE python parser (vinci.dossier.verdict) and ONE
    JS mirror (dossier.js). build.py ships the read RAW so it never becomes a third — the same
    two-divergent-parsers bug class the shared-parser rule exists to kill."""
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "frontend" / "build.py").read_text()
    assert "[—–-]" not in src and "split_lean" not in src, (
        "build.py grew a lean parser — emit evidence_balance verbatim and let the ONE shared "
        "parser split it")
