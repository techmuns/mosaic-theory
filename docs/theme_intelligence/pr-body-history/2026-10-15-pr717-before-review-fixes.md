**Stacked on #715** (base `claude/theme-intelligence-money`): both edit the spend guard and the extraction. Merge #715 first; this PR then needs a rebase onto main.

Operator, 2026-10-15: "…move to group 2". Group 2 is the money leads (`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`). U3, U4 and U26 are in #715, and U23d was fixed in #711, which leaves U23a–c. The full account is in `docs/records/2026-10-15-theme-intelligence-group-2-leads.md`.

## What changes

- **U23a: one re-asked part may take the whole limit set for it.** `reask-part --max-cost 1.00` refused a $0.90 call, because the guard held it to a retry's 85% share. `SpendGuard.begin_document(retry_share=)` now takes the share as a parameter: `reask-part` passes the whole limit, and every other document keeps 85%.
- **U23b: `--refresh` says what it does.** It "asked again" but made no model call. That behaviour is the repo's rule for paid answers ("paid once, never asked again"), and an existing test pins it. The flag's help, the run's note and the docs now say what it does: the pass runs again, the paid answer comes from the cache (set its file aside to have the model asked anew), and every name is checked against the SEC again.
- **U23c: a truncation marker holds at the cap it was written at.** A marker written at 16,384 tokens forced COMPACT after the cap was raised to 64,000. `extract.marker_holds` now compares caps, in extraction and completeness:
  - a higher cap asks the full request again;
  - a marker or a client that states no cap still holds;
  - a cached compact answer is still reused.

  The client now states its cap (`AnthropicLlmClient.max_tokens`), and `GuardedClient` passes it through.

## Real-run verification

The base is #715's head (8d9ce177), compared with this branch.

```
U23c (verifier's script)  base    calls sent (True = compact request): [True]
                          branch  calls sent (True = compact request): [False] | result compact: False
U23a (end to end through reask_part, --max-cost sized so the call takes 90% of it)
                          base    BudgetExceeded: a completeness call bounded at $0.62 does not fit the remaining $0.59
                                  of the retry / completeness limit $0.59 (D-737cf809ea03c04c part ) — not sent
                          branch  the one call is sent
```

Real data, under the theme-intelligence worktree:
- **U23a:** the one real paid re-ask (Gridlock part 4) was bounded at $0.9769 and billed $0.5278. Under the 85% share it needed `--max-cost` of at least $1.15; now $0.98 suffices. The 2 stored refusals are deliberate `--max-cost 0.01` runs, and they stay refused.
- **U23c:** all 4 real truncation markers record today's 21,333 cap. They all still hold, so nothing stored is re-asked and no cost changes.

Checks:
- Pins: `tests/test_theme_intelligence_group2.py`, 12 tests. Against the base, 6 fail and the 6 that pass are negatives.
- Mutants: 13 of 13 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean.

Offline suite (`pytest -m "not network"`): **5,400 passed, 513 skipped, 37 deselected** (exit 0); record and STATE lints 722 passed.

## Disposition

| Item | Status | Note |
|---|---|---|
| U23a: a re-ask may take the whole limit set for it | SHIPPED | pinned end to end through `reask_part` |
| U23b: `--refresh` | SHIPPED (wording) | the behaviour is kept by the paid-answer rule; a re-buying flag is the operator's call |
| U23c: a marker holds at its cap | SHIPPED | no stored marker is affected |
| U23d | — | already fixed in #711 |
| U3, U4, U26 | — | in #715 |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

