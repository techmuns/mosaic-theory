"""Build `tests/fixtures/ciq_kd_attribution.json`: the W85 pins' cut of three CIQ Key Developments
exports (operator ruling 2026-11-04, #891: a cut-down CIQ fixture holds a sheet's header row and
only the cells its pins read, cut through the real decode path).

Each name's export is named by its sha256 (the one its committed page was built from) and read by
`ciq.read_text`, as `ciq_sheets.key_developments` reads it. Kept: the 'Date | Company | Type |
Headline | Other Parties' header, and for each pinned row its row line and its 'Situation:' line.
The Situation is cut to its first 300 characters after whitespace is collapsed — exactly the
`verbatim` the committed page already carries — and the Other Parties cell, which no pin reads, is
blanked. Nothing else of the export is kept.

    python scripts/build_kd_attribution_fixture.py --manual-root <the CIQ manual folder>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from vinci.dossier.ciq import classify, read_text

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ciq_kd_attribution.json"

#: ticker → (the export, relative to the manual root; its sha256; the (date, headline start) of
#: each pinned row)
NAMES: dict[str, tuple[str, str, list[tuple[str, str]]]] = {
    "GOOGL": ("ciq-archive/replaced-2026-11-19/GOOGL/"
              "Alphabet Inc NasdaqGS GOOGL Key Developments.rtf",
              "42c70f0d8dd3", [("Sep-30-2026", "Lyft, Inc. Launches Lyft App in Europe")]),
    "UBER": ("ciq/UBER/Uber Technologies Inc NYSE UBER Key Developments.rtf",
             "c01be9430440", [("Jun-30-2026", "Wonder and Zipline Team Up")]),
    "AMZN": ("ciq/AMZN/Amazon com Inc NasdaqGS AMZN Key Developments.rtf",
             "8966359496c0", [("Aug-12-2026", "Kartoon Studios, Inc. Contracts"),
                              ("Sep-23-2026", "Best Buy and Amazon Open Fire Tv"),
                              ("Oct-20-2026", "Amazon Creates over 300,000")]),
}
_DATE = re.compile(r"^[A-Z][a-z]{2}-\d{2}-\d{4}$")


def cut(path: Path, rows: list[tuple[str, str]]) -> list[str]:
    lines = [ln.strip() for ln in read_text(path, classify(path)).splitlines() if ln.strip()]
    head = next(ln for ln in lines if ln.lower().startswith("date|") and "headline" in ln.lower())
    cols = [c.strip().lower() for c in head.split("|")]
    other = cols.index("other parties")
    out = [head]
    for date_s, start in rows:
        hits = [i for i, ln in enumerate(lines)
                if _DATE.match(ln.split("|")[0]) and ln.split("|")[0] == date_s
                and ln.split("|")[cols.index("headline")].startswith(start)]
        if len(hits) != 1:
            raise SystemExit(f"{path.name}: {len(hits)} rows match {date_s} {start!r}")
        cells = lines[hits[0]].split("|")
        cells[other] = ""
        sit = next(ln for ln in lines[hits[0] + 1:hits[0] + 3]
                   if ln.lower().startswith("situation:"))
        out += ["|".join(cells), " ".join(sit.split())[:300]]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manual-root", type=Path, required=True)
    a = ap.parse_args()
    doc: dict[str, object] = {
        "_about": ("Cut-down CIQ Key Developments exports for the W85 attribution pins "
                   "(tests/test_kd_attribution.py; operator ruling 2026-11-04, #891), built by "
                   "scripts/build_kd_attribution_fixture.py: each committed page's own export, "
                   "named by its sha256, read by ciq.read_text and cut to its header row and the "
                   "pinned rows; each Situation cut to the 300 characters the committed page "
                   "already carries as the row's verbatim, the Other Parties cell blanked."),
        "names": {}}
    names: dict[str, object] = {}
    for t, (rel, sha12, rows) in NAMES.items():
        path = a.manual_root / rel
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if not sha.startswith(sha12):
            raise SystemExit(f"{t}: {path.name} is {sha[:12]}, not the page's {sha12}")
        names[t] = {"workbook": path.name, "sha256": sha, "lines": cut(path, rows)}
    doc["names"] = names
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.name}: " + ", ".join(f"{t} {len(v['lines'])} lines"  # type: ignore[index]
                                            for t, v in names.items()))


if __name__ == "__main__":
    main()
