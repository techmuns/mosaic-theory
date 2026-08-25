"""Score an account's labelled calls and write the results beside its corpus.

READS HAND LABELS FIRST. ``labels.json`` holds both, keyed ``<tweet_id>|<TICKER>``, and every row
carries ``src``. A hand label always wins over the machine's guess for the same key — the whole
point of the tape is to grow the hand set, so the moment a row is labelled by a human the score
must follow it.

NO AGGREGATE IS PUBLISHED HERE. The counts printed by ``vinci calls score`` are an operator-facing
run summary, not a product surface: at 83 hand labels against 8,102 machine guesses any headline
hit-rate would be a statement about the machine's 55%-accurate bias calls, not about the author.
The dashboard's Scoreboard stays a CONDITIONAL stage until the hand set passes ~500.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from vinci.calls.accounts import account_dir
from vinci.calls.bars import BENCHMARK, load_bars
from vinci.calls.score import CallResult, is_scoreable, score_call


def _labels(handle: str) -> dict[str, dict[str, Any]]:
    p = account_dir(handle) / "labels.json"
    return json.loads(p.read_text())  # type: ignore[no-any-return]


def _posted_dates(handle: str) -> dict[str, date]:
    """tweet_id -> post date, read from the monthly post files (labels carry no date)."""
    out: dict[str, date] = {}
    for f in sorted((account_dir(handle) / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            out[str(p["id"])] = date.fromisoformat(str(p["d"])[:10])
    return out


def score_account(handle: str, *, only_hand: bool = False) -> list[CallResult]:
    """Score every directional label for one account. Unscoreable rows are omitted, not guessed."""
    labels, dates = _labels(handle), _posted_dates(handle)
    bench = load_bars(handle, BENCHMARK)
    cache: dict[str, list[Any]] = {}
    results: list[CallResult] = []
    for key, lab in labels.items():
        if only_hand and lab.get("src") != "hand":
            continue
        if not is_scoreable(lab.get("bias")):
            continue
        tweet_id, _, ticker = key.partition("|")
        posted = dates.get(tweet_id)
        if posted is None:
            continue
        if ticker not in cache:
            cache[ticker] = load_bars(handle, ticker)
        results.append(score_call(
            tweet_id=tweet_id, ticker=ticker, posted=posted, bias=str(lab["bias"]),
            target=lab.get("target"), target_type=lab.get("target_type"),
            horizon_lo=lab.get("hlo"), horizon_hi=lab.get("hhi"),
            bars=cache[ticker], bench=bench))
    results.sort(key=lambda r: (r.posted, r.ticker))
    return results


def write_results(handle: str, results: list[CallResult], *, hand_only: bool = False) -> Path:
    """Write the scored rows. A HAND-ONLY run writes its OWN file: it is a 76-row subset of the
    same corpus, and letting it share `results.jsonl` meant one convenience flag silently replaced
    the full 3,889-row artifact the frontend reads."""
    p = account_dir(handle) / ("results_hand.jsonl" if hand_only else "results.jsonl")
    p.write_text("".join(r.model_dump_json() + "\n" for r in results))
    return p
