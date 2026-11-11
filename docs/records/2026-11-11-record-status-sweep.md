---
id:
status: shipped
date: 2026-11-11
prs: [1012]
supersedes:
superseded-by:
---

# Every record reading `status: open` is now cited by an open §5.0 row: of the 82 open records, 68 are flipped (63 shipped, 4 recorded, 1 superseded) and 14 stay open, and a lint holds it

**WHAT.**
- **The sweep.** It covers every `docs/records/*.md` reading `status: open` on main `cbefc245`, 82 in all: 79 open on `2637e91b`, where the sweep began, plus three added by #971, #1009 and #972, which merged before it finished. Each is flipped to `shipped`, `recorded` or `superseded`, or kept `open`, by the rule below. The decision and evidence for each of the 82 are in the table at the end.
  - The only existing line changed in any record is its front-matter `status:`.
  - 32 of the `shipped` records had an empty `prs:` and no amendments heading. Each gains one appended `## Amendments` entry naming its PR, because `tests/test_records_ledger.py::test_a_shipped_record_names_the_pr_that_carried_it` refuses a shipped record with neither. The README allows nothing else after merge.
- **The lint**, `tests/test_record_status_matches_open_now.py`. A record reading `status: open` must be cited by filename in a numbered row of §5.0 OPEN NOW, outside struck (`~~…~~`) text. It failed first on `2637e91b`, naming 27 records, and passes after the sweep. On `cbefc245`, before the last flip, it names 1: #972's record. Incident → invariant, shipped Y.

**THE RULE THE SWEEP APPLIED.**
- **`open`**: the record anchors an open §5.0 row, and the item that row tracks is still open. 14 records.
- **`shipped`**: a build record whose PR merged. 63 records. Where part of the build is still open, it is tracked elsewhere, either as an open row's own item (row 41's combined rebuild) or as a fix-log row under row 60. The table names it.
- **`recorded`**: a pre-registration, a pilot run, a design, or a follow-up list whose items closed. 4 records.
- **`superseded`**: the item the record opened was retired whole by a later record. 1 record.

Every flip rests on its merged PR. `gh pr view` reads each of the 81 PRs as MERGED. Each record's adding commit on main's first parent is that PR's squash commit: 81 of 81, 0 mismatches. Two records came in one PR, #703.

**WHY.** B proposed the sweep and the lint on #1004 on 2026-11-11, and the operator approved them. §5.0 is the one authority on what is open, and the README says `status:` flips "when the item closes, is falsified, or is superseded". Nothing checked that it did. So the ledger came to answer "is this open?" one way while the snapshot answered it the other. For example, `2026-11-05-fact-layer-r2-upload.md` says in its own title that it closes STATE row 32's item (30), and it still read open.

**HOW VERIFIED.**
- **Fail first.** On unchanged `2637e91b`, the corpus lint fails naming 27 records and its 7 pins pass. The pins run on the real STATE.md and a real open record:
  - a row that drops its citation;
  - a citation only in §2 or in §5.0's prose;
  - a citation inside struck text;
  - a name that is a prefix of a cited one;
  - `status: open` quoted in a body;
  - the remedy, any closed status, passes.
- **After the sweep**, the six files holding the ledger, STATE and fix-log lints pass: 1016 passed, 1 skipped, with this record in the tree, before the merge of `main`. The full offline suite passed before the merge (10,630 passed, 629 skipped, 6 xfailed, with the network tests and the two `customers()` corpus tests of `tests/test_segment_absence_and_relationship_route.py` deselected). The PR body carries the run on the merged tree.
- **The body guard read the changed records.** A one-word body edit to one of them (`**WHAT.**` → `**WHAT**`) is refused by `test_a_merged_record_body_is_immutable`. Restored, with its appended amendment, the record passes. The amendment heading follows the old body with no blank line before it, so the body the guard splits off is byte-identical to the merged one.
- **The diff** removes 65 lines across 65 records, every one of them `status: open`. Nothing else is removed.

