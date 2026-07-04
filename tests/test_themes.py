"""Regression tests for the theme-detection layer (Component A, Stage 1).

The load-bearing ones, per the verification gate:
- the multi-factor OLS + the NEW sector leg done properly (loading ESTIMATED, not a 1:1
  cohort-mean);
- the vol-strip SELECTIVITY (the Part-4 mechanism: a high-vol speculative blob DISSOLVES under the
  vol strip while a diffuse low-vol theme SURVIVES and a real high-vol sub-theme is retained);
- the admissibility gates, fail-loud signals, the candidate-linkage surface;
- the assemble-not-conclude structural guard (no verdict/score/rank/driver field) and the
  no-forward-returns import guard (mirrors the ranker's AST guard).
"""

from __future__ import annotations

import ast
import math
import statistics
from datetime import date, timedelta
from pathlib import Path
from random import Random

from vinci.eod.client import EodClient, RawBar
from vinci.themes import cluster as cl
from vinci.themes.detection import _Name, _persistence, pull_closes
from vinci.themes.gates import evaluate_admissibility
from vinci.themes.linkage import candidate_linkage
from vinci.themes.residualize import (
    _ols_residuals,
    build_factors,
    daily_returns,
    realized_vol,
    residualize,
    solve_symmetric,
)
from vinci.themes.schemas import (
    AdmissibilityReport,
    CandidateTheme,
    FactorBasis,
    StrengthSignals,
    ThemeMember,
    Trajectory,
    WindowSpec,
)
from vinci.themes.signals import _horizon_return, compute_strength_signals

_THEMES_DIR = Path(__file__).resolve().parent.parent / "vinci" / "themes"


def _cal(n: int) -> list[date]:
    base = date(2025, 1, 1)
    return [base + timedelta(days=i) for i in range(n)]


def _corr(x: dict[date, float], y: dict[date, float]) -> float:
    common = sorted(set(x) & set(y))
    a = [x[d] for d in common]
    b = [y[d] for d in common]
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    cov = sum((p - ma) * (q - mb) for p, q in zip(a, b, strict=True))
    va = sum((p - ma) ** 2 for p in a)
    vb = sum((q - mb) ** 2 for q in b)
    return cov / math.sqrt(va * vb)


# --------------------------------------------------------------------------------------------------
# Linear algebra / OLS
# --------------------------------------------------------------------------------------------------
def test_solve_symmetric_recovers_known_solution() -> None:
    # A x = b with a known x = [1, -2, 3]
    a = [[4.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]]
    x = [1.0, -2.0, 3.0]
    b = [sum(a[i][j] * x[j] for j in range(3)) for i in range(3)]
    sol = solve_symmetric(a, b)
    assert sol is not None
    assert all(abs(sol[i] - x[i]) < 1e-9 for i in range(3))


def test_solve_symmetric_singular_returns_none() -> None:
    assert solve_symmetric([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0]) is None


def test_daily_returns_does_not_span_gaps() -> None:
    cal = _cal(5)
    closes = {cal[0]: 100.0, cal[1]: 110.0, cal[3]: 120.0, cal[4]: 132.0}  # cal[2] missing
    r = daily_returns(closes, cal)
    assert cal[1] in r and abs(r[cal[1]] - 0.10) < 1e-12  # 100→110
    assert cal[2] not in r and cal[3] not in r  # the gap day and the day after the gap are skipped
    assert cal[4] in r and abs(r[cal[4]] - 0.10) < 1e-12  # 120→132


