---
id:
status: shipped
date: 2026-08-27
prs: [511]
supersedes:
superseded-by:
---

# The class tag was never checkable, and now that it is, it holds

**The gap.** `post_class` is the field every per-class performance question slices on, and across
409 hand rows it had NEVER been verified. `patchRow` seeded `cls` from the adopted reading and no
control overwrote it — `data-f="cls"` appeared ZERO times in the bench. The 231/231 agreement
measured earlier was **the tool agreeing with itself**, not a person agreeing with the machine.

**The fix.** A `class` select in the always-visible tag block, same six-value vocabulary as
`CLASSES` in `vinci/calls/audit.py`, and `patchRow` now reads it like every other field instead of
hard-coding it.

**The measurement.** 75 rows, drawn at random across the whole corpus (no class or bias filter),
class checked on every one:

| | agreement | 95% CI |
| --- | --- | --- |
| **overall** | **74/75 = 99%** | [93%, 100%] |
| `flow_spam` | 32/32 | [89%, 100%] |
| `pnl_report` | 22/22 | [85%, 100%] |
| `noise` | 14/14 | [78%, 100%] |
| `signal_candidate` | 6/7 | [49%, 97%] |

One disagreement, `signal_candidate → noise`. **No real call was silently dropped**: of the 68 rows
the machine called NOT a call, the operator promoted zero.

**CAVEAT THAT MUST TRAVEL WITH THIS NUMBER — the control is PRE-FILLED with the machine's answer.**
99% therefore measures "the reader did not object", which is weaker evidence than an independent
blind reading; it is the same anchoring concern CLAUDE.md records against the machine-proposed
verdict. It is not worthless — the reader DID object once, and objected 20% of the time on `bias`
under identical pre-filling — but a blind class re-read would be the stronger test if the number
ever needs to carry more weight than "safe to accept".

**`signal_candidate` is the thin arm and the one that matters** — only 7 rows, because a random
draw is mostly non-calls (44 `flow_spam`, 27 `pnl_report`, 17 `noise` per 100). Its CI runs
[49%, 97%]. The 99% headline is carried by the classes that are easy.

**Scoring: unchanged.** 3,242 rows, zero verdicts moved, 51.06% of 2,824 — the class does not enter
the scorer, so verifying it moves no number. Hand labels 409 → 484.

**One import detail, correct behaviour:** a row exported `post_class: null`. It is one of the
original 83 gold labels, which predate the field; it round-tripped unchanged rather than being
clobbered, and classless gold rows fell 83 → 82 because one GAINED a class.

**Where this leaves the corpus.** Every field the analysis will slice on is now measured:
`post_class` 99%, `target_type` 98%, `specificity` 90%, `bias` 81% (76% on directional). Accepting
the machine's labels for the remaining ~7,700 rows is defensible, with a stated ~3pt drag on the
hit-rate (machine-labelled 51.1% vs human-verified 53.9%).
