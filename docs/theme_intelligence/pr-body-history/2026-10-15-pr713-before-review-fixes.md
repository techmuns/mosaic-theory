Fixes O22, the last open verified finding from the techmuns/mosaic-theory#703 review. Operator, 2026-10-15: "go ahead with o22".

This tool's own rule is "Do not bypass … robots restrictions". It was enforced by a robots.txt reader that could not read wildcard rules, and by an HTTP client that followed redirects without checking the target's robots.txt.

## What changes
| Before | After |
|---|---|
| `urllib.robotparser` reads every rule as a plain prefix, so `*` and `$` never match. Under J.P. Morgan's real file (`Disallow: /*.pdf`, `*/jcr_content/*`, `*/thank-you`), every PDF outside `/content` was allowed. | A new `fetch.RobotsRules` reader follows RFC 9309 §2.2.2: <br>• it takes the group(s) naming our product token (case-insensitive), else the `*` group; <br>• `*` matches any run of characters, and a trailing `$` anchors the end; <br>• the longest matching rule decides, and Allow wins a tie. <br>Crawl-delay works as before: our group's, else `*`'s. |
| The HTTP client followed redirects itself. A redirect to another host, or to a disallowed path on the same host, was fetched without that host's robots.txt being read. | Redirects are followed one hop at a time, at most 5. Each hop is checked against its own host's robots.txt (which fails closed, as for any host) and spaced like any request there. A hop that isn't fetched leaves the page BLOCKED, with the reason. robots.txt itself still follows redirects, as RFC 9309 asks. |

## Verification
- **Cached pages:** I checked every cached page URL on a host whose robots.txt the 2026-10-09 probe saved: 47 of the 65 distinct cached page URLs, across 9 hosts and 7 files.
  - **0** decisions change.
  - **0** cached fetches were redirected to another host.
  - So the defect never affected anything this tool has fetched. It was a rule the tool would have broken.
- **The real J.P. Morgan file**, kept as a fixture; it matches the live file line for line.
  - **Now refused** (allowed before): `/apac/…/outlook-2027.pdf`, `…x.pdf?download=1`, `…/jcr_content/…`, `…/thank-you`.
  - **Unchanged:** an article, a stylesheet, and `/content/…` (a plain prefix).
- **Live check, robots.txt only:** one request with the honest User-Agent; no page was fetched. The fetcher now refuses `…/tmt/outlook.pdf` on privatebank.jpmorgan.com and allows an article page.
- **Tests:** `tests/test_theme_intelligence_robots.py`, 15 tests.
  - Against main's reading, 11 fail.
  - The 4 that pass are behaviour main already got right: a plain prefix, an article, an Allow, and our own user-agent group.
- **Mutation check:** 14 of 14 mutants killed:
  - `*` and `$` handling;
  - the Allow-wins tie;
  - longest match;
  - which group is chosen, and case-insensitive agent names;
  - the crawl-delay fallback;
  - an empty Disallow;
  - the client following redirects itself;
  - an unchecked hop and the redirect limit;
  - an unspaced hop and an uncounted hop;
  - the old matcher.
- **Lint and suite:**
  - `ruff check .`: All checks passed!
  - `mypy --strict vinci`: Success: no issues found in 187 source files.
  - `pytest -m "not network"`: `5312 passed, 513 skipped, 37 deselected, 19 warnings in 110.77s`.
  - Record and STATE lints: `714 passed, 1 skipped`.
- **Cost:** $0, and 3 requests to privatebank.jpmorgan.com/robots.txt.

## Files
- **Code:** `vinci/theme_intelligence/fetch.py`.
- **Tests:** `tests/test_theme_intelligence_robots.py`, with the fixture `tests/fixtures/theme_intelligence/robots/privatebank_jpmorgan_com.txt` (a public robots.txt).
- **Docs, in their own commit:** `docs/records/2026-10-15-theme-intelligence-robots.md` and STATE row 32 item (8). With this PR, every verified finding of the #703 review is fixed; only the 55 confirmed U-leads remain, and they still need an order.

## Accepted, stated in the record
- **Paths are matched as the URL carries them**, with no percent-encoding normalisation. None of the probed files needs it.

## Disposition
| Brief item | Disposition |
|---|---|
| O22: robots wildcards (`*`, `$`, longest match) | SHIPPED |
| O22: a redirect target's robots.txt is checked | SHIPPED (hop by hop, at most 5, each spaced) |
| Real-data run | SHIPPED: cached-page check (0 change), the real JPM file, a live robots.txt check |
| Tests and mutation check | SHIPPED: 15 tests; 14 of 14 mutants killed |
| Record and STATE | SHIPPED |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

