# Disposition — the 2026-07-28 SMPL defect report, item by item

**Rendered:** 2026-08-03, against `defect-report.md` itself — read end to end, not summarised from STATE.
**Method:** every disposition below is a MEASUREMENT against code and the committed artifacts. STATE was
read to find candidate homes; it was never accepted as evidence. Where the two disagree, the measurement
is recorded and STATE's entry is named as stale.

**Why it was rendered this way.** The operator's count of what was closed has been wrong four times, each
time because the answer came from tracking. Tracking is a claim about the repo; this document is a reading
of it.

---

## The four states

| state | meaning |
|---|---|
| **CODE** | the guard/fix exists and is wired, but a committed page still carries the defect |
| **ARTIFACT** | the pages are clean, but nothing in code stops it recurring |
| **BOTH** | fix shipped AND every committed page is clean (exceptions named) |
| **OPEN** | neither |

**Population for every artifact claim: the 11 committed dossiers** — AORT, BRBR, CNXC, EPAM, FUBO, IT,
MVST, NCNO, SMPL, VITL, VRRM. Nine were re-assembled 2026-07-30; **FUBO** was assembled 2026-07-27 and is
sealed by its own standing rule; **MVST** was assembled 2026-07-10 and has since been re-serialised, not
re-assembled. Those two are the recurring exceptions and are named individually rather than netted out.

---

## A. Platform defects

The audit describes nine. The 2026-07-28 recount found **thirteen distinct failures** inside them, and
that denominator is used here.

| # | part | state | evidence |
|---|---|---|---|
| **P1** | pt1 absent-from-data | **BOTH** (2 names qualified) | item 17 · `vinci/dossier/materiality.py`, wired `assemble.py:444` · `tests/test_materiality.py` |
| | pt2 prose cites wrong figure | **CODE** (SMPL open) | item 19c · `315bfe7` · `tests/test_material_figure_presence.py` |
| **P2** | wrong 8-K selected | **OPEN** | item 1(c), blocked on ingestion |
| **P3** | pt1 mislabelled frozen reference | **OPEN** | mechanism disproved; not closed by item 16's `role` |
| | pt2 bull leg violates its own rule | **OPEN** | item 29 · recorded UNCLOSEABLE BY CODE |
| **P4** | pt1 stale price | **OPEN** | item 1(b) · `spot_as_of` does not exist |
| | pt2 false "underwritten" stamp | **ARTIFACT** | render-only; no guard |
| **P5** | pt1 backward-fill | **BOTH** | item 20 · 3 consumers fixed |
| | pt2 basis mislabel | **BOTH** (FUBO open) | item 19a · PR #270 · `tests/test_pe_basis_cause_claim.py` |
| **P6** | wrong extractor branch | **BOTH** | item 21 · `tests/test_segment_absence_and_relationship_route.py` |
| | *(suppliers half)* | **OPEN** | no `suppliers` field in `schemas.py` |
| **P7** | pt1 inputs not printed | **BOTH** | item 28 |
| | pt2 wrong share basis | **BOTH** | item 24(a) · `afc4b08` + `04d5936` — **STATE says BLOCKED** |
| **P8** | consensus vintage drift | **not a defect** | item 23, closed 2026-07-28; real problem folded into item 1 |
| **P9** | sheet-shape absence reason | **BOTH** (FUBO, MVST open) | item 19b |

Plus the **information-regression trio** → items 18a + 18: **BOTH**, MVST the one stale exception.

### The three that move against the record

**P7 pt2 — shipped, but the queue still says blocked.** Queue item 24 (`STATE.md:7081`) reads *"BOTH POLICY
LINES RETRACTED BY THE OPERATOR 2026-07-28; DO NOT IMPLEMENT AS WRITTEN. Item stays BLOCKED pending
archetype work."* The (a) half shipped on 2026-07-31 — `afc4b08` swapped the per-share denominator from
weighted-average diluted to point-in-time diluted outstanding, and `04d5936` moved all seven records:

```
AORT   49.731 -> 50.200    EPAM  54.183 -> 52.634    IT   69.965 -> 67.121
MVST  385.272 -> 386.069   NCNO 109.458 -> 110.509   WERN 59.910 -> 59.950
SMPL   93.678 ->  88.461   (r:r 3.83 -> 4.48 period -> 4.78 basis)
```

