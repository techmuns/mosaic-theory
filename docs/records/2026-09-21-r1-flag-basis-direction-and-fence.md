---
id:
status: open
date: 2026-09-21
prs: []
supersedes:
superseded-by:
---

# The R1 flag's basis sentence reads the right way round and never prints a signed percentage; both round-trip pins guard growth, not presence

**WHAT.** Three defects from #636 and #637. The first artifact pass to carry the new fields (AMZN,
WLK, PARR, 2026-09-21) surfaced all three when it ran the full offline suite red, before anything
was committed.

1. **The basis sentence ignored direction.** Whenever the two sources differed by 2+ points on the
   common year, the flag said "part of this gap may be basis, not business." But the twelve months
   are CIQ and the median is GAAP. So a year where CIQ reads above GAAP pushes the shown gap UP. That
   can create part of a gap ABOVE the median, but it can only narrow a gap BELOW it (and the mirror
   holds when CIQ reads below). WLK is the second kind: 8.7 points below, with CIQ 12.5 points above
   GAAP on FY2025. The sentence told the reader to discount a gap that, measured like-for-like, is
   8.8 points with CIQ on both legs and 20.8 with GAAP on both. It now says which way the difference
   pushes the gap. The two margins are stored as `basis_gaap_margin` / `basis_ciq_margin`, so the
   direction is data, not only prose.
2. **It printed a signed percentage into the fenced screening block.** WLK's FY2025 is a loss on
   both sources, and `:.1%` printed "GAAP -14.1% vs CIQ -1.6%". That is exactly the token
   `test_screening_context_never_differences_the_anchor_against_spot` forbids, because a signed
   percentage there reads as upside against spot. Losses are now written in words ("a 14.1% loss"),
   both in the basis clause and for a loss-making twelve months. The fence was not weakened.
3. **Both round-trip pins asserted absence, not growth.**
   `test_committed_pages_round_trip_byte_identically_with_the_new_field` (#636) and
   `test_committed_pages_round_trip_without_the_new_key` (#637) asserted the key never appears in
   any committed page. That held only until an artifact pass landed a real key, and both went red
   on AMZN. They now assert presence parity (the key survives the round-trip exactly when it was
   there) and no null.

One of #636's own unit pins asserted the defect: `test_midcycle_flag_fires_both_ways…` expected
"may be basis, not business" on WLK's numbers. It is rewritten to the corrected behaviour.

**WHY.** The artifact-pass rule caught this, as designed. The pages were written, the frontend
built, and the full offline suite run before anything was committed. Three tests went red, and
their causes were code, so no artifact commit could fix them. The direction defect was found
separately, by reading WLK's rendered sentence against its numbers. The suite did not catch it,
because no committed page carried the flag, and the unit pin written with it encoded the wrong
answer. The #636 record quotes WLK's sentence as a finding and says its round-trip guard "exists to
redden only if a null key ever appears". Both claims are corrected by an amendment appended there.

**HOW VERIFIED.**
- **WLK, real numbers.** LTM 1.1% (committed CIQ panel) against a 9.8% median over 10 fiscal years
  (EDGAR GAAP). FY2025: GAAP −14.13% (companyfacts OperatingIncomeLoss −1,578 / Revenues 11,170,
  $M) vs CIQ −1.60%. Like-for-like gaps:
  - CIQ on both legs: −8.76 pts (FY17–FY25 panel median 9.82%).
  - GAAP on both legs: −20.8 pts (LTM GAAP −11.02% = FY25 + 6M26 − 6M25, the filer's own columns).

  The page now reads: *"On FY2025 the two sources differ by 12.5 points (GAAP a 14.1% loss vs CIQ a
  1.6% loss): GAAP carries charges CIQ's EBIT excludes, and R1's median sits on the GAAP side —
  which pulls the median down toward the twelve months, so the difference narrows this gap rather
  than creating it: no reason to discount it, and if anything it understates it."*
- **Fleet.** The backfill's own compute, run on all 22 committed pages: 7 fire (AMZN, BRBR, GOOGL,
  LLY, NFLX, PARR, WLK). WLK is the only one whose sources differ by 2+ points, so it is the only
  page the defect reached.
- **Pins.** 4 new, 3 rewritten.
  - Against main's `anchor.py`, 4 go red: the defect.
  - On the pages the first pass wrote, the new corpus pin and the existing fence both go red on WLK.
  - After re-running the backfill with this code, all go green.
- **Mutations, 4 of 4 caught.** The writer leaking a null `midcycle_gap`; `segment_profit` leaving
  `DROP_WHEN_NONE`; the stored margins swapped; the direction inverted (caught by 3 pins).
- **The post-merge state.** This code plus the pass's three pages, re-backfilled: full offline suite 3,940 passed, 42 skipped, 0 failed.
  This branch alone, on main's pages: 3,940 passed, 42 skipped, 1 failed — this record's own empty `prs:` trail, closed by naming the PR.

**BOUNDARY.**
- **Pages:** 22 committed pages at `origin/main` 641e3a6; EDGAR companyfacts fetched 2026-09-21.
- **"Fires":** |`gap_pts`| ≥ `MIDCYCLE_GAP_PTS` = 5.0, on the stored 2-decimal rounding.
- **"Differ":** `basis_gap_pts` ≥ `BASIS_AGREE_PTS` = 2.0.
- **Thresholds:** both unchanged, set by face validity; no forward return was read.
- **Gaps:** percentage points of operating margin.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A flag written before this change stores no margins. The corpus pin refuses such a page ("re-run
  anchor-backfill") rather than excusing it. None is committed on main.
- **Verification incident, not a code defect.** The first re-backfill after the mutation run
  executed mutation 4 from a stale `.pyc`. The restore was the same size and landed in the same
  second the mutant was compiled, so Python's mtime+size check accepted the cached bytecode. That
  run wrote WLK's sentence inverted while the source on disk was correct. It was caught by reading
  the rendered sentence against the stored margins, and re-run from clean bytecode. Nothing was
  committed from it. It is recorded here because a mutation loop can silently poison a later real
  run, and a green diff of the source does not show what executed.
