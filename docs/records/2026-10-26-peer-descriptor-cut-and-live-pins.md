---
id: 2026-10-26-peer-descriptor-cut-and-live-pins
status: open
date: 2026-10-26
prs: []
supersedes:
superseded-by:
---

# A peer descriptor's word cut never ends on a function word, and three tests stop pinning values a re-assembly redraws

**WHAT.** Found by the 2026-10-26 artifact pass, which re-assembled 17 pages: its new pages turned
13 tests red. This change fixes the one real defect among them and moves the pins that broke on
data rather than on a defect. The pass itself lands separately, as artifacts only.

- **The defect.** `ciq_sheets._desc_first_sentence` cuts a first sentence longer than the 160-character
  cap at its last clause boundary, else at its last whole word. On a sentence with no comma inside
  the cap, the word cut can end mid-clause. Jack Henry's descriptor in V's 2026-10-12 comps export
  is a 173-character sentence, and the cut left "…payment processing services in the" on V's new
  page. `test_committed_peer_rosters_have_no_midclause_clip` refused it.
  - The word cut now backs off past any trailing function word, the same list the committed-page
    pin refuses. It never empties the descriptor, and a cut ending on a content word is untouched.
- **Two CNXC pins moved to a frozen fixture** (`tests/test_ev_gap_routing.py`). They hold CNXC as the
  two-forward-year minimum case of the adjacent-year check. The live page carries whatever years the
  latest CIQ export has, and the 2026-10-26 export added FY2028. The case now reads
  `tests/fixtures/cnxc_consensus_levels_two_years.json`: CNXC's block as committed at main `7213d486`
  (assembled 2026-08-18), frozen.
- **Two R4 tests strike their legs on the page's own close** (`tests/test_r4_template.py`,
  `tests/test_r4_card.py`). They set `underwrite_date="2026-10-09"` while reading the live page's
  `spot_as_of`. `scenario-create` refuses a spot after the underwrite date, correctly, so any
  re-assembly onto a later close turned 7 tests red. The underwrite date is now the template's own
  `spot_as_of`.

**WHY.** CLAUDE.md's TEST-LAYER RULE: an e2e test on a living committed artifact asserts invariants
only; a value pin lives on a frozen fixture. The CNXC and R4 pins asserted values of the live page,
so every re-assembly with fresh data broke them, and an artifact pass could not land green without
editing tests. The descriptor defect is the inverse case: a committed-page invariant caught a real
mid-clause cut on new data, so the code is fixed and the pin is kept as it is.

**HOW VERIFIED.**
- **Failing first:** `test_desc_word_cut_never_ends_on_a_function_word`, on the real Jack Henry
  sentence, failed on main's code with `'…services in the' == '…services'`. It passes on the fix.
- **The corpus:** old and new clippers over every peer business description in the assembler's 35
  CIQ comps exports, 338 descriptions in all. Exactly 1 changes, V's Jack Henry. Descriptions ending
  on a function word: 1 before, 0 after.
- **The moved pins:** the changed tests pass on main's committed pages (45 passed). With the changed
  test files copied into the artifact pass's worktree, they also pass on its 17 new pages (42
  passed), where 9 had failed or errored.

**BOUNDARY.**
- **Corpus sweep:** `/Users/work/Documents/GitHub/mosaic-theory-ta/data/manual/ciq`, the assembler's
  CIQ copy (35 folders, hash-identical to the operator's Drive on 2026-10-26). The population is
  every peer row of each comps export's Business Description sheet with a non-empty description.
- **Failures counted:** the artifact pass's full offline suite on 2026-10-26, run with the shared
  CIQ copy and store linked: 11 failed and 5 errors. 3 of those 16 fail identically on main
  `7213d486` with the same links (MCK's capital panel, the EV-bridge check against today's CIQ
  files, store freshness). The other 13 are the pass's: the 9 here, the descriptor pin, and three
  the pass lands itself (the monitor day, NFLX's companyfacts fixture, the staleness-split pin).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A descriptor can end one word earlier than before** whenever its cut lands on a function word.
  It is a capture, not the whole description, and the full text stays in the CIQ export.
- **The frozen CNXC block will not follow CNXC's coverage.** That is the point: the case it proves is
  "two forward years", and the live page no longer has it.
