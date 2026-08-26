---
id:
status: shipped
date: 2026-08-25
prs: [502]
supersedes:
superseded-by:
---

# §5 is frozen; new entries are born as records

**WHAT.** `docs/records/` opens as the knowledge ledger — one immutable file per entry. STATE.md §5
stops taking new entries; from this build onward a build's narrative goes in a record, and STATE.md
receives only what changed about current truth (a §5.0 OPEN NOW row, or a ≤3-line claim with a
pointer). CLAUDE.md's session ritual and OPERATOR-ACTION RULE are re-pointed accordingly, and four
superseded docs are banner-marked in place. This is P0 of the knowledge-ledger plan; the migration
of the existing 253 dated entries is P1 and has not run.

**WHY.** STATE.md reached **19,209 lines / 1.72 MB**, growing ~2,700 lines a week and doubling
roughly every **four weeks**. §5 alone was 9,876 lines across 804 bold headers, 51 carrying a
done-marker — appended like a journal, trusted like a snapshot. Closing an item edited nothing
upstream, so the file came to answer one question two ways: an entry reading `STILL OPEN — the
queue has not actually advanced` sat below a later entry recording that same run green, and an
agent that had verified the run itself that morning proposed re-triggering it that afternoon.
"Read STATE.md first" had also become physically unfollowable at 1.7 MB.

The shape is not new — it is the architecture this fund already runs on its **data**: an
append-only ledger beside regenerable snapshots. STATE.md is the snapshot; this directory is the
ledger. It is corroborated by three outside sources: Anthropic's context-engineering guidance
(minimal instruction files; durable state retrieved **just-in-time via lightweight identifiers**,
never preloaded), Diátaxis (documentation fails when forms are mixed), and Nygard's ADRs (one file
per decision, **immutable once accepted**; reversal adds a record and flips a status).

**WHY IN PLACE, NOT MOVED.** The published plan proposed a new `docs/fossils/` directory. Building
it surfaced that **`planning/` already is the fossil home** — CLAUDE.md line 260 calls those files
"the planning fossils" — so a third convention would have repeated the very mistake the records
ruling corrected. Superseded docs are therefore **bannered where they sit**: status is marked, no
path breaks, and any physical move waits for P1, where the citation sweep already runs.

**HOW VERIFIED.** Fossils were classified on **evidence, not filename**: a doc is dead only if
nothing live cites it. `EDGE_THESIS.md` and `OBJECTIVE_FUNCTION.md` were *excluded* on that test —
STATE.md cites both — while `LOOP1_BUILD_PLAN.md`, `MINIMAL_LOOP.md`, `GRAPH_LOOP.md` and
`ui-glowup-plan.md` are referenced only by other fossils or by nothing. Guards in
`tests/test_records_ledger.py`: §5 may shrink but not grow (the freeze, checkable); records are
named and headed correctly; a record `id:` may not collide with an identifier STATE.md still holds
(the S10 collision class, arriving through the new directory); fossil banners point somewhere live.
Mutation-tested — see the PR.

**WHAT IT COSTS.** §5 keeps its 9,876 lines until P1 migrates them, so the *reading* problem is not
solved yet — only the *growth* is stopped. The freeze pin is a ceiling with slack, not an equality,
because closing an item legitimately edits §5 in place; it refuses new essays, not new strikes.
And `docs/audits/` remains a second dated-record convention until P1 absorbs it.
