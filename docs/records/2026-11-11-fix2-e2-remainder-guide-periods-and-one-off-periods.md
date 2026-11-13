---
id:
status: shipped
date: 2026-11-11
prs: [1027]
supersedes:
superseded-by:
---

# Every guide filed under the next-fy default now reads the period its release states, a one-off item carries its period, a component inside a figure is not its lead, and a filing read with no going-concern doubt is CHECKED-ABSENT (TeamNostra fix request 2: RE2-D20's remainder, RE2-D17, and the residuals of RE2-D6 and RE2-D10) — built 27 of 27 at $0 on 2026-11-11 and 25 of 25 on 2026-11-13 (MVST retired; PARR's CIQ export refused); every built page's request moves at re-assembly, so a panel check is owed

**WHAT.**
- **RE2-D20, the rest** (`vinci/edgar/release_parse`). #976 flagged each guide filed under the
  `next-fy` default. There were 21 on the 27 committed pages, and each sat where its release states
  the period. Five readings now find it:
  - **A header glued to the previous list's last bullet** heads its own list (`_GLUED_HEADER`): a
    trailing run of capitalised words, years and footnote marks ending in Outlook, Guidance or
    Expectations and a colon. "• Adjusted EBITDA (3) of $55.5 million versus $68.0 million
    Updating Fiscal Year 2026 (4) Outlook: •" covers 12 SMPL guides.
  - **A list item's tail ending ";" is never a header** (`_list_header`). BURL's capex bullet
    holds "The timing and amount of such relocation expenditures are still uncertain;".
  - **A header that says what its outlook rests on.** A year-to-date or relative phrase that
    reaches "results" through its own year is the reported basis (`_YEAR_RESULTS_AFTER`). A header
    naming several periods is read at the clause its ONE forward VERB opens (two give no answer), cut at the first
    comma (`_named_period`), with the header's one year added where that clause names none. This
    covers 5 VRRM guides and 1 EPAM guide. A clause naming a quarter gives the quarter, so a
    quarterly list never reads as annual.
  - **A guide joined by "and" straight after its partner's range** takes the partner's period
    (`_partner_period`): VITL's headline.
  - **"full year" in the guide's own clause is FY:** SMPL's prose outlook.
  - The last two run only in place of the default.
- **RE2-D17: a one-off carries its period** (`OneOffItem.period`, in `schemas.py` with the
  operator's approval through the decision-path guard; `release_parse._one_off_period`).
  - **How it is read:** from the item's own words first, as a quarter or year through
    `_figure_period`; a year-to-date span in the release's words; a bare year as the year. Then
    the reader an actual's period goes through, as a current item. None stays None.
  - **When unset, the field is absent,** so every committed item round-trips byte-identically.
  - **The synthesis digest states it:** "one-off charge (Q2 2026): …", or "(period not read)".
  - **The gap-driver line states it:** "$11.3M inventory-related charge (Q2 2026)".
  - **The full-year impairment numerator** (`_fy_impairment`) passes over a quarter's or a
    year-to-date item, and (since 2026-11-13) one whose period was not read: it never falls
    through to an unread item. MVST's real Q3 2026 release showed why (THE 2026-11-13 RE-RUN,
    below).

- **RE2-D6's residual** (`release_parse._lead`). An amount introduced as a component ("including
  an SRE impact of $195.9 million") is not the clause's lead when a figure precedes it. So Par
  Pacific's "Adjusted Net Loss of $(5.5) million in the third quarter of 2024" is read, signed, not
  set aside silently by `_sub_unit`. A component with no figure before it is still the lead, so the
  sub-unit and quarter-against-a-year refusals hold (review).
- **RE2-D10's other half** (`filing_sections._going_concern`). A filing whose notes were read and
  that states no doubt returns the CHECKED-ABSENT state (no doubt, no verbatim, bound to the
  filing), never None. Text with no notes heading still makes no claim. "Read" means the notes'
  HEADING followed by notes with body text (`_notes_heading`, since the pre-draw review below):
  never a sentence that names the notes, and never a contents entry.

**WHY.**
- **RE2-D20.** A default that hides an absence is what the audit asked to stop. #976 shipped the
  flag, and these readings remove the absence itself where the text has the answer.
