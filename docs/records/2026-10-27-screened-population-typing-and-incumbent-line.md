---
id:
status: shipped
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# An issuer's line in the population no longer changes on a 90-day volume crossing, and a line its issuer registers as debt leaves the universe whatever the feed types it

**WHAT.** Data-integrity wave 2, lane L8, item 21: the two defects the 2,113 sign-off left open
inside the population (`docs/records/2026-09-01-population-signoff-2113.md`). Both are closed in
code. The 2026-10-16 population does not change.

1. **The incumbent line keeps its issuer's slot** (`universe.incumbent_lines`,
   `build_universe._one_line_per_issuer`).
   - One-line-per-issuer (#549) picks the highest-ADV line among an issuer's lines that clear
     every gate. ADV is a 90-day average.
   - The line the band's COMMITTED snapshot admitted now ranks first. ADV decides only among lines
     with no record, or after the incumbent has failed a gate.
   - The snapshot counts only when it is dated on or before the build's reference date, so a
     backdated rebuild is never steered by a population chosen later. Each band reads its own
     snapshot.
   - When the incumbent wins against a more-traded sibling, the loser's `duplicate_class` row
     names the incumbent and the snapshot date. Its source is
     `universe_snapshot.jsonl (the incumbent line)`, not `Polygon ADV`.
2. **A line its issuer registers as debt leaves at `non_common_equity`**
   (`vinci/resolver/instrument.py`, `EntityResolver.registered_line`, universe Axis 3).
   - The input is the cover page of the issuer's latest periodic report filed on or before the
     reference date. Its inline-XBRL `dei:TradingSymbol` / `dei:Security12bTitle` pair is a
     structured SEC field, keyed by the symbol, in the issuer's own words.
   - A title that names notes, debentures or bonds excludes the line. The deciding input is the
     title, stamped with the filing's date and accession.
   - The cover is read only for lines the feed types `CS` that clear every other gate.
   - Nothing else on a cover excludes anything: an unread cover, an absent symbol, a preferred
     line, LP units or an ADS of units changes nothing.
   - No drop stage was added, and no gate threshold changed.

**WHY.**

- **Item 2 of the sign-off record: #549's pre-registered falsifier fired.** Its record said
  that if any issuer's survivor changed between two consecutive weekly runs, the rule needed
  stickiness (keep the incumbent unless it fails a gate). Measured over every committed
  universe snapshot since #549, three issuers changed lines between consecutive builds. Only
  one was the volume rule:

  ```
  2026-08-24 (#553)  U-Haul enters the signed-off population as UHAL ($1.37B, its own class count)
                     UHAL.B is $11.00B, above the $10B ceiling, so it is no rival (it sits in the theme band)
  2026-09-22         UHAL.B closes at $54.89 -> $9.62B and enters the band; it takes the slot on ADV,
                     $22.1M/day against UHAL's $11.9M (retention row, run 2026-09-22-01), while UHAL
                     clears every gate
  2026-10-16         UHAL.B again, $18.4M/day against $10.1M
  ```

  The other two were renames: the internal id embeds the ticker, so a new id was minted (HLX→HOS
  on 2026-09-22, BRR→SVIA on 2026-10-16). That is a different mechanism, and it is NOT fixed here
  (see costs).
- **Item 1 of the sign-off record.** The feed types some debt `CS`.
  - Of the 5,324 lines Polygon's 2026-10-17 reference pull types `CS`, 58 name themselves
    notes, debentures or bonds.
  - ADAMK, a 9.600% senior note, sat in the primary population until 2026-09-01. It left only
    because ADAM out-traded it.
  - MCHPP sat in the primary population on 2026-08-24 and 2026-09-22 and was screened on 09-22.
    It is Microchip's mandatory-convertible preferred depositary, $1.74B on its own class count.
    It left on 2026-10-16 only because its sizing changed.
  - Typing by the feed's NAME was refused. "Our Bond, Inc. Common Stock" (OBAI) is the false
    positive that rule makes.

**MEASURED FIRST: what the 2026-10-16 population is.** These are the 2,065 members of the committed
`universe_snapshot.jsonl`. Each is classified from two deterministic fields:

- **Polygon type:** the 2026-10-17 reference pull.
- **SEC:** the cover page of its issuer's latest periodic report filed on or before 2026-10-16,
  read from EDGAR on 2026-10-27. 2,061 covers were read (2,055 distinct documents) and 2,461
  titles were on them.

| class (deterministic field) | members |
|---|---:|
| `CS`, cover registers the symbol as common stock | 1,931 |
| `CS`, cover title another equity form (subordinate voting shares, "Common", LP / trust units, rights-plan preferred tagged to the common's symbol: AVO) | 31 |
| `CS`, symbol not on its cover, or no cover read | 18 |
| `ADRC` (depositary receipt by Polygon's type) | 85 |
| **bond / note** (cover title) | **0** |
| **preferred** as the member's own line (cover title) | **0** (AVO is a rights-plan artefact on a common) |
| **ADR typed `CS`** (cover title an ADS) | **0** |
| warrant / unit (SPAC sense) / ETN | **0** |

- **Members whose OWN line is titled debt: 0.** The covers carry 87 debt titles, all belonging
  to OTHER lines of member issuers (their notes). On 2026-10-16 every one of the 58 debt-named
  `CS` lines fails the band, the $3M ADV floor or the share count before this gate. None is
  admitted and none is a de-duplication loser.
- **Foreign private issuers: 255 of 2,065 (12.3%).** These are members whose latest periodic
  report on or before 2026-10-16 is a 20-F or 40-F: 78 typed `ADRC` and 177 typed `CS`
  (direct-listed Canadian, Israeli, Greek-shipping and other FPIs).

**ADRs: WHAT THE CODE AND STATE INTEND.**

- **The code admits ADRs on purpose.**
  - `UniverseConfig.allowed_security_types = ("CS", "ADRC", "OS", "GDR")` since 2026-06-19.
  - The 2026-08-26 capability record notes that operating-company ADRs are not dropped.
  - #541 built ADS-denominated caps so that ADRs size correctly. It was one of the four changes
    the operator signed off at 2,113.
- **STATE row 4 gates FPI readiness (FPI1–FPI5) at the DOSSIER altitude only:** "gated on a
  non-US filer actually entering the book".
- **No record states in words whether a US-first fund's forward-validation population should
  contain FPIs.** They are 12.3% of it, and the dossier altitude cannot yet underwrite one
  (IFRS, 6-K, Section 16, foreign-currency workbooks).
- **Nothing was excluded.** The question is left as an operator decision in STATE §5.0.

**HOW VERIFIED.**

- **The replay reproduces the committed build exactly.**
  - `build_universe` was re-run offline on main's code at 2026-10-16, from the 2026-10-16 weekly
    run's own cache. That cache was APFS-cloned from the worktree that ran it, the TTL was
    ignored and the network refused.
  - Result: 2,065 members, the identical set, 0 caps differing.
  - Three per-ticker details lookups absent from that cache (BMMX, CTY, TCXB) replayed as failed
    lookups, which the builder already tolerates. Its `considered` count differs by 4, all
    dropped names, from a resolver index refreshed after the run. Membership is unaffected.
- **BEFORE → AFTER on this branch, same inputs, incumbent = the committed 2026-10-16 population**
  (what the next weekly will read):
  - **2,065 → 2,065. 0 names leave, 0 enter, 0 caps differ**, and the stats are identical stage
    by stage.
  - Every `CS` line reaching Axis 3 had its cover read: 2 documents fetched live, none
    unreadable. None is titled debt.
- **The U-Haul case on real data.** Same inputs, but the incumbent is the 2026-08-24 population
  (#553), the record U-Haul entered as UHAL. The ONLY difference is UHAL kept, UHAL.B dropped,
  0 caps differing. The UHAL.B row reads: "the incumbent line UHAL — admitted in the 2026-08-24
  population — keeps its issuer's slot while it clears every gate, though this line trades
  $18.4M/day against its $10.1M".
- **Fails first.** The U-Haul pin (frozen 2026-09-22 closes, ADVs and per-class counts) fails on
  main with `{'UHAL-B'} != {'UHAL'}`.
- **Pins.**
  - `tests/test_survivor_incumbent.py`, 7 pins:
    - positive: the incumbent keeps the slot;
    - negatives: no incumbent means the ADV winner; an incumbent that is also the ADV winner
      reads as an ADV win; an incumbent that fails a gate loses the slot (UHAL.B at its real
      08-24 close); a later-dated snapshot is ignored; bands don't cross; out-of-population rows
      are not incumbents.
  - `tests/test_registered_debt.py`, 9 pins over EIGHT REAL COVERS frozen verbatim
    (`tests/fixtures/cover_page_12b_titles.json`: Adamas, Brunswick, T-Mobile, Brown-Forman,
    Icahn, Coca-Cola FEMSA, U-Haul, Microchip) and Adamas's real filing index:
    - all 21 note titles read as debt; none of the 18 equity titles does;
    - BFB / UHAL.B / UHAL-B match;
    - ADAMK, absent from its cover, is not evidence;
    - the cover is the latest periodic report by the reference date;
    - the resolver reads the document its filing index names, cached forever;
    - through the real builder, a registered note that out-trades its common is not admitted
      while the common on the same cover is.
- **Mutations: 10 of 10 red on the intended pin.** Incumbent dropped from the rank key; no as-of
  bound on the incumbent; out-of-population rows read; cover gate disabled; symbols unfolded; no
  as-of bound on the cover; an absent title read as debt; "notes" dropped from the rule; a TTL on
  the filed document; the incumbent's row crediting ADV.
- **No paid model call.** The run used SEC and the frozen Polygon cache only.

**BOUNDARY.**

- **Population:** the primary band, 2,065 members, as of 2026-10-16. The theme band was not
  rebuilt by the weekly and its committed snapshot is still dated 2026-08-24. It is not part of
  any count here.
- **Polygon type:** the 2026-10-17 15:46–15:49Z reference pull, 13,271 rows, 5,324 of them
  typed `CS`.
- **Cover pages:** the latest 10-K/10-Q/20-F/40-F (or an amendment) filed on or before
  2026-10-16, from each issuer's RECENT submissions block, read 2026-10-27. 4 members have no
  periodic report in it: AYA, GORO, MDA, OGC.
- **Swap history:** every committed `universe_snapshot.jsonl` from c88962be (2026-08-24) through
  987d2b4e (2026-10-16), issuers present in consecutive builds.
- **ADVs:** 90 calendar days of grouped-daily bars ending at each build's reference date, from
  the cache.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **A note listed after its issuer's latest cover is not seen.**
   - ADAMK is that case: its 8-A12B is dated 2026-08-14, after Adamas's 2026-07-31 10-Q. The
     cover rule would NOT have caught the one debt line ever admitted. It catches it from the
     next 10-Q on.
   - Today stickiness protects an incumbent common from a fresh note's launch-week volume; a
     fresh note of an issuer with no line in the band is not protected.
   - FALSIFIER: a `CS` line admitted whose feed name is a note and whose symbol is absent from
     its issuer's cover. 0 on 2026-10-16.
2. **Each `CS` line that clears every other gate costs one filing document**, cached for good.
   - Cold: ~2,055 documents (the eight fixture documents are 1.1–7.8 MB each).
   - Warm: only covers filed since the last read. 1,803 of the 2,061 covers were filed in the
     91 days to 2026-10-16, and 6 in the last 7.
   - Free and SEC-paced, but it adds to a cold weekly run (row 31).
   - The lever if it bites: read covers only for issuers listing more than one SEC ticker. That
     gives up issuers whose only listing is a note.
3. **A cover can tag a symbol to the wrong title.** Mission Produce tags AVO to its rights-plan
   preferred. Only a debt title excludes, and 0 of 2,065 members' own lines carry one.
4. **A cover title is a text field.** It is classified by three words (notes / debentures /
   bonds), and the 2,461 member-cover titles carry no counter-example.
5. **The parser is a twin of `theme_intelligence.securities.parse_cover`.** The isolation
   boundary forbids sharing it.
6. **NOT FIXED here, reported:**
   - **Preferred typed `CS` (MCHPP) stays admissible.** The brief scoped exclusion to bonds and
     notes. Whether the allowlist's explicit PFD exclusion should extend to a cover-registered
     preferred is an open question, asked of the lane owner.
   - **A ticker rename mints a new internal id**, splitting one issuer's record. Measured: HLX→HOS
     and BRR→SVIA moved a population line. 5 members' latest cover still names the old symbol
     (HOS/HLX, SVIA/BRR, IA/ISSC, PLGO/FIHL, SKYD/PSKY).
   - **Per-class sizing admits a $1.2B class of an $11B company** (UHAL) to a ≤$10B band. That
     is #546's design, recorded as an observation.
7. **The ADR / FPI question is an operator decision** (STATE §5.0).
