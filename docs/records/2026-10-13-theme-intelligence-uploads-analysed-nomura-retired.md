---
id: 2026-10-13-theme-intelligence-uploads-analysed-nomura-retired
status: recorded
date: 2026-10-13
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the operator's three uploads analysed ($2.7458), and Nomura retired

**WHAT.**
- **Three supplied PDFs analysed into the pilot registry** at the operator's instruction
  (2026-10-13). The operator gave the reason: these PDF downloads are the publishers' official and
  only route. Each was imported with `--llm-permitted` on that instruction, after a backup
  (`backups/registry-20261013T155105Z.db`).

  | Document | Run | Cost | Imported as | Result |
  |---|---|---|---|---|
  | Citi — "Money: The Evolution to Digital" | `R-20261013T155116Z-ingest` | $0.3468 | a new article, read in full | 14 figures, 10 captured; the analysis proposed no thesis |
  | SemiAnalysis — "Are Open Models Catching Up?" | `R-20261013T155240Z-ingest` | $0.689 | a new article, a **preview** (the PDF ends with the subscriber notice) | new thesis `TH-38CA111885`, "Open models catch up to frontier faster each era, risking model-layer commoditization" (WATCH) |
  | SemiAnalysis — "Beijing Will Not Pace the Frontier" | `R-20261013T155548Z-ingest` | $1.71 | `--same-as A-5bfa8fff567e`: a new version of the article already held, still a preview | new thesis `TH-2651327A9B`, "China's frontier-safety governance is decided by leadership, not experts or binding rules" (SKIP); contradicting evidence added to `TH-38CA111885` (version 2) |

  - **The "Money" date.** The PDF prints no date. It was recorded as **2024-10-30**, the date
    Citi's own page states (as read by the 2026-10-12 health check's sample of that page). It is
    labelled operator-stated because the document is silent.
  - **The "Beijing" re-read.** On 2026-10-12 the same text proposed no thesis; this read proposed
    two (one becoming a thesis, one evidence against another). That is model run-to-run variance
    on near-identical text, not new material.
- **Nomura retired** (operator decision 2026-10-13: "stop requesting Nomura's portal-only reports
  and remove nomura from our sources list altogether"). Its full reports sit on the client portal
  (go.nomuranow.com), which offers no public sign-up, so they could never be supplied. It follows
  the Bank of America precedent (2026-10-11):
  - a named `[[retired]]` entry in `sources.toml`, with hosts `nomuraconnects.com` and
    `nomuranow.com` (its site and its portal);
  - its discovery adapter (`nomura_articles`) removed;
  - no discovery, health check, upload request or new import (a Nomura document, or any
    document claiming a Nomura address, is refused before it is read);
  - its two articles and the thesis it created (`TH-2FFD9B58A8`) stay in the registry as history;
  - the **desk** now follows the weekly report's rule (`report.research_intake`): Uploads never
    asks for a retired channel's preview, document or blocked page. Articles lists the history
    with "Not requested — Nomura retired 13 Oct 2026", where it said "Supply the full report".
  - Six active publishers remain: Citi, J.P. Morgan, TrendForce and SemiAnalysis automatic;
    Morgan Stanley and Goldman Sachs manual-first.

**WHY.** The operator's decisions on the three open items of
`docs/records/2026-10-13-theme-intelligence-columns-and-uploads.md`. The desk's Uploads list had
never applied the report's retired-channel rule. No retired channel left a preview in the 12 Oct
pilot until Nomura, so the gap was unseen; retiring Nomura exposed it.

**HOW VERIFIED.**
- **Real runs.** The three runs above, each SUCCEEDED, with the cost each recorded.
- **The rendered desk from a copy of the updated registry:**
  - Uploads and Sources carry no Nomura;
  - "Money" and "Open Models" read "supplied and analysed" on their sources' requests;
  - the two SemiAnalysis previews stay on "Full report needed" (they are previews);
  - "Faster, Slower, Then Steady" says "Not requested — Nomura retired 13 Oct 2026";
  - 0 broken links and 0 default-view problems over 24 pages;
  - no horizontal overflow on five routes at 1440 and 390 px.
- **Pins** (`tests/test_theme_intelligence_seven_sources.py`):
  - exactly six active channels; BofA and Nomura retired with their hosts; both adapters gone;
  - Nomura refused by source and by host (its site and its portal);
  - a preview Nomura left in the registry is never requested on Uploads and says "Not requested"
    on Articles, while an active channel's preview is still requested (negative).
  - Mutants: the Uploads filter and the Articles follow-up, 2 of 2 killed.
- **Tests that used Nomura only as an example** now use an active channel or a test-local source
  with the shared `generic_listing` adapter:
  - a request channel's linked report is never fetched;
  - an operator-verified date;
  - an undated page bounded by its last modification;
  - the intake's undated row;
  - the health checks' channel count (7 → 6).
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- **Pilot registry:** `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` in the
  `theme-intelligence` worktree. Before these runs: 23 model calls, $4.3345. After: 36 calls,
  $7.0803. Measured from its `llm_calls` on 2026-10-13, against the $18 pilot budget.
- **Figures and propositions:** the completeness ledgers the three runs recorded.
- **"24 pages":** the standalone render of the updated registry's latest run
  (`R-20261013T155548Z-ingest`), 2026-10-13.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $2.7458 of model spend (list price, as recorded per call).
- **OPEN, the operator's:** both SemiAnalysis requests stay open on Uploads, because both PDFs
  are previews. A paid SemiAnalysis subscription would supply the full posts. Without one, those
  requests can never be met, the same position Nomura was in. Whether to stop requesting
  SemiAnalysis's full posts (keeping SemiAnalysis as a source) is the operator's call; not built.
- "Money" is a 2024 report: its figures are dated two years before the analysis.
