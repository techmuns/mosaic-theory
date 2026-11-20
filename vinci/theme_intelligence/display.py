"""Display helpers every reader-facing surface shares — the card, the desk, the weekly report, the
CLI and the notes the engine stores. CLAUDE.md: A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION, so a
cut line says it is cut and where the rest is, and a cut list says how many it holds (U36). No
imports from this package: any module may use it.
"""

from __future__ import annotations

from collections.abc import Sequence


def clip(text: str, n: int, where: str = "the JSON export") -> str:
    """A shortened display line PRINTS ITS OWN TRUNCATION — the full value stays in `where`."""
    if len(text) <= n:
        return text
    return f"{text[:n].rstrip()}… [+{len(text) - n} chars — full text in {where}]"


#: THE LONGEST SOURCE QUOTE THE DESK PRINTS, in characters (operator ruling 2026-11-19, relayed by
#: coordinator A). CLAUDE.md lets the desk publish a source's own words only as SHORT verbatim
#: quotes, never its text. Set by face validity above every quote the desk held before the
#: incident: on the 2026-11-19 republish (#1139), 1,283 distinct claim quotes, the longest 911 (a
#: forecast table read as one block), the next 354.
DESK_QUOTE_MAX_CHARS = 400
#: printed beside a quote the desk shortened; the claim keeps every word
DESK_QUOTE_NOTE = "quote shortened for the desk — the claim keeps the source's full words"


def desk_quote(text: str) -> tuple[str, bool]:
    """A source's own words as the desk prints them: whole up to `DESK_QUOTE_MAX_CHARS`, else cut
    at the last word that fits, with "…" counted inside the cap (one unbroken token longer than
    the cap is cut where the cap falls). Returns (the text, whether it was cut). A cut quote is
    printed with `DESK_QUOTE_NOTE` beside it: a truncation says so."""
    if len(text) <= DESK_QUOTE_MAX_CHARS:
        return text, False
    head = text[:DESK_QUOTE_MAX_CHARS - 1]  # room for the "…"
    if not text[len(head)].isspace():  # the cap falls inside a word: end at the one before it
        space = max(head.rfind(" "), head.rfind("\n"), head.rfind("\t"))
        head = head[:space] if space > 0 else head
    return head.rstrip() + "…", True


def first_of(items: Sequence[str], n: int, sep: str = "; ") -> str:
    """The first `n` of `items`, joined — saying "(showing n of N)" when there are more."""
    shown = list(items[:n])
    return sep.join(shown) + (f" (showing {len(shown)} of {len(items)})" if len(items) > n
                              else "")
