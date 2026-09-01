"""POSITION MONITOR — the live book against its benchmarks, and the BUY−AVOID spread.

The ledger freezes what was decided; this module reports what has HAPPENED since, without ever
touching the frozen record. Three things it does and one it refuses:

1. **Benchmark by CAP BAND, assigned at ENTRY.** A $1B name and a $10B name do not share a
   yardstick, so the benchmark is chosen from market cap AT THE ENTRY DATE (entry price × shares
   at entry, both source-stamped) and then frozen. The ledger's own ``benchmark`` field predates
   this rule; the committed assignment artifact SUPERSEDES it for scoring (the ledger is
   append-only — a wrong yardstick is corrected FORWARD, never by mutating a logged row).
2. **Excess return per leg** — position return minus its assigned benchmark's return over the
   SAME window. Both sides are PRICE returns (Polygon daily closes): dividends are excluded on
   the position AND the benchmark alike. That understates a dividend-paying name's total return
   and its benchmark's alike; the bias is not zero and it is not symmetric. It is recorded here
   and printed in every artifact — never silently mixed with a total-return series.
3. **The BUY−AVOID spread** = mean(BUY excess) − mean(AVOID excess). SIGN CONVENTION: an AVOID
   leg that FALLS against its benchmark has NEGATIVE excess, and subtracting a negative makes the
   spread MORE positive — i.e. being right about a terminal decline pays into the spread exactly
   as being right about an overshoot does. That is the whole measurement.

What it refuses: **the interim spread is a DIAGNOSTIC, never a result.** §7 — nothing is ever
tuned on it; the pre-registered read is at each row's horizon date. And the freshness/trigger
panel FLAGS; it never adjudicates a trigger as fired — the machine surfaces, the human concludes.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from vinci.labels import resolve_label
from vinci.schemas.ledger import EVENT_CLOSE, ORIGIN_SCREEN
from vinci.sleeves import DEFAULT_SLEEVE

# --- design constants (tunable; named so a change is a decision, not a drift) ------------------
# Cap bands → benchmark proxy. Chosen by FACE VALIDITY (a small-cap leg is measured against a
# small-cap index), never by which pairing would have flattered a spread.
CAP_BAND_SMALL_MAX = 4_000_000_000.0     # < $4B  → IWM  (Russell 2000)
CAP_BAND_MID_MAX = 25_000_000_000.0      # $4–25B → MDY  (S&P MidCap 400)
BENCHMARK_SMALL, BENCHMARK_MID, BENCHMARK_LARGE = "IWM", "MDY", "SPY"

RETURN_BASIS = ("price-return both sides (Polygon daily closes; dividends excluded on the "
                "position AND the benchmark alike — never mixed with a total-return series)")
SPREAD_CAVEAT = (
    "DIAGNOSTIC ONLY until each row reaches its horizon date (§7: never tuned on). "
    "A leg's excess is price-return vs its assigned benchmark over the same window."
)
#: A dated snapshot filename — so a stray file in the directory cannot be read as a day.
_SNAPSHOT_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")

AVOID_SIGN_NOTE = (
    "BUY−AVOID = mean(BUY excess) − mean(AVOID excess). An AVOID leg falling against its "
    "benchmark carries NEGATIVE excess, so subtracting it makes the spread MORE positive: "
    "being right about a terminal decline pays in exactly as being right about an overshoot."
)


def benchmark_for_cap(cap_usd: float) -> tuple[str, str]:
    """Market cap (USD, at entry) → (benchmark ticker, band label). Fails loud on a non-positive
    cap: a benchmark assigned off a missing/zero cap would be a fabricated yardstick."""
    if not cap_usd > 0:
        raise ValueError(f"cap must be > 0 to assign a benchmark band (got {cap_usd!r})")
    if cap_usd < CAP_BAND_SMALL_MAX:
        return BENCHMARK_SMALL, f"small (<${CAP_BAND_SMALL_MAX / 1e9:.0f}B)"
    if cap_usd < CAP_BAND_MID_MAX:
        return BENCHMARK_MID, (f"mid (${CAP_BAND_SMALL_MAX / 1e9:.0f}–"
                               f"{CAP_BAND_MID_MAX / 1e9:.0f}B)")
    return BENCHMARK_LARGE, f"large (>${CAP_BAND_MID_MAX / 1e9:.0f}B)"


class BenchmarkAssignment(BaseModel):
    """One name's frozen yardstick, derived at its ENTRY date and committed.

    SUPERSEDES the ledger row's ``benchmark`` field for scoring (the row itself is never
    mutated — append-only). Every input is source-stamped so the band can be re-checked."""

    ticker: str
    entry_date: date
    entry_price: float
    shares: float                    # shares at entry, in SHARES (not millions)
    shares_source: str               # where the share count came from — verbatim
    cap_at_entry_usd: float
    band: str
    benchmark: str
    rationale: str
    assigned_at: date
    supersedes: str | None = None    # the ledger row's benchmark field this overrides

    model_config = {"frozen": True}


class PositionRow(BaseModel):
    """One ledger leg, marked to the latest close against its assigned benchmark."""

    ticker: str
    verdict: str
    sector: str | None = None
    # WHICH ROUTE and WHICH BOOK — carried so the spread below can be scoped the way the scoring
    # report already is. Defaults are the truthful reading of a row logged before the fields
    # existed: the screen was the only route that could reach the ledger, overshoot the only book.
    origin: str = ORIGIN_SCREEN
    sleeve: str = DEFAULT_SLEEVE
    entry_price: float
    entry_date: date
    current_price: float
    current_date: date
    position_return: float           # fraction, e.g. 0.0412 = +4.12%
    benchmark: str
    benchmark_entry: float
    benchmark_now: float
    benchmark_return: float
    excess: float                    # position_return − benchmark_return
    days_elapsed: int
    horizon_days: int
    horizon_date: date
    resolved: bool                   # has the row reached its horizon? (only then is it a result)
    # Is the POSITION still held? Distinct from ``resolved``, which is about the CALL's clock. A
    # closed row keeps marking to its horizon (the ruling), so this is the flag that lets a reader
    # separate "the call was right" from "the book held it" instead of inferring it from a note.
    closed: bool = False


class SpreadDiagnostic(BaseModel):
    """The BUY−AVOID spread with every honesty caveat attached to the number itself."""

    buy_n: int
    avoid_n: int
    buy_mean_excess: float | None = None
    avoid_mean_excess: float | None = None
    spread: float | None = None
    resolved_n: int = 0
    # THE DENOMINATOR TRAVELS WITH THE NUMERATOR. ``resolved_n`` counts the SCOPED rows, so a
    # renderer dividing it by the snapshot's total row count prints a fraction whose two halves
    # measure different populations — "resolved 1/2" on a book holding one screen row and one
    # followed row. BOTH renderers made exactly that mistake (review #382), and two independent
    # callers getting it wrong the same way is the signal that the scope belongs in the model
    # rather than in each caller's arithmetic. Legacy snapshots default to 0 and are never
    # rewritten; the renderers fall back to the row count for them, which is what they meant
    # when every row was screen-origin.
    scoped_n: int = 0
    max_days_elapsed: int = 0
    sign_convention: str = AVOID_SIGN_NOTE
    caveat: str = SPREAD_CAVEAT
    undefined_reason: str | None = None   # set when a leg is empty → spread is None, never 0.0
    # --- THE SAME SPREAD OVER POSITIONS STILL HELD (operator ruling 2026-08-12) ----------------
    # A decision keeps accruing to its horizon after the position is closed — the spread measures
    # the DISCRIMINATOR, and closing early is a portfolio action that does not retract the call.
    # That ruling stands. What it does NOT license is a headline the reader cannot decompose: on
    # 2026-08-11 the book read +9.54%, and +29.00 pts of the BUY leg came from IT — a position
    # closed at the entry price on 2026-07-21 whose REALIZED P&L was +0.0%. On rows still held the
    # same spread is −1.56%. The sign flips, so both are printed and neither is the "real" one:
    # the headline answers "was the call right", this answers "did the book hold it".
    closed_n: int = 0
    open_buy_n: int = 0
    open_avoid_n: int = 0
    spread_open_only: float | None = None
    open_undefined_reason: str | None = None


class RealizedRow(BaseModel):
    """One closed position's realized P&L — TYPED, not prose (operator to-do, 2026-08-12).

    The realized book reached the snapshot only as free-text ``notes`` strings, so the one view
    that says what the fund actually EARNED was unreadable by anything that was not parsing
    English. ``realized_return`` is DERIVED here exactly as ``pair_closes`` derives it — from the
    two frozen prices, never stored — so there is one definition and the note text below is
    rendered FROM this row rather than beside it."""

    ticker: str
    entry_id: str
    close_id: str
    verdict: str
    entry_price: float
    entry_price_as_of: date
    exit_price: float
    exit_price_as_of: date
    realized_return: float

    def note(self) -> str:
        """The human line — derived from the typed row, so display can never drift from data."""
        return (f"{self.ticker}: REALIZED {self.realized_return:+.1%} "
                f"(entry ${self.entry_price:,.2f} {self.entry_price_as_of} → exit "
                f"${self.exit_price:,.2f} {self.exit_price_as_of}) — realized P&L, a separate "
                f"view; the {self.verdict} call stays in horizon calibration")


class MonitorSnapshot(BaseModel):
    """One dated run — the auditable book history. Committed per run."""

    as_of: date
    price_basis: str = RETURN_BASIS
    rows: list[PositionRow] = Field(default_factory=list)
    spread: SpreadDiagnostic
    freshness: list[FreshnessRow] = Field(default_factory=list)
    # THEME-LEVEL falsifier deadlines (brief Item 2, 2026-08-29): every declared thesis card's
    # dated triggers, swept the same way the scenario `dated_triggers` are — a passed deadline is
    # a FLAG ("re-underwrite due"), never an adjudication that the trigger FIRED. Defaulted, so
    # every committed pre-Item-2 snapshot still validates (corpus-pinned).
    theme_falsifiers: list[ThemeFalsifierRow] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    # THE REALIZED BOOK, TYPED. It reached this artifact only as prose inside ``notes``, so the one
    # view that says what the fund actually EARNED could not be read by anything that was not
    # parsing English — while the marked-to-market rows beside it were fully structured. The note
    # lines are now RENDERED from these rows (``RealizedRow.note``), so there is one definition and
    # the display cannot drift from the data.
    realized: list[RealizedRow] = Field(default_factory=list)


class FreshnessRow(BaseModel):
    """Per live leg: what the record has READ, and what EDGAR has published since.

    ``unread_print`` is a FLAG, never an adjudication: it says a filing exists that the record's
    evidence postdates, not that any trigger fired. The human concludes."""

    ticker: str
    verdict: str
    last_evidence_date: date | None = None
    last_evidence_source: str | None = None
    newer_filings: list[str] = Field(default_factory=list)   # "FORM YYYY-MM-DD acc" per filing
    unread_print: bool = False
    next_expected_print: date | None = None
    next_expected_basis: str | None = None                   # ESTIMATE — from filing cadence
    triggers: list[str] = Field(default_factory=list)
    # (catalyst calendar, ratified 2026-07-24) analyst-DATED triggers whose deadline has PASSED —
    # each a FLAG ("… — deadline YYYY-MM-DD PASSED → re-underwrite due"), never an adjudication:
    # the window closed; whether the trigger FIRED is the human's read.
    passed_trigger_deadlines: list[str] = Field(default_factory=list)
    # (ruling 3) the EVALUATED form of the criteria above, for the criteria that carry arithmetic.
    # Empty is the normal state and does NOT mean "nothing fired": it means this record states no
    # measured criterion — every one of its falsifiers is a judgment. The renderer must say which.
    measured: list[MeasuredTriggerRow] = Field(default_factory=list)
    #: (MC1) tags whose series has gone quiet, named rather than silently served. `stale_served`
    #: has had no caller since #531 shipped it, so the 7 stale tags it can name reached no human.
    stale_tags: list[str] = Field(default_factory=list)
    watch_note: str | None = None                            # e.g. WERN avoid_priced


class MeasuredTriggerRow(BaseModel):
    """One MEASURED criterion, evaluated at monitor time (ruling 3, 2026-08-31).

    TYPED HERE SO `PanelSpec` READS IT RATHER THAN RECOMPUTING. `ThemeFalsifierRow` below records
    that indicator measurement "is the PanelSpec plan's job, and this sweep must never grow into a
    rival panel" — the same rule binds here. This row is not a panel: it is the evaluated STATE
    hung on the trigger list this row already carried in prose, so the panel that renders it later
    consumes one answer instead of computing a second one that could disagree.

    THE STATE IS THREE-VALUED AND `UNKNOWN` IS NOT A QUIET NO. A criterion the evaluator could not
    read must look different on the page from one that has not fired; they recommend opposite
    actions. `reason` is populated on every state, because a human reading FIRED needs the number
    as much as one reading UNKNOWN needs the cause.

    THE MACHINE PROPOSES A FIRING STATUS; THE HUMAN DECIDES THE ACTION. Nothing here moves a
    position, and `state == "FIRED"` is a highlight, never a disposition.
    """

    trigger: str                    # the analyst's sentence, verbatim
    #: THE TEST, carried so a prior day can be matched to a current criterion by what it MEASURES
    #: rather than by its prose. Matching on the sentence would let a typo fix reset a kill streak
    #: and would silently CARRY one across an AMENDED THRESHOLD — a different test, which must
    #: start again. These three are that identity.
    metric: str = ""
    comparator: str = ""
    threshold: float | None = None
    state: str                      # FIRED | NOT_FIRED | UNKNOWN
    #: Whether the COMPARISON held on this reading — recorded because it diverges from `state` on a
    #: sustain criterion (held, but the streak is short → NOT_FIRED). Reading the state alone when
    #: counting a streak would treat that reading as a failure and restart the count from the wrong
    #: place, which is the quiet way a two-quarter kill never fires.
    satisfied: bool | None = None
    reason: str                     # why — on every state, not only the refusals
    observed: float | None = None
    unit: str | None = None
    source: str | None = None       # the metric's own source_ref, so the number is checkable


class ThemeFalsifierRow(BaseModel):
    """One dated trigger from a theme thesis card, at sweep time. TYPED FIRST, prose rendered
    from it (the RealizedRow lesson): ``deadline_passed`` is the machine's whole contribution —
    the window closed; whether the falsifier FIRED is the human's read, exactly as with the
    scenario ``dated_triggers`` this mirrors. Indicator MEASUREMENT (the number beside the
    criterion) is deliberately NOT here — that is the PanelSpec plan's job, and this sweep must
    never grow into a rival panel."""

    driver_key: str
    kind: str            # "first-confirming" | "falsifier"
    trigger: str         # verbatim, the operator's words
    deadline: str        # ISO (declare-time validated)
    basis: str = ""
    deadline_passed: bool = False


def theme_falsifier_rows(cards: list[Any], *, today: date) -> list[ThemeFalsifierRow]:
    """Sweep every declared card's dated triggers. ``cards`` are ``ThemeThesis`` instances
    (duck-read here so the monitor stays importable without the themes package at type time).
    Deadlines are ISO by declare-time validation, so a parse failure is a corrupted card and
    raises LOUDLY rather than being skipped — unlike the scenario path, where an unparseable
    analyst date legitimately renders verbatim in the dossier instead."""
    rows: list[ThemeFalsifierRow] = []
    for card in cards:
        entries = [("first-confirming", card.first_confirming)]
        entries += [("falsifier", f) for f in card.falsifiers]
        for kind, t in entries:
            rows.append(ThemeFalsifierRow(
                driver_key=card.driver_key, kind=kind, trigger=t.trigger, deadline=t.deadline,
                basis=t.basis, deadline_passed=date.fromisoformat(t.deadline) <= today))
    return rows


MonitorSnapshot.model_rebuild()


# --- close rows: the position/close partition, and the realized view --------------------------
def entry_of(row: dict[str, Any]) -> dict[str, Any]:
    """The full LedgerEntry dict behind a ledger row — the ONE place the two shapes are reconciled.

    A committed ledger row mirrors the DB columns and carries the complete entry as JSON in
    ``payload``; a freshly dumped model is already the entry. Close fields (``event``,
    ``closes_entry_id``, ``exit_price``) live on the ENTRY, so every close-aware reader must go
    through here rather than probing the row's top level — where those keys simply do not exist on
    a committed row, and the filter would silently pass every close through as a position.
    """
    p = row.get("payload")
    if isinstance(p, str):
        return dict(json.loads(p))
    if isinstance(p, dict):
        return dict(p)
    return row


def decision_rows(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The rows that are POSITIONS — every raw ledger row whose ``event`` is not a close.

    THE LANDMINE THIS DEFUSES: ``compute_spread`` partitions by verdict alone, and a close row
    carries the ORIGINAL verdict for provenance. Appending a close for IT without this filter
    would count IT as a SECOND BUY leg and double it in the BUY−AVOID spread — corrupting the one
    number the fund exists to measure, silently, with nothing red.

    Legacy rows have no ``event`` key at all and are decision rows by definition, so this is a
    no-op on everything committed before 2026-07-22.
    """
    return [r for r in raw if entry_of(r).get("event") != EVENT_CLOSE]


