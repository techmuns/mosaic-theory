---
id:
status: open
date: 2026-11-19
prs: []
supersedes:
superseded-by:
---

# GOOGL rebuilt under the operator's $6 cap ($3.94, one build, 7 calls): on the 2026-11-19 CIQ export R1 prices $227.10 at the 2026-11-18 close's 17.58x, passed by the event rule; the EV/EBITDA basis pairs one day's figures; the prose no longer quotes $144,827M. A known, pre-existing defect, on main too, shows more here: the catalyst reader takes other companies' Key Developments as Alphabet's (Lyft's; → W85) (pages only, $3.94)

**THE RULING.** The operator's words were "Yes, cap $6", relayed by coordinator B, for a build after W73's code PR (#1144, merged as `bc1c0e16`). B's brief:
- hash-check the Drive export (comps `8a946223e6`);
- run the $0 precheck first, and on exit 1 STOP before any spend;
- one build under the cap, its `assembly_runs` file committed and its actual spend reported;
- the full offline suite on the committed result;
- a pages-only PR.

**WHAT.**
- **The spend: $3.94** (`usd` 3.944441, list price). One build, written on its first attempt: 7 model calls, 0 failed.
  - The calls: the maturity phase, the operating drivers and five synthesis draws.
  - No re-roll. A second build would not have fit the cap: past GOOGL builds cost $2.38 to $4.43.
  - The run file: `data/snapshots/assembly_runs/2026-11-19T22-31-21Z-dfbe9e9a.jsonl`.
- **R1 prices again.** Main's page withheld the screen value, since its multiple was the 2026-09-30 close and Alphabet's 8-K item 2.02 of 2026-10-28 outdated it. On the 2026-11-19 export:
  - R1 prices **$227.10** ($225.05 diluted; EV/EBIT 21.6x) at the **2026-11-18 close's 17.58x**, with the median 17.54x beside it.
  - The event rule's verdict: "nothing reported after it by the page's close of 2026-11-18". The drift is 0.0%: the close is the page's own.
  - The split: "Screen value $227.10 at 17.6x (the 2026-11-18 close) = $274.58 on current EBITDA ($185,516M) − $47.48 margin reversion".
  - The operator's R3 tag (2026-09-01) stands, the machine's R4 read beside it.
- **The EV/EBITDA basis pairs one day's figures** (W65). `valuation_basis.current_multiple` is CIQ's NTM P/E 20.51x on the 2026-11-18 snapshot, against the page price of the same day ($282.44): 0 days apart, where main's page was 12.
- **$144,827M is gone** from the page and from its synthesis. W80's refusal of a $0 refresh over it no longer applies: this was a full build.
- **What else the new export moves.**
  - The forward-consensus multiples, the peer grid, the credit panel, the catalyst path and the financial summary are all re-read at 2026-11-18.
  - The page's price is $282.44, from $293.45.
  - The synthesis lean stays `mixed`.
  - **The four forward bands are withheld.** CIQ's forward multiple history now ends in a partial 2026-11-18 column reading "-". So W50's rule withholds EV/NTM Revenue, EBITDA, EBIT and P/NTM EPS: "no current, and an older close is not one". The 2026-09-30 bands they carried are not priced in its place.
- **The transcript evidence** went to the operator's spool (`$VINCI_EVIDENCE_SPOOL`, the `driver-evidence` folder beside `manual/ciq` on the shared Drive). It went from 2,926 to 3,015 files: 89 new records. No page field quotes a transcript.

**A KNOWN, PRE-EXISTING DEFECT, OUT OF SCOPE HERE → W85** (coordinator B, 2026-11-19).
- **The reader.** `mechanical._catalyst_calendar` turns any forward-dated sentence in CIQ Key Developments into a "management-stated" catalyst. It never checks whose development it is.
- **It is already on main.** Main's GOOGL page prints a Lyft row (Sep-30-2026) as its Next catalyst. Per B, UBER carries a Wonder/Zipline row and AMZN a Kartoon Studios row. B is proposing the fix to the operator as W85: $0 code, then a $0 refresh of the pages it reaches.
- **What this rebuild adds on GOOGL.** The new export (`68170f53b6`) names other companies' developments alongside Alphabet's: Microsoft, NVIDIA, AMD, Broadcom, QUALCOMM and Lyft.
  - **The calendar's 3 rows.** Two are Lyft's: "Early access to the Lyft app rolls out in Barcelona and Hamburg first…" (Sep-30-2026, on main too) and "starting November 5, 2026, and marks the latest expansion of Lyft's growing partnership…" (Nov-05-2026, new).
  - **The main body's Next catalyst** prints the Sep-30 row, dated ~2026-10, as on main.
  - **The two scenario mirrors** (`frontend/scenarios/GOOGL*.json`) now take the Nov-05 row as their next catalyst. On main they read "Next results print, 2027-01-30".
  - **One operating-driver event row** (`operating_drivers.rows[8]`, Nov-05-2026) is Lyft's.
  - The synthesis does not mention Lyft.
- *Corrected 2026-11-20, before merge.* This section first called the defect new and said main's page carried none of it. B's review showed main's page already prints the Sep-30 row.

**HOW VERIFIED.**
- **The inputs:**
  - **Drive's 11 GOOGL exports** (a real folder, not a link), hashed in place:

    | export | sha256[:10] |
    |---|---|
    | comps | **`8a946223e6`** (B's) |
    | credit health | `ddd54c74f6` |
    | customers | `b93c09e890` |
    | financials, annual | `33deb718e8` |
    | financials, quarterly | `976c63d857` |
    | key developments | `68170f53b6` |
    | profile | `2ce05770b4` |
    | suppliers | `c58db0e2b6` |
    | estimates | `b77580d2db` |
    | Q2 2026 call | `cab0759d72` |
    | Q3 2026 call | `ae41f0dd5f` |

    None of the committed page's stamps (`482debf275`, `9a120cb5ae`, `f494e7869b`) is on disk.
  - **The price store:** a copy of the impact store, refreshed through 2026-11-18, the latest close.
- **The precheck ran twice. The first exited 1, and the cause was my store, not the export.**
  - The copy held GOOGL, and the peers it reads, only from 2026-08-05.
  - That gave 8 regressions: the 52-week range, the 180-day returns, the drawdown shape, the P/E percentile, and 3 of 508 Form 4s SEC did not serve. It also gave one post-spend refusal, a drawdown read short of its window.
  - The fix: per-symbol bars backfilled from 2024-11-20 for GOOGL, SPY and the seven peers the committed page read from 2026-04-15 (the history that page read), and the six full series brought through 2026-11-18.
  - The second run: **0 regressions, 0 post-spend refusals, exit 0**. It listed 47 fields that change value, source or note, and 688 block leaves. Nothing was spent before that exit 0.
- **The build** reproduces what the precheck showed, with the synthesis on top.
- **The full offline suite** passed on the committed result (`bin/commit`), with the CIQ link and the store set aside, as CI runs.
  - Its first run on these pages failed one pin, and the pin was wrong, not the page. `test_w65_basis_one_date.py::test_a_page_built_before_the_fields_sends_the_same_synthesis_facts` asserted that no committed page sends W65's `multiple_close`/`days_apart` keys to the synthesis. That held only while every page predated W65; this rebuild is the one W65 left waiting, and its block carries them.
  - The pin now holds presence parity, as its round-trip twin does: a key is sent exactly when the committed block carries it. On a pre-W65 block that is the old assertion exactly.
  - The fix is its own commit (`2c76f927`, test only), before this one. It passes on main's 26 pages and on this page; the old assertion fails on this page with `('GOOGL', 'multiple_close')`.

**BOUNDARY.**
- **Code:** main `bc1c0e16`, extraction `2026-11-19.the-screening-anchor-prices-a-dated-close-judged-by-the-event-rule`.
- **Build:** started 2026-11-19T22:31:21Z, finished 22:48:20Z.
- **The store:** frontier 2026-11-18. `price_store.declared_path` names the build's worktree folder, `w73-googl-rebuild`, since removed; the store is kept in this session's scratch. Its 15 series each cover at least the window the committed page read.
- **Spend:** list price over the build's 7 metered calls, as `run_metrics` priced them.
- **The defect's count:** this page's `catalyst_calendar` (3 rows) and `operating_drivers` event rows, at this build, against main's page. Other pages are B's, measured for W85.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$3.94 of the $6 cap.**
- **The Lyft rows stay on the page** until W85's reader fix and its $0 refresh. Main's page already carries the first of them.
- **The forward bands stay withheld** until CIQ's history carries a current at its export date.
