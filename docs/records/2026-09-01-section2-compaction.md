---
id:
status: shipped
date: 2026-09-01
prs: [TBD]
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

**VERIFIED.** 3 mutations: a 26-line §2 entry with no pointer CAUGHT; the same entry with a pointer
ALLOWED; the file creeping to 99 lines under the cap CAUGHT.
