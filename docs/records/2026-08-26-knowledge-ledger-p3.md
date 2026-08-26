---
id:
status: shipped
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
---

# §2 and §4 compacted: STATE.md 19,241 → 1,892 lines

**WHAT.** §2 "Built and verified" goes **3,686 → 889** lines and §4 "Deferred" **1,013 → 254**, with
3,600 lines of detail moved into **44 records**. Each capability and each deferred item keeps its
one-line summary in the snapshot with a pointer to its detail. Whole file: **19,241 → 1,892**, a
90% reduction across P0–P3.

**WHY IT WAS TRACTABLE WHERE §5 WAS NOT.** §5's entries had no machine-detectable boundaries and
needed 218 hand judgements. §2 and §4 are both **one nested bullet list** — `- **Name** — what it
does — *verified how*` — so the boundary is `^- \*\*` and it is exact. §2's own header already
states the intended form ("Each line: *what it does* — *verified how*"), which is precisely the
summary that stays; the 2,836 indented lines beneath were the elaboration.

**A CORRECTION MID-BUILD.** The first cut at §4 used `^\d+\.\s+\*\*`, matched only 5 of its
numbered "wave" headers, and produced a **979-line single record** — a dump, not a record. Caught by
reading the output rather than trusting the loss-check, which was perfectly happy: losslessness says
nothing about whether the boundaries are *useful*. Re-cut on `- **` → 5 records averaging 150 lines.

**AND A SELF-INFLICTED ONE.** Reverting that bad §4 pass with `git checkout -- STATE.md` also
discarded §2's finished work. Recoverable only because the 39 capability records were already on
disk and the script is deterministic — it reproduced the snapshot edit exactly, and each pointer was
re-asserted against a real file before writing. *This repo already carries a note about `git
checkout --` taking more than intended; it took more than intended again.*

**HOW VERIFIED.** Losslessness checked per section — no token from the removed text is absent from
snapshot + records — and refusing to write otherwise. All **44 pointers resolve** to a real file.
Two new guards, both mutation-tested: a pointed-at record renamed, and 800 lines of narrative
returning to the snapshot.

**A GUARD CAUGHT MY OWN INCONSISTENCY.** The §4 records were first stamped `status: open` — true of
the items, but the archive rule says a record is never the authority on status. §4 keeps the item
and its trigger and remains the authority; the records are `recorded` and say so.

**§7 STAYS, AND THE PLAN WAS WRONG ABOUT IT.** I wrote that §7 "The standing discipline" (495
lines) is *rules, not state*, so it belonged in CLAUDE.md or `docs/engineering.md`. The operator
challenged that, and reading §7 shows it is neither: it is **fund policy** — `DUAL MEASUREMENT —
RATIFIED 2026-07-22`, `HURDLE = 15%, FLAT, HOUSE-WIDE`, `SURVIVAL IS A HARD GATE`, the
print-freshness gate before any BUY, `Monitor cadence: MANUAL, never a scheduler`. Filing an
investment policy under engineering conventions would be a category error, and 495 lines would
nearly triple a CLAUDE.md that is deliberately minimal.

**"The hurdle is 15%, ratified 2026-07-21" IS current truth about the fund**, which is what a
snapshot holds. Nor should it be compacted: 34 conventions at a median of 13 lines is honest
density, and unlike §2 — where the summary line was the point and the detail was elaboration —
§7's content IS the policy. `HURDLE = 15%` without its derivation (risk-free ~4.3% + equity premium
~5% + demanded excess) is a number the next person edits, because nothing on the page says why.
Splitting a rule from its justification is how rules quietly change.

**SO THE ≤600 TARGET WAS WRONG.** I picked it before knowing what the file contained. At **1,892** —
§2 as 73 one-line capability summaries, §4 as 25 gated items with triggers, §7 as the ratified
policy in force — the file is readable in one sitting, which was the actual goal. Chasing 600 would
mean cutting summaries that are already one line each, trading real information for a number I
invented.
