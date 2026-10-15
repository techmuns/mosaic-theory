Operator, 2026-10-15: "fix group 1 as one PR". These are the verified review leads that fail a run or write a wrong fact (`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`). The full account is in `docs/records/2026-10-15-theme-intelligence-group-1-leads.md`.

## What changes

- **U8: a retired key's chain is followed.** The scenario: a thesis is retired by re-analysis, its successor is created at the salted id with the same key, and that successor is then re-keyed. The next bare-key article raised `StoreIntegrityError` on `thesis_versions`, and so did every later one. `engine._by_key` now follows the chain of retired ids the way `_create` salts past them. A former key finds the thesis created with it, as it already did without a retirement in between.
- **U1: a second route is a second contribution.** Two hypotheses of one later article version can reach one thesis by two routes. The second was dropped as ALREADY_INGESTED, its claims linked to nothing and no warning given. It now gets its own contribution id (`_update(part=)`), and the run warns `SAME_THESIS_IN_ARTICLE`.
- **U2: archiving keeps a review.** A REVIEW_NEEDED thesis (an `other` thesis, or a same-article sibling with an identity hold) that was archived came back ACTIVE, with its hold gone. `_under_review` keeps the hold while it is archived, and reactivation restores REVIEW_NEEDED.
- **U38: an undated source dates nothing.**
  - When it updates a thesis, the thesis keeps its own last-evidence date (main reset the 91-day clock to the run's as-of), the change items carry no date, and the run warns `UNDATED_SOURCE`.
  - When it creates a thesis, the clock starts at the as-of and the card says the source is undated.
  - The stale-series note names what it was measured against.
- **U18: demand and supply are two variables.** "Supply will fall short" against "demand will rise" was a CONTRADICTION, then a COMPETING relation; it is now compatible.
  - A shipped volume against either side is AMBIGUOUS.
  - So is a claim naming both sides, such as "supply will fall short of demand".
- **U14: a pulled registry compares block hashes.** A retitled copy of a held report was analysed and paid for again on a registry pulled without article text. The word-weighted hashes of the shared argument blocks now send it to REVIEW, never to an automatic merge. Bylines, date lines and disclaimers are left out.
- **U31e: an empty `SEC_USER_AGENT` is unset.** An unset GitHub secret arrives as `""` and raised IndexError at import. The fix is in the shared `vinci/config.sec_user_agent`, because the same empty value was sent to EDGAR as the User-Agent.

## Real-run verification

The verifier's reproductions, run on main (c2872114) and on this branch:

```
U8 (bare key)   main    a2 RAISED: StoreIntegrityError thesis_versions: id ['TH-C769458254', 1] already stored with a DIFFERENT payload
                branch  a2: PROCESSED [('TH-C769458254', False, ['CHALLENGED'])]
U1              main    v2 outcomes: [ATTRIBUTION, ALREADY_INGESTED] | SSD claim linked to any thesis: set()
                branch  v2 outcomes: [ATTRIBUTION, UPDATED v2]   | SSD claim linked; WARN SAME_THESIS_IN_ARTICLE
U2 (other)      main    after material update: status ACTIVE
                branch  after material update: status REVIEW_NEEDED
U2 (sibling)    main    sibling after material update: ('ACTIVE', 2, 'WATCH', [('clear', 'no blocking verification issue')])
                branch  sibling after material update: ('REVIEW_NEEDED', 2, 'WATCH', [('HOLD', 'identity under review …')])
U14             main    PULLED: INGESTED A-6e9dc9d1c77c | same article? False
                branch  PULLED: REVIEW A-22c4843c119d | same article? True   (text-held control: DUPLICATE on both)
U31e            main    SEC_USER_AGENT="" / "   " -> IndexError: list index out of range
                branch  -> 'mosaic-theory-theme-intelligence/0.1 (research scanner; contact: tech@muns.io)'
```

The verifier's own U8 script no longer fails on main: #714's stale-key lookup finds the successor when the article names a segment. The bare-key case above still failed.

Real registries (147, under the theme-intelligence worktree, backups excluded):
- **U18:** of 125,046 distinct claim pairs, compared both ways, 4,010 move AMBIGUOUS → COMPATIBLE. Every one of them is demand against supply. **No pair gains or loses a CONTRADICTS.**
- **U14:** 29 real articles give 53 same-publisher pairs. The one pair above the 20% floor is a true match: Citi's ETF report as a web page and as a PDF, at 100%. Pairs of different reports share at most 9.4%.
- **U38:** 2 undated TrendForce press releases made 3 contributions.
- **U8 and U2:** 0 trigger states, so both are latent.

**A $0 reassess of a pilot copy, main against this branch:** the same 19 theses reassessed and the same 3 changed on both, including TH-DEE87FCF51 SKIP → WATCH (accepted). There are 0 differences across the 23 theses, and the live pilot's checksum is unchanged.

Checks:
- Pins: `tests/test_theme_intelligence_group1.py`, 27 tests. Against main, 16 fail; the 11 that pass are negatives and controls.
- Mutants: 25 of 25 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean.
- Offline suite (`pytest -m "not network"`): **5,392 passed, 513 skipped, 37 deselected**. The record and STATE lints pass: 720 passed.

This branch is from main and does not include PR #715. Both edit STATE row 32 item (8), so whichever merges second resolves that one line.

## Disposition

| Item | Status | Note |
|---|---|---|
| U8: a retired key's chain is followed | SHIPPED | latent in stored data |
| U1: a second route is a second contribution | SHIPPED | one pin forces its route for the same-version case and says so |
| U2: archiving keeps a review | SHIPPED | latent in stored data |
| U38: an undated source dates nothing | SHIPPED | 2 real undated articles; stored records unchanged |
| U18: demand and supply are two variables | SHIPPED | 4,010 real pairs AMBIGUOUS → COMPATIBLE, no contradiction changes |
| U14: a pulled registry compares block hashes | SHIPPED | REVIEW only, never a merge |
| U31e: an empty SEC_USER_AGENT is unset | SHIPPED | in the shared `vinci/config.py` |

Accepted, stated in the record:
- A bare-key article updates the re-keyed thesis created with that key. This is the existing "former key finds its thesis" rule.
- Two contributions from one version can make two versions in one run.
- An undated update can reactivate a stale thesis that the same run then re-archives (shown).
- Block hashes miss re-flowed paragraphs.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

