---
status: shipped
date: 2026-11-19
prs: [1143]
supersedes:
superseded-by:
---

# The theme desk's registry export carries no report body, no long quote and no local path: the PDF reader no longer reads large type as a 1,204-character heading, and every exported row passes a public filter

**WHAT.**
- **The licence rule** (operator 2026-11-19, relayed by coordinator A: "Fix source + scrub tip").
  The registry export is PUBLIC: `export-state` and `state push` write it to the
  `theme-intelligence-state` branch of this public repository. Only titles, figures and SHORT
  quotes may leave this machine.
- **The source fix** (`vinci/theme_intelligence/documents.py`, `HEADING_MAX_CHARS = 150`). The PDF
  reader read a line in large type of at most 18 words as a heading, and merged a heading "wrapped
  onto a second line" with no length limit. A paragraph set in large type therefore became ONE
  heading, which was then the `section` of every block after it. A merge that would pass 150
  characters is now no heading: its lines are one paragraph, and the blocks after it keep the
  section before it.
- **The export, defence in depth** (`vinci/theme_intelligence/public.py`, applied in
  `Store.export_jsonl` to every row):
  - a source's own words are at most 400 characters (`display.DESK_QUOTE_MAX_CHARS`, the desk's
    cap): every `quote`, a source-risk `sentence`, and a claims row's `statement` (a passage
    claim's is the source's sentence);
  - a claim's quote shortened that way keeps its figure. When the head would drop the claim's
    `value_text`, the export writes the window around its first occurrence instead
    (`public.claim_quote`), so a later card citing the claim still finds its number;
  - a block's `section` over 150 characters is dropped (body text the reader misfiled);
  - every absolute local path is made relative to the data directory, or `⟨local path⟩/<file>`
    outside it;
  - a row no rule touches is written exactly as stored.
- **Not capped:**
  - an SEC filing's own sentence (`basis_quote`): a public record, not a publisher's text;
  - text the model wrote (card lines, reasons, rule traces);
  - `retrieval_note`: read on a74c4e30, it holds the reader's page notes and the cost estimate,
    not article text (28 over 200 characters, the longest 2,831).
- This machine's registry keeps every word. An import holds the shortened text.
- `docs/theme_intelligence.md` states the rule (§Persistence) and the heading limit (§Manual
  documents).

**WHY.** The review of #1140 found licensed text on the public branch, at its tip a74c4e30:
- report body misfiled as section headings;
- a 2,042-character and five 911-character claim quotes;
- 2 card quotes inside one thesis version.

Building this found a fourth leak: 78 absolute local paths, which show a username and a scratch
directory. They are in `article_versions.evidence_location` (17), `runs.output_dir` (57) and
`runs.warnings` (4).

The heading limit is set by the registry itself. Every real headline in it is at most 149
characters (24 words), and every longer "section" is a pull-quote or body text (183–1,204).

**HOW VERIFIED.**
- *Fails first* (`tests/test_theme_intelligence_public_export.py`, on #1140's head 8c318b01, which
  this branch stacks on):
  - a hand-built one-page PDF, 4 lines of 18-point type and 12 of 10-point body, read as one
    heading of all 4 lines, the section of every body block;
  - a synthetic article's export carried a 913-character quote, a 600-character section and an
    absolute `output_dir`.
  - The impact run's part 1 counts 6 of the 7 nodes failing on base and 0 on head.
  - The one passing at both is the negative pin that a heading set on two lines stays one heading.
  - The other negative pins import the new module, so they fail on base and hold on head: a short
    quote is untouched, a table no rule touches is byte-identical, and model text is not capped.
- *Corpus before synthetic.* The guard (`export_violations`) over the branch tip's export
  (a74c4e30) finds **390 violations**: 304 sections, 57 `output_dir`, 17 `evidence_location`,
  6 claim quotes, 4 run warnings and 2 card quotes. The same registry exported by this code has
  **0**. The 34 committed fixture JSON files under `tests/fixtures/theme_intelligence` pass the
  guard at base and head.
- *What each rule cuts.* Measured on this machine's registry, at the branch's a74c4e30 plus nothing
  local, exported to scratch, 8,899 rows:
  - sections: 304 blocks dropped, in 6 articles, 69 distinct strings, 31,916 distinct characters:

    | Article | Blocks | Distinct strings | Longest | Characters |
    |---|---|---|---|---|
    | A-f6805a6ed17c, GS Global Equity Strategy | 188 | 40 | 1,089 | 20,863 |
    | A-84d70c2ec04f, GS G4 Bond Supply | 85 | 17 | 1,204 | 8,105 |
    | A-2fb4b4c924c5, Citi | 8 | 3 | 332 | 914 |
    | A-0be56cc89833 | 10 | 4 | 240 | 840 |
    | A-9faa09cf8082, MS | 10 | 2 | 246 | 467 |
    | A-8feaba79612d, MS | 3 | 3 | 255 | 727 |

    A's count of 31,207 characters was made at another threshold; this one is sections over 150.
  - claim quotes: 6 shortened. C-24fca4a9adf226 (2,042) keeps its head, which holds its figure.
    The five 911-character table quotes are each written as the window around their own figure.
  - card quotes: 2 (TH-05B1B3DE4A v1, `s04_key_evidence`);
  - local paths: 78 rewritten.
- *Real documents.* Read with this code on the 8 PDFs of 2026-11-19 (local, licensed, never
  committed), the longest section in any is 149 (it was 1,204). Both Goldman reports' large-type
  paragraphs are paragraphs.

**BOUNDARY.**
- Counts are over `registry/*.jsonl` as exported. "Before" is the branch tip a74c4e30 as committed;
  "after" is this machine's registry at the same state, exported by this code.
- A source-text field is a `quote` or `sentence` key at any depth (JSON held as text included), or
  a claims row's `statement`. A section is `article_versions.payload.blocks[].section`.
- A local path is an absolute POSIX path under /Users, /private, /home, /var, /tmp, /Volumes, /opt
  or /root, or a Windows drive path.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *A stale hash on one version.* QA hashes a version's content AS STORED. TH-05B1B3DE4A v1's 2 card
  quotes are shortened in the export, so re-QA of its run (R-20261119T121614Z-ingest) on an imported
  registry reads that version's hash as changed. The weekly job QAs only its own run, and `upload`
  QAs only the runs it pushes. This was asked of coordinator A, with option (B), leaving card
  content uncapped. If A rules (B), the change is one exclusion in `public_payload`.
- *A window, not the whole cell.* A table figure that occurs more than once is windowed at its
  first occurrence, which may be another cell's. That is enough for the number check, which reads
  presence, and the claim's row prints its own value.
- *Not done here.* Re-exporting to the state branch (the tip scrub) and the history rewrite. Both
  wait for this PR to merge and for A's go, and nothing is pushed to that branch meanwhile.
