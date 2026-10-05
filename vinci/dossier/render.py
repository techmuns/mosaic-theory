"""Render a :class:`Dossier` to human-readable markdown — source_refs shown INSPECTABLE.

The point of the rendering is that the human verifies the primary datum (the cited filing cell / bar
window / CIQ sheet), not the summary. So every fact prints its ``source_ref``; every UNKNOWN/MISSING
prints why; bull/bear points print their citation and an ⚠ when a guardrail flagged them.
"""

from __future__ import annotations

import contextvars
import functools
import json
import math
import re
from collections import Counter
from collections.abc import Callable
from datetime import UTC, date, datetime
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING, Any, ParamSpec

from vinci.config import get_config
from vinci.dossier.anchor import Anchor
from vinci.dossier.covenant_extract import GoverningTerm, _derive_conversion, governing_terms
from vinci.dossier.extraction_version import stamp_detail, stamp_label
from vinci.dossier.freshness import RECONCILE_TOLERANCE, reconcile_cap
from vinci.dossier.schemas import (
    Dossier,
    FinancialSummary,
    ForwardMultiple,
    MechanicalLayer,
    PriceStoreStamp,
    Sourced,
    SourceStatus,
    StockInfo,
    Synthesis,
)
from vinci.dossier.verdict import MachineProposal, derive_proposal, split_lean
from vinci.sleeves import BY_KEY, DEFAULT_SLEEVE, require_sleeve

if TYPE_CHECKING:  # typing only — a RUNTIME import would cycle (scenarios → dossier.midcycle)
    from vinci.scenarios import ScenarioRecord

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



# --- (declutter P3) display transforms — reader-register curation of machine-composed strings.
# Display-ONLY: every transform leaves dossier.json untouched; each is mirrored in dossier.js.
_F4_CODES = re.compile(r"other ((?:[A-Z]×\d+/?)+)$")


def _fmt_insider(v: Any) -> str:
    """'other F×46/G×6/J×34/M×56' → 'other filings 142' — raw Form-4 transaction codes are machine
    dialect; the per-code split stays in dossier.json."""
    text = str(v)
    m = _F4_CODES.search(text)
    if not m:
        return text
    total = sum(int(n) for n in re.findall(r"×(\d+)", m.group(1)))
    return text[: m.start()] + f"other filings {total}"


#: How far the multiple series' own implied EBITDA margin may sit from the margin the company
#: REPORTS before the difference is stated beside the multiple. Measured 2026-09-30 across the 22
#: committed dossiers carrying both figures: 19 sit at or below 1.33x (most of that is rounding —
#: the reported margin is a whole percent), CNXC 1.33x and ROST 1.31x are the honest top, BURL is
#: 1.75x and VITL 5.01x. VITL already FAILS the coherence guard and never reaches here.
#:
#: BURL IS NOT CORRUPT DATA, WHICH IS WHY THIS DISCLOSES RATHER THAN DISQUALIFIES. Its implied
#: margin is 19.3% against 11.0% reported — a gap of $991M on $12.2B of revenue, which is the
#: order of its annual rent. The series is struck on something like EBITDAR: coherent, internally
#: consistent, and NOT the reported EBITDA the label "EV/EBITDA (TEV/LTM)" implies. Tightening the
#: coherence bound instead would have thrown the anchor away (VITL's treatment) over data that is
#: not broken. A reader told "9.0x, 8th percentile, near-floor" cannot otherwise know that 9.0x and
#: the company's reported EBITDA are not the same arithmetic — on BURL the same TEV over reported
#: EBITDA is nearer 15.6x, which is not a floor at all.
_MARGIN_BASIS_GAP = 0.25


def _reported_ltm_ebitda_margin(m: MechanicalLayer) -> float | None:
    """The EBITDA margin the company REPORTS, from the annual summary's LTM column.

    STRUCTURED VALUES, NEVER THE RENDERED CELL. The first cut read the display string `"11%"` and
    divided by 100. That is the parsers rule inverted — and it was not free: the `EBITDA margin`
    row is rendered to a WHOLE percent, so BURL's 11.146% arrived as 11.0% and the restated
    multiple published as 15.8x where the underwrite had derived 15.6x by hand. The `EBITDA ($M)`
    and `Revenue ($M)` rows both carry `values`, so the margin is computed from them; the display
    row is never consulted.
    """
    fs = getattr(m, "financial_summary", None)
    ann = getattr(fs, "annual", None) if fs is not None else None
    tbl = ann.value if ann is not None and ann.status is SourceStatus.PRESENT else None
    if tbl is None or "LTM" not in (tbl.columns or []):
        return None
    i = tbl.columns.index("LTM")

    def _at(label: str) -> float | None:
        for row in tbl.rows or []:
            if str(row.label).strip() != label:
                continue
            vals = row.values or []
            return vals[i] if i < len(vals) else None
        return None

    ebitda, revenue = _at("EBITDA ($M)"), _at("Revenue ($M)")
    if ebitda is None or revenue is None or revenue <= 0:
        return None
    return float(ebitda) / float(revenue)


def _multiple_basis_md(m: MechanicalLayer) -> str:
    """State the EV/EBITDA series' OWN denominator when it is not the reported one.

    Empty when the two agree, when either is missing, or when no band carries an implied margin —
    so the line appears only where it changes how the multiple should be read."""
    val = getattr(m, "valuation", None)
    oh = getattr(val, "own_history", None) if val is not None else None
    bands = oh.value if oh is not None and oh.status is SourceStatus.PRESENT else None
    if not bands:
        return ""
    band = next((b for b in bands if b.implied_ebitda_margin and "EBITDA" in str(b.metric)), None)
    reported = _reported_ltm_ebitda_margin(m)
    if band is None or not reported or reported <= 0:
        return ""
    implied = float(band.implied_ebitda_margin or 0)
    if not implied or abs(implied - reported) / reported <= _MARGIN_BASIS_GAP:
        return ""
    restated = band.current * (implied / reported) if band.current else None
    tail = (f"; the same TEV over REPORTED EBITDA is nearer {restated:,.1f}x"
            if restated else "")
    return (f"- **Multiple basis — read before the level:** the {band.metric} series implies a "
            f"{implied * 100:,.1f}% EBITDA margin, against {reported * 100:,.1f}% reported. Its "
            f"denominator is NOT the reported EBITDA{tail}. The level and percentile above are "
            f"internally consistent on the series' own basis; they are not comparable to a "
            f"multiple struck on reported EBITDA.")


def _forward_multiples_md(s: Sourced[list[ForwardMultiple]] | None) -> str:
    """The forward multiples as ONE line, each naming its column. Empty string when unbuilt, so a
    dossier assembled before the field renders exactly as it did."""
    if s is None:
        return ""
    if s.status is not SourceStatus.PRESENT or not s.value:
        return f"- **Forward multiples:** _{s.status.value.upper()}_ — {_clean_note(str(s.note))}"
    parts = "; ".join(f"{fm.label} {fm.multiple:,.1f}x (EPS ${fm.eps:,.2f})" for fm in s.value)
    px = s.value[0]
    asof = f" as-of {px.price_as_of}" if px.price_as_of else ""
    return (f"- **Forward multiples:** {parts} — at ${px.price:,.2f}{asof}"
            f"{_cite(s.source_ref)}")


def _fmt_customers(v: Any) -> str:
    """A raw relationship dump ('A (KOSE:X) — the name · Client Services · src: …; B …') → a count.
    The Brief already treats raw customer names as noise; the roster stays in dossier.json."""
    text = str(v)
    if "src:" not in text:
        return text
    n = len([seg for seg in text.split(";") if seg.strip()])
    return (f"{n} mapped client relationship(s) — roster in JSON; concentration %, when disclosed, "
            "is the 10-Q read above")


def _fmt_shape(v: Any) -> str:
    """Strip bare 8-K item codes ('earnings (2.02) + Reg-FD (7.01)') — the filing block below names
    the item types in words."""
    return re.sub(r"\s*\((\d\.\d{2})\)", "", str(v))


def _gap_list(shape: str) -> list[tuple[str, str]] | None:
    """(event study) Parse the committed shape 'discrete gap-downs — DATE cause; DATE cause' into
    per-gap (date, cause) rows for a scannable list. None (→ fall through to the run-on) for the
    gradual-bleed read or any shape not in the discrete-gap format. Cosmetic re-layout of the SAME
    committed labels — no logic reads the result; twin of dossier.js ``gapList``."""
    m = re.match(r"discrete gap-downs — (.+)", shape.strip())
    if m is None:
        return None
    rows: list[tuple[str, str]] = []
    for part in m.group(1).split("; "):
        dm = re.match(r"(\d{4}-\d{2}-\d{2})\s+(.+)", part.strip())
        if dm is None:
            return None  # an unexpected part shape → fail through, never a mangled list
        rows.append((dm.group(1), dm.group(2).strip()))
    return rows or None


def _gap_pct_from_perf(sp: Any, date_str: str) -> float | None:
    """The exact 1-day close-to-close move at ``date_str``, derived from consecutive DAILY perf
    points — the detector's own formula on the same closes (a rebased-index ratio IS the close
    ratio). None when the series doesn't carry the date or the previous point isn't the prior
    trading day (old weekly-downsampled JSON): REFUSE rather than misstate a multi-day move as
    the 1-day gap. Twin of dossier.js ``gapPctFromPerf``."""
    pts = getattr(sp, "points", None) or []
    idx = next((i for i, p in enumerate(pts) if p.date == date_str), None)
    if idx is None or idx == 0:
        return None
    a, b = pts[idx - 1], pts[idx]
    if a.name is None or b.name is None or a.name <= 0:
        return None
    spacing = (date.fromisoformat(b.date) - date.fromisoformat(a.date)).days
    # b must be the IMMEDIATELY-next trading day: 1 calendar day (adjacent weekday) or a Fri→Mon
    # weekend (3 days, prior point a Friday). Any other spacing — 2 (a weekday was skipped ⇒ a
    # downsampled step≥2 series), 4 (a day skipped / post-holiday), 7 (weekly) — can't be proven
    # consecutive, so REFUSE rather than misstate a multi-trading-day move as the 1-day gap.
    if not (spacing == 1 or (spacing == 3 and date.fromisoformat(a.date).isoweekday() == 5)):
        return None
    return float(b.name) / float(a.name) - 1.0


_LEGALESE_PAREN = re.compile(r"\s*\(\s*(?:the\s+)?[\u201c\"][^)]{1,70}[\u201d\"]\s*\)")
_XREF_STUB = re.compile(r"The information set forth in", re.IGNORECASE)
# (#2) items whose parsed body is a SUBSTANTIVE catalyst — it belongs on the visible card beside
# the 2.02 metrics: a material agreement, an offering, a restructuring/impairment, a mgmt change,
# a delisting/restatement. NOT 7.01 (Reg-FD "will host a webcast") / 9.01 (exhibits): those stay
# collapsed. Twin of dossier.js ``_SUBSTANTIVE``.
_SUBSTANTIVE_ITEM = re.compile(r"^(1\.01|1\.02|2\.05|2\.06|3\.01|4\.02|5\.02|8\.01)\b")


def _substantive_events(f: Any) -> list[str]:
    """Cleaned narratives of a filing's substantive non-2.02 items (the ones that belong on the
    visible card). Empty when the filing carries only earnings/Reg-FD/exhibits."""
    out: list[str] = []
    for ev in f.events:
        if _SUBSTANTIVE_ITEM.match(str(ev)):
            cleaned = _clean_item_event(ev)
            if cleaned is not None:
                out.append(cleaned)
    return out


def _clean_item_event(ev: str) -> str | None:
    """One parsed 8-K item line ("CODE Title: body") → the body with the DOUBLED leading title and
    the defined-term legalese parentheticals stripped, truncated at a cross-reference stub. None
    when nothing informative remains. Display trim of a parse-summary (never a verbatim quote —
    those live untouched in JSON); twin of dossier.js ``cleanItemEvent``."""
    m = re.match(r"^(\d\.\d\d)\s+([^:]{1,90}):\s*(.*)$", ev, re.DOTALL)
    if m is None:
        return ev
    code, title, body = m.group(1), m.group(2), m.group(3).strip()
    title = re.sub(r"^Item\s+\d\.\d\d:?\s*", "", title, flags=re.IGNORECASE).strip()
    # cross-reference stub truncation FIRST — otherwise the title-recovery fallback below reads the
    # stub text itself as a "title" and mangles instead of dropping (caught by the twin test)
    stub = _XREF_STUB.search(body)
    if stub:
        body = body[: stub.start()].strip()
    if not title:
        t2 = re.match(r"^([^.:]{2,80})[.:]\s*", body)
        if t2:
            title = t2.group(1).strip()
    if title:
        body = re.sub(
            rf"^(?:Item\s+\d\.\d\d[.:]?\s*)?{re.escape(title)}\s*[.:]\s*", "", body,
            flags=re.IGNORECASE,
        )
    body = _LEGALESE_PAREN.sub("", body)
    body = body.strip()
    if not body:
        return None  # pure cross-reference / heading-only item — nothing informative
    return f"{code} {title}: {body}" if title else f"{code}: {body}"


def _fmt_guide_verification(v: Any) -> str:
    """'guide verification (revenue): CIQ 6405.0–6405.0 vs release QUALITATIVE → plausibility flag;
    render the qualitative growth line' → the label duplicate, the degenerate range, and the
    trailing render-instruction are machine dialect."""
    text = str(v)
    text = re.sub(r"^guide verification \(([^)]+)\):\s*", r"\1: ", text)
    text = re.sub(r"\b(\d[\d,.]*)–\1\b", r"\1", text)
    return re.sub(r";\s*render the [^;]+$", "", text).strip()


def _clean_note(note: str) -> str:
    """Reader-register cleanup of machine-composed UNKNOWN/MISSING reasons (display-only)."""
    out = note
    out = re.sub(r"\s*for 8-Ks \['([^']+)'\]", r" for the filed 8-K \1", out)
    out = out.replace("Credit Health Panel: scale direction ambiguous — not rendered",
                      "credit-health panel scale is ambiguous in the export")
    return out

def _fact(label: str, s: Sourced[Any], fmt: Callable[[Any], str] = str) -> str:
    if s.status is SourceStatus.PRESENT:
        return f"- **{label}:** {fmt(s.value)}{_cite(s.source_ref)}"
    return f"- **{label}:** _{s.status.value.upper()}_ — {_clean_note(str(s.note))}"


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
     "no revised-outlook block parsed from the 99.1 — the revised forward guidance is UNKNOWN"),
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


# (declutter P2) the HEADLINE horizon metrics — the ones the synthesis actually argues from.
# Interest expense / EBT / the GAAP-vs-excl-excep net-income splits made an 18-row wall; they stay
# machine-complete in dossier.json, counted here.
_HORIZON_KEEP = re.compile(r"^(Revenue|EBITDA|EBIT|EPS)\b", re.IGNORECASE)


def _horizon_lines(s: Sourced[Any]) -> list[str]:
    """(4a · declutter P2) Horizon read: HEADLINE metrics with non-zero breadth first; zero-breadth
    rows collapse to one line; non-headline metrics are counted, not printed. The full grid stays
    in dossier.json."""
    label = "Horizon read (FQ — next-2Q revision breadth)"
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    nonzero: list[str] = []
    zero: list[str] = []
    skipped = 0
    for seg in (seg.strip() for seg in _body(str(s.value)).split("; ")):
        if not seg:
            continue
        if not _HORIZON_KEEP.match(seg):
            skipped += 1
            continue
        (nonzero if re.search(r"[1-9]\d*[↑↓]", seg) else zero).append(seg)
    out = [f"- **{label}** — {_cite_inline(s.source_ref)}:"]
    out += [f"  - {seg}" for seg in nonzero]
    if zero:
        labels = ", ".join(seg.split(":", 1)[0] for seg in zero)
        out.append(f"  - _no revisions in any window: {labels}_")
    if skipped:
        out.append(f"  - _+{skipped} non-headline metric rows in JSON_")
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


def _guide_period_year(period: str) -> int | None:
    """The fiscal year a guide COVERS, from its own period label (`FQ4 2002`, `FY 2027`)."""
    m = re.search(r"(20\d\d|19\d\d)", str(period or ""))
    return int(m.group(1)) if m else None


def _catalyst_asof_year(cp: Any) -> int | None:
    """The year the catalyst panel's data reaches. `as_of` is a FLOOR (`≥2026-07-21`), which is
    exactly right here: a guide period must be strictly BEHIND the data we hold before it can be
    called superseded, and a floor errs toward leaving guidance alone."""
    a = getattr(cp, "as_of", None)
    raw = getattr(a, "value", a)
    m = re.search(r"(20\d\d)-\d\d-\d\d", str(raw or ""))
    return int(m.group(1)) if m else None


def _guidance_bridge_lines(cp: Any) -> list[str]:
    """(H4) Guidance bridge as a table — metric | latest guide | for | dated | age | record | most
    recent — each a RECORDED delivery fact, no reading added. A pre-H4 dossier.json (no rows) falls
    back to the flat one-line string.

    A GUIDE WHOSE PERIOD HAS PASSED DOES NOT LEAD WITH ITS FIGURE. NFLX's table opened with
    `Gross Margin % — '47.00 - 48.00' for FQ4 2002`: a twenty-four-year-old number in a column
    headed "Latest guide", with the Age column two places right saying 8686d. The eye takes the
    figure. The row builder picks the newest guide with a PARSEABLE RANGE, so a company that
    stopped guiding a metric keeps surfacing whatever it last said.

    THE TEST IS THE GUIDE'S PERIOD, NOT ITS ISSUE AGE (review finding, #423). Age was the first
    criterion and it is wrong in BOTH directions, with a counterexample each way in the corpus:
    VITL's gross-margin guide is dated 2023-11-02 (977d) but is **for FY 2027**, still ahead of a
    2026 as-of — long-term guidance stays applicable without being reissued, and calling it
    "none current" is simply false. MVST's is only 238d old but is **for FY 2025**, a year already
    finished and never reguided — genuinely no current guide. Issue date says nothing about
    applicability; the guided period says everything.

    UNPARSEABLE ERRS TOWARD LEAVING IT ALONE. A period or as-of this cannot read leaves the row
    untouched: a false demotion actively misleads, while a missed one leaves the Age column still
    telling the truth.

    NOTHING IS DELETED — the figure stays in the cell, reframed as `none current (last: …)`, and
    `dossier.json` is untouched: the three-tier rule as written. The demoted rows also sort BELOW
    the current ones, because sheet order put NFLX's two dead guides at the top of its table.
    """
    rows_s = getattr(cp, "guidance_bridge_rows", None)
    if rows_s is None or rows_s.status is not SourceStatus.PRESENT or not rows_s.value:
        return [_fact("Guidance bridge (latest guide + track-record)", cp.guidance_bridge)]
    cols = ["Latest guide", "For", "Dated", "Age", "Record (met/resolved)", "Most recent"]
    asof_yr = _catalyst_asof_year(cp)

    def _superseded(r: Any) -> bool:
        yr = _guide_period_year(r.period)
        return yr is not None and asof_yr is not None and yr < asof_yr

    def _row(r: Any) -> list[Any]:
        guide = (f"none current (last: {r.latest_guide})" if _superseded(r) else r.latest_guide)
        return [r.metric, guide, r.period, r.dated, r.age, r.record, r.most_recent]

    ordered = ([r for r in rows_s.value if not _superseded(r)]
               + [r for r in rows_s.value if _superseded(r)])
    # (PR-A) WHOSE NUMBER IT IS, said once beneath the table rather than per row. The column reads
    # "Latest guide" and the citation names CIQ, which together read as the company's own words —
    # but CIQ states every guide as a LEVEL, so a rate-guider's figure here is CIQ's arithmetic.
    # Visa is the proven case: "low end of low-teens" revenue growth arrives as 45,200.0, exactly
    # FY25's 40,000 x 1.13. Once, not per row, because the sheet does not record which form
    # management used and 32 of 49 committed guides are ranges that plausibly ARE the company's.
    return _table("Guidance bridge (latest guide + sign-aware delivery track-record)",
                  rows_s.source_ref, cols, [_row(r) for r in ordered],
                  note="CIQ states every guide as a LEVEL in the metric's own units. Where "
                       "management guided a RATE, the level is CIQ's arithmetic on its own base, "
                       "not a figure the company published — check the release before quoting one "
                       "as guidance.")


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


