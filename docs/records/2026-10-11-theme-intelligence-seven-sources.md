---
id:
status: shipped
date: 2026-10-11
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — seven sources (Bank of America retired), identity before ticker, a market regime only on market-structure evidence, verification checks corrected, spending limits before every call, version dates, state sync exercised on GitHub

**WHAT.** In `vinci/theme_intelligence/` (research attention only, off the decision path), the
"final consolidated corrections and seven-source configuration" brief on PR #703. Every result
below is from a real run unless marked SYNTHETIC; cached replays are said to be cached.

- **Seven publishers** (`sources.toml`, `config.py`, `pipeline.py`, `report.py`, `health.py`).
  Bank of America removed — not replaced — and kept under `[[retired]]` as history: no
  discovery, health check, upload request or new import (`ingest-file`, `ingest-inbox`, `article`
  refuse it, a page on its host or a subdomain included); its old articles, theses, runs, health
  records and candidates stay untouched; a carried QUEUED BofA row becomes SOURCE_INACTIVE, never
  processed. Morgan Stanley and Goldman Sachs are **manual-first**: health-checked only, no
  discovery, research by upload; a week with nothing supplied says MISSING, not absent. Every
  count derives from the configured seven.
- **Identity before ticker** (`securities.py`). A registrant is accepted only when the source's
  own description of the company (its quote and role) is compatible with the issuer's SEC
  industry (SIC); a hint naming a non-SEC listing never resolves by a partial name. Point-in-time
  listing checks run after identity. Citi's "Delta" (a solid-oxide fuel-cell competitor) had
  resolved to Delta Air Lines; it is now UNRESOLVED — the company is Delta Electronics (TWSE
  2308, a Ceres Power SOFC licensee), not SEC-registered.
- **Record kind** (`engine.record_kind`). A record is a market regime only when its evidence
  measures equity-market structure (correlation, dispersion, breadth, PRICE volatility), on any
  node; otherwise it is corrected to an investment thesis (`RECORD_KIND_CORRECTED`) and its
  earnings transmission is tested. The first cut (`12e935b0`) exempted the market-wide node; the
  LatAm review found that exemption wrong and `1a998700` removed it.
- **Verification checks** (`verify.py`, `completeness.py`). A decline stated in words supplies a
  value's minus ("down ~27%"); a figure written with an ellipsis verifies piece by piece; a
  figure restated in a caption / table / summary is captured where the article states it, when
  the completeness pass names that claim and the words beside the figure agree. Not changed:
  the figure ledger itself (it is part of the completeness prompt — a change re-bills every pass).
- **Spending limits** (`budget.py`, `6c330dcc`). Run (scan $40 / batch $100), document ($30 or
  `--max-cost`), retries + completeness (85% of the document). Every call is BOUNDED before it is
  sent and refused if it does not fit (checkpoint BUDGET_HELD, resume without re-paying); the
  actual cost is recorded beside the bound. The $30 preflight estimate is kept.
- **Why long reviews resend the document; a cache shipped OFF** (`llm.py`, config
  `PROMPT_CACHE_PARTS = False`). Every completeness part resends the whole article.
- **Version dates** (`ArticleVersion.document_date`, `SourceRef.version_dates`). Each version
  keeps its own document's date and where it was read; a report up to 30 days before its page
  is ordinary (`VERSION_DATES_DIFFER`), anything else `PUBLICATION_DATE_CONFLICT` for review.
- **Found by this round's real runs and fixed**: a health action named the wrong page (Citi's
  LatAm page instead of its 96-word teaser) and printed "[PERSISTENT_FAILURE] Citi: " empty; the
  KPI strip said "Blocked sources: none" beside a health block counting two; a `state pull`
  replay recorded the private copy's hash as the upload's name and the replay time as its upload
  time.

**WHY.** The operator's brief (2026-10-11): seven approved publishers; the Delta error; the
Gridlock regulation card filed as a market regime; incomplete PDF verification; a $46.67 report
under a limit that was only an estimate; the GitHub path untested; LatAm's two dates.

**HOW VERIFIED.**

*Seven sources — live.* `sources --check-health` on a copy of the 2026-10-11 weekly registry
(12 historical BofA candidate rows, 1 BofA health record): **2 healthy / 3 degraded / 2 blocked
/ 0 errors of 7**, twice (14:25 and 14:29 UTC); every URL whose latest cached fetch is after
14:25 UTC is on the five automatic hosts (4 each) — **0 requests to BofA's host**; MS and GS not
re-requested inside their back-off. A $0 scan of the same registry (`--max-articles 0`): seven
coverage rows (MS, GS `MANUAL_FIRST`), the 12 BofA rows still UNDATED (never requeued), no BofA
on the dashboard. Fresh install: `init` + `sources` print seven (pinned).

