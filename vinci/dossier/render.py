"""Render a :class:`Dossier` to human-readable markdown — source_refs shown INSPECTABLE.

The point of the rendering is that the human verifies the primary datum (the cited filing cell / bar
window / CIQ sheet), not the summary. So every fact prints its ``source_ref``; every UNKNOWN/MISSING
prints why; bull/bear points print their citation and an ⚠ when a guardrail flagged them.
"""

from __future__ import annotations

import contextvars
import functools
import math
import re
from collections import Counter
from collections.abc import Callable
from datetime import UTC, date, datetime
from itertools import groupby
from typing import Any, ParamSpec

from vinci.dossier.covenant_extract import GoverningTerm, _derive_conversion, governing_terms
from vinci.dossier.schemas import Dossier, MechanicalLayer, Sourced, SourceStatus, StockInfo
from vinci.dossier.verdict import MachineProposal, derive_proposal, split_lean

# Display curation for the catalyst path — the full data always stays in dossier.json; these only
# cap/collapse/group the HUMAN view (the margin-trend mini-table idiom: curate display, not data).
_GROUP_CAP = 6  # (T3) revision-event broker-day LINES shown; the rest counted "+N in JSON"
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


# --- (A2) source-ref ENDNOTES: every citation registers into a per-document table and renders as a
# numbered [n] marker; the single Sources list is emitted once at document end. The table is a
# ContextVar reset at the top of render_markdown, so the assemble batch's worker threads never share
# it (each thread has its own context; a pooled thread is reset per render). Outside a render (a
# unit test calling an emitter) the table is None → the inline "↳ `ref`" fallback keeps working.
_ENDNOTES: contextvars.ContextVar[list[str] | None] = contextvars.ContextVar(
    "_dossier_endnotes", default=None)


def _ref_n(source_ref: str) -> int:
    """Register ``source_ref`` (deduped) into the endnote table → its 1-based number."""
    table = _ENDNOTES.get()
    assert table is not None  # callers guard: only invoked inside a render
    if source_ref not in table:
        table.append(source_ref)
    return table.index(source_ref) + 1


def _cite(source_ref: str | None) -> str:
    """(A2) A SUB-LINE citation → its ` [n]` marker in a render, else the "↳ `ref`" sub-line. A
    missing ref (never on a PRESENT fact — the validator enforces it) emits no cite."""
    if not source_ref:
        return ""
    if _ENDNOTES.get() is None:
        return f"\n  - ↳ `{source_ref}`"
    return f" [{_ref_n(source_ref)}]"


def _cite_inline(source_ref: str | None) -> str:
    """(A2) An INLINE citation (header/list-lead) → bare ``[n]`` or "↳ `ref`" (fallback)."""
    if not source_ref:
        return ""
    if _ENDNOTES.get() is None:
        return f"↳ `{source_ref}`"
    return f"[{_ref_n(source_ref)}]"


def _sources_section() -> list[str]:
    """(A2) The single document-end Sources list — every distinct source_ref in first-cited order.
    Empty when nothing was cited. Rendered once by :func:`render_markdown` at the very end."""
    table = _ENDNOTES.get()
    if not table:
        return []
    return ["", "# Sources", "", *[f"[{i}] `{ref}`" for i, ref in enumerate(table, 1)]]


_P = ParamSpec("_P")


def _endnote_scope(fn: Callable[_P, str]) -> Callable[_P, str]:
    """(A2) Run ``fn`` with a FRESH endnote table, then RESTORE the prior value (None outside a
    render) in a ``finally`` — so the documented "↳ `ref`" fallback keeps holding for a direct
    emitter call AFTER a render, and an exception mid-render can't leak a stale table onto a pooled
    worker thread. ``reset(token)`` (not ``set(None)``) restores exactly the pre-render value."""
    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> str:
        token = _ENDNOTES.set([])
        try:
            return fn(*args, **kwargs)
        finally:
            _ENDNOTES.reset(token)
    return wrapper


def _fact(label: str, s: Sourced[Any], fmt: Callable[[Any], str] = str) -> str:
    if s.status is SourceStatus.PRESENT:
        return f"- **{label}:** {fmt(s.value)}{_cite(s.source_ref)}"
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


# (K6) UNKNOWN reasons that describe the SAME underlying gap in DIFFERENT words fold to one render —
# beyond the byte-identical H3 dedup. Each: (matcher, topic-key, canonical reason to render once).
_UNKNOWN_TOPICS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"99\.1|revised[- ]?(?:outlook|guidance)", re.IGNORECASE), "99.1",
     "no revised-outlook 99.1 exhibit parsed — the revised forward guidance is UNKNOWN"),
    (re.compile(r"graph cohort|US-listed exposed names to price|cohort to (?:compare|price)", re.I),
     "graph-cohort", "MVST is in the graph but has no US-listed exposed names to price — UNKNOWN"),
)


def _dedupe_unknown_reasons(lines: list[str]) -> list[str]:
    """(H3 · K6) Collapse repeated UNKNOWN/MISSING fact REASONS to ONE render (first occurrence),
    with the affected-fields list. TWO triggers: (H3) a byte-identical DISTINCTIVE note
    (≥ ``_DEDUPE_MIN_REASON_LEN`` chars) carried by ≥2 fields; (K6) two reasons for the SAME
    gap in different words (a ``_UNKNOWN_TOPICS`` match — the 99.1 revised-guidance gap, the
    graph-cohort gap) fold to one canonical line. No fact is suppressed — every affected field stays
    named. Matches only inline `_fact` UNKNOWN lines (tables / synthesis points / caveats never)."""
    groups: dict[tuple[str, str], list[int]] = {}
    canon: dict[tuple[str, str], str] = {}
    for i, ln in enumerate(lines):
        m = _UNKNOWN_FACT.match(ln)
        if not m:
            continue
        status, reason = m.group(2), m.group(3)
        topic = next((t for pat, t, _c in _UNKNOWN_TOPICS if pat.search(reason)), None)
        key = (status, f"@{topic}" if topic else reason)
        groups.setdefault(key, []).append(i)
        if key not in canon:
            canon[key] = next(c for _p, t, c in _UNKNOWN_TOPICS if t == topic) if topic else reason
    drop: set[int] = set()
    for key, idxs in groups.items():
        status, tag = key
        if len(idxs) < 2 or (not tag.startswith("@") and len(tag) < _DEDUPE_MIN_REASON_LEN):
            continue
        labels = [m.group(1) for i in idxs if (m := _UNKNOWN_FACT.match(lines[i]))]
        lines[idxs[0]] = f"- **{' · '.join(labels)}:** _{status}_ — {canon[key]}"
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
    out = [f"- **{label}** — {_cite_inline(s.source_ref)}:"]
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
    out = [f"- **{label}** — {_cite_inline(s.source_ref)}:"]
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


# (T3) headline metric PRIORITY — each tuple is the substrings a metric must contain (all of them).
_HEADLINE_PRIORITY: tuple[tuple[str, ...], ...] = (("ebitda",), ("revenue",), ("eps", "normal"))


def _pct_delta(e: Any) -> float:
    """(T3) |%Δ| of a revision — |current − prior| / |prior|; -1 when either side is non-numeric or
    prior is 0. Cross-metric RAW deltas are unit-incoherent, so the headline ranks on |%Δ|, never
    raw |Δ| (a big-number Revenue move would otherwise always outrank a bigger-% EBITDA cut)."""
    try:
        prior, cur = float(e.broker_prior), float(e.broker_current)
    except (ValueError, TypeError):
        return -1.0
    return abs(cur - prior) / abs(prior) if prior else -1.0


def _n1(x: Any) -> str:  # a revision value → 1-decimal, or verbatim when non-numeric ('-')
    try:
        return f"{float(x):.1f}"
    except (ValueError, TypeError):
        return str(x)


def _revision_headline(evs: list[Any]) -> Any | None:
    """(T3) The headline revision for a broker-day, by metric PRIORITY (EBITDA > Revenue >
    EPS-Normalized) — the largest-|%Δ| revision of the first priority metric present; else the
    largest-|%Δ| of ANY metric. None when no event carries a clean |%Δ|. Never raw |Δ|."""
    numeric = [e for e in evs if _pct_delta(e) >= 0]
    if not numeric:
        return None
    for kws in _HEADLINE_PRIORITY:
        tier = [e for e in numeric if all(k in e.metric.lower() for k in kws)]
        if tier:
            return max(tier, key=_pct_delta)
    return max(numeric, key=_pct_delta)


