---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier and is dated in the body. The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **THE CALLS TAPE — scoring a public commentator's stated calls, and a parser that had been

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **THE DEFECT.** `tracker.py`'s `parse_target` took `s.split("-")[0]` as the first number, so a
    target written with a leading minus began with the empty string, `float("")` raised, and a bare
    `except Exception: return None` swallowed it. Every negative percentage therefore scored as *"the
    author named no target"* — indistinguishable downstream from a post that genuinely named none.
    **Measured on the corpus: 40 of 628 pct targets begin with a minus; 13 carry a bias agreeing with
    the sign and were resolvable all along.** One of them, $HIMS `-30%` of 2025-12-22, was actually
    TOUCHED — a correct call scored as an absent one. — *verified by running the OLD and NEW parsers
    over all 3,433 named targets in the committed corpus: 13 newly resolved, **0 prices moved**, and
    the 347 newly-refused rows are all `no_bias`, which tracker.py never scored anyway because it
    filters to bullish/bearish before parsing. The regression tests go RED on the old extraction
    (7 of 15 fail) and green on the fix.*
  - **Every non-resolution now carries a REASON** (`absent` / `qualitative` / `sign_conflict` /
    `no_bias` / `no_entry` / `unparseable`). The bug was never only the regex: it was five different
    facts about the author collapsing into one silent `None`.
  - **A stated direction that contradicts the stated bias is REFUSED, not coerced.** $QQQ of
    2026-02-13 is `bias=bullish` with `target=-10-15%` — the post calls that drawdown the downside
    branch *if* his signals flip. Forcing it through the bullish formula invents a target 10% ABOVE
    entry, a number the author never wrote. This is the spec's "worst case flips polarity with his
    position" trap, met at the parser rather than downstream. 21 rows.
  - **THE CONVENTIONS ARE UNCHANGED, and that is load-bearing.** Entry is the OPEN of the next
    trading day (never the post-day close — look-ahead that manufactures alpha out of the author's
    own timing); returns are signed by bias; an unelapsed horizon is OPEN and excluded; the 63-day
    default is FLAGGED wherever applied; SPY is the benchmark, and both legs end on the COMMON LAST
    BAR (`vinci/eod/features.py`'s lesson, ported deliberately). — *verified by transcribing
    tracker.py's main loop line-for-line and running BOTH over the same Polygon bars: **73 of 76
    hand-labelled calls identical, 3 differing only on `target_px`/`target_hit`** — exactly the
    authorised fix, nothing else.*
  - **ACCOUNTS ARE DATA** (`vinci/calls/accounts.py`). One directory per handle under `data/calls/`,
    an index DERIVED from each account's own `meta.json` so it cannot drift, and every read in the
    view namespaced by handle. Adding a second voice is a directory drop plus `vinci calls accounts`
    — no route, view or schema change. The selector is built from the index, not hardcoded.
  - **ONE SCREEN, NOT THREE** (operator decision, overriding the first design). Calendar, posts and
    chart are three panes of a single view; keys move FOCUS (day → post → cashtag) and the chart
    re-draws for whatever is focused. The URL still carries the full selection so a call is
    linkable, but it is written with `history.replaceState` — assigning `location.hash` fires
    `app.js`'s router, which re-renders all of `#main` and would tear the screen down on every
    keystroke. **A labelling tool that loses your place every few seconds does not get used.**
  - **Candles landed in `lib/exhibit.js` WITH their consumer**, per that file's own standing rule
    ("Not shipped unused"; extension points ship "when a real consumer lands — not before"). A pin
    enforces it: `test_calls_exhibit.py` fails if the primitive exists with no view drawing candles.
    `candleDomain` deliberately does NOT floor at zero the way `lineDomain` does — zero is
    meaningful for a margin, not for a price — and it pins an out-of-range target into view, so a
    chart cannot imply the target was never approached by leaving it off the axis.
  - **PRICES ARE FETCHED SERVER-SIDE, and the spec asked otherwise.** `APP_SPEC.md` has the page
    call Polygon on chart open; that would put `POLYGON_API_KEY` into client JavaScript and break
    the read-only mirror discipline stated twice in the code. Bars are pulled by
    `vinci calls fetch-bars`, committed, and mirrored — the path every other number on the
    dashboard already takes. Cost, stated on the page: prices are as of the last fetch, not live.
  - **NO AGGREGATE IS PUBLISHED.** At 83 hand labels against 8,102 machine ones, a headline
    hit-rate would describe the 55%-accurate labeller, not the author. The Scoreboard ships as a
    `conditional` stage — the app's existing vocabulary for "built when its trigger fires" — with
    the trigger stated on the page: ~500 hand labels.
  - *Real runs: 214 tickers fetched (95,592 bars; 3 empty — BRKB/DOGE/SPX, delisted or an index);
    3,889 directional calls scored (3,375 CLOSED, 349 OPEN, 154 NO_PRICE_DATA, 11 NO_ENTRY_BAR);
    browser-verified at 1760px with every rendered readout value checked against `results.jsonl`
    field-by-field, and all five overlays asserted present in the emitted SVG.*
  - **Two defects found by that browser pass, both fixed:** a deep link
    (`#/calls/<h>/<date>/TSLA/<id>`) opened the right DAY and then focused whatever was first, so a
    shared link pointed at the wrong chart silently; and the label chip prefixed `$` onto every
    target, rendering `$+12.33%` — a currency mark on a relative move.
  - **SECOND PASS (2026-08-25) — the descending-range bug, now authorised and fixed.** A range was
    read POSITIONALLY: the second number when bullish, the first when bearish. That is only "the
    high end vs the low end" while the author writes ranges ascending, and **88 of the corpus's 621
    ranges are descending** ("$TSLA 210-200", "$NVDA 120-118"). On those, a bullish call was handed
    its LOWER bound and a bearish call its HIGHER one — the target was easier to hit in BOTH
    directions, i.e. the error ran in the direction that flatters the author. Now read by VALUE.
    — *measured on the corpus: 88 targets moved, 55 of them on scored rows, **4 `target_hit` flips —
    all four from HIT to not-hit**, none the other way. Corpus hit-rate 74.4% → 74.2%. The corpus
    pin now asserts that the ONLY prices allowed to move are descending ranges, and that each
    resolves to its true high/low end.*
  - **AN AUDIT OF THE BUILD BRIEF AGAINST THE REAL DATA found four things the brief never said**,
    two of which were live defects:
    - **`bias: "mixed"` exists on 336 rows and the editor could not express it.** The bias control
      was built from the brief's enum (bullish/bearish/neutral/none). Opening a `mixed` row and
      touching any other field rewrote a two-sided read as a one-sided one, with nothing red.
      Fixed, and pinned: `test_calls_exhibit.py` now holds the editor's bias / spec / post_class
      vocabularies against every value the committed corpus carries, so the NEXT new value fails
      in CI rather than silently on someone's screen.
    - **`post_class` is not in the brief at all**, yet 2,166 of 8,185 rows (26%) are not signal —
      1,412 `flow_spam`, 474 `promo`, 219 `noise`, 61 `engagement`. Labelling throughput is the
      entire point of the screen, so a class filter matters more than most of the filters that
      WERE specified. Added.
    - **The specificity tiers had no definition anywhere** — the filter offered A/B/C/D against a
      scale the reader could not see. Now defined FROM the data (A: direction + target, usually a
      horizon · B: direction + target, no horizon · C: direction, no target · D: no directional
      call), with the measured row counts shown beside each.
    - **`needs_review` is true on 5,982 of 8,185 rows (73%)**, so as a filter it selects almost
      everything. Left as-is — it is the upstream labeller's field — but recorded so nobody reads
      a 73%-true flag as a shortlist.
  - **Three claims in the brief do not survive contact with the bundle**, recorded so they are not
    repeated: the renamed map holds **3** entries (SQ→XYZ, FB→META, TWTR→null), not the 8 asserted;
    monthly volume falls **2.0x** across the span (357 → 177), not ~3x; and the machine labeller's
    quoted **55% bias / 62% target accuracy is NOT re-derivable here** — a hand label REPLACES the
    machine row at the same key, so the machine's own guess for those 83 is retained nowhere in the
    bundle. The figure has to be taken on trust or re-measured upstream.
    **CORRECTED 2026-08-25:** this entry originally said "no surface in the app claims it was
    verified" — and `app.js` was at that moment stating "the machine labeller's 55%-accurate bias
    calls" as plain fact in the Scoreboard's unlock trigger, which a reader sees. Asserting a
    number the same entry records as unverifiable is the defect this repo forbids, found by
    auditing my own claims rather than by anything failing. Both mentions now ATTRIBUTE it to the
    brief and state why it cannot be re-derived here.
  - **A convention the brief never states, left unchanged but written down:** 53% of posts land
    outside 09:30–16:00 ET, and the scorer keys off the DATE only. So a pre-market post and an
    after-close post on the same day receive the SAME next-open entry. For the after-close post
    that is right; for the pre-market one it silently forfeits the session the post was about.
    Conservative in both cases (never look-ahead), so preserved — but it is an assumption, not a
    neutral fact, and it was nowhere in the brief.
  - **Chart windows are anchored on the POST, not on today** (`WINDOWS`, 5D/1M/3M/6M/1Y/5Y/MAX/FIT).
    The usual trailing-window row would be wrong here: the subject is a call at a fixed point in
    the past, so "last 6 months" can miss the call entirely. Each preset is `[post − lead, post +
    span]`, and a pin asserts every lead is negative and every span positive — a window that can
    scroll the call off screen is not a window on the call. FIT snaps to the scored horizon.
  - **A crosshair readout** (date · OHLC · the price at the cursor's own height) reads from the same
    geometry object the SVG was drawn from, so it can never report a bar that was not plotted.
  - **THIRD PASS (2026-08-25) — the sequence was being drawn one month wide.** The chart's whole
    claim is that the SEQUENCE is the story, and the prior-post markers were built from `S.posts`,
    which holds ONE month. On $HOOD at the 1Y window that drew **5 of the 30 posts actually in
    range** — a sequence missing 25 of its members, presented as complete. Now gathered across the
    window: `days.json` carries each day's ticker list, so the months worth opening are known
    without touching `posts/`, and only those are fetched (memoised). $HOOD now draws 35.
  - **The markers are CLICKABLE**, jumping to that post's day and focusing the same cashtag on it —
    a dot you cannot open is a tally mark, and the reasoning being compared lives in the TEXT. If a
    filter would hide the destination post the filters are cleared for the jump rather than landing
    on the wrong one silently.
  - **A stale-URL bug found by that jump.** `writeUrl()` read `S.ticker`/`S.tweetId`, which only a
    CHIP CLICK ever set — so after `j`/`k` or a marker jump the address bar still named the previous
    post, and a link shared from that state opened the wrong call. It now DERIVES both from what is
    focused, which makes the URL structurally unable to disagree with the screen.
  - **`needs_review` is not a queue and is no longer used as one.** The upstream flag is true on
    **5,982 of 8,185 rows (73%)** and is worse than unselective: it INCLUDES 1,410 `flow_spam` rows
    nobody should read and EXCLUDES 510 spec-A calls — the most reviewable rows in the corpus. As a
    filter it pointed away from the work. Replaced by a DERIVED queue, ordered most-actionable
    first and excluding the non-signal classes outright: target contradicts the bias (16) · target
    unreadable (0) · no price data (45) · a specific call still only guessed (1,180) · a target with
    no direction (1,004) · a two-sided read (315). **2,526 rows, 31%**, and each row's chip now
    names WHY it is queued. The upstream flag is still carried on the label — it is the labeller's
    signal, not ours to delete — it is simply not what the filter sorts by.
  - **THE ROUND TRIP IS CLOSED** (`vinci/calls/ingest.py`, `vinci calls import-labels`). Edits were
    reaching `localStorage` and the JSONL export and going no further, so the corpus never grew.
    Landing them is a CLI step and stays one: the dashboard is a read-only static mirror and must
    not acquire a write path, and hand labels are the ground truth this tool exists to grow — a
    silent background write is exactly how a reference set gets corrupted without a trace. Here the
    change lands in `git diff` like anything else. The merge is **whole or refused**: the file is
    parsed and keyed before a byte is written, so a bad row on line 40 cannot leave line 1 merged.
    A hand label REPLACES the machine guess at its key and clears `needs_review`; `meta.json`'s
    counts are recomputed from the merged corpus so they cannot drift. It deliberately does NOT
    re-score — that reads prices and takes real time — and says so on exit.
    — *round-trip verified end to end on the real corpus: a machine spec-A row exported in the
    browser's exact shape, imported (83 → 84 hand labels, "replaced a guess 1"), then reverted; the
    corpus is byte-identical to committed. Five pins cover replacement, the two flag columns
    surviving, meta drift, whole-or-nothing refusal, and dry-run.*
  - **FOURTH PASS (2026-08-25) — the chart was the smallest pane on the screen.** Three columns gave
    the EVIDENCE the narrowest share while navigation and the work queue each took a fixed slab.
    Now TWO: a 380px rail stacking calendar over posts, and the chart taking the rest — **74% of the
    content width at 1760px (1,062px, up from ~916), 65% at 1280px**, with the canvas widened
    880→1100 and deepened 470→560 so the extra room becomes resolution rather than stretch. The
    timeline strip and the stage subtitle are gone; the strip's one unique fact (monthly volume,
    the ~2x decline) now rides in the month dropdown's own option labels, where the reader is
    already choosing a month. — *verified at 1760 and 1280: no horizontal page scroll, calendar
    fits, chart does not overflow its pane; a full exercise (month switch → MAX → 1Y → marker jump)
    raised zero JS errors and zero failed fetches.*
  - **THE FILTERS DELIBERATELY DO NOT REACH THE CHART, and the page now says so.** The posts pane is
    filtered because that is how the work is found; the chart is the RECORD of what the author said
    about that ticker, and a filtered record is a false one — the same failure as drawing 5 of 30
    markers, arrived at from the other direction. The header now states the count and the fact
    ("148 posts on $SPY in view · unfiltered") rather than leaving the reader to infer it.
  - **A ticker-only deep link opened the wrong cashtag.** `#/calls/<h>/<date>/HOOD` matched HOOD
    against whatever post happened to be FIRST that day, missed, and silently focused something
    else — a link that looked honoured and was not. It now finds the first post on that day
    actually naming the ticker, then completes the URL with the resolved post id.
  - **FIFTH PASS (2026-08-25) — A TARGET NOWHERE NEAR THE PRICE WAS SCORING A HIT.** Found while
    looking for an OPEN call to test: `$TSLA bearish, target $5,000,000`, `$SPY bullish, target
    $12`, `$OPEN bearish, target $4,000,000` against a $4.79 entry. `target_hit` asks whether the
    HIGH ever reached the target for a bullish call and whether the LOW ever did for a bearish one,
    **so an absurdly high target on a bearish call is satisfied by every bar that ever traded**, and
    an absurdly low one on a bullish call likewise. The hit was arithmetic, not evidence.
    — *measured: **621 of 1,966 resolved targets sat outside 0.1x–10x of entry, and 489 of them were
    reporting a hit**. Refusing them (`TargetStatus.IMPLAUSIBLE`) drops the target-hit denominator
    1,808 → 1,212 and the corpus hit-rate **74.2% → 70.3%**.* The band is set on FACE VALIDITY and
    never on what it does to the rate — 10x admits a genuine ten-bagger call and 0.1x admits a
    90%-crash call, both of which this author makes; a $430 stock "reaching $5,000,000" is admitted
    by nothing. With no entry to compare against the target is NOT refused: the check exists to
    catch numbers that contradict a known price, not to discard targets for want of one.
    **This was not asked for**; it is the same defect family as the two authorised parser fixes
    (a silently-wrong target quietly scoring), it moves a headline number, and it is recorded here
    rather than folded in quietly.
  - **A live call now shows its own numbers.** OPEN rendered a pill and one sentence — nothing else
    — so the 349 calls whose outcome is still in play, arguably the more interesting half, showed
    no shaded band and no figures at all. The settled fields (`ret` / `excess` / `mfe` / `mae` /
    `direction_correct`) stay **None** so nothing can aggregate an unfinished call by accident,
    which is the convention's whole point; alongside them sit explicitly provisional ones —
    `mark`, `mark_date`, `elapsed_days`, `unrealised`, `bench_unrealised`, `mfe_to_date`,
    `mae_to_date`, `target_hit_to_date` — every one rendered under a "so far" label, with a
    progress bar and the words *excluded from every aggregate until the horizon elapses*. The chart
    band now runs for a live call too, with its right edge left OPEN (no closing rule) and marked
    "horizon still running (62/63d)", so it can never read as a horizon that ended.
  - **The chart sequence can now honour the filters, on request.** Default stays UNFILTERED — the
    chart is the record of what the author said about that ticker, and a filtered record is a false
    one — but "only his spec-A calls on this name" is a real question, so the header count doubles
    as the toggle and states which reading is on screen. One shared predicate (`postPasses` /
    `chipPasses`) backs both the posts list and the markers; two copies would drift the moment a
    filter was added and the surfaces would silently disagree about the same post.
  - **The calendar gave ~90px back to the rail**: its static legend is gone (it never changed and
    cost that on every load — the dots stay self-describing through each cell's title, and the Spec
    key carries the long form where it is asked for), cells are 44px → 30px, and the posts pane
    grew 62vh → 74vh. The month dropdown's post counts are gone at the operator's call; monthly
    volume now reads only off the calendar's own intensity.
  - **SIXTH PASS (2026-08-25) — the trivial hit, closed properly, and the sign gap widened to
    absolute targets.** `sign_conflict` only ever covered PERCENTAGE targets, where an explicit
    minus contradicts the bias. For a point or range target the direction is implied by where the
    level sits, and nothing checked it: **590 absolute targets sat on the opposite side of entry
    from the stated bias.**
    - **THE ROOT DEFECT WAS THE TOUCH TEST, not the label.** `target_hit` picked HIGHS for a
      bullish call and LOWS for a bearish one — correct wherever the target lies in the direction
      of the call, and **trivially true wherever it does not**: a bullish call with a level BELOW
      entry asked "did the high ever reach it", which the first bar satisfies. **326 of the 373
      signal-class rows in that shape were reporting a hit on arithmetic alone.** `touched()` now
      keys on the LEVEL's own position — did price travel from entry to the level — which is
      identical wherever the two rules agree. *358 hits flipped, **every one on a
      counter-directional row, zero collateral**; corpus hit-rate 70.3% → 40.8%.*
    - **MARKED, NOT REFUSED — and the ground truth is the reason.** Four of the 83 HAND labels are
      this shape and all four are CORRECT: `$UNH` bullish with a $300 target against a $303 entry
      is the support he expects a bounce FROM; `$SPY` bearish with $676–684 against $668 is the
      rejection zone he expects price to rise INTO before falling. These are **levels being
      watched, not targets being predicted.** A guard that discarded four ground-truth labels to
      catch a machine artifact would have been the worse trade — so the status is
      `COUNTER_DIRECTIONAL`, the price still resolves, the touch is still scored, and the readout
      says "reached the zone" instead of "inside the band". `$NOW` (bearish, $140–150 against a
      $112 entry) correctly flips to NOT hit: price never rose to the zone.
    - The headline separates cleanly now: **true targets 46.7%, watched levels 33.3%** — two
      different questions that were previously averaged into one number.
  - **A BIAS FILTER** (bullish / bearish / mixed / neutral / none, with corpus counts, plus
    "unlabelled (no chip)" — a distinct state from a label whose bias IS `none`, which is the author
    declining to take a side). — *verified on 2026-01-26: 6 posts → 5 bullish (every chip bullish)
    → 0 bearish (genuinely none that day) → 1 `none`.*
  - **A dev-only no-cache static server** (`serve_nocache.py`, launch config `calls-tape`). The
    browser caches ES modules hard enough that a reload kept running the PREVIOUS build of a view —
    so "verify it in the browser" was twice quietly testing old code, and twice I mistook a stale
    module for a broken feature. Not shipped to the deploy; a dev-loop correctness fix.
  - **SEVENTH PASS (2026-08-25) — EDITING A LABEL CHANGED THE CHIP AND NOTHING ELSE.** Reported
    from the screen: `$HOOD`, machine-labelled bullish, re-marked **bearish** after reading the post
    ("after an 800% run… might be topping out") — the chip flipped and **the readout kept the old
    answer**. Diagnosed screen-wide: the chip reads `labelFor()` (live), but the readout, the target
    line, the horizon band, the FIT window and three review reasons all read `S.results` — i.e.
    `results.jsonl`, scored SERVER-SIDE from the label as it stood BEFORE the edit. So the page
    showed a bearish chip beside a bullish-signed return with nothing saying they disagree. On that
    row the truth is the opposite of what was displayed: **Return −32% → +32%, Excess −38% → +38%,
    MFE/MAE +0%/−49% → +49%/−0%** — his call was RIGHT and the page said it was wrong.
    - **FIX: the browser recomputes an EDITED row locally** (`frontend/lib/callscore.js`), so the
      readout, target line, horizon band and FIT window all follow the label the operator can see.
      — *verified: bias flip moves every bias-dependent field; a horizon edit 105 → 20 moves the
      exit date 2026-06-08 → 2026-02-04 and shrinks the band 499px → 99px on BOTH panels; setting a
      resolvable target draws the target line.*
    - **IT IS A PREVIEW, NOT THE RECORD, and it says so.** `vinci calls score` stays authoritative;
      the readout carries a "recomputed from your edit" mark, and the path to make it the record is
      `calls import-labels` → `calls score`.
    - **THE TWIN IS PINNED, because a py↔JS twin over one artifact is precisely the hazard
      `test_duplicate_definitions.py` exists for** — neither side can import the other, so the
      conventions get hand-copied and a one-sided edit ships two surfaces that disagree with nothing
      red. `tests/test_calls_parity.py` runs `callscore.js` under node over the **real committed
      corpus** (3,000+ rows) and asserts every field matches the Python scorer, plus a 14-shape
      parser comparison. — *mutation-tested: flipping `signOf` to always return 1 reddens it.*
  - **EIGHTH PASS (2026-08-25) — CODE REVIEW OF THE WHOLE TAPE, five defects fixed.** Found by
    reading the diff, not by the screen; two of them were guards that had been WRITTEN and never
    worked, which is the more expensive kind because the comment says the hazard is handled.
    - **THE COMMON-LAST-BAR TRIM COULD NEVER FIRE.** `score.py` (and its JS twin) computed
      `common_end = min(b_win[-1], exit_date)` over a `b_win` **already bounded by `exit_date`** —
      so it re-derived the same window and changed nothing, while the NAME's leg was never trimmed
      at all. The exact asymmetry `vinci/eod/features.py` learned the expensive way was live in the
      module whose docstring cites it, and **the test pinned the defect**: it asserted `bench_ret is
      not None` for a benchmark stopping 13 bars short of the horizon. Fixed by REFUSING rather than
      trimming — if the benchmark does not span `[entry_date, exit_date]` there is no honest excess,
      so `bench_ret`/`excess` stay `None`. — *re-scored the corpus: **3,889 rows, byte-identical**,
      because SPY's window (2024-04-29 → 2026-08-24) happens to cover every call; the guard is
      latent-only today and would have bitten the first account whose benchmark fetch lagged.*
      Test now carries a negative AND a positive pin.
    - **A NON-POSITIVE ENTRY OPEN WOULD HAVE CRASHED THE RUN.** `unrealised` carried an `entry > 0`
      guard; `mfe_to_date` two lines below divided by the same entry with none, so a zero open (a
      bad vendor bar) raised `ZeroDivisionError` mid-account rather than returning None. Refused by
      name now — `NO_ENTRY_BAR`, detail states the open — in both Python and the JS twin.
    - **THE EXPORT LANDED DATELESS ROWS.** `exportJsonl()` indexed posts from `S.posts` — **one
      month** — while `S.edits` is restored from `localStorage` and accumulates across months and
      sessions. Every edited row outside the open month exported `date` / `quarter` / `text` /
      `has_video` as `null`, and `calls import-labels` writes them into `gold_labels.jsonl`
      unchallenged (it keys on `tweet_id|ticker` and never reads the date). **The ground truth this
      tool exists to grow would have been corrupted silently.** Now resolved across months, fetching
      only the months still missing an id.
    - **THE INLINE EDITOR WAS UNUSABLE ON ANY CASHTAG BUT THE FIRST.** The editor renders INSIDE
      `.pcard`, whose click handler sets `S.chipIdx = 0` and repaints. So a bias button on the
      second cashtag applied the edit and then re-rendered the editor for a DIFFERENT one, and
      clicking into the Target field repainted the pane out from under the input before a character
      could be typed. `.lchip` stopped propagation for exactly this reason; `.ed` did not.
    - **PAINTS RACED.** `paneChart()` awaits a fetch and the keyboard fires a paint per keystroke,
      so two held `j`-presses started two paints and whichever fetch settled LAST won the innerHTML
      — not necessarily the last post focused. Serialised by sequence number; a superseded paint
      drops its result. (Also: `S.local` — keyed `<tweet_id>|<TICKER>` with no handle in it — is now
      cleared on an account switch, and `rebuild_accounts` PRESERVES the stored `default` instead of
      silently resetting it to the alphabetically-first handle on every bare rebuild.)
    - **TEST LAYER, STATED HONESTLY.** The two DOM fixes and the paint race are pinned as SOURCE
      scans (`tests/test_calls_tape.py`), not end-to-end: there is no jsdom in this suite and the
      view's entry point needs a live `root`. A source pin cannot prove the fix works — it fails
      when the line that makes it work is deleted, which is the failure mode that occurred (the
      guard was never written). — *all three mutation-tested: removing each guard reddens its pin.*
      Recorded as accepted weaker-layer coverage rather than dressed up as e2e.
  - **NINTH PASS (2026-08-25) — SECOND CODE REVIEW, four defects fixed.** All four sit on the HAND
    path, which is the path the tape exists to grow.
    - **A NEGATIVE HORIZON WAS INDEXED BACKWARDS AND SCORED CLOSED.** `hz` reaches `win_all[hz]`
      unvalidated, and Python does not raise on a negative index — it returns a bar counted from the
      END of the fetched series. Shown on real bars: `horizon_hi = -5` produced `status: CLOSED`,
      `exit_date 2025-02-05`, `ret +33.7%` and `horizon_days: -5`, straight into the aggregates; a
      FRACTIONAL `hz` raised `TypeError` and took the whole `calls score` run down instead. Not
      reachable from the machine labeller — reachable from a hand label, because the tape's Horizon
      boxes take free text, `exportJsonl` carries it verbatim and `import-labels` writes it through
      unchallenged. Refused by name now (`BAD_HORIZON`) in **both** the scorer and the JS twin, and
      the tape coerces a clean positive whole number while KEEPING anything else verbatim so the
      readout names it rather than the typo being silently discarded (`Number("abc")` used to become
      `NaN`, fall through the `or` chain, and score at the 63-day default flagged **STATED**).
      — *pinned `tests/test_calls_score.py`, red on the old code for all six shapes; the corpus
      re-scores byte-identical (3,889 rows), so no committed number moved.*
    - **IN THE BROWSER THE SAME VALUE WEDGED THE SCREEN.** `winAll[-5]` is `undefined`, reading
      `.c` off it threw inside the awaited `paint()`, so the chart pane stayed on "Drawing…" and
      `wire()` / `wireCrosshair()` / `writeUrl()` never ran — and because the patch is persisted to
      `localStorage`, a reload reproduced it. Closed by the same guard.
    - **A PRICE PANEL WITH NO READABLE LEVEL ON IT.** The gridline ladder started at `1`, so any
      window whose padded span held no whole dollar drew no gridlines and **no y-axis labels at
      all**. Measured on the committed bars: 53 sampled windows, all on names between $3 and $5
      ($BB, 2025-08-25, 3.67–3.97). Ladder now goes down to 0.01, labels carry the matching
      precision, and multiples are counted rather than accumulated so 0.05 cannot drift into
      `4.050000000000001`. Above $1 the steps are unchanged.
    - **THE CALENDAR'S LABEL DOT NEVER MOVED AFTER AN IMPORT.** `days.json`'s `lab` is the only
      thing that dot reads and nothing in this repo regenerates the file (the corpus is produced
      upstream), so `import-labels` landed the labels, updated `meta.json`'s totals, and left every
      day showing its pre-import tally — the operator browses back to the month they just worked and
      the tool says they never labelled it. `import_labels` now DERIVES the per-day tally from
      `labels.json` + the post dates, so it cannot drift from what was merged. — *pinned against the
      real corpus (`tests/test_calls_ingest.py`): 2024-08-01 goes 0 → 1 and the per-day tallies
      still sum to `meta.n_hand_labels`.* The CLI's post-import advice also now names
      `vinci calls accounts`, which is what refreshes the hand-label count the toolbar reads.
    - **ALSO:** `focusPost()` was being called once per chart marker, and it re-filters the whole
      open month through `chipPasses` → `reviewReasons` each time (up to 47 full scans per draw on a
      screen whose point is keystroke throughput) — hoisted out of the loop; and the Horizon inputs'
      `value=` is now escaped, since they can hold operator free text.
