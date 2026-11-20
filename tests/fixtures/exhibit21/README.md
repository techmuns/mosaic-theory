# exhibit21 — real Exhibit 21 documents (W86)

The subsidiaries lists that `tests/test_exhibit21.py` reads, as EDGAR serves them. Each is the
Exhibit 21 of its filer's newest original 10-K, read on 2026-11-20 through the repo's SEC client
(`vinci.sec.build_sec_http`) by `scripts/w86_exhibit21_coverage.py fixtures`. They are public SEC
filings, not licensed content.

`cases.json` names each document's filer (CIK, the registrant name EDGAR's submissions document
gives), the 10-K's accession and filing date, the exhibit's own type (`EX-21`, `EX-21.1`,
`EX-21.01`) and its URL.

**Whole documents:** AMZN, GOOGL, TGT, SMPL, PARR, WERN, V, UBER.

**Cut documents:** LLY, TJX, EPAM. Each keeps the exhibit's prose and the first rows of each of its
tables (its header rows among them), plus the rows `cases.json` names under `kept_rows`. Every other
table row is removed through BeautifulSoup, so the markup that remains is the filing's own. A cut
document's name count is the cut's, never the filing's.

**Three SGML headers, whole:** Alphabet's 10-K `0001652044-26-000018`, which types its list
`EX-21.01`; its 10-Q `0001652044-26-000084`, which files none; and Oruka Therapeutics' 10-K
`0000950170-24-009809`, filed 2024-02-01 as "ARCA biopharma, Inc.", which files no Exhibit 21
(`cases.json` `historical` carries ORKA's real submissions `formerNames`).

**One index, whole:** Alphabet's 10-K `index.json`, a real EDGAR page that is not an SGML header.

What each case pins:
- **GOOGL:** "Google" is the filer's own and listed (`Google LLC`). "Lyft" is not listed (a company
  CIQ's Key Developments file under Alphabet; see `docs/records/2026-11-19-w73-googl-paid-rebuild.md`).
- **AMZN, TGT:** Whole Foods and Shipt are their filers' own and NOT listed. Both lists say they hold
  significant subsidiaries only (Reg S-K 601(b)(21)(ii)).
- **SMPL, LLY:** "Quest" and "LillyDirect" are listed only as the leading words of a longer name.
  LLY's list names affiliates too.
- **PARR:** lists part-owned companies with their shares, among them "Yellowstone Pipe Line Company
  (40.0% interest)".
- **UBER:** lists 13 names and states no omission.
- **WERN, TJX, EPAM, V:** the parser's shapes, respectively: numbered rows, section-title rows, an
  "Entity" column title, and a heading split across two text blocks.
