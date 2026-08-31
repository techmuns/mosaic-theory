---
id:
status: shipped
prs: [541]
date: 2026-08-31
supersedes:
superseded-by:
---

# ADS-denominated caps — the share count now matches the price's unit, and TSM stops being a $10.6T company

**WHAT.** For depositary receipts (Polygon types `ADRC`/`GDR`, hoisted as
`universe.DEPOSITARY_TYPES`) the universe builder now sizes market cap with
`share_class_shares_outstanding` — the count denominated in the TRADED unit — instead of the
filer's XBRL count, which is denominated in ORDINARY shares. New `EodClient.share_class_counts`
fetches it (per-ticker details endpoint, cached a day, scoped to the ~375 ADR/GDR tickers that
have a close). An ADR whose ADS count will not resolve is DROPPED at a new stage
`ads_count_unresolved` — never sized by assuming 1 ADS = 1 ordinary share. Admitted ADR rows stamp
`Polygon close x Polygon share_class_shares_outstanding (ADS-denominated)` in their committed
`source`; `ads_count_used` counts them.

**WHY — MEASURED BEFORE ANY CODE WAS WRITTEN.** An ADR's price is per ADS; its filed XBRL count is
per ordinary share; nothing converted between them. On the live 2026-08-24 snapshot:

| name | our cap (ordinary count) | Polygon's own market_cap | cap with the ADS count |
|---|---|---|---|
| TSM | **$10,635.4B** | $2,165.5B | **$2,127.1B** |
| NTES | $392.5B | $78.6B | $78.7B |
| GSK | $223.5B | $101.8B | $104.7B |
| SNY | $55.7B | $107.4B | $110.4B |
| SAP / ASML / ARM / NOK / INFY / STM | — | — | unchanged (~1:1) |

**TSM's error was not cosmetic.** $10.635T exceeded the theme band's $10T ceiling, so the most
important name in the AI silicon layer — a natural `silicon-ecosystem-moat` candidate — was
dropped `out_of_band` and sat in NO band, invisible to the ai-value-migration scan on arithmetic
rather than judgment. The ceiling's own comment said *"a name exceeding it should re-open this
knob, not vanish"*: the falsifier fired and nothing was watching.

