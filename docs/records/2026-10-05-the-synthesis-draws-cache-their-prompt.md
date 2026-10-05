---
id: 2026-10-05-the-synthesis-draws-cache-their-prompt
status: shipped
date: 2026-10-05
prs: [665]
supersedes:
superseded-by:
---

# The five synthesis draws cache their prompt, and say so when they stop

**WHAT.** A multi-draw synthesis now asks the API to cache its prompt: draw 1 writes it, draws 2–5
read it at a tenth of the input price. Nothing else caches. Proposed, sized and probed in
`docs/records/2026-10-05-pending-after-the-forward-multiples.md` (#664); this is its Stage 2.

- `AnthropicLlmClient.extract(..., cache=False)` — when set, a top-level
  `cache_control: {"type": "ephemeral"}`; when not, NO key at all, so every other request is
  byte-identical to before.
- `synthesize` passes `cache=True` only when it will draw more than once. A single draw passes
  nothing.
- `last_usage` always carries `cache_creation_input_tokens` and `cache_read_input_tokens`. Without
  them a cached log line reports a 121K-token prompt as 24 tokens.
- Each draw's USAGE line carries `started_s`, so the 5-minute cache lifetime is checkable from the
  log rather than assumed.
- **A guard for the failure that does not fail.** A draw after the first that reads nothing from
  cache raises `PromptCacheMissWarning`, naming the draw and its likely cause — started past the
  300s lifetime (a slow draw), or inside it (the prompt was not cached or not reused). It goes to
  the operator's terminal and `llm_call.log`, and is deliberately kept OFF the dossier: a cache
  miss changes what a build costs, never a fact on the page.

**WHY ONLY THE DRAWS.** A write bills 1.25× input and pays back only on a re-send inside the TTL.
Every single-call phase — covenant and driver extraction, graph, themes — sends its prompt once, so
caching it would be a 25% surcharge.

**HOW VERIFIED.**

*The real run.* ROST, five draws, `claude-opus-4-8`, on this branch, exit 0, 16:29–16:35 IST:

    draw  started   gap  input    write     read  output
     1      0.0s           24  121,015        0   4,323
     2     59.2s    59s    24        0  121,015   4,636
     3    120.5s    61s    24        0  121,015   4,163
     4    177.1s    57s    24        0  121,015   4,133
     5    232.6s    56s    24        0  121,015   4,316

One prompt size across all five (121,039 — byte-identical prompts). **Largest start-to-start gap
61s against a 300s lifetime**, now measured: the five draws end inside one lifetime with ~5×
headroom on any single gap. No miss section, no warning. **Synthesis billed ~$1.54 against ~$3.57
for the same calls uncached — 56.9% saved**, inside the 55–61% range #664 projected from logs.

*The draw tally, stated because a reader will compare it.* This run drew **3 mixed / 2
strongly-bullish**; ROST's committed #663 page drew 4 strongly-bullish / 1 mixed. ROST's own
UNCACHED history is 7 strongly-bullish of 10 draws across two builds (3/2, then 4/1); at that rate
two or fewer of five happens **about 1 time in 6**. Ordinary variance for this name — and one run
can neither convict nor clear caching. That rests on Anthropic's documented statement that caching
has no effect on output tokens, not on this measurement. The run was verification only: ROST's
committed page is unchanged.

*Mutation — nine, all caught.* M1 the client ignores `cache`; M2 it caches every call; M3 the draws
never ask; M4 a single draw asks too; M5 usage drops the cache-read field; M6 the guard never runs;
M7 it judges the writing draw; M8 a miss leaks into dossier flags; M9 expiry and non-reuse
swapped. Baseline and restored runs exit 0; source restored byte-identical.

*A harness that reported nine survivors, and was wrong.* The first mutation pass said every mutant
SURVIVED — the result that would mean the pins catch nothing. It was the harness: zsh does not
word-split an unquoted `$T`, so pytest received the four test paths as ONE missing path, errored,
and printed no `FAILED` line to find. One mutation run by hand failed as it should; the harness now
passes the list as an array and prints every run's exit code, so an erroring run cannot read as a
green one.

*Review fixes, before merge.* (a) A draw that RAISED was dropped from the miss guard's timeline,
so the next draw's gap was measured from the draw before it — draw 2 raising at 200s and draw 3
missing at 360s read as "past the 300s lifetime" when the gap was 160s. Every `LlmError` the client
raises follows a response, so the raised draw touched the cache; it now stays in the list as timing
only, never judged. Pinned end-to-end through `synthesize` (M10: drop it — caught). (b) The
`anthropic>=0.69` floor admitted SDKs the top-level `cache_control` keyword was never verified on —
a `TypeError` is not an `LlmError`, so it would have crashed the assembly rather than failed one
draw; the floor is now 0.112, the version the real run used.

*The gate.* ruff clean · `mypy --strict vinci` clean (154 files) · `pytest -m "not network"` exit 0.

**BOUNDARY.** One real build — ROST, 2026-10-05, prices on the 2026-09-22 close, `claude-opus-4-8`
list rates ($5 input, $6.25 5-minute write, $0.50 read, $25 output per MTok). The 56.9% is
SYNTHESIS only; an assembly's covenant and driver calls are untouched, so per-assembly savings run
lower — 42–60% on #664's five-name estimate.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **A changed interface.** `extract` gains `cache` and the SDK floor rises to 0.112; one test fake (`_Scripted`) and two
  `last_usage` pins moved with it. Duck-typed fakes without the parameter still work everywhere a
  single draw is made.
- **The saving depends on the draws staying sequential.** `assemble.py` already runs NAMES on a
  thread pool; moving the DRAWS onto one would void the cache — and the guard would say so.
- **Distributional equality is taken on the documentation**, not measured. Five draws cannot
  detect a shift.
- **Not CI-validated** — the `gate` workflow has failed on Actions billing since #652.
