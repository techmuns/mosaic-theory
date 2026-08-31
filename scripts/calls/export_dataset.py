"""Export the labelled corpus as JSONL for external statistical analysis.

ONE ROW PER (tweet x ticker). No filtering of any kind — every bias, every class, including the
rows an analysis would exclude, because the excluded rows are what selection is measured against.

THIS SCHEMA IS NOT THE CORPUS SCHEMA, and every place they differ is a decision recorded here and
in VALIDATION.md rather than smoothed over:

  bias              the corpus carries FIVE values (bullish, bearish, mixed, neutral, none), not
                    three. `mixed` and `none` are 4,877 of 8,185 rows — 60% — so they are emitted
                    as themselves. A consumer expecting three values must widen its enum.
  is_forward_call   DERIVED, never labelled. See FORWARD_CALL below.
  target            a NUMBER whose UNIT depends on `target_type`: a price for point/range, a
                    PERCENT for pct. Resolving a pct target to a price needs the entry price, which
                    is forward-looking data, and putting it in a label field would contaminate the
                    export. `target_type` disambiguates the unit.
  post_class        `signal_candidate` is renamed `signal` (a pure rename). `commentary` is in the
                    requested enum but does not exist in this corpus and will never appear.
  label_source      the corpus has THREE tiers — machine, llm, hand — and after the 2026-08 adoption
                    ZERO rows remain `machine`. `llm` is 7,473 rows. Collapsing it into "machine"
                    would hide the distinction that matters most: the llm reading measures 81% on
                    bias against hand labels where the original machine labeller measured ~55%.
  label_confidence  DERIVED from label_source, never labelled per row.
  stated_confidence the source field is FREE TEXT and mostly not a win rate at all — of 269
                    non-null values the observed shapes include "90% of traders fail" and "75% of
                    premium". Only a bare percentage is extracted; everything else becomes null.

    python -m scripts.calls.export_dataset [handle] [outdir]
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys
from typing import Any

from vinci.calls.audit import load_audit
from vinci.calls.targets import parse_target

#: A directional read IS a claim about future price — that is what the label means, and
#: `is_retrospective` is a SEPARATE flag precisely so a post can be both. `mixed` counts: a
#: two-sided forward view is still forward. Everything else (neutral, none) makes no price claim.
FORWARD_CALL = {"bullish", "bearish", "mixed"}

#: hand = a person read the post. llm = the adopted second reading, measured at 81% on bias against
#: 283 unbiased hand rows. machine = the original labeller, measured at ~55%; none survive today.
CONFIDENCE = {"hand": "high", "llm": "medium", "machine": "low"}

#: One row carries `target_type: "price"`, which is not a member of TARGET_TYPES — an LLM wrote it
#: and no guard rejected it. Coerced to `point` (its target is "500+") and reported by the run.
TYPE_FIXUP = {"price": "point"}

_BARE_PCT = re.compile(r"^\s*(\d{1,3})\s*%\s*$")


def stated_confidence(raw: object) -> int | None:
    """An integer percent ONLY from a bare '15%'. Free text like '90% of traders fail' is a claim
    about the world, not his confidence in this call, and is dropped rather than mined."""
    if not isinstance(raw, str):
        return None
    m = _BARE_PCT.match(raw)
    if not m:
        return None
    v = int(m.group(1))
    return v if 0 <= v <= 100 else None


def target_number(target: object, target_type: str | None, bias: str | None) -> float | None:
    """The stated target as a number, in the unit `target_type` implies. Never inferred: a post
    with no target yields null, and a qualitative one ('discount zone') yields null."""
    if target_type == "pct":
        m = re.search(r"[-+]?\d+(?:\.\d+)?", str(target or ""))
        return float(m.group(0)) if m else None
    p = parse_target(target, target_type, entry=None, bias=bias)
    return p.price


def main() -> int:
    handle = sys.argv[1] if len(sys.argv) > 1 else "pdicarlotrader"
    outdir = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else f"exports/{handle}")
    outdir.mkdir(parents=True, exist_ok=True)
    d = pathlib.Path("data/calls") / handle
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    posts: dict[str, Any] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p
    audit = load_audit(handle)

    rows: list[dict[str, Any]] = []
    coerced = 0
    no_post = 0
    for key, lab in labels.items():
        tid, _, ticker = key.partition("|")
        post = posts.get(tid)
        if post is None:
            no_post += 1
            continue
        ttype = lab.get("target_type")
        if ttype in TYPE_FIXUP:
            ttype = TYPE_FIXUP[ttype]
            coerced += 1
        cls = lab.get("post_class")
        rd = audit.get(tid)
        src = lab.get("src") or "llm"
        rows.append({
            "tweet_id": tid,
            "date": post.get("d"),
            "ticker": ticker.upper().lstrip("$"),
            "bias": lab.get("bias"),
            "action": lab.get("action") or "none",
            "is_retrospective": bool(lab.get("is_retrospective")),
            "is_forward_call": lab.get("bias") in FORWARD_CALL,
            "target": target_number(lab.get("target"), ttype, lab.get("bias")),
            "target_type": ttype or "none",
            "horizon_lo_days": lab.get("hlo"),
            "horizon_hi_days": lab.get("hhi"),
            "specificity": lab.get("spec"),
            "post_class": "signal" if cls == "signal_candidate" else cls,
            "stated_confidence": stated_confidence(rd.probability if rd else None),
            "has_video": bool(post.get("v")),
            "thesis_cluster_id": tid,
            "label_source": src,
            "label_confidence": CONFIDENCE.get(src, "low"),
        })
    rows.sort(key=lambda r: (str(r["date"]), r["tweet_id"], r["ticker"]))

    main_p = outdir / f"{handle}_labels.jsonl"
    main_p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                      encoding="utf-8")

    # THE AUDIT SAMPLE: 60 rows, stratified across quarters so no period is over-represented, WITH
    # the tweet text, so a reader can check a label against the words that produced it.
    rng = random.Random(20260828)
    by_q: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        dt = str(r["date"])
        q = f"{dt[:4]}Q{(int(dt[5:7]) - 1) // 3 + 1}"
        by_q.setdefault(q, []).append(r)
    quarters = sorted(by_q)
    per = 60 // len(quarters)
    sample: list[dict[str, Any]] = []
    for q in quarters:
        sample += rng.sample(by_q[q], min(per, len(by_q[q])))
    pool = [r for r in rows if r not in sample]
    sample += rng.sample(pool, 60 - len(sample))
    sample.sort(key=lambda r: (str(r["date"]), r["tweet_id"], r["ticker"]))
    samp_p = outdir / f"{handle}_audit_sample.jsonl"
    samp_p.write_text("".join(
        json.dumps({**r, "text": posts[r["tweet_id"]].get("txt"),
                    "url": posts[r["tweet_id"]].get("url")}, ensure_ascii=False) + "\n"
        for r in sample), encoding="utf-8")

    print(f"{len(rows):,} rows -> {main_p}")
    print(f"   dropped {no_post} label rows whose post is missing from the corpus")
    print(f"   coerced {coerced} target_type 'price' -> 'point'")
    print(f"{len(sample)} rows -> {samp_p}  ({len(quarters)} quarters, {per}/quarter + remainder)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