**BOUNDARY.**
- The population is every `docs/records/*.md` except README and TEMPLATE, at main `2637e91b` (2026-11-11). Of these, 79 read `status: open`. Across the sweep, ending at `cbefc245`, 82 did.
- A citation is the record's filename inside a numbered row of §5.0, with struck spans removed. By that rule, on `2637e91b`, 52 of the 79 were cited and 27 were not.
- The #1004 proposal counted 77 open and 36 uncited at `4c8349bc`. At `4c8349bc`, this rule counts 77 open and 25 uncited. Two other rules give the same 25: the full `docs/records/<name>` path, and unstruck text. The item cell alone gives 28. The 36 is not reproduced.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The lint checks one direction.** An open row may cite a shipped record as background, so "cited ⇒ open" is not pinned. Whether a cited record's item is still open is a judgment. It was made here for each of the 52 cited records: 14 kept, 38 flipped. *Falsifier:* a kept record whose row's item has closed, or a flipped one whose own item is still open.
- **PRs in flight.** At its head, #1006 adds a record reading `status: open` that no open row cites. #971's, #1009's and #972's merged while this was open, and are swept here. Once this merges, each needs `shipped` at merge, or a citation in the row that tracks it, before its re-sync passes. A new build record is written `shipped`, as A's bookkeeping records already are.
- **§5.0's prose lines do not count.** The cohort falsifier (#507) is named only in §5.0's "PRE-REGISTERED, WAITING ON DATA" line, which calls it "not a build". So it is `recorded`, and its readout will be a record of its own.
- **32 appended amendments** are what flipping an empty-`prs:` record honestly costs. The alternative, `recorded`, would call a merged code change something that only happened and was written down.
- **Three partial fixes are `shipped`**: #962 (RE2-D6), #966 (RE2-D10) and #976 (RE2-D20). Their remaining halves are `in progress` rows in the fix log, under row 60.

## The 79 decisions

On main `cbefc245`. Each evidence cell gives the PR and its squash commit, then, where it applies, the open row or the remainder.

