"""A scenario's references must belong to the company they justify.

BRBR's `assumptions` block is a byte-for-byte copy of SMPL's — all three axes, every reference
value, every note. BRBR's page therefore argues its bear multiple against *"this company's
trading-range low"* of **6.11x**, which is Simply Good Foods' floor; BRBR's own is **4.29x**. The
bear leg is 6.0x, so the prose reads as if it were stress-tested to the bottom of the name's own
range while sitting 1.71x ABOVE it. For a long-biased fund that is the dangerous direction: the
downside looks covered when it is not.

WHAT IS AND IS NOT WRONG. BRBR's ratified legs are its own and correctly scaled (bear revenue
2,250 / margin 8% / 6.0x against ~$2.3bn revenue; SMPL's are 1,200 / 13% / 5.5x). The DECISION is
not built on SMPL's figures — the JUSTIFICATION and the audit trail are. A human doing exactly what
source-binding exists for, checking the bear leg against its stated floor, verifies against another
company and comes away reassured. That is why this is worth a guard rather than a note.

TWO GUARDS, because either alone is escapable:
  1. no two scenario files share an `assumptions` block — catches the wholesale copy;
  2. every MULTIPLE-axis band statistic must be REPRODUCIBLE FROM THAT NAME'S OWN SERIES —
     catches a single hand-edited figure, which (1) cannot see.

WHY (2) IS "REPRODUCIBLE FROM ITS OWN SERIES" AND NOT "EQUALS THE BAND". Measured first, per
CORPUS BEFORE SYNTHETIC: a whole-band equality check flags EPAM, and EPAM is CORRECT. Its
reference is labelled *"post-2022 band median"* and sourced to *"series, 2022Q1 onward (n=18)"* —
15.16x is exactly EPAM's own trailing-20 median, a deliberate sub-window. The scoping lives in
prose, so it cannot be read structurally; the check that separates a windowed stat of YOUR OWN
series from ANOTHER COMPANY'S number is whether the value is derivable from this name's series at
all.

WHAT GUARD 2 ACTUALLY CATCHES — MEASURED, and the first draft of this docstring got it wrong.
It flags **1** of BRBR's 2 stable-role foreign values (`band_low` 6.11), not 2. `median` 17.85 is
SMPL's figure, but BRBR's OWN series genuinely produces a trailing-11 window median of 18.12 —
inside the 2% tolerance. So the value is foreign in PROVENANCE while being reachable in FACT, and
**no value-only test can separate those.** Tightening the tolerance does not help: EPAM's correct
`median` sits 32% from its whole-band median, so any threshold that rejects BRBR's 9.7% deviation
rejects EPAM's deliberate sub-window first. This is a real ceiling, recorded rather than tuned
around; guard (1) catches BRBR regardless, which is why two guards exist.
THE DISCRIMINATOR THAT WOULD WORK is not the value — it is the CITATION. BRBR's reference sources
itself to "35 closes, 8.55y span, sha 7bd83a1103", which are SMPL's; BRBR's own band carries 27
closes and a different sha. Checking those needs the cited provenance parsed out of a prose
`source` field, so it waits for provenance to be keyed structurally (the same unlock item 20 is
reopened against) rather than being bolted on with a regex here.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import statistics
from collections.abc import Callable, Sequence
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Scenario records KNOWN to carry foreign references, with the reason. Asserted as a SUPERSET, not
#: an equality: fixing BRBR must not redden the suite (docs/engineering.md — "a test that fails when
#: things IMPROVE is worse than one that decays"). Removing the entry is the last step of the fix.
#: UNLOCK: re-derive BRBR's `assumptions.multiple.references` from BRBR's own committed band
#: (low 4.29 / median 19.76 / current 9.18) and re-state the legs' rationale against those — an
#: ANALYST action, not a mechanical one, because which reference justifies which leg is an
#: underwriting argument the machine must not free-write.
#: EMPTY, AND THAT IS THE FIX LANDING — guard 3 demanded this deletion and was right.
#: BRBR sat here from 2026-08-17 while its multiple axis carried SMPL's figures. Those seven
#: references are now WITHDRAWN in the record itself (`excluded` + `excluded_reason`, which
#: renders dimmed WITH the reason rather than vanishing), so guard 2 sees no live reference
#: to exempt and guard 1 sees a block that no longer matches SMPL's.
#: DELETING THE ENTRY RESTORES PROTECTION rather than dropping it: re-paste SMPL's block and
#: guard 1 fires with nothing to excuse it; un-exclude those references and guard 2 fires on
#: values BellRing's own series cannot produce. An exemption is only ever earned while the
#: defect it names is live.
KNOWN_FOREIGN: dict[str, str] = {}

#: The EXACT shared-digest group that is exempt — not "any group containing an allowlisted name".
#: The first cut exempted the whole group, so a THIRD record pasted from BRBR/SMPL's block would
#: have been waved through for as long as the BRBR entry lived. Keyed as a frozenset so a new member
#: changes the key and reddens.
#: EMPTY for the same reason — BRBR's block no longer hashes to SMPL's, so ANY shared
#: assumptions block is now unexpected and fires.
KNOWN_SHARED_GROUPS: set[frozenset[str]] = set()

#: Records that cite a committed band while having NO committed dossier, so their band citations are
#: unverifiable by any means. Recorded rather than skipped: this is an anomaly in its own right — a
#: name underwritten without an assembled dossier — and it became VISIBLE only when the axis-scoped
#: predicate below started reaching WERN at all. UNLOCK: assemble the name, or drop the citation.
NO_COMMITTED_BAND = {"WERN": "underwritten with no committed dossier (found 2026-08-17)"}

_BAND_METRIC = "EV/EBITDA (TEV/LTM)"

#: ONLY the roles whose value is a STABLE STRUCTURAL STAT of the name's own close series. Measured,
#: not assumed — a first cut checked every band-sourced reference and produced two FALSE POSITIVES
#: on correct work, which is the failure mode that gets a guard switched off:
#:   · `percentile` — IT cites "this company's trailing 75th percentile" = 26.82x. Genuinely IT's,
#:     but an arbitrary quantile, and `_reachable` computes only min/max/median/mean. Unreachable
#:     by construction, so including it flags every correct quantile citation.
#:   · `current` — EPAM cites 4.87x where its band now reads 5.36x. A current multiple DRIFTS with
#:     every band refresh, so a citation going stale is expected and says nothing about ownership.
#: low/median/high do not move with price and cannot be an arbitrary quantile, so a mismatch there
#: means the figure is not this company's.
_STABLE_ROLES = {"band_low", "median", "band_high"}


def _scenarios() -> list[tuple[str, dict[str, Any]]]:
    out = []
    for p in sorted((ROOT / "scenarios").glob("*.json")):
        doc = json.loads(p.read_text())
        if doc.get("assumptions"):
            out.append((p.stem, doc))
    return out


def _own_band(ticker: str) -> dict[str, Any] | None:
    """The name's OWN committed EV/EBITDA band, or None when it has none."""
    path = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not path.is_file():
        return None
    bands = ((json.loads(path.read_text())["mechanical"]["valuation"].get("own_history") or {})
             .get("value") or [])
    return next((b for b in bands if b.get("metric") == _BAND_METRIC), None)


