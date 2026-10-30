---
id: 2026-10-30-a-going-concern-statement-is-read-as-stated
status: shipped
date: 2026-10-30
prs: [879]
supersedes:
superseded-by:
---

# A going-concern statement is read as stated: a denial, a hypothetical and the frame are not doubt, and a conclusion that cites ASC 205-40 is (audit E2-D17)

**WHAT.** `vinci/edgar/going_concern.find_going_concern_statement` is the one detector behind the
ranker's structural demote (`rank/structural.py`) and the dossier's filing reader
(`filing_sections`). It misread both directions:
- **"Management concluded that there is no substantial doubt…" read DOUBT.** Only "do not RAISE
  substantial doubt" was read as a denial.
- **"In accordance with ASC 205-40, management has concluded that these conditions raise
  substantial doubt…" read None.** Any sentence citing the standard was skipped as the
  evaluation frame.

Each rule below answers a real sentence it misread (the filer and accession are in
`tests/test_going_concern_precision.py`):
- **The frame is the QUESTION or the POLICY, never a citation.**
  - It is the "evaluates / considers / concludes / determines WHETHER" sentence, or "required to
    make certain additional disclosures if…".
  - Citing ASU 2014-15 or ASC 205-40 no longer makes a sentence a frame: Wolfspeed's 10-Q
    concludes doubt "in accordance with the requirements of ASC 205-40".
  - A frame sentence that states its own conclusion OF DOUBT is read as a conclusion. CRVS's
    "evaluated whether … and concluded that our existing cash … are sufficient" stays a frame.
- **A denial names the doubt it denies:** "no longer substantial doubt" (EOSE), "no substantial
  doubt" (PHAT), "does not believe that substantial doubt exists" (ACRS), "no material
  uncertainty exists" (MAR), and a doubt that "has been alleviated".
- **"Alleviate" denies the doubt only when no negator governs it.** "Management's plans
  alleviated substantial doubt" (RLMD's 2025 10-K) is a denial. "The management plan cannot
  alleviate the substantial doubt" (a 20-F) is doubt, and read None before.
- **A hypothetical needs its modal on the doubt itself:**
  - "could raise substantial doubt" (ZURA);
  - "may conclude that there is substantial doubt" (MNLK);
  - "substantial doubt could exist";
  - "may also contain statements expressing substantial doubt";
  - "If … there remains substantial doubt".

  Real conclusions stay doubt. SOCC's "…, if at all, substantial doubt exists" is doubt: the comma
  ends the conditional. SANA's "may not be sufficient …, and there is substantial doubt" is doubt:
  the modal is not on the doubt.
- **Version.** Extraction version `2026-10-30.E2-D17` (Python and dossier.js), re-pinned.

**WHY.** The demote is demote-only and the module says so: an ambiguous mention is NOT doubt. A
denial, a risk factor's hypothetical and the assessment question are not ambiguous. They state
that there is no doubt, or that there might one day be. The citation rule was the opposite error:
it hid a real conclusion because of the standard it named.

**HOW VERIFIED.**
- *Fails first on main* (08948b5a). 17 cases in `tests/test_going_concern_precision.py` fail on
  main and pass here:
  - 7 denials;
  - 2 hypotheticals;
  - 3 frames;
  - 4 conclusions that cite the standard or cannot alleviate;
  - the brief's two sentences.

  The negative pins (SOCC, SANA) and every earlier pin pass on both, including MVST's conclusion
  after its frame and TECX's frame alone.
