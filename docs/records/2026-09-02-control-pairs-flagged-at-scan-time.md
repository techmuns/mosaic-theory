---
id:
status: shipped
date: 2026-09-02
prs: []
supersedes:
superseded-by:
---

# Same asset, two tickers — control pairs flagged at scan time

*Driver: `ai-compute-platform` (found there; the guard is driver-agnostic).*

## What happened

The `ai-compute-platform` scan returned a nine-name binding-contract tier. Two of the nine were the
same asset: **Bit Digital (BTBT) discloses an approximately 70.5% majority equity stake in WhiteFiber
(WYFI)**, and both rows graded `binding-contracts-with-terms` independently. A tier reported as nine
names was eight assets.

This had already been caught once by hand, on the parent `ai-value-migration` sheet, and it came back
unnoticed in a different scan. A defect that recurs after a manual catch is a scan-time defect, not an
adjudication slip — the catch has to live where the rows are produced.

## Why the obvious fix does not work

The universe already de-duplicates by ISSUER (CIK, highest-ADV line). BTBT and WYFI are **different
CIKs** — two separate registrants, one of which owns most of the other. Issuer de-duplication is
correct and cannot see this.

## What was built

`flag_intra_population_control` in `vinci/themes/exposure.py`, a cross-row pass over the completed
scan (it needs the population to know whether a cited ticker is in scope). It flags every pair where
one scanned issuer discloses majority control of another scanned issuer, annotating **both** rows —
either may be the one a reader opens.

**It flags and never drops.** Which side of a control pair carries the exposure is an adjudication:
the parent may be a holding company whose only exposure IS the subsidiary, or the subsidiary may be a
sliver of a diversified parent. Dropping a name would be the machine concluding.

## The detector, and the false-positive shape that set its form

The first form matched majority-ownership language and then any ticker-shaped token near it. On the
live 745-row corpus that produced **9 candidate pairs, 8 of them false** — every false one was a
bare-word collision with a two-letter ticker:

```
NEE -> AI    [wholly owned subsidiary]      MARA -> AI   [majority ownership]
LBTYA -> IT  [70% of its equity]            HUT  -> IT   [wholly-owned subsidiary]
BTBT -> WYFI [70.5% majority equity stake]  ...
```

`AI` is C3.ai and `IT` is Gartner; both are ordinary English inside a sentence about AI data centers
and IT infrastructure. The shipped form requires the subsidiary to be cited **exchange-qualified**
(`(Nasdaq: WYFI)`) — the way a filing actually cites another public company. On the same corpus that
returns **one pair, zero false positives**.

## Verification (real runs, both live archives)

```
20260902T111713Z  n=745  control-pair flags=2   BTBT<->WYFI   ('70.5% majority equity stake')
20260902T095720Z  n=241  control-pair flags=2   BTBT<->WYFI   ('70.5% majority equity stake')
```

It fires on the **earlier** archive too: had the guard existed, the defect would not have reached a
second scan. Suite green, ruff + `mypy --strict` clean.

## The limit, stated loudly

**Recall is low by construction and the flag is NOT a clean bill.** `disclosed_facts` are
driver-exposure extracts, not filing text, so a control relationship surfaces only where it happened
to be relevant to the driver AND the subsidiary was cited exchange-qualified — true of **2 of 745
rows**. A pair this misses is a pair the analyst still owns.

The complete source is **EDGAR Exhibit 21, "Subsidiaries of the Registrant"** — a filed exhibit, not
a purchased dataset. Nothing in this repo extracts it. That is the right next build if control pairs
turn out to matter beyond this one; it was not built here because it is a new extraction pipeline and
this defect did not require one.

## Pins

`tests/test_themes_exposure.py` — positive: the real BTBT/WYFI pair, flagged on both sides, unrelated
names untouched. Negative: the observed `AI`/`IT` bare-word shapes must produce no pairs. Negative:
control of a name OUTSIDE the population is not flagged, because it cannot be double-counted.

## Incident → invariant

| incident | invariant | shipped |
| --- | --- | --- |
| BTBT/WYFI counted as two names in one tier, after a prior manual catch on another sheet | cross-row control-pair flag on every scan, both sides annotated | Y (recall-limited; limit recorded above) |
