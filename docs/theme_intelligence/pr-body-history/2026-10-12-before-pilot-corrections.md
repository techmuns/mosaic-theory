## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool.
- It reads research from **seven publisher channels** — five automatic, two manual-first — and from documents the operator supplies.
- It extracts source-anchored evidence, named companies and risks.
- It keeps a persistent, versioned registry of theses.
- It writes a decision-first weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path:
- no fund module imports it;
- it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned);
- it has its own SQLite registry;
- it has no buy / sell / target / weight field;
- its priority rules read no prices, returns or outcomes.

**This update reports the one supervised pilot** (next section) and carries its one code fix.
- **Code:** `vinci/theme_intelligence/parse.py`, one line — the paywall marker is searched for in the whole page.
- **Test:** `tests/test_theme_intelligence_parse_verify.py`, one test.
- **Untouched:** the prompts, the model, the sources, the cost limits, and fund decision code.

**Docs:**
- Record: `docs/records/2026-10-12-theme-intelligence-supervised-pilot.md`
- STATE §5.0 row 32
- The previous PR body: `docs/theme_intelligence/pr-body-history/2026-10-12-before-supervised-pilot.md`

**Not merged.** The weekly schedule is not enabled, and the production state branch was not created.

**Privacy:** no article text, card or dashboard from the pilot is committed. They stay in the git-ignored pilot registry, on this machine only.

---

## Supervised pilot (this update)

### Source rights — recorded apart from licensing

The operator chose **Option 2**: explicit acceptance of the identified terms-of-use and contractual risks, for **this one-time internal pilot only**. That is **not** publisher permission. Licensing is **NOT confirmed** for J.P. Morgan, TrendForce, Nomura or SemiAnalysis. On the reading of their terms, none of them permits automated collection or third-party AI processing.

Nothing behind authentication, a paywall, a robots rule or an access control was fetched. The optional PDF stays **PENDING RIGHTS/INPUT**.

### Verdicts

| Dimension | Verdict |
|---|---|
| Engineering quality | **REVIEW** — end to end on real articles. The guard, access discipline, QA, idempotence and author guard held. One material defect fixed; one open that loses an article. |
| Research accuracy | **REVIEW** — **0 wrong values in 96 numeric values checked**, and the theses are faithful to their sources. But the one RN meets two gate conditions on weak grounds; review warnings don't reach the card; and one comparison thesis is unstable across draws. |
| Coverage | **REVIEW** — 4 of 5 articles processed. Verification: 1 FULLY_VERIFIED, 3 INCOMPLETE, all stated. |
| Source permissions | **FAIL (not confirmed)** — risk accepted for one pilot ≠ licence. |
| Costs | **PASS** — **$3.9494 of the $18** automatic allocation ($0 of the $7 PDF allocation). 0 of 19 paid calls above their pre-send bound. Every processed article came in under its preflight low estimate. |
| Operational readiness (unattended weekly) | **FAIL** — blocked on source rights. 1 of 5 articles lost to an open defect. 2 of 7 channels healthy. |

The spend guard is an estimate-based, per-call pre-send bound plus a run limit. It is not a provider billing cap; the provider's bill is the authority.

### The five articles

| Article | Outcome | Theses | Cost |
|---|---|---|---|
| J.P. Morgan — "What risks? Earnings are up and to the right" | **FAILED** ×2 — pass 1 wrote `hypotheses` as broken JSON text, 4 of 4 answers | 0 (its 1 thesis lost) | $1.4865 |
| TrendForce — "HBM Supply Constraints Persist…" | FULLY_VERIFIED | RN `TH-7C895A0A4E`, WATCH `TH-1516B6186B` | $0.4950 |
| Nomura — "How AI Masks America's Rising Risk Premium" | INCOMPLETE (1 of 28 paragraphs open) | WATCH `TH-2FFD9B58A8` | $0.6305 |
| Nomura — "Faster, Slower, Then Steady" | PARTIAL (client-portal report not fetched) | 0 — correct (a Japan CPI outlook) | $0.3136 |
| SemiAnalysis — "Beijing Will Not Pace the Frontier" (comparison case) | recorded FULL — **it was a paid post's free preview** | 0 (an earlier draw gave 1 WATCH) | $1.0238 |

Duplicate test: two `--cache-only` re-runs returned ALREADY_INGESTED, $0, no new records.

### Defects

1. **FIXED — a long free preview was read as the full article.**
   - The marker was searched for in only the first 20,000 characters; this post's sits at character 29,821, in a `div.paywall` outside the parsed blocks.
   - A $0 corpus check over 60 cached pages flips exactly 2, both SemiAnalysis paid posts; nothing else changed.
   - Regression test on the live DOM shape; 3 of 3 mutants killed.
   - The pilot's stored record keeps FULL, because an already-ingested version is not re-parsed (open).
2. **OPEN, material — a pass-1 answer writing `hypotheses` as text loses the article.**
   - On the JPM article this happened in 4 of 4 answers. The answers were otherwise right: 27 of 27 numeric claims matched, and the lost thesis is the article's.
   - A minimal fix — a re-ask naming the refusal — was tried on the real case. It failed the same way ($0.7643), and was reverted; it is **not** in this branch.
   - **Your decision:**
     - (a) field-by-field salvage for pass 1, as completeness parts already have — each refused answer loses exactly its one hypothesis;
     - (b) strict tool use, which changes every cache key;
     - (c) accept, and report each lost article.
