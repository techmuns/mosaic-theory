---
id: 2026-10-14-theme-intelligence-exposure-and-thesis-page
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — who is exposed, by direction; two wrong tickers; the thesis page re-read; the four audit findings fixed

**WHAT.** At the operator's request (2026-10-14), three parts:
- "cross check the 'Who is exposed' section, is it showing the potential beneficiaries or
  potential adversaries? and is it even extracting the right public company names/tickers …
  diagnose deeply";
- re-read TH-188B31F187 and TH-BF20FBC464 for readability, "each section individually and as a
  whole";
- "fix the issues as per your audit" — the four findings of
  `docs/records/2026-10-14-theme-intelligence-tabs-audit.md`.

**Diagnosis — who is exposed** (pilot registry copy at `R-20261014T070200Z-ingest`):
- **The section showed neither beneficiaries nor adversaries.** It listed names only. The
  direction the card holds for each name and sector (the source's role, the thesis's reading,
  positive / negative) was dropped on the desk.
- **The sources name almost no companies.** 13 articles carry 109 mentions:
  - **0 potential beneficiaries**;
  - **2 potentially harmed**, both private (OpenAI, Anthropic);
  - the rest are publishers, data sources, context and examples.

  A sweep of the article text for likely names (memory makers, Alzheimer's drug makers, energy-drink
  makers and others) and for company suffixes found nothing the extractor missed. The six Morgan
  Stanley pages name no company but Morgan Stanley; TrendForce's HBM note names no memory maker.
- **0 of 15 current theses name a US-listed company as an exposure.** The only listed company on
  any thesis's list was **Morgan Stanley, the publisher**, on the Alzheimer thesis
  (TH-BF20FBC464). 12 of 15 name sectors: 31 lines, 25 that could benefit, 3 that could be hurt,
  3 with no direction.
- **The priority rules were not misled.** They count only exposure roles (`EXPOSURE_ROLES`), so
  the publisher never raised a research action. Three surfaces did not filter:
  - the desk's section;
  - the card's "Stock exposures" table;
  - the weekly report's names.
- **Two wrong tickers.** Of 15 listed-equity resolutions in the pilot:
  - the 13 that verified the model's ticker hint are right;
  - the 2 made by registrant-name prefix are wrong. "Citi" (hint C, Citigroup) resolved to
    **Citi Trends (CTRN)**, an apparel retailer: the hint's registrant is not named "Citi…", so
    every registrant was searched by prefix and the hint ignored. "Cognition" (classified private;
    the AI lab behind Devin) resolved to **Cognition Therapeutics (CGTX)**: its description names
    no industry the SIC check could veto.
- **The Alzheimer thesis has absorbed other articles.** Theses are keyed node · mechanism ·
  direction · geography, and **healthcare has no sub-nodes** (AI infrastructure has eight). So
  `healthcare|demand_volume_shift|positive|US` took in the healthcare-consumerism piece (12
  supporting items) and the conference piece (6 supporting, 1 catalyst). Its next step, risks,
  sectors and some figures are about direct-to-consumer cash pay and GLP-1, not Alzheimer's.
- **A company the theme implies is never proposed.** The schema has a separately labelled
  "enrichment" list for that (`EnrichmentCandidate`, an external hypothesis, never in the source
  lists). Nothing builds one: not found under the constructor, "enrich" in the pipeline, engine,
  CLI and guide, `git log -i --grep=enrich`, or `git log -S"EnrichmentCandidate("` (only the
  original build).

**Fixed (render-time unless stated; nothing stored changed):**
- **Who is exposed** (`desk.exposure_html`; one split for every surface, `cards.exposures_of`):
  - three groups — **Could benefit**, **Could be hurt**, **Named as exposed — direction not
    stated** — companies and sectors together;
  - each company with its ticker, or why it has none (private; no verified US listing; a listing
    not verified point-in-time), and what the source says of it;
  - the publisher, data sources and context are excluded and counted on an "also named" line;
  - when no listed company is named, the section says so, and that a name the source does not
    state is never added;
  - the card's exposure table and the weekly report's names use the same split.
- **The resolver** (`securities.py`; affects new resolutions only — data path):
  - a valid SEC hint naming one issuer now blocks a prefix match to a different business
    (unresolved, both names stated), while one corporate family stays one ("Entergy Louisiana",
    hint ETR);
  - a company the extraction classed private is matched only by the registrant's exact name.
