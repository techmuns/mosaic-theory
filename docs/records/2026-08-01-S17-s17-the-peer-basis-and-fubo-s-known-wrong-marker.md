---
id: S17
status: recorded
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S17. THE PEER BASIS, AND FUBO'S KNOWN-WRONG MARKER (2026-08-01).**

**MY PRIOR REPORT WAS WRONG: EDGAR DOES SUPPLY CAPITAL STRUCTURE.** `FundamentalSnapshot` carries
`ebitda_annual` (operating income + D&A) and `net_debt` (total debt - cash), both PRESENT on all
five names. What is deferred is the PERCENTILE, which needs a trailing series; the CURRENT multiple
needs only current inputs. Corrected EV/EBITDA, each input stamped separately because the three
never share an as_of:

| name | EV/EBITDA | cap @07-29 | net_debt | ebitda_annual |
|---|---|---|---|---|
| FLO | 9.64x | 1.58B | 1.71B @2026-05-21 | 0.341B @2026-02-25 |
| BRBR | 7.17x | 1.55B | 1.15B @2026-05-05 | 0.376B @2025-11-18 |
| SMPL | 6.73x | 0.93B | 0.27B @2026-07-09 | 0.178B @2025-10-28 |
| CPB | 6.03x | 6.85B | 2.55B @2026-06-08 | 1.558B @2025-09-18 |
| VITL | 5.71x | 0.59B | -0.03B @2026-05-07 | 0.098B @2026-02-26 |

**THE TWO SOURCES CANNOT BE RECONCILED BY ONE RULE — the disagreement FLIPS SIGN.** SMPL EDGAR
6.73x vs CIQ 5.3x (CIQ implies a ~31% LARGER EBITDA); BRBR EDGAR 7.17x vs CIQ 8.2x (CIQ implies a
SMALLER one). A single adjustment convention cannot produce both. **The operator's inference — EDGAR
FY GAAP pre-impairment vs CIQ LTM adjusted — holds on PERIOD but not as a uniform adjustment.**
Measured: EDGAR's SMPL EBITDA is FY ending **2025-08-30** (156.9 op + 21.4 D&A = 178.3M, filed
2025-10-28); BRBR's is FY ending **2025-09-30** (357.4 + 18.6 = 376.0M). Both are the filer's own
fiscal year, so the two names are not even on a common period as things stand.

**`ebitda_annual` DOES NOT REACH BACK FOR THE LATEST POSITIVE.** `latest_annual` is
`max(annual, key=(period_end, filed))` — sign-blind. **It does NOT carry #298's defect.** It is
however **UNBOUNDED IN AGE**: there is no `MAX_EPS_AGE_DAYS` analogue, so an arbitrarily stale
annual is used without a guard. Different defect from the one suspected, and worth its own item.

**QUARTERLY IS AVAILABLE AND ABUNDANT — an LTM GAAP EBITDA is buildable from EDGAR.** SMPL carries
**128** non-annual `operating_income` points and 29 `dep_amort`, latest period **2026-05-30**;
BRBR 66 and 40, latest **2026-03-31**. Against annuals ending 2025-08-30 / 2025-09-30, that is
~9 months fresher AND puts every name on a common trailing window. **Not built — reported.**

**WHICH BASIS A COHORT TABLE CAN USE (the answer to 1d): EDGAR ANNUAL GAAP, today.** It is the only
basis producible for all five under one convention. Its weakness is period, not adjustment: each
name sits on its own fiscal year-end. CIQ cannot supply a cohort table at all — it stops at the five
dossiered names. **LTM GAAP from quarterlies would fix the period axis and keep the convention; it
is the right target and does not exist yet.**

**THE PEER RULE, FIXED BEFORE ANY MULTIPLE WAS SEEN** (cap 0.3x-3.0x of the name · positive EBITDA ·
minimum three): **4 of 10 survive** — BRBR 8.5x, JJSF 7.7x, UTZ 29.0x, JBSS 8.0x. **Filtered median
8.25x**, against the default export's 7.80x and SMPL's own 5.30x. Dropped for cap: KHC (33.1x the
name), CAG (7.6x), CPB (7.0x), MZTI (3.2x), FRPT (3.1x), HAIN (0.05x). **No name was added or
removed after its multiple was seen.** The filtered median moves the basis AWAY from the audit's
8.0x by less than half a turn — it does not rescue 12.5x, and it does not vindicate 5.3x either.
*(A parse defect nearly inverted this: `tev_ebitda` is stored as a STRING, and a numeric-typed
filter reported ZERO survivors. Prose-as-data, D21, inside the peer grid.)*

**FUBO'S KNOWN-WRONG MARKER — BUILT AS A SIDECAR, operator ruling 2026-08-01.**
`data/dossiers/FUBO/known_wrong.json` holds five items, each stated KNOWN-FALSE rather than unknown:
pre-reverse-split share count · G3 never valued it · pre-fix caveat text · the `"13.1x rest on"`
agreement bug · pre-combination entity throughout. **`dossier.json` is UNTOUCHED** — it is the
record the standing rule seals — and `dossier.md` renders the banner ABOVE the brief, because a
rendered view is not the record and a reader who reaches the figures first has already been misled.
**THE EXCEPTION SERVES THE RULE:** the rule exists so FUBO cannot LOOK VALID on a wrong share base;
every item asserts a number is false, so the marked page cannot look valid. Each item carries a
`not_merely_stale` line — the gap/error distinction is the point, and a reader who files these under
"stale" underestimates them by a corporate action. **MUTATIONS, all RED:** marker absent · present
but not rendered · an item dropped · `dossier.json` modified (asserted against git, not intent).

**REVIEW FINDING (#308) — THE MARKER COULD VANISH SILENTLY.** The first cut caught `OSError`/
`ValueError` around the file read and returned no lines, so a corrupt or empty `known_wrong.json`
made the banner DISAPPEAR while the file sat there looking like the page was marked. Measured, all
three ways: malformed JSON, `items: []`, and a missing `items` key each rendered the page CLEAN.
**That is the worst available failure for a warning** — the page then looks valid, which is the
exact state the standing rule exists to prevent, reached through the mechanism built to prevent it.

**ABSENT and BROKEN are different states.** Absent is silence and correct (the other ten names).
Broken is a warning that failed, and rendering past it is the harm. Now RAISES on both, with the
message naming the fix ("fix or delete the file; never render past it"). Same distinction as
`extraction_version`'s `""`-vs-`None` normalisation and D21's gap-vs-error: *a thing that could not
be read is not a thing that was not there.* Mutation — revert to swallow-and-return-`[]` -> RED.

**FLEET BYTE-IDENTITY re-verified after both the renderer change and the fix: all 11 dossiers
render byte-identical to their committed `.md`** (FUBO including its new banner). The renderer
gained a call and changed nothing for the ten without a marker.
