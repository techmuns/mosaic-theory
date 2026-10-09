---
id:
status: shipped
date: 2026-10-09
prs: [693]
supersedes:
superseded-by:
---

# The R4 card render — an EV/NTM EBIT card walks each leg from EBIT to equity, and its markdown twin prints the same numbers

**WHAT.** An R4 (EV/NTM EBIT) record now renders its own inputs and bridge, on the card and in the
dossier's markdown twin. Every R1, R2 and R3 card and page is unchanged.

| where | what it shows on an R4 record |
|---|---|
| `uw-card.js` legs table | value/share → vs spot → **NTM EBIT at exit ($M)** → exit EV/NTM EBIT → **EV ($M)** → **less TEV claims ($M)** → **Equity ($M)** |
| `uw-card.js` methodology | the `ebit` axis labelled "NTM EBIT at exit ($M)", its chosen values formatted as $M, the summary reading "NTM EBIT and multiple methodology" |
| `uw-card.js` cross-checks | **dropped on R4.** There the leg's EV/EBIT IS its input multiple and no normalized FCF is computed, so the block would verify a number against itself |
| `frontend/build.py` | emits the leg's `ebit`, conditionally, the way `eps` is |
| `render.py` scenario table | NTM EBIT at exit, EV, less TEV claims and equity columns |
| `render.py` methodology | heading "NTM EBIT at exit", not "Ebit" |

Every figure is the RECORD's: `ebit` per leg, `ev`/`equity` from `result.per_scenario`, and the
claims from the `net_debt` fact. Nothing is re-derived for display. Each new row and column appears
only when a leg carries `ebit`.

**WHY.** The next step in the ruled build order (STATE row 10). #688's record required it before
any R4 record: without it an R4 card shows every input except the one that produced its value, R3's
2026-09-01 lesson. Preview rule: a Phase-1 preview, collapsed and print-expanded, was approved by
the operator on 2026-10-09 ("approved the card preview, finish the R4 card PR").

**TWO DEFECTS THE PREVIEW CAUGHT, fixed before approval:**
- **The twins disagreed by $1M.** On AMZN's bull leg the card showed EV 5,181,376 and the markdown
  showed 5,181,375.
  - Cause: the emitter rounds `ev`/`equity` to one decimal, then JS `Math.round` takes .5 UP. The
    markdown formatted the raw value with Python's `:,.0f`, which takes .5 to EVEN.
  - `_card_thousands` now applies the card's two roundings in the card's order.
- **The summary printed the field name** ("ebit and multiple methodology"). It now uses the
  quantity's name, for `ebit` only.

**HOW VERIFIED.**
- **Nothing else moved.** All 13 committed underwrite cards were rendered under node with main's
  `uw-card.js` (@1cdab997) and with this branch's: byte-identical HTML on 13 of 13. The first
  comparison failed 13 of 13 on whitespace alone — a `${}` row on a line of its own emits a newline
  even when empty — and the R4 rows were joined onto existing lines. All 26 dossier pages were then
  re-rendered and the mirror re-emitted with this code: `git status` clean, no page moved.
- **The preview.** A real R4 record was built through `scenario-propose` → `scenario-create` on
  AMZN's committed page, its tag set to R4 in a scratch worktree only, with ILLUSTRATIVE leg inputs.
  It was emitted, served and rendered:
  - the leg walk is complete;
  - 0 `undefined`/`NaN`, collapsed and with every `<details>` force-opened;
  - the twins agree digit for digit.
- **Tests** (`tests/test_r4_card.py`, 9) build the same record through the real create path in a
  temp root, emit its card with `build.py` and render it with `uw-card.js` under node. They pin:
  - the emitter carrying `ebit`, and none on an R3 card;
  - each R4 row equal to the record's own number;
  - the summary;
  - no self-cross-check;
  - 0 `undefined` in both states;
  - no committed card growing an R4 row;
  - md/web parity digit for digit;
  - the methodology heading;
  - an R3 table and heading unchanged;
  - the rounding rule, constructed on the cases where the two disagree.
- **Mutation.** Eleven mutants, all killed:

  | mutant | tests failing |
  |---|---|
  | the emitter drops `ebit` | 3 |
  | the R4 columns on every md table | 3 |
  | the card: no EBIT row | 2 |
  | the card: no bridge rows | 2 |
  | the card: claims from the wrong fact | 2 |
  | md: raw rounding (.5 to even) | 2 |
  | the card keeps the self-cross-check | 1 |
  | the card: raw axis name in the summary | 1 |
  | the card: R4 rows on every card | 1 |
  | md: no R4 columns | 1 |
  | md: heading prints "Ebit" | 1 |

**BOUNDARY.**
- **Population:** the 13 committed underwrite cards and 26 committed dossier pages at main
  @1cdab997, plus one R4 record built in a temp root from AMZN's committed page.
- **Date:** measured 2026-10-09.
- **Units:** $M; $ per share.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The HTML byte-identity of the R1/R2/R3 cards was MEASURED, not pinned.** No test holds main's
  rendering to compare against. A whitespace-only regression would pass the suite and change
  nothing a reader sees. The negative pins hold what matters: no committed card grows an R4 row,
  and an R3 table keeps its shape.
- **Next in the ruled build order:**
  - the refresh-vintage record, before the first R4 record is sealed;
  - the machine proposal;
  - the operator's AMZN and UBER re-tags.
