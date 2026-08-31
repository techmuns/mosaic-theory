---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**AUDIT-OF-RECORD + ACCEPTANCE POLICY + THE ITEM-1 INGESTION DEPENDENCY (2026-07-28,
operator-directed).** Three changes, none of them a defect fix — REMEDIATION STATUS IS STILL ZERO
of nine platform defects (verified, not asserted: #236 touched STATE.md and docs/ only; no
materiality guard exists anywhere in `vinci/`; no price-vs-panel as-of comparison exists; the
guidance `Situation`-cell path is intact. Re-assembling SMPL today reproduces all nine).

(1) **AUDIT OF RECORD is now the three-artifact folder** `docs/records/2026-07-28-smpl-audit-of-record.md` with a
README manifest as index. The earlier single-file export was an ABRIDGEMENT — only two of the
three artifacts were ever files, the full IC memo having been delivered in conversation — and it
is REMOVED, not left beside its replacement (two versions of one audit with no precedence marker
is item 19 in our own paperwork). PRECEDENCE ON VALUATION recorded in the manifest: the memo's
§10 audit-stage view (PW $14.44, **2.15:1 undiscounted**) is SUPERSEDED by the independent
dossier ($16.47 nominal / **$12.69 PV / 1.36:1 time-adjusted**) — the later document discounts
upside that requires ~2.5 years of proof against a downside that reprices in a quarter. Direction
unchanged, magnitude moves. The ERRATUM (`kind: note_clear`) now lives properly in the memo, and
records that the same scoping error occurred TWICE in one audit — the WATCH claim and P3's
anchor-block mislabel — both being the assertion-integrity finding (item 19) pointing back at the
audit itself. The memo carries the repo's recorded 93.678M share count, not the solved 93.77M.

(2) **ACCEPTANCE POLICY — binds every audit-derived build (items 1, 17–23).** Each ships with a
fixture that FAILS on `2facc5e` (the audit-merge commit) and PASSES after. **Suite-green-unchanged
is not evidence a defect is fixed** — the 1115-green suite at `2facc5e` is precisely a suite that
does not test for any of these nine. A build whose PR cannot show the red-then-green transition on
its own fixture is not done, regardless of code state. This extends, and does not replace, the
existing every-guard-ships-a-positive-AND-negative-pin rule.

(3) **ITEM 1 HAS AN INGESTION DEPENDENCY THAT WOULD OUTAGE THE PIPELINE IF THE CONTRACT LANDED
ALONE** (operator-raised, investigated 2026-07-28). The price store is a **git-ignored per-
environment SQLite DB** (`data/vinci.db`; `*.db` in .gitignore — "durable state is the committed
JSON/CSV snapshots, NOT the binary DB"), so there is NO committed price state and coverage is
whatever that environment last ingested. Two ingestion modes: whole-market `grouped-daily` (the
ongoing universe refresh) and per-symbol `--aggs` (ONE call per symbol, for backfilling a NEW
name's history), against a Polygon free tier of ~5 calls/min. Refresh is scheduled — but WEEKLY
(`.github/workflows/weekly-screen.yml`, Mondays 06:00 UTC, "refreshes EOD prices for the stored
universe"). **THE REAL DEPENDENCY IS A CADENCE MISMATCH, not partial name coverage:** prices
refresh on a weekly schedule while CIQ panels arrive MANUALLY and irregularly (CIQ is depth-stage,
manual — no programmatic feed), so a bundle pasted on a Thursday is automatically newer than
Monday's price, and a contract failing when `price.as_of < max(panel as_of)` would fail builds
BY DESIGN for most of the week. It would convert a silent-staleness defect into a visible build
outage — louder, but not fixed. SEQUENCING CONSEQUENCE: **the ingestion fix ships AHEAD of the
contract, not with it.** Minimum shape before item 1 can bind: price refresh on demand at build
time (or a cadence at least as fast as panel arrival), plus an explicit answer for a name whose
bars are absent entirely. Worktree evidence (this environment, NOT authoritative — a session
artifact): 11 securities in `securities`, all 11 with bars, 8 at 309 bars latest 2026-07-24 (a
session backfill) and NCNO/IWM/MDY at 1,268 latest 2026-07-21 — i.e. even here two names sit
three days behind the others, which is the cadence gap in miniature. SMPL's own recorded
`spot_source` reads "Polygon daily aggregate close 2026-07-22 (store)" — a store read, confirming
the audit's P4 mechanism claim (ledger exit price) was WRONG while its staleness substance was
right.
