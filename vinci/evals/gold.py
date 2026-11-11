"""The frozen gold set — 644 synthesis claims, coded twice blind and adjudicated — and the precision
and recall of each deterministic metric against it.

THE FINAL LABEL (design record §1): the adjudicated record where one exists, else the agreed
coding. The two coders agree on the verdict AND the materiality of every claim that was not
adjudicated; ``load_gold`` raises if a file says otherwise, rather than picking a coder.

THE SPLIT is the diagnosis's own, page-disjoint: DEV = the 14 pages AMZN … NFLX (330 claims), TEST
= the 14 pages NKE … WLK (314). Metric code is revised against DEV only; TEST is the headline.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vinci.evals.units import Unit, gold_prose

GOLD_DIR = Path(__file__).resolve().parents[2] / "tests/fixtures/synthesis_gold"
CLASSES = ("SIGN", "PATH", "PERIOD", "UNIT", "BASIS", "STALE", "CONFLICT", "ABSENT", "SELECTIVE",
           "OVERREACH", "LABEL")


@dataclass(frozen=True)
class GoldClaim:
    id: str
    page: str
    section: str
    text: str        # the prose (a decisive question's question and evidence claims)
    verdict: str
    material: bool
    favours: str | None
    fact: str | None
    source: str      # "agreed" | "adjudicated"
    half: str        # "dev" | "test"

    @property
    def error(self) -> bool:
        return self.verdict != "OK"

    def unit(self) -> Unit:
        return Unit(self.id, self.section, self.text)


def _jsonl(p: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_gold(folder: Path, manifest: dict[str, Any]) -> None:
    """THE FROZEN GOLD IS THE GOLD ITS MANIFEST HASHED (fix request 2, RG-D11). Every file a
    metric reads must equal the sha256 the manifest records, or nothing is loaded: a label edit
    that keeps the pinned counts moved M-LABEL's and M-SIGN's precision and recall, and nothing
    noticed. ``claims.jsonl``, ``adjudicated.jsonl`` and ``TAXONOMY.md`` are recorded as they are;
    each coder file is its two halves concatenated (``MANIFEST.files``), split at the DEV half's
    claim count."""
    src = manifest["source_sha256"]
    for name in ("claims.jsonl", "adjudicated.jsonl", "TAXONOMY.md"):
        if (got := _sha256((folder / name).read_bytes())) != src[name]:
            raise ValueError(f"{folder / name}: sha256 {got[:12]} is not the manifest's "
                             f"{src[name][:12]} — the frozen gold was edited; nothing is loaded")
    n = int(manifest["split"]["dev"]["claims"])
    for coder, prefix in (("coder_a.jsonl", "A"), ("coder_b.jsonl", "B")):
        lines = (folder / coder).read_bytes().splitlines(keepends=True)
        for half, part in ((f"{prefix}_half1.jsonl", lines[:n]), (f"{prefix}_half2.jsonl",
                                                                   lines[n:])):
            if (got := _sha256(b"".join(part))) != src[half]:
                raise ValueError(f"{folder / coder}: its part recorded as {half} has sha256 "
                                 f"{got[:12]}, not the manifest's {src[half][:12]} — the frozen "
                                 "gold was edited; nothing is loaded")


def load_gold(folder: Path = GOLD_DIR) -> list[GoldClaim]:
    manifest = json.loads((folder / "MANIFEST.json").read_text(encoding="utf-8"))
    verify_gold(folder, manifest)
    dev = set(manifest["split"]["dev"]["pages"])
    claims = _jsonl(folder / "claims.jsonl")
    a = {r["id"]: r for r in _jsonl(folder / "coder_a.jsonl")}
    b = {r["id"]: r for r in _jsonl(folder / "coder_b.jsonl")}
    adj = {r["id"]: r for r in _jsonl(folder / "adjudicated.jsonl")}
    out: list[GoldClaim] = []
    for c in claims:
        i = c["id"]
        if i in adj:
            rec, source = adj[i], "adjudicated"
        else:
            ra, rb = a[i], b[i]
            mat_differs = bool(ra.get("material")) != bool(rb.get("material"))
            if ra["verdict"] != rb["verdict"] or (ra["verdict"] != "OK" and mat_differs):
                raise ValueError(f"{i}: the coders disagree and no adjudication exists")
            rec, source = ra, "agreed"
        _, section, _ = i.split(":")
        out.append(GoldClaim(
            id=i, page=c["page"], section=section, text=gold_prose(c["text"]),
            verdict=rec["verdict"],
            material=bool(rec.get("material")) and rec["verdict"] != "OK",
            favours=rec.get("favours"), fact=rec.get("fact"), source=source,
            half="dev" if c["page"] in dev else "test"))
    return out


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - h) / d), min(1.0, (c + h) / d)


@dataclass(frozen=True)
class PR:
    """One metric on one half of the gold: flagged claims against the gold class."""

    metric: str
    gold_class: str
    half: str
    claims: int
    tp: int
    fp: int
    fn: int
    material_tp: int
    material_pos: int
    any_error_fired: int

    @property
    def fired(self) -> int:
        return self.tp + self.fp

    @property
    def precision(self) -> float | None:
        return self.tp / self.fired if self.fired else None

    @property
    def recall(self) -> float | None:
        pos = self.tp + self.fn
        return self.tp / pos if pos else None

    def line(self) -> str:
        def pct(x: float | None) -> str:
            return "—" if x is None else f"{x:.0%}"

        def ci(k: int, n: int) -> str:
            w = wilson(k, n)
            return "" if w is None else f" [{w[0]:.0%}–{w[1]:.0%}]"

        pos = self.tp + self.fn
        return (f"{self.metric:8} vs {self.gold_class:6} {self.half:4} n={self.claims}: fired "
                f"{self.fired}, TP {self.tp} FP {self.fp} FN {self.fn} | precision "
                f"{pct(self.precision)}{ci(self.tp, self.fired)} recall {pct(self.recall)}"
                f"{ci(self.tp, pos)} | material recall {self.material_tp}/{self.material_pos} | "
                f"any-error precision {self.any_error_fired}/{self.fired}")


def precision_recall(metric: str, gold_class: str, gold: Sequence[GoldClaim],
                     fired: Iterable[str], half: str) -> PR:
    hit = set(fired)
    pool = [g for g in gold if half == "all" or g.half == half]
    pos = {g.id for g in pool if g.verdict == gold_class}
    mat = {g.id for g in pool if g.verdict == gold_class and g.material}
    ids = {g.id for g in pool}
    f = hit & ids
    return PR(metric=metric, gold_class=gold_class, half=half, claims=len(pool), tp=len(f & pos),
              fp=len(f - pos), fn=len(pos - f), material_tp=len(f & mat), material_pos=len(mat),
              any_error_fired=sum(1 for g in pool if g.id in f and g.error))


def summary(gold: Sequence[GoldClaim]) -> dict[str, Any]:
    err = [g for g in gold if g.error]
    return {"claims": len(gold), "errors": len(err), "material": sum(g.material for g in err),
            "material_by_class": dict(Counter(g.verdict for g in err if g.material).most_common()),
            "by_class": dict(Counter(g.verdict for g in err).most_common()),
            "adjudicated": sum(g.source == "adjudicated" for g in gold)}
