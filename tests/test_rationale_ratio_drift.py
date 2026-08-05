"""A ratio stated in the thesis prose must be the ratio the record computes.

WHY THIS EXISTS. SMPL's `verdict.rationale` reads *"the grid reads 3.8 to 1 against our 2:1 bar"* —
present tense, undated — while the same page's header eleven lines above prints
`Reward : risk 4.78 : 1`. **3.83 was the pre-item-24 ratio**; the denominator swap moved it to 4.78
and the sealed prose did not follow.

**NOTHING CAUGHT IT.** `moved_cited_claims` covers material financial-summary figures, not the
ratio. 19c demands a material row be STATED but never compares a cited ratio to a computed one.
`prose_lint` checks register and length. No test compared the prose to the header. A reader met a
stale number in the one paragraph written for them.

THE ESCAPE IS COPIED, NOT INVENTED. IT's rationale cites `6.7:1`, `1.90:1` and `5.8:1` and is
CORRECT: it is a dated amendment chain in a closed record — *"[amended 2026-07-22: position closed
2026-07-21…]"* — where each ratio is tagged to its moment. That is a HISTORY, not a claim about now.
So the rule is: **an undated present-tense ratio must match the computation; a dated history need
not.** IT is pinned below as the passing case rather than special-cased.
"""
from __future__ import annotations

import re

import pytest

import vinci.scenarios as sc

#: The reward:risk BAR, not a claim about this name — every rationale states it.
_BAR = {"2", "2.0"}

#: `N:1` or `N to 1`.
_CITED = re.compile(r"(\d+\.?\d*)\s*(?::|\s+to\s+)\s*1\b")

#: A DATED amendment tag. Its presence means the ratios in the prose are a history, each tagged to
#: its moment — IT's shape. Copied from the one record that legitimately cites stale ratios.
_AMENDED = re.compile(r"\[amended\s+\d{4}-\d{2}-\d{2}")

#: 6.7 against a computed 6.6859 is the same number rounded for a reader; 3.8 against 4.78 is not.
_TOL = 0.05

#: SELF-CLEARING EXEMPTION, the `ANCHORS_AWAITING_BACKFILL` shape. SMPL is the ONE live instance,
#: and shipping the guard red would make "some tests fail" the normal state — the exact condition
#: that lets a real failure hide. The assertion is an EXACT SET, so this list cannot rot silently:
#: when the supersede lands SMPL stops diverging and this test REDDENS, forcing STATE to be updated;
#: if a NEW name drifts it reddens too.
#:
#: **EMPTY SINCE 2026-08-05 — THE EXEMPTION CLEARED ITSELF, EXACTLY AS DESIGNED.** SMPL's
#: `verdict.rationale` stated 3.8:1 against a computed 4.78:1: sealed record text a re-assembly
#: could not touch, because the page renders it from the record and `dossier.json` carries zero
#: occurrences of the string. The note here said *"clears via `scenario-supersede`"*, and the
#: supersede of 2026-08-05 reissued the record with a pending verdict and no rationale, so the
#: divergence is gone. The exact-set assertion then went RED on a name that no longer diverges,
#: which is what forced this edit — a stale licence could not sit here unnoticed. An empty set is
#: the right end state: any NEW divergence now reddens with nothing to hide behind.
RATIONALE_RATIO_AWAITING_SUPERSEDE: set[str] = set()


def _cited_ratios(rationale: str) -> set[str]:
    return {m for m in _CITED.findall(rationale or "") if m not in _BAR}


