---
id:
status: shipped
date: 2026-11-13
prs: [1028]
supersedes:
superseded-by:
---

# The fix-request-2 impact sweep, 49 of 49 PRs (#936 to #1003): `vinci.impact` measured what each PR's next build moves, base code against head code at $0. 11 moved something their own body did not state; in 2 of them a panel page's synthesis request moved with no panel check (#953 on five panel pages, #983 on BURL)

**WHAT.** The operator asked on 2026-11-11 for the cross-setup check (RUNBOOKS §o) to run on every
fix-request-2 PR that merged with a hand-built section ("Yes, run the sweep"). For each of the 49
PRs, with `N` its merge commit on main, the sweep ran
`python -m vinci.impact run --base N^ --head N --skip-fail-first` and read the report beside the
PR's own body. The operator said on 2026-11-13 "go ahead with the #1028 re-runs"; this record
finishes the sweep.

- **11 of 49 PRs moved something their body did not state** (the "reading" column):
  - **7 MISS**, a move the body denied or did not mention: #936, #944, #948, #953, #956, #966
    and #983;
  - **3 a wider move than the body counted**: #960 (`count`, 27 pages, not 13), #965 (`count`,
    18 pages, not 5) and #981 (`coverage`, it built 17 of 27; the other 10 move too);
  - **1 CORRECTION**, #976: its body said NFLX's and VITL's requests move, and 0 of 27 do; WERN's
    +2 release notes are not stated.
