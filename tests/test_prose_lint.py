"""The prose register linter — what it must catch, and what it must LEAVE ALONE.

Pins: every register category fires on a real observed shape; the three narrowings that separate a
house label from ordinary English hold (a linter that cries wolf gets switched off); the rationale
length rule counts words; ``write_record`` warns without blocking; and the new schema fields are
additive so every pre-existing record still validates.

The negative pins carry the actual sentences from committed records that motivated them — if a
future widening of a pattern re-breaks one, the test names the exact text that regressed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci import prose_lint as pl
from vinci import scenarios as sc

# ---------------------------------------------------------------- positive pins

@pytest.mark.parametrize(
    ("text", "category", "why"),
    [
        # each shape is lifted from a real committed record (see the 2026-07-21 worklist)
        ("8-K 0001702744-26-000021 reinstated guidance", "accession", "SMPL rationale"),
        ("trailing FCF yield ~12.3% (CIQ levered FCF 125.5)", "vendor", "SMPL rationale"),
        ("verified vs EDGAR companyfacts", "vendor", "EPAM margin method"),
        ("band refresh #162", "build_ref", "SMPL bull reason"),
        ("the 14.13% anchor is dragged by the pre-2021 regime", "house_token", "IT base reason"),
        ("committed evidence shows revenue deceleration", "house_token", "IT rationale"),
        ("Side taken: overshoot over GenAI disruption", "house_token", "IT rationale"),
        ("NOT pre-war (13.27% — dead regime)", "house_token", "EPAM base reason"),
        ("multiple near the own-history band-low (7.46)", "house_token", "IT bear reason"),
        ("below the 17.9x own-history median", "house_token", "SMPL base reason"),
        ("DRAFT — ratify at review. Legs set on the consensus path", "workflow_stamp", "EPAM"),
        ("the R1 recipe values it", "house_token", "recipe id as a bare token"),
        ("selected by screen2", "house_token", "screen name"),
        ("analyst adjudicated and the gate cleared", "workflow_stamp", "house status"),
        ("confidence stamped firm at assembly", "house_token", "grade in label context"),
    ],
)
def test_each_register_category_fires_on_a_real_shape(text: str, category: str, why: str) -> None:
    flags = pl.lint_text(text, "f")
    assert any(f.category == category for f in flags), (
        f"{why}: expected a [{category}] flag on {text!r}, "
        f"got {[(f.category, f.match) for f in flags]}"
    )


# ---------------------------------------------------------------- negative pins

@pytest.mark.parametrize(
    ("text", "why"),
    [
        # "early" as a DATE, not the freshness grade — from IT's re-underwrite trigger
        ("Q2-2026 print (early Aug): contract-value growth decelerates further",
         "'early Aug' is a date; flagging it would force mangling a good trigger"),
        # "clears" the VERB, not the `cleared` status — from IT's rationale
        ("a brutal secular bear (rev -20%, margin 13%, 8x) still clears 2.02:1",
         "'clears the bar' is standard buy-side English"),
        # possessive English, not the named statistic — from the analyst's SMPL/WERN restatements
        ("down to the lowest multiple in the company's own history",
         "'the company's own history' IS the plain restatement the rule asks for"),
        ("evidence that normal profitability is genuinely higher than the company's own history "
         "suggests", "same possessive form, WERN"),
        # the verb "overshot" states the claim; the noun "overshoot" is the house label
        ("our judgment is that the sell-off has overshot fair value",
         "stating the claim is exactly what the rule wants"),
    ],
)
def test_ordinary_english_is_not_flagged(text: str, why: str) -> None:
    assert pl.lint_text(text, "f") == [], f"false positive — {why}"


def test_own_history_narrowing_keeps_the_house_label_and_frees_the_english() -> None:
    """The one pattern that had to distinguish two senses of the same two words."""
    assert pl.lint_text("the own-history median is 17.9x", "f"), "hyphenated house label must flag"
    assert pl.lint_text("own history median of 17.9x", "f"), "spaced + statistic noun must flag"
    assert pl.lint_text("the company's own history suggests otherwise", "f") == [], \
        "possessive English must not flag"


# ---------------------------------------------------------------- length rule

def test_rationale_length_rule_counts_words_and_names_the_count() -> None:
    long = " ".join(["word"] * (pl.RATIONALE_MAX_WORDS + 1))
    flags = pl.lint_text(long, "verdict.rationale", max_words=pl.RATIONALE_MAX_WORDS)
    length = [f for f in flags if f.category == "length"]
    assert length and str(pl.RATIONALE_MAX_WORDS + 1) in length[0].match
    ok = " ".join(["word"] * pl.RATIONALE_MAX_WORDS)
    assert not [f for f in pl.lint_text(ok, "v", max_words=pl.RATIONALE_MAX_WORDS)
                if f.category == "length"], "exactly at the limit passes"


def test_length_rule_applies_to_rationale_fields_only() -> None:
    """A method is technical replication detail — it is allowed to be long."""
    long_method = " ".join(["detail"] * 300)
    rec = {"assumptions": {"margin": {"method": long_method}}}
    assert not [f for f in pl.lint_record(rec) if f.category == "length"]


# ---------------------------------------------------------------- record scanning

def test_structured_provenance_is_never_scanned() -> None:
    """An accession/vendor in a `source` is CORRECT — scanning there would invert the rule."""
    rec = {
        "spot_source": "Polygon EOD grouped-daily close 2026-07-17 (live)",
        "assumptions": {"revenue": {"method": "legs set off the consensus path", "references": [
            {"label": "FY2025 revenue", "value": 1.0, "unit": "$M",
             "source": "EDGAR companyfacts, 8-K 0001702744-26-000021 (CIQ cross-check)"}]}},
    }
    assert pl.lint_record(rec) == []


def test_lint_record_reaches_every_prose_surface() -> None:
    rec = {
        "verdict": {"rationale": "the anchor says so", "rationale_plain": "the anchor again",
                    "avoid_priced_note": "priced off the anchor",
                    "reunderwrite_triggers": ["anchor breaks"]},
        "scenarios": {"bear": {"reason": "anchor drags"}},
        "assumptions": {"margin": {"method": "anchor median"}},
        "gate_adjudication": "anchor adjudicated",
    }
    fields = {f.field for f in pl.lint_record(rec)}
    assert fields == {
        # rationale_plain is present, so IT is the reader-facing text and the sealed original is
        # exempt (see test_sealed_original_is_exempt_once_restated)
        "verdict.rationale_plain", "verdict.avoid_priced_note",
        "verdict.reunderwrite_triggers[0]", "scenarios.bear.reason",
        "assumptions.margin.method", "gate_adjudication",
    }


def test_sealed_original_is_exempt_once_restated_but_bound_until_then() -> None:
    """Whichever rationale faces the READER is the one the register binds.

    §7 seals the original: the machine never rewrites analyst words, and a restatement is recorded
    INSTEAD of altering it. If the sealed copy kept flagging, no restated record could ever reach
    zero — the linter would cry wolf forever and get switched off.
    """
    original = "Side taken: overshoot; the anchor is dragged by CIQ data"
    # no restatement yet -> the original is reader-facing and MUST flag
    only_original = pl.lint_record({"verdict": {"rationale": original}})
    assert only_original and all(f.field == "verdict.rationale" for f in only_original)
    # restatement recorded -> the original is a historical artifact, exempt; the plain text binds
    restated = pl.lint_record({"verdict": {"rationale": original,
                                           "rationale_plain": "The market has overshot on a "
                                                              "still-intact business."}})
    assert restated == [], "the sealed original must not flag once a restatement is recorded"
    # and the restatement itself is still policed
    bad_restatement = pl.lint_record({"verdict": {"rationale": original,
                                                  "rationale_plain": "the anchor says so"}})
    assert [f.field for f in bad_restatement] == ["verdict.rationale_plain"]


# ---------------------------------------------------------------- write-path + schema

def _minimal(**over: object) -> sc.ScenarioRecord:
    base: dict[str, object] = {
        "ticker": "TEST", "recipe_id": sc.RECIPE_R1, "recipe_desc": "d",
        "multiple_basis": "EV/EBITDA", "underwrite_date": "2026-07-21", "analyst": "tester",
        "spot": 10.0, "spot_source": "test",
        "facts": {
            "d_and_a": sc.Fact(value=1.0, unit="$M", basis="b", source="s"),
            "net_debt": sc.Fact(value=1.0, unit="$M", basis="b", source="s"),
            "diluted_shares": sc.Fact(value=1.0, unit="M shares", basis="b", source="s"),
        },
        "scenarios": {
            "bear": sc.ScenarioInput(revenue=1.0, margin=0.1, multiple=5.0, reason="r"),
            "base": sc.ScenarioInput(revenue=2.0, margin=0.1, multiple=5.0, reason="r"),
            "bull": sc.ScenarioInput(revenue=3.0, margin=0.1, multiple=5.0, reason="r"),
        },
        # schema 1.1 binds methodology on every axis; the text is deliberately register-clean so
        # the clean-write test below is actually testing the verdict prose it means to test
        "assumptions": {
            axis: sc.AssumptionDerivation(
                method="legs set against the reported history",
                references=[sc.RefPoint(label="FY2025", value=1.0, unit="$M", source="10-K")],
            )
            for axis in ("revenue", "margin", "multiple")
        },
    }
    base.update(over)
    return sc.ScenarioRecord(**base)  # type: ignore[arg-type]


def test_write_record_warns_on_register_violations_but_still_writes(tmp_path: Path) -> None:
    """Flag-only: the worklist surfaces, the record still persists (legacy must stay writable)."""
    rec = _minimal(verdict=sc.Verdict(status="confirmed", recorded="2026-07-21",
                                      rationale="the anchor is dragged by CIQ data"))
    with pytest.warns(pl.ProseRegisterWarning, match="prose-register flag"):
        path = sc.write_record(rec, root=tmp_path)
    assert path.exists(), "the lint must never block the write"
    assert json.loads(path.read_text())["verdict"]["rationale"] == \
        "the anchor is dragged by CIQ data", "the linter must NEVER rewrite analyst words"


def test_clean_record_writes_without_warning(tmp_path: Path, recwarn: pytest.WarningsRecorder
                                             ) -> None:
    rec = _minimal(verdict=sc.Verdict(status="confirmed", recorded="2026-07-21",
                                      rationale="BUY at $10. The market has sold a good business."))
    sc.write_record(rec, root=tmp_path)
    assert not [w for w in recwarn if issubclass(w.category, pl.ProseRegisterWarning)]


def test_new_fields_are_additive_so_existing_records_still_validate() -> None:
    """Every committed record predates rationale_plain — none may fail to load."""
    for p in sorted(Path("scenarios").glob("*.json")):
        if p.name.startswith("_"):
            continue
        rec = sc.ScenarioRecord.model_validate_json(p.read_text())
        assert rec.verdict is None or rec.verdict.rationale_plain is None or isinstance(
            rec.verdict.rationale_plain, str)


def test_rationale_plain_never_replaces_the_sealed_original() -> None:
    """Both fields coexist: the original is the sealed record, the restatement rides beside it."""
    v = sc.Verdict(status="confirmed", recorded="2026-07-21", rationale="original words",
                   rationale_plain="plain words", rationale_plain_recorded="2026-07-21")
    assert v.rationale == "original words" and v.rationale_plain == "plain words"


# ---------------------------------------------------------------- render pins

def _uw_card_src() -> str:
    return (Path(__file__).resolve().parents[1] / "frontend" / "views" / "shared" / "uw-card.js"
            ).read_text()


def test_rationale_render_leads_with_the_restatement_and_keeps_the_original() -> None:
    """Structure pin (never a text pin): the plain read leads, the sealed original stays reachable.

    Deliberately asserts SHAPE, not wording — rationale text is analyst-authored prose and an
    exact-string pin on it would rot the moment a name is re-underwritten.
    """
    import re

    src = _uw_card_src()
    fn = re.search(r"function rationaleFact\(v\) \{(.*?)\n\}", src, re.S)
    assert fn, "rationaleFact() is gone"
    body = fn.group(1)
    assert "if (!v.rationalePlain) return fact" in body, (
        "with no restatement the original must render exactly as before — no record is worse off")
    assert "uw-rationale-orig" in body and "<details" in body, (
        "the original must survive behind an expander, never be replaced")
    assert "v.recorded" in body, "the expander must date the original ('as recorded <date>')"
    # the card body calls it — the old inline conditional must be gone
    assert "${rationaleFact(v)}" in src and 'fact("Rationale", escapeHtml(v.rationale))' not in \
        re.sub(r"function rationaleFact\(v\) \{.*?\n\}", "", src, flags=re.S), (
        "the card body must route through rationaleFact()")


def test_card_emitter_omits_rationale_plain_when_absent() -> None:
    """Byte-identity guard: a record without a restatement must re-emit exactly as before."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frontend"))
    import build  # type: ignore[import-not-found]

    rec = json.loads((Path("scenarios") / "WERN.json").read_text())
    rec["verdict"] = dict(rec.get("verdict") or {})
    rec["verdict"].pop("rationale_plain", None)
    card = build._scenario_card(rec)
    assert "rationalePlain" not in card["verdict"], (
        "absent restatement must OMIT the key, never emit null")


