---
id: 2026-10-05-pending-after-the-forward-multiples
status: open
date: 2026-10-05
prs: [664]
supersedes:
superseded-by:
---

# What is still open after the forward-multiple work, and a costed proposal to cache the draws

**WHAT.** The operator actions left standing by #651–#663, recorded so they live in the repo rather
than in a chat transcript (OPERATOR-ACTION RULE), plus one new proposal — prompt caching on the
synthesis draws — measured on real call logs and awaiting a decision. Nothing here is built.

## The operator actions

1. **The normalized-EPS basis ruling** (opened in #663). `EPS (Normalized)` is 0.44–0.93× GAAP in
   the 6 LTM columns and 0.97–1.06× in all 13 estimate columns of the 7 names carrying forward
   multiples — two bases under one label. Name the basis on the row, or drop the normalized
   estimate rows as ≤6% duplicates of GAAP. The same render ruling should label `P/LTM EPS`, which
   is struck on GAAP LTM EPS and says so nowhere (open since #659). Unresolved in the same
   column: AMZN's FY26E net income $140,097M exceeds its FY26E EBIT $109,863M with no gain
   modeled — CIQ's own figure, faithfully extracted. Full measurement:
   `docs/records/2026-09-30-six-pages-onto-the-forward-multiples.md`.
2. **BURL's scenario record — the review's blocking issue.** The exit-date NTM denominator,
   Base/HPR/IRR and the roll-vs-re-rating split live in a scenario record, and BURL has none.
   `vinci scenario-propose BURL` pre-fills 3 of 9 cells (base revenue $12,825.8M, margin 7.478%,
   multiple 12.82x, leg_fy 2027) and refuses 6 with their reasons: the bear and bull legs, and
   `years_to_terminal`. `entry_basis` and `entry_denominator` are also empty, and they are the two
   fields that make `basis_decomposition` (computable since #660, rendered nowhere) produce the
   split the review asked for. Unlock: analyst inputs.
3. **Refresh prices before anyone underwrites off the seven forward-multiple pages.** AMZN, BURL,
   LLY, NFLX, NKE, ROST, TGT are all struck on the 2026-09-22 close, 8 days stale at build — kept
   deliberately so #663 compared like-for-like against 2026-09-28. Every multiple moves on a
   `vinci refresh` + re-assembly.
4. **GitHub Actions billing — nothing CI-validated since #652.** The `gate` workflow has failed on
   "recent account payments have failed" since #652; #652–#663 merged on local runs only. Recorded
   here because it was nowhere in STATE.md.
5. **WERN re-assembly — deferred by operator decision** (2026-09-29, "don't re-assemble wern for
   now"). Its page still carries the pre-#656 covenant heading.
6. **AMZN's CIQ bundle lacks the Credit Health Panel** (10 files vs 11 for every other name). Its
   credit fields read UNKNOWN, not wrong. Unlock: one more CIQ export.
7. **Decide on prompt caching for the synthesis draws** — below.

**§5.0 OPEN NOW is at its 60-line ceiling with zero headroom** (since #663). These seven are folded
into row 32, which #663 opened, rather than taking lines from anyone else's items. The next build
that opens an unrelated item must close a row first, or the operator raises the cap deliberately.

## The proposal: cache the five identical synthesis draws

**WHAT THE CONSOLE SAID** (2026-10-05): *"Prompt caching could save you up to $661 a month. Your
cache hit rate was 41% over the last 7 days."* That figure is computed over everything billed to
the org and cannot be decomposed from this repo. What CAN be stated: `vinci` sends **no
`cache_control` anywhere** — one call site, `vinci/graph/llm.py` `AnthropicLlmClient.extract` — so
its own traffic contributes **0%** to that 41%. The hits are coming from other traffic on the org.

**WHY THE DRAWS QUALIFY, from the code.** `synthesis.synthesize` builds `system`, `tool` and `user`
ONCE and calls `extract` five times in a plain `for` loop — **sequential, byte-identical**. That
is the textbook cache case, and it dodges the one trap that would void it: a cache entry is
readable only after the first response begins, so five PARALLEL identical calls would all pay full
price. These are not parallel.

**MEASURED, not estimated** — the `USAGE` lines in five real `llm_call.log` files (AMZN, BRBR, LLY,
NFLX, NKE; the #650 fleet pass of 2026-09-26; `claude-opus-4-8`; 25 calls):

    prompt per draw     112,815 – 211,653 tokens, IDENTICAL across all five draws of a name
    output per draw     ~4,000 – 4,700 tokens
    input share         97.2% of tokens, 87.4% of cost

At the live Opus 4.8 rates ($5 input, $6.25 5-minute write, $0.50 read, $25 output per MTok,
confirmed on the prompt-caching page 2026-10-05) — draw 1 writes the prompt, draws 2–5 read it:

    name   uncached   cached   saving
    AMZN    $5.79     $2.25    61.2%
    BRBR    $3.40     $1.51    55.5%
    LLY     $5.03     $2.02    59.9%
    NFLX    $3.84     $1.64    57.3%
    NKE     $3.51     $1.52    56.7%
    all    $21.57     $8.94    58.6%

**Input cost falls 67%** (5× → 1.25× + 4×0.10×); output is untouched. Mean **$4.31 → $1.79 of
SYNTHESIS per name** — synthesis only; see the correction below before reading it as a per-name
total.

**IT DOES NOT CHANGE A SINGLE OUTPUT TOKEN — and for this fund that is the question that matters**,
because the five-draw gate exists to MEASURE draw variance. The prompt-caching page states it
plainly: *"Prompt caching has no effect on output token generation."* The draws remain independent
samples; the gate's statistics are unaffected. Caching reprices the prefix; it does not reuse an
answer.

**SIDE BENEFITS.** Cache reads do not count against input-token rate limits, so fleet passes get
headroom; and draws 2–5 skip re-processing a ~200K-token prompt, so they start faster.

**IT SAVES DOLLARS, NOT TOKENS.** The same tokens are processed; the repeated ones bill at a tenth.

**THREE WAYS TO GET IT WRONG, each with a measured or documented cost:**

- **Caching every call.** A prompt that is never re-sent pays the 1.25× write for nothing — a 25%
  SURCHARGE. Every single-draw phase (graph extraction, theme phases) is that case. Cache ONLY when
  the same prompt is about to be re-sent: `draws > 1`.
- **Running the draws in parallel later** to save wall-clock. That silently voids the cache.
- **Breaking the log.** With caching, `usage.input_tokens` becomes the UNCACHED REMAINDER — a few
  tokens on draws 2–5. `last_usage` records only `input_tokens` and `output_tokens` today, and its
  docstring exists so that "(likely truncated)" can be CHECKED against real prompt size. It must
  also record `cache_creation_input_tokens` and `cache_read_input_tokens`, or every log after the
  change reports a 200K prompt as 3 tokens.

## Second pass, same day — three blind spots in the first

**1. "Per name" was synthesis only — an assembly makes up to five more calls caching cannot touch.**
Each assembly also sends up to 4 covenant-exhibit extractions and 1 transcript-driver extraction,
each a DIFFERENT document sent ONCE, so there is no repeat to cache. Their text, read from the
local EDGAR cache: AMZN's four loan agreements are **1,273,366 chars**, NFLX 993,674, NKE 812,579,
BRBR 221,641, LLY none; transcripts ~24K chars each. ESTIMATED at 3.5–4.5 chars/token (prose —
the JSON synthesis prompt measures 2.45), synthesis is **69–99% of an assembly's input**, and the
saving per ASSEMBLY is:

    AMZN 46–49%   BRBR 50–51%   LLY 59–60%   NFLX 42–44%   NKE 42–45%

**42–60%, not 58.6%** — the 58.6% is the synthesis figure and stays correct as that.

**2. The scale is far below the Console's $661.** Committed 5-draw assemblies since the draw gate
merged (#648, 2026-09-26): **25, all between 2026-09-27 and 2026-09-30**, none since — a LOWER
BOUND, since probes and re-runs that never reach git cost the same. At the measured mean that
burst carried ~$108 of synthesis, ~$45 cached. A weekly 26-name fleet cadence would be ~$450/month
of synthesis, ~$185 cached — **a saving on the order of $250/month, not $661**. The rest of the
Console's figure is other traffic on the org, which this repo cannot see or change.

**3. The build is wider than one function.** 14 of the 18 duck-typed test fakes declare
`extract(self, *, system, user, tool)` exactly, and fakes reach multi-draw `synthesize` through
the assemble path — a new `cache` keyword raises `TypeError` in each until it is added.
`tests/test_graph.py` pins `last_usage` as exactly three keys, and will rightly redden when it
gains the cache fields. `assemble.py` runs NAMES concurrently on a `ThreadPoolExecutor`; each
name's draws stay sequential in its thread and names never share a prefix, so caching is
unaffected — but that pool is where a future "parallelise the draws" change would be tempting.

**Observed, separate, out of scope:** covenant extraction re-reads the SAME exhibits on every
re-assembly — AMZN's 2014–2023 loan agreements, ~300K tokens, every time. Memoising that is a
larger lever than draw caching on exhibit-heavy names, and a decision-path change (it reuses an
LLM extraction instead of drawing a fresh one), so it is recorded rather than proposed.

**What survived the second pass unchanged:** the draws are sequential and byte-identical; prompts
are 100–200× the 1,024-token minimum; outputs are documented as unaffected; and the measured logs
themselves prove today's traffic gets NO hits — draws 2–5 bill the full prompt, identical to draw 1.

## How to test before building

- **Stage 1 — a ~$0.85 probe, nothing in the repo.** Send BRBR's real prompt (system and user
  verbatim from its `llm_call.log`, tool from `tool_for(sleeve)`) three times sequentially with the
  real forced `tool_choice`, top-level `cache_control`, and `max_tokens` small so output is ~free.
  PASS: call 1 `cache_creation_input_tokens` ≈ the full 112,815; calls 2–3 `cache_read` ≈ it and
  `input_tokens` near zero. Settles the mechanics on our exact request shape — forced tool on
  Opus 4.8 included, which the docs do not address — before a line of code changes.
- **Stage 2 — the code on a branch, one real 5-draw assembly (~$1.50–2.50).** USAGE lines must show
  draw 1 writing and draws 2–5 reading; start-to-start gaps under 300s, measured rather than
  inferred; the gate still completes 5/5. Plus a standing guard: a multi-draw build whose later
  draws read ZERO from cache raises a qa flag, because the costliest caching failure is silent —
  a later prompt change quietly misses on every request and only the bill notices.
- **Stage 3 — after merge.** Realised saving from the next fleet pass's USAGE lines, and per-key
  attribution in the Console once vinci has its own API key.

**STAGE 1 RAN 2026-10-05 — PASS.** BRBR's real prompt, three sequential calls, `claude-opus-4-8`,
forced `tool_choice`, top-level `cache_control`, `max_tokens` 64:

    call  start   took   input  cache_write  cache_read  output
     1     0.0s   3.9s     24      112,791           0      64
     2     3.9s   2.4s     24            0     112,791      64
     3     6.3s   2.8s     24            0     112,791      64

- **Fidelity is exact:** call 1's prompt totals **112,815 tokens — the logged uncached figure to
  the token**, so the probe reproduced the production request rather than a lookalike.
- **Caching works with our forced tool call on Opus 4.8** — the one thing the docs did not address.
- **24 tokens per call stay uncached** — the framing after the last cacheable block; negligible.
- **Billed ~$0.823 against ~$1.697 uncached** for the same three calls.
- Calls 2–3 returned ~1.3s faster than call 1. Three calls with 64-token outputs is an
  observation, not a latency measurement.
- **NOT tested:** the 5-minute TTL under real ~1-minute draws (these calls were seconds apart),
  and our own code path. Both are Stage 2.

**What no test here can show:** that cached draws are DISTRIBUTED like uncached ones. Five draws
cannot detect a shift, and none is expected — that rests on the documented guarantee, not on a
measurement this repo could make.

**THE BUILD, IF APPROVED.** `extract(..., cache=False)`; when set, send top-level
`cache_control={"type": "ephemeral"}` (5-minute TTL — draws start ~1 minute apart; SDK 0.112.0
supports the parameter); `synthesize` passes `cache=draws > 1`; `last_usage` gains the two cache
fields. Proven by one real 5-draw assembly showing draw 1 `cache_creation ≈ prompt` and draws 2–5
`cache_read ≈ prompt`, pinned by a test that a single-draw call sends no `cache_control`.

**BOUNDARY.** 25 calls, 5 names, `claude-opus-4-8`, logs dated 2026-09-26 in
`mosaic-theory-ta/data/dossiers/*/llm_call.log` (git-ignored, local). The 17 older logs there carry
no `USAGE` lines and are excluded rather than estimated. Rates are list prices; the Console's
$661 and 41% are the operator's org-wide figures, not reproduced here.
