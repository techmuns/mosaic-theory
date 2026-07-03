"""Render a :class:`Dossier` to human-readable markdown — source_refs shown INSPECTABLE.

The point of the rendering is that the human verifies the primary datum (the cited filing cell / bar
window / CIQ sheet), not the summary. So every fact prints its ``source_ref``; every UNKNOWN/MISSING
prints why; bull/bear points print their citation and an ⚠ when a guardrail flagged them.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable
from datetime import UTC, date, datetime
from itertools import groupby
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


def _fmt_assembled(dt: datetime) -> str:
    """The assembly stamp with a time — so two same-day re-assemblies are distinguishable. A fresh
    build is tz-aware UTC → rendered '… HH:MM UTC'; a legacy naive datetime (pre-UTC build) can't
    have its zone recovered, so it's shown as-is with a '(local)' note, not a false UTC claim."""
    if dt.tzinfo is not None:
        return f"{dt.astimezone(UTC):%Y-%m-%d %H:%M} UTC"
    return f"{dt:%Y-%m-%d %H:%M} (local)"


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


def _sourced_str(s: Sourced[Any]) -> str:
    """(audit) A ``Sourced[str]`` as inline text: the value when PRESENT, else its note — NEVER the
    bare word 'None' (which a raw ``{s.value}`` prints when the fact is UNKNOWN)."""
    if s.status is SourceStatus.PRESENT and s.value is not None:
        return str(s.value)
    return s.note or "n/a"


# (H3) an inline UNKNOWN/MISSING fact line — the only render shape the reason-dedup collapses.
_UNKNOWN_FACT = re.compile(r"^- \*\*(.+?):\*\* _(UNKNOWN|MISSING)_ — (.+)$")
# (audit) fold only DISTINCTIVE reasons. The fold is cross-section by design (the 99.1 case spans
# Leverage + Valuation), so a SHORT generic note ("no XBRL", "no positive EPS/price") shared by two
# UNRELATED fields would relocate one under the other's section. A long exact-match reason is
# effectively unique to its root cause, so it folds; terse notes render in place, as before.
_DEDUPE_MIN_REASON_LEN = 30


def _dedupe_unknown_reasons(lines: list[str]) -> list[str]:
    """(H3) Collapse repeated identical UNKNOWN/MISSING fact REASONS: the same DISTINCTIVE note
    (≥ ``_DEDUPE_MIN_REASON_LEN`` chars) carried by ≥2 fields renders ONCE, at the first occurrence,
    with the affected-fields list (e.g. the three 'adjusted figure not in the 99.1 revised guidance'
    fields → one line). No fact is suppressed — every affected field stays named. A short/generic
    reason is left in place (a coincidental cross-section collision must not move a fact). Matches
    only inline `_fact` UNKNOWN lines (tables / synthesis points / caveats never match)."""
    groups: dict[tuple[str, str], list[int]] = {}
    for i, ln in enumerate(lines):
        m = _UNKNOWN_FACT.match(ln)
        if m:
            groups.setdefault((m.group(2), m.group(3)), []).append(i)
    drop: set[int] = set()
    for (status, reason), idxs in groups.items():
        if len(idxs) < 2 or len(reason) < _DEDUPE_MIN_REASON_LEN:
            continue
        labels = [m.group(1) for i in idxs if (m := _UNKNOWN_FACT.match(lines[i]))]
        lines[idxs[0]] = f"- **{' · '.join(labels)}:** _{status}_ — {reason}"
        drop.update(idxs[1:])
    return [ln for i, ln in enumerate(lines) if i not in drop]


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


def _guidance_bridge_lines(cp: Any) -> list[str]:
    """(H4) Guidance bridge as a table — metric | latest guide | for | dated | age | record | most
    recent — each a RECORDED delivery fact, no reading added. A pre-H4 dossier.json (no rows) falls
    back to the flat one-line string."""
    rows_s = getattr(cp, "guidance_bridge_rows", None)
    if rows_s is None or rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return [_fact("Guidance bridge (latest guide + track-record)", cp.guidance_bridge)]
    cols = ["Latest guide", "For", "Dated", "Age", "Record (met/resolved)", "Most recent"]
    rows = [
        [r.metric, r.latest_guide, r.period, r.dated, r.age, r.record, r.most_recent]
        for r in rows_s.value
    ]
    return _table("Guidance bridge (latest guide + sign-aware delivery track-record)",
                  rows_s.source_ref, cols, rows)


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
        out += _guidance_bridge_lines(cp)
        out.append(_fact("Consensus stats (target + ratings)", cp.consensus_stats))
        out += _grouped_events_lines(cp.revision_events)
        sh = _fact("Surprise history (annual beat/miss)", m.consensus_context.surprise_history)
        out.append(sh)  # the one non-duplicate legacy fact, folded in
        # (F) positioning inputs — free DATED feeds; rendered only when present (pre-F JSON
        # has neither field → None → not rendered). Counts / shares / dates only, no interpretation.
        if cp.insider_activity is not None:
            out.append(_fact("Insider activity (Form 4, 6m)", cp.insider_activity))
        if cp.short_interest is not None:
            out.append(_fact("Short interest (FINRA)", cp.short_interest))
    out.append("")  # (D1) the management-commentary pointer moved OUT of here, into the appendix
    return out


# --- B4: the ONE shared markdown table renderer (every dossier table routes through here) ---------
_TABLE_MARK = "<!-- ds-table -->"  # marker a test greps to confirm a table used the shared renderer


