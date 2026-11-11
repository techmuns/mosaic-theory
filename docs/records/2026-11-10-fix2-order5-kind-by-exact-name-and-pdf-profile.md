---
status: shipped
date: 2026-11-10
prs: [970]
supersedes:
superseded-by:
---

# Fix request 2, order 5, the CIQ reader's RA-D10 (= A-D15 = RBC-D2) and RA-D17: a file's kind is its name's exact rule, never a keyword anywhere in it, and a PDF tearsheet is read as a PDF. No page moves

**WHAT.**
- **RA-D10 = A-D15 = RBC-D2** (`ciq.workbook_kind`, `_KIND_NAME_RULES`, `_customers_role`). CIQ
  names an export "<company> <exchange> <ticker> <kind>". The kind keywords matched ANYWHERE in
  the name, so the company's own name chose the kind:
  - every file of "Synchrony Financial"'s pack read as financials, and the pack was refused as
    "more than one export of a kind";
  - with only its Customers file, F27 read MISSING;
  - "Customers Bancorp"'s Suppliers file was read as its Customers.

  The kind is now decided by an exact rule on the stem: its end after the listing (" Customers",
  " Financials_Annual", "EstimatesReport", …), the comps book's start ("Company Comparable
  Analysis "), or a call's dated tail (", Q3 2026 Earnings Call, Oct 15, 2026"). Customers and
  Suppliers files are told apart by their end. `customer_roster` and the evals harness's comps
  lookup read the same rule.
  - "Public Investment Firm Profile", the contract's name for a REIT or asset-manager tearsheet,
    is now a profile.
  - A download's duplicate ("… Customers 2.rtf", "… Financials_Annual (1).xls") keeps its kind,
    so it meets the one-export refusal beside the original rather than losing to it unseen
    (review round 0).
- **RA-D17** (`ciq_sheets.gics_industry`). The tearsheet was decoded with `rtf_to_text` whatever
  its bytes, so a PDF tearsheet read "no Primary Industry Classification". It is now decoded by
  its own format (`read_text`), and a PDF's layout text, which holds the value on the label's own
  line, is read there first.

**WHY.** Document 15, order 5: "File kinds come from the file's content or an exact name rule,
never a keyword anywhere in the name".

**HOW VERIFIED.**
- **The real case.** SMPL's 11 exports were linked (not copied) under "Synchrony Financial NYSE
  SYF" names in a temporary folder. At `origin/main` the bundle raised `CiqAmbiguousError`
  ("financials: ['Company Comparable Analysis Synchrony Financial.xls', …"). Here it builds and
  its roster reads, PRESENT with 6 customers.
- **Fail first.** `tests/test_ciq_file_kinds_and_pdf_profile.py`, 20 cases, passes here, run from
  the primary checkout's licensed folder. On `origin/main` it fails at import, since
  `workbook_kind` does not exist there.
  - The real pins use four issuers' names (Synchrony Financial, Realty Income, Customers Bancorp,
    Consensus Cloud Solutions) over SMPL's pack.
  - The PDF pin converts SMPL's real tearsheet with LibreOffice and reads the same industry as the
    RTF.
  - The twins run on name strings and a stubbed layout text.
- **No page moves.** All 382 files in the 36 folders on disk keep the kind the keyword gave them,
  and `customer_roster` and `gics_industry` give the same value on all 36 folders (0 of 72 cells
  differ). Every tearsheet on disk is RTF. No synthesis request changes.

**BOUNDARY.** The exports under the primary checkout's `data/manual/ciq/` on 2026-11-10.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A name that matches no rule is unrecognised, and the assembler names it in the page's caveats.
- The rules are CIQ's own shapes as the 382 files show them. A future export shape needs a rule
  here, which the first such file shows by being named, never misfiled.

**Extraction version** `2026-11-10.kind-by-exact-name`; the drift pins are re-pinned.
