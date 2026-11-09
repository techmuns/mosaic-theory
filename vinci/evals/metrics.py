"""Deterministic fidelity metrics for synthesis prose — $0, run on any draw or gold claim.

Specification: the design record (`docs/records/2026-11-06-synthesis-eval-harness-design.md` §4).
Each metric reads ONE prose unit (`units.Unit`) against ITS page's own facts (`PageContext`) and
returns its hits — the phrase, and the fact that makes it wrong. Every fact is read from a
STRUCTURED value: a row's ``values``, a Sourced field's ``status``, the stated numbers production's
own trace collects. No display cell is parsed and no forward return is read.

THE ONE-PARSER RULE. Figures are found and read as written by production's own helpers
(``synthesis._claim_figure_ends``, ``synthesis._written``, ``synthesis._stated_numbers``), and the
material-direction metric IS production's ``material_direction_flags``. A second parser of the
same text is the bug class CLAUDE.md names; these metrics borrow, never re-implement.

THE METRICS: M-LABEL (a code-written label repeated against the page's facts), M-SIGN (#921's
material-direction flag), M-PATH (monotone wording against the page's series), M-ABSENT (a figure
the facts do not state; transcript-only or nowhere), M-ECHO (the prompt's instruction words in
the prose), M-GAP (a gap the page's gap test does not type a change, framed as a risk or carried
by a bear point — on the pages whose gap types are frozen). M-SIZE (prompt size per section)
reads a request, not a unit.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import cache, cached_property
from pathlib import Path
from typing import Any

from vinci.dossier import synthesis as syn
from vinci.dossier.mechanical import TRAILING_ONLY_NOTE
from vinci.dossier.schemas import DecisiveQuestion, MechanicalLayer, Synthesis
from vinci.evals.panel import has_forward_basis
from vinci.evals.units import Unit

I = re.IGNORECASE  # noqa: E741 — the flag, as #920's scorer named it


@dataclass(frozen=True)
class Hit:
    metric: str
    unit: str
    family: str
    phrase: str
    detail: str = ""


@dataclass
class PageContext:
    """One page's facts, read once. ``request`` (a `replay.Request`) is needed by M-ECHO only;
    ``transcript`` by M-ABSENT's transcript split only."""

    page: dict[str, Any]
    mech: MechanicalLayer
    transcript: str | None = None
    request: Any | None = None
    #: The page's git blob, where the caller read the page by it (the frozen panel's): M-GAP is
    #: defined only on a page whose blob is the one its gap types were frozen on.
    blob: str | None = None

    @cached_property
    def dumped(self) -> dict[str, Any]:
        d: dict[str, Any] = self.mech.model_dump(mode="json")
        return d

    @cached_property
    def forward_basis(self) -> bool:
        return has_forward_basis(self.page)

    @cached_property
    def guidance_rows(self) -> bool:
        g = (self.dumped.get("catalyst_path") or {}).get("guidance_bridge_rows") or {}
        return bool(g.get("value")) if isinstance(g, dict) else bool(g)

    @cached_property
    def no_gap_down(self) -> bool:
        dc = self.dumped.get("drawdown_cause") or {}
        return (dc.get("gap_down_dates") or {}).get("status") != "present"

    @cached_property
    def segment_profit(self) -> bool:
        """The page states a segment profit, on a filer that reports more than one segment (a
        single-segment filer has no segment EBITDA to disclose, so saying so is true)."""
        conc = self.dumped.get("concentration") or {}
        note = str((conc.get("segment_ebitda") or {}).get("note") or "")
        if note.startswith("single-segment"):
            return False
        if (conc.get("segment_profit") or {}).get("status") == "present":
            return True
        rows = (self.dumped.get("operating_drivers") or {}).get("rows") or []
        return any(_SEGMENT_PROFIT_FACT.search(" ".join(str(r.get(k) or "") for k in
                                                         ("metric", "verbatim",
                                                          "following_context")))
                   for r in rows)

    @cached_property
    def cash_and_cfo(self) -> bool:
        """An LTM CFO in the annual table AND a cash balance in the EV bridge or the implied
        valuation's bridge (read as present, not parsed)."""
        cols, rows = self.annual
        cfo = rows.get("CFO ($M)") or []
        ltm = next((i for i, c in enumerate(cols) if c.startswith("LTM")), None)
        has_cfo = ltm is not None and ltm < len(cfo) and cfo[ltm] is not None
        bridge = (self.dumped.get("implied_valuation") or {}).get("bridge")
        return has_cfo and bool(self.page.get("ev_bridge") or bridge)

    @cached_property
    def pe_history(self) -> bool:
        oh = ((self.dumped.get("valuation") or {}).get("own_history") or {}).get("value") or []
        return any("EPS" in str(s.get("metric")) and s.get("percentile") is not None for s in oh)

    @cached_property
    def stated(self) -> tuple[list[float], list[float], set[float], set[float]]:
        """The numbers the pre-synthesis layer states, ``primary_source`` included, LESS its
        date-indexed series (`_without_series`: a claim's figure meeting a daily price or a
        quarterly multiple is a coincidence, not the fact it reads). Returns (sorted |numeric
        leaves|, sorted |figures written in fact text, in base units|, years, ranks): a numeric
        leaf is matched at its unit's scales, a figure written in a fact's own text ("$578
        billion") at face — both read by production's own helpers."""
        tree = _without_series(self.mech.model_dump())
        nums = syn._FactNumbers()
        syn._stated_numbers(tree, nums)
        leaves: list[float] = []
        written: list[float] = []
        _collect(tree, leaves, written)
        return sorted(leaves), sorted(written), nums.years, nums.ranks

    @cached_property
    def direction_baseline(self) -> frozenset[str]:
        """The material-direction flags an EMPTY synthesis raises — claim-independent notices."""
        return frozenset(syn.material_direction_flags(_carrier(""), self.mech))

    @cached_property
    def facts_norm(self) -> str:
        """Every string the layer carries, folded as `_norm` folds a quote."""
        strings: list[str] = []

        def walk(o: Any) -> None:
            if isinstance(o, str):
                strings.append(o)
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, (list, tuple)):
                for v in o:
                    walk(v)

        walk(self.mech.model_dump(mode="json"))
        return " | ".join(_norm(x) for x in strings)

    @cached_property
    def transcript_norm(self) -> str:
        return _norm(self.transcript or "")

    @cached_property
    def annual(self) -> tuple[list[str], dict[str, list[float | None]]]:
        fs = self.dumped.get("financial_summary") or {}
        tbl = (fs.get("annual") or {}).get("value") or {}
        rows = {str(r["label"]): list(r.get("values") or []) for r in tbl.get("rows") or []}
        return list(tbl.get("columns") or []), rows


