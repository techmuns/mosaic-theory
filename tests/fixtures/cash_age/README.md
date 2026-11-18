# Frozen companyfacts for the net-debt cash pins

`tests/test_net_debt_cash_age.py` reads these. They track NO page. Each freezes a real filer whose
cash line is, or was, read at the wrong balance sheet (STATE.md §5.0 row 11 (b),
`docs/records/2026-11-19-net-debt-reads-its-cash-at-the-newest-balance-sheet.md`).

Each was cut from the primary checkout's SEC cache: the cached response's `text`, decoded as
`EdgarClient.companyfacts` decodes it, and left unmodified apart from the tag subset. Each keeps
`vinci.edgar.net_debt.READ_TAGS` in `us-gaap` and `ifrs-full`, which includes both cash aliases
and `Assets`, the total that dates the newest balance sheet. Every other tag and namespace is
dropped. The format is the exact companyfacts shape with `sort_keys` and `indent=1`, like the other
frozen fixtures.

**Checked 2026-11-19 against the full blob, at main 5152d885 and at this branch.** `net_debt` (its
date, cash tag and value, both bases and the refusal) and `balance_sheet_date` read the same on
the subset as on the full blob: uncut, cut at 2026-10-16 (screen run 2026-10-16-01's price date)
and cut at 2009-11-30. The result was 0 of 33 readings differing.

| file | filer (CIK) | fetched | shape |
|---|---|---|---|
| `PMT.json` | PennyMac Mortgage (1464423) | 2026-11-11 | cash aliases stop 2018-12-31, balance sheets to 2026-09-30: refused by the backstop |
| `JACK.json` | Jack in the Box (807882) | 2026-07-06 | no alias at its 2026-04-12 balance sheet; the walk's cash is 280d older: refused |
| `AHCO.json` | AdaptHealth (1725255) | 2026-11-11 | no alias at its 2026-06-30 or 2026-09-30 balance sheet; cash stops 2026-03-31: read at the run's cut (91d), refused today (183d) |
| `DBD.json` | Diebold Nixdorf (28823) | 2026-11-11 | `CashAndCashEquivalentsAtCarryingValue` to 2026-03-31, the restricted-cash total every quarter: read at 2026-09-30 (today) and 2026-06-30 (the run's cut) |
| `EMN.json` | Eastman Chemical (915389) | 2026-11-11 | the first alias only in its 10-K, the second in its 10-Qs: the oscillation; read at 2026-06-30 at the run's cut |
| `MORN.json` | Morningstar (1289419) | 2026-07-06 | the first alias to 2025-12-31, the second at its 2026-03-31 balance sheet |
| `HIMX.json` | Himax (1342338) | 2026-11-11 | us-gaap cash to 2017-12-31, IFRS balance sheets to 2025-12-31 |
| `SID.json` | National Steel (1049659) | 2026-07-06 | us-gaap cash to 2009-12-31, IFRS balance sheets in BRL to 2024-12-31 |
| `V.json` | Visa (1403161) | 2026-11-11 | both aliases at its 2026-09-30 balance sheet, $12,938M and $19,118M: the first is read |
| `TATT.json` | TAT Technologies (808439) | 2026-06-27 | an annual filer: its year end is its newest balance sheet |
| `ROP.json` | Roper Technologies (882835) | 2026-11-11 | a 10-Q filed 2009-11-02 tags `Assets` at 2009-12-31, a forward date |

`AHCO.json`, `EMN.json` and `V.json` were cut on 2026-11-19. The other eight were cut on 2026-11-17 for
option 1, the bound as first built, and are unchanged.