# --------------------------------------------------------------------------------------------------
# The SECTOR leg, done properly: the loading is ESTIMATED (not a 1:1 cohort-mean subtraction)
# --------------------------------------------------------------------------------------------------
def test_sector_leg_estimates_loading_not_unit() -> None:
    """A name with sector beta 2.0 (not 1) is fully residualized — the residual is ⊥ the sector.

    The throwaway spikes subtracted the cohort mean 1:1 (implicit β=1) → a β=2 name would keep a
    residual still correlated with the sector. The joint-OLS leg estimates β≈2 and removes it.
    """
    cal = _cal(180)
    rng = Random(1)
    sector = {d: rng.gauss(0, 0.02) for d in cal}
    days = sorted(sector)
    y = [2.0 * sector[d] + rng.gauss(0, 0.01) for d in days]
    resid = _ols_residuals(days, y, [[sector[d] for d in days]])
    assert resid is not None
    assert abs(_corr(resid, sector)) < 0.12  # β=2 estimated and stripped → residual ⊥ sector


def test_sector_strip_leaves_cross_sector_theme() -> None:
    """Same-sector names with no shared theme decorrelate after the sector strip; a cross-cutting
    theme (shared variance BEYOND the sector) survives — criterion 3 done properly."""
    cal = _cal(200)
    rng = Random(2)
    market = dict.fromkeys(cal, 0.0)  # isolate the sector leg (zero-variance market col is dropped)
    sector_common = {d: rng.gauss(0, 0.02) for d in cal}
    theme = {d: rng.gauss(0, 0.02) for d in cal}
    returns: dict[str, dict[date, float]] = {}
    sector_of: dict[str, str] = {}
    # 8 names in ONE sector; A/B share only the sector, C/D ALSO share a theme beyond it.
    for nm, has_theme in [("A", False), ("B", False), ("C", True), ("D", True),
                          ("E", False), ("F", False), ("G", False), ("H", False)]:
        beta = 0.8 + 0.4 * rng.random()
        returns[nm] = {
            d: beta * sector_common[d] + (theme[d] if has_theme else 0.0) + rng.gauss(0, 0.008)
            for d in cal
        }
        sector_of[nm] = "Technology"
    caps = dict.fromkeys(returns, 1.0)
    factors = build_factors(
        returns, market_returns=market, sector_of=sector_of, market_cap_of=caps,
        calendar=cal, basis=FactorBasis.MARKET_SECTOR,
    )
    resid, dropped = residualize(returns, factors, sector_of)
    assert not dropped
    ab = _corr(resid["A"], resid["B"])  # only the sector linked them → stripped → ~0
    cd = _corr(resid["C"], resid["D"])  # shared theme beyond the sector survives
    assert abs(ab) < 0.25
    assert cd > 0.55
    assert cd > ab + 0.3


# --------------------------------------------------------------------------------------------------
# The vol-strip SELECTIVITY — the Part-4 reproduction on synthetic data
# --------------------------------------------------------------------------------------------------
def _vol_strip_universe() -> tuple[
    dict[str, dict[date, float]], dict[str, str], dict[str, float], dict[date, float], list[date]
]:
    cal = _cal(220)
    rng = Random(7)
    market = {d: rng.gauss(0, 0.008) for d in cal}
    h = {d: rng.gauss(0, 0.02) for d in cal}  # housing theme (low amplitude → low total vol)
    v = {d: rng.gauss(0, 0.06) for d in cal}  # speculative high-vol GLUE (large)
    q = {d: rng.gauss(0, 0.05) for d in cal}  # a real high-vol sub-theme (quantum), orthogonal to v
    # 10 distinct broad sectors. The rule that mirrors a real cross-taxonomy theme: ≤1 member of a
    # given theme per broad sector, so each member's leave-one-out sector cohort is theme-free (the
    # broad 150-name GICS cohort barely contains a cross-taxonomy theme) — the sector leg strips
    # market/sector beta WITHOUT absorbing the theme factor.
    sectors = [
        "Technology", "Health Care", "Real Estate", "Financials", "Energy",
        "Materials", "Communication Services", "Utilities", "Consumer Staples",
        "Consumer Discretionary",
    ]
    returns: dict[str, dict[date, float]] = {}
    sector_of: dict[str, str] = {}
    caps: dict[str, float] = {}

    def add(nm: str, build: dict[date, float], sec: str) -> None:
        returns[nm] = build
        sector_of[nm] = sec
        caps[nm] = 1e8 + rng.random() * 9e9

    # Housing: 8 names, one per sector 0..7 (cross-taxonomy), low vol
    for i in range(8):
        add(f"H{i}", {d: market[d] + h[d] + rng.gauss(0, 0.01) for d in cal}, sectors[i])
    # Pure speculative blob: 8 names sharing only v (high vol), one per sector 0..7
    for i in range(8):
        add(f"S{i}", {d: market[d] + v[d] + rng.gauss(0, 0.02) for d in cal}, sectors[i])
    # Quantum: 3 high-vol names sharing v AND a strong extra q, in distinct sectors (8, 9, 0)
    for i, sec in enumerate((sectors[8], sectors[9], sectors[0])):
        add(f"Q{i}", {d: market[d] + v[d] + q[d] + rng.gauss(0, 0.015) for d in cal}, sec)
    # Independent fillers, ~3 per sector — enough to anchor each cohort to ~market while
    # keeping the speculative names dominant in the high-vol tercile (so the vol factor ≈ v).
    for i in range(30):
        add(f"F{i}", {d: market[d] + rng.gauss(0, 0.02) for d in cal}, sectors[i % 10])
    return returns, sector_of, caps, market, cal


