"""Step 3 of the SDK byte check (`capture.py`): two capture runs compared byte for byte, every
request matched by (path, label, n).

It prints per path the requests compared and the bodies byte-identical, then every header that
differs (name and both values, a key's value masked), in full and never cut. Exit 1 when any body
differs, a request is on one side only, a method or URL differs, or a header differs that is not
one of `ACCEPTED` (review of #1049, round 1: a planted `?beta=true` and an added beta header both
passed).

    python scripts/sdk_byte_check/compare.py <capture A> <capture B>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

Key = tuple[str, str, int]
#: Headers whose VALUE is a credential: compared as present or absent, never printed.
SECRET = frozenset({"x-api-key", "authorization"})
#: The headers `docs/records/2026-11-13-the-anthropic-sdk-is-pinned-at-2-6-0-behind-a-byte-check.md`
#: accepted as moving with the SDK (0.112.0 → 2.6.0), with the header order. Any OTHER header that
#: differs fails the check: a bump adding a beta or content header is a change to what the server
#: receives, and it is named, never waved through with the bodies.
ACCEPTED = frozenset({"anthropic-version", "x-api-key", "authorization", "user-agent",
                      "x-stainless-package-version", "accept-encoding", "(header order)"})


def load(d: Path) -> dict[Key, dict[str, Any]]:
    rows: list[dict[str, Any]] = json.loads((d / "index.json").read_text(encoding="utf-8"))
    return {(r["path"], r["label"], r["n"]): r for r in rows}


def compare(a: Path, b: Path) -> tuple[int, list[str]]:
    """(exit code, the report's lines)."""
    ra, rb = load(a), load(b)
    sa, sb = (json.loads((d / "summary.json").read_text(encoding="utf-8")) for d in (a, b))
    lines = [f"A: anthropic {sa['anthropic']} on {sa['http_lib']}   "
             f"B: anthropic {sb['anthropic']} on {sb['http_lib']}"]
    only = sorted(set(ra) ^ set(rb))
    if only:
        lines.append(f"requests on one side only ({len(only)}): {only}")
    per: dict[str, Counter[str]] = {}
    headers: Counter[tuple[str, str | None, str | None]] = Counter()
    urls: Counter[tuple[str, str, str, str]] = Counter()
    bodies: list[Key] = []
    for k in sorted(set(ra) & set(rb)):
        x, y = ra[k], rb[k]
        c = per.setdefault(k[0], Counter())
        c["compared"] += 1
        if (a / x["body_file"]).read_bytes() == (b / y["body_file"]).read_bytes():
            c["identical"] += 1
        else:
            bodies.append(k)
        if (x["method"], x["url"]) != (y["method"], y["url"]):
            urls[(x["method"], x["url"], y["method"], y["url"])] += 1
        hx, hy = dict(x["headers"]), dict(y["headers"])
        for name in sorted(set(hx) | set(hy)):
            vx, vy = hx.get(name), hy.get(name)
            if name in SECRET:
                vx = "<set>" if vx else None
                vy = "<set>" if vy else None
            if vx != vy:
                headers[(name, vx, vy)] += 1
        if [n for n, _ in x["headers"]] != [n for n, _ in y["headers"]]:
            headers[("(header order)", None, None)] += 1
    lines += [f"{p}: {c['compared']} compared, {c['identical']} bodies byte-identical"
              for p, c in per.items()]
    lines.append(f"bodies differing: {len(bodies)}" + (f" — {bodies}" if bodies else ""))
    lines.append(f"method/URL differing: {sum(urls.values())}")
    lines += [f"  {k} on {n} request(s)" for k, n in urls.items()]
    lines.append(f"headers differing ({len(headers)} distinct):")
    lines += [f"  {name}: {vx!r} -> {vy!r}  (on {n} request(s))"
              + ("" if name in ACCEPTED else "  — NOT ACCEPTED by the record: fails")
              for (name, vx, vy), n in sorted(headers.items(), key=lambda t: str(t[0]))]
    unaccepted = sorted({name for name, _, _ in headers if name not in ACCEPTED})
    if not set(ra) & set(rb):   # two empty captures are no check, never a pass
        lines.append("no request compared: a capture with nothing in it checks nothing")
        return 1, lines
    return (1 if only or bodies or urls or unaccepted else 0), lines


if __name__ == "__main__":
    code, out = compare(Path(sys.argv[1]), Path(sys.argv[2]))
    print("\n".join(out))
    raise SystemExit(code)
