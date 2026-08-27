---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# The first 16 decisions off the review bench reach the corpus

**What happened.** The operator read 16 (post, ticker) rows on the local audit bench and logged a
call on each. The export was verified byte-for-byte against what the page itself would download
(9,259 UTF-16 units, matching hash), dry-run first, then merged.

```
merged 16 row(s)   new 0   updated (hand) 0   replaced a guess 16
hand labels now 99   calendar days recounted 13
```

Corpus src is now **hand 99 · llm 8,102 · machine 0** — `labels.machine.json` still holds the
pre-adoption snapshot, so the bench's WAS column is unaffected.

**13 confirms, 3 overrides**, and the 3 overrides are exactly the 3 rows edited by hand — the
buttons produced no disagreement at all.

**What the re-score did.** 3,304 → 3,302 scored rows.

| | |
| --- | --- |
| dropped from scoring | `$TSLA` 2024-08-27, `$SOUN` 2025-10-03 — both re-read as `mixed` |
| verdict flipped | `$NVDA` 2024-08-16 — `-5.9% → +14.2%`, direction-correct False → True |
| direction-correct | 51.03% → **51.10%** of 2,855 |
| the HAND subset alone | 75 CLOSED, **58.7%** direction-correct |

**`mixed` REMOVES a row from scoring.** Both two-sided re-reads leave the scored set entirely,
which is the intended behaviour — a two-sided read is the human's call, never a coin-flip.

**THE `$NVDA` FLIP IS THE HORIZON, NOT THE TARGET.** Worth recording because the first reading of
the diff got it wrong: clearing the `$150` target changed `target_status` to `absent`, but what
moved the return was `hhi` going `30 → None`. The scorer fell back to its 63-day default
(`horizon_assumed: True`), the exit moved 2024-10-01 → 2024-11-15, and NVDA rose across that
window. A cleared horizon is not a neutral edit; it silently re-dates the exit.

**Bench design note, FOUND NOT CHANGED.** `patchRow` snapshots EVERY visible tag control, so any
single edit re-logs the whole row as it currently stands. Consequence: pressing `no call` (which
blanks target and horizon) and then correcting one field back leaves the other blanks in place.
That is what produced the cleared `$NVDA` horizon. It is not a cascade on an untouched field — the
patch is exactly what was on screen — but it is a trap worth knowing before a long labelling run.

**Class and retrospective do NOT gate scoring.** Verified against the corpus: 385 `promo`, 246
`pnl_report`, 29 `noise`, 27 `flow_spam`, 9 `engagement` and 508 retrospective rows are all scored
today. Two of the confirms above are `promo` + retrospective and will be scored as forward calls.
Whether that filter should exist is an open operator decision, NOT assumed here.

**Incident → invariant.** `tests/test_calls_ingest.py::test_the_calendars_hand_label_tally_follows_
the_import` named 2024-08-01 and went red when that day was labelled. Re-pointed to derive its own
unlabelled day; mutation-checked. Shipped: Y.
