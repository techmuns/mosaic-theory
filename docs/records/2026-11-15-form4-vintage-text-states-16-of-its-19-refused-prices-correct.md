---
id:
status: shipped
date: 2026-11-15
prs: []
supersedes:
superseded-by:
---

# #1069's vintage text states the cost its guard measures: 19 refused, 3 wrong and 16 correct, 14 of the 16 in the 2025-02-25 filing — where it said "14 of them correct"; its prose is amended under a narrow README exception, every other field pinned as merged, and LLY's page and mirror move one line each at $0

**WHAT.**
- **The misstatement.** The extraction vintage `2026-11-14.form4-price-its-filing-contradicts-is-refused` (merged in #1069) said the Form 4 price guard refuses "19 sale prices, 14 of them correct (the 2025-02-25 filing's)".
  - Its count of correct prices is false: 16 of the 19 are correct and 3 wrong.
  - The text renders on every page stamped with that vintage, through `stamp_detail`. On main `c58d5b2f` that is LLY alone, in the Record & reproduce Extraction row of `data/dossiers/LLY/dossier.md` and its mirror `frontend/dossiers/LLY.md`. The web's table is written at deploy from the same files.
  - #1069's own record, the guard's docstring and LLY's main-body insider line ("19 of 729 sales") were right. Only the vintage text was wrong.
- **The correction.** The `names` clause now reads "refusing 19 sale prices, 3 wrong and 16 correct (14 of them the 2025-02-25 filing's)".
  - A `note` quotes the replaced words and names this record.
  - The `id`, the `follows` and the code the vintage names are unchanged.
- **The rule it uses.** `vinci/dossier/extraction_versions/README.md` said an entry "is never edited or deleted once merged". It now carries one exception, scoped narrowly, beside the legacy row `2026-08-16.1`'s amendment:
  - a merged entry's prose may be corrected only where it misstates the code it names, and never so that it names other code;
  - every other field keeps its merged value (the guard compares parsed values, not bytes);
  - the replaced words are quoted in a `note`;
  - the entry is listed in `AMENDED` (`tests/test_extraction_version_entries.py`).
- **The page.** LLY's `dossier.md` was re-rendered from its stored record by `refresh._rerender_only`, which never writes the JSON, then `mirror_to_frontend()`. This was a separate artifact-only commit.

**WHY.**
- **Found by** bookkeeping batch 9 (fix request 2), which recorded it as a known misstatement on a committed page. The coordinator briefed this $0 fix.
- **Why the rule was in question.** No guard enforced the README rule on entry files: the digest pin covers only `LEGACY_VERSIONS`, and the stamp test checks only that ids resolve. No merged entry file had ever been modified (`git log --diff-filter=M` on the folder: empty). The one amendment precedent, legacy row `2026-08-16.1`, was legitimate "only because no artifact carried" it, and LLY carries this one. So the rule was put to the coordinator before anything was edited.
- **The coordinator's ruling** (2026-11-15), verbatim: "A. The immutability rule protects what an id MEANS: which code a committed page's stamp names." A wording fix that leaves the id, `follows` and the code untouched keeps that meaning and corrects a false statement on a public page.
- **The alternatives refused.**
  - A `note` alone: nothing renders it, so LLY's page would keep printing the false count.
  - A new vintage naming the correction: no extraction output changed, and LLY would keep its stamp and the old text.
- **One point of the ruling not adopted, because it was not so.** The ruling asked this record to note that the brief and the merged text "named the wrong filing for the 14". Checked: neither did.
  - The merged text attributes the 14 to "the 2025-02-25 filing", and `0001415889-25-005456` was filed 2025-02-25 (LLY's cached submissions index). Its trades are dated 2025-02-24.
  - The brief placed them in "the 2025-02-25 filing", with a pointer to the record.
  - The only false figure was the count of correct prices: 14 where it is 16.

**HOW VERIFIED.**
- **The measurement, before writing any figure.** #1069's code (`188e0476`, its squash merge; `vinci/` exported with `git archive`) was run read-only over the HTTP cache (`data/cache/sec`):
  - 5,601 Form 4 documents, 5,601 distinct accessions;
  - 1,856 filing-and-code groups with a stated price, 751 of them with two or more prices;
  - groups over 1.4×: 10; over 1.6×, 2×, 3×, 5× and 10×: 2 each;
  - the widest spans: 1001.95× (`0000316011-25-000073`, S, 4 lines), 1001.24× (`0001415889-25-005456`, S, 15 lines), then 1.51× (UBER) and 1.44× (WERN);
  - 19 lines refused, all LLY sales.
  - The script decodes each line with `_form4_codes`'s own XPaths and calls that code's `Form4Line` and `_refuse_inconsistent_prices`.
- **Wrong against correct,** from each price's own footnote range in the filing:
  - `-000073` (filed 2025-11-17): 1031414 against $1,031.00–$1,031.99, and 1032319 against $1,032.00–$1,032.95, are wrong. 1030.312 and 1033.155 are correct, each inside its range.
  - `-005456` (filed 2025-02-25): 878401 against $878.00–$878.95 is wrong. The other 14 are inside their ranges.
  - Total: 3 wrong, 16 correct (14 + 2). These match #1069's record ("3 wrong and 16 correct. Of the 16, 14 are the 2025-02-25 filing's other lines").
- **The pins:**
  - **Figures** (`test_the_vintage_states_the_refusal_cost_its_two_filings_measure`, `tests/test_form4_price_guard.py`):
    - it measures (refused, wrong, correct, correct in the 2025-02-25 filing) = (19, 3, 16, 14) from the committed real fixture, through production's `_form4_codes`, with footnote ranges deciding wrong against correct;
    - it then requires the vintage's cost clause (from "refusing" to its closing parenthesis, the filing date removed) to state exactly those integers, in order;
    - it asserts figures, not wording;
    - **red on main's text**, which states (19, 14): "At index 1 diff: 14 != 3".
  - **The exception's guard** (`test_an_amended_entry_corrects_its_prose_and_nothing_else`): every field but `names` and `note` equals the file as merged in #1069, the false words are out of `names` and quoted in `note`, and the entry still reads with its merged `follows`. Red on main: "`names` still says '14 of them correct'".
  - **Five negative pins** (`test_an_amendment_beyond_the_prose_is_refused`): a dropped follow, a renamed id, an added field, a note that does not quote the replaced words, and the false text kept are each named.
- **The pages, $0.** Every committed page was re-rendered from its stored record to memory: 26 pages, 25 unchanged, LLY moving 2 lines (1 removed, 1 added).
  - Written: `data/dossiers/LLY/dossier.md` 1−/1+ and `frontend/dossiers/LLY.md` 1−/1+, the mirror byte-identical to its source.
  - The moved line is the Extraction row alone: "…refusing 19 sale prices, 14 of them correct (the 2025-02-25 filing's)…" became "…refusing 19 sale prices, 3 wrong and 16 correct (14 of them the 2025-02-25 filing's)…".
  - `dossier.json` was not written.

**BOUNDARY.**
- **Corpus:** cache entries under the iCloud checkout's `data/cache/sec` whose text is an `ownershipDocument` with `documentType` 4 and whose URL is an EDGAR archive XML, read 2026-11-15. One document per accession.
- **A group:** one accession's lines of one open-market code (`P` or `S`) with a stated price above zero. A count is lines (transactions).
- **Code:** `188e0476` for the measurement; this branch for the pins and the re-render, cut from main `c58d5b2f`.
- **Pages:** the 26 committed `data/dossiers/*/dossier.json` at `c58d5b2f`.
- **The footnote reading** is this record's and the test's only. Production never parses the footnotes.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A merged entry's text can now change under a page.** The exception is bounded by the guard: only the prose, only to correct a misstatement of the code named, the old words kept in a `note`.
- **What the guard cannot judge:** whether a prose edit names other code. That stays a review question.
- **The falsifier:** an entry listed in `AMENDED` whose `follows` or `id` differs from its merged file, which reds the guard; or an amended entry whose new prose describes behaviour its code does not have.
- **The remaining figures in the text** ("No committed page re-renders differently", "of the 25 committed pages a $0 build reaches") are #1069's claims about #1069's change, at #1069's time, and are left as written.
