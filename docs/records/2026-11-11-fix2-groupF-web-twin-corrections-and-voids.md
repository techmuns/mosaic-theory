---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# The web twin of the ledger's corrections (RF-D7) and voids (operator ruling 2026-11-11, GOOGL): the page reads a decision at its correction, and a voided decision leaves the live book, the counts and the card, is shown once in an audit tier, and its sealed rationale carries one line saying it was voided

**WHAT.** The pages read the ledger through two twins of `vinci.monitor`, because neither may
import `vinci`. One is `frontend/build.py`'s `_ledger_join`, run by the Cloudflare build step. The
other is `frontend/lib/snapshots.js`'s `_loadLedger`, run in the browser.
- **Corrections (RF-D7; the VRRM half, held since #980 and kept as it was).** A decision that a
  CORRECTION row names is read at the corrected entry.
  - The decision log's and the dossier's entry cell reads "Entry (corrected)", and a collapsed tier
    shows the sealed entry and why it is not read (`frontend/lib/correction.js`).
  - An underwrite card's foot line says the ledger reads the entry at the correction, beside the
    sealed one.
- **Voids (GOOGL).**
  - **Build twin.** `_ledger_join` marks a voided decision `_voided`; it does not drop it, so the
    record it belonged to is still found. `_scenario_card` then carries no ledger verdict for it
    (its own or a predecessor's) and emits `voided` (`entryId`, `voidId`, `ruledOn`) instead.
  - **Page twin.** `_loadLedger` leaves a voided decision out of `entries`, so it is out of the
    counts and every per-book group. It returns the decision once in `voided`: the sealed entry,
    its correction, the ruling, the reason, and the result to date the void sealed.
  - **Decision log.** A collapsed `ds-voided` tier shows each voided call once. It is force-opened
    in print with every other `<details>`.
  - **Card.** The pill reads "verdict voided", never BUY. The Entry cell reads "— voided", and the
    foot line points to the decision log's audit tier.
  - **Dossier.** The Logged-verdict block says the verdict was VOIDED by the ruling, never "no
    verdict logged yet".
  - **The Brief's banner** (operator, 2026-11-11: "Approve + add a banner (Recommended)"). One
    line above the sealed rationale reads: "This verdict was voided by the operator's ruling of
    2026-11-11 — the text below is the sealed record, unedited." The date is the void row's own
    `ruled_on`. The sealed text itself is untouched.
- **The web reads no date.** In the Python readers a void is in effect from its `ruled_on` (the
  operator, 2026-11-11: "From 2026-11-11 on (Recommended)"; #984 round 1): a report cut before
  the ruling keeps the decision. The twins key on the void row's PRESENCE instead, which is the
  same answer on every page.
  - A page shows the book as it stands now.
  - #984's writer refuses a ruling dated after the void's own append, so every committed void is
    already in effect on the day any page is built.
  - The past monitor days the web mirrors are the Python monitor's own committed files, and the
    twins never recompute them.
- **What moves on `main` now.** The committed ledger holds the two corrections and no void until
  V2. Rebuilt on it, `frontend/scenarios/GOOGL.json` and `GOOGL-2026-08-17.json` gain
  `ledger.correction` (R-GOOGL, 340.65 on 2026-08-27): GOOGL's card states the corrected entry
  and still reads BUY. VRRM has no underwrite card; its correction shows on the decision log and
  its dossier. No other frontend file moves.

**WHY.** The operator's ruling of 2026-11-11 on GOOGL: "we want to remove the buy card/ buy
verdict altogether given it was done based on really old and wrong data and we dont want this buy
verdict to interfere in future at all". The order is V1 (the void's code, #984) → V3 (this) → V2
(the append), so that the web never shows a voided BUY (coordinator, 2026-11-11). The preview,
collapsed and force-open, was approved with the banner added.

**HOW VERIFIED.** See the PR's "Cross-setup validation (deterministic)".
- **Pins** (`tests/test_web_twin_corrections_and_voids.py`, 10):
  - each twin against `monitor.apply_corrections` + `monitor.decision_rows`, on the committed
    ledger and on it with GOOGL's void (2 × 2);
  - the decision log end to end;
  - GOOGL's committed page with the banner;
  - the banner's negative pin;
  - code review round 0's three: a newer void never hides an older live row the record owns; a
    record page names only its own voided call; a borrowed correction never speaks for a different
    entry.
- **Where the void row comes from.** The voided ledger is the committed one plus the X-GOOGL row
  that the real `vinci void-decision V-GOOGL` wrote in #984's dry run, on a backup of the primary
  store (`tests/fixtures/ledger_void/x_googl_dry_run.jsonl`). Once the void is committed, the pins
  read the committed row instead.
- **Fail first.**
  - On `b377795e` (V1's head, without this frontend), 6 of the first 7 fail, and the negative pin
    passes there, as it should. The two committed-ledger twin pins fail because the base twins
    read the corrected decisions at their sealed entries.
  - With only the banner removed, only its own pin fails.
  - Review round 0's three each fail on the source before its fix.
- **Round 0 also found the suite red.** Three existing checks broke on this change's own edits: an
  import's line position and two call-site strings in `tests/test_record_legibility.py` and
  `tests/test_log_command_id.py`. They are brought to the new signatures, and they still check
  what they checked.
- **Preview** (the frontend built over the voided ledger, served locally).
  - GOOGL's dossier, collapsed: the banner appears once, above the sealed thesis, and no BUY pill
    is on the page.
  - Force-open (every `<details>` opened, the print state): 7 tiers, the banner still once, and 0
    `undefined`, `NaN` or `[object Object]`. The only "BUY" is the sidebar's description of the
    BUY−AVOID spread.

**BOUNDARY.**
- The committed ledger is 9 rows at `173b4818` (two CORRECTION rows, no VOID).
- The void row is the dry run's of 2026-11-11: `X-GOOGL`, `ruled_on` 2026-11-11, marked 288.15 on
  2026-11-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The standalone card's "Verdict as recorded" expander shows the sealed text without the line.**
  The operator asked for ONE line on the dossier Brief, and the card already says the verdict was
  voided twice, in its pill and its foot line.
- **This PR is built on V1.** Its pins need V1's readers. It is cut onto `main` once V1 merges,
  and merges before the void is appended (V2).
