"""A NULL SYNTHESIS FROM A CONFIGURED CLIENT MUST FAIL THE BUILD AND WRITE NOTHING.

THE INCIDENT, twice. Recorded 2026-07-22 as a CONSCIOUSLY ACCEPTED RISK: a transient LLM failure
makes ``synthesize`` return None and the assembler writes the dossier anyway with
``synthesis: null`` — silently replacing a committed synthesis with nothing. BRBR's 6-bull/8-bear
synthesis was wiped by one flaky call.

It fired again on 2026-07-30 and destroyed AORT's committed synthesis. The run printed
``1 done · 0 error(s)`` — two false statements in one line: the write happened, and it was not
reported as an error. The only signal was the word ``NO-synth`` in a summary line, precisely the
weakness the 07-22 record names.

Acceptance predated any evidence the risk fires. It has now fired twice, so the guard replaces it
(STATE: accepted → CLOSED).

THE ONE LEGITIMATE NO-SYNTHESIS CASE is a build with NO client configured — the mechanical-only
path, disclosed by its own flag. That is a MODE; a client that was asked and produced nothing is a
FAILURE, and the two must not share an outcome.
"""
from __future__ import annotations

import inspect

import pytest

from vinci.dossier import assemble as asm

# --- the refusal itself, driven behaviourally ---------------------------------------------------


def test_a_null_synthesis_raises() -> None:
    """THE RED. The 07-30 shape exactly: a configured client returned nothing."""
    with pytest.raises(asm.DossierAssemblyError, match="refusing to write"):
        asm._require_synthesis(None, ticker="AORT", flags=["LLM synthesis failed"])


def test_a_present_synthesis_passes() -> None:
    """The control — a real build must not be refused. Any non-None object satisfies it: the guard
    asks whether a synthesis EXISTS, and judging its contents is a different question with a
    different owner."""
    asm._require_synthesis(object(), ticker="AORT", flags=[])


def test_the_refusal_does_not_read_the_flag_text() -> None:
    """The 07-22 guard pinned only that a FLAG is emitted, and the artifact was destroyed anyway.
    Flag wording is LLM-adjacent and rewordable, so the refusal must key on the VALUE. Driven with
    an empty flag list and with a populated one — both must refuse identically."""
    for flags in ([], ["LLM synthesis failed (no usable output)"], ["something else entirely"]):
        with pytest.raises(asm.DossierAssemblyError):
            asm._require_synthesis(None, ticker="X", flags=flags)


def test_the_refusal_names_the_incident_and_the_remedy() -> None:
    """A refusal that says only "failed" invites a retry loop. It must say what writing would have
    destroyed, and that re-running is the fix."""
    with pytest.raises(asm.DossierAssemblyError) as e:
        asm._require_synthesis(None, ticker="AORT", flags=[])
    msg = str(e.value)
    for token in ("AORT", "refusing to write", "Re-run", "2026-07-30"):
        assert token in msg, f"the refusal does not mention {token!r}: {msg}"


# --- placement: the two properties a behavioural call cannot show -------------------------------


def test_the_guard_precedes_the_write() -> None:
    """ORDER IS THE WHOLE GUARD. A refusal raised after ``_write`` would leave the destroyed
    artifact on disk — the exact outcome being prevented — while reporting an error, which is worse
    than the silent version because the console would then contradict the disk."""
    src = inspect.getsource(asm.assemble_one)
    assert src.index("_require_synthesis") < src.index("_write(dossier"), (
        "the refusal must come BEFORE the artifact is written")


def test_the_mechanical_only_mode_cannot_reach_the_guard() -> None:
    """THE CONTROL for placement. A build with NO LLM legitimately has no synthesis and must still
    assemble — a declared mode with its own disclosure. The guard sits INSIDE ``if llm is not
    None``; this pins that, because moving it out would turn a supported mode into a hard failure
    and freeze every mechanical-only build."""
    src = inspect.getsource(asm.assemble_one)
    assert src.index("if llm is not None:") < src.index("_require_synthesis")
    assert "LLM synthesis skipped (no ANTHROPIC client) — mechanical layer only" in src


def test_the_failure_is_counted_as_an_error_not_a_flag() -> None:
    """The 07-30 run reported ``0 error(s)`` while destroying an artifact. A guard whose failure is
    not COUNTED as a failure has closed nothing — so the refusal must be an exception the cohort
    collects into its error list, which the CLI prints as ``N done · M error(s)``."""
    assert issubclass(asm.DossierAssemblyError, Exception)
    cohort = inspect.getsource(asm.assemble_cohort)
    assert "errors" in cohort and "except Exception" in cohort
