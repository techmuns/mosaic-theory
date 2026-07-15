"""Component-A DRAFTING layer — one LLM call per UNREVIEWED cluster to draft a working name +
hypothesis + an ADVISORY disposition, so the human analyst triages faster. The machine DRAFTS; the
human OWNS. Reuses the graph LLM client (`llm.extract`), the LlmError→unassessed pattern, and the
#123 abort-fast (3 consecutive same-4xx → stop, never persist a poisoned run). A draft is a
HYPOTHESIS, never a fact, never a citation, never a decision — `suggested` is advisory only.
"""
from __future__ import annotations

from typing import Any

from vinci.graph.llm import LlmClient, LlmError
from vinci.themes.exposure import _client_error_status  # 4xx → systemic (abort); else None

_MATCH_MIN = 0.5  # member overlap (of the smaller set) that counts a cluster as already reviewed
_ABORT_AFTER = 3  # consecutive same-4xx (quota/auth) failures that abort before burning the budget
_SUGGESTIONS = ("keep-for-checks", "park", "reject")

_DRAFT_SYSTEM = (
    "You draft a working NAME and HYPOTHESIS for a cluster of co-moving small-cap US stocks, to "
    "help a human analyst triage it faster. You ASSEMBLE A HYPOTHESIS; you do NOT state facts, "
    "cite sources, or decide. Rules: (1) the hypothesis is a GUESS about the shared driver that "
    "might explain the co-movement — frame it as a hypothesis, never as established fact; (2) NO "
    "citations and NO claims about specific filings, numbers, or events; (3) `suggested` is "
    "ADVISORY ONLY — the analyst records the real decision, never you. keep-for-checks = worth the "
    "price + research checks; park = likely a factor/proxy that has already moved; reject = no "
    "shared driver / coincidence. Be terse."
)

DRAFT_TOOL: dict[str, Any] = {
    "name": "draft_theme",
    "description": (
        "Draft a working name + hypothesis for this co-moving cluster (ADVISORY, not a decision). "
        "The hypothesis is a guess about the shared driver, never a stated fact and never cited."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "draft_name": {"type": "string", "description": "a working label, <= 4 words"},
            "hypothesis": {
                "type": "string",
                "description": (
                    "<= 25 words; a HYPOTHESIS about the shared driver — not a fact, no citations"
                ),
            },
            "suggested": {"type": "string", "enum": list(_SUGGESTIONS)},
            "reason": {"type": "string", "description": "<= 15 words; why this suggestion"},
        },
        "required": ["draft_name", "hypothesis", "suggested", "reason"],
    },
}


class DraftAbortedError(RuntimeError):
    """3 consecutive same-4xx (quota/auth) failures — stop; do NOT persist a poisoned draft run."""

    def __init__(self, status: int, reason: str, drafted: list[dict[str, Any]]) -> None:
        super().__init__(f"draft aborted: {_ABORT_AFTER} consecutive {status} failures ({reason})")
        self.status, self.drafted = status, drafted


def _overlap(a: set[str], b: set[str]) -> float:
    return len(a & b) / min(len(a), len(b)) if a and b else 0.0