#: A list this long whose items are dated NUMBERS only is a price or multiple series
#: (`_without_series`) — daily prices, quarterly multiples. Shorter dated lists (a consensus
#: history, revision events) and any list whose items carry text stay: claims cite their points.
SERIES_MIN_POINTS = 30
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _numeric(v: Any) -> bool:
    return v is None or (isinstance(v, (int, float)) and not isinstance(v, bool))


def _dated(item: Any) -> bool:
    """A dated point carrying numbers and nothing else."""
    if isinstance(item, dict):
        d = item.get("date")
        return (isinstance(d, str) and bool(_ISO_DATE.match(d))
                and all(_numeric(v) for k, v in item.items() if k != "date"))
    if isinstance(item, (list, tuple)) and item:
        return (isinstance(item[0], str) and bool(_ISO_DATE.match(item[0]))
                and all(_numeric(v) for v in item[1:]))
    return False


def _collect(o: Any, leaves: list[float], written: list[float]) -> None:
    """Numeric leaves as stored, and each figure a string leaf WRITES (``_WRITTEN``, dates and
    identifiers blanked as ``_stated_numbers`` blanks them), in base units."""
    if o is None or isinstance(o, bool):
        return
    if isinstance(o, (int, float)):
        leaves.append(abs(float(o)))
    elif isinstance(o, str):
        rest = syn._BARE_YEAR.sub(" ", syn._DATE_OR_ID.sub(" ", o))
        for m in syn._WRITTEN.finditer(rest):
            if (w := syn._written(m.group(0))) is not None:
                written.append(abs(w.value))
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in syn._ID_KEYS and not str(k).endswith("_id"):
                _collect(v, leaves, written)
    elif isinstance(o, (list, tuple)):
        for v in o:
            _collect(v, leaves, written)


def _without_series(o: Any) -> Any:
    """``o`` with every list of at least ``SERIES_MIN_POINTS`` dated points removed."""
    if isinstance(o, dict):
        return {k: _without_series(v) for k, v in o.items()}
    if isinstance(o, list):
        if len(o) >= SERIES_MIN_POINTS and all(_dated(x) for x in o):
            return []
        return [_without_series(x) for x in o]
    return o


# ------------------------------------------------------------------------------------ M-LABEL

_SEGMENT_PROFIT_FACT = re.compile(
    r"operating (?:profit|income)|contribution margin|segment (?:profit|margin|operating)", I)

#: The trailing-only family reads the caveat's text from `mechanical.TRAILING_ONLY_NOTE`, split into
#: its clauses — never a retyped copy, which `test_sleeves` forbids. It is the SCORER's import,
#: never the code under test's (a comparison scores in its own process), and it is FIXED: the
#: family counts this wording whatever a later code writes (coordinator, 2026-11-07, for #923's
#: measurement — CAND prose echoing the OLD label must still count). The sha256 below is that
#: wording; a changed constant makes the scorer refuse to load, and moving it is a metric change
#: (RUNBOOKS §n step 7: the gold re-scored, DEV vs TEST stated again).
TRAILING_ONLY_SHA256 = "cbf0eed933cf5404bff6b923ae0a221ea785933982c0b13ccd931e604128229f"
if hashlib.sha256(TRAILING_ONLY_NOTE.encode()).hexdigest() != TRAILING_ONLY_SHA256:
    raise RuntimeError("mechanical.TRAILING_ONLY_NOTE is not the wording M-LABEL's trailing-only "
                       "family was defined on: a metric change (RUNBOOKS §n step 7), never silent")
