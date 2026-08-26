---
id: 
status: recorded
date: 2026-08-08
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**MEMO-GAP DISPOSITIONS — RECORDED 2026-08-08, from the seven items the IC memo raised.**

**M1 — DROPPED, NOT DEFERRED: TWIN RECOVERY DURATION IS NOT DERIVABLE, AND THE REASON IS
STRUCTURAL.** The committee's first question is the timeline — *when does a de-rating like this
reverse?* — and `twin_reference_cases` carries `name`, `outcome`, `distinguishing_fact`, `source`
and **no time field**. BellRing recovered; over how many quarters is nowhere.

**IT IS NOT ONE FIELD, AND THE RAW MATERIAL IS NOT THERE.** `own_history.series` holds 36 quarterly
closes **for the SUBJECT**, not for the twin. A twin's span needs the TWIN's price history, and the
twin is identified only by an **LLM-written company name** — no ticker, no CIK, no dates.

Measured across the committed fleet: **48 distinct twin names, 19 loosely matching a security in
the store** (a deliberately generous matcher, so the true figure is lower). The misses are
structural rather than a matcher problem:

  * **delisted or acquired** — Cardtronics, Endurance International Group, Chuy's Holdings;
  * **outside the mid-cap universe BY CONSTRUCTION** — Accenture, Cognizant, DoorDash, Chewy,
    Grab. A twin is *often* a larger company that already recovered;
  * **not a security at all** — `"Atkins Nutritionals (pre-2017 legacy brand)"` is a BRAND.

**THE CRITERION THAT MAKES A GOOD TWIN IS THE ONE THAT MAKES IT UNRESOLVABLE** (operator). A twin
earns its place by being a larger, already-recovered, often-acquired comparable — which is exactly
what puts it outside a mid-cap screen universe and outside a live price feed. Building it would
need three new capabilities: name→security resolution (the resolver takes tickers), per-twin price
history including delisted names, and a de-rating/recovery span detector.

**CLOSED. Do not re-propose without new evidence that the identifier problem has changed** — the
cost is not the blocker, the identifier is.

**M2 — DEFERRED WITH ITS COST STATED: INSTITUTIONAL OWNERSHIP NEEDS A PIPELINE, NOT AN EXTRACTOR.**

**THE QUESTION IS WELL-POSED, and that is recorded separately from the cost so the two are not
confused.** The thesis is that the sell-off overshot; the strongest form of that is a
**NON-FUNDAMENTAL SELLER** — an index deletion, a mandate breach, a forced exit. SMPL fell from
roughly $30 to $10, a path that crosses mandate thresholds, and **nothing in the artifact can say
whether anyone was forced out or whether a quality holder accumulated through it.** Three earlier
arguments against it were wrong: *"at $1M AUM it doesn't constrain"* answers a CAPACITY question
when the ask was about SIGNAL; a 45-day lag is not disqualifying against an 18-month horizon; and
insider data is DIFFERENT information, not a cheaper version — two insiders with $1.11M tells you
what two people did.

**CIQ DOES NOT CARRY IT.** The canonical export manifest (`vinci dossier requirements`) is the
authoritative set — four REQUIRED and four OPTIONAL exports — and **none is ownership or holders**.
No 13F capability exists in the repo either — searched for `13f` and `institutional owner` across
`vinci/`, nothing. And `render.py` already notes the gap in its own words, in the
content-relocation comment above the estimates-and-guidance section: *"the only actual OWNERSHIP
content in the dossier while the section NAMED for ownership carried none"*. **Cited by its TEXT,
not a line number** — the first draft of this entry said `render.py:599` and that line had already
moved by the time the entry was reviewed, **in the same session**. A durable record does not get to
use a positional reference.

  *Observed while fixing it: STATE carries **65** `file.py:NNN` citations. This one is simply the
  newest, and it rotted inside a single session — which is evidence about the other 64 rather than
  about this entry. Not rewritten here (65 edits is not a docs fix), and not closed with a machine
  check either: asserting a line still holds its content needs the content, which STATE does not
  record. **Recorded as accepted risk** — quote the text when writing a new one.*

**AND 13F-HR HAS NO PER-ISSUER INDEX.** Holdings are filed FILER-side, so finding one issuer's
holders means scanning every 13F-HR in a quarter — thousands — parsing the XML information tables
and matching CUSIP. That is a crawl-parse-aggregate pipeline with its own storage, **not an
extractor sitting beside the others**, and it is the largest of the seven memo items. It gates no
decision today.

**DEFERRED — unlock trigger: a second position exists, or an issuer-indexed holdings source
appears.** Recorded with the question intact so the next reader inherits the argument and not just
the price tag.