- **A panel page's request moved with no panel check in 2 of them:**
  - **#953**, on BURL, CNXC, MCK, ROST and SMPL (the `facts` section; 23 of 27 requests move). The
    check was approved as a retrospective run once order 8 merged; order 8 merged on 2026-11-12
    (#1030), and on main at 2026-11-13 the run has not happened.
  - **#983**, on BURL (new in this pass). Its panel check (#994) drew on a transform that left
    BURL as committed, because "BURL's committed guidance predates A-D8's block discovery, so no
    code rebuilds it". A build does rebuild it: BURL's next build gains 9 same-day guide rows, and
    its request moves in `facts` (82 lines added). No check has measured that.
  - Nothing was spent on either; the coordinator routes any paid check.
- **38 of 49 move only what their body states.** That count includes #962, whose 29 note moves on
  9 pages sit against its stated 28 notes on 10 (`≈ as stated`).
- **The 11 re-runs of 2026-11-13 move nothing.** That is #940's 4 unbuilt pages, #964, #975, #984,
  #986, #991, #995 and #999, and the three never started (#1001, #1002 and #1003). On each, 0 pages
  move and 0 requests move. #984's 5 pages moved on 2026-11-12 on the build day alone; with #1025's
  tool they do not.
- **Corrections, as appended amendments** (operator ruling 3, 2026-11-12, verbatim: "Yes, as
  appended amendments (Recommended)"; #1029 is the precedent). #1029 amended the records of #953,
  #956, #960, #965 and #976. This PR amends five more, each with one dated entry and no body
  rewritten:
  - #936 (`2026-11-09-fix2-order2-customer-count-surprise-listing-containing-headline.md`);
  - #944 (`2026-11-09-fix2-e1-asof-reach-and-amendments.md`);
  - #948 (`2026-11-10-fix2-e1-an-8ka-hit-is-an-8ka.md`);
  - #966 (`2026-11-10-fix2-e2-a-going-concern-denial-is-not-doubt.md`);
  - #983 (`2026-11-11-fix2-ra-d4-same-day-guides.md`).
  #981's record already carries its 10 extra pages, in its own amendment of 2026-11-11.

"Pages move" means base code against head code on the same inputs: the page's NEXT build, not the
committed page. "Requests move (on panel)" counts pages whose own build's synthesis request
differs, and names the panel pages among them. The six panel pages' frozen replay (each held at
its frozen blob) was identical in all 40 reports that ran it, of both passes. A "—" under "built" means base and head carry the same
`vinci/` tree and frontend source, so nothing is built.

| PR | measured (UTC) | built | pages move (fields) | requests move (on panel) | reading | what the measurement adds to the body |
|---|---|---|---|---|---|---|
| #936 | 11-11 | 28/28 | 25 (29) | 1 | MISS: request | PARR's request moves in `facts` (its surprise history, RA-D1). Body: "All 28 synthesis requests are byte-identical", but that compare held the committed page fixed. Off the panel. Pages: 25 move on the customer count, as stated. |
| #938 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #937 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #939 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #946 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #945 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #942 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #940 | 11-11, 11-13 | 27/27 | 0 (0) | 0 | as stated | 23 pages built 2026-11-11, and the 4 the environment stopped (NFLX, PARR, ROST, SMPL) built 2026-11-13: 0 of 27 pages and 0 requests move, as the body says ("0 of 28 pages move"). The extraction version moves, reported apart. |
| #943 | 11-11 | 27/27 | 0 (0) | 0 | as stated | Monitor output gains `realized_price_return` (RF-D3). |
| #948 | 11-11 | 27/27 | 1 (1) | 1 | MISS: request | WERN's pointer row moves, as stated; WERN's request ALSO moves in `facts`, and the body says nothing about requests. Off the panel. |
| #947 | 11-11 | — | 0 (0) | 0 | as stated | No page reaches the changed code; consumers as stated. |
| #944 | 11-11 | 27/27 | 1 (1) | 1 | MISS: page + request | PARR's cadence "37 results 8-Ks" → "38" at the same inputs, and PARR's request moves in `facts`. Body: "0 of 28 pages move" (true of each page at its own price date; this is its next build). Off the panel. |
| #949 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #954 | 11-11 | 27/27 | 0 (0) | 0 | as stated | Decision-ledger stdout adds "0 correction(s)", which is the PR's purpose. |
| #941 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #951 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #953 | 11-11 | 27/27 | 27 (488) | 23 (BURL, CNXC, MCK, ROST, SMPL) | MISS: panel request | 23 requests move in `facts`, 5 of them on the panel (BURL, CNXC, MCK, ROST, SMPL). Body: byte-identical, from the frozen replay. No panel check yet: it waited on order 8, which merged 2026-11-12 (#1030); on main at 2026-11-13 the run has not happened. |
| #955 | 11-11 | — | 0 (0) | 0 | as stated | No page reaches the changed code; consumers as stated. |
| #964 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("Pages rebuilt: none"). The head scoring report that refused an offloaded cache file on 2026-11-11 now runs, identical at both refs. |
| #956 | 11-11 | 27/27 | 2 (14) | 2 | MISS: page + request | MVST and WERN: the maturity wall goes from located to not_stated (7 fields each); both requests move in `primary_source`. Body: "0 of 27 pages move", "No synthesis request changes". MVST's committed page still says located, so it moves at its next assembly; WERN's committed page already says not_stated. Off the panel. Since then #1039 (merged 2026-11-13) fixes WERN's as #956's regression and leaves MVST's not_stated (MVST is being retired, #1044). |
| #962 | 11-11 | 27/27 | 9 (29) | 0 | ≈ as stated | 9 pages, 29 release-note moves (the body: 28 notes on 10 pages). Not sent: 0 requests, as stated. |
| #966 | 11-11 | 27/27 | 1 (2) | 1 | MISS: page + request | MVST's going-concern quote changes (2 fields) and MVST's request moves in `primary_source`. Body: "no committed page moves". Off the panel. |
| #957 | 11-11 | 27/27 | 2 (2) | 0 | as stated | ORKA and TECX gain a consensus note (in NOT_SENT): 0 requests. |
| #969 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #960 | 11-11 | 27/27 | 27 (29) | 0 | count | All 27 pages' `ev_bridge.note` move at a fresh build, plus 2 exit reasons; the body says 13 bridges. Outside the request: 0 move, as stated. |
| #963 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #965 | 11-11 | 27/27 | 18 (88) | 0 | count | 18 pages' `qa_flags` move at a fresh build (44 out, 44 in); the body names 5 committed pages. Not sent: 0 requests, as stated. |
| #974 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #975 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("no page moves and no synthesis request changes"). The extraction version moves on all 27, reported apart. |
| #976 | 11-11 | 27/27 | 7 (38) | 0 | CORRECTION | 0 of 27 requests move; the body said NFLX's and VITL's do, but caveats are never sent. Notes: NFLX +3 and VITL +2, as stated; WERN +2 not stated (a newer release). |
| #980 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #961 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #970 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #988 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #993 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #981 | 11-11 | 27/27 | 27 (604) | 27 (BURL, CNXC, LLY, MCK, ROST, SMPL) | coverage | Built 27 of 27; the body built 17 (10 had no bars). Those 10 also move, and so do their requests: GOOGL, NFLX, TGT, TJX, UBER and V off the panel; BURL, LLY, MCK and ROST on it. The panel check ran (#985). |
| #992 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #987 | 11-11 | — | 0 (0) | 0 | as stated | No page reaches the changed code; consumers as stated. |
| #986 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 13,986 values move on 27 pages"). The extraction version moves on all 27, reported apart; the frontend build's git-ignored `snapshots/extraction_versions.json` gains the new vintage, as #988 designed. |
| #984 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13 with #1025's tool: the 5 pages that moved on the build day alone (BRBR, BURL, CNXC, EPAM, FUBO) no longer move; 0 pages and 0 requests, as the body says. `vinci ledger`'s summary line gains "0 void(s)", which is the PR's purpose. |
| #995 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 27 pages move"; no request "at re-assembly either"). The body's compare ran the two changed functions; this one builds every page whole. The new vintage reaches the frontend build's `snapshots/extraction_versions.json`, as stated. |
| #983 | 11-12 | 27/27 | 16 (73) | 16 (BURL, CNXC, ROST, SMPL) | MISS: panel request (BURL) | 16 of 27 pages move in the guidance bridge and its rows. The panel check ran (#994) on a transform that left BURL as committed (the record: "no code rebuilds it"); BURL's own next build gains 9 same-day guide rows and its request moves in `facts` (+82 lines), which no panel check measured. 12 off-panel requests also move; the body's request compare covered the panel only. (Re-read 2026-11-13; the 2026-11-12 table read this row "as stated".) |
| #996 | 11-12 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #998 | 11-12 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #991 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 27 committed pages move"); the ledger, the scoring report and the monitor are identical. The screen it reaches (`eod/features.py`) was not run here (no `--run-screen`), so the body's own screen replay (0 of 24 names) is the only measure of it. |
| #999 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("No page, screen or synthesis request moves"). The page builds were reached by 5 `vinci/facts/` modules and 130 committed `data/facts/` files; the frontend build over them is identical (350 files). The ledger, scoring and monitor are not reached. |
| #1003 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Measured 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 27 pages move", by a function-level replay; this run builds every page whole). The extraction version moves on all 27, reported apart; the frontend build's `snapshots/extraction_versions.json` gains the vintage. |
| #1002 | 11-13 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move (measured 2026-11-13). The body says so ("No file under `vinci/` changes"). |
| #1001 | 11-13 | — | 0 (0) | 0 | as stated | Measured 2026-11-13: no `vinci/` change and no committed page input, so no page is built. The frontend build moves `scenarios/GOOGL.json` and `scenarios/GOOGL-2026-08-17.json`, as the body says, and the copy of its own edited `build.py`; the other 348 of 351 files are identical. |

**WHY.** A hand-built section measures what its author chose to measure, most often each
committed page at its own price date, or the six frozen panel pages through a transform. The
impact check builds every committed page twice, with base code and with head code, on one set of
inputs. It then compares every leaf, each page's own synthesis request and every downstream reader
the diff reaches. So it shows what the next build carries, including moves the author did not
look for. #983 is the clearest case: the panel check drew on the transform's view of BURL, and the
build's view differs.

The first pass (2026-11-11 to 11-12) measured 40 of 49. iCloud had offloaded most of the primary
checkout's `data/cache` and `.git`, and that failed six runs part-way. #984's run was clock noise,
which #1025 fixed in the tool. #1001 to #1003 had not started.

**HOW VERIFIED.**
- **The tool.** The re-runs used main's `vinci/impact/` as merged into this branch at `cebcc69b`
  (main `c0b6a519`): it includes #1025 (a kept build keyed by its UTC day) and #1031 (`build_days`
  reads `as_filed_by` only for a side with no `clock.json`). `vinci/impact/` is unchanged from
  there to main `dad8f441`.
