---
id:
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# The insider line's count of lines with no price names its horizon — "1 of 2 sales in the 3y scanned with no price stated" — the Codex review finding #995 merged without (TeamNostra fix request 2, RD-D2) — latent, 0 of 27 pages move

**WHAT.** `vinci/dossier/mechanical.compose_insider_line`: the clause #995 added beside the
largest sale now states its horizon. It uses the scan's own wording, which the absence clause
already uses: "in the 3y scanned", or "since <date>" for a foreign private issuer. The horizon is
built once and both clauses read it.

**WHY.** Codex, on #995 (P2, inline): the clause counts every row in the scan, but it follows
"sells N … — in the last 182 days". So an unpriced sale outside the window read as one inside it.
That breaks EVERY COUNT STATES ITS BOUNDARY. #995 was merged at `5ccec3bb`, before its round-1 fix
(`0ac096a2`) was pushed, so the fix lands here, off main `7edbfa36`, under its own vintage.

**HOW VERIFIED.**
- **Fail first, on main `7edbfa36`:**
  - `tests/test_insider_occurrence.py::test_rd_d2_the_unpriced_count_states_its_horizon` fails at
    line 180. Its unpriced sale sits outside the window, and the domestic and the "since" forms
    are both pinned.
  - `::test_rd_d2_largest_ranks_only_priced_lines_and_counts_the_rest` fails at line 153, because
    it now expects the horizon.
  - The end-to-end pin in `tests/test_dossier.py`, a Form 4 with no price read through the
    reader, takes the horizon.
- **The $0 replay** (#995's): 5,791 Form 4 filings in the 27 pages' scans, with 0 open-market P or
  S lines without a price. So the line moves on 0 of 27 pages.

**BOUNDARY.**
- **Pages:** the 27 committed pages.
- **Window:** each page's own 3-year Form 4 scan.
- **Unit:** one P or S row.
- **Date:** 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Deferred, from this PR's review:** on the foreign-issuer path, rows are bounded by FILING date,
  not transaction date. A late Form 5 can carry a trade dated before the issuer's start date, and
  "since <date>" then over-claims for it. The gap is already in main's absence, last and largest
  clauses, and this change only reuses their wording.
- *Falsifier:* a foreign issuer's page whose line counts a trade dated before its "since" date.
