---
id:
status: shipped
date: 2026-08-31
prs: [550]
supersedes:
superseded-by:
---

# STATE.md gets a tripwire, because the growth that caused the migration had already come back

**WHAT.** A whole-file ceiling of **2,500 lines** on STATE.md, set by operator ruling, with a
second pin refusing to let the file sit within 100 lines of it.

**WHY NOW.** The knowledge-ledger plan took STATE.md 19,241 → 1,892. Five days later it was 2,085
— about **38 lines a day**, which doubles the file in roughly seven weeks. P0 recorded the original
growth as "doubling every ~4 weeks", so the same shape had already returned, in the file the plan
had just finished rescuing.

**WHAT WAS AND WAS NOT GUARDED.** Two of eight sections: §5.0 at a 60-line cap, and §5's archive
frozen at 24 (+40 slack). §1, §2, §3, §4, §6, §7 and the file as a whole had nothing. So there was
no way to tell legitimate growth — a new capability genuinely belongs in §2 — from the drift that
produced 19,241 lines, until it was unreadable again. That is the gap this closes: not the growth,
the *invisibility* of it.

**WHY 2,500 AND NOT SMALLER.** The number is the operator's, and deliberately generous: 415 lines
of headroom over today. P3 retracted an earlier ≤600 target with the reasoning that a bound
invented before knowing what the file contains forces real information out to satisfy an arbitrary
number. This is a **tripwire, not a diet** — it fires long before the file stops being readable in
one sitting, which P3 named as the actual goal.

**THE MESSAGE IS THE FEATURE.** A size guard that only says "too big" invites the wrong fix. When
this trips it says: *move the detail into a record under `docs/records/`, never delete it* — the
snapshot keeps the one-line claim and a pointer, the ledger keeps the full account forever. And it
names the alternative out loud: raising the constant is a decision to let the file grow, which has
to be deliberate rather than silent.

**THE SECOND PIN IS THE ONE THAT MATTERS LONGER.** A ceiling with no headroom is a ceiling that
gets raised by whatever ordinary build first bumps into it — which is how a limit stops meaning
anything. Failing at 100 lines of slack forces the migration while it is still small.

**VERIFIED.** 3 mutations: the file grown past 2,500 CAUGHT; grown to 2,450 — inside the ceiling
but into the headroom — CAUGHT; today's real 2,085-line file PASSES. Run against the live
committed STATE.md, not a fixture.
