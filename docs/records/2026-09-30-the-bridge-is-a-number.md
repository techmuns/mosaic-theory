---
id: 2026-09-30-the-bridge-is-a-number
status: shipped
date: 2026-09-30
prs: [660]
supersedes:
superseded-by:
---

# The bridge is a number, and the guard reads every leg

**WHAT.** The two findings review of #658 left unfixed, both of which meant the guard did not catch
the case it was built for.

1. **The bridge escape was a bare substring test that ordinary prose satisfied.** A window mismatch
   was excused when the leg's `reason` named both periods. Base reasons routinely name their own
   year, so it collapsed to *does the reason mention the window*. Verified on the branch before
   touching it — all three of these PASSED the merged guard:

       "Base leg strikes FY2027 revenue at the street median; entry is quoted on NTM terms."
       "Revenue 1,340 is the median FY2027 street forecast; NTM trends support it."
       "Entry is quoted on NTM; the leg strikes FY2027 and the roll between them is ~1.1x."

   Only the third bridges anything. The guard could not tell them apart — which is the
   escape-hatch-satisfied-by-legal-input failure `leg_fy_problems` was criticised for one function
   above, reproduced one function later by the code criticising it.

2. **It read only the `base` leg.** GOOGL's motivating sentence — *"Bear EPS EXCEEDS today's NTM
   $13.29, so the downside is multiple compression from ~26x"* — is in the BEAR leg, whose
   `leg_fy` is None. No configuration of a base-only guard could ever reach it.

**THE FIX IS A NUMBER.** `entry_denominator` — the EPS or EBITDA the entry multiple divides. A
mismatch is excused only by supplying it; there is no prose escape at all. Boilerplate cannot
produce a number, and it is the bridge the mismatch actually requires: with it the entry multiple
is `spot / entry_denominator`, the roll is `leg.eps / entry_denominator`, and the re-rating is what
remains. The guard now walks EVERY leg, and a leg that compares itself to the entry multiple while
stating no `leg_fy` is refused outright.

**WHY AN IMPRECISE PROSE DETECTOR IS SAFE HERE, AND THE ONE IT REPLACES WAS NOT.** `_ENTRY_CLAIM`
is a regex over leg prose, and it will both miss and over-fire. It is safe because it is used ONLY
to ADD a refusal: a miss leaves the status quo, and a false positive asks an analyst to state a
year the leg should be stating anyway. An escape hatch has the opposite asymmetry — every miss
lets a defect through — which is exactly how the prose bridge failed. Direction of failure is the
whole argument; the same regex in the other position would be the same bug.

**HOW VERIFIED.**

*The counter-examples, before and after.* The reviewer's sentence passed the merged guard and is
now refused; the same record with `entry_denominator` stated passes, because the gap is quantified.
GOOGL's bear-leg prose was invisible and is now caught by name.

*The decomposition, on the record that motivated the work.* With the entry NTM its own bear leg
names in prose ($13.29), GOOGL's base decomposes to:

    entry 25.53x (339.35 / 13.29)  ->  exit 24.50x on FY2026 EPS $16.221
    denominator roll +22.1%   multiple change -4.1%   total +17.1%

and the record's own base price $397.41 against spot $339.35 is +17.1%. The split multiplies back
to the return the record already implies, which is the test that it bought something: the field is
READ, not merely stored.

*Mutation — five, all caught.* G1 the prose bridge restored; G2 base-only scope; G3 the entry-claim
detector never firing; G4 `entry_denominator` serialising as null; G5 the decomposition ignoring
the entry multiple so the roll is counted twice. Source restored byte-identical.

*A break found by checking call sites rather than trusting the edit.* Replacing the region deleted
`entry_basis_problems`, which `scenario-create` calls — the create path would have raised
`AttributeError` on every run. Restored with the new rule, and create now carries
`entry_denominator` with an empty-never-proposed template cell beside `entry_basis`.

*A pin replaced, not adjusted.* `test_a_reason_naming_both_periods_bridges_them` asserted the
exact behaviour identified as gameable. A pin encoding a wrong contract reddens when the contract
is fixed; it was the pin that was wrong.

**BOUNDARY.** Measured 2026-09-30 off `4af45b59`. *All nine committed records round-trip
byte-identical* — population `scenarios/*.json` excluding `_`-prefixed files, unit records;
`scenarios/_schema.json` regenerates to carry the field and is the only committed artifact that
moves. *25.53x / +22.1% / −4.1% / +17.1%*: GOOGL's own `spot` 339.35, base leg EPS 16.221 at
24.5x, and the 13.29 its bear leg states — not a figure this repo sources independently.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **A mismatched record now needs a NUMBER, not a sentence.** That is more work at the write
  boundary and it is the point; the sentence was doing nothing. Records whose windows already
  agree are unaffected.
- **`entry_denominator` is analyst-supplied and unverified.** Nothing checks it against the price
  or the leg — a wrong number produces a wrong decomposition, confidently. It is the same trust
  the rest of the leg inputs carry. *Falsifier:* a decomposition whose total does not reproduce
  the record's own implied return, which the pin now checks for GOOGL.
- **`_ENTRY_CLAIM` will miss entry comparisons phrased in ways it does not match.** Accepted for
  the asymmetry argued above; every miss leaves exactly the behaviour that shipped before.
- **The decomposition is not rendered anywhere.** `basis_decomposition` is available and pinned,
  but no page shows it, so the return attribution a reviewer asked for is computable and not yet
  published.
- **`leg_fy_problems`' own dead branch is STILL unfixed** (its refusal needs a blank `reason`,
  which the validator forbids). This record fixes the guard that copied it, not the original.
