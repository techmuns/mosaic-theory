"""Render a :class:`Dossier` to human-readable markdown — source_refs shown INSPECTABLE.

The point of the rendering is that the human verifies the primary datum (the cited filing cell / bar
window / CIQ sheet), not the summary. So every fact prints its ``source_ref``; every UNKNOWN/MISSING
prints why; bull/bear points print their citation and an ⚠ when a guardrail flagged them.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from vinci.dossier.schemas import Dossier, Sourced, SourceStatus

# --- display formatters (render boundary ONLY — the stored Sourced.value keeps full precision) ---
# Screen-data-record fields arrive as raw DataField floats; format for legibility here, never at the
# source, so the synthesis / number-trace still see the real number. CIQ-path fields are already
# clean strings and pass through unformatted (default ``str``).


def _ordinal(n: int) -> str:
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _mult(v: Any) -> str:  # multiples / ratios → "5.5x", "2.9x"
    return f"{float(v):.1f}x"


def _pctile(v: Any) -> str:  # a 0..1 percentile → "1st %ile", not 0.0103
    return f"{_ordinal(round(float(v) * 100))} %ile"


def _pct(v: Any) -> str:  # a fraction → percent → "-72.6%", not -0.726
    return f"{float(v) * 100:.1f}%"


def _signword(v: Any) -> str:  # -1/0/+1 → word, not a bare int
    n = int(v)
    return "positive" if n > 0 else "negative" if n < 0 else "flat"


def _dates(v: Any) -> str:  # list of ISO dates → comma-joined, not a Python list repr
    return ", ".join(str(x) for x in v)


def _fact(label: str, s: Sourced[Any], fmt: Callable[[Any], str] = str) -> str:
    if s.status is SourceStatus.PRESENT:
        return f"- **{label}:** {fmt(s.value)}\n  - ↳ `{s.source_ref}`"
    return f"- **{label}:** _{s.status.value.upper()}_ — {s.note}"


def render_markdown(d: Dossier) -> str:
    m = d.mechanical
    out: list[str] = [
        f"# Dossier — {d.name} ({d.ticker})",
        "",
        f"_Finalist rank {d.rank} · ref {d.reference_date} · assembled "
        f"{d.assembled_at:%Y-%m-%d %H:%M} · LLM {d.llm_model or 'none'}_",
        "",
        "> **Assembles and cites; never concludes.** There is no BUY/AVOID here — the verdict is "
        "the human's, logged separately via the ledger with a frozen entry price.",
        "",
    ]
    if d.flags:
        out += ["## ⚠ Flags (human review)", *[f"- {f}" for f in d.flags], ""]

    out += ["## Mechanical layer (source-bound facts)", "", "### Valuation"]
    out += [
        _fact("P/E", m.valuation.pe, _mult),
        _fact("P/E percentile (5y)", m.valuation.pe_percentile_5y, _pctile),
        _fact("EV/EBITDA (GAAP TEV/LTM)", m.valuation.ev_ebitda, _mult),
        _fact("EV/EBITDA percentile (5y)", m.valuation.ev_ebitda_percentile_5y, _pctile),
        _fact("EV/EBITDA (adjusted, forward)", m.valuation.ev_ebitda_adjusted_fwd),
        _fact("Adjusted EPS (earnings power)", m.valuation.adjusted_eps),
        _fact("Range position", m.valuation.range_position),
        "",
        "### Quality / durability",
        _fact("FCF sign", m.quality.fcf_sign, _signword),
        _fact("Free cash flow ($M)", m.quality.free_cash_flow),
        _fact("Margin trend", m.quality.margin_trend),
        _fact("Net debt / EBITDA", m.quality.net_debt_to_ebitda, _mult),
        _fact("Net debt / OCF", m.quality.net_debt_to_ocf, _mult),
        _fact("Net debt / EBITDA (fwd-adj)", m.quality.net_debt_to_ebitda_adjusted),
        _fact("Survival capacity (leverage + self-funding + wall)", m.quality.survival_capacity),
        _fact("Interest coverage", m.quality.interest_coverage, _mult),
        _fact("Share-count trend", m.quality.share_count_trend),
        _fact("Liquidity / covenant flags", m.quality.liquidity_covenant_flags),
        _fact("Multi-year trajectory (compounder vs melting ice)", m.quality.multi_year_trajectory),
        "",
        "### Concentration",
        _fact("Segments (revenue share)", m.concentration.segments),
        _fact("Segments (EBITDA share — where profit sits)", m.concentration.segment_ebitda),
        _fact("Customers", m.concentration.customers),
        _fact("Geographic", m.concentration.geographic),
        "",
        "### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)",
        _fact("Peer set (roster · caps · business)", m.peer_comps.peer_set),
        _fact("Comparability (confidence gate)", m.peer_comps.comparability),
        _fact(
            "Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)",
            m.peer_comps.trading_multiples,
        ),
        _fact("Fundamental deltas (earned-vs-residual inputs)", m.peer_comps.fundamental_deltas),
        "",
        "### Drawdown cause",
        _fact("Shape", m.drawdown_cause.shape),
        _fact("Gap-down dates", m.drawdown_cause.gap_down_dates, _dates),
    ]
    if m.drawdown_cause.filings:
        out.append("- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**")
        for f in m.drawdown_cause.filings:
            out.append(f"  - gap {f.gap_date} → {f.filing_date} [`{f.accession}`]({f.url})")
            out.append(f"    - items: {', '.join(f.item_types) or '—'}")
            for ev in f.events:
                out.append(f"    - {ev}")
    out.append(
        _fact("Revised guidance (catalyst 8-K Ex-99.1)", m.drawdown_cause.revised_guidance)
    )
    out += [
        "",
        "### Idiosyncratic vs shared (G2-vs-market compensation)",
        _fact("Name 180d return", m.idiosyncratic_vs_shared.name_180d_return, _pct),
        _fact("Market (IWM) 180d return", m.idiosyncratic_vs_shared.market_180d_return, _pct),
        _fact("Relative vs market", m.idiosyncratic_vs_shared.rel_vs_market, _pct),
        _fact("Cohort read", m.idiosyncratic_vs_shared.read),
    ]
    cohort = m.idiosyncratic_vs_shared.cohort
    if cohort.status is SourceStatus.PRESENT and cohort.value:
        out.append(f"- **Graph cohort** (`{cohort.source_ref}`):")
        for cm in cohort.value:
            ret = f"{cm.ret_180d:.0%}" if cm.ret_180d is not None else "no bars"
            out.append(f"  - [{cm.hops}h] {cm.ticker}: {ret} · via {cm.via}")
    else:
        out.append(_fact("Graph cohort", cohort))
    out += [
        "",
        "### Consensus context",
        _fact("EPS trend", m.consensus_context.eps_trend),
        _fact("Revenue trend", m.consensus_context.revenue_trend),
        _fact("Revision history", m.consensus_context.revision_history),
        _fact("Surprise history (beat/miss)", m.consensus_context.surprise_history),
        "",
        "### Management commentary (transcript POINTER — read the file; not a machine excerpt)",
        _fact("Earnings call", m.management_commentary),
        "",
    ]

    if d.synthesis is None:
        out += ["## Synthesis", "_Not produced (see flags)._", ""]
        return "\n".join(out)

    s = d.synthesis
    out += ["## Synthesis (LLM — framing for the human, every point source-bound)", ""]
    if s.evidence_balance:
        out += [f"**Evidence balance:** {s.evidence_balance}", ""]

    def points(title: str, pts: list[Any]) -> None:
        out.append(f"### {title}")
        for p in pts:
            warn = "" if p.cited else " ⚠ uncited"
            out.append(f"- {p.claim}{warn}\n  - ↳ `{p.source_ref}`")
        out.append("")

    points("Bull case (overshoot / mean-revert)", s.bull_points)
    points("Bear case (terminal / value-trap)", s.bear_points)
    out.append("### Twin reference cases")
    for t in s.twin_reference_cases:
        out.append(f"- **{t.name}** — {t.outcome}")
        out.append(f"  - distinguished by: {t.distinguishing_fact}")
        out.append(f"  - source: {t.source}")
    out += ["", "### Decisive question", f"**{s.decisive_question.question}**", ""]
    points("…evidence for", s.decisive_question.evidence_for)
    points("…evidence against", s.decisive_question.evidence_against)
    out += ["### Key unknowns", *[f"- {u}" for u in s.key_unknowns], ""]
    return "\n".join(out)
