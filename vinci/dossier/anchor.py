"""R1 anchor — the mid-cycle-margin × own-history-EV/EBITDA fundamental, PERSISTED source-bound.

A committed, spot-INDEPENDENT anchor so triage is a cheap READ, not a live CIQ+EDGAR recompute. The
value math is the #150 mid-cycle block (:func:`midcycle.scenario_value`, EBITDA basis: EV = (EBIT +
D&A) × multiple) — this module only GATHERS the source-bound inputs and CALLS it, never reimplements
the arithmetic. Every input is cited; a gap is FLAGGED and the anchor marked inapplicable, never
fabricated (a silently-zeroed D&A would understate EBITDA → understate the anchor).

An ATTENTION FILTER, not a verdict: it re-rates the name to its OWN-history median multiple on a
NAIVE reported-median margin — cycle / one-off / mix adjustments are the analyst's job in the full
2:1 underwrite. Spot and reward-to-base are computed LIVE at triage, never stored here.
"""
from __future__ import annotations

import statistics as st
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from vinci.dossier import midcycle as mc
from vinci.edgar.client import _max_outstanding_debt
from vinci.edgar.concepts import (
    ConceptPoint,
    extract_points,
    latest_annual,
    latest_instant,
    points_for_tag,
)

# --- tunable constants (named, not magic) -----------------------------------------------------
ANCHOR_FIRM_MIN_YEARS = 7            # a margin spanning >=7 FYs plausibly covers a cycle -> "firm"
# The multiple leg is firm on the WINDOW it actually spans, not a raw close count: a band could show
# 20 closes yet span 20 years if annual-mislabelled (the 2026-07-21 incident). Firm ⇔ >=5 calendar
# years AND quarterly periodicity — never point-count alone.
ANCHOR_FIRM_MIN_MULT_YEARS = 5.0

_USD_M = 1e6
RECIPE_R1 = "R1_midcycle_margin_evebitda"
RECIPE_R2 = "R2_NEEDED"
RECIPE_UNKNOWN = "unknown"
RECIPE_UNRESOLVED = "ANCHOR_UNRESOLVED"

# The margin DENOMINATOR is chosen by what the tag MEANS (total company revenue), never by which
# series is longest. Longest-wins picked AORT's `Revenues`, which reports a partial/segment measure
# for FY2011–17 ($30–45M vs the 606 tag's $180–190M — ~4x) and manufactured 38–50% "margins" and a
# false 15.83% anchor median. Preference order: the post-2018 ASC-606 total-revenue standard first,
# legacy totals last. Fewer VALID years beats more invalid ones.
_REVENUE_TAG_PREFERENCE = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)
# Two tags reporting the SAME fiscal year this far apart are not two views of one number — one of
# them is not total revenue. Never silently pick: flag, and use the preferred (total) tag.
_TAG_CONFLICT_PCT = 0.25
DQ_REVENUE_TAG_CONFLICT = "revenue_tag_conflict"
_DILUTED_TAG = "WeightedAverageNumberOfDilutedSharesOutstanding"
_NOTE = (
    "ATTENTION FILTER, not a verdict. Even a firm anchor requires a full bear/base/bull 2:1 "
    "underwrite before any BUY. Spot and reward-to-base are computed live at triage, not stored "
    "here."
)


class AnchorMargin(BaseModel, frozen=True):
    """The own-history median operating margin used, with its coverage + confidence."""

    value: float | None
    unit: str = "fraction"
    basis: str
    source: str
    anchor_years: int
    confidence: str  # firm | weak


class AnchorMultiple(BaseModel, frozen=True):
    """The own-history median EV/EBITDA — READ from the committed valuation block, never
    recomputed (same series/statistic the valuation own-history band already committed)."""

    value: float | None
    unit: str = "EV/EBITDA"
    source: str = "valuation.own_history.median"
    history_quarters: int
    confidence: str  # firm | weak


class AnchorInput(BaseModel, frozen=True):
    """One source-bound scalar input: value + unit + basis + citation (source-stamped)."""

    value: float | None
    unit: str
    basis: str
    source: str


