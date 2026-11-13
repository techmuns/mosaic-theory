---
id:
status: shipped
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# A full-text-search hit on an 8-K/A is an 8-K/A: efts's own `form` is read before its family, and the covenant pointer writes it (TeamNostra fix request 2, RE1-D11). 1 of 92 frozen pointer rows moves: WERN's credit agreement

**WHAT.**
- `vinci/edgar/client.parse_fts_hit` reads efts's `form` (the filing's own form) first. Its
  fallbacks are `root_forms` (the family), then `file_type` (the matched document), the last only
  when it is the main document's. An exhibit type such as "EX-99.3" is never a form (review
  round 0).
- `dossier/mechanical._covenant_pointers` writes the hit's form into the pointer row, where it
  wrote the literal "8-K". This is the line the coordinator cleared for this change, cited as
  ~4915; it is line 4937 in this tree.
- `_maturity_sources`, which reads the 8-Ks the pointers link, takes a link from every pointer's
  accession, whatever its label. Before, it took one only from a row reading "8-K", so an
  amendment newly named as one would have dropped out of the maturity check. Only an 8-K or an
  8-K/A in the submissions list can match a linked accession (review round 0).

**WHY.**
- **TeamNostra's reproduction (RE1-D11).** For a `form` / `file_type` of "8-K/A",
  `FtsHit.form` was "8-K", and no field said the filing was an amendment.
- **What efts sends, read in this machine's efts cache.** 49 distinct (root, form, document)
  triples. For an amendment, `root_forms` is ["8-K"], `form` is "8-K/A", and `file_type` is the
  matched document ("EX-99.3", "EX-99.1", or "8-K/A" when the main document matched). Read family
  first, every 8-K/A was an 8-K.
- **On a committed page.** WERN's 22 Unsecured Credit Agreement pointer is
  `0000793074-26-000090`, which EDGAR lists as an 8-K/A of 2026-04-14. The page reads "8-K", and
  so do the 19 covenant-term source refs and notes drawn from it ("8-K 0000793074-26-000090 ·
  wern-20260127ex101.htm").

**HOW VERIFIED.**
- **Fail first.** `tests/test_fts_amendment_form.py`, built on WERN's real efts hit, run in a
  throwaway checkout of `origin/main` `6fbbb4a2`: 5 of its 8 cases failed.
  - The parser returned "8-K".
  - An exhibit type would have been read as the form.
  - The pointer row read "8-K".
  - The maturity check dropped the link of a row labelled "8-K/A", and of one labelled "8-K12B".

  The 3 guards passed: a hit stating no form is named by its family, an original 8-K still reads
  "8-K", and a row labelled "8-K" keeps its link. All 8 pass after, with `test_edgar.py`, the
  covenant tests, `test_efts_caps_and_instants.py` and `test_amended_filings.py`.
- **The $0 page compare: the 28 pages frozen at `bcda7ce3`.**
  - **Population:** every covenant-pointer row reading "8-K" with an accession, 92 rows.
  - **Method:** each accession's form looked up in the submissions documents and every older page
    read live on 2026-11-09/10. All 92 resolved, after reading NFLX's three older pages for its
    2009 and 2014 pointers.
  - **Result: 1 of 92 is an 8-K/A,** WERN's `0000793074-26-000090`.
- **What moves on WERN, and when.**
  - On a rebuild, 20 labels move: `covenant_pointer_rows[0].filing` and the 19 covenant-term
    source refs and notes that cite the filing. They change from "8-K …" to "8-K/A …"; no value
    changes.
  - Its maturity check keeps the filing as a linked source.
  - Whether a $0 refresh can rewrite these labels was not checked. A re-assembly does, and
    WERN is on order 1's rebuild list (E2-D15's WERN half).
  - No other page moves.
- **The version.** Row `2026-11-10.fts-amendment-form`, re-pinned.
- **The full offline suite** ran green before commit (`bin/commit`).

**BOUNDARY.**
- **92 rows:** every object on the 28 `data/dossiers/*/dossier.json` at `bcda7ce3` carrying
  `filing` == "8-K", an `accession` and `exhibits`. All of them are
  `capital_structure.covenant_pointer_rows`.
- **49 triples:** the distinct (`root_forms`, `form`, `file_type`) values over every hit in the
  primary checkout's `data/cache/efts`, 2026-11-10.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **WERN's committed page keeps "8-K" until it is re-assembled.** That is a label, and the
  accession it names is correct.
- **`FtsHit` carries one form.** A reader that wants the family as well reads it from the form
  (`8-K/A` → `8-K`); none does today.
## Amendments

- **2026-11-11 — `status: open` → `shipped`** (the record-status sweep, `docs/records/2026-11-11-record-status-sweep.md`). This record's change merged to `main` as `9f6175db` (#948) on 2026-11-10. `prs:` was left empty at merge; the front matter stays as merged, so this entry names the PR.
- **2026-11-13 — what this PR's next build changes, from the impact sweep** (operator ruling 3, 2026-11-12, verbatim: "Yes, as appended amendments (Recommended)"). The body above is unchanged. The sweep ran this PR with `vinci.impact` (base `93a50599`, head `9f6175db`, measured 2026-11-11, $0): base code against head code on the same inputs, which shows what each page's NEXT build would change. Its record, with every row of the sweep, is `docs/records/2026-11-13-fix2-impact-sweep.md`.
  - **#948: WERN's synthesis request moves**, in its `facts` section (the covenant pointer row's form, `8-K` → `8-K/A`). WERN is off the panel. The body names WERN's pointer row and its labels, and says nothing about the request.
