---
id: 2026-10-12-theme-intelligence-supervised-pilot
status: open
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the one supervised pilot: five web articles, four publishers, $3.95 spent; one access-label defect fixed, one lost-article defect open; not ready for unattended weekly use

**OPERATOR DECISION — recorded apart from licensing.** On 2026-10-12 the operator chose
*"Option 2 — explicit operator acceptance of the identified terms-of-use and contractual risks
for this one-time internal research pilot."* The operator acknowledged that the publishers'
terms may restrict automated collection, storage and third-party AI processing; that public
availability does not establish permission; and that the decision is **not** publisher
authorization and **not** a legal determination. The pilot is internal only.
**Publisher licensing is NOT confirmed for any of the four publishers.** What the terms say,
read before the run (summarised, not quoted):

| Publisher | Terms, as read 2026-10-12 | Licence for automated use / AI processing |
|---|---|---|
| J.P. Morgan Private Bank | no robots or automatic devices to monitor or copy without written permission | NOT confirmed |
| TrendForce | personal, non-commercial use; no crawlers or derivative works without written consent | NOT confirmed |
| Nomura (Nomura Connects) | no copying, transmitting or derivative works; no scraping; no building a database | NOT confirmed |
| SemiAnalysis (Substack) | no crawling, scraping, or storing significant portions | NOT confirmed |

Nothing behind authentication, a paywall, a robots rule or an access control was fetched. The
optional manual PDF stays **PENDING RIGHTS/INPUT**: the only candidate was an EOTM report, not
the `jpm_tmt` channel, and its rights were never confirmed. The rendered cards, dashboards and
article text stay in the git-ignored pilot registry (`data/theme_intelligence/v2/pilot-2026-10-12/`,
local only). This record carries no article text beyond titles, block ids and counts.

**WHAT.** Five articles, chosen before the run, went through the production path (`article
--url`: pass 1, completeness pass 1b, the card review, deterministic research actions,
nine-section cards) into a fresh registry, with a $6 run limit each:

| Article (publisher, date) | Run | Outcome | Theses | Actual cost |
|---|---|---|---|---|
| "What risks? Earnings are up and to the right" (J.P. Morgan, 2026-10-09) | `R-20261012T101426Z` + `R-20261012T103452Z` | **FAILED both times** — every answer wrote `hypotheses` as broken JSON text (defect 2) | 0 (its 1 thesis lost) | $0.7222 + $0.7643 |
| "HBM Supply Constraints Persist…" (TrendForce, 2026-09-29) | `R-20261012T101924Z` | PROCESSED · FULLY_VERIFIED | RN `TH-7C895A0A4E`, WATCH `TH-1516B6186B` | $0.4950 |
| "How AI Masks America's Rising Risk Premium" (Nomura, 2026-09-30) | `R-20261012T102120Z` | PROCESSED · INCOMPLETE (1 of 28 paragraphs open) | WATCH `TH-2FFD9B58A8` | $0.6305 |
| "Faster, Slower, Then Steady" (Nomura, 2026-09-29) | `R-20261012T102413Z` | PARTIAL — the page summarises a client-portal report, not fetched | 0 — correct (a Japan CPI outlook) | $0.3136 |
| "Beijing Will Not Pace the Frontier" (SemiAnalysis, 2026-10-08; the comparison case) | `R-20261012T102530Z` | PROCESSED, recorded FULL — **it was a paid post's free preview** (defect 1) | 0 (an earlier draw gave 1 WATCH) | $1.0238 |

Totals: 3 theses — **1 RESEARCH NOW / 2 WATCH / 0 SKIP**; **$3.9494 of the $18 automatic
allocation**, $0 of the $7 PDF allocation. Two `--cache-only` re-runs ($0) returned
ALREADY_INGESTED with no new records.

**Verdicts.**

| Dimension | Verdict | Why |
|---|---|---|
| Engineering quality | **REVIEW** | End to end on real articles; the spend guard, access discipline, QA, idempotence and the author guard all held. One material defect FIXED (1), one OPEN (2) that loses an article, and the cosmetic or card defects 3–4. |
| Research accuracy | **REVIEW** | 0 wrong values in 96 numeric values checked, and the theses are faithful to their sources. But the one RN meets two gate conditions on weak grounds (5); two risk lines carry overstated labels, which the review flagged and the card does not show (4); and one comparison thesis appears in one draw and not the other (6). |
| Coverage | **REVIEW** | 4 of 5 articles processed. Verification: 1 FULLY_VERIFIED, 3 INCOMPLETE, all stated. The preview read as full is now detected for future fetches. |
| Source permissions | **FAIL (not confirmed)** | The operator accepted the risk for this one pilot. That is not a licence, and none of the four publishers' terms permits automated collection or AI processing on the reading above. |
| Costs | **PASS** | $3.9494 of $18. 0 of 19 paid calls above their pre-send bound; 0 refusals. Every processed article cost less than its preflight low estimate. |
| Operational readiness (unattended weekly use) | **FAIL** | Blocked on source rights whatever the engineering. 1 of 5 articles was lost to defect 2. 2 of 7 channels are healthy. |

