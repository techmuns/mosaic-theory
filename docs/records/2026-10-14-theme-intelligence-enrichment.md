---
id: 2026-10-14-theme-intelligence-enrichment
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the enrichment step (the companies a thesis implies, as our hypothesis); the Caffeine article re-read

**WHAT.** Operator, 2026-10-14: "yes re-analyse Caffeine, and build the enrichment step". Both
answer `docs/records/2026-10-14-theme-intelligence-exposure-and-thesis-page.md`, which found that
the sources name almost no companies: 0 of 15 theses named a US-listed exposure.

1. **The Caffeine article, re-read by the fixed reader** (`ti-parse-8`), with `ingest-file
   --reread`. The same file becomes a new version of the same article; the earlier version and its
   analysis are kept.
   - Run `R-20261014T095734Z-ingest`, $0.7336.
   - The new version `AV-8809a3db245c41dc` holds 36 figures, **0 open**. The old one held 37,
     with 7 open and garbled ("666111%").
   - "61% — need more energy" is captured and verified.
   - The energy-drink thesis TH-16225B12C4 gained version 2: Watch, 9 new items, 16 repeated.
   - Review's open items went from 21 in 6 articles to 14 in 5.
2. **The enrichment step** (`vinci/theme_intelligence/enrich.py`, the `enrich` command). For
   each thesis, the model proposes the US-listed companies its OWN steps to earnings reach. A
   design slot for this (`EnrichmentCandidate`) existed but was never built.
   - **Input:** the card's own lines only — statement, the `s03` steps, the sectors and business
     groups the source names, the companies it already names. Never the article's text (pinned).
   - **Output per company:** the step it moves through, benefit or hurt, how (at most 30 words),
     and what the company does. The shape contract and one literal example are in the prompt.
   - **Checked, deterministically:**
     - the step must be one of the card's steps to earnings (a market reaction is not one);
     - a company the source already names is never proposed again;
     - at most four on each side;
     - a thesis with no stated step is not sent.
   - **Every name goes through the SAME SEC resolution as a source-named company:** identity
     before ticker, then point-in-time common equity. A ticker the SEC does not verify is never
     shown as one. The page says "not verified by the SEC", or, for an ADR or cross-listing,
     "the US line of a foreign filer, not checked point-in-time" (from the SEC's own filing
     forms, a structured flag).
   - **Stored apart.** A new append-only table `enrichments` (schema v5): one set per pass over
     one thesis version, with what validation set aside and why. It is never written into the
     sealed thesis version. **No priority rule reads it:** pinned by test, and `engine.py` and
     `priority.py` do not mention it.
   - **Shown labelled:**
     - on the reading page, a dashed box under "Who is exposed": "Companies the thesis implies —
       our hypothesis", split into could benefit / could be hurt, each with ticker, step and how;
     - on the card, in section 05's existing "Enrichment — external hypotheses" slot, and in its
       Markdown and JSON.

     A set proposed for an earlier version says so.
   - **Cost:** one call per thesis through the spend guard, cached by exact request (a re-check
     costs $0). `--refresh` asks again.
   - **Does this select on form?** No. It is not a gate and decides nothing. It proposes by the
     mechanism the thesis states, not by how a filing discloses. **Accepted risk:** a model's
     recall favours familiar large companies. The prompt asks for companies to whom the step is
     material, and the analyst checks each one.

**HOW VERIFIED.**
- **The real pass** over the pilot registry: `R-20261014T100846Z-enrich`, 15 theses, $0.4685.
  - **72 proposals:** 51 could benefit, 21 could be hurt.
  - **19 set aside:** 17 over four on a side, 2 proposed twice.
  - **Every proposal was read.** Examples: HBM pricing → Micron (MU), SK hynix, Applied
    Materials (AMAT) and Lam Research (LRCX) could benefit, NVIDIA (NVDA) and AMD could be hurt;
    Alzheimer's → Eli Lilly (LLY) and Biogen (BIIB); energy drinks → Monster (MNST) and Celsius
    (CELH).
- **What reading the first pass changed:**
  - **The identity check now reads what the company does, never the mechanism's words.** A drug
    "pipeline" had read as oil and gas and refused Merck, and "nuclear power demand" refused two
    uranium miners.
  - **Foreign filers' US lines are said so.** Cameco, Novo Nordisk, Icon and eight others had
    read "not verified".
  - **A refusal's reason is always shown.**
  - **A ticker is listed once** (it had shown "CP, CP").
- **The re-check** `R-20261014T101431Z-enrich` ($0, all 15 answers from the cache) re-resolved
  every name: **55 with a verified US listing, 11 foreign filers' US lines, 6 unverified**, each
  with its reason. Merck now resolves to MRK.
- **Pins** (`tests/test_theme_intelligence_enrichment.py`; a hypothetical article, the authentic
  frozen SEC subset, a model stand-in answering in the real tool's shape):
  - kept, resolved and rendered (Amazon → AMZN; ASML as a foreign filer's US line);
  - set aside: a name the source already names, a step the card does not hold;
  - the request carries the thesis lines and no article text;
  - shown only in the hypothesis box, never in the source's groups or the card's stock-exposure
    table;
  - no new thesis version and the same research action; a second pass skipped, and `--refresh`
    answered from the cache;
  - no call for a thesis without a step; the table refuses an UPDATE;
  - identity reads the business, on Merck's real SEC record (SIC 2834): the pharma description
    resolves to MRK, while "oil pipeline operator" is refused.
  - **Mutants: 8 of 8 killed.**
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- Pilot registry `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` (the
  `theme-intelligence` worktree), read 2026-10-14.
- Spend: $11.6196 before these runs; **$12.8218 of the $18 pilot budget after**, over 87 paid
  calls.
- "72 proposals" etc. are the latest set of each of the 15 theses after the re-check run.
- Backups: `backups/registry-20261014T095734Z.db` (before the re-read) and
  `backups/registry-pre-v5-20261014.db` (before the schema moved to v5).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $1.2021 of model spend ($0.7336 re-read + $0.4685 enrichment).
- **Reported, not fixed:**
  - Emerson Electric is still refused identity. The model described it with "software", which
    the existing industry table does not allow for an electrical-equipment issuer (SIC 3600).
    Widening that table would change how source-named companies resolve too.
  - SK hynix's US ticker (HXSCL) is not SEC-verified, and Roche and Coherus do not resolve;
    each is shown with its reason.
- **Open (operator):** enrichment runs on demand (`enrich`), not yet inside the weekly run.
  Adding it to the weekly wrapper after the scan would cost about $0.03 per new or changed thesis.