class Anchor(BaseModel, frozen=True):
    """The R1 anchor block — source-bound, spot-independent. Optional on the Dossier so committed
    JSON predating it round-trips byte-identically; the UI ignores it for now (data-only)."""

    recipe_hint: str                    # RECIPE_R1 | RECIPE_R2 | RECIPE_UNKNOWN | RECIPE_UNRESOLVED
    applicable: bool
    multiple_basis: str = mc.MULTIPLE_BASIS  # "EV/EBITDA"
    computed_at: datetime
    reason: str | None = None           # why inapplicable (R2 / gap), else None
    # Fail-loud data-quality channel. A fired flag CAPS overall_confidence at "weak" no matter how
    # many years/quarters underlie the stats — AORT read "firm" on fabricated years; never again.
    data_quality: str | None = None                  # e.g. DQ_REVENUE_TAG_CONFLICT
    data_quality_detail: list[str] = []              # which tags disagreed, by how much
    margin: AnchorMargin | None = None
    multiple: AnchorMultiple | None = None
    d_and_a: AnchorInput | None = None
    net_debt: AnchorInput | None = None
    diluted_shares: AnchorInput | None = None
    ltm_revenue: AnchorInput | None = None
    anchor_base_value_per_share: float | None = None   # the spot-independent fundamental
    anchor_ev_ebit: float | None = None
    overall_confidence: str | None = None  # firm | weak (the WEAKER of margin/multiple)
    note: str = _NOTE


# --- committed-artifact readers (work on the mechanical layer as a dict) -----------------------
def _own_history_multiple(mechanical: dict[str, Any]) -> dict[str, Any] | None:
    """The committed own-history EV/EBITDA band — READ, never recomputed. Returns the median, close
    count, calendar span, periodicity label and any data-quality flag so the caller can judge the
    multiple leg on the WINDOW it actually spans, not the raw point count. None when absent/UNKNOWN.

    ``window_span_years``/``periodicity`` are optional (pre-metadata committed JSON lacks them): a
    band without them is treated as span-UNKNOWN → the leg cannot be firm (the safe read)."""
    oh = ((mechanical.get("valuation") or {}).get("own_history") or {}).get("value")
    if not isinstance(oh, list):
        return None
    ev = next((r for r in oh if isinstance(r, dict) and "EBITDA" in str(r.get("metric", ""))), None)
    if not ev or ev.get("median") is None:
        return None
    span = ev.get("window_span_years")
    return {
        "median": float(ev["median"]),
        "n_closes": int(ev.get("n_closes") or 0),
        "span_years": float(span) if span is not None else None,
        "periodicity": ev.get("periodicity"),
        "data_quality": ev.get("data_quality"),
    }


def _fs_annual(mechanical: dict[str, Any]) -> dict[str, Any]:
    return ((mechanical.get("financial_summary") or {}).get("annual") or {}).get("value") or {}


def _last_actual_index(ann: dict[str, Any], n: int) -> int:
    """Index of the last ACTUAL (non-estimate) column of the annual table."""
    ise = ann.get("is_estimate") or []
    return max((i for i, e in enumerate(ise) if not e), default=n - 1)


def _ltm_revenue_from_fs(mechanical: dict[str, Any]) -> float | None:
    """LTM revenue ($M) = the last ACTUAL Revenue column of committed
    ``financial_summary.annual`` (the same base the render's LTM column shows)."""
    ann = _fs_annual(mechanical)
    rev = next((r for r in ann.get("rows") or [] if r.get("label") == "Revenue ($M)"), None)
    vals = (rev or {}).get("values") or []
    if not vals:
        return None
    idx = _last_actual_index(ann, len(vals))
    return float(vals[idx]) if 0 <= idx < len(vals) and vals[idx] is not None else None


def _margin_from_fs(mechanical: dict[str, Any]) -> tuple[float, int] | None:
    """FALLBACK margin: median(EBIT / Revenue) over the ACTUAL years of committed
    ``financial_summary.annual`` (short history; used only when EDGAR op-income is untagged)."""
    ann = _fs_annual(mechanical)
    rows = {r.get("label"): r for r in ann.get("rows") or []}
    ebit = (rows.get("EBIT ($M)") or {}).get("values") or []
    rev = (rows.get("Revenue ($M)") or {}).get("values") or []
    ise = ann.get("is_estimate") or []
    margins = [
        ebit[i] / rev[i]
        for i in range(min(len(ebit), len(rev)))
        if not (i < len(ise) and ise[i]) and ebit[i] is not None and rev[i]
    ]
    return (st.median(margins), len(margins)) if margins else None


