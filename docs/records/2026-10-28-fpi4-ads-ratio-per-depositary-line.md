---
status: shipped
date: 2026-10-28
prs: [840]
supersedes:
superseded-by:
---

# FPI4: a depositary line's per-share figures are read per ADS, on the ratio its own filing states, or refused

**WHAT.** STATE §5.0 row 4, step 1 of the build order in
`docs/records/2026-10-28-fpi-readiness-measured-per-name.md` (operator ruling 2026-10-28: foreign
filers stay; build the readiness steps in that order). A depositary line is priced per ADS while
its filer reports per ORDINARY share. Nothing converted between them, so every per-share figure set
against the price was off by the ratio: QFIN 2, GPCR 3, IPX 10, KT 0.5. This build makes the
conversion in four places:

- **The reader** (`vinci/resolver/ads_ratio.py`, `EntityResolver.ads_ratio`). It reads the latest
  periodic report filed by the as-of date, on the same cover walk `registered_line` uses:
  - **EVERY depositary 12(b) title first**, not only the row a symbol match keeps. HSBC tags its
    symbol to its ordinary-share row as well as its ADS row, and the match keeps the ordinary one.
  - **Otherwise the filing's text.**
  - **Exactly one value, or a refusal with its reason.** Refused when the filing states several
    ratios (a change described beside its successor), states none, or counts UNITS / CPOs rather
    than shares.
  - **Grammar handled:**
    - fractions as fractions ("one-half of one share" = 0.5, "3/5 of one share" = 0.6,
      "five-ninths" = 5/9);
    - N-for-M ("every three ADSs represent two" = 2/3, "each three representing one" = 1/3);
    - the spelling "depository" (EC, IX).
- **The structured value** (`vinci/schemas/listing.py` `AdsRatio`): ordinary shares per ADS, with
  the source (12(b) title or filing text), the quote, the form, the filed date and the accession —
  or `status: refused` with its reason. It rides on `DataRecord.ads` and on the dossier's
  `stock_info.ads_ratio`. None on both means a line that is not a depositary receipt.
- **The screen.**
  - **Who reads a ratio:** `screen_universe(listing=…)`. The weekly run and `vinci screen` pass
    `listing_basis(eod.security_types(), resolver, ref)`, which reads a ratio only for a line
    Polygon types `ADRC`/`GDR`. That is the SAME type test the universe sizes on (#541), so one
    notion of "depositary line" serves both.
  - **When:** once per issuer, for names that survive the price gates.
  - **The P/E level:** `pe_current_and_percentile(…, ads=)` gives price per ADS ÷ (EPS per
    ordinary share × ratio). A refused ratio leaves the level UNKNOWN with the reason.
  - **The percentile is RATIO-FREE.** Every observation in the line's own range divides by the
    same constant, so it ranks identically and is kept, and G3's outcome cannot move.
  - **The run's row:** it carries an `ads_ratio` gate input (value, filed date, accession, quote;
    or None and the reason).
- **The dossier.**
  - **The page's P/E pair** goes through the same function (`_at_latest_close`).
  - **`stock_info.shares_out` is in ADSs:** EDGAR ordinary count ÷ ratio, or UNKNOWN with the
    refusal. The CIQ share bridge is not taken for a depositary line, because which unit its panel
    counts in is not stated.
  - **The short-interest denominator** gets the same conversion.
  - **The anchor:** `_traded_unit_counts`, the one helper both per-share paths (`_bridge_inputs`,
    `share_denominator`) now call, puts the diluted average and the dilutive increment in ADSs. It
    checks the page's count against the filer's basic average IN ONE UNIT.
    - Unconverted, GPCR's 71.3M-ADS count sat about 67% below its 218.0M-ordinary average and
      would have been refused; converted, it sits 1.8% from it and is used.
- **Sizing does NOT change, by design: no second path.** The universe already sizes every
  depositary line on Polygon's ADS-denominated count (#541), which needs no ratio. Measured
  beside it, the committed cap against EDGAR's ordinary count ÷ the ratio:
  - 34 of the 85 agree within 5%, 15 within 25%, and 30 are not comparable;
  - 6 are off by more than 25%: CIG, SQM, TGS, TME and ZLAB are multi-class or report an
    ADS-equivalent count;
  - so the EDGAR side is the unreliable one, and replacing #541 with it would be worse.

