---
id:
status: shipped
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# A stronger model reads the same tweets no better

**The question.** The corpus's tags come from a `claude-sonnet-5` reading of all 5,641 tweets. Would
`claude-opus-5` read the directional calls more accurately? A full re-read is **2,378 calls**.

**MEASURED FIRST, ON 463.** 484 hand labels now exist, so "better" is checkable before it is bought.
Opus re-read every hand-labelled tweet; each model's bias was scored against the human's.

| cut | n | sonnet-5 | opus-5 | McNemar |
| --- | --: | --- | --- | --- |
| all hand rows | 484 | **80%** | 78% | p = 0.184 — not distinguishable |
| `signal_candidate` only | 224 | **73%** | 71% | p = 0.503 — not distinguishable |
| **UNANCHORED gold labels** | **82** | **77%** | **77%** | **p = 1.000 — 6-6 on 12 disagreements** |

**The unanchored cut is the one that counts.** The 82 original gold labels were written BEFORE the
sonnet reading existed, so the human could not have been anchored on it. Everywhere else the bench
pre-fills the human's control with sonnet's answer, which hands sonnet a free advantage. On the one
clean comparison the two models are **exactly tied**, and split their disagreements 6-6.

**A FIRST RESULT THAT WAS AN ARTIFACT, recorded because it was nearly reported.** The first cut
restricted to rows where the human KEPT a direction and showed sonnet 95% vs opus 89%, McNemar
p=0.002 — apparently decisive. It was **selection on the outcome**: rows where the human abstained
were excluded, and those are exactly the rows where sonnet was wrong. Widening to every hand row
dissolved it. Second time this session a "significant" result came from an arm chosen after the
fact; the first was the `promo` effect (0.009 → 0.064).

**CONCLUSION: the ~77% ceiling is not model capacity, it is ambiguity in the tweets.** A stronger
reader does not move it, so the remaining 2,216 calls were NOT spent. 463 calls bought the answer
that 2,378 would have wasted.

**What shipped to make it checkable.** `run_audit` takes `out` and `model`; `vinci calls audit`
gains `--out`, `--model` and `--only`. **`--model` without `--out` is REFUSED**: `audit.jsonl` is
what the corpus was adopted from, and a second model overwriting it would destroy the record the
comparison depends on. `done` is read from the OUT file so each model resumes against its own
results instead of skipping what another model covered. Both pinned and MUTATION-CHECKED —
defaulting the output back to `audit.jsonl`, and dropping the model override, each redden their own
test.

The opus reading is kept at `data/calls/pdicarlotrader/audit.opus-5.jsonl` so the comparison stays
reproducible.
