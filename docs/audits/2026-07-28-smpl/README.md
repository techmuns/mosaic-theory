# SMPL audit of record — 2026-07-28

**Index and precedence for the three artifacts of this audit.** Read this first; it is the manifest
the memo's §Artifact Manifest specifies.

## Artifacts

| File | Purpose | Authoritative for |
|---|---|---|
| [`ic-memo.md`](ic-memo.md) | Full Investment Committee audit and stress test — 13 sections plus scoring, the audit trail, the erratum | **The audit finding of record, the decision sequence, the evidence dashboard** |
| [`defect-report.md`](defect-report.md) | Nine platform + seven name-level defects, each with root cause, fix and acceptance test | **The engineering queue** (STATE.md §Next-steps items 1, 17–24) |
| [`independent-dossier.md`](independent-dossier.md) | Thesis rebuilt on corrected methodology — brand-level sum-of-parts, cross-section multiples, time-value discipline | **The investment view and entry conditions** |

## The audited artifact has since MOVED — what changed, and what did not

This audit describes SMPL's `dossier.md` as it stood on 2026-07-28. **The committed artifact on
`main` now differs from it**, so a later reader diffing the two will find lines the audit does not
mention. Recorded here so that is not a surprise.

| date | change to the committed `dossier.md` | affects a finding? |
|---|---|---|
| 2026-07-28 (#245, queue item 26a) | Two lines added — the header date now reads `· extraction unstamped`, and Record & reproduce gains an `Extraction:` row | **No** |

**A RE-RENDER, NOT A RE-ASSEMBLY.** No extraction ran, no network was touched, no synthesis was
re-generated and `dossier.json` did not change — the render gained an extraction-version stamp and
all 11 committed dossiers were re-rendered from their existing JSON to keep them from drifting from
the renderer. SMPL's reads **"unstamped — assembled before extraction versions were declared;
vintage unknown"**, which is the truthful state of an artifact built before the stamp existed.

**Every defect in this audit is still open on the artifact.** SMPL is deliberately NOT re-assembled
(four of its five acceptance checks still fail, pending queue items 1, 18 and 22), so the numbers,
the prose and the missing $391.9M writedown are exactly as the audit found them. When SMPL IS
re-assembled, this table gets the row that matters.

## Precedence on valuation — READ BEFORE QUOTING A RATIO

Two reward:risk ratios exist in this folder and they are **not** alternatives; one supersedes the
other.

| Source | Value | Ratio | Status |
|---|---|---|---|
| `ic-memo.md` §10 | PW $14.44 (+40.5%) | **2.15:1** undiscounted | **SUPERSEDED** — audit-stage |
| `independent-dossier.md` §5 | $16.47 nominal · **$12.69 present value** | **1.36:1 time-adjusted** | **GOVERNS** |

The independent dossier rebuilt the valuation on a brand-level model and applied a discount to
upside that the memo did not (upside requires ~2.5 years of proof; downside reprices in a
quarter). **Direction and findings are unchanged; the magnitude and the ratio move.** Quote 1.36:1
unless you are explicitly citing the audit-stage view, and say so when you are.

For reference, the published dossier's own figure was 3.83:1 — anchored to a stale price, a
superseded guidance block, a one-month-stale consensus vintage and a share count 6% above the
disclosed figure.

## Supersession of the earlier commit

`docs/audits/2026-07-28-smpl-ic-audit.md` (added by #236, removed by this commit) was an
**abridged export**: only two of the three artifacts had ever been written to files, so the
committed copy was the defect report alone, and it lacked material present in the analysis as
delivered. Its hand-appended erratum is superseded by the properly-scoped erratum now carried in
`ic-memo.md`. The file is REMOVED rather than left beside its replacement — two versions of one
audit in a folder with no precedence marker is item 19 (assertion integrity) in our own paperwork.

## Erratum, and the pattern it belongs to

`ic-memo.md` carries ERRATUM (`kind: note_clear`) on the "There is no WATCH row" claim: scoped to
the five-row ledger export the auditor received, where the WATCH is a 2026-07-27 record reissue
held in a separate store. A scoping defect in the audit, **not a finding reversal**.

The memo records that this was the **second** such error in the same audit — the first being P3,
where a stale value was attributed to the anchor block because the dossier's own source label said
so. Both are the assertion-integrity finding (queue item 19) pointing back at the audit itself:
a conclusion drawn from an artifact that did not declare its own limits. That is worth keeping on
the record precisely because the audit found the same class in our pipeline.

## One correction carried in

The memo cites the repo's recorded share count of **93.678M**, not the auditor's solved 93.77M.

## What the audit verified as CORRECT — do not "fix" these

`defect-report.md` §D and `ic-memo.md` §2. The own-history multiple band (35 closes, min 6.11 /
median 17.85 / p25 15.20 / p75 20.88), the percentile placements, the margin anchors, all six
entry-boundary ratios, the EBIT→EBITDA bridge, every transcript-sourced operating claim verbatim,
the peer medians, and the insider activity all reproduced exactly from source. Three of the
auditor's own preliminary flags were retracted (§C). The mechanical assemble-and-cite layer is the
platform's verified strength; the defects are in freshness, materiality and render parity.