#: role -> the ONE statistic that role names. Cross-kind matching was a real defect in the first
#: cut: it pooled min/max/median/MEAN into one set, so a `median` reference could be satisfied by
#: some window's MEAN. Each role now compares against its own statistic only.
_ROLE_STAT: dict[str, Callable[[Sequence[float]], float]] = {
    "band_low": min, "median": statistics.median, "band_high": max}
#: role -> the band field that role cites directly.
_ROLE_FIELD = {"band_low": "low", "median": "median", "band_high": "high"}


def _reachable(band: dict[str, Any], role: str) -> set[float]:
    """Values this role could legitimately take from THIS name's own band.

    TWO SOURCES, and the second is not optional. (a) the band's STORED field for the role, because
    that is the number a correct reference copies; (b) the same statistic over any trailing window,
    since a reference may legitimately cite a declared sub-window (EPAM's "post-2022 median").

    (a) IS LOAD-BEARING, measured: a band's low/median/high are computed with the CURRENT close
    EXCLUDED, while every trailing window necessarily includes it. So on any name whose current
    close is a new extreme, the band's own published `low` is unreachable as a window minimum —
    **5 of 13 committed names are in that state** (CNXC, MVST, SMPL, UBER, VRRM), and SMPL's
    correct `band_low` citation passed the first cut only by coincidence, because a trailing-4
    median happened to land near it. Without (a) this guard cries wolf on correct work on 5 names,
    which is the failure mode that gets a guard switched off."""
    stat = _ROLE_STAT[role]
    out = {round(stat(series[-k:]), 4)
           for series in [[v for _, v in (band.get("series") or [])]]
           for k in range(4, len(series) + 1)}
    stored = band.get(_ROLE_FIELD[role])
    if isinstance(stored, (int, float)):
        out.add(round(float(stored), 4))
    return out


