---
id:
status: shipped
date: 2026-10-10
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence, review corrections — a whole-article ledger and a market-regime record keep every argument; labels say what a line IS; near-term is a calendar test; listings are point-in-time

**WHAT.** The PR #703 review accepted the architecture and rejected the analysis. Corrections, all
in `vinci/theme_intelligence/` (still off the decision path, AST-pinned):

- **Whole-article completeness (P0.1 / P1.7).** `completeness.py` builds a ledger from the article
  TEXT before any model output is read — every figure a body block states (sign and unit kept;
  years, tenors such as "200-day" and numbers inside names such as "S&P 500" are not figures) and
  every argument paragraph — then a second, independent model pass (`ti-complete-1`) re-reads the
  whole article beside the first pass's record and must account for each gap: add the missed
  claim / mention / thesis / regime record, attach evidence to an existing thesis, or call the gap
  immaterial WITH A REASON. Its additions are verified like pass 1. Each figure ends captured /
  added by the completeness pass / immaterial / uncaptured; an uncaptured figure or unaccounted
  paragraph is a WARN issue, a dashboard caveat and a failing QA check. Persisted in an
  append-only `completeness` table (migration v2).
- **Market-regime records (P0.1).** `ThesisKind.MARKET_REGIME`: a market-structure condition the
  article measures (breadth, correlation, dispersion) plus the research OPPORTUNITY it draws —
  no named stock, no earnings mechanism, never forced into a buy thesis, never dropped for naming
  no stock. A market-structure RISK stays a market risk. New mechanism `dispersion_selection`.
- **Research Now without a ticker (P0.2).** The exposure condition is a point-in-time-verified
  listed common equity OR a sector / theme the source names (a verified span containing the name).
  The source's stated role of a company stays apart from the thesis's reading of it, each labelled.
- **Point-in-time securities (P0.3).** A company's exposure lines are the common-equity lines on
  the inline-XBRL cover page of its latest 10-K / 10-Q / 20-F / 40-F filed on or before the as-of
  date; preferred / depositary-preferred / debt lines are kept for audit with their class; a
  current-map ticker absent from that cover is NOT_REGISTERED_AS_OF (UNVERIFIED when an 8-A12B
  falls in between, or when no cover can be read — and then it never counts as an exposure).
- **Labels and transmission (P0.4).** SOURCE OPINION / MEASURED OBSERVATION / FORECAST / MODEL
  INFERENCE / EXTERNALLY VERIFIED replace ARTICLE FACT (kept only for legacy records); a line
  carries the WEAKEST label of the claims it cites. A share-price / valuation / index move is a
  `market_reaction` step, never counted as an earnings mechanism; a step filed otherwise that only
  describes a price move is re-filed and logged.
- **Near term is a calendar test (P0.5).** `timewindow.py` reads each claim's stated window; a
  forecast or event counts only when its window starts within a year and ends within ~18 months
  of the as-of, a measured observation only when dated within a quarter. The model's horizon
  label is recorded, never decisive. A dislocation must be a mispricing measured in the last
  quarter and a catalyst a dated event inside the window.
- **Authors (P1.6).** The union of JSON-LD, schema.org/Person microdata, meta author and the
  visible byline (multi-line titles joined), plus people the TEXT credits as verified spans; a
  JSON-LD list missing a credited author is recorded (AUTHOR_METADATA_DISCREPANCY). Also: the
  publication date from the page's OWN Next.js page-data entry (Citi), matched by URL.
- **Re-anchor before withholding (P1.8).** A non-verbatim quote is re-anchored to the one
  verbatim sentence carrying its figure and sharing its words TWO-SIDEDLY; a rejected card line is
  re-cited to the reviewer's suggested spans, a verified claim carrying its numbers or words, or —
  only when an LLM reviewer will judge it again — the verbatim passage (minted as SOURCE OPINION
  evidence), then reviewed once more. A MODEL INFERENCE line is never re-anchored. Every claim a
  card cites is linked to its thesis.
