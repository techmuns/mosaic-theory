---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# The bench opened on the contested tail, so everything measured there was measured on it

**What was wrong.** The review bench opened pinned to priority band `1 direction flipped` —
391 rows, **4.8%** of the corpus. That is the right place to START and the wrong place to MEASURE
from. Of the operator's first 63 hand decisions, **61 came from that one band**, and band 1 by
construction contains only rows where BOTH readers named a direction. Every rate computed from
that reading — including "the adopted reading over-commits to bearish" — was a rate on rows the two
readers had already disagreed about, with no way to tell whether it held anywhere else.

**What shipped.** Two orders on the sort control:

- **`random sample`** — a draw over everything, for a base rate. Verified: releases the band filter,
  8,185 rows, and the first 100 come back at the corpus mix (52 `not a call`, 23 `call or not`,
  21 `detail moved`, 3 `direction flipped`, 1 `target unreadable`) rather than 100 of band 1.
- **`random, spread across bands`** — round-robin, so a short read touches all six. Verified
  1‑2‑3‑4‑5‑6‑1‑2‑3‑4‑5‑6.

**Choosing a random order RELEASES the band filter.** A random sample of the contested band is not
a random sample, and an option labelled "random sample" that silently drew from 4.8% of the corpus
would launder the same bias behind a word that says otherwise. Clicking a band afterwards is an
explicit choice and still narrows the draw.

**The order is a HASH of (seed, row), not a shuffle of the array.** It is therefore stable under
re-render and under filtering — logging a decision never moves the ground under the cursor — and
the seed is persisted, so a sample survives a reload half-read. `↻ re-roll` draws a new one, and
the button only appears on a random order. All four properties verified in the browser.

**A DATA-LOSS BUG CAUGHT BEFORE IT WROTE.** `decide()`'s `no call` path set
`cls: (POSTS[r.i]||{}).cc` — posts carry `wc` and `nc`, never `cc` — so it stored `undefined`,
which the export serialised as `post_class: null`. `import_rows` merges any key PRESENT in the row
(`if src_f in row`), so importing would have BLANKED the class on all 8 `no call` rows
(`signal_candidate`, `promo`). Fixed to `.nc`, plus an export fallback so the eight already logged
under the bug healed without a migration. Verified: 0 null classes in the export, and 0 rows lost a
class across the import.

**The import.** All 63 decisions merged — 47 new hand labels, 16 idempotent.

| | before | after |
| --- | --- | --- |
| hand labels | 99 | **146** |
| scored rows | 3,302 | 3,279 (23 dropped to `mixed`/`none`) |
| direction-correct | 51.07% | **51.10%** of 2,855 |
| the HAND subset alone | 58.7% of 75 | **59.0%** of 78 |

Exactly ONE previously-scored row changed verdict. The headline has now sat at ~51% across five
independent interventions — noise removal, the adopted reading, the missing-ticker tail, the
rename splice, and 63 hand corrections.
