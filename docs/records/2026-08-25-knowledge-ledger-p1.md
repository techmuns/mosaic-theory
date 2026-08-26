---
id:
status: shipped
date: 2026-08-25
prs: []
supersedes:
superseded-by:
---

# The archive left the snapshot: STATE.md 19,241 → 5,433 lines

**WHAT.** §5's 168 entries and the governance log's 30 incidents are now **198 immutable files**
under `docs/records/`, body verbatim. STATE.md keeps §5.0 OPEN NOW plus a pointer block. §5 went
**9,908 → 51 lines**, the governance log **3,957 → 10**. §2 (3,680 lines) stays, deferred to P3 by
operator ruling — so the file is not yet at its ≤600 target, and that is stated rather than implied.

**THE FINDING THAT SHAPED IT.** §5's entries have **no machine-detectable boundaries**. Three
independent probes agreed: wording does not separate an entry from a continuation (`REVIEW PASS ON
#500/#501` is an entry, `FIRST RUN AFTER THE FIX` is not, and they read identically), structure does
not either (no `---` rules; blank lines split 470/332 before bold headers), and confidence-tiering
misclassified in both directions. So the operator ruled: **read all 218 candidates by hand.**

That pass found what no rule could — **seven `###` sub-headings that ARE entry starts**, one of them
inside a 615-line span the dated-bold scan had read as a single entry. The judgement is stored as
DATA (`scripts/state_entry_boundaries.txt`), not re-derived by a regex that would silently stop
matching the next time anyone edits the file.

**HOW VERIFIED — twice, and the second check found something the first could not.**
The migration script proves losslessness by **reconstruction**: concatenating the records reproduces
the planned span byte-for-byte, and it refuses to write otherwise (198 records, 13,829 lines).
An *independent* rebuild — records + snapshot against the pre-migration file — then found **3 tokens
missing**: the old governance-log title, *"two-channel divergence (opened 2026-07-26)"*. The script
could not see it, because it verified what it PLANNED to cover, not what the snapshot rewrite
actually REMOVED — those differ by the section heading. The title is restored in the pointer, and
the re-run reports **zero missing tokens**.

**GUARDS EXTENDED.** The S/D citation test now resolves **corpus-wide** (STATE.md + `docs/records/`);
without that it reported all 13 identifiers as dangling on the migration commit — correct behaviour
on a stale corpus. `README.md`/`TEMPLATE.md` are excluded by name, because the README's
*illustrative* identifier in its filename example was duly reported as a dangling citation — the
guard was right and the corpus was wrong. `recorded` joins the status vocabulary: most migrated
entries are diagnoses, audits and experiment records, and calling those "shipped" would be a small
lie repeated a hundred times. The archive cap is re-set from 9,904 to 60.

**WHAT IT COSTS.** Boundaries are one reader's judgement; where a call was uncertain the entry was
left ATTACHED to its parent, because merging is cheap (content preserved, citations still grep-hit)
while tearing is not. Five records exceed 300 lines; the largest was inspected and is genuinely one
entry. §2 is untouched, so STATE.md is readable-in-one-sitting but not yet small.