def test_draft_badge_renders_from_structured_state_not_a_prose_marker() -> None:
    """An unratified axis is flagged by `unratified`, never by "DRAFT" typed into the method.

    Structural pin both ways: a null-stamped axis emits the flag and the card badges it; a stamped
    axis emits nothing and renders no badge. This is what let the DRAFT prose marker be DROPPED —
    the state was already structured, and a prose duplicate of structured state is precisely what
    the register rule removes.
    """
    import re
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frontend"))
    import build  # type: ignore[import-not-found]

    rec = json.loads((Path("scenarios") / "EPAM.json").read_text())
    card = build._scenario_card(rec)
    axes = {a["axis"]: a for a in card["assumptions"]}
    assert all(a.get("unratified") for a in axes.values()), (
        "EPAM's axes are unratified (ratified_by null) — every one must carry the flag")
    assert not any("DRAFT" in a["method"] for a in axes.values()), (
        "the prose marker is gone; structured state carries draft status now")

    stamped = json.loads((Path("scenarios") / "IT.json").read_text())
    st_card = build._scenario_card(stamped)
    assert not any("unratified" in a for a in st_card["assumptions"]), (
        "a ratified axis must OMIT the key entirely, so its card stays byte-identical")

    src = (Path(__file__).resolve().parents[1] / "frontend" / "views" / "shared" / "uw-card.js"
           ).read_text()
    fn = re.search(r"function methodLines\(c\) \{(.*?)\n\}", src, re.S)
    assert fn and "a.unratified" in fn.group(1) and "uw-draft-badge" in fn.group(1), (
        "methodLines must badge from a.unratified")


def test_every_committed_scenario_record_is_register_clean() -> None:
    """THE REPO CHECK. The four records are the external-reader surface — they stay clean.

    Data-coupled by design: it ships with the restatement that makes it true, because a test that
    is red at one commit and green at the next is a red commit.
    """
    dirty = {}
    for p in sorted(Path("scenarios").glob("*.json")):
        if p.name.startswith("_"):
            continue
        flags = pl.lint_record(json.loads(p.read_text()))
        if flags:
            dirty[p.stem] = [str(f) for f in flags]
    assert not dirty, ("prose-register violations in committed records:\n"
                       + json.dumps(dirty, indent=2))
