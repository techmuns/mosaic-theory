"""5a, MORN: the sentences around the call / question words in MORN's own 8-Ks, read through the
repo's SEC client (cached). Prints each matching sentence, cut at 300 chars, with its document."""

from __future__ import annotations

import html
import re
import sys

from probe_common import sec_http

CIK = "1289419"
WORDS = re.compile(
    r"(earnings call|conference call|investor questions|shareholder questions|"
    r"written responses|webcast|do not hold|does not hold)",
    re.I,
)


def text(raw: str) -> str:
    t = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(t))


def main(accs: list[str]) -> None:
    http = sec_http()
    for acc in accs:
        base = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc.replace('-', '')}"
        idx = http.get_json(f"{base}/index.json", ttl_seconds=86400)
        docs = [
            i["name"]
            for i in idx["directory"]["item"]
            if i["name"].endswith((".htm", ".txt")) and not i["name"].endswith("index.htm")
        ]
        print(f"=== {acc}: {len(docs)} document(s) {docs}")
        for d in docs:
            raw = (
                http.get_text(f"{base}/{d}", ttl_seconds=86400)
                if hasattr(http, "get_text")
                else http.get(f"{base}/{d}", ttl_seconds=86400)
            )
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", "replace")
            t = text(raw)
            sents = [s for s in re.split(r"(?<=[.!?])\s+", t) if WORDS.search(s)]
            print(
                f"  -- {d}: {len(sents)} matching sentence(s); showing {min(len(sents), 6)} of "
                f"{len(sents)}"
            )
            for s in sents[:6]:
                print("     *", s[:300])


if __name__ == "__main__":
    main(sys.argv[1:])
