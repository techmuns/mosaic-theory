---
id:
status: shipped
date: 2026-10-18
prs: [748]
supersedes:
superseded-by:
---

# A tenor in front of an agreement's name is part of the name — "364 DAY" keeps its 364

**WHAT.** `vinci/dossier/covenant_extract.py` `_LEAD_CODE` no longer strips a number followed by
DAY / WEEK / MONTH / YEAR(S). It strips the leading codes in front of a covenant agreement's
self-declared title, and its numeric branch, written for amount fragments such as "000" (left from
"$1,000"), also took the tenor of a facility named with a space:
- TJX's 2020 facility (`exhibit101364dayrevolv.htm`, 8-K 0000109198-20-000015) heads itself
  "364 DAY REVOLVING CREDIT AGREEMENT", and its first page (#747) published it as **"DAY REVOLVING
  CREDIT AGREEMENT"**.
- A hyphenated tenor ("364-DAY", "FIVE-YEAR") was already protected; a spaced one was not.
- Amount fragments, CUSIPs, filing ids and the year guard behave exactly as before.

**WHY.** The heading names the contract. A label that drops the tenor reads as a different, unnamed
facility, and it groups covenant rows under a title the document never used. Only the label was
wrong; the extracted terms were not affected. STATE §5.0 row 32 (10), opened by #747, is this.

**HOW VERIFIED.**
- **On the whole EDGAR cache, through production's own `html_to_text`:**
  - 5,682 cached exhibit documents; 114 carry an agreement title under the current code;
  - 7 captured titles start with a bare number: six amount fragments ("000 …" ×5, EPAM's
    "00 …"), still stripped, and TJX's "364 DAY …";
  - **exactly one title changes**: TJX's, "DAY REVOLVING CREDIT AGREEMENT" → "364 DAY REVOLVING
    CREDIT AGREEMENT".
- **Pins:**
  - **`test_a_day_count_before_the_title_is_part_of_the_name`, on TJX's real head.** It is
    byte-for-byte from the fetched exhibit through `html_to_text`.
    - **Kept:** the spaced tenor, and a tenor behind a CUSIP.
    - **Still stripped:** "000" and EPAM's "00".
    - **Unchanged:** the hyphenated "364-DAY", and WERN's real filing ids.
  - **`test_no_published_covenant_heading_lost_its_day_count`, end to end on the committed pages.**
    No covenant heading may begin with a bare duration word. It finds nothing on `main`, where TJX's
    page is not yet committed. **Shown to fire on the real page:** with #747's `TJX.md` placed in
    `frontend/dossiers/`, it fails naming `TJX.md: DAY REVOLVING CREDIT AGREEMENT`; the copy was
    removed.
- **Mutation:** restoring the old pattern fails the unit pin.
- **Suite:** see the PR.

**BOUNDARY.** "The EDGAR cache" is `data/cache/sec/*.json` in the shared data copy on 2026-10-18,
filtered to EDGAR archive documents (`.htm`/`.html`/`.txt`). "Titled" means `agreement_title`
returned a value. The before/after comparison ran the same documents through the old and new
patterns.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **TJX's page must be re-assembled on this code to carry the corrected heading.** It is not on
  `main` yet (#747). That pass, rebuilt after this merges, drops row 32 (10). Merged in the other
  order, the new end-to-end pin would be red until TJX is re-assembled.
- **The title keeps the document's own spelling, "364 DAY",** rather than a normalised "364-DAY": the
  heading is quoted, not rewritten. If one facility were ever headed both ways across its
  amendments, the two spellings would group separately. That case is not checked here.
