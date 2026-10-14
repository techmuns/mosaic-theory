---
id:
status: shipped
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — analytical safeguards after the PDF cost reduction: nothing material lost silently, nothing upgraded by omission

**WHAT.** The review of the cleaned Gridlock run ($11.70 vs $46.67) asked for safeguards before
another full-document run. All built and shown on the REAL saved answers at $0; no model call.

- **P0 · a malformed field costs that field** (`extract.salvage_fields`, `completeness.py`). An
  answer whose top level fails is validated FIELD BY FIELD, then item by item: a list that arrived
  as valid JSON text is decoded; a field that is not a list and not decodable is discarded WHOLE
  with the exact error and the ids its text names (reported, never used). A recovered part is
  merged and verified like any answer but NOT shown to later parts — so their requests stay
  exactly as paid and a replay costs $0. References to rejected claims cannot vouch (a figure
  stays `capture_not_verified`, a paragraph `account_names_no_record` — pinned end to end). The
  paid answer is never rewritten. **`reask-part --doc D-… --part N --max-cost X`** re-asks ONLY
  that part: the whole chain must first reproduce from the cache (else nothing is sent), the one
  call is bounded against the operator's `--max-cost` (no default), and the answer is kept beside
  the paid original (`<key>.reask-N.json`), used when the version is next analysed.
- **P0 · mechanism coverage** (`coverage.py`, new; on every analysed version, stored on its
  completeness report, alerts as `MECHANISM_COVERAGE` issues and in research verification). Every
  proposition a model pass proposed ends on a CARD, MERGED under one identity key (stated, with
  shared vs own evidence — distinct evidence is an alert), or DROPPED with why (incl. one a
  malformed field named). Every VERIFIED material fact (figure / forecast / event / metric) no
  thesis carries — nor an earlier version's card, nor a market risk — is grouped by page:
  excluded (a completeness verdict's reason), related (pass 1b named a hypothesis) or UNEXPLAINED;
  2+ unexplained facts on a page ALERT ("a mechanism no card holds?"), a lone fact is listed.
  Risks: each proposed risk's card(s), or dropped. Names: organisations a CITED paragraph names in
  a list of examples or as a dated source but nobody recorded — listed, never added. Nothing is
  forced into a card; nothing merges by similarity. Same-key merges now name both propositions.
- **P0 · missing timing never upgrades a thesis** (`timewindow.py`, `priority.py`, `engine.py`).
  The window reader learns "next five years", "next decade", "before 2030", "into the 2030s",
  "the end of the decade"; an OPINION naming a horizon beyond the next 4 quarters is long-dated
  evidence (never near-term). SKIP-3 also reads the thesis's other linked claims and the verified
  claims in the paragraphs its evidence sits in — for LONG-dated timing only, never near-term.
  No dated window anywhere → still WATCH (the methodology), now said: "timing UNKNOWN in the source
  evidence; a review should establish it".
- **P1 · re-read** (`engine._same_article_sibling`). A thesis a later version creates beside an
  earlier version's thesis that already held ≥ half its sentences is flagged
  `SAME_ARTICLE_SIBLING` (created, never merged); a re-read fact an earlier version's card carries
  is not an uncarried alert.
- **P1 · preflight** (`ingest.estimate_from`, `config.DOC_COST_*`). From the text the reader will
  SEND (after quarantine) and the ledger's parts; HIGH prices every call at its output cap and
  the densest characters-per-token measured, two extraction calls, $5 of card reviews. The $30
  default and every per-call bound are unchanged.
- **P1 · unread pages** (`documents.classify_unread`). Each quarantined page is classified from
  READABLE evidence only — back matter (no analysis after it, fine print: ≥2× the median readable
  page in smaller type, and after the last section the contents list names), possibly material,
  or unclassified. Only when EVERY unread page is back matter by the document's own contents list
  does the research-action gate read the analysis text as whole (F11 says why); the document
  stays PARTIAL and research verification still says "read only in part". A back-matter-only
  report is no longer "awaiting a complete document"; the visual-check line says what each page
  is and why.
- Engine stamp `ti-engine-4`; reader `ti-parse-6` unchanged — the cleaned Gridlock text's content sha
  (`6ea8321738bb3305`) is unchanged, so the demonstrated token saving stands. No prompt changed:
  every saved answer still replays at $0.

**WHY.** The paid acceptance run (record `2026-10-12-theme-intelligence-pdf-glyph-quarantine.md`)
lost a whole completeness part to one malformed field, carried Citi's low-cost US gas argument on
no card, merged fuel-cell economics into the gas-generation thesis on one key, read three SKIP-3
theses as WATCH because the cards dropped their long-dated sentences, and held a $11.70 report at
an estimated $31.40.

**HOW VERIFIED.** *Real, $0* — `docs/theme_intelligence/analytical-safeguards-2026-10-12/`:
1. The paid malformed answer (part 4 of 13): **14 claims, 4 mentions, 1 risk, 2 hypothesis
   additions, 25 figure + 25 paragraph reviews recovered**; lost only `added_hypotheses` (4,420
   characters, "Expecting property name enclosed in double quotes: line 1 column 938"), which
   named one proposition, hx4_1. The paid file is byte-unchanged.
2. Gridlock replayed from the paid run's own answers (fresh registry, cache only, no card review
   pass): **open items 27 + 27 → 6 + 5** (baseline 6 + 4); verified claims 246 → 247; mentions
   52 → 56; **held? no** — the default $30 limit, no `--max-cost`.