- **The command**, per PR: `python -m vinci.impact run --base N^ --head N --out <an empty folder
  outside the repo> --store <the store> --workers 4 --skip-fail-first`, from a plain clone, with
  the primary checkout's cache and `.env` named explicitly (`--cache-root`, `--env-file`), and the
  CIQ root below (`--ciq-root`). It ran one PR at a time, and each build tree was deleted once its
  report was copied out. #940 ran on its 4 unbuilt pages only (`--ticker`).
- **The store, the same content on every row.** Every row that built pages read one store,
  content `abeee0e75c67…` over 2,543,455 rows, priced to the 2026-11-09 close; each run's snapshot
  hashes `e33d420f9f5d…`.
  - The 40 rows of 2026-11-11/12 read the old sweep's `store/vinci.db` (file sha256 `964eee22…`).
  - The re-runs read a byte copy of that file (the same sha256). The content was re-computed
    with the tool's own digest before the copy: `abeee0e75c67…`, 2,543,455 rows. The old sweep's
    `store0/` copy is different content (`814dacde…`, 2,543,322 rows) and was not used.
  - The same-code rows build nothing and read no store.
- **The CIQ inputs, the same exports on every row.** Between the two passes, IT, ORKA, PARR and
  WERN were re-exported (2026-11-12, after 23:00 IST; #1041's re-export list), and MVST's folder
  was removed (MVST retired, #1044).
  - The re-runs read a scratch root of links: 22 names to the live CIQ folder, and the 5 to the
    Drive's `ciq-archive/replaced-2026-11-12/`. Checked hash for hash against the 40 rows' stamp:
    285 exports on 27 pages, identical.
  - Two first re-runs on the live exports, #940's 4 pages and #964, are set aside. On them PARR
    was refused at both refs: its new `Financials_Quarterly.xls` is a byte copy of
    `Financials_Annual.xls` (sha256 `29debc32…` both), and production refuses it
    (`CiqMislabelledError`). They also moved nothing: #940, 3 of 4 built, 0 move; #964, 26 of 27
    built, 0 move.
- **The cache.** At 2026-11-13 ~04:20Z the SEC cache was fully local (0 of 18,757 files
  offloaded). Polygon had 1,340 of 1,589 offloaded, Tiingo 12 of 46, EFTS 44 of 113, FINRA 9 of 35,
  and facts 379 of 379. Each file was read back from iCloud; from 05:23Z 0 of 20,919 files were
  offloaded. #975, and the start of #984, ran during the last of it; neither report has a read
  error, and their consumers match.
  Every re-run read 0 responses live and refused 0 vendor pulls. No re-run needed its one allowed
  retry.
- **The reading.** Each row's "reading" comes from the PR's own body (`gh pr view <n>`), read
  beside its report. The 40 rows' readings are as #1028 carried them, except #983's (re-read in
  this pass, from "as stated" to MISS) and two status notes: #953's panel check, and #1039 on
  #956's WERN.

**BOUNDARY.**
- **Population:** the 49 fix-request-2 PRs merged with a hand-built cross-setup section, from #936
  (merged 2026-11-09) to #1003 (merged 2026-11-11), in the sweep's merge order. The merge commits
  are in #1028's body.
- **Pages:** each PR's committed pages at its head: 28 before AORT was retired in #942, and 27
  after.
- **Dates:** measured from 2026-11-11T12:51Z (#936) to 2026-11-13T06:03Z (#964), UTC; each row
  gives its own day.
- **Inputs:** the one store; the same 285 CIQ exports on every row that built pages (AORT, the
  28th page before #942, had none); and the primary checkout's `data/cache` served frozen. No
  Polygon or Tiingo pull was made.
- **Counts:**
  - "11 of 49" counts PRs whose reading is not `as stated` or `≈ as stated`;
  - "2 of them" counts PRs where a panel page's own-build request differs and no panel check
    measured it;
  - "fields" counts leaf changes, the extraction-version field set apart.
- **What was not run:** the screen consumer (`--run-screen` not passed) and the theme desk (no
  `--theme-data`), on any row; and part 1, fail first (`--skip-fail-first`), on every row.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call, and no Polygon or Tiingo pull.
- **A next build is not the committed page.** Each move lands only when its page is re-assembled.
  #966's MVST move has nowhere to land once MVST's retirement (#1044) merges.
- **The screen and the theme desk were measured by no row here.** #991 reaches the screen through
  `eod/features.py`, and its body's own screen replay (0 of 24 names) is the only measure of it.
- **The re-runs measure at the 40 rows' CIQ vintage, not today's.** That keeps the 49 rows on one
  set of inputs. A page's next build on today's exports can differ: PARR's is refused outright
  until its quarterly Financials is re-exported.

