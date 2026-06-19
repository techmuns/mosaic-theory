"""Render a :class:`Dossier` to human-readable markdown — source_refs shown INSPECTABLE.

The point of the rendering is that the human verifies the primary datum (the cited filing cell / bar
window / CIQ sheet), not the summary. So every fact prints its ``source_ref``; every UNKNOWN/MISSING
prints why; bull/bear points print their citation and an ⚠ when a guardrail flagged them.
"""

from __future__ import annotations

from typing import Any

from mosaic.dossier.schemas import Dossier, Sourced, SourceStatus


def _fact(label: str, s: Sourced[Any]) -> str:
    if s.status is SourceStatus.PRESENT:
        return f"- **{label}:** {s.value}\n  - ↳ `{s.source_ref}`"
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
        _fact("P/E", m.valuation.pe),
        _fact("P/E percentile (5y)", m.valuation.pe_percentile_5y),
        _fact("EV/EBITDA", m.valuation.ev_ebitda),
        _fact("EV/EBITDA percentile (5y)", m.valuation.ev_ebitda_percentile_5y),
        _fact("Range position", m.valuation.range_position),
        "",
        "### Quality / durability",
        _fact("FCF sign", m.quality.fcf_sign),
        _fact("Free cash flow", m.quality.free_cash_flow),
        _fact("Margin trend", m.quality.margin_trend),
        _fact("Net debt / EBITDA", m.quality.net_debt_to_ebitda),
        _fact("Interest coverage", m.quality.interest_coverage),
        _fact("Share-count trend", m.quality.share_count_trend),
        _fact("Liquidity / covenant flags", m.quality.liquidity_covenant_flags),
        "",
        "### Concentration",
        _fact("Segments", m.concentration.segments),
        _fact("Customers", m.concentration.customers),
        _fact("Geographic", m.concentration.geographic),
        "",
        "### Drawdown cause",
        _fact("Shape", m.drawdown_cause.shape),
        _fact("Gap-down dates", m.drawdown_cause.gap_down_dates),
    ]
    if m.drawdown_cause.filings:
        out.append("- **8-Ks at the gap-downs (cause from item codes + parsed filing text):**")
        for f in m.drawdown_cause.filings:
            out.append(f"  - gap {f.gap_date} → {f.filing_date} [`{f.accession}`]({f.url})")
            out.append(f"    - items: {', '.join(f.item_types) or '—'}")
            for ev in f.events:
                out.append(f"    - {ev}")
    out += [
        "",
        "### Idiosyncratic vs shared (G2-vs-market compensation)",
        _fact("Name 180d return", m.idiosyncratic_vs_shared.name_180d_return),
        _fact("Market (IWM) 180d return", m.idiosyncratic_vs_shared.market_180d_return),
        _fact("Relative vs market", m.idiosyncratic_vs_shared.rel_vs_market),
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
        "",
        "### Management commentary (transcript — qualitative, no numbers derived)",
        _fact("Earnings call", m.management_commentary),
        "",
    ]

    if d.synthesis is None:
        out += ["## Synthesis", "_Not produced (see flags)._", ""]
        return "\n".join(out)

    s = d.synthesis
    out += ["## Synthesis (LLM — framing for the human, every point source-bound)", ""]

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
