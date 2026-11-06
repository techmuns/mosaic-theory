"""Score the frozen gold set with the deterministic metrics — the numbers the design record reports
and the tests pin. $0; transcripts are read only for M-ABSENT's transcript-only/nowhere split and
never change whether a metric fires."""
from __future__ import annotations

import json
from pathlib import Path

from vinci.dossier.schemas import MechanicalLayer
from vinci.evals import gold as gd
from vinci.evals import metrics as mt

ROOT = Path(__file__).resolve().parents[2]


def gold_context(ticker: str, *, pages: Path = ROOT / "data/dossiers",
                 transcript: str | None = None) -> mt.PageContext:
    """A gold page's facts AS THE CODERS READ THEM: the committed mechanical layer, whole."""
    page = json.loads((pages / ticker / "dossier.json").read_text(encoding="utf-8"))
    return mt.PageContext(page=page, mech=MechanicalLayer.model_validate(page["mechanical"]),
                         transcript=transcript)


def fired_on_gold(gold: list[gd.GoldClaim], *, pages: Path = ROOT / "data/dossiers",
                  tickers: set[str] | None = None) -> dict[str, set[str]]:
    """metric → the gold claim ids it fires on (pages limited to ``tickers`` when given)."""
    out: dict[str, set[str]] = {m: set() for m in mt.UNIT_METRICS}
    ctxs: dict[str, mt.PageContext] = {}
    for g in gold:
        if tickers is not None and g.page not in tickers:
            continue
        ctx = ctxs.get(g.page) or ctxs.setdefault(g.page, gold_context(g.page, pages=pages))
        for name, fn in mt.UNIT_METRICS.items():
            if fn(g.unit(), ctx):
                out[name].add(g.id)
    return out


def gold_report() -> str:
    gold = gd.load_gold()
    fired = fired_on_gold(gold)
    lines = [json.dumps(gd.summary(gold))]
    for half in ("dev", "test", "all"):
        for m, cls in mt.GOLD_CLASS.items():
            lines.append(gd.precision_recall(m, cls, gold, fired[m], half).line())
    return "\n".join(lines)