def _delta_txt(e: Any) -> str:
    """Signed magnitude of a revision — twin of `delta` in dossier.js. An em dash when either side
    does not parse as a number: a rating move ("Hold (3.00)") or an initiation with no prior has no
    delta, and inventing one would be worse than leaving it absent."""
    def _n(v: Any) -> float | None:
        t = str(v or "").strip().replace(",", "")
        try:
            return float(t)
        except ValueError:
            return None
    a, b = _n(e.broker_prior), _n(e.broker_current)
    if a is None or b is None:
        return "—"
    d = b - a
    if d == 0:
        return "0"
    sign = "+" if d > 0 else "−"
    return f"{sign}{abs(d):.2f}" if abs(d) < 1 else f"{sign}{abs(d):.1f}"


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
    # ORDER IS A TWIN CONTRACT (2026-07-29). This sorted by DATE ONLY, so ties kept insertion
    # order, while dossier.js reverse-sorted the composite "date|broker" string and so broke ties by
    # broker DESCENDING. With `_GROUP_CAP` truncating to six, the two surfaces published DIFFERENT
    # broker-days for the same name — AORT's md and web disagreed on rows 5 and 6, and neither was
    # wrong, they just never had to agree. Both now sort date DESC then broker ASC: deterministic,
    # and identical on either side.
    keys = sorted(sorted(groups, key=lambda k: k[1]), key=lambda k: k[0], reverse=True)

    # TABULAR (2026-07-29). Each broker-day is the same record — date, broker, up/down counts, the
    # largest-|Δ| headline, the remainder — and run together with middots it read as prose, hiding
    # the one thing a reader wants: how hard each broker cut. As columns the ↓ counts stack and that
    # becomes a glance. Routed through the shared `_table` (B4) like every other table, so the first
    # column is unlabelled and carries the date. Twin of `eventGroups` in dossier.js.
    # ONE definition of "withheld", mirroring `fullyGated` in dossier.js. VERIFIED against the
    # licensed workbooks (2026-07-29): CIQ writes "-" in Change Type on exactly the rows it
    # withholds — 349 of 349 such rows are fully entitlement-gated, and 0 of 2,513 rows carrying a
    # real change type are. So a broker-day with no direction is a WITHHELD one, not an empty one,
    # and Events = ↑ + ↓ + Init + Withheld closes. Counting only ↑/↓ printed "0↑/0↓" for a
    # fully-withheld day, which read as "nothing happened" when 27 revisions had landed.
    # WITHHELD = the events CIQ gave no direction for. Derived as the residual rather than by
    # re-testing the four value fields, which would duplicate dossier.js's field list across the
    # twins (the duplicate-set guard catches exactly that) — and the residual is also the stronger
    # definition, because Events = ↑ + ↓ + Init + Withheld then closes BY CONSTRUCTION.
    rows: list[list[str]] = []
    any_inits = any_held = False
    em = "—"   # render.py uses the literal em dash for an honest absence (no DASH constant)
    for dt, broker in keys[:_GROUP_CAP]:
        evs = groups[(dt, broker)]
        ct = Counter(e.change_type for e in evs)
        ups = sum(n for t, n in ct.items() if "upward" in t.lower())
        downs = sum(n for t, n in ct.items() if "downward" in t.lower())
        inits = sum(n for t, n in ct.items() if "initiation" in t.lower())
        held = len(evs) - ups - downs - inits
        any_inits = any_inits or inits > 0
        any_held = any_held or held > 0
        head = _revision_headline(evs)
        rows.append([
            dt, broker, str(len(evs)),
            str(ups) if ups else em, str(downs) if downs else em,
            str(inits) if inits else em, str(held) if held else em,
            f"{head.metric} {head.period}" if head else em,
            _n1(head.broker_prior) if head else em,
            _n1(head.broker_current) if head else em,
            _delta_txt(head) if head else em,
        ])
    # Init / Withheld columns only where they carry a value — a column of dashes is noise
    if not any_held:
        rows = [r[:6] + r[7:] for r in rows]
    if not any_inits:
        rows = [r[:5] + r[6:] for r in rows]
    cols = (["Broker", "Revisions", "↑", "↓"] + (["Init"] if any_inits else [])
            + (["Withheld"] if any_held else [])
            + ["Largest revision", "Prior", "Current", "Δ"])
    num = frozenset(i for i, c in enumerate(cols)
                    if c in {"Revisions", "↑", "↓", "Init", "Withheld", "Prior", "Current", "Δ"})
    note = (f"+{len(keys) - _GROUP_CAP} more broker-days in JSON"
            if len(keys) > _GROUP_CAP else "")
    return _table(f"{label} ({len(events)} events · {len(keys)} broker-days)",
                  s.source_ref, cols, rows, note=note, num_cols=num)


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
        hdr = "## The street — estimates & guidance"
        out.append(hdr)
        out.append(f"_{_asof_header(cp.as_of)}_")
        out += _horizon_lines(cp.horizon_read)
        out.append(_fact("Acceleration read (monthly consensus path)", cp.acceleration_read))
        out += _ladder_lines(cp.cross_name_anchor)
        # (buy-side restructure, twins the web) revised guidance is a guidance fact — it lives
        # beside the guidance bridge, not on the what-broke section
        # (item 1 clause (c)) THE SPLIT, rendered. Two different questions that used to be ONE
        # field: "what did management say in the filing that caused the gap" (drawdown-vintage by
        # construction) versus "what guide governs today". They coincide until guidance is revised
        # after the drawdown — SMPL's bear argued April's from the first while the base used July's
        # from the second, both unlabelled, on one page. Each now names its own filing.
        out.append(_fact("Guidance at the drawdown (8-K 99.1)",
                         m.drawdown_cause.revised_guidance))
        ps_cg = getattr(getattr(m, "primary_source", None), "current_guide", None)
        if ps_cg is not None:
            out.append(_fact("Current guide (latest results filing)", ps_cg))
        out += _guidance_bridge_lines(cp)
        out.append(_fact("Consensus stats (target + ratings)", cp.consensus_stats))
        out += _grouped_events_lines(cp.revision_events)
        sh = _fact("Surprise history (annual beat/miss)", m.consensus_context.surprise_history)
        out.append(sh)  # the one non-duplicate legacy fact, folded in
    # (content relocation 2026-07-24) POSITIONING (insider activity, short interest) moved OUT of
    # here, into the appendix — same move the management-commentary pointer already made. This
    # section is estimates & guidance; who owns the stock and who is short it is reference data,
    # and it was the only actual OWNERSHIP content in the dossier while the section NAMED for
    # ownership carried none.
    out.append("")
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


def _multiples_lines(s: Sourced[Any], *, grid_present: bool = False) -> list[str]:
    """(B4 · declutter P2) Trading multiples → the shared table. When the per-peer grid renders on
    the same page, the LTM rows here are its summary statistics restated (the grid carries every
    peer AND its own median row) — so only the FORWARD (NTM) rows survive, which exist nowhere
    else. Without the grid, the full table stands."""
    label = ("Forward multiples (name vs peer Low/Median/Mean/High · NTM)" if grid_present
             else "Trading multiples (name vs peer Low/Median/Mean/High · LTM+NTM)")
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
    if grid_present:
        rows = [r for r in rows if r[0].strip().upper().startswith("NTM")]
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


#: The scale, said where the scores are — a relative score read without it reads as absolute.
_CH_SCALE = ("S&P-MI relative score: 1 = top … 4 = bottom WITHIN each peer group — a rank among "
             "those companies, not an absolute measure")


#: The panel's field names, DERIVED from the labels rather than retyped — a fourth hand-copied
#: set across the py↔JS twins is exactly what `test_duplicate_definitions` exists to stop.
_CH_KEYS = tuple(d.lower() for d in _CH_DIMS)


def _credit_panel_col(p: Any) -> str:
    """A panel's COLUMN header: short, because a long one pushes the scores off a phone screen
    (preview, 2026-10-05). The full peer-group definition lives in the note. Twin: dossier.js."""
    return f"Industry ({p.n})" if p.population_kind == "industry" else f"Comps ({p.n})"


def _credit_panel_defn(p: Any) -> str:
    """What a panel's peer group IS, in full — the note line its short header points to."""
    if p.population_kind == "industry":
        industry = str(p.population).removesuffix(" (GICS industry)")
        return f"industry = {p.n} {industry} companies (GICS industry), the primary panel"
    return f"comps = the {p.n} companies of the CIQ comps template"


def _credit_panels_lines(s: Any) -> list[str]:
    """Every relative credit-health panel on file as ONE table: a ROW per dimension, a COLUMN per
    peer group — the industry panel first (primary), the comp set after. Read from the STRUCTURED
    panels, never from prose.

    WHY TWO COLUMNS AND NOT A WINNER: the same S&P score ranks the name inside two different
    populations, and on ten corpus names the two agreed on 23 of 40 dimensions. AMZN's liquidity is
    a 4 among megacap comps and a 2 among broadline retailers; both are true, and the page says
    which population each number belongs to instead of choosing one.

    DIMENSIONS DOWN, GROUPS ACROSS — the preview's own finding. The first cut put the groups in
    the rows, and at phone width their long labels pushed every score off-screen. Twin: dossier.js
    `creditPanels`."""
    ps = list(s.value or [])
    rows = [[dim, *(str(getattr(p, key)) for p in ps)] for dim, key in zip(_CH_DIMS, _CH_KEYS,
                                                                            strict=True)]
    notes = ["; ".join(_credit_panel_defn(p) for p in ps), _CH_SCALE]
    if len(ps) == 2:
        diff = [d for d, k in zip(_CH_DIMS, _CH_KEYS, strict=True)
                if getattr(ps[0], k) != getattr(ps[1], k)]
        if diff:
            notes.append(f"the two groups rank it differently on {', '.join(diff)}")
    rating = next((p.sp_long_term_issuer for p in ps if p.sp_long_term_issuer), None)
    notes.append(f"S&P issuer rating {rating}" if rating else "no S&P issuer rating")
    ind = next((p for p in ps if p.population_kind == "industry"), None)
    if ind is not None and ind.data_through:
        notes.append(f"industry panel reflects financials updated through {ind.data_through} — "
                     f"the export stamps no date of its own")
    if s.note:
        notes.append(str(s.note))
    return _table("Credit health — relative to each peer group", s.source_ref,
                  [_credit_panel_col(p) for p in ps], rows, note=" · ".join(notes),
                  num_cols=frozenset(range(len(ps))))


def _credit_health_lines(lv: Any) -> list[str]:
    """(K3) Credit health. The STRUCTURED panels when the page carries them (each row naming its
    peer group); otherwise the older 4-row mini-table parsed from the prose ``credit_health``
    value, kept so a page not yet refreshed renders exactly as it did. Falls back to the plain fact
    if the shape isn't as expected — never a fabricated score."""
    panels = getattr(lv, "credit_health_panels", None)
    if panels is not None and panels.status is SourceStatus.PRESENT and panels.value:
        return _credit_panels_lines(panels)
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
    # (buy-side layout, terse labels) the basis stays VISIBLE as a [TAG] — NET vs TOTAL vs FWD-ADJ
    # on adjacent rows is disclosure, never tooltip/cite-only; methodology beyond the basis lives in
    # the cite. Twins frontend leverageBlock()'s stat-grid cells (the md stays linear — content
    # parity, layout differs).
    lines = [
        "## Leverage & survival",  # (K5) header humanized; the net-vs-total discipline is per-row
        _fact("Net debt / EBITDA [NET]", lv.net_debt_to_ebitda, _mult),
        _fact("Total debt / EBITDA vs peers", lv.total_debt_to_ebitda),
        _fact("Net debt / OCF", m.quality.net_debt_to_ocf, _mult),
        _fact("Net debt / EBITDA [FWD-ADJ]", m.quality.net_debt_to_ebitda_adjusted),
        _fact("Interest coverage", lv.interest_coverage, _mult),
    ]
    # (declutter P1) when the two-input self-funding read exists it REPLACES the one-input survival
    # claim — the dossier used to print the weaker line and then a second line announcing that the
    # next one superseded it. Print the superseding read alone; the one-input line renders only for
    # a pre-RC-1 dossier that has nothing better.
    ps = m.primary_source
    if ps is not None and ps.self_funding.status is SourceStatus.PRESENT:
        # (terse label) the two-input rule reads in the value itself
        lines.append(_fact("Self-funding", ps.self_funding))
    else:
        lines.append(_fact("Survival", lv.survival))
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
    """(RC-1 C · declutter P2) The DECISION cross-checks from the filings — going concern (leads
    unsoftened when doubt is stated, else the checked-absence), the EBITDA-basis triangulation, and
    the 10-Q customer concentration. The pure VERIFICATION flags (wall coherence, guide
    verification) moved to the appendix (:func:`_verification_lines`) — they audit the assembly,
    they do not inform the verdict. Empty for a pre-RC-1 dossier.json."""
    ps = m.primary_source
    if ps is None:
        return []
    fil = ps.filing
    out = ["### Filing cross-checks — going concern · leverage basis", ""]
    gc = fil.going_concern if fil is not None else None
    if gc is not None and gc.substantial_doubt:  # doubt LEADS, unsoftened
        out += [f"- **⚠ Going concern — SUBSTANTIAL DOUBT:** {gc.verbatim}{_cite(gc.source_ref)}",
                f"  - management's plans: {gc.plans or '— none stated'}"]
    elif fil is not None:  # CHECKED-ABSENCE (not silence): the parser looked and found none
        out.append(f"- **Going-concern language:** none in latest 10-Q — checked, absent "
                   f"{_cite_inline(fil.source_ref)}")
    else:
        out.append("- **Going-concern language:** _UNKNOWN_ — latest 10-Q not parsed")
    tri_val = ps.basis_triangulation.value
    if tri_val is not None:  # multi-line → bold header + sub-bullets
        tri = tri_val.split("\n")
        out.append(f"- **{tri[0]}**{_cite(ps.basis_triangulation.source_ref)}")
        out += [f"  - {row.strip()}" for row in tri[1:] if row.strip()]
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