It is recorded as closed at `STATE.md:5375`, **1,706 lines earlier in the same file than the queue entry
that calls it blocked.** The auditor's sizing was right in direction and roughly in magnitude — they put
the understatement at ~$1.00–1.50/sh; SMPL moved 3.83 → 4.78, of which the denominator swap is the smaller
half (4.48 → 4.78) and a mis-dated period fix the larger. Item 24(b), the regime test, is genuinely still
blocked — and (b) is audit N2.

**P1 pt2 — the guard shipped, and SMPL violates it.** `uncited_material_figures`
(`vinci/dossier/synthesis.py:1108`) is wired at `assemble.py:433` to **RAISE**, not flag. `STATE.md:6533`
still records 19c as OPEN; that is stale. But the artifact side is worse than stale — running the shipped
guard over all eleven committed dossiers through the real `Dossier` model:

```
SMPL: WOULD REFUSE -> Asset Writedown ($M) LTM = -391.9
CNXC: CLEAN     AORT: CLEAN     EPAM: CLEAN     IT:   CLEAN     NCNO: CLEAN
BRBR: CLEAN     VITL: CLEAN     VRRM: CLEAN     MVST: CLEAN     FUBO: CLEAN
```

**The one page that fails is the page the guard was written for.** SMPL's synthesis never states −391.9;
the only near-match in its prose is `$1,392M` of *revenue*, which `_figure_cited`'s negative lookbehind
correctly rejects — the exact false citation its docstring says it was tightened to prevent. `315bfe7` is
an ancestor of the artifact commit and the guard raises unconditionally on the assembly path, so **current
code cannot reproduce SMPL's committed page.** The refresh path is not the hole: `moved_cited_claims`
enforces a narrower and different contract (a material figure that MOVED and that the prose CITES), and
never claimed to cover 19c. Re-assembling SMPL is what closes this, and the guard will refuse until the
roll cites the figure.

**P4 pt2 — closed in artifacts with no guard behind it.** SMPL now reads
`**Spot** $10.53 (entry-vintage — frozen at underwrite 2026-07-27)`, labels every grid column
`vs entry-vintage spot`, states *"Prices quoted below are entry-vintage (2026-07-27); the live close is in
Snapshot, above"*, and prints the live close separately as `CMP $10.22 (2026-07-24)`. The false stamp is
gone. Nothing prevents its return. This is **19a's split running the other way**, and it is the second
instance of that shape in this set.

### The ones still fully open, with what the artifact shows today

**P2 — the guidance block still reads April, on a page re-assembled 2026-07-30.**
`mechanical.drawdown_cause.revised_guidance` carries the 2026-04-09 guide verbatim ("Net sales expected to
range between $1.31 and $1.35 billion… Gross margins expected to decline between 300 and 350 basis
points"). Bear point [3] argues from `$217–225M … gross margin down 300–350bps`, endnoted **[11] to
`0001702744-26-000010`** — the April 8-K. The July 8-K `-000021` appears only at endnote [36]. Unchanged
from the audit six days later and through a fresh assembly. *Nuance the report could not have known:*
CIQ-side date selection now exists (`_guidance_rows` returns a guidance-date row; `_guidance_reads` takes
the latest), but the surface carrying this defect is the EDGAR 8-K path, not the CIQ Guidance sheet — so
the fix that exists does not reach it.

**P3 pt1 — two LTM revenues on one page.** `dossier.md:424` prints `LTM revenue $1,416.208M` under source
`[50] committed dossier anchor block (#158/#160/#162-verified)`, while `dossier.md:67` prints the current
`ltm revenue 1,392.235 $M`. The report's *mechanism* was wrong (the anchor is current; the stale figure is
the entry-vintage reference row) and its *label* finding is right and live.

**P3 pt2 — the method sentence contradicts its own leg, visibly.** `bull | 1,420` (md:54) against *"bull
sits just under the trailing twelve months"* (md:419) against `ltm revenue 1,392.235` (md:67). Recorded
UNCLOSEABLE BY CODE: the leg is analyst data, so a guard can only surface it. Item 29 types the constraint
so the check becomes arithmetic.

**P4 pt1 — `spot_as_of` does not exist.** The only occurrence of the identifier anywhere in `vinci/` is a
comment at `render.py:2366–2368` saying it is queued as the real fix. SMPL's price is a 2026-07-22 Polygon
store close while its CIQ comps panel is as-of 2026-07-24 — disclosed now, not guarded.

