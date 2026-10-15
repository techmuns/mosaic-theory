---
id: 2026-10-15-theme-intelligence-enrichment-condition-and-basis
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — enrichment proposals say their CONDITION and a CHECKED BASIS

**WHAT.** Operator, 2026-10-15, on the demo enrichment of J.P. Morgan's "Software Shock" (Twilio
and Atlassian proposed as "hurt"): "how do you know if Atlassian (TEAM), Twilio (TWLO) will be hurt
or benefited?" The answer was: the direction is the model's, and nothing checks it. Two options were
offered. Operator: "do both options as one PR".

| Option | What it does |
|---|---|
| **1. The condition** | Every proposal records the label of the card step it rests on (`step_label`), capped as every card line is: a line saying what could happen is at most the source's opinion. A step that is not a fact (the source's opinion, a forecast, our inference) makes the direction a CONDITION. Such a proposal is shown under **"Exposed — the direction holds only if its step does"**, as "exposed — would be hurt IF this holds: “<the step's words>” (source opinion)", and never under "Could be hurt". This applies on the thesis page, the card, its print and its markdown. Only a step that is measured or externally verified keeps "Could benefit / Could be hurt". A set stored before this change reads its step's label from the card version it was proposed from. If that card's step is not the recorded one, the label is never guessed: "its support was not recorded". |
| **2. The checkable basis** | The model now states how the company earns from the exposed line (`revenue_model`: subscription, usage-based, transaction fees, licences, product sales, advertising, services, other) and which line it is (`revenue_line`). Both are required by the tool, and the prompt version is `ti-enrich-2`. The basis is checked against the company's OWN latest annual report (10-K / 20-F / 40-F, never an amendment) filed on or before the as-of, read through the same SEC resolver and cache as the listing check, with filings cached for good. The check finds the filing's own revenue-source sentences ("We derive our revenues from …", "Our revenue is primarily derived from …") and compares the ways of earning they name with the one stated. **IN_FILING**: the sentence names it, and also lists the other ways it names. **FILING_NAMES_OTHER**: it names others, not this one. **NOT_DESCRIBED**: no such sentence in these words. **UNCHECKED**: nothing could be read, and the note says why. The quote starts at the filing's own words; a section title glued on by the text layer is dropped. The sentence is shown on demand on the page and in full on the printed card. A registrant the SEC identity check refused is never read. |

**THE DESIGN THAT WAS MEASURED AND REFUSED.** The first design searched the whole 10-K for each
model's words. On the 13 real filings of the demo's first proposals (`ti-enrich-1`), it confirmed
almost anything:
- Adobe matched 5 of 7 models;
- Salesforce's "per seat" hit was a sentence about attrition;
- most SaaS filings "confirmed" usage-based through a minor AI add-on.

Reading only the filing's own revenue-source sentences fixed this. It found one naming a way of
earning for 10 of the 13; AMD, Broadcom and Vertiv state none in these words.

**DOES THIS SELECT ON FORM?** Yes. The basis check reads a disclosure, so NOT_DESCRIBED or
FILING_NAMES_OTHER is a statement about the filing's words, never about the business.
- It removes, ranks and decides nothing. No priority rule reads enrichment (pinned since #703).
- The filing's sentence is shown beside the proposal for the analyst to read.

The condition selects on the card's provenance labels, which already govern every card line. It is
not a gate either: it changes the words shown, never what is proposed or what any rule reads.

**WHY.** A bare "could be hurt" on a step that is the source's opinion reads as our finding. A
company's direction resting on a guess about how it earns was unverifiable on the page.

**HOW VERIFIED.**
- **Real run** (the demo registry, J.P. Morgan's "Software Shock", as of 2026-02-09; $0.1195 for 3
  paid calls, then replays from the cache at $0). 16 proposals across 3 theses:
  - **every one** rests on a step that is not a fact (10 model inference, 4 source opinion, 2
    forecast), so all show as conditions;
  - **13 IN_FILING**:
    - **Twilio** stated usage-based. Its 10-K: "Our revenue is primarily derived from usage-based
      fees, which can lead to variability …". This sits beside "would be hurt IF agentic AI
      threatens SaaS domains (source opinion)";
    - **Intuit** is IN_FILING for subscription "— and also transaction fees": its sentence lists
      subscription once among many, and the note says so;
  - **3 NOT_DESCRIBED** (AMD, Broadcom, Micron).
- **Stored data** (every enrichment set under the `theme-intelligence` worktree's
  `data/theme_intelligence/`; 109 distinct proposals, all in the pilot registry):
  - **107 rest on a step that is not a fact**: 61 source opinion, 28 model inference, 18 forecast;
  - **2 rest on a measured observation**;
  - so when the desk is next published, 107 of 109 change from "Could benefit / be hurt" to
    "Exposed — … IF".
  - Stored sets carry no basis, so they show none until they are enriched again (a paid call per
    thesis).
- **A bug the real run caught:** the stated revenue model was first held in a variable named
  `model`, which overwrote the LLM model's name. The set recorded "usage_based" as its model and
  the call's cost as UNKNOWN. It was renamed and pinned.
- **Pins:** `tests/test_theme_intelligence_enrichment_basis.py`, 13 tests; the filing sentences
  are verbatim from the real 10-Ks named in the file.
  - On main the module cannot import (none of these functions exist), so all 13 fail.
  - One existing pin in `test_theme_intelligence_enrichment.py` changed its words on purpose:
    Amazon rests on an inference step and now reads as a condition.
- **Mutants: 20 of 20 killed.** An unmutated baseline passes. One survived the first pass, the
  capping of a stored card's step label; a pin with a pre-capping card now sees it.
- **Preview** (from the real demo run): the thesis page's box as served, with the filing's words
  opened, and the card's print state. The images are in
  `docs/theme_intelligence/enrichment-basis-2026-10-15/screenshots/`.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.**
- Code: main c2872114 against this branch, 2026-10-15.
- Real run: `data/theme_intelligence/demo-2026-10-15-fixes` (git-ignored), runs
  R-20261015T145548Z-enrich (paid) to R-20261015T150249Z-enrich.
- Stored-data counts: proposals distinct by `enrichment_id` over every `registry.db` under the
  `theme-intelligence` worktree's `data/theme_intelligence/` (backups excluded); each label is read
  from the card version its set rests on.
- Filings are the SEC's, read through the resolver's cache.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.1195 of model spend (one paid enrichment of 3 theses), plus SEC requests: one annual report
  per verified proposal, cached for good.
- **The vocabulary is ours.** A filing that says "member fees" for a subscription reads
  NOT_DESCRIBED. That is shown as such and never acted on.
- **"Names" is not "mainly".** A list sentence that names a model once counts as IN_FILING, so the
  note lists everything else the sentence names, and the quote is beside it.
- **Every proposal costs an annual-report read** the first time (1–5 MB per filing; then cached).
- **`vinci.graph.filings.html_to_text` is duplicated** as `securities.filing_text`: the package
  may import only shared plumbing (test_theme_intelligence_isolation).
- The thesis page's filing quote is on-demand (a closed `<details>`). Its complete printed record
  is the card (`cards/*.print.html`), whose print rule reveals it.
