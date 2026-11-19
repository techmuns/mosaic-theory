---
status: shipped
date: 2026-11-19
prs: [1135]
supersedes:
superseded-by:
---

# The theme desk's PDF reader no longer credits the login a layout tool wrote into the Author field: "girquark" on four Goldman Sachs reports is no author, and the upload asks for one

**WHAT.** `vinci/theme_intelligence/documents.py` reads a PDF's metadata Author with two filters:
one for a generic title and one for a placeholder user (U30b: "Microsoft Office User"). It now
has a third, `_LOGIN_AUTHOR`, which matches a LOGIN: one token of lowercase letters and digits,
joined by at most `.` `_` `-`. A login is never credited as a person. The rule applies to the PDF
Author field only. A byline, Markdown front matter and an operator's `--author` are untouched.
`docs/theme_intelligence.md` §Manual documents states the rule.

**WHY.** The $0 preflight of this week's manual uploads (2026-11-19, `upload --dry-run`, state
branch `2dda6c12`) read the author of four Goldman Sachs PDFs as `girquark`, "from the
document". The four were made with QuarkXPress 18.61, which wrote its user's login into the
Author field. The reader would have credited it for good:
- a stated `--author` is added BESIDE what the document names (`_finish`), so it cannot replace
  the login;
- `author --retract` removes only an operator-stated name.

The operator's ruling, relayed by coordinator A on 2026-11-19, was "Fix first (Recommended)",
with the rule to be principled and not "any one word". A preflight message I gave A said
`--author` "only fills a gap". It does not: the failing test showed it added beside the login,
giving `[girquark, Goldman Sachs]`. The conclusion is the same either way: once read, the login
stays.

What marks a tool-made name: the form an operating system gives a user id. A name written for a
reader carries a capital letter or a space ("Reuters", "e.e. cummings"), so one word alone never
qualifies. The trade is one-sided:
- a real name left out by this rule costs one question at upload (`--author`);
- a login kept is credited permanently and printed on the public desk.

**HOW VERIFIED.**
- *Fails first.* On main `5e380efc`, 5 of the new tests failed:
  `test_a_login_or_placeholder_in_the_author_field_is_no_author[girquark|jsmith|j.smith|a_user-2]`
  each read the login as the author, and `test_a_login_left_out_lets_the_operator_state_the_author`
  read `[girquark, Goldman Sachs]`. With the fix, all 46 tests in
  `tests/test_theme_intelligence_group7.py` pass.
- *Through the real decode path.* The tests append an incremental-update Info dictionary to a
  copy of the synthetic `glyph_mixed_synthetic.pdf`, so only the Author STRING changes and the
  reader is the production one.
- *Pins.* The positive pins are the four logins plus "Microsoft Office User", which still reads as
  no author. The negative pins are "Synthetic Strategist", "Reuters" (one word, kept),
  "e.e. cummings" (lowercase with a space, kept) and "Jan Hatzius and Synthetic Strategist"
  (split, both kept). The existing U30b test and the real-metadata test are unchanged and pass.
- *Corpus before synthetic.* The rule matches none of the registry's 47 distinct author names
  (54 name and source pairs). Only one of those names was read from PDF metadata: `Un-named`,
  which has a capital and is kept. So no stored article changes on a replay.
- *Real run.* Read locally on the 8 PDFs of 2026-11-19 (not committed; licensed), metadata only.
  The 4 Quark reports go from author `girquark` to no author, so the upload will ask for
  `--author "Goldman Sachs"`. The 4 web-saved pages are unchanged (no Author field).

**BOUNDARY.**
- Registry: `articles.jsonl` + `article_versions.jsonl` on `theme-intelligence-state@2dda6c12`,
  every author record at any nesting; 54 (name, source_field) pairs, 47 distinct names.
- Real run: the 8 PDFs in the operator's 2026-11-19 upload folder (7 Goldman Sachs,
  1 Morgan Stanley), read at this branch's head by `documents.read_document`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *Lost on purpose.* A real author written as one lowercase token in a PDF's Author field
  ("dylan") is no longer credited, and the upload asks for `--author`. This fails loud.
  Falsifier: a preflight that asks for an author of a PDF whose Author field held the person's
  real name.
- *Not caught.* A login with a capital ("JSmith") or a domain account ("CORP\jsmith") still reads
  as a person. Neither has been observed; it is not built speculatively.
- *Found, not fixed (scope).* `Un-named`, read from the PDF metadata of A-fc38d9934d44 ("Why
  Investors Are Reducing AI Exposure", gs_research), is the same class of tool-filled value and is
  still credited on the state branch. Extending the placeholder list would drop it on that
  article's next replay, so it is left to a decision of its own.
