"""Scoring a public commentator's stated calls against realised prices.

A RESEARCH-INPUT SUBSYSTEM, not a decision path. Nothing here feeds the screen, the ranker, the
ledger or the BUY-AVOID spread; it scores a third party's published calls so a human can read the
hit-rate of an outside voice. It reads the same Polygon bars the fund uses and nothing else.
"""


def jsonl_lines(text: str) -> list[str]:
    """Split JSONL on NEWLINES ONLY — never ``str.splitlines()``.

    A JSONL record ends at ``\n``. Python's ``splitlines()`` is UNICODE-aware and also breaks on
    U+2028, U+2029, U+0085 and the vertical-tab family — none of which ``JSON.stringify`` escapes,
    because all of them are legal unescaped inside a JSON string. So a record carrying one is torn
    in half by the reader and the file will not parse.

    Not hypothetical: a ``$WMT`` post in this corpus contains U+2028 (18 of the 5,641 posts do),
    and the browser bench's export of it read back as 186 lines for 185 rows. It failed LOUD rather
    than merging half a row — but that row could never be imported at all.
    """
    return [ln for ln in text.split("\n") if ln.strip()]
