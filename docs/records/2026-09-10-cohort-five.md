---
id:
status: open
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# Phase 4 — the cohort five: three shipped, two blocked, and the per-name config that made the tier real

**Phase:** 4 of the panel design (`docs/records/2026-08-27-between-print-monitor-panels.md`) ·
**Status:** built

## What shipped

Three of the design's five cohort panels, plus the per-name declaration layer the tier depended on:

| panel | status | source |
|---|---|---|
| capital conversion | **SHIPPED** | `commissioning` (#587), note resolved per filer |
| segment margin | **SHIPPED** | `segment_economics` (#578), note resolved per filer |
| cost of borrowing | **SHIPPED** | new — `vinci/borrowing.py`, from the CIQ capital panel |
| the race | **BLOCKED** | the counts are computed and discarded into a display string |
| backlog | **BLOCKED** | no structured field exists anywhere |

## The per-name declaration, and why it was load-bearing

The design says *"a NAME declares which panels it runs and with what config, beside its sleeve"*.
That declaration now lives in `data/followed.json` under a `panels` key, validated against the
registry **at read** — a typo'd panel key would otherwise surface as a missing tile on a page nobody
was watching.

**Measured, not assumed** (live EDGAR, 2026-09-10). Per-name note names turn refusals into resolved
reports on every name tried:

| name | repo-wide pattern | with its own declared note |
|---|---|---|
| GOOGL | REFUSED — two economics reports match, ambiguous | **READY** R83 |
| NFLX | REFUSED — no refinement match | **READY** R66 |
| LLY | REFUSED | **READY** R50 |
| V | REFUSED | **READY** R57 |
| UBER | REFUSED | **READY** R70 |

Five of five. Phase 3 recorded `segment_economics` refusing corpus-wide; this is what closes it.

**Two corrections to the design's own examples**, both measured:

* **WERN is not a rename case — it is a refusal case.** The design (and phase 2's module docstring)
  used "a trucking name commissioning tractors" as the argument for per-name config. WERN publishes
  **no** property-named `(Details)` report at all, searched as property / equipment / fleet / vessel /
  aircraft / network / infrastructure. The argument is still right; WERN is the wrong exemplar. The
  real rename pair is **GOOGL** (*"Supplemental Financial Statement Information - Property and
  Equipment"*) vs **NFLX** (*"Balance Sheet Components - Schedule of Property and Equipment and
  Accumulated Depreciation"*).
* **For UBER, IT and VRRM the first `/segment/` + `(Details)` match is a GOODWILL-BY-SEGMENT table** —
  the right name on the wrong numbers. Naming the report per filer is what prevents filing a goodwill
  roll-forward as segment economics.

LLY and V deliberately **do not declare** commissioning: neither publishes the note, so neither runs
the panel, and `not_in_set` renders nothing. That is the gating rule doing its job rather than a gap.

## A note's presence cannot be known offline

`resolve_cohort` takes an INJECTED `note_probe`. The resolver's contract is that it reads committed
artifacts and never fetches; resolving a note means fetching a FilingSummary. With no probe supplied,
every `rfile_note` requirement **refuses, naming the absent probe** — because a declaration is an
intention, not evidence, and assuming the note exists because a human wrote its name down is exactly
how one filer's note gets read as another's.

## Cost of borrowing, and the two bases

Weighted-average coupon struck per tranche on PRINCIPAL, from the capital panel's structured
`principal_musd` / `coupon` / `floating_rate`. The coupon cell is a display string (`"4.500%"`) and is
read through `clean_num` — the one shared, tested CIQ helper — never an ad-hoc regex.

**Two figures, each naming its basis.** A fixed-coupon average alone was not enough: **eight corpus
tranches are FLOATING yet state a current effective rate** (AORT's Secured Term Loan: 8.410% against
SOFR + 4.750%). So the panel reports both — the **fixed** average, which is contracted and will not
move, and the **all-in** rate, which is what is paid and resets — with the coverage of each.

The gap is material, not cosmetic:

| name | fixed (coverage) | all-in (coverage) | floating |
|---|---|---|---|
| AORT | 5.63% (16%) | **7.81% (100%)** | 84% |
| NCNO | 6.80% (23%) | 5.94% (100%) | 77% |
| WERN | 4.70% (5%) | 4.52% (46%) | 95% |
| V | 2.85% (100%) | 2.85% (100%) | 0% |

Reporting only the fixed average would understate AORT's cost of borrowing by 218bp. Names with no
floating debt show identical figures, which is the face-validity check.

**A floating tranche is never averaged into the fixed figure at zero.** Counting a 'NA' coupon as 0%
would drag the average down in proportion to how much floating debt a name carries — a fabricated
number that looks most authoritative exactly where it is most wrong. An all-floating stack **refuses**
rather than returning 0.0%, which would read as free money.

## The two blockers, recorded rather than stubbed

**the race** — the revision counts EXIST. `_revision_breadth` in `vinci/dossier/ciq_sheets.py`
computes `u` and `d` and then discards them into the display string `"47↑/0↓ last mo"`. Parsing them
back out is the prohibited re-parse the house rule exists to prevent. The fix belongs in the
extractor — emit the structured pair beside the line — and lands only on dossier re-assembly, so it
is a separate PR with a CIQ-workbook run, not a panel change.

**backlog** — appears nowhere as a structured field. Searched as "backlog", "remaining performance
obligation" and "RPO" across the corpus, plus `git log --grep` and `git log -S`: it exists only inside
management-commentary PROSE, on three names. A new extractor, not a panel. *Note for the next
searcher: a bare `/RPO/i` sweep reports 18 of 18 because it matches inside "Corporate".*

## Verification

Real runs throughout. Cost of borrowing hand-verified against GOOGL: 4.0237% over 58,004 of 67,504
musd (85.9% coverage), matching the module to four decimals, with a 9,000musd unpriced tranche and a
500musd floating tranche correctly excluded. Cohort resolution run offline (notes refuse) and against
live EDGAR (all declared panels ready).

Five mutations, all caught. **One of them passed at first and is the lesson:** deleting the floating
guard changed nothing, because the fixture gave every floating row coupon `"NA"` — so the
coupon-is-None check was silently doing the exclusion. Eight corpus tranches have a coupon AND a
benchmark, so the fixture was reshaped to AORT's real row; the mutation is now caught by three tests.
A fixture that does not carry the corpus's shapes tests the fixture.

Full offline suite green apart from the two standing environmental failures.
