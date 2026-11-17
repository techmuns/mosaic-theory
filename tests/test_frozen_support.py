"""`tests/frozen_support.py` fails loud where it would otherwise mislead (W27 follow-up, STATE row
41 (a); review round 1 of #1098, items 4 and 7)."""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from tests.frozen_support import CUT, covered_where, newest_frozen_copy


def test_an_empty_walk_fails_loud_and_names_its_property() -> None:
    """(−) Item 4: a walk that finds no covered page with its property proves nothing, so it fails
    naming the property; it never skips and never passes."""
    with pytest.raises(AssertionError, match="no covered page carries a property no page has"):
        covered_where(lambda _t, _d: False, "carries a property no page has")


def test_a_walk_returns_every_covered_page_with_the_property() -> None:
    """(+) The control: an always-true property walks every covered page, sorted."""
    got = [t for t, _ in covered_where(lambda _t, _d: True, "is a page")]
    assert got == sorted(got) and len(got) >= 2


def test_the_newest_frozen_copy_is_by_date_never_by_name(tmp_path: Path) -> None:
    """(+ / −) Item 7: hex does not sort by time. Two cuts whose names sort the other way round
    from their dates, and a dated folder between them: the newest is the latest DATE."""
    src = CUT / "SMPL"
    for folder in ("cut-0aaa0000", "cut-ffff0000", "2026-11-20"):
        shutil.copytree(src, tmp_path / folder / "SMPL")
    cuts = {"0aaa0000": date(2026, 12, 15), "ffff0000": date(2026, 11, 1)}
    assert newest_frozen_copy("SMPL", tmp_path, cuts) == tmp_path / "cut-0aaa0000" / "SMPL"
    assert sorted(tmp_path.glob("*/SMPL/dossier.json"))[-1].parent.parent.name == "cut-ffff0000", \
        "the name order this replaces would have picked the OLDER cut"
    cuts["0aaa0000"] = date(2026, 10, 1)
    assert newest_frozen_copy("SMPL", tmp_path, cuts) == tmp_path / "2026-11-20" / "SMPL"


def test_a_cut_with_no_date_cannot_be_ordered(tmp_path: Path) -> None:
    """(−) Item 7: a cut the registry gives no date raises, never sorts by name."""
    shutil.copytree(CUT / "SMPL", tmp_path / "cut-0aaa0000" / "SMPL")
    with pytest.raises(ValueError, match="cut-0aaa0000 states no date"):
        newest_frozen_copy("SMPL", tmp_path, {})
    with pytest.raises(FileNotFoundError, match="no frozen copy of ZZZZ"):
        newest_frozen_copy("ZZZZ", tmp_path, {})
