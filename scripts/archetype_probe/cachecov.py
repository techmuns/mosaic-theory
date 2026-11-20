"""Cache coverage of the two committed universes: which CIKs have submissions/companyfacts cached,
in a read-only SEC cache another checkout holds (ARCHETYPE_PROBE_SEC_CACHE) or the probe's own.
Prints fetched_at ranges."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from probe_common import CFG, WT, sec_cache_readonly

READONLY = sec_cache_readonly()
LOCAL = CFG.data_dir / "cache" / "sec"
CF = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SUB = "https://data.sec.gov/submissions/CIK{cik}.json"


def path_for(url: str, root: Path) -> Path:
    return root / f"{hashlib.sha256(url.encode()).hexdigest()}.json"


def meta(url: str) -> tuple[str, float] | None:
    roots = [(LOCAL, "probe")] if READONLY is None else [(READONLY, "read-only"), (LOCAL, "probe")]
    for root, name in roots:
        p = path_for(url, root)
        if p.exists():
            # read only the fetched_at without parsing the whole text: the entry is
            # {"url":..., "fetched_at":..., "text":...}
            with p.open() as fh:
                head = fh.read(400)
            i = head.find('"fetched_at":')
            fa = float(head[i + 13 :].split(",")[0]) if i >= 0 else -1.0
            return name, fa
    return None


def main() -> None:
    import datetime as dt

    ciks: dict[str, set[str]] = {}
    for band, f in (
        ("primary", "universe_snapshot.jsonl"),
        ("theme", "theme_universe_snapshot.jsonl"),
    ):
        for line in (WT / "data/snapshots" / f).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                ciks.setdefault(r["internal_id"].split("-")[1], set()).add(band)
    print(
        "distinct CIKs across both bands:",
        len(ciks),
        "| both bands:",
        sum(1 for v in ciks.values() if len(v) == 2),
    )
    for kind, tmpl in (("submissions", SUB), ("companyfacts", CF)):
        where: dict[str, int] = {}
        fas: list[float] = []
        missing = []
        for cik in ciks:
            m = meta(tmpl.format(cik=cik))
            if m is None:
                missing.append(cik)
                continue
            where[m[0]] = where.get(m[0], 0) + 1
            fas.append(m[1])
        fas.sort()

        def fmt(t: float) -> str:
            return dt.datetime.fromtimestamp(t, dt.UTC).date().isoformat()

        print(
            kind,
            where,
            "missing",
            len(missing),
            "fetched",
            fmt(fas[0]),
            "→",
            fmt(fas[-1]),
            "median",
            fmt(fas[len(fas) // 2]),
        )
        Path(sys.argv[1]).joinpath(f"missing_{kind}.txt").write_text("\n".join(missing))


main()
