---
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, the fact layer: RFL-D1 to RFL-D10 are all fixed on main (#992, #999), each confirmed by TeamNostra's own reproduction; slices 2b–6 are re-scoped against them (STATE row 44)

**WHAT.** Stream S3 of fix request 2 (issue #1004) took "any fact-layer remainder of RFL-D1–D10"
and the hand-off "Fact layer slices 2b–6, re-scoped against RFL-D1–D10 (#992, #999)". There is no
remainder. Every ID is fixed on main, and no code changes here. STATE §5.0 row 44 is re-scoped:
- what RFL settled;
- what slice 2b now owes;
- what slices 3, 4 and 6 inherit;
- the notes no ID asks for (FL-D11, FL-D12, the companyfacts-lag check #999 proposed).

| ID | Order | Fixed by | Confirmed on main `2637e91b` by |
|---|---|---|---|
| RFL-D1 a read past the copy's fetch | 5 | #992 `31ff7b87` | FL E1 and E5 (fix pack 2, `notes/FL_work/scripts`): a read past the copy's `fetched_at` now raises `FactStaleError` naming the fetch. At `622786a2` it returned the copy's latest value, unflagged |
| RFL-D2 no acceptance time | 7 | #992 | `test_facts_fix2.py`, 9 `rfl_d2` tests pass. The cut stands at 16:00 New York and reads `acceptanceDateTime`. The pages snapshot `edgar-e94e051d94ce1985` (#999) states a time for each of its 1,569 filings |
| RFL-D3 originals not kept | 7 | #999 `3d55bc31` | `test_facts_originals.py`, 13 tests pass. "Keeping originals is your call": the operator kept the pages' 81 originals, write-once by sha256 in R2 |
| RFL-D4 the reader trusts the manifest | 7 | #992 | FL E2 (d): the consistent edit is now refused on open ("the manifest's content does not recompute to its id"). At `622786a2` it served 120.3 for 12.03 |
| RFL-D5 "not ingested" = "nothing filed" | 7 | #992 | `test_rfl_d5_*` pass: BURL and MCK are `FactNotHeldError`; a held company with nothing filed is still `FactUnknownError` |
| RFL-D6 no source check on upload | 7 | #992 | `test_rfl_d6_*` pass: a `ciq` snapshot is refused before any request; the committed `edgar` ones may upload |
| RFL-D7 parity on a refreshed cache | 6 | #992 | FL E5: parity now names the changed response (True). At `622786a2` it gave 2 store "differences" |
| RFL-D8 duplicates as differences | 6 | #992 | `test_rfl_d8_*` pass: a duplicate held once is named, and zero-diff |
| RFL-D9 orphans on a shape error | 6 | #992 | FL E6: exit 1, "nothing written", 0 objects left on disk. At `622786a2`, 6 objects were left |
| RFL-D10 wrong reason for a wrong shape | 6 | #992 | FL E6: CCCC is unread because "the cached response has no 'facts' key (its keys: ['cik', 'entityName']): not companyfacts" |

**WHY.** CLAUDE.md requires STATE to be updated where a row's truth changes. Row 44 said "no
staleness signal yet" and named 2b's owed work before RFL-D1, D2, D4 and D5 existed. Read now,
that row understates what 2b must carry:
- the committed screen snapshot is schema v2, so a read on a filing's own day raises
  `FactCutUndeterminedError` until it is re-ingested;
- 1,677 of its 1,692 copies predate 2026-10-01, so a read past a copy's fetch now raises;
- the 372 companies not in the SEC cache must read as not held.

**HOW VERIFIED.**
- **TeamNostra's scripts.** E1, E2, E5 and E6 were copied out of the pack and run unchanged,
  except for their `assert "/wt_FL/" in vinci.__file__` line, and E6's last stderr read, which
  now reads stdout and stderr because the refusal prints on stdout. They ran on main `2637e91b`
  with this checkout's `vinci`. E2 ran against a copy of this checkout's `data/facts`. The
  outputs are quoted in the table.
- **The merged tests.** `tests/test_facts_fix2.py` and `tests/test_facts_originals.py` pass on
  main, 30 cases (`pytest -m "not network"`).
- **E2 (e)** still serves a swap made after the first read in one open store (120.3). That is
  FL-D11, a note no ID asks for, as #992's record says. It is listed open in row 44.

**BOUNDARY.**
- Every run was on 2026-11-11 at main `2637e91b`.
- E1, E5 and E6 use constructed inputs (fictional CIKs 999998, 999999 and 900001 to 900006).
- E2 used a copy of `data/facts`, the pages snapshot `edgar-4f3207f4da9fb71a` (v2, the archive
  #999 superseded), NFLX's FY2023 diluted EPS.
- "1,677 of 1,692" and "372" are row 44's own counts for the screen snapshot
  `edgar-6e0e4626855b9fce` (screen run 2026-10-16-01's universe), measured 2026-11-04. They are
  not re-measured here.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Nothing new. Row 44's (iii), whether the screen keeps the
day-level cut or adopts the acceptance cut, and slice 4's upload of CIQ-derived facts are
rulings, named in the row.
