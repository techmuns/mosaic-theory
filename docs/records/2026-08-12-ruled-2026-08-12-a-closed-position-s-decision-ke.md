---
id: 
status: shipped
date: 2026-08-12
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**RULED 2026-08-12 — A CLOSED POSITION'S DECISION KEEPS ACCRUING (decision-queue item 1), AND THE
HEADLINE MUST DECOMPOSE.** The question was whether a decision closed early still counts toward the
spread. **It does, and nothing changed about that:** the spread measures the DISCRIMINATOR, and
closing is a capital decision that does not retract the call — the same rule the scoring harness
already followed. What the ruling does NOT license is a headline the reader cannot take apart. On
2026-08-11 the book read **+9.54 pp**, and **+29.00 pts of the BUY leg came from IT — a position
closed at the entry price on 2026-07-21, realized P&L +0.0%.** Over the rows still held the same
spread is **−1.56 pp**. THE SIGN FLIPS, so both now print, neither labelled the "real" one: the
headline answers *was the call right*, the second answers *did the book hold it*. Keyed on the
DECISION's entry_id, never the ticker — SMPL is closed AND re-entered, so a ticker-keyed flag would
mark the live re-entry closed and silently drop it from the held figure.
**THE SAME SPLIT NOW ON THE SCORING REPORT (2026-08-12).** The monitor showed the decomposition
from #418 and the scoring report — the LP-facing artifact — did not, which is the surface-gap #378
was about: a number correct in one place and absent from the other. `ScoreReport` now carries
`n_closed` / `buy_avoid_spread_open_only` and renders them beside the headline, computed off the
SAME `primary` set so the two are comparable by construction. The headline is unchanged; the ruling
is unchanged. **The as-of filter on closes was applied from the start here rather than re-learned**
— #418's P1 (a close dated after the scoring date has not happened yet) transferred directly.
**A COUNT THAT COULD CONTRADICT ITS OWN BREAKDOWN, found reviewing my own diff.** `n_closed` was
summed over `primary` — every screen-origin resolved row — while the rendered "still held" figure
subtracted it from the two LEGS. Origin and sleeve are ORTHOGONAL, so a quality `PASS` can carry
screen origin (the model permits it), landing in `primary` and in neither leg; closing one printed
**"1 still held" beside "BUY n=1 · AVOID n=1"**. Counted over the legs the spread actually uses now,
so the line cannot disagree with its own breakdown. Also: the ledger is read ONCE per scoring run
(`iter_ledger` re-validates every row since #417, so a second scan doubled that for nothing), and
the as-of filter now REQUIRES a dated close rather than treating an undated one as already-happened
— the schema refuses an undated close outright, so the branch was unreachable and now says so.
**THE LIVE REPORT STILL PRINTS NOTHING, and that is correct:** zero verdicts have resolved (the
first BUY horizon passes 2027-01-16), so the split has nothing to decompose and stays silent. My
earlier objection — that this was "untestable scaffolding" — was too strong and is worth correcting:
the ARTIFACT is blank, the LOGIC is exercised on fixtures where rows resolve, exactly as
`test_scoring_close_rows.py` already does. *"The artifact is blank" and "the logic is unverifiable"
are different claims.*
**AND THE REALIZED BOOK IS TYPED (item 4).** It reached the snapshot only as free-text `notes`, so
the one view saying what the fund actually EARNED was unreadable by anything not parsing English,
while the marked-to-market rows beside it were fully structured. `MonitorSnapshot.realized` now
carries it, and the note line is RENDERED from the typed row (`RealizedRow.note`) so display cannot
drift from data — the standing rule that display formatting is never load-bearing.
**LOOK-AHEAD IN THE HISTORICAL BOOK — REVIEW P1 ON #418, AND IT WAS BROADER THAN REPORTED.** The
monitor's price path carefully refuses a future bar; the LEDGER path did not. `monitor --ref <past
date>` counted every close in today's ledger regardless of when it happened (at ref 2026-07-20 it
reported 2 closes against a truth of 0), AND — the half the review did not see, found by comparing a
re-run against the original file — it counted every DECISION too, marking SMPL's 2026-08-04
re-entry into the 2026-07-20 book with **`days_elapsed: -15`**, a position that did not exist yet.
Both halves now read the ledger as of the snapshot date (`monitor.decisions_as_of`,
`pair_closes(as_of=)`, `closed_decision_ids(as_of=)`), filtering AFTER pairing so the
unpairable/duplicate-close refusals still see the whole ledger. **VERIFIED BY REPRODUCTION:
re-running 2026-07-20 today now returns the original day's three rows and its spread to full
precision** (0.1442638831149694 both ways), with zero realized rows — both exits were still in the
future then.
**AND THE BOOK HISTORY HAD NO WRITE PROTECTION.** `write_snapshot`'s docstring claimed the history
is "never overwritten across days" and nothing enforced it — I silently replaced the committed
2026-07-20 snapshot while testing, which is how the decision look-ahead surfaced. It now refuses to
rewrite a SUPERSEDED day. The rule is deliberately "superseded", not "not today": the normal daily
run resolves to the LAST TRADING DAY, so a not-today rule refuses the routine re-run — the first cut
of the guard did exactly that.
**A PIN THAT COULD NOT FAIL, caught by mutation for the third time in this sequence.** The
re-entry guard was asserted against the COMMITTED ARTIFACT, which is static — mutating the keying
does not regenerate it, so the test stayed green while the logic was wrong. The keying moved to
`monitor.closed_decision_ids` and is now exercised against the real ledger, with the artifact pin
KEPT beside it: one catches the logic, the other catches what shipped. *An artifact pin proves what
was written; it cannot prove what the code would write next time.*

**~~OPERATOR TO-DO: decide whether the frozen baskets become a committed artifact.~~ DECIDED
2026-08-12 — THEY ARE COMMITTED** (`data/themes/baskets/<driver>.json`), reversing the standing
`.gitignore` rule for that artifact only. The reason the rule changed: Stage-4's entire product is a
number that accrues over CALENDAR TIME and its input existed on exactly ONE machine, so on any other
checkout the accrual could not be computed at all — two themes passed their 30-day horizon with
their diagnostics still reading "0 days forward from freeze" for precisely that reason. The
reconstruction path (#412) works ONLY for hold-none freezes, so the first RATIFIED theme would have
had no durable record of its BUY leg's entry dates anywhere.
**SCOPED, AND THE SCOPE IS PINNED.** The ratification LEDGER stays git-ignored — it is the analyst's
raw dispositioned worksheet output and committing it was not what was decided; a test asserts the
ledger and `data/forward/` are still ignored and that allowing `data/themes/` did not open the whole
directory. The baskets qualify under the private-repo rule as DERIVED analysis: tickers, dates,
cohorts and layer labels only — no verbatim filing text (`watchlist_triggers` is empty by
construction and pinned so), no CIQ, checked on the FILES.
**AND THE RATIFICATION LEDGER IS COMMITTED TOO (2026-08-12, second decision).** The basket says
which names are in which cohort; the LEDGER says WHY, in the analyst's own words, one appended row
at a time. `--ledger` was REQUIRED and ARBITRARY, so the dispositions went wherever the command line
pointed — which was somewhere git-ignored. It now defaults to `data/themes/ledgers/<driver>.jsonl`,
and an explicit `--ledger` still wins for ad-hoc runs (pinned that it does NOT also write the
canonical file: two ledgers for one freeze is two records of one judgment). Only the LOOSE
`forward_*` names stay ignored.
**THE THREE JULY 2026 LEDGERS ARE GONE AND ARE NOT RECONSTRUCTED — deliberately, and pinned so the
gap is not later filled in quietly.** A ledger is an APPEND-ONLY record whose value is that it
records what was appended and WHEN; a rebuild from the published mirror would carry one synthetic
timestamp for every row and no correction history, and committing that as "the ledger" would
misrepresent the artifact at the moment it starts being trusted. Their dispositions survive in the
mirrors (`rationale`, `gradeFact`, `accession` per name) — the honest surviving record, named as
such. **What was lost is the judgment; what remains is the conclusion.**
**MAKING THE LEDGER DURABLE CREATED A TORN WRITE — review P1 on #424, and the lesson generalises.**
The ledger append ran BEFORE the basket write, and the basket write can REFUSE (the #422 supersede
guard). So a refused re-freeze left the now-COMMITTED ledger holding dispositions for a basket that
was never frozen, and the retry appended the same judgment a third time: measured 1 row, then 2,
then 3. **The durability decision changed the cost of a side effect the write order had always
had.** Fixed by preflighting everything that can fail (`assert_basket_writable`, side-effect-free)
before any append, so the ledger and basket land as ONE successful freeze; the NOT-READY early exit
now writes nothing either, since an un-frozen tier should not record partial judgment.
*When an artifact becomes durable, re-read every path that writes it — the ordering that was
harmless while it was scratch is now the ordering of a permanent record.*
**AND A FIFTH PIN ASSERTING THE WRONG PROPERTY**, same family as the other four: the preflight's
no-side-effects test asserted the FILE was absent, so a mutation that `mkdir`s the parent stayed
green while the check touched the tree. Asserted on "creates nothing" instead of one visible
consequence of it.
**ONE PIN RETIRED BY DESIGN, recorded rather than deleted:** #412's P2 pinned that `--worksheet`
without `--ledger` must be refused. That half is now the NORMAL path — it is the whole point of the
default — so it was removed with its reason written where the pin used to be. The reverse (a bare
`--ledger`, nothing to append) still refuses.

**EVERY COMMITTED BASKET STATES ITS PROVENANCE**, because a basket written by the freeze and one
RECONSTRUCTED from the published mirror hold the same names and are NOT the same evidence. All three
today say RECONSTRUCTED — the freeze-time files were local-only and are gone. The freeze now writes
the canonical file itself, and `themes-forward --from-baskets` re-measures from it (preferred over
`--from-mirror`, which recovers from a summary and refuses a BUY leg).
**A WRITE THAT ESCAPED ITS CONFIG, caught by the suite within minutes.** The canonical path first
resolved from `Path.cwd()`, so an existing CLI test freezing a tmp worksheet wrote its four
synthetic names straight over the real committed basket in the repo. Keyed on the configured data
dir now, like every other durable artifact here, and the CLI test redirects config to a tmp tree.
**A COMMITTED BASKET WAS STILL SILENTLY REWRITABLE — review P1 on #422.** Every later
`themes-forward --worksheet …` for the same driver wrote a newly frozen object over the same
filename: measured, re-freezing defense moved `entry_dates` from {2026-07-03} to {2026-08-12},
shifting the forward window's start by 40 days with nothing said. The append-only ledger does not
protect this artifact, and committing it made the rewrite WORSE — the file now looks authoritative.
**This is the same class as the monitor-snapshot overwrite fixed hours earlier (#418), and this
module did not learn from it.** A second freeze now REFUSES; `--supersede-basket` archives the
existing basket under `baskets/archive/<driver>-<its freeze date>.json` first, so a supersession is
never destructive. A HOLE IN THAT FIX, found by reading the archive name back: the freeze timestamp
is DATE-ONLY, so two supersessions in one day collided and the second overwrote the first archive —
disambiguated, because re-dispositioning a tier twice in a session is normal.
**AND `--from-baskets` ACCEPTED ANY DRIVER (P2).** Passing the defense basket with
`--driver ai-datacenter` printed an AI-datacenter header over 108 defense names and measured them.
Unlike the mirror — which carries only a human label and can therefore only WARN — this artifact
holds the canonical registry key, so the mismatch is CHECKABLE and is now refused.
**AND THE FOURTH PIN-THAT-PROVED-NOTHING in this sequence, same root cause each time:** the
round-trip compared `write_baskets(...)` to `baskets_path(...)`, two values that MOVE TOGETHER — 
point the helper back at cwd and both change identically while every write lands in the repo. The
lesson generalises past artifacts: *a pin that compares two outputs of the same broken assumption
cannot fail; assert the property, not the agreement.*
