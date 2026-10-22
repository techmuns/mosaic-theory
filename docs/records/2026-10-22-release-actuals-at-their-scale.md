---
id:
status: shipped
date: 2026-10-22
prs: [777]
supersedes:
superseded-by:
---

# A release actual is read at its own scale, never out of a range, never off a sub-line, and a quarter keeps its quarter — fixed in the parser and landed on 15 pages without a re-assembly

**WHAT.** The release parser (`vinci/edgar/release_parse.py`) produced wrong numbers. Two of them
reached the visible card a reader sees. The defects were reported on 2026-09-17 and never fixed (STATE
row 28). They were found live on 2026-10-22 by a diagnosis the operator asked for ("go on 3").

| defect | example on main's pages | what the page carries now |
|---|---|---|
| a guidance RANGE read as an actual (`_RECON`'s lookahead backtracked into the digits) | VRRM's card: "adj EBITDA 2026 **$38.0M**; adj EPS 2026 **$1.10**" out of "$380 million to $385 million" / "$1.19 to $1.25" (on the card for 104 days); "adj EPS 2025 $1.30" out of "$1.32 to $1.38" | no actual; the range is refused with a quote of it in `qa_flags` |
| billions stored as millions (the scale word was matched and thrown away) | UBER adjusted EBITDA 2.5 / operating income 1.9, 2.1; V net income 6.1–6.3; FUBO revenue 1.549 / 1.574 / 1.482 | 2,500 / 1,900 / 2,100; 6,100–6,300; 1,549 / 1,574 / 1,482 ($M) |
| a sub-line read as the company's revenue | V "Other revenue of $1.5 billion" as V's revenue; FUBO "North America revenue of $1.57 billion" in the slot of its $1.574bn total | V's net revenue $10.9–11.6bn; sub-lines refused (an allowlist of the words a total may follow) |
| a basis-point guide printed as dollars | SMPL's card: "gross margin outlook: **$-350.0–$-300.0M**" | "−350 to −300 bps" |
| a quarter filed under a bare year (headers "Full-Year" / "FISCAL 2026 FOURTH QUARTER" unread; a table's date column read as the period) | TGT Q4 adjusted EPS $2.44 as FY2025, $2.41 as FY2024; NKE gross margins 40.6% / 40.2% / 49.2% as 2024 / 2025 / 2025 | TGT $2.44 as Q4 2025 and its FY $7.57 read; NKE Q2 2026 / Q3 2026; the Q4 margin and the "$2.41 in 2024" comparison refused, since the release does not state their period |

**The parser rules, one per defect:**
- **One amount token for every actual:** an atomic number that ends in a digit, a CAPTURED scale
  (billion/bn/B, million/mm/M, thousand/K, converted to $M), and a CAPTURED range tail
  (to / through / dash) that is refused. The same token now serves the reconciliation rows, revenue,
  the sub-unit check, one-offs and event impacts.
- **A per-share figure** that states a scale is refused, and so is **a total** that states none:
  `_scaled` never assumes $M.
- **Revenue** is read only after an allowlisted word. That list was measured on the 113
  "revenue(s) of $" statements in the 118 releases. "Net product revenue" counts as a total only
  where the release names no other revenue line (the Organogenesis fixture).
- **A figure joined by a bare "and" to a compared amount is refused** (TGT Q1: "…prior-year GAAP EPS
  of $2.27 and Adjusted EPS of $1.30."). So is a quarter compared with a bare year (TGT Q4: "$2.41 in
  2024").
- **Headers:** hyphenated forms ("Full-Year", "fourth-quarter") and year-first forms ("FISCAL 2026
  THIRD QUARTER") are read. A year inside a numeric date ("5/31/2025") is not a figure's period.
- **`_fmt_guide_range` prints `bps` in basis points,** signed.

**On the pages.** The new `refresh.release_figures_transform` (deterministic, from the release cache,
no model call) re-reads every cited exhibit's ACTUALS: the reconciliation rows, one-offs and event
impacts. It maps them back exhibit by exhibit, as assembly parsed them, and recomposes the visible
card from them. GUIDANCE is not re-read. Results:
- **15 of 27 pages move** (AORT, CNXC, EPAM, FUBO, IT, MVST, NFLX, NKE, SMPL, TGT, UBER, V, VITL,
  VRRM, WERN), **12 do not, 0 refuse.**
  - Ten carry moved figures: AORT, CNXC, FUBO, NKE, SMPL, TGT, UBER, V, VITL, VRRM.
  - Five gain only the new refusal notes: EPAM, IT, MVST, NFLX, WERN.
- **The card text changes on four pages:**
  - VRRM: the range-made figures are gone;
  - SMPL: bps;
  - VITL and AORT: Q4 relabelled, plus AORT's prior-year contrast.
- **#622's period fixes land with them.** The pages had been assembled before #622, and the transform
  re-reads with today's code. CNXC's Q4 figures had been filed as FY2025; its true FY2025 is now
  read (revenue $9,825.8M, adjusted EBITDA $1,469.3M). AORT, SMPL, VITL and VRRM get the same kind of
  relabel.
- **The two lines built from these rows were re-proven, not left behind.** For CNXC, FUBO, SMPL and
  VITL, the full-year/LTM inputs of `basis_triangulation` and `guide_verification` move.
  - Each line was first recomputed from the page's OLD rows, using the CIQ export and record as read
    today, and had to match the stored line byte for byte. All four did.
  - Then the new rows' line was written. It came back identical on all four.
- **VITL is in the pass.** Its anchor hold (row 32 (11)) is untouched; its release rows were wrong
  labels (a Q2 2025 figure filed as fiscal 2026).
- **A new refresh guard,** `moved_cited_release_figures`, refuses a page whose kept synthesis cites
  an old release figure the page no longer shows. It accepts only dollar-anchored forms, and treats
  a relabel as no move. It refused nothing on this pass. A first, un-anchored cut falsely refused
  FUBO on "1m/2m/3m" (months in a source_ref), which is why the forms are anchored.

**WHY.** These are wrong numbers in the record: two on cards the reader sees, the rest in the rows the
synthesis prompt reads (unit-less; no stored synthesis quotes one, checked by the guard on the real
pages). The SEC's forward-looking exception (Reg S-K 10(e)(1)(i)(B); C&DI 102.10(b)) is why outlook
ranges sit beside actuals at all: a range is never an actual. FactSet keeps a range as a range. XBRL
states scale as a power of ten the figure carries.

**HOW VERIFIED.**
- **Corpus, before any page was touched:** main's parser and this one on the 118 cited exhibits.
  - Reconciliation rows go 189 → 185; one-offs stay 16 and impacts 2.
  - 28 releases changed. Every removed and added row was read.
  - 65 refusals: 53 ranges, 10 sub-lines (pro forma 4, other 3, advertising 2, North America 1),
    1 'and'-coordinated, 1 quarter-against-a-year.
  - Header frames: unknown 43 → 34; 9 releases gain a correct frame (LLY ×5, NKE ×3, TGT ×1).
- **Two regressions surfaced by this run and fixed before landing:**
  - VRRM's second event-impact leg was lost when the match consumed the first leg's unit.
  - TGT's prior-year $1.30 would have become a new Q1 2026 row once the number token stopped eating
    sentence full stops.
- **Pages:** a dry run on copies of all 27, then the real pass, then a path-by-path diff against main.
  The only paths that moved were `primary_source.releases` (15), `drawdown_cause.filings` (4) and
  `layer_refreshes`.
- **Pins:** every defect is pinned on its verbatim sentence, and each red pin was run against main's
  parser as a control (VRRM excerpt: main → adj EPS 1.3 and adj EBITDA 40.0 from "$405 million to";
  V → 6.3 and 1.5; TGT → $2.44 as 2025; NKE → 2025).
  - The guard is pinned through `refresh_dossier` on a real page.
  - The transform is pinned offline: it removes VRRM's row, refuses on a changed exhibit count, and
    refuses a line that does not reproduce.
  - End-to-end on the committed pages, md and web.
  - Five existing pins froze the defect as the expectation (UBER 2.5; FUBO 1.482 / 1.484 / 1.549;
    CF's $2.89bn "a unit mismatch, not an LTM", which is $2,890M and IS its LTM). They now assert the
    correct values.
- **Mutation battery: 22 of 22 killed.** Every rule, every scale, each guard, the transform's two
  refusals, the renderer branch, and a correctly shaped high-unit mutant.
- **Suite:** full offline suite (`-m "not network"`), price store unlinked as in CI: **6,722 passed, 55 skipped, 2 failed** — V (`test_share_basis`) and MCK (`test_capital_panel_selection`), the CIQ data issues that fail identically on main (STATE row 32 (12)).

**BOUNDARY.**
- The 27 committed pages at main f49c380a, refreshed 2026-10-22.
- The 118 EX-99.1 texts they cite, from the shared SEC cache.
- The CIQ exports, from the shared copy, read only for the four line proofs.
- **"Moved"** means a page's JSON changed.
- **"Carry moved figures"** means a release figure was added, removed, or changed in value or
  period.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The allowlist refuses an unseen qualifier** (a gap, stated in `qa_flags`) rather than read it.
  The falsifier is a real total refused.
- **Guidance is not re-read** by the transform. GAAP-EPS guides (#762) and any later guidance
  changes land on a re-assembly.
- **Still open:**
  - 34 of 118 release headers resolve to no frame (row 28);
  - the multi-quarter LTM;
  - `test_primary_source_assembly_mvst_live`.
- **The refusals live in each release's `qa_flags`** (the JSON tier). The reader sees the corrected
  rows and the card, not the refusal list.
