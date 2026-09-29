---
id: 2026-09-28-fleet-onto-the-document-identity
status: shipped
date: 2026-09-28
prs: [657]
supersedes:
superseded-by:
---

# The fleet pass reaches ten names, and twelve are blocked on a CIQ re-export

**WHAT.** The standing artifact pass, run so the committed pages pick up the covenant-identity
work in #652 and #653 (a covenant exhibit is named by the DOCUMENT, and a title relabels a group
rather than merging two). It ships **10 of the 23** names it was aimed at. **12 refuse loud** with
`FreshnessError` — their CIQ panels are past the 45-day ceiling and the guard will not underwrite
from them, which is the guard working and an OPERATOR blocker, not a build one. **WERN assembled
cleanly and is HELD BACK by operator decision**, see below.

Shipped (each `1 done · 0 error(s)`): AMZN, BRBR, GOOGL, LLY, NFLX, NKE, ORKA, PARR, TECX, WLK.

Blocked, with the guard's OWN ages: NCNO 73d, VRRM 62d, CNXC 62d, AORT 61d, IT 61d, VITL 61d,
UBER 54d, EPAM 52d, V 52d, SMPL 48d, FUBO 48d, MVST 47d.

**THE BLOCKED LIST IS MEASURED, NOT INFERRED, AND THE FIRST VERSION WAS WRONG.** A scan of the
oldest `*_as_of` field in each committed dossier put 14 names past the ceiling and read several
far staler than they are (VRRM 181d, MVST 136d). Attempting all 14 corrected it: the guard checks
`valuation.implied_expectations.tev_as_of`, a different and newer field, and **TECX and WERN
assembled**. A `FreshnessError` aborts before any LLM call, so attempting is nearly free — which
is why the list below is the guard's verdict rather than a proxy for it.

**WERN IS HELD BACK.** It assembled and its stock purchase agreement is correctly refused, but its
Amendment No. 3 rendered a filing id as a contract name (#655, #656). #656's fix landed after this
set was built, and re-assembling WERN was deferred by operator decision, so its page stays as
committed — the pre-#652 pointer labels — rather than shipping a heading the new end-to-end guard
refuses. That guard passes on this set precisely because WERN is out of it.

**TWO OF THE FOUR HEADLINE MISLABEL CASES REMAIN UNFIXED ON THE PAGE.** VRRM (a revolving credit
agreement published under a term loan) and UBER (term loan agreements under convertible notes) are
blocked on a CIQ re-export. NKE — the executive offer letter reaching a covenant extractor — is
fixed here. WERN (a STOCK PURCHASE AGREEMENT under an unsecured credit agreement) is fixed in code
and verified, but held back from this set. The code closed on 2026-09-28; three of those four
pages have not.

**WHY.** The fix only reaches a reader through a re-assembly, so a merged PR changes nothing a
human sees until this pass runs. Running it also re-draws every synthesis five times, which is why
the diff is far wider than "headings changed" — see the cost section.

**HOW VERIFIED.**

*Covenant headings, committed → after.* Six of the ten changed, each from the pointer's guess to
the name the document gives itself:

    NKE    364-day Committed Credit Facility  ->  364-DAY CREDIT AGREEMENT
           Committed Credit Facilities        ->  CREDIT AGREEMENT
    AMZN   3 pointer families                 ->  4 document titles
    NFLX   4 pointer families                 ->  3 document titles
    BRBR, PARR, WLK                           ->  relabelled likewise

NKE also carries the refusal this work exists for: *"(E5) not a debt agreement — refused rather
than extracted under the pointer's guess (material contracts (10-K exhibit index))"*. Its CFO
offer letter no longer reaches a covenant extractor on a live page. TECX carries the same refusal
against its 10-K material-contracts pointer.

*The draw gate.* Five withheld on disagreement (AMZN, BRBR, GOOGL, NFLX, PARR); four unanimous
(LLY, NKE, ORKA, WLK). GOOGL's lean moved mixed → strongly-bullish and was STILL withheld at 3–2 —
a lean changing without a proposal following it is the gate doing its job. **NKE drew 5 attempted
/ 4 COMPLETED**: one draw failed, and unanimity was judged on the four usable ones, so its tally
reads 4 and not 5. That is the designed behaviour and it is worth stating, because a reader who
knows `SYNTHESIS_DRAWS = 5` will otherwise read "4" as a miscount.

*Anchors.* `anchor-backfill` over the nine: 4 changed. GOOGL ($197.01) and NFLX ($58.17) were
restored — a full assembly does not pass the CIQ workbooks and the backfill does — LLY and ORKA
moved, five were left byte-identical.

*Suite.* `pytest -m "not network"` run on the freshly written artifacts and green BEFORE pushing.
It first came back RED, and the failure is the useful part: `anchor-backfill` re-renders
`data/dossiers/*/dossier.md` AFTER the assembly's mirror step, so `frontend/dossiers/GOOGL.md` no
longer matched its source and `test_every_web_mirror_is_byte_identical_to_its_source` refused it.
The artifact-pass order is assemble → BUILD FRONTEND → commit, and the frontend build had been
skipped after the backfill. Re-run and green.

**BOUNDARY.** Measured 2026-09-28 off `e0287341`.
- *10 shipped / 12 blocked / 1 held back*: population = the 23 committed dossiers other than the
  three retail names landed in #654; unit = names. Every one of the 23 was ATTEMPTED; the blocked
  count is the guard's verdict, not a scan's estimate.
- *Panel ages*: as REPORTED BY THE GUARD, from `valuation.implied_expectations.tev_as_of` against
  a 2026-09-28 build and the 45-day `MAX_PANEL_AGE_DAYS` ceiling in `vinci/dossier/freshness.py`.
  An earlier scan of the oldest `*_as_of`/`*vintage` field in each dossier is NOT comparable — it
  reads older fields and overstated several names badly (VRRM 181d vs the guard's 62d).
- *6 of 10 headings changed*: the `- **Covenants — …**` lines in each `frontend/dossiers/<T>.md`,
  committed version vs this pass.
- *5 withheld / 4 unanimous*: `synthesis.draw_agreement`, over the NINE names measured before TECX
  was added to the set; TECX is not in that split.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The synthesis text changed on all ten, and that is not evidence.** A full assembly re-draws
  five times, so prose and tallies move on data that did not. GOOGL's lean flip is draw variance,
  not a new read. Nothing here should be interpreted as the machine changing its mind.
- **The fleet is now in two states.** Ten names carry document-identified covenant headings;
  thirteen carry the class-generic guesses, including three known-wrong ones (VRRM, UBER, WERN).
  A reader comparing two pages is comparing two vintages. STATE.md row 28 carries the blocked list.
- **WERN's page is knowingly stale.** Its fix exists and is verified; only the re-assembly is
  deferred. *Falsifier:* it is still unshipped at the next artifact pass.
- **The blocked list will grow.** MVST at 47d, SMPL and FUBO at 48d only just crossed; every name
  drifts toward the ceiling, so a name-by-name re-export loses to a batch.
- **NOT DONE:** the retail KPI patterns (same-store sales) for the anchored driver extractor; the
  four items #652's review left unfixed (`render.py:1245`, the pointer layer's class-generic
  queries, CNXC "Other Loans", the ancillary SECURITY AGREEMENT as a governing family).
