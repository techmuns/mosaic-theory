---
id: 2026-10-16-theme-intelligence-gs-markets-page-counts
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the GS-markets record's counts, re-derived with their boundaries (U40)

**WHAT.** `docs/records/2026-10-14-theme-intelligence-gs-markets-page.md` states counts with no
window, commit or BOUNDARY line (U40, verified in
`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`). Records are immutable,
so this record re-derives each count and says where it was measured. The earlier record is not
edited.

| Count as written (2026-10-14) | Re-derived here | Status |
|---|---|---|
| "deep thematic pieces, about two a month" (Goldman's Research page) | Not re-derivable. The page refuses automated reads: HTTP 403 to one fetch on 2026-10-16, and the pilot's one stored Goldman check (2026-10-12T10:14Z) is BLOCKED, HTTP 403. No Goldman listing, article or document is held: 0 of 13 articles and 0 of 9 documents in a copy of the pilot registry. | **UNVERIFIED.** It was one person's reading of the page on 2026-10-14, over a window not stated. |
| "Mutants: 2 of 2 killed" | The two mutants were not recorded, so they cannot be re-run as they were. Three mutants of the same pins were run at main 4283a3e0: Sources drops the extra pages; Uploads drops them; the config never reads `research_pages`. **3 of 3 killed**; the unmutated baseline passes (3 tests). | Re-derived, with different mutants. |
| "Goldman's two pages"; Morgan Stanley "exactly one"; "only Goldman has extra pages" | At main 4283a3e0, `sources.toml`: 6 active channels, 1 with `research_pages` (`gs_research`: `https://www.goldmansachs.com/insights/markets`). So Goldman shows 2 pages (`entry_url` plus 1) and every other channel shows 1. | Re-derived; matches. |
| "Mutants … ; the live local preview" (no count) | — | No count to re-derive. |

**WHY.** CLAUDE.md, EVERY COUNT STATES ITS BOUNDARY. A count with no window cannot be checked,
and "about two a month" reads like a measurement.

**HOW VERIFIED.**
- The pins re-run are the ones the earlier record names:
  - `tests/test_theme_intelligence_desk.py::test_sources_say_each_channels_state_in_plain_words_and_fold_the_checks_own`;
  - `…::test_uploads_link_each_requested_article_say_what_is_held_and_where_to_look`;
  - `tests/test_theme_intelligence_publishers.py::test_the_channel_policies_as_configured`.
- Each mutant was applied alone to a copy of main's tree (`git archive 4283a3e0`) and restored
  afterwards.
- The Goldman fetch was one request with the fetch tool's own client, no retry, 2026-10-16.

**BOUNDARY.**
- Code and config: main 4283a3e0, 2026-10-16.
- Pilot: a copy (SQLite backup API) of `v2/pilot-2026-10-12/registry.db` under the
  `theme-intelligence` worktree's `data/theme_intelligence/`, taken 2026-10-16. The live file's
  checksum is unchanged (5fcc240d4b087d2feb1f81e6d6fabc3c).
- The pilot's articles: every row of `articles` (13). Its documents: every row of `documents` (9).
  Its Goldman checks: every `source_health` row for `gs_research` (1).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **"About two a month" stays unverified.** Only a person can read Goldman's page. To settle it,
  the operator counts the Research page's pieces over a stated window, and the count goes in a
  record with that window.