**P6's suppliers half.** The routing half is fully closed: `biff_xls` appears in no committed dossier and
SMPL's `concentration.customers` carries parsed rows. But there is no `suppliers` field in
`vinci/dossier/schemas.py`, and SMPL's endnote [19] names `…Customers.xls` alone — the
Barclays/BMO/Goldman/SunTrust creditor group is still unread. *(The Barclays rows at md:505–506 are the
capital-structure covenant table, a different source — not the suppliers export.)*

### Two qualifications on artifact closure that a name-count would hide

**FUBO is the case that proves the code/artifact distinction, and it says so itself.** It is the only page
still carrying `rests on normalized/adjusted earnings` (19a) and one of two still carrying the sheet-shape
absence reason (19b). Its own `known_wrong.json` sidecar names both — `caveat-text-pre-fix` and
`agreement-bug` — and states the reason plainly: *"CNXC and SMPL carry the corrected form after
re-assembly — FUBO cannot re-assemble, so it still carries the old one."* It clears only on a
post-combination re-assembly.

**MVST's `material` key is a schema default, not a measurement.** All 11 of its financial-summary rows
carry the key with value `false`. That is not evidence the P1 guard evaluated MVST — the key arrived via
`04d5936`'s model round-trip, which added 79 schema-default fields to MVST's JSON (disclosed in that
commit). A probe that counts key-presence would score MVST closed on P1 pt1. It is unevidenced, not closed.

---

## B. Name-level defects — N1 to N7

**N1, N3, N4, N5 and N6 have no entry in STATE.md.** Not as queue items, not as halves, not as notes.
N2 appears exactly once, as a parenthetical inside queue item 24(b). N7 is queue item 22. Searched by
CONTENT as well as by label, because the label search alone gives false confidence — `N1` collides with an
unrelated concession-clause note at `STATE.md:1341`, and `CHRO` returns twelve substring hits
(*chronologically*, *Chrome*, *synchronous*) and zero real ones.

Transcribed below with content, so each is judgeable without reopening the report.

### N1 — Variant perception aimed at a consensus nobody holds · Critical · **OPEN, untriaged**

> The dossier's thesis is "overshoot over category decline." BellRing's FY2025 annual report describes
> category growth as robust and expects GLP-1 mainstreaming to *drive* penetration and category growth;
> SMPL's own CEO says the challenges are execution-driven rather than category-driven. The market is
> pricing **SMPL-specific share loss**, not category decline. Removes the stated edge; requires
> re-specification as a share-loss thesis.

Live. The committed thesis (md:19) still reads *"on the view that GLP-1 drugs permanently shrink the
snacking category. Our judgment is that the sell-off has overshot."*

**And the page already argues against itself.** Bear point [5], on the same document:
*"The category itself grew 10% while the company shrank, so the gap is a company-specific share loss
management concedes is execution-driven — an earned discount, not macro."* N1's evidence is already
extracted, cited, and rendered — sitting beneath a headline thesis that contradicts it. This is not a
missing-data problem; it is the synthesis and the thesis disagreeing in print.

### N2 — Exit multiple 12.5x is 43% above peer median NTM · Critical · **OPEN (queued, blocked)**

> 12.5x against a peer NTM median of 8.72x, unsupported outside the 2018–23 growth era. At today's 5.34x
> the base is $8.88; at peer parity $16.82; at 12.5x $25.71. Drives 100% of the excess upside.

Queue item **24(b)** — the regime test: *when is an own-history multiple band admissible after an
earnings-regime break — window it, down-weight it, or exclude it?* Blocked pending a ratified policy line.
EPAM's `DEAD REGIME` / `STRADDLES BREAK` exclusions are the in-house precedent, now expressible as
schema-1.3 `excluded` fields. Live: base multiple 12.5x (md:53), described as *"the 14th percentile, a
durable discount."*

### N3 — Base revenue equals consensus two years out · High · **OPEN, untriaged**

> Base revenue $1,330M equals consensus FY2028 ($1,331.0M) to 0.1%. Not a conservative mid-cycle figure —
> the street's two-years-out number, against a 180-day ledger horizon. Duration mismatch.

