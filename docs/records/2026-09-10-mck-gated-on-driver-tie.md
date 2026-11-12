---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# MCK is gated on DRIVER-TIE, not materiality — and the shortlist is WST alone

**WHAT.** MCK's $15bn is real, sourced and correctly scoped. The prior build moved the burden off it
onto undisclosed fee economics. **That was too gentle, and it was the wrong gate.** The driver is
**treated-volume expansion**, and McKesson has stated — quantitatively, unprompted, and in both
directions — that **volume and price do not reach its profit**. That is not unquantified exposure.
It is **exposure disclosed as insensitive to the exact variable the thesis turns on**, which is a
pass on TIE, not a dig-deeper on MAGNITUDE.

**The shortlist is WST alone.** Underwriting a second name to avoid a one-name list is not a reason.

## The tie fails in the issuer's own words, and it is quantified

`McKesson Corporation, Q1 2027 Earnings Call, Aug 05, 2026` — the CFO, on IRA and WAC:

> *"WAC movements impact top line… recognized on the drug selling price…
> …operating profit are less sensitive… **more than 95%…fee-for-service…**."*

And on volume, from the prior call (`Q4 2026, May 07, 2026`), GLP-1 revenue **down** 4% sequentially:

> *"…GLP-1 volumes **had no impact on operating profit in the quarter**."*

Volume **up** 24% YoY (Q1 FY27): segment profit *"driven by growth in specialty distribution,
including health systems and strategic accounts…"* — GLP-1
not among the drivers named.

**Set against the card's own mechanism**, which is customer-side and whose signature is
*"volumes UP while manufacturer net pricing COMPRESSES"*:

| the thesis's signature | what reaches MCK's P&L |
|---|---|
| volumes UP | nothing — stated on a decline, omitted on a +24% rise |
| net price COMPRESSES | revenue falls (recognised on drug selling price); GP/OP *"less sensitive"*, >95% fee-for-service |

**Neither leg transmits.** A name can be exposed to a category and untied to its driver, and MCK is
the clean case: the layer tag that admitted it — `access-distribution`, its ONLY tag — is precisely
the layer where fees are earned for service rather than on value.

## CORRECTION: the WAC-reset compounding does not hold, and that makes the case stronger

STATE.md row 21 has carried *"distribution fees ride the base the Jan-2027 WAC reset halves"* since
2026-09-03. **The evidence contradicts it for ≥95% of the branded book.** Fee-for-service is a fee
per unit of service, not a share of price — and MCK has already run the experiment:

> *"this past quarter… **…WAC pricing decreases**. And despite this dynamic,… **GP growth, margin expansion…**."* *(WAC decreases of
> January 2026, named in the prepared remarks.)*

So the Jan-2027 reset halves a **revenue** line and is not evidence of an earnings headwind.
**MCK is insulated in both directions**, and the configuration is not *losing-side* — it is
**no-exposure**: a 95th-percentile multiple with a GLP-1 line that transmits neither the upside nor
the downside. You do not gate it because it is positioned to lose. You gate it because the driver
does not reach it.

*The revenue line still matters for one thing: it is the number MCK was shortlisted on, and it is
the number the reset halves. The materiality figure was the part exposed to the WAC cut.*

## Does the theme have a picks-and-shovels expression beyond WST?

The frozen basket (`data/themes/baskets/glp1-drug-value-chain.json`, freeze 2026-09-01) ratifies
**15**: A, AMGN, BDX, CAH, COR, GPCR, HIMS, LLY, MCK, NVO, OMDA, PFE, VKTX, WAT, WST.

| | names | why it is not an open candidate |
|---|---|---|
| shortlisted, **gated** | BDX, WAT, **MCK** | counts and never a figure; a rate and never a base; **driver-tie** |
| **survives** | **WST** | sized, sourced, volume-tied, margin-accretive |
| premium side by construction | LLY, NVO | the price curve everything else is priced off; the card names them as the FIRST-CONFIRMING instrument, not as positions |
| approval bets | GPCR, VKTX, OMDA | `next-gen-assets`; binary on data/approval, not on the value chain |
| distributors, MCK's economics | **CAH, COR** | same structure; the gate above applies before any pull is made |
| competing assets, not infrastructure | AMGN, PFE | `next-gen-assets` first; they are the category's supply, not its picks and shovels |
| demand-side access channel | HIMS | telehealth/compounding is the sibling driver `glp1-demand-shift`, not this one |
| **untested** | **A** | Agilent — the only remaining name whose primary tag is `manufacturing-infra` and that has not been tested |

**One name is open, not a round.** And its prior is poor: **Agilent is WAT's closest structural
comparator** — the same LC/MS analytical-instrument business, and a member of WST's own peer set in
the charting export — and WAT's GLP-1 line sizes at **0.32%–0.79%** of the company. **No Agilent
source is on disk** (`manual/ciq/` has no `A` folder), so this is a stated prior, not a measurement.

**Recommendation: do not run a second shortlist round on these 15.** A second round would draw its
evidence from the same `context.json` prose that produced four names of which three collapsed. If
the question is worth settling, it is settled by **one CIQ pull on A** against the WST test — sized,
scoped, volume-tied, margin-accretive — and by nothing else. **The layer tag is not evidence of a
sized exposure**: 13 of the 15 carry `manufacturing-infra`, and it admitted BDX and WAT.