_NOTE_PARTS = [p.strip() for p in re.split(r"[;—]", TRAILING_ONLY_NOTE) if p.strip()]


def _loose(phrase: str) -> str:
    """``phrase`` as a pattern that tolerates a hyphen or any spacing between its words."""
    return r"\b" + r"[-\s]+".join(re.escape(w) for w in phrase.split()) + r"\b"


LABEL_FAMILIES: dict[str, re.Pattern[str]] = {
    "trailing-only": re.compile(
        "|".join([*(_loose(p) for p in _NOTE_PARTS),
                  r"temporarily depressed (?:level )?(?:from|vs\.?|versus|or) (?:a )?permanently "
                  r"impaired|cannot (?:by itself )?distinguish (?:a )?temporarily depressed|"
                  r"until a forward basis|without a forward (?:basis|anchor)"]), I),
    "bleed": re.compile(r"\bbleed\w*", I),
    "no-adjusted-forward": re.compile(
        r"ev_ebitda_adjusted_fwd|adjusted_eps\b[^.;]{0,24}UNKNOWN|\bno (?:revised |post-drawdown |"
        r"forward[-/ ]?|adjusted[-/ ]?)+(?:basis|guid\w*|EV/EBITDA|EBITDA|EPS)\b|\bno (?:revised )?"
        r"(?:post-drawdown )?guidance (?:was )?(?:parsed|available|readable)", I),
    "segment-undisclosed": re.compile(
        r"segment[- ](?:level )?(?:EBITDA|profit\w*|operating[- ]profit|margins?|profitability)"
        r"\b[^.;]{0,40}?\b(?:not|un|never)[- ]?disclosed|\bno segment[- ](?:level )?(?:EBITDA|"
        r"profit\w*|operating|margin)|segment_(?:ebitda|profit)\b|\bNOT segment EBITDA", I),
    "runway-not-derivable": re.compile(
        r"runway (?:is )?(?:not|un)[- ]?(?:derivable|derived|assessable|assessed)|"
        r"no runway(?:/burn)?[- ](?:adjusted )?(?:cash )?(?:horizon|derived)", I),
    "pe-percentile-blocked": re.compile(
        r"percentile cannot be (?:built|computed)|(?:share-basis change|stock split)[^.;]{0,80}"
        r"(?:percentile|range)|P/E (?:range|percentile)[^.;]{0,40}not (?:computable|available|"
        r"built)", I),
}
_GRADUAL = re.compile(r"\bgradual\w*", I)
#: "gradual" counts in a clause that describes a DECLINE and no rise ("a gradual advance" is not
#: a bleed).
_PRICE_CLAUSE = re.compile(r"declin\w*|\bfell\b|\bfall\w*|de-?rat\w*|sell-?off|slide|erosion|"
                           r"grind|decay|\bdrop\w*|bleed", I)
_RISE_CLAUSE = re.compile(r"advanc\w*|\bris\w*|\brose\b|rall\w*|\bgain\w*|climb\w*|recover\w*",
                          I)
_CLAUSE_SPLIT = re.compile(r";|\s[—–]\s|\.\s+(?=[A-Z])")


def _clauses(text: str) -> list[str]:
    return [c for c in _CLAUSE_SPLIT.split(text) if c.strip()]


def label_echo(u: Unit, ctx: PageContext) -> list[Hit]:
    out: list[Hit] = []
    conditions: dict[str, tuple[bool, str]] = {
        "trailing-only": (ctx.forward_basis, "the page carries a CIQ forward multiple"),
        "bleed": (ctx.no_gap_down, "the detector measures single-day drops only; gradualness is "
                                   "never measured"),
        "no-adjusted-forward": (ctx.forward_basis or ctx.guidance_rows,
                                "the page carries a forward multiple or guidance-bridge rows"),
        "segment-undisclosed": (ctx.segment_profit, "the page states a segment profit"),
        "runway-not-derivable": (ctx.cash_and_cfo, "the page states a cash balance and an LTM "
                                                    "CFO, from which a runway follows"),
        "pe-percentile-blocked": (ctx.pe_history,
                                  "valuation.own_history carries a P/E series with a percentile"),
    }
    for fam, rx in LABEL_FAMILIES.items():
        holds, why = conditions[fam]
        if holds and (m := rx.search(u.text)):
            out.append(Hit("M-LABEL", u.id, fam, m.group(0), why))
    if ctx.no_gap_down and not any(h.family == "bleed" for h in out):
        for c in _clauses(u.text):
            if (m := _GRADUAL.search(c)) and _PRICE_CLAUSE.search(c) and not _RISE_CLAUSE.search(c):
                out.append(Hit("M-LABEL", u.id, "bleed", m.group(0), conditions["bleed"][1]))
                break
    return out