**DEFECTS.**
1. **FIXED — a long free preview was read as the full article.** `parse.py` looked for the
   subscriber marker in only the first 20,000 characters of the page. The SemiAnalysis post's
   marker sits at character 29,821 of 30,129, in a `div.paywall` outside the parsed blocks, so the
   preview was recorded FULL. The article promises an investor section and then stops at a
   heading (b048 → b049). The pilot's zero-thesis outcome therefore partly reflects text it
   never had. The fix searches the whole page.
   - The live record is NOT corrected: an already-ingested version is not re-parsed (`--cache-only`
     re-run → ALREADY_INGESTED). That limitation is defect 7.
   - Every earlier registry holding this article (one cached extraction) carries the same FULL label.
2. **OPEN, material — pass 1 writes `hypotheses` as text, and the article is lost.**
   - Four of four answers for the JPM article (two runs, each with the one re-ask) gave the
     field as broken JSON text: a property name dropped, or an object closed early. The same
     shape was seen on 2026-10-10.
   - The answers' other content was right: the latest answer's 27 numeric claims all match the
     article, and its one hypothesis — earnings broadening beyond the mega-caps — is the
     article's thesis.
   - **Tried and falsified:** a re-ask naming the refusal (the second run, `R-20261012T103452Z`, used
     that local change). The named re-ask failed the same way. The change was reverted and is
     not in the branch. Its cost, $0.7643, bought that falsification.
   - **Decision needed.** Each option is a design change, not a fix:
     - (a) Salvage pass 1 field by field, as completeness parts already are. The article would
       proceed with its 25–30 claims and with the thesis left for pass 1b. A $0 check on the four
       refused answers: each loses exactly its one hypothesis.
     - (b) Schema-constrained ("strict") tool use. This changes every cache key.
     - (c) Accept that an article is occasionally lost, and report it.