# --- revenue-denominator selection (anchor-local; the shared resolver is NOT touched) ----------
def _revenue_candidates(facts: dict[str, Any]) -> dict[str, mc.AnnualSeries]:
    """Every candidate revenue tag that actually reports ANNUAL data, keyed by tag.

    Reads each tag EXPLICITLY so the choice below is OURS, not the shared alias resolver's —
    ``extract_points``/``CONCEPT_ALIASES`` and ``midcycle.annual_series`` (used by the mid-cycle
    block and its tests) are deliberately left unchanged. Reuses midcycle's point-folding rather
    than re-implementing XBRL parsing."""
    out: dict[str, mc.AnnualSeries] = {}
    for tag in _REVENUE_TAG_PREFERENCE:
        s = mc._series_from_points("revenue", tag, mc._annual_points(facts, tag, "revenue"))
        if s.by_year:
            out[tag] = s
    return out


def _total_revenue_series(facts: dict[str, Any]) -> tuple[mc.AnnualSeries | None, list[str]]:
    """The TOTAL-company revenue series chosen by PREFERENCE (never by longest coverage), plus any
    fail-loud disagreement notes.

    GUARD: when two candidate tags both report a fiscal year and disagree by more than
    ``_TAG_CONFLICT_PCT``, they are not two views of one number — one is not total revenue. Record
    the disagreement (the caller flags ``data_quality`` and caps confidence) and use the PREFERRED
    tag. No candidate at all → ``(None, [])``, and the caller marks the anchor UNRESOLVED rather
    than deriving a margin from a partial denominator."""
    cands = _revenue_candidates(facts)
    if not cands:
        return None, []
    tag = next(t for t in _REVENUE_TAG_PREFERENCE if t in cands)
    chosen = cands[tag]
    conflicts: list[str] = []
    for other, s in cands.items():
        if other == tag:
            continue
        for y in sorted(set(chosen.by_year) & set(s.by_year)):
            a, b = chosen.by_year[y], s.by_year[y]
            scale = max(abs(a), abs(b))
            if scale and abs(a - b) / scale > _TAG_CONFLICT_PCT:
                conflicts.append(f"FY{y}: {tag} {a / _USD_M:,.0f}M vs {other} {b / _USD_M:,.0f}M "
                                 f"({abs(a - b) / scale * 100:.0f}% apart)")
    return chosen, conflicts


# --- EDGAR source-bound extractors (fail-loud; a gap → None, never a fabricated zero) ----------
def _latest_dep_amort(facts: dict[str, Any]) -> tuple[float, str] | None:
    """Latest-FY consolidated D&A ($). Prefer the combined tag; else the source-stamped
    ``Depreciation + AmortizationOfIntangibleAssets`` split-sum (a filer like CNXC reports the two
    separately, not the combined tag). None when neither is tagged — flagged, never zero-filled."""
    p = latest_annual(extract_points(facts, "dep_amort"))
    if p:
        return p.value, "EDGAR companyfacts dep_amort (combined)"
    dep = latest_annual(points_for_tag(facts, "Depreciation"))
    am = latest_annual(points_for_tag(facts, "AmortizationOfIntangibleAssets"))
    # SAME fiscal period or nothing: summing an FY2025 depreciation into an FY2024 amortisation
    # would fabricate a D&A that never existed. This is the period-alignment discipline
    # ``edgar_fundamentals`` already applies to its own EBITDA add-back — misaligned → UNKNOWN
    # (flagged upstream), never a silently blended number.
    if dep and am and dep.period_end == am.period_end:
        fy = dep.fy or dep.period_end.year
        return dep.value + am.value, (
            f"EDGAR Depreciation + AmortizationOfIntangibleAssets (split, FY{fy})")
    return None


def _latest_point(facts: dict[str, Any], tag: str) -> ConceptPoint | None:
    """The most recent reported point for an explicit tag, by (period_end, filed).

    For a DURATION concept — the diluted weighted-average share count has no instant context —
    ``latest_instant`` would only reach it through its balance-sheet fallback, so the selection is
    made explicit here rather than resting on that fallback. The latest period IS the latest 10-Q's
    weighted average, which is the divisor the anchor wants."""
    pts = points_for_tag(facts, tag)
    return max(pts, key=lambda p: (p.period_end, p.filed)) if pts else None


def _sum_latest_tags(facts: dict[str, Any], *tags: str) -> float:
    """Sum the latest-instant value of each explicit tag — an absent LEASE tag is a legitimate 0
    (a filer without that lease type), unlike debt/cash which fail loud when wholly absent."""
    return sum(p.value for t in tags if (p := latest_instant(points_for_tag(facts, t))))