# ------------------------------------------------------------------------------------- M-SIGN

def _carrier(text: str) -> Synthesis:
    return Synthesis(evidence_balance="", bull_points=[], bear_points=[], twin_reference_cases=[],
                     decisive_question=DecisiveQuestion(question="", evidence_for=[],
                                                        evidence_against=[]),
                     key_unknowns=[text] if text else [])


def _cut(text: str, n: int) -> str:
    """``text`` to ``n`` characters, saying so when it was cut (CLAUDE.md: a truncated output
    prints its own truncation)."""
    return text if len(text) <= n else f"{text[:n]}… [cut, {len(text):,} chars]"


def material_direction(u: Unit, ctx: PageContext) -> list[Hit]:
    """Production's ``material_direction_flags`` on a one-unit carrier; the flags an EMPTY carrier
    also raises (a figure "not checked") are claim-independent and subtracted as a set."""
    flags = syn.material_direction_flags(_carrier(u.text), ctx.mech)
    return [Hit("M-SIGN", u.id, "material-direction", _cut(f, 160)) for f in flags
            if f not in ctx.direction_baseline]


# ------------------------------------------------------------------------------------- M-PATH

#: #920 §4's PATH regex, verbatim (its frozen scorer) — monotone wording.
PATH_WORDS = re.compile(
    r"\bevery\s+(?:step|year|period|single\s+year)\b|\bwithout\s+(?:interruption|a\s+(?:break|dip|"
    r"down\s?-?year|reversal|pause))\b|\bnever\s+(?:revers\w*|dipp?\w*|declin\w*|fell|fall\w*|"
    r"contract\w*)\b|\buninterrupted\w*|\bunbroken\b|\bmonoton\w*|\byear\s+after\s+year\b|"
    r"\bstraight[- ]line\b|\bin\s+every\s+(?:year|period)\b|\bconsecutive\b", I)

#: A series named in prose → the annual row(s) it is read from: one row, or (numerator,
#: denominator) for a margin. Order matters: a margin is matched before its numerator's name.
SERIES: tuple[tuple[str, re.Pattern[str], tuple[str, ...]], ...] = (
    ("EBIT margin", re.compile(r"\b(?:EBIT|operating)\s+margins?\b", I),
     ("EBIT ($M)", "Revenue ($M)")),
    ("EBITDA margin", re.compile(r"\bEBITDA\s+margins?\b|(?<!gross )(?<!EBIT )(?<!operating )"
                                 r"\bmargins?\b", I), ("EBITDA ($M)", "Revenue ($M)")),
    ("EBITDA", re.compile(r"\bEBITDA\b(?!\s+margin)", I), ("EBITDA ($M)",)),
    ("EBIT", re.compile(r"\bEBIT\b(?!\s+margin)|\boperating\s+(?:income|profit)\b", I),
     ("EBIT ($M)",)),
    ("revenue", re.compile(r"\brevenues?\b|\bsales\b|\btop[- ]line\b", I), ("Revenue ($M)",)),
    ("net income", re.compile(r"\bnet\s+income\b|\bnet\s+earnings\b", I), ("Net income ($M)",)),
    ("EPS", re.compile(r"\bEPS\b", I), ("EPS (GAAP, dil.)",)),
    ("FCF", re.compile(r"\bFCF\b|\bfree\s+cash\s+flow\b", I), ("FCF ($M)",)),
    ("CFO", re.compile(r"\bCFO\b|\boperating\s+cash\s+flow\b|\bOCF\b", I), ("CFO ($M)",)),
)
_RISE = re.compile(r"\bris\w*|\brose\b|\bgr[eo]w\w*|\bclimb\w*|\bcompound\w*|\bexpand\w*|"
                   r"\bincreas\w*|\bimprov\w*|\baccelerat\w*|\bhigher\b|\bup\b", I)
_FALL = re.compile(r"\bfall\w*|\bfell\b|\bdeclin\w*|\bcontract\w*|\bshr[iau]nk\w*|\bcompress\w*|"
                   r"\blower\b|\bdown\b|\bdeteriorat\w*|\berod\w*", I)
_HEDGE = re.compile(r"\b(?:almost|nearly|largely|mostly|broadly|virtually)\s*$", I)
_FY = re.compile(r"\bFY\s?'?(\d{4}|\d{2})\b|\bLTM\b", I)
#: A step against the claimed direction smaller than this share of the series' largest magnitude
#: (margins: of 1.0, i.e. half a point) is rounding, not a reversal a reader would see.
PATH_TOLERANCE = 0.005


