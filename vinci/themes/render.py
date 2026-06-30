"""Human-readable rendering of theme-detection output (the CLI face-validity surface).

Prints the candidate cluster, its gate values, the candidate linkage the analyst names a driver
from, and the §7.1 strength signals — assembled and presented, never ordered into a decision. The
output order is breadth (display only); NOT a quality ranking (themes are not ranked, §2).
"""

from __future__ import annotations

from vinci.schemas.envelope import DataField
from vinci.themes.schemas import CandidateTheme, ThemeDetectionResult, ThemeStage2, Trajectory


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


def render_stage2(s2: ThemeStage2) -> str:
    """Render the Stage-2 surface (leaders + type signals + confirmation) for one theme."""
    ls, ts, c = s2.leader_set, s2.type_signals, s2.confirmation
    pp = ts.price_pattern
    lines = [
        f"══ {s2.cluster_id} · {len(s2.member_tickers)} sub-$10B members ══",
        f"   members: {' '.join(s2.member_tickers)}",
        "   ── SUB-STEP 0: megacap leaders (machine ASSEMBLES; analyst RATIFIES) ──",
        f"   rule: {ls.rule}",
    ]
    if ls.leaders:
        for ld in ls.leaders:
            lines.append(
                f"     {ld.ticker:<6} ${ld.market_cap / 1e9:>6.0f}B  SIC {ld.sic}  "
                f"co-move {ld.residual_corr_to_cluster:+.2f}  {ld.name[:30]}"
            )
    else:
        lines.append("     (no co-moving >$10B leader — confirmation does not apply)")
    lines += [
        "   ── COMPONENT B: theme-type signals "
        "(the human judges type as part of naming the driver) ──",
        f"     price-pattern: {pp.read}",
        f"       leaders : {_traj(pp.leader_trajectory)}",
        f"       members : {_traj(pp.member_trajectory)}",
        f"       lead−member: {'  '.join(f'{lbl} {d:+.1%}' for lbl, d in pp.lead_minus_member)}",
        f"     vol-strip survival: {'SURVIVED' if ts.vol_strip_survived else 'FRAGMENTED'} "
        f"({ts.vol_strip_note})",
        f"     historical analog ({ts.historical_analog.status}): "
        f"{', '.join(ts.historical_analog.reference_themes) or '—'}",
    ]
    if ts.historical_analog.note:
        lines.append(f"       note: {ts.historical_analog.note}")
    lines.append(f"     TYPE STATE: {ts.defer_note}")
    lines.append(
        "   ── COMPONENT C: megacap confirmation SIGNAL "
        "(human reads to decide; not autonomous) ──"
    )
    if c is not None and c.grid:
        lines.append(f"     baseline {c.baseline_date} ({c.baseline_rationale})")
        lines.append(f"     leaders: {c.n_leaders} · clears →   +20%    +30%    +50%")
        for cell in c.grid:
            marks = "   ".join(
                "FIRE " if cell.clears[t] else "  -  " for t in ("+20%", "+30%", "+50%")
            )
            lines.append(f"       {cell.basis:<9} {cell.value:>+7.1%}   {marks}")
        lines.append(f"     scope: {c.scope_note}")
    else:
        lines.append("     (not computed — no co-moving mega-cap leaders)")
    return "\n".join(lines)
