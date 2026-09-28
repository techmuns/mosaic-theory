---
id: 2026-09-28-an-empty-ciq-view-is-a-fact
status: shipped
date: 2026-09-28
prs: [651]
supersedes:
superseded-by:
---

# An empty CIQ view is an answer, and a 600K cap was guarding a 1M-token window

**WHAT.** A guard, a note and a cap were wrong — each because it encoded an assumption nobody
had measured.

1. `read_text` refused any RTF over 4KB that yielded fewer than 50 words, raising a message that
   named a cause it had never checked for: "this is an OLE-disguised Word doc, not real RTF".
   BURL's customers export is real RTF, parses perfectly, and says *"There are no recently
   disclosed customers listed"*. It is 70,162 bytes on disk and 278 characters of text — which is
   exactly the shape the guard was built to reject.
2. Past that guard, the table parser found no rows and the reader was told "could not parse the
   Business-Relationships table" — a second false account of the same empty. The status is
   honestly UNKNOWN either way; what was wrong both times was the *reason*, and a reason is what
   a human acts on.
3. `_MAX_EXHIBIT_CHARS` was 600,000, commented "≈ 150K tokens, fits model's window". The
   configured model's window is 1M **tokens**. BURL had four credit-agreement exhibits refused
   for being too large.

**WHY.** A guard that states a cause it did not test is worse than one that says nothing: it
spends the reader's trust. The customers line for BURL said the engine could not read the file.
The file was fine. The right answer — *CIQ discloses no counterparties for this name* — is a fact
about the business, and it was being rendered as a defect in the tooling.

The exhibit cap is the same error with the opposite sign: a number chosen against an imagined
constraint, then never revisited when the constraint moved by nearly an order of magnitude.

The fix keeps the status UNKNOWN. No rows means no value, and an UNKNOWN that acquired a value
here would be the fabrication the house rule forbids. Only the note changed, from a claim about
this code to what the source actually says — and it now carries a `source_ref` naming the file,
because an asserted absence is still a claim and the reader must be able to open it and check.

**HOW VERIFIED.**

*The real run, first.* `customers()` over every name with a CIQ folder, at the branch head:
25 PRESENT, BURL reporting CIQ's own emptiness, **0 unexplained UNKNOWNs**. BURL's fact is now
`status=unknown, value=None, source_ref="CIQ Customers&Suppliers Burlington Stores Inc NYSE BURL
Customers.rtf"`, note *"CIQ discloses no customers for BURL — the export is empty by CIQ's own
statement, not unparsed"*. Its sibling Suppliers export parses **33 rows** from the same bundle,
which is what makes the empty customers view a fact about the company and not about the reader.

*The deeper extraction.* BURL's 744,759-char exhibit, sent in full through this module's own
`_extract_from_exhibit`, returned six of seven target terms verbatim: maturity **July 25, 2030**
(from December 22, 2026), **$1.0bn** commitments, **Term SOFR + 1.125%/1.375%**, a **springing**
fixed-charge covenant of **1.00:1.00** tested only during a Covenant Compliance Event, and ABL
collateral. Under the old cap all seven read UNKNOWN.

*Mutation — six, all caught, re-run against the FINAL code after the `customers()` branch landed
(the first four had been measured before it existed).* M1 sentinel removed → three pins redden,
including the corpus one on the real BURL bundle. M2 sentinel
widened → the ordinary-sentence pin reddens. M3 cap back to 600K and M4 cap to 9M → the
measured-cap pin reddens at both ends. M5 the `is_empty_view` condition dropped, so every no-rows
case claims CIQ said none, and M6 the branch reordered to fire before the row check → both caught
by `test_a_view_that_fails_to_parse_still_says_so`, the negative pin whose whole job is to stop the
honest note becoming a blanket one. Source restored byte-identical afterwards, `__pycache__`
cleared between mutants.

*Layer.* The reader-level pin was necessary but NOT sufficient, and finding that out is most of
this record. `read_text` returning the text still left the table parser finding no rows and the
page saying "could not parse" — a pin on `read_text` alone would have gone green over the symptom
the operator actually sees. The pins therefore sit on `customers()`, the function that writes the
note, with a corpus pin on the real BURL bundle beside the built fixture.

**BOUNDARY.** Every count above was measured on 2026-09-28 against branch
`fix/covenant-cap-and-empty-sentinel` off `5aceaafc`.
- *25 PRESENT / 1 empty / 0 unexplained*: population = the **26 ticker folders under
  `data/manual/ciq/`** in the TA worktree (the licensed corpus, never committed); unit = names;
  filter = none, every folder the store enumerates; window = n/a, current files as of that date.
- *0 customer rows / 33 supplier rows*: population = BURL's two Business-Relationships exports in
  that same bundle; unit = parsed relationship rows.
- *278 chars / 36 words from 70,162 bytes*: unit = `striprtf` output vs on-disk file size, one
  file (`…BURL Customers.rtf`).
- *645,693 / 648,641 / 662,704 / 744,759*: population = the exhibits BURL's capital-structure pass
  refused under the 600K cap; unit = characters of extracted exhibit text.
- *six of seven terms*: population = this module's seven target covenant terms; unit = terms
  returned with a verbatim quote, from ONE exhibit (the 744,759-char one), not the four.

**CORRECTION TO THIS BUILD'S OWN EARLIER WORDING.** Two drafts of the code comment and the test
docstring said the false UNKNOWN would hit "EVERY consumer retailer" and was "systematic for
consumer retail". The sweep above refutes it: ROST and TGT both parse customer rows, and BURL is
the only empty view in 26 names. The generalisation was written before the sweep and survived into
two files; it is now replaced by the measured boundary in all three places. Recording it because
the claim was the kind this repo's rules exist to catch — a sector assertion drawn from one name.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The sentinel is a phrase match, and phrases change.** If CIQ reworded to "No customers are
  currently reported", the regex misses, the thin-file guard fires again and BURL returns to a
  false UNKNOWN — loudly, in the old wording, not silently wrong. *Falsifier:* the corpus pin
  `test_the_real_burl_export_is_read_as_empty_not_broken` reddens on the next CIQ pull. Accepted
  because the failure mode is the status quo ante, not a fabricated value.
- **An UNKNOWN now may carry a `source_ref`.** The constructor change is additive (default None)
  and used at exactly one call site, so no other fact changes shape and no committed artifact
  churns. `_fact` cites only on PRESENT, so the ref reaches `dossier.json` — the machine-complete
  tier — and not the rendered Markdown line. That is the three-tier rule working, but it does mean
  the PDF reader sees the honest note without the file behind it. NOT fixed here: making `_fact`
  cite on UNKNOWN would touch every UNKNOWN line in every dossier, which is a separate decision.
- **The cap is now 1.2M chars against a 1M-token window.** Sized at roughly a third of the window
  on a 3.5–4 chars/token estimate for legal prose. If a future exhibit lands between 1.2M and the
  true ceiling it still FLAGS rather than truncating — the refusal behaviour is untouched, only
  the threshold moved. *Falsifier:* a real exhibit refused at the new cap, or a request that
  exceeds the window in practice.
- **Not done here:** the retail KPI patterns for the anchored driver extractor (same-store sales,
  comparable-store growth) remain absent, so those metrics stay unextracted for BURL/ROST/TGT.
