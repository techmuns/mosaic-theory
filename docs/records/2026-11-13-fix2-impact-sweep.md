---
id:
status: shipped
date: 2026-11-13
prs: [1028]
supersedes:
superseded-by:
---

# The fix-request-2 impact sweep, 71 PRs merged 2026-11-09 to 2026-11-13 (#936 to #1047): `vinci.impact` measured each one's next build, base code against head code at $0. 12 moved something their own body did not state; one panel check is owed and has not run (#953's), and #983's BURL move waits on its result

**WHAT.** The operator asked on 2026-11-11 for the cross-setup check (RUNBOOKS §o) to run on every
fix-request-2 PR merged with a hand-built section, from #936 ("Yes, run the sweep"). On 2026-11-13
the operator said "go ahead with the #1028 re-runs". The coordinator's review of the first draft
(2026-11-13) found the first pass's list of 49 incomplete, so the population is now derived by a
stated query (HOW VERIFIED). For each PR, with `N` its merge commit on main, the sweep ran
`python -m vinci.impact run --base N^ --head N --skip-fail-first` and read the report beside the
PR's own title and body.

- **The population: 71 PRs.** The query keeps 69; 47 of them are the first pass's, and 22 are new.
  The first pass also measured #942 (AORT retired) and #984 (GOOGL's void). Neither names fix
  request 2 nor is cited in the fix log, so the query leaves them out; they stay, as measured.
- **12 of 71 PRs moved something their body did not state** (the "reading" column):
  - **7 MISS**, a move the body denied or did not mention: #936, #944, #948, #953, #956, #966 and
    #983;
  - **4 a wider move than the body counted:**
    - #960 (`count`): 27 pages, not 13;
    - #962 (`count`): 29 notes on 9 pages, not 28 on 10;
    - #965 (`count`): 18 pages, not 5;
    - #981 (`coverage`): it built 17 of 27, and the other 10 move too;
  - **1 CORRECTION**, #976: its body said NFLX's and VITL's requests move; 0 of 27 do. WERN's +2
    release notes are not stated.
