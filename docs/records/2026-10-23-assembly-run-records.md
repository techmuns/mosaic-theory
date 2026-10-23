---
id: 2026-10-23-assembly-run-records
status: shipped
date: 2026-10-23
prs: [791]
supersedes:
superseded-by:
---

# Every dossier build leaves a record of what it cost and what it produced, and the shared LLM client's token counts are now per thread

**WHAT.** `vinci dossier` (via `assemble_cohort`) writes one JSON line per name ATTEMPTED to
`data/snapshots/assembly_runs/<UTC start>-<run id>.jsonl` — one new file per run, so two
worktrees never conflict on one file. `data/snapshots/` is already committed. Each line holds:

- the outcome: `written`, `refused` (the build's own guards) or `failed`;
- every LLM call, with its phase (the tool name), whether it succeeded, any error, and its token
  usage;
- the token totals, and the list-price cost in USD;
- the synthesis lean and the five-draw tally;
- the counts of caveats and QA flags.

The console prints one line per name and the run's total. The shape contract and one literal
example are in `vinci/dossier/run_metrics.py`.

Supporting changes:

- **A meter per name.** `vinci.graph.llm.MeteredLlmClient` wraps the client for one name. It counts
  a call that raises (a truncated or malformed tool call is billed), and passes the request through
  unchanged.
- **One price table.** `cost_usd` prices a call from `vinci.config.LLM_PRICE_PER_MTOK`. That table
  moved there from theme intelligence's config, which now imports it, so there is one price list,
  not two.
- **The artifact pass commits the run files.** CLAUDE.md's ARTIFACT-PASS RULE and RUNBOOKS step 6
  now say so; otherwise the series would never reach the repo.

**WHY.** This is Stage 0 of the 2026-10-22 agentic-engineering research report. Before any loop may
change a prompt or an extractor, the process it changes has to be measured, and the report asks for
two weeks of unbroken series first. Nothing kept it:

- token counts lived on the client for one call at a time;
- synthesis read them only to judge its own cache, and dropped them for a draw that raised;
- `llm_call.log` is git-ignored;
- only theme intelligence, which has its own ledger, priced its calls.

**FOUND ON THE WAY — A RACE, FIXED.** `AnthropicLlmClient` kept `last_usage` in a plain attribute,
while `assemble_cohort` runs up to eight names at once on ONE client. A thread could therefore read
another thread's token counts, and synthesis's cache-expiry check reads exactly that value. It is
now per thread. A call that gets no response clears it, so it can never report the previous call's
count. Both are pinned on the real client with only its transport swapped. The race pin fails on
the old code: the mutant that restores a shared attribute is killed by it.

**AND A SUBCLASS THAT COPIED IT.** Moving the slot broke theme intelligence's `ThemeLlmClient`,
which sends its own split-cache request and wrote the old attribute in a copied block. The
full suite caught it: 2 of `tests/test_theme_intelligence_prompt_cache.py`'s pins read
`last_usage` as `None`. Both clients now record through one base method
(`_record_usage`), and the theme client clears the slot before its call as the base does.

**HOW VERIFIED.**

- **A real assembly of LLY** with `claude-opus-4-8`, on 2026-10-23 from 13:26:31Z to 13:38:55Z
  (744.5 s). Prices were a copy of a store with bars through 2026-10-16, and the CIQ exports a copy
  of the operator's folder. Console:

  ```
  === dossier · 1 done · 0 error(s) · → data/dossiers/<ticker>/ ===
  --- what each build cost and produced → data/snapshots/assembly_runs/2026-10-23T13-26-31Z-48110ac2.jsonl
    LLY    written  7 call(s), 0 failed · $2.27 · lean strongly-bullish
    total $2.27 over 1 of 1 name(s)
  ```

  - The record has 7 calls: `maturity_event` 1, `operating_drivers` 1, `assemble_dossier_framing` 5.
  - The first synthesis draw wrote 187,584 tokens to the prompt cache, and each of the other four
    read them back.
  - Totals: 12,822 uncached input, 26,353 output, 187,584 cache-write and 750,336 cache-read
    tokens, which is **$2.270503** at list price.
- **Checked against an independent record:** the synthesis writes its own per-draw usage to
  `llm_call.log`. All 5 draws match the meter's numbers on all four token fields, and the USD
  recomputed from the totals at $5/$25 per million tokens equals the record's.
- **What the record caught on its first run.** The committed LLY page has a unanimous 5-of-5
  strongly-bullish synthesis. This rebuild drew **4 strongly-bullish and 1 mixed**, so its machine
  proposal would be withheld. That is the reproducibility signal the series exists to accumulate.
  The rebuilt page, the run file and the copied inputs were NOT committed: this is a code PR, and
  the series starts with the first artifact pass after merge.
- **`tests/test_run_metrics.py`, 12 pins:**
  - per-thread usage, and no stale usage;
  - the meter counting a call that raises, and passing requests through unchanged;
  - list price, and unknown cost recorded as unknown, never zero;
  - one shared price table;
  - end to end through the real `assemble_cohort` (offline, temp config) on the committed LLY
    dossier: a written build and a refused one, each read back from the file the run wrote;
  - a build with no LLM recorded as costing nothing;
  - a lost record reported as an error, with the dossier kept;
  - a long error saying it was cut;
  - the console total counting every name.
- **Mutants: 14 of 14 killed.** One survived the first draft of the tests (unmetered calls counted
  as metered), and an added pin killed it.
- **This change's own review** (`/code-review high --fix`) found 5 issues and fixed 2, each pinned:
  - an interrupted call (Ctrl-C) was recorded as a success;
  - the end-to-end pin named one living dossier, and now picks one from the corpus.
  The other 3 are the boundaries below.

**BOUNDARY.**

- **The real run:** one name (LLY), one run, 2026-10-23. Prices: the
  `research-alpha-audit-bcba59` worktree's store, bars through 2026-10-16. CIQ: the operator's
  LLY folder as of 2026-09-22.
- **The cost:** list price from `LLM_PRICE_PER_MTOK` (cached 2026-10-06), not the invoice.
- **The draw counts:** five draws on this build only — a tally, not a rate.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **NOT COVERED: other LLM callers.** These use the same client and are not yet recorded: graph
  extraction and judging (`vinci graph …`), rank-cause classification, and the themes commands.
  Theme intelligence keeps its own per-call ledger.
- **NOT COVERED: the dossier refresh path.** It makes no LLM call, so it writes no record.
- **The series exists only if artifact passes commit it** (CLAUDE.md ARTIFACT-PASS RULE, RUNBOOKS
  step 6). A pass that forgets leaves a gap no later run can fill.
- **A record is a measurement, not an invoice.** `usd` is list price over metered calls only, with
  `unmetered_calls` beside it.
- **Two cost functions still share one formula:** theme intelligence's `cost_of` and the new
  `cost_usd`. The price table they read is now one table. Merging the functions is left for a
  build that touches theme intelligence on purpose.
