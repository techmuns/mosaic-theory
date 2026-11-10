---
id:
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# A guide is read only where the release states one, for the period it states, and a guide the reader cannot read is said aloud (TeamNostra fix request 2: RE2-D1, RE2-D3, RE2-D4 = E2-D3, RE2-D5's guide half, RE2-D7, RE2-D19, RE2-D20). No guide moves on the 27 committed pages; five refusal notes reach Netflix and Vital Farms at their next re-assembly

**WHAT.** All in `vinci/edgar/release_parse._guidance` and `_period_for`.
- **RE2-D1, two figures are not a range.** "and" joins a range only after "between". "Total
  revenues of $412.0 million and $1,180.5 million for the three and nine months ended …" is no
  guide. No note: it states no guide.
- **RE2-D3, a withdrawn outlook.** A range is refused with a note when the release withdraws its
  outlook. That covers two cases:
  - a withdrawal in the range's own clause, unless a current word sits between them ("withdrew its
    prior outlook and now expects …" is read);
  - a release that withdraws its outlook anywhere and states this range as the prior one.

  Without a withdrawal, a prior range with no new one is still read, as review round 2 ruled.
- **RE2-D4 = E2-D3, a deal's period.** A quarter or year followed by a deal noun is not the guide's
  period. The nouns are acquisition, merger, divestiture, disposition, transaction, sale (singular),
  spin-off and separation, as in "the 2025 acquisition" and "the fourth quarter acquisition". The
  rule applies in the guide's own sentence, its trailing clause and its lead-in.
- **RE2-D5's guide half, a calendar period.** A range stated for a calendar period ("For calendar
  2027", "CY2027") is refused with a note. That is the actuals' rule from #962, through the same
  `_own_calendar`, so a calendar year inside a comparison sub-clause does not count.
- **RE2-D7, four shapes no longer dropped in silence.**
  - **Read:**
    - a qualifier before the low side ("to be approximately $500 million to $550 million");
    - "is/are expected to increase 5% to 7%", in the three change patterns;
    - "guidance (outlook) to $X to $Y". That runs after the range loop and only for a metric with
      no range yet, so an outlook list's bullet keeps its slot.
  - **Refused with a note:** a single-point guide that a forward verb governs. The verb must sit in
    the point's own clause or the header of the list it opens. A point that "was/were" follows, or
    that sits in a comparison or after "last year's", is a result. So is a brand's sub-line.
- **RE2-D19, a raise "to … from".** "raised its fiscal 2026 revenue outlook to $1.10 billion to
  $1.15 billion from its prior outlook of …" reads the new range through the "outlook to" form. A
  prior range stated earlier in the release gives way to it (`statements` now holds the form).
- **RE2-D20, the default.** A guide filed under `next-fy` writes a machine-tier flag,
  `GUIDANCE_PERIOD_DEFAULT_PREFIX` ("Guidance period not read"). It says no period was READ beside
  the guide, in its list header or in its outlook opener. It does not say the release states none.
  It is not a refusal and is not lifted to the reader.

**WHY.** TeamNostra's re-audit (document 14): E2-D1, D3, D4, D5, D7, D19 and D20. Order 6 holds D19;
order 4 holds the rest.
- **D1, D4 and D5 store a wrong guide.** D1's is a range across two actuals; D4 and D5 file a guide
  under the wrong period. A wrong period has the ~4x quarter-as-annual shape `_period_for` exists to
  prevent.
- **D3 keeps a withdrawn outlook as current.**
- **D7 and D19 drop a stated guide with no trace.** That is the absent-and-silent shape item 22
  prohibits. **It is live:** Vital Farms' latest release (8-K `0001193125-26-444348`) cut its
  outlook to "Net revenue of around $730 million", and main stored no guide and wrote no note.
- **D20 files an unread period under a label that reads as stated.** Burlington's page prints
  "next-fy adjusted EPS guide $11.77–$11.97" for a guide its release states for Fiscal Year 2026.