- **The headers,** once found, already read correctly (SMPL "Fiscal 2026", BURL "Fiscal 2026").
  13 of the 21 were `_list_header` returning the wrong header, not a period-reading gap.
- **RE2-D17.** BRBR's third-quarter release carries "an $11.3 million inventory-related charge
  recorded in the second quarter", VRRM's a six-month impairment, and LLY's a prior-year charge.
  All were stored, and digested for the synthesis, exactly as the quarter's. `_fy_impairment` took
  LLY's prior-year Q1 charge and VRRM's six-month one as full-year numerators.

- **RE2-D6.** #962 named it and left it: the SRE impact was taken for the current figure, so the
  comparison read as a sub-unit's.
- **RE2-D10.** A filing read in full with no doubt statement and a filing never read gave the same
  None. So the digest's "none stated (checked, absent)" and the Brief's "not flagged" could never
  print, and a reader that missed a real conclusion looked exactly like one that found none.

**HOW VERIFIED.**
- **Fail first** (the full $0 build's own run, head's tests on base code `7edbfa36` and head
  `73619437`): **23 of 93 tests fail on base and pass on head**, and 0 fail at head. They cover
  every RE2-D20 shape on real EX-99.1 text, every RE2-D17 reading, RE2-D6 on Par Pacific's real 8-K
  and RE2-D10 on TECX's real 10-Q, the review's pins, and the two moved existing pins:
  - `test_guidance_fix2_e2.py::test_re2_d20_verra_mobility_header_period_is_read` (#976's
    partial-state pin);
  - `test_guidance_opener_period.py::test_a_quarter_opener_never_labels_a_full_year_range`, now "FY"
    and still never Q3.
- **The full $0 build** (`python -m vinci.impact run --base 7edbfa36 --head 73619437`). Every
  committed page was built with each side's code from the same inputs.
  - **Store:** a read-only master, sha256 `4e77757f5cb370050ab9b43c450053379e8d20c0f605d4d4213b9e152e6a8e9d`,
    snapshotted fresh per build. 0 responses fetched live.
  - **Built 27 of 27; 27 of 27 pages move, with 115 field changes.** These are:
    - the going-concern read on 26 pages (MVST keeps its doubt);
    - 37 guide items on BURL, EPAM, SMPL, VITL and VRRM, with the default flags gone;
    - 22 of 23 one-offs on 7 pages;
    - BURL's `valuation.adjusted_eps` and `current_guide` lines, SMPL's and VITL's
      `disclosure_gaps` basis, and MVST's driver line, each now printing the period.
  - **Requests:** 27 of 27 differ. The system prompt and tool schema are unchanged, and the
    frozen-panel replay differs on LLY and SMPL.
  - **Readers:** the decision ledger, scoring report and monitor are identical at both refs. The
    committed pages re-render identically, and only `snapshots/extraction_versions.json` differs in
    `frontend/`.
- **The cited-release replay** (`replay_pages.py`, the committed pages' 122 cited EX-99.1s and 27
  10-Qs, base vs head, 0 misses):
  - **Guides:** 27 of 141 move, being the 21 defaults read (BURL 1, EPAM 1, SMPL 13, VITL 1, VRRM 5)
    and 6 labels made specific in scope.
  - **Default flags:** 21 → 0.
  - **One-offs:** 19 of 19 dated. IT's was checked against its own table ("—" for the quarter, 155
    for the year).
  - **Actuals:** 1 added, PARR's Q3 2024 -5.5. PARR's $0 build today reads a newer release set, so
    that row reaches no page now.
  - **`_fy_impairment`:** moves on LLY (35.0 → None) and VRRM (64.0 → None). Neither page prints
    the margin line it feeds. The full build's own release set moved a third, MVST's, which does
    print it; this list missed it (THE 2026-11-13 RE-RUN, below).

- **The third review's two fixes, after the full build:**
  - a lowercase quarter header ("Fourth quarter 2026 Outlook:") keeps its quarter, because a clean
    sentence-final tail is tried before the glued run;
  - "excluding special items, Adjusted Net Income of …" is the figure, not a component, because a
    component's reach stops at a comma.

  Each is pinned and fails first on the code before it. **They move 0 fields** on the 122 cited
  exhibits, and 0 on the full build's own release set (122 exhibits, 0 misses, pre-fix vs fixed).
  So the full build's numbers above hold for the final code.

