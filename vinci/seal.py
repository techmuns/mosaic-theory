"""THE SEAL — once a verdict is recorded, its rationale may only GROW.

The fund's record of what it believed at the moment it decided is the only thing that makes the
forward spread interpretable. If a rationale can be quietly re-worded after the fact, then every
past call reads as well-reasoned in hindsight and the track record proves nothing: you cannot
measure a discriminator whose stated reasoning moves with the outcome.

So a recorded verdict's ``rationale`` is APPEND-ONLY. It may grow by a dated amendment tag —
``[amended YYYY-MM-DD: ...]`` — and by nothing else. Rewording it, truncating it, or nulling it
all fail. The original is preserved INSIDE the field rather than beside it, which is what let the
second rationale field (``rationale_plain``) be retired: one field, sealed, that the linter and the
reader both bind to.

WHAT THIS DOES NOT PROTECT AGAINST, stated plainly: the baseline lives in a committed manifest
(``scenarios/_seal.json``), so anyone who deliberately regenerates that manifest defeats the seal.
This is a guard against silent drift and careless edits, NOT against a determined rewrite — for
names that opened a position the append-only LEDGER remains the untamperable copy, and for a watch
there is no such backstop (the 2026-07-21 WERN loss is the precedent). Regenerating a seal entry is
a deliberate, reviewable act and should be treated as one.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SEAL_FILE = "_seal.json"

# A verdict still awaiting the analyst has not been recorded, so its rationale is still a draft and
# is NOT sealed. Every other status is a decision that has been taken.
UNSEALED_STATUSES = frozenset({"pending_analyst", None, ""})

# THE only legal growth. Anchored so a tag must open a segment, and dated so an amendment cannot be
# backdated into invisibility — the date renders to the reader beside the text it changed.
#
# CLASSES (adopted 2026-07-27). A tag now declares WHAT KIND of change it records:
#   judgment — a leg or verdict change: the analyst's call moved. BELONGS in the rationale.
#   process  — a governance or system correction. A POINTER only; the detail lives in the
#              governance log, so the cap is tight.
#   machine  — a data or spot refresh. REJECTED from the rationale entirely: it belongs in the
#              record's ``refresh_log``, which is structured and machine-written.
# MOTIVATING CASE: SMPL's rationale reached 450 words of which 330 (73%) was amendment, and 169 of
# those words were process narration and a machine refresh — an audit trail three times the length
# of the thesis it was attached to. A reader met far more amendment than argument.
AMENDMENT_CLASSES: tuple[str, ...] = ("judgment", "machine", "process")
# Caps are FACE-VALIDITY limits on register, never tuned on anything. judgment is 100 (not 60): a
# real leg change legitimately carries the change, its evidence, AND its fragility disclosure —
# SMPL's 161-word re-verification showed 60 would force omission of substance. process is 25
# because it is a pointer by definition.
AMENDMENT_WORD_CAPS: dict[str, int] = {"judgment": 100, "process": 25}
# VERSION GATE. Tags dated ON OR AFTER this date must declare a class; every tag written before it
# stays legal unclassed — the rule is not retroactive, and a record written under the old contract
# is not made invalid by the new one.
CLASS_REQUIRED_FROM = "2026-07-27"

_CLASS_ALT = "|".join(AMENDMENT_CLASSES)
AMEND_TAG = re.compile(rf"\[amended (\d{{4}}-\d{{2}}-\d{{2}})(?:\s*\((?:{_CLASS_ALT})\))?\s*:")
_SPLIT = re.compile(rf"\s*(?=\[amended \d{{4}}-\d{{2}}-\d{{2}}(?:\s*\((?:{_CLASS_ALT})\))?\s*:)")
# A COMPLETE tag: opened by AMEND_TAG and closed by its bracket, nothing trailing. DOTALL so a
# multi-sentence amendment spanning newlines still reads as one tag.
_WHOLE_TAG = re.compile(
    rf"\[amended \d{{4}}-\d{{2}}-\d{{2}}(?:\s*\((?:{_CLASS_ALT})\))?\s*:.*\]", re.S)
# The head of one tag, for reading its date + (optional) class back off the text.
_TAG_HEAD = re.compile(
    rf"\[amended (\d{{4}}-\d{{2}}-\d{{2}})(?:\s*\((?P<cls>{_CLASS_ALT})\))?\s*:")


def tag_parts(tag: str) -> tuple[str, str | None, int]:
    """``(date, class-or-None, body word count)`` for ONE whole amendment tag.

    The word count measures the BODY — the text after the colon, minus the closing bracket — so a
    cap counts what the reader reads, not the tag's own scaffolding."""
    m = _TAG_HEAD.match(tag.strip())
    if m is None:
        return ("", None, 0)
    body = tag.strip()[m.end():].rstrip()
    if body.endswith("]"):
        body = body[:-1]
    return (m.group(1), m.group("cls"), len(body.split()))


def amendment_violations(rationale: str | None) -> list[str]:
    """Every class-contract violation in a rationale's amendment tags. Empty == compliant.

    THE CONTRACT, in one place so the seal and the linter cannot drift apart:
    a tag dated on/after :data:`CLASS_REQUIRED_FROM` must declare a class; ``machine`` is refused
    outright (its home is ``refresh_log``); ``judgment`` and ``process`` are capped. Tags written
    before the gate are legal unclassed and are NOT cap-checked — the rule is not retroactive.
    """
    out: list[str] = []
    for tag in amendments(rationale or ""):
        d, cls, words = tag_parts(tag)
        if not d:
            continue                                  # not a whole tag; `check` owns that failure
        if cls is None:
            if d >= CLASS_REQUIRED_FROM:              # ISO dates compare lexicographically
                out.append(
                    f"amendment {d} declares no class — tags dated on/after "
                    f"{CLASS_REQUIRED_FROM} must be one of {list(AMENDMENT_CLASSES)}")
            continue                                  # legacy tag: legal, and not cap-checked
        if cls == "machine":
            out.append(
                f"amendment {d} is class 'machine' — a data/spot refresh is REJECTED from the "
                "rationale; record it in the record's refresh_log (vinci scenario-refresh)")
            continue
        cap = AMENDMENT_WORD_CAPS[cls]
        if words > cap:
            out.append(
                f"amendment {d} ({cls}) is {words} words against a {cap}-word cap"
                + (" — a process tag is a POINTER; the detail belongs in the governance log"
                   if cls == "process" else ""))
    return out