def _gfm_cell(c: str) -> str:
    """(audit) Neutralise a value for a GFM table cell: a literal ``|`` opens a spurious column and
    a newline shatters the row — escape the pipe and collapse any whitespace run to a single space.
    The E5 covenant value/quote cells are VERBATIM filing text and can carry both."""
    return re.sub(r"\s+", " ", str(c).replace("|", "\\|")).strip()


def _table(
    label: str, cite: str | None, cols: list[str], rows: list[list[str]],
    note: str = "", name_rows: frozenset[int] = frozenset(),
) -> list[str]:
    """The single shared markdown table renderer (B4). Emits a GFM table tagged with ``_TABLE_MARK``
    so a test confirms every table routes here; ``name_rows`` indices bold the subject. Every
    cell is pipe/newline-sanitised (:func:`_gfm_cell`) so free-text (E5 verbatim) can't break it."""
    head = f"- **{label}**" + (f" — ↳ `{cite}`" if cite else "") + f"  {_TABLE_MARK}"
    out = [head, "", "| " + " | ".join(_gfm_cell(c) for c in [" ", *cols]) + " |",
           "|" + "---|" * (len(cols) + 1)]
    for i, row in enumerate(rows):
        cells = (f"**{_gfm_cell(c)}**" if i in name_rows else _gfm_cell(c) for c in row)
        out.append("| " + " | ".join(cells) + " |")
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
    # half-up (floor(x+0.5)) to MATCH the JS `Math.round` in dossier.js — Python's round() is
    # banker's (half-to-even), which would disagree with the web/PDF at every x.5% (12.5% → 12/13).
    # floor(x+0.5) also collapses a small negative (-0.4% → 0%), so never "-0%".
    return f"{math.floor(v * 100 + 0.5):d}%" if v is not None else "–"


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
    if v is None:
        return "–"
    v = round(v, 1) or 0.0  # collapse a signed near-zero (-0.04 → 0.0): never render "-0.0"
    return f"{v:,.1f}"


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


def _musd(v: float | None) -> str:  # a $M principal → "$25.0M", or "–"
    return f"${v:,.1f}M" if v is not None else "–"


def _maturity_wall_lines(cs: Any, reference_date: date) -> list[str]:
    """(E2) Deterministic month-precision maturity wall from the structured instruments, grouped vs
    the reference date: matured-pre-reference (resolution not in this data — verify the 8-K, NEVER
    assume repaid/defaulted) / due this reference year / due later years / undated (floor). No
    probability, risk, or conclusion language."""
    inst = cs.instruments
    if inst.status is not SourceStatus.PRESENT or not inst.value:
        return []
    matured: list[tuple[date, Any]] = []
    this_year: list[tuple[date, Any]] = []
    later: list[tuple[date, Any]] = []
    undated: list[Any] = []
    for i in inst.value:
        if i.maturity_date is None:
            undated.append(i)
            continue
        d = date.fromisoformat(i.maturity_date)
        (matured if d < reference_date else this_year if d.year == reference_date.year else later
         ).append((d, i))
    def dtot(xs: list[tuple[date, Any]]) -> float:
        return sum(i.principal_musd or 0.0 for _d, i in xs)

    def bykey(x: tuple[date, Any]) -> tuple[date, str]:  # sort a (date, instrument) pair stably
        return (x[0], x[1].description)

    out = [f"- **Maturity wall** (deterministic, vs the {reference_date.isoformat()} reference):"]
    if matured:
        out.append(
            f"  - **matured (pre-reference): {_musd(dtot(matured))}** — resolution not in this "
            "data; verify each against its 8-K (NEVER assume repaid or defaulted):")
        for d, i in sorted(matured, key=bykey):
            out.append(
                f"    - {d.isoformat()} ({(reference_date - d).days}d before ref): "
                f"{_musd(i.principal_musd)} {i.description[:34]}")
    if this_year:
        detail = ", ".join(
            f"{d.isoformat()} {_musd(i.principal_musd)}" for d, i in sorted(this_year, key=bykey))
        out.append(
            f"  - due ≤12m (through {reference_date.year}): {_musd(dtot(this_year))} — {detail}")
    for yr, grp in groupby(sorted(later, key=bykey), key=lambda x: x[0].year):
        out.append(f"  - due {yr}: {_musd(dtot(list(grp)))}")
    if undated:
        detail = ", ".join(f"{i.description[:26]} {_musd(i.principal_musd)}" for i in undated)
        undated_tot = sum(i.principal_musd or 0.0 for i in undated)
        out.append(
            f"  - undated (floor — no panel maturity): {_musd(undated_tot)} — {detail}")
    itemized = sum(i.principal_musd or 0.0 for i in inst.value)
    out.append(
        f"  - _reconciliation: itemized {_musd(itemized)} (panel {cs.detail_as_of}) vs the "
        f"latest-quarter aggregates below — the gap is unitemized / newer term loans; read the QoQ "
        "movement in the aggregates line._"
    )
    return out