Live, and **now measurable in code for the first time.** A1's consensus extractor reports SMPL Revenue
FY2028 median **1,339.5** on 7 estimates from the 2026-07-30 export, against a base of **1,330** — 0.7%.
The audit measured 1,331.0 on the 07-24 vintage; the finding survives a vintage change. The conceptual
home already exists (the two-clocks note, `STATE.md:8627` — how long we hold vs how far out we value);
what was missing was the data to check it against, and A1 supplies that.

### N4 — Bear multiple exceeds the market's own · High · **OPEN, untriaged**

> Bear multiple 7.0x exceeds the 5.34x the market pays today, and sits below all 35 historical closes. The
> bear case embeds a 31% multiple re-rate while assuming operational deterioration. Understates risk; the
> $3.58 risk figure is soft.

Live. Bear multiple 7x (md:52). The record's method defends it against declining packaged-food
comparables (6.08x INGR to 8.57x LW) rather than against the current close — and the same page prints
`EV/EBITDA (TEV/LTM) 5.3x … 0%ile → near-floor` at md:115. The bear multiple and the number it exceeds sit
sixty lines apart, neither referencing the other.

### N5 — Surprise record inverted · High · **OPEN, untriaged**

> The dossier shows annual GAAP surprises ending FY2025 at −36%. The last three quarters beat normalized
> EPS by **+8.3%, +12.5%, +20.0%**, and Q3 beat revenue consensus by 7.3% and its own EBITDA guide by
> 14.5%. Biases the bear leg.

Live and unchanged. md:349 still prints the annual GAAP-EPS series alone — *"FY2025 −36%"* — sourced
`CIQ Estimates→Surprise (annual)`. No quarterly series, no normalized basis. **Cheapest of the five**: it
is a second read off a sheet already being opened, not a judgment call.

### N6 — Governance gaps · High · **OPEN, untriaged**

> (a) The 2026-04-21 cost-savings and leadership-change announcement — CHRO departing by 2026-06-01, CSCO
> separating — unreported. (b) Insider buying (90,000 sh, ~$1.1M) shown without the ~$12.36M of
> prior-year selling at ~$36–37, including 147,200 shares by the CEO. (c) Buybacks of ~$213M against
> $102.2M YTD operating cash flow (~2×) framed purely as a confidence signal, while net debt rose
> $257M → $324.6M and cash fell $194.1M → $123.9M over two quarters.

All three live. (b) md:531 `Open-market buys 2 · sells 0 (net +90.0K sh)`; (c) md:154 *"Management is
returning capital aggressively into the drawdown … and net insider open-market activity is a buy (+90.0K
sh)"* with no OCF comparison; (a) no leadership-change row anywhere on the page.

**(b) is a platform defect wearing a name-level label, and that is the reason to pull it out of this
section.** The insider window is fixed at **six months**. That window is what turns a net seller into a
net buyer: the ~$12.36M of selling falls outside it, the ~$1.1M of buying falls inside, and the page
reports the net as positive without stating the window is doing the work. This is not a fact about SMPL —
it will read the same way on every name whose insiders sold more than six months ago. It belongs beside
P1–P9, not here.

Queue item 39 (DOSSIER GOVERNANCE BLOCK, proxy-sourced — board, auditor, compensation, related-party) is
adjacent but is a different object and predates the audit; it does not cover any of (a), (b) or (c).

### N7 — Kill criteria thinner than the ledger's · Medium · **BOTH**

> The V-row carries three measurable triggers; the dossier carries one. Monitoring degraded relative to
> the decision of record.

Closed, and the audit was half-wrong in a way that made it cheaper: the record carried all three all
along; `render.py` rendered none of them — a render gap, not a re-spec. Item 22 shipped 2026-07-29 as
`### What would reopen this name`. SMPL md:21–25 renders all three. Probe: clean on all 11 committed
dossiers. It shipped with a structural pin asserting `render.py` still does not import the ledger, so the
isolation that stops the machine asserting verdicts cannot be threaded in by a later "small" fix.

---

## C. Never triaged at all

Items the document contains that never became halves and never entered the queue.

**1. N1, N3, N4, N5, N6** — five of the seven name-level findings, above.

**2. R3's actionable residue — a live instruction inside a retraction.** R3 retracts *"term loans rose
$148M QoQ"* (they were flat for three quarters: 396.7 → 396.9 → 397.0) and then ends with a fix that was
not retracted:

