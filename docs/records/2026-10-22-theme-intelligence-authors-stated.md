---
id: 2026-10-22-theme-intelligence-authors-stated
status: recorded
date: 2026-10-22
prs: []
supersedes:
superseded-by:
---

# Theme intelligence: Morgan Stanley stated as author of its three unsigned web articles — QA passes on both merge runs

**WHAT.** The operator's ruling (2026-10-22: "use Morgan Stanley, merge 771 and apply it"),
applied to the registry of record. `theme-intelligence-state` moved 9939047e → **0cdebc0f**
(fast-forward, $0).

- **Three `author` runs** (#771) stated the same author on each article:
  - **Name:** "Morgan Stanley".
  - **Title:** "institution — the page names no individual author".
  - **Stated by:** nogods404 (operator).
  - **Reason:** the page names no individual author — an unsigned Morgan Stanley web article
    quoting Morgan Stanley Research analysts.
- **The runs:**
  - A-bcae0b1f5d86 (caffeine, D-a50ad278805b99cc) — R-20261022T035402Z-author;
  - A-cfc65506a485 (healthcare conference, D-f07743491474341f) — R-20261022T035403Z-author;
  - A-9faa09cf8082 (Industry 5.0, D-aabbd08f3d4f4141) — R-20261022T035404Z-author.
- **The "by" is the operator's GitHub identity**, the one PRs and pushes are made with. The
  ruling gave the name, not who to record as stating it.

**HOW VERIFIED.**
- **Rehearsed on a private bare mirror of the branch** (never origin), with main f705660a, the
  API key blanked.
- **QA's author check:**
  - R-20261021T101854Z-ingest: FAIL ("A-9faa09cf8082 (Morgan Stanley)") → PASS ("3 article(s)").
  - R-20261021T102637Z-ingest: FAIL (A-bcae0b1f5d86, A-cfc65506a485) → PASS ("5 article(s)").
- **Each author run passed QA 22/22**, including "every stated author is on its article: 1
  article(s)".
- **The commit, table by table, against 9939047e:**
  - articles: 3 records changed, now KNOWN, crediting "Morgan Stanley" with the operator-stated
    provenance;
  - documents: 3 records changed (declared authors, a history line);
  - runs: 3 added; verification issues: 3 added (AUTHORS_STATED); snapshots: 3 added (the runs'
    rendered outputs);
  - meta: the migration stamps re-minted at schema **8**. This is the first push by v8 code; the
    weekly job would do the same.
  - `review_resolutions.jsonl`: added, empty.
  - **Identical:** thesis versions (32), claim links (319), model calls (236), claims (412),
    change events (44), contributions (32), market contexts (69), enrichment sets (20).
  - No article text.
- **Pushed** only after origin's branch was confirmed still at 9939047e (a fast-forward, no
  force).

**BOUNDARY.**
- Registry `theme-intelligence-state` 9939047e → 0cdebc0f, 2026-10-22 (UTC), code main f705660a.
- Row counts are the JSONL rows of the pushed tree.
- The paid ledger is unchanged: 213 calls, $26.5690.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.**
- **Cards are not rewritten.** The cards' sealed source rows keep "author UNKNOWN" on the
  versions that recorded it, until a later version.
- **The app's desk is behind the registry.** Three new runs; the weekly report's source line
  reads the article record. It changes only on a republish.
