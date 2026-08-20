"""(K1b) A covenant value must name the filing it was read from.

CORPUS FIRST. EPAM's digest read "Expiration Date: October 21, 2026" from a 2017 8-K against a
capital-structure line saying Due 2030, and the page never said which filing it came from. The
suffix does not fix selection — it makes a stale selection VISIBLE, which is what the panel-age
stamp, the multiples vintage and the extraction version all do one layer over.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier.render import _covenant_source_suffix, _covenant_summary_lines
from vinci.dossier.schemas import Dossier

ROOT = pathlib.Path(__file__).resolve().parents[1]


class _G:
    """A GoverningTerm stand-in carrying only the two fields the suffix reads."""

    def __init__(self, base_ref: str | None, amended_by: tuple[str, ...] = ()) -> None:
        self.base_ref, self.amended_by = base_ref, amended_by


def test_the_suffix_names_the_base_filing_and_its_newest_amendment() -> None:
    dates = {"0001352010-17-000022": "2017-05-26", "0001352010-21-000039": "2021-10-25"}
    out = _covenant_source_suffix(
        _G("8-K 0001352010-17-000022 · exhibit10-1epamcreditagree.htm",
           ("0001352010-21-000039",)), dates)
    assert out == " — per an 8-K filed 2017-05-26, amended 2021-10-25", out


def test_an_unmatched_accession_yields_nothing_rather_than_a_guess() -> None:
    """FAIL-SOFT. An unattributed clause must read exactly as it does today, never worse — a
    guessed date on a covenant value would be the fabrication this repo refuses everywhere."""
    assert _covenant_source_suffix(_G("8-K 9999999999-99-999999 · x.htm"), {}) == ""
    assert _covenant_source_suffix(_G(None), {"a": "b"}) == ""


def test_the_newest_amendment_wins_when_several_are_chained() -> None:
    dates = {"0000000000-00-000001": "2019-01-01", "0000000000-00-000002": "2023-06-01",
             "0000000000-00-000003": "2025-11-19"}
    out = _covenant_source_suffix(
        _G("8-K 0000000000-00-000001 · base.htm",
           ("0000000000-00-000003", "0000000000-00-000002")), dates)
    assert "amended 2025-11-19" in out, out


def test_the_committed_fleet_dates_its_covenant_values() -> None:
    """THE ARTIFACT, NOT THE HELPER. A helper-level pin stays green if the call site is deleted —
    the #470 lesson. Asserted as a PHRASING-INDEPENDENT invariant on a LIVING artifact: at least
    one committed name's rendered digest carries a dated source, never a specific date.

    THE SKIP IS SCOPED TO THE DATA, NOT THE BEHAVIOUR — found by mutation. The first cut skipped
    whenever NO name carried a dated source, so deleting the call site made this test SKIP instead
    of fail: absent-because-no-data and absent-because-broken collapsed into one outcome, the exact
    class this repo keeps paying for. The denominator (names whose digest renders governing values
    at all) now decides the skip; the numerator decides the assertion."""
    with_values, with_dates = 0, 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        d = Dossier.model_validate(json.loads(p.read_text()))
        cs = d.mechanical.capital_structure
        if cs is None:
            continue
        lines = _covenant_summary_lines(cs)
        if not any(ln.lstrip().startswith("- **") and ":**" in ln for ln in lines):
            continue
        with_values += 1
        if any("per an 8-K filed" in ln for ln in lines):
            with_dates += 1
    if not with_values:
        pytest.skip("no committed name renders a governing covenant value")
    assert with_dates >= 1, (
        f"{with_values} committed name(s) render governing covenant values and NONE names its "
        f"source filing — the suffix is not reaching the page")
