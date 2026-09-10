---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# WAT's GLP-1 base IS sizeable from the transcripts — and it is under 1% of the company

**WHAT.** The operator's question was whether WAT's GLP-1 base can be established, with the decision
rule *establishable → stays; not establishable → fails the prong BDX failed*. **The answer is a
third case: it IS establishable, and the number that comes out fails.** WAT's GLP-1 testing line is
**0.32%–0.79% of the FY2026 company being underwritten** — below the operator's own stated noise
line of 2%, on the operator's own framing that *"+40% on 2% of revenue is noise; on 20% it's the
thesis."*

Recommendation: **gate WAT out; the shortlist is WST and MCK.** The judgement is the operator's.

## The derivation, from the only two numbers the corpus carries

`Waters Corporation, Q2 2026 Earnings Call, Aug 04, 2026` — Puneet Souda (Leerink) asks *"how much
contribution you saw from GLP-1s in the quarter?"*, explicitly about **Waters core instrumentation**.
The CEO answers with the growth rate; **the CFO, Amol Chaubal, is the one who sizes it**:

> *"I mean, look, broadly, we have said the idiosyncratic growth drivers will all add up to about
> 200 basis points. And the GLP-1 contribution there was about 30 basis points. Clearly, GLP-1s are
> running well ahead of that."*

Beside it, the same call:

> *"GLP-1 testing part of the business grew over 40% this quarter."*

Those two numbers pin the base through the growth-accounting identity:

```
contribution_bps / 10000  =  base_share  x  growth_rate
        =>  base_share    =  (bps/10000) / growth_rate
```

**The identity yields a share of whatever base the bps is quoted against, so it survives the one
ambiguity in the quote** — whether the 200bps frames legacy Waters or the whole company. Only the
conversion to the underwritten entity needs that denominator resolved, and legacy Waters is the
reading most favourable to WAT.

| contribution | GLP-1 growth | share of its own base | $ base (legacy Waters) | **% of TOTAL company** |
|---|---|---|---|---|
| **30 bps** *(stated)* | **40%** | **0.75%** | **$26m** | **0.40%** |
| 30 bps | 50% | 0.60% | $20m | 0.32% |
| 45 bps | 40% | 1.12% | $38m | 0.59% |
| 60 bps *(2x stated)* | 40% | 1.50% | $51m | **0.79%** |

Denominators are the company's own Q2 guidance: legacy Waters organic **$3.370–3.431bn**, Biosciences
+ Diagnostic Solutions **~$3.045bn**, total **~$6.45bn** FY2026.

**Even at double the stated contribution and the lowest growth rate the quote allows, WAT is 0.79%.**

### The inversion is the cleaner statement

