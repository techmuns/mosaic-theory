---
id:
status: open
date: 2026-11-10
prs: [966]
supersedes:
superseded-by:
---

# A going-concern denial, hypothetical or alleviated doubt is not doubt, and a real conclusion is (TeamNostra fix request 2: RE2-D9, RE2-D10). Two live filings move from doubt to none; no committed page moves

**WHAT.** `vinci/edgar/going_concern.find_going_concern_statement` feeds a page's
`substantial_doubt` and the ranker's structural demote.

- **RE2-D9: not doubt.** Four forms now deny or condition the doubt:
  - **a doubt that "does not exist"** ("concluded that substantial doubt about … does not exist")
    is a denial;
  - **plans that "alleviate" it, present tense,** state it alleviated, as "alleviated" did. A
    purpose ("to alleviate"), a modal ("will / may / could alleviate") and a "cannot alleviate"
    still leave the doubt standing;
  - **an alleviation is unsettled only by what precedes it, or by its own clause.** A later clause
    is another statement: "…have alleviated the substantial doubt …, and the Company does not
    expect to need additional financing" had been read as doubt because of that "not";
  - **"there will (would, may, might, could) be substantial doubt"** is a hypothetical.
- **RE2-D9, at the filing level.** A filing whose own plans alleviate the doubt its conditions
  raised states none. That is ASC 205-40's alleviated outcome, which is not a doubt conclusion.
- **RE2-D10: doubt.** Three forms are now read as conclusions:
  - a frame's own sentence that concludes with the verb after the doubt ("determined that
    substantial doubt about … exists");
  - a frame's own sentence that concludes with the company having it ("determined that the
    Company has substantial doubt");
  - a sentence with a "no" four words back. That "no" now governs only the words up to a
    conjunction, so "The Company has no revenue and recurring losses raise substantial doubt"
    denies nothing.

**WHY.**
- **TeamNostra's re-audit (document 14, E2-D9 and E2-D10) misread 7 of 9 constructed sentences.**
  On the page that sets `substantial_doubt: true`, and the ranker sinks the name.
- **The filing-level case is live on real filings:**
  - **Solo Brands' 10-Q `0001870600-26-000044`** says its conditions "raise substantial doubt"
    and then "These plans alleviate the substantial doubt …". Main quoted the alleviation as the
    doubt.
  - **Aeluma's 10-K `0001213900-25-086227`** says "As previously disclosed, we had expressed
    substantial doubt", then that the doubt "has been alleviated for at least the next twelve
    months". Main quoted the past "had expressed" as the doubt.

**HOW VERIFIED.**
- **Fail first.** `tests/test_going_concern_denials_and_conclusions.py` was run in an export of
  `origin/main` `9da0d096`: 9 of 16 fail and the 7 negative pins pass. The 9 are TeamNostra's 7
  constructed sentences plus Solo Brands and Aeluma. The negative pins are "plans to alleviate",
  "not alleviated", "no assurance", "cannot alleviate", "do not raise", "no conditions or events"
  and the frame alone.
- **The existing precision pins** (`tests/test_going_concern_precision.py`, the corpus the rules
  were grown from) all pass.
- **CORPUS FIRST: `scripts/going_concern_flips.py --ref origin/main`, the repo's own measure.** It
  ran over three SEC caches: the primary checkout's (109 filings mentioning a going concern),
  another worktree's (64) and this session's fetched cache (5). The caches overlap.
  - **Two filings move, both from doubt to none, both alleviated:** Aeluma, in two caches, and
    Solo Brands.
  - **0 move from none to doubt**, and no quoted sentence moves elsewhere. The rest of each
    cache's 22 doubt verdicts stand.
- **Real instances of the sentence-level shapes, by EDGAR full-text search** (paced client):
  - "there will be substantial doubt" has 4 hits, including Heron Therapeutics' 10-Q (its document
    did not resolve at the listed path);
  - "plans alleviate the substantial doubt" has 57 hits, Solo Brands among them.
- **The $0 replay of the 27 committed pages:** the cited 10-Q's going-concern field moves on none.
  MVST still states doubt.
- **Code review, round 0 (`/code-review high --fix`).** Five defects fixed, each with a constructed
  pin that fails on the first commit:
  - an alleviation settles only the doubt stated BEFORE it. One cleared the whole filing, so a
    later, separate doubt was dropped;
  - a modal or "won't" anywhere before an alleviation unsettles it (`_UNSETTLED`). Before, only a
    modal directly in front of the verb did;
  - a widened conclusion refuses a verb preceded by "not" or "longer" ("does not have substantial
    doubt" had become doubt);
  - "until", "unless" or "assurance" in a later clause still unsettles an alleviation;
  - "or" no longer blocks a denial ("do not individually or collectively raise").

  After the fixes the corpus measure is identical, and 0 reads move against the first commit.
  Deferred: a "does not exist" up to 200 characters on may deny a real doubt (under-flagging, the
  module's stated bias, with no corpus case), and an alleviation that cites ASC 205-40 is still
  skipped as a frame before the filing-level rule sees it.
- **The module docstring** records the exception to "every marker was demanded by a real filing":
  these markers came from TeamNostra's constructed sentences, two of them live.
- **The version.** Row `2026-11-10.going-concern-denials-and-conclusions`, in both tables,
  re-pinned.

**BOUNDARY.**
- **Pages:** `data/dossiers/*/dossier.json` at `9da0d096`, one cited 10-Q each.
- **Corpus:** every `sec`-namespace cache entry whose URL is an EDGAR Archives document and whose
  text says "going concern". That is 178 reads across the three caches, not deduplicated.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **An alleviation settles the doubt stated before it, never one stated after.** So a filing that
  states a current doubt and THEN recounts last year's alleviation would read as none.
  *Falsifier:* a filing whose doubt conclusion precedes an unrelated, unsettled "alleviated"
  sentence. None appears in the corpus above.
- **An absent going-concern statement still writes no flag** (document 14's note on
  `filing_sections.py:496-505`). The digest's "none stated (checked, absent)" state is unreachable:
  `_going_concern` returns a statement or None. Recorded, not changed: that line is the synthesis
  digest's.