*Citi, cached real reruns on the final code* (`final-a`, `final2-c`, `final-b2`; extraction and
completeness answers from the cache):

| report | theses | kinds | actions | open figures | open paragraphs | cost |
|---|---|---|---|---|---|---|
| Gridlock (60 pp) before | 16 | 14 thesis, 2 regime | 1 RN, 5 W, 10 S | 17 of 851 | 4 of 292 | (paid $46.67 earlier) |
| Gridlock after | 16 (same ids) | 16 thesis | 0 RN, 5 W, 11 S | **6 of 851** | 4 of 292 | $1.10 (reviews of the changed cards; then $0) |
| LatAm (57 pp) after | 14 | 14 thesis (3 corrected) | 8 W, 6 S | 1 of 319 | 0 of 208 | $0.22 (2 reviews) |
| ETF (34 pp + page) after | 1 | thesis | SKIP | **1 of 232** (was 5) | 0 of 144 | $0 |

Reassessment under the corrected type: "Uneven US regional power-market regulation…" RESEARCH
NOW → **SKIP** (rule SKIP-2 — the source shows no fundamental transmission step; its card says
listed earnings are UNKNOWN, a hypothesis to test); LatAm "Fiscal credibility and execution
dispersion…" WATCH → SKIP; "LatAm capex demand broadens…" stays SKIP. J.P. Morgan's calm-index
dispersion record stays a market regime, RESEARCH NOW (its evidence is implied correlation and
breadth; acceptance-pinned). Corpus what-if of the final rule over every pass-1 extraction in
`data/theme_intelligence/v2`: the J.P. Morgan and software-shock correlation records stay
regimes; one Nomura central-bank rates view (an older registry, not rerun) would flip.

