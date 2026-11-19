---
id:
status: shipped
date: 2026-11-19
prs: [1138]
supersedes:
superseded-by:
---

# The fast-values page refresh: all 10 refreshed active pages move ($0, `price_values_transform` then `ev_gap_transform`, no LLM). Each page's cap is now its close × its count, with CIQ's cap printed beside it where the two disagree by more than 2%. Each TEV is that cap + CIQ's claims, and the peer implied levels and the EV gap are struck on it. On 9 of the 10 the cross-sectional multiples are struck at the close as well. GOOGL's comps and estimates exports on disk are not its page's, so its cross-sectional read stays as stored. BRBR is excluded (A's rebuild), and the 15 watch pages are left as committed.

**WHAT.**
- **Pages refreshed.** Head code is main `8bc138cd`, which carries #1132 (`ccadf6ab`) and IT's Note B tag (#1133). Each of the 10 pages went through `refresh_dossier` with `price_values_transform(t, ciq_tev_claims=…)` followed by `ev_gap_transform(t)`, the order `refresh_dossier` composes. The 10 pages are EPAM, GOOGL, IT, LLY, NCNO, SMPL, TJX, VITL, VRRM and WERN.
  - **CIQ's claims come from the page itself.** They are its own `ev_bridge.ciq_tev_claims`, CIQ's TEV less its cap, read off the export the page was built from (round 1 of #1132). On every page the written `stock_info.ciq_tev_claims` equals that figure.
  - **The export-identity check** is the one #1132 deferred to this refresh. Each transform was handed only the on-disk CIQ files whose sha256 is in the page's own `inputs.ciq`. The primary checkout's folder was read in place.
    - 9 pages matched every recorded export, comps and estimates included.
    - GOOGL matched 4 of its 11. Its comps, estimates, both financials, credit-health, Key Developments and profile exports on disk are the 2026-11-19 re-export, not the ones its page records. So its cross-sectional read stays as stored, and its consensus vintage is carried, not re-read.
  - `refresh_dossier` re-rendered each `dossier.md`. `mirror_to_frontend()` then wrote `frontend/dossiers`, byte-identical to each page on all 10.
- **The cap at the close** (`stock_info.market_cap_at_close`) is the page's close × its EDGAR share count. CIQ's comps cap sits beside it (`stock_info.cap_cross_check`, at CIQ's own date), and the Snapshot prints it only beyond the 2% tolerance. Below, the gap is CIQ's cap against the cap at the close:

  | page | cap at the close | CIQ's cap (its date) | gap | printed |
  |---|---|---|---|---|
  | EPAM | $8,307.6M | $8,128.5M (2026-11-06) | −2.2% | yes |
  | GOOGL | $3,607,674.3M | $3,431,315.0M (2026-10-30) | −4.9% | yes |
  | IT | $12,174.7M | $12,174.7M (2026-11-11) | 0.0% | no |
  | LLY | $1,352,123.4M | $1,262,675.3M (2026-10-30) | −6.6% | yes |
  | NCNO | $2,367.4M | $2,423.5M (2026-10-27) | +2.4% | yes |
  | SMPL | $1,097.9M | $1,083.2M (2026-11-03) | −1.3% | no |
  | TJX | $150,080.5M | $162,059.2M (2026-10-16) | +8.0% | yes |
  | VITL | $406.6M | $408.8M (2026-11-06) | +0.5% | no |
  | VRRM | $252.3M | $332.9M (2026-11-06) | +31.9% | yes |
  | WERN | $1,669.8M | $1,669.8M (2026-11-11) | 0.0% | no |

  No ratio is a whole number, so no page prints the share-basis wording. Each page's close is 2026-11-11, except VRRM's, which is 2026-11-17.
- **The TEV at the close** (`implied_expectations.tev_at_close`) is the cap at the close plus CIQ's claims. It replaces the simple TEV, which was CIQ's cap plus the comps "Net Debt" line. The four peer-median implied levels are struck on it; the † identity rows are unchanged.

  | page | simple TEV (before) | TEV at the close |
  |---|---|---|
  | EPAM | $7,309.7M | $7,489.4M |
  | GOOGL | $3,316,548.0M | $3,510,930.3M |
  | IT | $13,855.0M | $13,855.0M |
  | LLY | $1,306,533.3M | $1,395,981.4M |
  | NCNO | $2,678.8M | $2,638.1M |
  | SMPL | $1,342.3M | $1,357.0M |
  | TJX | $170,372.2M | $158,393.5M |
  | VITL | $513.8M | $511.6M |
  | VRRM | $1,271.2M | $1,190.6M |
  | WERN | $2,625.7M | $2,625.7M |

  Three pages' simple TEV read a Net Debt line that is not CIQ's TEV less its cap. These are GOOGL (−$114,767.0M against −$96,744.0M), NCNO ($255.3M against $270.7M) and EPAM (−$818.8M against −$818.2M); on the other 7 the two figures agree. The implied levels move on 9 pages, on WERN in one row by $0.1M. On IT only their `source_ref` moves.
- **The EV gap's market side** is the TEV at the close, and each gap gains `vintages.tev_close_date`. Five pages compute a gap; the other five (GOOGL, LLY, TJX, VITL, VRRM) stay `not-computed`, as committed.

  | page | EV gap before → after | printed |
  |---|---|---|
  | EPAM | 0.8212 → 0.8015 | 0.82x → 0.80x |
  | IT | 1.2383 → 1.2383 | unchanged |
  | NCNO | 0.6940 → 0.7047 | 0.69x → 0.70x |
  | SMPL | 1.5363 → 1.5196 | 1.54x → 1.52x |
  | WERN | 1.1884 → 1.1884 | unchanged |

  IT and WERN move only past the fourth decimal: the cap at the close equals CIQ's cap to within $0.04M. The gap's bridge nets CIQ's claims, so its per-share figure moves on the two pages whose Net Debt line differed: EPAM $132.06 → $132.05 and NCNO $14.51 → $14.37. On SMPL only the bridge's "against TEV" figure moves.
- **The cross-sectional multiples** are the name's own multiples at the close, against CIQ's peer medians at CIQ's date. They move on 6 pages and are only re-dated on 3 more (IT, VITL, WERN). The peer medians are unchanged everywhere.

  | page | EV/EBITDA (vs median) | P/E (vs median) |
  |---|---|---|
  | EPAM | 8.7x → 8.9x (+18% → +20%) | 20x → 20.4x (+16% → +19%) |
  | GOOGL | as stored (comps export not the page's) | as stored |
  | IT | 9.4x, unchanged (−30%) | 13.8x, unchanged (−45%) |
  | LLY | 28x → 29.9x (+87% → +99%) | 46x → 46.6x (+59% → +61%) |
  | NCNO | 27.3x → 26.7x (−64% → −65%) | 74.3x → 72.6x (+54% → +51%) |
  | SMPL | 6.1x → 6.2x (−20% → −19%) | NM |
  | TJX | 13.3x → 12.4x (+94% → +81%) | 27.3x → 25.3x (+74% → +61%) |
  | VITL | 1.4x, unchanged (−87%) | NM |
  | VRRM | 3.6x → 3.4x (−69% → −71%) | 9.1x → 6.9x (−58% → −68%) |
  | WERN | 6.2x, unchanged (−56%) | NM |

- **IT's Note B tag (#1133) is unaffected.** It is on `scenarios/IT.json`, which this refresh does not write. IT's rendered page moves only in the lines listed under HOW VERIFIED.
- **The event rule moves nothing here.** The freshness check runs at assembly and in the $0 precheck (`assemble._freshness_check`, `prespend`), not in `refresh_dossier`. Every stored freshness verdict is therefore as committed, and the rule reaches each page at its next build.
- **BRBR is EXCLUDED** (coordinator B, 2026-11-19). Its rebuild is A's, and its on-disk export is the new 2026-11-19 one.
- **The watch pages are left as committed** (operator ruling, 2026-11-13): AMZN, BURL, CNXC, FUBO, MCK, NFLX, NKE, ORKA, PARR, ROST, TECX, TGT, UBER, V and WLK. Each takes the fast values at its next build once it is active.

**WHY.**
- #1132 put the fast values in code (operator, 2026-11-19: "Approve, $0 refresh"), and no committed page carried them. Each page's cap, TEV and multiples were still CIQ's export-date figures beside a later close; VRRM's cap was CIQ's $333M against $252M at its own close.
- Coordinator B ordered this refresh as its own artifact-only PR once #1132 merged.

**HOW VERIFIED.**
- **Every page diffed leaf by leaf** against main `8bc138cd` (a copy of each page taken before its refresh).
  - **Added:** 29 leaves on every page, 290 in all.
    - `stock_info.market_cap_at_close` (4), `stock_info.cap_cross_check` (9) and `stock_info.ciq_tev_claims` (4).
    - `implied_expectations.tev_at_close` (4) and `tev_close_date` (1).
    - `ev_gap.vintages.tev_close_date` (1).
    - One appended `layer_refreshes` entry (6), naming `mechanical.ev_gap`, `mechanical.stock_info` and `mechanical.valuation`.
  - **Changed:** 110 leaves, all inside those three blocks. They are the implied levels and their `source_ref`, the cross-sectional value, and the five computed gaps' figures.
  - **Removed:** 0 leaves.
  - No other block moves on any page: not `synthesis`, freshness, `anchor` or `qa_flags`. `refresh_dossier` refuses a refresh that moves a figure the stored synthesis cites, and it refused none of the 10.
- **Each md moves only** in these places:
  - the header's "layers refreshed to" stamp;
  - the Snapshot's cap (8 pages; not IT or WERN, whose cap is within $0.04M of CIQ's);
  - the "vs peers" and "Cross-sectional" lines (9 pages; not GOOGL);
  - the implied-expectations TEV line (10 pages) and its peer rows (4 on 8 pages, 1 on WERN, none on IT);
  - the EV gap's TEV vintage (the 5 computed pages), and its ratio rows and bridge on EPAM, NCNO and SMPL;
  - the TEV footnote;
  - the rendered refresh entry under "Record & reproduce".
- **The full offline suite passed** on the committed artifacts before the push (`bin/commit`).
  - Its first run on these pages was RED on 17 nodes of three pins written for the pre-#1132 page shape: 2 cap-drift, 10 EV-gap vintages and 5 idempotence. None of them had met a page carrying the new fields.
  - #1137 made those pins hold on both shapes. It merged first as its own tests-only PR, so no code rides in this artifact commit.
  - This commit is rebased on `377bfe86`. Re-run there from main's own pages, the refresh is byte-identical on all 40 page files.
- **The cross-setup validation** (`python -m vinci.impact run`, RUNBOOKS §o) is in the PR body.

**BOUNDARY.**
- **Roster:** `data/coverage_roster.jsonl` at `8bc138cd`, the latest row per ticker: 11 active and 15 watch, 26 committed pages.
- **Code:** main `8bc138cd`, 2026-11-19. Re-run byte-identical on main `377bfe86` (after #1134, #1135 and #1137), the base this commit is rebased on.
- **Inputs:**
  - each page's own stored layer (close, share count, CIQ's cap and claims);
  - the CIQ exports in the primary checkout as of 2026-11-19, read in place, never copied, and admitted only where their sha256 is in the page's `inputs.ciq`;
  - no EDGAR, Polygon or Tiingo request, and no model call ($0).
- **Count:**
  - Refreshed: 10 active pages (11 active less BRBR). All 10 moved.
  - Full export identity: 9 pages. GOOGL matched 4 of its 11 recorded exports, which leaves its cross-sectional read as stored.
  - Cap printed beside CIQ's: 6 pages beyond the 2% tolerance (EPAM, GOOGL, LLY, NCNO, TJX, VRRM); 4 within it (IT, SMPL, VITL, WERN).
  - TEV at the close against the simple TEV: different on 8 pages, equal to $0.1M on 2 (IT, WERN).
  - EV gap: computed on 5 pages; moved at print precision on 3 (EPAM, NCNO, SMPL).
  - Cross-sectional: moved on 6 pages, re-dated only on 3 (IT, VITL, WERN), and left as stored on 1 (GOOGL).
  - Excluded: 1 page (BRBR). Left as committed: 15 watch pages.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **GOOGL's page mixes two dates until its rebuild.** Its cap, TEV and implied levels are struck at the 2026-11-11 close, while its cross-sectional multiples stay CIQ's 2026-10-30 read. The comps export on disk is the 2026-11-19 re-export, and admitting it would put a workbook the page was not built from under the page's own `inputs.ciq`. It clears at GOOGL's rebuild on that export.
- **The freshness verdicts are as committed** until each page's next build, since the refresh does not run the event rule.
- **BRBR and the 15 watch pages carry none of this** until each is rebuilt (BRBR by A) or re-derived once active.
- **#1132's deferrals stand:** the CIQ-bridged share count on FUBO, NKE and V; `_peer_gap_question`'s unrestated signs; 10-Q/A and 10-K/A as events.