def _col_year(col: str) -> int | None:
    m = re.match(r"FY\s?(\d{4}|\d{2})\b", col)
    if m is None:
        return None
    y = int(m.group(1))
    return y if y > 100 else 2000 + y


def _series(ctx: PageContext, rows: tuple[str, ...]) -> list[tuple[str, float]]:
    cols, table = ctx.annual
    if any(r not in table for r in rows):
        return []
    out: list[tuple[str, float]] = []
    for i, c in enumerate(cols):
        if c.rstrip().endswith("E") or re.search(r"\d{2}E\b", c):
            continue  # an estimate column
        vals = [table[r][i] if i < len(table[r]) else None for r in rows]
        if any(v is None for v in vals):
            continue
        if len(vals) == 1:
            out.append((c, float(vals[0])))  # type: ignore[arg-type]
        elif vals[1]:
            out.append((c, float(vals[0]) / float(vals[1])))  # type: ignore[arg-type]
    return out


def _span(points: list[tuple[str, float]], clause: str) -> list[tuple[str, float]]:
    years = {(2000 + int(m.group(1)) if m.group(1) and len(m.group(1)) == 2
              else int(m.group(1)) if m.group(1) else 9999) for m in _FY.finditer(clause)}
    if len(years) < 2:
        return points
    lo, hi = min(years), max(years)
    keep = []
    for c, v in points:
        y = 9999 if c.startswith("LTM") else _col_year(c)
        if y is not None and lo <= y <= hi:
            keep.append((c, v))
    return keep


def path_monotone(u: Unit, ctx: PageContext) -> list[Hit]:
    out: list[Hit] = []
    for clause in _clauses(u.text):
        mw = PATH_WORDS.search(clause)
        if mw is None or _HEDGE.search(clause[max(0, mw.start() - 14):mw.start()]):
            continue  # "almost unbroken" hedges the path it describes
        taken = clause
        for name, rx, rows in SERIES:
            if not rx.search(taken):
                continue
            taken = rx.sub(" ", taken)  # a margin's name is not also its numerator's
            pts = _span(_series(ctx, rows), clause)
            if len(pts) < 3:
                continue
            rise, fall = bool(_RISE.search(clause)), bool(_FALL.search(clause))
            up = rise if rise != fall else pts[-1][1] >= pts[0][1]
            scale = 1.0 if len(rows) == 2 else max(abs(v) for _, v in pts) or 1.0
            for (c0, v0), (c1, v1) in zip(pts, pts[1:], strict=False):
                step = v1 - v0
                if (step < 0 if up else step > 0) and abs(step) > PATH_TOLERANCE * scale:
                    out.append(Hit("M-PATH", u.id, name, mw.group(0),
                                   f"{name} {c0} {v0:,.4g} → {c1} {v1:,.4g} against "
                                   f"'{'rise' if up else 'fall'}'"))
                    break
    return out


# ----------------------------------------------------------------------------------- M-ABSENT

_APPROX = re.compile(r"(?:~|≈|\babout|\broughly|\bnearly|\bapproximately|\baround|\balmost)\s*\$?$",
                     I)
#: The scales a figure may be stated at, by how it is WRITTEN: a percent as a fraction or as
#: itself; money written with a scale word ("$1.6B", "$806M") against the $M the tables state, or
#: at face; money without one ("$45.60") at face; a multiple or a plain number at face (a plain
#: number with a scale word, "29.6 million shares", also against $M-style tables).
_SCALES: dict[str, tuple[float, ...]] = {"pct": (1.0, 100.0), "x": (1.0,), "rank": (1.0, 100.0)}


def _scales(w: syn._Written) -> tuple[float, ...]:
    if w.unit in _SCALES:
        return _SCALES[w.unit]
    return (1.0, 1e6) if w.scale != 1.0 else (1.0,)
APPROX_WIDTH = 0.05


#: The second figure of a range carries the scale word for both ("$80–83B", "$2.25 to $2.5bn").
_RANGE_SCALE = re.compile(r"\s*(?:–|—|-|to)\s*\$?\d[\d,]*(?:\.\d+)?\s*"
                          r"(thousand|million|billion|trillion|mn|bn|tn|[kmbt])(?![a-z])", I)


def _written_at(text: str, end: int) -> tuple[syn._Written, str, int] | None:
    """The figure whose digits end at ``end``, read as written by production's ``_written``; the
    first figure of a range borrows the second's scale word."""
    for m in syn._NUM.finditer(text):
        if m.end() != end:
            continue
        start = m.start()
        while start > 0 and text[start - 1] in "$-−+ " and m.start() - start < 3:
            start -= 1
        lit = text[start:m.end() + 16]
        if (r := _RANGE_SCALE.match(text, m.end())) is not None:
            lit = text[start:m.end()] + r.group(1)
        w = syn._written(lit)
        if w is not None:
            return w, m.group(0), m.start()
    return None


