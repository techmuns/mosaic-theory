---
id: 
status: recorded
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

0. **PRINT-LAYOUT PASS — 2026-07-29 (operator: "this looks really bad and unprofessionally
   compiled as an equity analyst report").** Opened as a wide-table fix; the exported PDFs showed
   the width issue was a minority of the problem.
   **ROOT CAUSE OF THE HEADLINE DEFECT:** nine `@media (max-width: …)` blocks were PHONE
   breakpoints with no `screen` qualifier, and the A4 page box is ~794px — under all of them. So
   **every PDF ever exported got the mobile layout**: the At-a-glance band's five-cell contract
   collapsed to `repeat(2, 1fr)` and printed as a ragged 2x3 grid. All nine are now `screen and`;
   0 of 9 can match print. The band had never survived export, and the v2 work that designed it
   (#22 below) was previewed on screen only.
   **ALSO FIXED:** sources printed as one run-together paragraph (now one per line); chart x-labels
   physically overlapped (AORT 24 labels, 10 overlapping pairs, −6px min gap → thinned to 12, 0
   overlaps, newest period always kept); `[amended …]` tags interrupted the thesis mid-sentence
   (split into an "Appended since the verdict" block, mirroring how seal.py already models the
   text); tables used 40–60% of the measure (wide grids now take it, 2–4 column reference tables
   stay content-sized — stretching those was tried and reverted once already).
   **BULK AUDIT TIERS DO NOT PRINT** — the 250-event revision log expanded to THREE PAGES mid-report
   under the T1 force-open rule. It is the working paper behind aggregates the section already
   states. Suppressed to a pointer; NOT a breach of the three-tier rule, which reads "…or the
   JSON". First attempt used a bare `.ds-bulk { display:none !important }` and **shipped broken**:
   T1's `details:not([open])` is (0,1,1) against a class at (0,1,0), and among !important
   declarations specificity wins. The verification missed it by opening the `<details>` first —
   the one state where that rule cannot match. Pinned at (0,2,1), both open states.
   **WIDE TABLES PRINT AS CONTINUED BLOCKS** (P7). AORT's quarterly is 42 columns and ran 2154px
   past the measure; the browser does not paginate sideways, so the PDF silently dropped the
   most-recent columns while looking complete. Now split with the label column repeated —
   verified 252/154/54 cells preserved, zero missing.
   **REVISION LOG IS TABULAR ON BOTH TIERS**, and building it exposed a twin bug: the md sorted
   broker-days by date alone while the web reverse-sorted the composite string, so with the cap at
   six **the two surfaces published different broker-days**. Fixed to date DESC + broker ASC by
   CODE POINT on both sides (localeCompare collates case-insensitively and disagreed with python).
   Columns are now Revisions/↑/↓/Init/Withheld/Δ and CLOSE by construction. `Change Type = "-"`
   was **verified against the licensed workbooks, not guessed**: 349 of 349 such rows are fully
   entitlement-gated and 0 of 2,513 with a real type are — it is CIQ's own withheld marker, not an
   extractor defect, so nothing upstream needs changing.
   **PAGE COUNT ROSE 17 → 24 (AORT), AND THAT IS THE TRADE**, recorded so it is not re-litigated as
   a regression: ~5 of the 7 added pages are recovered content — the quarterly columns that used to
   fall off the sheet, and sources legible at one per line. The old count was short because the
   export was discarding data. Operator accepted 2026-07-29.
   **LESSONS (three, all mine):** a width measurement cannot see a HEIGHT/pagination failure — the
   first fix pushed AORT to 27 pages via `.fact { break-inside: avoid }` on a split fact; a
   source-text pin that scans raw source matches ITS OWN explanatory comment (hit three times,
   now strips comments first); and a print-media contract cannot be verified by simulation alone —
   the operator's real export caught what every green check missed, twice.
