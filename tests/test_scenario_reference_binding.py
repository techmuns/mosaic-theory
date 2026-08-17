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
  2. every reference sourced to a committed band must be REPRODUCIBLE FROM THAT NAME'S OWN SERIES —
     catches a single hand-edited figure, which (1) cannot see.

WHY (2) IS "REPRODUCIBLE FROM ITS OWN SERIES" AND NOT "EQUALS THE BAND". Measured first, per
CORPUS BEFORE SYNTHETIC: a whole-band equality check flags EPAM, and EPAM is CORRECT. Its
reference is labelled *"post-2022 band median"* and sourced to *"series, 2022Q1 onward (n=18)"* —
15.16x is exactly EPAM's own trailing-20 median, a deliberate sub-window. The scoping lives in
prose, so it cannot be read structurally; the check that separates a windowed stat of YOUR OWN
series from ANOTHER COMPANY'S number is whether the value is derivable from this name's series at
all. That formulation flags 2 of BRBR's 3 foreign values and **zero** correct references. A guard
that cries wolf on good work gets disabled, so no-false-positives outranks catching all three —
and guard (1) catches BRBR a second time regardless.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import statistics
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Scenario records KNOWN to carry foreign references, with the reason. Asserted as a SUPERSET, not
#: an equality: fixing BRBR must not redden the suite (docs/engineering.md — "a test that fails when
#: things IMPROVE is worse than one that decays"). Removing the entry is the last step of the fix.
#: UNLOCK: re-derive BRBR's `assumptions.multiple.references` from BRBR's own committed band
#: (low 4.29 / median 19.76 / current 9.18) and re-state the legs' rationale against those — an
#: ANALYST action, not a mechanical one, because which reference justifies which leg is an
#: underwriting argument the machine must not free-write.
KNOWN_FOREIGN = {"BRBR": "assumptions block copied verbatim from SMPL (found 2026-08-17, #407 era)"}

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


def _own_series(ticker: str) -> list[float] | None:
    """The name's OWN committed EV/EBITDA close series, or None when it has no band."""
    path = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not path.is_file():
        return None
    bands = ((json.loads(path.read_text())["mechanical"]["valuation"].get("own_history") or {})
             .get("value") or [])
    band = next((b for b in bands if b.get("metric") == _BAND_METRIC), None)
    if band is None:
        return None
    return [v for _, v in (band.get("series") or []) if isinstance(v, (int, float))]


def _reachable(series: list[float]) -> set[float]:
    """Every stat derivable from ANY trailing window (>=4 closes) of this name's own series.

    Trailing windows only — a scenario reference cites a trailing range, and admitting arbitrary
    interior windows would make the reachable set so large that nothing could ever fail."""
    out: set[float] = set()
    for k in range(4, len(series) + 1):
        w = series[-k:]
        out |= {round(min(w), 4), round(max(w), 4),
                round(statistics.median(w), 4), round(statistics.mean(w), 4)}
    if series:
        out.add(round(series[-1], 4))
    return out


def _band_refs(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """References whose SOURCE names the committed own-history band — the ones bound to a series."""
    refs = []
    for axis in (doc.get("assumptions") or {}).values():
        for ref in (axis.get("references") or []):
            if ref.get("excluded"):
                continue
            if (str(ref.get("role")) in _STABLE_ROLES
                    and "own_history" in str(ref.get("source") or "")
                    and isinstance(ref.get("value"), (int, float))):
                refs.append(ref)
    return refs


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
    unexpected = [g for g in shared if not any(n.split("-")[0] in KNOWN_FOREIGN for n in g)]
    assert not unexpected, (
        f"scenario records share a byte-identical assumptions block: {unexpected}. Every reference "
        f"value, source and note in one name's underwriting is then another name's — the human "
        f"source-checking a leg verifies against the wrong company. Re-derive the references from "
        f"each name's own committed band. (Known: {sorted(KNOWN_FOREIGN)}.)")


def test_every_band_reference_is_reproducible_from_its_own_series() -> None:
    """GUARD 2 — the single hand-edited figure, which guard 1 cannot see.

    A reference sourced to `valuation.own_history` claims to describe THIS company's trading
    history. If its value is not derivable from this company's own committed close series under any
    trailing window, it came from somewhere else."""
    checked, foreign = 0, []
    for name, doc in _scenarios():
        ticker = name.split("-")[0]
        series = _own_series(ticker)
        if not series or len(series) < 4:
            continue
        reach = _reachable(series)
        for ref in _band_refs(doc):
            checked += 1
            value = float(ref["value"])
            if not any(abs(value - r) <= 0.02 * max(1.0, abs(r)) for r in reach):
                foreign.append(f"{name} {ref.get('role') or ref.get('label')}={value}")
    assert checked >= 6, (
        f"only {checked} stable-role band references checked — the corpus shrank, so this proves "
        f"less than it did when written (6 across BRBR/EPAM/IT/SMPL)")
    unexpected = [f for f in foreign if f.split()[0].split("-")[0] not in KNOWN_FOREIGN]
    assert not unexpected, (
        f"reference(s) cite a figure their own name's close series cannot produce: {unexpected}. "
        f"A reference sourced to `valuation.own_history` asserts it describes THIS "
        f"company; a value unreachable from its own series belongs to another. (Known: "
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
    assert still_shared == sorted(KNOWN_FOREIGN), (
        f"{sorted(set(KNOWN_FOREIGN) - set(still_shared))} no longer shares an assumptions block "
        f"with another name — the underwriting was re-derived, so DELETE the KNOWN_FOREIGN "
        f"entry so the guards protect this name again. This is the good failure.")
