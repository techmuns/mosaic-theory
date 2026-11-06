"""Score the frozen gold set with the deterministic metrics — the numbers the design record reports
and the tests pin. $0; transcripts are read only for M-ABSENT's transcript-only/nowhere split and
never change whether a metric fires."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from vinci.dossier.schemas import MechanicalLayer
from vinci.evals import gold as gd
from vinci.evals import metrics as mt
from vinci.evals.replay import git_blob, git_show

ROOT = Path(__file__).resolve().parents[2]
#: The commit whose pages the gold was graded against (= main 3e97ee7d plus #918's NFLX and MCK);
#: every gold score reads its pages from HERE, never from the living tree, which moves as pages
#: are rebuilt — a one-byte change used to skip 8 of 13 per-claim pins (review round 2, #924).
GOLD_REF = "bcda7ce36e02369d2d67aaba6ff2004c3777d40e"


def _frozen_page(ticker: str, ref: str) -> dict[str, Any]:
    page: dict[str, Any] = json.loads(git_show(ref, f"data/dossiers/{ticker}/dossier.json"))
    return page


def gold_context(ticker: str, *, ref: str = GOLD_REF,
                 transcript: str | None = None) -> mt.PageContext:
    """A gold page's facts AS THE CODERS READ THEM: the mechanical layer of the page at the
    gold's freeze commit, whole."""
    page = _frozen_page(ticker, ref)
    return mt.PageContext(page=page, mech=MechanicalLayer.model_validate(page["mechanical"]),
                          transcript=transcript)


def living_drift(tickers: list[str], *, pages: Path = ROOT / "data/dossiers",
                 ref: str = GOLD_REF) -> list[str]:
    """The tickers whose LIVING page differs from the gold's frozen one — reported with every gold
    score, so a reader knows the committed pages have since moved (the score does not)."""
    out = []
    for t in tickers:
        living = pages / t / "dossier.json"
        blob = subprocess.run(["git", "hash-object", str(living)], capture_output=True,
                              text=True, check=True).stdout.strip() if living.exists() else ""
        if blob != git_blob(ref, f"data/dossiers/{t}/dossier.json"):
            out.append(t)
    return out


def fired_on_gold(gold: list[gd.GoldClaim], *, ref: str = GOLD_REF,
                  tickers: set[str] | None = None) -> dict[str, set[str]]:
    """metric → the gold claim ids it fires on, the pages read at ``ref`` (limited to
    ``tickers`` when given)."""
    out: dict[str, set[str]] = {m: set() for m in mt.UNIT_METRICS}
    ctxs: dict[str, mt.PageContext] = {}
    for g in gold:
        if tickers is not None and g.page not in tickers:
            continue
        ctx = ctxs.get(g.page) or ctxs.setdefault(g.page, gold_context(g.page, ref=ref))
        for name, fn in mt.UNIT_METRICS.items():
            if fn(g.unit(), ctx):
                out[name].add(g.id)
    return out


def gold_report() -> str:
    gold = gd.load_gold()
    fired = fired_on_gold(gold)
    lines = [json.dumps(gd.summary(gold)), f"pages read at the gold freeze {GOLD_REF[:12]}"]
    if moved := living_drift(sorted({g.page for g in gold})):
        lines.append(f"NOTE: the living pages of {moved} have moved since; the gold scores the "
                     "frozen ones")
    for half in ("dev", "test", "all"):
        for m, cls in mt.GOLD_CLASS.items():
            lines.append(gd.precision_recall(m, cls, gold, fired[m], half).line())
    return "\n".join(lines)