def _diverges(rec: sc.ScenarioRecord) -> bool:
    """True when an UNDATED rationale cites a ratio the record does not compute."""
    rationale = rec.verdict.rationale or ""
    if _AMENDED.search(rationale):
        return False                                  # a dated history, not a claim about now
    cited = _cited_ratios(rationale)
    if not cited:
        return False
    computed = [c for c in (rec.result.ratio, rec.verdict.ratio_at_entry) if c is not None]
    if not computed:
        return False        # FAIL-OPEN, and deliberately: with no computed ratio there is nothing
        # to compare against and refusing would invent one. The path is kept VISIBLE by
        # `test_every_record_has_a_computed_ratio_so_the_fail_open_path_stays_shut`, so a record
        # that loses its ratio cannot quietly buy an exemption from this guard.
    # MAGNITUDE-ONLY PROSE IS A LATENT FALSE POSITIVE, recorded rather than pre-solved: four records
    # carry a NEGATIVE computed ratio (AORT -0.67, MVST -0.33, NCNO -0.72, WERN -0.35), and a
    # rationale writing "0.7:1" for -0.67 would read as drift. None of them cites a ratio today, so
    # the case is theoretical; if one appears, the fix is to compare magnitudes, not to widen _TOL.
    return any(all(abs(float(n) - float(c)) > _TOL for c in computed) for n in cited)


def test_no_undated_rationale_cites_a_ratio_the_record_does_not_compute() -> None:
    """THE GUARD. Exact-set so the exemption self-clears in both directions."""
    records = sc.all_records()
    if not records:
        pytest.skip("no committed records")
    diverged = {t for t, r in records.items() if _diverges(r)}
    assert diverged == RATIONALE_RATIO_AWAITING_SUPERSEDE, (
        f"rationales citing a ratio the record does not compute: {sorted(diverged)}, recorded: "
        f"{sorted(RATIONALE_RATIO_AWAITING_SUPERSEDE)}. If a supersede has landed, shrink the set "
        "and update STATE; if a NEW name drifted, sealed prose is stating a number the grid no "
        "longer produces — the SMPL defect, recurring.")


def test_it_is_the_passing_case_because_its_history_is_dated() -> None:
    """PINNED AS THE ESCAPE, not special-cased. IT cites three ratios that are all stale against its
    computed 1.52 — and is CORRECT, because each is tagged to its moment in an amendment chain on a
    closed record. Remove the dating and the same text must fail: that is what separates a history
    from a stale claim, and it is the only thing that does."""
    records = sc.all_records()
    it = records.get("IT")
    if it is None:
        pytest.skip("no committed IT record")
    assert _AMENDED.search(it.verdict.rationale or ""), "IT's amendment dating is gone"
    assert _cited_ratios(it.verdict.rationale or ""), "IT no longer cites a ratio — re-pin this"
    assert not _diverges(it)

    undated = it.model_copy(update={
        "verdict": it.verdict.model_copy(
            update={"rationale": _AMENDED.sub("[amended", it.verdict.rationale or "")})})
    assert _diverges(undated), (
        "IT's ratios passed with the DATE stripped — the guard is keying on something other than "
        "the dating, so a genuinely stale present-tense ratio would pass too")


def test_the_exemption_names_only_names_that_exist_and_actually_diverge() -> None:
    """An exemption for a name that no longer diverges is a stale licence; one for a name that does
    not exist is a typo that silently widens the guard."""
    records = sc.all_records()
    if not records:
        pytest.skip("no committed records")
    for t in RATIONALE_RATIO_AWAITING_SUPERSEDE:
        assert t in records, f"exempted {t!r} has no committed record"
        assert _diverges(records[t]), f"exempted {t!r} no longer diverges — drop it and fix STATE"


def test_every_record_has_a_computed_ratio_so_the_fail_open_path_stays_shut() -> None:
    """`_diverges` fails open when a record computes no ratio — correct (there is nothing to compare
    against) but silent. This keeps the path VISIBLE: today every record computes one, so the
    fail-open branch is never taken, and a record that loses its ratio reddens here rather than
    quietly slipping the guard."""
    records = sc.all_records()
    if not records:
        pytest.skip("no committed records")
    missing = {t for t, r in records.items()
               if r.result.ratio is None and r.verdict.ratio_at_entry is None}
    assert not missing, (
        f"{sorted(missing)} compute no ratio, so the drift guard cannot check their prose — it "
        "fails OPEN for them. Either the record is incomplete or the guard needs a second basis.")
