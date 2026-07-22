"""Register linter for scenario-record PROSE — flag-only, never rewrites.

A scenario record is read by an external buy-side analyst who has never seen this repo. Prose that
carries an accession mid-sentence, a data-vendor's name, or a house-internal label ("the anchor",
"committed evidence", "DEAD REGIME") reads as internal notes leaking into a client-facing document —
and worse, it is not self-contained: the reader cannot check the claim without our vocabulary.

The rule (STATE.md §7 item 10, extended 2026-07-21) splits by FIELD, because the registers differ:

    rationale     plain thesis, <=~120 words — action + asymmetry, the variant view with its
                  carrying numbers, the kill condition
    triggers      measurable condition -> threshold -> action
    leg reasons   investment-committee register: statistics cited BY NAME
    methods       technical replication detail (a reader must be able to rebuild the number)

Two constraints bind EVERY prose field regardless of register: accessions and vendor names live in
the structured ``references`` / ``source`` fields only, and house-internal labels appear nowhere —
state the claim, not the label ("the sell-off has overshot fair value", never "overshoot").

WHY FLAG-ONLY. This module never edits a record. Rationale text is analyst-authored, and §7 holds
that the machine never rewrites analyst words; a linter that "fixed" prose would violate exactly the
line the rule exists to protect. It produces a worklist a human acts on.

DELIBERATELY NARROW MATCHES. Several house labels are also ordinary English, and a linter that cries
wolf gets switched off. Observed in the real records: "early Aug" (a date, not the freshness label
``early``) and "still clears 2.02:1" (the verb, not the ``cleared`` status). So the ambiguous labels
match only in label context, and ``cleared`` matches only the past participle. Each narrowing is
pinned by a negative test with the real sentence that motivated it.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from vinci import seal

# ---------------------------------------------------------------- limits

# The rationale is the one field with a LENGTH rule: it is the read a busy allocator gives you.
# "~120 words" in the rule; enforced as a hard 120 with the flag naming the actual count, so the
# margin conversation happens against a number rather than a vibe.
RATIONALE_MAX_WORDS = 120

# ---------------------------------------------------------------- patterns

# SEC accession: 0001702744-26-000021. Belongs in a reference's `source`, never mid-sentence.
_ACCESSION = re.compile(r"\b\d{10}-\d{2}-\d{6}\b")

# Data vendors + the filing system used AS a source citation. Naming them in prose tells an outside
# reader which subscription we hold, not what is true about the company.
_VENDORS = re.compile(r"\b(CIQ|Capital ?IQ|Polygon|EDGAR|companyfacts|S&P Global)\b")

# A PR / build number is repo provenance. "#162" means nothing to a reader outside this git history.
_BUILD_REF = re.compile(r"#\d{2,4}\b")

# House-internal labels with no ordinary-English collision — safe to match bare.
_HOUSE_PLAIN = re.compile(
    r"\b(anchor\w*|committed|overshoot|DOSSIER-NOW|Radar|dead regime|"
    r"twin call|avoid[- ]priced|band[- ]low)\b",
    re.IGNORECASE,
)

# `own-history <statistic>` is the house name for a computed series ("the own-history median",
# "own-history band-low"). But "the company's own history" is ORDINARY POSSESSIVE ENGLISH and is
# exactly the plain restatement the register rule asks for — flagging it would penalise the fix.
# So: the hyphenated/underscored form, or the spaced form only when it names a statistic.
_OWN_HISTORY = re.compile(
    r"\bown[-_]history\b|\bown history\s+(median|mean|band|multiple|percentile|stat\w*)\b",
    re.IGNORECASE,
)

# The recipe identifiers, as bare tokens (R1 / R2).
_RECIPE_ID = re.compile(r"\bR[12]\b")

# Screen names ("screen2", "Screen 2").
_SCREEN = re.compile(r"\bscreen\s?\d\b", re.IGNORECASE)

# --- narrowed matches (see module docstring) ---

# `ratified` / `ratify` / `DRAFT — ratify at review`: a workflow stamp, not analysis.
_RATIFY = re.compile(r"\b(ratif\w+|DRAFT\b[^.]*\bratif\w+)", re.IGNORECASE)

# `cleared` = the house status. "clears the 2:1 bar" is the ordinary verb and stays legal — so the
# PAST PARTICIPLE only. Motivated by real text: "brutal secular bear ... still clears 2.02:1".
_CLEARED = re.compile(r"\bcleared\b", re.IGNORECASE)

# Confidence / freshness labels that are also common English. Only fire in LABEL context — adjacent
# to a word that makes them a grade rather than an adjective. Motivated by real text: "Q2-2026 print
# (early Aug)" must NOT flag.
_GRADE_WORDS = r"(firm|partial|early|weak|current|stale)"
_GRADE_CONTEXT = re.compile(
    rf"(\b(confidence|freshness|evidence|rated|graded|stamp\w*|status)\b[^.]{{0,40}}\b{_GRADE_WORDS}\b"
    rf"|\b{_GRADE_WORDS}\b[^.]{{0,20}}\b(confidence|freshness|rating|grade|stamp\w*)\b)",
    re.IGNORECASE,
)


class ProseRegisterWarning(UserWarning):
    """Raised (as a warning) when a record is written with prose that breaks the register rule.

    A WARNING, never an exception: records written before the rule existed must stay writable, and
    the whole point of the linter is to hand a human a worklist — not to block the pipeline.
    """


class ProseFlag(BaseModel, frozen=True):
    """One register violation: WHERE, WHAT KIND, and the exact text that tripped it."""

    field: str  # dotted path within the record, e.g. "scenarios.base.reason"
    category: str  # accession | vendor | build_ref | house_token | workflow_stamp | length
    match: str  # the offending substring (or a count, for length)
    hint: str  # what to do instead

    def __str__(self) -> str:
        return f"{self.field}: [{self.category}] {self.match!r} — {self.hint}"


_CHECKS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (_ACCESSION, "accession",
     "move the accession to the reference's `source`; cite the filing in words"),
    (_VENDORS, "vendor", "name the fact, not the vendor; the vendor belongs in `source`"),
    (_BUILD_REF, "build_ref", "a PR/build number is repo provenance — drop it from prose"),
    (_HOUSE_PLAIN, "house_token", "state the claim, not the house label"),
    (_OWN_HISTORY, "house_token",
     "name the statistic in words, e.g. 'its nine-year multiple range'"),
    (_RECIPE_ID, "house_token", "name the method in words rather than its recipe id"),
    (_SCREEN, "house_token", "describe what the screen selected for, not its name"),
    (_RATIFY, "workflow_stamp", "ratification is a structured field, not prose"),
    (_CLEARED, "workflow_stamp",
     "'cleared' is a house status; say what passed and against what bar"),
    (_GRADE_CONTEXT, "house_token",
     "a confidence/freshness grade is a structured field, not prose"),
)


def lint_text(text: str, field: str, *, max_words: int | None = None) -> list[ProseFlag]:
    """Flag one prose string. ``max_words`` applies the length rule (rationale only)."""
    flags: list[ProseFlag] = []
    for pattern, category, hint in _CHECKS:
        for m in pattern.finditer(text):
            flags.append(ProseFlag(field=field, category=category, match=m.group(0), hint=hint))
    if max_words is not None:
        # The cap binds the THESIS, not the audit trail. A sealed rationale grows only by dated
        # `[amended …]` tags (vinci.seal), so counting those against the cap would force a choice
        # between recording an amendment and passing the linter — and the amendment would lose.
        # The register checks above still scan the tags: an amendment must read like the thesis it
        # extends, it just does not consume its budget.
        n = len(seal.base_text(text).split())
        if n > max_words:
            flags.append(
                ProseFlag(
                    field=field,
                    category="length",
                    match=f"{n} words",
                    hint=f"the rationale is the allocator's read — trim to <={max_words} words",
                )
            )
    return flags


def lint_record(rec: Any) -> list[ProseFlag]:
    """Every register violation in one scenario record (a ``ScenarioRecord`` or its plain dict).

    Scans ONLY prose. ``spot_source`` and each reference's ``source`` are structured provenance —
    an accession or a vendor name is CORRECT there, so scanning them would invert the rule.
    """
    d: dict[str, Any] = rec if isinstance(rec, dict) else rec.model_dump(mode="json")
    flags: list[ProseFlag] = []

    v = d.get("verdict") or {}
    # SINGLE REGISTER (ratified 2026-07-22). `verdict.rationale` is THE rationale — the field the
    # reader sees, the linter binds, and the seal protects.
    #
    # The former two-field arrangement (`rationale` sealed + `rationale_plain` reader-facing) split
    # the register in practice: the four restated records populated `rationale_plain` while the
    # three R2 records written afterwards populated `rationale`, so "the reader-facing text"
    # resolved to a DIFFERENT field per record and the linter's coverage moved with it. One field
    # cannot drift from itself.
    #
    # `rationale_plain` is DEPRECATED and read by nothing. What replaced its sealing job is
    # vinci/seal.py: growth is append-only, so the original survives INSIDE the field rather than
    # beside it — and the linter binding the whole field no longer risks crying wolf on sealed text,
    # because an amendment tag is appended in the same register as the text it extends.
    if v.get("rationale"):
        flags += lint_text(v["rationale"], "verdict.rationale",
                           max_words=RATIONALE_MAX_WORDS)
    if v.get("avoid_priced_note"):
        flags += lint_text(v["avoid_priced_note"], "verdict.avoid_priced_note")
    for i, t in enumerate(v.get("reunderwrite_triggers") or []):
        flags += lint_text(t, f"verdict.reunderwrite_triggers[{i}]")

    for leg, s in (d.get("scenarios") or {}).items():
        if isinstance(s, dict) and s.get("reason"):
            flags += lint_text(s["reason"], f"scenarios.{leg}.reason")

    for key, a in (d.get("assumptions") or {}).items():
        if isinstance(a, dict) and a.get("method"):
            flags += lint_text(a["method"], f"assumptions.{key}.method")

    if d.get("gate_adjudication"):
        flags += lint_text(d["gate_adjudication"], "gate_adjudication")

    return flags


def format_worklist(by_ticker: dict[str, list[ProseFlag]]) -> str:
    """Human-readable worklist — what a restatement pass has left to do."""
    lines: list[str] = []
    total = sum(len(f) for f in by_ticker.values())
    lines.append(f"PROSE REGISTER: {total} flag(s) across {len(by_ticker)} record(s)")
    for ticker in sorted(by_ticker):
        fl = by_ticker[ticker]
        if not fl:
            lines.append(f"  {ticker}: clean")
            continue
        lines.append(f"  {ticker}: {len(fl)} flag(s)")
        for f in fl:
            lines.append(f"    {f}")
    return "\n".join(lines)
