---
id: 2026-10-15-theme-intelligence-group-5-facts
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — group 5 of the verified review leads, a wrong or lost fact: U5, U6, U7, U10, U12, U25, U55

**WHAT.** Operator, 2026-10-15: "group the rest of the U-list and start the first". The rest of
`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md` (groups 1-4 were fixed
in #714-#722), grouped by what each lead does to a reader of the record:

| Group | Theme | Leads |
|---|---|---|
| **5** (this record) | Writes a wrong fact or loses one (engine, pipeline) | U7, U12 (both live on the pilot; U12 costs money), U5, U6, U25, U55, U10 |
| 6 | Verification and extraction checks | U17, U19, U20, U48 |
| 7 | Parsing and documents | U30, U15, U22, U50 |
| 8 | Companies and publishers | U11, U60a, U51 |
| 9 | Operations and alerts | U31a, U31c, U31d, U31f, U37, U57, U28 |
| 10 | Structure and reuse (no behaviour change) | U33, U53, U56, U58, U59, U60b, U27, U41, U34 |
| 11 | Docs and records | U35, U39, U40 |

Group 5:

| Lead | Defect | Fix |
|---|---|---|
| U7 | Re-analysis rebuilt the document without the page-stated class. Pilot A-b4589733a42a went from "page states it 'should not be regarded as a research report'" to "channel default for jpm_tmt". | `_stored_document` carries the stored class when the PAGE stated it. A class basis that is a channel default begins with `CHANNEL_DEFAULT`, the one phrase its writers and this reader share; a channel default is re-read from the current sources. |
| U12 | Re-analysis and file ingest never ran the archive pass, so SKIP theses stayed ACTIVE. The pilot's re-analysis paid to enrich three of them ($0.0965). | Re-analysis runs the archive pass BEFORE it enriches, as a scan does. The three CLI ingest commands end with `Pipeline.finish_ingest`: the archive pass, then finish. |
| U5 | A new claim on a held measure was read against `same_measure[-1]`, in claim-id (hash) order. A third origin confirming a moved date was a "timing change" in 2 of 6 text variants. | Held claims are taken in the order the thesis linked them. `_reading_for` reads a new claim against: its own origin's latest reading; else the latest it AGREES with (the same event date, or a close figure); else the latest. |
| U6 | A re-read that re-verifies an earlier thesis builds a version and discards it when nothing changes. Its review issues and the CONTEXT links of a re-anchored line were already written, for a version that never existed. | `_build_version(defer=True)` holds those writes in `Engine.deferred`. The re-read writes them with the version, or not at all. Every other caller writes them as before. |
| U25 | Re-running `article --url` on a registered URL without `--published` was ALREADY_INGESTED, but the article record, rewritten before that check, wiped the operator-verified date and the authors the text credits. | `_article_record` keeps what an earlier run verified when the new fetch cannot restate it: the earlier date when the page states none, and the authors the text credited (`TEXT_CREDIT`, the one phrase their writer and this reader share). A date the page states still wins. |
| U55 | `reassess` reused the tier its previous version recorded (a `sources.toml` change never reached it), and re-joined the old F10 note to the reasons it recomputed: a reason doubled, and a cleared HOLD stayed. Its timing context passed an empty article id. | Holds are derived as the update path derives them (failed spans, identity under review, `IDENTITY_HOLD`). Only the review's withheld-lines hold carries over (`review_holds`, prefix `REVIEW_HOLD`), since a reassess runs no review. The tier is read from the current sources (`Engine.reliability_of`, set by the pipeline from `Pipeline._reliability`, the rule the processing path uses). The timing context's article is named, its claims read from the store: the same pool as before. |
| U10 | `reanalyse --retire T --retire T` failed on the second RETIRED event, leaving T retired with no replacement. | The retire list is de-duplicated where the run reads it. |

**WHY.** Each writes a wrong fact to the registry or loses one an earlier run verified, and U12
paid for enrichment of theses that were already Skip.

**HOW VERIFIED.**
- **Real runs on copies of the pilot** (SQLite backup API; run R-20261014T110419Z-reanalyse;
  main 2a794602's code on one copy, this branch's on another; $0, no model call):
  - **U12:** an ingest run's end leaves **7** SKIP theses ACTIVE on main (19 active), and **0**
    on this branch (12 active). These are the targets the next enrichment would take.
  - **U7:** the re-analysis record of A-b4589733a42a (built by `_article_record`, not written)
    reads "channel default for jpm_tmt" on main, and keeps "b036: page states it 'should not be
    regarded as a research report'" on this branch.
  - **U55:** a reassess of every thesis changes the same 3 on both (TH-DEE87FCF51 SKIP → WATCH,
    the #714 effect, as in group 1). The current versions after it are identical on **all 23**
    (action, tier, hold note). The pilot has no failed span, no resolved identity and no tier
    change, so the fix changes nothing there.
  - The live pilot's checksum is unchanged (5fcc240d4b087d2feb1f81e6d6fabc3c).
- **U6 reproduced on the tests' re-read harness** (the orphan re-read, with a stub review that
  re-anchors one line): on main, the discarded version leaves **1** CONTEXT link for a version
  that does not exist and **1** review record; on this branch, **0** and **0**.
- **Pins:** `tests/test_theme_intelligence_group5.py`, 18 tests, each fix with its negative.
  - U5: a moved date confirmed in either id order, a date no one held, and a figure against its
    own origin, an agreeing one, and none. End to end over six wordings: the third date moves
    from 2Q27, never 1Q27.
  - U6: the discarded re-read leaves no link and no record, while its review did re-anchor.
  - U7: a page-stated class survives re-analysis, and a channel default stays one.
  - U10: retired once.
  - U12: an ingest run archives a SKIP thesis and keeps a WATCH one; a re-analysis enriches
    without the SKIP thesis.
  - U25: the date and the credited author survive a re-run, and a date the page states wins.
  - U55: a hold never doubles over three reassesses; an identity hold clears once resolved and
    stands while not; the current tier is read, and an engine without the lookup keeps the
    recorded one.
- **Mutants: 12 of 12 killed.** An unmutated baseline passes. One survived the first pass
  (scrambled linking order); the end-to-end pin now reads the moved-from date.
- Ruff and `mypy --strict vinci` clean. The offline suite result is in the PR.

**BOUNDARY.**
- Code: main 2a794602 against this branch, 2026-10-15.
- Pilot: copies of `v2/pilot-2026-10-12/registry.db` under the `theme-intelligence` worktree's
  `data/theme_intelligence/`, one per code.
- "SKIP theses ACTIVE": theses whose current version's research action is SKIP and whose status
  is ACTIVE.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **The live pilot's 7 SKIP theses** leave the active list at the next run that ends with the
  archive pass (now every scan, article, reassess, re-analysis and ingest run). The rule is the
  existing one ("a thesis archives at once when Skip"); only its reach changes.
- **The phrases `CHANNEL_DEFAULT`, `TEXT_CREDIT` and `REVIEW_HOLD`** are read back from stored
  text: the records written before this code carry no structured field for them. Each has one
  writer and one reader, sharing the constant.
- **Stored versions are not re-classified:** U5 and U55 change the next classification and the
  next reassess. The pilot's stored change classes stand as written.
- **The U6 and U55 doubling pins construct their trigger** (a stub review that re-anchors; a
  failed-span claim written through the store). The create path never links a claim that fails
  its span check, and no live registry was found in that state.