- *Corpus before synthetic:* every cached SEC filing that mentions a going concern, main's
  detector against this branch's, with `scripts/going_concern_flips.py --ref origin/main`
  (committed, so the counts re-run from the repo; cache only).
  - 582 filings read; 1 more raised in `html_to_text` (below).
  - DOUBT on 187 filings on main, **144** here.
  - **43 DOUBT → None**, read one by one: frames (auditor "Conclude whether", "considers
    whether"), the disclosure policy, denials, alleviations, and risk-factor hypotheticals. None
    states that the filer is in doubt now.
  - **0 None → DOUBT.** The first draft flipped CRVS's sufficiency conclusion; the conclusion
    override was narrowed to a conclusion of doubt.
  - 5 filings keep DOUBT but now quote another sentence. In Wolfspeed's and VSTM's cases it is
    the conclusion itself, which main had skipped as a frame.
- **The shown run on the decision path: the ranker queue, before and after.**
  - `scan_structural` was replayed over the committed `candidate_records.jsonl` (343 names). All
    343 were covered. 1,958 8-K bodies were fetched through the paced house client; the rest came
    from the primary checkout's cache.
  - It ran once with main's detector injected and once with this branch's, then
    `rank_from_snapshots` ranked each.
  - **Flags and queue order are identical.** The same 6 names are sunk for going-concern doubt:
    CBIO, HYMC, ONDS, RLMD, SOC and USAR. Those are the committed queue's 6, and each quotes the
    same sentence on both.
- **MVST and TECX are not regressed** on their pages' own 10-Qs (MVST 0001628280-26-055372, TECX
  0001193125-26-338062), fetched in full (4 paced requests):
  - MVST quotes "These conditions and events raise substantial doubt…" on both;
  - TECX reads None on both.
  - MVST is the only committed page outside the held test packs that carries a going-concern
    statement.

**BOUNDARY.**
- **The corpus:** every `sec`-namespace entry in the primary checkout's `data/cache` whose URL is
  an EDGAR Archives document and whose text matches "going concern", as cached on 2026-10-30.
- **The queue:** `data/snapshots/{candidate_records,ranked_queue}.jsonl` at 08948b5a.
  - The structural window is the scan's own, 8-Ks since each record's `as_of`, read from the
    submissions as cached.
  - So the replay is not the CI run of 2026-10-16 itself. Its going-concern names match that
    run's 6.
- **SEC requests:** all went through `CachedHttp` under the shared SEC pace, with nothing beyond
  the cache otherwise.

**FOUND, NOT FIXED — each outside negation and modality:**
- **"The going concern uncertainty period" reads as a doubt marker.** It is ASC 205-40's
  look-forward period. A 10-Q (0001493152-26-023071) saying working capital is sufficient "to
  conform to the going concern uncertainty period" is DOUBT on main and here.
- **A prior period's doubt reads as current.** Examples: "As previously disclosed, we had
  expressed substantial doubt…", or the 2024 explanatory paragraph RLMD's 2025 10-K reprints
  beside its own "plans alleviated" conclusion. These are DOUBT on main and here. Reading the
  period a statement speaks to is a separate rule.
- **`graph.filings.html_to_text` raises** `ValueError: zip() argument 2 is shorter than argument
  1` in `_furniture` on one cached 10-K (0001628280-26-028623, pre-20251231.htm). The page-furniture
  step fails on that document instead of returning its text.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The demote is unchanged on today's queue. On the dossier, a page whose filing denies or
  hypothesises doubt now carries no going-concern statement, where it carried one before. No
  committed page outside the held test packs moves: MVST's statement stands.
- The new markers are closed lists, grown from the sentences above. A denial or hypothetical in
  other words still reads DOUBT (an under-read, the module's chosen bias).
- Falsifier: a dossier or a queue name that reads None for a filer whose own filing concludes it
  has doubt now.

**REVIEW ROUND 1 (in-session `/code-review high`; Codex's review failed, usage limit).**
- `_NEGATED`'s first form now needs its negator to be a word. The "no" that ends "casino" read as
  a denial, so "Losses in our casino operations raise substantial doubt…" read None, on main
  too.
- A concessive "even if" no longer makes a sentence a hypothetical.
- Both were pinned red first.
- The corpus re-run is unchanged: DOUBT 187 → 144, 0 new.
- The ranker replay is unchanged: flags and queue order identical, the same 6 sunk.
