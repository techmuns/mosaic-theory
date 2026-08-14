"""A point that says a figure is NOT missing was flagged for saying it IS.

THE DEFECT. `NM` ("not meaningful") is a REAL STATE this codebase preserves deliberately — the
comp-set extractor's own contract is "NM PRESERVED as a real not-meaningful state (never dropped to
missing)". FUBO is the live instance: its trailing EBITDA is NEGATIVE, so TEV/EBITDA is arithmetic
nonsense rather than an absent number, and a careful synthesis point explains exactly that:

    "…its reconciler is that trailing EBITDA is negative (a real NM state, NOT MISSING); the
     forward view is the load-bearing read, and even there the name's NTM TEV/EBITDA 16.19 is a
     PREMIUM to the peer-median 9.87…"

`_MISSING_CLAIM` matched the `missing` inside `not missing`, so the citation check ruled the point
"asserts missing/UNKNOWN data yet cites a PRESENT field" and rendered it `⚠ uncited`. The model was
penalised for being PRECISE about a distinction the repo itself draws, and the most useful sentence
about the name's valuation was the one that got flagged.

WHY IT LOOKED LIKE PROSE CHURN AND WASN'T. FUBO carried an uncited flag in EVERY historical
artifact commit, and re-rolling its synthesis produced a FRESH instance of the same class (a
`bull_point` about TEV/Revenue became a `bear_point` about TEV/EBITDA NM) — because the cause is
the check, not the writing. Any name whose metric is genuinely NM will keep tripping it.

THE GUARD KEEPS ITS JOB. It exists so a claim cannot say "field X is missing" while citing some
unrelated PRESENT field as evidence, and every real absence phrasing below must still fire. Only a
NEGATED mention is exempted, and `not disclosed` / `not available` / `not provided` / `not
reported` are NOT negations — they MEAN missing, so they keep their own alternative in the pattern.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier.synthesis import _MISSING_CLAIM

#: Real absence claims — the guard's actual purpose. Each MUST match.
_REAL_ABSENCE = (
    "EBITDA is missing from the panel",
    "the covenant basis is unavailable",
    "leverage was not disclosed",
    "the ratio is not reported",
    "the reconciliation was not provided",
    "the figure is not available",
    "no segment data exists for this name",
    "shares outstanding are absent",
    "the basis is undisclosed",
    "the value is UNKNOWN",
)

#: Negated mentions — the claim asserts the OPPOSITE of absence. None may match.
_NEGATED = (
    "a real NM state, not missing",
    "the figure is NOT MISSING here",
    "this isn't missing, it is negative",
    "NM is not unavailable",
)


@pytest.mark.parametrize("claim", _REAL_ABSENCE)
def test_a_real_absence_claim_still_trips_the_guard(claim: str) -> None:
    """THE GUARD'S JOB, unchanged. Narrowing a check is where you quietly lose the thing it was
    for, so every absence phrasing is pinned individually — including the four `not <x>` forms that
    READ like negations but MEAN missing and must keep matching."""
    assert _MISSING_CLAIM.search(claim), (
        f"a genuine absence claim stopped tripping the guard: {claim!r} — the narrowing went too "
        f"far and a 'field X is missing' point can now cite an unrelated present field")


@pytest.mark.parametrize("claim", _NEGATED)
def test_a_negated_mention_does_not_trip_the_guard(claim: str) -> None:
    """THE FIX. Saying a figure is NOT missing is the opposite of asserting it is."""
    m = _MISSING_CLAIM.search(claim)
    assert m is None, (
        f"{claim!r} was read as an absence claim (matched {m.group(0)!r} under a negation) — the "
        f"point asserts the opposite of what the guard accused it of")


def test_the_live_fubo_sentence_is_no_longer_flagged() -> None:
    """THE OBSERVED FAILURE, pinned against the COMMITTED artifact rather than a paraphrase — the
    sentence is LLM-composed, so this reads it out of the record instead of restating it here,
    where a re-word would rot the pin.

    Skips rather than fails if FUBO's synthesis no longer carries an NM sentence: the point is that
    THIS shape must not be flagged, not that the model must keep writing it. If the population
    empties, the parametrised cases above still hold the rule.
    """
    path = pathlib.Path(__file__).resolve().parents[1] / "data/dossiers/FUBO/dossier.json"
    if not path.is_file():
        pytest.skip("FUBO dossier not committed")
    syn = json.loads(path.read_text()).get("synthesis") or {}
    claims = [
        p.get("claim", "") for side in ("bull_points", "bear_points")
        for p in (syn.get(side) or []) if isinstance(p, dict)
    ]
    negated = [c for c in claims if "not missing" in c.lower()]
    if not negated:
        pytest.skip("FUBO's current synthesis carries no 'not missing' sentence to pin")
    for c in negated:
        m = _MISSING_CLAIM.search(c)
        assert m is None, (
            f"the committed FUBO point still trips the guard on {m.group(0)!r} while explicitly "
            f"saying the figure is NOT missing: {c[:150]!r}")


def test_the_negation_guard_is_scoped_to_the_bare_tokens() -> None:
    """THE BOUNDARY, stated as a test so the next edit cannot blur it. `not disclosed` and friends
    are absence claims whose surface form begins with "not" — exempting anything preceded by "not"
    would silently retire four of the guard's ten phrasings."""
    for phrase in ("not disclosed", "not available", "not provided", "not reported"):
        assert _MISSING_CLAIM.search(f"the value was {phrase}"), (
            f"{phrase!r} stopped matching — it MEANS missing, and the negation guard must not "
            f"reach it")
    # …while the bare tokens under a negation stay exempt
    assert _MISSING_CLAIM.search("the value is missing")
    assert not _MISSING_CLAIM.search("the value is not missing")
