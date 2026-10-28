# Frozen companyfacts for the fiscal-year label pins

`tests/test_period_labels.py` reads these. They track NO page and are never regenerated: each
freezes a real filer in the shape that made a period label wrong, or that the label rule must
refuse (`docs/records/2026-10-28-a-label-names-its-own-year-and-a-rate-its-own-quote.md`).

Cut 2026-10-28 from the shared SEC cache, unmodified apart from the tag subset, in the exact
companyfacts shape (`sort_keys`, `indent=1`). Each keeps the aliases
(`vinci.edgar.concepts.CONCEPT_ALIASES`) of the fiscal calendar's inputs — revenue, net income,
diluted EPS — and of the concepts its pin reads. Each subset was checked at cut time to give the
pinned reader's output exactly as the full blob does.

| file | filer (CIK) | fetched | concepts kept | pinned reader |
|---|---|---|---|---|
| `WWW.json` | Wolverine World Wide (110471) | 2026-08-13 | calendar, operating cash flow, capex | `anchor._latest_fcf` |
| `TATT.json` | TAT Technologies (808439) | 2026-09-23 | calendar, operating cash flow, capex | `anchor._latest_fcf` |
| `CIK1653558.json` | Priority Technology Holdings (1653558) | 2026-08-13 | calendar | the fallback's revenue trajectory line |

- **Wolverine** stamps its 10-Ks for the years to 2024-12-28 and 2026-01-03 both `fy=2024`.
- **TAT** files 20-Fs: no 10-K states any of its years.
- **Priority** stamps two 10-Ks `fy=43465` and `fy=43830`, the spreadsheet serials of
  2018-12-31 and 2019-12-31. Its subset carries no EBITDA or FCF line, so only the trajectory's
  revenue line matches the full blob's.
