---
id:
status: shipped
prs: [559]
date: 2026-09-01
supersedes:
superseded-by:
---

# The first Stage-4 freeze — glp1-drug-value-chain starts its forward clock at 15 BUY / 29 AVOID

**WHAT.** `glp1-drug-value-chain` is frozen. 44 dispositioned names entered the append-only
ratification ledger (`data/themes/ledgers/glp1-drug-value-chain.jsonl`) and the committed basket
(`data/themes/baskets/glp1-drug-value-chain.json`): **15 RATIFIED (the BUY leg), 29 PASSED (the
AVOID leg), 0 pending**, entry dates stamped 2026-09-01. This is the first driver whose forward
BUY−AVOID spread begins accumulating, and the first ratification ledger the repo has ever held.

```
BUY    A AMGN BDX CAH COR GPCR HIMS LLY MCK NVO OMDA PFE VKTX WAT WST
AVOID  AHCO ALT AMLX AMPH AMRX ATR BAX BHVN ENTX HALO KE LGND LXRX MBX MLAB MRK OPK
       PODD PTGX RGEN RPRX SEPN SGMT SHC SRRK TMO UFPT VTRS ZTS
```

**WHY NOW.** The worksheet came back from the analyst with every row dispositioned and no blanks.
`dig-deeper` is defined as "temporary — MUST resolve before a basket freezes"; all six (AMRX, BHVN,
HIMS, NVO, OPK, VTRS) were resolved, so the gate opened. `ai-value-migration` is NOT frozen: six
remain (ARM, AVGO, DGXX, IBM, MMED, QCOM).

**THE HUMAN'S WORK IS INTACT AND CHECKABLE.** Before the freeze the returned file was verified
against what was sent: 44 rows out, 44 back, none added or dropped, and **no machine column altered
on any row** — so the evidence the analyst judged is byte-identical to the evidence sealed beside
their verdict. 15 rows had been shown the wrong grade-driving fact by an earlier export defect and
were re-judged on corrected evidence; one call changed as a result (ATR, ratify → pass, on the
corrected Injectables mix of ~9% of consolidated revenue).

**TWO GUARDS MET A CASE THEIR AUTHORS HAD NOT SEEN, and both were updated deliberately rather than
deleted.**

1. **The layer-label guard was a length proxy.** It asserted `len < 60` as "a crude length guard:
   any single string long enough to be a filing quote". `glp1-drug-value-chain` is the first
   `multi_tag=True` driver to reach a committed basket, so
   `incumbent-franchise+next-gen-assets+manufacturing-infra+access-distribution` — 75 chars of four
   DECLARED tags — tripped it. The guard now checks each `+`-separated component against the
   driver's own `provenance_tags`, which is what the length was ever a proxy for. It is strictly
   stronger: a 13-character bogus label (`made-up-layer`) passes the old check and fails the new one.
2. **The July-ledger pin.** Its message said: "if one has been RE-FROZEN from a real worksheet that
   is good — update this pin deliberately rather than deleting it." That is exactly this case, so
   the pin now names the three JULY drivers whose ledgers were lost and must never be fabricated,
   instead of asserting the ledger directory is empty. It still refuses a rebuilt July ledger; it
   no longer refuses every future freeze.

**HOW VERIFIED.** Full offline suite green on the committed artifacts — **3,406 passed, 143
skipped**. Both guard changes mutation-tested: a filing quote injected into a layer label reds, and
so does a short undeclared tag. The freeze's own output reconciles — 44 ledger rows, 15 + 29 = 44
basket names, entry dates on all 44.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **THE LEDGER IS APPEND-ONLY AND THE CLOCK IS RUNNING.** There is no delete path. Every later
   correction is a new row, not an edit. The spread these 44 names generate is now the fund's first
   real evidence, for or against.
2. **A REHEARSAL ATTEMPT WROTE THE COMMITTED BASKET.** `--baskets-out` is applied AFTER the default
   write, so pointing it at a scratch path does not prevent `data/themes/baskets/<driver>.json`
   from being written; passing a directory then crashed on the second write. The ledger DID stay in
   scratch, so nothing irreversible happened, and the stray basket was removed before the real run.
   There is no dry-run flag. FALSIFIER: if a second person tries to rehearse a freeze and dirties
   committed state, `--baskets-out` needs to gate both writes or a `--dry-run` flag is owed.
3. **ONE MACHINE-EXTRACTED FACT IS KNOWN WRONG AND IS SEALED ANYWAY.** On AMPH the `grade_fact`
   asserts no incretin attribution while the same accession discloses two GLP-1 APIs; the analyst
   caught it and passed on materiality instead. The ledger keeps the machine's fact as the input
   that was judged — which is the point — but it is a reminder that a grade_fact is an LLM
   extraction, not a verified quote.
