# Validation — @pdicarlotrader labelled call corpus

`pdicarlotrader_labels.jsonl` · 8,185 rows · one per (tweet × ticker) · 5,641 posts ·
2024-08-01 → 2026-08-24 · regenerate with `python -m scripts.calls.export_dataset`

**Read this before the data.** Five requested fields do not exist in the corpus as specified, and
two of them are derived rather than labelled. Each is named below with what was actually done.

---

## 1. How the labels were generated

### Tier 1 — the original machine labeller (superseded)

The corpus was first tagged by an upstream labeller, measured at **~55% on bias** against the 83
hand labels that existed at the time. **Zero rows carry it today**; it survives only in
`labels.machine.json` as a before-snapshot.

### Tier 2 — `llm`, the adopted second reading (7,473 rows, 91%)

- **Model:** `claude-sonnet-5`, one forced-tool call per tweet, 8 workers.
- **Coverage:** all 5,641 posts, 0 errors.
- **Unit:** the model returns a post-level reading plus one entry PER TICKER, because a single post
  routinely carries different views on different names.
- **Prompt rules that shape the data**, verbatim in `vinci/calls/audit.py`:
  - his ✅ / 🔻 notation marks flow direction, not his own view;
  - a stated DURATION is not a target ("into next week" is a horizon, not a price);
  - a worst-case level is not a bullish target;
  - `spec`: **A** = direction + target + stated horizon · **B** = direction + target, no horizon ·
    **C** = direction only · **D** = none;
  - a post with no directional content gets `bias: none` and `spec: D`.
- **Partial responses are kept, not discarded**: where the model returned post-level fields but
  omitted the ticker array, the post-level reading is retained and the row marked, because an empty
  ticker list passing silently is indistinguishable from a correct `none` on every ticker.

### Tier 3 — `hand`, human-verified (712 rows, 9%)

Read one at a time in a local review bench against the post text, the price at post time, and the
scored outcome. 83 are original gold labels predating the tier-2 reading; 629 were corrected or
confirmed during 2026-08.

---

## 2. Accuracy, and the sample it rests on

Measured by comparing the tier-2 reading against hand labels, **excluding rows drawn from the
"direction flipped" queue** — those were selected *for* disagreement and inflate every error rate.

| field | agreement | n |
| --- | --- | --- |
| `post_class` | **99%** | 75 |
| `target_type` | **98%** | 231 |
| `specificity` | **90%** | 231 |
| `bias` | **81%** | 283 |
| `bias`, unanchored subset | **77%** | 82 |

**The 81% figure is anchored.** The bench pre-fills each control with the model's answer, so it
measures "the reader did not object", which is weaker than an independent reading. The
**unanchored** row is the clean number: the 82 original gold labels were written *before* the
tier-2 reading existed. Both readers score 77% there.

**Where `bias` is wrong, it is over-commitment, not direction.** On 140 unbiased rows where the
model said directional: **76%** kept intact, **20%** re-read as non-directional (`mixed`/`none`),
**4%** flipped direction. Its weakness is deciding *whether* a post is a call, not which way.

**A stronger model does not help.** `claude-opus-5` re-read all 463 hand-labelled tweets:
80% vs sonnet's 78% overall (McNemar p = 0.18), and **77% vs 77%** on the unanchored gold labels,
splitting their 12 disagreements 6–6. Kept at `data/calls/pdicarlotrader/audit.opus-5.jsonl`.

**Completing the labelling would not change the aggregates.** Applying the measured transition
rates (82.3% keep / 2.5% flip / 15.2% abstain) to the un-reviewed rows projects a **+0.07pp** shift
in the headline hit-rate, 90% band [50.4%, 52.0%]. One 34-row batch tested this out of sample and
moved it −0.013pp.

---

## 3. Schema deviations — READ THESE

### `is_forward_call` is DERIVED and carries no independent information

Defined here as `bias ∈ {bullish, bearish, mixed}`. It is a **deterministic function of `bias`** —
perfectly collinear, and it will contribute nothing to any model that already includes `bias`.

