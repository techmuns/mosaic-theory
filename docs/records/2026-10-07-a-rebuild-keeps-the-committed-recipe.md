---
id: 2026-10-07-a-rebuild-keeps-the-committed-recipe
status: shipped
date: 2026-10-07
prs: [670]
supersedes:
superseded-by:
---

# A re-assembly keeps the committed recipe — every hand re-tag on record had been erased by the next one

**WHAT.** `assemble._write` now applies `preserve_operator_tag` — the rule `anchor-backfill` has
used since July — before it writes. When the committed anchor's recipe differs from the one this
build computes, the COMMITTED recipe and its reason are written, and a caveat on the page names
both. A committed anchor block that does not validate is refused rather than overwritten. `_write`
returns the dossier it actually wrote, and `assemble_one` returns that.

**WHY.** Every hand re-tag on record was erased by the next full re-assembly — four of four:

| name | re-tag, by hand | erased by |
|---|---|---|
| AORT | `R2_NEEDED`, 07-21 (`feca6b93`) | re-assembly, 07-23 (`28baa8f5`) |
| CNXC | `R1_NOT_ROBUST`, 07-21 (`9b9228bc`) | re-assembly, 07-22 (`5d663ea3`) |
| VITL | `R2_NEEDED`, 07-21 (`9b9228bc`) | re-assembly, 07-22 (`4a4e00ee`) |
| GOOGL | `R3_forward_pe`, 09-01 (`c005449f`) | artifact pass, 09-18 (`0251f4cb`, #631) |

Assembly computed the anchor fresh and wrote it over the committed block; only `anchor-backfill`
called `preserve_operator_tag`. The consequence reached the scenario gate: `check_tier_agreement`
refuses an R3 record against an R1 hint, so on 2026-10-07 the gate refused GOOGL's own committed R3
record — the fund's first confirmed position — and refuses an AMZN R3 record for the same reason.
Found while checking what an AMZN scenario would need.

**ONE RULE FOR BOTH WRITE PATHS, AND ITS LIMIT CARRIED WITH IT.** `preserve_operator_tag` cannot tell
an operator's tag from the machine's — provenance is not recorded on the block — so ANY divergence
keeps the committed recipe. Replayed over the whole committed history, the rule holds back exactly
six of 521 anchor transitions: the four erasures above, and NCNO's flip to `unknown` during a data
gap (07-23) and back (07-27), where `R2_NEEDED` was right on both sides. It never holds back a
recipe change that should have applied. Of the rest, 505 change no hint or reason, and in 6 the
anchor's applicability changed and the fresh reason wins — that branch is unchanged.

**WHY A CAVEAT, NOT A QA FLAG.** Once the build stops applying its own proposal, a name drifting
across a recipe boundary is noticed only if the page says so. `flags.is_qa` hides only its explicit
list, and a wrong recipe is invisible in the arithmetic it produces.

**HOW VERIFIED.**
- **Real replay of the four erasing builds** through the fixed `_write`: the full committed prior
  file from git on disk, and the full dossier each erasing commit wrote handed in as the build. All
  four keep their recipe and reason, and the caveat is on the rendered page.
- **Corpus negative:** all 26 committed dossiers written over a copy of themselves → 0 anchor or
  caveat changes.
- **Tests** (`tests/test_rebuild_keeps_committed_recipe.py`): the four incidents through `_write`
  and read back from disk (frozen fixture of the verbatim blocks from git), the 26-name negative,
  and the refusal. **Four mutants, all killed:** call removed from `_write` → 5 fail; invalid block
  accepted → 1; guard always rewrites → 26; caveat dropped → 4.
- Full offline suite green; `ruff` and `mypy --strict` clean (counts in the PR).

**BOUNDARY.** "Four of four" and "521 transitions": every committed version of
`data/dossiers/<T>/dossier.json` for the 26 names with a committed dossier, main @`4ab4de36`, each
version compared with the one before it. A "re-tag" is a hand edit naming a recipe the machine did
not propose — AORT's, CNXC's and VITL's are named in `preserve_operator_tag`'s docstring; GOOGL's
reason opens "OPERATOR RE-TAG". "3 of 8": GOOGL's committed anchor versions, same history.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A recipe now changes only by hand, on both write paths — the machine's tags included.**
  Accepted: it is the tagger's own contract (propose-only), and every divergence prints as a
  caveat. Falsifier: a recipe caveat that stands unacted across two re-assemblies of the same name —
  then it is noise, and recording provenance on the block (so only an operator's tag is kept) is due.
- **NOT FIXED HERE — reported (§5.0 row 10).** `check_tier_agreement` reads `anchor.applicable`, the
  R1 arithmetic's bit, as the RECIPE's. Replaying GOOGL's 09-18 build through the fixed path keeps
  `R3_forward_pe`, and the gate still refuses it, because that build found R1 inputs incomplete.
  GOOGL's `applicable` was False on 3 of its 8 committed anchors. Today both GOOGL and AMZN carry
  `applicable: true`, so an R3 re-tag on today's anchor passes the gate (measured 2026-10-07).
- **NOT DONE — the four tags are not restored.** Restoring them is an artifact change on the
  operator's word (§5.0 row 32, item 8). GOOGL's reason text is in git at `c005449f`.
