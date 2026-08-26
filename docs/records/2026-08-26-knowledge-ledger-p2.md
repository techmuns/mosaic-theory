---
id:
status: shipped
date: 2026-08-26
prs: []
supersedes:
superseded-by:
---

# One door for other tools, and a map for a reader arriving cold

**WHAT.** `AGENTS.md` opens as the cross-tool entry point (operator ruling: other AI tools will be
used). `docs/RUNBOOKS.md` gains a "which file answers which question" map. CLAUDE.md's header now
names all three surfaces — behaviour, snapshot, ledger — instead of two. Completes the
knowledge-ledger plan's P2.

**WHY A POINTER AND NOT A COPY.** The obvious build is to restate CLAUDE.md's rules inside
`AGENTS.md` so a non-Claude tool has them inline. That is the **twin-constant bug this repo has
already paid for twice**: the peer floor moved 6 → 5 in code while three surfaces went on saying
"under 6", and eleven committed rows contradicted their own caption until a value-level pin closed
it. Rules restated in two places drift, and the drift is silent because both copies read fine. So
`AGENTS.md` names CLAUDE.md as canonical, carries the three rules most likely to bite a tool that
skips it, and copies no sentence — enforced, not intended.

**HOW VERIFIED.** Three guards, three mutations, all caught: AGENTS.md copying a CLAUDE.md sentence
verbatim, AGENTS.md deleted, and the file map dropping a surface. The copy check compares long
sentences between the two files rather than checking for a phrase, so it catches a paraphrase-free
duplication regardless of what was copied.

**WHAT IT COSTS.** A tool that reads only `AGENTS.md` gets a map and three rules, not the whole
rulebook — one hop from the real thing. That is the deliberate trade: a short pointer that stays
true beats a long copy that quietly stops being true.
