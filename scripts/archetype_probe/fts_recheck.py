"""Search (c) of stage2.py, re-run for the names searches (a)/(b) did not find (the first run called
FtsResult.hits as a method; it is a property). Updates out/stage2.json in place."""

from __future__ import annotations

import json
from collections import Counter

from probe_common import OUT, edgar

path = OUT / "stage2.json"
R = json.loads(path.read_text())
ed = edgar()
for r in R:
    if "filers" in r:
        continue
    toks = r["tokens"]
    hits_by: Counter[str] = Counter()
    total, matched_total, errs = 0, 0, []
    for tok in toks[:2]:
        phrase = tok.title()
        try:
            res = ed.fulltext_search(
                phrase,
                forms="20-F,40-F,6-K,10-K",
                startdt="2024-01-01",
                enddt="2026-11-19",
                max_pages=1,
            )
            hs = res.hits
            total += len(hs)
            matched_total = max(matched_total, getattr(res, "read", len(hs)))
            for h in hs:
                dn = " ".join(h.display_names).upper()
                if any(t in dn for t in toks):
                    hits_by[dn[:90]] += 1
        except Exception as exc:  # noqa: BLE001 — unread, never absent
            errs.append(f"{phrase}: {type(exc).__name__}: {exc}"[:200])
    r["fts_hits_read"] = total
    r["fts_self_filer_hits"] = dict(hits_by)
    r["fts_errors"] = errs
    print(r["name"], total, dict(hits_by), errs, flush=True)
path.write_text(json.dumps(R, indent=1, default=str))
