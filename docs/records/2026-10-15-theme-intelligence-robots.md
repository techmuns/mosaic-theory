---
id: 2026-10-15-theme-intelligence-robots
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — robots.txt read per RFC 9309, and redirects checked hop by hop (O22)

**WHAT.** Operator, 2026-10-15: "go ahead with o22" — the last verified finding of the PR #703
review (`docs/records/2026-10-14-theme-intelligence-open-review-findings.md`).

| Defect | Fix |
|---|---|
| `urllib.robotparser` reads every rule as a plain prefix: `*` and `$` never match. J.P. Morgan's real file (`Disallow: /*.pdf`, `*/jcr_content/*`, `*/thank-you`) let every PDF outside `/content` through. | `fetch.RobotsRules`: the group(s) naming our product token (case-insensitive), else `*`; `*` matches any run of characters, a trailing `$` anchors the end; the longest matching rule decides and Allow wins a tie (RFC 9309 §2.2.2). Crawl-delay: our group's, else `*`'s, as before. |
| The HTTP client followed redirects itself: a redirect to another host — or to a disallowed path on the same host — was fetched without that host's robots.txt being read. | The fetcher follows a redirect ONE HOP AT A TIME (at most 5): each hop is checked against its own host's robots.txt (read, and failing closed, as for any host) and spaced like any request there. A hop that is not fetched leaves the page BLOCKED with the reason. robots.txt itself still follows redirects, as RFC 9309 asks. |

**WHY.** The tool's own rule — "Do not bypass … robots restrictions" (operator) — was enforced by a
reader that could not read the rules.

**HOW VERIFIED.**
- **Corpus:** every cached page URL on a host whose robots.txt the probe saved (2026-10-09; 7
  files, 9 hosts) — 47 of the 65 distinct cached page URLs: **0** decisions change, and **0**
  cached fetch was redirected to another host. The defect was latent in what this tool has
  fetched; it is a rule it would have broken.
- **The real J.P. Morgan file** (a fixture, line-identical to the live file re-read 2026-10-15):
  `/apac/…/outlook-2027.pdf` and `?download=1` PDFs, `…/jcr_content/…`, `…/thank-you` —
  allowed before, refused now; an article, a stylesheet, and `/content/…` (a plain prefix)
  unchanged.
- **Live, robots.txt only** (one request, the honest User-Agent, no page fetched): the fetcher now
  refuses `…/tmt/outlook.pdf` on privatebank.jpmorgan.com and allows an article page.
- **Pins:** `tests/test_theme_intelligence_robots.py`, 15 tests. Against main's reading, 11 fail;
  the 4 that pass are what main already got right (a plain prefix, an article, an Allow, our own
  group).
- **Mutants: 14 of 14 killed** (wildcard, `$`, the tie, longest-match, group choice, case of the
  agent, crawl-delay fallback, the empty Disallow, the client following redirects itself, an
  unchecked hop, the redirect limit, an unspaced hop, an uncounted hop, the old matcher).
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.** Code: main fcef226a against this branch, 2026-10-15. "65 / 47 URLs": distinct URLs of
every cached page (a `.body` beside its meta file) under the `theme-intelligence` worktree's
`data/theme_intelligence/`, and those on the 9 hosts of the 7 robots files in
`data/theme_intelligence/probe/sources/`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; 3 requests to privatebank.jpmorgan.com/robots.txt (the live check and two comparisons with
  the fixture).
- Paths are matched as the URL carries them (no percent-encoding normalisation); none of the
  probed files needs it.