def close_rows(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The close rows only — the realized-P&L view's input."""
    return [r for r in raw if entry_of(r).get("event") == EVENT_CLOSE]


def pair_closes(
    raw: list[dict[str, Any]], *, as_of: date | None = None,
) -> list[dict[str, Any]]:
    """Pair each close to the decision row it closes, and DERIVE the realized return.

    Realized return is computed here, never stored: it is ``exit/entry − 1`` from two frozen
    prices, so persisting it would create a second source of truth able to drift from the two
    numbers it came from. The ledger stores facts; views derive.

    ``as_of`` MAKES THE VIEW POINT-IN-TIME (operator review P1 on #418). Without it every close in
    the ledger counted regardless of when it happened, so `vinci monitor --ref <past date>` marked
    positions closed — and printed their realized P&L — for exits that had not occurred yet at that
    point in the book. The price path already refuses a future bar; the close path did not, so a
    historical snapshot was not reproducible. Filtering happens AFTER pairing, deliberately: the
    unpairable/duplicated-close refusals below must see the WHOLE ledger, or a malformed close
    dated past ``as_of`` would slip through unexamined.

    Refuses loud on an unpairable or duplicated close — a close pointing at nothing, or two closes
    for one entry, means the realized book is wrong and must not render as though it were right.
    """
    by_id = {entry_of(r)["entry_id"]: entry_of(r) for r in decision_rows(raw)}
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in close_rows(raw):
        c = entry_of(row)
        target = c.get("closes_entry_id")
        if not isinstance(target, str) or target not in by_id:
            raise ValueError(
                f"close row {c.get('entry_id')!r} references entry_id {target!r}, which is not a "
                "decision row in the ledger — a close must close something")
        if target in seen:
            raise ValueError(
                f"entry_id {target!r} is closed TWICE (second close {c.get('entry_id')!r}) — a "
                "position closes once, or the realized return is ambiguous")
        seen.add(target)
        d = by_id[target]
        entry, exit_ = float(d["entry_price"]), float(c["exit_price"])
        out.append({"ticker": d["ticker"], "entry_id": target, "close_id": c.get("entry_id"),
                    "verdict": d["verdict"], "entry_price": entry,
                    "entry_price_as_of": d.get("entry_price_as_of"),
                    "exit_price": exit_, "exit_price_as_of": c.get("exit_price_as_of"),
                    "realized_return": exit_ / entry - 1.0})    # DERIVED, never stored
    if as_of is None:
        return out
    return [r for r in out if date.fromisoformat(str(r["exit_price_as_of"])) <= as_of]


# --- spread ------------------------------------------------------------------------------------
def closed_decision_ids(
    raw: list[dict[str, Any]], *, as_of: date | None = None,
) -> set[str]:
    """The ENTRY IDs of decisions whose position has been closed — never the tickers.

    KEYED ON THE DECISION, because a name can be closed and re-entered: SMPL was closed 2026-07-22
    and re-entered 2026-08-04, so a ticker-keyed set marks the LIVE re-entry as closed too, drops it
    out of the still-held spread and changes the number the operator reads. This lives here rather
    than inline in the CLI so the keying is exercised against the real ledger instead of being
    re-derived correctly-or-not at each call site."""
    return {str(r["entry_id"]) for r in pair_closes(raw, as_of=as_of)}


def decisions_as_of(raw: list[dict[str, Any]], *, as_of: date) -> list[dict[str, Any]]:
    """The decision rows that EXISTED on ``as_of`` — entered on or before that date.

    The sibling of ``closed_decision_ids``, and the louder half of the same defect: without it
    `monitor --ref 2026-07-20` marked SMPL's 2026-08-04 re-entry into that day's book with
    ``days_elapsed: -15``, a position that did not exist yet. Lives here rather than inline at the
    call site so the rule is exercised against the real ledger — the CLI's copy could only ever be
    checked by a static artifact, which cannot catch a change to the code that writes it."""
    return [r for r in decision_rows(raw)
            if date.fromisoformat(str(entry_of(r)["entry_price_as_of"])) <= as_of]


def _is_buy(verdict: str) -> bool:
    """BUY-family vs the rest — mirrors the frontend isBuyVerdict (family, not equality)."""
    return verdict.upper().startswith("BUY")


def compute_spread(rows: list[PositionRow]) -> SpreadDiagnostic:
    """mean(BUY excess) − mean(AVOID excess) over the SCREEN-ORIGIN rows. An EMPTY leg makes the
    spread ``None`` with a stated reason — never 0.0, which would read as "no edge" when it means
    "not measurable".

    SCREEN-ORIGIN ONLY, matching `scoring/metrics.py` — this is the same headline number, printed
    by a different command, and the two must not disagree about what they measure. Without the
    filter a followed quality row landed in the AVOID leg by the BUY-prefix test below (`PASS` does
    not start with "BUY") and moved the fund's proof number on the operator's own console."""
    scoped = [r for r in rows if r.origin == ORIGIN_SCREEN]

    def legs(subset: list[PositionRow]) -> tuple[float | None, float | None, int, int, str | None]:
        b = [r.excess for r in subset if _is_buy(r.verdict)]
        a = [r.excess for r in subset if not _is_buy(r.verdict)]
        bm = sum(b) / len(b) if b else None
        am = sum(a) / len(a) if a else None
        why = None
        if bm is None or am is None:
            why = (f"no {'BUY' if bm is None else 'AVOID'} legs logged — the spread needs both "
                   f"sides")
        return bm, am, len(b), len(a), why

    buy_mean, avoid_mean, n_buy, n_avoid, reason = legs(scoped)
    # THE SAME ARITHMETIC OVER POSITIONS STILL HELD. Not a competing headline — a decomposition, so
    # a reader can see how much of the spread is carried by calls the book no longer owns. Its
    # "needs both sides" reason is worded for THIS scope, because "no AVOID legs" reads very
    # differently when it means "every AVOID was closed" than when it means "none was ever logged".
    still_open = [r for r in scoped if not r.closed]
    o_buy, o_avoid, o_nb, o_na, o_reason = legs(still_open)
    if o_reason is not None and len(still_open) < len(scoped):
        o_reason += f" among the {len(still_open)} of {len(scoped)} rows still held"
    return SpreadDiagnostic(
        buy_n=n_buy, avoid_n=n_avoid,
        buy_mean_excess=buy_mean, avoid_mean_excess=avoid_mean,
        spread=(buy_mean - avoid_mean) if (buy_mean is not None and avoid_mean is not None)
        else None,
        resolved_n=sum(1 for r in scoped if r.resolved),
        scoped_n=len(scoped),
        max_days_elapsed=max((r.days_elapsed for r in scoped), default=0),
        undefined_reason=reason,
        closed_n=sum(1 for r in scoped if r.closed),
        open_buy_n=o_nb, open_avoid_n=o_na,
        spread_open_only=(o_buy - o_avoid) if (o_buy is not None and o_avoid is not None)
        else None,
        open_undefined_reason=o_reason,
    )


def position_row(*, ticker: str, verdict: str, sector: str | None, entry_price: float,
                 entry_date: date, current_price: float, current_date: date, benchmark: str,
                 benchmark_entry: float, benchmark_now: float, horizon_days: int,
                 origin: str = ORIGIN_SCREEN, sleeve: str = DEFAULT_SLEEVE,
                 closed: bool = False) -> PositionRow:
    """Mark one leg. Fails loud on a non-positive entry or benchmark price — a return computed
    off a zero base is not a number this fund reports."""
    if not entry_price > 0 or not benchmark_entry > 0:
        raise ValueError(f"{ticker}: entry_price and benchmark_entry must be > 0 "
                         f"(got {entry_price!r}, {benchmark_entry!r})")
    pos_ret = current_price / entry_price - 1.0
    bench_ret = benchmark_now / benchmark_entry - 1.0
    horizon_date = entry_date + timedelta(days=horizon_days)
    return PositionRow(
        ticker=ticker, verdict=verdict, sector=sector,
        origin=origin, sleeve=sleeve,
        entry_price=entry_price, entry_date=entry_date,
        current_price=current_price, current_date=current_date,
        position_return=pos_ret, benchmark=benchmark, benchmark_entry=benchmark_entry,
        benchmark_now=benchmark_now, benchmark_return=bench_ret, excess=pos_ret - bench_ret,
        days_elapsed=(current_date - entry_date).days,
        horizon_days=horizon_days, horizon_date=horizon_date,
        resolved=current_date >= horizon_date,
        closed=closed,
    )


# --- display sector (re-resolved at the report layer; the frozen ledger row is never rewritten) --
def sector_for_display(sic: str | None) -> str | None:
    """One position's display sector from the entity master's SIC — ``None`` when there is no SIC.

    ABSENT IS NOT A LABEL. `resolve_label(None).sector` answers ``"Unknown"``, and so does a SIC
    that is PRESENT but unmappable — so collapsing the two dresses a BROKEN LOOKUP as a resolved
    reading, which is the shape CLAUDE.md forbids (missing data is never silently imputed, and
    equally never presented as a resolution). Absence returns ``None`` so the artifact records
    that no sector was read; ``"Unknown"`` then keeps exactly one meaning — a SIC WAS read and did
    not map. Found via IT/Gartner, whose SIC a partial upsert had destroyed: the monitor printed
    "sector re-resolved to Unknown", indistinguishable from an honest unmappable code.
    """
    if sic is None or not str(sic).strip():
        return None
    return resolve_label(sic).sector


def sector_note(*, ticker: str, sic: str | None, frozen_sector: str | None) -> str | None:
    """The display-layer note for one position's sector, or ``None`` when there is nothing to say.

    Two DIFFERENT facts, never one message: a SIC that is ABSENT from the committed entity master
    (say so, loudly — it is a data defect to repair, not a reading), and a SIC that resolves to a
    sector DIFFERING from the one frozen in the append-only ledger row (the forward-only
    correction the 87xx family fix introduced). The frozen row is never rewritten either way.
    """
    if sic is None or not str(sic).strip():
        # BOTH CAUSES NAMED, because they are not the same problem and only one is repairable.
        # The 2026-08-31 backfill measured it: of 418 CIKs missing a SIC, 378 simply had never
        # been enriched, but 40 — every one a BDC or fund — have NO SIC AT EDGAR to fetch. That
        # is the same blank the universe gate fails closed on (`unknown_sic`), so telling the
        # reader to "repair the row" would send them after a value that does not exist.
        return (f"{ticker}: SIC ABSENT from the committed entity master — sector UNRESOLVED, "
                f"NOT re-resolved (the frozen row logged {frozen_sector or '—'}, never "
                f"rewritten). Either EDGAR publishes none for this issuer (routine for BDCs and "
                f"funds) or the row lost one — check which; do not read this as a sector.")
    live = sector_for_display(sic)
    if frozen_sector and frozen_sector != live:
        return (f"{ticker}: sector re-resolved to {live} for display "
                f"(the frozen row logged {frozen_sector} — never rewritten)")
    return None


# --- freshness ---------------------------------------------------------------------------------
_AMENDED_RE = re.compile(r"\[amended (\d{4}-\d{2}-\d{2})")


def last_evidence_date(record: dict[str, Any]) -> tuple[date | None, str | None]:
    """The newest date the scenario record's evidence reflects: its underwrite date, or a LATER
    ``[amended YYYY-MM-DD …]`` tag on any leg reason (the visible-amendment convention). Returns
    ``(date, source)``; ``(None, None)`` when the record states no date at all (fail-honest)."""
    dates: list[tuple[date, str]] = []
    raw = record.get("underwrite_date")
    if raw:
        dates.append((date.fromisoformat(str(raw)), "underwrite_date"))
    for leg, s in (record.get("scenarios") or {}).items():
        for m in _AMENDED_RE.finditer(str(s.get("reason") or "")):
            dates.append((date.fromisoformat(m.group(1)), f"{leg} reason amendment"))
    if not dates:
        return None, None
    best = max(dates, key=lambda t: t[0])
    return best[0], best[1]


def next_expected_print(filing_dates: list[date], *,
                        today: date) -> tuple[date | None, str | None]:
    """ESTIMATE the next periodic filing from the filer's OWN cadence: the earliest prior filing
    whose date + 365d is still ahead of ``today``. Labeled an estimate everywhere it is shown —
    it schedules attention, it is never evidence."""
    future = sorted(d + timedelta(days=365) for d in filing_dates
                    if d + timedelta(days=365) > today)
    if not future:
        return None, None
    return future[0], "ESTIMATE — same-quarter filing one year prior + 365d (filer's own cadence)"


def _stale_tags(mechanical: dict[str, Any] | None) -> list[str]:
    """(MC1) The tags whose series has gone quiet, named for a human.

    `stale_served` shipped in #531 and has had NO CALLER since, so the seven stale tags it can
    name reached nobody — the reporting half of that work was built and left unwired, which is the
    same shape as the dilution overlay this repo already records. It needs companyfacts, which the
    monitor does not hold; what IS available here is the dossier's own recorded flags, so this
    reads those rather than inventing a second source for the same fact.
    """
    if not mechanical:
        return []
    out: list[str] = []
    for block in mechanical.values():
        if not isinstance(block, dict):
            continue
        for name, node in block.items():
            if isinstance(node, dict) and str(node.get("status") or "") == "stale":
                out.append(str(name))
    return sorted(set(out))


def _history_for(trig: Any, prior_days: list[dict[str, Any]]) -> list[Any] | None:
    """Prior readings of THIS criterion, newest first, from already-committed monitor days.

    THE HISTORY IS THE MONITOR DAYS THEMSELVES. They are dated, committed and append-only, and
    each already records what every criterion read — so a separate observation store would be a
    second copy of a fact the repo keeps, free to drift from it.

    MATCHED ON THE TEST, NOT THE SENTENCE. An amended threshold is a DIFFERENT criterion and its
    streak starts again; a reworded sentence is the same test and keeps its streak. Matching on
    prose would get both backwards.

    Returns None when no prior day carries this row at all — "never measured" is not "measured and
    did not hold", and the evaluator turns the first into UNKNOWN rather than a broken streak.
    """
    from vinci.triggers import Observation

    seen: list[Any] = []
    found = False
    for day in prior_days:                       # newest first, supplied by the caller
        for row in (day.get("freshness") or []):
            for m in (row.get("measured") or []):
                if (m.get("metric") == trig.metric and m.get("comparator") == trig.comparator
                        and m.get("threshold") == trig.threshold):
                    found = True
                    seen.append(Observation(source=m.get("source"),
                                            satisfied=bool(m.get("satisfied"))))
    return seen if found else None


def _measured_rows(record: dict[str, Any],
                   mechanical: dict[str, Any] | None,
                   prior_days: list[dict[str, Any]] | None = None) -> list[MeasuredTriggerRow]:
    """Evaluate this record's measured criteria. Absent dossier → UNKNOWN WITH ITS CAUSE.

    An absent mechanical layer is exactly the case that must not silently become "nothing fired":
    the criteria exist and were simply not measurable on this run, which is a different sentence
    from a quiet page and reaches the human as one.
    """
    from vinci.scenarios import MeasuredTrigger
    from vinci.triggers import UNKNOWN, evaluate

    prior_days = prior_days or []
    raw = (record.get("verdict") or {}).get("measured_triggers") or []
    out: list[MeasuredTriggerRow] = []
    for item in raw:
        trig = MeasuredTrigger.model_validate(item)
        if mechanical is None:
            out.append(MeasuredTriggerRow(
                trigger=trig.trigger, metric=trig.metric, comparator=trig.comparator,
                threshold=trig.threshold, state=UNKNOWN,
                reason=(f"no committed dossier was supplied for this run, so {trig.metric!r} could "
                        f"not be read — the criterion is unmeasured, not quiet")))
            continue
        st = evaluate(trig, mechanical, history=_history_for(trig, prior_days))
        out.append(MeasuredTriggerRow(
            trigger=trig.trigger, metric=trig.metric, comparator=trig.comparator,
            threshold=trig.threshold, state=st.state, satisfied=st.satisfied, reason=st.reason,
            observed=st.observed, unit=st.unit, source=st.source))
    return out


def freshness_row(*, ticker: str, verdict: str, record: dict[str, Any],
                  filings: list[tuple[str, date, str]], today: date,
                  watch_note: str | None = None,
                  mechanical: dict[str, Any] | None = None,
                  prior_days: list[dict[str, Any]] | None = None) -> FreshnessRow:
    """Build one freshness row. ``filings`` = (form, date, accession) for the name's periodic +
    earnings filings. A filing dated AFTER the record's last evidence date sets ``unread_print``
    — a flag for the human, never a verdict on any trigger.

    ``mechanical`` is the name's committed dossier mechanical layer, SUPPLIED BY THE CALLER rather
    than read here — the same rule the scoring package follows for baskets, and for the same
    reason: this module resolves neither config nor paths, so a reader that had to find a dossier
    would put file layout inside a pure function. Absent, the measured criteria are reported
    UNKNOWN with that as their stated cause, never silently skipped.
    """
    ev, ev_src = last_evidence_date(record)
    newer = [f"{form} {d.isoformat()} acc {acc}"
             for form, d, acc in sorted(filings, key=lambda t: t[1])
             if ev is not None and d > ev]
    nxt, basis = next_expected_print([d for _, d, _ in filings], today=today)
    # (catalyst calendar) the analyst's DATED triggers: a deadline on/before today → the PASSED
    # flag list; a future one joins the display list with its date. Both verbatim + labeled —
    # the machine never adjudicates whether a trigger fired.
    triggers = list((record.get("verdict") or {}).get("reunderwrite_triggers") or [])
    measured = _measured_rows(record, mechanical, prior_days)
    passed: list[str] = []
    for dt in (record.get("verdict") or {}).get("dated_triggers") or []:
        trig, deadline = str(dt.get("trigger") or ""), str(dt.get("deadline") or "")
        if not trig or not deadline:
            continue
        try:
            dl = date.fromisoformat(deadline)
        except ValueError:
            continue  # an unparseable analyst date renders verbatim in the dossier, not here
        if dl <= today:
            passed.append(f"{trig} — deadline {deadline} PASSED → re-underwrite due")
        else:
            triggers.append(f"{trig} (by {deadline})")
    return FreshnessRow(
        ticker=ticker, verdict=verdict, last_evidence_date=ev, last_evidence_source=ev_src,
        newer_filings=newer, unread_print=bool(newer),
        next_expected_print=nxt, next_expected_basis=basis,
        triggers=triggers, passed_trigger_deadlines=passed,
        measured=measured, stale_tags=_stale_tags(mechanical),
        watch_note=watch_note,
    )


# --- persistence -------------------------------------------------------------------------------
def monitor_dir(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / "data" / "monitor"


def assignments_path(root: Path | None = None) -> Path:
    return monitor_dir(root) / "benchmark_assignments.json"


def read_assignments(root: Path | None = None) -> dict[str, BenchmarkAssignment]:
    p = assignments_path(root)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    return {k: BenchmarkAssignment.model_validate(v) for k, v in raw.items()}


def write_assignments(items: dict[str, BenchmarkAssignment], *, root: Path | None = None) -> Path:
    p = assignments_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: json.loads(v.model_dump_json()) for k, v in sorted(items.items())}
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return p


def write_snapshot(
    snap: MonitorSnapshot, *, root: Path | None = None, rewrite_history: bool = False,
) -> Path:
    """One dated file per run — the auditable book history (never overwritten across days).

    REFUSES TO REWRITE A SUPERSEDED DAY. That docstring line claimed the history is never
    overwritten and nothing enforced it, so re-running `--ref <past date>` silently replaced that
    day's file. I did exactly that while testing the point-in-time fix, and it is how the decision
    look-ahead was found.

    THE RULE IS "SUPERSEDED", NOT "NOT TODAY", and the difference matters in practice: the normal
    daily run resolves to the LAST TRADING DAY, which is usually not today, so a not-today rule
    would refuse the routine re-run. Rewriting the FRONT of the book is fine — same day, better
    data. Rewriting a day that later snapshots already sit on top of is the destructive case, and
    that is what this refuses.

    Note that a past re-run now REPRODUCES: decisions and closes are both read as of the snapshot
    date. So this is a guard against a future divergence (a code change, a ledger correction),
    not against a known-bad rewrite.
    """
    d = monitor_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{snap.as_of.isoformat()}.json"
    if p.exists() and not rewrite_history:
        later = sorted(f.stem for f in d.glob("*.json")
                       if _SNAPSHOT_DAY.fullmatch(f.stem) and f.stem > snap.as_of.isoformat())
        if later:
            raise FileExistsError(
                f"{p} already exists and {len(later)} later snapshot(s) sit on top of it "
                f"(next: {later[0]}) — rewriting a superseded day replaces what the book recorded "
                f"then with what today's code and ledger produce. Pass rewrite_history=True if "
                f"that is genuinely what you mean.")
    p.write_text(snap.model_dump_json(indent=2) + "\n")
    return p


def latest_snapshot(root: Path | None = None) -> MonitorSnapshot | None:
    d = monitor_dir(root)
    if not d.is_dir():
        return None
    files = sorted(p for p in d.glob("*.json") if p.name != "benchmark_assignments.json")
    if not files:
        return None
    return MonitorSnapshot.model_validate_json(files[-1].read_text())


def render_table(snap: MonitorSnapshot) -> str:
    """The terminal view — the same numbers the artifact carries, with the caveats attached."""
    out = [f"BOOK as of {snap.as_of}  ({snap.price_basis})", ""]
    hdr = (f"{'TICKER':<7}{'VERDICT':<16}{'ENTRY':>9}{'NOW':>9}{'POS%':>8}"
           f"{'BMK':>5}{'BMK%':>8}{'EXCESS%':>9}{'DAYS':>7}  HORIZON")
    out.append(hdr)
    for r in sorted(snap.rows, key=lambda r: r.ticker):
        # THE BOOK IS NAMED ONLY WHEN IT IS NOT THE DEFAULT — a tag on every row is noise, and its
        # absence on the overshoot majority carries the same information (the shelf makes the same
        # call). Without it a followed row sits in this table indistinguishable from a screen one
        # while being deliberately excluded from the spread printed underneath.
        book = "" if r.sleeve == DEFAULT_SLEEVE else f"  [{r.sleeve}]"
        out.append(
            f"{r.ticker:<7}{r.verdict:<16}{r.entry_price:>9.2f}{r.current_price:>9.2f}"
            f"{r.position_return * 100:>+8.2f}{r.benchmark:>5}{r.benchmark_return * 100:>+8.2f}"
            f"{r.excess * 100:>+9.2f}{f'{r.days_elapsed}/{r.horizon_days}':>7}  "
            f"{r.horizon_date}{'' if not r.resolved else '  RESOLVED'}{book}")
    s = snap.spread
    # THE SCOPE IS STATED, because the number's meaning narrowed. It measures the discriminator on
    # the $300M–$10B hunting ground; a reader meeting an unlabelled "BUY−AVOID SPREAD" would carry
    # the old, wider meaning forward. The scoring report states the same scope on its own line.
    out += ["", "SCOPE: screen-origin rows only — other books are listed above but never pooled "
                "into this number."]
    out += ["", "BUY−AVOID SPREAD: "
            + ("UNDEFINED — " + (s.undefined_reason or "") if s.spread is None
               else f"{s.spread * 100:+.2f} pp")]
    if s.buy_mean_excess is not None:
        out.append(f"  BUY  n={s.buy_n} mean excess {s.buy_mean_excess * 100:+.2f} pp")
    if s.avoid_mean_excess is not None:
        out.append(f"  AVOID n={s.avoid_n} mean excess {s.avoid_mean_excess * 100:+.2f} pp")
    # Denominator from the diagnostic, NOT from the row list: `resolved_n` counts scoped rows
    # only. A legacy snapshot predating `scoped_n` reports 0 → fall back to the row count, which
    # is exactly right for it (every row it holds is screen-origin).
    scoped_n = s.scoped_n or len(snap.rows)
    out += [f"  resolved {s.resolved_n}/{scoped_n} · max days elapsed {s.max_days_elapsed}"]
    # THE DECOMPOSITION, printed only when it says something — with no closed rows the two numbers
    # are identical and a second line would be noise. The closed rows are IN the headline by
    # ruling; this says how much of it they carry, so nobody reads a spread earned on positions the
    # book no longer holds as a spread the book earned.
    if s.closed_n:
        held = scoped_n - s.closed_n
        open_txt = ("UNDEFINED — " + (s.open_undefined_reason or "")
                    if s.spread_open_only is None else f"{s.spread_open_only * 100:+.2f} pp")
        out += [f"  of which {s.closed_n} row(s) are CLOSED positions, still marked to horizon "
                f"(the call is scored; the exit was a capital decision)",
                f"  SAME SPREAD OVER THE {held} ROW(S) STILL HELD: {open_txt}"
                f"  [BUY n={s.open_buy_n} · AVOID n={s.open_avoid_n}]"]
    out += [f"  {s.caveat}", f"  {s.sign_convention}"]
    if snap.realized:
        out += ["", "REALIZED (closed positions — a separate view; never pooled into the spread)"]
        for rr in snap.realized:
            out.append(f"  {rr.ticker:<6} {rr.realized_return * 100:>+7.2f}%  "
                       f"{rr.entry_price:,.2f} {rr.entry_price_as_of} → "
                       f"{rr.exit_price:,.2f} {rr.exit_price_as_of}")
    if snap.freshness:
        out += ["", "FRESHNESS / TRIGGERS (machine flags; the human concludes)"]
        for f in snap.freshness:
            flag = "UNREAD PRINT" if f.unread_print else "current"
            out.append(f"  {f.ticker:<6} {flag:<13} evidence {f.last_evidence_date} "
                       f"({f.last_evidence_source}) · next print ~{f.next_expected_print} (est)")
            for nf in f.newer_filings:
                out.append(f"           newer: {nf}")
            for t in f.triggers:
                out.append(f"           trigger: {t}")
            # ADJACENT FIX, flagged in the shipping PR rather than silent (Item 2, 2026-08-29):
            # these flags were TYPED and persisted since the catalyst calendar but never rendered
            # here — an artifact-only flag the operator's console never showed. Every committed
            # day carries the field empty, so nothing ever misprinted; the gap was latent.
            for p in f.passed_trigger_deadlines:
                out.append(f"           ⚑ {p}")
            if f.watch_note:
                out.append(f"           note: {f.watch_note}")
    # THEME FALSIFIERS (brief Item 2) — always printed: "none declared" is a stated state, never
    # a silent absence (a card exists ⇔ rows exist, since a card carries ≥1 dated trigger).
    out += ["", "THEME FALSIFIERS (thesis cards; machine flags deadlines — the human concludes)"]
    if not snap.theme_falsifiers:
        out.append("  no thesis cards declared")
    for tf in snap.theme_falsifiers:
        if tf.deadline_passed:
            # the kind LEADS the flag (review 2026-08-31): without it a passed FIRST-CONFIRMING
            # printed indistinguishably from a passed falsifier — the human must see WHICH kind
            # of window closed before deciding what the re-underwrite is about.
            out.append(f"  {tf.driver_key:<24} ⚑ {tf.kind}: {tf.trigger} — deadline "
                       f"{tf.deadline} PASSED → re-underwrite due")
        else:
            out.append(f"  {tf.driver_key:<24}   {tf.kind}: {tf.trigger} (by {tf.deadline})")
        if tf.basis:
            out.append(f"{'':<28}basis: {tf.basis}")
    for n in snap.notes:
        out.append(f"NOTE: {n}")
    return "\n".join(out)
