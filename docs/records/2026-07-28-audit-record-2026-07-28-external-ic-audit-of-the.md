---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**AUDIT RECORD — 2026-07-28 EXTERNAL IC AUDIT OF THE SMPL DOSSIER (docs/audits/
2026-07-28-smpl-ic-audit.md) — VERIFIED AGAINST THE REPO, QUEUED.** An external Investment-
Committee audit of the live SMPL dossier (the 07-24 assembly; 104 claims, 93% resolved, three
self-retractions and a do-not-change list). Every checkable claim was verified against our own
files before queueing — CONFIRMED: **P1** (the $391.9M LTM Asset Writedown — 43% of market cap —
absent from the dossier, which cites only the FY25 $60.9M three times; the ledger V-row KNEW the
YTD $331M); the **information-regression trio** (V-row records $331M impairments, 1.2x loan-basis
leverage, ~2.1M-share buyback pace; the dossier prints "covenant basis: UNKNOWN (not disclosed)" —
a FALSE UNKNOWN, our own ledger knew — root cause: assembly never reads the ledger payload back);
**P2** (guidance block cites the April 8-K `-000010` 4×, never July's `-000021`; the bear leg
argues from the superseded guide while the base uses the fresh one); **P8** (two consensus
vintages in one build: 1,334 ×3 and 1,351.8 ×1, unreconciled); **P6/P9** (the `biff_xls` branch
error and the sheet-shape absence reason are both in the artifact); **P7** (the scenario block
prints none of shares/D&A/net-debt — the auditor reverse-solved our inputs to 93.77M vs the
recorded 93.678M, which proves the reproducibility gap). WRONG IN THE REPORT, so the queue items
below name the true objects: **P3's mechanism** — the ANCHOR is current (1,392.235, recomputed
07-24); the stale 1,416.208 sits in the underwrite record's ENTRY-VINTAGE reference row, whose
source label ("committed dossier anchor block") is itself the house-token confusion our linter now
flags; the surviving catch is real (bull 1,420 sits ABOVE the LTM it claims to sit "just under").
**P4's mechanism** — spot's source stamp reads Polygon store close 2026-07-22, NOT the ledger exit
price (they coincide because both froze the same session); the staleness substance stands.
**N7 is half-wrong** — the record carries ALL THREE re-underwrite triggers (parity with the
V-row); the md dossier simply does not render them — a RENDER gap, cheaper than re-speccing.
ERRATUM E1 appended to the committed memo (`kind: note_clear`, 2026-07-28, operator-directed):
its "no WATCH row" statement was scoped to the five-row ledger export the audit received — the
WATCH is the 07-27 record reissue the audit never saw; a rendering/scoping defect in the audit,
not a finding reversal (the committed export is an earlier copy lacking the sentence verbatim —
noted in the erratum itself). EXTERNAL VALIDATION banked: the auditor independently reproduced all six boundary-cell ratios
(2.17/1.92/2.34/2.07/1.96/1.73 — the exact cells the 1.3 migration re-homed) and §D verifies the
whole mechanical layer (band, percentiles, margin anchors, transcripts verbatim, peers, insiders).
OPERATOR QUESTIONS ANSWERED IN THIS RECORD: (1) **WATCH-vs-CLOSE in production is a TWIN-PARITY
GAP, not a data conflict.** The sequence is coherent (BUY 07-21 → CLOSED 07-24 → record reissued
WATCH 07-27) and the WEB narrates it — the 2026-07-27 external-honesty pass renders the verdict
chip close-aware ("BUY — closed … at $10.53") beside the watch status. The MD/PDF twin never got
that pass: `render.py` has no close-aware disposition, so the audited artifact shows WATCH + "not
held" with NO trace of the closed BUY. Queued as the render-parity item below. (2) **WHY SMPL WAS
SKIPPED on 07-27** — recorded at the time: "already current at 07-24 with its calendar, and
carrying the operator's #212/#217 work — re-assembly would have regenerated its synthesis for no
gain." Synthesis-weather avoidance, NOT an audit hold. Consequence owned: the 07-24 render stayed
the artifact of record four days. Mitigation, stated honestly: a 07-27 re-assembly would NOT have
cured the confirmed defects — P1/P2/P5/P6/P9 are extractor/synthesis code paths that reproduce on
every assembly, and SMPL was not in the 07-27 price backfill so spot would have stayed 07-22.
