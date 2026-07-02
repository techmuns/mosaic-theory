"""Render a :class:`Dossier` to human-readable markdown — source_refs shown INSPECTABLE.

The point of the rendering is that the human verifies the primary datum (the cited filing cell / bar
window / CIQ sheet), not the summary. So every fact prints its ``source_ref``; every UNKNOWN/MISSING
prints why; bull/bear points print their citation and an ⚠ when a guardrail flagged them.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from typing import Any

from vinci.dossier.schemas import Dossier, MechanicalLayer, Sourced, SourceStatus

# Display curation for the catalyst path — the full data always stays in dossier.json; these only
# cap/collapse/group the HUMAN view (the margin-trend mini-table idiom: curate display, not data).
_GROUP_CAP = 3  # revision-event broker-day groups shown; the rest noted "+N in JSON"
_ITEMS_PER_GROUP = 5  # material line items per group (largest |Δ| first)
_LADDER_KEEP = ("NTM", "FY 2026", "FY 2027", "FY 2028")  # multiples shown; later years → JSON

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


def _body(value: str) -> str:
    """Strip the trailing '  [as-of …]' / '  [data ≥ …]' suffix an extractor appends — the as-of is
    shown once on the section header, not repeated on every curated line."""
    i = value.rfind("  [")
    return value[:i] if i != -1 and value.rstrip().endswith("]") else value


def _asof_header(s: Sourced[Any]) -> str:
    """The section-header as-of, floor-aware: a '≥'-prefixed value is an unverified export FLOOR,
    never a plain as-of."""
    if s.status is not SourceStatus.PRESENT or not s.value:
        return "as-of UNKNOWN"
    v = str(s.value)
    return f"export date unverified (data ≥ {v[1:]})" if v.startswith("≥") else f"as-of {v}"


def _horizon_lines(s: Sourced[Any]) -> list[str]:
    """(4a) Horizon read: non-zero breadth rows first; rows with ZERO breadth across ALL windows
    collapse to one line. The full grid stays in dossier.json."""
    label = "Horizon read (FQ — next-2Q revision breadth)"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    nonzero: list[str] = []
    zero: list[str] = []
    for seg in (seg.strip() for seg in _body(str(s.value)).split("; ")):
        if seg:
            (nonzero if re.search(r"[1-9]\d*[↑↓]", seg) else zero).append(seg)
    out = [f"- **{label}** — ↳ `{s.source_ref}`:"]
    out += [f"  - {seg}" for seg in nonzero]
    if zero:
        labels = ", ".join(seg.split(":", 1)[0] for seg in zero)
        out.append(f"  - _no revisions in any window: {labels}_")
    return out


def _ladder_lines(s: Sourced[Any]) -> list[str]:
    """(4c) Forward-multiple ladder: NTM + FY26–FY28 only; later years noted, full in JSON."""
    label = "Cross-name anchor (NTM forward-multiple ladder)"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    segs = [seg.strip() for seg in _body(str(s.value)).split(" | ") if seg.strip()]
    kept = [seg for seg in segs if seg.split(":", 1)[0].strip() in _LADDER_KEEP]
    out = [f"- **{label}** — ↳ `{s.source_ref}`:"]
    out += [f"  - {seg}" for seg in kept]
    if len(segs) - len(kept) > 0:
        out.append(f"  - _+{len(segs) - len(kept)} later fiscal years in JSON_")
    return out


def _abs_delta(e: Any) -> float:
    try:
        return abs(float(e.broker_current) - float(e.broker_prior))
    except (ValueError, TypeError):
        return -1.0


def _grouped_events_lines(s: Sourced[Any]) -> list[str]:
    """(4d) Revision events GROUPED by (date, broker): a change-type summary + the material line
    items (largest |Δ| first) per group; cap 3 groups, the rest noted. Full list in dossier.json."""
    label = "Revision-event log"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    events = s.value
    groups: dict[tuple[str, str], list[Any]] = {}
    for e in events:
        groups.setdefault((e.date, e.broker), []).append(e)
    keys = sorted(groups, key=lambda k: k[0], reverse=True)  # most-recent broker-day first
    out = [f"- **{label}** ({len(events)} events · {len(keys)} broker-days) — ↳ `{s.source_ref}`:"]
    for key in keys[:_GROUP_CAP]:
        evs = groups[key]
        summary = ", ".join(
            f"{t}×{n}" if n > 1 else t for t, n in Counter(e.change_type for e in evs).items()
        )
        out.append(f"  - **{key[0]} · {key[1]}** — {summary}:")
        for e in sorted(evs, key=_abs_delta, reverse=True)[:_ITEMS_PER_GROUP]:
            out.append(
                f"    - {e.metric} {e.period}: {e.broker_prior}→{e.broker_current} "
                f"(cons {e.consensus_before}→{e.consensus_after})"
            )
        if len(evs) > _ITEMS_PER_GROUP:
            out.append(f"    - _+{len(evs) - _ITEMS_PER_GROUP} more line items in JSON_")
    if len(keys) > _GROUP_CAP:
        out.append(f"  - _+{len(keys) - _GROUP_CAP} more broker-days in JSON_")
    return out


def _catalyst_section(m: MechanicalLayer) -> list[str]:
    """The Catalyst-path section — horizon-matched estimates/guidance/revision view IN PLACE of the
    old thin 'Consensus context' slot. The legacy light facts are GONE (eps/revenue/revision-history
    are duplicated by the catalyst reads); only the non-duplicate Surprise history is folded in. A
    dossier.json predating catalyst_path degrades to the legacy consensus facts (back-compat)."""
    cp = m.catalyst_path
    out: list[str] = [""]
    if cp is None:  # pre-catalyst_path JSON — the legacy fallback (only place these still render)
        out += [
            "### Consensus context",
            _fact("EPS trend", m.consensus_context.eps_trend),
            _fact("Revenue trend", m.consensus_context.revenue_trend),
            _fact("Revision history", m.consensus_context.revision_history),
            _fact("Surprise history (beat/miss)", m.consensus_context.surprise_history),
        ]
    else:
        hdr = f"### Catalyst path (estimates · guidance · revisions) — {_asof_header(cp.as_of)}"
        out.append(hdr)
        out += _horizon_lines(cp.horizon_read)
        out.append(_fact("Acceleration read (monthly consensus path)", cp.acceleration_read))
        out += _ladder_lines(cp.cross_name_anchor)
        out.append(_fact("Guidance bridge (latest guide + track-record)", cp.guidance_bridge))
        out.append(_fact("Consensus stats (target + ratings)", cp.consensus_stats))
        out += _grouped_events_lines(cp.revision_events)
        sh = _fact("Surprise history (annual beat/miss)", m.consensus_context.surprise_history)
        out.append(sh)  # the one non-duplicate legacy fact, folded in
    out += [
        "",
        "### Management commentary (transcript POINTER — read the file; not a machine excerpt)",
        _fact("Earnings call", m.management_commentary),
        "",
    ]
    return out


# --- B4: the ONE shared markdown table renderer (every dossier table routes through here) ---------
_TABLE_MARK = "<!-- ds-table -->"  # marker a test greps to confirm a table used the shared renderer


def _table(
    label: str, cite: str | None, cols: list[str], rows: list[list[str]],
    note: str = "", name_rows: frozenset[int] = frozenset(),
) -> list[str]:
    """The single shared markdown table renderer (B4). Emits a GFM table tagged with ``_TABLE_MARK``
    so a test confirms every table routes here; ``name_rows`` indices are bolded (the subject)."""
    head = f"- **{label}**" + (f" — ↳ `{cite}`" if cite else "") + f"  {_TABLE_MARK}"
    out = [head, "", "| " + " | ".join([" ", *cols]) + " |", "|" + "---|" * (len(cols) + 1)]
    for i, row in enumerate(rows):
        out.append("| " + " | ".join(f"**{c}**" if i in name_rows else c for c in row) + " |")
    if note:
        out += ["", f"_{note}_"]
    out.append("")
    return out


# --- B.1 shared numeric formatters (ONE place): thousands-consistent, no negative-zero, net-cash
def _cap(v: float | None) -> str:  # $M → "$1.4B" / "$423M"
    if v is None:
        return "–"
    return f"${v / 1000:,.1f}B" if abs(v) >= 1000 else f"${v:,.0f}M"


def _pctc(v: float | None) -> str:  # fraction → "14%"; a value rounding to zero is "0%" (never -0%)
    return f"{round(v * 100):d}%" if v is not None else "–"  # round()→int collapses -0.4% → 0%


def _ratioc(s: str | None) -> str:  # a ratio → one decimal ("2" → "2.0"); "NM"/"–" pass through
    if s is None:
        return "–"
    try:
        return f"{float(s):.1f}"
    except (ValueError, TypeError):
        return str(s)


def _netdebt(v: float | None) -> str:  # $M net debt; NEGATIVE = net cash, labeled (CATL case)
    if v is None:
        return "–"
    return f"{-v:,.0f} (net cash)" if v < 0 else f"{v:,.0f}"


def _numc(v: float | None) -> str:  # a plain number cell → "550.7", or "–"
    return f"{v:,.1f}" if v is not None else "–"


def _split_note(text: str) -> tuple[str, str]:
    """Split a trailing '  [note]' off a value string → (body, note)."""
    m = re.search(r"\s*\[([^\]]*)\]\s*$", text)
    return (text[: m.start()].rstrip(), m.group(1)) if m else (text, "")


def _peer_grid_lines(s: Sourced[Any]) -> list[str]:
    """(B1) Per-peer comparability grid as a table: peers + the name (bolded) + the median footer;
    cap · EBITDA margin · rev growth · EBITDA growth · Debt/EBITDA · net debt. No computed delta."""
    label = "Per-peer grid (cap · margin · growth · leverage — name vs peers)"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    # full-word headers (B.1 item 2); 6 value columns — the row LABEL is the company (the shared
    # renderer prepends the empty label header), so the header count matches the cell count exactly.
    cols = ["Cap", "EBITDA margin", "Rev growth (1y)", "EBITDA growth (1y)",
            "Total debt/EBITDA", "Net debt ($M)"]
    trows: list[list[str]] = []
    name_rows: set[int] = set()
    for i, r in enumerate(s.value):
        if r.is_name:
            name_rows.add(i)
        tag = " · the name" if r.is_name else (" (peers)" if r.is_median else "")
        trows.append([
            r.name + tag, _cap(r.market_cap), _pctc(r.ebitda_margin), _pctc(r.rev_growth_1y),
            _pctc(r.ebitda_growth_1y), _ratioc(r.debt_to_ebitda), _netdebt(r.net_debt),
        ])
    return _table(label, s.source_ref, cols, trows, name_rows=frozenset(name_rows))


def _multiples_lines(s: Sourced[Any]) -> list[str]:
    """(B4) Trading multiples → the shared table (multiple × Name/Low/Median/Mean/High)."""
    label = "Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    body, note = _split_note(str(s.value))
    rows: list[list[str]] = []
    for seg in body.split(";"):
        m = re.match(
            r"\s*(.+?):\s*name\s+(\S+)\s+vs peers Low\s+(\S+)\s*/\s*Median\s+(\S+)\s*/\s*"
            r"Mean\s+(\S+)\s*/\s*High\s+(\S+)",
            seg,
        )
        if m:
            rows.append(list(m.groups()))
    if not rows:
        return [_fact(label, s)]
    return _table(label, s.source_ref, ["Name", "Low", "Median", "Mean", "High"], rows, note)


def _roster_lines(s: Sourced[Any]) -> list[str]:
    """(B4) Peer-set roster → the shared table (peer × mkt-cap/business); 'the name' as a footer."""
    label = "Peer set (roster · caps · business)"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    text = str(s.value)
    note = ""
    nm = re.search(r"\|\s*the name:\s*(.+)$", text)
    if nm:
        note = f"the name: {nm.group(1).strip()}"
        text = text[: nm.start()]
    text = re.sub(r"^\s*\d+\s+peers\s+—\s*", "", text)
    rows: list[list[str]] = []
    for seg in text.split(";"):
        m = re.match(r"\s*(.+?)\s+(\$[\d.,]+[BM])\s+—\s+(.*)", seg)
        if m:
            rows.append([m.group(1).strip(), m.group(2), m.group(3).strip()])
        elif seg.strip():
            rows.append([seg.strip(), "–", ""])
    if not rows:
        return [_fact(label, s)]
    return _table(label, s.source_ref, ["Mkt cap", "Business"], rows, note)


def _leverage_block(m: MechanicalLayer) -> list[str]:
    """(B2) Unified leverage & survival — ALL leverage in ONE block, both bases LABELED (no
    net-vs-total mixing) + OCF/fwd-adj + credit health. Replaces the scattered Quality leverage
    lines (which fall back for a pre-B2 dossier.json)."""
    lv = m.leverage_survival
    assert lv is not None
    return [
        "### Leverage & survival (unified — both bases labeled, no net-vs-total mixing)",
        _fact("Net debt / EBITDA (CIQ NET basis)", lv.net_debt_to_ebitda, _mult),
        _fact("Total debt / EBITDA (comps — name vs peer median)", lv.total_debt_to_ebitda),
        _fact("Net debt / OCF", m.quality.net_debt_to_ocf, _mult),
        _fact("Net debt / EBITDA (fwd-adj covenant basis)", m.quality.net_debt_to_ebitda_adjusted),
        _fact("Interest coverage", lv.interest_coverage, _mult),
        _fact("Survival (self-funding + nearest wall)", lv.survival),
        _fact("Credit health (S&P-MI scores — scale labeled)", lv.credit_health),
        "",
    ]


def _quality_leverage_lines(m: MechanicalLayer) -> list[str]:
    """The Quality leverage lines — rendered HERE only for a pre-B2 dossier.json; when the unified
    leverage_survival block exists they move there (not duplicated)."""
    if m.leverage_survival is not None:
        return []
    q = m.quality
    return [
        _fact("Net debt / EBITDA", q.net_debt_to_ebitda, _mult),
        _fact("Net debt / OCF", q.net_debt_to_ocf, _mult),
        _fact("Net debt / EBITDA (fwd-adj)", q.net_debt_to_ebitda_adjusted),
        _fact("Survival capacity (leverage + self-funding + wall)", q.survival_capacity),
        _fact("Interest coverage", q.interest_coverage, _mult),
    ]


def _peer_grid_or_deltas(pc: Any) -> list[str]:
    """(B1) The per-peer grid (with median footer) when present; else the legacy median-only deltas
    line (a pre-B1 fallback)."""
    if pc.peer_grid is not None:
        return _peer_grid_lines(pc.peer_grid)
    return [_fact("Fundamental deltas (earned-vs-residual inputs)", pc.fundamental_deltas)]


def _implied_lines(iv: Any) -> list[str]:
    """(B3) CIQ implied valuation — POSED: the implied EQUITY table (basis × Low/Median/Mean/High) +
    the bridge + the name's ACTUAL market cap adjacent. NO computed %/discount/upside; the
    heterogeneity gate renders verbatim on the header."""
    g = iv.comparability_gate
    gate = g.value if g.status is SourceStatus.PRESENT else ""
    out = [
        "### Implied valuation (CIQ-computed at peer multiples — POSED, not concluded)",
        f"> **Comparability gate:** {gate}" if gate else "",
        "> _Composition first — the human judges earned vs residual (not a machine upside)._",
        _fact("Name market cap ($M) — the ADJACENT fact to compare against", iv.market_cap),
        _fact("Bridge (TEV → equity)", iv.bridge),
    ]
    eq = iv.implied_equity
    if eq.status is SourceStatus.PRESENT and eq.value:
        cols = ["Basis", "Low", "Median", "Mean", "High"]
        trows = [
            [r.basis, _numc(r.low), _numc(r.median), _numc(r.mean), _numc(r.high)] for r in eq.value
        ]
        out += _table("Implied EQUITY value ($M, CIQ)", eq.source_ref, cols, trows)
    else:
        out.append(_fact("Implied equity", eq))
    out.append("")
    return out


def _flags_section(d: Dossier) -> list[str]:
    """The human-facing CAVEATS render LOW (next to key_unknowns), not at the top — a closing 'what
    to verify' checklist, not the headline. Only decision caveats show here (re-voiced, plus the
    'pull CIQ …' incomplete-input notes); the machine-QA self-checks live in ``d.qa_flags`` (JSON /
    dev only). The dossier assembles and cites; the verdict and the caveat-resolution are the
    human's."""
    if not d.caveats:
        return []
    return ["## ⚠ Analyst caveats — verify before the verdict",
            *[f"- {c}" for c in d.caveats], ""]


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
    out += ["## Mechanical layer (source-bound facts)", "", "### Valuation"]
    out += [
        # Lead with the CROSS-SECTIONAL read (the edge). The own-history percentile is near-0th for
        # nearly every finalist (the screen selects drawdowns), so it barely discriminates — it is
        # folded, with its RANGE + sample confidence, into the secondary own-history line below.
        _fact("Cross-sectional (vs peers — the edge)", m.valuation.cross_sectional),
        _fact("P/E", m.valuation.pe, _mult),
        _fact("EV/EBITDA (GAAP TEV/LTM)", m.valuation.ev_ebitda, _mult),
        _fact("EV/EBITDA (adjusted, forward)", m.valuation.ev_ebitda_adjusted_fwd),
        _fact("Adjusted EPS (earnings power)", m.valuation.adjusted_eps),
        _fact("Own-history range position", m.valuation.range_position),
        "",
        "### Quality / durability",
        _fact("FCF sign", m.quality.fcf_sign, _signword),
        _fact("Free cash flow ($M)", m.quality.free_cash_flow),
        _fact("Margin trend", m.quality.margin_trend),
        # B2: the leverage lines render HERE only when the unified block is absent (old JSON).
        *_quality_leverage_lines(m),
        _fact("Share-count trend", m.quality.share_count_trend),
        _fact("Liquidity / covenant flags", m.quality.liquidity_covenant_flags),
        _fact("Multi-year trajectory (compounder vs melting ice)", m.quality.multi_year_trajectory),
        "",
        # B2 unified leverage & survival (present on a fresh assembly; absent → lines stayed above).
        *(_leverage_block(m) if m.leverage_survival is not None else []),
        "### Concentration",
        _fact("Segments (revenue share)", m.concentration.segments),
        _fact("Segments (EBITDA share — where profit sits)", m.concentration.segment_ebitda),
        _fact("Customers", m.concentration.customers),
        _fact("Geographic", m.concentration.geographic),
        "",
        "### Peer comps (CIQ Company Comparable Analysis — consensus comp, framed to RESIST)",
        # B4: the roster + trading multiples route through the ONE shared table renderer.
        *_roster_lines(m.peer_comps.peer_set),
        _fact("Comparability (confidence gate)", m.peer_comps.comparability),
        *_multiples_lines(m.peer_comps.trading_multiples),
        # B1: the per-peer grid (medians as the footer) replaces the median-only deltas line.
        *_peer_grid_or_deltas(m.peer_comps),
        "",
        # B3 CIQ implied valuation (posed; heterogeneity gate on its header; no computed %).
        *(_implied_lines(m.implied_valuation) if m.implied_valuation is not None else []),
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
    out += _catalyst_section(m)

    if d.synthesis is None:
        out += ["## Synthesis", "_Not produced (see flags)._", "", *_flags_section(d)]
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
    out += _flags_section(d)
    return "\n".join(out)