def _cluster_with(members: set[str], clusters: list[cl.RawCluster], frac: float) -> bool:
    return any(len(set(c.members) & members) >= frac * len(members) for c in clusters)


def test_vol_strip_is_selective() -> None:
    returns, sector_of, caps, market, cal = _vol_strip_universe()
    housing = {f"H{i}" for i in range(8)}
    spec = {f"S{i}" for i in range(8)}
    quantum = {f"Q{i}" for i in range(3)}

    def run(basis: FactorBasis) -> list[cl.RawCluster]:
        f = build_factors(
            returns, market_returns=market, sector_of=sector_of, market_cap_of=caps,
            calendar=cal, basis=basis,
        )
        resid, _ = residualize(returns, f, sector_of)
        return cl.find_clusters(resid, cal, min_breadth=3)

    r1 = run(FactorBasis.MARKET_SECTOR)  # vol NOT stripped → the blob is present
    r2 = run(FactorBasis.FULL)  # +size+vol → the speculative glue is removed

    # R1: housing is its own cluster; the speculative names cohere into a blob (spec+quantum via v)
    assert _cluster_with(housing, r1, 0.7), "housing should cluster under R1"
    assert any(len(set(c.members) & (spec | quantum)) >= 10 for c in r1), "R1 shows the blob"

    # R2: the vol strip DISSOLVES the pure-speculative blob (it no longer even forms a basket),
    # but housing (low-vol, diffuse) SURVIVES
    assert _cluster_with(housing, r2, 0.7), "housing must survive the vol strip"
    assert not any(len(set(c.members) & spec) >= 3 for c in r2), "the pure-spec blob must dissolve"
    # the real high-vol sub-theme (quantum) is RETAINED — not collateral damage of the strip
    assert _cluster_with(quantum, r2, 1.0), "the real quantum sub-theme must be retained under R2"


def test_realized_vol_orders_high_above_low() -> None:
    cal = _cal(120)
    rng = Random(3)
    low = {d: rng.gauss(0, 0.01) for d in cal}
    high = {d: rng.gauss(0, 0.06) for d in cal}
    rv_low, rv_high = realized_vol(low), realized_vol(high)
    assert rv_low is not None and rv_high is not None and rv_high > rv_low


