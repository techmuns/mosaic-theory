"""Find pages in a PDF mentioning equity market capitalization by country; print their text, each
page cut at CAP characters and saying so.

    python scripts/archetype_probe/pdf_find.py <file.pdf> [needle ...]
"""

from __future__ import annotations

import sys

CAP = 4000


def shown(text: str, cap: int = CAP) -> str:
    """The page's text up to ``cap`` characters; a cut page says it was cut, and by how much."""
    if len(text) <= cap:
        return text
    return f"{text[:cap]}\n…[cut: showing {cap:,} of {len(text):,} characters]"


def main(args: list[str]) -> None:
    import pdfplumber

    path = args[0]
    needles = [s.lower() for s in args[1:]] or ["equity market cap"]
    with pdfplumber.open(path) as pdf:
        print("pages:", len(pdf.pages))
        for i, page in enumerate(pdf.pages):
            t = page.extract_text() or ""
            if all(n in t.lower() for n in needles):
                print(f"===== page {i + 1} =====")
                print(shown(t))


if __name__ == "__main__":
    main(sys.argv[1:])