def _capital_structure_lines(cs: Any, reference_date: date) -> list[str]:
    """(E1/E2–E5) Capital structure — the structured instruments table (replacing the flat
    liquidity_covenant_flags string), the month-precision maturity wall + reconciliation, then the
    maturity-anchored 8-Ks, covenant exhibit pointers, and the fenced Tier-2 covenant terms."""
    inst = cs.instruments
    out: list[str] = []
    if inst.status is SourceStatus.PRESENT and inst.value:
        cols = ["Type", "Principal", "Coupon", "Floating", "Maturity", "Sec", "Conv", "Cur"]
        rows = [
            [i.description, i.type, _musd(i.principal_musd), i.coupon or "–",
             i.floating_rate or "–",
             i.maturity_date or "undated", "Y" if i.secured else "N", "Y" if i.convertible else "N",
             i.currency]
            for i in inst.value
        ]
        out += _table(
            f"Capital structure (instruments) — panel {cs.detail_as_of}", inst.source_ref, cols,
            rows)
    else:
        out.append(_fact("Capital structure (instruments)", inst))
    out += _maturity_wall_lines(cs, reference_date)
    out += [
        _fact("Capital-structure aggregates (latest quarter)", cs.summary),
        _fact("8-Ks at instrument maturities", cs.maturity_filings),
    ]
    # (P3/FIX-3) the VERBATIM resolution at the maturity 8-K, when captured — replaces the pointer's
    # "read for resolution" with the actual event (a pre-P3 dossier.json has no field → nothing).
    mat_ev = getattr(cs, "maturity_event", None)
    if mat_ev is not None and (mat_ev.status is not SourceStatus.PRESENT or mat_ev.value):
        out.append(_fact("Maturity resolution (8-K verbatim)", mat_ev))
    out += _covenant_pointer_lines(cs)
    out += _covenant_term_lines(cs)
    out.append("")
    return out


def _covenant_pointer_lines(cs: Any) -> list[str]:
    """(H1) Covenant/contract pointers as a table — instrument family | filing | date | accession —
    each an EXHIBIT-BEARING, CIK-verified execution filing (a generic BS line renders its 'no
    contract-level filing' note). A pre-H dossier.json (no rows) falls back to the flat string."""
    rows_s = getattr(cs, "covenant_pointer_rows", None)
    if rows_s is None or rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return [_fact("Covenant exhibit pointers", cs.covenant_pointers)]
    cols = ["Filing", "Date", "Accession / exhibit (or note)"]
    rows = [
        [r.family, r.filing, r.filing_date or "—",
         (f"{r.accession} — {', '.join(r.exhibits[:3])}" if r.accession else r.note)]
        for r in rows_s.value
    ]
    return _table("Covenant / contract pointers (CIK-verified execution filings)",
                  rows_s.source_ref, cols, rows)


def _covenant_term_lines(cs: Any) -> list[str]:
    """(E5/H1d) Fenced Tier-2 covenant terms as a table — term | value (verbatim, or UNKNOWN) |
    source (exhibit · quote). Each PRESENT value is bound to the exhibit it was read from; an absent
    term is a visible UNKNOWN, never a guess. A pre-H1d dossier.json (no rows) falls back to the
    flat one-line string."""
    rows_s = getattr(cs, "covenant_term_rows", None)
    if rows_s is None or rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return [_fact("Covenant terms (Tier-2, fenced)", cs.covenant_terms)]
    cols = ["Value (verbatim, or UNKNOWN)", "Source (exhibit · verbatim quote)"]
    rows = []
    for r in rows_s.value:
        v = r.value
        if v.status is SourceStatus.PRESENT:
            src = v.source_ref or "—"
            if v.note:
                src = f"{src} — {v.note[:160]}{'…' if len(v.note) > 160 else ''}"
            rows.append([r.name, str(v.value), src])
        else:
            rows.append([r.name, "UNKNOWN", v.note or "not stated"])
    return _table("Covenant terms (Tier-2, fenced — verbatim, source-bound)",
                  rows_s.source_ref, cols, rows)


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


def _gate_shortref(gate: str) -> str:
    """(H3) The comparability gate is rendered VERBATIM once — at the Peer comps head. The G and
    Implied-Valuation headers cite it SHORT ('comparability: HETEROGENEOUS (see Peer comps gate)')
    rather than repeat the full text. A non-heterogeneous gate is already short — kept verbatim."""
    return ("comparability: HETEROGENEOUS (see Peer comps gate)"
            if "HETEROGENEOUS" in (gate or "") else (gate or ""))