**M3 — CLOSED: THE PEER BLOCK MEASURED THE LOAD; THE WRITE-DOWN HISTORY NOW MEASURES THE REST.**
Recorded 2026-08-10 at operator instruction because the finding had been over-read — including by
me — and CLOSED the same day by #394. The gap statement below is kept INTACT rather than rewritten
in hindsight: it is the argument that produced the build, and the disposition at the foot of this
entry is what changed.

**WHAT #372/#375 SETTLED.** `peer_capital_intensity` (committed on SMPL) measures acquired assets
— goodwill + intangibles — against two denominators, for the subject and every comps-grid peer:

  * SMPL **73.2% of total assets**, against a **57.6%** median (`median_large_assets`) over the
    7 peers above the size floor;
  * SMPL **165.9% of market cap**, against **144.7%** (`median_large_market_cap` — which on this
    data happens to equal `median_all_market_cap`; name the field, the coincidence is not a rule).

Elevated, and inside the band the large packaged-food names already occupy — KHC 71.3%, UTZ 65.3%,
CPB 61.5%. **THE LOAD IS ORDINARY FOR THE SECTOR.** That is the whole of what the block establishes.

**THE FLOOR IS ON MARKET CAP, NOT ASSETS** — `large = [r for r in peers if (r.market_cap or 0.0)
>= floor]`, worth stating because three of the exclusions are counter-intuitive: JBSS (~$939M
market cap) and HAIN (~$49M) fall out **despite** HAIN carrying $1.16bn of assets, and **SMPL
itself, at ~$909M, is below its own floor** — the subject is measured against LARGER peers and is
correctly absent from its own median. FRPT is excluded on a different ground: `no-tag`, which the
row states as *"the filer reports neither goodwill nor intangibles (a real balance sheet, not a
data gap)"* — not a fetch failure, and the distinction is the one §2 below turns on.

**WHAT IT DOES NOT SETTLE, AND THE QUESTION WAS THE OTHER HALF.** `PeerCapitalRow` carries eight
fields — `ticker`, `is_subject`, `market_cap`, `acquired`, `total_assets`, `pct_assets`,
`pct_market_cap`, `note` — and **no impairment field**. The subject side does: SMPL's
`capital_allocation` holds `goodwill_impairment` **$38.0M** and `intangible_impairment`
**$331.0M**. So SMPL's write-down has **no peer denominator**, and the question the memo actually
asked — *what does this say about management* — is untouched.

**BOTH CHARGES ARE A 272-DAY FY2026 YTD FIGURE — `2025-08-31→2026-05-30`, identical on both legs**
(the `source_ref`s say so). Stated here because this entry's own §1 cost is exactly that an
unlabelled flow invites a false comparison, and a record that warns about it while citing a bare
`$331.0M` would be teaching the error. The two legs sharing one window is also what makes the
**$369.0M** sum legitimate rather than a layer mix — check that the next time, do not assume it.

**WHY THAT IS THE HALF THAT BEARS ON MANAGEMENT QUALITY.** An impairment is the one accounting
event where management marks its OWN past capital allocation. Against a peer set that carries ~60%
acquired assets and rarely writes down, a $369.0M charge is management marking early; against a
sector that impairs routinely, the same charge is late capitulation. **The number means opposite
things under the two, and the artifact cannot distinguish them.** Carrying more than peers and
writing down more than peers are different claims — do not let the first stand in for the second.

**THIS IS NOT AN M1-STYLE STRUCTURAL BLOCK — THE RAW MATERIAL IS ALREADY IN HAND.**
`GOODWILL_IMPAIRMENT` and `INTANGIBLE_IMPAIRMENT` exist in `capital_allocation.py`, and
`build_peer_capital_intensity` already holds each peer's FULL `companyfacts` (one cached call per
peer) at the point where it computes `acquired`. **The DATA cost is two more `_pick` calls per peer
on facts already in memory** — no new fetch, no new source. The BUILD is the usual shape around it
(two `PeerCapitalRow` fields, their medians, both twins, pins), so "two calls" is the input cost,
not the ticket size; do not quote it as the latter. The gap is SCOPE, not capability: the brief
asked for the intensity of the load and impairment was not in it.

