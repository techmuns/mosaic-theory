---
id: 2026-10-21-theme-intelligence-beijing-readded
status: recorded
date: 2026-10-21
prs: [764]
supersedes:
superseded-by:
---

# Theme intelligence: the SemiAnalysis Beijing piece the one-registry merge left held is re-added as its own article, and the desk republished

**WHAT.** Operator, 2026-10-21: "re-add the stored preview and republish". This followed their
supplying a new copy of the piece.
- **The re-add.** The stored copy of SemiAnalysis's "Beijing Will Not Pace the Frontier: China's
  Speed-First AI Safety Regime" (8 Oct 2026, D-7eb518c393c30b6a) is re-added as its own article,
  A-5bfa8fff567e.
  - It mirrors `ingest-file --release D-7eb518c393c30b6a --as-new --as-of 2026-10-13`: the stored
    copy, under its RECORDED declaration (SemiAnalysis, the newsletter URL, the operator's
    2026-10-13 licence statement).
  - The run is marked as the replay it is (`replay_of` R-20261013T155548Z-ingest, the pilot run
    that first read it), so it joins the week its as-of falls in (`report.follows`).
  - Run R-20261021T123003Z-ingest, **$1.453**. A $0 `market` re-priced every active thesis.
- **The registry** is now `theme-intelligence-state` ddf4f8b7 → **9939047e**: 16 articles,
  30 theses.
- **The desk** is republished from run R-20261021T123639Z-market, rendered by main 06c9a5ed.

**WHY IT WAS HELD.**
- On 2026-10-13 the pilot recorded the upload as the same article as A-5bfa8fff567e, the pilot's
  automatic read of the same post (`--same-as`).
- The one-registry merge (#759) carried the pilot's supplied documents, not its automatically
  fetched articles. On replay the link named an article the registry did not hold: "REVIEW:
  --same-as A-5bfa8fff567e: no such article", and nothing was linked.
- It was the only one of the 9 documents with such a link.
- The hold was the merge's doing, not the document's. The record
  `docs/records/2026-10-21-theme-intelligence-one-registry.md` read it as an open review item.

**THE COPY THE OPERATOR SUPPLIED WAS NOT USED.**
- It is the same free preview (sha256 ed0797c3…, 19 pages), saved later: the texts are 99.65%
  identical.
- The only differences are the like count (113 → 130) and the missing paywall footer. The new copy
  ends at "…We explore these below.", just before "This post is for paid subscribers".
- That footer is what tells the reader the copy is a preview, and the new copy lacks it. Read
  alone, it would have passed as the full post.
- Both copies are clipped at the right margin IN THE TEXT LAYER ("published an essay arg…"), not
  only on screen.

**WHAT IT PRODUCED.**
- **Read as a preview only** (PARTIAL), as before: 4,698 words, 93 of 98 figures captured.
- **No thesis of its own.**
  - Under today's rules its evidence attaches to TH-38CA111885 ("Open models catch up to frontier
    faster each era, risking model-layer commoditization"): 19 new claims and 2 contradicting.
    That made version 2, and the Articles screen reads it as evidence against that thesis.
  - The pilot's own thesis from it, TH-2651327A9B ("China's frontier-safety governance is decided
    by leadership, not experts"), stays retired.
- **The desk opens on** "Week of 12–21 Oct 2026 · with research re-read after the scan": 16
  articles, 22 rows, 5 Research Now. "Held — match uncertain" is gone.
- **TH-38CA111885 v2** shows its version-1 company proposals, labelled as such ("version 1; the
  card is now version 2"), so no re-enrichment was paid for.

**HOW VERIFIED.**
- **The two PDFs**, by their text layers: 28,749 vs 28,950 characters; 3 differences, as above.
- **The working copy** came from the state branch through the private mirror. The push was
  registry JSONL only, a fast-forward from ddf4f8b7, made after checking that no weekly run was
  in progress.
- **QA of the re-add run: 17/20.** The 3 failures:
  - open research: 5 figures, 1 block, likely the clipped text;
  - no rendered cards, because a replay renders none.
- **A check against the code change made mid-run.** Main moved to 06c9a5ed during the $0 refresh
  (#762, TJX dossier code and data). No thesis, price context or proposal in the registry names
  TJX, so the refresh read nothing it changed.
- **The publication:**
  - the manifest equals the folder; 0 broken links; no local path;
  - 14 retired carried forward;
  - `publish --check`: current.
- **The app, in the browser pane:** the Articles screen lists the piece as "Partial — preview
  only … evidence against … 93 of 98 figures captured", with 2 weeks and no console error.
- **Suite** on the published files: 6,138 passed / 525 skipped (main 06c9a5ed).

**BOUNDARY.** Registry 9939047e (16 articles, 9 documents, 30 theses). Desk rendered by main
06c9a5ed on 2026-10-21. The publication changes 100 files: no file added or removed, `index.json`
included.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$1.453** for the re-add, within the $1–1.50 quoted.
- **The full paid post is still unread.** A full copy needs a clean save (fit to width) and the
  operator's call on reading paid SemiAnalysis posts in full; today that publisher is "preview
  only" by their ruling.
- **The 5 open figures** are likely the clipped words at line ends. A clean save would close them.
