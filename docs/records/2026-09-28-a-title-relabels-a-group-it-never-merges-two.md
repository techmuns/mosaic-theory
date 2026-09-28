---
id: 2026-09-28-a-title-relabels-a-group-it-never-merges-two
status: shipped
date: 2026-09-28
prs: [653]
supersedes:
superseded-by:
---

# A title relabels a group; it never merges two contracts

**WHAT.** #652 grouped covenant terms by the agreement title the document declares for itself.
That is right when several documents are amendments to ONE contract — BURL's arrive under four
different guessed instruments and must end up in one group — and wrong when two DIFFERENT
contracts happen to share a name. Review of #652 demonstrated the wrong half: two convertible
series, each with its own indenture, both heads titled "INDENTURE", collapsed into a single group.
The earlier series' conversion price DISAPPEARED, and the later indenture was published as an
`amended_by` of it — the fabricated supersession that (X-4) exists to refuse. For that case #652
was strictly worse than the mislabelling it replaced: silent data loss plus an invented
relationship, where before there were two correctly separated (if wrongly named) groups.

The fix: a title is WITHHELD from the collapse when it covers more than one BASE document from
DIFFERENT pointer families. Both halves are load-bearing.
- **Amendments excluded** — an amendment shares its base contract's identity, which is the whole
  reason a title may merge across guessed instruments at all.
- **Same-family bases excluded** — Nike's two successive 364-day agreements sit under one pointer
  family and were ALREADY one group before titles existed. Collapsing a renewal onto its
  predecessor is this repo's pre-existing behaviour, not something this change should alter.

Where the title is withheld, grouping falls back to the pointer family: the pre-#652 behaviour,
whose labels may be wrong but which never deletes a value.

A second, independent defect closed at the same time: `_LEAD_CODE` stripped a leading YEAR, so
"2021 CREDIT AGREEMENT" and "2024 CREDIT AGREEMENT" became one title. A year is a distinguisher,
not a code, and erasing it MANUFACTURES exactly the collision above.

**WHY.** The failure mode matters more than the frequency. A wrong covenant heading is a reading
error a human can catch against the cited exhibit; a deleted conversion price is invisible, and a
fabricated `amended_by` actively asserts that one contract supersedes another. The rule therefore
withholds the title wherever the document cannot prove it identifies ONE contract, and accepts the
weaker (older) label there rather than risk the stronger claim.

**HOW VERIFIED.**

*The three cases the rule must separate, each asserted:*

    A  two convertible series, both "INDENTURE", different families -> 2 groups, $12.34 AND $56.78
                                                                       kept, amended_by empty
    B  BURL's amendments under two different guessed instruments    -> 1 group, July 25 2030 governs
    C  Nike's two 364-day bases under ONE pointer family            -> 1 group, still named by the
                                                                       DOCUMENT, not the guess

*Real runs.* BURL re-assembled on the fix, exit 0: two headings, chain intact — "July 25, 2030 ·
Maturity Date means July 25, 2030 (amended from December 22, 2026)". AMZN re-assembled, exit 0:
four headings, all document titles, no withholding triggered.

*THE LIVE EXPOSURE IS ZERO, AND SAYING SO MATTERS MORE THAN THE FIX.* AMZN is the name whose two
364-day agreements collide, so its clean run prompted the right question: does the collapse ever
see both? Simulating the ACTUAL selection (`_core_agreement_exhibits`, capped at `_MAX_EXHIBITS`
= 4, round-robin by family) across the 24 names with pointers, **no name would have merged two
distinct contracts** — all five title collisions among extracted exhibits are legitimate chains
(BURL, NKE, PARR, UBER, WLK). The "5 of 11 groups carry >=2 bases" figure that justified blocking
the fleet pass was measured over ALL LOCATED exhibits, a wider population than the <=4 that reach
extraction. The block was precautionary, not necessary; #652's record carries an amendment saying
so, and this PR lifts it.

*Mutation — five, all caught, one survived first.* C1 (ambiguity check removed — #652's bug
restored), C2 (ambiguity ignores the family split), C3 (amendments counted as bases — BURL's chain
breaks), C4 (`is_amendment` case-insensitive), C5 (year stripped again). **C2 survived the first
round**: the pin asserted the group COUNT, and an over-firing withhold still yields one group for
a same-family pair — only the NAME changes. Strengthened to assert the group is named by the
document. Source restored byte-identical.

*A false positive caught by its own pin.* `is_amendment` first matched "No amendment to this
Agreement shall be effective" — an amendment CLAUSE inside a base contract's body, which would
have re-opened the merge from the other side. It is now heading-only and case-SENSITIVE: an
agreement heading is capitalised, running prose is not.

**BOUNDARY.** Measured 2026-09-28 on branch `fix/covenant-title-collision` off `f55eff4a`.
- *0 names would merge distinct contracts, 5 legitimate chains*: population = the 24 committed
  dossiers carrying covenant pointer rows with an accession; unit = names; the selection simulated
  is `_core_agreement_exhibits(pointers)[:_MAX_EXHIBITS]`, i.e. **<=4 exhibits per name**, which is
  what extraction actually sees.
- *3 titles withheld (AMZN x2, AORT)*: same 24 names but over the WIDER population of up to 3
  exhibits per pointer row (144 heads) — the set the reader was tuned on, NOT the set extraction
  sees. These two populations are not comparable and the difference is the whole point above.
- *0 titles carry a leading year*: same 144 heads. The year fix therefore changes nothing
  observable today and is closed as a latent case.
- *BURL 8 debt docs / 5 amendments / 0 withheld*: that name's located exhibits, same 144-head set.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **Where a title is withheld, the page shows the OLD guessed label.** That is deliberate — the
  pointer's guess is wrong-but-visible, the merge was wrong-and-silent — but it means #652's
  benefit does not reach those groups. *Falsifier:* a withheld group whose pointer family is
  demonstrably the wrong instrument, which is then published under it.
- **Same-family base pairs still collapse, and one of them may not be a renewal.** Nike's two
  364-day agreements are successive renewals, so latest-governs is right there; two genuinely
  distinct facilities filed under one pointer family would still merge. Not observed; accepted
  because splitting them would need an identifier this layer does not have.
- **`is_amendment` is heading-shaped.** A filer who sets the heading in title case and whose title
  does not reach `_AMEND_PREFIX` reads as a base document. The failure direction is safe — a base
  that is really an amendment makes a title look ambiguous and withholds it, falling back to the
  pointer — but it costs the merge. *Falsifier:* a known amendment chain that stops chaining.
- **The live-exposure measurement is of TODAY'S pointer sets.** Which exhibits reach extraction
  shifts as filings accumulate and as `_covenant_pointers` changes, so a collision that does not
  fire now can fire later. That is the reason to ship the guard despite zero live instances, and
  the reason the zero is a boundary, not a proof of safety.
- **NOT FIXED (unchanged from #652):** `render.py:1245`'s duplicated lead; the pointer layer's
  class-generic queries; CNXC "Other Loans" newly reaching a query; and the ancillary SECURITY
  AGREEMENT rendering as a governing family. All four are recorded in #652 or its review.
