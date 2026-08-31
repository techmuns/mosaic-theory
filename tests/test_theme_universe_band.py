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
from vinci.themes.detection import load_detection_universe
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


def _write_snapshots(snaps: Path, *, theme_rows: list[dict[str, object]] | None) -> None:
    snaps.mkdir(parents=True, exist_ok=True)
    (snaps / "securities.jsonl").write_text("\n".join(json.dumps(r) for r in [
        {"internal_id": "SEC-1", "eod_symbol": "AAA", "cik": "1", "name": "Small Co"},
        {"internal_id": "SEC-2", "eod_symbol": "MEGA", "cik": "2", "name": "Mega Co"},
    ]) + "\n")
    (snaps / "universe_snapshot.jsonl").write_text(json.dumps(
        {"as_of": "2026-08-31", "internal_id": "SEC-1", "in_universe": 1,
         "market_cap": 1.0e9}) + "\n")
    theme_file = snaps / "theme_universe_snapshot.jsonl"
    if theme_rows is None:
        theme_file.unlink(missing_ok=True)   # "band never built" must really remove it
    else:
        theme_file.write_text("\n".join(json.dumps(r) for r in theme_rows) + "\n")


def test_the_union_is_opt_in_per_call_site_not_per_checkout(tmp_path: Path) -> None:
    """THE DEFAULT IS PRIMARY-ONLY — corrected at review 2026-08-31, and this pin is the reason.

    The loader feeds two consumers with opposite sensitivities. The exposure scan reads each
    name's filings INDEPENDENTLY, so widening its population only adds names. Component A /
    stage-2 detection builds CROSS-SECTIONAL factors — the SMB leg is a tercile of the
    population's market caps — so unioning 810 names spanning $10B-$3.7T re-cuts those terciles
    and moves EVERY existing primary name's residual, its clusters, and its admission. The first
    version defaulted the union ON, which silently redefined that measurement for every caller.
    Opting in per call site is what keeps the band additive where it is safe and absent where it
    is not."""
    snaps = tmp_path / "snapshots"
    cfg = Config(data_dir=tmp_path)
    theme_row = [{"as_of": "2026-08-31", "internal_id": "SEC-2", "in_universe": 1,
                  "market_cap": 3.0e12}]

    _write_snapshots(snaps, theme_rows=theme_row)     # band BUILT and committed...
    names, as_of = load_detection_universe(cfg)       # ...and the DEFAULT still excludes it
    assert [n.ticker for n in names] == ["AAA"]
    assert {n.band for n in names} == {"primary"}
    assert as_of == date(2026, 8, 31)

    names, _ = load_detection_universe(cfg, include_theme_band=True)      # explicit opt-in
    assert sorted(n.ticker for n in names) == ["AAA", "MEGA"]
    assert {n.ticker: n.band for n in names} == {"AAA": "primary", "MEGA": "theme"}

    _write_snapshots(snaps, theme_rows=None)          # band never built: opting in is a no-op
    names, _ = load_detection_universe(cfg, include_theme_band=True)
    assert [n.ticker for n in names] == ["AAA"]


def test_only_the_exposure_scan_opts_into_the_band() -> None:
    """SOURCE PIN at the call sites, because the property is 'this population is not consulted'
    and only reading every caller can assert it. The exposure scan opts in; the residual
    detection path (`detect_themes` / `analyze_stage2`) must not — its factors are
    cross-sectional, so the band would move numbers that have nothing to do with it."""
    cli = (_REPO / "vinci/cli.py").read_text()
    fn = cli.split("def _cmd_themes_exposure(", 1)[1].split("\ndef ", 1)[0]
    assert "include_theme_band=True" in fn, "the exposure scan must opt in"
    # exactly ONE opt-in in the whole tree, so the band cannot spread by copy-paste. The loader's
    # own module is excluded by construction: it DEFINES the parameter.
    opt_ins = [rel for rel in ("vinci/cli.py", "vinci/themes/stage2.py", "vinci/themes/leaders.py",
                               "vinci/orchestrator.py", "vinci/screens/run.py")
               if "include_theme_band=True" in (_REPO / rel).read_text()]
    assert opt_ins == ["vinci/cli.py"], f"unexpected opt-in call sites: {opt_ins}"
    # and the loader's own default is the primary-only population
    loader = (_REPO / "vinci/themes/detection.py").read_text()
    assert "include_theme_band: bool = False" in loader


def test_a_name_in_both_bands_keeps_its_primary_identity(tmp_path: Path) -> None:
    """A name admitted by BOTH bands (a mid-cap that crossed $10B between builds) must appear
    ONCE, as primary. Two rows for one name would double it in every by-tag count the theme
    surfaces report, and the duplicate would carry the wrong provenance."""
    snaps = tmp_path / "snapshots"
    _write_snapshots(snaps, theme_rows=[
        {"as_of": "2026-08-31", "internal_id": "SEC-1", "in_universe": 1, "market_cap": 1.1e10},
        {"as_of": "2026-08-31", "internal_id": "SEC-2", "in_universe": 1, "market_cap": 3.0e12}])
    names, _ = load_detection_universe(Config(data_dir=tmp_path), include_theme_band=True)
    assert sorted(n.ticker for n in names) == ["AAA", "MEGA"]
    assert {n.ticker: n.band for n in names}["AAA"] == "primary"


def test_the_theme_band_only_stale_rows_are_filtered_to_its_own_latest_as_of(
    tmp_path: Path,
) -> None:
    """The two bands are built by SEPARATE runs, so their dates need not coincide: the theme rows
    are filtered to the THEME file's own latest as_of, never to the primary's. Pinned because
    filtering the theme rows on the primary date would silently empty the band whenever the two
    builds landed on different days — a whole population vanishing with no error."""
    snaps = tmp_path / "snapshots"
    _write_snapshots(snaps, theme_rows=[
        {"as_of": "2026-08-20", "internal_id": "SEC-2", "in_universe": 1, "market_cap": 2.9e12},
        {"as_of": "2026-08-28", "internal_id": "SEC-2", "in_universe": 1, "market_cap": 3.0e12}])
    names, as_of = load_detection_universe(Config(data_dir=tmp_path), include_theme_band=True)
    assert as_of == date(2026, 8, 31)                 # the PRIMARY population's vintage
    mega = [n for n in names if n.ticker == "MEGA"]
    assert len(mega) == 1 and mega[0].market_cap == 3.0e12   # the theme band's own latest row


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
