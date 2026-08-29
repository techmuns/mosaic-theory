"""Thesis-card + economics-roll-up mirrors and their twin pins (brief Items 1/4).

Three defect classes pinned: (1) the build must place mirrors by the card's MACHINE-STAMPED slug
and skip slugless/archived cards (the #412 mirror-binding class); (2) every committed card's
stamp must match the registry (drift guard — build.py is stdlib-only and cannot check this
itself); (3) the JS surface must read exactly the keys the models emit, and the loud stamp's
wording must be the ONE shared constant (twin-wording pin — the py gate and the page must not
drift into two stamps). Committed-corpus pins assert ABSENCE-PARITY while no card is declared
yet: zero data-side cards must mean zero mirrors, so the test always asserts something real.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from vinci.themes.drivers import DRIVER_SPECS
from vinci.themes.rollup import MemberEconomics, ThemeEconomicsRollup
from vinci.themes.thesis import THESIS_UNSTATED, ThemeThesis

_REPO = Path(__file__).resolve().parents[1]
_BUILD_PY = _REPO / "frontend" / "build.py"
_THEME_JS = _REPO / "frontend" / "views" / "themes" / "theme.js"
_SNAP_JS = _REPO / "frontend" / "lib" / "snapshots.js"


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("_thesis_mirror_build", _BUILD_PY)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_emitters_mirror_by_stamped_slug_and_skip_slugless_and_archive(
    tmp_path: Path, monkeypatch: Any
) -> None:
    bd = _load_build()
    monkeypatch.setattr(bd, "ROOT", tmp_path)
    monkeypatch.setattr(bd, "OUT_THEMES", tmp_path / "frontend" / "themes")
    src = tmp_path / "data" / "themes" / "thesis"
    (src / "archive").mkdir(parents=True)
    (src / "with-slug.json").write_text(json.dumps({"mirror_slug": "slugged", "x": 1}))
    (src / "no-slug.json").write_text(json.dumps({"mirror_slug": "", "x": 2}))
    # a superseded card in archive/ must never reach the page
    (src / "archive" / "with-slug-2026-01-01.json").write_text(
        json.dumps({"mirror_slug": "slugged", "x": 0}))
    assert bd.emit_theme_thesis() == ["slugged"]
    out = tmp_path / "frontend" / "themes" / "thesis"
    assert sorted(p.name for p in out.glob("*.json")) == ["slugged.json"]
    # VERBATIM — the build is a mirror, never a second author
    assert (out / "slugged.json").read_text() == (src / "with-slug.json").read_text()
    # economics: same discipline, same shape
    esrc = tmp_path / "data" / "themes" / "economics"
    esrc.mkdir(parents=True)
    (esrc / "d.json").write_text(json.dumps({"mirror_slug": "d-slug"}))
    assert bd.emit_theme_economics() == ["d-slug"]
    assert (tmp_path / "frontend" / "themes" / "economics" / "d-slug.json").exists()


def test_a_deleted_or_reslugged_card_does_not_leave_a_stale_mirror(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """REVIEW FINDING — the emitters copied without pruning, so a card deleted (or re-slugged)
    data-side left its mirror behind and the page kept rendering a declared thesis for a driver
    that has none: presence-when-absent, the exact inversion of the loud stamp. Safe to prune here
    because these sources are COMMITTED (unlike build_themes' git-ignored freeze artifacts)."""
    bd = _load_build()
    monkeypatch.setattr(bd, "ROOT", tmp_path)
    monkeypatch.setattr(bd, "OUT_THEMES", tmp_path / "frontend" / "themes")
    src = tmp_path / "data" / "themes" / "thesis"
    src.mkdir(parents=True)
    (src / "a.json").write_text(json.dumps({"mirror_slug": "alpha"}))
    (src / "b.json").write_text(json.dumps({"mirror_slug": "beta"}))
    assert sorted(bd.emit_theme_thesis()) == ["alpha", "beta"]
    out = tmp_path / "frontend" / "themes" / "thesis"
    # the operator deletes one card, and re-slugs the other
    (src / "a.json").unlink()
    (src / "b.json").write_text(json.dumps({"mirror_slug": "beta-2"}))
    assert bd.emit_theme_thesis() == ["beta-2"]
    assert sorted(p.name for p in out.glob("*.json")) == ["beta-2.json"], (
        "a stale mirror survived — the page would render a card its source no longer declares")
    # every card withdrawn ⇒ the whole mirror dir goes, not an empty shell serving stale files
    (src / "b.json").unlink()
    assert bd.emit_theme_thesis() == []
    assert not out.exists() or not list(out.glob("*.json"))


def test_emitters_are_noops_when_no_source_exists(tmp_path: Path, monkeypatch: Any) -> None:
    bd = _load_build()
    monkeypatch.setattr(bd, "ROOT", tmp_path)
    monkeypatch.setattr(bd, "OUT_THEMES", tmp_path / "frontend" / "themes")
    assert bd.emit_theme_thesis() == []
    assert bd.emit_theme_economics() == []
    assert not (tmp_path / "frontend" / "themes").exists()


def test_committed_cards_stamps_match_the_registry_or_absence_parity_holds() -> None:
    """The drift guard build.py cannot run itself (stdlib-only). With zero cards declared the
    pin is ABSENCE-PARITY — no data-side card ⇒ no mirror — so it is never vacuous."""
    data_side = sorted((_REPO / "data" / "themes" / "thesis").glob("*.json"))
    mirrors = sorted((_REPO / "frontend" / "themes" / "thesis").glob("*.json"))
    expected_mirrors = set()
    for p in data_side:
        card = ThemeThesis.model_validate_json(p.read_text())
        assert card.driver_key == p.stem
        assert card.mirror_slug == DRIVER_SPECS[card.driver_key].mirror_slug
        if card.mirror_slug:
            expected_mirrors.add(f"{card.mirror_slug}.json")
    assert {m.name for m in mirrors} == expected_mirrors


def test_committed_rollups_stamps_match_the_registry_or_absence_parity_holds() -> None:
    data_side = sorted((_REPO / "data" / "themes" / "economics").glob("*.json"))
    mirrors = sorted((_REPO / "frontend" / "themes" / "economics").glob("*.json"))
    expected = set()
    for p in data_side:
        r = ThemeEconomicsRollup.model_validate_json(p.read_text())
        assert r.driver_key == p.stem
        assert r.mirror_slug == DRIVER_SPECS[r.driver_key].mirror_slug
        if r.mirror_slug:
            expected.add(f"{r.mirror_slug}.json")
    assert {m.name for m in mirrors} == expected


def test_the_stamp_wording_is_the_one_shared_constant() -> None:
    """TWIN-WORDING PIN: the page's loud stamp and the py constant must be the same string — two
    wordings of the blocking state is how a reader learns to ignore one of them."""
    assert THESIS_UNSTATED in _THEME_JS.read_text()


def test_theme_js_reads_only_keys_the_models_emit() -> None:
    """SOURCE-STRING PIN (the card-verdict-keys pattern): every model field the page renders must
    exist on the emitting model, and the getters the page imports must exist in snapshots.js —
    so a rename on either side reddens here instead of rendering undefined."""
    js = _THEME_JS.read_text()
    snap = _SNAP_JS.read_text()
    for fn in ("getThemeThesis", "getThemeEconomics"):
        assert f"export async function {fn}" in snap
        assert fn in js
    card_keys = ("declared_date", "mechanism", "market_mistake", "null_thesis",
                 "first_confirming", "falsifiers", "note")
    for k in card_keys:
        assert k in ThemeThesis.model_fields
        assert k in js, f"theme.js never renders card field {k!r}"
    econ_keys = ("n_members", "n_underwritten", "membership_note", "as_of", "rows")
    for k in econ_keys:
        assert k in ThemeEconomicsRollup.model_fields
        assert k in js
    row_keys = ("ticker", "substructure_tag", "underwritten", "gate_regime", "asymmetry_tier",
                "return_tier", "eligible", "eligible_undefined", "underwrite_date",
                "ev_gap", "ev_gap_status", "ev_gap_reason", "ev_gap_vintages")
    for k in row_keys:
        assert k in MemberEconomics.model_fields
        assert k in js, f"theme.js never renders roll-up row field {k!r}"
