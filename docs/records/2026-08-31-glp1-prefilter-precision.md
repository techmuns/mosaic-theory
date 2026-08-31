---
id:
status: shipped
prs: [535]
date: 2026-08-31
supersedes:
superseded-by:
---

# GLP-1 prefilter precision — four generic English words carried 70% of the funnel, and two of them were terms of art

**WHAT.** `glp1-drug-value-chain`'s prefilter drops the four bare words `compounded`, `generic`,
`contract manufacturing`, `capacity expansion` and gains the phrases that carry their MEANING:
`compounding pharmacy`, `generic entry`, `generic competition`, `loss of exclusivity`.
24 terms → 24 (see the review round: the first draft added three more that could not contribute,
and one pre-existing term left with them).

**WHY — MEASURED, and the measurement changed the fix.** The first full sweep put 1,772 of 2,907
names through the expensive layer (61%). A per-term read of the cached EFTS responses:

| term | matches | unique |
|---|---|---|
| compounded | 993 | **578** |
| generic | 663 | 152 |
| contract manufacturing | 471 | 78 |
| capacity expansion | 308 | 144 |
| semaglutide / tirzepatide / incretin / amylin / dual agonist / GLP1 / peptide synthesis | 5–30 each | **0** |

The specific molecule vocabulary — the terms that make this filter MEAN this theme — contributes
zero unique names. Everything above ~30 names came from four words that are ordinary English.

**THE TRAP THIS AVOIDS.** Two of those words are simultaneously TERMS OF ART in the operator's
card: compounded semaglutide from compounding pharmacies IS the access-channel leg, and generic
entry after expiry IS the price-compression leg. Deleting them would have cut real thesis signal
along with the noise — the opposite error from the one being fixed. So each bare word is REPLACED
by a phrase that carries its meaning AND has no parent term already in the list: `compounding
pharmacy` (5 names), `generic entry` (27), `generic competition` (164), and `loss of exclusivity`
(167 — the most precise vocabulary pharma has for that leg).

**RESULT, with recall measured twice.**

| set | candidates | recall on the 11 pilot names |
|---|---|---|
| current (24 terms) | 1,772 (61%) | 11/11 |
| drop the 4 bare words | 475 (16%) | 11/11 |
| + phrase replacements | 511 (18%) | 11/11 |
| **+ loss of exclusivity (shipped)** | **531 (18%)** | **11/11** |

- RECALL, first read: all 11 names the bounded pilot proved driver-specific still clear the filter.
- RECALL, second and harder read — the population GIVEN UP was sampled through the real scan
  path, because 11/11 on names we already know is weak evidence about names we do not. Of the
  1,244 names the narrowed set drops, 20 sampled: **0 carried REAL exposure, and 18 of 20
  disclosed NO theme exposure at all** (1 committed-capacity, 1 aspirational). The sample reads
  as a catalogue of everything the theme is not — Adobe, Jacobs, Sonoco, Zebra, W.P. Carey,
  Plains All American, Rivian, Rocket Lab: what "compounded" as ordinary English was importing.
- The manufacturing leg the card names stays covered by SPECIFIC vocabulary (`CDMO`,
  `fill-finish`, `sterile injectable`, `peptide synthesis`, `peptide manufacturing`) rather than
  by a bare phrase that matched every manufacturer in the universe.
- ruff + `mypy --strict` clean; full offline suite green.

**REVIEW ROUND (2026-08-31, medium code-review — three findings applied).**
1. **Three of the seven added phrases could never contribute.** `compounded semaglutide`,
   `compounded GLP-1` and `peptide manufacturing` each CONTAIN a term still in the list
   (`semaglutide`, `GLP-1`, `peptide`), and EFTS matches the shorter token wherever the longer
   phrase appears — verified against the live universe, SUBSET=True for all three. They bought
   zero candidates and cost ~30 paced batch-queries apiece per scan. Removed; the candidate count
   is unchanged at 531 because they never added anything.
2. **The comment credited a phrase that contributes nothing.** It cited "compounded semaglutide"
   as what restores the access-channel leg; the phrase that actually reaches compounding-channel
   filers `semaglutide` alone would miss is `compounding pharmacy`. Corrected in the spec comment,
   this record and the PR body.
3. **An unrelated artifact was bundled** — the 1,266-row ai-value-migration scan-history archive
   rode along in a PR about glp1 vocabulary. Removed from this branch; the archive stays on disk
   for its own artifact commit.

**THE INVARIANT SHIPPED WITH IT** (`test_no_prefilter_term_is_contained_by_another_term_of_the_
same_driver`): no prefilter phrase may contain another term of the SAME driver at a word
boundary, checked across every driver, so this class cannot recur. Writing it found more than it
was aimed at:
- a PRE-EXISTING instance in this driver — `peptide synthesis` (5) covered by `peptide` (135) —
  removed here, since a list that fails its own new invariant is worse than the line saved;
- two more in OTHER live themes (`data center power` ⊂ `data center`; `protein shake` ⊂
  `protein`), allowlisted with their reason rather than silently edited: those are
  analyst-ratified vocabularies on themes with committed scans and frozen baskets, so changing
  them is an operator decision in its own change;
- and a BUG IN THE CHECK ITSELF. The first draft used plain substring containment, which flagged
  `snacking` ⊂ `snack` and `salty snacks` ⊂ `snack` as redundant. They are not: EFTS matches
  TOKENS, so "snack" does not match a filing saying only "snacking". The rule is word-boundary
  containment, and hyphenated pairs (`counter-drone`/`drone`) are deliberately left unflagged
  because EFTS's hyphen tokenisation was never measured.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The sweep drops from ~1,772 assessments (~2h10m) to ~531 (~40 min) — a 70% cut in the
  expensive layer, which is filings fetched plus one LLM call per candidate.
- RECALL RISK, stated: a filer whose only GLP-1 language is a bare "compounded" or "generic" is
  now missed. The 20-name sample is evidence, not proof, that this population is empty of real
  exposure; the next full sweep's REAL tier is the check that would falsify it.
- The sibling `glp1-demand-shift` (the consumption-side driver) is UNTOUCHED — its vocabulary
  was not measured here, and sweeping a term out of one driver never implies the other.
