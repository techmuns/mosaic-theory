---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# A JSONL record ends at \n, and `str.splitlines()` does not agree

**The break.** Importing the bench's 185-row export failed:
`_export.jsonl:140: not valid JSON — Unterminated string`. The file's hash matched the browser's
byte-for-byte, so the export was fine. Python read **186 lines for 185 rows**.

**Cause.** A `$WMT` post contains **U+2028 LINE SEPARATOR**. `JSON.stringify` does not escape it —
it is legal unescaped inside a JSON string — but `str.splitlines()` is UNICODE-aware and treats it
as a line break, tearing one record in half. **18 of the 5,641 posts carry U+2028.**

Only three characters can reach a reader raw this way: **U+2028, U+2029, U+0085**. Everything else
`splitlines()` honours (the vertical-tab family, U+001C–1E) is below 0x20, and every conformant
JSON writer escapes those — so they can never appear unescaped and are not part of the bug.

**It failed LOUD, which is the only reason this is a small entry.** The parse rejected the fragment
instead of merging half a row, and `import_labels` parses the WHOLE file before writing anything —
so nothing reached the corpus. But that row could never be imported at all.

**Fix.** One shared `vinci.calls.jsonl_lines()` splitting on `\n` only, and all four JSONL readers
routed through it — `import_labels`, the gold-label reader, `load_audit`, and `sheet._rows`'
results reader. Three of the four were not yet biting (their committed files happen to be clean),
and fixing only the one that bit would have left the same landmine under files that grow.

**Pinned.** `tests/test_calls_ingest.py` — the three raw-capable characters parametrised, plus the
verbatim `$WMT` shape that shipped, both written with `ensure_ascii=False` because that is what
`JSON.stringify` does. Each asserts the fixture still reproduces the tear before asserting the fix.
MUTATION-CHECKED: restoring `splitlines()` reddens all four.

**Also shipped: a loopback export endpoint.** The bench's export had been round-tripped by hand
three times — read out through the JS console, base64'd, pasted into a shell heredoc, hash
re-verified. Entirely mechanical, so it moved into the dev server: `POST /_export` writes the body
to a FIXED filename in the served scratchpad directory. Loopback-bound, dev-only, request cannot
choose the path, nothing near the repo. `serve_nocache.py` is scratchpad tooling, not shipped code.

**The import.** 185 rows — 122 new, 63 idempotent. Hand labels **146 → 268**.

| | before | after |
| --- | --- | --- |
| scored rows | 3,279 | 3,261 |
| direction-correct | 51.10% | **51.00%** of 2,841 |
| the HAND subset | 59.0% of 78 | **56.1%** of 123 |

Four previously-scored rows changed verdict; no row lost a `post_class`.
