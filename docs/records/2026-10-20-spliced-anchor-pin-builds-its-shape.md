---
id:
status: shipped
date: 2026-10-20
prs: [754]
supersedes:
superseded-by:
---

# The spliced-anchor pin builds its own failure shape instead of reading it off NFLX's living page

**WHAT.** `tests/test_valuation_basis.py::test_a_spliced_anchor_is_written_with_blocks_that_describe_it`
now sets NFLX's page to the inapplicable state itself (through `dossier_json`, so the stored blocks
describe it) before flipping `applicable` and checking that `write_recorded` re-derives the
valuation-basis block and records the write. Test only; no production code changes.

**WHY.** The pin took NFLX's COMMITTED anchor to be inapplicable — true when it was written, and the
real failure shape it was named after. #752's artifact pass makes NFLX applicable ($52.00: #749
reads its net debt, so #750's ex-lease bridge is complete), so the simulated flip became a no-op,
recorded nothing, and the pin failed on a page that is correct. Same class as the SMPL pin #751
fixed: a value read off a living artifact where the test meant a fixed shape.

**HOW VERIFIED.**
- Passes on main's pages (NFLX inapplicable) and on #752's rebuilt pages (NFLX applicable, copied
  in and restored): 28 of 28 in the file both ways.
- Mutation: dropping the recording step in `layer_refresh.write_recorded` fails the pin.
- Suite: see the PR.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Nothing beyond the pin no longer reading NFLX's live state —
which is the point; the end-to-end corpus checks of the same blocks remain.