def _lease_inclusive_net_debt(facts: dict[str, Any]) -> tuple[float | None, str] | None:
    """Lease-inclusive net debt ($): total debt (LT + current) + finance leases + operating leases −
    cash, latest 10-Q. Returns ``(value_or_None, bridge)``; the tested under-capture guard flips it
    UNKNOWN (value None) when a single instrument exceeds 1.1× the extracted debt total (never a
    confident understatement — 'pull CIQ'). Wholly-absent debt/cash → the whole thing is None."""
    ltd = latest_instant(extract_points(facts, "long_term_debt"))
    dc = latest_instant(extract_points(facts, "debt_current"))
    cash = latest_instant(extract_points(facts, "cash"))
    if not (ltd or dc) or cash is None:
        return None
    td = (ltd.value if ltd else 0.0) + (dc.value if dc else 0.0)
    fin = _sum_latest_tags(facts, "FinanceLeaseLiabilityCurrent", "FinanceLeaseLiabilityNoncurrent")
    opl = _sum_latest_tags(facts, "OperatingLeaseLiabilityCurrent",
                           "OperatingLeaseLiabilityNoncurrent")
    bridge = (
        f"total debt {td / _USD_M:,.0f} + finance leases {fin / _USD_M:,.0f} + operating leases "
        f"{opl / _USD_M:,.0f} − cash {cash.value / _USD_M:,.0f} ($M)"
    )
    ref = max((p.period_end.isoformat() for p in (ltd, dc) if p), default=None)
    witness = _max_outstanding_debt(facts, ref)
    if witness and witness[0] > td * 1.10:
        return None, (bridge + f" — UNDER-CAPTURED: {witness[1]} ${witness[0] / _USD_M:,.0f}M "
                      "alone exceeds the extracted long-term+current total; pull CIQ")
    return td + fin + opl - cash.value, bridge