> The label "(249.1→397.0 QoQ)" is a period mismatch that makes a three-quarter-old financing event look
> current. **Correct the label**; the debt build is not new.

Live: SMPL md:377 still reads `term loans 397.0 (249.1→397.0 QoQ)`. **A finding inside a retraction reads
as retracted** — that is the mechanism by which this one was lost, and it is worth naming because §C
contains three retractions and nobody re-read them for surviving instructions.

**3. §D's methodological item — explicitly flagged as needing a decision, and never given one.**

> The base-margin derivation averages two different bases — the 15.51% median is GAAP-inclusive of
> unusuals, while the "~13.8% trailing" is CIQ clean EBIT. On the anchor basis LTM is **−17.05%**. The
> resulting 14% happens to be defensible, but the stated derivation does not hold together. Recommend
> standardising the adjustment policy across both ends of the anchor.

The report placed this under *Verified Correct — Do Not Change*, labelled "not yet classified as a defect
but worth a decision." Nothing classified it. Live: md:429 and md:57 still describe exactly that
derivation. Note what it is — a **mixed-basis derived value**, the class the brief contract already has a
rule for (*a derived pin value must name the source LAYER of every component*). The rule exists; it was
never pointed at this.

**4. §G Unresolved — four of seven untriaged.** Covered: credit-agreement covenant terms (item 18),
close-price conflict (P4 / item 1), brand-level profitability (19b — single reportable segment, now stated
as a filing fact). Untriaged: **FINRA short interest** (never independently re-verified); **Circana
category data** (the +10% figure is management-sourced, verified as reported and not independently — and
it is load-bearing for N1); **Q4 FY26 buyback quantum** (determines year-end net debt and share count, i.e.
two scenario inputs); **twin outcomes**.

The twin item needs restating rather than closing. The audit could not verify Central Garden & Pet or
e.l.f. Beauty — **neither name is in SMPL's twin set any more.** The current set is Medifast, Hain,
BellRing, Utz Brands and WW International: three the audit verified, two it never saw. Twins are
LLM-composed and re-draw on every assembly, so **twin verification cannot be a one-time task by
construction** — either the verified outcome travels with the twin as a field, or every re-assembly
silently re-opens it.

---

## D. What this render changes about the record

Three STATE entries are contradicted by measurement and should be corrected in place rather than argued
with later:

| STATE says | measurement |
|---|---|
| queue item 24 — "BLOCKED … DO NOT IMPLEMENT AS WRITTEN" (`STATE.md:7081`) | (a) shipped 2026-07-31 and is recorded closed at `STATE.md:5375`; only (b) is blocked |
| item 19c — "**OPEN**" (`STATE.md:6533`) | shipped `315bfe7`, wired to raise at `assemble.py:433`, pinned |
| — *(no entry)* | SMPL's committed dossier violates that shipped guard; current code cannot reproduce it |

And the standing shape this set keeps producing, now with instances running both ways: **19a is closed in
code and open on FUBO's page; P4 pt2 is closed on the page with no code behind it.** A single "closed"
column cannot express either, which is why the four states are the render rather than a formatting choice.

---

## E. Score — and this is the ONLY place it exists

**Do not copy these totals anywhere.** Not into STATE, not into a PR body, not into a handoff. The
previous score line was retired 2026-08-01 for drifting; a count restated away from the rows it
summarises will drift from them, and the drift is invisible because a total looks like a fact rather
than a derivation.

Every count below **names the items behind it**, so it can be checked against §A and §B in one pass.
That is what makes it a reading of this document rather than a second source — and it is exactly the
property a copy loses. Re-derive it here; never carry it out.

**This warning is written from a failure, not a principle.** The first cut of this PR's STATE record
was headed *"SCORE, DERIVED NOT RESTATED"* and then restated the whole score four lines later — a
fifth prose copy of the number whose four previous copies are the reason this render was commissioned.
Caught in review of #317 and removed. The wording above was not strong enough to stop its own author
in the same PR, which is why it now reads as a prohibition rather than an observation.