**THE 2026-11-13 RE-RUN AND THE UNREAD-IMPAIRMENT FIX.**
- **What the cross-setup check found** (`vinci.impact run`, base main `dad8f441`, head `bf1cfeb8`,
  26 of 27 pages built, PARR refused at both refs by its mislabelled CIQ export): every move
  matched this record except MVST's margin line in `basis_triangulation`, "impairment-excluded
  32.4% (… 16.3/427.5)" at base and "37.0% (… 35.8/427.5)" at head.
  - `_fy_impairment` passed over the Q3 2026 release's $16.3M impairment, read as Q3 2026. It
    then took the next impairment in the same release (8-K `0001628280-26-072310`): a $35.8M one
    that the release states in its year-to-date paragraph and that the reader left unplaced.
  - "Taken as before", that nine-month figure stood as the full year's. The 2025 release's $32.5M,
    read as 2025, was never reached.
  - The 2026-11-11 full build had moved the same field; its readers list above named only LLY and
    VRRM.
- **The fix** (coordinator, 2026-11-13: fix it here, never accept it while the cheap fix exists):
  `_fy_impairment` passes over an impairment whose period was not read, as it passes over one read
  as a quarter. Then MVST reads its 2025 item, $32.5M.
- **Pinned on the real text:** `tests/fixtures/fy_impairment/mvst_releases.json` holds both EX-99.1s,
  decoded as `mechanical` decodes an exhibit (`normalize_text(html_to_text(…))`) and cut to the
  headline and the impairment sentences. Each cut emits exactly its full filing's impairment items
  (Q3 2026: 16.3 as Q3 2026 and 35.8 unread; FY2025: 32.5 as 2025).
  - `test_re2_d17_an_unread_impairment_is_never_the_full_years_mvst` fails first on `53385f9f`'s
    `mechanical.py`.
  - `test_re2_d17_neg_an_impairment_read_as_the_year_is_still_used_mvst` passes on both.
  - The constructed pin `test_re2_d17_the_full_year_impairment_is_never_a_quarters` moves on
    purpose: an unread item now gives None, not 32.5.
