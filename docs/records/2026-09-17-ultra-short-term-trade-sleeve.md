---
id:
status: shipped
date: 2026-09-17
prs: [626]
supersedes:
superseded-by:
---

# S5 ultra_short_term — the SHORT-DATED CATALYST TRADE: PARR under it, AMZN under quality

**WHAT.** A fifth sleeve, `ultra_short_term` (plain words: a short-dated catalyst trade), added by
operator decision 2026-09-17 and active in the decision ledger from the start. It is one registry
row in `vinci/sleeves.py`, plus the page-copy mirror in `frontend/views/shared/dossier.js`:

- **Bet:** a dated, nameable catalyst moves the price within weeks, and the market has its size or
  its timing wrong.
- **Twin:** priced or spent. The catalyst is already in the price, or its move fades before the exit.
- **Question:** *What is the dated catalyst — and is it already in the price?*
- **Verdicts:** BUY / PASS. A trade not taken says the catalyst is priced or too uncertain, never
  that the business is going away, so AVOID_TERMINAL would be a false record.
- **Entry:** the follow list.
- **Kill:** the book's BUY−PASS curve, each verdict scored at its own short horizon, fails to beat
  simply holding the same followed names over the same windows. That is the quality book's
  comparator (`vinci/scoring/baseline.py`), so scoring needed no change.

Follow entries in `data/followed.json`: **PARR** under `ultra_short_term`, **AMZN** under `quality`.
WLK is followed in a separate PR, because it is also a current screen candidate and needs a route
ruling first.

**WHY.** The operator wants PARR and WLK judged as short-dated trades, not as de-ratings (overshoot)
or as compounders (quality). Neither existing book asks the right question. A name judged under the
wrong book gets the wrong page questions, the wrong synthesis cases and the wrong proposal labels.

**HOW VERIFIED.**
- *Real run, live EDGAR + CIQ, prices through 2026-09-16, no LLM:* PARR assembled with
  `sleeve: ultra_short_term` and AMZN with `sleeve: quality`. AMZN read its CIQ workbooks: market
  cap $2,653,001.7M, multiples as of 2026-09-16. The PARR page's Brief heading is "What happened —
  and is the catalyst still ahead?". Under the dry run's temporary quality tag it read "… does it
  change the runway?", and nothing else in the heading list moved.
- *Prompt and proposal, built from the row:* the system prompt names "a US equity with a dated,
  near-term catalyst" and rule 3's two readings. The bull and bear definitions open the tool schema.
  Proposals: bullish → BUY, bearish → PASS, mixed → nothing.
- *The same PARR and AMZN runs on this PR's commit alone vs the combined branch:* identical apart
  from timestamps, one fetch latency and the checkout path.
- *Pins:* the ledger-active set is now {overshoot, quality, ultra_short_term}. The trade book's twin
  is not terminal and its legs are BUY/PASS. The derived row-completeness, JS-mirror, prompt and
  proposal pins cover the new row with no edits.
- *Mutation, bytecode caching off:* not ledger-active; records AVOID_TERMINAL; JS legs mirror
  missing the book; JS copy drifted. All 4 killed.

**BOUNDARY.** "Identical apart from…" compares every leaf of `dossier.json`: PARR 5,508 leaves,
AMZN 7,776. Both were assembled 2026-09-17 against store prices through 2026-09-16.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **Nothing enforces the horizon.** A short `--horizon-days` is what makes this book short, and it
   is typed per verdict. The page's copy-paste command still suggests `--horizon-days 180` for every
   book. A trade logged at 180 days would be scored as a half-year hold, and the ledger is
   append-only. Falsifier: any `ultra_short_term` row with `horizon_days` > 60. Proposed follow-up:
   a per-book horizon hint on the page (a render change, preview-gated) and/or a cap refused at log
   time. Either needs the operator to name the number.
2. **The kill test has almost no power at first.** With one name (PARR; WLK to follow), the passive
   basket is the name being judged.
3. **The page shows the key, not a label.** The shelf tag and decision-log chip print the raw key
   `ultra_short_term`, as they print `quality`.