def _implied_expectations_lines(v: Any) -> list[str]:
    """(G) Price-inverted expectations, MULTIPLES-space. Shared table: each stated multiple → the
    fundamental LEVEL price implies (TEV ÷ multiple); the consensus path anchors are juxtaposed
    BESIDE — never differenced (no %, gap, upside, or implied price/equity). The heterogeneity gate
    is cited SHORT on the header (verbatim once, at Peer comps — H3); both pricing as-ofs are
    stamped; a vintage-mismatch caveat renders when the pricing-vintages diverge (G5)."""
    ie = getattr(v, "implied_expectations", None)
    if ie is None:
        return []
    out = [
        f"- **Implied expectations (price-inverted · multiples-space)** — "
        f"{_gate_shortref(ie.heterogeneity_gate)}",
        "  - _price-implied fundamental levels at stated multiples — the human judges earned vs "
        "residual; identity (†): at the name's own multiple the implied level IS consensus._",
        f"  - _TEV as-of {ie.tev_as_of} · multiples as-of {ie.multiples_as_of}_",
    ]
    # rows carry the row-LABEL (the multiple's name) + one cell PER column — `_table` prepends a
    # blank header for the label, so each row must have len(cols)+1 cells: [label, multiple, level].
    rows: list[list[str]] = []
    for r in ie.rows:
        mult = f"{r.multiple:g}x" if r.multiple is not None else "NM"
        level = (
            f"${r.implied_level:,.1f}M {r.metric}" + (" †" if r.is_identity else "")
            if r.implied_level is not None else f"UNKNOWN — {r.note}")
        rows.append([r.label, mult, level])
    name_rows = frozenset(i for i, r in enumerate(ie.rows) if r.is_identity)
    out += _table(
        "Implied metric levels · fixed multiple set", ie.tev.source_ref,
        ["Multiple (× used)", "Implied level"], rows, name_rows=name_rows)
    # (audit) H7 made EBITDA anchors UNKNOWN-able (Trends may lack FY26/FY27) — show the NOTE, never
    # the bare word "None". rev_anchors is always PRESENT (ladder) but is guarded the same way.
    out.append(
        "- **Consensus path anchors (EBITDA — juxtapose, do NOT difference):** "
        f"{_sourced_str(ie.anchors)}")
    if ie.rev_anchors is not None:  # the parallel revenue anchors substantiate the TEV/Rev identity
        out.append(
            "- **Consensus path anchors (Revenue — juxtapose, do NOT difference):** "
            f"{_sourced_str(ie.rev_anchors)}")
    out.append(f"  - _{'⚠ ' if not ie.vintage_coherent else ''}{ie.coherence_note}_")
    if not ie.net_debt_reconciled:
        out.append("  - _⚠ net-debt disagrees with the cash/debt bridge — see the TEV source_")
    out.append(
        "  - _Fixed multiple set (declared in code, no per-name curation): name NTM + peer-median "
        "NTM/LTM, on TEV/EBITDA and TEV/Rev._")
    out.append("")
    return out


def _implied_lines(iv: Any) -> list[str]:
    """(B3) CIQ implied valuation — POSED: the implied EQUITY table (basis × Low/Median/Mean/High) +
    the bridge + the name's ACTUAL market cap adjacent. NO computed %/discount/upside; the
    heterogeneity gate renders verbatim on the header."""
    g = iv.comparability_gate
    gate = g.value if g.status is SourceStatus.PRESENT else ""
    out = [
        "### Implied valuation (CIQ-computed at peer multiples — POSED, not concluded)",
        f"> **Comparability gate:** {_gate_shortref(gate)}" if gate else "",  # (H3) short-ref
        "> _Composition first — the human judges earned vs residual (not a machine upside)._",
        _fact("Name market cap ($M) — the ADJACENT fact to compare against", iv.market_cap),
        _fact("Bridge (TEV → equity)", iv.bridge),
    ]
    eq = iv.implied_equity
    if eq.status is SourceStatus.PRESENT and eq.value:
        # the basis is the ROW LABEL (under `_table`'s prepended blank header), NOT a `cols` entry —
        # listing it in `cols` too would make the header one column wider than each row, shifting
        # every Low/Median/Mean/High value one header to the left in the rendered GFM table.
        cols = ["Low", "Median", "Mean", "High"]
        trows = [
            [r.basis, _numc(r.low), _numc(r.median), _numc(r.mean), _numc(r.high)] for r in eq.value
        ]
        out += _table("Implied EQUITY value ($M, CIQ)", eq.source_ref, cols, trows)
    else:
        out.append(_fact("Implied equity", eq))
    out.append("")
    return out


def _fin_table_lines(label: str, s: Sourced[Any]) -> list[str]:
    """A Sourced[FinTable] → the shared markdown table (columns → header, each row's [label, *cells]
    → a data row). UNKNOWN/MISSING falls back to the standard fact line."""
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    ft = s.value
    rows = [[r.label, *r.cells] for r in ft.rows]
    return _table(label, s.source_ref, ft.columns, rows, ft.note)


def _annual_with_fcf_label(s: Sourced[Any]) -> Sourced[Any]:
    """(D5b) Display-only: relabel the levered-FCF row + footnote it — the appendix FCF is CIQ's
    'Levered Free Cash Flow', NOT a CFO − capex derivation. No extractor change; the FinTable is
    rebuilt in place (frozen-model copy)."""
    if s.status is not SourceStatus.PRESENT or not s.value:
        return s
    ft = s.value
    rows = [
        r.model_copy(update={"label": "FCF (levered, CIQ)"}) if r.label == "FCF ($M)" else r
        for r in ft.rows
    ]
    if rows == list(ft.rows):  # no FCF row to relabel → unchanged
        return s
    fcf_note = "FCF (levered, CIQ) = CIQ 'Levered Free Cash Flow', NOT CFO − capex"
    note = f"{ft.note} · {fcf_note}" if ft.note else fcf_note
    return s.model_copy(update={"value": ft.model_copy(update={"rows": rows, "note": note})})


def _appendix_lines(m: MechanicalLayer) -> list[str]:
    """The FINANCIAL-SUMMARY appendix (C1–C4) — rendered AFTER the twins, before the verdict footer.
    C1/C2 are tables through the shared renderer (E columns marked + stamped); C3 is the posture
    block + the BS↔bridge coherence gate. Absent for a pre-C dossier (back-compat → omitted)."""
    fs = m.financial_summary
    if fs is None:
        return []
    hdr = ("## APPENDIX — FINANCIAL SUMMARY (actuals + consensus estimates) "
           f"— {_asof_header(fs.as_of)}")
    out = ["", hdr, "### Annual (last-4-FY + LTM + FY26E/FY27E consensus)"]
    annual = _annual_with_fcf_label(fs.annual)  # D5b: FCF row relabeled + footnoted (display-only)
    out += _fin_table_lines("Annual financials ($M; E = consensus)", annual)
    out.append("### Trailing 8 quarters (the recent-quarter trajectory)")
    out += _fin_table_lines("Quarterly financials", fs.quarterly)
    out += [
        "### Balance-sheet posture",
        _fact("Posture", fs.balance_sheet),
        _fact("Coherence — BS vs implied-valuation bridge", fs.coherence),
        "",
    ]
    return out