def _meets(sorted_vals: list[float], lo: float, hi: float) -> bool:
    i = bisect.bisect_left(sorted_vals, lo - 1e-12)
    return i < len(sorted_vals) and sorted_vals[i] <= hi + 1e-12


def _found(w: syn._Written, approx: bool, ctx: PageContext, literal: str) -> bool:
    leaves, written, years, ranks = ctx.stated
    a = abs(w.value)
    half = max(w.half, APPROX_WIDTH * a) if approx else w.half
    if (w.unit == "plain" and "." not in literal and "," not in literal and 1900 <= a <= 2100
            and a in years):
        return True
    if w.unit == "rank" and a in ranks:
        return True
    if _meets(written, a - half, a + half):
        return True
    return any(_meets(leaves, (a - half) / s, (a + half) / s) for s in _scales(w))


def _in_transcript(literal: str, transcript: str | None) -> bool:
    if not transcript:
        return False
    plain = literal.replace(",", "")
    for lit in {literal, plain}:
        if re.search(rf"(?<![\d.,]){re.escape(lit)}(?![\d]|[.,]\d)", transcript):
            return True
    return False


#: A quoted span of at least this many words is checked against the facts' own text.
QUOTE_MIN_WORDS = 3
#: Double quotes, curly quotes, or straight single quotes that open after no word character and
#: close before none — so a possessive ("CIQ's … FY24's") is never read as a quotation.
_QUOTED = re.compile(r"“([^”]{8,240})”|\"([^\"]{8,240})\"|‘([^’]{8,240})’"
                     r"|(?<![\w])'([^']{8,240})'(?![\w])")


def _norm(text: str) -> str:
    return " ".join(_tokens(text))


def absent_quotes(u: Unit, ctx: PageContext) -> list[Hit]:
    """A phrase the unit QUOTES that no fact's text contains (case, punctuation and spacing
    folded) — management words the facts never carried: transcript-only, or nowhere."""
    out: list[Hit] = []
    for m in _QUOTED.finditer(u.text):
        span = next(g for g in m.groups() if g is not None)
        q = _norm(span)
        if len(q.split()) < QUOTE_MIN_WORDS or q in ctx.facts_norm:
            continue
        where = ("transcript-only" if ctx.transcript and q in ctx.transcript_norm else "nowhere")
        out.append(Hit("M-ABSENT", u.id, f"quote:{where}", _cut(span, 80)))
    return out


def absent_number(u: Unit, ctx: PageContext) -> list[Hit]:
    out: list[Hit] = absent_quotes(u, ctx)
    for _v, end in syn._claim_figure_ends(u.text):
        got = _written_at(u.text, end)
        if got is None:
            continue
        w, literal, start = got
        approx = bool(_APPROX.search(u.text[max(0, start - 16):start]))
        if _found(w, approx, ctx, literal):
            continue
        where = "transcript-only" if _in_transcript(literal, ctx.transcript) else "nowhere"
        out.append(Hit("M-ABSENT", u.id, where, literal,
                       f"{w.unit} {w.value:,.6g} ± {w.half:,.3g}{' (approx)' if approx else ''}"))
    return out


# ------------------------------------------------------------------------------------- M-ECHO

_WORD = re.compile(r"[a-z]+")
ECHO_N = 5


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower().replace("’", "").replace("'", ""))


def shingles(text: str, n: int = ECHO_N) -> set[tuple[str, ...]]:
    t = _tokens(text)
    return {tuple(t[i:i + n]) for i in range(len(t) - n + 1)}


@dataclass
class EchoIndex:
    """The instruction shingles of one request: in its instruction text, in none of its facts."""

    instruction: set[tuple[str, ...]] = field(default_factory=set)

    @classmethod
    def of(cls, request: Any, ctx: PageContext) -> EchoIndex:
        import json

        sections = user_sections(request.user)
        facts_text = sections.get("facts", "") + sections.get("transcripts", "")
        facts_text += json.dumps(ctx.mech.model_dump(mode="json"), default=str)
        if ctx.transcript:
            facts_text += ctx.transcript
        instr = request.system + json.dumps(request.kwargs.get("tools"))
        instr += "".join(v for k, v in sections.items() if k not in ("facts", "transcripts"))
        return cls(shingles(instr) - shingles(facts_text))


def instruction_echo(u: Unit, ctx: PageContext, index: EchoIndex) -> list[Hit]:
    hits = sorted(shingles(u.text) & index.instruction)
    return [Hit("M-ECHO", u.id, "instruction", " ".join(hits[0]),
                f"{len(hits)} instruction shingle(s)")] if hits else []


# ------------------------------------------------------------------------------------- M-SIZE

_HEADER = re.compile(r"\n\n=== (.+?) ===\n")
SECTION_NAMES = (("PRIMARY-SOURCE", "primary_source"), ("OPERATING DRIVERS", "operating_drivers"),
                 ("Earnings-call transcripts", "transcripts"),
                 ("MATERIAL FIGURES", "material_figures"), ("THE DRAWDOWN WHEN", "drawdown_anchor"))