# --------------------------------------------------------------------------------------------------
# Clustering, coherence, gates
# --------------------------------------------------------------------------------------------------
def test_find_clusters_separates_two_groups() -> None:
    cal = _cal(150)
    rng = Random(5)
    fa = {d: rng.gauss(0, 0.03) for d in cal}
    fb = {d: rng.gauss(0, 0.03) for d in cal}
    resid: dict[str, dict[date, float]] = {}
    for i in range(4):
        resid[f"A{i}"] = {d: fa[d] + rng.gauss(0, 0.01) for d in cal}
    for i in range(3):
        resid[f"B{i}"] = {d: fb[d] + rng.gauss(0, 0.01) for d in cal}
    resid["X"] = {d: rng.gauss(0, 0.03) for d in cal}  # a lone noise name
    clusters = cl.find_clusters(resid, cal, min_breadth=3)
    groups = [set(c.members) for c in clusters]
    assert {"A0", "A1", "A2", "A3"} in groups
    assert {"B0", "B1", "B2"} in groups
    assert all("X" not in g for g in groups)


def test_gates_breadth_coherence_persistence() -> None:
    coherent = cl.RawCluster(
        members=["a", "b", "c", "d"], coherence=0.55, tau_stability=[0.45, 0.5]
    )
    # all pass
    ok = evaluate_admissibility(coherent, member_retention=0.8, persistence_note="ok")
    assert ok.admissible
    # breadth fail (a pair)
    pair = cl.RawCluster(members=["a", "b"], coherence=0.7, tau_stability=[0.5])
    assert not evaluate_admissibility(pair, member_retention=0.9, persistence_note="x").breadth_pass
    # coherence fail (loosely chained)
    chained = cl.RawCluster(members=["a", "b", "c"], coherence=0.18, tau_stability=[0.5])
    chained_report = evaluate_admissibility(chained, member_retention=0.9, persistence_note="x")
    assert not chained_report.coherence_pass
    # persistence fail (a blip)
    blip = evaluate_admissibility(coherent, member_retention=0.2, persistence_note="x")
    assert not blip.persistence_pass and not blip.admissible


def test_persistence_unevaluable_window_is_not_a_pass() -> None:
    """A window too short to evaluate persistence must NOT auto-pass it (fail-loud, not silent 1.0).

    Regression for the review finding: ``_persistence`` used to return 1.0 retention for every
    cluster when ``len(calendar) <= persist_days``, silently admitting themes on an untested
    criterion (reachable via ``--window-days``)."""
    clusters = [
        cl.RawCluster(members=["a", "b", "c"], coherence=0.6),
        cl.RawCluster(members=["d", "e", "f"], coherence=0.6),
    ]
    short_cal = _cal(50)  # 50 < persist_days (126) → un-evaluable
    ret = _persistence(
        clusters, {}, iwm={}, market_caps={}, sector_of={}, calendar=short_cal,
        persist_days=126, basis=FactorBasis.FULL,
    )
    assert ret == {0: None, 1: None}  # None = un-evaluable, NOT a fabricated 1.0
    # and the gate treats None as fail-loud (NOT admissible), with an honest reason
    rep = evaluate_admissibility(clusters[0], member_retention=None, persistence_note="x")
    assert not rep.persistence_pass and not rep.admissible
    assert any("NOT evaluable" in r for r in rep.fail_reasons)


# --------------------------------------------------------------------------------------------------
# §7.1 strength signals — fail-loud, trailing-only
# --------------------------------------------------------------------------------------------------
def test_strength_signals_present_and_fail_loud() -> None:
    cal = _cal(120)
    rng = Random(9)
    closes = {
        nm: {d: 10.0 * (1.0 + 0.0005 * i + rng.gauss(0, 0.01)) for i, d in enumerate(cal)}
        for nm in ("A", "B", "C")
    }
    market = {d: 100.0 * (1.0 + 0.0002 * i) for i, d in enumerate(cal)}
    sig = compute_strength_signals(
        ["A", "B", "C"], closes, market_closes=market, calendar=cal, reference_date=cal[-1]
    )
    # momentum + rel-strength are 1/3/6/12mo trajectories (shortest→longest), each horizon present
    assert [lbl for lbl, _ in sig.momentum.ordered()] == ["1mo", "3mo", "6mo", "12mo"]
    assert all(f.is_known for _, f in sig.momentum.ordered())
    assert all(f.is_known for _, f in sig.rel_strength_vs_market.ordered())
    assert sig.crowding_overextension.is_known
    # too little history → UNKNOWN, never a partial-window number
    short = _cal(5)
    sig2 = compute_strength_signals(
        ["A"], {"A": dict.fromkeys(short, 10.0)}, market_closes=dict.fromkeys(short, 100.0),
        calendar=short, reference_date=short[-1],
    )
    assert not sig2.crowding_overextension.is_known
    assert not sig2.momentum.h12mo.is_known  # 1 member < floor → UNKNOWN, not a fabricated value


