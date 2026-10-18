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


def first_of(items: Sequence[str], n: int, sep: str = "; ") -> str:
    """The first `n` of `items`, joined — saying "(showing n of N)" when there are more."""
    shown = list(items[:n])
    return sep.join(shown) + (f" (showing {len(shown)} of {len(items)})" if len(items) > n
                              else "")
