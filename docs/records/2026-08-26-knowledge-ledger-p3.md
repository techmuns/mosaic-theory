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

**WHAT IT COSTS, AND WHAT IS LEFT.** §7 "The standing discipline" is **495 lines** and untouched:
it is RULES, not state, so it belongs in CLAUDE.md or `docs/engineering.md` — a placement decision,
not a migration, and it is the operator's. That is the gap between 1,892 and the ≤600 target I set
in the plan, and the target itself now looks wrong: at 1,892 the file is readable in one sitting,
which was the actual goal.