| for WAT to reach | GLP-1 would have to contribute | vs the 30 bps stated |
|---|---|---|
| 2% of revenue (the noise line) | ~152 bps | **5.1x** |
| 10% of revenue (WST's disclosed base) | ~758 bps | 25x |

The **entire** idiosyncratic bundle — GLP-1 *plus* PFAS *plus* India generics *plus* biologics —
is 200 bps. Clearing the noise line would take three-quarters of the whole bundle for GLP-1 alone.

## Why this is the BDX defect one stage later

BDX was gated for having **agreement counts and never a figure**. WAT has **a growth rate and never
a base** — which reads like a figure and is not one, because a rate without a denominator is not a
size. The prong is materiality; 40% answers a different question. **Caught a stage later precisely
because a percentage feels quantified.**

## The corpus audit, counted

**11 files in `manual/ciq/WAT`: 6 text-bearing read, 5 spreadsheets skipped.** Across all six —
two transcripts, Key Developments, Public Company Profile, Customers, Suppliers — there are **15
GLP-1 sentences, and exactly 2 carry a number**: the 40% growth rate and the 30 bps contribution.
Both are in the Q2 call; Key Developments' 3 mentions are prose and the other three files have none.
The Q1 2026 call names GLP-1 twice, both qualitative. There is no other sizing anywhere in the pull.

## THE COMPARISON FIGURE WAS WRONG: WST is 10% of sales, not 18%

Checking WAT against WST surfaced a defect in the number WST has been carried on since step 8.

**What the corpus says**, `West Pharmaceutical Services, Inc., Q1 2026 Earnings Call, Apr 23, 2026`:

> *"HVP components GLP-1 revenues grew significantly and contributed **10% of total company sales**,
> consistent with the previous quarter."*

That is the **only** GLP-1 size in WST's entire pull — 53 GLP-1 sentences across the two transcripts,
one with a number. `docs/records/2026-09-03-glp1-shortlist-step-8.md` records
**"GLP-1 is 18% of net sales (10% elastomer, 8% West Vantage)"**. The 10% half is sourced. **The 8%
half appears nowhere in the corpus** — no West Vantage GLP-1 split is disclosed on either call.

**And there IS an 18% in the corpus, attached to something else:**

> Q1 2026: *"Turning now to West Vantage, the new brand name Contract Manufacturing segment, **which
> represents 18% of our business**."*
> Q2 2026: *"Turning to West Vantage segment, **which represents 17% of Q2 revenues**."*

That is the segment's **total** share of revenue — GLP-1 and non-GLP-1 alike, and it moves 18 → 17
between quarters. A segment's share of the company was read as GLP-1's share of the company.
**Same error class as WAT's**: a share-of-something taken for a share-of-GLP-1.

**WST's verdict is unchanged** — 10% is 5x the noise line and 12–30x WAT — but the figure is wrong in
**6 records and STATE.md**, and it is the number the whole shortlist was ordered on. STATE.md is
corrected by this build; the merged record bodies are immutable and carry amendments.

## BDX is the seller, and nothing upstream flagged it

The businesses that moved WAT's denominator +31% are **BD Biosciences and BD Diagnostic Solutions** —
sold by **BDX, the fourth name on this shortlist**. Two of four names sat on opposite sides of the
same transaction through steps 8, 9 and 10, and no stage flagged it. Recorded as **accepted risk**:
the shortlist has no counterparty check, and building one on M&A data is not proportionate to a
four-name list. **Falsifier: a second shortlist where two names are transaction counterparties.**

## The multiple reference is pre-deal — a LIMITED-class mismatch

Recorded whether or not WAT is gated out. WAT's EV/NTM EBIT and P/NTM EPS distributions (n=38
settled quarters) describe **standalone Waters**. The post-deal entity has a different mix, margin
structure and leverage. Using that distribution as the reference for the post-deal company is a
basis mismatch of exactly the class `BASIS MATCH: LIMITED` exists to catch — the denominator changed
underneath the history. If WAT is ever underwritten, the reference needs restating, not just
caveating.

**BOUNDARY.** Source: operator's CIQ exports, `manual/ciq/`, read 2026-09-10 through
`vinci.dossier.ciq.read_text`. WAT population = 11 files, 6 text-bearing, 2 transcripts (Q1 2026
May 05, Q2 2026 Aug 04); WST = 11 files, 6 text-bearing, 2 transcripts (Q1 2026 Apr 23, Q2 2026
Jul 23). GLP-1 term set `GLP-1|GLP1|GLP 1`, case-insensitive, sentence-level. Revenue denominators
are FY2026 guidance as given on the Q2 2026 call, USD, reported basis. Growth rate is the Q2 2026
quarter; the 30 bps is a full-year plan figure, so the table brackets 30–60 bps rather than
asserting one. No raw CIQ committed.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The 30 bps and the 40% are **not the same period** — a plan
figure against a quarter's actual. Mixing them is why the result is a range and not a point. The
range is wide enough to absorb it: WAT reaches the 2% line only at ~152 bps, which is 5x the stated
plan and beyond the width of any period mismatch. **Falsifier: WAT discloses a GLP-1 revenue figure
or segment share above 2% of total revenue** — at which point the prong is met and the name returns.
