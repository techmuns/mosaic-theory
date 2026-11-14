---
id:
status: shipped
date: 2026-11-14
prs: [1070]
supersedes:
superseded-by:
---

# Rebuild of the 10 active pages, group 3: IT is re-assembled once on main `1f32cbdf` and the operator's 2026-11-12 re-export, priced at the 2026-11-11 close with Polygon and Tiingo calls blocked, losing no field and now priceable; WERN was built too but is HELD, its page left as main's, because one of its release figures is quoted by a line cut before the figure (#829's 200-character cap) — $8.83 of a $13.37 cap on anthropic 2.6.0

**WHAT.**
- **The scope and the rulings** are group 1's (`docs/records/2026-11-14-rebuild-group-1-ncno-smpl-tjx.md`). IT and WERN were built on the operator's 2026-11-12 re-exports, once each, in that order, with no refused re-roll.

| | IT | WERN (built, **HELD**: page not committed, run line committed) |
|---|---|---|
| committed page before | 2026-08-18, ext `2026-08-16.1` | 2026-09-17, ext `2026-08-16.1` |
| $0 precheck on the 11-11 store | exit 0 · 0 regressions · 0 refusals (117 fields) | exit 0 · 0 · 0 (117) |
| run · cost · calls (0 failed) | `3286d4b9` · $3.65 · 7 | `ccbf7ad2` · $5.18 · 10 |
| last cost before | none (priced at the $4.44 median) | none (the $4.44 median) |
| price (close 2026-11-11) | $193.00 (was $179.19, 08-17) | $27.84 (was $35.84, 09-16) |
| lean (5 draws) | mixed (5 / 5) | mixed (5 / 5) |
| machine proposal | none → none | none → none |
| R1 anchor base $/sh | 383.8594 → 371.6709 | 32.6747 → 38.3247 (held, not committed) |
| `valuation_basis.priceable` | false → **true** | true → true |
| 10-Q read | `0000749251-26-000245` → `…-000307` | `0000793074-26-000140` → `…-000172` |
| Sourced fields lost | 0 | 0 |

- **WERN IS HELD** (coordinator 2026-11-14, choosing (b) then (a): "hold WERN out of group 3 the way LLY was held").
  - **The defect:** its new page carries an adjusted-EPS row, −0.03 (the Q3 2025 comparative, 8-K `0000793074-26-000165` EX-99.1), whose verbatim is cut at 199 characters, before the figure. The committed-artifact invariant `test_release_parse::test_committed_dossiers_carry_no_ratio_as_a_currency_amount` refuses it, because the quote shows no currency evidence for its value.
  - The value is right, so WERN's synthesis read the correct figure. The cut is the known 200-character `_verbatim` cap (#829, deferred; STATE row 34, which lists EPAM 1, TJX 2 and VRRM 2).
  - **So the page is not committed.** `data/dossiers/WERN/` and its mirrors stay main's 2026-09-17 page. Its run line `ccbf7ad2` IS committed ($5.18 spent). The built WERN artifacts are kept outside the repository for the refresh.
  - **Next:** a $0 code PR fixing `_verbatim`'s cut (a quote never ends before the figure it backs), pinned on that 8-K's real text, then a $0 refresh of the held build through the deterministic path, not a paid rebuild. That PR also states whether EPAM's, TJX's and VRRM's rows re-quote.
