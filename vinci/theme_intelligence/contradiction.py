"""Claim-level contradiction — does THIS claim contradict THAT one, or are they compatible?

Two theses can predict opposite outcomes on one value-chain node, mechanism and segment and still
rest on compatible evidence: HBM contract prices rising while conventional DRAM prices fall in the
same quarter are both true at once. A thesis is weakened only by evidence that DIRECTLY
contradicts its own: a pair of claims about

  the same PRODUCT       read from the verbatim quote against the taxonomy's `[[product]]`
                         vocabulary (the most specific term wins: "conventional DRAM" is not the
                         generic "DRAM"; a generic term against one of the products it covers is
                         AMBIGUOUS, never assumed equal)
  the same VARIABLE      price / demand / supply / volume / revenue / margin / capex /
                         inventory / valuation — read from the quote and the claim's metric.
                         Demand and supply are DIFFERENT variables: supply falling short and
                         demand rising are one reading, not two opposite ones; a shipped volume
                         against either is AMBIGUOUS
  the same PERIOD        the windows the claims state overlap (one unstated: AMBIGUOUS)
  the same GEOGRAPHY     overlapping (Global contains every region)

with OPPOSITE directions of change (rise vs fall, read from the quote; a quote saying both, or
neither, is AMBIGUOUS). Any dimension PROVABLY different, or the same direction, makes the pair
COMPATIBLE. Anything else is AMBIGUOUS — held for a human, never applied automatically.

Everything here is deterministic vocabulary over source text and structured fields: no model is
asked, and nothing is tuned on outcomes.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date

from vinci.theme_intelligence.config import Product
from vinci.theme_intelligence.schemas import Claim
from vinci.theme_intelligence.timewindow import window_of

CONTRADICTS, COMPATIBLE, AMBIGUOUS = "CONTRADICTS", "COMPATIBLE", "AMBIGUOUS"

#: the measured variable a claim speaks about (deterministic vocabulary, plain English)
VARIABLES: dict[str, tuple[str, ...]] = {
    "price": ("price", "prices", "pricing", "asp", "asps", "contract price", "spot price",
              "average selling price"),
    # demand and supply are two variables (2026-10-14: "supply will fall short" was read as the
    # opposite of "demand will rise" — the same bullish read filed as a contradiction)
    "demand": ("demand", "bit demand", "orders", "bookings"),
    "supply": ("supply", "bit supply", "output", "production"),
    "volume": ("shipment", "shipments", "units", "unit", "bits", "volume", "volumes"),
    "revenue": ("revenue", "revenues", "sales"),
    "margin": ("margin", "margins", "profitability"),
    "capex": ("capex", "capital expenditure", "capital expenditures", "capital spending"),
    "inventory": ("inventory", "inventories"),
    "valuation": ("multiple", "multiples", "valuation", "valuations", "p/e", "ev/sales",
                  "ev/ebitda", "share price", "share prices", "stock price", "index"),
}
_UP = re.compile(r"\b(?:ris(?:e|es|ing)|rose|risen|increas\w*|grow\w*|grew|higher|gain\w*|"
                 r"jump\w*|surg\w*|rebound\w*|recover\w*|accelerat\w*|climb\w*|up\b|tighten\w*|"
                 r"strengthen\w*|expand\w*)", re.I)
_DOWN = re.compile(r"\b(?:fall\w*|fell|declin\w*|drop\w*|lower|cut|cuts|decreas\w*|slump\w*|"
                   r"plung\w*|down\b|compress\w*|weaken\w*|soften\w*|eas(?:e|es|ing|ed)\b|"
                   r"contracted|contracting|contraction|shrink\w*|slow\w*)", re.I)
_NEG = re.compile(r"\b(?:not|no|never|neither|nor|without|unlikely)\b", re.I)
#: a shipped VOLUME is neither demand nor supply alone: against either it is unclear, never
#: "different" (which would make the pair compatible) nor "the same"
_RELATED = {frozenset({"volume", "demand"}), frozenset({"volume", "supply"})}
_SIDES = frozenset({"demand", "supply"})


@dataclass(frozen=True)
class PairVerdict:
    kind: str  # CONTRADICTS | COMPATIBLE | AMBIGUOUS
    challenger: str  # claim ids
    incumbent: str
    reasons: tuple[str, ...]  # what was compared, said plainly


@dataclass
class Assessment:
    """Every challenger claim against every incumbent claim."""

    pairs: list[PairVerdict] = field(default_factory=list)

    @property
    def contradicting(self) -> list[str]:
        """Challenger claims that directly contradict at least one incumbent claim."""
        return list(dict.fromkeys(p.challenger for p in self.pairs if p.kind == CONTRADICTS))

    @property
    def ambiguous(self) -> list[PairVerdict]:
        return [p for p in self.pairs if p.kind == AMBIGUOUS]

    @property
    def verdict(self) -> str:
        if self.contradicting:
            return CONTRADICTS
        return AMBIGUOUS if self.ambiguous else COMPATIBLE


def _text(c: Claim) -> str:
    return " ".join(x for x in (c.quote, c.metric or "", c.scope or "") if x)


def _matches(text: str, terms: Iterable[str]) -> list[tuple[int, int, str]]:
    out = []
    for t in terms:
        for m in re.finditer(rf"(?<![\w-]){re.escape(t)}(?![\w-])", text, re.I):
            out.append((m.start(), m.end(), t))
    return out


def products_of(c: Claim, products: Iterable[Product]) -> set[str]:
    """The products a claim names — the MOST SPECIFIC term wins: a match inside a longer match
    ("DRAM" inside "conventional DRAM") is not counted."""
    return products_in(_text(c), products)


def products_in(text: str, products: Iterable[Product]) -> set[str]:
    """`products_of` for a plain text (a risk statement)."""
    hits: list[tuple[int, int, str]] = []
    for p in products:
        hits += [(s, e, p.id) for s, e, _t in _matches(text, p.terms)]
    keep = [h for h in hits if not any(o[0] <= h[0] and h[1] <= o[1] and (o[1] - o[0])
                                       > (h[1] - h[0]) for o in hits)]
    return {pid for _s, _e, pid in keep}


def variables_of(c: Claim) -> set[str]:
    text = _text(c)
    return {v for v, terms in VARIABLES.items() if _matches(text, terms)}


def direction_of(c: Claim) -> str | None:
    """'up' / 'down' read from the verbatim quote; None when it says both, neither, or negates."""
    up, down = bool(_UP.search(c.quote)), bool(_DOWN.search(c.quote))
    if up == down or _NEG.search(c.quote):
        return None
    return "up" if up else "down"


def _product_relation(a: set[str], b: set[str],
                      covers: dict[str, set[str]]) -> tuple[str, str]:
    """('same' | 'different' | 'unclear', why)."""
    if not a or not b:
        return "unclear", "a claim names no product the taxonomy knows"
    if a & b:
        return "same", f"same product ({', '.join(sorted(a & b))})"
    wide_a = set().union(*(covers.get(x, {x}) for x in a))
    wide_b = set().union(*(covers.get(x, {x}) for x in b))
    if wide_a & wide_b:
        return "unclear", (f"a generic product against one it covers ({', '.join(sorted(a))} vs "
                           f"{', '.join(sorted(b))})")
    return "different", f"different products ({', '.join(sorted(a))} vs {', '.join(sorted(b))})"


def compare(ch: Claim, inc: Claim, *, products: list[Product], ref: date,
            overlap_geo: Callable[[str, str], bool], geo_ch: str, geo_inc: str) -> PairVerdict:
    """One challenger claim against one incumbent claim."""
    covers = {p.id: set(p.covers) for p in products if p.covers}
    reasons: list[str] = []
    unclear: list[str] = []
    rel, why = _product_relation(products_of(ch, products), products_of(inc, products), covers)
    if rel == "different":
        return PairVerdict(COMPATIBLE, ch.claim_id, inc.claim_id, (why,))
    (unclear if rel == "unclear" else reasons).append(why)
    va, vb = variables_of(ch), variables_of(inc)
    related = any(frozenset({x, y}) in _RELATED for x in va for y in vb)
    if va and vb and not va & vb and not related:
        return PairVerdict(COMPATIBLE, ch.claim_id, inc.claim_id, (
            f"different variables ({', '.join(sorted(va))} vs {', '.join(sorted(vb))})",))
    if va & vb:
        reasons.append(f"same variable ({', '.join(sorted(va & vb))})")
    elif related:
        unclear.append(f"related variables ({', '.join(sorted(va))} vs {', '.join(sorted(vb))}) "
                       f"— a shipped volume is neither demand nor supply alone")
    else:
        unclear.append("a claim names no measured variable")
    if va & vb & _SIDES and (va >= _SIDES or vb >= _SIDES):
        # "supply will fall short of demand": its one direction belongs to supply — read against
        # demand it would be the opposite of the same bullish reading
        unclear.append("a claim speaks of both demand and supply — which one its direction "
                       "belongs to is unclear")
    wa = window_of(ch.period, ref) or window_of(ch.quote, ref)
    wb = window_of(inc.period, ref) or window_of(inc.quote, ref)
    if wa and wb:
        if not (wa.start <= wb.end and wb.start <= wa.end):
            return PairVerdict(COMPATIBLE, ch.claim_id, inc.claim_id, (
                f"different periods ({wa.start}..{wa.end} vs {wb.start}..{wb.end})",))
        if (wa.to_date or wb.to_date) and (wa.to_date, wa.start) != (wb.to_date, wb.start):
            # a change accumulated SINCE X and a change over another span can both be true: a
            # rise since 2019 is not contradicted by a fall in 2026 (2026-10-15)
            return PairVerdict(COMPATIBLE, ch.claim_id, inc.claim_id, (
                f"different spans (a change since {(wa if wa.to_date else wb).start} vs one "
                f"over {(wb if wa.to_date else wa).start}..{(wb if wa.to_date else wa).end})",))
        reasons.append("overlapping periods")
    else:
        unclear.append("a claim states no period")
    if not overlap_geo(geo_ch, geo_inc):
        return PairVerdict(COMPATIBLE, ch.claim_id, inc.claim_id, (
            f"different geographies ({geo_ch} vs {geo_inc})",))
    reasons.append("overlapping geography")
    da, db = direction_of(ch), direction_of(inc)
    if da and db and da == db:
        return PairVerdict(COMPATIBLE, ch.claim_id, inc.claim_id, (
            f"the same direction ({da})",))
    if not (da and db):
        unclear.append("a quote states no single direction of change")
    if unclear:
        return PairVerdict(AMBIGUOUS, ch.claim_id, inc.claim_id, tuple(unclear + reasons))
    return PairVerdict(CONTRADICTS, ch.claim_id, inc.claim_id,
                       (*reasons, f"opposite directions ({da} vs {db})"))


def assess(challenger: list[Claim], incumbent: list[Claim], *, products: list[Product],
           ref: date, overlap_geo: Callable[[str, str], bool], geo_ch: str,
           geo_inc: str) -> Assessment:
    """Every challenger claim against every incumbent claim. A claim restating an observation
    already compared (same economic evidence from the same origin) is compared once."""
    out = Assessment()
    seen: set[tuple[str, str]] = set()
    for c in challenger:
        for i in incumbent:
            key = (_evidence_key(c), _evidence_key(i))
            if key in seen:
                continue
            seen.add(key)
            out.pairs.append(compare(c, i, products=products, ref=ref, overlap_geo=overlap_geo,
                                     geo_ch=c.geography or geo_ch, geo_inc=i.geography or geo_inc))
    return out


def _evidence_key(c: Claim) -> str:
    """The underlying economic observation and its original source — a claim restating the
    same measure and value from the same origin is the same evidence."""
    return f"{c.measure_key}|{c.value if c.value is not None else c.value_text}|{c.origin_id}"