def _grouped_events_lines(s: Sourced[Any]) -> list[str]:
    """(4d · T3) Revision events COMPRESSED to ONE line per broker-day — date · broker · action mix
    (n↑/n↓, initiations) · the headline revision (largest-|Δ|, EBITDA-preferred) · '+N items in
    JSON'. Cap ``_GROUP_CAP`` broker-days, the remainder counted; the expanded per-item view is the
    web on-demand tier + the JSON. Full list always in dossier.json."""
    label = "Revision-event log"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    events = s.value
    groups: dict[tuple[str, str], list[Any]] = {}
    for e in events:
        groups.setdefault((e.date, e.broker), []).append(e)
    keys = sorted(groups, key=lambda k: k[0], reverse=True)  # most-recent broker-day first
    out = [f"- **{label}** ({len(events)} events · {len(keys)} broker-days) "
           f"— {_cite_inline(s.source_ref)}:"]
    for dt, broker in keys[:_GROUP_CAP]:
        evs = groups[(dt, broker)]
        ct = Counter(e.change_type for e in evs)
        ups = sum(n for t, n in ct.items() if "upward" in t.lower())
        downs = sum(n for t, n in ct.items() if "downward" in t.lower())
        inits = sum(n for t, n in ct.items() if "initiation" in t.lower())
        mix = f"{ups}↑/{downs}↓" + (f", {inits} initiations" if inits else "")
        head = _revision_headline(evs)
        headline = (f" · {head.metric} {head.period} {_n1(head.broker_prior)}→"
                    f"{_n1(head.broker_current)}" if head else "")
        rest = len(evs) - (1 if head else 0)
        out.append(f"  - **{dt} · {broker}** · {mix}{headline}"
                   + (f" · +{rest} items in JSON" if rest > 0 else ""))
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
    num_cols: frozenset[int] = frozenset(),
) -> list[str]:
    """The single shared markdown table renderer (B4). Emits a GFM table tagged with ``_TABLE_MARK``
    so a test confirms every table routes here; ``name_rows`` indices bold the subject. Every
    cell is pipe/newline-sanitised (:func:`_gfm_cell`) so free-text (E5 verbatim) can't break it.
    ``num_cols`` (indices into ``cols``) right-align numeric columns (K2)."""
    head = f"- **{label}**" + (f" — {_cite_inline(cite)}" if cite else "") + f"  {_TABLE_MARK}"
    # (K2) GFM alignment row — numeric cols right-align (`---:`); col 0 is the prepended blank cell.
    aligns = ["---", *("---:" if i in num_cols else "---" for i in range(len(cols)))]
    out = [head, "", "| " + " | ".join(_gfm_cell(c) for c in [" ", *cols]) + " |",
           "|" + "|".join(aligns) + "|"]  # (K2) `---:` right-aligns; keep the `|---` table marker
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
        # half-up at 1dp (floor(x*10+0.5)/10) to MATCH dossier.js _ratioC + the _pctc convention —
        # Python :.1f is banker's (half-to-even), disagreeing with the web/PDF at a quarter-tie
        # (7.25 → 7.2 vs 7.3). floor(x*10+0.5) == JS Math.round(x*10) on the same IEEE double.
        return f"{math.floor(float(s) * 10 + 0.5) / 10:.1f}"
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
    """(B1/B2) Per-peer comparability grid: peers + the name (bolded) + the median footer;
    cap · TEV/EBITDA · TEV/Rev · P/E · margin · rev growth · Debt/EBITDA · net debt. No computed
    delta — the human compares the name row against the peers + the median. (EBITDA growth stays in
    the JSON; the grid is capped at 8 value columns for print — the valuation multiples lead.)"""
    label = "Per-peer grid (cap · valuation · margin · growth · leverage — name vs peers)"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    # full-word headers; 8 value columns — the row LABEL is the company (the shared renderer adds
    # the empty label header), so the header count matches the cell count exactly.
    cols = ["Cap", "TEV/EBITDA", "TEV/Rev", "P/E", "EBITDA margin", "Rev growth (1y)",
            "Total debt/EBITDA", "Net debt ($M)"]
    trows: list[list[str]] = []
    name_rows: set[int] = set()
    for i, r in enumerate(s.value):
        if r.is_name:
            name_rows.add(i)
        tag = " · the name" if r.is_name else (" (peers)" if r.is_median else "")
        trows.append([
            r.name + tag, _cap(r.market_cap), _ratioc(r.tev_ebitda), _ratioc(r.tev_rev),
            _ratioc(r.pe), _pctc(r.ebitda_margin), _pctc(r.rev_growth_1y),
            _ratioc(r.debt_to_ebitda), _netdebt(r.net_debt),
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


_CH_DIMS = ("Overall", "Operational", "Solvency", "Liquidity")
_CH_NAME_RE = re.compile(
    r"Overall/Operational/Solvency/Liquidity\s+([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)")
_CH_PEER_RE = re.compile(r"peer-median\s+O/Op/S/L\s+([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)")


def _credit_health_lines(lv: Any) -> list[str]:
    """(K3) Credit health as a 4-row mini-table (dimension | name | peer median) parsed from the
    prose ``credit_health`` value, with a scale footnote. Render-side only — no extractor change.
    Falls back to the plain fact if the shape isn't as expected — never a fabricated score."""
    ch = lv.credit_health
    if ch.status is not SourceStatus.PRESENT or not ch.value:
        return [_fact("Credit health", ch)]
    text = str(ch.value)
    nm, pr = _CH_NAME_RE.search(text), _CH_PEER_RE.search(text)
    if not nm or not pr:  # unknown shape → the plain fact, not a fabricated table
        return [_fact("Credit health", ch)]
    rows = [[dim, nm.group(i + 1), pr.group(i + 1)] for i, dim in enumerate(_CH_DIMS)]
    scale = re.search(r"scale\b.*", text)
    rating = re.search(r"\(([^)]*(?:issuer rating|unrated|rated)[^)]*)\)", text)
    note = " · ".join(p for p in ((rating.group(1) if rating else ""),
                                  (scale.group(0) if scale else "")) if p)
    # (audit) the dimension is the ROW LABEL (the blank column `_table` prepends) — NOT a `col`,
    # else the 3-cell rows sit under a 4-cell header and every score shifts one column left.
    return _table("Credit health", ch.source_ref, ["Name", "Peer median"], rows,
                  note=note, num_cols=frozenset({0, 1}))


def _leverage_block(m: MechanicalLayer) -> list[str]:
    """(B2) Unified leverage & survival — ALL leverage in ONE block, both bases LABELED (no
    net-vs-total mixing) + OCF/fwd-adj + credit health. Replaces the scattered Quality leverage
    lines (which fall back for a pre-B2 dossier.json)."""
    lv = m.leverage_survival
    assert lv is not None
    lines = [
        "### Leverage & survival",  # (K5) header humanized; the net-vs-total discipline is per-row
        _fact("Net debt / EBITDA (CIQ NET basis)", lv.net_debt_to_ebitda, _mult),
        _fact("Total debt / EBITDA (comps — name vs peer median)", lv.total_debt_to_ebitda),
        _fact("Net debt / OCF", m.quality.net_debt_to_ocf, _mult),
        _fact("Net debt / EBITDA (fwd-adj covenant basis)", m.quality.net_debt_to_ebitda_adjusted),
        _fact("Interest coverage", lv.interest_coverage, _mult),
        _fact("Survival (self-funding + nearest wall)", lv.survival),
    ]
    # (RC-1 C) the two-input self-funding read SUPERSEDES the one-input survival claim above —
    # placed adjacent so the correction is unmissable (MVST 'self-funding' is actually MIXED).
    ps = m.primary_source
    if ps is not None and ps.self_funding.status is SourceStatus.PRESENT:
        lines.append(_fact("Self-funding — two-input read (supersedes the line above)",
                           ps.self_funding))
    return [*lines, *_credit_health_lines(lv), ""]


def _event_impact_lines(m: MechanicalLayer) -> list[str]:
    """(RC-1 C) Event-impact quantifications parsed from the 8-K EX-99.1 (the Avis class: 'expects
    the termination to reduce … revenue by ~$135–145M') — rendered in the drawdown-cause section as
    quantified effect. Deduped; each source-bound. Empty for a pre-RC-1 JSON or a name with none."""
    ps = m.primary_source
    if ps is None:
        return []
    out: list[str] = []
    seen: set[tuple[str, str, float | None, float | None]] = set()
    for r in ps.releases:
        for ei in r.event_impacts:
            key = (ei.metric, ei.effect, ei.low, ei.high)
            if key in seen:
                continue
            seen.add(key)
            if not out:
                out.append("- **Event-impact quantifications (8-K EX-99.1, verbatim-bound):**")
            rng = (f"${ei.low:,.0f}–{ei.high:,.0f}M" if ei.low is not None and ei.high is not None
                   else "unquantified")
            out.append(f"  - {ei.effect} {ei.metric} by {rng} ({ei.period}) "
                       f"— {_cite_inline(ei.source_ref)}")
    return out


def _primary_source_block(m: MechanicalLayer) -> list[str]:
    """(RC-1 C) Primary-source cross-checks — the four cross-source derivations over the actual 8-K
    releases + latest 10-Q vs the CIQ/EDGAR panel. Decision data → MAIN BODY. Going-concern LEADS
    unsoftened when doubt is stated, else the CHECKED-ABSENCE ('none in latest 10-Q'). Empty for a
    pre-RC-1 dossier.json (primary_source absent)."""
    ps = m.primary_source
    if ps is None:
        return []
    fil = ps.filing
    out = ["### Primary-source cross-checks (8-K releases + latest 10-Q vs CIQ panel)", ""]
    gc = fil.going_concern if fil is not None else None
    if gc is not None and gc.substantial_doubt:  # doubt LEADS, unsoftened
        out += [f"- **⚠ Going concern — SUBSTANTIAL DOUBT:** {gc.verbatim}{_cite(gc.source_ref)}",
                f"  - management's plans: {gc.plans or '— none stated'}"]
    elif fil is not None:  # CHECKED-ABSENCE (not silence): the parser looked and found none
        out.append(f"- **Going-concern language:** none in latest 10-Q — checked, absent "
                   f"{_cite_inline(fil.source_ref)}")
    else:
        out.append("- **Going-concern language:** _UNKNOWN_ — latest 10-Q not parsed")
    out.append(_fact("Wall coherence — filing ≤12m vs CIQ panel (same window)", ps.wall_coherence))
    tri_val = ps.basis_triangulation.value
    if tri_val is not None:  # multi-line → bold header + sub-bullets
        tri = tri_val.split("\n")
        out.append(f"- **{tri[0]}**{_cite(ps.basis_triangulation.source_ref)}")
        out += [f"  - {row.strip()}" for row in tri[1:] if row.strip()]
    out.append(_fact("Guide verification — CIQ guide vs release", ps.guide_verification))
    cc = fil.concentration if fil is not None else None
    if cc is not None and cc.customers:
        out.append(f"- **Customer concentration (latest 10-Q):**{_cite(cc.source_ref)}")
        for c in cc.customers:
            kind = " _(disclosed floor)_" if c.value_kind == "floor" else ""
            prior = f" (prior {c.prior_pct:.1f}%)" if c.prior_pct is not None else ""
            out.append(f"  - {c.name}: {c.pct:.1f}%{kind}{prior}")
        if cc.terms:
            out.append(f"  - order terms: {cc.terms}")
    return [*out, ""]


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


_CS_COLS = ["Type", "Principal", "Coupon", "Floating", "Maturity", "Sec", "Conv", "Cur"]
_CS_NUM = frozenset({1})  # (K2) the Principal column right-aligns


def _instrument_row(i: Any) -> list[str]:
    """One instrument → a table row (description is the row LABEL under ``_table``'s blank cell)."""
    return [i.description, i.type, _musd(i.principal_musd), i.coupon or "–", i.floating_rate or "–",
            i.maturity_date or "undated", "Y" if i.secured else "N", "Y" if i.convertible else "N",
            i.currency]


def _near_dated(i: Any, ref: date) -> bool:
    """(K1) A live near-dated tranche for the MAIN body: matured / ≤ ref-year / the next year (≤12m
    + 2027 for a 2026 reference). Undated line items (leases, notes payable) → the appendix."""
    if i.maturity_date is None:
        return False
    return date.fromisoformat(i.maturity_date).year <= ref.year + 1


def _clip(s: str, n: int) -> tuple[str, bool]:
    """Collapse whitespace + clip a verbatim clause to ≤``n`` chars (… when cut). Returns
    ``(clipped, was_trimmed)`` — the caller adds a 'full verbatim in JSON' note only when trimmed.
    The full verbatim lives in the appendix / JSON."""
    s = re.sub(r"\s+", " ", str(s)).strip()
    return (s, False) if len(s) <= n else (s[:n - 1].rstrip() + "…", True)


def _clip120(s: str) -> str:
    """(K1) ≤120-char clause for the curated main body — full verbatim in the appendix + JSON."""
    return _clip(s, 120)[0]


# (K1) governing-term name → short label for the curated main-body covenant line (survival-critical
# only; principal is in the instruments panel; security/guaranty/agent/law detail → appendix).
_SUMMARY_TERMS = (
    ("financial-maintenance", "Financial maintenance"), ("conversion", "Conversion"),
    ("interest", "Interest / coupon"), ("maturity date", "Maturity"),
    ("mandatory prepayment", "Events of default"),
)


_MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December")
_DATE_RE = rf"(?:{_MONTHS})\s+\d{{1,2}},\s+\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}}"


_CADENCE = {"week": "weekly", "month": "monthly", "quarter": "quarterly", "day": "daily",
            "year": "annually"}


def _clause_numbers(raw: str) -> list[float]:
    """(RC-1.5d) Every number stated in the clause, as floats (thousands-commas stripped) — the
    consistency guard checks each structured rate component against this set so a transcription slip
    can never headline the row."""
    out: list[float] = []
    for tok in re.findall(r"\d+(?:\.\d+)?", raw.replace(",", "")):
        try:
            out.append(float(tok))
        except ValueError:  # pragma: no cover — the regex only yields parseable tokens
            continue
    return out


def _num_in_clause(v: float, nums: list[float]) -> bool:
    """True iff ``v`` appears among the clause's numbers (format-tolerant: 3.0 matches '3.00')."""
    return any(abs(v - n) < 1e-6 for n in nums)


def _fmt_bps(v: float) -> str:
    """A bps value AS DISCLOSED — integer when whole ('115'), else the decimal ('112.5'). No
    normalization to percent (the brief: bps stays bps). ``v`` is finite (``_opt_float`` gates
    non-finite out) and in a realistic bps range, so ``str`` never uses exponential notation."""
    return str(int(v)) if v == int(v) else str(v)


def _fmt_pct(v: float) -> str:
    """A percent rate component AS DISCLOSED — the value's EXACT shortest decimal, padded to a
    MINIMUM of 2 decimals: 3.0→'3.00', 9.75→'9.75', 6.125→'6.125' (an eighth-of-a-point coupon).
    NEVER a lossy 2-decimal round (``f"{6.125:.2f}"`` is '6.12', mis-rounding a decision rate AND
    diverging from JS ``toFixed(2)`` which yields '6.13' — the H2 mirror-drift hazard). py/JS
    byte-identical: both use the shortest round-trip repr. ``v`` is finite, 0–100% (``_opt_float``
    gates non-finite), so ``repr`` never uses exponential notation."""
    intpart, _, frac = repr(v).partition(".")
    frac = (frac + "00")[:2] if len(frac) <= 2 else frac
    return f"{intpart}.{frac}"


def _compose_interest_lead(term: GoverningTerm | None, raw: str) -> tuple[str, str]:
    """(RC-1.5d) The interest value-lead COMPOSED FROM STRUCTURE — never re-parsed from the clause.
    Returns ``(lead, qa)``: the composed lead (e.g. 'Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK)')
    or '' when the components are absent/incomplete, plus a QA note when the consistency guard
    tripped (else ''). REQUIRED: ``base_rate_label`` + exactly one of ``margin_pct``/``margin_bps``;
    ``floor_pct``/``pik_pct`` optional. COMPONENT-CONSISTENCY GUARD: each numeric component's digits
    must appear in the parent clause; a mismatch OR both margins present ⇒ no lead + QA (a slip must
    never headline the row). Units render AS DISCLOSED (bps stays bps). A ``term`` of None (a
    pre-RC-1.5d JSON, no components) ⇒ no lead — the clause carries it, no crash."""
    if term is None:
        return "", ""
    base = (term.base_rate_label or "").strip()
    m_pct, m_bps = term.margin_pct, term.margin_bps
    if not base or (m_pct is None and m_bps is None):
        return "", ""  # required components absent → clause alone
    if m_pct is not None and m_bps is not None:
        return "", "both a percent and a bps margin given — ambiguous, lead suppressed"
    nums = _clause_numbers(raw)
    for comp in (m_pct, m_bps, term.floor_pct, term.pik_pct):
        if comp is None:
            continue
        if not math.isfinite(comp):  # defence-in-depth: a non-finite never headlines, never crashes
            return "", "a rate component is not a finite number — lead suppressed"
        if not _num_in_clause(comp, nums):
            return "", f"rate component {_fmt_bps(comp)} not stated in the clause — lead suppressed"
    if m_pct is not None:
        margin = f"{_fmt_pct(m_pct)}%"
    else:
        assert m_bps is not None  # exactly one margin present (guarded above)
        margin = f"{_fmt_bps(m_bps)} bps"
    extras = [x for x in (
        f"Floor {_fmt_pct(term.floor_pct)}%" if term.floor_pct is not None else "",
        f"+{_fmt_pct(term.pik_pct)}% PIK" if term.pik_pct is not None else "") if x]
    lead = f"{base} + {margin}" + (f" ({', '.join(extras)})" if extras else "")
    return lead, ""


def _covenant_value_lead(label: str, raw: str, term: GoverningTerm | None = None) -> str:
    """(K1, generalized · audit-hardened) The extractable VALUE a curated covenant line LEADS with,
    before the ≤120c clip — RIGHT or ABSENT, never wrong. The interest lead is COMPOSED FROM the
    term's structured rate components (RC-1.5d) — no clause re-parse; the other branches stay
    ANCHORED on the verbatim clause (a TEST-anchored cadence, a maturity-anchored date, a contiguous
    1..k enumeration) so ambiguous prose yields '' and the clause carries it. NEVER fabricates."""
    if label == "Conversion":
        return _derive_conversion(raw).strip().lstrip("(").rstrip(")")
    if label == "Financial maintenance":
        thr = re.search(r"not less than\s+\$[\d,]*\d(?:\.\d+)?", raw)  # end on a digit (no trail ,)
        if not thr:
            return ""
        # cadence ONLY when anchored to the TEST ("as of/tested … each <unit>") — not a forecast
        cad = re.search(r"(?:as of|tested)\b[^.;]{0,40}?\beach\s+(?:calendar\s+|fiscal\s+)?"
                        r"(week|month|quarter|day|year)", raw, re.IGNORECASE)
        return f"{thr.group(0)} {_CADENCE.get(cad.group(1).lower(), '') if cad else ''}".strip()
    if label == "Interest / coupon":
        return _compose_interest_lead(term, raw)[0]  # composed from structure; fixed-rate → clause
    if label == "Maturity":
        repl = re.search(rf"replaced with[^.;]*?({_DATE_RE})", raw, re.IGNORECASE)  # amendment wins
        anch = re.search(rf"(?:maturity\s*date|matur\w+)[^.;]{{0,40}}?({_DATE_RE})", raw,
                         re.IGNORECASE)  # else a maturity-anchored date, not a random first date
        m = repl or anch or re.search(_DATE_RE, raw)  # else first date (case-sensitive on months)
        return m.group(1 if (repl or anch) else 0) if m else ""
    if label == "Events of default":
        nums = {int(n) for n in re.findall(r"(?<![\$\d.])\b(\d{1,2})\.\s", raw)}  # contiguous 1..k
        k = 0
        while k + 1 in nums:  # a section number / dollar figure can't inflate the count
            k += 1
        acc = "acceleration" if re.search(r"acceler", raw, re.IGNORECASE) else ""
        return "; ".join(p for p in (f"{k} enumerated" if k >= 2 else "", acc) if p)
    return ""


def _covenant_summary_lines(cs: Any) -> list[str]:
    """(K1) CURATED covenant summary for the MAIN body — the governing VALUES that drive survival
    (financial-maintenance / conversion / interest / maturity / a 1-line events-of-default), each a
    ≤120-char clause; the conversion line leads with the derived $/sh. Debt families only — the
    RSU/equity-incentive family is appendix-only. Full per-family tables live in the appendix
    + JSON; returns nothing (the appendix carries the detail) when there are no governing rows."""
    rows_s = getattr(cs, "covenant_term_rows", None)
    ptrs = getattr(cs, "covenant_pointer_rows", None)
    if rows_s is None or rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return []
    gov = governing_terms(rows_s.value, ptrs.value if ptrs is not None and ptrs.value else [])
    fams: list[str] = []
    for g in gov:
        fl = g.family.lower()
        if "material contract" in fl or "incentive" in fl:  # RSU/equity exhibit → appendix-only
            continue
        if g.family not in fams:
            fams.append(g.family)
    out: list[str] = []
    for fam in fams:
        parts: list[str] = []
        for g in (t for t in gov if t.family == fam):
            if g.value.status is not SourceStatus.PRESENT:
                continue
            label = next((lbl for key, lbl in _SUMMARY_TERMS if key in g.term.lower()), None)
            if label is None:
                continue
            raw = str(g.value.value)
            lead = _covenant_value_lead(label, raw, g)  # (K1) lead with the extractable value
            clause = f"{lead} · {_clip120(raw)}" if lead else _clip120(raw)
            parts.append(f"  - **{label}:** {clause}")
        if parts:
            out.append(f"- **Covenants — {fam}** (governing values; full verbatim in appendix):")
            out += parts
    return out


def _capital_structure_lines(cs: Any, reference_date: date) -> list[str]:
    """(E1/E2–E5 · K1) Capital structure — MAIN body (curated): the live near-dated tranches (≤12m +
    2027) with their economics, the month-precision maturity wall + reconciliation, the QoQ
    aggregates, the maturity-resolution verbatim, and a CURATED covenant-values summary. The full
    instrument panel, the 8-K/covenant pointer tables, and the full per-family covenant tables move
    to the appendix (:func:`_capital_structure_appendix_lines`) — machine-complete JSON, curated
    surface."""
    inst = cs.instruments
    out: list[str] = []
    if inst.status is SourceStatus.PRESENT and inst.value:
        near = [i for i in inst.value if _near_dated(i, reference_date)]
        moved = len(inst.value) - len(near)
        note = (f"{moved} undated / later aggregate line item(s) in the appendix panel"
                if moved else "")
        out += _table(f"Live instruments — near-dated (≤12m + {reference_date.year + 1}) — panel "
                      f"{cs.detail_as_of}", inst.source_ref, _CS_COLS,
                      [_instrument_row(i) for i in near], note=note, num_cols=_CS_NUM)
    else:
        out.append(_fact("Capital structure (instruments)", inst))
    out += _maturity_wall_lines(cs, reference_date)
    out.append(_fact("Capital-structure aggregates (latest quarter)", cs.summary))
    # (P3/FIX-3) the VERBATIM resolution at the maturity 8-K, when captured (the 8-K pointer list
    # itself is provenance → appendix). A pre-P3 dossier.json has no field → nothing.
    mat_ev = getattr(cs, "maturity_event", None)
    if mat_ev is not None and (mat_ev.status is not SourceStatus.PRESENT or mat_ev.value):
        out.append(_fact("Maturity resolution (8-K verbatim)", mat_ev))
    out += _covenant_summary_lines(cs)
    out.append("")
    return out


def _capital_structure_appendix_lines(cs: Any) -> list[str]:
    """(K1) Capital-structure PROVENANCE for the appendix: the full instrument panel (incl. undated
    line items), the 8-K maturity-filing pointers, the covenant/contract pointer table, and the full
    per-family governing covenant tables (verbatim quotes, agent/governing-law/guaranty rows,
    amendment chains). Rendered whenever a capital_structure exists (render_markdown guards that) —
    (audit C1) the old instruments-empty early-return DROPPED the relocated 8-K/pointer/covenant
    flat facts when there was no structured panel; removed, so nothing is lost from the surface. The
    8-K/pointer/covenant `_fact`s below always render (UNKNOWN-safe). Relocated + kept in JSON."""
    inst = cs.instruments
    # (T1) the ON-DEMAND / audit tier: the md keeps it in full under this marker; the web collapses
    # it in a <details> that print excludes; the JSON is machine-complete. Nothing deleted.
    out: list[str] = ["", "### Capital-structure provenance — on-demand (web collapsed · print-"
                      "excluded · JSON) — full panel · pointers · terms"]
    if inst.status is SourceStatus.PRESENT and inst.value:
        out += _table(f"Capital structure — full instrument panel {cs.detail_as_of}",
                      inst.source_ref, _CS_COLS, [_instrument_row(i) for i in inst.value],
                      num_cols=_CS_NUM)
    out.append(_fact("8-Ks at instrument maturities", cs.maturity_filings))
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
    """(P5/E5) Fenced Tier-2 covenant terms, TERM-GOVERNED — ONE table per instrument family, each
    term collapsed to its GOVERNING value (an amendment overrides the base), the source citing
    the base § with an "amended by <accession>" chain. No UNKNOWN row is ordered above a present
    answer (governing_terms takes the latest PRESENT). A pre-H1d dossier.json falls back to the flat
    one-line string."""
    rows_s = getattr(cs, "covenant_term_rows", None)
    if rows_s is None or rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return [_fact("Covenant terms (from the filed agreement)", cs.covenant_terms)]
    ptrs = getattr(cs, "covenant_pointer_rows", None)
    gov = governing_terms(rows_s.value, ptrs.value if ptrs is not None and ptrs.value else [])
    if not gov:
        return [_fact("Covenant terms (from the filed agreement)", cs.covenant_terms)]
    families: list[str] = []
    for g in gov:
        if g.family not in families:
            families.append(g.family)
    cols = ["Governing value (lead · clause ≤200c)", "Source §"]
    out: list[str] = []
    for fam in families:
        fam_terms = [g for g in gov if g.family == fam]
        # (T2) the family source lineage moves to the table FOOTER, not repeated on every row: the
        # base accession/exhibit + the amendment-accession chain.
        present_bases = [g.base_ref for g in fam_terms
                         if g.value.status is SourceStatus.PRESENT and g.base_ref]
        fam_base = present_bases[0] if present_bases else rows_s.source_ref
        amend_accs = sorted({a for g in fam_terms for a in g.amended_by})
        footer = ("Source §: " + str(fam_base)
                  + (f" · amended by {', '.join(amend_accs)}" if amend_accs else ""))
        rows: list[list[str]] = []
        for g in fam_terms:
            v = g.value
            if v.status is not SourceStatus.PRESENT:  # UNKNOWN — one row, not above a present (P5)
                rows.append([g.term, "UNKNOWN", v.note or "not stated"])
                continue
            # (T2) value = the extractable value-lead + a ≤200c clause; 'full verbatim in JSON' only
            # when the clause was actually trimmed.
            label = next((lbl for key, lbl in _SUMMARY_TERMS if key in g.term.lower()), None)
            verbatim = str(v.value)
            # (RC-1.5d) the interest lead composes from structure and carries a QA note when the
            # consistency guard trips (a slipped/ambiguous rate component → clause alone + QA); the
            # QA note is an audit-tier annotation (this appendix table is on-demand, not main body).
            if label == "Interest / coupon":
                lead, qa = _compose_interest_lead(g, verbatim)
            else:
                lead, qa = (_covenant_value_lead(label, verbatim, g) if label else ""), ""
            clause, trimmed = _clip(verbatim, 200)
            cell = (f"{lead} · {clause}" if lead else clause) + (
                " — full verbatim in JSON" if trimmed else "") + (f" — ⚠ QA: {qa}" if qa else "")
            # source §: an off-family base (≠ the family footer) annotates inline; an amended row
            # keeps its amendment ref; a plain base row points at the footer.
            if g.base_ref and g.base_ref != fam_base:
                ref = g.base_ref
            elif g.amended_by:
                ref = f"amended by {', '.join(g.amended_by)}"
            else:
                ref = "base (footer)"
            rows.append([g.term, cell, ref])
        out += _table(f"Covenant terms — {fam} (governing agreement)", rows_s.source_ref,
                      cols, rows, note=footer)
    # (FIX-2) ONE human line inside the covenant block for located agreement exhibits NOT extracted
    # this run (cost bound / fetch fail) — the per-exhibit machine detail is a QA flag, not a
    # caveat. Derived: located pointer accessions minus the accessions the extraction actually read.
    located = {p.accession for p in (ptrs.value if ptrs is not None and ptrs.value else [])
               if p.accession}
    extracted = {m.group(1) for r in rows_s.value
                 if (m := re.search(r"\b(\d{10}-\d{2}-\d{6})\b",
                                 r.value.source_ref or r.value.note or ""))}
    missing = sorted(located - extracted)
    if missing:
        out.append(f"- _{len(missing)} located agreement exhibit(s) not extracted this run "
                   f"(cost bound / fetch fail) — see the pointer table: {', '.join(missing)}_")
    return out


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
        f"- **What the current price implies (at stated multiples)** — "  # (K4) human-facing rename
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
        "Price-implied levels (at each stated multiple)", ie.tev.source_ref,
        ["Multiple (× used)", "Implied level"], rows, name_rows=name_rows)
    out.append("  - _Reads AGAINST the consensus path anchors below — juxtapose the price-implied "
               "level vs consensus per metric; never subtract one from the other._")  # (K4)
    # (audit) H7/P8 made BOTH EBITDA and Revenue anchors UNKNOWN-able — they read the DIRECT
    # Estimates→Trends levels (may lack FY26/FY27), so show the NOTE via _sourced_str, never bare
    # "None". rev_anchors is guarded the same way (no longer the always-PRESENT ladder).
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
    """(B3 · K4) DEMOTED to the appendix, reference-only: implied EQUITY at the peer-MEDIAN multiple
    for the 3 decision bases (LTM EBITDA · NTM EBITDA · NTM Revenue), with the name's ACTUAL market
    cap adjacent. MEDIAN column only — full Low/Mean/High + all other bases stay in the JSON.
    No computed %/discount/upside; the heterogeneity gate renders short on the header."""
    g = iv.comparability_gate
    gate = g.value if g.status is SourceStatus.PRESENT else ""
    out = [
        "### Reference: CIQ implied equity at peer-median multiples",  # (K4) renamed + demoted
        f"> **Comparability gate:** {_gate_shortref(gate)}" if gate else "",  # (H3) short-ref
        "> _Reference only — the human judges earned vs residual (not a machine upside); the full "
        "Low/Mean/High and all bases are in the JSON._",
        _fact("Name market cap ($M) — the ADJACENT fact to compare against", iv.market_cap),
        _fact("Bridge (TEV → equity)", iv.bridge),
    ]
    eq = iv.implied_equity
    if eq.status is SourceStatus.PRESENT and eq.value:
        keep = ("LTM EBITDA", "NTM EBITDA", "NTM Revenue")  # (K4) the 3 decision bases only
        # (audit C4) word-boundary, not substring — so "NTM EBITDA" doesn't match "NTM EBITDAR"
        rows = [[r.basis, _numc(r.median)] for r in eq.value
                if any(re.match(rf"{re.escape(k)}\b", r.basis) for k in keep)]
        out += _table("Implied equity at peer-median ($M, CIQ)", eq.source_ref,
                      ["Implied equity (median)"], rows, num_cols=frozenset({0}))
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
        "### Management commentary",  # (K5) 'transcript pointer, not an excerpt' noted on the fact
        _fact("Earnings call (transcript pointer — read the file)", m.management_commentary),
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
           # (A4) BOTH "going concern" and "going-concern" — the hyphen variant was missed, sinking
           # a stated going-concern to 'unclassified' at the bottom (the codebase idiom double-lists
           # variants, cf. net-debt / net debt below).
           "refinanc", "liquidity", "going concern", "going-concern", "solven", "net-debt",
           "net debt", "total-debt", "total debt", "debt/ebitda", "adjusted ebitda negative",
           "adjusted ebitda was negative",
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
        # (K6, FINAL widening) adjusted EBITDA within ~40 chars of a negative marker (-$/(/negative)
        r"|\badjusted\s+ebitda\b.{0,40}?(?:-\s*\$|\(|negative)"
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
    out = ["## Synthesis", ""]  # (K5) 'LLM framing, source-bound' discipline is in each cite
    if s.evidence_balance:
        out += [f"**Evidence balance:** {s.evidence_balance}", ""]

    def cite(p: Any, tag: str = "") -> str:
        warn = "" if getattr(p, "cited", True) else " ⚠ uncited"
        return f"- {p.claim}{tag}{warn}{_cite(p.source_ref)}"

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


# --- (Brief) first-cut tier -------------------------------------------------------------------
# Leads the dossier with the machine's assembled READ (evidence_balance), its PROPOSED verdict
# (the 2026-07-13 pivot: a deterministic, face-validity-frozen derivation of the lean — see
# vinci/dossier/verdict.py; the LLM still emits no verdict field), the decisive question, a compact
# decision-data strip, and only the DECISION-THREATENING caveats. The HUMAN's confirm/override is
# the verdict of record — a ledger/frontend concern (this static md never renders a logged verdict;
# the web mirror shows it as a read-only status chip). Mirrors briefTier() in frontend dossier.js.

# Caveats worth surfacing on the Brief: the ones that threaten the DECISION (leverage basis,
# going-concern, wall/liquidity, dilution…). Freshness/plumbing caveats (parse counts, export-date
# floors, as-of stamps) stay in the full caveats block below, off the Brief.
_BRIEF_DECISION_KW = re.compile(
    r"leverage|covenant|going.?concern|maturity|wall|liquidity|dilut|solven|"
    r"\bbasis\b|runway|refinanc|\bcash\b", re.IGNORECASE)


def _going_concern_brief(m: MechanicalLayer) -> str | None:
    """The going-concern flag as one Brief line, source-bound. ``None`` when the primary-source
    filing (or its going-concern read) is absent — never a fabricated 'not flagged'."""
    ps = m.primary_source
    fil = ps.filing if ps is not None else None
    gc = fil.going_concern if fil is not None else None
    if gc is None or fil is None:
        return None
    ref = fil.source_ref or "latest 10-Q"
    state = "⚠ SUBSTANTIAL DOUBT stated" if gc.substantial_doubt else "not flagged"
    return f"- **Going concern:** {state}{_cite(ref)}"


def _brief_verify_first(caveats: list[str], limit: int = 2) -> list[str]:
    """Only DECISION-THREATENING caveats (lead clause), never freshness/plumbing ones."""
    out: list[str] = []
    for c in caveats:
        if not _BRIEF_DECISION_KW.search(c):
            continue
        lead = re.split(r";|\s+—\s+", c, maxsplit=1)[0].strip()
        if len(lead) > 120:
            lead = lead[:117].rstrip() + "…"
        out.append(lead)
        if len(out) >= limit:
            break
    return out


def _brief_case_lines(s: Any) -> list[str]:
    """THE CASE, condensed — top-3 bull / top-3 bear (same evidence-weighted order as Analysis) +
    top-3 key unknowns. The FULL synthesis stays in the Analysis tier; source-bound here too."""
    if s is None or (not s.bull_points and not s.bear_points):
        return []
    out: list[str] = ["**The case** _(top points; the full bull/bear is in Analysis)_", ""]

    def top3(pts: list[Any]) -> list[str]:
        top = [p for p, _tier, _cr in _ordered_points(pts)][:3]
        return [f"- {p.claim}{_cite(p.source_ref)}" for p in top]

    out += ["_Bull — overshoot:_", *(top3(s.bull_points) or ["- —"])]
    out += ["_Bear — terminal:_", *(top3(s.bear_points) or ["- —"])]
    uks = list(s.key_unknowns)[:3]
    if uks:
        out += ["_Key unknowns:_", *[f"- {u}" for u in uks]]
    out.append("")
    return out


def _brief_oneliner(desc: str) -> str:
    """First sentence of a CIQ business description ('{Co}, Inc. engages in …'), abbreviation-aware
    so the split doesn't stop at 'Inc.'/'Corp.'; capped for the teaser."""
    sent = ""
    for piece in re.split(r"(?<=\.)\s+", desc):
        sent = f"{sent} {piece}".strip() if sent else piece
        if not re.search(r"\b(Inc|Corp|Ltd|Co|LLC|LP|plc|Ltda|S\.A|N\.V)\.$", sent):
            break
    return sent if len(sent) <= 220 else sent[:220].rsplit(" ", 1)[0] + "…"


def _fmt_cap(v: float) -> str:
    return f"${v / 1000:.1f}B" if v >= 1000 else f"${round(v)}M"  # v in $M


def _fmt_shares(v: float) -> str:  # raw share count → "151.9M" / "1.2B"
    return f"{v / 1e9:.1f}B" if v >= 1e9 else f"{v / 1e6:.1f}M"


def _brief_snapshot(exchange: str | None, cik: str | None, si: StockInfo | None) -> list[str]:
    """(Brief snapshot) the scalar facts on ONE line — exchange · CMP · cap · 52-wk · shares · book
    value/sh · CIK — the linear-markdown mirror of the web dossier's snapshot table. Fail-honest:
    a value with no source is omitted (e.g. AORT has no CIQ Book Value/Share → no book/sh), never
    fabricated; one ↳ names the sources, the per-field source_ref lives in JSON."""
    p = SourceStatus.PRESENT
    parts: list[str] = []
    if exchange:
        parts.append(exchange)
    if si is not None:
        if si.price.status is p and si.price.value is not None:
            asof = f" ({si.as_of.isoformat()})" if si.as_of is not None else ""
            parts.append(f"CMP ${si.price.value:,.2f}{asof}")
        if si.market_cap.status is p and si.market_cap.value is not None:
            parts.append(f"cap {_fmt_cap(si.market_cap.value)}")
        if (si.low_52w.status is p and si.low_52w.value is not None
                and si.high_52w.status is p and si.high_52w.value is not None):
            parts.append(f"52-wk ${si.low_52w.value:,.2f}–${si.high_52w.value:,.2f}")
        if si.shares_out.status is p and si.shares_out.value is not None:
            parts.append(f"shares {_fmt_shares(si.shares_out.value)}")
        if si.book_value_ps.status is p and si.book_value_ps.value is not None:
            parts.append(f"book value/sh ${si.book_value_ps.value:,.2f}")
    if cik:
        parts.append(f"CIK {cik}")
    if not parts:
        return []
    return [f"- **Snapshot:** {' · '.join(parts)}"
            f"{_cite('exchange · EOD · EDGAR shares · CIQ book value + cap')}"]


def _customer_concentration(m: MechanicalLayer) -> str | None:
    """The top-customer % (a concentration RISK) from the 10-Q — NOT the raw customer names."""
    ps = m.primary_source
    fil = ps.filing if ps is not None else None
    conc = fil.concentration if fil is not None else None
    custs = [c for c in (conc.customers if conc is not None else []) if c.pct is not None]
    if not custs or fil is None:
        return None
    top = sorted(custs, key=lambda x: x.pct or 0.0, reverse=True)
    # a disclosed floor ('exceeded N%', value_kind='floor') keeps its ≥ qualifier — the source said
    # "more than N%", never an exact N% (source-fidelity: the human sees what the filing stated).
    t0 = "≥" if top[0].value_kind == "floor" else ""
    line = f"top customer {t0}{round(top[0].pct or 0.0)}%"
    if top[0].prior_pct is not None:
        line += f" (from {round(top[0].prior_pct)}%)"
    if len(top) > 1:
        # if either of the top-2 is a disclosed floor, their sum is itself a floor (≥)
        t2 = "≥" if any(x.value_kind == "floor" for x in top[:2]) else ""
        line += f" · top-2 ~{t2}{round(sum((x.pct or 0.0) for x in top[:2]))}%"
    return f"- **Customer concentration:** {line} of revenue{_cite(fil.source_ref)}"


def _brief_financials(m: MechanicalLayer) -> list[str]:
    """The Motilal-style financials snapshot — the key income-statement rows (un-truncated), as a
    table; the full statement stays in the Appendix."""
    fs = m.financial_summary
    if fs is None or fs.annual.status is not SourceStatus.PRESENT or fs.annual.value is None:
        return []
    tbl = fs.annual.value
    want = {"Revenue ($M)", "Revenue growth", "EBITDA ($M)", "EBITDA margin",
            "EBIT ($M)", "Net income ($M)", "EPS (GAAP, dil.)", "FCF ($M)"}
    rows = [[r.label, *r.cells] for r in tbl.rows if r.label in want]
    if not rows or not tbl.columns:
        return []
    # num_cols are 0-based indices into cols (the period columns) — _table prepends the label cell
    # itself. range(len) right-aligns EVERY period; range(1, len+1) left off column 0 and wasted
    # index len (the first period rendered left-aligned).
    num_cols = frozenset(range(len(tbl.columns)))
    return _table("Financial snapshot", fs.annual.source_ref, list(tbl.columns), rows,
                  num_cols=num_cols)


def _machine_read_md(eb: str) -> str:
    """The machine's evidence read as markdown: the lean word (before the em-dash) bold + Sentence-
    cased, then its rationale verbatim. Mirrors the web teaser's machineReadHtml minus the direction
    tint (markdown has no color). Parsed by THE shared lean parser (verdict.split_lean — the same
    one the proposal derives from). Fail-soft: an un-split read is verbatim."""
    parts = split_lean(eb)
    if parts is None:
        return eb
    lean, rest = parts
    return f"**{lean[:1].upper() + lean[1:]}** — {rest}"


def _machine_proposal_md(p: MachineProposal) -> str:
    """The machine's PROPOSED verdict (the 2026-07-13 pivot) — the deterministic derivation of the
    committed lean (verdict.derive_proposal; face-validity mapping, never outcome-tuned). Renders
    ABOVE the human slot; the human's confirm/override below is the verdict of record. A present
    proposal does NOT repeat the lean's rationale — the machine-read line sits directly above and
    already carries it (the #109 de-dup discipline); the row names its DERIVATION instead. No
    proposal renders its fail-honest note — never a coin-flip. AVOID_TERMINAL displays as AVOID
    (display only; the enum is the structured value in the ledger/JSON)."""
    if p.action is None:
        return f"**Machine proposal:** none — {p.note}"
    return f"**Machine proposal:** {p.action_word} — derived from the lean above"


def _brief_lines(d: Dossier, *, show_proposal: bool = False) -> list[str]:
    """(Brief) the market-standard first cut in 8 sections — teaser → setup → company → case →
    financial snapshot → valuation → catalyst → verify. Machine-assembled + source-bound. The
    machine's proposed verdict is DERIVED + sealed to the shadow ledger at assembly but NOT shown
    here before the human logs theirs (``show_proposal=False``, the default) — so it can't anchor
    the human or contaminate the human-vs-machine comparison. The human's confirm/override in the
    Recommendation slot is the verdict of record."""
    m = d.mechanical
    s = d.synthesis
    out: list[str] = ["# Brief — first cut", ""]
    # 1 — TEASER: business one-liner · machine read · the human's Recommendation/Target · snapshot —
    # the linear mirror of the web's 2/3 narrative + 1/3 snapshot. Identity + rank + framing live in
    # the doc header above, so the teaser no longer repeats the ticker/name/cap (that was a dup).
    bd = d.business_description
    if bd is not None and bd.status is SourceStatus.PRESENT and bd.value is not None:
        out.append(_brief_oneliner(bd.value))
    if s is not None and s.evidence_balance:
        out += ["", _machine_read_md(s.evidence_balance)]
    # THE PIVOT (2026-07-13) — REVISED same day (anti-anchoring): the machine's proposed verdict is
    # DERIVED (deterministic, face-validity-frozen over the committed lean; the LLM still emits no
    # verdict field) and SEALED to the shadow ledger at assembly — but it is NOT shown in the brief
    # before the human logs theirs, so it can't anchor the human OR contaminate the human-vs-machine
    # comparison (the same discipline as tiers-never-ranks). Revealed only AFTER the verdict is
    # logged (the ledger CLI prints it), or on an explicit ``--show-proposal`` peek. The machine
    # READ above (the evidence lean) is the assembled evidence summary, not the verdict — it
    # stays, mirroring the full bull/bear balance in the Analysis synthesis.
    if show_proposal:
        out += ["", _machine_proposal_md(
            derive_proposal(s.evidence_balance if s is not None else None))]
    else:
        out += ["", "**Machine proposal:** _sealed at assembly — revealed after your verdict is "
                "logged (or `--show-proposal`)_"]
    out += ["", "**Recommendation / Target (human):** _not yet logged — confirm or override "
            "(Buy / Avoid + target)_"]
    snap = _brief_snapshot(d.exchange, d.cik, m.stock_info)
    if snap:
        out += ["", *snap]
    # DECISION TILES (moved up from the old setup section, mirroring the web's teaser tiles): price
    # action (raw 180d drawdown) + idiosyncratic (vs market) + leverage + FCF (+ going-concern when
    # flagged). The "Valuation (vs peers)" line is NOT here — it renders once, in Valuation below.
    io = m.idiosyncratic_vs_shared
    tiles: list[str] = []
    if io is not None and io.name_180d_return.status is SourceStatus.PRESENT:
        tiles.append(_fact("Price action (180d)", io.name_180d_return, _pct))
    if io is not None:
        tiles.append(_fact("Idiosyncratic (vs market, 180d)", io.rel_vs_market, _pct))
    if m.quality is not None:
        tiles.append(_fact("Net debt / EBITDA", m.quality.net_debt_to_ebitda, _mult))
        tiles.append(_fact("Free cash flow", m.quality.fcf_sign, _signword))
    gc = _going_concern_brief(m)
    if gc is not None:
        tiles.append(gc)
    if tiles:
        out += ["", *tiles]
    out.append("")
    # 2 — DECISIVE QUESTION: the one framing question the human resolves. Drawdown / idiosyncratic /
    # leverage / FCF facts are teaser tiles now, so this section is just the question (title carries
    # the label — no inline "Decisive question:" prefix).
    if s is not None and s.decisive_question is not None and s.decisive_question.question:
        out += ["## Decisive question", f"**{s.decisive_question.question}**", ""]
    # 3 — COMPANY & BUSINESS: segments · geography · customer concentration (not names)
    out.append("## Company & business")
    if m.concentration is not None:
        out += [_fact("Segments", m.concentration.segments),
                _fact("Geography", m.concentration.geographic)]
    cc = _customer_concentration(m)
    if cc is not None:
        out.append(cc)
    out.append("")
    # 4 — THE CASE: condensed bull/bear + key unknowns. (PR-B) the operating drivers are NOT a
    # standalone block — a mechanically-extracted fact list can't render the directional CALL (that
    # is the human's verdict); they feed the synthesis instead, where the bull/bear grounds in them
    # and cites them (operating_drivers stays machine-complete in dossier.json for audit).
    out += ["## The case", *_brief_case_lines(s)]
    # 5 — FINANCIAL SNAPSHOT: un-truncated key financials + the ratios panel
    out.append("## Financial snapshot")
    out += _brief_financials(m)
    # (Phase-4) the per-period return-ratio YoY table REPLACES the latest-only "Key ratios"
    # fact (the web adds a line exhibit above — markdown has no chart, so the table carries
    # every ratio). Fail-honest: a name without the CIQ Ratios panel keeps the latest line.
    if m.return_ratios is not None and m.return_ratios.status is SourceStatus.PRESENT:
        out += _fin_table_lines("Return ratios — per fiscal period", m.return_ratios)
    elif m.key_ratios is not None:
        out.append(_fact("Key ratios (latest)", m.key_ratios))
    out.append("")
    # 6 — VALUATION: cross-sectional + own-history + the multiple ladder + the implied ladder
    out.append("## Valuation")
    if m.valuation is not None:
        out += [_fact("Valuation (vs peers)", m.valuation.cross_sectional),
                _fact("Own-history range", m.valuation.range_position)]
    if m.peer_comps is not None:
        out.append(_fact("Comparability", m.peer_comps.comparability))
    if m.catalyst_path is not None:
        out += _ladder_lines(m.catalyst_path.cross_name_anchor)
    if m.implied_valuation is not None:
        out += _implied_lines(m.implied_valuation)
    out.append("")
    # 7 — CATALYST & CONSENSUS: the street's forward view (context, never a machine driver/target)
    cp = m.catalyst_path
    if cp is not None:
        out += ["## Catalyst & consensus",
                _fact("Consensus (target · ratings)", cp.consensus_stats)]
        if cp.insider_activity is not None:
            out.append(_fact("Insider activity (6m)", cp.insider_activity))
        if cp.short_interest is not None:
            out.append(_fact("Short interest", cp.short_interest))
        out.append("")
    # 8 — VERIFY FIRST: the decision-threatening caveats
    vf = _brief_verify_first(d.caveats)
    if vf:
        out += ["## Verify first", "; ".join(vf), ""]
    return out


def _mc_pct(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.1f}%"


def _mc_pctile(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.0f}th pct"


def _midcycle_section(mc: Any) -> list[str]:
    """(mid-cycle) 'Mid-cycle & scenarios'. Empty when the record is absent (byte-identity for
    pre-midcycle dossiers). Anchors always; the grid, ratio + sensitivity only when scenarios were
    supplied. Assemble-not-conclude: assumptions are the analyst's, the machine shows arithmetic +
    placement + the ratio per the ratified convention."""
    if mc is None:
        return []
    out: list[str] = ["### Mid-cycle & scenarios",
                      f"_A trailing multiple on trough earnings misleads; these anchor on the "
                      f"cycle. Reward/risk convention: {mc.convention}_", ""]
    # ANCHOR A — own margin history
    years = sorted(mc.margin_by_year, key=int)
    series = "  ".join(f"{y}:{mc.margin_by_year[y] * 100:.1f}%" for y in years)
    out += [
        f"- **Own operating-margin history** ({mc.margin_coverage}; revenue `{mc.revenue_tag}` / "
        f"operating income `{mc.opinc_tag}`, EDGAR XBRL): {series}",
        f"  - median **{_mc_pct(mc.margin_median)}** · Q1 {_mc_pct(mc.margin_q1)} / Q3 "
        f"{_mc_pct(mc.margin_q3)} · trough {_mc_pct(mc.margin_trough)} · "
        f"peak {_mc_pct(mc.margin_peak)}",
    ]
    if mc.fuel_disclosed:
        out.append(f"  - fuel-surcharge split (BOTH ways): incl median "
                   f"{_mc_pct(mc.fuel_incl_median)} · ex median {_mc_pct(mc.fuel_excl_median)}")
    else:
        out.append(f"  - fuel-surcharge: {mc.fuel_note}")
    # ANCHOR B — peer band
    if mc.peer_medians:
        peers = " · ".join(f"{t} {_mc_pct(v)}" for t, v in mc.peer_medians.items())
        out.append(f"- **Peer band** (each peer's own long-history median): {peers} → band median "
                   f"**{_mc_pct(mc.peer_band_median)}**")
    for t, why in mc.peer_excluded.items():
        out.append(f"  - {t}: {why}")
    # ANCHOR D — own EV/EBITDA band
    if mc.multiple_available:
        out.append(f"- **Own EV/EBITDA band** ({mc.multiple_note}): trough "
                   f"{mc.multiple_trough:.1f}x · median {mc.multiple_median:.1f}x · "
                   f"upper-quartile {mc.multiple_upper_quartile:.1f}x")
    else:
        out.append(f"- **Own EV/EBITDA band**: {mc.multiple_note}")
    # SCENARIO GRID + ratio (only when supplied)
    if mc.scenarios:
        hdr = ("| scenario | rev $M | margin | ×mult | op-inc $M | value/sh | "
               "margin own/peer pct | source |")
        out += ["", f"**Scenario grid** (analyst-supplied; machine computes value + placement; "
                f"$M rev/net-debt; spot ${mc.spot:.2f}, net debt ${mc.net_debt_musd:.0f}M):",
                "", hdr, "|---|---:|---:|---:|---:|---:|---|---|"]
        for s in mc.scenarios:
            out.append(
                f"| {s.name} | {s.revenue_musd:.0f} | {_mc_pct(s.margin)} | {s.multiple:.1f}x | "
                f"{s.op_income_musd:.0f} | ${s.value_per_share:.2f} | "
                f"{_mc_pctile(s.margin_pct_of_own)} / {_mc_pctile(s.margin_pct_of_peer)} "
                f"| {s.source}"
                f"{(' — ' + s.reason) if s.reason else ''} |")
        out.append("")
        if mc.ratio_undefined:
            out.append(f"- **Reward/risk: {mc.ratio_undefined}** "
                       f"(reward = base−spot ${mc.reward:.2f}; risk leg degenerate)")
        elif mc.ratio is not None:
            verdict = "CLEARS" if mc.clears_bar else "BELOW"
            out.append(f"- **Reward/risk = {mc.ratio:.2f}:1** — **{verdict}** the "
                       f"≥{mc.bar:.0f}:1 bar (reward base−spot ${mc.reward:.2f}; risk "
                       f"spot−bear ${mc.risk:.2f}; bull not in the ratio — convention).")
        if mc.sensitivity:
            cells = "; ".join(
                f"m{r['d_margin'] * 100:+.0f}pt/×{r['d_multiple']:+.0f}="
                + ("undef" if r["ratio"] is None else f"{r['ratio']:.2f}") for r in mc.sensitivity)
            out.append(f"  - sensitivity (base margin ±1pt / multiple ±1 turn): {cells}")
    out.append("")
    return out


@_endnote_scope
def render_markdown(d: Dossier, *, dev: bool = False, show_proposal: bool = False) -> str:
    """(D1) Facts-first restructure. Section order: header → caveats → mechanical layer [drawdown &
    idiosyncrasy (clubbed) → leverage & survival → trajectory → valuation → peer comps → catalyst →
    concentration] → synthesis → appendix (+ management-commentary pointer) → verdict footer. Old
    committed JSONs still render (every field is optional-safe). ``dev`` shows the D3 tier tags.
    ``show_proposal`` reveals the sealed machine proposal in the brief (default False — the brief
    hides it so it can't anchor the human before they log their verdict).
    The fresh per-document endnote table + its reset are handled by ``@_endnote_scope``."""
    m = d.mechanical
    out: list[str] = [
        f"# Dossier — {d.name} ({d.ticker})",
        "",
        f"_Assembled facts · machine proposal sealed (revealed after the human's verdict) · "
        f"verdict of record: the human's · data as of {d.reference_date} · assembled "
        f"{_fmt_assembled(d.assembled_at)} · {d.llm_model or 'mechanical layer only'}_",
        "",
    ]
    # (3-tier) BRIEF — first cut: the machine READ + decisive question + decision data + condensed
    # case + valuation snapshot. The derived proposal is SEALED at assembly but hidden here
    # (anti-anchoring) unless ``show_proposal``; the human's logged confirm/override — a ledger
    # concern — is the verdict of record, and the reveal happens after it is logged.
    out += _brief_lines(d, show_proposal=show_proposal)
    # (3-tier) ANALYSIS — the full dossier: caveats → mechanical layer → FULL synthesis.
    out += ["# Analysis — full dossier", ""]
    # (D1) CAVEATS — what to verify before trusting the evidence below.
    out += _flags_section(d)
    out += ["## Mechanical layer", ""]  # (K5) methodology jargon lives in source_refs/JSON

    # (D1·§1) Drawdown cause & idiosyncrasy — CLUBBED: what happened, and did it happen alone?
    out.append("### Drawdown cause & idiosyncrasy — what happened, and did it happen alone?")
    out += [
        _fact("Shape", m.drawdown_cause.shape),
        _fact("Gap-down dates", m.drawdown_cause.gap_down_dates, _dates),
    ]
    if m.drawdown_cause.filings:
        out.append("- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**")
        for f in m.drawdown_cause.filings:
            out.append(f"  - gap {f.gap_date} → {f.filing_date} [`{f.accession}`]({f.url})")
            out.append(f"    - items: {', '.join(f.item_types) or '—'}")
            # (B1) parsed release drivers ARE the informative cause — they supersede the item-code
            # boilerplate; non-earnings 8-Ks (no match) still show their source-bound events.
            if f.drivers is not None and f.drivers.status is SourceStatus.PRESENT:
                out.append(f"    - **what the results showed:** {f.drivers.value}"
                           f"{_cite(f.drivers.source_ref)}")
            else:
                for ev in f.events:
                    out.append(f"    - {ev}")
    out.append(_fact("Revised guidance", m.drawdown_cause.revised_guidance))
    out += _event_impact_lines(m)  # (RC-1 C) Avis-class event-impact quantifications
    out += [
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
    # (RC-1 C) primary-source cross-checks — filings vs CIQ panel (self-funding lives in leverage
    # above; wall / triangulation / guide / going-concern / concentration here).
    out += _primary_source_block(m)

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

    # (mid-cycle) the cyclical-underwriting section — UNDER the valuation block. Rendered only when
    # the record is present (absent → nothing, so pre-midcycle dossiers are byte-identical).
    out += _midcycle_section(d.midcycle)

    # (D1·§5) Peer comps — roster + comparability + multiples + grid + implied valuation.
    out.append("### Peer comps")  # (K5) discipline framing lives in the block body + source_refs
    out += _roster_lines(m.peer_comps.peer_set)
    out.append(_fact("Comparability (confidence gate)", m.peer_comps.comparability))
    out += _multiples_lines(m.peer_comps.trading_multiples)
    out += _peer_grid_or_deltas(m.peer_comps)
    out.append("")
    # (K4) implied valuation is DEMOTED to the appendix (reference-only) — not in the main body.

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

    # (3-tier) APPENDIX — data & audit: financial summary → capital-structure provenance →
    # implied-valuation reference → management-commentary pointer, then the verdict footer.
    out += ["# Appendix — data & audit", ""]
    appendix = _appendix_lines(m)
    out += appendix if appendix else ["## Financial summary", ""]
    if m.capital_structure is not None:
        out += _capital_structure_appendix_lines(m.capital_structure)  # (K1) provenance
    if m.implied_valuation is not None:
        out += _implied_lines(m.implied_valuation)  # (K4) reference-only, demoted here
    out += _mgmt_commentary_lines(m)
    out += [
        "---",
        "> **The machine PROPOSES; the human DECIDES.** The proposed verdict is sealed at assembly "
        "and revealed only after the human logs theirs — the verdict of record is the human's, "
        "with a frozen entry price in the ledger.",
    ]
    out += _sources_section()  # (A2) the single document-end Sources list — every [n] resolves here
    return "\n".join(_dedupe_unknown_reasons(out))  # (H3) fold repeated UNKNOWN reasons
