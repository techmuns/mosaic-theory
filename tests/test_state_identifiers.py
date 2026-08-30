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

#: A REFERENCE — ANY `S<n>`/`D<n>` token. Deliberately BROAD, and the breadth is MEASURED, not
#: assumed: over the current STATE.md it matches **100 occurrences across 38 distinct tokens and
#: every one resolves to an existing entry — zero false positives.**
#:
#: THE FIRST CUT WAS NARROW AND THAT WAS THE #302 DEFECT AGAIN. It enumerated only the bracketed /
#: possessive / `see` / `STATE §` forms, justified by a false-positive risk that was never
#: measured — the same speculative narrowing that made the hygiene guard blind to six live
#: violations. Sensitivity-tested per form: the narrow pattern CAUGHT `(S99)`, `(S99,`,
#: `STATE S99`, `S99's`, `see S99` and MISSED `S99 records…`, `as S99 established`, `per S99` —
#: blind to the most natural way to write a citation, for a benefit that does not exist here.
#:
#: If a legitimate non-reference token ever appears (a product code, an axis label), this reds and
#: an exclusion gets added ON THE EVIDENCE. Loud first, narrowed on a real instance — never the
#: reverse.
REFERENCE = re.compile(r"\b([SD]\d{1,3})\b")


def _headings(text: str) -> list[str]:
    return [f"{k}{n}" for k, n in HEADING.findall(text)]


#: WHERE ENTRIES LIVE AFTER P1 (2026-08-25). The S/D entries moved out of STATE.md into
#: `docs/records/`, one file each, so resolving a citation against STATE.md ALONE now reports every
#: one of them as dangling — which is exactly what this test did on the migration commit, correctly.
#: The property being protected has not changed: *a citation resolves to exactly one entry*. What
#: changed is that the corpus is now two places, so it is read as two places.
RECORDS = ROOT / "docs" / "records"


#: README.md and TEMPLATE.md are documentation ABOUT records, not records. They carry an
#: ILLUSTRATIVE `D23` in the naming example, which this test duly reported as a dangling citation —
#: correct behaviour on a wrong corpus. Excluded by name, not by pattern, so a real record can
#: never be dropped from the check by accident.
_NOT_RECORDS = {"README.md", "TEMPLATE.md"}


def _corpus() -> str:
    parts = [STATE.read_text()]
    parts += [p.read_text() for p in sorted(RECORDS.glob("*.md"))
              if p.name not in _NOT_RECORDS]
    return "\n".join(parts)


def _references(text: str) -> set[str]:
    return set(REFERENCE.findall(text))


def test_every_state_identifier_is_unique() -> None:
    """THE S10 COLLISION, and any successor. Two entries under one number make every citation of it
    ambiguous — and the ambiguity is silent, because both entries render fine."""
    ids = _headings(_corpus())
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, (
        f"duplicate STATE.md identifiers: {dupes} — a citation of these resolves to two entries. "
        "Renumber the NEWER one; the older keeps its number so existing citations survive.")


def test_every_state_reference_resolves_to_an_entry() -> None:
    """A reference to a number no entry holds is a citation into a hole — the same broken property
    as a duplicate, seen from the other side."""
    text = _corpus()
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


def test_the_reference_pattern_catches_bare_prose_citations_too() -> None:
    """THE REVIEW FIX. The first cut enumerated bracketed/possessive/`see`/`STATE §` forms and
    missed bare prose — the most natural way to write a citation — on an UNMEASURED false-positive
    risk. Measured, that risk is zero on this corpus, so the pattern is broad and this pins the
    forms the narrow one dropped."""
    assert _references("(S15) and (D15, and STATE S3 and S3's and see D3 and D16's") == {
        "S15", "D15", "S3", "D3", "D16"}
    assert _references("S99 records the thing; as D98 established; per S97") == {
        "S99", "D98", "S97"}, "bare-prose citations must be checked — they were the blind spot"
    assert _references("no identifiers here, 2026-07-29, 10-K, $300M") == set(), (
        "dates, form types and dollar amounts must not read as identifiers")


def test_the_broad_pattern_has_no_false_positives_on_the_committed_record() -> None:
    """CORPUS BEFORE SYNTHETIC, applied to the widening itself. The pattern is only safe to keep
    broad while every token it finds resolves — asserted against the live file rather than assumed.
    If this reds, the fix is an exclusion justified by the token that forced it, never a quiet
    re-narrowing."""
    text = _corpus()
    unresolved = sorted(_references(text) - set(_headings(text)))
    assert not unresolved, (
        f"tokens matched but not resolvable: {unresolved} — either a dangling citation, or a "
        "non-reference token that needs an exclusion recorded with the instance that forced it")


def test_no_committed_conflict_markers_anywhere() -> None:
    """INVARIANT for a real incident (2026-08-30): a rebase resolution left `<<<<<<<` markers
    COMMITTED in STATE.md and the whole suite stayed green — the identifier lints check that
    references resolve, and a file with markers still resolves. That is the same blind spot
    CLAUDE.md names for dropped entries ("a smaller file that is still internally consistent, so
    it passes"), and STATE.md is exactly where the #443 rebase hazard lands.

    Cheap, total, and it fails on the file that actually carries the damage."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    hunted = [root / "STATE.md", root / "CLAUDE.md", *sorted((root / "docs").rglob("*.md"))]
    for d in ("vinci", "tests", "frontend"):
        hunted += [p for p in (root / d).rglob("*")
                   if p.suffix in {".py", ".js", ".css", ".json", ".md"} and p.is_file()]
    assert len(hunted) > 50, "the sweep found almost nothing — the globs are wrong, not the repo"
    bad: list[str] = []
    for p in hunted:
        try:
            text = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if line.startswith(("<<<<<<< ", ">>>>>>> ")) or line.rstrip() == "=======":
                bad.append(f"{p.relative_to(root)}:{n}: {line[:60]}")
    assert not bad, "committed merge-conflict markers:\n  " + "\n  ".join(bad)