def _mgmt_commentary_lines(m: MechanicalLayer) -> list[str]:
    """(D1) The management-commentary pointer — relocated into the appendix zone (it is a transcript
    POINTER, not a headline read: the human opens the file, the machine never excerpts it). Rendered
    unconditionally so a pre-C dossier.json (no financial-summary appendix) still surfaces it."""
    return [
        "### Management commentary (transcript POINTER — read the file; not a machine excerpt)",
        _fact("Earnings call", m.management_commentary),
        "",
    ]


# (D4) a guardrail caveat is emitted as "Lead (a bull point): '<full claim>' — <explanation>". Parse
# it into the structured shape; the offending sentence is shown IN FULL (synthesis no longer _snips
# the human caveats — truncation is retained for the dev-only QA flags).
_CAVEAT_RE = re.compile(
    r"^(?P<lead>.*?)\((?P<where>[^)]*?\bpoint[^)]*?)\):\s*'(?P<what>.*?)'\s*—\s*(?P<why>.*)$",
    re.DOTALL,
)


def _split_why_how(explanation: str) -> tuple[str, str]:
    """(D4) A guardrail explanation ends with its actionable clause after the last ';'
    ('… peer-set composition; POSE justified-vs-residual …') → (why-it-matters, how-to-verify)."""
    if "; " in explanation:
        head, _, tail = explanation.rpartition("; ")
        return head.strip(), tail.strip()
    return explanation.strip(), ""


def _caveat_block(c: str) -> list[str]:
    """(D4) A guardrail caveat renders in the what / where / why-it-matters / how-to-verify shape,
    the offending sentence IN FULL. A mechanical / 'pull CIQ …' caveat is already a complete
    advisory sentence, so it stays a single full-sentence bullet (no forced split)."""
    m = _CAVEAT_RE.match(c)
    if not m:
        return [f"- {c}"]
    why, how = _split_why_how(m.group("why").strip())
    out = [
        f"- **{m.group('lead').strip()}** — {m.group('what').strip()}",
        f"  - _where:_ {m.group('where').strip()}",
        f"  - _why it matters:_ {why}",
    ]
    if how:
        out.append(f"  - _how to verify:_ {how}")
    return out


def _flags_section(d: Dossier) -> list[str]:
    """(D1) The human-facing CAVEATS render at the TOP (right under the header) — the first thing
    the human sees is what to verify before trusting anything below. Each renders in the D4
    what/where/why-it-matters/how-to-verify shape, the offending sentence IN FULL. Only decision
    caveats show here (re-voiced, plus the 'pull CIQ …' notes); the machine-QA self-checks live in
    ``d.qa_flags`` (JSON / dev only). The dossier assembles and cites; the verdict is the human."""
    if not d.caveats:
        return []
    out = ["## ⚠ Analyst caveats — verify before the verdict", ""]
    for c in d.caveats:
        out += _caveat_block(c)
    out.append("")
    return out


# --- D2: the two trajectory views ('Margin trend' + 'Multi-year trajectory') are one story; merge
# them into ONE table here — both are free-text extractor output (unchanged), PARSED here.
_TRAJ_ROWS: tuple[tuple[str, tuple[str, ...]], ...] = (  # (display, source-series aliases)
    ("Revenue ($M)", ("absolute revenue", "revenue")),
    ("EBITDA ($M)", ("absolute ebitda", "ebitda")),
    ("EBITDA margin", ("ebitda margin",)),
    ("Gross margin", ("gross margin",)),
    ("ROIC", ("roic",)),
)


def _parse_traj_series(text: str) -> tuple[dict[str, list[tuple[str, str]]], list[str], str]:
    """Parse 'Label: period val → period val; Label2: …  [note]' → {label_lower: [(period, val)…]},
    the ordered period list (from the first series), and the bracketed note. A segment with <2 '→'
    steps (e.g. the same-quarter YoY line) is NOT a per-period series — skipped here, surfaced as a
    footnote by the caller."""
    note = ""
    mnote = re.search(r"\s*\[([^\]]*)\]\s*$", text)
    if mnote:
        note, text = mnote.group(1).strip(), text[: mnote.start()]
    out: dict[str, list[tuple[str, str]]] = {}
    for seg in text.split("; "):
        if ":" not in seg:
            continue
        label, rest = seg.split(":", 1)
        steps = [s.strip() for s in rest.split(" → ") if s.strip()]
        if len(steps) < 2:
            continue
        pairs = [
            (mm.group("p").strip(), mm.group("v"))
            for st in steps
            if (mm := re.match(r"^(?P<p>.+?)\s+(?P<v>-?[\d,.]+%?)$", st))
        ]
        if pairs:
            out[label.strip().lower()] = pairs
    periods = [p for p, _ in next(iter(out.values()), [])]
    return out, periods, note