- **The thesis page:**
  - the order now follows a decision: the thesis; why and what next; who is exposed beside what
    could prove it wrong; the figures; the mechanism beside what changed;
  - the strongest figures lead with what the thesis statement cites (the Alzheimer page led with a
    gene-editing market);
  - plain words: "8 checks passed" (was "8 conditions met"); "a recent mispricing" (was "a
    dislocation" — `priority.py`: "a mispricing measured in the last quarter"); "newest evidence
    published … · on the desk since …" (was "first seen … last material update");
  - "what changed" says since when the action stands ("Research Now since version 2, raised from
    Watch");
  - a thesis filed at an area's root (the taxonomy has two levels) is "parent" of every thesis in
    the area. That link moves to the broader-area fold; Canada's power thesis had listed HBM
    pricing as related.
- **The Evidence tab:**
  - "$413 $/year … · per year" reads "$413 per year" (`unit_shown`);
  - a figure the article states twice for one measure is one line ("stated 2 times", both quotes);
    another year or measure never merges.
- **The four audit findings:**
  1. **The weekly report's Sources** say each channel's state in words, from the checks'
     structured tests: "partly working", "the site refuses automated access; a known restriction —
     supply its research by upload". The words come from one shared helper,
     `health.plain_line`, which the desk's Sources use too. The raw reasons stay in Operations &
     audit.
  2. **The card's "At a glance"** is one closed fold on screen and left out of the print, where
     it only repeated the sections (operator, 2026-10-14). This reverses the 2026-10-12 redesign's
     open placement; the test pin says so.
  3. **Titles:** a trailing site part that repeats the publisher ("… | Morgan Stanley") is dropped
     by the importer and on every screen (`parse.clean_title`, which also decodes "&#039;").
  4. **Overprinted PDF glyphs are read once** (`documents.py`: pdfplumber `dedupe_chars`; reader
     version `ti-parse-8`): "Need more energy 666111%%%" reads "61%".

**WHY.** For a fund the section exists to say who wins and who loses. It said neither, and it
printed the publisher as the one listed name. The wrong tickers would have reached a card the day
either company was named as an exposure.

**HOW VERIFIED.**
- **Corpus before synthetic:**
  - *Reader:* every real PDF at hand (83: the local registries' documents, the operator's supplied
    PDFs, the scratch copies and the fixtures) was read with and without the de-duplication.
    **6 changed, every change a correction:** the Caffeine page in three copies; VRSK
    "vveerriisskk..ccoomm" → "verisk.com"; "yeear"/"deecade" → "year"/"decade" in an asset-class
    returns note; ServiceNow's twice-printed footer page numbers printed once. 77 unchanged.
  - *Resolver:* every stored mention in every local registry with an SEC cache was resolved by the
    old and the new resolver, offline. **4,790 (registry, mention) pairs across 146 registries; 80
    not re-resolvable offline. 15 changed, every one a correction:** Citi→CTRN (1), Cognition→CGTX
    (13), xAI from ambiguous to unresolved (1). Listed-equity 914 → 900; no correct listing lost.
    A first version also refused "Entergy Louisiana" (hint ETR); the family exception came from
    that run.
- **Pins** (positive and negative each):
  - who is exposed, end to end on a hypothetical article with the authentic frozen SEC subset:
    Micron under "Could benefit" with MU and Microsoft under "Could be hurt" with MSFT; FactSet,
    named as the data source but carried in the thesis's list, sits in no group — on the reading
    page, the card's exposure table and the weekly report;
  - the thesis-cited figure leads; a figure stated twice is one line, while another year stays
    apart;
  - "$413 per year", and a title without its site suffix on Articles, the reading page and the
    card (the unit and title helpers each with a negative case);
  - a root-node link is folded, while a thesis sharing a source stays listed;
  - the weekly report's Sources carry no raw reason or state code, and Operations still does;
  - the glance is folded on screen and absent from the print;
  - the resolver: Citi unresolved, Citigroup resolves to C, Entergy Louisiana not refused;
    Cognition unresolved, "Cognition Therapeutics" resolves, a company-typed "Cognition" keeps the
    designed match;
  - an overprinted label is read once, while repeated digits (1100) stay; the importer drops a
    site suffix that repeats the channel's publisher and keeps one that does not.
  - Two existing pins were updated deliberately: the reading page's exposure selector (`.expo`),
    and the scan pin's "manual-first" wording (now "by upload only"; the coded form is checked
    still in the KPI).
  - **Mutants: 15 of 15 killed** (10 render, 3 resolver, 1 reader, 1 importer).
- **The live local preview** (the pilot registry published, not committed): on TH-BF20FBC464, TH-188B31F187 and TH-38CA111885, each section was read alone and the page as a whole. Before
  and after were rendered from the same registry (HEAD's code against this change).
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- Counts of theses, mentions and resolutions are from the copy of the pilot registry at
  `R-20261014T070200Z-ingest`, read 2026-10-14.
- "83 PDFs" and "146 registries" are the `theme-intelligence` worktree's
  `data/theme_intelligence/` (every `registry.db` but backups, each with its own SEC cache), the
  scratch copies, `/Users/work/Downloads` and the fixtures, read 2026-10-14.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **Stored records keep what they hold until re-read.** The Caffeine article's seven open figures
  still read "666111%" until it is analysed again with the fixed reader (about $0.68 at its first
  run's cost; the operator's call). The two wrong tickers sit on stored cards, never as exposures,
  until those articles are re-resolved.
- **Reported, not fixed — decisions for the operator:**
  - healthcare has no sub-nodes, so unrelated healthcare articles merge into one thesis. A
    taxonomy change re-keys theses: it touches the decision path;
  - proposing listed companies a theme implies (the enrichment step) is designed but not built.
    It would be a new, labelled model step with its own cost;
  - foreign issuers filing 20-F (Alibaba, Baidu) are not resolved to their US ADRs, by design;
    "Google" does not resolve to Alphabet;
  - some sector lines are extraction noise: "biotech" from an analyst's job title, "seven
    sectors", "large-cap productivity gains".
