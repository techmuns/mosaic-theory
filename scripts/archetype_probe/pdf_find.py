"""Find pages in a PDF mentioning equity market capitalization by country; print their text."""

import sys

import pdfplumber

path = sys.argv[1]
needles = [s.lower() for s in sys.argv[2:]] or ["equity market cap"]
with pdfplumber.open(path) as pdf:
    print("pages:", len(pdf.pages))
    for i, page in enumerate(pdf.pages):
        t = page.extract_text() or ""
        low = t.lower()
        if all(n in low for n in needles):
            print(f"===== page {i + 1} =====")
            print(t[:4000])
