"""An LLM SECOND READING of every tweet's tags — proposed, never applied.

WHAT THIS IS FOR. The corpus carries 8,102 machine tags against 83 human ones, and the machine is
demonstrably wrong in ways already measured here: 624 targets nowhere near the price, 590 levels on
the wrong side of the entry, options-FLOW amounts read as price targets. Hand-checking 8,185 rows
cold is the bottleneck. So this reads each tweet ONCE and proposes its own reading of the tags, and
the sheet shows that beside the current tag with the disagreements coloured — turning "read
everything" into "look at where two readers disagree".

IT PROPOSES; THE HUMAN DECIDES. Nothing here writes a label. The output is an advisory column in a
workbook the operator edits, and the operator's sheet is what becomes the record via
`vinci calls import-labels`. That is the same division this repo applies to its own dossiers, and
it matters more here, not less: the thing being audited IS a labeller.

ONE CALL PER TWEET, NOT PER ROW. The unit of judgement is the post — you cannot read a cashtag's
bias without the sentence around it — but a post naming eight tickers can carry a different bias per
ticker (his Monthly BX Cycle Report does exactly that), so the model returns a reading PER TICKER
and the rows are expanded from it.

RESUMABLE BY CONSTRUCTION. The run is thousands of paid calls; it appends each result as it lands
and skips tweet ids already present, so an interruption costs the in-flight call and nothing else.
"""
from __future__ import annotations

import threading
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from vinci.calls import jsonl_lines
from vinci.calls.accounts import account_dir
from vinci.config import get_config
from vinci.graph.llm import AnthropicLlmClient, LlmClient, LlmError

BIASES = ["bullish", "bearish", "mixed", "neutral", "none"]
ACTIONS = ["enter_long", "enter_short", "add", "trim", "exit", "no_entry", "hold", "none"]
TARGET_TYPES = ["point", "range", "pct", "qualitative", "none"]
SPECS = ["A", "B", "C", "D"]
CLASSES = ["signal_candidate", "flow_spam", "promo", "pnl_report", "noise", "engagement"]

SYSTEM = """You audit tags on a stock commentator's posts. You are a SECOND READER: a machine \
labeller has already tagged these, it is wrong often, and a human will decide. Read only what the \
post says. Never infer a view the author did not state, and never resolve an ambiguity by guessing \
the more interesting reading.

Definitions you must apply exactly:
- bias: the author's stated directional view ON THAT TICKER. `none` when he states no direction \
(commentary, a flow list, a P&L brag). `mixed` when he genuinely argues both sides. `neutral` only \
when he explicitly says he is neutral/flat.
- action: what he says HE is doing with his own position. `none` when he says nothing about it. \
`no_entry` when he explicitly declines to take one.
- target: a price or move HE names. Copy it VERBATIM as written ("172-180", "-10%", "ATH"). If he \
names a level he is WATCHING rather than predicting (a support to bounce from, a resistance to \
reject at, a buy zone), still record it — the sheet distinguishes those downstream.
- horizon: trading days, only if he states a timeframe. "next week" ~5, "a couple of months" ~42, \
"3-6 months" 63-126, "by year end" count it. Leave null if he states none. Never invent one.
- spec: A = direction + target + a stated horizon. B = direction + target, no horizon. C = \
direction, no target. D = no directional call at all.
- post_class: signal_candidate (a real read on a name), flow_spam (an options-flow list, usually \
"$TICKER - $NNM"), promo (selling a course/discord/newsletter), pnl_report (bragging a result), \
engagement (a poll or a like-bait question), noise (everything else).
- probability: any stated likelihood, VERBATIM ("70% of the time", "most cases", "odds are"). Null \
if he states none. Do not convert vague words into numbers.

HIS OWN NOTATION, which you must read consistently. He posts cycle reports as a list of tickers \
each carrying a marker: a check or green circle means his system reads that name as still in its \
bull cycle (bullish); a red/down triangle, red circle or cross means it has broken (bearish). The \
marker IS the call — reading one direction of marker but not the other is the error to avoid.\
 A ticker listed with no marker and no sentence about it is `none`/`D`.

TWO TRAPS THAT HAVE ALREADY PRODUCED BAD TAGS HERE:
- A DURATION IS NOT A TARGET. "3-5 months of cooling off" is a HORIZON, not a price range, while \
"$40-50" is a price. If a number is followed by a time word it is a horizon and the target is null.
- "WORST CASE" FLIPS WITH HIS POSITION. When he is OUT of a name, his "worst case" is that it runs \
without him (an UPSIDE number); when he is IN, it is downside. Read which side he is on first.

`mixed` is for a genuinely two-sided read where he gives the bull case and the bear case as live \
alternatives. A bounce he acknowledges while staying bearish is BEARISH, not mixed.

Return one entry per ticker given. If a ticker is only named in a list with no view attached, its \
bias is `none` and its spec is `D`."""