## THE SESSION'S FINDING: three names broke on POPULATION, one on UNIT

Four names entered the shortlist. **Four broke, and all four on a `BOUNDARY` dimension:**

| name | figure carried | dimension |
|---|---|---|
| BDX | ~100 agreements, 80+ molecules | **population** — a count with no base |
| WAT | *"grew over 40% this quarter"* | **population** — a rate with no denominator |
| WST | *"18% of net sales"* | **population** — a segment's revenue share read as GLP-1's |
| MCK | *"$15bn quarterly"* | **unit** — correctly scoped revenue; the prong never said revenue or earnings |

Every shortlist number came from `context.json` prose and **none carried its scope**. The `BOUNDARY`
field — *window, filter, population, unit* — was added to `docs/records/TEMPLATE.md` on 2026-09-02
as a ten-minute afterthought to a state-integrity follow-up. **It turns out to be the control
governing the shortlist**, and it is a FIELD rather than a rule precisely because a rule you must
remember is weaker than a blank you must fill.

**The gap it does not close:** the field governs RECORDS. Step 8 — shortlisting — is a NO COMMAND
stage by design, so nothing made these four numbers pass through a record before they ordered a
shortlist. That is the design and it is not being changed here; what changes is that a name enters
a shortlist with a sized, scoped figure attached, or it is not a shortlist entry.

**BOUNDARY.** Source: operator's CIQ exports, `manual/ciq/`, read 2026-09-10 via
`vinci.dossier.ciq.read_text`. MCK quotes: Q1 FY2027 call (quarter ended 2026-06-30) and Q4 FY2026
call (quarter ended 2026-03-31); segment = North American Pharmaceutical. Basket population = the
15 `ratified` in `data/themes/baskets/glp1-drug-value-chain.json` at freeze 2026-09-01; layer tags
are that file's `layer_of`. Card mechanism quoted from `data/themes/thesis/glp1-drug-value-chain.json`
(declared 2026-08-31). No raw CIQ committed.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **A one-name shortlist concentrates the theme's entire test on
WST**, and a single name cannot separate a driver read from a name-specific one — the theme's
confirming evidence will not be distinguishable from West's execution. Accepted deliberately: the
alternative is underwriting a name whose driver-tie is disclosed as absent. **The triage of the
other 11 is a JUDGEMENT from layer tags and business type, not a per-name test** — CAH and COR in
particular are gated by analogy to MCK, and the analogy is strong (same layer, same fee structure)
but unverified against their own disclosures. **Falsifier for the MCK gate: McKesson disclosing a
GLP-1 gross or operating profit figure, or attributing segment profit growth to GLP-1 volume** —
either would restore the tie. **Falsifier for the one-name conclusion: A, CAH or COR disclosing a
sized, volume-tied GLP-1 economic** at the standard WST meets.

## Amendments

**2026-11-13 — REDACTION: 10 spans cut to “…”**, under the operator's ruling of 2026-11-12, verbatim
"Cut all 21 + guard (Recommended)", whose option read: "One $0 PR. Each run is cut to 12 words or
fewer. Each record gets a dated redaction amendment naming count, position and hash only, as #1036
did. A local-only test scans every tracked file against the transcripts on disk, and skips in CI
where they are absent."

CLAUDE.md's rule, since 2026-11-10: no public field quotes more than 12 consecutive transcript
words, and this repo is public. This record was written before the rule, and 5 of its quotations
shared more consecutive words with the call they cite. Each is cut in place to 12 words or fewer,
keeping the words that carry the figure or the claim this record relies on; nothing else in it
moved, and nothing was reworded. Each run is named below by its line in the record as merged, its
length and the words kept, the call it shares them with and where it starts in that call, and the
sha256 of its words: never by the words. A word is counted as the guard counts it
(`tests/test_tracked_files_hold_no_transcript_run.py`): split at whitespace, every dash form and a
slash, lower-cased, edge punctuation off, apostrophes folded. The hash is of those words joined by
single spaces, its first 16 hex digits. Git history keeps the old text, as the operator accepted; no
history is rewritten.

| line | words → kept | call | starts at word | run sha256 |
|---|---|---|---|---|
| 25 | 15 → 11 | `McKesson Corporation, Q1 2027 Earnings Call, Aug 05, 2026` | 6,631 | `e9b0ecb23886c232` |
| 26 | 38 → 11 | `McKesson Corporation, Q1 2027 Earnings Call, Aug 05, 2026` | 6,647 | `0e82ee0706e3af3b` |
| 32 | 16 → 12 | `McKesson Corporation, Q4 2026 Earnings Call, May 07, 2026` | 3,115 | `61edb1e3095e8145` |
| 34 | 19 → 12 | `McKesson Corporation, Q1 2027 Earnings Call, Aug 05, 2026` | 3,164 | `9331f16fed7f42a0` |
| 56 | 23 → 11 | `McKesson Corporation, Q1 2027 Earnings Call, Aug 05, 2026` | 6,709 | `c8918b624a4ada6d` |