Of the **thirteen** platform failures: **six BOTH** (P1 pt1, P5 pt1, P5 pt2, P6 routing, P7 pt1, P7 pt2),
**one CODE-only** (P1 pt2), **one ARTIFACT-only** (P4 pt2), **four OPEN** (P2, P3 pt1, P3 pt2, P4 pt1),
**one not-a-defect** (P8). P6's suppliers half is a fourteenth failure the recount did not separate; it is
open. The information-regression trio is BOTH.

Of the **seven** name-level findings: **one BOTH** (N7), **one queued and blocked** (N2), **five untriaged
and open** (N1, N3, N4, N5, N6).

---

## F. The tail, dispositioned — 2026-08-03

§C above **identified** the tail; it never **dispositioned** it. This section does, item by item, measured
against current code and the SMPL page **as re-assembled 2026-08-03** (`#325`/`#326`) — so every line
number below is fresh, not carried over from §C.

**Three of the eight need a RULING, not a fix.** They are marked ⚖ and restated as questions in
STATE §Next-steps.

### §C — the three retractions, re-read for surviving instructions

| item | what survives the retraction | live? | disposition |
|---|---|---|---|
| **R1** | *"at entry one stress cell already failed (1.92:1); on the re-set 14% normal **both** now fail"* | rendered in full | **CLOSED** |
| **R2** | *"what remains is only the mixed-basis issue in setting the 14% normal"* | — | **NOT A SEPARATE ITEM** — see below |
| **R3** | *"**Correct the label**; the debt build is not new"* | `md:400` | **OPEN — fix, no ruling** |

**R1 — closed, and the page is better than the audit required.** `md:467–470` renders **both** boundary
cells (A `1.96:1`, B `1.73:1`), both bases, and states the consequence in words: *"on the re-set 14%
normal they read ≈1.96 / ≈1.73 — below the bar."* No instruction survived the retraction; the audit said
the dossier stated this accurately and it still does.

**R2 is not a fifth item — it is §D's item, cross-referenced.** Its residue sentence forwards explicitly
(*"the mixed-basis issue in setting the 14% normal (P10-adjacent, see below)"*), and **"P10" does not
exist** — the report has P1–P9, so the pointer resolves to §D's note and nowhere else. Anyone counting
§C's residue and §D's note as two open items **double-counts one finding.** Disposed as one, under §D.

**R3 — still live, and the mechanism is a frequency the sheet does not have.**
`md:400` reads `term loans 397.0 (249.1→397.0 QoQ)`. `vinci/dossier/ciq_sheets.py:747` opens
`Capital Structure Summary` with **`freq="annual"`**, then `:778–779` compares `vcols[-2]` → `vcols[-1]`
and hard-codes the string **`QoQ`**. Two adjacent *annual* columns, labelled quarter-over-quarter. That
reproduces the audit's numbers exactly: term loans were **396.7 (Nov-25) → 396.9 (Feb-26) → 397.0
(May-26)** — flat across the real quarters — while 249.1 is the FY2025 year-end value, so the printed
"QoQ" move spans roughly **three quarters and a fiscal-year boundary**.

**And the correct label is already computed and thrown away.** Ten lines above, `_cs_col_date(hdrs[-1][j])`
parses each column's date — solely to refuse when the columns are not in ascending order. The dates that
would name the two periods honestly are in hand at `:764` and discarded by `:779`. That is the
**called-result-discarded** rung, and it sits directly beneath a comment refusing to stamp
*"(latest quarter)"* on an unasserted convention — the function declines to assert a provenance it cannot
prove, then asserts a frequency it cannot prove, fifteen lines later.
*No ruling needed: name the two periods instead of asserting a frequency.*

### §D — the mixed-basis margin item ⚖ **RULING**

**What it says.** *"The base-margin derivation averages two different bases — the 15.51% median is
GAAP-inclusive of unusuals, while the '~13.8% trailing' is CIQ clean EBIT. On the anchor basis LTM is
−17.05%. The resulting 14% happens to be defensible, but the stated derivation does not hold together."*

**Live, and one degree worse than the report knew.** `md:57` and `md:446` still state the derivation. The
two ends are not merely different bases — **they are different KINDS of value**:

- **15.51%** is computed and sourced — endnote `[53]`: `EDGAR companyfacts OperatingIncomeLoss /
  RevenueFromContractWithCustomer… FY2019-FY2025, FY2025 ex the $60.9M impairment`. GAAP operating
  income with **only one named impairment removed**, i.e. inclusive of every other unusual item.