def _trajectory_table_lines(m: MechanicalLayer) -> list[str]:
    """(D2) 'Margin trend' + 'Multi-year trajectory' merged into ONE trajectory table (revenue,
    EBITDA, EBITDA margin, gross margin, ROIC) + the same-quarter YoY footnote. Every row the two
    parents carried survives, markers ((R)/(LTM)) preserved, zero value drift (revenue/EBITDA are
    identical in both). Falls back to the raw fact when neither field parses (old JSON safe)."""
    mt, my = m.quality.margin_trend, m.quality.multi_year_trajectory
    merged: dict[str, list[tuple[str, str]]] = {}
    periods: list[str] = []
    notes: list[str] = []
    yoy = ""
    for s in (mt, my):
        if s.status is not SourceStatus.PRESENT or not s.value:
            continue
        parsed, per, note = _parse_traj_series(s.value)
        merged.update(parsed)  # dup keys (revenue/EBITDA) are identical across the two → no drift
        periods = periods or per
        if note:
            notes.append(note)
        if not yoy and (ym := re.search(r"(Revenue YoY[^;\[]*)", s.value)):
            yoy = ym.group(1).strip()
    # match a row's value to a column by a period key NORMALISED of the day + the (R)/(LTM) marker:
    # the extractor marks (R) on the income-statement series but NOT on ROIC, so a raw-string match
    # would blank ROIC in the reclassified columns.
    def _norm(p: str) -> str:
        return re.sub(r"\s*\((?:R|LTM)\)", "", re.sub(r"-\d{1,2}-", "-", p)).strip()

    rows: list[list[str]] = []
    for disp, aliases in _TRAJ_ROWS:
        series = next((merged[a] for a in aliases if a in merged), None)
        if series is not None:
            by_n = {_norm(p): v for p, v in series}
            rows.append([disp, *[by_n.get(_norm(p), "–") for p in periods]])
    if not rows or not periods:  # nothing parsed → fall back to the raw text (back-compat)
        pick = mt if mt.status is SourceStatus.PRESENT else my
        return [_fact("Trajectory (revenue · EBITDA · margins · ROIC)", pick)]
    cols = [re.sub(r"-\d{1,2}-", "-", p) for p in periods]  # "Dec-31-2021"→"Dec-2021"; keep markers
    # (N6) dedupe the footnote at the SEMICOLON-FRAGMENT level — both parent notes lead with
    # "R reclassified", which would otherwise repeat when the two are concatenated.
    frags = [f.strip() for n in notes for f in n.split(";") if f.strip()]
    note = "; ".join(dict.fromkeys(frags))
    note = f"{yoy}. {note}" if yoy else note
    src = mt.source_ref if mt.status is SourceStatus.PRESENT else my.source_ref
    return _table("Trajectory ($M · % — per period)", src, cols, rows, note)


# --- D3: deterministic render-side ordering of bull/bear points. NEVER an LLM/schema field — the
# tier is derived here from the claim text (face-validity keyword map) + the citation source_ref.
# The claim is classified on its PRIMARY assertion — text after a concession marker (N1) is stripped
# first. A point takes the HIGHEST tier (lowest number) whose keywords it matches (checked 1→5); a
# point matching none → tier 4.5 (never dropped). Keyword map declared here + documented in STATE.
_TIER_KEYWORDS: tuple[tuple[float, tuple[str, ...]], ...] = (
    (1.0, ("free cash flow", "levered free cash", "fcf", "self-fund", "self fund", "cash generat",
           "cash burn", "cash-negative", "interest coverage", "maturity", "wall", "covenant",
           "refinanc", "liquidity", "going concern", "solven", "net-debt", "net debt", "total-debt",
           "total debt", "debt/ebitda", "adjusted ebitda negative", "adjusted ebitda was negative",
           # (R1 audit) the bare "turned negative" keyword was REMOVED — it matched a subject-less
           # "competitor guidance turned negative"; the SCOPED _TIER_REGEX carries the real cases.
           "ebitda was negative")),
    (2.0, ("revenue", "top-line", "topline", "volume", "shipment", "bookings", "backlog", "orders",
           "guide", "guidance", "deteriorat", "growth")),
    (3.0, ("margin", "gross profit", "operating leverage", "opex", "cost structure", "profitab",
           "net profit", "non-operating", "earnings quality")),
    (4.0, ("peer", "competit", "customer", "concentrat", "market share", "moat", "supplier",
           "segment")),
    (5.0, ("valuation", "multiple", "p/e", "ev/ebitda", "discount", "re-rate", "rerate",
           "underperform", "percentile", "%ile", "cheap", "expensive", "vs iwm", "relative")),
)
_TIER_NAME: dict[float, str] = {  # (N3) dev-view labels only — never shown in the human view
    1.0: "solvency/cash", 2.0: "revenue trajectory", 3.0: "margin structure",
    4.0: "competitive/concentration", 4.5: "unclassified",
    5.0: "valuation & relative price action",
}
_CITATION_CLASS = ("structured", "transcript", "LLM")  # rank 0/1/2 — the tiebreak within a tier
# (N1) a claim's tier reflects its PRIMARY assertion; everything from the first concession marker on
# is a hedge/counter it acknowledges, not what it argues — so classify on the text BEFORE it.
_CONCESSION = re.compile(
    r"\b(?:though|although|but|however|offset by|posing whether|the human must weigh)\b",
    re.IGNORECASE,
)


