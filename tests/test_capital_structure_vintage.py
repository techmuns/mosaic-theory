"""The debt schedule has never carried an age, and one of them still lists a dead facility.

THE DEFECT. NFLX's committed page lists the Warner Bros. Discovery bridge facility. Its commitments
were terminated on **2026-02-27** — and the page cannot know, because the CIQ capital-structure
panel is dated **2026-01-23** and nothing on the page says how old that is.

WHY THE AGE WAS INVISIBLE — a format mismatch nobody had cause to notice. `freshness._PANEL_KEY`
DOES match `detail_as_of`, so the key was found; but `freshness._ISO` wants `2026-01-23` and CIQ
writes `Jan-23-2026`, so the date was never extracted and the panel silently contributed nothing.
Measured across all 14 committed dossiers, the source filings run **82-280 days** behind their own
build (SMPL 280 · V 277 · BRBR 265 · NFLX 199 …).

AND WHY THE OBVIOUS FIX IS REFUSED. Teaching `freshness._ISO` the CIQ format routes the panel into
`panel_age(kind="export")`, which feeds `check_freshness` — a GATE with a **45-day** ceiling that
**all fourteen names are past**. That change raises `FreshnessError` on the entire fleet, which is
the failure `check_freshness`'s own docstring names: *"a guard that stops every build is a freeze
wearing a guard's name."* So the age is rendered beside the schedule it describes, and the gate is
left alone. `test_the_panel_is_deliberately_kept_out_of_the_freshness_gate` pins that decision with
its measurement, so a later "improvement" has to confront the number rather than rediscover it.

THE TERMINATION HALF NEEDS NO FILING READ. Item 1.02 — "Termination of a Material Definitive
Agreement" — is carried in the filer's own submissions index, so a 1.02 filed AFTER the panel's
source date proves the panel cannot reflect it, from dates alone. Fleet today: 3 of 14 flag (NFLX's
WBD termination, UBER's 2026-08-07 Delivery Hero 8-K, VITL's 2026-08-06 refinancing).

A FLAG, NEVER A DELETION, and never a claim about WHICH instrument died — matching a termination to
a facility means reading the 8-K, and a wrong match is worse than an honest "something ended after
this snapshot, check it".
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.mechanical import _capital_structure_vintage, _cs_panel_filed

NFLX_PANEL = "A 2025 filed Jan-23-2026"
BUILT = date(2026, 7, 29)


class _Filing:
    def __init__(self, d: date, items: list[str], accession: str = "0001193125-26-082247") -> None:
        self.filing_date, self.items, self.accession = d, items, accession


class _Edgar:
    """Only `recent_filings` is touched, so a duck type drives this offline."""

    def __init__(self, filings: list[_Filing] | Exception) -> None:
        self._f = filings

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ()) -> list[_Filing]:
        if isinstance(self._f, Exception):
            raise self._f
        return self._f


# ─── the date CIQ actually writes ─────────────────────────────────────────────────────────────

def test_the_ciq_month_name_date_parses_where_the_iso_regex_cannot() -> None:
    """THE ROOT CAUSE, pinned as a unit. Every committed panel uses this format; the freshness
    module's ISO pattern matches none of them, which is why no schedule has ever shown an age."""
    from vinci.dossier.freshness import _ISO
    assert _ISO.search(NFLX_PANEL) is None, (
        "the ISO pattern now matches CIQ's format — the workaround here may be redundant, but "
        "check `check_freshness` first: routing this panel into the gate refuses the whole fleet")
    assert _cs_panel_filed(NFLX_PANEL) == date(2026, 1, 23)
    assert _cs_panel_filed("Q2 2026 filed May-06-2026") == date(2026, 5, 6)   # FUBO's shape
    assert _cs_panel_filed("A 2025 filed Mar-16-2026") == date(2026, 3, 16)


def test_an_unstated_or_unparseable_vintage_is_unknown_rather_than_assumed_fresh() -> None:
    """FAIL LOUD. A panel with no stated filing date has an UNKNOWN age, never a default one — an
    assumed-fresh schedule is the state this whole change exists to remove."""
    for bad in ("", "A 2025", "filed sometime", "A 2025 filed 13-99-2026"):
        assert _cs_panel_filed(bad) is None, bad
    out = _capital_structure_vintage(_Edgar([]), "0001065280", "A 2025", BUILT)
    assert out.value is None and "states no source filing date" in (out.note or "")


# ─── the termination signal ───────────────────────────────────────────────────────────────────