It was never labelled. The rows where an independent label would plausibly differ are the **514**
that are `is_retrospective AND is_forward_call` — a post like *"up 40% since our call"* carries a
bullish bias describing a move that already happened, and a human might well call that
forward=false. **If this field matters to your analysis, it needs labelling; do not treat it as
observed.**

### `label_confidence` is DERIVED from `label_source`

`hand → high`, `llm → medium`, `machine → low`. There is no per-row confidence in the corpus. It is
a restatement of `label_source`, not a second signal.

### `bias` has FIVE values, not three

`bullish` 2,448 · `bearish` 846 · **`mixed` 396** · `neutral` 14 · **`none` 4,481**. The `mixed` and
`none` rows are **60% of the corpus** and cannot be collapsed without destroying the distinction
between "no view" and "two-sided view". Widen your enum.

### `label_source` has no `machine` rows

`llm` 7,473 · `hand` 712. The tier-1 labeller was fully replaced. Do not map `llm` to `machine`:
they differ by ~22 points of bias accuracy.

### `post_class`: `signal_candidate` renamed to `signal`; `commentary` never occurs

Emitted values: `signal` 3,134 · `flow_spam` 1,545 · `pnl_report` 1,239 · `promo` 1,186 ·
`noise` 715 · `engagement` 285 · **`null` 81**. The nulls are the original gold labels, made before
`post_class` existed. `commentary` is in the requested enum but is not a category this corpus uses.

### `stated_confidence` is effectively EMPTY — 2 non-null of 8,185

The source field is free text and mostly not a confidence at all. Of 269 non-null raw values the
shapes include *"90% of traders fail"*, *"75% of premium"*, *"most likely"*. Only a bare percentage
is extracted; everything else is dropped rather than mined into a number it does not mean.
**Treat this column as unusable.**

### `target` is a number whose UNIT depends on `target_type`

A **price** for `point` and `range`; a **percent** for `pct`. Resolving a `pct` target to a price
requires the entry price, which is forward-looking data — putting it in a label field would
contaminate the export. For `range` the price is the target END, chosen by bias, matching the
scorer. `qualitative` and `none` yield null. 1,749 rows carry a number.

### One value was coerced

`1947343463386615982|MSTR` carried `target_type: "price"`, which is not a member of the enum — a
model wrote it and no guard rejected it. Coerced to `point` (its target is `"500+"`). This is a
real validation gap in the ingest path, not a display artifact.

---

## 4. Known limits of the data itself

- **Horizons are rarely stated.** 986 of 8,185 rows (12%) carry one. Everything else is unstated,
  and `null` is correct — nothing was inferred.
- **Duplicate windows.** He posts the same name repeatedly; 230 of the bullish rows share a
  (ticker, date) with another row. Group by `thesis_cluster_id` (= `tweet_id`) for per-post
  weighting, or de-duplicate on (ticker, date) for per-opportunity weighting.
- **30 rows have no price data** — crypto, indices, and cashtag typos in the source posts. They are
  present in this file; they simply cannot be scored.
- **`action` has never been accuracy-tested**, and the operator labelled `enter_long` and `add`
  interchangeably. It is also read by nothing in the scorer. Treat it as the least reliable column.
- **One regime.** 25 months, net-up and tech-led. Beat-SPY at 63 days by posting quarter runs
  74 / 44 / 50 / 66 / 62 / 22 / 43 / 50 percent — a 52-point swing that dominates every
  cross-sectional effect measured so far.

---

## 5. The audit sample

`pdicarlotrader_audit_sample.jsonl` — 60 rows, stratified across all 9 quarters (6 per quarter plus
a 6-row remainder), seeded `20260828` and reproducible. Same schema plus `text` and `url`, so each
label can be checked against the words that produced it.

Composition: `signal` 20 · `promo` 15 · `noise` 9 · `flow_spam` 8 · `pnl_report` 7 ·
`engagement` 1 · bias `none` 33 / `bullish` 17 / `bearish` 7 / `mixed` 3 · source `llm` 52 /
`hand` 8 — close to corpus proportions, which is what stratifying on quarter alone gives.
