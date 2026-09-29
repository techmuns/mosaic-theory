---
id: 2026-09-29-the-filing-id-was-lowercase
status: shipped
date: 2026-09-29
prs: [656]
supersedes:
superseded-by:
---

# The filing id was lowercase, and the fixture that proved the fix was not

**WHAT.** #655 swapped the strip order so a leading filing id could not hide the amendment prefix.
The order was genuinely wrong and the swap is kept. **It did not fix the page.** Re-assembling
WERN on #655 produced the identical broken heading:

    Covenants — 20260605EX101 1758963679 24780046 AMENDMENT NO. 3 TO LOAN AND SECURITY AGREEMENT

The real cause is one character class. `_LEAD_CODE`'s alphanumeric branch was `[A-Z0-9]{6,}` —
uppercase only — and WERN's id arrives **lowercase**: `wern-20260605ex101`. It never matched, in
either order. The trailing `.upper()` in `agreement_title` then rendered the surviving id in
capitals, which is precisely why it looked like an uppercase token and why an uppercase fixture
seemed to reproduce it.

**WHY THIS GOT THROUGH, AND IT IS THE POINT OF THIS RECORD.** #655's pin used a hand-typed
approximation of WERN's head with the id in CAPS. That string matched `[A-Z0-9]{6,}`, so the pin
went green, the mutation was caught, the suite passed, and the defect shipped untouched. The rule
this repo already holds — CORPUS BEFORE SYNTHETIC, fixtures are built from the REAL type — exists
for exactly this, and I transcribed the document instead of fetching it. A fixture retyped from a
document is not that document: the one detail I normalised away while typing was the detail that
mattered.

**HOW VERIFIED.**

*The real documents, byte-for-byte as EDGAR serves them* (both now pinned, copied not typed):

    wern-20260605ex101 ... AMENDMENT NO. 3 TO LOAN AND SECURITY AGREEMENT -> LOAN AND SECURITY AGREEMENT
    wern-20260605ex102 ... PERFORMANCE GUARANTY                           -> PERFORMANCE GUARANTY

*The guards that make case-insensitivity safe*, unchanged: `AMENDED AND RESTATED CREDIT AGREEMENT`
(the digit requirement keeps the widened class off digitless words), `364-DAY CREDIT AGREEMENT`
(a hyphen still protects a real name), `SECOND AMENDED AND RESTATED CREDIT AGREEMENT` (BURL's
chain).

*A guard at the layer the defect was visible at.* Both unit pins in #655 passed while the page
published a filing id as a contract name — a pin on the reader cannot see the page. **New
end-to-end pin** over `frontend/dossiers/*.md`: no rendered covenant heading may begin with a
filing-id-shaped token (>=6 alphanumerics, carrying a digit, no hyphen). Checked against the real
shapes: it REJECTS `20260605EX101 …` and ALLOWS `364-DAY CREDIT AGREEMENT`,
`FIVE-YEAR REVOLVING CREDIT AGREEMENT`, `2025 Convertible Notes`, `24 Credit Agreement`,
`SECOND AMENDED AND RESTATED CREDIT AGREEMENT`, `LOAN AND SECURITY AGREEMENT`. It asserts a
non-zero heading count first, so it cannot pass vacuously.

*Mutation — two, both caught.* K1 reverts the class to `[A-Z0-9]` — the #655 blind spot — and is
caught by the real-document pin, which is the pin #655 lacked. K2 drops the digit requirement and
is caught by three separate pins. Source restored byte-identical.

**BOUNDARY.** Measured 2026-09-29 off `e78037bc`. WERN is the only name whose rendered covenant
heading carries a filing id; population = the 26 committed dossiers, unit = rendered
`- **Covenants — …**` headings. The end-to-end pin currently passes on the COMMITTED pages because
WERN's broken page was never committed — it exists only in the pending fleet artifact set, which
is where the pin will bite. Verified against that pending page directly: it rejects the heading.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **Case-insensitivity widens the code branch onto ordinary words, and only the DIGIT requirement
  holds it off them.** If a contract is ever named with a digit-bearing word of six or more
  characters and no hyphen, its first word will be stripped. Not observed across 144 exhibit
  heads. *Falsifier:* a heading that loses its first word.
- **The end-to-end pin keys on a SHAPE, not on correctness.** A wrong-but-well-formed heading
  passes it. It catches the id class, nothing more.
- **NOT FIXED (unchanged):** `render.py:1245`'s duplicated lead; the pointer layer's class-generic
  queries; CNXC "Other Loans"; the ancillary SECURITY AGREEMENT as a governing family.
