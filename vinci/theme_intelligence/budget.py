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
message and the tool schema) / `CHARS_PER_TOKEN_BOUND`, all priced as cache WRITES (the dearest
input rate), plus the call's full output cap. A call whose bound does not fit the smallest
remaining limit is REFUSED (`BudgetExceeded`) — it is never sent. This is a conservative bound
from the request's size, NOT a provider-side billing cap: a pathological text that tokenises
finer than the ratio could cost more than bounded. Every call records its bound and its actual
cost, so the bound is checked against the bill (the run manifest carries both).

AFTER A REFUSAL. Nothing about the article is written: the pipeline checkpoints it
(BUDGET_HELD), the answers already paid for stay in the content-addressed cache, and a re-run
with a higher limit (`--max-cost`, `--budget`, `--release`) resumes without paying for them
again. A scan stops at the first refusal and queues the rest.
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
    Deliberately NOT a RuntimeError, so no "pass not run" handler swallows it."""


def call_bound(model: str, system: str, user: str, tool: dict[str, Any],
               max_tokens: int = LLM_MAX_TOKENS) -> float:
    """The conservative cost bound of one call (USD), from its size and output cap."""
    if model not in PRICE_PER_MTOK:
        raise BudgetExceeded(f"no price is configured for {model!r} — a call cannot be bounded, "
                             f"so it is not made (add it to config.PRICE_PER_MTOK)")
    pin, pout = PRICE_PER_MTOK[model]
    chars = len(system) + len(user) + len(json.dumps(tool))
    in_tok = chars / CHARS_PER_TOKEN_BOUND
    return (in_tok * pin * 1.25 + max_tokens * pout) / 1_000_000


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
    calls: list[dict[str, Any]] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)

    def start_run(self, mode: str, limit: float | None = None) -> None:
        self.run_limit = default_run_limit(mode) if limit is None else limit
        self.run_spent = 0.0
        self.calls, self.refusals = [], []
        self.end_document()

    def begin_document(self, label: str, limit: float | None = None) -> None:
        self.doc_label = label
        self.doc_limit = DOC_COST_LIMIT_USD if limit is None else limit
        self.doc_spent = self.retry_spent = 0.0
        self.doc_extractions = 0

    def end_document(self) -> None:
        self.doc_label, self.doc_limit = "", None
        self.doc_spent = self.retry_spent = 0.0
        self.doc_extractions = 0

    @property
    def retry_limit(self) -> float | None:
        return None if self.doc_limit is None else self.doc_limit * DOC_RETRY_COMPLETENESS_SHARE

    def remaining(self, kind: str) -> tuple[float, str]:
        """The smallest remaining limit that applies to a call of this kind, and its name."""
        rows: list[tuple[float, str]] = []
        if self.run_limit is not None:
            rows.append((self.run_limit - self.run_spent, f"the run budget ${self.run_limit:,.2f}"))
        if self.doc_limit is not None:
            rows.append((self.doc_limit - self.doc_spent,
                         f"the document limit ${self.doc_limit:,.2f} ({self.doc_label})"))
            if kind in ("completeness", "retry") and self.retry_limit is not None:
                rows.append((self.retry_limit - self.retry_spent,
                             f"the retry / completeness limit ${self.retry_limit:,.2f} "
                             f"({self.doc_label})"))
        if not rows:
            return float("inf"), "no limit"
        return min(rows)

    def classify(self, tool: dict[str, Any]) -> str:
        kind = _KIND.get(str(tool.get("name", "")), "extraction")
        if kind == "extraction":
            self.doc_extractions += 1
            if self.doc_extractions > 1:  # a re-extraction (compact mode) is a retry
                kind = "retry"
        return kind

    def check(self, bound: float, kind: str) -> None:
        left, which = self.remaining(kind)
        if bound > left:
            msg = (f"a {kind} call bounded at ${bound:,.2f} does not fit the remaining "
                   f"${max(left, 0.0):,.2f} of {which} — not sent")
            self.refusals.append(msg)
            raise BudgetExceeded(msg)

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
    def last_usage(self) -> dict[str, int] | None:
        u = getattr(self._inner, "last_usage", None)
        return u if isinstance(u, dict) else None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **kw: Any) -> dict[str, Any]:
        from vinci.theme_intelligence.extract import cost_of

        kind = self._guard.classify(tool)
        bound = call_bound(self.model, system, user, tool)
        self._guard.check(bound, kind)
        before = self.last_usage
        try:
            out: dict[str, Any] = self._inner.extract(system=system, user=user, tool=tool, **kw)
        except BaseException:
            after = self.last_usage  # billed and then failed (a truncation): still spent
            self._guard.record(kind, bound, cost_of(self.model, after)
                               if after is not None and after is not before else None)
            raise
        self._guard.record(kind, bound, cost_of(self.model, self.last_usage))
        return out
