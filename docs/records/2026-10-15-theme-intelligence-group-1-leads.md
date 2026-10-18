---
id: 2026-10-15-theme-intelligence-group-1-leads
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — group 1 of the verified review leads: U8, U1, U2, U38, U18, U14, U31e

**WHAT.** Operator, 2026-10-15: "fix group 1 as one PR". These are the leads that fail a run or
write a wrong fact, from `docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`.

| Lead | Defect | Fix |
|---|---|---|
| U8 | A thesis retired by re-analysis, its successor created at the salted id with the same key, and that successor's key then corrected. The next article with the bare key raised StoreIntegrityError on `thesis_versions`, and so did every later one with that key. | The key lookup follows the chain of retired ids, the way `_create` salts past them (`engine._by_key`). A former key finds the thesis created with it, as it already did without a retirement in between. |
| U1 | A later version of an article whose two hypotheses reach ONE thesis by two routes (the exact key, and the same-article route): the second was dropped as ALREADY_INGESTED. The version's one contribution id swallowed it, and its new claims were linked to nothing, with no warning. | A second hypothesis reaching a thesis this version already contributed to gets a contribution of its own (`_update(part=)`). The run warns `SAME_THESIS_IN_ARTICLE`. A thesis the same version created counts too. |
| U2 | A thesis held for review (an `other` thesis, or a same-article SIBLING with its identity hold) was archived as stale, then reactivated ACTIVE by new evidence. The review state and the identity hold were gone for good, and the sibling could reach RESEARCH NOW. | Archiving takes a thesis off the active list, never out of review (`_under_review`). The hold applies while it is archived, and reactivation brings it back REVIEW_NEEDED. A thesis never held for review still comes back ACTIVE. |
| U38 | An undated document took the run's as-of as its publication date. An old report read as current last evidence, reset a thesis's 91-day stale clock, and its change items were dated to the run. | An undated source dates nothing. A thesis it updates keeps its own last-evidence date, its change items carry no date, and the run warns `UNDATED_SOURCE`. A thesis it creates starts its clock at the as-of, the only date the registry has, and its card says the source is undated. The stale-series note says what it was measured against. |
| U18 | "Supply will fall short" against "demand will rise" was a CONTRADICTION, then a COMPETING relation. Both are the same bullish reading: demand and supply were one variable, "volume". | Demand and supply are two variables, so the pair is compatible. A shipped volume against either is AMBIGUOUS, never "different". A claim naming both ("supply will fall short of demand") is AMBIGUOUS against either, because its one direction belongs to supply. |
| U14 | On a pulled registry (no article text), a retitled copy of a held report (27% title overlap) was a NEW article, analysed and paid for a second time. With the text held, the same copy was a DUPLICATE. | A pulled registry still holds each block's hash. The argument blocks (paragraphs, list items) the two documents share, weighted by their words, stand in for the text overlap. That is evidence for REVIEW, never for an automatic merge. Bylines, date lines and disclaimers are left out, because every report of a publisher repeats them. |
| U31e | An empty `SEC_USER_AGENT` raised IndexError when `theme_intelligence.config` was imported. That is what an unset GitHub secret becomes in the workflow. | An empty or blank value is unset: `vinci/config.sec_user_agent` falls back to the default, as it does when the variable is absent. The fix is in the shared config, because the empty value also sent an empty User-Agent to EDGAR. |

**WHY.** U8 and U31e fail a run outright; U1, U2, U38 and U18 write a wrong fact or lose one;
U14 pays for a report twice.

**HOW VERIFIED.**
- **The verifier's reproductions, main (c2872114) against this branch:**
  - **U8:** the verifier's own script no longer fails on main. #714's stale-key lookup now finds
    the successor when the article names a segment. With a BARE key (no segment named), main
    raises `StoreIntegrityError thesis_versions: id [TH-C769458254, 1]`; this branch processes
    the article onto that thesis.
  - **U1:** on main the SSD claim is linked to nothing and there is no warning. On this branch it
    is linked, and the run warns `SAME_THESIS_IN_ARTICLE`.
  - **U2:** main brings the `other` thesis back ACTIVE, and the stale sibling back ACTIVE with
    its hold "clear". This branch brings both back REVIEW_NEEDED, and the sibling keeps its hold.
  - **U14:** on main the pulled registry INGESTS a second article. On this branch the copy goes
    to REVIEW against the held one. The text-holding control stays DUPLICATE on both.
  - **U31e:** main raises IndexError for "" and for "   ". This branch uses the default contact.