- **Reach on the corpus:** MVST was the only page with an unread impairment: 22 of 23 one-offs carried a
  period on the 26 pages built at `bf1cfeb8`, and the 23rd was MVST's $35.8M. MVST is retired
  (#1044, `12764514`), so its page is gone from the corpus. No committed page prints the margin
  line, which prints only with the year's gross margin, the impairment and the revenue together
  (`primary_source.basis_triangulation`).
  - A refresh compares `_fy_impairment` on the committed rows with the re-read ones, and rebuilds the
    release lines where they differ, after proving the old lines reproduce from the old rows.
  - The committed rows carry no period, so the fixed code reads None on all four pages holding an
    impairment: IT, LLY, SMPL and VRRM. Which of them a refresh rebuilds therefore changes.
  - None of the four pages' committed rows carries the year's gross margin or revenue, so the
    margin line cannot print on either side, and that proof is unaffected (measured on the 26
    committed pages at `14a57fc5`).

- **The re-run on the fix** (`vinci.impact run --base origin/main --head 32f4d6a4`, base main
  `12764514`, $0, 653.9 s; the same store copy, `--ciq-root`, `--cache-root` and `--env-file` as
  the run above; 0 responses fetched live):
  - **Fail first:** 28 of 142 nodes fail on base code and pass on head; 0 fail at head.
  - **Pages:** 25 of 26 built (PARR refused at both refs, its CIQ export); 25 of 25 move, with 103
    field changes. These are the `bf1cfeb8` run's 110 less MVST's seven, row for row: the fix moves
    no field on the pages built.
  - **Requests:** 25 of 25 differ, the system prompt and tool schema the same on all. The six panel
    pages differ, and row 53's check is OWED.
  - **Readers:** the decision ledger, scoring report and monitor are identical at both refs.
- **The panel captures** for `register --from-impact` (the six panel pages, base `12764514` and
  head `32f4d6a4`) are outside the repo, because requests carry licensed transcript text.
  - Each arm has `request.json`, `layer.json` and `built.json`, plus the manifest (sha256
    `d5afead0728903a0b582fff12d2dc63faf66911d0c76fbd6ddfe080e696cef66`).
  - All 12 arms have `recapture_equal` true: the five calls are identical, a re-capture from the
    built page equals the run's request, and a re-capture from `layer.json` equals it byte for byte.
  - A $0 dry check from a checkout of main read the export, the fixed scorer and the 12 layers.
    0 of its 12 request pins were drawn before.
- **The panel's expected cost: $29.40; plus 20%, $35.28.**
  - Inputs: each panel request's size at fix 3b's tokens per character for that page, and each
    page's mean output per draw over the five kept 60-draw ledgers.
  - Prices: `LLM_PRICE_PER_MTOK`, with each of the 12 page-arms writing its own cache.
  - The eight recorded 60-draw runs average $29.15.
- **The cap, ruled by the operator on 2026-11-13, verbatim:** "Estimate +20%, max $40
  (Recommended)". That is $35.28. Nothing is registered or drawn until the operator approves the
  #1004 note.

**THE PRE-DRAW REVIEW (2026-11-13) AND ITS FOUR FIXES.** The coordinator's independent review
at `23ff180c` (code identical to `32f4d6a4`) said FIX FIRST. Each fix is pinned on real SEC text
(`tests/fixtures/e2_review/real_text_cuts.json`, cut through the production decode path) in
`tests/test_e2_review_basis_notes_ytd.py`. Seven positive pins fail on `32f4d6a4` and two negatives
pass on both.
1. **A period inside a header's "Based on …" clause is the outlook's basis** (`_BASIS_CLAUSE` in
   `_named_period`). Verra Mobility's Q3 2025 header (8-K `0001193125-25-256337`) reads "Based on our
   year-to-date 2025 results and our outlook for the fourth quarter, we are increasing revenue
   guidance as follows …". The basis-year skip dropped "year-to-date 2025" and left "the fourth
   quarter" as the only period, so revenue, adjusted EBITDA and adjusted EPS, all full-year guides,
   read Q4 with their default flag removed. That was a fabricated period. They now stay on the
   flagged default.
   - The section's title ("2025 Full Year Guidance") sits sentences earlier, and the reader does not
     have it cleanly, so it is not read.
   - Verra Mobility's 2026 headers still read 2026, because their own clauses name the year.
2. **CHECKED-ABSENT needs the notes' heading** (`_notes_heading`, in place of a title matched
   anywhere). A heading here is:
   - a capitalised title, not preceded by a word that makes it a reference ("See Notes to …");
   - followed within 300 characters by its first note, with no page number between;
   - followed by notes carrying body text, not an index's page numbers.
   It reads the forms the cited 10-Qs use, among them Lilly's "Notes to Consolidated Condensed
   Financial Statements", McKesson's "FINANCIAL NOTES" and Vital Farms' HTML-split "CONSOLID ATED".
   - **Before:** a cover-and-contents cut of TECX's 10-Q read CHECKED-ABSENT, as did every cited
     10-Q cut 200 characters past its contents entry. Lilly's and McKesson's only match was an ASU
     2024-03 sentence.
   - **Now, on the 26 cited 10-Qs** (the 25 built pages' and PARR's): every one reads CHECKED-ABSENT
     from its body heading. Every cut 200 characters past its contents entry makes no claim, except
     WLK, whose first match is its body heading itself. The earlier comment's "all 27 cited 10-Qs
     carry one" is replaced: what was matched was a phrase.
3. **An item after a year-to-date comparison sentence, its own sentence silent, is unread**
   (`_after_a_year_to_date_sentence`). Microvast's $11.1M write-down ("… from 36.6% in YTD 2025.
   This change was primarily attributable to …") was filed as Q3 2026, RE2-D17's own failure shape.
   The quarter's $9.3M ("… in Q3 2025. This change …") stays Q3 2026.
4. **The release's own year in a Q1–Q3 release is unread**, never its full year. There is no case on
   the corpus; the pin is Gartner's real footnote shape moved into a second-quarter release.
- **The replay** (every cached EX-99.x exhibit, parsed at `32f4d6a4` and at the fix):
  - 164 exhibits under 30 CIKs, 0 errors.
  - **2 move:** Verra Mobility's Q3 2025 release (three guides Q4 → `next-fy`, default flags 0 → 3)
    and Microvast's Q3 2026 release (the $11.1M, Q3 2026 → unread).
  - No panel page's exhibit moves, and every panel page reads CHECKED-ABSENT from the same 10-Q, so
    their requests are expected byte-identical.
