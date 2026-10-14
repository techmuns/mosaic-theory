---
id: 2026-10-14-theme-intelligence-weekly-enrichment-healthcare
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — enrichment in the weekly scan; Emerson's identity; healthcare's sub-categories and pharma's segments

**WHAT.** Three operator decisions, 2026-10-14:
- "yes add enrichment to the weekly run";
- "build Healthcare sub-categories";
- "Emerson electric is a software/automation company and not electrical-equipment company".

1. **Enrichment in the weekly scan** (`pipeline.run_scan`). Both weekly wrappers (the laptop
   script and the Actions workflow) call `scan`, so the scan itself now ends with the enrichment
   step:
   - over every active thesis whose current version has no set — the theses the week created or
     changed, and any a manual run left;
   - inside the scan's own run, so its calls are on the scan's bill and the week's desk and report
     carry the proposals;
   - after the archive pass, so archived theses are skipped;
   - a refusal by the spend guard, or a missing model, is a run WARNING, never a failed scan;
   - `scan --no-enrich` opts out.

   Measured cost: $0.4685 for 15 theses, about $0.03 each (`R-20261014T100846Z-enrich`).
2. **Emerson's identity** (`securities._COMPATIBLE`). A software description is compatible with
   an industrial or electrical-equipment issuer. Industrial automation is sold as software, and
   the SEC's industry code lags the business: Emerson is still filed under SIC 3600 (electrical
   equipment). Its enrichment proposal now resolves to EMR (re-check `R-20261014T103521Z-enrich`,
   $0, from the cache).
3. **Healthcare's four sub-categories** (`config/taxonomy.toml`), added, never renamed:
   - pharma & biotech;
   - life-science tools;
   - medtech & diagnostics;
   - health services & payers.

   Each has a short desk name. The four theses already keyed at `healthcare` keep their keys.
4. **Pharma's segments**, added after the first real run showed the children alone were not
   enough:
   - neurology (Alzheimer's, dementia);
   - obesity & metabolic (GLP-1);
   - oncology;
   - direct-to-consumer / cash-pay.

   Segments are read from the hypothesis's own statement and verified quotes, never from the
   model's choice, and never sent to it. A therapy area and a sales channel are different claims.

**WHY.**
- Enrichment answers who is exposed only if it runs each week.
- The industry-code veto refused a company the operator knows to be an automation-software
  business.
- With one healthcare node, every article arguing rising US healthcare demand shared one thesis
  key: the pilot's Alzheimer thesis absorbed a cash-pay care-delivery piece and a GLP-1
  conference piece (`docs/records/2026-10-14-theme-intelligence-exposure-and-thesis-page.md`).

**HOW VERIFIED.**
- **Real runs, in two fresh scratch registries** — not the pilot. Each ingested the Alzheimer
  article ("3 Biotech Industry Trends", 14 Sep) and then the consumerism article that
  contaminated it (29 Sep):
  - **Children only** (`R-20261014T104013Z-ingest` $0.8394, `R-20261014T104332Z-ingest`
    $0.5316): a partial split. The consumerism piece made its own health-services thesis, and
    the AI-tools thesis moved to life-science tools. But a "$26bn biopharma direct-to-consumer
    cash-pay" hypothesis still put **12 items onto the Alzheimer thesis**, now keyed pharma &
    biotech with the same mechanism, direction and geography.
  - **Children and segments** (`R-20261014T104659Z-ingest` $0.4267, `R-20261014T104817Z-ingest`
    $0.6025): **the split is complete.** Alzheimer's drugs (pharma & biotech · neurology) holds 8
    items, all from the Alzheimer article. Direct-to-consumer cash pay (pharma & biotech ·
    direct-to-consumer) holds 13, all from the consumerism article. AI drug-discovery tools sit
    under life-science tools; consumer choice in care delivery under health services & payers.
- **Corpus before synthetic — Emerson's widening.** Every stored mention in every local registry
  was resolved by the old and the new resolver, offline: **4,793 (registry, mention) pairs over
  146 registries; 0 changed** (79 not re-resolvable offline). Its only effect is on the
  enrichment proposals.
- **Pins** (positive and negative each):
  - the scan enriches inside its own run (one call, purpose `enrich`), and a scan with
    enrichment off asks nothing;
  - the `scan` command turns the step on, and `--no-enrich` off;
  - Emerson with a software description resolves to EMR, while a software description still is
    not an airline;
  - the children are in the extractor's node menu, and a drug-market and a care-payment thesis
    are two active theses, while a second drug-market article updates the first;
  - neurology and direct-to-consumer are two pharma theses, while a second Alzheimer article
    updates the neurology one.
  - **Mutants: 5 of 5 killed:** the scan hook, the CLI flag, the identity widening, the children
    (both their pins fail without them), and the direct-to-consumer segment.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- The demo registries are scratch copies, discarded: they prove the keys; the pilot registry is
  unchanged by them.
- "4,793 pairs / 146 registries": the `theme-intelligence` worktree's `data/theme_intelligence/`,
  every `registry.db` but backups, each with its own SEC cache, read 2026-10-14.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$2.4002 of model spend** for the two demo registries ($1.371 + $1.0292), outside the pilot
  registry's ledger and counted toward the pilot budget. With the registry's $12.8218, **the pilot
  has spent $15.2220 of $18**.
- **A wrong prediction, recorded.** I expected the second demo to replay its answers at about
  $0, but it cost $1.0292. The extraction prompt lists the theses already in the registry, and
  their keys now carry segments; the card reviews name thesis ids, which changed. Neither was a
  cache hit.
- **The pilot's four `healthcare` theses keep their keys**, so the Alzheimer thesis (TH-BF20FBC464,
  Research Now) stays merged. Splitting it needs its three articles analysed again under the new
  taxonomy: about $2–2.5 at the demo's per-article cost, against $2.78 left. That would also
  need a path that re-analyses an article already held, which does not exist (the same file is a
  duplicate). Recorded open for the operator.
- Segments exist for pharma & biotech only, where the collision was observed. The other children
  have none until one is shown to be needed.