3. **OPEN, cosmetic — web articles print "page None".** Six format sites; one persists into a stored risk's text.
4. **OPEN, card quality — reviewer warnings never reach the card.** 7 sentences were flagged REVIEW_PARTIAL, two of them labelled MEASURED OBSERVATION on conditional content. They print unmarked; only BLOCK findings are withheld.
5. **OPEN, research — the one RN's gate rests on weak grounds.**
   - Its "source-named exposure" is the page's category tag, "Semiconductors".
   - Its own horizon is longer-term, yet the gate counts a 2027 window as near-term.
   - It is defensible on substance; its audit trail is weak.
6. **OPEN, research — the SemiAnalysis comparison case is unstable.** One earlier draw gave 1 WATCH; the pilot's draw gave 0. An independent read finds 0 narrowly better, but borderline — and the text was a preview.
7. **OPEN, operations — no combined weekly page for article-by-article runs.** `report --week` renders the latest run; a `scan` gives the combined page.

### Also checked

- **Nine sections:** 9 of 9 rendered card files (3 theses × md / html / print) have all nine sections.
- **Cross-source links:** 0 between articles, as expected for four topics. One correct SIBLING: TrendForce's two theses, one article, different economics.
- **Independent confirmations:** 0.
- **Within-article duplicates:**
  - Nomura's ~80% figure, stated twice, shows as 2 evidence rows.
  - A TrendForce claim used on both sides was flagged CLAIM_BOTH_SIDES and removed from the WATCH's counter-evidence.
- **Author guard:** refused 2 invented author attributions.
- **Access:**
  - Morgan Stanley fails closed (robots.txt unreachable).
  - Goldman Sachs's 403 is never bypassed.
  - The Nomura portal report is flagged for upload, never fetched.

### Gate

- ruff clean; `mypy --strict vinci` clean (184 files).
- `pytest -m "not network"`: **4,961 passed, 511 skipped, 0 failed** (exit 0; code `d3666abd`).
- `qa --run` on all 7 pilot runs: processed runs 19–20 of 20 (the misses are stated open items); failed runs 19 of 20 (no cards to compare).
- CI: read after push.

| brief item | disposition | note |
|---|---|---|
| Run the five selected articles, fresh isolated registry | SHIPPED | `data/theme_intelligence/v2/pilot-2026-10-12/` (git-ignored) |
| 1 financial and factual accuracy | SHIPPED | 96 numeric values checked, 0 wrong |
| 2 completeness of distinct theses | SHIPPED | 3 theses; JPM's lost (defect 2); SemiAnalysis read from a preview (defect 1) |
| 3 citations, dates, numerical qualifications | SHIPPED | dates right; one mis-cited mechanism and two overstated labels — the review flagged them, the card does not show them (defect 4) |
| 4 company identities and mechanisms | SHIPPED | no wrong identity; RN exposure from a category tag (defect 5) |
| 5 counter-evidence and risks | SHIPPED | the source's own risks surfaced; SemiAnalysis caveats under-captured |
| 6 RN / WATCH / SKIP | SHIPPED | 1 / 2 / 0; WATCHes sound; RN gate weak (defect 5) |
| 7 duplicate evidence and cross-source relationships | SHIPPED | 0 cross-article links, 0 independent confirmations, 1 correct SIBLING, 2 within-article duplicates |
| 8 nine-section card quality | SHIPPED | 9 / 9; "page None" (defect 3) |
| 9 actual cost | SHIPPED | $3.9494 of $18 |
| Verdicts | SHIPPED | above |
| Risk acceptance recorded apart from licensing | SHIPPED | record + STATE row 32; licensing NOT confirmed |
| Manual PDF | SKIPPED | PENDING RIGHTS/INPUT — "can be handled separately" |
| Fix only a reproducible material defect | SHIPPED / PARTIAL | defect 1 fixed; defect 2's minimal fix falsified, so it goes to your decision |
| Not merged; no schedule; no state branch; no investment-decision code | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **Pilot closeout** (`docs/records/2026-10-12-theme-intelligence-pilot-closeout.md`):
  - one fuel-cell thesis;
  - a thesis keyed by its subject (grid equipment);
  - the review queue;
  - the pilot-readiness check (10 of 10).
- **Coverage and identity** (`docs/records/2026-10-12-theme-intelligence-coverage-identity.md`):
  - the part-4 re-ask;
  - one technology per thesis;
  - same-article identity matches;
  - the source's own risks.
- **Analytical safeguards** (`docs/records/2026-10-12-theme-intelligence-analytical-safeguards.md`):
  - field-by-field salvage;
  - mechanism coverage;
  - the timing rules;
  - the preflight.
- **Targeted PDF cost reduction** (`docs/records/2026-10-12-theme-intelligence-pdf-glyph-quarantine.md`).
- **State-pull ledger, seven-source corrections, hybrid ingestion, source health, review rounds 2–3, the original build:** see the records named in `STATE.md` §2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

