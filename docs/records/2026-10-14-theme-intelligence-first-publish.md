---
id: 2026-10-14-theme-intelligence-first-publish
status: recorded
date: 2026-10-14
prs: []
supersedes:
superseded-by:
---

# Artifact pass: the research desk's first publication into the app

**WHAT.** After PR #703 merged (e7e49a13), the pilot registry's latest run is published into the
app's Theme intelligence section. The command was `publish` (code at origin/main e7e49a13): run
`R-20261014T110419Z-reanalyse`, 23 theses, 80 files (4.1 MB) under `frontend/theme-intelligence/`.
Artifact-only, as CLAUDE.md requires: no code in the commit.

**WHY.** Until a publication is committed, the deployed section reads "No theme-intelligence run
is published yet" (handled since O19). This was the operator's plan: "After merge: publish the
current snapshot". Commitability is the operator decision of 2026-10-13 (CLAUDE.md, theme
intelligence: derived analysis with short verbatim source quotes, internal use on the authed
deploy).

**HOW VERIFIED.**
- **The registry is untouched:** the pilot registry's checksum is the same before and after the
  publish.
- **Leak check** (publish's own, plus a scan of the site):
  - no local path, registry file name or key text;
  - no test-domain article (publish refuses one).
- **Licence check — how much of each source appears verbatim:** the 15 article versions held, by
  sentences over 40 characters.
  - The longest quoted span is 385 characters; there are 1,538 quotes.
  - Cumulatively, the most-quoted article has **25.9%** of its sentence text verbatim on the
    site (18 of 62 sentences); the next ones are 23.3%, 21.7% and 19.9%.
  - Each quote is short. **The cumulative share is the operator's call**, said here and in the
    PR rather than assumed.
- **ARTIFACT-PASS RULE:** the full offline suite passes with the publication in place (the
  result is in the PR).

**BOUNDARY.**
- Pilot registry `data/theme_intelligence/v2/pilot-2026-10-12` (the `theme-intelligence`
  worktree), read 2026-10-14.
- "Verbatim share": per article version, the characters of its sentences (over 40 characters)
  found whole in the published pages' text, over all its sentences' characters.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **No state branch exists yet** (`theme-intelligence-state` is absent on origin). The pilot is
  therefore the only registry this could be published from; a later publication should come from
  the registry of record once one exists.
- **Not re-checked in a browser this time:** the local preview server was stopped. The pages are
  what the merged code renders, and the in-app rendering of this code was verified on
  2026-10-14.
