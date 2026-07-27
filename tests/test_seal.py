"""THE SEAL — a recorded verdict's rationale may only grow by dated amendment tags.

Why this exists at the REPO layer and not only as a unit test: the thing being protected is the
committed artifact, and the failure mode is an edit that looks reasonable in a diff. A unit test on
the checker would pass happily while a record on disk had been silently re-worded, so the binding
assertion here runs over `scenarios/*.json` as committed.

The unit tests below are the PIN's own proof — each one mutates a rationale in a specific way and
asserts the checker goes red. A guard that has never been shown to fail is not a guard.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci import seal

ROOT = Path(__file__).resolve().parents[1]

_SEALED = "The market has overshot on a business whose economics have not changed."
_AMEND = " [amended 2026-07-22: the perimeter-corrected figure moves the base leg, not the call.]"


def _records() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text())
            for p in sorted((ROOT / "scenarios").glob("[A-Z]*.json"))}


# --- the binding assertion: every committed record, against the committed manifest --------------
def test_committed_records_are_sealed_and_intact() -> None:
    """THE repo-layer pin. Every recorded verdict must have a seal entry, and its rationale must
    still open with the exact sealed bytes."""
    violations = seal.check_all(_records(), seal.load_manifest(ROOT))
    assert violations == [], "SEAL VIOLATION:\n  " + "\n  ".join(violations)


def test_every_recorded_verdict_has_a_seal_entry() -> None:
    """A sealed record with no manifest entry must FAIL, not be skipped — otherwise the seal is
    dodged by deleting the entry, which is the easiest possible bypass."""
    manifest = seal.load_manifest(ROOT)
    for ticker, rec in _records().items():
        v = rec.get("verdict") or {}
        if seal.is_sealed(v.get("status")):
            assert ticker in manifest, (
                f"{ticker} has a recorded verdict ({v.get('status')!r}) but no seal entry")
            assert v.get("rationale"), f"{ticker} is sealed but its rationale is empty"


def test_pending_records_are_not_sealed() -> None:
    """A verdict the analyst has not taken yet is still a draft — sealing it would freeze wording
    before the decision it describes exists."""
    assert not seal.is_sealed("pending_analyst")
    assert not seal.is_sealed(None)
    assert seal.is_sealed("confirmed") and seal.is_sealed("watch") and seal.is_sealed("passed")


# --- the PIN'S OWN PROOF: defective inputs must go red ------------------------------------------
def _check(rationale: str | None, entry: dict | None = None, status: str = "confirmed"):
    return seal.check(ticker="TEST", status=status,
                      rationale=rationale,
                      entry=seal.seal_entry(_SEALED) if entry is None else entry)


def test_unchanged_rationale_passes() -> None:
    assert _check(_SEALED) == []


def test_appending_a_dated_amendment_tag_passes() -> None:
    """The ONE legal growth.

    UPDATED 2026-07-27 for amendment CLASSES: a tag dated on/after the gate must declare its kind,
    so the second (2026-08-01) tag here is classed. The pre-gate tag beside it stays legal
    unclassed — the non-retroactivity guarantee, asserted rather than assumed."""
    assert _check(_SEALED + _AMEND) == []                       # pre-gate, unclassed: legal
    assert _check(_SEALED + _AMEND + " [amended 2026-08-01 (judgment): and again.]") == []
    # ...and the same tag WITHOUT a class is now refused — the gate has teeth
    assert _check(_SEALED + _AMEND + " [amended 2026-08-01: and again.]") != []


@pytest.mark.parametrize("mutation,label", [
    (_SEALED.replace("overshot", "undershot"), "a single word changed"),
    (_SEALED.replace("The market", "The mrkt"), "a typo introduced"),
    (_SEALED[:-1], "one character truncated"),
    (_SEALED + " And it still is.", "free prose appended without a tag"),
    (_SEALED + _AMEND + " plus a quiet extra sentence.", "prose smuggled in after a legal tag"),
    ("Something else entirely.", "wholesale replacement"),
    ("", "emptied"),
])
def test_mutating_a_sealed_rationale_goes_red(mutation: str, label: str) -> None:
    """PROOF OF THE PIN. Each of these is a way a recorded rationale could be quietly changed;
    every one must be caught. If any passes, the seal is decorative."""
    assert _check(mutation) != [], f"seal did NOT catch: {label}"


def test_nulling_a_sealed_rationale_goes_red() -> None:
    """The 2026-07-21 precedent: all four originals were dropped to null in one pass. That was a
    deliberate analyst call made BEFORE this seal existed; afterwards it must be impossible to do
    by accident."""
    out = _check(None)
    assert out and "NULL" in out[0]


def test_a_missing_seal_entry_goes_red() -> None:
    out = seal.check(ticker="TEST", status="confirmed", rationale=_SEALED, entry=None)
    assert out and "NO seal entry" in out[0]


def test_prepending_text_goes_red() -> None:
    """Growth must be at the END. Prepending would push the sealed text down and change what the
    reader meets first, which is a rewrite by another name."""
    assert _check("Actually, on reflection. " + _SEALED) != []


def test_amendment_tag_must_carry_a_date() -> None:
    """An undated amendment cannot be placed in time against the verdict it modifies."""
    assert _check(_SEALED + " [amended: no date here.]") != []


# --- the helpers the linter shares --------------------------------------------------------------
def test_base_text_strips_amendments_for_the_word_cap() -> None:
    """The linter's length rule binds the THESIS, not the audit trail — otherwise recording an
    amendment and passing the linter become mutually exclusive, and the amendment loses."""
    assert seal.base_text(_SEALED + _AMEND) == _SEALED
    assert seal.base_text(_SEALED) == _SEALED
    assert len(seal.amendments(_SEALED + _AMEND)) == 1


def test_committed_manifest_covers_no_unknown_tickers() -> None:
    """A seal entry for a record that no longer exists is stale state — it would let a deleted
    record be silently re-added under its old seal."""
    unknown = set(seal.load_manifest(ROOT)) - set(_records())
    assert not unknown, f"seal manifest names records that do not exist: {sorted(unknown)}"