def user_sections(user: str) -> dict[str, str]:
    """USER split on the prompt's own section headers: ``facts`` (the opening and the facts JSON)
    then each digest section by name. An unknown header keeps its own text as its name."""
    out: dict[str, str] = {}
    cuts = [(m.start(), m.group(1)) for m in _HEADER.finditer(user)]
    out["facts"] = user[:cuts[0][0]] if cuts else user
    for (start, head), nxt in zip(cuts, [*cuts[1:], (len(user), "")], strict=False):
        name = next((n for p, n in SECTION_NAMES if head.startswith(p)), head[:40])
        out[name] = out.get(name, "") + user[start:nxt[0]]
    return out


def prompt_size(request: Any) -> dict[str, int]:
    import json

    sizes = {"system": len(request.system),
             "tool_schema": len(json.dumps(request.kwargs.get("tools")))}
    for k, v in user_sections(request.user).items():
        sizes[f"user.{k}"] = len(v)
    sizes["total"] = sizes["system"] + sizes["tool_schema"] + len(request.user)
    return sizes


# -------------------------------------------------------------------------------------- M-GAP

#: Each frozen panel page's gap entries, typed by fix 4a's gap test (#927's code at 601d2f7e):
#: the PAGE's truth, the same for both arms. M-GAP imports nothing from #927.
GAP_TYPES_FILE = Path(__file__).with_name("synthesis_gap_types.json")
GAP_CHANGE = "change or deviation"


@cache
def _gap_pages() -> dict[str, tuple[str, list[dict[str, Any]]]]:
    data = json.loads(GAP_TYPES_FILE.read_text(encoding="utf-8"))
    return {t: (str(v["dossier_blob"]), list(v["gaps"])) for t, v in data["pages"].items()}


def gap_entries(ticker: str | None, blob: str | None) -> list[dict[str, Any]] | None:
    """The page's frozen gap entries — None unless the page IS the one they were frozen on: its
    ticker is in the file and its git blob is the file's (#929 review F3: a re-assembled page of
    the same ticker would otherwise read freeze-time types). Where None, M-GAP is UNDEFINED, never
    zero: `score_units` leaves it out, and a registration and a score refuse it as a target."""
    frozen = _gap_pages().get(str(ticker)) if ticker else None
    if frozen is None or blob is None or blob != frozen[0]:
        return None
    return frozen[1]


#: Fit on the gold's DEV half only (CNXC, LLY, MCK; 2026-11-09), then frozen before TEST was read
#: (`docs/records/2026-11-09-m-gap-gold-and-metric.md`).
#: A unit STATES A GAP: an item missing, unknown, undisclosed, unreadable or not derivable.
_GAP_STATED = re.compile(
    r"UNKNOWN|\bmissing\b|not disclosed|undisclosed|no segment|segment[- ]EBITDA breakout|"
    r"single[- ]segment|not (?:readable|parse|available|assessable|derivable)|unavailable|"
    r"cannot be (?:struck|assessed|verified|confirmed|read)|extraction failed|opaque|opacity|"
    r"\bno (?:forward|revised|adjusted|company)", I)
#: ... and FRAMES it against the company: a risk, a concern, opacity that hides something.
_GAP_RISK = re.compile(r"\brisks?\b|opaque|opacity|red flag|\bconcern|caution|weakness|"
                       r"blind spot|obscur|\bmask|\bhid(?:e|es|den|ing)\b", I)
_GAP_BEARISH = re.compile(r"\bbearish\w*", I)
#: ... unless it calls the gap neutral or an open question ("a risk, NOT a neutral gap" is a risk).
_GAP_NEUTRAL = re.compile(r"(?<!not a )(?<!not )(?<!rather than a )(?<!rather than )\bneutral\b|"
                          r"not directional|non-directional|neither case|either way|to resolve|"
                          r"must resolve|resolve before", I)
#: A NEGATED framing word is no framing: "never bearish", "an unknown rather than a risk", "carries
#: no risk signal". The negator stands within three words before it, inside the same clause (no
#: comma, colon, semicolon, dash or bracket between), so "a risk, NOT a neutral gap" and "not
#: neutral — surface it as a BEARISH risk" still frame (#929 review F1: rule 8's new text says
#: "never bearish", and a model echoes its instructions; motivated by that wording, not by TEST —
#: the change leaves the gold's DEV and TEST hit sets identical, unit for unit).
_GAP_NEGATED = re.compile(r"\b(?:never|not|no|nor|rather than|instead of|without)"
                          r"(?:\s+[^\s,;:.()\[\]—–-]+){0,3}\s*$", I)


def _framed(rx: re.Pattern[str], text: str) -> re.Match[str] | None:
    """The first match of ``rx`` in ``text`` that no negator governs."""
    return next((m for m in rx.finditer(text)
                 if not _GAP_NEGATED.search(text[max(0, m.start() - 60):m.start()])), None)


