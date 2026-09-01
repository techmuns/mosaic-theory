---
id:
status: open
prs: []
date: 2026-09-01
supersedes:
superseded-by:
---

# The themes surface showed the three least-evidenced drivers and hid the two best

**WHAT.** `frontend/build.py` now discovers the CANONICAL committed freeze
(`data/themes/baskets/<driver>.json` + `data/themes/ledgers/<driver>.jsonl`), ACCUMULATES the index
instead of rebuilding it from one run, and stamps each driver with a pipeline `stage`. The themes
index is re-cut as a stage-grouped work queue: a flat stat band, one row per driver, and a
`Needs next` column naming the single thing standing between that driver and its next stage.

**WHY — THE SURFACE WAS INVERTED.** `build_themes` globbed `forward_*_baskets.json` under
git-ignored `data/forward/`, a layout that no longer exists. `pairs` came back EMPTY on every run,
the preserve-guard kept three July pages frozen in place, and the two drivers with a real
ratification ledger were structurally unreachable:

```
ai-datacenter          card - scan - basket Y ledger -   PAGE Y
defense-demand-shift   card - scan - basket Y ledger -   PAGE Y
truckload-supply-purge card - scan - basket Y ledger -   PAGE Y
ai-value-migration     card Y scan Y basket Y ledger Y   PAGE -
glp1-drug-value-chain  card Y scan Y basket Y ledger Y   PAGE -
```

The index therefore read "0 Buys across 3 themes" while 183 ratified names sat in two drivers it
could not see. The empty `mirror_slug` on both was a SECOND lock on a door already bricked up — it
gates the thesis-card mirror, not the page.

**THREE DEFECTS FOUND BY BUILDING IT, none visible from reading:**

1. **Repointing discovery would have DELETED the July history.** `build_themes` writes `index.json`
   from the summaries it built THIS run; the three July `<slug>.json` survived on disk (it never
   rmtree's) while the index listing them dropped to two. A page nothing can reach is a deletion the
   file listing hides. The index now carries forward any committed page this run did not rebuild —
   the operator's standing rule is that every historical theme scan is preserved.
2. **`screened` read the newest scan file, not the archive.** A scan history accumulates: the full
   sweep plus later deltas. `hist[-1]` reported ai-value-migration as **102** names screened against
   a true **1,354** — a 13x understatement on the one number that says how much was looked at. It is
   now the union, latest-wins per ticker.
3. **The pooled line stated a false comparison.** It asserted `poolable but UNPOWERED (n <
   _MIN_THEMES)` unconditionally with the numbers interpolated, so the first run to cross the
   threshold rendered the literal falsehood **"5 < 4 themes"**. Crossing it is a real change in what
   the diagnostic may claim and must not arrive as a typo.

**TWO PIECES OF COPY WENT FALSE THE MOMENT A DRIVER FROZE**, and were removed rather than reworded
around: the verdict/scan KEY described `firm / partial / early / none` columns that left the table
with the stage regrouping, and the summary claimed "no Buy verdicts, so no buy leg" beside a band
reporting 183. The `.pooled-strip` amber gate gradient also stopped being right: it read as an alarm
about numbers that are merely pending, so the band is flat on the page background and the gate
register stays reserved for the gate.

**ALSO CARRIED**: `passedCount` — the AVOID leg, which no consumer could reach before, so the
surface could only ever show one leg of a two-legged measurement; and `firstTest`, read from the
declared card so the page cannot drift from the operator's own deadline.

**HOW VERIFIED.** Full offline suite green — **3,436 passed, 130 skipped**; `ruff` and
`mypy --strict vinci` clean. Rendered and read in the browser at 1440x1000, light AND dark, with no
console errors: the band reads UNDEFINED / 2 of 5 / 183 buy · 218 avoid / Nov 30 2026, and the table
groups `CLOCK RUNNING · 2` above `ARCHIVED … · 3`. Three pins added, two mutation-tested: dropping
the accumulation reds the carry-forward pin, and restoring the unconditional sentence reds the
false-comparison pin.

**A FATAL ERROR THE CACHED TAB HID.** Removing the key left one `VS_KEY` reference behind; the
already-loaded tab kept rendering the old markup and showed nothing wrong, while a FRESH tab threw
`VS_KEY is not defined` and rendered "Loading themes…" forever. Python's `http.server` sends no
cache headers, so a preview tab silently serves stale ES modules — verifying a frontend change in
the tab that was already open is not verification.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **Stage is derived from what is on disk, so it cannot see a worksheet.** A driver whose sheet is
   out with an analyst reads `scanned`, identical to one nobody has touched. The worksheet lives
   outside the repo; inventing a `reviewing` stage would be asserting state the build cannot
   observe. FALSIFIER: if the operator wants that distinction, the worksheet's issue/return has to
   be recorded in the repo first.
2. **Neither frozen driver has a `mirror_slug`,** so the thesis card still mirrors nothing and the
   theme DETAIL page is unchanged by this work. The index reaches both pages; the detail redesign
   is not built.