**THE MEASUREMENT CHANGED THE DESIGN — the brief's own verify-at-build gate doing its job.** The
brief proposed extracting the ratio from each 20-F cover page ("each ADS represents N ordinary
shares") with a regex, cross-checked against Polygon. Probing first showed that unnecessary:
`share_class_shares_outstanding` is ALREADY in the traded unit, so `price x that count` needs no
ratio arithmetic at all — verified against Polygon's independent `market_cap` across 13 ADRs
(implied ratios 5.00 TSM, 4.99 NTES, 2.13 GSK, 0.50 SNY, ~1.00 for the six unaffected names). A
regex over cover-page prose was replaced by a structured value, which is what the
parsers-consume-structured-values rule asks for anyway. The implied ratio survives only as the
diagnostic that PROVED the mechanism, not as machinery.

**HOW VERIFIED.**
- 5 pins in `tests/test_ads_denominated_cap.py`, each on the observed shape: an ADR is sized by
  its ADS count (the TSM shape, 5:1); an ADR with no ADS count DROPS loudly (2 of a 60-name sample
  carry none); a domestic `CS` name never touches the path and keeps its EDGAR tag; the CEILING
  regression pinned at the band boundary, because a wrong cap does not merely mis-label — it
  deletes the name from the population; and a coherence pin that `DEPOSITARY_TYPES` ⊆ the admitted
  instrument allowlist.
- SIX EXISTING TESTS REDDENED, which is the evidence the change binds the real builder: four EOD
  stubs lacked `share_class_counts` (extended — all are domestic-CS fixtures, so `{}` is the
  truthful answer), and the retention guard correctly refused both a 9th drop stage and a new
  admitted-name counter (both allowlisted WITH their reason: `ads_count_unresolved` IS a drop
  stage and emits its row through `_drop`; `ads_count_used` counts admitted names and has no drop
  to evidence).
- REAL RUNS, both bands at the committed vintage 2026-08-24 from a cold DB over main's entity
  master. **TSM is now in the theme band at $2,127.1B** (Polygon's independent market_cap:
  $2,165.5B) and **NVO at $159.1B**, both stamped
  `Polygon close x Polygon share_class_shares_outstanding (ADS-denominated)`. 356 names sized by
  an ADS count per pass; 18 dropped at `ads_count_unresolved`; `no_shares` fell **1,366 → 1,240**.

- **THE ERROR WAS FAR LARGER THAN THE MOTIVATING CASE.** TSM's 5x was not the worst; the theme
  band was carrying multi-TRILLION caps:

  | name | before | after | factor |
  |---|---|---|---|
  | BSAC | $6,802.9B | $17.0B | ~400x |
  | BCH | $4,347.8B | $21.7B | ~200x |
  | TM (Toyota) | $2,526.1B | $282.9B | ~9x |
  | AMX | $1,434.3B | $71.3B | ~20x |
  | HSBC | $1,787.8B | $357.4B | ~5x |
  | EC | $712.6B | $35.6B | ~20x |
  | PDD | $495.7B | $123.9B | ~4x |
  | NTES | $392.5B | $78.7B | ~5x |

  51 theme-band and 26 primary-band caps moved by more than 2%.
- **BAND MEMBERSHIP MOVED, AND THE PRIMARY BAND IS THE VALIDATION POPULATION** — the operator
  decision this record exists to surface, and the ordering fix made it LARGER. **PRIMARY
  2,000 → 2,039: 49 ENTERED, 10 LEFT.** Entering: ASR ATAT ATHM BILI BMA BSBR BZ CIG CSAN DRD EDU
  ELPC ELVR FINV GDS GGAL GPCR GRFS IMOS IQ JOYY KC KOF MESO MNSO MOMO OMAB PAC PAM RERE SBSW
  SIMO SSL TAL TEO TGS TIMB TKC TME VEON VIPS VIST VLRS VNET WPP WRD XPEV YMM ZLAB — foreign
  names that were either MIS-SIZED into the wrong band or dropped entirely for want of a count
  they never needed. Leaving: ABVX FMS JZ KEP LOMA NAMI PKX SBS SKM YXT (corrected caps outside
  the band; six moved coherently into the theme band). **THEME 907 → 913**: 32 entered (TSM, NVO,
  SONY, SE, TAK, JD, BIDU, ERIC, VALE, ITUB, VOD …), 26 left for the primary band.
  Every move is a name that was in the WRONG band on arithmetic, or absent on a requirement that
  did not apply to it — not a redefinition of the band. **At 49 names (~2.5% of the population)
  this warrants explicit operator sign-off rather than the coverage-repair default.**
- ruff + `mypy --strict` clean; offline suite **3262 passed**.

**REVIEW ROUND (2026-08-31, medium code-review — three findings, one of them substantive).**
1. **THE GATE RAN IN THE WRONG ORDER, and it cost the change most of its value.** The first draft
   dropped a name at `no_shares` (missing EDGAR XBRL count) BEFORE reading the instrument type —
   so a depositary receipt was required to have a count that the very next branch discards.
   Measured: **eight of the nine names lost at `no_shares` carry a perfectly good Polygon ADS
   count** — NVO (3,390,128,000), SONY, ERIC, TAK, GRAB, JD, SE, BIDU; only AZN genuinely has
   neither. **NVO is the exact name the FPI1 follow-on was written to recover**, and this change
   was already fetching what sizes it. The type is now read FIRST: for an ADR the XBRL count is
   never consulted, so its absence is not fatal. NVO, SONY, ERIC, TAK, JD, SE and BIDU are all
   admitted. (GRAB is NOT a depositary receipt — it needs the XBRL count it lacks, so it remains
   an FPI1 case, correctly.)
2. `DEPOSITARY_TYPES` had been inserted BETWEEN the `DROP_STAGES` docstring and `DROP_STAGES`,
   leaving a comment about "EVERY drop this builder can make" attached to the instrument-type
   tuple. Restored to its own constant.
3. This record and the PR body deferred those eight names to Phase 2, which stopped being true
   once (1) was fixed in the same PR. Corrected here.

Two pins hold the ordering in BOTH directions: an ADR with no XBRL count is admitted on its ADS
count, and a DOMESTIC name with no XBRL count is still dropped at `no_shares` — so the fix cannot
quietly become "nobody needs a share count".

**PHASE 2 IS NOW MUCH SMALLER THAN THE BRIEF ASSUMED.** FPI1 was scoped to recover IFRS-only
filers via per-name `ifrs-full` reads. For depositary receipts that is no longer needed — the ADS
count resolves them. What remains for FPI1: non-depositary foreign filers whose shares are
IFRS-tagged (GRAB shape), and names with no count in any source (AZN). Re-scope before building.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- SOURCE TIER: an ADR's cap now rests on a Polygon reference count rather than an EDGAR filing.
  That is a deliberate trade — the filing's number is in the wrong unit, so it is precise and
  wrong — and the row's `source` says exactly which count sized it. The EDGAR count remains
  primary for every domestic name.
- ~375 per-ticker reference calls on a cold cache (a day's TTL), once per build.
- VINTAGE: Polygon's share count and the XBRL count have different as-of dates, so the two
  disagree by a few percent even where the ratio is 1:1. Immaterial for a COARSE band; it would
  not be for a valuation, and this number is never used as one.
- 8 depositary receipts are now dropped that were previously admitted on a mis-scaled cap
  (`ads_count_unresolved`). That is the intended trade: absent beats wrong, loudly.
- NOT FIXED HERE: names still absent for a MISSING share count (NVO, AZN, TAK, BIDU, JD, SE,
  GRAB, SONY, ERIC) — that is FPI1, the brief's Phase 2, and it stays out of this PR.
