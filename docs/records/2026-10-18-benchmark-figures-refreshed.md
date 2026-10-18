---
id: 2026-10-18-benchmark-figures-refreshed
status: recorded
date: 2026-10-18
prs: [745]
supersedes:
superseded-by:
---

# GOOGL and LLY's benchmark figures corrected; the seven pages whose prose quotes the stale figure are refused

**WHAT.** STATE §5.0 row 32 (7): nine committed pages read SPY's or MDY's 2026-09-16 close as the
2026-09-22 close: GOOGL, LLY, NKE, ROST and TGT on SPY; BURL, ORKA, PARR and WLK on MDY. The
operator chose, 2026-10-18, to recompute only the benchmark figures, with no model calls.

**WHAT THE CHECK FOUND FIRST, AND WHAT IT CHANGED.** Before any page was written, each page's
synthesis was searched for its stored figures.
- **Seven of the nine quote the stale benchmark figure**:
  - NKE: "SPY rose ~16.9% (-47.6% relative)";
  - ROST: "underperformed SPY by ~8.4pts";
  - TGT: "vs SPY +13.7%";
  - BURL: "the mid-cap benchmark rose 8.5%, a 28pt relative drag";
  - ORKA: "vs the benchmark's ~11%";
  - PARR: "+11% for MDY";
  - WLK: "a +8.5% market benchmark (rel −48%)".
- Recomputing their figures under a kept synthesis would leave each page contradicting its own
  tables: the 19c defect `vinci/dossier/refresh.py` exists to refuse.
- **The write path would not have refused them.** `moved_cited_claims` is money-only, and
  `moved_cited_counts` covers revision counts. A return passed both.
- The operator then chose: correct GOOGL and LLY, add the check, and leave the seven for a
  re-assembly. GOOGL's and LLY's prose never quotes the benchmark; their matching numbers (17%, 57%)
  are a revenue growth rate and a P/E premium.

**THE CODE** (`vinci/dossier/refresh.py`).
- **`moved_cited_returns`**, wired into `refresh_dossier` beside the two existing checks. A
  market-relative return that moves (the name's and the market's 180 days, the difference, and the
  52-week chart's two returns) and that the stored prose quotes refuses the refresh, naming the
  figure.
- **`return_cited`** is the matcher. It leans to "cited", the safe direction for a refusal:
  - one decimal ("16.9%", "8.4pts") stands alone;
  - a whole number ("11%") counts only within 60 characters of a market word or the benchmark's
    symbol;
  - the prose is matched decoded, because a JSON-escaped minus (`−`) had hidden WLK's
    "rel −48%".
- **`benchmark_figures_transform(ticker, reference_date)`** re-reads the benchmark side through
  `_market_legs` and `_stock_performance` at the page's own date.
  - **It moves only what the bug touched, or nothing** (`horizon_read_transform`'s rule): the name's
    180-day move, its source, and every point, the return and the end date of its 52-week line must
    reproduce the stored page exactly, or the page is left for a re-assembly.
  - The cohort and its read are kept.

**THE RUN** (this machine's store, SPY and MDY complete since 2026-10-18; through `refresh_dossier`;
`mirror_to_frontend()` last).
- **GOOGL and LLY refreshed.** Each moved eight leaves and nothing else:
  - the market's 180 days, 16.9% → 19.9%;
  - the difference (GOOGL 8.1% → 5.1%, LLY 13.6% → 10.6%);
  - the 52-week chart's SPY return, 13.7% → 16.6%;
  - the chart's last four SPY points (09-17, 09-18, 09-19 and 09-22, which had carried the 09-16
    close flat);
  - the page's `layer_refreshes` entry.

  The synthesis and the name's side are byte-identical, and `frontend/dossiers/` mirrors both pages
  byte for byte.
- **The seven refused by the write path itself**, each naming the figure its prose quotes. NKE, BURL
  and WLK are refused on the market move and the difference, ROST on the difference, and TGT, ORKA
  and PARR on the chart's benchmark return. Their files are untouched.

**HOW VERIFIED.**
- **The corrected figures.** All nine pages' own name figures reproduce exactly from this
  machine's store (the 180-day move, and the chart's points and return), so only the benchmark side
  moved. The corrections are the benchmarks' own moves:
  - SPY: market 16.9% → 19.9%, chart 13.7% → 16.6%;
  - MDY: market 8.5% → 9.2%, chart 11.2% → 12.0%.
- **Pins** (`tests/test_benchmark_figures_refresh.py`).
  - **The citation check, on FROZEN prose excerpts** (verbatim from the pages, 2026-10-18, never the
    living synthesis):
    - one decimal is refused;
    - a rounded figure beside the market is refused, and NEGATIVE: GOOGL's "grew 17%" is not;
    - the escaped minus is read;
    - NEGATIVE: a quoted figure that did not move is never refused;
    - at the call site, `refresh_dossier` refuses a page carrying a frozen claim quoting its moved
      market return, and the file is untouched.
  - **The transform, on TECX (IWM, 2026-09-22) against the committed price fixtures**, which
    reproduce the page exactly:
    - a page rebuilt the incident's way (the old lookup over IWM missing 09-17..09-22) is restored
      exactly, with the name's side and the cohort unchanged;
    - NEGATIVE: a correct page is a no-op;
    - NEGATIVE: a page whose own figures do not reproduce is left untouched.
- **Mutation.** 7 mutants, all killed:
  - the check not wired in;
  - no decoding;
  - a rounded figure counting without context;
  - no one-decimal match;
  - unmoved figures checked;
  - no reproduction check;
  - the chart not replaced.
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"` with the store moved aside:
  5886 passed, 512 skipped.

**BOUNDARY.**
- 2026-10-18, branch over main 57517b76.
- Store: this machine's `data/vinci.db`, with SPY and MDY refreshed to 2026-10-16
  (`docs/records/2026-10-18-spy-mdy-refreshed-locally.md`).
- Population: the nine pages named in row 32 (7), each at its own reference date, 2026-09-22.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The seven stay wrong until re-assembled.** NKE, ROST and TGT understate SPY's 180-day move by
  3.0 points (relative figures 3.0 points too high); BURL, ORKA, PARR and WLK understate MDY's by
  0.7 points. A re-assembly reruns the paid synthesis and moves the page to the current screen
  date, so it is the operator's decision (row 32 (7)).
- **`return_cited` is a matcher on model-written prose**, not a parser. A paraphrase ("about a
  sixth") is not caught, the same stated limit as `moved_cited_counts`. It leans to refusing, so
  its errors send a correct page to re-assembly rather than certify a wrong one.
- `scripts/refresh_stock_performance.py` is stale: it calls `_stock_performance` without the `bench=`
  argument the function requires, so it would raise. It is not used here, and not changed
  (reported).