- **IT's four moved pins** (tests only, each shown red under a mutant of what it guards):
  1. `test_dilution_denominator`: IT leaves `ANCHORS_AWAITING_BACKFILL`, its committed base now the recompute's (red with IT's anchor reverted to main's page).
     - Review round 0: IT also leaves `BRIDGE_ONLY_ANCHORS`, because the EDGAR-only recompute values it now, so it is compared rather than passed over.
  2. `test_statement_recon`: IT's tracking companyfacts are regenerated to its September-quarter 10-Q (RUNBOOKS §i step 6, SEC only; red with the stale fixture).
  3. `test_valuation_basis::test_the_gate_applies_the_templates_own_share_guard`: it reads IT's frozen 2026-08-18 page (`tests/fixtures/frozen_pages/2026-08-18/IT/`, byte-identical to main's), whose share counts disagreed by 5.43%. IT's living page now reads counts that agree and is priceable. Red with the guard's tolerance raised.
  4. `test_facts_fix2`: the fact layer's acceptance-time pins ingested the tracking fixture, so regenerating it moved their count of unstated accessions (60 → 61). They now read Gartner's companyfacts frozen at its 2026-08-04 filing (`tests/fixtures/facts/IT-companyfacts-filed-to-2026-08-04.json`, byte-identical to main's tracking fixture). Red with the tracking fixture swapped back in.
  - Review round 0 also labels the frozen IT page apart from the living one in the share-guard pin, so the refusal it requires names which IT.
  - WERN's two premise moves (the Werner wall tests, and its two strict-xfail pins) are not needed while its page stays main's, so they are unchanged.
- **IT's Key Developments text.** Two `operating_drivers` rows on IT's page (tier `anchored`, source CIQ Key Developments, 2026-11-03 and 2026-08-04; 35 words each) share a 19-word run with a call.
  - The local 12-word guard excuses them as KD-sourced and reports them apart.
  - Main's BRBR, BURL and V pages carry the same shape.
  - Whether KD text may be published is the operator's open item (STATE row 60, item 3b). The coordinator ruled it fine to ship and is raising it with the operator.
- **The store, the as-of date and the vendor guard** are group 1's: content sha256 `598a3d2c07f17df5f071742f1a0ea6cc23452f02334c0273bc755de523fa1cb6`, frontier 2026-11-11.
  - Each page read its 14 Polygon reference responses from the 11-11 cache; 0 were refused.
  - Live reads: IT 1 FINRA and 1 SEC; WERN 1 FINRA and 1 SEC.
- **The spool,** write-once: 238 files added for IT and WERN (120 claims, 118 located passages). The 2,433 there after group 2 are unchanged by sha256 and mtime, and none is missing. The total is 2,266 → 2,671 across the three groups.

**WHY.** IT and WERN were the active pages on the operator's 2026-11-12 re-exports. A page carries fix request 2's code only once it is re-assembled.

**HOW VERIFIED.**
- **The $0 precheck** on the 11-11 working copy, boundary lines per RUNBOOKS §i step 4:
  - IT: committed page assembled 2026-08-18T12:39:51Z, `2026-08-16.1`, reference 2026-08-14; the page's export stamps `66405c3bc0` ×9 and `d324beb8f6` ×3 are NOT on disk (re-exported 11-12); 117 fields compared.
  - WERN: 2026-09-17T19:46:23Z, `2026-08-16.1`, reference 2026-08-24; stamps `797fc18691` ×8 and `f9f23c93b9` ×3 NOT on disk; 117 compared.
- **After each build,** `prespend.compare` lists 0 regressions, 0 list members gone and 0 moves on each.
- **The run records** state `sdk_version` 2.6.0, `claude-opus-4-8`, schema 3.
- **The gate, CI-style,** in a clean worktree:
  - the first run, on the branch holding both pages, failed on 8 nodes: IT's three, WERN's four premise moves, and WERN's quote cut;
  - with WERN held and IT's three moved, one more node failed (`test_facts_fix2`'s count, item 4 above), and nothing else;
  - with all four moved, at `55d1b5c1`: ruff clean, `mypy --strict` clean on 219 files, 11,361 passed, 664 skipped, 11 xfailed, 0 failed (pytest exit 0, counted from its progress line), and the mirror in sync.
- **The local 12-word transcript guard:**
  - 91 calls read; 3,158 files scanned;
  - 112 runs shared with a call: 96 excused by SEC filings and 16 by Key Developments exports;
  - 0 unexcused. The 4 KD-only runs new to this branch are IT's two rows and their mirrors.
- **The cross-setup section** (`python -m vinci.impact run`, head `55d1b5c1`, patch-id `83849c0c`): nothing moves, because `vinci/` is identical; 0 of 90 changed-test nodes fail at head.

**THE SDK (#1049's falsifier).** 17 calls, 0 failed, all on 2.6.0, and 0 later draws re-wrote the prompt cache. Neither page has an earlier recorded build, so there is no like-for-like cost. Across the three groups that makes 64 calls and 0 failures on 2.6.0, and 1 cache re-write in 32 later draws, against 2 in 176 on 0.112.0.

**BOUNDARY.**
- **Code:** main `1f32cbdf` for the builds, on branch `artifacts/it-wern-rebuild-2026-11-14`, merged with `origin/main` `a7e5d0e4`; the gate and the cross-setup section at `55d1b5c1`.
- **Pages:** IT's and WERN's committed `dossier.json` at `1f32cbdf`.
- **CIQ:** the operator's 2026-11-12 re-exports, read only.
- **Builds:** IT 2026-11-14 07:22Z; WERN 09:30Z.
- **Spool:** hashed after group 2 (2,433) and after WERN (2,671).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $8.83 of the $13.37 cap, WERN's held $5.18 included; the three groups together $32.42 of $46.30. LLY's and WERN's pages are bought and not yet committed: LLY waits for a paid rebuild after #1069, and WERN for a $0 refresh after the #829 fix.
- IT's two KD-sourced rows ship under the coordinator's ruling; the publication question is the operator's.