- **Readability (P2).** Dashboard KPIs in plain words (accessible / blocked sources BY NAME,
  articles analysed full vs partial, Research Now / Watch / Skip, new / upgraded / downgraded /
  challenged, figures not yet captured); article date and first-detected date apart ("new to the
  registry" never "new to the market"); engine codes, ids, change classes and rule traces behind
  one audit toggle (print shows all) — registry ids inside a card line included; the card opens
  on a compact decision view, nine sections unchanged. The KPIs count the theses THIS RUN created
  or changed and its events (a SKIP is archived at once, and still counts; a thesis new this run
  can also be challenged in it), each tile stating that population.
- **Over-long articles.** A truncated extraction is retried ONCE in a declared compact mode (at
  most 25 claims; the completeness pass then re-reads the article), the truncation remembered so a
  replay never re-pays it, its cost recorded, and the issue EXTRACTION_COMPACT raised. The output
  cap rose to the SDK's non-streaming ceiling, 21,333 tokens. The completeness pass reviews more
  than 50 open gaps in PARTS (COMPLETENESS_IN_PARTS), each shown what the earlier parts added and
  skipped if they already covered its gaps; a part that overruns is split once (the discarded call
  recorded at its cost), a half that overruns again fails loud.
- **Malformed answers.** Model answers are validated ITEM BY ITEM: an item failing its schema is
  dropped and named (MALFORMED_ITEM_DROPPED), never coerced; every valid item is kept; the paid
  answer is cached before validation. An extraction whose TOP level fails is set aside
  (`<key>.invalid-N.json`, kept for the record) and the identical request asked ONCE more
  (ANSWER_SET_ASIDE, its cost recorded); a second failure fails loud with both calls costed.
  Nothing is repaired or decoded into shape. A pass-1b addition naming no hypothesis of the
  article — silently skipped before — is now reported the same way.
- **Numbers are read through ONE shared helper** (`stated_numbers` / `word_numbers`): a number
  hyphen-joined to a capitalised name is part of the name ("GLM-5.3", "COVID-19"); "twenty-four"
  is one number; "doubling" states ×2 (or +100%); the ledger reads word ranges ("three-four
  months"), unit-glued figures ("75GW", "930MW", "744B") and the "99th percentile"; a figure
  prints its unit once ("~43%", never "~43% %").
- **Publisher of a feed-host URL.** A URL is matched on every host a channel is configured with
  (entry, listing, sitemap, feed): SemiAnalysis posts on newsletter.semianalysis.com were filed
  "UNKNOWN publisher".
- **Each publisher's contribution on the card.** The article that creates a version shows its own
  contribution class on the sources line (it had fallen back to "initial record" for every
  update), and a COMPETING link says what the rule found — the same node, with the two mechanisms
  named — instead of claiming "same node and mechanism".

**WHY.** The review: the calm-index article produced only a utilities thesis and lost its central
dispersion argument; Research Now demanded a ticker even for a sector opportunity; Alphabet's
mapping carried GOOGM / GOOGN into a February 2026 record; a falling share price was counted as an
earnings mechanism and a publisher's interpretation labelled as fact; a long-range forecast passed
as near-term; Nick Roberts was missing; completeness was checked only against the claims the first
model chose. The real runs of this round then exposed the further defects listed under HOW
VERIFIED — each found on real pages, none anticipated.

**HOW VERIFIED.** Real runs on the final code (`5c9f3b9a`), one FRESH registry per case, model
answers content-cached (a replay costs nothing). Worked output: `docs/theme_intelligence/`.

- *J.P. Morgan "Software Shock", as of 2026-02-09:* exactly three theses — software sell-off
  oversold (WATCH: the premise is conditional in the source), AI infrastructure swept up (WATCH:
  its only offered dislocation is a rhetorical question, a SOURCE OPINION — RESEARCH NOW in the
  first build), AI-adopter margins (WATCH). Ledger: 34 figures — 13 captured by pass 1, 1 added by
  pass 1b, 20 immaterial with a reason, 0 open; 12 argument blocks — 11 anchored, 1 immaterial. The
  "99th percentile" correlation is captured (`C-1d705296dc93cb`) and stays a market risk. Alphabet:
  GOOGL (Class A Common) and GOOG (Class C Capital) VERIFIED from the cover of the 10-K filed
  2026-02-05 (0001652044-26-000018); GOOGM / GOOGN NOT_REGISTERED_AS_OF. QA 19/19.
- *J.P. Morgan "A calm index, a restless market", as of 2026-10-10:* the market-regime record
  (`macro_market` / `dispersion_selection`) and the utilities thesis (`power_grid` /
  `policy_regulation` / negative), both RESEARCH NOW on observations dated 2026-09-30 / 10-02.
  Ledger: 19 figures — 16 captured, 3 immaterial, 0 open: ~43% (`C-a97bbb9aa2d733`), 75%
  (`C-a8e001324178a8`), 11.2 (`C-61a7adf78143ca`), 41 (`C-61a7adf78143ca`, `C-b141683e305af8`).
  Authors Kriti Gupta and Nick Roberts — JSON-LD lists only the first, the byline's
  schema.org/Person items both (AUTHOR_METADATA_DISCREPANCY recorded). QA 19/19. Open issues kept
  visible: an entity the text never names dropped (BLOCK), a sector span not naming "utilities"
  dropped (WARN), one "what could go wrong" line withheld as unsupported (BLOCK).
- *Two publishers, one thesis (real):* SemiAnalysis "Inside GLM-5.3: How Sparse Attention Affects
  DRAM Memory TAM" (2026-09-28, a paid post — preview only, PARTIAL) creates "Sparse attention does
  not reduce overall AI memory capacity demand" (`ai_infrastructure.memory` /
  `demand_volume_shift`); TrendForce "AI Server Demand Sustains Memory Contract Price Increases in
  4Q26, While Consumer-Side Pressure Persists" (2026-09-30) independently confirms it — the SAME
  thesis id, version 2, 6 new claims from an origin the thesis did not hold, evidence STRONGER;
  each publisher keeps its own source line (authors, date, origins: SemiAnalysis InferenceX vs
  TrendForce's own analysis; "initial record" vs "new evidence"). TrendForce's pricing argument is
  a SIBLING (same node, `pricing_cycle`), its weak-consumer argument a separate SKIP thesis. Two
  figures stay open on the SemiAnalysis article ("GLM's 5.2 / 5.3 model"): pass 1b named claim
  k1_2 as capturing them, k1_2 verified but does not quote them — coverage is re-derived from
  verified quotes, never taken from the model's verdict. QA 18/19 (that open pair) and 19/19.
- *Contradictory evidence (real):* SemiAnalysis "Everyone Says Datacenter Moratoriums Are Killing
  the US Buildout…" (2026-09-15, PARTIAL) — "Grid friction pushes datacenters behind-the-meter"
  (`power_grid`, positive) and "Datacenter moratoriums barely dent the US AI buildout pipeline"
  (`datacenter_physical`); then J.P. Morgan (2026-10-02). The utilities thesis (`power_grid`,
  negative) is COMPETING with the behind-the-meter thesis: never merged, its supporting claims
  linked as CONTRADICTS (version 2, WEAKER, event CHALLENGED), the J.P. Morgan source line marked
  "contradicts the thesis", the card stating the basis — the same node, DIFFERENT mechanisms
  (`demand_volume_shift` vs `policy_regulation`). Read on its merits the challenge is weak: the
  two theses address different segments of the node (behind-the-meter suppliers vs grid-tied
  utilities), and two of the five claims filed against it are price moves. The rule is the first
  build's (its acceptance case pairs two mechanisms); it is left as an operator decision — STATE
  §5.0 row 32 (8)(b). QA 18/19 (one paragraph left unaccounted, visible) and 19/19.
- *The weekly sample, reprocessed from scratch:* `scan --from 2026-10-01 --to 2026-10-10
  --as-of 2026-10-10` into a fresh registry — 6 of 8 channels reachable (Morgan Stanley: robots.txt
  unreachable → fail closed; Goldman Sachs: HTTP 403 — BLOCKED, never bypassed); 6 dated articles
  in the window, the first build's sample (TrendForce ×2, SemiAnalysis ×2 — PARTIAL previews,
  Nomura, J.P. Morgan), plus 13 undated pages counted and never placed. 192 claims extracted, 192
  span-verified; ledger 228 figures, 3 open; 61 claims and 1 thesis added by pass 1b; 10 theses
  created, 2 versions added by challenges (one SemiAnalysis thesis challenged by two theses of one
  article → v3 — the case that had stopped the run). KPIs: Research Now / Watch / Skip 2 / 7 / 1;
  new / upgraded / downgraded / challenged 10 / 0 / 0 / 1. Item-level validation dropped 2
  malformed items; the parts path ran on 2 long articles. QA 18/20 — 3 figures ("42 … 22 (52%)")
  and 2 paragraphs left open by pass 1b, listed, never hidden.
- *Defects the real runs of this round exposed, each fixed, pinned and mutation-checked:*
  (1) one mention typed "other" discarded a whole paid extraction → item-level validation;
  (2) the completeness pass over a long post (124 open figures + 91 paragraphs) overran the output
  cap → parts of at most 50; (3) SemiAnalysis URLs filed "UNKNOWN publisher" → every configured
  host; (4) "GLM-5.3" read as a figure (blocked a bottom line, 8 false ledger figures), "doubling"
  failing its number check, "three-four months" split, "75GW" / "744B" / "99th percentile" missed,
  "(1)…(5)" read as figures → one shared number reading; (5) "~43% %" and "15–20% % QoQ" → a unit
  printed once; (6) `hypotheses` returned as broken JSON text — twice, on two long SemiAnalysis
  extractions — failed the article and reported $0 → set aside and asked once more, both
  recovered, costs recorded; (7) an update's source line showed "initial record" → the current
  contribution; (8) a COMPETING line claimed "same node and mechanism" → the basis as found;
  (9) one article challenging a thesis twice stopped the weekly run (duplicate contribution id) →
  one id per challenger; (10) the KPI strip showed "Skip 0" (a SKIP is archived at once) and
  "challenged 0" (a thesis created and challenged in one run sits under NEW) → counts over this
  run's theses and events, each tile stating its population; (11) thesis / article ids in the
  first view of challenged cards → behind the audit toggle.
- *Tests and mutants:* new files `test_theme_intelligence_long_articles.py` (21 items) and
  `test_theme_intelligence_numbers.py` (22), plus pins in the corrections / calm-index / overlap
  files. Mutation runs on the final code: 25 of the 26 review-correction guards killed — the
  survivor (`passage-needs-llm-review`) is EQUIVALENT in practice: FACT_WITHOUT_CLAIM was raised 0
  times in the 32 registries of this round's runs (27 REVIEW_UNSUPPORTED, 16
  NUMBER_NOT_IN_CITED_CLAIMS), because a line citing no verified claim is labelled MODEL INFERENCE
  by composition; 39 of 39 for this round's fixes (one more, a "third ask", was equivalent — the
  loop raises on the second — and was replaced by a mutant of the raise itself). Gate: `ruff check vinci tests frontend` clean; `mypy --strict vinci` clean (176 files); `pytest -m "not network"` 4,575 passed, 507 skipped, 37 deselected, 0 failed — on the final tree (`5c9f3b9a` plus the worked output, fixtures and docs committed with it).

