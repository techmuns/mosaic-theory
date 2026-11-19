---
id:
status: open
date: 2026-11-19
prs: []
supersedes:
superseded-by:
---

# IT (Gartner): the operator read trigger 2 as MET against Q3 2026 under the year-on-year rule ("IT note B", 2026-11-19). The reading is one dated judgment tag on `scenarios/IT.json`'s sealed rationale, and the page is re-rendered. The verdict stays `watch` until the full re-underwrite, which is now owed: operator plus coordinator B, STATE row 32 item (34). $0, no transcript text.

**WHAT.**
- **The reading.** `verdict.reunderwrite_triggers[1]` (trigger 2, recorded 2026-07-22) reads:
  "the quarterly report shows contract-value growth stabilizing AND client count, salesforce and
  retention turning - re-set the downside case from the new evidence and re-underwrite in full".
  On 2026-11-19 the operator chose Note B. Their words, verbatim: **"IT note B"**. The note's
  text, as it now stands in the record:

  > 2026-11-19. Trigger 2 read against Q3 2026 under the year-on-year rule: contract value
  > stabilizing (YoY growth +1.0% → +1.7% → +2.5%), and client enterprises (−5.1% → −4.5% →
  > −4.1% YoY), salesforce (−3.4% → −3.2% → −1.8% YoY) and retention (global wallet −5.3 → −3.1
  > → −0.5 pts YoY) all narrowing. Trigger 2 met; the downside case is re-set from the new
  > evidence and IT is re-underwritten in full.

- **Where it is recorded.** One tag appended to `verdict.rationale`:
  `[amended 2026-11-19 (judgment): the operator's reading ("IT note B"), approving the
  year-on-year rule for "turning"; text rendered by coordinator B from Gartner's filings and 3Q26
  supplement (deck read visually): "<Note B, verbatim>" See <this record>]`. The body is 96 words,
  under the seal's 100-word cap for a `judgment` tag.
- **What does NOT change.**
  - `verdict.status` stays `watch`, and `recorded` stays 2026-07-21.
  - The trigger sentences in `reunderwrite_triggers` are unchanged, and so are their Q1 2026
    baselines.
  - `dated_triggers` and `measured_triggers` stay empty.
  - The legs, the grid, `spot` and `facts` are unchanged.
  - The re-underwrite is owed, not done. The note says "IT is re-underwritten in full" because
    that is the consequence the trigger names.
- **Four files, one line each:** `scenarios/IT.json`, `data/dossiers/IT/dossier.md`,
  `frontend/dossiers/IT.md` and `frontend/scenarios/IT.json`, each moving only the rationale line.

**WHO WROTE WHAT.**

| part | author | how |
|---|---|---|
| The five-quarter figures | Gartner | its 10-Qs, its 10-K and its 3Q26 Earnings Supplement (sources below) |
| The two reading rules, and Note B's text | coordinator B (session `local_7e5fb8ce`) | rendered under Rule Y from Gartner's filed figures, in B's uncommitted fact sheet of 2026-11-19. B states the rendering is deterministic: the approved rule decides each leg by arithmetic on the figures |
| The choice of Note B, and with it Rule Y as the reading of "turning" | **the operator** | "IT note B", 2026-11-19. This is the verdict of record on trigger 2 |
| The tag's attribution clause, this record and the STATE item | this session | no figure, and no word of the note, was written here |

**THE TWO RULES B OFFERED.** The record never defined "turning", and the outcome depends on what
it means.
- **Rule L, levels:** a measure is turning when its level rose in each of the last two quarters
  (Q1→Q2 and Q2→Q3 2026). Under it trigger 2 is **not met**, because client enterprises still fell:
  12,913 → 12,775 → 12,680.
- **Rule Y, year-on-year:** a measure is turning when its year-on-year change improved in each of
  the last two quarters, a decline that is narrowing. Under it all four legs are met.
- **The operator chose Rule Y** by choosing Note B. A future reading of an IT trigger that says
  "turning" reads it this way unless the operator rules again.

**THE FIGURES** (B's fact sheet, 2026-11-19; FX-neutral where Gartner states it; percentages
computed from the dollar figures).

