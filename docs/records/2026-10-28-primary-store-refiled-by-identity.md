---
id: 2026-10-28-primary-store-refiled-by-identity
status: shipped
date: 2026-10-28
prs: [842]
supersedes:
superseded-by:
---

# The primary's price store is re-filed by identity: 11,047 bars leave the 30 reused tickers' current ids for their former holders, exactly as rehearsed — STATE.md §5.0 row 32 item (25) closed

**WHAT.** The operator ran row 32 item (25) from #839
(`docs/records/2026-10-28-bars-filed-under-their-own-security.md`) in the primary checkout,
after a fast-forward of `main` to `68da34ae` (#839 merged as `a40c0e75`):

```
.venv/bin/python -m vinci.cli reattribute-prices
```

It printed `reading 2,401 securities' bars as of 2026-08-05`, one `re-filed` line per id for 30
ids, then:

> done: 0 reuse(s) and 0 succession(s) newly recorded; 11,047 bar(s) re-filed, 0 carried

- **The 30 ids:** ACIC, AKTS, ARIS, BBBY, CAI, CALY, CBIO, CD, CNR, CORZ, CORZW, DBD, GOLD, HHH,
  LION, LUXE, MNR, MRLN, NIQ, NP, OPI, RCD, SAIL, SEZL, SI, TACO, TEN, TRON, VELO, WLTH.
- **The bars by id** match #839's measured store bar for bar: OPI 1,028, ARIS 998, GOLD 925,
  AKTS 829 … SEZL 1.
- **0 newly recorded:** the 30 reuses come from the committed `ticker_tenure.jsonl`, and the
  store holds no new XPRO or CLBK id, so there is no succession to record.
- **The committed tables are unchanged:** `git status -- data/snapshots` is clean at `68da34ae`.

**WHY.** The primary's store, the working store that scoring and the monitor read, held 30
reused tickers' former holders' bars under the current holders' ids. Its next refresh would not
have moved them: the ingest guard keeps new bars right, but it never revisits held ones.

**HOW VERIFIED.**
- **Rehearsed twice, on read-only backups of this store as found on 2026-10-28,** before the run:
  - with #839's branch code;
  - with the merged `68da34ae` code, which also carries #837, #838 and #841's changes to the
    resolver and the `Identity` schema.

  Both gave 11,047 bars re-filed off the same 30 ids, 0 bars changed in place, and every ledger
  and benchmark bar identical: IT, SMPL and VRRM 1,236 bars each; IWM 1,236, MDY 1,236 and SPY
  307; GOOGL has none in this store.
- **The live run's counts equal the rehearsals'.**

**BOUNDARY.**
- **Store:** the primary checkout's `data/vinci.db` as found on 2026-10-28: 2,572,227 bars, its
  latest bar 2026-08-05, 2,401 non-benchmark securities read.
- **Run:** by the operator, in the primary checkout's terminal, on 2026-10-28, at `68da34ae`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Not done by this run: XPRO and CLBK.** Their new ids are not yet in this store. The next
  weekly build records each pair, since `build_universe` runs the same repair over its
  population, and carries its history.
- **Still open:** this store is still pre-split through 2026-08-05 for IESC, SFBS, BYND and seven
  more (row 32 item (22), `restate-prices`), a separate repair. The two touch disjoint names: none
  of the ten it restates is among the 30 re-filed here.
