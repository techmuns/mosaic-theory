---
id: 
status: recorded
date: 2026-08-19
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**FOUR FINDINGS FROM THE SMPL-VERDICT AND NFLX-SLEEVE WORK (2026-08-19).**

**1 — THE SEAL-MANIFEST WINDOW IS STRUCTURAL, NOT A ONE-OFF (read at the source).** The manifest
is keyed on TICKER, and `cli.py`'s supersede wrapper re-seals the live key CONDITIONALLY:
`if seal.is_sealed(live.verdict.status): man[live.ticker] = seal_entry(live.rationale or "")`.
**An incoming record that arrives `pending_analyst` skips that branch**, so the live ticker key
keeps the PREDECESSOR's entry — the very entry the line above just copied to the archive key.
Measured on SMPL: `man["SMPL"]` was byte-identical to `man["SMPL-2026-07-27"]` (678 chars,
`d621bcff…`) against a live rationale of `""`. **NOTHING SURFACES IT**: `seal.check_all` calls
`verify`, which returns `[]` immediately when `is_sealed(status)` is False, so an unsealed record
cannot fail its own seal check. **THE WINDOW: from any supersede whose incoming verdict is
unsealed, until the next sealed write — which then REFUSES**, naming a mutation the writer did not
make. Every future supersede of that shape recreates it; today's stale-entry count says nothing
about tomorrow's.
**AND THE REFUSAL MISATTRIBUTES, WHICH IS WHAT MAKES IT EXPENSIVE.** It fires on the person writing
a legitimate rationale and tells them the sealed text was MUTATED — an accusation against a write
that did nothing wrong, for a supersede that happened weeks earlier. The next person spends a turn
investigating their own edit. A guard that names the wrong actor costs more than one that says
nothing.
**UNLOCK — AND THE ONE-LINE FIX CARRIES THE DEFECT IT FIXES.** Re-sealing unconditionally seals an
unsealed record to **`chars: 0`**, and **zero reads as "sealed, empty" rather than "not yet
sealed"** — the absent-versus-zero class this repo has paid for five times (`no-record` vs
`cannot-read-record`, `filer-reports-none` vs `we-could-not-fetch`, CNXC's zero, the NM refusals,
the empty-store raise). **Keying the manifest on the RECORD ID avoids it by construction: a missing
key means NEVER SEALED, which is a different state from a key sealing nothing.** Recorded so the
cheaper fix is not chosen for being cheaper.

**2 — THE VERDICT VOCABULARY IS LOSSY.** `VerdictStatus` is
`pending_analyst | confirmed | overridden | passed | watch`. `confirmed`/`overridden` encode
AGREEMENT or DISAGREEMENT with a machine proposal — but when the lean is `mixed` the machine
proposes NOTHING, and **no status distinguishes decided-with-no-proposal from
decided-against-a-proposal.** That distinction survives only in the ledger payload
(`disposition: "no_proposal"`, `machine_lean: "mixed"`, `machine_proposal: null`). SMPL is the
live instance: `watch` is honest and INCOMPLETE. Recorded, not built — a sixth status is a
constitutional change, not a schema tweak.

**3 — THE `OPEN`-ROW INVARIANT, DESIGN ONLY.** Nothing checks that a name with an open ledger row
carries a filled verdict. A ledger `OPEN` with no matching `CLOSE` implies the record must NOT read
`pending_analyst`. Cheap and checkable; **it would have fired on the fund's ONLY position for two
weeks**, and only a hand read found it. Seven of eight superseded records were hand-filled and SMPL
was not.

**4 — THE TWIN VOCABULARY FORCES A BINARY THE FACTS DO NOT SUPPORT.** Re-tagging NFLX `quality` →
`overshoot` moved the same four twins from *kept compounding / re-rated to fair value* to
*recovered / went terminal* — which PROVES the sleeve reaches the prompt (#381 holds, the check was
informative either way). But **"Disney went terminal" is a stronger claim than "Disney re-rated to
fair value", and the second is more accurate**: Disney did neither. **This is the `AVOID_TERMINAL`
problem one layer over** — the quality book got `PASS` because "terminal" on a fully-priced
compounder would be a false record, and **the twin labels have no equivalent escape.** One live
instance. Recorded; **do NOT build a third label** on one case.
