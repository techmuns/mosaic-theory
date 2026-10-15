---
id: 2026-10-15-theme-intelligence-robots-review-fixes
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the review of the robots.txt change: three findings fixed

**WHAT.** A high-effort review of PR #713 (`docs/records/2026-10-15-theme-intelligence-robots.md`)
reported three findings on it (seven more on PR #714); operator, 2026-10-15: "fix all ten".

| Finding | Fix |
|---|---|
| **robots.txt redirects depended on the injected client.** Page fetches pass `follow_redirects=False` explicitly; the robots.txt fetch took the client's default, so with a client that does not follow, a redirected robots.txt (a 3xx) failed the host closed. | The robots.txt fetch follows redirects explicitly (RFC 9309), whatever the client's default. |
| **A group naming our agent WITH a version was not ours.** `User-agent: mosaic-theory-theme-intelligence/0.1` never equalled the product token, so its rules fell back to `*`. | The User-agent value is read as its product token, the version dropped. |
| **Every check recompiled every rule's pattern.** | Each rule's pattern is compiled once, when the file is read. |

**WHY.** One could fail a host closed for a file it may read; one could crawl a path a host
disallowed for us by name; one is repeated work on every fetch.

**HOW VERIFIED.**
- **Corpus:** the 47 cached page URLs on the 9 hosts whose robots.txt the probe saved — still **0**
  decisions changed against urllib's, 0 cross-host redirects.
- **Pins:** 3 more in `tests/test_theme_intelligence_robots.py` (18 in all): a versioned agent
  line, a redirected robots.txt with a non-following client, and the rules compiled once (a
  check that recompiles fails).
- **Mutants: 17 of 17 killed** (the change's 14, one rewritten for the new agent line, and 3 for
  these fixes).
- Ruff and `mypy --strict vinci` clean; offline suite `5315 passed, 513 skipped, 37 deselected`.

**BOUNDARY.** Code: PR #713's branch, 2026-10-15; the 47 URLs as in the change's own record.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0; no request made.
