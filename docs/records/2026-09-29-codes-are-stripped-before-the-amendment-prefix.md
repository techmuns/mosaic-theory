---
id: 2026-09-29-codes-are-stripped-before-the-amendment-prefix
status: shipped
date: 2026-09-29
prs: [655]
supersedes:
superseded-by:
---

# A filing id in front of the title hid the amendment prefix

**WHAT.** `agreement_title` (#652, refined in #653) stripped a leading filing id AFTER trying to
strip the amendment prefix. `_AMEND_PREFIX` is anchored at `^`, so while the id is still in front
it cannot match, and the amendment INSTANCE survives normalisation. The fix swaps the two: codes
first, then the prefix. One line, plus the comment saying why the order is load-bearing.

WERN is the real case. Its Amendment No. 3 head begins

    20260605EX101 1758963679 24780046 AMENDMENT NO. 3 TO LOAN AND SECURITY AGREEMENT

and the page published under exactly that string — a filing id rendered as a contract name. Worse
than the cosmetics: the un-normalised title did not match the base contract's title, so the
amendment became a SECOND governing group beside `LOAN AND SECURITY AGREEMENT` instead of
collapsing into it. That is the merge failure #653's normalisation exists to prevent, arriving
through the back door of an ordering bug.

**WHY.** The defect was mine, shipped in #653 and found by the fleet pass that #653 unblocked —
the first artifact pass to run WERN through the new reader. It is the reason the pass is worth
running before trusting the code: 144 cached exhibit heads had tuned the reader, and none of them
carried a filing id ahead of the title in the shape WERN's does.

**HOW VERIFIED.** The three shapes, through the shipped function:

    20260605EX101 1758963679 24780046 AMENDMENT NO. 3 TO LOAN AND SECURITY AGREEMENT
        -> LOAN AND SECURITY AGREEMENT
    Deal CUSIP Number: 02313HAF7 AMENDED AND RESTATED CREDIT AGREEMENT Dated as of
        -> AMENDED AND RESTATED CREDIT AGREEMENT          (the case the OLD order protected)
    Exhibit 10.1 EXECUTION VERSION SIXTH AMENDMENT TO SECOND AMENDED AND RESTATED CREDIT AGREEMENT
        -> SECOND AMENDED AND RESTATED CREDIT AGREEMENT   (BURL's chain, unchanged)

The second is the one that makes the swap non-trivial: `_LEAD_CODE`'s alphanumeric branch would eat
"AMENDED" outright were it not for the digit guard added in #652, so running it FIRST is only safe
because that guard holds. Its pin is kept and a second added for it here.

*Mutation.* O1 — the order reverted — is CAUGHT by
`test_a_filing_id_in_front_does_not_hide_the_amendment_prefix`. Source restored byte-identical.

**BOUNDARY.** Measured 2026-09-29 off `e0287341`. **One name affected across the fleet**: scanning
every `- **Covenants — …**` heading in `frontend/dossiers/*.md` after the 11-name pass, WERN is the
only heading carrying an un-normalised prefix. The other digit-leading headings are either correct
document titles (`364-DAY CREDIT AGREEMENT`, `364-DAY REVOLVING CREDIT AGREEMENT`) or pointer
families on names not re-assembled (`2025/2028/2029 Convertible Notes`, `24 Credit Agreement`).
Population: the 26 committed dossiers; unit: rendered covenant headings.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **WERN's committed page still carries the defect until it is re-assembled.** The code closes
  here; the page closes on the next artifact pass, which is queued behind this.
- **The reader is still tuned on a 144-head sample.** This bug existed in that sample's blind spot
  — no cached head had a filing id ahead of the title in WERN's shape — and the next unfamiliar
  head shape can do the same. *Falsifier:* another heading that renders an id, a date or a docket
  number as a contract name.
- **NOT FIXED (unchanged):** `render.py:1245`'s duplicated lead; the pointer layer's class-generic
  queries; CNXC "Other Loans"; the ancillary SECURITY AGREEMENT rendering as a governing family.