3. **The three SKIP→WATCH theses are SKIP-3 again on the source's own sentence**: midstream
   ("We forecast annual capex over the next five years to be >2x …"), skilled labour ("The
   shortage is unlikely to clear before 2030 …" — an opinion with a horizon, recovered from part
   4), nuclear ("… over the next decade"). Actions: paid run WATCH 6 / SKIP 8 → replay WATCH 3 /
   SKIP 11 (baseline WATCH 5 / SKIP 11); RESEARCH NOW 0 throughout. One WATCH now carries "timing
   UNKNOWN" (powered land).
4. **Coverage, 6 alerts**: the dropped regulatory-reform proposition (with the re-ask command);
   fuel cells merged into gas generation on one key with **0 shared / 17 own** supporting claims;
   pages 7 (6 facts), 14 (4), 16 (2) and **37 (4 — the low-cost US gas argument: Henry Hub $2–4,
   Asian LNG ~$8 / ~$20, $5–8 by decade-end)**. 16 propositions accounted for (14 card, 1 merged,
   1 dropped); 24 uncarried facts in 12 page groups (8 lone facts listed, not alerted); 11 risks
   each with its card(s); 9 unrecorded names incl. Renault, Volvo, Carwow, OLX, CBRE.
5. Re-read of the real PDF in a copy of the baseline (labelled harness, alignment hints off): 1
   article, 1 document, 2 versions; **0 duplicate rows, 0 independent confirmations**; 7 sibling
   theses flagged (e.g. the transformer story re-keyed: 60 of 67 sentences already on the earlier
   thesis); page 37 not alerted there — the earlier version's gas card still carries it.
6. Preflight vs measured (list price): Gridlock first read $28.54–$58.92 vs **$46.67** (held, as
   it should be); cleaned **$6.56–$20.77 vs $11.70** (was $5.60–$31.40, held); LatAm $6.60–$19.82
   vs $9.47; ETF $3.75–$14.10 vs $3.80 — every measured cost inside its range.
7. Gridlock pages 54–60: all back matter (13,229–56,781 characters a page at 9pt vs a median
   readable page of 2,430 at 10pt; after the contents list's last section, page 51); the
   synthetic mixed fixture's pages stay unclassified.
8. The `reask-part` command for the one remaining proposition — bounded at $0.98 — refused at
   `--max-cost 0.01` with nothing sent; with a STUB client (never the API) it sent exactly one
   request, part 4's, and reproduced the other 12 from the cache byte for byte.

*Offline fixtures* — the production re-read WITH alignment hints: the aligned story updates the
same thesis (its re-read sentences REPEATED), the one keyed anew is created and flagged, one shared
sentence among three is cross-citation (no flag), a fact an earlier card carries raises no alert.

*Tests*: `tests/test_theme_intelligence_safeguards.py` (33, new), +4 in
`test_theme_intelligence_long_articles.py` (2 rewritten: a malformed field no longer leaves the pass
"not run"), +3 in `test_theme_intelligence_glyph_quarantine.py`, the preflight calibration test
moved to the new model. **24 mutants, all killed** (one survived first — the place-name filter —
and was pinned). Full offline suite on the final tree: 4,919 passed, 511 skipped, 0 failed; ruff
and `mypy --strict` clean.

**CORRECTION of my earlier record.** "added gradually over four years from 2025 to 2028" was NOT
silently missed: the ledger reads counted periods in words, and pass 1b judged it immaterial with
a reason. Recorded as an amendment there and in `9-…txt` here.

**BOUNDARY.** Article `A-82a8a9210bae` (60 pages, as of 2026-10-11). Baseline `final-a` (answers
of `R-20261011T100624Z-ingest`); paid `glyph-paid` / `R-20261012T050655Z-ingest`; replay
`glyph-safeguards4` / `R-20261012T072027Z-ingest`, final code (no card review pass — verification holds from
that pass are absent, which affects RESEARCH NOW only, of which there is none); re-read
`glyph-reread6` / `R-20261012T071315Z-ingest`. Counts: span-verified claims; open = uncaptured
figures + unreviewed paragraphs; uncarried = verified material claims linked to no thesis (any
role), cited by no market risk, carried by no earlier version's card. **New API spend: $0.00.**

**WHAT IT COSTS / WHAT IS ACCEPTED / STILL OPEN.**
- *Not re-asked:* the regulatory-reform proposition (part 4) — `reask-part … --part 4 --max-cost
  1.20` would cost ≤ $0.98; not run without approval. Its evidence is recovered.
- *A re-asked answer applies at the next analysis of that version* (replay / rebuild / re-read),
  not in place — the registry is append-only.
- *Two baseline risks are on no card and NOT FLAGGED:* European "bragawatts" demand (p47) and
  raw-material inflation on storage returns (p33) — a risk stated inside an accounted-for
  paragraph is not tracked by any check.
- *The low-cost gas mechanism has no card* — it is now ALERTED, not restored; whether it deserves
  one is the reviewer's call (no card is forced).
- *Fuel cells stay merged* into gas generation by the identity rule (one key) — now ALERTED with
  0 of 17 supporting claims shared; splitting same-key hypotheses into separate theses is an
  identity-rule change left for a decision.
- *Coverage thresholds are face-validity* (2 facts a page alert; a sibling shares ≥ half its
  sentences): falsifiers — an alert page a reviewer finds to be context only, or a re-keyed story
  sharing under half its sentences.
- *Unread back matter relaxes the research gate* only with the document's own contents list.
  Falsifier: a report whose trailing fine print holds analysis — a visual check is still listed.
- *No control draw* — run-to-run variability still unmeasured (a second cleaned draw, ~$12).