#: A label the unit QUOTES ('not assessable (a risk)') is the page's word, not the unit's framing.
#: A possessive ("company's") never opens a quote.
_GAP_QUOTED = re.compile(r"(?<![A-Za-z])'[^']{1,80}'(?![A-Za-z])")
#: Which of the page's entries a unit names (the taxonomy's hints); a unit naming only type-4
#: entries frames a change, which the gap test lets be raised.
GAP_ITEM_WORDS: dict[str, re.Pattern[str]] = {
    "segment profit by segment": re.compile(
        r"segment[- _](?:level )?(?:ebitda|profit|operating|margin)|single[- ]segment", I),
    "the outlook a gap-down's 8-K furnished": re.compile(
        r"revised[- ]guid\w*|revised outlook|(?:gap[- ]down|drawdown)[^.;]{0,40}(?:outlook|guid)",
        I),
    "a company adjusted-EBITDA guide": re.compile(
        r"ev_ebitda_adjusted_fwd|net_debt_to_ebitda_adjusted|adjusted[- ](?:forward[- ])?"
        r"(?:EV/)?EBITDA|company[- ]adjusted", I),
    "an annual adjusted-EPS guide in the newest release": re.compile(r"adjusted[- _]eps", I),
    "the FCF sign behind the survival line's runway leg": re.compile(r"fcf[_ ]sign|runway", I),
    "a current guide": re.compile(r"current[_ ]guide|current outlook", I),
}


def gap_framing(u: Unit, ctx: PageContext) -> list[Hit]:
    """M-GAP: a `key_unknowns` line or a bear point that STATES a gap and holds it against the
    company — calls it a risk or bearish, or (a bear point) rests on it — where the page's gap test
    types none of the named entries a change (`GAP_CHANGE`). The gap test (fix 4a) lets only a
    change be raised as a risk, so every other such framing is the misread. A gap the page's list
    does not name is "type not determined", which counts. Empty off the frozen pages."""
    entries = gap_entries(ctx.page.get("ticker"), ctx.blob)
    if entries is None or u.section not in ("key_unknowns", "bear_points"):
        return []
    text = _GAP_QUOTED.sub("", u.text)
    if not (stated := _GAP_STATED.search(text)):
        return []
    if u.section == "bear_points":
        framing, phrase = "bear-rest", stated.group(0)
    elif m := _framed(_GAP_BEARISH, text):
        framing, phrase = "bearish", m.group(0)
    elif (m := _framed(_GAP_RISK, text)) and not _GAP_NEUTRAL.search(text):
        framing, phrase = "risk", m.group(0)
    else:
        return []
    named = [e for e in entries if (w := GAP_ITEM_WORDS.get(e["item"])) and w.search(text)]
    if named and all(e["type"] == GAP_CHANGE for e in named):
        return []
    types = "; ".join(f"{e['item']}: {e['type']}" for e in named) or "not on the page's list"
    return [Hit("M-GAP", u.id, framing, phrase,
                f"the page's gap test types it {types} — only a change may be raised as a risk")]


# ----------------------------------------------------------------------------------- registry

UNIT_METRICS: dict[str, Callable[[Unit, PageContext], list[Hit]]] = {
    "M-LABEL": label_echo, "M-SIGN": material_direction, "M-PATH": path_monotone,
    "M-ABSENT": absent_number, "M-GAP": gap_framing,
}
#: A metric defined only on some pages: (its test of the page). Off them it is left out of a
#: score — undefined, never zero.
PAGE_LIMITED: dict[str, Callable[[PageContext], bool]] = {
    "M-GAP": lambda ctx: gap_entries(ctx.page.get("ticker"), ctx.blob) is not None,
}
#: The families a metric's hits are filed under, where a registration may gate on some of them
#: only (`Registration.no_worsening_families`).
METRIC_FAMILIES: dict[str, tuple[str, ...]] = {"M-LABEL": tuple(LABEL_FAMILIES)}
#: The gold class each unit metric is measured against.
GOLD_CLASS = {"M-LABEL": "LABEL", "M-SIGN": "SIGN", "M-PATH": "PATH", "M-ABSENT": "ABSENT"}


def score_units(units: Sequence[Unit], ctx: PageContext, *,
                echo: EchoIndex | None = None) -> dict[str, list[Hit]]:
    """Every metric over ``units``: metric → hits (M-ECHO only when an index is given)."""
    names = [m for m in UNIT_METRICS if m not in PAGE_LIMITED or PAGE_LIMITED[m](ctx)]
    out: dict[str, list[Hit]] = {m: [] for m in names}
    for u in units:
        for name in names:
            out[name] += UNIT_METRICS[name](u, ctx)
    if echo is not None:
        out["M-ECHO"] = [h for u in units for h in instruction_echo(u, ctx, echo)]
    return out