- **Panel pages' requests moved, in their `facts` section only, under 2 of them.** The operator's
  ruling in bookkeeping batch 3 (item 2): a FACTS-only request move needs no paid panel by default
  ("Not needed; #953 is the test (Recommended)"), and #953's retrospective panel run is that
  ruling's falsifier.
  - **#953: owed.** It moves on BURL, CNXC, MCK, ROST and SMPL (23 of 27 requests move). Its run
    is approved ("Run it now, $35 cap (Recommended)") and was to run once order 8 merged. Order 8
    merged on 2026-11-12 (#1030); on main at `12764514` the run has not happened.
  - **#983 on BURL: not owed by default.** It is an operator question that waits on #953's result.
    Its panel check (#994) drew on a transform that left BURL as committed, because "BURL's
    committed guidance predates A-D8's block discovery, so no code rebuilds it". A build does
    rebuild it: BURL's next build gains 9 same-day guide rows, and its request moves in `facts`
    (82 lines added).
  - Nothing was spent on either.
- **59 of 71 move only what their body states, as far as this sweep measures.** The screen (reached
  statically by 31 rows) and the theme desk (by 30) were run on no row. So "as stated" covers
  pages, requests, renders, and the ledger, scoring report and monitor where reached. #987 and
  #1007 reach only the theme desk, so nothing they reach was measured.
- **The 33 runs of 2026-11-13 move nothing.** That is the 11 the first pass could not finish
  (#940's 4 pages, #964, #975, #984, #986, #991, #995, #999, #1001, #1002, #1003) and the 22 new
  PRs. On each, 0 pages and 0 requests move. #984's 5 pages moved on 2026-11-12 on the build day
  alone; with #1025's tool they do not.
- **Corrections, as appended amendments** (operator ruling 3, 2026-11-12, verbatim: "Yes, as
  appended amendments (Recommended)"; #1029 is the precedent). #1029 amended the records of #953,
  #956, #960, #965 and #976. This PR amends five more, each with one dated entry and no body
  rewritten:
  - #936 (`2026-11-09-fix2-order2-customer-count-surprise-listing-containing-headline.md`);
  - #944 (`2026-11-09-fix2-e1-asof-reach-and-amendments.md`);
  - #948 (`2026-11-10-fix2-e1-an-8ka-hit-is-an-8ka.md`);
  - #966 (`2026-11-10-fix2-e2-a-going-concern-denial-is-not-doubt.md`);
  - #983 (`2026-11-11-fix2-ra-d4-same-day-guides.md`).
  #981's record already names its 10 extra pages, in its own amendment of 2026-11-11.
- **The pages behind three counts**, each at its page's next build (MVST is now retired, #1044):
  - **#960, the bridge note, 27:** AMZN, BRBR, BURL, CNXC, EPAM, FUBO, GOOGL, IT, LLY, MCK, MVST, NCNO,
    NFLX, NKE, ORKA, PARR, ROST, SMPL, TECX, TGT, TJX, UBER, V, VITL, VRRM, WERN and WLK;
  - **#965, `qa_flags`, 18:** BRBR, BURL, CNXC, EPAM, IT, MCK, MVST, NCNO, NFLX, NKE, PARR, ROST, TGT,
    TJX, VITL, VRRM, WERN and WLK (88 field changes, 44 flags out and 44 in);
  - **#962, release notes, 29 on 9:** BRBR 2, BURL 2, EPAM 3, FUBO 1, MVST 8, SMPL 8, TGT 2, TJX 1
    and VITL 2. The body's "BRBR 2, BURL 2, EPAM 3, FUBO 1, MVST 5, SMPL 8, TGT 2, TJX 1, VITL 2,
    WERN 2" is right on the other 8 pages.

"Pages move" means base code against head code on the same inputs: the page's NEXT build, not the
committed page. "Requests move (on panel)" counts pages whose own build's synthesis request differs,
and names the panel pages among them. The six panel pages' frozen replay (each held at its frozen
blob) was identical in all 42 row reports that ran it. Under "built":
- **"—":** base and head carry the same `vinci/` tree and frontend source (same code), so nothing is
  built;
- **"not reached":** `vinci/` or frontend source changes, but no page builder reaches the change, so
  no page is built. The row names the consumers it reaches.

| PR | merged (UTC) | measured (UTC) | built | pages move (fields) | requests move (on panel) | reading | what the measurement adds to the body |
|---|---|---|---|---|---|---|---|
| #936 | 11-09 17:43 | 11-11 | 28/28 | 25 (29) | 1 | MISS: request | PARR's request moves in `facts` (its surprise history, RA-D1). Body: "All 28 synthesis requests are byte-identical", but that compare held the committed page fixed. Off the panel. Pages: 25 move on the customer count, as stated. |
| #938 | 11-10 03:16 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #937 | 11-10 03:18 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #939 | 11-10 04:35 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #946 | 11-10 04:37 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #945 | 11-10 04:38 | 11-11 | 28/28 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #942 | 11-10 06:15 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #940 | 11-10 06:48 | 11-11, 11-13 | 27/27 | 0 (0) | 0 | as stated | 23 pages built 2026-11-11, and the 4 the environment stopped (NFLX, PARR, ROST, SMPL) built 2026-11-13: 0 of 27 pages and 0 requests move, as the PR's title says ("0 of 28 pages move"). The extraction version moves, reported apart. |
| #943 | 11-10 07:31 | 11-11 | 27/27 | 0 (0) | 0 | as stated | Monitor output gains `realized_price_return` (RF-D3). |
| #948 | 11-10 07:32 | 11-11 | 27/27 | 1 (1) | 1 | MISS: request | WERN's pointer row moves, as stated; WERN's request ALSO moves in `facts`, and the body says nothing about requests. Off the panel. |
| #947 | 11-10 08:30 | 11-11 | not reached | 0 (0) | 0 | as stated | `vinci/` changes, but no page builder reaches it, so no page is built. The ledger, scoring report and monitor it reaches are identical; the screen it reaches was not run. |
| #944 | 11-10 08:31 | 11-11 | 27/27 | 1 (1) | 1 | MISS: page + request | PARR's cadence "37 results 8-Ks" → "38" at the same inputs, and PARR's request moves in `facts`. The PR's title: "0 of 28 pages move" (true of each page at its own price date; this is its next build). Off the panel. |
| #949 | 11-10 08:42 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #954 | 11-10 10:21 | 11-11 | 27/27 | 0 (0) | 0 | as stated | Decision-ledger stdout adds "0 correction(s)", which is the PR's purpose. |
| #941 | 11-10 10:51 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #951 | 11-10 11:17 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #953 | 11-10 11:41 | 11-11 | 27/27 | 27 (488) | 23 (BURL, CNXC, MCK, ROST, SMPL) | MISS: panel request | 23 requests move in `facts`, 5 of them on the panel (BURL, CNXC, MCK, ROST, SMPL). Body: byte-identical, from the frozen replay. No panel check yet: it waited on order 8, which merged 2026-11-12 (#1030); on main at 2026-11-13 the run has not happened. |
| #955 | 11-10 12:40 | 11-11 | not reached | 0 (0) | 0 | as stated | `vinci/` changes, but no page builder reaches it, so no page is built. The decision ledger it reaches is identical. |
| #964 | 11-10 16:47 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says (its fix-log table's "Pages rebuilt" cell reads "none"). The head scoring report that refused an offloaded cache file on 2026-11-11 now runs, identical at both refs. |
| #958 | 11-10 16:50 | 11-13 | not reached | 0 (0) | 0 | as stated | `vinci/evals/` changes, and no page builder or consumer reaches it, so nothing is built; the title says "harness only". |
| #956 | 11-10 17:29 | 11-11 | 27/27 | 2 (14) | 2 | MISS: page + request | MVST and WERN: the maturity wall goes from located to not_stated (7 fields each); both requests move in `primary_source`. Body: "0 of 27 pages move", "No synthesis request changes". MVST's committed page still said located, so it would move at its next assembly; WERN's committed page already says not_stated. Off the panel. Since then #1039 (merged 2026-11-13) fixes WERN's as #956's regression, and MVST is retired (#1044, merged 2026-11-13 as `12764514`), so its page has no next build. |
| #962 | 11-10 18:00 | 11-11 | 27/27 | 9 (29) | 0 | count | 29 release-note moves on 9 pages at a fresh build. The body states 28 notes on 10 pages ("BRBR 2, BURL 2, EPAM 3, FUBO 1, MVST 5, SMPL 8, TGT 2, TJX 1, VITL 2, WERN 2"); measured, MVST gains 8 and WERN 0, the other 8 pages as stated. Not sent: 0 requests, as stated. |
| #966 | 11-10 18:29 | 11-11 | 27/27 | 1 (2) | 1 | MISS: page + request | MVST's going-concern quote changes (2 fields) and MVST's request moves in `primary_source`. Body: "no committed page moves". Off the panel. |
| #957 | 11-10 19:49 | 11-11 | 27/27 | 2 (2) | 0 | as stated | ORKA and TECX gain a consensus note (in NOT_SENT): 0 requests. |
| #969 | 11-10 20:12 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #960 | 11-10 20:38 | 11-11 | 27/27 | 27 (29) | 0 | count | All 27 pages' `ev_bridge.note` move at a fresh build, plus 2 exit reasons; the body says 13 bridges. Outside the request: 0 move, as stated. |
| #963 | 11-10 21:06 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #965 | 11-10 21:51 | 11-11 | 27/27 | 18 (88) | 0 | count | 18 pages' `qa_flags` move at a fresh build (44 out, 44 in); the body names 5 committed pages. Not sent: 0 requests, as stated. |
| #977 | 11-11 02:36 | 11-13 | — | 0 (0) | 0 | as stated | Same code: bookkeeping, no `vinci/` or frontend source change, so nothing can move. |
| #974 | 11-11 02:40 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #975 | 11-11 02:42 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("no page moves and no synthesis request changes"). The extraction version moves on all 27, reported apart. |
| #976 | 11-11 03:35 | 11-11 | 27/27 | 7 (38) | 0 | CORRECTION | 0 of 27 requests move; the body said NFLX's and VITL's do, but caveats are never sent. Notes: NFLX +3 and VITL +2, as stated; WERN +2 not stated (a newer release). |
| #980 | 11-11 04:15 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #961 | 11-11 04:46 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #970 | 11-11 05:05 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #988 | 11-11 06:48 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #989 | 11-11 06:51 | 11-13 | — | 0 (0) | 0 | as stated | Same code: bookkeeping, no `vinci/` or frontend source change, so nothing can move. |
| #990 | 11-11 07:09 | 11-13 | — | 0 (0) | 0 | as stated | Same code: a panel check's record, no `vinci/` or frontend source change, so nothing can move. |
| #982 | 11-11 07:11 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Measured 2026-11-13: the whole-page build the body did not run ("A $0 BUILD of every page is not run for this PR"): 0 of 27 pages and 0 requests move, as its proposal compare found. The ledger, scoring report and monitor are identical; the frontend build's `snapshots/extraction_versions.json` gains the vintage. |
| #985 | 11-11 07:11 | 11-13 | — | 0 (0) | 0 | as stated | Same code: a panel check's record, no `vinci/` or frontend source change, so nothing can move. |
| #993 | 11-11 07:54 | 11-11 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #981 | 11-11 08:10 | 11-11 | 27/27 | 27 (604) | 27 (BURL, CNXC, LLY, MCK, ROST, SMPL) | coverage | Built 27 of 27; the body built 17 (10 had no bars). Those 10 also move, and so do their requests: GOOGL, NFLX, TGT, TJX, UBER and V off the panel; BURL, LLY, MCK and ROST on it. The panel check ran (#985). |
| #992 | 11-11 08:17 | 11-11 | 27/27 | 0 (0) | 0 | as stated | 0 move, as the body says. |
| #987 | 11-11 08:18 | 11-11 | not reached | 0 (0) | 0 | as stated | `vinci/` changes, but no page builder reaches it, so no page is built. Its one reached consumer, the theme desk, was not run (no `--theme-data`), so nothing it reaches was measured. |
| #986 | 11-11 08:22 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 13,986 values move on 27 pages"). The extraction version moves on all 27, reported apart; the frontend build's git-ignored `snapshots/extraction_versions.json` gains the new vintage, as #988 designed. |
| #984 | 11-11 08:34 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13 with #1025's tool: the 5 pages that moved on the build day alone (BRBR, BURL, CNXC, EPAM, FUBO) no longer move; 0 pages and 0 requests, as the body says. `vinci ledger`'s summary line gains "0 void(s)", which is the PR's purpose. |
| #994 | 11-11 08:59 | 11-13 | — | 0 (0) | 0 | as stated | Same code: a panel check's record, no `vinci/` or frontend source change, so nothing can move. |
| #995 | 11-11 09:11 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 27 pages move"; no request "at re-assembly either"). The body's compare ran the two changed functions; this one builds every page whole. The new vintage reaches the frontend build's `snapshots/extraction_versions.json`, as stated. |
| #983 | 11-11 09:48 | 11-12 | 27/27 | 16 (73) | 16 (BURL, CNXC, ROST, SMPL) | MISS: panel request (BURL) | 16 of 27 pages move in the guidance bridge and its rows. The panel check ran (#994) on a transform that left BURL as committed (the record: "no code rebuilds it"); BURL's own next build gains 9 same-day guide rows and its request moves in `facts` (+82 lines), which no panel check measured. 12 off-panel requests also move; the body's request compare covered the panel only. (Re-read 2026-11-13; the 2026-11-12 table read this row "as stated".) |
| #996 | 11-11 09:52 | 11-12 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #998 | 11-11 10:26 | 11-12 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move. |
| #991 | 11-11 10:44 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 27 committed pages move"); the ledger, the scoring report and the monitor are identical. The screen it reaches (`eod/features.py`) was not run here (no `--run-screen`), so the body's own screen replay (0 of 24 names) is the only measure of it. |
| #999 | 11-11 10:45 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Re-run 2026-11-13: 0 pages and 0 requests move, as the body says ("No page, screen or synthesis request moves"). The page builds were reached by 5 `vinci/facts/` modules and 130 committed `data/facts/` files; the frontend build over them is identical (350 files). The ledger, scoring and monitor are not reached. |
| #1003 | 11-11 11:27 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Measured 2026-11-13: 0 pages and 0 requests move, as the PR's title says ("0 of 27 pages move"; its compare was a function-level replay, and this run builds every page whole). The extraction version moves on all 27, reported apart; the frontend build's `snapshots/extraction_versions.json` gains the vintage. |
| #1002 | 11-11 11:30 | 11-13 | — | 0 (0) | 0 | as stated | Same code: the `vinci/` tree and frontend source are unchanged, so nothing can move (measured 2026-11-13). The body says so ("No file under `vinci/` changes"). |
| #1001 | 11-11 11:38 | 11-13 | not reached | 0 (0) | 0 | as stated | Measured 2026-11-13: no `vinci/` change and no committed page input, so no page is built. The frontend build moves `scenarios/GOOGL.json` and `scenarios/GOOGL-2026-08-17.json`, as the body says, and the copy of its own edited `build.py`; the other 348 of 351 files are identical. |
| #1008 | 11-11 12:50 | 11-13 | — | 0 (0) | 0 | as stated | Same code: artifact-only (the committed ledger gains `X-GOOGL`, as the body says); with one `vinci/` tree, nothing the code builds can move. |
| #971 | 11-11 12:59 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Measured 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 27 pages move"); the ledger, scoring report and monitor are identical. The extraction version moves on all 27, reported apart. |
| #1011 | 11-11 13:13 | 11-13 | — | 0 (0) | 0 | as stated | Same code: bookkeeping, no `vinci/` or frontend source change, so nothing can move. |
| #1009 | 11-11 13:15 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Measured 2026-11-13: 0 pages and 0 requests move, as the body says ("No code path, page or synthesis request moves"); the ledger, scoring report and monitor are identical. |
| #972 | 11-11 13:33 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Measured 2026-11-13: 0 pages and 0 requests move, as the body says ("0 of 27 pages move"); the ledger, scoring report and monitor are identical. The extraction version moves on all 27, reported apart. |
| #1012 | 11-11 14:21 | 11-13 | — | 0 (0) | 0 | as stated | Same code: a records lint and record status flips, no `vinci/` or frontend source change, so nothing can move. |
| #1006 | 11-11 15:32 | 11-13 | 27/27 | 0 (0) | 0 | as stated | Measured 2026-11-13: 0 pages and 0 requests move beyond the extraction version, as the body says ("No other value moves"). The 25 committed pages it rewrote (all but ORKA and TECX) carry no transcript words, and base code cannot read them back (its schema requires the words), so only head's code renders them: the change the body describes. The ledger, scoring report and monitor are identical. |
| #1017 | 11-11 17:44 | 11-13 | — | 0 (0) | 0 | as stated | Same code: a stream's record and STATE re-scope, no `vinci/` or frontend source change, so nothing can move. |
| #1013 | 11-11 17:58 | 11-13 | — | 0 (0) | 0 | as stated | Same code: bookkeeping, no `vinci/` or frontend source change, so nothing can move. |
| #1007 | 11-12 03:32 | 11-13 | not reached | 0 (0) | 0 | as stated | `vinci/theme_intelligence/` changes, and no page builder reaches it, so no page is built. Its one reached consumer, the theme desk, was not run (no `--theme-data`), so the title's "0 of 696 stored claims move" is not re-measured here. |
| #1021 | 11-12 11:08 | 11-13 | — | 0 (0) | 0 | as stated | Same code: bookkeeping, no `vinci/` or frontend source change, so nothing can move. |
| #1029 | 11-12 11:36 | 11-13 | — | 0 (0) | 0 | as stated | Same code: five appended record amendments, as the body says ("Docs only"); nothing can move. |
| #1033 | 11-12 15:19 | 11-13 | — | 0 (0) | 0 | as stated | Same code: bookkeeping, no `vinci/` or frontend source change, so nothing can move. |
| #1043 | 11-13 04:08 | 11-13 | — | 0 (0) | 0 | as stated | Same code: a design record, no `vinci/` or frontend source change, so nothing can move. |
| #1047 | 11-13 06:05 | 11-13 | — | 0 (0) | 0 | as stated | Same code: bookkeeping, no `vinci/` or frontend source change, so nothing can move. |

**WHY.** A hand-built section measures what its author chose to measure, most often each
committed page at its own price date, or the six frozen panel pages through a transform. The
impact check builds every committed page twice, with base code and with head code, on one set of
inputs. It then compares every leaf, each page's own synthesis request and every downstream reader
the diff reaches. So it shows what the next build carries, including moves the author did not look
for. #983 is the clearest case: the panel check drew on the transform's view of BURL, and the
build's view differs.

The first pass (2026-11-11 to 11-12) measured 40 of its 49. iCloud had offloaded most of the
primary checkout's `data/cache` and `.git`, and that failed six runs part-way. #984's run was clock
noise, which #1025 fixed in the tool. Three had not started.

**HOW VERIFIED.**
- **The population query.**
  - **The source:** `gh pr list --repo techmuns/mosaic-theory --state merged --search
    "merged:>=2026-11-08" --limit 300 --json number,title,body,mergedAt,mergeCommit` (116 PRs).
  - **A PR is kept when all three hold:**
    1. it merged at or after #936's merge (2026-11-09T17:43:03Z) and at or before main `12764514`
       (#1044, 2026-11-13T07:00:39Z);
    2. it is fix-request-2 work: its title or body matches `fix[ -]request[ -]2` (any case), or
       `docs/fix-log-teamnostra-2.md` at `12764514` cites its number;
    3. its validation is hand-built: its body carries no section written by `vinci.impact run`.
       That is, neither the tool's stamp line (`python -m vinci.impact run --base …` followed by
       "$0 (no model call)"), nor its `### 2. Pages — built` heading, nor a cross-setup heading
       followed by that command.
  - **What it found:** 108 PRs merged in the window, 86 of them fix-request-2 work. 17 of those were
    tool-written: #1000, #1014, #1016, #1019, #1020, #1023, #1024, #1025, #1026, #1030, #1032, #1034,
    #1036, #1038, #1039, #1042 and #1044. That leaves 69.
  - **A PR with no validation section at all counts as hand-built:** its body measured nothing, so
    whatever moves is unstated.
  - **Bodies merged before #980 name the section differently** ("$0 page compare", "The $0 compare
    on the 27 committed pages"). The "Cross-setup validation" heading first appears on #980.
  - **Outside the lower cut:** #932 and #934 merged before #936. The operator's ask starts at #936.
- **The tool.** Main `c0b6a519`'s `vinci/impact/`. It includes #1025 (a kept build keyed by its UTC
  day) and #1031 (`build_days` reads `as_filed_by` only for a side with no `clock.json`), and it is
  unchanged through main `b207c8a9`.
- **The command**, per PR: `python -m vinci.impact run --base N^ --head N --out <an empty folder
  outside the repo> --store <the store> --workers 4 --skip-fail-first`, from a plain clone, with the
  primary checkout's cache and `.env` named explicitly (`--cache-root`, `--env-file`), and the CIQ
  root below (`--ciq-root`).
  - One PR ran at a time, and each build tree was deleted once its report was copied out.
  - #940 ran on its 4 unbuilt pages only (`--ticker`).
  - #1039, tool-written and outside the population, was started by the run list and stopped before
    it built anything; it is not a row.
- **The store, the same content on every row that built pages:** content `abeee0e75c67…` over
  2,543,455 rows, priced to the 2026-11-09 close; each run's snapshot hashes `e33d420f9f5d…`.
  - The first pass read the old sweep's `store/vinci.db` (file sha256 `964eee22…`).
  - The 2026-11-13 runs read a byte copy of that file (the same sha256). The content was
    re-computed with the tool's own digest before use. The old sweep's `store0/` copy is different
    content (`814dacde…`, 2,543,322 rows) and was not used.
  - Same-code rows build nothing and read no store.
- **The CIQ inputs, the same 285 exports on every row that built pages.** Between the passes, IT,
  ORKA, PARR and WERN were re-exported (2026-11-12, after 23:00 IST; #1041's re-export list), and
  MVST's folder was removed.
  - The 2026-11-13 runs read a scratch root of links: 22 names to the live CIQ folder, and the 5 to
    the Drive's `ciq-archive/replaced-2026-11-12/`. It was checked hash for hash against the first
    pass's stamp: identical.
  - Two first re-runs on the live exports (#940's 4 pages, and #964) are set aside. On them PARR
    was refused at both refs: its new `Financials_Quarterly.xls` is a byte copy of
    `Financials_Annual.xls` (sha256 `29debc32…` both), and production refuses it
    (`CiqMislabelledError`). They also moved nothing.
- **The cache.**
  - At 2026-11-13 ~04:20Z the SEC cache was fully local (0 of 18,757 files offloaded). Polygon had
    1,340 of 1,589 offloaded, Tiingo 12 of 46, EFTS 44 of 113, FINRA 9 of 35, and facts 379 of 379.
  - Each file was read back from iCloud. From 05:23Z, 0 of 20,919 files were offloaded. #975, and
    the start of #984, ran during the last of it; neither report has a read error, and their
    consumers match.
  - Every 2026-11-13 run read 0 responses live and refused 0 vendor pulls. None needed its one
    allowed retry.
- **The reading.** Each row's "reading" comes from the PR's own title and body (`gh pr view <n>`),
  read beside its report.
  - The first pass's readings are as #1028 carried them, except: #983 (re-read, from "as stated" to
    MISS); #962 (from "≈ as stated" to `count`, per the review); the four quotes the review found
    were the title's or a table cell's (#940, #944, #964, #1003); and status notes on #953 and #956.
  - Every quote a row attributes to a body or a title was checked against that text: 19 of 19
    match.

**BOUNDARY.**
- **Population:** the 71 PRs above, merged 2026-11-09T17:43Z (#936) to 2026-11-13T06:05Z (#1047),
  inside the cut at main `12764514`.
- **Pages:** each PR's committed pages at its head: 28 before AORT was retired in #942, and 27
  after.
- **Dates:** measured from 2026-11-11T12:51Z (#936) to 2026-11-13T08:29Z (#1047), UTC; each row
  gives its merge time and its measuring day.
- **Inputs:** the one store; the same 285 CIQ exports on every row that built pages (AORT, the 28th
  page before #942, had none); and the primary checkout's `data/cache`, served frozen. No Polygon
  or Tiingo pull was made.
- **Counts:**
  - "12 of 71" counts PRs whose reading is not `as stated`;
  - "panel pages' requests moved under 2" counts PRs where a panel page's own-build request
    differs;
  - "fields" counts leaf changes, the extraction-version field set apart;
  - "reached statically" counts reports whose consumer list names the screen (31) or the theme
    desk (30) as reached.
- **What was not run, on any row:** the screen (`--run-screen` not passed), the theme desk (no
  `--theme-data`), and part 1, fail first (`--skip-fail-first`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call, and no Polygon or Tiingo pull.
- **A next build is not the committed page.** Each move lands only when its page is re-assembled.
  MVST is retired (#1044, merged 2026-11-13 as `12764514`), so #956's and #966's MVST moves have no
  next build to land in.
- **The screen and the theme desk are measured by no row.** 31 rows reach the screen statically
  (#986's body says it reaches "screen G3", and #991's own screen replay of 0 of 24 names is the
  only measure of one), and 30 reach the theme desk.
- **The 2026-11-13 runs measure at the first pass's CIQ vintage, not today's.** That keeps every
  row on one set of inputs. A page's next build on today's exports can differ: PARR's is refused
  outright until its quarterly Financials is re-exported.
- **The population is a text query.** A PR that does fix-request-2 work without naming it, and that
  the fix log does not cite, is missed. The query reproduces 47 of the first pass's 49, and the
  other 2 are kept by hand (#942, #984).

