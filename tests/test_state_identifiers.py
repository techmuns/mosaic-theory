"""STATE.md's S/D IDENTIFIERS MUST BE UNIQUE AND EVERY REFERENCE MUST RESOLVE.

THE INCIDENT. `S10` was held by TWO entries — Batch A (2026-07-31) and #302's `RefPoint.vintage`
(2026-08-01) — and stayed that way across FOUR merged PRs. Nothing noticed, because nothing looked:
the record is prose, and prose does not typecheck. It surfaced only when the operator asked for a
handoff enumeration, i.e. by luck rather than by check.

DANGLING REFERENCES ARE THE SAME CLASS. A duplicate makes `S10` ambiguous; a reference to a
number no entry holds makes it empty. Both break the same property — *a citation resolves to exactly
one entry* — so both are checked here rather than in two places.

WHY THIS IS THE LINTABLE HALF OF D22. D22 records that the suite is unverified evidence and that its
counter-measures (corpus before synthetic, real-type fixtures) are review discipline, not lintable.
Identifier integrity IS lintable, and this is it: the cheapest real guard available for the record.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "STATE.md"

#: AN ENTRY HEADING. Bold, at the start of its own paragraph: `**S10. …` / `**D15. …`. Matched
#: mid-line as well as at line-start, because a heading can follow an inline aside — D14 does
#: exactly that (`*(scheduling superseded by D19.)* **D14. …`), and a line-anchored pattern silently
#: missed it in the first enumeration this file exists to replace.
HEADING = re.compile(r"\*\*([SD])(\d+)\.\s")

#: A REFERENCE. Every form the record actually uses, enumerated from the file rather than imagined:
#: `(S15)`, `(D15,`, `STATE S3`, `S3's`, `see D3`, `D16's`. NOT a bare `S3` in running prose — that
#: matches section numbers, ticker fragments and dates, and a guard with false positives gets
#: disabled. Under-matching here is safe: it only means a reference form is unchecked, never that a
#: real one is wrongly flagged.
REFERENCE = re.compile(
    r"\((?P<a>[SD]\d+)[),;]"          # (S15)  (D15,  (D15;
    r"|STATE §?\s?(?P<b>[SD]\d+)"     # STATE S3 / STATE §S3
    r"|(?P<c>[SD]\d+)'s\b"            # S3's / D16's
    r"|see (?P<d>[SD]\d+)"            # see D3
)


def _headings(text: str) -> list[str]:
    return [f"{k}{n}" for k, n in HEADING.findall(text)]


def _references(text: str) -> set[str]:
    out = set()
    for m in REFERENCE.finditer(text):
        out.add(next(g for g in m.groups() if g))
    return out


def test_every_state_identifier_is_unique() -> None:
    """THE S10 COLLISION, and any successor. Two entries under one number make every citation of it
    ambiguous — and the ambiguity is silent, because both entries render fine."""
    ids = _headings(STATE.read_text())
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, (
        f"duplicate STATE.md identifiers: {dupes} — a citation of these resolves to two entries. "
        "Renumber the NEWER one; the older keeps its number so existing citations survive.")


def test_every_state_reference_resolves_to_an_entry() -> None:
    """A reference to a number no entry holds is a citation into a hole — the same broken property
    as a duplicate, seen from the other side."""
    text = STATE.read_text()
    known = set(_headings(text))
    dangling = sorted(r for r in _references(text) if r not in known)
    assert not dangling, (
        f"STATE.md references entries that do not exist: {dangling} — either the entry was "
        "renumbered without updating its citations, or the citation is a typo.")


def test_the_lint_reds_on_the_real_historical_collision() -> None:
    """D22'S COUNTER-MEASURE APPLIED TO THIS LINT ITSELF: validated against the REAL defect, not a
    synthetic mutation.

    `c112f25` is the merge of #303 — a commit where the S10 collision was LIVE and had already
    survived four merged PRs. If this lint cannot see it there, it would not have seen it then,
    and a guard that would have missed its own founding incident is decoration.

    Skips rather than fails when the object is unreachable (a shallow clone, or a worktree without
    that history) — an unavailable fixture is not a defect in the code under test. That is #280's
    lesson, applied here rather than re-learned."""
    try:
        blob = subprocess.run(
            ["git", "show", "c112f25:STATE.md"], cwd=ROOT,
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:      # pragma: no cover - env-dependent
        pytest.skip(f"git unavailable: {exc}")
    if blob.returncode != 0:                                  # pragma: no cover - env-dependent
        pytest.skip("commit c112f25 not reachable in this checkout")

    ids = _headings(blob.stdout)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert dupes == ["S10"], (
        f"expected the historical S10 collision at c112f25, found {dupes or 'none'} — if this is "
        "empty the lint cannot detect the defect it was built for")


def test_the_reference_pattern_matches_the_forms_the_record_actually_uses() -> None:
    """The matcher is enumerated from the file, so it must keep matching what the file contains.
    Pins the FORMS, not a count — the record grows, and a count would redden on every entry."""
    assert _references("(S15) and (D15, and STATE S3 and S3's and see D3 and D16's") == {
        "S15", "D15", "S3", "D3", "D16"}
    # Deliberately NOT matched: bare prose numbers, which is why the guard stays usable.
    assert _references("the S3 stage and D1 tranche") == set()
