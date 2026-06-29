"""Human-readable rendering of theme-detection output (the CLI face-validity surface).

Prints the candidate cluster, its gate values, the candidate linkage the analyst names a driver
from, and the §7.1 strength signals — assembled and presented, never ordered into a decision. The
output order is breadth (display only); NOT a quality ranking (themes are not ranked, §2).
"""

from __future__ import annotations

from vinci.schemas.envelope import DataField
from vinci.themes.schemas import CandidateTheme, ThemeDetectionResult, Trajectory


def _pct(df: DataField[float]) -> str:
    return f"{df.value:+.1%}" if df.is_known and df.value is not None else f"UNKNOWN ({df.note})"


def _num(df: DataField[float]) -> str:
    return f"{df.value:.2f}" if df.is_known and df.value is not None else f"UNKNOWN ({df.note})"


def _traj(t: Trajectory) -> str:
    """Render a four-horizon trajectory shortest→longest as a shape (no collapse to a number)."""
    return "  ".join(f"{label} {_pct(field)}" for label, field in t.ordered())


def render_theme(theme: CandidateTheme) -> str:
    a = theme.admissibility
    s = theme.strength_signals
    tickers = " ".join(m.ticker for m in theme.members)
    verdict = "ADMISSIBLE (analyst names the driver)" if a.admissible else "rejected"
    lines = [
        f"── {theme.cluster_id} · {a.breadth_value} names · {verdict} ──",
        f"   members: {tickers}",
        f"   gates: breadth {a.breadth_value} {'PASS' if a.breadth_pass else 'FAIL'} · "
        f"coherence {a.coherence_value:.2f} {'PASS' if a.coherence_pass else 'FAIL'} · "
        f"persistence {'PASS' if a.persistence_pass else 'FAIL'} ({a.persistence_note})",
        f"   τ-stability: {theme.tau_stability or '—'}",
        f"   candidate linkage (criterion 1 — ANALYST judges): "
        f"{theme.candidate_linkage.shared_note}",
        "   strength/lifecycle signals (INPUTS the human reads as a SHAPE — never an auto-rank):",
        f"     momentum    {_traj(s.momentum)}",
        f"     rel-vs-IWM  {_traj(s.rel_strength_vs_market)}",
        f"     breadth-expanding {_num(s.breadth_expanding)} · "
        f"over-extension {_pct(s.crowding_overextension)}",
    ]
    if a.fail_reasons:
        lines.append(f"   fail: {'; '.join(a.fail_reasons)}")
    return "\n".join(lines)


def render_result(result: ThemeDetectionResult, *, top: int | None = None) -> str:
    st = result.stats
    w = result.window
    out = [
        f"=== Theme detection · Component A · ref {result.reference_date} · "
        f"basis {result.residual_basis.value} ===",
        f"universe {st.universe_size} · coverage {st.names_with_coverage} "
        f"(dropped {st.names_dropped_insufficient_history} insufficient-history) · "
        f"SIC resolved {st.sic_resolved}",
        f"window {w.start}..{w.end} ({w.trading_days} trading days)",
        f"clusters {st.clusters_found} → ADMISSIBLE {st.admissible} · rejected "
        f"breadth {st.rejected_breadth} / coherence {st.rejected_coherence} / "
        f"persistence {st.rejected_persistence}",
        "",
        "--- ADMISSIBLE candidate themes (the analyst names/judges each; NOT ranked) ---",
    ]
    shown = result.candidate_themes if top is None else result.candidate_themes[:top]
    out.extend(render_theme(t) for t in shown)
    return "\n".join(out)
