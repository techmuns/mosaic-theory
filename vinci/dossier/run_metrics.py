"""What each dossier build COST and PRODUCED — one JSON line per name, as a dated series.

WHY (2026-10-23, Stage 0 of the agentic-engineering report). Before any loop may change a prompt
or an extractor, the process has to be measured: what a build spends, which of its calls fail, and
what it produced — the lean, whether the five draws agreed, how many caveats and QA flags it
raised. None of it was kept. The token counts lived on the client for one call at a time, and
`llm_call.log` is git-ignored. The report asks for two weeks of unbroken series first.

WHERE. ``<snapshots>/assembly_runs/<UTC start>-<run id>.jsonl`` — one file per assembly
invocation, one line per name ATTEMPTED, written as each name finishes. One file per run, never
one shared file: two worktrees assembling on the same day then add two files instead of
conflicting on the same last line. `data/snapshots/` is already committed, so the series rides the
artifact commit that carries the dossiers (CLAUDE.md: derived artifacts may be committed; code may
not ride with them).

A REFUSED OR FAILED NAME IS RECORDED TOO. A re-rolled synthesis is paid for, and the refusal is
the outcome a loop most needs to count. ``outcome`` says which: ``written``, ``refused`` (a
`DossierAssemblyError`, the build's own guards) or ``failed`` (anything else).

THE RECORD — shape contract, one literal example (abridged to one call):

    {"schema": 1, "run_id": "3f9c2a1b", "ticker": "VRRM", "outcome": "written", "error": null,
     "started_at": "2026-10-23T13:40:12Z", "finished_at": "2026-10-23T13:44:57Z", "seconds": 285.0,
     "model": "claude-opus-4-8", "extraction_version": "…",
     "calls": [{"phase": "assemble_dossier_framing", "ok": true, "error": null,
                "cached_prompt": true,
                "usage": {"input_tokens": 41, "output_tokens": 4120,
                          "cache_creation_input_tokens": 112791, "cache_read_input_tokens": 0,
                          "max_tokens": 16384}}],
     "totals": {"calls": 8, "failed_calls": 0, "unmetered_calls": 0, "input_tokens": …,
                "output_tokens": …, "cache_creation_input_tokens": …,
                "cache_read_input_tokens": …},
     "usd": 1.93,
     "synthesis": {"lean": "strongly-bullish", "lean_raw": "Strongly bullish",
                   "draws": {"attempted": 5, "completed": 5,
                             "labels": {"strongly-bullish": 5}, "unanimous": true}},
     "flags": {"caveats": 4, "qa_flags": 11}}

BOUNDARIES THE FIELDS CARRY. ``usd`` is list price over the METERED calls only; a call that got no
response is counted in ``unmetered_calls`` and adds nothing. ``usd`` is ``null`` when the model has
no list price (`vinci.config.LLM_PRICE_PER_MTOK`) — unknown, never zero — and ``0.0`` on a build
with no LLM client, which made no call. The phase is the tool name: ``covenant_terms``,
``maturity_event``, ``operating_drivers``, ``assemble_dossier_framing`` (synthesis).
``synthesis`` and ``flags`` are ``null`` when nothing was written. An ``error`` longer than 300
characters says it was cut.
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vinci.dossier.extraction_version import EXTRACTION_VERSION
from vinci.dossier.schemas import Dossier
from vinci.dossier.verdict import split_lean
from vinci.graph.llm import MeteredLlmClient, cost_usd

SCHEMA = 1
RUNS_DIR = "assembly_runs"
ERROR_CAP = 300
_TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                 "cache_read_input_tokens")


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _capped(text: str | None) -> str | None:
    """The text, or its first ERROR_CAP characters with a statement that it was cut."""
    if text is None or len(text) <= ERROR_CAP:
        return text
    return f"{text[:ERROR_CAP]}… [first {ERROR_CAP} of {len(text)} characters]"


class RunLog:
    """One assembly invocation's file. Safe to add to from `assemble_cohort`'s worker threads."""

    def __init__(self, snapshots_dir: Path, *, started: datetime | None = None) -> None:
        started = started or datetime.now(UTC)
        self.run_id = uuid.uuid4().hex[:8]
        self.path = (snapshots_dir / RUNS_DIR
                     / f"{started.astimezone(UTC):%Y-%m-%dT%H-%M-%SZ}-{self.run_id}.jsonl")
        self.records: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def add(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, sort_keys=True)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            self.records.append(record)


def _synthesis(dossier: Dossier) -> dict[str, Any] | None:
    s = dossier.synthesis
    if s is None:
        return None
    parts = split_lean(s.evidence_balance) if s.evidence_balance.strip() else None
    raw = parts[0].strip() if parts else None
    da = s.draw_agreement
    return {"lean": re.sub(r"\s+", "-", raw.lower()) if raw else None, "lean_raw": raw,
            "draws": da.model_dump(mode="json") if da is not None else None}


def name_record(
    *, run_id: str, ticker: str, started: datetime, finished: datetime,
    meter: MeteredLlmClient | None, dossier: Dossier | None = None,
    error: BaseException | None = None,
) -> dict[str, Any]:
    """One name's line. Pass ``dossier`` for a written build, ``error`` for one that raised."""
    from vinci.dossier.assemble import DossierAssemblyError

    calls = [{**c, "error": _capped(c["error"])} for c in (meter.calls if meter else [])]
    metered = [c["usage"] for c in calls if c["usage"] is not None]
    model = meter.model if meter else None
    costs = [cost_usd(model, u) for u in metered] if model is not None else []
    outcome = ("written" if error is None
               else "refused" if isinstance(error, DossierAssemblyError) else "failed")
    return {
        "schema": SCHEMA, "run_id": run_id, "ticker": ticker, "outcome": outcome,
        "error": _capped(f"{type(error).__name__}: {error}") if error is not None else None,
        "started_at": _iso(started), "finished_at": _iso(finished),
        "seconds": round((finished - started).total_seconds(), 1),
        "model": model, "extraction_version": EXTRACTION_VERSION,
        "calls": calls,
        "totals": {"calls": len(calls), "failed_calls": sum(1 for c in calls if not c["ok"]),
                   "unmetered_calls": len(calls) - len(metered),
                   **{k: sum(u.get(k, 0) for u in metered) for k in _TOKEN_FIELDS}},
        "usd": (0.0 if meter is None
                else round(sum(c for c in costs if c is not None), 6)
                if all(c is not None for c in costs) else None),
        "synthesis": _synthesis(dossier) if dossier is not None else None,
        "flags": ({"caveats": len(dossier.caveats), "qa_flags": len(dossier.qa_flags)}
                  if dossier is not None else None),
    }


def summary(records: list[dict[str, Any]]) -> list[str]:
    """The console lines for a run: one per name, then the run's total — every name counted."""
    lines = []
    for r in sorted(records, key=lambda r: str(r["ticker"])):
        t = r["totals"]
        usd = "unpriced" if r["usd"] is None else f"${r['usd']:.2f}"
        lean = (r["synthesis"] or {}).get("lean") or "—"
        lines.append(f"  {r['ticker']:<6} {r['outcome']:<8} {t['calls']} call(s), "
                     f"{t['failed_calls']} failed · {usd} · lean {lean}")
    priced = [r["usd"] for r in records if r["usd"] is not None]
    unpriced = len(records) - len(priced)
    lines.append(f"  total ${sum(priced):.2f} over {len(priced)} of {len(records)} name(s)"
                 + (f" ({unpriced} unpriced)" if unpriced else ""))
    return lines