| record | decision | evidence |
|---|---|---|
| `2026-08-26-cohort-anchoring-falsifier.md` | recorded | #507 merged `2cd72167` 2026-08-28; a pre-registration, written and frozen; §5.0's own prose calls it "not a build", and its readout waits on 10 verdicts per arm |
| `2026-09-01-app-shell-is-not-a-404.md` | shipped | #565 merged `8d57e6a7` 2026-09-02; its context.json gap was a theme-driver gap; themes retired (#908) |
| `2026-09-01-r3-reaches-the-create-path.md` | shipped | #557 merged `c005449f` 2026-09-01 |
| `2026-09-02-below-split-into-its-own-driver.md` | superseded | #572 merged `6156bab7` 2026-09-02; the driver it split out was retired with `vinci.themes` on 2026-11-04 (#908, 2026-11-04-retire-themes-and-the-charting-reader.md) |
| `2026-09-02-state-integrity-followups.md` | recorded | #577 merged `32ca8994` 2026-09-02; items 1 and 2 closed won't-do (its own amendment; rows 17 and 18 deleted); item 3 landed as the template's BOUNDARY field in #580 (a78b3c12) and CLAUDE.md's rule; row 19 is empty |
| `2026-10-05-pending-after-the-forward-multiples.md` | open | #664 merged `2c770098` 2026-10-05; row 32 item (1), the normalized-EPS basis ruling, is still the operator's |
| `2026-10-12-theme-intelligence-pilot-corrections.md` | shipped | #703 merged `e7e49a13` 2026-10-14; the J.P. Morgan acceptance-test question ended with the pilot's retirement (2026-10-21-theme-intelligence-one-registry.md) |
| `2026-10-12-theme-intelligence-supervised-pilot.md` | recorded | #703 merged `e7e49a13` 2026-10-14; the one supervised pilot run, an experiment; the pilot retired 2026-10-21 (2026-10-21-theme-intelligence-one-registry.md) |
| `2026-10-26-self-funding-reads-the-latest-quarter.md` | shipped | #806 merged `5f4bf269` 2026-10-26; its pages: row 32 item (17), closed 2026-10-26 (2026-10-26-artifact-pass-17-pages.md) |
| `2026-10-27-release-source-and-page-furniture.md` | open | #829 merged `ad0a11df` 2026-10-27; row 30: the committed pages keep their old guide rows until each is re-assembled |
| `2026-10-30-a-filings-window-reads-every-submissions-page-it-overlaps.md` | open | #878 merged `894e962e` 2026-10-31; row 42: its two edges are open (S3's prices/refresh stream) |
| `2026-10-30-a-marker-or-absent-row-is-no-value-never-zero.md` | shipped | #877 merged `01c95fde` 2026-10-31; pages: row 41's combined rebuild |
| `2026-10-30-a-press-release-income-statement-is-refused-and-each-ltm-checked-against-its-quarters.md` | shipped | #868 merged `9503c4fa` 2026-10-30; pages: row 41 |
| `2026-10-30-edgar-reads-that-stopped-short-say-so.md` | shipped | #871 merged `8e6b12b1` 2026-10-30; pages: row 41 |
| `2026-10-30-one-latest-cell-reader.md` | shipped | #872 merged `ad84cb3f` 2026-10-30; pages: row 41 |
| `2026-10-30-the-edgar-fallback-says-where-each-figure-was-filed.md` | shipped | #875 merged `08948b5a` 2026-10-30; pages: row 41 |
| `2026-10-30-the-synthesis-is-asked-for-each-material-figure.md` | shipped | #865 merged `a15a2abf` 2026-10-29 |
| `2026-11-01-four-small-ciq-reader-fixes.md` | shipped | #881 merged `60151ccc` 2026-11-02; pages: row 41 |
| `2026-11-02-amended-filings-are-read-by-the-operators-ruling.md` | shipped | #882 merged `936dd707` 2026-11-02; pages: row 41 |
| `2026-11-02-inputs-are-cut-at-the-pages-price-date.md` | shipped | #884 merged `ae016a68` 2026-11-03; pages: row 41 |
| `2026-11-02-mnst-and-celh-followed-neither-page-built.md` | open | #887 merged `89ae0ad1` 2026-11-03; row 32 item (27): MNST has no page until its Q3 10-Q, and CELH is not followed |
| `2026-11-02-net-debt-is-read-as-filed-by-the-pages-price-date.md` | shipped | #885 merged `02314b24` 2026-11-03; pages: row 41 |
| `2026-11-03-the-at-price-ex-lease-multiple-reads-its-share-count-as-filed-by-the-price-date.md` | shipped | #888 merged `9e996d7f` 2026-11-03; pages: row 41 |
| `2026-11-04-fact-layer-adr.md` | open | #896 merged `48c12137` 2026-11-04; row 44: slices 2b–6 are open |
| `2026-11-04-fact-layer-slice-2a.md` | shipped | #904 merged `bd6e0d12` 2026-11-04; its deferred item, the screen objects in one worktree, closed when both snapshots went to R2 (#913) |
| `2026-11-05-every-page-records-what-it-was-built-from.md` | open | #911 merged `c4c9f432` 2026-11-05; row 48: slice 1 shipped; the gate (slice 2) is next |
| `2026-11-05-fact-layer-r2-upload.md` | shipped | #913 merged `049fbfe6` 2026-11-05; its title closes row 32 item (30); row 32 lists (30) closed |
| `2026-11-05-the-non-operating-window-reads-each-filers-fourth-quarter.md` | open | #916 merged `c6ce5782` 2026-11-06; row 51: in code, not yet on the pages |
| `2026-11-06-synthesis-eval-harness-design.md` | open | #924 merged `8a1fab7a` 2026-11-06; row 53: the harness program (order 8, S1) is open |
| `2026-11-06-the-fact-layers-labels-describe-never-judge.md` | open | #923 merged `a9c59287` 2026-11-07; row 54: in code; no page carries it until rebuilt |
| `2026-11-09-fix2-e1-asof-reach-and-amendments.md` | shipped | #944 merged `a9c60902` 2026-11-10 |
| `2026-11-09-fix2-e1-round-figure-restatements-are-named.md` | shipped | #940 merged `ecd95189` 2026-11-10 |
| `2026-11-09-fix2-e1-sec-budget-across-machines.md` | shipped | #939 merged `02ed3d29` 2026-11-10 |
| `2026-11-09-fix2-order2-coverage-credit-and-graph-judge.md` | shipped | #937 merged `d1a91f0a` 2026-11-10 |
| `2026-11-09-fix2-order2-customer-count-surprise-listing-containing-headline.md` | open | #936 merged `6fbbb4a2` 2026-11-09; row 59: six pages print no customer count until each is re-assembled |
| `2026-11-09-teamnostra-fix-request-2.md` | open | #934 merged `23772a60` 2026-11-09; row 60: fix request 2 is open (the fix log) |
| `2026-11-09-the-layer-cuts-releases-and-ciq-guidance-at-the-price-date.md` | open | #932 merged `cb8139ee` 2026-11-09; row 57: in code; no page carries it until rebuilt |
| `2026-11-10-driver-evidence-store.md` | shipped | #951 merged `586fdcfd` 2026-11-10 |
| `2026-11-10-driver-facts-not-quotes.md` | open | #941 merged `d0563738` 2026-11-10; row 60: the RG-D19/RG-D8 stream's PR 3 (#1006) is open |
| `2026-11-10-fix2-e1-a-point-guide-is-a-range-of-one.md` | shipped | #945 merged `1d0c374c` 2026-11-10 |
| `2026-11-10-fix2-e1-an-8ka-hit-is-an-8ka.md` | shipped | #948 merged `9f6175db` 2026-11-10 |
| `2026-11-10-fix2-e2-a-covenant-value-states-only-figures-its-quote-states.md` | shipped | #961 merged `d9dd48f5` 2026-11-11 |
| `2026-11-10-fix2-e2-a-going-concern-denial-is-not-doubt.md` | shipped | #966 merged `7adfdae4` 2026-11-10; RE2-D10's no-flag half: fix-log row, in progress |
| `2026-11-10-fix2-e2-a-maturity-belongs-to-its-subject-and-an-unread-body-is-not-a-clean-scan.md` | shipped | #969 merged `670a784c` 2026-11-10 |
| `2026-11-10-fix2-e2-a-release-actual-is-never-dropped-silently.md` | shipped | #962 merged `bfedbac9` 2026-11-10; RE2-D6 partial: fix-log row, in progress; notes land with the $0 release_figures_transform pass |
| `2026-11-10-fix2-e2-a-wall-for-part-of-the-debt-is-not-the-wall.md` | shipped | #956 merged `f2c8cfc3` 2026-11-10 |
| `2026-11-10-fix2-groupF-a-split-confirmed-by-two-vendors-and-a-realized-total-return.md` | shipped | #943 merged `93a50599` 2026-11-10 |
| `2026-11-10-fix2-groupF-b-the-universes-inputs-on-one-basis.md` | shipped | #946 merged `7d0e3c91` 2026-11-10 |
| `2026-11-10-fix2-groupF-c-a-stale-close-is-never-sealed.md` | shipped | #947 merged `81644a28` 2026-11-10 |
| `2026-11-10-fix2-groupF-d-two-stale-seals-corrected-by-appended-rows.md` | shipped | #954 merged `5ec1dc7c` 2026-11-10; rows appended (#980), read by the web (#1001); row 38's rehearsal is its own item |
| `2026-11-10-fix2-groupF-e-a-correction-row-is-tagged-and-the-suite-reads-a-corrected-ledger.md` | shipped | #955 merged `5e3def4a` 2026-11-10 |
| `2026-11-10-fix2-groupF-f-the-two-corrections-appended.md` | shipped | #980 merged `946943ec` 2026-11-11; the web reads the correction since #1001 |
| `2026-11-10-fix2-order3-bridge-total-and-band-history.md` | shipped | #960 merged `33ff2024` 2026-11-10; the bridge notes land in the page pass after driver facts PR 3 (#1006) |
| `2026-11-10-fix2-order3-ciq-marker-residuals.md` | shipped | #957 merged `507d4f32` 2026-11-10 |
| `2026-11-10-fix2-order4-unit-and-headers.md` | shipped | #963 merged `2f920944` 2026-11-10 |
| `2026-11-10-fix2-order5-header-offset-and-renamed-tabs.md` | shipped | #971 merged `df24ff35` 2026-11-11; RA-D7 and RA-D12 (fix log: batch 4) |
| `2026-11-10-fix2-order5-kind-by-exact-name-and-pdf-profile.md` | shipped | #970 merged `173b4818` 2026-11-11 |
| `2026-11-10-fix2-order5-period-order-and-duration.md` | shipped | #972 merged `cbefc245` 2026-11-11; RA-D5 and V1-O2 (fix log: batch 4) |
| `2026-11-10-fix2-order6-loud-with-the-right-cause.md` | shipped | #965 merged `cd832299` 2026-11-10 |
| `2026-11-10-fix2-rd-d1-dated-impairment-headroom.md` | shipped | #953 merged `7ec84833` 2026-11-10; RD-D1 fixed in the fix log |
| `2026-11-10-fix2-vinci-ciq-removed.md` | shipped | #964 merged `a71b9f67` 2026-11-10 |
| `2026-11-10-the-proposal-vote-rule-design.md` | recorded | #950 merged `9da0d096` 2026-11-10; a design (no code); implemented by #982 (83258405, 2026-11-11-the-vote-rule-implemented.md, shipped) |
| `2026-11-11-fix2-e1-same-day-filings-alias-by-day-and-segment-namespaces.md` | shipped | #986 merged `65758333` 2026-11-11 |
| `2026-11-11-fix2-e2-a-guide-is-read-as-stated-or-said-aloud.md` | shipped | #976 merged `2b9b766c` 2026-11-11; RE2-D20 partial: fix-log row, in progress |
| `2026-11-11-fix2-f27-relationship-view-edges.md` | shipped | #975 merged `c2a4d743` 2026-11-11 |
| `2026-11-11-fix2-fact-layer-acceptance-staleness-and-causes.md` | shipped | #992 merged `31ff7b87` 2026-11-11 |
| `2026-11-11-fix2-fact-layer-keeps-the-pages-originals.md` | shipped | #999 merged `3d55bc31` 2026-11-11 |
| `2026-11-11-fix2-groupF-g-a-refresh-never-mixes-split-bases.md` | shipped | #991 merged `87f763d3` 2026-11-11 |
| `2026-11-11-fix2-groupF-googl-voided-by-an-appended-row.md` | shipped | #984 merged `a3fc8e1b` 2026-11-11 |
| `2026-11-11-fix2-groupF-h-googl-void-appended.md` | shipped | #1008 merged `2637e91b` 2026-11-11 |
| `2026-11-11-fix2-groupF-web-twin-corrections-and-voids.md` | shipped | #1001 merged `8a72be4c` 2026-11-11 |
| `2026-11-11-fix2-hooks-ci-and-tests.md` | shipped | #996 merged `7edbfa36` 2026-11-11; RH-D2 and RH-D10 went on in #1002 (its record stays open) |
| `2026-11-11-fix2-order6-quality-reason-names-only-live-code.md` | shipped | #974 merged `ed2c5f8f` 2026-11-11 |
| `2026-11-11-fix2-order9-ciq-notes-corrected.md` | shipped | #998 merged `8c5e7345` 2026-11-11 |
| `2026-11-11-fix2-ra-d2-dividend-level-and-na-unstated.md` | shipped | #981 merged `62d682c6` 2026-11-11; measured on the panel, ships (#985) |
| `2026-11-11-fix2-ra-d4-same-day-guides.md` | shipped | #983 merged `85306351` 2026-11-11; measured on the panel, ships (#994) |
| `2026-11-11-fix2-rd-d2-the-unpriced-count-names-its-horizon.md` | shipped | #1003 merged `3410860a` 2026-11-11 |
| `2026-11-11-fix2-rd-unpriced-insider-lines-and-hidden-lease-cells.md` | shipped | #995 merged `6d9907d7` 2026-11-11 |
| `2026-11-11-fix2-rg-d20-instructions-say-what-the-code-does.md` | shipped | #1009 merged `d8147e97` 2026-11-11; RG-D20 (fix log: batch 4) |
| `2026-11-11-fix2-rh-d2-rh-d10.md` | open | #1002 merged `e3f715b0` 2026-11-11; row 32: RH-D10 closed, but RH-D2's hook edit waits on the operator |
| `2026-11-11-fix2-version-entries-one-file-per-vintage.md` | shipped | #988 merged `fdf85180` 2026-11-11 |
| `2026-11-11-impact-check-cross-setup-validation.md` | shipped | #1000 merged `fb568c7f` 2026-11-11 |