def _strip_concession(claim: str) -> str:
    m = _CONCESSION.search(claim)
    return claim[: m.start()] if m else claim


# (R1) word-boundary regexes with INTERPOSITION tolerance — a substring keyword misses "adjusted
# EBITDA OF negative $5.5M" (words between 'EBITDA' and 'negative'); allows ≤3 interposed
# words. Face-validity only (like the keyword map); checked BEFORE the keywords, highest-tier-first.
_TIER_REGEX: tuple[tuple[float, re.Pattern[str]], ...] = (
    (1.0, re.compile(
        # (adjusted) EBITDA ... negative — interposition-tolerant primary case (pins the R1 test)
        r"\b(?:adjusted\s+)?ebitda\b(?:\s+\w+){0,3}\s+negative\b"
        # "... turned negative" ONLY when the SUBJECT is a solvency/cash line (EBITDA above already
        # covers "EBITDA turned negative"); a subject-less "competitor guidance turned negative" no
        # longer false-matches tier-1. (R1 audit fix.)
        r"|\b(?:cash[\s-]*flow|fcf|free\s+cash\s+flow|operating\s+(?:income|cash\s*flow)|ocf)\b"
        r"(?:\s+\w+){0,3}\s+turned\s+negative\b"
        r"|\bcash-negative\b", re.IGNORECASE)),
)


def _point_tier(claim: str) -> float:
    c = _strip_concession(claim)
    cl = c.lower()
    for tier, pat in _TIER_REGEX:  # R1 — interposition-tolerant patterns win first (highest tier)
        if pat.search(c):
            return tier
    for tier, kws in _TIER_KEYWORDS:
        if any(k in cl for k in kws):
            return tier
    return 4.5  # unclassifiable → between competitive (4) and valuation (5); never dropped


def _citation_rank(source_ref: str, cited: bool) -> int:
    s = (source_ref or "").lower()
    if not cited or "llm-suggested" in s or "unverified" in s or "made-up" in s:
        return 2  # LLM-suggested / unsourced
    return 1 if "transcript" in s else 0  # transcript-cited vs structured-fact-cited


def _ordered_points(pts: list[Any]) -> list[tuple[Any, float, int]]:
    """(D3) Sort by (tier, citation-class, original emission index) — a STABLE sort, so ties keep
    emission order and the render is deterministic. Ordering is WITHIN a case only (nothing nets
    across bull vs bear). Returns (point, tier, citation_rank) so the dev view can show the tier."""
    keyed = [
        (p, _point_tier(p.claim), _citation_rank(p.source_ref, getattr(p, "cited", True)), i)
        for i, p in enumerate(pts)
    ]
    keyed.sort(key=lambda t: (t[1], t[2], t[3]))
    return [(p, tier, cr) for p, tier, cr, _ in keyed]


def _twin_outcome(t: Any) -> str:
    """(H6) The outcome on an '[LLM-suggested, unverified]' twin is the MODEL's claim, not a sourced
    analogue — suffix it '(LLM-claimed — verify)' so the human checks it. A roster- or self-sourced
    twin (a real source_ref) renders plain. Deterministic, render-side."""
    src = (getattr(t, "source", "") or "").lower()
    unverified = "llm-suggested" in src or "unverified" in src
    return f"{t.outcome} (LLM-claimed — verify)" if unverified else t.outcome


def _synthesis_lines(d: Dossier, *, dev: bool) -> list[str]:
    """(D1/D3) Synthesis in the facts-first order — evidence balance → bull → bear → decisive
    question → key unknowns → twins (twins LAST). Bull/bear points are deterministically ordered
    (D3, render-side); the [tier · citation-class] tag shows in the DEV view only."""
    s = d.synthesis
    assert s is not None
    out = ["## Synthesis (LLM — framing for the human, every point source-bound)", ""]
    if s.evidence_balance:
        out += [f"**Evidence balance:** {s.evidence_balance}", ""]

    def cite(p: Any, tag: str = "") -> str:
        warn = "" if getattr(p, "cited", True) else " ⚠ uncited"
        return f"- {p.claim}{tag}{warn}\n  - ↳ `{p.source_ref}`"

    def ordered(title: str, pts: list[Any]) -> None:  # D3 — deterministic tier order
        out.append(f"### {title}")
        for p, tier, cr in _ordered_points(pts):
            tag = f" `[T{tier:g} {_TIER_NAME[tier]} · {_CITATION_CLASS[cr]}]`" if dev else ""
            out.append(cite(p, tag))
        out.append("")

    def plain(title: str, pts: list[Any]) -> None:  # emission order (decisive evidence)
        out.append(f"### {title}")
        out.extend(cite(p) for p in pts)
        out.append("")

    ordered("Bull case (overshoot / mean-revert)", s.bull_points)
    ordered("Bear case (terminal / value-trap)", s.bear_points)
    out += ["### Decisive question", f"**{s.decisive_question.question}**", ""]
    plain("…evidence for", s.decisive_question.evidence_for)
    plain("…evidence against", s.decisive_question.evidence_against)
    out += ["### Key unknowns", *[f"- {u}" for u in s.key_unknowns], ""]
    out.append("### Twin reference cases")  # (D1) twins move to the END of the synthesis
    for t in s.twin_reference_cases:
        out.append(f"- **{t.name}** — {_twin_outcome(t)}")
        out.append(f"  - distinguished by: {t.distinguishing_fact}")
        out.append(f"  - source: {t.source}")
    out.append("")
    return out


