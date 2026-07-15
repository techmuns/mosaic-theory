"""Component-A DRAFTING layer — one LLM call per cluster to draft a working name + hypothesis + an
ADVISORY triage disposition, so the human analyst decides faster. The machine DRAFTS; the human
OWNS. Reuses the graph LLM client (`llm.extract`), the LlmError→unassessed pattern, and the #123
abort-fast (3 consecutive same-4xx → stop, never persist a poisoned run). A draft is a HYPOTHESIS,
never a fact, never a citation, never a decision — `suggested` is advisory only.

The triage rubric (v2, 2026-07-15) makes `park` the default for proxy / already-moved / cyclical
clusters and reserves `keep-for-checks` for the flat-or-lagging + nameable-corporate-driver middle;
runtime FEW-SHOT precedent (the fund's own recent decisions, self-excluded) primes the fund's house
style. `PROMPT_VERSION` gates idempotency — a bump regenerates, same version reuses.
"""
from __future__ import annotations

from typing import Any

from vinci.graph.llm import LlmClient, LlmError
from vinci.themes.exposure import _client_error_status  # 4xx → systemic (abort); else None

_MATCH_MIN = 0.5  # member overlap (of the smaller set) that counts a cluster as already reviewed
_ABORT_AFTER = 3  # consecutive same-4xx (quota/auth) failures that abort before burning the budget
_SUGGESTIONS = ("keep-for-checks", "park", "reject")
_PRECEDENT_K = 10  # most-recent decision+reason pairs injected as few-shot (the fund's case law)

# Bump to regenerate committed drafts under a changed rubric; same version reuses (no LLM spend).
PROMPT_VERSION = "2"

_DRAFT_SYSTEM = (
    "You draft a working NAME and HYPOTHESIS for a cluster of co-moving small-cap US "
    "stocks, plus an ADVISORY triage disposition, to help a human analyst decide faster. "
    "You ASSEMBLE and TRIAGE; you do NOT state facts, cite sources, or decide.\n"
    "HYPOTHESIS: a GUESS about the shared driver that might explain the co-movement — "
    "framed as a hypothesis, never established fact; NO citations, NO claims about "
    "specific filings, numbers, or events.\n"
    "TRIAGE — pick the tightest fit; most co-moving small-cap clusters are proxies or "
    "already-moved and should PARK:\n"
    "- park: commodity / rate / factor PROXIES (the group tracks a price or macro "
    "factor, not company execution); groups that have ALREADY MOVED on the driver "
    "(reason over the rel-strength / momentum stats given); recognized, priced cycles.\n"
    "- reject: driverless grab-bags (no shared corporate driver — coincidence); "
    "collapsed gimmicks.\n"
    "- keep-for-checks: ONLY when price is FLAT-OR-LAGGING the market AND there is a "
    "plausible, nameable CORPORATE driver (company execution, not a factor proxy). This "
    "is the AMBIGUOUS MIDDLE — it is NEVER the default.\n"
    "When a statistic drives the call, CITE it in the reason (e.g. '+206% vs market — "
    "too late', 'flat vs market, real driver'). "
    "`suggested` is ADVISORY ONLY — the analyst records the real decision, never you. "
    "Be terse."
)