TOOL: dict[str, Any] = {
    "name": "record_reading",
    "description": "Record your reading of this post's tags.",
    "input_schema": {
        "type": "object",
        "properties": {
            "post_class": {"type": "string", "enum": CLASSES},
            "is_retrospective": {
                "type": "boolean",
                "description": "recalling a call already made, not making one"},
            "is_conditional": {
                "type": "boolean",
                "description": "the view is gated on an if ('if X closes above, then...')"},
            "probability": {"type": ["string", "null"],
                            "description": "verbatim likelihood phrase, or null"},
            "summary": {"type": "string", "description": "one clause: what he actually says"},
            "tickers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "bias": {"type": "string", "enum": BIASES},
                        "action": {"type": "string", "enum": ACTIONS},
                        "target": {"type": ["string", "null"]},
                        "target_type": {"type": "string", "enum": TARGET_TYPES},
                        "horizon_lo_days": {"type": ["integer", "null"]},
                        "horizon_hi_days": {"type": ["integer", "null"]},
                        "spec": {"type": "string", "enum": SPECS},
                        "note": {"type": "string", "description": "one short clause of evidence"},
                    },
                    "required": ["ticker", "bias", "action", "target", "target_type",
                                 "horizon_lo_days", "horizon_hi_days", "spec", "note"],
                },
            },
        },
        "required": ["post_class", "is_retrospective", "is_conditional", "probability",
                     "summary", "tickers"],
    },
}


class TickerReading(BaseModel, frozen=True):
    ticker: str
    bias: str
    action: str
    target: str | None
    target_type: str
    horizon_lo_days: int | None
    horizon_hi_days: int | None
    spec: str
    note: str = ""


class PostReading(BaseModel, frozen=True):
    tweet_id: str
    post_class: str
    is_retrospective: bool
    is_conditional: bool
    probability: str | None
    summary: str = ""
    #: DEFAULTED, so a partial response is still worth something. Observed twice on the real
    #: corpus: the model returned post_class, probability and a summary and simply omitted the
    #: ticker array. Failing the whole row threw away a correct post-level reading to punish a
    #: missing sub-field — the row is instead kept, marked, and the operator reads that one tweet.
    tickers: list[TickerReading] = []
    model: str = ""
    error: str | None = None


def _user(post: dict[str, Any], tickers: Sequence[str]) -> str:
    return (f"Posted {post.get('d')} (UTC {str(post.get('t'))[11:16]}).\n"
            f"Cashtags to report on: {', '.join(tickers)}\n\n"
            f"POST:\n{post.get('txt') or ''}")


def audit_post(client: LlmClient, post: dict[str, Any], tickers: Sequence[str]) -> PostReading:
    """One tweet, one call. A model or validation failure is RECORDED on the row, never raised —
    a single bad post must not abort a run of thousands."""
    tid = str(post["id"])
    try:
        raw = client.extract(system=SYSTEM, user=_user(post, tickers), tool=TOOL)
        r = PostReading(tweet_id=tid, model=client.model, **raw)
        if not r.tickers:
            # keep the post-level reading, but never let an empty list pass as "no view on any
            # ticker" — that is indistinguishable from a correct `none` on every one of them
            return r.model_copy(update={
                "error": "the model returned no ticker array — post-level fields kept, "
                         "per-ticker reading is MISSING and this row needs a human"})
        return r
    except (LlmError, ValidationError, KeyError, TypeError) as exc:
        return PostReading(tweet_id=tid, post_class="noise", is_retrospective=False,
                           is_conditional=False, probability=None, tickers=[],
                           model=client.model, error=f"{type(exc).__name__}: {exc}"[:300])


def audit_path(handle: str) -> Path:
    return account_dir(handle) / "audit.jsonl"


def load_audit(handle: str) -> dict[str, PostReading]:
    p = audit_path(handle)
    if not p.is_file():
        return {}
    out: dict[str, PostReading] = {}
    for line in jsonl_lines(p.read_text()):
        if line.strip():
            r = PostReading.model_validate_json(line)
            out[r.tweet_id] = r
    return out


def run_audit(
    handle: str, *, posts: Iterable[dict[str, Any]], tickers_of: Any,
    client: LlmClient | None = None, workers: int = 8, limit: int | None = None,
    on_done: Any = None,
) -> dict[str, int]:
    """Audit every post not already in ``audit.jsonl``. Appends as results land."""
    cli = client or AnthropicLlmClient(model=get_config().calls_audit_llm_model)
    done = set(load_audit(handle))
    todo = [p for p in posts if str(p["id"]) not in done]
    if limit is not None:
        todo = todo[:limit]
    out_p = audit_path(handle)
    lock = threading.Lock()
    counts = {"attempted": 0, "ok": 0, "failed": 0, "skipped": len(done)}
    if not todo:
        return counts

    with out_p.open("a") as fh, ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(audit_post, cli, p, tickers_of(p)): p for p in todo}
        for fut in as_completed(futs):
            r = fut.result()
            with lock:
                fh.write(r.model_dump_json() + "\n")
                fh.flush()
                counts["attempted"] += 1
                counts["failed" if r.error else "ok"] += 1
                if callable(on_done):
                    on_done(counts, r)
    return counts
