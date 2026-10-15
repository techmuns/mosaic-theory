---
id: 2026-10-14-theme-intelligence-company-matching
status: recorded
date: 2026-10-14
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — company matching: review findings O8-O12, with the verified leads U21 and U23d

**WHAT.** The resolver that turns a company a source names into an SEC registrant and its listing
(`vinci/theme_intelligence/securities.py`). Operator, 2026-10-14: fix O8-O12, and "fold U21 and
U23d into company matching". The findings are in
`docs/records/2026-10-14-theme-intelligence-open-review-findings.md` (O8-O12) and
`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md` (U21, U23d).

| # | Defect | Fix |
|---|---|---|
| O8 | With a ticker hint, a private company resolved by a partial name ("Cognition", hint CGTX, to Cognition Therapeutics). A fund took the first fund ticker in the quote (VanEck's ETF read as iShares' SOXX). | The private-company guard applies on every path, the hint path included: only the registrant's exact name overrides it. A fund takes the ticker printed in its own name or right after it. If none is, it takes the only fund ticker printed. Several printed with none beside its name is AMBIGUOUS. |
| O9 | A bare name prefix resolved to another company when no business term vetoed it ("Schneider" to Schneider National, a trucking firm). | **A partial name needs backing.** It resolves only when one of these confirms it: an SEC-listed ticker hint naming the same registrant, the registrant's exact name, the model's issuer hint naming it exactly, or a described business that is the registrant's OWN industry. The issuer-hint backing is a flag, not a test on the method sentence. |
| O10 | A company described by the industry it serves was refused: GE ("jet engines for commercial aviation") as an airline, Thermo Fisher ("tools sold to pharmaceutical companies") as a drug maker, CVS as not healthcare. "GE" with the hint GE was refused as two identities. | **The industry a company serves is not its own.** The business is read without its customer clause ("… for …", "… sold to …", "… supplying …"). "Aviation" is not an airline. SIC 5912 (drug stores) is also healthcare. A name written as the very ticker the hint names ("GE", hint GE) is that registrant. |
| O11 | The identity check read the quote's words: "Merck's late-stage pipeline" read as oil and gas. | The check reads the role, what the source says the company does, never the quote's wording. "Pipeline" is oil and gas only when the oil or gas is named, or as a pipeline operator, company or network. |
| O12 | One failed SEC submissions fetch was cached as None for the run, switching the identity check off. | A failed read is retried on the next lookup, never remembered as "no data". A refusal made without the SEC data says so. |
| U21 | Foreign-filer status was any 20-F / 40-F among the recent filings, at every date. Enbridge, a 10-K filer since 2018, was refused. | Status is read **as of the resolution date**: the latest periodic report on or before it, amendments aside (an amendment restates an earlier period). With no report by then it is None, undecidable; never guessed. |
| U23d | The SEC ticker map was stamped with the day it was READ, even when served from a cache up to 7 days old. The stamp went into the record's source and its id. | The map carries the day it was FETCHED, the older of its two files. `CachedHttp.fetched_at` reports a cached copy's fetch time. An HTTP layer that holds none makes the source say "retrieval date not recorded", never today's date. |

**WHY.**
- **A wrong registrant is a wrong fact.** The desk would show a trucking firm as a data-centre
  supplier.
- **Over-strict vetoes hid real companies:** GE, Boeing, Howmet, Thermo Fisher, Danaher and CVS on
  real SEC data; and in the corpus below, every mention written as its own ticker.
- **A false date in a source line breaks "fail loud, never fabricate".**

**HOW VERIFIED.**
- **Corpus before synthetic.** Every distinct stored mention, re-resolved by main's resolver
  (7aaa4944) and by this branch's, offline from the registries' own SEC caches with the shared
  SEC caches as fallback. Result: **4,794 pairs.**
  - **4,704 re-resolved both ways. 42 changed, every one from UNRESOLVED on main:**
    - WMB ×30, AMD ×10 and GEV ×1 are now LISTED_EQUITY, each written as its own ticker with
      that ticker as the hint (O10).
    - Nebius ×1 is still UNRESOLVED, now naming its registrant and the foreign-filer reason.
  - **No mention that main resolved resolves differently.** O9's backing rule refuses no stored
    mention: the corpus holds no unbacked partial name. The rule is shown on the pins below.
  - **90 pairs could not finish offline:** TRP, KMI and DTM, 30 registries each, all re-reads of
    one report. Main refused them before any SEC read, so their SEC files were never fetched.
    Resolved live (cached files first; 4 fetches into a scratch cache, with the honest User-Agent):
    - KMI and DTM: LISTED_EQUITY, verified point-in-time on their 10-Q covers.
    - TRP: TC Energy, identified, then UNRESOLVED as a foreign filer (40-F).
- **U21 on real SEC data** (cached submissions, plus one live cover page; Enbridge is not a stored
  mention):
  - as of 2026-10-11: main UNRESOLVED ("issuer files 20-F/40-F"); this branch LISTED_EQUITY ENB,
    VERIFIED on the 10-Q filed 2026-07-31.
  - as of 2016-06-30: a foreign filer on both, correctly.
- **U23d on real SEC data:** the ticker map in the shared cache was fetched 2026-10-10. Main
  stamps it "retrieved 2026-10-14" (the day it was read); this branch stamps "retrieved
  2026-10-10".
- **Pins:** `tests/test_theme_intelligence_company_matching.py`, 19 tests, each fix with its
  negative.
  - The registrants are real: `tests/fixtures/theme_intelligence/company_matching/sec_records.json`,
    16 registrants and 2 funds, provenance in the file.
  - On main's code, 17 of the 19 fail. The 2 that pass are a negative case and the issuer-hint
    backing guard.
- **Mutants: 21 of 21 killed**, each fix mutated alone in a scratch copy.
  - The first pass killed 16. The 5 survivors were invisible to the tests, which were tightened:
    - "aviation" as an airline (the customer clause had already removed it);
    - the bare "pipeline" regex and the quote read (no role carried the term);
    - the amendment rule (a 40-F/A is not a foreign annual form);
    - the older-of-two-maps rule (both maps had the same date).
- The SEC test doubles (`FrozenSecHttp`, `SecDouble`, `MerckSec`) report no fetch time.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- **"4,794 pairs":** distinct (registry, name, entity type, ticker hint, role) over the 146
  `registry.db` with an SEC cache under the `theme-intelligence` worktree's
  `data/theme_intelligence/` (backups excluded), read 2026-10-14.
  - Each pair is resolved as of its name's latest stored resolution date, else 2026-10-13.
  - The fallback caches are `v2/shared_http_cache/sec`, `http_cache/sec` and `pit/sec`; for
    TRP / KMI / DTM, also the pilot's and the live scratch cache.
- **"16 registrants":** the fixture's, with their files fetched 2026-10-10 to 2026-10-14, each
  date recorded per registrant.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 of model spend; 7 SEC requests in all, into a scratch cache: KMI's and DTM's submissions
  and 10-Q covers, Schneider National's and Uranium Energy's submissions (for the fixture), and
  Enbridge's 10-Q cover.
- **Not fixed, found here:** a company whose SEC name lags its trading name ("GE Aerospace", filed
  as GENERAL ELECTRIC CO) is not resolved by its ticker hint alone. A name is matched against the
  registrant's name; that design is unchanged.
- **Not in this batch:** the resolver's refusal notes still list `[:3]` candidates without a
  count (U36).
