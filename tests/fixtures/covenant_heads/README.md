# Covenant exhibit heads

`heads.json` holds real EDGAR exhibits as the covenant phase reads them: each `head` is the first
3,000 characters `covenant_extract._fetch_exhibit` returns (`html_to_text` over the filed document).
That is all of `agreement_title`'s input, since it reads only `text[:3000]`. `is_amendment` reads
less (`text[:1500]`). Public filings, not licensed data.

Written 2026-11-04 at main `4a820016` from the EDGAR cache. Each `filing` is the accession the
committed page's pointer row carries, and the form shown is that row's form. Every entry was a
covenant-phase TARGET on a committed page (`_core_agreement_exhibits` over its
`covenant_pointer_rows`) and was refused by the IDENTIFY-OR-REFUSE guard at that commit:

| ticker | exhibit | what it is | the guard should |
|---|---|---|---|
| SMPL | `f8k032018ex10-1_simplygood.htm` | Repricing Amendment to the 2017 Credit Agreement | pass |
| SMPL | `a19-22146_1ex10d1.htm` | Amendment No. 2 (Incremental Facility Amendment) to it | pass |
| NCNO | `firstamendmenttocreditagre.htm` | First Amendment to the 2022 Credit Agreement | pass |
| NCNO | `exhibit1035secondamendment.htm` | Second Amendment to Office Lease | refuse |
| TJX | `tjx-20260131xexhibit1024.htm` | First Amendment to a stock incentive plan (2,404 chars in all) | refuse |
| NKE | `nke-5312026exhibit1029.htm` | CFO offer letter | refuse |
| TGT | `tgt20260131-exhibit1018.htm` | CEO transition letter | refuse |
| TGT | `form8-k_creditagreement105.htm` | the 8-K's own cover document, which cites "the Credit Agreement" | refuse |
| VRRM | `vrrm-ex10_1.htm` | Amendment No. 4 to the Revolving Credit Agreement, with a title-cased heading | not be renamed "CREDIT AGREEMENT" from its recital (a separate shape, still refused) |
| UBER | `e23472_ex10-1.htm` | capped-call dealer confirmation | refuse |

To re-fetch one, call `_fetch_exhibit(build_sec_http(), cik, accession, exhibit)[:3000]`, where
`cik` is the page's own CIK. Re-fetch an entry only together with the pins that read it
(`tests/test_covenant_document_identity.py`).
