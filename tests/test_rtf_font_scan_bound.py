"""A CIQ RTF export reads in time linear in its size (issue #1004, the `customers()` hang).

THE SHAPE THIS GUARDS. striprtf 0.0.32 finds its font table with one `findall` over the whole file,
and the pattern's lazy `.*?\\fcharset` restarts at every `\\f<n>` font switch and runs to the end
of the line. CIQ's exports put megabytes on a line, so the read grew with the square of the size:
measured on 2026-11-11, AMZN's 2.9 MB Customers export did not finish in 90 s, GOOGL's 2.6 MB took
83.5 s and V's 1.6 MB 10.3 s, every second of it in that `findall`. Two corpus tests called
`customers()` on every folder, hung locally, and were deselected by every local gate.

`ciq.read_text` now puts a newline before each font switch, which bounds each scan at the next
switch. A newline means nothing in RTF outside binary data, so the text is unchanged. These
synthetic files have the shape of CIQ's exports (a font table, then one long line of rows that
switch fonts), built in the test. The corpus check is in
`tests/test_segment_absence_and_relationship_route.py`, whose two tests now bound each export.
"""
from __future__ import annotations

import time
from pathlib import Path

from striprtf.striprtf import rtf_to_text

from vinci.dossier import ciq

_HEAD = (r"{\rtf1\ansi\ansicpg1252\deff0{\fonttbl{\f0\fnil\fcharset0 Calibri;}"
         r"{\f1\fnil\fcharset0 Arial;}}")

#: 16,000 rows make a 645 KB line. Main's read took 24 s at this size on 2026-11-11 (6.0 s at 8,000
#: rows, 1.6 s at 4,000: quadratic). The bounded read takes 0.13 s, and 0.52 s at 2.6 MB.
_ROWS = 16_000
_BOUND_S = 5.0


def _one_line(rows: int) -> str:
    return _HEAD + "".join(rf"\f{i % 2} Row {i} Name|Distributor|Retail\par"
                           for i in range(rows)) + "}"


def test_a_long_line_of_font_switches_reads_within_a_bound(tmp_path: Path) -> None:
    """(+) A CIQ-shaped export of 645 KB reads in well under the bound, with every row."""
    path = tmp_path / "ACME Inc NYSE ACME Customers.rtf"
    path.write_text(_one_line(_ROWS), encoding="utf-8")
    t0 = time.monotonic()
    text = ciq.read_text(path, ciq.CiqFormat.RTF_TEXT)
    elapsed = time.monotonic() - t0
    assert text.count("Name|Distributor|Retail") == _ROWS
    assert elapsed < _BOUND_S, f"read {path.stat().st_size} B in {elapsed:.1f}s"


def test_the_bounded_scan_leaves_striprtfs_text_unchanged() -> None:
    """(−) The newline changes no character of the text: font switches between text, a hex
    escape, a Unicode escape with its fallback, a bold toggle, a HYPERLINK field of the corpus's
    shape (its font switch in the result), and an escaped backslash followed by 'f1', which is
    literal text and is never split."""
    raw = (_HEAD + r"\f0 a\f1 b \\f1 lit\'e9 \u8217?x\f0 c\par\b\f1 d\b0\f0 e"
           r'{\field{\*\fldinst{HYPERLINK "https://example.com"}}{\fldrslt{\f1 link}}}}')
    bounded = ciq._bounded_font_scan(raw)
    assert bounded != raw and bounded.count("\n") == 8
    assert rtf_to_text(bounded) == rtf_to_text(raw)
    assert r"\\f1" in bounded
    assert '("https://example.com")' in rtf_to_text(bounded)


def test_a_file_holding_binary_data_is_read_as_it_stands() -> None:
    """(−) A newline inside a `\\bin` group would change the bytes its length counts, so a file
    holding one is not touched."""
    raw = _HEAD + r"{\pict\bin4 \f1x}\f0 text}"
    assert ciq._bounded_font_scan(raw) == raw


def test_only_the_bin_control_word_leaves_a_file_as_it_stands() -> None:
    """(+) `\\binfsxn`/`\\binsxn` (page setup) and an escaped "\\bin" in the text hold no binary
    data, so they do not switch the bound off and send the read back to quadratic time."""
    for body in (r"\binfsxn1\f0 a", r"\binsxn2\f0 a", r"\f0 C:\\bin4 x"):
        raw = _HEAD + body + "}"
        bounded = ciq._bounded_font_scan(raw)
        assert bounded != raw, body
        assert rtf_to_text(bounded) == rtf_to_text(raw), body
