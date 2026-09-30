---
id: 2026-09-30-a-multiple-names-its-denominator
status: shipped
date: 2026-09-30
prs: [659]
supersedes:
superseded-by:
---

# A multiple names the denominator it is struck on

**WHAT.** Two gaps in the dossier's valuation surface, both found by a real underwrite built on
BURL's `dossier.json` and reviewed by the team.

1. **The dossier published only TRAILING multiples** — `P/LTM EPS`, `EV/EBITDA (TEV/LTM)` — while
   every underwrite runs on forward earnings. An analyst asked for a forward P/E therefore had to
   source one OUTSIDE the dossier, and outside numbers arrive with no stated denominator. The
   underwrite used an external "~22.1x forward P/E", applied 22x to FY+2 at the exit, and reported
   the difference as **ZERO multiple change**. Now published, from the dossier's own data:

       P/FY27E (normalized) 21.77x     P/FY28E (normalized) 18.78x
       P/FY27E (GAAP)       22.37x     P/FY28E (GAAP)       19.17x

   The external 22.1x lands between the two FY27E figures — it was FY+1-struck. The three-turn gap
   to FY+2 is exactly what was reported as zero. Each row carries the `column` and `eps_basis` it
   came from, so two of them can never be silently compared across periods.

2. **The EV/EBITDA series' denominator is not the reported EBITDA, and nothing said so.** BURL's
   band implies a 19.3% EBITDA margin against 11% reported. The page read "9.0x, 8th percentile,
   near-floor", which is unreadable without knowing that the same TEV over REPORTED EBITDA is
   nearer 15.8x. The underwrite derived 15.6x by hand and localised the defect correctly; the
   dossier should not have made it do that.

**WHY THIS DISCLOSES RATHER THAN DISQUALIFIES, WHICH IS THE PART THAT CHANGED ON MEASUREMENT.**
The first design was to tighten `band_guards._MAX_MARKET_RATIO` so BURL's gap tripped the existing
coherence guard. **That would have been wrong.** The guard already exists and already works — VITL
fails it and is disqualified with the right sentence. Measuring BURL's gap in dollars: implied
EBITDA $2,352M vs reported $1,361M is $991M on $12.2B of revenue, the order of its annual rent.
The series is struck on something like EBITDAR — coherent, internally consistent, and simply NOT
what the label "EV/EBITDA (TEV/LTM)" implies. Tightening the bound would have thrown away a usable
anchor over data that is not broken. Only the measurement separated "differently based" from
"incoherent", and the instruments for those two are not the same.

**HOW VERIFIED.**

*The corpus, for the disclosure threshold.* Implied vs reported EBITDA margin across the 22
committed dossiers carrying both: 19 sit at or below 1.33x — most of that is the reported margin
being a whole-percent cell — with CNXC 1.33x and ROST 1.31x the honest top, BURL 1.75x, VITL 5.01x.
The threshold is set from that distribution, not chosen; it fires on BURL, CNXC, ROST and VITL and
is silent on the other 18. A line on every page trains a reader to skip it, and then it is not
there when it matters.

*The arithmetic it restores.* The disclosure computes 15.8x for BURL; the underwrite derived 15.6x
by hand (the gap is the whole-percent rounding of the reported margin). The engine now reproduces
independently what the analyst had to reconstruct.

*Mutation — six, all caught.* F1 estimate columns read from the "E" label suffix instead of the
`is_estimate` flag; F2 the column/row provenance dropped; F3 a negative forward EPS published;
F4 a missing price returning an empty list instead of UNKNOWN; F5 the disclosure never fires;
F6 the disclosure fires on everything. Sources restored byte-identical.

*Three regressions the e2e pins caught, all mine.* (a) Both render helpers return "" where they do
not apply, and an appended "" is a BLANK LINE — 26 committed pages went stale over names that
gained nothing. (b) `forward_multiples` serialised as `null` on every dossier, and
`refresh_dossier` compares serialized text, so a no-op refresh rewrote all 26 — the #302
"119 null keys" defect one module over, fixed with the same absent-vs-null rule. (c) After both,
exactly four names legitimately change. No unit test could have seen any of the three.

**BOUNDARY.** Measured 2026-09-30 off `55b791e9`.
- *22 names / 19 at or below 1.33x / BURL 1.75x / VITL 5.01x*: population = committed
  `data/dossiers/*/dossier.json` carrying BOTH an EV/EBITDA band with `implied_ebitda_margin` and
  an "EBITDA margin" LTM cell; unit = names; ratio = implied ÷ reported margin.
- *21.77x / 22.37x / 18.78x / 19.17x*: BURL at ITS OWN committed price $256.85 (2026-09-22), not
  the $268.12 the underwrite used — the two are different as-ofs and the multiples move with them.
- *15.8x vs the underwrite's 15.6x*: same TEV, reported-EBITDA denominator; the difference is the
  whole-percent rounding of the 11% cell.
- *4 pages regenerated*: BURL, CNXC, ROST, VITL — the names whose rendered output changes. JSON
  byte-identical for all four; only `dossier.md` and its frontend mirror move.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **THIS PR CARRIES FOUR REGENERATED `dossier.md` FILES.** A renderer change that adds a line makes
  the committed page stale, and three e2e pins refuse that. The render path is deterministic with
  no LLM phase, so regenerating is one call and no re-assembly is implied — but it IS derived data
  in a code PR, so it is stated here rather than left to be noticed. It also corrects pre-existing
  drift: `frontend/monitor/2026-09-22.json` still carried a `2026-08-24` window against a source
  re-cut to `2026-09-22` in #657.
- **The forward multiples reach only RE-ASSEMBLED names.** `forward_multiples` is built at assembly
  time, so every committed dossier renders no such row until its next pass. The disclosure, by
  contrast, reads fields already present and lands immediately. Two halves of one fix with two
  different arrival dates.
- **NTM is not computed.** FY+1 and FY+2 are published because the dossier can state them exactly;
  an NTM blend needs a fiscal calendar the dossier does not carry, and inventing one would
  reintroduce the unstated denominator this record exists to end. An analyst can build it from the
  two published points, which is the honest division.
- **The disclosure threshold is a relative gap, not a basis detector.** It says the two numbers
  disagree, not why. BURL's rent hypothesis is arithmetic consistency, not a proven attribution.
- **NOT FIXED:** `P/LTM EPS` is struck on GAAP LTM EPS ($11.13, not the normalized $8.95) and its
  label says neither — a third unstated basis, found in the same review and left alone here.
