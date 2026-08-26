---
id: 
status: recorded
date: 2026-08-10
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ROUND-2 RESEARCH RECORD (literature, read 2026-08-10/11. NOT measured on our data; the one thing
that was measured here says so explicitly).**
**Three corrections to round 1.** (a) **Long-only was under-weighted** — AVOIDs prove the
discriminator, only BUYs pay LPs, so the ROI question is a BUY-side question and time-to-payment is
the whole IRR. (b) **"Down a lot" is an anti-signal on its own**: George–Hwang's 52-week-high
anchoring finds far-below-high names keep underperforming, while nearness-to-low predicts nothing.
The screen carries no stabilisation element, so the raw pool tilts toward continued losers. (c)
**Do not buy while estimates are still falling** (Chan–Jegadeesh–Lakonishok revisions drift, slowest
to update on the worst performers). Revisions are already extracted, and display-only today.
**Confirmed from round 1.** The POOL is right (Brandes' falling-knives work: a losing majority with
a fat right tail still compounds, so selection is everything — which is precisely what this fund
claims to supply); megacaps remain the thinnest-coverage edge we can reach; tailwind-riding carries
documented crash risk at regime turns (Daniel–Moskowitz, momentum crashes); and classic technicals
fail data-snooping controls (Sullivan–Timmermann–White, Bajgrowicz–Scaillet). **That last finding
was independently reproduced ON OUR OWN DATA** by the price-states session in the same week — RSI
null, the 200d-MA filter degenerate — which makes it convergent evidence from two directions rather
than a citation we happen to like.
**Evidence-graded signal table, retained for the record** (now the price-states session's input):
buyback-after-crash ~30% abnormal / 3–4y (Peyer–Vermaelen) · insider clusters 4–8% / 6–12mo
(Lakonishok–Lee, Seyhun, Cohen–Malloy–Pomorski) · F-score +7.5%/yr (Piotroski) · revisions drift
(CJL 1996) · distress → anomalously LOW returns (Campbell–Hilscher–Szilagyi 2008) · short interest
(Rapach–Ringgenberg–Zhou) · 13D catalysts compress gaps to 3–18 months.

**AND ONE CORRECTION TO THIS SESSION'S OWN EARLIER REASONING, because it was repeated more than
once before it was checked against the code.** "The proof spread nets out tailwinds by
construction" is TRUE ONLY OF A MARKET-WIDE TAILWIND. `vinci/scoring/metrics.py` `aggregate`
computes `buy_mean − avoid_mean` on **raw** `name_return`, not on benchmark excess: a rise common to
both legs does subtract out, but a tailwind concentrated in the BUY leg — which is exactly what
deliberately picking a hot cohort produces — lands in the primary number looking like
discrimination. The beta it is carrying shows up only one line down, in `buy_excess_gross` and the
beta/alpha regression. **Consequence for ruling (3):** buying tailwind names to reach resolutions
faster would inflate the one number the fund exists to prove. Read the excess and beta lines beside
the spread before believing any cohort-timed improvement in it.

**HANDOFF TO THE PRICE-STATES / EVIDENCE-STRIP SESSION (PR #405 and its Phase B/C).** Their measured
result STRENGTHENS ruling (1) rather than competing with it: waiting for the 50d-MA reclaim is free
(+0.73 to +1.79 pts vs MDY at 30/60/120d — corrected before merge, see §3), **0 of 306 eventual
≥+50% winners were missed by waiting**, and the median winner had earned only 2% of its total gain before the reclaim. If there
is no rush to catch the knife, then a missing catalyst costs entry TIMING, not the trade — which is
the empirical half of the ruling this entry records.
**TWO SIGNALS THEIR PHASE B/C LIST DOES NOT CARRY** — offered for their consideration, deliberately
not built here, since the queue/dossier surface is theirs: (a) **a buyback ANNOUNCED AFTER the
crash** (Peyer–Vermaelen; strongest in precisely this pool, and 8-K parsing already exists), and
(b) **revision-breadth INFLECTION rather than level** (CJL drift; already extracted, display-only).
Both are filing/estimate-sourced, so both clear their own price-states ruling — that ruling bars a
PRICE state from moving a rank, and neither of these is one.

**NO MACHINE CHECK SHIPS WITH THIS ENTRY, deliberately, and the INVARIANT RULE is satisfied by
saying so rather than by inventing one.** A gate that was declined has nothing to enforce; the only
enforceable version — "warn when a base year sits beyond the horizon" — is the same gate in a softer
costume, and it would fire on every R1 record by construction (R1 is timeless; see the two-clocks
note). The pre-registered falsifier above is the control, and it reads off the ledger.

**OPERATOR CONTRACT CHANGE — `data/followed.json` ENTRIES ARE NOW DATED (PR #409, operator review
P1).** The quality sleeve's kill test compares its BUY leg against indexing the follow list, and the
first cut read the roster as "whatever is in the file today" and applied it to every historical
verdict. On an APPEND-ONLY ledger that is non-reproducible: adding a quality name next month
silently rewrites the comparator for a BUY recorded last month — over a window in which that name
was not followed at all — so the kill test's historical answer would depend on future roster edits.
Two rules follow, and they are the operator's to keep:
1. **Every follow entry states `followed_since`** (ISO date). It is REQUIRED — a name that cannot
   be placed in time cannot be placed in a basket, and "assume always followed" is the look-ahead
   itself. The three committed entries were backfilled from `git log -- data/followed.json`, not
   chosen: **UBER 2026-08-07** (`fdb95f4`), **V 2026-08-10** (`63dc405`), **NFLX 2026-08-10**
   (`b939ede`).
2. **Removing a name is a TOMBSTONE, never a delete** — set `followed_until` (EXCLUSIVE; the last
   day held is the day before it). A deleted entry takes its history with it and silently re-dates
   every past basket that contained it.
**CONSEQUENCE, STATED SO IT IS NOT MISREAD AS A BUG:** the quality book has no basket history yet.
The roster as of 2026-08-06 is EMPTY, so any quality verdict entered before 2026-08-07 refuses its
comparator with that reason rather than back-dating today's three names onto it. The kill test
starts producing numbers once quality verdicts are entered after the follow dates and their
horizons pass — which is the correct behaviour and the point of the fix.
