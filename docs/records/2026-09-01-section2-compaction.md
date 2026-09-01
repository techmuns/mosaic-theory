---
id:
status: shipped
date: 2026-09-01
prs: [555]
supersedes:
superseded-by:
---

# §2's convention was documented and unenforced, so the snapshot grew back to five lines of headroom

**THE DIAGNOSIS, NOT THE SYMPTOM.** STATE.md sat at **2,095 against an enforced 2,100 cap** — five
lines. The history shows it hitting 2,100 exactly on 2026-08-30 and being trimmed the same day: the
file had been running flush against its limit, each build paying a just-in-time tax.

**WHERE THE GROWTH WAS.** From P3 (#506, 1,944 lines) to 2026-09-01 (2,095): **+151 lines in six
days, of which §2 was +128.** Not diffuse drift — one section.

**AND WHAT KIND OF GROWTH.** 14 of §2's 91 bullets ran ≥21 lines and held **459 lines: 45% of the
section in 15% of its entries**, the largest 70. Three of those already carried a `*(detail: …)*`
pointer, so their detail was **duplicated**, not relocated.

**ROOT CAUSE A — the convention had no enforcement.** §2 documents its own shape: a summary in the
snapshot, the narrative in a record behind a pointer. Nothing checked it. The only guard was the
whole-file cap, and a total cannot tell a 3-line capability summary from a 70-line build narrative.
It also fires hundreds of lines downstream, so it lands on whichever build happens to be last
rather than the one that added the narrative.

**ROOT CAUSE B — the cap's slack was sized against a shape the file has never had.** Its comment
justifies 155 lines by "a 2-3 line summary in §2". Measured: only **17 of 91 entries** were ever
that short — median 6, mean 11, p90 23. Sizing a guard against an ideal rather than the corpus is
what let the slack last six days. (This is also why the 2,500 ceiling proposed in #550 was closed:
a second, looser number would not have touched either cause.)

**THE FIXES.**

1. **Compaction** (`scripts/compact_state_section2.py`): 11 entries moved to records, 3 duplicates
   collapsed onto pointers they already had. §2 **1,023 → 608**; STATE.md **2,095 → 1,680**.
   Headroom 5 → **420**. All 91 bullets survive; the largest entry is now 20 lines.
2. **A per-entry pin** — a §2 entry ≥21 lines must carry a record pointer. 21 comes from the live
   distribution, where the narratives actually begin, not from an ideal.
3. **A headroom pin** — the file may not sit within 100 lines of the cap, so the limit is not
   discovered at the moment of breach and raising it stays a deliberate decision.

**LOSSLESS, AND PROVED THAT WAY.** The script refuses to write unless the split reconstructs §2
byte-for-byte (P3's method). Verified after the fact too: all 11 records contain their block
verbatim against the pre-compaction file, and all **68 pointers resolve**.

**WHY THE CAP IS A SHARED BUDGET, AND WHAT THAT MEANS.** CI checks out the MERGE RESULT for a
`pull_request` event (`actions/checkout@v4`, no explicit `ref:`), so the cap is measured on
PR-merged-into-main, not on the branch. Every open PR therefore draws from one 2,100-line budget:
each is green alone, and whichever merges last pays. The failing PR is not the one that consumed
the budget, and its only remedy is compacting somebody else's entries — which is precisely why the
last person to hit it left it. Headroom is what makes that collision rare; it is not a property the
guard can enforce away.

**A PER-PR DELTA CAP WAS CONSIDERED AND REJECTED — it would be dead code.** The obvious fix for
misattribution is to bound each PR's own contribution instead of the shared total. Measured over
the 33 STATE.md-touching commits since P3: median **2** lines, mean 4.7, p90 16, **max 25**. A cap
at 25, 30, 40 or 50 fires on **none of them**. Sizing it on the last 200 commits instead would
suggest 40 (42% would fire) — but that window is mostly PRE-P3, a regime the migration ended. Sizing
a guard against a shape the file no longer has is root cause B repeated, so it is recorded here
rather than built.

**WHICH LEAVES THE ACTUAL SHAPE OF THE PROBLEM: monotonic inflow, no outflow.** Post-P3 per-PR
behaviour is disciplined — nobody is dumping narratives. The +151 lines came from 33 commits
averaging 4.7 lines each, every one of them reasonable. §2 gains a bullet per capability shipped
(73 → 91 since P3) and **nothing ever removes one**. A fixed cap against a monotonic list is hit
again by arithmetic; the only question is when. So compaction is not a one-off repair, it is the
outflow, and the headroom pin is what schedules it before it becomes an emergency.

**VERIFIED.** 3 mutations: a 26-line §2 entry with no pointer CAUGHT; the same entry with a pointer
ALLOWED; the file creeping to 99 lines under the cap CAUGHT.