**THE TWO REAL COSTS, so the next build does not discover them.** (1) **BASIS.** Impairment is a
FLOW; intensity is an INSTANT. `_pick(kind="flow")` takes the latest period_end and, at that end,
the LONGEST span — so it lands on DIFFERENT windows across peers with different fiscal calendars
(SMPL's own is a 272-day YTD, not an annual). That is the basis-mistranslation class this repo
keeps re-meeting. **Its most recent instance was in the #363 ANALYSIS, not in shipped code** — a
span was read off a fiscal-year label, the operator caught it before merge, and `_span` exists
precisely to prevent it; cited that way because "#363 was wrong" would misdescribe a PR that
shipped correct. A peer impairment column needs a DECLARED COMMON WINDOW, or it is not a
comparison. (2) **ABSENCE WILL BE COMMON, AND ITS FREQUENCY IS UNMEASURED.** Some peers will
report no charge in any given window — how many, and how often, **is the very base rate this
entry says we do not have**, so no figure is asserted here and none should be inferred. What
follows regardless: the column will carry real absences, and `filer-reports-none` vs
`we-could-not-fetch` must not render alike — #362 exactly. `build_peer_capital_intensity`
**already implements the three-absence discipline** (`unresolved` / `fetch-failed` / no-tag, each
its own sentence, all three verified present in code); extend that, do not re-invent it.

**CLOSED 2026-08-10 by #394** (`PeerImpairment`, four states, trailing-5FY window; artifacts on
11 of 12 names — FUBO refused, sealed by its own `known_wrong.json`).

**THE ANSWER, AND IT IS A NEGATIVE ONE.** Over the trailing five fiscal years, **3 of the 4 large
peers that could be ASSESSED took a charge, median 31.1% of acquired assets among those that
did** (KHC 31.1%, CAG 47.1%, MZTI 2.1%; JJSF `explicit-zero`). **Writing down acquired assets is
ORDINARY in packaged food.** So the inference the memo wanted is NOT AVAILABLE: SMPL having taken
a charge is evidence neither of unusual candour nor of unusual lateness, because a charge is what
this sector does. That removes a reading rather than supplying one — which is the useful outcome
here, since the reading was being made.

**WHAT IT STILL DOES NOT SETTLE — three limits, none of them cosmetic.**

  1. **n=4, and the three exclusions are not noise.** The assessed set is 4 of 7 large peers.
     CPB is `none-in-window` (four charges FY2013–FY2018, none since), BRBR and UTZ are
     `untagged`. A base rate on four names is thin, and CPB is the pointed case: over five years
     it contributes nothing, while its own history says this sector impairs in WAVES. A longer
     lens would give a different number.
  2. **SMPL'S LIVE CHARGE STILL HAS NO SAME-BASIS PEER DENOMINATOR — the residual that matters.**
     `$369.0M` is a **272-day year-to-date** point; every peer window figure is ANNUAL. SMPL's
     comparable figure is the **$60.9M / 4.0%** in the window column. **DO NOT divide 369.0 by
     1,508.9 and set the resulting 24.5% beside the 31.1% median** — that is precisely the basis
     mistranslation this entry was written about, and shipping the block has now put both numbers
     in ONE ROW where the error is one glance away. The page labels the column for this reason.
     It resolves on its own when SMPL's FY2026 closes and the charge lands in an annual period.
  3. **The five-year window is FACE-VALIDITY, never derived and never tuned.** It spans a full
     impairment cycle (KHC's run is FY2019–FY2025) while staying about current management. A
     ten-year window is a different question with a different answer; changing it to move a
     result would be outcome-tuning.

**INCIDENT → INVARIANT (from #394's review).**

  * *A window of only REVERSALS was described as "nil"* — `charged` filters on `> 0`, so a window
    of negative points reached `explicit-zero` and asserted "every one nil" about figures that are
    not (CMI states −$210.0M for FY2025; also HSY, PAR ×2, TTEC). → `test_a_window_of_only_
    reversals_is_never_described_as_nil`, with its negative half pinning that a genuine all-zero
    window still reads "every one nil". **Shipped Y.**
  * *A non-summable `pending` leg was dropped SILENTLY* — the two families' latest year-to-date
    points often end on different dates (13 live instances); only the latest end is summable, but
    this module STATES a period mismatch rather than dropping one quietly. → `test_a_pending_leg_
    on_a_different_window_is_named_not_silently_dropped`. **Shipped Y.** It caught a live instance
    on its first run: CPB was dropping a 181-day combined-tag charge.
  * *A code comment claimed the combined-tag guard had NO live instance* — it has one: **HLF**
    resolves its annual goodwill series to `GoodwillAndIntangibleAssetImpairment`, 11 annual
    points. The claim came from SMPL's eleven names rather than the corpus, and the test that said
    "SYNTHETIC and says so" repeated it. Both corrected. → **No machine check shipped**: whether a
    comment's factual claim is true is not machine-checkable. **Recorded as ACCEPTED RISK**, with
    the transferable rule — *a claim about "the corpus" is scoped to the corpus actually swept, and
    the sweep's breadth belongs in the sentence.* The 95-peer sweep is what found all three.