def _verification_lines(m: MechanicalLayer) -> list[str]:
    """(declutter P2) Assembly-verification flags — wall coherence and guide verification check the
    ASSEMBLY against the filings; they belong with the audit tier, not between decision sections."""
    ps = m.primary_source
    if ps is None:
        return []
    return [
        "### Assembly verification — filing vs panel",
        _fact("Wall coherence — filing ≤12m vs CIQ panel (same window)", ps.wall_coherence),
        _fact("Guide verification — CIQ guide vs release", ps.guide_verification,
              _fmt_guide_verification),
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

    out = [f"- **Maturity wall** · vs the {reference_date.isoformat()} reference:"]
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
        # word-boundary cap (the old [:26] cut mid-word: "Operating Lease Liabilitie")
        def _short(name: str, cap: int = 34) -> str:
            return name if len(name) <= cap else name[:cap].rsplit(" ", 1)[0] + "…"
        detail = ", ".join(f"{_short(i.description)} {_musd(i.principal_musd)}" for i in undated)
        undated_tot = sum(i.principal_musd or 0.0 for i in undated)
        out.append(
            f"  - undated (floor — no panel maturity): {_musd(undated_tot)} — {detail}")
    itemized = sum(i.principal_musd or 0.0 for i in inst.value)
    out.append(
        f"  - _reconciliation: itemized {_musd(itemized)} (panel {cs.detail_as_of}) vs the "
        f"aggregates below — the gap is unitemized / newer term loans; read the term-loan movement "
        "in the aggregates line, which names the period columns it spans._"
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


_ACC_IN_REF = re.compile(r"(\d{10}-\d{2}-\d{6})")


def _covenant_source_suffix(g: Any, dates: dict[str, str]) -> str:
    """(K1b) The FILING a covenant value was read from, appended to its clause.

    WHY A DATE AND NOT A BETTER SELECTOR. Selection can always be wrong — measured: EPAM's digest
    read "Expiration Date: October 21, 2026" from a 2017 8-K, against a capital-structure line
    saying Due 2030, and NOTHING on the page said which filing it came from. A dated source makes
    a stale read OBVIOUS beside the panel without anyone knowing the pointer set is mis-ordered,
    which is the principle the rest of this layer already runs on (the panel-age stamp, the
    multiples vintage, the extraction version). It is orthogonal to the ordering fix and lands
    first because it INDICTS rather than repairs — a wrong value that says where it came from is
    auditable; a wrong value that says nothing is not.

    The accession is carried inside ``base_ref``'s prose, and the pointer rows hold the dates, so
    the join is a lookup rather than a new fetch. An unmatched accession yields NOTHING rather than
    a guessed date — an unattributed clause reads exactly as it does today, never worse."""
    ref = getattr(g, "base_ref", None)
    m = _ACC_IN_REF.search(str(ref or ""))
    base = dates.get(m.group(1)) if m else None
    amended = [dates[a] for a in (getattr(g, "amended_by", ()) or ()) if a in dates]
    if not base and not amended:
        return ""
    if not base:
        return f" — per an 8-K filed {max(amended)}"
    tail = f", amended {max(amended)}" if amended else ""
    return f" — per an 8-K filed {base}{tail}"


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
    # accession -> filing_date, so each governing value can name the filing it was read from
    _pdates = {p.accession: p.filing_date
               for p in (ptrs.value if ptrs is not None and ptrs.value else [])
               if p.accession and p.filing_date}
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
            parts.append(f"  - **{label}:** {clause}{_covenant_source_suffix(g, _pdates)}")
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
    # (PR-3) THE PANEL'S AGE LEADS THE INSTRUMENTS IT DESCRIBES — the stamp-position rule: a vintage
    # read AFTER the numbers does not work, because by then the reader has already taken them as
    # current. Every committed schedule is 82-280 days old and the page has never said so, which is
    # why NFLX still lists a facility terminated in February. Rendered only when the field exists;
    # dossiers assembled before it carry None, and "unknown" would claim we looked.
    if cs.panel_vintage is not None:
        out.append(_fact("Debt schedule vintage", cs.panel_vintage))
    if inst.status is SourceStatus.PRESENT and inst.value:
        near = [i for i in inst.value if _near_dated(i, reference_date)]
        moved = len(inst.value) - len(near)
        note = (f"{moved} undated / later aggregate line item(s) in the appendix panel"
                if moved else "")
        if near:
            out += _table(f"Live instruments — near-dated (≤12m + {reference_date.year + 1}) — "
                          f"panel {cs.detail_as_of}", inst.source_ref, _CS_COLS,
                          [_instrument_row(i) for i in near], note=note, num_cols=_CS_NUM)
        else:
            # (declutter) no tranche due in the window → say so; never an all-header empty table
            out.append(f"- **Live instruments — near-dated (≤12m + {reference_date.year + 1}):** "
                       f"none due in the window — {note or 'full panel in the appendix'}"
                       f"{_cite(inst.source_ref)}")
    else:
        out.append(_fact("Capital structure (instruments)", inst))
    out += _maturity_wall_lines(cs, reference_date)
    # NO PERIOD IN THE LABEL (audit R3). The value stamps itself with the column it was read from,
    # so a fixed "(latest quarter)" here could only ever contradict it — as it did on SMPL, where
    # both the label and the value called an annual step a quarter.
    out.append(_fact("Capital-structure aggregates", cs.summary))
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
    # the audit tier: the md keeps it in full; the web collapses it in a <details> (which PRINTS
    # EXPANDED since the T1 amendment); the JSON is machine-complete. Nothing deleted. (The old
    # header carried the internal tier framing AND said "print-excluded" — stale on both counts.)
    out: list[str] = ["", "### Capital structure & debt terms — instruments · pointers · covenants"]
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


# THE TWO-PANEL TEV STAMP IS GONE, AND THE DEFECT IT GUARDED DOES NOT EXIST (review of #321).
# `_tev_stamp`/`_stock_as_of` printed "BLENDED: market cap <stock_info.as_of> + net debt <comps>",
# which was wrong twice over: `stock_info.as_of` is the EOD PRICE date, not the cap's vintage, and
# the cap itself comes off the SAME CIQ Comparable Analysis panel as net debt on all 11 committed
# names — NCNO's cap and net debt are both 2026-07-20, so the page labelled a single-vintage TEV
# as blended. It manufactured the false provenance stamp it claimed to prevent.
# The #320 record's "mixed-basis TEV" finding rested on the same mistake and is corrected in STATE.


def _implied_expectations_lines(v: Any) -> list[str]:
    """(G) Price-inverted expectations, MULTIPLES-space. Shared table: each stated multiple → the
    fundamental LEVEL price implies (TEV ÷ multiple); the consensus path anchors are juxtaposed
    BESIDE. The heterogeneity gate is cited SHORT on the header (verbatim once, at Peer comps —
    H3); a vintage-mismatch caveat renders when the pricing-vintages diverge (G5).

    THE NEVER-DIFFERENCED RULE STILL BINDS HERE AND NO LONGER BINDS THE SECTION (A2, 2026-08-03).
    This block juxtaposes and does not subtract — that has not changed. What changed is that the
    section now also carries `_ev_gap_lines`, which DOES state a ratio between our leg and the
    street. The distinction is not squeamishness about arithmetic: THIS table inverts a PRICE, so
    differencing it against consensus would produce an implied upside — a verdict in numbers, which
    the machine does not author. The EV gap divides OUR OWN COMMITTED LEG by consensus and
    reconciles by identity, so it is a decomposition of a stated position, not a conclusion about
    what the price should be. Same section, two different objects; the old docstring said the rule
    covered the section and now it says what it actually covers.

    THE TEV STAMP IS SINGLE-PANEL AND CORRECT AS STATED. `recompute_derived` strikes TEV from
    `stock_info.market_cap + peer_grid.net_debt`, and BOTH come off the CIQ Comparable Analysis
    panel — verified on all 11 committed names, where the cap's own as-of equals the stored
    `tev_as_of` every time. A "blended" caveat here was briefly added and REMOVED: it read
    `stock_info.as_of`, which is the EOD PRICE date, and so invented a two-panel claim about a
    one-panel number."""
    ie = getattr(v, "implied_expectations", None)
    if ie is None:
        return []
    out = [
        f"- **What the current price implies (at stated multiples)** — "  # (K4) human-facing rename
        f"{_gate_shortref(ie.heterogeneity_gate)}",
        f"  - _TEV as-of {ie.tev_as_of} · multiples as-of {ie.multiples_as_of} · † at the name's "
        "own multiple the implied level is consensus by identity_",
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

    # (audit) H7/P8 made BOTH EBITDA and Revenue anchors UNKNOWN-able — they read the DIRECT
    # Estimates→Trends levels (may lack FY26/FY27), so show the NOTE via _sourced_str, never bare
    # "None". rev_anchors is guarded the same way (no longer the always-PRESENT ladder).
    out.append(f"- **Consensus path anchors (EBITDA):** {_sourced_str(ie.anchors)}")
    if ie.rev_anchors is not None:  # the parallel revenue anchors substantiate the TEV/Rev identity
        out.append(f"- **Consensus path anchors (Revenue):** {_sourced_str(ie.rev_anchors)}")
    # (declutter) the coherence SELF-CHECK prints only when it FAILS — a passing
    # residual-within-tolerance line is assembly QA, not analysis. Same for net-debt.
    if not ie.vintage_coherent:
        out.append(f"  - _⚠ {ie.coherence_note}_")
    if not ie.net_debt_reconciled:
        out.append("  - _⚠ net-debt disagrees with the cash/debt bridge — see the TEV source_")
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
        "### Implied equity at peer multiples",  # (tier redesign) vendor out of the title
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


def _all_none_row(cells: list[str]) -> bool:
    """A row whose every cell literally reads 'none' carries no information — the label's absence
    IS the fact, and six cells of 'none' are furniture (IT's Dividend/sh row)."""
    return bool(cells) and all(str(c).strip().lower() == "none" for c in cells)


def _fin_table_lines(label: str, s: Sourced[Any]) -> list[str]:
    """A Sourced[FinTable] → the shared markdown table (columns → header, each row's [label, *cells]
    → a data row). UNKNOWN/MISSING falls back to the standard fact line."""
    if s.status is not SourceStatus.PRESENT or not s.value:
        return [_fact(label, s)]
    ft = s.value
    rows = [[r.label, *r.cells] for r in ft.rows if not _all_none_row(list(r.cells))]
    return _table(label, s.source_ref, ft.columns, rows, ft.note)


def _ebitda_basis_lines(fs: FinancialSummary) -> list[str]:
    """The actual-vs-estimate EBITDA basis read, as ONE line under the annual table.

    RENDERED ONLY WHEN THE ROWS DISAGREE. A consistent read is the expected state and printing it
    everywhere would train the reader to skip the line — which is exactly how the flagged names
    would then be missed. The number is always in `dossier.json` regardless; this is the surface
    that has to earn its space.

    ONE DEFINITION, TWO CALL SITES (brief snapshot + appendix). The repo's twin-drift rule: the same
    caveat rendered by two copies is one edit away from saying two different things about the same
    table.
    """
    b = fs.ebitda_basis
    if b is None or not b.divergent:
        return []
    return ["", f"> **EBITDA basis — the actual and estimate rows differ.** {b.note}", ""]


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
    hdr = ("## Financial statements (actuals + consensus estimates) "
           f"— {_asof_header(fs.as_of)}")
    out = ["", hdr, "### Annual — every exported fiscal year + LTM + consensus"]
    annual = _annual_with_fcf_label(fs.annual)  # D5b: FCF row relabeled + footnoted (display-only)
    out += _fin_table_lines("Annual financials ($M; E = consensus)", annual)
    out += _ebitda_basis_lines(fs)
    out.append("### Quarterly — every exported quarter")
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


def _positioning_lines(m: MechanicalLayer) -> list[str]:
    """(content relocation 2026-07-24) OWNERSHIP & POSITIONING — insider activity + short interest,
    relocated out of "The street" (which is estimates & guidance). Free DATED feeds: counts, shares
    and dates only, never an interpretation. Rendered only when present — pre-F JSON has neither
    field, so the whole section is omitted rather than printing two empty rows."""
    cp = m.catalyst_path
    if cp is None:
        return []
    rows = []
    if cp.insider_activity is not None:
        # THE LABEL CARRIES THE HORIZON ONLY WHEN THE VALUE DOES NOT — derived, never chosen.
        # #319 removed "6m" from this label while the committed value still read
        # `sells 0 (net +90.0K sh)`, leaving the served page with NO horizon at all. Reverting was
        # correct then and would be wrong now that refreshed values state their own window; and
        # FUBO makes a fixed answer impossible either way — its record is SEALED, so its value can
        # never be refreshed, and a hardcoded "(Form 4)" would strand exactly that page.
        # Reading the value settles all three cases and cannot drift out of step with it.
        _horizon_in_value = "in the last " in str(cp.insider_activity.value or "")
        rows.append(_fact("Insider activity (Form 4)" if _horizon_in_value
                          else "Insider activity (Form 4, 6m)",
                          cp.insider_activity, _fmt_insider))
    if cp.short_interest is not None:
        rows.append(_fact("Short interest (FINRA)", cp.short_interest))
    return ["### Ownership & positioning", *rows, ""] if rows else []


def _md_cell(text: str) -> str:
    """Analyst free text safe for a markdown TABLE cell. GFM splits rows on "|" before any inline
    parsing, so an unescaped pipe shifts every later cell and the trailing ones are DISCARDED —
    a source silently vanishing, which is worse than an ugly row."""
    return text.replace("|", "\\|")


def _ref_value(value: float, unit: str) -> str:
    """A reference point in DISPLAY-natural form. The record stores value + unit separately, already
    in display units (4.06 + "%", 6.56 + "x"), so most units suffix — but a currency unit PREFIXES
    its symbol: "1450.9$M" is not a number anyone reads.

    EXACT TWIN of dossier.js ``refValue`` — pinned by test_ref_value_py_js_parity, because the
    first cut was NOT: this used ``,.6g`` while the JS used a bare ``toLocaleString``, and three
    committed references already rendered differently in the PDF and on the web ($1,416.21M vs
    $1,416.208M). Two traps that fix avoids, both verified: ``g`` flips to SCIENTIFIC at 1e6
    ("$1.23457e+06M" in a PDF), and ``toLocaleString``'s default 3-fraction-digit cap silently
    rounds a non-zero source-bound value to "$0M" — the fabrication class this repo forbids.
    So: fixed 6 decimals (every committed value carries ≤3), trailing zeros trimmed, manual
    grouping — never scientific, never a rounded-away non-zero."""
    n = float(value)
    s = f"{n:.6f}"
    if float(s) == 0 and n != 0:
        s = f"{n:.10f}"                 # a value smaller than 6dp must never display as 0
    s = s.rstrip("0").rstrip(".")
    neg, s = s.startswith("-"), s.lstrip("-")
    ip, _, fp = s.partition(".")
    s = ("-" if neg else "") + f"{int(ip):,}" + (f".{fp}" if fp else "")
    return f"${s}{unit[1:]}" if unit.startswith("$") else f"{s}{unit}"


def _assumption_methodology_lines(card: ScenarioRecord | None) -> list[str]:
    """(addition #1, 2026-07-27) "How these numbers were set" — the per-AXIS methodology behind the
    underwrite: a method sentence and the SOURCE-BOUND reference points each leg was chosen
    against. Schema 1.1 has captured this on every record since it shipped, and NOTHING rendered
    it — the reviewable "why these numbers" was committed and shown to nobody (SMPL alone carries
    3 axes and 12 references). Appendix, because it is the audit of the analyst's inputs, not a
    decision surface; the legs themselves and their reasons already render in the Brief's grid.

    An UNRATIFIED axis is marked: the record distinguishes a method sentence the analyst stood
    behind from one that merely shipped with the run. Absent record → nothing (most names carry no
    underwrite). Twin: dossier.js assumptionMethodology()."""
    axes = getattr(card, "assumptions", None) if card is not None else None
    if not axes:
        return []
    out = ["## How these numbers were set", "",
           "_Per-axis methodology from the underwrite record — the reference frame each leg was "
           "chosen against, not a re-derivation._", ""]
    for axis, a in axes.items():
        # RATIFIED-BY is the predicate, matching the card exactly: frontend/build.py emits
        # `unratified` from `not ratified_by`, so badging off `ratified` (the DATE) here let the
        # twins disagree whenever only one of the pair was set. The date is shown when present.
        stamp = (f" · ratified{f' {a.ratified}' if a.ratified else ''}" if a.ratified_by
                 else " · **DRAFT — not ratified by the analyst**")
        out += [f"### {axis.capitalize()}{stamp}", "", a.method, ""]
        if a.references:
            # The SOURCE is an ENDNOTE, not a third column. Main-body cites resolve to the Sources
            # list in this repo (frontend/lib/cites.js states the two sanctioned modes; inline is
            # for on-demand audit blocks). This card hand-rolled the inline form on BOTH twins —
            # the same defect that motivated extracting cites.js out of uw-card.js. `_cite` also
            # DEDUPES: a source cited on four axes prints once instead of four times.
            out += ["| reference | value |", "| --- | ---: |"]
            # ESCAPE PIPES: the label is analyst free text in a markdown TABLE. GFM splits on "|"
            # before inline parsing, so a pipe silently shifts cells and drops content (backticks
            # do not protect it). The value is machine-formatted and the cite is a bare [n].
            # (schema 1.3) leg and exclusion render FROM FIELDS, twinning the web: a leg chip
            # after the label, and an excluded row italicised with its reason stated — never a
            # confident bare number for a reference the analyst rejected. Labels stay verbatim.
            for r in a.references:
                leg = f" `{r.leg}`" if r.leg else ""
                if r.excluded:
                    out.append(f"| _{_md_cell(r.label)}{leg} — excluded: "
                               f"{_md_cell(r.excluded_reason or '')}_ "
                               f"| _{_ref_value(r.value, r.unit)}_{_cite(r.source)} |")
                else:
                    out.append(f"| {_md_cell(r.label)}{leg} "
                               f"| {_ref_value(r.value, r.unit)}{_cite(r.source)} |")
            out.append("")
        else:
            # a pure-judgment method honestly stated beats a fabricated reference (schema 1.1)
            out += ["_No reference points recorded — stated as judgment._", ""]
        # (schema 1.3) dated axis NOTES — analyst findings beside the numbers they interpret
        # (the home the SMPL boundary-cells narrative never had). Twin: assumptionMethodology().
        for n in getattr(a, "notes", []) or []:
            out += [f"_{n.date} — {n.text}_{_cite(n.source) if n.source else ''}", ""]
    return out


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


def _dejargon_caveat(c: str) -> str:
    """(A) Render-time cleanup — the human tier never shows the synthesis's field tokens or the
    internal rule numbers a guardrail cites; the committed JSON keeps the raw strings (machine
    tier). Twin of dossier.js ``dejargonCaveat``. ``AS_OF`` (a real sidecar name) is left intact."""
    c = c.replace("evidence_balance", "the written assessment")
    c = c.replace("bull_points", "bull points").replace("bear_points", "bear points")
    return re.sub(r"\s*\(rule \d+\)", "", c)


_CATALYST_STALE_RE = re.compile(
    r"Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; "
    r"its data is on/after (?P<floor>[\d-]+) \(the latest embedded revision event\), so it is "
    r"up to (?P<days>\d+)d before the [\d-]+ reference — beyond the (?P<tol>\d+)d tolerance — "
    r"and the true export date is unknown, so freshness cannot be confirmed\. (?P<action>.+)"
)


def _reword_catalyst_stale(c: str) -> str:
    """(Option 1) Lead the catalyst-staleness caveat with the name-specific DISCRIMINATOR — how many
    days stale, vs the tolerance — instead of the structural 'no as-of stamp' preamble that buried
    it (all CIQ exports lack a stamp; only some are stale). Render-time, deterministic; fails
    through unchanged if the template ever differs. Twin of dossier.js ``rewordCatalystStale``."""
    m = _CATALYST_STALE_RE.search(c)
    if m is None:
        return c
    return (
        f"Estimates data up to {m['days']}d stale (beyond the {m['tol']}d tolerance) — freshness "
        f"UNVERIFIABLE: the CIQ Estimates export has no as-of stamp, and its data is on/after "
        f"{m['floor']} (its latest embedded revision event — a worst-case floor on the true export "
        f"date). {m['action']}"
    )


_ACRONYMS = re.compile(r"\b(ebitda|eps|fcf|ebit|roic|roe)\b", re.IGNORECASE)


def _fix_acronyms(s: str) -> str:
    """(D) Financial acronyms render uppercase even when a parser lower-cased them (a guidance label
    like 'adjusted ebitda outlook'). Word-boundary only — never mid-word. Twin of dossier.js
    ``fixAcronyms``."""
    return _ACRONYMS.sub(lambda m: m.group(0).upper(), s)


def _caveat_block(c: str) -> list[str]:
    """(D4) A guardrail caveat renders in the what / where / why-it-matters / how-to-verify shape,
    the offending sentence IN FULL. A mechanical / 'pull CIQ …' caveat is already a complete
    advisory sentence, so it stays a single full-sentence bullet (no forced split)."""
    c = _reword_catalyst_stale(_dejargon_caveat(c))  # committed strings, any variant
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


def _caveat_group_block(group: list[str]) -> list[str]:
    """(D4·collapse) N caveats sharing one guard TYPE (same lead + what/where/why shape) render as
    ONE advisory — the lead once, each offending claim nested with its own where, one shared
    why/how when identical. The twin of the web ``caveatGroupBlock``: the same guard firing on two
    synthesis points (BRBR's 2× margin-compression) is one action item, not two near-identical
    blocks; every claim is still shown in full."""
    matches: list[re.Match[str]] = []
    for c in group:
        m = _CAVEAT_RE.match(_dejargon_caveat(c))
        assert m is not None  # groups of >1 are only formed from _CAVEAT_RE-matching caveats
        matches.append(m)
    lead = matches[0].group("lead").strip()
    parts = [
        (m.group("where").strip(), m.group("what").strip(), *_split_why_how(m.group("why").strip()))
        for m in matches
    ]
    same_why = len({p[2] for p in parts}) == 1
    same_how = len({p[3] for p in parts}) == 1
    out = [f"- **{lead}** ({len(parts)} points)"]
    # LOSSLESS: a shared why/how prints once below; a why/how that DIFFERS across the group prints
    # per-claim on the where line — so the collapse never silently drops a claim's why-it-matters or
    # how-to-verify (the "curating never deletes a fact" contract).
    for where, what, why, how in parts:
        out.append(f"  - {what}")
        line = f"    - _where:_ {where}"
        if not same_why:
            line += f" · _why:_ {why}"
        if not same_how and how:
            line += f" · _how:_ {how}"
        out.append(line)
    if same_why:
        out.append(f"  - _why it matters:_ {parts[0][2]}")
    if same_how and parts[0][3]:
        out.append(f"  - _how to verify:_ {parts[0][3]}")
    return out


def _flags_section(d: Dossier) -> list[str]:
    """(D1) The human-facing CAVEATS render at the TOP (right under the header) — the first thing
    the human sees is what to verify before trusting anything below. Each renders in the D4
    what/where/why-it-matters/how-to-verify shape, the offending sentence IN FULL. Only decision
    caveats show here (re-voiced, plus the 'pull CIQ …' notes); the machine-QA self-checks live in
    ``d.qa_flags`` (JSON / dev only). The dossier assembles and cites; the verdict is the human."""
    # (tier redesign) analyst caveats ONLY — the `primary-source:` assembly-log line is process
    # telemetry and renders in Record & reproduce, never as a caveat to the reader.
    caveats = [c for c in d.caveats if not _is_process_caveat(c)]
    if not caveats:
        return []
    # (Option 2) collapse caveats sharing a guard TYPE into one grouped block; non-matching +
    # singletons stay one-per-block (identical to the prior render for the 99% single case). Grouped
    # FIRST so the (B) header count is DISTINCT advisories — one grouped card per type, twin of web.
    groups: list[list[str]] = []
    by_lead: dict[str, list[str]] = {}
    for c in caveats:
        m = _CAVEAT_RE.match(_dejargon_caveat(c))
        if m is None:
            groups.append([c])
            continue
        lead = m.group("lead").strip()
        if lead in by_lead:
            by_lead[lead].append(c)
        else:
            g = [c]
            by_lead[lead] = g
            groups.append(g)
    hdr = "## ⚠ Analyst caveats — verify before the verdict"
    out = [hdr, "", f"_{len(groups)} to verify._", ""]
    for g in groups:
        out += _caveat_block(g[0]) if len(g) == 1 else _caveat_group_block(g)
    out.append("")
    return out


def _is_process_caveat(c: str) -> bool:
    """Assembly telemetry ("primary-source: N EX-99.1 release(s) … (+0.3s fetch)") — a process log
    line, not an analyst caveat; it renders in the Appendix's Record & reproduce."""
    return c.startswith("primary-source:")


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

    # (declutter P2) rows that DUPLICATE another table on the same page are dropped: the
    # revenue/EBITDA/EBITDA-margin series are cell-identical to the financial summary (which now
    # carries the FULL history), and ROIC is cell-identical to the return-ratios RoCE row directly
    # beneath this table. Each drop is CONDITIONAL on the duplicating table being present, so a
    # dossier without a Ratios sheet keeps its ROIC here (fail-honest, never a silent hole).
    fs_present = (m.financial_summary is not None
                  and m.financial_summary.annual.status is SourceStatus.PRESENT)
    rr_present = (m.return_ratios is not None
                  and m.return_ratios.status is SourceStatus.PRESENT)
    dup = (({"Revenue ($M)", "EBITDA ($M)", "EBITDA margin"} if fs_present else set())
           | ({"ROIC"} if rr_present else set()))
    rows: list[list[str]] = []
    for disp, aliases in _TRAJ_ROWS:
        if disp in dup:
            continue
        series = next((merged[a] for a in aliases if a in merged), None)
        if series is not None:
            by_n = {_norm(p): v for p, v in series}
            rows.append([disp, *[by_n.get(_norm(p), "–") for p in periods]])
    if not rows or not periods:
        if merged and periods:
            # everything deduplicated away — keep the decision-relevant footnote, skip the table
            frags0 = [f.strip() for n in notes for f in n.split(";") if f.strip()]
            note0 = "; ".join(dict.fromkeys(frags0))
            return [f"- _{yoy}. {note0}_" if yoy else f"- _{note0}_"] if (yoy or note0) else []
        pick = mt if mt.status is SourceStatus.PRESENT else my  # nothing parsed → raw (back-compat)
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
        # (K6 widening, NARROWED by the hybrid audit) adjusted EBITDA within ~40 chars of a negative
        # marker — a bare "(" fired on ANY parenthetical (SMPL: "adjusted EBITDA -18.4% …
        # (-460bps)" → an accidental Tier-1 on a decline point), so "(" now counts only when it
        # opens an accounting-$ amount ("($5.5)"); "-$" and the word "negative" unchanged.
        r"|\badjusted\s+ebitda\b.{0,40}?(?:-\s*\$|\(\s*\$|\$\s*\(|negative)"
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


# (D3 hybrid, ratified 2026-07-24 on the 119-draw archive) SIDE-AWARE tier rank: the bear case
# keeps solvency-first (death-risk first — a survival fact is NEVER demoted below a narrative
# point); the bull case leads with the mean-revert MECHANISM (revenue → margin) and demotes the
# balance sheet to the ENABLER slot (it is why you can wait, not why you are right). Face-validity
# editorial convention, never outcome-tuned. Valuation stays last on both sides.
_BULL_TIER_RANK: dict[float, int] = {2.0: 0, 3.0: 1, 1.0: 2, 4.0: 3, 4.5: 4, 5.0: 5}
_BEAR_TIER_RANK: dict[float, int] = {1.0: 0, 2.0: 1, 3.0: 2, 4.0: 3, 4.5: 4, 5.0: 5}


def _decisive_refs(s: Any, side: str) -> frozenset[str]:
    """The SAME-SIDE decisive-question evidence refs (bull ↔ evidence_for, bear ↔
    evidence_against). Rule 2 makes synthesis copy source_refs verbatim from the supplied facts, so
    exact-ref overlap is a sound, deterministic crux-linkage signal (mean ~31% of a list's points
    across the 119-draw archive; 0-overlap lists degrade gracefully to the tier order)."""
    dq = getattr(s, "decisive_question", None)
    if dq is None:
        return frozenset()
    ev = dq.evidence_for if side == "bull" else dq.evidence_against
    return frozenset(p.source_ref for p in (ev or []))


def _driver_refs_of(mech: Any) -> frozenset[str]:
    """Refs of the operating-driver rows — a point citing one is MECHANISM-BEARING (synthesis rule
    12's preference, enforced as a within-tier tiebreak, not just inclusion)."""
    od = getattr(mech, "operating_drivers", None)
    if od is None:
        return frozenset()
    return frozenset(r.source_ref for r in (od.rows or []) if r.source_ref)


def _ordered_points(
    pts: list[Any], *, side: str,
    crux_refs: frozenset[str] = frozenset(), driver_refs: frozenset[str] = frozenset(),
) -> list[tuple[Any, float, int, bool, bool]]:
    """(D3 hybrid) Deterministic ordering of one case's points — plain English: the bull case
    leads with the points that ground the DECISIVE QUESTION, the bear case leads with SURVIVAL.

    Sort keys (STABLE sort — ties keep emission order, the render is deterministic):
      bull: (crux-linked first, side-aware tier rank, mechanism-bearing, citation-class, emission)
      bear: (side-aware tier rank, crux-linked, mechanism-bearing, citation-class, emission)
    The asymmetry is the ratified hybrid: on the bull side the crux IS the thesis, so it dominates;
    on the bear side the tier dominates so a T1 survival fact can never be demoted below a
    narrative crux point (0 demotions across the 119-draw archive; crux-dominant ordering demoted
    one in ~5 draws). Ordering is WITHIN a case only (nothing nets across bull vs bear).
    Returns (point, tier, citation_rank, crux_linked, mechanism_bearing) for the dev view."""
    rank = _BULL_TIER_RANK if side == "bull" else _BEAR_TIER_RANK
    keyed = []
    for i, p in enumerate(pts):
        tier = _point_tier(p.claim)
        cr = _citation_rank(p.source_ref, getattr(p, "cited", True))
        crux = 0 if p.source_ref in crux_refs else 1
        mech_b = 0 if p.source_ref in driver_refs else 1
        key = ((crux, rank[tier], mech_b, cr, i) if side == "bull"
               else (rank[tier], crux, mech_b, cr, i))
        keyed.append((key, p, tier, cr, crux == 0, mech_b == 0))
    keyed.sort(key=lambda t: t[0])
    return [(p, tier, cr, cx, mb) for _, p, tier, cr, cx, mb in keyed]


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
    out = ["## The argument", ""]  # discipline language lives ONCE, in How to read this dossier
    if s.evidence_balance:
        out += [f"**Evidence balance:** {s.evidence_balance}", ""]
        out += _draw_agreement_md(s)

    def cite(p: Any, tag: str = "") -> str:
        warn = "" if getattr(p, "cited", True) else " ⚠ uncited"
        return f"- {p.claim}{tag}{warn}{_cite(p.source_ref)}"

    driver_refs = _driver_refs_of(d.mechanical)

    def ordered(title: str, pts: list[Any], side: str) -> None:  # D3 hybrid order
        out.append(f"### {title}")
        for p, tier, cr, cx, mb in _ordered_points(
                pts, side=side, crux_refs=_decisive_refs(s, side), driver_refs=driver_refs):
            marks = ("" if not dev else
                     (" · crux" if cx else "") + (" · mech" if mb else ""))
            tag = (f" `[T{tier:g} {_TIER_NAME[tier]} · {_CITATION_CLASS[cr]}{marks}]`"
                   if dev else "")
            out.append(cite(p, tag))
        out.append("")

    def plain(title: str, pts: list[Any]) -> None:  # emission order (decisive evidence)
        out.append(f"### {title}")
        out.extend(cite(p) for p in pts)
        out.append("")

    _sl = BY_KEY[d.sleeve]
    ordered(_sl.bull_label, s.bull_points, "bull")
    ordered(_sl.bear_label, s.bear_points, "bear")
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


# --- (catalyst calendar · PLACEMENT B, re-ordered 2026-07-27) ---------------------------------
def _calendar_entries(
    d: Dossier, card: ScenarioRecord | None,
) -> list[tuple[str, str, str, str, str]]:
    """The MERGED dated entries — machine rows (mechanical.catalyst_calendar) + the analyst's
    dated triggers from the underwrite record — as (date, event, basis, tests, source_ref),
    sorted by date. The machine rows are assembled; the trigger rows are ANALYST-TYPED (the
    machine never invents a trigger or its date). Empty when neither exists."""
    entries: list[tuple[str, str, str, str, str]] = []
    cal = d.mechanical.catalyst_calendar
    if cal is not None:
        for r in cal.rows:
            entries.append((r.expected_date, r.event, r.date_basis, r.tests_what, r.source_ref))
    # dated triggers live on the VERDICT block (they are the recorded decision's falsifiers)
    for t in (getattr(getattr(card, "verdict", None), "dated_triggers", None) or []):
        basis_note = f" ({t.basis})" if t.basis else ""
        entries.append((
            t.deadline, f"Re-underwrite trigger: {t.trigger}", "trigger-deadline",
            "the analyst's own falsifier — unresolved by this date, the monitor flags "
            "re-underwrite due", f"underwrite record (analyst-typed{basis_note})"))
    entries.sort(key=lambda e: e[0])
    return entries


def _catalyst_calendar_lines(d: Dossier, card: ScenarioRecord | None) -> list[str]:
    """(PLACEMENT B, re-ordered 2026-07-27) The dated re-rating path. It followed the argument as
    the Analysis CLOSER until the decision re-order; it still follows the argument, but now sits
    4th of 10 — on a months-to-quarters book the dated path is the trade, not an afterthought.
    Rows are dated + basis-labeled + cited; an EMPTY
    assembled calendar renders its honest reason (never invented dates); absent field (pre-build
    dossier.json) renders NOTHING — old artifacts round-trip without a phantom section."""
    cal = d.mechanical.catalyst_calendar
    if cal is None and not (
            getattr(getattr(card, "verdict", None), "dated_triggers", None) or []):
        return []
    out = ["## Catalyst calendar — what tests the thesis, and when", ""]
    entries = _calendar_entries(d, card)
    if entries:
        for date_s, event, basis, tests, src in entries:
            out.append(f"- **{event}** — ~{date_s} `[{basis}]` — {tests}{_cite(src)}")
    else:
        out.append("- _no dated catalysts could be assembled — see the QA flags "
                   "(a missing date is stated, never guessed)_")
    if cal is not None and cal.qa_flags:
        out += [f"  - _QA: {q}_" for q in cal.qa_flags]
    out += ["", "_Dates assembled from sources or the analyst's own triggers; no probabilities, "
            "no weighting, no direction — weighing catalysts is the verdict's job._", ""]
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
    """Only DECISION-THREATENING caveats (lead clause), never freshness/plumbing ones — and never
    a RESOLVED one: that is the record of a check that PASSED, not a demand to verify (surfaced by
    VRRM, whose "RESOLVED (P/E basis)" caveat fired the Brief warning strip)."""
    out: list[str] = []
    for c in caveats:
        if re.match(r"RESOLVED\b", c, re.IGNORECASE):
            continue
        if not _BRIEF_DECISION_KW.search(c):
            continue
        lead = re.split(r";|\s+—\s+", c, maxsplit=1)[0].strip()
        if len(lead) > 120:
            lead = lead[:117].rstrip() + "…"
        out.append(lead)
        if len(out) >= limit:
            break
    return out


def _draw_agreement_md(s: Synthesis) -> list[str]:
    """The reproducibility of THIS build's read, as a COUNT with its boundary — never a rate.

    Five draws cannot support a percentage (3-of-5 carries a 95% CI of roughly [23%, 88%]), so this
    prints what happened and refuses to imply more. A single-draw artifact prints nothing at all:
    "not measured" must not read as "agreed", which is why the absent case is silent rather than
    reassuring.
    """
    a = s.draw_agreement
    if a is None or a.attempted < 2:
        return []
    if a.unanimous:
        return [f"_Reproducibility: all {a.completed} of {a.attempted} draws on this build "
                f"returned the same lean._", ""]
    split = ", ".join(f"{n}x {lab or 'unparsed'}" for lab, n in sorted(a.labels.items(),
                                                                      key=lambda kv: -kv[1]))
    return [f"**Reproducibility: the draws DISAGREED** — {a.completed} of {a.attempted} draws "
            f"gave {split}. The read below is the first draw carrying the majority lean, and the "
            f"machine proposal is withheld. A tally of this build, not a rate.", ""]


def _brief_case_lines(s: Any, mech: Any, *, sleeve: str = DEFAULT_SLEEVE) -> list[str]:
    """THE CASE, condensed — top-3 bull / top-3 bear (same evidence-weighted hybrid order as
    Analysis, so the Brief's three ARE the lead of the full argument). The decisive question +
    unknowns live in the cover's crux block; the FULL synthesis stays in the Analysis tier."""
    if s is None or (not s.bull_points and not s.bear_points):
        return []
    # (tier redesign) no inner "The case" line — the section header carries it; leg labels state
    # the claim, not the house shorthand.
    out: list[str] = ["_(top points; the full argument is in Analysis)_", ""]
    driver_refs = _driver_refs_of(mech)

    def top3(pts: list[Any], side: str) -> list[str]:
        ordered = _ordered_points(pts, side=side, crux_refs=_decisive_refs(s, side),
                                  driver_refs=driver_refs)
        return [f"- {p.claim}{_cite(p.source_ref)}" for p, *_ in ordered[:3]]

    _sl = BY_KEY[require_sleeve(sleeve, where="render._brief_case_lines")]
    out += [f"_{_sl.bull_label}:_", *(top3(s.bull_points, "bull") or ["- —"])]
    out += [f"_{_sl.bear_label}:_", *(top3(s.bear_points, "bear") or ["- —"])]
    # (buy-side cover) key unknowns moved to the cover's crux block — no second copy here
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


def _cap_drift(si: StockInfo) -> str:
    """`" ⚠ implies $68.18/sh vs CMP (-13.2%)"` when the cap and the price disagree, else `""`.

    THE NUMBER ALREADY EXISTED AND NEVER REACHED THE PAGE (2026-08-12). `reconcile_cap` computes
    this on every build — UBER's cap implies $68.18/sh against the $78.54 close printed two fields
    to its left — and `check_freshness` deliberately does NOT fail on ordinary drift, because
    failing would stop 8 of 14 builds. Its own docstring assigns the disclosure to rendering
    instead ("a rendering obligation, clause (e)"), and clause (e) shipped only HALF of it: the cap
    got its VINTAGE and never its MAGNITUDE. A reader cannot infer 13% from a date, so the analyst
    who found this had to fetch the share count and recompute — which is the work the page exists
    to have already done.

    WHY THE GAP AND NOT THE DATE decides whether this prints: 8 of the 14 committed names carry NO
    `market_cap_as_of` at all, so a vintage-keyed caveat is blank exactly where the drift is worst
    (AORT -18.4%, VITL -19.0%, MVST +17.6% — all undated). The gap is computable whenever the three
    inputs are present, which is the condition the reconciliation already requires.

    Silent inside the tolerance the guard itself uses: a 0.0% name (BRBR, EPAM, NFLX, V, VRRM) says
    nothing, so the mark means something wherever it appears.
    """
    p = SourceStatus.PRESENT
    if not (si.market_cap.status is p and si.shares_out.status is p and si.price.status is p):
        return ""
    recon = reconcile_cap(cap_musd=si.market_cap.value, shares=si.shares_out.value,
                          spot=si.price.value)
    if recon is None or abs(recon.gap) <= RECONCILE_TOLERANCE:
        return ""
    # A SHARE-BASIS mismatch is not drift and must not read as it: the ratio wording names the
    # corporate action instead. Unreachable on a passing build (the guard raises on it) — kept
    # because this renderer also runs over artifacts assembled before that guard existed.
    if recon.corporate_action:
        return f" ⚠ SHARE-BASIS MISMATCH: implies ${recon.implied_price:,.2f}/sh vs CMP"
    return f" ⚠ implies ${recon.implied_price:,.2f}/sh vs CMP ({recon.gap:+.1%})"


def _brief_snapshot(exchange: str | None, si: StockInfo | None) -> list[str]:
    """(Brief snapshot) the scalar facts on ONE line — exchange · CMP · cap · 52-wk · shares · book
    value/sh — the linear-markdown mirror of the web key-figures table (CIK moved to Record &
    reproduce: an identifier, not a decision figure). Fail-honest:
    a value with no source is omitted (e.g. AORT has no CIQ Book Value/Share → no book/sh), never
    fabricated; one ↳ names the sources, the per-field source_ref lives in JSON."""
    p = SourceStatus.PRESENT
    parts: list[str] = []
    if exchange:
        parts.append(exchange)
    if si is not None:
        if si.price.status is p and si.price.value is not None:
            asof = f" ({si.as_of.isoformat()})" if si.as_of is not None else ""
            stale = f" ⚠ {si.price.note}" if si.price.note else ""  # assembly staleness, loud
            parts.append(f"CMP ${si.price.value:,.2f}{asof}{stale}")
        if si.market_cap.status is p and si.market_cap.value is not None:
            # (item 1, clause (e)) The cap comes from the CIQ comps panel and the price from the
            # EOD store. On all 11 committed dossiers those disagree — SMPL least at -2.4%, FUBO
            # worst at -91% — so an unlabelled cap sitting beside a live price reads as though the
            # two describe the same moment. They do not. Label the older one with its own vintage.
            #
            # THE CAP'S OWN as-of, NOT A NEIGHBOUR'S (O3, 2026-08-04). This read `cap_as_of`, which
            # the sole caller fed from `implied_expectations.multiples_as_of` — the MULTIPLES panel.
            # Wrong on 11 of 11: IT rendered a cap as-of 2026-06-25 as 2026-07-27, five weeks shown
            # as three days. The label exists to disclose the gap between a frozen cap and a live
            # price, and naming the wrong object concealed precisely that. `market_cap_as_of` is now
            # carried structurally from the same derivation that stamps the cap's source_ref.
            #
            # NO DATE beats a WRONG date: a dossier assembled before the field existed has no cap
            # vintage to state, so it prints none rather than falling back to the neighbour.
            cap_iso = si.market_cap_as_of.isoformat() if si.market_cap_as_of is not None else ""
            si_iso = si.as_of.isoformat() if si.as_of is not None else ""
            cap_v = f" ({cap_iso})" if cap_iso and cap_iso != si_iso else ""
            parts.append(f"cap {_fmt_cap(si.market_cap.value)}{cap_v}{_cap_drift(si)}")
        if (si.low_52w.status is p and si.low_52w.value is not None
                and si.high_52w.status is p and si.high_52w.value is not None):
            parts.append(f"52-wk ${si.low_52w.value:,.2f}–${si.high_52w.value:,.2f}")
        if si.shares_out.status is p and si.shares_out.value is not None:
            parts.append(f"shares {_fmt_shares(si.shares_out.value)}")
        if si.book_value_ps.status is p and si.book_value_ps.value is not None:
            parts.append(f"book value/sh ${si.book_value_ps.value:,.2f}")
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


_BRIEF_FY = 4  # actual fiscal years on the first cut; the Appendix + JSON keep every one



# THE brief's static row set — ONE definition. `assemble._mark_material`/the materiality guard read
# it by import (a second python copy is the duplication class test_parity_pins.py exists for), and
# dossier.js keeps a hand copy pinned against this one because JS cannot import it.
BRIEF_CORE_ROWS = frozenset({
    "Revenue ($M)", "Revenue growth", "EBITDA ($M)", "EBITDA margin",
    "EBIT ($M)", "Net income ($M)", "EPS (GAAP, dil.)", "FCF ($M)",
})

def _brief_window(tbl: Any) -> list[int]:
    """Column indices for the BRIEF's view of the annual table: the last ``_BRIEF_FY`` ACTUAL
    fiscal years + LTM + every consensus column. Curated at the RENDER layer — the record holds
    every exported year (the truncation used to happen at extraction, which put five-plus years of
    actuals beyond recovery). Mirrors briefWindow() in dossier.js."""
    cols = list(tbl.columns)
    est = list(getattr(tbl, "is_estimate", None) or [])

    def is_est(i: int) -> bool:
        return i < len(est) and bool(est[i])

    always = [i for i, c in enumerate(cols) if is_est(i) or str(c).upper().startswith("LTM")]
    actual = [i for i, c in enumerate(cols)
              if not is_est(i) and not str(c).upper().startswith("LTM")]
    return sorted(actual[-_BRIEF_FY:] + always)


def _brief_financials(m: MechanicalLayer) -> list[str]:
    """The financials snapshot — the key income-statement rows over the BRIEF's window (last 4
    fiscal years + LTM + consensus); the full exported history stays in the Appendix and the JSON,
    and the hidden count is stated rather than silently dropped."""
    fs = m.financial_summary
    if fs is None or fs.annual.status is not SourceStatus.PRESENT or fs.annual.value is None:
        return []
    tbl = fs.annual.value
    want = BRIEF_CORE_ROWS
    idx = _brief_window(tbl)
    cols = [tbl.columns[i] for i in idx]
    # (P1 brief fix, 2026-07-28) The whitelist is STATIC LABELS **plus any row flagged material**.
    # Surfacing the writedown into the appendix closed the data half of P1 but not the harm: a
    # brief-only reader still never met a 43%-of-market-cap charge. Not every $2M restructuring
    # line — only rows over the floor, flagged ONCE at assembly (`FinRow.material`); this renderer
    # reads the flag and never recomputes the threshold. Twin: financialSnapshot() in dossier.js.
    rows = [[r.label, *[r.cells[i] for i in idx if i < len(r.cells)]]
            for r in tbl.rows if r.label in want or getattr(r, "material", False)]
    if not rows or not cols:
        return []
    hidden = len(tbl.columns) - len(idx)
    # num_cols are 0-based indices into cols (the period columns) — _table prepends the label cell
    # itself. range(len) right-aligns EVERY period; range(1, len+1) left off column 0 and wasted
    # index len (the first period rendered left-aligned).
    out = _table("Financial snapshot", fs.annual.source_ref, cols, rows,
                 num_cols=frozenset(range(len(cols))))
    if hidden > 0:
        out.append(f"_table shows the last {_BRIEF_FY} fiscal years · {hidden} earlier "
                   f"{'year is' if hidden == 1 else 'years are'} in the Appendix_")
    # MAIN BODY, not an audit tier. This table puts an actual EBITDA column beside a consensus one,
    # and on 7 of 11 committed names those two are not the same basis. A reader who meets the row
    # without the label reads a definitional step as growth — which is the decision, not provenance.
    out += _ebitda_basis_lines(fs)
    return out


def _capital_allocation(m: MechanicalLayer) -> list[str]:
    """Capital created or destroyed, rendered BESIDE the writedown rather than in its own section.

    THE READER'S QUESTION IS "HOW MUCH MORE CAN THEY WRITE DOWN", and that needs the charge and
    the remaining balance ADJACENT. The Financial-snapshot table already surfaces the writedown row
    (it is flagged `material`), so this block follows it directly — split apart they are two facts
    on one page rather than one argument.

    IT MUST NOT READ THE SAME ON A NAME THAT HAS IMPAIRED AND ONE THAT NEVER HAS. SMPL carries a
    charge and a balance; EPAM carries $1.59bn of balance and no charge in four and thirteen years,
    and THAT STALENESS IS THE FINDING — it has never written any of it down. So a name with no
    charge says so in words, naming how old its last tags are, rather than printing a `$0.0M` that
    reads as a measurement of this period.

    EVERY CAVEAT TRAVELS ONTO THE SURFACE, not just into the JSON: the buyback average is labelled
    a fiscal-period average WITH ITS WINDOW, a PERIOD MISMATCH names both spans, and `brand_split`
    prints as a stated gap so the aggregate never reads as complete.
    """
    # GATED PER BLOCK, NOT ON THE FIRST ONE. The section holds TWO independent blocks — the
    # subject's own balance, and the peer comparison — and an early return on `capital_allocation`
    # meant seven names carried `peer_capital_intensity` in their JSON and showed NOTHING on the
    # page. Only the four names that happen to have both rendered it, and those are exactly the
    # four the first verification sampled: checking where it works cannot find this.
    ca = m.capital_allocation
    if (ca is None and m.peer_capital_intensity is None and m.dilution_pipeline is None
            and m.ownership_events is None and m.sbc is None):
        return []
    out: list[str] = ["", "**Capital allocation — created or destroyed**", ""]
    if ca is None:
        return (out + _dilution_pipeline_lines(m) + _ownership_events_lines(m)
                + _sbc_lines(m) + _peer_capital_intensity_lines(m))

    gw, intang = ca.goodwill, ca.intangibles
    if gw.status is SourceStatus.PRESENT or intang.status is SourceStatus.PRESENT:
        left = sum(x.value or 0.0 for x in (gw, intang) if x.status is SourceStatus.PRESENT)
        both = ("goodwill + intangibles"
                if gw.status is SourceStatus.PRESENT and intang.status is SourceStatus.PRESENT
                else ("goodwill" if gw.status is SourceStatus.PRESENT else "intangibles"))
        src = gw if gw.status is SourceStatus.PRESENT else intang
        out.append(f"- **Impairment headroom — {both} remaining:** ${left:,.1f}M"
                   f"{_cite(src.source_ref)}")
    out.append(_fact("Goodwill", gw, lambda v: f"${v:,.1f}M"))
    out.append(_fact("Intangibles (net)", intang, lambda v: f"${v:,.1f}M"))

    # A STALE charge is NOT a current one. The extractor marks it (it holds both dates); this
    # renderer only reads the mark — reconstructing the comparison from a `source_ref` string here
    # would be the divergent-string-parse class.
    charges = (("Goodwill impairment", ca.goodwill_impairment),
               ("Intangible impairment", ca.intangible_impairment))
    live = [(lbl, f) for lbl, f in charges
            if f.status is SourceStatus.PRESENT and f.value
            and not str(f.note or "").startswith("STALE")]
    if live:
        out += [_fact(lbl, f, lambda v: f"${v:,.1f}M") for lbl, f in live]
    else:
        stale = [f for _, f in charges if str(f.note or "").startswith("STALE")]
        tail = (_clean_note(str(stale[0].note)).split("STALE — ")[-1]) if stale else (
            "the filer records no impairment under any tag tried")
        out.append("- **Impairment:** _NONE IN THE CURRENT PERIOD_ — " + tail)

    out.append(_fact("Buyback — cash", ca.buyback_cash, lambda v: f"${v:,.1f}M"))
    out.append(_fact("Buyback — shares repurchased", ca.buyback_shares, lambda v: f"{v:,.0f}"))
    # `_fact` prints a note only when the fact is ABSENT, so a PERIOD MISMATCH on two PRESENT
    # values would be silently dropped — EPAM states cash over 89 days and shares over 364, and
    # printed adjacent they invite exactly the division the average-price guard refuses. Surfaced
    # once, under the pair it describes.
    pair_note = ca.buyback_cash.note or ca.buyback_shares.note or ""
    if "PERIOD MISMATCH" in pair_note:
        out.append("  - ⚠ **PERIOD MISMATCH** — "
                   + _clean_note(pair_note.split("PERIOD MISMATCH —")[-1].strip()))
    avg = ca.buyback_avg_price
    if avg.status is SourceStatus.PRESENT:
        window = str(avg.source_ref).split("(")[-1].rstrip(")")
        line = (f"- **Buyback — average cost/share:** ${avg.value:,.2f} — **fiscal-period average "
                f"over {window}; NOT a purchase price** and not evidence of when they bought"
                f"{_cite(avg.source_ref)}")
        if "PERIOD MISMATCH" in (avg.note or ""):
            line += ("\n  - ⚠ **PERIOD MISMATCH** — "
                     + _clean_note(str(avg.note).split("PERIOD MISMATCH —")[-1].strip()))
        out.append(line)
    else:
        out.append(_fact("Buyback — average cost/share", avg))

    out.append(_fact("Acquisition consideration", ca.acquisition_consideration,
                     lambda v: f"${v:,.1f}M"))
    out += _dilution_pipeline_lines(m)
    out += _ownership_events_lines(m)
    out += _sbc_lines(m)
    gap = _clean_note(str(ca.brand_split.note)).removeprefix("NOT AVAILABLE FROM XBRL — ")
    out.append(f"- **Per-brand split:** _NOT AVAILABLE FROM XBRL_ — {gap}")
    # THE PEER COMPARISON SITS INSIDE THIS BLOCK, not beside it. "Is $1.5bn a lot?" is unanswerable
    # from the balance alone, and a reader who has just met the number should not have to go
    # looking for the only thing that scales it.
    out += _peer_capital_intensity_lines(m)
    return out



def _dilution_pipeline_lines(m: MechanicalLayer) -> list[str]:
    """FORWARD dilution capacity, one MAIN-BODY line — the buyback block's mirror side.

    Renders the composed counts line with its endnote cite. "None on file" prints (it is a stated
    fact about the register); only a None FIELD — a dossier predating the extractor — renders
    nothing, so committed pages are unchanged until their next assembly."""
    dp = m.dilution_pipeline
    if dp is None:
        return []
    return [_fact("Registered offering pipeline (equity/debt not distinguished)", dp.line)]


def _ownership_events_lines(m: MechanicalLayer) -> list[str]:
    """SCHEDULE 13D/G FILING ACTIVITY — one MAIN-BODY line, beside the register it acts on.

    IT REPORTS FILINGS, NOT OWNERSHIP (review of #470). The label said "beneficial ownership" and
    the line said "activist/control", both of which read a CONCLUSION off a form type: a 13D/A can
    disclose an exit as easily as a stake. What the index supports is that a filing of a given
    schedule happened on a date — the reader opens the accession for the rest.

    It sits beside the pipeline line because the two are the same question from opposite sides:
    that one says how many shares COULD be issued, this one says the register is being filed on.

    "No 13D on file" prints — it is a finding about the register, not a blank. Only a None FIELD
    (a dossier predating the extractor) renders nothing, so committed pages are unchanged until
    their next assembly."""
    oe = m.ownership_events
    if oe is None:
        return []
    return [_fact("Schedule 13D/G filing activity", oe.line)]


def _sbc_lines(m: MechanicalLayer) -> list[str]:
    """The ONGOING dilution engine — one MAIN-BODY line, completing the share-register trio.

    THE RATIO IS THE READING, THE DOLLARS ARE THE SCALE, and both come from the SAME window (see
    `SbcLine`). The line prints its period because the ratio is only meaningful as a ratio of a
    stated one — FUBO's FY2024 SBC over a post-merger LTM revenue read 0.7% against a true 2.6%,
    and nothing on the page would have shown which periods were being divided."""
    s = m.sbc
    if s is None:
        return []
    return [_fact("Stock-based compensation", s.line)]


def _peer_capital_intensity_lines(m: MechanicalLayer) -> list[str]:
    """Is this acquired-asset load unusual for the sector, or exactly what it looks like?

    BOTH DENOMINATORS, and the order is the argument. Against TOTAL ASSETS first, because that is
    the comparable property — how acquisitive the balance sheet IS. Against MARKET CAP second and
    labelled, because a cheap stock shows a high ratio on identical accounting: SMPL's 166% is
    partly $1.5bn of goodwill and partly a market cap that halved, so reading it alone would
    measure the de-rating the thesis argues is an overshoot.

    THE MEDIAN IS GIVEN TWICE — all peers, and peers above a STATED size floor. The set spans $49M
    to $30.1bn and a $49M distressed name's ratio-to-market-cap (HAIN, 950%) is a de-rating
    artifact, not a statement about its balance sheet.
    """
    pc = m.peer_capital_intensity
    if pc is None or not pc.rows:
        return []
    def pct(v: float | None) -> str:
        return "—" if v is None else f"{v * 100:.0f}%"

    def usd(v: float | None) -> str:
        return "—" if v is None else f"{v:,.0f}"
    # The reason column exists ONLY when a row has one — an always-present empty column bolds to
    # `****` on the subject row and reads as a missing value rather than an absent concept.
    noted = any(r.note for r in pc.rows)
    cols = (["mcap $M", "acquired $M", "assets $M", "% assets", "% mcap"]
            + (["why"] if noted else []))
    rows = [[r.ticker, usd(r.market_cap), usd(r.acquired), usd(r.total_assets),
             pct(r.pct_assets), pct(r.pct_market_cap)]
            # "—" not "" — `name_rows` bolds every cell in the subject row, and an empty
            # one renders as a bare `****` that reads as a missing value.
            + ([(r.note or "—").split(" — ")[0]] if noted else [])
            for r in pc.rows]
    out = _table("Peer acquired-asset intensity — goodwill + intangibles",
                 "EDGAR companyfacts (Goodwill, intangibles, Assets) · peer set + market caps from "
                 "the CIQ comps grid",
                 cols, rows, num_cols=frozenset(range(5)),
                 name_rows=frozenset(i for i, x in enumerate(pc.rows) if x.is_subject))
    out.append(
        f"- **Median — all peers (n={pc.n_all}):** {pct(pc.median_all_assets)} of assets · "
        f"{pct(pc.median_all_market_cap)} of market cap")
    out.append(
        f"- **Median — peers ≥ ${pc.size_floor:,.0f}M market cap (n={pc.n_large}):** "
        f"{pct(pc.median_large_assets)} of assets · "
        f"{pct(pc.median_large_market_cap)} of market cap")
    out.append(
        "- _Read the ASSETS column for the peer judgement — it measures how acquisitive the "
        "balance sheet is. The market-cap column sizes the exposure but moves with the price, so "
        "a de-rated name shows a high ratio on unchanged accounting._")
    return out + _peer_impairment_lines(pc)


def _peer_impairment_lines(pc: Any) -> list[str]:
    """Does the sector WRITE DOWN what it carries — the half the balance columns cannot answer.

    THE BASE RATE IS THE DECISION VALUE, so it leads. SMPL carrying 73% of assets against a 57.6%
    median settles that the LOAD is ordinary; it says nothing about whether the sector marks that
    load down, and the same charge means opposite things against a sector that impairs routinely
    and one that never does (STATE.md §M3).

    THE DENOMINATOR IS THE ASSESSED SET, NOT THE PEER SET, and the difference is the finding.
    A peer with no annual observation in the window (CPB — four charges FY2013-FY2018, none since)
    was not measured, and counting it as a clean year would manufacture the reassuring answer out
    of an absence.

    THE LIVE COLUMN IS NOT THE WINDOW COLUMN. A year-to-date charge is excluded from the window
    total by the annual rule that makes that total summable — SMPL's window figure is the $60.9M
    FY2025 charge while its live year-to-date is $369.0M, a 6x gap between two numbers a reader
    would otherwise take for the same quantity. The column is labelled, not merged.
    """
    have = [r for r in pc.rows if r.impairment is not None]
    if not have:
        return []

    def pct(v: float | None) -> str:
        return "—" if v is None else f"{v * 100:.0f}%"

    def usd(v: float | None) -> str:
        return "—" if v is None else f"{v:,.0f}"

    rows = []
    for r in have:
        i = r.impairment
        last = (f"{i.last_charge_end} (${i.last_charge_amount:,.0f}M)"
                if i.last_charge_end is not None else "never")
        rows.append([r.ticker, i.state_label or i.state,
                     f"{i.charged_years} of {i.observations}" if i.observations else "—",
                     usd(i.total), pct(i.pct_acquired), last, usd(i.pending)])
    out = _table(
        f"Peer write-down history — did they MARK DOWN what they carry? "
        f"(trailing {pc.imp_window_years} fiscal years)",
        "EDGAR companyfacts, ANNUAL durations only (goodwill + intangible impairment families) · "
        "each row's window ends at that filer's own balance date",
        ["state", "yrs charged", "window $M", "% acquired", "last charge (any date)",
         "live YTD $M"],
        rows, num_cols=frozenset({3, 4, 6}),
        name_rows=frozenset(i for i, x in enumerate(have) if x.is_subject))
    if pc.imp_n_large_assessed:
        out.append(
            f"- **Base rate — {pc.imp_n_large_charged} of {pc.imp_n_large_assessed} large peers "
            f"ASSESSED over the window took a charge**, median {pct(pc.imp_median_large_pct)} of "
            f"acquired assets among those that did. The denominator counts only peers with an "
            f"annual observation in the window — a name with none was not measured, and is not a "
            f"clean year.")
    out.append(
        "- _`reports nil` is a MEASUREMENT — the filer tags impairment and states zero. "
        "`no annual obs.` and `does not tag` are not measurements and must not be read as clean "
        "years. The **live YTD** column is excluded from the window total: a year-to-date charge "
        "is not an annual one, and the two are different quantities._")
    return out


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


def _underwrite_lines(card: ScenarioRecord | None) -> list[str]:
    """(md/web parity) The UNDERWRITE layer on the markdown Brief — the analyst's thesis, the
    at-a-glance economics, and the bear/base/bull table.

    Until now this rendered ONLY on the web: the scenario record is a separate committed artifact
    (``scenarios/<TICKER>.json``) that this renderer never read, so an exported .md silently
    dropped the thesis, the target, the reward:risk and every scenario — exactly what the buy-side
    cover leads with. The record is passed IN (never loaded here): a runtime import of
    ``vinci.scenarios`` would cycle back into ``vinci.dossier.midcycle``.

    Assemble-not-conclude holds: every number below is the analyst's own recorded input or plain
    arithmetic already computed in the record — this function derives no new judgment. Absent
    record → no section at all (byte-identity for un-underwritten names)."""
    if card is None:
        return []
    r, v = card.result, card.verdict
    out: list[str] = []
    per = r.per_scenario or {}
    base = per.get("base")
    spot = card.spot
    # the stat strip — target (base value/share), spot, reward, risk, ratio
    strip: list[str] = []
    if base is not None and base.value_per_share is not None:
        vps = base.value_per_share
        upside = (vps / spot - 1.0) if spot else None
        # (item 1e) "vs spot" is against the FROZEN entry-vintage spot below, never the live close
        # that leads this page. SMPL rendered "+130.2% vs spot" off $10.53 while the page's own CMP
        # read $10.22 — two prices, one label, and nothing telling the reader which was which.
        strip.append(f"**Target (base)** ${vps:,.2f}"
                     + (f" ({upside:+.1%} vs entry-vintage spot)" if upside is not None else ""))
    # (item 1e) "FROZEN AT UNDERWRITE <date>", never "underwritten <date>" as if it dated the
    # price. `underwrite_date` is when the call was frozen; the close it was struck on is 1-5 days
    # OLDER on all 6 committed records (SMPL's 10.53 is a 07-22 close under a 07-27 underwrite
    # date). The old wording is audit P4 verbatim — "the page asserts 'underwritten 2026-07-27'
    # over a 07-22 price" — and it survived into the fix meant to close P4.
    #
    # The struck date is NOT structurally available: `ScenarioRecord` has `spot` and `spot_source`
    # and no `spot_as_of`, and the date lives inside analyst free text phrased differently per
    # record. Parsing it out would be the banned display-string parse, so the source line below
    # carries it VERBATIM instead, and a structured `spot_as_of` is queued as the real fix.
    strip.append(f"**Spot** ${spot:,.2f} (entry-vintage — frozen at underwrite "
                 f"{card.underwrite_date})")
    if r.reward is not None:
        strip.append(f"**Reward** ${r.reward:,.2f}")
    if r.risk is not None:
        strip.append(f"**Risk** ${r.risk:,.2f}")
    if r.ratio is not None:
        strip.append(f"**Reward : risk** {r.ratio:,.2f} : 1 (bar {r.bar:g} : 1)")
    elif r.ratio_undefined:
        strip.append("**Reward : risk** UNDEFINED")
    # (2026-08-05) THE SECOND TEST, BESIDE THE FIRST — not below it, not in the appendix. The house
    # convention is nominal 2:1 AND a base-case IRR floor AND a stated horizon; an IRR that renders
    # somewhere else reads as a diagnostic, and this one is a GATE. A record with no horizon says
    # so rather than omitting the line, because a silently absent IRR is indistinguishable from one
    # that passed. `horizon_years` is printed with it: the return is meaningless without the period
    # it is earned over, and printing a rate beside no date is how a 5-year story gets compared
    # against a price paid today (the same error the R2 PV/nominal split exists to prevent).
    if getattr(r, "irr", None) is not None:
        yrs = f", {r.horizon_years:g}y" if r.horizon_years else ""
        strip.append(f"**Base IRR** {r.irr:.1%} (floor {r.irr_floor:.0%}{yrs})")
    elif getattr(r, "irr_undefined", None):
        strip.append(f"**Base IRR** UNDEFINED — {r.irr_undefined}")
    if getattr(r, "gate", None):
        strip.append(f"**Gate** {r.gate} (both tests)")
    out += [" · ".join(strip), ""]
    # THE TIERED LADDER (2026-08-21) — a second strip line, present only on new-regime records.
    # A record without `gate_regime` was judged under the 2:1/15% booleans alone, and the page
    # SAYS so: absence must not read as the new labels having been applied and passed. Labels are
    # humanised from the enum values once, here (the JS card mirrors them — uw-card.js).
    if getattr(r, "gate_regime", None):
        _tl = {"poor": "poor (<1:1)", "below_target": "below target", "target_met": "target met",
               "preferred": "preferred", "fails": "fails", "minimum_met": "minimum met",
               "undefined": "UNDEFINED"}
        tier_bits = [f"**Asymmetry** {_tl.get(r.asymmetry_tier or 'undefined', r.asymmetry_tier)}",
                     f"**Return** {_tl.get(r.return_tier or 'undefined', r.return_tier)}"]
        # THE THRESHOLDS ARE FORMATTED ONLY IF THEY EXIST. `gate_regime` does NOT imply them:
        # `scenario-supersede` writes the incoming payload's `result` VERBATIM (pinned in
        # test_tiered_gates), so a hand-authored payload can carry a regime stamp beside null
        # thresholds. Formatting those raised `TypeError: unsupported format string passed to
        # NoneType.__format__` and took the WHOLE md/PDF render down with it — a crash in the
        # export, from a record shape a supported command can produce (review, #489).
        _lines = (f"≥{r.eligible_ratio:g}:1 & ≥{r.eligible_irr:.0%}"
                  if r.eligible_ratio is not None and r.eligible_irr is not None else None)
        if r.eligible is True:
            el = f"ELIGIBLE ({_lines})" if _lines else "ELIGIBLE (thresholds unstated)"
        elif r.eligible is False:
            el = (f"BELOW ELIGIBILITY (needs {_lines})" if _lines
                  else "BELOW ELIGIBILITY (thresholds unstated)")
        else:
            el = f"eligibility UNDEFINED — {r.eligible_undefined or 'input missing'}"
        tier_bits.append(f"**Eligibility** {el}")
        out += [" · ".join(tier_bits),
                f"_gate regime {r.gate_regime} · IRR {r.irr_convention or 'convention unstated'}_",
                ""]
    elif getattr(r, "gate", None):
        out += ["_judged under the 2:1 / 15% regime (pre-2026-08-21; tiers not applied)_", ""]
    # (item 1e) THE SPOT'S PROVENANCE, verbatim — the only place the price's OWN date reaches a
    # print reader. The web has carried it since the masthead redesign, as the `[S1]` cite beside
    # the value; the md rendered it NOWHERE, so the export could state a frozen price with no way
    # to learn when it was struck. Printed as recorded and never parsed: it is analyst free text
    # ("Polygon daily aggregate close 2026-07-22 (store; latest bar at reissue)"), and reading a
    # date out of it to compose a stamp is precisely the display-string parse the repo forbids.
    if card.spot_source:
        out += [f"_Spot source: {card.spot_source}_", ""]
    if v.status:
        # DISPOSITION, not the verdict: `status` is confirm/override against the machine proposal.
        # The BUY/AVOID verdict of record lives in the append-only ledger, which this package does
        # not import (the structural no-verdict line) — labelling it "verdict" here would blur the
        # two exact things the pivot keeps separate.
        rec = f" ({v.recorded})" if v.recorded else ""
        entry = f" · entry ${v.entry_price:,.2f} (entry-vintage)" if v.entry_price is not None \
            else ""
        out += [f"**Underwrite disposition:** {v.status.upper()}{rec}{entry} — "
                f"_the BUY/AVOID verdict of record is the ledger's_", ""]
        # (item 22, VISIBLE-ABSENCE RULE) This renderer CANNOT express the ledger: the underwrite
        # record is the only artifact it reads, and the render package deliberately does not import
        # the ledger — that isolation is what stops the machine asserting verdicts, and it is load-
        # bearing. So the gap is DECLARED rather than closed here. SMPL showed `WATCH` + "not held"
        # with no trace that a BUY had existed and been closed, and a reader could not detect they
        # were seeing a partial view — not incomplete, MISLEADING.
        #
        # Deliberately names NO DATE. An earlier draft of this line read "prior BUY closed 07-24",
        # which this function has no way to obtain; a render that invents the fact it just admitted
        # it cannot reach is worse than the silence it replaces.
        out += ["> **Not shown here:** any prior position, close or realized return for this name. "
                "This surface reads the underwrite record only — the ledger is the record of "
                "positions. **See the Decision log.**", ""]
    # the THESIS — the analyst's own words, never machine text. ONE field since 2026-07-22:
    # `rationale` is canonical, `rationale_plain` deprecated and read by nothing (vinci/seal.py).
    thesis = v.rationale
    if thesis:
        # (item 1e) the rationale is SEALED analyst text and is never edited — so where it quotes a
        # price ("WATCH at $10.53 — not held"), the vintage is supplied AROUND it. Labelled, not
        # corrected: the entry-vintage number is the reference frame the call was made in, and
        # rewriting it would falsify the record rather than date it.
        #
        # It points at "Snapshot" because that is what the MARKDOWN calls the block carrying the
        # live close (`- **Snapshot:** … CMP $10.22 (2026-07-24) …`). The first cut said "Key
        # figures", which is the WEB's heading and appears nowhere in the md — a pointer to a
        # section that does not exist, in the batch whose subject is false claims about the page.
        out += ["### Thesis — our rationale",
                # THE DATE THE PRICES WERE STRUCK, not the date the underwrite was written
                # (2026-09-01). "entry-vintage" is the right WORD — these are the frozen spot's
                # prices, as `vs entry-vintage spot` says two tables down — but the date beside it
                # was `underwrite_date`, when the analyst WROTE the underwrite. `spot_as_of` is
                # when the quoted price closed. They differ on EVERY committed record: a day or
                # two normally, seventeen on a reissue, so the stamp has always named a date none
                # of the prices below it belong to. Falls back to `underwrite_date` for the two
                # records stating no `spot_as_of`, where it is the only date there is.
                f"_Prices quoted below are entry-vintage "
                f"({card.spot_as_of or card.underwrite_date}); "
                f"the live close is in Snapshot, above._", "", thesis, ""]
    # (item 22 / audit N7) what would REOPEN the name. Recorded on every watch record — 16 triggers
    # across 6 names — rendered on the web card and, until now, nowhere in the md. A trigger the
    # reader never sees cannot do the job it was written for. Placed AFTER the rationale to match
    # the web card's order (rationale → host extras → trigger chips): the twins are allowed to LAG
    # each other, but a reader comparing them should not meet the same two blocks in two orders.
    if v.reunderwrite_triggers:
        out += ["### What would reopen this name", ""]
        out += [f"- {t}" for t in v.reunderwrite_triggers]
        out.append("")
    return out


def _scenario_table_lines(card: ScenarioRecord | None) -> list[str]:
    """(md/web parity) The bear/base/bull table + each scenario's recorded REASON — the web's
    'Scenario analysis' card. The assumptions ARE the argument on the buy side, so the reasons
    render beside the arithmetic rather than as hidden metadata. Analyst inputs and the record's
    own computed value/share only — no new derivation."""
    if card is None:
        return []
    per = card.result.per_scenario or {}
    spot = card.spot
    rows: list[str] = []
    any_eps = any(x.eps is not None for x in card.scenarios.values())
    # ...AND THE COLUMNS THEMSELVES GO, not just their cells (2026-09-01). The `—` treatment below
    # was the right call for an R2 leg that omits ONE driver inside an otherwise-full table; it is
    # the wrong one for R3, where NEITHER revenue nor margin exists and the row read
    # "| — | $15.388 | — | 20.5x |" — two empty columns flanking the only number that produced the
    # value. Same rule as the EPS column and the card's leg rows: a column appears when the record
    # carries its number. R1/R2 legs always carry both, so their tables stay byte-identical.
    any_rev = any(x.revenue is not None for x in card.scenarios.values())
    any_marg = any(x.margin is not None for x in card.scenarios.values())
    for nm in ("bear", "base", "bull"):
        s = card.scenarios.get(nm)
        p = per.get(nm)
        if s is None or p is None:
            continue
        vps = p.value_per_share
        vs = f"{vps / spot - 1.0:+.1%}" if (vps is not None and spot) else "—"
        # margin is OPTIONAL by design: an R2 EV/Revenue leg applies its multiple to revenue and
        # never reads a margin, so the record omits one rather than fabricating a driver the
        # arithmetic ignores. Render the absence as "—" — never format None, never invent 0%.
        marg = "—" if s.margin is None else f"{s.margin:.1%}"
        # REVENUE IS OPTIONAL FOR THE SAME REASON MARGIN IS (review of #542). An R3 leg values a
        # share as EPS × multiple and carries no revenue at all, so the first cut printed
        # "$0M revenue → $397.41/share" — a fabricated driver next to a real value. The EPS column
        # appears only when some leg has one, so R1/R2 tables stay byte-identical.
        rev_cell = (f" {'—' if s.revenue is None else f'{s.revenue:,.0f}'} |") if any_rev else ""
        marg_cell = f" {marg} |" if any_marg else ""
        eps_cell = (f" {'—' if s.eps is None else f'${s.eps:,.3f}'} |") if any_eps else ""
        rows.append(f"| {nm} |{rev_cell}{eps_cell}{marg_cell} {s.multiple:g}x | "
                    f"{'—' if vps is None else f'${vps:,.2f}'} | {vs} |")
    if not rows:
        return []
    # (item 1e) the % column is computed against the record's FROZEN spot, not the live close that
    # leads this page — so the header names the BASIS. It deliberately does NOT carry
    # `underwrite_date`: that is the freeze date, not the date the price was struck, and stamping
    # it here would assert a vintage the record cannot support (see `_underwrite_lines`).
    rev_head, rev_rule = (" revenue $M |", " ---: |") if any_rev else ("", "")
    eps_head, eps_rule = (" EPS |", " ---: |") if any_eps else ("", "")
    marg_head, marg_rule = (" margin |", " ---: |") if any_marg else ("", "")
    out = [f"_{card.recipe_desc}_", "",
           f"| scenario |{rev_head}{eps_head}{marg_head} multiple | value / sh | "
           "vs entry-vintage spot |",
           f"| --- |{rev_rule}{eps_rule}{marg_rule} ---: | ---: | ---: |", *rows, ""]
    for nm in ("bear", "base", "bull"):
        s = card.scenarios.get(nm)
        if s is not None and s.reason:
            out.append(f"- **{nm}** — {s.reason}")
    out.append("")
    return out + _scenario_input_lines(card)


def _scenario_input_lines(card: ScenarioRecord) -> list[str]:
    """(item 28) The RECORDED INPUTS behind the grid, printed on the same page as the grid.

    ORIGIN: the 13-part audit could not reproduce a single scenario cell from anything the dossier
    printed. The auditor solved the system backwards and landed on 93.77M shares against our
    recorded 93.677801M — a 0.1% miss, and the miss IS the finding: the inputs were recoverable
    only by inference. They were in ``ScenarioRecord.facts`` the whole time, source-stamped, and
    this renderer never printed them.

    Prints EVERY recorded fact rather than a fixed shares/D&A/net-debt trio, because the trio is
    recipe-specific: R1 records carry an absolute D&A figure, R2 records carry a D&A RATIO plus a
    share-growth term (and a burn-to-breakeven on MVST). A hardcoded three would print blanks on
    half the corpus and silently omit the inputs that actually drive the other half.
    (Those field names are spelled in prose deliberately. The twin-parity pin does a bare-token
    search across the two renderers, so a key named only in a COMMENT here registers as a
    one-sided field and reds a check this block has nothing to do with.)

    Distinct from item 24, which is the shares-BASIS policy question: this discloses whatever basis
    was chosen, and says which one it was."""
    # THE FORMULA IS NOT A FACT, AND THE EARLY RETURN CONFLATED THEM (review of #542). This
    # returned on empty `facts` — reasonable while every recipe had some — but R3 records carry
    # NONE BY CONSTRUCTION: `_run_r3` refuses the enterprise facts outright, because a P/E multiple
    # already values equity. So the one recipe whose arithmetic a reader is least likely to guess
    # was the one whose stamped chain never printed. Return only when there is nothing at all.
    if not card.facts and not card.recipe_formula:
        return []

    def num(v: float) -> str:
        """Full recorded precision, trailing zeros stripped. NOT ``%g``: at 6 significant digits
        it renders 93.677801 as 93.6778, and this block exists because an auditor back-solved
        93.77 against that very number — printing a rounded input would reproduce the defect in
        smaller type."""
        return f"{v:,.6f}".rstrip("0").rstrip(".")

    rows = [f"| {name.replace('_', ' ')} | {num(f.value)} {f.unit} | {f.basis} | {f.source} |"
            for name, f in card.facts.items()]
    out: list[str] = []
    if rows:
        out = ["**Scenario inputs** — every value in the grid recomputes from these.", "",
               "| input | value | basis | source |",
               "| --- | ---: | --- | --- |", *rows, ""]
    elif card.recipe_formula:
        # A recipe with no record-level facts still has a chain worth printing, and saying WHY
        # there are none is the point: a blank table would read as an omission.
        out = ["**Scenario inputs** — this recipe reads no record-level facts; each leg carries "
               "its own inputs, and the chain below is how they combine.", ""]
    # THE CHAIN, not just the numbers. `recipe_formula` is stamped onto the record by `run_recipe`
    # and was rendered by NOTHING — so a reader with the inputs still had to guess how they
    # combine. That guess is not hypothetical: verifying this very block, the D&A add-back was
    # omitted and the base leg recomputed to $21.38 against a recorded $24.24. Inputs without the
    # chain are still a system to be solved backwards, which is the audit's original complaint.
    if card.recipe_formula:
        out += [f"_Chain ({card.multiple_basis}):_ "
                + " → ".join(card.recipe_formula), ""]
    return out


# The one-line method gloss for R1 — the web spells the recipe out rather than printing its slug,
# and the print twin must say the SAME words (a reader comparing the two reads one method, not two).
_SCREEN_METHOD_R1 = "mid-cycle margin × the median multiple of its own history"
_SCREEN_SUBTITLE = (
    "A mechanical re-rate to the median multiple of this name's own trading history, on its naive "
    "reported median margin. An attention filter only — it applies no structural adjustment, so a "
    "cheap-looking screen still has to survive the full bear/base/bull underwrite.")


def _screening_context_lines(anchor: Anchor | None) -> list[str]:
    """(md/web parity) The screening ANCHOR — how this name surfaced. Twin of anchorInner() in
    frontend dossier.js, which renders it for every name; this renderer rendered it for NONE, so
    the level that put the name in the funnel was missing from every committed ``dossier.md``.
    That loss is total on the five names carrying no scenario card, where this is the only
    valuation LEVEL in the document (``Valuation — first cut`` is relative-only by the
    ImpliedValuation fence).

    WHO actually lost it: the ``Full dossier MD`` download and the committed ``.md`` record. NOT
    the PDF — the download menu's PDF scopes are ``window.print()`` on the WEB page, which has
    always drawn anchorInner. The first write-up of this fix said "every PDF omitted it" and that
    was wrong; corrected after a live preview.

    HARD FENCE, same as the web: the base value renders as a LEVEL and is labelled
    spot-independent. No %, delta, discount or upside against spot is computed here — differencing
    it against the price is exactly the machine-implied upside the fence forbids.

    An INAPPLICABLE anchor still renders: ``reason`` is the diagnostic telling the human WHY there
    is no screen value (a failed coherence guard, a missing own-history multiple), and suppressing
    it would hide a known gap behind an empty section."""
    if anchor is None:
        return []
    method = (_SCREEN_METHOD_R1 if anchor.recipe_hint.startswith("R1")
              else (anchor.recipe_hint or "—"))
    rows = [f"| Method | {_md_cell(method)} | "
            f"{'applicable' if anchor.applicable else 'NOT applicable'} |"]
    mg, mu = anchor.margin, anchor.multiple
    if mg is not None:
        rows.append(f"| Mid-cycle margin | {'—' if mg.value is None else f'{mg.value * 100:.1f}%'} "
                    f"| {mg.anchor_years}y history · {mg.confidence} |")
    if mu is not None:
        rows.append(f"| Median multiple, own history | "
                    f"{'—' if mu.value is None else f'{mu.value:.1f}x'} | "
                    f"{mu.history_quarters} closes · {mu.confidence} · "
                    f"{_md_cell(anchor.multiple_basis)} |")
    base = anchor.anchor_base_value_per_share
    if base is not None:
        ev = anchor.anchor_ev_ebit
        rows.append(f"| Screen value / share | ${base:,.2f} | spot-independent · "
                    f"EV/EBIT {'—' if ev is None else f'{ev:.1f}'}x |")
    rows.append(f"| Overall confidence | {anchor.overall_confidence or '—'} |  |")
    out = ["### Screening context — how this name surfaced — _not a verdict_", "",
           f"_{_SCREEN_SUBTITLE}_", "",
           "| input | value | basis |", "| --- | ---: | --- |", *rows, ""]
    # the sentence is written ONCE, in vinci/dossier/anchor.py — both renderers print it verbatim
    if anchor.midcycle_gap is not None:
        out += [f"**Mid-cycle assumption under strain.** {anchor.midcycle_gap.read}", ""]
    if anchor.data_quality:
        out.append(f"**data_quality: {anchor.data_quality}**")
        out += [f"- {x}" for x in anchor.data_quality_detail]
        out.append("")
    if anchor.reason:
        out += [f"_{anchor.reason}_", ""]
    return out


def _brief_lines(d: Dossier, *, show_proposal: bool = False,
                 card: ScenarioRecord | None = None) -> list[str]:
    """(Brief · tier redesign 2026-07-21) the IC one-pager, SIX decision-ordered sections —
    decision strip → company snapshot → what happened → the case → financial snapshot → valuation
    first-cut. Everything needed to decide PASS vs READ DEEPER, nothing else. The machine's
    proposed verdict is DERIVED + sealed at assembly and NOT shown before the human logs theirs
    (``show_proposal=False``, the default — anti-anchoring); it rides as the assessment line's
    suffix, never a standing row (the proposal is a deterministic mapping of that same lean, so a
    second row was the same fact twice). The old "Recommendation / Target" slot is gone — the
    verdict of record is a ledger concern and renders where the ledger is displayed. Mirrors
    briefTier() in frontend dossier.js (the web additionally leads with the underwrite card, a
    separate committed artifact this renderer does not read)."""
    m = d.mechanical
    s = d.synthesis
    out: list[str] = ["# Brief — first cut", ""]
    # 1 — "At a glance" (card-split mirror): the machine's ASSESSMENT (no proposal here — user
    # decision), the CONDITIONAL warning line, and the company identity in one opening section.
    # (The web opener additionally leads with the underwrite masthead, a separate committed
    # artifact this renderer does not read.)
    out.append("## At a glance")
    # (md/web parity) the UNDERWRITE layer leads the glance when the name has a recorded card:
    # economics strip → verdict of record → the analyst's thesis. Absent card → unchanged.
    out += _underwrite_lines(card)
    vf = _brief_verify_first(d.caveats)
    if vf:
        out += ["> ⚠ **Verify before the verdict:** " + "; ".join(vf)
                + " — full caveats in Analysis.", ""]
    bd = d.business_description
    if bd is not None and bd.status is SourceStatus.PRESENT and bd.value is not None:
        out.append(_brief_oneliner(bd.value))
    # the NARRATIVE slot sits above Segments (mirrors the web opener). AUTHORSHIP: a logged name
    # leads with the analyst's THESIS (rendered by _underwrite_lines above) and the machine read
    # is suppressed — the human's words are the verdict of record, and two voices in one slot
    # blurs which is which. A pending name keeps the machine assessment, never titled a thesis.
    has_thesis = card is not None and bool(card.verdict.rationale)
    if s is not None and s.evidence_balance and not has_thesis:
        out.append(_machine_read_md(s.evidence_balance))
    if m.concentration is not None:
        out += [_fact("Segments", m.concentration.segments),
                _fact("Geography", m.concentration.geographic)]
    cc = _customer_concentration(m)
    if cc is not None:
        out.append(cc)
    snap = _brief_snapshot(d.exchange, m.stock_info)
    if snap:
        out += snap
    # (buy-side cover) THE CRUX closes the cover — the decisive question ONLY, plus an honest
    # count-pointer to the unknowns. The former `key_unknowns[:2]` teaser was REMOVED (2026-07-24,
    # weather audit): across 109 consecutive historical draw pairs the unknowns' SET survives only
    # 17% and the top-2 slots ~7% — the teaser presented weather-rolled prose as a curated "top-2
    # that would change our mind", a judgment the machine never made. The QUESTION's subject is
    # draw-stable; the full unknown list lives in Analysis. Mirrors cruxInner() on the web.
    if s is not None and s.decisive_question is not None and s.decisive_question.question:
        out += ["", "**The crux — what decides this, and what would change our mind**",
                f"**{s.decisive_question.question}**"]
        n_unk = len(s.key_unknowns)
        out.append(f"_{n_unk} key unknown{'s' if n_unk != 1 else ''} + the evidence for/against "
                   "— in Analysis_")
        # (catalyst calendar) ONE line: the earliest upcoming dated event — when the crux next
        # gets tested. Rendered only when a dated entry exists; twin: cruxInner() on the web.
        upcoming = _calendar_entries(d, card)
        if upcoming:
            date_s, event, basis, _tests, _src = upcoming[0]
            out.append(f"**Next catalyst:** {event} ~{date_s} `[{basis}]` — calendar in Analysis")
    out.append("")
    # (user decision) the standing machine-proposal line is GONE from the default brief — the
    # pivot MECHANISM is untouched (derived + sealed to the shadow ledger at assembly; disposition
    # recorded at log time; the ledger CLI reveals post-log). ``--show-proposal`` is the operator's
    # explicit peek and still renders the proposal, under its own section header.
    # (brief re-order 2026-07-27) WHAT HAPPENED now precedes the scenario grid: the reader
    # met the valuation before the problem it values. Setup, then what it's worth.
    # 3 — WHAT HAPPENED: the drawdown shape + the decision tiles. The Brief used to show the raw
    # drawdown % with no WHY; the fund's whole question (overshoot vs terminal) starts from what
    # broke. Full event log + filings stay in Analysis.
    # (content relocation 2026-07-24) TITLE, not composition. The section carries the event (shape,
    # 180d, idio) AND survival triage (net debt/EBITDA, FCF sign, going concern). Keeping those
    # adjacent is right — overshoot-vs-terminal is the fund's whole question and survival is its
    # discriminator — but "What happened" described only the first half.
    out.append(f"## {BY_KEY[d.sleeve].survive_heading}")
    if m.drawdown_cause is not None:
        out.append(_fact("Shape", m.drawdown_cause.shape, _fmt_shape))
    io = m.idiosyncratic_vs_shared
    if io is not None and io.name_180d_return.status is SourceStatus.PRESENT:
        out.append(_fact("Price (180d)", io.name_180d_return, _pct))
    # (buy-side what-happened, twins the web strip) the market leg + the idio read join the
    # comparison — same declutter-P1 suppression as the Analysis section
    if io is not None and (io.market_180d_return.status is SourceStatus.PRESENT
                           or io.rel_vs_market.status is not SourceStatus.PRESENT):
        out.append(_fact(f"Market ({io.benchmark_symbol}) 180d", io.market_180d_return, _pct))
    if io is not None:
        out.append(_fact("vs market (180d)", io.rel_vs_market, _pct))
    if io is not None and io.read.status is SourceStatus.PRESENT:
        out.append(_fact("Read", io.read))
    if m.quality is not None:
        out += [_fact("Net debt / EBITDA", m.quality.net_debt_to_ebitda, _mult),
                _fact("Free cash flow", m.quality.fcf_sign, _signword)]
    gc = _going_concern_brief(m)
    if gc is not None:
        out.append(gc)
    out.append("")
    # SCENARIO ANALYSIS — the recorded bear/base/bull table (+ reasons); the sealed machine
    # proposal joins it only under the operator's explicit --show-proposal peek.
    scen = _scenario_table_lines(card)
    # The SCREENING ANCHOR closes the section in both twins (underwriteDetail() appends it after
    # the card detail, and renders the section on the anchor ALONE when no card exists — with the
    # absence stated rather than the section vanishing). The markdown twin now does the same: a
    # shorter document is not a substitute for saying "this name has not been underwritten".
    screen = _screening_context_lines(d.anchor)
    if scen or screen or show_proposal:
        out.append("## Scenario analysis")
        if not scen and screen:
            out += ["_no scenario record for this name_", ""]
        out += scen
        if show_proposal:
            out += [_machine_proposal_md(
                derive_proposal(s.evidence_balance if s is not None else None,
                                sleeve=d.sleeve,
                                draws_unanimous=(s.draw_agreement.unanimous
                                                 if s is not None and s.draw_agreement else None))),
                ""]
        out += screen
    # 4 — THE CASE: the condensed bull/bear alone — the decisive question + unknowns moved to the
    # cover's CRUX block (buy-side cover), so the question renders once per tier.
    out.append("## The case")
    out += _brief_case_lines(s, d.mechanical, sleeve=d.sleeve)
    # 5 — FINANCIAL SNAPSHOT: the compact table. The per-period return-ratios table moved to the
    # Analysis trajectory section (the web keeps its exhibit here; markdown has no chart).
    out.append("## Financial snapshot")
    out += _brief_financials(m)
    # BESIDE THE WRITEDOWN, deliberately. The snapshot's `material` rows carry the impairment
    # CHARGE; the block below carries what is LEFT to impair. The reader's question spans both, so
    # a separate section would make them two facts on one page instead of one argument.
    out += _capital_allocation(m)
    if (m.return_ratios is None or m.return_ratios.status is not SourceStatus.PRESENT) \
            and m.key_ratios is not None:
        out.append(_fact("Key ratios (latest)", m.key_ratios))
    out.append("")
    # 6 — VALUATION, FIRST CUT: the trailing-range read + peers + ONE consensus line (enough to
    # know whether the view is variant). The forward-multiple ladder lives in Analysis only; the
    # implied-equity table in the Appendix only.
    out.append("## Valuation — first cut")
    if m.valuation is not None:
        out += [_fact("vs own trading history", m.valuation.range_position),
                _fact("vs peers", m.valuation.cross_sectional)]
        # FORWARD multiples, each naming the column its denominator came from. MAIN BODY, not
        # audit: this is a decision value, and it is the row whose absence sent a real underwrite
        # outside the dossier for a multiple with no stated basis. Printing the basis beside the
        # number is the entire point — two of these can never be silently compared across periods.
        # APPEND ONLY WHEN THERE IS A LINE. Both helpers return "" where they do not apply —
        # every dossier assembled before these fields is in that state — and an appended "" is a
        # BLANK LINE in the rendered page, which makes the committed .md stale against its own
        # JSON on names that gained nothing. Caught by the three e2e mirror pins, not by a unit.
        out += [line for line in (_forward_multiples_md(m.valuation.forward_multiples),
                                  _multiple_basis_md(m)) if line]
    if m.peer_comps is not None:
        out.append(_fact("Comparability", m.peer_comps.comparability))
    if m.catalyst_path is not None:
        # (content relocation 2026-07-24) framed as CONTRAST, not as one of our numbers. The rows
        # above are our read; this is the street's. On a fund whose edge IS a variant view, listing
        # the consensus target as a peer of our own valuation blurs the distinction being sold.
        out.append(_fact("The street, for contrast (target · ratings)",
                         m.catalyst_path.consensus_stats))
    out.append("")
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
        basis = getattr(mc, "multiple_basis", "EV/EBITDA")
        hdr = (f"| scenario | rev $M | margin | EBIT $M | +D&A → EBITDA $M | ×mult ({basis}) | "
               "value/sh | margin own/peer pct | source |")
        out += ["", f"**Scenario grid** (analyst-supplied; machine computes value + placement; "
                f"$M rev/net-debt; spot ${mc.spot:.2f}, net debt ${mc.net_debt_musd:.0f}M; the "
                f"multiple is applied to **{basis}**):",
                "", hdr, "|---|---:|---:|---:|---:|---:|---:|---|---|"]
        for s in mc.scenarios:
            out.append(
                f"| {s.name} | {s.revenue_musd:.0f} | {_mc_pct(s.margin)} | "
                f"{s.op_income_musd:.0f} | {s.ebitda_musd:.0f} | {s.multiple:.1f}x | "
                f"${s.value_per_share:.2f} | "
                f"{_mc_pctile(s.margin_pct_of_own)} / {_mc_pctile(s.margin_pct_of_peer)} "
                f"| {s.source}"
                f"{(' — ' + s.reason) if s.reason else ''} |")
        out.append("")
        # CROSS-CHECKS — capital intensity is what an EBITDA multiple hides. Labelled, not headline.
        xs = [s for s in mc.scenarios if s.ev_ebit is not None or s.norm_fcf_musd is not None]
        if xs:
            cells = " · ".join(
                f"{s.name} EV/EBIT {('—' if s.ev_ebit is None else f'{s.ev_ebit:.1f}x')}, "
                f"norm-FCF {('—' if s.norm_fcf_musd is None else f'${s.norm_fcf_musd:.0f}M')}"
                for s in xs)
            out += [f"- _Cross-checks (capital intensity — an {basis} multiple flatters a "
                    f"capital-heavy carrier; maint-capex ≈ D&A):_ {cells}", ""]
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


def _drawdown_idio_lines(m: MechanicalLayer, *, sleeve: str = DEFAULT_SLEEVE) -> list[str]:
    """(D1·§1) The drawdown READ — per-gap ledger when the
    shape is discrete), the market comparison, the graph cohort, and the 8-K evidence grouped by
    accession. Extracted verbatim from render_markdown (2026-07-27) so the analysis tier
    COMPOSES like its JS twin instead of running inline — no behaviour change.
    Twin: drawdownIdio()."""
    out: list[str] = []
    # (D1·§1) Drawdown cause & idiosyncrasy — CLUBBED: what happened, and did it happen alone?
    # (buy-side anatomy) the Shape classification is this section's READ — label twins the web lead
    # THE QUESTION THE PAGE ASKS, per book. "What broke" is the right question for a name that
    # broke and the WRONG one for a compounder that never did — the defect this build removes. The
    # SECTION is unchanged: the gap-downs and the idiosyncratic-vs-shared split are real facts
    # about any name's price path; only the heading claimed something about the name.
    _row = BY_KEY[require_sleeve(sleeve, where="render._drawdown_idio_lines")]
    out.append(f"## {_row.drawdown_heading}")
    # (event study) discrete gap-downs render as a scannable per-gap list — date, the TRUE 1-day
    # move (derived from the daily perf series; omitted, never estimated, when the committed series
    # can't carry it), cause. One gap / unparseable shape → the one-line fact.
    _shape = m.drawdown_cause.shape
    _rows = (_gap_list(_fmt_shape(_shape.value))
             if _shape.status is SourceStatus.PRESENT and _shape.value is not None else None)
    if _rows is not None:  # ANY discrete-gap name — a 1-gap ledger still carries the true %
        out.append(f"- **{_row.read_label}** · discrete gap-downs:{_cite(_shape.source_ref)}")
        for _gd, _cause in _rows:
            _gpct = _gap_pct_from_perf(m.stock_performance, _gd)
            _gpct_s = f" **{_gpct * 100:+.1f}%**" if _gpct is not None else ""
            out.append(f"  - {_gd}{_gpct_s} → {_cause}")
    else:
        out.append(_fact(_row.read_label, _shape, _fmt_shape))
    # (declutter) the dates row repeats the shape line whenever every date already appears there
    gd = m.drawdown_cause.gap_down_dates
    shape_v = m.drawdown_cause.shape
    if not (gd.status is SourceStatus.PRESENT and shape_v.status is SourceStatus.PRESENT
            and all(str(d) in str(shape_v.value) for d in (gd.value or []))):
        out.append(_fact("Gap-down dates", gd, _dates))
    # (buy-side restructure, twins the web) the alone-or-with-market comparison follows the READ
    # directly; the 8-K evidence closes the section as provenance. Revised guidance is a guidance
    # fact — it renders on the street section (legacy no-catalyst-path JSON keeps it here).
    io = m.idiosyncratic_vs_shared
    out += ["", "_Company-specific or market-wide?_",
            _fact("Name 180d return", io.name_180d_return, _pct)]
    # (declutter P1) an "UNKNOWN — benchmark bars unavailable" market row directly above a PRESENT
    # relative-vs-market number reads as a contradiction (if relative is known, the market read
    # existed at assembly). Show the market row only when it carries a value or the relative is
    # absent too — the honest-absence case.
    if (io.market_180d_return.status is SourceStatus.PRESENT
            or io.rel_vs_market.status is not SourceStatus.PRESENT):
        out.append(
            _fact(f"Market ({io.benchmark_symbol}) 180d return", io.market_180d_return, _pct))
    out.append(_fact("Relative vs market", io.rel_vs_market, _pct))
    cohort = io.cohort
    if cohort.status is SourceStatus.PRESENT and cohort.value:
        out.append(_fact("Cohort read", io.read))
        out.append(f"- **Graph cohort** (`{cohort.source_ref}`):")
        for cm in cohort.value:
            ret = f"{cm.ret_180d:.0%}" if cm.ret_180d is not None else "no bars"
            out.append(f"  - [{cm.hops}h] {cm.ticker}: {ret} · via {cm.via}")
    else:
        # (declutter · buy-side) absence is ONE quiet footnote line, never a labelled fact row
        out.append("_no supplier/customer cohort mapped for this name — the comparison is vs "
                   "the market only_")
    # GROUP BY ACCESSION (twin of the web): one 8-K can explain two consecutive gap-downs
    # (SMPL 04-09/04-10, CNXC 02-11/02-12); the flat loop printed the same block per gap-date,
    # once even as "gap 2026-04-10 → 2026-04-09" which read like a date error. One entry per
    # filing, naming every gap-down it explains. An administrative-only 8-K (5.07 annual-meeting
    # vote, etc.) is dropped here — its card recited noise; the shape line already reads "no
    # earnings/guidance filing" for that gap and the filing ref stays in JSON.
    grouped: dict[str, tuple[Any, list[str]]] = {}
    for f in m.drawdown_cause.filings:
        if not f.explanatory:
            continue
        k = f.accession or f"{f.form}|{f.filing_date}"
        grouped.setdefault(k, (f, []))[1].append(f.gap_date)
    # (#2/#3b twin) a filing is CARDED when it parsed a driver OR carries a substantive non-2.02
    # item (1.01/8.01/…); those show in full. NON-carded filings (a lone 7.01, an unparsed 2.02)
    # list under "Other 8-Ks" — no filing is shown twice.
    _carded = {k: (f, gaps) for k, (f, gaps) in grouped.items()
               if (f.drivers is not None and f.drivers.status is SourceStatus.PRESENT)
               or _substantive_events(f)}
    _uncarded = {k: v for k, v in grouped.items() if k not in _carded}
    if _carded:
        out.append("- **Gap-downs — what the results showed (parsed EX-99.1) + the 8-K:**")
        for f, gaps in _carded.values():
            gap_str = " and ".join(gaps)
            plural = "s" if len(gaps) > 1 else ""
            out.append(f"  - gap-down{plural} {gap_str} → filed {f.filing_date} "
                       f"[`{f.accession}`]({f.url})")
            # 9.01 (exhibits) + 7.01 (Reg-FD webcast noise) dropped from display; JSON keeps them
            _shown_items = [t for t in f.item_types
                            if not (t.startswith("9.01") or t.startswith("7.01"))]
            out.append(f"    - items: {', '.join(_shown_items) or '—'}")
            # the parsed EX-99.1 driver (metrics) PLUS the substantive non-2.02 item narratives —
            # the driver often isn't the catalyst (VRRM's Avis termination, AORT's 1.01 agreement)
            if f.drivers is not None and f.drivers.status is SourceStatus.PRESENT:
                out.append(f"    - **what the results showed:** {_fix_acronyms(f.drivers.value)}"
                           f"{_cite(f.drivers.source_ref)}")
            for ev in _substantive_events(f):
                out.append(f"    - {_fix_acronyms(ev)}")
    if _uncarded:
        out.append(f"- **Other 8-Ks at the gap dates ({len(_uncarded)}):**")
        for f, _gaps in _uncarded.values():
            _shown_items = [t for t in f.item_types if not t.startswith("9.01")]
            out.append(f"  - filed {f.filing_date} · items: {', '.join(_shown_items) or '—'} "
                       f"[`{f.accession}`]({f.url})")
            for ev in f.events:
                cleaned = _clean_item_event(ev)
                if cleaned is not None:
                    out.append(f"    - {cleaned}")
    out += _event_impact_lines(m)  # (RC-1 C) Avis-class event-impact quantifications
    if m.catalyst_path is None:  # legacy: never drop the fact when there is no street section
        out.append(_fact("Revised guidance", m.drawdown_cause.revised_guidance))
    out.append("")
    return out


def _leverage_survival_lines(d: Dossier, m: MechanicalLayer) -> list[str]:
    """(D1·§2) "Leverage & survival" — the survival story in one place: the unified
    leverage block (or the pre-B2 fallback), FCF, capital structure + maturity wall,
    and the primary-source cross-checks. Twin: dossier.js leverageSurvival().

    Extracted verbatim from render_markdown (2026-07-27) so the analysis tier COMPOSES
    like its JS twin instead of running inline — no behaviour change."""
    out: list[str] = []
    # (D1·§2) Leverage & survival — the survival story in one place (+ FCF + liquidity).
    if m.leverage_survival is not None:
        out += _leverage_block(m)  # ## Leverage & survival (unified) …
    else:  # pre-B2 JSON: the quality leverage lines under the same header
        out += ["## Leverage & survival", *_quality_leverage_lines(m)]
    # (declutter P1) "FCF sign: UNKNOWN" directly above a present FCF value read as a
    # contradiction — the sign is derivable from the number on the same surface. The sign row
    # renders only when it carries a value or the FCF value itself is absent.
    if (m.quality.fcf_sign.status is SourceStatus.PRESENT
            or m.quality.free_cash_flow.status is not SourceStatus.PRESENT):
        out.append(_fact("FCF sign", m.quality.fcf_sign, _signword))
    # (PR-5) THE BASIS TRAVELS WITH THE NUMBER. `_fact` renders a note only when the fact is NOT
    # present, so a PRESENT figure's note is written to JSON and never reaches the page — 55 of
    # NFLX's 135 present facts carry one today. That is fine for most, and not for this one: CIQ's
    # "Levered Free Cash Flow" disagrees with CFO − capex on 13 of 14 committed names (0.27x to
    # 2.28x, and AORT differs in SIGN), so the figure is unreadable without its basis. Rendered
    # here rather than by changing `_fact`, which would add ~55 lines of mostly-verbatim notes to
    # every page.
    fcf = m.quality.free_cash_flow
    if fcf.status is SourceStatus.PRESENT and fcf.note:
        out.append(f"- **Free cash flow ($M):** {fcf.value} — {_clean_note(str(fcf.note))}"
                   f"{_cite(fcf.source_ref)}")
    else:
        out.append(_fact("Free cash flow ($M)", fcf))
    # (E1/E2) structured capital structure + maturity wall replace the flat liquidity string; pre-E
    # dossier.json falls back to the legacy Quality.liquidity_covenant_flags line.
    if m.capital_structure is not None:
        out += _capital_structure_lines(m.capital_structure, d.reference_date)
    else:
        out += [_fact("Liquidity / covenant flags", m.quality.liquidity_covenant_flags), ""]
    # (RC-1 C) primary-source cross-checks — filings vs CIQ panel (self-funding lives in leverage
    # above; wall / triangulation / guide / going-concern / concentration here).
    out += _primary_source_block(m)

    return out


def _trajectory_section_lines(m: MechanicalLayer) -> list[str]:
    """(D1·§3·D2) "Operating trajectory" — the merged margin/multi-year table, the
    share-count trend, and the per-period return-ratios table. Twin: dossier.js trajectorySection().

    Extracted verbatim from render_markdown (2026-07-27) so the analysis tier COMPOSES
    like its JS twin instead of running inline — no behaviour change."""
    out: list[str] = []
    # (D1·§3 · D2) Operating trajectory — the merged margin/multi-year table + share-count trend
    # + (tier redesign) the per-period return-ratios table, moved here from the Brief.
    out.append("## Operating trajectory")
    out += _trajectory_table_lines(m)
    out.append(_fact("Share-count trend", m.quality.share_count_trend))
    # (PR-4) MAIN BODY, beside the trajectory it qualifies — this decides whether the EPS a reader
    # is about to divide by means anything, so it is a decision value rather than audit context.
    # Rendered only when the field exists: dossiers assembled before it carry None, and printing
    # "unknown" for them would claim we looked.
    if m.quality.nonoperating_earnings is not None:
        out.append(_fact("Non-operating earnings", m.quality.nonoperating_earnings))
    if m.return_ratios is not None and m.return_ratios.status is SourceStatus.PRESENT:
        out += _fin_table_lines("Return ratios — per fiscal period", m.return_ratios)
    out.append("")

    return out


#: Coverage caution band — 3 <= n < 6 is thin but usable, so the count renders WITH a caution
#: rather than the route being narrowed. Mirrors `ev_gap.CAUTION_ESTIMATES`; the two are asserted
#: equal by test rather than shared by import, because the renderer must not depend on the compute
#: module (the twin JS has no import to share).
_EV_GAP_CAUTION_MAX = 5


def _pct_stated(x: float | None, *, base: str, when: str | None) -> str:
    """A percentage that STATES ITS BASE AND ITS DATE, or says it cannot.

    A bare "4.3%" is unreadable: percent of what, measured when. Both travel with the number here
    rather than in a caption a reader has to hunt for."""
    if x is None:
        return "UNKNOWN"
    stamp = f", {when}" if when else ", date unstated"
    return f"{x:.1%} ({base}{stamp})"


def _sigma_cell(cell: dict[str, Any]) -> str:
    """Sigma WITH ITS n, or NOTHING — never sigma alone.

    THE MVST TRAP IN PRINT: its EBITDA high == low == median on ONE estimate, so dispersion reads
    0.0%, which a reader takes for maximum agreement when it means there was nobody to disagree.
    The count is what tells those apart, so a sigma whose n is unknown does not render at all.
    """
    sd, raw = cell.get("std_dev"), cell.get("estimates")
    n = _estimate_head(raw)
    if sd is None or n is None:
        return "—"
    caution = " · thin" if n <= _EV_GAP_CAUTION_MAX else ""
    return f"sigma {sd:,.2f} on n={n}{caution}"


def _estimate_head(raw: object) -> int | None:
    """CIQ's raw pair (`9/11`) -> 9. Never re-labelled "broker count"; only read."""
    if not isinstance(raw, str) or "/" not in raw:
        return None
    head = raw.split("/", 1)[0].strip()
    return int(head) if head.isdigit() else None


def _ev_gap_lines(m: MechanicalLayer) -> list[str]:
    """(A2) THE EV GAP — our base case against the street, as three ratios whose product IS the gap.

    THREE STATES, THREE SENTENCES, NEVER AN EMPTY BLOCK. `None` means the refresh has not reached
    this name; `status="not-computed"` means it ran and could not strike a gap, and says why;
    `computed` renders the decomposition. The render ships on deploy while the refresh lags, so a
    block that simply vanished would leave a page silently missing a section — the two-speed defect
    #319 taught, which is why the compute layer returns a status for every path instead of omitting.

    NOT AN ATTRIBUTION. The three ratios are stated and their product reconciles by identity;
    nothing here says which ratio "explains" the gap. The shape LABEL is a deterministic function of
    the three, printed with whether the adjacent year agrees — because the uncomfortable label
    (`multiple-dominant`: the view rests on re-rating, not on the business) must not be movable by
    choosing a year.
    """
    g = getattr(m, "ev_gap", None)
    if not isinstance(g, dict):
        return ["### The EV gap — our base case vs the street", "",
                "_Not yet computed for this name — the mechanical refresh that writes it has not "
                "run here. This is a MISSING REFRESH, not a finding: nothing has been measured "
                "and nothing is being withheld._", ""]
    v = g.get("vintages") or {}
    cons_as_of, tev_as_of = v.get("consensus_as_of"), v.get("tev_as_of")
    head = ["### The EV gap — our base case vs the street", ""]
    if g.get("status") != "computed":
        why = str(g.get("reason") or "no reason recorded")
        form = g.get("form")
        line = f"_No gap is struck for this name: {why}._"
        if form:
            line = (f"_No gap is struck for this name: {why}. The consensus side alone still "
                    f"routes to **{form}** at FY{g.get('anchor_fy')}, so the form is known even "
                    "though the comparison is not._")
        return [*head, line, ""]

    r, br, cons = g["ratios"], g.get("bridge") or {}, g.get("consensus") or {}
    anchor, adj = g.get("anchor_fy"), g.get("adjacent_fy")
    shape = g.get("shape") or {}
    # THE CONSENSUS VINTAGE IS A FLOOR AND PRINTS AS ONE. SMPL's estimates export carries no
    # As-Of header, so its date is ">=". Stripping the marker would assert a precision the
    # workbook cannot attest — the operator's brief said "the 07-30 export"; the export says
    # "on or after 2026-07-21", and only the second is defensible on the page.
    # THE MARKER IS THE UNICODE ≥, not ">=" — the first cut checked ASCII and the note silently
    # never rendered, which is the same class as the value it guards: a precision claim nobody
    # could see was missing.
    floor_note = (" (a FLOOR — the export states no as-of, so the true date is on or after this)"
                  if isinstance(cons_as_of, str) and cons_as_of.lstrip().startswith(("≥", ">="))
                  else "")
    out = [*head,
           f"_Anchor FY{anchor} · consensus as-of {cons_as_of or 'UNKNOWN'}{floor_note} · "
           f"TEV as-of {tev_as_of or 'UNKNOWN'} · form {g.get('form')}_", ""]

    def ratio(x: float | None) -> str:
        return f"{x:.2f}x" if isinstance(x, (int, float)) else "UNKNOWN"

    # THE TOTAL GAP NEEDS NO CONSENSUS — `our_EV / TEV` is our leg against the market's price. Where
    # the DECOMPOSITION is suppressed the total still stands, so the block states it and says what
    # is missing, rather than withholding both. Suppressing a computable statement because a
    # different one is unavailable is what the first cut did to AORT/NCNO/MVST.
    decomp = g.get("decomposition") or {}
    if decomp.get("status") == "suppressed":
        out += [f"- **Total gap:** **{ratio(r.get('ev_gap'))}** — our EV against the market's TEV. "
                "No consensus enters this figure.", ""]
        out += [f"- **Decomposition suppressed:** {decomp.get('reason')}", ""]
        # NOT `m` — that is this function's MechanicalLayer parameter, and rebinding it silently
        # re-typed everything below. Caught by mypy; a dynamically-typed twin would not have.
        mg = decomp.get("margins") or {}
        if isinstance(mg.get("ours"), float) and isinstance(mg.get("consensus"), float):
            # FIGURES, NEVER A RATIO. `14.4% vs 19.4%` lets the reader see the distance and judge
            # how much of it is horizon; `0.74x` presents that distance as though its cause were
            # settled. The figures are strictly more information than the ratio they replace.
            out += [f"  - _Our EBITDA margin **{mg['ours']:.1%}** vs consensus "
                    f"**{mg['consensus']:.1%}** at FY{anchor} — shown as figures, NOT divided: "
                    f"{mg.get('basis')}_", ""]
        # NO SHAPE LINE. The label ranks three ratios; with none struck there is nothing to rank,
        # and printing one would assert an attribution the numbers do not support.
        out += _ev_gap_tail(g, br, cons, anchor, cons_as_of)
        return out

    rows = [
        ["revenue", ratio(r.get("revenue_ratio")),
         _sigma_cell(cons.get("Revenue") or {})],
        ["EBITDA margin", ratio(r.get("margin_ratio")),
         _sigma_cell(cons.get("EBITDA") or {})],
        ["exit multiple", ratio(r.get("multiple_ratio")),
         (f"street {br['market_multiple']:.2f}x at FY{anchor}"
          if isinstance(br.get("market_multiple"), (int, float)) else "—")],
        ["**product = the EV gap**", f"**{ratio(r.get('ev_gap'))}**", ""],
    ]
    out += _table("The gap, decomposed (ours / consensus, at the anchor year)",
                  None, ["ratio", "consensus dispersion"], rows,
                  note="the three ratios multiply to the gap by IDENTITY — this is a "
                       "decomposition, never an attribution of cause",
                  num_cols=frozenset({1}))

    # THE SHAPE, WITH ITS CROSS-YEAR CHECK. `agree` is TRISTATE: None means there was no adjacent
    # forward year to check against, which is absent evidence and must not read as confirmation.
    agree = shape.get("agree")
    if agree is True:
        chk = f"and FY{adj} gives the same shape — the label does not move with the year"
    elif agree is False:
        chk = (f"but FY{adj} gives **{shape.get('adjacent')}** — the shape MOVES between years, "
               "so neither is the answer on its own")
    else:
        chk = "with NO adjacent forward year to check it against — unchecked, not confirmed"
    out += [f"- **Shape:** **{shape.get('anchor')}** at FY{anchor}, {chk}.", ""]
    # THE BASIS CAVEAT RIDES WITH THE SHAPE, because the shape is what it qualifies. The TOTAL gap
    # carries no year and is unaffected; the ATTRIBUTION is struck at the anchor, so a leg struck
    # elsewhere makes this label describe a comparison the leg does not make. UNSTATED and
    # DISAGREEING render as different sentences — collapsing them would make the caveat useless on
    # precisely the records it exists for, every one of which predates the field.
    lb = g.get("leg_basis") or {}
    if lb.get("state") == "disagrees":
        # SEVERITY FOLLOWS THE CROSS-YEAR CHECK ALREADY PRINTED ONE LINE ABOVE. EPAM is the first
        # record to state `leg_fy`, and the first draft warned "⚠ … describes a comparison the leg
        # does not make. Re-read the attribution on FY2027" DIRECTLY BENEATH a line reading "FY2027
        # gives the same shape — the label does not move with the year." Two adjacent sentences,
        # one instructing work the other had just done, on the only page in the fleet that shows
        # this caveat at all. A reader meeting it first would read a defect where there is a
        # correctly-declared difference.
        #
        # `agree` is the SAME tristate the shape line uses, so the two can never diverge: shape
        # invariant across the checked year → DECLARED AND IMMATERIAL to the label; shape MOVES →
        # the warning is real and keeps its mark; unchecked → say unchecked, never confirmed.
        same_year = str(lb.get("leg_fy")) == str(adj)
        if agree is True and same_year:
            out += [f"  _Declared, and immaterial to this label: the base leg is struck at "
                    f"FY{lb.get('leg_fy')} and the decomposition at FY{lb.get('anchor_fy')}, but "
                    f"the shape is the same at both years (checked above), so the label holds on "
                    f"either basis. The total gap carries no year and is unaffected._", ""]
        elif agree is False and same_year:
            out += [f"  ⚠ **The label is struck on FY{lb.get('anchor_fy')}, the base leg is "
                    f"FY{lb.get('leg_fy')}, and the shape MOVES between them.** This is the case "
                    f"the caveat exists for: the split — and the label drawn from it — describes a "
                    f"comparison the leg does not make. Re-read the attribution on "
                    f"FY{lb.get('leg_fy')}.", ""]
        else:
            out += [f"  ⚠ **The label is struck on FY{lb.get('anchor_fy')}, but the underwrite's "
                    f"base leg is FY{lb.get('leg_fy')}.** {lb.get('note')}", ""]
    elif lb.get("state") == "unstated":
        out += [f"  _The record does not state which fiscal year its base leg is struck at, so "
                f"this label is reported on FY{lb.get('anchor_fy')}'s basis and is unverified "
                "against the leg. The total gap above carries no year and is unaffected._", ""]

    out += _ev_gap_tail(g, br, cons, anchor, cons_as_of)
    return out


def _ev_gap_tail(g: dict[str, Any], br: dict[str, Any], cons: dict[str, Any],
                 anchor: object, cons_as_of: object) -> list[str]:
    """The bridge, the dispersions and the D&A convention — shared by BOTH branches.

    ONE DEFINITION, because a decomposed and a suppressed block must not drift about how they
    report the same three things."""
    out: list[str] = []
    # POSITIVE shares, not merely numeric — see `build_ev_gap`'s own refusal.
    if (all(isinstance(br.get(k), (int, float)) for k in ("our_ev", "net_debt", "shares", "tev"))
            and br["shares"] > 0):
        eq = br["our_ev"] - br["net_debt"]
        out += [
            f"- **Bridge:** our EV ${br['our_ev']:,.0f}M − net debt ${br['net_debt']:,.0f}M "
            f"= equity ${eq:,.0f}M ÷ {br['shares']:,.3f}M sh = **${eq / br['shares']:,.2f}/sh** "
            f"— against TEV ${br['tev']:,.0f}M.", ""]
    for metric in ("Revenue", "EBITDA"):
        route = (g.get("routes") or {}).get(metric) or {}
        disp = route.get("dispersion")
        if isinstance(disp, (int, float)):
            when = f"FY{anchor}, as-of {cons_as_of}"
            out.append(f"  - _{metric} dispersion "
                       f"{_pct_stated(disp, base='high−low ÷ |median|', when=when)}_")
    if out and out[-1].startswith("  - _"):
        out.append("")
    if g.get("d_and_a_convention"):
        out += [f"  - _D&A convention: {g['d_and_a_convention']} — the two recipes differ and the "
                "reconciliation is an open analyst question, so it is stated rather than assumed._",
                ""]
    return out


def _valuation_section_lines(d: Dossier, m: MechanicalLayer) -> list[str]:
    """(D1·§4) "Valuation & own-history" — the cross-sectional read (the edge) first, then implied
    expectations, then the own-history reads; the mid-cycle underwrite block closes it when a
    record exists. Twin: dossier.js valuation().

    Extracted verbatim from render_markdown (2026-07-27) so the analysis tier COMPOSES
    like its JS twin instead of running inline — no behaviour change."""
    out: list[str] = []
    # (D1·§4) Valuation & own-history. (G) implied expectations slot in AFTER cross-sectional (the
    # edge) and BEFORE the own-history reads.
    out.append("## Valuation & own-history")
    out.append(_fact("Cross-sectional (vs peers — the edge)", m.valuation.cross_sectional))
    out += _implied_expectations_lines(m.valuation)
    # (A2) THE EV GAP sits directly after the price-implied levels: those state what the price
    # implies at each multiple, this states what OUR base case implies against the street. Same
    # question from the two sides, so they read together.
    out += _ev_gap_lines(m)
    # (declutter P1) the bare P/E and EV/EBITDA fact rows are GONE: both numbers already render
    # inside tables that carry their context (the peer grid; the dated range line below), and the
    # two sheets disagree by vintage (P/E 14.1 vs the comps grid's 13) — two values of one ratio
    # with no reconciliation reads as a contradiction, not information.
    out += [
        _fact("EV/EBITDA (adjusted, forward)", m.valuation.ev_ebitda_adjusted_fwd),
        _fact("Adjusted EPS (earnings power)", m.valuation.adjusted_eps),
        _fact("Own-history range position", m.valuation.range_position),
        "",
    ]

    # (mid-cycle) the cyclical-underwriting section — UNDER the valuation block. Rendered only when
    # the record is present (absent → nothing, so pre-midcycle dossiers are byte-identical).
    out += _midcycle_section(d.midcycle)

    return out


def _peer_comps_lines(m: MechanicalLayer) -> list[str]:
    """(D1·§5) "Peer comps" — roster, the comparability confidence gate, the multiples read and the
    per-peer grid. Implied valuation is DEMOTED to the appendix. Twin: dossier.js peerComps().

    Extracted verbatim from render_markdown (2026-07-27) so the analysis tier COMPOSES
    like its JS twin instead of running inline — no behaviour change."""
    out: list[str] = []
    # (D1·§5) Peer comps — roster + comparability + multiples + grid + implied valuation.
    out.append("## Peer comps")  # (K5) discipline framing lives in the block body + source_refs
    out += _roster_lines(m.peer_comps.peer_set)
    out.append(_fact("Comparability (confidence gate)", m.peer_comps.comparability))
    out += _multiples_lines(m.peer_comps.trading_multiples,
                            grid_present=m.peer_comps.peer_grid is not None)
    out += _peer_grid_or_deltas(m.peer_comps)
    out.append("")
    # (K4) implied valuation is DEMOTED to the appendix (reference-only) — not in the main body.

    return out


def _business_quality_lines(m: MechanicalLayer) -> list[str]:
    """(content relocation 2026-07-24) "Business quality" — what it sells, where the profit sits, to
    whom and where. Renamed from "Ownership & concentration", which held no ownership.
    Twin: dossier.js concentration().

    Extracted verbatim from render_markdown (2026-07-27) so the analysis tier COMPOSES
    like its JS twin instead of running inline — no behaviour change."""
    out: list[str] = []
    # (content relocation 2026-07-24) BUSINESS QUALITY — renamed from "Ownership & concentration",
    # which carried NO ownership: all four facts are the business MIX (what it sells, where the
    # profit sits, to whom, where). The real ownership data (insider activity, short interest) sat
    # in "The street" and moves to the appendix. This section answers "what is this business, and
    # is it any good" — the question that belongs BEFORE anyone argues about value.
    out.append("## Business quality")
    out += [
        _fact("Segments (revenue share)", m.concentration.segments),
        _fact("Segments (EBITDA share — where profit sits)", m.concentration.segment_ebitda),
        # (2026-09-21) segment profit from the 10-K's XBRL instance. ABSENT for a single-segment
        # filer, and then NOT rendered — an UNKNOWN badge would claim a gap in a breakdown the
        # company does not have. The sentence is written once, in mechanical._segment_profit_line.
        *([_fact("Segments (profit — the filer's own measure, 10-K)",
                 m.concentration.segment_profit, lambda v: str(v.line))]
          if m.concentration.segment_profit is not None else []),
        _fact("Customers", m.concentration.customers, _fmt_customers),
        _fact("Geographic", m.concentration.geographic),
        "",
    ]

    return out


def _argument_lines(d: Dossier, *, dev: bool) -> list[str]:
    """"The argument" — the synthesis tier (balance → bull → bear → decisive question → unknowns →
    twins), or the honest not-assembled note. Twin: dossier.js synthesis().

    Extracted verbatim from render_markdown (2026-07-27) so the analysis tier COMPOSES
    like its JS twin instead of running inline — no behaviour change."""
    out: list[str] = []
    # Synthesis — balance → bull → bear → decisive → unknowns → twins.
    if d.synthesis is not None:
        out += _synthesis_lines(d, dev=dev)
    else:
        out += ["## The argument",
                "_Synthesis not assembled — the tier's mechanical evidence stands alone._", ""]

    return out


#: THE SIDECAR THAT MARKS A SEALED RECORD AS KNOWN-WRONG. Read from a file BESIDE `dossier.json`,
#: never from the record: FUBO's standing rule seals the record until a post-combination
#: re-assembly exists, and the marker must not become a way around that. A rendered view is not
#: the record, so the block is printed; the record itself stays untouched.
#:
#: TOP OF THE PAGE, before the brief. A reader who reaches the numbers first has already been
#: misled — the whole point is the distinction between a GAP (a number we lack) and an ERROR (a
#: number we have and can demonstrate is wrong), and only the second needs to arrive first.
KNOWN_WRONG_FILE = "known_wrong.json"


def _known_wrong_lines(ticker: str, root: Path | None = None) -> list[str]:
    """The known-wrong banner, or nothing. Absent file == nothing rendered, which is the normal
    case for every name but FUBO."""
    base = root or (get_config().data_dir / "dossiers")
    path = Path(base) / ticker.upper() / KNOWN_WRONG_FILE
    # ABSENT is the normal case — ten of eleven names have no marker, and silence is correct.
    if not path.is_file():
        return []
    # PRESENT-BUT-UNUSABLE IS NOT SILENCE. Review finding: the first cut caught OSError and
    # ValueError and returned [], so a corrupt or empty marker made the banner VANISH while it sat
    # looking like the page was marked. That is the worst available failure for a warning — the
    # page renders CLEAN and looks valid, which is the exact state FUBO's standing rule exists to
    # prevent. A marker that cannot be read is a BROKEN WARNING, not an absent one; the two are
    # different states and only one of them is safe to render through.
    try:
        doc = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"{path} exists but cannot be read ({exc}) — a known-wrong marker that fails to "
            "render leaves the page looking valid. Fix or delete the file; never render past it."
        ) from exc
    items = doc.get("items") or []
    if not items:
        raise ValueError(
            f"{path} exists but names no items — an empty marker renders nothing and reads as "
            "'this page is fine'. Delete the file if the page is fine.")
    out = [
        "> ## ⚠ KNOWN-WRONG — do not read the figures on this page as current",
        ">",
        f"> {doc.get('the_distinction', '')}",
        ">",
    ]
    for i, it in enumerate(items, start=1):
        out.append(f"> **{i}. {it.get('claim', '')}** {it.get('known_false', '')}")
        if it.get("not_merely_stale"):
            out.append(f">     *{it['not_merely_stale']}*")
        out.append(">")
    if doc.get("clears_when"):
        out.append(f"> **Clears when:** {doc['clears_when']}")
        out.append(">")
    out.append("")
    return out


@_endnote_scope
def render_markdown(d: Dossier, *, dev: bool = False, show_proposal: bool = False,
                    card: ScenarioRecord | None = None,
                    dossiers_root: Path | None = None) -> str:
    """(D1 · re-ordered 2026-07-27) DECISION order. Analysis reads: what broke → business quality
    → the argument → catalyst calendar → valuation → peer comps → operating trajectory → the street
    → leverage & survival → analyst caveats. The old "mechanical layer" wrapper (a grouping by who
    PRODUCED the content) is gone, so those section heads are H2. Appendix: reading guide →
    statements → cap-structure provenance → implied equity → mgmt pointer → ownership & positioning
    → Record & reproduce. Old
    committed JSONs still render (every field is optional-safe). ``dev`` shows the D3 tier tags.
    ``show_proposal`` reveals the sealed machine proposal in the brief (default False — the brief
    hides it so it can't anchor the human before they log their verdict).
    The fresh per-document endnote table + its reset are handled by ``@_endnote_scope``."""
    m = d.mechanical
    # SLIM HEADER (tier redesign): name + the DOCUMENT date. The old meta italic was process
    # telemetry, and its "data as of <screen-date>" contradicted the body's own per-fact as-ofs.
    # The full vintage map + model + pivot mechanics live in Record & reproduce at the end.
    ident = f"({d.exchange}: {d.ticker})" if d.exchange else f"({d.ticker})"
    out: list[str] = [
        f"# Dossier — {d.name} {ident}",
        "",
        # (26a) the extraction stamp rides the DOCUMENT DATE, in the MAIN BODY. The date says when
        # this was built; the version says with what — and "are these two dossiers comparable?"
        # turns on the second. Deliberately NOT confined to Record & reproduce: a stamp a reader
        # never meets cannot stop them comparing two vintages, which is 17b's failure exactly.
        f"_{d.assembled_at:%B %-d, %Y} · extraction {stamp_label(d.extraction_version)}_",
        "",
    ]
    # BEFORE the brief: a known-wrong marker has to reach the reader before the numbers do.
    # THE BANNER MUST COME FROM BESIDE THE RECORD BEING RENDERED, not from the configured tree.
    # `refresh_dossier` decides a record is SEALED from `path.parent/known_wrong.json` — a
    # PATH-relative fact — while this lookup defaulted to `get_config().data_dir/dossiers`, a
    # CONFIG-relative one. Two sources of truth for one fact: rendering a sealed dossier in another
    # checkout, a staging tree or a temp copy would decide "sealed" from the sidecar beside it and
    # then render the banner from somewhere else — dropping it when the configured tree has no
    # marker for that ticker, or worse, pasting an UNRELATED name's marker onto the page. That is
    # the FUBO defect exactly (banner in one artifact, absent from the served one), re-created by
    # the fix meant to serve it. Every writer passes the root it is writing into.
    out += _known_wrong_lines(d.ticker, dossiers_root)
    # (3-tier) BRIEF — first cut: the machine READ + decisive question + decision data + condensed
    # case + valuation snapshot. The derived proposal is SEALED at assembly but hidden here
    # (anti-anchoring) unless ``show_proposal``; the human's logged confirm/override — a ledger
    # concern — is the verdict of record, and the reveal happens after it is logged.
    out += _brief_lines(d, show_proposal=show_proposal, card=card)
    # (3-tier · re-ordered 2026-07-27) ANALYSIS — the full dossier, in DECISION order (see the
    # composition below; caveats now CLOSE the tier rather than open it).
    out += ["# Analysis — full dossier", ""]
    # (content re-order 2026-07-27) DECISION order, not provenance order. The old sequence
    # ran machine-assembled facts first and the argument last, under a '## Mechanical layer'
    # wrapper — a grouping by WHO PRODUCED the content. That wrapper is gone (the web twin
    # never had it, per-fact source-binding already carries provenance precisely, and the
    # three tiers already separate decide/argue/prove), so the sequence below reads as the
    # questions a decision asks, in order. Twin: dossier.js analysisTier().
    out += _drawdown_idio_lines(m, sleeve=d.sleeve)
    out += _business_quality_lines(m)
    out += _argument_lines(d, dev=dev)
    out += _catalyst_calendar_lines(d, card)
    out += _valuation_section_lines(d, m)
    out += _peer_comps_lines(m)
    out += _trajectory_section_lines(m)
    out += _catalyst_section(m)
    out += _leverage_survival_lines(d, m)
    out += _flags_section(d)
    out += ["# Appendix — data & audit", ""]
    out += _how_to_read_lines()
    # (addition #1) the analyst's own inputs are audited FIRST — everything below is machine-
    # assembled evidence, so "why these numbers" belongs at the top of the audit tier.
    out += _assumption_methodology_lines(card)
    appendix = _appendix_lines(m)
    out += appendix if appendix else ["## Financial statements", ""]
    if m.capital_structure is not None:
        out += _capital_structure_appendix_lines(m.capital_structure)  # (K1) provenance
    if m.implied_valuation is not None:
        out += _implied_lines(m.implied_valuation)  # reference-only — its ONLY home
    out += _mgmt_commentary_lines(m)
    out += _positioning_lines(m)  # (relocation) insider + short interest, from "The street"
    out += _verification_lines(m)
    out += _record_reproduce_lines(d)
    out += _sources_section()  # (A2) the single document-end Sources list — every [n] resolves here
    return "\n".join(_dedupe_unknown_reasons(out))  # (H3) fold repeated UNKNOWN reasons


def _how_to_read_lines() -> list[str]:
    """The reading guide — the discipline language that used to repeat as per-section framing,
    stated ONCE (mirrors the web's collapsible; markdown has no <details>, so it prints)."""
    return [
        "## How to read this dossier",
        "- The machine assembles and cites; **the analyst decides**. Nothing here is a "
        "recommendation — the verdict of record is the human's, logged to an append-only ledger "
        "with a frozen entry price.",
        "- The machine's proposed verdict is derived deterministically from its written assessment "
        "and stays **sealed until the analyst's verdict is recorded**, so it cannot anchor the "
        "decision. A two-sided assessment proposes nothing.",
        "- Citations [n] resolve in the Sources list at the document end. **Cited is not "
        "verified** — the reference locates the claim so you can check it.",
        "- Reference values (peer-implied equity, price-implied levels) are shown **beside** the "
        "figures they contextualize, never differenced into an upside — the reader judges the gap.",
        "- A value shown as UNKNOWN is honestly absent at the source — nothing is imputed.",
        "",
    ]


def _panel_age_note(d: Dossier) -> str | None:
    """How old this build's OLDEST panel was AT ASSEMBLY (item 1, re-measured 2026-07-29). None
    when no panel is dated. Value-borne dates (an own-history band's observation date) are NOT
    panels — conflating them inverted the fleet ranking twice, putting SMPL top of a staleness list
    it is bottom of.

    Measured against ``assembled_at``, deliberately, NOT against today: a committed dossier reports
    the age it had when it was built, so re-reading last week's artifact does not silently age it.
    The previous form measured oldest→NEWEST, and the newest panel was the PRICE on 11 of 11 — so
    the rendered number moved when someone refreshed prices, on unchanged CIQ panels."""
    from vinci.dossier.freshness import panel_age

    pa = panel_age(d.mechanical.model_dump(mode="json"), d.assembled_at, kind="export")
    return pa.note() if pa is not None else None


def _consensus_age_note(d: Dossier) -> str | None:
    """How old the STREET's view is — the estimates-sourced panels, which no re-export moves.

    Printed SEPARATELY and ALWAYS, not folded into the panel age. Taking consensus staleness out of
    the gate would otherwise take it out of view, which is the opposite of the intent: a name nobody
    has revised in months is a neglect signal worth reading, and it is only readable if it is on the
    page. Past the ceiling this carries the caveat too."""
    from vinci.dossier.freshness import consensus_note, panel_age

    ca = panel_age(d.mechanical.model_dump(mode="json"), d.assembled_at, kind="consensus")
    if ca is None:
        return None
    return consensus_note(ca) or (
        f"consensus {ca.days}d old ({ca.oldest}, {ca.oldest_key}) — within the ceiling")


def _panel_age_line(d: Dossier) -> list[str]:
    """The panel-age lines, or nothing. Each computed ONCE — the notes walk the whole mechanical
    layer, and the first cut called one twice in a single expression (a second full model_dump per
    rendered dossier, for a value it already had).

    TWO LINES since the staleness split: the panel age is what we could have refreshed and did not,
    and it GATES; the consensus age is what the street has not revised, and it never does."""
    out: list[str] = []
    note = _panel_age_note(d)
    if note:
        out.append(f"- **Panel age:** {note}")
    cnote = _consensus_age_note(d)
    if cnote:
        out.append(f"- **Consensus age:** {cnote}")
    return out


def _price_store_line(stamp: PriceStoreStamp | None) -> str:
    """The price store, named by its WORKTREE rather than its absolute path.

    THE READER NEEDS COMPARABILITY, NOT A FILESYSTEM TOUR. `.../mosaic-theory-wb/data/vinci.db`
    reads as noise; `mosaic-theory-wb` is what tells one page from another, and the full declared
    and resolved paths stay in `dossier.json` — the machine-complete tier, exactly where the
    three-tier rule puts the full record behind a curated value.

    THE ARROW IS THE SYMLINK, and it is worth a reader's attention: a worktree whose store points
    into another's is reading data it did not refresh, which is how a corroboration check once
    reported that "the store" could not see a price it was never actually asked for.
    """
    if stamp is None:
        # UNSTAMPED IS NOT UNKNOWN-STORE. Every dossier committed before this field predates it;
        # saying so beats printing nothing, which would read as "no store worth naming".
        return "unstamped — this dossier predates the store stamp"
    declared = Path(stamp.declared_path).parent.parent.name or stamp.declared_path
    resolved = Path(stamp.resolved_path).parent.parent.name or stamp.resolved_path
    where = declared if declared == resolved else f"{declared} → {resolved}"
    reach = f"reaching {stamp.frontier}" if stamp.frontier else "holding no bars"
    return f"`{where}` · {reach}"


def _record_reproduce_lines(d: Dossier) -> list[str]:
    """RECORD & REPRODUCE — everything needed to date, audit, or regenerate this document. Absorbs
    the old header meta (assembly stamp, model), the assembly-log caveat line, and the identifiers.
    The queued assembly-provenance stamp (STATE §5 item 1) lands here when built. The logged
    verdict itself is a ledger/frontend concern — this static md names where it lives."""
    proc = [c for c in d.caveats if _is_process_caveat(c)]
    out = [
        "## Record & reproduce",
        f"- **Data window:** screened as of {d.reference_date} · assembled "
        f"{_fmt_assembled(d.assembled_at)}",
        # (26a) the long form: the version PLUS what it names. The header carries the identifier so
        # a reader meets it; this carries the meaning, which is audit-tier context by the three-tier
        # rule and print-expanded regardless.
        f"- **Extraction:** {stamp_detail(d.extraction_version)}",
        # (spot audit) WHICH STORE, beside with-what and when. Rendered on every dossier and not
        # only when it looks unusual: `data/` is per-worktree by design, so two pages built the
        # same day can be struck days apart, and a reader cannot infer that from anything else on
        # the page. Absent stamps say "unstamped" rather than nothing — a dossier built before the
        # field and one built from an unknown store must not read alike.
        f"- **Price store:** {_price_store_line(d.price_store)}",
        # (item 1) The build's panel spread, rendered on EVERY dossier rather than only when it
        # breaches: the spread is context a reader needs in order to read a multiple at all. Nine
        # of eleven committed dossiers pair fundamentals 30+ days older than their price with
        # nothing on the page saying so.
        *_panel_age_line(d),
        "- **Synthesis:** " + (
            f"model `{d.llm_model}` — facts assembled mechanically; the synthesis frames, "
            "the analyst decides"
            if d.llm_model and d.synthesis is not None
            else "not assembled — mechanical layer only"),
        f"- **Identifiers:** CIK `{d.cik or '—'}`"
        + (f" · {d.exchange} : {d.ticker}" if d.exchange else f" · {d.ticker}"),
    ]
    if proc:
        out.append("- **Assembly log:** " + "; ".join(proc))
    out += [
        f"- **Re-run:** `python -m vinci dossier --ticker {d.ticker}` — regenerates every "
        "assembled fact from the same sources; committed values change only when the sources have.",
        "- **Verdict record:** logged via the CLI to the append-only decision ledger "
        "(entry price frozen at the screen date); this document displays state, never records it.",
        "",
    ]
    return out