# --- the shared anchor computation (called by assembly AND the backfill writer) ----------------
def compute_anchor(mechanical: dict[str, Any], *, facts: dict[str, Any],
                   computed_at: datetime) -> Anchor:
    """The R1 anchor from SOURCE-BOUND inputs. ``mechanical`` is the mechanical layer as a dict
    (``model_dump`` at assembly, committed JSON at backfill); ``facts`` is EDGAR companyfacts.

    Every input is cited and fail-loud: a missing own-history multiple → inapplicable; a
    non-positive margin → the R2 (revenue-anchored) hint; an incomplete value bridge → applicable
    False with the per-input source stamps telling the human exactly what's missing. The base value
    is the #150 block's EBITDA-basis math, never reimplemented here."""
    mult = _own_history_multiple(mechanical)
    if mult is None:
        return Anchor(recipe_hint=RECIPE_UNKNOWN, applicable=False, computed_at=computed_at,
                      reason="own-history multiple missing (valuation.own_history.median absent)")
    mult_median, mult_qtrs = mult["median"], mult["n_closes"]
    mult_span, mult_period, mult_dq = mult["span_years"], mult["periodicity"], mult["data_quality"]

    # margin — median operating margin over the years the TOTAL-revenue tag covers. EBIT is aligned
    # to exactly those years by margin_anchor (it intersects the two series), so the ratio is always
    # one consistent basis. Fewer valid years beats more invalid ones.
    rev_s, conflicts = _total_revenue_series(facts)
    if rev_s is None:
        return Anchor(
            recipe_hint=RECIPE_UNRESOLVED, applicable=False, computed_at=computed_at,
            reason="no reliable total-revenue tag — refusing to derive a margin from a partial "
                   "denominator")
    oi_s = mc.annual_series(facts, "operating_income")  # single alias (OperatingIncomeLoss)
    ma = mc.margin_anchor(rev_s, oi_s)
    margin_val, margin_years = ma.median, ma.n_years
    margin_source = (f"EDGAR companyfacts {oi_s.tag} / {rev_s.tag} — reported median over "
                     f"{margin_years} FY") if margin_val is not None else ""
    data_quality = DQ_REVENUE_TAG_CONFLICT if conflicts else None
    forced_weak = bool(conflicts)
    if margin_val is None:
        fb = _margin_from_fs(mechanical)
        if fb is not None:
            margin_val, margin_years = fb
            margin_source = "financial_summary (short history) — EBIT/Revenue reported median"
            forced_weak = True

    # Two DIFFERENT facts, never lumped (the same fail-loud discipline edgar/client.py applies to
    # its own UNKNOWNs): a margin we could not COMPUTE is not a margin we computed and found
    # non-positive. The first is a data gap; only the second is an R2 (revenue-anchored) signal.
    if margin_val is None:
        return Anchor(
            recipe_hint=RECIPE_UNRESOLVED, applicable=False, computed_at=computed_at,
            reason=f"operating margin not computable — no fiscal year where both {oi_s.tag} and "
                   f"{rev_s.tag} report",
            data_quality=data_quality, data_quality_detail=conflicts)

    # POSITIVITY GUARD (minimal): a COMPUTED but non-positive margin → the revenue-anchored recipe.
    if margin_val <= 0:
        return Anchor(
            recipe_hint=RECIPE_R2, applicable=False, computed_at=computed_at,
            reason="no positive operating margin over available history — needs revenue-anchored "
                   "recipe",
            data_quality=data_quality, data_quality_detail=conflicts)

    # remaining source-bound inputs
    da = _latest_dep_amort(facts)
    nd = _lease_inclusive_net_debt(facts)
    dil = _latest_point(facts, _DILUTED_TAG)
    ltm_rev = _ltm_revenue_from_fs(mechanical)
    nd_val = nd[0] if nd else None

    # CONFIDENCE has a VALIDITY component, not just a count: any data-quality flag (or a fallback)
    # caps the margin leg — and therefore the overall — at "weak", however many years underlie it.
    m_conf = "firm" if (margin_years >= ANCHOR_FIRM_MIN_YEARS and not forced_weak) else "weak"
    # Multiple leg is firm on the WINDOW it spans + quarterly cadence — NOT the raw close count. A
    # band lacking span metadata (pre-refresh JSON) or flagged periodicity_mismatch cannot be firm.
    x_conf = ("firm" if (mult_span is not None and mult_span >= ANCHOR_FIRM_MIN_MULT_YEARS
                         and mult_period == "quarterly" and not mult_dq) else "weak")
    overall = "firm" if (m_conf == "firm" and x_conf == "firm") else "weak"
    if data_quality and margin_source:
        margin_source += f" — CAPPED weak: {data_quality}"

    margin_blk = AnchorMargin(value=round(margin_val, 6), basis="operating margin (EBIT / revenue)",
                              source=margin_source, anchor_years=margin_years, confidence=m_conf)
    multiple_blk = AnchorMultiple(value=mult_median, history_quarters=mult_qtrs, confidence=x_conf)
    da_blk = AnchorInput(value=(round(da[0] / _USD_M, 3) if da else None), unit="$M",
                         basis="consolidated latest FY",
                         source=(da[1] if da else "UNKNOWN — no D&A tag (combined or split)"))
    nd_blk = AnchorInput(value=(round(nd_val / _USD_M, 3) if nd_val is not None else None),
                         unit="$M", basis="lease-inclusive net debt (latest 10-Q)",
                         source=("EDGAR: " + nd[1]) if nd else "UNKNOWN — no debt/cash tag")
    dil_blk = AnchorInput(value=(dil.value if dil else None), unit="shares",
                          basis="diluted weighted-average (latest 10-Q)",
                          source=(f"EDGAR {_DILUTED_TAG}" if dil
                                  else "UNKNOWN — no diluted WA tag"))
    ltm_blk = AnchorInput(value=(round(ltm_rev, 3) if ltm_rev is not None else None), unit="$M",
                          basis="LTM revenue", source="committed financial_summary.annual (LTM)")

    # anchor base — the #150 block's EBITDA-basis value math; needs a complete bridge.
    base = ev_ebit = None
    if da and nd_val is not None and dil and dil.value > 0 and ltm_rev is not None:
        sv = mc.scenario_value(
            mc.Scenario(name="base", revenue=ltm_rev, margin=margin_val, multiple=mult_median,
                        source="anchor default", d_and_a=da[0] / _USD_M),
            net_debt=nd_val / _USD_M, shares=dil.value)
        base = round(sv.equity * _USD_M / dil.value, 4)
        ev_ebit = round(sv.ev_ebit, 4) if sv.ev_ebit is not None else None

    # a periodicity mismatch on the multiple band is its own fail-loud data-quality event; raise it
    # on the anchor (joining any revenue-tag conflict) so the flag rides with the number it taints.
    dq = data_quality
    detail = list(conflicts)
    if mult_dq:
        dq = f"{dq}+{mult_dq}" if dq else mult_dq
        detail.append(f"own_history multiple: {mult_dq} (periodicity {mult_period})")
    return Anchor(
        recipe_hint=RECIPE_R1, applicable=base is not None, computed_at=computed_at,
        reason=(None if base is not None else "R1 inputs incomplete — see per-input source stamps"),
        margin=margin_blk, multiple=multiple_blk, d_and_a=da_blk, net_debt=nd_blk,
        diluted_shares=dil_blk, ltm_revenue=ltm_blk,
        anchor_base_value_per_share=base, anchor_ev_ebit=ev_ebit, overall_confidence=overall,
        data_quality=dq, data_quality_detail=detail)