- **Real registries** (147 registries under the boundary below):
  - **U18, 125,046 distinct claim pairs** (both linked to theses on one value-chain node, within
    a registry), compared both ways (250,092 comparisons):
    - **4,010 move AMBIGUOUS → COMPATIBLE**, every one a demand claim against a supply claim;
    - **no pair gains or loses a CONTRADICTS.** The lead's pair was constructed.
  - **U14, 29 real articles with text** (synthetic fixtures excluded), 53 same-publisher pairs:
    - one pair shares 100% of its argument blocks, and it IS one report: Citi's "Sizing the ETF
      Opportunity" as a web page and as the "Must C" PDF, held in two registries;
    - every pair of different reports shares at most **9.4%**, below the 20% REVIEW floor;
    - the synthetic fixtures share a 22.6% boilerplate paragraph.
  - **U38: 2 undated articles** (TrendForce press releases, as of 2026-10-10) made 3
    contributions. Each created a thesis whose clock is the run's as-of, and that is unchanged
    in storage.
  - **U8 and U2: 0 trigger states.** No re-keyed thesis sits at a retired key's salted id, and no
    thesis created REVIEW_NEEDED is archived or was reactivated. Both are latent.
- **A $0 reassess of a copy of the pilot, main against this branch:**
  - the same 19 theses reassessed and the same 3 changed on both, including TH-DEE87FCF51 SKIP →
    WATCH, the #714 effect the operator accepted;
  - **0 differences** across the 23 theses;
  - the live pilot's checksum is unchanged.
- **Pins:** `tests/test_theme_intelligence_group1.py`, 27 tests, each fix with its negative.
  - Against main, 16 fail. The 11 that pass are what main already gets right:
    - a retired key with no successor;
    - one hypothesis is one contribution;
    - an ordinary thesis comes back ACTIVE;
    - a dated source and a dated stale series;
    - one variable with opposite directions, three ways;
    - another report on a pulled registry, and a shared disclaimer;
    - a set User-Agent.
  - One U1 pin forces its route, because no natural route is known to reach a thesis created in
    the same version. It says so.
- **Mutants: 25 of 25 killed.** An unmutated baseline passes. Two survived the first pass:
  - the retired-thesis guard on a suffixed key;
  - the block-kind filter. Its pin now shares a long disclaimer.
- Ruff and `mypy --strict vinci` clean; offline suite 5,392 passed, 513 skipped, 37 deselected.

**BOUNDARY.**
- Code: main c2872114 against this branch, 2026-10-15.
- Registries: every `registry.db` under the `theme-intelligence` worktree's
  `data/theme_intelligence/` (backups excluded).
- Claims, articles and theses are distinct by id across registries.
- "Real articles" are those whose title does not start "Synthetic".
- The pilot copy is `v2/pilot-2026-10-12`, copied with SQLite's backup API and reassessed as of
  2026-10-15.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **U8: a bare-key article now updates the thesis created with that key, even after its key was
  corrected.** That is the existing rule for a re-keyed thesis ("a former key finds its thesis"),
  now applied past a retirement. Main crashed instead.
- **U1: two contributions from one article version to one thesis can make two versions in one
  run.** Each says what it added, and the run warns.
- **U38:**
  - A thesis created by an undated source starts its clock at the run's as-of. This is said on
    the card and in the run, not inferred.
  - Undated evidence can REACTIVATE an archived thesis without moving its clock, so a stale
    thesis may be re-archived by the same run's archive pass.
- **U14:** block hashes are exact. A copy whose paragraphs were re-flowed (a PDF read differently)
  shares fewer blocks than its text would. The comparison only adds REVIEWs; it never merges.
- **U31e** changes `vinci/config.py`, shared by every EDGAR caller, but only for an empty or
  blank value. That value used to be sent to EDGAR as the User-Agent.