3. **OPEN, cosmetic — web articles print "page None".** Six format sites assume a PDF page
   number: `pipeline.py:562`, `:616` (persisted into a stored risk's scope text), `report.py:232`,
   `:238`, `schemas.py:996`, `:1002`. On the pilot: 2 lines on `TH-2FFD9B58A8` and 3 in the review
   queue.
4. **OPEN, card quality — reviewer warnings never reach the card.**
   - The card review flagged 7 sentences REVIEW_PARTIAL: 2 risk lines labelled MEASURED
     OBSERVATION whose content is conditional, and 5 specifics absent from the cited span.
   - Only BLOCK findings are withheld (`engine.py:1397–1418`). The 7 print unmarked, so the reader
     sees "MEASURED OBSERVATION" on a statement the review already questioned.
5. **OPEN, research — the one RN meets two of its gate conditions on weak grounds.**
   - Both TrendForce theses take their only "source-named exposure" from block b003, the page's
     category tag "Semiconductors". The RN reads it as positive, the WATCH as negative. The
     parties the article actually names (GPU and ASIC vendors) are not used.
   - The RN's own horizon is longer-term, and its card says the figures are for full-year 2027.
     Yet its gate counts the 2027 window as near-term, because the window overlaps the next
     four quarters.
   - The RN is defensible on substance — a large dated price forecast for a listed-supplier
     market — but its audit trail is weak.
6. **OPEN, research — the comparison case is unstable across draws.**
   - Same article, same prompt version: the earlier draw (one cached extraction shared by 12
     registries) proposed 1 thesis, graded WATCH; the pilot's draw proposed 0.
   - An independent read finds 0 narrowly the better answer. The earlier title joins two
     fragments into a causal claim the article does not make.
   - The read also finds the call borderline, and the article was a preview (defect 1). One
     pair of draws measures nothing more.
7. **OPEN — a stored retrieval label is not re-derived when the parser improves** (see 1).
8. **OPEN, operations — no combined weekly page for a pilot run article by article.** Each
   `article` run renders its own dashboard. `report --week` renders the week's LATEST run, here a
   $0 duplicate check that analysed nothing. All three cards are in that run's archive table,
   but one combined page needs a `scan`.

**Also checked:**
- **Nine sections:** all 9 rendered card files have all nine sections (3 theses × md, html and print).
- **Cross-source links:** 0 between articles, as expected for four different topics.
- **One SIBLING link (correct):** TrendForce's two theses — one article, different economics (memory pricing vs accelerator cost).
- **Independent confirmations:** 0.
- **Duplicate evidence within an article:**
  - Nomura states its ~80% concentration figure twice, and the card shows it as two evidence rows.
  - One TrendForce claim supports and qualifies both theses. The engine flagged it CLAIM_BOTH_SIDES (2 issues) and removed it from the WATCH's counter-evidence.
- **Author guard:** refused 2 author attributions the model invented for SemiAnalysis sentences (AUTHOR_SPAN_NOT_FOUND).
- **Access discipline held throughout:**
  - Morgan Stanley fails closed on an unreachable robots.txt.
  - Goldman Sachs's 403 is never bypassed.
  - The Nomura client-portal report is flagged for upload, not fetched.

**WHY.** The operator asked for one supervised pilot before any decision on weekly use, judged
on accuracy, completeness, citations, identities, risks, classification, duplicates, card
quality and cost, with fixes only for a reproducible material defect. Defect 1 qualified: it
misstates what was read, and was fixed with a corpus check. Defect 2 qualified, but its one
minimal fix was falsified on the real case, so it goes to the operator rather than into an
unasked design change.

**HOW VERIFIED.**
- **Defect 1:**
  - A $0 corpus check over every cached HTML page in the local registries. Under the old window, 2 FULL pages carry the marker — both SemiAnalysis paid posts (this one, and "A Brain Too Big to Carry On-Device", marker at character 45,959 of 46,272).
  - After the fix, those 2 read PARTIAL with the paywall note, and no other page changed (37 FULL / 20 PARTIAL / 3 BLOCKED, from 39 / 18 / 3).
  - The regression test copies the live DOM shape (`div.available-content` plus a sibling `div.paywall`, more than 20,000 characters of distinct hypothetical paragraphs). A pin requiring the text to pass the old window caught a fixture the parser de-duplicated below it.
  - Mutants: 3 of 3 killed — the old window restored, the page text not searched, and an `or` turned into `and`.
- **Defect 2:**
  - The four refused answers are kept as `.invalid-1/2.json` under two cache keys. The key changed between runs because the registry context in the request had changed.
  - The falsified fix's 5 of 5 mutants were killed before the paid run; the paid run then failed. The diff is not in the branch.
- **Accuracy:** every numeric value checked against the parsed article block in the pilot registry's HTTP cache. SemiAnalysis was checked by an independent read; its truncation finding was confirmed here before entry.
- **Gate:**
  - ruff and `mypy --strict vinci`: clean (184 files).
  - `pytest -m "not network"`: see the PR.
  - `qa --run` on every pilot run:
    - processed runs 19 or 20 of 20 — the misses are stated open items (Nomura b034; SemiAnalysis figures '32' and '102');
    - both failed runs 19 of 20 — no cards to compare.

**BOUNDARY.**
- **Spend:** `runs.payload.spend` of the pilot registry, 2026-10-12, 6 paid runs, 19 paid calls, list price.
- **"96 numeric values, 0 wrong":**

  | Article | Population checked |
  |---|---|
  | TrendForce | 2 of 2 card figures |
  | Nomura risk premium | 6 of 6 numeric evidence rows on `TH-2FFD9B58A8` |
  | Nomura Japan | 9 numeric claims of its 18 pass-1 claims |
  | SemiAnalysis | 52 numeric of 70 claims, pass 1 + 1b |
  | J.P. Morgan | 27 numeric of 30 claims in the latest refused answer |

  The unit is a stated value with its unit and period, compared with its cited block. Checked 2026-10-12 at `c1521a27`.
- **Corpus check:** distinct page URLs under `data/theme_intelligence/`, the newest cached copy each, HTML only, fetched FULL or PARTIAL — 60 pages.
- **"12 registries":** local registries holding the SemiAnalysis article's extraction under one cache key (`X-87309168789d`) — 1 model draw.
- **Channel health:** `sources --check-health`, 2026-10-12 10:11–10:14 UTC.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $3.9494 of API spend, of which $1.4865 bought no analysis: the JPM article.
- The operator accepted the publishers' terms risk for this one internal pilot only. **Falsifier
  for the readiness verdict:** written permission from each publisher whose research the weekly
  run would collect, or a licensed feed, recorded beside this record.
- Without that, the weekly schedule stays off whatever the engineering verdict.