**THE MEASUREMENT WAS CORRECTED, in #837 before it merged (d11a9b38).** #837's first cut read
**81 of 85** primary depositary lines. This reader reads **77** and refuses 8, and three of the
first cut's values were WRONG:

| line | #837 measured | this reader | the filing says |
|---|---:|---:|---|
| RERE | 2 | **0.667** | "every three ADSs represent two Class A ordinary shares" |
| TAL | 1 | **0.333** | "each three representing one Class A common share" |
| SKM (theme) | 5 | **0.556** | "each representing five-ninths of one share" |

The four that moved from known to refused:
- **Units or CPOs, not shares:** KOF ("10 units"), TV ("five Ordinary Participation
  Certificates"), BSBR ("one unit"), VLRS (CPOs). The share count of a unit is not in these words.
- **Two ratios stated:** HIMX's 20-F describes its change from 1:1 to 1:2.

In the theme band 95 of 105 are known.
- **Newly read** (the measurement's patterns missed them): ASX 2, E 2, HMY 1, PBR 2.
- **Newly refused:** CX and FMX (units); HTHT (five stated values).

All 16 ranked-queue depositary lines are known, as #837 said.

**REAL RUN** (production code: `EntityResolver.ads_ratio` and `pe_current_and_percentile`;
2026-10-16 primary population; filings to 2026-10-16).

- **Ratios, 85 depositary-typed lines:** 77 known (59 from a 12(b) title, 18 from the text), 8
  refused.
  - Refused, each with its reason: BMA and GGB state none; GRFS and HIMX state two; BSBR, KOF, TV
    and VLRS count units.
  - Distribution: 1 ×24, 10 ×9, 2 ×8, 5 ×8, 3 ×6, 4 ×5, 20 ×3, 0.5 ×2, 8 ×2, 15 ×2, 25 ×2, and
    0.2, 1/3, 2/3, 2.5, 6 and 7 once each.
- **The 16 queue names, with their filings:**
  - QFIN 2, GPCR 3 (10-Q), JKS 4, IPX 10, DQ 5, MLCO 3, DBVT 5 (10-Q), JMIA 2 (text), LPL 0.5
    (text);
  - NBTX, PONY, WB, HSAI, ABVX, SID and IVA at 1.
- **P/E before → after**, on the 2026-10-16 store's bars and companyfacts fetched 2026-10-28.
  22 depositary lines have a reading:

  | line (tier, queue rank) | ratio | P/E level before → after |
  |---|---:|---|
  | EDU | 10 | 202.9× → 20.3× |
  | JOYY | 20 | 41.9× → 2.1× |
  | TIGR | 15 | 65.3× → 4.4× |
  | YMM | 20 | 41.7× → 2.1× |
  | GDS | 8 | 42.0× → 5.2× |
  | SIMO | 4 | 232.2× → 58.0× |
  | MLCO (T1, 219) | 3 | 26.9× → 9.0× |
  | TAL | 1/3 | 4.36× → 13.09× |
  | VIPS | 0.2 | 0.18× → 0.91× |
  | QFIN (T2, 1) | 2 | 0.258× → 0.129× |

  - **The percentile moved on 0 of the 22**, so no G3 outcome moves.
  - **QFIN's level is still read on a CNY EPS.** The currency is FPI1a's unit guard, not this
    build's.
  - **Ratio 1 leaves the level unmoved:** WB, HSAI, NICE, RLX, BILI.
- **Sizing:** 0 caps move. FPI4 does not touch the universe.

**HOW VERIFIED.**
- **Pins** (`tests/test_ads_ratio.py`, 35). Every ratio pin reads a REAL filing:
  `tests/fixtures/ads_ratio_covers.json`, 19 names, holding each name's cover lines and the real
  text around its depositary mentions. `ratio_from` on that cut equals `read_ratio` on the whole
  document, recorded per name and asserted.
  - **Positive:** the twelve hand-checked ratios (TSM 5, BABA 8, TM 10, HMC 3, BP 6, SHEL 2,
    HSBC 5, SMFG 0.6, KT 0.5, LPL 0.5, QFIN 2, GPCR 3), plus RERE 2/3, TAL 1/3 and SKM 5/9.
  - **Negative:**
    - BIDU and GRFS refused, every value named;
    - two disagreeing titles refused;
    - ASML refused (states none);
    - KOF refused (units);
    - a fraction never read as its numerator, including where only the numerator guard can
      act;
    - the title outranking the text.
  - **The P/E level ÷ ratio:** a refused ratio withholds the level, and the percentile is
    identical either way. A common stock is unchanged byte for byte.
  - **The run's row** carries the ratio or the refusal.
  - **`listing_basis`** reads only `ADRC`/`GDR`, once per issuer.
  - **Both production call sites pass `listing`** (an AST check).
  - **A stored candidate** carries `ads` only for a depositary line. All committed
    `candidate_records.jsonl` rows have no key and round-trip.
  - **GPCR's real 10-Q counts through the anchor:** counts converted, the count used, and
    unconverted refused. A refused ratio withholds every count; a common stock is untouched.
- **Mutations: 15 of 16 red.** The survivor puts the text rules' fraction patterns after the
  counts. It is EQUIVALENT: `_NOT_A_NUMERATOR` alone keeps a numerator from being counted, so the
  order cannot change an answer. The docstring now credits the guard, not the order. The
  title-rule order is load-bearing ("every three ADSs represent two") and has its own red mutant.
- **Existing pins.** Two red, both fixed:
  - a page with no `ads_ratio` must write no null (`dossier_json`'s `DROP_WHEN_NONE` gains it);
  - the committed candidate rows must round-trip (the store excludes a None `ads`).
- **ruff and `mypy --strict vinci/`:** clean.
- **No paid model call.**

**BOUNDARY.**
- **Populations:**
  - primary: the committed `universe_snapshot.jsonl` (2,065 lines, as of 2026-10-16), of which
    85 are `ADRC`/`GDR` by Polygon's 2026-10-17 reference pull;
  - theme band: the committed `theme_universe_snapshot.jsonl` (2026-08-24), 105 depositary-typed;
  - queue: the committed `ranked_queue.jsonl` (343 names, run 2026-10-16-01).
- **Filings:** each issuer's newest periodic report (10-K/10-Q/20-F/40-F) filed on or before
  2026-10-16 whose cover tags its symbols, up to three back. Read 2026-10-28.
- **P/E:** the 2026-10-16 store copy's bars to 2026-10-16. Annual diluted EPS from companyfacts
  fetched 2026-10-28.
- **Sizing comparison:** the committed cap's ADS count (Polygon details, 2026-10-17) against
  EDGAR `dei:EntityCommonStockSharesOutstanding` at its newest accession ÷ the ratio.
- **Code** on `fpi4/ads-ratio`, rebased on #837's merge (`1341c021`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The ratio is the filing's CURRENT one, applied to the whole P/E range.**
   - This is right where Polygon's ADS price history is adjusted for a ratio change, as it adjusts
     a split.
   - A ratio change inside the range on an UNADJUSTED history would bend the percentile.
   - The issuers that describe a change (BIDU, HIMX, GRFS, HTHT) are refused outright.
   - FALSIFIER: a line whose percentile series jumps by its ratio on the change date.
2. **Units and CPOs are refused, not resolved.** Six depositary lines (KOF, TV, BSBR, VLRS, CX,
   FMX) wait for a reading of what a unit holds.
3. **Not wired, measured:**
   - **The peer-cohort command** (`cli._pc_valuation`) uses only the percentile, which no ratio
     can move.
   - **The theme-intelligence copy** of the P/E call is behind the isolation boundary.
   - **A CIQ consensus EPS** for an ADR (R3's forward P/E) is in whatever unit CIQ quotes. It is
     not converted here; the first R3 record on a depositary line must check it.
4. **No committed page moves.** None of the 27 committed dossiers is a depositary line, and the
   next weekly run writes the first `ads_ratio` rows.
