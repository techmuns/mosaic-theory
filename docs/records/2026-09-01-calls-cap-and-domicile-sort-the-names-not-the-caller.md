---
id:
status: falsified
date: 2026-09-01
prs: [511]
supersedes:
superseded-by:
---

# Market cap and domicile sort his returns cleanly — and sort the placebo identically

Neither cut had been run. Both are now, on bullish calls at 63 days.

**The data had to be fetched.** No committed source covers his book: `universe_snapshot.jsonl` keys
on `internal_id` (no ticker field at all) and is bounded to $0.3–10B by the fund's own universe
filter, so it cannot classify a mega-cap. Polygon's `v3/reference/tickers` supplies
`share_class_shares_outstanding`, `type` and `locale` per name — 244 fetched, 233 usable.

**Cap is computed AT POST TIME** — shares outstanding × the last close before the post — not today's
cap, which would classify a name by what it became. Share count is current, so this is approximate;
the bucket boundaries are decades wide and share drift rarely crosses one.

**`locale` is useless here: every ticker returns `us`, because they are all US-LISTED.** The
separating field is `type`: `ADRC` marks a foreign issuer (10 names — ARM, ASML, BABA, BIDU, JD,
NIO, NOK, NVO, PDD, TSM), `ETF`/`ETV` marks a fund (17 names, not companies at all).

## The cuts DO stratify — and the placebo strips every one of them

Each cohort beside the same names on a NEARBY day he did not post on (±90 days, same 63-day window):

| cohort | n | his mean excess | t | placebo mean excess | t | **his edge** |
| --- | --: | --- | --- | --- | --- | --- |
| mega-cap US (>$200B) | 971 | **+9.42%** | 10.23 | **+9.14%** | 9.78 | **+0.28%** |
| large-cap US ($10–200B) | 531 | +7.56% | 4.12 | +6.52% | 2.39 | +1.04% |
| mid-cap US ($2–10B) | 294 | +3.66% | 1.56 | **+10.48%** | 2.01 | **−6.82%** |
| foreign issuer (ADR) | 129 | −3.44% | −1.76 | −2.54% | −1.48 | −0.90% |
| ETF / fund | 176 | +1.36% | 1.06 | +1.45% | 1.06 | −0.10% |

**Cap sorts the returns over a 6-point range and none of the sort is his.** A mega-cap call returns
+9.42% over SPY; buying the same name on a random nearby day returns +9.14%. His contribution is
**0.28 points**. Large-cap: +1.04. The one large effect runs the WRONG WAY — in mid-caps he
underperforms a random day on the same names by **6.8 points**.

**ADRs are his worst cohort and everyone's worst cohort.** 37% beating SPY, mean −3.44% — against a
placebo of −2.54%. The names underperformed in this window; his calls on them are not distinctly bad.

**Funds are the only cohort that does not invert across the 2025-09 split** (52% → 59%), but the
mean is +1.36% at t=1.06 and the placebo is +1.45%. Nothing there either.

## The split, for completeness

Every US-equity cohort flips sign as usual — mid-cap hardest: **discovery +15.75% (t 4.79) →
holdout −14.99% (t −7.17)**; large-cap +12.82% → −9.89%; mega-cap +9.53% → +4.95%, the only one
staying positive, and its holdout MEDIAN excess is **−0.62%** while the mean is +4.95%, so even that
is a handful of tail winners rather than a broad result.

## Ruling

**FALSIFIED, and by the cleanest instrument used in this audit.** The previous cuts died on the
time split; this one dies on a within-period control, which is stronger — it holds the names, the
window and the market fixed and varies only whether he posted that day.

That makes it the second finding of the same shape as the trend filter: **a stratification that
genuinely orders the returns, contributes nothing once you ask what the names did anyway.** Cap is
a property of NVDA, not of his call on NVDA.