def insert_anchor_block(text: str, anchor: Anchor) -> str:
    """Append the ``anchor`` block as the LAST top-level field of a committed dossier.json TEXT,
    byte-preserving. The ONLY edit to existing bytes is a trailing comma on the previously-last
    field (unavoidable JSON syntax); every other field stays byte-for-byte identical. The backfill
    uses this rather than a model round-trip, because re-serializing older-schema dossiers drifts
    their other fields (new-default materialisation) — a corruption the string insert avoids."""
    body = anchor.model_dump_json(indent=2)  # a top-level-indented anchor object
    inner = "\n".join("  " + ln for ln in body.split("\n"))      # +2 so it sits at the field level
    field = '  "anchor": ' + inner.lstrip()                      # -> '  "anchor": {\n    …\n  }'
    end = text.rstrip()
    if not end.endswith("}"):
        raise ValueError("dossier.json is not a JSON object — refusing to insert the anchor")
    trailing = text[len(end):]                                   # preserved trailing whitespace
    head = end[:-1].rstrip()                                     # up to the last field's value
    return f"{head},\n{field}\n}}{trailing}"


def replace_valuation_fields(text: str, updates: dict[str, Any]) -> str:
    """Byte-preserving replace of one or more ``mechanical.valuation.<field>`` values in a committed
    dossier.json TEXT, leaving every OTHER field byte-for-byte identical.

    Takes the WHOLE cluster at once on purpose. ``own_history``, ``range_position``, ``ev_ebitda``
    and ``ev_ebitda_percentile_5y`` all derive from the SAME Multiples close series — the module
    guarantees they "can't drift" precisely because one loader feeds them. Refreshing one alone
    re-introduces the drift the guarantee exists to prevent (a band over 35 closes beside a string
    still saying "over 20 closes"), so the writer refuses to make that easy.

    A model round-trip drifts older-schema dossiers; a plain ``json.load``→``dump(indent=2,
    ensure_ascii=False)`` reproduces the committed bytes EXACTLY (verified), so it is the safe
    surgical path. Raises when a named field is absent (never silently no-ops)."""
    import json

    doc = json.loads(text)
    val = ((doc.get("mechanical") or {}).get("valuation"))
    if not isinstance(val, dict):
        raise ValueError("mechanical.valuation absent — refusing to refresh")
    for field, new in updates.items():
        if field not in val:
            raise ValueError(f"mechanical.valuation.{field} absent — refusing to refresh")
        val[field] = new
    out = json.dumps(doc, indent=2, ensure_ascii=False)
    return out + "\n" if text.endswith("\n") and not out.endswith("\n") else out


def anchor_changed(old: Anchor | None, new: Anchor) -> bool:
    """Did anything MATERIAL change? ``computed_at`` alone must never rewrite a committed artifact —
    a re-validation pass that moves nothing should leave every dossier byte-identical."""
    if old is None:
        return True
    a, b = old.model_dump(mode="json"), new.model_dump(mode="json")
    a.pop("computed_at", None)
    b.pop("computed_at", None)
    return a != b


_ANCHOR_FIELD = '\n  "anchor": {'


def replace_anchor_block(text: str, anchor: Anchor) -> str:
    """Byte-preserving REPLACE of an existing trailing anchor block (or a plain insert when absent).

    ``anchor`` is always the LAST field the model serialises, so the existing block is stripped back
    to the previous field and re-appended — every other field keeps its committed bytes, exactly as
    the #158 insert does."""
    i = text.rfind(_ANCHOR_FIELD)
    if i == -1:
        return insert_anchor_block(text, anchor)
    head = text[:i].rstrip()
    if head.endswith(","):
        head = head[:-1].rstrip()          # drop the separator; insert_anchor_block re-adds it
    trailing = text[len(text.rstrip()):]
    return insert_anchor_block(f"{head}\n}}{trailing}", anchor)
