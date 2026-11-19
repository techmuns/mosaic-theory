"""Spending limits on the model — checked BEFORE every paid call, recorded after it.

Measured 2026-10-11 (list price, claude-opus-4-8): Citi's 60-page Gridlock report cost $46.67
through the full pipeline, its 57-page LatAm report $9.47, its ETF page and 34-page report $3.80.
These are model-processing costs, not publisher fees.

LIMITS (config; the CLI raises them per run or document):
- a RUN: a weekly scan (`SCAN_BUDGET_USD`) or a manual batch — `ingest-file`, `ingest-inbox`,
  `article` (`BATCH_BUDGET_USD`);
- a DOCUMENT (one article or supplied report, all its calls): `DOC_COST_LIMIT_USD`, or the
  document's `--max-cost`;
- its RETRIES AND COMPLETENESS PASSES (a compact re-extraction, every completeness part and
  split): `DOC_RETRY_COMPLETENESS_SHARE` of the document limit, so extraction and card reviews
  always keep a share.

BEFORE A CALL. Its cost is BOUNDED: input tokens at most (characters of the system prompt, the
message and the tool schema) / `CHARS_PER_TOKEN_BOUND` — below every ratio measured on real calls
(config) — each priced at the rate it is billed at, a call that writes the prompt cache at the
cache-write rate, plus the call's full output cap. A call whose bound does not fit the smallest
remaining limit is REFUSED (`BudgetExceeded`) — it is never sent. This is a conservative bound
from the request's size, NOT a provider-side billing cap: a pathological text that tokenises
finer than the ratio could cost more than bounded. Every call records its bound and its actual
cost, so the bound is checked against the bill (the run manifest carries both).

AFTER A REFUSAL. Nothing about the article is written: the pipeline checkpoints it
(BUDGET_HELD), the answers already paid for stay in the content-addressed cache, and a re-run
with a higher limit (`--max-cost`, `--budget`, `--release`) resumes without paying for them
again. A refusal says WHICH limit refused it (`BudgetExceeded.scope`): a scan stops and queues
the rest only when its RUN budget is spent; a document's own limit holds that document alone.

THE LEDGER. Every call the model billed is reported (`SpendGuard.sent`), its answer used or
not; the pipeline records the ones no other path recorded — a call that ended in an exception
is still a paid call, and was missing from the run's cost (2026-10-14).

A RESUMED run carries its earlier attempt's spend (`start_run(carried=)`): one run id spends its
limit once.

CONCURRENT CALLS (2026-11-19, operator: speed it up "without compromising the quality"). The
check RESERVES: a call is admitted only if its bound fits what is left once every call still in
flight is counted at ITS bound, and that bound is held until the call settles at its actual
cost. So calls sent together can never jointly pass a run's or a document's limit, whatever
order they finish in (before, two threads could each read the same remaining dollars and both
be sent). A concurrent pass admits its calls on ONE thread, in input order, each against its own
document (`scope`). When the run's budget is what refuses a call while others are in flight, the
pass first waits for them (`reserve(make_room=)`), so a refusal is decided only with nothing in
flight: the same call a one-at-a-time pass would have refused. The rows of `calls` are written
at admission, in that order.

BOTH CLAIMS ASSUME EACH CALL COSTS NO MORE THAN ITS BOUND — the guard's own premise above, and
`summary()` counts the calls that broke it (`calls_over_their_bound`). A call that costs more
spends past its bound whether it ran alone or beside others, and a concurrent pass may then admit
a call a one-at-a-time pass, which would already have seen that overrun, refuses.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from vinci.theme_intelligence.config import (
    BATCH_BUDGET_USD,
    CHARS_PER_TOKEN_BOUND,
    DOC_COST_LIMIT_USD,
    DOC_RETRY_COMPLETENESS_SHARE,
    LLM_MAX_TOKENS,
    PRICE_PER_MTOK,
    SCAN_BUDGET_USD,
)

#: tool name → spending category (anything else is an extraction)
_KIND = {"record_completeness": "completeness", "record_review": "review"}
#: the kinds that also draw on a document's retry / completeness share
_RETRY_KINDS = ("completeness", "retry")


class BudgetExceeded(Exception):  # noqa: N818 — the operator-facing name
    """A paid call was refused: its bounded cost does not fit the remaining authorised budget.
    Deliberately NOT a RuntimeError, so no "pass not run" handler swallows it. `scope` names the
    limit that refused it: "run", "document", "retry" (a document's retry / completeness share)
    or "price" (no price configured)."""

    def __init__(self, msg: str, *, scope: str = "run") -> None:
        super().__init__(msg)
        self.scope = scope


def call_bound(model: str, system: str, user: str, tool: dict[str, Any],
               max_tokens: int = LLM_MAX_TOKENS, *, cache_write: bool = False) -> float:
    """The conservative cost bound of one call (USD), from its size and output cap. `cache_write`:
    the call writes the prompt cache (a completeness part under `PROMPT_CACHE_PARTS`), so its input
    is billed at 1.25x — before U28 every call was priced so, which left a cache write no margin
    for a request that tokenises finer than the ratio."""
    if model not in PRICE_PER_MTOK:
        raise BudgetExceeded(f"no price is configured for {model!r} — a call cannot be bounded, "
                             f"so it is not made (add it to config.PRICE_PER_MTOK)",
                             scope="price")
    pin, pout = PRICE_PER_MTOK[model]
    chars = len(system) + len(user) + len(json.dumps(tool))
    in_tok = chars / CHARS_PER_TOKEN_BOUND
    return (in_tok * pin * (1.25 if cache_write else 1.0) + max_tokens * pout) / 1_000_000


def default_run_limit(mode: str) -> float:
    return SCAN_BUDGET_USD if mode == "scan" else BATCH_BUDGET_USD


@dataclass
class DocScope:
    """One document's limit and spend: the guard's CURRENT one (`begin_document`, the
    one-at-a-time path), or one a concurrent pass opens per item (`SpendGuard.scope`) and names
    on each of its calls. `reserved` / `retry_reserved`: the bounds of its calls in flight."""
    label: str = ""
    limit: float | None = None
    retry_share: float = DOC_RETRY_COMPLETENESS_SHARE
    spent: float = 0.0
    retry_spent: float = 0.0
    extractions: int = 0
    reserved: float = 0.0
    retry_reserved: float = 0.0
    in_flight: int = 0

    @property
    def retry_limit(self) -> float | None:
        return None if self.limit is None else self.limit * self.retry_share


@dataclass(frozen=True)
class Reservation:
    """An admitted call's hold on the budget, until `SpendGuard.settle`. `row`: its row in
    `SpendGuard.calls`, written at admission — the rows keep the order calls were ADMITTED in,
    never the order they happened to finish in."""
    kind: str
    bound: float
    doc: DocScope
    row: int


@dataclass
class SpendGuard:
    run_limit: float | None = None
    run_spent: float = 0.0
    calls: list[dict[str, Any]] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    #: calls that reached the model, not yet matched to a ledger row (`sent` / `recorded`)
    unrecorded: list[dict[str, Any]] = field(default_factory=list)
    #: the bounds of the calls admitted and not yet settled, and how many there are
    run_reserved: float = 0.0
    in_flight: int = 0
    #: the CURRENT document (`begin_document`): a call that names no scope draws on it
    doc: DocScope = field(default_factory=DocScope)
    #: held by every read and write of the totals above — a call may settle on any thread
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def start_run(self, mode: str, limit: float | None = None,
                  carried: dict[str, Any] | None = None) -> None:
        """`carried`: a RESUMED run's earlier spend summary — its spend, calls and refusals
        count against the same limit (a resume restarted at $0 and could spend it twice)."""
        with self._lock:
            if self.in_flight:  # its row and spend would land in the new run's
                raise RuntimeError(f"a run started with {self.in_flight} paid call(s) in flight")
            self.run_limit = default_run_limit(mode) if limit is None else limit
            self.run_spent = float((carried or {}).get("spent_usd") or 0.0)
            self.calls = list((carried or {}).get("calls") or [])
            self.refusals = list((carried or {}).get("refusals") or [])
            self.unrecorded = []
        self.end_document()

    def scope(self, label: str, limit: float | None = None,
              retry_share: float = DOC_RETRY_COMPLETENESS_SHARE) -> DocScope:
        """A new document's limits (default `DOC_COST_LIMIT_USD`), NOT made current."""
        return DocScope(label=label, limit=DOC_COST_LIMIT_USD if limit is None else limit,
                        retry_share=retry_share)

    def begin_document(self, label: str, limit: float | None = None,
                       retry_share: float = DOC_RETRY_COMPLETENESS_SHARE) -> None:
        """`retry_share`: the part of the limit retries and completeness passes may take — the
        whole of it when the document IS one such call (`reask-part`: 2026-10-14, `--max-cost
        1.00` refused a $0.90 call at its $0.85 share)."""
        self.doc = self.scope(label, limit, retry_share)

    def end_document(self) -> None:
        self.doc = DocScope()

    @property
    def retry_limit(self) -> float | None:
        return self.doc.retry_limit

    def remaining(self, kind: str, doc: DocScope | None = None) -> tuple[float, str]:
        """The smallest remaining limit that applies to a call of this kind, and its name —
        with every call in flight counted at its bound."""
        with self._lock:
            left, which, _scope = self._tightest(kind, doc or self.doc)
        return left, which

    def _tightest(self, kind: str, doc: DocScope) -> tuple[float, str, str]:
        """(the caller holds the lock)"""
        rows: list[tuple[float, str, str]] = []
        if self.run_limit is not None:
            rows.append((self.run_limit - self.run_spent - self.run_reserved,
                         f"the run budget ${self.run_limit:,.2f}", "run"))
        if doc.limit is not None:
            rows.append((doc.limit - doc.spent - doc.reserved,
                         f"the document limit ${doc.limit:,.2f} ({doc.label})", "document"))
            if kind in _RETRY_KINDS and doc.retry_limit is not None:
                rows.append((doc.retry_limit - doc.retry_spent - doc.retry_reserved,
                             f"the retry / completeness limit ${doc.retry_limit:,.2f} "
                             f"({doc.label})", "retry"))
        if not rows:
            return float("inf"), "no limit", ""
        return min(rows)

    def classify(self, tool: dict[str, Any], doc: DocScope | None = None) -> str:
        d = doc or self.doc
        kind = _KIND.get(str(tool.get("name", "")), "extraction")
        if kind == "extraction":
            with self._lock:
                d.extractions += 1
                n = d.extractions
            if n > 1:  # a re-extraction (compact mode) is a retry
                kind = "retry"
        return kind

    def _refuse_unless_fits(self, bound: float, kind: str, doc: DocScope) -> None:
        """(the caller holds the lock)"""
        left, which, scope = self._tightest(kind, doc)
        if bound > left:
            msg = (f"a {kind} call bounded at ${bound:,.2f} does not fit the remaining "
                   f"${max(left, 0.0):,.2f} of {which} — not sent")
            self.refusals.append(msg)
            raise BudgetExceeded(msg, scope=scope)

    def check(self, bound: float, kind: str, doc: DocScope | None = None) -> None:
        """Refuse (`BudgetExceeded`) a bound that does not fit; holds nothing (`reserve` does)."""
        with self._lock:
            self._refuse_unless_fits(bound, kind, doc or self.doc)

    def reserve(self, bound: float, kind: str, doc: DocScope | None = None, *,
                make_room: Callable[[], bool] | None = None) -> Reservation:
        """Admit one call: its bound must fit what is left with every call in flight counted at
        its bound, and is held until `settle`. `make_room` (a concurrent pass): called, outside
        the lock, whenever the RUN's remaining budget is what refuses, to finish the oldest call
        still in flight; it returns False once there is none. So the run's refusal is decided
        only with nothing in flight, against the dollars a one-at-a-time pass would have had."""
        d = doc or self.doc
        while True:
            with self._lock:
                left, _which, scope = self._tightest(kind, d)
                if not (bound > left and make_room is not None and scope == "run"):
                    self._refuse_unless_fits(bound, kind, d)
                    self.run_reserved += bound
                    self.in_flight += 1
                    d.reserved += bound
                    d.in_flight += 1
                    if kind in _RETRY_KINDS:
                        d.retry_reserved += bound
                    self.calls.append({"kind": kind, "document": d.label,
                                       "bound_usd": round(bound, 4), "actual_usd": None})
                    return Reservation(kind, bound, d, len(self.calls) - 1)
            if not make_room():  # nothing left in flight: the next look decides
                make_room = None

    def settle(self, r: Reservation, actual: float | None) -> None:
        """An admitted call is over: its hold released, its cost spent (an unreported cost at its
        bound) and written into the row its admission opened."""
        with self._lock:
            self.in_flight -= 1
            r.doc.in_flight -= 1
            # each sum is zeroed once nothing is in flight: no float residue is ever held
            self.run_reserved = self.run_reserved - r.bound if self.in_flight else 0.0
            r.doc.reserved = r.doc.reserved - r.bound if r.doc.in_flight else 0.0
            if r.kind in _RETRY_KINDS:
                r.doc.retry_reserved = (r.doc.retry_reserved - r.bound if r.doc.in_flight
                                        else 0.0)
            self._spend(r.kind, r.bound if actual is None else actual, r.doc)
            self.calls[r.row]["actual_usd"] = None if actual is None else round(actual, 4)

    def sent(self, kind: str, usage: dict[str, int] | None, cost: float | None,
             error: str = "", tool: str = "", doc: DocScope | None = None) -> None:
        """A call the model BILLED — its answer used or not (`error`: why not)."""
        with self._lock:
            self.unrecorded.append({"kind": kind, "tool": tool,
                                    "document": (doc or self.doc).label,
                                    "usage": usage, "cost_usd": cost, "error": error})

    def recorded(self, usage: dict[str, int] | None, document: str | None = None) -> None:
        """A ledger row was written for one sent call: matched by its usage and, when the caller
        knows it, its document's label. By usage alone, two calls in flight with equal token
        counts could swap rows, so a paid call left unrecorded is labelled with another
        document's name (round 1 of #1141). A call with no label, or none sent under it, matches
        by usage, as before — never left over as a paid call no row recorded."""
        with self._lock:
            hits = [i for i, e in enumerate(self.unrecorded) if e["usage"] == usage]
            own = [i for i in hits if self.unrecorded[i]["document"] == document]
            if own or hits:
                del self.unrecorded[(own or hits)[0]]

    def take_unrecorded(self) -> list[dict[str, Any]]:
        with self._lock:
            out, self.unrecorded = self.unrecorded, []
        return out

    def _spend(self, kind: str, spent: float, doc: DocScope) -> None:
        """(the caller holds the lock)"""
        self.run_spent += spent
        doc.spent += spent
        if kind in _RETRY_KINDS:
            doc.retry_spent += spent

    def record(self, kind: str, bound: float, actual: float | None,
               doc: DocScope | None = None) -> None:
        """A call's spend recorded without an admission (`reserve` / `settle` is the guarded
        client's path)."""
        with self._lock:
            d = doc or self.doc
            self._spend(kind, bound if actual is None else actual, d)  # unreported: its bound
            self.calls.append({"kind": kind, "document": d.label, "bound_usd": round(bound, 4),
                               "actual_usd": None if actual is None else round(actual, 4)})

    def summary(self) -> dict[str, Any]:
        with self._lock:
            calls = [dict(c) for c in self.calls]
            refusals = list(self.refusals)
            spent = self.run_spent
        measured = [c for c in calls if c["actual_usd"] is not None]
        return {"run_limit_usd": self.run_limit, "spent_usd": round(spent, 4),
                "paid_calls": len(calls),
                "bound_total_usd": round(sum(c["bound_usd"] for c in calls), 4),
                "actual_total_usd": round(sum(c["actual_usd"] for c in measured), 4),
                "calls_over_their_bound": sum(1 for c in measured
                                              if c["actual_usd"] > c["bound_usd"]),
                "refusals": refusals, "calls": calls}


@dataclass(frozen=True)
class Admitted:
    """A call the guard admitted and holds budget for (`GuardedClient.admit`), not yet sent."""
    system: str
    user: str
    tool: dict[str, Any]
    kw: dict[str, Any]
    name: str
    reservation: Reservation


class GuardedClient:
    """The model client behind the guard: bound, reserve, call, settle. Same interface.

    `extract` admits and sends on the calling thread. A concurrent pass splits the two: it
    ADMITS on one thread, in input order (`admit`), and SENDS on a worker (`send`)."""

    def __init__(self, inner: Any, guard: SpendGuard) -> None:
        self._inner = inner
        self._guard = guard

    @property
    def model(self) -> str:
        return str(self._inner.model)

    @property
    def max_tokens(self) -> int | None:
        """The wrapped client's output cap, when it states one (a truncation marker is read
        against it)."""
        cap = getattr(self._inner, "max_tokens", None)
        return cap if isinstance(cap, int) else None

    @property
    def last_usage(self) -> dict[str, int] | None:
        u = getattr(self._inner, "last_usage", None)
        return u if isinstance(u, dict) else None

    @property
    def usage_per_thread(self) -> bool:
        """The wrapped client keeps each call's `last_usage` on the thread that made it, so its
        calls may be sent from several threads at once. A client that does not say so is sent
        one call at a time: a usage read after its call could be another thread's."""
        return getattr(self._inner, "usage_per_thread", False) is True

    def admit(self, *, system: str, user: str, tool: dict[str, Any],
              doc: DocScope | None = None, make_room: Callable[[], bool] | None = None,
              **kw: Any) -> Admitted:
        kind = self._guard.classify(tool, doc)
        name = str(tool.get("name", "")).removeprefix("record_")
        bound = call_bound(self.model, system, user, tool, cache_write=bool(kw.get("cache")))
        r = self._guard.reserve(bound, kind, doc, make_room=make_room)
        return Admitted(system, user, tool, kw, name, r)

    def send(self, a: Admitted) -> dict[str, Any]:
        from vinci.theme_intelligence.extract import cost_of

        r = a.reservation
        before = self.last_usage
        try:
            out: dict[str, Any] = self._inner.extract(system=a.system, user=a.user, tool=a.tool,
                                                      **a.kw)
        except BaseException as exc:
            after = self.last_usage  # billed and then failed (a truncation): still spent
            billed = after if after is not None and after is not before else None
            cost = cost_of(self.model, billed) if billed is not None else None
            self._guard.settle(r, cost)
            if billed is not None:  # no usage reported: not shown billed (the guard counts the
                self._guard.sent(r.kind, billed, cost,  # bound all the same)
                                 f"{type(exc).__name__}: {str(exc)[:200]}", a.name, r.doc)
            raise
        usage = self.last_usage
        cost = cost_of(self.model, usage)
        self._guard.settle(r, cost)
        self._guard.sent(r.kind, usage, cost, tool=a.name, doc=r.doc)
        return out

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **kw: Any) -> dict[str, Any]:
        return self.send(self.admit(system=system, user=user, tool=tool, **kw))
