---
id:
status: shipped
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# The ≤2-cashtag rule is withdrawn: a flow PRINT can carry a direction

**OPERATOR RULING (2026-08-28), option 1 of three offered.** `post_class` describes the post's
FORMAT; `bias` describes the view it carries. **A single-ticker flow print stays `flow_spam` and
may still carry a direction, and those rows are scored.** The earlier ≤2-cashtag rule — that a
post naming one or two tickers is not `flow_spam` — is **WITHDRAWN**, and the guard it was going to
justify is NOT shipped.

**How it surfaced.** 75 rows were queued as contradicting the rule. **71 came back still
`flow_spam`**, 43 of them bullish — the opposite of the previous batch, where 34 of 41 became
`signal_candidate`. Checked before importing: not a capture artifact (the raw text really does name
one cashtag), and not rushed confirming (43 were `edit`, 25 `cur`, 3 `no call`).

**The distinction the operator was actually drawing** is finer than cashtag count, and reading the
two sets side by side shows it:

| kept as `flow_spam` | promoted to `signal_candidate` |
| --- | --- |
| `Alpha Gold Flow Alert 🏆 $NVDA 05/23/25 $115 Calls – $3.67M Sweep` | `$ARM whale is buying more calls for 2025 👀` |
| `Alpha Gold Flow Alert 🏆 $MSFT 10/17/25 $460 Calls – $14.57M Block` | `🌊 Alpha Gold Alert $TSLA — Large Bullish Flow… buyers` |

The kept rows are **instrument prints** — strike, expiry, premium, contract count, no comment. The
promoted ones have him speaking. Cashtag count separates lists from alerts; it does NOT separate a
print from a view.

**A GUARD PROPOSED, WITHDRAWN, RE-PROPOSED AND KILLED.** Its whole history in one entry, because
each step was published: proposed when 41 of 41 obeyed the rule → withdrawn on one apparent
counterexample → re-proposed when that turned out to be an operator slip → **killed** when 71 real
rows contradicted it. The lesson is not "wait for more data"; it is that **a rule inferred from the
rows an operator happens to have read first is a description of that sample, not a law.** The 41
were flow ALERTS because that is what the queue served first.

**AND THE SINGLE-TICKER PRINTS ARE THE BEST BUCKET IN THE BOOK.**

| bucket | direction-correct | median excess |
| --- | --- | --- |
| `flow_spam`, 1–2 tickers, directional (42) | **60%** CI [44%, 73%] | **+2.24%** |
| `signal_candidate`, directional (2,198) | 49% CI [47%, 51%] | −0.44% |
| `flow_spam`, 3+ tickers, directional (10) | 40% CI [17%, 69%] | −2.41% |

On 42 rows the interval is wide and it is NOT a finding yet — but it points the opposite way to the
prior. Following whale prints beat his own stated calls, and the multi-ticker lists remain the
worst thing in the corpus, which is what the original audit found.

**THE GUARD THAT DOES SURVIVE** is the original one, unstated until now: **multi-ticker flow LISTS
must not be scored.** 1,455 rows sit on 3+-cashtag flow lists and only 10 carry a direction. That
is the invariant worth pinning — not the cashtag rule that replaced it for one afternoon.

**Scoring.** 3,273 → 3,307 rows; **zero** already-scored rows changed verdict. Direction-correct
51.09% → **51.18%** of 2,888. Hand labels 557 → **625**.

**INCIDENT — the worktree reset mid-session.** The first import attempt failed with the U+2028
error and `vinci.calls.jsonl_lines` missing; `vinci calls accounts` then reported
`hand=83 machine=8102 tracked=214`, the pre-session corpus. The worktree had been switched to
`claude/adoring-heisenberg-d54179` at the merge-base `10e959e`. **Nothing was lost** — the work was
pushed, and `feat/calls-audit-sheet` held all 32 commits locally and on origin; `git checkout` of
the branch restored the tree whole. Recorded because the failure LOOKED like data loss and was not:
the reason it was not is that every step of this session was committed and pushed as it happened.
