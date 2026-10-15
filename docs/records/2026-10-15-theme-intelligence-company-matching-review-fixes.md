---
id: 2026-10-15-theme-intelligence-company-matching-review-fixes
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the review of the company-matching change: five findings fixed

**WHAT.** A high-effort review of PR #711 (`docs/records/2026-10-14-theme-intelligence-company-matching.md`)
reported five findings on it; operator, 2026-10-15: "fix all eight" (with three on PR #712).

| Finding | Fix |
|---|---|
| **A failed SEC read was retried on every lookup, with the whole retry ladder.** O12 stopped caching a failure as "no data"; each later call (industry, foreign-filer check, cover page, narrowing) then re-paid ~31 s of backoff — an SEC outage stretched a scan to hours. | A failure is remembered for the resolver's run and not asked again. It is never read as "no data": a PARTIAL name whose registrant's filings could not be read is refused as **identity not checked** (said, with the error), never resolved without the check; the next run reads it again. The registrant's exact name needs no industry check and is not refused. |
| **The customer-clause rule cut at any "to".** "Expected to sell SOFC fuel cells to data centres" read as no business at all, so a wrong ticker hint went unchecked. | "to" is a customer clause only after a supplying word ("supplier to", "sold to", "sells to", "provider to", "exposure to", …); "for", "serving", "supplying" and "used by" still are. |
| **The fund ticker "beside its own name" matched case- and space-exactly.** A name written "VanEck semiconductor ETF" missed "VanEck Semiconductor ETF (SMH)" and fell to AMBIGUOUS. | The name is matched ignoring case and with any spacing. |
| **The foreign-filer check walked the older submission pages, and the cover page walked them again.** | The filing rows are walked once per registrant and date and shared (the foreign-filer check, the cover page, the enrichment's check). The walk itself stays: a historical as-of needs the older filings to know how the issuer filed then. |
| **`fetched_at` parsed the whole cached entry again** — megabytes for the SEC ticker map — right after the map itself was read. | The HTTP cache keeps the fetch time of what it just read or wrote; the file is read only for a URL this instance has not touched. |

**WHY.** One is a run that can take hours; one silently switched the identity check off for
plain role text; one lost a correct fund; two are repeated work on the resolver's path.

**HOW VERIFIED.**
- **Corpus before synthetic:** every stored mention (4,794 pairs, 146 registries) re-resolved by
  main (7aaa4944) and by this branch, offline from the SEC caches — now including the pilot's and
  the scratch cache of the earlier live fetches, so **0** pairs are left unresolvable. **No
  mention that main resolved resolves differently.** 131 that main refused now resolve or are
  identified: WMB ×30, KMI ×30, DTM ×30, AMD ×10, GEV ×1 listed; TRP ×30 identified as a foreign
  filer.
- **The customer-clause change on real roles:** 2 of 570 distinct stored roles read differently.
  "ETF cited to illustrate…" (an ETF: the fund path never reads roles). And Nebius, "Pivoted to
  328MW Bloom fuel cells", now reads as a fuel-cell business and is refused on identity — a
  company that BOUGHT fuel cells; UNRESOLVED as on main (before this fix it was identified, then
  refused as a foreign filer). A term table cannot tell buying from making; stated, not hidden.
- **Pins** (`tests/test_theme_intelligence_company_matching.py`, 22 tests): the failed read
  remembered and failing closed (and not for the exact name); an infinitive "to"; the fund name in
  another case and spacing; one walk of the filings; the fetch time kept from a read and from a
  write. All 5 new ones fail on the change before these fixes (e6761438).
- **Mutants: 29 of 29 killed** (the change's 19 still applicable, and 10 for these fixes). Two
  earlier mutants targeted code these fixes replace and were retired.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.** Code: PR #711's branch, 2026-10-15. "4,794 pairs / 570 roles": distinct (registry,
name, entity type, hint, role) and distinct role texts over every `registry.db` under the
`theme-intelligence` worktree's `data/theme_intelligence/` (backups excluded), read 2026-10-15.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no SEC or model requests.
- **A transient SEC failure early in a run refuses that registrant's partial names for the rest of
  the run** (identity not checked, said); the next run reads it again. Accepted over a run that
  re-pays the retry ladder on every lookup.
