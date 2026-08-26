---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-23 SMPL combined re-assembly — all three fixes now in the committed artifact
(branch `data/reassemble-smpl`, post-#198/#200/#201).** The ratified "fix first, re-assemble once":
SMPL re-assembled off the fresh main (carries #198's guidance/LTM fixes + #201's P/LTM caveat +
#200's benchmark-band logic), from the isolated CIQ-wired worktree. **All three defect shapes now
CLEARED in the committed `data/dossiers/SMPL/*` + `frontend/*`:** (1) revised guidance PRESENT —
"Updating Fiscal Year 2026 (4) Outlook: Net sales $1.31–$1.35B … adj EBITDA $217–225M", sourced to
Ex-99.1; (2) the bogus 49.3/6.6x row GONE — "company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN"
(49.3/6.6x absent from json); (3) **claim #7 RESOLVED** — the new caveat is in the dossier's caveats
+ md: "EDGAR P/E 10.9x and CIQ P/LTM EPS 16.0x rest on normalized/adjusted earnings — LTM GAAP
diluted EPS is NEGATIVE (−2.08); do not read them as a GAAP trailing multiple." SMPL now carries 5
caveats (was 2). `scenarios/SMPL.json` recipe re-run idempotent on values (ratio 4.0299), schema-
normalized (seal intact). Scope: SMPL only. Suite 1052 passed on the committed artifacts.
**SUPERSEDES #199** (which had only fixes 1+2) — #199 closed in favor of this combined PR. OPEN
(TEST-LAYER follow-up, own code PR): an e2e pin asserting the committed SMPL dossier carries the
P/LTM caveat (a phrasing-independent invariant on the living artifact) — the unit pins cover the
logic; the artifact-level regression pin belongs in a code PR, not this artifact commit.
