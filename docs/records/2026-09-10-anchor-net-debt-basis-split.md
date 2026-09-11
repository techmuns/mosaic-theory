---
id:
status: open
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# GOOGL's page says net debt +$64.9bn AND net cash −$121.7bn — two cash bases, one key, and the gap is exactly its marketable securities

**WHAT.** `data/dossiers/GOOGL/dossier.json` carries two net-debt figures for the SAME company and
the SAME quarter (Q2, 2026-06-30), and they disagree in SIGN:

| field | value | source |
|---|---:|---|
| `anchor.net_debt` | **+$64,880M** (net DEBT) | `EDGAR: total debt 100,164 + finance leases 2,590 + operating leases 18,037 − cash 55,911 ($M)` |
| `mechanical.quality.net_debt_to_ebitda` | **−0.7x**, on **−$121,683M** (net CASH) | `CIQ Net Debt $-121,683M [Q2 Jun-30-2026]` |

The arithmetic closes exactly, which is what identifies the cause rather than guessing at it:

```
242,474 (CIQ "cash & ST inv")  −  55,911 (EDGAR cash)  =  186,563
−121,683 (CIQ net debt)        +  186,563              =   64,880 (anchor net debt)
```

$186,563M is Alphabet's `MarketableSecuritiesCurrent` at 2026-06-30, to the dollar. The two rows
are not two estimates of one quantity; they are two DIFFERENT quantities wearing one name.

**WHY.** The key `cash` means different things on the two sides, and neither says so:

- **EDGAR** (`vinci/edgar/concepts.py:69`) maps `cash` to `CashAndCashEquivalentsAtCarryingValue`,
  falling back to `CashCashEquivalents…RestrictedCash…`. Cash and equivalents ONLY. Consumed by
  `anchor._lease_inclusive_net_debt` and `client.compute_fundamental_snapshot`.
- **CIQ** (`vinci/dossier/ciq_balance.py:199`) puts `cash` with the basis string
  *"total cash and short-term investments, latest balance sheet"*. Cash PLUS securities.

Both are defensible definitions. Carrying both under one key, on one page, without a basis label is
the defect — and it is the SAME SHAPE as the EBITDA-basis defect this repo fixed on 2026-09-05
("The two EBITDA rows are not the same basis, and now the page says which", #370/#371). That fix
labelled the basis; this row never was.

**Why it survived.** `_net_debt_to_ebitda` prefers CIQ outright when present, so the RATIO a reader
looks at is right. The EDGAR figure is the anchor block's own input, computed on a different path,
and nothing compares the two. A name with no CIQ (the breadth fallback) would surface the EDGAR
figure as the only one — labelled *"breadth estimate — may under-capture scattered debt"*, a caveat
about DEBT under-capture that says nothing about the CASH leg this record is about.

**HOW VERIFIED.** Measured over all 18 committed dossiers at `origin/main c656190`, 2026-09-10,
by comparing `anchor.net_debt.value` against the `CIQ Net Debt $…M` figure parsed from
`quality.net_debt_to_ebitda.source_ref`:

- 16 names carry BOTH figures (FUBO and TECX carry no CIQ net debt).
- **11 of 16 disagree** by more than $1M.
- **GOOGL is the ONLY sign flip**, and its gap is two orders of magnitude larger than any other:
  $186,563M. The full disagreeing set, re-derived 2026-09-10 over the 16 two-figure names
  (|anchor − CIQ| > $1M, UNIT $M): GOOGL 186,563 · V 2,419 · LLY 2,158 · **UBER 1,254** · IT 152.8 ·
  AORT 128.7 · VITL 84.0 · NCNO 31.3 · BRBR 8.6 · VRRM 7.9 · WERN 7.5. **UBER's $1.25bn gap was
  omitted from an earlier cut of this list and the tail was stated as "$8M–$153M" — wrong at both
  ends.** V, LLY and UBER all carry investment balances; only below IT do the gaps read as ordinary
  lease/period-end basis differences. So "GOOGL is the only MATERIAL gap" holds only against a bar
  above $2.4bn — a bar this fund has not set (§5.0 row 23), and one that UBER, a followed quality
  name carrying $521M of short-term investments, sits closest to.
- Independently, 5 of 19 names measured carry a SHORT-TERM investment tag at the same instant as
  their cash tag: GOOGL $186,563M, ORKA $857M, UBER $521M, NFLX $29M, VRRM $5M. Only GOOGL's is
  large enough relative to debt to flip a sign.

**BOUNDARY.** WINDOW: the latest instant of each concept as of 2026-09-10. FILTER: committed
dossiers only (`data/dossiers/*/dossier.json`), plus ORKA which is not committed. POPULATION: 18
committed names; 16 for the two-figure comparison; 19 for the tag census (18 + ORKA). UNIT: $M
throughout, and the ratio row is a multiple (x). Measured at `origin/main c656190` in worktree
`mosaic-theory-ta`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **NOT FIXED HERE, deliberately.** This was found while diagnosing ORKA's liquidity read
  (`docs/records/2026-09-10-orka-onboarding-blocked-on-ciq.md`) and is out of that build's scope.
  Reported, not fixed silently, per the scope rule.
- **WHAT A FIX MUST NOT DO.** The naive repair — add marketable securities into the EDGAR `cash`
  concept — walks into two traps this measurement already surfaced. (1) **Double counting:** ORKA
  tags `MarketableSecurities` $857.1M AND its two children `MarketableSecuritiesCurrent` $605.1M +
  `MarketableSecuritiesNoncurrent` $252.0M; summing all three gives $1,714M for an $857M balance.
  (2) **Stale tags:** GOOGL's `MarketableSecurities` last reports at 2022-09-30 and UBER's at
  2019-09-30, years behind their current figures — any sum must require the SAME `period_end` as
  the cash instant, exactly as `_lease_inclusive_net_debt` already requires a shared basis for
  `LongTermDebt` vs `LongTermDebtNoncurrent`.
- **ACCEPTED UNTIL RULED.** GOOGL's committed page keeps a +$64.9bn anchor net-debt input while its
  leverage ratio and Posture line read −$121.7bn. The RATIO the reader sees is correct; the anchor
  input is not, and GOOGL's R1 arithmetic was in any case re-tagged to a forward-P/E equity basis
  by operator ruling 2026-09-01, which reads no enterprise value at all — so nothing decision-facing
  currently rests on the wrong number. FALSIFIER: a name whose underwrite DOES route through
  EV−net-debt and which carries material short-term investments; there its anchor bridge would be
  wrong by the securities balance, silently.
