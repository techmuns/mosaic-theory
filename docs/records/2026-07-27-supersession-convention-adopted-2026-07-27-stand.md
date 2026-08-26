---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

19. **SUPERSESSION CONVENTION — ADOPTED 2026-07-27 (standing).** Verbatim:
   *"A withdrawn or closed verdict may be superseded by a reissued record; the outgoing record is
   archived, sealed, publicly rendered and bidirectionally linked; a live position is never
   superseded, only amended; supersession never touches the ledger."*
   **MOTIVATING CASE:** SMPL's rationale reached **450 words of which 330 were amendment** — and
   three-quarters of that was construction-era PROCESS (a staleness alarm, a machine refresh, a
   re-verification), not investment judgment. Amending further would have buried the thesis under
   its own maintenance history, and the seal rightly forbids editing any of it. The reissue gives
   a reader a clean current record **without deleting or rewriting one recorded word**. Executed:
   `SMPL-2026-07-21` archived (its 3 tags, class labels, superseded note and construction banner
   all travel with it); live `SMPL` reissued at 2026-07-27 with **zero amendment tags**, ratio
   **3.8341 PASS** at the same 10.53 spot, legs unchanged, facts read from the archived record
   rather than retyped.
   **MECHANISM:** `vinci scenario-supersede` — one instrumented path, the scenario-refresh
   precedent. FOUR refusals, each pinned by proving it fires: a LIVE position (confirmed with no
   close row), a ticker mismatch, an incoming record already pointing elsewhere, and any
   difference between the archived copy and its original beyond the `superseded_by` pointer.
   **SEAL KEYING, decided here:** the manifest is keyed by ticker, so the archived record takes
   its ARCHIVE KEY (`SMPL-2026-07-21`) and the live ticker key is RE-SEALED at the new rationale —
   the "deliberate, reviewable act" vinci/seal.py names, performed once and atomically inside the
   command rather than by hand.
   **SCOPE, both halves pinned:** archived records LEAVE the live set (audit / monitor / spread
   read `scenarios/*.json`, which does not recurse into `archive/`) so they can never be scored or
   counted twice; and they STAY in the seal sweep (`seal.load_all_sealable`) so superseding can
   never become a way to move a sealed rationale out from under the seal.
   **LEDGER UNTOUCHED** — verified: SMPL still carries exactly its decision row and its close row.
   *Consequence recorded rather than fixed:* the ledger's `underwrite_ref` still reads
   `scenarios/SMPL.json`, which now holds the REISSUED record. The pointer is one hop short, not
   wrong — a reader following it lands on the live record and walks `supersedes` back to the one
   that justified the row. Left as-is because the ledger is append-only and the chain resolves it.
   **KNOWN REGRESSION, stated not smoothed:** `vinci audit r1` reads SMPL as
   `*** NO GATE — new exposure` again, where the superseded record read
   `fired — discharged 2026-07-26`. Cause: the discharge reader keys on a dated `[verified …]`
   TAG, and the reissued record states its bear-state evidence as METHOD PROSE — which is what the
   reissue brief required (evidence, not amendment). The verification did not disappear; the
   classifier cannot see it in this shape. QUEUED: teach the discharge reader a structured
   verification field, or re-verify the reissued bear leg with a dated tag.