| measure | Q3 2025 | FY 2025 | Q1 2026 (baseline) | Q2 2026 | Q3 2026 |
|---|---:|---:|---:|---:|---:|
| Total contract value, YoY | +2.98% (+$146.0M) | +0.80% (+$41.0M) | +1.04% (+$54.0M) | +1.67% (+$86.6M) | +2.48% (+$129.0M), $5,340M |
| Quota-bearing associates (GTS + GBS) | 5,018 | 4,984 | 4,866 | 4,874 | 4,929 |
| Client enterprises, global (deck) | 13,218 | 13,279 | 12,913 | 12,775 | 12,680 |
| Wallet retention, global (deck) | 99.5% | 97.5% | 97.7% | 98.2% | 99.0% |
| Quota-bearing headcount, YoY (deck) | +2.2% | −2.3% | −3.4% | −3.2% | −1.8% |

**SOURCES** (Gartner, CIK 749251).

| period | filing | filed | accession |
|---|---|---|---|
| Q3 2025 | 10-Q | 2025-11-04 | `0000749251-25-000082` |
| FY 2025 | 10-K | 2026-02-12 | `0000749251-26-000112` |
| Q1 2026 | 10-Q | 2026-05-05 | `0000749251-26-000167` |
| Q2 2026 | 10-Q | 2026-08-04 | `0000749251-26-000245` |
| Q3 2026 | 10-Q | 2026-11-03 | `0000749251-26-000307` |

- **The deck rows are READ VISUALLY, not extracted.** They come from Gartner's 3Q26 Earnings
  Supplement, slides 6–7 "Insights Metrics", on investor.gartner.com (Quarterly Results → 2026
  Earnings Supplement Q3). B read them from the rendered slides in the in-app browser on
  2026-11-19.
- **The cross-check B states:** the deck's salesforce and contract-value rows match the 10-Qs
  exactly. The record's two baselines that are in no 10-Q also come from this deck: 12,913 client
  enterprises (from 13,600), and wallet retention 96.5% / 98.3% / 97.7%.
- **No transcript text** is quoted here, in the tag or on the page. B's sheet cites one call-sourced
  line (GTS and GBS new business), and it is left out of this record.

**WHY THIS FIELD, AND NOT ANOTHER.** A scenario record is changed through a tool wherever one
exists. None writes a verdict amendment, so the seal is the guard.
- **Searched:** the `scenario-*` subcommands in `vinci/cli.py` (`refresh`, `propose`, `create`,
  `supersede`, `criterion`), and every writer of `[amended …` in `vinci/`, `scripts/` and `bin/`.
  None appends a tag: the only hits are `vinci/seal.py`'s own refusal messages.
- **`scenario-refresh`** changes machine inputs only (spot and facts). Its help says it never
  touches the legs, the verdict or the rationale.
- **`scenario-supersede`** reissues the record with a new grid, archiving the old one. That is the
  re-underwrite's output, and it needs the operator's grid. Superseding now would archive the record
  only to reissue it unchanged.
- **`dated_triggers` is the wrong home.** A `DatedTrigger` (`vinci/scenarios.py`) is an
  analyst-typed falsifier **with a deadline** ("ISO date the window closes"), and "the machine never
  invents a trigger or its date". The operator gave no deadline. Written with one, the page's
  catalyst calendar would print it as "unresolved by this date, the monitor flags re-underwrite
  due", on a date nobody chose.
- **`scenario-criterion`** attaches a measured criterion beside the prose. It is not a reading,
  and client enterprises and wallet retention are deck figures that are not in the dossier's
  mechanical layer.
