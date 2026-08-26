---
id: 
status: open
date: 2026-08-19
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**VISA `diluted_shares` — MEASURED 2026-08-19; THE PER-FILING FETCH IS DESIGNED AND DEFERRED,
and the reason is recorded so it is not re-derived (the B1a lesson).**
**THE MECHANISM GENERALISES BUT THE POPULATION IS ONE.** The companyfacts summary API STRIPS
DIMENSIONED FACTS, so a per-class filer presents as: standard WA tags ABSENT (V:
`WeightedAverageNumberOfDilutedSharesOutstanding` zero undimensioned facts), EPS-derivation dead
(`EarningsPerShareDiluted` class-dimensioned too), and the only undimensioned cover fact a fossil
(`dei:EntityCommonStockSharesOutstanding` latest **2010-01-27, 469,280,842** vs ~1.836bn actual —
a 4x trap the next reader reaches for first). The right source is the 10-Q's OWN XBRL INSTANCE
(Class-A-as-converted member, ~1.836bn) — same EDGAR provenance chain the anchor cites; CIQ's
subsheet would put the anchor on a different vendor than its basis line claims.
**FLEET MEASUREMENT: V IS THE ONLY NAME MISSING THE INPUT — 13/14 resolve the standard tag.** By
the operator's stated criterion (one dual-class filer = one-name capability; four = infrastructure)
the fetch is NOT built now.
**AND THE FETCH ALONE WOULD NOT MAKE THE ANCHOR HONEST.** R1 selection in `anchor.py` is
MARGIN-SIGN ONLY (non-positive → R2); no book/percentile test exists, so a working input yields a
working R1 anchor for a quality compounder at the 44th percentile of its own multiple history —
a mid-cycle reversion for a name with no mid-cycle to revert to. That is the BOOK-BLIND gap one
layer up (recorded open item), and it GATES this build: if the ruling is that quality names do not
get R1 anchors, V's anchor stays `applicable: false` for the better-stated reason and the fetch has
no consumer. **UNLOCK: the book-blind ruling first; then, if R1 applies, the per-filing fetch with
(a) member selection that REFUSES when none maps cleanly (a silent wrong member is the 4x trap with
more steps) and (b) the dei cover fact refused as a diluted-shares source IN CODE — today nothing
reaches for that tag, so the refusal guards a path that does not exist yet and is recorded here
rather than built speculatively.**
