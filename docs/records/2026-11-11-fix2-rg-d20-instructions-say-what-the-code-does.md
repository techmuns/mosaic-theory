---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, RG-D20: thirteen instructions that contradicted each other or the code now say what is true. Comments, docstrings and prose only — no code path, page or synthesis request moves

**WHAT.** Each item of RG-D20 (the audit's G-D20 table, items a–m) is corrected where it stands.
None changes behaviour. Two items, (b) and (j), are the same defects as G-D15 and G-D14, which
#998 (order 9) fixed under those IDs while this was in review. The re-sync keeps #998's wording
for both, and its tests (`tests/test_ciq_notes_follow_the_code.py`) pin them.

| # | where | was | now |
|---|---|---|---|
| a | `vinci/graph/llm.py`; `tests/test_llm_sampling.py`'s docstring; record `2026-09-24-sampling-parameters-are-unavailable.md` | "every LLM phase runs through this one call site" | Every phase goes through this client, but the theme client's cached-article path and the eval replay call `messages.create` too, with no sampling parameter. The record gets an appended amendment; its body is unchanged |
| b | `docs/engineering.md` | "pin what you can (low/0 temperature…)" | **by #998 (G-D15)**: pass no sampling parameter; the lean label is handled by the draw gate |
| c | `vinci/dossier/synthesis.py` (number trace) | "Direction is the directional-lint's job" | The lint reads recommendation words, never a sign. `_recompute` and `material_direction_flags` compare a sign; any other figure is traced by magnitude |
| d | `synthesis.synthesize` docstring | "no numbers are derived from [the transcript]" | The prompt asks for none. A figure cited to a call anyway is KEPT, with a TRANSCRIPT-FIGURE flag that is machine-tier QA, hidden from the page |
| e | `CLAUDE.md` header | RUNBOOKS holds "monthly sweep, group-review recording, survivor checks, theme-advance … calendar" | the loops RUNBOOKS holds today; §a–d and §h retired 2026-11-04 |
| f | `AGENTS.md` | "this file is a POINTER" | names its one deliberate exception: the Code Review Rules, repeated in `.gemini/styleguide.md` because each reviewer reads only its own file, pinned equal by `test_review_process` |
| g | `.gemini/config.yaml` | "a COMMENT-ONLY second reviewer" | inert: Gemini is not installed (operator decision 2026-10-23) |
| h | `docs/RUNBOOKS.md` §n step 1 | "today only `M-LABEL`" can be a target | `M-GAP` joined it after meeting its bar on fresh gold; #927's registration targeted it |
| i | `docs/ciq_extraction_notes.md` rule 4 | "Do not hardcode positions", beside "row 7", "row 14", "rows 0-12", "row 17" | those numbers are where the exports seen put them, for orientation; find each row by its label |
| j | the same file's opening | "duplicated in … checklist.md" | **by #998 (G-D14)**: `checklist.md` is not in this repository |
| k | `vinci/verbatim.py`; `driver_extract.py`'s docstring | "this is that rule as one shared helper"; "covenant extraction trusts the model … (prompt-only)" | Covenants use the shared helper. `driver_extract` keeps its own `_norm`, whitespace and case only, so a re-typed curly quote passes one and drops a row in the other |
| l | `docs/CLOUD_DOSSIER_TRIGGER.md` | `require_env()` at `config.py:136`, and other `file:line` references | The references are dated 2026-06-26 and moved since; read each by its symbol |
| m | `docs/engineering.md` | the gate covers "`vinci` only — 111 source files" | state the count mypy prints: 206 at `6d9907d7` |

**Beyond the table, flagged.** Fixing (a) and (k) surfaced two more sentences making the same false
claims, so they are corrected with them:
- the sampling test's docstring;
- `driver_extract.py`'s description of covenant extraction.

**WHY.** An instruction that contradicts the code is followed: the next agent pins a temperature,
trusts a direction check that does not exist, or reads a retired loop as live. These are G-D20's
thirteen, each checked at the pin and again here against main `6d9907d7`.

**HOW VERIFIED.**
- Every claim the new wording makes was read in the code it names:
  - the two other `messages.create` sites;
  - `_recompute`'s signed comparison and `material_direction_flags`;
  - `TRANSCRIPT-FIGURE` in `flags._QA_MARKERS`;
  - `driver_extract._norm`;
  - `covenant_extract`'s import of `vinci.verbatim`;
  - `require_env` at `vinci/config.py`;
  - `mypy --strict vinci` printing 206 files;
  - the M-GAP records;
  - `test_review_process` pinning the two review lists equal.
- No watched module's hash moved: `tests/test_extraction_version_drift.py` passes, because
  comments and docstrings are not hashed.
- The amended record passes the ledger's immutability guard: the body is unchanged and an
  amendment is appended.

**BOUNDARY.** "206 source files": `python -m mypy --strict vinci` at main `6d9907d7`, 2026-11-11.
