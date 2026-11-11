---
id: 2026-11-11-fix2-rg-d21-a-stated-decline-reads-negative
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, RG-D21: the theme number check reads a stated decline's sign — "down 27%" is −27, and +27 for it is refused

**WHAT.** `vinci/theme_intelligence/verify.py` `_number_check`, the check every extracted claim's
figure passes before it can be evidence (fix request 2, group G, order 4; finding G-D21).

1. **The value text's own words state the decline.** A decline word inside it, before the number
   or right after it ("down 27%", "a 27% decline"), counts (`_states_decline`). −27 written "down
   27%" was refused, because the decline was looked for only beside the figure in the quote, and
   with the word inside the value text nothing stands beside it. This was a loud false refusal.
2. **A positive value for a figure stated as a decline is refused,** with the note "the quote
   states a decline but the value is positive". Until now "down 27%" read as +27 passed: a
   silent wrong value.
   - Kept positive: a claim whose METRIC names the decline ("mean reward reduction": its value is
     the decline's size), and a multiple ("3x lower").
   - The check now receives the claim's metric (`metric=`), at its three call sites.

**THE CODE REVIEW'S FIXES (round 0), each behind a pin that failed first.**
- **The sign is read beside the number that reads as the value,** not the first or the last in
  the value text. "2025 shipments down 27%" no longer hides its decline; "down 27%, up 5%" read
  as +5 is not refused.
- **The positive refusal needs a decline at every place the figure appears in the quote:** "rose
  27% while costs fell 27%" refuses neither sign.
- **A decline metric names the decline itself.** "loss" and "cut" name what fell ("net loss
  change"), so they no longer exempt.
- **A multiple** is "x" or "times" after a number, never "wait times".
- **A spelled-out "percent"** is skipped like "%".
- **Not changed:** "lower" still reads as a decline, so "27% lower than peers" read as +27 is
  refused. Dropping it would let "prices 27% lower YoY" stored +27 pass. That is a policy call,
  left as is.

**WHY.** On the registry the desk is published from, one stored claim carried the wrong sign:
C-f5fcf829b5a474, "Spot prices for low- to mid-capacitance consumer-grade MLCCs slipped
approximately 5%", value +5, metric "spot price change". The other positive reading of a stated
decline, C-743ff569c48ece ("a 3x lower mean reward", metric "mean reward reduction"), is coherent.
That is why the refusal carries its two exceptions, and why it is not a blanket rule.

**HOW VERIFIED.**
- **Pins, failing first on main 946943ec** (`tests/test_theme_intelligence_number_sign.py`):
  - the finding's own quote, −27 "down 27%" (was refused) and +27 (was passed);
  - the MLCC claim's shape;
  - negative pins: a metric naming the decline keeps +27, a multiple keeps 3, and a rise is
    unchanged.
- **Three existing tests changed, each stated in the PR:**
  - `test_a_positive_reading_of_a_stated_decline_is_unchanged` pinned the old behaviour "as
    before", and is reversed to `…_is_refused`.
  - Two fixtures stored a fall as a positive value: "fell 18%" as +18 and "fell 15%" as +15. They
    now read −18 and −15, and each test's own subject (a reaction refiled, a contradiction found)
    is unchanged.
- **Cross-setup, deterministic, $0.** Every claim carrying a figure in the desk's registry (696)
  through base and head:
  - **1 verdict changes,** C-f5fcf829b5a474: pass → refused.
  - **0 render-time changes.** `number_passes` flips for no claim stored as failing, so the
    committed desk renders identically until that claim is re-verified.
  - QA's "figures re-found in their quotes" is a separate check (`qa.py`), unaffected.
- **The suite:** see the PR.

**BOUNDARY.**
- Claims: the registry at `theme-intelligence-state` 4527c2b1 / ea8fb4a6 (the enrichment push
  adds no claims). 696 carry a value or a value text, of 1,190.
- Committed desk files: `frontend/theme-intelligence/` on main 946943ec.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **The stored claim keeps its pass until its article is analysed again,** when C-f5fcf829b5a474
  would be refused. Seven committed desk files cite it: TH-FDEF68AB50's and TH-C2EA7EB06F's card,
  print card and thesis page, and `review.html`.
- **Out of scope:** the decline word list. "Will fall 15%", future tense, is not one of the words
  the check reads; that is unchanged here.