- **~13.8%** appears **once, in the METHOD prose, with no endnote and no field.** Three literal `13.8`
  occurrences in the whole JSON, none of them a value — no code computes it.

So the interpolation runs from a cited GAAP-basis computation to an **uncited, analyst-written CIQ-basis
figure**, and the word **"clean" means something different at each end.** The brief contract already has
the governing rule — *a derived pin value must name the source LAYER of every component; a pin reachable
only by MIXING layers is MALFORMED* — and it was never pointed here.

**Why this is a ruling and not a fix:** the anchor is analyst judgment, not a computed field, so no guard
can set it. The decision is which basis the anchor is defined on — GAAP-incl-unusuals at both ends, CIQ
clean EBIT at both ends, or the interpolation abandoned — and whether the un-sourced end must acquire a
`source_ref` before it can be load-bearing. Code can then enforce the choice; it cannot make it.

### §G — the four untriaged of seven

| item | what it says | live? | disposition |
|---|---|---|---|
| **FINRA short interest** | dossier figure primary-sourced, *"not independently re-verified"* | richer than at audit | **CLOSED — obsolete as written** |
| **Circana category data** | the +10% figure is management-sourced, *"verified as reported, not independently"* | `md:91/150/172` | ⚖ **OPEN — narrow ruling** |
| **Q4 FY26 buyback quantum** | unknown; *"determines year-end net debt and share count"* | `md:153` | **OPEN — not actionable** |
| **Twin outcomes** | Central Garden & Pet, e.l.f. Beauty unverified | **see below** | ⚖ **OPEN — structurally uncloseable as written** |

**FINRA short interest — closed, because it was never a repo defect.** It records that *the auditor* did
not re-verify a figure the report itself calls primary-sourced. Nothing to fix. The surface has since
grown past the audit's snapshot: `md:549` carries a four-point series with settle dates, direction, %
of shares out, and days-to-cover, endnoted `[67]` to FINRA consolidated short interest with the ADV
divisor stated. Re-verifying a primary source against itself is not work.

**Circana — the page has partly closed this on its own, and the residue is N1's.** All three renderings now
**attribute** rather than assert: *"Management frames the problem as execution-driven within a growing
category — purposeful nutrition grew 10% …"*. The figure is no longer stated as independent fact, which
was the audit's actual complaint. The ruling that remains is narrow and general: **may a
management-sourced, un-independently-verified figure carry a thesis leg?** It is load-bearing for N1 —
N1's entire argument is that the category grew while the company shrank — so the answer governs N1, not
this line.

**Q4 buyback quantum — open, and correctly so.** No code or judgment closes it; it resolves when SMPL
prints Q4 FY26 (October). Recording it as OPEN with an external unblock date is the whole disposition.

**Twin outcomes — and this one re-opened itself while the audit was being dispositioned.**
§C reasoned that the item was stale because *"neither name is in SMPL's twin set any more"*, and predicted
the mechanism: *"twins are LLM-composed and re-draw on every assembly, so twin verification cannot be a
one-time task by construction."* **The 2026-08-03 re-assembly confirmed the prediction the same day:**

```
BEFORE  Medifast · The Hain Celestial Group · BellRing Brands · Utz Brands       · WW International
AFTER   Medifast · BellRing Brands · The Hain Celestial Group · e.l.f. Beauty    · WW International
```

**`e.l.f. Beauty` — one of the exact two names the audit could not verify — is back**, carrying
`(LLM-claimed — verify)`; `Utz Brands` silently left. Nothing about SMPL changed; the set re-drew.

**And it fails in the other direction too.** The audit **independently verified Medifast's terminal
outcome** (Q1 2026 revenue −34.3%, coaches −44.9%, FY26 guide $270–300M). Six days later the page still
prints **`Medifast — went terminal (LLM-claimed — verify)`**. Human verification did not travel into the
artifact, so it will be re-requested on every assembly, forever.

**Why this is a ruling:** verifying the two named twins closes nothing, because the set is not stable and
the verification has nowhere to live. The decision is the mechanism — **does a verified outcome become a
field that travels with the twin (making the set partly sticky), or does the twin block stay disposable
and stop carrying outcome claims at all?** Either is coherent; the current state is neither, and it
launders an LLM claim and a human verification into the same rendered sentence.