def test_horizon_return_fail_loud_on_short_coverage() -> None:
    """A name without history spanning a horizon yields UNKNOWN for THAT horizon (fail-loud)."""
    cal = _cal(252)
    full = {d: 100.0 + i * 0.1 for i, d in enumerate(cal)}
    ipo = {d: 50.0 + i * 0.2 for i, d in enumerate(cal) if i >= 252 - 80}  # only the last 80 days
    assert all(_horizon_return(full, cal, n) is not None for n in (21, 63, 126, 252))
    assert _horizon_return(ipo, cal, 21) is not None  # 1mo: covered
    assert _horizon_return(ipo, cal, 63) is not None  # 3mo: covered (80 ≥ 63)
    assert _horizon_return(ipo, cal, 126) is None  # 6mo: history doesn't span it → UNKNOWN
    assert _horizon_return(ipo, cal, 252) is None  # 12mo: UNKNOWN


def test_trajectory_reconciles_and_does_not_collapse() -> None:
    """The 12mo horizon reconciles to the median full-window return; no collapse field."""
    cal = _cal(252)
    members = {
        "A": {d: 100.0 * (1.0 + 0.001 * i) for i, d in enumerate(cal)},
        "B": {d: 100.0 * (1.0 - 0.0005 * i) for i, d in enumerate(cal)},
        "C": {d: 100.0 * (1.0 + 0.0002 * i) for i, d in enumerate(cal)},
    }
    market = {d: 100.0 * (1.0 + 0.0003 * i) for i, d in enumerate(cal)}
    sig = compute_strength_signals(list(members), members, market_closes=market, calendar=cal,
                                   reference_date=cal[-1])

    def full_ret(c: dict[date, float]) -> float:
        seq = [c[d] for d in cal if d in c]
        return seq[-1] / seq[0] - 1.0

    exp_mom = statistics.median(full_ret(c) for c in members.values())
    assert sig.momentum.h12mo.value is not None
    assert abs(sig.momentum.h12mo.value - exp_mom) < 1e-9  # 12mo = median full-window return
    assert sig.rel_strength_vs_market.h12mo.value is not None
    assert abs(sig.rel_strength_vs_market.h12mo.value - (exp_mom - full_ret(market))) < 1e-9

    # HARD CONSTRAINT: the trajectory is exactly four horizons — no slope/composite/score/rank field
    assert set(Trajectory.model_fields) == {"h1mo", "h3mo", "h6mo", "h12mo"}
    for banned in ("slope", "score", "composite", "rank", "trend", "coef", "verdict"):
        assert not hasattr(Trajectory, banned)
        assert banned not in Trajectory.model_fields


# --------------------------------------------------------------------------------------------------
# Criterion-1 candidate-linkage surface (proposes; never names a driver)
# --------------------------------------------------------------------------------------------------
def test_candidate_linkage_flags_cross_taxonomy() -> None:
    members = [
        ThemeMember(ticker="RGTI", name="Rigetti", cik="1", sic="7371", sector="Technology",
                    sic_source_ref="r"),
        ThemeMember(ticker="QUBT", name="Quantum Computing", cik="2", sic="7372",
                    sector="Technology", sic_source_ref="r"),
        ThemeMember(ticker="KBH", name="KB Home", cik="3", sic="1531",
                    sector="Consumer Discretionary", sic_source_ref="r"),
    ]
    link = candidate_linkage(members)
    assert link.crosses_taxonomy
    assert set(link.distinct_sics) == {"7371", "7372", "1531"}
    assert "CROSS-TAXONOMY" in link.shared_note
    # the machine proposes — it must not emit a named driver verdict
    assert "quantum" not in link.shared_note.lower()