def _band_refs(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Stable-role references on the MULTIPLE axis, in turns — what the EV/EBITDA band scores.

    SCOPED BY AXIS AND UNIT, NOT BY THE SOURCE STRING. The first cut used
    `"own_history" in ref["source"]`, which was wrong twice over. It made a rendered display string
    load-bearing — the rule this repo enforces everywhere else — and coverage then depended on how
    an author happened to phrase a citation: measured, it reached 3 of 8 records and silently
    exempted AORT's band `median` 32.1 ("CIQ Financials->Multiples (42 closes…)") and WERN's 6.56
    ("same series — derived band statistic").

    WIDENING NAIVELY WOULD HAVE BEEN WORSE, which is why the axis matters and not the wording:
    `median` also appears on the MARGIN axis, sourced to the anchor block or EDGAR companyfacts, and
    those values are PERCENTAGES. Scoring BRBR's margin median 15.45 against an EV/EBITDA close
    series is the same category error that made `percentile` a false positive. Only the `multiple`
    axis cites this band, and `unit == "x"` is the structural confirmation.

    MEASURED: 9 references across 6 records, up from 7 across 4, with zero false positives."""
    axis = (doc.get("assumptions") or {}).get("multiple") or {}
    return [ref for ref in (axis.get("references") or [])
            if not ref.get("excluded")
            and str(ref.get("role")) in _STABLE_ROLES
            and ref.get("unit") == "x"
            and isinstance(ref.get("value"), (int, float))]


def test_no_two_scenario_records_share_an_assumptions_block() -> None:
    """GUARD 1 — the wholesale copy. Two names cannot have arrived at byte-identical reference
    values, notes and prose across all three axes independently; that is a paste, not a coincidence.

    Keyed on the whole `assumptions` block rather than a per-reference comparison so it fires once,
    loudly, on the copy itself rather than N times on its symptoms."""
    seen: dict[str, list[str]] = {}
    for name, doc in _scenarios():
        digest = hashlib.sha256(
            json.dumps(doc["assumptions"], sort_keys=True).encode()).hexdigest()[:16]
        seen.setdefault(digest, []).append(name)
    shared = [names for names in seen.values() if len(names) > 1]
    assert seen, "no scenario record carries an assumptions block — the guard ran vacuously"
    unexpected = [g for g in shared
                  if frozenset(n.split("-")[0] for n in g) not in KNOWN_SHARED_GROUPS]
    assert not unexpected, (
        f"scenario records share a byte-identical assumptions block: {unexpected}. Every reference "
        f"value, source and note in one name's underwriting is then another name's — the human "
        f"source-checking a leg verifies against the wrong company. Re-derive the references from "
        f"each name's own committed band. (Known groups: "
        f"{[sorted(g) for g in KNOWN_SHARED_GROUPS]}.)")


def test_every_band_reference_is_reproducible_from_its_own_series() -> None:
    """GUARD 2 — the single hand-edited figure, which guard 1 cannot see.

    A stable-role reference on the multiple axis claims to describe THIS company's trading history
    — that is what `band_low` / `median` / `band_high` in turns MEAN, whatever prose the `source`
    field happens to carry. If its value is neither the band's own stored statistic for that role
    nor that same statistic over any trailing window, it came from somewhere else."""
    checked, foreign, unscored = 0, [], []
    for name, doc in _scenarios():
        refs = _band_refs(doc)
        band = _own_band(name.split("-")[0])
        if not refs:
            continue
        # FAIL LOUD, NEVER SKIP SILENTLY. A record citing a band while carrying no committed band
        # is the shape where a foreign figure is LEAST likely to be caught by eye — WERN is live in
        # exactly that state today. The first cut `continue`d here and said nothing.
        if band is None or len(band.get("series") or []) < 4:
            unscored.append(name)
            continue
        for ref in refs:
            checked += 1
            value, role = float(ref["value"]), str(ref["role"])
            reach = _reachable(band, role)
            if not any(abs(value - r) <= 0.02 * max(1.0, abs(r)) for r in reach):
                foreign.append(f"{name} {role}={value}")
    # NO HAND-TUNED FLEET TOTAL. The first cut asserted `checked >= 6` against an actual 7 — a
    # value-level pin on a living corpus with one reference of slack, and the documented BRBR unlock
    # rewrites two of the seven, so the floor could redden on the fix it prescribes. That is the
    # exact anti-pattern #460 removed from tests/test_dossier.py for "reddening on a win". What is
    # asserted instead is that the loop ran at all, which is corpus-size independent.
    assert checked, (
        "no stable-role band reference was scored — every scenario record either cites no band or "
        "has no committed band, so this guard proved nothing")
    surprise = [n for n in unscored if n.split("-")[0] not in NO_COMMITTED_BAND]
    assert not surprise, (
        f"{surprise} cite a committed own-history band but have no usable band to check against — "
        f"a scenario underwriting a name with no committed dossier is itself the anomaly, and its "
        f"band citations cannot be verified by any means. Assemble the name, or drop the citation. "
        f"(Known: {sorted(NO_COMMITTED_BAND)}.)")
    unexpected = [f for f in foreign if f.split()[0].split("-")[0] not in KNOWN_FOREIGN]
    assert not unexpected, (
        f"reference(s) cite a figure their own name's close series cannot produce: {unexpected}. "
        f"A stable-role band statistic on the multiple axis asserts it describes THIS "
        f"company's own trading history — whatever prose its `source` field carries. A value "
        f"unreachable from that name's own series belongs to another. (Known: "
        f"{sorted(KNOWN_FOREIGN)}.)")


def test_the_known_foreign_record_is_still_foreign_and_still_recorded() -> None:
    """THE ALLOWLIST IS NOT A PLACE THINGS GO TO BE FORGOTTEN.

    Both guards above skip `KNOWN_FOREIGN`, so without this the entry could sit there after BRBR is
    fixed and silently exempt a future regression on the same name. This asserts the exemption is
    still EARNED — BRBR still shares SMPL's block — and prints the unlock when it stops being."""
    blocks = {name.split("-")[0]: hashlib.sha256(
        json.dumps(doc["assumptions"], sort_keys=True).encode()).hexdigest()[:16]
        for name, doc in _scenarios()}
    for ticker in KNOWN_FOREIGN:
        assert ticker in blocks, f"{ticker} is allowlisted but has no scenario record — drop it"
    still_shared = [t for t in KNOWN_FOREIGN
                    if sum(1 for other, d in blocks.items() if d == blocks[t]) > 1]
    assert sorted(still_shared) == sorted(KNOWN_FOREIGN), (
        f"{sorted(set(KNOWN_FOREIGN) - set(still_shared))} no longer shares an assumptions block "
        f"with another name — the underwriting was re-derived, so DELETE the KNOWN_FOREIGN "
        f"entry so the guards protect this name again. This is the good failure.")
