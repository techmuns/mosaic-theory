---
id: 2026-10-30-a-going-concern-statement-is-read-as-stated
status: shipped
date: 2026-10-30
prs: [879]
supersedes:
superseded-by:
---

# A going-concern statement is read as stated: a denial, a hypothetical and the frame are not doubt, and a conclusion that cites ASC 205-40 is (audit E2-D17)

*The rules below are as of review round 2. Each review round's change is recorded at the end of
this record.*

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
- **The frame is the going-concern QUESTION, the cited STANDARD or the disclosure POLICY, and a
  sentence that states its own result is never a frame.**
  - The question is a "whether" whose object IS the evaluation: "whether there are (certain)
    conditions or events" (TECX, MVST, AIRS's "evaluates at each … period whether", LRMR), or
    "whether a material uncertainty exists" (the ISA auditor). A whether-clause about anything
    else ("assessing whether to file for protection under Chapter 11, and these conditions raise
    substantial doubt") is not a frame.
  - The standard cited ("in accordance with", ASU 2014-15, ASC 205-40, MNPR's spaced "205 - 40")
    is policy boilerplate, as main read it (RZLV).
  - The policy's own words are WVE's "required to make certain additional disclosures" and CSTL's
    "the mitigating effect of management's / its plans".
  - The RESULT that overrides the frame is:
    - "concluded / determined that … raise(d) substantial doubt";
    - "… substantial doubt exists" or "… a material uncertainty exists / remains";
    - "these conditions raise substantial doubt";
    - a plain "there is substantial doubt" that no "whether" or "if" asks.

    So Wolfspeed's "concluded that there is substantial doubt …, in accordance with … ASC
    205-40" and VSTM's "As a result of the assessment in accordance with the applicable
    accounting standards, these conditions raise substantial doubt" are doubt. CRVS's "evaluated
    whether … and concluded that our existing cash … are sufficient" stays a frame.
- **A denial names the doubt it denies:**
  - "no (longer) substantial doubt" (EOSE, PHAT, MNPR's "has no substantial doubt");
  - "no material uncertainty exists" (MAR);
  - "does not believe that substantial doubt exists" (ACRS);
  - SHBI's and ADC's "no conditions or events, considered in the aggregate, that raise(d)
    substantial doubt";
  - DBVT's and PCT's doubt that "is / are no longer present";
  - PSIX's "removal of substantial doubt".
- **Only a doubt that HAS BEEN alleviated is denied, and only where nothing in the sentence
  unsettles it.** That is RLMD's "plans alleviated substantial doubt", or "substantial doubt … has
  been alleviated". Each of these leaves the doubt standing:
  - a purpose: "plans to alleviate", "in order to alleviate";
  - a future: "will alleviate";
  - "until …";
  - "no assurance …" (RZLV);
  - XIAO's "cannot alleviate".
- **A hypothetical needs its modal to reach the doubt within a few words.** The forms are:
  - ZURA's "could raise substantial doubt";
  - LODE's "could have an immediate material adverse effect on liquidity and raise substantial
    doubt";
  - AGL's "could in the future, result in substantial doubt";
  - OGN's "could result in a going concern qualification";
  - EBS's "may give rise to …";
  - DNTH's "may include an explanatory paragraph";
  - MNLK's "may conclude that there is substantial doubt";
  - "substantial doubt could exist";
  - "If … there remains substantial doubt".

  These stay doubt:
  - SOCC's "…, if at all, substantial doubt exists": the comma ends the conditional.
  - SANA's "may not be sufficient …, and there is substantial doubt": the modal never reaches the
    doubt.
  - "Even if … there is substantial doubt": concessive.
  - **"Cast … doubt" is NOT a hypothetical.** In the IFRS / ISA 570 term of art, "a material
    uncertainty exists that may cast significant doubt", the modal belongs to the term and the
    sentence is a conclusion (KYIV, LAR, USAR's 10-Q).
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
  - DOUBT on 187 filings on main, **125** here (as of round 2; 144 before it).
  - **62 DOUBT → None**, read one by one: frames (the auditor's "Conclude whether", "considers
    whether", AIRS's, TOI's and ADUS's "evaluation as to whether"), the policy (WVE, CSTL, MNPR's
    standard), denials (SHBI, ADC, DBVT, PSIX), alleviations, and risk-factor hypotheticals (OGN,
    EBS, DNTH, AGL, LODE). None states that the filer is in doubt now.
  - **0 None → DOUBT.**
    - The first draft flipped CRVS's sufficiency conclusion; the conclusion override was narrowed
      to a conclusion of doubt.
    - A round-2 draft flipped LRMR's "whether there are certain conditions"; the whether-object
      was widened.
  - 11 filings keep DOUBT but now quote another sentence. In Wolfspeed's and VSTM's cases it is
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

**STILL READ DOUBT (measured at round 2), and why.** Of the 125 filings still DOUBT, these are not
a current statement of the issuer's own doubt. Main reads every one the same:
- **In this PR's class (a hypothetical whose modal sits further from the doubt than the window
  allows):** TALO ("could be well in excess of insured amounts and result in significant current
  losses … as well as going concern issues") and LZM ("may cause material and adverse impacts …,
  potentially causing substantial delays and raising substantial doubt"). The window is kept
  short on purpose: a longer one would reach SANA-like real conclusions.
- **A prior period's or a previously disclosed doubt** (a period rule, below), 19 filings:
  - BW, CGC, CODI, "forward" (0001683168-25-009068);
  - CK 0002100782, VSTM's 10-K;
  - two ONDS 10-Qs, a USAR 8-K;
  - the issuer whose 2025 offering closed (0001213900-25-086227);
  - EVMN, HE's 10-K, PCT;
  - AURA's Q1 10-Q, IAUX's Q1 10-Q;
  - MVST's FY2024 and FY2025 10-Ks ("In prior periods, we disclosed …");
  - NEXT (its 2023 statements);
  - PSIX's valuation-allowance history.
- **Not the issuer's own doubt**, 9 filings: a debtor (BBT, BRKL, the ones main also read DOUBT),
  a borrower (ZIONS twice), a tenant (NHI twice), an investee (BLFS), a predecessor (DBD), an
  acquiree (PURR's Rorschach).
- **Raised, then alleviated, in two sentences:** FRMI's Q1 10-Q, and MVST's Q1 10-Q (nit 6 of
  review round 2). Under ASC 205-40-50-12 an alleviated doubt is no substantial doubt; this
  detector reads sentence by sentence, so the earlier "raise substantial doubt" still fires.
  The committed MVST page (its Q2 10-Q) is unaffected.

Of the rest, two filings are the "going concern uncertainty period" term (below), and two are
TRC's risk lists, whose mention sits past the 600-character sentence window and was not read.
Everything else is a current statement of doubt: conclusions, auditors' explanatory paragraphs,
and risk bullets that assert it.

**FOUND, NOT FIXED — outside negation, modality and the frame:**
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
  other words still reads DOUBT. That is an OVER-read, an over-demote: the direction the module
  calls unsafe. The lists, measured above, leave two in-class over-reads in the corpus.
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

**REVIEW ROUND 2 (coordinator review of #879 at 97f4927a, the last round under the cap).**
- **Over-reaching guards, narrowed.**
  - "cast" and "significant" are out of the hypothetical (the IFRS term of art).
  - The frame is bounded to a whether-clause whose object is the going-concern evaluation.
  - The citation frame is restored, behind a wider result override.
  - Alleviation is a denial only when it is past and unsettled.
- **In-class misses, fixed:** SHBI, ADC, DBVT, AIRS, ABL, ADUS, TOI, CSTL, MNPR, OGN, EBS, DNTH,
  AGL, LODE and HE's Q1 10-Q. PCT's and PSIX's in-class sentences are fixed too, but each filing
  still reads DOUBT on a prior-period sentence (listed above).
- **Pins:** 30 new. 28 are red on 97f4927a. The other two (LRMR's "certain conditions", CSTL's
  second policy sentence) pass there; they guard regressions a round-2 draft introduced.
- **Corpus:** DOUBT 187 → 125 (62 off, 0 on).
- **Ranker replay** over the 343 queue names: unchanged, the same 6 sunk.
- **MVST and TECX:** unchanged.