# --------------------------------------------------------------------------------------------------
# Guards — assemble-not-conclude (schema) + no-forward-returns (imports)
# --------------------------------------------------------------------------------------------------
_FORBIDDEN_FIELD_TOKENS = (
    "verdict", "recommendation", "buy", "sell", "avoid", "driver_name",
    "theme_score", "priority", "probability", "direction", "target_price",
)


def _all_field_names(model: type) -> set[str]:
    names: set[str] = set()
    fields = getattr(model, "model_fields", None)
    if not fields:
        return names
    for fname, info in fields.items():
        names.add(fname)
        ann = info.annotation
        for sub in (ann, *getattr(ann, "__args__", ())):
            if isinstance(sub, type) and hasattr(sub, "model_fields"):
                names |= _all_field_names(sub)
    return names


def test_schema_cannot_conclude() -> None:
    """No theme record has a field that lets the machine conclude (verdict/score/rank/driver).

    Mirrors the dossier's no-verdict-field guard — concluding is structurally impossible, not merely
    avoided by convention."""
    names = _all_field_names(CandidateTheme) | _all_field_names(StrengthSignals) | _all_field_names(
        AdmissibilityReport
    )
    assert names  # guard is non-vacuous
    for n in names:
        for tok in _FORBIDDEN_FIELD_TOKENS:
            assert tok not in n.lower(), f"field {n!r} smuggles a conclusion ({tok})"


def test_themes_reads_no_forward_returns() -> None:
    """``vinci.themes`` imports no ``scoring``/``ledger`` — no code path can read forward returns
    when setting parameters (the ranker's no-forward-returns AST guard, applied here)."""
    checked = 0
    for path in _THEMES_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                assert "vinci.scoring" not in m and "vinci.ledger" not in m, (
                    f"{path.name} imports {m}"
                )
        checked += 1
    assert checked >= 6


def test_pull_closes_keeps_benchmark_separate() -> None:
    """IWM is the benchmark, not a universe member — it must not be looked up in the universe map.

    Regression: a KeyError fired when the benchmark symbol fell through to the universe-store line
    (caught by the first real Polygon run, not the unit tests of residualize/cluster)."""
    d1, d2 = date(2025, 1, 8), date(2025, 1, 9)  # both weekdays

    def _bar(t: str, c: float) -> RawBar:
        return RawBar(ticker=t, open=c, high=c, low=c, close=c, volume=1000.0)

    class _FakeEod(EodClient):
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day in (d1, d2):
                return {
                    "AAA": _bar("AAA", 10.0), "BBB": _bar("BBB", 20.0), "IWM": _bar("IWM", 100.0),
                }
            return {}

    names = [
        _Name(internal_id="SEC-1-AAA", ticker="AAA", cik="1", name="A", market_cap=1e9),
        _Name(internal_id="SEC-2-BBB", ticker="BBB", cik="2", name="B", market_cap=2e9),
    ]
    closes, iwm, calendar = pull_closes(
        _FakeEod(), names, reference_date=date(2025, 1, 10), window_days=15
    )
    assert calendar == [d1, d2]  # master calendar = days IWM has a bar
    assert iwm == {d1: 100.0, d2: 100.0}  # benchmark kept separate, no KeyError
    assert closes["SEC-1-AAA"] == {d1: 10.0, d2: 10.0}
    assert set(closes) == {"SEC-1-AAA", "SEC-2-BBB"}  # IWM never written into the universe map


def test_window_spec_is_trailing_only() -> None:
    # a sanity pin that the window record carries no forward field
    w = WindowSpec(reference_date=date(2026, 6, 17), window_days=365, start=date(2025, 6, 17),
                   end=date(2026, 6, 17), trading_days=250)
    assert w.end <= w.reference_date