Identity, every company mention in 7 real registries (95 mentions, re-resolved offline from the
cached SEC data): 4 corrections — Delta (DAL → UNRESOLVED), Siemens (no longer Siemens Energy),
Tencent (no longer Tencent Music), CBRE (ticker read without its quote marks); unchanged:
Amazon, Meta, Microsoft, NVIDIA, Bloom Energy, GE Vernova, Cummins, Caterpillar, Baker Hughes,
Constellation. Gridlock's DTM, WMB, KMI, TRP, MIR, Google and AWS stay UNRESOLVED (conservative
misses, not false matches); LatAm names two companies (Citi's Mexican entities, UNRESOLVED).

Verification materiality (after): Gridlock's six open figures — five on one infographic page
(p8, columns interleaved by the PDF text layer; "80% over five years", "24–48 months", "12–30+
months", "~$400 billion") whose facts the prose states and verified claims capture (b176, b183,
b185, b179), and "top-10" (a label); four paragraphs restate market risks the completeness pass
says are recorded, but a block review cannot cite a risk, so they stay open. LatAm's one is a
figure REFERENCE ("see Figure 23") the ledger read as a figure. ETF's one is a prior-year
"$10 trillion". No open item touches a RESEARCH NOW thesis. Fragmentation: no pair needed
merging; one overlap for a human (Gridlock's "four pillars" umbrella vs its transformer thesis).

Dates: LatAm page 2026-09-14 (page data) / report PDF 2026-09-10 (page 1-2) → both kept,
`VERSION_DATES_DIFFER` (4 days); ETF 2026-04-10 / 2026-04-08 (2 days).

*Completeness resend — measured* (Gridlock's paying run): 22 parts × 309,342–334,027 input
tokens, 7,130,969 in all = $35.65 of the pass's $39.44; prompt-cache tokens 0. The article
cache (same text, first block cached) on Citi's ETF report, one paid run each over the SAME
cached first-pass extraction:

| run | completeness cost | open figures | open paragraphs | claims the pass added | linked to the thesis |
|---|---|---|---|---|---|
| original, uncached | $2.586 | 1 of 252 | 0 of 162 | 46 | 66 |
| control, uncached (14:42 UTC) | $2.481 | 0 of 252 | 0 of 162 | 31 | 61 |
| cached (14:34 UTC) | $1.418 (−45%) | 2 of 252 | 0 of 162 | 26 | 55 |

Neither equivalence nor harm is shown: the cached run is lowest, inside a spread the two
uncached runs already show (15 added claims). Shipped OFF.

*Spend guard.* 44 paid calls in this correction run, none over its bound (largest 50% of it).

*GitHub state sync — the real private repository*, temporary branch
`theme-intelligence-state-test-20261011` (authorised by the brief; the production branch
`theme-intelligence-state` checked absent before and after), a SYNTHETIC registry (the labelled
synthetic fixtures; no licensed text), credentials from gh's active login through git's helper:

1. push from the "operator" machine → `4df9c5c` (fast-forward from nothing);
2. a FRESH directory pulls it: 1 run, 1 article, 1 thesis;
3. it imports the synthetic full report (`ingest-file --url`) → UPGRADED, $0.51;
4. push → `3f98095` (fast-forward);
5. the operator (stale) imports its own report ($0.31), push REFUSED ("the branch moved … run
   `state pull` first"), pull (backup, rebuild, replay of its import from cache) → push
   `11ba544`;
6. an Actions-style runner: fresh clone → `import-state` → a $0 scheduled-style scan (live
   discovery and health: 2/3/2 of 7, MS / GS MANUAL_FIRST): ONE weekly report covering the 4
   runs, both uploads listed "original NOT on this machine — its text is not re-verifiable
   here"; QA 22/22;
7. a raw rewind push of the branch → rejected by GitHub ("fetch first");
8. after the replay fix: the fresh directory (stale) imports the HTML edition ($0.47), push
   refused, pull — the branch holds the PDF edition and a pulled registry has no text, so the
   replay goes to REVIEW (never counted twice), keeping "ms_report_synthetic.html" and its
   15:03:13 arrival — push `2cf1f7e`; a second fresh runner restores it, QA 22/22;
9. the tree: 22 files, all JSONL; no PDF, HTML, synthetic page banner (article text), token,
   key or auth header; 0 article blocks carrying text;
10. thesis versions (v1 → v2, content hashes and prior links), article versions with their
    document dates, document records: identical on the operator machine and the runner;
11. re-checked vs carried: QA of the same upload run — on the importing machine before its
    pull, 11 of 12 claims re-checked against stored text (the 12th belongs to the version the
    branch delivered); on the runner 0 of 12 re-checked, 12 listed "NOT re-checkable here …
    never counted as re-verified".

*Mutation.* 19 for the round's earlier commits (16 killed at first; the 3 survivors were gaps
in the tests, pinned in `819cb375`, then killed); dates 9; verification checks 18 (the commit
message of `f022bff0` says 19 — the count on the final code is 18: one surviving condition
was removed as redundant, one new mutant added and killed); record kind 3; health output 5;
article cache 8; replay provenance 3; KPI 1 — every one killed.

**BOUNDARY.** Live checks: 2026-10-11 14:25–15:13 UTC, the seven configured channels, the
honest User-Agent. Citi reruns: three public Citi GPS reports, cached answers from the
2026-10-11 paying runs, code at `1a998700`. Open-item counts: one completeness ledger per
article version (figures as the ledger reads them). Identity: company / private-company
mentions in the registries hybrid-a, hybrid-c, hybrid-b2, contradiction-17, overlap-17,
hybrid-d, weekly-17, as of each article's run. Correction-run cost: **$7.33 measured** —
provider-reported usage × list price, every run started after 2026-10-11 13:00 UTC counted once
across 14 registries and two pre-pull backups (7 paying runs); the guard's pre-call bounds
summed $30.39 (an estimate, never the bill).

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- The article cache is OFF: long reviews keep costing what Gridlock cost. Falsifier for
  turning it on: three or more paired runs where the cached outcome stays inside the uncached
  spread.
- A `state pull` replaces a local document run with its replay; the original's paid-call
  records survive only in the pre-pull backup, so the branch under-reports that spend (seen:
  $0.31 and $0.47 here). OPEN.
- The figure ledger reads "2,358.5GVA" as "2,358" and "see Figure | | ; | 23" as a figure;
  fixing it changes the completeness prompt and re-bills every pass. OPEN, recorded.
- A block review cannot name a market risk, so a paragraph that restates a recorded risk stays
  open (Gridlock: 4). OPEN.
- The spend guard is a bound from the request's size, not a provider billing cap.
- On the test branch, D-737cf809's record carries the hash as its name and the replay time —
  written by the replay before the fix; later replays keep both. The branch is left for review;
  delete with `git push origin --delete theme-intelligence-state-test-20261011`.
- The token file (`~/.mosaic_gh_token`) is now refused for git operations too ("Invalid
  username or token"); gh's active login worked.
- Not merged; the production weekly schedule is not enabled.
