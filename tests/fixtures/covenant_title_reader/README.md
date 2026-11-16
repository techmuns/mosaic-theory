# Covenant title-reader heads (STATE row 63)

`heads.json` holds 33 real EDGAR exhibit heads as the covenant phase reads them. Each `head` is the
start of the text `covenant_extract._fetch_exhibit` returns (`html_to_text` over the filed
document), cut short. Public filings, not licensed data. `tests/test_covenant_title_reader.py`
reads it.

**Which heads.** These come from the $0 audit of 2026-11-16 at main `032d2fde`. It ran the real E5
loop over the 24 committed pages with pointer rows, cache-only, with the model stubbed.
- 30 heads are every located exhibit the loop refused as not a debt agreement.
- 3 are corpus heads that no committed pointer targets: two press releases and an exchange
  agreement. They come from the 3,575 cached archive documents, and the new reader is held
  against them.

**The fields.** `filing` is the pointer row's form and accession, or `corpus <accession>`. `family`
is the pointer's guess, blank for the corpus heads. `kind` is the audit's hand-read verdict, and
`is` gives its one-line evidence. The 5 `debt agreement` heads were refused wrongly. Every other
kind is a correct refusal:

| kind | n | heads |
|---|---|---|
| debt agreement | 5 | VRRM `vrrm-ex10_1.htm` (Amendment No. 4 to its Revolving Credit Agreement); CNXC third and fourth amendments to its Receivables Financing Agreement; NFLX 2018 and 2014 senior-notes purchase agreements |
| a titled contract that is not debt | 7 | BRBR LLC agreement, FUBO registration rights, NCNO office lease, PARR restricted stock award, V put-call option, VRRM GORES II subscription, WERN stock purchase |
| a plan, policy, award or notice | 10 | BURL, CNXC, EPAM, FUBO, LLY, NFLX, ORKA, TECX, TJX, VITL |
| a letter or a dealer confirmation | 4 | NKE offer letter, TGT transition letter, CNXC put option letter, UBER capped-call confirmation |
| the 8-K's own cover document | 1 | TGT `form8-k_creditagreement105.htm` |
| a bank commitment letter | 2 | IT 2017, NFLX 2025: headed by a code name ("Project Cobra Commitment Letter"); kept refused, an open question for the gate |
| an exchange agreement for convertible notes | 2 | FUBO (on a pointer row), BURL (corpus) |
| a press release | 2 | CNXC's notes-offering release and VRRM's 2026 release (corpus) |

**How each head was cut.** Each head is the first 3,000 characters read from the operator's EDGAR
cache (`data/cache/sec`, cache-only: a miss raised, and nothing was fetched). It is then cut to the
shortest length, at least 300 characters in steps of 50, at which two readers give the same
`agreement_title`, `is_debt_agreement` and `is_amendment` as on the full 3,000. The two readers are
the base reader (main `032d2fde`) and this PR's reader. So every pin reads the cut exactly as the
loop reads the whole exhibit, before and after the change. 32 heads are 300 characters long.
NCNO's office lease is 550, because its recital names the lease.

To re-fetch one, call `_fetch_exhibit(build_sec_http(), cik, accession, exhibit)`, where `cik` is
the page's own CIK. Cut it as above, and re-fetch an entry only together with the pins that read it.
