---
id: 
status: shipped
date: 2026-08-19
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**⚠ THE COVENANT-POINTER UNION — BUILT, MEASURED FLEET-WIDE, AND REVERTED 2026-08-19. DO NOT
RE-RUN IT WITHOUT READING THE ROOT CAUSE.** Recorded because a reverted experiment is exactly what
someone re-attempts in three months, and everything below lived only in chat.

**THE DEFECT IT TARGETED.** `_covenant_pointers` queries efts WITHOUT `sort`, so hits arrive in
RELEVANCE order, and the first two exhibit-bearing ones were kept. Measured: EPAM's current $700M
facility 8-K (2025-10-06) ranks THIRD and was discarded — its digest cited the 2017 agreement as
amended 2021 against a panel reading Due 2030. AORT's top hits are 2014/2005/2016/2005, so no cap
short of exhausting the list reaches its 2025 replacements. **A pure date-sort is wrong in the
OTHER direction**: an amendment 8-K attaches an AMENDMENT, not the contract — SMPL's newest is
"AMENDMENT NO. 8 TO CREDIT AGREEMENT" and its 2019 pointer is "AMENDMENT NO 2", so date-sorting
swaps one amendment for another and drops the 2018 base where the covenants live.

**WHAT WAS BUILT:** top 2 by relevance ∪ top 2 by date, deduplicated, all existing filters intact
(CIK-scope, as-of bound, exhibit-bearing). Pre-measured on the three broken names: +5 pointers,
three of AORT's five families IDENTICAL under both orderings (free), and the exhibit filter — not
the cap — doing the discriminating (SMPL: six by-date candidates probed, ONE kept).

**WHAT IT FIXED — the three names all improved:** EPAM maturity **Oct 21 2026 → Oct 3 2030** (the
current facility); **SMPL July 7 2024 → Dec 16 2026** on the FUND'S OPEN POSITION; IT June 2021 →
March 2024; WERN/NCNO/FUBO/V gained proper base→amendment chains.

**WHAT IT BROKE — found ONLY by the fleet-wide diff.** Of 47 changed terms, **36 were union-caused
(the source filing moved) and 11 were LLM re-extraction churn** (same source, reworded) — the
attribution matters, because a re-assembly re-runs extraction and would otherwise take credit or
blame for both. The regressions:
  * **CNXC — all four terms jumped to a 2023 SELLERS' NOTE and a 2024 securitization.** Maturity
    "December 27 2026 (Revolving, Term A)" → "second anniversary of the Closing Date (Sellers'
    Note)"; interest "Term SOFR + 1.25–2.00%" → "2.0% (Sellers' Note Interest Rate)"; financial
    maintenance "Consolidated Leverage Ratio ≤ 3.75:1.0" → **"Default Ratio > 2.25%, Delinquency
    Ratio > 4.0%"** — a securitization trigger where a leverage covenant belongs.
  * **MVST maturity moved BACKWARD**, Dec 10 2026 → Nov 28 2025 — a past date, the defect the work
    set out to remove, newly created.
  * **UBER** lost a concrete March 3 2030 for "eighteen (18) months after the Closing Date".
  * **BRBR** interest went from a Eurodollar floor to "the lesser of 1.5% per month" — a
    late-payment clause from a different agreement.

**ROOT CAUSE, AND IT PRE-EXISTS THE UNION.** `governing_terms` collapses by **(family, term)**
where `family` is the **CIQ instrument description used as the efts QUERY PHRASE** — and
*"Credit Agreement"* collects a credit facility, a Sellers' Note AND a receivables securitization.
**So "latest PRESENT wins" picks the newest filing REGARDLESS OF WHICH CONTRACT IT BELONGS TO.**
The union did not introduce this; it gave it more filings to go wrong with. **The collapse assumes
one instrument per family, and that is false.**

**NOT SHIPPED PER-NAME, DELIBERATELY** (operator ruling): applying it only where it happens not to
regress is tuning to the corpus — the same shape as a pin narrowing its comparison until it passes.

**THE RESULT THAT SURVIVES THE REVERT:** SMPL's fix came from the **2021-12-22** amendment — not
the base relevance keeps, not Amendment No. 8 date reaches. **A filing outside the top two of
EITHER ordering. The union reaches further than its design predicted; it simply cannot tell which
contract it has reached.**

**THREE DESIGN OPTIONS, UNCOSTED — start here, not from the union.**
  1. **Separate families by AGREEMENT IDENTITY.** Obstacle: identity needed the document (we had
     to open `f8k032018ex10-1` to learn it was Amendment No. 2). **A rule that needs the document
     to decide which documents to trust is circular** unless the exhibit TITLE or a CIQ instrument
     attribute carries lineage more cheaply. Open question.
  2. **STOP COLLAPSING** — render each exhibit's terms under its own source. CNXC genuinely HAS
     three maturities and showing one is the error whichever is chosen. No classification needed;
     cost is page length, a restructured render, and digest tokens.
  3. **Keep one value, FLAG THE COMPETITION** — "Maturity: X — per an 8-K filed Y · two other
     agreements in this family state different terms." Does NOT fix the wrong pick (CNXC still
     shows the Sellers' Note) but makes the ambiguity VISIBLE, the principle that just paid on the
     source date. No classification, no render restructure.
  **BEFORE COSTING: establish whether the digest's consumers can take MULTIPLE values per term.**
  If something downstream expects one, (2) is ruled out and (3) is the cheap honest answer.

**THE COST OF THE REVERT, STATED:** SMPL keeps a July 2024 maturity and EPAM keeps October 2026,
both stale and both rendering — **but both now VISIBLY stale**, because the source-date line
(#482) shipped separately and is merged. That mitigation is why the revert was the right trade
against introducing four new wrong values.