def test_a_termination_filed_after_the_panel_is_flagged_with_its_accession() -> None:
    """NFLX'S REAL SHAPE: panel filed 2026-01-23, Item 1.02 filed 2026-02-27. The reader is told
    the panel PREDATES it and cannot reflect it — and given the accession to check."""
    edgar = _Edgar([_Filing(date(2026, 2, 27), ["1.02"])])
    out = _capital_structure_vintage(edgar, "0001065280", NFLX_PANEL, BUILT)
    assert out.value is not None
    assert "187d old" in out.value and "2026-01-23" in out.value
    assert "Item 1.02" in out.value and "2026-02-27" in out.value
    assert "0001193125-26-082247" in out.value, "the accession to check is not named"
    assert "may already have been terminated" in out.value


def test_a_termination_filed_before_the_panel_is_not_a_finding() -> None:
    """THE ONE-SIDED HALF, and it is what keeps this from firing on every name with any history:
    a termination the panel already POSTDATES is baked into the schedule. Only a later one means
    the snapshot cannot know."""
    edgar = _Edgar([_Filing(date(2025, 6, 1), ["1.02"])])
    out = _capital_structure_vintage(edgar, "x", NFLX_PANEL, BUILT)
    assert out.value is not None and "no Item 1.02" in out.value, out.value


def test_an_eight_k_without_item_1_02_is_not_a_termination() -> None:
    """Item codes are the whole signal, so a filing carrying other items must not be read as one.
    UBER's real 1.02 arrives alongside 1.01/2.03/9.01, so the check is membership, not equality."""
    assert "no Item 1.02" in (_capital_structure_vintage(
        _Edgar([_Filing(date(2026, 6, 1), ["2.02", "9.01"])]), "x", NFLX_PANEL, BUILT).value or "")
    mixed = _capital_structure_vintage(
        _Edgar([_Filing(date(2026, 6, 1), ["1.01", "1.02", "2.03", "9.01"])]),
        "x", NFLX_PANEL, BUILT)
    assert "Item 1.02" in (mixed.value or "") and "no Item 1.02" not in (mixed.value or "")


def test_an_unreachable_edgar_says_unchecked_rather_than_clean() -> None:
    """THE DANGEROUS DEFAULT, refused. A network failure must not render as "no termination has
    been filed" — that is a guard reporting a clean pass it never made. The AGE still prints,
    because it needs no network."""
    from vinci.netcache import HttpError
    out = _capital_structure_vintage(_Edgar(HttpError("boom")), "x", NFLX_PANEL, BUILT)
    assert out.value is not None
    assert "187d old" in out.value, "the age was lost with the network"
    assert "UNCHECKED" in out.value and "no Item 1.02" not in out.value


# ─── the design decision, pinned with its measurement ─────────────────────────────────────────