def digest(text: str) -> str:
    """sha256 of the exact bytes — no normalisation. Whitespace IS content in analyst prose."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def base_text(rationale: str) -> str:
    """The rationale WITHOUT its amendment tags — the sealed thesis as first recorded."""
    return _SPLIT.split(rationale)[0].rstrip()


def amendments(rationale: str) -> list[str]:
    """Every appended amendment tag, in order."""
    return [p for p in _SPLIT.split(rationale)[1:] if p.strip()]


def seal_entry(rationale: str) -> dict[str, Any]:
    """The manifest entry that seals ``rationale`` as it stands now."""
    base = base_text(rationale)
    return {"chars": len(base), "sha256": digest(base)}


def is_sealed(status: str | None) -> bool:
    return status not in UNSEALED_STATUSES


def check(*, ticker: str, status: str | None, rationale: str | None,
          entry: dict[str, Any] | None) -> list[str]:
    """Violations of the seal for ONE record. Empty list == intact.

    Every branch fails LOUD rather than skipping: a sealed record with no manifest entry is a
    violation, not an exemption, or the seal could be dodged by deleting the entry.
    """
    if not is_sealed(status):
        return []
    if entry is None:
        return [f"{ticker}: verdict is recorded ({status!r}) but the record has NO seal entry — "
                f"a recorded rationale must be sealed; add it deliberately, never automatically"]
    if rationale is None:
        return [f"{ticker}: rationale is NULL on a recorded verdict — the seal forbids nulling; "
                f"a decision's stated reasoning cannot be withdrawn after the fact"]
    n = int(entry["chars"])
    prefix = rationale[:n]
    if len(rationale) < n:
        return [f"{ticker}: rationale SHRANK — {len(rationale)} chars against a sealed {n}; "
                f"the seal permits growth by amendment tags only"]
    if digest(prefix) != entry["sha256"]:
        return [f"{ticker}: the sealed opening {n} chars of the rationale were MUTATED "
                f"(sha256 {digest(prefix)[:16]}… != sealed {str(entry['sha256'])[:16]}…) — "
                f"reword by APPENDING '[amended <date>: …]', never by editing what was recorded"]
    # EVERY segment after the sealed prefix must be a WHOLE dated amendment tag — opened by the
    # tag and closed by its bracket, with nothing trailing.
    #
    # `fullmatch`, not `match`: the first draft of this checked only that a segment STARTED with a
    # tag, and the adversarial case below caught it — "[amended 2026-07-22: …] plus a quiet extra
    # sentence." opens legally and then says whatever it likes. Splitting rather than matching once
    # is likewise deliberate: a record accumulates amendments over its life, and each must stand on
    # its own.
    for seg in _SPLIT.split(rationale[n:]):
        if seg.strip() and not _WHOLE_TAG.fullmatch(seg.strip()):
            return [f"{ticker}: text was appended to the rationale that is not a dated amendment "
                    f"tag — got {seg.strip()[:60]!r}; the only legal growth is "
                    f"'[amended YYYY-MM-DD: …]'"]
    # ...and every tag must honour the CLASS contract (one definition, above).
    return [f"{ticker}: {v}" for v in amendment_violations(rationale)]


def load_manifest(root: Path) -> dict[str, Any]:
    p = root / "scenarios" / SEAL_FILE
    return json.loads(p.read_text()) if p.exists() else {}


def load_all_sealable(root: Path) -> dict[str, dict[str, Any]]:
    """Every record the seal governs, keyed as the manifest keys it: LIVE records by ticker, and
    ARCHIVED records by their archive key (``<TICKER>-<underwrite_date>``).

    Archived records stay in the sweep BY DESIGN (2026-07-27). Superseding a record must not be a
    way to move a sealed rationale out from under the seal — an archived record is still the
    record of what was believed, and the seal is the only thing that makes that claim checkable.
    (They leave the LIVE set, which is what the audit / monitor / spread read, so they can never
    be counted or scored twice.)"""
    import json as _json

    out: dict[str, dict[str, Any]] = {}
    d = root / "scenarios"
    if d.is_dir():
        for p in sorted(d.glob("*.json")):
            if not p.name.startswith("_"):
                out[p.stem] = _json.loads(p.read_text())
    a = d / "archive"
    if a.is_dir():
        for p in sorted(a.glob("*.json")):
            if not p.name.startswith("_"):
                out[p.stem] = _json.loads(p.read_text())
    return out


def check_all(records: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    """Violations across every record. ``records`` maps ticker (or archive key) -> record dict."""
    out: list[str] = []
    for ticker, rec in sorted(records.items()):
        v = rec.get("verdict") or {}
        out += check(ticker=ticker, status=v.get("status"), rationale=v.get("rationale"),
                     entry=manifest.get(ticker))
    return out


__all__ = ["AMEND_TAG", "SEAL_FILE", "UNSEALED_STATUSES", "amendment_violations", "amendments",
           "base_text", "check", "check_all", "digest", "is_sealed", "load_all_sealable",
           "load_manifest", "seal_entry", "tag_parts"]