def unreviewed_clusters(clusters: list[dict[str, Any]],
                        reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The current clusters NOT matched to any review by member overlap (mirrors build.py's inbox
    matcher — matching is by MEMBERS, never cluster_id, which is per-run)."""
    review_sets = [set(r.get("members", [])) for r in reviews]
    out = []
    for c in clusters:
        cs = {m["ticker"] for m in c.get("members", [])}
        if not any(_overlap(cs, rs) >= _MATCH_MIN for rs in review_sets):
            out.append(c)
    return out


def _stat(cluster: dict[str, Any], *keys: str) -> Any:
    node: Any = cluster
    for k in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(k)
    return node


def _cluster_prompt(cluster: dict[str, Any]) -> str:
    members = cluster.get("members", [])
    rows = "\n".join(
        f"  {m.get('ticker', '?')}  {m.get('name', '')}  "
        f"(SIC {m.get('sic', '?')}, {m.get('sector', '?')})"
        for m in members)
    rel = _stat(cluster, "strength_signals", "rel_strength_vs_market", "h12mo", "value")
    mom = _stat(cluster, "strength_signals", "momentum", "h12mo", "value")
    stats = (
        f"rel-strength vs market 12mo {rel}, momentum 12mo {mom}, "
        f"coherence {_stat(cluster, 'admissibility', 'coherence_value')}, "
        f"breadth-expanding {_stat(cluster, 'strength_signals', 'breadth_expanding', 'value')}, "
        f"crowding {_stat(cluster, 'strength_signals', 'crowding_overextension', 'value')}")
    return (
        f"A cluster of {len(members)} co-moving US small-cap stocks (co-movement, not a stated "
        f"theme).\n\nMembers (ticker · company · industry):\n{rows}\n\n"
        f"Co-movement stats: {stats}\n\n"
        "Draft a working name + a HYPOTHESIS about the shared driver that might explain the "
        "co-movement, and an advisory disposition. Do not assert facts or cite anything.")


def draft_cluster(cluster: dict[str, Any], key: str, llm: LlmClient) -> dict[str, Any]:
    """One LLM draft for a cluster → a drafted record. Raises on any LLM/validation failure (the
    caller turns that into an unassessed-error record — NEVER a fabricated draft)."""
    raw = llm.extract(system=_DRAFT_SYSTEM, user=_cluster_prompt(cluster), tool=DRAFT_TOOL)
    suggested = str(raw.get("suggested", "")).strip()
    if suggested not in _SUGGESTIONS:  # tool enforces the enum; fail-loud never fabricates
        raise LlmError(f"invalid suggested {suggested!r} (not in {_SUGGESTIONS})")
    return {
        "key": key, "cluster_id": cluster["cluster_id"],
        "members": [m.get("ticker") for m in cluster.get("members", [])],
        "status": "drafted", "draft_name": str(raw.get("draft_name", "")).strip(),
        "hypothesis": str(raw.get("hypothesis", "")).strip(), "suggested": suggested,
        "reason": str(raw.get("reason", "")).strip(), "error": None, "model": llm.model,
    }


def _unassessed(cluster: dict[str, Any], key: str, model: str, error: str) -> dict[str, Any]:
    return {
        "key": key, "cluster_id": cluster["cluster_id"],
        "members": [m.get("ticker") for m in cluster.get("members", [])],
        "status": "unassessed-error", "draft_name": None, "hypothesis": None,
        "suggested": None, "reason": None, "error": error, "model": model,
    }


def draft_unreviewed(clusters: list[dict[str, Any]], reviews: list[dict[str, Any]], scan_date: str,
                     llm: LlmClient, *, progress: Any = None) -> list[dict[str, Any]]:
    """Draft every UNREVIEWED cluster (one LLM call each), keyed "<scan_date>:<cluster_id>". Any
    call error → an unassessed-error record with the reason (never a fabricated draft). Aborts fast
    on _ABORT_AFTER consecutive same-4xx (quota/auth) — raises DraftAbortedError, persists none."""
    todo = unreviewed_clusters(clusters, reviews)
    out: list[dict[str, Any]] = []
    streak, last_status = 0, None
    for i, c in enumerate(todo, 1):
        key = f"{scan_date}:{c['cluster_id']}"
        try:
            out.append(draft_cluster(c, key, llm))
            streak = 0  # a success breaks the systemic-failure streak
        except Exception as exc:  # noqa: BLE001 — LlmError or the SDK's APIStatusError; never drop
            status = _client_error_status(exc)
            if status is not None and status == last_status:
                streak += 1
            elif status is not None:
                streak = 1
            else:
                streak = 0  # 5xx / network transient — does NOT trip the abort
            last_status = status
            out.append(_unassessed(c, key, llm.model, f"{type(exc).__name__}: {exc}"))
            if status is not None and streak >= _ABORT_AFTER:
                raise DraftAbortedError(status, f"{type(exc).__name__}: {exc}", out) from exc
        if progress:
            progress(f"drafted {i}/{len(todo)}")
    return out
