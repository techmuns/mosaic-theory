"""The PARALLEL THEME BAND (operator ruling 2026-08-31) — a second, larger population read ONLY at
the theme altitude.

WHY A SECOND BAND RATHER THAN A WIDER ONE. The primary band IS the forward-validation population:
screens, ranker and the BUY−AVOID spread have accumulated against that membership since the clock
started, so widening it mid-flight would change the experiment's population mid-experiment. The
parallel band adds reach for theme research without touching the record.

THE LOAD-BEARING PROPERTY IS THEREFORE CONTAMINATION, NOT COVERAGE — every pin below asks the same
question from a different side: can a theme-band name reach the decision path? The coverage pin
(megacaps are admitted at all) is the cheap half; the refusal pins are the half that matters.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from vinci.config import Config
from vinci.schemas.envelope import DataField, SourceTier
from vinci.store import Store
from vinci.universe import BUILD_THEME_UNIVERSE_TABLES, BUILD_UNIVERSE_TABLES, UNIVERSE_BANDS

_REPO = Path(__file__).resolve().parents[1]


def _cap(v: float) -> DataField[float]:
    return DataField.present(v, as_of=date(2026, 8, 31), source="DERIVED", tier=SourceTier.DERIVED)


def test_the_two_bands_are_separate_populations_in_the_store(tmp_path: Path) -> None:
    """THE CORE REFUSAL: a name recorded in the theme band is invisible to every primary-band
    read. `latest_universe` DEFAULTS to primary precisely so a decision-path caller cannot opt
    into the theme band by forgetting an argument — that default is asserted here, not assumed."""
    with Store(tmp_path / "t.db") as store:
        store.record_universe(as_of=date(2026, 8, 31), internal_id="SEC-PRIMARY",
                              in_universe=True, market_cap=_cap(1e9))
        store.record_universe(as_of=date(2026, 8, 31), internal_id="SEC-MEGACAP",
                              in_universe=True, market_cap=_cap(3e12), band="theme")
        # the decision-path read — the default — sees ONLY the primary name
        assert store.latest_universe(date(2026, 8, 31)) == ["SEC-PRIMARY"]
        assert store.get_universe(date(2026, 8, 31)) == ["SEC-PRIMARY"]
        # the theme altitude, asking explicitly, sees only its own
        assert store.latest_universe(date(2026, 8, 31), band="theme") == ["SEC-MEGACAP"]
        # and clearing one band leaves the other standing (a theme rebuild must not wipe the
        # population the spread is accumulating against)
        store.clear_universe(band="theme")
        assert store.latest_universe(date(2026, 8, 31), band="theme") == []
        assert store.latest_universe(date(2026, 8, 31)) == ["SEC-PRIMARY"]


def test_an_unknown_band_raises_rather_than_reading_the_wrong_population(tmp_path: Path) -> None:
    """A typo'd band must be LOUD. Silently defaulting to primary would mean a theme write landing
    in the validation population — the exact contamination this design exists to prevent."""
    with Store(tmp_path / "t.db") as store:
        with pytest.raises(ValueError, match="unknown universe band"):
            store.latest_universe(date(2026, 8, 31), band="themes")   # note the typo
        with pytest.raises(ValueError, match="unknown universe band"):
            store.record_universe(as_of=date(2026, 8, 31), internal_id="X", in_universe=True,
                                  market_cap=_cap(1.0), band="megacap")


def test_the_builder_exports_the_bands_to_different_files() -> None:
    """SOURCE-ORDER PIN. The two export sets share the accumulate-only entity master and differ
    ONLY in the membership table, so a theme build can never rewrite `universe_snapshot.jsonl` —
    the committed file the forward record reads."""
    assert "universe_snapshot" in BUILD_UNIVERSE_TABLES
    assert "universe_snapshot" not in BUILD_THEME_UNIVERSE_TABLES
    assert "theme_universe_snapshot" in BUILD_THEME_UNIVERSE_TABLES
    assert "theme_universe_snapshot" not in BUILD_UNIVERSE_TABLES
    # the entity master is SHARED (an identity is a fact about the world, not about a band)
    for t in ("issuers", "securities"):
        assert t in BUILD_UNIVERSE_TABLES and t in BUILD_THEME_UNIVERSE_TABLES
    # and each band writes its own stats file — one count, one population
    assert (UNIVERSE_BANDS["primary"][2] != UNIVERSE_BANDS["theme"][2])


def test_the_theme_band_is_wider_and_otherwise_identical() -> None:
    """The bands differ in CAP BOUNDS ONLY. Every other gate — exchanges, ADV floor, the
    operating-company SIC denylist, the instrument-type allowlist — is the same discipline, so the
    parallel band cannot become a back door for the junk those gates exist to exclude."""
    cfg = Config()
    p, t = cfg.universe, cfg.theme_universe
    assert t.market_cap_min_usd >= p.market_cap_max_usd   # the bands meet, they do not overlap
    assert t.market_cap_max_usd > t.market_cap_min_usd
    assert (t.exchanges, t.adv_floor_usd, t.excluded_sic_codes, t.allowed_security_types) == (
        p.exchanges, p.adv_floor_usd, p.excluded_sic_codes, p.allowed_security_types)


def test_no_decision_path_module_reads_the_theme_band() -> None:
    """THE CONTAMINATION SWEEP, at the source level: the screen / rank / ledger / scoring modules
    must never name the theme band. A grep-level pin is the honest layer here — the property is
    'this population is not consulted', and only reading every call site can assert that."""
    for rel in ("screens/run.py", "rank", "ledger", "scoring"):
        target = _REPO / "vinci" / rel
        files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        for f in files:
            src = f.read_text()
            assert 'band="theme"' not in src, f"{f.name} reads the theme band"
            assert "theme_universe" not in src, f"{f.name} names the theme-band population"


def test_a_full_export_refuses_to_blank_a_committed_population(tmp_path: Path) -> None:
    """REVIEW FINDING (2026-08-31), the one with a reachable caller: `vinci screen` full-exports
    WITHOUT rebuilding the DB from snapshots first, and no build path seeds the theme table. So a
    fresh checkout doing build-universe → screen exported ZERO theme rows over the committed 816
    — and the failure was silent in both directions: nothing raised, and the loader reads a
    present-but-empty file as "band not built" and reverts to primary-only.

    The guard is scoped to POPULATION tables, which are never legitimately empty once committed;
    the no-row-drop tables keep their own stricter rule, and a table that may legitimately empty
    (a screen finding no candidates) is deliberately NOT in this set."""
    snaps = tmp_path / "snapshots"
    snaps.mkdir(parents=True)
    committed = snaps / "theme_universe_snapshot.jsonl"
    committed.write_text(json.dumps(
        {"as_of": "2026-08-31", "internal_id": "SEC-MEGA", "in_universe": 1,
         "market_cap": 3.0e12, "source": "DERIVED", "coverage_status": "present"}) + "\n")

    with Store(tmp_path / "t.db") as store:          # a DB that never loaded the theme table
        store.record_universe(as_of=date(2026, 8, 31), internal_id="SEC-PRIMARY",
                              in_universe=True, market_cap=_cap(1e9))
        with pytest.raises(ValueError, match="refusing to truncate"):
            store.export_snapshots(snaps)            # the FULL export — no tables= subset
        # the committed population is still on disk, unblanked
        assert len([x for x in committed.read_text().splitlines() if x.strip()]) == 1
        # and an explicit subset that omits it still exports fine (the documented way out)
        store.export_snapshots(snaps, tables=["universe_snapshot"])
        assert (snaps / "universe_snapshot.jsonl").read_text().strip()