- **Also from the review:**
  - The titles' 27 of 27 are corrected to the run's 25 of 25.
  - `OneOffItem.model_json_schema(mode="serialization")` is `{}` because of the wrap serializer,
    while the validation schema carries `period`. No consumer reads it: `vinci/scenarios.py`
    references no `OneOffItem`, and the one `MechanicalLayer.model_json_schema()` call
    (`tests/test_untraceable_rank_and_duration.py`) uses the validation mode. So it is stated here,
    not changed in `schemas.py`.

**THE RE-RUN ON THE REVIEW'S FIXES (2026-11-13).** The fixes are commit `6f405ebb`, and main
`0d8a2a43` (#1048, #1050) is merged as `880435fc`: the one conflict was `synthesis.py`'s drift pin
(rule A), and #1050's figure-trace hunks are reached from `synthesize` only through `_validate`,
on the chosen draw after the model calls.
- **The gate:** `bin/commit` green on `6f405ebb`: 11,215 passed, 660 skipped, 11 xfailed, 0
  failed, counted from every progress line, a line split by a test's print included.
- **Section D:** `vinci.impact run --base origin/main --head 880435fc`, base `0d8a2a43`, $0, with
  the same store copy and flags as the runs above, and 0 responses fetched live.
  - **Fail first:** 34 of 151 nodes fail on main's code and pass on head; 0 fail at head.
  - **Pages:** 25 of 26 built (PARR refused). The 103 field changes are value for value those of
    the `32f4d6a4` run, so the review's four fixes move no field on the pages built.
  - **Requests:** 25 of 25 differ, with the same page lines.
  - **Readers:** the decision ledger, scoring report and monitor are identical.
  - **Still valid:** `verify` says VALID after main moved to `9fcd4a74`, which touches only
    `docs/`.
- **The panel captures, re-made** from that run (base `0d8a2a43`, head `880435fc`): manifest
  sha256 `392b5e980a8b480ef1cb5a47e73b3f1869179f55e99012d8302052ea6b9041bd`. All 12 arms are
  recapture-equal.
  - **All 12 request pins are byte-identical** to manifest `d5afead0…`'s, base and head arms
    alike, `request.json` bytes included, and every `layer.json` is identical.
  - `built.json` differs only in the build clock (`assembled_at`, `anchor.computed_at`), a
    caveat's fetch time and `extraction_version`.
  - A $0 dry check from a checkout of main `9fcd4a74` passes: export read, fixed scorer, 0 of 12
    pins drawn before, 12 layers validate.
- **The cost:** the requests are unchanged, so it is unchanged: $29.40 expected, $35.28 with 20%.
  The cap is $35.28 under the operator's ruling, "Estimate +20%, max $40 (Recommended)".

**BOUNDARY.**
- **Pages:** the 27 committed pages at `7edbfa36`.
- **Exhibits:** their 122 cited EX-99.1s and 27 cited 10-Qs (the replay); each page's own $0-build
  inputs (the full build, 12,672 responses).
- **Store:** the master named above.
- **Unit:** one leaf field, one guide item, one one-off item, or one `qa_flags` line.
- **Date:** 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No committed page moves in this PR.** The new readings reach a page at its next assembly or
  release refresh.
- **The synthesis request moves then on every page built,** all six panel pages included: 27 of 27
  on 2026-11-11 and 25 of 25 on 2026-11-13. Every page without a stated doubt gains the
  checked-absent going-concern line (26 then, 25 now), and the rest of the moved lines differ only by
  a period label. **A six-page panel check is owed before merge,** and is not drawn.
- **The Brief gains "Going concern: not flagged" at re-assembly** on those pages, 25 on 2026-11-13.
  That is a state the renderer and `dossier.js` already print.
- **`compare` replays the committed layer**, so it cannot see this change. The paid check registers
  from an impact export of fresh builds instead (`register --from-impact`, fix request 2 order 8,
  #1030), which needs no transform.
- **The year-to-date one-off label is the release's words, not a code.** No consumer parses it,
  and `_fy_impairment` treats any non-annual label as not the year.
- *Falsifier:* a release whose header the new readings label with a period its text does not
  state. The replay shows none on the 122.