def render_markdown(d: Dossier, *, dev: bool = False) -> str:
    """(D1) Facts-first restructure. Section order: header → caveats → mechanical layer [drawdown &
    idiosyncrasy (clubbed) → leverage & survival → trajectory → valuation → peer comps → catalyst →
    concentration] → synthesis → appendix (+ management-commentary pointer) → verdict footer. Old
    committed JSONs still render (every field is optional-safe). ``dev`` shows the D3 tier tags."""
    m = d.mechanical
    out: list[str] = [
        f"# Dossier — {d.name} ({d.ticker})",
        "",
        f"_Finalist rank {d.rank} · ref {d.reference_date} · assembled "
        f"{_fmt_assembled(d.assembled_at)} · LLM {d.llm_model or 'none'}_",
        "",
    ]
    # (D1) CAVEATS FIRST — the first thing the human sees is what to verify before trusting below.
    out += _flags_section(d)
    out += ["## Mechanical layer (source-bound facts — assembles & cites, never concludes)", ""]

    # (D1·§1) Drawdown cause & idiosyncrasy — CLUBBED: what happened, and did it happen alone?
    out.append("### Drawdown cause & idiosyncrasy — what happened, and did it happen alone?")
    out += [
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
    out += [
        _fact("Revised guidance (catalyst 8-K Ex-99.1)", m.drawdown_cause.revised_guidance),
        "",
        "_Did it happen alone? (idiosyncratic vs shared — the G2-vs-market compensation):_",
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
    out.append("")

    # (D1·§2) Leverage & survival — the survival story in one place (+ FCF + liquidity).
    if m.leverage_survival is not None:
        out += _leverage_block(m)  # ### Leverage & survival (unified) …
    else:  # pre-B2 JSON: the quality leverage lines under the same header
        out += ["### Leverage & survival", *_quality_leverage_lines(m)]
    out += [
        _fact("FCF sign", m.quality.fcf_sign, _signword),
        _fact("Free cash flow ($M)", m.quality.free_cash_flow),
    ]
    # (E1/E2) structured capital structure + maturity wall replace the flat liquidity string; pre-E
    # dossier.json falls back to the legacy Quality.liquidity_covenant_flags line.
    if m.capital_structure is not None:
        out += _capital_structure_lines(m.capital_structure, d.reference_date)
    else:
        out += [_fact("Liquidity / covenant flags", m.quality.liquidity_covenant_flags), ""]

    # (D1·§3 · D2) Trajectory — the merged margin/multi-year table + share-count trend.
    out.append("### Trajectory (revenue · EBITDA · margins · ROIC)")
    out += _trajectory_table_lines(m)
    out += [_fact("Share-count trend", m.quality.share_count_trend), ""]

    # (D1·§4) Valuation & own-history. (G) implied expectations slot in AFTER cross-sectional (the
    # edge) and BEFORE the own-history reads.
    out.append("### Valuation & own-history")
    out.append(_fact("Cross-sectional (vs peers — the edge)", m.valuation.cross_sectional))
    out += _implied_expectations_lines(m.valuation)
    out += [
        _fact("P/E", m.valuation.pe, _mult),
        _fact("EV/EBITDA (GAAP TEV/LTM)", m.valuation.ev_ebitda, _mult),
        _fact("EV/EBITDA (adjusted, forward)", m.valuation.ev_ebitda_adjusted_fwd),
        _fact("Adjusted EPS (earnings power)", m.valuation.adjusted_eps),
        _fact("Own-history range position", m.valuation.range_position),
        "",
    ]

    # (D1·§5) Peer comps — roster + comparability + multiples + grid + implied valuation.
    out.append("### Peer comps (CIQ Comparable Analysis — consensus comp, framed to RESIST)")
    out += _roster_lines(m.peer_comps.peer_set)
    out.append(_fact("Comparability (confidence gate)", m.peer_comps.comparability))
    out += _multiples_lines(m.peer_comps.trading_multiples)
    out += _peer_grid_or_deltas(m.peer_comps)
    out.append("")
    if m.implied_valuation is not None:
        out += _implied_lines(m.implied_valuation)

    # (D1·§6) Catalyst path (the management-commentary pointer moved to the appendix).
    out += _catalyst_section(m)

    # (D1·§7) Concentration.
    out.append("### Concentration")
    out += [
        _fact("Segments (revenue share)", m.concentration.segments),
        _fact("Segments (EBITDA share — where profit sits)", m.concentration.segment_ebitda),
        _fact("Customers", m.concentration.customers),
        _fact("Geographic", m.concentration.geographic),
        "",
    ]

    # Synthesis — balance → bull → bear → decisive → unknowns → twins.
    if d.synthesis is not None:
        out += _synthesis_lines(d, dev=dev)
    else:
        out += ["## Synthesis", "_Not produced (see flags)._", ""]

    # (D1) appendix (+ the relocated management-commentary pointer), then the verdict footer.
    appendix = _appendix_lines(m)
    out += appendix if appendix else ["## Appendix", ""]
    out += _mgmt_commentary_lines(m)
    out += [
        "---",
        "> **No BUY/AVOID here — this dossier only assembles and cites.** The verdict is the "
        "human's, logged separately via the ledger with a frozen entry price.",
    ]
    return "\n".join(_dedupe_unknown_reasons(out))  # (H3) fold repeated UNKNOWN reasons
