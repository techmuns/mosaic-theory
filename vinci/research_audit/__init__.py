"""Historical alpha audit of PUBLISHED SELL-SIDE research (MS / BofA / Citi / JPM / GS / Nomura).

WHAT THIS IS. An event study over third-party research: for each company a publication actually
rated, the market-adjusted total return over the 6 / 9 / 12 calendar months after the first
tradable close. Input is the operator's audit workbook (the source registry); output is a ledger,
leaderboards, a coverage report and a provenance log — every number traceable to an article row,
a price series and a benchmark series.

WHAT THIS IS NOT, AND MUST NEVER BECOME. CLAUDE.md: *validate forward, never backtest; never tune
on forward returns.* Those rules govern the FUND'S OWN discriminator. This package measures OTHER
PEOPLE'S published calls after the fact; nothing in the screen / ranker / ledger / scoring / freeze
path may import from it, and no parameter anywhere may be set from what it reports. It is a
research read, not an input.

THE LINES IT HOLDS (from the operator's brief, 2026-10-09):
- A company MENTION is never turned into a recommendation. Only a stated analyst rating is a
  directional signal, and only Overweight is scored as a long; Equal-Weight / Underweight /
  unrated mentions are kept in separate buckets.
- No author, date, rating, ticker or price is invented. Missing is UNKNOWN / blocked, loudly.
- A primary listing Polygon does not carry is UNAVAILABLE_POLYGON — never silently swapped for an
  ADR, an OTC line, an ETF or a similar company.
- No price is carried forward across a missing session; no incomplete horizon is computed.
"""
