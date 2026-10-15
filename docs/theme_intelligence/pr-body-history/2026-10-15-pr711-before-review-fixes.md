Fixes the company-matching findings from the techmuns/mosaic-theory#703 review (O8–O12), plus two leads verified in techmuns/mosaic-theory#710 (U21, U23d). Everything is in the SEC resolver, `vinci/theme_intelligence/securities.py`, which decides which listed company a source is talking about.

Operator, 2026-10-14: "merge 710, then fold U21 and U23d into company matching".

## What changes
| # | Before | After |
|---|---|---|
| O8 | A private company with a ticker hint resolved by a partial name ("Cognition", hint CGTX, became Cognition Therapeutics). A fund took the first fund ticker in the quote (VanEck's fund became SOXX). | The private-company guard now runs on every path, including the ticker-hint path. A fund takes the ticker beside its own name, or the only fund ticker printed. If several are printed and none sits beside its name, the result is AMBIGUOUS. |
| O9 | A bare name prefix resolved to another company ("Schneider" became Schneider National, a trucking firm). | **A partial name needs backing:** an SEC-listed ticker hint naming that company, its exact name, the model's issuer hint naming it exactly, or a described business that is the company's own industry. |
| O10 | GE, Boeing, Howmet, Thermo Fisher, Danaher and CVS were refused when described by the industry they serve. "GE" with the hint GE was refused as two identities. | **The industry a company serves is not its own:** the customer clause ("for …", "sold to …") is no longer read. "Aviation" no longer means an airline. SIC 5912 (drug stores) also counts as healthcare. A name written as the very ticker the hint names is that company. |
| O11 | The identity check read the quote's wording, so "Merck's late-stage pipeline" counted as oil and gas. | The check reads the role, never the quote. "Pipeline" means oil and gas only when oil or gas is named, or for a pipeline operator, company or network. |
| O12 | One failed SEC fetch was cached as "no data" for the whole run, which switched the identity check off. | A failed fetch is retried on the next lookup. A refusal made without the SEC data now says so. |
| U21 | A company counted as a foreign filer if it had any 20-F or 40-F among its recent filings, at every date. Enbridge, a 10-K filer since 2018, was refused. | Foreign-filer status comes from the latest periodic report on or before the as-of date; amendments don't count. With no report by then, the status is undecidable, never guessed. |
| U23d | The SEC ticker map was stamped with the day it was read, even when served from a cache up to 7 days old. | The map carries the day it was fetched (the older of its two files), via the new `CachedHttp.fetched_at`. Where no fetch time exists, the source says "retrieval date not recorded". |

## Verification

**Real data first.** I re-resolved every distinct stored mention with main's resolver (7aaa4944) and with this branch's. The run was offline, using the registries' own SEC caches with the shared caches as fallback: 4,794 (registry, mention) pairs across 146 local registries.
- **Nothing that main resolved resolves differently on this branch.**
- **42 changed, all from UNRESOLVED on main:**
  - WMB ×30, AMD ×10 and GEV ×1 are now LISTED_EQUITY. Each was written as its own ticker, with that ticker as the hint (O10).
  - Nebius ×1 is still UNRESOLVED, but now names its registrant and gives the foreign-filer reason.
- **90 could not finish offline:** TRP, KMI and DTM, 30 registries each, all re-reads of one report. Main refused them before any SEC lookup, so their SEC files were never cached. I resolved them live, reading cached files first and fetching 4 files into a scratch cache:
  - KMI and DTM resolve to LISTED_EQUITY, verified point-in-time.
  - TRP is identified as TC Energy, then left UNRESOLVED because it files 40-F.
- **O9's new rule refuses no stored mention:** the corpus holds no unbacked partial name. The rule is shown working on the test cases below.

**U21 on real SEC data:**
- As of 2026-10-11, Enbridge goes from main's UNRESOLVED ("issuer files 20-F/40-F") to **LISTED_EQUITY ENB, VERIFIED on its 10-Q filed 2026-07-31**.
- As of 2016-06-30 it is a foreign filer on both main and this branch, which is correct.

**U23d on real SEC data:** the shared cache's ticker map was fetched 2026-10-10. Main stamps it "retrieved 2026-10-14"; this branch stamps "retrieved 2026-10-10".

**Tests:** `tests/test_theme_intelligence_company_matching.py` adds 19 tests, each fix with its negative case.
- They run on real SEC records: `tests/fixtures/theme_intelligence/company_matching/sec_records.json`, 16 registrants and 2 funds, provenance in the file.
- On main's code 17 of the 19 fail. The 2 that pass are a negative case and the issuer-hint backing guard.

**Mutation check:** 21 of 21 mutants killed, each fix mutated alone. The first pass killed 16; the 5 survivors were cases the tests couldn't see, and those tests were tightened.

**Suite and lint:**
- `ruff check .`: All checks passed!
- `mypy --strict vinci`: Success: no issues found in 187 source files.
- `pytest -m "not network"`: `5271 passed, 513 skipped, 37 deselected, 19 warnings in 106.04s`.
- Record and STATE lints: `708 passed, 1 skipped`.

**Cost:** $0 of model spend and 7 SEC requests, all into a scratch cache.

## Not in this PR
- **"GE Aerospace" with the hint GE is still not resolved.** The SEC still files the company as GENERAL ELECTRIC CO, and names are matched against the registrant's name. Found while testing; the design is unchanged.
- **U36:** the resolver's refusal notes still list up to 3 candidates without saying how many there are.

## Files
- **Code:** `vinci/theme_intelligence/securities.py`, `vinci/theme_intelligence/enrich.py` (passes the as-of date to the foreign-filer check), and `vinci/netcache.py` (new `fetched_at`).
- **Tests:** the new test file and fixture. The SEC test doubles in `tests/theme_intelligence_support.py`, `tests/test_theme_intelligence_identity.py` and `tests/test_theme_intelligence_enrichment.py` gain a `fetched_at` that returns None.
- **Docs, in their own commit:** `docs/records/2026-10-14-theme-intelligence-company-matching.md` and STATE row 32, item (8).

## Disposition
| Brief item | Disposition |
|---|---|
| O8: private-company guard on the hint path; fund ticker choice | SHIPPED |
| O9: partial name needs backing | SHIPPED |
| O10: industry served is not the company's own; name-as-ticker | SHIPPED |
| O11: the role is read, not the quote; "pipeline" | SHIPPED |
| O12: a failed SEC read is not cached | SHIPPED |
| U21: foreign-filer status as of the date | SHIPPED |
| U23d: the ticker map's retrieval date | SHIPPED |
| Corpus re-resolution, main vs branch | SHIPPED: 0 regressions; 132 previously refused now resolved or identified |
| Regression tests and mutation check | SHIPPED: 19 tests; 21 of 21 mutants killed |
| Record and STATE | SHIPPED |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