@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_the_panel_is_deliberately_kept_out_of_the_freshness_gate() -> None:
    """THE REASON THE OBVIOUS FIX IS NOT THE FIX, pinned so it cannot be rediscovered the hard way.

    `check_freshness` RAISES past `MAX_PANEL_AGE_DAYS`. Every committed panel is past it — so
    teaching `freshness._ISO` the CIQ format would refuse the entire fleet, not tighten it. This
    asserts both halves: the panel contributes no date to `panel_dates` today, and the measurement
    that says it must not."""
    from vinci.dossier.freshness import MAX_PANEL_AGE_DAYS, panel_dates

    over = 0
    total = 0
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        doc = json.loads(p.read_text())
        mech: Any = doc.get("mechanical") or {}
        cs = mech.get("capital_structure") or {}
        filed = _cs_panel_filed(cs.get("detail_as_of") or "")
        if filed is None:
            continue
        total += 1
        if (date.fromisoformat(doc["assembled_at"][:10]) - filed).days > MAX_PANEL_AGE_DAYS:
            over += 1
        assert not [k for k, _ in panel_dates(mech) if "capital_structure" in k], (
            f"{p.parent.name}: the capital-structure panel now reaches `panel_dates`, which feeds "
            f"`check_freshness` — with {over}/{total} names past the {MAX_PANEL_AGE_DAYS}d ceiling "
            f"that gate would refuse the fleet")
    assert total, "no committed panel states a filing date — this test checked nothing"
    # THE CLAIM IS "GATING ON THIS PANEL WOULD REFUSE THE FLEET", NOT "EVERY PANEL IS STALE"
    # (2026-08-13). This required `over == total` — and after the 2026-08-12 re-assembly one name's
    # panel landed inside the ceiling, so a design argument that still holds comfortably reddened on
    # 13/14. What would actually overturn the argument is the ratio COLLAPSING, so that is what this
    # asserts: while a clear majority sits past the ceiling, the gate would still stop most of the
    # fleet, which is exactly why the panel is kept out of it.
    assert over > total / 2, (
        f"only {over}/{total} panels are past the {MAX_PANEL_AGE_DAYS}d ceiling — the majority no "
        f"longer is, so revisit whether the gate can now carry this panel after all")


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_every_committed_dossier_carries_its_panel_age() -> None:
    """#415's REVIEW LESSON, applied without being asked twice: a field only future assemblies
    populate ships nothing — the deployed pages would still have shown a debt schedule with no age
    beside it, which is the whole defect.

    PHRASING-INDEPENDENT (TEST-LAYER RULE): asserts the field is POPULATED and that the termination
    warning reaches at least one page; the specific dates and accessions are pinned on frozen
    fixtures above, because these artifacts get re-assembled.

    FUBO is exempt BY DERIVATION — `known_wrong.json` seals it and `refresh_dossier` refuses a
    transform on a sealed record."""
    missing, warned = [], []
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        if (p.parent / "known_wrong.json").exists():
            continue
        cs = (json.loads(p.read_text()).get("mechanical") or {}).get("capital_structure") or {}
        field = cs.get("panel_vintage")
        if field is None:
            missing.append(p.parent.name)
            continue
        val = field.get("value") or ""
        assert "old (source filed" in val, f"{p.parent.name}: no age in {val[:60]!r}"
        if "Item 1.02" in val and "no Item 1.02" not in val:
            warned.append(p.parent.name)
    assert not missing, (
        f"committed dossiers carry no panel vintage: {missing} — re-run the artifact pass, or the "
        f"page ships a debt schedule with no age beside it")
    assert warned, (
        "no committed page carries a termination warning — NFLX's WBD facility is the case this "
        "exists for, so a silent fleet means the signal stopped working")


def test_a_termination_filed_after_the_reference_date_is_not_this_records_to_report() -> None:
    """REVIEW FINDING (P1, #416) — THE LOOKAHEAD, and two of three committed warnings were it.

    `recent_filings` returns the CURRENT submissions index, so an unbounded "after the panel" test
    reports whatever exists when the code RUNS rather than at the record's as-of. Measured on the
    committed artifacts before the fix: UBER's 2026-07-29 record was flagged by an 8-K filed
    2026-08-07 (**+9d**) and VITL's 2026-07-06 record by one filed 2026-08-06 (**+31d**).

    Two harms, and the second is the quieter one: the page reports an event the reader could not
    have known, AND the artifact stops being reproducible — re-assembling at the same
    `reference_date` yields a different answer as time passes. That is the class `close_as_of`
    refuses one module over, arriving through a different door.

    The window is now `panel filed < 1.02 <= reference_date`, closed at both ends."""
    ref = date(2026, 7, 29)
    after = _Edgar([_Filing(date(2026, 8, 7), ["1.01", "1.02", "2.03"])])   # UBER's real shape
    out = _capital_structure_vintage(after, "0001543151", NFLX_PANEL, ref)
    assert out.value is not None
    assert "no Item 1.02" in out.value, (
        f"an 8-K filed 9 days after the as-of was reported as known at it: {out.value}")
    # …and one filed ON the reference date IS this record's to report — the bound is inclusive
    on_day = _Edgar([_Filing(ref, ["1.02"])])
    assert "Item 1.02" in (_capital_structure_vintage(
        on_day, "x", NFLX_PANEL, ref).value or "")
    assert "no Item 1.02" not in (_capital_structure_vintage(
        on_day, "x", NFLX_PANEL, ref).value or "")


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_no_committed_warning_cites_a_filing_after_its_own_as_of() -> None:
    """THE FLEET HALF of the same finding, and the pin that would have caught it: whatever a page
    cites must have existed at the date that page claims to be as of."""
    import re
    bad = []
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        doc = json.loads(p.read_text())
        cs = (doc.get("mechanical") or {}).get("capital_structure") or {}
        val = ((cs.get("panel_vintage") or {}).get("value")) or ""
        m = re.search(r"was filed (20\d\d-\d\d-\d\d)", val)
        if m and m.group(1) > str(doc.get("reference_date"))[:10]:
            bad.append(f"{p.parent.name}: cites {m.group(1)} on a "
                       f"{str(doc.get('reference_date'))[:10]} record")
    assert not bad, ("committed pages cite filings from after their own as-of:\n  "
                     + "\n  ".join(bad))
