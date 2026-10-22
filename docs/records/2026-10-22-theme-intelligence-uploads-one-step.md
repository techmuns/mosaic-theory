---
id: 2026-10-22-theme-intelligence-uploads-one-step
status: recorded
date: 2026-10-22
prs: [775]
supersedes:
superseded-by:
---

# Theme intelligence: the Uploads screen teaches the one-step upload — and the 58 open review lines have proposals awaiting the operator

**WHAT.** Items 2, 3 and 4 of the open list (operator, 2026-10-22: "yes, start 2, 3 and 4").

**Item 4 — the Uploads screen (this PR, a render change).**
- Each row's import command is now `upload --path <your copy> --source … --llm-permitted
  --budget <USD>`. Until now it was `ingest-file`, which neither checks before paying nor pushes.
- The weekly how-to now reads:
  1. **price it** with `--dry-run` — it pulls and checks identity, licence, the author it will
     credit and the cost against the budget, and imports nothing;
  2. **run it**;
  3. **clear** what is held: pull, release, push;
  4. **several files at once** through the inbox.
- The rules add `--remote` the first time on a machine, the author (only when the dry run says
  the page names none; a wrong name is retracted) and the budget (it must cover the estimate's
  high end).
- Releases of held documents keep `ingest-file --release`, since `upload` releases nothing.
- **The code review of this PR** (`/code-review high`, 9 findings; operator: "apply fixes, then
  merge"):
  - **No row states an author.** The rows had taught `--author "<as printed>"`. Quoted, a
    forgotten placeholder passed the shell and was credited as the article's author; and on a
    signed report a stated name is credited beside the byline as a second author. The CLI now
    refuses a whole-name `<…>` placeholder (`--author`, `--name`, `--retract`; exit 2).
  - **The dry run names who will be credited** and from where: "author: NAME (stated by you |
    from the document | kept from A-…)".
  - **A row's URL is shell-quoted**: a `#` commented out the flags after it, and an `&` split
    the command.
  - **The release step pulls first**; `--remote` is a rule for the first command on any machine,
    not only `upload`; the licence rule names the `sources.toml` exception.
  - The helper is `_upload_cmd` (it was `_ingest_cmd`).

**Items 2 and 3 — proposals, not applied.**
- The 58 open lines on the registry of record (0cdebc0f) are 47 dismissible review warnings and
  11 withheld lines. For each I proposed a disposition:
  - **35 corrections:** the 11 withheld lines and 24 warnings. Each is written only from claims
    the thesis links, and each passes `reassess --corrections` on a scratch copy.
  - **22 dismissals.**
  - **1 for the operator** (TH-38CA111885 s07.8, the China AI-safety risk framing).
- **The rule.** Dismiss when the review calls the line supported, the wording adds no fact, or
  the source says it (quoted). Correct when the line adds a fact the evidence does not carry: a
  figure, a named entity, a date, a mechanism, an attribution, or a forecast stated as realised.
- **Twelve warnings the source settles.** Checked against the original documents (then the retired
  pilot's archive, read only; the operator deleted it the same day, and the originals now live
  only in the main checkout's git-ignored `data/theme_intelligence/documents/<sha256>.pdf`,
  hash-verified against the registry), each says what the review thought unsupported. Example: in-vivo
  editing "could enable access to organs that cannot easily be removed, including the brain,
  heart, eyes and liver".
- **Where they live.** A decision page in the git-ignored `data/theme_intelligence/triage/`
  (`review-decisions-2026-10-22.html`); it quotes licensed research, so it is not committed. Each
  proposal can be approved or rejected there, and nothing is applied until the operator decides.

**FOUND — open, the agent's.** `reassess` (and so every analyst correction) re-records a
thesis's open review findings as the new version's own.
- Their keys change: all 31 warnings on the 8 theses the 11 withheld-line corrections touch.
  So a dismissal made before a re-grade or correction is open again.
- `review list` shows the finding as raised by the new version on today's date.
- Hence the order: corrections first, then dismissals with the keys as they then stand.
- A re-grade should carry a finding's origin, not mint a new one.

**HOW VERIFIED.**
- **Item 4:**
  - **The real registry** (0cdebc0f), published with this branch into scratch: the 2 rows asking
    for documents (Morgan Stanley, Goldman Sachs) give the `upload` command; 0 rows teach
    `ingest-file --path`. Re-run after the review fixes on cd0f4a08: both rows read `upload
    --path <your copy> --source ms_research|gs_research --llm-permitted --budget <USD>`, with no
    `--author`; the previews below are re-taken from that run.
  - **Preview** in `docs/theme_intelligence/uploads-one-step-2026-10-22/`: `uploads-screen.png`
    (as it opens) and `uploads-print.png` (every fold open).
  - **Pin:** `test_uploads_teach_the_one_step_upload`, end to end on the rendered desk. It checks
    the steps, the rules, and every import row; a NEGATIVE pin forbids `ingest-file --path` on a
    row.
  - **Mutation:** 3 mutants, 2 killed. The survivor removes only the prose mention of
    `--dry-run`; step 1's command still carries it, which is what the pin checks.
  - **The review fixes:** pins in `test_theme_intelligence_desk.py` (no row states an author;
    the release step pulls; the `--remote` rule; a URL holding `?`, `&` and `#` read back whole
    by `/bin/sh` with every flag after it), `test_theme_intelligence_author_statement.py` (a
    placeholder refused at `author --name`, `--retract` and `upload --author`; a name with
    brackets inside passes) and `test_theme_intelligence_upload.py` (the dry run's author line,
    stated and kept). **Mutation:** 7 mutants, all killed — the first URL pin read the command
    back with `shlex.split`, which treats neither `#` nor `&` as a shell does, and let the
    unquoted URL survive; it now asks a real shell.
- **Items 2 and 3, on one scratch copy:**
  - All 35 corrections in one $0 run change 14 theses' cards and **no research action**; QA 21/21.
  - The 22 dismissals then apply with the post-correction keys.
  - The Review queue goes from **58 open findings to 1** (the operator's call). 0 withheld lines
    remain.

**BOUNDARY.**
- Registry `theme-intelligence-state` 0cdebc0f, imported on 2026-10-22 (UTC); code: this branch
  on main fc746b56.
- "58 open lines" are the desk's Review items on non-archived theses: 47 warnings and 11
  withheld.
- "31 warnings" are those on the 8 theses the 11 withheld-line corrections touch.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- The corrections and dismissals are the operator's research call, applied only on their
  decision, with them as the reviewer of record.
- The re-grade gap stays open until fixed. Until then: corrections first.