DRAFT_TOOL: dict[str, Any] = {
    "name": "draft_theme",
    "description": (
        "Draft a working name + hypothesis for this co-moving cluster and an ADVISORY triage "
        "disposition (not a decision). The hypothesis is a guess about the shared driver, never a "
        "stated fact and never cited."
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
            "reason": {
                "type": "string",
                "description": (
                    "<= 15 words; cite the stat when it drives the call (e.g. '+206% vs market — "
                    "too late')"
                ),
            },
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


def draft_targets(clusters: list[dict[str, Any]], reviews: list[dict[str, Any]], scan_date: str,
                  *, include_reviewed: bool) -> list[dict[str, Any]]:
    """The clusters to draft. Normal: the UNREVIEWED set (the inbox). include_reviewed: the clusters
    that already carry a review FOR THIS scan (key ``<scan_date>:<cid>``) — the freshly-decided set,
    for a one-shot FACE-VALIDITY re-check of the rubric against the human's own calls. Never no-ops
    silently: the caller checks the returned list is non-empty for the reviewed path."""
    if not include_reviewed:
        return unreviewed_clusters(clusters, reviews)
    keys = {r["key"] for r in reviews}
    return [c for c in clusters if f"{scan_date}:{c['cluster_id']}" in keys]


def _drafts_current(prev: dict[str, Any], source: str, version: str) -> bool:
    """True iff committed drafts are for THIS snapshot AND this prompt version → reuse, no spend.
    A legacy pointer with no ``prompt_version`` (or a bumped one) is NOT current → regenerate."""
    return prev.get("source") == source and prev.get("prompt_version") == version


def _stat(cluster: dict[str, Any], *keys: str) -> Any:
    node: Any = cluster
    for k in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(k)
    return node


def _pct(v: Any) -> str:
    """A rel-strength / momentum fraction as a signed percent (2.056 → '+206%'); '?' if absent."""
    return f"{v * 100:+.0f}%" if isinstance(v, (int, float)) else "?"


def _recent_precedent(reviews: list[dict[str, Any]], cluster: dict[str, Any],
                      *, k: int = _PRECEDENT_K) -> list[tuple[str, str]]:
    """The ``k`` most-recent (decision, reason) pairs from reviews, EXCLUDING any review that
    overlaps ``cluster`` by members (no self-leak — a cluster must never see its own recorded
    decision). Recency by ``reviewed`` date; stable within a date."""
    cs = {m.get("ticker") for m in cluster.get("members", [])}
    pool = [r for r in reviews if _overlap(cs, set(r.get("members", []))) < _MATCH_MIN]
    pool.sort(key=lambda r: r.get("reviewed", ""), reverse=True)  # stable → file order per date
    return [(str(r.get("decision", "")), str(r.get("reason", ""))) for r in pool[:k]
            if r.get("decision")]


def _format_precedent(pairs: list[tuple[str, str]]) -> str:
    """Compact few-shot block for the prompt; empty string when there is no precedent."""
    if not pairs:
        return ""
    lines = "\n".join(f"- {d} — {r}" for d, r in pairs)
    return ("Recent analyst precedent (the fund's own case law — how it triaged OTHER clusters; "
            "your call is INDEPENDENT, not a vote count):\n" + lines + "\n\n")


def _cluster_prompt(cluster: dict[str, Any], precedent: str = "") -> str:
    members = cluster.get("members", [])
    rows = "\n".join(
        f"  {m.get('ticker', '?')}  {m.get('name', '')}  "
        f"(SIC {m.get('sic', '?')}, {m.get('sector', '?')})"
        for m in members)
    rel = _stat(cluster, "strength_signals", "rel_strength_vs_market", "h12mo", "value")
    mom = _stat(cluster, "strength_signals", "momentum", "h12mo", "value")
    stats = (
        f"rel-strength vs market 12mo {_pct(rel)}, momentum 12mo {_pct(mom)}, "
        f"coherence {_stat(cluster, 'admissibility', 'coherence_value')}, "
        f"breadth-expanding {_stat(cluster, 'strength_signals', 'breadth_expanding', 'value')}, "
        f"crowding {_stat(cluster, 'strength_signals', 'crowding_overextension', 'value')}")
    return (
        f"{precedent}A cluster of {len(members)} co-moving US small-cap stocks (co-movement, not a "
        f"stated theme).\n\nMembers (ticker · company · industry):\n{rows}\n\n"
        f"Co-movement stats: {stats}\n\n"
        "Draft a working name + a HYPOTHESIS about the shared driver that might explain the "
        "co-movement, and an advisory triage disposition. Do not assert facts or cite anything.")


def draft_cluster(cluster: dict[str, Any], key: str, llm: LlmClient,
                  reviews: list[dict[str, Any]] | tuple[()] = ()) -> dict[str, Any]:
    """One LLM draft for a cluster → a drafted record, primed with self-excluded few-shot precedent
    from ``reviews``. Raises on any LLM/validation failure (the caller turns that into an
    unassessed-error record — NEVER a fabricated draft)."""
    precedent = _format_precedent(_recent_precedent(list(reviews), cluster))
    user = _cluster_prompt(cluster, precedent)
    raw = llm.extract(system=_DRAFT_SYSTEM, user=user, tool=DRAFT_TOOL)
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
                     llm: LlmClient, *, progress: Any = None,
                     include_reviewed: bool = False) -> list[dict[str, Any]]:
    """Draft the target clusters (one LLM call each), keyed "<scan_date>:<cluster_id>", each primed
    with self-excluded few-shot precedent from ``reviews``. Normal: the UNREVIEWED set;
    include_reviewed: the clusters reviewed FOR THIS scan (the face-validity re-check set). Any call
    error → an unassessed-error record with the reason (never a fabricated draft). Aborts fast on
    _ABORT_AFTER consecutive same-4xx (quota/auth) — raises DraftAbortedError, persists none."""
    todo = draft_targets(clusters, reviews, scan_date, include_reviewed=include_reviewed)
    out: list[dict[str, Any]] = []
    streak, last_status = 0, None
    for i, c in enumerate(todo, 1):
        key = f"{scan_date}:{c['cluster_id']}"
        try:
            out.append(draft_cluster(c, key, llm, reviews))
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
