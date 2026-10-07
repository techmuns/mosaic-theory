---
id: 2026-10-07-forward-consensus-layer
status: shipped
date: 2026-10-07
prs: [673]
supersedes:
superseded-by:
---

# Forward consensus reaches the record — FY+0..FY+2 paths, spreads and revision counts, outside the synthesis

**WHAT.** A new dossier-level field, `forward_consensus`, built by ONE builder
(`ciq_sheets.forward_consensus`) that both assembly and a refresh transform call. For FY+0..FY+2 of
nine scenario metrics (Revenue, EBITDA, EBIT, EPS Normalized, EPS (GAAP), D&A, CFO, capex, FCF) it
carries:
- **`paths`** — every Estimates→Trends vintage, from Current back to 18 months. `acceleration_read`
  reads only FY+0, and only back to 12 months.
- **`spreads`** — mean, median, high, low, σ and CIQ's raw estimate pair, from Estimates→Consensus.
  `ordered_by` records that CIQ orders capex High/Low by size (60 of 62 capex cells).
- **`revisions`** — up/down counts, analysts, and analysts still in consensus, per 1/2/3-month
  window.
- **`withheld`** — every cell not written, and why.

`refresh_dossier` gains a `top_level` seam with an allowlist (`forward_consensus` only), and
`forward_consensus_transform` lands the layer on a committed page without re-drawing its synthesis.
**This PR changes no committed page.** The artifact pass follows.

**WHY.** The analyst team's scenario feedback on AMZN (2026-10-07), checked claim by claim against
the committed record and the workbooks:
- FY27 levels were already on the page (financial_summary FY27E, #436), so that claim held only for
  their history and for FY28.
- The history of the FY+1/FY+2 figures was missing — now `paths`.
- Spreads beyond Revenue/EBITDA were missing — now `spreads`. FY27 EBIT is mean 140,734, median
  142,280, high 166,089, low 118,506, σ 11,745 and "49/53", matching the team's figures.
- FY+1/FY+2 revision counts were missing — now `revisions`.

**WHY OUTSIDE `mechanical`.** `MechanicalLayer` is the only synthesis input. Inside it, this layer's
numbers (424–891 per name across the 26, counting every numeric field; AMZN 891) would change every
five-draw prompt and widen the untraceable-figure check, for data no claim was written against. A
digest for the synthesis is a later decision with its own shape contract.

**THREE READ DEFECTS, FOUND ON THE REAL EXPORTS AND NOT REPEATED HERE:**
1. **Wrong section.** `consensus_rows` takes a metric's first title after the company-level block,
   so AMZN's 'EPS (GAAP)' would read a 2005 quarterly block: FY2026 median 0.01 against a true
   12.91, and a low/median/high check passes it. Here a title counts only under the section that
   the sheet's own Market Summary vouches for. The company-level section is matched on Revenue. The
   per-share section is matched on whichever EPS line the summary carries: EPS Normalized on 20
   names, EPS (GAAP) on 6.
2. **An unbounded summary.** `_market_summary_current_year` scans 60 rows past the Market Summary,
   so BRBR's 'EPS (GAAP)' answers 3.12 from the annual section. The new reader stops at the
   'Fiscal Years' banner, which sits in column 1, not 0.
3. **Mis-bounded Revisions blocks.** `horizon_read` ends a block at the next metric on its own list,
   so on AMZN 'EPS Normalized' ran to row 125, six blocks on. Here a block ends at the next block of
   any kind. `horizon_read` itself is NOT changed: it is a synthesis input, and the fix is its own
   PR (§5.0 row 30 (A)).

**A FIRST DESIGN WAS ABANDONED ON THE CORPUS.** The first version identified the Consensus block by
equality with the Trends 'Current'. That passed on AMZN and failed on 7 names:
- partly through my own header detection — PARR's year header jumps 2000 → 2003, and I had
  required consecutive years;
- partly for real — the two sheets differ by up to ~1.2% (ROST EBITDA FY2027 0.9%).

The within-sheet Market Summary test is exact.

**HOW VERIFIED.**
- **Fleet run** (26 names, the exports on disk): 676 paths, 624 spreads (92% of the 676 possible)
  and 1,971 revision counts. 21 cells were withheld, each with its reason. 14 are the pre-revenue
  ORKA and TECX, whose summary vouches for no company-level section. 7 are incomplete cells on CNXC
  and WERN.
- **Invariants:**
  - 624 of 624 spreads sit within max(0.01, 2%) of their Trends current; a wrong-section read is
    off by orders of magnitude.
  - 1,971 of 1,971 counts have in-consensus ≤ analysts and up + down ≤ analysts.
  - Every spread's `ordered_by` matches its values.
- **Refresh dry run** on copies of all 26 committed dossiers: only the new block changes. The
  mechanical layer (so the synthesis prompt) and the rendered page are byte-identical, and the
  block sits before `anchor`, which stays the last field.
- **Tests** (`tests/test_forward_consensus.py`): 58 pass locally; the CIQ-backed ones skip in CI.
- **Seven mutants, all killed:**
  - wrong section → 26 fail; unbounded summary → 1; `horizon_read`-style bounding → 1;
  - ordering always "value" → 22; no refresh allowlist → 1; `null` when absent → 1;
  - assembly wiring dropped → 1.
- Full offline suite green (counts in the PR).

**BOUNDARY.** The 26 committed dossiers on main @`6b42cd32`. The CIQ Estimates exports on disk, each
dated by its own export (AMZN ≥2026-10-06). Counts as of 2026-10-07.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The CIQ-backed pins skip in CI**, because the licensed workbooks are never committed. The
  wrong-section, summary-bound, block-bound and ordering pins therefore run only where the exports
  are on disk. This is the repo's standing pattern (#436).
- **The Consensus mean and the Trends 'Current' can differ by up to ~1.2%.** Both are kept, each
  labelled by its sheet.
- **Pre-revenue names carry no company-level spreads.** The summary vouches for no section, so they
  are withheld with the reason stated.
- **Not in this PR:** the artifact pass (row 30 (B)); the forward-multiple history and the
  synthesis-digest decision (row 30 (C)); the `horizon_read` fix (row 30 (A)).
