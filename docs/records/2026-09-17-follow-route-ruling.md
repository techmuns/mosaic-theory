---
id:
status: shipped
date: 2026-09-17
prs: [627]
supersedes:
superseded-by:
---

# WLK follows the trade book though the screen also ranks it — by a stated route ruling

**WHAT.** A follow entry may carry `overrides_screen`: a route ruling, the operator's stated
decision that the follow's book governs a name the screen ALSO ranks.

- **Without a ruling**, a name on both routes still refuses to assemble. The refusal used to suggest
  "exclude the name from the ranked queue", a mechanism that does not exist. It now names the ruling
  field.
- **With a ruling**, `_finalist` returns the follow's book. The screen's own candidate record stays
  the data source, and the page's main body opens with *ALSO A CURRENT SCREEN CANDIDATE at rank N —
  judged under the '<book>' book, not 'overshoot', by operator ruling: … Follow reason: …*
- **Both follow-list readers** refuse a blank ruling, and a ruling on a name followed under
  overshoot, since there is nothing to rule on (`vinci/dossier/assemble.py` `_follow_entry`,
  `vinci/followed.py` `follow_records`).
- **The ledger side:** `log-verdict <screen candidate id>` refuses when that ticker is followed under
  another book (`vinci/cli.py` `_screen_id_book_conflict`), before the ledger write.

WLK is the first ruled name: candidate `WLK-screen2-20260824`, rank 183 in the 2026-08-24 queue,
followed under `ultra_short_term`.

**WHY.** A screen candidate id seals a screen-origin row with no sleeve, which reads as overshoot
and counts in the PRIMARY spread. The page's copy-paste command names exactly that id. So once WLK
could be assembled under the trade book, the likely way to log its verdict would put it into the
fund's proof metric under a book it is not judged in, and the ledger is append-only.

**HOW VERIFIED** (scratch checkouts; the ledger commands ran on COPIES of the store with the
committed candidate and ledger snapshots loaded, never on the working DB):
- *Assembly, live EDGAR, no LLM:* WLK came out `sleeve: ultra_short_term`, `rank: 183`, with the
  ruling as caveat 1. It also carries the loud "pull CIQ for WLK" caveat: the canonical Drive folder
  is empty.
- *Ledger, `main` (control):* `log-verdict WLK-screen2-20260824 --verdict BUY …` wrote
  `V-WLK-screen2-20260824 | origin screen | sleeve null | BUY`, a screen-origin overshoot BUY.
- *Ledger, this PR:* the same command refused, naming the ticker route, and the row count stayed 6.
  `log-verdict WLK --verdict PASS …` wrote `V-WLK | followed | ultra_short_term | PASS | 10d`, and
  the screen-id command refused again afterwards.
- *Pins:* ruling → follow's book with record kept and both routes named; blank or non-string
  ruling refused; default-book ruling refused; both readers refuse the same shapes (matched on the
  ruling's own message); guard unit + "before the ledger write" structural pin; an end-to-end
  refusal through the real parser on a copy of the committed snapshots, derived from the committed
  follow file (WLK today) with store and JSONL unchanged; the committed ruled candidate assembles
  under the follow's book.
- *Mutation, bytecode caching off:* finalist ignores the ruling; ruling path keeps overshoot; ruling
  path drops the note; either reader accepts a blank ruling; either reader accepts a default-book
  ruling; guard inverted; guard not called. All 9 killed.

**BOUNDARY.** Row counts are of the scratch store copy's `decision_ledger` table, 2026-09-17. The
copy was taken from the local working DB, which lacked the committed `V-GOOGL` row and the
2026-08-24 candidates until they were loaded from `data/snapshots`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The page's copy-paste command still names the screen
candidate id for WLK. The command now refuses loudly and names the ticker route, but the page does
not yet suggest the right command. A render change, reported rather than folded in.
