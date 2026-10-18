"""Write `glyph_mixed_synthetic.pdf` — a SYNTHETIC PDF whose text layer is partly UNDECODABLE.

A real PDF, written byte by byte, read by the real reader (pdfplumber): two fonts — standard
Helvetica (decodable) and "SyntheticNoMap", a Type0 / Identity-H font with NO character map
(no ToUnicode), which a text extractor can only report as "(cid:N)" codes — the failure seen on
the last seven pages of a real 60-page research PDF (2026-10-11).

    page 1  readable: a heading, a paragraph with figures
    page 2  MIXED: readable lines; a line that merely MENTIONS "(cid:12)" once; undecodable lines;
            a ruled 3 x 2 table, one of whose cells is undecodable
    page 3  every line undecodable, and a small image (so it is never mistaken for a scan)

Run from the repo root:
    python tests/fixtures/theme_intelligence/synthetic_documents/make_glyph_fixture.py
"""

from pathlib import Path

OUT = Path(__file__).parent / "glyph_mixed_synthetic.pdf"


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def readable(x: int, y: int, size: int, text: str) -> str:
    return f"BT /F1 {size} Tf {x} {y} Td ({esc(text)}) Tj ET\n"


def coded(x: int, y: int, n: int, start: int) -> str:
    """A line of `n` glyphs in the font with no character map (2-byte Identity-H codes)."""
    hexs = "".join(f"{(start + i) % 90 + 3:04X}" for i in range(n))
    return f"BT /F2 10 Tf {x} {y} Td <{hexs}> Tj ET\n"


def grid(x0: int, y0: int, widths: list[int], rows: int, h: int) -> str:
    """Ruling lines for a table (pdfplumber finds tables by their lines)."""
    w = sum(widths)
    ops = [f"{x0} {y0 - r * h} m {x0 + w} {y0 - r * h} l S" for r in range(rows + 1)]
    x = x0
    for cw in [0, *widths]:
        x += cw
        ops.append(f"{x} {y0} m {x} {y0 - rows * h} l S")
    return "0.5 w\n" + "\n".join(ops) + "\n"


page1 = (readable(72, 740, 9, "[SYNTHETIC TEST FIXTURE - invented content, no real publisher]")
         + readable(72, 700, 18, "Synthetic Grid Note")
         + readable(72, 670, 10,
                    "Transmission capital expenditure rose 18% in 2026 to $42 billion,")
         + readable(72, 656, 10, "and substation orders are projected to grow 12% in 2027 as")
         + readable(72, 642, 10, "interconnection queues lengthen across the synthetic regions."))
page2 = (readable(72, 740, 10, "Readable on a mixed page: transformer lead times reached 30 months")
         + readable(72, 726, 10, "in 2026, according to this invented note.")
         + readable(72, 700, 10,
                    "A sentence that mentions (cid:12) once is ordinary text and stays.")
         + coded(72, 670, 40, 0) + coded(72, 656, 38, 7) + coded(72, 642, 41, 13)
         + grid(72, 600, [150, 150], 3, 20)
         + readable(76, 586, 10, "Metric") + readable(226, 586, 10, "Value")
         + readable(76, 566, 10, "Capex growth") + readable(226, 566, 10, "18%")
         + readable(76, 546, 10, "Note") + coded(226, 546, 12, 29)
         + readable(72, 500, 10, "Readable again below the table: a 7% rise in reserve margins."))
page3 = ("".join(coded(72, 740 - 14 * i, 44, 5 * i) for i in range(12))
         + "q 20 0 0 20 500 60 cm /Im1 Do Q\n")

objs: list[bytes] = []


def add(body: str | bytes) -> int:
    objs.append(body.encode("latin-1") if isinstance(body, str) else body)
    return len(objs)


def stream(content: str) -> int:
    data = content.encode("latin-1")
    return add(b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream")


catalog = add("<< /Type /Catalog /Pages 2 0 R >>")
pages = add("PLACEHOLDER")
f1 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
desc = add("<< /Type /FontDescriptor /FontName /SyntheticNoMap /Flags 4 "
           "/FontBBox [0 -200 1000 900] /ItalicAngle 0 /Ascent 900 /Descent -200 "
           "/CapHeight 700 /StemV 80 >>")
cid = add(f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /SyntheticNoMap "
          f"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
          f"/FontDescriptor {desc} 0 R /DW 500 /CIDToGIDMap /Identity >>")
f2 = add(f"<< /Type /Font /Subtype /Type0 /BaseFont /SyntheticNoMap /Encoding /Identity-H "
         f"/DescendantFonts [{cid} 0 R] >>")
img = add(b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray "
          b"/BitsPerComponent 8 /Length 1 >>\nstream\n\x80\nendstream")
kids = []
for n, content in enumerate((page1, page2, page3), 1):
    s = stream(content)
    xobj = f" /XObject << /Im1 {img} 0 R >>" if n == 3 else ""
    kids.append(add(f"<< /Type /Page /Parent {pages} 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 {f1} 0 R /F2 {f2} 0 R >>{xobj} >> "
                    f"/Contents {s} 0 R >>"))
objs[pages - 1] = (f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] "
                   f"/Count {len(kids)} >>").encode("latin-1")
info = add("<< /Title (Synthetic Grid Note) /Author (Synthetic Strategist) >>")

out = bytearray(b"%PDF-1.4\n")
offsets = []
for i, body in enumerate(objs, 1):
    offsets.append(len(out))
    out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
xref = len(out)
out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
out += (b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objs) + 1, catalog, info, xref))
OUT.write_bytes(bytes(out))
print(f"wrote {OUT} ({len(out):,} bytes)")
