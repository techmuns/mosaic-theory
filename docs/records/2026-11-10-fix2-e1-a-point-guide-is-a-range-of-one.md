---
id:
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# A point guide is the range [low, low]: a missing high is never a high of zero, so a check that passed on a failure now fails (TeamNostra fix request 2, RE1-D16). 0 of 28 frozen pages move

**WHAT.**
- `vinci/edgar/primary_source.guide_verification_read` compared the two guides' highs as
  `(ciq_high or 0.0) - (release_high or 0.0)`.
- It now compares each side's TOP: its high, or its low when it states none (a point). A point
  meets only a point, or a range that is one.
- The two `or 0.0` sites leave `tests/test_zero_coercion_lint.py`'s allowlist with them. That list
  had allowed them with a reason this record disproves: "one side's high against the other's none
  is a mismatch, as it should be".

**WHY.**
- **TeamNostra's reproduction (RE1-D16).** CIQ guides a point of −0.05, and the release guides
  −0.05 to 0.00. The check read "cross-source VERIFIED", where −0.05 to 0.10 read "differ". That is
  a silent wrong value: a check that passes on a failure.
- **The same expression failed the other way.** A point CIQ states as a range of one
  (11,800–11,800) against the release's point 11,800 read MISMATCH, because its high was set
  against a zero.

**HOW VERIFIED.**
- **Fail first.** `tests/test_point_guide_verification.py`, run in a throwaway checkout of
  `origin/main` `6fbbb4a2`, had 3 of 6 failing:
  - TeamNostra's case;
  - its mirror (CIQ −0.05–0.00 against a release point −0.05);
  - the range of one against a point.

  The 3 passing are guards: a point against itself, a range against itself, and a point against
  a wider range still differing. All 6 pass after, and so do `test_cross_check.py`,
  `test_primary_source.py` and the zero-coercion lint.
- **$0 page compare.** The 28 pages frozen at `bcda7ce3` each print one guide-verification line,
  each read on 2026-11-10:
  - every VERIFIED line (AMZN, AORT, BRBR, CNXC, VITL) compares two full ranges;
  - the MISMATCH lines (LLY, VRRM) compare full ranges too;
  - every other page's line is a check that did not run.

  No page sets a point against anything, so no page moves. None needs a refresh or a rebuild.
- **The live pages too.** The same 28 lines read the same at `6fbbb4a2`, this branch's base (#936
  rewrote 20 page records after `bcda7ce3` and moved no guide line).
- **The version.** Row `2026-11-10.point-guide`, re-pinned.
- **The full offline suite** ran green before commit (`bin/commit`).

**BOUNDARY.**
- **28 pages:** `data/dossiers/*/dossier.json` at `bcda7ce3`. The lines were found by the text
  "guide verification (" in each page. The same read at `6fbbb4a2` (the live pages this merges onto).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A point now agrees only with a point or a range of one.** A CIQ point that sits inside a
  release range reads MISMATCH, as a point against a range always did when its high was not zero.
  Whether a point inside a range should count as corroboration is a different rule, and it is not
  made here. *Falsifier:* a page whose guide check reads MISMATCH where both sources state the same
  guide in different shapes.
