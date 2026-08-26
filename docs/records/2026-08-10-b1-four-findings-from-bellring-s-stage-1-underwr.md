---
id: 
status: recorded
date: 2026-08-10
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**B1 — FOUR FINDINGS FROM BELLRING'S STAGE-1 UNDERWRITE (2026-08-10).** Recorded because
underwriting a name found things the fleet-wide guards did not; the first is a class we had not
seen.

**B1a — ~~DESIGN READ ONLY — NOTHING BUILT~~ BUILT AT #397 (2026-08-10, `_following_paragraph`)
AND ON EVERY COMMITTED PAGE SINCE THE #472/#473 FLEET PASS — this entry stood as an open design
for eight days after the build merged (stale-record class, corrected 2026-08-18; the operator
re-specified the build from memory before the code was checked).** What shipped is the PARAGRAPH
bound, and the reasoning the ledger never carried: at the 2026-08-10 measurement (191 rows, 27KB)
+1 sentence grew the payload 90% and crossed ONE call boundary (EPAM's Nelnet row spliced the Q4
2025 call's opening remarks onto a quote); +2 sentences 186%/two crossings; **paragraph 161%/ZERO
— structural, since a blank line precedes every `--- <call> ---` header, so a paragraph cannot
cross one** (the code also hard-stops at `_CALL_HEADER`). Unconditional within transcript rows —
no opener list, no classifier ("THE ONE RULE IS THAT THERE IS NO RULE", the docstring carries the
BRBR "This is" counterexample); KD/event rows are excluded STRUCTURALLY (the extractor is
transcript-only, so `following_context` cannot exist on a KD row). Surfaced in the synthesis
digest at ≤400 chars/row (synthesis.py:901). **MEASURED ON THE COMMITTED FLEET 2026-08-18: 236 of
316 transcript rows carry context; BRBR's 70%-promotion row carries the exact reversing qualifier
("This is relatively in line with historical norms…") ON THE PAGE — the demonstrated instance is
closed.** Worst-case digest payload AORT 9.0KB — no name crowds the prompt. Pins:
`tests/test_following_context.py` (reversing qualifier captured · benign continuation carried ·
never runs into the next call · headerless clamp · end-of-paragraph yields nothing · fail-soft ·
re-wrapped quote stops at its own paragraph). Original entry:**
THE SEVERED VERBATIM: a quote can be faithful, auditable, and still argue the opposite of
its source.** `operating_drivers.rows[23]` on BRBR quotes *"In
the third quarter, 70% of RTD shake category volumes were sold on price promotion."* The quote is
**exact**, the source_ref is **correct**, the digits **trace**. Every guard we have — quote-in-
transcript, digit-trace, 19c's citation requirement — takes the QUOTED TEXT as the check, and this
row passes all of them. The sentence the extraction did not take is the one that reverses it:
*"This is relatively in line with historical norms for this period after adjusting for the shift of
a major e-commerce promotion, while down sequentially from the heavier promoted second quarter."*
The synthesis then built a bear point — *"jumped to 27% in Q2 then to 70% in Q3 … escalating
structurally"* — on a sequence the source explicitly contradicts.

  * **STRUCTURAL, NOT AN INCIDENT: 13 of 191 transcript-sourced verbatims (7%) across 9 of 12
    names** end at a sentence boundary followed by a contrastive opener.
  * **THE EXTRACTOR IS CONSISTENT; THE SOURCE IS NOT.** 97% of verbatims are exactly ONE sentence
    (185/191). Row 12 (Q2, `"27% … up 8 percentage points versus last year"`) and row 23 are not
    the extractor selecting differently — it did the identical thing both times. Row 12's qualifier
    happened to sit INSIDE the sentence; row 23's sat after it. **So this cannot be fixed by making
    the selector more careful.**
  * **AND IT CANNOT BE DETECTED BY CONNECTIVE.** Split by opener: 5 rows follow with a REVERSING
    connective (*however / but / while*), 10 with a CONTINUING one (*this is / importantly / in
    addition*). **BRBR's reversal is in the CONTINUING bucket** — *"**This is** relatively in line
    with historical norms"* — sharing its opener with VRRM's *"**This is** a great indication that
    safety measures are working"* and VITL's *"**This is** in addition to several distribution
    wins."* Identical syntax, opposite function. **A connective regex classifies the one case that
    bit us as benign.** The signal is semantic, and a deterministic detector for "does the next
    sentence change the reading" therefore DOES NOT EXIST at this layer.
  * **SO THE REMEDY IS DISCLOSURE, NOT EXTRACTION** — the honest answer the brief asked for. An LLM
    selecting a span cannot be made to select the right span, because "right" is defined by whether
    the following text changes the reading, which is the text-criterion judgment this repo has
    twice refused to invent. What IS deterministic: **carry the following sentence unconditionally**
    whenever a verbatim ends at a sentence boundary with more text after it. Measured cost: **190
    of 191 rows qualify, median 120 chars, 24.4KB total, ~90% growth on the verbatim payload.**
    No classification, no judgment, and it puts *"in line with historical norms"* beside the 70%.
  * **NOT BUILT, AND BRBR IS NOT RE-ROLLED.** Its stage-1 underwrite was done against the current
    synthesis; a reroll would orphan that analysis against bear points that no longer exist — the
    citation problem refused for SMPL. When it does reroll, the revert rule applies: fabricated
    signal, or facts leaving the page.
  * *Process note: three searches of the transcript returned zero hits for "BellRing" itself,
    because the `.rtf` exports are **OLE2 compound documents**. "Never assert absence off one
    search" stopped a false report here.*

**B1b — NOT-DETECTED IS NOT AGREEMENT. Shipped.** The un-flagged `ebitda_basis` branch said
*"consistent, so both EBITDA rows read as the same basis"* — an affirmative claim from a function
that tests ONE proxy against ONE threshold. BRBR at **1.73×** is the counterexample: FY25 EBITDA
reads 376 against a REPORTED ADJUSTED **481.6**, and FY26E **288.1** matches management's ADJUSTED
guidance of 275–295. **The threshold was NOT moved** — lowering `FLAG_HIGH` because a case fell
under it is tuning to the instance (operator ruling). The sentence changed, and the **1.5–2.0×
band is now named on the page**; BRBR 1.73× and IT 1.82× are its only fleet members.
**INCIDENT → INVARIANT: shipped Y** — `test_the_unflagged_branch_never_claims_the_rows_share_a_basis`
plus a band pin and its negative half (SMPL 1.19× must NOT get the warning).

**B1c — SAME WINDOW IS NOT SAME BASIS, and no period check can see the difference. Shipped.**
`buyback_avg_price` derived $28.23 on BRBR from `PaymentsForRepurchaseOfCommonStock` ÷
`TreasuryStockSharesAcquired` over an **identical 272-day window** — every period guard passed. The
cash leg is a CASH-FLOW line: it includes $3.9M of prior-year excise tax settled in the window and
excludes $1.2M accrued but unpaid. The filer's own figure is **$27.41 on $134.5M**. **It cannot be
repaired by fixing one leg** — 134.5 ÷ 4.86 is $27.67, because the company's implied count is
4.907M against the tag's 4.86M; BOTH legs sit on a different basis, so no arithmetic over these two
tags reproduces it. **DERIVATION REFUSED OUTRIGHT** rather than given a tighter period test, since
the defect is invisible to period comparison by construction.

**AND THE REVIEW FOUND THE DERIVATION HAD BEEN HIDING A REAL FIGURE.** A "vintage beats directness"
rule dropped the filer's own average whenever it was OLDER than the repurchase cash and both legs
aligned — sound only while a derivation existed to replace it. **BRBR states
`TreasuryStockAcquiredAverageCostPerShare` = $29.18 over 181 days**, and that rule suppressed it in
favour of the unreproducible $28.23. With the derivation gone, suppressing threw the filer's figure
away and then reported `no TreasuryStockAcquiredAverageCostPerShare` — an affirmative claim of
absence about a filer that discloses one. **The same class as B1b one module over: not-detected is
not agreement there, SUPPRESSED IS NOT ABSENT here.** The rule is removed; a stale figure now
prints with its window and a PERIOD MISMATCH note.

**BRBR keeps 5 of 9 capital-allocation fields (including the $29.18 average), IT keeps 6 of 9**;
IT genuinely states no direct tag, so its refusal stands. *Note the $29.18 covers 181 days while
the presentation's $27.41 covers nine months — different windows, not a disagreement.*
**INCIDENT → INVARIANT: shipped Y** — `tests/test_buyback_average.py`, offline, 5 pins, 3 mutations
killed. *(2 of the 4 names carrying the field were affected; the other 2 used the direct tag.)*

**B1d — BRBR'S LEVERAGE RATIO HAS NO COVENANT TO BE TESTED AGAINST. Recorded, not built.** Three
numbers, three bases: the revolver covenant is **6.0× maximum total net leverage on the company's
ADJUSTED basis**, management reports **3.2×**, and the dossier shows **4.3× on GAAP/CIQ EBITDA**
(`net_debt_to_ebitda`, CIQ Net Debt $1,123M ÷ CIQ LTM EBITDA $263M). **Compliant at June 30.**
`credit_health` is `None`, so the artifact carries the one basis that does NOT test the covenant
and neither of the two that do — nothing is mislabelled, but the number on the page cannot answer
the question a covenant exists to answer. **And the 4.29× own-history low is not a clean floor**:
it occurred under the pre-2022 Up-C / Post-controlled arrangement, a different capital structure
(operator correction — it was offered as a floor in the underwrite brief and withdrawn).
