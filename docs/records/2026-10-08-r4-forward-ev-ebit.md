---
id:
status: shipped
date: 2026-10-08
prs: [688]
supersedes:
superseded-by:
---

# R4 — the EV/NTM EBIT recipe computes and the create path reaches it; the page tag and the card come next

**WHAT.** Step (3) of the build order the operator ruled
(`2026-10-08-ev-ntm-ebit-eligibility-ratified.md`), first part: the recipe's ARITHMETIC and its
REACHABILITY through `scenario-create`.

| | |
|---|---|
| recipe | `R4_forward_ev_ebit`, basis `EV/NTM EBIT`, axes `ebit` and `multiple` |
| leg field | `ScenarioInput.ebit`: the NTM EBIT at the leg's exit, $M |
| formula | EV = NTM EBIT × EV/NTM EBIT; equity = EV − net debt at exit; value/share = equity ÷ diluted shares |
| units | as R1: $M over millions of shares |

Each leg carries its EBIT, EV, equity and EV/EBIT, so it can be walked from its driver to its
per-share value.

`_run_r4` refuses each of these rather than ignoring it:
- another basis;
- a leg without EBIT, or with a non-positive one (that name is R2's case);
- an EPS, revenue or margin on a leg (a driver the value never reads);
- a D&A fact (an EBITDA recipe's input);
- a missing net-debt or share fact;
- a misstated formula.

**THE OPERATOR'S RULINGS, 2026-10-08** — the method choices inside the arithmetic:

1. **Earnings axis: NTM EBIT at exit, $M.** One number per leg, like R3's EPS. Revenue × margin is
   the leg's derivation, not its input. The axis is named `ebit`, not `earnings`: R3's `earnings`
   axis maps to EPS, and one axis name meaning two units is the mismatch the axis map exists to
   prevent.
2. **Net debt: CIQ's,** the same source as the multiple: leases in, cash and short-term investments
   out. EDGAR's figure is shown beside it as a cross-check. This departs from the anchor's
   EDGAR-first rule for this recipe only.
3. **Exit net debt, the operator's rule as given:**
   - a reliable same-basis consensus or explicit exit forecast is used automatically where one
     exists;
   - otherwise today's same-basis net debt is held constant;
   - it is NEVER computed as current − FCF unless the data establish that the cash-flow line is the
     complete change in the net-debt balance;
   - it NEVER requires manual analyst input for dossier assembly;
   - the underwriting prompt (Prompt 1) may override the constant default with a stated derivation
     on the same EV basis.
4. **Non-operating investments stay inside the multiple, for now.** The bias is stated: the stake
   scales with EBIT, about −1.5% on AMZN's hold leg.

**THE CONSENSUS NET-DEBT LINE IS NOT SAME-BASIS — measured, so rule 3 holds today's figure.** CIQ's
Estimates export does carry a "Net Debt" consensus. Its REPORTED FY2025 values were set against
CIQ's own lease-inclusive balance-sheet net debt at the same date (Q4 Dec-31-2025):

| name | consensus line, FY2025 actual | CIQ balance sheet | gap |
|---|---|---|---|
| AMZN | −$57,381M | +$55,518M | $112.9bn — leases, roughly |
| GOOGL | −$80,296M | −$59,847M | $20.4bn |
| UBER | $3,816M | $4,669M | $0.9bn |
| WLK | $2,860M | $3,482M | $0.6bn |

None is the TEV bridge's basis. AMZN's consensus for FY2026–28 reads $22.3bn / $74.0bn / $104.0bn
against today's $128.6bn. The per-name test, which decides automatically, belongs to the dossier-side
build that supplies these facts (next).

**HOW VERIFIED.**

*Real inputs, from the committed pages.* AMZN:
- NTM EV/EBIT 23.3377 (Estimates ≥2026-10-06, `e10ed62223`);
- FY2028 EBIT consensus $183,485.95M;
- CIQ net debt $251,635M − $122,988M = $128,647M (Q2 Jun-30-2026);
- 10,903M diluted shares.

The hold leg computes **$380.95**, the figure the side-by-side of 2026-10-08 derived by hand. UBER
computes on its own page figures: 15.43x, $13,161.67M, $9,340M and 2,050.2M shares.

*Reachable.* The first cut was NOT reachable. A real `scenario-propose` → hand-edited R4 template →
`scenario-create` on AMZN found two defects, both fixed here:

1. **The create path dropped `ebit`.** It built every leg without the field, so `_run_r4` refused
   every R4 template. This is the unwired-capability class R3's create path was found in on
   2026-09-01.
2. **The tier gate knew only R1.** It refused an R1-versus-other disagreement only, so AMZN's page
   (the operator's R3 tag) passed an R4 record with nobody told. A forward recipe on the page that
   the record does not match is now refused.

A third gap was caught by the repo's own guard,
`test_every_scenario_input_field_is_settable_from_the_template`, on the full suite: `ebit` was
declared on `ScenarioInput` but no `scenario-propose` template cell could set it. The template now
carries an EMPTY `ebit` cell beside `eps`, never proposed, because it is the recipe's whole leg
driver. `record_legs_for_validation` (the supersede guard) also maps `ebit`. In a scratch root where AMZN's
page carries an R4 tag — the re-tag an operator would make — `scenario-create` then wrote a complete
R4 record:
- formula stamped;
- `ebit` on every leg;
- assumptions over `ebit` and `multiple`;
- CIQ net debt as the bridge.

*Tests* (`tests/test_r4_forward_ev_ebit.py`, 19):
- the hold leg on AMZN and UBER;
- the enterprise figures;
- the formula and axes;
- every refusal;
- `scenario-create` end to end in a temp root;
- the supersede guard's `ebit`;
- the tier gate, both ways (AMZN's R3 page refuses R4; a page and record on one recipe pass);
- a record without `ebit` writing no `ebit` key.

The committed `scenarios/_schema.json` is regenerated for the new field, +12 lines.

*Mutation.* Twelve mutants, all killed:

| mutant | tests failing |
|---|---|
| no dispatch | 15 |
| net debt added, not subtracted | 2 |
| shares scaled by 1e6 | 2 |
| a null `ebit` written | 2 |
| a stated EPS ignored | 1 |
| a non-positive EBIT computed | 1 |
| basis unchecked | 1 |
| a D&A fact ignored | 1 |
| create path drops `ebit` | 1 |
| supersede guard drops `ebit` | 1 |
| tier gate knows only R1 | 1 |
| enterprise figures left empty | 1 |

**BOUNDARY.**
- **Inputs:** the committed AMZN and UBER pages at main @55762d9f.
- **Consensus net-debt comparison:** the four names' Estimates and Financials exports on disk,
  measured 2026-10-08.
- **Units:** $M, and $ per diluted share.

**WHAT IT COSTS / WHAT IS ACCEPTED — WHAT IS NOT DONE, in order:**
1. **The dossier-side bridge.** CIQ net debt, the exit-net-debt rule run per name, the EDGAR
   cross-check and shares become facts the page supplies with no manual input. `scenario-propose`
   then emits an R4 template (it still emits basis `EV/EBITDA`, §5.0 row 10).
2. **The card and page render of an R4 leg.** The markdown table, the frontend card emitter and
   `uw-card.js` show EPS for R3 and nothing for `ebit` yet. Under the preview rule, and it MUST land
   before the first R4 record is committed, or that record's card shows every input except the one
   that produced its value (R3's 2026-09-01 lesson).
3. **The machine proposal.** The three conditions are written into the tagger. Condition 3 needs a
   STRUCTURED count of material non-operating quarters; today it is only prose in
   `quality.nonoperating_earnings`.
4. **The re-tags.** AMZN (R3 → R4) and UBER (`R2_NEEDED` → R4) are operator acts, made when (1) and
   (2) have landed.
5. **`basis_decomposition` reports nothing for R4.** It reads `eps`. It only reports and never
   refuses, so this is a missing readout, not a wrong one.