- **The precedent is a dated `judgment` tag on `verdict.rationale`**, written as a data commit
  under the seal check: IT's own two 2026-07-22 tags, and SMPL's 2026-08-19 trigger tag (#479).
  This change went through the house API, not a text edit: `read_record` → `model_copy` →
  `write_record`, which runs `validate_for_write` and the prose-register lint (no flags).

**HOW VERIFIED** (main `5e380efc`, 2026-11-19, $0).
- **The seal refuses a tag that breaks it.** A first draft of the tag was 105 words, and
  `seal.check` refused it: "amendment 2026-11-19 (judgment) is 105 words against a 100-word cap".
  The tag as written is 96 words and passes with no violations.
- **The page moves only by the tag.** Before the change, IT's committed `dossier.md` re-rendered
  byte-identical from its stored JSON and record (88,604 characters, both). After it, `git diff`
  shows four files with one line each, the rationale. The frontend mirror is byte-identical to
  `data/dossiers/IT/dossier.md`, and it moved no other file of the 26 pages and 13 underwrites
  it emits.
- **Note B's arithmetic, re-derived from levels: 10 of its 12 figures, and all 10 agree with
  its rounding.**
  - The year-ago levels for Q1 and Q2 2026 are the deck's 1Q25 and 2Q25 columns. B sent them
    on 2026-11-19, read visually from the same slides as the rest:
    - client enterprises 13,600 and 13,374;
    - quota-bearing headcount 5,038 and 5,034;
    - global wallet retention 103.0% and 101.3%;
    - global client retention 84.4% and 84.6%, which Note B does not quote.
  - The ten that re-derive:

    | figure | Q1 2026 | Q2 2026 | Q3 2026 |
    |---|---:|---:|---:|
    | client enterprises | 12,913 / 13,600 → −5.05% | 12,775 / 13,374 → −4.48% | 12,680 / 13,218 → −4.07% |
    | salesforce | 4,866 / 5,038 → −3.41% | 4,874 / 5,034 → −3.18% | 4,929 / 5,018 → −1.77% |
    | wallet retention, global | 97.7 − 103.0 → −5.3 pts | 98.2 − 101.3 → −3.1 pts | 99.0 − 99.5 → −0.5 pts |
    | contract value | not re-derived | not re-derived | +$129.0M on $5,340M → +2.48% |

  - **Two are not re-derived here: contract value in Q1 and Q2 (+1.0%, +1.7%).** Their dollar
    levels are in each 10-Q's business-measurements table, which this session did not read.
    B's +1.04% and +1.67% are computed from those dollar pairs, and the deck's printed Y/Y row
    reads 1.0% and 1.7%. Both agree with the note.
  - The salesforce figures also match the deck's own Y/Y row (−3.4%, −3.2%, −1.8%) and the
    record's Q1 baseline (4,866, −3.4%).
  - **What this check does and does not establish.** It confirms the arithmetic from the levels
    to the note. It does not check the reading of the deck: every deck level, the year-ago
    columns included, is B's visual reading.
- **Suite:** `pytest -m "not network"` on the branch (result in the PR body).

**BOUNDARY.**
- "10 of 12": the twelve year-on-year figures in Note B's text, in % or percentage points. The
  population is two sets of levels: the levels in sections 1–2 of B's fact sheet (Q3 2025 to
  Q3 2026), and the deck's 1Q25 and 2Q25 columns, which B sent on 2026-11-19.
- "Four files, one line each": `git diff --stat` against main `5e380efc`.
- "96 words": `seal.tag_parts`'s body count, the text after the colon without the closing bracket.
- "26 pages and 13 underwrites": `frontend/build.py`'s own summary line on this run.

**WHAT IS OWED NEXT.** The full re-underwrite, owned by the operator and coordinator B.
- **The machine's part ($0):** refresh the record's machine inputs at the current price
  (`scenario-refresh`), run `scenario-propose` for IT's recipe (`R1_midcycle_margin_evebitda`), and
  assemble the evidence for re-setting the downside case. The proposed base multiple's date is
  flagged against today's price: W73 moves it to a dated multiple.
- **The operator's part:** the downside revenue path, margin and exit multiple, the base and the
  bull, the horizon, and the verdict.
- A `confirmed` or `overridden` record owes a horizon at create or supersede
  (`docs/records/2026-11-17-recipe-3b-one-time-basis-the-horizon-and-the-eps-line.md`). A `watch`
  does not.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0:** no model call and no page rebuild, only a deterministic re-render of one page from its
  stored JSON.
- **ACCEPTED: every deck level rests on B's visual reading, not on a second extraction.** The
  year-ago columns are included. Two of the note's figures (contract value, Q1 and Q2) rest on
  B's computation from 10-Q dollar pairs this session did not read. The operator chose the note
  with those figures in it, and B's deck rows match the 10-Qs where both state a figure.
  - *Falsifier:* a re-read of the deck or the 10-Qs that gives a different level, or moves any of
    the 12 figures off the note's rounding. That is a correction appended to this record and a
    new dated tag. The sealed tag is never edited.
- **The rule is now part of the reading.** Rule Y is weaker than the ordinary sense of "turning"
  (B's sheet: "the decline is slowing" is a weaker condition than "the level stops falling"). The
  operator ruled on that difference in choosing Note B, and the record says so rather than leaving
  "turning" undefined a second time.