**HOW VERIFIED.**
- **Fail first.** `tests/test_guidance_fix2_e2.py` was run against an export of `origin/main`
  `670a784c`: 14 of the 23 written first fail. The 9 that pass are the negative pins:
  - a "between … and" range;
  - a prior range with no withdrawal;
  - a period naming no deal;
  - a fiscal period;
  - a result stated as one figure;
  - Burlington's headline beside its outlook list;
  - a read period carrying no flag;
  - a new outlook after a withdrawal;
  - a range never read as a point.

  On this branch all 37 pass (the 23, plus 14 from code review), and so do the 30 release and
  guidance test files.
- **Real text in the pins.** Each is a frozen literal cut from a committed page's cited exhibit:
  - Vital Farms `0001193125-26-444348` (D7's single points);
  - Burlington `0001193125-26-369502` (the "guidance to" headline does not displace the list);
  - Verra Mobility `0001628280-26-068453` (D20).

  The constructed sentences are TeamNostra's.
- **CORPUS FIRST: the $0 replay.** Every cited EX-99.1 on the 27 committed pages was read from the
  on-disk SEC caches, offline, through main's parser and this one.
  - **Guides: 141 on main, 141 here, 0 move.** Metric, period, bounds, unit and verbatim are all
    identical.
  - **Refusal notes (lifted to the reader): 24 → 29.** The new ones are Netflix's three single
    points and Vital Farms' two:
    - NFLX: free cash flow "roughly $11B"; revenue "$51.1B" for 2026; revenue "$13.4 billion" for
      Q4;
    - VITL: revenue "around $730 Million"; adjusted EBITDA loss "around $(15) million".

    Each is a real forward point. Three exhibits lose the "no anchored pattern matched —
    guidance/outlook" flag, since they now state guidance found and refused.
  - **Default flags: 0 → 21**, on BURL 1, EPAM 1, SMPL 13, VITL 1 and VRRM 5.
  - **The single-point rule's first form fired 20 times.** About half were results beside the word
    "guidance" or "outlook" in a nearby bullet, or the company name "Target". The rule now needs a
    forward verb in the point's own clause. A point after "was/were", inside a comparison, after
    "last year's", or on a sub-line is a result. Each remaining note was read and is a guide.
  - **The corpus scan for each shape** found:
    - D7d's form: Burlington ×3 and Vital Farms' headline; none takes a slot from the outlook
      list;
    - D3's: one hit, Vital Farms' "Withdraws … Fiscal 2030 Financial Targets". The pattern stops
      at "targets", so it is no outlook withdrawal;
    - D4's deal nouns: 23 hits, none in a guide's clause;
    - D5's calendar periods: none;
    - D1's "of … and": none.
- **Code review, round 0 (`/code-review high --fix`).** Ten findings, all fixed, each pinned on a
  test that fails on `dd9d8f44`. The review fixed six:
  - two figures joined by "and" are no current statement either, so they no longer make
    `_superseded_refused` drop the only range a release states;
  - the "guidance to" reader refuses one range shared by two metrics (BellRing's shape) and a
    prior "guidance to" beside a current one, as the range loop does;
  - a withdrawal AFTER a range in its clause withdraws it only when no current word states it
    ("now expects … and is withdrawing its long-term outlook" is read);
  - the calendar check reads the guide's whole clause. Its 170-character look-back missed a long
    sentence's opening "For calendar 2027";
  - "as expected" and "than anticipated" are no forward verb before a single point.

  I fixed the four it left:
  - a withdrawal covers a range only at its own horizon. A long-term or multi-year outlook, or one
    naming another year, leaves a prior range read;
  - the withdrawn outlook must be the verb's direct object (at most four words between) or the
    subject of a passive one ("… outlook … has been withdrawn");
  - a deal stated BEFORE its period in one clause ("the acquisition of Beta Corp in the fourth
    quarter") dates the deal, not the guide;
  - a percent range under a dollar metric's "guidance to" is refused, never stored as a level in %.

  Also, from the review's note: "revenue is expected to be $X to $Y", with no introducer, is read,
  as its "approximately" form now is.
- **One existing pin changed.** `tests/test_guidance_ranges_as_stated.py` stored "The Company
  expects calendar 2026 revenue of …" as a guide, but only because the calendar look-back missed
  the text's first sentence. The same sentence after a header was already refused. That row is now
  its own test: no sub-line refusal, a calendar refusal, no guide.
- **The corpus after round 0** is byte-identical in guides and flags to the run before it: 141
  guides, 0 move, the same 14 exhibits' flags.
- **Codex, round 1 (P1).** The deal-before-period rule took any deal noun within 40 characters, so
  "contributions from the acquisition to support fiscal 2026 revenue …" lost its stated year and
  was filed next-fy. A deal now dates a period only through "in" or "during" ("the acquisition of
  Beta Corp in the fourth quarter"). The pin fails on `3914a199`; the corpus replay is unchanged.
- **The version.** Row `2026-11-11.guides-as-stated`, in both tables, re-pinned.

**WHAT REACHES THE SYNTHESIS.** Guidance is not re-read by the $0 release refresh
(`refresh.release_figures_transform` reads actuals only), so nothing moves on a committed page now.
At each page's next re-assembly:
- **The 21 default flags stay in each release's own `qa_flags`.** Those sit inside `primary_source`,
  which `synthesis.NOT_SENT` excludes. No request moves for them.
- **The 5 refusal notes are lifted by `mechanical.guidance_refusal_flags`** into the page's flags,
  and so they reach the reader and the request. That happens on **NFLX and VITL only**. Neither is
  a panel page.
- **On the six panel pages (BURL, CNXC, LLY, MCK, ROST, SMPL), no guide and no refusal moves.** A
  six-page panel check would compare identical requests on all six, so none is proposed: it would
  measure nothing at about $28. NFLX's and VITL's requests change only by these caveats.

**BOUNDARY.**
- **Pages:** `data/dossiers/*/dossier.json` at `670a784c`, 27 pages.
- **Exhibits:** every EX-99.1 their `primary_source.releases` cite, 122 exhibits, read offline from
  the local SEC caches. None missed and none errored.
- **Unit:** one guide item, or one `qa_flags` line of one exhibit.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A single point is refused, not read.** A level guide prints as a range (`_fmt_guide_range`
  prints a point as "$730.0–$730.0M"), so reading one needs the printer first. The CIQ check
  already takes a point as [low, low] (#945). Proposed as a follow-up.
- **RE2-D20 is PARTIAL.** The flag is in the machine tier only, and the page still prints "next-fy".
  Each of the 21 sits under a list header or headline that names a fiscal year the reader does not
  parse, for example:
  - Simply Good's "Updating Fiscal Year 2026 (4) Outlook:";
  - Verra Mobility's "2026 Full Year Guidance";
  - Burlington's "For Fiscal Year 2026 (the 52-weeks ending January 30, 2027), the Company now
    expects:".

  Reading those headers would relabel all 21. That moves BURL's and SMPL's requests, both panel
  pages, so it is a separate change with its own panel check. Proposed, not built.
- **A calendar-year filer's "calendar 2027" guide is refused,** though it is its fiscal 2027. That
  is the trade #962 made for the actuals. *Falsifier:* a re-assembled page whose only current guide
  is refused for a calendar period by a calendar-year filer.
- **"of $X and $Y" is never a range,** and gets no note. *Falsifier:* a release that states a guide
  that way.
- **A period phrase before a deal noun is skipped.** "the fiscal 2026 sale of …" gives no period.
  *Falsifier:* a guide whose only stated period is written before such a noun.
