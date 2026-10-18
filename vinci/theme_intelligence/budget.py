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
"""

from __future__ import annotations

import json
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
class SpendGuard:
    run_limit: float | None = None
    run_spent: float = 0.0
    doc_limit: float | None = None
    doc_spent: float = 0.0
    doc_label: str = ""
    retry_spent: float = 0.0
    doc_extractions: int = 0
    retry_share: float = DOC_RETRY_COMPLETENESS_SHARE
    calls: list[dict[str, Any]] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    #: calls that reached the model, not yet matched to a ledger row (`sent` / `recorded`)
    unrecorded: list[dict[str, Any]] = field(default_factory=list)

    def start_run(self, mode: str, limit: float | None = None,
                  carried: dict[str, Any] | None = None) -> None:
        """`carried`: a RESUMED run's earlier spend summary — its spend, calls and refusals
        count against the same limit (a resume restarted at $0 and could spend it twice)."""
        self.run_limit = default_run_limit(mode) if limit is None else limit
        self.run_spent = float((carried or {}).get("spent_usd") or 0.0)
        self.calls = list((carried or {}).get("calls") or [])
        self.refusals = list((carried or {}).get("refusals") or [])
        self.unrecorded = []
        self.end_document()

    def begin_document(self, label: str, limit: float | None = None,
                       retry_share: float = DOC_RETRY_COMPLETENESS_SHARE) -> None:
        """`retry_share`: the part of the limit retries and completeness passes may take — the
        whole of it when the document IS one such call (`reask-part`: 2026-10-14, `--max-cost
        1.00` refused a $0.90 call at its $0.85 share)."""
        self.doc_label = label
        self.doc_limit = DOC_COST_LIMIT_USD if limit is None else limit
        self.retry_share = retry_share
        self.doc_spent = self.retry_spent = 0.0
        self.doc_extractions = 0

    def end_document(self) -> None:
        self.doc_label, self.doc_limit = "", None
        self.doc_spent = self.retry_spent = 0.0
        self.doc_extractions = 0

    @property
    def retry_limit(self) -> float | None:
        return None if self.doc_limit is None else self.doc_limit * self.retry_share

    def remaining(self, kind: str) -> tuple[float, str]:
        """The smallest remaining limit that applies to a call of this kind, and its name."""
        left, which, _scope = self._tightest(kind)
        return left, which

    def _tightest(self, kind: str) -> tuple[float, str, str]:
        rows: list[tuple[float, str, str]] = []
        if self.run_limit is not None:
            rows.append((self.run_limit - self.run_spent, f"the run budget ${self.run_limit:,.2f}",
                         "run"))
        if self.doc_limit is not None:
            rows.append((self.doc_limit - self.doc_spent,
                         f"the document limit ${self.doc_limit:,.2f} ({self.doc_label})",
                         "document"))
            if kind in ("completeness", "retry") and self.retry_limit is not None:
                rows.append((self.retry_limit - self.retry_spent,
                             f"the retry / completeness limit ${self.retry_limit:,.2f} "
                             f"({self.doc_label})", "retry"))
        if not rows:
            return float("inf"), "no limit", ""
        return min(rows)

    def classify(self, tool: dict[str, Any]) -> str:
        kind = _KIND.get(str(tool.get("name", "")), "extraction")
        if kind == "extraction":
            self.doc_extractions += 1
            if self.doc_extractions > 1:  # a re-extraction (compact mode) is a retry
                kind = "retry"
        return kind

    def check(self, bound: float, kind: str) -> None:
        left, which, scope = self._tightest(kind)
        if bound > left:
            msg = (f"a {kind} call bounded at ${bound:,.2f} does not fit the remaining "
                   f"${max(left, 0.0):,.2f} of {which} — not sent")
            self.refusals.append(msg)
            raise BudgetExceeded(msg, scope=scope)

    def sent(self, kind: str, usage: dict[str, int] | None, cost: float | None,
             error: str = "", tool: str = "") -> None:
        """A call the model BILLED — its answer used or not (`error`: why not)."""
        self.unrecorded.append({"kind": kind, "tool": tool, "document": self.doc_label,
                                "usage": usage, "cost_usd": cost, "error": error})

    def recorded(self, usage: dict[str, int] | None) -> None:
        """A ledger row was written for one sent call (matched by its usage)."""
        for i, e in enumerate(self.unrecorded):
            if e["usage"] == usage:
                del self.unrecorded[i]
                return

    def take_unrecorded(self) -> list[dict[str, Any]]:
        out, self.unrecorded = self.unrecorded, []
        return out

    def record(self, kind: str, bound: float, actual: float | None) -> None:
        spent = bound if actual is None else actual  # an unreported cost counts at its bound
        self.run_spent += spent
        self.doc_spent += spent
        if kind in ("completeness", "retry"):
            self.retry_spent += spent
        self.calls.append({"kind": kind, "document": self.doc_label, "bound_usd": round(bound, 4),
                           "actual_usd": None if actual is None else round(actual, 4)})

    def summary(self) -> dict[str, Any]:
        measured = [c for c in self.calls if c["actual_usd"] is not None]
        return {"run_limit_usd": self.run_limit, "spent_usd": round(self.run_spent, 4),
                "paid_calls": len(self.calls),
                "bound_total_usd": round(sum(c["bound_usd"] for c in self.calls), 4),
                "actual_total_usd": round(sum(c["actual_usd"] for c in measured), 4),
                "calls_over_their_bound": sum(1 for c in measured
                                              if c["actual_usd"] > c["bound_usd"]),
                "refusals": list(self.refusals), "calls": list(self.calls)}


class GuardedClient:
    """The model client behind the guard: bound, check, call, record. Same interface."""

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

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **kw: Any) -> dict[str, Any]:
        from vinci.theme_intelligence.extract import cost_of

        kind = self._guard.classify(tool)
        name = str(tool.get("name", "")).removeprefix("record_")
        bound = call_bound(self.model, system, user, tool, cache_write=bool(kw.get("cache")))
        self._guard.check(bound, kind)
        before = self.last_usage
        try:
            out: dict[str, Any] = self._inner.extract(system=system, user=user, tool=tool, **kw)
        except BaseException as exc:
            after = self.last_usage  # billed and then failed (a truncation): still spent
            billed = after if after is not None and after is not before else None
            cost = cost_of(self.model, billed) if billed is not None else None
            self._guard.record(kind, bound, cost)
            if billed is not None:  # no usage reported: not shown billed (the guard counts the
                self._guard.sent(kind, billed, cost,  # bound all the same)
                                 f"{type(exc).__name__}: {str(exc)[:200]}", name)
            raise
        cost = cost_of(self.model, self.last_usage)
        self._guard.record(kind, bound, cost)
        self._guard.sent(kind, self.last_usage, cost, tool=name)
        return out