**BOUNDARY.** Runs: commit `5c9f3b9a`, 2026-10-10; model `claude-opus-4-8`; prompts
`ti-extract-6` / `ti-complete-1` / `ti-review-4`; each article replayed AS OF the date shown.
Ledger counts: figures are the numbers the article BODY states (sign and unit kept; unit-glued
figures, counted periods and ranges in words, a percentile) — not years, tenors, days of a month,
numbers inside names, or list markers; approximate levels in words ("the mid 40s") and multiplier
words ("doubled") are NOT ledger figures (multipliers are verified when a claim states them);
argument blocks are paragraphs / list items of ≥ 12 words; "open" = neither captured by a verified
claim nor judged immaterial with a reason. SemiAnalysis posts: public preview only (PARTIAL).
Weekly: window 2026-10-01 → 2026-10-10, as-of 2026-10-10, the eight configured channels as
reachable on 2026-10-10 with the honest User-Agent; "discovered" = unique canonical URLs a
channel's listing / feed / page data exposed; "in window" = source-stated date inside the window.
Costs at list price ($5 / $25 per million input / output tokens); "paid calls" = files in the
shared content-keyed model cache — every answer, truncation marker and set-aside answer is one
billed call, a replay writes none — plus the calls listed below as leaving no file.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Model spend of this round: **$21.14 across 138 calls that left a cache file** (1,737,926 input /
  498,084 output tokens; extraction 19 + 2 set aside + 1 overrun, completeness 27, card review 89),
  **plus ≈ $1.7 for three calls that left none** — two SemiAnalysis extractions that overran the
  cap before the compact retry existed (≈ 16k and ≈ 21k output tokens), one moratoriums answer
  lost to the old whole-answer check — **plus up to two calls killed in flight** when I stopped
  runs to fix a defect (cost unknown, at most ≈ $1.2): ≈ $22.8–24 in all.
- The completeness pass and the card review are LLM judgements, checked deterministically where
  they can be (every addition re-verified; an "immaterial" verdict needs a reason; coverage
  re-derived from verified quotes). Their open gaps are listed, never resolved by fiat.
- OPERATOR DECISIONS (STATE §5.0 row 32 (8)): (a) whether a qualitative "swept up in the
  sell-off" observation may count as a dislocation — today it may not, so AI infrastructure is
  WATCH; falsifier: analysts repeatedly promote such theses by hand. (b) whether a challenger that
  shares only the value-chain NODE may weaken a thesis — today it does (the case above); falsifier:
  most CHALLENGED events on review turn out to address another segment of the node → split the
  node or require the same mechanism.
- The market-regime record's exposure line is the source's own words ("at both a sector and
  thematic level"), not a named sector — accepted as what the article claims; falsifier: an
  analyst cannot tell where to look → require the source to name a sector.
- Numbers written as version strings in prose ("GLM's 5.2 / 5.3 model") remain ledger figures:
  telling them from figures needs judgement, so they stay open and visible rather than skipped by
  a guess.
