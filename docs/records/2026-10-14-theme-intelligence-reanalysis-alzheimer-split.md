---
id: 2026-10-14-theme-intelligence-reanalysis-alzheimer-split
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — re-analysis of articles already held; the Alzheimer thesis split; the pilot budget raised to $25

**WHAT.** Operator, 2026-10-14: "build the re-analysis path and split the Alzheimer thesis, and
increase pilot budget to $25".

1. **Re-analysis** (`Pipeline.run_reanalyse`, `reanalyse`). Articles already held are analysed
   again under the current taxonomy and prompts, from their stored text (no fetch), through the
   same pipeline as an upload: extraction, completeness, verification, the engine, card reviews.
   - **Retire only what it fully replaces.** Every thesis named to RETIRE must hold evidence from
     the listed articles only; otherwise nothing is done. Retiring it would drop evidence no
     re-analysis restores.
   - **Retired, kept.** A retired thesis is archived with a `RETIRED` event giving the reason,
     and its key is tagged with the run, which frees the bare key. Its versions, links and
     history stay. The engine never matches, updates or reactivates it again: not by key, not by
     its key's id, not as an article's earlier thesis, and not in a relation. A new thesis whose
     key-derived id is the retired one's gets a new, deterministic id, never overwriting it.
   - **The extractor no longer sees it.** Retired theses are outside its registry context.
   - **A record already stored is kept.** A claim or mention whose content id is already stored
     is kept as first written: the id hashes the content, so an id never means two things.
   - **Enriched.** The theses the re-analysis creates or changes are enriched.
   - **Read as archived everywhere.** Every status reader treats `RETIRED` as archiving
     (`report.ARCHIVING`): the desk, the weekly report's categories and the card's status line.
2. **The split, on the pilot registry** (`R-20261014T110419Z-reanalyse`, $2.6315). Re-analysed:
   "3 Biotech Industry Trends" (14 Sep), "Healthcare Industry Trends Powering Growth Beyond 2026"
   (18 Sep) and "Healthcare Consumerism" (29 Sep). Retired: the four theses built only from them,
   all keyed `healthcare`:
   - TH-BF20FBC464 — Alzheimer's, Research Now, 34 items from all three articles;
   - TH-1D5A6AD90E — AI tools;
   - TH-2E2C6735DB — policy;
   - TH-7C43904AA3 — China biotech.

   | New thesis | Key | Action | Evidence from |
   |---|---|---|---|
   | TH-8DDD7B2868 Alzheimer's innovation unlocks a $70bn drug market | pharma & biotech · neurology | **Watch** | the Alzheimer article only (5 items) |
   | TH-A097D4722F Direct-to-consumer cash-pay unlocks a $26B biopharma opportunity | pharma & biotech · direct-to-consumer | Watch | the consumerism article only (10) |
   | TH-1B06ACA0B7 AI picks-and-shovels enablers monetize drug-discovery productivity | life-science tools | Watch | the biotech article (10) |
   | TH-DEB6560D7F Robust healthcare utilization sustains demand | health services & payers | Watch | the conference (5) and consumerism (6) articles |
   | TH-F6906B89B0 Easing US policy uncertainty lifts healthcare investment | healthcare (broad) | Watch | the conference article (5) |
   | TH-62BBF1F71E China's biotech innovation: partnership and competitive risk | pharma & biotech | Skip | the conference article (4) |
   | TH-DEE87FCF51 In-vivo gene editing opens new organ markets | pharma & biotech | Skip | the biotech article (7) |
   | TH-62BA09949E AI adoption shortens drug development | healthcare (broad) | Skip | the conference article (4) |

   **The Alzheimer thesis is now Watch, not Research Now.** On its own evidence it has no
   verified mispricing or dated catalyst (F7 absent; the other conditions are met). The merged
   thesis's catalyst came from the conference article: a different economic story. So that
   Research Now rested on another thesis's evidence — the contamination the split removes.
   Enrichment proposes Eli Lilly (LLY), Biogen (BIIB) and Lantheus (LNTH) for it, plus Eisai
   (not SEC-verified); for the cash-pay thesis, Eli Lilly, Pfizer (PFE), Hims & Hers (HIMS) and
   Novo Nordisk (a foreign filer's US line).

   Two theses took a retired thesis's former bare key: the broad AI-adoption thesis took
   TH-1D5A6AD90E's, and the policy thesis took TH-2E2C6735DB's. Both got new ids, as designed.
3. **The pilot budget is $25** (was $18).

**WHY.** The Alzheimer thesis had absorbed a cash-pay piece and a GLP-1 conference piece because
all three were keyed `healthcare`. The sub-categories and segments
(`docs/records/2026-10-14-theme-intelligence-weekly-enrichment-healthcare.md`) fix new articles,
not the theses already merged.

**HOW VERIFIED.**
- **The real run** (above), then QA on it: 18 of 20 pass after its outputs were rendered to the
  run's own folder. The two failures appear on these articles' ORIGINAL runs too, so they are
  data conditions, not regressions: one argument paragraph of the biotech article is unaccounted
  for, and the conference article names no author.
- **What the real run caught, and its fix.** The first publish showed the desk with "23 active ·
  0 archived": the four retired theses were listed active, the Alzheimer one at Research Now.
  The status readers knew only `ARCHIVED`; they now read `RETIRED` too. After that the desk
  shows **19 active · 4 archived**, and the retired thesis's page says "Retired — re-analysed".
- **Pins** (`tests/test_theme_intelligence_reanalysis.py`, hypothetical articles in the real
  extraction type):
  - a merged thesis is split into a neurology thesis (its article only) and a direct-to-consumer
    thesis (its article only), the retired one untouched (2 versions, an event);
  - a hypothesis on the retired thesis's bare key makes a NEW thesis with a NEW id;
  - a claim whose content was already stored is kept;
  - the retired thesis is archived as of the run, its page says retired, and Themes reads "3
    active · 1 archived";
  - NEGATIVE: a thesis holding evidence from an article not re-analysed is never retired, and
    nothing changes.
  - **Mutants: 7 of 7 killed:** the key, the id, claim reuse, the evidence check, the earlier
    theses, the already-applied bypass, and `RETIRED` read as archiving.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- Pilot registry `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` (the
  `theme-intelligence` worktree). Backup before the run:
  `backups/registry-pre-reanalyse-20261014.db`.
- Item counts are the thesis-claim links of each thesis, read 2026-10-14 after the run.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $2.6315.
- **The pilot has spent $15.4533 in its registry (116 paid calls), plus $2.4002 in the two scratch
  demo registries: $17.8535 of $25.**
- **History stays:** the retired theses keep their versions and evidence, readable from the
  archive.
- **One merge remains** (health services & payers, two articles), plausibly one thesis about
  services demand. It is recorded, not undone.
- The re-analysed articles' earlier claims stay in the registry beside the new ones. Only
  identical content is shared; nothing earlier is edited.
